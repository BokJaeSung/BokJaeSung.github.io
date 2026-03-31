---
title: "React.01 From DOM to React"
date: 2026-03-31T12:00:00+09:00
tags: ['react', 'dom', 'frontend', 'javascript', 'refactoring']
description: "Covers DOM, Virtual DOM, and React fundamentals, along with decisions made while refactoring a real MPA project to React."
---

DOM부터 React까지 개념을 정리하고, 실제 프로젝트를 React로 리팩터링하면서 결정한 것들을 함께 기록한다.

## 1. DOM (Document Object Model)

### 1.1 DOM이 뭔지

브라우저가 HTML 파일을 받으면 그냥 화면에 텍스트를 뿌리는 게 아니다. 브라우저는 HTML을 읽으면서 머릿속에 구조를 정리한다. 이 정리된 구조가 바로 **DOM**이다.

HTML은 사실 그냥 메모장에 쓴 텍스트 파일이다.

```html
<h1>안녕하세요</h1>
<p>저는 문단입니다</p>
<button>클릭하세요</button>
```

브라우저는 이걸 읽으면서 이렇게 정리한다.

```
document
└── html
    └── body
        ├── h1
        ├── p
        └── button
```

이 트리 구조가 DOM이다. JavaScript는 이 DOM을 통해서 HTML을 건드릴 수 있다.

> **한 줄 요약**: HTML = 설명서 (텍스트), DOM = 브라우저가 그 설명서를 읽고 메모리에 정리한 것, JavaScript = 그 정리된 것을 바꾸는 도구

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 16px;">▶ DOM 트리 시각화</div>
  <div id="dom-tree" style="font-size: 14px; line-height: 2;">
    <div class="dom-node" style="color: #60a5fa; opacity: 0; transition: opacity 0.4s;" data-delay="0">document</div>
    <div class="dom-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="300">└── html</div>
    <div class="dom-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="600">└── body</div>
    <div class="dom-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 72px;" data-delay="900">├── h1 <span style="color:#94a3b8">← "안녕하세요"</span></div>
    <div class="dom-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 72px;" data-delay="1200">├── p <span style="color:#94a3b8">← "저는 문단입니다"</span></div>
    <div class="dom-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 72px;" data-delay="1500">└── button <span style="color:#94a3b8">← "클릭하세요"</span></div>
  </div>
  <button onclick="replayDomTree()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateDomTree() {
  const nodes = document.querySelectorAll('.dom-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayDomTree() { animateDomTree(); }
const domObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateDomTree(); domObserver.disconnect(); }
}, { threshold: 0.5 });
const domTree = document.getElementById('dom-tree');
if (domTree) domObserver.observe(domTree);
</script>

> **핵심**: HTML = 설명서, DOM = 브라우저 메모리 속 구조, JS = 그 구조를 바꾸는 도구

---

### 1.2 JS가 DOM을 건드리는 방법

JavaScript는 DOM API를 통해 HTML 요소를 찾고, 바꾸고, 추가하고, 삭제할 수 있다.

```javascript
// 요소 찾기
document.getElementById("title")

// 텍스트 바꾸기
document.getElementById("title").textContent = "바뀐 제목"

// 색깔 바꾸기
document.getElementById("title").style.color = "red"

// 새 요소 추가하기
const newDiv = document.createElement("div")
document.body.appendChild(newDiv)
```

여기서 중요한 점은 JS가 건드리는 건 **메모리 속 DOM**이지, 원본 HTML 파일이 아니라는 것이다. 새로고침을 하면 HTML 파일을 다시 읽어서 DOM을 새로 만들기 때문에 원래대로 돌아간다.

```
HTML 파일 (디스크에 저장)   → 절대 안 바뀜
DOM (메모리에 존재)         → JS가 건드리는 곳
화면 (DOM 기준으로 그려짐)  → DOM이 바뀌면 화면도 바뀜
```

---

### 1.3 순수 DOM의 한계

순수 JavaScript로 DOM을 직접 건드리면 개발자가 모든 걸 직접 관리해야 한다.

```javascript
// 버튼 눌렀을 때 바뀌어야 하는 게 많으면
document.getElementById("title").textContent = "바뀜"
document.getElementById("count").textContent = 1
document.getElementById("box").style.color = "red"
document.getElementById("btn").classList.add("active")
document.getElementById("list").innerHTML = "..."
// ... 계속
```

바뀌는 게 많아질수록 코드가 폭발한다. 하나라도 빠뜨리면 버그가 생긴다. 이런 문제를 해결하기 위해 jQuery 같은 라이브러리가 등장했고, 이후에 React가 나왔다.

