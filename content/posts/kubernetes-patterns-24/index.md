---
series: ["K8sPatterns"]
title: "K8sPatterns.24 Network Segmentation"
date: 2026-08-31T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "security", "networking", "network-policy", "istio"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.24 Network Segmentation'
  relative: true
summary: "NetworkPolicy와 Istio AuthorizationPolicy로 파드 간 통신을 제한하는 방법. 기본 차단에서 시작해 필요한 경로만 허용한다."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-네임스페이스는-폴더다--방화벽이-아니다" style="color:var(--secondary,inherit);text-decoration:none;">2.1 네임스페이스는 폴더다 — 방화벽이 아니다</a></div>
    <div><a href="#22-옆-팀이-뚫리면-나도-뚫린다--멀티테넌시의-그늘" style="color:var(--secondary,inherit);text-decoration:none;">2.2 옆 팀이 뚫리면 나도 뚫린다 — 멀티테넌시의 그늘</a></div>
    <div><a href="#23-방화벽-티켓의-시대--앱을-아는-사람과-규칙을-짜는-사람이-다르다" style="color:var(--secondary,inherit);text-decoration:none;">2.3 방화벽 티켓의 시대 — 앱을 아는 사람과 규칙을 짜는 사람이 다르다</a></div>
  </div>
  <div><a href="#3-networkpolicy--l3l4-방화벽" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. NetworkPolicy — L3/L4 방화벽</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-두-겹의-애플리케이션-방화벽--l3l4와-l7" style="color:var(--secondary,inherit);text-decoration:none;">3.1 두 겹의 애플리케이션 방화벽 — L3/L4와 L7</a></div>
    <div><a href="#32-networkpolicy--종이는-쿠버네티스가-집행은-cni가" style="color:var(--secondary,inherit);text-decoration:none;">3.2 NetworkPolicy — 종이는 쿠버네티스가, 집행은 CNI가</a></div>
    <div><a href="#33-해부--podselector-ingress-egress" style="color:var(--secondary,inherit);text-decoration:none;">3.3 해부 — podSelector, ingress, egress</a></div>
    <div><a href="#34-라벨로-세그먼트-긋기--이름-직접-vs-역할-출입증" style="color:var(--secondary,inherit);text-decoration:none;">3.4 라벨로 세그먼트 긋기 — 이름 직접 vs 역할 출입증</a></div>
    <div><a href="#35-deny-all로-시작하라--빈-리스트와-빈-규칙의-함정" style="color:var(--secondary,inherit);text-decoration:none;">3.5 deny-all로 시작하라 — 빈 리스트와 빈 규칙의 함정</a></div>
    <div><a href="#36-namespaceselector--비운-것과-안-적은-것은-정반대" style="color:var(--secondary,inherit);text-decoration:none;">3.6 namespaceSelector — 비운 것과 안 적은 것은 정반대</a></div>
    <div><a href="#37-egress--안은-열고-밖은-닫고-policytypes-함정" style="color:var(--secondary,inherit);text-decoration:none;">3.7 egress — 안은 열고 밖은 닫고, policyTypes 함정</a></div>
    <div><a href="#38-도구--녹화inspektor-gadget와-감사cilium" style="color:var(--secondary,inherit);text-decoration:none;">3.8 도구 — 녹화(Inspektor Gadget)와 감사(Cilium)</a></div>
  </div>
  <div><a href="#4-authorizationpolicy--봉투-안을-보는-방화벽" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. AuthorizationPolicy — 봉투 안을 보는 방화벽</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#41-포트로는-부족하다--서비스-메시가-봉투를-여는-이유" style="color:var(--secondary,inherit);text-decoration:none;">4.1 포트로는 부족하다 — 서비스 메시가 봉투를 여는 이유</a></div>
    <div><a href="#42-신원은-어디서-오나--serviceaccount와-mtls" style="color:var(--secondary,inherit);text-decoration:none;">4.2 신원은 어디서 오나 — ServiceAccount와 mTLS</a></div>
    <div><a href="#43-해부--selector-action-rules" style="color:var(--secondary,inherit);text-decoration:none;">4.3 해부 — selector, action, rules</a></div>
    <div><a href="#44-deny와-평가-순서--custom--deny--allow" style="color:var(--secondary,inherit);text-decoration:none;">4.4 DENY와 평가 순서 — CUSTOM → DENY → ALLOW</a></div>
    <div><a href="#45-설정-문서라는-점-그리고-두-검문소-디버깅" style="color:var(--secondary,inherit);text-decoration:none;">4.5 설정 문서라는 점, 그리고 두 검문소 디버깅</a></div>
  </div>
  <div><a href="#5-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. Discussion</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-rbac과-헷갈리지-말-것--쿠버네티스-조작-권한-vs-앱끼리-통신-권한" style="color:var(--secondary,inherit);text-decoration:none;">5.1 RBAC과 헷갈리지 말 것 — 조작 권한 vs 통신 권한</a></div>
    <div><a href="#52-케이블에서-sdn을-거쳐-쿠버네티스로--규칙을-짜는-사람이-바뀌었다" style="color:var(--secondary,inherit);text-decoration:none;">5.2 케이블에서 SDN을 거쳐 쿠버네티스로</a></div>
    <div><a href="#53-ebpf와-cilium--두-겹을-하나로" style="color:var(--secondary,inherit);text-decoration:none;">5.3 eBPF와 Cilium — 두 겹을 하나로</a></div>
  </div>
  <div><a href="#6-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. References</a></div>
</div>
</div>
{{< /rawhtml >}}

---

## 1. Overview

```
Network Segmentation 패턴의 핵심
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"기본은 다 뚫려 있다"를 인정하고, 앱마다 방화벽을 들고 다니게 한다

  기본 상태: flat 네트워크  ← 모든 파드가 모든 파드에 닿는다 (네임스페이스 무관)
                        │  파드 하나 뚫리면 클러스터 전체로 횡이동
                        ▼
  1겹: NetworkPolicy (쿠버네티스 기본, L3/L4)
  ├─ podSelector로 "누구를 지킬지", ingress/egress로 "누구를 들일지"
  ├─ 허용 목록만 존재 — 적힌 것만 열리고 나머지는 자동 차단
  ├─ deny-all 깔고 필요한 문만 열기
  └─ 실제 집행은 CNI (Calico, Cilium ...) — Flannel은 못 함
                        ▼
  2겹: AuthorizationPolicy (Istio, L7)
  ├─ HTTP 메서드·경로·신원(ServiceAccount)까지 본다
  ├─ ALLOW / DENY / AUDIT — "막아라"를 직접 적을 수 있다
  └─ 실제 집행은 사이드카 프록시
                        ▼
  두 검문소를 모두 통과해야 파드에 도달한다 🔒
```

23장이 "뚫린 프로세스를 컨테이너 **안에** 가두는" 이야기였다면, 24장은 그 컨테이너가 **밖으로 뻗는 손**을 자르는 이야기다. 쿠버네티스 네트워크는 기본적으로 **평평(flat)**하다 — 노드가 달라도, 네임스페이스가 달라도, 모든 파드는 다른 모든 파드에 직접 연결할 수 있다. 개발할 때는 아무 설정 없이 서비스끼리 붙으니 편하지만, 보안 관점에서는 파드 하나가 뚫리는 순간 그 파드가 클러스터의 나머지 전부를 두드릴 수 있다는 뜻이다.

이 장의 재미는 그 열린 네트워크 위에 **두 겹의 방화벽을 앱과 함께 배포한다**는 데 있다. 방화벽 장비에 규칙을 넣어달라고 관리자에게 티켓을 내는 게 아니라, 앱을 아는 개발자가 Deployment 옆에 YAML 한 장을 더 두는 것이다. 그리고 그 YAML은 "이건 열어라"만 적는다 — 나머지는 알아서 닫힌다.

---

## 2. Problem

