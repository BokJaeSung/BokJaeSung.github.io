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

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-why-automated-placement" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Why Automated Placement?</a></div>
  <div><a href="#3-available-node-resources" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Available Node Resources</a></div>
  <div><a href="#4-container-resource-demands" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Container Resource Demands</a></div>
  <div><a href="#5-placement-policies" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. Placement Policies</a></div>
  <div><a href="#6-node-selector" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. Node Selector</a></div>
  <div><a href="#7-node-affinity" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. Node Affinity</a></div>
  <div><a href="#8-pod-affinity-and-antiaffinity" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">8. Pod Affinity and Antiaffinity</a></div>
  <div><a href="#9-taints-and-tolerations" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">9. Taints and Tolerations</a></div>
  <div><a href="#10-stranded-resources-and-descheduler" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">10. Stranded Resources and Descheduler</a></div>
  <div><a href="#11-배치-방법-종합-비교" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">11. 배치 방법 종합 비교</a></div>
  <div><a href="#12-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">12. Discussion</a></div>
</div>
</div>
{{< /rawhtml >}}

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

`requiredDuringScheduling`은 스케줄링 시점에 필수라는 뜻이다. 새롭게 스케줄링되는 Pod에 대해 Node Affinity 조건이 반드시 지켜져야 하며, 조건에 맞는 노드가 없으면 배치 자체가 되지 않는다.

필수값만 줄 수 있는 건 아니다. `preferredDuringScheduling`으로 "필수는 아니지만 가급적이면" 해당 노드로 스케줄링되도록 지정할 수 있다. preferred로 지정하면 조건에 맞는 노드가 자원 부족 등의 사정으로 Pod를 받아줄 수 없을 때, 조건에 맞지 않는 다른 노드로도 스케줄링된다.

```
requiredDuringSchedulingIgnoredDuringExecution
    필수 — 이 조건 안 맞으면 배치 안 함

preferredDuringSchedulingIgnoredDuringExecution
    선호 — 이 조건 맞으면 점수 올려줌, 안 맞아도 다른 노드로 배치는 됨
```

`IgnoredDuringExecution`은 실행 중이라면 무시하라는 뜻이다. 이미 실행 중인 Pod는 해당 노드가 더 이상 규칙을 충족하지 않는 상태가 되어도 굳이 내려서 다시 옮기지 않는다. 반대 개념으로 `RequiredDuringExecution`이 있으나(실행 중에도 조건 위반 시 재배치), 이 글 작성 시점 기준 정식 릴리스되지 않았다.

### 필드 구조

`requiredDuringSchedulingIgnoredDuringExecution`의 하위 필드로는 노드 셀렉터 설정을 묶는 `nodeSelectorTerms[]`와, 그 안에서 실제 조건을 정의하는 `matchExpressions[]`가 있다. `matchExpressions[]`의 하위 필드는 `key`, `operator`, `values[]`다.

- `key`: 노드의 레이블 키 중 하나
- `operator`: `key`가 만족해야 할 조건
- `values[]`: `operator`에 따라 비교할 값 목록

### 연산자 종류

| operator | 설명 |
|---|---|
| In | `values[]`에 설정한 값 중 레이블 값과 일치하는 것이 하나라도 있는지 확인 |
| NotIn | `values[]`에 있는 값 모두와 일치하지 않는지 확인 |
| Exists | `key` 필드 값이 레이블에 존재하는지만 확인 (`values[]` 불필요) |
| DoesNotExist | 노드 레이블에 `key` 필드 값이 없는지만 확인 (`values[]` 불필요) |
| Gt | `values[]`에 설정된 값(숫자)이 노드 레이블 값보다 큰지 확인 — `values[]`는 값 1개만 허용 |
| Lt | `values[]`에 설정된 값(숫자)이 노드 레이블 값보다 작은지 확인 — `values[]`는 값 1개만 허용 |

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

예를 들어 아래처럼 조건을 쓰면, 결국 `disktype=ssd` 라벨을 가진 노드에 스케줄링하라는 의미다.

