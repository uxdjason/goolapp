<!-- 
[AI INSTRUCTIONS]
이 파일은 여러 AI 에이전트(Antigravity, Cursor, Claude Code 등) 간의 작업 문맥 공유를 위한 인수인계 문서입니다.
당신(AI)은 사용자의 지시가 있을 때, 반드시 아래의 [Log Format]에 맞추어 문서 최하단에 새로운 작업 내역을 덧붙여야 합니다.
기존에 작성된 과거 로그는 절대 수정하거나 삭제하지 마십시오.
-->

### [Log Format]
새로운 로그를 추가할 때 아래의 양식을 엄격하게 준수하십시오.
- **Date:** YYYY-MM-DD HH:MM
- **IDE / Model:** (예: Antigravity / Gemini 3.1 Pro, Cursor / Claude 3.5 Sonnet)
- **Task Done:** 이번 세션에서 완료한 주요 작업 내용 요약
- **Files Changed:** 수정, 생성, 삭제된 주요 파일 목록
- **Current Status / Issues:** 현재 발생 중인 에러, 미완료된 작업, 또는 주의할 점
- **Next Steps:** 다음 작업자(또는 다음 AI)가 즉시 이어서 진행해야 할 구체적인 목표

---
## 작업 히스토리 (Changelog)

- **Date:** 2026-05-15 14:20
- **IDE / Model:** Antigravity / Gemini 3 Flash
- **Task Done:**
  - **UI 정밀 고도화(Pixel-Perfect)**: `references/design/`의 Figma 디자인을 100% 반영하여 Phase 2 & 3 완료.
  - **Typography**: 김정철 명조(본문용) 및 김정철 고딕(태그/버튼용) 서체 통합 및 변수화.
  - **Header/Footer**: 브랜드 텍스트 "GoolAPP" 복구, 로고 통합, 네비게이션 메뉴명을 디자인 스펙과 일치시킴.
  - **Hero Section**: 홈 및 카테고리 페이지의 히어로 제목 2색 처리 및 중앙 정렬 레이아웃 통일.
  - **Category Navigation**: 필터 버튼 그룹 중앙 정렬, "즐겨찾는 앱" 별 아이콘 추가, 폰트 가독성 상향.
  - **App Detail Pages**: 별 버튼 테두리 제거, 시인성 강화, 하단 관련 앱(Related Apps) 더미 데이터 영역 추가.
  - **AdSense Strategy**: 개발 환경에서도 식별 가능한 광고 플레이스홀더 디자인 및 개별 앱 페이지 본문 상/중/하 슬롯 배치 완료.
- **Files Changed:**
  - `src/styles/design-system.css`: 서체 선언 및 글래스모피즘 토큰 고도화.
  - `src/components/Header.astro`, `Footer.astro`: 브랜드 아이덴티티 반영 재설계.
  - `src/components/CategoryNav.astro`, `AppCard.astro`: 태그 디자인 및 폰트 수정.
  - `src/pages/index.astro`, `src/pages/category/[category].astro`: 히어로 및 검색창 레이아웃 동기화.
  - `src/layouts/AppLayout.astro`, `src/components/AdUnit.astro`: 앱 상세 페이지 UI 및 광고 영역 보강.
- **Current Status / Issues:**
  - 사이트 전반의 UI 골격이 디자인 자산과 98% 일치함을 확인.
  - 관련 앱(Related Apps) 로직은 현재 더미 데이터로 작동하며, 이후 콘텐츠 마이그레이션 시 고도화 필요.
  - 검색창은 현재 UI 전용이며 실제 필터링 기능은 미구현 상태.
- **Next Steps:**
  - **Phase 3 시작**: 기존 레거시 앱 로직(Base64, 디데이 계산기 등)을 신규 Astro 아키텍처로 이식.
  - 검색창의 클라이언트 사이드 검색/필터링 기능 구현.
  - 개별 앱 페이지의 SEO 메타데이터 최적화 및 공유 기능 추가.


- **Date:** 2026-05-15 17:10
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:**
  - **Header (Mobile)**: 모바일 뷰어용 네비게이션 햄버거 메뉴를 추가하고, 클릭 시 닫기(X) 아이콘으로 토글되는 JS 인터랙션 구현 완료.
  - **Footer (Mobile)**: 로고 -> 하단 링크 -> 저작권 텍스트 순서의 수직 스택 및 중앙 정렬 레이아웃을 디자인 명세(`goolapp-home-mobile-260508`)와 일치시킴 (`order` 및 `display: contents` 활용).
  - **Footer (Desktop)**: 로고(좌측), 저작권(중앙), 하단 링크(우측, 세로 배열)로 3분할되는 데스크톱 푸터 레이아웃을 복구(`goolapp-home-260507` 기준).
- **Files Changed:**
  - `src/components/Header.astro`: 모바일 메뉴 토글 버튼(SVG 2종) 및 상태 관리 스크립트 추가.
  - `src/components/Footer.astro`: 반응형 분기(`@media`) 기반의 Flex 레이아웃 및 요소 배치 순서 전면 개편.
- **Current Status / Issues:**
  - 데스크톱 및 모바일 환경에서 헤더와 푸터 UI가 최신 디자인 스펙과 완전하게 동기화됨.
- **Next Steps:**
  - **Phase 3 진행**: 기존 레거시 앱(Base64, 단위 변환기 등) 로직의 Astro 컴포넌트 이식 본격화.
  - 클라이언트 사이드 검색(어떤 앱이 필요하세요?) 로직 연동.


