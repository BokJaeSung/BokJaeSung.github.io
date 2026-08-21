---
series: ["K8sPatterns"]
title: "K8sPatterns.22 Configuration Template"
date: 2026-08-21T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "configuration", "gomplate"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.22 Configuration Template'
  relative: true
summary: "큰 설정 파일에 빈칸을 뚫어 템플릿으로 만들고, Init 컨테이너 안의 Gomplate가 ConfigMap 값으로 빈칸을 채워 시작 시점에 완성본을 찍어내는 법."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-configmap에-통째로-넣을-때-부딪히는-벽" style="color:var(--secondary,inherit);text-decoration:none;">2.1 ConfigMap에 통째로 넣을 때 부딪히는 벽</a></div>
    <div><a href="#22-진짜-문제는-중복--998줄이-세-번-복사된다" style="color:var(--secondary,inherit);text-decoration:none;">2.2 진짜 문제는 중복 — 998줄이 세 번 복사된다</a></div>
  </div>
  <div><a href="#3-solution" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-발상--공통은-템플릿으로-차이만-configmap으로" style="color:var(--secondary,inherit);text-decoration:none;">3.1 발상 — 공통은 템플릿으로, 차이만 ConfigMap으로</a></div>
    <div><a href="#32-빈칸은-언제-채우나--entrypoint-vs-init-컨테이너" style="color:var(--secondary,inherit);text-decoration:none;">3.2 빈칸은 언제 채우나 — ENTRYPOINT vs Init 컨테이너</a></div>
    <div><a href="#33-빈칸의-실제-모습--go-템플릿과-gomplate" style="color:var(--secondary,inherit);text-decoration:none;">3.3 빈칸의 실제 모습 — Go 템플릿과 Gomplate</a></div>
    <div><a href="#34-두-줄짜리-dockerfile--in-params-out-규약" style="color:var(--secondary,inherit);text-decoration:none;">3.4 두 줄짜리 Dockerfile — /in, /params, /out 규약</a></div>
    <div><a href="#35-configmap--환경마다-같은-이름-다른-값" style="color:var(--secondary,inherit);text-decoration:none;">3.5 ConfigMap — 환경마다 같은 이름, 다른 값</a></div>
    <div><a href="#36-deployment-명세--볼륨-둘-문패-셋" style="color:var(--secondary,inherit);text-decoration:none;">3.6 Deployment 명세 — 볼륨 둘, 문패 셋</a></div>
    <div><a href="#37-실행-흐름--합치기의-정체는-빈칸-치환-복사" style="color:var(--secondary,inherit);text-decoration:none;">3.7 실행 흐름 — "합치기"의 정체는 빈칸 치환 복사</a></div>
    <div><a href="#38-디버깅--완성본을-눈으로-확인하기" style="color:var(--secondary,inherit);text-decoration:none;">3.8 디버깅 — 완성본을 눈으로 확인하기</a></div>
  </div>
  <div><a href="#4-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-dry와-드리프트-차단" style="color:var(--secondary,inherit);text-decoration:none;">4.1 DRY와 드리프트 차단</a></div>
    <div><a href="#42-대가와-판단-기준" style="color:var(--secondary,inherit);text-decoration:none;">4.2 대가와 판단 기준</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Configuration Template 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

큰 설정 파일에 "빈칸"을 뚫는다 — 공통은 템플릿 한 곳에, 환경별 차이만 ConfigMap에

  /in (템플릿, 이미지에 내장)      /params (값, ConfigMap 마운트)
        \                              /
         \        읽기            읽기
          \                          /
           Init 컨테이너 안의 Gomplate  ← 시작 시점에 빈칸 채우기
                    │ 쓰기
                    ▼
           /out = emptyDir = 앱의 /config
                    │
                    ▼
           앱은 완성된 설정 파일을 "그냥 읽는다"
