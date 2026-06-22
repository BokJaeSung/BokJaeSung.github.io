---
title: "K8sPatterns.01 Introduction"
date: 2026-06-22T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "microservices", "container", "pod"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.01 Introduction'
  relative: true
summary: "A beginner-friendly summary of Chapter 1 from Kubernetes Patterns — covering containers, pods, services, labels, annotations, and namespaces."
---

## 들어가며

이 포스트는 *Kubernetes Patterns* 1챕터를 읽고 정리한 내용입니다.  
"클라우드 네이티브가 뭔데?" 라는 질문에서 시작해서, Kubernetes의 핵심 개념들을 쉽게 풀어봤습니다.

---

{{< rawhtml >}}
<details style="background:transparent;border:1px solid #30363d;border-radius:8px;padding:10px 16px;margin:1.2rem 0;font-family:inherit;">
<summary style="cursor:pointer;font-weight:600;font-size:14px;color:#8b949e;user-select:none;font-family:inherit;">목차 — Table of Contents</summary>
<div style="margin-top:10px;font-size:14px;line-height:2;font-family:inherit;">
  <div><a href="#1-왜-마이크로서비스인가" style="color:#c9d1d9;text-decoration:none;">1. 왜 마이크로서비스인가?</a></div>
  <div><a href="#2-좋은-앱을-만드는-4가지-설계-원칙" style="color:#c9d1d9;text-decoration:none;">2. 좋은 앱을 만드는 4가지 설계 원칙</a></div>
  <div><a href="#3-distributed-primitives--kubernetes의-기본-단위" style="color:#c9d1d9;text-decoration:none;">3. Distributed Primitives — Kubernetes의 기본 단위</a></div>
  <div><a href="#4-container" style="color:#c9d1d9;text-decoration:none;">4. Container</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#좋은-컨테이너-이미지의-8가지-조건" style="color:#6e7681;text-decoration:none;">좋은 컨테이너 이미지의 8가지 조건</a></div>
  </div>
  <div><a href="#5-pod" style="color:#c9d1d9;text-decoration:none;">5. Pod</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#pod의-3가지-핵심-특징" style="color:#6e7681;text-decoration:none;">Pod의 3가지 핵심 특징</a></div>
  </div>
  <div><a href="#6-service" style="color:#c9d1d9;text-decoration:none;">6. Service</a></div>
  <div><a href="#7-label" style="color:#c9d1d9;text-decoration:none;">7. Label</a></div>
  <div><a href="#8-annotation" style="color:#c9d1d9;text-decoration:none;">8. Annotation</a></div>
  <div><a href="#9-namespace" style="color:#c9d1d9;text-decoration:none;">9. Namespace</a></div>
  <div><a href="#10-전체-흐름-정리" style="color:#c9d1d9;text-decoration:none;">10. 전체 흐름 정리</a></div>
</div>
</details>
{{< /rawhtml >}}

---

## 1. 왜 마이크로서비스인가?

마이크로서비스는 큰 앱을 **잘게 쪼개서** 여러 개의 작은 서비스로 만드는 방식입니다.

```
쇼핑몰 (모놀리스)          쇼핑몰 (마이크로서비스)

[하나의 거대한 앱]    →    [로그인 서비스]
                          [결제 서비스]
                          [배송 서비스]
                          [상품 서비스]
```

| | 모놀리스 | 마이크로서비스 |
|--|---------|--------------|
| 개발 | 한 팀이 전부 | 팀별로 독립 개발 |
| 배포 | 전체를 한꺼번에 | 서비스별로 따로 |
| 장애 | 하나 터지면 전체 down | 일부만 영향 |
| 복잡도 | 개발은 단순, 규모가 커지면 복잡 | 개발은 복잡, 운영은 유연 |

> 핵심: 개발 복잡성을 운영 복잡성과 맞바꾸는 것 — 그래서 **Kubernetes가 필수**입니다.

