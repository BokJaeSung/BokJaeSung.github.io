---
series: ["K8sPatterns"]
title: "K8sPatterns.18.5 Sidecarless & eBPF"
date: 2026-08-10T21:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "patterns", "service-mesh", "ebpf", "cni"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.18.5 Sidecarless & eBPF'
  relative: true
summary: "Ambassador 패턴은 왜 요즘 잘 안 쓰일까 — 사이드카의 한계에서 출발해 Sidecarless 메시, CNI의 실체, eBPF까지. 하는 일은 그대로인데 프록시의 근무지만 이사 중이라는 이야기."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-사이드카-방식의-한계" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. 사이드카 방식의 한계</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-라이프사이클-불일치" style="color:var(--secondary,inherit);text-decoration:none;">2.1 라이프사이클 불일치</a></div>
    <div><a href="#22-n배의-비용" style="color:var(--secondary,inherit);text-decoration:none;">2.2 N배의 비용</a></div>
  </div>
  <div><a href="#3-세대-진화--프록시의-이사-기록" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. 세대 진화 — 프록시의 이사 기록</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-3단계-진화-지도" style="color:var(--secondary,inherit);text-decoration:none;">3.1 3단계 진화 지도</a></div>
    <div><a href="#32-3세대--개인-비서에서-층-안내데스크로" style="color:var(--secondary,inherit);text-decoration:none;">3.2 3세대 — 개인 비서에서 층 안내데스크로</a></div>
  </div>
  <div><a href="#4-cni의-실체" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. CNI의 실체</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-프로토콜이-아니라-규격이다" style="color:var(--secondary,inherit);text-decoration:none;">4.1 프로토콜이 아니라 규격이다</a></div>
    <div><a href="#42-pod가-생길-때-실제로-벌어지는-일" style="color:var(--secondary,inherit);text-decoration:none;">4.2 Pod가 생길 때 실제로 벌어지는 일</a></div>
    <div><a href="#43-cni-레이어라는-관용어" style="color:var(--secondary,inherit);text-decoration:none;">4.3 "CNI 레이어"라는 관용어</a></div>
  </div>
  <div><a href="#5-ebpf--커널-아래로" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. eBPF — 커널 아래로</a></div>
  <div><a href="#6-정리--패턴은-죽지-않았다" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. 정리 — 패턴은 죽지 않았다</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
The Question
==================================================

"앱 대신 바깥일(주소 찾기, 재시도, 분산...)을
 누가, 어디서 해줄 것인가?"

1세대: 앱이 직접          (라이브러리 내장)
2세대: Pod 안 전담 컨테이너 (Ambassador — Ch.18)
3세대: 노드당 프록시 1개    (Sidecarless Mesh)
다음:   커널 속으로         (eBPF)

일은 그대로, 근무지만 이사 중
```

18장에서 Ambassador 패턴을 정리했는데, 실무에서는 "요즘 이 패턴 잘 안 쓴다"는 말을 자주 듣는다. 컨테이너끼리 라이프사이클이 안 맞고, 이제는 메시 + CNI 조합으로 넘어갔고, 다음 단계는 커널 아래까지 내려간다는 것이다.

이 포스트에서는 그 말이 정확히 무슨 뜻인지 하나씩 짚어본다. 미리 결론부터 적으면 — 안 쓰이게 된 건 **Pod 안에 사이드카 컨테이너를 두는 구현 방식**이지 패턴의 아이디어가 아니다. "앱은 비즈니스 로직만, 네트워크 잡일은 대리인이"라는 방향은 오히려 더 극단적으로 실현되는 중이다.

---

## 2. 사이드카 방식의 한계

### 2.1 라이프사이클 불일치

같은 Pod에 있다는 게 장점만은 아니다. 두 컨테이너는 한집에 살지만 **서로의 생사를 조율할 방법이 없다.**

```
① 시작 순서 문제
   Pod 시작 → 메인 앱이 먼저 떴는데 앰배서더가 아직 안 뜸
   → 앱: "localhost:9009로 던질게!" → Connection refused 💥

② 종료 순서 문제
   Pod 종료 → 앰배서더가 먼저 죽음
   → 앱의 마지막 로그를 받아줄 사람이 없음 → 유실 💥

③ Job에서의 악명 높은 문제
   배치 Job: 메인 컨테이너는 일 끝내고 종료
   사이드카는 "나는 서버니까" 계속 생존
   → Job이 영원히 Completed 안 됨 🧟
