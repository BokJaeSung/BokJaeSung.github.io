---
title: "Lec.03 Geometric Problems"
date: 2026-03-18T09:00:00+09:00
tags: ["알고리즘", "기하학", "CCW", "외적", "선분교차", "볼록껍질"]
cover:
  image: 'images/cover.jpg'
  alt: 'Lec.03 Geometric Problems'
  relative: true
summary: "From cross product to convex hull: a complete walkthrough of CCW, line segment intersection, and the Monotone Chain algorithm."
---

## 1. CCW란?

세 점 A, B, C가 주어졌을 때 이 점들이 **반시계 방향**으로 배치되어 있는지 판별하는 알고리즘이다.

$$CCW(A, B, C) = (B_x - A_x)(C_y - A_y) - (B_y - A_y)(C_x - A_x)$$

- 결과 > 0 → 반시계방향 (CCW)
- 결과 < 0 → 시계방향 (CW)
- 결과 = 0 → 세 점이 일직선 (Collinear)

```python
def ccw(A, B, C):
    return (B[0]-A[0]) * (C[1]-A[1]) - (B[1]-A[1]) * (C[0]-A[0])
```

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<canvas id="ccw-canvas" style="width:100%;border-radius:8px;cursor:crosshair;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:10px;margin-top:12px;align-items:stretch;">
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;">
    <div style="font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#5c6bc0;margin-bottom:8px;">Formula</div>
    <div id="ccw-coords" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#7986cb;letter-spacing:.03em;margin-bottom:6px;">-</div>
    <div id="ccw-vecs" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#80cbc4;letter-spacing:.03em;margin-bottom:6px;">-</div>
    <div id="ccw-formula" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:18px;color:#e0e0e0;letter-spacing:.03em;">-</div>
  </div>
  <div id="ccw-result" style="min-width:130px;padding:10px 18px;border-radius:6px;text-align:center;font-size:20px;font-weight:700;letter-spacing:.05em;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:2px;">-</div>
