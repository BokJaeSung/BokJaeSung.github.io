---
series: ["K8sPatterns"]
title: "K8sPatterns.20 Configuration Resource"
date: 2026-08-15T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "configuration"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.20 Configuration Resource'
  relative: true
summary: "설정을 일급 리소스로 — ConfigMap과 Secret의 두 가지 소비 경로(환경 변수/볼륨), 핫 리로드와 드리프트의 명암, Base64가 보안이 아닌 이유, 그리고 immutable까지."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-환경-변수가-남긴-숙제" style="color:var(--secondary,inherit);text-decoration:none;">2.1 환경 변수가 남긴 숙제</a></div>
    <div><a href="#22-간접-계층이라는-해법" style="color:var(--secondary,inherit);text-decoration:none;">2.2 간접 계층이라는 해법</a></div>
  </div>
  <div><a href="#3-solution" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-configmap과-secret--사용법이-같은-쌍둥이" style="color:var(--secondary,inherit);text-decoration:none;">3.1 ConfigMap과 Secret — 사용법이 같은 쌍둥이</a></div>
    <div><a href="#32-configmap-정의와-네이밍-컨벤션" style="color:var(--secondary,inherit);text-decoration:none;">3.2 ConfigMap 정의와 네이밍 컨벤션</a></div>
    <div><a href="#33-kubectl로-만들기--yaml-대필-서비스" style="color:var(--secondary,inherit);text-decoration:none;">3.3 kubectl로 만들기 — YAML 대필 서비스</a></div>
    <div><a href="#34-환경-변수로-소비하기-env와-envfrom" style="color:var(--secondary,inherit);text-decoration:none;">3.4 환경 변수로 소비하기: env와 envFrom</a></div>
    <div><a href="#35-볼륨으로-소비하기-키가-파일이-된다" style="color:var(--secondary,inherit);text-decoration:none;">3.5 볼륨으로 소비하기: 키가 파일이 된다</a></div>
    <div><a href="#36-세밀하게-골라내기-items-path-mode" style="color:var(--secondary,inherit);text-decoration:none;">3.6 세밀하게 골라내기: items, path, mode</a></div>
    <div><a href="#37-핫-리로드의-명암--드리프트" style="color:var(--secondary,inherit);text-decoration:none;">3.7 핫 리로드의 명암 — 드리프트</a></div>
    <div><a href="#38-immutable--수정-금지가-주는-것" style="color:var(--secondary,inherit);text-decoration:none;">3.8 immutable — 수정 금지가 주는 것</a></div>
    <div><a href="#39-secret은-얼마나-안전한가" style="color:var(--secondary,inherit);text-decoration:none;">3.9 Secret은 얼마나 안전한가</a></div>
  </div>
  <div><a href="#4-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-정의와-사용의-분리" style="color:var(--secondary,inherit);text-decoration:none;">4.1 정의와 사용의 분리</a></div>
    <div><a href="#42-golden-hammer가-아니다--크기와-개수의-한계" style="color:var(--secondary,inherit);text-decoration:none;">4.2 Golden hammer가 아니다 — 크기와 개수의 한계</a></div>
  </div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Configuration Resource 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

설정을 "일급 리소스"로 승격시켜 정의와 사용을 분리하라

  [정의]                              [사용 — 결정권은 Pod에 있다]
  ConfigMap (일반 설정)    ─────┬──→  환경 변수    env (개별) / envFrom (전체+prefix)
  Secret    (민감 정보)         └──→  볼륨(파일)   전체 투영  / items+path+mode (선택)
       │
       └─ 사용법 동일. 차이는 Base64 인코딩(≠보안)과 운영상의 특별 취급뿐
