---
series: ["K8sPatterns"]
title: "K8sPatterns.13 Service Discovery"
date: 2026-07-22T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "networking"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.13 Service Discovery'
  relative: true
summary: "동적으로 배치되는 Pod를 내부/외부에서 안정적으로 찾아가는 방법 — ClusterIP, NodePort, LoadBalancer, Ingress까지."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-왜-pod-ip를-직접-쓰면-안-되나" style="color:var(--secondary,inherit);text-decoration:none;">2.1 왜 Pod IP를 직접 쓰면 안 되나</a></div>
    <div><a href="#22-쿠버네티스-이전-시대-client-side-discovery" style="color:var(--secondary,inherit);text-decoration:none;">2.2 쿠버네티스 이전 시대: Client-Side Discovery</a></div>
    <div><a href="#23-쿠버네티스-이후-시대-server-side-discovery" style="color:var(--secondary,inherit);text-decoration:none;">2.3 쿠버네티스 이후 시대: Server-Side Discovery</a></div>
  </div>
  <div><a href="#3-internal-service-discovery" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Internal Service Discovery</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-clusterip--service-리소스" style="color:var(--secondary,inherit);text-decoration:none;">3.1 ClusterIP — Service 리소스</a></div>
    <div><a href="#32-virtual-ip의-실체-kube-proxy와-iptables" style="color:var(--secondary,inherit);text-decoration:none;">3.2 Virtual IP의 실체: kube-proxy와 iptables</a></div>
    <div><a href="#33-디스커버리-방법-1-환경변수" style="color:var(--secondary,inherit);text-decoration:none;">3.3 디스커버리 방법 1: 환경변수</a></div>
    <div><a href="#34-디스커버리-방법-2-dns" style="color:var(--secondary,inherit);text-decoration:none;">3.4 디스커버리 방법 2: DNS</a></div>
    <div><a href="#35-clusterip-기타-특성" style="color:var(--secondary,inherit);text-decoration:none;">3.5 ClusterIP 기타 특성</a></div>
  </div>
  <div><a href="#4-manual-service-discovery" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Manual Service Discovery</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-selector-없는-service--수동-endpoint" style="color:var(--secondary,inherit);text-decoration:none;">4.1 Selector 없는 Service + 수동 Endpoint</a></div>
    <div><a href="#42-externalname" style="color:var(--secondary,inherit);text-decoration:none;">4.2 ExternalName</a></div>
  </div>
  <div><a href="#5-external-service-discovery" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. External Service Discovery</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-nodeport" style="color:var(--secondary,inherit);text-decoration:none;">5.1 NodePort</a></div>
    <div><a href="#52-loadbalancer" style="color:var(--secondary,inherit);text-decoration:none;">5.2 LoadBalancer</a></div>
    <div><a href="#53-ingress" style="color:var(--secondary,inherit);text-decoration:none;">5.3 Ingress</a></div>
  </div>
  <div><a href="#6-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. Discussion</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Service Discovery 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pod IP는 계속 바뀐다 → 안정적인 엔드포인트가 필요하다
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
        내부 Pod끼리           외부 → 내부          내부 → 외부
        ClusterIP / DNS    NodePort / LB / Ingress   ExternalName
```

Kubernetes에 배포된 애플리케이션은 거의 단독으로 존재하지 않는다. 클러스터 내부의 다른 서비스와 통신하거나, 외부 사용자의 요청을 받거나, 외부 DB에 연결하는 등 다양한 방향의 네트워크 통신이 필요하다.

문제는 Pod IP가 동적으로 바뀐다는 것이다. Pod가 재시작되거나 다른 노드로 옮겨지면 IP가 바뀌고, 스케일 업/다운 시 Pod 개수도 달라진다. **Service Discovery 패턴**은 이 문제를 해결하기 위해 소비자(Consumer)가 항상 같은 주소로 서비스 제공자(Producer)를 찾아갈 수 있도록 안정적인 엔드포인트를 제공한다.

---

## 2. Problem

### 2.1 왜 Pod IP를 직접 쓰면 안 되나

```
Pod가 생성될 때 IP가 동적으로 할당된다

배포 직후:  결제 Pod → 10.108.0.5
Pod 재시작: 결제 Pod → 10.108.1.23  (바뀜!)
스케일 업:  결제 Pod 3개로 늘어남   (어디로 보내지?)
```

만약 다른 서비스가 Pod IP를 직접 알고 접속한다면, Pod가 재시작될 때마다 주소를 갱신해야 한다. 이를 개발자가 직접 추적·등록·발견하는 것은 사실상 불가능에 가깝다.

### 2.2 쿠버네티스 이전 시대: Client-Side Discovery

Kubernetes 이전에는 **Client-Side Discovery** 방식이 일반적이었다. 서비스 소비자(Consumer)가 레지스트리(Registry)에서 서비스 목록을 직접 조회하고, 어떤 인스턴스로 요청을 보낼지 스스로 선택했다.

```
서비스 레지스트리 (ZooKeeper / Consul)
  ↑ 등록               ↓ 조회
