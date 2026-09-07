---
title: "apiVersion"
summary: "쿠버네티스 매니페스트 첫 줄에 오는 필드. 그룹과 버전 두 조각으로 이루어진다."
categories: ["쿠버네티스", "API"]
tags: ["kubernetes", "api", "manifest"]
---

## 1. 개요

**apiVersion**은 쿠버네티스 매니페스트의 첫 줄에 오는 필드로, 이 리소스가 어느 **API 그룹**에 속하며 어느 **버전**의 스키마를 따르는지를 선언한다. API 서버는 이 값을 보고 요청을 어느 핸들러로 넘길지, 어떤 필드를 허용할지 결정한다.

```yaml
apiVersion: apps/v1
kind: Deployment
```

## 2. 구조

```
apps/v1
└┬─┘ └┬
 │    └── 버전 — 얼마나 안정적인가
 └─────── 그룹 — 어느 묶음 소속인가
```

슬래시가 없으면 **코어 그룹**이다. 그룹명이 없는 게 아니라 생략된 것으로, 쿠버네티스 초기부터 있던 리소스들이 그룹 체계가 도입되기 전에 자리를 잡았다.

| 형태 | 예 | 해당 리소스 |
|---|---|---|
| 코어 (그룹 생략) | `v1` | Pod, Service, ConfigMap, Secret, Namespace, ServiceAccount |
| 그룹 + 버전 | `apps/v1` | Deployment, StatefulSet, DaemonSet |
| | `batch/v1` | Job, CronJob |
| | `networking.k8s.io/v1` | NetworkPolicy, Ingress |
| | `rbac.authorization.k8s.io/v1` | Role, RoleBinding |

## 3. 버전

### 3.1. 안정도 단계

| 버전 | 뜻 | 실무 |
|---|---|---|
| `v1alpha1` | 실험 단계. 예고 없이 바뀌거나 사라지며 기본 비활성인 경우가 많다 | 프로덕션 금지 |
| `v1beta1` | 대체로 동작하지만 필드가 바뀔 수 있다 | 조건부. 업그레이드 시 확인 |
| `v1`, `v2` | 안정. 하위 호환이 보장된다 | 안심하고 사용 |

숫자가 올라가는 것(`v1` → `v2`)은 안정 버전 안에서의 세대 교체다. `autoscaling/v2`가 그 예로, HPA가 여러 지표를 다루게 되면서 스펙이 크게 바뀌었다.

### 3.2. 명명 규칙의 예외

**버전이 `v1`이어도 내장이 아닐 수 있다.**

```yaml
apiVersion: serving.knative.dev/v1     # Knative — 설치해야 함
kind: Service
```

`v1`은 *그 프로젝트 안에서* 안정적이라는 뜻이지 쿠버네티스에 내장이라는 뜻이 아니다.

**도메인이 `k8s.io`여도 내장이 아닐 수 있다.**

```yaml
apiVersion: autoscaling.k8s.io/v1      # VPA — 쿠버네티스 프로젝트 산하지만 별도 설치
kind: VerticalPodAutoscaler
```

`k8s.io`는 "쿠버네티스 프로젝트가 관리한다"는 표시일 뿐이다. 반대로 HPA(`autoscaling/v2`)는 도메인이 없는데도 내장이다.

## 4. 확인 명령

첫 줄만으로는 내장 여부를 확정할 수 없다. 클러스터에 직접 묻는 것이 정확하다.

```bash
kubectl api-resources                      # 이 클러스터가 아는 리소스 전부
kubectl api-resources --api-group=apps     # 그룹으로 좁혀서
kubectl api-versions | grep autoscaling    # 살아 있는 버전 확인

kubectl explain hpa                        # 이 리소스가 무엇인지, 어느 버전인지
kubectl explain hpa.spec.metrics           # 필드 단위로
```

목록에 없으면 설치되지 않은 것이다. `error: the server doesn't have a resource type "..."` 가 그 신호다.

## 5. 그룹당 단일 등록

하나의 API 그룹에는 하나의 구현만 등록할 수 있다. 확장 API를 등록하는 `APIService` 리소스의 이름이 `<버전>.<그룹>` 형태로 고정되기 때문이다.

```bash
kubectl get apiservice | grep metrics
# v1beta1.metrics.k8s.io           kube-system/metrics-server            True
# v1beta1.custom.metrics.k8s.io    monitoring/prometheus-adapter         True
# v1beta1.external.metrics.k8s.io  keda/keda-operator-metrics-apiserver  True
```

`metrics.k8s.io`는 metrics-server가, `external.metrics.k8s.io`는 KEDA 같은 어댑터가 차지한다. 같은 자리에 다른 어댑터를 등록하면 에러가 아니라 **덮어써지고**, 먼저 있던 연결이 조용히 끊긴다. 한 클러스터에서 외부 지표 어댑터를 둘 이상 쓰기 어려운 이유다.

## 6. 사례 목록

이 블로그 K8sPatterns 시리즈에 실제로 등장한 것들.

| apiVersion | kind | 내장 | 비고 |
|---|---|---|---|
| `v1` | Pod, Service, ConfigMap, Secret | ✅ | 코어 그룹 |
| `apps/v1` | Deployment, StatefulSet | ✅ | |
| `batch/v1` | Job, CronJob | ✅ | |
| `autoscaling/v2` | HorizontalPodAutoscaler | ✅ | 도메인 없는 내장 그룹 |
| `networking.k8s.io/v1` | NetworkPolicy | ✅ | 규격만 내장, 집행은 CNI 몫 |
| `rbac.authorization.k8s.io/v1` | Role, RoleBinding | ✅ | |
| `apiregistration.k8s.io/v1` | APIService | ✅ | 확장 등록용 |
| `scheduling.k8s.io/v1` | PriorityClass | ✅ | |
| `policy/v1` | PodDisruptionBudget | ✅ | |
| `autoscaling.k8s.io/v1` | VerticalPodAutoscaler | ❌ | `k8s.io` 인데 설치 대상 |
| `serving.knative.dev/v1` | Service | ❌ | `v1` 인데 서드파티 |
| `keda.sh/v1alpha1` | ScaledObject | ❌ | |
| `bitnami.com/v1alpha1` | SealedSecret | ❌ | |
| `external-secrets.io/v1beta1` | ExternalSecret, SecretStore | ❌ | |
| `security.istio.io/v1beta1` | AuthorizationPolicy | ❌ | Istio |
| `secrets-store.csi.x-k8s.io/v1` | SecretProviderClass | ❌ | `x-` 는 SIG 산하 확장 |

`serving.knative.dev/v1`의 `kind: Service`는 코어 `v1`의 Service와 **이름만 같은 다른 리소스**다. 그룹이 다르면 남남이라 같은 이름을 써도 충돌하지 않는다. 그룹이 존재하는 이유가 이것이다.

## 7. 관련 문서

- **APIService** — 확장 API를 등록하는 리소스 *(예정)*
- **CRD** — 새 리소스 종류를 정의하는 방법 *(예정)*

## 8. 출처

- [Kubernetes API Overview](https://kubernetes.io/docs/reference/using-api/)
- [API Versioning](https://kubernetes.io/docs/reference/using-api/#api-versioning)
- [API Groups](https://kubernetes.io/docs/reference/using-api/#api-groups)
