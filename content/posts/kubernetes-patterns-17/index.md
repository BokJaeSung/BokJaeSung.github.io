---
series: ["K8sPatterns"]
title: "K8sPatterns.17 Adapter"
date: 2026-07-31T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "patterns"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.17 Adapter'
  relative: true
summary: "메인 앱을 건드리지 않고 외부 인터페이스를 통일하는 법 — Adapter 패턴으로 이질적인 컨테이너 시스템이 하나의 표준 얼굴을 갖는 방식을 이해한다."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-이질성이-만드는-충돌" style="color:var(--secondary,inherit);text-decoration:none;">2.1 이질성이 만드는 충돌</a></div>
    <div><a href="#22-모니터링-관점의-문제" style="color:var(--secondary,inherit);text-decoration:none;">2.2 모니터링 관점의 문제</a></div>
  </div>
  <div><a href="#3-solution--adapter-패턴" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution — Adapter 패턴</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-동작-구조" style="color:var(--secondary,inherit);text-decoration:none;">3.1 동작 구조</a></div>
    <div><a href="#32-예제--prometheus-모니터링" style="color:var(--secondary,inherit);text-decoration:none;">3.2 예제 — Prometheus 모니터링</a></div>
    <div><a href="#33-example-17-1-yaml-분석" style="color:var(--secondary,inherit);text-decoration:none;">3.3 Example 17-1 YAML 분석</a></div>
    <div><a href="#34-로깅에-적용하기" style="color:var(--secondary,inherit);text-decoration:none;">3.4 로깅에 적용하기</a></div>
  </div>
  <div><a href="#4-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-리버스-프록시로서의-adapter" style="color:var(--secondary,inherit);text-decoration:none;">4.1 리버스 프록시로서의 Adapter</a></div>
    <div><a href="#42-sidecar-패턴-3형제" style="color:var(--secondary,inherit);text-decoration:none;">4.2 Sidecar 패턴 3형제</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Adapter Pattern - Core Idea
==================================================

Heterogeneous system: each service speaks its own format
                    |
                    v
       Add an Adapter sidecar container in the same Pod
       (reads internal format → exposes standard format)
                    |
      +-------------+-------------+
      v                           v
  Main Container              Adapter Container
  (core logic, any format)    (translation only)
  no code changes needed      replaceable independently
                    |
                    v
       External system sees ONE unified interface
```

컨테이너는 서로 다른 언어와 라이브러리로 만들어진 앱을 통일된 방식으로 실행한다. 하지만 실행 환경이 통일됐다고 해서 **내부 데이터 형식**까지 통일되는 건 아니다. 팀마다 다른 기술을 쓰고, 서비스마다 메트릭과 로그를 각자의 방식으로 출력한다.

**Adapter 패턴**은 이 문제에 대한 해답이다. 메인 앱을 전혀 수정하지 않고, 옆에 Adapter 컨테이너를 붙여 복잡한 내부 형식을 외부 세계가 이해할 수 있는 **표준 인터페이스**로 변환한다. 전원 어댑터처럼 — 기기(메인 앱)는 그대로이고, 어댑터만으로 호환성을 확보한다.

---

## 2. Problem

### 2.1 이질성이 만드는 충돌

분산 시스템에서는 각 서비스가 서로 다른 형식으로 데이터를 출력하는 것이 자연스럽다.

```
서비스 A (Java)    →  JMX 형식 메트릭
서비스 B (Python)  →  StatsD 형식 메트릭
서비스 C (Node.js) →  custom JSON 형식 메트릭

           ↓

모니터링 서버 (Prometheus)
"모두 다른 형식인데, 어떻게 수집하지?"
```

외부 시스템이 모든 형식을 각각 파싱해야 한다면, 서비스가 늘어날수록 부담이 기하급수적으로 늘어난다. 이것이 **이질성(Heterogeneity)** 이 만드는 충돌이다.

### 2.2 모니터링 관점의 문제

모니터링 도구는 **시스템 전체의 통합된 뷰**를 기대한다. 그런데 서비스마다 메트릭을 노출하는 포맷도, 프로토콜도 다르다면 단일 모니터링 솔루션으로 전체를 바라보는 것이 불가능해진다.

```
Before (Adapter 없음):
  모니터링 서버 → 서비스A (XML 파싱 필요)
  모니터링 서버 → 서비스B (JSON 파싱 필요)
  모니터링 서버 → 서비스C (Plaintext 파싱 필요)
  ↑ 모니터링 서버가 모든 형식을 알아야 함

After (Adapter 적용):
  서비스A → [Adapter] → 표준 형식 ┐
  서비스B → [Adapter] → 표준 형식 ┼→ 모니터링 서버
  서비스C → [Adapter] → 표준 형식 ┘
  ↑ 모니터링 서버는 하나의 형식만 알면 됨
