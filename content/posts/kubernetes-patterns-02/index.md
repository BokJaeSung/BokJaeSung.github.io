---
title: "K8sPatterns.02 Predictable Demands"
date: 2026-06-24T09:00:00+09:00
tags: ["kubernetes", "cloud-native", "container"]
cover:
  image: 'images/cover.jpg'
  alt: 'K8sPatterns.02 Predictable Demands'
  relative: true
summary: "How to declare resource requirements and runtime dependencies so Kubernetes can schedule and manage containers predictably."
---

컨테이너화된 애플리케이션이 클라우드 네이티브 환경에서 제대로 동작하려면, 자신이 무엇을 필요로 하는지 명확하게 선언해야 한다. Kubernetes는 그 선언을 기반으로 어디에 배치할지, 언제 죽일지, 얼마나 허용할지를 결정한다. 이 챕터는 그 선언 방법 전반을 다룬다.

{{< rawhtml >}}
<details style="background:transparent;border:1px solid #30363d;border-radius:8px;padding:10px 16px;margin:1.2rem 0;font-family:inherit;">
<summary style="cursor:pointer;font-weight:600;font-size:14px;color:#8b949e;user-select:none;font-family:inherit;">목차 — Table of Contents</summary>
<div style="margin-top:10px;font-size:14px;line-height:2;font-family:inherit;">
  <div><a href="#0-overview" style="color:#c9d1d9;text-decoration:none;">0. Overview</a></div>
  <div><a href="#1-runtime-dependencies" style="color:#c9d1d9;text-decoration:none;">1. Runtime Dependencies</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#11-volume" style="color:#6e7681;text-decoration:none;">1.1 Volume</a></div>
    <div><a href="#12-hostport" style="color:#6e7681;text-decoration:none;">1.2 hostPort</a></div>
    <div><a href="#13-configmap--secret" style="color:#6e7681;text-decoration:none;">1.3 ConfigMap & Secret</a></div>
  </div>
  <div><a href="#2-resource-profiles" style="color:#c9d1d9;text-decoration:none;">2. Resource Profiles</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#21-compressible-vs-incompressible" style="color:#6e7681;text-decoration:none;">2.1 Compressible vs Incompressible</a></div>
    <div><a href="#22-requests--limits" style="color:#6e7681;text-decoration:none;">2.2 Requests & Limits</a></div>
    <div><a href="#23-quality-of-service" style="color:#6e7681;text-decoration:none;">2.3 Quality of Service</a></div>
    <div><a href="#24-best-practices" style="color:#6e7681;text-decoration:none;">2.4 Best Practices</a></div>
  </div>
  <div><a href="#3-pod-priority--preemption" style="color:#c9d1d9;text-decoration:none;">3. Pod Priority & Preemption</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#31-priorityclass" style="color:#6e7681;text-decoration:none;">3.1 PriorityClass</a></div>
    <div><a href="#32-preemptionpolicy-never" style="color:#6e7681;text-decoration:none;">3.2 preemptionPolicy: Never</a></div>
    <div><a href="#33-주의사항" style="color:#6e7681;text-decoration:none;">3.3 주의사항</a></div>
  </div>
  <div><a href="#4-project-resources" style="color:#c9d1d9;text-decoration:none;">4. Project Resources</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#41-resourcequota" style="color:#6e7681;text-decoration:none;">4.1 ResourceQuota</a></div>
    <div><a href="#42-limitrange" style="color:#6e7681;text-decoration:none;">4.2 LimitRange</a></div>
  </div>
  <div><a href="#5-capacity-planning" style="color:#c9d1d9;text-decoration:none;">5. Capacity Planning</a></div>
  <div><a href="#6-q--a" style="color:#c9d1d9;text-decoration:none;">6. Q & A</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#q1-cpu-limits는-왜-쓰지-않는가" style="color:#6e7681;text-decoration:none;">Q1. CPU limits는 왜 쓰지 않는가?</a></div>
    <div><a href="#q2-메모리는-왜-requests--limits인가" style="color:#6e7681;text-decoration:none;">Q2. 메모리는 왜 requests = limits인가?</a></div>
    <div><a href="#q3-qos와-우선순위의-차이" style="color:#6e7681;text-decoration:none;">Q3. QoS와 우선순위의 차이</a></div>
  </div>
</div>
</details>
{{< /rawhtml >}}

---

## 0. Overview

