---
series: ["K8sPatterns"]
title: "K8sPatterns.06 Automated Placement"
date: 2026-07-02T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "scheduling"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.06 Automated Placement'
  relative: true
summary: "How the Kubernetes scheduler assigns Pods to nodes using predicates, priorities, node affinity, pod affinity, taints and tolerations for optimal placement."
---

## 1. Overview

```
Pod 배치 문제
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

수십 ~ 수백 개의 Pod
어느 노드에 배치할지 사람이 직접 결정? → 불가능

Kubernetes 스케줄러가 자동으로 결정
    │
    ├─► 노드 가용 용량 확인
    ├─► 컨테이너 리소스 요구사항 확인
    └─► 배치 정책 적용
```

배치 제어 방법 (간단 → 복잡 순서)

| 방법 | 설명 |
|---|---|
| nodeSelector | 특정 라벨 가진 노드에만 배치 |
| Node Affinity | 필수/선호 조건으로 노드 선택 |
| Pod Affinity/Antiaffinity | 다른 Pod 위치 기준으로 배치 |
| Taints/Tolerations | 노드가 Pod를 거부/허용 |

---

## 2. Why Automated Placement?

### 문제

```
마이크로서비스 시스템
    │
    수십 ~ 수백 개의 격리된 프로세스
    │
    컨테이너 간 의존성
    노드 의존성 (SSD, GPU 등)
    리소스 요구사항
    │
    이 모든 것이 시간에 따라 변함
```

배치가 분산 시스템의 **가용성, 성능, 용량**에 직접 영향을 미친다.
잘못 배치하면 한 노드 장애 시 서비스 전체가 다운되거나, 리소스 경쟁으로 성능이 저하된다.

### 스케줄러가 하는 일

```
API 서버에서 새 Pod 정의 가져옴
    │
    모든 노드와 정책 고려
    │
    1단계: Predicates 필터링
           자격 없는 노드 탈락
    │
    2단계: Priorities 점수 매기기
           남은 노드 순위 결정
    │
    3단계: 노드 할당
           최고 점수 노드에 Pod 배치
```

스케줄러가 동작하는 세 가지 상황:
- 초기 배포 시
- 스케일 업 시 (새 Pod 추가)
- 노드 장애 시 (다른 노드로 이동)

---

## 3. Available Node Resources

### 노드 가용 용량 공식 (Example 6-1)

```
Allocatable =
  Node Capacity
  - Kube-Reserved  (Kubelet, 컨테이너 런타임)
  - System-Reserved (OS 데몬: sshd, udev 등)
```

예약을 안 하면?

```
Pod들이 노드 전체 용량 다 사용
    │
    OS, Kubelet도 자원 부족
    │
    노드 전체 불안정 (리소스 고갈) 💥
```

### Kubernetes 외부 컨테이너 문제

```
Docker로 직접 실행한 컨테이너
    │
    Kubernetes가 모름
    용량 계산에 반영 안 됨
    │
    스케줄러: "이 노드 자원 많네" → Pod 배치
    실제로는: 외부 컨테이너가 자원 다 씀 💥
```

**해결책: 플레이스홀더 Pod**

```yaml
# 아무것도 안 하지만 리소스만 선언
containers:
- name: placeholder
  image: pause
  resources:
    requests:
      cpu: "2"       # 외부 컨테이너가 쓰는 만큼
      memory: "4Gi"  # 예약해둠
```

스케줄러가 이 Pod를 보고 해당 자원이 사용 중임을 인식한다.

---

## 4. Container Resource Demands

스케줄러가 올바르게 배치하려면 컨테이너가 **리소스 요구사항을 선언**해야 한다.

```yaml
containers:
- name: my-app
  resources:
    requests:          # 스케줄러가 배치 기준으로 사용
      cpu: "500m"      # CPU 0.5개 보장
      memory: "128Mi"  # 메모리 128MB 보장
    limits:            # 이 이상 사용 불가
      cpu: "1000m"
      memory: "256Mi"
```

선언 없으면 스케줄러가 올바른 판단을 내리지 못하고, 피크 시간에 Pod들이 자원을 놓고 경쟁한다.

```
requests 기준으로 계산
    │
    실제 사용량이 아닌 선언값으로 예약
    requests: cpu: "2" → 실제 0.5 사용해도 2개 예약된 것으로 봄
```

---

## 5. Placement Policies

스케줄러는 기본 Predicate와 Priority 정책을 가지고 있다. 대부분의 경우 기본값으로 충분하다.

### Predicates (필터링)

자격 없는 노드를 걸러내는 규칙. 통과 못하면 탈락.

