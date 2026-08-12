---
series: ["K8sPatterns"]
title: "K8sPatterns.19 EnvVar Configuration"
date: 2026-08-12T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "configuration"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.19 EnvVar Configuration'
  relative: true
summary: "설정 외부화의 가장 단순한 수단, 환경 변수 — 기본값과 런타임 오버라이드 패턴부터 보안 한계와 불변성의 역설까지."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-하드코딩이-왜-문제인가" style="color:var(--secondary,inherit);text-decoration:none;">2.1 하드코딩이 왜 문제인가</a></div>
    <div><a href="#22-불변-이미지와-설정-외부화" style="color:var(--secondary,inherit);text-decoration:none;">2.2 불변 이미지와 설정 외부화</a></div>
  </div>
  <div><a href="#3-solution" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-핵심-패턴-빌드-시-기본값--런타임-오버라이드" style="color:var(--secondary,inherit);text-decoration:none;">3.1 핵심 패턴: 빌드 시 기본값 + 런타임 오버라이드</a></div>
    <div><a href="#32-docker에서의-구현" style="color:var(--secondary,inherit);text-decoration:none;">3.2 Docker에서의 구현</a></div>
    <div><a href="#33-kubernetes에서의-구현-env" style="color:var(--secondary,inherit);text-decoration:none;">3.3 Kubernetes에서의 구현: env</a></div>
    <div><a href="#34-환경-변수는-안전하지-않다" style="color:var(--secondary,inherit);text-decoration:none;">3.4 환경 변수는 안전하지 않다</a></div>
    <div><a href="#35-기본값에-대하여" style="color:var(--secondary,inherit);text-decoration:none;">3.5 기본값에 대하여</a></div>
    <div><a href="#36-편의-기능-3종-envfrom-downward-api-종속-변수" style="color:var(--secondary,inherit);text-decoration:none;">3.6 편의 기능 3종: envFrom, Downward API, 종속 변수</a></div>
    <div><a href="#37-command에서의-환경-변수-치환" style="color:var(--secondary,inherit);text-decoration:none;">3.7 command에서의 환경 변수 치환</a></div>
  </div>
  <div><a href="#4-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-규모의-한계와-spring-boot-프로파일-안티패턴" style="color:var(--secondary,inherit);text-decoration:none;">4.1 규모의 한계와 Spring Boot 프로파일 안티패턴</a></div>
    <div><a href="#42-파편화--이-값-어디서-온-거야" style="color:var(--secondary,inherit);text-decoration:none;">4.2 파편화 — "이 값 어디서 온 거야?"</a></div>
    <div><a href="#43-불변성의-역설--못-바꾸는-게-장점이다" style="color:var(--secondary,inherit);text-decoration:none;">4.3 불변성의 역설 — 못 바꾸는 게 장점이다</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
EnvVar Configuration 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

설정을 코드/이미지에서 분리하라 → 가장 단순한 수단이 환경 변수다
                    │
     ┌──────────────┼──────────────────┐
     ▼              ▼                  ▼
빌드 시 기본값     런타임 오버라이드      값의 출처
Dockerfile ENV   docker run -e      value (직접)
                 Pod spec env:      configMapKeyRef
                                    secretKeyRef
