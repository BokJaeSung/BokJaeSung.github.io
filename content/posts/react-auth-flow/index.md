---
title: "React.02 Authentication Flow"
date: 2026-03-31T13:00:00+09:00
tags: ['react', 'auth', 'context', 'axios', 'frontend', 'javascript']
cover:
  image: 'images/cover.jpg'
  alt: 'React.02 Authentication Flow'
  relative: true
summary: 'From api.js to Context API — a deep dive into the authentication flow in a real React project.'
---

실제 프로젝트 코드를 뜯어보면서 서버 통신 구조부터 Context API, 토큰 기반 인증까지 흐름을 정리했다.

---

## 1. 서버 통신 구조

### api.js란

`api.js`는 axios 인스턴스를 하나 만들어서 **모든 요청에 공통으로 적용될 설정**을 담는 파일이다.

```js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/v1',
})
```

여기서 만든 `api` 객체는 `axios` 원본과 **별개**다. `axios.create()`로 새 인스턴스를 만든 것이기 때문에, 이 객체에 붙인 인터셉터는 원본 `axios`에는 영향을 미치지 않는다.

### services 레이어와의 관계

```
api.js  ←  services/*.js  ←  컴포넌트
```

`services` 파일들은 `api.js`에서 만든 인스턴스를 `import`해서 **어떤 엔드포인트를 어떤 파라미터로 호출할지**만 정의한다.

```js
import api from '../api'

export const getDocuments = (params) =>
  api.get('/documents', { params })
```

| 관심사 | 담당 |
|---|---|
| 토큰 관리, 재시도, baseURL | `api.js` |
| "문서 목록은 GET /documents" | `services/documents.js` |
| "버튼 누르면 API 호출" | 컴포넌트 |

### axios 인터셉터 동작 원리

`getDocuments()`를 호출하면 자동으로 인터셉터를 통과한다. `api` 인스턴스를 쓰기 때문에 자동으로 끼어드는 것이다. 만약 services에서 `axios`를 직접 import하면 인터셉터를 통과하지 않는다.

특히 refresh 요청 시 원본 `axios`를 직접 쓰는 이유가 있다. `api` 인스턴스를 쓰면 refresh 요청도 인터셉터를 타게 되고, 거기서 또 401이 나면 refresh → 401 → refresh... 무한루프가 생기기 때문이다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 16px;">▶ 인터셉터 흐름</div>
  <div id="interceptor-flow" style="font-size: 14px; line-height: 2.2;">
    <div class="iflow-node" style="color: #60a5fa; opacity: 0; transition: opacity 0.4s;" data-delay="0">getDocuments() 호출</div>
    <div class="iflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="200">↓</div>
    <div class="iflow-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s;" data-delay="400">api.get('/documents') 실행</div>
    <div class="iflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="600">↓</div>
    <div class="iflow-node" style="color: #fbbf24; opacity: 0; transition: opacity 0.4s;" data-delay="800">요청 인터셉터 <span style="color:#94a3b8">← Authorization 헤더 자동 삽입</span></div>
    <div class="iflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="1000">↓</div>
    <div class="iflow-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s;" data-delay="1200">HTTP 요청 → 서버</div>
    <div class="iflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="1400">↓</div>
    <div class="iflow-node" style="color: #fbbf24; opacity: 0; transition: opacity 0.4s;" data-delay="1600">응답 인터셉터 <span style="color:#94a3b8">← 401이면 refresh, 정상이면 통과</span></div>
    <div class="iflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="1800">↓</div>
    <div class="iflow-node" style="color: #60a5fa; opacity: 0; transition: opacity 0.4s;" data-delay="2000">결과 반환</div>
  </div>
  <button onclick="replayInterceptorFlow()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateInterceptorFlow() {
  const nodes = document.querySelectorAll('.iflow-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayInterceptorFlow() { animateInterceptorFlow(); }
const iflowObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateInterceptorFlow(); iflowObserver.disconnect(); }
}, { threshold: 0.5 });
const iflowEl = document.getElementById('interceptor-flow');
if (iflowEl) iflowObserver.observe(iflowEl);
</script>

---

## 2. 토큰 기반 인증

### access_token vs refresh_token

로그인하면 서버가 토큰을 **2개** 준다.

| 토큰 | 역할 | 유효기간 |
|---|---|---|
| `access_token` | API 요청 시 신분증 | 짧음 (30분~1시간) |
| `refresh_token` | access_token 재발급용 | 김 (2주~한달) |

