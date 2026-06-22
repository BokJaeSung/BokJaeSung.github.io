---
title: "K8sPatterns.01 Introduction"
date: 2026-06-22T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "microservices", "container", "pod"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.01 Introduction'
  relative: true
summary: "A beginner-friendly summary of Chapter 1 from Kubernetes Patterns — covering containers, pods, services, labels, annotations, and namespaces."
---

## 들어가며

이 포스트는 *Kubernetes Patterns* 1챕터를 읽고 정리한 내용입니다.  
"클라우드 네이티브가 뭔데?" 라는 질문에서 시작해서, Kubernetes의 핵심 개념들을 쉽게 풀어봤습니다.

---

{{< rawhtml >}}
<details style="background:transparent;border:1px solid #30363d;border-radius:8px;padding:10px 16px;margin:1.2rem 0;font-family:inherit;">
<summary style="cursor:pointer;font-weight:600;font-size:14px;color:#8b949e;user-select:none;font-family:inherit;">목차 — Table of Contents</summary>
<div style="margin-top:10px;font-size:14px;line-height:2;font-family:inherit;">
  <div><a href="#1-왜-마이크로서비스인가" style="color:#c9d1d9;text-decoration:none;">1. 왜 마이크로서비스인가?</a></div>
  <div><a href="#2-좋은-앱을-만드는-4가지-설계-원칙" style="color:#c9d1d9;text-decoration:none;">2. 좋은 앱을 만드는 4가지 설계 원칙</a></div>
  <div><a href="#3-distributed-primitives--kubernetes의-기본-단위" style="color:#c9d1d9;text-decoration:none;">3. Distributed Primitives — Kubernetes의 기본 단위</a></div>
  <div><a href="#4-container" style="color:#c9d1d9;text-decoration:none;">4. Container</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#좋은-컨테이너-이미지의-8가지-조건" style="color:#6e7681;text-decoration:none;">좋은 컨테이너 이미지의 8가지 조건</a></div>
  </div>
  <div><a href="#5-pod" style="color:#c9d1d9;text-decoration:none;">5. Pod</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#pod의-3가지-핵심-특징" style="color:#6e7681;text-decoration:none;">Pod의 3가지 핵심 특징</a></div>
  </div>
  <div><a href="#6-service" style="color:#c9d1d9;text-decoration:none;">6. Service</a></div>
  <div><a href="#7-label" style="color:#c9d1d9;text-decoration:none;">7. Label</a></div>
  <div><a href="#8-annotation" style="color:#c9d1d9;text-decoration:none;">8. Annotation</a></div>
  <div><a href="#9-namespace" style="color:#c9d1d9;text-decoration:none;">9. Namespace</a></div>
  <div><a href="#10-전체-흐름-정리" style="color:#c9d1d9;text-decoration:none;">10. 전체 흐름 정리</a></div>
</div>
</details>
{{< /rawhtml >}}

---

## 1. 왜 마이크로서비스인가?

마이크로서비스는 큰 앱을 **잘게 쪼개서** 여러 개의 작은 서비스로 만드는 방식입니다.

```
쇼핑몰 (모놀리스)          쇼핑몰 (마이크로서비스)

[하나의 거대한 앱]    →    [로그인 서비스]
                          [결제 서비스]
                          [배송 서비스]
                          [상품 서비스]
```

| | 모놀리스 | 마이크로서비스 |
|--|---------|--------------|
| 개발 | 한 팀이 전부 | 팀별로 독립 개발 |
| 배포 | 전체를 한꺼번에 | 서비스별로 따로 |
| 장애 | 하나 터지면 전체 down | 일부만 영향 |
| 복잡도 | 개발은 단순, 규모가 커지면 복잡 | 개발은 복잡, 운영은 유연 |

> 핵심: 개발 복잡성을 운영 복잡성과 맞바꾸는 것 — 그래서 **Kubernetes가 필수**입니다.

---

## 2. 좋은 앱을 만드는 4가지 설계 원칙

책에서는 Kubernetes 패턴을 배우기 전에 **앱 자체를 잘 만들어야 한다**고 강조합니다.

### Clean Code
변수 이름 하나, 함수 하나하나가 나중에 다 유지보수 비용이 됩니다.  
아무리 좋은 Kubernetes 환경이어도 **코드가 쓰레기면 대규모 쓰레기**가 될 뿐입니다.

