---
title: "PersistentVolume / PVC"
summary: "저장소의 실체(PV)와 요청서(PVC)를 나눠 둔 구조. 앱은 얼마나 필요한지만 말하고 어디서 오는지는 모른다."
categories: ["쿠버네티스", "스토리지"]
tags: ["kubernetes", "storage", "volume"]
aliases_search: ["pv", "pvc", "persistentvolumeclaim", "퍼시스턴트 볼륨", "영구 볼륨", "스토리지클래스", "storageclass"]
---

## 1. 개요

**PersistentVolume**(PV)은 클러스터 안의 **실제 저장 공간**이고, **PersistentVolumeClaim**(PVC)은 그 공간을 달라는 **요청서**다.

공식 문서는 이 관계를 노드와 Pod 에 빗댄다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 250" style="width:100%;min-width:660px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pod 가 노드의 계산 자원을 소비하는 구조와 PVC 가 PV 의 저장 자원을 소비하는 구조가 같은 형태로 대응된다">
  <text x="380" y="26" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">이미 쓰고 있는 구조가 저장소에도 똑같이 있다</text>

  <!-- 행 라벨 -->
  <text x="26" y="86" font-size="10" fill="var(--secondary,#888)">실체</text>
  <text x="26" y="101" font-size="9" fill="var(--secondary,#888)">클러스터가 가진 것</text>
  <text x="26" y="176" font-size="10" fill="var(--secondary,#888)">요청</text>
  <text x="26" y="191" font-size="9" fill="var(--secondary,#888)">내가 쓰는 것</text>

  <!-- 계산 자원 -->
  <text x="290" y="52" text-anchor="middle" font-size="11" fill="var(--secondary,#888)">계산 자원 — 익숙한 쪽</text>
  <rect x="180" y="66" width="220" height="48" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="290" y="86" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2f6ea8">Node</text>
  <text x="290" y="102" text-anchor="middle" font-size="9" fill="#2f6ea8" opacity=".85">CPU · 메모리를 가진 실체</text>

  <rect x="180" y="156" width="220" height="48" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="290" y="176" text-anchor="middle" font-size="10.5" font-weight="600" fill="#2f6ea8">Pod</text>
  <text x="290" y="192" text-anchor="middle" font-size="9" fill="#2f6ea8" opacity=".85">"CPU 500m 주세요"</text>

  <path d="M290,152 V118" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="302" y="138" font-size="9" fill="#2e9c6d">소비</text>

  <!-- 저장 자원 -->
  <text x="600" y="52" text-anchor="middle" font-size="11" font-weight="600" fill="#8e44ad">저장 자원 — 같은 구조</text>
  <rect x="490" y="66" width="220" height="48" rx="5" fill="none" stroke="#8e44ad" stroke-width="1.8"/>
  <text x="600" y="86" text-anchor="middle" font-size="10.5" font-weight="600" fill="#8e44ad">PersistentVolume</text>
  <text x="600" y="102" text-anchor="middle" font-size="9" fill="#8e44ad" opacity=".85">100Gi 디스크라는 실체</text>

  <rect x="490" y="156" width="220" height="48" rx="5" fill="none" stroke="#8e44ad" stroke-width="1.8"/>
  <text x="600" y="176" text-anchor="middle" font-size="10.5" font-weight="600" fill="#8e44ad">PersistentVolumeClaim</text>
  <text x="600" y="192" text-anchor="middle" font-size="9" fill="#8e44ad" opacity=".85">"10Gi 주세요"</text>

  <path d="M600,152 V118" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="612" y="138" font-size="9" fill="#2e9c6d">소비</text>

  <!-- 대응 표시 -->
  <path d="M400,90 H486" stroke="var(--secondary,#888)" stroke-width="1" stroke-dasharray="4 4" fill="none" opacity=".6"/>
  <path d="M400,180 H486" stroke="var(--secondary,#888)" stroke-width="1" stroke-dasharray="4 4" fill="none" opacity=".6"/>
  <text x="443" y="84" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">대응</text>
  <text x="443" y="174" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">대응</text>

  <text x="380" y="236" text-anchor="middle" font-size="12" fill="var(--content,#333)">Pod 가 노드를 소비하듯, PVC 가 PV 를 소비한다</text>
