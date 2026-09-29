"""
Phase 4-2 (v2): 신규 앱 자동 생성 파이프라인
──────────────────────────────────────────────────────────────────────
변경 이력:
  v1: 기본 6단계 파이프라인 (spec → SEO → longform → astro → build → blog)
  v2: P1-2 요구사항 구현
      - --queries "q1,q2,..." 옵션: 연관 검색어 묶음을 SEO/롱폼/FAQ에 전달
      - --extend <기존slug> 옵션: 기존 앱 기능 확장 모드 (초안만 생성, 파일 수정 안내)
      - code_generation_system.md에 광고 배치 규칙·CLS 방지 규칙 적용
      - 롱폼 분량: 고정 7,000자 → 검색 의도에 맞는 2,500~4,000자
      - FAQ 질문: --queries의 실제 검색어 문장형에서 생성
      - 완료 체크리스트: 블로그 발행 + GSC 색인 요청 + 네이버 서치어드바이저 안내

사용법:
  # 신규 앱 제작 (기본)
  python scripts/new_app_pipeline.py "<타깃 검색어>" <slug>

  # 연관 검색어 묶음 포함
  python scripts/new_app_pipeline.py "학점 환산기" gpa-converter \\
      --queries "gpa 환산,4.3 4.5 환산,학점 변환기,4.3 학점 표"

  # 기존 앱 확장 모드 (초안 생성, 수동 적용)
  python scripts/new_app_pipeline.py "다주택자 보유세" property-holding-tax-calculator \\
      --queries "다주택자 보유세 계산기,다주택 종부세" \\
      --extend property-holding-tax-calculator
──────────────────────────────────────────────────────────────────────
"""  # noqa: E501
# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import json
import pathlib
import subprocess
import sys
import time
import datetime

root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
load_dotenv()

import scripts.lib.ai_client as ai_client


def slugify(text: str) -> str:
    """간단한 slug 변환 (영문 입력 전제)."""
    return text.lower().strip().replace(" ", "-")


def _repair_json(s: str) -> str:
    """잘린 JSON을 닫아서 파싱 가능하게 복구 시도."""
    s = s.strip()
    open_braces = s.count('{') - s.count('}')
    open_brackets = s.count('[') - s.count(']')
    while s.endswith(','):
        s = s.rstrip().rstrip(',')
    for _ in range(open_brackets):
        s += ']'
    for _ in range(open_braces):
        s += '}'
    return s


def is_quiz_app(slug: str, keyword: str = "", category: str = "") -> bool:
    """슬러그, 키워드, 카테고리로 퀴즈 앱 여부를 판단한다."""
    if category == "quiz":
        return True
    if slug.endswith("-quiz") or "-quiz-" in slug:
        return True
    if "퀴즈" in keyword or "quiz" in keyword.lower():
        return True
    return False


def _quiz_json_filename(slug: str) -> str:
    """slug → JSON 파일명 변환."""
    return slug.replace("-", "_")


# ── Step 1: 앱 사양 생성 ───────────────────────────────────────────────────────