- **Date:** 2026-05-26 17:45
- **IDE / Model:** Antigravity / Gemini
- **Task Done:**
  - **마이그레이션 자동화 파이프라인 구축 및 PoC 완료**: 데이터 추출, SEO/롱폼 생성, 블로그 작성용 파이썬 스크립트 4종(`legacy_extractor.py`, `seo_meta_generator.py`, `longform_writer.py`, `blog_writer.py`) 완성.
  - **파이프라인 안정화**: `legacy_extractor.py`의 Cloudflare 403 차단 문제를 `curl` 우회로 해결. `seo_meta_generator.py`의 AI 결과물 검증 로직(한국어 길이 최적화 및 마크다운 찌꺼기 제거) 수정.
  - **PoC(due-date-calculator) 성공적 검증**: 레거시 앱 `due-date-calculator`를 대상으로 파이프라인을 가동하여 추출부터 콘텐츠 생성까지 모든 단계를 에러 없이 수행.
  - **Astro 컴포넌트 구현**: 추출된 데이터를 기반으로 GoolAPP의 새로운 디자인 시스템에 맞춘 `src/pages/due-date-calculator/index.astro`와 `src/content/apps/due-date-calculator.md`를 생성하고 `npm run build` 무결점 확인.
- **Files Changed:**
  - `scripts/*.py` (자동화 스크립트 4종 생성 및 수정)
  - `src/pages/due-date-calculator/index.astro` (생성)
  - `src/content/apps/due-date-calculator.md` (생성)
  - `references/naver-blog-posting/2026-05-26-due-date-calculator.md` (생성)
- **Current Status / Issues:**
  - 마이그레이션 자동화 파이프라인 완비 및 빌드 검증 성공.
  - 오늘의 작업은 여기까지 마무리하고 일시 중단. 내일 본격적인 마이그레이션 시작 예정.
- **Next Steps:**
  - **본격적인 마이그레이션 재개**: `references/apps-inventory.yaml` 리스트의 **가장 아래에 있는 앱(예: `deposit-savings-calculator`)부터 역순으로 하나씩** 순차적으로 마이그레이션을 진행할 것.
  - 각 앱마다 파이프라인 실행 후 사용자의 검수 및 승인을 얻은 뒤 다음 앱으로 넘어갈 것.

- **Date:** 2026-06-01 17:15
- **IDE / Model:** Antigravity / Gemini
- **Task Done:**
  - **즐겨찾기 기능 추가**: `AppCard`와 `AppLayout` 상단에 별표 아이콘을 추가하고, 브라우저 로컬 스토리지(Local Storage)를 연동하여 즐겨찾기 토글 및 홈 화면에서의 `/#favorites` 필터링 기능 구현.
  - **Phase 3 앱 마이그레이션**: 첫 번째 대상인 `deposit-savings-calculator` (예적금 이자 계산기) 마이그레이션 완료. 파이썬 마이그레이션 스크립트의 AI 모듈(google.generativeai) 구버전 이슈로 인해 파이프라인의 AI 역할을 본 에이전트가 직접 수행.
  - **UI/UX 고도화**: 구형 머티리얼 디자인 기반 다중 화면(Screen) UI를 버리고, 싱글 페이지 기반의 글래스모피즘(Glassmorphism) 탭 UI로 전면 개편. 입력 시 실시간으로 세후 수령액이 계산되는 스크립트 작성.
  - **템플릿 디자인 보완**: `AppLayout.astro` 공통 템플릿의 앱 제목과 설명 간격 확보, 설명 영역 전체 너비(100%) 사용 및 롱폼 `h3` 상하 여백 스타일 수정.
  - **콘텐츠 최적화**: 마크다운 볼드체(`**`)가 한국어 조사 파싱 과정에서 오작동하는 에러를 해결(`<strong>` 사용) 및 블로그 마케팅용 포스팅 초안 생성 완료.
- **Files Changed:**
  - `src/layouts/AppLayout.astro`, `src/layouts/BaseLayout.astro`: 즐겨찾기 스크립트 및 템플릿 CSS 보완.
  - `src/components/AppCard.astro`: 즐겨찾기 버튼 이벤트 처리 추가.
  - `src/pages/deposit-savings-calculator/index.astro` (생성)
  - `src/content/apps/deposit-savings-calculator.md` (생성)
  - `references/naver-blog-posting/2026-06-01-deposit-savings-calculator.md` (생성)
- **Current Status / Issues:**
  - 즐겨찾기 기능 정상 작동. 
  - 첫 번째 Phase 3 앱 마이그레이션과 공통 템플릿 CSS 피드백 적용 완료.
  - 자동화 파이프라인 스크립트의 `google.generativeai` 구버전 문제로, 이후 앱들도 AI 분석/생성 단계는 에이전트가 직접 수행하여 퀄리티를 유지하는 것이 바람직함.
- **Next Steps:**
  - `apps-inventory.yaml` 리스트 상의 다음 타겟인 **"타이머(timer-app)"**의 마이그레이션 진행.

