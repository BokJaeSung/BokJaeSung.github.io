---
series: ["K8sPatterns"]
title: "K8sPatterns.12 Stateful Service"
date: 2026-07-20T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "stateful"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.12 Stateful Service'
  relative: true
summary: "고유하고 교체 불가능한 인스턴스로 구성된 스테이트풀 애플리케이션을 Kubernetes에서 운영하는 방법 — StatefulSet, Headless Service, PVC까지."
---

## 1. Overview

```
Stateful Service 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

스테이트풀 서비스 = 고유하고 교체 불가능한 인스턴스들의 집합
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
        Pod를 순서대로        직접 접근 가능한      인스턴스별 전용
          유지·관리           네트워크 신원          영구 스토리지
        (StatefulSet)     (Headless Service)    (volumeClaimTemplates)
```

Stateful Service 패턴은 **고유하고 교체 불가능한 인스턴스들**로 구성된 분산 스테이트풀 애플리케이션을 만들고 운영하는 방법을 설명한다. 영속적 신원, 안정적 네트워킹, 전용 스토리지, 순서성이 필요한 데이터베이스·메시지 큐·분산 코디네이터 같은 워크로드에 적합한 패턴이다.

---

## 2. Problem

### 모든 무상태 서비스 뒤에는 스테이트풀 서비스가 있다

아무리 잘 만들어진 무상태 서비스라도, 결국 그 뒤에는 데이터를 저장하는 스테이트풀 계층이 반드시 존재한다.

```
사용자 요청
    ↓
[Stateless 서비스]   ← Kubernetes가 잘 관리
API 서버 / 웹 서버
    ↓
[Stateful 서비스]    ← 초창기 Kubernetes가 못 관리
데이터베이스 / 캐시 / 메시지 큐
```

Kubernetes 초창기에는 스테이트풀 워크로드를 지원하지 않았기 때문에, 무상태 앱만 Kubernetes에 올리고 스테이트풀 컴포넌트는 클러스터 외부(퍼블릭 클라우드 관리형 DB, 온프레미스 하드웨어)에서 전통적인 방식으로 관리했다.

여기서 주의할 점이 있다. **"클러스터 외부"는 "클라우드 외부"가 아니다.** 클러스터는 Kubernetes가 관리하는 노드들의 집합이고, 클라우드는 AWS·GCP·Azure 같은 인프라 환경이다. AWS RDS처럼 클라우드에 두더라도 Kubernetes 클러스터가 관리하지 않으면 "클러스터 밖"이다.

```
초창기 Kubernetes 아키텍처

Public Cloud (AWS 등)

Kubernetes Cluster (무상태앱 관리) ──▶ RDS, S3 등 클라우드 관리형 DB
        클러스터 안                          클러스터 밖

→ 스테이트풀 앱은 클라우드 안에 있어도
  Kubernetes가 관리하지 않으면 "클러스터 밖"
```

기업 워크로드의 대부분이 스테이트풀인데, Kubernetes가 이를 지원하지 못한다면 "범용 클라우드 네이티브 플랫폼"이라고 부를 수 없었다. 이것이 StatefulSet 탄생의 역사적 배경이다.

### 무상태 vs 스테이트풀: 근본적인 차이

| 항목 | Stateless App | Stateful App |
|---|---|---|
| 인스턴스 특성 | 모두 동일 (교체 가능) | 각각 고유 (교체 불가) |
| 데이터 | 저장 안 함 | 자체 데이터 보유 |
| 재시작 | 아무 인스턴스나 OK | 동일 인스턴스여야 함 |
| 이름/주소 | 바뀌어도 무관 | 고정되어야 함 |
| 확장 | 자유롭게 가능 | 순서/절차 필요 |
| 예시 | 웹 서버, API 서버 | DB, Kafka, ZooKeeper |

스테이트풀 앱이 필요로 하는 것들:

```
① Persistent Identity  재시작 후에도 동일한 이름/ID 유지
② Networking           안정적이고 예측 가능한 네트워크 주소
③ Storage              데이터가 사라지지 않는 영구 저장소
④ Ordinality           Pod 간의 명확한 순서와 역할 구분
```

### ReplicaSet으로 스테이트풀 앱을 다루면 생기는 문제

Deployment/ReplicaSet으로도 MySQL, Redis 같은 스테이트풀 앱을 어느 정도 운영할 수 있다.

```
ReplicaSet (replicas=1) + Service + PVC 조합

[MySQL Pod] ──→ [Service] ──→ 클라이언트 접근
     │
     ▼
[PVC] ──→ [PV: 영구 스토리지]
```

