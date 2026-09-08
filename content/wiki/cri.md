---
title: "CRI / containerd"
summary: "kubelet 과 컨테이너 런타임 사이의 규격(CRI)과, 그 규격을 구현한 대표 런타임(containerd). 실제 컨테이너는 그 아래 runc 가 만든다."
categories: ["쿠버네티스", "아키텍처"]
tags: ["kubernetes", "node", "runtime", "containerd"]
aliases_search: ["containerd", "컨테이너디", "컨테이너 런타임", "container runtime", "runc", "런씨", "OCI", "cri-o", "dockershim", "도커심", "cgroup driver"]
---

## 1. 개요

**CRI**(Container Runtime Interface)는 kubelet 이 컨테이너 런타임에 말을 거는 규격이고, **containerd** 는 그 규격을 구현한 런타임 중 사실상 표준이다.

kubelet 은 컨테이너를 직접 만들지 못한다. 만드는 기술은 런타임에 있고, 그 런타임도 마지막 한 걸음은 더 아래 층(runc)에 맡긴다. 그래서 "컨테이너를 띄운다"는 한 문장 뒤에 **층이 셋** 있다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 400" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="kubelet 이 CRI 로 containerd 에 요청하고, containerd 가 OCI 런타임 규격으로 runc 를 호출하며, runc 가 리눅스 커널 기능으로 실제 컨테이너를 만드는 세 층 구조">
  <defs>
    <marker id="cr-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">위에서 아래로 "시켜라"가 내려가고, 규격이 층 사이를 나눈다</text>

  <!-- kubelet -->
  <text x="60" y="80" font-size="10" fill="var(--secondary,#888)">매니저</text>
  <rect x="280" y="50" width="200" height="50" rx="6" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="380" y="72" text-anchor="middle" font-size="11" font-weight="600" fill="#2e9c6d">kubelet</text>
  <text x="380" y="89" text-anchor="middle" font-size="8.5" fill="#2e9c6d" opacity=".85">PodSpec 대로 "띄워줘"</text>

  <!-- CRI 경계 -->
  <line x1="200" y1="126" x2="560" y2="126" stroke="#2f6ea8" stroke-width="1.2" stroke-dasharray="5 4"/>
  <text x="572" y="122" font-size="9.5" font-weight="600" fill="#2f6ea8">CRI</text>
  <text x="572" y="135" font-size="8.5" fill="#2f6ea8" opacity=".85">gRPC · unix socket</text>

  <!-- containerd -->
  <text x="60" y="180" font-size="10" fill="var(--secondary,#888)">주방 데몬</text>
  <rect x="280" y="150" width="200" height="50" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="380" y="172" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">containerd</text>
  <text x="380" y="189" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">이미지 받기 · 수명주기 · 감시</text>

  <!-- OCI 경계 -->
  <line x1="200" y1="226" x2="560" y2="226" stroke="#2f6ea8" stroke-width="1.2" stroke-dasharray="5 4"/>
  <text x="572" y="222" font-size="9.5" font-weight="600" fill="#2f6ea8">OCI runtime spec</text>
  <text x="572" y="235" font-size="8.5" fill="#2f6ea8" opacity=".85">번들 디렉터리 하나</text>

  <!-- runc -->
  <text x="60" y="280" font-size="10" fill="var(--secondary,#888)">실제 손</text>
  <rect x="280" y="250" width="200" height="50" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="380" y="272" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">runc</text>
  <text x="380" y="289" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">namespace · cgroup 설정 후 exec</text>

  <!-- 컨테이너 -->
  <text x="60" y="352" font-size="10" fill="var(--secondary,#888)">결과</text>
  <rect x="280" y="326" width="200" height="44" rx="5" fill="#e6b3d9" stroke="#a05590"/>
  <text x="380" y="353" text-anchor="middle" font-size="10.5" font-weight="600" fill="#5a2050">컨테이너 (프로세스)</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#cr-ar)">
    <path d="M380,100 V146"/>
    <path d="M380,200 V246"/>
    <path d="M380,300 V322"/>
  </g>

  <text x="380" y="392" text-anchor="middle" font-size="12" fill="var(--content,#333)">kubelet 도 containerd 도 컨테이너를 만들지 않는다 — 마지막 손은 runc 다</text>
</svg>
</div>
{{< /rawhtml >}}

kubelet 이 매니저라면 containerd 는 주방 데몬이고, 실제로 칼을 잡는 것은 그 밑의 runc 다. 각 층 사이에 **규격**이 있어서 층을 따로 갈아끼울 수 있다.

## 2. CRI

공식 문서의 정의는 이렇다 — "kubelet 과 컨테이너 런타임 사이 통신을 위한 주 **gRPC** 프로토콜". 목적도 명확하다. **클러스터 컴포넌트를 다시 컴파일하지 않고** 다양한 런타임을 쓸 수 있게 하는 플러그인 인터페이스다.