서비스 인스턴스         소비자
  - Instance A          → 목록 받아서
  - Instance B          → 직접 하나 선택
  - Instance C          → 요청 전송
```

레지스트리는 쉽게 말해 **"서비스 주소록"** 이다. 서비스가 뜰 때 자신의 IP를 등록하고, 죽을 때 삭제한다. 소비자는 레지스트리에서 목록을 받아 직접 인스턴스를 골라 통신한다.

대표적인 구현체:

| 도구 | 설명 |
|---|---|
| **ZooKeeper** | 분산 코디네이션 서비스, 서비스 등록/조회 |
| **Consul** | 서비스 디스커버리 + 헬스체크 |
| **Ribbon** | Netflix OSS, 클라이언트 사이드 로드밸런서 |

이 방식은 소비자마다 디스커버리 로직을 직접 구현해야 하고, 언어/프레임워크마다 에이전트가 달라지며, 레지스트리 운영도 별도로 필요해 복잡도가 높다.

### 2.3 쿠버네티스 이후 시대: Server-Side Discovery

Kubernetes는 이 모든 책임을 **플랫폼 레벨**로 끌어올렸다. 개발자가 직접 구현하던 배치, 헬스체크, 자가치유, 서비스 디스커버리, 로드밸런싱이 전부 Kubernetes가 자동으로 처리한다.

```
예전 (Client-Side):
소비자가 레지스트리 조회 → 직접 선택 → 요청

지금 (Server-Side):
소비자 → Service(고정 엔드포인트)만 호출
              ↓
         Kubernetes가 알아서 Pod 선택 후 전달
```

개발자는 더 이상 디스커버리 코드를 짤 필요가 없다. **비즈니스 코드만 작성하면 Kubernetes가 나머지를 처리한다.**

---

## 3. Internal Service Discovery

### 3.1 ClusterIP — Service 리소스

Kubernetes에서 내부 서비스 디스커버리의 핵심은 **Service 리소스**다. 동일한 기능을 제공하는 Pod 집합에 대해 고정적이고 안정적인 진입점(ClusterIP)을 제공한다.

```yaml
# Example 13-1. A simple Service
apiVersion: v1
kind: Service
metadata:
  name: random-generator        # ① DNS 이름으로 사용됨 — random-generator.default.svc.cluster.local
spec:
  selector:
    app: random-generator       # ② 이 라벨 가진 Pod들을 묶음 — Pod 생성 순서와 무관하게 매칭
  ports:
    - port: 80                  # ③ 클라이언트가 접근하는 포트 (ClusterIP:80)
      targetPort: 8080          # ④ 실제 Pod가 듣는 포트 — 컨테이너 내부 포트로 전달
      protocol: TCP             # ⑤ 기본값 TCP, UDP/SCTP도 지정 가능
```

Service가 생성되면 Kubernetes는 자동으로 **ClusterIP(가상 IP)** 를 할당한다. 이 IP는 Service가 존재하는 한 절대 바뀌지 않는다.

```
클라이언트 Pod
      ↓
ClusterIP: 10.109.0.5 (고정, 가상IP)
      ↓
Kubernetes가 실제 Pod IP로 변환
      ↓
random-generator Pod A / B / C 중 하나
```

셀렉터(selector)가 핵심이다. Pod가 나중에 생겨도, 먼저 생겨도 라벨만 맞으면 Service가 자동으로 묶어준다.

```
Pod 먼저 생성 → Service 나중에 생성
→ 라벨 보고 자동 연결 ✅

Service 먼저 생성 → Pod 나중에 생성
→ 라벨 보고 자동 연결 ✅
```

### 3.2 Virtual IP의 실체: kube-proxy와 iptables

ClusterIP는 실제로 어떤 네트워크 인터페이스에도 존재하지 않는 **가상 IP**다. 그렇다면 패킷이 어떻게 실제 Pod에 도달할까?

모든 노드에서 실행 중인 **kube-proxy**가 새 Service를 감지하고, 노드의 **iptables** 규칙을 업데이트한다.

```
클라이언트 → 10.109.0.5:80 (가상 IP)
↓
iptables 규칙 발동 ("이 IP로 오는 패킷 잡아서 변환")
↓
10.108.0.5:8080 (실제 Pod IP)로 교체
↓
실제 Pod에 도달
```

중요한 제약이 하나 있다. iptables는 Service 정의에 명시된 TCP/UDP 프로토콜에 대해서만 규칙을 추가하므로, **ClusterIP로 ping(ICMP)은 불가능하다.** curl은 되지만 ping은 응답이 없다.

가상 IP가 필요한 이유는 간단하다. Pod IP는 계속 바뀌지만, 클라이언트에게는 항상 같은 고정 주소를 줘야 하기 때문이다.

```
실제 IP(Pod IP) 직접 사용 시
→ Pod 죽으면 IP 사라짐 ❌
→ 스케일 업 시 새 IP 모름 ❌

