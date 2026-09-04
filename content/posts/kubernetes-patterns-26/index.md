---
series: ["K8sPatterns"]
title: "K8sPatterns.26 Access Control"
date: 2026-09-04T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "security", "rbac", "serviceaccount", "operator"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.26 Access Control'
  relative: true
summary: "API 서버로 가는 모든 요청은 인증·인가·어드미션 세 관문을 지난다. RBAC로 권한을 쪼개, 파드 하나가 뚫려도 피해가 거기서 끝나게 한다."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-100만-개의-열린-문--잠그지-않아서-뚫린다" style="color:var(--secondary,inherit);text-decoration:none;">2.1 100만 개의 열린 문 — 잠그지 않아서 뚫린다</a></div>
    <div><a href="#22-인증과-인가--누구인가와-무엇을-할-수-있는가" style="color:var(--secondary,inherit);text-decoration:none;">2.2 인증과 인가 — 누구인가와 무엇을 할 수 있는가</a></div>
    <div><a href="#23-오퍼레이터의-딜레마--구조상-큰-권한이-필요하다" style="color:var(--secondary,inherit);text-decoration:none;">2.3 오퍼레이터의 딜레마 — 구조상 큰 권한이 필요하다</a></div>
  </div>
  <div><a href="#3-세-관문--모든-요청이-지나는-길" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. 세 관문 — 모든 요청이 지나는 길</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-api-서버는-문이-하나다" style="color:var(--secondary,inherit);text-decoration:none;">3.1 API 서버는 문이 하나다</a></div>
    <div><a href="#32-인증--다섯-개의-입구-하나의-출구" style="color:var(--secondary,inherit);text-decoration:none;">3.2 인증 — 다섯 개의 입구, 하나의 출구</a></div>
    <div><a href="#33-사용자-표현--인증이-남기는-것" style="color:var(--secondary,inherit);text-decoration:none;">3.3 사용자 표현 — 인증이 남기는 것</a></div>
    <div><a href="#34-어드미션-컨트롤--내용물을-보는-마지막-검문" style="color:var(--secondary,inherit);text-decoration:none;">3.4 어드미션 컨트롤 — 내용물을 보는 마지막 검문</a></div>
  </div>
  <div><a href="#4-subject--누구인가" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Subject — 누구인가</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-user--리소스가-아니라-문자열이다" style="color:var(--secondary,inherit);text-decoration:none;">4.1 User — 리소스가 아니라 문자열이다</a></div>
    <div><a href="#42-serviceaccount--파드의-신분증" style="color:var(--secondary,inherit);text-decoration:none;">4.2 ServiceAccount — 파드의 신분증</a></div>
    <div><a href="#43-토큰은-어떻게-들어오나--secret-에서-projected-로" style="color:var(--secondary,inherit);text-decoration:none;">4.3 토큰은 어떻게 들어오나 — Secret 에서 projected 로</a></div>
    <div><a href="#44-group--명단은-클러스터-밖에-있다" style="color:var(--secondary,inherit);text-decoration:none;">4.4 Group — 명단은 클러스터 밖에 있다</a></div>
  </div>
  <div><a href="#5-rbac--무엇을-할-수-있는가" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. RBAC — 무엇을 할 수 있는가</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-role--세-축으로-권한을-쪼갠다" style="color:var(--secondary,inherit);text-decoration:none;">5.1 Role — 세 축으로 권한을 쪼갠다</a></div>
    <div><a href="#52-rolebinding--권한을-붙인다는-것의-의미" style="color:var(--secondary,inherit);text-decoration:none;">5.2 RoleBinding — 권한을 붙인다는 것의 의미</a></div>
    <div><a href="#53-네-가지-조합--범위는-바인딩이-정한다" style="color:var(--secondary,inherit);text-decoration:none;">5.3 네 가지 조합 — 범위는 바인딩이 정한다</a></div>
    <div><a href="#54-집계--파이프는-그대로-두고-물통을-채운다" style="color:var(--secondary,inherit);text-decoration:none;">5.4 집계 — 파이프는 그대로 두고 물통을 채운다</a></div>
    <div><a href="#55-디버깅--추측하지-말고-물어봐라" style="color:var(--secondary,inherit);text-decoration:none;">5.5 디버깅 — 추측하지 말고 물어봐라</a></div>
  </div>
  <div><a href="#6-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#61-세-가지-조언--필요-없는-건-주지-마라" style="color:var(--secondary,inherit);text-decoration:none;">6.1 세 가지 조언 — 필요 없는 건 주지 마라</a></div>
    <div><a href="#62-24장과의-구분--조작-권한-vs-통신-권한" style="color:var(--secondary,inherit);text-decoration:none;">6.2 24장과의 구분 — 조작 권한 vs 통신 권한</a></div>
    <div><a href="#63-모든-것이-리소스다--질문조차" style="color:var(--secondary,inherit);text-decoration:none;">6.3 모든 것이 리소스다 — 질문조차</a></div>
  </div>
  <div><a href="#7-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. References</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Access Control 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"뚫리는 건 막을 수 없다. 뚫렸을 때 닿는 범위를 미리 줄인다"

  API 서버 = 클러스터의 유일한 문
    kubectl 도, 오퍼레이터도, 스케줄러 자신도 여기로만 들어온다. 뒷문이 없다
                        │
                        ▼
  1관문: Authentication — "너 누구야?"
  ├─ OIDC / X.509 / 프록시 / 정적 토큰 / 웹훅 — 다섯 중 하나만 통과하면 끝
  ├─ 쿠버네티스에는 계정 시스템이 없다. 회사가 쓰던 것을 콘센트처럼 꽂는다
  └─ 어느 문으로 들어왔든 결과물은 한 형태: username + groups
                        ▼
  2관문: Authorization — "그거 해도 돼?"        ◀── 개발자의 영역
  ├─ RBAC = Role(권한 목록) + RoleBinding(연결선), 둘은 분리돼 있다
  ├─ 거부 규칙이 없다. 허용만 쌓이고, 한 군데서만 걸려도 통과
  └─ 막히면 403 Forbidden
                        ▼
  3관문: Admission Control — "내용이 규칙에 맞아?"
  ├─ 앞의 둘과 달리 YAML 안을 열어본다
  └─ Mutating(고쳐 넣음) → Validating(검사)
                        ▼
  셋을 다 통과해야 비로소 etcd 에 기록된다 🔒
```

24장이 파드가 **밖으로 뻗는 손**을 자르는 이야기였다면, 26장은 그 손이 **쿠버네티스 자신을 조작하려 할 때** 무엇을 허락할지 정하는 이야기다. 24장의 대상은 파드에서 파드로 가는 HTTP였고, 26장의 대상은 파드에서 API 서버로 가는 요청이다.

이 장의 재미는 쿠버네티스가 **자기 신분 관리를 하지 않기로 결정했다**는 데 있다. `kubectl create user` 같은 명령은 없다. 사람 계정은 회사 시스템에 맡기고, 쿠버네티스는 인증 결과로 넘어온 **문자열 몇 개**만 보고 권한을 판단한다. 반대로 파드는 자기가 만들었으니 신분증도 자기가 발급한다. 이 비대칭이 이 장의 거의 모든 구조를 설명한다.

---

## 2. Problem

### 2.1 100만 개의 열린 문 — 잠그지 않아서 뚫린다

2022년, 보안 연구자들이 인터넷에 노출된 쿠버네티스 인스턴스를 약 100만 개 찾아냈다. 특별한 기술이 필요하지도 않았다 — 스캐너를 돌렸더니 그냥 열려 있었다.

주목할 점은 **해킹당한 게 아니라는 것**이다. 취약점을 뚫은 게 아니라, 안내 데스크에 아무도 앉히지 않은 건물로 걸어 들어간 것에 가깝다. 24장의 flat network가 "기본값이 다 열림"이었듯, 여기서도 원인은 같다 — **잠그는 일을 아무도 안 했다.**

이 장의 무대를 건물로 그려두면 뒤가 편하다.

```
클러스터        = 회사 건물
API 서버        = 정문 안내 데스크 — 창문도 뒷문도 없다
컨트롤 플레인   = 관제실 — 앉으면 모든 층의 잠금장치를 조작할 수 있다
노드 / 파드     = 각 사무실과 그 안의 직원들
```

24장 2.1의 "네임스페이스는 폴더다"와 짝이 되는 문장이 여기서도 나온다 — **네임스페이스는 RBAC의 경계이긴 하지만, 그 경계는 규칙을 적어야 생긴다.** 아무 Role도 만들지 않으면 경계도 없다.

### 2.2 인증과 인가 — 누구인가와 무엇을 할 수 있는가

보안의 핵심에 두 단어가 있고, 이 장은 둘을 명확히 나눠 쓴다.

| | Authentication (인증) | Authorization (인가) |
|---|---|---|
| 질문 | **너 누구야?** | **그거 해도 돼?** |
| 다루는 것 | 주체(subject)의 신원 | 리소스에 대해 허용되는 동작 |
| 누구의 일 | 관리자 — 회사 계정 시스템 연동 | **개발자** — 배포할 때마다 YAML |
| 실패하면 | 401 Unauthorized | 403 Forbidden |
| 이 책의 분량 | 훑고 지나감 | **장의 대부분** |

책이 인증을 짧게 다루는 이유는 명확하다. 인증 설정은 API 서버를 띄울 때 주는 실행 옵션(`--oidc-issuer-url` 같은)이라 **개발자가 나중에 바꿀 수 있는 게 아니다.** 반면 인가는 Role과 RoleBinding이라는 평범한 YAML이라, Git에 커밋하고 앱과 함께 배포한다. 24장에서 NetworkPolicy가 "앱 옆에 두는 방화벽"이었던 것과 정확히 같은 자리다.

401과 403의 구분은 실전에서 바로 쓰인다 — **401이면 토큰·인증서 문제, 403이면 RBAC 문제**다. 어느 관문에서 걸렸는지가 에러 코드에 이미 적혀 있다.

### 2.3 오퍼레이터의 딜레마 — 구조상 큰 권한이 필요하다

권한을 잘못 주면 양쪽으로 터진다.

```
권한이 너무 많으면 → 권한 상승(privilege escalation)
                     앱 하나 뚫렸는데 옆 팀 Secret 읽고 Deployment 수정 → 클러스터 전체

