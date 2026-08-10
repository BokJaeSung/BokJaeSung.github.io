---
series: ["K8sPatterns"]
title: "K8sPatterns.18 Ambassador"
date: 2026-08-10T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "patterns"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.18 Ambassador'
  relative: true
summary: "외부 세계의 복잡함을 내 앱에서 걷어내는 법 — Ambassador 패턴으로 메인 컨테이너가 localhost만 바라보며 비즈니스 로직에 집중하는 방식을 이해한다."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-외부-접근이-어려운-네-가지-이유" style="color:var(--secondary,inherit);text-decoration:none;">2.1 외부 접근이 어려운 네 가지 이유</a></div>
    <div><a href="#22-책임이-두-개가-되는-순간" style="color:var(--secondary,inherit);text-decoration:none;">2.2 책임이 두 개가 되는 순간</a></div>
  </div>
  <div><a href="#3-solution--ambassador-패턴" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution — Ambassador 패턴</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-동작-구조" style="color:var(--secondary,inherit);text-decoration:none;">3.1 동작 구조</a></div>
    <div><a href="#32-대표-시나리오-세-가지" style="color:var(--secondary,inherit);text-decoration:none;">3.2 대표 시나리오 세 가지</a></div>
    <div><a href="#33-환경별-교체--etcd에서-memcached로" style="color:var(--secondary,inherit);text-decoration:none;">3.3 환경별 교체 — etcd에서 memcached로</a></div>
    <div><a href="#34-example-18-1-yaml-분석" style="color:var(--secondary,inherit);text-decoration:none;">3.4 Example 18-1 YAML 분석</a></div>
    <div><a href="#35-앰배서더의-실체--log_ambassadorjs" style="color:var(--secondary,inherit);text-decoration:none;">3.5 앰배서더의 실체 — log_ambassador.js</a></div>
  </div>
  <div><a href="#4-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-사이드카와-무엇이-다른가" style="color:var(--secondary,inherit);text-decoration:none;">4.1 사이드카와 무엇이 다른가</a></div>
    <div><a href="#42-레거시-앱의-무수술-현대화" style="color:var(--secondary,inherit);text-decoration:none;">4.2 레거시 앱의 무수술 현대화</a></div>
    <div><a href="#43-sidecar-패턴-3형제-완결" style="color:var(--secondary,inherit);text-decoration:none;">4.3 Sidecar 패턴 3형제 완결</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Ambassador Pattern - Core Idea
==================================================

Main app must consume external services
(changing addresses, sharding, retries, formats...)
                    |
                    v
     Add an Ambassador sidecar container in the same Pod
     (listens on localhost → handles the outside world)
                    |
      +-------------+-------------+
      v                           v
  Main Container              Ambassador Container
  (business logic only)       (smart proxy to outside)
  talks to localhost          replaceable per environment
                    |
                    v
   App sees ONE simple local endpoint, always
```

컨테이너화된 서비스는 혼자 살지 않는다. 데이터베이스, 캐시, 외부 API — 바깥의 다른 서비스에 연락해야 일을 할 수 있다. 문제는 이 "바깥에 연락하는 일"이 생각보다 복잡하다는 것이다.

**Ambassador 패턴**은 이 복잡함을 메인 앱에서 걷어낸다. 같은 Pod 안에 외부 통신을 전담하는 앰배서더 컨테이너를 붙이고, 메인 앱은 **localhost로만 통신**한다. 외국에 파견된 대사(Ambassador)가 현지의 복잡한 사정을 본국 대신 처리하듯 — 앱은 대사에게 말만 하면 되고, 바깥세상과의 협상은 대사가 전담한다.

앞 장의 Adapter가 **외부 → 내부**로 들어오는 요청을 표준화했다면, Ambassador는 정확히 반대 방향인 **내부 → 외부**로 나가는 요청을 추상화한다.

---

## 2. Problem

### 2.1 외부 접근이 어려운 네 가지 이유

외부 서비스에 안정적으로 접근하기 어려운 이유는 크게 네 가지다.

```
① 동적으로 변하는 주소
   어제: cache → 10.0.0.5
   오늘: cache → 10.0.0.17   (서버 재시작, 스케일링...)

② 로드 밸런싱 필요
   DB 서버가 3대인데, 요청을 누가 어떻게 분산하나?

③ 불안정한 프로토콜
   HTTP는 실패한다. 재시도/타임아웃/차단 로직은 누가 짜나?

④ 어려운 데이터 형식
   레거시 시스템의 특이한 포맷, 변환은 누가 하나?
