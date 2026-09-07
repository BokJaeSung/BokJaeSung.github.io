---
title: "Sidecar"
summary: "앱 옆에 붙어 공통 잡일을 대신하는 컨테이너. 앱 코드를 고치지 않고 기능을 얹는 방법이다."
categories: ["쿠버네티스", "패턴"]
tags: ["kubernetes", "pattern", "container"]
aliases_search: ["사이드카", "사이드카 패턴", "sidecar pattern", "사이드카 주입", "sidecar injection"]
---

## 1. 개요

앱이 다섯 개 있고, 다섯 개 모두 로그를 중앙 서버로 보내야 한다고 하자. 방법은 둘이다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 300" style="width:100%;min-width:620px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="앱마다 로그 전송 코드를 넣는 방식과, 로그 전송 컨테이너를 옆에 붙이는 사이드카 방식의 비교">
  <defs>
    <marker id="sc-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <text x="180" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#c0392b">앱마다 직접 — Java, Go, Python 각각 구현</text>
  <text x="570" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#2e9c6d">사이드카 — 한 번 만들어 전부에 붙임</text>

  <g>
    <rect x="40" y="48" width="130" height="58" rx="4" fill="#e6b3d9" stroke="#a05590"/>
    <text x="105" y="72" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a2050">Java 앱</text>
    <text x="105" y="92" text-anchor="middle" font-size="10" fill="#c0392b">+ 로그 전송 코드</text>

    <rect x="40" y="120" width="130" height="58" rx="4" fill="#e6b3d9" stroke="#a05590"/>
    <text x="105" y="144" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a2050">Go 앱</text>
    <text x="105" y="164" text-anchor="middle" font-size="10" fill="#c0392b">+ 로그 전송 코드</text>

    <rect x="40" y="192" width="130" height="58" rx="4" fill="#e6b3d9" stroke="#a05590"/>
    <text x="105" y="216" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a2050">Python 앱</text>
    <text x="105" y="236" text-anchor="middle" font-size="10" fill="#c0392b">+ 로그 전송 코드</text>
    <text x="105" y="272" text-anchor="middle" font-size="11" fill="#c0392b">같은 일을 3번 짠다</text>
  </g>

  <line x1="340" y1="40" x2="340" y2="266" stroke="var(--secondary,#888)" stroke-width="1" stroke-dasharray="4 4"/>

  <g>
    <rect x="400" y="48" width="230" height="72" rx="5" fill="#fbe0c4" stroke="#d9a86a"/>
    <rect x="414" y="62" width="94" height="44" rx="3" fill="#e6b3d9" stroke="#a05590"/>
    <text x="461" y="89" text-anchor="middle" font-size="11" font-weight="600" fill="#5a2050">Java 앱</text>
    <rect x="520" y="62" width="96" height="44" rx="3" fill="#4caf82"/>
    <text x="568" y="89" text-anchor="middle" font-size="11" font-weight="600" fill="#fff">로그 수집기</text>

    <rect x="400" y="132" width="230" height="72" rx="5" fill="#fbe0c4" stroke="#d9a86a"/>
    <rect x="414" y="146" width="94" height="44" rx="3" fill="#e6b3d9" stroke="#a05590"/>
    <text x="461" y="173" text-anchor="middle" font-size="11" font-weight="600" fill="#5a2050">Go 앱</text>
    <rect x="520" y="146" width="96" height="44" rx="3" fill="#4caf82"/>
    <text x="568" y="173" text-anchor="middle" font-size="11" font-weight="600" fill="#fff">로그 수집기</text>

    <text x="515" y="230" text-anchor="middle" font-size="11" fill="#2e9c6d">같은 이미지를 그냥 갖다 붙인다</text>
    <text x="515" y="250" text-anchor="middle" font-size="10.5" fill="var(--secondary,#888)">앱 코드는 손대지 않는다</text>
  </g>

  <text x="380" y="292" text-anchor="middle" font-size="12" fill="var(--content,#333)">공통 잡일을 앱 밖으로 빼는 것 — 그게 사이드카다</text>
</svg>
</div>
{{< /rawhtml >}}

**Sidecar**는 이렇게 앱 옆에 붙어 공통 잡일을 대신하는 컨테이너다. 오토바이 옆 보조 좌석에서 온 이름이다. 공식 문서는 이 목적을 "주 애플리케이션 코드를 직접 고치지 않고 기능을 더한다"고 표현한다.