```

21장 Immutable Configuration은 "환경마다 설정 이미지를 통째로 하나씩" 만들었다. 그런데 그 환경별 설정들을 나란히 놓고 보면 대부분 **99%가 같고 몇 줄만 다르다**. 통째로 여러 벌 만드는 것은 낭비이자 위험이다. **Configuration Template 패턴**은 설정 파일에서 환경마다 달라지는 자리만 빈칸으로 뚫어 **템플릿**으로 만들고, 애플리케이션 시작 시점에 환경별 파라미터를 채워 **그 환경 전용 완성본을 즉석에서 생성**한다.

이 장의 재미는 부품들의 역할 분담에 있다. 템플릿은 어디에 두는지, 빈칸에 넣을 값은 누가 어떤 경로로 배달하는지, 완성본은 어떻게 앱 컨테이너 손에 들어가는지 — 조각이 많아 보이지만 하나씩 따라가면 전부 이미 아는 부품(Init 컨테이너, ConfigMap 볼륨, emptyDir)의 재조합이다.

---

## 2. Problem

### 2.1 ConfigMap에 통째로 넣을 때 부딪히는 벽

20장의 표준 답안대로 설정 파일을 ConfigMap에 직접 넣는 방식은, 설정이 크고 복잡해지는 순간 익숙한 두 개의 벽에 다시 부딪힌다.

```
① 문법 충돌   — WildFly의 standalone.xml 같은 수백 줄짜리 XML을 YAML 안에
               문자열로 중첩해야 한다. 따옴표·들여쓰기·특수문자 하나에
               리소스 정의 전체가 깨진다. (21장 2.1의 "중첩 지옥" 재등장)

② 크기의 벽   — ConfigMap/Secret 값의 총합은 1MB. etcd가 부과하는 제한이라
               어떤 옵션으로도 못 넘는다. 대형 설정 세트는 아예 안 들어간다.
```

여기까지는 21장에서 본 것과 같은 벽이다. 그런데 이 장은 세 번째 문제를 정면에 세운다.

### 2.2 진짜 문제는 중복 — 998줄이 세 번 복사된다

큰 설정 파일은 환경이 달라도 **아주 조금만 다르다**. 이 유사성이 역설적으로 문제를 만든다. 환경별로 ConfigMap을 따로 만들면 이렇게 된다.

```
개발용 ConfigMap (1000줄)          테스트용 (1000줄)            운영용 (1000줄)
├─ 998줄: 공통 내용                ├─ 998줄: 공통 (복사!)        ├─ 998줄: 공통 (또 복사!)
└─ 2줄: DB주소 = 10.0.0.1         └─ 2줄: DB주소 = 10.0.0.2    └─ 2줄: DB주소 = 10.0.0.3
```

실제로 다른 것은 2줄뿐인데 998줄이 세 벌 존재한다. 공통 부분을 고칠 일이 생기면 세 군데를 전부, 빠짐없이, 똑같이 고쳐야 한다. 한 곳이라도 누락되는 순간 환경들의 설정이 미묘하게 어긋나기 시작한다 — 21장 2.2에서 본 **드리프트**가 바로 여기서 자란다. "개발에선 되는데 운영에서만 터져요"류 버그의 온상이다.

즉 이 장의 목표는: **공통 부분을 딱 한 곳에만 존재하게 만들면서, 1MB 제한과 문법 충돌도 함께 피하는 것**.

---

## 3. Solution

### 3.1 발상 — 공통은 템플릿으로, 차이만 ConfigMap으로

결혼식 초대장 100장을 만들 때 100장을 전부 손으로 쓰는 사람은 없다. **양식 한 장**에 빈칸을 뚫고 이름만 바꿔 넣는다. 이 패턴이 정확히 그것이다.

```
저장 위치가 뒤집힌다

공통 998줄  →  ConfigMap ❌   →  템플릿 파일로 만들어 "이미지"에 내장 ✅
다른 2줄    →  이미지 ❌      →  작은 값만 ConfigMap에 ✅
```

이러면 세 문제가 동시에 풀린다. ConfigMap에는 몇 줄짜리 값만 들어가니 **1MB 제한과 YAML 문법 충돌을 회피**하고, 공통 부분은 템플릿 한 곳에만 존재하니 **중복이 사라진다**. 남은 질문은 하나 — 흩어진 두 조각(템플릿 + 값)을 **누가, 언제 합쳐서** 앱이 읽을 완성본을 만드는가.

### 3.2 빈칸은 언제 채우나 — ENTRYPOINT vs Init 컨테이너

합치는 시점은 **애플리케이션 시작 직전**이다. 앱이 켜지기 전에 완성본이 정해진 위치에 놓여 있어야 하고, 앱은 그것이 템플릿이었는지도 모른 채 평범한 설정 파일로 읽는다. 방법은 둘이다.

```
방법 ①  ENTRYPOINT 방식
  Dockerfile의 ENTRYPOINT를 "템플릿 처리 → 앱 실행" 스크립트로 교체
  파라미터는 환경 변수로 받는다 (ConfigMap → env 주입도 가능하나, 반드시 env를 "거친다")
  단점: 앱 이미지를 직접 뜯어고쳐야 한다

