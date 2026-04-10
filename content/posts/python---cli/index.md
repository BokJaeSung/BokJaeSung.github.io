---
title: "Python 앱에서 외부 CLI 실행 파일 경로 탐지 및 디버깅"
date: 2026-04-10T22:07:45+09:00
tags: ["python", "debugging", "cli", "subprocess", "path-detection"]
cover:
  image: 'images/cover.jpg'
  alt: 'Python 앱에서 외부 CLI 실행 파일 경로 탐지 및 디버깅'
  relative: true
summary: ""
---

## 문제 상황

터미널 기반 Python 앱을 만들면서 외부 CLI 실행 파일(`*.exe`)을 subprocess로 호출해야 했다. 경로 탐지 로직을 직접 작성했는데, 실제로 제대로 동작하는지 확인이 필요했다.

## 경로 탐지 로직 확인

`summarizer.py` 안에 CLI 실행 파일 경로를 탐색하는 코드가 있었다. 핵심은 시스템 PATH 및 일반적인 설치 경로를 순서대로 탐색하고, 찾은 경로를 로그에 기록하는 구조였다.

```python
import shutil
import logging

def find_cli_executable():
    # PATH에서 먼저 탐색
    path = shutil.which("mytool")
    if path:
        logging.debug(f"CLI 실행 경로: {path}")
        return path

    # 일반 설치 경로 순서대로 확인
    candidates = [
        r"C:\Users\{username}\AppData\Local\Programs\mytool\mytool.exe",
        r"C:\Program Files\mytool\mytool.exe",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            logging.debug(f"CLI 실행 경로: {candidate}")
            return candidate

    return None
```

## 디버그 로그 설정

앱 실행 중 경로 탐지 성공 여부를 확인하기 위해 파일 기반 로그를 설정했다.

```python
import logging
import os

log_path = os.path.expanduser("~/.myapp/debug.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
```

## 디버깅 절차

1. 앱을 실행하고 실행 파일 호출이 발생하는 액션을 트리거한다.
2. 로그 파일을 확인한다.

```bash
cat ~/.myapp/debug.log
```

로그에 `CLI 실행 경로: C:\Users\...\mytool.exe` 형태로 찍히면 경로 탐색 단계는 성공이다. 이후 에러가 있다면 subprocess 호출 단계의 문제이므로 거기서부터 이어서 디버깅한다.

## 핵심 교훈

- 경로 탐지와 실제 실행은 분리해서 단계별로 검증한다.
- 탐지된 경로를 로그에 즉시 기록해두면 "경로 문제인가 vs 실행 문제인가"를 빠르게 구분할 수 있다.
- `shutil.which()`는 PATH 기반 탐색에 가장 간단하고 크로스플랫폼 친화적인 방법이다.