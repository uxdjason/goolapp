"""
Phase 4-1: trend keyword collector
- Google Trends (trending_searches + interest_over_time) -- primary
- Naver DataLab API -- always run in parallel, cross-validation
- Output: references/reports/trend-report-YYYY-MM-DD.md
- AI does minimal preprocessing only (filter junk + app idea hints)
- User reviews report and selects final keywords
"""# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
import os
import pathlib
import datetime
import time
import sys

root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

OUT_DIR = pathlib.Path("references/reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (기존 하드코딩된 앱 목록은 동적 파싱으로 대체)
# ── Google Trends ────────────────────────────────────────────────────────────

def collect_google_trends() -> dict:
    """Google Trends에서 한국 실시간 트렌딩 키워드 수집."""
    result = {"trending": [], "interest": {}, "error": None}
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="ko-KR", tz=540, timeout=(10, 30), retries=2, backoff_factor=0.5)

        # 1. 한국 실시간 트렌딩 검색어
        print("[Google Trends] 실시간 트렌딩 수집 중...")
        trending_df = pt.trending_searches(pn="south_korea")
        trending_kws = trending_df[0].tolist()[:50]  # 상위 50개
        result["trending"] = trending_kws
        print(f"  → {len(trending_kws)}개 트렌딩 키워드 수집 완료")

        # 2. 상위 20개에 대해 90일 추이 조회 (배치 5개씩)
        print("[Google Trends] 검색량 추이 조회 중...")
        top20 = trending_kws[:20]
        interest_map = {}
        for i in range(0, len(top20), 5):
            batch = top20[i:i+5]
            try:
                pt.build_payload(batch, geo="KR", timeframe="today 3-m")
                df = pt.interest_over_time()
                if not df.empty:
                    for kw in batch:
                        if kw in df.columns:
                            vals = df[kw].tolist()
                            recent_avg = sum(vals[-4:]) / max(len(vals[-4:]), 1)
                            prev_avg = sum(vals[:8]) / max(len(vals[:8]), 1)
                            rise_rate = round((recent_avg - prev_avg) / max(prev_avg, 1) * 100, 1)
                            interest_map[kw] = {
                                "recent_avg": round(recent_avg, 1),
                                "rise_rate_pct": rise_rate,
                            }
                time.sleep(1)  # rate limit 방지
            except Exception as e:
                print(f"  [WARN] 배치 {batch} 추이 조회 실패: {e}")
        result["interest"] = interest_map
        print(f"  → {len(interest_map)}개 추이 데이터 수집 완료")

    except ImportError:
        result["error"] = "pytrends 미설치. `pip install pytrends` 실행 후 재시도."
        print(f"  [ERROR] {result['error']}")
    except Exception as e:
        result["error"] = str(e)
        print(f"  [ERROR] Google Trends 수집 실패: {e}")

    return result


# ── Naver DataLab ────────────────────────────────────────────────────────────

