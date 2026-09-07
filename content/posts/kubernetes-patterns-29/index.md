---
series: ["K8sPatterns"]
title: "K8sPatterns.29 Elastic Scale"
date: 2026-09-07T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "autoscaling", "hpa", "vpa", "knative", "keda"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.29 Elastic Scale'
  relative: true
summary: "확장의 세 축 — 개수(HPA), 크기(VPA), 서버(CA). 내장은 HPA 하나뿐이고 숫자를 공급하는 쪽은 전부 설치한다는 것, 0에서 깨어나려면 Pod 앞에 문지기가 필요하다는 것, 그리고 서로 모르는 확장기들이 어떻게 맞물리는지까지."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-숫자를-미리-알-수-없다--예측이-아니라-실측" style="color:var(--secondary,inherit);text-decoration:none;">2.1 숫자를 미리 알 수 없다 — 예측이 아니라 실측</a></div>
    <div><a href="#22-세-축--개수-크기-서버" style="color:var(--secondary,inherit);text-decoration:none;">2.2 세 축 — 개수, 크기, 서버</a></div>
    <div><a href="#23-안티프래질--부하를-먹고-커지는-시스템" style="color:var(--secondary,inherit);text-decoration:none;">2.3 안티프래질 — 부하를 먹고 커지는 시스템</a></div>
  </div>
  <div><a href="#3-수동-확장--사람이-숫자를-바꾼다" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. 수동 확장 — 사람이 숫자를 바꾼다</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-명령형--빠르지만-파일에-남지-않는다" style="color:var(--secondary,inherit);text-decoration:none;">3.1 명령형 — 빠르지만 파일에 남지 않는다</a></div>
    <div><a href="#32-선언형--파일이-진실이다" style="color:var(--secondary,inherit);text-decoration:none;">3.2 선언형 — 파일이 진실이다</a></div>
    <div><a href="#33-리소스마다-다르다--statefulset-의-비대칭과-job-의-parallelism" style="color:var(--secondary,inherit);text-decoration:none;">3.3 리소스마다 다르다 — StatefulSet 의 비대칭과 Job 의 parallelism</a></div>
  </div>
  <div><a href="#4-hpa--판단은-내장-숫자는-설치" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. HPA — 판단은 내장, 숫자는 설치</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-정의-하나--울타리와-목표" style="color:var(--secondary,inherit);text-decoration:none;">4.1 정의 하나 — 울타리와 목표</a></div>
    <div><a href="#42-숫자는-어디서-오나--kubelet-에서-api-자리까지" style="color:var(--secondary,inherit);text-decoration:none;">4.2 숫자는 어디서 오나 — kubelet 에서 API 자리까지</a></div>
    <div><a href="#43-세-종류의-지표-그룹마다-하나뿐인-자리" style="color:var(--secondary,inherit);text-decoration:none;">4.3 세 종류의 지표, 그룹마다 하나뿐인 자리</a></div>
    <div><a href="#44-분자와-분모--requests-가-기준이다" style="color:var(--secondary,inherit);text-decoration:none;">4.4 분자와 분모 — requests 가 기준이다</a></div>
    <div><a href="#45-지표-선택--pod-를-늘리면-내려가는가" style="color:var(--secondary,inherit);text-decoration:none;">4.5 지표 선택 — Pod 를 늘리면 내려가는가</a></div>
    <div><a href="#46-공식은-비례식-나머지는-안전장치" style="color:var(--secondary,inherit);text-decoration:none;">4.6 공식은 비례식, 나머지는 안전장치</a></div>
  </div>
  <div><a href="#5-scale-to-zero--0-에서-깨우는-일은-누가-하나" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. Scale to Zero — 0 에서 깨우는 일은 누가 하나</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-hpa-는-왜-0-에서-못-깨어나나" style="color:var(--secondary,inherit);text-decoration:none;">5.1 HPA 는 왜 0 에서 못 깨어나나</a></div>
    <div><a href="#52-knative--문지기-카운터-결정권자" style="color:var(--secondary,inherit);text-decoration:none;">5.2 Knative — 문지기, 카운터, 결정권자</a></div>
    <div><a href="#53-keda--hpa-를-버리지-않고-반만-직접" style="color:var(--secondary,inherit);text-decoration:none;">5.3 KEDA — HPA 를 버리지 않고 반만 직접</a></div>
    <div><a href="#54-푸시와-풀--앱이-일하는-방식과-짝을-이룬다" style="color:var(--secondary,inherit);text-decoration:none;">5.4 푸시와 풀 — 앱이 일하는 방식과 짝을 이룬다</a></div>
  </div>
  <div><a href="#6-크기와-서버--vpa-와-ca" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. 크기와 서버 — VPA 와 CA</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#61-vpa--재시작이-문제였고-제자리-수정이-답이-되고-있다" style="color:var(--secondary,inherit);text-decoration:none;">6.1 VPA — 재시작이 문제였고, 제자리 수정이 답이 되고 있다</a></div>
    <div><a href="#62-네-모드--off-에서-시작한다" style="color:var(--secondary,inherit);text-decoration:none;">6.2 네 모드 — Off 에서 시작한다</a></div>
    <div><a href="#63-hpa-와-vpa--같은-지표를-보면-싸운다" style="color:var(--secondary,inherit);text-decoration:none;">6.3 HPA 와 VPA — 같은 지표를 보면 싸운다</a></div>
    <div><a href="#64-ca--cpu-가-아니라-pending-을-본다" style="color:var(--secondary,inherit);text-decoration:none;">6.4 CA — CPU 가 아니라 Pending 을 본다</a></div>
    <div><a href="#65-노드를-빼는-네-조건과-10분" style="color:var(--secondary,inherit);text-decoration:none;">6.5 노드를 빼는 네 조건과 10분</a></div>
  </div>
  <div><a href="#7-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#71-확장-수준--앱-튜닝이-맨-위인-이유" style="color:var(--secondary,inherit);text-decoration:none;">7.1 확장 수준 — 앱 튜닝이 맨 위인 이유</a></div>
    <div><a href="#72-내장과-설치--hpa-하나만-내장이다" style="color:var(--secondary,inherit);text-decoration:none;">7.2 내장과 설치 — HPA 하나만 내장이다</a></div>
    <div><a href="#73-서로-모르는데-맞물린다" style="color:var(--secondary,inherit);text-decoration:none;">7.3 서로 모르는데 맞물린다</a></div>
  </div>
  <div><a href="#8-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">8. References</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Elastic Scale 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"숫자를 사람이 맞추지 마라. 규칙만 정하고, 나머지는 실측에 맡긴다"

  확장의 세 축
  ├─ 개수  HPA · Knative · KEDA    Pod 를 몇 개
  ├─ 크기  VPA                     Pod 하나에 CPU/메모리 얼마
  └─ 서버  CA                      노드를 몇 대
                        │
                        ▼
  HPA — 이 장에서 유일하게 내장된 확장기
  ├─ 판단(HPA 컨트롤러)은 내장, 숫자 공급(metrics-server)은 설치
  ├─ 분자는 측정값, 분모는 requests. 둘 중 하나만 없어도 % 가 안 나온다
  └─ 0 으로 못 내려가고, 0 에서 못 깨어난다 — Pod 가 없으면 볼 게 없다
                        │
                        ▼
  0 으로 — Pod 앞에 문지기를 세운다
  ├─ Knative  HTTP 요청을 Activator 가 대신 받아둔다. HPA 를 버리고 자체 KPA
  └─ KEDA     큐를 30초마다 들여다본다. 0↔1 은 직접, 1↔n 은 HPA 에게
                        │
                        ▼
  크기와 서버
  ├─ VPA  requests 를 실측으로 맞춘다. 적용하려면 재시작 — 제자리 수정이 들어오는 중
  └─ CA   CPU 가 아니라 Pending Pod 를 본다. 노드를 빼려면 네 조건 + 10분
                        │
                        ▼
  서로 대화하지 않는데 맞물린다 → 부하가 올수록 커지는 시스템 = antifragile 🌱