가상 IP(ClusterIP) 사용 시
→ Pod가 몇 개든, IP가 바뀌든 ClusterIP는 그대로 ✅
→ kube-proxy가 뒤에서 실제 Pod IP로 변환 ✅
```

### 3.3 디스커버리 방법 1: 환경변수

Pod가 시작될 때 그 시점까지 존재하는 모든 Service의 정보가 자동으로 환경변수로 주입된다.

```bash
# Example 13-2. Service-related environment variables
RANDOM_GENERATOR_SERVICE_HOST=10.109.72.32
RANDOM_GENERATOR_SERVICE_PORT=80
```

앱 코드에서는 이 환경변수를 읽어 Service에 접근할 수 있다.

```python
import os, requests

host = os.environ['RANDOM_GENERATOR_SERVICE_HOST']
port = os.environ['RANDOM_GENERATOR_SERVICE_PORT']
requests.get(f"http://{host}:{port}")
```

**장점**

- 어떤 언어로도 환경변수 읽기 가능 (언어 무관)
- 클러스터 밖에서도 환경변수 직접 설정으로 테스트 가능

**단점 — 순서 제약**

```
❌ 잘못된 순서
Pod 먼저 시작 → Service 나중에 생성
→ 환경변수 없음! 영원히 접근 불가 (Pod 재시작 필요)

✅ 올바른 순서
Service 먼저 생성 → Pod 나중에 시작
→ 환경변수 정상 주입
```

환경변수는 Pod **시작 시점**에 딱 한 번 주입된다. 이미 실행 중인 Pod에는 나중에 추가할 수 없다.

### 3.4 디스커버리 방법 2: DNS

Kubernetes는 클러스터 내부에 **CoreDNS** 라는 DNS 서버를 실행한다. 새 Service가 생성되면 CoreDNS에 자동으로 등록되고, 모든 Pod는 이 DNS 서버를 자동으로 사용하도록 구성된다.

```
Pod에서 random-generator 호출 시

random-generator:80 입력
↓
CoreDNS 조회
↓
"random-generator = 10.109.0.5 야"
↓
실제 Service IP로 연결
```

클라이언트 입장에서는 IP를 몰라도 Service 이름만 알면 된다.

```python
# DNS 방식 — 이름만 쓰면 끝
requests.get("http://random-generator:80")
```

**FQDN (완전 정규화 도메인 이름)**

Service의 전체 DNS 주소는 다음과 같은 형식이다.

```
random-generator . default . svc . cluster.local
      ①               ②       ③        ④
```

| 부분 | 의미 |
|---|---|
| ① `random-generator` | Service 이름 |
| ② `default` | 네임스페이스 |
| ③ `svc` | Service 리소스 표시 |
| ④ `cluster.local` | 클러스터 고유 suffix |

같은 네임스페이스에서는 Service 이름만 써도 되고, 다른 네임스페이스에서는 `random-generator.default` 형식으로 쓰면 된다. 어떻게 이게 가능한지, Pod 내부를 들여다보면 그 답이 있다.

**/etc/resolv.conf: Pod가 DNS를 찾아가는 설정 파일**

Pod 내부에는 리눅스 표준 DNS 설정 파일인 `/etc/resolv.conf`가 있다. `random-generator`처럼 짧은 이름만 입력해도 CoreDNS까지 도달할 수 있는 이유가 이 파일 안에 있다.

```
# Pod 내부 /etc/resolv.conf 예시
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

| 줄 | 의미 |
|---|---|
| `nameserver` | 질의를 보낼 DNS 서버 IP — CoreDNS의 ClusterIP |
| `search` | 짧은 이름 뒤에 자동으로 붙여볼 접미사 목록 |
| `options ndots:5` | 점(`.`)이 5개 미만인 이름은 먼저 search 목록으로 시도 |

이 파일은 개발자가 손으로 작성하는 게 아니다. **kubelet이 Pod를 생성할 때 자동으로 만들어 주입**한다. 앱 코드가 이 파일을 직접 읽는 것도 아니다. 리눅스의 DNS resolver(glibc, musl 등)가 이름을 조회할 때마다 OS 레벨에서 알아서 참고하는 표준 메커니즘이다. 즉 앱은 `requests.get("http://random-generator:80")`이라고만 쓰면, 그 뒤의 이름 해석은 전부 OS가 이 파일을 보고 처리해준다.

**search 도메인: 짧은 이름이 FQDN으로 완성되는 과정**

`search` 줄에는 접미사 후보가 순서대로 나열되어 있다. 짧은 이름을 입력하면 resolver가 이 목록을 하나씩 붙여가며 순서대로 조회를 시도한다.

```
Pod에서 "random-generator" 조회 시 시도 순서

1차 시도: random-generator.default.svc.cluster.local  ← 성공 시 여기서 종료
2차 시도: random-generator.svc.cluster.local           (1차 실패 시에만)
3차 시도: random-generator.cluster.local                (2차 실패 시에만)
```

`random-generator.default`처럼 이미 네임스페이스를 포함한 이름을 쓰면 첫 번째 search 접미사(`default.svc.cluster.local`)만 붙어도 바로 FQDN이 완성되므로, 결과적으로 짧은 이름과 `.default`를 붙인 이름 둘 다 정상 동작한다.