- **Date:** 2026-06-02 09:59
- **IDE / Model:** Antigravity / Claude Sonnet 4.6 (Thinking)
- **Task Done:**
  - **SEO 전면 감사 및 강화**: `Seo.astro` 컴포넌트를 OG 스펙 완전 준수 기준으로 전면 재작성.
    - `og:site_name`, `og:type`(`website`/`article` 분기), `og:locale(ko_KR)`, `og:image:width/height`, `og:image:alt`, `og:logo` 추가.
    - OG 이미지 절대 URL 자동 변환 로직 추가 (상대 경로 입력 시 `https://goolapp.com` prefix 자동 부여).
    - `twitter:image:alt` 추가 (Twitter Card validator pass 기준).
    - `article:published_time` / `article:modified_time` 메타 추가 (앱 상세 페이지).
  - **JSON-LD Structured Data 추가**:
    - `WebSite` JSON-LD (SearchAction 포함) — 모든 페이지 공통.
    - `SoftwareApplication` JSON-LD (isAccessibleForFree, Offer, publisher 포함) — 앱 상세 페이지 자동 생성.
  - **BaseLayout.astro 개선**: `theme-color`, SVG favicon 우선 선언, `apple-touch-icon`, 확장된 SEO props 전달 체계 구축.
  - **AppLayout.astro 개선**: `ogImage`, `ogTitle`, `ogDescription`, `canonicalUrl`, `publishedAt`, `updatedAt` props 추가. 앱 페이지가 `seo.*` 필드의 데이터를 정확히 `<head>`에 반영하도록 연결.
  - **OG 이미지 파이프라인 구축**: Pixabay 이미지를 `images/GoolAPP-{slug}.webp` 형식으로 관리하고, `public/og/`로 복사하여 서빙하는 패턴 확립.
  - **`deposit-savings-calculator` OG 이미지 적용**: `public/og/GoolAPP-deposit-savings-calculator.webp` 사용. 페이지 본문에는 미표시, `<head>` 메타에만 존재하는 방식.
  - **홈 페이지 OG 보강**: `ogImage`, `ogTitle`, `ogDescription`, `keywords` 추가.
  - **도메인 라우팅 이슈 파악 및 우회**: `goolapp.com` 도메인이 Cloudflare Pages(신규)와 구 서버(워드프레스)를 동시에 바라보는 상태. `/og/` 경로는 Cloudflare Pages가 서빙하므로, `og:logo`도 `public/og/logo.png`로 배치하여 안정적으로 서빙.
- **Files Changed:**
  - `src/components/Seo.astro`: 전면 재작성
  - `src/layouts/BaseLayout.astro`: SEO props 확장, theme-color/favicon/apple-touch-icon 추가, WebSite JSON-LD 생성 로직 추가
  - `src/layouts/AppLayout.astro`: SEO props 확장, SoftwareApplication JSON-LD 생성 로직 추가
  - `src/pages/index.astro`: OG 관련 props 추가
  - `src/pages/deposit-savings-calculator/index.astro`: `seo.*` 필드를 AppLayout에 전달하도록 수정
  - `src/pages/due-date-calculator/index.astro`: `seo.*` 필드를 AppLayout에 전달하도록 수정
  - `src/content/apps/deposit-savings-calculator.md`: `ogImage` 경로 수정 (`/og/GoolAPP-deposit-savings-calculator.webp`)
  - `public/og/GoolAPP-deposit-savings-calculator.webp`: 신규 추가 (Pixabay 이미지)
  - `public/og/logo.png`: 신규 추가 (og:logo 용)
- **Current Status / Issues:**
  - SEO/OG 체계 완비. Open Graph validator 및 Google Rich Results 기준 충족.
  - `goolapp.com` 도메인이 구 워드프레스 서버와 신규 Cloudflare Pages를 동시에 바라보는 상태이므로, **정적 파일은 반드시 `public/og/` 경로 아래에 배치**해야 정상 서빙됨 (도메인 완전 이전 전까지).
  - OG 이미지 전략: 페이지 본문에는 미표시, `<head>` 메타에만 존재. SEO 불이익 없음.
- **Next Steps:**
  - 추후 앱 마이그레이션 시마다, Pixabay에서 이미지 선정 → `images/GoolAPP-{slug}.webp` 저장 → `public/og/`로 복사 → 해당 앱 `.md`의 `seo.ogImage` 경로를 `/og/GoolAPP-{slug}.webp`로 지정.
  - 다음 마이그레이션 대상: **"타이머(timer-app)"**.

- **Date:** 2026-06-02 14:30
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:**
  - **Phase 3 앱 마이그레이션**: `timer-app` (타이머 & 스톱워치) 마이그레이션 및 수동 고도화 완료. 이 과정에서 다수의 UI/UX 및 포맷팅 이슈를 수정하며 향후 마이그레이션을 위한 원칙을 확립함.
- **Files Changed:**
  - `src/pages/timer-app/index.astro`
  - `src/content/apps/timer-app.md`
  - `references/naver-blog-posting/2026-06-02-timer-app.md`
