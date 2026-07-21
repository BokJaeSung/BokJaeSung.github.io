---
series: ["K8sPatterns"]
title: "K8sPatterns.04 Health Probe Pattern"
date: 2026-06-29T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "health-probe"]
cover:
  image: 'images/cover.jpg'
  alt: 'Kubernetes.01 Health Probe Pattern'
  relative: true
summary: "A deep dive into Kubernetes Health Probe pattern: Process Health Check, Liveness Probe, and Readiness Probe for building self-healing cloud-native applications."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-why-health-probe" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Why Health Probe?</a></div>
  <div><a href="#3-process-health-check" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Process Health Check</a></div>
  <div><a href="#4-liveness-probe" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Liveness Probe</a></div>
  <div><a href="#5-readiness-probe" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. Readiness Probe</a></div>
  <div><a href="#6-sigterm과-readiness" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. SIGTERM과 Readiness</a></div>
  <div><a href="#7-전체-비교-정리" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. 전체 비교 정리</a></div>
  <div><a href="#8-deployment에서-실제-사용" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">8. Deployment에서 실제 사용</a></div>
  <div><a href="#9-custom-pod-readiness-gates" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">9. Custom Pod Readiness Gates</a></div>
  <div><a href="#10-startup-probe" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">10. Startup Probe</a></div>
  <div><a href="#11-example-4-4-jakarta-ee--wildfly" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">11. Example 4-4 (Jakarta EE / WildFly)</a></div>
  <div><a href="#12-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">12. Discussion</a></div>
</div>
</div>
{{< /rawhtml >}}

## 1. Overview

```
애플리케이션 상태 감지 체계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Process Health Check
  └─► 프로세스 생존 여부 (기본 제공)

Liveness Probe
  └─► 실제 동작 여부 감지 → 실패 시 재시작

Readiness Probe
  └─► 요청 처리 가능 여부 → 실패 시 트래픽 차단
```

---

## 2. Why Health Probe?

클라우드 네이티브 환경에서 핵심 철학은 하나다.

> **"장애를 피하는 것" → "감지하고 복구하는 것"**

버그 없는 코드는 없다. 분산 애플리케이션에서 장애 가능성은 더욱 높아진다.  
그래서 Kubernetes는 애플리케이션 상태를 외부에서 지속적으로 감시하고, 문제를 자동으로 처리한다.

### 프로세스 상태 체크만으로 부족한 이유

프로세스 살아있음 ≠ 애플리케이션 정상

| 상황 | 프로세스 | 실제 상태 |
|---|---|---|
| OutOfMemoryError (Java) | 🟢 Running | 🔴 비정상 |
| 무한루프 (Infinite Loop) | 🟢 Running | 🔴 비정상 |
| 데드락 (Deadlock) | 🟢 Running | 🔴 비정상 |
| 스래싱 (Thrashing) | 🟢 Running | 🔴 비정상 |

---

## 3. Process Health Check

Kubelet이 기본으로 제공하는 가장 단순한 체크.  
별도 설정 없이 자동으로 동작한다.

```
Kubelet
  └─► 컨테이너 프로세스 생존 여부 (PID 존재 여부)
        ├─► 살아있음 → 아무것도 안 함
        └─► 죽어있음 → 컨테이너 재시작 🔄
```

**한계:** 프로세스가 살아있지만 실제로는 동작 불능인 상황을 감지하지 못한다.

---

## 4. Liveness Probe

Kubelet이 **외부에서** 주기적으로 컨테이너에게 "아직 살아있냐?" 고 묻는다.  
실패 시 컨테이너를 재시작한다.

### 왜 외부 체크가 중요한가?

```
❌ 내부 감시 (Watchdog)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
데드락 발생
  └─► 감시 스레드도 같이 멈춤
        └─► 장애 보고 불가 ❌

✅ 외부 감시 (Kubelet)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
데드락 발생
  └─► Kubelet이 독립적으로 체크
        └─► 응답 없음 감지 → 재시작 ✅
```

### Probe 방법 4가지

| Probe 종류 | 동작 방식 |
|---|---|
| HTTP Probe | GET 요청 → 200~399 응답 → 정상 |
| TCP Socket | TCP 연결 성공 → 정상 |
| Exec Probe | 명령어 실행 → 종료코드 0 → 정상 |
| gRPC Probe | gRPC Health Check → SERVING → 정상 |

### 선택 가이드

