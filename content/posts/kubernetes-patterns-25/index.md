---
series: ["K8sPatterns"]
title: "K8sPatterns.25 Secure Configuration"
date: 2026-09-02T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "security", "secret", "gitops", "vault"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.25 Secure Configuration'
  relative: true
summary: "Secret은 암호화가 아니라 인코딩이다. Sealed Secrets·External Secrets·sops로 Git 노출을 막고, CSI·사이드카 주입으로 클러스터에 아무것도 남기지 않는 방법."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-secret은-암호화가-아니다--base64는-숨김이지-잠금이-아니다" style="color:var(--secondary,inherit);text-decoration:none;">2.1 Secret은 암호화가 아니다 — base64는 숨김이지 잠금이 아니다</a></div>
    <div><a href="#22-클러스터-밖에서는-평문과-같다--gitops가-드러낸-문제" style="color:var(--secondary,inherit);text-decoration:none;">2.2 클러스터 밖에서는 평문과 같다 — GitOps가 드러낸 문제</a></div>
    <div><a href="#23-클러스터-안도-안전하지-않다--관리자라는-신뢰-경계" style="color:var(--secondary,inherit);text-decoration:none;">2.3 클러스터 안도 안전하지 않다 — 관리자라는 신뢰 경계</a></div>
    <div><a href="#24-세-가지-노출--무엇을-막고-싶은가" style="color:var(--secondary,inherit);text-decoration:none;">2.4 세 가지 노출 — 무엇을 막고 싶은가</a></div>
  </div>
  <div><a href="#3-out-of-cluster-encryption--잠가서-내보내기" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Out-of-Cluster Encryption — 잠가서 내보내기</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-공통-구조--결국-secret으로-착지한다" style="color:var(--secondary,inherit);text-decoration:none;">3.1 공통 구조 — 결국 Secret으로 착지한다</a></div>
    <div><a href="#32-sealed-secrets--우편함-방식" style="color:var(--secondary,inherit);text-decoration:none;">3.2 Sealed Secrets — 우편함 방식</a></div>
    <div style="padding-left:18px;font-size:14px;"><a href="#321-하이브리드-암호화--왜-두-번-잠그나" style="color:var(--secondary,inherit);text-decoration:none;">3.2.1 하이브리드 암호화 — 왜 두 번 잠그나</a></div>
    <div style="padding-left:18px;font-size:14px;"><a href="#322-스코프--이-편지를-어디서-열-수-있게-할까" style="color:var(--secondary,inherit);text-decoration:none;">3.2.2 스코프 — 이 편지를 어디서 열 수 있게 할까</a></div>
    <div><a href="#33-external-secrets--git에는-주소만-적는다" style="color:var(--secondary,inherit);text-decoration:none;">3.3 External Secrets — Git에는 주소만 적는다</a></div>
    <div><a href="#34-sops--값만-잠그고-키는-남긴다" style="color:var(--secondary,inherit);text-decoration:none;">3.4 sops — 값만 잠그고 키는 남긴다</a></div>
    <div><a href="#35-sms-vs-kms--물건을-맡기나-열쇠를-맡기나" style="color:var(--secondary,inherit);text-decoration:none;">3.5 SMS vs KMS — 물건을 맡기나 열쇠를 맡기나</a></div>
  </div>
  <div><a href="#4-centralized-secret-management--아예-저장하지-않기" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Centralized Secret Management — 아예 저장하지 않기</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-secrets-store-csi-driver--금고를-폴더처럼-마운트한다" style="color:var(--secondary,inherit);text-decoration:none;">4.1 Secrets Store CSI Driver — 금고를 폴더처럼 마운트한다</a></div>
    <div style="padding-left:18px;font-size:14px;"><a href="#411-부트스트랩-문제와-irsa--들고-다닐-열쇠를-없앤다" style="color:var(--secondary,inherit);text-decoration:none;">4.1.1 부트스트랩 문제와 IRSA — 들고 다닐 열쇠를 없앤다</a></div>
    <div><a href="#42-pod-injection--컨테이너-레벨-해법" style="color:var(--secondary,inherit);text-decoration:none;">4.2 Pod Injection — 컨테이너 레벨 해법</a></div>
    <div style="padding-left:18px;font-size:14px;"><a href="#421-init-container와-sidecar" style="color:var(--secondary,inherit);text-decoration:none;">4.2.1 Init Container와 Sidecar</a></div>
    <div style="padding-left:18px;font-size:14px;"><a href="#422-vault-injector--mutating-webhook이-대신-붙여준다" style="color:var(--secondary,inherit);text-decoration:none;">4.2.2 Vault Injector — mutating webhook이 대신 붙여준다</a></div>
  </div>
  <div><a href="#5-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-무엇이-최선인가--상황에-따라-다르다" style="color:var(--secondary,inherit);text-decoration:none;">5.1 무엇이 최선인가 — 상황에 따라 다르다</a></div>
    <div><a href="#52-제품이-아니라-기법을-기억하라" style="color:var(--secondary,inherit);text-decoration:none;">5.2 제품이 아니라 기법을 기억하라</a></div>
    <div><a href="#53-완벽한-보안은-없다--어렵게-만들-뿐이다" style="color:var(--secondary,inherit);text-decoration:none;">5.3 완벽한 보안은 없다 — 어렵게 만들 뿐이다</a></div>
  </div>
  <div><a href="#6-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. References</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Secure Configuration 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"Secret 은 잠긴 게 아니다"를 인정하고, 그 위에 계층을 하나씩 덧댄다

  기본 상태: Secret = base64  ← 인코딩이지 암호화가 아니다. 한 줄이면 풀린다
                        │  Git 에 올리면 전 직원 공개, etcd 를 보면 관리자도 다 봄
                        ▼
  1겹: Out-of-cluster encryption — 잠가서 내보내기
  ├─ Sealed Secrets   Git 에 암호문. 클러스터 안 컨트롤러가 개인키로 푼다
  ├─ External Secrets Git 에 주소만. 오퍼레이터가 금고에서 가져와 동기화한다
  ├─ sops             Git 에 암호문. 배포하는 쪽(사람/CI)이 밖에서 푼다
  └─ 공통점: 결국 평범한 Secret 으로 착지한다 → 앱 코드 수정 불필요
                        ▼
  2겹: Centralized secret management — 아예 저장하지 않기
  ├─ CSI Driver       금고를 볼륨처럼 마운트. etcd 에 아무것도 안 남는다
  ├─ Init / Sidecar   파드 안 컨테이너가 가져와 공유 볼륨에 놓는다
  └─ Vault Injector   어노테이션 한 줄이면 사이드카를 자동 주입한다
                        ▼
  그래도 root 권한자는 결국 본다 — 목표는 "불가능"이 아니라 "어렵게" 🔒
```

24장이 뚫린 파드의 손이 옆으로 뻗지 못하게 막는 이야기였다면, 25장은 그 손이 쥐려는 물건 자체를 숨기는 이야기다. 애플리케이션은 혼자 살지 못한다 — DB에 붙고, 다른 마이크로서비스를 부르고, 클라우드 API를 호출한다. 그때마다 인증이 필요하고, 인증에는 자격 증명이 필요하다. 그 자격 증명은 앱이 손 닿는 거리에 있어야 하면서(가까이), 동시에 아무도 못 봐야 한다(안전하게).

이 두 요구가 서로 부딪히기 때문에 별도의 패턴이 필요하다. 그리고 이 장의 솔직함은 마지막 문장에 있다 — 완벽한 방법은 없다. 위협 수준과 신뢰 경계에 맞춰 계층을 몇 겹까지 쌓을지 고르는 문제일 뿐이다.

---

## 2. Problem

### 2.1 Secret은 암호화가 아니다 — base64는 숨김이지 잠금이 아니다

이 장을 읽기 전에 걷어내야 할 오해가 하나 있다. 이름이 Secret이니 뭔가 잠겨 있을 것 같지만, 실제로는 이렇다.

```yaml
kind: Secret
data:
  password: bXlwYXNzd29yZDEyMw==
```

```bash
$ echo bXlwYXNzd29yZDEyMw== | base64 -d
mypassword123
```

명령어 한 줄이면 풀린다. base64는 보안 기술이 아니라 바이너리를 텍스트로 옮기는 인코딩 방식이다. YAML에 아무 바이트나 넣을 수 없으니 안전하게 담기 위한 포장일 뿐, 자물쇠가 아니다.

24장에서 "네임스페이스는 폴더지 방화벽이 아니다"로 시작했던 것과 정확히 같은 구조의 오해다 — 이름이 주는 인상과 실제 기능이 다르다.

물론 쿠버네티스가 손을 놓고 있는 건 아니다. 클러스터 안에서는 나름의 울타리를 쳐준다.

| 보호 장치 | 무엇을 막나 |
|---|---|
| RBAC | 아무나 Secret을 읽지 못하게 |
| tmpfs 마운트 | 노드 디스크에 안 씀 (메모리에만) |
| 노드 한정 배포 | 그 Secret을 쓰는 노드에만 전달 |
| etcd 암호화 (옵션) | 저장 계층 자체를 암호화 |

문제는 이 울타리가 클러스터 안에서만 유효하다는 것이다.

### 2.2 클러스터 밖에서는 평문과 같다 — GitOps가 드러낸 문제

```bash
kubectl get secret db-secret -o yaml > secret.yaml
```

이 한 줄이면 위의 보호막이 전부 사라진다. 그냥 비밀번호가 적힌 텍스트 파일이 된다. 책의 표현대로 "naked and vulnerable" 상태다.

그리고 이 문제를 폭발시킨 것이 GitOps다. GitOps는 "Git에 있는 YAML이 곧 클러스터의 정답"이라는 방식으로, 모든 배포 설정을 Git에 넣고 Argo CD 같은 도구가 그걸 읽어 클러스터에 반영한다. 그런데 모든 걸 Git에 넣으라면서 Secret은?

Git에 평문 자격 증명이 올라가면 무슨 일이 생기는지 정리해 두자.

```
누가 보게 되나
  · 저장소 읽기 권한이 있는 회사 사람 전부
  · 저장소를 clone 한 모든 사람의 노트북
  · CI 서버, 백업 시스템
  · 퍼블릭 저장소면 전 세계 (봇이 몇 분 만에 찾는다)

지워도 소용없다
  git rm secret.yaml && git commit -m "비밀번호 삭제"
  → 커밋 히스토리에 영원히 남는다. git log -p 로 그대로 나온다
  → 히스토리를 재작성해도 이미 clone 해간 사본까지는 못 지운다
  → 유일한 대응은 그 비밀번호를 폐기하고 새로 발급하는 것
