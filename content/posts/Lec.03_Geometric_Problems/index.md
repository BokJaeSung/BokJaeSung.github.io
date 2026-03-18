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
    <div style="font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#5c6bc0;margin-bottom:6px;">Formula</div>
    <div id="ccw-formula" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:13px;color:#e0e0e0;letter-spacing:.03em;">-</div>
  </div>
  <div id="ccw-result" style="min-width:130px;padding:10px 18px;border-radius:6px;text-align:center;font-size:14px;font-weight:700;letter-spacing:.05em;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:2px;">-</div>
</div>
<p style="font-size:10px;color:#555;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">drag points to explore</p>
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
const pts=[{x:140/560,label:'A',color:'#e53935'},{x:320/560,label:'B',color:'#1e88e5'},{x:230/560,label:'C',color:'#43a047'}].map((p,i)=>({x:p.x,y:[210/280,210/280,80/280][i],label:p.label,color:p.color}));
let drag=null;
function cross(a,b,c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
function px(p){return{x:p.x*W,y:p.y*H};}
function draw(){
  ctx.clearRect(0,0,W,H);
  const [A,B,C]=pts.map(px);
  const val=cross(A,B,C);
  ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.lineTo(C.x,C.y);ctx.closePath();
  ctx.fillStyle=val===0?'rgba(150,150,150,0.08)':val>0?'rgba(67,160,71,0.18)':'rgba(229,57,53,0.18)';ctx.fill();
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
  const bx=Math.round(B.x-A.x),by=Math.round(B.y-A.y),cx=Math.round(C.x-A.x),cy=Math.round(C.y-A.y),rv=Math.round(val);
  document.getElementById('ccw-formula').textContent=`(${bx})(${cy}) − (${by})(${cx}) = ${rv}`;
  const res=document.getElementById('ccw-result');
  if(val===0){res.innerHTML='<span style="font-size:20px">—</span><span style="font-size:11px;font-weight:600;letter-spacing:.06em;margin-top:2px;">COLLINEAR</span>';res.style.background='#2a2d3a';res.style.color='#9e9e9e';}
  else if(val>0){res.innerHTML='<span style="font-size:22px">↺</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">CCW</span>';res.style.background='#1b3a1f';res.style.color='#69f0ae';}
  else{res.innerHTML='<span style="font-size:22px">↻</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">CW</span>';res.style.background='#3a1a1a';res.style.color='#ff5252';}
}
function pos(e){const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:(t.clientX-r.left)/r.width,y:(t.clientY-r.top)/r.height};}
cv.addEventListener('mousedown',e=>{const p=pos(e);drag=pts.reduce((b,pt,i)=>{const q=px(pt),pp={x:p.x*W,y:p.y*H};const d=Math.hypot(q.x-pp.x,q.y-pp.y);return d<(b?b.d:22)?{i,d}:b;},null);});
cv.addEventListener('mousemove',e=>{if(!drag)return;const p=pos(e);pts[drag.i].x=Math.max(16/W,Math.min(1-16/W,p.x));pts[drag.i].y=Math.max(16/H,Math.min(1-16/H,p.y));draw();});
cv.addEventListener('mouseup',()=>drag=null);
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
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:12px;color:#b0b8d0;letter-spacing:.03em;" id="seg-vals">-</div>
  <div id="seg-result" style="min-width:110px;padding:10px 18px;border-radius:6px;text-align:center;font-size:14px;font-weight:700;letter-spacing:.05em;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:2px;">-</div>