### 2.1 네임스페이스는 폴더다 — 방화벽이 아니다

이 장을 읽기 전에 가장 흔한 오해부터 걷어내야 한다. "네임스페이스로 팀을 나눴으니 격리된 것 아닌가?"

네임스페이스가 실제로 나눠주는 것과 안 나눠주는 것을 표로 보면 이렇다.

| 구분 | 네임스페이스가 나눠주는 것 | 안 나눠주는 것 |
|---|---|---|
| 이름 공간 (같은 이름의 Deployment 공존) | ✅ | |
| RBAC 권한 (`kubectl`로 남의 파드 조회) | ✅ | |
| 리소스 쿼터 | ✅ | |
| **네트워크 트래픽** | | ❌ 그대로 뚫림 |
| 노드/커널 | | ❌ 공유 |

컴퓨터의 폴더와 같다 — 파일을 폴더로 정리하면 보기는 편하지만, 폴더에 넣었다고 다른 프로그램이 그 파일을 못 읽는 건 아니다. 네임스페이스는 파드를 `팀A`, `팀B` 폴더에 나눠 담을 뿐, 팀A 파드가 팀B 파드에게 말 거는 것을 막지 않는다.

"근데 실제로 해보면 다른 네임스페이스 파드에 접근이 안 되던데?"라는 경험이 있다면, 그건 네임스페이스가 막아서가 아니라 **다른 두 가지 때문에 그렇게 보이는** 것이다.

```
하려는 것                          되나?   왜
─────────────────────────────────  ─────  ─────────────────────────────
kubectl get pods -n team-b          ❌     RBAC이 막음 (API 서버 접근)
curl web          (짧은 이름)       ❌     DNS가 내 네임스페이스에서만 찾음
curl web.team-b   (NS 붙임)         ✅     그냥 통과
파드 IP로 직접 접속                  ✅     아무것도 안 막음
```

해커는 위의 두 줄이 아니라 아래 두 줄로 들어온다. 관리 화면(API)은 잠겨 있는데 뒷문(네트워크)은 열려 있는 상태다. 그래서 책은 "네임스페이스는 그룹핑 개념일 뿐"이라고 못 박고 시작한다 — 바닥에 선만 그어놓은 셈이고, 그 선 위에 벽을 올리는 것이 이 장의 일이다.

### 2.2 옆 팀이 뚫리면 나도 뚫린다 — 멀티테넌시의 그늘

이 문제가 가장 아프게 드러나는 곳이 **여러 팀이 클러스터 하나를 나눠 쓰는 멀티테넌시** 환경이다.

```
팀A: 코드 완벽, 보안 철저
팀B: 실수로 구멍 뚫린 이미지 배포
      │
      ▼
해커가 팀B 파드 장악  →  팀A의 DB 파드로 그냥 걸어감 (아무도 안 막음)
      │
      ▼
팀A는 잘못한 게 하나도 없는데 털림
```

혼자 쓰는 클러스터면 리스크가 자기 안에서 끝나지만, 공유 클러스터에서는 **가장 약한 팀의 보안 수준이 클러스터 전체의 보안 수준**이 된다.

책은 멀티테넌시 자체가 쿠버네티스에 완성품으로 들어 있지 않다고 인정한다 — 네임스페이스+RBAC(열쇠), 쿼터(한 집이 물·전기 다 쓰는 것 방지), 스토리지·네트워크 격리(남의 창고·전화), 공유 자원 관리(DNS·CRD) 등 부품이 흩어져 있고 직접 조립해야 한다. 이 장이 맡는 부품은 **네트워크 격리**이며, 저자 스스로 이것이 **soft한** 접근이라고 선을 긋는다. 격리 강도를 스펙트럼으로 놓으면 이렇다.

```
격리 강도 (약함 → 강함)
네임스페이스만              폴더. 선만 그어짐
+ NetworkPolicy (이 장)     선 위에 벽. 자사 팀 간 분리엔 충분 ✅
vcluster                    테넌트마다 가상 컨트롤 플레인 — "가상 독채"
클러스터 분리               다른 건물
```

23장 4.1의 격리 스펙트럼(컨테이너 → gVisor → Kata → VM)과 정확히 같은 구조다. 오른쪽으로 갈수록 안전하고 비싸다.

### 2.3 방화벽 티켓의 시대 — 앱을 아는 사람과 규칙을 짜는 사람이 다르다

그럼 그냥 방화벽을 걸면 되는 것 아닌가? 옛날 방식은 이랬다.

```
개발자: "우리 주문 서비스가 결제 서비스랑 재고 서비스에 붙어야 해요. 포트 8080이랑 5432요."
관리자: "알겠습니다, 방화벽 규칙 추가할게요." (티켓 접수, 3일 후 반영)
```

문제는 세 가지다.

```
① 관리자는 앱을 모른다        — 앱 사정을 아는 건 코드를 짠 사람뿐
② 마이크로서비스면 선이 수백 개 — 서비스 50개가 얽힌 거미줄을 말로 전달해야 함
③ 계속 바뀐다                 — 배포는 하루 열 번, 방화벽 티켓은 그 속도를 못 따라감
```

핵심은 이 문장이다 — **"네트워크 토폴로지 정의는 여전히 애플리케이션 자체와 동떨어져 있다."** 앱을 아는 사람(개발자)과 규칙을 정하는 사람(관리자)이 다른 사람이고, 규칙이 다른 곳(방화벽 장비)에 산다. DevOps로 두 팀이 친해져도 이 구조 자체는 안 바뀐다.

즉 이 장의 목표는: **평평한 기본 네트워크 위에, 앱을 아는 개발자가 앱과 함께 배포하는 방화벽을 겹겹이 세워, 파드 하나가 뚫려도 손이 밖으로 뻗지 못하게 하는 것.**

---

## 3. NetworkPolicy — L3/L4 방화벽

### 3.1 두 겹의 애플리케이션 방화벽 — L3/L4와 L7

쿠버네티스의 답은 23장에서 본 **shift left**의 네트워크판이다. 개발 흐름을 `기획 → 개발 → 테스트 → 배포 → 운영`으로 그렸을 때 맨 오른쪽(운영·관리자)에 있던 네트워크 규칙을 왼쪽(개발·개발자)으로 당겨온다. 앱을 아는 사람과 규칙을 짜는 사람을 **같은 사람**으로 만드는 것이다.

이때 만드는 것이 "애플리케이션 방화벽" — 회사 방화벽 장비가 아니라 **앱 하나하나가 자기 방화벽을 들고 다니는** 그림이다. 주문 서비스를 배포할 때 Deployment YAML 옆에 "나는 결제 서비스랑만 통신함" YAML을 같이 넣는다. 앱이 어디로 옮겨가든 방화벽이 따라간다.

구현 수단은 둘이고, 경쟁 관계가 아니라 **같이 쓰는** 것이다.

| | NetworkPolicy | AuthorizationPolicy (서비스 메시) |
|---|---|---|
| 어디 것 | 쿠버네티스 기본 내장 | Istio (따로 설치) |
| 보는 계층 | L3/L4 — IP, 포트 | L7 — HTTP 경로, 메서드, 신원 |
| 비유 | **봉투 겉면**(주소·우편번호)만 보고 통과 | **봉투를 열어** 내용을 보고 통과 |
| 누가 집행 | CNI 플러그인 (커널) | 사이드카 프록시 (파드 안) |
| "막아라" | 직접 못 적음 (허용만) | `DENY` 액션 있음 |

건물로 치면 NetworkPolicy는 **출입증** — 이 층에 들어올 수 있냐 없냐. 서비스 메시는 **층 안에서 어느 방을 열 수 있고 캐비닛은 보기만 되고 못 꺼내고** 하는 세부 권한이다. 둘 다 쓰면 출입증으로 1차 거르고, 안에서 2차로 거른다. 책은 기본 내장이라 설치할 게 없는 NetworkPolicy부터 간다.