만약 `search` 줄이 없다면? 짧은 이름 그대로 인터넷의 공용 DNS 서버로 질의가 나가버리고, `random-generator`라는 도메인은 당연히 존재하지 않으므로 조회는 실패한다. search 도메인이야말로 "Service 이름 하나만 쓰면 되는" 경험을 가능하게 하는 핵심 장치다.

**CoreDNS 자신도 하나의 Service다**

`nameserver 10.96.0.10`에 박혀 있는 이 IP는 다름 아닌 **CoreDNS의 ClusterIP**다. CoreDNS는 `kube-system` 네임스페이스에 `kube-dns`라는 이름의 Service로 떠 있는, 다른 Service들과 동일한 존재다.

```
kube-system 네임스페이스
└── Service: kube-dns
      ClusterIP: 10.96.0.10   ← 클러스터 내 모든 Pod의 resolv.conf에 박히는 IP
      └── CoreDNS Pod(들)
```

여기서 재밌는 순환 문제가 생긴다. "Service 이름을 DNS로 찾으려면 CoreDNS가 필요한데, CoreDNS 자체도 Service라면 그건 어떻게 찾지?"라는 닭이 먼저냐 달걀이 먼저냐 문제다. Kubernetes는 이걸 아주 실용적으로 해결한다. **CoreDNS의 ClusterIP는 DNS 조회 없이 resolv.conf에 고정 IP로 직접 박아둔다.** 즉 CoreDNS를 찾아가는 첫걸음만큼은 DNS를 쓰지 않고 우회하는 셈이다.

**네임스페이스마다 resolv.conf가 조금씩 다르다**

`search` 줄의 첫 번째 항목은 Pod가 속한 네임스페이스 이름을 반영해 자동으로 바뀐다.

```
default 네임스페이스 Pod
search default.svc.cluster.local svc.cluster.local cluster.local

payment 네임스페이스 Pod
search payment.svc.cluster.local svc.cluster.local cluster.local
                ↑
        네임스페이스 이름만 다르고 나머지는 동일
```

이 덕분에 `payment` 네임스페이스의 Pod가 `random-generator`라는 짧은 이름을 조회하면, 자동으로 `random-generator.payment.svc.cluster.local`부터 먼저 시도한다. 즉 **짧은 이름은 항상 "내가 속한 네임스페이스" 안에서만 자동으로 해석**된다.

이건 의도된 보안 설계다. 다른 네임스페이스의 Service를 짧은 이름만으로 우연히, 또는 실수로 찾아가는 사고를 막는다. 정말로 다른 네임스페이스의 Service에 접근하고 싶다면 `random-generator.default`처럼 네임스페이스를 명시적으로 적어야 한다. 짧은 이름이 조용히 다른 팀의 Service로 연결되는 일은 일어나지 않는다.

**결론적으로**, 같은 네임스페이스 안에서 Service 이름만으로 접근이 가능한 이유는 우연이 아니라 ① kubelet이 자동 생성한 resolv.conf, ② 그 안의 search 도메인이 붙여주는 네임스페이스 접미사, ③ CoreDNS가 고정 IP로 항상 먼저 접근 가능하다는 세 가지 장치가 맞물린 결과다.

### 레퍼런스

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>이 동작은 Kubernetes 공식 문서 <strong>"DNS for Services and Pods"</strong>의 <strong>"Namespaces of Services"</strong> 섹션에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "DNS queries may be expanded using the Pod's <code>/etc/resolv.conf</code>. kubelet configures this file for each Pod. For example, a query for just <code>data</code> may be expanded to <code>data.test.svc.cluster.local</code>. The values of the <code>search</code> option are used to expand queries."
  </blockquote>
  <div>[해석] "DNS 조회는 Pod의 <code>/etc/resolv.conf</code>를 통해 확장될 수 있다. kubelet이 각 Pod마다 이 파일을 설정해준다. 예를 들어 <code>data</code>라는 짧은 이름만으로 조회해도 <code>data.test.svc.cluster.local</code>로 자동 확장될 수 있다. <code>search</code> 옵션의 값들이 이 조회 확장에 사용된다."</div>
  <div style="margin-top:10px;">그리고 바로 아래 예시로 제시된 <code>resolv.conf</code> 블록:</div>
  <pre style="margin:8px 0;overflow-x:auto;"><code>nameserver 10.32.0.10
search &lt;namespace&gt;.svc.cluster.local svc.cluster.local cluster.local
options ndots:5</code></pre>
  <div>이 두 부분이 "Service 이름만 써도 되는" 경험의 공식 근거다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#namespaces-of-services">kubernetes.io — DNS for Services and Pods #namespaces-of-services</a></div>
</div>
{{< /rawhtml >}}

**환경변수 방식과의 결정적 차이**

```
환경변수: Pod 시작 시점에 결정 → Service가 먼저 있어야 함
DNS:      요청 시점마다 조회   → 나중에 Service 생겨도 그때 찾으면 됨
```