방법 ②  Init 컨테이너 방식  ★ Kubernetes에서의 정답
  템플릿 처리를 별도의 Init 컨테이너가 담당하고, 결과를 emptyDir로 앱에 넘긴다
  ConfigMap을 볼륨으로 마운트해 "파일 그대로, 직접" 읽는다
  앱 이미지는 공식 이미지 순정 그대로
```

| | ① ENTRYPOINT | ② Init 컨테이너 |
|---|---|---|
| 처리 위치 | 앱 이미지 안의 스크립트 | 별도 준비 전용 컨테이너 |
| 앱 이미지 수정 | 필요 | **불필요** |
| 파라미터 경로 | ConfigMap → **환경 변수** → 스크립트 | ConfigMap → **볼륨(파일)** → 처리기 |
| 파라미터 형태 | 단순 `이름=값`만 편함 | 여러 줄·복잡한 값도 파일이라 자유 |

책이 ②를 "가장 매력적(most appealing)"이라 하는 근거가 표에 다 있다 — **ConfigMap을 directly(직접) 쓸 수 있고, 앱 이미지를 안 건드린다**. 21장에서 배달원(Init)과 게시판(emptyDir)을 이미 만들어봤으니, 이 장은 그 배달원에게 "복사" 대신 "**빈칸 채우기**"라는 더 똑똑한 일을 시키는 셈이다.

### 3.3 빈칸의 실제 모습 — Go 템플릿과 Gomplate

예제는 WildFly 서버, 환경은 개발/운영 둘, 차이는 단 하나 — 로그 줄 앞에 `DEVELOPMENT:` 또는 `PRODUCTION:` 접두어가 붙는 것뿐이다. 일부러 극단적으로 사소한 차이를 골랐다. "이거 하나 때문에 설정 전체를 두 벌 관리할 거냐"를 보여주기 위해서.

수백 줄짜리 standalone.xml에서 빈칸은 이 한 줄이다.

```xml
<!-- Example 22-1. 로그 설정 템플릿 (standalone.xml 중 일부) -->
<formatter name="COLOR-PATTERN">
  <pattern-formatter pattern="{{(datasource "config").logFormat}}"/>
