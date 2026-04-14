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
<style>
#tj-wrap{font-family:'JetBrains Mono','Fira Code',monospace;background:#0d0f18;border-radius:14px;padding:20px;box-shadow:0 8px 40px rgba(0,0,0,.5);margin:1.5rem 0;}
.tj-btn{padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;transition:background .15s;}
.tj-btn-p{background:#4f46e5;color:#fff;}.tj-btn-p:hover{background:#6366f1;}
.tj-btn-s{background:#1e2035;color:#94a3b8;border:1px solid #2d3050;}.tj-btn-s:hover{background:#252840;}
.tj-btn:disabled{opacity:.35;cursor:default;}
.tj-panel{background:#131525;border-radius:10px;padding:12px 16px;border:1px solid #1e2240;margin-bottom:10px;}
.tj-pt{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;}
.tj-chip{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;font-weight:700;font-size:14px;margin:2px;border:1.5px solid;}
#tj-info{background:#131525;border-radius:10px;padding:14px 18px;border-left:3px solid #6366f1;margin-top:12px;font-size:14px;color:#94a3b8;line-height:1.9;}
</style>
<div id="tj-wrap">
  <div style="display:flex;gap:8px;margin-bottom:16px;align-items:center;flex-wrap:wrap;">
    <button class="tj-btn tj-btn-s" id="tj-bb" onclick="tjB()">◀ 이전</button>
    <button class="tj-btn tj-btn-p" id="tj-bn" onclick="tjN()">다음 ▶</button>
    <span id="tj-sl" style="font-size:12px;color:#475569;margin-left:4px;"></span>
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start;">
    <svg id="tj-g" style="flex:1;min-width:260px;max-width:360px;background:#0d0f18;border-radius:12px;border:1px solid #1e2240;" viewBox="0 0 340 280"></svg>
    <div style="flex:1;min-width:200px;">
      <div class="tj-panel"><div class="tj-pt" style="color:#6366f1;">스택</div><div id="tj-sv" style="min-height:36px;"></div></div>
      <div class="tj-panel"><div class="tj-pt" style="color:#34d399;">발견된 SCC</div><div id="tj-sv2" style="min-height:24px;font-size:14px;color:#334155;"></div></div>
      <div class="tj-panel"><div class="tj-pt" style="color:#fbbf24;">콜스택</div><div id="tj-csv" style="min-height:24px;font-size:13px;line-height:1.8;color:#94a3b8;"></div></div>
    </div>
  </div>
  <div id="tj-info"></div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
(function(){
const nodes=[{id:0,x:90,y:85},{id:1,x:240,y:85},{id:2,x:240,y:200},{id:3,x:316,y:150}];
const edgeData=[{s:0,t:1,curve:false},{s:1,t:2,curve:false},{s:2,t:0,curve:true},{s:1,t:3,curve:false}];
const R=24,MF="'JetBrains Mono',monospace";
const C=(v,c)=>`<span style="color:${c};font-weight:600">${v}</span>`;

const steps=[
  {d:[-1,-1,-1,-1],l:[-1,-1,-1,-1],st:[],sc:[],ac:-1,he:-1,bk:false,
   cs:['dfs(0) 호출 예정'],
   inf:`DFS를 노드 <b>0</b>에서 시작합니다.`},
  {d:[0,-1,-1,-1],l:[0,-1,-1,-1],st:[0],sc:[],ac:0,he:-1,bk:false,
   cs:['▶ dfs(0)'],
   inf:`${C('disc[0] = low[0] = 0','#fbbf24')} 초기화. 스택에 0 push.`},
  {d:[0,1,-1,-1],l:[0,1,-1,-1],st:[0,1],sc:[],ac:1,he:0,bk:false,
   cs:['  dfs(0)','▶ dfs(1)'],
   inf:`0→1 이웃 미방문 → ${C('tree edge','#34d399')}. dfs(1) 호출.<br>${C('disc[1] = low[1] = 1','#fbbf24')}`},
  {d:[0,1,2,-1],l:[0,1,2,-1],st:[0,1,2],sc:[],ac:2,he:1,bk:false,
   cs:['  dfs(0)','  dfs(1)','▶ dfs(2)'],
   inf:`1→2 미방문 → ${C('tree edge','#34d399')}. dfs(2) 호출.<br>${C('disc[2] = low[2] = 2','#fbbf24')}`},
  {d:[0,1,2,-1],l:[0,1,0,-1],st:[0,1,2],sc:[],ac:2,he:2,bk:true,
   cs:['  dfs(0)','  dfs(1)','▶ dfs(2) ← 2→0 발견!'],
   inf:`2→0: 이미 방문 & ${C('스택에 있음','#f87171')} → ${C('back edge!','#f87171')}<br>${C('low[2] = min(2, disc[0]) = 0','#a78bfa')}<br>"2는 0번 조상까지 거슬러 올라갈 수 있다!"`},
  {d:[0,1,2,-1],l:[0,0,0,-1],st:[0,1,2],sc:[],ac:1,he:-1,bk:false,
   cs:['  dfs(0)','▶ dfs(1) ← dfs(2) 리턴'],
   inf:`dfs(2) 리턴. ${C('low[1] = min(low[1], low[2]) = min(1,0) = 0','#a78bfa')}<br>자식(2)이 발견한 정보가 부모(1)로 전파된다.`},
  {d:[0,1,2,3],l:[0,0,0,3],st:[0,1,2],sc:[[3]],ac:1,he:3,bk:false,
   cs:['  dfs(0)','▶ dfs(1) ← dfs(3) 리턴'],
   inf:`1→3 미방문 → dfs(3). ${C('disc[3]=low[3]=3','#fbbf24')}<br>이웃 없음. ${C('disc[3]==low[3]','#34d399')} → SCC 루트! 스택에서 3 pop.<br>${C('SCC {3} 완성!','#34d399')}`},
  {d:[0,1,2,3],l:[0,0,0,3],st:[0,1,2],sc:[[3]],ac:0,he:-1,bk:false,
   cs:['▶ dfs(0) ← dfs(1) 리턴'],
   inf:`dfs(1) 리턴. ${C('low[0] = min(0,0) = 0','#a78bfa')} (변화 없음)<br>disc[1]=1 ≠ low[1]=0 → 1은 SCC 루트 아님 (위로 탈출 가능).`},
  {d:[0,1,2,3],l:[0,0,0,3],st:[],sc:[[3],[0,1,2]],ac:-1,he:-1,bk:false,
   cs:['dfs(0) 종료'],
   inf:`모든 이웃 탐색 완료. ${C('disc[0]==low[0]==0','#34d399')} → SCC 루트!<br>스택에서 0이 나올 때까지 pop → ${C('SCC {0,1,2} 완성!','#34d399')}`}
];
let cur=0;

const svg=d3.select('#tj-g');
const defs=svg.append('defs');

function mkMarker(id,col){
  defs.append('marker').attr('id',id)
    .attr('viewBox','0 0 10 10').attr('refX',9).attr('refY',5)
    .attr('markerWidth',5).attr('markerHeight',5).attr('orient','auto-start-reverse')
    .append('path').attr('d','M2 2L8 5L2 8').attr('fill','none')
    .attr('stroke',col).attr('stroke-width',1.8).attr('stroke-linecap','round');
}
mkMarker('m-def','#2d3250');
mkMarker('m-tree','#34d399');
mkMarker('m-back','#f87171');
mkMarker('m-s012','#34d399');
mkMarker('m-s3','#fbbf24');

const glowF=defs.append('filter').attr('id','glow-tj')
  .attr('x','-50%').attr('y','-50%').attr('width','200%').attr('height','200%');
glowF.append('feGaussianBlur').attr('stdDeviation',5).attr('result','b');
const fm=glowF.append('feMerge');
fm.append('feMergeNode').attr('in','b');
fm.append('feMergeNode').attr('in','SourceGraphic');

const glowF2=defs.append('filter').attr('id','glow-tj2')
  .attr('x','-80%').attr('y','-80%').attr('width','260%').attr('height','260%');
glowF2.append('feGaussianBlur').attr('stdDeviation',9).attr('result','b');
const fm2=glowF2.append('feMerge');
fm2.append('feMergeNode').attr('in','b');
fm2.append('feMergeNode').attr('in','SourceGraphic');

function getPath(e){
  const s=nodes[e.s],t=nodes[e.t];
  const dx=t.x-s.x,dy=t.y-s.y,len=Math.sqrt(dx*dx+dy*dy);
  const ux=dx/len,uy=dy/len;
  const sx=s.x+ux*(R+1),sy=s.y+uy*(R+1);
  const ex=t.x-ux*(R+11),ey=t.y-uy*(R+11);
  if(e.curve){
    const mx=(s.x+t.x)/2-55,my=(s.y+t.y)/2+55;
    return `M${sx},${sy} Q${mx},${my} ${ex},${ey}`;
  }
  return `M${sx},${sy} L${ex},${ey}`;
}

const edgeG=svg.append('g');
const edgePaths=edgeG.selectAll('path').data(edgeData).enter().append('path')
  .attr('d',e=>getPath(e)).attr('fill','none')
  .attr('stroke','#2d3250').attr('stroke-width',1.5)
  .attr('stroke-dasharray',e=>e.curve?'5,4':'none')
  .attr('marker-end','url(#m-def)');

const nodeG=svg.append('g');
const ngs=nodeG.selectAll('g').data(nodes).enter().append('g')
  .attr('transform',d=>`translate(${d.x},${d.y})`);

ngs.append('circle').attr('class','ring')
  .attr('r',R+9).attr('fill','none').attr('stroke','transparent').attr('stroke-width',2).attr('opacity',0);
ngs.append('circle').attr('class','bg')
  .attr('r',R).attr('fill','#131525').attr('stroke','#2d3250').attr('stroke-width',1.5);
ngs.append('text').attr('class','lbl')
  .attr('text-anchor','middle').attr('y',-4).attr('fill','#64748b')
  .attr('font-size',15).attr('font-weight',700).attr('font-family',MF)
  .attr('dominant-baseline','central').text(d=>d.id);
ngs.append('text').attr('class','meta')
  .attr('text-anchor','middle').attr('y',10).attr('fill','#475569')
  .attr('font-size',9).attr('font-family',MF)
  .attr('dominant-baseline','central').text('');

function scGroup(nid,scc){
  for(const g of scc) if(g.includes(nid)) return g.length>1?'m':'s';
  return null;
}

function render(){
  const s=steps[cur],T=380;

  edgePaths.transition().duration(T).ease(d3.easeQuadInOut)
    .attr('stroke',(e,i)=>{
      if(i===s.he) return s.bk?'#f87171':'#34d399';
      const g=scGroup(e.s,s.sc);
      return g==='m'?'#34d39940':g==='s'?'#fbbf2440':'#2d3250';
    })
    .attr('stroke-width',(e,i)=>i===s.he?2.5:1.5)
    .attr('marker-end',(e,i)=>{
      if(i===s.he) return s.bk?'url(#m-back)':'url(#m-tree)';
      const g=scGroup(e.s,s.sc);
      return g==='m'?'url(#m-s012)':g==='s'?'url(#m-s3)':'url(#m-def)';
    });

  ngs.each(function(d){
    const g=d3.select(this),sc=scGroup(d.id,s.sc);
    let fill,stroke,lc,mc,glow=null,sw=1.5;
    if(sc==='m'){fill='#052e16';stroke='#34d399';lc='#34d399';mc='#16a34a';glow='url(#glow-tj)';sw=2;}
    else if(sc==='s'){fill='#1c1008';stroke='#fbbf24';lc='#fbbf24';mc='#d97706';glow='url(#glow-tj)';sw=2;}
    else if(d.id===s.ac){fill='#1e1b4b';stroke='#6366f1';lc='#a5b4fc';mc='#6366f1';sw=2;}
    else if(s.d[d.id]>=0){fill='#131a2e';stroke='#334155';lc='#7986cb';mc='#475569';}
    else{fill='#0d0f18';stroke='#1e2240';lc='#334155';mc='#1e2240';}
    g.select('.bg').transition().duration(T).attr('fill',fill).attr('stroke',stroke)
      .attr('stroke-width',sw).attr('filter',glow);
    g.select('.ring').transition().duration(T)
      .attr('stroke',glow?stroke:'transparent').attr('opacity',glow?.3:0);
    g.select('.lbl').transition().duration(T).attr('fill',lc);
    g.select('.meta').transition().duration(T).attr('fill',mc)
      .text(s.d[d.id]>=0?`d${s.d[d.id]} L${s.l[d.id]}`:'');
  });

  document.getElementById('tj-sv').innerHTML=s.st.length
    ?s.st.map(n=>{
      const sc2=scGroup(n,s.sc);
      let bg='#1e1b4b',bc='#4f46e5',c='#a5b4fc';
      if(sc2==='m'){bg='#052e16';bc='#34d399';c='#34d399';}
      if(sc2==='s'){bg='#1c1008';bc='#fbbf24';c='#fbbf24';}
      if(n===s.ac){bg='#2d2775';bc='#818cf8';}
      return `<span class="tj-chip" style="background:${bg};border-color:${bc};color:${c}">${n}</span>`;
    }).join('')
    :'<span style="color:#334155;font-size:13px">비어있음</span>';

  document.getElementById('tj-sv2').innerHTML=s.sc.length
    ?s.sc.map(g=>`<span style="color:${g.length>1?'#34d399':'#fbbf24'};font-weight:700;margin-right:8px">{${g.join(',')}}</span>`).join('')
    :'<span style="color:#334155">없음</span>';

  document.getElementById('tj-csv').innerHTML=s.cs.map(l=>
    l.startsWith('▶')
      ?`<span style="color:#fbbf24">${l}</span>`
      :`<span style="color:#475569">${l}</span>`
  ).join('<br>');

  document.getElementById('tj-info').innerHTML=s.inf;
  document.getElementById('tj-sl').textContent=`단계 ${cur+1} / ${steps.length}`;
  document.getElementById('tj-bb').disabled=cur===0;
  document.getElementById('tj-bn').disabled=cur===steps.length-1;
}

window.tjB=function(){if(cur>0){cur--;render();}};
window.tjN=function(){if(cur<steps.length-1){cur++;render();}};
render();
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

처음엔 둘 다 같은 값으로 시작한다. 그런데 탐색을 하다가 **"어, 이 사람이 이미 만난 0번을 알고 있네!"** 하면, "나는 0번까지 거슬러 올라갈 수 있구나" 라고 탈출 번호를 갱신한다. 이 정보는 부모에게 전파된다.

**핵심:** 탐색이 끝난 뒤 **만남번호 = 탈출번호** 인 사람은 "자기보다 먼저 만난 누구에게도 연락이 닿지 않는 사람"이다. 즉, **이 사람이 자기 그룹의 팀장**. 스택에서 이 팀장까지 꺼내면 그게 하나의 SCC다.

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

---

### 5.3 "오래됨"이 min인 이유

disc값이 **방문 순서**이기 때문이다.

```
먼저 만난 사람 → disc 값이 작다 → "더 오래됨"
```

low의 목적: "내가 얼마나 오래된 조상까지 거슬러 올라갈 수 있는가?" 가장 멀리 올라간 것 = 가장 작은 disc = `min`.

---

### 5.4 "먼저 온 것"이 왜 중요한가?

DFS 트리에서 **나보다 먼저 발견된 노드 = 나의 조상**이다.

- 나보다 **나중에** 발견된 노드에 닿는다 → 내 후손이다. 사이클이 아니다.
- 나보다 **먼저** 발견된 노드에 닿는다 → 내 조상이다. **사이클이다!**

low값이 추적하는 것이 바로 이것이다: "내가 사이클을 통해 얼마나 위의 조상까지 올라갈 수 있는가?"

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
| low 갱신 | `min(low[u], low[v])` — 서브트리 전체 흡수 | `min(low[u], disc[v])` — v의 disc만 참고 |

---

### 5.6 back edge에서 왜 disc[v]만 쓰는가?

back edge로 v에 닿았을 때, v는 **탐색 중인 조상**이다. 이 시점에 `low[v]` 는 아직 확정이 안 된 값이다. v의 이웃 탐색이 아직 안 끝났기 때문이다.

반면 `disc[v]` 는 이미 확정된 불변값이므로 안전하게 쓸 수 있다. v가 더 위로 올라갈 수 있는지는 나중에 `dfs(v)` 가 끝날 때 `low[v]` 가 위로 전파되면서 자동으로 반영된다.

---

### 5.7 SCC 체크 타이밍 — 왜 dfs 끝에서?

SCC 체크는 **v의 모든 이웃 탐색이 끝나 low[v]가 확정된 직후, 리턴하기 직전**에 한다.

```python
def dfs(u):
    ...
    for v in graph[u]:      # 모든 이웃 탐색
        ...
    # ← 여기! low[u] 확정. 이웃이 더 없으므로 low[u]는 더 이상 바뀌지 않는다.
    if disc[u] == low[u]:   # SCC 루트인지 체크
        ...
```

---

### 5.8 disc[v] == low[v] 의 의미

> **"내 서브트리 중에 나보다 먼저 발견된 노드에 닿을 수 있는 애가 아무도 없다"**

같으면 → 이 그룹은 위로 탈출구가 없다 → 여기서 닫힌 완전한 그룹 → **SCC 루트!**

다르면 → `low < disc` → 누군가 더 오래된 조상으로 가는 경로가 있다 → 아직 SCC가 위로 열려있다 → 여기서 자르면 안 된다.

---

### 5.9 조상 발견 ≠ SCC 즉시 완성

back edge를 발견해도 SCC가 바로 만들어지지 않는다. 아래 비교를 확인하라.

{{< rawhtml >}}
<style>
#cmp-wrap{font-family:'JetBrains Mono','Fira Code',monospace;background:#0d0f18;border-radius:14px;padding:20px;box-shadow:0 8px 40px rgba(0,0,0,.5);margin:1.5rem 0;}
.cmp-card{flex:1;min-width:240px;}
.cmp-hd{font-size:13px;font-weight:700;margin-bottom:12px;padding:8px 14px;border-radius:8px;}
.cmp-note{margin-top:10px;background:#131525;border-radius:8px;padding:10px 14px;font-size:12px;color:#64748b;line-height:1.8;border-left:3px solid;}
</style>
<div id="cmp-wrap">
  <div style="display:flex;gap:16px;flex-wrap:wrap;">
    <div class="cmp-card">
      <div class="cmp-hd" style="background:#1f0a0a;color:#f87171;border:1px solid #3d0f0f;">❌ back edge 발견 즉시 끊으면?</div>
      <div style="background:#0d0f1e;border-radius:10px;border:1px solid #1e2240;">
        <svg id="cmp-w" width="100%" viewBox="0 0 260 230"></svg>
      </div>
      <div class="cmp-note" style="border-color:#f8717155;">
        2에서 back edge 발견 시 바로 자르면,<br>
        1이 아직 탐색 중이라 <b style="color:#f87171">1도 사이클 안에 있다는 사실</b>을 놓친다.
      </div>
    </div>
    <div class="cmp-card">
      <div class="cmp-hd" style="background:#052e16;color:#34d399;border:1px solid #0f3d1f;">✓ dfs(0) 끝난 뒤 체크하면?</div>
      <div style="background:#0d0f1e;border-radius:10px;border:1px solid #1e2240;">
        <svg id="cmp-r" width="100%" viewBox="0 0 260 230"></svg>
      </div>
      <div class="cmp-note" style="border-color:#34d39955;">
        dfs(2)→dfs(1) 리턴하며 low 전파 완료 후,<br>
        dfs(0) 끝에서 <b style="color:#34d399">disc[0]==low[0]</b> 확인 → {0,1,2} 정확히 완성.
      </div>
    </div>
  </div>
</div>
<script>
(function(){
const MF="'JetBrains Mono',monospace";
function buildSvg(id,wrong){
  const sv=d3.select('#'+id);
  const W=260,bw=190,bh=40,gap=8,x=(W-bw)/2;
  const items=wrong?[
    {t:'dfs(0) 실행 중',s:'disc=0, low=0',stroke:'#3949ab',fill:'#0d1030'},
    {t:'dfs(1) 실행 중',s:'disc=1, low=0',stroke:'#3949ab',fill:'#0d1030'},
    {t:'dfs(2) 실행 중',s:'2→0 back edge 발견!',stroke:'#f87171',fill:'#200808'},
  ]:[
    {t:'dfs(2) 종료',s:'low[2]=0 → 1로 전파 ↑',stroke:'#334155',fill:'#0d0f18'},
    {t:'dfs(1) 종료',s:'low[1]=0 → 0으로 전파 ↑',stroke:'#334155',fill:'#0d0f18'},
    {t:'dfs(0) 종료!',s:'disc[0]==low[0]==0 ← 여기!',stroke:'#34d399',fill:'#052e16'},
  ];
  let y=16;
  items.forEach((it,i)=>{
    const g=sv.append('g');
    g.append('rect').attr('x',x).attr('y',y).attr('width',bw).attr('height',bh)
      .attr('rx',8).attr('fill',it.fill).attr('stroke',it.stroke).attr('stroke-width',1.3);
    g.append('text').attr('x',x+bw/2).attr('y',y+14).attr('text-anchor','middle')
      .attr('fill',it.stroke==='#334155'?'#94a3b8':it.stroke)
      .attr('font-size',12).attr('font-weight',700).attr('font-family',MF).text(it.t);
    g.append('text').attr('x',x+bw/2).attr('y',y+28).attr('text-anchor','middle')
      .attr('fill','#475569').attr('font-size',9.5).attr('font-family',MF).text(it.s);
    if(i<items.length-1){
      const ay=y+bh+gap/2;
      sv.append('line').attr('x1',W/2).attr('y1',y+bh+1).attr('x2',W/2).attr('y2',ay)
        .attr('stroke','#2d3250').attr('stroke-width',1);
      sv.append('polygon').attr('points',`${W/2-4},${ay} ${W/2+4},${ay} ${W/2},${ay+5}`)
        .attr('fill','#2d3250');
    }
    y+=bh+gap;
  });
  y+=12;
  const dc=wrong?'#f87171':'#34d399';
  sv.append('line').attr('x1',x-6).attr('y1',y).attr('x2',x+bw+6).attr('y2',y)
    .attr('stroke',dc).attr('stroke-width',2).attr('stroke-dasharray','5 3');
  sv.append('text').attr('x',W/2).attr('y',y+14).attr('text-anchor','middle')
    .attr('fill',dc).attr('font-size',10.5).attr('font-family',MF)
    .text(wrong?'← 여기서 자르면 틀림':'← 여기서 잘라야 함');
  y+=30;
  const rf=wrong?'#200808':'#052e16',rs=wrong?'#f87171':'#34d399';
  const rg=sv.append('g');
  rg.append('rect').attr('x',x).attr('y',y).attr('width',bw).attr('height',bh)
    .attr('rx',8).attr('fill',rf).attr('stroke',rs).attr('stroke-width',1.5);
  rg.append('text').attr('x',x+bw/2).attr('y',y+bh/2).attr('text-anchor','middle')
    .attr('dominant-baseline','central').attr('fill',rs)
    .attr('font-size',12).attr('font-weight',700).attr('font-family',MF)
    .text(wrong?'SCC {2} 만 추출 → 틀림!':'SCC {0, 1, 2} 완성! ✓');
}
buildSvg('cmp-w',true);
buildSvg('cmp-r',false);
})();
</script>
{{< /rawhtml >}}

---

### 5.10 on_stack 체크 — 왜 스택에 없는 노드를 무시해야 하는가?

스택에서 빠진 노드 = **이미 SCC가 완성된 노드**다.

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
  disc[0]=1, low[0]=0 → 다름 → SCC {1,2} 못 찾음!
```

**원래 SCC {1,2} 이었어야 하는데, 남의 SCC(3)의 disc값이 low를 오염시켜서 SCC를 아예 못 찾는다.**

`disc` 값이 작다 ≠ 조상이다. 조상인지 아닌지는 **스택에 있느냐 없느냐**로만 판단해야 한다.

---

### 5.11 low 전파는 언제 되는가?

`dfs(v)` 가 리턴되는 순간 바로 다음 줄에서 일어난다.

```python
dfs(v)                            # v 탐색 완료
low[u] = min(low[u], low[v])      # ← 바로 여기서 전파
```

별도로 전파를 "퍼뜨리는" 로직이 있는 게 아니라, **재귀 호출이 끝나고 돌아오는 흐름 자체가 전파**다.

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