```yaml
nodeAffinity:
  requiredDuringSchedulingIgnoredDuringExecution:
    nodeSelectorTerms:
    - matchExpressions:
      - key: disktype
        operator: In
        values: [ "ssd" ]
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

### labelSelector

Node Affinity가 `key`/`operator`/`values`로 **노드**의 레이블을 찾는 것과 달리, Pod Affinity/Antiaffinity는 `labelSelector`로 기준이 되는 **Pod**의 레이블을 찾는다.

`labelSelector.matchLabels`에 지정한 레이블과 일치하는 Pod가 있는 노드를 찾고, 그 노드의 `topologyKey` 값을 기준으로 같은(Affinity) 또는 다른(Antiaffinity) 위치에 배치한다.

```
labelSelector.matchLabels: confidential=high 인 Pod를 찾는다
    │
    그 Pod가 있는 노드의 topologyKey(security-zone) 값 확인
    │
    같은 값을 가진 노드에 배치 (Affinity)
```

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

### Step-by-Step: Pod Affinity/Antiaffinity 스케줄링 과정

{{< rawhtml >}}
<style>
#pa-wrap{font-family:'Space Grotesk',system-ui,sans-serif;background:linear-gradient(135deg,#1e3050 0%,#253c60 60%,#1c2d50 100%);border-radius:14px;padding:20px;box-shadow:0 8px 40px rgba(0,0,0,.6);margin:1.5rem 0;}
.pa-btn{padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;transition:background .15s;}
.pa-btn-p{background:#1f6feb;color:#fff;}.pa-btn-p:hover{background:#388bfd;}
.pa-btn-s{background:#21262d;color:#c9d1d9;border:1px solid #30363d;}.pa-btn-s:hover{background:#30363d;}
.pa-btn:disabled{opacity:.35;cursor:default;}
.pa-legend{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:12px;font-size:16px;font-weight:600;color:#c9d1d9;}
.pa-leg-dot{width:11px;height:11px;border-radius:50%;display:inline-block;margin-right:4px;border:1px solid;}
#pa-info{background:#1e2d45;border-radius:10px;padding:12px 16px;border-left:3px solid #2f81f7;margin-top:12px;font-size:18px;font-weight:600;color:#e6edf3;line-height:1.9;min-height:96px;transition:opacity .15s ease,transform .15s ease;}
</style>

<div id="pa-wrap">
  <div class="pa-legend">
    <span><span class="pa-leg-dot" style="background:#f472b622;border-color:#f472b6;"></span>confidential=high</span>
    <span><span class="pa-leg-dot" style="background:#60a5fa22;border-color:#60a5fa;"></span>confidential=none</span>
    <span><span class="pa-leg-dot" style="background:#fbbf2422;border-color:#fbbf24;"></span>새 Pod</span>
    <span><span class="pa-leg-dot" style="background:#34d39922;border-color:#34d399;"></span>후보/선정 노드</span>
  </div>
  <div style="display:flex;gap:8px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">
    <button class="pa-btn pa-btn-s" id="pa-bb" onclick="paB()">◀ 이전</button>
    <button class="pa-btn pa-btn-p" id="pa-bn" onclick="paN()">다음 ▶</button>
    <button class="pa-btn pa-btn-s" onclick="paR()" style="margin-left:4px;">↺ 초기화</button>
    <span id="pa-lbl" style="font-size:16px;color:#8b949e;margin-left:4px;"></span>
  </div>
  <svg id="pa-g" style="width:100%;background:linear-gradient(135deg,#1d3050 0%,#223a5e 100%);border-radius:12px;border:1px solid #21262d;" viewBox="0 0 800 260"></svg>
  <div id="pa-info"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
(function(){
const NL=[
  {id:'node-A',x:100,y:160,zone:'security-zone=secure',pod:{label:'high',color:'#f472b6'}},
  {id:'node-B',x:300,y:160,zone:'security-zone=secure',pod:{label:'none',color:'#60a5fa'}},
  {id:'node-C',x:500,y:160,zone:'security-zone=public', pod:null},
  {id:'node-D',x:700,y:160,zone:'security-zone=secure',pod:null}
];
const MF="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";
const C=(v,c)=>`<span style="color:${c};font-weight:700">${v}</span>`;

const SS=[
  {cand:[],sel:null,excl:[],newPodX:400,newPodY:50,
   inf:'새 Pod를 스케줄링해야 한다. 먼저 필수 조건인 podAffinity(confidential=high)부터 확인한다.'},
  {cand:['node-A'],sel:null,excl:[],newPodX:400,newPodY:50,
   inf:`${C('requiredDuringScheduling','#f472b6')}: labelSelector로 confidential=high Pod를 찾는다 → node-A에 있음.`},
  {cand:['node-A','node-B','node-D'],sel:null,excl:[],newPodX:400,newPodY:50,
   inf:`node-A의 ${C('topologyKey(security-zone)','#fbbf24')} 값과 같은 노드가 후보가 된다 → node-A, node-B, node-D (모두 secure).<br>node-C는 public이라 애초에 후보가 아니다.`},
  {cand:['node-A','node-B','node-D'],sel:null,excl:[],newPodX:400,newPodY:50,
   inf:`이제 선호 조건인 ${C('podAntiAffinity','#60a5fa')} (confidential=none과 같은 노드 피하기, weight 100, topologyKey: hostname)를 후보군에 적용한다.`},
  {cand:['node-A','node-B','node-D'],sel:null,excl:['node-B'],newPodX:400,newPodY:50,
   inf:`node-B는 ${C('confidential=none','#60a5fa')} Pod와 같은 호스트라 이 조건을 위반한다 → 후보에서 ${C('제외','#f87171')}.<br>node-A, node-D는 조건을 만족해 후보로 남는다.`},
  {cand:['node-A','node-D'],sel:'node-D',excl:['node-B'],newPodX:400,newPodY:50,
   inf:`남은 후보(A, D) 중 이미 Pod가 있는 node-A보다 비어있는 ${C('node-D가 선정','#34d399')}된다 (기본 스코어링 기준).`},
  {cand:['node-A','node-D'],sel:'node-D',excl:['node-B'],newPodX:700,newPodY:160,
   inf:`최종 배치: ${C('node-D','#34d399')}에 새 Pod가 스케줄링된다. (필수 조건 충족 + 선호 조건 만족 + 기본 스코어링에서 D가 선택)`}
];

let cur=0;
const svg=d3.select('#pa-g');
const defs=svg.append('defs');
const gF=defs.append('filter').attr('id','pa-gx').attr('x','-50%').attr('y','-50%').attr('width','200%').attr('height','200%');
gF.append('feGaussianBlur').attr('stdDeviation',5).attr('result','b');
const fm=gF.append('feMerge');fm.append('feMergeNode').attr('in','b');fm.append('feMergeNode').attr('in','SourceGraphic');

const nG=svg.append('g');
const nGs=nG.selectAll('g').data(NL).enter().append('g').attr('transform',d=>`translate(${d.x},${d.y})`);

nGs.append('rect').attr('class','box').attr('x',-80).attr('y',-60).attr('width',160).attr('height',120).attr('rx',10)
  .attr('fill','#1c2433').attr('stroke','#3a4f6a').attr('stroke-width',2.5);
nGs.append('text').attr('text-anchor','middle').attr('y',-70)
  .attr('fill','#e6edf3').attr('font-size',15).attr('font-weight',700).attr('font-family',MF).text(d=>d.id);
nGs.append('text').attr('text-anchor','middle').attr('y',-40)
  .attr('fill','#8b949e').attr('font-size',11).attr('font-family',MF).text(d=>d.zone);

nGs.filter(d=>d.pod).each(function(d){
  const g=d3.select(this);
  g.append('circle').attr('cx',0).attr('cy',10).attr('r',18).attr('fill',d.pod.color).attr('opacity',.9);
  g.append('text').attr('text-anchor','middle').attr('y',15)
    .attr('fill','#0d1117').attr('font-size',11).attr('font-weight',700).attr('font-family',MF).text(d.pod.label);
});

const newPod=svg.append('g').attr('id','pa-new-pod').attr('transform','translate(400,50)');
newPod.append('circle').attr('r',18).attr('fill','#fbbf24').attr('stroke','#fff').attr('stroke-width',2);
newPod.append('text').attr('text-anchor','middle').attr('y',5)
  .attr('fill','#1c2333').attr('font-size',10).attr('font-weight',700).attr('font-family',MF).text('new');

function fadeUpdate(id,html){
  const el=document.getElementById(id);
  if(el.innerHTML===html) return;
  el.style.opacity='0';el.style.transform='translateY(6px)';
  setTimeout(()=>{el.innerHTML=html;el.style.opacity='1';el.style.transform='translateY(0)';},140);
}

function render(){
  const s=SS[cur],T=360;
  nGs.select('.box').transition().duration(T)
    .attr('stroke',d=>d.id===s.sel?'#34d399':s.excl.includes(d.id)?'#f87171':s.cand.includes(d.id)?'#34d399':'#3a4f6a')
    .attr('stroke-width',d=>d.id===s.sel?4:(s.excl.includes(d.id)||s.cand.includes(d.id))?3:2.5)
    .attr('opacity',d=>s.excl.includes(d.id)?0.45:1)
    .attr('filter',d=>d.id===s.sel?'url(#pa-gx)':null);

  newPod.transition().duration(700).ease(d3.easeQuadInOut)
    .attr('transform',`translate(${s.newPodX},${s.newPodY})`);

  fadeUpdate('pa-info', s.inf);
  document.getElementById('pa-lbl').textContent=`단계 ${cur+1} / ${SS.length}`;
  document.getElementById('pa-bb').disabled=cur===0;
  document.getElementById('pa-bn').disabled=cur===SS.length-1;
}

window.paB=function(){if(cur>0){cur--;render();}};
window.paN=function(){if(cur<SS.length-1){cur++;render();}};
window.paR=function(){cur=0;render();};
render();
})();
</script>
{{< /rawhtml >}}

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

### Step-by-Step: Taint/Toleration 매칭 과정

{{< rawhtml >}}
<style>
#tt-wrap{font-family:'Space Grotesk',system-ui,sans-serif;background:linear-gradient(135deg,#1e3050 0%,#253c60 60%,#1c2d50 100%);border-radius:14px;padding:20px;box-shadow:0 8px 40px rgba(0,0,0,.6);margin:1.5rem 0;}
.tt-btn{padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;transition:background .15s;}
.tt-btn-p{background:#1f6feb;color:#fff;}.tt-btn-p:hover{background:#388bfd;}
.tt-btn-s{background:#21262d;color:#c9d1d9;border:1px solid #30363d;}.tt-btn-s:hover{background:#30363d;}
.tt-btn:disabled{opacity:.35;cursor:default;}
.tt-legend{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:12px;font-size:16px;font-weight:600;color:#c9d1d9;}
.tt-leg-dot{width:11px;height:11px;border-radius:50%;display:inline-block;margin-right:4px;border:1px solid;}
#tt-info{background:#1e2d45;border-radius:10px;padding:12px 16px;border-left:3px solid #2f81f7;margin-top:12px;font-size:18px;font-weight:600;color:#e6edf3;line-height:1.9;min-height:96px;transition:opacity .15s ease,transform .15s ease;}
</style>

<div id="tt-wrap">
  <div class="tt-legend">
    <span><span class="tt-leg-dot" style="background:#f87171;border-color:#f87171;"></span>Taint (master)</span>
    <span><span class="tt-leg-dot" style="background:#fbbf24;border-color:#fbbf24;"></span>Toleration 없는 Pod</span>
    <span><span class="tt-leg-dot" style="background:#34d399;border-color:#34d399;"></span>Toleration 있는 Pod</span>
  </div>
  <div style="display:flex;gap:8px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">
    <button class="tt-btn tt-btn-s" id="tt-bb" onclick="ttB()">◀ 이전</button>
    <button class="tt-btn tt-btn-p" id="tt-bn" onclick="ttN()">다음 ▶</button>
    <button class="tt-btn tt-btn-s" onclick="ttR()" style="margin-left:4px;">↺ 초기화</button>
    <span id="tt-lbl" style="font-size:16px;color:#8b949e;margin-left:4px;"></span>
  </div>
  <svg id="tt-g" style="width:100%;background:linear-gradient(135deg,#1d3050 0%,#223a5e 100%);border-radius:12px;border:1px solid #21262d;" viewBox="0 0 700 260"></svg>
  <div id="tt-info"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
(function(){
const NL=[
  {id:'master',   x:120,y:160,tainted:true},
  {id:'worker-1', x:350,y:160,tainted:false},
  {id:'worker-2', x:580,y:160,tainted:false}
];
const MF="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";
const C=(v,c)=>`<span style="color:${c};font-weight:700">${v}</span>`;

const SS=[
  {pod:null,podX:350,podY:40,rejected:[],ok:[],
   inf:'master 노드에는 taint(key: node-role.kubernetes.io/master, effect: NoSchedule)가 걸려있다.'},
  {pod:'A',podX:350,podY:40,rejected:[],ok:[],
   inf:`Pod ①을 배치해야 한다. 이 Pod에는 ${C('toleration이 없다','#fbbf24')}.`},
  {pod:'A',podX:350,podY:40,rejected:['master'],ok:['worker-1','worker-2'],
   inf:`toleration이 없으므로 master의 taint를 견딜 수 없다 → ${C('master 배치 거부','#f87171')}.<br>taint 없는 worker-1, worker-2는 정상 배치 가능.`},
  {pod:'A',podX:350,podY:160,rejected:['master'],ok:['worker-1','worker-2'],
   inf:`Pod ①은 ${C('worker-1','#34d399')}에 배치된다.`},
  {pod:'B',podX:350,podY:40,rejected:[],ok:[],
   inf:`Pod ②를 배치해야 한다. 이 Pod는 ${C('key: node-role.kubernetes.io/master, operator: Exists, effect: NoSchedule','#34d399')} toleration을 갖고 있다.`},
  {pod:'B',podX:350,podY:40,rejected:[],ok:['master','worker-1','worker-2'],
   inf:`toleration의 key가 master taint의 key와 일치하고, operator가 Exists라 value는 검사하지 않는다 → ${C('모든 노드 배치 가능','#34d399')} (master 포함).`},
  {pod:'B',podX:120,podY:160,rejected:[],ok:['master','worker-1','worker-2'],
   inf:`Pod ②는 taint를 견딜 수 있으므로 ${C('master','#34d399')}에도 배치될 수 있다.`}
];

let cur=0;
const svg=d3.select('#tt-g');
const defs=svg.append('defs');
const gF=defs.append('filter').attr('id','tt-gx').attr('x','-50%').attr('y','-50%').attr('width','200%').attr('height','200%');
gF.append('feGaussianBlur').attr('stdDeviation',5).attr('result','b');
const fm=gF.append('feMerge');fm.append('feMergeNode').attr('in','b');fm.append('feMergeNode').attr('in','SourceGraphic');

const nG=svg.append('g');
const nGs=nG.selectAll('g').data(NL).enter().append('g').attr('transform',d=>`translate(${d.x},${d.y})`);

nGs.append('rect').attr('class','box').attr('x',-85).attr('y',-60).attr('width',170).attr('height',120).attr('rx',10)
  .attr('fill','#1c2433').attr('stroke','#3a4f6a').attr('stroke-width',2.5);
nGs.append('text').attr('text-anchor','middle').attr('y',-70)
  .attr('fill','#e6edf3').attr('font-size',15).attr('font-weight',700).attr('font-family',MF).text(d=>d.id);
nGs.filter(d=>d.tainted).append('text').attr('text-anchor','middle').attr('y',-40)
  .attr('fill','#f87171').attr('font-size',11).attr('font-family',MF).text('taint: NoSchedule');

const podEl=svg.append('g').attr('id','tt-pod');
podEl.append('circle').attr('id','tt-pod-c').attr('r',18).attr('fill','#fbbf24').attr('stroke','#fff').attr('stroke-width',2);
podEl.append('text').attr('id','tt-pod-t').attr('text-anchor','middle').attr('y',5)
  .attr('fill','#1c2333').attr('font-size',11).attr('font-weight',700).attr('font-family',MF).text('');

function fadeUpdate(id,html){
  const el=document.getElementById(id);
  if(el.innerHTML===html) return;
  el.style.opacity='0';el.style.transform='translateY(6px)';
  setTimeout(()=>{el.innerHTML=html;el.style.opacity='1';el.style.transform='translateY(0)';},140);
}

function render(){
  const s=SS[cur],T=360;
  nGs.select('.box').transition().duration(T)
    .attr('stroke',d=>s.rejected.includes(d.id)?'#f87171':s.ok.includes(d.id)?'#34d399':'#3a4f6a')
    .attr('stroke-width',d=>(s.rejected.includes(d.id)||s.ok.includes(d.id))?3.5:2.5)
    .attr('opacity',d=>s.rejected.includes(d.id)?0.45:1);

  podEl.style('display', s.pod?null:'none');
  d3.select('#tt-pod-c').attr('fill', s.pod==='B'?'#34d399':'#fbbf24');
  d3.select('#tt-pod-t').text(s.pod==='B'?'②':'①');
  podEl.transition().duration(700).ease(d3.easeQuadInOut)
    .attr('transform',`translate(${s.podX},${s.podY})`);

  fadeUpdate('tt-info', s.inf);
  document.getElementById('tt-lbl').textContent=`단계 ${cur+1} / ${SS.length}`;
  document.getElementById('tt-bb').disabled=cur===0;
  document.getElementById('tt-bn').disabled=cur===SS.length-1;
}

window.ttB=function(){if(cur>0){cur--;render();}};
window.ttN=function(){if(cur<SS.length-1){cur++;render();}};
window.ttR=function(){cur=0;render();};
render();
})();
</script>
{{< /rawhtml >}}

### operator 종류

| operator | 설명 |
|---|---|
| Exists | key만 존재하면 매칭, value 불필요 |
| Equal | key와 value 모두 일치해야 매칭 |

Taint의 `value`는 선택 필드다. `value`가 있으면 Pod의 톨러레이션이 `operator: Equal`을 쓸 때 `key`뿐 아니라 `value`까지 정확히 일치해야 통과한다. `value`를 생략하면 빈 문자열("")로 취급되어, `Equal`을 쓸 경우 Pod 쪽 `value`도 비어있어야 매칭된다. `operator: Exists`를 쓰면 애초에 `value`를 보지 않으므로 이 값의 유무는 무관하다.

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

| 리소스 | 사용률 | 상태 |
|---|---|---|
| CPU | 90% | 거의 소진 — 새 Pod 배치 불가 |
| Memory | 20% (4GB 여유) | 남아있지만 CPU가 없어 활용 불가 |

메모리는 남았지만 CPU가 없어 새 Pod가 못 들어오는, 자원이 고립(Stranded)되는 상황이다.

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

### Descheduler 정책 4가지 (쉽게 풀어보기)

**1. RemoveDuplicates — "한 노드에 같은 Pod가 몰려있으면 정리"**

```
평소: Deployment replicas=3
  노드A: Pod 1개 / 노드B: Pod 1개 / 노드C: Pod 1개 (정상)