def step1_generate_spec(keyword: str, slug: str, queries: list[str]) -> dict:
    """키워드 + 연관 검색어로부터 앱 사양 JSON 생성."""
    print(f"\n[Step 1/6] 앱 사양 생성: '{keyword}'", flush=True)

    quiz_hint = ""
    if is_quiz_app(slug, keyword):
        quiz_hint = """
이 앱은 퀴즈 앱이다. 반드시 아래 조건을 지켜라:
- category는 반드시 "quiz"로 설정
- inputs: ["퀴즈 시작 버튼"]
- outputs: ["정오답 피드백", "점수", "결과 화면"]
- js_logic_summary: "JSON URL에서 문항 데이터를 fetch → 4지선다 퀴즈 진행 → 정오답 판정 → 결과 표시"
- json_data_filename: 퀴즈 JSON 파일명 (확장자 없이, 예: semiconductor_quiz)
- quiz_topic: 퀴즈 주제 한국어 설명 (문항 생성에 사용)
- quiz_prompt: 퀴즈 화면에서 보여줄 질문 문구 (예: "다음 설명에 해당하는 반도체 용어는?")
"""

    queries_hint = ""
    if queries:
        queries_hint = f"""
연관 검색어 묶음 (이 검색어들을 찾는 사람들을 위한 앱이다):
{chr(10).join(f'- {q}' for q in queries)}
"""

    SYSTEM = """너는 한국어 저관여 웹앱 기획자다.
입력 키워드로부터 GoolAPP에 추가할 앱의 사양을 JSON으로 반환한다.
JSON만 반환, 설명 없이.

출력 키:
- title: 앱 이름 (한국어, 예: "환율 계산기")
- slug: URL slug (영어 소문자 하이픈, 예: "exchange-rate-calculator")
- category: "calculator" | "quiz" | "tool" | "fun" | "datetime" | "finance" 중 하나
- core_function: 앱의 핵심 기능 2~3문장 설명
- inputs: 사용자가 입력하는 값 목록 (배열)
- outputs: 앱이 계산/출력하는 값 목록 (배열)
- features: 주요 기능 목록 3~5개 (배열)
- js_logic_summary: 핵심 계산 로직 의사코드 요약 (간결하게, 200자 이내)
- target_queries: 이 앱이 타깃하는 검색어 목록 (연관 검색어 묶음 포함, 배열)""" + quiz_hint

    user_msg = f"키워드: {keyword}\nslug: {slug}{queries_hint}"

    print(f"  → AI 호출 중 (앱 사양 JSON 생성)...")
    text = ai_client.call(
        task="semantic_analysis",
        system=SYSTEM,
        user=user_msg,
        max_tokens=2048,
        log_label=f"new_app:spec:{slug}",
    )
    cleaned = text.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    try:
        spec = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"  ⚠ JSON 파싱 실패 — 자동 복구 시도 중...")
        repaired = _repair_json(cleaned)
        spec = json.loads(repaired)
        print(f"  ✓ JSON 자동 복구 성공")

    # 퀴즈 앱 기본값
    if is_quiz_app(slug, keyword, spec.get("category", "")):
        spec.setdefault("category", "quiz")
        spec.setdefault("json_data_filename", _quiz_json_filename(slug))
        spec.setdefault("quiz_topic", spec.get("core_function", keyword))
        spec.setdefault("quiz_prompt", "다음 문제를 풀어보세요.")

    # target_queries 기본값
    spec.setdefault("target_queries", queries)

    wrapped = {
        "app": {
            "title": spec.get("title", keyword),
            "slug": slug,
            "category": spec.get("category", "tool"),
            "legacy_url": f"https://goolapp.com/{slug}/",
        },
        "parsed": {
            "meta": {"title": spec.get("title", keyword), "description": ""},
            "body_text": "",
            "inline_scripts": [],
            "external_scripts": [],
            "interactive": {"inputs": spec.get("inputs", []), "buttons": []},
        },
        "analysis": {
            "core_function": spec.get("core_function", ""),
            "io_contract": {"inputs": spec.get("inputs", []), "outputs": spec.get("outputs", [])},
            "js_logic_summary": spec.get("js_logic_summary", ""),
            "external_deps": [],
            "content_blocks": [],
            "faq_candidates": [],
            "astro_migration_notes": "신규 앱 — legacy 없음",
        },
        "_new_app_spec": spec,
        "_target_queries": queries,  # --queries 인수 보존
    }

    out_dir = pathlib.Path("references/legacy-extracts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.json"
    out_path.write_text(json.dumps(wrapped, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ 앱 사양 생성: {out_path}")
    return wrapped


# ── Step 1b: 퀴즈 JSON 생성 ───────────────────────────────────────────────────

def step1b_generate_quiz_json(slug: str, wrapped_spec: dict) -> str:
    """퀴즈 앱 전용 — 4지선다 문항 JSON 생성."""
    print(f"\n[Step 1b] 퀴즈 문항 JSON 생성...", flush=True)

    spec = wrapped_spec.get("_new_app_spec", {})
    json_data_filename = spec.get("json_data_filename", _quiz_json_filename(slug))
    quiz_topic = spec.get("quiz_topic", spec.get("core_function", slug))
    title = spec.get("title", slug)

    SYSTEM = """너는 한국어 퀴즈 데이터 전문가다.
주어진 주제에 대해 4지선다 퀴즈 문항을 JSON 배열로 생성한다.
순수 JSON 배열만 반환하고, 설명·마크다운 코드블록 없이 출력한다.

각 항목 형식 (반드시 준수):
{"quiz": "문제 텍스트", "selection": ["선택지1","선택지2","선택지3","선택지4"], "answer": 정답번호}

규칙:
- answer는 selection 배열의 1-based 인덱스 (1~4 사이 정수)
- selection은 반드시 4개
- 문항은 너무 쉽거나 너무 어렵지 않게 — 일반 성인이 도전할 수 있는 수준
- 정답 위치가 1,2,3,4에 고르게 분포되도록 작성
- 모든 텍스트는 한국어로 작성 (영문 고유명사는 그대로 사용 가능)
- 중복 문항 없이 30개 생성"""

    user_prompt = f"""주제: {title} ({quiz_topic})
위 주제에 대한 4지선다 퀴즈 문항 30개를 JSON 배열로 생성하라.
문항 예시:
{{"quiz": "반도체 공정에서 웨이퍼의 불순물을 제거하는 공정은?", "selection": ["세정 공정","식각 공정","증착 공정","포토 공정"], "answer": 1}}
"""

    def validate_quiz_json(text: str) -> bool:
        t = text.strip()
        if t.startswith("```"): t = t.split("\n", 1)[-1]
        if t.endswith("```"): t = t.rsplit("```", 1)[0]
        try:
            data = json.loads(_repair_json(t.strip()))
            return isinstance(data, list) and len(data) >= 20
        except Exception:
            return False

    print(f"  → AI 호출 중 (퀴즈 문항 30개 생성)...", flush=True)
    text = ai_client.call(
        task="semantic_analysis",
        system=SYSTEM,
        user=user_prompt,
        validator=validate_quiz_json,
        max_tokens=4096,
        log_label=f"quiz_json:{slug}",
    )

    cleaned = text.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        quiz_data = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"  ⚠ JSON 파싱 실패 — 자동 복구 시도 중...")
        quiz_data = json.loads(_repair_json(cleaned))

    valid_items = [
        item for item in quiz_data
        if (isinstance(item, dict)
            and "quiz" in item
            and "selection" in item
            and "answer" in item
            and isinstance(item["selection"], list)
            and len(item["selection"]) == 4
            and isinstance(item["answer"], int)
            and 1 <= item["answer"] <= 4)
    ]
    if len(valid_items) < 10:
        raise ValueError(f"유효한 퀴즈 문항이 너무 적습니다: {len(valid_items)}개")

    out_dir = pathlib.Path("public/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{json_data_filename}.json"
    out_path.write_text(json.dumps(valid_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ 퀴즈 문항 {len(valid_items)}개 저장: {out_path}")
    return json_data_filename


# ── Step 2: SEO 메타 생성 (--queries 반영) ───────────────────────────────────

def step2_generate_seo(slug: str, queries: list[str]) -> dict:
    """SEO 메타데이터 생성. queries를 extract JSON에 주입하여 검색어 최적화."""
    print(f"\n[Step 2/6] SEO 메타 생성...", flush=True)
    print(f"  → AI 호출 중 (SEO 메타데이터 작성)...", flush=True)

    # extract JSON에 queries 정보 주입
    extract_path = pathlib.Path(f"references/legacy-extracts/{slug}.json")
    if extract_path.exists():
        app_data = json.loads(extract_path.read_text(encoding="utf-8"))
        app_data["_target_queries"] = queries
        extract_path.write_text(json.dumps(app_data, ensure_ascii=False, indent=2), encoding="utf-8")

    from scripts.seo_meta_generator import generate_seo_meta
    seo = generate_seo_meta(slug)
    out_dir = pathlib.Path("references/seo_meta")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.json").write_text(json.dumps(seo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ SEO 메타 생성 완료")
    return seo


# ── Step 3: 롱폼 콘텐츠 생성 (--queries 반영, 분량 최적화) ───────────────────

def step3_generate_longform(slug: str, queries: list[str]) -> str:
    """롱폼 콘텐츠 생성. queries를 실제 FAQ 질문으로 활용."""
    print(f"\n[Step 3/6] 롱폼 콘텐츠 생성...", flush=True)
    print(f"  → AI 호출 중 (한국어 롱폼 본문 작성, 시간이 걸릴 수 있습니다)...", flush=True)

    # extract JSON에 queries 업데이트 (longform_writer가 읽음)
    extract_path = pathlib.Path(f"references/legacy-extracts/{slug}.json")
    if extract_path.exists():
        app_data = json.loads(extract_path.read_text(encoding="utf-8"))
        app_data["_target_queries"] = queries
        extract_path.write_text(json.dumps(app_data, ensure_ascii=False, indent=2), encoding="utf-8")

    from scripts.longform_writer import generate_longform
    longform = generate_longform(slug)
    out_dir = pathlib.Path("references/longform")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.md").write_text(longform, encoding="utf-8")
    print(f"  ✓ 롱폼 콘텐츠 생성 완료 ({len(longform)}자)")
    return longform


# ── Step 4: Astro 컴포넌트 생성 ───────────────────────────────────────────────

def step4_generate_astro(slug: str) -> None:
    """Astro 앱 컴포넌트 생성."""
    print(f"\n[Step 4/6] Astro 컴포넌트 생성...", flush=True)
    print(f"  → AI 호출 중 (Astro/JS 코드 생성, 가장 오래 걸립니다)...", flush=True)
    from scripts.app_generator import generate_app
    generate_app(slug)
    print(f"  ✓ Astro 컴포넌트 생성 완료")


# ── Step 5: 빌드 검증 ─────────────────────────────────────────────────────────

def step5_build_check() -> bool:
    """npm run build로 빌드 검증."""
    print(f"\n[Step 5/6] 빌드 검증 (npm run build)...", flush=True)
    print(f"  → 빌드 실행 중 (수십 초 소요)...", flush=True)
    result = subprocess.run(
        "npm run build", shell=True,
        capture_output=True, text=True, cwd=str(root_dir),
        encoding="utf-8", errors="replace"
    )
    if result.returncode == 0:
        print(f"  ✓ 빌드 검증 성공")
        return True
    else:
        print(f"  ✗ 빌드 실패")
        print(result.stdout[-2000:])
        print(result.stderr[-1000:])
        return False


# ── Step 6: 네이버 블로그 초안 생성 ──────────────────────────────────────────

def step6_generate_blog(slug: str) -> None:
    """네이버 블로그 초안 생성."""
    print(f"\n[Step 6/6] 네이버 블로그 초안 생성...", flush=True)
    print(f"  → AI 호출 중 (블로그 포스팅 초안 작성)...", flush=True)
    from scripts.blog_writer import generate_blog_post
    post = generate_blog_post(slug)
    today = datetime.date.today().isoformat()
    out_dir = pathlib.Path("references/naver-blog-posting")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}-{slug}.md"
    out_path.write_text(post, encoding="utf-8")
    print(f"  ✓ 블로그 초안 생성: {out_path}")


# ── [--extend] 기존 앱 확장 초안 생성 ────────────────────────────────────────

def run_extend_mode(keyword: str, slug: str, extend_slug: str, queries: list[str]) -> None:
    """
    기존 앱에 기능·섹션을 추가하는 확장 모드.
    신규 페이지를 만들지 않고, 기존 앱 수정 가이드를 references/extend-drafts/{slug}.md에 저장.
    """
    pipeline_start = time.time()
    print("=" * 60)
    print(f"GoolAPP 기존 앱 확장 모드")
    print(f"  타깃    : {keyword}")
    print(f"  slug    : {slug}")
    print(f"  기존 앱 : {extend_slug}")
    print(f"  연관 검색어: {', '.join(queries)}")
    print("=" * 60)

    # 기존 앱 파일 읽기
    existing_astro = pathlib.Path(f"src/pages/{extend_slug}/index.astro")
    existing_content = pathlib.Path(f"src/content/apps/{extend_slug}.md")

    existing_code = existing_astro.read_text(encoding="utf-8") if existing_astro.exists() else "(파일 없음)"
    existing_md = existing_content.read_text(encoding="utf-8") if existing_content.exists() else "(파일 없음)"

    queries_str = "\n".join(f"- {q}" for q in queries)

    SYSTEM = """너는 한국어 저관여 웹앱(GoolAPP) 수석 개발자다.
기존 Astro 앱에 새로운 기능이나 섹션을 추가하는 구체적인 수정 가이드를 제공한다.
Markdown 형식으로 명확하게 작성한다.

포함 사항:
1. 타깃 검색어 분석 — 어떤 사용자가 무엇을 원하는지
2. 기존 앱 변경 요약 (파일별, 변경 사항별)
3. src/pages/{slug}/index.astro 수정 — UI 변경사항 코드 스니펫 포함
4. src/content/apps/{slug}.md 수정 — Frontmatter 변경 + Longform 추가 섹션
5. 네이버 블로그 포스팅 초안 (기존 앱의 새 기능 각도로)
6. 완료 체크리스트"""

    user_msg = f"""타깃 검색어: {keyword}
slug: {slug}
기존 앱 slug: {extend_slug}

연관 검색어 (이 검색어들을 찾는 사용자를 위한 기능 추가):
{queries_str}

기존 Astro 컴포넌트 코드 (앞 100줄):
```astro
{existing_code[:3000]}
```

기존 Content MD (앞 50줄):
```markdown
{existing_md[:2000]}
```

위 기존 앱에 연관 검색어를 커버하는 기능을 추가하는 수정 가이드를 작성해줘."""

    print("\n→ AI 호출 중 (기존 앱 확장 가이드 생성)...", flush=True)
    text = ai_client.call(
        task="semantic_analysis",
        system=SYSTEM,
        user=user_msg,
        max_tokens=8000,
        log_label=f"extend:{slug}",
    )

    out_dir = pathlib.Path("references/extend-drafts")
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    out_path = out_dir / f"{today}-extend-{slug}.md"
    out_path.write_text(text, encoding="utf-8")

    elapsed = int(time.time() - pipeline_start)
    print("\n" + "=" * 60)
    print(f"✅ 확장 가이드 생성 완료! (소요: {elapsed}초)")
    print(f"   가이드 파일: {out_path}")
    print(f"\n📋 다음 단계 (사용자 검수 후 수동 적용):")
    print(f"   1. 위 파일에서 UI 변경사항 확인")
    print(f"   2. src/pages/{extend_slug}/index.astro 수정")
    print(f"   3. src/content/apps/{extend_slug}.md 수정")
    print(f"   4. npm run build 확인")
    print(f"   5. 네이버 블로그 포스팅 발행")
    print(f"   6. references/AI_CONTEXT.md 에 로그 추가")
    print("=" * 60)


# ── 신규 앱 메인 파이프라인 ──────────────────────────────────────────────────

def run(keyword: str, slug: str, queries: list[str]) -> None:
    pipeline_start = time.time()
    print("=" * 60)
    print(f"GoolAPP Phase 4 -- New App Pipeline Start (v2)")
    print(f"  키워드: {keyword}")
    print(f"  Slug  : {slug}")
    if queries:
        print(f"  연관 검색어: {', '.join(queries)}")
    print("=" * 60)

    def elapsed() -> str:
        secs = int(time.time() - pipeline_start)
        m, s = divmod(secs, 60)
        return f"{m}분 {s:02d}초 경과" if m else f"{s}초 경과"

    def step_done(label: str) -> None:
        print(f"  ✓ {label} 완료 [{elapsed()}]", flush=True)

    # Step 1: 앱 사양 생성
    wrapped_spec = step1_generate_spec(keyword, slug, queries)
    step_done("Step 1: 앱 사양")

    # Step 1b: 퀴즈 앱이면 JSON 문항 데이터 생성
    spec = wrapped_spec.get("_new_app_spec", {})
    _is_quiz = is_quiz_app(slug, keyword, spec.get("category", ""))
    if _is_quiz:
        json_data_filename = step1b_generate_quiz_json(slug, wrapped_spec)
        spec["json_data_filename"] = json_data_filename
        wrapped_spec["_new_app_spec"] = spec
        extract_path = pathlib.Path(f"references/legacy-extracts/{slug}.json")
        extract_path.write_text(json.dumps(wrapped_spec, ensure_ascii=False, indent=2), encoding="utf-8")
        step_done("Step 1b: 퀴즈 문항 JSON")

    # Step 2: SEO 메타 (queries 반영)
    step2_generate_seo(slug, queries)
    step_done("Step 2: SEO 메타")

    # Step 3: 롱폼 콘텐츠 (queries → FAQ 질문)
    step3_generate_longform(slug, queries)
    step_done("Step 3: 롱폼 콘텐츠")

    # Step 4: Astro 컴포넌트
    step4_generate_astro(slug)
    step_done("Step 4: Astro 컴포넌트")

    # Step 5: 빌드 검증
    build_ok = step5_build_check()
    step_done("Step 5: 빌드 검증")

    # Step 6: 블로그 초안 (빌드 성공 여부와 무관하게 생성)
    step6_generate_blog(slug)
    step_done("Step 6: 블로그 초안")

    total_secs = int(time.time() - pipeline_start)
    total_m, total_s = divmod(total_secs, 60)
    total_label = f"{total_m}분 {total_s:02d}초" if total_m else f"{total_s}초"

    print("\n" + "=" * 60)
    if build_ok:
        print(f"✅ 파이프라인 완료! (총 소요: {total_label})")
        print(f"   앱 페이지 : src/pages/{slug}/index.astro")
        print(f"   콘텐츠    : src/content/apps/{slug}.md")
        today_str = datetime.date.today().isoformat()
        print(f"   블로그 초안: references/naver-blog-posting/{today_str}-{slug}.md")
        if _is_quiz:
            _jfn = spec.get("json_data_filename", _quiz_json_filename(slug))
            print(f"   퀴즈 데이터: public/data/{_jfn}.json")
        print(f"\n📋 다음 단계 (사용자 검수):")
        print(f"   1. http://localhost:4321/{slug}/ 에서 앱 동작 확인")
        print(f"   2. src/content/apps/{slug}.md 롱폼 콘텐츠 검토")
        print(f"   3. 블로그 초안 검토 후 네이버 업로드")
        print(f"   4. ✅ GSC → URL 검사 → 색인 요청: https://goolapp.com/{slug}/")
        print(f"   5. ✅ 네이버 서치어드바이저 → 웹 페이지 수집 요청: https://goolapp.com/{slug}/")
        print(f"   6. references/AI_CONTEXT.md 에 로그 추가")
        print(f"   7. git add . && git commit -m 'feat: {keyword} 앱 추가' && git push")
    else:
        print(f"⚠️  빌드 실패 — 생성된 파일을 확인하고 수동 수정이 필요합니다. (총 소요: {total_label})")
        print(f"   앱 페이지 : src/pages/{slug}/index.astro")
    print("=" * 60)


# ── CLI 진입점 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GoolAPP 신규 앱 자동 생성 파이프라인 v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 신규 앱 (기본)
  python scripts/new_app_pipeline.py "학점 환산기" gpa-converter

  # 연관 검색어 묶음 포함
  python scripts/new_app_pipeline.py "학점 환산기" gpa-converter \\
      --queries "gpa 환산,4.3 4.5 환산,학점 변환기"

  # 기존 앱 확장 모드
  python scripts/new_app_pipeline.py "다주택자 보유세" property-holding-tax-calculator \\
      --queries "다주택자 보유세 계산기,다주택 종부세" \\
      --extend property-holding-tax-calculator
        """,
    )
    parser.add_argument("keyword", help="타깃 검색어 (예: '학점 환산기')")
    parser.add_argument("slug", help="URL slug (예: gpa-converter)")
    parser.add_argument(
        "--queries", "-q",
        type=str,
        default="",
        help="연관 검색어 묶음 (쉼표 구분, 예: 'gpa 환산,4.3 4.5 환산,학점 변환기')",
    )
    parser.add_argument(
        "--extend", "-e",
        type=str,
        default="",
        help="기존 앱 slug. 지정 시 확장 모드로 실행 (신규 페이지 미생성, 수정 가이드만 출력)",
    )
    args = parser.parse_args()

    keyword_arg = args.keyword
    slug_arg = args.slug
    queries_arg = [q.strip() for q in args.queries.split(",") if q.strip()] if args.queries else []
    extend_arg = args.extend.strip()

    if extend_arg:
        run_extend_mode(keyword_arg, slug_arg, extend_arg, queries_arg)
    else:
        run(keyword_arg, slug_arg, queries_arg)
