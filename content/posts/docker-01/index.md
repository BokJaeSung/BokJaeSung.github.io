---
title: "Docker.01 Bind Mount vs Volume (Named / Anonymous)"
date: 2026-08-19T09:00:00+09:00
tags: ["docker", "volume", "bind mount", "devops"]
cover:
  image: 'images/cover.jpg'
  alt: 'Docker.01 Bind Mount vs Volume (Named / Anonymous)'
  relative: true
summary: "How Docker persists data outside containers: bind mounts vs named and anonymous volumes, how each behaves on mount and removal, and the node_modules trick."
---

## 0. Contents

{{< rawhtml >}}
<div style="background:transparent;border:1.5px solid var(--primary,#888);border-radius:8px;padding:16px 20px;margin:1.2rem 0;font-family:inherit;box-shadow:0 2px 10px rgba(0,0,0,0.12);">
<div style="font-size:16px;line-height:2.1;font-family:inherit;">
  <div><a href="#1-why-we-need-them" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">1. Why We Need Them</a></div>
  <div><a href="#2-bind-mount" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">2. Bind Mount</a></div>
  <div><a href="#3-volume" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">3. Volume</a></div>
  <div style="padding-left:20px;font-size:15px;">
    <div><a href="#31-named-volume" style="color:var(--secondary,inherit);text-decoration:none;">3.1 Named Volume</a></div>
    <div><a href="#32-anonymous-volume" style="color:var(--secondary,inherit);text-decoration:none;">3.2 Anonymous Volume</a></div>
  </div>
  <div><a href="#4-comparison" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">4. Comparison</a></div>
  <div><a href="#5-node_modules-trick" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">5. node_modules Trick</a></div>
  <div><a href="#6-q--a" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. Q &amp; A</a></div>
  <div><a href="#7-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. References</a></div>
</div>
</div>
{{< /rawhtml >}}

컨테이너 밖에 데이터를 보관하는 세 가지 방법 — Bind Mount, Named Volume, Anonymous Volume — 의 동작 차이와 용도를 정리한다.

---

## 1. Why We Need Them

컨테이너의 쓰기 레이어는 컨테이너와 운명을 같이한다. 컨테이너를 지우면 그 안에 쓴 파일도 사라진다.[^docs-vol-life]

```
┌──────────── Container ─────────────┐
│  writable layer   ← gone on rm     │
│  ────────────────────────────────  │
│  image layers (read-only)          │
└────────────────────────────────────┘
```

그래서 컨테이너 바깥에 저장 공간을 두고 **마운트**해서 쓴다. 마운트 타입은 셋이지만(bind / volume / tmpfs), tmpfs는 호스트 메모리에만 올라가고 컨테이너가 멈추면 사라지므로[^docs-tmpfs] **영속화 수단은 사실상 둘**이다.

```
                 ┌──────────────┐
   Host path ────┤  Bind Mount  ├──► /container/path
                 └──────────────┘

                 ┌──────────────┐
   Docker area ──┤    Volume    ├──► /container/path
   (/var/lib/    │  ├ Named     │
    docker/      │  └ Anonymous │
    volumes/)    └──────────────┘
```

---

## 2. Bind Mount

호스트의 **특정 경로**(파일 또는 디렉터리)를 컨테이너 안에 그대로 연결한다. 경로는 사용자가 직접 지정한다.[^docs-bind-when]

```bash
# -v 문법
docker run -v /host/path:/container/path my-image

# --mount 문법 (더 명시적)
docker run --mount type=bind,source=/host/path,target=/container/path my-image
```

```yaml
# docker-compose.yml  —  ./ 또는 절대경로로 시작하면 Bind Mount
services:
  app:
    volumes:
      - ./src:/app/src
      - ./config/app.yaml:/app/config.yaml:ro   # 읽기 전용
```

**동작 특징**

```
Host: ./src ───────────────► Container: /app/src
       (양방향 즉시 반영)
```

- **양방향 즉시 반영** — 호스트에서 고치면 컨테이너에, 컨테이너에서 고치면 호스트에 바로 보인다
  - 복사가 아니다. **파일은 하나뿐이고 양쪽이 같은 실체를 볼 뿐**이다. 그래서 코드 한 줄 고칠 때마다 이미지를 다시 빌드할 필요가 없다

- **덮어쓰기(obscure)** — 컨테이너 경로에 원래 파일이 있어도 호스트 내용에 가려진다. 호스트 디렉터리가 비어 있으면 컨테이너도 빈 디렉터리를 보게 된다[^docs-bind-over]
  - **삭제가 아니라 "가려짐"이다.** 공식 문서도 *obscured* 라고 쓴다. 마운트를 떼면 원래 파일이 그대로 다시 보인다
  - 두 폴더 내용이 합쳐지는 것도 아니다. `/app` 이라는 **주소가 통째로 호스트 경로로 갈아끼워지는 것**에 가깝다. USB를 `/media/usb` 에 마운트하면 그 폴더에 뭐가 있었든 USB 내용만 보이는 것과 같은, 리눅스 마운트의 기본 동작이다
  - 영향 범위는 **마운트한 경로와 그 하위뿐**이다. `/app` 을 덮어도 `/usr/bin` 은 멀쩡하다
  - 이미지 안에 파일이 있는데 컨테이너에서 안 보인다면 대부분 이것이다 (5절 `node_modules` 문제가 정확히 이 현상)

- **이식성 낮음** — 호스트 경로 구조에 묶인다
  - `-v /Users/aaa/proj:/app` 은 내 컴퓨터에서만 돈다. 동료 맥은 `/Users/kim/...`, 윈도우는 `C:\Users\...`, 서버엔 아예 없는 경로다. Named Volume이 `my-data:/app` 하나로 어디서나 도는 것과 대비된다