```

모든 비자명(nontrivial)한 애플리케이션은 설정이 필요하다. DB 접속 정보, 외부 서비스 주소, 프로덕션 튜닝 값 — 이런 값을 코드에 하드코딩하는 대신 외부화하면, **한 번 빌드한 애플리케이션을 수정 없이 여러 환경에서 재사용**할 수 있다.

**EnvVar Configuration 패턴**은 이 외부화를 가장 단순한 도구인 **환경 변수**로 구현한다. 어떤 OS든, 어떤 언어든 환경 변수를 지원하기 때문에 보편적으로 적용 가능하다. 다만 이 단순함에는 명확한 적용 한계가 있으며, 그 한계선이 어디인지 아는 것이 이 패턴의 절반이다.

---

## 2. Problem

### 2.1 하드코딩이 왜 문제인가

```
❌ 하드코딩된 설정
코드 안에 DB 주소가 박혀 있음
→ 값이 바뀔 때마다: 코드 수정 → 재빌드 → 재배포
→ 환경(개발/운영)마다 다른 빌드가 필요
```

12요소 앱(twelve-factor app) 선언문이 나오기 훨씬 전부터, 설정을 코드에 하드코딩하는 것은 나쁜 관행으로 알려져 있었다. 설정은 외부화되어 **빌드 이후에도 변경 가능**해야 한다.

### 2.2 불변 이미지와 설정 외부화

컨테이너 세계에서 이 원칙은 더 중요해진다. 컨테이너 이미지의 핵심 철학은 **불변성(immutability)** — 한 번 만든 이미지는 절대 고치지 않고, 동일한 이미지를 모든 환경에서 재사용한다는 것이다.

```
❌ 설정이 이미지 안에 있으면
my-app-dev:1.0 / my-app-prod:1.0 ... 환경마다 이미지 재빌드
→ "테스트한 것"과 "운영에 올라간 것"이 서로 다른 물건

✅ 설정을 외부에서 주입하면
my-app:1.0 하나로 개발 → 스테이징 → 운영 전부 커버
→ 테스트를 통과한 바로 그 이미지가 운영에 올라감
```

그렇다면 컨테이너화된 세계에서 설정 외부화를 어떻게 구현하는 것이 최선일까?

---

## 3. Solution

### 3.1 핵심 패턴: 빌드 시 기본값 + 런타임 오버라이드

환경 변수의 결정적 강점은 **보편성**이다. 모든 OS가 환경 변수를 정의하고 자식 프로세스에 전파하는 방법을 알고 있으며, 모든 언어가 한 줄로 읽을 수 있다 — Java의 `System.getenv()`, Python의 `os.environ`, Node.js의 `process.env`. 라이브러리도, 설정 파일 파서도 필요 없다.

전형적인 사용 패턴은 두 단계다.

```
① 빌드 시점: 이미지 안에 안전한 기본값을 심는다
② 런타임:   배포 환경에 맞게 그 값을 덮어쓴다

[이미지]  LOG_LEVEL=info  (기본값, 고정)
     │
     ├─ 개발 서버 실행 → LOG_LEVEL=debug 로 오버라이드
     └─ 운영 서버 실행 → 기본값 그대로
```

굳이 런타임에 덮어쓰는 이유는 명확하다.

| 이유 | 설명 |
|---|---|
| **환경별 차이 흡수** | 개발 DB와 운영 DB 주소가 다르다 — 이미지 재빌드 없이 값만 교체 |
| **동일 아티팩트 보장** | 테스트한 이미지 = 운영 이미지, 빌드를 두 번 하지 않는다 |
| **민감 정보 분리** | 비밀번호를 이미지에 박으면 이미지를 받는 누구나 볼 수 있다 |
| **빠른 대응** | 로그 레벨 변경에 재빌드(수 분) 대신 재시작(수 초) |

기본값의 역할도 분명하다. 아무 설정 없이 실행해도 **일단 돌아가게** 하고, 바뀌는 값만 덮어쓰게 만드는 안전한 출발점이다.

### 3.2 Docker에서의 구현

**빌드 시점 — Dockerfile의 ENV 지시어**

```dockerfile
# Example 19-1. 환경 변수가 있는 Dockerfile
FROM openjdk:11
ENV PATTERN "EnvVar Configuration"   # ① 한 줄에 하나씩 정의
ENV LOG_FILE "/tmp/random.log"
ENV SEED "1349093094"