```

두 가지 문제가 있다. 첫째, **형식 불일치** — 앱의 출력 형식이 모니터링 도구가 기대하는 형식과 다르다. 둘째, **접근 방식 불일치** — Prometheus처럼 HTTP 엔드포인트로 스크랩해야 하는데, 앱이 HTTP를 지원하지 않는다.

---

## 3. Solution — Adapter 패턴

### 3.1 동작 구조

Adapter 컨테이너는 Sidecar 패턴 위에서 동작한다. 같은 Pod 안에서 메인 앱과 볼륨을 공유하며, **단 하나의 목적** — 형식 변환과 표준 인터페이스 노출 — 에만 집중한다.

```
+---------------------------------------------+
|                    Pod                       |
|   +------------------+  +-----------------+  |
|   |    Main App      |  |    Adapter      |  |
|   |  (any language)  |  |   (sidecar)     |  |
|   |                  |  |                 |  |
|   |  writes metrics/ |  |  1. read log    |  |
|   |  logs in its own |  |  2. transform   |  |
|   |  custom format   |  |  3. expose HTTP |  |
|   +--------+---------+  +--------+--------+  |
|            |                     |           |
|            +----------+----------+           |
|              shared volume (emptyDir)        |
+---------------------------------------------+
                              |
                   GET /metrics (standard format)
                              |
                 monitoring server / log aggregator
```

각 컨테이너의 단일 책임이 명확하다.

| 컨테이너 | 역할 | 모르는 것 |
|---|---|---|
| **Main App** | 비즈니스 로직 수행 + 커스텀 형식 출력 | 외부 모니터링 도구의 존재 |
| **Adapter** | 내부 형식 → 표준 형식 변환 + HTTP 노출 | 메인 앱의 비즈니스 로직 |

### 3.2 예제 — Prometheus 모니터링

랜덤 숫자 생성기 앱을 Prometheus로 모니터링하는 시나리오다. 앱은 숫자를 생성하는 데 걸린 시간을 로그 파일에 기록한다.

```
메인 앱이 출력하는 로그 형식:
  2024-01-15 10:23:45 duration=0.0023s value=42

Prometheus가 기대하는 형식:
  # HELP random_duration 랜덤 숫자 생성 소요 시간
  # TYPE random_duration gauge
  random_duration 0.0023
```

두 가지 문제가 있다. 형식이 다르고, HTTP 엔드포인트가 없다. Adapter가 둘 다 해결한다.

```
① 메인 앱  →  /logs/random.log 에 커스텀 형식 기록
              (emptyDir 공유 볼륨)
② Adapter  →  GET /metrics 요청 수신 시
              /logs/random.log 읽기
              → Prometheus 형식으로 변환
              → HTTP 응답 반환
③ Prometheus → :9889/metrics 스크랩
              → 시계열 DB 저장
```

Adapter는 **요청이 올 때만** 로그를 읽는다. Prometheus의 Pull 방식과 자연스럽게 맞아떨어지는 구조다.

### 3.3 Example 17-1 YAML 분석

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: random-generator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: random-generator
  template:
    metadata:
      labels:
        app: random-generator
    spec:
      containers:
      # ① 메인 앱 컨테이너 — 랜덤 숫자 서비스, 8080 포트
      - image: k8spatterns/random-generator:1.0
        name: random-generator
        env:
        - name: LOG_FILE
          value: /logs/random.log     # 로그 경로를 환경변수로 관리
        ports:
        - containerPort: 8080         # 서비스 트래픽 포트
          protocol: TCP
        volumeMounts:
        - mountPath: /logs
          name: log-volume            # 이 경로에 로그 파일 작성

      # ② Adapter 컨테이너 — Prometheus 형식으로 변환, 9889 포트
      - image: k8spatterns/random-generator-exporter
        name: prometheus-adapter
        env:
        - name: LOG_FILE
          value: /logs/random.log     # 메인 앱과 동일한 경로 (같은 파일 읽기)
        ports:
        - containerPort: 9889         # 모니터링 스크랩 포트
          protocol: TCP
        volumeMounts:
        - mountPath: /logs
          name: log-volume            # 같은 볼륨 마운트

      volumes:
      - name: log-volume
        emptyDir: {}                  # Pod 생성 시 빈 디렉토리 자동 생성
```

설계 포인트가 세 가지 있다.

**포트 분리** — 서비스 트래픽(:8080)과 모니터링(:9889)이 완전히 독립되어 있어 서로 간섭하지 않는다.

**환경변수로 경로 관리** — `LOG_FILE`을 두 컨테이너 모두 환경변수로 관리한다. 경로가 바뀌어도 YAML만 수정하면 되고, 하드코딩이 없다.

**emptyDir의 역할** — Pod 생성 시 자동으로 빈 디렉토리가 만들어지고, 두 컨테이너가 같은 경로(`/logs`)로 마운트한다. 메인 앱이 쓰면 Adapter가 읽는다. 두 컨테이너를 연결하는 유일한 접점이다.

