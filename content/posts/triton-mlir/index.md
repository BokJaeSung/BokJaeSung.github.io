---
title: 'GPU Kernel Compiler: Triton and MLIR'
date: 2026-03-10T10:00:00+09:00
tags: ['mlir', 'triton', 'gpu', 'compiler', 'deep-learning', 'cuda']
cover:
  image: 'images/cover.jpg'
  alt: 'MLIR 기반 Triton 컴파일 파이프라인'
  relative: true
summary: 'MLIR 기반 GPU 커널 컴파일러인 Triton이 뭔지, CUDA랑 뭐가 다른지, 내부 구조는 어떻게 생겼는지 정리'
---

## 딥러닝 모델이 GPU에서 돌아가는 과정

PyTorch로 모델 짜면 이렇게 쓴다.

```python
y = torch.relu(x @ W + b)
```

근데 이게 GPU에서 실제로 실행될 때는 전부 쪼개진다.

```
x @ W  →  행렬곱 (GEMM) 커널
+b     →  덧셈 커널
relu   →  활성화 함수 커널
```

각 연산이 GPU 커널 하나하나로 실행된다. 이 커널을 누가 만드냐가 문제인데, 예전에는 NVIDIA 엔지니어들이 cuDNN, cuBLAS에 수동으로 CUDA 코드를 짜서 넣어뒀다. 새로운 연산이 나오면 또 수동으로 짜야 했고.

이게 한계에 부딪히면서 컴파일러가 커널을 자동으로 생성하는 방향으로 바뀌었다. 그 결과물 중 하나가 Triton이다.

---

## CUDA vs Triton

CUDA로 벡터 덧셈을 짜면 이렇다.

```cuda
__global__ void add_kernel(float* x, float* y, float* out, int N) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid < N) {
        out[tid] = x[tid] + y[tid];
    }
}
```

thread 하나하나가 배열의 몇 번째 원소를 처리할지 개발자가 직접 배분한다. shared memory 관리, warp 동기화, memory coalescing 전부 신경써야 한다. 숙련된 엔지니어도 행렬곱 하나 최적화하는 데 몇 주 걸린다.

Triton으로 똑같은 걸 짜면 이렇다.

```python
import triton
import triton.language as tl

@triton.jit
def add_kernel(x_ptr, y_ptr, out_ptr, N, BLOCK_SIZE: tl.constexpr):
    pid = tl.program_id(0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    x = tl.load(x_ptr + offsets)
    y = tl.load(y_ptr + offsets)
    tl.store(out_ptr + offsets, x + y)
```

thread 단위가 아니라 BLOCK_SIZE 단위로 생각한다. 그 안에서 thread를 어떻게 쓸지는 컴파일러가 알아서 결정한다. shared memory 배치, warp 스케줄링, memory access 패턴 최적화를 Triton이 자동으로 처리한다.

추상화 수준이 한 단계 올라간 거다.

---

## MLIR이 중간에서 하는 일

Triton이 특별한 이유는 내부에서 MLIR을 쓴다는 거다.

MLIR(Multi-Level Intermediate Representation)은 2019년 Google이 발표한 컴파일러 인프라다. 핵심 아이디어는 여러 수준의 추상화를 하나의 프레임워크 안에서 표현할 수 있게 하는 것이다. 이걸 Dialect라고 부르는데, 각 Dialect는 특정 도메인을 위한 연산과 타입의 집합이다.

Triton의 컴파일 파이프라인은 이렇다.

```
Python 코드 (@triton.jit)
        ↓
tt dialect          ← 하드웨어 무관한 텐서 연산
        ↓
ttg dialect         ← GPU 레이아웃 정보 추가
        ↓
LLVM IR             ← LLVM이 받아서 처리
        ↓
PTX                 ← NVIDIA GPU 어셈블리
        ↓
GPU 실행
```

각 단계가 전부 MLIR pass다. `MLIR_ENABLE_DUMP=1` 환경변수를 켜면 각 pass 전후 IR이 어떻게 바뀌는지 볼 수 있다.

