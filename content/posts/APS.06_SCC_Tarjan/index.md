---
title: "APS.05 Tarjan's SCC Algorithm"
date: 2026-04-14T09:00:00+09:00
tags: ["알고리즘", "그래프", "SCC", "Tarjan", "DFS", "강한연결요소"]
cover:
  image: 'images/cover.jpg'
  alt: 'APS.05 Tarjan SCC Algorithm'
  relative: true
summary: "DFS 한 번으로 강한 연결 요소를 찾는 Tarjan 알고리즘의 원리를 비유, 시각화, Q&A로 완전히 이해한다."
---

## 1. 강한 연결 요소 (SCC) 란?

방향 그래프에서 **Strongly Connected Component (SCC)** 란, 그 안의 **모든 노드 쌍** $(u, v)$ 에 대해 $u \to v$ 경로와 $v \to u$ 경로가 모두 존재하는 **극대 부분 그래프**다.

쉽게 말해, SCC 안의 어떤 노드에서 출발해도 다른 모든 노드에 도달할 수 있다 — **서로 순환할 수 있는 노드 그룹**이다.

$$\forall\, u, v \in \text{SCC}: \quad u \leadsto v \;\text{and}\; v \leadsto u$$

| 그래프 | SCC들 |
|--------|-------|
| `0→1→2→0, 1→3` | `{0,1,2}`, `{3}` |
| `0→1, 1→0, 2→3, 3→2, 1→2` | `{0,1}`, `{2,3}` |
| `0→1→2→3` (일자) | `{0}`, `{1}`, `{2}`, `{3}` |

---

## 2. Brute Force — $O(V^3)$

모든 노드 쌍 $(u, v)$ 에 대해 BFS/DFS로 도달 가능성을 체크한다.

$$\text{같은 SCC} \iff u \leadsto v \;\text{and}\; v \leadsto u$$

**시간복잡도:** 각 쌍마다 $O(V+E)$ × $V^2$ 쌍 → $O(V^2(V+E)) \approx O(V^3)$

$V = 10{,}000$ 이면 $10^{12}$ — 불가능.

---

## 3. Tarjan 알고리즘 — $O(V+E)$

**DFS 한 번**으로 모든 SCC를 찾는다. 핵심 아이디어를 세 줄로 요약하면:

1. DFS 방문 순서대로 **발견 번호(disc)** 를 붙인다.
2. 각 노드가 도달할 수 있는 **가장 오래된 조상의 번호(low)** 를 추적한다.
3. $\text{disc}[v] = \text{low}[v]$ 이면 $v$ 가 하나의 SCC의 **루트**다.

### 3.1 핵심 변수

| 변수 | 의미 | 초기값 | 변하는가? |
|------|------|--------|-----------|
| `disc[v]` | $v$ 의 DFS 발견 순서 | `timer++` | **불변** (한 번 확정) |
| `low[v]` | $v$ 의 서브트리에서 도달 가능한 가장 작은 disc | `disc[v]` | **감소만** (min으로 갱신) |
| `onStack[v]` | $v$ 가 현재 스택에 있는가 | `True` (방문 시) | SCC 완성 시 `False` |
| `stack` | 현재 탐색 경로의 노드들 | 빈 스택 | push/pop |

`disc[v]` 는 **"몇 번째로 발견됐는가"** 라는 사실이다. 이미 일어난 일이므로 절대 바뀌지 않는다.

`low[v]` 는 **"내 팀이 거슬러 올라갈 수 있는 최고 선배 번호"** 이다. 초기값은 "일단 나 자신"이고, back edge를 발견하거나 자식이 정보를 전파해올 때만 `min()` 으로 감소한다.

`onStack[v]` 는 **"아직 SCC가 확정 안 된 노드"** 를 구분한다. 스택에 있으면 조상(= low 갱신 대상), 스택에서 빠졌으면 이미 다른 SCC에 확정된 남(= 무시 대상).

---

### 3.2 알고리즘 코드

```python
timer = 0
disc = [-1] * V
low  = [0] * V
on_stack = [False] * V
stack = []
sccs = []

def dfs(u):
    global timer
    disc[u] = low[u] = timer      # ❶ 초기화: disc와 low를 timer로
    timer += 1
    stack.append(u)
    on_stack[u] = True

    for v in graph[u]:
        if disc[v] == -1:          # ❷ tree edge: 미방문
            dfs(v)
            low[u] = min(low[u], low[v])   # 자식 결과 흡수
        elif on_stack[v]:          # ❸ back edge: 스택에 있는 조상
            low[u] = min(low[u], disc[v])  # disc값만 참고

    if disc[u] == low[u]:          # ❹ SCC 루트 발견!
        scc = []
        while True:
            w = stack.pop()
            on_stack[w] = False
            scc.append(w)
            if w == u:
                break
        sccs.append(scc)
```

