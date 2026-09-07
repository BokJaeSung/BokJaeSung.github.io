---
title: "Probe"
summary: "kubelet 이 컨테이너 상태를 확인하는 세 가지 검사. 실패했을 때 벌어지는 일이 각각 다르다."
categories: ["쿠버네티스", "워크로드"]
tags: ["kubernetes", "pod", "health"]
aliases_search: ["프로브", "헬스체크", "health check", "liveness", "readiness", "startup", "라이브니스", "레디니스"]
---

## 1. 개요

**Probe**는 kubelet 이 주기적으로 컨테이너를 찔러 보는 검사다. 세 종류가 있고, **실패했을 때 벌어지는 일이 서로 다르다.** 이 차이를 모르면 잘못 쓰기 쉽다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 320" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="세 프로브가 실패했을 때 컨테이너에 벌어지는 일 비교. startup 과 liveness 는 재시작하고 readiness 는 트래픽만 끊는다">
  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">가운데가 컨테이너 하나 — 프로브가 실패하면 여기에 무슨 일이 생기는가</text>

  <!-- startup -->
  <text x="26" y="66" font-size="11.5" font-weight="600" fill="#2f6ea8">startupProbe</text>
  <text x="26" y="82" font-size="9.5" fill="var(--secondary,#888)">다 떴나?</text>
  <rect x="160" y="52" width="130" height="44" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="225" y="79" text-anchor="middle" font-size="9.5" fill="#2f6ea8">초기화 실패</text>
  <rect x="396" y="50" width="80" height="48" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="436" y="79" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>
  <path d="M290,74 H392" stroke="#c0392b" stroke-width="1.6" fill="none"/>
  <text x="500" y="70" font-size="10.5" fill="#c0392b" font-weight="600">✕ 죽인다 → 재시작</text>
  <text x="500" y="88" font-size="10" fill="var(--secondary,#888)">restartPolicy 에 따라</text>

  <!-- liveness -->
  <text x="26" y="156" font-size="11.5" font-weight="600" fill="#c0392b">livenessProbe</text>
  <text x="26" y="172" font-size="9.5" fill="var(--secondary,#888)">살아 있나?</text>
  <rect x="160" y="142" width="130" height="44" rx="5" fill="none" stroke="#c0392b" stroke-width="1.4"/>
  <text x="225" y="169" text-anchor="middle" font-size="9.5" fill="#c0392b">교착 · 응답 없음</text>
  <rect x="396" y="140" width="80" height="48" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="436" y="169" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>
  <path d="M290,164 H392" stroke="#c0392b" stroke-width="1.6" fill="none"/>
  <text x="500" y="160" font-size="10.5" fill="#c0392b" font-weight="600">✕ 죽인다 → 재시작</text>
  <text x="500" y="178" font-size="10" fill="var(--secondary,#888)">kubelet 이 처리</text>

  <!-- readiness -->
  <text x="26" y="246" font-size="11.5" font-weight="600" fill="#2e9c6d">readinessProbe</text>
  <text x="26" y="262" font-size="9.5" fill="var(--secondary,#888)">받을 수 있나?</text>
  <rect x="160" y="232" width="130" height="44" rx="5" fill="none" stroke="#2e9c6d" stroke-width="1.4"/>
  <text x="225" y="259" text-anchor="middle" font-size="9.5" fill="#2e9c6d">DB 연결 대기 중</text>
  <rect x="396" y="230" width="80" height="48" rx="4" fill="#e6b3d9" stroke="#a05590"/>
  <text x="436" y="259" text-anchor="middle" font-size="10" font-weight="600" fill="#5a2050">컨테이너</text>
  <path d="M290,254 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="500" y="250" font-size="10.5" fill="#2e9c6d" font-weight="600">● 살려둔다</text>
  <text x="500" y="268" font-size="10" fill="var(--secondary,#888)">EndpointSlice 에서만 제외 — 트래픽 차단</text>

  <text x="380" y="306" text-anchor="middle" font-size="12" fill="var(--content,#333)">readiness 만 컨테이너를 죽이지 않는다 — 이 차이가 전부다</text>
</svg>
</div>
{{< /rawhtml >}}

## 2. 순서

셋은 나란히 도는 게 아니라 **단계가 있다.**

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 250" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="컨테이너가 시작되면 startup 프로브만 돌고 성공한 뒤에야 liveness 와 readiness 가 시작된다">
  <defs>
    <marker id="pb2-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="30" y="86" width="180" height="60" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="120" y="112" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">컨테이너 시작</text>
  <text x="120" y="130" text-anchor="middle" font-size="9.5" fill="#5a3d18">초기화 중</text>

  <rect x="266" y="86" width="180" height="60" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="356" y="112" text-anchor="middle" font-size="11.5" font-weight="600" fill="#2f6ea8">startupProbe</text>
  <text x="356" y="130" text-anchor="middle" font-size="9.5" fill="#2f6ea8">이것만 돈다</text>

  <rect x="510" y="52" width="210" height="52" rx="4" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="615" y="74" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">livenessProbe</text>
  <text x="615" y="92" text-anchor="middle" font-size="9.5" fill="#c0392b">이제부터 감시 시작</text>

  <rect x="510" y="126" width="210" height="52" rx="4" fill="none" stroke="#2e9c6d" stroke-width="1.5"/>
  <text x="615" y="148" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">readinessProbe</text>
  <text x="615" y="166" text-anchor="middle" font-size="9.5" fill="#2e9c6d">이제부터 트래픽 판단</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#pb2-ar)">
    <path d="M210,116 H262"/>
    <path d="M446,116 H486 V78 H506"/>
    <path d="M446,116 H486 V152 H506"/>
  </g>

  <text x="466" y="108" text-anchor="middle" font-size="9.5" font-style="italic" fill="#2e9c6d">성공한 뒤에야</text>
  <text x="356" y="176" text-anchor="middle" font-size="10" fill="var(--secondary,#888)">그동안 liveness 는 안 돈다 — 시작이 느려도 안 죽는다</text>

  <text x="380" y="228" text-anchor="middle" font-size="12" fill="var(--content,#333)">startup 이 통과할 때까지 나머지 둘은 대기한다</text>
