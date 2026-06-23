---
series: ["APS"]
title: "APS.10 Dijkstra, Bellman-Ford & Sliding Puzzle"
date: 2026-05-06T09:00:00+09:00
tags: ["알고리즘", "그래프", "최단경로", "dijkstra", "bellman-ford", "bfs", "sliding puzzle"]
cover:
  image: 'images/cover.jpg'
  alt: 'APS.10 Dijkstra, Bellman-Ford & Sliding Puzzle'
  relative: true
summary: "Shortest path algorithms (Dijkstra, Bellman-Ford) and BFS-based state-space search illustrated with the sliding puzzle problem."
---

# 최단 경로 & 슬라이딩 퍼즐 핵심 요약

{{< rawhtml >}}
<details style="background:transparent;border:1px solid #30363d;border-radius:8px;padding:10px 16px;margin:1.2rem 0;font-family:inherit;">
<summary style="cursor:pointer;font-weight:600;font-size:14px;color:#8b949e;user-select:none;font-family:inherit;">목차 — Table of Contents</summary>
<div style="margin-top:10px;font-size:14px;line-height:2;font-family:inherit;">
  <div><a href="#0-interactive-demo" style="color:#c9d1d9;text-decoration:none;">0. Interactive Demo</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#01-dijkstra-step-by-step" style="color:#6e7681;text-decoration:none;">0.1 Dijkstra Step-by-Step</a></div>
  </div>
  <div><a href="#1-최단-경로-문제-sssp" style="color:#c9d1d9;text-decoration:none;">1. 최단 경로 문제 (SSSP)</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#11-문제-정의" style="color:#6e7681;text-decoration:none;">1.1 문제 정의</a></div>
    <div><a href="#12-relaxation-연산" style="color:#6e7681;text-decoration:none;">1.2 Relaxation 연산</a></div>
    <div><a href="#13-초기화-및-불변-조건" style="color:#6e7681;text-decoration:none;">1.3 초기화 및 불변 조건</a></div>
  </div>
  <div><a href="#2-다익스트라-알고리즘" style="color:#c9d1d9;text-decoration:none;">2. 다익스트라 알고리즘</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#21-그리디-전략과-집합-s" style="color:#6e7681;text-decoration:none;">2.1 그리디 전략과 집합 S</a></div>
    <div><a href="#22-min-priority-queue" style="color:#6e7681;text-decoration:none;">2.2 Min-Priority Queue</a></div>
    <div><a href="#23-의사-코드" style="color:#6e7681;text-decoration:none;">2.3 의사 코드</a></div>
    <div><a href="#24-정확성-증명-귀류법" style="color:#6e7681;text-decoration:none;">2.4 정확성 증명</a></div>
    <div><a href="#25-시간-복잡도" style="color:#6e7681;text-decoration:none;">2.5 시간 복잡도</a></div>
    <div><a href="#26-lazy-deletion-heapq-구현" style="color:#6e7681;text-decoration:none;">2.6 Lazy Deletion</a></div>
  </div>
  <div><a href="#3-벨만-포드-알고리즘" style="color:#c9d1d9;text-decoration:none;">3. 벨만-포드 알고리즘</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#31-왜-다익스트라가-실패하는가" style="color:#6e7681;text-decoration:none;">3.1 왜 다익스트라가 실패하는가</a></div>
    <div><a href="#32-dp-전략" style="color:#6e7681;text-decoration:none;">3.2 DP 전략</a></div>
    <div><a href="#33-v-1번-반복하는-이유" style="color:#6e7681;text-decoration:none;">3.3 |V|−1번 반복하는 이유</a></div>
    <div><a href="#34-음수-사이클-탐지" style="color:#6e7681;text-decoration:none;">3.4 음수 사이클 탐지</a></div>
    <div><a href="#35-시간-복잡도" style="color:#6e7681;text-decoration:none;">3.5 시간 복잡도</a></div>
  </div>
  <div><a href="#4-슬라이딩-퍼즐" style="color:#c9d1d9;text-decoration:none;">4. 슬라이딩 퍼즐</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#41-반전inversion의-정의" style="color:#6e7681;text-decoration:none;">4.1 반전(Inversion)의 정의</a></div>
    <div><a href="#42-홀수-너비-퍼즐-3x3-5x5" style="color:#6e7681;text-decoration:none;">4.2 홀수 너비 퍼즐</a></div>
    <div><a href="#43-짝수-너비-퍼즐-4x4-6x6" style="color:#6e7681;text-decoration:none;">4.3 짝수 너비 퍼즐</a></div>
    <div><a href="#44-수직-이동이-홀짝성을-바꾸는-이유" style="color:#6e7681;text-decoration:none;">4.4 수직 이동과 홀짝성</a></div>
  </div>
  <div><a href="#5-bfs-브루트포스-탐색" style="color:#c9d1d9;text-decoration:none;">5. BFS (브루트포스 탐색)</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#51-상태를-문자열로-표현" style="color:#6e7681;text-decoration:none;">5.1 상태를 문자열로 표현</a></div>
    <div><a href="#52-bfs-구현" style="color:#6e7681;text-decoration:none;">5.2 BFS 구현</a></div>
    <div><a href="#53-3x3은-가능-4x4는-불가능한-이유" style="color:#6e7681;text-decoration:none;">5.3 3×3 vs 4×4</a></div>
  </div>
  <div><a href="#6-a-알고리즘" style="color:#c9d1d9;text-decoration:none;">6. A* 알고리즘</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#61-fn--gn--hn" style="color:#6e7681;text-decoration:none;">6.1 f(n) = g(n) + h(n)</a></div>
    <div><a href="#62-맨해튼-거리-휴리스틱" style="color:#6e7681;text-decoration:none;">6.2 맨해튼 거리 휴리스틱</a></div>
    <div><a href="#63-admissibility란" style="color:#6e7681;text-decoration:none;">6.3 Admissibility</a></div>
    <div><a href="#64-admissibility가-최적해를-보장하는-이유" style="color:#6e7681;text-decoration:none;">6.4 최적해 보장 이유</a></div>
    <div><a href="#65-bfs-vs-a-비교" style="color:#6e7681;text-decoration:none;">6.5 BFS vs A* 비교</a></div>
  </div>
  <div><a href="#7-핵심-질문-qa-모음" style="color:#c9d1d9;text-decoration:none;">7. Q &amp; A</a></div>
  <div style="padding-left:16px;font-size:13px;">
    <div><a href="#71-heapq--pq" style="color:#6e7681;text-decoration:none;">Q1. heapq == PQ?</a></div>
    <div><a href="#72-heap에-노드가-한-번만-들어가나" style="color:#6e7681;text-decoration:none;">Q2. heap 중복 삽입?</a></div>
    <div><a href="#73-n--m--om-인-이유" style="color:#6e7681;text-decoration:none;">Q3. n+m = O(m)?</a></div>
    <div><a href="#74-벨만-포드는-그리디인가-dp인가" style="color:#6e7681;text-decoration:none;">Q4. 벨만-포드 = DP?</a></div>
    <div><a href="#75-reachable이-어디-reachable" style="color:#6e7681;text-decoration:none;">Q5. Reachable?</a></div>
    <div><a href="#76-4x4에서-수직-이동이-홀짝성을-바꾸는-이유" style="color:#6e7681;text-decoration:none;">Q6. 수직 이동 홀짝성?</a></div>
    <div><a href="#77-r을-더하는-이유" style="color:#6e7681;text-decoration:none;">Q7. R을 더하는 이유?</a></div>
    <div><a href="#78-bfs가-브루트포스인가" style="color:#6e7681;text-decoration:none;">Q8. BFS = 브루트포스?</a></div>
    <div><a href="#79-선형-탐색-다익스트라는-pq를-안-쓰나" style="color:#6e7681;text-decoration:none;">Q9. 선형 탐색 다익스트라?</a></div>
    <div><a href="#710-lazy-deletion이-뭔가" style="color:#6e7681;text-decoration:none;">Q10. Lazy Deletion?</a></div>
    <div><a href="#711-a-코드가-lazy-deletion인가" style="color:#6e7681;text-decoration:none;">Q11. A* = Lazy Deletion?</a></div>
    <div><a href="#712-길고-짧다는-게-무슨-뜻인가" style="color:#6e7681;text-decoration:none;">Q12. 거리의 의미?</a></div>
    <div><a href="#713-goal--inttile-base16---1-이-좌표인가" style="color:#6e7681;text-decoration:none;">Q13. goal 인덱스 계산?</a></div>
    <div><a href="#714-admissibility가-왜-중요한가-쉽게" style="color:#6e7681;text-decoration:none;">Q14. Admissibility 쉽게?</a></div>
  </div>
