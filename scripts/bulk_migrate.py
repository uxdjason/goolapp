"""
대량 마이그레이션 자동화 오케스트레이터
"""
import sys, pathlib, json, time, yaml

# 루트 디렉터리를 sys.path에 추가하여 scripts 모듈을 찾을 수 있게 함
root_dir = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from scripts import legacy_extractor, seo_meta_generator, longform_writer, blog_writer, app_generator
import scripts.lib.ai_client as ai_client

COMPLETED_APPS = ["timer-app", "deposit-savings-calculator", "due-date-calculator", "birthday-information", "simple-memo", "qr-code-generator", "country-capital-quiz"]

def judge_app(slug: str):
    print(f"[*] 자체 검수 진행 중: {slug}...")
    
    astro_path = pathlib.Path(f"src/pages/{slug}/index.astro")
    md_path = pathlib.Path(f"src/content/apps/{slug}.md")
    blog_path = list(pathlib.Path("references/naver-blog-posting").glob(f"*-{slug}.md"))
    
    if not astro_path.exists() or not md_path.exists() or not blog_path:
        print("[-] 검수 실패: 필요한 파일이 일부 누락되었습니다.")
        return
        
    astro_code = astro_path.read_text(encoding="utf-8")
    md_content = md_path.read_text(encoding="utf-8")
    blog_content = blog_path[-1].read_text(encoding="utf-8")
    
    system_prompt = """
    너는 최고 수준의 프론트엔드/SEO 검수자야.
    생성된 코드(Astro), 롱폼 마크다운, 네이버 블로그 초안을 평가해서 다음 JSON 형태로 리포트를 반환해.
    {
        "has_all_features": bool,
        "design_rules_followed": bool,
        "blog_is_plain_text": bool,
        "blog_no_html": bool,
        "notes": "평가 코멘트"
    }
    """
    
    user_prompt = f"""
    [Astro 코드]
    {astro_code[:1500]} ...
    
    [블로그 초안]
    {blog_content[:1500]} ...
    """
    
    def validator(text):
        try:
            json.loads(text.strip().replace('```json','').replace('```',''))
            return True
        except: return False
        
    try:
        res = ai_client.call(
            task="semantic_analysis",
            system=system_prompt,
            user=user_prompt,
            validator=validator,
            max_tokens=1024,
            log_label=f"judge:{slug}"
        )
        res_json = json.loads(res.strip().replace('```json','').replace('```',''))
        print(f"[+] {slug} 검수 결과: {json.dumps(res_json, ensure_ascii=False)}")
    except Exception as e:
        print(f"[-] 검수 중 오류 발생: {e}")

def run_bulk(app_slug=None):
    inventory_path = pathlib.Path("references/apps-inventory.yaml")
    data = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    
    apps = data.get("apps", data) if isinstance(data, dict) else data
    
    pending_apps = [app for app in apps if app.get("slug") not in COMPLETED_APPS]
    
    if app_slug:
        pending_apps = [app for app in pending_apps if app.get("slug") == app_slug]
    else:
        pending_apps.reverse() # 옛날 것부터 역순으로 마이그레이션
    
    print(f"총 {len(pending_apps)}개의 앱 마이그레이션을 시작합니다.")
    
    for i, app in enumerate(pending_apps):
        slug = app.get("slug")
        print(f"\n=============================================")
        print(f"[{i+1}/{len(pending_apps)}] 마이그레이션 시작: {slug}")
        print(f"=============================================")
        
        try:
            print("[1/5] Extracting legacy data...")
            legacy_extractor.run(slug)
            
            print("[2/5] Generating SEO metadata...")
            seo_meta = seo_meta_generator.generate_seo_meta(slug)
            out_seo = pathlib.Path(f"references/seo_meta/{slug}.json")
            out_seo.parent.mkdir(parents=True, exist_ok=True)
            out_seo.write_text(json.dumps(seo_meta, ensure_ascii=False, indent=2), encoding="utf-8")
            
            print("[3/5] Generating longform content...")
            longform = longform_writer.generate_longform(slug)
            out_lf = pathlib.Path(f"references/longform/{slug}.md")
            out_lf.parent.mkdir(parents=True, exist_ok=True)
            out_lf.write_text(longform, encoding="utf-8")
            
            print("[4/5] Generating blog draft...")
            blog_draft = blog_writer.generate_blog_post(slug)
            import datetime
            out_blog = pathlib.Path(f"references/naver-blog-posting/{datetime.date.today().isoformat()}-{slug}.md")
            out_blog.parent.mkdir(parents=True, exist_ok=True)
            out_blog.write_text(blog_draft, encoding="utf-8")
            
            print("[5/5] Generating Astro application...")
            app_generator.generate_app(slug)
            
            # 자가 검수
            judge_app(slug)
            
            print(f"[!] {slug} 처리 완료. API Rate Limit을 위해 5초 대기합니다.")
            time.sleep(5)
            
        except Exception as e:
            print(f"[-] {slug} 처리 중 오류 발생: {e}")
            print(f"[!] 진행을 위해 다음 앱으로 넘어갑니다. (10초 대기)")
            time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("--app="):
        app_slug = sys.argv[1].split("=")[1]
        print(f"단일 앱 마이그레이션 모드: {app_slug}")
        run_bulk(app_slug)
    else:
        run_bulk()
