---
title: "APS.05 RMQ, Segment Tree, Sparse Table"
date: 2026-04-07T09:00:00+09:00
tags: ["알고리즘", "세그먼트트리", "RMQ", "SparseTable", "LCA"]
cover:
  image: 'images/cover.jpg'
  alt: 'APS.05 RMQ, Segment Tree, Sparse Table'
  relative: true
summary: "From range minimum query to LCA in O(1): Segment Tree, Sparse Table, and Euler tour reduction."
---

## 전체 흐름

```
LCA 문제
   ↓ 오일러 투어
배열로 변환
   ↓ RMQ로 환원
구간 최솟값 문제
   ↓ Segment Tree 또는 Sparse Table
O(log n) 또는 O(1) 쿼리
```

---

## RMQ (Range Minimum Query)

배열에서 특정 구간 `[l, r]`의 최솟값을 구하는 문제.

| 방법 | 전처리 | 쿼리 | 업데이트 |
|------|--------|------|----------|
| 단순 탐색 | O(1) | O(n) | O(1) |
| 세그먼트 트리 | O(n) | O(log n) | O(log n) |
| Sparse Table | O(n log n) | O(1) | 불가 |

---

## Segment Tree

### 핵심 아이디어

구간별 최솟값(또는 합 등)을 트리 구조로 미리 저장해두는 자료구조.

```
[0~7] : 1
├── [0~3] : 3
│   ├── [0~1] : 5
│   └── [2~3] : 3
└── [4~7] : 1
    ├── [4~5] : 1
    └── [6~7] : 2
```

각 노드는 **"내 담당 구간의 최솟값"** 을 저장한다.

### 배열로 저장 (힙 구조)

트리를 배열로 저장할 때 포인터 없이 인덱스만으로 이동한다.

- `tree[k]`의 부모 → `tree[k/2]`
- `tree[k]`의 자식 → `tree[2k]`, `tree[2k+1]`

배열 크기는 `4n`으로 잡는 것이 국룰이다. 이유는 아래와 같다.

- 트리 높이 `h = ceil(log2(n))`
- 최대 인덱스 = `2^(h+1) - 1`
- `h <= log2(n) + 1` 이므로 최대 인덱스 `<= 2^(log2(n)+2) = 4n`

n이 2의 거듭제곱보다 1만 커도 레벨이 하나 더 생겨 배열이 2배로 뛰기 때문에 `4n`으로 여유 있게 잡는다.

### 구현 (Python)

```python
n = len(arr)
tree = [0] * (4 * n)

def build(node, s, e):
    if s == e:
        tree[node] = arr[s]
        return
    mid = (s + e) // 2
    build(2*node, s, mid)
    build(2*node+1, mid+1, e)
    tree[node] = min(tree[2*node], tree[2*node+1])

def query(node, s, e, l, r):
    if l > r:
        return float('inf')
    if s == l and e == r:
        return tree[node]
    mid = (s + e) // 2
    return min(
        query(2*node,   s,   mid, l,           min(r, mid)),
        query(2*node+1, mid+1, e, max(l, mid+1), r)
    )

def update(node, s, e, idx, val):
    if s == e:
        tree[node] = val
        return
    mid = (s + e) // 2
    if idx <= mid: update(2*node,   s,   mid, idx, val)
    else:          update(2*node+1, mid+1, e, idx, val)
    tree[node] = min(tree[2*node], tree[2*node+1])
```

### 쿼리 원리 — 각 레벨에서 최대 2개 노드

쿼리 범위 `[l, r]`에는 왼쪽 끝점 `l`, 오른쪽 끝점 `r` 딱 2개뿐이다. "걸쳐있음(일부만 겹침)"은 이 두 끝점 근처에서만 발생하고, 중간 노드들은 전부 완전 포함 또는 완전 제외로 바로 처리된다.

따라서 각 레벨에서 더 내려가야 하는 노드는 최대 2개이고, 트리 높이가 `O(log n)`이므로 전체 쿼리 시간복잡도는 `O(log n)`이다.

