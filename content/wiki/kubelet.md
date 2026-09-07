---
title: "kubelet"
summary: "모든 노드에서 도는 에이전트. PodSpec 을 받아 그대로 만들어 놓고, 그 상태를 계속 유지한다."
categories: ["쿠버네티스", "아키텍처"]
tags: ["kubernetes", "node", "architecture"]
aliases_search: ["큐블릿", "쿠블렛", "노드 에이전트", "node agent", "static pod", "스태틱 파드"]
---

## 1. 개요

**kubelet**은 클러스터의 모든 노드에서 도는 에이전트다. 공식 문서의 정의는 짧다 — "Pod 안의 컨테이너가 실행되고 있는지 확인하는" 것.

받는 것은 **PodSpec**(Pod 를 서술한 YAML/JSON)이고, 하는 일은 거기 적힌 대로 컨테이너를 띄우고 그 상태를 유지하는 것이다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 280" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="kubelet 은 API 서버에서 PodSpec 을 받아 컨테이너 런타임에 실행을 요청하고, 노드와 Pod 상태를 API 서버에 보고한다">
  <defs>
    <marker id="kl-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">컨트롤 플레인은 "무엇을" 정하고, kubelet 은 "실제로" 만든다</text>

  <rect x="40" y="96" width="150" height="56" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="115" y="118" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2f6ea8">API 서버</text>
  <text x="115" y="135" text-anchor="middle" font-size="9" fill="#2f6ea8" opacity=".85">이 노드에 뜰 Pod 목록</text>

  <rect x="290" y="60" width="180" height="130" rx="6" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="380" y="84" text-anchor="middle" font-size="11" font-weight="600" fill="#2e9c6d">kubelet</text>
  <text x="380" y="106" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">PodSpec 을 받아</text>
  <text x="380" y="122" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">컨테이너를 띄우고</text>
  <text x="380" y="138" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">헬스 체크하고</text>
  <text x="380" y="154" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">상태를 보고한다</text>
  <text x="380" y="176" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">노드마다 하나</text>

  <rect x="570" y="60" width="150" height="50" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="645" y="80" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">컨테이너 런타임</text>
  <text x="645" y="96" text-anchor="middle" font-size="9" fill="#2f6ea8" opacity=".85">containerd 등</text>

  <rect x="570" y="140" width="150" height="50" rx="5" fill="#e6b3d9" stroke="#a05590"/>
  <text x="645" y="170" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#kl-ar)">
    <path d="M190,112 H286"/>
    <path d="M470,86 H566"/>
    <path d="M645,110 V136"/>
  </g>
  <path d="M286,140 H194" stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#kl-ar)"/>

  <text x="238" y="104" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">PodSpec</text>
  <text x="238" y="158" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">상태 보고</text>
  <text x="518" y="78" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">CRI 로 요청</text>

  <text x="380" y="240" text-anchor="middle" font-size="10" fill="var(--secondary,#888)">kubelet 은 컨테이너를 직접 만들지 않는다 — 런타임에 시킨다</text>
  <text x="380" y="266" text-anchor="middle" font-size="12" fill="var(--content,#333)">노드에서 실제로 일하는 것은 kubelet 하나뿐이다</text>
</svg>
</div>
{{< /rawhtml >}}

## 2. PodSpec

kubelet 이 받는 **PodSpec** 은 Pod 매니페스트의 `spec:` 부분이다. "이 Pod 가 어떻게 생겨야 하는가"를 적은 명세서다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web
spec:                        # ← 여기서부터가 PodSpec
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
  restartPolicy: Always
  volumes:
  - name: data
    emptyDir: {}
```

"Pod" 가 아니라 굳이 "PodSpec" 이라고 하는 이유는, Pod 객체 안에서 kubelet 이 쓰는 부분이 정해져 있기 때문이다.

| 부분 | 내용 | kubelet 은 |
|---|---|---|
| `metadata` | 이름 · 라벨 · 네임스페이스 | 참고만 한다 |
| `spec` | **어떻게 만들지** | **읽고 실행한다** |
| `status` | 지금 어떤 상태인지 | **써서 보고한다** |

`spec` 을 읽어 만들고, 결과를 `status` 에 쓴다. 원하는 상태와 실제 상태가 다른 칸에 있다는 이 구조가 7절 조정 루프의 전제다.

Deployment 를 쓸 때도 PodSpec 은 그 안에 있다. `spec` 이 **두 번** 나오는데, 바깥은 Deployment 의 것이고 `template` 안의 것이 PodSpec 이다.

```yaml
kind: Deployment
spec:                 # ← Deployment 의 spec — 개수, 전략
  replicas: 3
  template:           # Pod 를 찍어낼 틀
    spec:             # ← PodSpec. 3개 Pod 가 전부 이걸로 만들어진다
      containers:
      - name: nginx
        image: nginx:1.25