- **보안 부담** — 호스트 파일시스템을 컨테이너에 노출한다[^docs-bind-cons]
  - 컨테이너는 격리된 상자인데 bind mount는 거기에 바깥으로 통하는 구멍을 뚫는 것이다. 컨테이너 안 프로세스가 그 구멍으로 호스트 파일을 읽고 쓴다. 극단적으로 `-v /:/host` 면 호스트 전체를 만질 수 있다. **필요한 경로만, 가능하면 `:ro`** 가 원칙

- **권한(UID) 문제** — 경로는 있는데 컨테이너 실행 사용자가 읽기/쓰기 권한이 없는 경우[^docs-bind-cons]
  - 리눅스는 파일 주인을 이름이 아니라 **숫자(UID)** 로 기억한다. 호스트 파일 주인이 UID 501인데 컨테이너 프로세스가 UID 1000이면 그냥 거부된다
  - 볼륨은 Docker가 권한을 맞춰 주지만, bind mount는 **호스트 파일의 원래 권한을 그대로 쓴다**. 컨테이너가 만든 파일이 호스트에서 `root` 소유로 남아 못 지우는 상황도 여기서 나온다

- **SELinux 환경(RHEL·Fedora·Rocky)** — 레이블 때문에 Permission denied가 난다. `:z`(여러 컨테이너 공유) 또는 `:Z`(단독 사용)로 재레이블링해야 한다[^docs-bind-selinux]
  - UID 문제와는 별개다. 파일마다 붙은 레이블이 안 맞으면 **권한이 맞아도 차단**된다. 우분투·맥에서는 만날 일이 없고, 회사 서버가 RHEL 계열이면 반드시 만난다

- **파일 감시(inotify) 주의** — Docker Desktop(Mac·WSL2)에서는 호스트의 파일 변경 이벤트가 컨테이너로 전달되지 않는 경우가 있다[^vite-poll]
  - 위의 "양방향 즉시 반영"과 모순처럼 보이지만 다른 얘기다. **파일 내용은 이미 동기화돼 있고, "바뀌었다"는 알림만 안 가는 것**이다
  - 증상: 저장해도 핫 리로드가 안 되는데, 브라우저를 수동 새로고침하면 바뀐 내용이 나온다
  - 해결은 알림을 포기하고 주기적으로 직접 확인(폴링)하게 만드는 것. 대가는 CPU 사용량이다

    ```bash
    CHOKIDAR_USEPOLLING=true    # webpack, CRA, Nuxt 등
    ```
    ```js
    server: { watch: { usePolling: true } }   // Vite
    ```

**용도**

| 용도 | 예시 | 왜 Bind Mount인가 |
|---|---|---|
| 소스 코드 동기화 | `./src:/app/src` | 고칠 때마다 재빌드하지 않으려고 |
| 설정 파일 주입 | `./nginx.conf:/etc/nginx/nginx.conf:ro` | 이미지는 그대로 두고 설정만 갈아끼우려고. `:ro` 로 컨테이너가 못 고치게 막는다 |
| 결과물 꺼내기 | `./output:/app/output` | 컨테이너가 만든 로그·리포트를 호스트에서 바로 열어보려고 |

공통점은 **호스트가 그 파일을 직접 봐야 하는 경우**라는 것. 그게 아니면 Named Volume이 낫다.

---

## 3. Volume

Docker가 직접 만들고 관리하는 저장 공간. Linux에서는 보통 `/var/lib/docker/volumes/` 아래에 있고, 사용자는 호스트 경로를 알 필요가 없다.[^docs-vol-manage]

```
/var/lib/docker/volumes/
├── my-data/_data/              ← Named Volume
└── 9f3a1c...e7b2/_data/        ← Anonymous Volume (랜덤 해시)
```

### 3.1 Named Volume

```bash
docker volume create my-data        # 생략 가능 — 없으면 자동 생성
docker run -v my-data:/app/data my-image
```

```yaml
services:
  db:
    image: postgres:16
    volumes:
      - db-data:/var/lib/postgresql/data   # ./ 없이 이름만 → Named Volume

volumes:
  db-data:                               # 최상위에 선언
```

**동작 특징**

```
[1회차]  볼륨이 비어 있음

   Container  /app/data                Volume  my-data
   ┌────────────────────┐              ┌────────────────────┐
   │ index.html         │ ── (1) ────► │ (empty)            │
   │ 50x.html           │              │                    │
   └────────────────────┘              └────────────────────┘

   (1) copy   : 볼륨이 비었으므로 컨테이너 쪽 내용을 볼륨으로 복사

   ┌────────────────────┐              ┌────────────────────┐
   │ index.html         │ ◄──── (2) ── │ index.html         │
   │ 50x.html           │              │ 50x.html           │
   └────────────────────┘              └────────────────────┘

   (2) mount  : 복사가 끝난 뒤 연결. 이제 /app/data 는 볼륨을 본다
                파일은 같아 보이지만 실체는 이미지가 아니라 볼륨


[2회차 이후]  볼륨에 내용이 있음

   Container  /app/data                Volume  my-data
   ┌────────────────────┐              ┌────────────────────┐
   │ index.html         │ ◄──── (2) ── │ index.html         │
   │ my-page.html       │              │ my-page.html       │  ← 1회차에 추가한 것
   └────────────────────┘              └────────────────────┘

   (1) copy   : 없음. 볼륨이 비어 있지 않으므로 건너뛴다
   (2) mount  : 볼륨 내용이 그대로 보인다
                → 이미지를 새 버전으로 올려도 볼륨의 옛 파일이 계속 보인다
```