권한이 너무 적으면 → 배포 실패(deployment failure)
                     apply 는 성공했는데 실행 중 "Forbidden" 으로 죽는다
```

그리고 여기서 개발자가 흔히 하는 실수가 나온다 — **아래 문제를 빨리 없애려다 위 문제를 만든다.** Forbidden이 자꾸 뜨니 귀찮아서 권한을 넓게 열어버리는 것이다. 두 문제는 사실 이어져 있다.

이 딜레마가 가장 날카로워지는 곳이 **오퍼레이터**(28장)다. CRD로 쿠버네티스 API를 확장하는 컨트롤러·오퍼레이터는 하는 일이 이렇다.

```
1. 클러스터 전역을 계속 watch — "어디든 내 CRD 가 생기면 알려줘"
2. 변화를 감지하면 Pod, Service, Secret 을 직접 만들고 지운다
3. 이걸 한 네임스페이스가 아니라 여러 곳에서 한다
```

즉 오퍼레이터는 **태생적으로 넓은 권한을 요구한다.** 설정 실수가 아니라 패턴 자체의 성질이다. 게다가 Prometheus Operator, cert-manager처럼 **남이 만든 것을 가져다 쓰는** 경우가 대부분이라, 코드를 다 읽어보지 않은 프로그램에 클러스터 조작 권한을 주는 셈이 된다.

책의 답은 "권한을 주지 마라"가 아니다 — 그러면 일을 못 한다. **잘게 쪼개서 최소한만 주고, 뚫렸을 때 피해 범위를 좁혀두라**는 것이다. 원문의 표현은 *"limit the impact of any potential security breaches"* — 침해를 막는 게 아니라 **영향을 제한**한다. 24장의 blast radius 축소와 같은 사고방식이다.

즉 이 장의 목표는: **모든 요청이 지나는 단 하나의 문에서, 개발자가 앱과 함께 배포하는 권한 규칙으로, 뚫렸을 때 닿을 수 있는 범위를 미리 좁히는 것.**

---

## 3. 세 관문 — 모든 요청이 지나는 길

### 3.1 API 서버는 문이 하나다

쿠버네티스 API 서버로 들어오는 **모든** 요청은 세 단계를 순서대로 지난다.

```
kubectl / 오퍼레이터
        │
        ▼
┌──────────────── API 서버 ────────────────┐
│                                          │
│  Authentication → Authorization →        │
│                   Admission Control      │
│                                          │
└──────────────────────────────────────────┘
        │
        ▼
   etcd 에 기록
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 320" style="width:100%;min-width:620px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="API 서버의 세 관문: 모든 요청이 인증, 인가, 어드미션 컨트롤을 순서대로 지난 뒤에야 etcd에 기록된다">
  <defs>
    <marker id="ac-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="20" y="40" width="150" height="56" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="95" y="64" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">kubectl</text>
  <text x="95" y="82" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">오퍼레이터 · 스케줄러</text>

  <rect x="230" y="20" width="420" height="180" rx="6" fill="none" stroke="var(--content,#444)" stroke-width="2"/>
  <text x="440" y="44" text-anchor="middle" font-size="14" font-weight="600" fill="var(--content,#333)">API 서버</text>

  <rect x="252" y="66" width="118" height="60" rx="4" fill="#5b9bd5"/>
  <text x="311" y="92" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Authentication</text>
  <text x="311" y="110" text-anchor="middle" font-size="11.5" fill="#eaf3fb">너 누구야?</text>

  <rect x="392" y="66" width="118" height="60" rx="4" fill="#5b9bd5"/>
  <text x="451" y="92" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Authorization</text>
  <text x="451" y="110" text-anchor="middle" font-size="11.5" fill="#eaf3fb">그거 해도 돼?</text>

  <rect x="532" y="66" width="96" height="60" rx="4" fill="#4caf82"/>
  <text x="580" y="92" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Admission</text>
  <text x="580" y="110" text-anchor="middle" font-size="11.5" fill="#e9f7f1">뭐라고 썼는데?</text>

  <text x="311" y="152" text-anchor="middle" font-size="11.5" fill="#c0392b">✗ 401</text>
  <text x="451" y="152" text-anchor="middle" font-size="11.5" fill="#c0392b">✗ 403</text>
  <text x="580" y="152" text-anchor="middle" font-size="11.5" fill="#c0392b">✗ 403 + webhook</text>
  <text x="440" y="180" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">앞에서 막히면 뒤는 실행조차 되지 않는다</text>

  <rect x="700" y="48" width="52" height="52" rx="4" fill="#8e44ad"/>
  <text x="726" y="80" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">etcd</text>

  <g stroke="var(--content,#444)" stroke-width="1.8" fill="none" marker-end="url(#ac-ar)">
    <path d="M170,68 H226"/>
    <path d="M370,96 H388"/>
    <path d="M510,96 H528"/>
    <path d="M628,96 H696"/>
  </g>
  <g stroke="#c0392b" stroke-width="1.4" fill="none" stroke-dasharray="5 4" marker-end="url(#ac-ar)">
    <path d="M311,126 V140"/>
    <path d="M451,126 V140"/>
    <path d="M580,126 V140"/>
  </g>

  <text x="663" y="88" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">기록</text>
  <text x="440" y="236" text-anchor="middle" font-size="12.5" fill="var(--content,#333)">우회로가 없다 — kubectl 이든 파드 안 오퍼레이터든 내부 컴포넌트든 같은 문을 지난다</text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  세 관문 — 인증 · 인가 · 어드미션을 순서대로 통과해야 기록된다
</div>
</div>
{{< /rawhtml >}}

그림에서 정작 중요한 건 세 상자가 아니라 **바깥 테두리**다. 세 관문이 전부 API 서버 안에 있고, 우회로가 없다. `kubectl` 명령이든, 파드 안 오퍼레이터의 API 호출이든, 스케줄러가 보내는 내부 요청이든 예외가 없다.

**순서대로 통과**하는 것도 중요하다. 앞에서 막히면 뒤는 실행조차 되지 않는다.

```
1관문 실패 → 401 Unauthorized  "너 누군지 모르겠다"
2관문 실패 → 403 Forbidden     "누군지는 알겠는데 그건 안 된다"
3관문 실패 → 403 + admission webhook 메시지
```

세 번째 줄이 실전에서 헷갈리는 지점이다. 403이 떴다고 무조건 RBAC를 뒤지면 안 된다 — 에러 메시지에 `admission webhook "..." denied the request`가 있으면 권한은 있는데 **내용이 규정에 안 맞아서** 막힌 것이다.

### 3.2 인증 — 다섯 개의 입구, 하나의 출구

가장 먼저 새겨야 할 사실은 이것이다.

```
쿠버네티스에는 사용자 계정 시스템이 없다.
```

`kubectl create user`도, `kubectl get users`도 없다. 대신 **콘센트**처럼 만들어져 있다 — 회사가 이미 쓰는 인증 시스템을 규격에 맞게 꽂는다. 이유는 명확하다. 자체 계정 시스템을 만들면 회사가 직원 계정을 두 벌 관리해야 하고, 퇴사자를 한쪽에서만 지우는 순간 그게 곧 구멍이 된다.

꽂을 수 있는 것이 다섯 가지다.

