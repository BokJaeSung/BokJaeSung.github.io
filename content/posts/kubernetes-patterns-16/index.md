---
series: ["K8sPatterns"]
title: "K8sPatterns.16 Sidecar"
date: 2026-07-29T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "patterns"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.16 Sidecar'
  relative: true
summary: "컨테이너를 건드리지 않고 기능을 확장하는 법 — Sidecar 패턴으로 단일 목적 컨테이너들이 Pod 안에서 협력하는 방식을 이해한다."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-컨테이너란-무엇인가" style="color:var(--secondary,inherit);text-decoration:none;">2.1 컨테이너란 무엇인가</a></div>
    <div><a href="#22-재사용-가능한-컨테이너의-한계" style="color:var(--secondary,inherit);text-decoration:none;">2.2 재사용 가능한 컨테이너의 한계</a></div>
  </div>
  <div><a href="#3-solution--sidecar-패턴" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution — Sidecar 패턴</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-pod와-linux-네임스페이스" style="color:var(--secondary,inherit);text-decoration:none;">3.1 Pod와 Linux 네임스페이스</a></div>
    <div><a href="#32-예제--http-서버--git-동기화기" style="color:var(--secondary,inherit);text-decoration:none;">3.2 예제 — HTTP 서버 + Git 동기화기</a></div>
    <div><a href="#33-두-가지-사이드카-방식" style="color:var(--secondary,inherit);text-decoration:none;">3.3 두 가지 사이드카 방식</a></div>
  </div>
  <div><a href="#4-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-oop-비유--상속-vs-합성" style="color:var(--secondary,inherit);text-decoration:none;">4.1 OOP 비유 — 상속 vs 합성</a></div>
    <div><a href="#42-사이드카-분리-vs-합치기-트레이드오프" style="color:var(--secondary,inherit);text-decoration:none;">4.2 사이드카 분리 vs 합치기 트레이드오프</a></div>
    <div><a href="#43-투명한-사이드카-vs-명시적-사이드카" style="color:var(--secondary,inherit);text-decoration:none;">4.3 투명한 사이드카 vs 명시적 사이드카</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Sidecar Pattern - Core Idea
==================================================

Want to extend the main container without touching it
                    |
                    v
       Add a helper container in the same Pod
       (shared Linux namespaces + shared volume)
                    |
      +-------------+-------------+
      v                           v
  Main Container              Sidecar Container
  (core responsibility)       (auxiliary responsibility)
  no code changes needed      replaceable independently
```

단일 목적 컨테이너는 재사용성이 높다. 하지만 현실에서는 하나의 컨테이너만으로는 부족한 경우가 많다. 기능을 확장하려면 코드를 바꾸거나, 이미지를 새로 빌드하거나, 전혀 다른 컨테이너를 만들어야 할까?

**Sidecar 패턴**은 이 문제에 대한 우아한 답이다. 메인 컨테이너 옆에 보조 컨테이너를 붙여서, 기존 코드를 전혀 건드리지 않고 기능을 확장한다. 오토바이 사이드카처럼, 본체는 그대로이고 옆에 보조 칸을 추가하는 구조다.

---

## 2. Problem

### 2.1 컨테이너란 무엇인가

컨테이너는 애플리케이션과 그 실행에 필요한 모든 것을 하나로 묶은 패키징 단위다.

```
+-----------------------------+
|          Container          |
|  +------------------------+ |
|  |      Application       | |
|  +------------------------+ |
|  |   Libraries / Deps     | |
|  +------------------------+ |
|  |  Runtime env / config  | |
|  +------------------------+ |
+-----------------------------+
```

좋은 컨테이너는 세 가지 원칙을 따른다.

- **단일 목적** — 단일 Linux 프로세스처럼, 하나의 컨테이너는 하나의 역할만 담당
- **교체 가능성** — 언제든지 다른 컨테이너로 대체할 수 있어야 함
- **재사용성** — 이미 만들어진 컨테이너를 조합해 새 애플리케이션을 빠르게 구성

HTTP 호출을 위해 클라이언트 라이브러리를 직접 작성할 필요가 없듯이, 웹 서버 컨테이너도 처음부터 만들 필요가 없다. 기존의 잘 만들어진 컨테이너를 가져다 쓰면 된다. "바퀴를 재발명하지 마라."

### 2.2 재사용 가능한 컨테이너의 한계

단일 목적 컨테이너는 좋다. 하지만 두 가지 문제가 생긴다.

```
기존 방식 (모놀리식 컨테이너)
+------------------------------------+
|  HTTP serving + Git sync + logging |  -> 복잡, 유지보수 어려움
+------------------------------------+

