---
title: "Admission Webhook"
summary: "API 서버가 객체를 저장하기 직전, 외부 HTTP 서버에 물어보는 확장 지점. 요청을 고치거나 거부할 수 있다."
categories: ["쿠버네티스", "API"]
tags: ["kubernetes", "api", "admission", "webhook"]
aliases_search: ["어드미션 웹훅", "어드미션", "admission", "mutating", "validating", "뮤테이팅", "밸리데이팅", "웹훅"]
---

## 1. 개요

**Admission Webhook**은 API 서버가 객체를 etcd 에 저장하기 직전에 호출하는 외부 HTTP 서버다. 쿠버네티스가 "이거 저장해도 되나? 고칠 데 있나?" 하고 남에게 물어보는 지점이다.

쿠버네티스 코드를 고치지 않고 조직 규칙을 집행할 수 있는 자리이며, 사이드카 자동 주입도 여기서 일어난다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 260" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="요청이 인증 인가를 지나 Mutating 웹훅에서 수정되고 스키마 검증을 거쳐 Validating 웹훅에서 통과 여부가 결정된 뒤 etcd 에 저장되는 흐름">
  <defs>
    <marker id="aw-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="16" y="86" width="86" height="52" rx="4" fill="#fbe0c4" stroke="#d9a86a"/>
  <text x="59" y="108" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">kubectl</text>
  <text x="59" y="125" text-anchor="middle" font-size="10" fill="#5a3d18">apply</text>

  <rect x="130" y="34" width="470" height="156" rx="6" fill="none" stroke="var(--content,#444)" stroke-width="1.6"/>
  <text x="365" y="56" text-anchor="middle" font-size="12.5" font-weight="600" fill="var(--content,#333)">API 서버</text>

  <rect x="146" y="88" width="86" height="48" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="189" y="110" text-anchor="middle" font-size="10.5" font-weight="600" fill="#1b3f63">인증·인가</text>
  <text x="189" y="126" text-anchor="middle" font-size="9.5" fill="#1b3f63">누구·자격</text>

  <rect x="248" y="88" width="96" height="48" rx="4" fill="#4caf82"/>
  <text x="296" y="110" text-anchor="middle" font-size="10.5" font-weight="600" fill="#fff">Mutating</text>
  <text x="296" y="126" text-anchor="middle" font-size="9.5" fill="#e9f7f1">고친다</text>

  <rect x="360" y="88" width="96" height="48" rx="4" fill="#cfe3f5" stroke="#2f6ea8"/>
  <text x="408" y="110" text-anchor="middle" font-size="10.5" font-weight="600" fill="#1b3f63">스키마 검증</text>
  <text x="408" y="126" text-anchor="middle" font-size="9.5" fill="#1b3f63">내장</text>

  <rect x="472" y="88" width="112" height="48" rx="4" fill="#5b9bd5"/>
  <text x="528" y="110" text-anchor="middle" font-size="10.5" font-weight="600" fill="#fff">Validating</text>
  <text x="528" y="126" text-anchor="middle" font-size="9.5" fill="#eaf3fb">통과 / 거부만</text>

  <rect x="640" y="86" width="104" height="52" rx="4" fill="#8e44ad"/>
  <text x="692" y="117" text-anchor="middle" font-size="12" font-weight="600" fill="#fff">etcd</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#aw-ar)">
    <path d="M102,112 H142"/>
    <path d="M232,112 H244"/>
    <path d="M344,112 H356"/>
    <path d="M456,112 H468"/>
    <path d="M584,112 H636"/>
  </g>

  <rect x="248" y="196" width="96" height="30" rx="4" fill="none" stroke="#4caf82" stroke-dasharray="4 3"/>
  <text x="296" y="216" text-anchor="middle" font-size="10" fill="#2e9c6d">내 웹훅 서버</text>
  <rect x="472" y="196" width="112" height="30" rx="4" fill="none" stroke="#2f6ea8" stroke-dasharray="4 3"/>
  <text x="528" y="216" text-anchor="middle" font-size="10" fill="#2f6ea8">내 웹훅 서버</text>
  <path d="M296,140 V192" stroke="var(--secondary,#888)" stroke-width="1.2" stroke-dasharray="4 3" fill="none"/>
  <path d="M528,140 V192" stroke="var(--secondary,#888)" stroke-width="1.2" stroke-dasharray="4 3" fill="none"/>

  <text x="380" y="250" text-anchor="middle" font-size="12" fill="var(--content,#333)">고치는 쪽이 먼저, 검사하는 쪽이 나중 — 최종 결과물을 봐야 하기 때문</text>
</svg>
</div>
{{< /rawhtml >}}

## 2. 두 종류

| | Mutating | Validating |
|---|---|---|
| 할 수 있는 일 | 객체를 **고친다** | 통과 / 거부만 |
| 순서 | 먼저 | 나중 |
| 쓰임 | 사이드카 주입, 기본값 채우기 | 정책 위반 차단 |

순서가 이렇게 정해진 이유는 단순하다. **고치는 쪽이 나중에 오면 검사가 무의미해진다.** 검사를 통과한 뒤에 누가 내용을 바꿔버리면 검사한 의미가 없다. 그래서 다 고쳐놓고 최종 결과물을 검사한다.

공식 문서도 최종 상태를 봐야 하는 웹훅은 반드시 validating 을 쓰라고 못 박는다 — mutating 단계에서 본 객체는 그 뒤에 또 바뀔 수 있기 때문이다.

## 3. AdmissionReview

API 서버와 웹훅은 `AdmissionReview` 라는 JSON 을 주고받는다.