| 방식 | 어떻게 | 비유 | 특징 |
|---|---|---|---|
| **OIDC 베어러 토큰** | 외부 제공자가 발급한 JWT를 `Authorization` 헤더에 | "구글로 로그인" | 사람 사용자의 표준. 퇴사 시 자동 차단 |
| **X.509 인증서** | TLS 인증서 제시. `CN`→username, `O`→group | 여권 | 내부 컴포넌트용. **폐기가 사실상 안 된다** |
| **인증 프록시** | 앞에 세운 프록시가 확인 후 헤더로 전달 | 경비 초소 | 우회당하면 치명적 |
| **정적 토큰 파일** | CSV 파일에서 토큰 대조 | 출석부 | 만료 없음, 수정 시 재시작. **실무 부적합** |
| **웹훅** | 외부 서버에 물어봄 | 본사에 전화 | 표준으로 안 되는 체계용. 매 요청 네트워크 호출 |

여기서 **이 절의 가장 큰 함정** — 여러 개를 동시에 켤 수 있고, **하나만 성공하면 통과**한다.

```
인증 방식을 하나 더 켜는 것 = 보안 강화 ❌
                            = 입구를 하나 더 여는 것 ✅
```

OIDC를 아무리 엄격하게 설정해도, 예전에 테스트하려고 켜둔 정적 토큰 파일이 남아 있으면 공격자는 그쪽으로 들어온다. **보안은 가장 약한 고리로 결정된다** — 안 쓰는 인증 플러그인은 반드시 꺼야 한다.

게다가 **평가 순서가 고정돼 있지 않다.** kubeconfig에 인증서와 토큰이 둘 다 있으면 어느 쪽으로 인증될지 모르는데, 방식마다 username이 다를 수 있다(`hong` vs `hong@company.com`). RBAC는 그 문자열로 판단하니 **권한이 달라진다.** 코드도 설정도 안 바꿨는데 어제 되던 게 오늘 403이 나는, 원인 찾기 지독한 버그다. 해법은 단순하다 — **클라이언트 하나에 자격 증명 하나만.**

### 3.3 사용자 표현 — 인증이 남기는 것

방식은 다섯 개인데 **결과물은 하나의 형태로 통일된다.** 추출 방법은 전부 다르지만(JWT 파싱, 인증서 필드 읽기, 헤더 읽기, CSV 조회, 외부 호출) 나오는 것은 같다.

```
alice, 4bc01e30-406b-4514, [system:authenticated, developers], {scopes:openid}
 └username      └UID              └groups                          └extra
```

| 필드 | RBAC가 쓰나 | 용도 |
|---|---|---|
| username | **✅** | 권한 판단, 감사 로그 |
| UID | ❌ | 이름 재사용 구분 — 퇴사한 alice와 새로 온 alice |
| groups | **✅** | 권한 판단 |
| extra | ❌ | 인가 웹훅용 부가 정보 |

**RBAC가 실제로 보는 건 두 개뿐**이다. 그리고 인증이 끝나는 순간 토큰은 사라진다 — 뒷단계는 어떤 방식으로 인증됐는지 모르고, 알 필요도 없다.

이 설계 덕분에 인증 방식을 추가해도 RBAC를 손댈 필요가 없고, 반대로 인가를 웹훅으로 바꿔도 인증은 그대로다. 24장 5.2에서 본 **컨트롤 플레인과 데이터 플레인의 분리**처럼, 정해진 규격으로만 소통하고 서로의 내부는 모르는 구조다.

groups에 `system:authenticated`가 섞여 있는 게 눈에 띈다. 이건 어느 계정 시스템에도 없는, **쿠버네티스가 자동으로 붙이는 그룹**이다.

| 그룹 | 언제 붙나 |
|---|---|
| `system:unauthenticated` | 자격 증명 없이 온 요청 — 여기 권한 주면 익명 접근이 열린다 |
| `system:authenticated` | 어떤 방식으로든 인증 성공한 모든 요청 |
| `system:masters` | **RBAC를 아예 건너뛴다.** Role 검사 없이 무조건 허용 |
| `system:serviceaccounts` | 클러스터의 모든 SA |
| `system:serviceaccounts:<ns>` | 그 네임스페이스의 모든 SA |

`system:masters`는 따로 기억해 둘 값어치가 있다. **RBAC로 제한할 수 없다** — 규칙 밖에 있기 때문이다. 클러스터 초기 관리자 인증서에 `O=system:masters`가 박혀 있는데, 인증서는 폐기가 안 되니 한 번 발급하면 만료까지 최고 권한자다. 두 약점이 곱해지는 조합이라 취급에 주의가 필요하다.

`system:` 접두사가 예약어인 이유도 여기서 나온다. 쿠버네티스는 인증 시스템이 보내주는 이름을 **검증하지 않고 믿는다.** 회사 계정 시스템에서 누군가에게 `system:masters` 그룹을 주면 그대로 클러스터 관리자가 된다. 이름 충돌 문제가 아니라 **권한 상승 경로**다.

### 3.4 어드미션 컨트롤 — 내용물을 보는 마지막 검문

세 번째 관문은 앞의 둘과 **보는 것이 다르다.**

```
인증  "이 요청 보낸 사람이 누구지?"          → YAML 안 봄
인가  "그 사람이 pods 를 create 할 자격이 있나?" → YAML 안 봄
어드미션  "그래서 그 YAML 에 뭐라고 적었는데?"    → YAML 을 연다
```

그래서 "권한은 있는데 내용이 문제인" 요청을 여기서 잡는다 — 파드를 만들 권한은 분명히 있는 개발자가 검증 안 된 외부 이미지를 쓰려 한다면, 인가는 통과시키고 어드미션이 막는다.

두 종류가 있고 순서가 있다.

```
Mutating(변형)   요청 내용을 고친다 — 안 쓴 것을 채워 넣음
                  · PVC 에 기본 StorageClass 자동 지정
                  · 서비스 메시 사이드카 자동 주입 (24장 4.1)
                  · ServiceAccount 토큰 볼륨 자동 추가 (4.3)
        ▼
Validating(검증)  보기만 하고 통과/거부만 정한다
                  · 사내 레지스트리 이미지가 아니면 거부
                  · resource limit 없으면 거부
```

먼저 다 고쳐놓고 최종 결과물을 검사해야 말이 되니 이 순서다.

내장 컨트롤러 외에 **웹훅으로 직접 규칙을 붙일 수 있다.** `ValidatingWebhookConfiguration`, `MutatingWebhookConfiguration`이라는 전용 리소스로 등록하는데, 여기서 ABAC와의 대비가 다시 나온다 — 파일 수정 후 재시작이 필요했던 ABAC와 달리 이건 **리소스라 `kubectl apply`로 즉시 반영**된다. 문서 제목이 *Dynamic* Admission Control인 이유다.

조직 정책이 실제로 강제되는 지점이 여기다. "모든 컨테이너는 limit을 명시해야 한다"는 규칙이 문서에만 있으면 아무도 안 지키지만, 어드미션 컨트롤러에 넣으면 정문에서 자동 집행된다. 요즘은 코드를 직접 짜기보다 OPA Gatekeeper나 Kyverno로 정책만 선언한다.

**함정 하나** — 웹훅 서버가 죽으면? `failurePolicy`가 그걸 정한다.

```
Fail    보안은 확실하지만, 웹훅이 죽는 순간 아무것도 배포할 수 없다
Ignore  클러스터는 돌지만, 그동안 정책 검사가 통째로 건너뛰어진다
```

둘 다 나름의 사고를 부른다. 24장 3.2에서 "CNI가 지원 안 하면 조용히 아무것도 안 막힌다"고 했던 것과 같은 종류의 위험 — **막고 있다고 믿는데 실제로는 안 막히는 상태**다.

---

## 4. Subject — 누구인가

주체(subject)는 **요청에 결부된 신원**이다. 사람 그 자체가 아니라 요청에 붙어 있는 정보라는 점이 중요하다 — 같은 사람이라도 노트북에서 `kubectl`을 치면 사람 주체지만, CI 파이프라인에서 스크립트를 돌리면 서비스 어카운트 주체다. **요청 단위로 판단한다.**

종류는 셋이고, 성격이 극단적으로 갈린다.

| | User | Group | ServiceAccount |
|---|---|---|---|
| 쿠버네티스 리소스 | ❌ | ❌ | **✅** |
| 실체 | 문자열 | 문자열 목록 | etcd에 저장된 객체 |
| `kubectl get` | 불가 | 불가 | `kubectl get sa` |
| 오타 검증 | 안 됨 | 안 됨 | 됨 |
| 관리 주체 | 외부 계정 시스템 | 외부 계정 시스템 | **개발자** |

### 4.1 User — 리소스가 아니라 문자열이다

