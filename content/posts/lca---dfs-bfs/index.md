---
title: "LCA 바이너리 리프팅: DFS와 BFS 방식의 차이"
date: 2026-04-05T22:52:30+09:00
tags: ["algorithm", "LCA", "binary-lifting", "tree", "dp", "dfs", "bfs"]
cover:
  alt: 'LCA 바이너리 리프팅: DFS와 BFS 방식의 차이'
  relative: true
summary: ""
---

## LCA 바이너리 리프팅이란?

LCA(Lowest Common Ancestor, 최소 공통 조상)는 두 노드의 공통 조상 중 가장 깊은 노드를 찾는 알고리즘이다. 바이너리 리프팅(Binary Lifting)은 이를 O(log N) 시간에 처리하기 위해 **희소 테이블(Sparse Table)** 을 사전에 구축하는 방식이다.

핵심 아이디어는 다음과 같다. `parent[v][k]`를 "노드 v의 2^k번째 조상"으로 정의하면, 점화식은 아래와 같다:

```
parent[v][k] = parent[parent[v][k-1]][k-1]
```

즉, v의 2^k번째 조상은 "v의 2^(k-1)번째 조상의 2^(k-1)번째 조상"이다. 이 점화식을 미리 계산해두면 임의의 조상을 빠르게 탐색할 수 있다.

## 문제의 출발점: K 루프를 어디에 두어야 하나?

테이블을 채울 때 아래 두 구조 중 어느 것이 맞는지 처음에는 헷갈렸다.

**구조 A** - K 루프가 안쪽:
```python
for v in all_nodes:
    for k in range(1, LOG):
        if parent[v][k-1] is not None:
            parent[v][k] = parent[parent[v][k-1]][k-1]
```

**구조 B** - K 루프가 바깥쪽:
```python
for k in range(1, LOG):
    for v in all_nodes:
        if parent[v][k-1] is not None:
            parent[v][k] = parent[parent[v][k-1]][k-1]
```

결론부터 말하면, **DFS 방식에서는 A도 가능하고, BFS/반복문 방식에서는 B만 정확하다.**

## DFS에서 K 루프가 안쪽이어도 괜찮은 이유

DFS는 트리를 **위에서 아래로(top-down)** 탐색한다. 루트에서 시작해 자식을 재귀 호출하기 **전에** 현재 노드의 테이블을 전부 채운다.

```python
def dfs(u, p, d):
    parent[u][0] = p
    for k in range(1, LOG):       # 현재 노드의 K를 전부 채움
        if parent[u][k-1] is not None:
            parent[u][k] = parent[parent[u][k-1]][k-1]
    depth[u] = d

    for v in graph[u]:
        if v != p:
            dfs(v, u, d + 1)      # 그 다음에 자식으로 내려감
```

트리 `1 → 2 → 3 → 4`에서 DFS 호출 순서를 추적하면 이렇다:

```
dfs(1) 실행 → parent[1]의 모든 K 채움
  └─ dfs(2) 실행 → parent[2]의 모든 K 채움  ← 이때 1의 K는 이미 완성
       └─ dfs(3) 실행 → parent[3]의 모든 K 채움  ← 이때 1, 2의 K는 이미 완성
            └─ dfs(4) 실행 → parent[4]의 모든 K 채움
```

예를 들어 `parent[3][2]`를 채우려면 `parent[parent[3][1]][1]`이 필요하다.

- `parent[3][1]` = 3의 2번째 조상 = **1**
- `parent[1][1]` = 1의 2번째 조상

`dfs(3)`이 실행될 시점에 `dfs(1)`은 이미 완료됐으므로 `parent[1][1]`은 반드시 존재한다. DFS의 구조가 **"내 조상들의 테이블은 항상 나보다 먼저 완성된다"** 는 것을 보장하기 때문이다.

## BFS에서 K 루프를 반드시 바깥으로 꺼내야 하는 이유

BFS는 **레벨 순서**로 노드를 처리한다:

```
레벨 0: [1]
레벨 1: [2]
레벨 2: [3]
레벨 3: [4]
```

K 루프를 안쪽에 두고 노드 2를 처리한다고 가정하면:

- `parent[2][1]` = `parent[parent[2][0]][0]` = `parent[1][0]` → **있음** (직접 부모는 k=0이므로)
- `parent[2][2]` = `parent[parent[2][1]][1]` = `parent[1][1]` → **없음!**

노드 1의 `k=1` 값이 아직 채워지지 않은 상태에서 참조하려 하기 때문에 오류가 발생한다. BFS는 레벨 단위로 처리하므로 같은 레벨의 조상의 상위 K값이 완성됐다는 보장이 없다.

올바른 BFS(또는 반복문) 방식은 K를 바깥으로 꺼내어 **"k=0 전체 → k=1 전체 → k=2 전체"** 순서로 채우는 것이다:

```python
for k in range(1, LOG):
    for v in range(1, n + 1):
        if parent[v][k-1] is not None:
            parent[v][k] = parent[parent[v][k-1]][k-1]
```

이렇게 하면 k번째 레이어를 채울 때 k-1번째 레이어가 **모든 노드에 대해** 이미 완성돼 있음을 보장할 수 있다.

## 정리: 방식별 K 루프 위치

| 테이블 채우는 방식 | K 루프 위치 | 이유 |
|---|---|---|
| DFS (top-down 재귀) | 안쪽 가능 | 조상이 항상 자식보다 먼저 처리됨 |
| BFS / 반복문 | **바깥 필수** | `parent[ancestor][k-1]`이 아직 미계산일 수 있음 |

## None이 발생하는 유일한 경우

테이블을 채우다 보면 `None` 체크가 필요한데, 처음엔 "아직 채워지지 않아서 None인 경우도 있나?" 하고 헷갈렸다.

답은 명확하다. DFS 특성상 "아직 안 채워져서 None"인 경우는 **절대 발생하지 않는다.** `None`이 나타나는 유일한 경우는 **루트 위로 올라가려 할 때** 뿐이다.

```python
# 루트의 부모는 없으므로
parent[root][0] = None

# k=1을 채우려 하면
parent[root][1] = parent[parent[root][0]][0]
               = parent[None][0]  # None을 인덱스로 쓰면 오류 → 조건문으로 막음
```

따라서 조건문의 역할은 정확히 하나다:

```python
if parent[u][k-1] is not None:   # 루트 위로 넘어가는 것을 방지
    parent[u][k] = parent[parent[u][k-1]][k-1]
```

이 조건이 없으면 루트의 조상을 계산하려다 런타임 오류가 발생한다.

## 정리하며

바이너리 리프팅의 테이블 구축 로직을 제대로 이해하려면 점화식 `parent[v][k] = parent[parent[v][k-1]][k-1]`의 **의존 관계**를 먼저 파악해야 한다. 우변의 값이 항상 먼저 계산돼 있어야 한다는 조건을 DFS는 구조적으로 보장하고, BFS는 K 루프를 바깥에 두는 방식으로 보장한다.

알고리즘 자체보다 "왜 이렇게 짜야 하는가"를 이해하고 나니 코드를 암기할 필요 없이 자연스럽게 도출할 수 있게 됐다.