---
title: "Python TUI 앱에 mtime 캐시와 CLI 서브프로세스 연동 구현하기"
date: 2026-04-10T21:14:52+09:00
tags: ["python", "textual", "caching", "subprocess", "tui", "optimization"]
cover:
  image: 'images/cover.jpg'
  alt: 'Python TUI 앱에 mtime 캐시와 CLI 서브프로세스 연동 구현하기'
  relative: true
summary: ""
---

## 배경

Textual로 만든 TUI 앱에서 `~/.local/share/app/` 아래의 JSONL 파일들을 파싱해 목록으로 보여주는 기능이 있었다. 문제는 `r` (reload) 키를 누를 때마다, 그리고 포스트 생성 직전에도 같은 파일을 중복으로 읽고 있었다는 점이다. 파일이 수백 개를 넘어가면 체감할 수 있는 지연이 생겼고, 파싱 결과를 재사용할 방법이 필요했다.

---

## mtime 기반 인메모리 캐시

### 왜 mtime인가

내가 다루던 JSONL 파일은 **append-only** 구조다. 새 데이터가 추가될 때만 파일이 변경되므로, 파일의 수정 시간(`mtime`)이 바뀌지 않았다면 내용도 바뀌지 않았다는 보장이 생긴다. 덕분에 캐시 유효성 판단을 한 줄로 끝낼 수 있다.

```python
import pathlib
from dataclasses import dataclass
from typing import Optional

_session_cache: dict[pathlib.Path, tuple[float, Optional["Session"]]] = {}


def load_session(path: pathlib.Path, project_slug: str) -> Optional["Session"]:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None

    if path in _session_cache:
        cached_mtime, cached = _session_cache[path]
        if cached_mtime == mtime:
            return cached  # 파일 안 읽음, 메모리에서 즉시 반환

    result = _parse_session(path, project_slug)  # 실제 파싱
    _session_cache[path] = (mtime, result)
    return result
```

`stat()` syscall은 파일 내용을 읽는 것보다 훨씬 빠르다. mtime이 같으면 파싱 결과를 그대로 돌려주고, 달라졌을 때만 재파싱한다.

### 캐시 무효화 타이밍

- `r` 또는 `t` 키로 reload → `load_all_projects()` 재호출 → 파일마다 `load_session()` 통과
- 변경된 파일만 캐시 미스 → 재파싱 후 갱신
- 변경 없는 파일 → 캐시 히트, I/O 없음

이전에는 포스트 생성(`g` 키) 때도 `load_messages()`가 같은 파일을 다시 읽었다. 이제는 캐시를 통하므로 중복 파싱이 없어졌다.

---

## 디스크 캐시로 재시작 후에도 유지

인메모리 캐시는 프로세스가 종료되면 사라진다. 만약 LLM이 생성한 요약 같은 비용이 드는 결과물을 저장해야 한다면 디스크 캐시가 필요하다.

```python
import json
import pathlib

CACHE_FILE = pathlib.Path.home() / ".myapp" / "session_cache.json"
_disk_cache: dict[str, dict] = {}

# 앱 시작 시 로딩
try:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        _disk_cache = json.load(f)
except Exception:
    _disk_cache = {}


def _save_cache() -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_disk_cache, f, ensure_ascii=False, indent=2)
```

`session_id` 를 키로, 파싱 결과와 mtime을 값으로 저장한다. 앱을 재시작해도 이전 파싱 결과를 바로 사용할 수 있다.

저장 위치는 이미 설정 파일이 있는 `~/.myapp/`에 두는 것이 가장 자연스럽다. XDG 표준을 따른다면 `~/.cache/myapp/`도 좋은 선택이다.

---

## API 키 없이 CLI 서브프로세스로 LLM 호출

LLM API 구독은 있지만 API 키가 없는 경우, CLI 도구를 서브프로세스로 호출하면 된다. `subprocess.run()`으로 CLI를 실행하고 stdout을 캡처하는 구조다.

```python
import subprocess
import shutil


def _find_cli_exe() -> Optional[str]:
    # 1. PATH에서 먼저 찾기
    found = shutil.which("mytool")
    if found:
        return found

    # 2. VSCode 확장 등 특정 경로 탐색 (Windows)
    import glob
    pattern = str(
        pathlib.Path.home()
        / ".vscode"
        / "extensions"
        / "vendor.mytool-*"
        / "resources"
        / "native-binary"
        / "mytool.exe"
    )
    candidates = glob.glob(pattern)
    if not candidates:
        return None

    # 버전 정렬: 문자열 정렬이 아닌 버전 튜플로
    def version_key(p: str) -> tuple:
        import re
        m = re.search(r"mytool-(\d+)\.(\d+)\.(\d+)", p)
        return tuple(int(x) for x in m.groups()) if m else (0, 0, 0)

    return sorted(candidates, key=version_key)[-1]


def _call_cli(prompt: str) -> str:
    exe = _find_cli_exe()
    if not exe:
        raise RuntimeError("CLI 실행 파일을 찾을 수 없습니다.")

    result = subprocess.run(
        [exe, "-p", "-"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(pathlib.Path.home()),  # 프로젝트 컨텍스트 격리
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"CLI 오류: {result.stderr}")
    return result.stdout.strip()
```