access_token을 길게 쓰면 탈취당했을 때 오랫동안 악용 가능하다. 그래서 짧게 설정하고, 만료되면 refresh_token으로 조용히 재발급한다. 사용자 입장에서는 아무것도 모르고 계속 쓰는 것처럼 보인다.

### 토큰 자동 갱신 흐름

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 16px;">▶ 401 자동 갱신 흐름</div>
  <div id="refresh-flow" style="font-size: 14px; line-height: 2.2;">
    <div class="rflow-node" style="color: #60a5fa; opacity: 0; transition: opacity 0.4s;" data-delay="0">API 요청</div>
    <div class="rflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="200">↓</div>
    <div class="rflow-node" style="color: #f87171; opacity: 0; transition: opacity 0.4s;" data-delay="400">401 응답 <span style="color:#94a3b8">← access_token 만료</span></div>
    <div class="rflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="600">↓</div>
    <div class="rflow-node" style="color: #fbbf24; opacity: 0; transition: opacity 0.4s;" data-delay="800">refresh_token으로 새 access_token 요청 <span style="color:#94a3b8">← axios 원본으로 직접 요청</span></div>
    <div class="rflow-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="1000">↓</div>
    <div class="rflow-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s;" data-delay="1200">성공 → 새 access_token 저장 후 원래 요청 재시도</div>
    <div class="rflow-node" style="color: #f87171; opacity: 0; transition: opacity 0.4s;" data-delay="1200">실패 → refresh_token도 만료 → 로그아웃</div>
  </div>
  <button onclick="replayRefreshFlow()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateRefreshFlow() {
  const nodes = document.querySelectorAll('.rflow-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayRefreshFlow() { animateRefreshFlow(); }
const rflowObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateRefreshFlow(); rflowObserver.disconnect(); }
}, { threshold: 0.5 });
const rflowEl = document.getElementById('refresh-flow');
if (rflowEl) rflowObserver.observe(rflowEl);
</script>

### localStorage 저장 위치

localStorage는 **디스크**에 저장된다. 브라우저를 껐다 켜도, 컴퓨터를 재시작해도 남아있는 이유다.

| 저장소 | 위치 | 브라우저 꺼도 남음? |
|---|---|---|
| localStorage | 디스크 | ✅ |
| sessionStorage | 메모리 | ❌ |
| 변수 (`const token`) | 메모리 | ❌ |

---

## 3. Context API

### 전역변수 대신 Context를 쓰는 이유

전역변수로도 값을 공유할 수 있지만 문제가 있다.

```js
let user = { name: '홍길동' }
user = null  // 로그아웃해도 화면은 그대로 '홍길동' 표시 중
```

React는 `useState`로 관리하는 값이 바뀔 때만 리렌더링한다. 전역변수는 바뀌어도 React가 모른다. Context는 **useState + 전역 공유** 두 가지를 같이 해결한다.

### Context 객체란 무엇인가

`createContext()`를 호출하면 메모리에 **Context 객체**가 할당된다. 이 객체 안에는 `Provider`와 `Consumer` 두 멤버가 들어있다.

```js
const AuthContext = createContext()
// AuthContext = { Provider, Consumer }
```

`Provider`는 값을 하위 컴포넌트에 공급하는 컴포넌트고, `Consumer`는 값을 받는 옛날 방식이다. 현재는 `Consumer` 대신 `useContext` 훅을 쓴다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">▶ createContext() 실행 시 메모리 구조</div>
  <div id="context-obj" style="font-size: 14px; line-height: 2.2;">
    <div class="ctx-node" style="color: #60a5fa; opacity: 0; transition: opacity 0.4s;" data-delay="0">createContext() 호출</div>
    <div class="ctx-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="300">↓ 메모리에 객체 할당</div>
    <div class="ctx-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.5s;" data-delay="700">AuthContext <span style="color:#475569">{</span></div>
    <div class="ctx-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="1000">Provider, <span style="color:#94a3b8">← 값을 하위에 공급하는 컴포넌트</span></div>
    <div class="ctx-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="1300">Consumer, <span style="color:#475569">← 옛날 방식 (useContext로 대체됨)</span></div>
    <div class="ctx-node" style="color: #475569; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="1600">_currentValue  <span style="color:#475569">← 현재 value 참조 (내부용)</span></div>
    <div class="ctx-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s;" data-delay="1900"><span style="color:#475569">}</span></div>
  </div>
  <button onclick="replayContextObj()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateContextObj() {
  const nodes = document.querySelectorAll('.ctx-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayContextObj() { animateContextObj(); }
const ctxObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateContextObj(); ctxObserver.disconnect(); }
}, { threshold: 0.5 });
const ctxEl = document.getElementById('context-obj');
if (ctxEl) ctxObserver.observe(ctxEl);
</script>

