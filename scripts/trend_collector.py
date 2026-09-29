# -*- coding: utf-8 -*-
"""
GoolAPP 수요 기반 앱 선정 스크립트 (trend_collector.py v3)
──────────────────────────────────────────────────────────────────────
변경 이력:
  v1-v2: Google Trends RSS + Nate 실시간 검색어 기반
  v3   : 수요 기반으로 전환
         (1) 실제 유입 CSV(네이버 블로그 + GSC) → 연관 검색어 묶음 분석
         (2) 네이버 검색광고 API → 월간 검색량·경쟁도
         (3) 시즌 달력(references/seo/seasonal-calendar.yaml) → 시즌 선행 후보
         (4) [선택, --with-trends] 기존 Google Trends RSS + Nate 참고용 출력
         (5) 점수 산정 → 사용자 번호 선택 → demand-report-YYYY-MM-DD.md 저장

사용법:
  # 수요 기반 (기본)
  python scripts/trend_collector.py

  # 유입 CSV 경로 직접 지정 (없으면 references/demand/ 자동 스캔)
  python scripts/trend_collector.py --demand-dir references/demand/2026-09/

  # 트렌드 소스도 함께 출력 (참고용)
  python scripts/trend_collector.py --with-trends

완료 기준 (revenue-recovery-plan §P1-1):
  - API 키 없어도 유입 CSV + 시즌 달력만으로 리포트 생성
  - 07/08 네이버 유입 CSV를 넣으면 "학점 4.3↔4.5 환산기", "직종별 정년 계산",
    "다주택자 보유세" 같은 후보가 상위에 나옴 (회귀 테스트 기준)
──────────────────────────────────────────────────────────────────────
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import csv
import datetime
import glob
import json
import math
import os
import pathlib
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
import hmac
import hashlib
import base64

root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

REPORT_DIR = pathlib.Path("references/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

DEMAND_DIR = pathlib.Path("references/demand")
DEMAND_DIR.mkdir(parents=True, exist_ok=True)

SEASONAL_CALENDAR = pathlib.Path("references/seo/seasonal-calendar.yaml")
SERP_BLOCKLIST = pathlib.Path("references/seo/serp-widget-blocklist.yaml")


# ── 공통 유틸 ──────────────────────────────────────────────────────────────────

def load_yaml_list(path: pathlib.Path) -> list:
    """YAML 파일을 리스트로 로드 (PyYAML 없으면 간단 파서 사용)."""
    if not path.exists():
        return []
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, list) else []
    except ImportError:
        # PyYAML 없을 때 간단 파싱 (리스트 형식만)
        items = []
        current = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.rstrip()
            if line.startswith("- topic:") or line.startswith("- keyword:"):
                if current:
                    items.append(current)
                current = {}
                key = "topic" if "topic:" in line else "keyword"
                current[key] = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("  ") and ":" in line and current:
                k, v = line.strip().split(":", 1)
                v = v.strip().strip('"')
                try:
                    v = int(v)
                except ValueError:
                    try:
                        v = float(v)
                    except ValueError:
                        pass
                current[k.strip()] = v
        if current:
            items.append(current)
        return items


def load_existing_slugs() -> list[str]:
    """기존 앱 slug 목록."""
    return sorted(pathlib.Path(f).stem for f in glob.glob("src/content/apps/*.md"))


def load_existing_keywords() -> set:
    """기존 앱의 primaryKeyword / title / slug 단어 집합."""
    existing = set()
    for fpath in glob.glob("src/content/apps/*.md"):
        slug = pathlib.Path(fpath).stem
        for word in slug.replace("-", " ").split():
            existing.add(word.lower())
        content = pathlib.Path(fpath).read_text(encoding="utf-8")
        if "---" not in content:
            continue
        try:
            fm_text = content.split("---")[1]
            for m in re.finditer(r'(?:title|primaryKeyword|keywords):\s*["\\[]?([^"\\]\n]+)', fm_text):
                val = m.group(1).strip()
                existing.add(val.replace(" ", ""))
                for w in val.replace(",", " ").split():
                    existing.add(w.strip().lower())
        except Exception:
            pass
    return existing


# ── 1. 유입 CSV 파싱 ─────────────────────────────────────────────────────────

def load_demand_csvs(demand_dir: pathlib.Path) -> list[dict]:
    """
    references/demand/ 하위 CSV 파일을 읽어 검색어 목록 반환.
    지원 형식:
      A) 네이버 블로그 유입분석 CSV (컬럼: 검색어, 유입수 등)
      B) GSC 검색어 CSV (컬럼: 상위 검색어, 클릭수, 노출수 등)
    반환: [{"keyword": str, "count": int, "source": str}, ...]
    """
    results = []
    csv_files = list(demand_dir.rglob("*.csv"))
    if not csv_files:
        print(f"  [INFO] {demand_dir}/ 에서 CSV 파일을 찾을 수 없습니다.")
        print(f"  [INFO] 네이버 블로그 유입분석 CSV 또는 GSC 검색어 CSV를 아래 경로에 저장하세요:")
        print(f"         {demand_dir}/YYYY-MM/naver-blog-YYYY-MM.csv")
        print(f"         {demand_dir}/YYYY-MM/gsc-queries-YYYY-MM.csv")
        return []

    print(f"  [CSV] {len(csv_files)}개 CSV 파일 발견")
    for fpath in csv_files:
        source = "naver_blog" if "naver" in fpath.name.lower() or "blog" in fpath.name.lower() else "gsc"
        try:
            # BOM 처리 + 다중 인코딩 시도
            for enc in ("utf-8-sig", "cp949", "utf-8"):
                try:
                    text = fpath.read_text(encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print(f"    [WARN] 인코딩 감지 실패: {fpath.name}")
                continue

            lines = text.splitlines()
            
            # 실제 헤더 행 찾기 (상단 메타데이터 무시)
            header_idx = 0
            for i, line in enumerate(lines[:20]):
                if any(x in line.lower() for x in ["상세유입경로", "검색어", "쿼리", "query", "keyword", "상위 검색어"]):
                    header_idx = i
                    break
                    
            reader = csv.DictReader(lines[header_idx:])
            headers = reader.fieldnames or []

            # 컬럼명 자동 감지
            kw_col = next((h for h in headers if h and any(x in h.lower() for x in ["상세유입경로", "검색어", "쿼리", "query", "keyword", "상위 검색어"])), None)
            cnt_col = next((h for h in headers if h and any(x in h.lower() for x in ["비율", "유입수", "클릭수", "clicks", "count", "수"])), None)

            if not kw_col:
                print(f"    [WARN] 검색어 컬럼 감지 실패 (headers={headers[:5]}): {fpath.name}")
                continue

            count = 0
            for row in reader:
                kw = str(row.get(kw_col, "")).strip()
                if not kw or kw in ("-", "기타", "(not set)", "(not provided)"):
                    continue
                try:
                    # '비율' 등 소수점이 있을 수 있으므로 float 후 int 캐스팅
                    cnt_raw = str(row.get(cnt_col, "1")).replace(",", "").strip()
                    cnt = int(float(cnt_raw) * 100) if "비율" in cnt_col else int(float(cnt_raw))
                except (ValueError, TypeError):
                    cnt = 1
                results.append({"keyword": kw, "count": cnt, "source": source})
                count += 1

            print(f"    ✓ {fpath.name}: {count}개 검색어 로드 ({source})")
        except Exception as e:
            print(f"    [WARN] CSV 로드 실패 ({fpath.name}): {e}")

    # count 기준 내림차순 정렬 + 중복 병합
    merged: dict[str, dict] = {}
    for item in results:
        kw = item["keyword"]
        if kw in merged:
            merged[kw]["count"] += item["count"]
        else:
            merged[kw] = item.copy()
    final = sorted(merged.values(), key=lambda x: x["count"], reverse=True)
    print(f"  → 유입 검색어 총 {len(final)}개 (중복 병합 후)")
    return final


# ── 2. AI로 검색어 묶음 분석 ─────────────────────────────────────────────────

def ai_cluster_queries(queries: list[dict], existing_slugs: list[str]) -> list[dict]:
    """
    AI가 유입 검색어를 의미 단위로 묶고 앱 아이디어 제안.
    반환: [{"cluster_name": str, "queries": [...], "app_idea": str, ...}, ...]
    """
    if not queries:
        return []

    print(f"\n[AI] 유입 검색어 {len(queries)}개 클러스터링 중...")
    try:
        import scripts.lib.ai_client as ai_client
    except ImportError:
        print("  [ERROR] ai_client 임포트 실패")
        return []

    # 상위 80개만 전달 (토큰 절약)
    top_queries = queries[:80]
    kw_list = [{"keyword": q["keyword"], "count": q["count"]} for q in top_queries]

    SYSTEM = f"""너는 한국 저관여 웹앱(GoolAPP) 기획 전문가다.
