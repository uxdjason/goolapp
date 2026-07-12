"""
Phase 4-2: 앱 페이지 코드(Astro) 생성 및 Markdown 병합
"""
import json, pathlib, sys, datetime

root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import scripts.lib.ai_client as ai_client

def generate_app(slug: str) -> None:
    # 1. 파일 경로 확인 및 데이터 로드
    extract_path = pathlib.Path(f"references/legacy-extracts/{slug}.json")
    if not extract_path.exists():
        raise FileNotFoundError(f"Missing extract for {slug}: {extract_path}")
    
    seo_meta_path = pathlib.Path(f"references/seo_meta/{slug}.json")
    if not seo_meta_path.exists():
        raise FileNotFoundError(f"Missing seo_meta for {slug}: {seo_meta_path}")
        
    longform_path = pathlib.Path(f"references/longform/{slug}.md")
    if not longform_path.exists():
        raise FileNotFoundError(f"Missing longform for {slug}: {longform_path}")

    app_data = json.loads(extract_path.read_text(encoding="utf-8"))
    seo_meta = json.loads(seo_meta_path.read_text(encoding="utf-8"))
    longform = longform_path.read_text(encoding="utf-8")
    
    app_meta = app_data.get("app", {})
    parsed = app_data.get("parsed", {})
    analysis = app_data.get("analysis", {})

    # 2. Markdown 콘텐츠 파일 생성 (Frontmatter + 본문)
    import yaml
    
    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True

    cat_raw = app_meta.get("category", "tool").split(",")[0].strip()
    cat_map = {
        "엔터테인먼트": "fun",
        "학습 및 퀴즈": "quiz",
        "재무 및 금융": "finance",
        "날짜 및 시간": "datetime",
        "계산기": "calculator"
    }
    cat = cat_map.get(cat_raw, cat_raw)
    if cat not in ["calculator", "quiz", "datetime", "tool", "fun", "finance"]:
        cat = "tool"

    short_src = seo_meta.get("description", "")
    if len(short_src) > 80:
        # 80자 이하에서 첫 번째 문장 끝(. ! ?)을 찾아 거기서 자른다
        import re as _re
        m = _re.search(r'[.!?]\s', short_src[:80])
        if m:
            short_src = short_src[:m.end()].rstrip()
        else:
            # 문장 끝을 못 찾으면 80자 그대로 (차선책)
            short_src = short_src[:80]

    frontmatter = {
        "title": app_meta.get("title", ""),
        "slug": slug,
        "description": seo_meta.get("description", ""),
        "shortDescription": short_src,
        "category": [cat],
        "primaryKeyword": seo_meta.get("primaryKeyword", ""),
        "secondaryKeywords": list(seo_meta.get("secondaryKeywords", [])),
        "publishedAt": datetime.datetime.utcnow().date(),
        "seo": seo_meta
    }
    
    yaml_str = yaml.dump(frontmatter, Dumper=NoAliasDumper, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    md_content = f"---\n{yaml_str}---\n\n{longform}"
    
    md_out_dir = pathlib.Path("src/content/apps")
    md_out_dir.mkdir(parents=True, exist_ok=True)
    md_out_path = md_out_dir / f"{slug}.md"
    md_out_path.write_text(md_content, encoding="utf-8")
    print(f"[+] Markdown created: {md_out_path}")

    # 3. Astro 컴포넌트 자동 생성 (code_generation_system.md 활용)
    sys_prompt_path = pathlib.Path("scripts/prompts/code_generation_system.md")
    if not sys_prompt_path.exists():
        raise FileNotFoundError(f"Missing {sys_prompt_path}")
    system_prompt = sys_prompt_path.read_text(encoding="utf-8")

    user_prompt = f"""
    [앱 메타]
    {json.dumps(app_meta, ensure_ascii=False, indent=2)}
    
    [기존 WP 분석 결과]
    {json.dumps(analysis, ensure_ascii=False, indent=2)}
    
    [기존 인터랙티브 요소 (참고용)]
    {json.dumps(parsed.get('interactive', {}), ensure_ascii=False, indent=2)}
    
    위 데이터를 기반으로 `src/pages/{slug}/index.astro` 파일을 작성해줘.
    slug는 정확히 "{slug}" 이므로, frontmatter의 getEntry 호출에서 반드시 getEntry('apps', '{slug}')를 사용해야 해.
    Astro 소스코드만 출력해.
    """

    def validate_astro(text: str) -> bool:
        # Named Slot 구조 사용 여부 확인
        if 'slot="app"' not in text and "slot='app'" not in text:
            return False
        # 파일이 잘리지 않았는지 확인 (마지막 토큰이 </script> 또는 </style> 또는 </AppLayout> 로 끝나야 함)
        stripped = text.strip()
        if not (stripped.endswith('</script>') or stripped.endswith('</style>') or stripped.endswith('</AppLayout>') or stripped.endswith('```')):
            return False
        return True

    text = ai_client.call(
        task="code_generation",
        system=system_prompt,
        user=user_prompt,
        validator=validate_astro,
        max_tokens=8192,
        log_label=f"code_generation:{slug}"
    )

    cleaned = text.strip()
    if cleaned.startswith("```astro"): cleaned = cleaned[8:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    astro_out_dir = pathlib.Path(f"src/pages/{slug}")
    astro_out_dir.mkdir(parents=True, exist_ok=True)
    astro_out_path = astro_out_dir / "index.astro"
    astro_out_path.write_text(cleaned, encoding="utf-8")
    print(f"[+] Astro component created: {astro_out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app_generator.py <slug>")
        sys.exit(1)
        
    generate_app(sys.argv[1])