</div>
<p style="font-size:14px;color:#555;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">drag points to explore</p>
</div>
<script>
(function(){
const cv=document.getElementById('ccw-canvas');
const RATIO=560/280;
cv.style.aspectRatio=RATIO;
const ctx=cv.getContext('2d');
let W=560,H=280,dpr=1;
function resize(){
  dpr=window.devicePixelRatio||1;
  const r=cv.getBoundingClientRect();
  W=r.width;H=r.height;
  cv.width=W*dpr;cv.height=H*dpr;
  ctx.setTransform(dpr,0,0,dpr,0,0);
  draw();
}
new ResizeObserver(resize).observe(cv);
// initial grid coords (math): A=(-2,-1), B=(2,-1), C=(0,2); STEP≈W/11
const pts=[{x:178/560,y:191/280,label:'A',color:'#e53935'},{x:382/560,y:191/280,label:'B',color:'#1e88e5'},{x:280/560,y:38/280,label:'C',color:'#43a047'}];
let drag=null;
function cross(a,b,c){return (b.x-a.x)*(a.y-c.y)-(a.x-c.x)*(b.y-a.y);}
function px(p){return{x:p.x*W,y:p.y*H};}
function getStep(){return Math.round(W/11);}
function drawGrid(){
  const STEP=getStep();
  const ox=W/2,oy=H/2;
  // grid lines
  ctx.lineWidth=0.5;
  for(let i=Math.ceil(-ox/STEP);i*STEP+ox<W;i++){const x=ox+i*STEP;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.strokeStyle=i===0?'rgba(255,255,255,0.25)':'rgba(255,255,255,0.07)';ctx.stroke();}
  for(let i=Math.ceil(-oy/STEP);i*STEP+oy<H;i++){const y=oy+i*STEP;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.strokeStyle=i===0?'rgba(255,255,255,0.25)':'rgba(255,255,255,0.07)';ctx.stroke();}
  // axis arrows
  ctx.strokeStyle='rgba(255,255,255,0.35)';ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(8,oy);ctx.lineTo(W-8,oy);ctx.stroke();
  ctx.beginPath();ctx.moveTo(W-8,oy);ctx.lineTo(W-15,oy-5);ctx.moveTo(W-8,oy);ctx.lineTo(W-15,oy+5);ctx.stroke();
  ctx.beginPath();ctx.moveTo(ox,H-8);ctx.lineTo(ox,8);ctx.stroke();
  ctx.beginPath();ctx.moveTo(ox,8);ctx.lineTo(ox-5,15);ctx.moveTo(ox,8);ctx.lineTo(ox+5,15);ctx.stroke();
  // axis labels
  ctx.fillStyle='rgba(255,255,255,0.4)';ctx.font='bold 11px sans-serif';
  ctx.textAlign='left';ctx.fillText('x',W-10,oy-6);
  ctx.textAlign='center';ctx.fillText('y',ox+10,12);
  // tick labels (math coords: y flipped)
  ctx.fillStyle='rgba(255,255,255,0.25)';ctx.font='9px sans-serif';
  for(let x=ox+STEP;x<W-20;x+=STEP){const v=Math.round((x-ox)/STEP);ctx.textAlign='center';ctx.fillText(v,x,oy+12);}
  for(let x=ox-STEP;x>20;x-=STEP){const v=Math.round((x-ox)/STEP);ctx.textAlign='center';ctx.fillText(v,x,oy+12);}
  for(let y=oy-STEP;y>12;y-=STEP){const v=Math.round((oy-y)/STEP);ctx.textAlign='right';ctx.fillText(v,ox-4,y+3);}
  for(let y=oy+STEP;y<H-8;y+=STEP){const v=Math.round((oy-y)/STEP);ctx.textAlign='right';ctx.fillText(v,ox-4,y+3);}
}
function draw(){
  ctx.clearRect(0,0,W,H);
  drawGrid();
  const [A,B,C]=pts.map(px);
  const STEP=getStep();
  const ax=Math.round((A.x-W/2)/STEP),ay=Math.round((H/2-A.y)/STEP);
  const bx_=Math.round((B.x-W/2)/STEP),by_=Math.round((H/2-B.y)/STEP);
  const cx_=Math.round((C.x-W/2)/STEP),cy_=Math.round((H/2-C.y)/STEP);
  const bx=bx_-ax,by=by_-ay,cx=cx_-ax,cy=cy_-ay,rv=bx*cy-by*cx;
  ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.lineTo(C.x,C.y);ctx.closePath();
  ctx.fillStyle=rv===0?'rgba(150,150,150,0.08)':rv>0?'rgba(67,160,71,0.18)':'rgba(229,57,53,0.18)';ctx.fill();
  const arr=(x1,y1,x2,y2,col)=>{
    const dx=x2-x1,dy=y2-y1,len=Math.sqrt(dx*dx+dy*dy);if(len<1)return;
    const ux=dx/len,uy=dy/len,r=12;
    ctx.beginPath();ctx.moveTo(x1+ux*r,y1+uy*r);ctx.lineTo(x2-ux*r,y2-uy*r);
    ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
    const a=Math.atan2(dy,dx);
    ctx.beginPath();ctx.moveTo(x2-ux*r,y2-uy*r);ctx.lineTo(x2-ux*r-Math.cos(a-.4)*9,y2-uy*r-Math.sin(a-.4)*9);ctx.moveTo(x2-ux*r,y2-uy*r);ctx.lineTo(x2-ux*r-Math.cos(a+.4)*9,y2-uy*r-Math.sin(a+.4)*9);ctx.strokeStyle=col;ctx.lineWidth=2.5;ctx.stroke();
  };
  arr(A.x,A.y,B.x,B.y,'#ef5350');arr(B.x,B.y,C.x,C.y,'#66bb6a');arr(C.x,C.y,A.x,A.y,'#42a5f5');
  pts.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q.x,q.y,10,0,Math.PI*2);ctx.fillStyle=p.color;ctx.fill();ctx.strokeStyle='#1a1d27';ctx.lineWidth=2.5;ctx.stroke();ctx.fillStyle='#fff';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.fillText(p.label,q.x,q.y-17);});
  document.getElementById('ccw-coords').textContent=`A(${ax}, ${ay})  B(${bx_}, ${by_})  C(${cx_}, ${cy_})`;
  document.getElementById('ccw-vecs').textContent=`AB\u2192(${bx}, ${by})  AC\u2192(${cx}, ${cy})`;
  document.getElementById('ccw-formula').textContent=`(${bx})(${cy}) − (${by})(${cx}) = ${rv}`;
  const res=document.getElementById('ccw-result');
  if(rv===0){res.innerHTML='<span style="font-size:20px">—</span><span style="font-size:11px;font-weight:600;letter-spacing:.06em;margin-top:2px;">COLLINEAR</span>';res.style.background='#2a2d3a';res.style.color='#9e9e9e';}
  else if(rv>0){res.innerHTML='<span style="font-size:22px">↺</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">CCW</span>';res.style.background='#1b3a1f';res.style.color='#69f0ae';}
  else{res.innerHTML='<span style="font-size:22px">↻</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">CW</span>';res.style.background='#3a1a1a';res.style.color='#ff5252';}
}
function pos(e){const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:(t.clientX-r.left)/r.width,y:(t.clientY-r.top)/r.height};}
cv.addEventListener('mousedown',e=>{const p=pos(e);drag=pts.reduce((b,pt,i)=>{const q=px(pt),pp={x:p.x*W,y:p.y*H};const d=Math.hypot(q.x-pp.x,q.y-pp.y);return d<(b?b.d:22)?{i,d}:b;},null);});
cv.addEventListener('mousemove',e=>{if(!drag)return;const p=pos(e);pts[drag.i].x=Math.max(16/W,Math.min(1-16/W,p.x));pts[drag.i].y=Math.max(16/H,Math.min(1-16/H,p.y));draw();});
cv.addEventListener('mouseup',e=>{if(!drag)return;const p=pos(e);const S=getStep();const rx=Math.round((p.x*W-W/2)/S),ry=Math.round((p.y*H-H/2)/S);pts[drag.i].x=Math.max(16/W,Math.min(1-16/W,(W/2+rx*S)/W));pts[drag.i].y=Math.max(16/H,Math.min(1-16/H,(H/2+ry*S)/H));drag=null;draw();});
})();
</script>
{{< /rawhtml >}}