---

## 2. Virtual DOM

### 2.1 왜 필요한지

DOM을 직접 건드리는 건 생각보다 무거운 작업이다. DOM에는 브라우저가 화면을 그리는 데 필요한 모든 정보가 들어있기 때문에, 건드릴 때마다 브라우저가 화면을 다시 계산하고 그려야 한다.

요소 1000개 중에 하나만 바꾸면 되는데 실수로 전체를 갈아엎으면?

```javascript
// 이렇게 하면 1000개 전부 다시 그림
document.getElementById("list").innerHTML = 새목록전체
```

React는 이 문제를 Virtual DOM으로 해결했다.

---

### 2.2 동작 방식 (재조정)

Virtual DOM은 실제 DOM을 건드리기 전에 메모리에서 먼저 계산하고, 바뀐 부분만 실제 DOM에 반영하는 방식이다.

```
상태 바뀜
↓
Virtual DOM에서 새 화면 그려봄 (메모리에서만)
↓
이전 Virtual DOM이랑 비교 (diffing)
↓
"3번째 div의 숫자만 바뀌었네"
↓
실제 DOM에서 그 부분만 수정
```

이 과정을 **재조정(Reconciliation)** 이라고 부른다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 20px; font-family: monospace;">▶ Virtual DOM diffing 시각화</div>
  <div style="display: flex; gap: 16px; align-items: flex-start; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 180px;">
      <div style="color: #94a3b8; font-size: 11px; margin-bottom: 10px; font-family: monospace;">이전 Virtual DOM</div>
      <div style="background: #1e293b; border-radius: 8px; padding: 14px; font-family: monospace; font-size: 13px; line-height: 2;">
        <div style="color: #60a5fa;">ul</div>
        <div style="color: #34d399; padding-left: 16px;">├── li: "사과"</div>
        <div style="color: #34d399; padding-left: 16px;">├── li: "바나나"</div>
        <div style="color: #34d399; padding-left: 16px;">└── li: "포도"</div>
      </div>
    </div>
    <div style="display:flex; align-items:center; padding-top: 40px; color: #f59e0b; font-size: 20px;">→</div>
    <div style="flex: 1; min-width: 180px;">
      <div style="color: #94a3b8; font-size: 11px; margin-bottom: 10px; font-family: monospace;">새 Virtual DOM</div>
      <div style="background: #1e293b; border-radius: 8px; padding: 14px; font-family: monospace; font-size: 13px; line-height: 2;">
        <div style="color: #60a5fa;">ul</div>
        <div style="color: #34d399; padding-left: 16px;">├── li: "사과"</div>
        <div id="vdom-changed" style="color: #fbbf24; padding-left: 16px; background: #292524; border-radius: 4px; transition: all 0.5s;">├── li: "망고" ← 바뀜</div>
        <div style="color: #34d399; padding-left: 16px;">└── li: "포도"</div>
      </div>
    </div>
    <div style="display:flex; align-items:center; padding-top: 40px; color: #f59e0b; font-size: 20px;">→</div>
    <div style="flex: 1; min-width: 180px;">
      <div style="color: #94a3b8; font-size: 11px; margin-bottom: 10px; font-family: monospace;">실제 DOM 업데이트</div>
      <div style="background: #1e293b; border-radius: 8px; padding: 14px; font-family: monospace; font-size: 13px; line-height: 2;">
        <div style="color: #60a5fa;">ul</div>
        <div style="color: #94a3b8; padding-left: 16px;">├── li: "사과" ✓</div>
        <div id="real-dom-update" style="color: #94a3b8; padding-left: 16px;">├── li: "바나나" ✓</div>
        <div style="color: #94a3b8; padding-left: 16px;">└── li: "포도" ✓</div>
      </div>
    </div>
  </div>
  <div style="margin-top: 16px; color: #94a3b8; font-size: 12px; font-family: monospace; background: #1e293b; border-radius: 6px; padding: 10px;">
    → "바나나"만 "망고"로 바꾸면 됨. 나머지 2개는 건드리지 않음.
  </div>
</div>
</div>

Virtual DOM 자체는 JavaScript 객체다.

```javascript
// Virtual DOM 실제로 이렇게 생긴 JS 객체
{
  type: "h1",
  props: { className: "title" },
  children: ["안녕"]
}
```

---

### 2.3 리플로우와 리페인트

실제 DOM을 건드리는 게 느린 이유는 **리플로우**와 **리페인트** 때문이다.

