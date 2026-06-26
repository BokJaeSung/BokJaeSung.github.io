---
series: ["K8sPatterns"]
title: "K8sPatterns.03 Declarative Deployment"
date: 2026-06-26T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "container", "deployment"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.03 Declarative Deployment'
  relative: true
summary: "How Kubernetes Deployment resource automates application upgrades and rollbacks through declarative strategies including RollingUpdate, Recreate, Blue-Green, and Canary."
---

컨테이너화된 애플리케이션을 운영하다 보면 새 버전 배포가 반복적으로 발생한다. Kubernetes는 Deployment 리소스를 통해 이 과정을 선언적으로, 자동으로 처리한다. 이 챕터는 Deployment의 동작 원리와 네 가지 배포/릴리즈 전략을 다룬다.

{{< rawhtml >}}
<details style="background:transparent;border:1px solid #30363d;border-radius:8px;padding:10px 16px;margin:1.2rem 0;font-family:inherit;">
<summary style="cursor:pointer;font-weight:600;font-size:14px;color:#8b949e;user-select:none;font-family:inherit;">목차 — Table of Contents</summary>
<div style="margin-top:10px;font-size:14px;line-height:2;font-family:inherit;">
  <div><a href="#0-overview" style="color:#c9d1d9;text-decoration:none;">0. Overview</a></div>
  <div><a href="#1-problem--solution" style="color:#c9d1d9;text-decoration:none;">1. Problem & Solution</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#11-problem" style="color:#6e7681;text-decoration:none;">1.1 Problem</a></div>
    <div><a href="#12-solution" style="color:#6e7681;text-decoration:none;">1.2 Solution</a></div>
  </div>
  <div><a href="#2-how-deployment-works" style="color:#c9d1d9;text-decoration:none;">2. How Deployment Works</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#21-deployment--replicaset--pod" style="color:#6e7681;text-decoration:none;">2.1 Deployment → ReplicaSet → Pod</a></div>
    <div><a href="#22-prerequisites-for-deployment" style="color:#6e7681;text-decoration:none;">2.2 Prerequisites for Deployment</a></div>
    <div><a href="#23-kubectl-rollout" style="color:#6e7681;text-decoration:none;">2.3 kubectl rollout</a></div>
  </div>
  <div><a href="#3-rolling-deployment" style="color:#c9d1d9;text-decoration:none;">3. Rolling Deployment</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#31-example-yaml" style="color:#6e7681;text-decoration:none;">3.1 Example YAML</a></div>
    <div><a href="#32-maxsurge--maxunavailable" style="color:#6e7681;text-decoration:none;">3.2 maxSurge & maxUnavailable</a></div>
    <div><a href="#33-minreadyseconds" style="color:#6e7681;text-decoration:none;">3.3 minReadySeconds</a></div>
    <div><a href="#34-rolling-update-step-by-step" style="color:#6e7681;text-decoration:none;">3.4 Rolling Update Step-by-Step</a></div>
    <div><a href="#35-how-to-trigger-an-update" style="color:#6e7681;text-decoration:none;">3.5 How to Trigger an Update</a></div>
    <div><a href="#36-benefits-of-deployment" style="color:#6e7681;text-decoration:none;">3.6 Benefits of Deployment</a></div>
  </div>
  <div><a href="#4-fixed-deployment-recreate" style="color:#c9d1d9;text-decoration:none;">4. Fixed Deployment (Recreate)</a></div>
  <div><a href="#5-blue-green-release" style="color:#c9d1d9;text-decoration:none;">5. Blue-Green Release</a></div>
  <div><a href="#6-canary-release" style="color:#c9d1d9;text-decoration:none;">6. Canary Release</a></div>
  <div><a href="#7-strategy-comparison" style="color:#c9d1d9;text-decoration:none;">7. Strategy Comparison</a></div>
  <div><a href="#8-higher-level-deployments" style="color:#c9d1d9;text-decoration:none;">8. Higher-Level Deployments</a></div>
  <div><a href="#9-q--a" style="color:#c9d1d9;text-decoration:none;">9. Q & A</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#q1-deployment와-pod를-직접-만드는-것의-차이" style="color:#6e7681;text-decoration:none;">Q1. Deployment와 Pod를 직접 만드는 것의 차이</a></div>
    <div><a href="#q2-rolling-update-중-두-버전이-공존하면-문제가-없나" style="color:#6e7681;text-decoration:none;">Q2. Rolling Update 중 두 버전이 공존하면 문제가 없나</a></div>
    <div><a href="#q3-blue-green과-canary의-선택-기준" style="color:#6e7681;text-decoration:none;">Q3. Blue-Green과 Canary의 선택 기준</a></div>
  </div>
</div>
</details>
{{< /rawhtml >}}

---

Kubernetes에서 애플리케이션을 배포한다는 것은 YAML 파일을 작성하고 `kubectl apply`를 실행하는 것이다. 그 뒤의 모든 과정, 즉 Pod 생성, 헬스체크, 순차 교체, 실패 시 롤백은 Kubernetes가 처리한다. 이것이 선언적 배포의 핵심이다.

---

## 1. Problem & Solution

### 1.1 Problem

마이크로서비스 환경에서는 서비스 수가 많고, 각 서비스가 독립적으로 업데이트된다. 하나의 서비스를 새 버전으로 교체하려면 다음 단계가 필요하다.

- 새 버전 Pod 실행
- 기존 Pod 안전하게 종료 (graceful shutdown)
- 새 Pod 정상 실행 여부 확인
- 실패 시 이전 버전으로 롤백

이 과정을 수동으로 하면 사람 실수가 생기고, 스크립트로 자동화하면 유지 비용이 크다. 서비스가 많아질수록 배포 자체가 병목이 된다.

업데이트 방식은 크게 두 가지로 나뉜다.

| 방식 | 설명 | 단점 |
|---|---|---|
| 다운타임 허용 | 기존 전부 종료 후 새 버전 실행 | 서비스 중단 |
| 다운타임 없음 | 구버전과 신버전 동시 실행 | 리소스 2배 사용 |

### 1.2 Solution

