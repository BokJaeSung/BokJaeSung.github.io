---
title: "React.02 Authentication Flow"
date: 2026-04-01T12:00:00+09:00
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

`getDocuments()`를 호출하면 자동으로 인터셉터를 통과한다.

```
getDocuments() 호출
    ↓
api.get('/documents') 실행
    ↓
요청 인터셉터 → 토큰 헤더 자동 삽입
    ↓
HTTP 요청 → 서버
    ↓
응답 인터셉터 → 401이면 refresh 시도, 정상이면 통과
    ↓
결과 반환
```

`api` 인스턴스를 쓰기 때문에 자동으로 끼어드는 것이다. 만약 services에서 `axios`를 직접 import하면 인터셉터를 통과하지 않는다.

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

```
API 요청 → 401 응답 (access_token 만료)
    ↓
refresh_token으로 새 access_token 요청
    ↓
성공 → 새 access_token 저장 후 원래 요청 재시도
실패 → refresh_token도 만료 → 로그아웃
```

refresh 요청 시 원본 `axios`를 직접 쓰는 이유가 있다. `api` 인스턴스를 쓰면 refresh 요청도 인터셉터를 타게 되고, 거기서 또 401이 나면 refresh → 401 → refresh... 무한루프가 생기기 때문이다.

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

React는 `useState`로 관리하는 값이 바뀔 때만 리렌더링한다. 전역변수는 바뀌어도 React가 모른다.

Context는 **useState + 전역 공유** 두 가지를 같이 해결한다.

### createContext / Provider / useContext 관계

```
createContext()  →  빈 공간(Context 객체) 생성
Provider         →  그 공간에 값 채움 + 하위 컴포넌트에 공급
useContext       →  그 공간에서 값 꺼냄
```

`createContext()`가 반환하는 Context 객체 안에는 `Provider`와 `Consumer`가 있다. `Provider`는 `value` props로 넘긴 값을 하위 컴포넌트 전체에 공급한다.

```js
const AuthContext = createContext()

// Provider로 감싸서 value 공급
<AuthContext.Provider value={{ user, login, logout }}>
  {children}
</AuthContext.Provider>

// 어디서든 꺼내 씀
useContext(AuthContext)  // → { user, login, logout }
```

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

### useState와 localStorage 연동

```js
const [user, setUser] = useState(() => {
  const saved = localStorage.getItem('iai_user')
  return saved ? JSON.parse(saved) : null
})
```

앱이 처음 로드될 때 localStorage에서 유저 정보를 꺼내 `useState`에 올린다. localStorage는 **문자열만** 저장 가능하기 때문에 저장 시 `JSON.stringify`, 꺼낼 때 `JSON.parse`를 사용한다.

### 새로고침해도 로그인 유지되는 이유

```
새로고침
    ↓
메모리 초기화 (Context, useState 전부 사라짐)
    ↓
앱 다시 로드 → AuthProvider 마운트
    ↓
localStorage에서 유저 정보 복원
    ↓
로그인 상태 유지
```

localStorage = 메모리가 날아가도 살아남는 백업본이다.

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

## 6. 프론트엔드 보안 현실

### JSX 코드 노출 가능성

브라우저 개발자도구 → Sources 탭에서 번들된 JS를 볼 수 있다. `npm run dev`로 개발 중이면 원본 코드가 그대로 노출된다.

```
npm run dev    → 난독화 X (개발용)
npm run build  → 난독화 O (배포용)
```

### 난독화란

빌드 시 자동으로 적용된다. 변수명을 `a`, `b`, `c`로 축약하고 공백을 제거해서 읽기 어렵게 만든다. 하지만 브라우저가 실행할 수 있는 JS여야 하므로 완벽한 방어는 아니다.

난독화는 **귀찮게 만드는 것**이지 막는 것이 아니다. 민감한 로직(DB 접근, 검증 등)은 반드시 서버에 둬야 한다.