```
REST API / 웹서버   → HTTP Probe
DB / TCP 서버       → TCP Socket Probe
gRPC 서비스         → gRPC Probe
커스텀 로직 필요    → Exec Probe
```

### 주요 파라미터

| 파라미터 | 설명 |
|---|---|
| `initialDelaySeconds` | 앱이 뜨고 나서 첫 체크까지 대기 시간 |
| `periodSeconds` | 체크 주기 (초) |
| `timeoutSeconds` | 응답 대기 최대 시간 |
| `failureThreshold` | 몇 번 연속 실패 시 재시작할지 |

**타임라인 예시**

```
0초  : 컨테이너 시작
       │
       │ initialDelaySeconds: 30초 대기
       │
30초 : 첫 번째 체크
35초 : 두 번째 체크 (periodSeconds: 5) ← 실패 1회
40초 : 세 번째 체크                     ← 실패 2회
45초 : 네 번째 체크                     ← 실패 3회
       │
       └─► failureThreshold 도달 → 재시작 🔄
```

### Example 4-1

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-liveness-check
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    env:
    - name: DELAY_STARTUP
      value: "20"             # 앱 내부에서 20초 후 실제 시작 (초기화 지연 시뮬레이션)
    ports:
    - containerPort: 8080
      protocol: TCP
    livenessProbe:
      httpGet:
        path: /actuator/health  # Spring Boot Actuator 헬스 엔드포인트
        port: 8080
      initialDelaySeconds: 30   # DELAY_STARTUP(20)보다 길게 설정 — 앱이 뜨기 전에 체크하면 불필요한 재시작 반복
      # periodSeconds 미설정 → 기본값 10초마다 체크
      # failureThreshold 미설정 → 기본값 3회 연속 실패 시 재시작
```

**핵심 포인트:** `initialDelaySeconds(30) > DELAY_STARTUP(20)`  
앱이 완전히 뜨기 전에 체크하면 불필요한 재시작이 반복된다.

### DELAY_STARTUP 환경변수란?

`DELAY_STARTUP`은 Kubernetes 기본 기능이 아니라 `k8spatterns/random-generator` 이미지가 자체적으로 만든 환경변수다.  
앱 내부 코드가 이 값을 읽어 `Thread.sleep(20초)` 로 시작을 의도적으로 지연시킨다.

**교재 데모용 설정**으로 "느리게 시작하는 앱"을 시뮬레이션하기 위한 것이다. 실무에서는 Spring Boot, WildFly 같은 프레임워크가 원래 자체적으로 느리게 뜨기 때문에 이런 변수가 필요 없다.

```
DELAY_STARTUP: 20초        ← 앱이 뜨는 데 걸리는 시간
initialDelaySeconds: 30초  ← Probe가 기다리는 시간

30 > 20 → 앱이 완전히 뜨고 나서 체크 시작 ✅

반대라면?
initialDelaySeconds: 10 < DELAY_STARTUP: 20
→ 앱 아직 시작 중인데 체크 → 실패 → 재시작 💥
```

---

## 5. Readiness Probe

컨테이너가 **요청을 받을 준비가 됐는지** 체크한다.  
실패 시 컨테이너를 재시작하는 게 아니라, **트래픽만 차단**한다.

> 트래픽 = 클라이언트가 Pod에게 보내는 HTTP 요청들

### Liveness vs Readiness 핵심 차이

|  | Liveness Probe | Readiness Probe |
|---|---|---|
| 실패 시 조치 | 컨테이너 재시작 | 트래픽 차단 |
| 컨테이너 상태 | 종료 후 교체 | 살아있음 유지 |
| 언제 쓰나 | 앱 자체가 망가짐 | 외부 요인이 문제 |

### 재시작이 답이 아닌 상황들

**1. 앱 초기화 중**
```
재시작하면?  초기화 → 또 초기화 → 또 초기화 → 무한루프 💥
기다리면?    초기화 완료 → 트래픽 수신 ✅
```

**2. DB 연결 대기**
```
재시작하면?  앱 재시작해도 DB가 빨리 뜨지 않음 → 무의미한 재시작 💥
기다리면?    DB 준비 완료 → 자동으로 연결 → 트래픽 수신 ✅
```

**3. 과부하 상태**
```
재시작하면?  재시작하자마자 또 트래픽 폭증 → 또 과부하 💥
기다리면?    트래픽 차단 → 다른 Pod가 분산 처리 → 부하 감소 → 정상화 ✅
```

**4. 외부 API 장애**
```
재시작하면?  내가 재시작한다고 카카오페이 API가 복구되지 않음 💥
기다리면?    API 복구 대기 → 복구됨 → 트래픽 수신 ✅
```

### 트래픽 차단 동작 원리

```
[ 클라이언트 ]
      │
      ▼