{{< rawhtml >}}
<style>
#k2-wrap{font-family:system-ui,sans-serif;background:transparent;padding:8px 0;margin:1.5rem 0;}
#k2-card{background:#fff;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.10);padding:16px;}
.k2-btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;transition:background .15s;}
.k2-btn-p{background:#1e1e1e;color:#fff;}.k2-btn-p:hover{background:#333;}
.k2-btn-s{background:transparent;color:#555;border:1px solid #ccc;}.k2-btn-s:hover{background:#f0f0f0;}
.k2-btn:disabled{opacity:.3;cursor:default;}
#k2-info{background:transparent;padding:10px 0 10px 14px;border-left:3px solid #1e1e1e;margin-top:14px;font-size:15px;font-weight:500;color:#1e1e1e;line-height:1.8;min-height:56px;}
.k2-g{transition:opacity 0.25s ease;}
</style>

<div id="k2-wrap">
  <div style="display:flex;gap:8px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">
    <button class="k2-btn k2-btn-s" id="k2-bb" onclick="k2B()">◀ 이전</button>
    <button class="k2-btn k2-btn-p" id="k2-bn" onclick="k2N()">다음 ▶</button>
    <button class="k2-btn k2-btn-s" onclick="k2R()" style="margin-left:4px;">↺ 초기화</button>
    <span id="k2-lbl" style="font-size:13px;color:#999;margin-left:4px;"></span>
  </div>
  <div id="k2-card" style="width:65%;margin:0 auto;min-width:260px;">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 516" style="width:100%;font-family:inherit;">
    <defs>
      <marker id="k2-arr" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
        <polygon points="0,0 8,3.5 0,7" fill="#999"/>
      </marker>
      <clipPath id="k2-api-clip">
        <rect x="55" y="108" width="390" height="134" rx="10"/>
      </clipPath>
      <clipPath id="k2-sc-clip">
        <rect x="55" y="270" width="390" height="130" rx="10"/>
      </clipPath>
    </defs>

    <!-- 애플리케이션 -->
    <g id="k2-app" class="k2-g">
      <rect x="160" y="20" width="180" height="44" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
      <text x="250" y="47" fill="#1e1e1e" font-size="15" text-anchor="middle" font-weight="600" font-family="inherit">애플리케이션</text>
    </g>

    <!-- Arrow 1 -->
    <g id="k2-a1" class="k2-g">
      <line x1="250" y1="64" x2="250" y2="106" stroke="#bbb" stroke-width="1.5" marker-end="url(#k2-arr)"/>
      <text x="258" y="89" fill="#aaa" font-size="12" font-family="inherit">kubectl apply</text>
    </g>

    <!-- API Server 외곽 -->
    <g id="k2-api-hdr" class="k2-g">
      <rect id="k2-api-border" x="55" y="108" width="390" height="134" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
      <text x="75" y="128" fill="#aaa" font-size="11" font-family="inherit">API Server</text>
    </g>

    <!-- LimitRange -->
    <g id="k2-lr" class="k2-g">
      <rect id="k2-lrf" x="55" y="133" width="390" height="52" fill="#fff" stroke="none" clip-path="url(#k2-api-clip)"/>
      <text x="75" y="152" fill="#1e1e1e" font-size="13" font-weight="600" font-family="inherit">LimitRange</text>
      <text x="90" y="168" fill="#666" font-size="12" font-family="inherit">기본값 주입 / 범위 초과 시 즉시 거절</text>
    </g>
    <line x1="55" y1="185" x2="445" y2="185" stroke="#e8e8e8" stroke-width="1"/>

    <!-- ResourceQuota -->
    <g id="k2-rq" class="k2-g">
      <rect id="k2-rqf" x="55" y="185" width="390" height="57" fill="#fff" stroke="none" clip-path="url(#k2-api-clip)"/>
      <text x="75" y="204" fill="#1e1e1e" font-size="13" font-weight="600" font-family="inherit">ResourceQuota</text>
      <text x="90" y="220" fill="#666" font-size="12" font-family="inherit">네임스페이스 총량 초과 시 즉시 거절</text>
      <text x="90" y="236" fill="#aaa" font-size="11" font-family="inherit">→ Scheduler까지 가지도 못함</text>
    </g>

    <!-- Arrow 2 -->
    <g id="k2-a2" class="k2-g">
      <line x1="250" y1="242" x2="250" y2="268" stroke="#bbb" stroke-width="1.5" marker-end="url(#k2-arr)"/>
      <text x="258" y="260" fill="#aaa" font-size="12" font-family="inherit">통과</text>
    </g>

    <!-- Scheduler 외곽 -->
    <g id="k2-sc-hdr" class="k2-g">
      <rect id="k2-sc-border" x="55" y="270" width="390" height="130" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
      <text x="75" y="290" fill="#aaa" font-size="11" font-family="inherit">Scheduler</text>
    </g>

    <!-- Runtime Dependencies -->
    <g id="k2-rd" class="k2-g">
      <rect id="k2-rdf" x="55" y="295" width="390" height="50" fill="#fff" stroke="none" clip-path="url(#k2-sc-clip)"/>
      <text x="75" y="314" fill="#1e1e1e" font-size="13" font-weight="600" font-family="inherit">Runtime Dependencies</text>
      <text x="90" y="330" fill="#666" font-size="12" font-family="inherit">Volume, hostPort, ConfigMap/Secret → 노드 필터링</text>
    </g>
    <line x1="55" y1="345" x2="445" y2="345" stroke="#e8e8e8" stroke-width="1"/>

    <!-- PriorityClass -->
    <g id="k2-pc" class="k2-g">
      <rect id="k2-pcf" x="55" y="345" width="390" height="55" fill="#fff" stroke="none" clip-path="url(#k2-sc-clip)"/>
      <text x="75" y="365" fill="#1e1e1e" font-size="13" font-weight="600" font-family="inherit">PriorityClass</text>
      <text x="90" y="381" fill="#666" font-size="12" font-family="inherit">우선순위 높은 Pod 먼저 배치, 자리 없으면 선점</text>
    </g>

    <!-- Arrow 3 -->
    <g id="k2-a3" class="k2-g">
      <line x1="250" y1="400" x2="250" y2="424" stroke="#bbb" stroke-width="1.5" marker-end="url(#k2-arr)"/>
      <text x="258" y="417" fill="#aaa" font-size="12" font-family="inherit">배치</text>
    </g>

    <!-- Kubelet -->
    <g id="k2-kl" class="k2-g">
      <rect x="55" y="426" width="390" height="80" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
      <text x="250" y="451" fill="#1e1e1e" font-size="14" text-anchor="middle" font-weight="700" font-family="inherit">Kubelet / Node</text>
      <text x="75" y="470" fill="#666" font-size="12" font-family="inherit">→ QoS 기반 종료 순서 결정</text>
      <text x="90" y="486" fill="#aaa" font-size="11" font-family="inherit">BestEffort → Burstable → Guaranteed 순으로 종료</text>
    </g>
  </svg>
  </div>
  <div id="k2-info"></div>
</div>

<script>
(function(){
  const ST=[
    {a:null, info:'YAML 선언 전. Kubernetes는 아직 아무것도 모른다.'},
    {a:'k2-app', info:'애플리케이션이 YAML을 작성한다. requests/limits, PriorityClass, Volume 등을 선언하는 과정이다.'},
    {a:'k2-a1', info:'<code style="background:#f0f0f0;padding:1px 6px;border-radius:4px;color:#1e1e1e;">kubectl apply</code>로 YAML이 API Server에 전달된다.'},
    {a:'k2-lr', info:'LimitRange 체크 (API Server). requests/limits를 명시하지 않았으면 기본값을 자동 주입한다. 설정 범위를 벗어나면 이 시점에서 즉시 거절된다.'},
    {a:'k2-rq', info:'ResourceQuota 체크 (API Server). 네임스페이스 총 사용량이 한도를 초과하면 즉시 거절된다. Scheduler까지 가지도 못한다.'},
    {a:'k2-a2', info:'API Server 단계를 통과한 Pod 오브젝트가 etcd에 저장된다. Scheduler가 이를 감지하고 배치 작업을 시작한다.'},
    {a:'k2-rd', info:'Runtime Dependencies 확인 (Scheduler). Volume 마운트 가능 여부, hostPort 충돌, ConfigMap/Secret 존재 여부를 검사한다. 조건을 만족하는 노드를 필터링한다.'},
    {a:'k2-pc', info:'PriorityClass 적용 (Scheduler). 우선순위가 높은 Pod를 먼저 배치한다. 자리가 없으면 낮은 우선순위 Pod를 선점(Preemption)하여 자리를 만든다.'},
    {a:'k2-a3', info:'Scheduler가 최적 노드를 선택하고 Pod를 바인딩한다.'},
    {a:'k2-kl', info:'Kubelet이 Pod를 실행한다. 이후 노드 리소스가 부족하면 QoS 등급 기준으로 종료 순서를 결정한다: BestEffort → Burstable → Guaranteed.'},
  ];
  const GS=['k2-app','k2-a1','k2-lr','k2-rq','k2-a2','k2-rd','k2-pc','k2-a3','k2-kl'];
  const API_STEPS=['k2-lr','k2-rq'];
  const SC_STEPS=['k2-rd','k2-pc'];
  const FILLS={'k2-lr':'k2-lrf','k2-rq':'k2-rqf','k2-rd':'k2-rdf','k2-pc':'k2-pcf'};
  let cur=0;

  function render(){
    const s=ST[cur];
    GS.forEach(id=>{
      const el=document.getElementById(id);
      if(el) el.style.opacity = s.a===null ? '1' : (s.a===id ? '1' : '0.18');
    });
    const apiHdr=document.getElementById('k2-api-hdr');
    if(apiHdr) apiHdr.style.opacity = (!s.a || API_STEPS.includes(s.a)) ? '1' : '0.18';
    const scHdr=document.getElementById('k2-sc-hdr');
    if(scHdr) scHdr.style.opacity = (!s.a || SC_STEPS.includes(s.a)) ? '1' : '0.18';
    Object.entries(FILLS).forEach(([gid,fid])=>{
      const f=document.getElementById(fid);
      if(!f) return;
      const active=s.a===gid;
      f.setAttribute('fill', active ? '#f4f4f4' : '#fff');
      f.setAttribute('stroke', active ? '#aaa' : 'none');
      f.setAttribute('stroke-width','1.5');
    });
    const apiBorder=document.getElementById('k2-api-border');
    if(apiBorder) apiBorder.setAttribute('stroke', API_STEPS.includes(s.a) ? '#1e1e1e' : '#e0e0e0');
    const scBorder=document.getElementById('k2-sc-border');
    if(scBorder) scBorder.setAttribute('stroke', SC_STEPS.includes(s.a) ? '#1e1e1e' : '#e0e0e0');
    document.getElementById('k2-info').innerHTML=s.info;
    document.getElementById('k2-lbl').textContent=`${cur} / ${ST.length-1}`;
    document.getElementById('k2-bb').disabled=cur===0;
    document.getElementById('k2-bn').disabled=cur===ST.length-1;
  }
  window.k2N=()=>{if(cur<ST.length-1){cur++;render();}};
  window.k2B=()=>{if(cur>0){cur--;render();}};
  window.k2R=()=>{cur=0;render();};
  render();
})();
</script>
{{< /rawhtml >}}

Kubernetes는 ESP가 아니다. 애플리케이션이 무엇을 필요로 하는지 직접 알려줘야만 적절한 노드에 배치하고 안정적으로 관리할 수 있다.

---

## 1. Runtime Dependencies

### 1.1 Volume

컨테이너의 파일시스템은 컨테이너가 종료되면 함께 사라진다. 데이터를 보존하려면 Volume을 선언해야 한다.

emptyDir vs PersistentVolume

| | emptyDir | PersistentVolume |
|---|---|---|
| 저장 위치 | 노드 로컬 디스크 (또는 RAM) | 노드 외부 스토리지 |
| Pod 삭제 시 | 함께 삭제 | 유지 |
| 컨테이너 재시작 시 | 유지 | 유지 |
| 주 용도 | 임시 파일, 컨테이너 간 공유 | DB 데이터, 영구 보존 필요 데이터 |

emptyDir은 Pod가 살아있는 동안만 존재한다. 컨테이너끼리 파일을 주고받거나 임시 캐시를 저장할 때 적합하다. `medium: Memory`를 설정하면 RAM에 저장되어 속도가 빠르지만 용량은 제한된다.

```yaml
volumes:
- name: temp-storage
  emptyDir: {}          # 기본: 노드 디스크
  # emptyDir:
  #   medium: Memory    # RAM에 저장
```

PersistentVolume(PV)은 Pod가 삭제되어도 데이터가 남는다. PVC(PersistentVolumeClaim)를 통해 연결한다.

```yaml
# Example 2-1. Dependency on a PersistentVolume
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    volumeMounts:
    - mountPath: "/logs"   # 컨테이너 안에서 /logs 경로에 연결
      name: log-volume
  volumes:
  - name: log-volume
    persistentVolumeClaim:
      claimName: random-generator-log   # 이 PVC가 없으면 Pod 실행 안 됨
```

스케줄러는 Pod가 필요로 하는 볼륨의 종류를 확인한다. 클러스터의 어떤 노드도 해당 볼륨을 제공하지 못하면 Pod는 아예 스케줄링되지 않는다.

> PVC는 Pod yaml과 별도로 먼저 생성해야 한다. 실제 실행 시에는 PVC yaml을 먼저 apply한 뒤 Pod yaml을 apply하는 순서를 지킨다.

---

### 1.2 hostPort

`hostPort`는 컨테이너 포트를 노드의 특정 포트에 직접 연결하는 설정이다.

```yaml
containers:
- name: my-app
  image: my-app:1.0
  ports:
  - containerPort: 8080
    hostPort: 80        # 노드의 80포트와 직접 연결
```

문제는 `hostPort`를 설정하면 Kubernetes가 클러스터 전체 노드에 해당 포트를 예약한다는 점이다. 결과적으로 노드당 해당 Pod를 최대 1개만 배치할 수 있고, 스케일아웃 시 노드 수만큼만 Pod를 늘릴 수 있다.

이러한 이유로 `hostPort`는 안티패턴으로 간주되며, 포트 관리는 Service(NodePort, LoadBalancer)를 통해 하는 것이 권장된다.

{{< rawhtml >}}
<div style="margin:1.5rem 0;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 870 430" style="width:100%;font-family:system-ui,sans-serif;">
  <defs>
    <marker id="hp-arr" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
      <polygon points="0,0 8,3.5 0,7" fill="#aaa"/>
    </marker>
    <marker id="hp-arr-g" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
      <polygon points="0,0 8,3.5 0,7" fill="#4a9d6f"/>
    </marker>
    <filter id="hp-sh" x="-10%" y="-10%" width="120%" height="135%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.08"/>
    </filter>
  </defs>

  <!-- ===== ARROWS (맨 앞 = 카드 아래) ===== -->
  <line x1="220" y1="114" x2="220" y2="142" stroke="#bbb" stroke-width="1.5" marker-end="url(#hp-arr)"/>
  <line x1="220" y1="166" x2="220" y2="178" stroke="#bbb" stroke-width="1.5" marker-end="url(#hp-arr)"/>
  <text x="228" y="176" fill="#bbb" font-size="10" font-family="inherit">:80</text>
  <line x1="640" y1="114" x2="640" y2="142" stroke="#bbb" stroke-width="1.5" marker-end="url(#hp-arr)"/>
  <line x1="600" y1="192" x2="575" y2="262" stroke="#4a9d6f" stroke-width="1.5" marker-end="url(#hp-arr-g)"/>
  <line x1="640" y1="192" x2="615" y2="320" stroke="#4a9d6f" stroke-width="1.5" marker-end="url(#hp-arr-g)"/>
  <line x1="680" y1="192" x2="655" y2="378" stroke="#4a9d6f" stroke-width="1.5" marker-end="url(#hp-arr-g)"/>

  <!-- Divider -->
  <line x1="435" y1="8" x2="435" y2="422" stroke="#e8e8e8" stroke-width="1.5" stroke-dasharray="5,4"/>

  <!-- ===== LEFT: hostPort ===== -->
  <rect x="130" y="10" width="180" height="26" rx="7" fill="#fff0f0" stroke="#ffcccc" stroke-width="1"/>
  <text x="220" y="28" fill="#c0392b" font-size="13" font-weight="700" text-anchor="middle" font-family="inherit">hostPort</text>
  <rect x="90" y="44" width="260" height="22" rx="6" fill="#fff5f5" stroke="#ffcccc" stroke-width="1"/>
  <text x="220" y="59" fill="#c0392b" font-size="11" text-anchor="middle" font-family="inherit">⚠  노드당 Pod 1개 — 스케일아웃 불가</text>

  <rect x="120" y="78" width="200" height="36" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="220" y="101" fill="#1e1e1e" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">External Traffic  :80</text>

  <!-- Node 1 (active) -->
  <rect x="38" y="144" width="364" height="114" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="56" y="163" fill="#aaa" font-size="11" font-family="inherit">Node  192.168.1.1</text>
  <rect x="120" y="180" width="200" height="36" rx="8" fill="#f0f7ff" stroke="#ccdff5" stroke-width="1"/>
  <text x="220" y="203" fill="#1e5fa8" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">Pod A  :8080</text>
  <text x="56" y="244" fill="#27ae60" font-size="11" font-family="inherit">✓  직접 접근 가능</text>

  <!-- Node 2 (empty) -->
  <rect x="38" y="274" width="364" height="44" rx="10" fill="#f9f9f9" stroke="#ebebeb" stroke-width="1"/>
  <text x="56" y="293" fill="#ccc" font-size="11" font-family="inherit">Node  192.168.1.2</text>
  <text x="56" y="310" fill="#ccc" font-size="11" font-family="inherit">✕  Pod 없음 — 이 노드 IP로는 접근 불가</text>

  <!-- Node 3 (empty) -->
  <rect x="38" y="330" width="364" height="44" rx="10" fill="#f9f9f9" stroke="#ebebeb" stroke-width="1"/>
  <text x="56" y="349" fill="#ccc" font-size="11" font-family="inherit">Node  192.168.1.3</text>
  <text x="56" y="366" fill="#ccc" font-size="11" font-family="inherit">✕  Pod 없음 — 이 노드 IP로는 접근 불가</text>

  <!-- ===== RIGHT: Service ===== -->
  <rect x="550" y="10" width="180" height="26" rx="7" fill="#f0fff4" stroke="#c0e8cc" stroke-width="1"/>
  <text x="640" y="28" fill="#218c4a" font-size="13" font-weight="700" text-anchor="middle" font-family="inherit">Service</text>
  <rect x="468" y="44" width="344" height="22" rx="6" fill="#f0fff4" stroke="#c0e8cc" stroke-width="1"/>
  <text x="640" y="59" fill="#218c4a" font-size="11" text-anchor="middle" font-family="inherit">✓  자동 로드밸런싱 · 어느 노드든 접근 가능</text>

  <rect x="540" y="78" width="200" height="36" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="640" y="101" fill="#1e1e1e" font-size="13" font-weight="600" text-anchor="middle" font-family="inherit">External Traffic</text>

  <!-- Service ClusterIP -->
  <rect x="480" y="144" width="320" height="48" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="640" y="166" fill="#1e1e1e" font-size="13" font-weight="700" text-anchor="middle" font-family="inherit">Service (ClusterIP)</text>
  <text x="640" y="183" fill="#999" font-size="11" text-anchor="middle" font-family="inherit">kube-proxy가 Pod로 분산</text>

  <!-- Pod A (Node 1) -->
  <rect x="450" y="264" width="280" height="44" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="466" y="283" fill="#aaa" font-size="11" font-family="inherit">Node  192.168.1.1</text>
  <text x="466" y="300" fill="#1e1e1e" font-size="12" font-weight="600" font-family="inherit">Pod A  :8080</text>

  <!-- Pod B (Node 2) -->
  <rect x="450" y="322" width="280" height="44" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="466" y="341" fill="#aaa" font-size="11" font-family="inherit">Node  192.168.1.2</text>
  <text x="466" y="358" fill="#1e1e1e" font-size="12" font-weight="600" font-family="inherit">Pod B  :8080</text>

  <!-- Pod C (Node 3) -->
  <rect x="450" y="380" width="280" height="44" rx="10" fill="#fff" stroke="#e0e0e0" stroke-width="1" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.09))"/>
  <text x="466" y="399" fill="#aaa" font-size="11" font-family="inherit">Node  192.168.1.3</text>
  <text x="466" y="416" fill="#1e1e1e" font-size="12" font-weight="600" font-family="inherit">Pod C  :8080</text>

