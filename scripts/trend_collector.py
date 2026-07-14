# -*- coding: utf-8 -*-
"""
GoolAPP 트렌드 수집기 (v2)
──────────────────────────────────────────────────────────────────────
사용법:
  python scripts/trend_collector.py

동작:
  1. Google Trends KR RSS → 실시간 급상승 키워드 수집
  2. Naver DataLab API    → 수집된 키워드 교차 검증 (네이버 검색량 확인)
  3. AI                   → 저관여 앱 가능성 판단 + 앱 아이디어 제안
  4. 터미널에 번호 매긴 앱 후보 목록 출력 → 사용자가 번호 선택
  5. 선택 결과를 references/reports/trend-report-YYYY-MM-DD.md 에 저장
──────────────────────────────────────────────────────────────────────
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import json, os, pathlib, datetime, time, urllib.request, xml.etree.ElementTree as ET

root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

REPORT_DIR = pathlib.Path("references/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ── 1. Google Trends KR RSS ──────────────────────────────────────────────────

def collect_google_trends_rss() -> list[dict]:
    """
    Google Trends 한국 RSS 피드에서 급상승 키워드 수집.
    반환: [{"keyword": str, "traffic": str, "news_title": str}, ...]
    """
    url = "https://trends.google.com/trending/rss?geo=KR"
    print(f"[1/3] Google Trends RSS 호출 중...")
    print(f"      URL : {url}")
    print(f"      잠시 기다려주세요...", flush=True)
    t0 = time.time()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        print(f"      응답 수신 완료 ({time.time()-t0:.1f}초)")

        root = ET.fromstring(raw)
        ns = {"ht": "https://trends.google.com/trending/rss"}
        items = []

        for item in root.findall(".//item"):
            title_el = item.find("title")
            traffic_el = item.find("ht:approx_traffic", ns)
            news_el = item.find("ht:news_item/ht:news_item_title", ns)

            keyword = title_el.text.strip() if title_el is not None else ""
            traffic = traffic_el.text.strip() if traffic_el is not None else "N/A"
            news    = news_el.text.strip() if news_el is not None else ""

            if keyword:
                items.append({"keyword": keyword, "traffic": traffic, "news_title": news})

        # 한국어가 포함된 키워드만 (외국어 트렌드 제거)
        def is_korean(s):
            return any('\uac00' <= c <= '\ud7a3' for c in s)

        korean_items = [x for x in items if is_korean(x["keyword"])]
        print(f"  → 총 {len(items)}개 중 한국어 키워드 {len(korean_items)}개 추출")
        return korean_items

    except Exception as e:
        print(f"  [ERROR] Google Trends RSS 수집 실패: {e}")
        return []


# ── 1.5 Nate 실시간 검색어 ────────────────────────────────────────────────────

def collect_nate_trends() -> list[dict]:
    """네이트(Nate) 실시간 검색어 10개 수집"""
    print("      Nate 실시간 검색어 호출 중...")
    items = []
    try:
        url = "https://www.nate.com/js/data/jsonLiveKeywordDataV1.js"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("euc-kr")
            data = json.loads(raw)
            for row in data:
                kw = row[1]
                # 너무 긴 설명문구 제외
                if len(kw) < 20:
                    items.append({
                        "keyword": kw,
                        "traffic": "N/A",
                        "news_title": "네이트 실시간 검색어"
                    })
        print(f"      응답 수신 완료 ({time.time()-t0:.1f}초)")
        print(f"  → Nate Trends: 키워드 {len(items)}개 추출")
    except Exception as e:
        print(f"  [WARN] Nate 수집 실패: {e}")
    return items


# ── 2. Naver DataLab API ─────────────────────────────────────────────────────

def collect_naver_trends(keywords: list[str]) -> dict:
    """
    Naver DataLab API로 키워드별 최근 검색량 지수 조회.
    반환: {keyword: {"recent_avg": float, "rise_rate_pct": float}, ...}
    """
    client_id     = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("  [WARN] NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 없음 — Naver 검증 건너뜀")
        return {}

    if not keywords:
        return {}

    total_batches = (min(len(keywords), 25) + 4) // 5
    print(f"[2/3] Naver DataLab API 교차 검증")
    print(f"      키워드 {len(keywords)}개 → {total_batches}개 배치로 호출")
    print(f"      URL : https://openapi.naver.com/v1/datalab/search")

    end_date   = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    interest_map = {}

    # 최대 25개, 5개씩 배치
    for i in range(0, min(len(keywords), 25), 5):
        batch = keywords[i:i+5]
        batch_num = i // 5 + 1
        print(f"      배치 {batch_num}/{total_batches} 호출 중: {batch} ...", flush=True)
        keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in batch]

        payload = json.dumps({
            "startDate":     start_date.strftime("%Y-%m-%d"),
            "endDate":       end_date.strftime("%Y-%m-%d"),
            "timeUnit":      "date",
            "keywordGroups": keyword_groups,
        }, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(
            "https://openapi.naver.com/v1/datalab/search",
            data=payload,
        )
        req.add_header("X-Naver-Client-Id", client_id)
        req.add_header("X-Naver-Client-Secret", client_secret)
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for result in data.get("results", []):
                kw     = result["title"]
                ratios = [d["ratio"] for d in result.get("data", []) if d["ratio"] > 0]
                if ratios:
                    recent  = ratios[-7:] if len(ratios) >= 7 else ratios
                    prev    = ratios[:7]  if len(ratios) >= 14 else ratios[:len(ratios)//2]
                    r_avg   = sum(recent) / len(recent)
                    p_avg   = sum(prev)   / len(prev)   if prev else r_avg
                    rise    = round((r_avg - p_avg) / max(p_avg, 0.1) * 100, 1)
                    interest_map[kw] = {
                        "recent_avg":   round(r_avg, 1),
                        "rise_rate_pct": rise,
                    }
            for kw in batch:
                if kw in interest_map:
                    n = interest_map[kw]
                    print(f"      └ {kw}: 최근 {n['recent_avg']:.1f} / 상승률 {n['rise_rate_pct']:+.1f}%")
        except Exception as e:
            print(f"      └ [실패] {e}")

        time.sleep(0.3)

    print(f"      완료: {len(interest_map)}개 키워드에 대한 네이버 검색량 데이터 수집 완료")
    return interest_map


# ── 3. 기존 앱 목록 로드 (중복 방지) ─────────────────────────────────────────

def load_existing_keywords() -> set:
    """기존 앱의 title, primaryKeyword, slug를 모두 수집 (중복 방지용)"""
    existing = set()
    try:
        import glob, re
        for fpath in glob.glob("src/content/apps/*.md"):
            # slug는 파일명에서 추출
            slug = pathlib.Path(fpath).stem
            # slug의 단어들을 개별로 추가 (예: loan-interest-calculator → 이자, interest, loan)
            for word in slug.replace("-", " ").split():
                existing.add(word.lower())

            content = pathlib.Path(fpath).read_text(encoding="utf-8")
            if "---" not in content:
                continue
            try:
                fm_text = content.split("---")[1]
                for m in re.finditer(r'(?:title|primaryKeyword|keywords):\s*["\[]?([^"\]\n]+)["\]]?', fm_text):
                    val = m.group(1).strip()
                    existing.add(val.replace(" ", ""))
                    # 개별 단어도 추가
                    for w in val.replace(",", " ").split():
                        existing.add(w.strip().lower())
            except Exception:
                pass
    except Exception as e:
        print(f"  [WARN] 기존 앱 목록 로드 실패: {e}")
    return existing


def load_existing_slugs() -> list[str]:
    """기존 앱 slug 목록 반환 (AI에게 전달해 의미적 중복 판단용)"""
    import glob
    return sorted(pathlib.Path(f).stem for f in glob.glob("src/content/apps/*.md"))


# ── 4. AI 전처리 (저관여 앱 가능성 판단) ────────────────────────────────────

def ai_evaluate(candidates: list[dict], naver_data: dict, existing_slugs: list[str]) -> list[dict]:
    """
    AI가 각 키워드에 대해:
    - 저관여 웹앱으로 만들 수 있는지 판단 (외부 API 불필요 기준)
    - 뉴스 맥락으로 키워드 의미 정확히 파악
    - 기존 앱과 의미적 중복 여부 확인
    - 구체적인 앱 아이디어 제안
    """
    n = len(candidates)
    print(f"[3/3] AI 앱 가능성 평가 중...")
    print(f"      키워드 {n}개를 Claude/Gemini에 전달 중...")
    print(f"      (API 응답까지 10~30초 소요될 수 있습니다)", flush=True)
    t0 = time.time()

    try:
        import scripts.lib.ai_client as ai_client
    except ImportError:
        print("  [ERROR] ai_client 임포트 실패")
        return candidates

    kw_list = []
    for item in candidates:
        kw = item["keyword"]
        n  = naver_data.get(kw, {})
        kw_list.append({
            "keyword":       kw,
            "google_traffic": item.get("traffic", "N/A"),
            "news_context":   item.get("news_title", "")[:120],  # 더 긴 맥락 전달
            "naver_recent":   n.get("recent_avg", "N/A"),
            "naver_rise_pct": n.get("rise_rate_pct", "N/A"),
        })

    SYSTEM = f"""너는 한국 저관여 웹앱 기획 전문가다.
