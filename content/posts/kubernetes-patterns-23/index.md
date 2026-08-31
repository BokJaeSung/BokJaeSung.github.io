---
series: ["K8sPatterns"]
title: "K8sPatterns.23 Process Containment"
date: 2026-08-24T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "security", "least-privilege"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.23 Process Containment'
  relative: true
summary: "검사는 언젠가 뚫린다고 가정하고, securityContext 7종 세트로 프로세스를 최소 권한의 울타리에 가둔 뒤, PSS/PSA 정책으로 그 울타리를 클러스터 차원에서 강제하는 법."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-검사는-사진일-뿐--위험-0는-없다" style="color:var(--secondary,inherit);text-decoration:none;">2.1 검사는 사진일 뿐 — 위험 0%는 없다</a></div>
    <div><a href="#22-진짜-무서운-것은-탈출--컨테이너에서-클러스터로" style="color:var(--secondary,inherit);text-decoration:none;">2.2 진짜 무서운 것은 탈출 — 컨테이너에서 클러스터로</a></div>
  </div>
  <div><a href="#3-securitycontext--개발자가-세우는-울타리" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. securityContext — 개발자가 세우는 울타리</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-securitycontext--두-레벨과-우선순위" style="color:var(--secondary,inherit);text-decoration:none;">3.1 securityContext — 두 레벨과 우선순위</a></div>
    <div><a href="#32-root-금지--runasuser-runasnonroot-그리고-init-컨테이너-트릭" style="color:var(--secondary,inherit);text-decoration:none;">3.2 root 금지 — runAsUser, runAsNonRoot, Init 컨테이너 트릭</a></div>
    <div><a href="#33-승급-차단--allowprivilegeescalation-false" style="color:var(--secondary,inherit);text-decoration:none;">3.3 승급 차단 — allowPrivilegeEscalation: false</a></div>
    <div><a href="#34-privileged라는-빨간-버튼과-capability라는-열쇠-꾸러미" style="color:var(--secondary,inherit);text-decoration:none;">3.4 privileged라는 빨간 버튼과 capability라는 열쇠 꾸러미</a></div>
    <div><a href="#35-drop-all--add--열쇠는-전부-회수-후-선별-지급" style="color:var(--secondary,inherit);text-decoration:none;">3.5 drop ALL + add — 열쇠는 전부 회수 후 선별 지급</a></div>
    <div><a href="#36-읽기-전용-파일시스템--불변-인프라의-자물쇠" style="color:var(--secondary,inherit);text-decoration:none;">3.6 읽기 전용 파일시스템 — 불변 인프라의 자물쇠</a></div>
    <div><a href="#37-seccomp과-selinux--커널-차원의-마지막-두-필터" style="color:var(--secondary,inherit);text-decoration:none;">3.7 seccomp과 SELinux — 커널 차원의 마지막 두 필터</a></div>
  </div>
  <div><a href="#4-pss와-psa--개인의-성실함에서-시스템의-강제로" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. PSS와 PSA — 개인의 성실함에서 시스템의 강제로</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-pss와-psa--기준집과-점검관" style="color:var(--secondary,inherit);text-decoration:none;">4.1 PSS와 PSA — 기준집과 점검관</a></div>
    <div><a href="#42-psa의-적용--네임스페이스-라벨로-거는-정책" style="color:var(--secondary,inherit);text-decoration:none;">4.2 PSA의 적용 — 네임스페이스 라벨로 거는 정책</a></div>
    <div><a href="#43-도입-순서--기록-먼저-강제는-나중에" style="color:var(--secondary,inherit);text-decoration:none;">4.3 도입 순서 — 기록 먼저, 강제는 나중에</a></div>
    <div><a href="#44-명부는-누가-쓰는가--세-모드의-출력처" style="color:var(--secondary,inherit);text-decoration:none;">4.4 명부는 누가 쓰는가 — 세 모드의 출력처</a></div>
    <div><a href="#45-psa는-고쳐주지-않는다--non-mutating이라는-선택" style="color:var(--secondary,inherit);text-decoration:none;">4.5 PSA는 고쳐주지 않는다 — non-mutating이라는 선택</a></div>
  </div>
  <div><a href="#5-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-컨테이너는-울타리다--단-제대로-설정했을-때만" style="color:var(--secondary,inherit);text-decoration:none;">5.1 컨테이너는 울타리다 — 단, 제대로 설정했을 때만</a></div>
    <div><a href="#52-shift-left--보안을-왼쪽으로" style="color:var(--secondary,inherit);text-decoration:none;">5.2 Shift Left — 보안을 왼쪽으로</a></div>
  </div>
  <div><a href="#6-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. References</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Process Containment 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"뚫린다"를 전제로 한 2차 방어선 — 프로세스를 최소 권한의 울타리에 가둔다

  1차 방어: 정적 분석 · 동적 스캔 · 의존성/이미지 스캔   ← "알려진" 위험만 잡는다
                        │  언젠가 뚫림 (제로데이, 새 코드)
                        ▼
  2차 방어: Process Containment  ← 이 장
  ├─ 개발자의 도구: securityContext
  │    runAsNonRoot · allowPrivilegeEscalation: false
  │    capabilities drop ALL · readOnlyRootFilesystem
  │    seccompProfile · seLinuxOptions
  │
  └─ 관리자의 도구: 정책
       PSS 3등급 (Privileged / Baseline / Restricted)
       + PSA (warn / audit / enforce)
                        ▼
  "What happens in a container stays in a container" 🔒
```

이 장의 출발점은 겸손한 인정이다 — **아무리 검사해도 언젠가는 뚫린다.** 정적 분석, 동적 스캔, 의존성 스캔, 이미지 스캔은 모두 "알려진" 취약점만 잡는다. 새 코드와 새 라이브러리는 계속 새 구멍을 만들고, 위험 0%는 보장할 수 없다. **Process Containment 패턴**은 그래서 방향을 바꾼다. 침입을 막는 게 아니라, **침입당했다고 가정하고 침입자가 할 수 있는 일을 최소화**한다. 최소 권한의 원칙(principle of least privilege)으로 프로세스를 지정된 경계 안에 가두면, 컨테이너가 뚫려도 피해는 컨테이너 안에서 끝난다.

이 장의 재미는 울타리가 **겹겹이** 세워진다는 데 있다. root 금지, 승급 차단, 능력 회수, 쓰기 금지, 시스템 콜 필터, 라벨 장벽 — 하나하나는 작은 말뚝이지만 일곱 개가 겹치면 해커는 들어와도 할 수 있는 게 없다. 그리고 마지막에, 이 말뚝들을 개인의 성실함이 아니라 **클러스터 정책으로 강제**하는 장치(PSS/PSA)까지 세운다.

---

## 2. Problem

### 2.1 검사는 사진일 뿐 — 위험 0%는 없다

쿠버네티스 워크로드의 주요 공격 경로는 애플리케이션 코드다. 이를 막는 검사들은 이미 많다.

```
① 정적 분석 (SAST)   — 코드를 실행하지 않고 소스만 읽어 결함 탐지
② 동적 스캔 (DAST)   — 진짜 해커처럼 공격 시도 (SQLi, CSRF, XSS 등)
③ 의존성 스캔        — 갖다 쓴 라이브러리에 알려진 취약점이 있는지 확인
④ 이미지 스캔        — 베이스 이미지와 패키지를 취약점 DB와 대조
```

전부 필요한 검사다. 그런데 공통 한계가 있다 — **전부 "알려진" 문제만 잡는다.** 수배 전단에 있는 범인만 잡을 수 있는 셈이라, 처음 보는 신종 수법(제로데이)은 그냥 통과한다. 게다가 검사는 찍는 순간의 사진일 뿐이다. 오늘 통과한 앱도 내일 추가한 코드 한 줄, 업데이트한 라이브러리 하나 때문에 구멍이 생긴다.

### 2.2 진짜 무서운 것은 탈출 — 컨테이너에서 클러스터로

런타임 수준의 프로세스 보안 통제가 없다면, 앱 코드를 뚫은 공격자의 목표는 앱 하나에서 끝나지 않는다.

```
앱 코드 뚫기 → 컨테이너 장악 → 호스트(노드) 장악 → 클러스터 전체 장악
   (입구)                       (컨테이너 탈출!)        (게임 오버)