| Predicate | 설명 |
|---|---|
| PodFitsResources | 자원 충분한가? |
| PodFitsHostPorts | 포트 사용 가능한가? |
| NoDiskConflict | 디스크 충돌 없는가? |
| NoVolumeZoneConflict | 볼륨 존 충돌 없는가? |
| MatchNodeSelector | 노드 라벨 맞는가? |
| HostName | 특정 호스트명인가? |

### Priorities (우선순위)

후보 노드에 점수를 매기는 규칙. weight가 높을수록 중요.

| Priority | weight | 설명 |
|---|---|---|
| LeastRequestedPriority | 2 | 자원 적게 쓰는 노드 선호 |
| BalancedResourceAllocation | 1 | CPU/메모리 균형 노드 선호 |
| ServiceSpreadingPriority | 2 | 같은 서비스 Pod 분산 선호 |
| EqualPriority | 1 | 모든 노드 동등 |

### 전체 흐름

```
전체 노드 10개
    │
    Predicates 필터링
    → 자원 부족, 포트 충돌 등으로 탈락
    │
    후보 노드 3개
    │
    Priorities 점수
    노드A: 90점
    노드B: 70점
    노드C: 50점
    │
    노드A에 Pod 배치 ✅
```

### 커스텀 스케줄러

```yaml
# 특정 스케줄러 지정
spec:
  schedulerName: my-scheduler  # 기본값: default-scheduler
```

여러 스케줄러를 동시에 운영할 수 있다. GPU 전용, ML 워크로드 전용 등 특수한 배치 요구사항에 활용한다.  
스케줄러 정책 변경과 커스텀 스케줄러 생성은 **관리자만** 가능하다.

---

## 6. Node Selector

가장 단순한 노드 배치 방법. 특정 라벨을 가진 노드에만 Pod를 배치한다.

### Example 6-3

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  nodeSelector:
    disktype: ssd    # 이 라벨 있는 노드에만 배치
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
```

```
노드1: disktype=ssd  → 배치 가능 ✅
노드2: disktype=hdd  → 탈락 ❌
노드3: disktype=ssd  → 배치 가능 ✅
```

### 노드에 라벨 추가

```bash
kubectl label node 노드이름 disktype=ssd
kubectl get nodes --show-labels
```

### 기본 라벨 활용

모든 노드에 자동으로 붙어있는 기본 라벨도 사용할 수 있다.

| 라벨 | 설명 | 예시 |
|---|---|---|
| `kubernetes.io/hostname` | 노드 이름 | node1 |
| `kubernetes.io/os` | 운영체제 | linux, windows |
| `kubernetes.io/arch` | CPU 아키텍처 | amd64, arm64 |
| `node.kubernetes.io/instance-type` | 인스턴스 타입 | m5.large |

```yaml
# 특정 노드에 직접 배치
nodeSelector:
  kubernetes.io/hostname: node1

# Linux 노드에만
nodeSelector:
  kubernetes.io/os: linux
```

### nodeSelector 한계

단순한 라벨 매칭만 가능하다. "SSD면 좋겠어(선호)" 같은 표현이 불가능하고 무조건 AND 조건이다.  
복잡한 조건이 필요하면 **Node Affinity**를 사용한다.

---

## 7. Node Affinity

nodeSelector의 일반화. 필수/선호 조건을 구분하고 다양한 연산자를 사용할 수 있다.

### 두 가지 규칙 타입

```
requiredDuringSchedulingIgnoredDuringExecution
    필수 — 이 조건 안 맞으면 배치 안 함

preferredDuringSchedulingIgnoredDuringExecution
    선호 — 이 조건 맞으면 점수 올려줌, 없어도 배치는 됨
```

`IgnoredDuringExecution`: 이미 실행 중인 Pod는 노드 라벨이 변경되어도 영향받지 않음.

### 연산자 종류

| 연산자 | 설명 |
|---|---|
| In | 값이 목록 안에 있으면 |
| NotIn | 값이 목록 안에 없으면 |
| Exists | 키가 존재하면 |
| DoesNotExist | 키가 없으면 |
| Gt | 값이 크면 |
| Lt | 값이 작으면 |

### Example 6-4

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  affinity:
    nodeAffinity:

      # 필수: 코어 수 3개 초과 노드에만 배치
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:        # 라벨로 매칭
          - key: numberCores
            operator: Gt
            values: [ "3" ]

      # 선호: 가능하면 master 노드 피하기
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchFields:             # 노드 필드(jsonpath)로 매칭
          - key: metadata.name
            operator: NotIn
            values: [ "master" ]   # In, NotIn만 가능, 값은 1개만

  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
```