</svg>
</div>
{{< /rawhtml >}}

---

### 1.3 ConfigMap & Secret

거의 모든 애플리케이션은 설정 정보를 필요로 한다. Kubernetes는 ConfigMap과 Secret을 통해 이를 관리한다.

| | ConfigMap | Secret |
|---|---|---|
| 용도 | 일반 설정값 | 민감한 정보 (비밀번호, API 키) |
| 보안 수준 | 낮음 | 상대적으로 높음 |
| 소비 방식 | 환경변수 또는 파일 | 동일 |

```yaml
# Example 2-2. Dependency on a ConfigMap
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
    env:
    - name: PATTERN
      valueFrom:
        configMapKeyRef:
          name: random-generator-config   # ConfigMap 이름
          key: pattern                    # 가져올 키
```

볼륨과의 차이점이 있다. ConfigMap이 없을 때 Pod는 스케줄링은 되지만 실행되지 않는다. 겉으로는 Pod가 존재하는 것처럼 보여 원인을 찾기 어려울 수 있다.

| 의존성 | 없을 때 결과 |
|---|---|
| Volume (PV) | 스케줄링 자체 안 됨 |
| ConfigMap / Secret | 스케줄링은 됨, 실행만 안 됨 |

---

## 2. Resource Profiles

### 2.1 Compressible vs Incompressible