{{< rawhtml >}}
<svg width="100%" viewBox="0 0 680 440" xmlns="http://www.w3.org/2000/svg" style="font-family:sans-serif;">
  <defs>
    <marker id="arr1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="#888780" stroke-width="1.5" stroke-linecap="round"/>
    </marker>
  </defs>
  <!-- 범례 -->
  <rect x="60" y="10" width="12" height="12" rx="2" fill="#fde8e8" stroke="#E24B4A" stroke-width="1"/>
  <text x="78" y="20" font-size="12" fill="#5f5e5a">걸쳐있음 → 더 내려감</text>
  <rect x="230" y="10" width="12" height="12" rx="2" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1"/>
  <text x="248" y="20" font-size="12" fill="#5f5e5a">완전 포함 → 리턴 ✓</text>
  <rect x="390" y="10" width="12" height="12" rx="2" fill="#f5f5f3" stroke="#b4b2a9" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="408" y="20" font-size="12" fill="#5f5e5a">완전 제외 → 무시</text>
  <!-- 레벨 라벨 -->
  <text x="28" y="78" font-size="11" fill="#888780" text-anchor="middle">Lv 0</text>
  <text x="28" y="158" font-size="11" fill="#888780" text-anchor="middle">Lv 1</text>
  <text x="28" y="238" font-size="11" fill="#888780" text-anchor="middle">Lv 2</text>
  <text x="28" y="318" font-size="11" fill="#888780" text-anchor="middle">Lv 3</text>
  <!-- 쿼리 범위 바 -->
  <text x="340" y="415" font-size="13" fill="#2c2c2a" text-anchor="middle" font-weight="500">쿼리: [3 ~ 13]</text>
  <rect x="196" y="400" width="350" height="4" rx="2" fill="#EF9F27" opacity="0.8"/>
  <text x="196" y="397" font-size="11" fill="#888780" text-anchor="middle">3</text>
  <text x="546" y="397" font-size="11" fill="#888780" text-anchor="middle">13</text>
  <!-- Lv0: [0~15] 걸쳐있음 -->
  <rect x="290" y="58" width="100" height="34" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="340" y="80" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">0 ~ 15</text>
  <!-- Lv1 -->
  <rect x="130" y="138" width="100" height="34" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="180" y="160" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">0 ~ 7</text>
  <rect x="450" y="138" width="100" height="34" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="500" y="160" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">8 ~ 15</text>
  <!-- Lv2 -->
  <rect x="58" y="218" width="84" height="34" rx="6" fill="#f5f5f3" stroke="#b4b2a9" stroke-width="1" stroke-dasharray="4 3"/>
  <text x="100" y="240" font-size="12" fill="#888780" text-anchor="middle">0 ~ 3</text>
  <rect x="172" y="218" width="84" height="34" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="214" y="240" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">4 ~ 7</text>
  <rect x="378" y="218" width="84" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="420" y="240" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">8~11 ✓</text>
  <rect x="490" y="218" width="90" height="34" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="535" y="240" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">12 ~ 15</text>
  <!-- Lv3 -->
  <rect x="58" y="298" width="70" height="34" rx="6" fill="#fafaf9" stroke="#d3d1c7" stroke-width="0.5" opacity="0.4"/>
  <text x="93" y="320" font-size="11" fill="#b4b2a9" text-anchor="middle" opacity="0.5">0~1</text>
  <rect x="140" y="298" width="70" height="34" rx="6" fill="#fafaf9" stroke="#d3d1c7" stroke-width="0.5" opacity="0.4"/>
  <text x="175" y="320" font-size="11" fill="#b4b2a9" text-anchor="middle" opacity="0.5">2~3</text>
  <rect x="222" y="298" width="70" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="257" y="320" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">4~5 ✓</text>
  <rect x="304" y="298" width="70" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="339" y="320" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">6~7 ✓</text>
  <rect x="378" y="298" width="70" height="34" rx="6" fill="#fafaf9" stroke="#d3d1c7" stroke-width="0.5" opacity="0.4"/>
  <text x="413" y="320" font-size="11" fill="#b4b2a9" text-anchor="middle" opacity="0.5">8~9</text>
  <rect x="460" y="298" width="74" height="34" rx="6" fill="#fafaf9" stroke="#d3d1c7" stroke-width="0.5" opacity="0.4"/>
  <text x="497" y="320" font-size="11" fill="#b4b2a9" text-anchor="middle" opacity="0.5">10~11</text>
  <rect x="545" y="298" width="78" height="34" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="584" y="320" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">12~13</text>
  <!-- Lv4 -->
  <rect x="542" y="358" width="56" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="570" y="379" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">12 ✓</text>
  <rect x="610" y="358" width="56" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="638" y="379" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">13 ✓</text>
  <!-- 엣지 -->
  <line x1="320" y1="92" x2="210" y2="138" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="360" y1="92" x2="470" y2="138" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="160" y1="172" x2="110" y2="218" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="200" y1="172" x2="214" y2="218" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="480" y1="172" x2="420" y2="218" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="520" y1="172" x2="535" y2="218" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="200" y1="252" x2="257" y2="298" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="228" y1="252" x2="339" y2="298" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="560" y1="252" x2="584" y2="298" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="570" y1="332" x2="570" y2="358" stroke="#d3d1c7" stroke-width="0.8"/>
  <line x1="598" y1="332" x2="638" y2="358" stroke="#d3d1c7" stroke-width="0.8"/>
  <!-- 레벨별 걸침 카운트 -->
  <text x="46" y="79" font-size="11" fill="#E24B4A" text-anchor="end">걸침 1</text>
  <text x="46" y="159" font-size="11" fill="#E24B4A" text-anchor="end">걸침 2</text>
  <text x="46" y="239" font-size="11" fill="#E24B4A" text-anchor="end">걸침 2</text>
  <text x="46" y="319" font-size="11" fill="#E24B4A" text-anchor="end">걸침 1</text>
  <text x="46" y="379" font-size="11" fill="#1D9E75" text-anchor="end">리턴 ✓</text>