**요청** — "이 객체를 이 사용자가 이렇게 만들려고 한다"

**응답** — 거부하려면 이렇게

```json
{ "allowed": false, "status": { "message": "이미지는 사내 레지스트리만 허용" } }
```

고치려면 이렇게

```json
{
  "allowed": true,
  "patch": "W3sib3AiOiJhZGQiLCJwYXRoIjoi...",
  "patchType": "JSONPatch"
}
```

`patch` 는 **base64 로 인코딩된 JSON Patch** 다. "객체를 통째로 돌려주는" 게 아니라 "어디를 어떻게 바꿔라"만 보낸다.

```json
[{ "op": "add", "path": "/spec/containers/-", "value": { "name": "vault-agent", ... } }]
```

사이드카 주입의 실체가 이것이다. 내가 낸 YAML 에 없던 컨테이너가 이 패치로 끼어든다.

## 4. failurePolicy

웹훅 서버가 죽으면 어떻게 되는가. 이 한 필드가 정한다.

| 값 | 웹훅이 응답하지 않으면 | 결과 |
|---|---|---|
| `Fail` (기본) | 요청을 **거부** | 안전하지만, 웹훅이 죽으면 배포가 전부 막힌다 |
| `Ignore` | 요청을 **통과** | 계속 돌아가지만, 정책이 조용히 무시된다 |

어느 쪽도 공짜가 아니다.

```
보안 정책 웹훅   → Fail   막혀서 못 뜨는 게, 검사 없이 뜨는 것보다 낫다
편의 기능 웹훅   → Ignore 사이드카 못 붙는다고 배포까지 막을 이유는 없다
```

타임아웃 기본값은 10초이고, 공식 문서는 **짧게 잡으라**고 권한다. `Fail` + 긴 타임아웃 조합이면 웹훅 하나가 느려질 때 클러스터 전체 배포가 그만큼 지연된다.

## 5. 순환 의존과 교착

공식 문서가 가장 강하게 경고하는 지점이다.

> Admission webhooks are essentially part of the cluster control-plane. You should write and deploy them with great caution.

웹훅은 **컨트롤 플레인의 일부**다. 잘못 만들면 클러스터가 스스로를 잠근다.

```
전형적인 교착
  웹훅이 "모든 Pod 를 검사한다" 로 설정됨  (namespaceSelector 없이)
        ↓
  웹훅 서버 자신도 Pod 다
        ↓
  웹훅 Pod 를 띄우려면 → 웹훅에게 물어봐야 함 → 그 웹훅이 아직 안 떴음
        ↓
  영원히 못 뜬다 (failurePolicy: Fail 이면 완전 정지)
```

그래서 실무에서는 `kube-system` 과 웹훅 자신의 네임스페이스를 검사 대상에서 제외한다. 공식 문서의 표현으로는 **자기가 의존하는 컴포넌트의 요청을 가로채지 말라**는 것이다.

## 6. reinvocationPolicy

웹훅이 여러 개일 때 생기는 문제. A 웹훅이 먼저 돌고, 그 뒤 B 웹훅이 객체를 고치면 **A 는 자기가 본 것과 다른 최종 객체를 갖게 된다.**

| 값 | 동작 |
|---|---|
| `Never` (기본) | 한 번만 호출 |
| `IfNeeded` | 다른 웹훅이 객체를 고쳤으면 **다시 호출** |

`IfNeeded` 는 편해 보이지만 웹훅이 **여러 번 실행되어도 결과가 같아야**(멱등) 안전하다. 사이드카 주입 웹훅이 이걸 안 지키면 컨테이너가 두 개 붙는다.

## 7. 등록

`kubectl apply` 로 등록하는 리소스다. 재시작이 필요 없어서 문서 제목이 *Dynamic* Admission Control 이다.

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy.example.com
webhooks:
- name: pod-policy.example.com
  rules:                          # 어떤 요청을 가로챌지
  - apiGroups:   [""]
    apiVersions: ["v1"]
    operations:  ["CREATE"]
    resources:   ["pods"]
  clientConfig:                   # 어디로 물어볼지
    service:
      namespace: example-namespace
      name: example-service
    caBundle: <CA_BUNDLE>         # HTTPS 필수
  admissionReviewVersions: ["v1"]
  sideEffects: None
  timeoutSeconds: 5
  failurePolicy: Fail
```

직접 서버를 짜는 대신 **OPA Gatekeeper 나 Kyverno** 로 정책만 선언하는 방식이 일반적이다. 웹훅 서버 구현·TLS 인증서 관리·교착 회피를 대신 해준다.

## 8. 관련 문서

- **apiVersion** — `admissionregistration.k8s.io/v1` 그룹 → [apiVersion](/wiki/apiversion/)
- **Sidecar** — 주입되는 대상 → [Sidecar](/wiki/sidecar/)
- [CRD](/wiki/crd/) — 웹훅이 검증·변형하는 사용자 정의 리소스

## 9. 출처

두 종류의 순서, 응답 필드, `failurePolicy`, 교착 경고는 공식 문서 "Dynamic Admission Control" 에 근거한다.

> "Mutating admission webhooks are invoked first, and can modify objects sent to the API server to enforce custom defaults. After all object modifications are complete, and after the incoming object is validated by the API server, validating admission webhooks are invoked."

> "Admission webhooks are essentially part of the cluster control-plane. You should write and deploy them with great caution."

> "Default timeout for a webhook call is 10 seconds. You can set the timeout and it is encouraged to use a short timeout for webhooks."

- [Kubernetes — Dynamic Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/)
- [Kubernetes — Admission Controllers Reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