- **비어 있으면 채워 준다** — 볼륨이 비어 있으면 컨테이너 쪽 기존 내용을 볼륨으로 복사해 준다. `nginx` 이미지의 `/usr/share/nginx/html` 에 빈 볼륨을 걸면 이미지에 들어 있던 `index.html` 이 볼륨으로 복사된다[^docs-vol-over][^nerlich-init]
  - 순서가 핵심이다. **복사를 먼저 하고 그 다음 연결**한다. 그래서 연결한 뒤에도 파일이 그대로 보인다. 빈 폴더를 bind mount하면 그냥 덮여서 텅 비는 것과 정반대다
  - 겉보기엔 아무 일도 없어 보이지만 **실체가 바뀐다**. 그 파일은 이제 이미지가 아니라 볼륨에 있고, 수정하면 컨테이너를 지웠다 새로 만들어도 남는다
  - 단, **DB 이미지의 초기화는 이것과 다른 메커니즘**이다. `postgres` 이미지의 데이터 디렉터리는 이미지 안에서 비어 있어 복사할 것이 없고, 실제로는 entrypoint가 데이터 디렉터리가 비었는지 보고 `initdb` 를 돌린다[^pg-init]
    - 판단 주체가 Docker가 아니라 **postgres 자신**이다. 그래서 볼륨을 지우면(`docker compose down -v`) 다음 실행 때 초기화 SQL이 다시 돈다 — 개발 중 스키마를 갈아엎을 때 쓰는 방법

- **컨테이너를 지워도 유지** — `docker volume rm` 으로 직접 삭제해야 한다[^docs-vol-rm]
  - 컨테이너와 볼륨은 **수명이 따로**다. 컨테이너는 언제든 버리고 새로 만드는 일회용이지만 데이터는 그러면 안 되므로, 이 분리가 볼륨을 쓰는 가장 큰 이유다
  - `postgres:15` 컨테이너를 지우고 `postgres:16` 으로 새로 만든 뒤 같은 볼륨을 연결하면, 데이터는 그대로 두고 버전만 올릴 수 있다
  - 뒤집으면 함정이기도 하다. 컨테이너를 다 지워도 볼륨은 남아 디스크를 먹는다. `docker volume ls` 로 가끔 확인해야 한다

- **여러 컨테이너가 같은 볼륨 공유 가능**
  - 경로가 아니라 **이름표로 부르기 때문**에 가능하다. 업로드를 받는 `web` 과 후처리하는 `worker` 가 같은 `uploads` 볼륨을 물면 파일이 바로 오간다
  - 다만 동시 쓰기 충돌은 Docker가 막아 주지 않는다. **DB 데이터 볼륨을 두 DB 컨테이너가 동시에 물면 데이터가 깨진다**

- **볼륨 드라이버로 NFS, 클라우드 스토리지 연결 가능**[^docs-vol-driver]
  - 볼륨의 실체를 호스트 디스크가 아닌 다른 것으로 바꿀 수 있다. 컨테이너는 여전히 `/app/data` 에 쓸 뿐, 아무것도 달라지지 않는다
  - 이것도 이름표 방식이라 가능한 일이다. "호스트의 이 경로"라고 못박는 Bind Mount로는 안 된다. 서버 여러 대가 같은 데이터를 봐야 할 때 쓴다

- **Mac/Windows에서는 Bind Mount보다 I/O 빠름**[^datacamp-perf]
  - Docker는 리눅스 기술이라 Mac·Windows에서는 리눅스 VM 안에서 돈다. Bind Mount는 파일을 읽을 때마다 **VM ↔ 호스트 파일시스템 경계를 넘으며 번역**해야 하지만, 볼륨은 VM 안에 있어 그 경계를 넘지 않는다
  - `node_modules` 처럼 파일이 수만 개인 폴더에서 차이가 크게 벌어진다. `node_modules` 에 볼륨을 거는 5절의 트릭이 **성능 면에서도 이득인 이유**다
  - 리눅스에는 VM이 없으므로 이 차이가 없다

**용도**

| 용도 | 왜 Volume인가 |
|---|---|
| DB 데이터 | 컨테이너 버전을 올려도 데이터는 남아야 한다 |
| 업로드 파일 | 사용자가 올린 것은 날리면 안 된다 |
| 캐시·빌드 산출물 | 날아가도 되지만, 남아 있으면 다음 실행이 빨라진다 |

공통점은 **호스트에서 직접 열어볼 일이 없다**는 것. 직접 봐야 하면 Bind Mount, 아니면 Volume — 이 기준 하나로 대부분 갈린다.

### 3.2 Anonymous Volume

컨테이너 경로만 적고 호스트 쪽 이름/경로를 생략한 볼륨. Docker가 랜덤 해시로 이름을 붙인다.[^docs-vol-anon]

```bash
docker run -v /app/data my-image
```

```
$ docker volume ls
DRIVER    VOLUME NAME
local     9f3a1c4e6b...e7b2     ← 누가 만든 건지 알기 어려움
```

**생성되는 경우**

- `-v /container/path` 처럼 컨테이너 경로만 지정
- Dockerfile에 `VOLUME /data` 가 선언돼 있는데 실행 시 아무 마운트도 안 걸어 준 경우[^docs-dockerfile]

**삭제 규칙** — 여기서 많이 헷갈린다[^docs-vol-rm][^nerlich-rm]

```
docker run --rm ...  → 컨테이너 종료 시 익명 볼륨도 함께 삭제
docker run ...       → 컨테이너 rm 해도 익명 볼륨은 남음 (고아 볼륨)
docker rm -v <ctr>   → 컨테이너와 익명 볼륨 함께 삭제
docker volume prune  → 미사용 '익명' 볼륨만 정리 (기본값)
docker volume prune -a → named 볼륨까지 포함해 미사용 전부 정리
```

