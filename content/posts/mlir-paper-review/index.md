---
title: '[논문 리뷰] MLIR: A Compiler Infrastructure for the End of Moore''s Law'
date: 2026-03-05T14:00:00+09:00
tags: ['mlir', 'compiler', 'llvm', 'paper-review', 'ml-compiler']
cover:
  image: 'images/cover.jpg'
  alt: 'MLIR Paper Review'
  relative: true
summary: 'Chris Lattner가 Google에서 만든 MLIR 논문을 읽고 정리했음. "왜 LLVM 하나로는 안 되는가"라는 질문에서 시작해서, Dialect 기반의 다층 IR 설계가 어떻게 컴파일러 인프라의 새로운 패러다임을 열었는지를 다룸.'
---

**논문**: MLIR: A Compiler Infrastructure for the End of Moore's Law
**저자**: Chris Lattner, Mehdi Amini et al. (Google, IISc)
**링크**: [arXiv:2002.11054](https://arxiv.org/abs/2002.11054)

---

## 읽게 된 계기

AI 가속기 컴파일러 관련 작업을 하면서 MLIR을 직접 써봤는데, "그래서 이게 정확히 어떤 문제를 풀려고 만든 거야?"라는 질문이 계속 남아 있었음. 공식 문서보다 원 논문이 설계 의도를 훨씬 잘 설명해준다고 해서 읽어봤음.

---

## 1. 문제 제기: 왜 MLIR이 필요한가

논문이 시작하는 지점은 단순한데, 되게 핵심을 찌른다.

> 지금 컴파일러 생태계를 보면, 각 언어/프레임워크가 저마다 중간 표현(IR)을 따로 만들고 있음. Swift는 SIL, Rust는 MIR, Julia는 Julia IR... 그런데 이것들 전부 결국엔 LLVM IR로 수렴함.

왜 중간에서 각자 다른 IR을 만드는가? 이유는 있다. LLVM IR은 추상화 수준이 너무 낮아서, 고수준 의미(semantic)를 보존하면서 최적화하려면 중간 레이어가 필요하다는 것.

그 중간 레이어를 언어마다 따로 만드는 건 명백한 낭비였음. 그 낭비를 없애려고 나온 게 MLIR.

---

## 2. 핵심 설계 철학 6가지

논문의 Section 2~3에서 MLIR이 어떻게 달라야 하는지를 6가지로 정리함.

### ① Little Builtin, Everything Customizable

MLIR이 기본으로 제공하는 건 세 개뿐.

- **Type**: 값의 종류 (`i32`, `tensor<4xf32>`, 사용자 정의 타입)
- **Operation (Op)**: 모든 명령의 기본 단위
- **Attribute**: 컴파일 타임에 확정되는 정적 정보

나머지는 전부 사용자가 정의함. 하드코딩된 가정이 없으니 어떤 도메인에도 적용 가능했음.

### ② SSA + Nested Regions

MLIR은 SSA(Static Single Assignment) 형태를 기본으로 한다. 각 값은 딱 한 번만 정의되기 때문에 데이터 흐름 추적이 쉬워짐.

여기에 더해 **중첩 Region**을 지원한다는 게 핵심. `for` 루프 안에 `if` 블록이 있고 그 안에 또 다른 Op가 있는 구조를, 평탄하게 펼치지 않고 그대로 IR에 표현할 수 있음.

```mlir
affine.for %i = 0 to %N {
  affine.for %j = 0 to %N {
    %0 = affine.load %A[%i]
    %1 = affine.load %B[%j]
    %2 = std.mulf %0, %1
    affine.store %2, %C[%i+%j]
  }
}
```

루프 구조가 IR에 살아 있으니, 루프 타일링 같은 최적화를 IR 수준에서 직접 적용할 수 있다.

### ③ Progressive Lowering (단계적 하강)

기존 방식의 문제는 하나의 단계로 뚝 떨어진다는 것.

```
Source → AST → LLVM IR → Machine Code
```

LLVM IR로 내려가는 순간 고수준 정보가 모두 사라짐. 텐서가 뭐였는지, 루프 구조가 뭐였는지 다 잊어버린다. 그리고 그 손실은 선택이 아니라 사고처럼 일어남.

MLIR의 접근:

```
TF Graph dialect   ← 그래프 수준 최적화 (operator fusion 등)
       ↓
affine dialect     ← 루프 수준 최적화 (tiling, interchange 등)
       ↓
std dialect        ← Op 수준 최적화 (algebraic simplification 등)
       ↓
LLVM IR            ← 최종 코드 생성
```

각 단계에서 그 단계에서만 가능한 최적화를 적용하고, 구조를 버리는 건 의도적으로 선택할 때만 함.

### ④ Maintain Higher-Level Semantics

위와 연결되는 얘기인데, 논문이 명시적으로 강조하는 부분이 있음.

> "flat CFG로 내려가면 루프 수준 최적화는 더 이상 불가능하다. 구조를 잃는 건 의도된 결정이어야지, 사고로 일어나면 안 된다."

추상화를 내리는 행위 자체를 설계 결정으로 취급한다는 관점이 인상적이었음.

### ⑤ Declarative Rewrite Patterns

변환 규칙을 코드가 아니라 선언적으로 표현한다.

- **ODS (Operation Definition Specification)**: Op 구조를 TableGen으로 선언
- **DRR (Declarative Rewrite Rules)**: `LeakyReLU → Compare + Select` 같은 변환 규칙을 패턴으로 선언

변환 로직을 일일이 C++로 짜는 대신, 규칙을 정의하면 프레임워크가 나머지를 처리함. 코드 재사용성이 높아짐.

### ⑥ IR Validation

열린 생태계라는 건 곧 버그가 더 들어올 수 있다는 뜻. MLIR은 각 Op가 자체 verifier를 갖도록 설계해서, IR 불변성 위반을 조용히 넘기지 않고 초기에 잡음.

---

## 3. IR 구조: Op · Attribute · Type · Dialect

### Op의 해부학

MLIR에서 모든 것은 Op다. 명령(instruction)도, 함수(function)도, 모듈(module)도 전부 Op.

Op 하나는 이렇게 생겼음.

| 구성 요소 | 설명 | 예시 |
|---|---|---|
| opcode | 어느 dialect의 무슨 명령인지 | `affine.for` |
| operands | 입력 값들 | `%arg0, %arg1` |
| results | 출력 값들 | `%result` |
| attributes | 컴파일 타임 정적 정보 | `{lower_bound=0, step=1}` |

### Dialect

**Dialect** = Ops + Types + Attributes를 하나의 네임스페이스 아래 묶은 것.

| Dialect | 담당 | 주요 Op |
|---|---|---|
| `tf` | TensorFlow 그래프 | `tf.Add`, `tf.MatMul`, `tf.Conv2D` |
| `affine` | 루프·메모리 최적화 | `affine.for`, `affine.load`, `affine.store` |
| `std` | 기본 산술 | `std.addf`, `std.mulf`, `std.call` |
| `llvm` | 최종 코드 생성 | `llvm.add`, `llvm.br`, `llvm.ret` |

핵심은 **다른 dialect가 같은 IR 안에 공존할 수 있다**는 것. 이게 Progressive Lowering을 가능하게 하는 기술적 토대.

### Recursive Structure (Op → Region → Block → Op)

```
Op (affine.for)
  └─ Region
       └─ Block (^bb0)
            ├─ Op (affine.load)
            ├─ Op (std.mulf)
            └─ terminator Op
```

Op가 내부에 Region을 가질 수 있고, Region 안에 또 Op가 들어갈 수 있음. 이 재귀적 구조 덕분에 루프, 조건문, 함수 정의 같은 복잡한 제어 흐름을 IR에서 계층적으로 표현 가능.

---

## 4. 적용 사례

### TensorFlow

LLVM IR에는 텐서나 비동기 제어 흐름이라는 개념이 없음. TF 그래프를 LLVM IR로 직접 내리면 고수준 의미가 전부 날아가서, 그래프 수준 최적화가 불가능해짐.

MLIR의 `tf` dialect를 쓰면 TF 그래프 구조를 IR에서 그대로 표현할 수 있음.

```mlir
%0 = tf.graph (%arg0 : tensor<f32>, %arg1 : tensor<f32>) {
  %1, %ctrl = tf.ReadVariableOp(%arg2)
  %2, %ctrl1 = tf.Add(%arg0, %1)
  tf.fetch %2 : tensor<f32>
}
```

이 표현 위에서 그래프 최적화(algebraic simplification), 모바일 배포 변환, XLA 코드젠, 이종 하드웨어(GPU/TPU) 타겟팅을 순차적으로 적용할 수 있음.

### DSP: Optimizing Pattern Rewriting

MLIR의 패턴 리라이트 시스템이 가진 특성이 몇 가지 있음.

- **런타임 확장성**: 리라이트 패턴을 컴파일 타임이 아니라 런타임에 동적으로 추가 가능
- **하드웨어 벤더 친화적**: 하드웨어 벤더가 새로운 lowering 규칙을 드라이버 수준에서 주입할 수 있음
- **메타 구조**: 패턴 리라이트 규칙 자체를 MLIR dialect로 표현함 → MLIR이 MLIR 자신의 변환 규칙을 기술하는 메타 계층이 됨

### Lattice Regression Compiler

기존에 C++ 템플릿으로 짜던 lattice regression 컴파일러를 MLIR로 재작성한 사례.

| | Before | After |
|---|---|---|
| 구현 방식 | C++ 템플릿 | MLIR 기반 |
| 최적화 | 어려움 | 범용 최적화 적용 가능 |
| 투명성 | 낮음 | 높음 |

결과: **3인월** 만에 전체 컴파일러 재구축, 프로덕션 모델에서 **8배 성능 향상**, **M+ 사용자**에게 실 적용.

---

## 5. 열린 생태계의 대가: Pass 설계 문제

Op가 완전히 확장 가능하면, 컴파일러 패스를 어떻게 작성해야 하는가? 모든 Op를 알 수 없으니 일반적인 패스를 짜기가 어려워짐.

MLIR은 네 가지로 이 문제를 해결함.

**① Op Traits**: Op에 `no_side_effect`, `commutative` 같은 속성을 태깅. Dead Code Elimination이나 CSE 같은 패스가 특정 dialect 몰라도 trait만 보고 동작 가능.

**② Privileged Hooks**: 각 Op가 constant folding, canonicalization 훅을 직접 구현. 패스 하나가 훅을 호출하면 모든 dialect에 걸쳐 동작. LLVM의 InstCombine, DAGCombine, PeepholeOptimizer를 하나로 대체.

**③ Optimization Interfaces**: 패스가 인터페이스를 정의하고, dialect가 구현함. 예: inliner 패스가 `CallableOpInterface`를 정의하면, TF 그래프든 Flang 함수든 해당 인터페이스를 구현하는 것은 다 inlining 가능.

**④ Dialect-specific Passes**: 무리하게 일반화할 필요 없이, 특정 dialect에만 동작하는 패스도 완전히 유효함.

결과적으로 Canonicalization 패스 하나가 LLVM에서 수십 개였던 특수 목적 패스들을 대체함.

### Dialect Mixing의 힘

가장 인상적인 부분.

```mlir
affine.for %i = 0 to %N
  tf.MatMul(%A, %B)       ← tf dialect
  std.addf %x, %y         ← std dialect
  affine.store %r, %C[%i] ← affine dialect
```

서로 다른 dialect가 같은 IR 안에서 공존하면, affine의 루프 최적화가 TF Op에 자동으로 적용됨. OpenMP dialect를 Fortran과 C 컴파일러가 공유하는 것도 이 구조 덕분.

---

## 6. 한계와 저자들의 솔직한 고백

논문 Section 6.4를 읽으면서 오히려 신뢰도가 올라갔음. 저자들이 직접 인정하는 한계들.

- MLIR은 거의 모든 것을 표현할 수 있는데, 무엇을 어떻게 표현해야 하는지는 알려주지 않음
- IR 설계는 여전히 과학이 아니라 예술
- 대부분의 엔지니어는 추상화를 처음부터 설계해본 경험이 없음
- 호환되지 않는 추상화 설계로 인한 내부 단편화 위험

> "설계 포인트들이 완전히 이해되고 모범 사례가 정립되려면 몇 년의 연구가 더 필요할 것이다."

### Looking Forward

그럼에도 저자들이 기대하는 방향은 분명함.

1. **Out-of-tree dialect 확산**: 커뮤니티가 독립적으로 만드는 dialect들이 빠르게 늘어나는 중
2. **소스 언어 프론트엔드 도입**: 더 많은 컴파일러가 MLIR을 공통 중간 레이어로 채택할 것
3. **AST 수준 적용**: 아직 초기이지만, 소스 레벨 AST도 MLIR로 표현하려는 시도가 있음
4. **구조화 데이터**: JSON, protobuf 같은 데이터 표현에도 MLIR 개념을 적용하는 방향

---

## 총평

### 잘 한 것

- "중간 표현을 여러 레벨로" 라는 아이디어는 단순한데 강력함. 기존 컴파일러들이 왜 고통받았는지를 구조적으로 설명하고, 그 해결책을 깔끔하게 제시했음
- Dialect 개념이 추상화 수준을 명문화한다는 것. 코드가 어느 단계에 있는지를 타입 시스템이 강제함
- 실제 TF, Lattice compiler 같은 프로덕션 사례를 들고 나왔다는 점. 이론적 제안이 아니라 실제로 동작한다는 걸 보여줌

### 아쉬운 것

- "어떤 dialect 계층을 설계해야 하는가"에 대한 가이드가 논문에는 거의 없음. 저자들도 인정하는 부분
- 진입 장벽 얘기를 좀 더 했으면 좋았을 것. TableGen 문법 배우는 게 생각보다 시간이 걸림
- 성능 벤치마크가 Lattice 사례 하나뿐이라 일반화하기 어려움

### 한 줄 요약

> 컴파일러 인프라의 "추상화 레벨"을 일급 개념으로 만들어서, 언어도 하드웨어도 도메인도 가리지 않는 재사용 가능한 컴파일러 인프라를 만든 논문.

---

## 결론: 논문이 말하는 것

논문의 마지막 메시지는 세 가지로 요약됨.

**① Concrete Design** — Op · Dialect · Region · Type, 최소한의 빌딩 블록이지만 어떤 추상화도 표현 가능.

**② Real Applicability** — TF 그래프, DSP 컴파일러, Fortran IR. 이론이 아니라 실제 프로덕션에서 검증됨.

**③ New Research Implications** — 재사용 가능한 패스, dialect 혼합, 단계적 하강. 컴파일러 인프라를 설계하는 완전히 새로운 방식을 제안함.

향후 연구로 기대되는 영역: C++ CIL(표준 IR), Auto-diff, Parallel ops, GC 기반 언어, DB 쿼리 최적화, 컴파일러 교육까지.

> *"We believe there is still a lot to discover, and several more years of research will be required until the design points are all fully understood and best practices are established."*