</formatter>
```

```
{{ (datasource "config").logFormat }}
│   │                   │
│   │                   └ 그 YAML 안의 logFormat 키 값을 꺼내라 (붙여 쓴다)
│   └ "config"라는 이름의 데이터 소스(= 마운트된 ConfigMap 파일)를 열어라
└ Go 템플릿 문법의 빈칸 표시 — "나중에 채울 자리"
```

빈칸을 채우는 도구가 **Gomplate**(Go)다. Tiller(Ruby) 같은 대안도 있지만 역할은 같다 — **템플릿과 값을 받아 빈칸이 채워진 완성본 파일을 만드는 것**, 딱 그것뿐이다. 우편물 자동 인쇄기라고 생각하면 된다. 양식(템플릿)의 빈칸에 명단(ConfigMap)의 이름을 넣어 찍어낼 뿐, 편지 내용이 뭔지는 모른다.

역할 분담이 중요하다. ConfigMap 안의 문자열을 "이건 YAML이고 logFormat 키의 값은 이거군"이라고 **해석하는 것은 순전히 Gomplate**다. Kubernetes는 우체부처럼 내용을 읽지 않고 파일로 배달만 한다.

### 3.4 두 줄짜리 Dockerfile — /in, /params, /out 규약

Init 컨테이너 이미지는 놀랄 만큼 간단하다.

```dockerfile
# Example 22-2. 템플릿 이미지의 Dockerfile
FROM k8spatterns/gomplate     # ① 도구(Gomplate + 실행 스크립트)가 깔린 범용 베이스
COPY in /in                   # ② 개발자 PC의 in/ 폴더(템플릿)를 이미지 /in에 굽기
```

`COPY in /in`의 두 `in`은 서로 다른 곳이다 — 왼쪽은 **빌드하는 개발자 PC의 폴더**(Dockerfile 옆), 오른쪽은 **이미지 안 경로**. 개발자가 작성한 standalone.xml 템플릿이 이 한 줄로 이미지에 박제된다. 베이스가 도구를, COPY가 재료를 담당하니 두 줄로 끝난다.

베이스 이미지는 **폴더 세 개로 일하는 규약**을 갖고 있다. 컨베이어 벨트다.

```
📥 /in      재료 투입구   템플릿 (이미지에 내장 — 빌드 때 COPY로. 마운트 불필요!)
📋 /params  주문서 함     Gomplate 데이터 소스인 YAML 파일 (ConfigMap 볼륨 마운트)
📤 /out     완성품 출구   처리된 설정 파일 (emptyDir — 앱 컨테이너와 공유)
```

| 폴더 | 채워지는 시점 | 방법 | 왜 |
|---|---|---|---|
| `/in` | **이미지 빌드 때** (미리) | Dockerfile `COPY` | 공통이라 모든 환경 동일 → 구워도 됨 |
| `/params` | **Pod 실행 때** (나중) | ConfigMap 볼륨 마운트 | 환경마다 다름 → 구우면 환경별 이미지가 됨 |
| `/out` | **Pod 실행 때** (나중) | emptyDir 마운트 | 다른 컨테이너와 공유해야 함 → 이미지 안 폴더론 불가 |

이 규약 덕에 베이스는 재사용된다. WildFly든 Nginx든 **템플릿만 갈아 끼우면(COPY 한 줄)** 어떤 앱의 설정 생성기로든 변신한다.

**빌드 전후로 폴더가 어떻게 바뀌는지** 눈으로 따라가 보자.

```
① 개발자 PC — 이미지 빌드하는 곳 💻

📁 작업 폴더/ (docker build 실행하는 곳)
├── Dockerfile                    ← "FROM gomplate / COPY in /in" 2줄
└── in/                           ← 템플릿 보관 폴더 (COPY의 왼쪽 "in")
    └── standalone.xml            ← 빈칸 뚫린 템플릿 (원본!)
                                     ...공통 설정 수백 줄...
                                     pattern="{{(datasource "config").logFormat}}"

        │  docker build
        ▼

② init container 이미지 안 — 빌드 결과물 📦

📦 k8spatterns/example-config-cm-template-init 이미지
├── (Gomplate 실행 파일)          ← FROM 베이스에서 물려받음
├── (엔트리포인트 스크립트)        ← FROM 베이스에서 물려받음
├── in/                           ← COPY in /in 으로 복사됨 ✅
│   └── standalone.xml            ← ①의 템플릿이 여기 박제
├── params/                       ← 텅 빔! (실행 때 마운트로 채워질 자리)
└── out/                          ← 텅 빔! (실행 때 마운트로 채워질 자리)
```

`/params`와 `/out`이 **텅 빈 채로 출하된다**는 것이 이 이미지의 핵심이다. 재료(템플릿)만 굽고 주문서와 완성품 자리는 비워두었기에, 같은 이미지가 개발에도 운영에도 쓰인다.


### 3.5 ConfigMap — 환경마다 같은 이름, 다른 값

두 번째 재료. 환경마다 달라지는 그 값의 실물이다.

```bash
# Example 22-3. 템플릿에 채워 넣을 값을 담은 ConfigMap 생성 (개발 환경)
kubectl create configmap wildfly-cm \
  --from-literal='config.yml=logFormat: "DEVELOPMENT: %-5p %s%e%n"'
