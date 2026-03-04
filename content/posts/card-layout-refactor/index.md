---
title: '블로그 카드 레이아웃 개선 과정'
date: 2026-03-04T18:00:00+09:00
tags: ['blog', 'hugo', 'css', 'layout']
cover:
  image: 'images/cover.jpg'
  alt: 'Card Layout Refactor'
  relative: true
---

맥에서 멀쩡하던 카드 레이아웃이 윈도우 모니터에서 너무 크게 보이는 문제를 고치면서 구조 자체를 뜯어고친 과정을 정리함.

## 문제: 모니터마다 카드 크기가 달라짐

맥에서 볼 때는 카드 높이가 적당했는데, 윈도우 모니터로 보니 카드가 너무 커졌음. 원인은 카드 높이를 `65vh`로 잡아놨기 때문이었음. `vh`는 뷰포트 높이 기준이라 모니터가 크면 그냥 비례해서 커짐.

가로폭도 마찬가지였음. 그리드 컨테이너를 `max-width: 90vw`로 잡아놨는데, 27인치 모니터에서는 `90vw`가 엄청 넓어짐.

## 카드 높이 고정 시도

처음엔 `vh`를 픽셀로 바꾸는 것만 해봤음.

```css
.post-entry {
  height: 400px; /* 65vh → 고정 픽셀 */
}
```

모니터 간 차이는 없어졌는데, 이미지 비율이 깨지거나 텍스트가 카드 밖으로 넘치는 경우가 생겨서 만족스럽지 않았음.

## 다른 블로그 참고

비슷한 구조로 잘 만들어진 블로그([hyper-accel.github.io](https://hyper-accel.github.io))를 참고했음. 같은 PaperMod 테마에 2열 카드 그리드를 쓰고 있었는데, 구조 자체가 달랐음.

핵심 차이는 두 가지였음.

**1. 커스텀 `list.html` 템플릿**

기존에는 PaperMod 기본 템플릿의 `.main` 요소를 CSS로 억지로 그리드로 만들었음. 저 블로그는 `layouts/_default/list.html`을 직접 만들어서 포스트들을 `.posts-grid-container` div로 감싸고 있었음.

```html
<div class="posts-grid-container">
  {{ range $paginator.Pages }}
  <article class="post-entry">...</article>
  {{ end }}
</div>
```

CSS가 특정 클래스를 정확히 타겟하니까 훨씬 깔끔했음.

**2. 이미지 높이를 고정하지 않음**

`aspect-ratio`나 고정 픽셀 없이 `height: auto`로 이미지 원본 비율 그대로 표시했음. 같은 행의 카드들은 그리드가 알아서 높이를 맞춰줌.

```css
.post-entry .entry-cover img {
  width: 100%;
  height: auto;
  object-fit: cover;
}
```

## 개선 결과

참고한 블로그 CSS와 구조를 적용하면서 달라진 것들:

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 카드 높이 | `65vh` 고정 | 콘텐츠에 맞게 동적 |
| 이미지 높이 | `flex: 1`로 카드 꽉 채움 | 원본 비율 유지 |
| 그리드 적용 방식 | `.main`에 CSS 해킹 | 커스텀 `list.html` |
| 가로폭 기준 | `90vw` | `1024px` 고정 |

## 로컬 이미지 적용

이 과정에서 외부 URL 이미지 대신 로컬 이미지도 써봤음. Hugo의 **페이지 번들** 구조를 쓰면 됨.

```
content/posts/
└── 글-제목/
    ├── index.md
    └── images/
        └── cover.jpg
```

프론트매터에서 이렇게 경로를 잡으면 Hugo가 번들 내 이미지를 리소스로 인식하고 자동으로 처리함.

```yaml
cover:
  image: 'images/cover.jpg'
  relative: true
```

외부 URL은 언제든 깨질 수 있으니 실제 글에는 로컬 이미지를 쓰는 게 나음.

## 마치며

`vh`나 `vw` 같은 뷰포트 단위는 반응형으로 써야 할 때는 좋은데, 카드 높이처럼 일정한 크기가 필요한 곳에 쓰면 모니터마다 결과가 달라짐. 처음부터 잘 만들어진 레퍼런스를 보고 구조를 잡는 게 시행착오를 줄이는 방법인 것 같음.