# ② 또는 한 줄에 전부 (= 문법, 최근 권장 스타일 — 레이어도 하나만 생성)
ENV PATTERN="EnvVar Configuration" LOG_FILE=/tmp/random.log SEED=1349093094
```

**애플리케이션에서 읽기**

```java
// Example 19-2. Java에서 환경 변수 읽기
public Random initRandom() {
    long seed = Long.parseLong(System.getenv("SEED"));  // ① 환경 변수는 항상 문자열 → 타입 변환 필요
    return new Random(seed);                            // ② EnvVar의 시드로 난수 생성기 초기화
}
```

**런타임 — docker run -e 로 오버라이드**

```bash
# Example 19-3. 컨테이너 시작 시 환경 변수 덮어쓰기
docker run -e PATTERN="EnvVarConfiguration" \
       -e LOG_FILE="/tmp/random.log" \
       -e SEED="147110834325" \
       k8spatterns/random-generator:1.0
```

```
그냥 실행:     SEED = 1349093094   (이미지 기본값)
-e로 실행:    SEED = 147110834325  (오버라이드) — 재빌드 없음 ✅
```

### 3.3 Kubernetes에서의 구현: env

Docker의 `-e`에 해당하는 것이 Pod 스펙의 `env:` 필드다. 여기서 값을 지정하는 방법이 **세 가지**로 나뉜다.

```yaml
# Example 19-4. 환경 변수가 설정된 Pod
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    env:
    - name: LOG_FILE
      value: /tmp/random.log            # ① 리터럴 값 직접 지정 — 가장 단순
    - name: PATTERN
      valueFrom:
        configMapKeyRef:                # ② ConfigMap에서 가져오기
          name: random-generator-config #    ③ 참조할 ConfigMap 이름
          key: pattern                  #    ④ 그 안에서 찾을 키
    - name: SEED
      valueFrom:
        secretKeyRef:                   # ⑤ Secret에서 가져오기 (조회 방식은 ConfigMap과 동일)
          name: random-generator-secret
          key: seed
```

**ConfigMap은 Pod가 아니라 독립 리소스다**

```yaml
apiVersion: v1
kind: ConfigMap            # kind가 ConfigMap — 컨테이너도 프로세스도 없는 순수 데이터 리소스
metadata:
  name: random-generator-config
data:                      # spec이 아니라 data
  pattern: "EnvVar Configuration"
```

| | Pod | ConfigMap |
|---|---|---|
| 핵심 필드 | `spec` (뭘 실행할지) | `data` (무슨 값을 담을지) |
| 하는 일 | 컨테이너 실행 | 데이터 보관만 |
| 스코프 | 네임스페이스 | 네임스페이스 |

ConfigMap은 네임스페이스 단위로 원하는 만큼 만들 수 있고, **여러 Pod이 하나를 공유**하는 것이 일반적이다(Pod:ConfigMap = N:M). 단, 다른 네임스페이스의 ConfigMap은 참조할 수 없다. 실무에서는 이 제약을 역이용해 네임스페이스마다 같은 이름의 ConfigMap을 두고 내용만 환경별로 다르게 채운다 — 같은 배포 YAML이 어느 네임스페이스에서든 "자기 동네" 설정을 찾아 쓰게 된다.

간접 참조(ConfigMap/Secret)의 장점은 **설정을 Pod 정의와 독립적으로 관리**할 수 있다는 것이다. 명함에 집 주소를 인쇄하는 대신 "연락처는 홈페이지 참조"라고 적는 것과 같다 — 이사를 가도 명함을 다시 찍을 필요가 없다.

| 방식 | 언제 쓰나 |
|---|---|
| `value` (직접) | 단순하고 안 민감한, 이 Pod만 쓰는 값 |
| `configMapKeyRef` | 여러 곳에서 공유하는 일반 설정 |
| `secretKeyRef` | 민감한 값 — 단, 아래 3.4의 한계를 반드시 알고 쓸 것 |

### 3.4 환경 변수는 안전하지 않다

위 예제에서 SEED는 Secret에서 온다. 유효한 사용법이지만, 여기서 반드시 짚어야 할 함정이 있다.

```
위험의 본질은 "출발지"가 아니라 "도착지"다

