---
title: 'Operating a Kubernetes Cluster: rollout, delete, apply'
date: 2026-07-14T09:00:00+09:00
tags: ['kubernetes', 'kubectl', 'devops']
cover:
  image: 'images/cover.jpg'
  alt: 'Operating a Kubernetes Cluster: rollout, delete, apply'
  relative: true
summary: 'kubectl commands that change cluster state — rollout, delete, apply — walked through with a real failed deployment and rollback on a live cluster.'
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-reading과-operating의-경계" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Reading과 Operating의 경계</a></div>
  <div><a href="#2-rollout-배포-이력-관리" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. rollout: 배포 이력 관리</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#21-rollout-status-배포-진행-확인" style="color:var(--secondary,inherit);text-decoration:none;">2.1 rollout status: 배포 진행 확인</a></div>
    <div><a href="#22-rollout-undo-직전-버전으로-롤백" style="color:var(--secondary,inherit);text-decoration:none;">2.2 rollout undo: 직전 버전으로 롤백</a></div>
  </div>
  <div><a href="#3-delete-삭제와-자동-재생성" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. delete: 삭제와 자동 재생성</a></div>
  <div><a href="#4-apply-대부분-ci-cd가-대신하는-명령어" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. apply: 대부분 CI/CD가 대신하는 명령어</a></div>
  <div><a href="#5-명령어별-옵션과-예시" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. 명령어별 옵션과 예시</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-kubectl-rollout" style="color:var(--secondary,inherit);text-decoration:none;">5.1 kubectl rollout</a></div>
    <div><a href="#52-kubectl-delete" style="color:var(--secondary,inherit);text-decoration:none;">5.2 kubectl delete</a></div>
    <div><a href="#53-kubectl-apply" style="color:var(--secondary,inherit);text-decoration:none;">5.3 kubectl apply</a></div>
  </div>
  <div><a href="#6-실사용-빈도와-위험도" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. 실사용 빈도와 위험도</a></div>
  <div><a href="#7-정리" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. 정리</a></div>
</div>
</div>
{{< /rawhtml >}}

`get`, `describe`, `logs`, `config`는 클러스터를 조회할 뿐 상태를 바꾸지 않는다. 지금부터 다루는 `rollout`, `delete`, `apply`는 클러스터의 실제 상태를 바꾸는 명령어다. 조회 명령어는 잘못 실행해도 영향이 없지만, 이 명령어들은 실행 전에 무엇이 바뀌는지 파악하는 과정이 필요하다.

## 1. Reading과 Operating의 경계

| | Reading (조회) | Operating (상태 변경) |
|---|---|---|
| 명령어 | `get`, `describe`, `logs`, `config` | `rollout`, `delete`, `apply` |
| 클러스터에 미치는 영향 | 없음 | 있음 |
| 잘못 실행했을 때 | 정보를 잘못 봄 | 서비스 중단, 데이터 손실로 이어질 수 있음 |
| 실행 전 확인할 것 | 없음 | 대상 네임스페이스, 영향받는 리소스 범위 |

`rollout status`처럼 이름은 Operating 그룹에 있어도 실제로는 조회만 하는 하위 명령어도 있다. 이 구분은 명령어 이름이 아니라 **클러스터 상태를 실제로 바꾸는가**를 기준으로 한다.

## 2. rollout: 배포 이력 관리

`rollout`은 단일 명령어가 아니라 배포 이력을 다루는 하위 명령어의 모음이다.

```bash
kubectl rollout status deployment/<name> -n dev    # 배포 진행 확인 (조회)
kubectl rollout undo deployment/<name> -n dev      # 직전 버전으로 롤백
kubectl rollout restart deployment/<name> -n dev   # 코드 변경 없이 재시작
```

### 2.1 rollout status: 배포 진행 확인

배포가 완료됐는지, 아니면 아직 진행 중인지 확인한다. 상태를 바꾸지 않는 조회 명령어다.

```bash
$ kubectl rollout status deployment/hello-api -n blog-demo
Waiting for deployment "hello-api" rollout to finish: 0 of 2 updated replicas are available...
deployment "hello-api" successfully rolled out
```

### 2.2 rollout undo: 직전 버전으로 롤백

새 버전을 배포했는데 문제가 발생했을 때, 원인을 조사하기 전에 우선 직전 버전으로 되돌리는 명령어다.