```

그래서 질문이 이렇게 좁혀진다. Secret을 Git에 올려도 될까? 올린다면 암호화해야 하는데, 암호화했으면 언젠가는 풀어야 한다. 그 열쇠는 어디에 두지?

열쇠를 Git에 같이 두면 암호화한 의미가 없고, 사람이 매번 손으로 풀면 GitOps의 자동화가 깨진다. 결국 복호화가 일어나는 지점을 어디로 잡을 것인가가 이 장 전체를 관통하는 질문이 된다.

```
선택지 세 곳
  개발자 로컬   커밋 전 암호화, 배포 시 로컬에서 복호화  → 열쇠 관리가 흩어짐
  CI 파이프라인 빌드 서버가 복호화해서 클러스터에 적용   → CI 가 새 공격 표적
  클러스터 내부 암호문 그대로 넣고 안에서 컨트롤러가 품  → Sealed Secrets 방식
```

### 2.3 클러스터 안도 안전하지 않다 — 관리자라는 신뢰 경계

밖을 막았다고 끝이 아니다. etcd 암호화를 켜고 Secret을 잘 넣어뒀다 해도, 클러스터에 저장된 모든 데이터에 접근할 수 있는 사람이 최소 한 명은 존재한다 — 클러스터 관리자다.

RBAC은 "누가 무엇을 할 수 있는가"를 아주 세밀하게 정할 수 있다. A팀은 dev 네임스페이스의 Secret만, B팀은 아예 못 봄, 이런 식으로. 그런데 이 규칙을 만드는 사람은 규칙 밖에 있다. `cluster-admin`은 필요하면 자기 자신에게 어떤 권한이든 부여할 수 있고, etcd 암호화 키도 노드 접근 권한도 관리자가 쥐고 있다. 자물쇠를 관리하는 사람이 마스터키를 가진 셈이다.

여기서 이 장의 반전이 나온다 — 아무리 암호화 기술을 겹겹이 쌓아도, 어느 지점에서는 결국 사람을 믿느냐 마느냐의 문제로 귀결된다.

| 상황 | 관리자가 누구인가 | 신뢰 수준 |
|---|---|---|
| 내가 직접 운영하는 클러스터 | 나 자신 | 높음 — Secret으로 충분할 수도 |
| 회사 공용 플랫폼 팀이 운영 | 같은 회사 다른 팀 | 중간 — 계약·정책으로 커버 |
| 퍼블릭 클라우드(EKS/GKE) | 클라우드 업체 | 상황에 따라 |
| 외부 업체가 운영 대행 | 제3자 | 낮음 — 별도 보호 필요 |

신뢰 경계(trust boundary)란 "여기까지는 믿고, 여기서부터는 못 믿는다"는 선이다. 이 선을 어디에 긋느냐가 곧 설계 결정이 된다. 24장 2.2의 격리 스펙트럼(네임스페이스 → NetworkPolicy → vcluster → 클러스터 분리)과 같은 구조로, 오른쪽으로 갈수록 안전하고 비싸다.

### 2.4 세 가지 노출 — 무엇을 막고 싶은가

이 장의 도구들이 헷갈리는 이유는 "노출"이 한 종류가 아니기 때문이다. 앞으로 나올 모든 도구는 아래 셋 중 어디를 막느냐로 갈린다.

```
① Git 노출          저장소에 접근 가능한 모두가 본다
② 사람 노출         복호화 권한을 가진 개발자·CI 가 본다
③ 클러스터 관리자   etcd 를 뒤지면 다 본다
```

| | ① Git | ② 사람 | ③ 관리자 |
|---|---|---|---|
| 대책 없음 | ❌ | ❌ | ❌ |
| sops | ✅ | ❌ | ❌ |
| Sealed Secrets | ✅ | ✅ | ❌ |
| External Secrets | ✅ | ✅ | ❌ |
| CSI / Injector | ✅ | ✅ | ✅ |

아래로 갈수록 많이 막지만 그만큼 무거워진다. 먼저 "누구를 어디까지 믿는가"를 정하고, 그다음에 도구를 고르는 순서가 되어야 한다.

---

## 3. Out-of-Cluster Encryption — 잠가서 내보내기

### 3.1 공통 구조 — 결국 Secret으로 착지한다

쿠버네티스에서 보안 설정을 지원하는 방식은 크게 두 부류다.

```
① Out-of-cluster encryption   (이 장 3절)
   암호화된 정보를 클러스터 밖에 둔다. 권한 없는 사람이 읽어도 상관없다
   → 클러스터에 들어가기 직전이나 들어간 직후에 Secret 으로 변환된다

② Centralized secret management  (이 장 4절)
   전용 금고 서비스에 맡긴다. 클러스터에 Secret 을 안 만들 수도 있다
