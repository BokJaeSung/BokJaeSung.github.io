---
series: ["K8sPatterns"]
title: "K8sPatterns.09 Daemon Service"
date: 2026-07-10T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "daemonset", "infrastructure"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.09 Daemon Service'
  relative: true
summary: "DaemonSet ensures one Pod per node for infra daemons — nodeSelector, scheduling evolution from nodeName to nodeAffinity, and comparison with Static Pods."
---
 
## 1. Overview

```
Daemon Service 패턴의 위치
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Deployment  → 원하는 수의 Pod 복제본을 클러스터 어딘가에 배치
DaemonSet   → 모든(또는 특정) 노드에 Pod를 하나씩 배치   ← 이번 챕터!
```

쿠버네티스를 **아파트 단지**로 비유해보자.

- **노드(Node)** = 각 아파트 동
- **일반 Pod** = 빈방이 있는 동에 자유롭게 들어가는 주민
- **DaemonSet** = 관리소가 "각 동마다 꼭 한 명씩 배치하는 경비원"을 두는 규칙

DaemonSet의 핵심은 단 두 가지다.

> **"조건에 맞는 모든 노드에, 빠짐없이, Pod를 하나씩"**

---

## 2. Daemon 이란

### 2.1 OS 수준의 데몬

데몬은 **백그라운드에서 죽지 않고 계속 돌아가는 프로그램**이다. 화면에 창이 뜨지 않고, 컴퓨터가 켜지는 순간 알아서 시작되며, 문제가 생겨도 자동으로 다시 켜진다.

Unix/Linux에서는 이름 끝에 `d`를 붙이는 관례가 있다.

| 이름 | 역할 |
|---|---|
| `httpd` | 웹 서버 |
| `sshd` | 원격 접속 |
| `named` | 도메인 주소 변환(DNS) |

다른 OS에서는 다른 이름으로 부른다 — Windows의 **서비스(Service)**, 메인프레임의 **Started Task / Ghost Job**.

### 2.2 애플리케이션 수준의 데몬 (JVM)

OS에만 있는 개념이 아니다. JVM의 **데몬 스레드**도 같은 원리다.

- 낮은 우선순위로 백그라운드에서 실행
- **가비지 컬렉션(GC)**, 파이널라이제이션 같은 보조 작업 전담
- 메인 프로그램(사용자 스레드)이 종료되면 자신의 작업 완료 여부와 무관하게 함께 종료

```
사용자 스레드 (User Thread)     데몬 스레드 (Daemon Thread)
──────────────────────          ──────────────────────────
높은 우선순위                    낮은 우선순위
앱 수명 제어                     수명 제어 불가
비즈니스 로직 처리                GC, 파이널라이제이션 등 보조 작업
JVM이 종료를 기다림               JVM 종료 시 무시됨
```

핵심은 "눈에 보이지 않는 곳에서 시스템이 잘 돌아가도록 묵묵히 돕는 24시간 백그라운드 일꾼"이라는 점이다. 이 개념이 이제 쿠버네티스로 확장된다.

---

## 3. Problem

클러스터 수준의 인프라 작업이 필요한 경우를 생각해보자.

| 용도 | 예시 |
|---|---|
| 클러스터 스토리지 | Ceph, GlusterFS 에이전트 |
| 로그 수집 | Fluentd, Filebeat |
| 메트릭 수집 | Prometheus Node Exporter |
| 핵심 컴포넌트 | kube-proxy, CNI 플러그인 |

이런 프로그램들의 공통점은 **모든 서버(노드)에 똑같이 설치되어야 한다**는 것이다. 서버가 추가되면 자동으로 그 서버에도 설치되어야 하고, 서버가 제거되면 함께 삭제되어야 한다.

일반 Deployment로는 이를 표현할 수 없다. "원하는 개수"를 지정하는 방식이기 때문에 "모든 노드에 하나씩"이라는 보장이 없다.

---

## 4. Solution: DaemonSet

DaemonSet은 **클러스터의 모든(또는 특정) 노드에 Pod를 하나씩 자동으로 배치하고 유지**하는 리소스다.