```

19장의 환경 변수는 설정 외부화의 최소 비용 진입점이었지만, 규모·파편화·보안의 경계선을 넘는 순간 감당이 안 된다는 것을 확인했다. **Configuration Resource 패턴**은 그 다음 단계다 — 설정 데이터를 Kubernetes의 네이티브 리소스인 **ConfigMap**(일반 데이터)과 **Secret**(기밀 데이터)에 담아, **구성의 라이프사이클을 애플리케이션의 라이프사이클로부터 분리**한다.

이 장의 절반은 두 가지 소비 경로(환경 변수 vs 볼륨)의 사용법이고, 나머지 절반은 그 선택이 만들어내는 운영상의 결과다 — 핫 리로드, 구성 드리프트, 불변성, 그리고 "Secret은 정말 안전한가"라는 질문.

---

## 2. Problem

### 2.1 환경 변수가 남긴 숙제

19장에서 확인한 EnvVar Configuration의 한계를 다시 소환하면:

```
① 규모   — 소수의 변수, 단순한 설정까지만. nginx.conf 전체를 환경 변수에? ❌
② 파편화 — 정의 위치가 사방에 흩어짐. "이 값 어디서 온 거야?"
③ 확신 불가 — OCI 이미지의 ENV조차 Deployment에서 런타임에 덮어써질 수 있음
```

특히 ②가 치명적이다. 설정 데이터는 **한곳에 모여** 있어야지, 여러 리소스 정의 파일에 흩어져 있으면 안 된다. 그렇다고 구성 파일 전체의 내용을 환경 변수 하나에 욱여넣는 것은 말이 되지 않는다 — 줄바꿈, 특수문자, 가독성 전부 재앙이다.

### 2.2 간접 계층이라는 해법

필요한 것은 약간의 **간접 계층(indirection)** 이다. "모든 문제는 간접 계층을 하나 추가하면 해결할 수 있다"는 격언 그대로다.

```
직접 방식                          간접 방식
─────────                         ─────────
Pod 안에 값을 하드코딩              Pod은 ConfigMap을 "참조"만
env:                              env:
- name: DB_HOST                   - name: DB_HOST
  value: "mysql.example.com"        valueFrom:
      ▲                               configMapKeyRef:
  값이 명세에 박힘                        name: app-config  ← 이름을 가리킴
                                        key: db-host
```

한 단계 거쳐 가면(간접), Pod 정의는 건드리지 않고 ConfigMap만 바꿔 설정을 변경할 수 있고, 같은 ConfigMap을 여러 곳에서 재사용할 수 있으며, 환경 변수뿐 아니라 **파일 형태로도** 제공할 수 있다. Kubernetes는 이 간접 계층을 플랫폼 내장 기능으로 제공한다.

---

## 3. Solution

### 3.1 ConfigMap과 Secret — 사용법이 같은 쌍둥이

둘 다 본질은 **키-값 저장소**다. ConfigMap에 대한 설명은 대부분 Secret에 그대로 적용된다. 기술적 차이는 단 하나 — Secret의 값은 **Base64로 인코딩**된다는 것.

여기서 미리 못 박아둘 것: **Base64는 암호화가 아니다.** 누구나 `base64 -d` 한 줄로 원문을 볼 수 있는, 보안 관점에서 평문과 동일한 인코딩이다. Base64의 진짜 목적은 TLS 인증서 같은 **바이너리 데이터를 텍스트 기반 YAML에 담기 위한 포장**이다. Secret이 그럼에도 더 안전한 이유는 3.9에서 따로 다룬다.

ConfigMap의 키는 두 가지 방식으로 소비된다.

| 소비 방식 | 키의 역할 | 값의 도착 형태 |
|---|---|---|
| 환경 변수 참조 | 키 = 환경 변수 이름 | `echo $KEY` |
| 볼륨 마운트 | 키 = **파일 이름** | `cat /경로/KEY` |

두 번째가 이 장의 주인공이다. 19장에서 환경 변수에 담을 수 없었던 "파일 형태의 설정"이 드디어 갈 곳을 찾는다.

### 3.2 ConfigMap 정의와 네이밍 컨벤션

```yaml
# Example 20-1. ConfigMap 리소스
apiVersion: v1
kind: ConfigMap
metadata:
  name: random-generator-config
data:
  PATTERN: Configuration Resource     # ① 환경 변수용 키 — 대문자 컨벤션
  application.properties: |           # ② 파일용 키 — 파일 이름 그대로. | 는 YAML 멀티라인 문자열
    # Random Generator config
    log.file=/tmp/generator.log
    server.port=7070
  EXTRA_OPTIONS: "high-secure,native"
  SEED: "432576345"                   # ③ 숫자처럼 보여도 반드시 따옴표 — data 값은 문자열만 허용
