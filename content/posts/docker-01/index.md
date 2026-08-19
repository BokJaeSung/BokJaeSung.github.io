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
  <div><a href="#6-commands" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">6. Commands</a></div>
  <div><a href="#7-q--a" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">7. Q &amp; A</a></div>
  <div><a href="#8-references" style="color:var(--primary,inherit);text-decoration:none;font-weight:600;">8. References</a></div>
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

- 호스트에서 수정 → 컨테이너에 즉시 보임 (핫 리로드에 최적)
- 컨테이너에서 수정 → 호스트에 즉시 보임
- **덮어쓰기**: 컨테이너 경로에 원래 파일이 있어도 호스트 내용으로 가려짐. 호스트 디렉터리가 비어 있으면 컨테이너도 빈 디렉터리를 보게 됨[^docs-bind-over]
- 호스트 경로 구조에 묶이므로 **이식성 낮음**
- 호스트 파일시스템을 컨테이너에 노출 → 보안 부담[^docs-bind-cons]
- 권한 문제 빈번: 호스트 경로는 있는데 컨테이너 실행 사용자(UID)가 읽기/쓰기 권한이 없는 경우[^docs-bind-cons]
- **SELinux 환경(RHEL·Fedora·Rocky)** 에서는 레이블 때문에 Permission denied가 난다. `:z`(여러 컨테이너 공유) 또는 `:Z`(단독 사용) 옵션으로 재레이블링해야 한다[^docs-bind-selinux]
- **파일 감시(inotify) 주의**: Docker Desktop(Mac·WSL2)에서는 호스트의 파일 변경 이벤트가 컨테이너로 전달되지 않는 경우가 있다. 핫 리로드가 안 먹으면 폴링을 켠다 (`CHOKIDAR_USEPOLLING=true`, Vite는 `server.watch.usePolling`)[^vite-poll]

**용도**: 개발 중 소스 코드 동기화, 설정 파일 주입(`:ro`), 로그/결과물을 호스트로 꺼내기

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
첫 마운트 (볼륨이 비어 있을 때):
  Container /app/data (이미지 기본 파일) ──복사──► Volume
                                                  │
  이후부터는 Volume 내용이 /app/data 에 보임 ◄───────┘
```

- 볼륨이 비어 있으면 **컨테이너 쪽 기존 내용을 볼륨으로 복사**해 준다. 예를 들어 `nginx` 이미지의 `/usr/share/nginx/html` 에 빈 볼륨을 걸면 이미지에 들어 있던 `index.html` 이 볼륨으로 복사된다[^docs-vol-over][^nerlich-init]
  - 단, **DB 이미지의 초기화는 이것과 다른 메커니즘**이다. `postgres` 이미지의 데이터 디렉터리는 이미지 안에서 비어 있어 복사할 것이 없고, 실제로는 entrypoint가 데이터 디렉터리가 비었는지 보고 `initdb` 를 돌리는 것이다[^pg-init]
- 컨테이너를 지워도 유지. `docker volume rm` 으로 직접 삭제해야 함[^docs-vol-rm]
- 여러 컨테이너가 같은 볼륨 공유 가능
- 볼륨 드라이버로 NFS, 클라우드 스토리지 연결 가능[^docs-vol-driver]
- Mac/Windows에서는 Docker VM 내부에 저장되어 Bind Mount보다 I/O 빠름[^datacamp-perf]

**용도**: DB 데이터, 업로드 파일, 캐시 등 운영 환경의 영속 데이터

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

```
이미지 빌드 시:   npm install → /app/node_modules 생성 ✔

실행 시 Bind Mount:
  Host ./ (node_modules 없음 or 다른 OS용) ──► /app
                                               └── node_modules  ← 호스트 것으로 덮임 ✘
```

컨테이너에서 설치한 `node_modules`가 호스트의 (비어 있거나 호환 안 되는) 것으로 덮어써진다. 해결책은 **더 깊은 경로에 익명 볼륨을 하나 더 거는 것**.[^oneuptime-dev]

```yaml
services:
  app:
    volumes:
      - .:/app                 # Bind Mount — 소스 코드
      - /app/node_modules      # Anonymous Volume — 컨테이너 쪽 node_modules 유지
```

```
/app              ← Bind Mount (호스트)
└── node_modules  ← Anonymous Volume (더 구체적인 경로가 우선)
```

Docker는 더 구체적인(깊은) 경로의 마운트를 우선하므로 `/app/node_modules`는 호스트 영향을 받지 않는다.

**함정 — Compose는 재생성 시 익명 볼륨을 재사용한다**

`docker compose up` 으로 컨테이너를 다시 만들어도 Compose는 **이전 컨테이너의 익명 볼륨을 그대로 가져온다**. 즉 `package.json` 을 고치고 이미지를 새로 빌드해도 예전 `node_modules` 가 그대로 살아 있다. 의존성을 갱신하려면 익명 볼륨을 새로 만들어야 한다.[^compose-up-v]

```bash
docker compose up --build -V     # -V = --renew-anon-volumes
```

---

## 6. Commands

```bash
# 볼륨 관리
docker volume ls                     # 목록
docker volume inspect my-data        # 실제 호스트 경로(Mountpoint) 등 확인
docker volume rm my-data             # 삭제
docker volume prune                  # 미사용 '익명' 볼륨만 (Docker 23.0+ 기본값)
docker volume prune -a               # named 포함, 미사용 전부