---

## 2. 좋은 앱을 만드는 4가지 설계 원칙

책에서는 Kubernetes 패턴을 배우기 전에 **앱 자체를 잘 만들어야 한다**고 강조합니다.

### Clean Code
변수 이름 하나, 함수 하나하나가 나중에 다 유지보수 비용이 됩니다.  
아무리 좋은 Kubernetes 환경이어도 **코드가 쓰레기면 대규모 쓰레기**가 될 뿐입니다.

### Domain-Driven Design (DDD)
비즈니스 관점에서 소프트웨어를 설계하는 방법론입니다.

```
❌ "기술적으로 어떻게 만들지?"
✅ "실제 쇼핑몰이 어떻게 돌아가지?"  ← 이걸 먼저 생각
```

현실 세계와 가까운 구조로 설계하면 → 나중에 컨테이너화와 자동화가 훨씬 쉬워집니다.

### Hexagonal Architecture
핵심 비즈니스 로직과 외부(DB, UI, 클라우드)를 **분리**하는 설계 방식입니다.

```
        [외부: DB, API, UI]
               ↕
        [인터페이스 (연결 통로)]
               ↕
        [핵심 비즈니스 로직]  ← 이게 중심!
```

외부가 바뀌어도 핵심 로직은 그대로 → AWS → Azure 이전도 외부 연결만 바꾸면 끝!

### 12-Factor App + Microservices 원칙

현대 클라우드 앱의 표준이 된 방법론으로, 세 가지를 목표로 합니다.

| 목표 | 의미 |
|------|------|
| Scale (확장성) | 사용자 늘어도 잘 버팀 |
| Resiliency (회복성) | 일부가 터져도 전체는 안 죽음 |
| Pace of Change (변화 속도) | 빠르게 업데이트 가능 |

---

## 3. Distributed Primitives — Kubernetes의 기본 단위

Java/JVM과 비교하면 Kubernetes를 쉽게 이해할 수 있습니다.

| Java (로컬, 1대) | Kubernetes (분산, 여러 대) |
|----------------|--------------------------|
| Class (설계도) | Container Image |
| Object (실행) | Container |
| JVM | Kubernetes |
| 생성자 `new` | Init Container |
| 데몬 스레드 | DaemonSet |
| Spring IoC | Pod |
| ExecutorService | CronJob |

```
Java = 방 하나에서 일하는 것
Kubernetes = 여러 건물에 걸쳐 팀이 협업하는 것 🏢🏢🏢
```

---

## 4. Container

컨테이너 이미지 = **붕어빵 틀** 🐟  
컨테이너 = **실제 붕어빵** 🐟🐟🐟

틀(이미지) 하나로 붕어빵(컨테이너)을 여러 개 찍어낼 수 있습니다.

### 좋은 컨테이너 이미지의 8가지 조건

| # | 조건 | 의미 |
|---|------|------|
| 1 | Single concern | 딱 한 가지 역할만 |
| 2 | Owned by one team | 담당 팀 하나 + 독립 배포 주기 |
| 3 | Self-contained | 필요한 것을 다 들고 다님 |
| 4 | Immutable | 한번 만들면 수정 ❌, 새 버전 출시 ✅ |
| 5 | Defines resource requirements | CPU/메모리 필요량 미리 명시 |
| 6 | Well-defined APIs | 외부와 소통하는 창구가 명확 |
| 7 | Single Unix process | 컨테이너 하나 = 프로세스 하나 |
| 8 | Disposable | 언제든 만들고 없애도 OK |

> 좋은 컨테이너는 **레고 블록처럼 작고, 환경별로 설정만 바꿔서 재사용** 가능해야 합니다.

---

## 5. Pod

마이크로서비스는 개발할 때는 **컨테이너 이미지**, 실행할 때는 **Pod**입니다.

