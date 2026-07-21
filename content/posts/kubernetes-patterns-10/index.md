---
series: ["K8sPatterns"]
title: "K8sPatterns.10 Singleton Service"
date: 2026-07-13T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "singleton"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.10 Singleton Service'
  relative: true
summary: "분산 환경에서 단 하나의 인스턴스만 활성화되도록 보장하는 방법 — Out-of-Application Locking부터 분산 락, PodDisruptionBudget까지."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div><a href="#3-solution" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-active-active-vs-active-passive" style="color:var(--secondary,inherit);text-decoration:none;">3.1 Active-Active vs Active-Passive</a></div>
  </div>
  <div><a href="#4-out-of-application-locking" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Out-of-Application Locking</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#42-replicaset-방식의-한계" style="color:var(--secondary,inherit);text-decoration:none;">4.1 ReplicaSet 방식의 한계</a></div>
    <div><a href="#43-statefulset" style="color:var(--secondary,inherit);text-decoration:none;">4.2 StatefulSet</a></div>
  </div>
  <div><a href="#5-in-application-locking" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. In-Application Locking</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-apache-zookeeper-ephemeral-node" style="color:var(--secondary,inherit);text-decoration:none;">5.1 Apache ZooKeeper: Ephemeral Node</a></div>
  </div>
  <div><a href="#6-poddisruptionbudget" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. PodDisruptionBudget</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#방식별-최종-선택-기준" style="color:var(--secondary,inherit);text-decoration:none;">6.1 방식별 최종 선택 기준</a></div>
  </div>
  <div><a href="#7-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. Discussion</a></div>
</div>
</div>
{{< /rawhtml >}}

## 1. Overview

```
Kubernetes의 인스턴스 수 제어 방향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ReplicaSet (replicas: N)  → 여러 개 동시 실행 (Active-Active)
Singleton Service         → 딱 하나만 Active    ← 이번 챕터!
PodDisruptionBudget       → 최소 N개는 항상 유지
```

Singleton Service 패턴은 **동시에 활성화되는 서비스 인스턴스를 하나로 제한**하기 위한 패턴이다. 스케일 아웃이 기본인 Kubernetes에서, 역설적으로 "하나만 실행"을 보장하는 메커니즘을 다룬다.

---

## 2. Problem

Kubernetes의 강점 중 하나는 Pod를 여러 개(레플리카) 띄워 처리량과 가용성을 높이는 것이다.

```
레플리카를 늘리면:
처리량 ↑  (여러 Pod가 동시에 요청 처리)
가용성 ↑  (하나 죽어도 나머지가 처리)
```

그런데 현실에는 이런 요구사항도 있다.

> "여러 인스턴스가 동시에 실행되면 안 된다."

예를 들어:

- **주기적 작업(Scheduler)**: 3개 Pod가 떠 있으면 같은 배치 작업이 3번 실행된다
- **폴링(Polling)**: 파일시스템/DB를 여러 Pod가 동시에 읽고 처리하면 중복 처리 발생
- **순서 보장 메시지 컨슈머**: 단일 스레드로 순서대로 소비해야 하는데 여러 인스턴스가 나눠 가져가면 순서가 깨진다

이런 경우 **동시에 Active인 인스턴스를 정확히 1개로 제한**해야 한다.

---

## 3. Solution

근본적으로 싱글톤은 두 가지 수준에서 구현할 수 있다.

```
싱글톤 구현 방법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Out-of-Application Locking  → 앱 외부(Kubernetes)가 제어
                               앱은 자신이 싱글톤인지 모름

In-Application Locking      → 앱 코드 내부에서 직접 제어
                               분산 락으로 스스로 보장
```

### 3.1 Active-Active vs Active-Passive

일반 레플리카는 모든 인스턴스가 동시에 요청을 처리하는 **Active-Active** 토폴로지다. 싱글톤이 필요한 경우에는 **Active-Passive** 토폴로지가 필요하다.

```
Active-Active (일반 레플리카)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Service]
  ├──► Pod1 (Active)
  ├──► Pod2 (Active)
  └──► Pod3 (Active)   ← 모두 동시 처리

Active-Passive (싱글톤 목표)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pod1 (Active)   ← 실제 작업 수행
Pod2 (Passive)  ← 대기
Pod3 (Passive)  ← 대기
```

---

## 4. Out-of-Application Locking

이름 그대로 **애플리케이션 외부의 관리 프로세스**가 싱글톤을 보장한다. 앱 코드는 자신이 싱글톤으로 실행되는지조차 모른다.