> `docker volume prune` 은 API 1.42(Docker 23.0) 이후 **기본적으로 익명 볼륨만** 지운다. 안 쓰는 named 볼륨까지 지우려면 `--all` 이 필요하다.[^docs-vol-prune]

**용도**: 특정 디렉터리가 Bind Mount에 덮이지 않게 보호, 임시 캐시. 운영에서는 추적이 어려우므로 Named Volume 권장[^datacamp-faq]

---

## 4. Comparison

| 구분 | Bind Mount | Named Volume | Anonymous Volume |
|---|---|---|---|
| 문법 (`-v`) | `/host:/ctr`, `./x:/ctr` | `name:/ctr` | `/ctr` |
| 저장 위치 | 사용자가 지정한 호스트 경로 | Docker 관리 영역 | Docker 관리 영역 (랜덤명) |
| 마운트 시 컨테이너 기존 내용 | 호스트 내용으로 **덮음** | 볼륨이 비어 있으면 **복사해 옴** | 볼륨이 비어 있으면 **복사해 옴** |
| 컨테이너 삭제 시 | 호스트 파일 그대로 | 유지 (수동 삭제) | `--rm` / `rm -v` 면 삭제, 아니면 잔류 |
| 이식성 | 낮음 (호스트 경로 의존) | 높음 | 낮음 (이름 추적 어려움) |
| 여러 컨테이너 공유 | 가능 | 가능 (이름으로 참조) | 사실상 어려움 |
| 주 용도 | 개발 소스 동기화, 설정 주입 | DB·업로드 등 영속 데이터 | 덮어쓰기 방지, 임시 캐시 |

**선택 기준 한 줄**: 개발 중 코드는 Bind Mount, 그 외 데이터는 Named Volume. 익명 볼륨은 보호용으로만.[^oneuptime-sum]

---

## 5. node_modules Trick

Node 프로젝트에서 프로젝트 루트 전체를 Bind Mount하면 문제가 생긴다.

**배경 두 가지**

- `node_modules` 는 `npm install` 이 만들어 내는 의존성 폴더다. 파일이 수만 개라 Git에 올리지 않으므로(`.gitignore`) **호스트 프로젝트 폴더에 없는 것이 정상**이다. 게다가 일부 패키지는 설치 시점에 그 OS에 맞게 컴파일되므로, macOS에서 설치한 것을 리눅스 컨테이너에서 쓸 수 없다
- **이미지는 빌드 시점의 스냅샷**이다. Dockerfile의 `COPY . .` 는 연결이 아니라 복사라서, 이후 호스트에서 코드를 고쳐도 이미지 안의 사본은 그대로다. 그래서 개발 중에는 매번 `docker build` 하는 대신 Bind Mount로 호스트 원본을 직접 보게 한다 — 그 편의가 아래 문제를 같이 데려온다

```
[1] 이미지 빌드 (docker build)

    Image  /app
    ┌────────────────────┐
    │ package.json       │
    │ index.js           │
    │ node_modules/      │   ← npm install 로 설치됨 (리눅스용 바이너리)
    └────────────────────┘


[2] 실행:  -v .:/app     ← /app 이 통째로 호스트로 교체된다

    Host  ./                            Container  /app
    ┌────────────────────┐              ┌────────────────────┐
    │ package.json       │ ───────────► │ package.json       │
    │ index.js           │              │ index.js           │
    │ (no node_modules)  │              │ (no node_modules)  │   ← 가려짐
    └────────────────────┘              └────────────────────┘

    호스트에 node_modules 가 없거나(설치 안 함),
    있어도 macOS/Windows용이라 리눅스 컨테이너에서 못 쓰는 바이너리다.

    결과:  Error: Cannot find module 'express'
```

컨테이너에서 설치한 `node_modules`가 호스트의 (비어 있거나 호환 안 되는) 것으로 덮어써진다. 해결책은 **더 깊은 경로에 익명 볼륨을 하나 더 거는 것**.[^oneuptime-dev]

```yaml
services:
  app:
    volumes:
      - .:/app                 # Bind Mount — 소스 코드
      - /app/node_modules      # Anonymous Volume — 컨테이너 쪽 node_modules 유지
```

두 번째 줄은 **호스트와 연결하는 것이 아니다.** 콜론이 없어 호스트 쪽 경로가 아예 지정되지 않았으므로 Docker 관리 영역의 익명 볼륨이 붙는다. 목적 자체가 **그 경로만 호스트를 피하게 하는 것**이다.

```yaml
- ./node_modules:/app/node_modules   # ✘ 호스트와 연결 — 없거나 다른 OS용이라 문제 그대로
- /app/node_modules                  # ✔ 호스트가 아닌 볼륨에 연결
```

볼륨은 비어 있으면 컨테이너 쪽 내용을 복사해 오므로(3.1절), 이미지에 있던 **리눅스용** `node_modules` 가 볼륨으로 옮겨 담긴 뒤 유지된다.

```
[3] 해결:  /app/node_modules 자리에만 마운트를 하나 더 얹는다

    적용 순서 (경로가 얕은 것부터)

      1) /app                ← Bind Mount        : 호스트 ./ 로 교체
      2) /app/node_modules   ← Anonymous Volume  : 그 위에 한 칸 더 덮음

    결과

    Container  /app
    ┌───────────────────────────────┐
    │ package.json                  │   ← 호스트 (Bind Mount)
    │ index.js                      │   ← 호스트 (Bind Mount)
    │ node_modules/                 │   ← 볼륨. 이미지에 있던 것이 복사돼 유지
    │   ├ express/                  │
    │   └ ...                       │
    └───────────────────────────────┘

    소스는 호스트와 실시간 동기화되고,
    node_modules 만 컨테이너(리눅스)용 그대로 남는다.
```

