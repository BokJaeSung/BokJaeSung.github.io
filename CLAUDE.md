# CLAUDE.md — BokJaeSung.github.io 블로그 운영 가이드

Hugo PaperMod 기반 GitHub Pages 블로그. 학습 내용 아카이빙 목적으로 운영 중.

---

## 프로젝트 구조

```
content/posts/{포스트-슬러그}/
  index.md          ← 본문
  images/
    cover.jpg       ← 커버 이미지 (필수)
```

- `main` 브랜치에 push → GitHub Actions → `hugo --minify` 빌드 → `gh-pages` 자동 배포
- 포스트 작성 후 반드시 커밋하고 push해야 배포됨

---

## Frontmatter 형식

```yaml
---
title: "시리즈명.번호 제목"
date: 2026-04-11T09:00:00+09:00
tags: ["태그1", "태그2"]
cover:
  image: 'images/cover.jpg'
  alt: '제목과 동일하게'
  relative: true
summary: "영문으로 한 줄 요약. 핵심 키워드 포함."
---
```

**규칙:**
- `title`: 시리즈가 있으면 `APS.05`, `React.02` 형식 접두어 사용
- `date`: 한국 시간 기준 (`+09:00`), 시각은 `09:00:00`으로 통일
- `tags`: 소문자 또는 한글, 배열 형식
- `summary`: 영문 한 문장. 독자가 읽을지 말지 판단할 수 있을 정도로 구체적으로
- `cover.image`: 항상 `images/cover.jpg`, `relative: true` 고정

---

## 본문 구성 순서

### 기술/알고리즘 포스트 (APS 시리즈 등)

```
1. 전체 흐름  ← ASCII 다이어그램으로 구조 한눈에 보여주기
2. 핵심 개념  ← 개념별로 H2 섹션 분리, 표/코드블록 적극 활용
3. 구현 코드  ← 언어 명시 (```python, ```cpp 등)
4. 시각화/애니메이션 (있으면)  ← rawhtml shortcode로 래핑
5. 마치며 (선택)  ← 짧게, 핵심 한 줄 정리
```

### 개념/프레임워크 포스트 (React 시리즈 등)

```
1. 도입 한 줄  ← 무엇을 다루는지 명확하게
2. 구조/흐름 다이어그램
3. 개념별 H2 섹션
4. 표로 비교 (해당되면)
5. 실제 코드 예시
```

---

## 스타일 규칙

- **문체**: 간결하게. 불필요한 서론 없이 바로 본론.
- **코드블록**: 언어 항상 명시. 주석은 핵심만.
- **표**: 비교가 필요한 곳엔 적극 사용 (시간복잡도, 옵션 비교 등)
- **다이어그램**: ASCII 박스/화살표로 구조 시각화. 복잡한 애니메이션은 HTML로.
- **HTML 삽입**: Hugo rawhtml shortcode 필수 래핑
  ```
  {{< rawhtml >}}
  <div>...</div>
  {{< /rawhtml >}}
  ```
- **다크테마**: HTML 직접 작성 시 색상은 CSS 변수 또는 다크/라이트 모두 보이는 값 사용

---

## 커밋 메시지 형식

```
post: {포스트 제목 또는 슬러그}
fix: {수정 내용 요약}
docs: {문서 변경 내용}
chore: {빌드/설정 관련}
```

예시:
```
post: APS.05 Graph Problems
fix: APS.05 다크테마 색상 수정
```

---

## APS 시리즈 포스트 스타일 레퍼런스 (APS.06 기준)

### 목차
- 문서 최상단(frontmatter 바로 다음, 도입 문단보다 위)에 배치
- 소제목 `## 0. Contents`를 목차 박스 바로 위에 명시
- 접기/펼치기 없이 항상 펼쳐진 상태 (`<details>` 사용 안 함)
- 스타일: 배경 투명, 테두리는 `var(--primary,#888)` 1.5px + 은은한 `box-shadow`로 눈에 띄게
- 메인 항목: `var(--primary,inherit)` 색상 + `font-weight:600`, 글자 크기 16px
- 서브 항목(예: `3.1`, `5.1`): `var(--secondary,inherit)` 색상, 들여쓰기, 글자 크기 15px
- 라벨 텍스트("목차 — Table of Contents" 등)는 넣지 않음 — `## 0. Contents` 제목이 그 역할을 대신함
- 섹션 번호는 `0.`부터 시작 가능 (Contents 자신이 0번)

```html
{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-..." style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. ...</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#11-..." style="color:var(--secondary,inherit);text-decoration:none;">1.1 서브항목</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}
```

