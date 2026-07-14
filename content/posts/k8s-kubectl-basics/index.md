---
title: 'Reading a Kubernetes Cluster: config, get, describe, logs'
date: 2026-07-14T09:00:00+09:00
tags: ['kubernetes', 'kubectl', 'devops']
cover:
  image: 'images/cover.jpg'
  alt: 'Reading a Kubernetes Cluster: config, get, describe, logs'
  relative: true
summary: 'kubectl commands look like a random pile of subcommands until you split them into verbs and nouns — walked through with a real pending pod from a live cluster.'
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-범위가-좁아지는-순서-config--get--describe" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. 범위가 좁아지는 순서: config → get → describe</a></div>
  <div><a href="#2-get-목록-조회" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. get: 목록 조회</a></div>
  <div><a href="#3-describe와-logs의-정보-출처" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. describe와 logs의 정보 출처</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-사례-10일째-pending-상태인-파드" style="color:var(--secondary,inherit);text-decoration:none;">3.1 사례: 10일째 Pending 상태인 파드</a></div>
  </div>
  <div><a href="#4-logs가-적용되는-범위" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. logs가 적용되는 범위</a></div>
  <div><a href="#5-명령어별-옵션과-예시" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. 명령어별 옵션과 예시</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#51-kubectl-config" style="color:var(--secondary,inherit);text-decoration:none;">5.1 kubectl config</a></div>
    <div><a href="#52-kubectl-get" style="color:var(--secondary,inherit);text-decoration:none;">5.2 kubectl get</a></div>
    <div><a href="#53-kubectl-describe" style="color:var(--secondary,inherit);text-decoration:none;">5.3 kubectl describe</a></div>
    <div><a href="#54-kubectl-logs" style="color:var(--secondary,inherit);text-decoration:none;">5.4 kubectl logs</a></div>
  </div>
  <div><a href="#6-로그의-보존-범위" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. 로그의 보존 범위</a></div>
  <div><a href="#7-정리" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. 정리</a></div>
</div>
</div>
{{< /rawhtml >}}

`kubectl`의 서브커맨드는 `get`, `describe`, `logs`, `config` 정도로 수가 적지만, 각각이 무엇을 반환하는지는 하나의 문장 구조로 봐야 명확해진다.

```
kubectl [동작] [대상] [이름]
         ↑       ↑      ↑
        get    pods   내파드이름
```

동작(verb)의 종류는 `get`, `describe`, `logs`, `exec`, `delete`, `apply` 정도로 제한적이다. 구분이 필요한 지점은 동작이 아니라 대상(명사) — `pod`, `node`, `namespace`, `configmap` — 그리고 동작마다 정보를 제공하는 주체가 다르다는 점이다.

## 1. 범위가 좁아지는 순서: config → get → describe

```
내 컴퓨터 (kubectl)
     │
     │  ← config: 어느 클러스터에 연결할지
     ↓
클러스터 A (dev)          클러스터 B (다른 계정)
     │
     │  ← get: 이 클러스터 안에 뭐가 있나 (목록)
     ↓
파드1, 파드2, 파드3 ...
     │
     │  ← describe: 이 중 파드1 하나를 자세히
     ↓
파드1의 상세 정보 + 이벤트
```

`kubectl`은 한 번에 하나의 클러스터에만 명령을 전달한다. kubeconfig에 클러스터를 여러 개 등록할 수는 있으나, 그중 하나만 `current-context`로 지정되며 모든 명령은 해당 클러스터로만 전달된다.

```bash
kubectl config current-context      # 현재 연결된 클러스터 확인
kubectl config get-contexts         # 등록된 클러스터 목록
kubectl config use-context <name>   # 전환
```

## 2. get: 목록 조회

`get` 뒤에 붙는 명사에 따라 반환되는 목록의 종류가 달라진다.

```bash
kubectl get pods          # 파드
kubectl get nodes         # 서버(노드)
kubectl get namespaces    # 네임스페이스
kubectl get configmap     # 환경설정 값
```

확인해야 할 핵심 컬럼은 두 가지다.

```bash
$ kubectl get pods -n default
NAME            READY   STATUS    RESTARTS   AGE
node-affinity   0/1     Pending   0          10d
```

- `READY 0/1` — 컨테이너가 준비되지 않은 상태
- `STATUS Pending` — 아직 스케줄되지 않은 상태

이 두 값에 따라 다음 진단 단계가 결정된다.

## 3. describe와 logs의 정보 출처

파드를 하나의 프로세스로 볼 때, 두 명령어가 답하는 질문은 서로 다르다.

- `describe` — 쿠버네티스 스케줄러/컨트롤러가 이 파드를 다루며 기록한 이벤트
- `logs` — 파드 내부 애플리케이션이 출력한 내용

| | describe | logs |
|---|---|---|
| 정보의 출처 | 쿠버네티스 시스템 | 애플리케이션 코드 |
| 사용 시점 | 파드가 뜨지 않을 때 (Pending) | 파드는 떴는데 동작이 이상할 때 |
| 확인 가능한 내용 | 스케줄링 실패, 이미지 풀 실패, OOM | DB 연결 실패, 500 에러, 예외 |

