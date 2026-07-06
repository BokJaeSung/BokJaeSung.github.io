---
series: ["K8sPatterns"]
title: "K8sPatterns.07 Batch Job"
date: 2026-07-06T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "batch"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.07 Batch Job'
  relative: true
summary: "격리된 원자적 작업 단위를 안정적으로 실행하기 위한 Job 리소스 — completions, parallelism, Indexed Job까지."
---

## 1. Overview

```
Kubernetes의 Pod 실행 방식들
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

베어 Pod     → 노드 장애 시 복구 안 됨 (개발/테스트용)
ReplicaSet   → 계속 실행되어야 하는 서비스용 (웹서버 등)
DaemonSet    → 모든 노드에 하나씩 (모니터링, 로그 등)
Job          → 딱 한 번, 끝날 때까지 확실히 실행     ← 이번 챕터!
```

Batch Job 패턴은 **격리된 원자적 작업 단위**를 관리하기 위한 패턴이다. 분산 환경에서 완료될 때까지 단기 실행 Pod를 안정적으로 실행하는 **Job 리소스**를 기반으로 한다.

---

## 2. Problem

지금까지 살펴본 Pod 실행 방식들의 공통점은 모두 **장기 실행 프로세스**를 위한 것이라는 점이다.

```
ReplicaSet: 계속 살아있어야 함  (웹서버)
DaemonSet:  계속 살아있어야 함  (노드당 1개)
베어 Pod:   장애 시 복구 안 됨  (신뢰성 없음)
```

그런데 현실에는 이런 요구사항도 있다.

> "정해진 작업을 딱 한 번, 확실히 끝내고 종료하고 싶다."

예를 들어:

- 대용량 데이터 배치 처리
- 이미지/영상 파일 변환
- 월말 정산 작업

이런 작업은 **완료되면 끝나야 하고**, 실패하면 **재시도**되어야 한다. 기존 primitive로는 이 요구사항을 안정적으로 채울 수 없다.

---

## 3. Solution: Job

Kubernetes의 **Job**은 ReplicaSet과 비슷하게 하나 이상의 Pod를 생성하고 성공적으로 실행되도록 보장한다. 차이점은, 예상된 수의 Pod가 **성공적으로 종료되면 Job이 완료된 것으로 간주**되고 더 이상 Pod를 만들지 않는다는 점이다.

```
ReplicaSet vs Job
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ReplicaSet: Pod 종료 → 다시 새 Pod 생성 (무한 반복)
Job:        Pod 종료(성공) → 완료로 간주, 추가 생성 안 함
```

### Job Controller는 어디서 동작하나?

Job은 Pod가 아니다. **Control Plane의 Controller Manager 안에서 동작하는 컨트롤러**다.

```
[Control Plane]                    [워커 노드]
  Controller Manager
    └── Job Controller  ──────►    kubelet
         "Pod 5개 만들어!"              └── 실제로 Pod 실행

Job Controller = "명령 내리는 관리자"
kubelet        = "실제로 실행하는 현장 직원"
```

### Example 7-1. Job 명세

```yaml
apiVersion: batch/v1   # Job은 batch API 그룹 소속 (core v1이 아님)
kind: Job
metadata:
  name: random-generator
spec:
  completions: 5                  # 성공한 Pod가 5개가 될 때까지 Job은 미완료 상태
  parallelism: 2                  # 동시에 최대 2개까지만 Pod 실행 (나머지는 대기)
  ttlSecondsAfterFinished: 300    # Job/Pod가 Completed 된 뒤 300초 지나면 자동 정리(GC)
  template:                       # 여기부터는 일반 Pod spec과 동일한 템플릿
    metadata:
      name: random-generator
    spec:
      restartPolicy: OnFailure    # Job에서 허용되는 값은 OnFailure/Never뿐 (Always 불가)
      containers:
      - image: k8spatterns/random-generator:1.0
        name: random-generator
        command: [ "java", "RandomRunner", "/numbers.txt", "10000" ]
        # 이 컨테이너가 종료(exit)해야 Pod가 완료 처리됨 — 데몬처럼 무한 대기하면 안 됨
```

`template.spec.containers`에 정의된 명세는 **5개 Pod 모두 동일하게 복제**된다.

```
[템플릿] random-generator:1.0
    │
    ├──► Pod 1 (동일 명세)
    ├──► Pod 2 (동일 명세)
    ├──► Pod 3 (동일 명세)
    ├──► Pod 4 (동일 명세)
    └──► Pod 5 (동일 명세)
```