#### 사례: 잘못된 이미지 태그로 배포가 멈춘 상황

정상적으로 떠 있는 디플로이먼트에 존재하지 않는 이미지 태그로 업데이트를 시도했다.

```bash
$ kubectl set image deployment/hello-api hello-api=nginxdemos/hello:this-tag-does-not-exist -n blog-demo
deployment.apps/hello-api image updated
```

몇 초 뒤 파드 상태를 보면, 기존 파드 2개는 그대로 살아있고 새로 생성된 파드만 이미지를 받아오지 못해 멈춰 있다.

```bash
$ kubectl get pods -n blog-demo
NAME                         READY   STATUS         RESTARTS   AGE
hello-api-6845657cbd-g4bq8   1/1     Running        0          22s
hello-api-6845657cbd-hqlfh   1/1     Running        0          22s
hello-api-6cbf7bc8d7-5g4qf   0/1     ErrImagePull   0          8s
```

`describe`로 원인을 확인하면 존재하지 않는 태그 때문에 이미지를 받아오지 못하고 있다는 것이 바로 나온다.

```bash
$ kubectl describe pod hello-api-6cbf7bc8d7-5g4qf -n blog-demo
...
Events:
  Type     Reason   Age  From     Message
  Warning  Failed   15s  kubelet  Error: ImagePullBackOff
```

Deployment는 새 파드가 정상적으로 뜰 때까지 기존 파드를 내리지 않기 때문에, 이 시점에서 서비스 자체는 중단되지 않는다. 다만 배포는 이 상태로 멈춰 더 진행되지 않는다. 원인을 붙잡고 있기보다 먼저 롤백한다.

```bash
$ kubectl rollout history deployment/hello-api -n blog-demo
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

$ kubectl rollout undo deployment/hello-api -n blog-demo
deployment.apps/hello-api rolled back

$ kubectl rollout status deployment/hello-api -n blog-demo
deployment "hello-api" successfully rolled out
```

`rollout history`로 이전 리비전이 존재하는지 먼저 확인한 뒤, `rollout undo`로 직전 버전으로 되돌리고, `rollout status`로 정상 복구를 확인하는 순서다.

## 3. delete: 삭제와 자동 재생성

`delete`가 위험한지 여부는 **무엇을 지우는가**에 따라 갈린다.

| 삭제 대상 | 결과 |
|---|---|
| `delete pod` (Deployment 소속) | Deployment가 감지해 즉시 새 파드를 재생성 |
| `delete deployment` | 하위 파드까지 모두 사라지고, 재생성하려면 다시 배포해야 함 |

### 사례: 파드 하나를 지워도 서비스는 유지된다

```bash
$ kubectl get pods -n blog-demo
NAME                         READY   STATUS    RESTARTS   AGE
hello-api-6845657cbd-g4bq8   1/1     Running   0          82s
hello-api-6845657cbd-hqlfh   1/1     Running   0          82s

$ kubectl delete pod hello-api-6845657cbd-g4bq8 -n blog-demo
pod "hello-api-6845657cbd-g4bq8" deleted from blog-demo namespace

$ kubectl get pods -n blog-demo
NAME                         READY   STATUS    RESTARTS   AGE
hello-api-6845657cbd-h7bd5   1/1     Running   0          5s
hello-api-6845657cbd-hqlfh   1/1     Running   0          87s
```

삭제한 파드(`g4bq8`)는 사라지고, 5초 만에 이름이 다른 새 파드(`h7bd5`)가 생성됐다. Deployment가 replica 수 부족을 감지해 즉시 채워 넣은 결과다. 이 때문에 `delete pod`는 원인이 불명확한 문제 상황에서 파드를 재생성시켜 복구를 시도하는 용도로 비교적 자주 쓰인다.

반면 `kubectl delete deployment hello-api -n blog-demo`는 이 Deployment 자체를 지우는 것이라, 재생성해줄 대상이 사라져 서비스가 완전히 내려간다. 다시 띄우려면 `apply`로 처음부터 다시 배포해야 한다.

## 4. apply: 대부분 CI/CD가 대신하는 명령어

`apply`는 YAML에 정의한 상태를 클러스터에 적용하는 명령어다.

```bash
kubectl apply -f deployment.yaml
```