입력: 실제 유입 검색어 목록 (count=유입수)
출력: 의미 단위로 묶은 클러스터 배열 (JSON만, 설명 없이)

각 클러스터 형식:
{{
  "cluster_name": "주요 도구 검색어 (예: 학점 환산기)",
  "queries": ["원본 검색어1", "원본 검색어2", ...],
  "total_count": 묶음 내 count 합계,
  "app_idea": "구체적인 앱 아이디어 한 줄",
  "app_type": "calculator|quiz|tool|fun|datetime|finance 중 하나",
  "slug_hint": "영문 소문자 하이픈 slug",
  "classification": "new|extend|optimize 중 하나",
  "extend_slug": "extend일 때 기존 앱 slug, 아니면 null",
  "appifiable": true|false,
  "reason": "한 줄 이유"
}}

classification 기준:
- new: 해당 앱이 아예 없음 → 신규 앱 제작 필요
- extend: 기존 앱이 일부만 커버 → 기능 확장 필요
- optimize: 이미 잘 커버 → SEO title/description 최적화만

appifiable=false 기준:
- 연예인·드라마·사건·스포츠 경기 결과
- 실시간 API 없이 구현 불가 (날씨, 실시간 주가 등)
- 기존 앱과 완전히 동일한 기능

기존 앱 slug 목록 (의미 중복 여부 판단용):
{chr(10).join(existing_slugs)}