```

한 ConfigMap 안에 **성격이 다른 두 스타일의 키가 공존**하는 것이 이 예제의 포인트다.

```
용도별 네이밍 컨벤션 (권장)

환경 변수용 → UPPER_CASE          (PATTERN, SEED, EXTRA_OPTIONS)
파일용     → filename.ext         (application.properties)
```

기술적 강제가 아니라 가독성 관례지만, 실제 제약과도 맞아떨어진다 — 환경 변수 이름에는 점(`.`)이 들어갈 수 없어서 `application.properties`는 애초에 환경 변수가 될 수 없고, 뒤에 나올 `envFrom`에서 자동으로 걸러진다. 컨벤션이 곧 안전장치가 되는 셈이다.

**중요: ConfigMap 자체에는 "이 키는 환경 변수용, 저 키는 파일용"이라는 정보가 전혀 없다.** ConfigMap은 데이터 창고일 뿐이고, 어떻게 꺼내 쓸지는 전적으로 **소비하는 쪽(Pod 명세)이 결정**한다. 같은 ConfigMap을 A Pod은 환경 변수로, B Pod은 파일로 써도 된다.

### 3.3 kubectl로 만들기 — YAML 대필 서비스

`application.properties`가 100줄이라면? YAML 안에 복사해 넣고 들여쓰기를 전부 맞추는 것은 고문이다. `kubectl create cm`이 이를 대신해준다.

```bash
# Example 20-2. 파일로부터 ConfigMap 생성
# ① --from-literal: 짧은 값은 명령줄에서 직접
# ② --from-file:    로컬 디스크의 실제 파일을 통째로
kubectl create cm spring-boot-config \
  --from-literal=PATTERN="Configuration Resource" \
  --from-literal=EXTRA_OPTIONS="high-secure,native" \
  --from-literal=SEED="432576345" \
  --from-file=application.properties
```

`--from-file`의 동작: **내 컴퓨터의** `application.properties` 파일을 kubectl이 직접 읽어서, 키 = 파일 이름, 값 = 파일 내용으로 ConfigMap에 넣는다. 결과물은 Example 20-1과 동일하다 — 이 명령은 YAML을 대신 써주는 편의 기능일 뿐이다.

```
[내 노트북]                            [Kubernetes 클러스터]
application.properties  ──kubectl──→   ConfigMap (데이터로 저장)
     (진짜 파일)                             │
                                            ▼ 나중에 Pod이 볼륨 마운트하면
                                       컨테이너 안에서 다시 파일로 부활
```

| | YAML 직접 작성 | kubectl 명령 |
|---|---|---|
| 장점 | Git 버전 관리, 선언적 | 빠름, 파일 자동 포함 |
| 단점 | 긴 파일 들여쓰기 지옥 | 실행 이력 없으면 재현 곤란 |

실무 절충안 — 명령으로 YAML을 **생성만** 하고 Git에 커밋:

```bash
kubectl create cm spring-boot-config --from-file=application.properties \
  --dry-run=client -o yaml > configmap.yaml    # 두 방식의 장점을 모두
```

Secret도 동일하다(`kubectl create secret generic ...`). 이때 Base64 인코딩은 kubectl이 알아서 해준다.

### 3.4 환경 변수로 소비하기: env와 envFrom

**개별 주입 — configMapKeyRef**

```yaml
# Example 20-3. ConfigMap으로부터 환경 변수 설정
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - env:
    - name: PATTERN                        # ① 컨테이너 안에 만들 환경 변수 이름 (키와 달라도 됨)
      valueFrom:
        configMapKeyRef:
          name: random-generator-config    # ② 참조할 ConfigMap 이름
          key: PATTERN                     # ③ 그 안의 키 이름
```

19장 Example 19-4에서 이미 본 문법이다. 키가 20개면 이 5줄 블록을 20번 반복해야 한다는 게 문제인데 —

**통째 주입 — envFrom + prefix**

```yaml
# Example 20-4. ConfigMap의 모든 항목을 환경 변수로
spec:
  containers:
  - envFrom:
    - configMapRef:
        name: random-generator-config   # ① 유효한 환경 변수 이름인 키를 전부 가져옴
      prefix: CONFIG_                    # ② 모든 키 앞에 접두사