```
DaemonSet 배치 구조

[클러스터]
  ├── Node 1  →  Pod (DaemonSet 관리)
  ├── Node 2  →  Pod (DaemonSet 관리)
  ├── Node 3  →  Pod (DaemonSet 관리)
  └── Node 4 (신규 추가)  →  Pod 자동 생성 ✅
```

노드가 추가되면 자동으로 Pod가 생성되고, 노드가 제거되면 해당 Pod도 함께 정리된다. 관리자가 별도로 지시하지 않아도 된다.

### 4.1 ReplicaSet vs DaemonSet

비유로 먼저 이해하자.

> **ReplicaSet (주민 기준):** 입주민이 많이 몰릴 것을 대비해, 동 개수와 상관없이 "무조건 총 3가구만 입주시켜!"
>
> **DaemonSet (동 기준):** 모든 동을 청소하고 관리하기 위해, "동마다 무조건 경비원 1명씩 다 배치해!"

코드로 보면 차이가 명확하다.

```yaml
# ReplicaSet: 개수 기준
spec:
  replicas: 3   # 서버가 몇 대든 상관없이 총 3개

# DaemonSet: 노드 기준
# replicas 필드 없음 → 노드당 자동으로 1개
```

| 항목 | ReplicaSet | DaemonSet |
|---|---|---|
| **Pod 개수 기준** | 관리자가 숫자로 지정 | 노드 수에 따라 자동 결정 |
| **트래픽 증가 시** | replicas 늘려서 대응 | 변화 없음 (노드당 1개 유지) |
| **노드 추가 시** | 변화 없음 | Pod 자동 추가 |
| **주요 용도** | 웹서버, API 서버 등 앱 | 로그 수집기, 모니터링 에이전트 등 인프라 |

### 4.2 Example 9-1. DaemonSet Resource

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: random-refresher
spec:
  selector:
    matchLabels:
      app: random-refresher       # 이 DaemonSet이 관리할 Pod 라벨
  template:
    metadata:
      labels:
        app: random-refresher
    spec:
      nodeSelector:
        feature: hw-rng           # hw-rng 라벨이 있는 노드에만 배포
      containers:
      - image: k8spatterns/random-generator:1.0
        name: random-generator
        command: [ "java", "RandomRunner", "/numbers.txt", "10000", "30" ]
        volumeMounts:
        - mountPath: /host_dev
          name: devices
      volumes:
      - name: devices
        hostPath:
          path: /dev              # 호스트의 /dev 디렉토리를 직접 마운트
```

항목별로 쪼개어 보면:

- **`kind: DaemonSet`** — "이건 일반 앱이 아니라, 서버마다 하나씩 까는 데몬셋이야"
- **`nodeSelector: feature: hw-rng`** — 하드웨어 난수 생성기(hw-rng)가 장착된 노드들만 골라서 배포
- **`hostPath: /dev`** — 호스트의 `/dev`(하드웨어 장치 경로)를 컨테이너의 `/host_dev`에 연결. 컨테이너가 실제 하드웨어 장치에 접근하기 위해 필요하다.

구조를 한눈에 정리하면:

```
DaemonSet
 ├── selector           ← 어떤 Pod를 관리할지
 └── template
      └── Pod
           ├── nodeSelector: feature=hw-rng   ← 어느 노드에서 실행할지
           ├── container (random-generator)    ← 뭘 실행할지
           └── volume (hostPath: /dev)         ← 호스트 장치 직접 접근
```

### 4.3 nodeSelector — 모든 노드 vs 특정 노드

"모든 노드에 하나씩"이라고 했는데 왜 특정 노드만 고르냐는 의문이 생길 수 있다. 모순이 아니다.

> **"조건을 만족하는 노드들을 모아놓고, 그 안에서 모든 노드에 하나씩"**

아파트 비유로 다시 보면:

```
기본 DaemonSet (조건 없음)
  1동, 2동, 3동, 4동, 5동 → 전부 경비원 1명씩

nodeSelector 적용 (hw-rng 조건)
  지하주차장 있는 동: 1동, 3동, 5동
  → 1동, 3동, 5동에만 경비원 1명씩
  → 나중에 지하주차장 있는 7동 신축 → 자동으로 7동에도 배치 ✅