- **리플로우(Reflow)**: 요소의 크기나 위치가 바뀌면 브라우저가 새로운 레이아웃을 계산하고 화면을 다시 그린다. 주변 요소들까지 전부 다시 계산하기 때문에 비용이 크다.
- **리페인트(Repaint)**: 요소의 색상이나 테두리 등 외양만 바뀌면 해당 요소만 다시 그린다. 리플로우보다는 가볍다.

```
리플로우  >  리페인트  (리플로우가 훨씬 무거움)
```

Virtual DOM은 변경사항을 한 번에 모아서 최소한으로 실제 DOM에 반영하기 때문에 리플로우와 리페인트를 최소화할 수 있다.

> **핵심**: Virtual DOM의 진짜 장점은 단순히 속도가 아니다. 개발자가 실수로 DOM을 많이 건드리는 걸 막고, 바뀐 부분만 자동으로 최소한으로 반영해주는 것이다.

---

## 3. React 기초

### 3.1 컴포넌트

컴포넌트는 그냥 함수다. 단, **화면(JSX)을 반환하는 함수**다.

```javascript
function Button() {
    return <button>클릭</button>
}
```

컴포넌트는 레고 블록처럼 재사용할 수 있다.

```javascript
function App() {
    return (
        <div>
            <Button />
            <Button />
            <Button />
        </div>
    )
}
```

규칙은 딱 두 개다.

1. 함수 이름이 대문자로 시작해야 한다. (`Button` O, `button` X)
2. JSX를 반환해야 한다.

---

### 3.2 props

props는 컴포넌트에 데이터를 넘기는 방법이다. 함수 파라미터랑 똑같은 개념이다.

```javascript
// 넘기는 쪽
<Button text="클릭해줘" color="red" />
<Button text="제출" color="blue" />
<Button text="취소" color="gray" />

// 받는 쪽
function Button({ text, color }) {
    return (
        <button style={{ color: color }}>
            {text}
        </button>
    )
}
```

같은 컴포넌트인데 props만 달라서 다르게 보인다.

```
<Button text="클릭해줘" color="red" />  →  빨간 클릭해줘 버튼
<Button text="제출" color="blue" />     →  파란 제출 버튼
<Button text="취소" color="gray" />     →  회색 취소 버튼
```

---

### 3.3 useState

React에서 변수를 그냥 선언하면 값이 바뀌어도 화면이 안 바뀐다. React가 모르기 때문이다.

```javascript
// 이렇게 하면 화면 안 바뀜
function Counter() {
    let count = 0
    return (
        <button onClick={() => count++}>
            {count}
        </button>
    )
}
```

`useState`를 쓰면 값이 바뀔 때 React가 알아서 화면을 업데이트한다.

```javascript
function Counter() {
    const [count, setCount] = useState(0)
    //     ↑           ↑              ↑
    //   현재값     바꾸는함수       초기값

    return (
        <button onClick={() => setCount(count + 1)}>
            {count}
        </button>
    )
}
```

`setCount`를 호출하면 값을 바꾸고 동시에 React에게 "나 바뀌었어, 다시 그려줘"라고 알려준다.

아래는 useState가 없을 때와 있을 때의 차이를 직접 눌러볼 수 있는 데모다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 20px; font-family: monospace;">▶ useState 직접 체험</div>
  <div style="display: flex; gap: 24px; flex-wrap: wrap;">
    <div style="flex: 1; min-width: 200px; background: #1e293b; border-radius: 10px; padding: 20px; text-align: center;">
      <div style="color: #f87171; font-size: 12px; font-family: monospace; margin-bottom: 12px;">❌ 일반 변수 (화면 안 바뀜)</div>
      <div id="bad-count-display" style="font-size: 48px; font-weight: bold; color: #475569; margin: 16px 0;">0</div>
      <button onclick="badCount()" style="background: #374151; color: #9ca3af; border: none; border-radius: 8px; padding: 10px 24px; cursor: pointer; font-size: 14px;">클릭해도 소용없음</button>
      <div style="color: #475569; font-size: 11px; font-family: monospace; margin-top: 12px;">let count = 0<br>count++ ← React가 모름</div>
    </div>
    <div style="flex: 1; min-width: 200px; background: #1e293b; border-radius: 10px; padding: 20px; text-align: center;">
      <div style="color: #34d399; font-size: 12px; font-family: monospace; margin-bottom: 12px;">✅ useState (화면 바뀜)</div>
      <div id="good-count-display" style="font-size: 48px; font-weight: bold; color: #60a5fa; margin: 16px 0; transition: transform 0.1s;">0</div>
      <button onclick="goodCount()" style="background: #173DBA; color: white; border: none; border-radius: 8px; padding: 10px 24px; cursor: pointer; font-size: 14px;">클릭!</button>
      <button onclick="resetCount()" style="background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 8px; padding: 10px 16px; cursor: pointer; font-size: 14px; margin-left: 8px;">↺</button>
      <div style="color: #475569; font-size: 11px; font-family: monospace; margin-top: 12px;">const [count, setCount] = useState(0)<br>setCount(count + 1) ← React가 앎</div>
    </div>
  </div>