입력: 한국 실시간 트렌딩 키워드 목록 (JSON 배열)
출력: 각 키워드에 대해 아래 필드들'만' 포함하는 JSON 배열. (입력받은 news_context, traffic 등 원본 데이터는 절대 다시 출력하지 마라). 설명 없이 JSON만 반환.

## 중요: 키워드 의미 파악
- news_context(뉴스 헤드라인)를 반드시 읽고 키워드의 실제 의미를 파악하라.
- 예: "천궁" + 뉴스에 "미사일/방산" → 한국 방공 미사일 시스템 / "천궁" + 뉴스에 "별자리" → 천문학
- 동음이의어나 중의적 단어는 반드시 뉴스 맥락으로 판단하라.

## 출력 JSON 객체의 필수 필드:
- "keyword": 원본 키워드
- "appifiable": true/false
- "reason": 한 줄 이유 (이미 유사 앱 존재 시 명시)
- "app_idea": 앱 아이디어 (appifiable=true, 구체적으로 한 줄)
- "app_type": "calculator" | "quiz" | "tool" | "fun" | "datetime" | "finance" 중 하나
- "slug_hint": 영문 소문자 하이픈 slug
- "duplicate_of": 기존 앱과 중복이면 해당 slug 문자열, 아니면 반드시 null