```

Example 20-1 기준 결과는 환경 변수 **3개**다: `CONFIG_PATTERN`, `CONFIG_EXTRA_OPTIONS`, `CONFIG_SEED`.

```
키는 4개인데 왜 3개?

PATTERN, EXTRA_OPTIONS, SEED   → 유효한 이름 → 주입 ✅
application.properties          → 점(.) 포함 → 조용히 무시 (에러도 없음)
```

`prefix`의 용도는 두 가지 — 기존 변수(`PATH`, `HOME`)와의 **충돌 방지**, 그리고 이름만 봐도 ConfigMap 출신임을 아는 **출처 표시**.

**⚠️ 겹칠 때의 우선순위**

```
env로 직접 지정한 값          ← 최강. 항상 이긴다
   ▲
envFrom의 뒤쪽 ConfigMap      ← 앞쪽의 중복 키를 덮어씀
   ▲
envFrom의 앞쪽 ConfigMap      ← 최약
```

이 규칙은 유용한 패턴을 만든다 — `envFrom`으로 공통 기본 설정을 깔고, `env`로 이 Pod만의 특별한 값을 덮어쓰는 식. Secret은 `configMapKeyRef` → `secretKeyRef`, `configMapRef` → `secretRef`로 단어만 바꾸면 된다. 단, **민감한 값을 환경 변수로 보내는 것 자체의 위험**(19장 3.4)은 여전하다.

### 3.5 볼륨으로 소비하기: 키가 파일이 된다

```yaml
# Example 20-5. ConfigMap을 볼륨으로 마운트
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    volumeMounts:                    # ② 컨테이너: "그 볼륨을 내 /config에 걸어줘"
    - name: config-volume            #    ← 이름으로 아래 볼륨을 지목 (연결 고리)
      mountPath: /config
  volumes:                           # ① Pod: "config-volume이라는 볼륨을 준비"
  - name: config-volume
    configMap:
      name: random-generator-config  #    볼륨의 내용물 = 이 ConfigMap
```

**왜 두 곳에 나눠 적나?** Pod 하나에 컨테이너가 여러 개일 수 있기 때문이다. 볼륨은 Pod 수준(`volumes`)에 한 번 정의하고, 각 컨테이너가 원하는 위치(`volumeMounts`)에 각자 건다 — "공용 창고 하나 준비"와 "내 방 어디에 문을 낼지"의 분리다.

**결과 — 키 4개 = 파일 4개, 1:1 투영**

```
/                                  ← 컨테이너 루트
├── app/
│   └── random-generator.jar       (이미지에 원래 있던 것)
└── config/                        ← ★ mountPath (여기부터 ConfigMap)
    ├── PATTERN                    내용: Configuration Resource
    ├── application.properties     내용: # Random Generator config
    │                                    log.file=/tmp/generator.log
    │                                    server.port=7070
    ├── EXTRA_OPTIONS              내용: high-secure,native
    └── SEED                       내용: 432576345
```

envFrom에서 버려졌던 `application.properties`가 여기서는 당당히 파일이 된다 — 파일 이름에 점은 아무 문제가 없다. 반대로 환경 변수용 키들도 가리지 않고 전부 파일이 된다. **볼륨 마운트는 기본적으로 전량 투영**이다.

파일 내용에 대한 흔한 오해 하나 — `/config/SEED`는 JSON도 특수 포맷도 아닌 **그냥 텍스트 파일**이다. 키가 이름, 값이 내용, 그게 전부다. 값에 JSON 문자열을 넣으면 JSON 파일이 되고, properties를 넣으면 properties 파일이 되는 것뿐이다. Kubernetes는 내용을 해석하지 않는다.

**들여다보면 보이는 것 — 심볼릭 링크**

```
/config/
├── PATTERN → ..data/PATTERN                (심볼릭 링크)
├── ..data → ..2026_08_15_09_00_00.12345/   (링크)
└── ..2026_08_15_09_00_00.12345/            (진짜 파일들의 숨김 폴더)
```

파일들이 실은 숨김 폴더를 가리키는 링크다. ConfigMap이 수정되면 kubelet이 새 버전 폴더를 만들고 `..data` 링크만 휙 바꿔치기한다 — **원자적(atomic) 교체**. 다음 절의 핫 리로드가 이 메커니즘 위에서 동작한다.

⚠️ 실무 함정: 이미지 안에 `/config`에 원래 파일이 있었다면 마운트 순간 **전부 가려진다**(리눅스 마운트의 기본 동작). 특정 파일 하나만 끼워 넣으려면 `subPath`를 쓰되, subPath 마운트는 자동 갱신이 안 된다는 트레이드오프가 있다.

### 3.6 세밀하게 골라내기: items, path, mode

전량 투영이 싫다면 — 노출할 키, 파일 이름, 권한까지 개별 제어할 수 있다.

```yaml
# Example 20-6. ConfigMap 항목을 선택적으로 볼륨에 노출
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    volumeMounts:
    - name: config-volume
      mountPath: /config
  volumes:
  - name: config-volume
    configMap:
      name: random-generator-config
      items:                              # ① 이 목록에 적은 키만 파일로 (필터)
      - key: application.properties       # ② ConfigMap에서 찾을 키 이름 (원본과 정확히 일치)
        path: spring/myapp.properties     # ③ 컨테이너에 만들 경로/이름 (하위 폴더 자동 생성)
        mode: 0400                        # ④ 파일 권한 — 소유자 읽기 전용