```

구조가 **2단계**라는 점을 놓치기 쉽다. ConfigMap의 키가 `config.yml`이고, 그 값이 다시 `logFormat: ...`이라는 YAML 한 줄이다. 볼륨으로 마운트되면 **키가 파일명, 값이 파일 내용**이 되기 때문이다.

```
ConfigMap "wildfly-cm"
└─ 키: config.yml                          ← 마운트되면 /params/config.yml 파일이 된다
    └─ 값: logFormat: "DEVELOPMENT: ..."   ← 그 파일의 내용 (YAML)
                │
                └ 템플릿의 datasource "config" ↔ 파일명 config.yml
                  템플릿의 .logFormat        ↔ YAML 키 logFormat   ← 이름이 전부 맞물린다
```

키에 `.yml` 확장자를 붙인 것도 설계다 — Gomplate가 확장자를 보고 "YAML로 파싱하면 되겠군"을 알아챈다.

주의할 것: 이 명령은 **etcd에 리소스를 등록만** 한다. 아직 어떤 컨테이너와도 연결되지 않았고, 어디에도 파일로 보이지 않는다. 파일이 되는 것은 Pod 정의에서 마운트를 선언하고 Pod가 실행되는 순간이다. 유튜브에 영상을 올렸다고 TV에 나오지 않는 것과 같다 — 채널을 연결하고 전원을 켜야 한다.

그리고 아까 질문의 답 — "어디 ConfigMap에 넣냐". 운영 클러스터에서는 **같은 이름으로, 값만 바꿔** 만든다.

```bash
# 운영 환경 — 이름은 동일, 값만 PRODUCTION
kubectl create configmap wildfly-cm \
  --from-literal='config.yml=logFormat: "PRODUCTION: %-5p %s%e%n"'
```

Pod는 `wildfly-cm`이라는 **이름으로만** 참조하므로, 어느 클러스터에 배포되느냐에 따라 그 장소의 값이 자동으로 쓰인다. 체인 호텔의 공통 안내문 양식과 지점별 금고 — 양식은 하나, 어느 지점에서 인쇄하느냐로 내용이 정해진다.

그러면 실행 시점에 **비어 있던 두 자리가 채워진다.** Init 컨테이너 안에서 본 모습이다.

```
④ Pod 실행 중 — init container 안에서 보이는 구조 (Gomplate 작업 중) 🚀

🔧 init container
├── /in/                              [출처: 이미지 내장 (COPY)]
│   └── standalone.xml                ← 템플릿 (빈칸 있음), 읽기용
│
├── /params/                          [출처: ConfigMap 볼륨 마운트] ★③이 파일로 변신!
│   └── config.yml                    ← 내용: logFormat: "DEVELOPMENT: ..."
│
└── /out/                             [출처: emptyDir 마운트]
    └── standalone.xml                ← Gomplate가 생성한 완성본 (빈칸 채워짐!)
                                         pattern="DEVELOPMENT: %-5p %s%e%n"
```

②에서 텅 비어 있던 `/params`와 `/out`이 마운트로 채워진 것이 보인다. 이미지는 그대로인데 **바깥에서 꽂아준 것만으로** 개발용 완성본이 나왔다. 운영 클러스터라면 `/params/config.yml`의 내용만 `PRODUCTION:`으로 바뀌고 나머지는 전부 동일하다.


### 3.6 Deployment 명세 — 볼륨 둘, 문패 셋

마지막 조각, 모든 재료를 연결하는 설계도다.

```yaml
# Example 22-4. 템플릿 처리기를 Init 컨테이너로 가진 Deployment (.template.spec 부분)
initContainers:
- image: k8spatterns/example-config-cm-template-init  # ① 22-2로 구운 이미지 (템플릿 내장)
  name: init
  volumeMounts:
  - mountPath: "/params"               # ② ConfigMap이 파일로 비치는 창구
    name: wildfly-parameters
  - mountPath: "/out"                  # ③ 완성본을 써낼 출구 = emptyDir
    name: wildfly-config
containers:
- image: jboss/wildfly:10.1.0.Final    # ④ 공식 이미지 순정 그대로 — 이 패턴의 자랑
  name: server
  command:
  - "/opt/jboss/wildfly/bin/standalone.sh"
  - "-Djboss.server.config.dir=/config" # ⑤ "설정은 /config에서 읽어" — 이미지 대신 옵션으로 방향만 튼다
  volumeMounts:
  - mountPath: "/config"               # ⑥ ③과 같은 볼륨을 다른 문패로
    name: wildfly-config