Kubernetes에서 리소스는 두 가지로 분류된다.

| | Compressible (압축 가능) | Incompressible (압축 불가능) |
|---|---|---|
| 예시 | CPU, 네트워크 대역폭 | 메모리 |
| 부족 시 | 스로틀링 (느려짐) | Pod 종료 (OOMKill) |
| 조절 가능 여부 | 가능 | 불가능 |

CPU는 시분할 방식으로 여러 프로세스가 나눠 사용할 수 있다. 부족하면 느려질 뿐 죽지 않는다. 반면 메모리는 이미 점유된 공간을 강제로 회수할 방법이 없어, 초과 시 프로세스를 종료하는 것 외에 선택지가 없다.

---

### 2.2 Requests & Limits

```yaml
# Example 2-3
resources:
  requests:
    cpu: 100m       # 최소 보장량 (스케줄러가 이 값으로 배치 결정)
    memory: 200Mi
  limits:
    memory: 200Mi   # 최대 허용량 (CPU limits는 의도적으로 생략)
```

- requests: 스케줄러가 배치 결정에 사용하는 값. 이 값을 기준으로 노드에 여유 공간이 있는지 판단한다.
- limits: 컨테이너가 사용할 수 있는 최대치. 초과 시 CPU는 스로틀링, 메모리는 Pod 종료.