```
개발/빌드할 때          실행할 때

컨테이너 이미지    →    Pod
(설계도, 틀)           (실제로 살아서 돌아가는 것)
```

Kubernetes에서 컨테이너를 실행하는 **유일한 방법**은 Pod를 통하는 것입니다.

### Pod의 3가지 핵심 특징

**1. 스케줄링의 최소 단위**

Pod 안에 컨테이너가 여러 개라면, 스케줄러는 **모든 컨테이너의 자원을 합산**해서 감당할 수 있는 서버를 찾습니다.

**2. 컨테이너들의 동거 보장 (Colocation)**

같은 Pod 안의 컨테이너끼리 소통하는 방법:

| 방법 | 설명 | 속도 |
|------|------|------|
| 공유 파일시스템 | 같은 폴더를 읽고 씀 | 빠름 ⚡ |
| localhost 네트워크 | 내부망으로 통신 | 빠름 ⚡ |
| IPC | 프로세스간 직접 통신 | 매우 빠름 ⚡⚡ |

**3. IP/포트 공유**

Pod 안의 컨테이너들은 IP 주소와 포트를 공유합니다. 포트가 겹치면 충돌이 납니다.

```
Pod (IP: 10.0.0.1)
├── 컨테이너 A → 포트 8080 ✅
├── 컨테이너 B → 포트 8081 ✅
└── 컨테이너 C → 포트 8080 ❌ 충돌!
```

**사이드카 패턴** — Pod 안에 메인 컨테이너 + 보조 컨테이너를 함께 두는 방식:

```
Pod
├── 메인 앱 컨테이너 🚗
└── 사이드카 컨테이너 🏍️  (로그 수집, 모니터링 등)
```

---

## 6. Service

Pod는 언제든 죽고 다시 생깁니다. 그때마다 IP 주소가 바뀝니다.

```
사용자: "10.0.0.1로 접속해야지!"
Pod가 죽고 새로 생김 → 새 IP: 10.0.0.5
사용자: "어?? 접속이 안되네" 😱
```

Service는 이 문제를 해결하는 **고정 주소 + 대표 창구**입니다.

```
사용자 → Service (주소 고정! 절대 안 바뀜 🔒)
               ↓
          살아있는 Pod로 자동 연결
```

| Service의 역할 | 설명 |
|--------------|------|
| 고정 주소 | IP/포트가 절대 안 바뀜 |
| 서비스 디스커버리 | 살아있는 Pod를 자동으로 찾아줌 |
| 로드 밸런싱 | 여러 Pod에 트래픽을 골고루 분배 |

> Service = **대표전화** 📞 / Pod = **실제 상담원**

---

## 7. Label

마이크로서비스로 쪼개면 Pod가 여러 개가 됩니다.  
이 Pod들이 **같은 앱에 속한다는 걸 표시**하는 방법이 Label입니다.

```
Pod 1 → label: app=쇼핑몰, tier=frontend
Pod 2 → label: app=쇼핑몰, tier=backend
Pod 3 → label: app=쇼핑몰, tier=database

Pod 4 → label: app=결제, tier=api
Pod 5 → label: app=결제, tier=database
```

Label로 Pod 그룹을 관리할 수 있습니다:

```bash
# app=쇼핑몰인 Pod 전부 재시작
kubectl rollout restart deployment -l app=쇼핑몰
```

**Label 사용 시 주의사항**

- 추가는 언제든 쉽게 가능 ✅
- 삭제는 **매우 위험** ⚠️ — ReplicaSet, Service, 모니터링 등 어디서 쓰이는지 파악하기 어려움
- 미리 너무 많이 달지 말고, **필요한 것만** 달기

> Label = 인스타그램 해시태그 🏷️ — 단순 태그가 아니라 **Kubernetes가 실제 Pod를 관리하는 데 핵심적으로 사용**됩니다.

---

## 8. Annotation

Label과 비슷하지만 목적이 다릅니다.