### Domain-Driven Design (DDD)
비즈니스 관점에서 소프트웨어를 설계하는 방법론입니다.

```
❌ "기술적으로 어떻게 만들지?"
✅ "실제 쇼핑몰이 어떻게 돌아가지?"  ← 이걸 먼저 생각
```

현실 세계와 가까운 구조로 설계하면 → 나중에 컨테이너화와 자동화가 훨씬 쉬워집니다.

### Hexagonal Architecture
핵심 비즈니스 로직과 외부(DB, UI, 클라우드)를 **분리**하는 설계 방식입니다.

```
        [외부: DB, API, UI]
               ↕
        [인터페이스 (연결 통로)]
               ↕
        [핵심 비즈니스 로직]  ← 이게 중심!
```

외부가 바뀌어도 핵심 로직은 그대로 → AWS → Azure 이전도 외부 연결만 바꾸면 끝!

### 12-Factor App + Microservices 원칙

현대 클라우드 앱의 표준이 된 방법론으로, 세 가지를 목표로 합니다.

| 목표 | 의미 |
|------|------|
| Scale (확장성) | 사용자 늘어도 잘 버팀 |
| Resiliency (회복성) | 일부가 터져도 전체는 안 죽음 |
| Pace of Change (변화 속도) | 빠르게 업데이트 가능 |

---

## 3. Distributed Primitives — Kubernetes의 기본 단위

Java/JVM과 비교하면 Kubernetes를 쉽게 이해할 수 있습니다.

| Java (로컬, 1대) | Kubernetes (분산, 여러 대) |
|----------------|--------------------------|
| Class (설계도) | Container Image |
| Object (실행) | Container |
| JVM | Kubernetes |
| 생성자 `new` | Init Container |
| 데몬 스레드 | DaemonSet |
| Spring IoC | Pod |
| ExecutorService | CronJob |

```
Java = 방 하나에서 일하는 것
Kubernetes = 여러 건물에 걸쳐 팀이 협업하는 것 🏢🏢🏢
```