| 항목 | 내용 |
|---|---|
| 프로토콜 | gRPC |
| 연결 | 노드 안 unix socket — `--container-runtime-endpoint` 로 지정 |
| 누가 클라이언트인가 | **kubelet** 이 요청하고, 런타임이 응답한다 |
| 서비스 | RuntimeService (컨테이너·Pod 샌드박스 수명주기) · ImageService (이미지 받기·조회·삭제) |
| 버전 | 1.26 부터 `v1` API 필수. 미지원 런타임이면 **노드 등록 자체가 안 된다** |

```
kubelet ──gRPC──▶ /run/containerd/containerd.sock ──▶ containerd
         "RunPodSandbox"  "CreateContainer"  "PullImage" …
```

### 2.1. 오가는 것

두 서비스로 나뉘고, 각각 대표 호출이 있다.

| 서비스 | 다루는 것 | 대표 호출 |
|---|---|---|
| **ImageService** | 이미지 | `PullImage` `ImageStatus` `ListImages` `RemoveImage` |
| **RuntimeService** | 샌드박스 · 컨테이너 | `RunPodSandbox` `CreateContainer` `StartContainer` `StopContainer` `ListContainers` `ContainerStatus` `Exec` `Status` |

**방향은 한쪽이다.** kubelet 이 묻고 containerd 가 답한다. containerd 가 먼저 kubelet 에게 말을 거는 일은 없다 — 소켓을 열어 놓고 기다릴 뿐이다. Pod 하나가 뜨고 지는 동안 오가는 순서를 그리면 이렇다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 450" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="kubelet 과 containerd 사이의 CRI 호출 순서. 부팅 시 Version 과 Status 로 확인하고, PullImage, RunPodSandbox, CreateContainer, StartContainer 순으로 Pod 를 띄우며, 이후 ListContainers 로 주기적으로 상태를 묻고, 삭제 시 StopContainer 부터 RemovePodSandbox 까지 역순으로 내린다. 모든 요청은 kubelet 이 시작한다">
  <defs>
    <marker id="cr5-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">화살표는 전부 왼쪽에서 오른쪽 — containerd 는 먼저 말을 걸지 않는다</text>

  <!-- 참여자 -->
  <rect x="140" y="46" width="120" height="38" rx="5" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="200" y="70" text-anchor="middle" font-size="11" font-weight="600" fill="#2e9c6d">kubelet</text>
  <rect x="500" y="46" width="120" height="38" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="560" y="70" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">containerd</text>
  <line x1="200" y1="84" x2="200" y2="418" stroke="#2e9c6d" stroke-width="1" stroke-dasharray="3 3" opacity=".5"/>
  <line x1="560" y1="84" x2="560" y2="418" stroke="#2f6ea8" stroke-width="1" stroke-dasharray="3 3" opacity=".5"/>

  <!-- 호출 -->
  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#cr5-ar)">
    <path d="M204,116 H556"/>
    <path d="M204,160 H556"/>
    <path d="M204,204 H556"/>
    <path d="M204,248 H556"/>
    <path d="M204,292 H556"/>
    <path d="M204,350 H556"/>
    <path d="M204,394 H556"/>
  </g>
  <path d="M556,306 H204" stroke="#2f6ea8" stroke-width="1.2" stroke-dasharray="4 3" fill="none" marker-end="url(#cr5-ar)"/>

  <g font-size="10" font-weight="600" fill="var(--content,#333)" text-anchor="middle">
    <text x="380" y="110">Version · Status</text>
    <text x="380" y="154">PullImage</text>
    <text x="380" y="198">RunPodSandbox</text>
    <text x="380" y="242">CreateContainer → StartContainer</text>
    <text x="380" y="286">ListContainers · ContainerStatus</text>
    <text x="380" y="344">StopContainer → RemoveContainer</text>
    <text x="380" y="388">StopPodSandbox → RemovePodSandbox</text>
  </g>
  <g font-size="8.5" fill="var(--secondary,#888)" text-anchor="middle">
    <text x="380" y="128">"CRI v1 이니? 살아 있니?" — 부팅 때, 이후 주기적</text>
    <text x="380" y="172">ImageService — 없으면 받아 둔다</text>
    <text x="380" y="216">샌드박스 생성 → 여기서 shim 이 하나 뜬다</text>
    <text x="380" y="260">컨테이너마다 한 쌍</text>
    <text x="380" y="318">답: 지금 이런 것들이 돌고 있다</text>
    <text x="380" y="362">삭제 시 — 컨테이너부터</text>
    <text x="380" y="406">마지막에 샌드박스 → shim 도 내려간다</text>
  </g>

  <text x="380" y="438" text-anchor="middle" font-size="12" fill="var(--content,#333)">containerd 는 알려주지 않는다 — kubelet 이 계속 묻는다</text>