</svg>
{{< /rawhtml >}}

### 쿼리 함수의 세 가지 케이스

```
① left > right   → 완전 제외, inf 리턴 (min에 영향 없음)
② s==l, e==r     → 완전 포함, tree[node] 바로 리턴
③ 그 외          → 걸쳐있음, 반으로 쪼개 재귀
```

쿼리 `[2~3]`에서 `inf`가 발생하는 흐름:

{{< rawhtml >}}
<svg width="100%" viewBox="0 0 680 510" xmlns="http://www.w3.org/2000/svg" style="font-family:sans-serif;">
  <rect x="60" y="10" width="12" height="12" rx="2" fill="#fde8e8" stroke="#E24B4A" stroke-width="1"/>
  <text x="78" y="20" font-size="12" fill="#5f5e5a">걸쳐있음</text>
  <rect x="160" y="10" width="12" height="12" rx="2" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1"/>
  <text x="178" y="20" font-size="12" fill="#5f5e5a">완전 포함 ✓</text>
  <rect x="290" y="10" width="12" height="12" rx="2" fill="#f5f5f3" stroke="#b4b2a9" stroke-width="1" stroke-dasharray="3 2"/>
  <text x="308" y="20" font-size="12" fill="#5f5e5a">left &gt; right → inf</text>
  <text x="340" y="48" font-size="13" fill="#2c2c2a" text-anchor="middle" font-weight="500">쿼리: [2 ~ 3]</text>
  <rect x="270" y="60" width="140" height="44" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="340" y="78" font-size="11" fill="#888780" text-anchor="middle">node [0~7]</text>
  <text x="340" y="96" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">query(2~3)</text>
  <line x1="310" y1="104" x2="190" y2="156" stroke="#b4b2a9" stroke-width="1"/>
  <line x1="370" y1="104" x2="490" y2="156" stroke="#b4b2a9" stroke-width="1"/>
  <text x="215" y="136" font-size="11" fill="#1D9E75" text-anchor="middle">right=min(3,3)=3</text>
  <text x="465" y="136" font-size="11" fill="#E24B4A" text-anchor="middle">left=max(2,4)=4</text>
  <text x="465" y="148" font-size="11" fill="#E24B4A" text-anchor="middle">right=3  →  4&gt;3!</text>
  <rect x="100" y="156" width="140" height="44" rx="6" fill="#fde8e8" stroke="#E24B4A" stroke-width="1.5"/>
  <text x="170" y="174" font-size="11" fill="#888780" text-anchor="middle">node [0~3]</text>
  <text x="170" y="192" font-size="13" fill="#A32D2D" text-anchor="middle" font-weight="500">query(2~3)</text>
  <rect x="420" y="156" width="140" height="44" rx="6" fill="#f5f5f3" stroke="#b4b2a9" stroke-width="1" stroke-dasharray="4 3"/>
  <text x="490" y="174" font-size="11" fill="#888780" text-anchor="middle">node [4~7]</text>
  <text x="490" y="192" font-size="13" fill="#888780" text-anchor="middle">4 &gt; 3 → inf</text>
  <line x1="150" y1="200" x2="100" y2="252" stroke="#b4b2a9" stroke-width="1"/>
  <line x1="190" y1="200" x2="300" y2="252" stroke="#b4b2a9" stroke-width="1"/>
  <text x="80" y="238" font-size="11" fill="#888780" text-anchor="middle">right=min(3,1)=1</text>
  <text x="80" y="250" font-size="11" fill="#E24B4A" text-anchor="middle">→ 2&gt;1!</text>
  <text x="315" y="238" font-size="11" fill="#1D9E75" text-anchor="middle">left=2, right=3</text>
  <rect x="30" y="252" width="130" height="44" rx="6" fill="#f5f5f3" stroke="#b4b2a9" stroke-width="1" stroke-dasharray="4 3"/>
  <text x="95" y="270" font-size="11" fill="#888780" text-anchor="middle">node [0~1]</text>
  <text x="95" y="288" font-size="13" fill="#888780" text-anchor="middle">2 &gt; 1 → inf</text>
  <rect x="230" y="252" width="130" height="44" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="295" y="270" font-size="11" fill="#888780" text-anchor="middle">node [2~3]</text>
  <text x="295" y="288" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">query(2~3) ✓</text>
  <line x1="295" y1="296" x2="295" y2="336" stroke="#1D9E75" stroke-width="1.2"/>
  <rect x="230" y="336" width="130" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1"/>
  <text x="295" y="357" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">값 리턴</text>
  <line x1="95" y1="296" x2="95" y2="336" stroke="#b4b2a9" stroke-width="1"/>
  <rect x="30" y="336" width="130" height="34" rx="6" fill="#f5f5f3" stroke="#b4b2a9" stroke-width="1" stroke-dasharray="4 3"/>
  <text x="95" y="357" font-size="13" fill="#888780" text-anchor="middle">inf 리턴</text>
  <line x1="95" y1="370" x2="170" y2="410" stroke="#b4b2a9" stroke-width="1"/>
  <line x1="295" y1="370" x2="170" y2="410" stroke="#b4b2a9" stroke-width="1"/>
  <rect x="80" y="410" width="180" height="34" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="170" y="431" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">min(inf, 값) = 값</text>
  <line x1="170" y1="444" x2="340" y2="478" stroke="#b4b2a9" stroke-width="1"/>
  <line x1="490" y1="200" x2="340" y2="478" stroke="#b4b2a9" stroke-width="0.8" stroke-dasharray="4 3"/>
  <rect x="240" y="478" width="200" height="24" rx="6" fill="#e1f5ee" stroke="#1D9E75" stroke-width="1.5"/>
  <text x="340" y="494" font-size="13" fill="#0F6E56" text-anchor="middle" font-weight="500">min(값, inf) = 최종 답</text>