Kubernetes의 Deployment 리소스가 이 문제를 해결한다. Deployment는 "이런 상태여야 해"라고 선언해두면 나머지를 자동으로 처리하는 주문서다.

```
개발자가 할 일:   YAML 파일 작성 + kubectl apply
Kubernetes가 할 일: Pod 생성, 교체, 헬스체크, 롤백 전부
```

릴리즈 사이클마다 수십 번 배포가 반복되는 환경에서, 이 자동화는 운영 비용을 크게 줄인다.

---

## 2. How Deployment Works

### 2.1 Deployment → ReplicaSet → Pod

Deployment는 직접 Pod를 만들지 않는다. 내부적으로 ReplicaSet을 생성하고, ReplicaSet이 Pod를 관리한다.

```
Deployment (주문서/설계도)
    ↓ 생성
ReplicaSet (Pod 개수 관리자)
    ↓ 생성
Pod  Pod  Pod (실제 앱)
```

업데이트 시에는 새 ReplicaSet이 추가로 생성되고, 기존 ReplicaSet의 Pod를 하나씩 줄이면서 새 ReplicaSet의 Pod를 늘린다. 업데이트가 완료된 후에도 기존 ReplicaSet은 삭제되지 않고 replicas=0 상태로 남는다. 롤백 시 재사용하기 위해서다.

```
업데이트 완료 후:
ReplicaSet v1 → (replicas=0, 롤백 대기)
ReplicaSet v2 → Pod✅ Pod✅ Pod✅
```

### 2.2 Prerequisites for Deployment

Deployment가 Pod를 예측 가능하게 시작하고 종료하려면 컨테이너가 두 가지를 갖춰야 한다.

| 조건 | 설명 | 관련 챕터 |
|---|---|---|
| Lifecycle 이벤트 처리 | SIGTERM 수신 시 작업을 마무리하고 종료 | Chapter 5, Managed Lifecycle |
| Health-check endpoint | readinessProbe로 준비 완료 여부를 알림 | Chapter 4, Health Probe |

이 두 가지가 없으면 Kubernetes는 Pod가 언제 준비됐는지, 언제 안전하게 종료할 수 있는지 알 수 없다.

### 2.3 kubectl rollout

Deployment는 YAML 파일 수정만으로도 관리할 수 있지만, 일상적인 작업에는 `kubectl rollout` 명령어가 편리하다.

참고로 Kubernetes 1.18 이전에는 `kubectl rolling-update` 명령어가 있었다. 이 방식은 클라이언트(kubectl)가 각 업데이트 단계를 직접 서버에 지시하는 명령형 방식이었다. 현재의 `kubectl rollout`은 서버 측에서 Deployment 선언을 기반으로 Kubernetes가 알아서 처리하는 선언형 방식이다.

| 명령어 | 역할 |
|---|---|
| `kubectl rollout status` | 현재 배포 진행 상태 확인 |
| `kubectl rollout pause` | 롤아웃 일시 중지 |
| `kubectl rollout resume` | 일시 중지된 롤아웃 재개 |
| `kubectl rollout undo` | 이전 버전으로 롤백 |
| `kubectl rollout history` | 배포 히스토리 확인 |
| `kubectl rollout restart` | 현재 Pod 재시작 (업데이트 없이) |

---

## 3. Rolling Deployment

RollingUpdate는 Deployment의 기본 전략이다. Pod를 하나씩 교체하면서 항상 일정 수 이상의 Pod가 살아있도록 보장한다. 서비스 중단 없이 업데이트할 수 있다.

### 3.1 Example YAML

```yaml
# Example 3-1. Deployment for a rolling update
apiVersion: apps/v1
kind: Deployment
metadata:
  name: random-generator
spec:
  replicas: 3              # Pod 3개 유지 (롤링 업데이트는 2개 이상 필요)
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 업데이트 중 추가로 띄울 수 있는 Pod 수 → 최대 4개
      maxUnavailable: 1    # 동시에 꺼져도 되는 Pod 수 → 최소 2개 유지
  minReadySeconds: 60      # 새 Pod readinessProbe 성공 후 60초 대기
  selector:
    matchLabels:
      app: random-generator
  template:
    metadata:
      labels:
        app: random-generator
    spec:
      containers:
      - image: k8spatterns/random-generator:1.0
        name: random-generator
        readinessProbe:            # 롤링 배포에서 핵심. 절대 빠뜨리면 안 됨
          exec:
            command: [ "stat", "/tmp/random-generator-ready" ]
```

### 3.2 maxSurge & maxUnavailable

두 필드 모두 절댓값 또는 퍼센트(%)로 설정할 수 있다. 퍼센트일 때 replicas 수를 기준으로 계산하며, maxSurge는 올림, maxUnavailable은 내림으로 처리한다. 기본값은 둘 다 25%다.

```
replicas: 3, maxSurge: 1, maxUnavailable: 1 기준

최대 Pod 수 = 3 + 1 = 4개   (maxSurge)
최소 Pod 수 = 3 - 1 = 2개   (maxUnavailable)
→ 업데이트 중 항상 2~4개 사이에서 유지
```

숫자를 키우면 교체 속도가 빨라지고, 줄이면 느리지만 안정적이다.

### 3.3 minReadySeconds

새 Pod의 readinessProbe가 이 시간(초) 동안 연속으로 성공해야 "준비 완료"로 인정하고 다음 Pod 교체를 시작한다.

```
새 Pod 시작
    ↓
readinessProbe 통과 ✅
    ↓
minReadySeconds: 60 → 60초 동안 이상 없어야 함
    ↓
"준비 완료" 인정 → 다음 Pod 교체 시작
```

값을 크게 설정할수록 안전하고, 교체 사이사이에 여유가 생겨 `kubectl rollout pause`로 일시 중지하기도 쉽다.

### 3.4 Rolling Update Step-by-Step