</svg>
</div>
{{< /rawhtml >}}

`kubectl exec` 도 이 통로다. kubelet 이 `Exec` 을 호출하면 containerd 가 스트리밍 주소를 돌려주고, kubelet 이 거기에 붙는다.

### 2.2. 상태를 아는 방법

containerd 가 알려주지 않으니 **kubelet 이 주기적으로 묻는다.** `ListPodSandbox` · `ListContainers` · `ContainerStatus` 를 돌려서 컨테이너가 죽었는지를 알아채고, 그래야 `restartPolicy` 를 돌릴 수 있다. 최근에는 `GetContainerEvents` 라는 **스트리밍 호출**이 추가되어 kubelet 이 한 번 붙어 두면 변화가 생길 때마다 이벤트를 받는 방식도 있다. 이 경우에도 연결을 여는 쪽은 kubelet 이다 — 방향은 여전히 한쪽이다.

CRI 는 규격일 뿐 프로그램이 아니다. `crictl` 이 이 규격으로 런타임에 직접 묻는 도구라서, 런타임이 뭐든 같은 명령으로 볼 수 있다.

## 3. containerd

containerd 의 자기 소개는 이렇다 — "단순성·견고성·이식성에 중점을 둔 업계 표준 컨테이너 런타임"이며, 호스트의 **컨테이너 수명주기 전체를 관리하는 데몬**이다.

맡는 범위가 README 에 나열되어 있다.

| 범위 | 하는 일 |
|---|---|
| 이미지 | 레지스트리에서 받아오고 저장한다 (OCI Distribution 규격) |
| 실행·감시 | 컨테이너를 시작하고, 죽었는지 지켜본다 |
| 저장소 | 레이어를 풀어 파일시스템(snapshot)을 만든다 |
| 네트워크 | 네트워크 네임스페이스를 붙인다 |

한 가지 성격이 중요하다.

> "containerd is designed to be **embedded into a larger system**, rather than being used directly by developers or end-users."

사람이 직접 쓰라고 만든 게 아니라 **쿠버네티스나 Docker 같은 상위 시스템에 박혀서** 도는 부품이다. 그래서 `docker` 같은 친절한 CLI 가 없고, 실무에서는 `crictl` 이나 `ctr` 로 들여다본다.

그리고 containerd 자신도 마지막 한 걸음은 남에게 맡긴다.

> "Most interactions with the Linux and Windows container feature sets are handled via **runc** and/or OS-specific libraries."

### 3.1. 안쪽 구조와 shim

containerd 가 "컨테이너를 띄운다"고 할 때 안에서 일어나는 순서다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 340" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="containerd 데몬이 레지스트리에서 이미지를 받아 snapshotter 로 rootfs 를 만들고, 컨테이너마다 shim 프로세스를 띄워 runc 에 OCI 번들을 넘긴다. runc 는 컨테이너를 만들고 빠지며 shim 이 남아 지켜본다">
  <defs>
    <marker id="cr3-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">데몬은 준비까지만 — 컨테이너 옆에 남는 것은 shim 이다</text>

  <!-- 레지스트리 -->
  <rect x="30" y="90" width="110" height="44" rx="5" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="85" y="110" text-anchor="middle" font-size="10" font-weight="600" fill="#c0392b">레지스트리</text>
  <text x="85" y="125" text-anchor="middle" font-size="8.5" fill="#c0392b" opacity=".85">OCI 이미지</text>

  <!-- containerd 데몬 -->
  <rect x="180" y="50" width="300" height="130" rx="6" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="330" y="70" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2f6ea8">containerd (데몬)</text>
  <rect x="200" y="90" width="120" height="44" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.2"/>
  <text x="260" y="110" text-anchor="middle" font-size="9.5" fill="#2f6ea8">이미지 받기 · 저장</text>
  <text x="260" y="125" text-anchor="middle" font-size="8" fill="#2f6ea8" opacity=".8">레이어 단위</text>
  <rect x="340" y="90" width="120" height="44" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.2"/>
  <text x="400" y="110" text-anchor="middle" font-size="9.5" fill="#2f6ea8">snapshotter</text>
  <text x="400" y="125" text-anchor="middle" font-size="8" fill="#2f6ea8" opacity=".8">레이어 → rootfs</text>
  <text x="330" y="164" text-anchor="middle" font-size="8.5" fill="var(--secondary,#888)">여기까지 하고 shim 을 띄운다</text>

  <!-- shim -->
  <rect x="520" y="88" width="120" height="48" rx="5" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="580" y="108" text-anchor="middle" font-size="10" font-weight="600" fill="#2e9c6d">containerd-shim</text>
  <text x="580" y="124" text-anchor="middle" font-size="8.5" fill="#2e9c6d" opacity=".85">Pod(샌드박스)마다 하나</text>

  <!-- runc -->
  <rect x="520" y="196" width="120" height="44" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="580" y="216" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">runc</text>
  <text x="580" y="231" text-anchor="middle" font-size="8.5" fill="#2f6ea8" opacity=".85">띄우고 빠진다</text>

  <!-- 컨테이너 -->
  <rect x="520" y="272" width="120" height="40" rx="5" fill="#e6b3d9" stroke="#a05590"/>
  <text x="580" y="297" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#cr3-ar)">
    <path d="M140,112 H196"/>
    <path d="M320,112 H336"/>
    <path d="M480,112 H516"/>
    <path d="M580,136 V192"/>
    <path d="M580,240 V268"/>
  </g>
  <text x="600" y="168" font-size="8.5" fill="var(--secondary,#888)">OCI 번들</text>
  <text x="600" y="180" font-size="8.5" fill="var(--secondary,#888)">rootfs + config.json</text>

  <!-- shim 이 컨테이너를 붙들고 있음 -->
  <path d="M644,112 H690 V292 H644" stroke="#2e9c6d" stroke-width="1.2" stroke-dasharray="4 3" fill="none" marker-end="url(#cr3-ar)"/>
  <text x="700" y="205" font-size="8.5" fill="#2e9c6d" opacity=".9">stdio · 종료</text>
  <text x="700" y="217" font-size="8.5" fill="#2e9c6d" opacity=".9">코드 붙들기</text>

  <text x="330" y="214" text-anchor="middle" font-size="9.5" fill="var(--secondary,#888)">containerd 가 재시작돼도 shim 과 컨테이너는 그대로 산다</text>
  <text x="380" y="330" text-anchor="middle" font-size="12" fill="var(--content,#333)">runc 는 만들고 사라지고, shim 이 남아 지켜본다 — 그래서 데몬 재시작이 컨테이너를 안 죽인다</text>
