---
series: ["K8sPatterns"]
title: "K8sPatterns.05 Managed Lifecycle"
date: 2026-07-01T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "lifecycle"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.05 Managed Lifecycle'
  relative: true
summary: "How Kubernetes communicates lifecycle events to containers via SIGTERM, SIGKILL, postStart, preStop hooks, and init containers for graceful startup and shutdown."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-why-managed-lifecycle" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Why Managed Lifecycle?</a></div>
  <div><a href="#3-sigterm-signal" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. SIGTERM Signal</a></div>
  <div><a href="#4-sigkill-signal" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. SIGKILL Signal</a></div>
  <div><a href="#5-poststart-hook" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. PostStart Hook</a></div>
  <div><a href="#6-prestop-hook" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. PreStop Hook</a></div>
  <div><a href="#7-전체-컨테이너-수명주기" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. 전체 컨테이너 수명주기</a></div>
  <div><a href="#8-other-lifecycle-controls" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">8. Other Lifecycle Controls</a></div>
  <div><a href="#9-entrypoint-rewriting" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">9. Entrypoint Rewriting</a></div>
  <div><a href="#10-무엇을-써야-하나" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">10. 무엇을 써야 하나?</a></div>
  <div><a href="#11-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">11. Discussion</a></div>
</div>
</div>
{{< /rawhtml >}}

## 1. Overview

```
Kubernetes ↔ 앱 양방향 소통
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4장 Health Probe  (앱 → Kubernetes)
  └─► "나 이런 상태야" 알림

5장 Managed Lifecycle  (Kubernetes → 앱)
  └─► "너한테 중요한 일 생겼어" 명령
        ├─► SIGTERM   → 종료 요청
        ├─► SIGKILL   → 강제 종료
        ├─► postStart → 시작 직후 실행
        └─► preStop   → 종료 직전 실행
```

---

## 2. Why Managed Lifecycle?

### 4장과의 차이

4장 Health Probe는 **읽기 전용**이다. Kubernetes가 앱 상태를 물어보면 앱이 답변만 한다. 앱의 상태는 바뀌지 않는다.

5장 Managed Lifecycle은 **명령**이다. Kubernetes가 앱에게 시키면 앱이 실제로 행동한다.

```
4장 Health Probe
  Kubernetes → "살아있어?"
  앱         → "응" (읽기 전용, 상태 안 바뀜)

5장 Managed Lifecycle
  Kubernetes → "이제 종료해"
  앱         → 정리 작업 시작 (실제 행동)
```

### 단순 프로세스 모델의 한계

그냥 켜고 끄는 것만으로는 부족한 경우가 있다.

- 워밍업이 필요한 앱 → 시작 직후 캐시 로딩, DB 커넥션 미리 맺기
- 깔끔한 종료가 필요한 앱 → 처리 중인 요청 마무리, DB 커넥션 정상 종료

그래서 Kubernetes는 컨테이너가 수신하고 반응할 수 있는 이벤트를 발생시킨다.  
반응할지 말지는 앱이 결정한다. 필요 없으면 무시해도 된다.

### 적용 레벨

이 챕터의 이벤트와 훅은 **Pod 레벨이 아닌 개별 컨테이너 레벨**에서 적용된다.

```
Pod
  ├─► Pod 레벨: Init Container (15장)
  │
  ├─► 컨테이너 1 (앱)      → postStart, preStop, SIGTERM 독립
  └─► 컨테이너 2 (사이드카) → postStart, preStop, SIGTERM 독립
```

Pod 안에 컨테이너가 여러 개여도 각자 독립적으로 이벤트를 처리하며 서로 영향을 주지 않는다.

| Pod 레벨 | 컨테이너 레벨 |
|---|---|
| Init Container (15장) | postStart / preStop / SIGTERM / SIGKILL |
| Pod 전체에 적용 | 각 컨테이너에 개별 적용 |

---

## 3. SIGTERM Signal

Kubernetes가 컨테이너를 종료할 때 — Pod 종료든 Liveness Probe 실패로 인한 재시작이든 — 컨테이너는 **SIGTERM 신호**를 먼저 받는다.

