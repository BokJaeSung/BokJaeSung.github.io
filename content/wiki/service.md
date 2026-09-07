---
title: "Service"
summary: "죽고 살아나며 IP가 바뀌는 Pod 앞에 두는 고정 주소. 타입에 따라 어디까지 도달할 수 있는지가 달라진다."
categories: ["쿠버네티스", "네트워크"]
tags: ["kubernetes", "network", "service"]
aliases_search: ["서비스", "clusterip", "클러스터아이피", "nodeport", "노드포트", "loadbalancer", "로드밸런서", "headless", "헤드리스"]
---

## 1. 개요

**Service**는 여러 Pod 앞에 두는 **고정 주소**다. 공식 문서는 "Pod 로 실행 중인 네트워크 애플리케이션을 노출하는 방법"이라고 정의한다.

Pod 는 죽고 다시 뜰 때마다 IP 가 바뀐다. 앱이 다른 앱의 IP 를 직접 알고 있으면 그 앱이 재시작하는 순간 연결이 끊긴다. Service 는 그 앞에 안 바뀌는 이름과 IP 를 하나 세워둔다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 250" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pod 의 IP 는 재시작마다 바뀌지만 Service 이름과 IP 는 고정이라 호출하는 쪽이 영향을 받지 않는다">
  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">오른쪽은 계속 바뀌는데, 왼쪽은 아무것도 안 바꿔도 된다</text>

  <!-- 호출하는 쪽 -->
  <text x="26" y="120" font-size="11.5" font-weight="600" fill="#2f6ea8">frontend</text>
  <text x="26" y="136" font-size="9.5" fill="var(--secondary,#888)">부르는 쪽</text>
  <rect x="120" y="98" width="150" height="48" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="195" y="119" text-anchor="middle" font-size="9.5" fill="#2f6ea8">http://backend:8080</text>
  <text x="195" y="134" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".8">이 한 줄이 안 바뀐다</text>

  <!-- Service -->
  <rect x="330" y="98" width="140" height="48" rx="5" fill="none" stroke="#2e9c6d" stroke-width="1.8"/>
  <text x="400" y="119" text-anchor="middle" font-size="10" font-weight="600" fill="#2e9c6d">Service: backend</text>
  <text x="400" y="134" text-anchor="middle" font-size="8.5" fill="#2e9c6d" opacity=".85">10.96.0.12 고정</text>

  <!-- Pod 들 -->
  <rect x="560" y="48" width="180" height="34" rx="4" fill="none" stroke="#c0392b" stroke-width="1.1" stroke-dasharray="4 3"/>
  <text x="650" y="69" text-anchor="middle" font-size="9" fill="#c0392b">Pod  10.1.3.7  ✕ 죽음</text>

  <rect x="560" y="94" width="180" height="34" rx="4" fill="none" stroke="#c0392b" stroke-width="1.1" stroke-dasharray="4 3"/>
  <text x="650" y="115" text-anchor="middle" font-size="9" fill="#c0392b">Pod  10.1.8.2  ✕ 죽음</text>

  <rect x="560" y="140" width="180" height="34" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="650" y="161" text-anchor="middle" font-size="9" font-weight="600" fill="#5a2050">Pod  10.1.2.9  ● 지금</text>

  <!-- 연결 -->
  <path d="M270,122 H326" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <path d="M470,122 H520 V157 H556" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <path d="M470,122 H520 V111 H556" stroke="#c0392b" stroke-width="1" stroke-dasharray="3 3" fill="none" opacity=".45"/>
  <path d="M520,111 V65 H556" stroke="#c0392b" stroke-width="1" stroke-dasharray="3 3" fill="none" opacity=".45"/>

  <text x="298" y="114" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">이름으로</text>
  <text x="650" y="196" text-anchor="middle" font-size="9.5" fill="var(--secondary,#888)">재시작할 때마다 IP 가 새로 배정된다</text>

  <text x="380" y="234" text-anchor="middle" font-size="12" fill="var(--content,#333)">부르는 쪽은 뒤에서 Pod 가 몇 번 죽고 살아나든 모른다</text>