### Provider와 useContext의 관계

`Provider`는 `value` props로 넘긴 값을 **태그 안에 있는 모든 컴포넌트**에 공급한다. `useContext`는 그 공간에서 값을 꺼내는 열쇠다. Provider 밖에서 `useContext`를 쓰면 값이 없어서 `undefined`가 반환된다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">▶ Provider 범위와 useContext 접근</div>
  <div id="provider-scope" style="font-size: 14px; line-height: 2.2;">
    <div class="scope-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s;" data-delay="0">&lt;AuthContext.Provider value=&#123;&#123; user, login, logout &#125;&#125;&gt;</div>
    <div class="scope-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="400">  &lt;LoginPage /&gt;      <span style="color:#94a3b8">← useAuth() 가능 ✅</span></div>
    <div class="scope-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="700">  &lt;StatisticsPage /&gt; <span style="color:#94a3b8">← useAuth() 가능 ✅</span></div>
    <div class="scope-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="1000">    &lt;Navbar /&gt;       <span style="color:#94a3b8">← 몇 단계 깊어도 가능 ✅</span></div>
    <div class="scope-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s;" data-delay="1300">&lt;/AuthContext.Provider&gt;</div>
    <div class="scope-node" style="color: #f87171; opacity: 0; transition: opacity 0.4s;" data-delay="1700">&lt;OutsidePage /&gt;    <span style="color:#94a3b8">← Provider 밖 → undefined ❌</span></div>
  </div>
  <button onclick="replayProviderScope()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateProviderScope() {
  const nodes = document.querySelectorAll('.scope-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayProviderScope() { animateProviderScope(); }
const scopeObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateProviderScope(); scopeObserver.disconnect(); }
}, { threshold: 0.5 });
const scopeEl = document.getElementById('provider-scope');
if (scopeEl) scopeObserver.observe(scopeEl);
</script>

### props drilling과 Context의 차이

**props drilling** — 중간 컴포넌트들이 값을 사용하지도 않으면서 전달만 해야 한다.

```
App (user 보유)
 ↓ user 전달
Layout (안 씀, 전달만)
 ↓ user 전달
Header (안 씀, 전달만)
 ↓ user 전달
UserIcon (여기서 드디어 사용)
```

**Context** — 필요한 컴포넌트가 직접 꺼낸다.

```
App
└── UserIcon → useAuth()로 바로 꺼냄
```

---

## 4. AuthProvider 동작 원리

### 구조 시각화

```
main.jsx
└── App
    └── BrowserRouter
        └── AuthProvider  ← 커스텀 컴포넌트 (useState, login, logout 보유)
            └── AuthContext.Provider  ← value를 하위에 공급
                └── Routes
                    ├── LoginPage
                    ├── StatisticsPage
                    ├── QAPage
                    ├── DocumentsPage
                    └── MembersPage
```

`AuthProvider`는 단순히 `AuthContext.Provider`를 감싸서 로직을 추가한 커스텀 컴포넌트다. `useAuth`가 `useContext`를 감싼 것과 같은 패턴이다.

### useState와 localStorage 연동

```js
const [user, setUser] = useState(() => {
  const saved = localStorage.getItem('iai_user')
  return saved ? JSON.parse(saved) : null
})
```

앱이 처음 로드될 때 localStorage에서 유저 정보를 꺼내 `useState`에 올린다. localStorage는 **문자열만** 저장 가능하기 때문에 저장 시 `JSON.stringify`, 꺼낼 때 `JSON.parse`를 사용한다.