</div>
</div>

<script>
let badVar = 0;
let goodVar = 0;

function badCount() {
  badVar++;
  // 화면은 안 바뀜 - 의도적으로 업데이트 안 함
}

function goodCount() {
  goodVar++;
  const el = document.getElementById('good-count-display');
  el.textContent = goodVar;
  el.style.transform = 'scale(1.3)';
  el.style.color = goodVar % 2 === 0 ? '#60a5fa' : '#a78bfa';
  setTimeout(() => { el.style.transform = 'scale(1)'; }, 100);
}

function resetCount() {
  goodVar = 0;
  badVar = 0;
  document.getElementById('good-count-display').textContent = '0';
  document.getElementById('good-count-display').style.color = '#60a5fa';
}
</script>

```javascript
// 자주 쓰는 패턴들
const [count, setCount] = useState(0)        // 숫자
const [name, setName] = useState("")          // 문자열
const [isOpen, setIsOpen] = useState(false)  // boolean
const [list, setList] = useState([])          // 배열
```

주의할 점은 setter 함수로만 값을 바꿔야 한다는 것이다.

```javascript
count = count + 1    // ❌ React가 모름
setCount(count + 1)  // ✅ React가 알아서 화면 업데이트
```

---

### 3.4 useEffect

React 컴포넌트는 기본적으로 순수해야 한다. 같은 입력이면 항상 같은 출력이어야 한다는 뜻이다. 근데 서버에서 데이터 가져오기, 타이머, DOM 직접 건드리기 같은 건 실행할 때마다 결과가 달라질 수 있다. 이런 걸 **사이드 이펙트**라고 한다.

`useEffect`는 이런 사이드 이펙트를 넣는 공간이다.

```javascript
function App() {
    const [user, setUser] = useState(null)

    useEffect(() => {
        fetch("https://api.example.com/user")
            .then(res => res.json())
            .then(data => setUser(data))
    }, [])  // 처음 한 번만 실행

    return <div>{user?.name}</div>
}
```

의존성 배열(`[]`)에 따라 실행 시점이 달라진다.

```javascript
// 처음 한 번만 실행
useEffect(() => { ... }, [])

// 매 렌더링마다 실행
useEffect(() => { ... })

// count 바뀔 때만 실행
useEffect(() => { ... }, [count])
```

아래는 useEffect의 실행 타이밍을 눈으로 볼 수 있는 데모다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 16px; font-family: monospace;">▶ useEffect 실행 타이밍 시뮬레이션</div>
  <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;">
    <button onclick="simulateEffect('mount')" style="background: #1e3a5f; color: #60a5fa; border: 1px solid #2563eb; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">컴포넌트 마운트</button>
    <button onclick="simulateEffect('update')" style="background: #1a3a2a; color: #34d399; border: 1px solid #059669; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">상태 업데이트</button>
    <button onclick="simulateEffect('unmount')" style="background: #3a1a1a; color: #f87171; border: 1px solid #dc2626; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">컴포넌트 언마운트</button>
    <button onclick="clearEffectLog()" style="background: #1e293b; color: #64748b; border: 1px solid #334155; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">초기화</button>
  </div>
  <div id="effect-log" style="background: #020617; border-radius: 8px; padding: 16px; font-family: monospace; font-size: 12px; min-height: 120px; line-height: 1.8;">
    <span style="color: #475569;">// 버튼을 눌러서 useEffect 실행 타이밍을 확인하세요</span>
  </div>
</div>
</div>

