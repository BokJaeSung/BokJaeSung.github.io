---
title: '[논문 리뷰] PyTorch: An Imperative Style, High-Performance Deep Learning Library'
date: 2026-03-16T09:00:00+09:00
tags: ['pytorch', 'deep-learning', 'paper-review', 'autograd', 'neurips']
cover:
  image: 'images/cover.jpg'
  alt: 'PyTorch 2019 Paper Review'
  relative: true
summary: 'NeurIPS 2019에 발표된 PyTorch 원 논문 리뷰. Eager Execution 기반의 설계 철학과 autograd 구현, 그리고 왜 연구자들이 PyTorch에 열광했는지를 정리함.'
---

> **논문**: *PyTorch: An Imperative Style, High-Performance Deep Learning Library*  
> **저자**: Adam Paszke et al. | **발표**: NeurIPS 2019

---

PyTorch를 쓰다 보면 "이거 왜 이렇게 자연스럽지?" 싶을 때가 있다. `print()` 찍으면 바로 값이 나오고, 일반 파이썬 디버거도 그냥 되고, `if`문이나 `for`문도 그냥 쓰면 된다. 그게 당연한 게 아니었다. 이 논문을 읽고 나서야 그 이유를 알았다.

---

## 배경: 딥러닝이 얼마나 복잡해졌나

논문은 이런 말로 시작한다.

> *"In a surprisingly short amount of time, machine learning grew from recognizing individual digits into autonomously playing StarCraft."*

숫자 인식에서 스타크래프트 자율 플레이까지, 딥러닝이 다루는 문제가 폭발적으로 복잡해졌다. 모델 구조도 단순한 레이어 나열에서 수많은 루프와 재귀 함수가 얽힌 형태로 진화했다.

문제는 기존 프레임워크들이 이런 복잡성을 따라가기 힘들었다는 것이다.

---

## 기존 방식의 문제: 설계도 먼저, 실행 나중

TensorFlow 1.x, Theano, Caffe의 방식을 **Define-and-Run**이라고 부른다. 요리로 비유하면 이렇다.

```
레시피 완성 (그래프 설계)
    ↓
재료 투입 (데이터)
    ↓
요리 시작 (session.run)
```

코드로 보면 이런 식이다.

```python
# TensorFlow 1.x
x = tf.placeholder(tf.float32)
y = tf.matmul(x, W)   # 실행 X — 설계도에 추가만 됨
z = tf.nn.relu(y)     # 실행 X — 마찬가지

print(z)              # ❌ 'Tensor("Relu:0")' 출력
                      # 실제 값이 아님!

session.run(z, {x: data})  # 여기서야 비로소 실행
```

`print()`를 찍어도 실제 값이 안 나온다. 그래프 노드 정보만 나온다. 중간에 뭔가 잘못됐어도 `session.run()`을 돌려봐야 안다. 디버깅이 매우 고통스럽다.

더 큰 문제는 `if`문이다. 파이썬의 `if`를 그대로 쓸 수 없어서 `tf.cond()`라는 특수한 문법을 써야 했다. 복잡한 모델일수록 코드가 난해해진다.

---

## PyTorch의 답: 실행하면서 동시에 정의

PyTorch의 방식은 **Define-by-Run**이다. 논문에서는 이걸 **Dynamic Eager Execution**이라고 부른다.

> *"PyTorch performs immediate execution of dynamic tensor computations with automatic differentiation and GPU acceleration."*

말 그대로 **즉시(immediate) 실행**이다.

```python
# PyTorch
x = torch.tensor([2.0], requires_grad=True)
y = x @ W     # 이 줄이 실행되는 순간 바로 계산됨
z = relu(y)   # 이것도 마찬가지

print(z)      # ✅ tensor([6.0]) — 실제 값이 바로 나옴
```

`if`문도, `for`문도 그냥 쓴다.

```python
for x in data:
    if x > 0:
        y = model_a(x)
    else:
        y = model_b(x)
```

### 그러면 역전파는 어떻게?