하지만 이 방식에는 근본적인 한계가 있다.

**① At-Most-One 미보장**

ReplicaSet은 At-Least-X 시맨틱스를 따른다. "최소 X개는 반드시 유지"가 목표이므로, Pod 교체 중에 잠깐 X개를 초과하는 것은 허용된다.

```
Pod 교체 중 발생하는 상황

기존 Pod  종료 중... (아직 살아있음)
새 Pod    이미 시작됨

→ 잠깐이라도 두 Pod가 동시에 같은 PV에 접근
→ Pod-A: "재고 = 10개" 저장
→ Pod-B: "재고 = 8개" 저장 (덮어씀)
→ 어떤 데이터가 맞는 건지 알 수 없음 💀
```

**② 다중 인스턴스 클러스터링 불가 — 스토리지 문제**

replicas=3으로 늘리면 분산 스테이트풀 앱처럼 보이지만, PVC가 하나라면 모든 Pod가 같은 디스크를 공유한다.

```
replicas=3 + PVC 하나

[rg-0] ──┐
[rg-1] ──┼──→ [PVC] ──→ [PV 하나] ← 전부 공유 ❌
[rg-2] ──┘

MySQL Master-Slave 구성이라면?
→ Master와 Slave가 같은 디스크를 공유 → 불가능 💀

기숙사 방 하나를 여러 명이 공유하는 구조 →
각자 자신만의 방(전용 PV)이 반드시 필요
```

이에 대한 우회책도 존재하지만, 모두 미봉책에 불과하다.

```
우회책 1 — PV 안에 서브폴더 나눠 쓰기
/data/rg-0/  ← rg-0 전용
/data/rg-1/  ← rg-1 전용

문제: PV 하나가 죽으면 전부 사망 (단일 장애점)
     스케일링 시 폴더 충돌, 고아 데이터 발생

우회책 2 — 인스턴스마다 ReplicaSet 분리
ReplicaSet-0 + PVC-0 + Service-0
ReplicaSet-1 + PVC-1 + Service-1

문제: 스케일 업마다 모든 리소스를 수동 생성
     "MySQL 클러스터 전체"라는 단일 추상화 없음
     관리 복잡도 폭증
```

**③ 인스턴스를 구별할 방법이 없음 — 네트워킹 문제**

```
ReplicaSet의 Pod 이름
rg-7d6f8b-xk2pq   (랜덤 해시)
rg-7d6f8b-ab3nz   (랜덤 해시)
→ 재시작하면 이름 바뀜
→ "Master는 항상 이 Pod" 보장 불가
→ Slave가 재시작된 Master를 찾을 수 없음

ReplicaSet의 Pod IP 문제
최초 배포: Master IP = 10.0.0.1 → Slave들이 이 주소 저장
재시작 후: Master IP = 10.0.0.7 (바뀜!)
→ Slave-1: "Master가 10.0.0.1인데..." → 연결 실패 💀
```

우회책으로 ReplicaSet마다 Service를 만들 수 있지만, Pod 자체의 호스트명은 재시작마다 바뀌고 자신이 어떤 Service 이름으로 접근되는지도 알 수 없다.

### Pets vs Cattle

DevOps 세계에서 유명한 비유로 StatefulSet의 설계 철학을 잘 설명할 수 있다.

```
ReplicaSet (Cattle 🐄)          StatefulSet (Pets 🐕)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
소 100마리 중 한 마리가 아파요      반려견 "초코"가 아파요
→ 그냥 새 소로 교체하면 됨          → 새 강아지로 교체? ❌
→ 이름도 없고, 개별 관리 불필요      → 이름이 있고, 고유한 특성 보유
→ 모두 동일하고 교체 가능            → 개별적인 관리와 치료가 필요
```

StatefulSet은 초기에 이 비유에서 영감을 받아 **PetSet**이라 불렸다가, 더 중립적인 이름인 StatefulSet으로 바뀌었다.

---

## 3. Solution: StatefulSet