```

컨테이너 하나가 뚫리는 건 호텔 방 하나가 털리는 것이지만, 호스트까지 넘어가면 그 노드 위의 **모든 컨테이너**가, 클러스터까지 넘어가면 **서비스 전체**가 넘어간다. 이것이 **컨테이너 탈출(container breakout)**이다. 탈출을 가능케 하는 발판은 대부분 과잉 권한 — root, privileged, 후한 capability다.

즉 이 장의 목표는: **1차 방어(검사)가 뚫리는 것을 전제로, 쿠버네티스 설정만으로 2차 방어선을 세워 rogue 프로세스를 지정된 경계 안에 가두는 것.**

---

## 3. securityContext — 개발자가 세우는 울타리

### 3.1 securityContext — 두 레벨과 우선순위

컨테이너가 어떤 권한을 가질지는 원래 컨테이너 런타임(도커 등)이 **기본값**으로 정한다. 쿠버네티스가 관리하는 경우, 이 보안 설정의 통제권은 쿠버네티스로 넘어오고 사용자에게는 **securityContext**라는 창구로 노출된다. 쓸 수 있는 자리는 두 곳이다.

```
Pod 레벨      spec.securityContext              → 볼륨 + 모든 컨테이너에 적용
컨테이너 레벨  spec.containers[].securityContext  → 그 컨테이너 하나에만 적용

둘이 겹치면?  → 컨테이너 레벨이 이긴다 (더 구체적인 쪽 우선)
```

학교 규칙과 같다 — 전교 규칙(Pod)보다 우리 반 규칙(컨테이너)이 우선한다. 볼륨 관련 설정(fsGroup 등)은 컨테이너들이 공유하는 것이라 **Pod 레벨에만** 있다는 것도 기억해 두자.

참고로 "컨테이너의 권한"이라는 표현은 줄임말이다. 커널의 세계에는 컨테이너라는 단위가 없고 프로세스만 있어서, securityContext로 적는 모든 것 — UID, capability, seccomp 필터, SELinux 라벨 — 은 최종적으로 **컨테이너 안에서 도는 프로세스에** 붙는다. 패턴 이름이 Container가 아니라 **Process** Containment인 이유이며, 이 관점은 3.4에서 자세히 편다.

한 가지 원칙을 미리 깔아둔다 — 일반 앱 개발자가 이 세세한 설정을 전부 손으로 만질 필요는 **없어야 정상**이다. 그런 건 전역 정책으로 검증·강제되는 게 맞고(4장에서 회수된다), 세밀한 튜닝이 진짜 필요한 건 빌드 시스템이나 노드 접근이 필요한 특수 인프라 컨테이너뿐이다. 이 장은 평범한 클라우드 네이티브 앱에 유용한 공통 설정만 본다.

### 3.2 root 금지 — runAsUser, runAsNonRoot, 그리고 Init 컨테이너 트릭

리눅스에서 root(**UID 0**)는 모든 걸 할 수 있는 계정이다. 해커가 뚫은 컨테이너가 root라면 탈출 취약점 하나로 호스트 root까지 이어질 위험이 커진다. 도둑 손에 쥐어진 게 **마스터키(root)냐 화장실 열쇠 하나(일반 사용자)냐**의 차이다. 그런데 많은 이미지가 사용자를 아예 안 만들거나, 만들어도 기본 실행 사용자로 지정하지 않아 **기본값인 root로 실행**된다.

용어부터 정확히 해두자 — **root는 프로세스가 아니라 "신분"이다.**

```
사용자(UID)  = "누구냐"라는 이름표.  root는 그중 0번인 특별 신분
프로세스     = 실행 중인 프로그램.  반드시 어떤 이름표를 "달고" 실행됨
"root로 실행" = "UID 0 이름표를 단 프로세스"의 줄임말
```

그리고 UID 숫자에는 **서열이 없다.** 특별한 것은 0 하나뿐이고, 0이 아니면 1이든 1000이든 65534든 전부 대등한 일반 사용자다. 아파트 동호수와 같다 — 101호와 2503호 중 누가 높은 게 아니라, 딱 한 곳(0호 = 마스터키 보관실)만 특별한 것. 1000과 2000의 차이는 높낮이가 아니라 "서로 남"이라는 소유 구분이며, 이게 바로 아래 함정의 원리다.

**방법 ① — runAsUser로 덮어쓰기**

```yaml
# Example 23-1. Pod의 컨테이너에 사용자/그룹 지정
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  securityContext:
    runAsUser: 1000     # UID 1000으로 실행 (root는 UID 0)
    runAsGroup: 2000    # GID 2000으로 실행
  containers:
  - name: app
    image: k8spatterns/random-generator:1.0
```

`runAsUser`가 프로세스의 **신분(UID)**, `runAsGroup`이 **소속 그룹(GID)**이다. 파일 권한은 "주인/그룹/나머지" 셋으로 나뉘므로 둘 다 맞아야 접근이 뜻대로 된다.

이미지에 뭐라고 적혀 있든 이 설정이 덮어쓴다. 단, **함정이 있다** — 이미지 안의 파일들은 보통 이미지에 지정된 그 사용자 소유로 만들어져 있다. 아무 번호나 적으면 파일 주인은 1001인데 프로세스는 1000이 되어 `Permission denied`로 앱이 죽는다. 1001호에 이사 왔는데 1000호 열쇠를 받은 격이다 — 1000이 1001보다 "낮아서"가 아니라 그냥 "남이라서" 못 여는 것. 그래서 **이미지를 먼저 확인하고, 이미지에 정의된 바로 그 UID/GID로** 실행해야 한다.

**방법 ② — runAsNonRoot로 검문만 하기 (덜 간섭적, 권장)**

```yaml
spec:
  securityContext:
    runAsNonRoot: true   # root(UID 0)면 컨테이너 시작 자체를 거부!
```

| | `runAsUser: 1000` | `runAsNonRoot: true` |
|---|---|---|
| 하는 일 | 사용자를 **바꿔버림** | root인지 **검사만** 함 |
| 검사 주체/시점 | — | **Kubelet이 런타임에** 검증 |
| 파일 소유권 충돌 | 잘못 지정하면 터짐 | 사용자를 안 바꾸니 위험 없음 |
| root면? | root가 아니게 됨 | **실행 거부** ❌ |

클럽 입구에서 손님 옷을 강제로 갈아입히는 것(runAsUser)과, 신분증만 확인해 미성년자를 돌려보내는 것(runAsNonRoot)의 차이다. 이미지가 정한 사용자를 존중하면서 "root만 아니면 돼"라는 최소 규칙만 거니 부작용이 적다. 검사 로직도 숫자 비교가 아니라 `UID == 0 ? 거부 : 통과` — 0인지만 본다.

**방법 ③ — root가 꼭 필요하면 Init 컨테이너로 수명 제한**

볼륨 소유자가 root라 일반 사용자인 앱이 못 쓰는 경우가 있다. 그럴 땐 root 작업을 "잠깐 왔다 가는" Init 컨테이너에 맡긴다.

```
① Init 컨테이너 (root) 시작 → chown으로 볼륨 소유권을 앱 UID로 변경 → 종료 👋
② 앱 컨테이너 (non-root) 시작 → 볼륨이 이미 내 소유, 정상 작동 ✅
```

이삿날 열쇠공(root)을 불러 잠금장치만 바꾸고 보내는 것이다 — 열쇠공은 상주하지 않는다. 앱이 도는 내내 root 프로세스는 존재하지 않으니, **root 노출 시간이 초반 몇 초로 압축**된다. root라는 신분이 죽는 게 아니라, 그 신분을 단 프로세스가 짧게 살다 죽는 것이다.

### 3.3 승급 차단 — allowPrivilegeEscalation: false

non-root로 실행해도 뒷문이 하나 남아 있다 — **권한 승급(privilege escalation)**. 리눅스의 `sudo`처럼, 일반 사용자가 특정 프로그램(setuid 비트가 붙은 `su`, `passwd` 등)을 실행하는 순간 root 권한을 얻는 메커니즘이다. 입구 검문(runAsNonRoot)을 통과시켰는데 건물 안에 **아무나 누르면 열리는 임원실 비상버튼**이 있는 셈이다.

이 뒷문은 버그가 아니라 리눅스의 **공식 통로**다. 원래 UID 변경은 단방향 밸브다 — root는 아무 UID로나 내려갈 수 있지만, 일반 사용자가 올라가는 것은 커널이 거부한다. 그런데 현실적 딜레마가 하나 있었다: 모든 비밀번호는 root 소유의 `/etc/shadow`에 저장되는데, 일반 사용자도 "자기" 비번은 바꿔야 한다. 그래서 만든 예외가 **setuid 비트** — 이 표시가 붙은 파일은 "누가 실행하든 **파일 주인(root)의 신분으로**" 돌아간다.

```
UID 1000 사용자가 passwd 실행
    ↓  (passwd = root 소유 + setuid 파일)