DNS 방식에서 Pod가 먼저 떠 있어도 괜찮은 이유는, 요청을 보낼 때 그때그때 CoreDNS에 물어보기 때문이다. Service가 나중에 생성되면 CoreDNS에 등록되고, 그 이후 Pod의 조회는 성공한다.

한 가지 보완 포인트가 있다. **비표준 포트**는 DNS로 알 수 없다. `http://random-generator:80` 처럼 표준 포트라면 그냥 쓰면 되지만, 포트가 비표준이라면 환경변수(`RANDOM_GENERATOR_SERVICE_PORT`)를 읽어 보완한다.

### 3.5 ClusterIP 기타 특성

**다중 포트 (Multiple Ports)**

Service 하나에 여러 포트를 동시에 정의할 수 있다.

```yaml
ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

HTTP/HTTPS를 모두 지원하는 Pod에 Service 두 개를 만들 필요가 없다.

**세션 어피니티 (Session Affinity)**

기본적으로 Service는 요청마다 랜덤으로 Pod를 선택한다. `sessionAffinity: ClientIP`를 설정하면 같은 클라이언트 IP에서 오는 요청은 항상 같은 Pod로 전달된다.

```
기본값:
요청1 → Pod A / 요청2 → Pod C / 요청3 → Pod B (랜덤)

sessionAffinity: ClientIP:
10.0.0.1의 모든 요청 → 항상 Pod A ✅
```

단, Service는 L4(Transport Layer) 로드밸런싱을 수행한다. IP와 포트만 보며, HTTP 쿠키 같은 애플리케이션 레벨 정보는 볼 수 없다. 쿠키 기반 세션 고정이 필요하다면 Ingress를 써야 한다.

**Readiness Probe 연동**

Pod가 readinessProbe를 정의했고 체크가 실패하고 있다면, 라벨이 맞더라도 Service 엔드포인트 목록에서 자동으로 제외된다. 준비된 Pod에만 트래픽이 간다.

```
Pod A (준비됨)   ✅ → 트래픽 받음
Pod B (준비중)   ❌ → 트래픽 차단 (라벨 맞아도!)
```

**ClusterIP 직접 지정**

기본적으로 자동 할당되지만, `.spec.clusterIP` 필드로 직접 지정할 수 있다. 레거시 앱이 특정 IP를 하드코딩하거나 기존 DNS 항목을 재사용해야 할 때 유용하다. 단, 권장하지 않는다.

---

## 4. Manual Service Discovery

일반 Service는 셀렉터로 Pod를 자동으로 찾아 엔드포인트를 관리한다. 하지만 외부 DB, 레거시 시스템처럼 **Pod가 아닌 대상에 연결**할 때는 엔드포인트를 수동으로 지정한다.

### 4.1 Selector 없는 Service + 수동 Endpoint

**Step 1. 셀렉터 없는 Service 생성**

```yaml
# Example 13-3. Service without selector
apiVersion: v1
kind: Service
metadata:
  name: external-service      # ① Endpoint와 이름을 맞출 기준 — DNS 이름으로도 사용됨
spec:
  type: ClusterIP             # ② 내부 전용 가상 IP만 발급 (기본값이라 생략 가능)
  ports:
    - protocol: TCP
      port: 80                # ③ 내부 Pod가 접근할 포트
  # selector 없음 — ④ Kubernetes야 Pod 찾지 마, 내가 직접 지정할게
```

**Step 2. 같은 이름으로 Endpoint 수동 생성**

```yaml
# Example 13-4. Endpoints for an external service
apiVersion: v1
kind: Endpoints
metadata:
  name: external-service   # ① Service 이름과 반드시 같아야 연결됨!
subsets:
  - addresses:
    - ip: 1.1.1.1          # ② 외부 서버 1 — 실제 라우팅 대상
    - ip: 2.2.2.2          # ③ 외부 서버 2 — 여러 개면 자동 로드밸런싱
    ports:
    - port: 8080           # ④ 외부 서버가 실제로 듣는 포트 (Service의 port와 별개)
```

Kubernetes는 Service와 Endpoint를 **이름으로 매칭**한다. 이름이 같아야 Service가 해당 Endpoint를 사용한다.

```
내부 Pod
↓
external-service ClusterIP (가상IP)
↓
Endpoint 리소스 (수동 지정)
↓
1.1.1.1:8080 또는 2.2.2.2:8080 (로드밸런싱)
```

내부 Pod 입장에서는 외부 서버든 내부 Pod든 Service 이름으로 똑같이 접근한다. 외부 서버 IP가 바뀌어도 Endpoint만 수정하면 되고, 코드는 건드릴 필요가 없다.

**주의**: Endpoint에는 일반 Pod IP나 외부 IP는 넣을 수 있지만, 다른 Service의 ClusterIP(가상 IP)는 넣을 수 없다. ClusterIP는 iptables에서만 처리되는 주소라 Endpoint에서는 라우팅이 불가하다.

**마이그레이션 활용**

이 패턴의 가장 강력한 활용처는 온프레미스 → Kubernetes 마이그레이션이다.

```
1단계: 온프레미스 서버 운영 중
Endpoint → 외부 서버 IP 직접 지정
클라이언트 → Service IP(고정)로 접근