노드A 장애 발생
  → 컨트롤러가 "3개가 안 되네" 하고 노드B, C에 Pod를 추가로 만듦
  → 노드B: Pod 2개 / 노드C: Pod 2개 (총 5개, 원래는 3개여야 함)

노드A가 복구됨
  → 이제 Pod가 5개나 떠있음 (초과)
  → RemoveDuplicates가 중복분을 지워서 다시 3개로 맞춤
```

같은 서비스의 Pod가 한 노드에 여러 개 몰려도 이 정책이 정리해준다.

**2. LowNodeUtilization — "널널한 노드로 옮겨서 균등하게"**

노드를 세 그룹으로 나눠서 생각하면 쉽다.

```
텅 빈 노드 (threshold 미만)     → Pod를 받아도 되는 노드
적당히 쓰는 노드                → 그냥 둔다
꽉 찬 노드 (targetThreshold 초과) → 여기서 Pod를 퇴거시킨다
```

꽉 찬 노드에서 Pod를 몇 개 내쫓으면, 스케줄러가 그 Pod를 텅 빈 노드에 다시 배치해준다. 결과적으로 노드들의 사용률이 고르게 맞춰진다.

**3. RemovePodsViolatingInterPodAntiAffinity / RemovePodsViolatingNodeAffinity — "규칙이 바뀌었는데 아직 안 지켜진 Pod 정리"**

Affinity 규칙은 **Pod가 처음 배치될 때만** 검사한다. 문제는 배치가 끝난 뒤에 규칙이 새로 추가되거나 노드 라벨이 바뀌는 경우다.

```
Pod가 배치될 당시엔 규칙 없었음 → 정상 배치
    │
    나중에 Affinity 규칙 추가 / 노드 라벨 변경
    │
    이 Pod는 이제 규칙을 위반한 상태 (근데 스케줄러는 신경 안 씀)
    │
    Descheduler가 이 Pod를 퇴거
    │
    스케줄러가 규칙에 맞는 노드로 다시 배치