### Example 12-1. StatefulSet 정의

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: rg                          # ① Pod 이름의 접두사 — rg-0, rg-1 생성
spec:
  serviceName: random-generator     # ② 연결할 Headless Service 이름 (DNS 생성에 사용)
  replicas: 2                       # ③ 두 개의 Pod — rg-0, rg-1
  selector:
    matchLabels:
      app: random-generator         # ④ 아래 template의 라벨과 반드시 일치해야 함
  template:
    metadata:
      labels:
        app: random-generator       # ⑤ Headless Service의 selector가 찾는 라벨
    spec:
      containers:
      - image: k8spatterns/random-generator:1.0   # ⑥ 각 Pod(rg-0, rg-1)에 동일하게 적용되는 이미지
        name: random-generator
        ports:
        - containerPort: 8080       # ⑦ Headless Service의 port(8080)와 매칭되는 컨테이너 포트
          name: http                # ⑧ 포트 이름 — Service의 port 이름(http)과 연결
        volumeMounts:
        - name: logs                # ⑨ 아래 volumeClaimTemplates의 name과 매칭
          mountPath: /logs          # ⑩ 컨테이너 내부에서 PVC가 마운트되는 경로
  volumeClaimTemplates:             # ⑪ Pod마다 전용 PVC를 자동 생성 (ReplicaSet에는 없는 기능)
  - metadata:
      name: logs                   # ⑫ PVC 이름 접두사 — logs-rg-0, logs-rg-1 생성
    spec:
      accessModes: [ "ReadWriteOnce" ]   # ⑬ 한 번에 하나의 노드에서만 마운트 가능
      resources:
        requests:
          storage: 10Mi            # ⑭ Pod별로 요청하는 전용 볼륨 크기
```

ReplicaSet YAML과 비교했을 때 눈에 띄는 차이는 두 가지다. `serviceName` 필드와 `volumeClaimTemplates` 블록. 이 두 가지가 StatefulSet의 핵심이다.

StatefulSet이 생성하는 리소스:

```
StatefulSet (rg)
├── Pod: rg-0
│   └── PVC: logs-rg-0 ──→ PV-0 (10Mi)
│
└── Pod: rg-1
    └── PVC: logs-rg-1 ──→ PV-1 (10Mi)

+ Headless Service (random-generator)
  ├── rg-0.random-generator.default.svc.cluster.local (DNS)
  └── rg-1.random-generator.default.svc.cluster.local (DNS)
```

---

## 4. Storage

### volumeClaimTemplates: Pod처럼 PVC도 찍어낸다

ReplicaSet은 이미 존재하는 PVC를 이름으로 참조한다. StatefulSet은 Pod 템플릿처럼 PVC 템플릿을 정의하고, Pod가 생성될 때 즉석에서(on the fly) PVC를 자동 생성한다.

```
ReplicaSet 방식 (persistentVolumeClaim)
────────────────────────────────────────
미리 만들어진 PVC 하나를 가져다 씀

[rg-0] ──┐
[rg-1] ──┼──→ [PVC 하나] ──→ [PV 하나] 공유 ❌
[rg-2] ──┘


StatefulSet 방식 (volumeClaimTemplates)
────────────────────────────────────────
Pod 생성 시 PVC를 즉석에서 자동 생성

[rg-0] ──→ [logs-rg-0] ──→ [PV-0] 전용 ✅
[rg-1] ──→ [logs-rg-1] ──→ [PV-1] 전용 ✅
```

이름 생성 규칙:

```
Pod 이름   = StatefulSet이름 + 순번  =  rg-0, rg-1
PVC 이름   = 템플릿이름 + Pod이름    =  logs-rg-0, logs-rg-1
```

### PV는 누가 만드나?

StatefulSet이 PVC 발급까지만 담당하고, 실제 디스크(PV)는 외부 주체가 담당한다는 점을 명확히 이해해야 한다.

```
역할 분담

StatefulSet   →  Pod 생성, PVC 자동 생성
관리자         →  PV 수동 생성 (Static Provisioning)
StorageClass  →  PVC 생성 감지 후 PV 자동 생성 (Dynamic Provisioning)
```

| 생성 주체 | ReplicaSet | StatefulSet |
|---|---|---|
| Pod | ✅ 직접 | ✅ 직접 |
| PVC | ❌ 관리자가 미리 | ✅ 자동 생성 |
| PV | ❌ 관리자/SC | ❌ 관리자/SC |

실무에서는 StorageClass + Dynamic Provisioning을 사용해 PV까지 자동 생성되는 것이 일반적이다. PVC가 생성되면 StorageClass가 감지하고, 클라우드 인프라(AWS EBS, GCP PD 등)에서 PV를 자동으로 생성해 바인딩한다. 온프레미스 환경에서만 관리자가 PV를 미리 만들어두는 경우가 많다.

```
Dynamic Provisioning 흐름

StatefulSet 배포
    ↓
logs-rg-0 PVC 자동 생성
    ↓
StorageClass가 PVC 감지
    ↓
AWS EBS / GCP PD 등에서 PV 자동 생성 ✅
    ↓
PVC ↔ PV 자동 바인딩
    ↓