출발지                도착지
─────────            ─────────────
value       ─┐
ConfigMap   ─┤
Secret      ─┼──→  환경 변수 ⚠️  도착하면 전부 동일하게 노출
envFrom     ─┘       │
                     ├─ kubectl exec pod -- env 로 즉시 조회
                     ├─ 자식 프로세스에 무조건 자동 상속
                     └─ 크래시 시 환경 변수 전체 덤프 → 로그 유출

Secret      ────→  볼륨(파일) ✅  도착지가 다르면 위험도 다르다
```

Secret이라는 금고에서 꺼냈어도, **환경 변수라는 투명 봉지에 담는 순간** 보호는 풀린다. `kubectl exec my-pod -- env` 한 줄이면 값이 그대로 보이고, 앱이 실행한 모든 자식 프로세스가 값을 물려받으며, 많은 프레임워크와 에러 수집 도구가 크래시 시 환경 변수 전체를 덤프한다.

**민감한 값은 Secret을 볼륨(파일)으로 마운트하는 것이 정석이다.**

```yaml
spec:
  containers:
  - name: random-generator
    volumeMounts:
    - name: secret-vol
      mountPath: /etc/secrets      # 이 경로 아래 키별로 파일이 생김
      readOnly: true
  volumes:
  - name: secret-vol
    secret:
      secretName: random-generator-secret
      defaultMode: 0400            # 파일이라 권한 제어가 가능 — 환경 변수엔 없는 개념
```

| 유출 경로 | 환경 변수 | 볼륨(파일) |
|---|---|---|
| `env` / `/proc/1/environ` 조회 | 노출 ❌ | 안 보임 ✅ |
| 자식 프로세스 자동 상속 | 무조건 상속 ❌ | 경로를 알고 직접 읽어야 함 ✅ |
| 크래시 로그 환경 덤프 | 딸려 나감 ❌ | 대상 아님 ✅ |
| 파일 권한 제어 | 개념 없음 ❌ | 0400 등 가능 ✅ |
| 값 갱신 | 재시작 필요 ❌ | 자동 갱신 (tmpfs, 앱이 재로딩 시 무중단 교체) ✅ |

판단 기준은 하나만 기억하면 된다. **"이 값이 로그에 찍혀도 괜찮은가?"** — 괜찮으면(포트, 경로, 로그레벨) 환경 변수, 안 되면(비밀번호, 토큰, API 키) 볼륨이다.

### 3.5 기본값에 대하여

기본값은 존재조차 모르는 설정을 골라야 하는 부담을 없애준다. Spring Boot의 포트 8080처럼, **설정보다 관례(convention over configuration)** 패러다임의 핵심이기도 하다. 하지만 진화하는 애플리케이션에서는 안티패턴이 될 수 있다.

```
😱 기본값 변경의 파장

v1.0: 타임아웃 기본값 = 30초
  → 수백 명이 아무 설정 없이 사용 중 (암묵적으로 30초에 의존)

v2.0: 기본값을 5초로 변경
  → 아무것도 안 바꾼 사용자들의 앱이 갑자기 타임아웃 폭발
  → 설정 파일 어디에도 "30초"가 없었으므로 원인 추적도 어려움