### 새로고침해도 로그인 유지되는 이유

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">▶ 새로고침 시 상태 복원 흐름</div>
  <div id="refresh-restore" style="font-size: 14px; line-height: 2.2;">
    <div class="restore-node" style="color: #f87171; opacity: 0; transition: opacity 0.4s;" data-delay="0">새로고침</div>
    <div class="restore-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="300">↓</div>
    <div class="restore-node" style="color: #f87171; opacity: 0; transition: opacity 0.4s;" data-delay="600">메모리 초기화 <span style="color:#94a3b8">← Context, useState 전부 사라짐</span></div>
    <div class="restore-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="900">↓</div>
    <div class="restore-node" style="color: #fbbf24; opacity: 0; transition: opacity 0.4s;" data-delay="1200">AuthProvider 마운트 → useState 초기화 실행</div>
    <div class="restore-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="1500">↓</div>
    <div class="restore-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s;" data-delay="1800">localStorage.getItem('iai_user') <span style="color:#94a3b8">← 디스크에서 꺼냄</span></div>
    <div class="restore-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="2100">↓</div>
    <div class="restore-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s;" data-delay="2400">user 복원 → 로그인 상태 유지 ✅</div>
  </div>
  <button onclick="replayRefreshRestore()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateRefreshRestore() {
  const nodes = document.querySelectorAll('.restore-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayRefreshRestore() { animateRefreshRestore(); }
const restoreObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateRefreshRestore(); restoreObserver.disconnect(); }
}, { threshold: 0.5 });
const restoreEl = document.getElementById('refresh-restore');
if (restoreEl) restoreObserver.observe(restoreEl);
</script>

### login / logout 함수 흐름

`setUser`는 외부에 노출하지 않고 `login`/`logout`을 통해서만 간접적으로 바꿀 수 있다.

```js
// value에 setUser 안 넣음 → 직접 수정 불가
<AuthContext.Provider value={{ user, login, logout }}>

// login() 호출 시
login()  → setUser(userData) + localStorage 저장
logout() → setUser(null) + localStorage 삭제
```

아무 컴포넌트나 `user`를 직접 못 바꾸게 막는 의도적인 설계다.

### Context 메모리 구조

Context 객체 자체는 실제 데이터를 들고 있지 않다. 실제 데이터는 `AuthProvider`의 `useState` 안에 있고, Context는 그것을 **가리키는 참조**만 보관한다.

<div style="margin: 32px 0;">
<div style="background: #0f172a; border-radius: 12px; padding: 24px; font-family: monospace;">
  <div style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">▶ 메모리 구조 — Context vs AuthProvider</div>
  <div id="mem-structure" style="font-size: 14px; line-height: 2.2;">
    <div class="mem-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s;" data-delay="0">메모리</div>
    <div class="mem-node" style="color: #a78bfa; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="300">├── AuthContext 객체 <span style="color:#475569">← createContext()로 할당</span></div>
    <div class="mem-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="600">│     └── _currentValue → <span style="color:#fbbf24">참조 (포인터)</span></div>
    <div class="mem-node" style="color: #94a3b8; opacity: 0; transition: opacity 0.4s; padding-left: 72px;" data-delay="900">│                   ↓ 가리킴</div>
    <div class="mem-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 24px;" data-delay="1200">└── AuthProvider 실행 공간 <span style="color:#475569">← 렌더링될 때 생성</span></div>
    <div class="mem-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="1500">      ├── user = &#123; name: '홍길동', ... &#125; <span style="color:#475569">← 실제 데이터</span></div>
    <div class="mem-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="1800">      ├── login = async function() &#123;...&#125; <span style="color:#475569">← 실제 함수</span></div>
    <div class="mem-node" style="color: #34d399; opacity: 0; transition: opacity 0.4s; padding-left: 48px;" data-delay="2100">      └── logout = async function() &#123;...&#125; <span style="color:#475569">← 실제 함수</span></div>
  </div>
  <button onclick="replayMemStructure()" style="margin-top: 16px; background: #1e293b; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px;">↺ 다시 보기</button>
</div>
</div>

<script>
function animateMemStructure() {
  const nodes = document.querySelectorAll('.mem-node');
  nodes.forEach(node => {
    node.style.opacity = '0';
    const delay = parseInt(node.getAttribute('data-delay'));
    setTimeout(() => { node.style.opacity = '1'; }, delay);
  });
}
function replayMemStructure() { animateMemStructure(); }
const memObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) { animateMemStructure(); memObserver.disconnect(); }
}, { threshold: 0.5 });
const memEl = document.getElementById('mem-structure');
if (memEl) memObserver.observe(memEl);
</script>

### 생명주기

```
브라우저에서 앱 열림
    ↓
AuthProvider 마운트 → Context 공간 생성, user 초기화
    ↓
앱 사용 중 (페이지 이동해도 AuthProvider 유지)
    ↓
브라우저 탭 닫힘 / 새로고침
    ↓
AuthProvider 언마운트 → Context 소멸 (메모리에서 사라짐)
```

페이지 이동 시에도 `AuthProvider`는 유지되기 때문에 로그인 상태가 끊기지 않는다.

---

## 5. ProtectedRoute