</svg>
</div>
{{< /rawhtml >}}

**shim** 이 이 구조의 요점이다. containerd 데몬이 직접 runc 를 부르는 게 아니라, Pod(샌드박스)마다 작은 프로세스(shim)를 하나 띄우고 그 shim 이 runc 를 부른다. 쿠버네티스에서는 같은 Pod 의 컨테이너들을 sandbox ID 로 묶어 한 shim 이 맡는다.

프로세스 트리로 보면 세 관계가 분명해진다.

```
PID 1 (init)
 ├─ containerd                 데몬
 └─ containerd-shim            containerd 가 만들었지만 자식이 아니다 (아래 설명)
     ├─ runc  (잠깐)           shim 의 자식. 컨테이너를 만들고 곧 종료한다
     └─ 컨테이너 프로세스        runc 가 만들고 떠나자 shim 에게 입양된다
```

**shim 은 containerd 의 자식이 아니다.** 만들기는 containerd 가 만들지만, 공식 문서의 `start` 절차대로 — containerd 가 실행한 프로세스는 "소켓을 듣는 **새 프로세스를 하나 만들고**, 그 주소를 containerd 에 돌려준 뒤, **종료**"한다. 부모가 사라진 진짜 shim 은 init 밑으로 옮겨가고, containerd 와의 부모-자식 관계는 그 순간 끊긴다. 그래서 containerd 를 재시작하거나 업그레이드해도 shim 이 함께 죽지 않는다.

**runc 는 shim 의 자식이고, 컨테이너는 shim 의 양자다.** shim 이 runc 를 실행하면 runc 가 namespace 와 cgroup 을 만들어 컨테이너 프로세스를 띄운 뒤 자기는 종료한다. 부모(runc)를 잃은 컨테이너 프로세스는 원래 PID 1 에게 가야 하지만, shim 이 자신을 **sub-reaper** 로 등록해 두었기 때문에 shim 에게 입양된다. 그 덕에 shim 이 부모 자격으로 종료 코드를 회수하고 표준 입출력을 붙들 수 있다.

셋의 수명은 다르다. shim 은 컨테이너 하나가 아니라 **Pod 하나의 수명**을 따라간다.