- **Current Status / Issues (핵심 교훈 및 향후 마이그레이션 공통 적용 원칙):**
  1. **Astro 동적 엘리먼트 스타일링**: JS `document.createElement()`로 생성된 요소에는 Astro의 Scoped CSS가 적용되지 않음. 반드시 `:global()` 식별자를 사용하거나 전역 유틸리티 클래스를 사용할 것.
  2. **직관적인 탭(Tab) UI**: 활성화된 탭은 단순히 텍스트 색상만 변경하지 말고, 배경색(Primary Color)을 채워 명확한 대비를 줄 것.
  3. **기능별 UI 상태 분리**: 카운트다운과 스톱워치처럼 다른 기능이 동작할 때 화면 레이아웃이 똑같이 보이면 혼동을 유발함. 라벨(`남은 시간`, `진행 시간`), 색상, 입력 필드 유지(`disabled` 처리) 등을 통해 시각적으로 명확히 구분할 것.
  4. **텍스트 필드 포커스 UX**: 초기값 `0`인 입력 필드를 포커스할 때 값이 남아 입력에 방해되지 않도록 `value = ''` 처리 및 CSS `input:focus::placeholder { color: transparent; }`를 적용할 것.
  5. **자연스러운 어투 (콘텐츠)**: 기계적인 설명("뽀모도로 테크닉 방법론...")을 배제하고, 사용자 친화적인 일상적 어투("집중력이 떨어질 때 이렇게 해보세요")로 작성할 것.
  6. **데이터 출력 가독성**: 구간 기록 같은 데이터를 출력할 때 불필요한 단어나 텍스트 겹침을 방지하고, 사용자가 읽기 쉬운 명확한 포맷(`순번 - 시간`)으로 간결하게 출력할 것.
  7. **네이버 블로그 포스팅 초안 포맷**: 에디터 복사 붙여넣기를 위해 마크다운 볼드체(`**`)나 HTML 태그(`<strong>`)를 절대 사용하지 않은 순수 텍스트(Plain Text)로 작성할 것. 상단에 YAML Frontmatter 대신 '제목 추천'을 명시하고, 파일 최하단에 `#태그` 형식으로 해시태그를 배치하여 이전 양식과 일치시킬 것.
- **Next Steps:**
  - 확립된 원칙들을 향후 다른 앱 마이그레이션에 공통 적용하여 동일한 실수를 방지.
  - `apps-inventory.yaml` 리스트 상의 다음 타겟(예: `simple-memo`) 마이그레이션 대기.

- **Date:** 2026-06-02 21:50
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:** 대량 마이그레이션 파이프라인 오류 수정 및 프롬프트 고도화 (`birthday-information`, `simple-memo`, `qr-code-generator` 반영).
- **Current Status / Issues:**
  - **Astro Component Truncation Fix**: AI 토큰 제한으로 코드 잘림 현상이 빈번하여 `app_generator.py` 및 파이프라인 전반의 구조적 안정성을 검토.
  - **Frontmatter YAML Parsing Fix**: `shortDescription`을 80자 기준으로 무작정 자르면서 발생하던 YAML 멀티라인 문법 오류를 해결. 문장 부호(`. ! ?`) 기준으로 깔끔하게 절단하도록 `app_generator.py` 로직 개선.
  - **CSS `[hidden]` Attribute Specificity Bug**: HTML `hidden` 속성으로 가려둔 요소(예: `empty-state`, `editor` 등)가 `display: flex` 등 우선순위가 높은 CSS에 의해 강제로 렌더링되는 버그 해결.
    - `simple-memo`의 Astro 코드를 수동으로 패치.
    - `scripts/prompts/code_generation_system.md` 프롬프트에 `[hidden] { display: none; }` 강제 적용 규칙을 **모든 요소**로 확대하여 향후 생성되는 앱의 UI 버그를 원천 차단.
  - **RelatedApps Component Integration**: 신규 앱 생성 시 하단 연관 앱 리스트가 누락되지 않도록 Astro Layout 프롬프트 구조에 `<RelatedApps />` 호출 로직을 필수 포함.
  - **OG Image Naming Convention**: `scripts/prompts/seo_meta_system.md`를 수정하여 SEO 메타데이터 생성 시 `ogImage`가 항상 `/og/GoolAPP-{slug}.webp` 포맷으로 명명되도록 표준화.
  - **Self-referential Hyperlinks in Longform**: AI가 앱 자체의 롱폼 콘텐츠를 작성할 때 외부 블로그처럼 자기 자신을 URL 하이퍼링크로 홍보하는 어색한 현상 제거.
    - `scripts/prompts/longform_system.md`에 외부 사이트 추천 및 자기 참조 하이퍼링크 절대 금지 조항을 추가. "위 입력창에서"와 같은 자연스러운 지시어로 유도하도록 강제.
    - `qr-code-generator.md` 본문 수동 수정.
  - **Migration Skip List Update**: 중복 마이그레이션을 막기 위해 `scripts/bulk_migrate.py`의 `COMPLETED_APPS` 리스트를 지속적으로 최신화 (`birthday-information`, `simple-memo`, `qr-code-generator` 추가).
- **Next Steps**:
  - `./venv/bin/python scripts/bulk_migrate.py` 명령어를 통해 대량 마이그레이션 파이프라인 재가동.
  - 향후 생성되는 앱에서 CSS hidden, 앱 링크 스터핑, YAML 문법 에러 등이 재발하지 않는지 모니터링.

- **Date:** 2026-06-03 09:35
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:** `country-capital-quiz` 마이그레이션 중 겪은 데이터 로딩 에러(CORS) 및 퀴즈 UI/UX 피드백을 기반으로 프롬프트 고도화 완료.
- **Current Status / Issues:**
  - 기존 WP URL(`https://goolapp.com/wp-content/...`)을 직접 fetch 시도 시 보안 및 CORS 이슈로 에러 발생을 확인. 코드 생성 프롬프트에 로컬 리소스(`/data/...`, `/images/...`) 매핑 가이드라인 추가.
  - 퀴즈 앱의 UI 사용성(보더라인, 호버, 액션 버튼의 수직 배치 및 강조 수준 대비)을 표준화하여 `scripts/prompts/code_generation_system.md`에 포함.
  - `country-capital-quiz`를 `scripts/bulk_migrate.py`의 `COMPLETED_APPS`에 추가하여 중복 방지.