### 섹션 헤딩
- 헤딩 텍스트는 **영문 우선**. 한글 헤딩은 앵커 ID가 한글로 생성되어 목차 링크 관리가 번거로움
- 목차 링크 앵커는 헤딩 텍스트 기반 자동 생성 규칙 따름 (소문자, 공백→`-`, 특수문자 제거)

### 인터랙티브 애니메이션 (d3.js)
- d3.js CDN을 해당 섹션 `<script>` 바로 위에 로드
  ```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
  ```
- 같은 페이지에 d3 애니메이션이 여러 개여도 `<script src>` 태그는 **첫 번째 애니메이션 앞에 1개만** 두면 됨 (d3는 전역에 남아있어 이후 스크립트에서 재사용 가능)
- 색상 팔레트 (다크 배경 기준):
  - tree edge: `#34d399`, back edge: `#f87171`, cross edge: `#fbbf24`
  - 활성 노드: `#58a6ff`, 완성된 SCC: `#fbbf24` / `#f472b6` / `#34d399` / `#a78bfa` / `#60a5fa`
  - 배경: `linear-gradient(135deg, #1e3050, #253c60, #1c2d50)`

### Q & A 섹션
- 깊은 개념 질문들은 `## 5. Q & A` 하나로 묶고 `### 5.1`, `### 5.2` ... 형식으로 나열
- 목차에서는 `Q1.`, `Q2.` ... 형식으로 표기

---

## K8sPatterns 시리즈 스타일 레퍼런스 (K8sPatterns.25 기준)

『Kubernetes Patterns』 각 장을 한 편으로 정리하는 시리즈. 책 내용을 옮겨 적는 게 아니라
**"왜 이렇게 설계됐는가"를 비유와 함정 중심으로 재구성**하는 것이 이 시리즈의 성격이다.

### frontmatter
```yaml
series: ["K8sPatterns"]          # ← 시리즈 내비게이션용, 반드시 첫 줄
title: "K8sPatterns.25 Secure Configuration"   # 접두어 + 책의 영문 패턴명
tags: ["kubernetes", "cloud-native", "devops", ...]  # 앞 3개는 고정
summary: "한글 한 문장. 이 장의 결론을 미리 말해버린다."   # 이 시리즈만 한글 허용
```

### 문서 구조

```
0. Contents          목차 박스 (rawhtml)
1. Overview          ASCII 요약 다이어그램 + 도입 2문단
2. Problem           2.1~2.4  왜 이 패턴이 필요한가
3. {첫 번째 축}       3.1~3.x  해법 A 계열
4. {두 번째 축}       4.1~4.x  해법 B 계열
5. Discussion        5.1~5.x  + "### 핵심 메시지"
6. References        rawhtml 인용 박스
```

- **3·4장은 "Solution"이라고 쓰지 않고 내용으로 이름 짓는다**
  (예: `3. Out-of-Cluster Encryption — 잠가서 내보내기` / `4. Centralized Secret Management — 아예 저장하지 않기`)
- 해법이 한 갈래뿐이면 3장 하나로 두고 4장은 만들지 않는다
- 큰 절 안의 세부는 `#### 3.2.1` 처럼 3단계까지 내려간다.
  **판단 기준: 다른 도구와 나란히 설 수 있으면 3.x, 특정 도구의 내부 이야기면 3.2.x**
- 목차 3단계 항목은 `padding-left:18px; font-size:14px` 로 한 칸 더 들여쓴다
- `### 핵심 메시지`와 References의 항목은 목차에 넣지 않는다

### 섹션 제목
- `번호 + 영문 키워드 — 한글 요약` 형식. 대시(`—`) 뒤가 그 절의 결론이다
  - `3.2 Sealed Secrets — 우편함 방식`
  - `3.5 deny-all로 시작하라 — 빈 리스트와 빈 규칙의 함정`
- 제목만 훑어도 장 전체가 읽히도록 쓴다

### Overview의 ASCII 요약
코드블록 안에 장 전체를 한 장으로 압축한다. 제목 + `━` 구분선 + 흐름.

```
{패턴명} 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{한 줄 요지}

  기본 상태: ...  ← 문제의 출발점
                        │  왜 문제인지 한 줄
                        ▼
  1겹: ...
  ├─ ...
  └─ ...
                        ▼
  {결론 한 줄} 🔒
```

- 이어지는 도입 문단은 **앞 장과 연결**하며 시작한다
  (예: "24장이 뚫린 파드의 손이 옆으로 뻗지 못하게 막는 이야기였다면, 25장은 그 손이 쥐려는 물건 자체를 숨기는 이야기다.")

### 핵심 메시지 (Discussion 끝)
코드블록 안에 `축 → 내용` 형식으로 정리하고, 바로 아래 `>` 인용구로 한 문단 결론.