단일 목적 컨테이너만 사용하면?
+-------------+   +----------------+
| HTTP server |   |  Git syncer    |  -> 어떻게 협력시킬 것인가?
+-------------+   +----------------+
```

1. **기능 확장 수단이 없다** — 기존 컨테이너를 수정하지 않고 기능을 추가하는 방법
2. **컨테이너 간 협력 수단이 없다** — 여러 컨테이너가 함께 동작하는 메커니즘

**Sidecar 패턴**이 바로 이 두 문제를 해결한다.

---

## 3. Solution — Sidecar 패턴

### 3.1 Pod와 Linux 네임스페이스

Sidecar 패턴은 Kubernetes의 **Pod** 위에서 동작한다. Pod는 여러 컨테이너를 하나의 논리적 단위로 묶는 기본 단위다.

Pod 안에는 **pause 컨테이너**가 가장 먼저 실행된다. 실제 작업은 하지 않지만, 다른 컨테이너들이 공유할 **Linux 네임스페이스를 먼저 확보**해두는 역할을 한다.

```
+---------------------------------------+
|                  Pod                   |
|   +-----------+                        |
|   |   pause   |  <- starts first       |
|   | container |     creates & holds    |
|   |           |     Linux namespaces    |
|   +-----------+                        |
|                                        |
|   +-----------+    +-----------+       |
|   |   Main    |    |  Sidecar  |       |
|   | Container |    | Container |       |
|   +-----------+    +-----------+       |
|         ^                ^             |
|         +----------------+             |
|          shared Linux namespaces       |
+---------------------------------------+
```

> **Linux 네임스페이스 ≠ Kubernetes 네임스페이스**
> Kubernetes 네임스페이스는 `dev`, `staging` 같은 클러스터 수준의 논리적 그룹이다.
> Linux 네임스페이스는 컨테이너 격리/공유의 OS 기술적 구현체다.

Pod 안의 컨테이너들이 공유하는 것들이다.

| 공유 항목 | 의미 |
|---|---|
| **IP 주소** | Pod 안 모든 컨테이너가 같은 IP |
| **포트 공간** | 같은 포트 번호를 두 컨테이너가 동시에 쓸 수 없음 |
| **localhost** | 서로 localhost로 바로 통신 가능 |
| **볼륨** | 같은 파일을 읽고 쓸 수 있음 |

반면 파일시스템, 프로세스, CPU/메모리는 각 컨테이너가 독립적으로 갖는다.

Pod가 컨테이너에 부여하는 런타임 제약도 있다.

```
✅ 같은 노드에 배포  →  네트워크 지연 없이 초고속 통신
✅ 같은 생명주기    →  메인이 죽으면 사이드카도 함께 종료 (운명 공동체)
✅ 볼륨 공유        →  파일 기반 데이터 교환 가능
✅ 로컬 네트워크    →  localhost로 직접 통신
```

### 3.2 예제 — HTTP 서버 + Git 동기화기

Sidecar 패턴의 전형적인 예시다.

```
+---------------------------------------------+
|                    Pod                      |
|   +------------------+  +-----------------+ |
|   |   app (main)     |  | poll (sidecar)  | |
|   |  centos/httpd    |  |  bitnami/git    | |
|   |                  |  |                 | |
|   |  serves files    |  |  git pull       | |
|   |  over HTTP to    |  |  every 60s to   | |
|   |  clients         |  |  sync files     | |
|   +--------+---------+  +--------+--------+ |
|            |                     |          |
|            +----------+----------+          |
|              shared volume "git"             |
|                 (emptyDir)                   |
+---------------------------------------------+
```

각 컨테이너의 단일 책임이 명확하다.

| 컨테이너 | 역할 | 모르는 것 |
|---|---|---|
| **app (HTTP 서버)** | 파일을 HTTP로 제공 | 파일이 어디서 오는지 |
| **poll (Git 동기화기)** | Git → 로컬 동기화 | 파일이 어떻게 사용되는지 |

실제 Pod 정의다.

```yaml
# Example 16-1. Pod with a sidecar
apiVersion: v1
kind: Pod
metadata:
  name: web-app                       # Pod 이름
