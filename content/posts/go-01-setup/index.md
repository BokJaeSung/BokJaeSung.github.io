---
title: "Go.01 Setting Up Your Go Development Environment"
date: 2026-06-28T09:00:00+09:00
tags: ["go", "golang", "환경설정", "개발환경"]
cover:
  image: 'images/cover.jpg'
  alt: 'Go.01 Setting Up Your Go Development Environment'
  relative: true
summary: "How to install Go, configure VS Code, and build your first Hello World program with essential tooling."
---

## 1. 전체 흐름

```
Go 설치
   ↓
go version 확인
   ↓
프로젝트 폴더 생성 (ch1)
   ↓
go mod init (모듈 초기화)
   ↓
hello.go 작성
   ↓
go build → 실행파일 생성
   ↓
go fmt → 코드 자동 정리
   ↓
Makefile 작성 → 빌드 자동화
```

---

## 2. Go 설치

### 플랫폼별 설치 방법

| 플랫폼 | 방법 |
|--------|------|
| Windows | `.msi` 파일 설치 또는 `choco install golang` |
| Mac | `.pkg` 파일 설치 또는 `brew install go` |
| Linux/BSD | `.tar.gz` 압축 해제 후 PATH 등록 |

Windows와 Mac의 설치 파일은 자동으로 올바른 위치에 Go를 설치하고, 이전 버전을 제거하며, 실행 파일을 기본 경로에 추가해줌.

Linux는 직접 PATH를 등록해야 함.

```bash
$ tar -C /usr/local -xzf go1.20.5.linux-amd64.tar.gz
$ echo 'export PATH=$PATH:/usr/local/go/bin' >> $HOME/.bash_profile
$ source $HOME/.bash_profile
```

### 환경변수(PATH)란?

컴퓨터에게 "이 폴더들 안에서 프로그램 찾아봐" 라고 알려주는 목록.

```
터미널에 go 입력
   ↓
$PATH 목록 확인
   ↓
/usr/local/go/bin 폴더에서 go 발견
   ↓
실행 ✅
```

PATH에 등록 안 되어 있으면 → `command not found ❌`

### 설치 확인

```bash
$ go version
go version go1.20.5 windows/amd64
```

---

## 3. Go의 특징

Go 프로그램은 **단일 실행 파일**로 컴파일됨.

| 언어 | 실행 방식 |
|------|-----------|
| Go | 단일 실행 파일로 바로 실행 |
| Java | JVM(가상머신) 필요 |
| Python | Python 인터프리터 필요 |
| JavaScript | Node.js 런타임 필요 |

→ 추가 소프트웨어 없이 바로 실행 가능하기 때문에 배포가 훨씬 쉬움.

---

## 4. 첫 번째 Go 프로그램

### 모듈 초기화

```bash
$ mkdir ch1
$ cd ch1
$ go mod init hello_world
```

`go mod init`을 실행하면 `go.mod` 파일이 자동 생성됨.

```
module hello_world

go 1.20
```

`go.mod` 파일에는 모듈 이름, 최소 지원 Go 버전, 의존하는 외부 패키지 목록이 담겨 있음. Python의 `requirements.txt`, Ruby의 `Gemfile`과 같은 역할.

> `go.mod`는 직접 수정하지 말 것. `go get` 또는 `go mod tidy`로 관리.