```

클라우드 환경에서 이 네 가지는 예외 상황이 아니라 **일상**이다. 서버는 죽었다 살아나며 IP가 바뀌고, 서비스는 여러 인스턴스로 흩어져 있으며, 네트워크는 언제든 실패한다.

### 2.2 책임이 두 개가 되는 순간

이상적인 컨테이너는 **단일 목적(single-purposed)** 이어야 하고, 다양한 맥락에서 **재사용 가능**해야 한다. 그런데 위의 네 가지 문제를 메인 앱이 직접 처리하면 어떻게 될까.

```
주문 처리 앱의 코드:
  ✅ 주문 처리 로직            ← 원래 하려던 일
  ❌ 서비스 디스커버리 라이브러리  ← 어? 이건 왜
  ❌ 샤드 라우팅 계산           ← 이것도...
  ❌ 재시도 / 서킷브레이커       ← 이것도...
  ❌ 데이터 형식 변환           ← 이것도...
```

"주문 처리 앱"이 "주문 처리 + 네트워크 잡일 앱"이 된다. 책임이 두 개 이상이 되는 순간 두 가지를 잃는다.

**재사용성 상실** — Consul 클라이언트가 내장된 앱은 Consul 없는 환경에서 못 쓴다. 다른 프로젝트에서 이 앱을 가져다 쓰려면 쓸모없는 짐까지 함께 짊어져야 한다.

**변경 비용 폭증** — 디스커버리 방식이 바뀌면, 비즈니스 로직은 그대로인데도 앱 전체를 수정하고 재빌드해야 한다.

외부 접근용 라이브러리를 앱 컨테이너에 넣고 싶지 않다는 것, 그리고 환경에 따라 접근 방식을 **갈아끼우고** 싶다는 것 — 이 두 요구를 동시에 만족시키는 것이 Ambassador 패턴의 목표다.

---

## 3. Solution — Ambassador 패턴

### 3.1 동작 구조

같은 Pod 안의 컨테이너들은 **네트워크 네임스페이스를 공유**한다. 이것이 패턴의 기술적 기반이다. 한집에 사는 룸메이트끼리 방문만 두드리면 되듯, 같은 Pod 안에서는 `localhost`로 서로 통신할 수 있다.

```
+---------------------------------------------------------+
|                          Pod                            |
|   +------------------+        +---------------------+   |
|   |    Main App      |        |     Ambassador      |   |
|   | (business logic) |        | (etcd client, etc.) |   |
|   |                  |        |                     |   |
|   |  send request to |  --->  |  listen :9009       |   |
|   |  localhost:9009  |        |  handle complexity  |   |
|   +------------------+        +----------+----------+   |
|                                          |              |
+------------------------------------------|--------------+
                                           |
                                  distributed access
                                           |
                                +----------v----------+
                                |  etcd  etcd  etcd   |
                                |  (remote cluster)   |
                                +---------------------+
```

메인 앱은 그냥 `localhost:9009`에 던지고, 주소 추적·샤딩·재시도 같은 복잡한 일은 전부 앰배서더가 맡는다. 각 컨테이너의 단일 책임이 명확하다.

| 컨테이너 | 역할 | 모르는 것 |
|---|---|---|
| **Main App** | 비즈니스 로직 수행, localhost로 요청 | 외부 서비스의 주소, 개수, 프로토콜 |
| **Ambassador** | 외부 서비스와의 실제 통신 전담 | 메인 앱의 비즈니스 로직 |

메인 앱 입장에서는 바로 옆에 서비스 하나가 있는 것처럼 보이지만, 실제로는 앰배서더가 뒤에서 멀리 있는 분산 클러스터와 통신하고 있다. **복잡함이 사라진 게 아니라, 위치가 옮겨진 것**이다.

### 3.2 대표 시나리오 세 가지

책이 제시하는 세 가지 활용 사례를 보면 이 패턴이 커버하는 범위가 보인다.

**① 캐시 샤딩** — 개발 환경에서는 캐시 1개면 되지만, 운영 환경에서는 데이터가 여러 샤드에 쪼개져 있다. `"user123"은 어느 샤드에?`를 계산하는 라우팅 로직을 앰배서더가 전담한다.

```
개발:  [App] → [캐시 1개]              간단
운영:  [App] → 샤드1? 샤드2? 샤드3?     복잡 → Ambassador 담당
```

**② 클라이언트 사이드 서비스 디스커버리** — 레지스트리(주소록 서버)에 "결제 서비스 지금 어디 있어?"를 물어보고 찾아가는 방식. 이 조회 코드를 앱에 넣는 대신 앰배서더가 대신 조회한다.

**③ 회복탄력성(Resiliency)** — HTTP 같은 신뢰할 수 없는 프로토콜을 쓸 때 필요한 보호 장치들을 앰배서더에 몰아넣는다.

| 장치 | 역할 |
|---|---|
| **Timeout** | "N초 기다려도 응답 없으면 끊는다" |
| **Retry** | "실패하면 N번까지 다시 시도한다" |
| **Circuit Breaker** | "계속 실패하면 당분간 아예 요청을 차단한다" — 죽은 서비스에 요청을 퍼붓다 내 앱까지 함께 죽는 연쇄 장애를 막는 두꺼비집 |

### 3.3 환경별 교체 — etcd에서 memcached로

이 패턴의 진가는 **교체**에서 드러난다. 운영 환경에서는 원격 분산 저장소(etcd), 개발 환경에서는 로컬 인메모리 캐시(memcached) — 앰배서더만 갈아끼우면 된다.

```
운영 환경 (Figure 18-1):
  [App] --localhost--> [etcd client Ambassador] --> etcd 클러스터 (원격/분산)