```
{패턴명} 의 몫: {한 줄}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

전제      → ...
문제      → ...
1겹       → ...
  하위      들여쓰기로 도구별 한 줄
함정      → ...
결론      → ...
```

### 문체
- **볼드(`**`)를 쓰지 않는다.** 강조는 문장 구조로 한다
- 단정적으로, 짧게. 대시(`—`)로 부연을 붙이는 리듬
- 과장 금지: "발가벗겨진다", "목숨 걸고", "지옥", "큰일" 같은 표현 대신
  "평문과 같다", "엄격히 지킨다", "복구할 수 없다"
- 책에 대한 평가를 넣어도 된다 ("책의 총평도 솔직하다", "책이 눈에 띄는 오탈자는")

### 이 시리즈만의 장치
- **비유를 하나 정해 절 끝까지 밀고 간다** — 우편함(Sealed Secrets), 은행 주소+카드/출금 요청서(SecretStore/ExternalSecret), 금고(SMS), 검문소(PSA), 개찰구
- **함정 문단** — "여기서 두 가지 함정.", "실무 팁 하나 —" 로 시작해 실제로 겪는 에러 메시지까지 적는다
  (예: `no key could decrypt secret` 이 뜨면 십중팔구 스코프 문제다)
- **공격 시나리오** — 왜 이 제약이 있는지 설명할 때 악용 흐름을 코드블록으로 보여준다
- **비교표** — `| 구분 | A | B |` 형식. 판단 기준이 되는 축을 세로로
- **앞 장 상호참조** — "23장 3.5의 capability와 정확히 같은 함정이고, 답도 같다"
  시리즈를 관통하는 원리(기록 먼저·강제는 나중에, 기본값 뒤집기)를 반복해서 연결한다

### 코드블록
- `yaml` / `bash` 명시. 주석으로 포인트 표시 — `# ★ 실무 비권장 (4.1.1)`
- 개념 다이어그램은 언어 없는 ``` 블록에 ASCII로
- 한글은 모노스페이스에서 폭이 어긋나므로 **ASCII 박스 안에는 한글을 넣지 않는다**

### 책 그림 재현 (인라인 SVG)
책의 Figure는 이미지 파일이 아니라 인라인 SVG로 그린다.

```html
{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 380" style="width:100%;min-width:600px;height:auto;font-family:inherit;"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{그림 설명}">
  <defs>
    <marker id="xx-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
            orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/></marker>
    <path id="xx-doc" d="M0,0 h130 v40 c-21.7,0 -21.7,8 -43.3,8 c-21.7,0 -21.7,-8 -43.3,-8 c-21.7,0 -21.7,8 -43.3,8 z"/>
  </defs>
  ...
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  {캡션 — 그림이 말하는 결론}
</div>
</div>
{{< /rawhtml >}}
```

- 팔레트: 리소스 문서 `#e8952f`(주황) / `#fbe0c4`(연주황, 글자 `#5a3d18`) / `#4caf82`(초록)
  컴포넌트 `#5b9bd5`(파랑) / `#cfe3f5`(연파랑, 글자 `#1b3f63`) / 외부 서비스 `#c0392b`(빨강) / KMS `#8e44ad`
- 글자·화살표는 `var(--content)`, 점선 테두리는 `var(--secondary)` — 다크·라이트 양쪽 대응
- **한 페이지에 여러 그림이 있으므로 `marker`/`path` id에 그림별 접두사를 붙인다** (`es-`, `ss-`, `sp-`, `cs-`, `vi-`)
- 화살표는 반드시 도형 경계에 붙인다 (도형 끝에서 4~6px 띄우고 화살촉이 닿게)
- 그림을 넣었으면 같은 내용의 ASCII 다이어그램은 지운다

### References
`rawhtml` 인용 박스에 **원문 영어 + [해석] + 본문 어느 절의 근거인지**를 함께 적는다.

```html
{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>{무엇이 어디에 명시되어 있는지}</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "{원문 인용}"
  </blockquote>
  <div>[해석] "{번역}" — {본문 3.5의 근거다}</div>
  <div style="margin-top:10px;">→ <a href="...">{사이트 — 문서명}</a></div>
</div>
{{< /rawhtml >}}
```

- 책의 오탈자·부정확한 서술을 발견하면 여기에 적는다
- 공식 문서를 1순위로. 블로그를 인용할 땐 어느 섹션인지까지 특정한다

---

## 포스트 작성 시 체크리스트

- [ ] `content/posts/{슬러그}/index.md` 생성
- [ ] `images/cover.jpg` 존재하는지 확인
- [ ] frontmatter 형식 맞는지 확인 (date 시간대, summary 영문)
- [ ] HTML 사용 시 `rawhtml` shortcode로 래핑했는지 확인
- [ ] 커밋 후 push