</div>
<p style="font-size:10px;color:#555;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">red = seg1(p1p2) · blue = seg2(p3p4) · drag to explore</p>
</div>
<script>
(function(){
const cv=document.getElementById('seg-canvas');
cv.style.aspectRatio='560/260';
const ctx=cv.getContext('2d');
let W=560,H=260,dpr=1;
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);draw();}
new ResizeObserver(resize).observe(cv);
const pts=[{x:100/560,y:200/260,label:'p1',c:'#e53935'},{x:300/560,y:90/260,label:'p2',c:'#e53935'},{x:90/560,y:100/260,label:'p3',c:'#1e88e5'},{x:310/560,y:210/260,label:'p4',c:'#1e88e5'}];
let drag=null;
function px(p){return{x:p.x*W,y:p.y*H};}
function ccw(a,b,c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
function onSeg(p,q,r){return Math.min(p.x,q.x)<=r.x&&r.x<=Math.max(p.x,q.x)&&Math.min(p.y,q.y)<=r.y&&r.y<=Math.max(p.y,q.y);}
function intersects(){
  const [p1,p2,p3,p4]=pts.map(px);
  const d1=ccw(p3,p4,p1),d2=ccw(p3,p4,p2),d3=ccw(p1,p2,p3),d4=ccw(p1,p2,p4);
  if(d1*d2<0&&d3*d4<0)return true;
  if(d1===0&&onSeg(p3,p4,p1))return true;if(d2===0&&onSeg(p3,p4,p2))return true;
  if(d3===0&&onSeg(p1,p2,p3))return true;if(d4===0&&onSeg(p1,p2,p4))return true;
  return false;
}
function draw(){
  ctx.clearRect(0,0,W,H);
  const [p1,p2,p3,p4]=pts.map(px);
  const d1=ccw(p3,p4,p1),d2=ccw(p3,p4,p2),d3=ccw(p1,p2,p3),d4=ccw(p1,p2,p4);
  const hit=intersects();
  if(hit){const dx=p2.x-p1.x,dy=p2.y-p1.y,ex=p4.x-p3.x,ey=p4.y-p3.y,d=dx*ey-dy*ex;if(d!==0){const t=((p3.x-p1.x)*ey-(p3.y-p1.y)*ex)/d;const ix=p1.x+t*dx,iy=p1.y+t*dy;ctx.beginPath();ctx.arc(ix,iy,7,0,Math.PI*2);ctx.fillStyle='#ffd740';ctx.fill();}}
  ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#ef5350';ctx.lineWidth=2.5;ctx.stroke();
  ctx.beginPath();ctx.moveTo(p3.x,p3.y);ctx.lineTo(p4.x,p4.y);ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;ctx.stroke();
  pts.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q.x,q.y,9,0,Math.PI*2);ctx.fillStyle=p.c;ctx.fill();ctx.strokeStyle='#1a1d27';ctx.lineWidth=2.5;ctx.stroke();ctx.fillStyle='#fff';ctx.font='bold 12px sans-serif';ctx.textAlign='center';ctx.fillText(p.label,q.x,q.y-14);});
  document.getElementById('seg-vals').textContent=`d1·d2 ${d1*d2>0?'> 0':d1*d2<0?'< 0':'= 0'}   d3·d4 ${d3*d4>0?'> 0':d3*d4<0?'< 0':'= 0'}`;
  const res=document.getElementById('seg-result');
  if(hit){res.innerHTML='<span style="font-size:22px">✕</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">INTERSECT</span>';res.style.background='#1b3a1f';res.style.color='#69f0ae';}
  else{res.innerHTML='<span style="font-size:22px">∥</span><span style="font-size:11px;font-weight:700;letter-spacing:.06em;margin-top:2px;">NO CROSS</span>';res.style.background='#3a1a1a';res.style.color='#ff5252';}
}
function pos(e){const r=cv.getBoundingClientRect();const t=e.touches?e.touches[0]:e;return{x:(t.clientX-r.left)/r.width,y:(t.clientY-r.top)/r.height};}
cv.addEventListener('mousedown',e=>{const p=pos(e);drag=pts.reduce((b,pt,i)=>{const q=px(pt),pp={x:p.x*W,y:p.y*H};const d=Math.hypot(q.x-pp.x,q.y-pp.y);return d<(b?b.d:22)?{i,d}:b;},null);});
cv.addEventListener('mousemove',e=>{if(!drag)return;const p=pos(e);pts[drag.i].x=Math.max(16/W,Math.min(1-16/W,p.x));pts[drag.i].y=Math.max(16/H,Math.min(1-16/H,p.y));draw();});
cv.addEventListener('mouseup',()=>drag=null);
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
    d1 = ccw(p3, p4, p1);  d2 = ccw(p3, p4, p2)
    d3 = ccw(p1, p2, p3);  d4 = ccw(p1, p2, p4)

    if d1*d2 < 0 and d3*d4 < 0: return True

    if d1 == 0 and on_segment(p3, p4, p1): return True
    if d2 == 0 and on_segment(p3, p4, p2): return True
    if d3 == 0 and on_segment(p1, p2, p3): return True
    if d4 == 0 and on_segment(p1, p2, p4): return True

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
  <button onclick="mcStep(-1)" style="padding:7px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:14px;color:#b0b8d0;transition:background .15s;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">◀</button>
  <button onclick="mcStep(1)" style="padding:7px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:14px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">▶</button>
  <button onclick="mcReset()" style="padding:7px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:14px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">↺</button>
  <span id="mc-desc" style="font-size:10px;font-weight:700;letter-spacing:.1em;color:#5c6bc0;margin-left:8px;text-transform:uppercase;"></span>