```
SIGTERM = "이제 종료해" (정중하게)
SIGKILL = "당장 죽어"  (강제로)

SIGTERM을 먼저 보내고
응답 없으면 SIGKILL로 강제 종료
```

### SIGTERM이 오는 상황

- Pod 종료 시 (`kubectl delete pod`, 스케일 다운, 롤링 업데이트)
- Liveness Probe 실패 시 — 재시작 전에도 SIGTERM 먼저 옴

### SIGTERM 받은 후 해야 할 일

```
단순한 앱
  SIGTERM 수신 → 바로 종료

복잡한 앱
  SIGTERM 수신
    │
    새 요청 안 받음
    처리 중인 요청 마무리
    DB 커넥션 정상 종료
    임시 파일 삭제
    │
    종료
```

```java
// Spring Boot 예시
@PreDestroy
public void onShutdown() {
    requestHandler.stopAccepting();     // 새 요청 차단
    requestHandler.waitForCompletion(); // 진행 중 요청 완료
    dbConnection.close();               // DB 커넥션 종료
}
```

---

## 4. SIGKILL Signal

SIGTERM 후 일정 시간이 지나도 종료되지 않으면 **SIGKILL로 강제 종료**된다.

```
SIGTERM 전송
    │
    기본 30초 대기
    │
    아직 종료 안 됨
    │
    SIGKILL (무조건 종료, 무시 불가)
```

### terminationGracePeriodSeconds

```yaml
spec:
  terminationGracePeriodSeconds: 60  # 기본 30초 → 60초로 변경
  containers:
  - name: my-app
```

단, `kubectl delete pod --grace-period=0` 같은 명령으로 **재정의될 수 있어 보장되지 않는다.**

### Ephemeral 설계

SIGKILL에 대비해 앱을 **빠른 시작/종료가 가능한 임시적(Ephemeral) 구조**로 설계해야 한다.

| | 나쁜 설계 | 좋은 설계 (Ephemeral) |
|---|---|---|
| 시작/종료 시간 | 오래 걸림 | 빠름 |
| 상태 저장 위치 | 로컬 | 외부 저장소 |
| SIGKILL 시 결과 | 데이터 유실 | 잃을 게 없음 |

---

## 5. PostStart Hook

프로세스 신호만으로는 수명주기 관리가 제한적이다. 그래서 Kubernetes는 `postStart`와 `preStop` 훅을 제공한다.

`postStart`는 컨테이너가 **시작된 직후 자동으로 실행되는 추가 작업**이다. 앱을 시작시키는 게 아니라, 시작 후 워밍업 작업을 수행한다.

```
컨테이너 시작 (Kubelet이 시킴)
    │
    ├─► 메인 앱 실행     (병렬)
    └─► postStart 실행   (병렬)
          워밍업 작업 수행
```

### 컨테이너 시작 주체

메인 앱 시작은 개발자가 직접 시키는 게 아니다. Kubelet이 컨테이너 런타임(Docker, containerd 등)에 명령을 내리고, 런타임이 이미지 안에 정의된 `ENTRYPOINT`/`CMD`를 실행한다.

```
Kubelet
  └─► 컨테이너 런타임 (containerd 등)
        └─► 컨테이너 안의 ENTRYPOINT 실행
              예: java -jar app.jar
```

개발자는 YAML에 이미지만 지정하면 된다. 시스템콜은 컨테이너 내부에서 **추가 프로세스**를 실행할 때 쓰는 것이고, 메인 앱 자체를 시작시키는 것은 Kubelet이 담당한다.

```
메인 앱 시작   → Kubelet이 시킴 (개발자 관여 없음)
postStart 실행 → 시작 직후 자동 실행 (추가 작업)
sh -c "..."    → 컨테이너 내부에서 추가 프로세스 실행 (시스템콜)
```

postStart는 메인 앱과 **같은 컨테이너 안에서** 별개의 프로세스로 실행된다. 파일시스템, 네트워크를 공유한다.