rg-0 Pod가 마운트하여 사용
```

### 스케일링의 비대칭 동작 (중요)

StatefulSet 스케일링에서 가장 중요한 특성 중 하나다. 스케일 업과 다운의 동작이 **비대칭**이다.

```
스케일 업 (replicas 2 → 3)
─────────────────────────────
✅ rg-2 Pod    생성
✅ logs-rg-2   PVC 자동 생성
✅ PV-2        생성 (StorageClass 있을 시)

스케일 다운 (replicas 3 → 2)
─────────────────────────────
✅ rg-2 Pod    삭제
❌ logs-rg-2   PVC 유지! (삭제 안 됨)
❌ PV-2        유지! (비용 계속 발생 ⚠️)
```

이 동작은 의도적 설계다. **실수로 인한 스케일 다운이 데이터 손실로 이어지지 않도록** 하기 위함이다. 나중에 rg-2가 다시 생성되면 logs-rg-2 PVC에 자동으로 재연결된다.

데이터가 필요 없어졌을 때는 PVC를 수동으로 삭제해야 한다.

```
안전한 스케일 다운 절차

1단계: 데이터 이전 확인
   rg-2의 데이터가 rg-0, rg-1로 완전히 복제됐는지 확인 ✅
2단계: 스케일 다운
   kubectl scale statefulset rg --replicas=2
3단계: PVC 수동 삭제
   kubectl delete pvc logs-rg-2
4단계: PV 자동 정리 (StorageClass reclaimPolicy에 따라)
```

---

## 5. Networking

### 안정적 네트워크 신원이 필요한 이유

스테이트풀 앱은 단순히 데이터만 저장하는 것이 아니다. **호스트명, 피어(peers)들의 연결 주소** 같은 설정값도 저장한다. 즉, 인스턴스들이 서로를 찾기 위한 "주소록"이 앱 내부에 있다.

Pod IP는 재시작마다 바뀌기 때문에, 이 주소록이 금방 쓸모없어진다.

```
문제 상황

MySQL Slave의 설정 파일
  master_host = 10.0.0.1  ← Master의 IP 저장

Master Pod 재시작 발생
  재시작 전 IP: 10.0.0.1
  재시작 후 IP: 10.0.0.7  (바뀜!)

Slave: "10.0.0.1로 연결 시도..."
→ 응답 없음, 연결 실패 💀
```

### Headless Service: 직통번호 발급소

StatefulSet은 이 문제를 Headless Service를 통해 해결한다.

```yaml
# Example 12-2. Headless Service
apiVersion: v1
kind: Service
metadata:
  name: random-generator          # ① StatefulSet의 serviceName과 반드시 일치해야 함
spec:
  clusterIP: None                 # ② 이게 Headless — 대표 IP 없음, 로드밸런서 없음
  selector:
    app: random-generator         # ③ 이 라벨을 가진 Pod들을 DNS에 등록
  ports:
  - name: http                    # ④ 포트 이름 — SRV 레코드에도 그대로 노출됨
    port: 8080                    # ⑤ 각 Pod의 A/SRV 레코드에 매핑되는 서비스 포트
```

일반 Service와 Headless Service의 차이:

```
일반 Service (clusterIP 있음)
─────────────────────────────────────
"교환원이 연결해주는 대표번호"

클라이언트 ──→ [Service IP: 10.96.0.1]
                      ↓ 로드밸런싱
               rg-0 or rg-1 (어디로 갈지 모름)


Headless Service (clusterIP: None)
─────────────────────────────────────
"교환원 없는 직통번호 목록"

클라이언트 ──→ rg-0.random-generator... ──→ rg-0 직접 ✅
클라이언트 ──→ rg-1.random-generator... ──→ rg-1 직접 ✅
```

Headless Service가 하는 일과 하지 않는 일:

```
✅ 각 Pod에 고정 DNS 주소 부여 (A 레코드)
✅ 전체 멤버 조회 지원 (SRV 레코드)
✅ CoreDNS에 엔드포인트 레코드 등록
❌ 로드밸런싱 없음
❌ 대표 ClusterIP 없음
❌ kube-proxy 개입 없음
```

### DNS 주소 체계: A 레코드와 SRV 레코드

Headless Service가 생성되면 CoreDNS(클러스터 내부 DNS 서버)에 두 종류의 레코드가 자동 등록된다.

```
A 레코드 — 특정 Pod 직접 접근
────────────────────────────────────────────────────
dig A rg-0.random-generator.default.svc.cluster.local
→ 10.0.0.5 (rg-0의 IP만 반환)