규칙:
- 비슷한 검색어는 하나의 cluster로 묶어라 (예: "gpa 환산", "4.3 4.5 환산", "학점 변환기" → 같은 클러스터)
- 클러스터가 너무 잘게 쪼개지지 않도록 할 것 (최소 5개 이상 검색어가 있어야 의미 있는 클러스터)
- 결과는 total_count 내림차순으로 정렬"""

    user_input = json.dumps(kw_list, ensure_ascii=False)

    try:
        text = ai_client.call(
            task="keyword_scoring",
            system=SYSTEM,
            user=user_input,
            max_tokens=4000,
            log_label="trend_collector_v3:cluster",
        )
        cleaned = text.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        elif cleaned.startswith("```"): cleaned = cleaned[3:]
        if cleaned.endswith("```"): cleaned = cleaned[:-3]

        # JSON 자동 복구
        cleaned = re.sub(r':\s*([,}\]])', r': null\1', cleaned.strip())
        if cleaned.count('[') > cleaned.count(']'):
            cleaned = cleaned.rstrip().rstrip(',') + "\n]"

        clusters = json.loads(cleaned)
        print(f"  → AI 클러스터링 완료: {len(clusters)}개 묶음")
        return clusters if isinstance(clusters, list) else []
    except Exception as e:
        print(f"  [WARN] AI 클러스터링 실패: {e}")
        # 폴백: 상위 10개를 개별 후보로 반환
        fallback = []
        for q in top_queries[:10]:
            fallback.append({
                "cluster_name": q["keyword"],
                "queries": [q["keyword"]],
                "total_count": q["count"],
                "app_idea": None,
                "app_type": None,
                "slug_hint": None,
                "classification": "new",
                "extend_slug": None,
                "appifiable": None,
                "reason": "AI 미처리",
            })
        return fallback


# ── 3. 시즌 달력 기반 후보 ────────────────────────────────────────────────────

def load_seasonal_candidates() -> list[dict]:
    """
    seasonal-calendar.yaml에서 현재 날짜 기준 lead_weeks 이내 항목 반환.
    반환: [{"cluster_name": str, "seasonal": True, ...}, ...]
    """
    items = load_yaml_list(SEASONAL_CALENDAR)
    if not items:
        print("  [INFO] seasonal-calendar.yaml 없음. 시즌 후보 건너뜀.")
        return []

    today = datetime.date.today()
    candidates = []
    for item in items:
        try:
            peak_month = int(item.get("peak_month", 0))
            lead_weeks = int(item.get("lead_weeks", 4))
            if not (1 <= peak_month <= 12):
                continue

            # 이번 해 또는 내년 peak_month 계산
            peak_this_year = datetime.date(today.year, peak_month, 1)
            peak_next_year = datetime.date(today.year + 1, peak_month, 1)

            # 가장 가까운 peak 시점
            candidates_dates = [peak_this_year, peak_next_year]
            nearest_peak = min(candidates_dates, key=lambda d: abs((d - today).days))

            # lead_weeks 기간 안에 들어오는지 확인
            days_until_peak = (nearest_peak - today).days
            lead_days = lead_weeks * 7

            if -7 <= days_until_peak <= lead_days:  # 피크 1주 후까지 포함
                related_apps = item.get("related_apps", [])
                classification = "extend" if related_apps else "new"
                candidates.append({
                    "cluster_name": item.get("topic", ""),
                    "queries": [item.get("topic", "")],
                    "total_count": 0,  # 시즌 신호는 검색량 데이터 없음
                    "app_idea": item.get("notes", ""),
                    "app_type": "calculator",
                    "slug_hint": None,
                    "classification": classification,
                    "extend_slug": related_apps[0] if related_apps else None,
                    "related_apps": related_apps,
                    "appifiable": True,
                    "reason": f"시즌 선행 {lead_weeks}주 이내 (피크: {peak_month}월, D-{max(0, days_until_peak)}일)",
                    "seasonal": True,
                    "peak_month": peak_month,
                    "days_until_peak": days_until_peak,
                })
        except Exception as e:
            continue

    print(f"  → 시즌 후보 {len(candidates)}개 (현재 날짜 기준 lead 구간)")
    return candidates


# ── 4. 네이버 검색광고 API — 월간 검색량 ──────────────────────────────────────

def get_naver_searchad_volume(keywords: list[str]) -> dict:
    """
    네이버 검색광고 API (keywordstool)로 키워드별 월간 검색량 조회.
    반환: {keyword: {"pc": int, "mobile": int, "total": int, "comp_idx": str}, ...}
    
    환경변수 필요:
      NAVER_SEARCHAD_API_KEY
      NAVER_SEARCHAD_SECRET
      NAVER_SEARCHAD_CUSTOMER_ID
    """
    api_key = os.getenv("NAVER_SEARCHAD_API_KEY", "")
    secret = os.getenv("NAVER_SEARCHAD_SECRET", "")
    customer_id = os.getenv("NAVER_SEARCHAD_CUSTOMER_ID", "")

    if not (api_key and secret and customer_id):
        print("  [INFO] NAVER_SEARCHAD_API_KEY / SECRET / CUSTOMER_ID 없음 → 검색량 조회 건너뜀")
        print("         .env에 추가하면 검색량 기반 점수 산정이 가능해집니다.")
        print("         U-6 참조: 네이버 검색광고 계정에서 API 키 발급")
        return {}

    if not keywords:
        return {}

    print(f"\n[검색량] 네이버 검색광고 API 호출 ({len(keywords)}개 키워드)...")
    base_url = "https://api.searchad.naver.com"
    result = {}

    # 5개씩 배치
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i + 5]
        hint_params = "&".join(f"hintKeywords={urllib.request.quote(k)}" for k in batch)
        url = f"{base_url}/keywordstool?{hint_params}&showDetail=1"

        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}.GET./keywordstool"
        signature = base64.b64encode(
            hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")

        req = urllib.request.Request(url)
        req.add_header("X-Timestamp", timestamp)
        req.add_header("X-API-KEY", api_key)
        req.add_header("X-Customer", customer_id)
        req.add_header("X-Signature", signature)
        req.add_header("Content-Type", "application/json; charset=UTF-8")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for item in data.get("keywordList", []):
                kw = item.get("relKeyword", "")
                pc = item.get("monthlyPcQcCnt", 0)
                mobile = item.get("monthlyMobileQcCnt", 0)
                comp_idx = item.get("compIdx", "중간")
                # "< 10" 처리
                pc = 0 if isinstance(pc, str) else int(pc)
                mobile = 0 if isinstance(mobile, str) else int(mobile)
                total = pc + mobile
                result[kw] = {"pc": pc, "mobile": mobile, "total": total, "comp_idx": str(comp_idx)}
                print(f"  └ {kw}: PC {pc:,} / 모바일 {mobile:,} / 경쟁도 {comp_idx}")
        except Exception as e:
            print(f"  [WARN] 검색량 조회 실패 ({batch}): {e}")

        time.sleep(0.5)

    print(f"  → 검색량 조회 완료: {len(result)}개")
    return result


# ── 5. SERP 위젯 블록리스트 로드 ─────────────────────────────────────────────

def load_serp_blocklist() -> set:
    """serp-widget-blocklist.yaml에서 블록 키워드 집합 반환."""
    items = load_yaml_list(SERP_BLOCKLIST)
    blocked = set()
    for item in items:
        kw = item.get("keyword", "")
        if kw:
            blocked.add(kw)
            blocked.add(kw.replace(" ", ""))
    return blocked


# ── 6. 점수 산정 ─────────────────────────────────────────────────────────────

CATEGORY_WEIGHTS = {
    "금융": 1.5, "세금": 1.5, "부동산": 1.5, "대출": 1.5, "급여": 1.5, "보험": 1.5,
    "finance": 1.5,
    "생활": 1.0, "건강": 1.0, "calculator": 1.0, "tool": 1.0, "datetime": 1.0,
    "퀴즈": 0.7, "게임": 0.7, "운세": 0.7, "fun": 0.7, "quiz": 0.7,
}

FINANCE_KEYWORDS = {"세금", "부동산", "대출", "이자", "금리", "연봉", "급여", "보험", "종부세", "재산세", "종합소득세", "최저임금", "퇴직금", "연금"}


def calc_score(cluster: dict, search_vol: dict, serp_blocked: set, today: datetime.date) -> float:
    """
    score = log10(월간검색수 + 1)
          × 광고단가 가중치
          × SERP 가중치
          × 시즌 가중치
          × 유입 실적 가중치
    """
    name = cluster.get("cluster_name", "")
    queries = cluster.get("queries", [])
    total_count = cluster.get("total_count", 0)
    seasonal = cluster.get("seasonal", False)
    app_type = cluster.get("app_type") or ""

    # 월간 검색량 (검색광고 API 결과 또는 추정)
    vol = 0
    for q in queries:
        if q in search_vol:
            vol = max(vol, search_vol[q].get("total", 0))
    if vol == 0:
        # 유입 실적이 있으면 최소 검색량 추정
        vol = max(total_count * 50, 100) if total_count > 0 else 100

    # 광고단가 가중치
    cat_weight = CATEGORY_WEIGHTS.get(app_type, 1.0)
    # 키워드 기반 보완
    for fw in FINANCE_KEYWORDS:
        if fw in name:
            cat_weight = max(cat_weight, 1.5)
            break
    if any(k in name for k in ["퀴즈", "게임", "운세", "점"]):
        cat_weight = min(cat_weight, 0.7)

    # SERP 가중치
    serp_weight = 1.0
    for q in queries:
        if q in serp_blocked or q.replace(" ", "") in serp_blocked:
            serp_weight = 0.3
            break

    # 시즌 가중치
    season_weight = 1.0
    if seasonal:
        season_weight = 1.3
    # 유입 실적 가중치
    inflow_weight = 1.5 if total_count > 0 else 1.0

    score = math.log10(vol + 1) * cat_weight * serp_weight * season_weight * inflow_weight
    return round(score, 3)


# ── 7. [선택] 기존 Google Trends RSS + Nate 실시간 (--with-trends) ─────────────

def collect_google_trends_rss() -> list[dict]:
    url = "https://trends.google.com/trending/rss?geo=KR"
    print(f"  [Trends] Google Trends RSS 호출 중...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        ns = {"ht": "https://trends.google.com/trending/rss"}
        items = []
        for item in root.findall(".//item"):
            title_el = item.find("title")
            traffic_el = item.find("ht:approx_traffic", ns)
            news_el = item.find("ht:news_item/ht:news_item_title", ns)
            keyword = title_el.text.strip() if title_el is not None else ""
            traffic = traffic_el.text.strip() if traffic_el is not None else "N/A"
            news = news_el.text.strip() if news_el is not None else ""
            if keyword and any('\uac00' <= c <= '\ud7a3' for c in keyword):
                items.append({"keyword": keyword, "traffic": traffic, "news_title": news})
        print(f"  → Google Trends: 한국어 키워드 {len(items)}개")
        return items
    except Exception as e:
        print(f"  [WARN] Google Trends 실패: {e}")
        return []


def collect_nate_trends() -> list[dict]:
    print("  [Trends] Nate 실시간 검색어 호출 중...")
    items = []
    try:
        url = "https://www.nate.com/js/data/jsonLiveKeywordDataV1.js"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("euc-kr")
            data = json.loads(raw)
            for row in data:
                kw = row[1]
                if len(kw) < 20:
                    items.append({"keyword": kw, "traffic": "N/A", "news_title": "Nate 실시간"})
        print(f"  → Nate: {len(items)}개")
    except Exception as e:
        print(f"  [WARN] Nate 실패: {e}")
    return items


# ── 8. 터미널 출력 + 사용자 선택 ─────────────────────────────────────────────

def display_and_select(candidates: list[dict], serp_blocked: set) -> list[dict]:
    """
    후보 목록을 점수순으로 정렬·출력하고 사용자가 번호로 선택.
    """
    scoreable = [c for c in candidates if c.get("appifiable") is not False]
    if not scoreable:
        print("\n[!] 앱 제작 가능한 후보가 없습니다.")
        return []

    print("\n" + "=" * 70)
    print("  수요 기반 앱 후보 목록 (점수순)")
    print("=" * 70)

    for i, item in enumerate(scoreable, 1):
        name = item.get("cluster_name", "")
        idea = item.get("app_idea") or ""
        atype = item.get("app_type") or ""
        slug = item.get("slug_hint") or ""
        cls = item.get("classification", "new")
        reason = item.get("reason", "")
        score = item.get("_score", 0)
        vol = item.get("_vol_str", "")
        seasonal = item.get("seasonal", False)
        ext = item.get("extend_slug", "")
        queries = item.get("queries", [])
        is_blocked = any(q in serp_blocked for q in queries)
        blocked_label = "⚠️ SERP위젯" if is_blocked else ""

        print(f"\n  [{i}] {name}  (점수: {score:.2f}) {blocked_label}")
        print(f"       분류   : {cls}" + (f" → {ext}" if ext else "") + (" 🗓 시즌" if seasonal else ""))
        print(f"       타입   : {atype}")
        print(f"       검색량 : {vol}")
        print(f"       아이디어: {idea}")
        print(f"       slug   : {slug}")
        print(f"       근거   : {reason}")
        if len(queries) > 1:
            print(f"       검색어 : {', '.join(queries[:5])}")

    # 제외 목록
    excluded = [c for c in candidates if c.get("appifiable") is False]
    if excluded:
        print("\n" + "=" * 70)
        print("  앱으로 만들기 어려운 후보:")
        for x in excluded:
            print(f"    ✗ {x.get('cluster_name','')} — {x.get('reason','')}")

    # SERP 확인 체크리스트
    blocked_items = [c for c in scoreable if c.get("_serp_blocked")]
    if blocked_items:
        print("\n" + "=" * 70)
        print("  ⚠️  사용자 직접 확인 필요 (SERP 위젯 여부):")
        for item in blocked_items:
            print(f"    → '{item.get('cluster_name','')}': 네이버/구글 검색 결과에 위젯이 없는지 확인 후 선택")

    print("\n" + "=" * 70)
    print("원하는 앱 번호를 선택하세요 (예: 1  또는  1,3  또는  skip):")
    raw = input("  > ").strip()

    if not raw or raw.lower() == "skip":
        print("  건너뜁니다.")
        return []

    selected = []
    for part in raw.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < len(scoreable):
                selected.append(scoreable[idx])
        except ValueError:
            pass
    return selected


# ── 9. 리포트 저장 ──────────────────────────────────────────────────────────

def save_report(all_candidates: list[dict], selected: list[dict]) -> pathlib.Path:
    today = datetime.date.today().isoformat()
    out_path = REPORT_DIR / f"demand-report-{today}.md"

    lines = [
        f"# GoolAPP 수요 기반 리포트 — {today}",
        "",
        "> 유입 CSV(네이버 블로그 + GSC) + 시즌 달력 + 네이버 검색광고 API 기반 자동 수집",
        f"> 생성 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    if selected:
        lines += ["## ✅ 선택된 앱 후보", ""]
        for item in selected:
            name = item.get("cluster_name", "")
            idea = item.get("app_idea") or ""
            slug = item.get("slug_hint") or ""
            cls = item.get("classification", "new")
            queries = item.get("queries", [])
            lines.append(f"### {name}")
            lines.append(f"- **아이디어**: {idea}")
            lines.append(f"- **slug**: `{slug}`")
            lines.append(f"- **분류**: {cls}")
            lines.append(f"- **타입**: {item.get('app_type','')}")
            lines.append(f"- **점수**: {item.get('_score', 0):.2f}")
            lines.append(f"- **연관 검색어**: {', '.join(queries)}")
            lines.append("")

        lines += ["---", "", "### 다음 단계 명령어", "```"]
        for item in selected:
            name = item.get("cluster_name", "")
            slug = item.get("slug_hint") or ""
            queries = item.get("queries", [])
            q_arg = ",".join(queries[:5])
            cls = item.get("classification", "new")
            extend = item.get("extend_slug", "")
            if cls == "extend" and extend:
                lines.append(f'python scripts/new_app_pipeline.py "{name}" {slug} --queries "{q_arg}" --extend {extend}')
            else:
                lines.append(f'python scripts/new_app_pipeline.py "{name}" {slug} --queries "{q_arg}"')
        lines += ["```", ""]

    # 전체 후보 표
    scoreable = [c for c in all_candidates if c.get("appifiable") is not False]
    not_app = [c for c in all_candidates if c.get("appifiable") is False]

    lines += [
        "---", "",
        f"## 전체 앱 후보 ({len(scoreable)}개, 점수순)",
        "",
        "| # | 후보명 | 분류 | 점수 | 검색량 | 시즌 | slug 힌트 |",
        "|---|--------|------|------|--------|------|-----------|",
    ]
    for i, item in enumerate(scoreable, 1):
        name = item.get("cluster_name", "")
        cls = item.get("classification", "new")
        score = item.get("_score", 0)
        vol = item.get("_vol_str", "")
        seasonal = "🗓" if item.get("seasonal") else ""
        slug = item.get("slug_hint") or ""
        lines.append(f"| {i} | **{name}** | {cls} | {score:.2f} | {vol} | {seasonal} | `{slug}` |")

    if not_app:
        lines += ["", f"## 제외된 후보 ({len(not_app)}개)", ""]
        for item in not_app:
            lines.append(f"- {item.get('cluster_name','')} — {item.get('reason','')}")

    lines += [
        "",
        "---",
        "",
        "## 사용자 확인 사항",
        "",
        "- [ ] SERP 위젯 여부: 위 ⚠️ 표시 항목을 네이버에서 직접 검색해 위젯 없는지 확인",
        "- [ ] 선택 후 `python scripts/new_app_pipeline.py` 실행",
        "- [ ] 완료 후 `references/AI_CONTEXT.md`에 로그 추가",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ── 메인 ──────────────────────────────────────────────────────────────────────

def run(demand_dir: pathlib.Path, with_trends: bool = False):
    print("=" * 70)
    print("  GoolAPP 수요 기반 앱 선정 스크립트 v3")
    print("  유입 CSV + 시즌 달력 + 네이버 검색광고 API → 앱 후보 제안")
    print("=" * 70)

    today = datetime.date.today()
    existing_slugs = load_existing_slugs()
    existing_keywords = load_existing_keywords()
    serp_blocked = load_serp_blocklist()

    all_candidates: list[dict] = []

    # ── Step 1: 유입 CSV 분석 ──────────────────────────────────────────────────
    print("\n[1/4] 유입 CSV 분석...")
    raw_queries = load_demand_csvs(demand_dir)

    if raw_queries:
        clusters = ai_cluster_queries(raw_queries, existing_slugs)
        # appifiable이 None인 항목 → 기본 true 처리
        for c in clusters:
            if c.get("appifiable") is None:
                c["appifiable"] = True
        all_candidates.extend(clusters)
    else:
        print("  유입 CSV가 없어 AI 클러스터링을 건너뜁니다.")

    # ── Step 2: 시즌 달력 ─────────────────────────────────────────────────────
    print("\n[2/4] 시즌 달력 기반 후보 추가...")
    seasonal = load_seasonal_candidates()
    # 기존 클러스터와 중복 제거 (topic 기준)
    existing_names = {c.get("cluster_name", "") for c in all_candidates}
    for s in seasonal:
        if s.get("cluster_name", "") not in existing_names:
            all_candidates.append(s)

    # ── Step 3: 검색량 조회 (네이버 검색광고 API) ────────────────────────────
    print("\n[3/4] 네이버 검색량 조회...")
    kw_to_query = []
    for c in all_candidates:
        if c.get("appifiable") is not False:
            kw_to_query.extend(c.get("queries", [])[:2])
    kw_to_query = list(dict.fromkeys(kw_to_query))[:30]  # 중복 제거, 최대 30개
    search_vol = get_naver_searchad_volume(kw_to_query)

    # ── Step 4: 점수 산정 + 정렬 ─────────────────────────────────────────────
    print("\n[4/4] 점수 산정 및 정렬...")
    for c in all_candidates:
        if c.get("appifiable") is False:
            c["_score"] = 0
            c["_vol_str"] = "-"
            c["_serp_blocked"] = False
            continue
        score = calc_score(c, search_vol, serp_blocked, today)
        c["_score"] = score

        # 검색량 문자열
        queries = c.get("queries", [])
        vol = 0
        for q in queries:
            if q in search_vol:
                vol = max(vol, search_vol[q].get("total", 0))
        c["_vol_str"] = f"{vol:,}" if vol > 0 else "데이터 없음"

        # SERP 블록 여부
        c["_serp_blocked"] = any(q in serp_blocked for q in queries)

    # 점수 내림차순 정렬 (appifiable=False는 맨 뒤)
    all_candidates.sort(key=lambda x: (x.get("appifiable") is False, -x.get("_score", 0)))

    # ── [선택] Google Trends + Nate ───────────────────────────────────────────
    if with_trends:
        print("\n[참고] 기존 트렌드 소스 수집 (--with-trends)...")
        trend_items = collect_google_trends_rss() + collect_nate_trends()
        if trend_items:
            print(f"\n  참고용 트렌드 키워드 ({len(trend_items)}개):")
            for item in trend_items[:20]:
                print(f"    - {item['keyword']} (트래픽: {item.get('traffic','N/A')})")

    # ── 터미널 출력 + 사용자 선택 ────────────────────────────────────────────
    selected = display_and_select(all_candidates, serp_blocked)

    # ── 리포트 저장 ──────────────────────────────────────────────────────────
    out_path = save_report(all_candidates, selected)
    print(f"\n✅ 리포트 저장: {out_path}")

    if selected:
        print("\n[다음 단계] 선택한 앱을 만들려면:")
        for item in selected:
            name = item.get("cluster_name", "")
            slug = item.get("slug_hint") or ""
            queries = item.get("queries", [])
            q_arg = ",".join(queries[:5])
            cls = item.get("classification", "new")
            extend = item.get("extend_slug", "")
            if cls == "extend" and extend:
                print(f'  python scripts/new_app_pipeline.py "{name}" {slug} --queries "{q_arg}" --extend {extend}')
            else:
                print(f'  python scripts/new_app_pipeline.py "{name}" {slug} --queries "{q_arg}"')
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GoolAPP 수요 기반 앱 선정 스크립트 v3")
    parser.add_argument(
        "--demand-dir",
        type=str,
        default=str(DEMAND_DIR),
        help=f"유입 CSV 디렉토리 경로 (기본: {DEMAND_DIR})",
    )
    parser.add_argument(
        "--with-trends",
        action="store_true",
        help="Google Trends RSS + Nate 실시간 검색어도 참고용으로 출력",
    )
    args = parser.parse_args()
    run(pathlib.Path(args.demand_dir), with_trends=args.with_trends)