</svg>
</div>
{{< /rawhtml >}}

나누는 이유는 **역할 분리**다. 앱을 만드는 사람은 "10Gi 필요하다"만 적고, 그게 AWS EBS 인지 NFS 인지는 몰라도 된다.

## 2. 생명주기

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 360" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PV 와 PVC 가 각각 만들어져 Available 과 Pending 상태로 있다가 바인딩되면 둘 다 Bound 가 되고 Pod 가 사용한 뒤 PVC 를 지우면 회수 정책에 따라 처리된다">
  <defs>
    <marker id="pv-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <text x="24" y="74" font-size="11" font-weight="600" fill="#8e44ad">PV</text>
  <text x="20" y="90" font-size="9" fill="var(--secondary,#888)">저장소 실체</text>
  <text x="24" y="214" font-size="11" font-weight="600" fill="#2e9c6d">PVC</text>
  <text x="20" y="230" font-size="9" fill="var(--secondary,#888)">요청서</text>

  <line x1="100" y1="30" x2="100" y2="300" stroke="var(--border,#ccc)" stroke-width="1"/>

  <text x="180" y="26" text-anchor="middle" font-size="10.5" font-weight="600" fill="var(--content,#333)">① 준비</text>
  <text x="360" y="26" text-anchor="middle" font-size="10.5" font-weight="600" fill="var(--content,#333)">② 바인딩</text>
  <text x="510" y="26" text-anchor="middle" font-size="10.5" font-weight="600" fill="var(--content,#333)">③ 사용</text>
  <text x="660" y="26" text-anchor="middle" font-size="10.5" font-weight="600" fill="var(--content,#333)">④ 회수</text>

  <rect x="120" y="50" width="120" height="50" rx="4" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="180" y="70" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">PV 생성</text>
  <text x="180" y="86" text-anchor="middle" font-size="9" fill="#8e44ad">Available</text>

  <rect x="300" y="50" width="120" height="50" rx="4" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="360" y="78" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">Bound</text>

  <rect x="450" y="50" width="120" height="50" rx="4" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="510" y="78" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">Bound</text>

  <rect x="600" y="42" width="130" height="30" rx="4" fill="none" stroke="#2e9c6d" stroke-width="1.4"/>
  <text x="665" y="62" text-anchor="middle" font-size="9.5" fill="#2e9c6d">Retain — 데이터 남음</text>
  <rect x="600" y="78" width="130" height="30" rx="4" fill="none" stroke="#c0392b" stroke-width="1.4"/>
  <text x="665" y="98" text-anchor="middle" font-size="9.5" fill="#c0392b">Delete — 디스크까지 삭제</text>

  <rect x="120" y="190" width="120" height="50" rx="4" fill="none" stroke="#2e9c6d" stroke-width="1.5"/>
  <text x="180" y="210" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">PVC 생성</text>
  <text x="180" y="226" text-anchor="middle" font-size="9" fill="#2e9c6d">Pending</text>

  <rect x="300" y="190" width="120" height="50" rx="4" fill="none" stroke="#2e9c6d" stroke-width="1.5"/>
  <text x="360" y="218" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">Bound</text>

  <rect x="450" y="190" width="120" height="50" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="510" y="210" text-anchor="middle" font-size="10" font-weight="600" fill="#5a3d18">Pod 가 마운트</text>
  <text x="510" y="226" text-anchor="middle" font-size="9" fill="#5a3d18">PVC 를 볼륨으로</text>

  <rect x="600" y="190" width="130" height="50" rx="4" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="665" y="218" text-anchor="middle" font-size="10" font-weight="600" fill="#2f6ea8">PVC 삭제</text>

  <g stroke="var(--content,#444)" stroke-width="1.6" fill="none" marker-end="url(#pv-ar)">
    <path d="M240,75 H296"/>
    <path d="M240,215 H296"/>
    <path d="M420,75 H446"/>
    <path d="M420,215 H446"/>
    <path d="M570,215 H596"/>
  </g>

  <path d="M360,100 V186" stroke="#2e9c6d" stroke-width="2" fill="none"/>
  <text x="372" y="146" font-size="9.5" font-weight="600" fill="#2e9c6d">1 : 1</text>
  <text x="372" y="160" font-size="9" fill="var(--secondary,#888)">배타적</text>

  <path d="M665,186 V114" stroke="#c0392b" stroke-width="1.6" stroke-dasharray="5 4" fill="none" marker-end="url(#pv-ar)"/>
  <text x="676" y="152" font-size="9" fill="#c0392b">정책 적용</text>

  <text x="180" y="264" text-anchor="middle" font-size="9" fill="var(--secondary,#888)">맞는 PV 없으면</text>
  <text x="180" y="277" text-anchor="middle" font-size="9" fill="#c0392b">Pending 에 머문다 → Pod 도 못 뜬다</text>

  <text x="380" y="330" text-anchor="middle" font-size="12" fill="var(--content,#333)">PV 와 PVC 는 따로 만들어져 짝을 찾는다 — 맺어지면 다른 짝은 못 낀다</text>