```
포트 역할 구분:

외부 사용자/클라이언트
      ↓
   :8080  ←  random-generator (랜덤 숫자 서비스)

Prometheus Server
      ↓
   :9889  ←  prometheus-adapter (메트릭 스크랩)
```

### 3.4 로깅에 적용하기

Adapter 패턴은 메트릭뿐 아니라 **로깅**에도 그대로 적용된다. 각 서비스가 서로 다른 형식과 상세 수준으로 로그를 출력하는 문제를 해결한다.

Adapter는 세 가지 작업을 수행한다.

**정규화(Normalize)** — 서로 다른 형식의 로그를 통일된 구조로 변환한다.

```
Java:   "2024-01-15 10:23:45 [ERROR] NullPointerException"
Python: {"level":"error","msg":"KeyError","ts":1705312345}

           ↓ Adapter 정규화

{"timestamp":"2024-01-15T10:23:45Z","level":"ERROR","message":"..."}
{"timestamp":"2024-01-15T10:23:45Z","level":"ERROR","message":"..."}
```

**정리(Clean up)** — DEBUG, TRACE 같은 노이즈를 제거하고, 민감 정보를 마스킹한다.

**보강(Enrich)** — Chapter 14의 **Self Awareness 패턴**을 함께 활용한다. Downward API로 Pod 자신의 메타데이터를 환경변수로 받아, 로그에 컨텍스트를 자동으로 추가한다.

```yaml
# Self Awareness 패턴 — Downward API
env:
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
- name: NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
```

```
Before (컨텍스트 없음):
  {"level":"ERROR","message":"NullPointerException"}

After (Self Awareness로 보강):
  {
    "level":     "ERROR",
    "message":   "NullPointerException",
    "pod":       "random-generator-7d6b9c-xk2p9",
    "node":      "worker-node-1",
    "namespace": "production"
  }
```

메인 앱은 Prometheus도, ELK도, Fluentd도 모른다. Adapter만 교체하면 모니터링 도구를 바꿀 수 있다.

---

## 4. Discussion

### 4.1 리버스 프록시로서의 Adapter

Adapter는 Sidecar 패턴의 특수화다. 그리고 외부 시스템 관점에서 보면 **리버스 프록시**이기도 하다.

```
일반 프록시 (Forward Proxy):
  클라이언트 → [Proxy] → 외부 서버
  "내가 외부로 나갈 때 대리인"

리버스 프록시 (Adapter):
  외부 시스템 → [Adapter] → 내부 앱
  "외부가 들어올 때, 복잡한 내부를 숨기는 대리인"
```

Adapter 뒤에 어떤 언어, 어떤 형식의 앱이 있든 외부 시스템은 신경 쓰지 않아도 된다. **복잡성을 숨기고, 통합된 인터페이스만 노출한다.** 이것이 Adapter의 본질이다.

이름을 구분하는 이유도 여기에 있다. "Sidecar 컨테이너 추가했어요"라고 하면 무엇을 하는지 알 수 없다. "Adapter 컨테이너 추가했어요"라고 하면 **형식 변환과 인터페이스 통일**이 목적임을 즉시 전달한다. 패턴 이름 자체가 설계 의도를 전달하는 언어다.

### 4.2 Sidecar 패턴 3형제

Sidecar 패턴에서 파생된 세 가지 패턴을 나란히 보면 관계가 명확해진다.

```
Sidecar 패턴 (범용 — Chapter 16)
│
├── Adapter 패턴 (Chapter 17)
│   방향: 외부 → 내부 (Reverse Proxy)
│   목적: 이질적인 내부를 표준 인터페이스로 노출
│   예시: Prometheus exporter, 로그 정규화기
│
└── Ambassador 패턴 (Chapter 18)
    방향: 내부 → 외부 (Forward Proxy)
    목적: 외부 서비스 연결을 내부에서 추상화
    예시: DB 프록시, API 게이트웨이
```

| 구분 | Sidecar | Adapter | Ambassador |
|---|---|---|---|
| **역할** | 보조 기능 일반 | 형식 변환 특화 | 외부 연결 특화 |
| **방향** | 내부 지원 | 외부→내부 (Reverse) | 내부→외부 (Forward) |
| **목적** | 다양 | 인터페이스 통일 | 외부 서비스 추상화 |
| **예시** | 로그 수집, 모니터링 | Prometheus 변환 | DB 연결, API 게이트웨이 |

> Adapter 패턴의 핵심은 **"메인 앱이 외부를 전혀 몰라도 된다는 것"** 이다.
> 앱은 자기 언어로 자기 형식대로 데이터를 출력하고,
> Adapter가 모든 변환 책임을 전담한다.
> 이것이 클라우드 네이티브에서 이질적인 시스템들을 하나로 묶는 방법이다.