### 3.2 NetworkPolicy — 종이는 쿠버네티스가, 집행은 CNI가

NetworkPolicy는 파드의 들어오는(ingress) 연결과 나가는(egress) 연결에 규칙을 거는 쿠버네티스 리소스다. 그런데 이 장에서 **가장 먼저 새겨야 할 사실**이 하나 있다.

```
NetworkPolicy는 규칙을 "적는 것"이고, 실제로 "막는 것"은 CNI 플러그인이다.
```

쿠버네티스 API 서버는 NetworkPolicy YAML을 받아 저장할 뿐이다. 그걸 읽고 실제로 패킷을 떨어뜨리는 건 CNI(Container Network Interface) 플러그인 — 파드에 IP를 주고, 가상 네트워크 선을 꽂고, 노드 간 경로를 잡아주는 **파드 네트워크 담당 부품**이다. 쿠버네티스 본체에는 안 들어 있고 골라서 깐다(아파트 관리사무소가 통신사를 불러 인터넷 선을 깔아주듯). 그리고 **모든 CNI가 NetworkPolicy를 지원하는 것은 아니다.**

| CNI | NetworkPolicy | 비고 |
|---|---|---|
| Flannel | ❌ | 연결만 해줌. 정책은 저장만 되고 아무것도 안 막힘 |
| Calico | ✅ | 가장 흔한 선택 |
| Cilium | ✅ | eBPF 기반, L7까지 (5.3) |
| EKS / GKE / AKS | ✅ | 기본이거나 옵션 |
| Minikube | ✅ | `--cni=calico` 등 |

여기서 이 장에서 가장 조심해야 할 함정이 나온다 — CNI가 지원하지 않으면 `kubectl apply`는 **성공이라고 뜬다.** 에러도 경고도 없다. 그런데 아무것도 안 막힌다. 방화벽 걸었다고 안심하고 있는데 문이 그대로 열려 있는 상태다. 그래서 정책을 처음 걸어보면 반드시 `curl`로 **실제로 막히는지 직접 확인**해야 한다. "YAML이 들어갔다"와 "동작한다"는 다른 문장이다.

두 상황을 구분해 두자.

```
CNI가 아예 없음          → 파드가 IP를 못 받아 ContainerCreating에서 멈춤, 노드 NotReady
                          (프리한 게 아니라 네트워크 자체가 없음 — kubeadm init 직후 그 상태)
NetworkPolicy 미지원 CNI → 다 연결됨, 아무것도 안 막힘 (chapter 처음의 flat network)
지원 CNI                 → 다 연결됨, 정책 걸면 막힘
```

내 클러스터가 어느 줄인지는 `kubectl get pods -n kube-system`에 calico/cilium/flannel 중 뭐가 떠 있는지 보면 된다.

### 3.3 해부 — podSelector, ingress, egress

NetworkPolicy는 딱 두 부분이다.

```
누구한테 걸 건가   → spec.podSelector
무슨 규칙인가      → ingress / egress
```

책의 첫 예제 — "DB 파드에는 backend 파드만 들어올 수 있다."

```yaml
# Example 24-1. 인그레스 트래픽을 허용하는 간단한 NetworkPolicy
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: allow-database
spec:
  podSelector:              # ❶ 누구를 지킬 건가 → DB 파드
    matchLabels:
      app: chili-shop
      id: database
  ingress:                  # ❷ 들어오는 규칙 목록 (여러 개면 OR)
    - from:                 #    이 규칙의 출발지 목록
        - podSelector:      # ❸ 누구를 들여보낼 건가 → backend 파드
            matchLabels:
              app: chili-shop
              id: backend
```

`podSelector`가 두 번 나와서 헷갈리기 쉬운데, **위치가 뜻을 정한다.**

| 위치 | 역할 | 비유 |
|---|---|---|
| `spec.podSelector` (바깥) | 이 정책이 **보호하는** 파드 | 문지기 세울 집 |
| `ingress[].from[].podSelector` (안쪽) | **들여보낼** 파드 | 출입 명단 |

파드를 이름으로 고르지 않고 **라벨**로 고르는 이유는, 파드 이름이 `backend-7d9f8-abc12`처럼 랜덤이고 계속 바뀌기 때문이다. 라벨은 Deployment의 `template.metadata.labels`에 적어두면 거기서 나오는 파드마다 자동으로 붙는 이름표 스티커라, 파드가 죽고 새로 떠도 정책이 자동으로 따라붙는다. Service가 파드를 찾는 그 `selector`와 완전히 같은 원리다.

그리고 이 예제에서 **적혀 있지 않은 것**이 중요하다.

```
frontend → DB     ❌ 막힘.    명단에 없으니까 — "deny"라고 안 적었는데도
포트 없음          → backend는 DB의 모든 포트 접근 가능. 좁히려면 ports: 추가
네임스페이스 없음   → 같은 네임스페이스의 backend만 (3.6)
egress 없음        → DB가 나가는 건 제한 없음. 이 정책은 들어오는 것만 건드림
```

첫 줄이 NetworkPolicy의 핵심 철학이다 — **"막아라"라고 적는 칸이 없다.** 허용 목록(allow list)만 적는다.

```
파드에 정책 없음      → 다 열림
파드에 정책 하나라도  → 적힌 것만 열리고 나머지는 자동 차단
```

왜 거부 규칙을 안 만들었을까? 허용과 거부가 공존하면 **충돌**이 생긴다(정책 A는 frontend 허용, 정책 B는 frontend 거부 — 누가 이기나?). 우선순위·순서를 정해야 하고, 정책이 많아질수록 "결국 열린 거야 닫힌 거야" 계산이 지옥이 된다. 허용만 있으면 단순하다 — **모든 정책의 허용 목록을 합집합**하면 끝이고 순서는 무관하다. 대신 "다 열되 이거 하나만 막아"가 불편한데, 그 자리를 뒤에서 Istio의 `DENY`가 채운다(4장).

규칙의 재료도 정리해 두자. `from`(egress면 `to`)에 올 수 있는 것은 셋이고, 옆에 `ports`를 붙일 수 있다.

```
from / to 에 올 수 있는 것
  podSelector        클러스터 안 파드 (라벨)
  namespaceSelector  다른 네임스페이스 (라벨)
  ipBlock            파드가 아닌 것 — 외부 서버, 노드, VPN 대역 (CIDR + except)

ports               그 규칙에 한해 "이 포트만" (from 과 AND)
```

YAML의 `-`는 "목록의 한 칸"이라 `ingress` 아래 `- from`은 규칙 하나, `from` 아래 `- podSelector`는 출발지 하나다. 규칙이 여러 개면 OR(하나라도 맞으면 통과), 한 규칙 안의 `from`과 `ports`는 AND(둘 다 맞아야)다.

### 3.4 라벨로 세그먼트 긋기 — 이름 직접 vs 역할 출입증

2.3에서 "개발자가 관리자에게 의존성을 말로 설명해야 한다"가 문제였다. 라벨은 그 답이다 — 개발자 머릿속의 의존성 그림을 **그대로 YAML로 옮긴다.**

```
frontend → backend → database          (개발자가 아는 그림)

라벨:  id: frontend / id: backend / id: database
정책:  backend 파드: from frontend
       database 파드: from backend
그림에 없는 선(frontend → database)은 정책에 안 적으니 자동으로 막힘
```

예제가 라벨을 굳이 두 개(`app`, `id`) 쓰는 이유도 여기 있다. 둘 다 그냥 라벨이고 예약어가 아니지만, 저자가 용도를 나눠둔 것이다.

```
app: chili-shop   → 어느 앱 소속인가 (아파트 이름)    = 세그먼트 경계
id:  database     → 그 앱 안에서 뭐냐 (호수)          = 세그먼트 안의 역할
```