```

기본값은 코드/이미지 안에 하드코딩된 값이라 바꾸려면 재빌드가 필요하고, 무엇보다 기본값에 조용히 의존하던 사용자들이 변경 시 반드시 놀라게 된다. 그래서 책의 처방은 세 가지다.

| 처방 | 내용 |
|---|---|
| **메이저 버전업** | 기본값 변경은 호환성 파괴다 — 시맨틱 버저닝에서 메이저 번호를 올려 요란하게 알려라 |
| **Fail fast** | 어중간한 기본값은 제거하고, 값이 없으면 시작 시 에러를 내라 — 조용히 이상하게 도는 것보다 일찍 시끄럽게 죽는 게 낫다 |
| **90% 규칙** | 오래 갈 거라 90% 확신 못 하는 값은 처음부터 기본값을 주지 마라 |

비밀번호와 DB 접속 파라미터는 기본값을 주지 말아야 할 대표 후보다 — 환경 의존적이라 예측이 불가능하고, 비밀번호에 예측 가능한 기본값이 있다는 것 자체가 보안 사고다(공유기 `admin/admin`을 떠올려보라). 덤으로, 기본값이 없으면 모든 설정이 명시적으로 적히므로 **설정 파일 자체가 살아있는 문서**가 된다.

### 3.6 편의 기능 3종: envFrom, Downward API, 종속 변수

**① envFrom — 하나씩 말고, 통째로**

```yaml
# 키가 20개면 configMapKeyRef를 20번 반복? → envFrom으로 한 방에
envFrom:
- configMapRef:
    name: random-generator-config   # 안의 모든 키가 각각 환경 변수로 자동 주입
```

YAML이 극적으로 짧아지지만, 뭐가 들어오는지 YAML만 봐서는 안 보인다는 단점이 있다. 특히 **Secret에 envFrom을 쓰는 것은 신중해야 한다** — 필요 없는 비밀까지 전부 유입되고(최소 권한 위반), Secret에 키가 추가되면 YAML 수정 없이도 새 비밀이 컨테이너에 흘러들며, 크래시 덤프 한 번에 비밀 전체 세트가 유출된다.

**② Downward API — 실행 시점에만 아는 "내 정보"**

Pod 이름이나 IP는 Pod가 뜨기 전엔 존재하지 않는 값이라 ConfigMap에 미리 적어둘 수 없다. Downward API는 Kubernetes가 실행 시점에 이런 메타데이터를 아래로 내려주는(downward) 메커니즘이다.

```yaml
env:
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name       # 내 Pod 이름 — Deployment가 붙인 랜덤 접미사까지 포함
- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP        # 내 IP — 스케줄링 후에야 배정되는 값
```

로그에 자기 Pod 이름을 찍는 등, "내가 누구인지" 알아야 하는 앱에 유용하다. 단, 노드 이름·서비스 어카운트·라벨 전체 같은 과한 정보까지 노출하면 컨테이너 침해 시 공격자에게 클러스터 정찰 정보를 주는 셈이 되므로, 앱이 실제로 필요한 필드만 내려주는 것이 원칙이다.

**③ 종속 변수 — 변수로 변수 만들기**

```yaml
# Example 19-5. 종속 환경 변수
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    env:
    - name: PORT
      value: "8181"                  # ① 고정값 — 작성 시점에 아는 값
    - name: IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP    # ② Downward API — 실행 시점에만 아는 값
    - name: MY_URL
      value: "https://$(IP):$(PORT)" # ③ 앞서 정의된 IP, PORT를 조합 → https://10.1.2.3:8181
```

이 예제의 묘미는 **작성 시점에 알 수 없는 값(Pod IP)까지 재료로 삼아, 실행 시점에 완성품(URL)을 자동 조립**한다는 데 있다. 앱 코드에서 IP를 조회하고 문자열을 이어붙이는 로직이 필요 없다.

**⚠️ 순서 함정 — 조용한 실패**

```yaml
# ❌ 잘못된 순서
env:
- name: MY_URL
  value: "https://$(IP):8181"   # IP가 아직 정의 안 됨
- name: IP
  value: "10.1.2.3"