```

26장이 **한 문에서 요청을 검문하는** 이야기였다면, 29장은 그 문 안쪽의 시스템이 **스스로 몸집을 바꾸는** 이야기다. 앞 장까지는 "Pod 3개를 유지해라"고 적으면 Kubernetes가 3개를 지켰다. 이 장은 그 **3이라는 숫자 자체를 누가 정하느냐**를 묻는다.

이 장의 재미는 확장기들이 **서로 대화하지 않는다**는 데 있다. HPA는 Pod만 보고, CA는 Pending Pod와 빈 노드만 본다. VPA는 HPA가 있는지조차 모른다. 그런데 결과적으로 맞물려 돌아간다 — HPA가 Pod를 늘리면 자리가 모자라고, 자리가 모자라면 Pending이 생기고, Pending이 생기면 CA가 노드를 산다. 아무도 다음 사람에게 전화하지 않았는데 릴레이가 이어지는 구조다. 그리고 그 릴레이의 출발점은 언제나 **실제 측정값**이지 사람의 예상이 아니다.

---

## 2. Problem

### 2.1 숫자를 미리 알 수 없다 — 예측이 아니라 실측

Kubernetes는 원하는 상태(desired state)를 적어두면 그대로 유지해준다. 문제는 **그 상태에 적을 숫자를 사람이 미리 알기 어렵다**는 것이다.

```
replicas: ?        점심시간엔 손님이 몰리고 새벽엔 텅 빈다
requests.cpu: ?    앱이 실제로 얼마 쓰는지 배포 전엔 감으로 적는다
노드: ? 대          이번 주 세일 트래픽이 10배일지 3배일지 아무도 모른다
```

너무 크게 잡으면 돈 낭비, 너무 작게 잡으면 SLA를 못 지킨다. 그리고 어렵게 맞춰놔도 워크로드는 시간대·요일·계절에 따라 계속 변한다. 책의 표현을 빌리면 "정확히 파악하는 데 시간과 노력이 든다" — 한 번이 아니라 **계속**.

이 장의 전환은 한 문장이다.

```
예측(anticipated)   "아마 점심에 100명 올 거야"        → 사람이 짐작, 틀리기 쉽다
실측(actual usage)  "지금 문 앞에 47명 줄 서 있다"     → 측정값에 반응, 정확하다
```

다행히 Kubernetes에서는 이 숫자들 — 복제본 수, requests, 노드 수 — 을 **바꾸기가 쉽다.** 그러니 "얼마로 적을지"를 고민하는 대신 "언제 바꿀지"의 규칙만 정하고, 실제 값은 측정에 맡기자는 것이다.

### 2.2 세 축 — 개수, 크기, 서버

확장은 세 방향이 있고, 이 장은 셋을 다 다룬다.

| 축 | 뭘 바꾸나 | 도구 | 식당으로 |
|---|---|---|---|
| **수평** | Pod **개수** | HPA, Knative, KEDA | 요리사를 더 고용 |
| **수직** | Pod 하나의 **CPU/메모리** | VPA | 요리사 한 명에게 더 큰 주방 |
| **클러스터** | **노드** 개수 | CA | 식당 건물을 넓힘 |

수평이 기본이고 수직은 예외다. 수평은 "똑같은 거 하나 더"라 기존 Pod를 건드리지 않지만, 수직은 "있는 걸 고치기"라 **Pod를 죽였다 살려야** 한다. 상태 없는 웹 서버는 옆 Pod가 받아주니 괜찮지만, DB처럼 하나뿐인 것은 재시작이 곧 다운타임이다.

그리고 여기서 개발자가 자주 빠지는 함정 — **셋을 따로 배우면 각각은 쉬운데, 같이 돌리면 어렵다.** 공유 클러스터에서 내 서비스가 자동으로 확 늘어나면 옆 팀이 쓸 자리가 없어진다. 책이 "종이 위에서는 간단해 보이지만 상당한 시행착오가 필요하다"고 못 박는 이유다.

### 2.3 안티프래질 — 부하를 먹고 커지는 시스템

책이 이 장 첫 부분에 꺼내고 마지막에 다시 가져오는 단어가 **antifragile**이다.

```
취약(fragile)      충격을 받으면 깨진다          유리잔
튼튼(robust)       충격을 받아도 버틴다          돌
안티프래질         충격을 받으면 더 강해진다     운동으로 단련되는 근육
```

앞 장들까지의 Kubernetes는 두 번째였다. Pod가 죽으면 다시 띄우고, 노드가 죽으면 다른 노드에서 살린다 — **안 무너지기**. 이 장은 세 번째를 만든다. 트래픽이 몰리면 Pod가 늘고 노드가 늘어난다 — **부하를 먹고 커지기**.

즉 이 장의 목표는: **사람이 예측한 숫자가 아니라 실제 측정값에 반응해서, 개수·크기·서버 세 축으로 시스템이 스스로 커지고 작아지게 만드는 것.**

---

## 3. 수동 확장 — 사람이 숫자를 바꾼다

자동화 전에 수동을 먼저 보는 이유가 있다. 자동 확장은 **뒷북**이기 때문이다. CPU가 80%를 넘는 것을 *본 다음에* 늘리기 시작하니, 그 사이 몇 십 초는 이미 느려진 상태다. 반면 사람은 미래를 안다 — "금요일 밤 11시 세일 시작"을 알면 목요일에 미리 늘려둘 수 있다. 손님이 몰리기 전에 계산대를 미리 여는 것이다.

| | 자동 확장 | 수동 확장 |
|---|---|---|
| 반응 시점 | 부하가 오른 **후** | 부하가 오르기 **전**에 가능 |
| 적합한 상황 | 예측 불가능한 트래픽 | 예측 가능한 이벤트, 최적값 찾는 튜닝 단계 |

### 3.1 명령형 — 빠르지만 파일에 남지 않는다

ReplicaSet은 "Pod가 N개여야 해"라는 숫자를 항상 지켜보는 감시자다. 그러니 사람이 할 일은 그 숫자 하나를 바꾸는 것뿐이다.

```bash
kubectl scale deployment random-generator --replicas=4
```

책의 예제는 `deployment`가 빠진 `kubectl scale random-generator --replicas=4`로 적혀 있는데, 실제로는 리소스 종류를 명시해야 동작한다.

빠르고 직관적이지만 **파일에 남지 않는다.** 원래 YAML에는 여전히 `replicas: 2`라고 적혀 있다.

### 3.2 선언형 — 파일이 진실이다

명령형이 만드는 사고에는 이름이 있다 — **설정 드리프트(configuration drift).**

```
1. Git 에 replicas: 2 라고 적힌 YAML 이 있음
2. 트래픽 몰려서 kubectl scale --replicas=4          → 클러스터는 4개
3. 며칠 뒤 동료가 YAML 을 조금 고치고 kubectl apply   → 다시 2개로 돌아감
4. 갑자기 느려지는데 아무도 이유를 모름
```

"파일에 적힌 것"과 "실제 돌아가는 것"이 어긋난 상태다. 해법은 YAML의 `replicas`를 고쳐서 `kubectl apply`하는 것 — 그러면 클러스터도 4, Git도 4, 히스토리에 누가 언제 왜 바꿨는지도 남는다.

책이 말하는 **역반영(backporting)**은 운영 규칙이다. 급하면 `scale`로 먼저 하되, 상황이 정리되면 **반드시 YAML에도 따라 적어 커밋**하라는 것. 26장에서 RBAC가 파일이 아니라 리소스라서 GitOps에 올라탈 수 있었던 것과 같은 자리 — 여기서도 진실은 Git에 있어야 한다.

### 3.3 리소스마다 다르다 — StatefulSet 의 비대칭과 Job 의 parallelism

확장할 수 있는 리소스는 Deployment, ReplicaSet, StatefulSet, Job인데 두 개가 조금 다르게 행동한다.

**StatefulSet은 늘릴 땐 만들고, 줄일 땐 안 지운다.** 12장에서 본 대로 각 Pod가 자기 전용 디스크(PVC)를 갖는다.

```
3 → 5   Pod 2개 + 디스크 2개 새로 생김
5 → 3   Pod 2개는 사라지지만 디스크 2개는 그대로 남음
```

디스크를 같이 지우면 데이터가 날아가기 때문이다. 다시 5개로 늘리면 남아 있던 디스크가 그대로 다시 붙는다. 다만 안 쓰는 디스크도 비용이 나가니 정말 필요 없으면 수동으로 지워야 한다.

**Job은 이름만 다르다.** 7장의 Job은 "계속 도는 서비스"가 아니라 "일 끝내면 종료되는 작업"이라 복제본이라는 말 대신 **동시 실행 수**라고 부른다.

```yaml
spec:
  parallelism: 4      # replicas 가 아니라 이것
```

이름은 다르지만 뜻은 같다 — 일꾼을 늘려서 처리량을 키운다. 이미지 1만 장 변환을 1개로 돌리면 10시간, 4개로 돌리면 2.5시간.

| 리소스 | 확장 필드 | 축소 시 특이점 |
|---|---|---|
| Deployment / ReplicaSet | `replicas` | 없음 |
| StatefulSet | `replicas` | PVC는 남김 |
| Job | `parallelism` | 작업 완료 시 종료 |

---

## 4. HPA — 판단은 내장, 숫자는 설치

명령형이든 선언형이든 사람이 세 단계를 해야 한다 — 부하가 변하는 걸 **알아채고**, 몇 개로 늘릴지 **판단하고**, 명령을 **실행**. 지금까지는 실행만 쉬웠다. HPA는 앞의 둘까지 Kubernetes에 맡긴다.

### 4.1 정의 하나 — 울타리와 목표

```bash
kubectl autoscale deployment random-generator --cpu-percent=50 --min=1 --max=5
```

이 한 줄이 아래 YAML을 만든다.

```yaml
# Example 29-4. HPA 정의
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: random-generator
spec:
  minReplicas: 1                  # ❶ 아무리 한가해도 1개는 유지
  maxReplicas: 5                  # ❷ 아무리 바빠도 5개까지만
  scaleTargetRef:                 # ❸ 조절할 대상
    apiVersion: apps/v1
    kind: Deployment
    name: random-generator
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50    # ❹ 목표 CPU 사용률
```

❶❷는 울타리다. min은 갑자기 트래픽이 왔을 때 0에서 시작하는 것보다 1개라도 있어야 바로 응답할 수 있어서, max는 버그나 공격으로 Pod가 무한히 늘어나 클러스터를 잡아먹는 걸 막는 **비용 안전장치**다.

❸에서 **HPA는 ReplicaSet이 아니라 Deployment에 붙여야 한다.** Deployment는 배포할 때마다 새 ReplicaSet을 만들고 옛것을 비운다.

```
Deployment
   ├── ReplicaSet v1 (이미지 1.0)  ← Pod 0개로 줄어듦     ← HPA 를 여기 붙였다면?
   └── ReplicaSet v2 (이미지 2.0)  ← Pod 3개 새로 생김     ← HPA 가 없다
```

HPA를 ReplicaSet v1에 붙여뒀다면 배포 한 번에 자동 확장이 조용히 꺼진다. 회사 정책을 "이번 분기 TF팀"에 걸어두면 TF가 해체될 때 정책도 사라지는 것과 같다 — **부서에 걸어야** TF가 바뀌어도 유지된다.

HPA는 `/scale` 서브리소스가 있는 리소스에만 붙는다. Deployment, ReplicaSet, StatefulSet은 되고 단일 Pod나 DaemonSet은 안 된다. 그리고 **HPA 리소스 자체는 Kubernetes 코어에 내장**되어 있다 — `kubectl api-resources | grep autoscal`에 아무것도 안 깔아도 나온다. 이 장에서 내장인 것은 이것 하나뿐이라는 점을 미리 적어둔다.

### 4.2 숫자는 어디서 오나 — kubelet 에서 API 자리까지

HPA가 "지금 CPU 75%"라는 숫자를 얻기까지의 길은 생각보다 길고, **어디까지가 내장이고 어디부터 설치인지**가 실무에서 자주 헷갈린다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 340" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HPA 지표 파이프라인: 각 노드의 kubelet 이 측정하고, metrics-server 가 모아서 API 자리에 내놓고, HPA 가 읽어서 replicas 를 고친다">
  <defs>
    <marker id="hp-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <!-- kubelets -->
  <g>
    <rect x="20" y="30" width="130" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
    <text x="85" y="50" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">kubelet (노드1)</text>
    <text x="85" y="68" text-anchor="middle" font-size="11" fill="#1b3f63">cAdvisor 측정</text>
    <rect x="20" y="100" width="130" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
    <text x="85" y="120" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">kubelet (노드2)</text>
    <text x="85" y="138" text-anchor="middle" font-size="11" fill="#1b3f63">cAdvisor 측정</text>
    <rect x="20" y="170" width="130" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
    <text x="85" y="190" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">kubelet (노드3)</text>
    <text x="85" y="208" text-anchor="middle" font-size="11" fill="#1b3f63">cAdvisor 측정</text>
  </g>
  <text x="85" y="244" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">내장 — 항상 재고 있다</text>

  <!-- metrics-server -->
  <rect x="220" y="100" width="140" height="50" rx="4" fill="#f7e08a" stroke="#c9a92c"/>
  <text x="290" y="120" text-anchor="middle" font-size="12" font-weight="600" fill="#5a4a10">metrics-server</text>
  <text x="290" y="138" text-anchor="middle" font-size="11" fill="#5a4a10">모아서 노출 · Pod 1개</text>
  <text x="290" y="244" text-anchor="middle" font-size="11.5" font-style="italic" fill="#c0392b">설치 — 없으면 HPA 가 안 돈다</text>

  <!-- API server slot -->
  <rect x="420" y="80" width="130" height="90" rx="4" fill="none" stroke="var(--content,#444)" stroke-width="2"/>
  <text x="485" y="102" text-anchor="middle" font-size="12" font-weight="600" fill="var(--content,#333)">kube-apiserver</text>
  <rect x="432" y="112" width="106" height="46" rx="3" fill="#e9f2fa" stroke="#2f6ea8"/>
  <text x="485" y="130" text-anchor="middle" font-size="10.5" fill="#12324f">metrics.k8s.io</text>
  <text x="485" y="146" text-anchor="middle" font-size="10.5" fill="#12324f">APIService 자리</text>
  <text x="485" y="244" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">자리(이름)는 내장, 채우는 건 설치</text>

  <!-- HPA -->
  <rect x="610" y="100" width="130" height="50" rx="4" fill="#5b9bd5"/>
  <text x="675" y="120" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">HPA 컨트롤러</text>
  <text x="675" y="138" text-anchor="middle" font-size="11" fill="#eaf3fb">15초마다 계산</text>
  <text x="675" y="244" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">내장</text>

  <!-- Deployment -->
  <rect x="610" y="270" width="130" height="50" rx="4" fill="#4caf82"/>
  <text x="675" y="290" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">Deployment</text>
  <text x="675" y="308" text-anchor="middle" font-size="11" fill="#e9f7f1">replicas 수정</text>

  <g stroke="var(--content,#444)" stroke-width="1.8" fill="none" marker-end="url(#hp-ar)">
    <path d="M150,55 L216,110"/>
    <path d="M150,125 H216"/>
    <path d="M150,195 L216,140"/>
    <path d="M360,125 H428"/>
    <path d="M538,125 H606"/>
    <path d="M675,150 V266"/>
  </g>
  <text x="690" y="212" text-anchor="start" font-size="11" font-style="italic" fill="var(--content,#333)">replicas: 3 → 6</text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  측정은 내장, 수집기는 설치, 판단은 내장 — 가운데 한 칸만 사람이 깔아야 한다
</div>
</div>
{{< /rawhtml >}}

| 단계 | 누가 | 내장? |
|---|---|---|
| 컨테이너 사용량 **측정** | kubelet 안의 cAdvisor | ✅ 노드마다 있다 |
| 노드별 값을 **모아 API로 노출** | metrics-server | ❌ 클러스터에 1개 설치 |
| API 그룹 **이름과 위임 메커니즘** | `metrics.k8s.io`, APIService | ✅ 내장 |
| 그 API를 **읽어서 판단** | HPA 컨트롤러 | ✅ 내장 |

**측정 자체는 이미 되고 있다.** Kubernetes를 설치한 순간부터 모든 노드의 kubelet이 자기 노드 컨테이너의 CPU·메모리를 재고 있다. 앱마다 뭘 만들 필요가 없다. 없는 것은 **흩어진 값을 한곳에 모아주는 Pod 하나**뿐이고, 그게 metrics-server다.

metrics-server가 "기본 제공"처럼 느껴지는 건 GKE·AKS 같은 관리형 클러스터가 미리 깔아주기 때문이다. EKS, minikube, kubeadm은 직접 깔아야 한다. 확인은 간단하다.

```bash
kubectl top pods              # 값이 나오면 있는 것
# error: Metrics API not available   → 없는 것
```

**등록은 APIService 리소스로 한다.** "이 API 경로로 오는 요청은 저 Service에게 넘겨라"고 API 서버에 알려주는 것이다.

```yaml
apiVersion: apiregistration.k8s.io/v1
kind: APIService
metadata:
  name: v1beta1.metrics.k8s.io          # <버전>.<그룹> — 이 이름은 고정