### Example 5-1

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: post-start-hook
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    lifecycle:
      postStart:
        exec:
          command:
          - sh
          - -c
          # sh -c 로 쉘 명령어 문자열을 실행 — 파이프, &&, 리다이렉션 모두 사용 가능
          - sleep 30 && echo "Wake up!" > /tmp/postStart_done
          # ↑ 두 가지 작업을 순서대로 실행:
          #
          # [1] sleep 30
          #   실제 워밍업 작업(캐시 로딩, DB 커넥션 풀 생성 등)을 30초로 시뮬레이션
          #   postStart는 블로킹이므로 이 30초 동안
          #   컨테이너 상태는 Waiting, Pod 상태는 Pending 으로 유지됨
          #   → Readiness Probe도 아직 시작 안 됨
          #   → 트래픽도 아직 안 들어옴
          #
          # [2] echo "Wake up!" > /tmp/postStart_done
          #   sleep이 성공(종료코드 0)한 경우에만 && 조건으로 실행
          #   워밍업 완료 시점에 트리거 파일을 생성
          #   메인 앱이 이 파일 존재 여부로 postStart 완료를 확인 가능
          #   (stat /tmp/postStart_done 등으로 체크)
          #
          # 주의: sleep 30이 실패하거나(종료코드 != 0) 명령 전체가 실패하면
          #   Kubernetes가 메인 컨테이너를 강제 종료하고 재시작함
```

### 블로킹 특성

postStart는 **블로킹 호출**이다. 완료될 때까지 컨테이너 상태는 `Waiting`, Pod 상태는 `Pending`으로 유지된다.

```
0초   컨테이너 시작
       │
       ├─► 메인 앱 실행 중...
       └─► postStart 실행 중...
       │
       컨테이너 상태: Waiting
       Pod 상태:      Pending
       │
30초  postStart 완료
       │
       컨테이너 상태: Running
       Pod 상태:      Running
```

이 특성을 활용해 **메인 앱이 초기화될 시간을 벌어줄 수 있다.**

### postStart로 시작 막기

postStart가 0이 아닌 종료 코드를 반환하면 Kubernetes가 **메인 컨테이너를 강제 종료**한다.

```
postStart 실행
    │
    조건 확인 (필요한 설정 파일 있나?)
    │
    ├─► 종료코드 0 → 정상, 계속 실행
    └─► 종료코드 1 → 메인 앱 강제 종료, 재시작
```

### 지원 방법

- `exec` → 명령어 실행 (컨테이너 내부)
- `httpGet` → HTTP GET 요청
- Health Probe와 동일, `tcpSocket`은 미지원

### 주의사항

| 주의사항 | 설명 | 대응 방법 |
|---|---|---|
| 타이밍 보장 없음 | 메인 앱보다 먼저 실행될 수 있음 | 메인 앱 상태에 의존하는 로직 넣지 말 것 |
| 중복 실행 가능 | at-least-once — 2번 이상 실행될 수 있음 | 멱등성 보장하게 구현 |
| HTTP 재시도 없음 | httpGet 실패 시 재시도 안 함 | exec 방식 선호 |

**멱등성:** 몇 번 실행해도 결과가 같은 것. `touch /tmp/ready`는 몇 번 실행해도 파일 하나만 생긴다.

**타이밍 보장 없음 — 왜 문제인가?**

postStart는 메인 앱과 병렬로 실행된다. postStart가 메인 앱보다 먼저 실행될 수 있으므로, 메인 앱의 API를 호출하는 로직을 postStart에 넣으면 메인 앱이 아직 안 뜬 상태에서 호출해 실패한다.

**HTTP 재시도 없음 — Health Probe와의 차이**

Health Probe는 실패 시 `failureThreshold`만큼 재시도한다. postStart의 `httpGet`은 실패하면 그냥 실패 처리된다. 재시도가 없으므로 네트워크 순간 오류에도 취약하다. postStart에는 `exec` 방식을 선호한다.

한 줄 요약: postStart는 언제 실행될지, 몇 번 실행될지 보장이 없으므로 중요한 로직은 넣지 않는다.

---

## 6. PreStop Hook

종료 직전에 전송되는 **블로킹 호출**이다. SIGTERM과 동일한 의미를 가지며, SIGTERM에 반응하기 어려울 때 사용한다.

preStop이 완료된 **후에** SIGTERM이 전송된다.

```
종료 결정
    │
    preStop 실행 (블로킹)
    │
    preStop 완료
    │
    SIGTERM 전송
    │
    30초 대기
    │
    SIGKILL