{{< rawhtml >}}
<div style="margin:2rem auto;width:100%;text-align:center;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 660" style="width:100%;font-family:inherit;">
  <defs>
    <marker id="k1-a" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
      <polygon points="0,0 8,3.5 0,7" fill="#8b949e"/>
    </marker>
  </defs>

  <!-- Deployment → ReplicaSet → Pod -->
  <line x1="310" y1="78" x2="270" y2="137" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="275" y1="183" x2="458" y2="259" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- CronJob → Job → Pod -->
  <line x1="640" y1="78" x2="640" y2="137" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="625" y1="183" x2="502" y2="259" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- DaemonSet → Pod -->
  <line x1="130" y1="163" x2="435" y2="261" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- StatefulSet → Pod -->
  <line x1="480" y1="183" x2="480" y2="259" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- Replication Controller → Pod -->
  <line x1="786" y1="162" x2="522" y2="261" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- Service → Pod (HPA 위로 곡선) -->
  <path d="M140,280 Q260,220 420,285" stroke="#8b949e" stroke-width="1.5" fill="none" marker-end="url(#k1-a)"/>
  <!-- HPA → Pod -->
  <line x1="351" y1="285" x2="420" y2="285" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- VPA → Pod -->
  <line x1="619" y1="285" x2="540" y2="285" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- PDB → Pod (VPA 위로 곡선) -->
  <path d="M802,280 Q660,220 540,285" stroke="#8b949e" stroke-width="1.5" fill="none" marker-end="url(#k1-a)"/>
  <!-- Pod → Container → Volume -->
  <line x1="480" y1="311" x2="480" y2="369" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="480" y1="421" x2="480" y2="467" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <!-- Volume → 하위 5개 -->
  <line x1="445" y1="513" x2="120" y2="587" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="460" y1="513" x2="245" y2="587" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="478" y1="513" x2="435" y2="583" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="500" y1="513" x2="630" y2="587" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>
  <line x1="518" y1="513" x2="825" y2="583" stroke="#8b949e" stroke-width="1.5" marker-end="url(#k1-a)"/>

  <!-- ROW 1 -->
  <rect x="245" y="32" width="130" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="310" y="55" fill="#c9d1d9" font-size="14" text-anchor="middle" dominant-baseline="central">Deployment</text>
  <rect x="585" y="32" width="110" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="640" y="55" fill="#c9d1d9" font-size="14" text-anchor="middle" dominant-baseline="central">CronJob</text>

  <!-- ROW 2 -->
  <rect x="10" y="137" width="120" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="70" y="160" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">DaemonSet</text>
  <rect x="205" y="137" width="120" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="265" y="160" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">ReplicaSet</text>
  <rect x="420" y="137" width="120" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="480" y="160" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">StatefulSet</text>
  <rect x="595" y="137" width="90" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="640" y="160" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">Job</text>
  <rect x="786" y="133" width="145" height="54" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="858" y="152" fill="#c9d1d9" font-size="12" text-anchor="middle">Replication</text>
  <text x="858" y="170" fill="#c9d1d9" font-size="12" text-anchor="middle">Controller</text>

  <!-- ROW 3 (Pod level) -->
  <rect x="30" y="262" width="110" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="85" y="285" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">Service</text>
  <rect x="206" y="258" width="145" height="54" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="278" y="277" fill="#c9d1d9" font-size="12" text-anchor="middle">Horizontal Pod</text>
  <text x="278" y="295" fill="#c9d1d9" font-size="12" text-anchor="middle">Autoscaler</text>
  <!-- Pod (중심 노드) -->
  <rect x="420" y="259" width="120" height="52" rx="6" fill="rgba(88,166,255,0.22)" stroke="#58a6ff" stroke-width="2.5"/>
  <text x="480" y="285" fill="#c9d1d9" font-size="16" text-anchor="middle" dominant-baseline="central" font-weight="700">Pod</text>
  <rect x="620" y="258" width="145" height="54" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="692" y="277" fill="#c9d1d9" font-size="12" text-anchor="middle">Vertical Pod</text>
  <text x="692" y="295" fill="#c9d1d9" font-size="12" text-anchor="middle">Autoscaler</text>
  <rect x="802" y="258" width="140" height="54" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="872" y="277" fill="#c9d1d9" font-size="12" text-anchor="middle">Pod Disruption</text>
  <text x="872" y="295" fill="#c9d1d9" font-size="12" text-anchor="middle">Budget</text>

  <!-- ROW 4: Container (green) -->
  <rect x="405" y="369" width="150" height="52" rx="6" fill="#1a4a20" stroke="#2ea043" stroke-width="2"/>
  <text x="480" y="388" fill="#ffffff" font-size="13" text-anchor="middle">Container</text>
  <text x="480" y="408" fill="#ffffff" font-size="13" text-anchor="middle">(your code)</text>

  <!-- ROW 5: Volume -->
  <rect x="425" y="467" width="110" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="480" y="490" fill="#c9d1d9" font-size="14" text-anchor="middle" dominant-baseline="central">Volume</text>

  <!-- ROW 6: Storage -->
  <rect x="20" y="587" width="110" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="75" y="610" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">ConfigMap</text>
  <rect x="195" y="587" width="100" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="245" y="610" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">Secret</text>
  <rect x="363" y="583" width="145" height="54" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="435" y="602" fill="#c9d1d9" font-size="12" text-anchor="middle">Persistent</text>
  <text x="435" y="620" fill="#c9d1d9" font-size="12" text-anchor="middle">VolumeClaim</text>
  <rect x="570" y="587" width="120" height="46" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="630" y="610" fill="#c9d1d9" font-size="13" text-anchor="middle" dominant-baseline="central">Downward API</text>
  <rect x="753" y="583" width="145" height="54" rx="5" fill="rgba(88,166,255,0.1)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="825" y="602" fill="#c9d1d9" font-size="12" text-anchor="middle">HostPath;</text>
  <text x="825" y="620" fill="#c9d1d9" font-size="12" text-anchor="middle">EmptyDir</text>
</svg>
<p style="font-size:13px;color:#6e7681;margin-top:8px;">Kubernetes Distributed Primitives — Container를 중심으로 Pod, Volume, 각종 컨트롤러가 연결된 전체 구조</p>
</div>
{{< /rawhtml >}}

---

## 4. Container

컨테이너 이미지 = **붕어빵 틀** 🐟  
컨테이너 = **실제 붕어빵** 🐟🐟🐟