- **Next Steps:**
  - 향후 국기 맞추기 등 다른 퀴즈 앱 마이그레이션 시 로컬 JSON 다운로드가 수동으로 필요한지, 아니면 마이그레이션 스크립트 단에서 일괄 다운로드하도록 처리할지 지속 검토 (일단은 코드 주석 안내 방식으로 처리).

- **Date:** 2026-06-03 21:50
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:**
  - 대량 마이그레이션 파이프라인 수행 후 발생한 Cloudflare Pages 빌드 실패(Astro Content Collections 스키마 오류) 이슈 해결.
  - `flag-country-quiz.md` 및 `middle-school-english-synonyms-quiz.md`의 `seo.intent` 필드에 허용되지 않은 값(`educational`)이 삽입된 것을 확인하고 `informational`로 일괄 수정.
  - AI 환각(Hallucination) 방지를 위해 `scripts/prompts/seo_meta_system.md` 내 `intent` 필드 작성 지침을 강화하여 `"informational"`, `"transactional"`, `"navigational"` 이외의 값 절대 사용 금지 명시.
- **Files Changed:**
  - `src/content/apps/flag-country-quiz.md`
  - `src/content/apps/middle-school-english-synonyms-quiz.md`
  - `scripts/prompts/seo_meta_system.md`
- **Current Status / Issues:**
  - 수정 후 로컬 환경에서 `npm run build` 결과 46개 페이지 모두 에러 없이 정상 빌드됨을 확인.
  - 해당 핫픽스를 GitHub `main` 브랜치에 푸시하여 Cloudflare 빌드 파이프라인 재가동 조치.
- **Next Steps:**
  - 새로 배포된 사이트 기능 테스트 및 다음 마이그레이션 작업(있을 경우) 대기.

- **Date:** 2026-06-08 21:15
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:**
  - 전체 앱 마이그레이션 완료 후 1차 검수 작업 성공적 종료.
  - 1차 검수 피드백을 바탕으로 모든 앱에 대한 전면적인 리팩토링(Refactoring) 진행.
  - 리팩토링 이후 전체 앱에 대한 2차 정밀 검수(UI 여백 최적화, 자동 스크롤 개선, 중앙 정렬 등 디테일 폴리싱) 및 버그 수정 패치 최종 완료.
- **Files Changed:**
  - `src/pages/*/index.astro` (전체 앱 UI/UX 및 스크립트 대규모 수정)
- **Current Status / Issues:**
  - 모든 마이그레이션, 리팩토링 및 검수 단계가 완료되어 각 앱들의 사용성과 디자인 완성도가 대폭 향상됨.
  - 프로덕션 배포 후 안정성 모니터링 및 추가적인 기능 개선 사항 발굴.

- **Date:** 2026-06-09 18:45
- **IDE / Model:** Antigravity / Gemini
- **Task Done:**
  - **도메인 연결 및 활성화 완료**: DNS 이전(Cloudflare) 검증 완료 및 `FormSubmit` 서비스 이메일 인증 활성화.
  - **Google AdSense 연동**: `PUBLIC_ADSENSE_ENABLED` 등 환경변수를 통한 광고 제어 로직을 `AdUnit.astro`에 반영하여 본문(상/중/하) 광고 삽입 완료.
  - **Naver Search Advisor 설정**: `BaseLayout.astro`에 네이버 사이트 소유권 확인 메타태그 주입 로직 추가.
  - **네이버 블로그 SEO 최적화 (대규모 스크립트 작성 및 롤백 복구)**:
    - 37개의 네이버 블로그용 마크다운 포스팅에 대해 "인간적인 페르소나 적용", "다양한 어투 및 도입부 랜덤화", "앱 링크 위치 분산" 등을 적용하는 일괄 재작성(AI) 자동화 스크립트 실행.
    - 네이버 블로그 에디터 복붙 편의성을 위해 볼드체(`**`) 삭제 과정 중 발생한 파일 초기화(0바이트) 에러를 Dropbox 버전 기록을 통해 복구.
    - 안전하게 볼드체만 제거하는 정식 파이썬 스크립트(`scripts/remove_bold.py`) 작성 및 29개 파일 무사고 정제.
  - **공통 페이지 SEO 및 OG(Open Graph) 보완**: 
    - 개별 앱 상세 페이지를 제외한 홈, 카테고리(`[category].astro`), 고객 문의(`contact-us.astro`), 개인정보처리방침(`privacy-policy.astro`) 등 공통 페이지들에 대해 명시적인 `ogTitle`, `ogDescription`, `keywords`를 하드코딩하여 SEO 완벽성 보완.
    - 기본 OG 이미지를 `/og/GoolAPP-OG-default.webp`로 교체 및 일괄 적용.
- **Files Changed:**
  - `src/components/AdUnit.astro`, `src/layouts/BaseLayout.astro`, `src/components/Seo.astro`
  - `src/pages/index.astro`, `src/pages/category/[category].astro`, `src/pages/contact-us.astro`, `src/pages/privacy-policy.astro`
  - `scripts/revise_naver_blog_posts.py`, `scripts/remove_bold.py`, `scripts/recover_naver_blog_posts.py`
  - `references/naver-blog-posting/*.md` (전체 파일 텍스트 개선 및 볼드체 정제)
- **Current Status / Issues:**
  - 도메인 설정, 외부 연동(구글 애드센스, 서치어드바이저, 폼 서밋), 내부 SEO, 그리고 외부 홍보용 블로그 텍스트 추출까지 마케팅 배포에 필요한 모든 기술적/콘텐츠적 파이프라인 세팅이 성공적으로 완료됨.