```

두 층을 다른 주체가 읽는다.

```
Deployment.spec                 replicas: 3     → 컨트롤러가 본다
Deployment.spec.template.spec   containers …    → 복사되어 Pod 가 되고 → kubelet 이 본다
```

kubelet 은 **Deployment 파일 자체를 본 적이 없다.** 컨트롤러가 `template` 을 복사해 만든 Pod 객체만 받는다. 그래서 `replicas` 는 kubelet 입장에서 존재하지 않는 값이다.

## 3. 관리 범위

공식 문서가 한 문장으로 선을 긋는다.

> "The kubelet doesn't manage containers which **were not created by Kubernetes**."

같은 노드에서 `docker run` 으로 직접 띄운 컨테이너는 kubelet 이 모른다. 죽어도 되살리지 않고, 지표도 수집하지 않는다. **자기가 만든 것만** 돌본다.

## 4. PodSpec 의 세 가지 출처

대부분은 API 서버에서 오지만, 공식 문서는 셋을 나열한다.

| 출처 | 설명 | 갱신 주기 |
|---|---|---|
| **API 서버** | 일반적인 경로. 스케줄러가 배정한 Pod | watch — 즉시 |
| **파일** | 지정 디렉터리의 매니페스트를 읽는다 | 기본 20초 |
| **HTTP 엔드포인트** | 지정 URL 을 주기적으로 확인 | 기본 20초 |

뒤의 둘로 만들어진 Pod 를 **static Pod** 라고 한다. API 서버를 거치지 않으므로 **API 서버가 죽어 있어도 뜬다.**

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 250" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="일반 Pod 는 API 서버를 거쳐 kubelet 에 도달하지만 static Pod 는 노드의 파일에서 직접 읽히므로 API 서버 없이도 뜬다">
  <defs>
    <marker id="kl3-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">같은 kubelet 인데 PodSpec 이 오는 길이 둘이다</text>

  <!-- 일반 경로 -->
  <text x="30" y="80" font-size="10" fill="var(--secondary,#888)">일반 Pod</text>
  <rect x="120" y="60" width="130" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="185" y="80" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">kubectl apply</text>
  <text x="185" y="96" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">사용자 · 컨트롤러</text>
  <rect x="300" y="60" width="130" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="365" y="80" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">API 서버</text>
  <text x="365" y="96" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">etcd 에 저장 · 스케줄</text>

  <!-- static 경로 -->
  <text x="30" y="176" font-size="10" fill="var(--secondary,#888)">static Pod</text>
  <rect x="120" y="156" width="130" height="46" rx="5" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="185" y="176" text-anchor="middle" font-size="10" font-weight="600" fill="#c0392b">노드의 파일</text>
  <text x="185" y="192" text-anchor="middle" font-size="8.5" fill="#c0392b" opacity=".85">/etc/kubernetes/manifests/</text>
  <rect x="300" y="156" width="130" height="46" rx="5" fill="none" stroke="var(--secondary,#888)" stroke-width="1.1" stroke-dasharray="4 3"/>
  <text x="365" y="183" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">API 서버 안 거침</text>

  <!-- kubelet (합류점) -->
  <rect x="490" y="98" width="120" height="70" rx="6" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="550" y="128" text-anchor="middle" font-size="11" font-weight="600" fill="#2e9c6d">kubelet</text>
  <text x="550" y="146" text-anchor="middle" font-size="8.5" fill="#2e9c6d" opacity=".85">둘 다 똑같이 띄운다</text>

  <rect x="650" y="110" width="90" height="46" rx="5" fill="#e6b3d9" stroke="#a05590"/>
  <text x="695" y="137" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#kl3-ar)">
    <path d="M250,83 H296"/>
    <path d="M430,83 H460 V122 H486"/>
    <path d="M250,179 H460 V144 H486"/>
    <path d="M610,133 H646"/>
  </g>

  <text x="200" y="230" text-anchor="middle" font-size="9.5" fill="var(--secondary,#888)">API 서버 · etcd · 스케줄러 자신이 이 길로 뜬다 — 닭이 달걀보다 먼저</text>
</svg>
</div>
{{< /rawhtml >}}

컨트롤 플레인 자체가 이 방식으로 뜬다. `kube-apiserver`, `etcd`, `kube-scheduler` 가 보통 `/etc/kubernetes/manifests/` 안의 파일로 실행된다.

```
닭과 달걀 문제
  API 서버를 띄우려면 → 누가 띄우나?
  스케줄러가 배정해야 하는데 → 스케줄러도 아직 안 떴다