[ Service ]
      │
      ├─► Pod 1 ✅ 트래픽 수신
      ├─► Pod 2 🚫 Readiness 실패 → 트래픽 차단 (컨테이너는 살아있음)
      └─► Pod 3 ✅ 트래픽 수신
```

### Example 4-2 (파일 기반 Readiness Probe)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-readiness-check
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    readinessProbe:
      exec:
        # stat 명령어로 파일 존재 여부 확인
        # 파일 있음 → 종료코드 0 → Readiness 통과 → 트래픽 수신
        # 파일 없음 → 종료코드 1 → Readiness 실패 → 트래픽 차단
        command: [ "stat", "/var/run/random-generator-ready" ]
      # initialDelaySeconds 미설정 → 기본값 0초 (컨테이너 시작 즉시 체크 시작)
      # 앱이 파일을 생성하기 전까지는 계속 Readiness 실패 → 정상 동작
```

**동작 원리:**

```
컨테이너 시작
  │
  │ 앱 초기화 중 (파일 없음)
  │ stat → 파일 없음 → 종료코드 1 ❌ → 트래픽 차단
  │
  앱 초기화 완료
  │
  └─► 앱이 파일 생성
      touch /var/run/random-generator-ready 📄
        │
        stat → 파일 있음 → 종료코드 0 ✅ → 트래픽 수신
```

앱이 파일을 생성/삭제하는 것만으로 트래픽을 직접 제어할 수 있다.

### Probe 파라미터 기본값

명시적으로 설정하지 않으면 Kubernetes가 아래 기본값을 적용한다.

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `initialDelaySeconds` | 0초 | 시작 즉시 체크 |
| `periodSeconds` | 10초 | 10초마다 체크 |
| `timeoutSeconds` | 1초 | 1초 안에 응답 없으면 실패 |
| `failureThreshold` | 3회 | 3번 연속 실패 시 조치 |
| `successThreshold` | 1회 | 1번 성공하면 정상 판단 |

Example 4-2는 파라미터를 생략했으므로 모두 기본값이 적용된다. 기본값 기준으로 타임라인을 보면:

```
0초  : 컨테이너 시작 → 즉시 첫 체크
       파일 없음 ❌ (실패 1)
10초 : 파일 없음 ❌ (실패 2)
20초 : 파일 없음 ❌ (실패 3) → Readiness 실패 확정 → 트래픽 차단 🚫

       앱 초기화 완료 → 파일 생성 📄

30초 : 파일 있음 ✅ (성공 1) → successThreshold 달성 → 트래픽 수신 시작 ✅
```

---

## 6. SIGTERM과 Readiness

`SIGTERM`은 Kubernetes가 Pod를 종료할 때 컨테이너에게 보내는 "이제 종료해" 신호다.

SIGTERM을 받는 순간 Kubernetes는 **Readiness 결과와 무관하게** 즉시 트래픽을 차단한다.  
개발자가 따로 Readiness 실패 처리를 하지 않아도 종료 중인 Pod로 새 요청이 들어가는 일은 없다.

```
Pod 종료 결정
  │
  ├─► ① 트래픽 차단 🚫   ← 동시에
  └─► ② SIGTERM 전송     ← 동시에
        │
        새 요청은 다른 Pod로
        현재 처리 중인 요청만 마무리 (graceful shutdown)
        │
        컨테이너 종료 완료 ✅
```

### Readiness가 통과 중인데 종료되면?

Readiness가 아직 통과 중(정상 상태)이어도 SIGTERM을 받는 순간 트래픽이 차단된다.  
"Readiness 통과 중 = 트래픽 수신 중"이라는 생각과 달리, **종료 신호가 Readiness보다 우선**한다.

---

## 7. 전체 비교 정리

| 상황 | 재시작 | 트래픽 차단 |
|---|---|---|
| 앱 초기화 중 | ❌ 무의미 | ✅ 정답 |
| DB 준비 대기 | ❌ 무의미 | ✅ 정답 |
| 과부하 | ❌ 무의미 | ✅ 정답 |
| 외부 API 장애 | ❌ 무의미 | ✅ 정답 |
| 데드락 / 무한루프 | ✅ 정답 | ❌ 무의미 |
| OOM | ✅ 정답 | ❌ 무의미 |