틀(이미지) 하나로 붕어빵(컨테이너)을 여러 개 찍어낼 수 있습니다.

### 좋은 컨테이너 이미지의 8가지 조건

| # | 조건 | 의미 |
|---|------|------|
| 1 | Single concern | 딱 한 가지 역할만 |
| 2 | Owned by one team | 담당 팀 하나 + 독립 배포 주기 |
| 3 | Self-contained | 필요한 것을 다 들고 다님 |
| 4 | Immutable | 한번 만들면 수정 ❌, 새 버전 출시 ✅ |
| 5 | Defines resource requirements | CPU/메모리 필요량 미리 명시 |
| 6 | Well-defined APIs | 외부와 소통하는 창구가 명확 |
| 7 | Single Unix process | 컨테이너 하나 = 프로세스 하나 |
| 8 | Disposable | 언제든 만들고 없애도 OK |

> 좋은 컨테이너는 **레고 블록처럼 작고, 환경별로 설정만 바꿔서 재사용** 가능해야 합니다.

---

## 5. Pod

마이크로서비스는 개발할 때는 **컨테이너 이미지**, 실행할 때는 **Pod**입니다.

```
개발/빌드할 때          실행할 때

컨테이너 이미지    →    Pod
(설계도, 틀)           (실제로 살아서 돌아가는 것)
```

Kubernetes에서 컨테이너를 실행하는 **유일한 방법**은 Pod를 통하는 것입니다.

### Pod의 3가지 핵심 특징

**1. 스케줄링의 최소 단위**

Pod 안에 컨테이너가 여러 개라면, 스케줄러는 **모든 컨테이너의 자원을 합산**해서 감당할 수 있는 서버를 찾습니다.

**2. 컨테이너들의 동거 보장 (Colocation)**

같은 Pod 안의 컨테이너끼리 소통하는 방법:

| 방법 | 설명 | 속도 |
|------|------|------|
| 공유 파일시스템 | 같은 폴더를 읽고 씀 | 빠름 ⚡ |
| localhost 네트워크 | 내부망으로 통신 | 빠름 ⚡ |
| IPC | 프로세스간 직접 통신 | 매우 빠름 ⚡⚡ |

{{< rawhtml >}}
<div style="margin:2rem auto;width:65%;text-align:center;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 340" style="width:100%;font-family:inherit;">
  <defs>
    <marker id="kp1-gray" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#c9d1d9"/>
    </marker>
    <marker id="kp1-gold-r" markerWidth="8" markerHeight="6" refX="1" refY="3" orient="auto">
      <path d="M8,0 L0,3 L8,6 Z" fill="#fbbf24"/>
    </marker>
    <marker id="kp1-gold" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#fbbf24"/>
    </marker>
  </defs>

  <!-- Pod border -->
  <rect x="8" y="8" width="504" height="322" rx="10" fill="none" stroke="#6e7681" stroke-width="2" stroke-dasharray="10,5"/>
  <text x="492" y="318" fill="#8b949e" font-size="13" text-anchor="end" font-family="inherit">Pod</text>

  <!-- Container 1 (Python) -->
  <rect x="30" y="40" width="165" height="120" rx="8" fill="rgba(52,211,153,0.07)" stroke="#34d399" stroke-width="1.5"/>
  <text x="112" y="68" fill="#c9d1d9" font-size="13" text-anchor="middle" font-family="inherit">Container</text>
  <rect x="57" y="80" width="111" height="50" rx="5" fill="rgba(52,211,153,0.12)" stroke="#34d399" stroke-width="1"/>
  <text x="112" y="111" fill="#34d399" font-size="14" text-anchor="middle" font-weight="600" font-family="inherit">Python</text>

  <!-- Container 2 (Java) -->
  <rect x="325" y="40" width="165" height="120" rx="8" fill="rgba(88,166,255,0.07)" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="408" y="68" fill="#c9d1d9" font-size="13" text-anchor="middle" font-family="inherit">Container</text>
  <rect x="352" y="80" width="111" height="50" rx="5" fill="rgba(88,166,255,0.12)" stroke="#58a6ff" stroke-width="1"/>
  <text x="408" y="111" fill="#58a6ff" font-size="14" text-anchor="middle" font-weight="600" font-family="inherit">Java</text>

  <!-- localhost 양방향 화살표 -->
  <line x1="203" y1="100" x2="317" y2="100" stroke="#fbbf24" stroke-width="1.5" marker-end="url(#kp1-gold)" marker-start="url(#kp1-gold-r)"/>
  <text x="260" y="93" fill="#fbbf24" font-size="12" text-anchor="middle" font-style="italic" font-family="inherit">localhost</text>

  <!-- 화살표: Container1 → Disk -->
  <line x1="112" y1="160" x2="212" y2="242" stroke="#c9d1d9" stroke-width="1.5" marker-end="url(#kp1-gray)"/>
  <!-- 화살표: Container2 → Disk -->
  <line x1="408" y1="160" x2="308" y2="242" stroke="#c9d1d9" stroke-width="1.5" marker-end="url(#kp1-gray)"/>

  <!-- Disk (실린더) -->
  <ellipse cx="260" cy="292" rx="62" ry="19" fill="#0d1f35" stroke="#58a6ff" stroke-width="1.5"/>
  <rect x="198" y="252" width="124" height="40" fill="#0d1f35" stroke="none"/>
  <line x1="198" y1="252" x2="198" y2="292" stroke="#58a6ff" stroke-width="1.5"/>
  <line x1="322" y1="252" x2="322" y2="292" stroke="#58a6ff" stroke-width="1.5"/>
  <ellipse cx="260" cy="252" rx="62" ry="19" fill="#1a3050" stroke="#58a6ff" stroke-width="1.5"/>
  <text x="260" y="277" fill="#58a6ff" font-size="14" text-anchor="middle" font-weight="600" font-family="inherit">Disk</text>