<script>
let effectLogCount = 0;
function simulateEffect(type) {
  effectLogCount++;
  const log = document.getElementById('effect-log');
  const time = new Date().toLocaleTimeString('ko-KR', {hour12: false});
  let line = '';
  if (type === 'mount') {
    line = `<div style="color:#60a5fa">[${time}] 컴포넌트 마운트 → useEffect(fn, []) 실행 ← 처음 한 번만</div>`;
  } else if (type === 'update') {
    line = `<div style="color:#34d399">[${time}] 상태 변경 → useEffect(fn, [count]) 실행 ← count 바뀔 때마다</div>`;
    line += `<div style="color:#94a3b8; padding-left: 16px;">          → useEffect(fn, []) 실행 안 함 ← 의존성 없음</div>`;
  } else if (type === 'unmount') {
    line = `<div style="color:#f87171">[${time}] 컴포넌트 언마운트 → cleanup 함수 실행</div>`;
    line += `<div style="color:#94a3b8; padding-left: 16px;">return () => clearInterval(timer) ← 이런 정리 작업</div>`;
  }
  if (effectLogCount === 1) log.innerHTML = '';
  log.innerHTML += line;
}
function clearEffectLog() {
  effectLogCount = 0;
  document.getElementById('effect-log').innerHTML = '<span style="color: #475569;">// 버튼을 눌러서 useEffect 실행 타이밍을 확인하세요</span>';
}
</script>

> **핵심**: useEffect = React가 "화면 그리는 것 말고 다른 작업은 여기다 넣어줘" 하고 만든 공간

---

## 4. React 동작 방식

### 4.1 CSR이란

React는 기본적으로 **CSR(Client Side Rendering)** 방식이다.

```
서버 → index.html (텅 빔) + app.js (React 코드) 보내줌
↓
브라우저가 app.js 실행
↓
React가 DOM 만들기 시작
↓
화면 보여줌
```

HTML 파일은 사실상 비어있다.

```html
<body>
    <div id="root"></div>  <!-- 이게 전부 -->
    <script src="app.js"></script>
</body>
```

나머지는 다 React가 JavaScript로 DOM에 직접 집어넣는다.

---

### 4.2 SPA와 라우터

React는 **SPA(Single Page Application)** 방식이다. HTML 파일이 딱 한 장이다. 페이지 이동처럼 보이지만 실제로는 서버 요청 없이 컴포넌트만 갈아끼우는 것이다.

```javascript
function App() {
    return (
        <Routes>
            <Route path="/"        element={<Home />} />
            <Route path="/login"   element={<Login />} />
            <Route path="/profile" element={<Profile />} />
        </Routes>
    )
}
```

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 16px; font-family: monospace;">▶ SPA 라우팅 시뮬레이션</div>
  <div style="display: flex; gap: 8px; margin-bottom: 16px; background: #1e293b; border-radius: 8px; padding: 8px; flex-wrap: wrap;">
    <button onclick="simulateRoute('/')" style="background: #173DBA; color: white; border: none; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">/</button>
    <button onclick="simulateRoute('/login')" style="background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">/login</button>
    <button onclick="simulateRoute('/profile')" style="background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 8px 16px; cursor: pointer; font-size: 13px; font-family: monospace;">/profile</button>
  </div>
  <div style="background: #020617; border-radius: 8px; overflow: hidden; border: 1px solid #1e293b;">
    <div style="background: #1e293b; padding: 8px 16px; font-family: monospace; font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 8px;">
      <span style="color: #475569;">●</span>
      <span id="spa-url" style="color: #60a5fa;">localhost:3000/</span>
      <span style="color: #475569; font-size: 11px; margin-left: auto;">서버 요청 없음 ✓</span>
    </div>
    <div id="spa-content" style="padding: 32px; text-align: center; font-family: monospace; transition: all 0.3s; min-height: 120px; display: flex; align-items: center; justify-content: center;">
      <div>
        <div style="font-size: 32px; margin-bottom: 8px;">🏠</div>
        <div style="color: #60a5fa; font-size: 18px; font-weight: bold;">Home 컴포넌트</div>
        <div style="color: #475569; font-size: 12px; margin-top: 8px;">HTML은 그대로, 컴포넌트만 교체됨</div>
      </div>
    </div>
  </div>
  <div id="spa-log" style="margin-top: 12px; font-family: monospace; font-size: 11px; color: #475569;"></div>
</div>
</div>

<script>
const spaPages = {
  '/': { icon: '🏠', name: 'Home 컴포넌트', color: '#60a5fa' },
  '/login': { icon: '🔐', name: 'Login 컴포넌트', color: '#a78bfa' },
  '/profile': { icon: '👤', name: 'Profile 컴포넌트', color: '#34d399' },
};
let currentRoute = '/';
function simulateRoute(path) {
  if (path === currentRoute) return;
  currentRoute = path;
  const page = spaPages[path];
  document.getElementById('spa-url').textContent = 'localhost:3000' + path;
  const content = document.getElementById('spa-content');
  content.style.opacity = '0';
  setTimeout(() => {
    content.innerHTML = `<div>
      <div style="font-size: 32px; margin-bottom: 8px;">${page.icon}</div>
      <div style="color: ${page.color}; font-size: 18px; font-weight: bold;">${page.name}</div>
      <div style="color: #475569; font-size: 12px; margin-top: 8px;">HTML은 그대로, 컴포넌트만 교체됨</div>
    </div>`;
    content.style.opacity = '1';
  }, 150);
  document.getElementById('spa-log').textContent = `→ 서버 요청 없이 ${page.name}으로 교체완료`;
}
</script>