핵심: 앱 자체가 망가진 경우 → Liveness → 재시작, 외부 요인이 문제인 경우 → Readiness → 트래픽 차단

---

## 8. Deployment에서 실제 사용

교재 예시는 Pod 단독 YAML이지만, 실무에서는 Deployment 안에 작성한다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3                   # Pod 3개 운영 — 1개가 Readiness 실패해도 나머지 2개로 트래픽 처리
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - image: k8spatterns/random-generator:1.0
        name: random-generator
        env:
        - name: DELAY_STARTUP
          value: "20"           # 앱이 20초 후 실제 시작
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /actuator/health  # 앱이 살아있는지 체크하는 엔드포인트
            port: 8080
          initialDelaySeconds: 30   # DELAY_STARTUP(20)보다 길게 — 너무 짧으면 시작 전에 재시작 반복
          periodSeconds: 10         # 10초마다 체크
          timeoutSeconds: 5         # 5초 안에 응답 없으면 실패로 간주
          failureThreshold: 3       # 3회 연속 실패 시 컨테이너 재시작 (총 30초 유예)
        readinessProbe:
          exec:
            command: [ "stat", "/var/run/random-generator-ready" ]  # 앱이 준비되면 이 파일을 직접 생성
          initialDelaySeconds: 5    # liveness보다 짧게 — 앱 준비 완료를 빠르게 감지
          periodSeconds: 10         # 10초마다 파일 존재 여부 확인
```

`livenessProbe`와 `readinessProbe`는 컨테이너당 각각 1개씩 설정한다.  
컨테이너가 여러 개라면 각 컨테이너마다 독립적으로 설정한다.

---

## 9. Custom Pod Readiness Gates

### 기존 Readiness의 한계

Readiness Probe는 컨테이너 단위로 동작한다. 모든 컨테이너가 통과하면 Pod는 Ready로 판단하고 트래픽을 수신한다.  
그런데 **AWS Load Balancer 같은 외부 인프라도 재설정이 필요한 경우**라면 이것만으로 부족하다.

```
컨테이너들 Readiness ✅
AWS Load Balancer 재설정 중... ⏳
        │
        └─► Pod는 Ready로 판단 → 트래픽 수신 시작 💥
              (로드밸런서가 아직 준비 안됨)
```

### Readiness Gates

`readinessGates` 필드로 Pod가 Ready가 되기 위한 **추가 조건**을 선언한다.  
이 조건은 외부 Controller가 관리하며, 직접 `True`로 변경해줘야 한다.

```
기존:
  모든 컨테이너 Readiness ✅ → Pod Ready

Readiness Gates 추가 후:
  모든 컨테이너 Readiness ✅
  + 외부 조건 (Controller가 True로 변경) ✅
        │
        └─► Pod Ready
```

### Example 4-3

```yaml
apiVersion: v1
kind: Pod
spec:
  readinessGates:
  - conditionType: "k8spatterns.io/load-balancer-ready"
    # 추가 조건 선언 — 이 조건도 True여야 Pod가 Ready

status:
  conditions:
  - type: "k8spatterns.io/load-balancer-ready"
    status: "False"   # 기본값 False — 외부 Controller가 True로 바꿔줘야 함
  - type: Ready
    status: "False"   # 위 조건이 False이므로 Pod도 NotReady
```

### 동작 흐름

```
Pod 시작
  │
  ├─► 컨테이너 Readiness 통과 ✅
  │
  ├─► readinessGates 조건 확인
  │       └─► k8spatterns.io/load-balancer-ready = False ❌
  │
  └─► Pod = NotReady 🚫 (트래픽 차단)
              │
              외부 Controller가 AWS LB 상태 감시
              LB 설정 완료 → 조건을 True로 변경
              │
              k8spatterns.io/load-balancer-ready = True ✅
              │
              Pod = Ready ✅ → 트래픽 수신 시작
