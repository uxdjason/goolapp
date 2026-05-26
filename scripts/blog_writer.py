"""
Phase 3-2-D & Phase 4-3 공통
네이버 블로그용 포스트 글을 생성한다.
"""
import json, pathlib, sys, datetime
import scripts.lib.ai_client as ai_client

def generate_blog_post(slug: str) -> str:
    # 1. system prompt 로드
    sys_prompt_path = pathlib.Path("scripts/prompts/naver_blog_system.md")
    if not sys_prompt_path.exists():
        raise FileNotFoundError(f"Missing {sys_prompt_path}")
    system_prompt = sys_prompt_path.read_text(encoding="utf-8")

    # 2. 필요한 입력 데이터 로드
    extract_path = pathlib.Path(f"references/legacy-extracts/{slug}.json")
    if not extract_path.exists():
        raise FileNotFoundError(f"Missing extracted data for {slug}: {extract_path}")
    app_data = json.loads(extract_path.read_text(encoding="utf-8"))
    
    seo_meta_path = pathlib.Path(f"references/seo_meta/{slug}.json")
    if not seo_meta_path.exists():
        raise FileNotFoundError(f"Missing SEO meta data for {slug}: {seo_meta_path}")
    seo_meta = json.loads(seo_meta_path.read_text(encoding="utf-8"))

    # 3. AI 체인 호출
    user_prompt = f"""
    [앱 정보]
    {json.dumps(app_data.get('app'), ensure_ascii=False, indent=2)}
    
    [SEO 메타 (앱 페이지용)]
    {json.dumps(seo_meta, ensure_ascii=False, indent=2)}
    
    위 데이터를 바탕으로 네이버 블로그 포스트용 콘텐츠를 작성해줘.
    이 글의 목적은 네이버 검색 노출을 통해 GoolAPP 앱 페이지(https://goolapp.com/category/[category]/[slug] 형식)로 트래픽을 유도하는 거야.
    """

    def validate_blog(text: str) -> bool:
        # 간단한 검증: 최소 길이 및 링크 포함 여부
        if len(text) < 1000:
            return False
        return True

    text = ai_client.call(
        task="naver_blog",
        system=system_prompt,
        user=user_prompt,
        validator=validate_blog,
        max_tokens=4096,
        log_label=f"naver_blog:{slug}"
    )
    
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python blog_writer.py <slug>")
        sys.exit(1)
        
    slug = sys.argv[1]
    res = generate_blog_post(slug)
    
    out_dir = pathlib.Path("references/naver-blog-posting")
    out_dir.mkdir(exist_ok=True, parents=True)
    today = datetime.date.today().isoformat()
    out_path = out_dir / f"{today}-{slug}.md"
    out_path.write_text(res, encoding="utf-8")
    print(f"[+] Naver Blog post generated: {out_path}")