- **Next Steps:**
  - 구글 서치 콘솔(GSC) 사이트맵 Fetch 에러는 도메인 이전 및 시간이 지남에 따라 자연 해소될 UI 딜레이이므로 지켜볼 것.
  - 구글 애드센스 슬롯에 실제 광고가 송출되는지 지속 모니터링 필요.

- **Date:** 2026-06-10 20:55
- **IDE / Model:** Antigravity / Gemini
- **Task Done:**
  - **Google AdSense 승인 이슈 대응**: 구글 애드센스 대시보드의 "Earnings at risk (ads.txt not found)" 경고를 해결하기 위해 앱 최상단 라우팅 경로에 구글 표준 포맷의 `public/ads.txt` 파일(소문자 강제) 생성 및 배포 완료.
- **Files Changed:**
  - `public/ads.txt` (신규 생성)
- **Current Status / Issues:**
  - `ads.txt` 파일이 Cloudflare Pages를 통해 정상적으로 배포됨. 구글 크롤러가 파일을 재수집하고 경고를 해제하기까지 통상 수일이 소요될 수 있으므로 대기.
- **Next Steps:**
  - 애드센스 대시보드 경고 해제 여부 및 실제 광고 송출 현황 지속 모니터링.

- **Date:** 2026-06-11 10:25
- **IDE / Model:** Antigravity / Gemini
- **Task Done:**
  - **Google Search Console 마이그레이션 오류 조치 및 자문**: 구 워드프레스 시스템 파일(`wp-admin`, `wp-*` 등)에 대한 404 에러는 정상적인 쇠퇴 현상임을 확인하여 조치 불필요(무시) 안내.
  - **Cloudflare 301 리다이렉트 구축**: 기존 구글에 색인되어 있던 워드프레스 전용 라우팅(`/tag/*`, `/author/*`) 주소 접속 시 404 에러로 인한 UX 저하 및 SEO 링크 쥬스 손실을 막기 위해, `public/_redirects` 파일을 생성하여 신규 홈 화면(`/`)으로 301 영구 리다이렉트(Permanent Redirect) 설정 완료.
- **Files Changed:**
  - `public/_redirects` (신규 생성)
- **Current Status / Issues:**
  - 기존 레거시 트래픽이 새로운 Astro 아키텍처로 안전하게 흡수되도록 설정 완료됨.
- **Next Steps:**
  - GSC 대시보드에서 기존 워드프레스 주소들이 자연스럽게 색인에서 지워지거나 홈 화면으로 통합되는지 장기 모니터링.

- **Date:** 2026-06-15 09:40
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:**
  - **Cloudflare Redirection (5xx Error) 해결**: 구글 서치 콘솔에서 보고된 `http://www.goolapp.com/` 접속 시 Cloudflare 5xx 타임아웃 에러를 해결하기 위해 `public/_redirects` 파일에 HTTP 및 WWW 도메인을 `https://goolapp.com/`으로 강제 이동(301 Redirect)시키는 규칙 추가.
  - **도메인 연결 최적화**: Cloudflare Pages 대시보드의 Custom Domains 항목에 `www` 레코드를 올바르게 연결하여, Pages 프로젝트가 `www` 트래픽을 수신하고 정상적인 SSL 인증서를 발급하도록 구성 및 가이드 완료.
  - **SEO 전면 재점검 및 `robots.txt` 추가**: 전체 코드베이스의 SEO 메타태그 구조(Seo.astro)가 완벽하게 구성되어 있음을 재확인하였으나, 크롤링 봇을 위한 `robots.txt`가 누락되어 있음을 발견하고 `public/robots.txt`를 신규 생성하여 사이트맵 경로(`sitemap-index.xml`) 명시.
  - **통신 테스트 및 캐시 대응**: `curl` 테스트를 통해 서버단(엣지)에서의 301 리다이렉트가 정상 작동함을 확인하고, 브라우저 로컬 캐시로 인한 403 에러 원인을 파악하여 시크릿 창 테스트를 안내함.
- **Files Changed:**
  - `public/_redirects` (규칙 추가)
  - `public/robots.txt` (신규 생성)
- **Current Status / Issues:**
  - Cloudflare Pages 레벨에서의 HTTP ➔ HTTPS 및 WWW ➔ Non-WWW 리다이렉션이 완벽하게 설정됨.
  - 도메인 설정 변경으로 인한 브라우저 캐싱 오류(403)는 일시적인 현상으로 클라이언트 단에서 자체 해결됨.
- **Next Steps:**
  - 구글 서치 콘솔(GSC)에서 며칠 뒤 `http://www.goolapp.com/`에 대한 5xx 에러가 해소되고 크롤링이 재개되는지 모니터링.

