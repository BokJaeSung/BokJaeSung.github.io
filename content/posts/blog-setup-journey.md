---
title: 'GitHub Pages 블로그 세팅 과정'
date: 2026-03-04T12:00:00+09:00
tags: ['blog', 'hugo', 'github-pages']
cover:
  image: 'https://picsum.photos/seed/blog/800/400'
  alt: 'Blog Setup'
---

GitHub Pages 블로그를 세팅하면서 겪은 문제들과 해결 과정을 정리해보았습니다.

## CSS가 적용되지 않는 문제

블로그를 처음 배포했을 때 스타일이 전혀 적용되지 않는 문제가 있었습니다. 원인을 찾기 위해 Chrome 개발자도구를 열어보니 다음과 같은 에러가 있었습니다.

```
Failed to find a valid digest in the 'integrity' attribute for resource
'stylesheet.css' with computed SHA-256 integrity '...'.
The resource has been blocked.
```

이는 **SRI(Subresource Integrity)** 해시 불일치 문제였습니다.

Hugo는 빌드 시 CSS 파일의 SHA-256 해시를 계산해 HTML의 `integrity` 속성에 자동으로 삽입합니다. 브라우저는 이 값을 실제 파일과 대조해 위변조 여부를 검증하고, 값이 다르면 보안상의 이유로 파일 로드를 차단합니다.

문제는 Hugo 소스 없이 빌드 결과물만 저장소에 올리다 보니, CSS 파일이 변경되었을 때 HTML의 해시값이 자동으로 갱신되지 않은 것입니다. 해결 방법은 실제 CSS 파일의 해시를 다시 계산해 HTML에 반영하는 것이었습니다.

```bash
cat stylesheet.css | openssl dgst -sha256 -binary | base64
```

## Hugo 소스 없이 관리하던 문제

근본적인 원인은 Hugo 소스(`hugo.toml`, `content/`, `themes/` 등)가 없고 빌드 결과물만 저장소에 있었다는 점입니다. Hugo는 소스를 기반으로 HTML을 생성할 때 해시값도 함께 계산해 삽입해주는데, 소스가 없으니 이 과정이 생략된 것입니다.

이를 해결하기 위해 저장소 구조를 다음과 같이 개편했습니다.

- `main` 브랜치: Hugo 소스 파일 관리 (직접 편집하는 공간)
- `gh-pages` 브랜치: Hugo가 빌드한 결과물 (GitHub Actions가 자동 관리)

```
main에 push
  → GitHub Actions 실행
    → hugo --minify 빌드
      → gh-pages 브랜치에 결과물 자동 배포
```

이제 글을 쓸 때는 `content/posts/` 아래에 마크다운 파일만 작성하고 push하면 나머지는 자동으로 처리됩니다.

## 마치며

단순히 HTML 파일을 올리는 방식에서 Hugo 소스 기반의 자동 배포 구조로 전환하면서, 앞으로는 글 작성에만 집중할 수 있게 되었습니다.