```
STATUS 확인
 ├─ Pending / ImagePullBackOff → describe 우선
 │    (컨테이너가 실행된 적 없어 logs는 비어있음)
 └─ Running인데 이상 / CrashLoopBackOff → logs 우선
      (원인이 불명확하면 describe로 재시작 이력 추가 확인)
```

### 3.1 사례: 10일째 Pending 상태인 파드

운영 중인 클러스터에 `node-affinity`라는 파드가 열흘째 `Pending` 상태로 남아 있었다.

```bash
$ kubectl logs node-affinity -n default
# 출력 없음
```

로그가 비어있는 이유는 이 파드가 어느 노드에도 배정되지 않아(`Node: <none>`) 컨테이너가 실행된 적이 없기 때문이다. 이 경우 `logs`는 정보를 제공하지 못한다.

```bash
$ kubectl describe pod node-affinity -n default
...
Events:
  Type     Reason            Age                   From                Message
  Warning  FailedScheduling  15m (x954 over 3d7h)  default-scheduler   0/2 nodes are available: 2 node(s) didn't match Pod's node affinity/selector.
```

원인은 `describe`의 `Events` 섹션에 나타난다. 파드가 요구하는 노드 조건을 만족하는 서버가 클러스터에 없어 스케줄링이 거부된 상태였다. Pending 상태에서는 `logs`보다 `describe`를 먼저 확인해야 한다는 원칙을 그대로 보여주는 사례다.

## 4. logs가 적용되는 범위

`logs`는 대상이 애플리케이션 파드인지 쿠버네티스 시스템 파드인지와 무관하게 동일하게 동작한다. coredns나 scheduler 역시 `kube-system` 네임스페이스에 배치된 파드이기 때문이다.

```bash
kubectl logs <애플리케이션파드> -n dev
kubectl logs coredns-869c9f5ffb-cd72b -n kube-system
```

네임스페이스 전체에서 발생한 이벤트를 파드 단위가 아니라 한번에 확인하려면 `get events`를 사용한다. `describe`의 Events가 파드 하나로 좁혀진 뷰라면, 이는 네임스페이스 전체에 대한 뷰다.

```bash
kubectl get events -n default --sort-by=.lastTimestamp
```

## 5. 명령어별 옵션과 예시

### 5.1 kubectl config

| 옵션 | 예시 | 설명 |
|---|---|---|
| `current-context` | `kubectl config current-context` | 현재 연결된 클러스터 이름 출력 |
| `get-contexts` | `kubectl config get-contexts` | 등록된 클러스터 전체 목록 (선택된 항목은 `*` 표시) |
| `use-context <이름>` | `kubectl config use-context prod-cluster` | 다른 클러스터로 전환 |
| `set-context --current --namespace=<이름>` | `kubectl config set-context --current --namespace=dev` | 기본 네임스페이스 지정 |
| `view` | `kubectl config view` | kubeconfig 전체 내용 출력 |

```bash
$ kubectl config current-context
do-sgp1-k8s-1-36-0-do-1-sgp1-1782274110070
```

### 5.2 kubectl get

| 옵션 | 예시 | 설명 |
|---|---|---|
| `-n <네임스페이스>` | `kubectl get pods -n dev` | 특정 네임스페이스만 조회 |
| `-A` | `kubectl get pods -A` | 모든 네임스페이스 통틀어 조회 |
| `-o wide` | `kubectl get pods -o wide` | IP, 배정된 노드 등 추가 컬럼 표시 |
| `-o yaml` | `kubectl get pod <이름> -o yaml` | 리소스 전체 정의를 yaml 원본으로 출력 |
| `-w` | `kubectl get pods -w` | 상태 변화를 실시간으로 스트리밍 |
| `-l <라벨>` | `kubectl get pods -l app=api` | 특정 라벨이 붙은 리소스만 필터링 |

```bash
$ kubectl get pods -n monitoring -o wide
NAME                      READY   STATUS    RESTARTS   AGE   IP             NODE
prometheus-grafana-...    3/3     Running   0          12d   10.108.0.142   pool-ah0zo0om2-3cpau7
```

기본 출력에는 없는 IP와 배정된 노드까지 `-o wide`로 확인할 수 있다.

### 5.3 kubectl describe

| 옵션 | 예시 | 설명 |
|---|---|---|
| `describe pod <이름>` | `kubectl describe pod api-server-abc -n dev` | 파드 상세 정보 + 이벤트 |
| `describe node <이름>` | `kubectl describe node pool-ah0zo0om2-3cpau7` | 노드 상태, 리소스 사용량, 이벤트 |
| `describe deployment <이름>` | `kubectl describe deployment api-server -n dev` | 배포 설정, replica 상태, 최근 이벤트 |
| `describe configmap <이름>` | `kubectl describe configmap app-config -n dev` | configmap 안의 키-값 내용 |