개발 환경 (Figure 18-2):
  [App] --localhost--> [memcached Ambassador]      (로컬에서 끝)

  ↑ App은 두 경우 모두 완전히 동일. 한 글자도 안 바뀐다.
```

게임기 본체는 그대로 두고 카트리지만 바꿔 끼우는 구조다. 개발할 땐 무거운 etcd 클러스터 없이 가볍게 테스트하고, 배포할 땐 앰배서더 이미지만 교체한다.

### 3.4 Example 18-1 YAML 분석

책의 예제는 로깅 앰배서더다. REST 서비스가 응답을 반환하기 전, 생성된 데이터를 고정 URL `http://localhost:9009`로 던지고, 앰배서더가 이 포트에서 받아 처리한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
  labels:
    app: random-generator
spec:
  containers:
  # ① 메인 앱 컨테이너 — 랜덤 숫자 REST 서비스, 8080 포트
  - image: k8spatterns/random-generator:1.0
    name: main
    env:
    - name: LOG_URL
      value: http://localhost:9009   # 로그 목적지를 환경변수로 주입
    ports:
    - containerPort: 8080            # 외부 공개 포트
      protocol: TCP

  # ② 앰배서더 컨테이너 — 9009에서 대기, 로그 처리 전담
  - image: k8spatterns/random-generator-log-ambassador
    name: ambassador                 # 포트 선언 없음 = Pod 내부 전용
```

설계 포인트가 세 가지 있다.

**환경변수로 목적지 주입** — 앱 코드에 주소가 하드코딩되어 있지 않다. `LOG_URL`만 바꾸면 목적지를 바꿀 수 있고, 앱은 "환경변수의 URL로 던진다"는 것만 안다.

**9009 포트는 밖에 안 보인다** — 메인 컨테이너의 8080은 `containerPort`로 명시했지만, 앰배서더는 포트 선언 자체가 없다. 9009는 Pod 내부에서만 접근 가능한 **비공개 창구**다. 바깥에서는 로그 처리 경로가 존재하는지조차 알 수 없다.

```
외부 사용자  →  :8080  ✅ (열림)   →  main
외부 사용자  →  :9009  ❌ (차단)
main       →  localhost:9009 ✅   →  ambassador  (Pod 내부 전용)
```

**교체는 YAML 한 줄** — 콘솔 출력 대신 Elasticsearch로 보내고 싶다면, 앰배서더의 `image:` 한 줄만 바꾼다. 메인 앱은 코드도, 이미지도, 재빌드도 필요 없다. REST 서비스 입장에서는 로그 데이터가 그 뒤에 어떻게 되든 알 바 아니기 때문이다.

### 3.5 앰배서더의 실체 — log_ambassador.js

YAML의 `image:` 한 줄 뒤에는 당연히 실제 프로그램이 있다. [공식 예제 저장소](https://github.com/k8spatterns/examples/tree/main/structural/Ambassador)의 `image/` 디렉토리에 앰배서더의 소스가 그대로 공개되어 있다.

```
structural/Ambassador/
├── pod.yml                 ← Example 18-1
└── image/
    ├── Dockerfile          ← 이미지 빌드 레시피
    └── log_ambassador.js   ← 앰배서더 본체 (Node.js)
```

본체는 놀랍도록 단순한 Node.js HTTP 서버다.

```javascript
// log_ambassador.js — 핵심만 발췌
server = http.createServer(function (req, res) {
  if (req.method == 'POST') {
    // ① 메인 앱이 POST로 던진 로그 데이터를 수신
    req.on('end', function () {
      var resp = JSON.parse(body);
      // ② 콘솔에 출력 — 실전에서는 이 부분만
      //    로깅 인프라 전송 코드로 바꾸면 된다
      console.log(">>> ID: " + resp.id +
                  " -- Duration: " + resp.duration +
                  " -- Random: " + resp.random);
    });
  }
  res.writeHead(200);
  res.end();
});

