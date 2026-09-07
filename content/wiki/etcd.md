---
title: "etcd"
summary: "쿠버네티스가 모든 클러스터 데이터를 담아두는 키-값 저장소. 여기 없는 것은 클러스터에 없는 것이다."
categories: ["쿠버네티스", "아키텍처"]
tags: ["kubernetes", "etcd", "storage"]
aliases_search: ["에티시디", "이티씨디", "etcd 백업", "etcd 암호화"]
---

## 1. 개요

**etcd**는 쿠버네티스가 클러스터의 모든 데이터를 저장하는 키-값 저장소다. 공식 문서의 표현으로는 "**모든 클러스터 데이터를 위한 백킹 스토어**"이며, API 서버가 유일하게 말을 거는 상대다.

Pod, Deployment, Secret, ConfigMap, 노드 목록, RBAC 규칙 — `kubectl get` 으로 볼 수 있는 것은 전부 여기 들어 있다. **여기 없으면 클러스터에 없는 것이다.**

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 300" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="kubectl 과 스케줄러 kubelet 등 모든 컴포넌트가 API 서버를 통해서만 etcd 에 접근하고, etcd 는 클러스터의 유일한 진실 저장소다">
  <defs>
    <marker id="et-ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--content,#444)"/>
    </marker>
  </defs>

  <rect x="20" y="34" width="130" height="40" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="85" y="59" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">kubectl</text>
  <rect x="20" y="90" width="130" height="40" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="85" y="115" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">스케줄러</text>
  <rect x="20" y="146" width="130" height="40" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="85" y="171" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">컨트롤러</text>
  <rect x="20" y="202" width="130" height="40" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="85" y="227" text-anchor="middle" font-size="11.5" font-weight="600" fill="#5a3d18">kubelet</text>

  <rect x="270" y="70" width="150" height="136" rx="5" fill="none" stroke="#2f6ea8" stroke-width="1.5" stroke-width="1.6"/>
  <text x="345" y="128" text-anchor="middle" font-size="13" font-weight="600" fill="#1b3f63">API 서버</text>
  <text x="345" y="150" text-anchor="middle" font-size="10.5" fill="#1b3f63">유일한 통로</text>

  <ellipse cx="620" cy="86" rx="70" ry="18" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <rect x="550" y="86" width="140" height="106" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <ellipse cx="620" cy="192" rx="70" ry="18" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="620" y="128" text-anchor="middle" font-size="14" font-weight="600" fill="#2f6ea8">etcd</text>
  <text x="620" y="152" text-anchor="middle" font-size="10" fill="#8e44ad">Pod · Secret · RBAC</text>
  <text x="620" y="168" text-anchor="middle" font-size="10" fill="#8e44ad">노드 · ConfigMap …</text>

  <g stroke="var(--content,#444)" stroke-width="1.5" fill="none" marker-end="url(#et-ar)">
    <path d="M150,54 H200 V132 H266"/>
    <path d="M150,110 H200 V132 H266"/>
    <path d="M150,166 H200 V132 H266"/>
    <path d="M150,222 H200 V132 H266"/>
    <path d="M420,138 H546"/>
  </g>

  <text x="483" y="128" text-anchor="middle" font-size="10.5" font-style="italic" fill="var(--content,#333)">읽고 쓴다</text>
  <text x="345" y="240" text-anchor="middle" font-size="10.5" fill="#c0392b">아무도 etcd 에 직접 접근하지 않는다</text>

  <text x="380" y="282" text-anchor="middle" font-size="12" fill="var(--content,#333)">etcd 에 없으면 클러스터에 없는 것 — 여기가 유일한 진실</text>
</svg>
</div>
{{< /rawhtml >}}

## 2. 접근 권한의 무게

공식 문서가 한 문장으로 못 박는다.

> "Access to etcd is **equivalent to root permission** in the cluster."

etcd 를 읽을 수 있다는 것은 클러스터의 root 라는 뜻이다. RBAC 를 아무리 촘촘히 짜도 그것 역시 etcd 안의 데이터일 뿐이라, etcd 에 직접 닿는 사람 앞에서는 의미가 없다.