Spring Framework의 싱글톤 빈과 같은 원리다. 클래스 코드에는 "나는 싱글톤이야"라는 코드가 없지만, Spring이 외부에서 딱 하나만 생성해 관리한다.

```
Out-of-Application 방식의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
앱 코드  →  "그냥 실행될 뿐, 싱글톤인지 모름"
Kubernetes →  "이 앱은 1개만 실행해야 해" (외부에서 강제)

관심사 분리 (Separation of Concerns):
앱 코드     → 비즈니스 로직만 집중
외부 관리자  → 인스턴스 수 제어
```

### 4.1 ReplicaSet + replicas: 1

Kubernetes에서 Out-of-Application 싱글톤을 구현하는 가장 단순한 방법은 `replicas: 1`로 Pod를 시작하는 것이다. 단, **이것만으로는 고가용성이 보장되지 않는다.**

```
단순 Pod 1개 실행:
Pod1 💀  →  죽으면 끝, 아무도 살려주지 않음 ❌

ReplicaSet + replicas: 1:
Pod1 💀  →  ReplicaSet이 즉시 감지
            "1개 있어야 하는데 0개네!"
            →  Pod2 자동 생성 ✅
```

ReplicaSet은 `replicas`라는 **목표값**을 24시간 감시하며 유지하는 관리자다. Pod 자체가 아니라 Kubernetes 안에서 동작하는 별도의 컨트롤러 오브젝트다.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: my-singleton
spec:
  replicas: 1          # 외부에서 1개로 제한 — 앱 코드 수정 없음
  selector:
    matchLabels:
      app: my-singleton
  template:
    ...
```

이 토폴로지는 정확히 Active-Passive는 아니다(Passive 인스턴스가 없다). 그러나 Kubernetes가 **항상 1개의 Pod가 실행되도록 보장**하기 때문에 동일한 효과를 낸다.

헬스 체크(Chapter 4, Health Probe)와 결합하면 Pod 장애 시 자동으로 치유(healing)되어 고가용성 싱글톤에 가까워진다.

### 4.2 ReplicaSet 방식의 한계

주의해야 할 점이 두 가지 있다.

**첫째, 실수로 레플리카 수가 늘어날 수 있다.**

```
누군가 kubectl scale --replicas=3 실행
→  Kubernetes가 막아주지 않음
→  싱글톤 즉시 깨짐 ❌
```

플랫폼 수준에서 레플리카 수 변경을 막는 메커니즘이 없다.

**둘째, "항상 정확히 1개"는 사실이 아니다.**

ReplicaSet은 **가용성(Availability)을 일관성(Consistency)보다 우선**시한다. 즉, `at most 1`이 아니라 `at least 1` 의미론을 적용한다.

```
at most 1 (ReplicaSet이 하지 않는 것):
Pod1 완전히 죽은 거 확인 후 → Pod2 생성
(그 사이 잠깐 0개 감수)

at least 1 (ReplicaSet이 실제 하는 것):
일단 Pod2 먼저 생성 → 나중에 Pod1 제거
(잠깐 2개 동시 실행 감수)
```

가장 흔한 케이스는 **노드 네트워크 단절**이다.

```
정상:
클러스터 ────── Node A
                 └── Pod1 (Active) ✅

Node A 단절:
클러스터 ── X ── Node A (Pod1 살아있지만 연락 안됨)
              ↓ "죽었다고 판단"
클러스터 ────── Node B
                 └── Pod2 (새로 생성) ✅

결과: Pod1 + Pod2 일시적 동시 실행 ⚠️
```

이 외에도 레플리카 수 변경, Pod 노드 이동 시에도 일시적으로 2개가 실행될 수 있다. 이는 무상태(Stateless) 앱에는 문제없지만, 싱글톤이 필요한 앱에는 치명적일 수 있다.

### 4.3 StatefulSet

ReplicaSet이 느슨한 싱글톤 보장을 제공한다면, **StatefulSet은 엄격한 싱글톤 보장**을 제공한다.

```
ReplicaSet:  가용성 우선 → 잠깐 2개 허용 (at least 1)
StatefulSet: 일관성 우선 → 잠깐 0개 허용 (exactly 1)