spec:
  group: metrics.k8s.io
  version: v1beta1
  service:                              # 그냥 Kubernetes Service (ClusterIP)
    name: metrics-server
    namespace: kube-system
    port: 443
```

여기서 `service`는 **일반 Kubernetes Service 리소스**이고 타입은 ClusterIP다. 외부 IP가 아니다. API 서버가 클러스터 내부에서 그 Service로 프록시하고, 뒤의 Pod가 실제 값을 만든다. Pod IP는 재시작하면 바뀌지만 Service 이름은 고정이라 이 구조가 필요한 것이다 — 일반 앱 간 통신에서 Service를 쓰는 이유와 같다.

보통 이 YAML을 손으로 쓰지 않는다. `kubectl apply -f components.yaml`이나 Helm으로 설치하면 Deployment + Service + APIService가 한꺼번에 딸려온다.

### 4.3 세 종류의 지표, 그룹마다 하나뿐인 자리

지표는 셋이고, 셋 다 4.2와 **완전히 같은 구조**로 공급된다. 바뀌는 건 어댑터 Pod가 어디 가서 값을 가져오느냐뿐이다.

```
kube-apiserver ──▶ Service(ClusterIP) ──▶ 어댑터 Pod ──▶ 실제 데이터 소스
                                                        (kubelet / Prometheus / AWS ...)
```

| 종류 | `type` | 예 | API 그룹 | 공급자 |
|---|---|---|---|---|
| 표준 | `Resource` | CPU, 메모리 | `metrics.k8s.io` | metrics-server |
| 커스텀 | `Pods`, `Object` | 초당 요청 수, Ingress 총 요청 | `custom.metrics.k8s.io` | Prometheus Adapter 등 |
| 외부 | `External` | 클라우드 큐 길이 | `external.metrics.k8s.io` | KEDA, 클라우드 어댑터 |

표준 지표가 "가장 쓰기 쉽다"고 책이 말하는 이유가 여기 있다. `cpu`, `memory`라는 이름은 어떤 클러스터에서든 똑같고 metrics-server 하나면 끝난다. 커스텀은 "초당 요청 수"처럼 **앱만 아는 숫자**라 앱이 `/metrics`로 노출하고, Prometheus가 긁고, 어댑터가 변환하는 파이프라인을 직접 깔아야 한다. 외부는 아예 클러스터 밖(AWS SQS, Kafka)의 값이라 인증까지 붙는다.

```
표준:   설치 → 설정 거의 없음
커스텀: 설치 → 쿼리 매핑 설정 필요
외부:   설치 → 인증 + 소스 설정 필요
```

**그리고 이 절의 가장 중요한 제약** — APIService는 이름으로 식별되니, **그룹마다 어댑터를 하나만** 붙일 수 있다.

```bash
kubectl apply -f aws-adapter-apiservice.yaml     # 이미 KEDA 가 external 자리를 점유 중
```

에러가 나지 않는다. **덮어써진다.** 나중 것이 이기고 먼저 있던 KEDA 연결이 조용히 끊긴다. 26장 3.2에서 "인증 방식을 여러 개 켜면 하나만 성공해도 통과"였던 것과 정반대의 위험 — 여기서는 하나만 살아남는다. AWS 어댑터와 GCP 어댑터를 동시에 쓰고 싶으면 불가능하고, 그래서 KEDA 같은 **중개자**가 필요해진다(5.3).

```bash
kubectl get apiservice | grep metrics
v1beta1.metrics.k8s.io           kube-system/metrics-server              True
v1beta1.custom.metrics.k8s.io    monitoring/prometheus-adapter           True
v1beta1.external.metrics.k8s.io  keda/keda-operator-metrics-apiserver    True
```

### 4.4 분자와 분모 — requests 가 기준이다

HPA가 "50%"라는 퍼센트를 만들려면 숫자 두 개가 필요하다.

```
              실제로 쓰고 있는 양     ← metrics-server 가 재서 줌 (분자)
사용률 = ─────────────────────────
              requests 에 적은 양     ← Pod spec 에 이미 있음 (분모)
```

| | 어디서 오나 | 성격 |
|---|---|---|
| 분자 — 실제 사용량 (지금 150m) | metrics-server | 측정값, 매초 변함 |
| 분모 — requests (200m) | Pod spec, API 서버에 저장됨 | 선언값, 내가 YAML에 적은 것 |

metrics-server는 **분자만** 준다. 분모는 2장 "Predictable Demands"에서 적은 requests를 그냥 읽는다. 그래서 **둘 중 하나만 없어도 HPA가 안 돈다** — metrics-server가 없으면 분자가 없고, requests가 없으면 분모가 없다.

여기서 헷갈리기 쉬운 것 — **기준은 `limits`가 아니라 `requests`다.**

```
requests 100m, limits 500m 인 Pod 가 300m 쓰고 있다면
  HPA 눈에는   300%  (100m 기준)
  limits 대비는  60%
```

limits 대비로는 여유가 있는데 HPA는 "엄청 바쁘다"고 판단해 늘린다. 즉 **requests 값 자체가 HPA 동작을 좌우한다.** requests를 감으로 낮게 적으면 HPA가 과민 반응하고, 높게 적으면 둔감해진다. 이 문제의 답이 뒤에 나올 VPA다(6.1).

### 4.5 지표 선택 — Pod 를 늘리면 내려가는가

책이 "가장 중요한 결정"이라고 부르는 것이 지표 선택이다. HPA의 계산식은 이런 믿음 위에 서 있다.

```
"Pod 를 2배로 늘리면 → 지표가 절반으로 내려갈 것이다"
```

이 믿음이 깨지면 HPA는 엉뚱한 짓을 한다. 그러니 판단 기준은 하나다 — **Pod를 늘리면 그 숫자가 내려가는가?**

```
초당 요청 1000건
  Pod 2개 → Pod 당 500건
  Pod 4개 → Pod 당 250건     ✓ 내려간다. 로드밸런서가 나눠주니까

메모리
  Pod 2개 → 각각 800MB (JVM 힙 + 캐시)
  Pod 4개 → 각각 800MB       ✗ 안 내려간다. 자기 몫이니까
```

요청은 나눠 갖는 성질이지만 메모리는 Pod 하나가 혼자 쓰는 고정 비용이다. 옆에 Pod가 몇 개 생기든 자기 800MB는 그대로다. 그러면 무슨 일이 벌어지나.

```
1. HPA: "메모리 80%네, 목표 50%니까 늘리자"  → 3개
2. 15초 뒤: "여전히 80%? 더 늘리자"          → 5개
3. 15초 뒤: "아직도 80%?!"                   → 8개
4. ... maxReplicas 도달할 때까지
```

돈은 돈대로 쓰고 사용률은 1도 안 내려가고, 결국 상한에 걸려 멈춘다. **Pod를 아무리 늘려도 내려가지 않는 숫자를 내리겠다고 애쓰는 것**이다.

| 지표 | Pod 늘리면 내려가나 | HPA 적합? |
|---|---|---|
| 초당 요청 수 | ✓ | 매우 좋음 |
| CPU | ✓ (요청 처리에 쓰니까) | 좋음, 기본 선택 |
| 큐 길이 | ✓ (소비자가 늘면 빨리 빠짐) | 좋음 |
| 메모리 | ✗ (대부분) | **피할 것** |

메모리가 문제라면 HPA가 아니라 VPA나 앱 튜닝이 답이다. 지표가 여러 개면 각각 따로 계산해서 **가장 큰 값**을 택한다 — 어느 하나라도 한계에 걸리면 안 되니, 가장 많이 필요하다는 쪽을 따른다.

### 4.6 공식은 비례식, 나머지는 안전장치

계산은 비례식 하나다.

$$\text{원하는 개수} = \left\lceil \text{현재 개수} \times \frac{\text{현재 사용률}}{\text{목표 사용률}} \right\rceil$$

```
Pod 1개, CPU 90%, 목표 50%   →  1 × (90/50) = 1.8  →  올림해서 2개
Pod 4개, CPU 25%, 목표 50%   →  4 × (25/50) = 2    →  2개로 줄임
```

"부하가 목표의 몇 배인가"를 구해서 Pod 개수에 곱한다. 소수점은 올림 — 부족한 것보다 남는 게 안전하니까.

HPA는 계산 결과 숫자 하나를 Deployment의 `replicas`에 **써넣기만** 한다. 직접 Pod를 만들지 않는다. 그 뒤는 Deployment → ReplicaSet → 스케줄러의 기존 흐름 그대로다. 사람이 `kubectl scale`로 하던 일을 HPA가 대신 치는 것뿐이고, 그 아래 메커니즘은 동일하다.

책이 "단순화한 공식"이라고 한 이유는 그 위에 안전장치가 얹히기 때문이다. 이름은 **스래싱(thrashing)** 또는 플래핑 — 3 → 5 → 3 → 5를 15초마다 반복하는 나쁜 상태를 막는 것이다.

```
늘릴 때   갓 뜬 Pod 의 CPU 는 안 믿는다
          Java·Node 는 시작할 때 몇십 초간 CPU 100% 를 찍는다. 그걸 넣으면
          "새 Pod 가 바쁘네 → 더 늘려 → 그것도 바쁘네 → 더" 의 폭주가 된다