</div>
<div id="mc-explain" style="margin-top:8px;font-size:12px;color:#b0b8d0;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;min-height:36px;letter-spacing:.02em;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;"></div>
<p style="font-size:10px;color:#555;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">red = lower hull · blue = upper hull · green = done</p>
</div>
<script>
(function(){
let pts=[],steps=[],idx=0;
const cv=document.getElementById('mc-canvas');
cv.style.aspectRatio='560/240';
const ctx=cv.getContext('2d');
let W=560,H=240,dpr=1;
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(steps.length)render();}
new ResizeObserver(resize).observe(cv);
function cross(O,A,B){return (A.x-O.x)*(B.y-O.y)-(A.y-O.y)*(B.x-O.x);}
function rand(){
  pts=[];for(let i=0;i<10;i++)pts.push({x:50+Math.random()*(W-100),y:25+Math.random()*(H-50)});
  build();idx=0;render();
}
function build(){
  steps=[];
  const s=[...pts].sort((a,b)=>a.x===b.x?a.y-b.y:a.x-b.x);
  steps.push({lo:[],up:[],s,desc:'① x좌표 정렬',ex:'모든 점을 x좌표 순으로 정렬합니다.'});
  let lo=[];
  for(let i=0;i<s.length;i++){
    while(lo.length>=2&&cross(lo[lo.length-2],lo[lo.length-1],s[i])<=0){lo.pop();steps.push({lo:[...lo],up:[],s,cur:s[i],desc:'② 아래껍질 - CW 제거',ex:'CCW ≤ 0 → 이전 점 제거'});}
    lo.push(s[i]);steps.push({lo:[...lo],up:[],s,cur:s[i],desc:'② 아래 껍질',ex:`(${Math.round(s[i].x)}, ${Math.round(s[i].y)}) 추가`});
  }
  let up=[];
  for(let i=s.length-1;i>=0;i--){
    while(up.length>=2&&cross(up[up.length-2],up[up.length-1],s[i])<=0){up.pop();steps.push({lo:[...lo],up:[...up],s,cur:s[i],desc:'③ 위껍질 - CW 제거',ex:'CCW ≤ 0 → 이전 점 제거'});}
    up.push(s[i]);steps.push({lo:[...lo],up:[...up],s,cur:s[i],desc:'③ 위 껍질',ex:`(${Math.round(s[i].x)}, ${Math.round(s[i].y)}) 추가`});
  }
  const hull=[...lo.slice(0,-1),...up.slice(0,-1)];
  steps.push({lo:[...lo],up:[...up],hull,s,desc:'✓ 완성!',ex:'아래 + 위 합치면 볼록 껍질 완성!'});
}
function render(){
  ctx.clearRect(0,0,W,H);
  const st=steps[idx];
  if(st.hull){ctx.beginPath();st.hull.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.closePath();ctx.fillStyle='rgba(105,240,174,0.1)';ctx.fill();ctx.strokeStyle='#69f0ae';ctx.lineWidth=2.5;ctx.stroke();}
  if(st.lo&&st.lo.length>1){ctx.beginPath();st.lo.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.strokeStyle='#ef5350';ctx.lineWidth=2.5;ctx.stroke();}
  if(st.up&&st.up.length>1){ctx.beginPath();st.up.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;ctx.stroke();}
  st.s.forEach((p,i)=>{
    const inLo=st.lo&&st.lo.some(q=>q===p),inUp=st.up&&st.up.some(q=>q===p);
    const col=st.hull?'#69f0ae':inLo?'#ef5350':inUp?'#42a5f5':'#555';
    ctx.beginPath();ctx.arc(p.x,p.y,6,0,Math.PI*2);ctx.fillStyle=col;ctx.fill();
    ctx.fillStyle=st.hull||inLo||inUp?'#e0e0e0':'#666';ctx.font='bold 10px sans-serif';ctx.textAlign='center';ctx.fillText(i+1,p.x,p.y-11);
  });
  if(st.cur){ctx.beginPath();ctx.arc(st.cur.x,st.cur.y,11,0,Math.PI*2);ctx.strokeStyle='#ffd740';ctx.lineWidth=2.5;ctx.stroke();}
  document.getElementById('mc-desc').textContent=`${idx+1} / ${steps.length}  —  ${st.desc}`;
  document.getElementById('mc-explain').textContent=st.ex;
}
window.mcStep=d=>{idx=Math.max(0,Math.min(steps.length-1,idx+d));render();};
window.mcReset=rand;
rand();
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