**왜 `/app` 을 덮었는데 그 아래 `node_modules` 는 안 덮이나**

마운트는 폴더를 통째로 소유하는 것이 아니라 **경로 단위 규칙**으로 등록된다. 커널은 경로를 찾을 때 **가장 길게 일치하는 마운트 지점**을 쓴다.

```
등록된 마운트
  /app                → 호스트 폴더
  /app/node_modules   → 볼륨

/app/src/index.js          → /app 이 일치        → 호스트에서 찾음
/app/node_modules/express  → /app/node_modules 가
                             더 길게 일치         → 볼륨에서 찾음
```

`/app` 규칙이 무효화된 것이 아니라, **더 구체적인 경우에만 예외**가 생긴 것이다. Docker는 마운트를 걸기 전에 목적지 경로가 **짧은 것부터 정렬**하므로, compose에 순서를 거꾸로 써도 `/app` → `/app/node_modules` 순으로 처리된다.

Docker만의 기능이 아니라 리눅스 마운트의 기본 동작이다. 서버에서 `/` 아래에 `/home`, `/var` 를 각각 다른 디스크로 마운트하는 것과 같다.

```bash
mount /dev/sdb1 /media/usb          # USB 전체
mount /dev/sdc1 /media/usb/photos   # photos 자리만 다른 디스크
```

**직접 확인**

```bash
docker run --rm -v $(pwd):/app -v /app/test alpine sh -c \
  "mkdir -p /app/test && echo hi > /app/test/a.txt && echo hi > /app/b.txt"

ls b.txt      # → 있음.  /app 은 호스트에 연결돼 있으므로
ls test/      # → 없음.  /app/test 는 볼륨에 연결돼 있으므로
```

같은 컨테이너에서 쓴 파일인데 한쪽만 호스트에 남는다. 경로에 따라 저장되는 곳이 다르다는 증거다.

**함정 — Compose는 재생성 시 익명 볼륨을 재사용한다**

`docker compose up` 으로 컨테이너를 다시 만들어도 Compose는 **이전 컨테이너의 익명 볼륨을 그대로 가져온다**. 즉 `package.json` 을 고치고 이미지를 새로 빌드해도 예전 `node_modules` 가 그대로 살아 있다. 의존성을 갱신하려면 익명 볼륨을 새로 만들어야 한다.[^compose-up-v]

```bash
docker compose up --build -V     # -V = --renew-anon-volumes
```

---

## 6. Q & A

{{< rawhtml >}}
<details style="border:1px solid var(--primary,#888);border-radius:8px;padding:12px 16px;margin:1rem 0;">
<summary style="cursor:pointer;font-weight:600;color:var(--primary,inherit);">질문 5개 — 클릭해서 펼치기</summary>
{{< /rawhtml >}}

### 6.1 `-v`와 `--mount`는 뭐가 다른가?

기능은 같다. `-v`는 짧고 `호스트:컨테이너:옵션` 순서 규칙을 외워야 하며, 호스트 경로가 없으면 **자동 생성**해 버린다. `--mount`는 `type=bind,source=...,target=...` 으로 명시적이고, Bind Mount 시 소스 경로가 없으면 **에러**를 낸다. 실수 방지 측면에서 `--mount`가 안전하다.[^docs-bind-syntax]

### 6.2 Compose에서 `./data:/x` 와 `data:/x` 차이는?

앞에 `./`, `/`, `~`가 붙으면 Bind Mount, 이름만 있으면 Named Volume이다.[^devto] Named Volume은 최상위 `volumes:` 키에 선언해야 하며, 실제 볼륨 이름은 `{프로젝트명}_{볼륨명}` 으로 만들어진다.[^docs-compose] 단 `name:` 을 직접 지정하거나 `external: true` 로 기존 볼륨을 참조하면 프로젝트명 접두어가 붙지 않는다.[^compose-vol-name]

### 6.3 Named Volume은 이미 데이터가 있어도 복사하나?

아니다. **볼륨이 비어 있을 때만** 첫 마운트 시 복사한다.[^docs-vol-over][^nerlich-init] 이미 데이터가 있는 볼륨을 새 이미지 버전에 마운트하면 이미지의 새 기본 파일은 반영되지 않는다.

혼동하기 쉬운데, **DB 초기화 스크립트가 두 번째 실행부터 안 도는 것은 이 복사 규칙 때문이 아니다.** `postgres` 이미지는 "데이터 디렉터리가 비어 있을 때만" `/docker-entrypoint-initdb.d` 를 실행한다 — 원문: *"scripts in `/docker-entrypoint-initdb.d` are only run if you start the container with a data directory that is empty"*. 볼륨 복사가 아니라 **entrypoint의 판단**이다.[^pg-init]

### 6.4 볼륨 데이터는 어디에 실제로 있나?

Linux는 `docker volume inspect` 의 `Mountpoint`(보통 `/var/lib/docker/volumes/<name>/_data`). Mac/Windows Docker Desktop은 Linux VM 안에 있어서 호스트에서 직접 경로로 접근할 수 없다. 내용을 보려면 유틸리티 컨테이너에 마운트해서 본다.

### 6.5 운영 환경에서 Bind Mount를 쓰면 안 되나?

금지는 아니다. 호스트가 직접 읽고 써야 하는 파일(설정 주입, 로그 수집, 결과물 export)에는 의도적으로 쓴다. 다만 DB 같은 장기 데이터는 호스트 경로 의존·권한 문제·백업 설계 때문에 Named Volume이 기본값이다.[^datacamp-faq]

---

## 마치며