줄일 때   최근 5분간 계산 결과 중 최댓값을 따른다
          70% 72% 30% 68% ... 에서 30% 순간에 줄이면 15초 뒤 다시 늘려야 한다
          5분 내내 "3개면 충분" 이 나와야 비로소 3개로 줄어든다
```

왜 줄일 때만 이렇게 보수적인가 — 늘리는 게 늦으면 서비스가 느려지고(사용자가 바로 느낀다), 줄이는 게 늦으면 돈이 조금 더 나간다(5분어치). **늘릴 땐 빨리, 줄일 땐 천천히**가 의도된 비대칭이다.

이 안전장치는 `.spec.behavior`로 조절한다. 손잡이는 둘이다.

```yaml
# Example 29-5. 축소는 5분 지켜본 뒤 1분에 10% 씩, 확장은 15초에 4개씩
spec:
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300    # 얼마나 참고 — 5분
      policies:
      - type: Percent
        value: 10                        # 얼마나 빨리 — 현재의 10%
        periodSeconds: 60                #             1분마다
    scaleUp:
      policies:
      - type: Pods
        value: 4                         # 15초에 4개씩
        periodSeconds: 15
```

| | 질문 | 비유 |
|---|---|---|
| `stabilizationWindowSeconds` | 결정하기 전에 **얼마나 지켜보나** | 대기 시간 |
| `policies` | 한 번에 **몇 개까지** 바꿀 수 있나 | 속도 제한 |

이 설정으로 Pod 20개가 5개까지 내려오려면 약 15분, 2개가 20개까지 올라가려면 1분이다. `scaleDown.selectPolicy: Disabled`로 축소 자체를 끌 수도 있다.

**책의 오류 하나** — "모든 behavior 매개변수를 `kubectl autoscale`로도 설정할 수 있다"고 적혀 있는데, 실제 `kubectl autoscale`은 `--min`, `--max`, `--cpu-percent`만 지원한다. behavior를 쓰려면 YAML로 작성해 `apply`해야 한다.

지연은 어쩔 수 없이 쌓인다. cAdvisor 주기 + metrics-server 주기 + HPA 주기 + 안정화 창 + 새 Pod가 뜨는 시간. 보통 1~3분이고, 주기를 줄이면 API 서버 부하와 스래싱이 늘어난다. 현실적인 대응은 주기가 아니라 **④→⑤ 구간**(이미지 크기, 앱 시작 시간, readiness probe)을 줄이고, 목표치를 낮게 잡아 여유분을 두고, 예측 가능한 이벤트는 3장의 수동 사전 확장으로 처리하는 것이다.

---

## 5. Scale to Zero — 0 에서 깨우는 일은 누가 하나

HPA는 강력하지만 한 가지를 못 한다 — **아무도 안 쓸 때 Pod를 0개로 줄이는 것.** 밤에 아무도 안 쓰는 내부 도구, 한 달에 한 번 쓰는 리포트 생성기가 Pod 1개씩 계속 떠 있으면 비용이 계속 나간다.

### 5.1 HPA 는 왜 0 에서 못 깨어나나

0으로 줄이는 것 자체는 어렵지 않다. 까다로운 건 **0에서 다시 깨우는 것**이다.

```
HPA 는 Pod 의 CPU 를 보고 판단한다.
Pod 가 0개면 볼 CPU 가 없다.
Pod 0개 → 요청 들어옴 → 받을 Pod 가 없어서 실패 → CPU 도 0 → HPA 는 조용함
```

Pod가 없으면 "바쁘다"는 신호를 영영 받을 수 없다. 그래서 HPA는 애초에 0으로 안 내려간다.

해법은 하나다 — **Pod가 아니라 Pod 앞쪽을 지켜보는 무언가**를 두는 것. HTTP 요청이 오면 잠깐 붙잡아두고 Pod를 띄운 뒤 넘겨주거나(Knative), 큐에 메시지가 쌓이는 걸 보고 Pod를 띄운다(KEDA).

책이 강조하는 것 — **둘은 대체재가 아니라 보완재다.** 트리거가 뭐냐에 따라 쓰는 게 다르다.

| | Knative | KEDA |
|---|---|---|
| 깨우는 신호 | **HTTP 요청** | **외부 이벤트** (큐, DB, cron) |
| 적합한 앱 | 웹 API, 함수 | 메시지 소비자, 배치 |
| 같이 쓰는 예 | 사용자 API | 주문 처리 워커 |

### 5.2 Knative — 문지기, 카운터, 결정권자

Knative는 세 조각(Serving, Eventing, Functions)짜리 애드온이고 이 장에서 중요한 건 **Serving**뿐이다. 일반 Kubernetes에서 웹 앱 하나 띄우려면 Deployment + Service + Ingress + HPA 넷을 써야 하는데, Knative Serving은 이걸 리소스 하나로 줄인다.

```yaml
# Example 29-6. Knative Service
apiVersion: serving.knative.dev/v1        # ❶ 코어 Service 와 이름만 같은 다른 리소스
kind: Service
metadata:
  name: random
  annotations:
    autoscaling.knative.dev/target: "80"   # ❷ Pod 당 동시 요청 80개
    autoscaling.knative.dev/window: "120s" # ❸ 최근 2분 평균으로 판단
spec:
  template:
    spec:
      containers:
      - image: k8spatterns/random          # ❹ 유일한 필수 항목
```

❶ **`kind: Service`지만 코어 Service가 아니다.** `apiVersion`이 `serving.knative.dev/v1`이고, 설치해야 생긴다. 헷갈려서 보통 **ksvc**라고 부른다. 이걸 만들면 그 안에서 코어 Service, Deployment, Ingress가 자동 생성되고 외부 접속 URL(`http://random.default.example.com`)까지 생긴다 — Knative Service는 코어 Service를 **포함하는 상위 개념**이다.

❷ Knative는 CPU를 보지 않는다. **동시 요청 수** — 지금 이 Pod가 병렬로 처리 중인 요청 수 — 를 본다.

| 지표 | 식당으로 | 문제 |
|---|---|---|
| CPU | 요리사가 얼마나 땀 흘리나 | 외부 API 기다리는 동안은 땀 안 흘림. 실제론 바쁜데 한가해 보임 |
| rps | 1초에 손님 몇 명 들어오나 | 라면 손님 10명과 코스 손님 10명이 같아 보임 |
| **동시 요청** | 지금 **테이블에 앉아 있는** 손님 수 | — |

테이블에 앉아 있는 손님 수 = (들어오는 속도) × (머무는 시간). rps에 없던 "요청 하나가 얼마나 오래 걸리나"가 자동으로 들어간다. 느린 요청이 많으면 동시 요청이 쌓이니 늘려야 한다는 걸 정확히 잡는다.

**Knative는 HPA를 버렸다.** 처음엔 커스텀 지표 어댑터로 만들어 HPA가 판단하게 했지만, 4.3의 "그룹마다 자리 하나" 제약에 걸렸다 — Knative가 그 자리를 차지하면 사용자는 Prometheus Adapter를 못 붙인다. 게다가 0에서 깨우기, 요청 붙잡아두기는 HPA 공식으로 불가능하다. 그래서 숫자 공급도 판단도 **전부 자기가 하는** 자체 컨트롤러를 만들었다. 이름은 **KPA(Knative Pod Autoscaler)**다.

