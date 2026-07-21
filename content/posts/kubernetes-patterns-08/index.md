---
series: ["K8sPatterns"]
title: "K8sPatterns.08 Periodic Job"
date: 2026-07-07T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "devops", "batch", "cronjob"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.08 Periodic Job'
  relative: true
summary: "Batch Job 패턴에 시간 차원을 더한 CronJob — schedule, concurrencyPolicy, startingDeadlineSeconds까지."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-overview" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Overview</a></div>
  <div><a href="#2-problem" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Problem</a></div>
  <div><a href="#3-solution-cronjob" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Solution: CronJob</a></div>
  <div><a href="#4-cronjob-전용-필드" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. CronJob 전용 필드</a></div>
  <div><a href="#5-실전-예제-매일-새벽-db-백업" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. 실전 예제: 매일 새벽 DB 백업</a></div>
  <div><a href="#6-실패-처리-누가-뭘-담당하나" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. 실패 처리: 누가 뭘 담당하나</a></div>
  <div><a href="#7-job-vs-cronjob-선택-기준" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. Job vs CronJob 선택 기준</a></div>
  <div><a href="#8-discussion" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">8. Discussion</a></div>
</div>
</div>
{{< /rawhtml >}}

## 1. Overview

```
Periodic Job 패턴의 위치
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job      → 딱 한 번, 끝날 때까지 확실히 실행
CronJob  → Job을 정해진 시간마다 반복 실행     ← 이번 챕터!
```

Periodic Job 패턴은 **Batch Job 패턴을 확장**한 것이다. 시간이라는 차원을 추가해, 특정 시각 또는 주기라는 **시간적 이벤트(temporal event)** 에 의해 작업 실행이 트리거된다.

한 줄 요약:

> **Job = "이 작업을 실행해"**
> **CronJob = "이 작업을 언제언제 실행해"**

---

## 2. Problem

### 실시간이 대세지만 스케줄링은 여전히 필요하다

요즘 개발 트렌드는 REST API(HTTP), Kafka/RabbitMQ(경량 메시징) 같은 **실시간·이벤트 기반** 통신이 주류다. 그러나 그 트렌드와 무관하게, **정해진 시간에 자동으로 반복 실행**되는 작업의 필요성은 사라지지 않는다.

전형적인 예시들:

| 분류 | 예시 |
|---|---|
| 시스템 유지보수 | 매일 새벽 DB 백업, 오래된 로그 정리·아카이빙 |
| 비즈니스 로직 | 매주 뉴스레터 발송, 매달 정산 처리 |
| 시스템 연동 | 파일 전송을 통한 B2B 연동, DB 폴링을 통한 애플리케이션 연동 |

### 기존 방식들과 각각의 문제점

**1. Cron / 전용 스케줄링 소프트웨어**

리눅스에 원래 있던 `cron`은 **그 서버 한 대에 종속**된다. 서버가 죽으면 스케줄도 끝이다(단일 장애점). 전문 스케줄링 소프트웨어는 단순한 용도에 비해 **비용이 과하다**.

**2. 앱 안에 스케줄러 직접 구현 (Quartz, Spring Batch 등)**

그래서 개발자들이 스케줄링 + 비즈니스 로직을 직접 구현하기 시작했다. 하지만 스케줄러가 앱 안에 있으니 **앱 전체를 고가용성으로** 만들어야 한다. 여러 인스턴스를 띄우면 동시에 여러 곳에서 실행될 수 있고, 그걸 막으려면 **리더 선출** 같은 복잡한 분산 시스템 문제를 해결해야 한다.

```
결과: 하루에 파일 몇 개 복사하는 단순한 작업 하나 때문에
      여러 노드 + 분산 리더 선출 + Failover 로직이 필요해진다

→ 문제의 크기에 비해 해결책이 너무 과하다
```

어떻게 짜든 **"하나만 실행되게" + "죽어도 살아나게"** 를 동시에 만족시키기가 너무 힘들다. 이것이 Kubernetes CronJob이 등장한 배경이다.

---

## 3. Solution: CronJob

### CronJob은 Job 위에 시간 스케줄만 얹은 것

```
Pod → Job → CronJob
(실행단위) (완료보장) (시간스케줄)
```

CronJob은 Kubernetes가 기본으로 제공하는 리소스로, 별도 설치 없이 그냥 쓴다. Cron이라는 이름은 리눅스 crontab에서 따왔고, **표현식 문법(`* * * * *`)도 그대로 빌려썼다.** 실제 동작은 완전히 다르다 — 클러스터 위에서 동작한다.