### 완료 판정 기준: Exit Code

Kubernetes는 컨테이너 내부 로직을 알지 못한다. 오직 **exit code**로만 성공/실패를 판단한다.

```
exit code 0   → 성공 (Completed)
exit code 1~  → 실패 (재시작 정책에 따라 처리)
```

여러 컨테이너가 한 Pod에 있다면, **메인 컨테이너의 exit code**가 완료 기준이 된다. 사이드카 컨테이너는 completions 카운트에 영향을 주지 않는다.

```
completions: 10 인 Job에 사이드카(로그 수집기)가 붙어 있다면

[Pod 1]
 ├── main 컨테이너    → 완료 ✅  (1/10)
 └── sidecar 컨테이너  → main과 함께 종료

...

[Pod 10]
 ├── main 컨테이너    → 완료 ✅  (10/10)
 └── sidecar 컨테이너  → main과 함께 종료
        │
        ▼
   Job 완료 (기준: main 컨테이너 10회 성공)
```

사이드카가 메인보다 오래 살아있으면 Pod 자체가 끝나지 않는 문제가 있었는데, Kubernetes 1.29부터는 `initContainers`에 `restartPolicy: Always`를 지정해 **네이티브 사이드카**로 선언할 수 있다. 이렇게 하면 메인 컨테이너가 완료될 때 사이드카도 함께 자동 종료된다.

### 완료된 Pod는 왜 바로 삭제하지 않을까?

```
완료 즉시 삭제한다면?
  → 로그 확인 불가, 디버깅 불가 😱

그래서:
  완료 → Completed 상태로 유지 (로그 확인 가능)
       → ttlSecondsAfterFinished 만큼 대기
       → 자동 삭제 (자원 낭비 방지)
```

`ttlSecondsAfterFinished`는 **"로그 볼 시간은 주고, 그 다음엔 치운다"**는 절충안이다.

### restartPolicy: OnFailure vs Never

Job에서는 `restartPolicy: Always`를 사용할 수 없다 — 성공한 Pod를 계속 재시작하면 Job이 영원히 끝나지 않기 때문이다.

```
OnFailure                          Never
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
같은 Pod를 재활용                   Pod를 버리고 새로 생성
실패 → 컨테이너만 재시작 (Pod 유지)   실패 → 새 Pod 생성 (실패 Pod는 기록으로 남음)
```

### Figure 7-1 해석: parallelism은 "슬롯" 개념

책의 Figure 7-1은 시간 순서가 아니라 **동시 실행 슬롯**을 나타낸 그림이다. `completions: 5`, `parallelism: 2`일 때의 실행 모습은 다음과 같다.

```
슬롯2 │ Pod✅  Pod✅        Pod🔄
슬롯1 │ Pod✅  Pod✅
      └───────────────────────────
        1,2    3,4     5      (완료 순번)
```

즉 "1, 2 완료"는 **첫 번째·두 번째로 성공한 Pod**라는 뜻이다. 2개씩 병렬로 돌다가, 남은 completions가 1개뿐인 마지막 순간에는 슬롯 하나만 사용된다.

```
1단계: 슬롯1, 슬롯2 동시 실행 → 2개 완료 (2/5)
2단계: 슬롯1, 슬롯2 동시 실행 → 4개 완료 (4/5)
3단계: 슬롯1만 실행 (남은 completions 1개뿐이므로) → 5개 완료 (5/5)
```

`parallelism`이 항상 그 숫자만큼 꽉 채워 실행되는 건 아니다 — 남은 completions 수, 리소스 쿼터, 스로틀링 등에 따라 실제 동시 실행 Pod 수는 더 적을 수 있다.

---

## 4. 왜 베어 Pod 대신 Job인가?

| | 베어 Pod | Job |
|---|---|---|
| 클러스터 재시작 생존 | ✗ | ✓ (etcd에 영구 기록) |
| 완료 후 기록 보존 | 일부만 (`OnFailure`일 때만) | ✓ |
| 여러 번 실행 (`completions`) | ✗ | ✓ |
| 병렬 실행 (`parallelism`) | ✗ | ✓ |
| 일시 중지/재개 (`suspend`) | ✗ | ✓ |
| 노드 장애 시 재배치 | ✗ (실패 상태로 방치) | ✓ (스케줄러가 다른 노드로 재배치) |