### matchExpressions vs matchFields

| | matchExpressions | matchFields |
|---|---|---|
| 기준 | 노드 라벨 | 노드 필드 (jsonpath) |
| 사용 가능 연산자 | 모두 | In, NotIn만 |
| 값 개수 | 여러 개 | 1개만 |

### nodeSelector vs Node Affinity 비교

| | nodeSelector | Node Affinity |
|---|---|---|
| 필수/선호 구분 | ✗ 필수만 | ✓ 둘 다 |
| 연산자 | = 만 | In, NotIn, Gt, Lt 등 |
| 복잡한 조건 | ✗ | ✓ |
| 사용 난이도 | 쉬움 | 복잡함 |

---

## 8. Pod Affinity and Antiaffinity

Node Affinity는 노드 특성 기준이다. Pod 간의 위치 관계를 기준으로 배치하려면 **Pod Affinity/Antiaffinity**를 사용한다.

### 개념

```
Pod Affinity (같이 있고 싶어)
    자주 통신하는 Pod끼리 같은 노드에
    → 네트워크 지연 감소

Pod Antiaffinity (떨어져 있고 싶어)
    같은 서비스 Pod들을 여러 노드에 분산
    → 고가용성
```

### topologyKey

어떤 레벨에서 규칙을 적용할지 결정한다.

| topologyKey | 레벨 |
|---|---|
| `kubernetes.io/hostname` | 노드 단위 |
| `topology.kubernetes.io/zone` | 가용 영역 단위 |
| `topology.kubernetes.io/region` | 리전 단위 |
| `rack` | 랙 단위 (커스텀) |

### Example 6-5

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  affinity:

    # 필수: confidential=high Pod와 같은 security-zone에 배치
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            confidential: high   # 이 라벨 가진 Pod 근처에
        topologyKey: security-zone
        # confidential=high Pod가 있는 노드의 security-zone 값과
        # 같은 security-zone 라벨을 가진 노드에 배치

    # 선호: confidential=none Pod와 다른 노드에 배치
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              confidential: none   # 이 Pod랑 다른 노드에
          topologyKey: kubernetes.io/hostname

  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
```

**시나리오:** 기밀 데이터 처리 앱을 보안 구역 안에 배치하고, 비기밀 Pod와 격리한다.

```
필수 (podAffinity)
  confidential=high Pod와 같은 security-zone ✅

선호 (podAntiAffinity)
  confidential=none Pod 없는 노드 우선
  (weight: 100 → 강한 선호)
```

---

## 9. Taints and Tolerations

Node Affinity는 Pod가 노드를 선택하는 것이다. Taints/Tolerations는 반대로 **노드가 Pod를 거부**하는 메커니즘이다.

```
Node Affinity → Pod 관점: "나 이런 노드에 가고 싶어"
Taints/Tolerations → 노드 관점: "나 아무 Pod나 못 받아"
```

### opt-in vs opt-out

```
Affinity (opt-out)
    기본: 모든 노드 사용 가능
    특정 노드만 선택 → 나머지 제외

Taint/Toleration (opt-in)
    기본: 이 노드 사용 불가
    Toleration 있는 Pod만 허용
```

### Taint Effect 종류

| Effect | 설명 |
|---|---|
| NoSchedule | Toleration 없으면 배치 안 함 (실행 중인 Pod 유지) |
| PreferNoSchedule | 가능하면 배치 안 함 (어쩔 수 없으면 가능) |
| NoExecute | 배치 안 함 + 실행 중인 Pod도 쫓아냄 |

### Example 6-6 (Tainted Node)

```yaml
apiVersion: v1
kind: Node
metadata:
  name: master
spec:
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
    # Toleration 없는 Pod 배치 불가
    # 마스터 노드를 일반 Pod로부터 보호
```

```bash
# 명령어로 추가
kubectl taint nodes master node-role.kubernetes.io/master="true":NoSchedule
```

### Example 6-7 (Pod with Toleration)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  tolerations:
  - key: node-role.kubernetes.io/master
    operator: Exists    # value 상관없이 key만 있으면 매칭
    effect: NoSchedule  # 이 effect에만 적용
                        # 비워두면 모든 effect에 적용
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
```

### Taint와 Toleration 매칭

```
노드 Taint
  key: node-role.kubernetes.io/master
  effect: NoSchedule

Pod Toleration
  key: node-role.kubernetes.io/master  ← 일치 ✅
  operator: Exists                      ← key만 있으면 됨
  effect: NoSchedule                   ← 일치 ✅

매칭 성공 → 마스터 노드에 배치 가능 ✅
```

### operator 종류