| | 태어날 때 | 죽을 때 |
|---|---|---|
| containerd | 노드 부팅 시 systemd 가 띄운다 — kubelet 보다 **먼저** 있어야 노드가 등록된다 | 노드 종료·업그레이드 시. **재시작해도 shim 과 컨테이너는 그대로 산다** |
| shim | Pod 샌드박스 생성 시 — 첫 컨테이너보다 **먼저** | Pod 삭제 후 containerd 가 shutdown 을 요청할 때 — 마지막 컨테이너보다 **나중** |
| runc | shim 이 컨테이너를 만들 때마다 잠깐 | 컨테이너 프로세스를 띄우자마자 |
| 컨테이너 | runc 가 만들 때 | 프로세스가 끝날 때 → shim 이 종료 코드 회수 |

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 390" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="시간축 위에 containerd, shim, runc, 컨테이너 A, 컨테이너 B 의 수명을 나란히 그린 타임라인. containerd 가 재시작하는 동안에도 shim 과 컨테이너는 끊기지 않는다">
  <defs>
    <marker id="cr4-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">왼쪽에서 오른쪽으로 시간이 흐른다 — 막대 길이가 살아 있는 기간</text>

  <path d="M170,44 H556" stroke="#2e9c6d" stroke-width="1.4" fill="none" marker-end="url(#cr4-ar)"/>
  <text x="170" y="40" font-size="8.5" fill="#2e9c6d" opacity=".85">시간</text>

  <!-- containerd -->
  <text x="26" y="78" font-size="11.5" font-weight="600" fill="#2f6ea8">containerd</text>
  <text x="26" y="92" font-size="9.5" fill="var(--secondary,#888)">데몬 · 노드마다 하나</text>
  <rect x="170" y="62" width="176" height="28" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="364" y="81" text-anchor="middle" font-size="10" fill="#c0392b">✕</text>
  <text x="364" y="58" text-anchor="middle" font-size="8" fill="#c0392b">업그레이드</text>
  <rect x="382" y="62" width="178" height="28" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="580" y="80" font-size="10.5" fill="var(--content,#333)">노드가 켜진 동안 — <tspan font-weight="600">쉬어도 아래는 그대로</tspan></text>
  <line x1="26" y1="106" x2="734" y2="106" stroke="var(--content,#333)" stroke-width="1" opacity=".1"/>

  <!-- shim -->
  <text x="26" y="138" font-size="11.5" font-weight="600" fill="#2e9c6d">shim</text>
  <text x="26" y="152" font-size="9.5" fill="var(--secondary,#888)">Pod 마다 하나</text>
  <rect x="170" y="122" width="390" height="28" rx="4" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="365" y="140" text-anchor="middle" font-size="9" fill="#2e9c6d" opacity=".85">위가 쉬는 동안에도 끊기지 않는다</text>
  <line x1="560" y1="116" x2="560" y2="156" stroke="#2e9c6d" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="580" y="140" font-size="10.5" fill="var(--content,#333)">먼저 태어나 <tspan font-weight="600">나중에</tspan> 죽는다</text>
  <line x1="26" y1="166" x2="734" y2="166" stroke="var(--content,#333)" stroke-width="1" opacity=".1"/>

  <!-- runc -->
  <text x="26" y="198" font-size="11.5" font-weight="600" fill="#2f6ea8">runc</text>
  <text x="26" y="212" font-size="9.5" fill="var(--secondary,#888)">CLI</text>
  <rect x="186" y="182" width="26" height="28" rx="3" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <rect x="304" y="182" width="26" height="28" rx="3" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <rect x="404" y="182" width="26" height="28" rx="3" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="580" y="200" font-size="10.5" fill="var(--content,#333)">만들 때만 <tspan font-weight="600">잠깐</tspan></text>
  <line x1="26" y1="226" x2="734" y2="226" stroke="var(--content,#333)" stroke-width="1" opacity=".1"/>

  <!-- 컨테이너 A -->
  <text x="26" y="258" font-size="11.5" font-weight="600" fill="#a05590">컨테이너 A</text>
  <text x="26" y="272" font-size="9.5" fill="var(--secondary,#888)">앱</text>
  <rect x="212" y="242" width="84" height="28" rx="4" fill="none" stroke="#a05590" stroke-width="1.5"/>
  <text x="313" y="261" text-anchor="middle" font-size="10" fill="#c0392b">✕</text>
  <rect x="330" y="242" width="100" height="28" rx="4" fill="none" stroke="#a05590" stroke-width="1.5"/>
  <text x="580" y="260" font-size="10.5" fill="var(--content,#333)">재시작돼도 <tspan font-weight="600">같은 shim</tspan> 아래</text>
  <line x1="26" y1="286" x2="734" y2="286" stroke="var(--content,#333)" stroke-width="1" opacity=".1"/>

  <!-- 컨테이너 B -->
  <text x="26" y="318" font-size="11.5" font-weight="600" fill="#a05590">컨테이너 B</text>
  <text x="26" y="332" font-size="9.5" fill="var(--secondary,#888)">사이드카</text>
  <rect x="430" y="302" width="124" height="28" rx="4" fill="none" stroke="#a05590" stroke-width="1.5"/>
  <text x="580" y="320" font-size="10.5" fill="var(--content,#333)">사이드카도 <tspan font-weight="600">같은 shim</tspan></text>

  <text x="380" y="378" text-anchor="middle" font-size="12" fill="var(--content,#333)">노드 ⊇ Pod ⊇ 프로세스 — 각 층이 아래층을 죽이지 않도록 끊어 두었다</text>
</svg>
</div>
{{< /rawhtml >}}