CPU 단위인 `m`은 밀리코어(millicore)를 의미한다. `1000m = 1 CPU 코어`, `100m = 0.1 코어`다.

---

### 2.3 Quality of Service

requests와 limits 설정 방식에 따라 Pod의 QoS 등급이 자동으로 결정된다. 이 등급은 노드 리소스 부족 시 Kubelet이 Pod를 종료하는 순서에 영향을 준다.

| QoS 등급 | 조건 | 종료 우선순위 |
|---|---|---|
| Best-Effort | requests, limits 모두 미설정 | 가장 먼저 종료 |
| Burstable | requests < limits | 중간 |
| Guaranteed | requests = limits | 마지막 |

---

### 2.4 Best Practices

| 리소스 | requests | limits |
|---|---|---|
| CPU | 설정 | 설정하지 않음 |
| Memory | 설정 | requests와 동일하게 설정 |

CPU limits를 설정하면 노드에 여유 CPU가 있어도 그 이상 사용하지 못해 낭비가 발생한다. 메모리는 limits를 requests와 동일하게 설정해 Guaranteed 등급을 확보하고 예상치 못한 OOMKill을 방지한다.

---

## 3. Pod Priority & Preemption

QoS가 "죽는 순서"를 결정한다면, Priority는 "배치되는 순서"를 결정한다.