# 결과: 에러가 나지 않는다!
# MY_URL = "https://$(IP):8181"  ← 치환 안 되고 글자 그대로 들어감
```

`$( )`는 목록에서 **먼저(위에)** 정의된 변수와 envFrom으로 가져온 변수만 참조할 수 있다. 순서가 틀려도 에러 없이 문자 그대로 들어가므로, 한참 뒤 "왜 접속이 안 되지?"로 발견되는 전형적인 조용한 실패다. 또 하나 — 쉘의 `${VAR}`가 아니라 **소괄호 `$(VAR)`** 문법이다. 치환은 컨테이너 시작 시점에 단 한 번 일어난다.

**⚠️ 보안 관점** — 종속 변수 자체는 배관일 뿐이다. 포트·IP 같은 공개 값을 흘리면 안전하지만, `postgres://$(USER):$(PASSWORD)@host` 같은 접속 URL 조립은 비밀번호를 두 군데(원본 변수 + URL)에 노출시키고, 접속 URL은 에러 로그에 특히 잘 찍힌다. 비밀이 섞인 조립은 하지 말 것.

### 3.7 command에서의 환경 변수 치환

같은 `$( )` 문법을 컨테이너의 **시작 명령어**에도 쓸 수 있다.

```yaml
# Example 19-6. command 정의에서 환경 변수 사용
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - name: random-generator
    image: k8spatterns/random-generator:1.0
    command: [ "java", "RandomRunner", "$(OUTPUT_FILE)", "$(COUNT)" ]  # ① 시작 명령어에서 참조
    env:
    - name: OUTPUT_FILE
      value: "/numbers.txt"          # ② 명령어에 치환될 변수 정의
    - name: COUNT
      valueFrom:
        configMapKeyRef:
          name: random-config
          key: RANDOM_COUNT
```

```
작성:       java RandomRunner $(OUTPUT_FILE) $(COUNT)
              ↓ 컨테이너 시작 직전, Kubernetes가 치환
실제 실행:   java RandomRunner /numbers.txt 12345
```

이 방식의 진짜 가치는 **환경 변수를 읽을 줄 모르는 앱**에게 있다. 명령줄 인자(`args[0]`, `args[1]`)로만 설정을 받는 레거시 앱·CLI 도구도, command 치환을 통하면 **코드 한 줄 수정 없이** ConfigMap 기반 설정 체계에 편입된다. 앱은 자기가 ConfigMap과 엮인 줄도 모른다.

주의: 이 command는 쉘을 거치지 않으므로 쉘의 `${VAR}` 치환은 일어나지 않는다. Kubernetes 자신이 `$(VAR)`만 치환한다 — 중괄호로 쓰면 역시 에러 없이 문자 그대로 들어간다.

### 레퍼런스

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>종속 변수의 순서 규칙과 <code>$(VAR_NAME)</code> 문법은 Kubernetes 공식 문서 <strong>"Define Dependent Environment Variables"</strong>에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "Note that order matters in the <code>env</code> list."
  </blockquote>
  <div>[해석] "<code>env</code> 목록에서는 순서가 중요하다는 점에 유의하라." — 공식 문서는 참조 대상이 목록의 더 아래에 정의되어 있으면 "정의된" 것으로 취급되지 않고, 해석되지 못한 참조는 일반 문자열로 처리되며, 잘못 파싱된 환경 변수가 있어도 컨테이너 시작 자체는 막히지 않는다고 설명한다. <code>$$(VAR_NAME)</code>으로 이스케이프하면 참조 여부와 무관하게 절대 확장되지 않는다는 규칙도 함께 다룬다.</div>
  <div style="margin-top:10px;">공식 예제 Pod의 로그로 세 케이스가 한눈에 검증된다:</div>
  <pre style="margin:8px 0;overflow-x:auto;"><code>UNCHANGED_REFERENCE=$(PROTOCOL)://172.17.0.1:80   ← 순서 위반: 글자 그대로