```
리눅스 Cron      = 개인 알람시계 (서버 한 대)
Kubernetes CronJob = 알람시계 + 대신 실행해주는 팀 전체 (클러스터)
```

CronJob 인스턴스는 Unix crontab 한 줄과 같다고 볼 수 있다. 이를 Kubernetes 리소스로 만들어, 시간 관리는 플랫폼이 담당하고 개발자는 **"뭘 실행할지"만** 구현하면 된다.

### Example 8-1. CronJob 명세

```yaml
apiVersion: batch/v1   # CronJob도 Job과 마찬가지로 batch API 그룹 소속
kind: CronJob
metadata:
  name: random-generator
spec:
  schedule: "*/3 * * * *"       # 3분마다 실행 (분 시 일 월 요일 순서의 Cron 표현식)
  jobTemplate:                  # 이 아래는 통째로 "일반 Job의 spec"과 동일한 템플릿
    spec:
      template:                 # Job의 template과 마찬가지로 Pod spec을 감싸는 한 겹
        spec:
          containers:
          - image: k8spatterns/random-generator:1.0
            name: random-generator
            command: [ "java", "-cp", "/", "RandomRunner", "/numbers.txt", "10000" ]
            # 이 컨테이너가 exit code 0으로 끝나야 해당 회차 Job이 Completed 처리됨
          restartPolicy: OnFailure   # Pod 레벨 정책 — Job(및 CronJob)은 Always 불가
```

구조를 한눈에 보면:

```
CronJob
 ├── schedule: "*/3 * * * *"   ← 언제 실행?
 └── jobTemplate               ← 뭘 실행?
      └── Job
           └── Pod
                └── Container (실제 작업)
```

`jobTemplate` 안은 일반 Job spec과 동일하다. 즉 CronJob은 **실행 시간마다 Job을 하나씩 새로 생성하는 공장**이다.

```
CronJob (하나)
  ├── Job (3시 실행)
  ├── Job (6시 실행)
  ├── Job (9시 실행)
  └── Job (12시 실행)
```

### 노드는 직접 골라야 하나?

**지가 알아서 찾는다.** Control Plane 안의 스케줄러가 실행 시간이 되면 "어느 노드가 여유있나" 자동으로 골라서 Pod를 띄워준다.

```
CronJob → "새벽 2시 됐다"
    ↓
Control Plane 스케줄러 → "Node 2가 여유있네"
    ↓
Node 2에서 자동 실행
```

직접 고르고 싶다면 조건을 걸 수 있다:

```yaml
nodeSelector:
  disktype: ssd    # SSD 달린 노드에서만 실행
```

기본은 자동, 필요하면 조건 걸어서 제한하는 방식이다.

### 서버가 죽어도 실행되나?

된다. Kubernetes는 여러 노드로 이루어진 클러스터이기 때문이다.

```
[Control Plane] ← 두뇌 (스케줄링 담당)
    ├── Node 1  ← 죽음
    ├── Node 2  ← 여기서 자동 실행
    └── Node 3
```

CronJob 실행 시간이 되면 Control Plane이 명령한다. Node 1이 죽어있으면 Node 2에서 실행한다. 클러스터가 살아있는 한 실행은 보장된다. 기존 Cron이 단일 장애점이었던 문제를 플랫폼 차원에서 해결한다.

---

## 4. CronJob 전용 필드

Job spec 외에, CronJob은 시간 관련 추가 필드들을 가진다.

### `.spec.schedule`

```yaml
schedule: "0 * * * *"   # 매 시간 정각마다
schedule: "*/3 * * * *"  # 3분마다
schedule: "0 2 * * *"   # 매일 새벽 2시
```

crontab 표현식을 그대로 사용한다.

### `.spec.startingDeadlineSeconds`

예정된 시간에 실행되지 못했을 때, **몇 초 안에는 늦게라도 실행할 것인가**를 지정한다.

```
오전 9시 실행 예정, startingDeadlineSeconds: 60 설정

시나리오 A: 리소스 부족으로 9시에 못 뜸
  → 9시 01분까지는 실행 시도 ✅

시나리오 B: 9시 01분도 넘겨버림
  → 이번 회차 스킵 ❌
```

어떤 작업은 **늦게 실행하면 의미가 없다.** 오전 9시 주가 데이터 수집이 10시에 실행되면 이미 낡은 데이터다. 이럴 때 차라리 이번 회차를 건너뛰는 게 낫다.