쿠버네티스 문서가 직접 못 박는다 — 일반 사용자 계정을 나타내는 객체가 없다.

```
kubectl get users          ← 없는 명령
kubectl create user hong   ← 없는 명령
kubectl delete user hong   ← 없는 명령
```

**쿠버네티스는 자기 클러스터에 누가 접근할 수 있는지 목록조차 갖고 있지 않다.** 물어봐도 대답을 못 한다.

사용자의 실체는 인증 결과로 나온 문자열이 전부다. OIDC 토큰의 `email`이거나 인증서의 `CN`이거나. 그 문자열의 주인이 실존하는지, 퇴사했는지, 심지어 오타인지도 모른다.

```yaml
subjects:
- kind: User
  name: 존재하지않는사람      # ← 이래도 apply 성공한다
```

검증할 방법이 없기 때문이다. 오타를 내면 **조용히 권한이 안 붙고**, 원인 찾기가 어렵다.

그러면 `kind: User`에 붙는 `apiGroup: rbac.authorization.k8s.io`는 뭔가? 실제 리소스를 가리키는 게 아니라, **인증 결과의 어느 칸을 볼지 정하는 표시**다. `kind: User`면 username 칸, `kind: Group`이면 groups 칸. 쿠버네티스에서 대상을 가리키는 표준 형식(`apiGroup + kind + name`)에 끼워 맞춘 것뿐이다.

### 4.2 ServiceAccount — 파드의 신분증

여기서 정확히 나눠야 할 셋이 있다.

```
오퍼레이터        ← 실제로 일하는 코드
    │ 담겨서 실행됨
파드              ← 코드가 도는 그릇
    │ 지정됨
ServiceAccount    ← 그 파드의 신분증      ◀── 주체는 여기
```

**오퍼레이터는 주체가 아니다.** 오퍼레이터를 담은 파드에 지정된 SA가 주체다. 신분증과 사람을 분리하는 것과 같은데, 이래야 파드가 죽고 새로 떠도 같은 신분을 쓰고, 파드가 10개로 늘어도 권한은 한 번만 주면 된다.

리소스 자체는 놀랍도록 비어 있다.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: random-sa
  namespace: default
automountServiceAccountToken: false      # ★ 이 예제의 진짜 알맹이
```

`spec`조차 없다. **권한이 하나도 안 적혀 있다** — 권한은 RoleBinding이 따로 맡기 때문이다. 이 리소스는 "이런 신분이 존재한다"는 등록 그 이상도 이하도 아니다.

역할 분담을 못 박아두면 뒤가 편하다.

```
ServiceAccount  →  신분 (who)
Role            →  권한 (what)
RoleBinding     →  둘의 연결
```

**`automountServiceAccountToken`이 이 절의 핵심 함정이다.** 기본값이 `true`라, 아무것도 안 하면 켜져 있다.

모든 네임스페이스에는 `default`라는 SA가 자동으로 존재하고(지워도 컨트롤러가 다시 만든다), SA를 지정하지 않은 파드에 자동으로 붙는다. 그래서 이런 파드도,

```yaml
kind: Pod
spec:
  containers:
  - name: nginx
    image: nginx        # 쿠버네티스 API 를 쓸 일이 전혀 없다
```

실제로 뜬 걸 보면 `serviceAccountName: default`가 붙어 있고 **토큰까지 마운트돼 있다.**

```bash
kubectl exec nginx -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
eyJhbGciOiJSUzI1NiIs...
```

개발자가 의도한 게 아니라 기본값이 그런 것이라, 모르면 그냥 넘어간다. 24장 3.5의 "기본값이 위험한 쪽"과 같은 구조이고, 답도 같다 — **기본을 뒤집는다.**

```
이 파드가 쿠버네티스 API 를 호출하나?
  ├─ 아니오 (nginx, 프론트엔드, 배치 작업 등 대부분) → automount: false
  └─ 예   (오퍼레이터, 컨트롤러)                      → 전용 SA 를 만들어 지정
```

권한을 좁히는 것보다 **신분증 자체를 안 주는 것**이 더 강한 조치다. 없는 것은 훔칠 수도 없다.

SA에는 신원 외에 두 필드가 더 있다.

| 필드 | 용도 | 방향 |
|---|---|---|
| `imagePullSecrets` | 비공개 레지스트리 로그인 정보 | kubelet이 이미지 받아올 때 |
| `secrets` + `enforce-mountable-secrets` 어노테이션 | 마운트 가능한 Secret 화이트리스트 | 파드가 볼륨 붙일 때 |

`imagePullSecrets`는 편의 기능이다. 파드마다 쓰는 대신 SA에 한 번 붙이면 자동 주입된다(그 주입도 어드미션 컨트롤러가 한다). `default` SA에 붙여두는 게 흔한 패턴이다.

두 번째는 보안 기능인데, 막으려는 구멍이 흥미롭다 — **파드는 기본적으로 자기 네임스페이스의 아무 Secret이나 마운트할 수 있고, 이건 RBAC로 막히지 않는다.** kubelet이 대신 읽어서 파일로 넣어주는 구조라 파드의 SA에 Secret 읽기 권한이 없어도 마운트는 된다. RBAC를 우회하는 경로가 하나 있다는 뜻이다. 다만 어노테이션 스위치와 목록을 **둘 다** 켜야 작동하고(하나만 있으면 무효), 요즘은 Kyverno 같은 정책 도구로 처리하는 편이라 실무에서 자주 보이진 않는다.

### 4.3 토큰은 어떻게 들어오나 — Secret 에서 projected 로

파드에 SA를 지정하면 그다음은 전부 자동이다.

```
ServiceAccount 생성
   ↓  쿠버네티스가 JWT 발급·서명·갱신·무효화까지 전담
파드가 그 SA 를 지정 (또는 default)
   ↓  어드미션 컨트롤러가 볼륨 설정을 자동으로 끼워 넣음
파드 안에 파일로 등장
   /var/run/secrets/kubernetes.io/serviceaccount/token
```

개발자가 쓴 적 없는 볼륨과 볼륨 마운트가 파드 스펙에 들어가 있는 이유가 이것이다. 3.4의 Mutating 어드미션이 하는 일이 여기서 눈에 보인다.

**1.24를 기점으로 방식이 바뀌었고**, 이게 이 절에서 알아둘 변화다.

| | ~1.23 (Secret) | 1.24~ (projected) |
|---|---|---|
| 저장 위치 | etcd에 Secret으로 | **저장 안 함** — 발급해서 바로 주입 |
| 조회 | `kubectl get secret`으로 읽힘 | 조회 불가 |
| 만료 | **없음 — 영구 유효** | 1시간, 만료 전 자동 교체 |
| 유효 범위 | 무제한 | **파드 생명주기 동안만** |

핵심 개선은 **중간 표현이 사라졌다**는 것이다. 예전엔 토큰이 Secret이라는 실물로 클러스터에 저장돼 있어서, 파드에 들어가지 않고도 `secrets: list` 권한만 있으면 네임스페이스의 모든 토큰을 조용히 긁어갈 수 있었다.

```
예전:  발급 → [Secret] → 파드
                 ↑ 여기가 취약점

지금:  발급 → 파드
```

**다만 오해하면 안 되는 것** — 이건 토큰 노출을 막는 게 아니라 **경로를 줄인 것**이다. 여전히 남아 있는 경로가 있다.

| 경로 | Secret 방식 | projected |
|---|---|---|
| 파드 침입 | 가능 | 가능 |
| `kubectl exec` | 가능 | **가능** ← `pods/exec` 권한은 사실상 토큰 읽기 권한이다 |
| 노드 침입 | 가능 | **가능** |
| Secret 읽기 | 가능 | **불가** ← 사라진 것 |
| etcd / 백업 | 가능 | **불가** ← 사라진 것 |

사라진 둘이 **가장 조용하고 넓은 경로**였다는 점이 개선의 의미다. 여기에 만료 1시간과 파드 종속이 겹치니, 어느 경로로 훔쳐도 시한부가 된다.

한 가지 실전 함정 — 자동 교체되므로 **프로그램이 토큰 파일을 한 번만 읽고 캐시하면 안 된다.** 잘 돌던 앱이 몇 시간 뒤 401을 뱉는 증상이 나온다. 공식 클라이언트 라이브러리는 알아서 다시 읽는다.

만료 없는 토큰이 정말 필요하면(클러스터 밖 CI 도구 등) Secret을 수동으로 만들 수는 있지만, 옛 방식의 단점을 그대로 떠안는다. 요즘 권장은 `kubectl create token my-sa --duration=1h` — 수명을 지정해 받고 저장하지 않는다.

### 4.4 Group — 명단은 클러스터 밖에 있다

Role이 권한 쪽을 묶는다면, 그룹은 **사람 쪽을 묶는다.** 양쪽에서 묶어야 관리가 완성된다.

```
그룹 없이:  Role 하나 → alice 에 연결
                     → bob 에 연결
                     → ... 50 번 반복, 입퇴사 때마다 수정