| operator | 설명 |
|---|---|
| Exists | key만 존재하면 매칭, value 불필요 |
| Equal | key와 value 모두 일치해야 매칭 |

### 실제 사용 사례

```
마스터 노드 보호
  마스터 노드에 NoSchedule taint
  → 시스템 Pod만 toleration으로 접근

GPU 노드 전용화
  GPU 노드에 gpu=true:NoSchedule taint
  → GPU 필요한 Pod만 toleration 추가
  → 일반 Pod는 GPU 노드 사용 불가
```

---

## 10. Stranded Resources and Descheduler

### 스케줄러의 한계 — 배치는 스냅샷 결정

스케줄러는 Pod를 노드에 할당하는 순간까지만 관여한다. 배치가 끝나면 역할이 끝나고, Pod가 삭제되고 재생성되지 않는 한 배치를 바꾸지 않는다.

```
스케줄러 = 스냅샷 기반 결정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
새 Pod 배치 요청
    │
    "지금 이 순간" 클러스터 상태만 확인
    │
    최적 노드 선택 → 배치 완료
    │
    이후 클러스터가 어떻게 변하든 관여 안 함
```

### 문제 상황

**1. 리소스 단편화 (Stranded Resources, Figure 6-2)**

```
노드 A
┌─────────────────────────────────┐
│  CPU ████████████████░░  (거의 다 씀)│
│  MEM ████░░░░░░░░░░░░░  (4GB 남음) │
│                                 │
│  메모리는 남았지만 CPU가 없어서   │
│  새 Pod가 못 들어옴 = 낭비 💥    │
└─────────────────────────────────┘
```

원인은 컨테이너 리소스 요구사항이 실제 사용량과 어긋나게 잡히는 것이다. CPU를 넉넉하게 요청하고 메모리는 적게 요청하면, CPU가 먼저 소진되고 메모리만 계속 비어있는 상태로 고립된다.

**2. 클러스터 확장 시 불균형**

```
처음: 노드 3개, Pod 균등 배치
    │
    나중: 노드 5개로 확장
    │
    새 노드 2개는 텅 빔
    기존 Pod는 재배치되지 않아 불균형 유지
```

**3. 노드 라벨 변경**

```
노드A: region=us-east 라벨 → Pod 배치됨
    │
    라벨 변경: region=us-west
    │
    이미 배치된 Pod는 그대로 실행 (재배치 안 됨)
```

### Descheduler

스케줄러가 신규 배치만 담당하는 반면, Descheduler는 **이미 배치된 Pod를 재배치**해 클러스터 리소스 활용률을 개선하는 선택적(옵트인) 기능이다. 상시 실행되지 않고, 클러스터 관리자가 필요한 시점에 Job으로 실행한다.

```
스케줄러                Descheduler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
신규 Pod만 처리          이미 배치된 Pod 재배치
컨트롤러로 상시 실행      필요할 때 Job으로 실행
```

**동작 흐름**

```
관리자가 Descheduler Job 실행
    │
    현재 클러스터 상태 분석
    │
    정책에 따라 퇴거 대상 Pod 선택 (예: RemoveDuplicates)
    │
    대상 Pod 삭제 (퇴거)
    │
    스케줄러가 다시 최적 노드에 재배치
    │
    클러스터 리소스 재조정 완료
```

**RemoveDuplicates 정책 예시** — 노드 장애로 컨트롤러가 다른 노드에 대체 Pod를 만들었다가, 장애 노드가 복구되며 같은 서비스의 Pod가 한 노드에 중복으로 몰리는 경우 초과분을 제거해 원하는 replica 수로 되돌린다.

### 그 외 Descheduler 정책

| 정책 | 목적 |
|---|---|
| RemoveDuplicates | 한 노드에 몰린 중복 Pod 제거 |
| LowNodeUtilization | 저활용 노드로 Pod를 옮겨 균등 분산 |
| RemovePodsViolatingInterPodAntiAffinity | Pod Antiaffinity 규칙 위반 Pod 퇴거 |
| RemovePodsViolatingNodeAffinity | Node Affinity 규칙 위반 Pod 퇴거 |

**LowNodeUtilization** — 노드를 활용도 기준 세 그룹으로 나눈다.

```
underutilized (threshold 미만)  → Pod를 받는 대상
적절 (threshold ~ targetThreshold) → 영향 없음
overutilized (targetThreshold 초과) → Pod를 퇴거시키는 대상
```

overutilized 노드의 Pod를 퇴거시키면 스케줄러가 underutilized 노드에 재배치해 리소스 사용률이 균등해진다.