```

```
Example 20-5 (전량)             Example 20-6 (선택)
/config/                        /config/
├── PATTERN                     └── spring/
├── application.properties          └── myapp.properties   ← 이것만!
├── EXTRA_OPTIONS
└── SEED                        최종 경로 = mountPath + path
                                = /config/spring/myapp.properties
```

- **`key` vs `path`** — "ConfigMap에서 뭘 꺼낼지" vs "컨테이너 어디에 어떤 이름으로 놓을지". 꺼내는 이름과 놓는 이름의 분리다. ConfigMap의 키는 조직 관례를 따르고, 파일 경로는 앱이 요구하는 정확한 위치에 맞출 수 있다.
- **`mode: 0400`** — `r--------`, 소유자만 읽기. 파일이기에 가능한 권한 제어(환경 변수엔 없는 개념)이며, ConfigMap보다 **Secret 마운트에서 진가**를 발휘한다.

여기까지 오면 소비 방법의 전체 지도가 완성된다.

| | 전체 주입 | 개별 선택 |
|---|---|---|
| **환경 변수** | `envFrom` + `prefix` (20-4) | `env` + `configMapKeyRef` (20-3) |
| **볼륨(파일)** | `volumes.configMap` (20-5) | + `items` / `path` / `mode` (20-6) |

모든 결정권은 소비하는 쪽에 있다. 전체든 개별이든, 이름을 바꾸든, 권한을 걸든 자유 조합이다.

### 3.7 핫 리로드의 명암 — 드리프트

두 소비 경로의 가장 중요한 운영상 차이가 여기서 갈린다.

```
ConfigMap 수정 (kubectl edit / apply)
        │
        ├──→ 볼륨 파일     : kubelet이 자동 갱신 (심볼릭 링크 교체) ✅
        │                   앱이 파일 변경을 감지(watch)하면 → 무중단 핫 리로드
        │
        └──→ 환경 변수     : 반영 안 됨 ❌
                            프로세스 시작 시 메모리에 복사·고정 — OS 수준 제약
```

단, "파일이 갱신된다"와 "설정이 적용된다"는 다르다. 시작할 때 한 번만 설정을 읽는 앱이라면 파일이 바뀌어도 옛 값으로 계속 돈다 — 결국 재시작이 필요하다. 핫 리로드는 **앱이 지원할 때만** 완성되는 그림이다(nginx reload, Spring Cloud refresh 등).

**그런데 이 편리함에는 어두운 면이 있다.**

```
😱 핫 변경이 만드는 사고 — 구성 드리프트(configuration drift)

새벽 장애 → 담당자가 kubectl edit cm으로 직접 수정 → 불 끔 → Git 반영 깜빡
        │
        ▼  이제 Git의 설정 ≠ 클러스터의 실제 설정 (어긋남 = 드리프트)
        │
몇 주 뒤 정상 배포 → Git의 옛 설정이 클러스터를 덮어씀
        │
        ▼  새벽의 수정 소리 없이 증발 💨 → 같은 장애 재발 → "어? 왜 또?"
           그 수정은 어디에도 기록되지 않았으므로 원인 추적 불가