노드 단절 시:
ReplicaSet  → 구 Pod 종료 확인 안 하고 새 Pod 생성
StatefulSet → 구 Pod 완전히 종료 확인 후 새 Pod 생성
```

```
중복 실행이 더 무서운가?  →  StatefulSet
서비스 중단이 더 무서운가?  →  ReplicaSet
```

StatefulSet은 Stateful 애플리케이션을 위해 설계되었으며, 더 강력한 싱글톤 보장을 포함한 많은 기능을 제공한다. 단, 복잡도도 함께 올라간다. 자세한 내용은 Chapter 11에서 다룬다.

싱글톤 Pod가 외부로부터 **들어오는 연결(Incoming Connection)** 을 수락해야 할 때는 Service 리소스가 필요하다. StatefulSet으로 관리되는 싱글톤 Pod처럼 Pod가 하나뿐이고 안정적인 네트워크 ID가 있는 경우, 일반 ClusterIP Service 대신 **Headless Service**(`clusterIP: None`)가 더 적합하다.

```
일반 Service (ClusterIP):
[가상 IP] → kube-proxy → Pod    (로드밸런싱, 중간 레이어 존재)

Headless Service:
[DNS 조회] → Pod IP 직접 반환  (중간 레이어 없음, 직접 연결)
```

Headless Service는 Pod IP가 바뀌어도 Kubernetes가 DNS 레코드를 자동으로 업데이트해주므로 클라이언트는 항상 현재 Pod에 접근할 수 있다.

---

## 5. In-Application Locking

앱 코드 내부에서 **분산 락(Distributed Lock)** 을 이용해 직접 싱글톤을 보장하는 방식이다.

```
분산 락의 원리:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pod1 시작 → 락 획득 시도 → 성공! → Active ✅ (실제 작업 수행)
Pod2 시작 → 락 획득 시도 → 실패  → Passive ⏳ (락 해제 감시)
Pod3 시작 → 락 획득 시도 → 실패  → Passive ⏳ (락 해제 감시)

Pod1 장애 → 락 자동 해제
Pod2 락 획득 성공 → Active ✅  (즉시 전환)
```

Out-of-Application과 결정적으로 다른 점은, **Passive 인스턴스들이 이미 살아서 대기 중**이라는 것이다. Active 장애 시 새 Pod를 생성할 필요 없이 즉시 Failover된다.

```
Out-of-Application:
Pod 자체를 1개로 제한 → 장애 시 새 Pod 생성 시간 필요

In-Application:
Pod는 여러 개 실행 중, 락을 가진 1개만 Active
→ 장애 시 즉시 전환 ✅
```

클래식 OOP의 싱글톤 패턴과 비교하면 이해가 쉽다.

```
클래식 싱글톤 (단일 프로세스):
private static instance; // 정적 변수에 저장
private 생성자 → 외부 생성 차단
→ "이 프로세스 안에서" 1개 보장

분산 싱글톤 (여러 Pod):
같은 코드가 Pod마다 따로 돌아감
→ 클래식 싱글톤 패턴은 무의미
→ 분산 락으로 "클러스터 전체에서" 1개 보장 필요
```

### 5.1 Apache ZooKeeper: Ephemeral Node

ZooKeeper를 이용한 구현은 **임시 노드(Ephemeral Node)** 를 분산 락으로 사용한다.

```
임시 노드의 특성:
클라이언트 세션이 살아있는 동안만 존재
세션 종료(또는 Pod 장애) 시 → 자동 삭제

→ 이것이 핵심!
   Active Pod가 갑자기 죽어도 락이 자동 해제됨
   데드락(Deadlock) 없음 ✅
```

```
ZooKeeper 분산 락 흐름:

Pod1 → 세션 생성 → /lock 임시 노드 생성 성공 → Active ✅
Pod2 → /lock 생성 시도 → 이미 존재! → Passive (감시 중) ⏳
Pod3 → /lock 생성 시도 → 이미 존재! → Passive (감시 중) ⏳

Pod1 💀 → 세션 종료 → /lock 자동 삭제
Pod2, Pod3 감지 → 동시에 생성 시도
→ 먼저 성공한 쪽이 Active ✅
```

### 5.2 Kubernetes 환경에서의 선택: Etcd + ConfigMap

ZooKeeper 클러스터를 락킹만을 위해 별도로 운영하는 것은 오버헤드다. Kubernetes는 이미 내부적으로 **Etcd**를 쓰고 있다.

```
ZooKeeper 사용 시:
Kubernetes 클러스터 + ZooKeeper 클러스터 따로 관리
→ 관리 포인트 2개, 복잡도 ↑