프로세스가 UID 0으로 태어남 🎩  ← 일반 사용자가 0에 "도달"하는 유일한 역류 통로
    ↓
/etc/shadow 수정 → 임무 완료, 종료
```

은행 창구와 같다 — 고객은 금고에 못 들어가지만, 열쇠 가진 창구 직원(passwd)에게 부탁하면 직원이 은행 권한으로 내 통장만 꺼내온다. sudo도 원리는 동일하다. 설계 의도는 "딱 정해진 안전한 작업만 root로"였지만, 해커는 이 합법적 뒷문을 비틀어 쓴다 — setuid 프로그램의 버그를 찌르거나, 이미지에 굴러다니는 `su`·`mount` 같은 setuid 바이너리를 이용해 root로 점프하는 것이다.

```yaml
spec:
  containers:
  - name: app
    securityContext:
      runAsNonRoot: true
      allowPrivilegeEscalation: false   # 승급 자체를 원천 차단 (컨테이너 레벨 전용!)
```

이 설정은 커널의 **`no_new_privs`** 플래그를 켠다 — "이 프로세스와 자식들은 실행(exec)을 통해 새 권한을 얻을 수 없다." 뒷문을 하나하나 찾아 막는 게 아니라 **뒷문이라는 메커니즘 자체를 꺼버리는** 것이라, setuid 비트가 그냥 무시되고 sudo도 작동하지 않는다. 그리고 **부작용이 거의 없다** — non-root로 설계된 정상 앱은 수명 주기 동안 승급이 필요할 일이 없기 때문이다. 정상 앱엔 영향 없고 해커의 승급 시도만 막히는 **공짜 보안**이다.

여기서 runAsNonRoot와 이 설정이 **왜 항상 짝으로 다니는지**도 짚어두자. 컨테이너는 프로세스 "하나"가 아니라 첫 프로세스(PID 1)에서 뻗은 **프로세스 트리**이고, UID는 프로세스마다 개별로 붙는다 — 전통적 nginx가 좋은 예로, master는 root(특권 포트 열기 담당)로 돌고 worker들은 스스로 신분을 낮춘 UID 101로 요청을 처리한다. 즉 한 컨테이너 안에 여러 UID가 공존할 수 있다. 그런데 runAsNonRoot는 **시작점(PID 1)만** 검문한다 — 시작이 non-root여도 안에 setuid 바이너리가 있으면 실행 중에 root 프로세스가 태어날 수 있는 것이다. 그 구멍을 allowPrivilegeEscalation이 **트리 전체**에 대해 막는다.

```
runAsNonRoot                    →  시작점 검문: "트리의 뿌리가 UID 0이면 거부"
allowPrivilegeEscalation: false →  트리 전체: "실행 중 신분 세탁 금지"

둘을 합치면 = 이 컨테이너의 프로세스 트리에 UID 0이 "영원히 등장할 수 없음" 🔒
```

여기까지가 root 방어 3종 세트다.

```
"처음부터 root로 들어가자"        → runAsNonRoot에 막힘 ❌
"들어가서 승급하자"               → allowPrivilegeEscalation에 막힘 ❌
"오래 사는 root 프로세스를 노리자" → Init 트릭 덕에 존재하지 않음 ❌
```

세 번째 줄은 앞의 둘과 성격이 다르다 — 해커 자신이 root가 되는 게 아니라, **이미 root로 상주하는 남의 프로세스를 속이거나 장악해 대리로 쓰는** 공격이다(금고를 직접 못 여니, 열쇠를 항상 들고 다니는 경비원을 협박해 대신 열게 하는 것). 이 공격에는 표적이 "오래 살아 있어야" 한다는 전제가 붙는데, Init 트릭은 root 작업을 앱 시작 전 몇 초에 몰아넣고 죽이므로 — 해커가 침입 가능한 시간대(앱 실행 중)에는 **노릴 root 프로세스 자체가 존재하지 않는다.** 표적 소멸에 의한 방어다.

### 3.4 privileged라는 빨간 버튼과 capability라는 열쇠 꾸러미

본질적으로 컨테이너는 **노드 위에서 돌아가는 프로세스**다. VM처럼 분리된 별세계가 아니라 **호스트 커널을 직접 호출**한다. 그래서 컨테이너에 준 권한 = 호스트 커널에 대한 권한이다.

이 "공유"의 실체를 정확히 보자. 커널에는 애초에 **컨테이너라는 개념이 없다** — 커널이 아는 것은 프로세스뿐이고, 컨테이너란 namespace와 cgroup을 두른 프로세스 트리에 우리가 붙인 별명이다. 격리조차 벽이 아니라 **시야 속임**이다: namespace는 커널이 프로세스마다 "너에게는 이 프로세스들만, 이 네트워크만, 이 파일시스템만 보여줄게"라고 장부를 다르게 보여주는 기능이다. 건물을 따로 지은 것(VM)이 아니라, 한 건물의 세대들에게 자기 층만 보이는 엘리베이터를 준 것 — 관리사무소(커널)는 하나다.

```
VM:        앱 → 게스트 커널 → 하이퍼바이저(중간 검문) → 호스트    ← 검문소 있음
컨테이너:   앱 → 호스트 커널 (직행!)                              ← 검문소 없음
```

호스트에서 `ps`를 치면 컨테이너 안의 프로세스가 다른 프로세스들과 나란히 그대로 보인다(안의 "PID 1"은 namespace가 만든 착시). 컨테이너마다 감독관 프로세스(containerd의 shim)가 붙긴 하지만 **띄우고 생사만 관리**할 뿐, 커널 호출을 대신 받아주지 않는다 — 중개자가 없어서 빠르고(수십 ms에 뜨는 이유), 없어서 위험하다. 검문 가능한 유일한 장소가 **커널 자체**라는 뜻이고, 이 장의 필터들(capability·seccomp·SELinux)이 전부 커널 기능인 이유, 그리고 패턴 이름이 Container가 아니라 **Process** Containment인 이유가 여기 있다.

커널 레벨 호출이 필요하면 권한을 줘야 하는데, 방법이 둘이다 — root로 실행해 전부 주거나(과잉), 필요한 **capability**만 골라 주거나(적정).

**Capability란** — 현대 리눅스는 root의 전능함을 약 40개의 작은 능력 조각으로 쪼개놨다. root = 모든 문이 열리는 **마스터키 꾸러미 40개**, capability 시스템 = 그 꾸러미를 풀어 필요한 열쇠 1~2개만 골라 줄 수 있게 한 것. UID가 0/비0의 이분법이라면, capability가 그 사이의 촘촘한 단계를 담당한다.

| Capability 예 | 할 수 있는 일 |
|---|---|
| `NET_BIND_SERVICE` | 1024 미만 특권 포트(80, 443)에 바인딩 |
| `NET_ADMIN` | 네트워크 설정 변경 |
| `CHOWN` | 파일 소유자 변경 |
| `SYS_ADMIN` | 온갖 관리 작업 — 사실상 root급이라 "new root"라 불림 ⚠️ |

**그리고 root보다 더한 것 — privileged.** `securityContext.privileged: true`를 켠 컨테이너는 **호스트의 root와 동급**이며 커널 권한 검사를 우회한다.

"컨테이너 안의 root"와 뭐가 다른가 — 여기가 헷갈리는 지점이다. 평범한 컨테이너는 안에서 root여도 **울타리 안의 root**다. capability는 제한되어 있고, 호스트 장치(`/dev`)는 안 보이고, 커널 파라미터도 못 건드린다. 반면 privileged는 그 울타리를 통째로 걷어낸다.

```
[컨테이너 안의 root] — 울타리 안의 왕
  · capability는 일부만
  · 호스트 장치 안 보임
  · 커널 설정 못 바꿈