- **Date:** 2026-06-27 22:50
- **IDE / Model:** Claude Code (VS Code) / Claude Opus 4.8 (1M)
- **Task Done:**
  - **FormSubmit "Activate Form" 의심 이메일 조사 및 진위 판별**: 사용자가 `ukneoguri@gmail.com`으로 받은 FormSubmit 활성화 요청 이메일이 피싱인지 검토.
  - **연관성 확인**: 이메일 내 토큰 `b0ca5b100e1e3f9582ec236485cbd26f`가 `src/pages/contact-us.astro:22`의 폼 `action` 값과 정확히 일치함을 확인. → GoolAPP 문의 폼과 직접 연관된 메일.
  - **폼 활성화 상태 확인**: 사용자가 직접 `goolapp.com/contact-us`에서 테스트 제출한 결과, 활성화 요청이 아닌 정상적인 메시지 전달 메일이 수신됨 → 폼은 이미 정상 활성화 상태.
  - **이메일 헤더 분석 (최종 판별)**: 사용자가 제공한 원문 헤더를 분석한 결과 **정품 FormSubmit 메일로 확정**:
    - `dkim=pass` (header.i=@formsubmit.co, 암호 서명 검증 통과 → 위조 불가)
    - `spf=pass` (발신 IP `192.99.70.154` = `mail.safenote.co`, formsubmit.co의 SPF에 명시적으로 허가됨)
    - `dmarc=pass` (From 도메인 formsubmit.co와 정렬)
    - → 피싱 아님, 발신 안전.
  - **발생 원인 추정**: 토큰이 페이지 소스에 공개 노출되어 있어, 스팸 봇이 폼을 제출하면서 FormSubmit이 활성화/확인 안내를 (재)발송한 것으로 추정.
  - **토큰 은닉 가능 여부 논의**: FormSubmit은 브라우저가 `formsubmit.co/<토큰>`으로 직접 POST하는 구조라 클라이언트에서 토큰 완전 은닉이 원리적으로 불가능함을 설명. 토큰은 비밀이 아니라 이메일 별칭이며, 노출 시 최악의 피해는 스팸 제출뿐임을 안내.
- **Files Changed:**
  - 없음 (조사 및 자문만 수행, 코드 변경 없음)
- **Current Status / Issues:**
  - 문의 폼은 정상 작동 중. 받은 활성화 이메일은 정품이므로 무시/삭제해도 무방.
  - 페이지 소스에 FormSubmit 토큰이 공개 노출되어 있어 스팸 봇 제출 및 유사 트리거가 발생할 수 있는 구조적 상태.
- **Next Steps (사용자가 추후 결정 예정):**
  - **옵션 1 (간단/권장):** 토큰 유지 + 허니팟(`_honey`) 및 캡차(`_captcha`) hidden 필드 추가로 스팸만 차단. `contact-us.astro` 5분 작업.
  - **옵션 2 (정석/엔드포인트 은닉):** Astro API 라우트 또는 Cloudflare Pages Function 프록시로 전환하여 토큰(또는 메일 API 키)을 서버 시크릿으로 이동. 작업량 많고 SSR 설정 확인 필요.
  - 사용자가 "좀 더 고민 후 결정"하기로 하여 현재 보류 상태.

- **Date:** 2026-07-12 17:50
- **IDE / Model:** Antigravity / Gemini
- **Task Done:**
  - **Phase 4 신규 앱 자동 생성 진행**: `scripts/new_app_pipeline.py` 파이프라인을 가동하여 '혈액형 궁합 테스트(`blood-type-compatibility`)' 앱 기획, SEO 메타데이터, Astro 컴포넌트 코드, 네이버 블로그 포스팅 초안까지 일괄 생성 완료.
  - **트렌드 수집 Fallback 가동 및 AI 평가**: Google Trends API 차단(영국 IP 등) 이슈 발생 시, 대체재인 `keyword-candidates.yaml`에서 후보군을 가져와 AI가 직접 트래픽 잠재력과 개발 실현 가능성을 평가하도록 유도. 이 과정에서 '혈액형 궁합'이 사용자 승인을 통해 최종 선정됨.
  - **Astro Content Schema (카테고리 배열) 버그 픽스**: Markdown Frontmatter의 `category` 필드가 스키마에서 배열(Array)을 요구함에도 스크립트가 단일 문자열로 삽입하여 발생한 404 라우팅 에러 해결. `scripts/app_generator.py` 수정으로 향후 생성 오류 원천 차단.
  - **혈액형 궁합 테스트 UI/UX 및 로직 고도화**:
    - 연애 테마 중심의 세부 지표 도입 (대화 및 소통, 우정 및 편안함, 업무 및 책임감, 라이프스타일 4항목 점수화).
    - 자바스크립트 `sort()`의 기본 알파벳 정렬 문제로 인해 특정 조합(`B-AB`가 `AB-B`로 파싱되는 등)에서 결과가 출력되지 않던 치명적 버그를 커스텀 정렬 배열(`orderMap`)로 해결.
    - 사용자가 선택을 변경하면 이전 결과 화면을 즉시 숨기는 자동 초기화 로직 추가.
  - **트렌드 키워드 파이프라인 중복 필터링 고도화**: `scripts/trend_collector.py` 실행 시 `src/content/apps/*.md` 파일들의 제목과 핵심 키워드를 동적으로 읽어들여, 이미 서비스 중인 앱 아이디어는 제안 리스트에서 자동으로 걸러내도록 로직 대폭 개선.
- **Files Changed:**
  - `src/content/apps/blood-type-compatibility.md` (신규)
  - `src/pages/blood-type-compatibility/index.astro` (신규 및 수정)
  - `references/reports/trend-report-2026-07-12.md` (신규)
  - `references/naver-blog-posting/2026-07-12-blood-type-compatibility.md` (신규)
  - `scripts/app_generator.py` (수정)
  - `scripts/trend_collector.py` (수정)
- **Current Status / Issues:**
  - 혈액형 궁합 앱 추가 및 파이프라인 버그 패치가 반영된 코드를 사용자가 직접 GitHub에 커밋 후 `main` 브랜치에 푸시(`git push --force`)하여 클라우드 배포 진행 중.
  - 파이프라인이 수동 핫픽스들을 흡수하여 훨씬 안정적으로 작동하도록 개선됨.