```

### Example 5-2

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pre-stop-hook
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    lifecycle:
      preStop:
        httpGet:
          path: /shutdown        # 앱 내부에 구현된 종료 준비 엔드포인트
          port: 8080
          # preStop 동작 흐름:
          #   1. Kubernetes가 종료 결정
          #   2. GET /shutdown:8080 요청 전송 (블로킹 — 응답 올 때까지 대기)
          #   3. 앱이 /shutdown 수신
          #      → 새 요청 차단
          #      → 처리 중인 요청 마무리
          #      → DB 커넥션 정리 등 정리 작업 수행
          #      → 완료되면 HTTP 응답 반환
          #   4. preStop 완료 → SIGTERM 전송
          #   5. 30초 대기 후 SIGKILL
          #
          # httpGet 방식 주의사항:
          #   - 재시도 없음 — 한 번 실패하면 바로 실패 처리
          #   - 앱이 /shutdown 응답하기 전에 이미 죽어있으면 실패
          #   - 이런 경우 exec + sleep 조합이 더 안전
```

언어/프레임워크가 SIGTERM 핸들링을 미지원하거나 레거시 앱이 SIGTERM을 무시할 때, `preStop`의 `/shutdown` 엔드포인트로 대신 처리할 수 있다.

### 실무에서 가장 많이 쓰는 패턴

```yaml
preStop:
  exec:
    command: ["sleep", "5"]   # exec + sleep 조합
```

SIGTERM이 왔을 때 트래픽 차단 전파가 비동기로 처리되는 시간차가 있다. `sleep 5`로 잠깐 기다리는 동안 전파가 완료되어 안전하게 종료할 수 있다.

### 주의사항

preStop이 실패하거나 멈춰도 **컨테이너 삭제와 프로세스 종료를 막을 수 없다.** 종료 전 마지막 정리 기회이지, 종료 자체를 막는 거부권이 아니다.

postStart와 동일한 보장/한계를 가진다 (at-least-once, HTTP 재시도 없음).

### postStart vs preStop 비교

| | postStart | preStop |
|---|---|---|
| 실행 시점 | 시작 직후 | 종료 직전 |
| 목적 | 워밍업 | 정리 작업 |
| 블로킹 | ✓ | ✓ |
| 메인 앱과 관계 | 병렬 실행 | 먼저 실행 후 SIGTERM |
| 종료 막기 | 불가 | 불가 |

---

## 7. 전체 컨테이너 수명주기

```
컨테이너 시작
    │
    postStart  ──► 워밍업 (블로킹, Waiting 상태 유지)
    │
    Running    ──► 정상 운영
    │
    preStop    ──► 정리 작업 (블로킹, SIGTERM 전 완료)
    │
    SIGTERM    ──► 종료 요청 (30초 유예)
    │
    SIGKILL    ──► 강제 종료 (무시 불가)
```

---

## 8. Other Lifecycle Controls

컨테이너 레벨 훅 외에, **Pod 레벨**에서 초기화를 담당하는 Init Container가 있다.

### Init Container 특징

```
순차 실행
  Init Container 1 완료
      │
  Init Container 2 완료
      │
  메인 앱 컨테이너 시작

완료 보장
  실패하면 재시도 — 성공할 때까지
  메인 앱은 절대 먼저 시작 안 함
```

### lifecycle 훅 vs Init Container

| | Lifecycle hooks | Init containers |
|---|---|---|
| 활성화 시점 | 컨테이너 수명주기 | Pod 수명주기 |
| 시작 단계 | postStart 명령어 1개 | initContainers 목록 순차 실행 |
| 종료 단계 | preStop 명령어 | 해당 기능 없음 |
| 타이밍 보장 | ENTRYPOINT와 동시 실행 (보장 없음) | 모든 init 완료 후 앱 시작 (100% 보장) |
| 사용 사례 | 컨테이너별 시작/종료 정리 | 순차적 워크플로우, 컨테이너 재사용 |

---

## 9. Entrypoint Rewriting

Init Container와 lifecycle 훅으로 해결 못하는 경우가 있다. **사이드카가 있는 복잡한 수명주기 관리**가 필요할 때다.

### 왜 필요한가?