volumes:
- name: wildfly-parameters             # ⑦ 볼륨의 "실체" 선언부 — ConfigMap과의 연결이 바로 여기
  configMap:
    name: wildfly-cm
- name: wildfly-config                 # ⑧ 빈 공유 폴더. Pod 소유, Pod과 함께 소멸
  emptyDir: {}
```

**연결은 두 단계로 나뉘어 적힌다** — 그래서 "ConfigMap 연결하는 데가 없는데?" 하고 놓치기 쉽다. `volumes:`(맨 아래)가 볼륨의 실체를 정하고(⑦ "wildfly-parameters의 정체는 ConfigMap wildfly-cm"), 각 컨테이너의 `volumeMounts:`가 그 볼륨을 자기 경로에 붙인다(② "그걸 내 /params에"). 채널 등록과 각 방 TV에서 채널 틀기가 따로인 것이다. 21장 3.7에서 본 "볼륨의 주인은 Pod, 컨테이너는 이용자"가 여기서도 그대로다.

**같은 볼륨, 다른 문패** — `wildfly-config`(emptyDir)는 실체가 하나인데 마운트가 두 번이다.

```
        📂 wildfly-config (emptyDir, 실체 하나)
       /                              \
  Init 컨테이너에선 "/out"         WildFly에선 "/config"
  (여기에 씀 ✍️)                   (여기서 읽음 👀)
```

Init이 /out에 넣는 순간 그 파일은 이미 WildFly의 /config에 "도착"해 있다. 복사도 전송도 없다 — 애초에 같은 방이니까. 그리고 `/in`은 volumeMounts에 없다는 것도 확인하자. 템플릿은 3.4의 `COPY`로 이미지에 이미 들어 있으니, 실행 시점에 연결할 것이 없다.

### 3.7 실행 흐름 — "합치기"의 정체는 빈칸 치환 복사

이 Deployment를 시작하면:

```
① Pod 생성
   wildfly-cm → wildfly-parameters 볼륨 준비 / emptyDir 생성 (텅 빔)

② Init 컨테이너 실행 — 안에서 Gomplate가 일한다
   /in/standalone.xml 을 한 글자씩 /out 으로 베껴 쓰다가
   {{...logFormat}} 빈칸을 만나면 →
       /params/config.yml (ConfigMap이 비친 파일)을 열어
       logFormat 값 "DEVELOPMENT: %-5p %s%e%n" 을 찾아
       빈칸 자리에 대신 써넣고 → 계속 베껴 쓴다
   완성본이 /out 에 생기면 임무 완료, 종료 👋
   (15장의 보장: Init이 "성공 종료"해야만 다음이 시작된다)

③ WildFly 컨테이너 실행
   -Djboss.server.config.dir=/config 옵션대로 /config 에서 설정을 읽음
   /config = 같은 emptyDir. 완성본이 이미 놓여 있다
   로그: "DEVELOPMENT: INFO  서버 시작됨" 🎉
```

"합치기"는 두 파일을 이어 붙이는 것이 아니다. **템플릿을 베껴 쓰다가 빈칸 자리만 ConfigMap 값으로 갈아 끼우는 치환 복사**다. 원본 템플릿(/in)은 그대로 남고, 새 완성본이 /out에 생긴다. 대필 작가가 원고를 옮겨 적다가 "___"를 만나면 메모지를 보고 채워 넣는 것과 같다.

emptyDir이 Pod와 함께 소멸해도 문제없는 이유도 여기 있다 — 완성본은 템플릿+ConfigMap만 있으면 **언제든 다시 구울 수 있는 빵**이다. Pod 재시작마다 Init이 새로 굽고, 덕분에 그 사이 ConfigMap이 바뀌었다면 최신 값으로 갱신되는 부수 효과까지 있다.

환경 전환은? **이 Deployment는 한 글자도 안 바꾼다.** 21장(3.8)에선 그래도 Init 이미지 이름 한 줄은 바꿔야 했는데, 이 장에선 그마저 없다 — 이미지도 템플릿도 공통이고, 다른 것은 각 클러스터의 ConfigMap 값뿐이니까.

### 3.8 디버깅 — 완성본을 눈으로 확인하기

이 패턴은 부품이 많아 "안 될 때 어디를 봐야 하는지"가 즉각적이지 않다. Init은 일 끝나면 사라지고, 완성본은 emptyDir 안이라 바로 안 보인다. 책의 팁은 **중간 산출물을 직접 열어보는 것**이다.

```
방법 ①  노드에서 직접 (하드코어)
  emptyDir의 실체는 노드 디스크의 이 경로다:
  /var/lib/kubelet/pods/{podid}/volumes/kubernetes.io~empty-dir/
  → 컨테이너가 죽어 있어도 볼 수 있다. 대신 노드 접속 권한 필요