---

## 2. 외적(Cross Product)

CCW 공식 $x_1y_2 - x_2y_1$ 은 **3D 외적의 z성분**이다.

두 벡터를 3D로 확장하면 (z=0):

$$\mathbf{a} \times \mathbf{b} = (0,\ 0,\ x_1y_2 - x_2y_1)$$

x, y 성분이 0이므로 z성분만 남고, 그 부호가 회전 방향을 결정한다.

### 평행사변형 넓이

외적의 크기 = 두 벡터가 만드는 **평행사변형의 넓이**

$$|\mathbf{a} \times \mathbf{b}| = |\mathbf{a}||\mathbf{b}|\sin\theta$$

두 공식이 같다는 증명: $\mathbf{a} = (|\mathbf{a}|\cos\alpha,\ |\mathbf{a}|\sin\alpha)$ 로 놓으면

$$x_1y_2 - x_2y_1 = |\mathbf{a}||\mathbf{b}|(\cos\alpha\sin\beta - \sin\alpha\cos\beta) = |\mathbf{a}||\mathbf{b}|\sin(\beta - \alpha)$$

즉 $x_1y_2 - x_2y_1$ 은 좌표 계산용, $|\mathbf{a}||\mathbf{b}|\sin\theta$ 는 기하학적 해석용으로 **수학적으로 동일**하다.

### 2D vs 3D 외적

| | 2D | 3D |
|---|---|---|
| 공식 | $x_1y_2 - x_2y_1$ | $(y_1z_2-z_1y_2,\ z_1x_2-x_1z_2,\ x_1y_2-y_1x_2)$ |
| 결과 | 스칼라 | 벡터 |
| 관계 | 3D z성분만 꺼낸 것 | z=0 놓으면 2D와 동일 |

### 부호 결정 원리

2D에서 z축은 화면을 수직으로 뚫는 방향이다. **오른손 법칙**(convention)에 의해:

- 반시계 회전 → 엄지 화면 밖(+z) → 외적 **양수**
- 시계 회전 → 엄지 화면 안(-z) → 외적 **음수**

이는 수학적 증명이 아닌 오른손 좌표계로의 **약속**이다.

---

## 3. 선분 교차 판별

### 핵심 아이디어: Straddle

한 선분이 다른 선분의 직선을 **"걸치는가(straddle)"** 를 CCW로 판별한다.

$$d_1 = CCW(p_1, p_2, p_3), \quad d_2 = CCW(p_1, p_2, p_4)$$

$$d_1 \cdot d_2 < 0 \implies p_3, p_4 \text{ 가 직선 } p_1p_2 \text{ 의 양쪽}$$

조건 하나만으로는 부족하다. **직선** 기준이라 선분이 짧으면 교점에 못 미칠 수 있기 때문이다. 반대쪽도 확인해야 한다:

$$d_3 = CCW(p_3, p_4, p_1), \quad d_4 = CCW(p_3, p_4, p_2)$$