containerd 는 노드 부팅 때 systemd 가 띄우는 데몬이라 어느 Pod 와도 수명이 묶이지 않는다. 업그레이드로 잠깐 내려가도 shim 과 컨테이너는 계속 돌고, 그 사이 kubelet 이 새 컨테이너를 만들거나 지우지 못할 뿐이다. 다시 뜬 containerd 는 살아 있는 shim 들의 소켓에 재접속해 상태를 복구한다.

그래서 kubelet 이 `restartPolicy` 로 컨테이너를 되살릴 때 shim 은 그대로이고 runc 만 한 번 더 불린다. 컨테이너가 죽어도 shim 은 바로 사라지지 않고 종료 코드를 들고 containerd 가 가져갈 때까지 기다린다 — containerd 가 마침 재시작 중이어도 그 값이 안 없어지는 이유다.

이렇게 나눈 이유는 **데몬과 컨테이너의 수명을 떼어놓기 위해서**다. kubelet 이 죽어도 컨테이너가 도는 것과 같은 설계가 한 층 아래에서 반복된다.

### 3.2. 데몬의 수명

shim 에게 던진 세 질문을 containerd 자신에게도 던져 본다. 먼저 이 문서에 나온 모든 층에 대해 **누가 누구를 만드는지**를 한 번에 세워 두면 답이 절반은 나온다.

```
systemd     ─만든다─▶  containerd         노드 부팅 때 (서비스)
systemd     ─만든다─▶  kubelet            노드 부팅 때 (서비스)

kubelet     ─시킨다─▶  containerd         "이 Pod 샌드박스 만들어줘"  (CRI)
containerd  ─만든다─▶  shim               Pod 마다 하나. 띄우고 손을 뗀다
shim        ─만든다─▶  runc               컨테이너마다 잠깐 (자식)
runc        ─만든다─▶  컨테이너 프로세스    만들고 exit → shim 이 입양
```

kubelet 은 이 줄에서 유일하게 **아무것도 직접 만들지 않는다.** 시킬 뿐이다. 그리고 containerd 와 kubelet 은 서로를 만들지 않는 형제다 — 둘 다 systemd 가 띄우고, 순서만 `containerd → kubelet` 이다.

**누가 만드나 — 쿠버네티스가 아니다.** containerd 는 쿠버네티스 아래에 있는 노드 소프트웨어다. 노드에 패키지로 설치되고(관리형 클러스터면 노드 이미지에 미리 들어 있다) **systemd 가 부팅 때 `containerd.service` 로 띄운다.** kubelet 은 만들지 않고 붙기만 한다 — 소켓 `/run/containerd/containerd.sock` 에 연결해 `v1` API 를 확인하고, 없으면 노드 등록을 하지 않는다. 그래서 노드의 부팅 순서는 `containerd → kubelet` 이다.

**몇 개인가 — 노드당 하나.** Pod 당도 컨테이너당도 아니다. 노드가 50개면 containerd 프로세스가 50개이고, 각각 자기 노드의 모든 Pod 를 맡는다. 데몬은 하나인데 그 아래 shim 은 Pod 수만큼 있는 구조다.

**어떻게 죽나 — 노드와 함께, 또는 관리자 손에.**

| 상황 | 무슨 일 | 그 사이 컨테이너는 |
|---|---|---|
| `systemctl restart containerd` — 업그레이드 · 설정 변경 | SIGTERM 을 받고 정리 후 종료, systemd 가 다시 띄운다 | 그대로 돈다 |
| 크래시 | systemd 의 `Restart=always` 가 자동 복구 | 그대로 돈다 |
| 노드 종료 · 재부팅 | 노드와 함께 죽는다 | 노드와 함께 죽는다 |

죽어 있는 동안 노드에서 벌어지는 일은 kubelet 이 죽었을 때와 닮았다.

```
돌던 컨테이너      계속 실행 — shim 이 붙들고 있다
새 컨테이너 생성    불가 — kubelet 의 CRI 호출이 실패한다
컨테이너 삭제      불가
노드 상태          오래 가면 kubelet 이 런타임 불량을 보고 → NotReady
```

다시 뜨면 `/run/containerd` 아래 남은 상태로 살아 있는 shim 소켓들을 찾아 재접속하고, 어떤 컨테이너가 돌고 있는지를 shim 에게 물어 복구한다. 그래서 짧은 재시작은 사용자가 눈치채지 못한다. 위 타임라인의 `✕ 업그레이드` 구간이 바로 이 장면이다.

## 4. OCI 와 runc

**OCI**(Open Container Initiative)는 컨테이너의 두 가지를 규격화한 단체다.

| 규격 | 정하는 것 | 덕분에 |
|---|---|---|
| Image spec | 이미지 파일 구조 | Docker 로 빌드한 이미지가 containerd 에서 그대로 돈다 |
| Runtime spec | "이 번들을 컨테이너로 띄워라"의 형식 | runc 자리에 다른 구현(gVisor, Kata)을 끼울 수 있다 |

