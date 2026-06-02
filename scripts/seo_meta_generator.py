"""
Phase 3-2-C & Phase 4-2 공통
Astro Content Collection의 seo 프롬프트를 생성한다.
"""
import json, pathlib, sys
import scripts.lib.ai_client as ai_client

def generate_seo_meta(slug: str) -> dict:
    # 1. system prompt 로드
    sys_prompt_path = pathlib.Path("scripts/prompts/seo_meta_system.md")
    if not sys_prompt_path.exists():
        raise FileNotFoundError(f"Missing {sys_prompt_path}")
    system_prompt = sys_prompt_path.read_text(encoding="utf-8")

    # 2. 필요한 입력 데이터 로드
    extract_path = pathlib.Path(f"references/legacy-extracts/{slug}.json")
    if not extract_path.exists():
        raise FileNotFoundError(f"Missing extracted data for {slug}: {extract_path}")
    
    app_data = json.loads(extract_path.read_text(encoding="utf-8"))
    
    # 3. AI 체인 호출
    user_prompt = f"""
    [앱 메타 및 분석 데이터]
    {json.dumps(app_data, ensure_ascii=False, indent=2)}
    
    위 데이터를 기반으로 SEO 메타데이터 JSON을 생성해줘.
    """

    def validate_seo(text: str) -> bool:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            elif cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            obj = json.loads(cleaned.strip())
            # Schema requirements from src/content.config.ts
            required_keys = ['title', 'description', 'canonicalPath', 'ogTitle', 'ogDescription', 'intent', 'primaryKeyword', 'secondaryKeywords']
            if not all(k in obj for k in required_keys):
                return False
            if not (10 <= len(obj['title']) <= 100): return False
            if not (80 <= len(obj['description']) <= 300): return False
            if 'searchDescription' in obj and not (80 <= len(obj['searchDescription']) <= 300): return False
            if not (80 <= len(obj['ogDescription']) <= 300): return False
            if not obj['canonicalPath'].startswith('/') or not obj['canonicalPath'].endswith('/'): return False
            return True
        except Exception:
            return False

    text = ai_client.call(
        task="seo_meta",
        system=system_prompt,
        user=user_prompt,
        validator=validate_seo,
        max_tokens=2048,
        log_label=f"seo_meta:{slug}"
    )
    
    cleaned = text.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    elif cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    return json.loads(cleaned.strip())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seo_meta_generator.py <slug>")
        sys.exit(1)
        
    slug = sys.argv[1]
    res = generate_seo_meta(slug)
    
    out_dir = pathlib.Path("references/seo_meta")
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / f"{slug}.json"
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] SEO Meta generated: {out_path}")