`suspend: true`로 설정하면 실행 중인 Pod가 모두 삭제되고, `suspend: false`로 되돌리면 재개된다.

---

## 5. Job의 종류

`.spec.completions`와 `.spec.parallelism` 두 값의 조합에 따라 Job의 종류가 나뉜다.

### Single Pod Job

두 값을 모두 생략하거나 기본값(1)으로 두면, Pod 1개만 실행하고 성공하면 즉시 완료된다.

### Fixed Completion Count Job

```
completions: 5, parallelism: 1
[Pod1] → [Pod2] → [Pod3] → [Pod4] → [Pod5] → 완료

completions: 5, parallelism: 2
[Pod1][Pod2] → [Pod3][Pod4] → [Pod5] → 완료
```

작업 개수를 **미리 알고 있고**, 작업 1개당 Pod 1개를 쓸 만큼 처리 비용이 클 때 적합하다.

### Indexed Job

```
completions: 5, completionMode: Indexed

Pod 0 → JOB_COMPLETION_INDEX=0 → 자기 몫만 처리
Pod 1 → JOB_COMPLETION_INDEX=1 → 자기 몫만 처리
Pod 2 → JOB_COMPLETION_INDEX=2 → 자기 몫만 처리
Pod 3 → JOB_COMPLETION_INDEX=3 → 자기 몫만 처리
Pod 4 → JOB_COMPLETION_INDEX=4 → 자기 몫만 처리
```

각 Pod가 `JOB_COMPLETION_INDEX` 환경변수(또는 `batch.kubernetes.io/job-completion-index` 어노테이션)로 자신의 인덱스를 받아, **외부 작업 큐 없이** 자기가 처리할 작업을 스스로 계산한다.

```
Pod끼리 통신/동기화 여부
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pod 0  Pod 1  Pod 2  Pod 3  Pod 4
 │      │      │      │      │
 ❌ 서로 통신 안 함
 ❌ 서로 상태 모름
 ✅ 각자 인덱스로 독립 계산 → 겹치지 않게 처음부터 설계됨
```

시험지 나눠주듯 "1~30번은 1조, 31~60번은 2조"처럼 **애초에 겹치지 않게 구간을 나눠주기 때문에** 조율이 필요 없다.

### Example 7-2. Indexed Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: file-split
spec:
  completionMode: Indexed          # 각 Pod에 0부터 시작하는 고유 인덱스 부여
  completions: 5                   # 인덱스는 0, 1, 2, 3, 4 (총 5개)
  parallelism: 5                   # 5개 전부 동시 실행 (인덱스별로 병렬 처리)
  template:
    spec:
      containers:
      - image: alpine
        name: split
        command:
        - "sh"
        - "-c"
        - |
          # JOB_COMPLETION_INDEX는 Kubernetes가 각 Pod에 자동 주입하는 환경변수
          start=$(expr $JOB_COMPLETION_INDEX \* 10000)      # 이 Pod가 처리할 시작 줄
          end=$(expr $JOB_COMPLETION_INDEX \* 10000 + 10000) # 이 Pod가 처리할 끝 줄(미포함)
          awk "NR>=$start && NR<$end" /logs/random.log \    # NR: awk의 현재 줄 번호 변수
          > /logs/random-$JOB_COMPLETION_INDEX.txt          # 결과를 인덱스별 파일로 저장
        volumeMounts:
        - mountPath: /logs
          name: log-volume    # 모든 Pod가 같은 볼륨을 공유해야 원본 파일에 접근 가능
      restartPolicy: OnFailure
```

50,000줄짜리 `random.log` 파일을 5개 Pod가 동시에 10,000줄씩 나눠서 처리한다.

```
[random.log 50,000줄]
        │
   ┌────┴────┬────┬────┬────┐
 Pod0      Pod1 Pod2 Pod3 Pod4   ← 5개 동시 실행
   │         │    │    │    │
   ▼         ▼    ▼    ▼    ▼
 random-0  -1   -2   -3   -4  .txt