### 3.1 PriorityClass

```yaml
# Example 2-4. Pod priority
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000                  # 숫자가 클수록 높은 우선순위
globalDefault: false         # true로 설정 시 우선순위 미지정 Pod의 기본값
description: "This is a very high-priority Pod class"
---
apiVersion: v1
kind: Pod
metadata:
  name: random-generator
spec:
  containers:
  - image: k8spatterns/random-generator:1.0
    name: random-generator
  priorityClassName: high-priority   # PriorityClass 연결
```

노드에 자리가 없을 때 스케줄러는 낮은 우선순위 Pod를 강제로 종료(선점)하고 높은 우선순위 Pod를 배치한다. 이미 실행 중인 Pod도 선점 대상이 될 수 있다.

> 선점 시 스케줄러는 QoS를 고려하지 않는다. Guaranteed Pod라도 우선순위가 낮으면 종료될 수 있다. 중요한 Pod는 QoS와 우선순위를 모두 높게 설정해야 한다.

---

### 3.2 preemptionPolicy: Never

우선순위는 높이되 기존 Pod를 죽이고 싶지 않을 때 사용한다.

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-no-evict
value: 1000
preemptionPolicy: Never   # 선점 비활성화
```

줄 서는 순서는 VIP이지만, 이미 앉아있는 사람은 쫓아내지 않는 방식이다.

---

### 3.3 주의사항

- 높은 우선순위 Pod의 선점이 `PodDisruptionBudget`을 무시할 수 있다. 예를 들어 "최소 2개 이상 살아있어야 한다"고 설정된 DB 클러스터가 선점으로 인해 모두 종료될 수 있다.

  > Kubernetes 1.22+ 이후 스케줄러는 선점 시 PDB를 존중하도록 개선되었다. "완전히 무시한다"는 설명은 구버전 기준이며, 현재는 엣지 케이스에서 PDB 위반이 발생할 수 있는 정도로 이해하는 것이 정확하다.
- 악의적인 사용자가 최고 우선순위로 Pod를 대량 생성하는 것을 막기 위해 `ResourceQuota`로 PriorityClass 사용을 제한할 수 있다.
- 우선순위 변경은 클러스터 전체에 영향을 미칠 수 있어 신중하게 운영해야 한다.

---

## 4. Project Resources

여러 팀이 하나의 클러스터를 공유할 때, 한 팀이 자원을 독점하지 못하도록 제어하는 도구들이다.

### 4.1 ResourceQuota

네임스페이스 전체의 리소스 총량을 제한한다.

```yaml
# Example 2-5. Definition of resource constraints
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
  namespace: default