```

```
전체 클러스터 노드
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│     Node 1      │  │     Node 2      │  │     Node 3      │
│  feature:hw-rng │  │  (라벨 없음)    │  │  feature:hw-rng │
│   ✅ Pod 배포   │  │   ❌ 배포 안됨  │  │   ✅ Pod 배포   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

일반 Pod(ReplicaSet)와의 차이도 여기서 드러난다.

```
같은 조건(hw-rng 노드 3대)에서

ReplicaSet + nodeSelector:
  "그 노드들 중에서 아무 데나 총 3개만 켜줘"
  → Node 1에 3개가 몰릴 수도 있음

DaemonSet + nodeSelector:
  "그 노드들 각각에 무조건 1개씩 켜줘"
  → Node 1, 3, 5에 각 1개씩, 총 3개 (보장)
```

---

## 5. DaemonSet의 주요 특징

DaemonSet은 일반 ReplicaSet과 동작 방식이 다른 몇 가지 특이점이 있다.

**스케줄러 없이도 실행 가능 (구버전 기준)**
DaemonSet이 생성한 Pod는 `nodeName`이 직접 지정되어 있어, 쿠버네티스 스케줄러 없이도 실행된다. 덕분에 스케줄러가 시작되기 전에도 Pod를 띄울 수 있다 — 즉 클러스터 부팅 초기에 어떤 Pod보다도 먼저 실행될 수 있다.

**unschedulable 노드도 무시**
노드가 `drain`이나 `cordon` 상태(unschedulable)여도 DaemonSet은 영향을 받지 않는다. 인프라 관리 작업은 노드 격리 상태와 무관하게 실행되어야 하기 때문이다.

**RestartPolicy는 Always만**
```yaml
restartPolicy: Always     # ✅ 허용
restartPolicy: OnFailure  # ❌ 불가
restartPolicy: Never      # ❌ 불가
```
데몬은 항상 살아있어야 한다. liveness probe 실패 시 컨테이너가 종료되어도 반드시 재시작이 보장되어야 한다.

**우선순위가 높다**
DaemonSet Pod는 특정 노드에서만 실행되어야 하므로 여러 컨트롤러가 특별 대우를 한다.

| 컨트롤러 | DaemonSet Pod 처리 |
|---|---|
| Descheduler | 축출(eviction) 회피 |
| Cluster Autoscaler | 별도로 분리해 관리 |

---

## 6. Scheduling Evolution

DaemonSet의 스케줄링 방식은 Kubernetes 버전을 거치며 크게 바뀌었다.

### 6.1 구버전: nodeName 방식

```yaml
# DaemonSet 컨트롤러가 직접 nodeName 지정
spec:
  nodeName: worker-node-1   # 스케줄러 완전 우회
```

스케줄러를 거치지 않고 Pod에 직접 노드를 지정했다. 스케줄러 없이도 동작하고, 스케줄러보다 먼저 실행될 수 있었다. 하지만 문제가 있었다.

```
노드 리소스 부족 시나리오

DaemonSet 컨트롤러: "이 노드에 Pod를 배포해야 하는데..."
                          ↓
                    리소스가 없음!
                          ↓
                    ❌ 아무것도 못함 (선점/Preemption 불가)
```

스케줄러가 가진 선점(Preemption) 기능을 사용할 수 없었다. 스케줄링 로직이 스케줄러와 DaemonSet 컨트롤러 두 곳에 중복되어 유지보수 부담도 생겼다. Affinity, Anti-affinity 같은 최신 기능도 활용 불가였다.

### 6.2 신버전: nodeAffinity 방식 (v1.17+)

```yaml
# nodeAffinity를 통해 기본 스케줄러에 위임
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchFields:
          - key: metadata.name
            operator: In
            values:
            - worker-node-1
```

`nodeName` 직접 지정 대신 `nodeAffinity`를 설정하고 기본 스케줄러에 위임하는 방식으로 전환했다.

```
구버전 흐름
DaemonSet 컨트롤러 → nodeName 직접 설정 → 스케줄러 우회

신버전 흐름
DaemonSet 컨트롤러 → nodeAffinity 설정 → 기본 스케줄러가 처리
                                               ↓
                                   선점, Taint/Toleration, 우선순위 등 활용 가능
```