```
HPA 방식:   지표 어댑터 → API 자리 하나 → HPA → replicas
KPA 방식:   Knative 가 직접 측정 → KPA → replicas         API 자리 안 씀
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 330" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Knative Pod Autoscaler: Activator 가 요청을 받아 Pod 로 넘기고, Queue-proxy 가 동시 요청을 세고, 둘의 보고를 받은 Autoscaler 가 replicas 를 정한다">
  <defs>
    <marker id="kn-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <text x="20" y="72" font-size="12.5" font-weight="600" fill="var(--content,#333)">HTTP 요청</text>

  <!-- Activator -->
  <rect x="140" y="40" width="130" height="56" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="205" y="62" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Activator</text>
  <text x="205" y="82" text-anchor="middle" font-size="11" fill="#5a3d18">문지기 · Pod 밖 · 항상</text>

  <!-- Deployment -->
  <rect x="140" y="140" width="330" height="170" rx="6" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="305" y="162" text-anchor="middle" font-size="13" font-weight="600" fill="#1e4b38">Deployment</text>
  <rect x="380" y="150" width="80" height="24" rx="3" fill="#2e9c6d"/>
  <text x="420" y="167" text-anchor="middle" font-size="11" font-weight="600" fill="#fff">replicas=3</text>

  <!-- Pod -->
  <rect x="160" y="180" width="200" height="118" rx="5" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="260" y="198" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">Pod</text>
  <rect x="176" y="208" width="168" height="34" rx="3" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="260" y="224" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">Queue-proxy (카운터)</text>
  <text x="260" y="236" text-anchor="middle" font-size="10" fill="#5a3d18">사이드카 · 동시 요청 셈</text>
  <rect x="176" y="254" width="168" height="34" rx="3" fill="#fff" stroke="#2f6ea8"/>
  <text x="260" y="276" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1b3f63">App-container</text>
  <!-- ghost pods -->
  <rect x="370" y="190" width="12" height="100" rx="3" fill="#cfe3f5" stroke="#2f6ea8"/>
  <rect x="386" y="200" width="12" height="90" rx="3" fill="#cfe3f5" stroke="#2f6ea8"/>

  <!-- Autoscaler -->
  <rect x="580" y="140" width="150" height="56" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="655" y="162" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Autoscaler</text>
  <text x="655" y="182" text-anchor="middle" font-size="11" fill="#5a3d18">결정권자</text>

  <g stroke="var(--content,#444)" stroke-width="1.8" fill="none" marker-end="url(#kn-ar)">
    <path d="M90,68 H136"/>
    <path d="M205,96 V176"/>
    <path d="M260,242 V250"/>
    <path d="M270,68 H655 V136"/>
    <path d="M344,225 H655 V200"/>
    <path d="M580,168 H464"/>
  </g>
  <g font-size="11" font-style="italic" fill="var(--content,#333)">
    <text x="215" y="140" text-anchor="start">요청 전달</text>
    <text x="460" y="60" text-anchor="middle">"요청 왔어" (푸시)</text>
    <text x="470" y="240" text-anchor="middle">"동시 요청 N개" (푸시)</text>
    <text x="522" y="160" text-anchor="middle">controls</text>
  </g>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  KPA — 문지기와 카운터가 숫자를 보고하면 결정권자가 Pod 개수를 정한다
</div>
</div>
{{< /rawhtml >}}

| 컴포넌트 | 어디에 | 살아있는 때 | 역할 |
|---|---|---|---|
| Activator (문지기) | Pod **밖**, 클러스터에 1개 | 항상 | Pod 0개일 때 요청을 **붙잡아둔다** |
| Queue-proxy (카운터) | Pod **안**, 사이드카 | Pod가 있을 때만 | 요청이 지나갈 때 **개수를 센다** |
| Autoscaler (결정권자) | 별도 Pod | 항상 | 보고받은 숫자로 **replicas를 정한다** |

문지기와 카운터의 차이는 **Pod가 0개일 때 존재하느냐**다. Queue-proxy는 Pod 안에 있으니 Pod가 없으면 같이 사라진다. Activator는 밖에 따로 있으니 살아 있다. 그래서 0에서 깨어나는 순서가 이렇게 된다.

```
1. Pod 0개. 요청 도착
2. Activator 가 받음 (Pod 없어도 얘는 있다)
3. Activator → Autoscaler: "요청 왔어"
4. Autoscaler → replicas: 1
5. Pod 뜨는 동안 Activator 가 요청을 계속 들고 있음 — 유실 없음
6. Pod 준비되면 넘겨줌
```

Pod가 있고 여유가 있으면 Activator는 경로에서 빠지고 요청이 Pod로 직접 간다. 다시 끼어드는 건 Pod가 전부 꽉 찼을 때다. `target-burst-capacity: "-1"`로 항상 끼워둘 수도 있지만 홉이 하나 늘어 약간 느려진다.

Queue-proxy는 18장의 앰배서더 사이드카다. 개발자가 적은 적 없는 컨테이너가 Pod에 들어가 있는 이유 — 26장 3.4에서 봤던 Mutating 어드미션이 여기서도 일한다.

**Knative에는 scaler 같은 플러그인이 없다.** 지표 소스가 항상 자기가 세는 HTTP 요청이라 외부에 물어볼 필요가 없다. Kafka 메시지로 깨우고 싶으면 Knative **Eventing**이 Kafka 메시지를 HTTP 요청으로 바꿔 Serving에 쏜다 — "전부 HTTP로 만들어서 HTTP 하나만 잘 다루자"는 방식이다.

튜닝은 annotation 몇 개면 된다. 진짜 자주 쓰는 건 셋이다.

| annotation | 뜻 | HPA 대응 |
|---|---|---|
| `target` | Pod 하나가 동시에 몇 명 받을까 | `averageUtilization` (단위만 다름) |
| `min-scale` | `"1"`이면 0으로 안 내려감 — 콜드 스타트 없음 | `minReplicas` |
| `max-scale` | 비용 안전장치 | `maxReplicas` |

### 5.3 KEDA — HPA 를 버리지 않고 반만 직접

KEDA는 Knative와 정반대 선택을 했다 — **HPA를 그대로 쓴다.** 4.3의 `external.metrics.k8s.io` 자리에 자기를 등록하고 숫자를 공급하는 어댑터 역할을 하되, 그 뒤에서 수십 가지 소스를 한데 모은다.

```
Kubernetes API ── 창구 1개 ── KEDA ─┬─ AWS SQS
                                    ├─ Kafka
                                    ├─ Redis
                                    └─ ... 70+ scaler
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 340" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="KEDA 구조: ScaledObject 를 읽은 Operator 가 HPA 를 대신 만들고, 0에서 1 구간은 Operator 가 직접 처리하며 1에서 n 구간은 HPA 가 KEDA 지표를 읽어 조정한다">
  <defs>
    <marker id="kd-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="20" y="46" width="150" height="52" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="95" y="68" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">ScaledObject</text>
  <text x="95" y="86" text-anchor="middle" font-size="10.5" fill="#5a3d18">사용자가 쓰는 유일한 것</text>

  <rect x="250" y="36" width="150" height="72" rx="4" fill="#4caf82"/>
  <text x="325" y="62" text-anchor="middle" font-size="13" font-weight="600" fill="#fff">KEDA Operator</text>
  <text x="325" y="82" text-anchor="middle" font-size="10.5" fill="#e9f7f1">HPA 를 대신 만든다</text>
  <text x="325" y="97" text-anchor="middle" font-size="10.5" fill="#e9f7f1">0↔1 은 직접 조정</text>

  <rect x="250" y="176" width="150" height="60" rx="4" fill="#5b9bd5"/>
  <text x="325" y="200" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">keda-hpa-…</text>
  <text x="325" y="219" text-anchor="middle" font-size="10.5" fill="#eaf3fb">1↔n 은 HPA 가</text>

  <rect x="250" y="272" width="150" height="46" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="325" y="300" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">Deployment</text>

  <rect x="470" y="176" width="170" height="60" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="555" y="200" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">external.metrics</text>
  <text x="555" y="219" text-anchor="middle" font-size="10.5" fill="#1b3f63">.k8s.io — 창구 1개</text>

  <rect x="640" y="36" width="100" height="108" rx="4" fill="#c0392b"/>
  <text x="690" y="60" text-anchor="middle" font-size="11.5" font-weight="600" fill="#fff">SQS</text>
  <text x="690" y="82" text-anchor="middle" font-size="11.5" font-weight="600" fill="#fff">Kafka</text>
  <text x="690" y="104" text-anchor="middle" font-size="11.5" font-weight="600" fill="#fff">Redis</text>
  <text x="690" y="128" text-anchor="middle" font-size="10.5" fill="#f6d5d1">70+ scaler</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#kd-ar)">
    <path d="M170,72 H246"/>
    <path d="M325,108 V172"/>
    <path d="M325,236 V268"/>
    <path d="M400,206 H466"/>
    <path d="M404,90 H636"/>
    <path d="M470,206 H406"/>
  </g>

  <g font-size="11" fill="var(--content,#333)" font-style="italic">
    <text x="208" y="62" text-anchor="middle">apply</text>
    <text x="368" y="146" text-anchor="middle">creates</text>
    <text x="368" y="260" text-anchor="middle">replicas</text>
    <text x="520" y="82" text-anchor="middle">poll (0↔1 판단)</text>
    <text x="433" y="196" text-anchor="middle">query</text>
  </g>

  <text x="380" y="332" text-anchor="middle" font-size="12" fill="var(--content,#333)">HPA 를 버리지 않고, HPA 가 못 하는 0↔1 구간만 직접 맡는다</text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  KEDA — 창구는 하나, 뒤에는 70여 개의 소스
</div>
</div>
{{< /rawhtml >}}

"창구는 하나지만 뒤에 여러 창구를 두는" 중개자다. 4.3의 제약을 이렇게 풀었다.

사용자는 `ScaledObject` 하나만 쓴다.

```yaml
# Example 29-7. ScaledObject
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: kafka-scaledobject
spec:
  scaleTargetRef:
    name: kafka-consumer            # ❶ 이 Deployment 를 (kind 생략 시 Deployment)
  pollingInterval: 30               # ❷ 0↔1 판단을 위해 30초마다 큐를 들여다봄
  triggers:
  - type: kafka                     # ❸ Kafka scaler 선택
    metadata:                       # ❹ 그 scaler 가 어디 접속할지
      bootstrapServers: bootstrap.kafka.svc:9092
      consumerGroup: my-group       #    "이 그룹이 아직 안 읽은 메시지" (lag) 기준
      topic: my-topic
```

`ScaledObject`가 생기면 KEDA Operator가 **HPA를 대신 만들어준다.**

```bash
kubectl get hpa
NAME                        REFERENCE                 TARGETS
keda-hpa-kafka-scaledobject Deployment/kafka-consumer 12/50 (avg)
```

`keda-hpa-` 접두어가 붙은 HPA를 직접 고치면 안 되고 `ScaledObject`를 고쳐야 한다. Deployment ↔ ReplicaSet 관계와 같다.

**"하이브리드"의 뜻** — KEDA는 구간을 둘로 나눈다.

```
큐 비어 있음 → Pod 0개                            (KEDA 가 0으로 내림)
      ↓ 메시지 들어옴
KEDA Operator: "임계값 넘었네" → replicas: 1       ← 0→1 은 KEDA 직접
      ↓ 메시지 계속 쌓임
HPA: KEDA 지표 보고 → replicas: 5                  ← 1→n 은 HPA
      ↓ 큐 줄어듦
HPA: → replicas: 1                                 ← n→1 은 HPA
      ↓ 큐 비어서 한동안 조용
KEDA Operator: → replicas: 0                       ← 1→0 은 KEDA 직접
```

HPA가 못 하는 구간(0↔1)만 직접 처리하고, 이미 잘 돌아가는 HPA를 나머지에 재활용한 것이다. `pollingInterval`이 "활성화 단계"에만 쓰이는 이유도 여기 있다 — Pod가 있을 때는 HPA가 자기 주기(15초)로 KEDA에 물어보지만, 0개일 때는 HPA가 놀고 있으니 KEDA Operator가 직접 30초마다 Kafka를 확인해야 한다.

| | Knative | KEDA |
|---|---|---|
| 0↔1 | 자체 (Activator) | 자체 (Operator) |
| 1↔n | 자체 (KPA) | **HPA** |
| 지표 공급 | 자체 | APIService 어댑터 |
| 소스 확장 | 없음 (HTTP 고정) | 70+ scaler, gRPC로 커스텀 가능 |

**ScaledJob**도 있다. Deployment의 `replicas` 대신 **Job의 개수**를 늘렸다 줄였다 한다. "메시지 하나 = 동영상 변환 10분" 같은 무거운 작업은 Pod가 계속 살아 있는 것보다 메시지당 Job 하나를 띄워 끝나면 사라지는 게 깔끔하고, 중간에 축소당해 작업이 끊길 위험도 없다. 7장의 Job이 `parallelism`을 수동으로 정해야 했던 것을, 여기서는 **Job 자체가 복제본 역할**을 하면서 자동으로 채운다.

2023년 기준 각주 — KEDA에도 HTTP 애드온이 있지만 Knative의 Activator만큼 성숙하지 않았다. 그래서 "HTTP는 Knative, 이벤트는 KEDA"로 나뉘는 것이다.

### 5.4 푸시와 풀 — 앱이 일하는 방식과 짝을 이룬다

숫자가 "보내지느냐" vs "가져와지느냐"의 차이다.

```
푸시  Activator/Queue-proxy ──"지금 동시 요청 12개!"──▶ Autoscaler
      알아서 보고한다. 요청을 받는 순간 바로 알려주니 즉시

풀    KEDA Operator ──"큐에 몇 개 있어?"──▶ Kafka
                    ◀──"47개"──
      물어봐야 대답한다. 30초마다
```

왜 나뉘나 — Kafka한테 "메시지 오면 KEDA에 알려줘"라고 시킬 수는 없다. 남의 시스템이다. Knative는 자기가 직접 요청을 받으니 즉시 알 수 있고, KEDA는 남의 시스템이라 직접 확인하러 가야 한다.

그리고 **앱이 일하는 방식과 확장기 방식이 짝을 이룬다.**

| 앱이 | 확장기도 | |
|---|---|---|
| 요청을 **받음** (웹 서버) | 푸시 | Knative |
| 일을 **가져옴** (큐 소비자) | 풀 | KEDA |

받는 앱은 앞에 문지기를 두면 되고, 가져오는 앱은 큐를 들여다보면 된다.

| | HPA | Knative | KEDA |
|---|---|---|---|
| 확장 지표 | 리소스 사용량 | HTTP 요청 | 외부 지표 (큐 밀린 양 등) |
| Scale-to-zero | ✗ | ✓ | ✓ |
| 유형 | 풀 | 푸시 | 풀 |
| 고르는 법 | 항상 트래픽 있는 웹 서버 | 가끔 쓰는 웹 서비스 | 큐에서 일 가져오는 워커 |

---

## 6. 크기와 서버 — VPA 와 CA

지금까지는 전부 Pod **개수**였다. 남은 두 축은 Pod **크기**와 **서버**다.

### 6.1 VPA — 재시작이 문제였고, 제자리 수정이 답이 되고 있다

4.4에서 requests가 HPA의 분모라고 했다. 그런데 대부분 그 requests를 **감으로 적고 그대로 둔다.** 잘못 적으면 양쪽으로 터진다.

```
너무 낮게   적음: 100Mi   실제: 800Mi
            스케줄러가 100Mi 만 잡고 노드에 Pod 를 잔뜩 넣음
            → 실제로는 다들 800Mi 씀 → 노드 메모리 터짐 → OOM 으로 죽거나 쫓겨남

너무 높게   적음: 2Gi     실제: 200Mi
            노드에 2Gi 자리 잡아놓고 200Mi 만 씀
            → 나머지 1.8Gi 는 다른 Pod 도 못 쓰는 빈 자리 → 돈 낭비, 노드 더 필요
```

