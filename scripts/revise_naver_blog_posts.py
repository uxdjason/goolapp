import os
import glob
import random
from lib import ai_client

BLOG_DIR = "references/naver-blog-posting"

SYSTEM_PROMPT = """당신은 네이버 블로그 SEO 최적화 전문 카피라이터이자 베테랑 블로거입니다. 
주어진 블로그 초안을 완전히 새롭고 "사람이 직접 쓴 것처럼 자연스러운" 포스팅으로 재작성하세요. 
모든 글이 똑같은 템플릿처럼 보이지 않도록 아래 지침을 엄격히 따르십시오.

[필수 규칙]
1. 도입부(Hook) 다양화: "안녕하세요" 같은 식상한 인사말은 절대 금지합니다.
   - 경험담(스토리텔링), 호기심 유발 질문, 통계, 혹은 결론부터 말하는 두괄식 중 하나로 바로 시작하세요.
2. 어투(Tone) 강제 할당: 제가 입력의 맨 첫 줄에 지정해주는 **[말투 지정]**을 무조건 따라서 글 전체의 톤앤매너를 유지하세요.
3. 링크 위치 다양화: GoolAPP 링크(https://goolapp.com/...)를 무조건 글 맨 아래에 두지 마세요! 문맥상 가장 어울리는 곳(도입부 직후, 중단 등)에 자연스럽게 배치하세요. (기존 초안에 있는 링크 URL은 반드시 정확히 보존)
4. 본문 구조: 단조로운 넘버링(1, 2, 3)을 피하고, 썰을 풀듯이 문단을 나누거나 개인적인 팁(Tip), 주의사항 등을 삽입하여 인간적인 느낌(경험기)을 주세요.
5. 키워드 최적화: 제목과 첫 문단에 핵심 키워드를 자연스레 녹이되 억지로 반복하지 마세요. (원문 하단의 #태그들은 그대로 유지)
6. 제목 추천 부분도 재작성본의 톤에 맞춰 3개 정도 제안하되, 사람들의 클릭을 유도하는 감성적/직관적 카피로 뽑아주세요.
7. 답변에는 오직 '블로그 포스팅 본문'만 출력하세요. (설명이나 사족 금지)
"""

TONES = [
    "친근한 구어체 (해요체) - 이웃집 친구가 꿀팁을 알려주듯 편안하고 다정한 말투",
    "전문적인 비즈니스체 (하십시오체) - 신뢰감을 주는 전문가가 정확한 정보를 전달하는 말투",
    "개인적인 일기체 (해체/반말+해요체 혼합) - 혼자 경험을 끄적이다가 정보를 공유하는 톤",
    "감성 에세이체 - 차분하고 감성적으로 일상의 소소한 불편함을 이야기하며 시작하는 톤",
    "유쾌하고 텐션 높은 리뷰어체 - 이모티콘을 쓰듯 발랄하고 리액션이 큰 톤"
]

def main():
    md_files = glob.glob(os.path.join(BLOG_DIR, "*.md"))
    md_files = sorted([f for f in md_files if not f.endswith('README.md')])
    
    total = len(md_files)
    print(f"Found {total} markdown files to revise.")

    for i, file_path in enumerate(md_files, 1):
        filename = os.path.basename(file_path)
        print(f"[{i}/{total}] Processing {filename}...")
        
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        chosen_tone = random.choice(TONES)
        
        user_prompt = f"**[말투 지정]**: {chosen_tone}\n\n[원본 초안]\n{original_content}"

        try:
            # We use 'naver_blog' task chain to invoke the LLM
            revised_content = ai_client.call(
                task="naver_blog",
                system=SYSTEM_PROMPT,
                user=user_prompt,
                log_label=f"revise_{filename}"
            )
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(revised_content)
                
            print(f"  -> Success! (Tone: {chosen_tone.split(' - ')[0]})")
            
        except Exception as e:
            print(f"  -> Error processing {filename}: {e}")

if __name__ == "__main__":
    main()
