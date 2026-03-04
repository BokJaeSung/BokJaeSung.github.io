---
title: 'GitHub Pages 블로그 세팅 과정'
date: 2026-03-04T12:00:00+09:00
tags: ['blog', 'hugo', 'github-pages']
cover:
  image: 'images/cover.jpg'
  alt: 'Blog Setup'
  relative: true
---

Hugo + GitHub Pages로 블로그를 세팅하면서 겪은 문제들을 정리함.

## CSS가 아예 안 먹히는 문제

처음 배포했을 때 스타일이 전혀 적용되지 않았음. Chrome 개발자도구를 열어보니 이런 에러가 있었음.

```
Failed to find a valid digest in the 'integrity' attribute for resource
'stylesheet.css' with computed SHA-256 integrity '...'.
The resource has been blocked.
```

**SRI(Subresource Integrity)** 해시 불일치 문제였음.

Hugo는 빌드할 때 CSS 파일의 SHA-256 해시를 계산해서 HTML의 `integrity` 속성에 자동으로 박아줌. 브라우저는 이 값을 실제 파일이랑 대조해서 위변조 여부를 검증하는데, 값이 다르면 보안상의 이유로 파일 로드를 차단함.

문제는 Hugo 소스 없이 빌드 결과물만 저장소에 올리다 보니, CSS 파일이 바뀌어도 HTML의 해시값이 자동으로 갱신이 안 됐던 것.

## Hugo 소스 자체가 없었던 문제

근본적인 원인은 Hugo 소스(`hugo.toml`, `content/`, `themes/` 등)가 아예 없고 빌드 결과물만 저장소에 있었다는 점이었음. Hugo는 소스를 기반으로 HTML을 생성할 때 해시값도 함께 계산해서 삽입해주는데, 소스가 없으니 이 과정이 생략된 것.

이를 해결하기 위해 저장소 구조를 다음과 같이 바꿈.

- `main` 브랜치: Hugo 소스 파일 관리 (직접 편집하는 공간)
- `gh-pages` 브랜치: Hugo가 빌드한 결과물 (GitHub Actions가 자동 관리)

```
main에 push
  → GitHub Actions 실행
    → hugo --minify 빌드
      → gh-pages 브랜치에 결과물 자동 배포
```

이제 글 쓸 때는 `content/posts/` 아래에 마크다운 파일만 작성하고 push하면 나머지는 알아서 처리됨.

## 레이아웃 커스텀

블로그 구조가 잡히고 나서 보기 좋게 다듬었음.

### 2열 카드 그리드

PaperMod 기본 레이아웃은 글 목록이 1열로 쭉 나열되는 형태였음. 2열 그리드로 바꾸기 위해 커스텀 `list.html` 템플릿을 추가해서 포스트들을 `.posts-grid-container`로 감싸고, CSS Grid로 레이아웃을 잡았음.

```css
.posts-grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2rem;
}
```

### 카드 스타일

카드에 둥근 모서리, 테두리, 패딩을 주고 호버 시 살짝 떠오르면서 그림자가 생기게 했음. 커버 이미지는 이미지 원본 비율대로 표시되고, 호버 시 약간 확대됨.

```css
.post-entry {
  border-radius: 1.25rem;
  padding: 1.5rem;
}

.post-entry:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
```

### 글 본문 너비

PaperMod 기본 본문 너비가 너무 좁았음. `.post-single`에 `max-width: 70vw`를 줘서 화면의 70%까지 넓어지도록 했음.

## 마치며

HTML 파일 직접 올리는 방식에서 Hugo 소스 기반 자동 배포 구조로 전환하면서 구조가 많이 깔끔해졌음. 이제 글만 쓰면 나머지는 GitHub Actions가 알아서 처리해줌.