```

Kubernetes는 오랫동안 "A가 준비된 후 B를 시작하라"를 보장하지 않았다. 1.28에서 **네이티브 사이드카**(`initContainers` + `restartPolicy: Always`)가 도입되어 순서 문제는 어느 정도 완화됐지만, 구조 자체에서 오는 다음 문제는 남는다.

### 2.2 N배의 비용

```
Pod 1,000개 = 프록시 1,000개

- 메모리/CPU: 프록시 오버헤드 × 1,000
- 업그레이드: 프록시 버전 하나 올리려면
              1,000개 Pod 전체 재시작
- 운영 부담: 장애 지점도 1,000개
```

Istio 클래식(사이드카 모드)이 이 비용을 치른 대표 사례다. Pod마다 Envoy를 자동 주입하는 방식은 Ambassador 패턴의 대규모 자동화 버전이었고, 패턴의 장점과 함께 단점도 N배로 물려받았다.

---

## 3. 세대 진화 — 프록시의 이사 기록

### 3.1 3단계 진화 지도

```
1세대: 앱 안에 라이브러리 내장
   [앱 + Consul클라이언트 + 재시도로직]
   → 책 18장 도입부의 "문제 상황" 그 자체

2세대: Ambassador / Sidecar          ← Ch.18 (책 출간 시점의 답)
   [앱] + [앰배서더]   Pod마다 한 쌍
   → Istio 클래식 = 이 패턴의 자동화

3세대: Sidecarless 메시 + CNI         ← 현재
   프록시를 Pod에서 꺼내 노드 레벨로
   - Istio Ambient Mesh: 노드당 ztunnel 1개
   - Cilium: CNI 계층에 메시 기능 통합

다음: eBPF                            ← 방향
   처리 로직 자체가 커널 속으로
```

### 3.2 3세대 — 개인 비서에서 층 안내데스크로

2세대와 3세대의 차이는 비유로 보면 이해가 쉽다.

**2세대 = 직원마다 개인 비서 1명.** 직원(Pod) 1,000명이면 비서(프록시)도 1,000명. 월급(리소스)이 2배이고, 직원과 비서의 출퇴근이 안 맞으면 일이 멈추고(라이프사이클), 비서 재교육(업그레이드)은 전사적 행사다.

**3세대 = 층마다 안내데스크 1개.** 층(노드) 단위로 데스크(프록시)를 통합한다. 직원이 몇 명이든 데스크는 층 수만큼만 있고, 직원의 출퇴근과 무관하게 데스크는 항상 그 자리에 있다.

```
Gen 2 (sidecar per Pod):             Gen 3 (node-level proxy):
+-node---------------------+         +-node---------------------+
| +Pod-----+  +Pod-----+   |         |  +Pod+   +Pod+   +Pod+   |
| |app|prox|  |app|prox|   |         |  |app|   |app|   |app|   |
| +--------+  +--------+   |         |  +-+-+   +-+-+   +-+-+   |
+--------------------------+         |    |       |       |     |
 proxy count = Pod count             |    +-------+-------+     |
 lifecycle problems x N              |            |             |
                                     |    [ node proxy x 1 ]    |
                                     +--------------------------+
                                      lifecycle problem: gone
```

2세대는 프록시가 Pod 수만큼 늘어나고 라이프사이클 문제도 쌍마다 생기지만, 3세대는 노드당 프록시 1개로 통합되면서 라이프사이클 문제 자체가 소멸한다.

두 가지 대표 구현이 있다.

| | Istio Ambient Mesh | Cilium |
|---|---|---|
| **접근** | 노드마다 전용 프록시(ztunnel) 배치 | 별도 프록시 없이 CNI 계층에 기능 내장 |
| **비유** | 층마다 안내데스크 신설 | 건물 배선 자체에 자동응답 기능 내장 |
| **핵심 기술** | ztunnel (zero-trust tunnel) | eBPF |

Cilium은 여기서 한 발 더 나간다. 어차피 네트워크 배관(CNI)을 자기가 다 깔았으니, 프록시를 따로 세우는 대신 배관 자체에 그 기능을 심어버렸다 — 데스크라는 별도 존재마저 생략한 셈이다. "커널 아래까지 내려간다"는 말이 여기서 나온다.

---

## 4. CNI의 실체

3세대를 이해하려면 CNI가 정확히 무엇인지 알아야 한다. 먼저 흔한 오해 하나 — **CNI는 프로토콜이 아니다.**

### 4.1 프로토콜이 아니라 규격이다

CNI(Container Network Interface)는 **"컨테이너에 네트워크를 붙이는 프로그램은 이렇게 만들어라"** 라는 규격이다. USB가 포트 모양과 신호 방식을 정의한 규격이고, 그 규격을 지키면 어떤 마우스든 꽂히는 것과 같은 구조다.

```
CNI 규격 (문서):
  "네트워크 플러그인은
   ① 실행 파일(binary)이어야 하고
   ② ADD/DEL 명령을 받아야 하고
   ③ 설정과 결과는 JSON으로 주고받아야 한다"