### hello.go 작성

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, world!")
}
```

| 구성 요소 | 설명 |
|-----------|------|
| `package main` | 패키지 선언. `main` 패키지가 프로그램 시작점 |
| `import "fmt"` | 표준 라이브러리의 `fmt` 패키지 불러오기 |
| `func main()` | 모든 Go 프로그램의 시작 함수 |
| `fmt.Println(...)` | 화면에 출력하고 줄바꿈 |

Go는 패키지 전체를 import함. 특정 함수나 타입만 골라서 import 불가.

### 빌드 및 실행

```bash
$ go build
$ ./hello_world
Hello, world!
```

실행 파일 이름을 바꾸고 싶을 때 `-o` 플래그 사용.

```bash
$ go build -o hello
```

---

## 5. 주요 Go 도구들

| 명령어 | 역할 |
|--------|------|
| `go build` | 코드를 실행 파일로 컴파일 |
| `go fmt` | 코드 자동 정리 |
| `go vet` | 흔한 실수 검사 |
| `go mod` | 의존성 관리 |
| `go test` | 테스트 실행 |

### go fmt

Go는 코드 형식을 강제함. 탭 들여쓰기, 중괄호 위치 등이 정해져 있음.

```bash
$ go fmt ./...
```

`./...` = 현재 폴더 및 모든 하위 폴더에 적용.

#### 왜 표준 포맷을 강제하나?

표준 포맷이 있으면 **소스 코드를 조작하는 툴**을 만들기가 훨씬 쉬워짐. 컴파일러도 단순해지고, 코드 자동 생성 도구도 만들기 쉬워짐.

부가 효과로, 개발자들이 오랫동안 낭비해온 **포맷 논쟁**을 없애줌. 중괄호 스타일, 탭 vs 스페이스 등의 싸움이 사라짐.

> Go 팀이 먼저 포맷을 표준화해서 논쟁을 없애고 나중에 툴링의 장점을 발견했다고 생각하는 개발자가 많지만, Go의 개발 리더 Russ Cox는 더 나은 툴링이 원래 동기였다고 밝힌 바 있음.

**세미콜론 자동 삽입 규칙** 때문에 중괄호 위치가 고정됨.

Go 컴파일러는 줄 끝이 아래 토큰 중 하나이면 **자동으로 세미콜론을 삽입**함.

| 토큰 종류 | 예시 |
|-----------|------|
| 식별자 | `foo`, `x`, `myVar` |
| 정수/실수/문자열 리터럴 | `42`, `3.14`, `"hello"` |
| `break`, `continue`, `fallthrough`, `return` | — |
| `++`, `--` | — |
| `)`, `]`, `}` | 닫는 괄호류 |

```go
// 줄 끝이 ) → 세미콜론 자동 삽입
func main()
// 컴파일러가 보는 것: func main();

// 결과: { 가 함수 본문이 아닌 독립 블록으로 해석 → 오류
```

```go
// ❌ 잘못된 예시
func main()
{
    fmt.Println("Hello, world!")
}

// 컴파일러가 이렇게 해석함
func main();  // ← 세미콜론 자동 삽입 → 오류!
{
    ...
};
```

```go
// ✅ 올바른 예시 — 줄 끝이 { 이므로 세미콜론 삽입 안 됨
func main() {
    fmt.Println("Hello, world!")
}
```

### go vet

`go fmt`가 형식 문제를 잡는다면, `go vet`은 **문법적으로는 유효하지만 논리적으로 잘못된 코드**를 잡아냄.

대표적인 예: `fmt.Printf`의 플레이스홀더와 인자 개수 불일치.

```go
// ❌ 컴파일은 되지만 잘못된 코드
fmt.Printf("Hello, %s!\n")  // %s에 대응하는 인자가 없음
```

```bash
$ go vet ./...
# hello_world
./hello.go:6:2: fmt.Printf format %s reads arg #1, but call has 0 args
```

```go
// ✅ 올바른 코드
fmt.Printf("Hello, %s!\n", "world")
```

`go vet`이 잡는 주요 케이스:
- 포맷 문자열 플레이스홀더와 인자 개수 불일치
- 잘못된 struct 태그
- unreachable 코드 등

`go vet`으로 잡지 못하는 것들은 서드파티 코드 품질 도구(staticcheck 등)로 보완 가능.

> `go fmt`로 포맷을 정리하고, `go vet`으로 잠재적 버그를 스캔하는 것이 기본 습관. Go 코드가 어떻게 생겨야 하는지는 **Effective Go**와 Go 위키의 **Code Review Comments** 페이지를 참고.

---

## 6. Makefile로 빌드 자동화

IDE는 편리하지만 자동화하기 어려움. 현대 소프트웨어 개발은 **누구든, 어디서든, 언제든 동일하게 실행되는 반복 가능한 빌드**를 요구함.

이런 자동화가 없으면 개발자가 빌드 문제에 어깨를 으쓱하며 "내 컴퓨터에선 되는데요?"라고 말하는 상황이 생김. `make`는 이 문제를 해결하는 도구로, 빌드 단계와 순서를 스크립트로 명시할 수 있음. Unix 시스템에서 1976년부터 사용되어 온 검증된 도구이며, Go 개발자들 사이에서도 표준적으로 채택됨.

```makefile
.DEFAULT_GOAL := build      # make만 쳐도 build 실행