마운트 시 "덮느냐, 복사해 오느냐"와 삭제 시 "남느냐, 같이 지워지느냐" 두 축만 잡으면 세 방식이 구분된다.

{{< rawhtml >}}
</details>
{{< /rawhtml >}}

---

## 7. References

각주 번호에 마우스를 올리면 아래 내용이 그대로 뜬다. 각 항목은 **문서 → 섹션 → 내용 → 링크** 순으로 적었고, 링크는 그 섹션으로 바로 이동한다.

[^docs-vol-life]: <span class="fn-k">문서</span> Docker Docs — Volumes<br><span class="fn-k">섹션</span> A volume's lifecycle<br><span class="fn-k">내용</span> 컨테이너의 쓰기 레이어는 컨테이너와 수명을 같이한다. 그래서 영속 데이터는 볼륨에 둔다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/volumes/#a-volumes-lifecycle">https://docs.docker.com/engine/storage/volumes/#a-volumes-lifecycle</a>

[^docs-vol-over]: <span class="fn-k">문서</span> Docker Docs — Volumes<br><span class="fn-k">섹션</span> Mounting a volume over existing data<br><span class="fn-k">내용</span> 원문: "if you mount an <em>empty volume</em> ... these files or directories are propagated (copied) into the volume" — 빈 볼륨을 마운트하면 컨테이너 쪽 기존 내용이 볼륨으로 복사된다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/volumes/#mounting-a-volume-over-existing-data">https://docs.docker.com/engine/storage/volumes/#mounting-a-volume-over-existing-data</a>

[^docs-vol-anon]: <span class="fn-k">문서</span> Docker Docs — Volumes<br><span class="fn-k">섹션</span> Named and anonymous volumes<br><span class="fn-k">내용</span> 이름을 지정하지 않으면 Docker가 임의의 고유 이름(랜덤 해시)을 부여한다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/volumes/#named-and-anonymous-volumes">https://docs.docker.com/engine/storage/volumes/#named-and-anonymous-volumes</a>

[^docs-vol-rm]: <span class="fn-k">문서</span> Docker Docs — Volumes<br><span class="fn-k">섹션</span> Remove volumes / Remove anonymous volumes<br><span class="fn-k">내용</span> `docker volume rm`, `docker rm -v`, `docker volume prune` 의 삭제 규칙과 익명 볼륨 처리 방식.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/volumes/#remove-volumes">https://docs.docker.com/engine/storage/volumes/#remove-volumes</a>

[^docs-vol-driver]: <span class="fn-k">문서</span> Docker Docs — Volumes<br><span class="fn-k">섹션</span> Use a volume driver<br><span class="fn-k">내용</span> 볼륨 드라이버로 NFS·CIFS/Samba·클라우드 스토리지 등 원격 저장소를 볼륨으로 연결할 수 있다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/volumes/#use-a-volume-driver">https://docs.docker.com/engine/storage/volumes/#use-a-volume-driver</a>

[^docs-vol-manage]: <span class="fn-k">문서</span> Docker Docs — Volumes<br><span class="fn-k">섹션</span> Create and manage volumes<br><span class="fn-k">내용</span> `docker volume inspect` 출력의 `"Mountpoint": "/var/lib/docker/volumes/my-vol/_data"` — 볼륨 실체가 Docker 관리 영역에 있음을 보여준다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/volumes/#create-and-manage-volumes">https://docs.docker.com/engine/storage/volumes/#create-and-manage-volumes</a>

[^docs-bind-when]: <span class="fn-k">문서</span> Docker Docs — Bind mounts<br><span class="fn-k">섹션</span> When to use bind mounts<br><span class="fn-k">내용</span> 호스트의 특정 파일/디렉터리 경로를 사용자가 직접 지정해 컨테이너와 공유하는 방식.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/bind-mounts/#when-to-use-bind-mounts">https://docs.docker.com/engine/storage/bind-mounts/#when-to-use-bind-mounts</a>

[^docs-bind-over]: <span class="fn-k">문서</span> Docker Docs — Bind mounts<br><span class="fn-k">섹션</span> Bind-mounting over existing data<br><span class="fn-k">내용</span> 원문: "the pre-existing files are obscured by the mount" — 컨테이너에 원래 있던 파일은 마운트에 가려진다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/bind-mounts/#bind-mounting-over-existing-data">https://docs.docker.com/engine/storage/bind-mounts/#bind-mounting-over-existing-data</a>

[^docs-bind-cons]: <span class="fn-k">문서</span> Docker Docs — Bind mounts<br><span class="fn-k">섹션</span> Considerations and constraints<br><span class="fn-k">내용</span> 컨테이너 프로세스가 호스트 파일시스템을 변경할 수 있어 "can have security implications". 파일 소유권·권한(UID) 이슈도 이 섹션에서 다룬다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/bind-mounts/#considerations-and-constraints">https://docs.docker.com/engine/storage/bind-mounts/#considerations-and-constraints</a>

[^docs-bind-syntax]: <span class="fn-k">문서</span> Docker Docs — Bind mounts<br><span class="fn-k">섹션</span> Syntax<br><span class="fn-k">내용</span> `--volume`은 없는 호스트 디렉터리를 자동 생성하지만, `--mount`는 생성하지 않고 에러를 낸다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/bind-mounts/#syntax">https://docs.docker.com/engine/storage/bind-mounts/#syntax</a>

[^docs-dockerfile]: <span class="fn-k">문서</span> Docker Docs — Dockerfile reference<br><span class="fn-k">섹션</span> VOLUME<br><span class="fn-k">내용</span> Dockerfile에 `VOLUME`으로 선언된 경로에 실행 시 아무 마운트도 걸지 않으면 익명 볼륨이 생성된다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/reference/dockerfile/#volume">https://docs.docker.com/reference/dockerfile/#volume</a>

