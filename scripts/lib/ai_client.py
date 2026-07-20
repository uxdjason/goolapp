"""
모든 AI 호출의 단일 진입점.
- 작업(task)을 받아 모델 체인을 결정
- 1순위 → 2순위 → Fallback 순서로 시도
- 응답 검증(validator) 실패 시 자동 재시도/전환
- 모든 호출 결과를 references/ai-call-logs/ 에 기록
"""
from __future__ import annotations
from typing import Callable
import json, os, time, pathlib, datetime as dt
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = pathlib.Path("references/ai-call-logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class AICallError(Exception):
    pass

# (provider, model) 튜플의 우선순위 체인
TASK_CHAINS: dict[str, list[tuple[str, str]]] = {
    "code_generation":   [("anthropic","claude-opus-4-7"), ("anthropic","claude-sonnet-4-6"), ("google","gemini-2.5-pro")],
    "longform_korean":   [("anthropic","claude-opus-4-7"), ("anthropic","claude-sonnet-4-6"), ("google","gemini-2.5-pro")],
    "seo_meta":          [("anthropic","claude-haiku-4-5"), ("anthropic","claude-sonnet-4-6"), ("google","gemini-2.5-flash")],
    "json_ld":           [("anthropic","claude-haiku-4-5"), ("anthropic","claude-sonnet-4-6"), ("google","gemini-2.5-flash")],
    "naver_blog":        [("anthropic","claude-opus-4-7"), ("anthropic","claude-sonnet-4-6"), ("google","gemini-2.5-pro")],
    "semantic_analysis": [("anthropic","claude-sonnet-4-6"), ("anthropic","claude-opus-4-7"), ("google","gemini-2.5-pro")],
    "keyword_scoring":   [("anthropic","claude-haiku-4-5"), ("anthropic","claude-sonnet-4-6"), ("google","gemini-2.5-flash")],
}

def call(
    task: str,
    system: str,
    user: str,
    *,
    validator: Callable[[str], bool] | None = None,
    max_tokens: int = 4096,
    log_label: str = "",
) -> str:
    """task 체인을 따라 시도. validator가 있으면 통과 시까지 재시도/전환."""
    chain = TASK_CHAINS[task]
    last_err: Exception | None = None
    for step, (provider, model) in enumerate(chain):
        for attempt in range(2):  # 모델당 최대 2회
            attempt_label = f" (재시도 {attempt})" if attempt > 0 else ""
            fallback_label = f" [fallback #{step}]" if step > 0 else ""
            print(f"    ⏳ AI 호출 중: {provider}/{model}{fallback_label}{attempt_label} ...", flush=True)
            t0 = time.time()
            try:
                text = _dispatch(provider, model, system, user, max_tokens)
                if validator and not validator(text):
                    raise AICallError(f"validator failed [{provider}/{model}]")
                elapsed = time.time() - t0
                print(f"    ✅ 완료: {provider}/{model} ({elapsed:.1f}초, {len(text)}자)", flush=True)
                _log(task, log_label, provider, model, step, attempt, "ok", elapsed, len(text))
                return text
            except Exception as e:
                elapsed = time.time() - t0
                print(f"    ❌ 실패: {provider}/{model} ({elapsed:.1f}초) — {e}", flush=True)
                last_err = e
                _log(task, log_label, provider, model, step, attempt, f"err:{e}", elapsed, 0)
                wait = min(2 ** attempt, 8)
                if wait > 0:
                    print(f"    ⏸  {wait}초 대기 후 재시도...", flush=True)
                time.sleep(wait)
    raise AICallError(f"All providers exhausted for task={task}. Last error: {last_err}")

def _dispatch(provider: str, model: str, system: str, user: str, max_tokens: int) -> str:
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    if provider == "google":
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        m = genai.GenerativeModel(model, system_instruction=system)
        return m.generate_content(user).text
    raise ValueError(f"unknown provider: {provider}")

def _log(task, label, provider, model, step, attempt, status, elapsed, out_chars):
    rec = {
        "ts": dt.datetime.utcnow().isoformat() + "Z",
        "task": task, "label": label, "provider": provider, "model": model,
        "fallback_step": step, "attempt": attempt, "status": status,
        "elapsed_s": round(elapsed, 2), "out_chars": out_chars,
    }
    fp = LOG_DIR / f"{dt.date.today().isoformat()}.jsonl"
    with fp.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