방법 ②  kubectl exec (간편) ⭐
  kubectl exec -it <pod> -- cat /config/standalone.xml
  → 실행 중인 Pod에 들어가 마운트된 /config를 열어본다
```

완성본을 확인하면 문제 단계가 바로 좁혀진다.

```
"로그에 DEVELOPMENT: 접두어가 안 붙어요"
  ├─ /config에 파일이 없다        → Init 실패. Init 로그를 보자
  ├─ {{...}}가 그대로 남아 있다    → Gomplate가 값을 못 찾음. ConfigMap 키 이름/데이터 소스 확인
  └─ 파일도 값도 정상이다          → WildFly 쪽. -Djboss...=/config 옵션 확인
```

### 레퍼런스

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>ConfigMap 크기 제한은 Kubernetes 공식 문서 <strong>"ConfigMaps"</strong>에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "A ConfigMap is not designed to hold large chunks of data. The data stored in a ConfigMap cannot exceed 1 MiB."
  </blockquote>
  <div>[해석] "ConfigMap은 큰 데이터 덩어리를 담도록 설계되지 않았다. ConfigMap에 저장되는 데이터는 1 MiB를 초과할 수 없다." — 2.1의 "크기의 벽"이 이것이며, 같은 문서는 이 한도를 넘는 경우 볼륨 마운트나 별도 서비스 사용을 고려하라고 안내한다. 이 장의 답은 "애초에 큰 부분을 ConfigMap 밖(템플릿)으로 빼는 것"이다.</div>
  <div style="margin-top:10px;">Gomplate 공식 문서는 datasource를 파일·환경 변수 등 다양한 출처에서 읽을 수 있는 값의 원천으로 정의하며, 파일 확장자로 포맷(YAML/JSON 등)을 추론한다고 설명한다 — 3.5에서 키 이름을 <code>config.yml</code>로 지은 이유가 이것이다.</div>
  <div style="margin-top:10px;">Init 컨테이너의 순차·완료 보장("Each init container must complete successfully before the next one starts")은 21장 레퍼런스에서 확인한 그대로이며, 3.7의 "빈 폴더를 볼 틈이 없다"의 근거다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/concepts/configuration/configmap/">kubernetes.io — ConfigMaps</a></div>
  <div>→ <a href="https://docs.gomplate.ca/datasources/">docs.gomplate.ca — Datasources</a></div>
  <div>→ <a href="https://kubernetes.io/docs/concepts/workloads/pods/init-containers/">kubernetes.io — Init Containers</a></div>
</div>
{{< /rawhtml >}}

---

## 4. Discussion

### 4.1 DRY와 드리프트 차단

이 패턴이 사는 가치는 **DRY**(Don't Repeat Yourself — 반복하지 마라)다.

```
패턴 적용 전 ❌                          패턴 적용 후 ✅
공통 998줄 × 환경 수만큼 사본            공통 998줄 = 템플릿 "딱 한 곳"
환경 전환 = ConfigMap 통째 교체          환경 전환 = 작은 값 몇 줄만 다름
공통 수정 = 모든 사본을 빠짐없이         공통 수정 = 템플릿 파일 하나 → 이미지 재빌드
           (하나라도 놓치면 드리프트)              모든 환경에 동일 적용, 어긋날 사본 자체가 없음
