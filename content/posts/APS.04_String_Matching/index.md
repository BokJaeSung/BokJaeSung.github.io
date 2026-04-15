---
title: "APS.04 String Matching"
date: 2026-03-25T09:00:00+09:00
tags: ["알고리즘", "문자열", "KMP", "Rabin-Karp", "해시", "접두사함수"]
cover:
  image: 'images/cover.jpg'
  alt: 'APS.04 String Matching'
  relative: true
summary: "From naïve O(nm) to KMP O(n+m): prefix function, rolling hash, and binary search on longest repeated substring."
---

## 1. 문자열 패턴 매칭 문제란?

텍스트 $T = t_1 t_2 \cdots t_n$ (길이 $n$) 안에서 패턴 $P = p_1 p_2 \cdots p_m$ (길이 $m \le n$) 이 등장하는 모든 위치를 찾는 문제다.

$$T[s+1 \cdots s+m] = P[1 \cdots m] \quad (0 \le s \le n-m)$$

$s$ 는 **shift** — 패턴을 텍스트 위에 갖다 댈 시작 위치다. $s \le n-m$ 인 이유는 그 이상이면 패턴이 텍스트 밖으로 삐져나오기 때문이다.

---

## 2. Naive way

가장 단순한 접근: 모든 $s$ 에 대해 패턴을 처음부터 비교한다.

```python
def string_matching_naive(T: str, P: str):
    n = len(T)
    m = len(P)
    shifts = []
    for s in range(n - m + 1):
        for j in range(m):
            if T[s + j] != P[j]:
                break
        else:
            shifts.append(s)
    return shifts
```

**시간복잡도:** $O\big((n-m+1) \cdot m\big) = O(nm)$

최악의 경우 — `T = "aaa...a"`, `P = "aa...ab"` 처럼 매번 마지막 글자에서만 불일치가 나면 항상 $m$ 번을 다 써야 한다.

| n | m | 최대 비교 횟수 |
|---|---|---|
| 100 | 10 | 1,000 |
| 1,000 | 100 | 100,000 |
| 20,000 | 10,000 | 200,000,000 (약 6초) |

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="naive-T" value="abcababcab" maxlength="16" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:180px;" placeholder="Text T">
  <input id="naive-P" value="abc" maxlength="8" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:120px;" placeholder="Pattern P">
  <button onclick="naiveRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="naiveStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 한 칸</button>
  <button onclick="naiveAuto()" id="naive-auto-btn" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">⏩ 자동</button>
</div>
<canvas id="naive-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:10px;margin-top:10px;align-items:stretch;">
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;">
    <div id="naive-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.6;">시작 버튼을 누르세요.</div>
  </div>
  <div style="min-width:140px;background:#1a1d27;border-left:3px solid #37474f;border-radius:6px;padding:10px 14px;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;">
    <div style="font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5c6bc0;margin-bottom:6px;">Stats</div>
    <div>비교: <span id="naive-cmp" style="color:#ffd740;">0</span></div>
    <div>발견: <span id="naive-found" style="color:#69f0ae;">-</span></div>
  </div>