`id: backend`만 쓰면 같은 네임스페이스의 다른 앱 backend가 딸려 들어오고, `app: chili-shop`만 쓰면 frontend·backend·database가 다 잡혀 "backend만"을 못 고른다. 그래서 "래미안 101호"처럼 둘을 합쳐야 딱 한 집이 나온다. 여기서 `app`은 컨테이너 하나가 아니라 **앱 전체**를 가리키는 가장 큰 단위다 — chili-shop의 파드가 9개면 9개 전부에 이 라벨이 붙는다.

```
앱 (app: chili-shop)
 ├── frontend Deployment → 파드 ×3      ← 이 Deployment/StatefulSet이 "워크로드"
 ├── backend Deployment  → 파드 ×5
 └── database StatefulSet → 파드 ×1
```

라벨은 파드에 붙고(컨테이너에는 없다), NetworkPolicy도 파드 단위로만 본다.

책은 라벨링 방식을 두 가지로 나눈다.

**방법 ① — 워크로드별 고유 라벨(이름 직접 부르기).** 워크로드 하나당 라벨 값 하나. `id: database`는 database StatefulSet **전용**이고 다른 워크로드가 같은 값을 쓰면 안 된다(정책이 엉뚱한 데도 걸린다). 같은 워크로드에서 나온 파드 3개가 같은 값을 갖는 건 당연히 괜찮다 — 그게 "하나"다.

**방법 ② — 역할 라벨(출입증).** 정책에 이름을 안 적고 역할을 적는다.

```yaml
# Example 24-2. 역할 기반 네트워크 세그먼트 정의
kind: Pod
metadata:
  labels:
    app: chili-shop
    id: backend
    role-database-client: 'true'    # DB 출입증
    role-cache-client: 'true'       # 캐시 출입증
---
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: allow-database-client
spec:
  podSelector:
    matchLabels:
      app: chili-shop
      id: database
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: chili-shop
              role-database-client: 'true'   # "DB 출입증 있는 애 누구든"
```

backend라는 이름이 정책 어디에도 안 나온다. 나중에 `reporting` 서비스가 DB를 써야 하면, reporting 파드에 `role-database-client: 'true'` 한 줄 붙이면 끝 — 정책은 안 건드린다. (`'true'`에 따옴표가 있는 건 라벨 값이 문자열이어야 해서다. 따옴표 없이 `true`는 YAML이 불리언으로 읽어 에러가 난다. 키 이름 자체에 역할을 넣은 건 같은 키를 파드 하나에 두 번 못 달기 때문이다.)

| | 방법 ① 이름 직접 | 방법 ② 역할 출입증 |
|---|---|---|
| 새 워크로드 추가 | 정책 수정 필요 | 스티커만 붙임 |
| 정책 읽기 | **한눈에** — 정책 파일 하나로 "backend가 DB 쓰는구나" | 정책엔 "출입증 소지자"만 있어 **누가 갖고 있는지 워크로드를 뒤져야** 함 |
| 어울리는 상황 | 컴포넌트 적고 잘 안 바뀔 때 | 컴포넌트 많고 자주 늘 때 |

출입 명단에 "김철수, 이영희"가 적힌 것(①)과 "직원증 소지자"라고 적힌 것(②)의 차이다. 저자는 ②가 유연하긴 하지만 ①이 읽기 쉬워 자주 낫다는 입장이다.

### 3.5 deny-all로 시작하라 — 빈 리스트와 빈 규칙의 함정

지금까지 한 것은 "DB 파드에 자물쇠 달기"다. 그런데 자물쇠 안 단 파드는? 그냥 열려 있다.

```
database  → 정책 있음 → 잠김 ✅
backend   → 정책 없음 → 열림 ❌ 아무나 들어옴
frontend  → 정책 없음 → 열림 ❌
```

파드 10개면 정책 10개를 다 만들어야 하고 하나 까먹으면 거기가 구멍이다. 다음 달에 누가 새 서비스를 띄우며 정책을 안 만들면 또 구멍이다. 원인은 **기본값이 "다 열림"**이라서다 — 안전한 쪽이 아니라 위험한 쪽이 기본이라, 잠그는 걸 하나하나 해야 하고 안 한 건 열려 있다.

23장 3.5의 capability("비워두면 0개가 아니라 후한 기본 세트")와 정확히 같은 함정이고, 답도 같다 — **기본값을 뒤집는다.** 일단 다 막고 시작한다.

```yaml
# Example 24-3. 들어오는 트래픽 전체 거부
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: deny-all
spec:
  podSelector: {}    # ❶ 조건 없음 = 이 네임스페이스의 모든 파드
  ingress: []        # ❷ 허용 명단이 텅 빔 = 아무도 못 들어옴
```

세 줄이 네임스페이스 전체를 잠근다. 이 위에 24-1 같은 허용 정책을 얹으면, 정책은 **합집합**이므로 deny-all이 다 막아도 allow-database가 backend를 열어준다. 빼먹은 파드는 막혀 있고(안전), 새로 만든 파드도 막혀 있어(안전) 필요하면 그때 연다. 실수해도 "안 되네?" 하고 알아채지, 조용히 뚫려 있진 않다.

여기서 이 장의 두 번째 큰 함정 — **괄호 하나 차이로 정반대가 된다.**

| 적은 것 | 뜻 | 결과 |
|---|---|---|
| `ingress: []` | 규칙 0개 | 아무도 못 들어옴 |
| `ingress: [{}]` | 규칙 1개인데 **조건 없음** | **아무나 들어옴** |
| `ingress:` 안 적음 | 규칙 0개 | 아무도 못 들어옴 |

`{}`는 "조건 없음"이라 `podSelector`에서는 "전부 선택"이었다. 규칙 자리에 `{}`를 넣어도 "조건 없이 다 허용"이 되어 `[{}]`는 allow-all이 된다.

한 가지 아쉬운 점 — NetworkPolicy는 **네임스페이스 범위**라 "클러스터 전체 기본 차단"을 한 방에 하는 방법이 기본 기능엔 없다. 네임스페이스 20개면 deny-all을 20번 만들어야 하고, 새 네임스페이스가 생길 때 빼먹으면 거기만 다시 flat이 된다. 해법은 CNI 확장(Calico `GlobalNetworkPolicy`, Cilium `CiliumClusterwideNetworkPolicy`), 네임스페이스 생성 자동화에 deny-all 포함, 또는 Kyverno/Gatekeeper로 "정책 없는 네임스페이스는 생성 거부"다. 쿠버네티스 쪽에서도 `AdminNetworkPolicy`라는 전역 정책 규격을 만들고 있지만 CNI가 별도 지원해야 하는 단계다. 이 아쉬움을 Istio가 어떻게 푸는지는 4장에서 본다.

### 3.6 namespaceSelector — 비운 것과 안 적은 것은 정반대

2.1에서 "다른 네임스페이스는 컨트롤 못 한다"고 했는데, 3.3의 재료 목록에는 `namespaceSelector`가 있다. 모순처럼 보이지만 **위치가 다르다.**

```
못 하는 것:  다른 네임스페이스 파드를 "지키기"
             spec.podSelector 는 내 네임스페이스 안에서만 찾는다
             (team-a 에 만든 정책으로 team-b 의 DB 를 잠글 수 없다)

할 수 있는 것: 다른 네임스페이스에서 오는 걸 "허용/차단"
             from / to 안에 namespaceSelector 를 적는다
```

우리 집 문에 자물쇠 다는 건 우리 집만 되지만, 우리 집 출입 명단에 옆집 사람 이름 올리는 건 된다.

```yaml
from:
  - namespaceSelector:          # monitoring 네임스페이스 "안의"
      matchLabels:
        team: monitoring
    podSelector:                # prometheus 파드만   (같은 - 항목 → AND)
      matchLabels:
        app: prometheus
```