</svg>
</div>
{{< /rawhtml >}}

앱은 `http://backend:8080` 으로 부르면 된다. 뒤에서 Pod 가 몇 개 뜨고 지든 모른다.

## 2. 타입별 도달 범위

네 종류가 있고, 앞의 셋은 **위에 얹히는 구조**다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 300" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="하나의 경로에 ClusterIP 가 항상 있고 NodePort 와 LoadBalancer 는 그 앞에 입구를 하나씩 더 붙이는 구조">
  <text x="380" y="26" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">경로는 하나 — 타입은 그 앞에 입구를 몇 개 더 세울지 정한다</text>

  <!-- 본 경로: ClusterIP → Pod (항상 존재) -->
  <rect x="470" y="120" width="130" height="52" rx="5" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="535" y="142" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2e9c6d">ClusterIP</text>
  <text x="535" y="158" text-anchor="middle" font-size="8.5" fill="#2e9c6d" opacity=".85">10.96.0.12 · 항상 있다</text>

  <rect x="654" y="124" width="76" height="44" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="692" y="151" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">Pod</text>
  <path d="M600,146 H650" stroke="#2e9c6d" stroke-width="1.8" fill="none"/>

  <!-- 입구 3개 -->
  <rect x="300" y="120" width="120" height="52" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="360" y="142" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">NodePort</text>
  <text x="360" y="158" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">30000~32767</text>
  <path d="M420,146 H466" stroke="#2e9c6d" stroke-width="1.8" fill="none"/>

  <rect x="130" y="120" width="120" height="52" rx="5" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="190" y="142" text-anchor="middle" font-size="10" font-weight="600" fill="#c0392b">LoadBalancer</text>
  <text x="190" y="158" text-anchor="middle" font-size="8.5" fill="#c0392b" opacity=".85">클라우드 공인 IP</text>
  <path d="M250,146 H296" stroke="#2e9c6d" stroke-width="1.8" fill="none"/>

  <!-- 출발지 -->
  <text x="30" y="140" font-size="10" fill="#c0392b">외부</text>
  <text x="30" y="155" font-size="10" fill="#c0392b">사용자</text>
  <path d="M70,146 H126" stroke="#c0392b" stroke-width="1.5" fill="none"/>

  <text x="535" y="212" text-anchor="middle" font-size="10" fill="#2f6ea8">클러스터 안 앱은 여기로 바로 들어온다</text>
  <path d="M535,196 V178" stroke="#2f6ea8" stroke-width="1.5" fill="none"/>

  <!-- 타입별 범위 표시 -->
  <rect x="452" y="100" width="164" height="92" rx="7" fill="none" stroke="#2e9c6d" stroke-width="1" stroke-dasharray="5 4" opacity=".7"/>
  <text x="534" y="94" text-anchor="middle" font-size="9" fill="#2e9c6d">type: ClusterIP</text>

  <rect x="284" y="86" width="332" height="120" rx="8" fill="none" stroke="#2f6ea8" stroke-width="1" stroke-dasharray="5 4" opacity=".7"/>
  <text x="350" y="80" text-anchor="middle" font-size="9" fill="#2f6ea8">type: NodePort</text>

  <rect x="114" y="72" width="502" height="148" rx="9" fill="none" stroke="#c0392b" stroke-width="1" stroke-dasharray="5 4" opacity=".7"/>
  <text x="180" y="66" text-anchor="middle" font-size="9" fill="#c0392b">type: LoadBalancer</text>

  <text x="380" y="266" text-anchor="middle" font-size="12" fill="var(--content,#333)">바깥 타입을 고르면 안쪽 것이 자동으로 함께 만들어진다</text>
  <text x="380" y="288" text-anchor="middle" font-size="10" fill="var(--secondary,#888)">ExternalName 만 이 경로에 없다 — 프록시 없이 DNS CNAME 만 돌려준다</text>
</svg>
</div>
{{< /rawhtml >}}