[privileged]        — 울타리가 없음
  · capability 전부
  · 호스트 디스크가 그대로 보임 (마운트해서 읽기/쓰기 가능)
  · 커널 파라미터 변경 가능
```

호스트 디스크가 보인다는 것이 결정적이다 — 노드의 파일시스템을 그냥 마운트해서 읽고 쓸 수 있으니, **탈출 취약점을 찾을 필요조차 없다.** 정문이 열려 있는데 담을 넘을 이유가 없다. 그래서 이 옵션은 컨테이너를 격리(isolate)하는 게 아니라 호스트와 **한 몸으로 묶는(bundle)** 것이다.

```
일반 non-root 컨테이너     🔒🔒🔒
컨테이너 안의 root         🔒🔒     (그래도 격리는 있음)
privileged 컨테이너        💀       (격리 자체가 소멸 — 탈출할 필요조차 없음)
```

네트워크 스택 조작이나 하드웨어 접근이 필요한 관리용 컨테이너(CNI, 스토리지 드라이버 등)에만 쓰이는 옵션이고, 일반 앱은 **아예 피하고 필요한 capability만 개별 부여**하는 것이 맞다.

문제는 "내 앱이 어떤 capability를 쓰는지" 알기 어렵다는 것 — 개발자는 "서버 시작해줘" 한 줄을 쓸 뿐이고, 커널 호출은 프레임워크와 라이브러리 깊숙한 곳에서 일어난다(음식점 손님이 주방의 냉장고 열쇠 사용 횟수를 모르는 것과 같다). 책의 처방은 둘이다.

```
① 화이트리스트 접근 — capability 0개로 시작, 에러 나면 그것만 추가, 반복
   ("에러가 곧 답" — 앱이 비명 지르는 지점이 필요 목록을 알려준다)
② SELinux permissive 모드 — 위반을 막지 않고 "기록만" 하는 모드로 앱을 돌린 뒤
   audit 로그를 분석해 필요한 능력 목록을 뽑는다 (앱을 안 죽이고 파악 가능)
```

새 직원에게 출입기록만 남는 임시 카드를 주고 한 달 지켜본 뒤, **실제로 드나든 방의 열쇠만** 정식 발급하는 것이다.

### 3.5 drop ALL + add — 열쇠는 전부 회수 후 선별 지급

여기 반전이 하나 있다 — **capabilities 섹션을 비워두면 0개가 아니다.** 컨테이너 런타임의 **기본 capability 세트**가 자동으로 붙는데, 이게 대부분의 프로세스가 필요로 하는 것보다 훨씬 후하다(CHOWN, KILL, SETUID, NET_RAW, MKNOD...). 호텔 체크인하며 아무 말 안 했더니 객실 키에 헬스장·주방·창고 키까지 한 뭉치 딸려오는 격이다. 안 쓰는 열쇠는 해커에게만 유용하다.

그래서 모범 답안은 **전부 버리고, 필요한 것만 되돌려주기**다.

```yaml
# Example 23-2. Pod 권한 설정
apiVersion: v1
kind: Pod
metadata:
  name: web-app
spec:
  containers:
  - name: app
    image: docker.io/centos/httpd
    securityContext:
      capabilities:
        drop: [ 'ALL' ]               # ① 런타임 기본 세트를 몽땅 회수
        add: ['NET_BIND_SERVICE']     # ② 필요한 능력 딱 하나만 지급
```

왜 하필 `NET_BIND_SERVICE`인가 — 리눅스에서 **1024 미만 포트는 특권 포트**라 일반 사용자는 못 연다. 그런데 이 예제는 웹 서버(httpd)이고 80번 포트를 열어야 한다. root의 40개 능력 중 정확히 **1개만** 쓰는, 최소 권한 원칙의 교과서적 사례다.

그런데 더 나은 대안도 있다 — **애초에 비특권 포트(8080 등, ≥1024)에 바인딩하는 컨테이너로 교체**하면 capability 자체가 필요 없어진다. 열쇠를 주는 대신 **열쇠가 필요 없게 짐을 복도 사물함으로 옮기는** 것이다. "사용자가 8080으로 접속해야 하는 것 아니냐"는 걱정은 Service가 해결한다 — `port: 80, targetPort: 8080` 두 줄이면 밖에서는 여전히 80으로 보이고, 안에서만 8080이다(회사 대표번호와 내선번호의 관계). 그래서 실무에서도 처음부터 비특권 포트용으로 만들어진 이미지(nginx-unprivileged 등)를 선호한다.

```
보안 사고방식의 3단계
1단계: 필요한 권한을 다 준다 (root)
2단계: 필요한 권한"만" 준다 (add: NET_BIND_SERVICE)
3단계: 권한이 필요 없게 설계를 바꾼다 (8080 포트) ★ 가장 안전한 권한 = 존재하지 않는 권한
```

### 3.6 읽기 전용 파일시스템 — 불변 인프라의 자물쇠

잘 만든 클라우드 네이티브 앱은 컨테이너 파일시스템에 쓸 일이 없다. 컨테이너는 **일회용(ephemeral)**이라 재시작하면 안에 적은 건 다 증발하기 때문이다 — 상태는 외부 DB로, 로그는 stdout으로 보내는 것이 11장 Stateless Service의 설계다. 쓸 일이 없다면? **쓰기를 아예 막아도 부작용이 없다.** 또 하나의 공짜 보안이다.

```yaml
securityContext:
  readOnlyRootFilesystem: true   # 루트 파일시스템을 읽기 전용으로 마운트
```

해커에게는 치명적이다.

```
해커의 할 일 목록:
  악성 도구 다운로드/설치      → ❌ 디스크에 못 씀
  앱 설정 파일 몰래 변조       → ❌ 못 씀
  백도어/웹쉘 심기            → ❌ 못 씀
```

도둑이 미술관에 들어왔는데 모든 전시물이 방탄유리에 고정되어 있는 상황 — 침입은 했는데 발 디딜 곳이 없다. 임시 파일이 필요한 앱이라면 루트는 잠그고 `/tmp`에만 emptyDir을 붙인다("전부 잠그고 필요한 곳만 열기" — drop ALL + add와 같은 철학).

이 설정이 강제하는 원칙이 **불변 인프라(immutable infrastructure)**다. 실행 중인 것은 절대 수정하지 않고, 변경은 새 이미지 빌드 → 통째 교체로만 한다(입은 옷 수선 대신 새 옷 갈아입기). 수정이 물리적으로 불가능하니 "지금 도는 컨테이너 = 이미지 그대로"가 보장된다.

### 3.7 seccomp과 SELinux — 커널 차원의 마지막 두 필터

securityContext에는 더 많은 항목이 있지만, 책이 "꼭 체크하라"고 꼽는 나머지 둘은 `seccompProfile`과 `seLinuxOptions`다. 3.4에서 봤듯 컨테이너의 커널 호출에는 중간 검문소가 없으므로, 검문 가능한 유일한 장소인 **커널 자체**에 두 필터를 다는 것이다 — 하나는 "행동"을, 하나는 "대상"을 거른다.

**seccomp — 시스템 콜 필터.** 프로그램은 중요한 일(파일 열기, 네트워크 연결...)을 하려면 커널에 부탁해야 하는데, 그 창구가 **시스템 콜**이고 리눅스엔 300개 이상 있다. 평범한 앱이 실제 쓰는 건 일부 — 나머지는 안 쓰는데 열려 있는 문이고, 컨테이너 탈출의 상당수가 잘 안 쓰이는 시스템 콜의 커널 버그를 찌른다. seccomp은 커널에 "이 프로세스는 **이 목록의 콜만** 쓸 수 있다"고 지시하는 리눅스 커널 기능이며, 허용 목록을 **프로파일**로 묶어 컨테이너/Pod에 적용한다.

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault   # 런타임 기본 프로파일 — 위험한 콜 수십 개 차단, 실무 권장
```