def collect_naver_trends(keywords: list[str]) -> dict:
    """Naver DataLab API로 키워드 검색량 추이 조회."""
    result = {"interest": {}, "error": None}
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        result["error"] = "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수 없음"
        print(f"  [ERROR] {result['error']}")
        return result

    if not keywords:
        result["error"] = "조회할 키워드 없음"
        return result

    try:
        import httpx

        # DataLab은 한 번에 최대 5개 키워드 그룹 비교
        # 키워드를 5개씩 배치로 나눠 조회
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=90)
        interest_map = {}

        for i in range(0, min(len(keywords), 20), 5):
            batch = keywords[i:i+5]
            keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in batch]

            payload = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": "week",
                "keywordGroups": keyword_groups,
                "device": "",
                "ages": [],
                "gender": "",
            }

            resp = httpx.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers={
                    "X-Naver-Client-Id": client_id,
                    "X-Naver-Client-Secret": client_secret,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                kw = item["title"]
                ratios = [d["ratio"] for d in item.get("data", [])]
                if ratios:
                    recent_avg = sum(ratios[-4:]) / max(len(ratios[-4:]), 1)
                    prev_avg = sum(ratios[:8]) / max(len(ratios[:8]), 1)
                    rise_rate = round((recent_avg - prev_avg) / max(prev_avg, 1) * 100, 1)
                    interest_map[kw] = {
                        "recent_avg": round(recent_avg, 1),
                        "rise_rate_pct": rise_rate,
                    }
            time.sleep(0.3)

        result["interest"] = interest_map
        print(f"  → Naver: {len(interest_map)}개 추이 데이터 수집 완료")

    except Exception as e:
        result["error"] = str(e)
        print(f"  [ERROR] Naver DataLab 수집 실패: {e}")

    return result


# ── AI 최소 전처리 ────────────────────────────────────────────────────────────

def ai_preprocess(keywords: list[str], google_interest: dict, naver_interest: dict) -> list[dict]:
    """
    AI가 최소한의 전처리만 수행:
    - 연예인/뉴스/스포츠 등 '앱화 불가' 키워드 표시
    - 각 키워드에 앱 아이디어 힌트 제안
    - 기존 앱과의 유사도 표시
    사용자가 이 결과를 보고 최종 선택함.
    """
    import scripts.lib.ai_client as ai_client

    SYSTEM = """너는 한국어 저관여 웹앱 기획자다.
입력은 한국 트렌딩 검색어 목록 (JSON 배열).
각 키워드에 대해 아래 JSON 배열을 반환한다. 설명 없이 JSON만.

출력 형식 (배열):
[
  {
    "keyword": "원본 키워드",
    "appifiable": true/false,  // 저관여 웹앱으로 구현 가능한가?
    "reason": "한 줄 이유 (앱화 불가인 경우 명확히)",
    "app_idea": "가능한 앱 아이디어 한 줄 (appifiable=true인 경우만)",
    "app_type": "calculator/quiz/tool/fun/datetime/finance 중 하나"
  }
]

appifiable=false 판단 기준:
- 연예인 이름, 드라마/영화 제목, 뉴스 사건, 스포츠 경기 결과
- 특정 상품/브랜드명
- 저관여 앱으로 구현할 수 없는 추상적 개념

appifiable=true 판단 기준:
- 계산기/변환기로 만들 수 있는 것 (세금, 요금, 수치 계산 등)
- 퀴즈/테스트로 만들 수 있는 것
- 생성기/도구로 만들 수 있는 것 (추첨, 생성 등)
- 날짜/시간 관련 도구"""

    user = json.dumps(keywords[:40], ensure_ascii=False)

    def validate_scoring(text: str) -> bool:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            elif cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            json.loads(cleaned.strip())
            return True
        except Exception:
            return False

    try:
        text = ai_client.call(
            task="keyword_scoring",
            system=SYSTEM,
            user=user,
            validator=validate_scoring,
            max_tokens=2048,
            log_label="trend:preprocess",
        )
        cleaned = text.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        elif cleaned.startswith("```"): cleaned = cleaned[3:]
        if cleaned.endswith("```"): cleaned = cleaned[:-3]
        items = json.loads(cleaned.strip())
    except Exception as e:
        print(f"  [WARN] AI 전처리 실패 ({e}), 원본 리스트 사용")
        items = [{"keyword": kw, "appifiable": None, "reason": "AI 미처리", "app_idea": "", "app_type": ""} for kw in keywords[:40]]

    # 트렌드 점수 병합
    for item in items:
        kw = item["keyword"]
        g = google_interest.get(kw, {})
        n = naver_interest.get(kw, {})
        item["google_rise_pct"] = g.get("rise_rate_pct", "N/A")
        item["google_recent_avg"] = g.get("recent_avg", "N/A")
        item["naver_rise_pct"] = n.get("rise_rate_pct", "N/A")
        item["naver_recent_avg"] = n.get("recent_avg", "N/A")

    return items


# ── 리포트 생성 ────────────────────────────────────────────────────────────

def build_report(items: list[dict], google_error: str | None, naver_error: str | None) -> str:
    today = datetime.date.today().isoformat()
    lines = []
    lines.append(f"# GoolAPP 트렌드 리포트 — {today}")
    lines.append("")
    lines.append("> **사용법:** 아래 목록을 검토하고 개발할 키워드를 선택하세요.")
    lines.append("> 선택 후 `python scripts/new_app_pipeline.py \"<키워드>\" <slug>` 실행")
    lines.append("")

    if google_error:
        lines.append(f"> ⚠️ Google Trends 오류: {google_error}")
    if naver_error:
        lines.append(f"> ⚠️ Naver DataLab 오류: {naver_error}")
    if google_error or naver_error:
        lines.append("")

    # ── 앱화 가능 키워드 ──
    appifiable = [x for x in items if x.get("appifiable") is True]
    not_appifiable = [x for x in items if x.get("appifiable") is False]
    unknown = [x for x in items if x.get("appifiable") is None]

    lines.append(f"## ✅ 앱화 가능 후보 ({len(appifiable)}개)")
    lines.append("")
    lines.append("| # | 키워드 | 타입 | 앱 아이디어 | Google상승% | Naver상승% |")
    lines.append("|---|--------|------|-------------|------------|-----------|")
    for i, item in enumerate(appifiable, 1):
        kw = item["keyword"]
        idea = item.get("app_idea", "")
        atype = item.get("app_type", "")
        g_rise = item.get("google_rise_pct", "N/A")
        n_rise = item.get("naver_rise_pct", "N/A")
        g_str = f"{g_rise:+.1f}%" if isinstance(g_rise, (int, float)) else str(g_rise)
        n_str = f"{n_rise:+.1f}%" if isinstance(n_rise, (int, float)) else str(n_rise)
        lines.append(f"| {i} | **{kw}** | {atype} | {idea} | {g_str} | {n_str} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── 앱화 불가 키워드 (참고용) ──
    lines.append(f"## ❌ 앱화 불가 키워드 ({len(not_appifiable)}개, 참고용)")
    lines.append("")
    lines.append("| 키워드 | 이유 |")
    lines.append("|--------|------|")
    for item in not_appifiable:
        lines.append(f"| {item['keyword']} | {item.get('reason', '')} |")

    if unknown:
        lines.append("")
        lines.append(f"## ❓ AI 미처리 ({len(unknown)}개)")
        for item in unknown:
            lines.append(f"- {item['keyword']}")

    lines.append("")
    lines.append("---")
    lines.append(f"*생성 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def run():
    print("=" * 50)
    print("GoolAPP Phase 4 -- Trend Collector Start")
    print("=" * 50)

    # 1. Google Trends
    print("\n[1/3] Google Trends 수집...")
    google = collect_google_trends()

    # 기존 생성된 앱 목록 추출 (중복 제안 방지용)
    existing_kws = set()
    try:
        import glob, yaml
        for fpath in glob.glob("src/content/apps/*.md"):
            content = pathlib.Path(fpath).read_text(encoding="utf-8")
            if "---" in content:
                fm = yaml.safe_load(content.split("---")[1])
                if fm and isinstance(fm, dict):
                    if fm.get("title"): existing_kws.add(fm["title"].replace(" ", ""))
                    if fm.get("primaryKeyword"): existing_kws.add(fm["primaryKeyword"].replace(" ", ""))
    except Exception as e:
        print(f"  [WARN] 기존 앱 목록 추출 중 오류 발생: {e}")

    # 2. Naver DataLab (Google에서 수집된 키워드로 교차 검증, 또는 실패 시 yaml 로드)
    # 중복 키워드는 필터링하여 후보군 구성
    raw_trending = google.get("trending", [])
    candidates = [c for c in raw_trending if c.replace(" ", "") not in existing_kws][:40]
    
    if not candidates:
        print("  [WARN] Google Trends 실시간 트렌드 수집 실패 또는 모두 중복됨. Fallback으로 후보 풀을 로드합니다.")
        try:
            import yaml
            import random
            yaml_path = pathlib.Path("references/seo/keyword-candidates.yaml")
            if yaml_path.exists():
                with open(yaml_path, "r", encoding="utf-8") as f:
                    seeds = yaml.safe_load(f)
                
                # 중복 필터링
                seeds = [s for s in seeds if s.replace(" ", "") not in existing_kws]

                candidates = random.sample(seeds, min(len(seeds), 40))
                print(f"  → yaml 후보 풀에서 중복 제외 후 랜덤 {len(candidates)}개 로드 완료")
            else:
                print("  [ERROR] fallback 파일이 없습니다: references/seo/keyword-candidates.yaml")
        except Exception as e:
            print(f"  [ERROR] fallback 로드 실패: {e}")

    if not candidates:
        print("  [ERROR] 검증할 키워드가 없습니다. 종료합니다.")
        return

    print("\n[2/3] Naver DataLab 교차 검증...")
    naver = collect_naver_trends(candidates)

    # 3. AI 전처리
    print("\n[3/3] AI 전처리 (앱화 가능성 판단)...")
    items = ai_preprocess(candidates, google.get("interest", {}), naver.get("interest", {}))

    # 4. 리포트 생성
    report = build_report(items, google.get("error"), naver.get("error"))
    today = datetime.date.today().isoformat()
    out_path = OUT_DIR / f"trend-report-{today}.md"
    out_path.write_text(report, encoding="utf-8")

    print(f"\n{'=' * 50}")
    print(f"✅ 리포트 저장 완료: {out_path}")
    print(f"   앱화 가능 후보: {len([x for x in items if x.get('appifiable')])}개")
    print(f"   → 리포트를 열어 원하는 키워드를 선택하세요.")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    run()