| 조건 | 의미 |
|------|------|
| $d_1 \cdot d_2 < 0$ | $p_3, p_4$ 가 $p_1p_2$ 직선 양쪽 |
| $d_3 \cdot d_4 < 0$ | $p_1, p_2$ 가 $p_3p_4$ 직선 양쪽 |
| **둘 다 만족** | **진짜 교차** |

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<canvas id="seg-canvas" style="width:100%;border-radius:8px;cursor:crosshair;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:10px;margin-top:12px;align-items:stretch;">
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;">
    <div style="font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#5c6bc0;margin-bottom:8px;">Values</div>
    <div id="seg-d12" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#ef9a9a;letter-spacing:.03em;margin-bottom:5px;">-</div>
    <div id="seg-d34" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#90caf9;letter-spacing:.03em;margin-bottom:5px;">-</div>
    <div id="seg-vals" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:18px;color:#e0e0e0;letter-spacing:.03em;">-</div>
  </div>
  <div id="seg-result" style="min-width:130px;padding:10px 18px;border-radius:6px;text-align:center;font-size:20px;font-weight:700;letter-spacing:.05em;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:2px;">-</div>
</div>
<p style="font-size:14px;color:#555;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">red = seg1(p1p2) · blue = seg2(p3p4) · drag to explore</p>
</div>
<script>
(function(){
const cv=document.getElementById('seg-canvas');
const RATIO=560/280;cv.style.aspectRatio=RATIO;
const ctx=cv.getContext('2d');
let W=560,H=280,dpr=1;
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
new ResizeObserver(resize).observe(cv);
function getStep(){return Math.round(W/11);}
// initial positions in grid coords: p1=(-2,-2), p2=(2,1), p3=(-2,1), p4=(2,-2)
const pts=[
  {x:(280-2*51)/560,y:(140+2*51)/280,label:'p1',c:'#e53935'},
  {x:(280+2*51)/560,y:(140-1*51)/280,label:'p2',c:'#e53935'},
  {x:(280-2*51)/560,y:(140-1*51)/280,label:'p3',c:'#1e88e5'},
  {x:(280+2*51)/560,y:(140+2*51)/280,label:'p4',c:'#1e88e5'}
];
let drag=null;
function px(p){return{x:p.x*W,y:p.y*H};}
// integer grid coords (math y-up) from pixel coords — for exact ===0 detection
function gpx(p){const S=getStep();return{x:Math.round((p.x-W/2)/S),y:Math.round((H/2-p.y)/S)};}
function ccwG(a,b,c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
function ccw(a,b,c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
function onSeg(p,q,r){return Math.min(p.x,q.x)<=r.x&&r.x<=Math.max(p.x,q.x)&&Math.min(p.y,q.y)<=r.y&&r.y<=Math.max(p.y,q.y);}
// returns {type:'general'}|{type:'collinear',pts:[...touching points]}|false
function intersects(p1,p2,p3,p4){
  const [g1,g2,g3,g4]=[p1,p2,p3,p4].map(gpx);
  const d1=ccwG(g1,g2,g3),d2=ccwG(g1,g2,g4),d3=ccwG(g3,g4,g1),d4=ccwG(g3,g4,g2);
  if(d1*d2<0&&d3*d4<0)return{type:'general'};
  const tp=[];
  if(d1===0&&onSeg(p1,p2,p3))tp.push(p3);
  if(d2===0&&onSeg(p1,p2,p4))tp.push(p4);
  if(d3===0&&onSeg(p3,p4,p1))tp.push(p1);
  if(d4===0&&onSeg(p3,p4,p2))tp.push(p2);
  if(tp.length)return{type:'collinear',pts:tp};
  return false;
}
function drawGrid(){
  const STEP=getStep();const ox=W/2,oy=H/2;
  ctx.lineWidth=0.5;
  for(let i=Math.ceil(-ox/STEP);i*STEP+ox<W;i++){const x=ox+i*STEP;ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.strokeStyle=i===0?'rgba(255,255,255,0.25)':'rgba(255,255,255,0.07)';ctx.stroke();}
  for(let i=Math.ceil(-oy/STEP);i*STEP+oy<H;i++){const y=oy+i*STEP;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.strokeStyle=i===0?'rgba(255,255,255,0.25)':'rgba(255,255,255,0.07)';ctx.stroke();}
  ctx.strokeStyle='rgba(255,255,255,0.35)';ctx.lineWidth=1.5;
  ctx.beginPath();ctx.moveTo(8,oy);ctx.lineTo(W-8,oy);ctx.stroke();
  ctx.beginPath();ctx.moveTo(W-8,oy);ctx.lineTo(W-15,oy-5);ctx.moveTo(W-8,oy);ctx.lineTo(W-15,oy+5);ctx.stroke();
  ctx.beginPath();ctx.moveTo(ox,H-8);ctx.lineTo(ox,8);ctx.stroke();
  ctx.beginPath();ctx.moveTo(ox,8);ctx.lineTo(ox-5,15);ctx.moveTo(ox,8);ctx.lineTo(ox+5,15);ctx.stroke();
  ctx.fillStyle='rgba(255,255,255,0.4)';ctx.font='bold 11px sans-serif';
  ctx.textAlign='left';ctx.fillText('x',W-10,oy-6);
  ctx.textAlign='center';ctx.fillText('y',ox+10,12);
  ctx.fillStyle='rgba(255,255,255,0.25)';ctx.font='9px sans-serif';
  for(let x=ox+STEP;x<W-20;x+=STEP){const v=Math.round((x-ox)/STEP);ctx.textAlign='center';ctx.fillText(v,x,oy+12);}
  for(let x=ox-STEP;x>20;x-=STEP){const v=Math.round((x-ox)/STEP);ctx.textAlign='center';ctx.fillText(v,x,oy+12);}
  for(let y=oy-STEP;y>12;y-=STEP){const v=Math.round((oy-y)/STEP);ctx.textAlign='right';ctx.fillText(v,ox-4,y+3);}
  for(let y=oy+STEP;y<H-8;y+=STEP){const v=Math.round((oy-y)/STEP);ctx.textAlign='right';ctx.fillText(v,ox-4,y+3);}
}
function sgn(v){return v>0?'> 0':v<0?'< 0':'= 0';}
function draw(){
  ctx.clearRect(0,0,W,H);
  drawGrid();
  const [p1,p2,p3,p4]=pts.map(px);
  const [g1,g2,g3,g4]=[p1,p2,p3,p4].map(gpx);
  const d1=ccwG(g1,g2,g3),d2=ccwG(g1,g2,g4),d3=ccwG(g3,g4,g1),d4=ccwG(g3,g4,g2);
  const hit=intersects(p1,p2,p3,p4);
  ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#ef5350';ctx.lineWidth=2.5;ctx.stroke();
  ctx.beginPath();ctx.moveTo(p3.x,p3.y);ctx.lineTo(p4.x,p4.y);ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;ctx.stroke();
  pts.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q.x,q.y,10,0,Math.PI*2);ctx.fillStyle=p.c;ctx.fill();ctx.strokeStyle='#1a1d27';ctx.lineWidth=2.5;ctx.stroke();ctx.fillStyle='#fff';ctx.font='bold 12px sans-serif';ctx.textAlign='center';ctx.fillText(p.label,q.x,q.y-16);});
  if(hit){
    if(hit.type==='general'){const dx=p2.x-p1.x,dy=p2.y-p1.y,ex=p4.x-p3.x,ey=p4.y-p3.y,dv=dx*ey-dy*ex;if(dv!==0){const t=((p3.x-p1.x)*ey-(p3.y-p1.y)*ex)/dv;const ix=p1.x+t*dx,iy=p1.y+t*dy;ctx.beginPath();ctx.arc(ix,iy,8,0,Math.PI*2);ctx.fillStyle='#ffd740';ctx.fill();ctx.strokeStyle='#1a1d27';ctx.lineWidth=2;ctx.stroke();}}
    else{const seen=new Set();hit.pts.forEach(p=>{const k=`${p.x},${p.y}`;if(seen.has(k))return;seen.add(k);ctx.beginPath();ctx.arc(p.x,p.y,9,0,Math.PI*2);ctx.fillStyle='#ffd740';ctx.fill();ctx.strokeStyle='#1a1d27';ctx.lineWidth=2;ctx.stroke();});}
  }
  document.getElementById('seg-d12').textContent=`d1 = CCW(p1,p2,p3) ${sgn(d1)}   d2 = CCW(p1,p2,p4) ${sgn(d2)}`;
  document.getElementById('seg-d34').textContent=`d3 = CCW(p3,p4,p1) ${sgn(d3)}   d4 = CCW(p3,p4,p2) ${sgn(d4)}`;
  const sgnProd=(a,b,sa,sb)=>a*b>0?'> 0':a*b<0?'< 0':a===0&&b===0?`= 0  (${sa}=0, ${sb}=0)`:a===0?`= 0  (${sa}=0)`:`= 0  (${sb}=0)`;
  document.getElementById('seg-vals').textContent=`d1\u00b7d2 ${sgnProd(d1,d2,'d1','d2')}   d3\u00b7d4 ${sgnProd(d3,d4,'d3','d4')}`;
  const res=document.getElementById('seg-result');
  if(hit&&hit.type==='general'){res.innerHTML='<span style="font-size:22px">\u2715</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">INTERSECT</span>';res.style.background='#1b3a1f';res.style.color='#69f0ae';}
  else if(hit&&hit.type==='collinear'){res.innerHTML='<span style="font-size:20px">\u2014</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">COLLINEAR</span>';res.style.background='#2a2d3a';res.style.color='#ffd740';}
  else{res.innerHTML='<span style="font-size:22px">\u2225</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">NO CROSS</span>';res.style.background='#3a1a1a';res.style.color='#ff5252';}
}
function pos(e){const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:(t.clientX-r.left)/r.width,y:(t.clientY-r.top)/r.height};}
cv.addEventListener('mousedown',e=>{const p=pos(e);drag=pts.reduce((b,pt,i)=>{const q=px(pt),pp={x:p.x*W,y:p.y*H};const d=Math.hypot(q.x-pp.x,q.y-pp.y);return d<(b?b.d:22)?{i,d}:b;},null);});
cv.addEventListener('mousemove',e=>{if(!drag)return;const p=pos(e);pts[drag.i].x=Math.max(16/W,Math.min(1-16/W,p.x));pts[drag.i].y=Math.max(16/H,Math.min(1-16/H,p.y));draw();});
cv.addEventListener('mouseup',e=>{if(!drag)return;const p=pos(e);const S=getStep();const rx=Math.round((p.x*W-W/2)/S),ry=Math.round((p.y*H-H/2)/S);pts[drag.i].x=Math.max(16/W,Math.min(1-16/W,(W/2+rx*S)/W));pts[drag.i].y=Math.max(16/H,Math.min(1-16/H,(H/2+ry*S)/H));drag=null;draw();});
})();
</script>
{{< /rawhtml >}}