</svg>
</div>
{{< /rawhtml >}}

**바인딩은 일대일**이다. 한 PVC 가 한 PV 를 잡으면 다른 PVC 는 그 PV 를 쓸 수 없다. 컨트롤 플레인의 루프가 새 PVC 를 지켜보다가 조건에 맞는 PV 를 찾아 묶는다.

맞는 PV 가 없으면 PVC 는 `Pending` 에 머문다. 그 Pod 도 뜨지 못한다.

## 3. 정적 준비와 동적 준비

| | 정적 | 동적 |
|---|---|---|
| 누가 | 관리자가 미리 PV 를 만들어 둠 | StorageClass 가 PVC 요청을 받고 즉석에서 생성 |
| 맞는 게 없으면 | `Pending` | 새로 만든다 |
| 언제 | 온프레미스, 기존 NFS 활용 | 클라우드 대부분 |

동적 준비는 **StorageClass** 가 담당한다. "빠른 SSD", "저렴한 HDD" 같은 등급을 만들어두면 PVC 가 그 이름을 지목한다.

```yaml
kind: PersistentVolumeClaim
spec:
  storageClassName: fast-ssd      # 이 등급으로 만들어 달라
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
```

`storageClassName: ""` 은 **동적 준비를 끄겠다는 뜻**이다. 기존 PV 하고만 묶으라는 의미다.

## 4. 접근 모드