이미 존재하는 리소스에 적용하면 기존 설정을 덮어쓴다. 오래된 YAML 파일을 실수로 적용하면 최근 변경사항이 사라질 수 있고, 의도한 네임스페이스가 아닌 곳에 적용하면 엉뚱한 환경에 배포된다.

이 팀 구성(CI/CD로 자동 배포되는 단일 클러스터, dev/prod 네임스페이스 분리)에서는 `apply`를 개발자가 직접 실행할 일이 많지 않다. 대부분 CI/CD 파이프라인이 커밋을 감지해 자동으로 적용하고, 개발자는 그 결과를 `rollout status`나 `get pods`로 확인하는 쪽에 가깝다. 로컬에서 급하게 변경사항을 테스트할 때 정도가 직접 `apply`를 실행하는 경우다.

## 5. 명령어별 옵션과 예시

### 5.1 kubectl rollout

| 옵션 | 예시 | 설명 |
|---|---|---|
| `status` | `kubectl rollout status deployment/api -n dev` | 배포 진행 상태 확인 |
| `history` | `kubectl rollout history deployment/api -n dev` | 리비전(배포 이력) 목록 확인 |
| `undo` | `kubectl rollout undo deployment/api -n dev` | 직전 리비전으로 롤백 |
| `undo --to-revision=<N>` | `kubectl rollout undo deployment/api --to-revision=2 -n dev` | 특정 리비전으로 롤백 |
| `restart` | `kubectl rollout restart deployment/api -n dev` | 코드 변경 없이 파드를 순차 재시작 |

### 5.2 kubectl delete

| 옵션 | 예시 | 설명 |
|---|---|---|
| `delete pod <이름>` | `kubectl delete pod api-abc -n dev` | 파드 하나 삭제 (Deployment 소속이면 자동 재생성) |
| `delete deployment <이름>` | `kubectl delete deployment api -n dev` | 디플로이먼트 전체 삭제 (하위 파드도 모두 사라짐) |
| `--grace-period=<초>` | `kubectl delete pod api-abc --grace-period=0 --force -n dev` | 정상 종료를 기다리지 않고 즉시 삭제 |

### 5.3 kubectl apply

| 옵션 | 예시 | 설명 |
|---|---|---|
| `-f <파일>` | `kubectl apply -f deployment.yaml` | YAML 파일 내용을 클러스터에 적용 |
| `-f <디렉토리>` | `kubectl apply -f ./manifests/` | 디렉토리 내 모든 YAML 파일 적용 |
| `--dry-run=client` | `kubectl apply -f deployment.yaml --dry-run=client` | 실제로 적용하지 않고 결과만 미리 확인 |
| `-n <네임스페이스>` | `kubectl apply -f deployment.yaml -n dev` | 적용 대상 네임스페이스 지정 |

## 6. 실사용 빈도와 위험도

인프라를 직접 구축하지 않고 CI/CD가 배포를 대신 처리하는 팀 구성을 기준으로 한 빈도와 위험도다.

| 명령어 | 빈도 | 위험도 |
|---|---|---|
| `rollout status` | 자주 | 🟢 안전 (조회) |
| `rollout undo` | 가끔, 그러나 결정적 | 🟡 주의 |
| `delete pod` | 가끔 | 🟡 주의 |
| `apply` | 드묾 (대부분 CI/CD가 실행) | 🟡 주의 |
| `delete deployment` | 거의 없음 | 🔴 위험 |

`rollout status`는 배포 후 확인 습관으로 자리잡아야 할 만큼 자주 쓰이고, `rollout undo`는 실행 빈도 자체는 낮지만 장애 상황에서 이 명령어를 아는지 모르는지가 복구 시간을 크게 좌우한다. `delete deployment`처럼 되돌리기 어려운 명령어는 실행 전 대상 네임스페이스를 `kubectl config current-context`로 다시 확인하는 습관이 필요하다.

## 7. 정리

`rollout`, `delete`, `apply`는 모두 클러스터 상태를 바꾸지만 위험도는 서로 다르다. `rollout status`처럼 조회에 가까운 것부터, `delete pod`처럼 자동 복구가 뒤따르는 것, `delete deployment`처럼 되돌리기 어려운 것까지 폭이 넓다. 명령어 이름만으로 위험도를 판단하지 않고, **무엇을 대상으로 하며 되돌릴 방법이 있는가**를 먼저 확인하는 것이 이 그룹의 핵심 판단 기준이다.