### 최종 규칙

두 선분은 다음 중 하나를 만족하면 교차한다.

**Case 1. General** — $d_1 \cdot d_2 < 0$ AND $d_3 \cdot d_4 < 0$

**Case 2. Collinear** — $d$ 값 중 하나라도 0이면, 해당 끝점이 다른 선분 위에 있는지 체크

$$\text{onSeg}(p, q, r): \quad \min(p_x, q_x) \le r_x \le \max(p_x, q_x) \quad \text{AND} \quad \min(p_y, q_y) \le r_y \le \max(p_y, q_y)$$

```python
def on_segment(p, q, r):
    return (min(p[0],q[0]) <= r[0] <= max(p[0],q[0]) and
            min(p[1],q[1]) <= r[1] <= max(p[1],q[1]))

def intersects(p1, p2, p3, p4):
    d1 = ccw(p1, p2, p3);  d2 = ccw(p1, p2, p4)
    d3 = ccw(p3, p4, p1);  d4 = ccw(p3, p4, p2)

    if d1*d2 < 0 and d3*d4 < 0: return True

    if d1 == 0 and on_segment(p1, p2, p3): return True
    if d2 == 0 and on_segment(p1, p2, p4): return True
    if d3 == 0 and on_segment(p3, p4, p1): return True
    if d4 == 0 and on_segment(p3, p4, p2): return True

    return False
```