2단계: Kubernetes로 이전 완료
Service에 selector 추가
Endpoint 수동 관리 → 자동 관리로 전환

클라이언트는 Service IP가 그대로라 아무것도 바꿀 필요 없음 ✅
```

Service를 삭제 후 재생성하면 ClusterIP가 바뀌어버리기 때문에, Service는 유지하면서 selector와 Endpoint만 교체하는 것이 핵심이다.

### 4.2 ExternalName

외부 서비스가 IP가 아닌 도메인 이름으로 제공될 때 사용한다.

```yaml
# Example 13-5. Service with an external destination
apiVersion: v1
kind: Service
metadata:
  name: database-service            # ① 내부 Pod가 사용할 이름 — 실제 도메인을 감춤
spec:
  type: ExternalName                # ② ClusterIP 발급 없이 DNS CNAME으로만 동작
  externalName: my.database.example.com   # ③ 실제 리다이렉트될 외부 도메인
  ports:
    - port: 80                      # ④ ExternalName에서는 사실상 참고용 (프록시하지 않음)
```

동작 방식은 Manual Endpoint와 다르다. IP가 아니라 **DNS CNAME**으로 동작한다.

```
Manual Endpoint 방식
Pod → ClusterIP → kube-proxy → 외부 IP (프록시 거침)

ExternalName 방식
Pod → DNS 조회 → CNAME → my.database.example.com → 직접 연결 (프록시 없음)
```

`database-service.default.svc.cluster.local`을 조회하면 `my.database.example.com`으로 CNAME 리다이렉트된다. Pod는 Service 이름만 알면 되고, 실제 외부 도메인이 바뀌어도 Service 정의만 수정하면 된다.

**그냥 도메인을 코드에 직접 쓰면 안 되냐?**

직접 써도 동작한다. 하지만 ExternalName을 쓰면 환경마다 다른 도메인을 Service 이름 하나로 추상화할 수 있다.

```
개발환경: database-service → dev.database.example.com
운영환경: database-service → prod.database.example.com

코드는 항상 "database-service"만 씀 ✅
```

---

## 5. External Service Discovery

지금까지는 클러스터 내부에서의 디스커버리였다. 이제 반대 방향, **외부에서 클러스터 안의 Pod에 접근**하는 방법을 다룬다.

ClusterIP는 클러스터 내부 가상 네트워크에만 존재하는 IP라, 외부 인터넷에서는 라우팅 자체가 불가능하다. 외부 진입점을 따로 만들어야 한다.

### 5.1 NodePort

클러스터의 **모든 노드에 특정 포트를 열어** 외부에서 접근하게 하는 방식이다.

```yaml
# Example 13-6. Service with type NodePort
apiVersion: v1
kind: Service
metadata:
  name: random-generator
spec:
  type: NodePort           # ① ClusterIP + 모든 노드의 포트 개방을 함께 생성
  selector:
    app: random-generator  # ② 이 라벨을 가진 Pod로 트래픽 전달
  ports:
    - port: 80          # ③ ClusterIP 포트 (내부용) — 클러스터 내부에서는 여전히 이 포트로 접근
      targetPort: 8080  # ④ 실제 Pod가 듣는 포트
      nodePort: 30036   # ⑤ 모든 노드에 열리는 외부 포트 (30000~32767 범위, 생략 시 자동 할당)
      protocol: TCP     # ⑥ TCP 기본, NodePort는 UDP도 지원
```

포트 흐름:

```
외부 사용자 → 노드IP:30036 (nodePort)
                  ↓
             ClusterIP:80 (port)  ← 자동 생성
                  ↓
             Pod:8080 (targetPort)
```

NodePort는 ClusterIP 위에 올라타는 구조다. NodePort Service를 만들면 ClusterIP도 자동 생성된다.

```
내부에서 접근: ClusterIP:80 → Pod:8080
외부에서 접근: 노드IP:30036 → ClusterIP:80 → Pod:8080
```

**모든 노드에 동시에 열린다**

```
노드A IP: 192.168.1.10
노드B IP: 192.168.1.11

192.168.1.10:30036 → Pod 접근 ✅
192.168.1.11:30036 → Pod 접근 ✅  (Pod가 그 노드에 없어도!)
```

Pod가 없는 노드로 요청이 와도, kube-proxy가 다른 노드의 Pod로 전달해준다.

**단점들**

| 단점 | 설명 |
|---|---|
| 포트 번호 | 30000~32767 사이의 못생긴 포트 번호 |
| 방화벽 | 클라우드에서 해당 포트를 방화벽에서 열어줘야 함 |
| 노드 장애 | 클라이언트가 죽은 노드로 접속하면 연결 실패 (클라이언트가 직접 재시도해야 함) |

**Source NAT 문제**

외부 클라이언트 요청이 한 노드에 도착했는데 Pod가 다른 노드에 있다면, 노드 간 패킷 전달 과정에서 출발지 IP가 노드 IP로 교체된다.

```
클라이언트 (99.99.99.99) → 노드A:30036
↓ (Pod가 노드B에 있음)
노드A가 패킷 수정
출발지 IP: 99.99.99.99 → 노드A IP로 변경!
→ Pod는 진짜 클라이언트 IP를 알 수 없음 ❌
```

`externalTrafficPolicy: Local`을 설정하면 항상 같은 노드의 Pod로만 전달해 Source NAT가 발생하지 않는다. 단, 해당 노드에 Pod가 없으면 연결 실패다. DaemonSet으로 모든 노드에 Pod를 배치하는 경우에 유용하다.

### 5.2 LoadBalancer

NodePort의 한계를 해결하는 방식이다. NodePort 위에 **클라우드 제공자의 로드밸런서**를 자동으로 붙인다.

```yaml
# Example 13-7. Service of type LoadBalancer
apiVersion: v1
kind: Service
metadata:
  name: random-generator