.PHONY: fmt vet build       # 이건 파일 이름 아니고 명령어야!

fmt:                        # fmt 타겟
	go fmt ./...            # → 코드 정리

vet: fmt                    # vet 타겟 (fmt 먼저 실행)
	go vet ./...            # → 버그 검사

build: vet                  # build 타겟 (vet 먼저 실행)
	go build                # → 빌드
```

Makefile 구성 요소:

| 항목 | 설명 |
|------|------|
| target | 콜론(`:`) 앞의 단어. 실행 가능한 작업 단위 |
| 의존 target | `build: vet`에서 `vet`처럼 콜론 뒤에 오는 단어. 먼저 실행됨 |
| `.DEFAULT_GOAL` | `make`만 쳤을 때 실행할 기본 target 지정 |
| `.PHONY` | 프로젝트에 target과 같은 이름의 파일/폴더가 있어도 혼동하지 않도록 방지 |
| 들여쓰기 | 반드시 **탭(tab)**으로 해야 함. 스페이스 사용 시 오류 |

```bash
$ make
go fmt ./...
go vet ./...
go build
```

명령어 하나로 정리 → 검사 → 빌드가 순서대로 자동 실행됨. `make vet`이나 `make fmt`로 개별 실행도 가능.

포맷과 검사가 빌드 전에 항상 실행되도록 강제하기 때문에, 개발자나 CI 서버가 빌드를 실행할 때 어떤 단계도 빠뜨리지 않게 됨.

> Windows는 `make` 기본 지원 안 됨 → Chocolatey 설치 후 `choco install make`로 설치.

---

## 7. 개발 도구 선택

### VS Code (무료)
- Go 확장 프로그램 설치 필요
- 자동으로 **Delve**(디버거)와 **gopls**(언어 서버) 설치해줌
- `gopls` = 코드 자동완성, 오류 검사, 변수 위치 찾기 등을 담당하는 백엔드

### GoLand (유료)
- JetBrains의 Go 전용 IDE
- 플러그인 없이 바로 사용 가능
- 학생 및 오픈소스 기여자는 무료 라이선스 신청 가능

### Go Playground
- 설치 없이 브라우저에서 바로 Go 실행
- `Run` → 실행, `Format` → `go fmt` 적용, `Share` → URL 공유
- 시계가 2009년 11월 10일로 고정 (Go 첫 발표일)
- 민감한 정보 입력 금지 (Share 시 Google 서버에 저장됨)

---

## 8. Go 호환성 약속

Go 개발 도구는 주기적으로 업데이트됨. Go 1.2 이후로는 약 6개월마다 새 버전이 출시되고, 버그·보안 수정이 필요할 때는 패치 릴리즈도 별도로 나옴.

빠른 개발 주기에도 불구하고 Go 팀은 **하위 호환성**을 강하게 약속하고 있기 때문에, 릴리즈는 대규모 변경보다 점진적인 개선 위주임.

**Go 호환성 약속(Go Compatibility Promise)** 이란, Go 버전이 1로 시작하는 동안은 버그나 보안 수정이 아닌 이상 언어 문법이나 표준 라이브러리를 하위 호환성을 깨는 방식으로 변경하지 않겠다는 공식 선언임.

Russ Cox는 GopherCon 2022 기조연설에서 이렇게 말했음:

> "호환성을 우선시한 것이 Go 1에서 우리가 내린 가장 중요한 설계 결정이었다고 생각한다."

| 대상 | 하위 호환성 보장 |
|------|----------------|
| Go 언어 문법 | ✅ 보장 |
| 표준 라이브러리 | ✅ 보장 |
| `go` 명령어 | ❌ 보장 안 됨 |

단, 이 약속은 **`go` 명령어 자체에는 적용되지 않음**. `go` 명령어의 플래그나 동작 방식은 과거에도 하위 호환성 없이 변경된 적이 있고, 앞으로도 그럴 수 있음.

---

## 마치며

Go는 설치부터 빌드까지 매우 간단하고, `go fmt`로 코드 스타일 논쟁을 없애고, 단일 실행 파일로 배포를 단순화한 실용적인 언어.