# 볼륨 내용 들여다보기 (앱 컨테이너 없이)
docker run --rm -v my-data:/d alpine ls -la /d
docker run -it --rm -v my-data:/d alpine sh

# 볼륨 백업 / 복원 (tar로 호스트에 꺼내기)
docker run --rm -v my-data:/d -v $(pwd):/backup alpine \
  tar czf /backup/my-data.tgz -C /d .
docker run --rm -v my-data:/d -v $(pwd):/backup alpine \
  tar xzf /backup/my-data.tgz -C /d

# 컨테이너가 어떤 마운트를 쓰는지 확인
docker inspect <ctr> --format '{{json .Mounts}}' | jq
```

**직접 확인해 볼 실험**

```bash
# 1) 익명 볼륨 + --rm  → 종료 후 volume ls 에 남지 않음
docker run --rm -v /data alpine sh -c "echo hi > /data/a"
docker volume ls

# 2) 익명 볼륨, --rm 없이 → rm 해도 볼륨이 남아 있음
docker run --name t -v /data alpine sh -c "echo hi > /data/a"
docker rm t
docker volume ls          # 해시 이름 볼륨 잔류 확인

# 3) Named Volume 초기 복사 확인
docker run --rm -v nginx-html:/usr/share/nginx/html nginx:alpine ls /usr/share/nginx/html
#  → index.html 등 이미지 기본 파일이 볼륨으로 복사돼 있음

# 4) Bind Mount 덮어쓰기 확인
mkdir empty && docker run --rm -v $(pwd)/empty:/usr/share/nginx/html nginx:alpine ls /usr/share/nginx/html
#  → 비어 있음 (이미지 파일이 가려짐)

# 뒷정리
docker volume rm nginx-html   # 실험 3: --rm 을 붙였어도 named 볼륨은 남는다
docker volume prune           # 실험 2가 남긴 익명 볼륨 정리
rmdir empty
```

---

## 7. Q & A

### 7.1 `-v`와 `--mount`는 뭐가 다른가?

기능은 같다. `-v`는 짧고 `호스트:컨테이너:옵션` 순서 규칙을 외워야 하며, 호스트 경로가 없으면 **자동 생성**해 버린다. `--mount`는 `type=bind,source=...,target=...` 으로 명시적이고, Bind Mount 시 소스 경로가 없으면 **에러**를 낸다. 실수 방지 측면에서 `--mount`가 안전하다.[^docs-bind-syntax]

### 7.2 Compose에서 `./data:/x` 와 `data:/x` 차이는?

앞에 `./`, `/`, `~`가 붙으면 Bind Mount, 이름만 있으면 Named Volume이다.[^devto] Named Volume은 최상위 `volumes:` 키에 선언해야 하며, 실제 볼륨 이름은 `{프로젝트명}_{볼륨명}` 으로 만들어진다.[^docs-compose] 단 `name:` 을 직접 지정하거나 `external: true` 로 기존 볼륨을 참조하면 프로젝트명 접두어가 붙지 않는다.[^compose-vol-name]

### 7.3 Named Volume은 이미 데이터가 있어도 복사하나?

아니다. **볼륨이 비어 있을 때만** 첫 마운트 시 복사한다.[^docs-vol-over][^nerlich-init] 이미 데이터가 있는 볼륨을 새 이미지 버전에 마운트하면 이미지의 새 기본 파일은 반영되지 않는다.

혼동하기 쉬운데, **DB 초기화 스크립트가 두 번째 실행부터 안 도는 것은 이 복사 규칙 때문이 아니다.** `postgres` 이미지는 "데이터 디렉터리가 비어 있을 때만" `/docker-entrypoint-initdb.d` 를 실행한다 — 원문: *"scripts in `/docker-entrypoint-initdb.d` are only run if you start the container with a data directory that is empty"*. 볼륨 복사가 아니라 **entrypoint의 판단**이다.[^pg-init]

### 7.4 볼륨 데이터는 어디에 실제로 있나?

Linux는 `docker volume inspect` 의 `Mountpoint`(보통 `/var/lib/docker/volumes/<name>/_data`). Mac/Windows Docker Desktop은 Linux VM 안에 있어서 호스트에서 직접 경로로 접근할 수 없다. 내용을 보려면 유틸리티 컨테이너에 마운트해서 본다.

### 7.5 운영 환경에서 Bind Mount를 쓰면 안 되나?

금지는 아니다. 호스트가 직접 읽고 써야 하는 파일(설정 주입, 로그 수집, 결과물 export)에는 의도적으로 쓴다. 다만 DB 같은 장기 데이터는 호스트 경로 의존·권한 문제·백업 설계 때문에 Named Volume이 기본값이다.[^datacamp-faq]

---

## 마치며

마운트 시 "덮느냐, 복사해 오느냐"와 삭제 시 "남느냐, 같이 지워지느냐" 두 축만 잡으면 세 방식이 구분된다.

---

## 8. References

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