```yaml
spec:
  containers:
  - name: app                 # 본체
    image: my-app
  - name: log-collector       # 옆자리
    image: fluent-bit
```

## 2. 공유 자원

핵심 질문은 이것이다 — **왜 남의 컨테이너가 내 로그 파일을 읽을 수 있지?**

같은 Pod 안이면 셋을 공유하기 때문이다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 250" style="width:100%;min-width:620px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pod 안에서 앱과 사이드카가 네트워크, 볼륨, 수명을 공유하는 구조">
  <rect x="130" y="24" width="500" height="160" rx="6" fill="#fbe0c4" stroke="#d9a86a" stroke-width="1.6"/>
  <text x="380" y="47" text-anchor="middle" font-size="13" font-weight="600" fill="#5a3d18">Pod — IP 하나를 나눠 쓴다</text>

  <rect x="160" y="62" width="180" height="50" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="250" y="92" text-anchor="middle" font-size="12" font-weight="600" fill="#5a2050">App container</text>

  <rect x="420" y="62" width="180" height="50" rx="4" fill="#4caf82"/>
  <text x="510" y="92" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">Sidecar</text>

  <rect x="160" y="132" width="440" height="34" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="380" y="154" text-anchor="middle" font-size="11.5" font-weight="600" fill="#1b3f63">공유 볼륨 /var/log — 한쪽이 쓰면 다른 쪽이 읽는다</text>

  <path d="M250,112 V128" stroke="var(--content,#444)" stroke-width="1.5" fill="none"/>
  <path d="M510,112 V128" stroke="var(--content,#444)" stroke-width="1.5" fill="none"/>
  <text x="285" y="126" font-size="10.5" fill="var(--content,#333)">쓴다</text>
  <text x="522" y="126" font-size="10.5" fill="var(--content,#333)">읽는다</text>

  <text x="380" y="126" text-anchor="middle" font-size="11" fill="var(--secondary,#888)">서로를 localhost 로 부른다</text>

  <text x="380" y="212" text-anchor="middle" font-size="12" fill="var(--content,#333)">네트워크 · 볼륨 · 수명을 공유 — 그래서 남남이 아니다</text>
  <text x="380" y="234" text-anchor="middle" font-size="11" fill="var(--secondary,#888)">같이 뜨고 같이 죽는다. 따로 스케줄링되지 않는다</text>
</svg>
</div>
{{< /rawhtml >}}

앱은 옆에 뭐가 붙었는지 **모른다.** 그냥 `/var/log/app.log` 에 쓰고, `localhost:8080` 으로 보낼 뿐이다. 이 무지가 사이드카의 장점이다 — 앱을 안 고쳐도 되는 이유가 여기 있다.

## 3. Init Container 와의 차이

둘 다 Pod 안에 컨테이너를 하나 더 두지만, 갈리는 지점은 하나다.

```
값이 한 번 정해지면 끝인가?          → Init Container
값이 계속 바뀌거나 갱신해야 하는가?   → Sidecar
```

만료되는 토큰을 예로 들면 분명해진다. Init Container 는 앱보다 먼저 실행되고 **종료된다.** 토큰을 받아 파일에 놓는 것까지는 되지만, 1시간 뒤 만료될 때 갱신해 줄 주체가 없다. 사이드카는 계속 살아 있으므로 갱신한다.

| | Init Container | Sidecar |
|---|---|---|
| 언제 | 앱보다 먼저, 끝나면 종료 | 앱과 함께, 계속 |
| 잘하는 일 | 준비 (내려받기, 마이그레이션) | 갱신 · 중계 · 관찰 |
| 못 하는 일 | 실행 중 갱신 | — |

### 3.1. 정식 사이드카 (restartPolicy: Always)

오래도록 사이드카는 `containers` 에 하나 더 적는 **관행**이었을 뿐, 쿠버네티스가 아는 개념이 아니었다. 그래서 문제가 있었다.

```
Pod 종료
  앱: 마지막 요청 처리 중…
  프록시 사이드카: 먼저 죽음 💀
  → 마지막 요청이 나갈 길이 없어진다
```