Etcd 사용 시:
Kubernetes가 이미 내장 → 추가 설치 불필요
Kubernetes API로 바로 접근 가능 ✅
```

Etcd는 **Raft 프로토콜**을 사용해 분산 일관성을 보장하는 키-값 저장소로, 리더 선출(Leader Election) 구현에 필요한 기본 요소를 제공한다.

**Apache Camel**은 한 단계 더 나아가 Etcd API 대신 **Kubernetes의 ConfigMap을 분산 락으로 재활용**한다.

```
ConfigMap의 본래 목적: 앱 설정값 저장
Apache Camel의 활용:   ConfigMap을 락 저장소로 재활용

ConfigMap (락 역할):
data:
  leader: "Pod1"   ← 현재 리더 기록
  version: 42      ← 낙관적 락킹용 버전
```

핵심은 Kubernetes의 **낙관적 락킹(Optimistic Locking)** 보장이다.

```
낙관적 락킹 동작:

Pod1: ConfigMap 읽음 (version: 42) → 업데이트 시도 → 성공! (version: 43)
Pod2: ConfigMap 읽음 (version: 42) → 업데이트 시도 → 실패! (이미 43)
                                                        → 재시도
```

한 번에 하나의 Pod만 ConfigMap을 업데이트할 수 있다는 Kubernetes 보장 덕분에, 추가 인프라 없이 Kubernetes API만으로 리더 선출을 구현할 수 있다.

```
Camel 동작 결과:

Pod1 (Active): Camel 라우트 실행 ✅
Pod2 (Passive): 대기 ⏳
Pod3 (Passive): 대기 ⏳

Pod1 장애 → ConfigMap 갱신 중단
→ Pod2 또는 Pod3 락 획득 → 즉시 Active ✅
```

ZooKeeper, Etcd, Redis, Consul 등 어떤 구현을 쓰든 원리는 같다. **락을 가진 1개만 Active, 나머지는 Passive 대기. Pod 수가 아무리 많아도 비즈니스 로직은 1개만 수행.**

---

## 6. PodDisruptionBudget

싱글톤이 "너무 많으면 안 된다"는 상한선 제어라면, **PodDisruptionBudget(PDB)** 은 "너무 적으면 안 된다"는 하한선 제어다.

```
인스턴스 수 제어 방향
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

많음 ↑  ← 싱글톤 / 리더 선출이 제한 (상한선)
      │
      │  ← 이 범위 안에서 운영
      │
적음 ↓  ← PDB가 제한 (하한선)
```

PDB는 **자발적 중단(Voluntary Disruption)** 시 동시에 내려가는 Pod 수를 제한한다.

```
자발적 중단 (PDB가 제어 가능):
  kubectl drain (노드 유지보수)
  클러스터 스케일 다운
  노드 업그레이드
  → 예측 가능 → PDB로 지연/제한 ✅

비자발적 중단 (PDB가 제어 불가):
  노드 하드웨어 장애
  커널 패닉
  네트워크 단절
  → 예측 불가 → PDB로 막을 수 없음 ❌
```

### Example 10-1. PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: random-generator-pdb
spec:
  selector:
    matchLabels:
      app: random-generator   # 이 라벨을 가진 Pod에 적용
  minAvailable: 2             # 최소 2개는 항상 Running 상태 유지
                              # "80%"처럼 백분율도 가능
```

```
Pod 5개 운영 중, minAvailable: 2 설정 시:

kubectl drain node-1 실행
→ Pod 축출 시도
→ "최소 2개는 살아있어야 함"
→ Pod 5 → 4 → 3 → 2 (여기서 멈춤!)
                    ↑
               PDB 하한선
```

`minAvailable` 대신 `maxUnavailable`을 쓸 수도 있다. 단, **두 필드를 동시에 지정할 수 없다.**

```
minAvailable: 3   →  "최소 3개 유지" = 최대 2개 동시 중단 가능
maxUnavailable: 2 →  "최대 2개 중단" = 최소 3개 유지

결과는 같지만 표현 방식이 다름
둘 중 하나만 선택 — 동시 지정 시 충돌 가능성 있으므로 금지
```

PDB는 **컨트롤러(ReplicaSet, Deployment, StatefulSet 등)가 관리하는 Pod에만 완전히 적용**된다. 컨트롤러 없이 직접 생성한 Bare/Naked Pod에는 제한적으로 동작한다(축출 후 자동 생성이 없으므로 PDB의 의미가 퇴색된다).

PDB가 특히 유용한 상황:

| 상황 | 이유 |
|---|---|
| Etcd, ZooKeeper 클러스터 | 쿼럼(과반수) 유지 필수 |
| Kafka 브로커 | 최소 복제본 수 보장 |
| 결제/금융 서비스 | SLA 기준 처리량 유지 |

```
Etcd 5노드 클러스터, 쿼럼 = 3개:

PDB 없이 drain:
3개 동시 축출 가능 → 쿼럼 미달 → 클러스터 중단 ❌

PDB (minAvailable: 3):
항상 3개 이상 유지 → 쿼럼 항상 보장 ✅
```

---

## 7. Discussion

### 강한 싱글톤 보장이 필요할 때

ReplicaSet은 가용성 우선 설계라 `at-most-one`을 보장하지 않는다. 짧은 시간 2개가 동시에 실행되는 시나리오가 실제로 존재한다.

```
2개가 될 수 있는 상황:
① 노드 네트워크 단절 → 구 Pod 살아있는데 새 Pod 생성
② 레플리카 수 변경 도중
③ Pod 다른 노드로 이동 도중
```

이것이 허용되지 않는다면:

```
StatefulSet 사용:
→ 인프라 수준에서 exactly 1 보장
→ 복잡도 ↑

In-Application Locking 사용:
→ 코드 수준에서 exactly 1 보장
→ 추가 장점: replicas를 실수로 늘려도 싱글톤 유지
             (락은 1개만 획득 가능하므로)
```

### 일부 컴포넌트만 싱글톤이어야 할 때

하나의 애플리케이션 안에 **스케일 가능한 부분**과 **싱글톤이어야 하는 부분**이 함께 있는 경우가 있다.

```
예시: 이커머스 서비스

HTTP API (주문 조회, 상품 검색)  →  스케일 가능 ✅
재고 동기화 폴링                 →  싱글톤 필요 ⚠️
```

Out-of-Application 방식(`replicas: 1`)으로는 전체를 1개로 제한해버려 HTTP API도 스케일 불가다.

```
해결책 1: 컴포넌트 분리 배포
┌──────────────┐   ┌───────────────┐
│ HTTP service │   │ polling       │
│ replicas: N  │   │ replicas: 1   │
└──────────────┘   └───────────────┘
장점: 깔끔한 분리
단점: 배포 복잡도 ↑, 오버헤드 ↑, 항상 실용적이지는 않음

해결책 2: In-Application Locking (권장)
replicas: N으로 스케일 아웃

Pod1: HTTP ✅  + 폴링 Active ✅ (락 보유)
Pod2: HTTP ✅  + 폴링 Passive ⏳
Pod3: HTTP ✅  + 폴링 Passive ⏳

→ HTTP는 3개가 처리 (스케일 아웃 효과) ✅
→ 폴링은 1개만 수행 (싱글톤 보장) ✅
→ Pod1 장애 시 폴링도 즉시 인계 ✅
```

### 방식별 최종 선택 기준

```
싱글톤 방식 선택 가이드
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

잠깐 2개 실행이 허용되는가?
          ↓ YES
ReplicaSet + replicas: 1
(단순, 빠름, 고가용성에 가까움)

          ↓ NO
엄격한 싱글톤이 필요하다

          ↓ 인프라 수준에서 해결하고 싶다
StatefulSet
(exactly 1 보장, 복잡도 중간)

          ↓ 코드 수준에서 해결하거나
            실수로 인한 스케일링도 막고 싶다
In-Application Locking
(ZooKeeper / Etcd / Redis / ConfigMap)
(가장 강력, 복잡도 높음, 즉각 Failover)
```

| | ReplicaSet | StatefulSet | In-Application |
|---|---|---|---|
| 우선순위 | 가용성 | 일관성 | 일관성 |
| 싱글톤 보장 | 느슨함 | 엄격함 | 엄격함 |
| Passive 인스턴스 | 없음 | 없음 | 있음 (대기 중) |
| 장애 시 복구 | 새 Pod 생성 | 새 Pod 생성 | 즉시 전환 ✅ |
| 실수 스케일링 방지 | ❌ | ❌ | ✅ |
| 복잡도 | 낮음 | 중간 | 높음 |

> Singleton Service 패턴의 핵심은 **"실행 중인 인스턴스 수"와 "Active 인스턴스 수"를 분리해서 생각하는 것**이다. 여러 Pod가 떠 있어도 비즈니스 로직을 수행하는 것은 단 하나. In-Application Locking이 이 분리를 가장 명확하게 실현한다.