| | Label | Annotation |
|--|-------|------------|
| 목적 | 검색/그룹핑/관리 | 부가정보 저장 |
| 사용자 | 사람 | 기계/자동화 도구 |
| 검색 가능? | ✅ | ❌ |
| 예시 | `app=쇼핑몰` | 빌드ID, Git 브랜치 등 |

Annotation에 저장하는 정보 예시:

```yaml
annotations:
  build-id: "12345"
  git-branch: "main"
  image-hash: "sha256:abc..."
  author: "김철수"
  timestamp: "2026-06-22"
```

> Label = **책의 분류 태그** 🏷️ / Annotation = **책 뒷면의 상세정보** 📖

---

## 9. Namespace

하나의 Kubernetes 클러스터를 **용도별로 나누는 칸막이**입니다.

```
Kubernetes 클러스터 = 하나의 큰 사무실 🏢

dev namespace | testing namespace | production namespace
(개발팀 공간)   (QA팀 공간)         (운영팀 공간)
```

**주요 특징 정리:**

| 특징 | 설명 |
|------|------|
| 이름 충돌 방지 | 같은 이름을 Namespace별로 따로 쓸 수 있음 |
| DNS 주소 구분 | `my-app.production.svc.cluster.local` |
| ResourceQuota | Namespace별로 CPU/메모리 한도 설정 가능 |
| 기본 격리 없음 | ⚠️ 기본적으로 다른 Namespace 접근 가능 (별도 네트워크 정책 필요) |

**실제로 많이 쓰는 구성:**

```
비운영 클러스터 🖥️          운영 클러스터 🖥️
├── dev namespace           ├── performance namespace
├── testing namespace       └── production namespace
└── integration namespace
```

> 완벽한 격리가 필요하면 **클러스터 자체를 분리**해야 합니다.

---

## 10. 전체 흐름 정리

{{< rawhtml >}}
<div style="background:linear-gradient(135deg,#1e3050,#253c60,#1c2d50);border-radius:12px;padding:24px;margin:1.5rem 0;font-family:monospace;font-size:14px;color:#c9d1d9;line-height:2;">
<div style="color:#58a6ff;font-weight:bold;margin-bottom:8px;">[ 개발 → 배포 → 운영 전체 흐름 ]</div>
<div>1. 개발팀이 Clean Code + DDD로 앱 설계</div>
<div>2. 컨테이너 이미지로 패키징 (단일 목적, 불변)</div>
<div>3. Kubernetes에 Pod로 배포</div>
<div>4. Service로 고정 주소 제공</div>
<div>5. Label로 Pod 그룹 관리</div>
<div>6. Namespace로 환경(dev/prod) 분리</div>
<div>7. Annotation으로 자동화 도구에 메타데이터 전달</div>
</div>
{{< /rawhtml >}}

| 개념 | 한마디 요약 | 비유 |
|------|-----------|------|
| Container | 앱을 담는 도시락통 | 붕어빵 틀/붕어빵 🍱 |
| Pod | 컨테이너들의 묶음 | Spring IoC 컨텍스트 |
| Service | Pod의 고정 주소/대표창구 | 대표전화 📞 |
| Label | Pod에 붙이는 태그 | 인스타 해시태그 🏷️ |
| Annotation | 기계가 읽는 메모장 | 책 뒷면 상세정보 📖 |
| Namespace | 클러스터를 나누는 칸막이 | 사무실 부서 칸막이 🚧 |

---

## 마치며

1챕터의 핵심 메시지는 단순합니다.

> **"Kubernetes가 아무리 좋아도, 앱 자체가 잘 만들어져 있지 않으면 소용없다."**

좋은 그릇(Kubernetes)도 중요하지만, 담는 내용물(앱)이 먼저입니다.  
다음 챕터부터는 본격적으로 Kubernetes 패턴들을 하나씩 살펴볼 예정입니다.