`-`를 따로 붙이면 OR가 된다 — "monitoring NS 전부 **또는** 내 NS의 prometheus". 들여쓰기 한 칸이 의미를 가르니 실제로 자주 실수하는 지점이다.

책의 Table 24-1은 `podSelector`와 `namespaceSelector`의 여섯 가지 조합을 나열하는데, 외울 필요 없이 규칙 두 개로 환원된다.

```
규칙 1:  {} 는 "조건 없음 = 전부"
         podSelector: {}        → 파드 전부
         namespaceSelector: {}  → 네임스페이스 전부

규칙 2:  안 적으면(---) 기본값이 다르다
         namespaceSelector 안 적음 → 내 네임스페이스만
         podSelector 안 적음       → 파드 전부
```

즉 `namespaceSelector`는 **비운 것(`{}`)과 안 적은 것이 정반대**다.

```yaml
# 내 네임스페이스의 backend만
from:
  - podSelector: {matchLabels: {id: backend}}

# 모든 네임스페이스의 backend   ← {} 하나 붙인 것만으로 범위가 클러스터 전체
from:
  - namespaceSelector: {}
    podSelector: {matchLabels: {id: backend}}
```

한 줄 요약 — **`{}`는 "다"고, 안 적으면 "여기"다.** 실무에서 제일 조심할 것은 `namespaceSelector: {}`를 무심코 붙여 다른 팀 네임스페이스까지 열어버리는 일이다.

### 3.7 egress — 안은 열고 밖은 닫고, policyTypes 함정

egress는 ingress의 거울상이다 — `from`이 `to`로 바뀌고 나머지는 같다. 그런데 **egress deny-all은 못 한다.**

```
파드가 curl backend 를 하면 제일 먼저 하는 일
  → "backend 가 IP 몇 번이지?" 하고 DNS(kube-system 의 CoreDNS 파드)에 물어본다
  → 나가는 걸 다 막으면 DNS 도 못 물어봐서, backend 가 열려 있어도 이름을 못 찾는다
```

게다가 ingress로 "DB는 backend만 받아"를 이미 막았는데 egress까지 빡빡하게 하면 backend 쪽에도 "DB로 나가도 됨"을 또 적어야 한다 — 같은 화살표를 양쪽에서 두 번 적는 셈이다. 그래서 저자의 절충안은 이렇다.

```
클러스터 안 → 안    다 허용 (DNS 포함)
클러스터 안 → 밖    다 차단  ← 해커가 데이터를 빼돌리는 길을 막는다 (blast radius 축소)
누가 누구에게 들어오나는 ingress 로만 정한다
```

문(ingress)만 잘 잠그면 안에서 돌아다니는 건 놔둬도 된다 — 어차피 목적지 문이 잠겨 있다. 대신 밖으로 나가는 건 막아서, 들어오긴 했는데 아무 데도 못 가게 한다.

```yaml
# Example 24-4. 클러스터 내부로 나가는 것만 허용
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: egress-allow-internal-only
spec:
  policyTypes:              # ❶ "나는 egress 만 담당" — 이게 없으면 사고 (아래)
    - Egress
  podSelector: {}           # ❷ 이 네임스페이스의 모든 파드
  egress:
    - to:
        - namespaceSelector: {}   # ❸ 모든 네임스페이스의 모든 "파드"
```

어떻게 밖을 막았을까? `namespaceSelector: {}`는 모든 네임스페이스의 모든 **파드**다. 클러스터 밖 서버(구글, 외부 API)는 파드가 아니라 어느 네임스페이스에도 없으니 명단에 못 들어가고 자동으로 막힌다 — "deny"라고 안 쓰고 밖을 막았다. DNS는 CoreDNS **파드**니까 명단에 들어가 정상 동작한다.

이 예제의 진짜 교훈은 `policyTypes`다. 이 필드는 정책이 **어느 방향을 담당하는지** 선언하는 칸인데, 안 적으면 쿠버네티스가 추측한다.

```
policyTypes 를 안 적으면
  · Ingress 는 "항상" 포함
  · Egress 는 egress: 섹션이 있을 때만 포함
```

비대칭이다. `ingress:`만 적으면 egress는 안 건드리는데, `egress:`만 적으면 **Ingress까지 딸려 온다.** 그리고 딸려 온 Ingress에 규칙이 없으니 빈 목록 = 다 막힘. 나가는 것만 정리하려던 정책이 모든 파드의 들어오는 문을 잠가버린다.

"`egress:`라고 명시했는데도 추측한다고?" — 그렇다. `egress:` 섹션은 "나가는 규칙의 **내용**"이지 "이 정책의 **종류**"가 아니다. "그럼 ingress는 안 건드리는 거지?"는 별도 질문이고 그 답은 `policyTypes`에서만 한다. 쿠버네티스 입장에서는 "정책이 걸렸다 = 일단 ingress는 잠근다"가 기본 태도다(원래 ingress 제한용으로 만들어졌고 egress는 나중에 붙었다). 설계가 직관적이진 않으니 **egress 정책이면 `policyTypes: [Egress]`를 반사적으로 붙이는** 습관이 실전 해법이다.

| `policyTypes` | 실제 적용 |
|---|---|
| 안 적음 + ingress만 있음 | Ingress |
| 안 적음 + egress만 있음 | **Ingress + Egress** ← 함정 |
| `[Egress]` | Egress만 |
| `[Ingress, Egress]` | 둘 다 |

밖은 막았으니 이제 밖에 나가야 하는 파드(결제 → 외부 결제 API, 알림 → 슬랙)에게만 문을 따로 연다. 밖은 파드가 아니니 IP로 적는다.

```yaml
# Example 24-5. IP 대역으로 외부 접근 허용 (except 문법 예시)
kind: NetworkPolicy
apiVersion: networking.k8s.io/v1
metadata:
  name: allow-external-ips
spec:
  policyTypes: [Egress]     # ★ 책 예제에는 이 줄이 빠져 있다 — 그대로 쓰면 모든 파드의 ingress 가 잠긴다
  podSelector: {}
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0             # 세상 모든 IP 로 나가도 되는데…
            except:
              - 192.168.0.0/16          # …이 대역(보통 사내망)은 빼고
              - 172.23.42.0/24
```

책 예제는 `except` 문법을 보여주려 범위를 넓게 잡은 것이고, 실제 "결제 파드에 결제 API만"이라면 `podSelector`를 좁히고 `cidr: 203.0.113.10/32`처럼 한 주소만 적는다.

**내부 egress까지 잠글 거면 절대 막으면 안 되는 둘.** 24-4보다 더 빡빡하게 "안에서도 필요한 데만" 가고 싶다면 최소 이 둘은 열어야 한다.

| 뭐 | 왜 | 어떻게 |
|---|---|---|
| DNS | 안 열면 이름을 못 찾아 아무 데도 못 감 | `kube-system` NS로 **53 UDP + TCP** (응답이 크면 TCP로 넘어간다) |
| API 서버 | 오퍼레이터·컨트롤러가 쿠버네티스와 대화하려면 | 라벨이 없어 **IP로** — `kubectl get endpoints -n default kubernetes`로 확인 후 `ipBlock` + 6443 |

일반 앱이면 DNS만 챙기면 되고, API 서버는 컨트롤러를 만들 때만 신경 쓰면 된다. (`Endpoints`는 최근 버전에서 `EndpointSlice`로 넘어가는 중이라 `kubectl get endpointslices -n default`로도 같은 정보가 나온다.)

### 3.8 도구 — 녹화(Inspektor Gadget)와 감사(Cilium)

서비스 10개면 allow 정책 10개 + deny-all + egress + DNS 예외… YAML이 금방 수십 장이 된다. 책의 첫 조언은 처음부터 다 짜려 하지 말고 **레시피를 복사해서 고쳐 쓰라**는 것이다(GitHub의 *Kubernetes Network Policy Recipes*에 흔한 패턴이 YAML로 정리돼 있다).