[^docs-compose]: <span class="fn-k">문서</span> Docker Docs — Compose file reference (services → volumes)<br><span class="fn-k">섹션</span> Short syntax<br><span class="fn-k">내용</span> 원문: "To avoid ambiguities with named volumes, relative paths should always begin with `.` or `..`" — 이름만 쓰면 최상위 `volumes:`의 named volume으로 해석된다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/reference/compose-file/services/#short-syntax-5">https://docs.docker.com/reference/compose-file/services/#short-syntax-5</a>

[^nerlich-init]: <span class="fn-k">문서</span> Luca Nerlich — Volumes and Bind Mounts<br><span class="fn-k">섹션</span> Volume initialisation behaviour<br><span class="fn-k">내용</span> 원문: "When Docker mounts a named volume into a container and the volume is empty, Docker copies the existing contents of the container's directory into the volume"<br><span class="fn-k">링크</span> <a href="https://lucanerlich.com/docker/beginners-guide/volumes-and-bind-mounts/">https://lucanerlich.com/docker/beginners-guide/volumes-and-bind-mounts/</a>

[^nerlich-rm]: <span class="fn-k">문서</span> Luca Nerlich — Volumes and Bind Mounts<br><span class="fn-k">섹션</span> Removing Volumes<br><span class="fn-k">내용</span> 익명 볼륨은 `docker rm`에 `-v`를 붙여야 컨테이너와 함께 제거된다.<br><span class="fn-k">링크</span> <a href="https://lucanerlich.com/docker/beginners-guide/volumes-and-bind-mounts/">https://lucanerlich.com/docker/beginners-guide/volumes-and-bind-mounts/</a>

[^datacamp-perf]: <span class="fn-k">문서</span> DataCamp — Docker Mount Types: Volumes, Bind Mounts &amp; tmpfs Guide<br><span class="fn-k">섹션</span> Docker Mount Performance and Security<br><span class="fn-k">내용</span> macOS/Windows에서는 Docker가 Linux VM 안에서 동작해 bind mount는 호스트↔VM 파일 동기화 오버헤드가 붙는다. 볼륨은 VM 내부에 있어 더 빠르다.<br><span class="fn-k">링크</span> <a href="https://www.datacamp.com/tutorial/docker-mount">https://www.datacamp.com/tutorial/docker-mount</a>

[^datacamp-faq]: <span class="fn-k">문서</span> DataCamp — Docker Mount Types<br><span class="fn-k">섹션</span> Docker Mount FAQs<br><span class="fn-k">내용</span> 원문: "always use named volumes instead of anonymous ones so you can track and manage them easily"<br><span class="fn-k">링크</span> <a href="https://www.datacamp.com/tutorial/docker-mount">https://www.datacamp.com/tutorial/docker-mount</a>

[^oneuptime-dev]: <span class="fn-k">문서</span> OneUptime — How to Choose Between Docker Bind Mounts and Named Volumes<br><span class="fn-k">섹션</span> Development Workflow Example<br><span class="fn-k">내용</span> 소스 코드는 bind mount로 걸고, `node_modules`에는 별도 볼륨을 덧대 호스트와 동기화되지 않게 하는 패턴.<br><span class="fn-k">링크</span> <a href="https://oneuptime.com/blog/post/2026-01-16-docker-bind-mounts-vs-volumes/view">https://oneuptime.com/blog/post/2026-01-16-docker-bind-mounts-vs-volumes/view</a>

[^oneuptime-sum]: <span class="fn-k">문서</span> OneUptime — How to Choose Between Docker Bind Mounts and Named Volumes<br><span class="fn-k">섹션</span> Summary<br><span class="fn-k">내용</span> 원문: "use bind mounts for code during development, named volumes for everything else"<br><span class="fn-k">링크</span> <a href="https://oneuptime.com/blog/post/2026-01-16-docker-bind-mounts-vs-volumes/view">https://oneuptime.com/blog/post/2026-01-16-docker-bind-mounts-vs-volumes/view</a>

[^devto]: <span class="fn-k">문서</span> kakisoft — Named Volumes vs Bind Mounts, Behavior Differences, and Key Pitfalls (DEV Community)<br><span class="fn-k">섹션</span> Named Volume / Bind Mount<br><span class="fn-k">내용</span> Named Volume은 "No `./` prefix", Bind Mount는 "Has a `./` prefix" 로 구분한다고 설명한다.<br><span class="fn-k">링크</span> <a href="https://dev.to/kakisoft/docker-host-container-file-sharing-named-volumes-vs-bind-mounts-behavior-differences-and-key-45o9">https://dev.to/kakisoft/docker-host-container-file-sharing-named-volumes-vs-bind-mounts-behavior-differences-and-key-45o9</a>
[^docs-vol-prune]: <span class="fn-k">문서</span> Docker Docs — docker volume prune<br><span class="fn-k">섹션</span> Description / Options<br><span class="fn-k">내용</span> 원문: "By default, it only removes anonymous volumes." `--all`(`-a`)은 "Remove all unused volumes, not just anonymous ones" 이며 API 1.42+(Docker 23.0~)에서 도입됐다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/reference/cli/docker/volume/prune/">https://docs.docker.com/reference/cli/docker/volume/prune/</a>

[^compose-up-v]: <span class="fn-k">문서</span> Docker Docs — docker compose up<br><span class="fn-k">섹션</span> Options — ``-V, --renew-anon-volumes``<br><span class="fn-k">내용</span> 원문: "Recreate anonymous volumes instead of retrieving data from the previous containers" — 즉 기본 동작은 이전 컨테이너의 익명 볼륨 데이터를 그대로 가져오는 것이다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/reference/cli/docker/compose/up/">https://docs.docker.com/reference/cli/docker/compose/up/</a>