주의할 것 — **쿠버네티스에서 이 필드를 안 적으면 `Unconfined`(필터 없음)가 될 수 있다.** 도커를 직접 쓸 때는 기본 프로파일이 자동 적용되지만, 쿠버네티스는 그렇지 않아서 명시해야 한다. capability와 정반대의 함정이다 — capability는 안 적으면 **너무 많이** 주고, seccomp은 안 적으면 **아예 안 막는다**. 둘 다 "비워두면 안전하겠지"가 틀린다.

커널 = 콜센터, 시스템 콜 = 내선번호 300개, seccomp = "이 고객은 5번·12번·40번 내선만 연결 가능"이라는 교환원 지시다.

**SELinux — 라벨 기반 접근 통제.** 출신부터 특이하다 — 미국 NSA가 만들어 리눅스 커널에 기증한 보안 모듈로, 기존 권한 체계(DAC, 임의 접근 제어)의 두 구멍을 겨냥했다: ① 규칙을 파일 **주인이** 정하므로 `chmod 777` 한 번에 임의로 풀리고, ② **root 앞에서 무력**하다는 것. SELinux의 답은 그 위에 한 겹을 더 얹는 것이다 — 시스템의 모든 것(프로세스, 파일)에 **라벨**을 붙이고, 어떤 라벨이 어떤 라벨에 접근 가능한지를 **정책**으로 정한다. 이 검사는 UID/파일권한과 **별개로 추가로** 돌며, 주인도 정책을 못 풀고 root여도 라벨이 안 맞으면 거부된다(강제 접근 제어, MAC). 회사 건물의 **색깔 출입증** — 사장님(root)이라도 빨간 구역엔 빨간 출입증 없이 못 들어간다. "누구냐(UID)"가 아니라 "무슨 라벨이냐"로 판단하는 것이다.

쿠버네티스에선 `seLinuxOptions`로 Pod 내 **모든 컨테이너와 볼륨**에 커스텀 라벨을 붙인다. 컨테이너 런타임은 보통 컨테이너마다 **고유한 라벨**을 발급하고, 그 컨테이너의 파일들에도 같은 라벨을 붙인다.

```
컨테이너 A (라벨: c1)  →  라벨 c1이 붙은 파일만 접근 가능 ✅
                       →  호스트 파일 (라벨 다름)         접근 거부 ❌
                       →  컨테이너 B의 파일 (라벨 c2)     접근 거부 ❌
```

즉 어찌어찌 탈출해 호스트 파일에 손을 뻗어도, **라벨이 안 맞아서** 커널이 거부한다. 프로세스를 완전히 장악해도 그 프로세스에 붙은 라벨의 한계를 못 벗어난다 — "뚫려도 울타리 안에서 끝나게"라는 이 장의 철학이 커널 심장부에서 반복되는 셈이다. 컨테이너 탈출의 마지막 단계 — 호스트 파일 만지기 — 를 막는 최후의 벽이다. 호스트 OS가 SELinux를 지원해야 하며(RHEL 계열 기본, 우분투 계열은 유사 역할의 AppArmor), 두 모드가 있다.

| 모드 | 하는 일 | 용도 |
|---|---|---|
| **Enforcing** | 위반 = 즉시 **거부** + 기록 | 실전 운영 |
| **Permissive** | 위반 = 통과시키되 **기록만** | 정찰/디버깅 (3.4의 "capability 알아내기"가 이것) |

**두 필터의 구분** — seccomp은 "이 **행동**을 해도 되나"(시스템 콜), SELinux는 "이 **대상**에 접근해도 되나"(라벨). 겹치면 해커는 할 수 있는 행동도, 만질 수 있는 대상도 없어진다.

```
🏁 여기까지 쌓인 방어선 7종
① runAsNonRoot            처음부터 root         ❌
② allowPrivilegeEscalation 실행 중 root 되기     ❌
③ privileged 회피          호스트와 한 몸 되기    ❌
④ drop ALL + add          커널 능력 악용         ❌
⑤ readOnlyRootFilesystem  악성 파일 설치/변조    ❌
⑥ seccompProfile          취약한 커널 창구 찌르기 ❌
⑦ seLinuxOptions          이미지 밖 파일 접근    ❌
```

---

## 4. PSS와 PSA — 개인의 성실함에서 시스템의 강제로

### 4.1 PSS와 PSA — 기준집과 점검관

문제가 하나 남았다. 이 7종 세트를 회사의 수백 개 Pod YAML마다(그것도 Deployment 템플릿 속 깊숙이) 사람이 손으로 넣으면 **반드시 빠뜨린다**. 게다가 넣는 사람은 워크로드 작성자(앱 개발자)인데, 개발자는 조직의 보안 전문가가 아니다. 보안은 가장 약한 고리만큼만 강하다 — 100개 중 99개를 완벽히 잠가도 뚫린 1개로 들어온다. 소방 규정을 입주민 각자에게 맡기는 대신 **건축법 + 소방 점검으로 강제**하듯, 클러스터 차원의 정책이 필요하다.

그 답이 **Pod Security Standards(PSS)** + **Pod Security Admission(PSA)**이다. (구버전의 PodSecurityPolicy는 **v1.25에서 제거**되고 이 체제로 대체됐다.)

```
PSS = 기준집 (법전)      — "안전한 Pod란 이런 것"이라는 공통 언어를 정의
PSA = 점검관 (집행기관)   — Pod "생성(admission) 시점"에 검사해 미달이면 거부

표준과 강제 수단을 분리한 덕에, 같은 PSS를 PSA로 강제해도 되고
Kyverno · OPA Gatekeeper 같은 서드파티로 강제해도 된다.
```

한 가지 오해 방지 — **PSS는 클러스터에 존재하는 YAML/리소스가 아니다.** 공식 문서에 적힌 기준표이고, 그 내용이 PSA 컨트롤러의 코드에 내장되어 있다(`kubectl get pss` 같은 명령은 없다). 자동차 검사소의 배기가스 기준표가 법령집이지 검사소에서 작성하는 서류가 아닌 것과 같다 — 기준은 장비(PSA)에 내장되어 있고, 우리는 접수창구에서 "어느 검사로 할지"만 고른다. 그리고 **고정 메뉴다** — "baseline에서 hostPath만 허용" 같은 편집은 불가능하다. 전임자 PSP가 무한 커스텀의 복잡함으로 망한 교훈에서 일부러 단순화한 것이고, 그 덕에 "restricted"라는 말이 어느 회사·어느 감사에서든 정확히 같은 뜻으로 통하는 **공통 언어**가 됐다. 회사 고유 규칙이 필요해지는 순간이 Kyverno/Gatekeeper(정책을 YAML로 직접 작성)의 차례이며, 실무에선 PSA로 바닥을 깔고 그 위에 커스텀 정책을 얹는 조합이 흔하다.

**PSS의 3등급** — 매우 관대함 → 매우 엄격함 순이며, **누적(cumulative)** 구조다. 누적이란 각 등급이 서로 다른 규칙을 갖는 게 아니라, **아래 등급의 규칙을 전부 포함한 뒤 더 얹는다**는 뜻이다.

```
Privileged  = 규칙 없음
Baseline    = (최소한의 규칙)
Restricted  = Baseline 전부  +  추가 규칙   ← 포함 관계
```

그래서 Restricted를 통과한 Pod은 Baseline도 자동으로 통과한다. 등급을 올리는 것은 규칙을 "바꾸는" 게 아니라 "더 쌓는" 것이다.

| | Privileged | Baseline | Restricted |
|---|---|---|---|
| 제한 | 없음 (allow-by-default) | 최소한 | 최대 |
| 대상 | 신뢰된 사용자, **인프라 워크로드** | 일반 **비중요 앱** | **보안 중요 앱**, 낮은 신뢰 사용자 |
| privileged 컨테이너 | ✅ | ❌ | ❌ |
| root로 실행 | ✅ | ✅ | ❌ (runAsNonRoot 필수) |
| 승급 | ✅ | 일부 제한 | ❌ (allowPrivilegeEscalation:false 필수) |
| 성격 | 의도된 예외 관리 | 도입 용이성 ↔ 알려진 승급 방지의 **균형** | **도입 편의를 희생**하고 최신 모범 사례 강제 |