### Windows에서 PATH 문제

VSCode Marketplace에서 확장으로 설치한 경우, 실행 파일이 `~/.vscode/extensions/vendor.tool-버전/resources/native-binary/` 안에만 존재하고 PATH에는 등록되지 않는다. `shutil.which()`로 못 찾으면 이 경로를 직접 탐색해야 한다.

버전 폴더가 여러 개 있을 때 `sorted(candidates)[-1]`로 정렬하면 `2.1.9`가 `2.1.100`보다 크게 나오는 문자열 정렬 함정에 빠진다. 위 코드처럼 버전을 정수 튜플로 변환해 비교해야 정확하다.

### cwd 격리

서브프로세스를 실행할 때 `cwd`를 홈 디렉터리로 지정하지 않으면, CLI가 현재 작업 디렉토리의 프로젝트 설정 파일을 읽어들여 엉뚱한 컨텍스트로 응답할 수 있다. 블로그 생성 앱 디렉토리에서 실행하면 CLI가 해당 프로젝트의 이전 대화를 참조해서 잘못된 응답을 돌려줬던 것이 이 이유였다.

---

## 응답 파싱: 구분자 기반 구조화

LLM을 두 번 호출(본문 생성 → 제목/태그 추출)하는 대신, 한 번의 호출로 구분자 기반 출력을 받으면 API 비용과 지연을 절반으로 줄일 수 있다.

```python
SYSTEM_PROMPT = """
아래 형식으로 정확히 출력하세요 (다른 텍스트 없이):
===TITLE===
제목 (50자 이내)
===TAGS===
tag1, tag2, tag3
===BODY===
마크다운 본문
"""


def _parse_response(raw: str) -> tuple[str, list[str], str]:
    title, tags_str, body = "", "", ""

    if "===TITLE===" in raw:
        title = raw.split("===TITLE===")[1].split("===")[0].strip()
    if "===TAGS===" in raw:
        tags_raw = raw.split("===TAGS===")[1].split("===")[0].strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    if "===BODY===" in raw:
        body = raw.split("===BODY===")[1].strip()

    return title, tags, body
```

JSON 응답을 받아 `json.loads()`로 파싱하는 것보다 단순하고, 정규식보다 명확하다. LLM이 응답 형식을 벗어나는 경우에도 각 섹션을 독립적으로 파싱하므로 부분적으로 복구할 수 있다.

---

## 메모리 최적화: Lazy Loading

목록에서 세션을 클릭할 때 메시지 전체를 메모리에 올리는 것은 낭비다. 세션 메타데이터(제목, 날짜, 요약)는 목록 표시에 필요하지만, 실제 메시지 내용은 포스트 생성 직전에만 필요하다.

```python
# 나쁜 예: 클릭할 때마다 로딩
def on_session_selected(self, session: Session) -> None:
    messages = load_messages(session)  # ← 불필요한 I/O
    self.update_preview(messages)

# 좋은 예: 생성 직전에만 로딩
async def _generate_post(self, sessions: list[Session]) -> None:
    self.status_bar.update("대화 내용 수집 중...")
    all_messages = []
    for session in sessions:
        messages = load_messages(session)  # 여기서만 로딩
        all_messages.extend(messages)
    
    self.status_bar.update("CLI 호출 중...")
    result = _call_cli(build_prompt(all_messages))
    # ...
    
    # 사용 후 명시적으로 참조 해제 (GC 유도)
    del all_messages
```

세션이 수백 개이고 각 세션에 수십~수백 턴의 대화가 있다면, 전부 메모리에 올리는 것은 수백 MB에 달할 수 있다. 생성 직전에만 로딩하고 즉시 참조를 해제하면 메모리 사용량을 상시 수 MB 수준으로 유지할 수 있다.

---

## 정리

이번 작업에서 배운 핵심은 세 가지다.

1. **append-only 파일에는 mtime이 완벽한 캐시 키다.** 복잡한 해시 계산이나 버전 관리 없이 `stat().st_mtime` 비교 한 줄로 충분하다.

2. **실행 파일은 PATH에 없을 수 있다.** 특히 Windows에서 IDE 확장으로 설치된 도구는 자체 디렉토리에만 존재한다. `shutil.which()` 실패 시 알려진 경로를 탐색하는 fallback을 항상 준비해두는 것이 좋다.

3. **데이터는 필요한 시점에만 로딩하라.** 목록 표시와 상세 처리에 필요한 데이터를 분리하고, 무거운 데이터는 실제 사용 직전에 로딩하면 메모리와 초기 로딩 시간을 모두 아낄 수 있다.