진짜 문제는 **이미 돌아가는 시스템**에 정책을 나중에 끼울 때다 — 누가 누구를 부르는지 문서도 없고 만든 사람은 퇴사했다. 여기서 두 종류의 도구가 등장하며, 둘 다 23장 3.4에서 본 "**기록 먼저, 강제는 나중에**"(SELinux permissive → enforcing)의 네트워크판이다.

```
녹화 방식 — Inspektor Gadget
  정책 없이 앱을 돌리며 실제 트래픽을 커널(eBPF)에서 녹화
  "frontend→backend:8080", "backend→db:5432" … 를 모으면 그게 의존성 그래프
  → NetworkPolicy YAML 자동 생성 (kubectl gadget advise network-policy)

감사 방식 — Cilium policy audit mode
  deny-all 정책을 "걸어 놓되 실제로 막지는 않는" 모드로 돌림
  정책에 어긋나는 트래픽을 통과시키면서 "켰으면 이게 막혔을 거야"만 기록
  → 위반 목록이 곧 필요한 허용 목록 → 정책 수정 → 감사 모드 끄고 진짜 차단
```

eBPF는 리눅스 커널 안에 **샌드박스된 미니 프로그램을 안전하게 꽂는** 기술이다. 모든 패킷은 커널을 지나므로 커널에서 보면 다 보이는데, 원래 커널에 뭘 넣는 건 실수 한 번에 서버가 뻗는 위험한 일이었다. eBPF 프로그램은 들어가기 전에 검증기가 검사해(무한 루프·이상한 메모리 접근 거부) 커널 안에서 돌면서도 커널을 못 죽인다. 앱 코드를 안 건드리고 사이드카도 안 붙이고, 앱은 관찰당하는지도 모른다 — 도청기가 아니라 **CCTV**다. 브라우저 확장 프로그램이 크롬 소스를 안 고치고 기능을 붙이듯, 리눅스 커널의 차세대 플러그인 아키텍처라 불린다.

두 도구 모두에게 붙는 같은 경고 — **안 돌린 경로는 기록에 없다.** 한 달에 한 번 도는 정산 배치, 장애 때만 뜨는 복구 로직이 녹화 기간에 안 돌면 정책에서 빠지고, 나중에 그게 돌 때 막혀서 터진다. 그래서 책은 녹화 중에 **통합 테스트를 전부 돌려 모든 경로를 한 번씩 밟게 하라**고 한다. 도구는 마법이 아니고, 뭘 돌리느냐가 결과를 정한다.

---

## 4. AuthorizationPolicy — 봉투 안을 보는 방화벽

### 4.1 포트로는 부족하다 — 서비스 메시가 봉투를 여는 이유

NetworkPolicy로 "frontend는 backend 8080에 접근 가능"까지 했다. 그런데 backend가 이런 API를 갖고 있다면?

```
GET    /orders         ← frontend 가 써도 됨
POST   /orders         ← frontend 가 써도 됨
DELETE /orders/all     ← 관리자만
GET    /admin/users    ← 관리자만
```

8080 포트를 열면 이 넷이 **다 열린다.** 포트 하나에 API 수십 개가 매달려 있는데 포트 단위로만 막으니 세밀하게 안 된다. L7을 보려면 **패킷 안을 열어 HTTP를 해석**해야 하고, CNI는 IP·포트만 보고 지나보내는 구조라 길목에 뭔가를 세워야 한다. 그것이 **서비스 메시**다.

```
[frontend 파드]                              [backend 파드]
  앱 → 사이드카 프록시  ──HTTP──▶  사이드카 프록시 → 앱
                                       ↑
                              여기서 경로·메서드·신원 검사
```

서비스 메시는 암호화·재시도·로깅·권한처럼 **모든 앱이 똑같이 해야 하는 일**을 앱 밖으로 빼서 공통 부품(사이드카 프록시, 주로 Envoy)이 대신하게 한다. 앱은 `http://backend`로 보낼 뿐인데 실제로는 프록시가 가로채 처리한다. (파드마다 프록시가 붙어 무거운 탓에, Istio ambient 모드나 Cilium처럼 노드당 프록시 하나·eBPF로 가로채는 방식이 최근 흐름이다.) 책은 Istio를 예로 들되 Istio 전체가 아니라 **CRD 하나 — `AuthorizationPolicy`**만 본다.

CRD(CustomResourceDefinition)는 쿠버네티스에 새 리소스 **종류**를 등록하는 방법이다. Istio를 깔면 `AuthorizationPolicy`, `VirtualService` 같은 종류가 새로 생겨 `kubectl apply`로 똑같이 쓸 수 있다. 그 YAML 안의 `source`, `operation`은 CRD가 아니라 그 종류의 **필드**(칸)다 — Pod의 `containers`, `image`가 별도 리소스가 아닌 것과 같다.

### 4.2 신원은 어디서 오나 — ServiceAccount와 mTLS

먼저 이 인가가 어떤 신원 위에서 도는지 흐름부터 보자.

```
[준비]  Deployment YAML 의 serviceAccountName: frontend
          → 파드 생성, Istio 가 사이드카 주입
          → Istio 컨트롤 플레인(istiod)이 인증서 발급
             신원: cluster.local/ns/chili-shop/sa/frontend  ← ServiceAccount 기반
          → 사이드카가 보관, 만료 전 자동 순환(rotation)

[요청]  frontend 앱: "GET /orders" → http://backend:8080
          │
          ▼  frontend 사이드카가 가로챔, 인증서 꺼냄
          │  backend 사이드카와 mTLS 악수 ◀── 인증: "너 누구야?" 서로 신분증 교환
          ▼
   ─── NetworkPolicy ─── CNI 가 검사: 출발 IP·포트 허용?     ◀── 1차 (L3/L4)
          │ ❌ → 타임아웃                               ✅
          ▼
   backend 사이드카: 상대 인증서에서 신원 읽음 → "frontend 구나"
          AuthorizationPolicy 확인                        ◀── 2차 (L7), 인가: "이거 해도 돼?"
            principals: frontend? ✅  methods: GET? ✅  paths: /orders? ✅
          │ ❌ → 403 Forbidden                          ✅
          ▼
   backend 앱이 요청 처리
```

용어를 짚어두자. **인증(authentication)**은 "너 누구야?", **인가(authorization)**는 "너 이거 해도 돼?"이며 순서가 있다. **인증서**는 "나 frontend야"를 증명하는 위조 불가능한 디지털 신분증이고, **TLS**는 서버만 신분증을 보여주는 암호화, **mTLS**(mutual)는 **양쪽 다** 보여주는 것이다. NetworkPolicy가 "이 IP에서 왔으니 frontend겠지"라고 IP → 파드 → 라벨로 역추적하는 데 반해(IP는 속일 수 있다), Istio는 인증서를 직접 보니 못 속인다. **ServiceAccount**는 파드가 쓰는 계정(사람용 User와 별개)이고 그 이름이 신원에 박힌다.

### 4.3 해부 — selector, action, rules

이제 리소스 자체. 구조는 NetworkPolicy와 놀랄 만큼 닮았다 — 대상 고르고(`selector`), 액션 정하고(`action`), 규칙 적는다(`rules`).

```yaml
# Example 24-6. Prometheus 가 모든 앱의 /metrics 만 긁어갈 수 있게
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: prometheus-scraper
  namespace: istio-system            # ❶ 여기 두면 "모든 네임스페이스"에 적용
spec:
  selector:                          # ❷ 누구를 지킬 건가 (없으면 NS 전체)
    matchLabels:
      has-metrics: "true"            #    역할 출입증 방식 (3.4 방법 ②)
  action: ALLOW                      # ❸ 규칙에 맞으면 통과
  rules:
    - from:
        - source:
            namespaces: ["prometheus"]   # ❹ 누가 — prometheus 네임스페이스에서
      to:
        - operation:
            methods: ["GET"]             # ❺ 뭘 — GET /metrics/* 만
            paths: ["/metrics/*"]
```