[^pg-init]: <span class="fn-k">문서</span> Docker Official Image — postgres (docker-library/docs)<br><span class="fn-k">섹션</span> Initialization scripts<br><span class="fn-k">내용</span> 원문: "scripts in `/docker-entrypoint-initdb.d` are only run if you start the container with a data directory that is empty; any pre-existing database will be left untouched on container startup."<br><span class="fn-k">링크</span> <a href="https://github.com/docker-library/docs/blob/master/postgres/README.md">https://github.com/docker-library/docs/blob/master/postgres/README.md</a>

[^docs-tmpfs]: <span class="fn-k">문서</span> Docker Docs — tmpfs mounts<br><span class="fn-k">섹션</span> tmpfs mounts<br><span class="fn-k">내용</span> 원문: "a tmpfs mount is temporary, and only persisted in the host memory. When the container stops, the tmpfs mount is removed, and files written there won't be persisted."<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/tmpfs/">https://docs.docker.com/engine/storage/tmpfs/</a>

[^docs-bind-selinux]: <span class="fn-k">문서</span> Docker Docs — Bind mounts<br><span class="fn-k">섹션</span> Configure the SELinux label<br><span class="fn-k">내용</span> SELinux가 켜진 호스트에서 bind mount에 `:z`(공유 레이블) 또는 `:Z`(private 레이블)를 붙여 재레이블링하는 방법을 설명한다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/engine/storage/bind-mounts/#configure-the-selinux-label">https://docs.docker.com/engine/storage/bind-mounts/#configure-the-selinux-label</a>

[^vite-poll]: <span class="fn-k">문서</span> Vite — Server Options<br><span class="fn-k">섹션</span> server.watch<br><span class="fn-k">내용</span> WSL2/Docker 같은 가상 파일시스템에서는 파일 변경 감시가 동작하지 않을 수 있어 `{ usePolling: true }` 를 권한다. 다만 "usePolling leads to high CPU utilization" 이라는 단서가 붙는다.<br><span class="fn-k">링크</span> <a href="https://vite.dev/config/server-options">https://vite.dev/config/server-options</a>

[^compose-vol-name]: <span class="fn-k">문서</span> Docker Docs — Compose file reference (top-level volumes)<br><span class="fn-k">섹션</span> name / external<br><span class="fn-k">내용</span> 원문: "The name is used as is and is not scoped with the stack name." `external: true` 면 프로젝트명 접두어 없이 기존 볼륨을 그대로 찾는다.<br><span class="fn-k">링크</span> <a href="https://docs.docker.com/reference/compose-file/volumes/">https://docs.docker.com/reference/compose-file/volumes/</a>


{{< rawhtml >}}
<style>
.fn-k{
  display:inline-block; min-width:38px; margin-right:6px;
  font-size:11.5px; font-weight:700; letter-spacing:.02em;
  color:var(--primary,#888); opacity:.85;
}
.footnotes li{ line-height:1.9; }
.fn-tip{
  position:fixed; z-index:9999; max-width:min(460px, 90vw);
  padding:12px 15px; border-radius:8px; font-size:13.5px; line-height:1.75;
  background:var(--theme,#1e1e1e); color:var(--content,#ddd);
  border:1px solid var(--primary,#888); box-shadow:0 6px 24px rgba(0,0,0,.35);
  opacity:0; transform:translateY(4px); transition:opacity .12s ease, transform .12s ease;
  pointer-events:none; word-break:break-word;
}
.fn-tip.show{ opacity:1; transform:translateY(0); pointer-events:auto; }
.fn-tip a{ color:var(--primary,#6cf); text-decoration:underline; word-break:break-all; }
.fn-tip .fn-k{ min-width:36px; }
a.footnote-ref{ scroll-margin-top:80px; }
/* 각주가 연달아 붙을 때 구분자 삽입: 8,13 */
sup[id^="fnref"] + sup[id^="fnref"]::before{
  content:","; margin:0 1px; color:var(--secondary,#888); font-weight:400;
}
</style>
<script>
(function(){
  function init(){
    var refs = document.querySelectorAll('a.footnote-ref, sup[id^="fnref"] > a');
    if(!refs.length) return;
    var tip = document.createElement('div');
    tip.className = 'fn-tip';
    document.body.appendChild(tip);
    var hideTimer;

    function hide(){ hideTimer = setTimeout(function(){ tip.classList.remove('show'); }, 160); }
    function keep(){ clearTimeout(hideTimer); }

    tip.addEventListener('mouseenter', keep);
    tip.addEventListener('mouseleave', hide);

    refs.forEach(function(a){
      a.addEventListener('mouseenter', function(){
        var id = decodeURIComponent((a.getAttribute('href')||'').slice(1));
        var li = document.getElementById(id);
        if(!li) return;
        var clone = li.cloneNode(true);
        clone.querySelectorAll('.footnote-backref').forEach(function(b){ b.remove(); });
        keep();
        tip.innerHTML = clone.innerHTML;
        tip.classList.add('show');

        var pad = 12, r = a.getBoundingClientRect();
        var w = tip.offsetWidth, h = tip.offsetHeight;
        var x = r.left, y = r.bottom + 10;
        if(x + w + pad > window.innerWidth) x = window.innerWidth - w - pad;
        if(y + h + pad > window.innerHeight) y = r.top - h - 10;
        if(y < pad) y = pad;
        tip.style.left = Math.max(pad, x) + 'px';
        tip.style.top = y + 'px';
      });
      a.addEventListener('mouseleave', hide);
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
</script>
{{< /rawhtml >}}
