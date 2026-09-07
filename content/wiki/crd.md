---
title: "CRD"
summary: "쿠버네티스에 새 리소스 종류를 추가하는 방법. kubectl 로 다룰 수 있는 나만의 kind 를 만든다."
categories: ["쿠버네티스", "API"]
tags: ["kubernetes", "api", "extension"]
aliases_search: ["custom resource definition", "커스텀 리소스", "커스텀 리소스 정의", "custom resource", "씨알디"]
---

## 1. 개요

**CRD**(CustomResourceDefinition)는 쿠버네티스에 **새로운 리소스 종류를 등록**하는 리소스다. 등록하고 나면 내가 만든 `kind` 를 Pod 나 Deployment 와 똑같이 다룰 수 있다.

```bash
kubectl get sealedsecrets          # bitnami.com 이 만든 종류
kubectl get scaledobjects          # keda.sh 가 만든 종류
kubectl describe vpa my-app        # autoscaling.k8s.io 가 만든 종류
```

쿠버네티스를 다시 빌드하지 않고 API 를 늘리는 방법이며, 프로그래밍 없이 YAML 하나로 된다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 250" style="width:100%;min-width:620px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CRD 를 등록하면 API 서버가 새 종류를 알게 되고, 그 종류의 객체를 kubectl 로 만들 수 있으며, 컨트롤러가 그것을 보고 실제 자원을 만든다">
  <defs>
    <marker id="cr-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="20" y="34" width="150" height="50" rx="4" fill="none" stroke="#2e9c6d" stroke-width="1.5"/>
  <text x="95" y="55" text-anchor="middle" font-size="11.5" font-weight="600" fill="#2f6ea8">① CRD 등록</text>
  <text x="95" y="72" text-anchor="middle" font-size="10" fill="#2e9c6d">kind: Foo 라는 게 있다</text>

  <rect x="20" y="146" width="150" height="50" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="95" y="167" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">② 객체 생성</text>
  <text x="95" y="184" text-anchor="middle" font-size="10" fill="#5a3d18">kind: Foo 짜리 YAML</text>

  <rect x="250" y="60" width="200" height="110" rx="6" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="350" y="88" text-anchor="middle" font-size="12.5" font-weight="600" fill="#1b3f63">API 서버</text>
  <text x="350" y="112" text-anchor="middle" font-size="10.5" fill="#1b3f63">스키마 검증 · 저장</text>
  <text x="350" y="132" text-anchor="middle" font-size="10.5" fill="#1b3f63">kubectl 지원</text>
  <text x="350" y="152" text-anchor="middle" font-size="10.5" fill="#1b3f63">RBAC · 감사 로그</text>

  <rect x="530" y="34" width="210" height="52" rx="4" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="635" y="55" text-anchor="middle" font-size="11.5" font-weight="600" fill="#2f6ea8">etcd 에 저장</text>
  <text x="635" y="72" text-anchor="middle" font-size="10" fill="#8e44ad">여기까지가 CRD 의 전부</text>

  <rect x="530" y="132" width="210" height="66" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="635" y="156" text-anchor="middle" font-size="11.5" font-weight="600" fill="#2f6ea8">③ 컨트롤러 (별도)</text>
  <text x="635" y="174" text-anchor="middle" font-size="10" fill="#2f6ea8">보고 있다가 실제 자원을 만든다</text>
  <text x="635" y="190" text-anchor="middle" font-size="10" fill="#2f6ea8">없으면 아무 일도 안 일어난다</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#cr-ar)">
    <path d="M170,66 H246"/>
    <path d="M170,166 H246"/>
    <path d="M450,90 H526"/>
    <path d="M450,150 H526"/>
  </g>

  <text x="380" y="232" text-anchor="middle" font-size="12" fill="var(--content,#333)">CRD 는 "그릇"만 만든다 — 담긴 것을 보고 일하는 주체는 따로 있다</text>
</svg>
</div>
{{< /rawhtml >}}

## 2. 컨트롤러와의 분리

가장 많이 오해하는 지점이다. **CRD 를 만들고 객체를 생성해도 아무 일도 일어나지 않는다.**

```bash
kubectl apply -f my-backup.yaml    # kind: Backup
kubectl get backups                # 목록에 뜬다
# 백업? 안 된다. 아무도 안 봤으니까
```

공식 문서는 커스텀 리소스 자체의 기능을 "**구조화된 데이터를 저장하고 조회**"하는 것이라고만 말한다. 값이 잘 생긴 YAML 인지 검사해서 etcd 에 넣어주는 것까지다.