{{< rawhtml >}}
<style>
.k3btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;transition:background .15s;}
.k3btn-p{background:#1e1e1e;color:#fff;}.k3btn-p:hover{background:#333;}
.k3btn-s{background:transparent;color:#555;border:1px solid #ccc;}.k3btn-s:hover{background:#f0f0f0;}
.k3btn:disabled{opacity:.3;cursor:default;}
.k3info{padding:10px 0 10px 14px;border-left:3px solid #1e1e1e;margin-top:14px;font-size:14px;font-weight:500;color:#1e1e1e;line-height:1.8;min-height:52px;}
</style>
<div style="font-family:system-ui,sans-serif;padding:8px 0;margin:1.5rem 0;">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <button class="k3btn k3btn-s" id="ru-bb" onclick="ruB()">◀ 이전</button>
  <button class="k3btn k3btn-p" id="ru-bn" onclick="ruN()">다음 ▶</button>
  <button class="k3btn k3btn-s" onclick="ruR()">↺ 초기화</button>
  <span id="ru-lbl" style="font-size:13px;color:#999;margin-left:4px;"></span>
</div>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 288" style="width:100%;font-family:inherit;">
  <defs>
    <marker id="ru-ar" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto"><polygon points="0,0 8,3.5 0,7" fill="#888"/></marker>
  </defs>
  <!-- Service -->
  <rect x="16" y="104" width="90" height="62" rx="8" fill="#fde8cc" stroke="#e8a050" stroke-width="1.5"/>
  <text x="61" y="140" fill="#8b4513" font-size="13" font-weight="700" text-anchor="middle" font-family="inherit">Service</text>
  <!-- arrow → RS v1 -->
  <line id="ru-a1" x1="106" y1="122" x2="148" y2="72" stroke="#888" stroke-width="1.5" marker-end="url(#ru-ar)"/>
  <g id="ru-a1x" style="display:none"><line x1="120" y1="107" x2="132" y2="95" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/><line x1="132" y1="107" x2="120" y2="95" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/></g>
  <!-- arrow → RS v2 -->
  <line id="ru-a2" x1="106" y1="152" x2="148" y2="212" stroke="#888" stroke-width="1.5" marker-end="url(#ru-ar)"/>
  <g id="ru-a2x" style="display:none"><line x1="120" y1="167" x2="132" y2="179" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/><line x1="132" y1="167" x2="120" y2="179" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/></g>
  <!-- RS v1 frame -->
  <rect x="150" y="12" width="458" height="118" rx="8" fill="none" stroke="#6ea8d4" stroke-width="1.5" stroke-dasharray="7,4"/>
  <text x="598" y="27" fill="#4472a8" font-size="11" font-weight="700" text-anchor="end" font-family="inherit">ReplicaSet</text>
  <text x="166" y="27" fill="#4472a8" font-size="11" font-family="inherit">v 1.0</text>
  <text id="ru-rs1e" x="379" y="72" fill="#bbb" font-size="12" text-anchor="middle" font-family="inherit" style="display:none">replicas = 0</text>
  <!-- RS v2 frame -->
  <g id="ru-rs2">
    <rect x="150" y="152" width="458" height="118" rx="8" fill="none" stroke="#5aaa7a" stroke-width="1.5" stroke-dasharray="7,4"/>
    <text x="598" y="167" fill="#2d7a4a" font-size="11" font-weight="700" text-anchor="end" font-family="inherit">ReplicaSet</text>
    <text x="166" y="167" fill="#2d7a4a" font-size="11" font-family="inherit">v 1.1</text>
  </g>
  <!-- v1 pods: x=174,314,454 y=34 w=112 h=76 -->
  <g id="ru-v1p1"><rect x="174" y="34" width="112" height="76" rx="6" fill="#d4e4f7" stroke="#6ea8d4" stroke-width="1.5"/>
    <text x="189" y="76" fill="#1a56db" font-size="12" font-weight="600" font-family="inherit">v 1.0</text>
    <text id="ru-v1p1-r" x="267" y="80" fill="#34a853" font-size="22" font-weight="700" text-anchor="middle" font-family="inherit">✓</text>
    <text id="ru-v1p1-s" x="267" y="80" fill="#ea4335" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✕</text>
    <text id="ru-v1p1-t" x="267" y="80" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit" style="display:none">↻</text>
  </g>
  <g id="ru-v1p2"><rect x="314" y="34" width="112" height="76" rx="6" fill="#d4e4f7" stroke="#6ea8d4" stroke-width="1.5"/>
    <text x="329" y="76" fill="#1a56db" font-size="12" font-weight="600" font-family="inherit">v 1.0</text>
    <text id="ru-v1p2-r" x="407" y="80" fill="#34a853" font-size="22" font-weight="700" text-anchor="middle" font-family="inherit">✓</text>
    <text id="ru-v1p2-s" x="407" y="80" fill="#ea4335" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✕</text>
    <text id="ru-v1p2-t" x="407" y="80" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit" style="display:none">↻</text>
  </g>
  <g id="ru-v1p3"><rect x="454" y="34" width="112" height="76" rx="6" fill="#d4e4f7" stroke="#6ea8d4" stroke-width="1.5"/>
    <text x="469" y="76" fill="#1a56db" font-size="12" font-weight="600" font-family="inherit">v 1.0</text>
    <text id="ru-v1p3-r" x="547" y="80" fill="#34a853" font-size="22" font-weight="700" text-anchor="middle" font-family="inherit">✓</text>
    <text id="ru-v1p3-s" x="547" y="80" fill="#ea4335" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✕</text>
    <text id="ru-v1p3-t" x="547" y="80" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit" style="display:none">↻</text>
  </g>
  <!-- v2 pods -->
  <g id="ru-v2p1" style="display:none"><rect x="174" y="174" width="112" height="76" rx="6" fill="#c8e6d4" stroke="#5aaa7a" stroke-width="1.5"/>
    <text x="189" y="216" fill="#137333" font-size="12" font-weight="600" font-family="inherit">v 1.1</text>
    <text id="ru-v2p1-r" x="267" y="220" fill="#34a853" font-size="22" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✓</text>
    <text id="ru-v2p1-s" x="267" y="220" fill="#ea4335" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✕</text>
    <text id="ru-v2p1-t" x="267" y="220" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit" style="display:none">↻</text>
  </g>
  <g id="ru-v2p2" style="display:none"><rect x="314" y="174" width="112" height="76" rx="6" fill="#c8e6d4" stroke="#5aaa7a" stroke-width="1.5"/>
    <text x="329" y="216" fill="#137333" font-size="12" font-weight="600" font-family="inherit">v 1.1</text>
    <text id="ru-v2p2-r" x="407" y="220" fill="#34a853" font-size="22" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✓</text>
    <text id="ru-v2p2-s" x="407" y="220" fill="#ea4335" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✕</text>
    <text id="ru-v2p2-t" x="407" y="220" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit" style="display:none">↻</text>
  </g>
  <g id="ru-v2p3" style="display:none"><rect x="454" y="174" width="112" height="76" rx="6" fill="#c8e6d4" stroke="#5aaa7a" stroke-width="1.5"/>
    <text x="469" y="216" fill="#137333" font-size="12" font-weight="600" font-family="inherit">v 1.1</text>
    <text id="ru-v2p3-r" x="547" y="220" fill="#34a853" font-size="22" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✓</text>
    <text id="ru-v2p3-s" x="547" y="220" fill="#ea4335" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit" style="display:none">✕</text>
    <text id="ru-v2p3-t" x="547" y="220" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit" style="display:none">↻</text>
  </g>
</svg>
<div id="ru-info" class="k3info"></div>
</div>
<script>
(function(){
  const ST=[
    {v1:['r','r','r'],v2:[null,null,null],rs2:0,a1:1,a2:0,e:0,
     info:'초기 상태. v1.0 Pod 3개 모두 정상 운영 중. Service는 v1.0 ReplicaSet으로만 트래픽을 라우팅한다.'},
    {v1:['r','r','r'],v2:['t',null,null],rs2:1,a1:1,a2:0,e:0,
     info:'업데이트 시작. ReplicaSet v1.1 생성, Pod 1개 기동 (↻). maxSurge:1 → 최대 4개 허용. v1.1 Pod 미준비 상태라 트래픽은 아직 v1.0으로만.'},
    {v1:['s','r','r'],v2:['r',null,null],rs2:1,a1:1,a2:1,e:0,
     info:'v1.1 Pod 1번 준비 완료 (readinessProbe ✓). v1.0 Pod 1개 종료 (✕). Service가 v1.1으로도 트래픽 분산 시작.'},
    {v1:['s','r','r'],v2:['r','t',null],rs2:1,a1:1,a2:1,e:0,
     info:'v1.1 두 번째 Pod 기동 시작. 전체 Pod 수: 4개 (maxSurge 허용). 현재 가용: v1.0 × 2, v1.1 × 1.'},
    {v1:['s','s','r'],v2:['r','r',null],rs2:1,a1:1,a2:1,e:0,
     info:'v1.1 두 번째 Pod 준비 완료. v1.0 Pod 하나 더 종료. Pod 수: 3개. 현재 가용: v1.0 × 1, v1.1 × 2.'},
    {v1:['s','s','r'],v2:['r','r','t'],rs2:1,a1:1,a2:1,e:0,
     info:'v1.1 세 번째 Pod 기동 시작. 전체 Pod 수: 4개. 현재 가용: v1.0 × 1, v1.1 × 2.'},
    {v1:['s','s','s'],v2:['r','r','r'],rs2:1,a1:0,a2:1,e:0,
     info:'v1.1 세 번째 Pod 준비 완료. 마지막 v1.0 Pod 종료. 트래픽 전부 v1.1로. v1.0 ReplicaSet은 존재하지만 Service가 더 이상 라우팅하지 않는다.'},
    {v1:[null,null,null],v2:['r','r','r'],rs2:1,a1:0,a2:1,e:1,
     info:'업데이트 완료. ReplicaSet v1.0은 replicas=0 상태로 잔존 — 롤백 시 재사용. <code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;color:#1e1e1e;font-size:13px;">kubectl rollout undo</code>로 즉시 이전 버전 복귀 가능.'},
  ];
  let cur=0;
  const $=id=>document.getElementById(id);
  function pod(pre,i,st){
    const el=$(`ru-${pre}p${i+1}`);
    if(!el)return;
    if(st===null){el.style.display='none';return;}
    el.style.display='block';
    ['r','s','t'].forEach(k=>{const g=$(`ru-${pre}p${i+1}-${k}`);if(g)g.style.display=k===st?'block':'none';});
  }
  function show(id,v){const e=$(id);if(e)e.style.display=v?'block':'none';}
  function render(){
    const s=ST[cur];
    s.v1.forEach((st,i)=>pod('v1',i,st));
    s.v2.forEach((st,i)=>pod('v2',i,st));
    show('ru-rs2',s.rs2); show('ru-a1',s.a1); show('ru-a1x',!s.a1);
    show('ru-a2',s.a2&&s.rs2); show('ru-a2x',!s.a2&&s.rs2); show('ru-rs1e',s.e);
    $('ru-info').innerHTML=s.info;
    $('ru-lbl').textContent=`${cur} / ${ST.length-1}`;
    $('ru-bb').disabled=cur===0; $('ru-bn').disabled=cur===ST.length-1;
  }
  window.ruN=()=>{if(cur<ST.length-1){cur++;render();}};
  window.ruB=()=>{if(cur>0){cur--;render();}};
  window.ruR=()=>{cur=0;render();};
  render();
})();
</script>
{{< /rawhtml >}}

아래는 텍스트로 정리한 전체 흐름이다.

```
STEP 0: v1✅ v1✅ v1✅                         (3개)
STEP 1: v1✅ v1✅ v1✅ | v2🔄                  (4개, maxSurge 허용)
STEP 2: v1✅ v1✅      | v2✅                  (3개, v1 하나 종료)
STEP 3: v1✅ v1✅      | v2✅ v2🔄             (4개)
STEP 4: v1✅           | v2✅ v2✅             (3개, v1 하나 더 종료)
STEP 5: v1✅           | v2✅ v2✅ v2🔄        (4개)
STEP 6:                | v2✅ v2✅ v2✅        (3개, 마지막 v1 종료)
완료:   ReplicaSet v1(replicas=0 대기) | v2✅ v2✅ v2✅
```

업데이트 내내 Pod 수는 2개(최소)와 4개(최대) 사이에서 유지된다. 사용자는 서비스 중단을 느끼지 못한다.

### 3.5 How to Trigger an Update

업데이트를 시작하는 방법은 세 가지다.

```bash
# 1. 새 YAML 파일로 통째로 교체
kubectl replace -f new-deployment.yaml

# 2. 특정 부분만 수정
kubectl patch deployment random-generator \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"random-generator","image":"k8spatterns/random-generator:2.0"}]}}}}'

# 또는 에디터로 직접 수정
kubectl edit deployment random-generator

# 3. 이미지만 바꿀 때 (가장 간단)
kubectl set image deployment/random-generator \
  random-generator=k8spatterns/random-generator:2.0
```

| 방법 | 언제 쓰나 |
|---|---|
| `kubectl replace` | 변경사항이 많을 때 |
| `kubectl patch / edit` | 일부 필드만 수정할 때 |
| `kubectl set image` | 이미지 버전만 바꿀 때 |

### 3.6 Benefits of Deployment

명령형 방식의 단점을 해결하는 것 외에 Deployment는 네 가지 구조적 장점을 가진다.

**서버 측 자동 관리.** 업데이트 전 과정이 서버에서 처리된다. 클라이언트(개발자)의 개입 없이 Kubernetes가 상태를 유지한다.

**선언적 목표 지향.** "어떻게 해라"가 아니라 "이런 상태여야 해"를 선언한다. 도달 방법은 Kubernetes가 결정한다.

**환경 간 재사용.** YAML 파일은 단순 문서가 아니라 실행 가능한 객체다. 개발 → 스테이징 → 운영 환경에서 같은 파일을 그대로 사용할 수 있다.

**버전 관리와 롤백.** 업데이트 과정이 전부 기록되고 버전이 매겨진다. `kubectl rollout history`로 확인하고 `kubectl rollout undo`로 언제든 롤백할 수 있다.

---

## 4. Fixed Deployment (Recreate)

RollingUpdate의 단점은 업데이트 중 두 버전이 동시에 실행된다는 것이다. API가 하위 호환이 되지 않는 변경이 있을 때 문제가 생긴다.

예를 들어 응답 필드명이 `price`에서 `amount`로 바뀌었다면, v1 Pod와 v2 Pod가 공존하는 시간 동안 클라이언트는 어떤 응답이 올지 예측할 수 없다.

이 경우 Recreate 전략을 사용한다.

```yaml
spec:
  strategy:
    type: Recreate    # maxUnavailable = replicas 전체로 설정하는 것과 같음
```

```
BEFORE: v1✅ v1✅ v1✅
           ↓
중간:   v1❌ v1❌ v1❌  ← 전부 종료 (다운타임 발생)
           ↓
AFTER:  v2✅ v2✅ v2✅  ← 전부 동시에 시작
```

Recreate는 `maxUnavailable`을 replicas 수 전체로 설정한 것과 동일하게 동작한다. 기존 Pod를 전부 종료한 뒤 새 Pod를 전부 동시에 시작한다. 중간에 다운타임이 발생하지만, 두 버전이 절대 공존하지 않는다는 것이 보장된다.

| | RollingUpdate | Recreate |
|---|---|---|
| 다운타임 | 없음 | 있음 |
| v1/v2 공존 | 있음 | 없음 |
| API 호환성 문제 | 발생 가능 | 없음 |
| 언제 사용 | 일반적인 업데이트 | API 크게 변경 시 |

---

## 5. Blue-Green Release

Blue-Green은 Kubernetes 기본 제공 전략이 아니다. Deployment와 Service 같은 기본 리소스를 조합해서 구현하는 고급 릴리즈 전략이다.

{{< rawhtml >}}
<style>
.k3btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;transition:background .15s;}
.k3btn-p{background:#1e1e1e;color:#fff;}.k3btn-p:hover{background:#333;}
.k3btn-s{background:transparent;color:#555;border:1px solid #ccc;}.k3btn-s:hover{background:#f0f0f0;}
.k3btn:disabled{opacity:.3;cursor:default;}
.k3info{padding:10px 0 10px 14px;border-left:3px solid #1e1e1e;margin-top:14px;font-size:14px;font-weight:500;color:#1e1e1e;line-height:1.8;min-height:52px;}
</style>
<div style="font-family:system-ui,sans-serif;padding:8px 0;margin:1.5rem 0;">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <button class="k3btn k3btn-s" id="bg-bb" onclick="bgB()">◀ 이전</button>
  <button class="k3btn k3btn-p" id="bg-bn" onclick="bgN()">다음 ▶</button>
  <button class="k3btn k3btn-s" onclick="bgR()">↺ 초기화</button>
  <span id="bg-lbl" style="font-size:13px;color:#999;margin-left:4px;"></span>
</div>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 280" style="width:100%;font-family:inherit;">
  <defs>
    <marker id="bg-ar" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto"><polygon points="0,0 8,3.5 0,7" fill="#888"/></marker>
    <marker id="bg-ar-act" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto"><polygon points="0,0 8,3.5 0,7" fill="#1e1e1e"/></marker>
  </defs>
  <rect x="240" y="12" width="140" height="52" rx="8" fill="#fff" stroke="#e0e0e0" stroke-width="1.5" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.08))"/>
  <text x="310" y="36" fill="#1e1e1e" font-size="13" font-weight="700" text-anchor="middle" font-family="inherit">Service</text>
  <text id="bg-sel" x="310" y="52" fill="#aaa" font-size="10" text-anchor="middle" font-family="inherit">selector: version=v1.0</text>
  <line id="bg-abl" x1="280" y1="64" x2="210" y2="108" stroke="#1e1e1e" stroke-width="2" marker-end="url(#bg-ar-act)"/>
  <g id="bg-ablx" style="display:none"><line x1="236" y1="84" x2="248" y2="96" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/><line x1="248" y1="84" x2="236" y2="96" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/></g>
  <line id="bg-agl" x1="340" y1="64" x2="410" y2="108" stroke="#ccc" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#bg-ar)"/>
  <g id="bg-aglx" style="display:none"><line x1="372" y1="84" x2="384" y2="96" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/><line x1="384" y1="84" x2="372" y2="96" stroke="#ea4335" stroke-width="2.5" stroke-linecap="round"/></g>
  <g id="bg-blue">
    <rect x="20" y="110" width="270" height="140" rx="10" fill="#e8f0fe" stroke="#4285f4" stroke-width="1.5"/>
    <text x="155" y="128" fill="#1a56db" font-size="12" font-weight="700" text-anchor="middle" font-family="inherit">Blue (v1.0)</text>
    <rect x="40" y="142" width="70" height="82" rx="6" fill="#c5d8f8" stroke="#4285f4" stroke-width="1"/>
    <text x="75" y="168" fill="#1a56db" font-size="11" font-weight="600" text-anchor="middle" font-family="inherit">v 1.0</text>
    <text id="bg-b1" x="75" y="198" fill="#34a853" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit">✓</text>
    <rect x="120" y="142" width="70" height="82" rx="6" fill="#c5d8f8" stroke="#4285f4" stroke-width="1"/>
    <text x="155" y="168" fill="#1a56db" font-size="11" font-weight="600" text-anchor="middle" font-family="inherit">v 1.0</text>
    <text id="bg-b2" x="155" y="198" fill="#34a853" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit">✓</text>
    <rect x="200" y="142" width="70" height="82" rx="6" fill="#c5d8f8" stroke="#4285f4" stroke-width="1"/>
    <text x="235" y="168" fill="#1a56db" font-size="11" font-weight="600" text-anchor="middle" font-family="inherit">v 1.0</text>
    <text id="bg-b3" x="235" y="198" fill="#34a853" font-size="20" font-weight="700" text-anchor="middle" font-family="inherit">✓</text>
  </g>
  <g id="bg-green">
    <rect x="330" y="110" width="270" height="140" rx="10" fill="#e6f4ea" stroke="#34a853" stroke-width="1.5"/>
    <text x="465" y="128" fill="#137333" font-size="12" font-weight="700" text-anchor="middle" font-family="inherit">Green (v1.1)</text>
    <rect x="350" y="142" width="70" height="82" rx="6" fill="#b8dfca" stroke="#34a853" stroke-width="1"/>
    <text x="385" y="168" fill="#137333" font-size="11" font-weight="600" text-anchor="middle" font-family="inherit">v 1.1</text>
    <text id="bg-g1" x="385" y="198" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit">↻</text>
    <rect x="430" y="142" width="70" height="82" rx="6" fill="#b8dfca" stroke="#34a853" stroke-width="1"/>
    <text x="465" y="168" fill="#137333" font-size="11" font-weight="600" text-anchor="middle" font-family="inherit">v 1.1</text>
    <text id="bg-g2" x="465" y="198" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit">↻</text>
    <rect x="510" y="142" width="70" height="82" rx="6" fill="#b8dfca" stroke="#34a853" stroke-width="1"/>
    <text x="545" y="168" fill="#137333" font-size="11" font-weight="600" text-anchor="middle" font-family="inherit">v 1.1</text>
    <text id="bg-g3" x="545" y="198" fill="#4285f4" font-size="20" text-anchor="middle" font-family="inherit">↻</text>
  </g>
</svg>
<div id="bg-info" class="k3info"></div>
</div>
<script>
(function(){
  const ST=[
    {sel:'selector: version=v1.0',abl:1,ablx:0,agl:0,aglx:0,blueOpacity:1,blue:['✓','✓','✓'],green:['↻','↻','↻'],info:'Blue(v1.0)는 트래픽을 받는 중. Green(v1.1)은 별도 Deployment로 준비 중.'},
    {sel:'selector: version=v1.0',abl:1,ablx:0,agl:0,aglx:0,blueOpacity:1,blue:['✓','✓','✓'],green:['✓','✓','✓'],info:'Green(v1.1) Pod 3개가 모두 준비 완료. 아직 트래픽은 Blue로만 향함.'},
    {sel:'selector: version=v1.1',abl:0,ablx:1,agl:1,aglx:0,blueOpacity:0.4,blue:['✓','✓','✓'],green:['✓','✓','✓'],info:'Service selector를 <code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;color:#1e1e1e;font-size:12px;">version=v1.1</code>로 변경. 트래픽이 즉시 Green으로 전환된다.'},
    {sel:'selector: version=v1.1',abl:0,ablx:0,agl:1,aglx:0,blueOpacity:0.15,blue:['✕','✕','✕'],green:['✓','✓','✓'],info:'Blue Deployment 삭제 완료. 리소스 반환. 다음 배포 시 Green → Blue 방향으로 동일 절차 반복.'},
  ];
  let cur=0;
  const $=id=>document.getElementById(id);
  function show(id,v){const e=$(id);if(e)e.style.display=v?'block':'none';}
  function render(){
    const s=ST[cur];
    $('bg-sel').textContent=s.sel;
    const abl=$('bg-abl'), agl=$('bg-agl');
    if(abl){ abl.style.display=s.abl?'block':'none'; abl.setAttribute('stroke', s.abl?'#1e1e1e':'#ccc'); abl.setAttribute('marker-end', s.abl?'url(#bg-ar-act)':'url(#bg-ar)'); }
    if(agl){ agl.style.display='block'; agl.setAttribute('stroke', s.agl?'#1e1e1e':'#ccc'); agl.setAttribute('marker-end', s.agl?'url(#bg-ar-act)':'url(#bg-ar)'); agl.setAttribute('stroke-dasharray', s.agl?'none':'5,3'); }
    show('bg-ablx', s.ablx); show('bg-aglx', s.aglx);
    const blueGrp=$('bg-blue'); if(blueGrp) blueGrp.style.opacity=s.blueOpacity;
    ['b1','b2','b3'].forEach((id,i)=>{ const e=$("bg-"+id); if(e){ e.textContent=s.blue[i]; e.setAttribute('fill', s.blue[i]==='✓' ? '#34a853' : s.blue[i]==='↻' ? '#4285f4' : '#ea4335'); }});
    ['g1','g2','g3'].forEach((id,i)=>{ const e=$("bg-"+id); if(e){ e.textContent=s.green[i]; e.setAttribute('fill', s.green[i]==='✓' ? '#34a853' : '#4285f4'); }});
    $('bg-info').innerHTML=s.info;
    $('bg-lbl').textContent=`${cur+1} / ${ST.length}`;
    $('bg-bb').disabled=cur===0; $('bg-bn').disabled=cur===ST.length-1;
  }
  window.bgN=()=>{if(cur<ST.length-1){cur++;render();}};
  window.bgB=()=>{if(cur>0){cur--;render();}};
  window.bgR=()=>{cur=0;render();};
  render();
})();
</script>
{{< /rawhtml >}}

구현 방식은 다음과 같다.

```yaml
# Blue Deployment (기존 v1.0)
metadata:
  name: app-blue
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: random-generator
        version: v1.0       # Blue 식별 라벨

# Green Deployment (새 v1.1)
metadata:
  name: app-green
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: random-generator
        version: v1.1       # Green 식별 라벨
```

```yaml
# Service - selector 변경으로 트래픽 전환
spec:
  selector:
    app: random-generator
    version: v1.0    # → v1.1로 바꾸면 즉시 Green으로 전환
```

전환 흐름은 다음과 같다.

```
STEP 1: Green Deployment 생성 (별도 주문서 제출)
STEP 2: Green Pod 전부 준비 완료 확인
STEP 3: Service selector: v1.0 → v1.1 (트래픽 즉시 전환)
STEP 4: 문제 없으면 Blue Deployment 삭제
        문제 있으면 selector를 v1.0으로 되돌리면 즉시 롤백
```

| | 내용 |
|---|---|
| 장점 | 한 버전만 서비스 → 클라이언트 단순, 즉시 롤백 가능 |
| 단점 1 | 두 환경이 동시에 뜨는 동안 리소스 2배 필요 |
| 단점 2 | 오래 실행 중인 프로세스나 DB 스키마 변경 시 복잡성 증가 |

---

## 6. Canary Release

Canary는 전체 Pod 중 일부만 새 버전으로 교체해서 소수의 사용자가 먼저 경험하게 하는 전략이다. 새 버전에 문제가 없다고 확인되면 나머지를 교체한다.

광산에서 유독가스 감지를 위해 카나리아 새를 먼저 들여보내던 데서 이름이 유래했다.

구현은 두 개의 Deployment를 사용한다.

```yaml
# 기존 Deployment (v1) - replicas 많음
metadata:
  name: app-v1
spec:
  replicas: 4

# Canary Deployment (v2) - replicas 적음
metadata:
  name: app-v2
spec:
  replicas: 1    # 전체의 20%만
```

두 Deployment가 같은 라벨을 공유하면 Service가 자동으로 트래픽을 분산한다.

```
전체 5개 Pod 중:
v1 Pod 4개 → 트래픽 80%
v2 Pod 1개 → 트래픽 20%
```

확인 후 전환 과정은 다음과 같다.

```bash
# v2 문제없으면 점진적 전환
kubectl scale deployment app-v2 --replicas=5
kubectl scale deployment app-v1 --replicas=0

# v2 문제 있으면 즉시 롤백
kubectl delete deployment app-v2
```

Canary와 RollingUpdate는 겉보기에 비슷하지만 목적이 다르다.

| | RollingUpdate | Canary |
|---|---|---|
| 목적 | 빠른 전체 교체 | 안전한 검증 후 교체 |
| 전환 주체 | Kubernetes 자동 | 사람이 판단 |
| 모니터링 | 없음 | 각 단계마다 확인 |
| 트래픽 조절 | 불가 | 가능 |

---

## 7. Strategy Comparison

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.5rem 0;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 320" style="width:100%;font-family:system-ui,sans-serif;">
  <defs>
    <marker id="dc-arr" markerWidth="7" markerHeight="6" refX="6" refY="3" orient="auto">
      <polygon points="0,0 7,3 0,6" fill="#bbb"/>
    </marker>
  </defs>

  <!-- 헤더 행 -->
  <rect x="10" y="10" width="700" height="36" rx="6" fill="#f4f4f4" stroke="#e0e0e0" stroke-width="1"/>
  <text x="90" y="33" fill="#aaa" font-size="12" font-weight="600" font-family="inherit">전략</text>
  <text x="230" y="33" fill="#aaa" font-size="12" font-weight="600" text-anchor="middle" font-family="inherit">다운타임</text>
  <text x="340" y="33" fill="#aaa" font-size="12" font-weight="600" text-anchor="middle" font-family="inherit">두 버전 공존</text>
  <text x="460" y="33" fill="#aaa" font-size="12" font-weight="600" text-anchor="middle" font-family="inherit">자동화</text>
  <text x="570" y="33" fill="#aaa" font-size="12" font-weight="600" text-anchor="middle" font-family="inherit">리소스</text>
  <text x="670" y="33" fill="#aaa" font-size="12" font-weight="600" text-anchor="middle" font-family="inherit">K8s 기본</text>

  <!-- RollingUpdate -->
  <rect x="10" y="56" width="700" height="54" rx="6" fill="#fff" stroke="#e0e0e0" stroke-width="1"/>
  <text x="30" y="79" fill="#1e1e1e" font-size="13" font-weight="700" font-family="inherit">RollingUpdate</text>
  <text x="30" y="97" fill="#aaa" font-size="11" font-family="inherit">기본 전략</text>
  <text x="230" y="87" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">없음 ✓</text>
  <text x="340" y="87" fill="#ea4335" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">있음</text>
  <text x="460" y="87" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">완전 자동 ✓</text>
  <text x="570" y="87" fill="#1e1e1e" font-size="13" text-anchor="middle" font-family="inherit">보통</text>
  <text x="670" y="87" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">✓</text>

  <!-- Recreate -->
  <rect x="10" y="120" width="700" height="54" rx="6" fill="#fff" stroke="#e0e0e0" stroke-width="1"/>
  <text x="30" y="143" fill="#1e1e1e" font-size="13" font-weight="700" font-family="inherit">Recreate</text>
  <text x="30" y="161" fill="#aaa" font-size="11" font-family="inherit">Fixed Deployment</text>
  <text x="230" y="151" fill="#ea4335" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">있음</text>
  <text x="340" y="151" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">없음 ✓</text>
  <text x="460" y="151" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">완전 자동 ✓</text>
  <text x="570" y="151" fill="#1e1e1e" font-size="13" text-anchor="middle" font-family="inherit">보통</text>
  <text x="670" y="151" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">✓</text>

  <!-- Blue-Green -->
  <rect x="10" y="184" width="700" height="54" rx="6" fill="#fff" stroke="#e0e0e0" stroke-width="1"/>
  <text x="30" y="207" fill="#1e1e1e" font-size="13" font-weight="700" font-family="inherit">Blue-Green</text>
  <text x="30" y="225" fill="#aaa" font-size="11" font-family="inherit">고급 릴리즈 전략</text>
  <text x="230" y="215" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">없음 ✓</text>
  <text x="340" y="215" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">없음 ✓</text>
  <text x="460" y="215" fill="#ea4335" font-size="13" text-anchor="middle" font-family="inherit">사람 개입</text>
  <text x="570" y="215" fill="#ea4335" font-size="13" text-anchor="middle" font-family="inherit">2배</text>
  <text x="670" y="215" fill="#ea4335" font-size="13" text-anchor="middle" font-family="inherit">✕</text>

  <!-- Canary -->
  <rect x="10" y="248" width="700" height="54" rx="6" fill="#fff" stroke="#e0e0e0" stroke-width="1"/>
  <text x="30" y="271" fill="#1e1e1e" font-size="13" font-weight="700" font-family="inherit">Canary</text>
  <text x="30" y="289" fill="#aaa" font-size="11" font-family="inherit">고급 릴리즈 전략</text>
  <text x="230" y="279" fill="#34a853" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">없음 ✓</text>
  <text x="340" y="279" fill="#ea4335" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">있음 (의도적)</text>
  <text x="460" y="279" fill="#ea4335" font-size="13" text-anchor="middle" font-family="inherit">사람 개입</text>
  <text x="570" y="279" fill="#1e1e1e" font-size="13" text-anchor="middle" font-family="inherit">보통</text>
  <text x="670" y="279" fill="#ea4335" font-size="13" text-anchor="middle" font-family="inherit">✕</text>
</svg>
</div>
{{< /rawhtml >}}

기본 전략(RollingUpdate, Recreate)은 Kubernetes가 완전 자동으로 처리한다. 고급 전략(Blue-Green, Canary)은 전환 시점을 사람이 판단해야 하며, Kubernetes가 직접 지원하지 않는다.

---

## 8. Higher-Level Deployments

Deployment는 RollingUpdate와 Recreate만 기본 제공한다. Blue-Green과 Canary를 선언적으로 자동화하려면 별도 플랫폼이 필요하다.

이 플랫폼들은 모두 Operator 패턴(Chapter 28)을 기반으로 동작한다. 새로운 커스텀 리소스 타입을 도입해 롤아웃 동작을 선언하면, Operator가 서버 측에서 필요한 작업을 처리한다. 일부는 업데이트 오류 시 자동 롤백도 지원한다.

**Flagger.** Flux CD GitOps 도구의 일부다. 카나리와 Blue-Green 배포를 지원하며, 인그레스 컨트롤러와 서비스 메시와 통합해 트래픽 분할을 처리한다. 커스텀 메트릭으로 롤아웃 상태를 모니터링하고 실패 시 자동 롤백한다.

**Argo Rollouts.** Argo CD GitOps 생태계의 일부로, Kubernetes를 위한 CD 솔루션이다. Flagger와 기능이 유사하며, 인그레스 컨트롤러와 서비스 메시를 지원한다. Flagger와 Argo Rollouts 중 선택은 어떤 GitOps 플랫폼을 사용하는지에 따라 결정하면 된다.

**Knative.** Kubernetes 위의 서버리스 플랫폼이다. 트래픽 기반 오토스케일링이 핵심 기능이며(Chapter 29), 트래픽 분할을 통한 간단한 배포 지원도 제공한다. Flagger나 Argo Rollouts만큼 고급 롤아웃 기능을 제공하지는 않지만, 이미 Knative를 사용하는 환경이라면 별도 도구 없이 활용할 수 있다.

세 프로젝트 모두 CNCF(Cloud Native Computing Foundation) 소속이다.

---

## 9. Q & A

### Q1. Deployment와 Pod를 직접 만드는 것의 차이

Pod를 직접 생성하면 해당 Pod가 종료될 때 아무도 살려주지 않는다. Deployment를 사용하면 Pod가 죽어도 Kubernetes가 자동으로 새 Pod를 만들어 선언된 수를 유지한다. Deployment 없이 Pod를 직접 운영하는 것은 구성 파일 없이 서버를 수동으로 관리하는 것과 같다. 운영 환경에서는 반드시 Deployment를 사용해야 한다.

### Q2. Rolling Update 중 두 버전이 공존하면 문제가 없나

API 응답 구조가 동일하게 유지되는 경우라면 문제없다. 하위 호환성이 보장되는 변경, 예를 들어 기존 필드를 유지하면서 새 필드를 추가하는 경우가 이에 해당한다. 반면 기존 필드를 삭제하거나 이름을 변경하는 등 하위 호환이 깨지는 변경이라면 두 버전 공존이 클라이언트 오류를 유발한다. 이 경우 Recreate 또는 Blue-Green 전략을 선택해야 한다.

### Q3. Blue-Green과 Canary의 선택 기준

두 전략 모두 두 버전 공존 문제를 해결하지만 방식이 다르다.

Blue-Green은 전환이 순간적으로 이루어진다. 신버전이 완전히 준비된 후 트래픽을 한꺼번에 전환하므로, 전환 중 두 버전이 동시에 트래픽을 받는 시간이 없다. 대신 리소스가 일시적으로 2배 필요하다.

Canary는 소수 사용자에게 먼저 노출해서 실제 트래픽으로 검증한 뒤 점진적으로 전환한다. 리소스 효율은 좋지만 검증 기간 동안 두 버전이 공존한다. API가 크게 바뀌었다면 Blue-Green이 맞고, 새 버전의 안정성을 실사용자로 검증하면서 위험을 최소화하고 싶다면 Canary가 맞다.