대상(명사)만 바뀔 뿐 형태는 동일하다. 파드, 노드, 디플로이먼트, 컨피그맵 등 어떤 리소스든 상세 정보와 이벤트를 함께 확인할 때 사용한다.

```bash
$ kubectl describe pod node-affinity -n default
...
Events:
  Warning  FailedScheduling  ...  0/2 nodes are available: node affinity/selector 불일치
```

### 5.4 kubectl logs

| 옵션 | 예시 | 설명 |
|---|---|---|
| `-f` | `kubectl logs <pod> -f` | 실시간으로 로그를 계속 따라가며 출력 |
| `--tail=<N>` | `kubectl logs <pod> --tail=50` | 최근 N줄만 출력 |
| `--previous` | `kubectl logs <pod> --previous` | 재시작 직전, 종료된 컨테이너의 로그 |
| `--since=<시간>` | `kubectl logs <pod> --since=1h` | 지정한 시간 범위 이후 로그만 출력 |
| `-c <컨테이너명>` | `kubectl logs <pod> -c sidecar` | 파드 안에 컨테이너가 여러 개일 때 대상 지정 |

```bash
$ kubectl logs prometheus-grafana-59695b477f-lzdvf -n monitoring --tail=5
logger=plugins.update.checker t=... level=info msg="Update check succeeded" ...
```

`READY` 컬럼이 `2/2`, `3/3`처럼 1보다 큰 파드는 컨테이너가 여러 개 떠있는 상태이므로, `-c`로 대상을 지정하지 않으면 어떤 컨테이너의 로그인지 지정하라는 에러가 발생한다.

## 6. 로그의 보존 범위

`kubectl logs`는 로그를 저장하는 것이 아니라, 그 순간 컨테이너 런타임이 들고 있는 로그 파일을 그대로 읽어오는 것이다. 애플리케이션이 stdout/stderr로 출력한 내용을 노드 위의 컨테이너 런타임(containerd 등)이 캡처해 로컬 디스크에 파일로 남기고, `kubectl logs`는 API 서버를 거쳐 해당 노드에 그 파일을 요청하는 방식으로 동작한다.

```
애플리케이션의 표준출력(stdout)
      ↓
컨테이너 런타임이 캡처
      ↓
노드의 로컬 디스크에 파일로 저장
      ↓
kubectl logs 실행 시 → API 서버 → 해당 노드에 요청 → 파일 내용 반환
```

로그의 수명은 컨테이너·파드·노드의 수명과 같다. 즉 별도의 로그 수집기가 없는 경우 다음과 같은 제약이 따른다.

| 상황 | 결과 |
|---|---|
| 파드가 삭제됨 | 로그도 함께 삭제됨 |
| 노드가 사라짐(스케일 다운, 장애 교체) | 해당 노드의 로그 전부 소실 |
| 로그 로테이션(용량 제한) 발동 | 오래된 로그부터 자동 삭제 |
| 여러 노드에 파드가 흩어져 있음 | 노드별로 따로 조회해야 하며 한곳에서 검색 불가 |

이 때문에 실무에서는 Fluentd, Fluent Bit, Loki, ELK 같은 로그 수집기를 각 노드에 배치해 컨테이너가 살아있는 동안 stdout/stderr를 실시간으로 별도 저장소에 옮겨 영구 보존한다.

## 7. 정리

| 명령어 | 조회 범위 | 정보 출처 | 위험도 |
|---|---|---|---|
| `kubectl config` | 연결 대상 클러스터 | 접속 설정 | 🟢 안전 (단, 착오 시 이후 명령의 사고 원인이 됨) |
| `kubectl get <종류>` | 클러스터 내 목록 | 조회 | 🟢 안전 |
| `kubectl describe <종류> <이름>` | 개별 리소스 상세 + 이벤트 | 시스템 | 🟢 안전 |
| `kubectl logs <파드>` | 개별 파드 출력 | 애플리케이션 | 🟢 안전 |

네 명령어 모두 클러스터 상태를 변경하지 않는 조회 전용 명령어다. `get`, `describe`, `logs`는 아무리 잘못 실행해도 클러스터에 영향을 주지 않지만, `config`는 예외적으로 다뤄야 한다. 명령어 자체는 조회·전환에 그치지만, **어느 클러스터·네임스페이스에 연결되어 있는지 착각한 상태에서 `delete`, `apply`, `scale` 같은 상태 변경 명령을 실행하는 사고**로 이어질 수 있기 때문이다. 위험한 명령을 실행하기 전에는 `kubectl config current-context`로 연결 대상을 먼저 확인하는 습관이 필요하다.

네 명령어는 조회 범위를 좁혀가며 시스템 관점과 애플리케이션 관점을 오가는 하나의 축 위에 있다. 이 축을 기준으로 삼으면 `exec`, `port-forward`, `rollout` 등 상태를 변경하는 서브커맨드의 위치와 위험도도 함께 정리된다.