**4가지 핵심 지점:**

- **❶ 초기화** — `disc[u] = low[u] = timer++`. 방문 즉시 번호를 붙인다. `disc` 가 `-1`이 아니면 "방문했음"을 의미하므로 별도 `visited` 배열이 필요 없다.

- **❷ tree edge** — `dfs(v)` 를 호출해서 v의 서브트리 전체를 탐색한 뒤, `low[v]` (최종 결과)를 `low[u]` 에 흡수한다.

- **❸ back edge** — `dfs(v)` 를 호출하지 않는다. v는 지금 콜스택에 살아있는 조상이므로, v에 "닿을 수 있다"는 사실만 기록하면 된다 → `disc[v]` 만 참고.

- **❹ SCC 체크** — 모든 이웃 탐색이 끝나 `low[u]` 가 확정된 뒤, `disc[u] == low[u]` 이면 스택에서 u까지 pop하여 SCC를 만든다.

---

### 3.3 단계별 실행 시각화

그래프 `0→1→2→0, 1→3` 에서 타잔 알고리즘의 실행을 단계별로 확인한다.

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <button onclick="tjBack()" id="tj-back" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">◀ 이전</button>
  <button onclick="tjNext()" id="tj-next" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">다음 ▶</button>
  <span id="tj-step-lbl" style="font-family:'JetBrains Mono',monospace;font-size:13px;color:#8090a0;">단계 1 / 9</span>
</div>
<div style="display:flex;gap:12px;flex-wrap:wrap;">
  <canvas id="tj-graph" style="flex:1;min-width:260px;border-radius:8px;background:#1a1d27;display:block;aspect-ratio:320/280;"></canvas>
  <div style="flex:1;min-width:220px;">
    <div style="background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;margin-bottom:8px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5c6bc0;margin-bottom:6px;">스택</div>
      <div id="tj-stack" style="font-family:'JetBrains Mono',monospace;font-size:15px;color:#b0b8d0;min-height:28px;">[]</div>
    </div>
    <div style="background:#1a1d27;border-left:3px solid #69f0ae;border-radius:6px;padding:10px 14px;margin-bottom:8px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#69f0ae;margin-bottom:6px;">발견된 SCC</div>
      <div id="tj-scc" style="font-family:'JetBrains Mono',monospace;font-size:15px;color:#b0b8d0;min-height:28px;">없음</div>
    </div>
    <div style="background:#1a1d27;border-left:3px solid #ffd740;border-radius:6px;padding:10px 14px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#ffd740;margin-bottom:6px;">콜스택</div>
      <div id="tj-callstack" style="font-family:'JetBrains Mono',monospace;font-size:14px;color:#b0b8d0;min-height:28px;line-height:1.6;"></div>
    </div>
  </div>
</div>
<div style="background:#1a1d27;border-left:3px solid #ce93d8;border-radius:6px;padding:10px 14px;margin-top:10px;">
  <div id="tj-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;line-height:1.8;"></div>