그룹으로:  Role 하나 → "developers" 그룹에 연결   ← 한 번이면 끝
```

여기서 24장 3.4의 "역할 출입증" 라벨링과 발상이 정확히 같다 — 이름을 직접 부르지 않고 역할로 부른다.

그런데 **쿠버네티스에 그룹 멤버십 구조가 없다.**

```yaml
- kind: Group
  name: developers
  # members: [...]   ← 이런 필드는 없다
```

`developers`에 누가 속하는지 쿠버네티스는 모른다. 그 판단은 **인증 시스템이 이미 끝냈고**, 결론만 토큰에 실려 온다.

```json
{ "email": "alice@company.com", "groups": ["developers", "oncall"] }
```

그래서 RBAC가 하는 일은 **"이 사용자가 그 그룹에 속하나?"를 검사하는 게 아니다.** 요청에 딸려온 그룹 문자열 목록에 그 이름이 들어 있는지 대조할 뿐이다.

```
콘서트장 입구 비유
  직원은 VIP 명단을 갖고 있지 않다. 팔찌에 "VIP" 라고 적혀 있는지만 본다
  VIP 가 몇 명인지, 누구인지 모른다. 명단은 티켓 판매처에 있다
```

여기서 두 가지가 따라 나온다.

```
① 소속을 바꿔도 즉시 반영되지 않는다
   회사 계정에서 빼도 이미 발급된 토큰에는 그룹이 박혀 있다 → 만료까지 유효
② 토큰을 위조할 수 있으면 아무 그룹이나 될 수 있다
   서명 검증이 신뢰의 유일한 뿌리다
```

**서비스 어카운트 그룹은 예외적으로 규칙이 있다.** 명단이 있어서가 아니라 **이름에서 계산되기 때문**이다.

```
system:serviceaccount:dev:my-operator
                      └ns┘
        ↓ 잘라내면
system:serviceaccounts:dev
system:serviceaccounts
```

지정할 필요 없이 자동으로 붙는다. "dev의 모든 파드에게"를 한 줄로 쓸 수 있지만, 범위가 넓어 새 파드가 생기면 자동으로 권한을 갖게 되니 조심해야 한다.

| | 사람 그룹 | SA 그룹 |
|---|---|---|
| 어디서 오나 | 회사 계정 시스템 | 이름에서 자동 계산 |
| 자유롭게 정의 | 가능 | 불가 (규칙 고정) |
| 멤버 조회 | 불가 | `kubectl get sa -n dev` |

**그럼 username은 왜 필요한가?** 권한을 그룹으로 준다면 개인 이름은 무의미해 보인다. 두 용도가 남는다 — 개인에게 직접 주는 경우, 그리고 **감사 로그**다. 프로덕션 파드가 삭제됐는데 로그에 `developers`만 있고 이름이 없다면 팀원 20명 중 누가 했는지 영영 모른다.

```
groups   → 뭘 할 수 있나 (권한)
username → 누가 했나     (책임)
```

---

## 5. RBAC — 무엇을 할 수 있는가

인가 방식도 플러그형이라 갈아 끼울 수 있다(RBAC / ABAC / 웹훅 / Node). 하지만 결론은 이미 나 있다 — **거의 모든 클러스터가 RBAC를 쓴다.**

ABAC가 밀려난 이유가 이 책의 다른 장들과도 통한다.

| | ABAC | RBAC |
|---|---|---|
| 저장 | 노드의 파일 | etcd (API 리소스) |
| 변경 반영 | **서버 재시작** | 즉시 |
| 관리 | SSH + 수동 편집 | `kubectl`, GitOps |
| 조회 | 파일 열어보기 | `kubectl get roles` |

ABAC만 혼자 **선언적 운영 철학 밖에** 있었다. 24장에서 NetworkPolicy가 "앱 옆의 YAML"이었던 것처럼, RBAC도 앱과 함께 배포되는 리소스다. 그래서 이게 개발자의 일이 된다.

### 5.1 Role — 세 축으로 권한을 쪼갠다

Role의 알맹이는 `rules` 하나뿐이고, 각 규칙은 세 축으로 되어 있다.

```yaml
# Example 26-6. 코어 리소스 읽기 전용
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer-ro
  namespace: default        # ❶ Role 은 항상 네임스페이스에 묶인다
rules:
- apiGroups:
  - ""                      # ❷ 빈 문자열 = 코어 API 그룹
  resources:                # ❸ 무엇을
  - pods
  - services
  verbs:                    # ❹ 어떻게
  - get
  - list
  - watch
```

```
apiGroups  →  어느 API 그룹의
resources  →  어떤 리소스를
verbs      →  어떻게
```

**`apiGroups: [""]`가 가장 헷갈리는 부분이다.** 쿠버네티스 리소스는 그룹으로 나뉘어 있는데, 초창기 리소스들은 그룹 개념이 생기기 전에 만들어져 이름이 없다. 그 "이름 없음"이 빈 문자열이다.

| 그룹 | 리소스 |
|---|---|
| `""` (코어) | pods, services, configmaps, secrets, serviceaccounts, nodes |
| `apps` | deployments, statefulsets, daemonsets |
| `batch` | jobs, cronjobs |
| `rbac.authorization.k8s.io` | roles, rolebindings |

그래서 파드와 Deployment 권한은 **규칙을 나눠 써야 한다.** 그룹을 잘못 적으면 에러도 안 나고 `apply`는 성공하는데 **조용히 아무 효력이 없다.** "권한 줬는데 왜 안 되지?"의 십중팔구가 이것이다. `kubectl api-resources`로 확인하는 습관이 필요하다.

verb는 HTTP 메서드에 대응되지만 **더 잘게 쪼개져 있다.**

| verb | HTTP | 주의점 |
|---|---|---|
| `get` | GET | 이름을 알아야만 조회 |
| `list` | GET | **뭐가 있는지 모르는 상태에서 전부 훑는다** |
| `watch` | GET | 연결을 열어두고 변화 알림 — 오퍼레이터 필수 |
| `create` | POST | |
| `update` / `patch` | PUT / PATCH | 따로 줘야 한다 |
| `delete` | DELETE | |
| `deletecollection` | DELETE | 한 번에 전부 삭제 — 매우 위험 |

HTTP로는 같은 GET인데 셋으로 나눈 이유는 **위험도가 다르기 때문**이다. `secrets: get`은 이름을 아는 하나지만 `secrets: list`는 네임스페이스의 모든 Secret을 통째로 긁는다.

실전 함정 — **`get`만 주면 `kubectl get pods`가 안 된다.** 목록 조회는 `list`다. 그리고 오퍼레이터에는 거의 항상 `get, list, watch` 세트가 들어간다.

**하위 리소스는 별도 항목이다.**

```yaml
resources: ["pods", "pods/log", "pods/exec"]
```

`pods`를 적어도 `pods/log`는 안 포함된다. "파드는 보이는데 로그가 안 보인다"가 여기서 나온다. 그리고 `pods/exec`는 이름만 봐서는 안 위험해 보이는데 **컨테이너 안으로 들어가는 권한**이라, 4.3에서 봤듯 그 네임스페이스의 모든 토큰을 읽을 수 있다.

**그리고 이 절의 핵심 철학** — 24장 3.3과 똑같다.

```
RBAC 에는 거부(deny) 규칙이 없다.
기본이 전부 거부고, 적은 것만 열린다.
```

위 예제가 `delete`를 금지한 게 아니라 **안 적은 것**이다. "전부 허용하되 삭제만 금지"는 불가능하다. 대신 규칙을 읽으면 할 수 있는 일의 전부가 그대로 보이고, 우선순위 계산이 필요 없다.

**규칙 여러 개는 OR다** — 하나만 걸려도 통과한다. 그래서 세밀하게 잘 짜놓고 마지막에 넓은 규칙 하나를 추가하면 앞의 것들이 전부 무의미해진다.

와일드카드는 그 위험의 완성형이다.

```yaml
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]        # 사실상 cluster-admin
```

`*`가 특히 위험한 건 **미래까지 포함**하기 때문이다. 나중에 CRD를 설치하면 권한을 준 시점에 존재하지도 않던 리소스에 접근하게 된다. 24장 3.6의 `namespaceSelector: {}`가 "전부"였던 것과 같은 종류의, 무심코 붙였다가 범위가 폭발하는 표기다.

한 가지 덧붙이면, `resources: ["*"]`는 **무제한이 아니다** — 지정한 `apiGroups` 안에서만 전부다. 진짜 무제한은 셋이 모두 `*`일 때다.

### 5.2 RoleBinding — 권한을 붙인다는 것의 의미

Role을 `apply`해도 **아무 일도 일어나지 않는다.** 아직 아무에게도 안 붙었기 때문이다.

```
주체 (alice)          권한 (Role: pod-reader)
        └──── RoleBinding ────┘
                  ▲
          이 선을 긋는 게 "권한을 붙인다"
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 360" style="width:100%;min-width:620px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RBAC 구조: 주체와 Role은 서로 모르고, RoleBinding이 둘을 이어 줄 때만 권한이 생긴다">
  <defs>
    <marker id="rb-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <!-- 주체 (클러스터 밖 개념) -->
  <rect x="20" y="120" width="150" height="96" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="95" y="144" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Subject</text>
  <text x="95" y="166" text-anchor="middle" font-size="11.5" fill="#5a3d18">User (문자열)</text>
  <text x="95" y="184" text-anchor="middle" font-size="11.5" fill="#5a3d18">Group (문자열)</text>
  <text x="95" y="202" text-anchor="middle" font-size="11.5" fill="#5a3d18">ServiceAccount (리소스)</text>

  <!-- 네임스페이스 -->
  <rect x="210" y="40" width="510" height="280" rx="6" fill="none"
        stroke="var(--secondary,#888)" stroke-width="1.5" stroke-dasharray="7 5"/>
  <text x="465" y="62" text-anchor="middle" font-size="13" font-weight="600" fill="var(--content,#333)">Namespace: default</text>

  <rect x="245" y="130" width="150" height="76" rx="4" fill="#5b9bd5"/>
  <text x="320" y="160" text-anchor="middle" font-size="13" font-weight="600" fill="#fff">RoleBinding</text>
  <text x="320" y="182" text-anchor="middle" font-size="11.5" fill="#eaf3fb">subjects + roleRef</text>

  <rect x="480" y="130" width="180" height="76" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="570" y="156" text-anchor="middle" font-size="13" font-weight="600" fill="#1b3f63">Role</text>
  <text x="570" y="177" text-anchor="middle" font-size="11" fill="#1b3f63">apiGroups · resources · verbs</text>
  <text x="570" y="195" text-anchor="middle" font-size="11" fill="#1b3f63">"" · pods · get, list</text>

  <!-- 리소스 -->
  <rect x="480" y="248" width="180" height="50" rx="4" fill="#4caf82"/>
  <text x="570" y="278" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">pods (default 안)</text>

  <g stroke="var(--content,#444)" stroke-width="1.8" fill="none" marker-end="url(#rb-ar)">
    <path d="M170,168 H241"/>
    <path d="M395,168 H476"/>
    <path d="M570,206 V244"/>
  </g>

  <g font-size="11.5" fill="var(--content,#333)" font-style="italic">
    <text x="205" y="158" text-anchor="middle">subjects</text>
    <text x="435" y="158" text-anchor="middle">roleRef</text>
    <text x="606" y="230" text-anchor="middle">허용 범위</text>
  </g>

  <text x="465" y="344" text-anchor="middle" font-size="12.5" fill="var(--content,#333)">
    Role 만 만들면 아무 일도 없다 — RoleBinding 이 선을 그어야 권한이 생긴다
  </text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  RBAC — 주체와 권한은 서로 모르고, 바인딩이 둘을 잇는다