공항으로 치면 Privileged = 정비사 출입증(활주로까지 통행), Baseline = 일반 승객 검색대(흉기만 걸러냄), Restricted = 국빈 행사장 검문이다. 그리고 눈여겨볼 것 — Restricted가 요구하는 필드(`allowPrivilegeEscalation`, `runAsNonRoot`, `runAsUser`...)는 **전부 이 장 앞에서 배운 설정들**이다. 즉 Restricted = 이 장 모범 답안의 강제판이다.

### 4.2 PSA의 적용 — 네임스페이스 라벨로 거는 정책

**PSA의 적용** — 별도 리소스 없이 **네임스페이스 라벨**로 「등급 + 위반 시 행동」을 지정한다.

"라벨로 정책을 건다"가 낯설다면 — 라벨은 원래 아무 힘 없는 **분류용 포스트잇**(`app: nginx`, `team: payment`)이고, 셀렉터가 그걸 보고 대상을 골라내는 용도다(Service→Pod 연결이 대표 사례). PSA는 그 시스템을 빌려 쓴다: `pod-security.kubernetes.io/` 접두사가 붙은 라벨만 **"자기 앞으로 온 설정 메모"**로 읽는 것이다(접두사 = 수신인 주소). 라벨 자체는 여전히 아무 일도 안 한다 — 팻말을 보고 행동하는 것은 API 서버 속 PSA 컨트롤러다. 호텔 문고리의 "Do Not Disturb" 팻말과 그것을 지키기로 약속된 청소부의 관계와 같다. "별도 리소스 없이"가 강조된 이유는 전임자와의 대비다 — PSP는 전용 리소스 작성 + RBAC 연결이 필요했지만, PSA는 기존 문고리에 팻말만 건다.

```
라벨 공식:  pod-security.kubernetes.io/<행동>: <등급>
                                       └┬─┘   └┬─┘
                          "위반하면 어떻게"    "어느 기준표로"
```

| 행동 | 위반한 Pod은? | 누가 알게 되나 | 비유 |
|---|---|---|---|
| **warn** | 통과 ✅ | 개발자 (kubectl에 경고) | "속도를 줄이시오" 전광판 |
| **audit** | 통과 ✅ | 관리자 (감사 로그) | 몰래 찍는 조사 카메라 |
| **enforce** | **거부 ❌** | 개발자 (배포 실패) | 진짜 단속 카메라 + 차단기 |

```yaml
# Example 23-3. 네임스페이스에 보안 표준 설정
apiVersion: v1
kind: Namespace
metadata:
  name: baseline-namespace
  labels:
    pod-security.kubernetes.io/enforce: baseline       # baseline 미달 → 생성 거부
    pod-security.kubernetes.io/enforce-version: v1.25  # 표준의 "버전" 고정 (선택)
    pod-security.kubernetes.io/warn: restricted        # restricted 미달 → 경고만
    pod-security.kubernetes.io/warn-version: v1.25
```

이 예제의 **이중 잣대**가 영리하다 — 최소선(baseline)은 강제하고, 목표(restricted)는 경고로 유도한다. "최소한은 무조건 지켜. 그리고 목표를 향해 가라고 계속 잔소리할게." 개발자가 경고를 보고 하나씩 고치면, 다 고쳐진 시점에 enforce를 restricted로 올리면 된다.

`version` 라벨은 표준의 특정 버전을 고정한다 — 클러스터를 업그레이드하면 표준의 세부 내용도 바뀔 수 있어서, 고정하지 않으면(기본값 latest) 어제 멀쩡히 배포되던 Pod가 오늘 갑자기 거부되는 사고가 난다. "건축법 기준"이 아니라 "**2025년판 건축법 기준**"으로 심사한다고 못 박는 것이다.

### 4.3 도입 순서 — 기록 먼저, 강제는 나중에

기존 네임스페이스에 적용할 때의 모범 순서도 이제 익숙한 패턴이다 — SELinux의 permissive → enforcing과 같은 "**기록 먼저, 강제는 나중에**"다.

```
① audit만 켬   → 로그로 누가 위반 중인지 조용히 파악 (아무도 안 다침)
② warn 추가    → 개발자들에게 "곧 강제됩니다" 예고
③ 수정 완료 확인
④ enforce 전환 → 안전하게 강제 🔒
   (PSA는 "생성 시점"에만 검사한다. 그래서 enforce를 켜도 이미 도는 Pod은 멀쩡히
    계속 돈다 — 문제없어 보인다. 그러다 롤아웃·스케일아웃·축출·노드 장애로 Pod이
    다시 만들어지는 순간 거부되어 그때서야 터진다. 순서를 안 지키면 새벽 장애다)
⑤ rollout restart → 기존 위반 Pod를 내 손으로 교체 (숨은 마지막 단계)
   (④까지 해도 이미 도는 미달 Pod는 그대로다. 정책과 현실이 어긋난 구간이
    남아 있는 것. 어차피 언젠가 재생성될 거라면 새벽 3시가 아니라 업무 시간에
    직접 눌러서 확인하는 편이 낫다)
```

오해하기 쉬운 지점 — 이 순서는 위 사고 시나리오와 모순이 아니다. 새벽 장애의 범인은 enforce 자체가 아니라 **"미달 Pod가 살아 있는 상태에서" enforce를 켠 것**이고, ①~③은 enforce를 피하는 과정이 아니라 **enforce를 켜도 걸릴 Pod가 0개인 상태를 만드는** 과정이다. 어차피 단속 카메라는 켤 건데, 다들 속도를 줄인 뒤에 켜면 딱지가 0장인 것뿐이다.

그런데 의문이 하나 남는다 — "생성 시점만 검사한다면, audit/warn은 **이미 도는** 위반자를 어떻게 아는가?" 경로가 둘 있다.

```
① enforce 라벨을 붙이는/바꾸는 "그 순간" — PSA가 기존 Pod를 1회 전수 스캔해
   결과를 경고로 뱉는다 (거부·퇴출은 없음. "existing pods ... violate ..." 식)
   ※ 이 스캔은 enforce 라벨에만 걸린다. audit/warn 라벨을 붙이는 것만으로는
     기존 Pod를 훑지 않는다 — 즉 ①은 ②의 병렬 경로가 아니라 지름길이다
② 이후 몇 주간 — 배포·오토스케일·노드 교체로 Pod들이 자연히 재생성되며
   검문소를 지나가고, 그때마다 audit 기록이 쌓여 명단이 완성된다
   (컨테이너 "재시작"은 검사 없음, Pod "재생성"은 검사 발동 — 이 구분이 중요)
```

즉 PSA는 순찰을 도는 대신 **위반자들이 제 발로 검문소를 지나가길 기다리며 명부를 쌓는** 방식이다. 그리고 enforce 전환 직전의 확인 사살로 모의 심사가 있다:

```bash
kubectl label --dry-run=server --overwrite ns my-ns \
  pod-security.kubernetes.io/enforce=restricted
# → 실제 라벨을 붙이지 않고, 기존 Pod 전수 스캔 결과(누가 걸릴지)만 미리 받아본다
#    경고 0건 확인 후 진짜로 전환하면 무사고 ✅
```

### 4.4 명부는 누가 쓰는가 — 세 모드의 출력처

정확히 말하면 검문소를 지나는 것은 **Pod가 아니라 Pod의 설계도**다. 돌고 있는 Pod가 검문소로 걸어갈 리는 없다. 지나가는 것은 "이런 스펙으로 Pod 하나 만들어 달라"는 **요청서**이고, 그것이 통과해야 비로소 etcd에 Pod 객체가 생기고 kubelet이 컨테이너를 띄운다. 한 번 태어난 Pod는 죽을 때까지 검문소 근처에 다시 오지 않는다. Pod가 죽어서 새 Pod가 뜨는 것도 그 Pod의 부활이 아니라, 컨트롤러가 "개수가 안 맞네" 하고 **새 요청서를 쓴 것**이다. 컨테이너 재시작이 검사에서 빠지는 이유도 같다 — Pod 객체가 그대로 살아 있으니 아무도 요청서를 쓸 일이 없고, 노드 안에서 조용히 처리되고 끝난다.