// ③ YAML의 LOG_URL과 정확히 맞물리는 지점
server.listen(9009, "localhost");
```

```dockerfile
# Dockerfile — 4줄로 포장 완료
FROM node
EXPOSE 9009
COPY log_ambassador.js /opt
CMD node /opt/log_ambassador.js
```

전체 흐름을 잇는다면: **JS 코드 작성 → Dockerfile로 이미지 빌드 → 레지스트리 업로드 → YAML이 이미지를 지정 → Pod 안에서 실행**. YAML에 앰배서더가 딱 두 줄이었던 이유는, 복잡한 작업이 이미 이미지로 포장돼 있고 YAML은 그 완성품을 가리키기만 하면 되기 때문이다.

실행 후 `kubectl logs -f random-generator -c ambassador`로 앰배서더가 실제로 데이터를 받는 모습을 확인할 수 있다.

---

## 4. Discussion

### 4.1 사이드카와 무엇이 다른가

Ambassador는 Sidecar 패턴의 특수화다. 결정적인 차이는 **기능을 더해주지 않는다**는 점이다.

```
일반 Sidecar:
  [Sidecar] → [App]     앱에 새 능력을 추가 (파일 동기화, TLS...)
  "나를 업그레이드해주는 코치"

Ambassador:
  [App] → [Ambassador] → 외부     외부 통신을 대신함
  "나 대신 바깥에 심부름 다녀오는 비서"
```

앰배서더는 앱을 더 강하게 만들지 않는다. 앱이 원래 하려던 "바깥에 연락하기"를 더 똑똑하게 **중계**할 뿐이다. 그래서 책은 이것을 **smart proxy**라 부르고, Proxy 패턴이라는 별칭으로도 불린다.

### 4.2 레거시 앱의 무수술 현대화

이 패턴이 특히 빛나는 곳은 레거시다. 코드를 짠 사람은 퇴사했고, 빌드하는 법은 아무도 모르고, 건드리면 터질 것 같은 10년 된 앱 — 코드를 한 줄도 안 고치고 옆에 앰배서더만 붙이면:

```
[레거시 앱] --> [Ambassador] --> 외부
 (그대로 둠)       │
                  ├─ 요청 계측         (모니터링)
                  ├─ 통신 기록         (로깅)
                  ├─ 새 서버로 안내     (라우팅)
                  └─ 재시도/차단        (회복탄력성)
```

현대적 네트워킹 기능이 **무수술로** 이식된다. 서비스 메시(Istio 등)의 사이드카 프록시가 정확히 이 원리로 동작한다.

### 4.3 Sidecar 패턴 3형제 완결

17장에서 예고한 3형제 구도가 이 장으로 완성된다. Adapter와 Ambassador는 정확히 거울상이다.

```
Sidecar 패턴 (범용 — Chapter 16)
│
├── Adapter 패턴 (Chapter 17)
│   방향: 외부 → 내부 (Reverse Proxy)
│   목적: 이질적인 내부를 표준 인터페이스로 노출
│   예시: Prometheus exporter, 로그 정규화기
│
└── Ambassador 패턴 (Chapter 18)  ← 이번 장
    방향: 내부 → 외부 (Forward Proxy)
    목적: 외부 서비스 연결을 내부에서 추상화
    예시: DB/캐시 프록시, 서비스 디스커버리, 서킷브레이커
```

| 구분 | Sidecar | Adapter | Ambassador |
|---|---|---|---|
| **역할** | 보조 기능 일반 | 형식 변환 특화 | 외부 연결 특화 |
| **방향** | 내부 지원 | 외부→내부 (Reverse) | 내부→외부 (Forward) |
| **누구를 위해 숨기나** | — | 외부 시스템을 위해 내부를 숨김 | 내부 앱을 위해 외부를 숨김 |
| **예시** | 로그 수집, 모니터링 | Prometheus 변환 | DB 연결, 캐시 샤딩, 재시도 |

이점도 대칭적이다. 앱은 비즈니스 로직에 집중하며 단일 목적을 유지하고, 재사용의 혜택은 **양방향**으로 발생한다 — 잘 만든 Redis 앰배서더 하나를 주문 앱, 결제 앱, 리뷰 앱 어디에나 조합할 수 있다. 앱 블록과 앰배서더 블록을 각각 한 번만 만들면 조합은 공짜다.

> Ambassador 패턴의 핵심은 **"메인 앱이 바깥세상을 전혀 몰라도 된다는 것"** 이다.
> 앱은 localhost의 고정 주소로 말만 하고,
> 주소 추적, 분산, 재시도, 변환 — 바깥과의 모든 협상은 대사가 전담한다.
> Adapter가 안을 숨겨 밖을 편하게 했다면, Ambassador는 밖을 숨겨 안을 편하게 한다.