Init Container는 앱 시작 전에 완료되고 종료된다. 운영 중에는 존재하지 않으므로 사이드카처럼 계속 실행할 수 없다.

예를 들어 Istio 프록시는 메인 앱과 함께 계속 실행되어야 하고, 프록시가 준비되기 전에 메인 앱이 실행되면 안 된다. Init Container로는 이 요구사항을 충족할 수 없다.

### 개념

원래 명령어를 슈퍼바이저(래퍼)로 교체해 수명주기를 제어한다.

```
원래:
  command: random-generator-runner --seed 42

바꿔치기 후:
  command: supervisor random-generator-runner --seed 42
              │
              supervisor가 사이드카 준비 확인
              → 준비되면 메인 앱 실행
```

### Example 5-3 (원래 구조)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-random-generator
spec:
  restartPolicy: OnFailure
  # OnFailure: 종료코드가 0이 아닐 때만 재시작
  # Always(기본값): 항상 재시작 — 서버처럼 계속 떠있어야 하는 앱
  # Never: 절대 재시작 안 함 — 배치 잡처럼 한 번만 실행하는 앱

  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    command:
    - "random-generator-runner"
    # Dockerfile의 ENTRYPOINT/CMD 대신 이 명령어로 덮어씀
    # 지정하지 않으면 이미지에 정의된 ENTRYPOINT가 그대로 실행됨
    args:
    - "--seed"
    - "42"
    # command의 인자로 전달됨
    # 최종 실행 명령어: random-generator-runner --seed 42
    #
    # 이 구조의 한계:
    #   - 사이드카가 준비되기 전에 메인 앱이 바로 실행됨
    #   - postStart/preStop 훅 없음 → 시작/종료 시 추가 작업 불가
    #   - 사이드카(프록시 등)가 아직 준비 안 됐는데 트래픽 받을 수 있음
    #   → Example 5-4에서 supervisor로 이 문제를 해결함
```

### Example 5-4 (래퍼 적용)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: wrapped-random-generator
spec:
  restartPolicy: OnFailure
  # OnFailure: 종료코드가 0이 아닐 때만 재시작
  # supervisor가 실패(사이드카 준비 타임아웃 등)하면 재시작
  # 정상 종료(종료코드 0)면 재시작 안 함 — 배치성 작업에 적합

  volumes:
  - name: wrapper
    emptyDir: { }
    # 새로 생성되는 빈 볼륨 — Init Container와 메인 앱 컨테이너가 공유
    # Init Container가 supervisor 파일을 여기 복사하고,
    # 메인 앱이 이 볼륨에서 supervisor를 꺼내 실행한다

  initContainers:
  - name: copy-supervisor
    image: k8spatterns/supervisor    # supervisor 바이너리가 담긴 이미지
    volumeMounts:
    - mountPath: /var/run/wrapper
      name: wrapper                  # 공유 볼륨을 /var/run/wrapper 에 마운트
    command: [ cp ]
    args: [ supervisor, /var/run/wrapper/supervisor ]
    # supervisor 바이너리를 공유 볼륨에 복사하는 것이 전부
    # 복사 완료 후 Init Container는 종료 — 이후 역할 없음
    # 메인 앱 컨테이너는 이 Init Container가 성공적으로 완료된 후에만 시작된다

  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    volumeMounts:
    - mountPath: /var/run/wrapper
      name: wrapper                        # 같은 공유 볼륨 마운트 — supervisor 파일 접근
    command:
    - "/var/run/wrapper/supervisor"        # 원래 ENTRYPOINT 대신 supervisor를 진입점으로 교체
                                           # supervisor가 사이드카 준비 여부를 확인하고
                                           # 준비되면 아래 args의 명령어를 실행한다
    args:
    - "random-generator-runner"            # Example 5-3의 원래 command가 여기로 이동
    - "--seed"                             # 원래 args도 그대로 supervisor에게 넘김
    - "42"
    # supervisor의 역할:
    #   1. 사이드카(프록시 등)가 준비됐는지 확인
    #   2. 준비 완료 → random-generator-runner --seed 42 실행
    #   3. 메인 프로세스 종료 시 정리 작업 수행
```

### Pod 안 컨테이너 역할 분담

