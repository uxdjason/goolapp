"""
기존 WordPress 앱 페이지를 크롤링하여 정제된 구조화 데이터를 만든다.
AI에게 URL을 던지지 않는다. AI는 A-4 단계에서 정제 데이터만 받는다.
"""
import json, pathlib, re, sys
import yaml, httpx
from bs4 import BeautifulSoup

INVENTORY = pathlib.Path("references/apps-inventory.yaml")
OUT_DIR   = pathlib.Path("references/legacy-extracts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# A-1
def load_inventory() -> list[dict]:
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))

import subprocess
# A-2
def fetch_wp_data(slug: str) -> dict | None:
    for post_type in ["posts", "pages"]:
        url = f"https://goolapp.com/wp-json/wp/v2/{post_type}?slug={slug}"
        # Use curl to bypass Cloudflare TLS fingerprinting blocking httpx
        result = subprocess.run(["curl", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                if data and isinstance(data, list):
                    return data[0]
            except Exception:
                pass
    return None

# A-3 — 결정론적 정제. 여기서는 AI를 호출하지 않는다.
def parse_wp_page(wp_data: dict) -> dict:
    title = wp_data.get("title", {}).get("rendered", "")
    content_html = wp_data.get("content", {}).get("rendered", "")
    soup = BeautifulSoup(content_html, "html.parser")

    description = ""  # WP API doesn't expose meta tags directly

    body_html = content_html
    body_text = soup.get_text("\n", strip=True)

    inline_scripts = [s.get_text() for s in soup.find_all("script") if not s.get("src")]
    external_scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]

    inputs  = [str(t) for t in soup.find_all(["input", "select", "textarea"])]
    buttons = [str(t) for t in soup.find_all("button")]

    headings = [{"level": int(h.name[1]), "text": h.get_text(strip=True)} for h in soup.find_all(re.compile(r"^h[2-4]$"))]

    return {
        "meta": {"title": title, "description": description},
        "body_html": body_html,
        "body_text": body_text,
        "inline_scripts": inline_scripts,
        "external_scripts": external_scripts,
        "interactive": {"inputs": inputs, "buttons": buttons},
        "headings": headings,
    }

# A-4 — AI에게는 정제된 parsed.json + 명시적 질문만 전달
# AI 호출은 §3 정책에 따라 scripts/lib/ai_client.py를 경유한다 (직접 SDK 호출 금지).
import scripts.lib.ai_client as ai_client

AI_SYSTEM_PROMPT = """\
너는 한국어 웹앱을 Astro 정적 사이트로 마이그레이션하는 분석가야.
입력으로 이미 1차 정제된 JSON 데이터를 받는다. URL을 다시 크롤링하지 마.
JSON에 없는 내용을 추측하거나 만들어내지 마. 모르면 'unknown'이라고 적어.

출력은 마크다운/설명/코드펜스 없이 JSON 하나만. 키는 한국어 설명 가능.

출력 키:
1. core_function: 앱의 핵심 기능 1~2문장 요약
2. io_contract:   {inputs: [...], outputs: [...]} — 어떤 입력을 받아 어떤 결과를 내는지
3. js_logic_summary: inline_scripts를 보고 핵심 알고리즘을 의사코드 또는 요약으로 정리
4. external_deps: external_scripts 중 마이그레이션 시 제거/대체해야 할 항목
5. content_blocks: body_text에서 롱폼으로 가져갈 가치가 있는 단락들의 인덱스
6. faq_candidates: headings + 본문에서 FAQ 후보 (있으면)
7. astro_migration_notes: Astro 변환 시 주의점 (예: jQuery 의존, document.write 사용 등)
"""

def _is_valid_analysis(text: str) -> bool:
    try:
        obj = json.loads(text)
        return all(k in obj for k in (
            "core_function", "io_contract", "js_logic_summary",
            "external_deps", "content_blocks", "faq_candidates", "astro_migration_notes",
        ))
    except Exception:
        return False

def ai_analyze(parsed: dict, app_meta: dict) -> dict:
    user = (
        f"[앱 메타]\n{json.dumps(app_meta, ensure_ascii=False, indent=2)}\n\n"
        f"[정제된 페이지 데이터]\n{json.dumps(parsed, ensure_ascii=False, indent=2)}"
    )
    text = ai_client.call(
        task="semantic_analysis",          # §3-1 모델 체인 적용 + Fallback
        system=AI_SYSTEM_PROMPT,
        user=user,
        validator=_is_valid_analysis,      # 7개 키 검증, 실패 시 다음 모델로 전환
        max_tokens=4096,
        log_label=f"legacy_extract:{app_meta.get('slug','?')}",
    )
    return json.loads(text)

def run(slug_filter: str | None = None) -> None:
    for app in load_inventory():
        if "apps" in load_inventory(): # Need to handle root key 'apps' in yaml
            pass # The load_inventory() is handled properly later
        
    apps = load_inventory().get("apps", []) if isinstance(load_inventory(), dict) else load_inventory()

    for app in apps:
        if slug_filter and app["slug"] != slug_filter:
            continue
        slug = app["slug"]
        url  = app.get("legacy_url", app.get("wp_url"))
        print(f"[+] {slug} ← {url}")

        wp_data = fetch_wp_data(slug)
        if not wp_data:
            print(f"[-] Data not found for {slug}")
            continue
        
        (OUT_DIR / f"{slug}.raw.json").write_text(json.dumps(wp_data, ensure_ascii=False, indent=2), encoding="utf-8")

        parsed = parse_wp_page(wp_data)
        (OUT_DIR / f"{slug}.parsed.json").write_text(
            json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        analyzed = ai_analyze(parsed, app)
        final = {"app": app, "parsed": parsed, "analysis": analyzed}
        (OUT_DIR / f"{slug}.json").write_text(
            json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8"
        )

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else None)