트레이드오프는 명확하다.

| | 구버전 | 신버전 (v1.17+) |
|---|---|---|
| 스케줄러 의존성 | 없음 | 필수 |
| 선점(Preemption) | ❌ | ✅ |
| Affinity / Taints | ❌ | ✅ |
| 스케줄링 로직 중복 | 있음 | 없음 |
| 스케줄러 없이 실행 | 가능 | 불가 |

스케줄러 독립성을 포기하는 대신, 리소스 경쟁 상황에서의 안정성과 최신 스케줄러 기능을 얻었다.

---

## 7. Static Pods

DaemonSet과 유사하게 노드에서 컨테이너를 실행하는 또 다른 방법 — **Static Pod**다.

Kubelet은 API 서버와 통신하는 것 외에, **로컬 디렉토리를 직접 감시**해서 Pod를 실행할 수 있다.

```
일반 Pod 실행 흐름
사용자 → API Server → 스케줄러 → Kubelet → Pod 실행

Static Pod 실행 흐름
/etc/kubernetes/manifests/ (로컬 디렉토리)
        ↓
      Kubelet이 직접 감시
        ↓
      Pod 실행 (API Server, 스케줄러 불필요)
```

Kubelet은 해당 디렉토리를 주기적으로 스캔해 변경을 감지하고 Pod를 추가/제거한다. Pod가 크래시하면 직접 재시작한다.

| 항목 | Static Pod | DaemonSet |
|---|---|---|
| **관리 주체** | Kubelet만 | DaemonSet 컨트롤러 |
| **API Server 필요** | ❌ | ✅ |
| **스케줄러 필요** | ❌ | ✅ (v1.17+) |
| **실행 노드** | 1개 노드만 | 모든(또는 지정) 노드 |
| **헬스체크** | ❌ | ✅ |
| **kubectl로 관리** | ❌ | ✅ |
| **플랫폼 통합성** | 낮음 | 높음 |

Static Pod의 주된 사용처는 쿠버네티스 자체 시스템 컴포넌트다 — `etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`. API 서버 자체가 없는 상황에서도 실행되어야 하기 때문이다.

일반적인 용도에는 DaemonSet이 권장된다. 플랫폼 통합성이 높고 Kubernetes 도구를 그대로 활용할 수 있기 때문이다.

---

## 8. Discussion

노드에서 데몬 프로세스를 실행하는 방법은 여러 가지가 있지만 각각 한계가 있다.

```
방법별 한계점

Static Pod       → API로 관리 불가, 단일 노드에만 존재
Bare Pod         → 삭제/노드 장애 시 복구 불가
Init 스크립트    → 별도 툴체인 필요, Kubernetes 도구 활용 불가
(systemd 등)       앱과 데몬을 완전히 다른 방식으로 관리해야 함
```

DaemonSet은 이 모든 한계를 해결한다.

```
DaemonSet이 해결하는 것
  ✅ Kubernetes API로 완전히 관리 (kubectl 그대로 사용)
  ✅ 노드 장애 시 자동 복구
  ✅ Affinity, Taint 등 플랫폼 기능 활용
  ✅ 노드 추가 시 자동 배포
  ✅ 앱과 동일한 방식으로 모니터링/운영
```

DaemonSet과 CronJob은 **단일 노드 개념을 분산 시스템 프리미티브로 승격**시킨 좋은 예시다.

```
전통적 단일 노드 개념     →    Kubernetes 분산 개념
─────────────────────          ──────────────────────
crontab               →        CronJob
                                (클러스터 전체에서 스케줄 관리)

daemon 스크립트        →        DaemonSet
(systemd, upstartd)             (모든 노드에서 일관되게 실행)
```

DaemonSet은 플랫폼 관리자에 가까운 도구지만, 클러스터 인프라가 어떻게 동작하는지 이해하려는 개발자에게도 반드시 필요한 개념이다.

> DaemonSet이 해결해주는 문제들이 원래 복잡했던 것이지, DaemonSet 자체가 복잡한 게 아니다.
> 그 복잡한 걸 "각 동마다 경비원 한 명씩" 수준으로 단순하게 만들어준 것이 핵심이다.