</svg>
<p style="font-size:13px;color:#6e7681;margin-top:8px;">같은 Pod 안의 컨테이너들은 localhost와 Disk를 공유한다</p>
</div>
{{< /rawhtml >}}

**3. IP/포트 공유**

Pod 안의 컨테이너들은 IP 주소와 포트를 공유합니다. 포트가 겹치면 충돌이 납니다.

```
Pod (IP: 10.0.0.1)
├── 컨테이너 A → 포트 8080 ✅
├── 컨테이너 B → 포트 8081 ✅
└── 컨테이너 C → 포트 8080 ❌ 충돌!
```

**사이드카 패턴** — Pod 안에 메인 컨테이너 + 보조 컨테이너를 함께 두는 방식:

```
Pod
├── 메인 앱 컨테이너 🚗
└── 사이드카 컨테이너 🏍️  (로그 수집, 모니터링 등)
```

---

## 6. Service

Pod는 언제든 죽고 다시 생깁니다. 그때마다 IP 주소가 바뀝니다.

```
사용자: "10.0.0.1로 접속해야지!"
Pod가 죽고 새로 생김 → 새 IP: 10.0.0.5
사용자: "어?? 접속이 안되네" 😱
```

Service는 이 문제를 해결하는 **고정 주소 + 대표 창구**입니다.

```
사용자 → Service (주소 고정! 절대 안 바뀜 🔒)
               ↓
          살아있는 Pod로 자동 연결
```

| Service의 역할 | 설명 |
|--------------|------|
| 고정 주소 | IP/포트가 절대 안 바뀜 |
| 서비스 디스커버리 | 살아있는 Pod를 자동으로 찾아줌 |
| 로드 밸런싱 | 여러 Pod에 트래픽을 골고루 분배 |

> Service = **대표전화** 📞 / Pod = **실제 상담원**

---

## 7. Label

마이크로서비스로 쪼개면 Pod가 여러 개가 됩니다.  
이 Pod들이 **같은 앱에 속한다는 걸 표시**하는 방법이 Label입니다.

```
Pod 1 → label: app=쇼핑몰, tier=frontend
Pod 2 → label: app=쇼핑몰, tier=backend
Pod 3 → label: app=쇼핑몰, tier=database

Pod 4 → label: app=결제, tier=api
Pod 5 → label: app=결제, tier=database
```

Label로 Pod 그룹을 관리할 수 있습니다:

```bash
# app=쇼핑몰인 Pod 전부 재시작
kubectl rollout restart deployment -l app=쇼핑몰
```

**Label 사용 시 주의사항**