**RemovePodsViolatingInterPodAntiAffinity / RemovePodsViolatingNodeAffinity** — Affinity 규칙은 스케줄링 시점에만 평가되므로, 배치 이후에 규칙이 새로 추가되거나 노드 라벨이 바뀌면 이미 배치된 Pod가 규칙을 위반한 상태로 남을 수 있다. 두 정책은 이런 위반 Pod를 퇴거시켜 스케줄러가 규칙에 맞는 노드로 다시 배치하게 한다.

### 퇴거 대상에서 제외되는 Pod

Descheduler는 다음 Pod는 절대 퇴거시키지 않는다.

| 대상 | 이유 |
|---|---|
| `scheduler.alpha.kubernetes.io/critical-pod` 어노테이션 Pod | 시스템 핵심 Pod 보호 |
| ReplicaSet/Deployment/Job 등 컨트롤러 없는 Pod | 퇴거해도 재생성해줄 컨트롤러가 없음 |
| DaemonSet Pod | 퇴거해도 DaemonSet이 같은 노드에 다시 생성 — 의미 없음 |
| 로컬 스토리지를 쓰는 Pod | 퇴거 시 데이터 유실 위험 |
| PodDisruptionBudget을 위반하게 되는 Pod | 서비스 최소 가용 개수 보장 |
| Descheduler 자기 자신 | Critical Pod로 마킹되어 스스로는 건드리지 않음 |

### QoS 레벨과 퇴거 순서

퇴거가 필요할 때는 중요도가 낮은 Pod부터 선택된다.

```
1순위 Best-Effort  (request/limit 없음)       → 가장 먼저 퇴거
2순위 Burstable    (request < limit)          → 그다음
3순위 Guaranteed   (request = limit)          → 가장 마지막, 가장 보호받음
```

### 해결 방향

```
해결책 1: 리소스 요구사항 세분화
    requests를 실제 사용량에 맞게 더 작게 설정
    → 더 많은 Pod가 빈틈에 들어갈 수 있음

해결책 2: Descheduler로 재배치
    노드 단편화 해소, Pod 재조정
    → 리소스 활용률 개선
```

### 스케줄러 과도한 제한 주의

nodeSelector, Node/Pod Affinity, Taints를 한꺼번에 많이 걸면 배치 가능한 노드가 아예 없어질 수 있다.

```
너무 많은 제약을 동시에 걸면?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
nodeSelector + Node Affinity +
Pod Affinity + Taints 전부 적용
    │
    배치 가능한 노드가 없음 💥
    Pod는 Pending 상태로 남고 리소스는 낭비됨
```

스케줄러는 배치 시점의 스냅샷만 보고 결정하며 이후 변화에 대응하지 않는다. 최소한의 제약만 걸고 스케줄러를 신뢰하되, 리소스 단편화가 누적되면 Descheduler로 정리하는 것이 실무적인 선택이다.

---

## 11. 배치 방법 종합 비교

```
┌──────────────────────┬──────────────────────────────────────┐
│ 방법                 │ 특징                                 │
├──────────────────────┼──────────────────────────────────────┤
│ nodeSelector         │ 단순 라벨 매칭, 필수만               │
│ Node Affinity        │ 필수/선호, 다양한 연산자             │
│ Pod Affinity         │ 다른 Pod와 같이 배치                 │
│ Pod Antiaffinity     │ 다른 Pod와 떨어져 배치               │
│ Taints/Tolerations   │ 노드가 Pod 거부, 허가증으로 접근     │
└──────────────────────┴──────────────────────────────────────┘
```

### 선택 가이드

```
SSD, GPU 같은 특수 하드웨어 필요
    → nodeSelector 또는 Node Affinity

자주 통신하는 Pod끼리 가까이
    → Pod Affinity

고가용성 위해 Pod 분산
    → Pod Antiaffinity

마스터 노드 보호, 전용 노드
    → Taints/Tolerations

대부분의 경우
    → 스케줄러에게 맡기는 게 최선
```

스케줄러에게 맡기는 것이 기본이다. 배치 로직을 과도하게 제어하면 오히려 스케줄러의 최적화를 방해한다.

---

## 12. Discussion

Automated Placement 패턴은 리소스 요구사항과 배치 정책을 통해 스케줄러와 소통하는 방법을 다룬다. nodeSelector, Affinity, Taints/Tolerations는 배치를 세밀하게 제어하는 도구이지만, 기본값은 항상 "스케줄러에게 맡기기"다.

다음 챕터 Self Awareness는 애플리케이션이 자기 자신에 대한 메타데이터(Pod 이름, 네임스페이스, 리소스 제한 등)를 다운워드 API로 조회하는 방법을 다룬다.