rg-0  .  random-generator  .  default  .  svc  .  cluster.local
 ↑              ↑               ↑          ↑           ↑
Pod이름      Service이름     네임스페이스   리소스    클러스터 도메인


SRV 레코드 — 전체 멤버 조회 (IP + 포트 + 호스트명)
────────────────────────────────────────────────────
dig SRV random-generator.default.svc.cluster.local
→ rg-0.random-generator.default.svc.cluster.local:8080
→ rg-1.random-generator.default.svc.cluster.local:8080

random-generator.default.svc.cluster.local
        ↑
  Service 이름으로 조회 → 전체 Pod 목록 반환
```

두 레코드의 용도 차이:

```
A 레코드  = "강남점 직통번호"   (특정 Pod에 직접 접근)
SRV 레코드 = "지점 전체 전화번호부" (멤버 목록 + 포트까지 한번에)
```

SRV 레코드가 강력한 이유는 **동적 클러스터 멤버 검색** 때문이다. replicas를 늘리면 새 Pod가 SRV 레코드에 자동 등록되어, 앱이 하드코딩 없이 새 멤버를 자동으로 감지할 수 있다.

```
스케일 업 후 SRV 재조회
→ rg-0, rg-1, rg-2 모두 반환 ✅ (자동 반영)
```

### 레코드는 어디에 저장되나?

```
쿠버네티스 클러스터 내부의 CoreDNS Pod
(kube-system 네임스페이스에 존재)

Headless Service 생성
    ↓
API 서버가 Endpoints 오브젝트 생성
    ↓
CoreDNS가 API 서버를 감시
    ↓
CoreDNS 내부에 A/SRV 레코드 자동 등록

Pod 재시작 → IP 바뀜 → CoreDNS 자동 업데이트
→ DNS 주소 자체는 불변 ✅
```

스테이트풀 앱에서 두 DNS를 언제 쓰나:

```
A 레코드 (특정 Pod 지정)         SRV 레코드 (전체 멤버 파악)
────────────────────────────────────────────────────
쓰기 요청 → rg-0 (Master)만      "지금 몇 개 떠있지?"
읽기 요청 → rg-1 (Slave) 지정    새 멤버 자동 감지
특정 샤드 담당 Pod 접근           클러스터 초기화 시
```

스테이트풀 앱에서는 대부분 **A 레코드(특정 Pod 직접 지정)** 를 쓴다. Service 전체 조회(`random-generator.default...`)는 앱 자체가 라우팅을 처리할 수 있는 경우에만 제한적으로 사용한다.

### Headless Service ↔ StatefulSet 양방향 연결

단순 selector만으로는 부족하다. **양쪽에서 서로를 참조**해야 완전한 네트워크 신원이 부여된다.

```
StatefulSet → Service 참조
────────────────────────────────
spec:
  serviceName: "random-generator"  ← Service 이름 명시

Service → Pod 참조
────────────────────────────────
spec:
  selector:
    app: random-generator          ← Pod 레이블로 선택

둘 다 있어야:
rg-0.random-generator... DNS 생성 ✅
SRV 레코드 등록 ✅
완전한 네트워크 신원 부여 ✅
```

`serviceName`이 없으면 DNS가 생성되지 않아 Pod에 직접 접근할 방법이 사라진다. selector가 없으면 Service가 Pod를 찾지 못한다. 두 가지는 반드시 함께 설정해야 한다.

---

## 6. Ordinality (순서성)

StatefulSet의 Pod 이름에 붙는 서수(ordinal)는 단순한 번호가 아니다. 이 번호가 **역할, 스케일링 순서, 업데이트 순서**를 결정한다.

```
rg-0 → 가장 먼저 생성 → 보통 Master / Leader 역할
rg-1 → 두 번째 생성  → Follower / Slave
rg-2 → 세 번째 생성  → Follower / Slave
```

### 스케일 업: 순차 시작 (0 → n-1)

```
replicas: 0 → 3

타임라인
t=0   rg-0 시작
t=3   rg-0 Running + Ready 확인 ✅
t=3   rg-1 시작       ← rg-0 완료 후!
t=6   rg-1 Running + Ready 확인 ✅
t=6   rg-2 시작       ← rg-1 완료 후!
t=9   rg-2 Running + Ready 확인 ✅

핵심: 이전 Pod가 완전히 준비되기 전까지
      다음 Pod는 절대 시작하지 않음
```

### 스케일 다운: 역순 종료 (n-1 → 0)

```
replicas: 3 → 0

STEP 1: rg-2 종료 → 완전히 종료 확인 ✅
         ↓
