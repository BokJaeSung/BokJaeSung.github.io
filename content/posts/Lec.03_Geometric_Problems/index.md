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
<div style="margin:1.5rem 0;">
<canvas id="ccw-canvas" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;cursor:crosshair;"></canvas>
<div style="display:flex;gap:10px;margin-top:8px;">
  <div style="flex:1;background:#f5f5f5;border-radius:6px;padding:8px 12px;font-size:13px;">
    <div style="color:#888;font-size:11px;margin-bottom:2px;">공식 계산</div>
    <div id="ccw-formula" style="font-family:monospace;">-</div>
  </div>
  <div id="ccw-result" style="min-width:130px;padding:8px 14px;border-radius:6px;text-align:center;font-weight:500;font-size:14px;background:#e8f5e9;color:#2e7d32;">-</div>
</div>
<p style="font-size:12px;color:#888;margin-top:6px;">점을 드래그해서 방향이 바뀌는 걸 확인해보자</p>
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
  ctx.fillStyle=val===0?'rgba(150,150,150,0.1)':val>0?'rgba(67,160,71,0.12)':'rgba(229,57,53,0.12)';ctx.fill();
  const arr=(x1,y1,x2,y2,col)=>{
    const dx=x2-x1,dy=y2-y1,len=Math.sqrt(dx*dx+dy*dy);if(len<1)return;
    const ux=dx/len,uy=dy/len,r=12;
    ctx.beginPath();ctx.moveTo(x1+ux*r,y1+uy*r);ctx.lineTo(x2-ux*r,y2-uy*r);
    ctx.strokeStyle=col;ctx.lineWidth=2;ctx.stroke();
    const a=Math.atan2(dy,dx);
    ctx.beginPath();ctx.moveTo(x2-ux*r,y2-uy*r);ctx.lineTo(x2-ux*r-Math.cos(a-.4)*9,y2-uy*r-Math.sin(a-.4)*9);ctx.moveTo(x2-ux*r,y2-uy*r);ctx.lineTo(x2-ux*r-Math.cos(a+.4)*9,y2-uy*r-Math.sin(a+.4)*9);ctx.strokeStyle=col;ctx.lineWidth=2;ctx.stroke();
  };
  arr(A.x,A.y,B.x,B.y,'#e53935');arr(B.x,B.y,C.x,C.y,'#43a047');arr(C.x,C.y,A.x,A.y,'#1e88e5');
  pts.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q.x,q.y,9,0,Math.PI*2);ctx.fillStyle=p.color;ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#333';ctx.font='500 13px sans-serif';ctx.textAlign='center';ctx.fillText(p.label,q.x,q.y-16);});
  const ax=Math.round(A.x),ay=Math.round(A.y),bx=Math.round(B.x-A.x),by=Math.round(B.y-A.y),cx=Math.round(C.x-A.x),cy=Math.round(C.y-A.y),rv=Math.round(val);
  document.getElementById('ccw-formula').textContent=`(${bx})(${cy}) − (${by})(${cx}) = ${rv}`;
  const res=document.getElementById('ccw-result');
  if(val===0){res.textContent='= 0  일직선';res.style.background='#f5f5f5';res.style.color='#888';}
  else if(val>0){res.textContent='> 0  반시계 ↺';res.style.background='#e8f5e9';res.style.color='#2e7d32';}
  else{res.textContent='< 0  시계방향 ↻';res.style.background='#ffebee';res.style.color='#c62828';}
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
<div style="margin:1.5rem 0;">
<canvas id="seg-canvas" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;cursor:crosshair;"></canvas>
<div style="display:flex;gap:10px;margin-top:8px;">
  <div style="flex:1;background:#f5f5f5;border-radius:6px;padding:8px 12px;font-size:12px;font-family:monospace;" id="seg-vals">-</div>
  <div id="seg-result" style="min-width:100px;padding:8px 14px;border-radius:6px;text-align:center;font-weight:500;font-size:14px;">-</div>
</div>
<p style="font-size:12px;color:#888;margin-top:6px;">빨강=선분1(p1p2), 파랑=선분2(p3p4). 점을 드래그해서 확인.</p>
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
  ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='#e53935';ctx.lineWidth=2.5;ctx.stroke();
  ctx.beginPath();ctx.moveTo(p3.x,p3.y);ctx.lineTo(p4.x,p4.y);ctx.strokeStyle='#1e88e5';ctx.lineWidth=2.5;ctx.stroke();
  pts.forEach(p=>{const q=px(p);ctx.beginPath();ctx.arc(q.x,q.y,8,0,Math.PI*2);ctx.fillStyle=p.c;ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();ctx.fillStyle='#333';ctx.font='12px sans-serif';ctx.textAlign='center';ctx.fillText(p.label,q.x,q.y-13);});
  document.getElementById('seg-vals').textContent=`d1·d2=${d1*d2>0?'>0':d1*d2<0?'<0':'=0'}  d3·d4=${d3*d4>0?'>0':d3*d4<0?'<0':'=0'}`;
  const res=document.getElementById('seg-result');
  res.textContent=hit?'교차 O':'교차 X';res.style.background=hit?'#e8f5e9':'#ffebee';res.style.color=hit?'#2e7d32':'#c62828';
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
<div style="margin:1.5rem 0;">
<canvas id="mc-canvas" style="width:100%;border:1px solid #e0e0e0;border-radius:8px;"></canvas>
<div style="display:flex;gap:8px;margin-top:8px;align-items:center;">
  <button onclick="mcStep(-1)" style="padding:5px 12px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer;">◀</button>
  <button onclick="mcStep(1)" style="padding:5px 12px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer;">▶</button>
  <button onclick="mcReset()" style="padding:5px 12px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer;">🔀</button>
  <span id="mc-desc" style="font-size:12px;color:#888;margin-left:4px;"></span>
</div>
<div id="mc-explain" style="margin-top:6px;font-size:12px;color:#555;background:#f9f9f9;border-radius:6px;padding:8px 12px;min-height:28px;"></div>
<p style="font-size:12px;color:#888;margin-top:4px;">빨강=아래껍질, 파랑=위껍질, 초록=완성</p>
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
  if(st.hull){ctx.beginPath();st.hull.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.closePath();ctx.fillStyle='rgba(67,160,71,0.12)';ctx.fill();ctx.strokeStyle='#43a047';ctx.lineWidth=2;ctx.stroke();}
  if(st.lo&&st.lo.length>1){ctx.beginPath();st.lo.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.strokeStyle='#e53935';ctx.lineWidth=2;ctx.stroke();}
  if(st.up&&st.up.length>1){ctx.beginPath();st.up.forEach((p,i)=>i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y));ctx.strokeStyle='#1e88e5';ctx.lineWidth=2;ctx.stroke();}
  st.s.forEach((p,i)=>{
    const inLo=st.lo&&st.lo.some(q=>q===p),inUp=st.up&&st.up.some(q=>q===p);
    ctx.beginPath();ctx.arc(p.x,p.y,5,0,Math.PI*2);ctx.fillStyle=st.hull?'#43a047':inLo?'#e53935':inUp?'#1e88e5':'#aaa';ctx.fill();
    ctx.fillStyle='#999';ctx.font='10px sans-serif';ctx.textAlign='center';ctx.fillText(i+1,p.x,p.y-10);
  });
  if(st.cur){ctx.beginPath();ctx.arc(st.cur.x,st.cur.y,9,0,Math.PI*2);ctx.strokeStyle='#ff9800';ctx.lineWidth=2;ctx.stroke();}
  document.getElementById('mc-desc').textContent=`${idx+1}/${steps.length}  ${st.desc}`;
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