여기가 가장 자주 오해되는 부분이다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 400" style="width:100%;min-width:680px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="네 가지 접근 모드에서 하나의 볼륨에 몇 개의 노드와 Pod 가 붙을 수 있는지 비교">
  <text x="380" y="24" text-anchor="middle" font-size="11.5" fill="var(--secondary,#888)">가운데 원기둥이 볼륨 하나 — 여기에 누가 붙을 수 있는가</text>

  <text x="26" y="62" font-size="11.5" font-weight="600" fill="#2f6ea8">ReadWriteOnce (RWO)</text>
  <rect x="26" y="72" width="150" height="60" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="40" y="88" font-size="9" fill="#2f6ea8">Node A</text>
  <rect x="36" y="94" width="60" height="28" rx="3" fill="#e6b3d9" stroke="#a05590"/>
  <text x="66" y="112" text-anchor="middle" font-size="9" fill="#5a2050">Pod ✓</text>
  <rect x="104" y="94" width="60" height="28" rx="3" fill="#e6b3d9" stroke="#a05590"/>
  <text x="134" y="112" text-anchor="middle" font-size="9" fill="#5a2050">Pod ✓</text>
  <rect x="196" y="72" width="150" height="60" rx="5" fill="none" stroke="#c0392b" stroke-width="1.2" stroke-dasharray="4 3"/>
  <text x="210" y="88" font-size="9" fill="#c0392b">Node B</text>
  <text x="271" y="110" text-anchor="middle" font-size="9.5" fill="#c0392b">붙을 수 없다 ✕</text>
  <ellipse cx="430" cy="86" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <rect x="396" y="86" width="68" height="32" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <ellipse cx="430" cy="118" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="430" y="108" text-anchor="middle" font-size="9.5" font-weight="600" fill="#2f6ea8">볼륨</text>
  <path d="M176,102 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="500" y="98" font-size="10.5" fill="var(--content,#333)">노드 <tspan font-weight="600">1개</tspan>가 읽고 쓴다</text>
  <text x="500" y="116" font-size="10" fill="var(--secondary,#888)">그 노드 안 Pod 는 여러 개 가능</text>

  <text x="26" y="166" font-size="11.5" font-weight="600" fill="#2f6ea8">ReadOnlyMany (ROX)</text>
  <rect x="26" y="176" width="150" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="101" y="204" text-anchor="middle" font-size="9.5" fill="#2f6ea8">Node A ✓</text>
  <rect x="196" y="176" width="150" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="271" y="204" text-anchor="middle" font-size="9.5" fill="#2f6ea8">Node B ✓</text>
  <ellipse cx="430" cy="182" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <rect x="396" y="182" width="68" height="26" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <ellipse cx="430" cy="208" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="430" y="202" text-anchor="middle" font-size="9.5" font-weight="600" fill="#2f6ea8">볼륨</text>
  <path d="M176,199 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <path d="M346,199 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="500" y="200" font-size="10.5" fill="var(--content,#333)">노드 <tspan font-weight="600">여러 개</tspan> — 단 읽기만</text>

  <text x="26" y="256" font-size="11.5" font-weight="600" fill="#2f6ea8">ReadWriteMany (RWX)</text>
  <rect x="26" y="266" width="150" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="101" y="294" text-anchor="middle" font-size="9.5" fill="#2f6ea8">Node A ✓</text>
  <rect x="196" y="266" width="150" height="46" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <text x="271" y="294" text-anchor="middle" font-size="9.5" fill="#2f6ea8">Node B ✓</text>
  <ellipse cx="430" cy="272" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <rect x="396" y="272" width="68" height="26" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <ellipse cx="430" cy="298" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="430" y="292" text-anchor="middle" font-size="9.5" font-weight="600" fill="#2f6ea8">볼륨</text>
  <path d="M176,289 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <path d="M346,289 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="500" y="284" font-size="10.5" fill="var(--content,#333)">노드 <tspan font-weight="600">여러 개</tspan>가 읽고 쓴다</text>
  <text x="500" y="302" font-size="10" fill="var(--secondary,#888)">NFS 같은 공유 파일시스템</text>

  <text x="26" y="346" font-size="11.5" font-weight="600" fill="#c0392b">ReadWriteOncePod (RWOP)</text>
  <rect x="26" y="356" width="150" height="34" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.4"/>
  <rect x="36" y="362" width="60" height="22" rx="3" fill="#e6b3d9" stroke="#a05590"/>
  <text x="66" y="377" text-anchor="middle" font-size="9" fill="#5a2050">Pod ✓</text>
  <rect x="104" y="362" width="60" height="22" rx="3" fill="none" stroke="#c0392b" stroke-dasharray="3 2"/>
  <text x="134" y="377" text-anchor="middle" font-size="9" fill="#c0392b">Pod ✕</text>
  <rect x="196" y="356" width="150" height="34" rx="5" fill="none" stroke="#c0392b" stroke-width="1.2" stroke-dasharray="4 3"/>
  <text x="271" y="377" text-anchor="middle" font-size="9.5" fill="#c0392b">Node B ✕</text>
  <ellipse cx="430" cy="358" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <rect x="396" y="358" width="68" height="22" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <ellipse cx="430" cy="380" rx="34" ry="9" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="430" y="376" text-anchor="middle" font-size="9" font-weight="600" fill="#2f6ea8">볼륨</text>
  <path d="M176,373 H392" stroke="#2e9c6d" stroke-width="1.6" fill="none"/>
  <text x="500" y="374" font-size="10.5" fill="var(--content,#333)">클러스터 전체에서 <tspan font-weight="600">Pod 1개</tspan></text>
</svg>
</div>
{{< /rawhtml >}}

| 모드 | 약어 | 의미 |
|---|---|---|
| `ReadWriteOnce` | RWO | **노드 하나**가 읽고 쓴다. 같은 노드의 여러 Pod 는 가능 |
| `ReadOnlyMany` | ROX | 여러 노드가 읽기만 |
| `ReadWriteMany` | RWX | 여러 노드가 읽고 쓴다 |
| `ReadWriteOncePod` | RWOP | **Pod 하나**만. 클러스터 전체에서 하나 (1.22+, CSI 전용) |

공식 문서가 명시한다 — "ReadWriteOnce 는 **같은 노드에서 실행되는 여러 Pod 가 볼륨에 접근하는 것을 여전히 허용**한다."

그리고 **한 번에 하나의 모드로만 마운트된다.** NFS 처럼 여러 모드를 지원하는 볼륨이라도, 한 노드에서 RWO 로 쓰거나 여러 노드에서 ROX 로 쓸 뿐 동시에는 안 된다.

## 5. 회수 정책

PVC 를 지웠을 때 데이터를 어떻게 할지 정한다.

| 정책 | 동작 | 기본값 |
|---|---|---|
| `Retain` | PV 와 데이터를 그대로 둔다. 관리자가 손으로 처리 | **수동 생성 PV** |
| `Delete` | PV 객체와 실제 저장소(EBS 등)까지 삭제 | **동적 생성 PV** |
| `Recycle` | 볼륨을 비우고 재사용 (`rm -rf /thevolume/*`) | 사용 중단됨 |

기본값이 갈리는 지점이 함정이다.

```
관리자가 만든 PV   → Retain  → PVC 지워도 데이터 남음
동적으로 생긴 PV   → Delete  → PVC 지우면 디스크까지 사라짐
```

클라우드에서 PVC 를 무심코 지웠다가 DB 데이터가 함께 사라지는 사고가 여기서 나온다. 중요한 데이터라면 StorageClass 의 `reclaimPolicy` 를 `Retain` 으로 바꿔둔다.

`Recycle` 은 공식 문서가 **사용 중단(deprecated)** 을 명시하며 동적 준비를 권한다.

## 6. 관련 문서

- [Service](/wiki/service/) — Headless Service 와 StatefulSet 조합
- **StatefulSet** — Pod 마다 고유 PVC 를 갖는 워크로드 *(예정)*
- **CSI** — 저장소 플러그인 규격 *(예정)*

## 7. 출처

정의, 생명주기, 접근 모드, 회수 정책 기본값은 공식 문서 "Persistent Volumes" 에 근거한다.

> "A PersistentVolume (PV) is a piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using Storage Classes. It is a resource in the cluster just like a node is a cluster resource."

> "A PersistentVolumeClaim (PVC) is a request for storage by a user. It is similar to a Pod. Pods consume node resources and PVCs consume PV resources."

> "ReadWriteOnce -- the volume can be mounted as read-write by a single node. ReadWriteOnce access mode still can allow multiple pods to access the volume when the pods are running on the same node."

> "The default reclaim policy for manually created PersistentVolumes is Retain. The default reclaim policy for dynamically provisioned PersistentVolumes is Delete."

> "A volume can only be mounted using one access mode at a time, even if it supports many."

- [Kubernetes — Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Kubernetes — Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
