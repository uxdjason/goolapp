"""
Phase 4-2: 신규 앱 자동 생성 파이프라인
- 사용자가 trend_collector.py 리포트에서 선택한 키워드를 기반으로 신규 앱 생성
- 기존 Phase 3 스크립트(seo_meta_generator, longform_writer, app_generator, blog_writer) 재사용
- legacy-extracts 없이 신규 사양(spec)을 직접 입력으로 사용

사용법:
  python scripts/new_app_pipeline.py "<키워드>" <slug>
  예: python scripts/new_app_pipeline.py "환율 계산기" exchange-rate-calculator
"""# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
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
    # 열린 배열/객체를 닫아줌
    open_braces  = s.count('{') - s.count('}')
    open_brackets = s.count('[') - s.count(']')
    # 마지막 완전하지 않은 키-값 쌍 제거 (콤마로 끝나는 경우)
    while s.endswith(','):
        s = s.rstrip().rstrip(',')
    for _ in range(open_brackets):
        s += ']'
    for _ in range(open_braces):
        s += '}'
    return s


def step1_generate_spec(keyword: str, slug: str) -> dict:
    """키워드로부터 앱 사양 JSON 생성."""
    print(f"\n[Step 1/6] 앱 사양 생성: '{keyword}'", flush=True)

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
- js_logic_summary: 핵심 계산 로직 의사코드 요약 (간결하게, 200자 이내)"""

    print(f"  → AI 호출 중 (앱 사양 JSON 생성)...")
    text = ai_client.call(
        task="semantic_analysis",
        system=SYSTEM,
        user=f"키워드: {keyword}\nslug: {slug}",
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

    # spec을 legacy-extracts 형식으로 감싸서 기존 스크립트 재사용 가능하게
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
        "_new_app_spec": spec,  # 원본 사양 보존
    }

    # references/legacy-extracts/{slug}.json 에 저장 (기존 스크립트 재사용용)
    out_dir = pathlib.Path("references/legacy-extracts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.json"
    out_path.write_text(json.dumps(wrapped, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ 앱 사양 생성: {out_path}")
    return wrapped


def step2_generate_seo(slug: str) -> dict:
    """SEO 메타데이터 생성."""
    print(f"\n[Step 2/6] SEO 메타 생성...", flush=True)
    print(f"  → AI 호출 중 (SEO 메타데이터 작성)...", flush=True)
    from scripts.seo_meta_generator import generate_seo_meta
    seo = generate_seo_meta(slug)
    out_dir = pathlib.Path("references/seo_meta")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.json").write_text(json.dumps(seo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ SEO 메타 생성 완료")
    return seo


def step3_generate_longform(slug: str) -> str:
    """롱폼 콘텐츠 생성."""
    print(f"\n[Step 3/6] 롱폼 콘텐츠 생성...", flush=True)
    print(f"  → AI 호출 중 (한국어 롱폼 본문 작성, 시간이 걸릴 수 있습니다)...", flush=True)
    from scripts.longform_writer import generate_longform
    longform = generate_longform(slug)
    out_dir = pathlib.Path("references/longform")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.md").write_text(longform, encoding="utf-8")
    print(f"  ✓ 롱폼 콘텐츠 생성 완료 ({len(longform)}자)")
    return longform


def step4_generate_astro(slug: str) -> None:
    """Astro 앱 컴포넌트 생성."""
    print(f"\n[Step 4/6] Astro 컴포넌트 생성...", flush=True)
    print(f"  → AI 호출 중 (Astro/JS 코드 생성, 가장 오래 걸립니다)...", flush=True)
    from scripts.app_generator import generate_app
    generate_app(slug)
    print(f"  ✓ Astro 컴포넌트 생성 완료")


def step5_build_check() -> bool:
    """npm run build로 빌드 검증."""
    print(f"\n[Step 5/6] 빌드 검증 (npm run build)...", flush=True)
    print(f"  → 빌드 실행 중 (수십 초 소요)...", flush=True)
    result = subprocess.run(
        "npm run build", shell=True,
        capture_output=True, text=True, cwd=str(root_dir),
    )
    if result.returncode == 0 or "Completed in" in result.stdout:
        print(f"  ✓ 빌드 성공")
        return True
    else:
        print(f"  ✗ 빌드 실패")
        print(result.stdout[-2000:])
        print(result.stderr[-1000:])
        return False


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


def run(keyword: str, slug: str) -> None:
    pipeline_start = time.time()
    print("=" * 60)
    print(f"GoolAPP Phase 4 -- New App Pipeline Start")
    print(f"  키워드: {keyword}")
    print(f"  Slug  : {slug}")
    print("=" * 60)

    def elapsed() -> str:
        secs = int(time.time() - pipeline_start)
        m, s = divmod(secs, 60)
        return f"{m}분 {s:02d}초 경과" if m else f"{s}초 경과"

    def step_done(label: str) -> None:
        print(f"  ✓ {label} 완료 [{elapsed()}]", flush=True)

    # Step 1: 앱 사양 생성
    step1_generate_spec(keyword, slug)
    step_done("Step 1: 앱 사양")

    # Step 2: SEO 메타
    step2_generate_seo(slug)
    step_done("Step 2: SEO 메타")

    # Step 3: 롱폼 콘텐츠
    step3_generate_longform(slug)
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

    # 최종 요약
    print("\n" + "=" * 60)
    if build_ok:
        print(f"✅ 파이프라인 완료! (총 소요: {total_label})")
        print(f"   앱 페이지 : src/pages/{slug}/index.astro")
        print(f"   콘텐츠    : src/content/apps/{slug}.md")
        print(f"   블로그 초안: references/naver-blog-posting/{datetime.date.today().isoformat()}-{slug}.md")
        print(f"\n📋 다음 단계 (사용자 검수):")
        print(f"   1. http://localhost:4321/{slug}/ 에서 앱 동작 확인")
        print(f"   2. src/content/apps/{slug}.md 롱폼 콘텐츠 검토")
        print(f"   3. 블로그 초안 검토 후 네이버 업로드")
        print(f"   4. git add . && git commit -m 'feat: {keyword} 앱 추가' && git push")
    else:
        print(f"⚠️  빌드 실패 — 생성된 파일을 확인하고 수동 수정이 필요합니다. (총 소요: {total_label})")
        print(f"   앱 페이지 : src/pages/{slug}/index.astro")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python scripts/new_app_pipeline.py \"<키워드>\" <slug>")
        print("예시 : python scripts/new_app_pipeline.py \"환율 계산기\" exchange-rate-calculator")
        sys.exit(1)

    keyword_arg = sys.argv[1]
    slug_arg = sys.argv[2]
    run(keyword_arg, slug_arg)