규격을 따르는 제품들:
  Calico, Flannel, Cilium, AWS VPC CNI, Weave...
```

규격이 같으니 K8s는 어떤 CNI 플러그인이든 갈아끼울 수 있다. 그리고 중요한 사실 — **CNI는 특정 세대의 기술이 아니라 모든 세대에 항상 존재하는 필수 기반**이다. CNI 없이는 Pod가 IP조차 받지 못한다.

실체는 노드의 디스크에서 직접 확인할 수 있다.

```bash
# 플러그인 = 그냥 실행 파일
$ ls /opt/cni/bin/
calico  bridge  loopback  host-local  portmap ...

# 설정 = 그냥 JSON
$ cat /etc/cni/net.d/10-calico.conflist
```

### 4.2 Pod가 생길 때 실제로 벌어지는 일

CNI 플러그인은 상주 데몬이 아니다. **Pod 생성/삭제 순간에만 호출됐다가 일 끝내고 종료되는 실행 파일**이다.

```
① kubelet: "Pod 하나 만들어야겠다"
② 런타임이 Pod의 빈 네트워크 공간(netns) 생성
   → 이 시점: 랜카드도 IP도 없는 깡통 📦
③ 런타임이 CNI 플러그인 호출
   CNI_COMMAND=ADD, 설정 JSON을 stdin으로
④ 플러그인의 실제 작업:
   - 가상 랜선(veth pair) 생성 — 한쪽은 Pod, 한쪽은 노드
   - IP 할당 (예: 10.244.1.5)
   - 라우팅 규칙 추가
⑤ 결과 JSON 반환 → 종료 (퇴근)
⑥ Pod 통신 가능 ✅
```

전기기사를 떠올리면 된다. 새 입주자(Pod)가 오면 관리사무소(kubelet)가 기사(플러그인)를 호출하고, 기사는 콘센트를 뚫고(veth) 계량기 번호를 부여하고(IP) 배전반에 등록한(라우팅) 뒤 돌아간다. **상주하지 않고 부를 때만 온다.**

이걸 보면 프로토콜과의 차이가 분명해진다.

| | 프로토콜 (TCP, HTTP) | CNI |
|---|---|---|
| 정의하는 것 | 데이터를 **주고받는 방법** | 네트워크를 **설치하는 프로그램의 규격** |
| 동작 시점 | 통신하는 내내 | Pod 생성/삭제 순간에만 |
| 비유 | 전화 통화 예절 | 전화기 설치 기사 자격 규정 |

CNI가 배선을 깔고 나면, 그 위로 흐르는 트래픽은 평범한 TCP/IP다. **CNI는 공사 담당이지 통화 담당이 아니다.**

### 4.3 "CNI 레이어"라는 관용어

그런데 모순처럼 보이는 지점이 있다. 설치 기사는 퇴근한다면서, "Cilium은 CNI 레이어에서 트래픽을 처리한다"는 말은 무엇인가?

답: "CNI 레이어"는 공식 용어가 아니라 관용 표현이고, 가리키는 것은 규격이 아니라 **"CNI 제품이 깔아놓고 관리하는 네트워크 기반시설 전체"** 다. "Cilium을 설치한다"는 것은 실제로 부품 3개를 배치하는 일이다.

```
"Cilium" 설치 시 실제 배치되는 것:

① CNI 플러그인 바이너리   /opt/cni/bin/cilium-cni
   → 규격 담당. Pod 생성 시만 호출, 퇴근 ✅

② cilium-agent (데몬)     노드마다 상주
   → 정책 관리, eBPF 프로그램 로드/갱신

③ eBPF 프로그램           커널 안에 상주 ⭐
   → 흐르는 트래픽을 실시간 처리
     (로드밸런싱, 암호화, 관측)