---

## 4. 볼록 껍질 (Convex Hull)

여러 점들을 모두 포함하는 **가장 작은 볼록 다각형**이다.

### 핵심 원리 (두 알고리즘 공통)

최신 세 점 A, B, C에서:

$$CCW(A, B, C) > 0 \implies \text{반시계 → B 유지}$$
$$CCW(A, B, C) \le 0 \implies \text{시계 or 일직선 → B 제거}$$

B가 새 껍질이 되는 게 아니라, **볼록성을 깨는 점 B를 제거**하는 것이다.

### Monotone Chain

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<canvas id="mc-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:6px;margin-top:12px;align-items:center;">
  <button onclick="mcStep(-1)" style="padding:7px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:14px;color:#b0b8d0;transition:background .15s;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">&#9664;</button>
  <button onclick="mcStep(1)" style="padding:7px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:14px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">&#9654;</button>
  <button onclick="mcRestart()" style="padding:7px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:14px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">&#8635;</button>
  <span id="mc-desc" style="font-size:16px;font-weight:700;letter-spacing:.1em;color:#5c6bc0;margin-left:8px;text-transform:uppercase;"></span>
</div>
<div style="display:flex;gap:10px;margin-top:8px;align-items:stretch;">
  <div id="mc-explain" style="flex:1;font-size:17px;color:#b0b8d0;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;min-height:36px;letter-spacing:.02em;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;"></div>
  <div id="mc-stack" style="min-width:150px;background:#1a1d27;border-left:3px solid #37474f;border-radius:6px;padding:10px 14px;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;letter-spacing:.03em;">-</div>