```
[1단계] Init Container (copy-supervisor)
  공유 볼륨에 supervisor 파일 복사
  할 일 끝 → 종료 (이후 없음)

[2단계] 메인 앱 + 사이드카 동시 시작
  사이드카: 네트워크 프록시 등 준비 중
  메인 앱:  supervisor가 먼저 실행
              │
              사이드카 준비될 때까지 대기
              │
              사이드카 준비 완료
              │
              random-generator-runner --seed 42 실행
```

**Init Container가 메인 앱을 통제하는 게 아니다.** 둘 다 같은 Pod 레벨 볼륨을 각자 마운트해서 파일을 주고받는 것이다.

### 세 가지 방법 비교

| | lifecycle 훅 | Init Container | Entrypoint Rewriting |
|---|---|---|---|
| 레벨 | 컨테이너 | Pod | 컨테이너 |
| 사이드카 지원 | ✗ | ✗ | ✓ |
| 완료 보장 | ✗ | ✓ | ✓ |
| 복잡도 | 낮음 | 낮음 | 높음 |
| 사용 빈도 | 많음 | 많음 | 드묾 (Istio 등 인프라 솔루션) |

---

## 10. 무엇을 써야 하나?

| 상황 | 선택 |
|---|---|
| 간단한 시작/종료 작업 | lifecycle 훅 (postStart/preStop) |
| 타이밍 보장이 필요한 경우 | Init Container |
| 사이드카 + 정밀 제어 | Entrypoint Rewriting |

엄격한 규칙은 없다. bash 스크립트로 다 처리할 수도 있지만, 컨테이너와 스크립트가 강하게 결합되어 유지보수가 어려워진다.

```
노력    낮음 ─────────────────────────────────► 높음
        bash → lifecycle 훅 → Init Container → Entrypoint Rewriting

보장/
재사용  낮음 ─────────────────────────────────► 높음
```

컨테이너와 Pod 수명주기의 단계와 훅을 이해하는 것이, Kubernetes가 관리하는 앱을 만드는 핵심이다.

---

## 11. Discussion

### 플랫폼과 앱의 계약

클라우드 네이티브 플랫폼의 핵심 가치는 **불안정한 인프라 위에서 앱을 안정적으로 실행하고 스케일링**할 수 있다는 점이다. 이를 위해 플랫폼은 앱에게 일련의 **제약과 계약(constraints and contracts)** 을 제시한다.

앱이 이 계약을 지키면 플랫폼의 모든 기능을 온전히 활용할 수 있다. 계약을 무시하면 플랫폼이 제공하는 자동화 혜택을 받지 못한다.

```
플랫폼이 제공하는 것
  └─► 안정적 실행, 자동 스케일링, 자가 치유

앱이 지켜야 할 것 (계약)
  └─► SIGTERM 핸들링
      postStart/preStop 훅 구현
      Liveness/Readiness Probe 제공
      빠른 시작/종료 (Ephemeral 설계)
```

### 현재: POSIX 프로세스처럼 동작

지금 당장의 요구사항은 단순하다. **잘 설계된 POSIX 프로세스처럼 동작**하는 것이다.

- SIGTERM 수신 → 정리 후 종료
- 빠른 시작과 빠른 종료
- 상태는 외부 저장소에 저장

### 미래: 더 많은 이벤트

앞으로는 더 세밀한 이벤트가 추가될 수 있다.

- 스케일 업 직전 힌트 → 미리 준비할 기회
- 리소스 반납 요청 → 종료되기 전에 스스로 정리

현재는 이런 이벤트가 없지만, 플랫폼이 발전할수록 앱이 반응할 수 있는 신호가 늘어난다.

### 핵심: 앱 수명주기는 사람이 아닌 플랫폼이 관리한다

```
전통적인 방식
  사람이 직접 → 시작, 종료, 재시작 결정

클라우드 네이티브
  플랫폼(Kubernetes)이 → 시작, 종료, 재시작 자동 결정
  앱은 → 플랫폼의 신호에 반응할 준비만 하면 됨
```

Managed Lifecycle 패턴은 이 자동화된 수명주기 관리에서 **앱이 해야 할 역할**을 정의한다. 다음 챕터 Automated Placement는 Kubernetes가 컨테이너를 노드에 배치하는 **스케줄링 결정**을 다룬다.