```

실시간 변경은 어디에도 추적되지 않고 재시작 시 쉽게 사라진다. 19장 4.3에서 본 "불변성의 역설"이 ConfigMap 세계에서 재현되는 것이다. 그래서 많은 사람이 한번 배포되면 변하지 않는 **불변(immutable) 구성**을 선호한다.

### 3.8 immutable — 수정 금지가 주는 것

본격적인 불변 구성은 21장의 몫이지만, ConfigMap/Secret만으로 저렴하게 달성하는 방법이 있다 — Kubernetes 1.21부터 지원하는 `immutable` 필드다.

```yaml
# Example 20-7. 불변 Secret
apiVersion: v1
kind: Secret
metadata:
  name: random-config
data:
  user: cm9sYW5k        # base64 -d 하면 "roland" — 저자 이름. Base64≠보안의 산증인
immutable: true          # ① data 안이 아니라 최상위 필드. 기본값 false
```

효과는 두 가지다.

```
① 수정 원천 봉쇄
   kubectl edit → "Forbidden: field is immutable" 거부
   변경의 유일한 경로: 삭제 → 재생성 → 참조하는 Pod 재시작

② 클러스터 성능 향상
   가변 객체: kubelet이 "값 바뀌었나?" 계속 감시(watch) — 수천 Pod이면 수천 연결
   불변 객체: "어차피 안 바뀌잖아" → 한 번 읽고 감시를 아예 끊음
   → 대규모 클러스터에서 API 서버 부하가 상당히(considerably) 감소
```

불변인데 설정은 바뀌어야 하니, 실무 패턴은 **이름에 버전 붙이기**다.

```
random-config-v1 (immutable) ──┐  수정 대신 새 버전 생성
random-config-v2 (immutable) ──┤  Deployment의 참조만 v2 → v3 교체
random-config-v3 (immutable) ──┘  → 자동 롤링 업데이트로 Pod 재시작까지 해결
```

모든 변경이 버전으로 기록되고, 문제 시 이전 버전으로 되돌리면 끝 — 3.7의 드리프트가 원천 차단된다.

| | 가변 (기본값) | 불변 (`immutable: true`) |
|---|---|---|
| 수정 | `kubectl edit` 즉시 | 삭제 후 재생성만 |
| 볼륨 핫 리로드 | 됨 | 안 됨 (감시 자체가 꺼짐) |
| 드리프트 위험 | 있음 ⚠️ | 없음 ✅ |
| API 서버 부하 | 감시 연결 유지 | 없음 (성능 ↑) |
| 어울리는 곳 | 개발, 자주 바뀌는 설정 | 운영, 대규모 클러스터 |

### 3.9 Secret은 얼마나 안전한가

"Base64로 인코딩하니까 안전하다"는 **가장 흔한 오해**다. 다시 한번 — Base64는 열쇠 없이 누구나 되돌릴 수 있는 변환이며, 보안 관점에서 평문이다. 진짜 목적은 바이너리 데이터의 텍스트 포장이고, 33% 크기 팽창(3바이트 → 4글자)이라는 비용까지 치른다.

그럼 Secret이 ConfigMap보다 안전하다고 여겨지는 근거는? **인코딩이 아니라 Kubernetes가 Secret을 다루는 운영 방식**에 있다.

```
Secret 보안의 층위

Base64 인코딩            ← 보안 아님 (포장일 뿐) ❌
├─ 필요한 노드에만 배포     그 Secret을 쓰는 Pod이 있는 노드에만 전송 — 노출 범위 축소
├─ tmpfs(메모리) 저장      노드에서 디스크에 절대 안 씀. Pod 제거 시 즉시 소멸
│                         → 디스크 도난·폐기 시에도 안 남음
├─ etcd 암호화 (옵션 ⚠️)   중앙 저장소에서의 encryption at rest
│                         "can be" — 기본값이 아니라 관리자가 켜야 함
├─ RBAC 접근 제어          특정 서비스 어카운트만 읽기 허용 (26장)
└─ ...그러나 뚫린다 ↓
```

**⚠️ Pod 생성 권한 = 사실상 Secret 열람 권한**

```
상황: Secret 직접 읽기 권한은 없음. 하지만 Pod 생성 권한은 있음.

