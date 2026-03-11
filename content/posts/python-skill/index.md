---
title: 'Pythonic Codes'
date: 2026-03-11T08:00:00+09:00
tags: ['python', 'codingtest', 'string', 'while', 'switch']
cover:
  image: 'images/cover.jpg'
  alt: 'Pythonic code patterns for coding tests'
  relative: true
summary: 'Python patterns picked up from coding tests — while loops, string immutability, switch alternatives, replace behavior, and list comprehensions'
---

## else는 어디에 묶이나

```python
while True:
    answer.append(n)
    if n == 1:
        break
    if n % 2 == 0:
        n /= 2
    else:           # ← if n % 2 == 0 에 묶임
        n = 3 * n + 1
```

`else`는 같은 들여쓰기의 바로 위 `if`에 붙는다. 헷갈리면 들여쓰기 레벨만 보면 됨.

---

## while 루프 탈출 조건

### 종료 조건이 명확하면 그냥 while에 박으면 됨

```python
while n != 1:
    n = n // 2 if n % 2 == 0 else 3 * n + 1
```

### 루프 중간에서 체크해야 하면 while True + break

```python
while True:
    data = input("입력: ")
    if data == "quit":
        break
    print(data)
```

### 판단 기준

| 상황 | 패턴 |
|------|------|
| 종료 조건을 루프 전에 알 수 있음 | `while 조건` |
| 루프 돌다가 종료 조건이 생김 | `while True + break` |

`while True` 쓸 거면 break 조건부터 써놓고 시작하는 게 낫다. 안 그러면 무한루프 디버깅하다 시간 다 날림.

---

## 파이썬에 switch 없음

### match (Python 3.10+)

```python
match n:
    case 1:
        print("one")
    case 2:
        print("two")
    case _:     # default
        print("other")
```

### if / elif

```python
if n == 1:
    print("one")
elif n == 2:
    print("two")
else:
    print("other")
```

### dict lookup

```python
cases = {1: "one", 2: "two", 3: "three"}
result = cases.get(n, "other")
```

코테에선 dict가 제일 짧음. 조건 복잡해지면 if/elif 쓰면 됨.

---

## replace() 시간복잡도

- `replace()` → `O(n * m)`
- `for`문 → `O(n)`
- 근데 단일 문자 replace면 m=1이라 사실상 똑같음

### 동작 방식

```python
"aaaa".replace("aa", "b")   # "bb"  ← 앞에서부터 먹고 진행
"aaa".replace("aa", "b")    # "ba"  ← aa 먹고 a 남음
```

왼쪽에서 오른쪽으로 한 번만 스캔하고 끝. 교체 결과를 다시 검사하지 않음.

---

## 문자열은 immutable

```python
myString[i] = 'l'   # ❌ TypeError
```

파이썬 문자열은 인덱스로 수정 못 함. replace, upper, 슬라이싱 전부 새 문자열 만들어서 반환하는 거임.

```python
def solution(myString):
    return ''.join(c if c >= 'l' else 'l' for c in myString)
```

`ord()` 안 써도 문자끼리 직접 비교 됨. `'a' >= 'l'` 이런 식으로.

---

## 변수명 덮어쓰는 실수

```python
def solution(a, b, c):
    a = len(set([a, b, c]))  # ❌ a 날아감
    if a == 1:
        answer = (a + b + c) * ...  # a가 len() 결과라 전부 틀림
```

```python
def solution(a, b, c):
    unique = len(set([a, b, c]))  # ✅
    if unique == 1:
        answer = (a + b + c) * (a**2 + b**2 + c**2) * (a**3 + b**3 + c**3)
```

파라미터랑 다른 변수명 쓰는 거 기본임. `unique`, `cnt`, `k` 이런 거로.

---

## 콜라츠 수열 리팩토링

```python
# Before
def solution(n):
    answer = []
    while True:
        answer.append(n)
        if n == 1:
            break
        if n % 2 == 0:
            n /= 2
        else:
            n = 3 * n + 1
    return answer

# After
def solution(n):
    answer = []
    while n != 1:
        answer.append(n)
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    return answer + [1]
```

- `while True + break` → while 조건으로
- if/else → 삼항연산자
- `/=` → `//=` (float 변환 버그 있었음)

---

## 리스트 컴프리헨션 + join 패턴

```python
def solution(myString):
    answer = [x if x > 'l' else 'l' for x in myString]
    return ''.join(answer)
```

문자열 순회하면서 조건 처리할 때 기본 패턴. 리스트 컴프리헨션으로 만들고 join으로 합치면 됨.

한 줄로 더 줄이면

```python
def solution(myString):
    return ''.join(x if x > 'l' else 'l' for x in myString)
```

answer 변수 없이 제너레이터 바로 join에 넘기는 것도 됨. 취향 차이.