| 타입 | 어디서 닿나 | 만들면 함께 생기는 것 |
|---|---|---|
| `ClusterIP` (기본) | 클러스터 안에서만 | — |
| `NodePort` | 노드 IP + 고정 포트 | ClusterIP |
| `LoadBalancer` | 외부 IP (클라우드가 발급) | NodePort + ClusterIP |
| `ExternalName` | — (DNS CNAME 만 반환) | 프록시 없음 |

표를 위 그림과 겹쳐 읽으면 이렇게 된다. `NodePort` 를 만들면 ClusterIP 가 **자동으로 함께 생기고**, `LoadBalancer` 를 만들면 NodePort 와 ClusterIP 가 **둘 다 함께 생긴다.** 없애는 게 아니라 앞에 입구를 하나씩 더 세우는 것이다.

```
type: ClusterIP      →  [ClusterIP]
type: NodePort       →  [NodePort] → [ClusterIP]
type: LoadBalancer   →  [LB] → [NodePort] → [ClusterIP]
                          ↑ 새로 생기는 입구      ↑ 항상 있다
```

`ExternalName` 만 성격이 다르다. 트래픽을 넘기는 게 아니라 **DNS 로 다른 이름을 알려줄 뿐**이라 프록시도 ClusterIP 도 없다. 외부 DB 를 클러스터 안 이름처럼 부르고 싶을 때 쓴다.

## 3. 셀렉터와 EndpointSlice

Service 는 IP 목록을 직접 들고 있지 않다. **라벨 셀렉터**로 조건만 적어두면 컨트롤러가 맞는 Pod 를 계속 찾아 채운다.

```yaml
spec:
  selector:
    app: backend        # 이 라벨을 가진 Pod 전부
  ports:
  - port: 80            # Service 가 받는 포트
    targetPort: 9376    # Pod 가 듣는 포트
```

공식 문서의 설명대로 컨트롤러가 "셀렉터에 맞는 Pod 를 계속 스캔해 **EndpointSlice** 를 갱신"한다. Pod 가 늘거나 죽으면 그 목록이 자동으로 바뀐다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 320" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Service 에는 조건만 적혀 있고, 컨트롤러가 라벨이 맞는 Pod 를 찾아 EndpointSlice 에 IP 를 채우며, kube-proxy 가 그 목록을 읽어 라우팅 규칙을 만든다">
  <defs>
    <marker id="sv2-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">Service 는 IP 목록을 갖고 있지 않다 — 조건만 적혀 있다</text>

  <!-- 왼쪽: 선언 -->
  <text x="30" y="72" font-size="10" fill="var(--secondary,#888)">내가 쓴 것</text>
  <rect x="30" y="82" width="170" height="56" rx="5" fill="none" stroke="#2e9c6d" stroke-width="1.8"/>
  <text x="115" y="104" text-anchor="middle" font-size="10" font-weight="600" fill="#2e9c6d">Service</text>
  <text x="115" y="122" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">selector: app=backend</text>

  <!-- 아래: Pod 들 -->
  <text x="30" y="212" font-size="10" fill="var(--secondary,#888)">실제로 떠 있는 것</text>
  <rect x="30" y="222" width="80" height="34" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="70" y="243" text-anchor="middle" font-size="8.5" fill="#5a2050">app=backend</text>
  <rect x="120" y="222" width="80" height="34" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="160" y="243" text-anchor="middle" font-size="8.5" fill="#5a2050">app=backend</text>
  <rect x="210" y="222" width="80" height="34" rx="4" fill="none" stroke="#c0392b" stroke-width="1.1" stroke-dasharray="4 3"/>
  <text x="250" y="243" text-anchor="middle" font-size="8.5" fill="#c0392b">app=other</text>

  <!-- 컨트롤러 -->
  <rect x="290" y="82" width="150" height="56" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="365" y="104" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">컨트롤러</text>
  <text x="365" y="122" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">조건에 맞는 Pod 를 찾는다</text>

  <!-- EndpointSlice -->
  <rect x="290" y="180" width="150" height="56" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="365" y="202" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">EndpointSlice</text>
  <text x="365" y="220" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">10.1.3.7 · 10.1.8.2</text>

  <!-- kube-proxy -->
  <rect x="530" y="180" width="150" height="56" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="605" y="202" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">kube-proxy</text>
  <text x="605" y="220" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">노드마다 라우팅 규칙</text>

  <!-- 흐름 -->
  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#sv2-ar)">
    <path d="M200,110 H286"/>
    <path d="M200,239 H286"/>
    <path d="M365,138 V176"/>
    <path d="M440,208 H526"/>
  </g>

  <text x="243" y="102" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">① 조건을 읽고</text>
  <text x="243" y="232" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">② 맞는 Pod 를 골라</text>
  <text x="378" y="162" font-size="9" fill="var(--secondary,#888)">③ 목록을 채운다</text>
  <text x="483" y="200" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">④ 읽는다</text>

  <text x="605" y="276" text-anchor="middle" font-size="9.5" fill="var(--secondary,#888)">Pod 가 늘거나 죽으면 ②③ 이 자동으로 다시 돈다</text>
  <text x="380" y="306" text-anchor="middle" font-size="12" fill="var(--content,#333)">조건을 적어두면 목록은 컨트롤러가 계속 맞춰 준다</text>
