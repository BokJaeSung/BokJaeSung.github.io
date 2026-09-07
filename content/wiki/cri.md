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
  <text x="580" y="124" text-anchor="middle" font-size="8.5" fill="#2e9c6d" opacity=".85">컨테이너마다 하나</text>

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

**shim** 이 이 구조의 요점이다. containerd 데몬이 직접 runc 를 부르는 게 아니라, 컨테이너마다 작은 프로세스(shim)를 하나 띄우고 그 shim 이 runc 를 부른다. runc 는 컨테이너를 만든 뒤 종료하고, shim 이 남아 컨테이너의 표준 입출력과 종료 코드를 붙들고 있는다.

이렇게 나눈 이유는 **데몬과 컨테이너의 수명을 떼어놓기 위해서**다. containerd 를 업그레이드하거나 재시작해도 shim 은 데몬의 자식이 아니라 살아남고, 그 아래 컨테이너도 멀쩡하다. kubelet 이 죽어도 컨테이너가 도는 것과 같은 설계가 한 층 아래에서 반복된다.

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

- [Kubernetes — Container Runtime Interface (CRI)](https://kubernetes.io/docs/concepts/architecture/cri/)
- [Kubernetes — Container Runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Kubernetes Blog — Don't Panic: Kubernetes and Docker](https://kubernetes.io/blog/2020/12/02/dont-panic-kubernetes-and-docker/)
- [Kubernetes Blog — Dockershim Removal FAQ](https://kubernetes.io/blog/2022/02/17/dockershim-faq/)
- [containerd — README](https://github.com/containerd/containerd/blob/main/README.md)
- [runc — README](https://github.com/opencontainers/runc/blob/main/README.md)