```js
export default function ProtectedRoute({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/" replace />
  return children
}
```

```jsx
<Route path="/statistics" element={<ProtectedRoute><StatisticsPage /></ProtectedRoute>} />
```

`/statistics`에 접근하면 `ProtectedRoute`가 먼저 실행된다. `user`가 없으면 `/`로 강제 이동, 있으면 `StatisticsPage`를 렌더링한다.

단, 이건 **UI를 막는 것**일 뿐이다. `localStorage`를 직접 조작하면 우회 가능하다. 진짜 보안은 서버 API에서 토큰을 검증하는 것이다.

---

## 6. 자주 헷갈리는 것들

### AuthContext vs AuthProvider — 뭐가 다른가

둘 다 "Context"라는 단어를 쓰니까 헷갈리기 쉽다.

| | AuthContext | AuthProvider |
|---|---|---|
| 만드는 것 | `createContext()` | 직접 작성한 컴포넌트 |
| 역할 | 빈 공간 (그릇) | 공간에 값을 채우고 관리 |
| 데이터 보유 | ❌ (참조만 있음) | ✅ (실제 데이터) |
| 없애면 | 값을 꺼낼 공간 없음 | 실제 데이터 없음 |

`AuthContext`만 있으면 빈 그릇이고, `AuthProvider`가 있어야 그릇에 값이 채워진다.

### useAuth vs useContext — 왜 두 개인가

```js
// 이 둘은 완전히 같은 동작
const { user } = useContext(AuthContext)  // 매번 AuthContext도 import해야 함
const { user } = useAuth()               // 한 줄로 끝
```

`useAuth`는 `useContext(AuthContext)`를 **이름 붙여서 포장**한 것뿐이다. 내부적으로 `useContext`를 호출한다.

### setUser는 Context를 수정하는가

아니다. `setUser`는 `AuthProvider`의 `useState`를 수정한다. Context는 그 결과를 자동으로 반영할 뿐이다.

```
setUser(newUser)
    ↓
AuthProvider의 useState 업데이트  ← 여기를 수정
    ↓
Context의 참조가 새 값을 가리킴   ← 자동으로 따라감
    ↓
하위 컴포넌트 리렌더링
```

Context를 "직접 수정"하는 API는 없다. 항상 `useState`를 통해 간접적으로 반영된다.

### Provider 안에 있어야만 useAuth()를 쓸 수 있는가

그렇다. `useContext`는 가장 가까운 상위 Provider에서 값을 가져오기 때문이다. Provider 밖에서 호출하면 `undefined`가 반환된다.

다만 현재 코드에서는 `AuthProvider`가 `Routes` 전체를 감싸고 있기 때문에 모든 페이지에서 `useAuth()`가 가능하다.

### login/logout은 함수인데 어떻게 Context에서 꺼내 쓰나

함수 자체가 전달되는 게 아니라 **함수를 가리키는 참조(포인터)**가 전달된다.

```js
value={{ user, login, logout }}
// login의 메모리 주소가 value에 들어감
```

자식 컴포넌트가 `login()`을 호출하면 → 참조를 따라가서 → `AuthProvider` 안의 함수가 실행된다. `setUser`도 그 함수 안에 있으므로 정상 동작한다.

### ProtectedRoute는 진짜 보안인가

아니다. UI를 막는 것일 뿐이다.

```js
// 브라우저 콘솔에서
localStorage.setItem('iai_user', '{"name":"해커"}')
// 새로고침하면 로그인됨
```

진짜 보안은 서버에서 토큰을 검증하는 것이다. 프론트엔드의 ProtectedRoute는 **로그인 안 한 사용자에게 빈 페이지를 보여주지 않기 위한 UX 처리**다.

---

## 7. 프론트엔드 보안 현실

### JSX 코드 노출 가능성

브라우저 개발자도구 → Sources 탭에서 번들된 JS를 볼 수 있다. `npm run dev`로 개발 중이면 원본 코드가 그대로 노출된다.

```
npm run dev    → 난독화 X (개발용)
npm run build  → 난독화 O (배포용)
```

### 난독화란

빌드 시 자동으로 적용된다. 변수명을 `a`, `b`, `c`로 축약하고 공백을 제거해서 읽기 어렵게 만든다. 하지만 브라우저가 실행할 수 있는 JS여야 하므로 완벽한 방어는 아니다.

난독화는 **귀찮게 만드는 것**이지 막는 것이 아니다. 민감한 로직(DB 접근, 검증 등)은 반드시 서버에 둬야 한다.