</div>
</div>
{{< /rawhtml >}}

```yaml
# Example 26-7. RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-rolebinding
  namespace: default             # 생략하면 default. 명시하는 편이 안전
subjects:                        # ❶ 목록 — 여러 개 가능
- kind: User
  name: alice
  apiGroup: "rbac.authorization.k8s.io"
- kind: ServiceAccount           # ❷ 종류가 달라도 한 목록에 섞인다
  name: contractor
  apiGroup: ""
roleRef:                         # ❸ 하나만. 변경 불가
  kind: Role
  name: developer-ro
  apiGroup: rbac.authorization.k8s.io
```

주체와 Role은 **다대다**다. `subjects`는 배열이고 `roleRef`는 단수라, 한 주체에 여러 Role을 주려면 RoleBinding을 여러 개 만든다.

`roleRef`가 **변경 불가**인 게 의도적이다. "파드 읽기"용 바인딩이 어느 날 슬쩍 "전체 관리자"로 바뀌는 사고를 막는다. 수정하려면 지우고 다시 만들어야 한다.

**"붙인다"는 표현이 오해를 만들 수 있어 정확히 해두면** — 주체는 전혀 변하지 않는다.

```bash
kubectl create sa my-operator
kubectl apply -f rolebinding.yaml
kubectl get sa my-operator -o yaml    # 권한에 대한 언급이 하나도 없다
```

권한은 SA 안에 저장되는 게 아니라 RoleBinding이라는 **별도 리소스에 기록**돼 있고, API 서버는 요청마다 그것들을 훑어서 계산한다. 그래서 권한 회수는 SA를 지우는 게 아니라 **연결선만 끊으면** 된다.

| 표현 | 실제 |
|---|---|
| 권한을 붙인다 | RoleBinding 생성 |
| 권한을 뗀다 | RoleBinding 삭제 |
| 권한을 바꾼다 | Role의 `rules` 수정 |

그리고 24장 3.3에서 본 것과 같은 이유로, **권한은 모든 경로에서 합쳐진다.**

```
alice 의 최종 권한
 = 개인 바인딩 + developers 그룹 + system:authenticated + ClusterRoleBinding
 = 전부 합집합, 빼는 방법 없음
```

특정 사용자의 권한을 줄이려고 그의 RoleBinding을 지웠는데 **그룹으로 들어오는 권한이 남아** 여전히 가능한 경우가 흔하다.

### 5.3 네 가지 조합 — 범위는 바인딩이 정한다

Role은 네임스페이스에 묶인다. 그래서 짝이 되는 클러스터 범위 리소스가 따로 있고, 조합이 넷이다.

```
RoleBinding        + Role          →  그 네임스페이스에만
RoleBinding        + ClusterRole   →  그 네임스페이스에만 (정의만 재사용)
ClusterRoleBinding + ClusterRole   →  클러스터 전체
ClusterRoleBinding + Role          →  ❌ 불가능
```

**네 번째가 안 되는 이유**가 이 구조를 이해하는 열쇠다. ClusterRoleBinding은 "모든 네임스페이스에 적용"인데 Role은 한 네임스페이스분의 권한밖에 없다 — **바인딩이 요구하는 범위를 권한이 채울 수 없다.**

그리고 여기서 가장 헷갈리는 것.

```
ClusterRole 은 "클러스터 전역 권한"이 아니라 "클러스터 전역에서 참조 가능한 정의"다.
범위는 바인딩이 정한다.
```

같은 ClusterRole을 RoleBinding으로 붙이면 그 네임스페이스에만, ClusterRoleBinding으로 붙이면 전체에 적용된다.

ClusterRole의 용도는 둘이다.

```
① 네임스페이스가 없는 리소스를 다루려고 — 선택의 여지가 없다
     nodes, namespaces, CustomResourceDefinitions,
     persistentvolumes, storageclasses, clusterroles

② 여러 네임스페이스에서 재사용하는 템플릿 — 선택의 문제
     Role 은 네임스페이스를 못 넘어 열 곳에 쓰려면 열 번 복사해야 한다
```

①에 CRD가 있는 게 중요하다. **오퍼레이터를 설치하려면 CRD 권한이 필요하고, 그건 ClusterRole로만 줄 수 있다.** `customresourcedefinitions: create`는 사실상 API를 확장할 수 있는 권한이라 개발자에게는 보통 읽기만 준다.

기본 제공 ClusterRole 넷은 직접 짜지 않아도 된다.

| ClusterRole | 범위 | 빠진 것 |
|---|---|---|
| `view` | 읽기 | **Secret, Role, RoleBinding** |
| `edit` | 읽기+수정 | Role, RoleBinding |
| `admin` | 네임스페이스 내 전부 | — |
| `cluster-admin` | **전부** | — |

`view`에서 Secret이 빠진 이유는 4.3의 논리 그대로다 — 읽는 순간 DB 비밀번호와 클라우드 키를 손에 넣으니 "구경만" 하는 권한이 아니다. `edit`에서 Role/RoleBinding이 빠진 건 **권한을 수정할 수 있으면 스스로 권한을 늘릴 수 있어서**다.

**ClusterRoleBinding은 관리 작업에만 써야 한다.** 책이 명시적으로 못 박는 부분인데, 이유는 "앞으로 생길 네임스페이스까지 자동으로 포함"하기 때문이다. `*` 와일드카드가 미래 리소스를 포함했던 것과 같은 성질이다.

**오퍼레이터의 정답에 가까운 패턴**은 이것이다 — `subjects`에는 SA만 `namespace` 필드를 가질 수 있다는 점을 이용한다.