- 추가는 언제든 쉽게 가능 ✅
- 삭제는 **매우 위험** ⚠️ — ReplicaSet, Service, 모니터링 등 어디서 쓰이는지 파악하기 어려움
- 미리 너무 많이 달지 말고, **필요한 것만** 달기

> Label = 인스타그램 해시태그 🏷️ — 단순 태그가 아니라 **Kubernetes가 실제 Pod를 관리하는 데 핵심적으로 사용**됩니다.

---

## 8. Annotation

Label과 비슷하지만 목적이 다릅니다.

| | Label | Annotation |
|--|-------|------------|
| 목적 | 검색/그룹핑/관리 | 부가정보 저장 |
| 사용자 | 사람 | 기계/자동화 도구 |
| 검색 가능? | ✅ | ❌ |
| 예시 | `app=쇼핑몰` | 빌드ID, Git 브랜치 등 |

Annotation에 저장하는 정보 예시:

```yaml
annotations:
  build-id: "12345"
  git-branch: "main"
  image-hash: "sha256:abc..."
  author: "김철수"
  timestamp: "2026-06-22"
```

> Label = **책의 분류 태그** 🏷️ / Annotation = **책 뒷면의 상세정보** 📖

---

## 9. Namespace

하나의 Kubernetes 클러스터를 **용도별로 나누는 칸막이**입니다.

```
Kubernetes 클러스터 = 하나의 큰 사무실 🏢

dev namespace | testing namespace | production namespace
(개발팀 공간)   (QA팀 공간)         (운영팀 공간)
```

**주요 특징 정리:**

| 특징 | 설명 |
|------|------|
| 이름 충돌 방지 | 같은 이름을 Namespace별로 따로 쓸 수 있음 |
| DNS 주소 구분 | `my-app.production.svc.cluster.local` |
| ResourceQuota | Namespace별로 CPU/메모리 한도 설정 가능 |
| 기본 격리 없음 | ⚠️ 기본적으로 다른 Namespace 접근 가능 (별도 네트워크 정책 필요) |

**실제로 많이 쓰는 구성:**

```
비운영 클러스터 🖥️          운영 클러스터 🖥️
├── dev namespace           ├── performance namespace
├── testing namespace       └── production namespace
└── integration namespace
```

> 완벽한 격리가 필요하면 **클러스터 자체를 분리**해야 합니다.

---

## 10. 전체 흐름 정리

{{< rawhtml >}}
<div style="background:linear-gradient(135deg,#1e3050,#253c60,#1c2d50);border-radius:12px;padding:24px;margin:1.5rem 0;font-family:monospace;font-size:14px;color:#c9d1d9;line-height:2;">
<div style="color:#58a6ff;font-weight:bold;margin-bottom:8px;">[ 개발 → 배포 → 운영 전체 흐름 ]</div>
<div>1. 개발팀이 Clean Code + DDD로 앱 설계</div>
<div>2. 컨테이너 이미지로 패키징 (단일 목적, 불변)</div>
<div>3. Kubernetes에 Pod로 배포</div>
<div>4. Service로 고정 주소 제공</div>
<div>5. Label로 Pod 그룹 관리</div>
<div>6. Namespace로 환경(dev/prod) 분리</div>
<div>7. Annotation으로 자동화 도구에 메타데이터 전달</div>
</div>
{{< /rawhtml >}}

| 개념 | 한마디 요약 | 비유 |
|------|-----------|------|
| Container | 앱을 담는 도시락통 | 붕어빵 틀/붕어빵 🍱 |
| Pod | 컨테이너들의 묶음 | Spring IoC 컨텍스트 |
| Service | Pod의 고정 주소/대표창구 | 대표전화 📞 |
| Label | Pod에 붙이는 태그 | 인스타 해시태그 🏷️ |
| Annotation | 기계가 읽는 메모장 | 책 뒷면 상세정보 📖 |
| Namespace | 클러스터를 나누는 칸막이 | 사무실 부서 칸막이 🚧 |

---

## 마치며

1챕터의 핵심 메시지는 단순합니다.

> **"Kubernetes가 아무리 좋아도, 앱 자체가 잘 만들어져 있지 않으면 소용없다."**

좋은 그릇(Kubernetes)도 중요하지만, 담는 내용물(앱)이 먼저입니다.  
다음 챕터부터는 본격적으로 Kubernetes 패턴들을 하나씩 살펴볼 예정입니다.