### `.spec.concurrencyPolicy`

이전 Job이 아직 실행 중인데 다음 실행 시간이 됐을 때 어떻게 할 것인지 지정한다.

```
상황: 3분마다 실행되는 CronJob인데 작업이 5분 걸린다면?
```

| 옵션 | 동작 |
|---|---|
| `Allow` (기본값) | 이전 Job 실행 중이어도 새 Job 시작 → 동시에 쌓일 수 있음 |
| `Forbid` | 이전 Job이 끝날 때까지 다음 실행 스킵 |
| `Replace` | 이전 Job 강제 종료 후 새 Job 시작 |

```
Allow:
  3분: Job A 시작
  6분: Job A 실행중 → Job B도 시작 (동시 실행)
  9분: Job A,B 실행중 → Job C도 시작 → 계속 쌓임 ⚠️

Forbid:
  3분: Job A 시작
  6분: Job A 실행중 → Job B 스킵
  9분: Job A 실행중 → Job C 스킵 → 안전하게 순서 보장

Replace:
  3분: Job A 시작
  6분: Job A 강제종료 → Job B 시작
  9분: Job B 강제종료 → Job C 시작 → 항상 최신 Job만 실행
```

언제 뭘 쓰냐:

| 정책 | 상황 |
|---|---|
| `Allow` | 작업이 독립적이고 겹쳐도 상관없을 때 |
| `Forbid` | DB 백업처럼 겹치면 안 될 때 |
| `Replace` | 항상 최신 데이터로만 작업해야 할 때 |

주의할 점: 동시성 정책은 **같은 CronJob 안에서만** 적용된다. 서로 다른 CronJob끼리는 무조건 동시 실행이 허용된다.

### `.spec.suspend`

CronJob을 **일시 정지**한다.

```yaml
spec:
  suspend: true   # 이후 실행 예약 중단
```

`true`로 설정하면 이후 실행이 예약되지 않는다. 이미 실행 중인 Job에는 **영향 없다**. 점검이나 임시 중단이 필요할 때 유용하다.

### `.spec.successfulJobsHistoryLimit` / `.spec.failedJobsHistoryLimit`

시간마다 Job이 하나씩 생성되므로 방치하면 계속 쌓인다. 성공/실패한 Job 기록을 **몇 개나 보관**할지 지정한다.

```yaml
successfulJobsHistoryLimit: 3   # 성공한 Job 3개만 보관
failedJobsHistoryLimit: 3       # 실패한 Job 3개만 보관
```

감사(auditing) 목적으로 기록은 남기되, 자원 낭비를 막기 위해 개수를 제한한다.

### 전체 필드 정리

| 필드 | 역할 |
|---|---|
| `schedule` | 언제 실행할지 (Cron 표현식) |
| `startingDeadlineSeconds` | 늦으면 얼마까지 허용할지 |
| `concurrencyPolicy` | 동시 실행을 어떻게 처리할지 |
| `suspend` | 일시 정지 |
| `successfulJobsHistoryLimit` | 성공 기록 보관 수 |
| `failedJobsHistoryLimit` | 실패 기록 보관 수 |

---

## 5. 실전 예제: 매일 새벽 DB 백업

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"           # 매일 새벽 2시 (트래픽 적은 시간)
  concurrencyPolicy: Forbid       # 이전 백업이 안 끝났으면 이번 회차는 스킵 (겹치면 데이터 꼬일 수 있음)
  successfulJobsHistoryLimit: 3   # 성공 기록 3개까지만 남기고 이후는 자동 정리
  failedJobsHistoryLimit: 3       # 실패 기록도 3개까지만 (원인 추적용으로만 보관)
  jobTemplate:                    # 실행될 때마다 여기 정의대로 Job이 새로 생성됨
    spec:
      template:
        spec:
          containers:
          - name: db-backup
            image: postgres:14   # pg_dump 클라이언트가 포함된 이미지 (DB 서버와 별개)
            command:
            - /bin/sh
            - -c
            - |
              # 파일명에 날짜를 박아 매일 다른 파일로 저장 (덮어쓰기 방지)
              pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > /backup/backup-$(date +%Y%m%d).sql
            env:
            - name: DB_HOST
              value: "postgres-service"   # 같은 클러스터 내 Service 이름으로 DNS 접근
            - name: DB_USER
              value: "admin"
            - name: DB_NAME
              value: "mydb"
            - name: PGPASSWORD              # pg_dump가 참조하는 표준 환경변수명 (임의로 못 바꿈)
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: password      # 비밀번호를 평문(value)이 아닌 Secret 참조로 주입
            volumeMounts:
            - name: backup-storage
              mountPath: /backup    # 위 pg_dump 출력 경로와 반드시 일치해야 함
          restartPolicy: OnFailure   # 백업 실패 시 컨테이너만 재시작 (Pod는 유지)
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc  # 컨테이너/Pod가 사라져도 백업 파일은 PV에 남음
```

실제로는 백업 파일을 S3 같은 외부 스토리지로 올리는 명령어를 추가하는 게 일반적이다:

```sh
pg_dump ... > /tmp/backup.sql && aws s3 cp /tmp/backup.sql s3://my-bucket/
```

---

## 6. 실패 처리: 누가 뭘 담당하나

### DB 연결이 끊겼을 때

Kubernetes가 다 해주는 것처럼 보여도, **비즈니스 로직의 견고함은 개발자 책임**이다.

```bash
#!/bin/bash
MAX_RETRY=3
COUNT=0

until pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > /backup/backup.sql
do
  COUNT=$((COUNT+1))
  if [ $COUNT -eq $MAX_RETRY ]; then
    echo "백업 실패 - 재시도 횟수 초과"
    exit 1   # 0이 아닌 코드로 종료 → Job이 실패로 기록되고, restartPolicy에 따라 컨테이너 재시작
  fi
  echo "$COUNT 번째 실패, 10초 후 재시도"
  sleep 10   # DB 일시 장애(재기동, 네트워크 순단)를 감안한 대기
done
```

스크립트가 1차 방어선, Kubernetes가 2차 방어선이다:

| 역할 | 담당 |
|---|---|
| 연결 끊겼을 때 재시도 | 스크립트 (직접 구현) |
| 스크립트 자체가 죽으면 재시작 | Kubernetes (`restartPolicy: OnFailure`) |

### 반드시 고려해야 할 예외 상황들

CronJob 컨테이너를 구현할 때 아래 케이스들을 직접 처리해야 한다:

| 예외 상황 | 설명 |
|---|---|
| `duplicate runs` | 같은 작업이 중복 실행됨 |
| `no runs` | 예정된 실행이 아예 안 됨 |
| `parallel runs` | 동시에 여러 개 실행됨 |
| `cancellations` | 실행 도중 취소됨 |

---

## 7. Job vs CronJob 선택 기준

기준은 단 하나다:

> **반복 실행이 필요하냐 아니냐**

```
한 번 → Job
반복  → CronJob
```

| | Job | CronJob |
|---|---|---|
| 실행 방식 | 수동 트리거 또는 1회 | 시간 스케줄에 따라 자동 반복 |
| 적합한 경우 | DB 마이그레이션, 일괄 데이터 처리 | DB 백업, 리포트 발송, 로그 정리 |

---

## 8. Discussion

CronJob 자체는 단순하다. Job에 시간 스케줄을 얹은 것이다. 그런데 Pod, 컨테이너 리소스 격리, Automated Placement, Health Probe 같은 다른 Kubernetes 기능들과 조합하면 **강력한 Job 스케줄링 시스템**이 된다.

핵심은 **관심사의 분리**다:

```
예전: 앱 안에 스케줄러 직접 구현
  → 스케줄링 + 고가용성 + Failover + 리더 선출 모두 개발자 몫

현재: Kubernetes CronJob
  → 스케줄링, 고가용성, Failover = 플랫폼이 담당
  → 개발자는 비즈니스 로직만 집중
```

스케줄링이 **앱 밖에서, 플랫폼 차원에서** 처리되기 때문에 얻는 이점:

- **고가용성**: 노드가 죽어도 클러스터가 다른 노드에서 실행
- **리소스 효율**: 실행할 때만 Pod 생성, 끝나면 삭제
- **정책 기반 배치**: 어느 노드에서 실행할지 플랫폼이 결정

CronJob은 **시간적 차원이 필요한 작업에만** 쓰는 특수한 도구다. 범용은 아니지만, Kubernetes 기능들이 서로 위에 쌓이며 발전하는 방식을 잘 보여주는 좋은 예시이기도 하다:

```
Pod
 └── Job (완료 보장)
      └── CronJob (시간 스케줄)
```

> CronJob이 해결해주는 문제들이 원래 복잡했던 것이지, CronJob 자체가 복잡한 게 아니다.
> 그 복잡한 걸 단순하게 만들어준 게 핵심이다.