```

①의 요지는 단순하다 — 바깥에서 주워 와서 Secret으로 바꾼다. 두 동작뿐이다.

```
[클러스터 밖]              [클러스터 안]
암호문 / 금고에 있는 값  →  평범한 Secret  →  앱
```

이 구조의 실용적 미덕은 앱이 안 바뀐다는 것이다. 앱은 자기가 받은 게 어디서 왔는지 모른다. 그냥 Secret일 뿐이다. 어떤 도구를 쓰든 마지막 착지점이 같으니, 기존 앱에 그대로 얹을 수 있다.

이 장이 다루는 세 도구(2023년 기준)의 차이는 출발지와 어디서 푸느냐뿐이다.

| 도구 | 비밀이 어디 있나 | 누가 푸나 |
|---|---|---|
| Sealed Secrets | Git에 암호문 | 클러스터 안 컨트롤러 |
| External Secrets | AWS/Vault 등 금고 | 클러스터 안 오퍼레이터 |
| sops | Git에 암호문 | 클러스터 밖 (사람/CI) |

셋 다 쿠버네티스 내장이 아니라 별도로 설치하는 서드파티 도구다. 쿠버네티스는 핵심만 담고 나머지는 생태계에 맡기는 구조라, 이 장의 해법은 전부 외부 도구다.

### 3.2 Sealed Secrets — 우편함 방식

2017년 Bitnami가 내놓은, 이 분야에서 가장 오래된 애드온 중 하나다. 아이디어를 한 문장으로 하면 우편함이다.

```
누구나 우편함에 편지를 넣을 수 있다      → 공개키로 암호화 (아무나 가능)
꺼내는 열쇠는 집주인만 갖고 있다         → 개인키는 클러스터 안에만
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 390" style="width:100%;min-width:600px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sealed Secrets 아키텍처: 클러스터 밖에서 공개키로 Secret을 암호화해 SealedSecret으로 Git에 올리고, 클러스터 안 오퍼레이터가 개인키로 복호화해 Secret을 만든다">
  <defs>
    <marker id="ss-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
    <path id="ss-doc" d="M0,0 h130 v40 c-21.7,0 -21.7,8 -43.3,8 c-21.7,0 -21.7,-8 -43.3,-8 c-21.7,0 -21.7,8 -43.3,8 z"/>
  </defs>

  <!-- Cluster -->
  <rect x="300" y="40" width="420" height="320" rx="6" fill="none" stroke="var(--content,#444)" stroke-width="1.5"/>
  <text x="510" y="62" text-anchor="middle" font-size="14" font-weight="600" fill="var(--content,#333)">Cluster</text>

  <!-- Secret (밖) -->
  <g transform="translate(110,95)">
    <use href="#ss-doc" fill="#fbe0c4"/>
    <text x="65" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">Secret</text>
  </g>

  <!-- Git -->
  <rect x="95" y="166" width="160" height="120" rx="4" fill="none" stroke="var(--content,#444)" stroke-width="1.5"/>
  <g transform="translate(110,186)">
    <use href="#ss-doc" fill="#e8952f"/>
    <text x="65" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">SealedSecret</text>
  </g>
  <text x="175" y="272" text-anchor="middle" font-size="13" fill="var(--content,#333)">Git</text>

  <!-- SealedSecret (클러스터) -->
  <g transform="translate(330,186)">
    <use href="#ss-doc" fill="#e8952f"/>
    <text x="65" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">SealedSecret</text>
  </g>

  <!-- Secret (클러스터) -->
  <g transform="translate(330,286)">
    <use href="#ss-doc" fill="#fbe0c4"/>
    <text x="65" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">Secret</text>
  </g>

  <!-- Operator -->
  <rect x="560" y="70" width="140" height="270" rx="4" fill="#5b9bd5"/>
  <text x="630" y="92" text-anchor="middle" font-size="13.5" font-weight="600" fill="#fff">Operator</text>
  <rect x="580" y="105" width="100" height="56" rx="3" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="630" y="128" text-anchor="middle" font-size="12" fill="#1b3f63">Public</text>
  <text x="630" y="145" text-anchor="middle" font-size="12" fill="#1b3f63">key</text>
  <rect x="580" y="245" width="100" height="56" rx="3" fill="#1f5fa8" stroke="#0e3a6b"/>
  <text x="630" y="268" text-anchor="middle" font-size="12" fill="#fff">Private</text>
  <text x="630" y="285" text-anchor="middle" font-size="12" fill="#fff">key</text>

  <!-- 실선 화살표 -->
  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#ss-ar)">
    <path d="M175,143 V180"/>
    <path d="M255,210 H326"/>
    <path d="M556,315 H466"/>
  </g>
  <!-- 점선 화살표 -->
  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" stroke-dasharray="6 4" marker-end="url(#ss-ar)">
    <path d="M578,133 H246"/>
    <path d="M556,205 H466"/>
    <path d="M395,234 V280"/>
  </g>

  <g font-size="12" fill="var(--content,#333)" font-style="italic">
    <text x="412" y="125" text-anchor="middle">Encrypt</text>
    <text x="511" y="197" text-anchor="middle">Watch</text>
    <text x="432" y="262" text-anchor="middle">Decrypt</text>
    <text x="511" y="307" text-anchor="middle">Create</text>
  </g>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  Sealed Secrets 아키텍처 — 밖에서 공개키로 잠그고, 안에서 개인키로 연다
</div>
</div>
{{< /rawhtml >}}

부품은 두 개이고, 둘 다 있어야 동작한다.

| 부품 | 어디에 | 역할 |
|---|---|---|
| `kubeseal` (CLI) | 내 노트북 | 잠그기 |
| 컨트롤러 (오퍼레이터) | 클러스터 안 | 풀기 |

전체 흐름은 이렇다.

```
[내 노트북]
  Secret YAML (평문)
      ↓ kubeseal 실행 — 공개키로 암호화
  SealedSecret YAML (암호문) → Git 에 커밋 ✅

[클러스터]
  SealedSecret 적용
      ↓ 컨트롤러가 감지, 개인키로 복호화
  Secret 생성 → 앱이 사용
```

실제로 어떻게 생기는지 전후를 보자.

```yaml
# kubeseal 전 — Git 금지
kind: Secret
data:
  password: bXlwYXNzd29yZA==   # base64, 그냥 풀림
---
# kubeseal 후 — Git 가능
kind: SealedSecret
apiVersion: bitnami.com/v1alpha1
spec:
  encryptedData:
    password: AgBv3kM8xQpL9d...(긴 암호문)
    user: AgAmvgFQBBNPlt9G...
```

`kind`가 `Secret` → `SealedSecret`으로, `data`가 `encryptedData`로 바뀌었다. `Ag`로 시작하는 건 Sealed Secrets 형식의 표식이고, base64와 달리 아무리 디코딩해도 원래 값이 안 나온다.

눈여겨볼 점은 값을 통째로가 아니라 하나씩 암호화한다는 것이다. 비밀번호만 바꾸면 `password` 줄만 바뀌고 `user` 줄은 그대로다.

핵심은 암호화는 밖, 복호화는 안이라는 비대칭이다. 개인키가 클러스터 밖으로 절대 안 나가기 때문에, 내 노트북이 털려도 Git이 털려도 비밀번호는 안 샌다. 대신 대가가 둘 있다.

```
① 다른 클러스터에서는 못 푼다
   클러스터마다 개인키가 다르다 → dev 용 SealedSecret 을 prod 에 그냥 못 쓴다
   보안상 장점이지만, 클러스터가 여러 개면 각각 다시 봉인해야 한다

② 개인키를 잃으면 끝이다
   Git 의 모든 SealedSecret 이 영원히 못 풀리는 쓰레기가 된다. 복구 불가
```

②는 실무에서 가장 많이 터지는 사고라 별도로 강조할 만하다.

```bash
# 이건 무조건 해두자. 이 파일은 Git 금지 — 금고나 1Password 로
kubectl get secret -n kube-system \
  -l sealedsecrets.bitnami.com/sealed-secrets-key \
  -o yaml > sealed-secrets-key-BACKUP.yaml
```

특히 위험한 순간은 이렇다 — 클러스터를 새로 만들고 기존 Git 매니페스트를 그대로 적용할 때, `helm uninstall`로 오퍼레이터를 지우면서 Secret도 같이 삭제될 때, etcd 복구에 실패할 때. 쿠버네티스가 알아서 백업해주지 않으므로 관리자의 몫이다.

그리고 한계도 분명하다. 복호화된 평범한 Secret이 결국 클러스터 안에 생긴다. 2.4의 표에서 ③을 못 막는 이유다. 이건 "Git에 안전하게 올리기"를 푸는 도구지, "클러스터 안에서 숨기기"를 푸는 도구가 아니다.

#### 3.2.1 하이브리드 암호화 — 왜 두 번 잠그나

Sealed Secrets는 AES-256-GCM으로 대칭 암호화하고, 그 세션 키를 다시 RSA-OAEP로 비대칭 암호화한다. TLS가 쓰는 것과 같은 구성이다. 왜 두 번 잠글까?

| | 대칭 (AES) | 비대칭 (RSA) |
|---|---|---|
| 속도 | 빠름 | 느림 |
| 크기 제한 | 없음 | 작은 데이터만 (2048비트 키면 200바이트 남짓) |
| 문제 | 열쇠를 어떻게 전달? | 느리고 제한적 |

각자 못하는 게 있어서 섞어 쓴다.

```
1. 임시 열쇠(세션 키)를 즉석에서 하나 만든다
2. 실제 비밀번호는 → AES 로 잠근다     (빠름, 크기 무관)
3. 그 임시 열쇠만  → RSA 공개키로 잠근다 (작으니까 가능)
4. 둘을 같이 저장한다
```

큰 짐은 튼튼한 금고(AES)에 넣고, 그 금고 열쇠는 작은 우편함(RSA)에 넣는다. 우편함은 집주인만 열 수 있으니, 열쇠를 꺼내서 → 금고를 여는 순서가 된다. 이 구조는 뒤에 나올 sops에서도, KMS 연동에서도 똑같이 반복된다.

공개키를 Git에 올려도 되는 이유도 여기서 나온다 — 이름 그대로 공개키라 잠글 수만 있고 열 수는 없다. 실무에서는 이걸 파일로 받아두면 클러스터에 접속하지 않고도 봉인할 수 있어 CI나 오프라인 환경에서 편하다.

```bash
kubeseal --fetch-cert > pub-cert.pem                        # 공개키 뽑아두기
kubeseal --cert pub-cert.pem < secret.yaml > sealed.yaml    # 클러스터 없이 암호화
```

| | 공개키 | 개인키 |
|---|---|---|
| 어디에 | 아무 데나, Git에도 OK | 클러스터 안에만 |
| 할 수 있는 것 | 잠그기만 | 풀기 |
| 유출되면 | 문제 없음 | 치명적 |
| 잃어버리면 | 다시 받으면 됨 | 복구 불가 |

공개키는 자유롭게 배포하고, 개인키 하나만 엄격히 지킨다. 보안이 한 점으로 모이는 것이 이 설계의 핵심이자, 동시에 그 한 점을 잃으면 복구할 수 없다는 위험이기도 하다.

#### 3.2.2 스코프 — 이 편지를 어디서 열 수 있게 할까

Sealed Secrets는 암호화할 때 네임스페이스와 이름을 암호문에 같이 섞어 넣는다. 복호화할 때 "너 원래 `prod` 네임스페이스의 `db-secret` 맞아?" 하고 대조하고, 안 맞으면 안 풀어준다.

왜 이런 게 필요한지는 공격 시나리오를 보면 바로 이해된다.

```
악의적인 개발자가
  Git 에서 prod 네임스페이스의 암호화된 DB 비밀번호를 복사
  → 자기가 권한 있는 dev 네임스페이스에 붙여넣고 적용
  → 파드를 띄워 echo $DB_PASSWORD 로 프로덕션 비밀번호를 훔쳐본다
```

Strict 모드면 이게 막힌다. 네임스페이스가 다르니 복호화 자체가 실패한다.

| 스코프 | 네임스페이스 | 이름 | 보안 | 언제 |
|---|---|---|---|---|
| Strict (기본) | 고정 | 고정 | 가장 강함 | 그냥 이걸 써라 |
| Namespace-wide | 고정 | 자유 | 중간 | Helm 릴리스마다 이름이 바뀔 때 |
| Cluster-wide | 자유 | 자유 | 가장 약함 | 모든 팀에 뿌릴 공용 레지스트리 인증 등 |

지정 방법은 두 가지다.

```bash
kubeseal < secret.yaml > sealed.yaml                        # Strict (기본)
kubeseal --scope namespace-wide < secret.yaml > sealed.yaml
kubeseal --scope cluster-wide  < secret.yaml > sealed.yaml
```

```yaml
# 어노테이션으로도 가능 — GitOps 에서 매니페스트로 관리할 때 편하다
kind: Secret
metadata:
  name: db-secret
  annotations:
    sealedsecrets.bitnami.com/cluster-wide: "true"   # ★ 따옴표 필수
```

| 어노테이션 | 값 | 효과 |
|---|---|---|
| `sealedsecrets.bitnami.com/namespace-wide` | `"true"` | 이름은 자유, 네임스페이스는 고정 |
| `sealedsecrets.bitnami.com/cluster-wide` | `"true"` | 이름·네임스페이스 모두 자유 |

여기서 두 가지 함정. 첫째, 값은 반드시 문자열이어야 한다 — 따옴표 없이 `true`라고 쓰면 YAML이 불리언으로 읽어 에러가 난다(24장 3.4의 `role-database-client: 'true'`와 같은 이유다). 둘째, `strict`용 어노테이션은 따로 없다 — 둘 다 안 붙이면 자동으로 가장 안전한 Strict가 된다. 기본값이 안전한 쪽이라는 점에서 24장 3.5의 "기본값이 다 열림"보다 나은 설계다.

실무 팁 하나 — SealedSecret을 적용했는데 Secret이 안 생기고 로그에 `no key could decrypt secret`이 뜬다면, 십중팔구 스코프 문제다. 이름이나 네임스페이스를 도중에 바꿨을 가능성이 높다.

### 3.3 External Secrets — Git에는 주소만 적는다

External Secrets Operator의 발상은 앞과 정반대다.

```
Sealed Secrets   → 비밀번호를 Git 에 넣는다 (잠가서)
External Secrets → Git 에 주소만 적는다. 비밀번호는 금고에 있다
```

```yaml
# Sealed Secrets — 잠긴 실제 값이 Git 에 있다
kind: SealedSecret
spec:
  encryptedData:
    password: AgCrKIIF2gA7tSR...
---
# External Secrets — 값이 아예 없다. 암호화조차 안 되어 있다
kind: ExternalSecret
spec:
  data:
  - secretKey: password
    remoteRef:
      key: prod/db-password        # 그냥 주소. 전화번호부 같은 것
```

암호화된 데이터 저장소를 직접 관리하지 않고 외부 SMS에 힘든 일을 맡긴다. 암호화, 복호화, 안전한 영속화까지 전부. 그러면 클라우드 SMS의 기능이 딸려 온다.

```
자동 키 교체    30일마다 DB 비밀번호를 알아서 갱신
감사 로그       누가 언제 이 값을 읽었는지 기록
전용 UI         터미널 없이 브라우저에서 관리
정교한 권한     IAM 으로 세밀하게
```

Sealed Secrets로는 이 중 하나도 못 한다. 개인키 백업과 교체가 전부 내 책임이었던 것과 대조적이다.

리소스는 두 개이고, 오퍼레이터가 이 둘을 조정(reconcile)한다.

| 리소스 | 답하는 질문 | 비유 |
|---|---|---|
| `SecretStore` | 어느 금고? 어떻게 로그인? | 은행 주소 + 내 카드 |
| `ExternalSecret` | 그 안에서 뭘 꺼내? | 출금 요청서 |

굳이 나눈 이유는 금고 접속 정보(리전, 인증 방식)가 모든 시크릿에 대해 똑같기 때문이다. 매번 반복해 적을 이유가 없다.

```
SecretStore (1개)  ←──┬── ExternalSecret: db-password
                      ├── ExternalSecret: api-key
                      └── ExternalSecret: smtp-cred
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 360" style="width:100%;min-width:600px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="External Secrets 아키텍처: Git의 ExternalSecret을 적용하면 오퍼레이터가 SecretStore를 참조해 외부 SMS에서 값을 가져와 Secret을 만든다">
  <defs>
    <marker id="es-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
    <path id="es-doc" d="M0,0 h130 v44 c-21.7,0 -21.7,8 -43.3,8 c-21.7,0 -21.7,-8 -43.3,-8 c-21.7,0 -21.7,8 -43.3,8 z"/>
  </defs>

  <!-- Cluster -->
  <rect x="200" y="30" width="400" height="300" rx="6" fill="none"
        stroke="var(--secondary,#888)" stroke-width="1.5" stroke-dasharray="7 5"/>
  <text x="400" y="52" text-anchor="middle" font-size="14" font-weight="600" fill="var(--content,#333)">Cluster</text>

  <!-- Git -->
  <rect x="20" y="150" width="150" height="120" rx="4" fill="none" stroke="var(--content,#444)" stroke-width="1.5"/>
  <g transform="translate(30,170)">
    <use href="#es-doc" fill="#e8952f"/>
    <text x="65" y="27" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">ExternalSecret</text>
  </g>
  <text x="95" y="256" text-anchor="middle" font-size="13" fill="var(--content,#333)">Git</text>

  <!-- SecretStore -->
  <g transform="translate(232,80)">
    <use href="#es-doc" fill="#c0392b"/>
    <text x="65" y="27" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">SecretStore</text>
    <text x="112" y="46" text-anchor="middle" font-size="13">🔑</text>
  </g>

  <!-- ExternalSecret (in cluster) -->
  <g transform="translate(232,178)">
    <use href="#es-doc" fill="#e8952f"/>
    <text x="65" y="27" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">ExternalSecret</text>
  </g>

  <!-- Secret -->
  <g transform="translate(232,266)">
    <use href="#es-doc" fill="#fbe0c4"/>
    <text x="65" y="27" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">Secret</text>
  </g>

  <!-- Operator -->
  <rect x="450" y="75" width="110" height="230" rx="4" fill="#5b9bd5"/>
  <text x="505" y="196" text-anchor="middle" font-size="13.5" font-weight="600" fill="#fff">Operator</text>

  <!-- SMS -->
  <rect x="650" y="150" width="80" height="60" rx="4" fill="#c0392b"/>
  <text x="690" y="185" text-anchor="middle" font-size="13.5" font-weight="600" fill="#fff">SMS</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#es-ar)">
    <path d="M170,204 H228"/>
    <path d="M450,106 H368"/>
    <path d="M450,204 H368"/>
    <path d="M450,292 H368"/>
    <path d="M560,180 H646"/>
  </g>

  <g font-size="12" fill="var(--content,#333)" font-style="italic">
    <text x="199" y="196" text-anchor="middle">kubectl apply</text>
    <text x="409" y="198" text-anchor="middle">Watch</text>
    <text x="409" y="286" text-anchor="middle">Create</text>
    <text x="603" y="172" text-anchor="middle">Fetch secret</text>
  </g>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  External Secrets 아키텍처 — Git에는 주소만, 값은 SMS에서
</div>
</div>
{{< /rawhtml >}}

```yaml
# ① 은행 주소와 출입증 등록 — 아직 아무 비밀번호도 안 가져온다
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: secret-store-aws
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        secretRef:                       # ★ 액세스 키 방식 — 실무 비권장 (4.1.1)
          accessKeyIDSecretRef:
            name: awssm-secret
            key: access-key
          secretAccessKeySecretRef:
            name: awssm-secret
            key: secret-access-key
---
# ② 출금 요청서
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h                    # ❹ 1시간마다 다시 확인
  secretStoreRef:                        # ❶ 위의 store 참조
    name: secret-store-aws
    kind: SecretStore
  target:
    name: db-credentials-secrets         # ❷ 만들어질 Secret 이름
    creationPolicy: Owner                # ❺ 이 Secret 의 주인은 나
  data:                                  # ❸ AWS 경로 → Secret 키 매핑
  - secretKey: username
    remoteRef:
      key: cluster/db-username
  - secretKey: password
    remoteRef:
      key: cluster/db-password
```

이름이 달라도 되는 게 포인트다. AWS에서는 `cluster/db-username`이지만 Secret 안에서는 그냥 `username`으로 쓴다.

```
AWS Secret Manager              생성될 Secret
─────────────────────           ──────────────
cluster/db-username     ──→     username
cluster/db-password     ──→     password
```

`refreshInterval`이 진짜 강점이다. Sealed Secrets는 한 번 풀면 끝이지만, External Secrets는 계속 동기화한다.

```
Sealed Secrets    다시 봉인 → 커밋 → 배포   (사람 개입)
External Secrets  AWS 에서 값만 변경        (끝)
```

Git을 건드릴 필요가 없어서 자동 키 교체와 궁합이 좋다. 다만 Secret이 바뀌어도 파드가 자동으로 재시작하지는 않는다 — 환경변수로 읽었다면 파드를 다시 띄워야 하고, 볼륨이면 파일은 갱신되지만 앱이 다시 읽어야 한다. Reloader 같은 도구를 같이 쓰기도 한다.

`creationPolicy: Owner`는 "이 Secret은 내가 주인"이라는 선언이다. ExternalSecret을 지우면 Secret도 같이 삭제되고, 누가 손으로 고치면 다음 동기화 때 되돌린다.

이 도구의 가장 큰 가치는 기능이 아니라 관심사 분리에 있다.

```
보안팀   금고에 접근해 비밀번호 관리. 쿠버네티스는 몰라도 됨
개발자   "cluster/db-password 를 가져다 써" 라고만 적음
         → 실제 값을 평생 볼 일이 없다
```

Sealed Secrets는 이게 안 된다. 봉인하려면 누군가는 평문 비밀번호를 손에 쥐어야 한다. 클라이언트 측 솔루션 대비 이 방식의 결정적 장점은 오직 서버 측 오퍼레이터만이 외부 SMS 자격 증명을 안다는 것이다.

```
❌ 클라이언트 방식: 개발자A, 개발자B, CI서버 … 전부 AWS 키 보유
✅ 오퍼레이터 방식: 오퍼레이터 하나만 보유
```

External Secrets Operator는 난립하던 여러 Secret 동기화 프로젝트를 통합했고, 2023년 기준 이 용도의 지배적 솔루션이다. 실무적으로는 "골라도 안전하다"는 신호다. 다만 Sealed Secrets와 똑같은 비용을 갖는다 — 서버 측 컴포넌트가 항상 실행되어야 한다.

### 3.4 sops — 값만 잠그고 키는 남긴다

앞의 두 도구가 남긴 공통 숙제가 있다. 오퍼레이터가 클러스터에 상주해야 한다. GitOps 세계에서 정말 서버 측 컴포넌트가 필요할까?

Mozilla의 sops("Secret OPerationS")는 순수 클라이언트 측 솔루션이다. 클러스터에 설치할 게 없다.

```
Sealed Secrets   → 클러스터 안 오퍼레이터가 품
External Secrets → 클러스터 안 오퍼레이터가 가져옴
sops             → 클러스터는 아무것도 모른다
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 700 340" style="width:100%;min-width:560px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sops 아키텍처: 로컬에서 KMS 키로 Secret을 암호화해 Git에 두고, 적용 직전 같은 키로 복호화해 클러스터에 넣는다">
  <defs>
    <marker id="sp-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
    <path id="sp-doc" d="M0,0 h130 v40 c-21.7,0 -21.7,8 -43.3,8 c-21.7,0 -21.7,-8 -43.3,-8 c-21.7,0 -21.7,8 -43.3,8 z"/>
  </defs>

  <!-- Secret (평문) -->
  <g transform="translate(60,40)">
    <use href="#sp-doc" fill="#fbe0c4"/>
    <text x="65" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">Secret</text>
  </g>

  <!-- KMS -->
  <rect x="300" y="40" width="110" height="52" rx="4" fill="#8e44ad"/>
  <text x="355" y="72" text-anchor="middle" font-size="13.5" font-weight="600" fill="#fff">KMS</text>

  <!-- Git -->
  <rect x="40" y="180" width="180" height="120" rx="4" fill="none" stroke="var(--content,#444)" stroke-width="1.5"/>
  <g transform="translate(60,200)">
    <use href="#sp-doc" fill="#e8952f"/>
    <text x="65" y="20" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">Secret</text>
    <text x="65" y="35" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">(encrypted)</text>
  </g>
  <text x="130" y="288" text-anchor="middle" font-size="13" fill="var(--content,#333)">Git</text>

  <!-- Cluster -->
  <rect x="420" y="180" width="230" height="120" rx="6" fill="none"
        stroke="var(--secondary,#888)" stroke-width="1.5" stroke-dasharray="7 5"/>
  <g transform="translate(470,200)">
    <use href="#sp-doc" fill="#fbe0c4"/>
    <text x="65" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">Secret</text>
  </g>
  <text x="535" y="288" text-anchor="middle" font-size="13" fill="var(--content,#333)">Cluster</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#sp-ar)">
    <path d="M125,88 V194"/>
    <path d="M220,240 H466"/>
    <path d="M214,178 L297,94"/>
    <path d="M355,232 V98"/>
  </g>

  <g font-size="12" fill="var(--content,#333)" font-style="italic">
    <text x="180" y="146" text-anchor="middle">sops --encrypt</text>
    <text x="300" y="228" text-anchor="middle">sops --decrypt</text>
  </g>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  sops — 값만 잠가 Git에 두고, 적용 직전 같은 열쇠로 연다
</div>
</div>
{{< /rawhtml >}}

그리고 sops는 쿠버네티스 전용이 아니다. 그냥 파일 암호화 도구라서 Terraform 변수, Ansible 설정, 앱의 `config.yaml`, 개인 메모에도 쓴다. 쿠버네티스 매니페스트는 여러 용도 중 하나일 뿐이다.

핵심 아이디어는 모든 값은 암호화하되 키는 그대로 두는 것이다.

```yaml
# 원본
apiVersion: v1
kind: ConfigMap
metadata:
  name_unencrypted: db-auth      # ★ _unencrypted 접미사 = 암호화 건너뛰기
data:
  USER: "batman"
  PASSWORD: "r0b1n"
```

```bash
$ age-keygen -o keys.txt                    # ① 열쇠 쌍 생성
Public key: age1j49ugcg2rzyye07ksyvj5688m6hmv

$ sops --encrypt \                          # ② 공개키로 잠그기
    --age age1j49ugcg2rzyye07ksyvj5688m6hmv \
    configmap.yaml > configmap_encrypted.yaml
```

```yaml
# 결과
apiVersion: ENC[AES256_GCM,data:...,iv:...,tag:...,type:str]
kind: ENC[AES256_GCM,data:...]
metadata:
  name_unencrypted: db-auth                 # ← 그대로 보인다
data:
  USER: ENC[AES256_GCM,data:...]
  PASSWORD: ENC[AES256_GCM,data:...]
sops:                                       # ← sops 가 붙인 메타데이터
  age:
  - recipient: age1j49ugcg2rzyye07ksyvj5688m6hmv
    enc: |
      -----BEGIN AGE ENCRYPTED FILE-----
      YWdlLWVuY3J5cHRpb24ub3JnL3Yx...
      -----END AGE ENCRYPTED FILE-----
  unencrypted_suffix: _unencrypted
```

여기서 두 가지를 짚어야 한다.

첫째, `enc`가 3.2.1에서 본 그 구조다. 문서의 값들은 세션 키로 AES 암호화되고, 그 세션 키를 age 공개키로 비대칭 암호화한 결과가 `enc`에 들어간다. 완전히 같은 하이브리드 패턴이다.

```
값들     ← 세션 키로 AES 암호화        → ENC[...] 에
세션 키  ← age/RSA/KMS 로 비대칭 암호화 → enc: 에
```

둘째, `_unencrypted` 접미사가 필요한 이유. sops는 쿠버네티스를 모르니 `apiVersion`, `kind`까지 무차별 암호화한다. 리소스 이름까지 가려지면 Git에서 파일을 봐도 이게 뭔지 모른다. 그래서 이 접미사가 붙은 필드는 건너뛴다. (실무에서는 `.sops.yaml`에 `encrypted_regex: '^(data|stringData)$'`를 적어 "data 아래만 암호화"하는 게 더 흔하다.)

"키는 두고 값만 잠근다"의 실용적 가치는 Git diff에서 나온다.

```diff
 data:
   USER: ENC[AES256_GCM,data:vN7k...]       # 그대로
-  PASSWORD: ENC[AES256_GCM,data:zR4t...]
+  PASSWORD: ENC[AES256_GCM,data:mB8w...]   # 이것만 바뀜
```

값은 여전히 모르지만 "비밀번호가 변경됐구나"는 알 수 있다. 코드 리뷰에서 꽤 큰 차이다.

복호화와 배포는 한 줄이다.

```bash
$ export SOPS_AGE_KEY_FILE=keys.txt                         # ① 개인키 위치
$ sops --decrypt configmap_encrypted.yaml | kubectl apply -f -   # ② 풀어서 바로 적용
configmap/db-auth created
```

파이프로 이어서 평문 파일이 디스크에 안 생긴다. 그리고 복호화 과정에서 `_unencrypted` 접미사가 자동으로 제거되어, 쿠버네티스는 정상적인 `name` 필드로 받는다.

여기서 헷갈리기 쉬운 지점 하나 — `age-keygen`은 하나의 파일에 공개키와 개인키를 둘 다 넣는다.

```
keys.txt  ┬─ # public key: age1j49...        ← 잠글 때 (화면에도 출력됨)
          └─ AGE-SECRET-KEY-1QYQSZ...        ← 풀 때 (파일 안에만)
```

잠글 때는 `--age age1j49...`로 공개키 문자열을 직접 쓰고, 풀 때는 `SOPS_AGE_KEY_FILE`로 파일을 가리킨다. 명령어가 하나였을 뿐 열쇠는 둘이다.

sops는 로컬에서 돌릴 수도, CI 파이프라인에서 돌릴 수도 있는데 실무 정답은 후자다.

```
개발자   암호문만 커밋. 복호화 권한 없음
CI       자동으로 풀어서 배포. 사람 눈에 안 띔
```

```yaml
# GitHub Actions
- run: sops -d secret.enc.yaml | kubectl apply -f -
```

그리고 CI가 쓸 열쇠로는 age 파일보다 클라우드 KMS가 매끄럽다 — 개인키 파일을 CI 시크릿에 넣고 관리·교체할 필요가 없어지기 때문이다(4.1.1).

정리하면 sops의 트레이드오프는 명확하다.

| | 좋은 점 | 나쁜 점 |
|---|---|---|
| | 클러스터에 설치할 게 없음 | 개발자/CI 가 복호화 권한을 가짐 |
| | 쿠버네티스 아니어도 씀 | 값 바꾸면 다시 잠그고 커밋해야 함 |
| | Git diff 가 읽힘 | 자동 동기화 없음 |

2.4의 표에서 sops만 ②를 못 막는 이유가 이것이다. 오퍼레이터가 있으면 사람이 안 봐도 되고(안전, 무거움), 없으면 사람이 봐야 한다(가벼움, 덜 안전). 공짜는 없다.

### 3.5 SMS vs KMS — 물건을 맡기나 열쇠를 맡기나

앞에서 AWS Secrets Manager와 AWS KMS가 둘 다 나왔는데, 이름이 비슷하지만 하는 일이 다르다.

```
SMS (Secret Management System)   물건을 맡아주는 금고
KMS (Key Management System)      열쇠만 맡아주는 곳. 물건은 내가 보관
```

| | SMS | KMS |
|---|---|---|
| 뭘 보관 | 비밀번호 자체 | 암호화 키만 |
| 예시 | AWS Secrets Manager, Azure Key Vault | AWS KMS, GnuPG 키서버 |
| 내가 하는 일 | "값 좀 줘" | "이거 잠가줘 / 풀어줘" |
| 데이터 위치 | 클라우드 안 | 내 쪽에 (Git 등) |

이 장에서 이미 둘 다 봤다.

```yaml
# External Secrets → SMS 방식. Git 에 값이 없다
remoteRef:
  key: prod/db-password
---
# sops → KMS 방식. Git 에 암호문이 있고, 여는 열쇠만 AWS 것
password: ENC[AES256_GCM,data:zR4t...]
sops:
  kms:
    arn: arn:aws:kms:us-east-1:123456:key/abc-123
```

SMS는 은행 대여금고다. 물건을 맡기고 필요할 때 꺼낸다. 암호화를 알아서 해주므로 내가 신경 쓸 게 없다 — `aws secretsmanager get-secret-value`를 치면 평문이 그냥 나온다. 책이 "투명하게 암호화된다"고 한 게 이 뜻이다.

KMS는 열쇠 보관소다. 물건은 내 집 금고(=Git)에 두고, 그 금고 열쇠만 맡긴다. 열려면 열쇠를 빌려 와야 한다.

여기서 흔한 오해 하나를 짚자 — KMS가 내 파일을 보는 게 아니다.

```
1. sops 가 파일 안의 sops: 블록에서 enc(암호화된 데이터 키)를 읽는다
2. 그 작은 데이터 키만 AWS 로 보낸다: "이거 풀어줘"
3. AWS 는 내 계정 권한만 확인 (IAM 정책 + KMS 키 정책, 둘 다 통과해야 함)
4. 통과하면 데이터 키를 풀어서 돌려준다
5. sops 가 받은 키로 내 컴퓨터에서 문서를 푼다
```

네트워크로 오가는 건 작은 열쇠 조각뿐이고, 실제 비밀번호는 내 컴퓨터를 떠나지 않는다.

age 대신 KMS를 쓰면 얻는 것이 크다.

| | age 파일 | 클라우드 KMS |
|---|---|---|
| 열쇠 파일 | 있음 (관리 부담) | 없음 |
| 팀 공유 | 파일을 어떻게 나눠주지? | IAM 권한만 주면 끝 |
| 퇴사자 | 이미 복사해갔으면 못 막음 | 권한 회수 → 즉시 차단 |
| 감사 | 없음 | CloudTrail 에 전부 기록 |

나중에 취소가 가능하다는 것이 파일 대신 KMS를 쓰는 결정적 이유다. 저장소를 통째로 복사해간 사람도 권한을 빼면 그 순간부터 못 푼다.

참고로 여러 명이 풀 수 있게 하려면 `enc`를 여러 개 넣으면 된다 — 같은 데이터 키를 각자의 방식으로 잠가둔 것이다. 사람이 나가면 그 줄만 지우고 다시 암호화한다.

```yaml
sops:
  kms:
  - arn: .../key/aws-prod-key
    enc: AQICAHh...              # AWS 권한자용
  age:
  - recipient: age1ql3z...
    enc: -----BEGIN AGE...       # 개발자 A 용
  - recipient: age1x7fp...
    enc: -----BEGIN AGE...       # CI 서버용
```

---

## 4. Centralized Secret Management — 아예 저장하지 않기

3절의 세 도구는 ①과 ②는 막았지만 ③은 못 막았다. 이유는 하나다 — 셋 다 결국 평범한 Secret을 클러스터에 만든다.

```bash
kubectl get secret -o yaml   # 관리자가 치면 그냥 다 보인다
```

그래서 발상을 바꾼다. 애초에 Secret 리소스를 만들지 말자.

```
[기존]
금고 → Secret 리소스 → 앱
        ↑ 여기가 취약

[새 방식]
금고 ──────────────→ 앱
   (파드가 뜰 때 직접 가져옴. 저장 안 함)
```

핵심은 on demand다. 미리 저장해두는 게 아니라 파드가 뜰 때 그때그때 가져와서 메모리에만 둔다. 파드가 죽으면 같이 사라지고, 재시작하면 금고에서 다시 받아온다. 클러스터에 저장된 게 없으니 관리자가 볼 것도 없다.

구현 방법은 크게 셋이고, 첫 번째는 권장되지 않는다.

| 방식 | 어떻게 | 앱 코드 |
|---|---|---|
| 앱이 직접 호출 | Vault SDK 로 요청 | 수정 필요 ❌ |
| CSI 드라이버 | 볼륨으로 마운트 | 그대로 ✅ |
| Init / Sidecar 주입 | 컨테이너가 가져와 파일로 | 그대로 ✅ |

앱이 직접 호출하는 방식의 문제는 두 가지다 — SMS에 접근할 자격 증명을 여전히 앱 옆에 둬야 하고(결국 원점), 코드가 특정 SMS에 묶여서 AWS로 옮기면 다시 짜야 한다.

### 4.1 Secrets Store CSI Driver — 금고를 폴더처럼 마운트한다

한 문장으로 하면 금고를 폴더처럼 마운트한다. 앱은 그냥 파일을 읽는다. 그 파일이 사실은 Vault에서 실시간으로 온 거라는 걸 모른다.

CSI(Container Storage Interface)는 쿠버네티스가 정해둔 스토리지 붙이는 규격이다. USB 규격 같은 것으로, 이 규격만 지키면 뭐든 볼륨으로 마운트할 수 있다. 원래는 EBS, NFS 같은 디스크용이었는데 누군가 "비밀번호도 파일처럼 마운트하면 되겠네"라고 생각한 결과가 Secrets Store CSI Driver다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 720 400" style="width:100%;min-width:600px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Secrets Store CSI Driver 아키텍처: CSI 드라이버와 SMS provider가 금고에서 값을 가져와 파드 볼륨으로 투영한다">
  <defs>
    <marker id="cs-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
    <path id="cs-doc" d="M0,0 h130 v40 c-21.7,0 -21.7,8 -43.3,8 c-21.7,0 -21.7,-8 -43.3,-8 c-21.7,0 -21.7,8 -43.3,8 z"/>
  </defs>

  <rect x="20" y="30" width="500" height="350" rx="6" fill="none" stroke="var(--content,#444)" stroke-width="1.5"/>
  <text x="270" y="52" text-anchor="middle" font-size="14" font-weight="600" fill="var(--content,#333)">Cluster</text>

  <rect x="50" y="70" width="130" height="50" rx="4" fill="#5b9bd5"/>
  <text x="115" y="90" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Kubernetes</text>
  <text x="115" y="107" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">CSI</text>

  <rect x="300" y="70" width="140" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="370" y="90" text-anchor="middle" font-size="12.5" font-weight="600" fill="#1b3f63">Secret Store</text>
  <text x="370" y="107" text-anchor="middle" font-size="12.5" font-weight="600" fill="#1b3f63">CSI Driver</text>

  <rect x="300" y="170" width="140" height="46" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="370" y="198" text-anchor="middle" font-size="12.5" font-weight="600" fill="#1b3f63">SMS provider</text>

  <!-- Pod -->
  <rect x="50" y="230" width="160" height="130" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="130" y="252" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Pod</text>
  <ellipse cx="90" cy="279" rx="18" ry="7" fill="#4caf82"/>
  <rect x="72" y="279" width="36" height="26" fill="#4caf82"/>
  <ellipse cx="90" cy="305" rx="18" ry="7" fill="#3d9670"/>
  <rect x="70" y="322" width="120" height="26" rx="3" fill="#e6b3d9" stroke="#a05590"/>
  <text x="130" y="340" text-anchor="middle" font-size="12" font-weight="600" fill="#5a2050">App container</text>
  <path d="M108,292 H196" stroke="var(--content,#444)" stroke-width="1.4" fill="none"/>
  <path d="M130,292 V318" stroke="var(--content,#444)" stroke-width="1.4" fill="none" marker-end="url(#cs-ar)"/>

  <!-- SecretProviderClass -->
  <g transform="translate(300,268)">
    <use href="#cs-doc" fill="#4caf82"/>
    <text x="65" y="26" text-anchor="middle" font-size="11.5" font-weight="600" fill="#fff">SecretProviderClass</text>
  </g>

  <!-- Vault -->
  <rect x="570" y="170" width="120" height="60" rx="4" fill="#c0392b"/>
  <text x="630" y="195" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">HashiCorp</text>
  <text x="630" y="212" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Vault</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#cs-ar)">
    <path d="M186,95 H294"/>
    <path d="M304,95 H190" />
    <path d="M370,126 V164"/>
    <path d="M370,164 V126"/>
    <path d="M90,126 V272"/>
    <path d="M212,292 H296"/>
    <path d="M446,193 H566"/>
    <path d="M446,290 H630 V236"/>
  </g>

  <g font-size="12" fill="var(--content,#333)" font-style="italic">
    <text x="152" y="180" text-anchor="middle">Volume projection</text>
    <text x="254" y="284" text-anchor="middle">References</text>
    <text x="506" y="185" text-anchor="middle">Fetch data</text>
    <text x="530" y="282" text-anchor="middle">Key-values ref</text>
  </g>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  Secrets Store CSI Driver — 금고의 값을 파드 볼륨으로 투영한다
</div>
</div>
{{< /rawhtml >}}

| 상자 | 정체 | 하는 일 |
|---|---|---|
| Kubernetes CSI | 쿠버네티스 내장 | "볼륨 붙여줘" 요청을 드라이버에 넘김 |
| Secret Store CSI Driver | 설치 (공통) | 값을 파일로 만들어 파드에 마운트 |
| SMS provider | 설치 (금고별) | 실제로 Vault/AWS 에 접속해 값을 가져옴 |

셋으로 나눈 이유는 금고가 바뀌어도 앞의 둘은 그대로이기 위해서다. Vault에서 AWS로 이사해도 provider만 교체한다. 24장 5.2에서 본 컨트롤 플레인/데이터 플레인 분리와 같은 발상이다.

참고로 초록색 `SecretProviderClass`가 파란 상자들과 떨어져 있는 건, 파란 상자는 실행되는 프로그램이고 초록 상자는 내가 쓴 설정 파일이기 때문이다. 24장 4.5의 "공지문과 경비원" 관계가 여기서도 반복된다.

설정은 두 덩어리다.

```yaml
# ① 뭘 가져올지 — 주문서
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-database
spec:
  provider: vault                                  # ❶ azure, gcp, aws, vault
  parameters:
    vaultAddress: "http://vault.default:8200"      # ❷ Vault 주소 (실무는 https)
    roleName: "database"                           # ❸ Vault 쪽 인증 역할
    objects: |
      - objectName: "database-password"            # ❹ 파드에 생길 파일 이름
        secretPath: "secret/data/database-creds"   # ❺ Vault 안의 경로
        secretKey: "password"                      # ❻ 그중 이 키만
---
# ② 실제로 쓰는 파드
kind: Pod
apiVersion: v1
metadata:
  name: shell-pod
spec:
  serviceAccountName: vault-access-sa              # ❶ 신분증
  containers:
  - image: k8spatterns/random
    volumeMounts:
    - name: secrets-store
      mountPath: "/secrets-store"                  # ❷ 여기에 파일이 생긴다
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io             # ❸ CSI 드라이버 지정
      readOnly: true                               #    사실상 필수 (쓰기 미지원)
      volumeAttributes:
        secretProviderClass: "vault-database"      # ❹ ①을 참조
```

경로와 파일 이름의 관계를 정리하면 이렇다.

```
Vault 안:
  secret/data/database-creds
      ├─ username: admin
      └─ password: mypass123    ← secretKey 로 이것만 선택

파드 안:
  /secrets-store/database-password    ← objectName 이 파일 이름
  내용: mypass123
```

`objectName`은 Vault의 실제 경로와 무관하게 내가 정하는 파일 이름이다.

세 곳의 이름이 서로 맞물려야 한다는 점이 실무에서 제일 많이 막히는 지점이다.

```
쿠버네티스 쪽                     Vault 쪽
─────────────                    ──────────
Pod
 └ serviceAccountName:      ←→   bound_service_account_names:
     vault-access-sa                 vault-access-sa

SecretProviderClass
 └ roleName: database       ←→   auth/kubernetes/role/database
```

```bash
# Vault 쪽에 미리 있어야 하는 설정
vault write auth/kubernetes/role/database \
    bound_service_account_names=vault-access-sa \
    bound_service_account_namespaces=default \
    policies=db-policy
```

파드가 뜰 때 무슨 일이 일어나는지 순서로 보자.

```
1. 파드 스케줄됨
2. kubelet → CSI 드라이버 호출
3. 드라이버가 SecretProviderClass 를 읽음
4. SMS provider 가 파드의 SA 토큰으로 인증
5. 값을 받아옴
6. tmpfs(메모리)에 파일로 씀
7. 컨테이너에 마운트
8. 그제서야 컨테이너 시작   ← 7 까지 실패하면 ContainerCreating 에서 멈춘다
```

기존 Secret 볼륨과 비교하면 `volumes` 아래 한 블록만 다르다.

```yaml
# 기존 — etcd 에서 읽음
volumes:
- name: creds
  secret:
    secretName: db-secret
# CSI — Vault 에서 읽음
volumes:
- name: creds
  csi:
    driver: secrets-store.csi.k8s.io
    volumeAttributes:
      secretProviderClass: "vault-database"
```

`volumeMounts`나 컨테이너 쪽은 완전히 동일해서, 앱 코드도 배포 구조도 거의 그대로 두고 전환할 수 있다.

여기서 자주 나오는 질문 하나 — 메모리는 휘발하는데 그때마다 어디서 가져오나?

```
[AWS / Vault]  ← 원본. 항상 여기 있다
      ↓ 파드 뜰 때마다 요청
[파드 메모리]   ← 임시 사본. 파드와 함께 사라진다
```

원본은 금고에 영구 보관되어 있고 파드는 사본을 잠깐 빌려 쓴다. 그래서 파드가 죽어도 데이터 손실이 없고, 재시작하면 자동으로 최신 값을 받는다. 대신 금고가 죽으면 새 파드가 못 뜬다.

```
[기존]  etcd 에 저장 → 파드 뜰 때 etcd 에서 읽음 → 금고 없어도 됨
[CSI]  etcd 에 없음  → 파드 뜰 때 금고에서 읽음  → 금고가 살아있어야 함
```

"미리 복사해두느냐 vs 그때그때 받아오느냐"의 차이다.

실무에서 걸리는 것들을 모아두자.

```
환경변수로 못 쓴다        파일만 된다. secretObjects 로 Secret 을 만들 수는 있지만
                          그러면 etcd 에 저장되어 이 절의 장점이 사라진다 ⚠️
자동 반영 안 된다         rotationPollInterval 을 켜야 파일이 갱신되고,
                          그래도 앱이 파일을 다시 읽어야 한다
금고 장애 = 배포 중단     기존 파드는 멀쩡하지만 스케일아웃·재배포가 막힌다
노드 재부팅 시 폭주       파드 수백 개가 동시에 금고를 호출 → API 과금·rate limit
설치에 cluster-admin      DaemonSet 으로 모든 노드에 깔리고 kubelet 경로를 건드린다
```

책의 총평도 솔직하다 — 설정은 복잡하지만 사용은 단순하고, 기밀 데이터를 클러스터 안에 저장하는 것을 피할 수 있다. 다만 Secret만 쓸 때보다 움직이는 부품이 많아 잘못될 수 있는 것도 많고 문제 해결도 어렵다. 24장 3.2에서 "CNI가 지원 안 하면 조용히 아무것도 안 막힌다"고 했던 것과 같은 종류의 경고다.

#### 4.1.1 부트스트랩 문제와 IRSA — 들고 다닐 열쇠를 없앤다

3.3의 SecretStore 예제를 다시 보면 이상한 점이 있다.

```yaml
auth:
  secretRef:
    accessKeyIDSecretRef:
      name: awssm-secret      # ← AWS 로그인 키를 Secret 으로 클러스터에 넣었다
```

> "비밀번호를 클러스터에 안 두려고 이걸 쓰는 건데, AWS 키를 또 Secret으로 넣네?"

맞다. 이걸 부트스트랩 문제라고 한다 — 금고를 열려면 금고 열쇠가 필요한데 그 열쇠는 또 어디 두나.

그래도 이득은 있다.

```
전: DB 비번, API 키, SMTP 비번 … 수십 개가 클러스터에
후: AWS 키 1 개만 클러스터에, 나머지 전부 금고에
```

지켜야 할 대상이 수십 개에서 하나로 줄었고, 그 하나도 IAM으로 권한을 좁힐 수 있다. 하지만 실무에서는 그 하나마저 없앤다.

```yaml
# 액세스 키가 사라졌다
provider:
  aws:
    service: SecretsManager
    region: us-east-1
    auth:
      jwt:
        serviceAccountRef:
          name: external-secrets-sa
```

이게 IRSA(IAM Roles for Service Accounts)다. 원리는 "열쇠 대신 신분 증명"이다.

```
액세스 키 = 비밀번호로 로그인   → 복사되고, 잃어버리고, 남이 주우면 끝
IRSA     = 얼굴로 인증         → 들고 다닐 게 없다
```

쿠버네티스가 파드에 서명된 신분증(JWT 토큰)을 자동으로 넣어준다.

```
"나는 클러스터 X 의 default 네임스페이스에 있는
 external-secrets-sa 라는 계정입니다"  + 클러스터의 서명 ✍️
```

AWS는 미리 등록해둔 신뢰 관계로 이 서명을 검증한다. 설정은 이렇다.

```yaml
kind: ServiceAccount
metadata:
  name: external-secrets-sa
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/eso-role
```

토큰은 어디에 저장되나? 여기서 중요한 사실이 있다 — etcd에 남지 않는다.

| | 액세스 키 | 바운드 토큰 |
|---|---|---|
| 저장 위치 | etcd (영구) | 파드 메모리(tmpfs)만 |
| 만료 | 없음 | 1시간 (자동 갱신) |
| 훔쳐서 쓰면 | 어디서든 작동 | 그 파드 아니면 거부 |
| kubectl 로 조회 | 가능 | 불가능 |

"bound(묶인)"의 의미가 핵심이다. 토큰 안에 파드·네임스페이스·계정·만료 시각이 박혀 있어서, 파드가 죽으면 즉시 무효가 되고 복사해가도 다른 데선 안 먹힌다. 옛날(~1.20)에는 서비스어카운트 토큰이 Secret으로 etcd에 영구 저장됐는데, 지금은 kubelet이 파드가 뜰 때 즉석 발급한다.

CI가 클러스터 밖에서 돌면 IRSA를 못 쓰지만, OIDC 페더레이션으로 같은 일을 한다.

| CI 위치 | 방식 | 키 파일 |
|---|---|---|
| 클러스터 안 (Tekton, ArgoCD) | IRSA | 없음 ✅ |
| GitHub Actions / GitLab CI | OIDC | 없음 ✅ |
| 온프렘 Jenkins 등 | 액세스 키 | 있음 ❌ |

```
IRSA:  쿠버네티스가 서명한 토큰 → AWS 가 신뢰
OIDC:  GitHub 이 서명한 토큰    → AWS 가 신뢰
```

이름만 다르지 구조가 같다. 클라우드별로 GCP는 Workload Identity, Azure는 Managed Identity, Vault는 Kubernetes Auth Method라 부르지만 개념은 하나다 — 파드의 신원을 금고가 믿게 만든다. 처음 세팅이 번거로울 뿐, 한 번 해두면 키 교체도 유출 걱정도 사라진다.

### 4.2 Pod Injection — 컨테이너 레벨 해법

CSI가 볼륨 레벨 해법이라면, Pod injection은 컨테이너 레벨 해법이다. 같은 문제를 다른 층위에서 푼다.

```
CSI:       클러스터에 설치한 드라이버가 가져옴 → cluster-admin 필요
Injection: 파드 안의 컨테이너가 가져옴        → 파드 YAML 만 고치면 됨
```

#### 4.2.1 Init Container와 Sidecar

책은 이미 배운 두 패턴을 그대로 재활용한다.

```
Init Container (15장)
  파드 시작 → Init 이 금고에서 가져와 공유 볼륨에 씀 → 종료
           → 앱 컨테이너 시작, 그 파일을 읽음
  한 번 가져오고 끝. 이후 값이 바뀌어도 모른다

Sidecar (16장)
  사이드카가 안 죽고 계속 돌면서 금고와 동기화
  → SMS 가 시크릿을 교체(rotation)해도 로컬에서 갱신된다
```

```yaml
initContainers:
- name: fetch-secret
  image: vault-fetcher
  volumeMounts:
  - name: shared
    mountPath: /secrets
containers:
- name: app
  volumeMounts:
  - name: shared            # 같은 볼륨을 공유
    mountPath: /secrets
volumes:
- name: shared
  emptyDir:
    medium: Memory          # 메모리에만 — 디스크에 안 씀
```

사이드카가 중요한 이유는 Vault의 동적 시크릿 때문이다. Vault는 DB 계정을 1시간짜리로 발급하고 만료시킬 수 있는데, 그러면 누군가 계속 갱신해줘야 한다. Init Container로는 불가능하다.

네 방식을 한 표로 정리하면 이렇다.

| | 앱 코드 수정 | 값 갱신 | 부담 |
|---|---|---|---|
| 직접 호출 | 필요 ❌ | 앱이 알아서 | 코드가 SMS 에 결합 |
| Init Container | 불필요 ✅ | 안 됨 | 가벼움 |
| Sidecar | 불필요 ✅ | 됨 ✅ | 컨테이너 +1 |
| CSI | 불필요 ✅ | 설정하면 됨 | 드라이버 설치 |

#### 4.2.2 Vault Injector — mutating webhook이 대신 붙여준다

앞의 패턴들을 직접 쓸 수도 있지만 번거롭다. 앱마다 사이드카 20줄을 복붙해야 하고, Vault 버전을 올리면 전부 고쳐야 한다. 외부 컨트롤러가 대신 주입하게 맡기는 것이 훨씬 낫다.

HashiCorp Vault Sidecar Agent Injector가 그 예다. 어노테이션 세 줄이면 끝난다.

```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "database"
    vault.hashicorp.com/agent-inject-secret-db: "secret/data/db-creds"
spec:
  containers:
  - name: my-app        # 내 앱만 쓴다. 사이드카는 자동으로 붙는다
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 400" style="width:100%;min-width:620px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Vault Injector 아키텍처: 파드를 적용하면 인젝터가 사이드카를 끼워 넣고, 그 사이드카가 SMS에서 값을 받아 앱 컨테이너에 공유한다">
  <defs>
    <marker id="vi-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
    <path id="vi-doc" d="M0,0 h150 v66 c-25,0 -25,8 -50,8 c-25,0 -25,-8 -50,-8 c-25,0 -25,8 -50,8 z"/>
  </defs>

  <!-- Pod (작성한 YAML) -->
  <g transform="translate(20,60)">
    <use href="#vi-doc" fill="#fbe0c4" stroke="#d9a86a"/>
    <text x="75" y="20" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Pod</text>
    <rect x="14" y="30" width="122" height="26" rx="3" fill="#e6b3d9" stroke="#a05590"/>
    <text x="75" y="48" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a2050">App container</text>
  </g>

  <!-- Cluster -->
  <rect x="250" y="30" width="380" height="340" rx="6" fill="none"
        stroke="var(--secondary,#888)" stroke-width="1.5" stroke-dasharray="7 5"/>
  <text x="440" y="52" text-anchor="middle" font-size="14" font-weight="600" fill="var(--content,#333)">Cluster</text>

  <rect x="280" y="72" width="120" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="340" y="92" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">Kubernetes</text>
  <text x="340" y="109" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">API server</text>

  <rect x="470" y="72" width="130" height="50" rx="4" fill="#4caf82"/>
  <text x="535" y="92" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">Vault Sidecar</text>
  <text x="535" y="109" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">Agent Injector</text>

  <rect x="670" y="72" width="80" height="50" rx="4" fill="#c0392b"/>
  <text x="710" y="103" text-anchor="middle" font-size="13" font-weight="600" fill="#fff">SMS</text>

  <!-- 만들어진 Pod -->
  <path d="M300,220 h250 v120 c-41.7,0 -41.7,10 -83.3,10 c-41.7,0 -41.7,-10 -83.3,-10 c-41.7,0 -41.7,10 -83.3,10 z"
        fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="420" y="243" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Pod</text>
  <rect x="390" y="255" width="130" height="26" rx="3" fill="#e6b3d9" stroke="#a05590"/>
  <text x="455" y="273" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a2050">App container</text>
  <rect x="390" y="295" width="130" height="26" rx="3" fill="#4caf82"/>
  <text x="455" y="313" text-anchor="middle" font-size="11.5" font-weight="600" fill="#fff">Vault Sidecar</text>
  <ellipse cx="345" cy="277" rx="16" ry="6" fill="#4caf82"/>
  <rect x="329" y="277" width="32" height="24" fill="#4caf82"/>
  <ellipse cx="345" cy="301" rx="16" ry="6" fill="#3d9670"/>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#vi-ar)">
    <path d="M176,97 H276"/>
    <path d="M400,97 H466"/>
    <path d="M470,110 H406"/>
    <path d="M604,97 H666"/>
    <path d="M340,126 V214"/>
    <path d="M386,277 H366"/>
    <path d="M386,308 H366"/>
  </g>

  <g font-size="12" fill="var(--content,#333)" font-style="italic">
    <text x="226" y="88" text-anchor="middle">kubectl apply</text>
    <text x="434" y="88" text-anchor="middle">Inject sidecar</text>
    <text x="360" y="176" text-anchor="middle">Create</text>
  </g>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  Vault Injector — 어노테이션만 보고 사이드카를 대신 끼워 넣는다
</div>
</div>
{{< /rawhtml >}}

동작 원리는 mutating webhook — 파드가 만들어지는 중간에 끼어들어 명세를 수정하는 것이다.

```
[내가 쓴 Pod]  App container 만 있음
      ↓ kubectl apply
[API 서버]     "어? vault 어노테이션 있네"
      ↓ Injector 에게 물어봄
[Injector]     사이드카 + 볼륨을 추가한 명세를 돌려줌
      ↓ Create
[실제 Pod]     App container + Vault Sidecar + 공유 볼륨
                        ↓
                     SMS(Vault) 에서 값 가져옴
```

내가 쓴 YAML과 실제로 만들어진 파드가 다르다.

```bash
kubectl get pod my-app -o yaml   # 내가 안 쓴 vault-agent 컨테이너가 들어있다
```

책이 이걸 "사용자에게 완전히 투명하다(transparent)"고 표현한 이유다 — 내가 모르는 사이에 일어나지만 신경 쓸 필요가 없다.

웹훅은 두 종류인데, 이건 고치는 쪽이다.

```
validating  검사만 한다. 통과 / 거부
mutating    내용을 고친다  ← Vault Injector
```

참고로 이 확장 지점 자체는 쿠버네티스 내장이지만, 거기 뭘 꽂을지는 각자 선택이다. Istio(Envoy 프록시), Linkerd, Datadog 에이전트도 같은 자리를 쓴다. 24장의 사이드카 주입과 완전히 같은 메커니즘이다.

CSI와 비교하면 이렇다.

| | CSI | Vault Injector |
|---|---|---|
| 무엇을 설치 | 노드에 드라이버 + provider (DaemonSet ×2) | 웹훅 하나 (Deployment) |
| 파드에 뭐가 추가 | 볼륨만 | 컨테이너 + 볼륨 |
| 파드 명세 | 내가 씀 | 자동 주입 |
| 자원 | 노드당 하나 | 파드마다 사이드카 |

책의 평가는 "여전히 Injector 컨트롤러를 설치해야 하지만, CSI를 특정 SMS provider와 함께 엮는 것보다 움직이는 부품이 적다"는 것이다. 그러면서도 전용 클라이언트 라이브러리 없이 그냥 파일을 읽는 것만으로 시크릿에 접근할 수 있다.

```java
// 이렇게 안 해도 된다
VaultClient client = new VaultClient(...);

// 이렇게만
String pw = Files.readString(Path.of("/vault/secrets/db"));
```

앱은 Vault를 모른다. 나중에 AWS로 옮겨도 앱 코드는 그대로다.

---

## 5. Discussion

### 5.1 무엇이 최선인가 — 상황에 따라 다르다

여러 방법을 봤으니 질문은 하나다. 어느 것이 최선인가? 늘 그렇듯 상황에 따라 다르다.

| 원하는 것 | 답 | 왜 |
|---|---|---|
| Git에 안전하게 올리기만 | sops | 순수 클라이언트 측 암호화. 설치할 게 없다 |
| 가져오는 일과 쓰는 일의 분리 | External Secrets | 개발자는 이름만 적고 값은 평생 안 본다 |
| 클러스터에 영구 저장 금지 | CSI Provider | 액세스 토큰 외에 아무것도 안 남는다 |
| SMS 직접 접근 차단 + 간단함 | Vault Injector | 어노테이션 몇 줄. 다만 대가가 있다 |

세 번째 항목의 "액세스 토큰을 제외하면"이라는 단서가 솔직하다. 완벽한 무저장은 아니다 — 금고에 들어갈 열쇠 하나는 클러스터에 남는다(4.1.1의 부트스트랩 문제). 다만 지킬 게 수십 개에서 하나로 줄고, IRSA를 쓰면 그 하나도 영구 저장되지 않는다.

네 번째의 대가는 책이 콕 집어 지적한다 — 보안 어노테이션이 애플리케이션 배포에 새어 들어가면서 개발자와 관리자의 경계가 흐려진다.

```yaml
# 개발자가 쓰는 파드 YAML 인데
annotations:
  vault.hashicorp.com/role: "database"
  vault.hashicorp.com/agent-inject-secret-db: "secret/data/db-creds"
  # ↑ 개발자가 Vault 경로와 역할 이름을 알아야 한다
  #   잘못 쓰면 다른 시크릿에 접근하려 시도할 수도 있다
  #   "이 설정은 누가 책임지나?" 가 애매해진다
```

External Secrets는 이게 깔끔했다 — 보안 설정은 SecretStore에, 개발자는 이름만 참조. Injector는 그 경계가 뭉개진다. 24장에서 shift left가 미덕이었다면(앱을 아는 사람이 규칙을 짠다), 여기서는 같은 움직임이 비용이 되는 셈이다. 네트워크 규칙은 개발자가 아는 게 맞지만, 금고 경로는 꼭 그렇지 않다.

### 5.2 제품이 아니라 기법을 기억하라

책은 나열한 프로젝트들이 2023년 집필 시점 기준이며, 새 경쟁자가 나오거나 기존 프로젝트가 중단됐을 수 있다고 인정한다. 실제로 이 분야는 도구가 빨리 바뀐다.

그러면서 붙이는 단서가 이 장에서 가장 오래 남을 문장이다 — 사용된 기법들은 보편적이며 앞으로의 솔루션에서도 계속 쓰일 것이다.

```
제품 → 바뀐다 (Sealed Secrets, sops, ESO, Vault …)
기법 → 안 바뀐다
```

| 기법 | 대표 도구 | 핵심 질문 |
|---|---|---|
| 클라이언트 측 암호화 | sops, Sealed Secrets | 어디에 두고 어디서 푸나 |
| Secret 동기화 | External Secrets | 누가 가져와서 어디에 놓나 |
| 볼륨 투영 | CSI 드라이버 | 저장하나 마운트하나 |
| 사이드카 주입 | Vault Injector | 누가 파드에 넣어주나 |

5년 뒤 도구 이름이 전부 바뀌어도 새 도구는 이 넷 중 하나다. "어디에 저장되고, 누가 가져와서, 어떻게 앱에 주는가" 세 가지만 물으면 바로 분류된다. 24장 5.3에서 "어느 도구를 쓰든 패턴 자체는 그대로"라고 했던 것과 정확히 같은 결론이다.

### 5.3 완벽한 보안은 없다 — 어렵게 만들 뿐이다

책은 마지막에 분명한 경고를 남긴다.

> 시크릿 설정에 아무리 안전하게 접근하더라도, 악의를 가진 누군가가 클러스터와 컨테이너에 완전한 root 접근 권한을 갖고 있다면, 그 데이터에 도달할 방법은 언제나 존재한다.

실제로 그렇다.

```
CSI 로 파일만 마운트해도    → kubectl exec 으로 들어가 cat 하면 끝
사이드카로 주입해도         → 파드 메모리를 덤프하면 나온다
앱이 직접 Vault 를 호출해도 → 프로세스에 붙어 가로챌 수 있다
```

결국 앱이 쓰려면 어딘가에서는 평문이 되어야 하니까, 그 순간을 잡으면 된다. 이건 도구의 결함이 아니라 원리적 한계다.

그럼 왜 하나? "불가능하게"가 아니라 "어렵게"가 목표이기 때문이다.

```
아무 대책 없음   Git 훔쳐보면 끝              (누구나 가능)
sops            복호화 권한이 필요            (권한자만)
Sealed/External  클러스터 접근이 필요          (관리자급)
CSI / Injector   클러스터 root 권한이 필요     (극소수 + 흔적이 남는다)
```

공격 난이도를 올리고, 공격 가능한 사람 수를 줄이고, 흔적을 남기게 만드는 것. 그게 현실적인 보안이다.

"추가 계층(extra layer)"이라는 책의 표현이 정확하다. 이 패턴은 Secret을 대체한 게 아니라 그 위에 덧붙인 것이다.

```
[기본]  Secret (base64, 사실상 평문)
[+1층] 암호화해서 Git 에            (sops, Sealed Secrets)
[+2층] 금고에서 동기화             (External Secrets)
[+3층] 클러스터에 저장 안 함        (CSI, Injector)
```

한 겹씩 쌓을수록 안전해지지만 복잡해진다. 어디까지 쌓을지는 각자의 신뢰 경계에 달렸다 — 이 장이 처음부터 끝까지 반복한 메시지다.

### 핵심 메시지

```
Secure Configuration 의 몫: 뚫린 파드가 "쥐려는 물건" 자체를 숨기는 계층
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

전제      → Secret 은 암호화가 아니라 base64 인코딩이다. 한 줄이면 풀린다
문제      → 클러스터 밖에서는 평문과 같고(GitOps), 안에서는 관리자가 다 본다
노출 3종  → ① Git ② 사람(복호화 권한자) ③ 클러스터 관리자 — 뭘 막고 싶은지부터 정해라
1겹       → Out-of-cluster: 잠가서 내보내고 결국 Secret 으로 착지 → 앱 수정 불필요
  Sealed    우편함. 공개키로 잠그고 클러스터 개인키로 푼다. 개인키 백업이 생명
  External  Git 엔 주소만. 오퍼레이터만 금고 자격증명을 안다. refreshInterval 로 동기화
  sops      값만 잠그고 키는 남긴다 → Git diff 가 읽힌다. 대신 사람/CI 가 평문을 본다
암호화    → 하이브리드: 값은 AES 로, 그 세션 키는 RSA/age/KMS 로. 모든 도구가 같은 구조
SMS/KMS   → SMS 는 물건을 맡기고, KMS 는 열쇠만 맡긴다. KMS 는 권한 회수로 사후 차단 가능
2겹       → Centralized: 아예 Secret 을 안 만든다. 파드가 뜰 때 금고에서 직접
  CSI       금고를 볼륨처럼 마운트. etcd 에 아무것도 없음. 대신 금고 죽으면 파드가 못 뜬다
  Injection Init(1회) / Sidecar(갱신 가능) / Injector(mutating webhook 으로 자동 주입)
인증      → IRSA·OIDC — 들고 다닐 열쇠를 없앤다. 토큰은 파드 메모리에만, 1시간, 파드에 묶임
함정      → 개인키 잃으면 복구 불가 / CSI 환경변수 쓰려면 결국 etcd 저장 /
            어노테이션이 앱 배포에 새어 개발자·관리자 경계가 흐려진다
결론      → 정답은 없다. 신뢰 경계를 먼저 긋고 도구를 고른다. root 앞에선 결국 뚫린다
```

> Secure Configuration 은 "비밀을 없애는 패턴이 아니라, 비밀이 머무는 시간과 장소를 줄이는 패턴" 이다.
> Secret 이 잠긴 게 아님을 인정하고, Git 으로 나갈 땐 잠그고,
> 클러스터엔 가능하면 남기지 말고, 남겨야 한다면 볼 수 있는 사람을 줄여라.
> 완벽한 잠금은 없다 — 다만 훔치는 데 필요한 권한을 계속 올리는 것, 그것이 이 계층의 일이다.

---

## 6. References

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>Secret이 암호화되지 않는다는 사실은 Kubernetes 공식 문서 <strong>"Secrets"</strong>에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "Kubernetes Secrets are, by default, stored unencrypted in the API server's underlying data store (etcd)."
  </blockquote>
  <div>[해석] "쿠버네티스 Secret은 기본적으로 API 서버의 백엔드 저장소(etcd)에 암호화되지 않은 채로 저장된다." — 2.1의 "base64는 잠금이 아니다"와 2.3의 "관리자는 다 본다"의 근거다. 같은 문서는 etcd encryption at rest 활성화 방법, Secret에 접근 가능한 주체를 RBAC으로 제한하는 방법, 그리고 파드에 마운트된 Secret이 tmpfs에 올라간다는 점을 설명한다.</div>
  <div style="margin-top:10px;">Bitnami의 <strong>Sealed Secrets</strong> 저장소는 세 가지 스코프(strict / namespace-wide / cluster-wide)의 의미와 어노테이션, 그리고 개인키 백업·순환 절차를 문서화한다 — 3.2의 근거다. <strong>External Secrets Operator</strong> 문서는 <code>SecretStore</code>와 <code>ExternalSecret</code>의 분리, <code>creationPolicy</code>, 템플릿 기능을 다룬다.</div>
  <div style="margin-top:10px;">책의 예제에서 눈에 띈 부분 — Example 25-1의 <code>name: DB-credentials</code>는 대문자를 포함해 실제로는 적용되지 않는다(쿠버네티스 리소스 이름은 소문자와 하이픈만 허용). Example 25-3의 <code>data</code> 문법도 실제 v1beta1 스펙(<code>secretKey</code> + <code>remoteRef</code>)과 다르게 축약되어 있고, Example 25-6의 <code>http://vault.default:8200</code>은 예제용으로 TLS가 빠진 형태다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/concepts/configuration/secret/">kubernetes.io — Secrets</a></div>
  <div>→ <a href="https://github.com/bitnami-labs/sealed-secrets">GitHub — Sealed Secrets</a></div>
  <div>→ <a href="https://external-secrets.io/">external-secrets.io — External Secrets Operator</a></div>
  <div>→ <a href="https://github.com/getsops/sops">GitHub — sops</a></div>
  <div>→ <a href="https://secrets-store-csi-driver.sigs.k8s.io/">secrets-store-csi-driver.sigs.k8s.io — Secrets Store CSI Driver</a></div>
  <div>→ <a href="https://developer.hashicorp.com/vault/docs/platform/k8s/injector">developer.hashicorp.com — Vault Agent Injector</a></div>
</div>
{{< /rawhtml >}}