---

### 4.3 API 서버와의 관계

React(클라이언트)는 DB에 직접 접근할 수 없다. 보안 때문이다.

```
브라우저 → DB        ❌ (절대 안 됨)
브라우저 → API 서버 → DB  ✅
```

```javascript
useEffect(() => {
    fetch("https://api.myapp.com/users")  // API 서버에 요청
        .then(res => res.json())
        .then(data => setUsers(data))     // API 서버가 DB에서 가져온 데이터
}, [])
```

전체 구조는 이렇다.

```
React (브라우저)   → 화면 그리기, 라우팅, API 요청 보내기
API 서버          → 인증 확인, DB에서 데이터 가져오기
DB               → 데이터 저장
```

---

### 4.4 클라이언트 보안 한계

React로 만든 app.js는 누구나 다운로드해서 볼 수 있다. 모든 컴포넌트 코드, 라우터 구조가 다 보인다. 그래서 클라이언트 코드에는 중요한 정보를 절대 넣으면 안 된다.

```
❌ 클라이언트에 두면 안 되는 것
→ DB 접근 코드
→ 비밀키 (API key)
→ 비즈니스 로직
→ 결제 로직

✅ 서버에만 있어야 하는 것
→ 위에 있는 것들 전부
```

로그인한 사람만 볼 수 있는 페이지도 클라이언트에서만 막으면 안 된다. 반드시 서버에서도 토큰 검증을 해야 한다.

```
클라이언트 토큰 검사  →  UX용 (눈속임 가능)
서버 토큰 검증       →  진짜 보안
```

> **핵심**: 클라이언트 코드는 다 공개된다고 생각하고, 중요한 건 무조건 서버에 둬야 한다.

---

## 5. 더 나아가기

### 5.1 SSR과 Next.js

CSR의 단점은 첫 로딩이 느리고 SEO가 안 좋다는 것이다. HTML이 텅 비어있기 때문에 검색엔진이 내용을 읽지 못한다.

**SSR(Server Side Rendering)** 은 서버에서 HTML을 미리 만들어서 보내주는 방식이다. Next.js가 대표적이다.

```
CSR: 브라우저가 JS 실행해서 DOM 만듦 (느림)
SSR: 서버가 HTML 미리 만들어서 보내줌 (빠름)
```

Next.js는 React 기반 프레임워크다.

```
React   =  엔진
Next.js =  엔진 + 차체 + 편의기능 다 합친 완성차
```

React를 모르면 Next.js를 쓸 수 없다. React가 근본이다.

---

### 5.2 WebAssembly

JavaScript는 웹 브라우저에서 사용할 수 있는 사실상 유일한 언어다. 다른 언어로 짜도 결국 브라우저가 읽으려면 JS로 변환해야 한다.

**WebAssembly**는 이 한계를 넘으려는 시도다. C, C++, Rust로 작성된 프로그램을 브라우저에서 돌릴 수 있게 해준다.

단, DOM을 직접 제어할 수 없기 때문에 JavaScript를 완전히 대체하는 건 아니다. JavaScript와 상호 보완적인 관계로, 고성능이 필요한 부분은 WebAssembly, 화면 제어는 JavaScript가 담당하는 방식으로 쓰인다.

> Flash → WebAssembly로 세대교체가 된 것이지, JS 대체가 아니다.

---

## 6. 실전: MPA → React 리팩터링 계획

이론을 익힌 직후 실제 프로젝트를 React로 리팩터링하면서 결정한 것들을 정리한다.

프로젝트는 로그인, 통계, 질의응답(AI 챗봇), 문서관리, 회원관리로 구성된 내부 관리자 웹앱이다. 현재는 HTML 파일 6개가 각각 독립적으로 존재하는 MPA 구조다.

---

### 6.1 MPA vs SPA — 왜 바꾸는가

현재 구조:

```
index.html     ← 로그인
statistics.html ← 통계
qa.html        ← 채팅
members.html   ← 회원관리
documents.html ← 문서관리
```

페이지를 이동할 때마다 서버에서 새 HTML을 통째로 받아온다. 화면이 깜빡이고 전체 새로고침이 발생한다.

React SPA로 바꾸면:

```
HTML 파일은 index.html 하나

/            → Login 컴포넌트
/statistics  → Statistics 컴포넌트
/qa          → QA 컴포넌트
```

HTML은 그대로, 컴포넌트만 교체되기 때문에 깜빡임이 없다.

---

### 6.2 React Router — 필수인가 선택인가

React에는 기본 라우팅 기능이 없다. 서드파티 라이브러리인 **React Router**를 따로 설치해야 한다.

```bash
npm install react-router-dom
```

React Router 없이 `useState`만으로 페이지 전환을 구현할 수도 있다.

```jsx
// useState 방식
const [page, setPage] = useState('login')
if (page === 'login') return <Login />
if (page === 'statistics') return <Statistics />
```

하지만 이 방식은 URL이 바뀌지 않아서 뒤로가기, 새로고침, 링크 공유가 모두 안 된다. 실제 서비스라면 사용자 입장에서 망가진 웹사이트처럼 느껴진다.

> 결론: 학습용이면 선택, 실제 배포 서비스라면 사실상 필수.

---

### 6.3 기술 스택 결정

| 항목 | 선택 | 이유 |
|---|---|---|
| 빌드 도구 | Vite | 빠른 개발 서버 |
| 라우팅 | React Router v6 | 페이지 이동 처리 |
| 상태 관리 | useState + useContext | 규모가 작아 Redux 불필요 |
| 차트 | react-chartjs-2 | 기존 Chart.js를 React 방식으로 래핑 |
| CSS | 기존 파일 그대로 | 스타일 재작업 없이 이식 |

Next.js는 고려하지 않았다. 이유는 두 가지다.

1. 로그인이 필요한 내부 서비스라 SEO가 필요 없다.
2. React를 익히는 단계에서 Next.js를 같이 배우면 헷갈린다.

---

### 6.4 폴더 구조

기존 파일 구조를 최대한 유지하는 방향으로 잡았다.

```
기존                       React
──────────────────────────────────────
index.html + index.js  →  pages/LoginPage.jsx
statistics.html + js   →  pages/StatisticsPage.jsx
qa.html + js           →  pages/QAPage.jsx
documents.html + js    →  pages/DocumentsPage.jsx
members.html + js      →  pages/MembersPage.jsx
js/common.js           →  context/AuthContext.jsx
css/*.css              →  public/css/*.css (그대로)
img/                   →  public/img/ (그대로)
```

최종 구조:

```
src/
├── main.jsx
├── App.jsx
├── context/
│   └── AuthContext.jsx   ← common.js 역할
└── pages/
    ├── LoginPage.jsx
    ├── StatisticsPage.jsx
    ├── QAPage.jsx
    ├── DocumentsPage.jsx
    └── MembersPage.jsx

public/
├── css/                  ← 기존 그대로
├── img/                  ← 기존 그대로
└── font/                 ← 기존 그대로
```

`components/`, `hooks/` 같은 폴더는 필요할 때 추가하기로 했다. 처음부터 과도하게 구조를 나누면 오히려 복잡해진다.

---

### 6.5 인증 처리 — 중복 코드 제거

현재 가장 큰 문제는 인증 코드가 모든 페이지에 복붙되어 있다는 것이다.

```js
// statistics.js, members.js, documents.js 전부 첫 줄이 이것
if (!localStorage.getItem('iai_user')) location.href = 'index.html';
function logout() { localStorage.removeItem('iai_user'); location.href = 'index.html'; }
```

React에서는 `AuthContext` 하나로 해결된다.

```jsx
// context/AuthContext.jsx
const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('iai_user')
    return saved ? JSON.parse(saved) : null
  })

  function login(userData) {
    localStorage.setItem('iai_user', JSON.stringify(userData))
    setUser(userData)
  }

  function logout() {
    localStorage.removeItem('iai_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
```

그리고 로그인이 필요한 페이지는 `ProtectedRoute`로 감싼다.

```jsx
// 로그인 안 했으면 / 로 리다이렉트
function ProtectedRoute({ children }) {
  const { user } = useContext(AuthContext)
  if (!user) return <Navigate to="/" />
  return children
}

// App.jsx 라우터 설정
<Routes>
  <Route path="/"           element={<LoginPage />} />
  <Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
  <Route path="/qa"         element={<ProtectedRoute><QAPage /></ProtectedRoute>} />
</Routes>
```

---

### 6.6 핵심 변환 패턴

**페이지 이동:**

```js
// 기존
location.href = 'statistics.html'

// React
const navigate = useNavigate()
navigate('/statistics')
```

**DOM 조작 → 상태:**