VPA는 **실제 사용량을 보고 requests를 대신 정해주는** 도구다. HPA가 "몇 개?"를 모르는 문제를 자동으로 풀었듯, VPA는 "얼마나 크게?"를 같은 방식으로 푼다. 4.5에서 메모리는 HPA로 못 푼다고 했는데, 그 답이 이것이다.

```yaml
# Example 29-8. VPA
apiVersion: autoscaling.k8s.io/v1         # 설치해야 생기는 그룹
kind: VerticalPodAutoscaler
metadata:
  name: random-generator-vpa
spec:
  targetRef:                              # HPA 의 scaleTargetRef 와 같은 역할
    apiVersion: apps/v1
    kind: Deployment
    name: random-generator
  updatePolicy:
    updateMode: "Off"                     # 추천만 해라, 손대지 마라
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 360" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="VPA 구조: Recommender 가 사용량 히스토리로 requests 를 추천하고, Updater 가 Pod 를 쫓아내면 Admission plugin 이 새로 뜨는 Pod 에 추천값을 끼워 넣는다">
  <defs>
    <marker id="vp-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="20" y="150" width="130" height="56" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="85" y="174" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">VPA 리소스</text>
  <text x="85" y="192" text-anchor="middle" font-size="10.5" fill="#5a3d18">updateMode</text>

  <rect x="215" y="34" width="160" height="60" rx="4" fill="#4caf82"/>
  <text x="295" y="58" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Recommender</text>
  <text x="295" y="77" text-anchor="middle" font-size="10.5" fill="#e9f7f1">8일 히스토그램 · 높은 백분위</text>

  <rect x="215" y="150" width="160" height="56" rx="4" fill="#4caf82"/>
  <text x="295" y="174" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Updater</text>
  <text x="295" y="192" text-anchor="middle" font-size="10.5" fill="#e9f7f1">돌던 Pod 를 쫓아냄</text>

  <rect x="215" y="262" width="160" height="60" rx="4" fill="#5b9bd5"/>
  <text x="295" y="286" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">Admission plugin</text>
  <text x="295" y="305" text-anchor="middle" font-size="10.5" fill="#eaf3fb">Mutating 웹훅 (26장 3.4)</text>

  <rect x="470" y="120" width="180" height="118" rx="5" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="560" y="146" text-anchor="middle" font-size="12.5" font-weight="600" fill="#1b3f63">새로 뜨는 Pod</text>
  <rect x="490" y="160" width="140" height="30" rx="3" fill="#fff" stroke="#2f6ea8"/>
  <text x="560" y="180" text-anchor="middle" font-size="10.5" fill="#1b3f63">내 YAML: cpu 100m</text>
  <rect x="490" y="198" width="140" height="30" rx="3" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="560" y="218" text-anchor="middle" font-size="10.5" font-weight="600" fill="#5a3d18">실제: cpu 350m</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#vp-ar)">
    <path d="M150,168 H211"/>
    <path d="M295,150 V98"/>
    <path d="M295,206 V258"/>
    <path d="M379,292 H466 V242"/>
    <path d="M470,140 H379 V98"/>
  </g>

  <g font-size="11" fill="var(--content,#333)" font-style="italic">
    <text x="180" y="160" text-anchor="middle">모드</text>
    <text x="336" y="126" text-anchor="middle">추천값</text>
    <text x="336" y="236" text-anchor="middle">쫓겨난 자리에</text>
    <text x="424" y="284" text-anchor="middle">requests 주입</text>
    <text x="424" y="132" text-anchor="middle">사용량 관측</text>
  </g>

  <text x="380" y="350" text-anchor="middle" font-size="12" fill="var(--content,#333)">Deployment YAML 은 그대로다 — 생성 시점에 웹훅이 고쳐서 돌려준다</text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  VPA — 추천하는 쪽, 쫓아내는 쪽, 끼워 넣는 쪽이 나뉘어 있다
</div>
</div>
{{< /rawhtml >}}

HPA YAML과 거의 똑같이 생겼고 차이는 `updateMode` 하나다. 그리고 HPA와 달리 **VPA는 설치해야 한다.** 세 부품으로 되어 있다.

| 부품 | 역할 | 일하는 모드 |
|---|---|---|
| Recommender | 8일간 사용량 히스토그램 → 높은 백분위 값 추천. OOM 이벤트도 반영 | 전부 |
| Admission plugin | Pod **새로 뜰 때** requests를 끼워 넣음 — Mutating 웹훅 | Initial 이상 |
| Updater | 돌고 있는 Pod를 **쫓아냄** (새로 뜨면서 위 플러그인이 적용) | Auto/Recreate |

Recommender가 평균이 아니라 **높은 쪽**을 고르는 이유 — 평균으로 잡으면 피크 때 모자란다. Admission plugin은 26장 3.4에서 본 Mutating 어드미션 그대로다. 내가 낸 YAML은 `100m`인데 실제로 뜬 Pod는 `350m` — Deployment YAML은 그대로인데 VPA 웹훅이 생성 시점에 고쳐서 돌려준 것이다.

**VPA의 근본 문제는 Kubernetes 철학과 부딪힌다는 것이다.** Kubernetes는 "고치지 말고 버리고 새로 만들어라"로 설계됐고 Pod의 `resources` 필드는 불변이었다. 수평 확장은 이 철학과 딱 맞지만(똑같은 거 하나 더), 수직 확장은 정반대다(있는 걸 고쳐야 함). 그래서 VPA가 requests를 바꾸려면 **Pod를 죽였다 살려야** 했다.

이 문제가 지금은 풀리고 있다. 리눅스 cgroup 자체는 원래 실행 중에도 값을 바꿀 수 있었다 — 막고 있던 건 Kubernetes 쪽이었다. **In-Place Pod Vertical Scaling**이 들어오면서 `/resize` 서브리소스로 `resources`를 수정할 수 있게 됐고, kubelet이 컨테이너 런타임에 "cgroup 값 바꿔"를 요청한다. 프로세스는 죽지 않고 CPU 배정만 늘어난다.

```bash
kubectl patch pod mypod --subresource resize --patch \
  '{"spec":{"containers":[{"name":"app","resources":{"requests":{"cpu":"500m"}}}]}}'
```

| | 늘리기 | 줄이기 |
|---|---|---|
| CPU | ✓ | ✓ |
| 메모리 | ✓ | ⚠️ 앱이 이미 쓰고 있으면 못 줄임 — 바로 OOM |

그리고 **노드에 여유가 있어야** 한다. 꽉 차 있으면 결국 재스케줄링이 필요하다. 그래서 모드 이름이 `InPlace**Or**Recreate`다 — 제자리로 시도하고, 안 되면 재생성. 앱 쪽 함정도 하나 — JVM처럼 시작할 때 힙 크기를 정하는 앱은 cgroup이 커져도 **앱은 옛날 크기 그대로** 쓴다. 이런 앱은 어차피 재시작해야 효과가 난다(7.1).

### 6.2 네 모드 — Off 에서 시작한다

책은 세 모드를 설명하고 "Auto는 나중에 제자리 수정을 지원할 예정"이라고 적었다. 2026년 기준으로 그 미래는 다른 이름으로 왔다.

| 모드 | Pod 새로 뜰 때 | 이미 도는 Pod | 파괴성 |
|---|---|---|---|
| `Off` | 안 건드림 | 안 건드림 — 추천만 | 없음 |
| `Initial` | requests 넣어줌 | 안 건드림 | 부분적 |
| `InPlaceOrRecreate` | requests 넣어줌 | 제자리 시도, 안 되면 재시작 | 낮음 |
| `Auto` / `Recreate` | requests 넣어줌 | **무조건 재시작** | 높음 |

**`Off`는 감시만 하고 손은 안 대는 모드다.** 추천값은 `status.recommendation`에 쌓인다.

```bash
kubectl describe vpa random-generator-vpa
Recommendation:
  Container Recommendations:
    Container Name: random-generator
    Target:
      Cpu:     250m
      Memory:  340Mi
```

**`Initial`이 "부분적으로 파괴적"인 이유**가 미묘하다. 재시작은 안 시키지만 requests가 바뀌면 **자리 크기가 바뀐다.** 100m 자리 → 350m 자리로 커지면 원래 노드에 빈자리가 없어 다른 노드로 가고, 어느 노드에도 없으면 **Pending으로 멈춘다.** 배포했는데 Pod가 안 뜨고, 이유를 찾아보면 VPA가 requests를 올려놔서 자리가 없는 것이다.

`Auto`는 이제 굳이 쓸 이유가 없다. 책 쓸 땐 "나중에 좋아질 거야"였는데 실제로는 `InPlaceOrRecreate`라는 다른 이름으로 나왔다. 고르는 순서는 이렇다.

```
Off                 ← 추천값이 말 되는지 며칠 확인
    ↓
Initial             ← 다음 배포 때 자연스럽게 반영
    ↓
InPlaceOrRecreate   ← 더 자동화하고 싶으면. 재시작 최소화
```

### 6.3 HPA 와 VPA — 같은 지표를 보면 싸운다

둘은 서로를 모른다. 둘 다 CPU를 보고 있다면 이렇게 된다.

```
CPU 높음
  → HPA: "Pod 늘려!"      → Pod 4개
  → VPA: "CPU 키워!"      → 각 Pod 2배
  → 결과: 4개 × 2배 = 8배 용량      필요한 건 2배였다
```

서로 모르니까 둘 다 반응해서 과하게 된다 — **이중 확장.** 해법은 같은 지표를 두 개가 보지 않게 하는 것이다.

| HPA가 보는 것 | VPA가 하는 것 | |
|---|---|---|
| CPU | CPU 조절 | ❌ 충돌 |
| 커스텀 지표 (요청 수) | CPU/메모리 조절 | ✓ |
| CPU | `Off`로 추천만 | ✓ |

실무에서 흔한 조합은 **HPA는 요청 수로, VPA는 Off로 추천만 보고 사람이 반영**이다.

### 6.4 CA — CPU 가 아니라 Pending 을 본다

HPA가 Pod를 늘리려는데 노드에 자리가 없으면? CA가 **노드(서버)를 더 산다.** 노드는 곧 VM이고 VM은 시간당 요금이니, 밤에 Pod가 줄어 노드가 텅 비면 반납해서 요금을 아끼고 낮에 다시 필요하면 새로 산다.

**CA의 신호는 CPU가 아니다.** 4.2의 HPA가 "자리 없어서 못 뜬 Pod"를 만들면 그것이 신호다.

```bash
kubectl get pods
NAME          STATUS
worker-xxx    Pending       ← 만들긴 했는데 놓을 데가 없어서 기다리는 중