</div>
</div>
<script>
(function(){
const cv=document.getElementById('tj-graph');
const ctx=cv.getContext('2d');
let W=320,H=280,dpr=1;
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
new ResizeObserver(resize).observe(cv);
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";
const C=(v,c)=>`<span style="color:${c}">${v}</span>`;

const nodePos=[
  {x:0.25,y:0.25},{x:0.65,y:0.25},
  {x:0.65,y:0.7},{x:0.88,y:0.48}
];
const edges=[[0,1],[1,2],[2,0],[1,3]];

const steps=[
  {title:"시작",disc:[-1,-1,-1,-1],low:[-1,-1,-1,-1],stack:[],scc:[],active:[],hEdge:null,callstack:["dfs(0) 호출 예정"],
   info:`DFS를 노드 0에서 시작합니다.`},
  {title:"dfs(0)",disc:[0,-1,-1,-1],low:[0,-1,-1,-1],stack:[0],scc:[],active:[0],hEdge:null,callstack:["▶ dfs(0)"],
   info:`${C('disc[0]=0, low[0]=0','#ffd740')} 으로 초기화. 스택에 0 push.`},
  {title:"0→1 tree edge",disc:[0,1,-1,-1],low:[0,1,-1,-1],stack:[0,1],scc:[],active:[1],hEdge:0,callstack:["  dfs(0)","▶ dfs(1)"],
   info:`0의 이웃 1은 미방문 → ${C('tree edge','#69f0ae')}. dfs(1) 호출.<br>${C('disc[1]=1, low[1]=1','#ffd740')}`},
  {title:"1→2 tree edge",disc:[0,1,2,-1],low:[0,1,2,-1],stack:[0,1,2],scc:[],active:[2],hEdge:1,callstack:["  dfs(0)","  dfs(1)","▶ dfs(2)"],
   info:`1의 이웃 2는 미방문 → ${C('tree edge','#69f0ae')}. dfs(2) 호출.<br>${C('disc[2]=2, low[2]=2','#ffd740')}`},
  {title:"2→0 back edge!",disc:[0,1,2,-1],low:[0,1,0,-1],stack:[0,1,2],scc:[],active:[2],hEdge:2,callstack:["  dfs(0)","  dfs(1)","▶ dfs(2) ← 2→0 발견"],
   info:`2의 이웃 0은 이미 방문 & ${C('스택에 있음','#ef5350')} → ${C('back edge!','#ef5350')}<br>${C('low[2] = min(2, disc[0]) = min(2, 0) = 0','#ce93d8')}<br>\"2는 0번까지 거슬러 올라갈 수 있다!\"`},
  {title:"2→1 전파",disc:[0,1,2,-1],low:[0,0,0,-1],stack:[0,1,2],scc:[],active:[1],hEdge:null,callstack:["  dfs(0)","▶ dfs(1) ← dfs(2) 리턴"],
   info:`dfs(2) 리턴. ${C('low[1] = min(low[1], low[2]) = min(1, 0) = 0','#ce93d8')}<br>자식(2)이 0까지 갈 수 있으니, 부모(1)도 0까지 갈 수 있다.`},
  {title:"1→3 tree edge → SCC{3}",disc:[0,1,2,3],low:[0,0,0,3],stack:[0,1,2],scc:[[3]],active:[1],hEdge:3,callstack:["  dfs(0)","▶ dfs(1) ← dfs(3) 리턴"],
   info:`1의 이웃 3은 미방문 → dfs(3). ${C('disc[3]=3, low[3]=3','#ffd740')}<br>3은 이웃 없음. ${C('disc[3]==low[3]==3','#69f0ae')} → SCC 루트!<br>스택에서 3 pop → ${C('SCC {3} 완성!','#69f0ae')}`},
  {title:"1→0 전파",disc:[0,1,2,3],low:[0,0,0,3],stack:[0,1,2],scc:[[3]],active:[0],hEdge:null,callstack:["▶ dfs(0) ← dfs(1) 리턴"],
   info:`dfs(1) 리턴. ${C('low[0] = min(low[0], low[1]) = min(0, 0) = 0','#ce93d8')} (변화 없음)<br>disc[1]=1 ≠ low[1]=0 → 1은 SCC 루트가 아님 (위로 탈출 가능).`},
  {title:"SCC {0,1,2} 완성!",disc:[0,1,2,3],low:[0,0,0,3],stack:[],scc:[[3],[0,1,2]],active:[0,1,2],hEdge:null,callstack:["dfs(0) 종료"],
   info:`dfs(0) 이웃 탐색 완료. ${C('disc[0]==low[0]==0','#69f0ae')} → SCC 루트!<br>스택에서 0이 나올 때까지 pop → ${C('SCC {0,1,2} 완성!','#69f0ae')}<br>0→1→2→0 사이클이므로 같은 SCC.`}
];
let cur=0;

function draw(){
  ctx.clearRect(0,0,W,H);
  const s=steps[cur];
  const R=Math.min(W,H)*0.09;

  edges.forEach((e,idx)=>{
    const a=nodePos[e[0]],b=nodePos[e[1]];
    const ax=a.x*W,ay=a.y*H,bx=b.x*W,by=b.y*H;
    const dx=bx-ax,dy=by-ay,len=Math.sqrt(dx*dx+dy*dy);
    const ux=dx/len,uy=dy/len;
    const sx=ax+ux*R,sy=ay+uy*R;
    const ex=bx-ux*(R+8),ey=by-uy*(R+8);
    const isHL=s.hEdge===idx;
    const isBack=idx===2&&cur>=4;

    if(idx===2){
      const mx=(ax+bx)/2-W*0.15,my=(ay+by)/2+H*0.15;
      ctx.strokeStyle=isHL?'#ef5350':isBack?'#ef535066':'#3a3f50';
      ctx.lineWidth=isHL?2.5:1.5;
      if(isBack&&!isHL){ctx.setLineDash([5,3]);}
      ctx.beginPath();ctx.moveTo(sx,sy);ctx.quadraticCurveTo(mx,my,ex,ey);ctx.stroke();
      ctx.setLineDash([]);
      const t=0.85,qx=2*(1-t)*mx+t*bx,qy=2*(1-t)*my+t*by;
      const adx=bx-qx,ady=by-qy,al=Math.sqrt(adx*adx+ady*ady);
      const anx=adx/al,any=ady/al;
      ctx.fillStyle=ctx.strokeStyle;ctx.beginPath();
      ctx.moveTo(ex,ey);ctx.lineTo(ex-8*anx+4*any,ey-8*any-4*anx);ctx.lineTo(ex-8*anx-4*any,ey-8*any+4*anx);ctx.closePath();ctx.fill();
    } else {
      ctx.strokeStyle=isHL?'#5c6bc0':'#3a3f50';
      ctx.lineWidth=isHL?2.5:1.5;
      ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(ex,ey);ctx.stroke();
      ctx.fillStyle=ctx.strokeStyle;ctx.beginPath();
      ctx.moveTo(ex,ey);ctx.lineTo(ex-8*ux+4*uy,ey-8*uy-4*ux);ctx.lineTo(ex-8*ux-4*uy,ey-8*uy+4*ux);ctx.closePath();ctx.fill();
    }
  });

  nodePos.forEach((p,i)=>{
    const x=p.x*W,y=p.y*H;
    let fill='#1e2130',stroke='#3a3f50',tc='#b0b8d0';
    const inSCC=s.scc.find(g=>g.includes(i));
    if(inSCC){
      if(inSCC.length>1){fill='#0d2818';stroke='#69f0ae';tc='#69f0ae';}
      else{fill='#2a1f00';stroke='#ffd740';tc='#ffd740';}
    } else if(s.active.includes(i)){fill='#1a237e';stroke='#5c6bc0';tc='#9fa8da';}
    else if(s.disc[i]>=0){fill='#1a1a2e';stroke='#3949ab';tc='#7986cb';}
    ctx.fillStyle=fill;ctx.beginPath();ctx.arc(x,y,R,0,Math.PI*2);ctx.fill();
    ctx.strokeStyle=stroke;ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x,y,R,0,Math.PI*2);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${Math.round(R*0.7)}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(i,x,y-R*0.15);
    if(s.disc[i]>=0){
      ctx.font=`${Math.round(R*0.45)}px ${MONO}`;ctx.fillStyle='#8090a0';
      ctx.fillText(`d${s.disc[i]} L${s.low[i]}`,x,y+R*0.35);
    }
  });
}

function update(){
  const s=steps[cur];
  draw();
  document.getElementById('tj-step-lbl').textContent=`단계 ${cur+1} / ${steps.length}`;
  document.getElementById('tj-stack').innerHTML=s.stack.length?s.stack.map(n=>`<span style="display:inline-block;width:28px;height:28px;line-height:28px;text-align:center;background:#1a237e;border:1px solid #5c6bc0;border-radius:4px;margin:2px;">${n}</span>`).join(''):'비어있음';
  document.getElementById('tj-scc').innerHTML=s.scc.length?s.scc.map(g=>`<span style="color:${g.length>1?'#69f0ae':'#ffd740'}">{${g.join(',')}}</span>`).join(' '):'없음';
  document.getElementById('tj-callstack').innerHTML=s.callstack.map(l=>l.startsWith('▶')?`<span style="color:#ffd740">${l}</span>`:l).join('<br>');
  document.getElementById('tj-info').innerHTML=s.info;
  document.getElementById('tj-back').disabled=cur===0;
  document.getElementById('tj-next').disabled=cur===steps.length-1;
}

window.tjBack=function(){if(cur>0){cur--;update();}};
window.tjNext=function(){if(cur<steps.length-1){cur++;update();}};
update();
})();
</script>
{{< /rawhtml >}}