</div>
</details>
{{< /rawhtml >}}

---

## 0. Interactive Demo

### 0.1 Dijkstra Step-by-Step

아래 6개 노드 가중 그래프에서 다익스트라 알고리즘이 어떻게 최단 경로를 확정해 나가는지 단계별로 확인한다.

그래프 구조: `S→A(4)`, `S→B(2)`, `B→A(1)`, `B→C(5)`, `A→C(1)`, `A→D(3)`, `C→D(2)`

{{< rawhtml >}}
<style>
#dijk-wrap{font-family:'Space Grotesk',system-ui,sans-serif;background:linear-gradient(135deg,#1e3050 0%,#253c60 60%,#1c2d50 100%);border-radius:14px;padding:20px;box-shadow:0 8px 40px rgba(0,0,0,.6);margin:1.5rem 0;}
.dijk-btn{padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;transition:background .15s;}
.dijk-btn-p{background:#1f6feb;color:#fff;}.dijk-btn-p:hover{background:#388bfd;}
.dijk-btn-s{background:#21262d;color:#c9d1d9;border:1px solid #30363d;}.dijk-btn-s:hover{background:#30363d;}
.dijk-btn:disabled{opacity:.35;cursor:default;}
.dijk-panel{background:#1e2d45;border-radius:10px;padding:10px 14px;border:1px solid #21262d;margin-bottom:8px;}
.dijk-pt{font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;}
.dijk-chip{display:inline-flex;align-items:center;justify-content:center;min-width:44px;height:36px;border-radius:7px;font-weight:700;font-size:14px;margin:2px;border:1.5px solid;padding:0 6px;}
.dijk-legend{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:12px;font-size:14px;font-weight:600;color:#c9d1d9;}
.dijk-leg-dot{width:11px;height:11px;border-radius:2px;display:inline-block;margin-right:4px;border:1px solid;}
#dijk-info{background:#1e2d45;border-radius:10px;padding:12px 16px;border-left:3px solid #2f81f7;margin-top:12px;font-size:17px;font-weight:600;color:#e6edf3;line-height:1.9;min-height:80px;transition:opacity .15s ease,transform .15s ease;}
#dijk-pqv,#dijk-finv,#dijk-tbl{transition:opacity .15s ease,transform .15s ease;}
</style>

<div id="dijk-wrap">
  <div class="dijk-legend">
    <span><span class="dijk-leg-dot" style="background:#34d39933;border-color:#34d399;"></span>확정 (S집합)</span>
    <span><span class="dijk-leg-dot" style="background:#58a6ff33;border-color:#58a6ff;"></span>현재 처리 중</span>
    <span><span class="dijk-leg-dot" style="background:#fbbf2433;border-color:#fbbf24;"></span>relaxation 발생</span>
    <span><span class="dijk-leg-dot" style="background:#21262d;border-color:#3a4f6a;"></span>미방문</span>
  </div>
  <div style="display:flex;gap:8px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">
    <button class="dijk-btn dijk-btn-s" id="dijk-bb" onclick="dijkB()">◀ 이전</button>
    <button class="dijk-btn dijk-btn-p" id="dijk-bn" onclick="dijkN()">다음 ▶</button>
    <button class="dijk-btn dijk-btn-s" onclick="dijkR()" style="margin-left:4px;">↺ 초기화</button>
    <span id="dijk-lbl" style="font-size:15px;color:#8b949e;margin-left:4px;"></span>
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start;">
    <div style="flex:2;min-width:300px;display:flex;flex-direction:column;gap:10px;">
      <svg id="dijk-g" style="width:100%;background:linear-gradient(135deg,#1d3050 0%,#223a5e 100%);border-radius:12px;border:1px solid #21262d;" viewBox="0 0 560 330"></svg>
      <div id="dijk-info"></div>
    </div>
    <div style="flex:1;min-width:190px;">
      <div class="dijk-panel">
        <div class="dijk-pt" style="color:#6366f1;">Priority Queue</div>
        <div id="dijk-pqv" style="min-height:40px;font-size:13px;"></div>
      </div>
      <div class="dijk-panel">
        <div class="dijk-pt" style="color:#34d399;">확정된 정점 (S)</div>
        <div id="dijk-finv" style="font-size:15px;min-height:24px;line-height:2;"></div>
      </div>
      <div class="dijk-panel">
        <div class="dijk-pt" style="color:#fbbf24;">dist / parent 테이블</div>
        <div id="dijk-tbl" style="font-size:14px;font-weight:600;color:#9aaac8;min-height:200px;"></div>
      </div>
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
(function(){
/* ── 노드 / 간선 정의 ── */
const NL=[
  {id:'S',x:80, y:80},
  {id:'A',x:280,y:80},
  {id:'B',x:80, y:240},
  {id:'C',x:280,y:240},
  {id:'D',x:480,y:80},
];
const NM={};NL.forEach(n=>NM[n.id]=n);
const R=28;

const EL=[
  {s:'S',t:'A',w:4, co:0,  id:0},
  {s:'S',t:'B',w:2, co:0,  id:1},
  {s:'B',t:'A',w:1, co:0,  id:2},
  {s:'B',t:'C',w:5, co:0,  id:3},
  {s:'A',t:'C',w:1, co:0,  id:4},
  {s:'A',t:'D',w:3, co:0,  id:5},
  {s:'C',t:'D',w:2, co:0,  id:6},
];

const C2=(v,c)=>`<span style="color:${c};font-weight:700">${v}</span>`;
const INF='∞';

/*
  각 단계: {
    dist: {S,A,B,C,D},  par: {...},
    fin: [],             // 확정된 노드 배열
    cur: null|'X',       // 현재 extract-min 노드
    relax: [],           // 이번 단계에서 relaxation된 간선 id 배열
    inf: string
  }
*/
const SS=[
  // 0 — 초기화
  {dist:{S:0,A:INF,B:INF,C:INF,D:INF},par:{S:'-',A:'-',B:'-',C:'-',D:'-'},
   fin:[],cur:null,relax:[],pq:[{n:'S',d:0}],
   inf:'초기화: dist[S]=0, 나머지 ∞. PQ에 (S,0) 삽입.'},

  // 1 — Extract S
  {dist:{S:0,A:4,B:2,C:INF,D:INF},par:{S:'-',A:'S',B:'S',C:'-',D:'-'},
   fin:['S'],cur:'S',relax:[0,1],pq:[{n:'B',d:2},{n:'A',d:4}],
   inf:`${C2('EXTRACT-MIN → S','#58a6ff')} (dist=0). 확정!<br>S→A relax: dist[A]=4. S→B relax: dist[B]=2.<br>PQ: [(B,2),(A,4)]`},

  // 2 — Extract B
  {dist:{S:0,A:3,B:2,C:7,D:INF},par:{S:'-',A:'B',B:'S',C:'B',D:'-'},
   fin:['S','B'],cur:'B',relax:[2,3],pq:[{n:'A',d:3},{n:'C',d:7}],
   inf:`${C2('EXTRACT-MIN → B','#58a6ff')} (dist=2). 확정!<br>B→A relax: dist[A] 4→${C2('3','#fbbf24')} (경로 S→B→A). B→C relax: dist[C]=7.<br>PQ: [(A,3),(C,7)]`},

  // 3 — Extract A
  {dist:{S:0,A:3,B:2,C:4,D:6},par:{S:'-',A:'B',B:'S',C:'A',D:'A'},
   fin:['S','B','A'],cur:'A',relax:[4,5],pq:[{n:'C',d:4},{n:'D',d:6}],
   inf:`${C2('EXTRACT-MIN → A','#58a6ff')} (dist=3). 확정!<br>A→C relax: dist[C] 7→${C2('4','#fbbf24')} (경로 S→B→A→C). A→D relax: dist[D]=6.<br>PQ: [(C,4),(D,6)]`},

  // 4 — Extract C
  {dist:{S:0,A:3,B:2,C:4,D:6},par:{S:'-',A:'B',B:'S',C:'A',D:'A'},
   fin:['S','B','A','C'],cur:'C',relax:[],pq:[{n:'D',d:6}],
   inf:`${C2('EXTRACT-MIN → C','#58a6ff')} (dist=4). 확정!<br>C→D: dist[D]=6 이미 같음 → relax 없음.<br>PQ: [(D,6)]`},

  // 5 — Extract D (완료)
  {dist:{S:0,A:3,B:2,C:4,D:6},par:{S:'-',A:'B',B:'S',C:'A',D:'A'},
   fin:['S','B','A','C','D'],cur:'D',relax:[],pq:[],
   inf:`${C2('EXTRACT-MIN → D','#58a6ff')} (dist=6). 확정!<br>PQ 비어있음. 알고리즘 종료.<br>최단 거리: S=0, B=2, A=3, C=4, D=6`},
];

let cur=0;

/* ── 간선 경로 계산 ── */
function edgePath(e){
  const s=NM[e.s],t=NM[e.t];
  const dx=t.x-s.x,dy=t.y-s.y,len=Math.sqrt(dx*dx+dy*dy);
  const ux=dx/len,uy=dy/len;
  let px=-uy,py=ux;
  if(py<0||(py===0&&px<0)){px=-px;py=-py;}
  if(e.co!==0){
    const cpx=(s.x+t.x)/2+px*e.co,cpy=(s.y+t.y)/2+py*e.co;
    const as=Math.atan2(cpy-s.y,cpx-s.x),ae=Math.atan2(cpy-t.y,cpx-t.x);
    const sx2=s.x+Math.cos(as)*(R+1),sy2=s.y+Math.sin(as)*(R+1);
    const ex=t.x+Math.cos(ae)*(R+10),ey=t.y+Math.sin(ae)*(R+10);
    return `M${sx2.toFixed(1)},${sy2.toFixed(1)} Q${cpx.toFixed(1)},${cpy.toFixed(1)} ${ex.toFixed(1)},${ey.toFixed(1)}`;
  }
  const sx2=s.x+ux*(R+1),sy2=s.y+uy*(R+1);
  const ex=t.x-ux*(R+11),ey=t.y-uy*(R+11);
  return `M${sx2.toFixed(1)},${sy2.toFixed(1)} L${ex.toFixed(1)},${ey.toFixed(1)}`;
}

/* ── SVG 초기 세팅 ── */
const svg=d3.select('#dijk-g');
const defs=svg.append('defs');
function mkM(id,col){
  defs.append('marker').attr('id',id)
    .attr('viewBox','0 0 10 10').attr('refX',8).attr('refY',5)
    .attr('markerWidth',8).attr('markerHeight',8).attr('orient','auto-start-reverse')
    .append('path').attr('d','M1 2L8 5L1 8').attr('fill',col)
    .attr('stroke',col).attr('stroke-width',1).attr('stroke-linecap','round');
}
mkM('dm-def','#2f81f7');
mkM('dm-rel','#fbbf24');
mkM('dm-fin','#34d399');
mkM('dm-cur','#58a6ff');

const gF=defs.append('filter').attr('id','dgx').attr('x','-50%').attr('y','-50%').attr('width','200%').attr('height','200%');
gF.append('feGaussianBlur').attr('stdDeviation',5).attr('result','b');
const fm=gF.append('feMerge');fm.append('feMergeNode').attr('in','b');fm.append('feMergeNode').attr('in','SourceGraphic');

const MF="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";

/* 간선 그룹 */
const eG=svg.append('g');
const ePaths=eG.selectAll('g').data(EL).enter().append('g');
const eLines=ePaths.append('path')
  .attr('d',e=>edgePath(e)).attr('fill','none')
  .attr('stroke','#2f81f7').attr('stroke-width',2.5)
  .attr('marker-end','url(#dm-def)');
/* 간선 가중치 레이블 */
ePaths.append('text').attr('fill','#8b949e').attr('font-size',13).attr('font-weight',700)
  .attr('font-family',MF).attr('text-anchor','middle')
  .each(function(e){
    const s=NM[e.s],t=NM[e.t];
    const mx=(s.x+t.x)/2,my=(s.y+t.y)/2;
    const dx=t.x-s.x,dy=t.y-s.y,len=Math.sqrt(dx*dx+dy*dy);
    let px=-dy/len,py=dx/len;
    if(py<0||(py===0&&px<0)){px=-px;py=-py;}
    const off=e.co!==0?e.co*0.45:18;
    d3.select(this).attr('x',mx+px*off).attr('y',my+py*off).text(e.w);
  });

/* 노드 그룹 */
const nG=svg.append('g');
const nGs=nG.selectAll('g').data(NL).enter().append('g')
  .attr('transform',d=>`translate(${d.x},${d.y})`);
nGs.append('circle').attr('class','dring').attr('r',R+9)
  .attr('fill','none').attr('stroke','transparent').attr('stroke-width',2.5).attr('opacity',0);
nGs.append('circle').attr('class','dbg').attr('r',R)
  .attr('fill','#1c2433').attr('stroke','#2f81f7').attr('stroke-width',2.5);
nGs.append('text').attr('class','dlbl').attr('text-anchor','middle').attr('dominant-baseline','central')
  .attr('fill','#e0e8ff').attr('font-size',18).attr('font-weight',700).attr('font-family',MF)
  .text(d=>d.id);

/* ── 렌더 ── */
function render(){
  const s=SS[cur],T=360;

  /* 버튼 */
  document.getElementById('dijk-bb').disabled=cur===0;
  document.getElementById('dijk-bn').disabled=cur===SS.length-1;
  document.getElementById('dijk-lbl').textContent=`${cur+1} / ${SS.length}`;

  /* 간선 색상 */
  eLines.transition().duration(T).ease(d3.easeQuadInOut)
    .attr('stroke',(_,i)=>{
      if(s.relax.includes(i)) return '#fbbf24';
      /* 확정 경로 간선: par 기반 */
      const e=EL[i];
      if(s.fin.includes(e.t)&&s.par[e.t]===e.s) return '#34d399';
      return '#2f81f7';
    })
    .attr('stroke-width',(_,i)=>s.relax.includes(i)?3.5:2.5)
    .attr('opacity',(_,i)=>{
      const e=EL[i];
      const vis=s.dist[e.s]!==INF;
      return vis?1:0.45;
    })
    .attr('marker-end',(_,i)=>{
      if(s.relax.includes(i)) return 'url(#dm-rel)';
      const e=EL[i];
      if(s.fin.includes(e.t)&&s.par[e.t]===e.s) return 'url(#dm-fin)';
      return 'url(#dm-def)';
    });

  /* 노드 색상 */
  nGs.each(function(d){
    const g=d3.select(this);
    const isFin=s.fin.includes(d.id);
    const isCur=d.id===s.cur;
    let fill,stroke,lc,sw=2.5,glw=null;
    if(isFin&&isCur){fill='#0d4028';stroke='#34d399';lc='#ffffff';sw=3;glw='url(#dgx)';}
    else if(isFin){fill='#0d2f20';stroke='#34d399';lc='#6effc8';sw=2.5;}
    else if(isCur){fill='#0d2f5e';stroke='#58a6ff';lc='#ffffff';sw=3;glw='url(#dgx)';}
    else if(s.dist[d.id]!==INF){fill='#1c2d45';stroke='#2f81f7';lc='#e6edf3';sw=2.5;}
    else{fill='#1e2d45';stroke='#3a4f6a';lc='#8b949e';sw=2.5;}
    g.select('.dbg').transition().duration(T)
      .attr('fill',fill).attr('stroke',stroke).attr('stroke-width',sw).attr('filter',glw);
    g.select('.dring').transition().duration(T)
      .attr('stroke',isFin?'#34d399':'transparent').attr('opacity',isFin?.25:0);
    g.select('.dlbl').transition().duration(T).attr('fill',lc);
  });

  /* 패널 fade 유틸 */
  function fadeUpdate(id,html){
    const el=document.getElementById(id);
    if(el.innerHTML===html) return;
    el.style.opacity='0';el.style.transform='translateY(6px)';
    setTimeout(()=>{el.innerHTML=html;el.style.opacity='1';el.style.transform='translateY(0)';},140);
  }

  /* PQ 패널 */
  fadeUpdate('dijk-pqv', s.pq.length
    ?s.pq.map(({n,d})=>{
        const isCur=n===s.cur;
        const f=isCur?'#0d2f5e':'#1e2d45';
        const sc2=isCur?'#58a6ff':'#4f6a8a';
        return `<span class="dijk-chip" style="background:${f};border-color:${sc2};color:#c9d1d9;">${n}: ${d}</span>`;
      }).join('')
    :'<span style="color:#6070a0;font-size:13px">비어있음</span>');

  /* 확정 집합 패널 */
  fadeUpdate('dijk-finv', s.fin.length
    ?s.fin.map(n=>`<span style="color:#34d399;font-weight:700;margin-right:6px">${n}</span>`).join('')
    :'<span style="color:#334155">없음</span>');

  /* dist/par 테이블 */
  const NODES=['S','A','B','C','D'];
  fadeUpdate('dijk-tbl',
    `<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px;font-size:13px;font-weight:700;">
      <div style="color:#6e7681;letter-spacing:.08em;text-transform:uppercase;padding:2px 4px;text-align:center;">node</div>
      <div style="color:#fbbf24;letter-spacing:.08em;text-transform:uppercase;padding:2px 4px;text-align:center;">dist</div>
      <div style="color:#a78bfa;letter-spacing:.08em;text-transform:uppercase;padding:2px 4px;text-align:center;">par</div>`+
    NODES.map(n=>{
      const isFin=s.fin.includes(n);
      const isCur=n===s.cur;
      const nc=isFin?'#34d399':isCur?'#58a6ff':'#8b949e';
      const nbg=isFin?'#0d2f20':isCur?'#0d2f5e':'#243450';
      const dv=s.dist[n];
      const dc=dv===INF?'#6e7681':isFin?'#6effc8':'#fde68a';
      return `
      <div style="display:flex;align-items:center;justify-content:center;padding:3px 0;">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:7px;border:1.5px solid ${nc};background:${nbg};color:${nc};font-size:15px;">${n}</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;padding:3px 0;">
        <span style="display:inline-flex;align-items:center;justify-content:center;min-width:32px;height:28px;border-radius:6px;border:1.5px solid #fbbf2488;background:#2a1f0044;color:${dc};font-size:14px;padding:0 6px;">${dv}</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;padding:3px 0;">
        <span style="display:inline-flex;align-items:center;justify-content:center;min-width:32px;height:28px;border-radius:6px;border:1.5px solid #a78bfa88;background:#28205044;color:#c4b5fd;font-size:14px;padding:0 6px;">${s.par[n]}</span>
      </div>`;
    }).join('')+
    '</div>');

  /* 설명 패널 */
  fadeUpdate('dijk-info', s.inf);
}

function dijkN(){if(cur<SS.length-1){cur++;render();}}
function dijkB(){if(cur>0){cur--;render();}}
function dijkR(){cur=0;render();}
window.dijkN=dijkN;window.dijkB=dijkB;window.dijkR=dijkR;

render();
})();
</script>
{{< /rawhtml >}}

---

## 1. 최단 경로 문제 (SSSP)

### 1.1 문제 정의

- **입력:** 가중 방향 그래프 $G = (V, E)$, 출발 정점 $s \in V$, 간선 가중치 함수 $w: E \rightarrow \mathbb{R}$
- **출력:** $s$에서 모든 정점까지의 최소 비용 경로

**최단 경로 가중치 정의:**

$$\delta(u, v) = \begin{cases} \min\{w(p) \mid p \text{는 } u \to v \text{ 경로}\} & \text{경로 존재 시} \\ \infty & \text{경로 없을 시} \end{cases}$$

---

### 1.2 Relaxation 연산

각 정점 $v$는 두 가지 속성을 유지한다:
- `v.d` : $s$에서 $v$까지 현재까지 알려진 최단 거리 추정값
- `v.π` : 현재 최단 경로에서 $v$의 선행 정점

```
RELAX(u, v, w):
    if v.d > u.d + w(u, v):
        v.d = u.d + w(u, v)
        v.π = u
```

> **핵심:** "u를 경유하면 v까지 더 짧게 갈 수 있는가?" 를 확인하고 가능하면 갱신

---

### 1.3 초기화 및 불변 조건

```
s.d = 0,  v.d = ∞  (v ≠ s)
v.π = NIL  (모든 v)
```

**불변 조건:** 항상 $v.d \geq \delta(s, v)$ 성립 → Relaxation 반복으로 $\delta(s, v)$에 수렴

---

## 2. 다익스트라 알고리즘

### 2.1 그리디 전략과 집합 S

1. 최단 경로가 확정된 정점들의 집합 $S$ 유지
2. 매 단계마다 $V - S$에서 `d`값이 최소인 정점 $u$ 선택
3. $u$를 $S$에 추가하고, $u$에서 나가는 모든 간선 Relaxation

**그리디가 성립하는 이유:** $w \geq 0$ 이면 이미 확정된 거리는 절대 더 짧아지지 않음

---

### 2.2 Min-Priority Queue

| 연산 | 역할 |
|------|------|
| `EXTRACT-MIN` | $d$값 최소 정점 추출 |
| `DECREASE-KEY` | Relaxation 후 $d$값 갱신 |

---

### 2.3 의사 코드

```
DIJKSTRA(G, w, s):
    s.d = 0,  v.d = ∞  for all v ≠ s
    PQ = V

    while PQ ≠ ∅:
        u = EXTRACT-MIN(PQ)
        for each v ∈ Adj[u]:
            RELAX(u, v, w)
```

---

### 2.4 정확성 증명 (귀류법)

- **가정:** $u.d > \delta(s, u)$ 인 정점 $u$가 존재한다고 가정
- 최단 경로 위 첫 미확정 정점 $y$, 선행자 $x \in S$ 설정
- $(x, y)$ Relaxation 완료 → $y.d \leq \delta(s, y)$
- $w \geq 0$ → $\delta(s, y) \leq \delta(s, u) < u.d$
- $\therefore y.d < u.d$ → $u$가 최솟값이라는 조건에 **모순!**
- $\therefore u.d = \delta(s, u)$ 성립 ✅

{{< rawhtml >}}
<div id="proof-wrap" style="font-family:'Space Grotesk',system-ui,sans-serif;background:linear-gradient(135deg,#1e3050 0%,#253c60 60%,#1c2d50 100%);border-radius:14px;padding:20px;box-shadow:0 8px 40px rgba(0,0,0,.6);margin:1.2rem 0;">
  <div style="display:flex;gap:8px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">
    <button onclick="proofB()" id="proof-bb" style="padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;background:#21262d;color:#c9d1d9;border:1px solid #30363d;">◀ 이전</button>
    <button onclick="proofN()" id="proof-bn" style="padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;background:#1f6feb;color:#fff;">다음 ▶</button>
    <button onclick="proofR()" style="padding:7px 18px;border:none;border-radius:8px;cursor:pointer;font-size:16px;font-weight:600;background:#21262d;color:#c9d1d9;border:1px solid #30363d;margin-left:4px;">↺ 초기화</button>
    <span id="proof-lbl" style="font-size:15px;color:#8b949e;margin-left:4px;"></span>
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start;">
    <svg id="proof-svg" viewBox="0 0 520 310" style="flex:1;min-width:280px;background:linear-gradient(135deg,#1d3050 0%,#223a5e 100%);border-radius:12px;border:1px solid #21262d;width:100%;"></svg>
    <div id="proof-info" style="flex:1;min-width:200px;background:#1e2d45;border-radius:10px;padding:14px 16px;border-left:3px solid #2f81f7;font-size:15px;font-weight:600;color:#e6edf3;line-height:1.9;min-height:160px;transition:opacity .15s,transform .15s;"></div>
  </div>
</div>
<script>
(function(){
/* ── 단계 데이터 ── */
const C3=(v,c)=>`<span style="color:${c};font-weight:800">${v}</span>`;
const STEPS=[
  {
    sSet:['s'],          /* S 집합 */
    uNode:'u',           /* 이번에 extract할 노드 */
    xNode:null,
    yNode:null,
    showP:false,         /* s→u 점선 경로 */
    showPrime:false,     /* s→x→y 초록 경로 */
    showUV:false,        /* u→v 파란 실선 */
    inf:`${C3('가정:','#f87171')} 어떤 정점 u에 대해 ${C3('u.d > δ(s,u)','#f87171')} 라고 가정하자.<br>즉, 알고리즘이 u를 S에 추가하는 순간 거리 추정이 아직 최적이 아니라는 뜻.`
  },
  {
    sSet:['s'],
    uNode:'u',xNode:null,yNode:null,
    showP:true,showPrime:false,showUV:false,
    inf:`s에서 u까지의 실제 최단 경로 P가 존재한다.<br>경로 P는 S 안의 정점들을 지나 ${C3('처음으로 S 밖으로 나가는 지점','#fbbf24')}이 있다.`
  },
  {
    sSet:['s'],
    uNode:'u',xNode:'x',yNode:'y',
    showP:true,showPrime:false,showUV:false,
    inf:`최단 경로 P 위에서 ${C3('x ∈ S','#34d399')} (확정), ${C3('y ∉ S','#f87171')} (미확정) 인 인접 쌍을 잡는다.<br>x→y 간선이 S 경계를 처음 넘는 간선이다.`
  },
  {
    sSet:['s'],
    uNode:'u',xNode:'x',yNode:'y',
    showP:true,showPrime:true,showUV:false,
    inf:`x가 S에 추가될 때 x→y를 ${C3('Relaxation','#fbbf24')} 했으므로:<br>${C3('y.d ≤ δ(s,x) + w(x,y) = δ(s,y)','#34d399')}<br>또한 불변조건 y.d ≥ δ(s,y) 이므로 → ${C3('y.d = δ(s,y)','#34d399')}`
  },
  {
    sSet:['s'],
    uNode:'u',xNode:'x',yNode:'y',
    showP:true,showPrime:true,showUV:true,
    inf:`w ≥ 0 이므로 경로 P에서 y 이후 구간도 음수가 없다:<br>${C3('δ(s,y) ≤ δ(s,u)','#a78bfa')}<br>따라서 ${C3('y.d = δ(s,y) ≤ δ(s,u) < u.d','#f87171')}<br>→ y.d < u.d 이므로 알고리즘은 u 대신 y를 먼저 뽑았어야 한다. ${C3('모순! ✗','#f87171')}`
  },
  {
    sSet:['s'],
    uNode:'u',xNode:'x',yNode:'y',
    showP:true,showPrime:true,showUV:false,
    inf:`${C3('∴ 가정이 거짓.','#34d399')}<br>u가 S에 추가되는 순간 항상 ${C3('u.d = δ(s,u)','#34d399')} 성립.<br>귀납적으로 모든 정점에 대해 최단 거리가 올바르게 확정된다. ✅`
  },
];

let cur=0;

/* ── SVG 요소 ── */
const svg=d3.select('#proof-svg');
const defs=svg.append('defs');

/* 화살표 마커 */
function mkM2(id,col){
  defs.append('marker').attr('id',id)
    .attr('viewBox','0 0 10 10').attr('refX',8).attr('refY',5)
    .attr('markerWidth',7).attr('markerHeight',7).attr('orient','auto-start-reverse')
    .append('path').attr('d','M1 2L8 5L1 8').attr('fill',col).attr('stroke',col)
    .attr('stroke-width',1).attr('stroke-linecap','round');
}
mkM2('pm-blue','#2f81f7');
mkM2('pm-green','#34d399');
mkM2('pm-yellow','#fbbf24');

/* glow 필터 */
const gF=defs.append('filter').attr('id','pgx').attr('x','-60%').attr('y','-60%').attr('width','220%').attr('height','220%');
gF.append('feGaussianBlur').attr('stdDeviation',6).attr('result','b');
const fm=gF.append('feMerge');fm.append('feMergeNode').attr('in','b');fm.append('feMergeNode').attr('in','SourceGraphic');

const MF="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif";

/* S 집합 원 배경 */
const sBg=svg.append('ellipse')
  .attr('cx',195).attr('cy',155).attr('rx',150).attr('ry',130)
  .attr('fill','#e05a5a').attr('opacity',0.13);

/* S 레이블 */
svg.append('text').attr('x',110).attr('y',55).attr('fill','#e05a5a')
  .attr('font-size',22).attr('font-weight',700).attr('font-family',MF)
  .attr('opacity',0.7).text('S');

/* 노드 좌표 */
const POS={s:{x:130,y:160},u:{x:280,y:100},x:{x:280,y:220},v:{x:420,y:100},y:{x:420,y:230}};

/* P 점선 (s→u) */
const pathP=svg.append('path')
  .attr('d','M155,155 C180,130 240,110 255,105')
  .attr('fill','none').attr('stroke','#2f81f7').attr('stroke-width',3.5)
  .attr('stroke-dasharray','10,6').attr('marker-end','url(#pm-blue)')
  .attr('opacity',0);
svg.append('text').attr('id','plbl').attr('x',185).attr('y',120)
  .attr('fill','#2f81f7').attr('font-size',18).attr('font-weight',700).attr('font-family',MF)
  .attr('opacity',0).text('P');

/* P' 초록 경로 (s→x→y) */
const pathPrime1=svg.append('path')
  .attr('d','M148,168 C170,190 230,215 255,220')
  .attr('fill','none').attr('stroke','#34d399').attr('stroke-width',2.5)
  .attr('marker-end','url(#pm-green)').attr('opacity',0);
const pathPrime2=svg.append('path')
  .attr('d','M308,222 L393,228')
  .attr('fill','none').attr('stroke','#34d399').attr('stroke-width',2.5)
  .attr('marker-end','url(#pm-green)').attr('opacity',0);
svg.append('text').attr('id','p2lbl').attr('x',345).attr('y',255)
  .attr('fill','#34d399').attr('font-size',18).attr('font-weight',700).attr('font-family',MF)
  .attr('opacity',0).text("P'");

/* u→v 파란 실선 */
const pathUV=svg.append('path')
  .attr('d','M308,100 L393,100')
  .attr('fill','none').attr('stroke','#2f81f7').attr('stroke-width',3)
  .attr('marker-end','url(#pm-blue)').attr('opacity',0);

/* 노드 그룹 */
const nodeData=[
  {id:'s',label:'s',cx:POS.s.x,cy:POS.s.y},
  {id:'u',label:'u',cx:POS.u.x,cy:POS.u.y},
  {id:'x',label:'x',cx:POS.x.x,cy:POS.x.y},
  {id:'v',label:'v',cx:POS.v.x,cy:POS.v.y},
  {id:'y',label:'y',cx:POS.y.x,cy:POS.y.y},
];

const nGs2=svg.selectAll('.pnode').data(nodeData).enter().append('g').attr('class','pnode');
nGs2.append('circle').attr('class','pbg').attr('r',26)
  .attr('cx',d=>d.cx).attr('cy',d=>d.cy)
  .attr('fill','#1c2433').attr('stroke','#3a4f6a').attr('stroke-width',2.5);
nGs2.append('text').attr('class','plbl2')
  .attr('x',d=>d.cx).attr('y',d=>d.cy)
  .attr('text-anchor','middle').attr('dominant-baseline','central')
  .attr('fill','#8b949e').attr('font-size',17).attr('font-weight',700).attr('font-family',MF)
  .text(d=>d.label);

/* ── 렌더 ── */
function render(){
  const st=STEPS[cur],T=400;
  document.getElementById('proof-bb').disabled=cur===0;
  document.getElementById('proof-bn').disabled=cur===STEPS.length-1;
  document.getElementById('proof-lbl').textContent=`${cur+1} / ${STEPS.length}`;

  /* S 배경 opacity */
  sBg.transition().duration(T).attr('opacity', st.sSet.length>0 ? 0.15 : 0.05);

  /* P 점선 */
  pathP.transition().duration(T).attr('opacity', st.showP?1:0);
  d3.select('#plbl').transition().duration(T).attr('opacity', st.showP?1:0);

  /* P' 초록 */
  const prOp=st.showPrime?1:0;
  pathPrime1.transition().duration(T).attr('opacity',prOp);
  pathPrime2.transition().duration(T).attr('opacity',prOp);
  d3.select('#p2lbl').transition().duration(T).attr('opacity',prOp);

  /* u→v */
  pathUV.transition().duration(T).attr('opacity', st.showUV?1:0);

  /* 노드 스타일 */
  nGs2.each(function(d){
    const g=d3.select(this);
    const isS=d.id==='s';
    const isU=d.id==='u' && st.uNode==='u';
    const isX=d.id==='x' && st.xNode==='x';
    const isY=d.id==='y' && st.yNode==='y';
    const isV=d.id==='v';
    let fill,stroke,lc,sw=2.5,flt=null;
    if(isS){fill='#7f1d1d';stroke='#ef4444';lc='#fff';sw=3;flt='url(#pgx)';}
    else if(isU){fill='#3b1d6e';stroke='#a78bfa';lc='#fff';sw=3;flt='url(#pgx)';}
    else if(isX&&st.showPrime){fill='#3b1d6e';stroke='#a78bfa';lc='#fff';sw=3;flt='url(#pgx)';}
    else if(isY&&st.yNode){fill='#1e2d45';stroke='#34d399';lc='#e6edf3';sw=2.5;}
    else if(isV){fill='#1e2d45';stroke='#3a4f6a';lc='#8b949e';sw=2.5;}
    else{fill='#1c2433';stroke:'#3a4f6a';lc='#8b949e';sw=2.5;}
    g.select('.pbg').transition().duration(T)
      .attr('fill',fill).attr('stroke',stroke).attr('stroke-width',sw).attr('filter',flt);
    g.select('.plbl2').transition().duration(T).attr('fill',lc);
  });

  /* 설명 패널 */
  const el=document.getElementById('proof-info');
  el.style.opacity='0';el.style.transform='translateY(6px)';
  setTimeout(()=>{el.innerHTML=st.inf;el.style.opacity='1';el.style.transform='translateY(0)';},150);
}

function proofN(){if(cur<STEPS.length-1){cur++;render();}}
function proofB(){if(cur>0){cur--;render();}}
function proofR(){cur=0;render();}
window.proofN=proofN;window.proofB=proofB;window.proofR=proofR;
render();
})();
</script>
{{< /rawhtml >}}

---

### 2.5 시간 복잡도

| 구현 | 복잡도 |
|------|--------|
| 선형 탐색 | $O(V^2)$ |
| 이진 힙 | $O((V+E)\log V)$ |
| 피보나치 힙 | $O(E + V\log V)$ |

$$T(n, m) = O((n+m)\log m) = O(m \log n)$$

> $n + m = O(m)$ 인 이유: 연결 그래프에서 $m \geq n-1$ 이므로 $n = O(m)$

---

### 2.6 Lazy Deletion (heapq 구현)

```python
from heapq import heappush, heappop

def dijkstra(graph, source):
    dist, parent = init_single_source(graph, source)
    PQ = [(0, source)]
    visited = set()

    while PQ:
        d, u = heappop(PQ)
        if u in visited:   # Lazy Deletion: 낡은 항목 버림
            continue
        visited.add(u)
        for v, w in graph[u]:
            if relax(u, v, w, dist, parent):
                heappush(PQ, (dist[v], v))  # 중복 삽입

    return dist, parent
```

**핵심:** `heapq`는 DECREASE-KEY가 없어서 중복 삽입 후 꺼낼 때 `visited`로 걸러냄

| 방식 | PQ 크기 | 복잡도 |
|------|---------|--------|
| Lazy Deletion | $O(m)$ | $O(m \log m)$ |
| 피보나치 힙 | $O(n)$ | $O(m + n\log n)$ |

---

## 3. 벨만-포드 알고리즘

### 3.1 왜 다익스트라가 실패하는가

음수 간선이 있으면 이미 확정한 정점의 거리가 나중에 더 짧아질 수 있음 → **그리디 붕괴**

```
s --(4)--> A
|          ↑
└--(2)--> B --(-5)--> A

Dijkstra: dist[A] = 4  (오답)
실제 최단: dist[A] = 2 + (-5) = -3
```

---

### 3.2 DP 전략

벨만-포드는 **동적 프로그래밍** 기반:

$$\text{dist}^{(i)}[v] = \min_{(u,v) \in E}\left(\text{dist}^{(i-1)}[u] + w(u,v)\right)$$

> $i$번 반복 후 → 최대 $i$개의 간선을 사용하는 최단 경로 확정

---

### 3.3 $|V|-1$번 반복하는 이유

- 최단 경로는 사이클을 포함하지 않음 → 최대 $n-1$개의 간선
- $n-1$번 반복이면 모든 최단 경로 확정 보장

```
BELLMAN-FORD(G, w, s):
    dist[s] = 0,  dist[v] = ∞  for all v ≠ s

    for i from 1 to |V|-1:
        for each edge (u, v) ∈ E:
            RELAX(u, v)
```

---

### 3.4 음수 사이클 탐지

$n$번째 반복에서도 갱신이 발생하면 → **음수 사이클 존재**

```python
for each edge (u, v, w):
    if dist[v] > dist[u] + w:
        return "음수 사이클 존재!"
```

---

### 3.5 시간 복잡도

$$T = O(VE) = O(nm)$$

| | Dijkstra | Bellman-Ford |
|--|---------|-------------|
| 전략 | 그리디 | DP |
| 음수 간선 | ❌ | ✅ |
| 음수 사이클 탐지 | ❌ | ✅ |
| 복잡도 | $O(m \log n)$ | $O(nm)$ |

---

## 4. 슬라이딩 퍼즐

### 4.1 반전(Inversion)의 정의

> 순열에서 $i < j$ 이고 $a_i > a_j$ 인 쌍 $(a_i, a_j)$, **빈 칸(0)은 무시**

**예시:** `1 2 3 4 5 8 0 7 6` → 반전 쌍: (8,7), (8,6), (7,6) → **반전 수 = 3**

---

### 4.2 홀수 너비 퍼즐 (3×3, 5×5)

- 수직/수평 이동 모두 반전의 홀짝성 **보존**
- 수직 이동 시 넘는 타일 수 = $n - 1$ = 짝수 → 홀짝성 유지

$$\text{풀이 가능} \iff I \equiv 0 \pmod{2}$$

---

### 4.3 짝수 너비 퍼즐 (4×4, 6×6)

- 수직 이동 시 넘는 타일 수 = $n - 1$ = **홀수** → 홀짝성 **반전**
- $I$와 $R$이 동시에 홀짝성이 바뀌어 $I + R$은 불변

$$\text{풀이 가능} \iff I + R \equiv 1 \pmod{2}$$

| $I$ | $R$ | $I+R$ | 풀이 가능 |
|-----|-----|-------|---------|
| 짝수 | 홀수 | 홀수 | ✅ |
| 홀수 | 짝수 | 홀수 | ✅ |
| 짝수 | 짝수 | 짝수 | ❌ |
| 홀수 | 홀수 | 짝수 | ❌ |

---

### 4.4 수직 이동이 홀짝성을 바꾸는 이유

```
4×4에서 수직 이동을 1차원으로 펼치면:

before: [0]  13  14  15  12
after:   13   14  15  [0]  12

12가 15, 14, 13을 하나씩 넘어감
= 인접 교환 3번 (홀수!)
→ 반전 수의 홀짝성 반전
```

---

## 5. BFS (브루트포스 탐색)

### 5.1 상태를 문자열로 표현

```python
# n=4 목표 상태
target = "123456789ABCDEF0"
# 10 이상은 A,B,C... 로 표현 (한 글자 유지)
```

---

### 5.2 BFS 구현

```python
def bfs(n, start):
    target = "123456789ABCDEF"[:n*n-1] + "0"
    queue = deque([(start, 0)])
    visited = set([start])

    while queue:
        state, depth = queue.popleft()
        if state == target:
            return depth
        blank = state.index('0')
        for di, dj in [(0,1),(1,0),(0,-1),(-1,0)]:
            new_state = move(state, blank, di, dj, n)
            if new_state and new_state not in visited:
                queue.append((new_state, depth+1))
                visited.add(new_state)
    return -1
```

---

### 5.3 3×3은 가능, 4×4는 불가능한 이유

| 퍼즐 | 전체 상태 수 | BFS 가능 |
|------|------------|---------|
| 3×3 | $9! = 362,880$ | ✅ |
| 4×4 | $16! \approx 2 \times 10^{13}$ | ❌ 메모리/시간 폭발 |

> 4×4 이상은 **A\* 알고리즘** 필요

---

## 6. A* 알고리즘

### 6.1 $f(n) = g(n) + h(n)$

| 기호 | 의미 |
|------|------|
| $g(n)$ | 시작점 → $n$까지 실제 이동 횟수 |
| $h(n)$ | $n$ → 목표까지 휴리스틱 추정값 |
| $f(n)$ | 총 예상 비용 (PQ 정렬 기준) |

```python
if new_state not in g or new_depth < g[new_state]:
    g[new_state] = new_depth
    new_f = g[new_state] + h(n, new_state)
    heappush(PQ, (new_f, new_depth, new_state))
```

---

### 6.2 맨해튼 거리 휴리스틱

$$h_{Manhattan}(n) = \sum_{\text{모든 타일}} |\Delta row| + |\Delta col|$$

```python
def h(n, state):
    total = 0
    for i, tile in enumerate(state):
        if tile == '0': continue
        cur_row, cur_col = i // n, i % n
        goal = int(tile, base=16) - 1
        goal_row, goal_col = goal // n, goal % n
        total += abs(cur_row - goal_row) + abs(cur_col - goal_col)
    return total
```

---

### 6.3 Admissibility란?

> 휴리스틱이 실제 비용을 **절대 과대평가하지 않는** 조건

$$\boxed{h(n) \leq h^*(n) \quad \text{for all } n}$$

- 과소평가 또는 정확 → **Admissible** ✅
- 과대평가 → **Not Admissible** ❌

---

### 6.4 Admissibility가 최적해를 보장하는 이유

**$f(n)$은 하한(Lower Bound):**

$$f(n) = g(n) + h(n) \leq g(n) + h^*(n) = \text{실제 최적 비용}$$

**맨해튼 거리가 Admissible인 이유:**
- 이동 1번 → 타일 하나가 정확히 1칸 이동
- 이동 1번 → 맨해튼 거리 최대 1 감소
- $h(n)$만큼 이동해야 목표 도달 → $h_{Manhattan}(n) \leq h^*(n)$ ✅

**결론:**
$$h \text{ Admissible} \implies f(n) \text{이 하한} \implies \text{PQ에서 처음 꺼낸 목표 = 최적해}$$

---

### 6.5 BFS vs A* 비교

| | BFS | A* |
|--|-----|-----|
| 전략 | 브루트포스 | 휴리스틱 탐색 |
| 정렬 기준 | `depth` | `f = g + h` |
| 방향성 | 없음 | 목표 방향 우선 |
| 최적해 | ✅ (균일 비용) | ✅ (Admissible 조건) |
| 3×3 | ✅ | ✅ |
| 4×4 | ❌ | ✅ |


## 7. 핵심 질문 Q&A 모음
 
---
 
### 7.1 heapq == PQ?
 
**A.** 같은 개념이지만 다른 레벨
 
- **PQ** = 추상 자료구조 (개념)
- **heapq** = 파이썬에서 이진 최소 힙으로 PQ를 구현한 라이브러리
```
Priority Queue (추상 개념)
        ↓ 구현
heapq (이진 최소 힙)
```
 
단, `heapq`에는 **DECREASE-KEY가 없어서** 다익스트라에서 Lazy Deletion으로 우회해야 함
 
---
 
### 7.2 heap에 노드가 한 번만 들어가나?
 
**A.** 아니다. 같은 노드가 **여러 번** 들어갈 수 있다.
 
```python
# Relaxation 성공할 때마다 무조건 새 항목 삽입
heappush(PQ, (dist[v], v))  # 기존 항목 삭제 없이 추가!
```
 
- DECREASE-KEY가 없으므로 기존 항목은 그대로 두고 새 항목 추가
- PQ 최대 크기 = $O(m)$ (간선 수만큼 쌓임)
- 꺼낼 때 `visited` 체크로 낡은 항목 버림
---
 
### 7.3 $n + m = O(m)$ 인 이유?
 
**A.** 연결 그래프에서 $m \geq n - 1$ 이기 때문
 
```
연결 그래프 조건: 정점 n개 연결 → 최소 n-1개 간선 필요
→ m ≥ n-1
→ n = O(m)
→ n + m = O(m) + O(m) = O(m)
```
 
> 비연결 그래프라면 성립 안 하지만, 다익스트라는 연결 그래프를 가정
 
---
 
### 7.4 벨만-포드는 그리디인가 DP인가?
 
**A.** **DP**다.
 
| 구분 | Dijkstra (그리디) | Bellman-Ford (DP) |
|------|-----------------|-----------------|
| 선택 방식 | 매번 최솟값 하나 확정 | 모든 간선을 반복 완화 |
| 이전 결과 활용 | ❌ | ✅ $i-1$번째 결과 → $i$번째 |
| 음수 간선 | ❌ | ✅ |
 
점화식: $\text{dist}^{(i)}[v] = \min(\text{dist}^{(i-1)}[u] + w(u,v))$ → DP의 전형적 구조
 
---
 
### 7.5 Reachable이 어디 reachable?
 
**A.** **목표 상태(Goal State)에 도달 가능**하다는 의미
 
```
목표 상태:           초기 상태:
┌─────────┐         ┌─────────┐
│ 1  2  3 │         │ 1  2  3 │
│ 4  5  6 │   ←?    │ 4  5  6 │
│ 7  8  0 │         │ 8  7  0 │
└─────────┘         └─────────┘
 
"합법적인 이동(상하좌우)만으로 목표 상태까지 갈 수 있는가?"
```
 
반전 수로 판별 가능 → 실제로 탐색하지 않아도 $O(n^2)$에 판별
 
---
 
### 7.6 4×4에서 수직 이동이 홀짝성을 바꾸는 이유?
 
**A.** 수직 이동 = 1차원으로 펼치면 인접 교환 **3번(홀수)**
 
```
before: [0]  13  14  15  12
after:   13   14  15  [0]  12
 
12가 이동하면서 13, 14, 15를 하나씩 넘어감
= 인접 교환 3번
→ 반전 수 N → N+3 (홀짝성 반전!)
```
 
| 퍼즐 너비 | 넘는 타일 수 | 홀짝 변화 |
|---------|------------|--------|
| 3 (홀수) | 2개 (짝수) | 유지 |
| 4 (짝수) | 3개 (홀수) | **반전** |
 
---
 
### 7.7 $R$을 더하는 이유?
 
**A.** 수직 이동 시 $I$와 $R$이 **동시에** 홀짝성이 바뀌어 서로 상쇄되기 때문
 
```
수직 이동 1번:
  I: 홀짝 바뀜 (+3)
  R: 홀짝 바뀜 (±1)
  ──────────────
  I+R: 홀짝 유지! (불변량)
 
목표 상태: I=0, R=1 → I+R = 1
∴ 풀이 가능 ⟺ I+R ≡ 1 (mod 2)
```
 
---
 
### 7.8 BFS가 브루트포스인가?
 
**A.** 맞다. BFS = 브루트포스
 
- 어떤 휴리스틱 없이 **가능한 모든 상태를 빠짐없이 탐색**
- 3×3: $9! = 362,880$개 → 가능
- 4×4: $16! \approx 2 \times 10^{13}$개 → 불가능 → A* 필요
---
 
### 7.9 선형 탐색 다익스트라는 PQ를 안 쓰나?
 
**A.** 맞다. PQ 대신 **배열을 선형 탐색**으로 최솟값을 찾는 방식
 
```python
# PQ 없이 매번 전체 배열 순회
u = 미방문 노드 중 dist가 최소인 노드  # O(V)
```
 
| 구현 | 최솟값 선택 | 복잡도 |
|------|-----------|--------|
| 선형 탐색 | 전체 배열 순회 $O(V)$ | $O(V^2)$ |
| heapq | `heappop` $O(\log V)$ | $O(m \log n)$ |
 
> 밀집 그래프($m \approx n^2$)에서는 오히려 선형 탐색이 유리
 
---
 
### 7.10 Lazy Deletion이 뭔가?
 
**A.** **지우지 않고 넣어두고, 꺼낼 때 버리는** 방식
 
```
문제: heapq는 DECREASE-KEY가 없음
해결: 기존 항목 삭제 대신 새 항목 추가 (중복 삽입)
 
PQ: [(3, A), (7, A)]  ← (7,A)는 낡은 항목
       ↓
(3, A) 꺼냄 → 처리 ✅
(7, A) 꺼냄 → visited 체크 → 버림 ❌
```
 
> Dijkstra에서는 `visited`로, A*에서는 `g` 값 비교로 걸러냄
 
---
 
### 7.11 A* 코드가 Lazy Deletion인가?
 
**A.** 엄밀히는 다르다
 
| | Dijkstra (Lazy Deletion) | A* 이 코드 |
|--|------------------------|-----------|
| 중복 삽입 | ✅ 무조건 | 조건부 (`new_depth < g`) |
| 거르는 시점 | **꺼낼 때** | **넣을 때** |
| 방식 | `visited` 체크 | `g` 값 비교 |
 
> A*는 Lazy Deletion보다 **"더 짧은 경로만 조건부 삽입"** 에 가까움
 
---
 
### 7.12 "길고 짧다"는 게 무슨 뜻인가?
 
**A.** 슬라이딩 퍼즐에서 "거리" = **이동 횟수**
 
```
같은 상태 X에 도달하는 두 경로:
  경로 A: 3번 이동  ← 더 짧음
  경로 B: 7번 이동  ← 더 김
 
new_depth < g[new_state]
= "지금 발견한 경로의 이동 횟수가 기존보다 적다"
```
 
---
 
### 7.13 `goal = int(tile, base=16) - 1` 이 좌표인가?
 
**A.** 아니다. **1차원 인덱스**이고, 좌표로 변환해야 맨해튼 거리 계산 가능
 
```python
goal     = int(tile, base=16) - 1   # 1차원 인덱스
goal_row = goal // n                 # 2차원 행 좌표
goal_col = goal % n                  # 2차원 열 좌표
 
# 맨해튼 거리
dist = abs(cur_row - goal_row) + abs(cur_col - goal_col)
```
 
```
n=4, tile="A" (10번 타일):
goal = 9
goal_row = 9 // 4 = 2
goal_col = 9 %  4 = 1
→ 목표 위치: (2행, 1열) ✅
```
 
---
 
### 7.14 Admissibility가 왜 중요한가? (쉽게)
 
**A.** **낙관적으로 추정해야 최적 경로를 안 놓친다**
 
```
실제 거리 = 10
 
h(n) = 7  → 낙관적 추정 ✅ → 이 경로 계속 탐색
h(n) = 13 → 비관적 추정 ❌ → 이 경로 포기 → 최적해 놓침!
```
 
> Admissible → $f(n)$이 항상 하한 → 최적 경로를 절대 건너뛰지 않음
> → PQ에서 목표를 **처음 꺼내는 순간 = 최적해**
 