```yaml
kind: RoleBinding
metadata:
  namespace: prod            # 권한이 적용되는 곳
subjects:
- kind: ServiceAccount
  name: my-operator
  namespace: operators       # 오퍼레이터가 사는 곳 — 달라도 된다
roleRef:
  kind: ClusterRole
  name: view-pod
```

오퍼레이터를 한 곳에 두고 **관리할 네임스페이스마다 RoleBinding을 하나씩** 만든다. YAML은 늘지만 권한은 딱 그 네임스페이스들에만 열리고, 새 네임스페이스가 생겨도 자동으로 퍼지지 않는다. 그 명시성이 안전장치가 된다.

### 5.4 집계 — 파이프는 그대로 두고 물통을 채운다

내가 CRD를 만들면 사용자는 그걸 못 본다. 기본 `view`에 안 들어 있기 때문이다.

```bash
kubectl get postgresclusters
# Error: postgresclusters is forbidden
```

`view`를 직접 고치면 되지 않나 싶지만 **쿠버네티스 업그레이드 때 덮어쓰인다.** 그래서 집계(aggregation)라는 장치가 있다.

```yaml
# 기본 view 는 실제로 이렇게 생겼다
kind: ClusterRole
metadata:
  name: view
  labels:
    rbac.authorization.k8s.io/aggregate-to-edit: "true"    # ❶ 나를 edit 이 가져가라
aggregationRule:
  clusterRoleSelectors:
  - matchLabels:
      rbac.authorization.k8s.io/aggregate-to-view: "true"  # ❷ 이 라벨 붙은 걸 내가 모은다
rules: []                                                  # ❸ 쿠버네티스가 채운다
```

**`rules: []`는 "규칙이 없다"가 아니라 "내가 안 쓸 테니 네가 채워라"**다. 실제로 조회하면 수십 줄이 들어 있다. 여기에 수동으로 뭘 적어도 컨트롤러가 곧 덮어쓴다 — `default` SA를 지워도 다시 생기는 것과 같은, "쿠버네티스가 소유한 필드"다.

라벨과 셀렉터가 양쪽에 다 있어서 **계단이 자동으로 쌓인다.**

```
개별 ClusterRole 들 (aggregate-to-view 라벨)
        ↓ 모여서
      view      (aggregate-to-edit 라벨을 갖고 있음)
        ↓
      edit      (aggregate-to-admin 라벨을 갖고 있음)
        ↓
      admin
```

누가 "edit에는 view 권한도 포함"이라고 적어둔 게 아니다. 그래서 **맨 아래 하나만 추가해도 위로 전부 전파**된다.

라벨+셀렉터라는 방식 자체는 24장 3.4에서 이미 본 것이다. Service가 파드를 찾는 그 원리이고, **관계의 방향을 뒤집는** 효과가 핵심이다.

```
목록 방식:    수집하는 쪽이 대상을 다 알아야 한다 → view 를 계속 고쳐야 함
라벨 방식:    수집당하는 쪽이 손을 든다          → view 는 그대로
```

**그래서 오퍼레이터 개발자가 할 일은 이 한 장이다.**

```yaml
kind: ClusterRole
metadata:
  name: postgres-viewer
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
- apiGroups: ["mycompany.com"]
  resources: ["postgresclusters"]
  verbs: ["get", "list", "watch"]
```

**바인딩이 없다는 점**을 눈여겨볼 만하다. 필요 없기 때문이다.

```
바인딩 = 파이프 (누구 → view)     ← 관리자가 예전에 이미 놓았다
view   = 물통 (권한 내용)          ← 여기에 물을 더 붓는 것
```

파이프는 그대로 두고 물통을 채우니, 기존 `view` 사용자들이 **아무 설정 없이** 새 CRD를 볼 수 있게 된다. 오퍼레이터 개발자는 어느 회사가 어떤 그룹을 어떻게 묶어놨는지 알 수 없으니, 바인딩은 안 만들고 **권한 내용만 제공**하는 게 맞는 설계다.

### 5.5 디버깅 — 추측하지 말고 물어봐라

권한이 여러 경로에서 합쳐지고 거부 규칙도 없으니, 최종 결과를 머리로 계산하는 건 사실상 불가능하다. 그래서 **직접 물어보는** API가 있다.

```bash
kubectl auth can-i list pods \
  --namespace dev-1 --as system:serviceaccount:test:test-sa
# yes
```

`--as`로 남인 척할 수 있고, SA는 4.2의 정식 긴 이름을 쓴다.

내부적으로는 `SubjectAccessReview`라는 **리소스가 생성되고**, 인가 컨트롤러가 `status`를 채워 돌려준다. 평소 쓰는 판단 로직을 그대로 돌리되 실행만 안 하는 것이라 결과가 정확하다. 저장은 되지 않는다 — 리소스 형식을 빌린 함수 호출에 가깝다.

**다만 한계가 있다** — `can-i`는 결과만 알려주고 **이유는 알려주지 않는다.**

사실 이건 RBAC 구조상 어쩔 수 없다. 거부 규칙이 없으니 안 되는 이유는 언제나 하나다 — **허용하는 규칙을 못 찾았다.** 특정 규칙이 막은 게 아니라 아무것도 허용하지 않은 것이라, 지목할 범인이 없다.

그래서 질문을 바꿔야 한다.

```
❌ 왜 안 되지?
✅ 지금 뭐가 되지?  →  kubectl auth can-i --list -n dev
```

`--list`가 여러 경로에서 합쳐진 **최종 권한 전부**를 보여준다. 거기서 빠진 걸 찾는 방식이다.

`can-i`는 한 번에 하나씩만 물어보니, 전체 그림이 필요하면 도구를 쓴다.

| 상황 | 도구 |
|---|---|
| 이 권한 되나 확정 | `kubectl auth can-i` |
| 이 주체의 전체 권한 | `kubectl auth can-i --list`, **rakkess** (`kubectl access-matrix`) |
| 클러스터에 위험한 게 있나 | **KubiScan** — `cluster-admin`, `*`, `secrets: list`, `pods/exec` 스캔 |
| 내가 누구로 인식되나 | `kubectl auth whoami` |

마지막 것이 의외로 자주 쓰인다. 3.2의 "인증 순서가 고정되지 않았다" 문제로 엉뚱한 username으로 인식되고 있을 때, 이걸 안 보면 RBAC만 계속 뒤지게 된다.

---

## 6. Discussion

### 6.1 세 가지 조언 — 필요 없는 건 주지 마라

책이 장을 닫으며 남기는 조언은 셋이고, 전부 같은 말의 변주다.

```
① 와일드카드를 피하라
   verbs: ["*"] 는 deletecollection 과 pods/exec 까지 포함하고, 미래 리소스도 포함한다
   → "와일드카드 금지"를 정책으로 세우고, 타당한 이유가 있을 때만 예외로 푼다
     (그때그때 판단하면 결국 편한 쪽으로 흐른다)

② 파드에 cluster-admin 을 주지 마라. 절대로
   책에서 "Never." 를 문장 하나로 따로 쓴 유일한 대목
   권한 수정 가능 → 스스로 무한 확장 / 모든 Secret 열람 → 클러스터 밖까지
   사람 관리자와 달리 파드는 코드라 취약점이 있을 수 있다

③ 토큰을 자동 마운트하지 마라
   automountServiceAccountToken: false
   기준은 하나 — 이 파드가 쿠버네티스 API 를 호출하나?
```

세 조언의 공통점이 이 패턴의 요약이다.

```
와일드카드    → 필요 없는 권한을 주지 마라
cluster-admin → 필요 없는 최고 권한을 주지 마라
토큰 마운트   → 필요 없는 신분증을 주지 마라
```

효과 순으로 매기면 ② → ③ → ①이다. ②는 하나만 지켜도 최악을 피하고, ③은 대부분의 파드에 즉시 적용 가능하며, ①은 꾸준히 지켜야 하는 습관이다.

그리고 조합 선택은 **좁은 것에서 시작해 필요할 때만 넓히는** 순서다.

```
Role + RoleBinding                ← 여기서 출발
    ↓ 여러 네임스페이스가 필요하면
ClusterRole + RoleBinding (여러 개)
    ↓ 전역 리소스(nodes, CRD)가 정말 필요하면
ClusterRole + ClusterRoleBinding  ← 마지막 수단
```

### 6.2 24장과의 구분 — 조작 권한 vs 통신 권한

24장 5.1에서 이미 짚었지만, 26장을 읽고 나면 경계가 더 선명해진다. 같은 클러스터의 두 상황이다.