spec:
  hard:
    pods: 4              # 이 네임스페이스에서 Pod 최대 4개
    limits.memory: 5Gi  # 모든 Pod의 메모리 limits 합계 최대 5GB
```

| | ResourceQuota | Pod requests/limits |
|---|---|---|
| 범위 | 네임스페이스 전체 합계 | Pod 개별 |
| 설정 주체 | 클러스터 관리자 | 개발자 |

---

### 4.2 LimitRange

개별 컨테이너의 리소스 범위와 기본값을 강제한다.

```yaml
# Example 2-6. Definition of allowed and default resource usage limits
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: default
spec:
  limits:
  - min:
      memory: 250Mi
      cpu: 500m
    max:
      memory: 2Gi
      cpu: 2
    default:                # limits 미설정 시 자동 적용
      memory: 500Mi
      cpu: 500m
    defaultRequest:         # requests 미설정 시 자동 적용
      memory: 250Mi
      cpu: 250m
    maxLimitRequestRatio:   # limits / requests 최대 비율
      memory: 2             # 메모리 limits는 requests의 2배까지
      cpu: 4                # CPU limits는 requests의 4배까지
    type: Container
```

개발자가 실수로 리소스를 선언하지 않아도 LimitRange가 기본값을 자동으로 적용한다. requests와 limits의 격차가 너무 크면 오버커밋이 발생해 성능이 저하될 수 있으므로 `maxLimitRequestRatio`로 비율을 제한하는 것이 중요하다.

---

## 5. Capacity Planning

환경마다 컨테이너 수와 리소스 프로파일이 다르다.

| 환경 | 권장 QoS | Pod 종료 시 |
|---|---|---|
| 개발/테스트 | Best-Effort, Burstable | 큰 문제 없음 |
| 운영 | Guaranteed (일부 Burstable) | 클러스터 용량 증설 신호 |

전체 필요 자원을 계산할 때는 실제 앱 리소스 외에 다음을 반드시 포함해야 한다.

- 오토스케일링 여유분
- 빌드 작업용 리소스
- 인프라 컨테이너 리소스

각 서비스의 리소스 선언이 정확하게 되어 있어야 전체 인프라 계획을 데이터 기반으로 세울 수 있다.

---

## 6. Q & A

### Q1. CPU limits는 왜 쓰지 않는가?

CPU는 압축 가능한 자원이다. 노드에 여유 CPU가 있을 때 limits를 설정하면 그 여유분을 사용하지 못하고 낭비된다. limits 없이 requests만 설정하면 최소 보장량은 확보하면서 여유 CPU가 있을 때 더 사용할 수 있다.

피자 파티 비유로 설명하면, 손님마다 최소 2조각을 보장하되(requests) 남은 피자는 누구든 더 먹을 수 있게(limits 없음) 하는 방식이다.

### Q2. 메모리는 왜 requests = limits인가?

메모리는 압축 불가능한 자원이다. requests보다 limits를 크게 설정하면 실제 메모리가 부족할 때 OOM Killer가 해당 Pod가 아닌 무관한 Pod를 종료시킬 수 있다. requests = limits로 설정하면 메모리를 초과한 Pod는 자기 자신만 죽고 다른 Pod에 영향을 주지 않는다. 이것이 Guaranteed QoS 등급을 확보하는 방법이기도 하다.

### Q3. QoS와 우선순위의 차이

두 개념은 독립적이며 담당하는 상황이 다르다.

| | QoS | Priority |
|---|---|---|
| 담당 | Kubelet | Scheduler |
| 상황 | 노드 메모리 부족 시 | 새 Pod 배치 시 자리 필요 시 |
| 기준 | QoS 등급 → 우선순위 순 | 우선순위만 (QoS 무시) |

중요한 Pod는 QoS(Guaranteed)와 우선순위(high-priority) 모두 높게 설정해야 두 상황 모두에서 보호받을 수 있다.