spec:
  type: LoadBalancer             # ① NodePort + ClusterIP + 클라우드 LB까지 한 번에 생성
  clusterIP: 10.0.171.239        # ② Kubernetes가 자동 할당 (내부 전용, 직접 지정 비권장)
  loadBalancerIP: 78.11.24.19    # ③ 원하는 외부IP 지정 (선택 사항, 클라우드 지원 시에만 유효)
  selector:
    app: random-generator        # ④ 트래픽을 전달할 Pod 라벨
  ports:
    - port: 80                   # ⑤ 로드밸런서·ClusterIP 공통 포트
      targetPort: 8080           # ⑥ 실제 Pod가 듣는 포트
status:
  loadBalancer:
    ingress:
      - ip: 146.148.47.155       # ⑦ 실제로 생성된 외부IP — Kubernetes가 결과를 자동으로 채워줌
```

계층 구조:

```
LoadBalancer (클라우드 로드밸런서)
  └── NodePort (자동 생성)
        └── ClusterIP (자동 생성)
              └── Pod
```

LoadBalancer Service 하나만 만들면 아래의 모든 레이어가 자동으로 생성된다.

```
외부 클라이언트
↓
클라우드 로드밸런서 (고정 외부IP)
↓
노드:NodePort (살아있는 노드 자동 선택)
↓
ClusterIP
↓
Pod
```

클라이언트는 로드밸런서 IP 하나만 알면 된다. 노드가 죽어도, Pod가 이동해도, 클라이언트는 아무것도 바꿀 필요가 없다.

**YAML의 IP 3개 이해하기**

| 필드 | 의미 | 누가 |
|---|---|---|
| `spec.clusterIP` | 클러스터 내부 가상IP | Kubernetes 자동 할당 |
| `spec.loadBalancerIP` | 원하는 외부IP (선택) | 개발자가 미리 예약 |
| `status.ingress.ip` | 실제로 생성된 외부IP | Kubernetes가 결과를 여기에 기록 |

`spec`은 내가 원하는 것을 Kubernetes에 요청하는 곳이고, `status`는 Kubernetes가 실제 결과를 알려주는 곳이다. 개발자는 `status.ip`를 확인해 DNS에 등록하거나 외부에 공개한다.

**단점**

Service 하나당 클라우드 로드밸런서 하나가 생성된다. Service가 10개면 로드밸런서도 10개, 그만큼 비용이 발생한다. 이 문제를 해결하는 것이 Ingress다.

이 Service 타입은 클라우드 제공자가 Kubernetes를 지원할 때만 동작한다. 세부 동작(IP 고정 가능 여부, Source IP 보존 여부 등)은 AWS, GCP, DigitalOcean마다 다르므로 각 클라우드 문서를 확인해야 한다.

### 5.3 Ingress

Ingress는 Service 타입이 아니라 **별도의 Kubernetes 리소스**다. Service들 앞에 위치해 스마트 라우터 역할을 한다.

**핵심 강점: 외부IP 하나로 여러 Service 처리**

```
LoadBalancer 방식
결제 Service → 외부IP 1개 💰
주문 Service → 외부IP 1개 💰
유저 Service → 외부IP 1개 💰

Ingress 방식
외부IP 1개
/payment → 결제 Service ✅
/order   → 주문 Service ✅
/user    → 유저 Service ✅
```

Ingress는 HTTP URL 경로까지 보는 **L7(Application Layer) 라우팅**을 수행한다. NodePort, LoadBalancer가 IP/포트만 보는 L4인 것과 차이가 있다.

**기본 Ingress 정의**

```yaml
# Example 13-8. An Ingress definition
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: random-generator
spec:
  defaultBackend:               # ① 별도 rules가 없을 때 모든 요청이 향하는 기본 목적지
    service:
      name: random-generator    # ② 기본 목적지 Service 이름
      port:
        number: 8080            # ③ Service가 노출하는 포트 (targetPort 아님)