---

## 4. 비유: 탐정이 용의자를 만나러 다닌다

탐정이 용의자들을 처음 만나는 순서대로 **명찰**을 달아준다고 상상하자. 명찰에는 두 가지가 적혀 있다.

| 명찰 항목 | 의미 | 대응 변수 |
|-----------|------|-----------|
| **만남 번호** | 내가 몇 번째로 만난 사람인지 | `disc[v]` |
| **탈출 번호** | 나 또는 내 인맥 중, 가장 먼저 만난 사람의 번호 | `low[v]` |

처음엔 둘 다 같은 값으로 시작한다. 그런데 탐색을 하다가 **"어, 이 사람이 이미 만난 0번을 알고 있네!"** 하면, "나는 0번까지 거슬러 올라갈 수 있구나" 라고 탈출 번호를 갱신한다. 이 정보는 부모에게 전파된다 ("나도 0번까지 갈 수 있어!").

**핵심:** 탐색이 끝난 뒤 **만남번호 = 탈출번호** 인 사람은 "자기보다 먼저 만난 누구에게도 연락이 닿지 않는 사람"이다. 즉, **이 사람이 자기 그룹의 팀장**. 스택에서 이 팀장까지 꺼내면 그게 하나의 SCC다.

사이클 안에 있는 사람들(0, 1, 2)은 결국 모두 "탈출 번호 = 0"으로 수렴하고, 0번이 팀장이 되어 셋이 한 팀으로 묶인다. 3번은 누구에게도 갈 수 없으니 혼자 팀장이자 팀원이다.