해결
  kubelet 이 파일을 직접 읽어 띄운다 → API 서버 없이도 시작 가능
```

## 5. 담당 범위

각 장에서 kubelet 이 나오는 대목을 모으면 담당 범위가 드러난다.

| 일 | 내용 |
|---|---|
| 컨테이너 실행 | CRI 로 런타임(containerd 등)에 요청 |
| 재시작 | 컨테이너가 죽으면 `restartPolicy` 에 따라 되살린다 |
| 헬스 체크 | [Probe](/wiki/probe/) 를 주기적으로 실행하고 결과에 따라 조치 |
| 볼륨 마운트 | PV·ConfigMap·Secret 을 컨테이너 파일시스템에 연결 |
| 토큰 발급 | ServiceAccount 토큰을 Pod 가 뜰 때 즉석 발급 (etcd 에 저장하지 않음) |
| 지표 수집 | 내장 cAdvisor 가 CPU·메모리 사용량을 측정 |
| 상태 보고 | 노드와 Pod 의 현재 상태를 API 서버에 계속 알린다 |

**ConfigMap 갱신**도 kubelet 의 일이다. 값이 바뀌면 새 폴더를 만들고 심볼릭 링크만 바꿔치기해서, 앱이 반쯤 바뀐 파일을 보는 일이 없게 한다.

## 6. 컨테이너 런타임과의 경계

"kubelet 이 컨테이너를 띄운다"는 말은 절반만 맞다. kubelet 은 **지시를 받는 쪽**이지, 컨테이너를 만드는 기술을 갖고 있지 않다.

컨테이너를 실제로 만드는 일은 리눅스 커널 기능(namespace, cgroup)을 조작하는 것이다. 이미지를 풀고, 격리된 공간을 만들고, 그 안에서 프로세스를 시작한다. 이걸 하는 별도 프로그램이 **컨테이너 런타임**이고, containerd 나 CRI-O 가 그것이다.

```
kubelet:      "nginx 이미지로 컨테이너 하나 띄워줘"        ← 요청만
containerd:   이미지 받고, 격리 공간 만들고, 프로세스 시작   ← 실제 작업
```

식당으로 치면 kubelet 은 매니저, 런타임은 주방이다. 매니저는 주문서(PodSpec)를 보고 "이거 만들어" 하고 넘길 뿐 칼을 잡지 않는다. 대신 나온 음식이 주문서와 맞는지 확인하고, 안 맞으면 다시 시킨다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 300" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="kubelet 은 CRI 규격으로 컨테이너 런타임에 요청하고, 런타임이 커널 기능을 써서 실제 컨테이너를 만든다. 런타임은 규격만 맞으면 교체할 수 있다">
  <defs>
    <marker id="kl4-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">규격(CRI)만 맞으면 주방은 갈아끼울 수 있다</text>

  <rect x="40" y="90" width="150" height="70" rx="6" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="115" y="116" text-anchor="middle" font-size="11" font-weight="600" fill="#2e9c6d">kubelet</text>
  <text x="115" y="134" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">매니저 — 주문만 넘긴다</text>
  <text x="115" y="148" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">칼은 안 잡는다</text>

  <line x1="290" y1="60" x2="290" y2="230" stroke="#2f6ea8" stroke-width="1.2" stroke-dasharray="5 4"/>
  <text x="290" y="50" text-anchor="middle" font-size="9.5" font-weight="600" fill="#2f6ea8">CRI</text>
  <text x="290" y="246" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".8">주문 규격</text>

  <rect x="380" y="58" width="150" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="455" y="78" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">containerd</text>
  <text x="455" y="94" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">요즘 기본</text>

  <rect x="380" y="122" width="150" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="455" y="142" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">CRI-O</text>
  <text x="455" y="158" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">Red Hat 계열</text>

  <rect x="380" y="186" width="150" height="46" rx="5" fill="none" stroke="#c0392b" stroke-width="1.1" stroke-dasharray="4 3"/>
  <text x="455" y="206" text-anchor="middle" font-size="10" fill="#c0392b">Docker (dockershim)</text>
  <text x="455" y="222" text-anchor="middle" font-size="8.5" fill="#c0392b" opacity=".85">1.24 에서 제거</text>

  <rect x="620" y="90" width="110" height="70" rx="5" fill="#e6b3d9" stroke="#a05590"/>
  <text x="675" y="118" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>
  <text x="675" y="136" text-anchor="middle" font-size="8.5" fill="#5a2050" opacity=".85">namespace · cgroup</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#kl4-ar)">
    <path d="M190,125 H260 V81 H376"/>
    <path d="M260,125 H376"/>
    <path d="M530,81 H580 V125 H616"/>
    <path d="M530,145 H580 V125 H616"/>
  </g>

  <text x="225" y="117" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">요청</text>
  <text x="575" y="112" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">실제 생성</text>

  <text x="380" y="282" text-anchor="middle" font-size="12" fill="var(--content,#333)">주방을 바꿔도 매니저는 그대로다 — Docker 가 빠질 때 kubelet 은 손대지 않았다</text>
</svg>
</div>
{{< /rawhtml >}}

매니저와 주방 사이의 주문 규격이 **CRI**(Container Runtime Interface)다. 이 규격만 지키면 어떤 런타임이든 붙일 수 있다.

### 6.1. Docker 지원 종료의 실체

1.24 에서 "Docker 지원이 빠진다"고 했을 때 소란이 있었지만, 실제로 빠진 것은 **kubelet 과 Docker 사이의 어댑터(dockershim)** 하나였다. Docker 는 CRI 를 직접 말하지 못해서 중간에 통역이 필요했는데, 그 통역을 kubelet 안에 넣어두던 것을 뺀 것이다.

```
전:  kubelet ─(dockershim)─▶ Docker ─▶ containerd ─▶ 컨테이너
후:  kubelet ─────CRI──────▶ containerd ─▶ 컨테이너
```

Docker 자체가 내부에서 containerd 를 쓰고 있었으니, 가운데 층을 걷어내고 바로 붙인 셈이다. kubelet 코드는 그대로였고, 노드의 런타임 설정만 바꾸면 됐다.

### 6.2. 노드에서 확인하기

노드에 들어가 `docker ps` 를 쳤는데 아무것도 안 나오면서 Pod 는 잘 돌고 있다면, 런타임이 containerd 인 것이다. kubelet 은 Docker 명령어를 모르며 알 필요도 없다.

```bash
crictl ps          # CRI 규격으로 런타임에 직접 묻는다 — 어느 런타임이든 동작
crictl images
```

`crictl` 은 CRI 를 말하는 도구라 런타임이 뭐든 같은 명령으로 볼 수 있다.

## 7. 조정 루프

kubelet 은 컨테이너를 **한 번 띄우고 끝내지 않는다.** PodSpec 이 말하는 상태와 실제 상태를 계속 비교해서 어긋나면 맞춘다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 290" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="kubelet 은 PodSpec 이 요구하는 상태와 노드의 실제 상태를 반복해서 비교하고, 차이가 있으면 컨테이너를 띄우거나 재시작해 맞춘다">
  <defs>
    <marker id="kl2-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">"띄운다"가 아니라 "맞춘다" — 그래서 죽어도 되살아난다</text>

  <rect x="40" y="70" width="170" height="60" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="125" y="92" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">원하는 상태</text>
  <text x="125" y="110" text-anchor="middle" font-size="9" fill="#2f6ea8" opacity=".85">PodSpec: 컨테이너 2개</text>

  <rect x="40" y="180" width="170" height="60" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="125" y="202" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">실제 상태</text>
  <text x="125" y="220" text-anchor="middle" font-size="9" fill="#2f6ea8" opacity=".85">런타임에 물어봄: 1개 실행 중</text>

  <rect x="300" y="120" width="160" height="70" rx="6" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="380" y="146" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2e9c6d">비교</text>
  <text x="380" y="166" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">하나 모자란다</text>

  <rect x="550" y="120" width="170" height="70" rx="5" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="635" y="146" text-anchor="middle" font-size="10" font-weight="600" fill="#c0392b">조치</text>
  <text x="635" y="166" text-anchor="middle" font-size="9" fill="#c0392b" opacity=".85">죽은 컨테이너 재시작</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#kl2-ar)">
    <path d="M210,100 H256 V148 H296"/>
    <path d="M210,210 H256 V162 H296"/>
    <path d="M460,155 H546"/>
  </g>
  <path d="M635,190 V250 H125 V244" stroke="#2e9c6d" stroke-width="1.6" fill="none" stroke-dasharray="5 4" marker-end="url(#kl2-ar)"/>

  <text x="380" y="266" text-anchor="middle" font-size="9.5" fill="var(--secondary,#888)">조치 후 실제 상태가 바뀌고 → 다시 비교 → 같아질 때까지 반복</text>
</svg>
</div>
{{< /rawhtml >}}

컨테이너가 죽으면 "1개 실행 중 ≠ 2개 요구" 라는 차이가 생기고, kubelet 이 그걸 메운다. 이 루프가 `restartPolicy` 의 실체다. Probe 실패 시 재시작하는 것도 같은 루프다 — "건강하지 않은 컨테이너"를 "없는 것"으로 치고 다시 만든다.

### 7.1. 컨트롤러의 루프와 다른 점

Deployment 의 `replicas: 3` 을 맞추는 것은 **kubelet 이 아니다.** 같은 "비교해서 맞춘다" 구조지만 보는 대상이 다르다.

| | 컨트롤러 (ReplicaSet) | kubelet |
|---|---|---|
| 보는 것 | 클러스터 전체의 **Pod 개수** | 내 노드에 배정된 **Pod 안의 컨테이너** |
| 어긋남 | "3개여야 하는데 2개" | "컨테이너 2개여야 하는데 1개 죽음" |
| 조치 | Pod 객체를 새로 만든다 | 그 Pod 의 컨테이너를 재시작한다 |
| 어디서 | 컨트롤 플레인 | 각 노드 |

PodSpec 에는 "Pod 몇 개"가 없다. 그건 Deployment 의 `replicas` 이고 컨트롤러가 본다. kubelet 은 자기한테 온 Pod 하나하나의 **안쪽**만 맞춘다.

```
컨테이너가 죽음       → kubelet 이 재시작 (Pod 는 그대로, RESTARTS 만 올라감)
노드가 통째로 죽음     → kubelet 도 같이 죽었으니 손쓸 수 없음
                     → 컨트롤러가 "개수 부족"을 보고 다른 노드에 새 Pod