```

책의 표현이 정확하다 — 통째 복사는 처음엔 작동하더라도(works *initially*) 시간이 지나며 **어긋날 운명(doomed to diverge)** 이다. 사람이 여러 사본을 완벽하게 동기화하는 일은 언젠가 반드시 실패한다. 템플릿 방식은 어긋날 사본을 없애 **드리프트를 원천 차단**한다. Deployment·이미지·템플릿 전부가 환경 불변이고, 환경 의존적인 것은 ConfigMap의 작은 값들뿐이다.

한 가지 이웃 기술 — OpenShift에서는 리소스 정의(Deployment YAML) 자체를 파라미터화하는 **OpenShift Template**이 있다(21장 3.8에서 이미 사용). 층이 다르다는 점만 구분하면 된다: 이 장의 패턴은 **앱 설정 파일**의 빈칸을, OpenShift Template(일반 K8s에선 Helm/Kustomize)은 **매니페스트**의 빈칸을 채운다. 큰 설정 세트 문제는 후자가 풀어주지 못하며, replicas 수처럼 매니페스트 수준의 환경 차이는 전자가 풀어주지 못한다. 상황에 따라 둘을 함께 쓴다.

### 4.2 대가와 판단 기준

책이 먼저 경고한다 — 이 설정은 더 복잡하고, **잘못될 수 있는 움직이는 부품(moving parts)이 더 많다**.

```
① 부품 수      템플릿 파일 + Go 템플릿 문법 + Init 이미지 빌드 + Gomplate
               + ConfigMap + 볼륨 둘 + 마운트 연결. 기본 패턴은 ConfigMap 하나였다.

② 고장 지점    템플릿 문법 오타, 데이터 소스 이름 불일치, 키 이름 오타,
               마운트 경로 실수 — 어디서든 조용히 어긋날 수 있다. 3.8의 디버깅이 필수 소양.

③ 사용 조건    "애플리케이션이 huge한 구성 데이터를 요구할 때만" 쓰라고 책이 못 박는다.
```

판단 공식은 간단하다.

```
설정 크기 = 큼 (수백 줄~)   AND   환경별 차이 = 아주 작음 (몇 줄)
→ 이 조합일 때만 Configuration Template. 예제가 딱 그랬다 — 수백 줄 중 로그 접두어 하나.
```

| 설정의 모습 | 올바른 도구 |
|---|---|
| 작고 단순, 1MB 이하 | immutable ConfigMap/Secret (20·21장) ✅ |
| 크고, 환경마다 통째로 다르거나 레지스트리 배포가 필요 | Immutable Configuration (21장) |
| **크지만 환경마다 조금씩만 다름** | **Configuration Template (이 장)** ✅ |
| 매니페스트 자체가 환경별로 다름 (replicas 등) | OpenShift Template / Helm / Kustomize |

### 핵심 메시지

```
Configuration Template의 몫: "거대하지만 거의 같은" 설정을 사본 없이 관리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

공통      → 빈칸 뚫린 템플릿으로 Init 이미지에 내장 (/in, COPY 한 줄)
차이      → 환경마다 같은 이름의 ConfigMap에 작은 값만 (/params, 볼륨 마운트)
합치기    → Init 컨테이너 안의 Gomplate가 시작 시점에 빈칸 치환 복사
전달      → /out = emptyDir = 앱의 /config. 같은 방, 다른 문패
앱        → 공식 이미지 순정 그대로. 완성된 파일을 "그냥 읽는다"
환경 전환 → ConfigMap 값만 다르다. Deployment·이미지·템플릿은 한 글자도 안 바뀐다
```

> Configuration Template은 **"거의 같은 큰 설정을 여러 벌 복사하는 대신, 한 벌에 빈칸을 뚫는 답"** 이다.
> 공통은 템플릿으로 Init 이미지에 굽고, 환경별 차이는 ConfigMap의 작은 값으로만 남겨,
> 시작 시점에 Gomplate가 빈칸을 채운 완성본을 emptyDir 게시판에 붙이고 퇴장하게 하라.
> 앱은 그 게시판을 평범한 설정 폴더로 읽을 뿐이고, 환경 전환은 ConfigMap 값 몇 줄로 끝난다.
> 그러나 부품이 많아 고장 지점도 많으니 — 설정이 정말 크고, 차이가 정말 작을 때만 꺼내 들 것.