NetworkPolicy로는 못 하던 것 셋이 이 한 장에 들어 있다.

```
① 클러스터 전역 정책     istio-system 은 특별 취급 — 거기 둔 정책은 모든 NS 에 자동 적용
                          (3.5 의 아쉬움 해결. 새 NS 가 생겨도 자동으로 잠긴다)
② HTTP 수준 필터         methods, paths — "8080 은 열되 GET /metrics 만"
③ DENY 액션              "막아라"를 직접 적을 수 있다 (아래)
```

| 액션 | 뜻 |
|---|---|
| `ALLOW` | 규칙에 맞으면 통과 |
| `DENY` | 규칙에 맞으면 차단 |
| `AUDIT` | 통과시키되 로그만 (Cilium 감사 모드와 같은 발상) |
| `CUSTOM` | 외부 서버(OAuth 등)에 물어봄 |

### 4.4 DENY와 평가 순서 — CUSTOM → DENY → ALLOW

`DENY`가 생기면 3.3에서 미룬 충돌 문제가 돌아오는데, Istio는 우선순위를 못 박아 푼다 — **`CUSTOM → DENY → ALLOW`**, DENY가 하나라도 걸리면 ALLOW가 있어도 막힌다. 유연함을 얻는 대신 규칙 하나를 더 외우는 셈이다. 규칙의 논리 구조는 NetworkPolicy와 같다 — 규칙 여러 개는 OR, 한 규칙 안의 `from`/`to`/`when`은 AND, 한 필드 안의 값 여러 개(`methods: [GET, POST]`)는 OR. (책 본문의 "모든 규칙이 만족되어야 한다"는 규칙 하나 안의 조건을 말하려던 표현으로 보이며, 규칙 목록 전체가 AND라면 규칙을 두 개 적는 순간 거의 아무것도 안 맞게 된다.)

당연히 여기도 **deny-all이 먼저**다. 24-6은 허용만 적었으므로 기본이 다 열려 있으면 의미가 없다.

```yaml
# Example 24-7. 클러스터 전체 기본 거부
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: istio-system
spec: {}       # selector 없음(모든 파드) + action 기본 ALLOW + rules 없음(허용 0개) = 전부 거부
```

`spec: {}` 한 줄이 클러스터 전체를 잠근다 — NetworkPolicy의 `ingress: []`와 같은 원리("ALLOW인데 허용할 게 없음")에 `istio-system`의 전역 효과가 합쳐진 것이다. 운영 중이라면 `action: AUDIT`으로 먼저 돌려 뭐가 막힐지 보고 진짜 deny-all로 바꾸는 게 안전하다.

### 4.5 설정 문서라는 점, 그리고 두 검문소 디버깅

두 가지를 덧붙여 둔다. 첫째, 이 YAML은 **실행되는 프로그램이 아니라 설정 문서**다 — Deployment처럼 파드가 생기지 않는다. `kubectl apply`로 저장되면 `istiod`(28장의 Operator 패턴)가 감지해 각 사이드카에 규칙을 뿌리고, 사이드카가 요청마다 검사한다. 벽에 붙이는 공지문과 그걸 읽고 집행하는 경비원의 관계다(NetworkPolicy도 `kubectl apply → API 서버 → CNI가 읽어 커널 규칙으로 변환`으로 같은 구조). 둘째, 사이드카가 주입되지 않은 파드는 AuthorizationPolicy가 검사하지 못한다 — 그래서 NetworkPolicy deny-all이 밑에서 받쳐줘야 하며, 책이 "둘을 함께 쓰라"고 하는 이유다.

두 검문소를 다 봐야 하니 디버깅은 까다롭지만, 증상으로 범인을 대충 가릴 수 있다.

| 증상 | 범인 |
|---|---|
| 타임아웃, 연결 자체가 안 됨 | NetworkPolicy (커널에서 패킷 드롭) |
| 연결은 되는데 403 Forbidden | AuthorizationPolicy (사이드카가 응답) |

---

## 5. Discussion

### 5.1 RBAC과 헷갈리지 말 것 — 쿠버네티스 조작 권한 vs 앱끼리 통신 권한

쿠버네티스에서 "authorization"이 두 군데서 나오는데 완전히 다른 것이다. 같은 클러스터의 두 상황으로 보자.

```
상황 1 — 개발자 민수가 노트북에서
  kubectl delete deployment payment -n chili-shop
  → 이 요청은 "쿠버네티스 API 서버"로 간다 (파드가 아니라 쿠버네티스에게 "지워줘")
  → API 서버가 확인: 민수에게 이 권한 있나?          = RBAC (26장)

상황 2 — frontend 파드가 앱 코드로
  DELETE http://backend:8080/orders/123
  → 쿠버네티스는 전혀 모른다. 파드에서 파드로 가는 HTTP 일 뿐
  → backend 사이드카가 확인: frontend 가 이거 해도 되나? = AuthorizationPolicy (이 장)
```

| | RBAC | AuthorizationPolicy |
|---|---|---|
| 요청이 어디로 | 쿠버네티스 API 서버 | 내 앱 파드 |
| 누구의 권한 | 사람, 도구, 오퍼레이터 | 파드끼리 |
| 비유 | **건물 관리 권한** — 누가 방을 만들고 부수나 | **방끼리 왕래 규칙** — 101호가 502호에 택배 놓고 올 수 있나 |

둘은 서로 안 만난다. 민수에게 RBAC 전권을 줘도 민수가 frontend 파드 안에서 `DELETE /orders`를 날리면 AuthorizationPolicy가 막고, AuthorizationPolicy가 아무리 빡빡해도 `kubectl delete`로 파드 자체를 지우는 건 RBAC 영역이다. 관리사무소 권한이 있다고 남의 집 냉장고를 열 수 있는 게 아니고, 입주민 규칙이 빡빡하다고 관리사무소가 방을 못 부수는 게 아니다.

한 줄로 — **RBAC = 쿠버네티스를 조작할 권한, AuthorizationPolicy = 앱끼리 통신할 권한.** 책이 "접근 제어(RBAC)는 주로 오퍼레이터에게 유용하다"고 덧붙이는 이유는, 오퍼레이터가 API 서버에 "내 CRD 변화 알려줘"를 계속 물어보기 때문이다 — 3.7에서 API 서버 IP를 열어줘야 한다고 한 것과 같은 맥락이다.

### 5.2 케이블에서 SDN을 거쳐 쿠버네티스로 — 규칙을 짜는 사람이 바뀌었다

책의 Discussion은 이 패턴을 네트워크 역사의 세 번째 단계로 놓는다.

```
1단계  케이블         서버 A 와 B 가 통신 못 하게 하려면? 선을 안 꽂으면 됨
                      완벽하게 안전, 완벽하게 안 유연 — 바꾸려면 사람이 서버실에 감

2단계  가상화 + SDN    VM 수십 개를 케이블로는 못 나눔 → 스위치·방화벽이 소프트웨어가 됨
                      관리자가 화면에서 클릭으로 연결·차단
                      그래도 "규칙을 짜는 사람"은 여전히 앱을 모르는 관리자

3단계  쿠버네티스 정책  평평한 기본 네트워크 위에 개발자가 YAML 로 세그먼트를 "덮어씌움"
                      앱을 아는 사람이, 앱 옆에서, 앱과 함께 배포 (shift left)
```

SDN의 핵심 아이디어인 **컨트롤 플레인(어디로 보낼지 결정)과 데이터 플레인(실제로 보냄)의 분리**는 이 장에서 본 모든 것에 그대로 들어 있다 — 관제탑은 비행기를 직접 안 몰고 지시만 하듯, 정책을 읽고 규칙을 계산하는 쪽(istiod, Calico 컨트롤러)과 실제로 패킷을 막는 쪽(사이드카, 커널의 iptables/eBPF)이 나뉜다. 그래서 정책을 바꿔도 트래픽은 계속 흐르고, 새 지시만 받으면 된다.