STEP 2: rg-1 종료 → 완전히 종료 확인 ✅
         ↓
STEP 3: rg-0 종료

핵심: 항상 높은 인덱스부터, 하나씩 완전히 종료 후 다음
```

### 왜 순서가 중요한가?

```
MySQL Master-Slave 예시

스케일 업 시
rg-0 (Master) 완전히 준비됨
    ↓
rg-1 (Slave) 시작: "rg-0.random-generator...에 연결해서 복제 시작" ✅

만약 동시에 시작되면?
rg-1: "Master 어딨지?" → 연결 실패 💀


스케일 다운 시 (역순이므로 Master가 마지막)
rg-2 데이터를 rg-0, rg-1로 이전 후 종료
    ↓
rg-1 데이터를 rg-0으로 이전 후 종료
    ↓
rg-0 (Master) 마지막 종료 ✅

만약 Master(rg-0)가 먼저 종료되면?
→ Slave들이 Master를 잃고 혼란 💀
```

### ZooKeeper 3노드 앙상블과 순서성

ZooKeeper는 분산 코디네이션 서비스로, 리더 선출과 설정 공유를 담당한다. 혼자 있으면 단일 장애점이 되기 때문에, 보통 **홀수 노드(3, 5, 7)** 로 앙상블을 구성한다.

```
ZooKeeper 3노드 앙상블

┌──────────┐   ┌──────────┐   ┌──────────┐
│  rg-0    │◄──│  rg-1    │◄──│  rg-2    │
│ (Leader) │──►│(Follower)│──►│(Follower)│
└──────────┘   └──────────┘   └──────────┘
      ↑
  투표로 뽑힌 리더 (3개 중 2표 이상 = 과반수)

왜 홀수인가?
1대 → 죽으면 끝
2대 → 1대 죽으면 "과반수?" 판단 불가 😵
3대 → 1대 죽어도 2표로 리더 선출 가능 ✅
```

StatefulSet의 순서 보장이 있어야 rg-0이 먼저 완전히 떠서 리더로 선출되고, rg-1, rg-2가 순서대로 앙상블에 합류할 수 있다.

### ReplicaSet vs StatefulSet 스케일링 비교

| 항목 | ReplicaSet | StatefulSet |
|---|---|---|
| 스케일 업 | 동시에 시작 | 순서대로 하나씩 (0→n-1) |
| 스케일 다운 | 동시에 종료 | 역순으로 하나씩 (n-1→0) |
| 속도 | 빠름 ✅ | 느림 ⚠️ |
| 안전성 | 낮음 ❌ | 높음 ✅ |
| 대상 앱 | 무상태 | 스테이트풀 |

---

## 7. Other Features

### Partitioned Updates (파티셔닝 업데이트)

스케일링뿐 아니라 이미 실행 중인 StatefulSet을 업데이트할 때도 순서가 중요하다. `.spec.updateStrategy.rollingUpdate.partition` 파라미터로 업데이트 범위를 제어할 수 있다.

```yaml
spec:
  updateStrategy:
    type: RollingUpdate        # ① 롤링 업데이트 전략 사용 (다른 옵션: OnDelete)
    rollingUpdate:
      partition: 2             # ② 인덱스 2 이상만 업데이트, 0~1은 보호 (기본값: 0)
```

```
partition: 2 설정 시 (Pod 4개: rg-0 ~ rg-3)

rg-0  구버전 🔒  (0 < 2, 보호됨)
rg-1  구버전 🔒  (1 < 2, 보호됨)
rg-2  신버전 ✅  (2 ≥ 2, 업데이트)
rg-3  신버전 ✅  (3 ≥ 2, 업데이트)
```

**핵심**: partition 미만의 Pod는 강제로 삭제해도 **구버전으로 재생성**된다. partition이 일종의 "버전 보호막" 역할을 한다.

```
partition: 2인 상태에서 rg-0을 강제 삭제하면?
→ 쿠버네티스가 rg-0을 구버전으로 재생성 ✅
→ 신버전으로 올라가지 않음
```

이를 활용해 쿼럼을 유지하면서 단계적으로 전체 업데이트를 진행할 수 있다.

```
ZooKeeper 5노드 쿼럼(과반수 = 3개) 유지하며 업데이트

1단계: partition: 3
   rg-0 구버전 🔒 ┐
   rg-1 구버전 🔒 ├─ 3개 유지 → 쿼럼 보존 ✅
   rg-2 구버전 🔒 ┘
   rg-3 신버전 업데이트
   rg-4 신버전 업데이트
   → 업데이트 중에도 항상 3개 이상 운영 ✅