```

### 절대 건드리지 않는 Pod들

Descheduler가 아무리 정리를 해도, 다음 Pod는 손대지 않는다.

- **핵심 시스템 Pod** — `critical-pod`로 표시된 것들
- **주인 없는 Pod** — ReplicaSet/Deployment/Job 같은 컨트롤러가 관리하지 않는 Pod (퇴거해도 다시 살려줄 사람이 없다)
- **DaemonSet Pod** — 노드마다 1개씩 있어야 하는 Pod라, 퇴거해봤자 그 자리에 다시 생긴다
- **로컬 스토리지 쓰는 Pod** — 옮기면 그 안의 데이터가 사라진다
- **PDB(PodDisruptionBudget) 위반이 되는 Pod** — "이 서비스는 최소 N개는 살아있어야 해"라는 규칙을 어기게 되면 건드리지 않는다
- **Descheduler 자기 자신** — 스스로를 critical-pod로 표시해서 자기 자신은 안전하게 지킨다

### 퇴거 순서 — 덜 중요한 것부터

정리가 필요할 때, 아무 Pod나 무작위로 퇴거시키지 않는다. QoS 등급이 낮은 것부터 순서대로 뺀다.

```
1번으로 퇴거  Best-Effort  → 자원 요청을 아예 안 한 Pod (제일 가벼운 취급)
2번으로 퇴거  Burstable    → 최소 자원만 보장받는 Pod
3번으로 퇴거  Guaranteed   → 요청=제한으로 확실히 보장받는 Pod (제일 마지막까지 보호)
```

중요한 서비스일수록(Guaranteed) 웬만하면 건드리지 않고, 자원 보장이 약한 Pod부터 먼저 정리 대상이 된다.

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

| 방법 | 특징 |
|---|---|
| nodeSelector | 단순 라벨 매칭, 필수만 |
| Node Affinity | 필수/선호, 다양한 연산자 |
| Pod Affinity | 다른 Pod와 같이 배치 |
| Pod Antiaffinity | 다른 Pod와 떨어져 배치 |
| Taints/Tolerations | 노드가 Pod 거부, 허가증으로 접근 |

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

배치는 **최소한으로 개입**하는 게 목표인 영역이다. Chapter 2(Predictable Demands)의 가이드대로 컨테이너의 리소스 요구사항을 제대로 선언해두면, 스케줄러가 알아서 가장 적합한 노드에 Pod를 배치해준다. 그것만으로 부족할 때, 원하는 배포 토폴로지로 스케줄러를 유도하는 방법은 여러 가지가 있다. 아래는 **단순한 것부터 복잡한 것 순**으로 정리한 목록이다 (이 목록은 쿠버네티스 릴리스마다 계속 바뀐다).

### 단순 → 복잡, 7단계 스펙트럼

**1. nodeName — Pod를 노드에 하드와이어링**

Pod를 특정 노드에 직접 못박는 가장 단순한 방법이다. 원래 이 필드는 스케줄러가 정책에 따라 채워야 하는데, 수동으로 지정하면 Pod가 스케줄링될 수 있는 범위가 극도로 좁아진다. 쿠버네티스 이전 시대처럼 "이 앱은 이 노드에서 돌린다"고 못박던 방식으로 되돌아가는 셈이라 지양해야 한다.

**2. nodeSelector — key-value 라벨 매칭**

Pod와 노드에 같은 key-value 라벨이 있어야 배치가 허용된다. Pod와 노드에 의미 있는 라벨을 붙여두는 건 (다른 이유로도) 어차피 해야 할 일이므로, nodeSelector는 스케줄러를 제어하는 가장 무난하고 받아들일 만한 수단이다.

**3. 기본 스케줄러 정책 변경**

기본 스케줄러는 클러스터 안에서 새 Pod를 노드에 배치하는 역할을 웬만큼 잘 해낸다. 하지만 필요하다면 이 스케줄러의 필터링/우선순위 정책 목록, 순서, 가중치(weight)를 바꿀 수도 있다.

**4. Pod Affinity/Antiaffinity**

Pod가 다른 Pod에 대한 의존성을 표현하는 규칙이다. 지연시간 요구사항, 고가용성, 보안 제약 등을 이유로 쓴다.

**5. Node Affinity**

Pod가 노드에 대한 의존성을 표현하는 규칙이다. 노드의 하드웨어, 위치 등을 고려할 때 쓴다.

**6. Taints and Tolerations**

주도권이 Pod가 아니라 **노드**에 있다. 어떤 Pod를 받고 안 받을지 노드가 결정한다. 특정 그룹의 Pod를 위해 노드를 전용화하거나, 런타임에 Pod를 퇴거시키는 데 유용하다. 또 하나의 장점은, 새 라벨을 가진 노드를 클러스터에 추가할 때 **기존의 모든 Pod에 라벨을 새로 붙일 필요 없이**, 그 새 노드에 배치되어야 할 Pod에만 톨러레이션을 추가하면 된다는 점이다.

**7. 커스텀 스케줄러**

위 방법들로도 충분하지 않거나 배치 요구사항이 복잡하다면 스케줄러를 직접 작성할 수도 있다. 커스텀 스케줄러는 기본 스케줄러 대신, 혹은 기본 스케줄러와 나란히 실행될 수 있다. 절충안으로 "스케줄러 익스텐더(scheduler extender)"를 두는 방법도 있는데, 기본 스케줄러가 배치를 결정하는 마지막 단계에서 이 익스텐더를 호출하는 방식이다. 이러면 스케줄러 전체를 구현할 필요 없이 노드를 필터링/우선순위화하는 HTTP API만 제공하면 된다.

직접 스케줄러를 두는 것의 장점은 하드웨어 비용, 네트워크 지연, 리소스 활용도처럼 **쿠버네티스 클러스터 바깥의 요소**까지 배치 결정에 반영할 수 있다는 것이다. 기본 스케줄러와 나란히 여러 커스텀 스케줄러를 동시에 운영하면서, Pod마다 어떤 스케줄러를 쓸지 지정할 수도 있다. 각 스케줄러가 서로 다른 Pod 그룹에 특화된 정책 집합을 가질 수 있다.

### 핵심 요약

이렇게 Pod 배치를 제어하는 방법은 다양하고, 그중 알맞은 방법을 고르거나 여러 방법을 조합하는 일은 까다로울 수 있다. 이 챕터에서 가져갈 핵심은 다음 세 가지다.

```
1. 컨테이너 리소스 프로파일을 제대로 산정하고 선언하라
2. Pod와 노드에 적절히 라벨을 붙여라
3. 쿠버네티스 스케줄러에는 최소한으로만 개입하라
```

다음 챕터 Self Awareness는 애플리케이션이 자기 자신에 대한 메타데이터(Pod 이름, 네임스페이스, 리소스 제한 등)를 다운워드 API로 조회하는 방법을 다룬다.