**명부를 쓰는 것은 PSA가 아니다.** PSA는 "이 요청 위반임"이라는 주석(`pod-security.kubernetes.io/audit-violations`)을 감사 이벤트에 **붙이기만** 한다. 그 이벤트를 실제로 기록하는 것은 API 서버의 **감사(audit) 서브시스템**이고, 파일에 쓸지 웹훅으로 보낼지는 감사 백엔드가 정한다. 둘 다 `kube-apiserver` 안에 있지만 부서가 다르다 — **장부가 없으면 딱지는 그냥 사라진다.** `--audit-policy-file`/`--audit-log-path`가 설정돼 있지 않으면(kubeadm 기본값은 꺼져 있다) audit 모드는 성실히 도장을 찍는데 아무 데도 안 남는다. 관리형 클러스터라면 EKS는 컨트롤 플레인 로깅의 `audit`, GKE는 Cloud Logging, AKS는 `kube-audit` 진단 설정을 켜야 보인다. "audit 라벨만 붙이면 알아서 쌓이겠지"가 안 통하는 이유다.

세 모드의 출력처가 다르다는 점도 여기서 갈린다.

```
enforce → API 응답으로 거부 (그 자리에서 끝)
audit   → 감사 로그에 기록      ← 명부는 오직 여기서 쌓인다
warn    → 요청한 클라이언트에게 경고 1회. 저장 안 됨
```

그래서 ②의 몇 주간 명부를 만드는 것은 실질적으로 **`audit` 하나**다. Pod를 만드는 주체는 사람이 아니라 ReplicaSet 컨트롤러이므로, 그때의 `warn`은 컨트롤러에게 날아가고 아무도 보지 못한다. 쿠버네티스가 **warn/audit을 워크로드 리소스(Deployment 등)에도 적용**하는 이유가 이것이다 — `kubectl apply` 하는 **사람**의 화면에 띄우려는 것이다. 반대로 `enforce`는 워크로드 리소스에 적용되지 않고 결과물인 Pod에만 걸린다. 그래서 미달 Deployment는 `apply`가 성공하고, 정작 Pod만 안 뜬다. `kubectl get deploy`는 멀쩡한데 `get pod`가 비어 있는, 원인 찾기 성가신 형태다(범인은 `kubectl describe rs`의 `FailedCreate`에 있다).

한 가지 더 — **enforce를 켠 뒤에도 명부는 계속 쌓인다.** 위의 이중 잣대(`enforce: baseline` + `audit/warn: restricted`)를 쓰면, restricted 기준으로는 위반이지만 baseline은 통과하는 Pod가 정상적으로 뜨면서 동시에 기록된다. **막는 선과 재는 선을 다르게 두는 것**이고, 이것이 다음 등급으로 올라가기 위한 승급 심사 자료가 된다.

```
1단계  enforce: 없음      audit/warn: baseline     ← baseline 위반자 파악
2단계  enforce: baseline  audit/warn: restricted   ← baseline 강제 + restricted 조사
3단계  enforce: restricted                          ← 최종
```

### 4.5 PSA는 고쳐주지 않는다 — non-mutating이라는 선택

마지막으로, **PSA는 고쳐주지 않는다.** 공식 문서의 표현 그대로 "non-mutating admission controller"이며, 미달 Pod에 `runAsNonRoot: true`를 대신 채워 넣는 일 따위는 하지 않는다. 전임자 PSP는 `defaultAllowPrivilegeEscalation`·`defaultAddCapabilities` 같은 필드로 **기본값을 주입해 통과시켰지만**, PSA는 그 기능을 의도적으로 버렸다. 몰래 고쳐주면 매니페스트와 실제 Pod가 달라지고, 다른 클러스터로 옮겼을 때 동작이 달라지기 때문이다. PSA는 "YAML에 적힌 게 전부"를 지킨다.

그 대가는 안 고치면 **아무도 낫게 해주지 않는다**는 것이다. 컨트롤러는 백오프를 두고 무한히 재시도하고, 타임아웃도 자동 롤백도 없다. 다만 피해 양상은 상황마다 다르다 — 롤아웃 중이라면 새 ReplicaSet이 0개에서 멈출 뿐 **기존 Pod는 살아 있어** 서비스는 유지된다(그래서 ⑤를 업무 시간에 직접 하는 게 안전하다). 반면 노드 장애나 축출로 Pod가 죽는 상황에서는 죽은 만큼 채워지지 않아 replica가 **10 → 9 → 8로 서서히 침식**된다. 한 번에 터지지 않아 알람도 늦고, 이것이 "새벽 장애"의 실제 모습이다. 급하면 `enforce`를 한 등급 낮추거나 라벨을 떼서 일단 열고, 고친 뒤 다시 켜는 것이 순서다. 자동으로 값을 채워 넣고 싶다면 그것은 PSA의 일이 아니라 Kyverno·Gatekeeper 같은 **mutating 웹훅**의 몫이다(어드미션은 mutating을 먼저, validating을 나중에 돌리므로 그 조합이 성립한다).

---

## 5. Discussion

### 5.1 컨테이너는 울타리다 — 단, 제대로 설정했을 때만

현실의 골칫거리는 **레거시 앱**이다. 쿠버네티스 보안 통제를 염두에 두지 않고 만들어진 앱 — root로만 돌고, 자기 디렉터리에 파일을 쓰고, 80번 포트를 하드코딩한 — 을 컨테이너에 욱여넣으면, 보안 정책이 엄격한 배포판/환경(OpenShift 등)에서는 배포 자체가 줄줄이 거부된다. 이 장의 지식이 필요한 이유가 그것이다 — 뭐가 왜 막히는지 알아야 앱을 고치든(비특권 포트로 변경, 파일 쓰기 제거) 정책 예외를 신청하든 제대로 판단할 수 있다.

그리고 이 장이 남기는 관점의 전환 — **컨테이너는 세 가지다.**

```
① 패키징 포맷        앱 + 의존성을 한 상자에 ("내 컴에선 됐는데" 해결)
② 자원 격리 수단     CPU/메모리를 나누는 칸막이
③ 보안 울타리        ★ 단, "when configured properly" — 제대로 설정했을 때만
```

대부분 ①②까지만 안다. 이 장의 메시지는 ③이 공짜로 주어지지 않는다는 것이다 — 그냥 돌리면 얇은 비닐 커튼(privileged면 커튼조차 없음)이고, securityContext 7종을 채워야 비로소 진짜 울타리가 된다. 장 제목이 왜 Process **Containment**(가두기)인지가 여기서 완성된다. 컨테이너(container)라는 이름값을 하게 만들려면 울타리를 직접 세워야 한다.

이 관점을 시험하는 질문 하나 — **"그래서 컨테이너는 샌드박스인가?"** 구조적으로 아니다. 샌드박스의 약속은 "안의 코드가 악의적이어도 탈출 불가"인데, 컨테이너는 바닥(커널)이 호스트와 이어져 있다 — 모래놀이통처럼 생겼지만 **바닥이 거실 바닥과 연결**된 셈이라(3.4의 커널 직행), 커널 버그 하나가 탈출구가 된다. 그래서 "신뢰할 수 없는 코드를 컨테이너에서 돌리지 마라"가 업계의 정설이다. 이 장의 7종은 그 바닥에 철판을 겹겹이 대는 작업 — 자사 앱을 "뚫려도 가두는" 데는 충분하지만, 구조 자체를 바꾸진 못한다. 진짜 샌드박스가 필요하다면(멀티테넌트, 사용자 코드 실행 플랫폼) **커널 공유 자체를 끊는** 층으로 올라간다.