2단계: 안정 확인 후 partition: 0
   → 전체 업데이트 완료
```

partition 값에 따른 동작 요약:

```
partition: 0   → 모든 Pod 업데이트 (기본값)
partition: 2   → rg-2 이상만 업데이트, rg-0/rg-1 보호
partition: 999 → 아무것도 업데이트 안 됨 (일시 중단 효과)
```

### Parallel Deployments (병렬 배포)

순서가 필요 없는 스테이트풀 앱이라면, `podManagementPolicy: Parallel`로 ReplicaSet처럼 동시에 시작/종료할 수 있다.

```yaml
spec:
  podManagementPolicy: Parallel   # 모든 Pod를 동시에 시작/종료 (기본값: OrderedReady)
```

```
OrderedReady (기본)       Parallel
────────────────────────────────────
rg-0 시작                rg-0 ┐
    ↓ Ready 확인         rg-1 ├ 동시에!
rg-1 시작                rg-2 ┘
    ↓ Ready 확인
rg-2 시작
```

| 정책 | 순서 보장 | 속도 |
|---|---|---|
| OrderedReady (기본) | ✅ 있음 | ❌ 느림 |
| Parallel | ❌ 없음 | ✅ 빠름 |

언제 각 정책을 쓰나:

```
OrderedReady (기본)
→ MySQL Master-Slave (Master 먼저 떠야 Slave 연결 가능)
→ ZooKeeper 앙상블 (리더 선출 순서 중요)

Parallel
→ Redis 캐시 클러스터 (노드들이 독립적)
→ Elasticsearch (클러스터가 자체적으로 멤버 동기화)
```

### At-Most-One Guarantee

StatefulSet의 가장 핵심적인 보장이다. 동일한 신원의 Pod가 동시에 2개 이상 존재하지 않음을 보장한다.

| 항목 | ReplicaSet (At-Least-X) | StatefulSet (At-Most-One) |
|---|---|---|
| 목표 | 최소 X개는 반드시 유지 | 동일한 Pod는 최대 1개만 존재 |
| 초과 허용 | 일시적으로 X개 초과 허용 | 이전 Pod 완전 종료 확인 후 생성 |
| 노드 장애 시 | 즉시 새 Pod 생성 | 확인될 때까지 대기 |
| 복구 속도 | 빠른 복구 | 느린 복구 |
| 중복 가능성 | 있음 | 없음 |

노드 장애 시 동작 차이:

```
ReplicaSet (At-Least-X)        StatefulSet (At-Most-One)
───────────────────────────────────────────────────────────
Node-1 NotReady 감지            Node-1 NotReady 감지
         ↓                               ↓
즉시 Node-2에 새 Pod 생성        "확인될 때까지 대기"
→ 빠른 복구 ✅                   새 Pod 생성 안 함 🔒
→ 중복 가능성 있음 ⚠️            → 느린 복구 ⚠️
                                 → 중복 절대 없음 ✅
```

**보장을 깨는 방법 (주의)**

이 보장은 쿠버네티스 혼자서는 절대 깨지 않는다. 하지만 **인간의 적극적 개입**이 있으면 깨질 수 있다.

```
방법 1: 살아있는 노드를 API에서 강제 삭제
kubectl delete node node-1  (물리 노드는 아직 살아있음!)
→ API 서버: "node-1 없음"
→ StatefulSet 컨트롤러: "Pod 없네? 새로 만들어야겠다"
→ Node-2에 rg-0 새로 생성
→ Node-1의 rg-0도 살아있음 → 중복 발생 💀


방법 2: Pod 강제 삭제 (--grace-period=0 --force)
kubectl delete pod rg-0 --grace-period=0 --force

정상 삭제와의 차이:
정상: Kubelet 확인 → Pod 완전 종료 → 새 Pod 시작
강제: API에서 즉시 삭제 → Kubelet 확인 없음 → 새 Pod 즉시 시작
→ 기존 Pod가 아직 살아있으면 중복 발생 💀
→ grace-period=0이므로 데이터 마무리 작업도 없음
```

안전한 강제 조치 조건:

```
노드 강제 삭제 허용 조건
→ 물리 노드 전원이 완전히 꺼진 것을 확인 ✅
→ 해당 노드에 실행 중인 Pod 프로세스 없음 확인 ✅