</div>
<p style="font-size:13px;color:#778;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">green = match · red = mismatch · amber = current window</p>
</div>
<script>
(function(){
const cv=document.getElementById('naive-canvas');
const ctx=cv.getContext('2d');
let W=560,H=180,dpr=1;
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(ns)drawNaive();}
new ResizeObserver(resize).observe(cv);
cv.style.aspectRatio='560/180';

let ns=null,naiveTimer=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";

function drawBox(x,y,w,h,bg,border,text,textCol,fontSize){
  ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(x,y,w,h,4);ctx.fill();
  ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,y,w,h,4);ctx.stroke();
  if(text){ctx.fillStyle=textCol;ctx.font=`bold ${fontSize}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,x+w/2,y+h/2);}
}

function drawNaive(){
  if(!ns)return;
  ctx.clearRect(0,0,W,H);
  const {T,P,s,j,found,done}=ns;
  const n=T.length,m=P.length;
  const bw=Math.min(Math.floor((W-40)/Math.max(n,m+1)),54);
  const bh=Math.max(42,Math.min(bw,Math.round(H*0.24)));
  const gap=3;
  const rowGap=Math.round(H*0.12);
  const labelH=16;
  const totalH=labelH+bh+rowGap+bh;
  const ty=Math.round((H-totalH)/2)+labelH;
  const py=ty+bh+rowGap;
  const fs=Math.round(bh*0.45);
  const startX=(W-n*(bw+gap))/2;
  const patStart=startX+s*(bw+gap);
  const patW=m*(bw+gap)-gap;

  // index labels (T행 위)
  ctx.fillStyle='#8090a0';ctx.font=`13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  for(let i=0;i<n;i++) ctx.fillText(i,startX+i*(bw+gap)+bw/2,ty-10);

  // T text boxes
  for(let i=0;i<n;i++){
    let bg='#1e2130',border='#2a2d3a',textCol='#b0b8d0';
    if(found.some(f=>i>=f&&i<f+m)){bg='#1b3a1f';border='#69f0ae';textCol='#69f0ae';}
    else if(!done&&i>=s&&i<s+m){
      const pj=i-s;
      if(pj<j){bg='#1b3a1f';border='#43a047';textCol='#69f0ae';}
      else if(pj===j){bg='#1a237e';border='#5c6bc0';textCol='#9fa8da';}
      else{bg='#1e2130';border='#37474f';textCol='#546e7a';}
    }
    drawBox(startX+i*(bw+gap),ty,bw,bh,bg,border,T[i],textCol,fs);
  }

  // P pattern boxes — centered under the matching T window
  for(let i=0;i<m;i++){
    let bg='#1a1a2e',border='#3949ab',textCol='#7986cb';
    if(!done){
      if(i<j){bg='#1b3a1f';border='#43a047';textCol='#69f0ae';}
      else if(i===j){bg='#3a1a1a';border='#e53935';textCol='#ef9a9a';}
    }
    drawBox(patStart+i*(bw+gap),py,bw,bh,bg,border,P[i],textCol,fs);
  }
  // s= label below P row, centered
  ctx.fillStyle='#8090a0';ctx.font=`13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='top';
  ctx.fillText(`s=${s}`,patStart+patW/2,py+bh+4);
  if(done&&found.length===0){
    ctx.fillStyle='#ef9a9a';ctx.font=`14px sans-serif`;ctx.textAlign='center';ctx.textBaseline='top';
    ctx.fillText('패턴 없음',W/2,py+bh+4);
  }
}

window.naiveRestart=function(){
  if(naiveTimer){clearInterval(naiveTimer);naiveTimer=null;document.getElementById('naive-auto-btn').textContent='⏩ 자동';}
  const T=document.getElementById('naive-T').value||'abcababcab';
  const P=document.getElementById('naive-P').value||'abc';
  if(P.length>T.length)return;
  ns={T,P,s:0,j:0,cmp:0,found:[],done:false};
  document.getElementById('naive-cmp').textContent='0';
  document.getElementById('naive-found').textContent='-';
  document.getElementById('naive-info').innerHTML=`<span style="color:#90caf9">s=0</span>, <span style="color:#90caf9">j=0</span> 에서 비교 시작`;
  drawNaive();
};
const nI=id=>document.getElementById(id);
const nC=(v,c)=>`<span style="color:${c}">${v}</span>`;
const nIdx=v=>nC(v,'#90caf9');
const nChr=v=>nC(`'${v}'`,'#ffd740');
const nRes=v=>nC(v,'#ce93d8');
const nOk=v=>nC(v,'#69f0ae');
const nNg=v=>nC(v,'#ef5350');

window.naiveStep=function(){
  if(!ns||ns.done)return;
  const {T,P}=ns;const n=T.length,m=P.length;
  if(ns.s>n-m){ns.done=true;nI('naive-info').innerHTML=`완료! 총 <span style="color:#ffd740">${ns.cmp}</span>번 비교`;drawNaive();return;}
  ns.cmp++;
  nI('naive-cmp').textContent=ns.cmp;
  if(T[ns.s+ns.j]===P[ns.j]){
    nI('naive-info').innerHTML=`${nIdx('s='+ns.s)}, ${nIdx('j='+ns.j)}: T[${ns.s+ns.j}]=${nChr(T[ns.s+ns.j])} <b style="color:#69f0ae">=</b> P[${ns.j}]=${nChr(P[ns.j])} ${nOk('✓')}`;
    ns.j++;
    if(ns.j===m){ns.found.push(ns.s);nI('naive-found').textContent=ns.found.join(', ');nI('naive-info').innerHTML=`${nOk('✓ 패턴 발견!')} ${nIdx('s='+ns.s)}`;ns.s++;ns.j=0;}
  } else {
    nI('naive-info').innerHTML=`${nIdx('s='+ns.s)}, ${nIdx('j='+ns.j)}: T[${ns.s+ns.j}]=${nChr(T[ns.s+ns.j])} <b style="color:#ef5350">≠</b> P[${ns.j}]=${nChr(P[ns.j])} → ${nRes('s+1')}`;
    ns.s++;ns.j=0;
  }
  if(ns.s>n-m){ns.done=true;nI('naive-info').innerHTML=`완료! 총 <span style="color:#ffd740">${ns.cmp}</span>번 | 발견: ${ns.found.length?nOk(ns.found.join(', ')):nNg('없음')}`;}
  drawNaive();
};

window.naiveAuto=function(){
  if(naiveTimer){clearInterval(naiveTimer);naiveTimer=null;document.getElementById('naive-auto-btn').textContent='⏩ 자동';return;}
  if(!ns)naiveRestart();
  document.getElementById('naive-auto-btn').textContent='⏸ 정지';
  naiveTimer=setInterval(()=>{if(!ns||ns.done){clearInterval(naiveTimer);naiveTimer=null;document.getElementById('naive-auto-btn').textContent='⏩ 자동';return;}naiveStep();},220);
};
naiveRestart();
})();
</script>
{{< /rawhtml >}}

---

## 3. KMP (Knuth-Morris-Pratt) 알고리즘

### 핵심 관찰

나이브는 불일치 시 맞춰둔 $j$ 개의 정보를 전부 버리고 $s+1$ 로 이동한다.

그런데 우리는 이미 $T[s+1 \cdots s+j] = P[1 \cdots j]$ 라는 사실을 알고 있다. **텍스트 포인터 $i$ 는 절대 뒤로 가지 않는다.** 불일치 시 패턴 포인터 $j$ 만 $\pi[j-1]$ 로 줄인다.

### Prefix Function (접두사 함수)

$\pi[i]$ = $P[0 \cdots i]$ 에서 **자기 자신을 제외한** 접두사이면서 동시에 접미사인 것 중 가장 긴 길이.

자기 자신을 제외하는 이유: 포함하면 $i = \pi[i]$ 가 되어 무한루프. 항상 $\pi[i] < i$ 가 성립해야 한다.

```python
def compute_prefix_function(P: str):
    m = len(P)
    pi = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and P[j] != P[i]:
            j = pi[j - 1]
        if P[j] == P[i]:
            j += 1
        pi[i] = j
    return pi
```

**시간복잡도:** $O(m)$

### ※ 왜 불일치 시 $j = \pi[j-1]$ 인가?

`P[i] ≠ P[j]` 일 때, $j$ 를 무작정 0으로 되돌리면 틀린다. 예시로 확인해보자.

패턴 `abcaaxabcab` 에서 $i=10$, $j=3$ 까지 채워진 상황:

$$\pi = [0,\ 0,\ 0,\ 1,\ 1,\ 0,\ 1,\ 2,\ 3,\ 4,\ ?]$$

$P[i] = \texttt{b}$, $P[j] = \texttt{a}$ 로 불일치. LPS 길이 5는 불가.

**왜 $j=0$ 으로 가면 안 되나?**

$i-1$ 번째까지의 부분 문자열 `abcaaxabca` 의 LPS 길이는 $\pi[i-1] = 4$ — 접두사 `abca` 와 접미사 `abca` 가 같다. 이 4글자짜리 접두사/접미사 자체는 LPS 길이가 1이다 (`a`). 즉:

$$\text{`abcaaxabca'의 접두사 == 접미사 길이} = 4, \quad \text{그 다음으로 긴 길이} = 1$$

$j=0$ 으로 가버리면 이미 알고 있는 "길이 1짜리 일치" 정보를 버리게 된다.

**올바른 이동: $j = \pi[j-1]$**

$j-1$ 번째까지 접두사 안에서의 "접두사 = 접미사" 길이가 $\pi[j-1]$ 에 저장되어 있다. 이 위치로 $j$ 를 옮기면 이미 매칭된 부분을 재활용할 수 있다.

$$j = \pi[j-1] = \pi[2] = 0 \xrightarrow{\text{다시 비교}} P[i]=P[j] \implies \pi[i] = j+1 = 1$$

$j$ 를 한 번에 0으로 보내는 게 아니라, **`while` 루프로 $\pi$ 를 타고 내려가며** 일치하는 지점을 찾거나 $j=0$ 에 도달한다. 이 과정이 분할상환 $O(m)$ 을 보장한다.

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="pi-P" value="abcaaxabcabc" maxlength="14" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:180px;" placeholder="Pattern P">
  <button onclick="piRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="piBack()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">◀ 이전</button>
  <button onclick="piStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 다음</button>
</div>
<canvas id="pi-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;margin-top:10px;">
  <div id="pi-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.6;">패턴을 입력하고 시작 버튼을 누르세요.</div>
</div>
<p style="font-size:13px;color:#778;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">amber = current q · purple = computed π value</p>
</div>
<script>
(function(){
const cv=document.getElementById('pi-canvas');
const ctx=cv.getContext('2d');
let W=560,H=210,dpr=1;
cv.style.aspectRatio='560/210';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(ps)drawPi();}
new ResizeObserver(resize).observe(cv);

let ps=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";

function buildPiSteps(P){
  const m=P.length,pi=new Array(m).fill(0);
  const steps=[{i:-1,j:0,jb:0,jc:0,pi:[...pi],msg:'초기화: π 배열을 0으로 세팅'}];
  let j=0;
  for(let i=1;i<m;i++){
    // fallback steps: each iteration of the while loop becomes its own step
    while(j>0&&P[i]!==P[j]){
      const jprev=j;
      j=pi[j-1];
      steps.push({i,j,jb:jprev,jc:j,fallback:true,pi:[...pi],msg:`<span style="color:#90caf9">i=${i}</span>, <span style="color:#ef5350">j=${jprev}</span><br>P[${jprev}]='<span style="color:#ffd740">${P[jprev]}</span>' <span style="color:#ef5350;font-weight:700">≠</span> P[${i}]='<span style="color:#ffd740">${P[i]}</span>' → 불일치<br>fallback: j = π[j-1] = π[${jprev-1}] = <span style="color:#ce93d8">${j}</span>`});
    }
    const jc=j;
    if(P[i]===P[j])j++;
    pi[i]=j;
    const match=P[jc]===P[i];
    const cmp=match?`<span style="color:#69f0ae;font-weight:700">=</span>`:`<span style="color:#ef5350;font-weight:700">≠</span>`;
    const line3=match
      ?`j: <span style="color:#ce93d8">${jc}</span>→<span style="color:#ce93d8">${j}</span> → <span style="color:#69f0ae">π[${i}] = ${j}</span>`
      :`j: <span style="color:#ce93d8">${jc}</span> 유지 → <span style="color:#69f0ae">π[${i}] = 0</span>`;
    steps.push({i,j,jb:jc,jc,pi:[...pi],msg:`<span style="color:#90caf9">i=${i}</span>, <span style="color:#ef5350">j=${jc}</span><br>P[${jc}]='<span style="color:#ffd740">${P[jc]??'-'}</span>' ${cmp} P[${i}]='<span style="color:#ffd740">${P[i]}</span>'<br>${line3}`});
  }
  return steps;
}

function drawPi(){
  if(!ps)return;
  ctx.clearRect(0,0,W,H);
  const {P,steps,idx}=ps;
  const m=P.length;
  const labelW=46;
  const bw=Math.min(Math.floor((W-labelW-16)/m),58);
  const bh=Math.max(44,Math.round(H*0.2));
  const gap=3;
  const rowGap=Math.round(H*0.1);
  const totalH=bh*2+rowGap;
  const ty=Math.round((H-totalH)/2);
  const py=ty+bh+rowGap;
  const startX=labelW+Math.round(((W-labelW)-(m*(bw+gap)-gap))/2);
  const fs=Math.round(bh*0.44);
  const st=steps[idx];

  // row labels
  ctx.textBaseline='middle';ctx.textAlign='right';
  ctx.font=`italic bold 15px sans-serif`;ctx.fillStyle='#5c8de8';
  ctx.fillText('pattern',startX-8,ty+bh/2);
  ctx.font=`italic bold 15px sans-serif`;ctx.fillStyle='#ef5350';
  ctx.fillText('π',startX-8,py+bh/2);

  // blue bracket: matched prefix [0..j-1] on pattern row
  const j=st.j,ci=st.i,jb=st.jb??0,jc=st.jc??0,isFallback=!!st.fallback;

  // fallback curved arrow: jb → jc (right to left, arc above boxes)
  if(isFallback&&jb!==jc){
    const x1=startX+jb*(bw+gap)+bw/2; // departure center
    const x2=startX+jc*(bw+gap)+bw/2; // arrival center
    const ay=ty-2; // arrow base y (top of pointer area)
    const cpY=ay-Math.max(18, Math.round((jb-jc)*(bw+gap)*0.45)); // control point height
    ctx.save();
    ctx.strokeStyle='#ef5350';ctx.lineWidth=2;ctx.setLineDash([4,3]);
    ctx.beginPath();ctx.moveTo(x1,ay);ctx.quadraticCurveTo((x1+x2)/2,cpY,x2,ay);ctx.stroke();
    ctx.setLineDash([]);
    // arrowhead at x2: tangent = (cp→end) direction
    const cpX=(x1+x2)/2;
    const tdx=x2-cpX,tdy=ay-cpY;
    const tlen=Math.sqrt(tdx*tdx+tdy*tdy);
    const tnx=tdx/tlen,tny=tdy/tlen;
    const hs=7;
    ctx.fillStyle='#ef5350';ctx.beginPath();
    ctx.moveTo(x2,ay);
    ctx.lineTo(x2-hs*(tnx-tny*0.5),ay-hs*(tny+tnx*0.5));
    ctx.lineTo(x2-hs*(tnx+tny*0.5),ay-hs*(tny-tnx*0.5));
    ctx.closePath();ctx.fill();
    ctx.restore();
  }
  // draw prefix highlight bracket (j chars from left)
  if(j>0&&ci>=0){
    const bx=startX,by=ty,bW=j*(bw+gap)-gap,bH=bh;
    ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;
    ctx.strokeRect(bx-1,by-1,bW+2,bH+2);
  }
  // draw suffix highlight bracket (j chars ending at i)
  if(j>0&&ci>=0&&ci-j+1>=0){
    const bx=startX+(ci-j+1)*(bw+gap),by=ty,bW=j*(bw+gap)-gap,bH=bh;
    ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;
    ctx.strokeRect(bx-1,by-1,bW+2,bH+2);
  }

  for(let ii=0;ii<m;ii++){
    const x=startX+ii*(bw+gap);
    // pattern row
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(x,ty,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,ty,bw,bh,4);ctx.stroke();
    // character
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font=`bold ${fs}px ${MONO}`;ctx.fillStyle=tc;
    ctx.fillText(P[ii],x+bw/2,ty+bh/2);
    // j pointer
    if(ci>=0){
      const pfs=Math.round(fs*0.8);
      ctx.font=`italic bold ${pfs}px sans-serif`;
      ctx.textAlign='center';ctx.textBaseline='bottom';
      if(isFallback){
        if(ii===jb){ctx.fillStyle='#ef535055';ctx.fillText('j',x+bw/2,ty-2);}
        if(ii===jc){ctx.fillStyle='#ef5350';ctx.fillText('j',x+bw/2,ty-2);}
      } else {
        if(ii===jc){ctx.fillStyle='#ef5350';ctx.fillText('j',x+bw/2,ty-2);}
      }
    }
    // i pointer (current index)
    if(ii===ci&&ci>=0){
      ctx.font=`italic bold ${Math.round(fs*0.8)}px sans-serif`;
      ctx.fillStyle='#42a5f5';ctx.textAlign='center';ctx.textBaseline='bottom';
      ctx.fillText('i',x+bw/2,ty-2);
    }

    // π row
    const piVal=ii<=ci&&ci>=0?st.pi[ii]:null;
    bg='#1e2130';border='#2a2d3a';tc='#8090a0';
    if(piVal!==null&&piVal>0){bg='#1a0a2e';border='#7c4dff';tc='#b39ddb';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(x,py,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,py,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(piVal!==null?piVal:'',x+bw/2,py+bh/2);
  }
}

window.piRestart=function(){
  const P=document.getElementById('pi-P').value||'abcaaxabcabc';
  ps={P,steps:buildPiSteps(P),idx:0};
  document.getElementById('pi-info').innerHTML=ps.steps[0].msg;
  drawPi();
};
window.piBack=function(){
  if(!ps||ps.idx<=0)return;
  ps.idx--;
  document.getElementById('pi-info').innerHTML=ps.steps[ps.idx].msg;
  drawPi();
};
window.piStep=function(){
  if(!ps||ps.idx>=ps.steps.length-1)return;
  ps.idx++;
  document.getElementById('pi-info').innerHTML=ps.steps[ps.idx].msg;
  drawPi();
};
piRestart();
})();
</script>
{{< /rawhtml >}}

### KMP 매칭

```python
def string_matching_kmp(T: str, P: str):
    n, m = len(T), len(P)
    pi = compute_prefix_function(P)
    shifts = []
    q = 0
    for i in range(n):
        while q > 0 and P[q] != T[i]:
            q = pi[q - 1]      # 폴백 — i는 고정, q만 줄임
        if P[q] == T[i]:
            q += 1
        if q == m:
            shifts.append(i - m + 1)
            q = pi[q - 1]
    return shifts
```

**시간복잡도:** $O(n+m)$

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="kmp-T" value="ababdababcabbababcabababcababa" maxlength="32" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:240px;" placeholder="Word W">
  <input id="kmp-P" value="ababcaba" maxlength="12" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:140px;" placeholder="Pattern P">
  <button onclick="kmpRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="kmpBack()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">◀ 이전</button>
  <button onclick="kmpStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 다음</button>
</div>
<canvas id="kmp-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;margin-top:10px;">
  <div id="kmp-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.8;">시작 버튼을 누르세요.</div>
</div>
</div>
<script>
(function(){
const cv=document.getElementById('kmp-canvas');
const ctx=cv.getContext('2d');
let W=760,H=260,dpr=1;
cv.style.aspectRatio='760/260';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(ks)drawKmp();}
new ResizeObserver(resize).observe(cv);

let ks=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";

function computePi(P){const m=P.length,pi=new Array(m).fill(0);let j=0;for(let i=1;i<m;i++){while(j>0&&P[i]!==P[j])j=pi[j-1];if(P[i]===P[j])j++;pi[i]=j;}return pi;}

function buildKmpSteps(T,P,pi){
  const n=T.length,m=P.length;
  const C=(v,c)=>`<span style="color:${c}">${v}</span>`;
  const cW=v=>C(v,'#69f0ae');   // w_idx - green
  const cP=v=>C(v,'#ef5350');   // p_idx - red
  const cChr=v=>C(`'${v}'`,'#ffd740');
  const cRes=v=>C(v,'#ce93d8');
  const steps=[];
  let w=0,p=0,found=[];
  while(w<n){
    if(T[w]===P[p]){
      // push BEFORE incrementing: show current comparison position
      steps.push({w,p,found:[...found],match:true,
        msg:`${cW('w_idx='+w)}, ${cP('p_idx='+p)}<br>${cChr(T[w])} = ${cChr(P[p])} → 일치<br>w_idx: ${cW(w)}→${cW(w+1)}, p_idx: ${cP(p)}→${cP(p+1)}`});
      w++;p++;
      if(p===m){
        const pos=w-m;found=[...found,pos];
        steps.push({w,p:m,found:[...found],match:true,
          msg:`${cW('w_idx='+w)}, ${cP('p_idx='+(m))}<br>패턴 발견! 위치 ${cRes(pos)}<br>p_idx = π[${m-1}] = ${cRes(pi[m-1])} (fallback)`});
        p=pi[m-1];
      }
    } else {
      if(p>0){
        const pb=p;
        // push before fallback: show mismatch position
        steps.push({w,p:pb,found:[...found],fallback:true,
          msg:`${cW('w_idx='+w)}, ${cP('p_idx='+pb)}<br>${cChr(T[w])} ≠ ${cChr(P[pb])} → 불일치<br>p_idx = π[${pb-1}] = ${cRes(pi[pb-1])} (w 고정, p fallback)`});
        p=pi[pb-1];
      } else {
        steps.push({w,p:0,found:[...found],
          msg:`${cW('w_idx='+w)}, ${cP('p_idx=0')}<br>${cChr(T[w])} ≠ ${cChr(P[0])} → 불일치<br>p_idx=0 유지, w_idx: ${cW(w)}→${cW(w+1)}`});
        w++;
      }
    }
  }
  steps.push({w,p,found:[...found],done:true,msg:`완료! 발견 위치: ${found.length?found.map(f=>cRes(f)).join(', '):C('없음','#ef5350')}`});
  return steps;
}

function drawKmp(){
  if(!ks)return;
  ctx.clearRect(0,0,W,H);
  const {T,P,pi,steps,idx}=ks;
  const st=steps[idx];
  const n=T.length,m=P.length;
  const labelW=48;
  const gap=3;
  const bw=Math.min(Math.floor((W-labelW-8-(n-1)*gap)/n),48);
  const bh=Math.max(38,Math.round(H*0.17));
  const rowGap=Math.round(H*0.08);
  const totalH=bh*3+rowGap*2;
  const wy=Math.round((H-totalH)/2);
  const patY=wy+bh+rowGap;
  const piY=patY+bh+rowGap;
  const startX=labelW+Math.round(((W-labelW)-(n*(bw+gap)-gap))/2);
  const fs=Math.round(bh*0.44);
  const {w,p,found}=st;
  const s=w-p; // pattern start in T

  // row labels
  ctx.textBaseline='middle';ctx.textAlign='right';
  ctx.font=`italic bold 14px sans-serif`;
  ctx.fillStyle='#69f0ae';ctx.fillText('word',startX-8,wy+bh/2);
  ctx.fillStyle='#ef5350';ctx.fillText('Pattern',startX-8,patY+bh/2);
  ctx.fillStyle='#ce93d8';ctx.fillText('pi',startX-8,piY+bh/2);

  // w pointer: triangle marker on bottom edge of word box + label inside box bottom
  if(w<n&&!st.done){
    const wx=startX+w*(bw+gap)+bw/2,wby=wy+bh;
    ctx.fillStyle='#69f0ae';
    ctx.beginPath();ctx.moveTo(wx-5,wby+2);ctx.lineTo(wx+5,wby+2);ctx.lineTo(wx,wby+8);ctx.closePath();ctx.fill();
    ctx.font=`bold ${Math.round(fs*0.65)}px sans-serif`;ctx.textAlign='center';ctx.textBaseline='bottom';
    ctx.fillText('w',wx,wby-2);
  }

  // word row (T)
  for(let k=0;k<n;k++){
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    if(found.some(f=>k>=f&&k<f+m)){bg='#1b3a1f';border='#69f0ae';tc='#69f0ae';}
    else if(k===w&&!st.done){bg='#1a237e';border='#5c6bc0';tc='#9fa8da';}
    else if(k>=s&&k<w&&!st.done){bg='#0d2818';border='#2e7d32';tc='#66bb6a';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),wy,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),wy,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(T[k],startX+k*(bw+gap)+bw/2,wy+bh/2);
    // index label
    ctx.fillStyle='#8090a0';ctx.font=`${Math.round(bh*0.28)}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(k,startX+k*(bw+gap)+bw/2,wy-10);
  }

  // p pointer: triangle marker on bottom edge of pattern box + label inside box bottom
  if(!st.done){
    const ppx=startX+s*(bw+gap)+p*(bw+gap)+bw/2,pby=patY+bh;
    ctx.fillStyle='#ef5350';
    ctx.beginPath();ctx.moveTo(ppx-5,pby+2);ctx.lineTo(ppx+5,pby+2);ctx.lineTo(ppx,pby+8);ctx.closePath();ctx.fill();
    ctx.font=`bold ${Math.round(fs*0.65)}px sans-serif`;ctx.textAlign='center';ctx.textBaseline='bottom';
    ctx.fillText('p',ppx,pby-2);
  }

  // pattern row (P) — aligned under T[s..s+m-1]
  const patStartX=startX+s*(bw+gap);
  for(let k=0;k<m;k++){
    const px2=patStartX+k*(bw+gap);
    if(px2+bw>W)break;
    let bg='#1e2130',border='#3949ab',tc='#7986cb';
    if(k<p){bg='#1a0a2e';border='#7c4dff';tc='#b39ddb';}
    if(k===p&&!st.done){bg='#1a237e';border='#5c6bc0';tc='#9fa8da';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(px2,patY,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(px2,patY,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(P[k],px2+bw/2,patY+bh/2);
    // p index label
    ctx.fillStyle='#8090a0';ctx.font=`${Math.round(bh*0.28)}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(k,px2+bw/2,patY-10);
  }

  // pi row — always aligned from index 0 (same width as pattern)
  const piStartX=startX;
  for(let k=0;k<m;k++){
    const px2=piStartX+k*(bw+gap);
    let bg='#1e2130',border='#2a2d3a',tc='#8090a0';
    if(pi[k]>0){bg='#1a0a2e';border='#7c4dff';tc='#b39ddb';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(px2,piY,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(px2,piY,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(pi[k],px2+bw/2,piY+bh/2);
  }
}

window.kmpRestart=function(){
  const T=document.getElementById('kmp-T').value||'ababdababcabbababcabababcababa';
  const P=document.getElementById('kmp-P').value||'ababcaba';
  if(P.length>T.length)return;
  const pi=computePi(P);
  const steps=buildKmpSteps(T,P,pi);
  ks={T,P,pi,steps,idx:0};
  document.getElementById('kmp-info').innerHTML=steps[0].msg;
  drawKmp();
};
window.kmpBack=function(){
  if(!ks||ks.idx<=0)return;
  ks.idx--;
  document.getElementById('kmp-info').innerHTML=ks.steps[ks.idx].msg;
  drawKmp();
};
window.kmpStep=function(){
  if(!ks||ks.idx>=ks.steps.length-1)return;
  ks.idx++;
  document.getElementById('kmp-info').innerHTML=ks.steps[ks.idx].msg;
  drawKmp();
};
kmpRestart();
})();
</script>
{{< /rawhtml >}}

---

## 4. Rabin-Karp 알고리즘

글자를 하나씩 비교하는 대신, 부분 문자열 전체를 숫자(해시)로 바꿔서 비교한다.

$$\text{hash}(P) = \left(p_1 d^{m-1} + p_2 d^{m-2} + \cdots + p_m d^0\right) \bmod q$$

### Rolling Hash

$$t_{s+1} = \left(d \cdot (t_s - T[s+1] \cdot h) + T[s+m+1]\right) \bmod q, \quad h = d^{m-1} \bmod q$$

앞 글자 빼고 → 왼쪽으로 shift → 새 글자 더하기. 이전 해시에서 $O(1)$ 에 다음 해시 계산.

```python
def string_matching_rabin_karp(T: str, P: str, d=256, q=10**9+7):
    n, m = len(T), len(P)
    h = pow(d, m - 1, q)
    p, t = 0, 0
    for i in range(m):
        p = (d * p + ord(P[i])) % q
        t = (d * t + ord(T[i])) % q
    shifts = []
    for s in range(n - m + 1):
        if p == t and T[s:s + m] == P:
            shifts.append(s)
        if s < n - m:
            t = (d * (t - ord(T[s]) * h) + ord(T[s + m])) % q
    return shifts
```

**시간복잡도:** $O(n+m)$ expected

### 4.1 해시 충돌 확률과 기대 spurious hit 수

해시 함수가 $\bmod\, q$ 에서 균등 분포한다고 가정하면, 서로 다른 두 문자열 $X \neq Y$ 에 대해

$$\Pr[\,\text{hash}(X) = \text{hash}(Y)\,] = \frac{1}{q}$$

즉 spurious hit(해시는 같지만 실제 문자열은 다른 경우)이 발생할 확률은 각 윈도우마다 $\frac{1}{q}$.

텍스트에 총 $n - m + 1$ 개의 윈도우가 있으므로, 기대 spurious hit 수는

$$\mathbb{E}[\,\text{spurious hits}\,] = \frac{n - m + 1}{q}$$

$q$ 를 충분히 큰 소수(예: $10^9 + 7$)로 잡으면 이 값은 사실상 0에 가깝다. spurious hit이 발생해도 문자열 전체를 $O(m)$ 으로 검증하면 되므로, 전체 기대 시간복잡도는 $O(n + m)$ 이 된다.

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="rk-T" value="2359031415267399" maxlength="18" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:200px;" placeholder="Text T (숫자)">
  <input id="rk-P" value="31415" maxlength="6" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:100px;" placeholder="Pattern P">
  <button onclick="rkRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="rkBack()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">◀ 이전</button>
  <button onclick="rkStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 다음</button>
</div>
<canvas id="rk-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;margin-top:10px;">
  <div id="rk-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.8;">시작 버튼을 누르세요.</div>
</div>
</div>
<script>
(function(){
const cv=document.getElementById('rk-canvas');
const ctx=cv.getContext('2d');
let W=560,H=200,dpr=1;
cv.style.aspectRatio='560/200';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(rks)drawRk();}
new ResizeObserver(resize).observe(cv);

const RD=10,RQ=13;
let rks=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";
const C=(v,c)=>`<span style="color:${c}">${v}</span>`;

function hashStr(s,len){let h=0;for(let i=0;i<len;i++)h=(RD*h+parseInt(s[i]))%RQ;return h;}

function buildRkSteps(T,P){
  const n=T.length,m=P.length;
  const steps=[];
  let hh=1;for(let i=0;i<m-1;i++)hh=(hh*RD)%RQ;
  const ph=hashStr(P,m);
  let th=hashStr(T,m);
  const found=[],spurious=[];
  steps.push({s:0,th,ph,found:[],spurious:[],
    msg:`${C('P hash','#ffd740')}("${P}") mod ${RQ} = ${C(ph,'#ffd740')}<br>초기 T hash("${T.slice(0,m)}") = ${C(th,'#90caf9')}<br>h = d^(m-1) mod q = ${C(hh,'#ce93d8')}`});
  for(let s=0;s<n-m+1;s++){
    const cur=T.slice(s,s+m);
    const hashMatch=th===ph;
    const realMatch=cur===P;
    let line3;
    if(hashMatch&&realMatch){found.push(s);line3=`${C('해시일치 + 실제일치','#69f0ae')} → 발견! 위치 ${C(s,'#ffd740')}`;}
    else if(hashMatch){spurious.push(s);line3=`${C('해시일치','#ffd740')} but ${C('실제불일치','#ef5350')} → Spurious Hit`;}
    else{line3=`${C('해시불일치','#7986cb')} → 스킵`;}
    steps.push({s,th,ph,found:[...found],spurious:[...spurious],
      msg:`s=${C(s,'#90caf9')}: T[${s}..${s+m-1}]="${C(cur,'#ffd740')}"<br>hash = ${C(th,'#ffd740')} (P hash = ${C(ph,'#ce93d8')})<br>${line3}`});
    if(s<n-m){
      const oldTh=th;
      const removeChar=T[s],addChar=T[s+m];
      const removeVal=parseInt(removeChar),addVal=parseInt(addChar);
      const newTh=((RD*(th-(removeVal*hh%RQ)+RQ)+addVal)%RQ+RQ)%RQ;
      th=newTh;
      steps.push({s,rolling:true,removeIdx:s,addIdx:s+m,removeChar,addChar,removeVal,addVal,oldTh,newTh,hh,
        th,ph,found:[...found],spurious:[...spurious],
        msg:`Rolling Hash: s=${C(s,'#90caf9')} → s=${C(s+1,'#90caf9')}<br>${C('빼기','#ef5350')} T[${s}]='${removeChar}'(${removeVal}) × h=${hh}, ${C('더하기','#69f0ae')} T[${s+m}]='${addChar}'(${addVal})<br>= (d×(${oldTh} - ${removeVal}×${hh}) + ${addVal}) mod ${RQ} = ${C(newTh,'#ffd740')}`});
    }
  }
  steps.push({s:n-m,th,ph,found:[...found],spurious:[...spurious],done:true,
    msg:`완료! 발견: ${found.length?found.map(f=>C(f,'#69f0ae')).join(', '):C('없음','#ef5350')} | Spurious hit: ${C(spurious.length,'#ef9a9a')}`});
  return steps;
}

function drawRk(){
  if(!rks)return;
  ctx.clearRect(0,0,W,H);
  const {T,P,steps,idx}=rks;
  const st=steps[idx];
  const {s,found,spurious}=st;
  const n=T.length,m=P.length;
  const bw=Math.min(Math.floor((W-40)/n),54);
  const bh=Math.max(42,Math.round(H*0.24));
  const gap=3;
  const startX=Math.round((W-n*(bw+gap)+gap)/2);
  const indexH=16,hashBarH=22,rowGap=8;
  const totalH=indexH+bh+rowGap+hashBarH;
  const ty=Math.round((H-totalH)/2)+indexH;
  const fs=Math.round(bh*0.45);

  // index labels
  ctx.fillStyle='#8090a0';ctx.font=`${Math.round(bh*0.28)}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  for(let k=0;k<n;k++) ctx.fillText(k,startX+k*(bw+gap)+bw/2,ty-10);

  // boxes
  for(let k=0;k<n;k++){
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    if(found.some(f=>k>=f&&k<f+m)){bg='#1b3a1f';border='#69f0ae';tc='#69f0ae';}
    else if(spurious.some(sp=>k>=sp&&k<sp+m)){bg='#3a0a0a';border='#e53935';tc='#ef9a9a';}
    if(st.rolling){
      // rolling step: highlight remove (red) and add (green) chars, current window dim
      if(k===st.removeIdx){bg='#3a1010';border='#ef5350';tc='#ef5350';}
      else if(k===st.addIdx){bg='#0d2b1a';border='#69f0ae';tc='#69f0ae';}
      else if(k>s&&k<s+m){bg='#1e2130';border='#3a3f50';tc='#8090a0';}
      else if(k>=s&&k<s+m){bg='#2a1f00';border='#ffd74055';tc='#ffd74088';}
    } else {
      if(k>=s&&k<s+m&&!found.some(f=>k>=f&&k<f+m)&&!spurious.some(sp=>k>=sp&&k<sp+m)){bg='#2a1f00';border='#ffd740';tc='#ffd740';}
    }
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),ty,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),ty,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(T[k],startX+k*(bw+gap)+bw/2,ty+bh/2);
  }

  // rolling: draw minus arrow over removeIdx, plus arrow over addIdx
  if(st.rolling){
    const arrowY=ty-4;
    const rx=startX+st.removeIdx*(bw+gap)+bw/2;
    const ax=startX+st.addIdx*(bw+gap)+bw/2;
    // minus sign above remove char
    ctx.fillStyle='#ef5350';ctx.font=`bold 15px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='bottom';
    ctx.fillText('−',rx,arrowY);
    // plus sign above add char
    ctx.fillStyle='#69f0ae';ctx.font=`bold 15px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='bottom';
    ctx.fillText('+',ax,arrowY);
    // dashed arrow from old window to new window (shift right)
    const wx1=startX+s*(bw+gap)+bw/2;
    const wx2=startX+(s+1)*(bw+gap)+bw/2;
    const wy=ty+bh+rowGap+hashBarH/2;
    ctx.save();ctx.strokeStyle='#ffd74088';ctx.lineWidth=1.5;ctx.setLineDash([4,3]);
    ctx.beginPath();ctx.moveTo(wx1,wy);ctx.lineTo(wx2-4,wy);ctx.stroke();
    ctx.setLineDash([]);
    // arrowhead
    ctx.fillStyle='#ffd74088';ctx.beginPath();ctx.moveTo(wx2,wy);ctx.lineTo(wx2-7,wy-4);ctx.lineTo(wx2-7,wy+4);ctx.closePath();ctx.fill();
    ctx.restore();
  }

  // hash bar under current window
  const barY=ty+bh+rowGap;
  const barX=startX+s*(bw+gap);
  const barW=m*(bw+gap)-gap;
  const isMatch=st.th===st.ph;
  const isReal=T.slice(s,s+m)===P;
  const barColor=st.rolling?'#ffd740':isMatch?(isReal?'#69f0ae':'#e53935'):'#5c6bc0';
  ctx.fillStyle=st.rolling?'rgba(255,215,64,0.08)':isMatch?(isReal?'rgba(105,240,174,0.15)':'rgba(229,57,53,0.15)'):'rgba(92,107,192,0.1)';
  ctx.fillRect(barX,barY,barW,hashBarH);
  ctx.strokeStyle=barColor;ctx.lineWidth=1;ctx.strokeRect(barX,barY,barW,hashBarH);
  ctx.fillStyle=barColor;
  ctx.font=`bold 13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText(st.rolling?`${st.oldTh} → ${st.newTh}`:`h=${st.th}`,barX+barW/2,barY+hashBarH/2);
}

window.rkRestart=function(){
  const T=document.getElementById('rk-T').value||'2359031415267399';
  const P=document.getElementById('rk-P').value||'31415';
  if(P.length>T.length)return;
  const steps=buildRkSteps(T,P);
  rks={T,P,steps,idx:0};
  document.getElementById('rk-info').innerHTML=steps[0].msg;
  drawRk();
};
window.rkBack=function(){
  if(!rks||rks.idx<=0)return;
  rks.idx--;
  document.getElementById('rk-info').innerHTML=rks.steps[rks.idx].msg;
  drawRk();
};
window.rkStep=function(){
  if(!rks||rks.idx>=rks.steps.length-1)return;
  rks.idx++;
  document.getElementById('rk-info').innerHTML=rks.steps[rks.idx].msg;
  drawRk();
};
rkRestart();
})();
</script>
{{< /rawhtml >}}

### Spurious Hit

해시가 같아도 실제 문자열이 다를 수 있다 — **Spurious Hit**.

- **Strict Verification**: 해시 일치 시 실제 문자열 직접 비교
- **Double Hashing**: 독립적인 해시 두 개 사용. 충돌 확률 $\frac{1}{q_1 \cdot q_2} \approx 0$

기댓값 분석: $q = 10^9+7$ 이면 $n = 10^9$ 텍스트에서도 Spurious Hit 기댓값 $\approx 1$ 회.

---

## 5. Problem 4.2 — String Exponentiation

문자열 $S$ 가 주어질 때, $S = A^k$ 를 만족하는 최대 $k$ 를 구하라.

### 핵심 관찰

$S = A^k$ 이면 $S$ 는 주기 $p = |A|$ 를 가진다. 즉 $S[i] = S[i+p]$ 가 모든 유효한 $i$ 에 대해 성립.

$\pi[n-1]$ 은 $S$ 전체에서 접두사 = 접미사인 가장 긴 길이이므로, 겹치는 부분의 길이가 $\pi[n-1]$ 이고 **겹치지 않는 최소 반복 단위**의 길이가

$$p = n - \pi[n-1]$$

### 판별 규칙

$$k = \begin{cases} n/p & n \bmod p = 0 \\ 1 & \text{otherwise} \end{cases}$$

$n \bmod p = 0$ 이 아니면 $S$ 는 완전한 반복이 아니므로 $k = 1$.

### 예시: $S = \texttt{abcabcabc}$

| $i$ | $S[i]$ | $\pi[i]$ |
|-----|--------|----------|
| 0 | a | 0 |
| 1 | b | 0 |
| 2 | c | 0 |
| 3 | a | 1 |
| 4 | b | 2 |
| 5 | c | 3 |
| 6 | a | 4 |
| 7 | b | 5 |
| 8 | c | 6 |

$$n = 9,\quad \pi[n-1] = 6,\quad p = 9 - 6 = 3,\quad 9 \bmod 3 = 0 \implies k = \frac{9}{3} = 3$$

접두사 `abcabcabc` 와 접미사 `abcabcabc` 가 길이 6 만큼 겹친다 — 즉 반복 단위 `abc` 가 3번 등장.

### 알고리즘

1. $\pi$ 배열 계산
2. $p = n - \pi[n-1]$
3. $n \bmod p = 0$ 이면 $k = n/p$, 아니면 $k = 1$

```python
def maximum_exponent(s: str):
    n = len(s)
    pi = compute_prefix_function(s)
    period = n - pi[-1]
    if n % period == 0:
        return n // period
    else:
        return 1
```

---

## 6. Problem 4.3 — Longest Repeated Substring

### 6.1 문제 정의

- **입력:** 소문자 영문자로 구성된 길이 $n$ 의 문자열 $S$
- **출력:** $S$ 에서 **두 번 이상** 등장하는 부분 문자열 중 가장 긴 것의 길이 $L$
- **조건:** 두 등장 위치가 겹쳐도 됨 (overlapping 허용)

$S = \texttt{banana}$ 에서 두 번 이상 나오는 부분 문자열 중 가장 긴 것은?

- `b` → 1번만 → ✗
- `an` → $S[1..2]$, $S[3..4]$ → ✓
- `ana` → $S[1..3]$, $S[3..5]$ → ✓ (겹쳐도 됨!)
- `anan` → 1번만 → ✗

→ 답: $L = 3$

| 예시 | 답 | 근거 |
|------|-----|------|
| `abcabcabc` | 6 | `abcabc` 가 위치 0, 3 에 등장 (overlap) |
| `abcd` | 0 | 반복 부분문자열 없음 |
| `banana` | 3 | `ana` 가 위치 1, 3 에 등장 |

---

### 6.2 접근법 1 — DP: $O(n^2)$

**아이디어:** 모든 접미사 쌍 $(S[i:],\ S[j:])$ 의 LCP(Longest Common Prefix)를 DP 테이블로 구한다.

$$dp[i][j] = \text{LCP}(S[i:],\ S[j:]) = \begin{cases} dp[i+1][j+1] + 1 & S[i] = S[j] \\ 0 & \text{otherwise} \end{cases}$$

답 $= \max_{i \neq j} dp[i][j]$

**한계:** 테이블 크기 $O(n^2)$, 시간·공간 모두 $O(n^2)$.

---

### 6.3 접근법 2 — KMP: $O(n^2)$

**아이디어:** 각 접미사 $S[i:]$ 에 대해 prefix function을 계산한다. $\pi[k]$ 의 최댓값이 그 접미사 내에서 가장 긴 "접두사 = 접미사" 길이이므로 반복 부분문자열 후보가 된다.

**한계:** 접미사가 $n$ 개, 각 prefix function 계산이 $O(n)$ → 전체 $O(n^2)$.

---

### 6.4 접근법 3 — Rabin-Karp + 이진탐색: $O(n \log n)$

#### 핵심 관찰 — 단조성

`check(L)` = "길이 $L$ 인 중복 부분문자열이 존재하는가?"

길이 $L$ 짜리가 두 번 나오면, 그 앞 $L-1$ 글자도 반드시 두 번 나온다:

$$\text{check}(L) = \text{True} \implies \text{check}(L-1) = \text{True}$$

유효한 길이 집합은 항상 $\{0, 1, \ldots, k\}$ 형태 → **이진탐색으로 최대 $k$ 탐색 가능**.

#### check(L) 구현 — Rolling Hash

고정된 $L$ 에 대해 길이 $L$ 창을 슬라이드하며 해시를 집합에 넣는다. 해시 충돌 시 실제 문자열로 검증.

```
S = b a n a n a,  L = 3

창[0]: "ban" → hash=H1 → seen={H1:[0]}
창[1]: "ana" → hash=H2 → seen={H1:[0], H2:[1]}
창[2]: "nan" → hash=H3 → seen={..., H3:[2]}
창[3]: "ana" → hash=H2 → H2 이미 있음! "ana"=="ana" → True ✓
```

rolling hash 갱신 $O(1)$:

$$h_{s+1} = \bigl(d \cdot h_s - S[s] \cdot d^L + S[s+L]\bigr) \bmod q$$

#### 이진탐색 흐름

```
left=0, right=n, ans=0
while left <= right:
    mid = (left+right) // 2
    if check(mid):      # 길이 mid 중복 존재
        ans = mid
        left = mid + 1  # 더 길어도 가능?
    else:
        right = mid - 1 # 더 짧은 것만 가능
return ans
```

**시간복잡도:** `check` $O(n)$ × 이진탐색 $O(\log n)$ = **$O(n \log n)$**

```python
def has_duplicate_substring(T: str, L: int, d=256, q=10**9+7) -> bool:
    n = len(T)
    if L == 0:
        return True
    if L > n:
        return False
    h = pow(d, L - 1, q)
    t = 0
    for i in range(L):
        t = (d * t + ord(T[i])) % q
    seen = {t: [0]}
    for s in range(1, n - L + 1):
        t = (d * (t - ord(T[s - 1]) * h) + ord(T[s + L - 1])) % q
        if t in seen:
            current = T[s:s + L]
            for prev in seen[t]:
                if T[prev:prev + L] == current:
                    return True
            seen[t].append(s)
        else:
            seen[t] = [s]
    return False


def longest_repeated(n: int, s: str) -> int:
    def bin_search(left: int, right: int) -> int:
        if left > right:
            return right
        mid = (left + right) // 2
        if has_duplicate_substring(s, mid):
            return bin_search(mid + 1, right)
        else:
            return bin_search(left, mid - 1)
    return bin_search(0, n)
```

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="bs-S" value="banana" maxlength="14" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:160px;" placeholder="String S">
  <button onclick="bsRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="bsBack()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">◀ 이전</button>
  <button onclick="bsStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 다음</button>
</div>
<canvas id="bs-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;margin-top:10px;">
  <div id="bs-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.8;">시작 버튼을 누르세요.</div>
</div>
</div>
<script>
(function(){
const cv=document.getElementById('bs-canvas');
const ctx=cv.getContext('2d');
let W=560,H=280,dpr=1;
cv.style.aspectRatio='560/280';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(bss)drawBs();}
new ResizeObserver(resize).observe(cv);

let bss=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";
const RD=256,RQ=1000003;

function hasDup(s,L){
  if(L===0)return{found:true,pos:[]};
  const n=s.length;if(L>n)return{found:false,pos:[]};
  let h=1;for(let i=0;i<L-1;i++)h=(h*RD)%RQ;
  let t=0;for(let i=0;i<L;i++)t=(RD*t+s.charCodeAt(i))%RQ;
  const seen=new Map();seen.set(t,[0]);
  for(let i=1;i<=n-L;i++){
    t=((RD*(t-s.charCodeAt(i-1)*h%RQ+RQ)+s.charCodeAt(i+L-1))%RQ+RQ)%RQ;
    if(seen.has(t)){
      for(const p of seen.get(t)){
        if(s.slice(p,p+L)===s.slice(i,i+L))return{found:true,pos:[p,i]};
      }
      seen.get(t).push(i);
    } else seen.set(t,[i]);
  }
  return{found:false,pos:[]};
}

function buildSteps(s){
  const n=s.length;
  const C=(v,c)=>`<span style="color:${c}">${v}</span>`;
  const steps=[];
  let left=0,right=n,ans=0;
  steps.push({left,right,mid:null,result:null,ans,winPos:[],winLen:0,
    msg:`이진탐색 시작<br>${C('left='+left,'#90caf9')}, ${C('right='+right,'#90caf9')}`});
  while(left<=right){
    const mid=Math.floor((left+right)/2);
    const {found,pos}=hasDup(s,mid);
    const substr=found&&mid>0?` → "${C(s.slice(pos[0],pos[0]+mid),'#69f0ae')}" 위치 ${C(pos[0],'#ffd740')}, ${C(pos[1],'#ffd740')}`:'';
    steps.push({left,right,mid,result:found,ans,winPos:pos,winLen:mid,
      msg:`${C('mid='+mid,'#ffd740')}: check(${mid}) = ${found?C('True','#69f0ae'):C('False','#ef5350')}${substr}<br>→ ${found?C('left='+(mid+1),'#90caf9'):C('right='+(mid-1),'#90caf9')}`});
    if(found){ans=mid;left=mid+1;}
    else right=mid-1;
  }
  steps.push({left,right,mid:null,result:null,ans,winPos:[],winLen:0,
    msg:`완료! 최장 반복 부분문자열 길이 = ${C(ans,'#69f0ae')}${ans>0?` ("${C(s.slice(0,ans),'#ffd740')}..." 등)`:`  (반복 없음)`}`});
  return steps;
}

function drawBs(){
  if(!bss)return;
  ctx.clearRect(0,0,W,H);
  const {s,steps,idx}=bss;
  const n=s.length;
  const st=steps[idx];

  // === Row 1: binary search on lengths 0..n ===
  const bw1=Math.min(Math.floor((W-40)/(n+1)),52);
  const bh1=Math.max(36,Math.round(H*0.15));
  const gap1=3;
  const row1X=(W-(n+1)*(bw1+gap1))/2;
  const row1Y=Math.round(H*0.05);
  const fs1=Math.round(bh1*0.42);

  // label
  ctx.fillStyle='#8090a0';ctx.font=`12px ${MONO}`;ctx.textAlign='left';ctx.textBaseline='middle';
  ctx.fillText('길이',row1X-36,row1Y+bh1/2);

  // cumulative answer: all lengths ≤ ans are confirmed True
  let curAns=0;steps.slice(0,idx+1).forEach(st=>{if(st.ans>curAns)curAns=st.ans;});

  for(let L=0;L<=n;L++){
    let bg='#1e2130',border='#2a2d3a',tc='#607080';
    if(st.mid===L){bg='#2a1f00';border='#ffd740';tc='#ffd740';}
    else if(L<=curAns&&curAns>0){bg='#0d2818';border='#43a047';tc='#69f0ae';}
    else if(st.result===false&&st.mid!==null&&L>st.right){tc='#37474f';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(row1X+L*(bw1+gap1),row1Y,bw1,bh1,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(row1X+L*(bw1+gap1),row1Y,bw1,bh1,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs1}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(L,row1X+L*(bw1+gap1)+bw1/2,row1Y+bh1/2);
  }
  // L R M pointers
  const pY=row1Y+bh1+4;
  ctx.font=`bold 12px sans-serif`;ctx.textBaseline='top';
  if(st.left<=n){ctx.fillStyle='#90caf9';ctx.textAlign='center';ctx.fillText('L',row1X+st.left*(bw1+gap1)+bw1/2,pY);}
  if(st.right>=0&&st.right<=n){ctx.fillStyle='#90caf9';ctx.textAlign='center';ctx.fillText('R',row1X+st.right*(bw1+gap1)+bw1/2,pY);}
  if(st.mid!==null){ctx.fillStyle='#ffd740';ctx.textAlign='center';ctx.fillText('M',row1X+st.mid*(bw1+gap1)+bw1/2,pY+14);}

  // === Row 2: string S with sliding window for current mid ===
  const bw2=Math.min(Math.floor((W-40)/n),52);
  const bh2=Math.max(36,Math.round(H*0.15));
  const gap2=3;
  const row2X=(W-n*(bw2+gap2))/2;
  const row2Y=Math.round(H*0.52);
  const fs2=Math.round(bh2*0.44);
  const L=st.winLen;
  const [p1,p2]=st.winPos;

  ctx.fillStyle='#8090a0';ctx.font=`12px ${MONO}`;ctx.textAlign='left';ctx.textBaseline='middle';
  ctx.fillText('문자열',row2X-46,row2Y+bh2/2);

  for(let k=0;k<n;k++){
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    if(st.result===true&&L>0){
      if(k>=p1&&k<p1+L){bg='#0d2818';border='#43a047';tc='#69f0ae';}
      if(k>=p2&&k<p2+L){bg='#1a0a2e';border='#7c4dff';tc='#ce93d8';}
    } else if(st.result===false&&L>0){
      // show last window checked = position n-L
      const last=n-L;
      if(k>=last&&k<last+L){bg='#2a0a0a';border='#ef5350';tc='#ef9a9a';}
    }
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(row2X+k*(bw2+gap2),row2Y,bw2,bh2,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(row2X+k*(bw2+gap2),row2Y,bw2,bh2,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs2}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(s[k],row2X+k*(bw2+gap2)+bw2/2,row2Y+bh2/2);
    // index
    ctx.fillStyle='#8090a0';ctx.font=`${Math.round(bh2*0.28)}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(k,row2X+k*(bw2+gap2)+bw2/2,row2Y-10);
  }

  // legend for row2
  if(st.result===true&&L>0){
    const lx=row2X,ly=row2Y+bh2+8;
    ctx.font=`12px ${MONO}`;ctx.textBaseline='top';
    ctx.fillStyle='#43a047';ctx.fillText(`■ 첫 번째 등장 [${p1}..${p1+L-1}]`,lx,ly);
    ctx.fillStyle='#7c4dff';ctx.fillText(`■ 두 번째 등장 [${p2}..${p2+L-1}]`,lx+180,ly);
  } else if(st.result===false&&L>0){
    ctx.font=`12px ${MONO}`;ctx.textBaseline='top';
    ctx.fillStyle='#ef5350';ctx.fillText(`■ 중복 없음 (길이 ${L})`,row2X,row2Y+bh2+8);
  }
}

window.bsRestart=function(){
  const s=document.getElementById('bs-S').value||'banana';
  const steps=buildSteps(s);
  bss={s,steps,idx:0};
  document.getElementById('bs-info').innerHTML=steps[0].msg;
  drawBs();
};
window.bsBack=function(){
  if(!bss||bss.idx<=0)return;
  bss.idx--;
  document.getElementById('bs-info').innerHTML=bss.steps[bss.idx].msg;
  drawBs();
};
window.bsStep=function(){
  if(!bss||bss.idx>=bss.steps.length-1)return;
  bss.idx++;
  document.getElementById('bs-info').innerHTML=bss.steps[bss.idx].msg;
  drawBs();
};
bsRestart();
})();
</script>
{{< /rawhtml >}}

---

## 7. 알고리즘 종합 비교

### 패턴 매칭 알고리즘

| 알고리즘 | 시간복잡도 | 공간 | 결정론적? | 핵심 아이디어 |
|---|---|---|---|---|
| **Naïve** | $O(nm)$ | $O(1)$ | ✓ | 모든 shift에서 전부 비교 |
| **KMP** | $O(n+m)$ | $O(m)$ | ✓ | $\pi$ 함수로 불일치 시 점프, $i$ 고정 |
| **Rabin-Karp** | $O(n+m)$ expected | $O(1)$ | ✗ | 해시 비교 후 일치 시만 검증 |

**KMP vs Rabin-Karp:** 둘 다 $O(n+m)$ 이지만 접근이 다르다.
- KMP는 결정론적 — 해시 충돌 없이 항상 정확.
- Rabin-Karp는 확률론적 — 여러 패턴 동시 검색에 유리.

### 응용 문제 알고리즘

| 문제 | 알고리즘 | 시간복잡도 | 핵심 도구 |
|---|---|---|---|
| **4.2** String Exponentiation | $\pi$ 함수 | $O(n)$ | $p = n - \pi[n-1]$, 주기 판별 |
| **4.3** Longest Repeated Substring (DP) | LCP DP | $O(n^2)$ | $dp[i][j] = \text{LCP}(S[i:], S[j:])$ |
| **4.3** Longest Repeated Substring (최적) | Rabin-Karp + 이진탐색 | $O(n \log n)$ | 단조성 → 이진탐색, rolling hash |