## 중요: 모든 필드는 반드시 값이 있어야 합니다
- appifiable=false 인 항목: app_idea=null, app_type=null, slug_hint=null
- 값이 없을 때 빈 문자열("") 금지. 반드시 null 사용
- 필드를 생략하거나 값 없이 콜론만 쓰는 것 절대 금지 (예: "app_type": → 오류)

## 기존 서비스 중인 앱 slug 목록 (이와 의미가 겹치면 appifiable=false):
{chr(10).join(existing_slugs)}

## appifiable=false 기준:
- 연예인 이름, 드라마/영화 제목, 뉴스 사건, 스포츠 경기 결과, 특정 인물/브랜드
- 기존 앱 목록과 의미적으로 동일하거나 매우 유사한 기능 (예: 이미 이자 계산기 있으면 또 만들 필요 없음)
- 외부 실시간 API(날씨, 지도, 공공 데이터 등) 없이 구현 불가능한 도구
  예) 실시간 기상 시뮬레이터, 실시간 교통 안내, 주가 조회

## appifiable=true 기준 (순수 JavaScript만으로 구현 가능한 것):
- 숫자 입력 → 계산 결과 출력 (세금, 이자, 건강지수, 날짜, 부동산 비용 등)
- 퀴즈/테스트/성향 진단 (정적 데이터로 운영 가능한 것)
- 생성기/추첨기 (로또, 랜덤 등)
- 부동산 관련: 취득세 계산기, 청약 가점 계산기, 전월세 전환율 계산기 등 (공식 기반)
- 건강/생활: BMI, 칼로리, 수면 시간 계산 등
- 금융: 복리 계산, 적금 이자, 환율 환산 등 (실시간 환율 불필요 — 직접 입력)"""

    user_input = json.dumps(kw_list, ensure_ascii=False)

    try:
        text = ai_client.call(
            task="keyword_scoring",
            system=SYSTEM,
            user=user_input,
            max_tokens=4000,
            log_label="trend_collector:ai_eval",
        )
        cleaned = text.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        elif cleaned.startswith("```"):   cleaned = cleaned[3:]
        if cleaned.endswith("```"):       cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # JSON 자동 복구: 값 없이 끊긴 필드 처리 (예: "app_type":  → "app_type": null)
        import re as _re
        cleaned = _re.sub(r':\s*([,}\]])', r': null\1', cleaned)
        # 배열이 닫히지 않은 경우 닫기
        if cleaned.count('[') > cleaned.count(']'):
            cleaned = cleaned.rstrip().rstrip(',') + "\n]"

        # JSON 파싱
        result = json.loads(cleaned)
        
        # 원본 데이터와 AI 평가 결과 병합
        final_result = []
        for orig in kw_list:  # use kw_list since it has google_traffic, naver_rise_pct
            kw = orig["keyword"]
            ai_item = next((x for x in result if x.get("keyword") == kw), None)
            merged = orig.copy()
            if ai_item:
                merged.update(ai_item)
            else:
                merged["appifiable"] = None
                merged["reason"] = "AI 누락"
            final_result.append(merged)
            
        print(f"      완료 ({time.time()-t0:.1f}초) — 앱 제작 가능: {sum(1 for x in final_result if x.get('appifiable'))}개")
        return final_result

    except Exception as e:
        print(f"  [WARN] AI 평가 실패 ({e})")
        # 디버그: AI가 반환한 원문 일부 출력
        try:
            print(f"  [DEBUG] AI 원문 앞 300자: {text[:300]}")
        except Exception:
            pass
        print("  원본 키워드 목록을 그대로 반환합니다.")
        for item in candidates:
            item["appifiable"] = None
            item["reason"]     = "AI 미처리"
            item["app_idea"]   = ""
            item["app_type"]   = ""
            item["slug_hint"]  = ""
            item["duplicate_of"] = None
        return candidates


# ── 5. 터미널 출력 + 사용자 선택 ────────────────────────────────────────────

def display_and_select(items: list[dict]) -> list[dict]:
    """
    앱 제작 가능 후보를 번호 매겨 터미널에 출력하고,
    사용자가 원하는 번호(들)를 입력하면 해당 항목 반환.
    """
    appifiable = [x for x in items if x.get("appifiable") is True]

    if not appifiable:
        print("\n[!] 앱 제작 가능한 후보가 없습니다.")
        return []

    print("\n" + "=" * 65)
    print("  저관여 앱 후보 목록")
    print("=" * 65)
    for i, item in enumerate(appifiable, 1):
        kw      = item.get("keyword", "")
        idea    = item.get("app_idea", "")
        atype   = item.get("app_type", "")
        g_traf  = item.get("google_traffic", "N/A")
        n_rise  = item.get("naver_rise_pct", "N/A")
        n_rise_str = f"{n_rise:+.1f}%" if isinstance(n_rise, (int, float)) else str(n_rise)
        slug    = item.get("slug_hint", "")

        print(f"\n  [{i}] {kw}  (Google: {g_traf} / Naver상승: {n_rise_str})")
        print(f"       타입  : {atype}")
        print(f"       아이디어: {idea}")
        print(f"       slug  : {slug}")

    print("\n" + "=" * 65)
    print("  참고 — 앱으로 만들기 어려운 키워드:")
    not_app = [x for x in items if x.get("appifiable") is False]
    for x in not_app:
        print(f"    ✗ {x['keyword']} — {x.get('reason','')}")
    print("=" * 65)

    print("\n원하는 앱 번호를 선택하세요 (예: 1  또는  1,3  또는  skip):")
    raw = input("  > ").strip()

    if not raw or raw.lower() == "skip":
        print("  건너뜁니다.")
        return []

    selected = []
    for part in raw.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < len(appifiable):
                selected.append(appifiable[idx])
        except ValueError:
            pass

    return selected


# ── 6. 리포트 저장 ────────────────────────────────────────────────────────────

def save_report(all_items: list[dict], selected: list[dict]) -> pathlib.Path:
    today    = datetime.date.today().isoformat()
    out_path = REPORT_DIR / f"trend-report-{today}.md"

    lines = [
        f"# GoolAPP 트렌드 리포트 — {today}",
        "",
        "> Google Trends RSS + Naver DataLab API 기반 자동 수집",
        f"> 생성 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # 선택된 앱
    if selected:
        lines += ["## ✅ 선택된 앱 후보", ""]
        for item in selected:
            kw   = item.get("keyword", "")
            idea = item.get("app_idea", "")
            slug = item.get("slug_hint", "")
            lines.append(f"### {kw}")
            lines.append(f"- **아이디어**: {idea}")
            lines.append(f"- **slug**: `{slug}`")
            lines.append(f"- **타입**: {item.get('app_type','')}")
            lines.append(f"- **Google 트래픽**: {item.get('google_traffic','N/A')}")
            n_rise = item.get('naver_rise_pct', 'N/A')
            n_rise_str = f"{n_rise:+.1f}%" if isinstance(n_rise, (int,float)) else str(n_rise)
            lines.append(f"- **Naver 상승률**: {n_rise_str}")
            lines.append("")
        lines += [
            "---",
            "",
            "### 다음 단계",
            "```",
        ]
        for item in selected:
            kw   = item.get("keyword", "")
            slug = item.get("slug_hint", "")
            lines.append(f'python scripts/new_app_pipeline.py "{kw}" {slug}')
        lines += ["```", ""]

    # 전체 후보 목록
    appifiable = [x for x in all_items if x.get("appifiable") is True]
    not_app    = [x for x in all_items if x.get("appifiable") is False]

    lines += [
        "---",
        "",
        f"## 전체 앱 제작 가능 후보 ({len(appifiable)}개)",
        "",
        "| # | 키워드 | 타입 | 아이디어 | Google | Naver상승% |",
        "|---|--------|------|----------|--------|-----------|",
    ]
    for i, item in enumerate(appifiable, 1):
        kw      = item.get("keyword","")
        idea    = item.get("app_idea","")
        atype   = item.get("app_type","")
        g_traf  = item.get("google_traffic","N/A")
        n_rise  = item.get("naver_rise_pct","N/A")
        n_str   = f"{n_rise:+.1f}%" if isinstance(n_rise,(int,float)) else str(n_rise)
        lines.append(f"| {i} | **{kw}** | {atype} | {idea} | {g_traf} | {n_str} |")

    lines += ["", f"## 앱으로 만들기 어려운 키워드 ({len(not_app)}개)", ""]
    for item in not_app:
        lines.append(f"- {item['keyword']} — {item.get('reason','')}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ── 메인 ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 65)
    print("  GoolAPP 트렌드 수집기 v2")
    print("  Google Trends RSS + Naver DataLab → 앱 후보 제안")
    print("=" * 65)

    # 1. 트렌드 수집 (Google + Nate)
    google_items = collect_google_trends_rss()
    nate_items   = collect_nate_trends()
    
    # 중복 키워드 병합 (Google 우선)
    combined_items = list(google_items)
    seen_kws = {x["keyword"].replace(" ", "") for x in combined_items}
    for item in nate_items:
        if item["keyword"].replace(" ", "") not in seen_kws:
            combined_items.append(item)
            seen_kws.add(item["keyword"].replace(" ", ""))

    if not combined_items:
        print("[!] 트렌드 수집 실패. 네트워크를 확인하세요.")
        return

    # 2. 기존 앱과 중복 제거 (텍스트 기반 1차 필터)
    existing      = load_existing_keywords()
    existing_slugs = load_existing_slugs()
    
    # 2.5 후보가 너무 적을 경우 YAML 파일에서 고정 키워드 추가 (최소 15~20개 확보)
    try:
        import yaml, random
        yaml_path = pathlib.Path("references/seo/keyword-candidates.yaml")
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                seeds = yaml.safe_load(f)
            # 이미 기존 앱이거나 combined_items에 있는 것 제외
            current_kws = {x["keyword"].replace(" ", "") for x in combined_items}
            seeds_filtered = [s for s in seeds if s.replace(" ", "") not in existing and s.replace(" ", "") not in current_kws]
            
            # 부족한 만큼 채우기 (최대 10개 랜덤 추가)
            add_count = max(0, 15 - len(combined_items))
            if add_count > 0 and seeds_filtered:
                to_add = random.sample(seeds_filtered, min(add_count, len(seeds_filtered)))
                for kw in to_add:
                    combined_items.append({"keyword": kw, "traffic": "N/A", "news_title": "기본 제공 아이디어 (트렌드 외)"})
                print(f"  → 트렌드 키워드 부족으로 예비 후보 {len(to_add)}개 추가")
    except Exception as e:
        print(f"  [WARN] 예비 후보 추가 실패: {e}")

    filtered = [x for x in combined_items if x["keyword"].replace(" ","") not in existing]
    print(f"  기존 앱 1차 필터링: {len(combined_items)}개 → {len(filtered)}개 (나머지는 AI가 의미적 중복 재확인)")

    if not filtered:
        print("[!] 새로운 키워드가 없습니다 (모두 기존 앱과 중복).")
        return

    # 3. Naver DataLab 교차검증
    kw_list    = [x["keyword"] for x in filtered]
    naver_data = collect_naver_trends(kw_list)

    # 4. AI 평가 (existing_slugs 전달 → 의미적 중복도 판단)
    evaluated = ai_evaluate(filtered, naver_data, existing_slugs)

    # 5. 터미널 출력 + 사용자 선택
    selected = display_and_select(evaluated)

    # 6. 리포트 저장
    out_path = save_report(evaluated, selected)
    print(f"\n✅ 리포트 저장: {out_path}")

    if selected:
        print("\n[다음 단계] 선택한 앱을 만들려면:")
        for item in selected:
            kw   = item.get("keyword","")
            slug = item.get("slug_hint","")
            print(f'  python scripts/new_app_pipeline.py "{kw}" {slug}')
    print()


if __name__ == "__main__":
    run()