우회: 높은 권한의 서비스 어카운트를 "빌려 입은" Pod을 직접 생성
      → 그 Pod에 목표 Secret을 볼륨으로 마운트
      → Pod의 파일/로그로 비밀번호 열람 완료 😈

결론: 네임스페이스에서 Pod을 만들 수 있는 사용자·컨트롤러는
      어떤 서비스 어카운트든 사칭(impersonate) 가능
      = 그 네임스페이스의 모든 Secret과 ConfigMap에 접근 가능
```

RBAC으로 Secret을 아무리 조여도 Pod 생성 권한이 뒷문이 된다. 그래서 책의 처방은 **방어를 여러 겹으로(defense in depth)** — 진짜 민감한 정보는 애플리케이션 수준에서 한 겹 더 암호화하거나, Vault·AWS Secrets Manager 같은 외부 비밀 관리 도구를 쓰고 Kubernetes Secret에는 접속 토큰 정도만 둔다. Git에 YAML을 저장하는 GitOps 맥락의 안전한 Secret 관리(Sealed Secrets, SOPS 등)는 25장에서 다룬다.

### 레퍼런스

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>ConfigMap을 사용하는 Pod의 자동 갱신 동작과 그 한계는 Kubernetes 공식 문서 <strong>"ConfigMaps"</strong>에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "ConfigMaps consumed as environment variables are not updated automatically and require a pod restart."
  </blockquote>
  <div>[해석] "환경 변수로 소비된 ConfigMap은 자동으로 업데이트되지 않으며 Pod 재시작이 필요하다." — 공식 문서는 볼륨으로 마운트된 ConfigMap은 kubelet의 주기적 동기화로 최종적으로(eventually) 갱신되지만, <code>subPath</code> 볼륨 마운트로 소비하는 컨테이너는 갱신을 받지 못한다는 점, 그리고 <code>immutable: true</code>가 설정된 ConfigMap은 kube-apiserver에 대한 감시(watch)를 닫아 클러스터 성능을 개선한다는 점을 함께 설명한다.</div>
  <div style="margin-top:10px;">Secret 문서는 이 장의 보안 논의를 그대로 뒷받침한다 — etcd의 Secret은 기본적으로 암호화되지 않은 채 저장되므로 encryption at rest를 활성화할 것, API 접근 권한이 있는 누구나 Secret을 조회·수정할 수 있으므로 RBAC으로 최소 권한을 적용할 것을 권고한다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/concepts/configuration/configmap/">kubernetes.io — ConfigMaps</a></div>
  <div>→ <a href="https://kubernetes.io/docs/concepts/configuration/secret/">kubernetes.io — Secrets</a></div>
  <div>→ <a href="https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/">kubernetes.io — Encrypting Confidential Data at Rest</a></div>
</div>
{{< /rawhtml >}}

---

## 4. Discussion

ConfigMap과 Secret은 구성 정보를 Kubernetes API로 관리하기 쉬운 전용 리소스 객체에 담는다. 그리고 이것들은 플랫폼의 **내장(intrinsic) 기능**이다 — 어떤 클러스터든 설치 없이 그냥 있고, kubectl·RBAC·네임스페이스 같은 표준 도구가 전부 통하며, 21장처럼 직접 만들어야 하는 커스텀 구조물이 필요 없다.

### 전체 메커니즘 정리

| 메커니즘 | 문법 | 특징 / 주의 |
|---|---|---|
| **YAML 정의** | `kind: ConfigMap` + `data` | 환경 변수용은 대문자, 파일용은 파일명 컨벤션 |
| **명령 생성** | `kubectl create cm --from-literal/--from-file` | YAML 대필. `--dry-run=client -o yaml`로 Git 병행 |
| **개별 env** | `env` + `configMapKeyRef` | 변수 이름 ≠ 키 이름 가능 |
| **통째 env** | `envFrom` + `prefix` | 무효한 키(점 포함)는 조용히 무시. env 직접 지정이 항상 우선 |
| **전량 볼륨** | `volumes.configMap` | 키 = 파일명, 값 = 내용. 심볼릭 링크 기반 원자적 갱신 |
| **선택 볼륨** | `items` + `path` + `mode` | 키 필터링, 경로/이름 변경, 파일 권한(0400) |
| **핫 리로드** | 볼륨만 해당 | 앱의 파일 감지 필요. 드리프트 위험 ⚠️ |
| **불변화** | `immutable: true` | 수정 금지 + 감시 중단(성능 ↑). 변경은 버전 교체로 ✅ |
| **Secret 소비** | `secretKeyRef` / `secretRef` / `secret:` | 문법만 다르고 동작 동일. Base64 ≠ 보안 ⚠️ |

### 4.1 정의와 사용의 분리

이 패턴의 가장 큰 장점을 한 줄로 줄이면 — **구성 데이터의 정의(definition)와 사용(usage)의 분리(decoupling)** 다.

```
[정의]                              [사용]
ConfigMap                           Pod / Deployment
"데이터가 뭔지"            ←분리→    "그걸 어떻게 쓸지"
(random-generator-config)           (env? envFrom? 볼륨? items로 골라서?)
```

이 분리가 실제로 가능하게 해주는 것들:

- 설정만 바꿀 때 Pod 명세를 안 건드린다 (그 반대도 성립)
- 같은 ConfigMap을 여러 Pod이 **각자 다른 방식으로** 소비한다 — 결정권은 항상 사용하는 쪽에
- 같은 앱 이미지를 환경(개발/운영)마다 다른 ConfigMap과 조합해 재사용한다
- 설정 담당자와 배포 담당자의 역할이 분리된다

19장의 "명함에 집 주소 대신 홈페이지 주소를 적는" 간접 참조가, 이 장에서 파일 마운트·선택 투영·불변화까지 갖춘 완전한 체계로 자란 것이다.

### 4.2 Golden hammer가 아니다 — 크기와 개수의 한계

하지만 이 구성 리소스에도 명확한 제약이 있다.

```
① 크기 — 1MB 제한
   ConfigMap/Secret은 etcd에 저장되는데, etcd는 작고 빠른 키-값 저장소지
   대용량 파일 저장소가 아니다. 큰 객체는 클러스터 전체를 느리게 만든다.