kubectl describe pod worker-xxx
Events:
  FailedScheduling   0/3 nodes are available: insufficient memory
  TriggeredScaleUp   pod triggered scale-up: [{node-group-1 3->4}]   ← CA 가 반응
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 300" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HPA 와 CA 의 릴레이: HPA 가 Pod 를 늘리면 자리가 없어 Pending 이 생기고, CA 가 그걸 보고 노드를 추가한다. 한가해지면 반대 순서로 노드를 반납한다">
  <defs>
    <marker id="ca-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <!-- 위쪽: 늘어나는 흐름 -->
  <text x="20" y="34" font-size="12.5" font-weight="600" fill="var(--content,#333)">늘어날 때</text>
  <rect x="20" y="50" width="120" height="50" rx="4" fill="#5b9bd5"/>
  <text x="80" y="70" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">HPA</text>
  <text x="80" y="88" text-anchor="middle" font-size="11" fill="#eaf3fb">"Pod 3개 더"</text>

  <rect x="200" y="50" width="120" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="260" y="70" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">스케줄러</text>
  <text x="260" y="88" text-anchor="middle" font-size="11" fill="#1b3f63">자리 없음</text>

  <rect x="380" y="50" width="120" height="50" rx="4" fill="#fbe0c4" stroke="#c0392b"/>
  <text x="440" y="70" text-anchor="middle" font-size="12" font-weight="600" fill="#7a2e22">Pod Pending</text>
  <text x="440" y="88" text-anchor="middle" font-size="11" fill="#7a2e22">← CA 의 신호</text>

  <rect x="560" y="50" width="120" height="50" rx="4" fill="#4caf82"/>
  <text x="620" y="70" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">CA</text>
  <text x="620" y="88" text-anchor="middle" font-size="11" fill="#e9f7f1">"노드 하나 더"</text>

  <g stroke="var(--content,#444)" stroke-width="1.8" fill="none" marker-end="url(#ca-ar)">
    <path d="M140,75 H196"/>
    <path d="M320,75 H376"/>
    <path d="M500,75 H556"/>
  </g>
  <text x="620" y="128" text-anchor="middle" font-size="11" font-style="italic" fill="var(--content,#333)">클라우드 API 호출 → VM 생성 → Node 등록 (1~3분)</text>

  <!-- 아래쪽: 줄어드는 흐름 -->
  <text x="20" y="184" font-size="12.5" font-weight="600" fill="var(--content,#333)">줄어들 때</text>
  <rect x="20" y="200" width="120" height="50" rx="4" fill="#5b9bd5"/>
  <text x="80" y="220" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">HPA</text>
  <text x="80" y="238" text-anchor="middle" font-size="11" fill="#eaf3fb">Pod 줄임</text>

  <rect x="200" y="200" width="120" height="50" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="260" y="220" text-anchor="middle" font-size="12" font-weight="600" fill="#1b3f63">노드 비어감</text>
  <text x="260" y="238" text-anchor="middle" font-size="11" fill="#1b3f63">requests 합 &lt; 50%</text>

  <rect x="380" y="200" width="120" height="50" rx="4" fill="#f7e08a" stroke="#c9a92c"/>
  <text x="440" y="220" text-anchor="middle" font-size="12" font-weight="600" fill="#5a4a10">네 조건 + 10분</text>
  <text x="440" y="238" text-anchor="middle" font-size="11" fill="#5a4a10">시뮬레이션 통과</text>

  <rect x="560" y="200" width="120" height="50" rx="4" fill="#4caf82"/>
  <text x="620" y="220" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">CA</text>
  <text x="620" y="238" text-anchor="middle" font-size="11" fill="#e9f7f1">cordon → drain → 반납</text>

  <g stroke="var(--content,#444)" stroke-width="1.8" fill="none" marker-end="url(#ca-ar)">
    <path d="M140,225 H196"/>
    <path d="M320,225 H376"/>
    <path d="M500,225 H556"/>
  </g>
  <text x="380" y="284" text-anchor="middle" font-size="12" fill="var(--content,#333)">HPA 와 CA 는 서로에게 전화하지 않는다 — 그런데 릴레이가 이어진다</text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  분리되어 있지만 보완적 — HPA 는 Pod 만 보고, CA 는 Pending 과 빈 노드만 본다
</div>
</div>
{{< /rawhtml >}}

CA는 "노드 하나 추가하면 Pod가 들어갈까?"를 먼저 계산한다. Pod가 메모리 64Gi를 요구하는데 노드 종류가 16Gi짜리면 100개를 추가해도 못 들어가니, 이런 경우 CA는 노드를 안 늘린다.

**CA는 아무 서버나 사지 않는다** — **노드 그룹** 중 하나에서 한 대 더 산다. AWS의 Auto Scaling Group, GKE의 node pool이 이것이고, 그룹 안은 다 같은 크기라고 가정한다. 그래야 "기존 노드 하나와 똑같이 생겼겠지"로 계산할 수 있다. 여러 그룹이 후보면 **expander**가 고른다 — `random`(기본), `least-waste`, `most-pods`, `price`, `priority`. 실무에선 `least-waste`나 `priority`를 많이 쓴다.

여기서 짚어둘 것 — **Node 리소스는 내장이지만 "관찰용"이지 "생성용"이 아니다.**

| | Pod | Node |
|---|---|---|
| YAML 만들면 | 컨테이너가 생김 | 아무것도 안 생김 |
| 관계 | 리소스 → 실체 | 실체 → 리소스 |

서버가 먼저 있고 그게 붙으면 Node 객체가 생기는 순서다. 그래서 CA는 Kubernetes API가 아니라 **클라우드 API를 직접 호출**해 VM을 만들고, 그 VM의 kubelet이 등록하면 Node가 생긴다. 노드 그룹, 노드를 사고 반납하는 것은 전부 클라우드 쪽 개념이다.

이 빈틈을 메우려는 게 **Cluster API**다. `MachineDeployment`라는 리소스를 만들어 **YAML로 노드를 생성**할 수 있게 하고, 클라우드별 차이는 machine controller가 흡수한다. Pod ↔ Deployment 관계를 노드에 적용한 것이다. 2026년 기준 AWS, Azure, GCP, vSphere, OpenStack 등 주요 공급자는 다 있지만, EKS·GKE·AKS 같은 관리형 서비스를 쓰면 각자 노드 자동 확장이 이미 있어 만날 일이 거의 없다. 자체 관리 클러스터의 표준으로 자리잡았지 관리형까지 대체하진 않았다. AWS의 **Karpenter**도 알아둘 만하다 — 노드 그룹 없이 "이 Pod에 딱 맞는 크기의 VM"을 그때그때 고르는 대안으로, EKS에서는 CA 대신 이걸 쓰는 경우가 많다.

CA도 **설치해야 하는 애드온**이고, HPA와 달리 `kind: ClusterAutoscaler` 같은 리소스가 없다. 백그라운드에서 도는 Pod 하나고, 설정은 실행 옵션과 노드 그룹 태그로 한다.

### 6.5 노드를 빼는 네 조건과 10분

노드를 빼는 건 그 위 Pod를 전부 쫓아내는 거라 **네 가지를 다 통과해야** 뺀다.

```
① 반 이상 비어 있나       requests 합이 노드 용량의 50% 미만 (실제 사용량 아님)
② 쫓겨난 Pod 가 갈 데 있나  CA 가 머릿속으로 시뮬레이션 — 안 들어가면 안 지움
③ 노드에 "빼지 마" 표시 없나  cluster-autoscaler.kubernetes.io/scale-down-disabled
④ 못 옮기는 Pod 없나
     PodDisruptionBudget 위반   "최소 2개는 항상"인데 옮기면 1개
     로컬 스토리지 사용          옮기면 디스크 데이터 못 가져감
     컨트롤러 없는 단독 Pod      쫓아내면 다시 안 뜸
     시스템 Pod                  kube-system
```

**실무 함정** — "노드가 텅 비었는데 왜 안 줄어들지?"는 대부분 ④다. `kubectl run`으로 띄운 Pod 하나, 로컬 볼륨 쓰는 Pod 하나가 노드를 붙잡고 있다.

넷을 통과한 상태가 **10분** 유지되면 cordon(새 Pod 받지 마) → drain(위의 Pod를 하나씩 쫓아냄, 다른 노드에서 다시 뜸) → 다 비면 VM 반납. 10분 기다리는 이유는 HPA의 5분 안정화 창과 같다 — 잠깐 비었다고 바로 빼면 다시 사야 한다. 그리고 Pending Pod가 있으면 축소는 아예 안 본다. 늘려야 할 때 줄이면 안 되니까.

CA가 특히 빛나는 경우 — 밤 2시에 배치 작업이 노드 5개 분량을 쓰고 30분 만에 끝난다면, CA 없이는 그 5개를 24시간 내내 켜둬야 한다. CA가 있으면 30분어치만 낸다.

---

## 7. Discussion

### 7.1 확장 수준 — 앱 튜닝이 맨 위인 이유

책은 장을 닫으며 확장 기법을 **작은 것부터 큰 것 순서로** 다시 세운다.

| 층 | 뭘 조절 | 누가 | 언제 |
|---|---|---|---|
| 앱 튜닝 | 프로세스 안 (스레드, 힙) | 사람 | **처음 한 번** |
| VPA | Pod 크기 | 자동 (Off로 추천만도 가능) | 처음 한 번 + 이후 |
| HPA / Knative / KEDA | Pod 개수 | 자동 | 이제부터 계속 |
| CA | 노드 개수 | 자동 | 자리 모자랄 때 |

이 장에서 다루지 않은 앱 튜닝이 왜 맨 위에 있는가 — **밑에서 안 쓰면 위에서 아무리 줘도 낭비**이기 때문이다.

```
앱: 스레드 1개만 씀
VPA: CPU 4개로 키움     → 3개 놈
HPA: Pod 10개로 늘림    → 각각 3개씩 놈
CA: 노드 3개 추가       → 다 놈
```

반대 방향도 위험하다. 힙을 컨테이너 limit보다 크게 잡으면 OOM인데, 이건 Pod를 100개로 늘려도 **100개가 다 똑같이 죽는다.** 수평 확장은 "같은 걸 복제"하니 잘못된 설정도 같이 복제된다.

전형적인 함정은 앱이 **노드 전체를 자기 몫으로 착각**하는 것이다. 컨테이너에 CPU 2개를 줬는데 `nproc`은 노드 전체(64코어)를 돌려주니 스레드 64개를 만든다. 최신 JVM은 cgroup을 읽어서 알아서 하지만, 오래된 런타임은 시작 스크립트에서 "내 몫은 2개"를 계산해 넘겨줘야 한다. 한 걸음 더 가면 Netflix Adaptive Concurrency Limits처럼 앱이 자기 응답 시간을 재면서 동시성을 실시간으로 조절하는 **앱 내 자동 확장**도 있다 — Knative가 Pod 밖에서 동시 요청을 조절했다면, 이건 Pod 안에서 스스로 하는 것이다.

그래서 순서는 이렇다.