---

## Triton Dialect 구조

Triton은 총 4개의 custom dialect를 정의한다.

**tt (Triton dialect)**

하드웨어에 독립적인 텐서 연산을 표현한다. 개발자가 Python으로 짠 커널이 처음 변환되는 단계다. load, store, dot 같은 연산들이 여기 정의된다.

**ttg (TritonGPU dialect)**

레이아웃 인코딩을 추가한다. 데이터가 GPU의 thread, warp, CTA에 어떻게 분산되는지 표현한다. Linear Layout이라는 개념이 여기서 쓰이는데, 하드웨어 배치를 GF(2) 선형대수(XOR/AND)로 수학적으로 표현하는 방식이다.

**ttng (TritonNvidiaGPU dialect)**

NVIDIA Hopper 아키텍처 특화 연산들이 여기 있다. WGMMA, TMA 같은 것들이다. Ampere 계열 GPU에서는 ttg가 주로 쓰인다.

**amdg (TritonAMDGPU dialect)**

AMD GPU 특화 연산이다.

GitHub 소스코드 기준으로 언어 비율이 MLIR 40%, Python 30%, C++ 29% 정도다. 소스의 절반 가까이가 MLIR이라는 건데, 내부를 읽으려면 MLIR을 알아야 한다는 뜻이기도 하다.

---

## torch.compile과의 연결

PyTorch 2.0에서 나온 `torch.compile`이 내부적으로 Triton을 쓴다.

```python
@torch.compile
def my_func(x, W):
    return torch.relu(x @ W)
```

이렇게 하면 PyTorch가 연산 그래프를 분석해서 Triton 커널을 자동 생성한다. 개발자가 커널을 직접 짜지 않아도 최적화된 GPU 코드가 나온다.

생성된 Triton 코드를 보고 싶으면 이렇게 하면 된다.

```bash
TORCH_LOGS=output_code python your_script.py
```

---

## Triton이 실제로 쓰이는 곳

**Flash Attention**이 대표적인 사례다. Attention 연산을 메모리 효율적으로 바꾼 아이디어를 Triton으로 구현했고, 현재 LLM 학습/추론의 핵심 커널로 쓰인다.

**Liger Kernel**은 Meta가 만든 Triton 기반 커널 모음이다. LLM 학습 최적화에 특화되어 있다.

이 외에도 PyTorch 내부에서 elementwise 연산, softmax, layer norm 등 다양한 커널이 Triton으로 생성된다.

---

## IREE와의 차이

Triton과 자주 비교되는 게 IREE다.

Triton은 GPU 하나를 극한으로 잘 쓰기 위한 도구다. GPU 커널 생성 부분만 담당하고, 타깃도 NVIDIA/AMD GPU다.

IREE는 모델 하나를 최대한 많은 하드웨어에서 돌리기 위한 엔드-투-엔드 컴파일러다. 같은 모델을 NVIDIA GPU, AMD GPU, 스마트폰 NPU, CPU 전부에서 돌릴 수 있다. 대신 특정 하드웨어에서 Triton처럼 성능을 극한까지 뽑지는 않는다.

둘 다 MLIR 기반이라 컴파일 파이프라인 구조 자체는 비슷하다. Triton 먼저 익히고 IREE 보면 구조가 훨씬 빠르게 읽힌다.

---

## 더 읽을 것들

**논문**
- Triton: An Intermediate Language and Compiler for Tiled Neural Network Computations — Philippe Tillet et al., MAPL@PLDI 2019
- FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness — Tri Dao et al., NeurIPS 2022
- MLIR: Scaling Compiler Infrastructure for Domain Specific Computation — Lattner et al., CGO 2021

**문서**
- triton-lang.org 공식 튜토리얼
- github.com/triton-lang/triton
- PyTorch torch.compile 문서

**영상**
- Triton Developer Conference 2025 YouTube Playlist (현재 MLIR 기반 구조 설명)