---

## 5. 왜 성립하는가? — Deep Dive

### 5.1 왜 visited 배열이 없는가?

`disc` 배열 자체가 visited 역할을 한다.

```python
disc[v] == -1   # 미방문
disc[v] >= 0    # 이미 방문
```

단, 이미 방문한 노드를 만났을 때 **두 가지 경우를 구분**해야 한다.

| 경우 | 조건 | 의미 | 행동 |
|------|------|------|------|
| 스택에 있음 | `on_stack[v] == True` | 내 조상 (사이클!) | low 갱신 |
| 스택에서 빠짐 | `on_stack[v] == False` | 남의 완성된 SCC | 무시 |

그래서 `on_stack[]` 배열이 필요하다.

---

### 5.2 low는 어떻게 변하는가?

low는 **절대 증가하지 않는다.** `min()` 으로만 갱신하기 때문이다.

갱신되는 순간은 딱 두 가지:

| 시점 | 코드 | 의미 |
|------|------|------|
| back edge 발견 | `low[u] = min(low[u], disc[v])` | 조상 v까지 올라갈 수 있다 |
| 자식 탐색 완료 | `low[u] = min(low[u], low[v])` | 자식이 발견한 정보를 흡수 |

예시 그래프 (0→1→2→0, 1→3) 의 low 변화:

| 시점 | 이유 | low 변화 |
|------|------|----------|
| 0 방문 | 초기화 | `low[0] = 0` |
| 1 방문 | 초기화 | `low[1] = 1` |
| 2 방문 | 초기화 | `low[2] = 2` |
| 2→0 back edge | `min(2, disc[0])` | **`low[2]: 2→0`** |
| 2 완료, 1로 복귀 | `min(low[1], low[2]) = min(1, 0)` | **`low[1]: 1→0`** |
| 3 방문 | 초기화 | `low[3] = 3` |
| 3 완료, 1로 복귀 | `min(low[1], low[3]) = min(0, 3)` | 변화 없음 |
| 1 완료, 0으로 복귀 | `min(low[0], low[1]) = min(0, 0)` | 변화 없음 |

**한 줄 요약:** back edge를 타고 "오래된 조상"을 발견할 때만 low가 쭉 내려가고, 그 정보가 자식→부모로 전파되면서 같은 사이클 안의 모든 노드의 low가 같은 값으로 수렴한다.

---

### 5.3 "오래됨"이 min인 이유

disc값이 **방문 순서**이기 때문이다.

```
먼저 만난 사람 → disc 값이 작다 → "더 오래됨"
```

low의 목적: "내가 얼마나 오래된 조상까지 거슬러 올라갈 수 있는가?"

올라갈수록 disc가 작아지고, 가장 멀리 올라간 것 = 가장 작은 disc = `min`.

---

### 5.4 "먼저 온 것"이 왜 중요한가?

DFS 트리에서 **나보다 먼저 발견된 노드 = 나의 조상**이다.

- 나보다 **나중에** 발견된 노드에 닿는다 → 내 후손이다. 사이클이 아니다.
- 나보다 **먼저** 발견된 노드에 닿는다 → 내 조상이다. **사이클이다!**

```
0 → 1 → 2 → 0   (2가 조상인 0에게 닿음 = 사이클!)
```

low값이 추적하는 것이 바로 이것이다: "내가 사이클을 통해 얼마나 위의 조상까지 올라갈 수 있는가?"

단, 조상에 닿는다고 바로 SCC가 되는 것은 아니다. 조상이 자기 탐색을 다 끝냈을 때 비로소 SCC가 완성된다 (§5.7 참고).

---

### 5.5 Tree Edge vs Back Edge

```python
for v in graph[u]:
    if disc[v] == -1:          # tree edge
        dfs(v)
        low[u] = min(low[u], low[v])
    elif on_stack[v]:          # back edge
        low[u] = min(low[u], disc[v])
```

| | Tree Edge | Back Edge |
|--|-----------|-----------|
| 조건 | `disc[v] == -1` (미방문) | `on_stack[v] == True` (방문 & 스택) |
| `dfs(v)` 호출 | **호출한다** | **호출 안 한다** |
| low 갱신 | `min(low[u], low[v])` — 서브트리 전체 결과 흡수 | `min(low[u], disc[v])` — v의 disc만 참고 |

**tree edge**는 v의 서브트리를 u가 직접 탐색한 결과이므로 `low[v]` (최종 결과)를 가져온다.