</div>
<p style="font-size:10px;color:#555;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">red = lower hull · blue = upper hull · green = done · &#9654; to step · &#8635; to restart</p>
</div>
<script>
(function(){
let pts=[],steps=[],idx=0;
const cv=document.getElementById('mc-canvas');
cv.style.aspectRatio='560/260';
const ctx=cv.getContext('2d');
let W=560,H=260,dpr=1;
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);initPts();build();if(steps.length)render();}
new ResizeObserver(resize).observe(cv);
function cross(O,A,B){return (A.x-O.x)*(B.y-O.y)-(A.y-O.y)*(B.x-O.x);}
function drawGrid(){
  ctx.lineWidth=0.5;
  const GX=Math.round(W/10),GY=Math.round(H/8);
  for(let x=GX/2;x<W;x+=GX){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.strokeStyle='rgba(255,255,255,0.05)';ctx.stroke();}
  for(let y=GY/2;y<H;y+=GY){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.strokeStyle='rgba(255,255,255,0.05)';ctx.stroke();}
}
// fixed example — ratios of 560×260, good spread with interior + hull points
const FIXED_PTS=[
  [0.10,0.73],[0.22,0.23],[0.35,0.88],[0.48,0.12],[0.50,0.55],
  [0.58,0.80],[0.65,0.35],[0.72,0.65],[0.85,0.20],[0.90,0.78]
];
function initPts(){pts=FIXED_PTS.map(([rx,ry])=>({x:rx*W,y:ry*H}));}
function restart(){initPts();build();idx=0;render();}
function build(){
  steps=[];
  const s=[...pts].sort((a,b)=>a.x===b.x?a.y-b.y:a.x-b.x);
  steps.push({lo:[],up:[],s,desc:'① x\uc88c\ud45c \uc815\ub82c',ex:'\ubaa8\ub4e0 \uc810\uc744 x\uc88c\ud45c \uc21c\uc73c\ub85c \uc815\ub82c\ud569\ub2c8\ub2e4.'});
  let lo=[];
  for(let i=0;i<s.length;i++){
    while(lo.length>=2&&cross(lo[lo.length-2],lo[lo.length-1],s[i])<=0){lo.pop();steps.push({lo:[...lo],up:[],s,cur:s[i],desc:'\u2462 \uc544\ub798\uaecd\uc9c8 - CW \uc81c\uac70',ex:'CCW \u2264 0 \u2192 \uc774\uc804 \uc810 \uc81c\uac70'});}
    lo.push(s[i]);steps.push({lo:[...lo],up:[],s,cur:s[i],desc:'\u2461 \uc544\ub798 \uaecd\uc9c8',ex:`(${Math.round(s[i].x)}, ${Math.round(s[i].y)}) \ucd94\uac00`});
  }
  let up=[];
  for(let i=s.length-1;i>=0;i--){
    while(up.length>=2&&cross(up[up.length-2],up[up.length-1],s[i])<=0){up.pop();steps.push({lo:[...lo],up:[...up],s,cur:s[i],desc:'\u2462 \uc704\uaecd\uc9c8 - CW \uc81c\uac70',ex:'CCW \u2264 0 \u2192 \uc774\uc804 \uc810 \uc81c\uac70'});}
    up.push(s[i]);steps.push({lo:[...lo],up:[...up],s,cur:s[i],desc:'\u2462 \uc704 \uaecd\uc9c8',ex:`(${Math.round(s[i].x)}, ${Math.round(s[i].y)}) \ucd94\uac00`});
  }
  const hull=[...lo.slice(0,-1),...up.slice(0,-1)];
  steps.push({lo:[...lo],up:[...up],hull,s,desc:'\u2713 \uc644\uc131!',ex:'\uc544\ub798 + \uc704 \ud569\uce58\uba74 \ubcfc\ub85d \uaecd\uc9c8 \uc644\uc131!'});
}
function render(){
  ctx.clearRect(0,0,W,H);
  drawGrid();
  const st=steps[idx];
  if(st.hull){ctx.beginPath();st.hull.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.closePath();ctx.fillStyle='rgba(105,240,174,0.1)';ctx.fill();ctx.strokeStyle='#69f0ae';ctx.lineWidth=2.5;ctx.stroke();}
  if(st.lo&&st.lo.length>1){ctx.beginPath();st.lo.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.strokeStyle='#ef5350';ctx.lineWidth=2.5;ctx.stroke();}
  if(st.up&&st.up.length>1){ctx.beginPath();st.up.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;ctx.stroke();}
  st.s.forEach((p,i)=>{
    const inLo=st.lo&&st.lo.some(q=>q===p),inUp=st.up&&st.up.some(q=>q===p);
    const col=st.hull?'#69f0ae':inLo?'#ef5350':inUp?'#42a5f5':'#4a4e5e';
    ctx.beginPath();ctx.arc(p.x,p.y,8,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();ctx.strokeStyle='#1a1d27';ctx.lineWidth=2;ctx.stroke();
    ctx.fillStyle=st.hull||inLo||inUp?'#e0e0e0':'#777';ctx.font='bold 13px sans-serif';ctx.textAlign='center';ctx.fillText(i+1,p.x,p.y-15);
  });
  if(st.cur){ctx.beginPath();ctx.arc(st.cur.x,st.cur.y,12,0,Math.PI*2);ctx.strokeStyle='#ffd740';ctx.lineWidth=2.5;ctx.stroke();}
  const loLen=st.lo?st.lo.length:0,upLen=st.up?st.up.length:0;
  document.getElementById('mc-desc').textContent=`${idx+1} / ${steps.length}  \u2014  ${st.desc}`;
  document.getElementById('mc-explain').textContent=st.ex;
  const sIdx=p=>st.s.indexOf(p)+1;
  document.getElementById('mc-stack').innerHTML=`<div style="font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#ef9a9a;margin-bottom:4px;">Lower [${loLen}]</div><div style="font-size:15px;color:#ef9a9a;margin-bottom:8px;">${st.lo&&st.lo.length?st.lo.map(p=>sIdx(p)).join(' \u2192 '):'\u2014'}</div><div style="font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#90caf9;margin-bottom:4px;">Upper [${upLen}]</div><div style="font-size:15px;color:#90caf9;">${st.up&&st.up.length?st.up.map(p=>sIdx(p)).join(' \u2192 '):'\u2014'}</div>`;
}
window.mcStep=d=>{idx=Math.max(0,Math.min(steps.length-1,idx+d));render();};
window.mcRestart=restart;
restart();
})();
</script>
{{< /rawhtml >}}