</svg>
{{< /rawhtml >}}

---

## Sparse Table

### 핵심 아이디어

`st[i][j] = A[i]부터 2^j개의 최솟값`을 미리 전처리해두고, 쿼리를 2개의 구간으로 덮어 O(1)에 해결한다.

- `i`: 시작 인덱스
- `j`: 구간 길이의 지수 (2^j개)

### 전처리 — DP로 O(n log n)

```python
st[i][0] = A[i]  # 길이 1짜리

# 작은 구간 2개를 합쳐 큰 구간 만들기
st[i][j] = min(st[i][j-1], st[i + 2^(j-1)][j-1])
#               왼쪽 절반        오른쪽 절반 시작점
```

오른쪽 절반의 시작점이 `i + 2^(j-1)`인 이유: 왼쪽이 `i`부터 `2^(j-1)`개를 차지하므로 오른쪽은 그 다음인 `i + 2^(j-1)`부터 시작한다.

### 쿼리 — O(1)

```python
def query(L, R):
    length = R - L + 1
    k = floor(log2(length))
    return min(st[L][k], st[R - 2**k + 1][k])
```

길이 `ℓ = R - L + 1`에 대해 `k = floor(log2(ℓ))`로 잡으면, 길이 `2^k`짜리 구간 2개가 `[L, R]`을 완전히 덮는다.