**runc** 는 Runtime spec 의 기준 구현이다. README 의 정의 한 줄이 전부다.

> "runc is a CLI tool for spawning and running containers on Linux according to the OCI specification."

containerd 가 이미지를 풀어 번들 디렉터리를 만들어 놓으면, runc 가 그것을 받아 리눅스 커널에 namespace 와 cgroup 을 설정하고 프로세스를 실행한다. **그 순간 컨테이너가 생긴다.** runc 는 데몬이 아니라 그때그때 불려서 일하고 빠지는 CLI 다.

```
containerd:  이미지 레이어 풀기 → rootfs + config.json (OCI 번들)
runc:        번들 읽기 → namespace/cgroup 만들기 → 프로세스 exec → 종료
```

## 5. 런타임 비교

공식 문서가 나열한 흔한 선택지다. 노드마다 하나를 깔아야 Pod 가 뜬다.

| 런타임 | 성격 | 비고 |
|---|---|---|
| **containerd** | 사실상 기본. CNCF 졸업 프로젝트 | 대부분의 관리형 클러스터가 이것 |
| **CRI-O** | 쿠버네티스 전용으로 얇게 만든 런타임 | Red Hat · OpenShift 계열 |
| Docker Engine + cri-dockerd | Docker 를 계속 쓰기 위한 어댑터 | 1.24 이후 별도 설치 필요 |
| Mirantis Container Runtime | 상용 Docker Engine | 기업용 |

containerd 와 CRI-O 는 **둘 다 밑에서 runc 를 부른다.** 차이는 위쪽 — containerd 는 Docker 에서 나와 범용이고, CRI-O 는 CRI 만을 위해 만들어져 그 외 기능이 없다.

## 6. Docker 의 위치

가장 헷갈리는 지점이다. 공식 블로그의 한 문장이 답이다.

> "Docker is not a single thing but a **stack** of technologies for building and running containers. containerd … is included in Docker."

Docker 는 런타임 하나가 아니라 CLI · 빌드 · 네트워크 · 볼륨이 묶인 **스택**이고, 그 안에서 컨테이너를 실제로 돌리는 부품이 containerd 다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 270" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="1.24 이전에는 kubelet 이 dockershim 과 Docker Engine 을 거쳐 containerd 에 닿았고, 이후에는 CRI 로 containerd 에 직결된다. 실제 일하는 containerd 와 runc 는 그대로다">
  <defs>
    <marker id="cr2-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2e9c6d"/>
    </marker>
  </defs>

  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">Docker 가 빠진 게 아니라, Docker 를 거치던 길이 빠졌다</text>

  <!-- 전 -->
  <text x="30" y="82" font-size="10" fill="var(--secondary,#888)">전 (~1.23)</text>
  <rect x="120" y="60" width="90" height="44" rx="5" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="165" y="87" text-anchor="middle" font-size="10" font-weight="600" fill="#2e9c6d">kubelet</text>
  <rect x="246" y="60" width="100" height="44" rx="5" fill="none" stroke="#c0392b" stroke-width="1.2" stroke-dasharray="4 3"/>
  <text x="296" y="80" text-anchor="middle" font-size="9.5" fill="#c0392b">dockershim</text>
  <text x="296" y="95" text-anchor="middle" font-size="8" fill="#c0392b" opacity=".85">CRI 통역</text>
  <rect x="382" y="60" width="110" height="44" rx="5" fill="none" stroke="#c0392b" stroke-width="1.2" stroke-dasharray="4 3"/>
  <text x="437" y="80" text-anchor="middle" font-size="9.5" fill="#c0392b">Docker Engine</text>
  <text x="437" y="95" text-anchor="middle" font-size="8" fill="#c0392b" opacity=".85">안에 containerd 가 있음</text>
  <rect x="528" y="60" width="100" height="44" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="578" y="87" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">containerd</text>
  <rect x="664" y="60" width="70" height="44" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="699" y="87" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">runc</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#cr2-ar)">
    <path d="M210,82 H242"/>
    <path d="M346,82 H378"/>
    <path d="M492,82 H524"/>
    <path d="M628,82 H660"/>
  </g>

  <!-- 후 -->
  <text x="30" y="182" font-size="10" fill="var(--secondary,#888)">후 (1.24~)</text>
  <rect x="120" y="160" width="90" height="44" rx="5" fill="none" stroke="#2e9c6d" stroke-width="2"/>
  <text x="165" y="187" text-anchor="middle" font-size="10" font-weight="600" fill="#2e9c6d">kubelet</text>
  <rect x="528" y="160" width="100" height="44" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="578" y="187" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">containerd</text>
  <rect x="664" y="160" width="70" height="44" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="699" y="187" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">runc</text>

  <g stroke="#2e9c6d" stroke-width="1.6" fill="none" marker-end="url(#cr2-ar)">
    <path d="M210,182 H524"/>
    <path d="M628,182 H660"/>
  </g>
  <text x="367" y="174" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">CRI 로 직결</text>

  <text x="380" y="236" text-anchor="middle" font-size="9.5" fill="var(--secondary,#888)">빨간 두 칸만 사라졌다 · 오른쪽 두 칸은 전과 똑같다</text>
  <text x="380" y="258" text-anchor="middle" font-size="12" fill="var(--content,#333)">docker build 로 만든 이미지는 OCI 이미지라 그대로 돈다</text>