```

트래픽을 실제로 처리하는 것은 ③이다. 설치 기사(①)가 공사하러 온 김에 **벽 안에 스마트 배전 시스템(③)을 심고, 상주 관리인(②)을 배치하고** 간 구조다. 용어를 분리하면 모순이 사라진다.

| 용어 | 의미 | 동작 시점 |
|---|---|---|
| **CNI (규격)** | 문서상의 인터페이스 정의 | — |
| **CNI 플러그인** | 규격을 따르는 실행 파일 | Pod 생성/삭제 순간 |
| **"CNI 레이어"** (관용어) | CNI 제품이 관리하는 기반시설 전체 (veth + 라우팅 + eBPF + 에이전트) | 24시간 상시 |

같은 규격에 꽂히는 플러그인이라도 제품별로 얹은 것이 다르다 — Flannel은 규격 최소한(IP 붙이기)만, Calico는 + NetworkPolicy, Cilium은 + 메시 기능까지. "메시 + CNI"라는 말은 CNI를 새로 도입한다는 뜻이 아니라, **원래 있던 배관 계층에 메시 기능을 통합하는 방향**을 뜻한다.

---

## 5. eBPF — 커널 아래로

"다음 단계는 커널 아래까지 내려간다"의 정체가 eBPF다.

출발점은 단순한 사실이다. **어차피 모든 패킷은 커널을 통과한다.** 그렇다면 유저 공간의 프록시로 패킷을 올렸다 내렸다 왕복시킬 게 아니라, 커널 안에서 바로 처리하면 된다.

```
사이드카 경로 (왕복 지옥):
  앱 → 커널 → 프록시(유저 공간) → 커널 → 네트워크
       ↑ 매 요청마다 컨텍스트 스위칭 비용

eBPF 경로:
  앱 → 커널 (여기서 처리 끝) → 네트워크
```

```
앱 (유저 공간)
────────────────────────
커널 (네트워크 스택)   ← 🎯 eBPF 프로그램이 여기서
   로드밸런싱, 라우팅,      트래픽을 직접 처리
   관측, 보안 정책
────────────────────────
하드웨어
```

eBPF는 커널을 재컴파일하지 않고도 커널 안에서 검증된 프로그램을 실행하게 해주는 기술이다. Cilium이 이것의 대표 주자이며, CNI 플러그인이면서 eBPF로 로드밸런싱·네트워크 정책·관측(Hubble)까지 커널 레벨에서 해결한다. "메시 + CNI + 커널"이라는 흐름이 정확히 Cilium이 걷는 길이다.

---

## 6. 정리 — 패턴은 죽지 않았다

처음의 질문으로 돌아가자. **"앱 대신 바깥일을 누가 해줄 것인가"** — Ambassador 패턴과 그 후계자들은 전부 이 하나의 질문에 대한 답이고, 달라진 것은 답변자의 근무지뿐이다.

```
질문: 앱 대신 바깥일 해줄 사람 구함

1세대: 없음. 앱이 직접             → 책임 2개, 재사용 불가
2세대: 개인 비서 (Ambassador)      → Pod 안. 비서가 Pod 수만큼 필요
3세대: 층 안내데스크 (ztunnel)      → 노드당 1개. 라이프사이클 문제 소멸
다음:   배선 내장 (Cilium/eBPF)     → 커널 속. 대리인의 존재조차 안 보임
```

| | Ambassador (2세대) | ztunnel / eBPF (3세대~) |
|---|---|---|
| **하는 일** | 앱 대신 외부 통신 처리 | **완전히 동일** |
| **사는 곳** | Pod 안 (앱과 한집) | 노드 / 커널 (앱 밖) |
| **개수** | Pod마다 1개 | 노드마다 1개 (또는 0개처럼 보임) |
| **앱 YAML** | 컨테이너 2줄 추가 필요 | 건드릴 필요 없음 |

그래서 18장을 공부한 가치는 사라지지 않는다.

**원리가 이어진다.** "앱은 비즈니스 로직만, 네트워크는 인프라가"라는 방향은 세대가 바뀌어도 그대로다. Ambassador를 이해하고 있으면 Ambient Mesh는 "같은 일을 노드에서 하는 것", Cilium은 "같은 일을 커널에서 하는 것"으로 바로 이해된다.

**레거시가 남아 있다.** 기존 클러스터에는 여전히 사이드카 방식이 대량으로 돌아가고 있다. Istio 클래식 환경을 트러블슈팅하려면 결국 이 패턴을 알아야 한다.

**설명할 때 깊이가 달라진다.** "Ambassador 패턴 아세요?"라는 질문에 패턴 설명만 하는 것보다, "다만 라이프사이클 불일치와 Pod당 프록시 비용 때문에 요즘은 Ambient Mesh나 eBPF 기반으로 넘어가는 추세"까지 이어서 답할 수 있으면 훨씬 낫다.

> 대리인은 옆방(Pod) → 관리실(노드) → 건물 배관(커널) 속으로 점점 깊이 숨어들었다.
> 이제 앱은 대리인의 존재조차 모른다.
> **패턴이 죽은 것이 아니라, 너무 성공해서 보이지 않게 된 것이다.**