```
상황 1 — 개발자 민수가 노트북에서
  kubectl delete deployment payment -n chili-shop
  → 요청이 "API 서버"로 간다
  → 세 관문 통과 여부를 RBAC 가 판단                    = 26장

상황 2 — frontend 파드가 앱 코드로
  DELETE http://backend:8080/orders/123
  → 쿠버네티스는 이 요청의 존재조차 모른다. 파드→파드 HTTP 일 뿐
  → NetworkPolicy(IP·포트) + AuthorizationPolicy(경로·신원)가 판단 = 24장
```

| | RBAC (26장) | NetworkPolicy / AuthorizationPolicy (24장) |
|---|---|---|
| 요청 목적지 | API 서버 | 내 앱 파드 |
| 무엇을 통제 | 쿠버네티스 리소스 조작 | 파드 간 통신 |
| 비유 | **건물 관리 권한** — 방을 만들고 부수는 것 | **방끼리 왕래 규칙** |
| 신원의 근거 | 토큰의 username·groups | IP(NetworkPolicy) / 인증서(mTLS) |

**둘은 서로 만나지 않는다.** 민수에게 RBAC 전권을 줘도 그가 frontend 파드 안에서 `DELETE /orders`를 날리면 AuthorizationPolicy가 막고, AuthorizationPolicy가 아무리 빡빡해도 `kubectl delete pod`는 RBAC 영역이다.

흥미로운 건 **한 곳에서 만난다**는 점이다 — ServiceAccount다.

```
RBAC        SA 에 Role 을 붙여 "쿠버네티스에 뭘 할 수 있나"를 정한다
Istio mTLS  SA 이름이 그대로 신원이 되어 "누구와 통신할 수 있나"의 근거가 된다
            cluster.local/ns/chili-shop/sa/frontend
```

같은 신분증이 두 체계에서 각각 다른 문을 여는 셈이다. 24장 4.2에서 "ServiceAccount는 파드가 쓰는 계정"이라고 짧게 넘어갔던 것의 정체가 26장 전체였다.

### 6.3 모든 것이 리소스다 — 질문조차

이 장을 관통하는 설계 철학이 하나 있다. **쿠버네티스는 모든 것을 API 리소스로 표현하려 한다.**

```
권한          → Role, RoleBinding          (ABAC 의 파일과 대비)
신분          → ServiceAccount
어드미션 규칙 → ValidatingWebhookConfiguration  ("Dynamic" Admission Control)
토큰 요청     → TokenRequest
"이거 되나요?" → SubjectAccessReview        ← 질문조차 리소스다
```

리소스가 된다는 건 곧 `kubectl apply`로 다루고, Git에 커밋하고, 코드 리뷰를 받고, 감사 로그에 남는다는 뜻이다. ABAC가 밀려난 이유도, 어드미션 웹훅이 "dynamic"인 이유도, `can-i`가 특별한 명령이 아닌 이유도 전부 같은 문장에서 나온다.

다만 **예외가 둘 남아 있다** — User와 Group. 이 둘만 리소스가 아니고 문자열이다. 의도적인 선택이다. 신원 관리는 회사가 이미 잘하고 있고, 쿠버네티스가 또 하면 계정을 두 벌 관리하게 된다.

```
쿠버네티스가 만든 것(파드)  → 신분증도 자기가 발급한다  → ServiceAccount (리소스)
쿠버네티스가 안 만든 것(사람) → 신분증은 남에게 맡긴다   → User (문자열)
```

이 비대칭 하나가 26장의 거의 모든 구조를 설명한다 — 왜 인증 방식이 다섯 개나 되는지, 왜 사람은 조회가 안 되는지, 왜 그룹 명단이 클러스터 밖에 있는지, 왜 서비스 어카운트만 모든 클러스터에서 똑같이 동작하는지.

### 핵심 메시지

```
Access Control 의 몫: 하나뿐인 문에서, 뚫렸을 때 닿을 범위를 미리 좁히는 것
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

전제      → API 서버가 유일한 문. 모든 요청이 인증→인가→어드미션 셋을 순서대로 지난다
            401=인증, 403=인가, admission webhook 메시지=어드미션
인증      → 쿠버네티스에 계정 시스템이 없다. 회사 것을 꽂는다
            다섯 방식 중 하나만 통과하면 되니, 방식을 늘리는 건 문을 늘리는 것
            결과물은 언제나 username + groups (UID·extra 는 RBAC 가 안 본다)
주체      → User·Group 은 문자열, ServiceAccount 만 리소스
            SA 는 권한이 아니라 신분. 권한은 RoleBinding 이 따로 맡는다
토큰      → 1.24 부터 projected — 저장 안 하고, 1시간 만료, 파드 죽으면 무효
            그래도 exec·노드 침입 경로는 남는다. 근본 대책은 automount: false
RBAC      → 세 축(apiGroups·resources·verbs)으로 쪼갠다. 거부 규칙이 없다
            규칙은 OR, 권한은 모든 경로에서 합집합, 빼는 방법이 없다
범위      → ClusterRole 은 "정의"일 뿐, 범위는 바인딩이 정한다
            ClusterRoleBinding 은 미래 네임스페이스까지 포함 — 관리 작업에만
집계      → rules: [] 는 비운 게 아니라 맡긴 것. 라벨만 붙이면 view 가 흡수한다
디버깅    → 추측하지 말고 can-i. 단 이유는 안 알려주니 --list 로 "뭐가 되는지"를 본다
조언      → * 쓰지 말고, 파드에 cluster-admin 절대 주지 말고, 안 쓰면 토큰 끄기
```

> Access Control 은 **"침해를 막는 패턴이 아니라, 침해의 반경을 정하는 패턴"** 이다.
> 문은 하나뿐이니 그 문만 지키면 되고,
> 신분은 밖에서 오지만 권한은 안에서 정하며,
> 거부를 적을 수 없으니 필요한 것만 하나씩 적어야 한다.
> 그러면 파드 하나가 뚫려도, **그 파드가 할 수 있는 일은 원래 해야 했던 일뿐이다.**

---

## 7. References

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>사람 사용자가 쿠버네티스 리소스가 아니라는 사실은 공식 문서 <strong>"Authenticating"</strong>에 그대로 적혀 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "Kubernetes does not have objects which represent normal user accounts."
  </blockquote>
  <div>[해석] "쿠버네티스에는 일반 사용자 계정을 나타내는 객체가 없다." — 4.1의 근거이자 이 장 전체의 비대칭(사람은 밖, 파드는 안)을 만드는 한 문장이다. 같은 문서는 인증 플러그인을 여러 개 켰을 때 하나만 성공하면 통과한다는 점과 평가 순서가 보장되지 않는다는 점(3.2), 인증 결과가 username·UID·groups·extra 네 필드로 표현된다는 점(3.3)을 설명한다.</div>
  <div style="margin-top:10px;">RBAC 레퍼런스는 <code>rules</code>의 세 축(3.5.1), 규칙 간 OR 평가와 거부 규칙의 부재, Role/ClusterRole × RoleBinding/ClusterRoleBinding 네 조합 중 <code>ClusterRoleBinding + Role</code>이 불가능하다는 점(5.3), 그리고 <code>aggregationRule</code>을 설정하면 <code>rules</code>가 컨트롤러 소유가 된다는 점(5.4)을 정의한다. 기본 제공 ClusterRole <code>view</code>/<code>edit</code>/<code>admin</code>의 정확한 권한 범위도 여기 있다.</div>
  <div style="margin-top:10px;">서비스 어카운트 토큰이 Secret에서 projected 볼륨으로 전환된 배경(4.3)은 <strong>Bound Service Account Tokens</strong> 관련 문서와 1.24 릴리스 노트에 정리돼 있다. 만료·대상(audience)·파드 종속이 한꺼번에 들어온 변화다.</div>
  <div style="margin-top:10px;">책 예제에서 눈에 띈 것 — Problem 절의 "authentication has two fundamental parts and authorization"은 어순이 깨진 문장으로 보이며, 문맥상 "접근 제어는 인증과 인가 두 부분으로 이루어진다"는 뜻이다. Table 26-1과 26-6은 PDF 추출 과정에서 열이 섞여 원문 대조가 필요하다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/reference/access-authn-authz/authentication/">kubernetes.io — Authenticating</a></div>
  <div>→ <a href="https://kubernetes.io/docs/reference/access-authn-authz/rbac/">kubernetes.io — Using RBAC Authorization</a></div>
  <div>→ <a href="https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/">kubernetes.io — Admission Controllers</a></div>
  <div>→ <a href="https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/">kubernetes.io — Managing Service Accounts</a></div>
  <div>→ <a href="https://github.com/corneliusweig/rakkess">GitHub — rakkess (kubectl access-matrix)</a></div>
  <div>→ <a href="https://github.com/cyberark/KubiScan">GitHub — KubiScan</a></div>
</div>
{{< /rawhtml >}}