"덮어씌운다(overlay)"는 표현도 정확하다 — 기본 네트워크는 건드리지 않고 여전히 flat이다. 그 **위에** 정책이라는 층을 얹어 통과·차단을 정하고, 정책을 다 지우면 다시 flat으로 돌아간다. 23장에서 컨테이너가 "제대로 설정했을 때만" 울타리였듯, 쿠버네티스 네트워크도 정책을 얹었을 때만 세그먼트가 된다.

### 5.3 eBPF와 Cilium — 두 겹을 하나로

이 장의 불편함은 두 개를 따로 써야 한다는 것이었다 — YAML도 두 종류, 집행 주체도 둘(CNI/사이드카), 디버깅도 두 군데. 책의 마지막 문단은 그 불편함이 사라지는 방향을 가리킨다.

```yaml
# CiliumNetworkPolicy — 리소스 하나에 L3/L4 와 L7 을 같이 적는다
ingress:
  - fromEndpoints:
      - matchLabels:
          id: frontend            # ← L3/L4: 누가
    toPorts:
      - ports:
          - port: "8080"
        rules:
          http:
            - method: GET         # ← L7: 뭘
              path: /orders
```

가능한 이유는 eBPF가 **커널에서 패킷 안을 열어볼 수 있어서**다. 4장에서 "L7을 보려면 길목에 프록시를 세워야 한다"고 했는데, eBPF는 커널 자체가 길목이라 파드마다 사이드카를 안 붙여도 된다. 집행 주체 하나, 리소스 하나.

| | 집행 주체 | L3/L4 | L7 |
|---|---|---|---|
| 책의 방식 | CNI + Istio 사이드카 | NetworkPolicy | AuthorizationPolicy |
| Cilium | eBPF 하나 | CiliumNetworkPolicy | CiliumNetworkPolicy |

책이 쓰인 시점(2023) 기준으로 "앞으로의 쿠버네티스 버전에서"라는 전망이었고, 지금은 Cilium이 꽤 표준에 가까워졌으며 Istio도 사이드카 없는 ambient 모드로 같은 방향을 가고 있다. 다만 어느 도구를 쓰든 **패턴 자체는 그대로**다 — 기본은 다 뚫려 있고, 앱을 아는 사람이 라벨로 세그먼트를 긋고, deny-all에서 시작해 필요한 문만 연다.

### 핵심 메시지

```
Network Segmentation 의 몫: 뚫린 파드의 "손"이 밖으로 뻗지 못하게 하는 앱 방화벽
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

전제      → 네임스페이스는 폴더일 뿐 방화벽이 아니다. 기본은 flat, 다 뚫려 있다
1겹       → NetworkPolicy — podSelector 로 지킬 대상, ingress/egress 로 들일 대상
            허용 목록만 존재: 적힌 것만 열리고 나머지는 자동 차단
            집행은 CNI — Flannel 은 못 하고, 지원 안 되면 조용히 아무것도 안 막힌다
라벨      → app 으로 세그먼트 경계, id/role 로 역할. 이름 직접(읽기 쉬움) vs 출입증(유연함)
기본값    → deny-all 을 깔고 필요한 문만 연다. [] 는 잠금, [{}] 는 개방
egress    → 클러스터 안은 열고 밖은 닫는다. DNS(53 UDP/TCP)는 항상 열어라
함정      → egress 정책엔 policyTypes: [Egress] 를 반사적으로. {} 는 "다", 안 적으면 "여기"
도구      → 녹화(Inspektor Gadget)·감사(Cilium) — 단, 안 돌린 경로는 기록에 없다
2겹       → AuthorizationPolicy — HTTP 메서드·경로·신원(ServiceAccount) 까지, DENY 가능
            istio-system 에 두면 전역, spec: {} 한 줄로 클러스터 전체 deny-all
구분      → RBAC 은 쿠버네티스를 조작할 권한, AuthorizationPolicy 는 앱끼리 통신할 권한
문화      → Shift Left — 방화벽 티켓 대신, 앱을 아는 개발자가 앱 옆에 YAML 한 장
```

> Network Segmentation 은 **"연결을 만드는 패턴이 아니라, 연결을 끊는 패턴"** 이다.
> 기본으로 주어진 평평한 네트워크 위에, 앱을 아는 사람이 라벨로 선을 긋고,
> 일단 전부 막은 뒤 그림에 있는 화살표만 하나씩 열고,
> 봉투 겉면(IP·포트)과 봉투 속(HTTP·신원) 두 검문소를 겹쳐 세워라.
> 그러면 파드 하나가 뚫려도, **그 파드가 닿을 수 있는 곳은 원래 닿아야 했던 곳뿐이다.**
---

## 6. References

{{< rawhtml >}}
<div style="border-left:2px solid var(--secondary,#888);padding:2px 16px;margin:0.6rem 0 1.2rem;font-size:15px;line-height:1.75;opacity:0.92;">
  <div>파드가 기본적으로 격리되어 있지 않다는 사실은 Kubernetes 공식 문서 <strong>"Network Policies"</strong>에 명시되어 있다.</div>
  <blockquote style="margin:10px 0;padding-left:12px;border-left:2px solid var(--secondary,#888);font-style:italic;">
    "By default, a pod is non-isolated for ingress; all inbound connections are allowed."
  </blockquote>
  <div>[해석] "기본적으로 파드는 인그레스에 대해 격리되어 있지 않다. 모든 들어오는 연결이 허용된다." — 2.1의 "네임스페이스는 폴더다"와 3.5의 "기본값이 다 열림"의 근거다. 같은 문서는 <code>policyTypes</code>를 생략했을 때의 기본값 결정 규칙(3.7), <code>podSelector</code>와 <code>namespaceSelector</code>를 같은 항목에 둘 때와 따로 둘 때의 AND/OR 차이(3.6), 그리고 NetworkPolicy가 네트워크 플러그인(CNI)의 지원 없이는 아무 효과가 없다는 점(3.2)을 설명한다.</div>
  <div style="margin-top:10px;">Istio의 <strong>AuthorizationPolicy</strong> 레퍼런스는 <code>selector</code>·<code>action</code>·<code>rules</code>의 구조, 루트 네임스페이스(<code>istio-system</code>)에 둔 정책의 전역 적용, 그리고 CUSTOM → DENY → ALLOW의 평가 순서를 정의한다 — 4장의 근거다.</div>
  <div style="margin-top:10px;">책의 예제에서 눈에 띈 오탈자 — Problem 절의 "imposing isolation constraints"는 문맥상 <em>no</em>가 빠진 것으로 보이고, Example 24-2 주석의 "backend Pod"는 database Pod, Example 24-5에는 <code>policyTypes: [Egress]</code>가 빠져 있다. 규칙 평가에 대한 "all of the rules must be satisfied"도 실제 Istio 동작(규칙 간 OR)과 다르다.</div>
  <div style="margin-top:10px;">→ <a href="https://kubernetes.io/docs/concepts/services-networking/network-policies/">kubernetes.io — Network Policies</a></div>
  <div>→ <a href="https://istio.io/latest/docs/reference/config/security/authorization-policy/">istio.io — Authorization Policy</a></div>
  <div>→ <a href="https://github.com/ahmetb/kubernetes-network-policy-recipes">GitHub — Kubernetes Network Policy Recipes</a></div>
  <div>→ <a href="https://github.com/inspektor-gadget/inspektor-gadget">GitHub — Inspektor Gadget</a></div>
  <div>→ <a href="https://docs.cilium.io/">docs.cilium.io — Cilium Documentation</a></div>
</div>
{{< /rawhtml >}}