{{< rawhtml >}}
<div style="overflow-x:auto;margin:1.4rem 0;">
<svg viewBox="0 0 760 260" style="width:100%;min-width:640px;height:auto;font-family:inherit;" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="정상 경로는 RBAC 검사를 거치지만 etcd 에 직접 접근하면 모든 검사를 우회해 Secret 을 그대로 읽는다">
  <text x="190" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#2e9c6d">정상 경로</text>
  <text x="560" y="26" text-anchor="middle" font-size="12.5" font-weight="600" fill="#c0392b">etcd 직접 접근</text>

  <rect x="60" y="46" width="120" height="40" rx="4" fill="none" stroke="#d9a86a" stroke-width="1.5"/>
  <text x="120" y="71" text-anchor="middle" font-size="11" font-weight="600" fill="#5a3d18">사용자</text>
  <rect x="60" y="106" width="120" height="40" rx="4" fill="none" stroke="#2f6ea8" stroke-width="1.5"/>
  <text x="120" y="131" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">RBAC 검사</text>
  <rect x="60" y="166" width="120" height="40" rx="4" fill="none" stroke="#2e9c6d" stroke-width="1.5"/>
  <text x="120" y="191" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">허용된 것만</text>
  <path d="M120,86 V102" stroke="var(--content,#444)" stroke-width="1.5" fill="none"/>
  <path d="M120,146 V162" stroke="var(--content,#444)" stroke-width="1.5" fill="none"/>
  <text x="120" y="228" text-anchor="middle" font-size="10.5" fill="#2e9c6d">문을 통해 들어간다</text>

  <line x1="330" y1="40" x2="330" y2="240" stroke="var(--secondary,#888)" stroke-width="1" stroke-dasharray="4 4"/>

  <rect x="430" y="46" width="140" height="40" rx="4" fill="none" stroke="#c0392b" stroke-width="1.5"/>
  <text x="500" y="71" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">노드 접근 권한자</text>
  <rect x="430" y="166" width="140" height="40" rx="4" fill="none" stroke="#8e44ad" stroke-width="1.5"/>
  <text x="500" y="191" text-anchor="middle" font-size="11" font-weight="600" fill="#2f6ea8">etcd 데이터 전부</text>
  <path d="M500,86 V162" stroke="#c0392b" stroke-width="2" fill="none" stroke-dasharray="6 4"/>
  <text x="600" y="128" font-size="10.5" fill="#c0392b">RBAC 를 지나지 않는다</text>
  <text x="500" y="228" text-anchor="middle" font-size="10.5" fill="#c0392b">담을 넘는다</text>

  <text x="380" y="252" text-anchor="middle" font-size="12" fill="var(--content,#333)">RBAC 도 etcd 안의 데이터다 — 저장소에 직접 닿으면 규칙이 무의미해진다</text>
</svg>
</div>
{{< /rawhtml >}}

그래서 공식 문서는 **API 서버만 etcd 에 접근하게** 하고, TLS 클라이언트 인증으로 그 외를 막으라고 권한다.

## 3. Secret 과의 관계

Secret 은 **기본적으로 암호화되지 않은 채** etcd 에 저장된다. base64 는 인코딩이지 암호화가 아니다.

```
Secret 저장 경로
  kubectl apply → API 서버 → etcd 에 base64 그대로
                                    ↑ 여기를 읽으면 평문
```

대응은 두 층이다.

| 대책 | 막는 것 | 못 막는 것 |
|---|---|---|
| **etcd 암호화** (`EncryptionConfiguration`) | 디스크·백업 파일 유출 | 클러스터 관리자 (API 서버가 복호화해서 보여줌) |
| **Secret 을 아예 안 만들기** (CSI·사이드카 주입) | 관리자까지 | 파드 메모리에 접근하는 root |

"etcd 에 아무것도 남기지 않는다"는 접근이 나오는 배경이 이것이다. 저장하지 않으면 저장소를 털려도 나올 게 없다.

## 4. 백업

etcd 를 잃는 것은 **클러스터를 잃는 것**이다. 노드가 멀쩡해도 무엇을 어떻게 돌려야 하는지 아무도 모르게 된다.

```bash
ETCDCTL_API=3 etcdctl snapshot save snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

공식 문서는 백업 방법을 셋으로 나눈다 — **내장 스냅샷**, **볼륨 스냅샷**, **etcdctl 옵션을 이용한 스냅샷**. 관리형 클러스터(EKS·GKE·AKS)는 클라우드가 대신 하므로 사용자가 신경 쓰지 않는다.

## 5. 홀수 멤버

etcd 는 과반수 합의(Raft)로 동작하므로 멤버 수를 **홀수**로 둔다. 공식 문서는 프로덕션에서 **5대**를 권한다.

| 멤버 | 과반수 | 견딜 수 있는 장애 |
|---|---|---|
| 3 | 2 | 1대 |
| 4 | 3 | 1대 — 3대와 같다 |
| 5 | 3 | 2대 |
| 6 | 4 | 2대 — 5대와 같다 |

짝수를 더해도 장애 내성이 늘지 않는다. 4대는 3대와 똑같이 1대까지만 견디면서 통신 비용만 늘어난다.

## 6. 디스크 지연

공식 문서가 경고하는 지점이다.

> "Performance and stability of the cluster is sensitive to network and disk I/O. Any resource starvation can lead to heartbeat timeout, causing instability of the cluster."

etcd 는 쓰기를 디스크에 확정한 뒤 응답하므로 **디스크가 느리면 클러스터 전체가 느려진다.** 하트비트가 늦으면 리더 선출이 다시 일어나고, 그동안 API 서버가 멈춘 것처럼 보인다. 그래서 SSD 를 쓰고 **전용 머신에 격리**하라고 권한다.

## 7. 관련 문서

- [apiVersion](/wiki/apiversion/) — 저장되는 객체의 그룹과 버전
- [CRD](/wiki/crd/) — 커스텀 리소스도 결국 etcd 에 저장된다
- **Secret** — 암호화 설정과 대안 *(예정)*

## 8. 출처

역할, 접근 권한 경고, 홀수 멤버, 디스크 민감도는 공식 문서에 근거한다.

> "etcd is a consistent and highly-available key value store used as Kubernetes' backing store for all cluster data."

> "Access to etcd is equivalent to root permission in the cluster so ideally only the API server should have access to it."

> "You should run etcd as a cluster with an odd number of members. … A five-member cluster is recommended in production."

- [Kubernetes — Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Kubernetes — Cluster Components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes — Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