```
쿼리 [3 ~ 13], 길이 11, k=3, 2^k=8

왼쪽:  [3  ~ 10]  (3부터 8개)
오른쪽: [6  ~ 13]  (13-8+1=6 부터 8개)

겹치는 부분이 있어도 최솟값이라 상관없음
```

두 구간이 겹쳐도 되는 이유: 최솟값은 겹쳐도 결과가 동일하기 때문이다.

### 인터랙티브 — 직접 쿼리해보기

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);font-family:sans-serif;">
<style>
.sp-cell{width:42px;height:42px;display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid #2a2d3a;border-radius:6px;font-size:12px;background:#1a1d27;color:#b0b8d0;transition:background .2s,border-color .2s;}
.sp-cell.hl-l{background:#1b3a2e;border-color:#1D9E75;color:#69f0ae;font-weight:600;}
.sp-cell.hl-r{background:#1e1a3a;border-color:#7986cb;color:#b39ddb;font-weight:600;}
.sp-cell.hl-b{background:#3a2e00;border-color:#ffd740;color:#ffd740;font-weight:600;}
.sp-cell .sp-idx{font-size:9px;opacity:.5;}
.sp-row{display:flex;gap:5px;align-items:center;margin-bottom:5px;}
.sp-lbl{font-size:12px;color:#556;width:68px;text-align:right;flex-shrink:0;}
</style>
<div style="font-size:12px;color:#556;margin-bottom:6px;letter-spacing:.06em;text-transform:uppercase;">원본 배열 A</div>
<div class="sp-row" id="sp-arr"></div>
<div style="font-size:12px;color:#556;margin:14px 0 6px;letter-spacing:.06em;text-transform:uppercase;">Sparse Table st[i][j]</div>
<div id="sp-table"></div>
<div style="margin:18px 0 10px;border-top:1px solid #2a2d3a;padding-top:16px;font-size:12px;color:#556;letter-spacing:.06em;text-transform:uppercase;">쿼리 범위</div>
<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-bottom:12px;">
  <div style="display:flex;align-items:center;gap:8px;"><label style="font-size:12px;color:#778;">L</label><input type="range" id="sp-l" min="0" max="7" value="2" step="1" style="width:90px;"><span id="sp-lv" style="font-size:13px;font-weight:600;color:#69f0ae;min-width:14px;">2</span></div>
  <div style="display:flex;align-items:center;gap:8px;"><label style="font-size:12px;color:#778;">R</label><input type="range" id="sp-r" min="0" max="7" value="6" step="1" style="width:90px;"><span id="sp-rv" style="font-size:13px;font-weight:600;color:#b39ddb;min-width:14px;">6</span></div>
</div>
<div id="sp-vis" style="margin-bottom:12px;"></div>
<div id="sp-res" style="background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:12px 14px;font-size:13px;color:#b0b8d0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;"></div>
</div>
<script>
(function(){
const A=[3,1,4,1,5,9,2,6],n=8;
const st=Array.from({length:n},()=>Array(4).fill(0));
for(let i=0;i<n;i++)st[i][0]=A[i];
for(let j=1;(1<<j)<=n;j++)for(let i=0;i+(1<<j)-1<n;i++)st[i][j]=Math.min(st[i][j-1],st[i+(1<<(j-1))][j-1]);
function render(){
  const ar=document.getElementById('sp-arr');
  ar.innerHTML='<div class="sp-lbl">A[i]</div>';
  A.forEach((v,i)=>{ar.innerHTML+=`<div class="sp-cell" id="spa${i}"><div class="sp-idx">${i}</div><div>${v}</div></div>`;});
  const tb=document.getElementById('sp-table');
  tb.innerHTML='';
  for(let j=0;j<4;j++){if((1<<j)>n)break;const row=document.createElement('div');row.className='sp-row';row.innerHTML=`<div class="sp-lbl">j=${j} (${1<<j}개)</div>`;for(let i=0;i<n;i++){if(i+(1<<j)-1<n){row.innerHTML+=`<div class="sp-cell" id="st${i}_${j}"><div class="sp-idx">[${i}][${j}]</div><div>${st[i][j]}</div></div>`;}else{row.innerHTML+=`<div style="width:42px;flex-shrink:0;"></div>`;}}tb.appendChild(row);}
}
function update(){
  let L=+document.getElementById('sp-l').value,R=+document.getElementById('sp-r').value;
  if(L>R){L=R;document.getElementById('sp-l').value=L;}
  document.getElementById('sp-lv').textContent=L;
  document.getElementById('sp-rv').textContent=R;
  document.querySelectorAll('.sp-cell').forEach(e=>e.classList.remove('hl-l','hl-r','hl-b'));
  const len=R-L+1,k=Math.floor(Math.log2(len)),rs=R-(1<<k)+1;
  for(let i=0;i<n;i++){const e=document.getElementById(`spa${i}`);if(!e)continue;const il=i>=L&&i<=L+(1<<k)-1,ir=i>=rs&&i<=R;if(il&&ir)e.classList.add('hl-b');else if(il)e.classList.add('hl-l');else if(ir)e.classList.add('hl-r');}
  const sl=document.getElementById(`st${L}_${k}`),sr=document.getElementById(`st${rs}_${k}`);
  if(sl)sl.classList.add('hl-l');
  if(sr){sr.classList.remove('hl-l');sr.classList.add(rs===L?'hl-b':'hl-r');}
  const lp=(L/n*100).toFixed(1),lw=((1<<k)/n*100).toFixed(1),rp=(rs/n*100).toFixed(1),rw=((1<<k)/n*100).toFixed(1);
  document.getElementById('sp-vis').innerHTML=`<div style="font-size:11px;color:#556;margin-bottom:6px;letter-spacing:.05em;">구간 커버 (겹쳐도 OK)</div><div style="position:relative;height:50px;background:#111318;border-radius:6px;overflow:hidden;"><div style="position:absolute;left:${lp}%;width:${lw}%;height:24px;background:rgba(29,158,117,.25);border:1.5px solid #1D9E75;border-radius:3px;top:4px;display:flex;align-items:center;justify-content:center;"><span style="font-size:10px;color:#69f0ae;font-weight:600;">[${L}~${L+(1<<k)-1}]</span></div><div style="position:absolute;left:${rp}%;width:${rw}%;height:24px;background:rgba(121,134,203,.2);border:1.5px solid #7986cb;border-radius:3px;top:22px;display:flex;align-items:center;justify-content:center;"><span style="font-size:10px;color:#b39ddb;font-weight:600;">[${rs}~${R}]</span></div></div>`;
  const ans=Math.min(st[L][k],st[rs][k]);
  document.getElementById('sp-res').innerHTML=`길이 ${len} → k=⌊log2(${len})⌋=${k} → 2<sup>${k}</sup>=${1<<k}개짜리 2개<br><span style="color:#69f0ae;">st[${L}][${k}] = ${st[L][k]}</span>  ·  <span style="color:#b39ddb;">st[${rs}][${k}] = ${st[rs][k]}</span>  →  <strong style="color:#ffd740;">min = ${ans}</strong>`;
}
render();update();
document.getElementById('sp-l').addEventListener('input',update);
document.getElementById('sp-r').addEventListener('input',update);
})();
</script>
{{< /rawhtml >}}

### 업데이트가 불가능한 이유

값 하나가 바뀌면 그 값을 포함하는 `st[i][j]` 칸을 전부 다시 계산해야 한다. 이는 사실상 전처리 `O(n log n)`을 다시 하는 것과 같다.

---

## Segment Tree vs Sparse Table

| | Segment Tree | Sparse Table |
|---|---|---|
| 전처리 | O(n) | O(n log n) |
| 쿼리 | O(log n) | O(1) |
| 업데이트 | O(log n) | 불가 |

**선택 기준:**
- 배열이 고정 (쿼리만 있음) → Sparse Table
- 배열이 바뀜 (업데이트 + 쿼리) → Segment Tree

LCA 문제에서 트리 구조가 고정이면 오일러 투어 배열도 불변이므로 Sparse Table이 최적이다.

---

## LCA와의 연결

```
LCA(u, v)
= 오일러 투어 배열에서 u와 v 사이 구간의 최솟값(깊이 기준)에 해당하는 노드
= RMQ(euler_tour, first[u], first[v])
```

Sparse Table로 전처리하면 LCA 쿼리를 O(1)에 처리할 수 있다.