kubectl delete pod   → 컨트롤러가 새로 만듦. kubelet 은 사라진 것을 정리만
```

두 루프가 층을 나눠 맡기 때문에, 노드 하나가 죽어도 서비스가 유지된다.

## 8. 장애 시 동작

kubelet 이 멈춰도 **이미 돌던 컨테이너는 계속 돈다.** 런타임이 실행 주체이기 때문이다. 다만 아무도 돌보지 않는 상태가 된다.

| | kubelet 이 살아 있을 때 | 죽었을 때 |
|---|---|---|
| 기존 컨테이너 | 계속 실행 | 계속 실행 (돌봄 없음) |
| 컨테이너가 죽으면 | 재시작 | 그대로 방치 |
| 새 Pod 배정 | 실행 | 아무 일도 안 일어남 |
| 노드 상태 | Ready | `NotReady` → 일정 시간 후 Pod 재배치 |

컨트롤 플레인은 노드가 보고를 멈추면 `NotReady` 로 표시하고, 시간이 지나면 그 노드의 Pod 를 다른 노드로 옮긴다.

## 9. 관련 문서

- [Probe](/wiki/probe/) — kubelet 이 실행하는 헬스 체크
- [PersistentVolume / PVC](/wiki/persistent-volume/) — kubelet 이 마운트한다
- [etcd](/wiki/etcd/) — kubelet 은 여기에 직접 접근하지 않는다
- **CRI** — 컨테이너 런타임 인터페이스 *(예정)*

## 10. 출처

정의, PodSpec 출처, 관리 범위는 공식 문서에 근거한다.

> "An agent that runs on each node in the cluster. It makes sure that containers are running in a Pod."

> "The kubelet takes a set of PodSpecs that are provided through various mechanisms and ensures that the containers described in those PodSpecs are running and healthy. The kubelet doesn't manage containers which were not created by Kubernetes."

> "Other than from a PodSpec from the apiserver, there are two ways that a container manifest can be provided to the Kubelet. **File**: Path passed as a flag on the command line. … **HTTP endpoint**: HTTP endpoint passed as a parameter on the command line."

- [Kubernetes — Cluster Architecture](https://kubernetes.io/docs/concepts/architecture/)
- [Kubernetes — kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)
- [Kubernetes — Static Pods](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/)