spec:
  containers:
  - name: app                         # ① 메인 컨테이너 — HTTP 서빙만 담당
    image: centos/httpd                #    이미 만들어진 httpd 이미지 그대로 사용
    volumeMounts:
    - mountPath: /var/www/html         # httpd가 기본으로 서빙하는 경로에
      name: git                        # 공유 볼륨 "git"을 마운트

  - name: poll                        # ② 사이드카 컨테이너 — Git 동기화만 담당
    image: bitnami/git                 #    Git 클라이언트가 설치된 이미지
    volumeMounts:
    - mountPath: /var/lib/data         # git 작업 디렉토리에도
      name: git                        # 같은 볼륨 "git"을 마운트 (경로만 다름)
    env:
    - name: GIT_REPO                   # ③ 동기화할 원격 저장소 주소
      value: https://github.com/mdn/beginner-html-site-scripted
    command: [ "sh", "-c" ]            # ④ 컨테이너 시작 시 실행할 셸
    args:
    - |
      git clone $(GIT_REPO) .          # 최초 1회: 저장소 전체를 clone
      while true; do                   # 이후: 무한 루프로 계속 동기화
        sleep 60                       # 60초 대기 (폴링 주기)
        git pull                       # 원격 변경사항을 로컬에 반영
      done
    workingDir: /var/lib/data          # ⑤ 위 명령어가 실행될 기준 디렉토리
                                        #    (git clone/pull이 이 경로에서 수행됨)

  volumes:
  - name: git                         # ⑥ app과 poll이 공유하는 볼륨 이름
    emptyDir: {}                       #    Pod 생성 시 자동 생성되는 빈 디스크
                                        #    Pod가 삭제되면 내용도 함께 사라짐
```

마운트 경로가 다른 이유가 있다.

```
poll 컨테이너          app 컨테이너
/var/lib/data    =    /var/www/html
(git 작업 경로)        (httpd 기본 경로)

같은 볼륨 "git"이지만,
각 컨테이너의 표준 경로에 맞게 마운트
→ 서로 코드 수정 없이 자기 표준 경로 그대로 사용 가능
```

전체 데이터 흐름이다.

```
[GitHub 원격 저장소]
        ↓  git clone / 60초마다 git pull
[emptyDir 볼륨 "git"]
        ↓  httpd가 파일 읽어서 서빙
[웹 브라우저 클라이언트]  ←  HTTP 응답
```

두 컨테이너는 서로를 전혀 모르지만, 공유 볼륨이라는 약속된 접점을 통해 협력한다. **느슨한 결합(Loose Coupling), 강한 협력(Strong Collaboration).**

### 3.3 두 가지 사이드카 방식

사이드카는 메인 컨테이너가 그 존재를 아느냐 모르느냐에 따라 두 가지로 나뉜다.

```
Transparent Sidecar (Envoy)              Explicit Sidecar (Dapr)
------------------------------           ------------------------------
external traffic                         [Main Container]
    |                                          | direct HTTP/gRPC API call
    v                                          v
[Sidecar] <- intercepts traffic          [Sidecar]
 automatically                                |
    |                                          v
    v                                     external system
[Main Container] <- "looks like it
 came straight to me"