② Base64 팽창 — 바이너리는 실질 ~700KB
   원본 700KB ──Base64 (×1.33)──→ 약 933KB ≈ 1MB 한도 도달
   한도는 "인코딩 후" 크기 기준이다.

③ 개수 쿼터
   ResourceQuota로 네임스페이스당 ConfigMap/Secret 개수 제한 가능
   "설정마다 하나씩 무한정" 전략이 실제 클러스터에서는 막힐 수 있다.
```

그리고 무엇보다 — ConfigMap은 **구성 전용**이다. 편리한 파일 전달 통로라고 해서 ML 모델, 이미지 에셋, DB 덤프 같은 애플리케이션 데이터를 담는 것은 오용이다. "망치를 들면 모든 게 못으로 보인다" — ConfigMap은 golden hammer가 아니다.

| 데이터 | 올바른 도구 |
|---|---|
| 일반 설정 (수 KB) | ConfigMap ✅ |
| 비밀번호, 인증서 | Secret (+ 앱 수준 암호화) ✅ |
| 큰 구성 데이터 (>1MB) | 21~22장의 패턴들 |
| 앱 데이터, 파일, 모델 | 볼륨, 오브젝트 스토리지, 이미지 |

### 핵심 메시지

```
Configuration Resource의 몫: 설정을 일급 리소스로 — 정의와 사용의 분리
그 너머는 다음 패턴들의 영역이다

Immutable Configuration  → 1MB를 넘는 설정을 컨테이너 이미지로 버전 관리 (21장)
Configuration Template   → 환경마다 조금씩 다른 대형 설정의 중복 제거 (22장)
```

> Configuration Resource는 **"설정 외부화의 표준 답안"** 이다.
> ConfigMap/Secret이라는 간접 계층으로 정의와 사용을 분리하고,
> 환경 변수(단순 키-값)와 볼륨(파일, 핫 리로드, 권한 제어)이라는 두 경로를 상황에 맞게 고르되,
> 드리프트가 두려우면 immutable로 잠그고, Base64를 보안으로 착각하지 말며,
> 1MB의 벽을 만나는 순간 다음 패턴으로 넘어가야 한다.