**아이디어**: x좌표 정렬 → 아래 껍질(왼→오) → 위 껍질(오→왼) → 합치기

위아래를 나누는 이유: 한 방향만 훑으면 위/아래 경계를 동시에 처리하다 오목한 부분이 생긴다. 각자 한 방향만 담당하면 CCW 조건 하나로 깔끔하게 처리된다.

```python
def monotone_chain(points):
    points = sorted(set(points))
    lower = []
    for p in points:
        while len(lower) >= 2 and ccw(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and ccw(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]
```

### Graham Scan

**아이디어**: 가장 아래 점 기준 → 극각(각도) 순 정렬 → 반시계 한 바퀴

```python
def graham_scan(points):
    pivot = min(points, key=lambda p: (p[1], p[0]))
    sorted_pts = sorted(points, key=lambda p: math.atan2(p[1]-pivot[1], p[0]-pivot[0]))
    hull = []
    for p in sorted_pts:
        while len(hull) >= 2 and ccw(hull[-2], hull[-1], p) <= 0:
            hull.pop()
        hull.append(p)
    return hull
```

### 두 알고리즘 비교

| | Monotone Chain | Graham Scan |
|---|---|---|
| 정렬 기준 | **x좌표** | **극각 (각도)** |
| 진행 방향 | 아래/위 각 1회 | 반시계 한 바퀴 |
| 구현 난이도 | 단순 | 각도 계산 필요 |
| 시간복잡도 | $O(n \log n)$ | $O(n \log n)$ |
| 핵심 로직 | CCW ≤ 0 이면 pop | 동일 |

결과는 동일하다. Monotone Chain이 구현이 더 단순해서 실무에서 선호된다.