```

`NR`은 awk 내부에서 현재 처리 중인 줄 번호를 나타내는 변수로, `NR>=start && NR<end` 조건으로 해당 구간만 잘라낸다.

---

## 6. Partitioning의 한계: 전체 작업자 수를 모른다

Work Queue Job은 외부 큐(Redis, RabbitMQ 등)가 이미 작업을 잘라주지만, Indexed Job은 **Pod 스스로** 작업을 나눠야 한다. 이때 각 Pod는 다음을 알아야 한다.

```
필요한 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 자기 인덱스        (JOB_COMPLETION_INDEX 로 제공됨)
❌ 전체 Pod 개수      (completions 값 — 2023년 기준 미지원!)
✅ 작업 전체 크기      (파일 크기 등, 별도로 알아야 함)
```

`JOB_COMPLETION_TOTAL` 같은 환경변수가 있으면 편하겠지만 아직 지원되지 않는다. 대신 두 가지 우회책이 있다.

### 방법 1: 하드코딩

```java
int totalPods = 5;  // 전체 Pod 개수를 소스 코드에 직접 하드코딩
                     // completions 값과 반드시 일치해야 하지만 강제할 방법이 없음
```

`completions`를 바꾸려면 **코드도 수정하고 이미지도 새로 빌드**해야 한다. 코드와 YAML이 강하게 결합된다.

### 방법 2: 환경변수로 주입

```yaml
spec:
  completions: 5           # 실제 Job의 완료 목표치
  template:
    spec:
      containers:
      - env:
        - name: JOB_COMPLETION_TOTAL
          value: "5"        # 위 completions 값을 사람이 손으로 그대로 복사해 넣음
                            # → 나중에 completions만 바꾸고 이 값을 깜빡하면 버그로 이어짐
```

이미지를 새로 빌드할 필요는 없지만, `completions`를 바꿀 때 **YAML 안 두 곳**(`completions`와 환경변수)을 모두 수정해야 하므로 실수 여지가 남는다.

| | 하드코딩 | 환경변수 주입 |
|---|---|---|
| 이미지 재빌드 필요 | ✅ | ❌ |
| 수정 지점 | 코드 + YAML | YAML 2곳 |
| 결합도 | 높음 | 중간 |

---

## 7. 작업 항목을 어떻게 Job/Pod에 매핑할까

Job은 작업 항목을 어떻게 나눌지 강제하지 않는다. 개발자가 아래 두 전략 중 선택해야 한다.

### 전략 1: 작업 항목 1개 = Job 1개

```
장점: 각 작업을 독립적으로 추적/재실행 가능
단점: Job 오브젝트 수 증가, 관리 오버헤드 큼
적합: 복잡하고 개별 추적이 중요한 작업 (금융 거래 등)
```

### 전략 2: 작업 항목 전체 = Job 1개

```
장점: Job 오브젝트 1개, 리소스 절약
단점: 개별 작업 추적은 앱 내부 배치 프레임워크가 담당해야 함
적합: 단순하고 대량인 작업 (로그 처리, 대량 메일 발송 등)
```

| | Job per 작업 | Job for 전체 |
|---|---|---|
| Job 수 | 많음 | 1개 |
| 개별 추적 | ✅ | ❌ |
| 관리 주체 | Kubernetes | 앱 내부 (Spring Batch, JBeret 등) |
| 적합한 경우 | 복잡/중요 | 단순/대량 |

---

## 8. Discussion

Job 프리미티브는 스케줄링의 **최소한의 기본기**만 제공한다. 복잡한 요구사항은 배치 프레임워크(Java 생태계의 Spring Batch, JBeret 등)와 조합해야 한다.

```
Job이 해주는 것            Job이 안 해주는 것
━━━━━━━━━━━━━━━━━━━━      ━━━━━━━━━━━━━━━━━━━━━━━━
✅ Pod 실행 보장            ❌ 작업 항목 세부 관리
✅ 완료 횟수 관리            ❌ 진행률 추적
✅ 병렬 실행                ❌ 작업 간 의존성 관리
✅ 실패 시 재시작
```

모든 서비스가 항상 실행될 필요는 없다.

```
항상 실행       → ReplicaSet / Deployment
모든 노드       → DaemonSet
필요할 때만     → Job              ← 이번 챕터
주기적으로      → CronJob (Job 기반)
```

Job으로 짧은 수명의 작업을 처리하면, ReplicaSet처럼 계속 떠 있는 추상화를 쓰는 것보다 **다른 워크로드를 위한 자원을 절약**할 수 있다. Job은 노드의 가용 용량, Pod 배치 정책, 컨테이너 의존성을 고려해 스케줄링된다.

> Job은 **"필요할 때만, 필요한 만큼"** 실행되는 워크로드를 위한 primitive다. 다양한 워크로드를 지원하는 것이 Kubernetes의 강점이다.