SERVICE_ADDRESS=https://172.17.0.1:80              ← 올바른 순서: 정상 치환
ESCAPED_REFERENCE=$(PROTOCOL)://172.17.0.1:80      ← $$ 이스케이프: 의도적 미치환</code></pre>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/tasks/inject-data-application/define-interdependent-environment-variables/">kubernetes.io — Define Dependent Environment Variables</a></div>
  <div>→ <a href="https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/">kubernetes.io — Define Environment Variables for a Container</a></div>
  <div>→ <a href="https://12factor.net/config">12factor.net — III. Config: Store config in the environment</a></div>
</div>
{{< /rawhtml >}}

---

## 4. Discussion

환경 변수는 쉽고, 모두가 알고, 컨테이너 개념(불변 이미지 + 런타임 주입)에 매끄럽게 대응하며, 모든 런타임 플랫폼이 지원한다. 하지만 **안전하지 않고, 적당한(decent) 개수의 설정까지만 감당**한다.

### 전체 메커니즘 정리

| 메커니즘 | 문법 | 시점 | 용도 / 주의 |
|---|---|---|---|
| **Dockerfile 기본값** | `ENV KEY value` | 빌드 | 안전한 출발점 — 값 변경엔 재빌드 필요 |
| **Docker 오버라이드** | `docker run -e` | 런타임 | 재빌드 없이 환경별 값 교체 |
| **직접 지정** | `env` + `value` | 런타임 | 단순·비민감·Pod 전용 값 |
| **ConfigMap 참조** | `configMapKeyRef` | 런타임 | 공유 설정, Pod 정의와 분리 관리 |
| **Secret 참조** | `secretKeyRef` | 런타임 | YAML/Git 노출은 막지만 런타임 노출은 못 막음 ⚠️ |
| **통째 주입** | `envFrom` | 런타임 | 키 많을 때 편리 — Secret엔 신중히 |
| **Downward API** | `fieldRef` | 런타임 | Pod 이름·IP 등 실행 시점 정보 |
| **종속 변수** | `$(VAR)` | 시작 시 1회 | 변수 조합 — 순서 위반 시 조용한 실패 ⚠️ |
| **command 치환** | `command` 내 `$(VAR)` | 시작 시 1회 | 인자만 받는 앱을 무수정 편입 |
| **Secret 볼륨** | `volumeMounts` | 런타임 | 민감 값의 정석 — 권한 제어·무중단 갱신 ✅ |

이제 한계를 세 가지 축으로 정리한다.

### 4.1 규모의 한계와 Spring Boot 프로파일 안티패턴

설정이 수십 개로 늘면 환경 변수의 구조적 약점이 드러난다 — 계층 구조가 없고(전부 평평한 이름-값), 타입이 없고(전부 문자열), nginx.conf 같은 파일 형태의 복잡한 값은 사실상 담을 수 없다.

이때 많은 팀이 쓰는 우회책이 있다. **환경별 설정 파일을 이미지 안에 전부 넣고, 환경 변수 하나로 선택**하는 방식 — Spring Boot 프로파일이 대표적이다.

```
[이미지 안]
application-dev.yaml    ← 개발 설정 80개
application-prod.yaml   ← 운영 설정 80개

[환경 변수는 스위치 1개만]
SPRING_PROFILES_ACTIVE=prod
```

환경 변수 80개가 1개로 줄었으니 똑똑해 보인다. 하지만 이것은 이 장이 처음부터 피하려던 상태로의 회귀다 — **설정 파일들이 다시 이미지 안에 갇혔다.** 스위치만 외부화됐지 알맹이는 내부화된 것이다.

```
부작용 ①: dev 설정 한 줄 수정 → 이미지 재빌드 → 운영까지 새 이미지
          ("빌드 없이 설정 변경"이라는 목표가 무너짐)

부작용 ②: 운영에 배포된 이미지 안에 개발 설정이,
          개발자 손의 이미지 안에 운영 정보가 동봉됨
```