```

### 일반 Readiness vs Readiness Gates

| | 일반 Readiness | Readiness Gates |
|---|---|---|
| 체크 대상 | 컨테이너 내부 | 외부 시스템까지 |
| 판단 주체 | Kubelet | 외부 Controller |
| 조건 변경 | Probe 결과 자동 반영 | 외부에서 직접 변경 |
| 사용 상황 | DB 연결, 초기화 등 | AWS LB, Istio 등 외부 인프라 연동 |

Pod Ready 조건 = 모든 컨테이너 Readiness + 모든 readinessGates 조건. 둘 다 충족해야 진짜 Ready다.

---

## 10. Startup Probe

### Liveness와 Readiness가 같은 체크를 할 때

많은 앱이 두 Probe에 같은 경로를 쓴다. 그래도 둘 다 설정하는 이유는 **역할이 다르기 때문**이다.  
Readiness가 있으면 초기화가 끝날 때까지 트래픽을 막아 **시작할 시간**을 확보해준다.

### Rolling Update와 Readiness

Deployment 롤링 업데이트 시, **새 Pod의 Readiness를 통과해야만 이전 Pod를 종료**한다.

```
v1 Pod 3개 실행 중
  [v1] [v1] [v1]

v2 배포 시작
  [v1] [v1] [v2 시작 중...]
                │
                Readiness 통과 ✅ → v1 하나 종료
                │
  [v1] [v2] [v2 시작 중...]
                │
                Readiness 통과 ✅ → v1 마지막 종료
                │
  [v2] [v2] [v2]  완료!
```

Readiness가 없으면 v2가 준비되기 전에 v1이 종료되어 요청 처리 실패가 발생한다.

### 문제: Liveness만으로 느린 앱을 해결하려 할 때

`initialDelaySeconds`를 늘리거나 `failureThreshold`를 크게 잡으면 느린 시작을 버틸 수 있다.  
하지만 이 파라미터는 **운영 중에도 그대로 적용**된다.

```
Liveness만 사용 시 (느슨한 파라미터)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
periodSeconds: 30, failureThreshold: 10

운영 중 치명적 오류 발생
  └─► 30초 × 10번 = 최대 300초(5분) 후에야 재시작 💥
        (5분 동안 장애 방치)
```

Startup Probe로 시작 단계와 운영 단계를 **분리**하면 각각 최적의 파라미터를 쓸 수 있다.

```
[시작 단계] Startup Probe  → periodSeconds: 30, failureThreshold: 10 (느슨하게)
[운영 단계] Liveness Probe → periodSeconds: 10, failureThreshold: 3  (빠르게)
```

### Startup Probe 동작

Startup Probe가 성공하기 전까지 **Liveness/Readiness 체크를 아예 시작하지 않는다**.

```
컨테이너 시작
  │
  Startup Probe 동작 (Liveness/Readiness 대기 중 ⏳)
  │
  체크... 실패 ← 아직 초기화 중
  체크... 실패
  │
  초기화 완료 → Startup Probe 성공 ✅
  │
  이제부터 Liveness/Readiness 시작 → 정상 운영
```

### 마커 파일 패턴

HTTP 엔드포인트는 앱이 완전히 뜬 후에야 응답한다. Startup Probe에는 **파일 존재 여부**가 더 정확한 시작 완료 신호다.

```
앱 내부: 시작 완료 → touch /tmp/started  (마커 파일 생성)

startupProbe:
  exec:
    command: ["stat", "/tmp/started"]   → 파일 있으면 성공 ✅
```

### 세 가지 Probe 역할 정리

| | 언제 동작하나 | 실패 시 조치 |
|---|---|---|
| Startup Probe | 시작 중에만 (성공하면 종료) | 재시작 |
| Liveness Probe | 운영 중 계속 | 재시작 |
| Readiness Probe | 운영 중 계속 | 트래픽 차단 |

---

## 11. Example 4-4 (Jakarta EE / WildFly)

WildFly는 Jakarta EE 서버로 시작에 수 분이 걸린다. 시작 완료 시 마커 파일을 자동 생성한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-startup-check
spec:
  containers:
  - image: quay.io/wildfly/wildfly
    name: wildfly

    startupProbe:
      exec:
        command: [ "stat", "/opt/jboss/wildfly/standalone/tmp/startup-marker" ]
        # WildFly가 시작 완료 시 자동 생성하는 마커 파일
        # HTTP 엔드포인트는 아직 응답 불가 → 파일 체크가 더 정확
      initialDelaySeconds: 60   # 60초 대기 후 첫 체크 (WildFly 최소 기동 시간)
      periodSeconds: 60         # 60초마다 체크
      failureThreshold: 15      # 최대 15번 실패 허용
                                # 총 대기 시간: 60 + (60 × 15) = 최대 960초(약 16분)

    livenessProbe:
      httpGet:
        path: /health
        port: 9990              # WildFly 관리 포트 (일반 앱 포트와 다름)
      periodSeconds: 10         # Startup 성공 후 10초마다 빠르게 체크
      failureThreshold: 3       # 3번(30초) 실패 시 즉시 재시작 — 운영 중 장애는 빠르게 처리
```