```js
// 기존
document.getElementById('errMsg').style.display = 'block'

// React
const [showError, setShowError] = useState(false)
// JSX: {showError && <p className="error-msg">...</p>}
```

**링크:**

```html
<!-- 기존 -->
<a href="members.html">회원관리</a>

<!-- React -->
<Link to="/members">회원관리</Link>
```

**class 속성:**

```html
<!-- 기존 HTML -->
<div class="login-card">

<!-- JSX -->
<div className="login-card">
```

CSS 파일 자체는 손댈 필요 없다.

---

### 6.7 AI 채팅 — 스트리밍과 세션 처리

QA 페이지는 AI 챗봇 인터페이스다. 일반 API 요청과 다르게 두 가지를 고려해야 한다.

**스트리밍 응답 (SSE)**

AI 응답을 한 번에 받으면 응답이 완성될 때까지 화면이 멈춰 보인다. 그래서 글자가 하나씩 타이핑되듯 나오는 스트리밍 방식을 쓴다.

```jsx
async function sendMessage(text) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message: text, session_id: sessionId })
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const token = decoder.decode(value)
    setMessage(prev => prev + token)  // 글자 하나씩 추가
  }
}
```

**세션 처리**

매 요청마다 대화 내역 전체를 보내는 방식도 있지만, 백엔드(FastAPI + LangChain)가 세션을 관리하기로 했다.

```
첫 대화 → 서버가 session_id 발급
이후 요청 → session_id만 보내면 됨
서버가 session_id로 대화 맥락 찾아서 처리
```

프론트는 `session_id`만 저장하고, 화면에 보여줄 메시지 목록은 따로 `useState`로 관리한다.

```
서버: 대화 맥락 관리 (AI가 기억하는 용도)
프론트: 화면에 표시할 메시지 목록 (사용자가 보는 용도)
```

---

### 6.8 API 연동 순서

현재 모든 데이터는 JS 파일 안에 하드코딩되어 있다. 백엔드는 FastAPI로 개발 중이다.

작업 순서를 이렇게 잡았다:

```
1. 더미 데이터 그대로 React 리팩터링 완성
       ↓
2. API 명세 작성 (화면 기준으로)
       ↓
3. 백엔드 API 완성
       ↓
4. 더미 데이터 → fetch로 교체
```

화면이 완성된 상태에서 API를 연동하면 뭘 만들어야 할지 명확하다. 그리고 더미 데이터를 `fetch`로 교체하는 작업은 어렵지 않다.

`.env` 파일로 API 주소를 관리하고, CORS 설정은 FastAPI 쪽에서 처리한다.

```
개발: VITE_API_URL=http://localhost:8000
배포: VITE_API_URL=https://api.iai.com
```

---

## 정리

이 글에서 다룬 핵심 내용을 한 눈에 정리한다.

| 개념 | 한 줄 요약 |
|---|---|
| **DOM** | 브라우저가 HTML을 읽고 메모리에 만든 트리 구조. JS가 건드리는 대상 |
| **Virtual DOM** | 실제 DOM 건드리기 전에 메모리에서 계산하고, 바뀐 부분만 반영 |
| **컴포넌트** | JSX를 반환하는 함수. 레고 블록처럼 조합해서 화면을 만든다 |
| **props** | 컴포넌트에 데이터를 넘기는 방법. 함수 파라미터와 같은 개념 |
| **useState** | React가 알아야 화면이 바뀐다. setter 함수로만 값을 바꿔야 한다 |
| **useEffect** | 서버 요청, 타이머 같은 사이드 이펙트를 넣는 공간 |
| **CSR / SPA** | JS가 DOM을 직접 만든다. HTML 파일은 하나, 컴포넌트만 교체 |
| **클라이언트 보안** | 클라이언트 코드는 전부 공개된다. 중요한 건 서버에만 |
| **SSR / Next.js** | 서버에서 HTML을 미리 만들어 보내는 방식. SEO가 필요하면 고려 |

MPA → React 리팩터링에서 얻은 교훈:

- **인증 로직은 Context 하나로 모아라.** 복붙된 코드가 버그의 온상이다.
- **폴더 구조는 필요할 때 추가하라.** 처음부터 `hooks/`, `components/` 다 만들면 오히려 복잡해진다.
- **더미 데이터로 화면 먼저 완성하고, API는 나중에 연동하라.** 화면이 있어야 API 명세도 명확해진다.
- **React Router는 실제 배포 서비스라면 사실상 필수다.** URL이 바뀌지 않으면 뒤로가기, 새로고침, 링크 공유가 전부 망가진다.