정적 그래프는 미리 그린 설계도로 역전파한다. 그런데 PyTorch는 설계도가 없는데 어떻게 역전파를 할까?

**실행하면서 연산 기록을 남긴다.** 각 텐서는 "나는 어떤 연산으로 만들어졌는가"를 내부적으로 기억한다.

```
x (2.0)
  ↓ ×3
y (6.0)  →  grad_fn = MulBackward  →  (x를 가리키는 포인터)
  ↓ +1
z (7.0)  →  grad_fn = AddBackward  →  (y를 가리키는 포인터)
```

이 포인터 체인이 사실상 그래프다. `z.backward()`를 호출하면 포인터를 역방향으로 따라가며 gradient를 계산한다. 다 끝나면 이 기록은 메모리를 아끼기 위해 자동으로 삭제된다.

그래서 이런 에러가 생긴다.

```python
z.backward()   # 기록 삭제됨
z.backward()   # ❌ RuntimeError: 기록이 없음
               # retain_graph=True 옵션 필요
```

---

## 모델 작성: 그냥 파이썬 클래스

논문이 강조하는 또 하나의 포인트다.

> *"Layers should really be understood as stateful functions with implicit parameters."*

레이어 = **가중치(상태)를 가진 파이썬 클래스**.

```python
class LinearLayer(nn.Module):
    def __init__(self, in_sz, out_sz):
        super().__init__()
        self.w = nn.Parameter(torch.randn(in_sz, out_sz))  # 가중치
        self.b = nn.Parameter(torch.randn(out_sz))         # 편향

    def forward(self, x):          # 실제 계산
        return torch.mm(x, self.w) + self.b
```

`__init__`에서 가중치를 만들고, `forward()`에서 계산한다. `forward(x)`를 호출할 때 `w`와 `b`를 직접 넘기지 않아도 된다. 이미 클래스 안에 있으니까. 이게 논문이 말하는 **"암묵적 파라미터를 가진 상태 함수"**다.

모델은 이 레이어들을 조합한다.

```python
class FullModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(1, 128, 3)
        self.fc   = LinearLayer(128, 10)

    def forward(self, x):
        x = F.relu(self.conv(x))
        return F.softmax(self.fc(x))
```

중요한 건 논문이 이렇게 말한다는 거다.

> *"Nothing forces the user to structure their code in that way."*

이렇게 짜야 한다는 강제가 없다. 이 자유로움이 GAN 같은 복잡한 구조에서 진가를 발휘한다.

---

## GAN 예시: 복잡한 구조도 자연스럽게

GAN은 두 모델(생성자, 판별자)이 서로 경쟁하는 구조다. 두 모델의 loss가 서로 얽혀 있어서 엄격한 API로는 구현이 까다롭다. PyTorch에서는 그냥 이렇게 쓴다.

```python
def step(real_sample):
    # 1. 판별자 업데이트
    errD_real = loss(discriminator(real_sample), real_label)
    errD_real.backward()

    fake = generator(get_noise())
    errD_fake = loss(discriminator(fake.detach()), fake_label)
    #                              ↑
    #              생성자까지 역전파 흘러들어가지 않도록 차단
    errD_fake.backward()
    optimD.step()

    # 2. 생성자 업데이트
    errG = loss(discriminator(fake), real_label)
    errG.backward()
    optimG.step()
```

`fake.detach()`가 핵심이다. 판별자를 학습할 때는 생성자 가중치까지 건드리면 안 된다. `detach()`로 역전파 연결을 끊어서 판별자만 업데이트한다.

---

## 성능: 편의성을 포기하지 않았다

Eager Execution이 편한 건 알겠는데, 느리지 않을까? 논문은 이 걱정에 정면으로 답한다.

> *"Trading 10% of speed for a significantly simpler to use model is acceptable; 100% is not."*

10% 느린 건 OK, 2배 느린 건 NO. 그래서 내부를 꼼꼼하게 최적화했다.

### 겉은 파이썬, 속은 C++