### 타이밍 계산

| | 계산 | 결과 |
|---|---|---|
| Startup 최대 대기 | 60 + (60 × 15) | 960초 (약 16분) |
| Liveness 재시작까지 | 10 × 3 | 30초 |

Startup으로 느린 시작을 허용하고, Liveness는 빠른 파라미터로 유지해 운영 중 장애를 빠르게 처리한다.

### 전체 타임라인

```
0초   : WildFly 컨테이너 시작
         Startup Probe 대기 / Liveness 대기 ⏳
         │
60초  : Startup 1번째 체크 → 마커 파일 없음 ❌
120초 : Startup 2번째 체크 → 마커 파일 없음 ❌
         │
         WildFly 기동 완료!
         startup-marker 파일 자동 생성 📄
         │
180초 : Startup 3번째 체크 → 파일 있음 ✅ → Startup 성공!
         │
         Liveness Probe 시작 (GET /health:9990, 10초마다)
         정상 운영 모드 🚀
```

### Health Probe 완전 정리

Startup → Liveness/Readiness 순서로 동작하며, 셋 모두 Kubelet이 **외부에서** 독립적으로 체크한다.  
앱이 내부에서 망가져도 감지 가능하고, 자동 복구(Self-Healing)가 실현된다.

---

## 12. Discussion

완전한 자동화를 위해 클라우드 네이티브 앱은 플랫폼이 상태를 읽고 해석하고 수정 조치를 취할 수 있도록 **높은 관찰 가능성(Observability)** 을 제공해야 한다.  
Health Probe는 그 중 가장 기본이지만, 컨테이너가 상태를 드러내는 수단은 더 있다.

### 컨테이너 관찰 수단

```
[ 컨테이너 ]
    │
    ├─► Health Probes        → Kubernetes가 자동 조치
    │       ├─► Liveness     → 재시작
    │       ├─► Readiness    → 트래픽 차단
    │       └─► Startup      → 시작 완료 대기
    │
    ├─► Logging              → 사람이 분석
    │       ├─► stdout/stderr           → 중앙 로그 수집
    │       └─► /dev/termination-log   → 종료 직전 마지막 기록
    │
    └─► Metrics & Tracing    → 고급 모니터링
            ├─► Prometheus   → 메트릭 수집/시각화
            └─► OpenTracing  → 마이크로서비스 간 분산 추적
```

### Logging

로깅은 자동 조치용이 아니라 **사람이 분석**하는 수단이다. 장애 사후 분석과 눈에 안 띄는 오류 감지에 유용하다.

- `stdout/stderr` 로 출력 → 중앙 로그 수집 시스템(ELK, Grafana Loki 등)으로 전송
- `/dev/termination-log` → 컨테이너가 종료되기 직전 이유를 기록. `kubectl describe pod` 에서 확인 가능

```
echo "DB 연결 실패로 종료" > /dev/termination-log
exit 1

# kubectl describe pod
# Last State: Terminated
#   Message: "DB 연결 실패로 종료"
```

### 관찰 수단별 비교

| | Health Probe | Logging | Metrics |
|---|---|---|---|
| 자동 조치 | ✅ 가능 | ❌ 불가 | ❌ 불가 |
| 사람이 분석 | 가능 | ✅ 주목적 | ✅ 가능 |
| 실시간 감지 | ✅ 빠름 | 느림 | ✅ 빠름 |
| 사후 분석 | 제한적 | ✅ 최적 | ✅ 가능 |
| 필수 여부 | ✅ 필수 | ✅ 권장 | 선택 |

### 클라우드 네이티브 앱 최소 요건

기본 (필수): Liveness/Readiness Probe 제공, stdout/stderr 로깅, `/dev/termination-log` 기록  
고급 (권장): Prometheus 메트릭 노출, OpenTracing 분산 추적, 구조화된 로그(JSON)

### 핵심 철학

컨테이너는 내부 구현을 숨긴 블랙박스처럼 다뤄진다. 그러나 플랫폼이 관찰하고 자동 관리할 수 있도록 **상태를 드러내는 API는 반드시 구현**해야 한다.

Health Probe(앱 → Kubernetes 방향)와 다음 챕터의 Managed Lifecycle 패턴(Kubernetes → 앱 방향)이 합쳐져 완전한 양방향 소통이 완성된다.