**back edge**는 v에 닿기만 한 것이므로 `disc[v]` 만 기록하면 충분하다.

---

### 5.6 back edge에서 왜 disc[v]만 쓰고 low[v]는 안 쓰는가?

back edge로 v에 닿았을 때, v는 **탐색 중인 조상**이다. v의 서브트리는 지금 u 자신이 속해있는 곳이다.

```
dfs(0) 실행 중    ← v = 0 (아직 실행 중!)
  dfs(1) 실행 중
    dfs(2) 실행 중  ← u = 2
      2 → 0 back edge 발견
```

이 시점에 `low[0]` 은 **아직 확정이 안 된 값**이다. 0의 이웃 탐색이 아직 안 끝났기 때문이다. 불완전한 값을 가져와봤자 의미가 없다.

반면 `disc[0] = 0` 은 **이미 확정된 불변값**이므로 안전하게 쓸 수 있다.

v가 더 위로 올라갈 수 있는지는 나중에 `dfs(v)` 가 끝날 때 `low[v]` 가 위로 전파되면서 자동으로 반영된다. u가 지금 굳이 `low[v]` 까지 볼 필요가 없다.

---

### 5.7 SCC 체크 타이밍 — 왜 dfs 끝에서?

SCC 체크는 **v의 모든 이웃 탐색이 끝나 low[v]가 확정된 직후, 리턴하기 직전**에 한다.

```python
def dfs(u):
    ...
    for v in graph[u]:      # 모든 이웃 탐색
        ...
    # ← 여기! low[u] 확정
    if disc[u] == low[u]:   # SCC 루트인지 체크
        ...
```

**왜 이 시점인가?**

이웃을 하나씩 탐색할 때마다 low값이 바뀔 수 있다. for문이 끝나야 더 이상 low를 바꿀 기회가 사라진다 → 확정.

**너무 일찍 체크하면?**

자식들이 아직 back edge를 발견하지 못한 상태라 low값이 내려오지 않았을 수 있다. 실제론 사이클인데 SCC를 발견하지 못하는 버그가 생긴다.

---

### 5.8 disc[v] == low[v] 의 의미

> **"내 서브트리 중에 나보다 먼저 발견된 노드에 닿을 수 있는 애가 아무도 없다"**

다르면?

```
disc[1] = 1, low[1] = 0 → "1번 팀에서 누군가가 0번까지 닿을 수 있다"
                         → 아직 SCC가 위로 열려있다
                         → 여기서 자르면 안 된다
```

같으면?

```
disc[0] = 0, low[0] = 0 → "우리 팀은 위로 탈출구가 없다"
                         → 여기서 닫힌 완전한 그룹이다
                         → SCC 루트!
```

---

### 5.9 조상 발견 ≠ SCC 즉시 완성

2에서 back edge로 0을 발견해도 SCC가 바로 만들어지지 않는다.

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:12px;flex-wrap:wrap;">
  <div style="flex:1;min-width:250px;">
    <div style="font-size:14px;font-weight:600;color:#ef5350;margin-bottom:8px;">❌ back edge 발견 즉시 SCC를 끊으면?</div>
    <canvas id="tj-wrong" style="width:100%;border-radius:8px;background:#1a1d27;display:block;aspect-ratio:280/240;"></canvas>
  </div>
  <div style="flex:1;min-width:250px;">
    <div style="font-size:14px;font-weight:600;color:#69f0ae;margin-bottom:8px;">✓ dfs(0)가 완전히 끝난 뒤 체크하면?</div>
    <canvas id="tj-right" style="width:100%;border-radius:8px;background:#1a1d27;display:block;aspect-ratio:280/240;"></canvas>
  </div>
</div>
<div style="background:#1a1d27;border-left:3px solid #ffd740;border-radius:6px;padding:10px 14px;margin-top:10px;font-family:'JetBrains Mono',monospace;font-size:14px;color:#b0b8d0;line-height:1.8;">
  <b style="color:#ef5350;">왼쪽:</b> 2에서 back edge 발견 시 바로 자르면, 1이 아직 탐색 중이라 1도 사이클 안에 있는데 빠뜨린다.<br>
  <b style="color:#69f0ae;">오른쪽:</b> dfs(2)→dfs(1) 순서로 리턴하며 low가 전파된 뒤, dfs(0) 끝에서 체크하면 정확히 {0,1,2}를 잡아낸다.