실제로 일이 일어나려면 **컨트롤러**가 필요하다. 그 객체를 지켜보다가 실제 자원을 만드는 프로그램이다.

```
CRD + 컨트롤러 = 오퍼레이터
```

`SealedSecret` 을 만들면 Secret 이 생기는 것은 CRD 때문이 아니라 Bitnami 컨트롤러가 그걸 보고 복호화하기 때문이다. 컨트롤러를 지우면 YAML 은 남아 있는데 아무 일도 안 일어난다.

## 3. 기본 리소스와 같은 대우

직접 만든 종류인데도 기본 리소스와 똑같은 대우를 받는다.

| | 내용 |
|---|---|
| kubectl | `get` `describe` `edit` `delete` 전부 동작 |
| RBAC | 이 종류에 대한 권한을 Role 로 제어 |
| 감사 로그 | 누가 언제 만들었는지 기록 |
| 규약 | `.spec` `.status` `.metadata` 구조 |
| watch | 변경을 구독할 수 있어 컨트롤러가 붙는다 |

직접 API 서버를 짜서 이걸 다 만들려면 큰 작업이다. YAML 하나로 얻는 게 이것이다.

## 4. ConfigMap 과의 갈림길

설정을 담는 것이 목적이라면 ConfigMap 으로 충분할 때가 많다. 공식 문서가 기준을 제시한다.

| 상황 | 선택 |
|---|---|
| `mysql.cnf` 처럼 **이미 잘 정의된 설정 파일 형식**이 있다 | ConfigMap |
| Pod 안 프로그램이 그 파일을 읽어 스스로 설정하면 끝 | ConfigMap |
| 파일이 바뀌면 롤링 업데이트로 반영하고 싶다 | ConfigMap |
| `kubectl` 로 직접 다루고 싶다 | **CRD** |
| 변경을 감시해 자동화를 붙이고 싶다 | **CRD** |
| `.spec` / `.status` 규약을 쓰고 싶다 | **CRD** |
| 다른 리소스를 추상화하거나 요약한다 | **CRD** |

핵심은 **누가 읽느냐**다. 그 앱만 읽으면 ConfigMap, 쿠버네티스가 읽고 반응해야 하면 CRD 다.

## 5. 선언적 API 의 조건

공식 문서는 CRD 가 잘 맞는 조건을 나열한다.

- 객체 수가 적고 각각 작다
- 애플리케이션이나 인프라의 **설정**을 담는다
- 자주 바뀌지 않는다
- 사람이 읽고 쓴다
- 주 연산이 생성·조회·수정·삭제다
- 객체 간 트랜잭션이 필요 없다 — **원하는 상태를 표현할 뿐 정확한 상태가 아니다**

마지막 항목이 판단 기준이 된다. 초당 수천 건이 오가거나, 여러 객체를 한 트랜잭션으로 묶어야 하거나, 실시간 정합성이 필요하면 CRD 는 맞지 않는다. 그건 데이터베이스가 할 일이다.

## 6. API Aggregation 과의 비교

새 API 를 추가하는 방법은 둘이다.

| | CRD | API Aggregation |
|---|---|---|
| 만드는 법 | YAML 등록 | **API 서버를 직접 구현** |
| 저장 | etcd (쿠버네티스가 알아서) | 내가 정함 |
| 버전 변환 | 제한적 | 마음대로 |
| 난이도 | 쉬움 | 어려움 |

공식 문서의 표현으로는 "**사용 편의성과 유연성 어느 쪽도 포기하지 않기 위해**" 두 가지를 다 제공한다. 대부분은 CRD 로 충분하고, metrics-server 처럼 데이터를 etcd 에 두면 안 되는 경우에 Aggregation 을 쓴다.

## 7. 관련 문서

- [apiVersion](/wiki/apiversion/) — CRD 가 새 그룹과 버전을 만든다
- [Admission Webhook](/wiki/admission-webhook/) — CRD 객체를 검증·변형하는 확장 지점
- **Operator** — CRD + 컨트롤러 조합 *(예정)*

## 8. 출처

정의, ConfigMap 과의 선택 기준, 선언적 API 조건은 공식 문서 "Custom Resources" 에 근거한다.

> "A custom resource is an extension of the Kubernetes API that is not necessarily available in a default Kubernetes installation."

> "When you combine a custom resource with a custom controller, custom resources provide a true declarative API."

> "The objects are updated relatively infrequently. … The API represents a desired state, not an exact state."

- [Kubernetes — Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [Kubernetes — Extend the Kubernetes API with CustomResourceDefinitions](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/)
- [Kubernetes — API Aggregation](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/)