```
사용자 코드 (Python)
      ↓
Python 바인딩 (얇은 껍데기)
      ↓
libtorch C++ 코어  ←  실제 연산은 여기서
  ├── 텐서 연산
  ├── autograd
  └── GPU 연산자
```

파이썬의 GIL(한 번에 하나의 스레드만 허용) 문제가 있지만, 실제 텐서 연산은 C++에서 처리되므로 GIL 없이 멀티스레드로 실행된다.

### CPU와 GPU가 동시에 돌아간다

```
CPU: [명령1][명령2][명령3][명령4]  ← 앞서 달림
GPU:    [연산1       ][연산2    ]  ← 큐에서 순서대로
```

CPU는 CUDA 스트림(GPU 작업 큐)에 명령을 넣고 기다리지 않는다. 바로 다음 명령을 큐에 넣는다. GPU는 큐에서 꺼내서 순서대로 실행한다. 결과적으로 GPU가 쉬는 시간이 없다.

논문의 ResNet-50 실험에서 CPU가 GPU보다 약 3배 빠르게 앞서 달렸다. 파이썬 오버헤드가 있어도 GPU를 거의 100% 활용할 수 있었다.

### GPU 메모리 캐싱

`cudaMalloc`(GPU 메모리 할당)과 `cudaFree`(반납)는 CPU를 블로킹하는 동기 호출이다. 매번 호출하면 느리다. 그래서 PyTorch는 한 번 받은 VRAM을 해제하지 않고 캐시에 보관했다가 재사용한다.

```
1회차: cudaMalloc 호출 → CPU 블로킹 → 느림
2회차~: 캐시에서 재사용 → 호출 없음 → 빠름
```

실험에서 첫 번째 iteration은 cudaMalloc 때문에 느렸지만, 두 번째부터는 캐시를 재사용해서 훨씬 빨라졌다.

### 메모리 즉시 해제

파이썬의 가비지 컬렉터는 메모리 해제를 미룬다. 작은 VRAM에서는 치명적이다. PyTorch는 레퍼런스 카운팅 방식으로 아무도 안 쓰는 순간 바로 해제한다.

```python
a = torch.tensor([1.0])  # 카운트: 1
b = a                    # 카운트: 2
del b                    # 카운트: 1
del a                    # 카운트: 0 → 즉시 VRAM 해제 ✅
```

---

## 실험 결과: 17% 이내

CNTK, MXNet, TensorFlow, Chainer, PaddlePaddle과 비교했을 때 PyTorch는 **가장 빠른 프레임워크 대비 17% 이내** 성능을 보였다.

왜 비슷한가? 모든 프레임워크가 결국 **cuDNN**과 **cuBLAS**를 사용하기 때문이다. 실제 GPU 연산은 동일한 라이브러리가 처리하니 근본적인 차이가 나기 어렵다.

채택률도 증명한다. arXiv 논문에서 PyTorch 언급 비율이 2017년 출시 이후 급격히 증가했고, ICLR 2019에서는 **296편**의 논문이 PyTorch를 언급했다.

---

## 마무리

논문 한 줄로 요약하면 이렇다.

> *"편하게 쓰되, 너무 느리면 안 된다."*

Eager Execution 덕분에 디버깅이 쉽고, C++ 코어와 비동기 GPU 실행 덕분에 성능도 잃지 않았다. 거기에 "모든 것이 그냥 파이썬 프로그램"이라는 자유로운 설계가 복잡한 구조도 자연스럽게 표현하게 해줬다.

논문에서 미래 계획으로 언급한 **PyTorch JIT**는 이후 `torch.compile()`과 **Triton**으로 발전했다. Eager Execution의 편의성을 유지하면서 정적 그래프의 최적화 이점까지 흡수하는 방향이다. 앞으로 PyTorch가 어디까지 발전할지, 기대가 된다.

---

## 참고

- [PyTorch 논문 (arXiv)](https://arxiv.org/abs/1912.01703)
- [PyTorch 공식 문서](https://pytorch.org/docs/)
- [torch.compile 소개](https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html)