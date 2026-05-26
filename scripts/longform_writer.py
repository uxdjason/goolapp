"""
Phase 3-2-C & Phase 4-2 공통
앱 페이지 롱폼 본문 및 FAQ를 생성한다.
"""
import json, pathlib, sys, re
import scripts.lib.ai_client as ai_client

def generate_longform(slug: str) -> str:
    # 1. system prompt 로드
    sys_prompt_path = pathlib.Path("scripts/prompts/longform_system.md")
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
    
    [SEO 메타]
    {json.dumps(seo_meta, ensure_ascii=False, indent=2)}
    
    위 데이터를 바탕으로 롱폼 콘텐츠(Markdown 본문)를 작성해줘.
    """

    def validate_longform(text: str) -> bool:
        # 글자 수 (공백 제외)
        chars = len(re.sub(r"\s+", "", text))
        if not (1500 <= chars <= 2500):
            return False
        # 필수 섹션 5개 존재 (H2 헤더 기준)
        h2 = re.findall(r"^##\s+(.+)$", text, re.M)
        required = ["란?", "이럴 때 써보세요", "알아두면 좋은 점", "자주 묻는 질문", "관련 도구"]
        return all(any(r in h for h in h2) for r in required)

    text = ai_client.call(
        task="longform_korean",
        system=system_prompt,
        user=user_prompt,
        validator=validate_longform,
        max_tokens=4096,
        log_label=f"longform:{slug}"
    )
    
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python longform_writer.py <slug>")
        sys.exit(1)
        
    slug = sys.argv[1]
    res = generate_longform(slug)
    
    out_dir = pathlib.Path("references/longform")
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / f"{slug}.md"
    out_path.write_text(res, encoding="utf-8")
    print(f"[+] Longform generated: {out_path}")