</svg>
</div>
{{< /rawhtml >}}

Docker Engine 은 CRI 를 말하지 못했다. 그래서 쿠버네티스가 **dockershim** 이라는 통역을 kubelet 안에 넣어 두었는데, 이름대로 임시(shim)였고 유지 부담이 커져 **1.24 에서 제거**했다.

빠진 것은 통역과 그 뒤의 Docker Engine 층이다. Docker 가 안에 품고 있던 containerd 에 kubelet 이 **바로 붙게** 됐을 뿐이라, 실제 일하는 부품은 하나도 안 바뀌었다. `docker build` 로 만든 이미지는 OCI 이미지라 계속 돈다. Docker 를 꼭 런타임으로 써야 하면 **cri-dockerd** 를 따로 깔면 되지만, 굳이 그럴 이유는 거의 없다.

## 7. cgroup 드라이버

kubelet 과 런타임이 **같은 cgroup 드라이버**를 써야 한다. 공식 문서가 "critical" 이라고 표시한 지점이다.

| 드라이버 | 언제 |
|---|---|
| `systemd` | init 이 systemd 인 대부분의 리눅스 — **권장** |
| `cgroupfs` | kubelet 기본값이지만, systemd 환경에서는 비권장. cgroup v2 에서는 쓰지 않는다 |

둘이 다르면 **cgroup 관리자가 둘**이 되어 서로 모르는 채 자원을 나누고, 결국 노드가 불안정해진다. kubelet 설정(`cgroupDriver: systemd`)과 containerd 설정(`SystemdCgroup = true`)을 함께 맞춘다. kubeadm 은 1.22 부터 kubelet 쪽을 systemd 로 기본 잡는다.

## 8. 관련 문서

- [kubelet](/wiki/kubelet/) — CRI 의 클라이언트. 6절이 이 문서의 위쪽 층이다
- [Sidecar](/wiki/sidecar/) — 런타임이 한 Pod 안에서 여러 컨테이너를 돌리는 사례
- **Pod** — 런타임이 만드는 "Pod 샌드박스"의 실체 *(예정)*

## 9. 출처

CRI 의 정의와 연결 방식, containerd 의 범위와 설계 의도, runc 의 정의, Docker 와의 관계, cgroup 드라이버 요구는 각 공식 문서에 근거한다.

> "The Container Runtime Interface (CRI) is the main gRPC protocol for the communication between the node components kubelet and container runtime." — Kubernetes Docs

> "For Kubernetes v1.26 and later, the kubelet requires that the container runtime supports the `v1` CRI API. If a container runtime does not support the `v1` API, the kubelet will not register the node." — Kubernetes Docs

> "containerd is designed to be embedded into a larger system, rather than being used directly by developers or end-users." — containerd README

> "`runc` is a CLI tool for spawning and running containers on Linux according to the OCI specification." — runc README

> "Docker is not a single thing but a stack of technologies for building and running containers. containerd, which is a daemon for managing and running containers, is included in Docker." — Kubernetes Blog

> "It's critical that the kubelet and the container runtime use the same cgroup driver and are configured the same." — Kubernetes Docs

> "the shim: 1. creates a new process to listen on a socket for ttRPC commands from containerd 2. returns the address to that socket to containerd 3. exits" … "The shim process takes responsibility as a sub-reaper to cleanup exited containers" — containerd runtime v2 docs

- [Kubernetes — Container Runtime Interface (CRI)](https://kubernetes.io/docs/concepts/architecture/cri/)
- [kubernetes/cri-api — api.proto (RuntimeService · ImageService)](https://github.com/kubernetes/cri-api/blob/master/pkg/apis/runtime/v1/api.proto)
- [Kubernetes — Container Runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Kubernetes Blog — Don't Panic: Kubernetes and Docker](https://kubernetes.io/blog/2020/12/02/dont-panic-kubernetes-and-docker/)
- [Kubernetes Blog — Dockershim Removal FAQ](https://kubernetes.io/blog/2022/02/17/dockershim-faq/)
- [containerd — README](https://github.com/containerd/containerd/blob/main/README.md)
- [containerd — Runtime v2 (shim)](https://github.com/containerd/containerd/blob/main/docs/runtime-v2.md)
- [runc — README](https://github.com/opencontainers/runc/blob/main/README.md)