```

`defaultBackend`만 쓰면 모든 요청이 하나의 Service로 간다. 이건 LoadBalancer와 큰 차이가 없다. 진짜 강점은 다음의 경로 기반 라우팅이다.

**Fan-out (경로 기반 라우팅)**

```yaml
# Example 13-9. A definition for Nginx Ingress controller
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: random-generator
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /   # ① Controller별 추가 설정 — nginx 전용 네임스페이스 접두사
spec:
  rules:                          # ② 경로별 라우팅 규칙 목록
  - http:
      paths:
      - path: /                   # ③ 매칭 경로
        pathType: Prefix          # ④ /로 시작하는 모든 경로 매칭 (/hello, /foo/bar 등)
        backend:
          service:
            name: random-generator   # ⑤ 이 경로로 온 요청이 향할 Service
            port:
              number: 8080
      - path: /cluster-status     # ⑥ 두 번째 라우팅 규칙 — 별도 Service로 분기
        pathType: Exact           # ⑦ 정확히 /cluster-status만 매칭 (하위 경로 불포함)
        backend:
          service:
            name: cluster-status
            port:
              number: 80
```

`pathType` 차이:

```
Prefix: /abc → /abc, /abc/def, /abc/xyz 전부 매칭
Exact:  /abc → 정확히 /abc만 매칭 (/abc/def는 안됨)
```

라우팅 동작:

```
외부IP:80/              → random-generator:8080
외부IP:80/hello         → random-generator:8080 (Prefix 매칭)
외부IP:80/cluster-status → cluster-status:80
```

**Ingress Controller 필수**

Ingress 리소스는 설계도일 뿐이다. 실제로 동작하려면 클러스터에 **Ingress Controller**가 설치되어 있어야 한다.

```
Ingress 리소스 = 설계도 (무엇을 라우팅할지)
Ingress Controller = 실제 엔진 (어떻게 라우팅할지)
```

대표적인 Controller:

| Controller | 특징 |
|---|---|
| **nginx-ingress** | 가장 널리 사용 |
| **traefik** | 동적 설정, 자동 TLS |
| **AWS ALB Ingress** | AWS 네이티브 ALB 연동 |

Controller마다 추가 설정 방식이 다르다. nginx라면 `annotations`에 `nginx.ingress.kubernetes.io/` 접두사 설정을 넣고, traefik이라면 traefik 전용 설정을 쓴다.

**Ingress Controller도 Pod다**

Ingress Controller는 클러스터 내부에서 Pod로 실행된다. 따라서 내부 DNS를 사용할 수 있고, `random-generator`처럼 Service 이름으로 Pod를 찾아 전달한다.

```
외부
↓
Ingress Controller (Pod, 클러스터 내부)
↓
"random-generator" → CoreDNS → ClusterIP → Pod
```

**Ingress 제공 기능**

- HTTP/HTTPS 기반 URL 경로 라우팅
- 도메인 기반 가상 호스팅 (`payment.myapp.com`, `order.myapp.com`)
- TLS 종료 (HTTPS 처리)
- 로드밸런싱

단, HTTP/HTTPS 외의 프로토콜(TCP, UDP)에는 제한적이다. 비HTTP 트래픽은 NodePort나 LoadBalancer가 더 적합하다.

---

## 6. Discussion

### 전체 메커니즘 정리

| 이름 | 설정 | 방향 | 용도 |
|---|---|---|---|
| **ClusterIP** | `type: ClusterIP` | 내부 | 가장 일반적인 내부 디스커버리 |
| **Headless** | `clusterIP: None` | 내부 | 가상IP 없이 Pod 직접 DNS 접근 (StatefulSet) |
| **Manual IP** | `kind: Endpoints` | 내부→외부 | 외부 IP 직접 지정 |
| **ExternalName** | `type: ExternalName` | 내부→외부 | 외부 도메인 CNAME 연결 |
| **NodePort** | `type: NodePort` | 외부→내부 | 비HTTP 트래픽, 단순 외부 노출 |
| **LoadBalancer** | `type: LoadBalancer` | 외부→내부 | 클라우드 로드밸런서 자동 연동 |
| **Ingress** | `kind: Ingress` | 외부→내부 | HTTP 기반 스마트 라우팅, 비용 절감 |

### 단순 → 복잡 순서

```
ClusterIP       가장 기본, 내부 전용
  ↓
NodePort        외부 노출 기본
  ↓
LoadBalancer    NodePort + 클라우드 로드밸런서
  ↓
Ingress         L7 라우팅, 가장 강력하고 복잡
```

### 핵심 메시지

개발자가 직접 해야 했던 것들 — Pod IP 추적, DNS 등록, 로드밸런싱, 노드 장애 처리 — 이 전부 Kubernetes가 자동으로 처리한다. 개발자는 YAML만 작성하면 된다.

```
Service는 Pod IP(계속 변함)와 클라이언트 사이의 안정적인 추상화 레이어다.
어떤 메커니즘을 선택하느냐는 소비자와 제공자의 위치(내부/외부)에 따라 결정된다.
```

> Service Discovery는 **"Pod를 어떻게 안정적으로 찾아가느냐"** 의 문제다.
> Kubernetes는 클러스터 내부의 ClusterIP/DNS부터 외부 노출을 위한 NodePort/LoadBalancer/Ingress까지,
> 상황에 맞는 다양한 메커니즘을 제공해 이 문제를 플랫폼 레벨에서 해결한다.