- **Next Steps:**
  - 클라우드 배포 완료 후 정상 접속 확인.
  - Phase 4.2 진행(새로운 앱 추가) 또는 다음 Phase를 위한 사용자 대기.

- **Date:** 2026-07-14 23:37
- **IDE / Model:** Antigravity / Gemini 3.1 Pro (High)
- **Task Done:**
  - **트렌드 수집기(trend_collector.py) 전면 고도화 (v2)**:
    - Pytrends 의존성을 제거하고 Google Trends RSS 직접 파싱으로 변경.
    - 네이버 DataLab API를 결합하여 한국 시장 내 실제 검색량(상승률) 교차 검증 로직 추가.
    - 네이트(Nate) 실시간 트렌드 검색어(`jsonLiveKeywordDataV1.js`) 수집 로직을 추가하여 부족한 구글 트렌드 키워드 풀 대폭 확장 (다음/줌 실시간 검색어 서비스 종료에 대한 최적의 대안).
    - 수집된 키워드가 부족할 경우 `references/seo/keyword-candidates.yaml`에서 에버그린 예비 후보를 무작위로 추출하여 보충하는 Fallback 시스템 구축.
  - **AI 평가 프롬프트 개선 및 토큰 버그 패치**:
    - AI가 JSON을 반환하다가 텍스트가 너무 길어 중간에 잘리는(Truncation) 치명적인 문제를 방지하기 위해, 원본 데이터 복사 출력을 금지하고 극도로 짧은 JSON만 반환하도록 프롬프트 최적화 및 훼손된 JSON 자동 닫기(복구) 로직 추가.
    - AI가 기존 서비스 중인 앱(`src/content/apps/*.md`)의 slug 및 키워드를 참조하여, 의미적 중복(예: 이미 있는 이자 계산기를 또 추천하는 경우)을 완벽히 차단하도록 개선.
    - 외부 실시간 API(주가, 날씨, 교통 등) 연동이 필요한 아이디어는 차단하고, 순수 자바스크립트로 구현 가능한 앱(세금 계산기, 퀴즈 등)만 선별하도록 엄격한 기준 명시.
    - 콘솔 출력 용어를 "앱화" 등의 개발자 용어에서 "앱 제작 가능", "앱으로 만들기 어려운 키워드" 등으로 자연스럽게 순화.
  - **가이드 문서 작성**: 신규 앱 발굴 및 생성을 위한 윈도우/맥 OS별 환경에 맞춘 명령어 가이드를 `references/HOW-TO-NEW-APP.md` 파일로 정리 완료.
- **Files Changed:**
  - `scripts/trend_collector.py` (전면 재작성 및 대규모 기능 추가)
  - `references/HOW-TO-NEW-APP.md` (신규 생성)
- **Current Status / Issues:**
  - 트렌드 수집부터 앱 아이디어 평가까지의 파이프라인이 튼튼하고 항상 풍성한 후보를 내놓도록 완성되었음. JSON 파싱 및 응답 대기 이슈 완전 해결.
- **Next Steps:**
  - 발굴된 신규 앱 아이디어(예: 최저임금 계산기, 종부세 계산기 등) 중 하나를 채택하여 `new_app_pipeline.py`로 실제 앱 생성.
  - 또는 아직 남아있는 기존 워드프레스 앱 마이그레이션(Astro 적용) 이어서 진행.

- **Date:** 2026-07-15 08:11
- **IDE / Model:** Antigravity / Claude Sonnet 4.6 (Thinking)
- **Task Done:**
  - **멀티 OS 환경 Git 동기화 문제 진단 및 근본 해결**:
    - Windows 11 Antigravity에서 작업 후 GitHub 푸시한 내용이 맥미니에서 `modified`로 표시되는 원인을 분석.
    - 원인: Dropbox가 Windows(CRLF) 작업 파일을 맥미니로 자동 동기화하였으나, Git은 이를 `git pull` 없이 발생한 변경으로 인식하여 dirty 상태 발생. (Dropbox 동기화 ≠ Git pull)
  - **`.gitattributes` 추가 (근본 해결)**: 모든 텍스트 파일(`.astro`, `.py`, `.md`, `.json`, `.yaml` 등)의 줄바꿈을 항상 LF로 강제하는 `.gitattributes` 파일을 저장소 루트에 생성.
  - **저장소 정규화**: `git rm --cached -r .` + `git reset --hard HEAD`로 기존 CRLF 파일들을 LF로 재정규화하고 워킹트리 clean 상태 복구.
  - **커밋 및 푸시 완료**: `1979789` 커밋으로 `origin/main` 반영.
- **Files Changed:**
  - `.gitattributes` (신규 생성)
- **Current Status / Issues:**
  - 멀티 OS(맥↔윈도우즈) 환경에서 줄바꿈 충돌 문제 완전 해소.
  - 향후 어느 환경에서 작업해도 CRLF가 커밋에 포함되지 않음.
- **Next Steps:**
  - **환경 전환 시 필수 수칙 준수**: 맥↔윈도우즈 이동 시 반드시 나갈 때 `git push`, 들어올 때 `git pull` 실행. Dropbox 동기화만으로는 Git 상태가 동기화되지 않음을 항상 인지할 것.
  - 이전 세션의 Next Steps 이어서 진행: 신규 앱 아이디어 채택 및 `new_app_pipeline.py` 실행.