```
격리 스펙트럼 (약함 → 강함)
기본 컨테이너      바닥 뚫린 모래통. 샌드박스 아님
+ 7종 세트(이 장)  바닥에 철판 여러 겹. 자사 앱엔 충분 ✅
gVisor            컨테이너와 커널 사이에 "가짜 커널"을 끼워 직행을 차단
Kata Containers   컨테이너마다 경량 VM을 씌워 커널을 아예 따로 지급
VM                완전 별도 커널. 전통적 최강 격리
```

강해질수록 속도·밀도를 내주므로(VM을 버리고 컨테이너로 온 이유가 다시 청구된다), **돌리는 코드의 신뢰도에 따라 층을 고르는** 것이다.

### 5.2 Shift Left — 보안을 왼쪽으로

마지막은 문화 이야기다. 개발 과정을 시간 축으로 그리면:

```
[설계] → [개발] → [테스트] → [배포] → [운영]
 왼쪽 ◄──────────────────────────► 오른쪽

전통 방식: 배포 직전(오른쪽)에 보안 검사
  → "root로 돌면 안 됩니다" / "네?? 출시가 다음 주인데요??" 😱

Shift Left: 개발 첫날(왼쪽)부터 운영 보안을 생각
  → 개발용 네임스페이스에도 운영 수준의 표준 적용 (warn: restricted가 훌륭한 도구)
  → 처음부터 non-root 이미지로 개발 (Dockerfile의 USER 지시어 — 이것 자체가 shift left)
  → 문제를 그날 발견, 그날 수정 → 막판 깜짝 사고(last-minute surprises) 없음
```

건물 다 짓고 소방 점검에서 "비상구가 없네요" 소리를 듣는 것과, **설계 도면 단계에서** 소방 기준을 반영하는 것 — 어느 쪽 수정 비용이 쌀지는 뻔하다.

이름이 주는 오해 하나 — "**맨** 왼쪽으로 옮기라"는 뜻이 아니다. 검사를 설계 단계 한 점으로 몰빵하는 게 아니라, 오른쪽 끝에 몰려 있던 **시작점을 왼쪽으로 당겨 전 구간에 펴 바르는** 것이다("start left"가 더 정확한 이름이라는 말이 있는 이유).

```
전통:        ────────────────────█    (끝에 몰빵)
잘못된 이해:  █────────────────────    (앞에 몰빵)
Shift Left:  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    (시작점만 왼쪽으로, 전 구간에 분산)
```

각 단계에서만 잡히는 문제가 따로 있기 때문이다 — 설계에서는 구조("애초에 root가 필요 없게"), 테스트에서는 돌려봐야 아는 문제(DAST), 운영에서는 출시 후 새로 알려지는 취약점(CVE). 특히 마지막은 왼쪽으로 옮길 수가 없다 — 미래의 취약점은 미래에만 대응 가능하니까. 이 장의 도구들도 실제로 전 구간에 배치되어 있다: 개발의 `warn`, 배포의 `enforce`, 운영 중 24시간 작동하는 seccomp/SELinux. 왼쪽의 활동은 오른쪽 검문을 대체하는 게 아니라, **거기서 걸릴 일을 미리 소멸시키는** 역할이다.

### 핵심 메시지

```
Process Containment의 몫: 뚫린 후의 피해를 컨테이너 안에 가두는 2차 방어선
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

전제      → 검사(1차 방어)는 알려진 위험만 잡는다. 뚫린다고 가정하라
root      → runAsNonRoot로 거부 + allowPrivilegeEscalation:false로 승급 차단
            + 불가피하면 Init 컨테이너로 root 수명 압축
능력      → privileged는 격리의 포기. drop ALL 후 필요한 capability만 add
            (가장 좋은 답은 비특권 포트처럼 권한 필요 자체를 없애는 설계)
디스크    → readOnlyRootFilesystem으로 쓰기 봉쇄 = 불변 인프라 강제
커널      → seccomp(행동/시스템 콜)과 SELinux(대상/라벨)의 이중 필터
강제      → 개인의 성실함 대신 PSS 3등급 + PSA 네임스페이스 라벨로
            (warn/audit로 정찰 → enforce로 전환, version 고정으로 예측 가능하게)
문화      → Shift Left — 이 모든 걸 개발 첫날부터
```

> Process Containment은 **"침입을 막는 패턴이 아니라, 침입자를 가두는 패턴"** 이다.
> root도 아니고, root가 될 수도 없고, 커널 능력도 없고, 파일 하나 못 만들고,
> 위험한 시스템 콜은 차단되고, 자기 이미지 밖은 쳐다보지도 못하게 —
> 최소 권한의 말뚝 일곱 개를 겹쳐 세운 뒤, 그 울타리를 PSS/PSA 정책으로 클러스터 전체에 강제하라.
> 그러면 보안 침해를 포함해, **컨테이너 안에서 일어난 일은 컨테이너 안에 머문다.**

---

## 6. References

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>Restricted 프로파일의 성격은 Kubernetes 공식 문서 <strong>"Pod Security Standards"</strong>에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "Heavily restricted policy, following current Pod hardening best practices."
  </blockquote>
  <div>[해석] "현재의 Pod 하드닝 모범 사례를 따르는, 강하게 제한된 정책." — 4장에서 본 "Restricted = 이 장 모범 답안의 강제판"이 이것이다. 같은 문서는 세 프로파일(Privileged/Baseline/Restricted)의 각 항목별 허용·금지 목록을 표로 제공한다.</div>
  <div style="margin-top:10px;">PodSecurityPolicy는 v1.21에서 사용 중단(deprecated) 선언 후 <strong>v1.25에서 완전히 제거</strong>되었으며, 공식 후계 체제가 PSS + PSA(admission controller)임이 공식 블로그와 문서에 안내되어 있다.</div>
  <div style="margin-top:10px;">seccomp이 프로세스의 시스템 콜을 제한하는 리눅스 커널 기능이라는 정의와 <code>RuntimeDefault</code> 프로파일 사용법은 공식 튜토리얼 "Restrict a Container's Syscalls with seccomp"에서 확인할 수 있다 — 3.7의 근거다.</div>
  <div style="margin-top:10px;">세 모드의 출력처(<code>enforce</code>=거부, <code>audit</code>="the addition of an audit annotation to the event recorded in the audit log", <code>warn</code>="a user-facing warning"), <code>enforce</code>가 워크로드 리소스에는 적용되지 않는다는 점("enforce mode is not applied to workload resources, only to the resulting pod objects"), 그리고 <code>enforce</code> 라벨 추가/변경 시 기존 Pod를 전수 검사해 경고로 돌려준다는 동작("the admission plugin will test each pod in the namespace against the new policy")이 각각 공식 문서에 명시되어 있다. PSA가 <strong>non-mutating</strong>이라는 점과 PSP의 기본값 주입 기능이 사라졌다는 점은 마이그레이션 문서에 있다 — "Pod Security Admission is a non-mutating admission controller, meaning it won't modify pods before validating them."</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/tasks/configure-pod-container/enforce-standards-namespace-labels/">kubernetes.io — Enforce Pod Security Standards with Namespace Labels</a></div>
  <div>→ <a href="https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/">kubernetes.io — Migrate from PodSecurityPolicy to PodSecurity Admission</a></div>
  <div style="margin-top:10px;">Pod Security Admission 문서는 네임스페이스 라벨의 형식(<code>pod-security.kubernetes.io/&lt;MODE&gt;</code>, <code>&lt;MODE&gt;-version</code>)과 세 모드(enforce/audit/warn)의 동작, 그리고 네임스페이스 라벨 변경 시 기존 Pod에 대한 경고 동작을 설명한다 — 4장의 "라벨 = 설정 메모"와 "1회 전수 스캔"의 근거다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/concepts/security/pod-security-standards/">kubernetes.io — Pod Security Standards</a></div>
  <div>→ <a href="https://kubernetes.io/docs/concepts/security/pod-security-admission/">kubernetes.io — Pod Security Admission</a></div>
  <div>→ <a href="https://kubernetes.io/docs/tasks/configure-pod-container/security-context/">kubernetes.io — Configure a Security Context</a></div>
  <div>→ <a href="https://kubernetes.io/docs/tutorials/security/seccomp/">kubernetes.io — Restrict a Container's Syscalls with seccomp</a></div>
</div>
{{< /rawhtml >}}

---
