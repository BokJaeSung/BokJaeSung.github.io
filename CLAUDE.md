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

## 포스트 작성 시 체크리스트

- [ ] `content/posts/{슬러그}/index.md` 생성
- [ ] `images/cover.jpg` 존재하는지 확인
- [ ] frontmatter 형식 맞는지 확인 (date 시간대, summary 영문)
- [ ] HTML 사용 시 `rawhtml` shortcode로 래핑했는지 확인
- [ ] 커밋 후 push