Pod 강제 삭제 허용 조건
→ 해당 노드가 완전히 격리됨 확인 ✅
→ 데이터 백업 완료 확인 ✅
→ 정말 긴급한 상황에서만 최후의 수단으로
```

---

## 8. 전체 구조 한눈에 보기

```
클러스터 내부
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Headless Service: random-generator]
  clusterIP: None
  selector: app=random-generator
         │
    ┌────┴────┐
    ▼         ▼
  rg-0      rg-1        ← StatefulSet이 생성한 Pod (이름 항상 고정)
  (Pod)     (Pod)
    │         │
    ▼         ▼
logs-rg-0  logs-rg-1    ← volumeClaimTemplates로 자동 생성된 PVC
  (PVC)      (PVC)
    │         │
    ▼         ▼
  PV-0      PV-1        ← 완전히 독립된 디스크
 (10Mi)    (10Mi)

DNS 접근 (CoreDNS에 자동 등록)
rg-0.random-generator.default.svc.cluster.local → rg-0 직접
rg-1.random-generator.default.svc.cluster.local → rg-1 직접

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

각 구성 요소가 해결하는 문제:

| 구성 요소 | 해결하는 문제 | 핵심 동작 |
|---|---|---|
| **StatefulSet** | Pod 순서·신원 보장 | 고정 이름(rg-0, rg-1), 순차 시작/종료 |
| **volumeClaimTemplates** | 인스턴스별 전용 스토리지 | Pod 생성 시 PVC 자동 생성 |
| **Headless Service** | 안정적 네트워크 신원 | 고정 DNS, A/SRV 레코드 (CoreDNS 등록) |
| **At-Most-One** | 중복 Pod 방지 | 종료 확인 후 재생성, 노드 장애 시 대기 |
| **Partition** | 안전한 단계적 업데이트 | 인덱스 기반 업데이트 보호, 쿼럼 유지 |
| **podManagementPolicy** | 순서 vs 속도 트레이드오프 | OrderedReady / Parallel 선택 |

---

## 9. Discussion

이 챕터에서 배운 핵심 내용을 정리하면 다음과 같다.

```
단일 인스턴스 스테이트풀 앱
→ Deployment + PVC로 어느 정도 가능
→ 하지만 At-Most-One 미보장 → 데이터 손실 위험

분산 스테이트풀 앱
→ 스토리지, 네트워킹, 신원, 순서성 모두 필요
→ ReplicaSet 우회책들 (서브폴더, RS 분리)은 모두 한계
→ StatefulSet이 하나의 추상화로 해결
```

"상태(State)"는 단순히 스토리지만이 아니다. 스테이트풀 앱이 필요로 하는 상태의 여러 측면:

```
📦 스토리지       인스턴스별 전용 PV (volumeClaimTemplates)
🌐 네트워킹       고정 DNS 주소 (Headless Service)
🏷️ 신원           고정된 Pod 이름 (ordinal suffix)
🔢 순서성         생성/종료 순서 보장 (OrderedReady)
🗳️ 쿼럼           최소 인스턴스 수 유지 (Partition 활용)
🔒 중복 방지      At-Most-One 시맨틱스
```

StatefulSet이 해결하지 못하는 케이스도 있다. 앱마다 고유한 특수 요구사항들 — 자동 백업, 커스텀 페일오버 로직, 특수한 스케일링 절차 — 은 StatefulSet만으로 커버할 수 없다. 쿠버네티스는 이를 위해 **CRD + Operator** 패턴을 제공한다.

```
수준 1: Deployment + PVC
→ 단순 단일 인스턴스 스테이트풀 앱

수준 2: StatefulSet
→ 분산 스테이트풀 앱의 공통 요구사항 해결

수준 3: CRD + Operator
→ 앱 특화 운영 로직 완전 자동화
  (백업, 페일오버, 쿼럼 관리, 커스텀 스케일링)
  → Chapter 27, 28에서 다룸
```

결국 StatefulSet은 스테이트풀 앱을 클라우드 네이티브의 **이등 시민에서 일등 시민으로 승격**시킨 핵심 프리미티브다. 무상태 앱에서 Deployment가 하는 역할을, 스테이트풀 앱에서는 StatefulSet이 담당한다.

> Stateful Service는 **고유하고 교체 불가능한 인스턴스**로 구성되며, StatefulSet + Headless Service + volumeClaimTemplates의 조합으로 스토리지·네트워킹·신원·순서성 전 과정을 자동화할 수 있다. 각 구성 요소는 서로를 직접 알지 못하고 **label과 serviceName이라는 연결 고리**로만 묶인다. Kubernetes는 이 빌딩 블록들의 조합으로 스테이트풀 앱을 **클라우드 네이티브 일급 시민**으로 다룰 수 있게 한다.