지금은 `initContainers` 에 `restartPolicy: Always` 를 주면 **정식 사이드카**가 된다.

```yaml
initContainers:
- name: logshipper
  image: alpine:latest
  restartPolicy: Always        # ★ 이 한 줄
  command: ['sh', '-c', 'tail -F /opt/logs.txt']
```

이름은 init 인데 종료되지 않는다. 대신 순서 보장이 생긴다.

```
시작:  사이드카가 준비될 때까지 다음 컨테이너가 기다린다
종료:  앱이 완전히 멈출 때까지 kubelet 이 사이드카를 죽이지 않는다
       그다음 명세의 역순으로 내린다
```

프록시가 앱보다 먼저 죽는 문제가 여기서 해결된다.

| 버전 | 상태 |
|---|---|
| v1.28 | 피처 게이트로 도입 |
| v1.29 | 기본 활성화 |
| v1.33 | 안정(stable) |

## 4. 쓰임새

이름만 사이드카일 뿐 하는 일은 제각각이다. 공통점은 **모든 앱이 똑같이 해야 하는 일**이라는 것.

| 시키는 일 | 예 | 앱이 직접 하면 |
|---|---|---|
| 트래픽을 대신 주고받기 | Istio Envoy | 언어마다 mTLS·재시도 구현 |
| 금고에서 시크릿 받아두기 | Vault Agent | 앱마다 Vault SDK 의존 |
| 로그 긁어 보내기 | Fluent Bit | 로깅 라이브러리 통일 강요 |
| 요청 수 세기 | Knative Queue-proxy | 앱이 자기 부하를 보고해야 함 |

언어가 5개면 5번 짜야 하는 것을, 컨테이너 하나 만들어 전부에 붙이는 것으로 바꾼다.

## 5. 자동 주입

사이드카를 매니페스트마다 손으로 적으면 앱이 수십 개일 때 같은 20줄을 복사하게 되고, 버전을 올릴 때 전부 고쳐야 한다. 그래서 **생성되는 순간 끼워 넣는** 방식을 쓴다.

```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"    # 이것만 적었는데
spec:
  containers:
  - name: my-app                                # 사이드카가 붙어서 만들어진다
```

내가 낸 YAML 과 실제로 뜬 Pod 가 다르다.

```bash
kubectl get pod my-app -o yaml    # 쓴 적 없는 vault-agent 컨테이너가 있다
```

[Mutating Admission Webhook](/wiki/admission-webhook/) 이 하는 일이고, Istio·Linkerd·Vault Injector 가 모두 이 방식이다. 실제로 오가는 것은 컨테이너를 추가하라는 JSON Patch 한 줄이다.

## 6. 비용과 대안

Pod 마다 컨테이너가 하나씩 는다. Pod 가 3000개면 컨테이너가 6000개다. 메모리와 CPU 가 그만큼 더 들고, 앱과 프록시 중 어느 쪽 문제인지 가리는 수고도 생긴다.

그래서 **사이드카를 없애려는 흐름**이 있다. 프록시를 Pod 마다 붙이는 대신 커널(eBPF)에서 처리하는 방식으로, Cilium 과 Istio Ambient 모드가 그 방향이다. 사이드카가 풀었던 문제를 다른 층위에서 다시 푸는 셈이다.

## 7. 관련 문서

- **Init Container** — 앱보다 먼저 실행되고 종료되는 컨테이너 *(예정)*
- [Admission Webhook](/wiki/admission-webhook/) — 사이드카를 자동으로 끼워 넣는 확장 지점
- **mTLS** — 프록시 사이드카가 담당하는 상호 인증 *(예정)*

## 8. 출처

정의와 버전, 시작·종료 순서 보장은 공식 문서 "Sidecar Containers" 에 근거한다.

> "These containers are used to enhance or to extend the functionality of the primary app container by providing additional services, or functionality such as logging, monitoring, security, or data synchronization, **without directly altering the primary application code**."

> "Upon Pod termination, the kubelet **postpones terminating sidecar containers until the main application container has fully stopped**. The sidecar containers are then shut down in the opposite order of their appearance in the Pod specification."

> "Sidecar containers **share the same network and storage namespaces** with the primary container."

- [Kubernetes — Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/)
- [Kubernetes — Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Istio — Sidecar Injection](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/)