</svg>
</div>
{{< /rawhtml >}}

공식 문서 그대로다 — "startup 프로브가 설정되어 있으면, 그것이 성공할 때까지 쿠버네티스는 liveness 와 readiness 프로브를 실행하지 않는다."

## 3. 세 프로브의 용도

| | 묻는 것 | 실패하면 | 언제 쓰나 |
|---|---|---|---|
| `startupProbe` | 다 떴나? | 재시작 | 시작이 오래 걸리는 앱 |
| `livenessProbe` | 살아 있나? | 재시작 | 교착(deadlock) 감지 |
| `readinessProbe` | 받을 수 있나? | 트래픽만 차단 | 의존 서비스 준비 확인 |

**liveness 는 교착을 위한 것**이다. 공식 문서의 예시가 "프로세스는 돌고 있는데 진행하지 못하는 상태"다. 앱이 문제가 생겼을 때 스스로 죽는다면 liveness 는 필요 없다 — kubelet 이 `restartPolicy` 로 알아서 처리한다.

**readiness 는 의존성을 위한 것**이다. 앱 자체는 멀쩡한데 DB 연결이 아직이라면, 죽일 게 아니라 트래픽만 안 보내면 된다.

```
앱은 정상, DB 연결 대기 중
  liveness  → 통과   (앱은 살아 있으니까)
  readiness → 실패   (아직 요청을 처리 못 하니까)
결과: 재시작 없이 트래픽만 안 온다 ✅
```

## 4. 검사 방식

네 가지 중 **하나만** 지정한다.

| 방식 | 성공 조건 |
|---|---|
| `httpGet` | 응답 코드가 200 이상 400 미만 |
| `exec` | 컨테이너 안에서 명령 실행, 종료 코드 0 |
| `tcpSocket` | 해당 포트가 열려 있음 |
| `grpc` | gRPC 헬스 체크 응답이 `SERVING` |

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15   # 첫 검사까지 대기
  periodSeconds: 10         # 검사 주기 (기본 10초)
  failureThreshold: 3       # 몇 번 실패하면 조치할지
```

## 5. 연쇄 장애

공식 문서가 **경고(Caution)** 로 표시한 지점이다.

> "Incorrect implementation of liveness probes can lead to **cascading failures**."

부하가 높을 때 응답이 느려지면 liveness 가 실패하고, 컨테이너가 재시작된다. 그 사이 다른 Pod 들이 그 부하를 나눠 받아 더 느려지고, 그것들도 재시작된다.

```
부하 증가
  → 응답 지연 → liveness 실패 → 재시작
  → 그 Pod 몫이 남은 Pod 로 → 더 느려짐 → 또 실패 → 또 재시작
  → 전체가 무너진다
```

**재시작이 해결책이 아닌 상황에서 재시작을 하기 때문**이다. 느린 것은 죽은 것이 아니다.

그래서 공식 문서가 권하는 패턴이 있다 — liveness 와 readiness 에 **같은 저비용 엔드포인트**를 쓰되, **liveness 의 `failureThreshold` 를 더 높게** 두는 것이다. 그러면 문제가 생겼을 때 트래픽이 먼저 끊기고(readiness), 그래도 회복되지 않을 때만 재시작된다(liveness).

```
문제 발생
  readiness 먼저 실패 → 트래픽 차단 → 부하가 빠지며 회복 기회
  회복 안 되면 → liveness 실패 → 그때 재시작
```

## 6. startupProbe 의 판단 기준

시작이 느린 앱에 liveness 를 그냥 걸면 **뜨는 도중에 죽는다.** 초기화가 안 끝났는데 검사가 시작되기 때문이다.

`initialDelaySeconds` 를 크게 잡는 방법도 있지만, 그러면 **평상시 장애 감지도 그만큼 늦어진다.** startupProbe 는 이 둘을 분리한다.

공식 문서의 판단 기준은 명확하다.

> 컨테이너가 보통 `initialDelaySeconds + failureThreshold × periodSeconds` 보다 오래 걸려 시작한다면, liveness 와 같은 엔드포인트를 검사하는 startup 프로브를 지정해야 한다.

## 7. 관련 문서

- [Service](/wiki/service/) — readiness 실패 시 EndpointSlice 에서 빠진다
- **restartPolicy** — liveness 실패 후의 동작을 정한다 *(예정)*

## 8. 출처

세 프로브의 동작, 순서, 연쇄 장애 경고는 공식 문서 "Liveness, Readiness, and Startup Probes" 에 근거한다.

> "If a startup probe is configured, Kubernetes does not execute liveness or readiness probes until the startup probe succeeds."

> "If the readiness probe returns a failed state, the EndpointSlice controller removes the Pod's IP address from the EndpointSlices of all Services that match the Pod."

> "Liveness probes could catch a deadlock, where an application is running, but unable to make progress."

> "Incorrect implementation of liveness probes can lead to cascading failures. This results in restarting of container under high load; failed client requests as your application became less scalable; and increased workload on remaining pods due to some failed pods."

- [Kubernetes — Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
- [Kubernetes — Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