```

**투명한 사이드카 — Envoy**

Envoy 프록시가 대표적인 예다. 메인 컨테이너의 모든 수신·발신 트래픽을 자동으로 가로채서 다양한 네트워크 기능을 제공한다. 메인 컨테이너는 Envoy가 있는지조차 모른다.

| Envoy가 제공하는 기능 | 설명 |
|---|---|
| **TLS** | 암호화 통신 자동 처리 |
| **로드 밸런싱** | 트래픽 자동 분산 |
| **자동 재시도** | 실패 시 자동으로 재요청 |
| **서킷 브레이킹** | 장애 전파 차단 |
| **분산 추적** | 요청 흐름 추적/모니터링 |

이는 **AOP(관점 지향 프로그래밍)**과 유사하다. 메인 컨테이너를 건드리지 않고 직교적 기능을 Pod에 도입한다. 이것이 **서비스 메시(Service Mesh)**의 핵심 원리이며, Istio와 Linkerd 같은 현대 클라우드 네이티브 인프라의 기반이다.

**명시적 사이드카 — Dapr**

Dapr는 메인 컨테이너가 API를 직접 호출해서 기능을 사용하는 명시적 방식이다. 트래픽을 자동으로 가로채지 않는다.

```python
# 메인 컨테이너 코드에서 Dapr API를 직접 호출
POST http://localhost:3500/v1.0/publish/topic   # 메시지 발행
GET  http://localhost:3500/v1.0/invoke/serviceB # 서비스 호출
POST http://localhost:3500/v1.0/state/store     # 상태 저장
```

두 방식의 핵심 차이다.

| | Envoy (투명) | Dapr (명시적) |
|---|---|---|
| **앱이 사이드카 인식** | ❌ 모름 | ✅ 알고 사용 |
| **트래픽 가로챔** | ✅ 자동 | ❌ 안함 |
| **앱 코드 수정** | ❌ 불필요 | ✅ API 호출 필요 |
| **주요 역할** | 네트워크 처리 | 분산 앱 기능 제공 |

---

## 4. Discussion

### 4.1 OOP 비유 — 상속 vs 합성

컨테이너 이미지는 클래스, 컨테이너는 객체와 같다. 이 비유를 확장하면 두 가지 확장 방식이 나온다.

**상속 방식 — Dockerfile FROM**

```dockerfile
FROM centos/httpd      # 부모 이미지를 상속
RUN yum install -y git # Git 기능을 추가
```

```
관계: 새 컨테이너 "is-a" HTTP 서버
문제: 강한 결합 (tightly coupled)
      → 부모 이미지가 바뀌면 자식도 영향받음
      → 하나의 컨테이너가 두 가지 책임을 가짐
```

**합성 방식 — Sidecar 패턴**

```
Pod "has-a" HTTP 서버 + Git 동기화기

문제 없음: 느슨한 결합 (loosely coupled)
           → 각자 독립적으로 교체/업데이트 가능
           → 단일 책임 원칙 유지
```

OOP에서도 "상속보다 합성을 선호하라"는 원칙이 있듯이, 컨테이너 세계에서도 Sidecar 패턴(합성)이 Dockerfile 상속보다 더 유연하고 유지보수하기 좋은 방식이다.

**빌드 시점 결합 vs 런타임 결합**

```
상속 (빌드 시점 결합):
  변경하려면 이미지를 다시 빌드해야 함 ❌

합성 (런타임 결합):
  Pod YAML만 수정하면 바로 교체 가능 ✅
```

### 4.2 사이드카 분리 vs 합치기 트레이드오프

합성 방식에서는 메인 컨테이너와 사이드카가 **각각 독립적인 프로세스**로 동작한다. 즉 각각 실행, 헬스 체크, 재시작, 리소스 소비가 발생한다.

현대의 사이드카는 작고 최소한의 리소스를 소비하지만, 상황에 따라 분리할지 합칠지 판단이 필요하다.

| 항목 | 사이드카 분리 | 메인에 합치기 |
|---|---|---|
| **유연성** | ✅ 높음 | ❌ 낮음 |
| **재사용성** | ✅ 높음 | ❌ 낮음 |
| **리소스** | ❌ 2배 소비 | ✅ 단일 소비 |
| **복잡도** | ❌ 관리 포인트 증가 | ✅ 단순함 |
| **단일 책임** | ✅ 유지 | ❌ 위반 |

| 사이드카로 분리 ✅ | 메인에 합치기 ✅ |
|---|---|
| 재사용 가능한 기능 | 재사용 불필요 |
| 다른 팀이 관리 | 같은 팀이 관리 |
| 독립적 릴리스 필요 | 함께 배포 |
| 리소스 여유 있음 | 리소스 매우 제한적 |

### 4.3 투명한 사이드카 vs 명시적 사이드카

마지막으로 두 사이드카 방식을 실생활 비유로 정리한다.

| 투명한 사이드카 (Envoy) | 명시적 사이드카 (Dapr) |
|---|---|
| 공항 보안검색대 | 비서 |
| 내가 신경 안써도 자동으로 검사해줌 | 내가 직접 "이거 해줘"라고 요청해야 함 |
| 존재를 몰라도 됨 | 존재를 알고 써야 함 |

> Sidecar 패턴의 핵심은 **"메인 컨테이너를 건드리지 않는 것"** 이다.
> 투명하든 명시적이든, 메인 컨테이너는 자신의 역할에만 집중하고,
> 나머지는 사이드카가 알아서 보완한다.
> 이것이 클라우드 네이티브에서 단일 목적 컨테이너 생태계를 건강하게 유지하는 방법이다.