</svg>
</div>
{{< /rawhtml >}}

`port` 와 `targetPort` 가 다를 수 있다는 점이 자주 걸린다. 앞은 부르는 쪽이 쓰는 번호, 뒤는 컨테이너가 실제로 듣는 번호다.

## 4. Headless Service

`clusterIP: None` 을 주면 **가상 IP 를 만들지 않는다.** DNS 를 물으면 Service IP 하나가 아니라 **Pod IP 들이 그대로** 돌아온다.

```
일반 Service      backend  →  10.96.0.12          (하나. 뒤에서 분배)
Headless Service  backend  →  10.1.3.7, 10.1.8.2  (전부. 직접 고른다)
```

부하 분산을 포기하는 대신 **개별 Pod 를 지목할 수 있게** 된다. StatefulSet 과 함께 쓰이는 이유다 — 데이터베이스 복제본에서 "0번이 리더"처럼 특정 Pod 를 찍어야 하는 경우가 있다.

## 5. 타입 선택

```
클러스터 안에서만 쓴다              → ClusterIP
개발 중 잠깐 밖에서 확인한다         → NodePort
운영 환경에서 외부에 연다            → LoadBalancer (또는 Ingress)
Pod 를 개별로 지목해야 한다          → Headless
외부 주소에 클러스터 안 이름을 붙인다  → ExternalName
```

HTTP 서비스를 여러 개 외부에 연다면 LoadBalancer 를 서비스마다 만드는 것보다 **Ingress** 가 낫다. LoadBalancer 는 클라우드에서 개당 과금되므로, 하나의 진입점에서 경로로 나누는 편이 저렴하고 관리하기 쉽다.

## 6. 관련 문서

- **Label / Selector** — Service 가 Pod 를 고르는 방법 *(예정)*
- **StatefulSet** — Headless Service 와 함께 쓰이는 워크로드 *(예정)*
- **Ingress** — HTTP 경로 기반 외부 노출 *(예정)*

## 7. 출처

정의, 타입별 동작, 계층 관계, EndpointSlice 갱신은 공식 문서 "Service" 에 근거한다.

> "In Kubernetes, a Service is a method for exposing a network application that is running as one or more Pods in your cluster."

> "**NodePort**: Exposes the Service on each Node's IP at a static port (the NodePort). A ClusterIP Service, to which the NodePort Service routes, is automatically created."

> "**LoadBalancer**: Exposes the Service externally using a cloud provider's load balancer. NodePort and ClusterIP Services, to which the external load balancer routes, are automatically created."

> "The controller for that Service continuously scans for Pods that match its selector, and then makes any necessary updates to the set of EndpointSlices for the Service."

- [Kubernetes — Service](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes — EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