```
1. 앱 튜닝        ← 처음 한 번. 앱이 자기 몫을 제대로 쓰게
2. VPA (Off)      ← 처음 한 번. requests 값 찾기
3. HPA 켜기       ← 이제부터 자동
4. CA             ← 자리 모자라면 노드 추가
```

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 330" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="확장 수준: 앱 튜닝이 맨 아래 기초이고 그 위로 VPA, HPA, CA 가 쌓인다. 밑에서 안 쓰면 위에서 아무리 줘도 낭비다">
  <defs>
    <marker id="lv-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="150" y="30" width="420" height="52" rx="4" fill="#c0392b"/>
  <text x="290" y="61" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">CA — 노드 개수</text>
  <text x="470" y="61" text-anchor="middle" font-size="10.5" fill="#f6d5d1">자리 모자랄 때</text>

  <rect x="150" y="94" width="420" height="52" rx="4" fill="#5b9bd5"/>
  <text x="290" y="125" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">HPA · Knative · KEDA — Pod 개수</text>
  <text x="470" y="125" text-anchor="middle" font-size="10.5" fill="#eaf3fb">이제부터 계속</text>

  <rect x="150" y="158" width="420" height="52" rx="4" fill="#4caf82"/>
  <text x="290" y="189" text-anchor="middle" font-size="12.5" font-weight="600" fill="#fff">VPA — Pod 크기 (requests)</text>
  <text x="470" y="189" text-anchor="middle" font-size="10.5" fill="#e9f7f1">처음 한 번 + 이후</text>

  <rect x="150" y="222" width="420" height="56" rx="4" fill="#fbe0c4" stroke="#d9a86a" stroke-width="2"/>
  <text x="290" y="246" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5a3d18">앱 튜닝 — 프로세스 안 (스레드, 힙)</text>
  <text x="290" y="266" text-anchor="middle" font-size="10.5" fill="#5a3d18">사람이 · 처음 한 번 · 이 장이 다루지 않는 층</text>
  <text x="470" y="252" text-anchor="middle" font-size="10.5" fill="#5a3d18">기초 공사</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#lv-ar)">
    <path d="M110,258 V86"/>
  </g>
  <text x="86" y="176" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">쌓는</text>
  <text x="86" y="192" text-anchor="middle" font-size="11.5" font-style="italic" fill="var(--content,#333)">순서</text>

  <text x="620" y="150" text-anchor="middle" font-size="11.5" font-style="italic" fill="#c0392b">밑에서 안 쓰면</text>
  <text x="620" y="168" text-anchor="middle" font-size="11.5" font-style="italic" fill="#c0392b">위는 낭비</text>

  <text x="380" y="310" text-anchor="middle" font-size="12" fill="var(--content,#333)">앱이 스레드 1개만 쓰면 CPU 4개도, Pod 10개도, 노드 3대도 전부 논다</text>
</svg>
<div style="text-align:center;font-size:13px;opacity:0.75;margin-top:6px;color:var(--content,#333);">
  확장 수준 — 아래가 튼튼해야 위가 의미를 갖는다
</div>
</div>
{{< /rawhtml >}}

1, 2는 기초 공사고 3부터가 일상 운영이다.

### 7.2 내장과 설치 — HPA 하나만 내장이다

이 장 전체에서 가장 자주 헷갈리는 질문을 한 표로 닫아둔다.

| | 내장? | 리소스? |
|---|---|---|
| HPA | ✅ | `kind: HorizontalPodAutoscaler` |
| HPA 컨트롤러 | ✅ kube-controller-manager 안 | — |
| 컨테이너 측정 (cAdvisor) | ✅ kubelet 안 | — |
| API 그룹 이름 · APIService 위임 | ✅ | `kind: APIService` |
| Node 객체 | ✅ (관찰용) | `kind: Node` |
| metrics-server | ❌ 설치 | Deployment + Service + APIService |
| Prometheus Adapter | ❌ 설치 | 〃 |
| VPA | ❌ 설치 | `kind: VerticalPodAutoscaler` |
| CA | ❌ 설치 | **리소스 없음** — Pod 하나 |
| Knative | ❌ 설치 | `kind: Service` (`serving.knative.dev`) |
| KEDA | ❌ 설치 | `kind: ScaledObject`, `ScaledJob` |
| Cluster API | ❌ 설치 | `kind: MachineDeployment` |

패턴이 보인다 — **"판단하는 쪽"(HPA)은 내장, "숫자를 공급하는 쪽"(metrics-server 등)은 설치.** Kubernetes는 "HPA는 `metrics.k8s.io`에 물어본다"는 **규칙과 빈 자리**만 갖고 있고, 그 자리를 채우는 건 세 종류 다 애드온이다. cAdvisor처럼 측정 자체는 필수라 kubelet에 넣었지만, "어떻게 모아서 노출할지"는 환경마다 원하는 게 달라서(Prometheus로 대체하는 곳도 많다) 코어에서 빼고 교체 가능하게 둔 것이다.

그래서 HPA YAML을 만들었는데 아무 반응이 없다면 HPA 문제가 아니라 **지표 공급이 없는** 경우가 대부분이다.

```bash
kubectl describe hpa random-generator
# unable to get metrics ...   → metrics-server 부터 확인
```

### 7.3 서로 모르는데 맞물린다

이 장의 확장기들은 **서로 대화하지 않는다.** HPA는 Pod만 본다. CA는 Pending Pod와 빈 노드만 본다. VPA는 HPA가 있는지조차 모른다. KEDA는 HPA를 만들어놓고 0↔1만 챙긴다. 그런데 결과적으로 릴레이가 이어진다.

```
HPA/VPA: "Pod 가 더 필요해"
    ↓ 자리 없으면 Pending
CA:      "노드 하나 더"
    ↓ 한가해지면
HPA:     Pod 줄임 → 노드 비어감
    ↓ 10분 후
CA:      노드 반납
```

책의 표현은 "분리되어 있지만 보완적(decoupled but complementary)"이다. 아무도 다음 사람에게 전화하지 않았는데 각자 자기 신호(CPU, Pending, 빈 노드)만 보고 움직이니 전체가 맞물린다. 24장의 컨트롤 플레인·데이터 플레인 분리, 26장의 인증·인가 분리와 같은 설계 — **정해진 신호로만 소통하고 서로의 내부는 모른다.**

다만 6.3에서 봤듯 **같은 신호를 둘이 보면** 이 분리가 독이 된다. HPA와 VPA가 둘 다 CPU를 보면 이중 확장이다. 분리는 신호가 겹치지 않을 때만 안전하다.

그리고 이 릴레이의 출발점은 언제나 실측이다. 사람이 "아마 100명 올 거야"라고 짐작한 숫자가 아니라, 지금 문 앞에 47명 서 있다는 측정값. 그것이 2.3의 **antifragile** — 부하가 올수록 시스템이 커지는 성질 — 을 만든다.

### 핵심 메시지

```
Elastic Scale 의 몫: 예측이 아니라 실측에 반응해서, 세 축으로 스스로 커지고 작아지는 것
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

전제      → 숫자를 미리 알 수 없다. 규칙만 정하고 값은 측정에 맡긴다
            수동은 예측적(미리), 자동은 반응적(뒷북) — 둘 다 자리가 있다
수동      → scale 은 빠르지만 파일에 안 남는다. 급하면 쓰되 반드시 YAML 에 역반영
HPA       → 이 장에서 유일하게 내장. Deployment 에 붙인다 (ReplicaSet 아님)
            분자(측정값)는 metrics-server, 분모(requests)는 Pod spec — 둘 다 있어야 %
            지표는 "Pod 를 늘리면 내려가는가" 로 고른다. 메모리는 대부분 아니다
            늘릴 땐 빨리 줄일 땐 천천히 — behavior 는 YAML 로만
자리      → APIService 는 그룹마다 하나. 두 개 붙이면 에러 없이 덮어써진다
0 으로    → Pod 가 없으면 HPA 는 볼 게 없다. Pod 앞에 문지기를 둔다
            Knative: HTTP, 푸시, HPA 버리고 KPA. Activator 가 요청을 붙잡아둔다
            KEDA: 이벤트, 풀, HPA 위에 얹음. 0↔1 만 직접
VPA       → requests 를 실측으로. 재시작이 문제였고 InPlaceOrRecreate 가 답이 되는 중
            Off 로 시작. HPA 와 같은 지표 보면 이중 확장
CA        → CPU 가 아니라 Pending 을 본다. 노드를 빼려면 네 조건 + 10분
            리소스가 아니라 Pod 하나. 클라우드 API 를 직접 부른다
수준      → 앱 튜닝이 맨 위. 밑에서 안 쓰면 위에서 아무리 줘도 낭비
            앱 튜닝 → VPA(Off) → HPA → CA 순으로 쌓는다
```

> Elastic Scale 은 **"숫자를 맞추는 패턴이 아니라, 숫자를 맞추지 않아도 되게 만드는 패턴"** 이다.
> 사람은 울타리와 목표만 정하고,
> 측정은 kubelet 이, 판단은 HPA 가, 자리는 CA 가 각자 맡으며,
> 서로 대화하지 않는데도 신호가 이어진다.
> 그러면 트래픽이 몰릴수록 시스템은 **약해지는 대신 커진다.**

---

## 8. References

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>HPA 가 requests 를 기준으로 계산한다는 것과 안정화 창의 동작은 공식 문서 <strong>"Horizontal Pod Autoscaling"</strong>에 정리되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "desiredReplicas = ceil[currentReplicas * ( currentMetricValue / desiredMetricValue )]"
  </blockquote>
  <div>[해석] 4.6 의 비례식이 공식 문서에 그대로 적혀 있다. 같은 문서가 여러 지표를 걸었을 때 최댓값을 택한다는 것(4.5), 갓 시작한 Pod 의 CPU 샘플을 무시한다는 것과 축소 안정화 창의 기본값이 5분이라는 것(4.6), 그리고 <code>.spec.behavior</code> 의 <code>policies</code>·<code>stabilizationWindowSeconds</code>·<code>selectPolicy</code> 정의를 담고 있다. Pod 리소스 <code>resize</code> 서브리소스와 제자리 수정(6.1)은 <strong>"Resize CPU and Memory Resources assigned to Containers"</strong> 문서에, VPA 의 <code>InPlaceOrRecreate</code> 모드는 autoscaler 저장소의 VPA 문서에 있다.</div>
  <div style="margin-top:10px;">Knative 의 Activator·Queue-proxy·Autoscaler 구조와 <code>autoscaling.knative.dev/</code> annotation 목록(5.2)은 Knative Serving 의 <strong>"Autoscaling"</strong> 문서에, KEDA 가 <code>ScaledObject</code> 로부터 HPA 를 생성하고 0↔1 만 직접 처리한다는 점(5.3)은 KEDA 의 <strong>"Concepts"</strong> 문서에 정리되어 있다. Cluster Autoscaler 의 축소 조건 네 가지와 10분 대기, expander 종류(6.4~6.5)는 autoscaler 저장소의 FAQ 가 가장 정확하다.</div>
  <div style="margin-top:10px;">책 예제에서 눈에 띈 것 — Example 29-1 의 <code>kubectl scale random-generator</code> 는 리소스 종류(<code>deployment</code>)가 빠져 있어 실제로는 동작하지 않는다. "모든 behavior 매개변수를 <code>kubectl autoscale</code> 로 구성할 수 있다"는 문장은 실제와 다르며, 해당 명령은 <code>--min</code>·<code>--max</code>·<code>--cpu-percent</code> 만 지원한다. VPA 의 <code>Auto</code> 모드가 "미래에 제자리 수정을 지원할 예정"이라는 서술(2023 기준)은 이후 <code>InPlaceOrRecreate</code> 라는 별도 모드로 실현되었고, <code>Auto</code> 는 여전히 <code>Recreate</code> 와 같이 동작한다. Google Stackdriver 는 현재 Google Cloud Monitoring 으로 이름이 바뀌었다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/">kubernetes.io — Horizontal Pod Autoscaling</a></div>
  <div>→ <a href="https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/">kubernetes.io — Resize CPU and Memory Resources assigned to Containers</a></div>
  <div>→ <a href="https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler">GitHub — Vertical Pod Autoscaler</a></div>
  <div>→ <a href="https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md">GitHub — Cluster Autoscaler FAQ</a></div>
  <div>→ <a href="https://github.com/kubernetes-sigs/metrics-server">GitHub — metrics-server</a></div>
  <div>→ <a href="https://knative.dev/docs/serving/autoscaling/">knative.dev — Autoscaling</a></div>
  <div>→ <a href="https://keda.sh/docs/concepts/">keda.sh — Concepts</a></div>
  <div>→ <a href="https://cluster-api.sigs.k8s.io/">cluster-api.sigs.k8s.io — The Cluster API Book</a></div>
</div>
{{< /rawhtml >}}