</div>
</div>
<script>
(function(){
const MONO="'JetBrains Mono',monospace";
function drawWrong(){
  const cv=document.getElementById('tj-wrong');
  const ctx=cv.getContext('2d');
  const dpr=window.devicePixelRatio||1;
  const r=cv.getBoundingClientRect();
  const W=r.width,H=r.height;
  cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,W,H);
  const bw=Math.round(W*0.55),bh=34,gap=10,x=Math.round((W-bw)/2);
  let y=20;
  const items=[
    {label:'dfs(0) 실행 중',sub:'d=0, L=0',col:'#3949ab'},
    {label:'dfs(1) 실행 중',sub:'d=1, L=0',col:'#3949ab'},
    {label:'dfs(2) 실행 중',sub:'d=2, L=0',col:'#3949ab'},
  ];
  items.forEach(it=>{
    ctx.fillStyle='#1a1a2e';ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.fill();
    ctx.strokeStyle=it.col;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.stroke();
    ctx.fillStyle='#b0b8d0';ctx.font=`bold 13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(it.label,x+bw/2,y+bh/2-6);
    ctx.fillStyle='#8090a0';ctx.font=`11px ${MONO}`;
    ctx.fillText(it.sub,x+bw/2,y+bh/2+8);
    y+=bh+gap;
  });
  y+=4;
  ctx.strokeStyle='#ef5350';ctx.lineWidth=2;ctx.setLineDash([6,3]);
  ctx.beginPath();ctx.moveTo(x-10,y);ctx.lineTo(x+bw+10,y);ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle='#ef5350';ctx.font=`bold 12px sans-serif`;ctx.textAlign='center';
  ctx.fillText('여기서 바로 자르면?',W/2,y+16);
  y+=30;
  ctx.fillStyle='#3a0a0a';ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.fill();
  ctx.strokeStyle='#ef5350';ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.stroke();
  ctx.fillStyle='#ef9a9a';ctx.font=`bold 13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText('SCC {2}? 틀림!',x+bw/2,y+bh/2);
}

function drawRight(){
  const cv=document.getElementById('tj-right');
  const ctx=cv.getContext('2d');
  const dpr=window.devicePixelRatio||1;
  const r=cv.getBoundingClientRect();
  const W=r.width,H=r.height;
  cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,W,H);
  const bw=Math.round(W*0.55),bh=34,gap=10,x=Math.round((W-bw)/2);
  let y=20;
  const items=[
    {label:'dfs(2) 종료',sub:'low[2]=0 → 1로 전파',col:'#37474f'},
    {label:'dfs(1) 종료',sub:'low[1]=0 → 0으로 전파',col:'#37474f'},
    {label:'dfs(0) 종료!',sub:'disc[0]=0, low[0]=0 → 같음!',col:'#43a047'},
  ];
  items.forEach((it,i)=>{
    ctx.fillStyle=i===2?'#0d2818':'#1e2130';ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.fill();
    ctx.strokeStyle=it.col;ctx.lineWidth=i===2?1.5:1;ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.stroke();
    ctx.fillStyle=i===2?'#69f0ae':'#b0b8d0';ctx.font=`bold 13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(it.label,x+bw/2,y+bh/2-6);
    ctx.fillStyle='#8090a0';ctx.font=`11px ${MONO}`;
    ctx.fillText(it.sub,x+bw/2,y+bh/2+8);
    if(i<2){
      const my=y+bh+gap/2;
      ctx.fillStyle='#5c6bc066';ctx.beginPath();ctx.moveTo(W/2-4,my-3);ctx.lineTo(W/2+4,my-3);ctx.lineTo(W/2,my+3);ctx.closePath();ctx.fill();
    }
    y+=bh+gap;
  });
  y+=4;
  ctx.strokeStyle='#69f0ae';ctx.lineWidth=2;ctx.setLineDash([6,3]);
  ctx.beginPath();ctx.moveTo(x-10,y);ctx.lineTo(x+bw+10,y);ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle='#69f0ae';ctx.font=`bold 12px sans-serif`;ctx.textAlign='center';
  ctx.fillText('스택에서 0까지 pop',W/2,y+16);
  y+=30;
  ctx.fillStyle='#0d2818';ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.fill();
  ctx.strokeStyle='#69f0ae';ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,y,bw,bh,6);ctx.stroke();
  ctx.fillStyle='#69f0ae';ctx.font=`bold 13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText('SCC {0,1,2} 완성!',x+bw/2,y+bh/2);
}

drawWrong();drawRight();
new ResizeObserver(drawWrong).observe(document.getElementById('tj-wrong'));
new ResizeObserver(drawRight).observe(document.getElementById('tj-right'));
})();
</script>
{{< /rawhtml >}}

왼쪽이 실패하는 이유: 2에서 back edge를 발견한 시점에 **1이 아직 탐색 중**이다. 1도 사이클 안에 있는데, 그 사실은 low가 전파돼야 알 수 있다.

---

### 5.10 on_stack 체크 — 왜 스택에 없는 노드를 무시해야 하는가?

스택에서 빠진 노드 = **이미 SCC가 완성된 노드**다. SCC 체크 조건 `disc[v] == low[v]` 가 성립해서 꺼냈다는 것은 "나보다 오래된 조상으로 가는 경로가 없다"가 이미 증명된 것이다.

$$\text{스택에 있음} = \text{SCC 미확정} = \text{조상일 수 있음} = \text{low 갱신 대상}$$
$$\text{스택에서 빠짐} = \text{SCC 확정 완료} = \text{남의 SCC} = \text{무시}$$

#### 무시 안 하면 어떤 버그가 발생하는가?

```
그래프: 0→1, 1→2, 2→1 (사이클), 1→3
탐색 순서: 3이 먼저 → SCC {3} 완성 (disc[3]=0)
이후 0→1→2 탐색
```

```
dfs(3) → SCC {3} 완성, disc[3]=0, 스택에서 빠짐
dfs(0) → disc[0]=1
  dfs(1) → disc[1]=2
    dfs(2) → disc[2]=3
      2→1 back edge → low[2] = 2
    dfs(2) 리턴 → low[1] = min(2, 2) = 2
    1→3 간선 발견 → on_stack 체크 없이 갱신하면
      low[1] = min(2, disc[3]) = min(2, 0) = 0  ← 잘못된 갱신!
  dfs(1) 리턴 → low[0] = min(1, 0) = 0
  disc[0]=1, low[0]=0 → 다름 → SCC {0,1,2} 못 찾음!
```

**원래 SCC {1,2} 이었어야 하는데, 남의 SCC(3)의 disc값이 low를 오염시켜서 SCC를 아예 못 찾는다.**

핵심: `disc` 값이 작다고 조상인 것은 아니다. disc가 작은 건 조상의 **필요조건**이지 **충분조건이 아니다.** 조상인지 아닌지는 **스택에 있느냐 없느냐**로만 판단해야 한다.

---

### 5.11 low 전파는 언제 되는가?

`dfs(v)` 가 리턴되는 순간 바로 다음 줄에서 일어난다.

```python
dfs(v)                            # v 탐색 완료
low[u] = min(low[u], low[v])      # ← 바로 여기서 전파
```

별도로 전파를 "퍼뜨리는" 로직이 있는 게 아니라, **재귀 호출이 끝나고 돌아오는 흐름 자체가 전파**다.

```
dfs(2) 리턴 → low[2]=0 을 1에게 전파
dfs(1) 리턴 → low[1]=0 을 0에게 전파
```

자식이 발견한 정보가 콜스택을 타고 자동으로 올라오는 구조다.

---

### 5.12 min을 하는 이유

이미 다른 경로로 더 오래된 조상을 발견했을 수도 있기 때문이다.

```
2→0 back edge → low[2] = min(2, disc[0]) = 0
2→1 back edge → low[2] = min(0, disc[1]) = 0  ← min 덕에 0 유지
```

min 없이 그냥 대입하면 "지금까지 발견한 가장 오래된 조상" 정보를 덮어써서 잃어버린다.

---

### 5.13 dfs(0)가 끝나면 반드시 0을 포함하는 SCC가 완성되는가?

아니다. `disc[0] == low[0]` 일 때만 완성된다.

**disc[0] != low[0] 인 경우:**

```
3→0→1→2→0 구조에서 0이 조상 3으로 올라갈 수 있을 때
→ low[0] < disc[0]
→ 0은 3의 SCC에 흡수될 예정
→ dfs(3)이 끝날 때 비로소 완성
```

dfs(0)가 끝나는 건 그냥 "0 쪽 탐색이 다 끝났다"는 것일 뿐이고, low[0]가 자기 자신을 가리킬 때만 SCC가 만들어진다.

---

## 6. 시간복잡도

$$O(V + E)$$

| 요소 | 비용 |
|------|------|
| 각 노드 방문 | 딱 한 번 → $O(V)$ |
| 각 간선 확인 | 딱 한 번 → $O(E)$ |
| disc, low 갱신 | 상수 시간 |
| 스택 push/pop | 각 노드 한 번씩 → $O(V)$ |

---

## 7. 알고리즘 비교

| 알고리즘 | 시간복잡도 | DFS 횟수 | 그래프 뒤집기 |
|----------|-----------|----------|---------------|
| Tarjan | $O(V+E)$ | **1번** | 불필요 |
| Kosaraju | $O(V+E)$ | 2번 | 필요 |
| Brute Force | $O(V^3)$ | 모든 쌍 | 불필요 |

Kosaraju도 같은 시간복잡도이지만 DFS를 두 번 돌고 그래프를 한 번 뒤집어야 해서 실제 상수가 Tarjan보다 크다. Tarjan이 DFS 한 번에 끝내므로 실용적으로 더 빠르다.