책은 이 구성을 권장하지 않는다(설정은 항상 애플리케이션 외부에). 올바른 방향은 파일 관리라는 발상은 유지하되 **파일을 이미지 밖 — 즉 ConfigMap에 두고 볼륨으로 마운트**하는 것이다(다음 장). 그리고 이런 우회책이 존재한다는 사실 자체가, **환경 변수는 소~중규모 설정 전용**이라는 한계의 증거다.

### 4.2 파편화 — "이 값 어디서 온 거야?"

환경 변수는 어디서나 설정할 수 있다는 장점이 그대로 뒤집혀 단점이 된다 — 실제로 아무 데서나 설정되기 때문이다.

```
LOG_LEVEL 하나가 설정될 수 있는 곳

① 베이스 이미지의 Dockerfile ENV
② 내 앱의 Dockerfile ENV          ← ①을 덮어씀
③ Pod YAML의 env: value           ← ②를 덮어씀
④ ConfigMap (configMapKeyRef)
⑤ Secret (secretKeyRef)
⑥ envFrom 통째 유입
⑦ 컨테이너 시작 스크립트의 export
```

중앙 집중된 정의 장소가 없으면, 장애 상황에서 값 하나의 출처를 찾느라 온 시스템을 뒤지게 된다. 이 문제의 처방 역시 다음 장으로 이어진다 — 설정을 한 리소스(ConfigMap)에 모아 **출처를 추적 가능하게** 만드는 것.

### 4.3 불변성의 역설 — 못 바꾸는 게 장점이다

환경 변수는 컨테이너 시작 시점에 박제되어 실행 중에는 변경할 수 없다. 운영 중 로그 레벨을 "핫하게" 올려 튜닝할 수 없다는 건 분명 단점이다. 그런데 많은 사람이 이를 오히려 장점으로 본다 — **설정에까지 불변성이 확장**되기 때문이다.

```
😱 핫 변경이 가능한 세상의 흔한 사고

운영자가 급하다고 실행 중인 서버 설정을 손으로 수정 (기록 없음)
→ 3주 뒤 Pod 재시작 → 손 수정분 증발 → "예전엔 됐는데 왜 안 되지???"
→ 아무도 원인을 모르는 눈송이 서버(snowflake server) 탄생

😊 불변 방식

설정 변경의 유일한 경로: YAML 수정 → 새 Pod으로 교체 (롤링 업데이트)
→ YAML 수정은 Git에 기록됨
→ 지금 도는 모든 Pod의 설정 = YAML에 적힌 그대로. 예외 없음.
```

이것이 "항상 정의되고 잘 알려진(defined and well-known) 설정 상태"의 의미다. 몰래 고친 설정이 존재할 수 없으므로, "지금 운영에 뭐가 돌고 있어?"라는 질문의 답이 항상 "YAML 봐. 그게 전부야"가 된다. 그리고 Kubernetes에서는 롤링 업데이트가 무중단으로 Pod을 교체해주므로, "재시작"이 아프지 않다 — 불변성의 장점만 챙길 수 있는 것이다.

```
이 장을 관통하는 철학
이미지도 불변, 설정도 불변 → 바꾸고 싶으면 고치지 말고 교체하라
```

### 핵심 메시지

```
환경 변수의 몫: 적은 수의, 단순한, 안 민감한 키-값 설정
그 너머는 다음 패턴들의 영역이다

Configuration Resource   → ConfigMap/Secret을 제대로 (특히 볼륨 마운트)
Immutable Configuration  → 설정 자체를 불변 이미지로 버전 관리
Configuration Template   → 템플릿 + 환경별 값으로 실행 시점에 설정 생성
```

> EnvVar Configuration은 **"설정 외부화의 최소 비용 진입점"** 이다.
> 빌드 시 기본값 + 런타임 오버라이드 패턴으로 불변 이미지 철학을 지키되,
> 보안(도착지가 환경 변수인 순간 노출), 규모(평평한 키-값의 한계), 파편화(출처 추적 불가)의
> 경계선을 넘는 순간 다음 패턴으로 넘어가야 한다.