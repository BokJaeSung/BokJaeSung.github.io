---
title: "Lec.04 String Matching"
date: 2026-03-25T09:00:00+09:00
tags: ["알고리즘", "문자열", "KMP", "Rabin-Karp", "해시", "접두사함수"]
cover:
  image: 'images/cover.jpg'
  alt: 'Lec.04 String Matching'
  relative: true
summary: "From naïve O(nm) to KMP O(n+m): prefix function, rolling hash, and binary search on longest repeated substring."
---

## 1. 문자열 패턴 매칭 문제란?

텍스트 $T = t_1 t_2 \cdots t_n$ (길이 $n$) 안에서 패턴 $P = p_1 p_2 \cdots p_m$ (길이 $m \le n$) 이 등장하는 모든 위치를 찾는 문제다.

$$T[s+1 \cdots s+m] = P[1 \cdots m] \quad (0 \le s \le n-m)$$

$s$ 는 **shift** — 패턴을 텍스트 위에 갖다 댈 시작 위치다. $s \le n-m$ 인 이유는 그 이상이면 패턴이 텍스트 밖으로 삐져나오기 때문이다.

---

## 2. 나이브 알고리즘

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

나이브는 불일치 시 맞춰둔 $q$ 개의 정보를 전부 버리고 $s+1$ 로 이동한다.

그런데 우리는 이미 $T[s+1 \cdots s+q] = P[1 \cdots q]$ 라는 사실을 알고 있다. **텍스트 포인터 $i$ 는 절대 뒤로 가지 않는다.** 불일치 시 패턴 포인터 $q$ 만 $\pi[q-1]$ 로 줄인다.

### Prefix Function (접두사 함수)

$\pi[q]$ = $P[0 \cdots q]$ 에서 **자기 자신을 제외한** 접두사이면서 동시에 접미사인 것 중 가장 긴 길이.

자기 자신을 제외하는 이유: 포함하면 $q = \pi[q]$ 가 되어 무한루프. 항상 $\pi[q] < q$ 가 성립해야 한다.

```python
def compute_prefix_function(P: str):
    m = len(P)
    pi = [0] * m
    k = 0
    for q in range(1, m):
        while k > 0 and P[k] != P[q]:
            k = pi[k - 1]
        if P[k] == P[q]:
            k += 1
        pi[q] = k
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
  <input id="pi-P" value="ababaca" maxlength="12" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:160px;" placeholder="Pattern P">
  <button onclick="piRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="piStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 다음</button>
  <button onclick="piAuto()" id="pi-auto-btn" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">⏩ 자동</button>
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

let ps=null,piTimer=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";

function buildPiSteps(P){
  const m=P.length,pi=new Array(m).fill(0);
  // store k BEFORE the update so we can show j pointer correctly
  const steps=[{q:-1,k:0,kb:0,pi:[...pi],msg:'초기화: π 배열을 0으로 세팅'}];
  let k=0;
  for(let q=1;q<m;q++){
    const kb=k;
    while(k>0&&P[k]!==P[q])k=pi[k-1];
    if(P[k]===P[q])k++;
    pi[q]=k;
    const match=P[kb]===P[q];
    const cmp=match?`<span style="color:#69f0ae;font-weight:700">=</span>`:`<span style="color:#ef5350;font-weight:700">≠</span>`;
    steps.push({q,k,kb,pi:[...pi],msg:`<span style="color:#90caf9">i(q)=${q}</span>, <span style="color:#ef5350">j(k)=${kb}</span>: P[${kb}]='<span style="color:#ffd740">${P[kb]??'-'}</span>' ${cmp} P[${q}]='<span style="color:#ffd740">${P[q]}</span>' → k=<span style="color:#ce93d8">${k}</span> → <span style="color:#69f0ae">π[${q}]=${k}</span>`});
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

  // blue bracket: matched prefix [0..k-1] on pattern row
  const k=st.k,q=st.q,kb=st.kb??0;
  // draw prefix highlight bracket (k chars from left)
  if(k>0&&q>=0){
    const bx=startX,by=ty,bW=k*(bw+gap)-gap,bH=bh;
    ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;
    ctx.strokeRect(bx-1,by-1,bW+2,bH+2);
  }
  // draw suffix highlight bracket (k chars ending at q)
  if(k>0&&q>=0&&q-k+1>=0){
    const bx=startX+(q-k+1)*(bw+gap),by=ty,bW=k*(bw+gap)-gap,bH=bh;
    ctx.strokeStyle='#42a5f5';ctx.lineWidth=2.5;
    ctx.strokeRect(bx-1,by-1,bW+2,bH+2);
  }

  for(let i=0;i<m;i++){
    const x=startX+i*(bw+gap);
    // pattern row
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(x,ty,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,ty,bw,bh,4);ctx.stroke();
    // character
    ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.font=`bold ${fs}px ${MONO}`;ctx.fillStyle=tc;
    ctx.fillText(P[i],x+bw/2,ty+bh/2);
    // j pointer (kb = k before update = where prefix comparison happens)
    if(i===kb&&q>=0){
      ctx.font=`italic bold ${Math.round(fs*0.8)}px sans-serif`;
      ctx.fillStyle='#ef5350';ctx.textAlign='center';ctx.textBaseline='bottom';
      ctx.fillText('j',x+bw/2,ty-2);
    }
    // i pointer (q = current index)
    if(i===q&&q>=0){
      ctx.font=`italic bold ${Math.round(fs*0.8)}px sans-serif`;
      ctx.fillStyle='#42a5f5';ctx.textAlign='center';ctx.textBaseline='bottom';
      ctx.fillText('i',x+bw/2,ty-2);
    }

    // π row
    const piVal=i<=q&&q>=0?st.pi[i]:null;
    bg='#1e2130';border='#2a2d3a';tc='#8090a0';
    if(piVal!==null&&piVal>0){bg='#1a0a2e';border='#7c4dff';tc='#b39ddb';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(x,py,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,py,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(piVal!==null?piVal:'',x+bw/2,py+bh/2);
  }
}

window.piRestart=function(){
  if(piTimer){clearInterval(piTimer);piTimer=null;document.getElementById('pi-auto-btn').textContent='⏩ 자동';}
  const P=document.getElementById('pi-P').value||'ababaca';
  ps={P,steps:buildPiSteps(P),idx:0};
  document.getElementById('pi-info').innerHTML=ps.steps[0].msg;
  drawPi();
};
window.piStep=function(){
  if(!ps||ps.idx>=ps.steps.length-1)return;
  ps.idx++;
  document.getElementById('pi-info').innerHTML=ps.steps[ps.idx].msg;
  drawPi();
};
window.piAuto=function(){
  if(piTimer){clearInterval(piTimer);piTimer=null;document.getElementById('pi-auto-btn').textContent='⏩ 자동';return;}
  if(!ps)piRestart();
  document.getElementById('pi-auto-btn').textContent='⏸ 정지';
  piTimer=setInterval(()=>{if(!ps||ps.idx>=ps.steps.length-1){clearInterval(piTimer);piTimer=null;document.getElementById('pi-auto-btn').textContent='⏩ 자동';return;}piStep();},500);
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
  <input id="kmp-T" value="abcababcab" maxlength="16" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:180px;" placeholder="Text T">
  <input id="kmp-P" value="ababc" maxlength="8" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:120px;" placeholder="Pattern P">
  <button onclick="kmpRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="kmpStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 한 칸</button>
  <button onclick="kmpAuto()" id="kmp-auto-btn" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">⏩ 자동</button>
</div>
<canvas id="kmp-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:10px;margin-top:10px;align-items:stretch;">
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;">
    <div id="kmp-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.6;">시작 버튼을 누르세요.</div>
    <div id="kmp-pi-row" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;color:#8090a0;margin-top:4px;"></div>
  </div>
  <div style="min-width:140px;background:#1a1d27;border-left:3px solid #37474f;border-radius:6px;padding:10px 14px;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;">
    <div style="font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5c6bc0;margin-bottom:6px;">Stats</div>
    <div>비교: <span id="kmp-cmp" style="color:#ffd740;">0</span></div>
    <div>i: <span id="kmp-i" style="color:#90caf9;">-</span></div>
    <div>q: <span id="kmp-q" style="color:#a5d6a7;">-</span></div>
    <div>발견: <span id="kmp-found" style="color:#69f0ae;">-</span></div>
  </div>
</div>
<p style="font-size:13px;color:#778;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">green = matched · red = mismatch · blue = current i · purple = reused chars</p>
</div>
<script>
(function(){
const cv=document.getElementById('kmp-canvas');
const ctx=cv.getContext('2d');
let W=560,H=190,dpr=1;
cv.style.aspectRatio='560/190';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(ks)drawKmp();}
new ResizeObserver(resize).observe(cv);

let ks=null,kmpTimer=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";

function computePi(P){const m=P.length,pi=new Array(m).fill(0);let k=0;for(let q=1;q<m;q++){while(k>0&&P[k]!==P[q])k=pi[k-1];if(P[k]===P[q])k++;pi[q]=k;}return pi;}

function drawKmp(){
  if(!ks)return;
  ctx.clearRect(0,0,W,H);
  const {T,P,i,q,found,done,pi}=ks;
  const n=T.length,m=P.length;
  const bw=Math.min(Math.floor((W-40)/n),54);
  const bh=Math.max(42,Math.round(H*0.22));
  const gap=3;
  const startX=(W-n*(bw+gap))/2;
  const ty=18,py=ty+bh+22;
  const fs=Math.round(bh*0.45);
  const s=i-q;

  ctx.fillStyle='#8090a0';ctx.font=`13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  for(let k=0;k<n;k++) ctx.fillText(k,startX+k*(bw+gap)+bw/2,ty-10);

  for(let k=0;k<n;k++){
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    if(found.some(f=>k>=f&&k<f+m)){bg='#1b3a1f';border='#69f0ae';tc='#69f0ae';}
    else if(!done){
      if(k===i){bg='#1a237e';border='#5c6bc0';tc='#9fa8da';}
      else if(k>=s&&k<i){bg='#1b3a1f';border='#43a047';tc='#69f0ae';}
    }
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),ty,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),ty,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(T[k],startX+k*(bw+gap)+bw/2,ty+bh/2);
  }

  const patStart=startX+s*(bw+gap);
  for(let k=0;k<m;k++){
    let bg='#1a1a2e',border='#3949ab',tc='#7986cb';
    if(k<q){bg='#1a0a2e';border='#7c4dff';tc='#b39ddb';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(patStart+k*(bw+gap),py,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(patStart+k*(bw+gap),py,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(P[k],patStart+k*(bw+gap)+bw/2,py+bh/2);
  }
  // s label
  ctx.fillStyle='#8090a0';ctx.font=`13px sans-serif`;ctx.textAlign='center';ctx.textBaseline='top';
  ctx.fillText(`s=${s}`,patStart+m*(bw+gap)/2,py+bh+3);
}

window.kmpRestart=function(){
  if(kmpTimer){clearInterval(kmpTimer);kmpTimer=null;document.getElementById('kmp-auto-btn').textContent='⏩ 자동';}
  const T=document.getElementById('kmp-T').value||'abcababcab';
  const P=document.getElementById('kmp-P').value||'ababc';
  if(P.length>T.length)return;
  const pi=computePi(P);
  ks={T,P,pi,i:0,q:0,cmp:0,found:[],done:false};
  document.getElementById('kmp-cmp').textContent='0';
  document.getElementById('kmp-i').textContent='0';
  document.getElementById('kmp-q').textContent='0';
  document.getElementById('kmp-found').textContent='-';
  document.getElementById('kmp-pi-row').textContent=`π = [${pi.join(', ')}]`;
  document.getElementById('kmp-info').innerHTML=`<span style="color:#90caf9">i=0</span>, <span style="color:#90caf9">q=0</span> 에서 시작`;
  drawKmp();
};
const kI=id=>document.getElementById(id);
const kC=(v,c)=>`<span style="color:${c}">${v}</span>`;
const kIdx=v=>kC(v,'#90caf9');
const kChr=v=>kC(`'${v}'`,'#ffd740');
const kRes=v=>kC(v,'#ce93d8');
const kOk=v=>kC(v,'#69f0ae');
const kNg=v=>kC(v,'#ef5350');

window.kmpStep=function(){
  if(!ks||ks.done)return;
  const {T,P,pi}=ks;const n=T.length,m=P.length;
  if(ks.i>=n){ks.done=true;kI('kmp-info').innerHTML=`완료! 총 <span style="color:#ffd740">${ks.cmp}</span>번 비교`;drawKmp();return;}
  ks.cmp++;
  kI('kmp-cmp').textContent=ks.cmp;
  if(P[ks.q]===T[ks.i]){
    kI('kmp-info').innerHTML=`${kIdx('i='+ks.i)}, ${kIdx('q='+ks.q)}: ${kChr(T[ks.i])} <b style="color:#69f0ae">=</b> ${kChr(P[ks.q])} ${kOk('✓')} → ${kRes('q+1')}`;
    ks.q++;ks.i++;
    if(ks.q===m){const pos=ks.i-m;ks.found.push(pos);kI('kmp-found').textContent=ks.found.join(', ');kI('kmp-info').innerHTML=`${kOk('✓ 패턴 발견!')} ${kIdx('s='+pos)} → ${kRes('q=π['+(m-1)+']='+pi[m-1])}`;ks.q=pi[m-1];}
  } else {
    if(ks.q>0){kI('kmp-info').innerHTML=`${kIdx('i='+ks.i)}, ${kIdx('q='+ks.q)}: ${kChr(T[ks.i])} <b style="color:#ef5350">≠</b> ${kChr(P[ks.q])} → ${kRes('q=π['+(ks.q-1)+']='+pi[ks.q-1])} <span style="color:#ce93d8;font-size:0.9em">(i 고정!)</span>`;ks.q=pi[ks.q-1];}
    else{kI('kmp-info').innerHTML=`${kIdx('i='+ks.i)}, ${kIdx('q=0')}: ${kChr(T[ks.i])} <b style="color:#ef5350">≠</b> ${kChr(P[0])} → ${kRes('i+1')}`;ks.i++;}
  }
  kI('kmp-i').textContent=ks.i;
  kI('kmp-q').textContent=ks.q;
  if(ks.i>=n){ks.done=true;kI('kmp-info').innerHTML=`완료! 총 <span style="color:#ffd740">${ks.cmp}</span>번 | 발견: ${ks.found.length?kOk(ks.found.join(', ')):kNg('없음')}`;}
  drawKmp();
};

window.kmpAuto=function(){
  if(kmpTimer){clearInterval(kmpTimer);kmpTimer=null;document.getElementById('kmp-auto-btn').textContent='⏩ 자동';return;}
  if(!ks)kmpRestart();
  document.getElementById('kmp-auto-btn').textContent='⏸ 정지';
  kmpTimer=setInterval(()=>{if(!ks||ks.done){clearInterval(kmpTimer);kmpTimer=null;document.getElementById('kmp-auto-btn').textContent='⏩ 자동';return;}kmpStep();},280);
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

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="rk-T" value="2359031415267399" maxlength="18" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:200px;" placeholder="Text T (숫자)">
  <input id="rk-P" value="31415" maxlength="6" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:100px;" placeholder="Pattern P">
  <button onclick="rkRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="rkStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 슬라이드</button>
  <button onclick="rkAuto()" id="rk-auto-btn" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">⏩ 자동</button>
</div>
<canvas id="rk-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:10px;margin-top:10px;align-items:stretch;">
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;">
    <div id="rk-hash-line" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;line-height:1.8;"></div>
  </div>
  <div style="min-width:140px;background:#1a1d27;border-left:3px solid #37474f;border-radius:6px;padding:10px 14px;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;">
    <div style="font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5c6bc0;margin-bottom:6px;">Stats</div>
    <div>슬라이드: <span id="rk-steps" style="color:#ffd740;">0</span></div>
    <div>해시일치: <span id="rk-hit" style="color:#ef9a9a;">0</span></div>
    <div>발견: <span id="rk-found" style="color:#69f0ae;">-</span></div>
  </div>
</div>
<p style="font-size:13px;color:#778;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">amber = current window · green = match found · red = spurious hit</p>
</div>
<script>
(function(){
const cv=document.getElementById('rk-canvas');
const ctx=cv.getContext('2d');
let W=560,H=170,dpr=1;
cv.style.aspectRatio='560/170';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(rks)drawRk();}
new ResizeObserver(resize).observe(cv);

const RD=10,RQ=13;
let rks=null,rkTimer=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";

function hashStr(s,len){let h=0;for(let i=0;i<len;i++)h=(RD*h+parseInt(s[i]))%RQ;return h;}

function drawRk(){
  if(!rks)return;
  ctx.clearRect(0,0,W,H);
  const {T,P,s,m,found,spurious}=rks;
  const n=T.length;
  const bw=Math.min(Math.floor((W-40)/n),54);
  const bh=Math.max(42,Math.round(H*0.26));
  const gap=3;
  const startX=(W-n*(bw+gap))/2;
  const ty=18;
  const fs=Math.round(bh*0.45);

  ctx.fillStyle='#8090a0';ctx.font=`13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  for(let k=0;k<n;k++) ctx.fillText(k,startX+k*(bw+gap)+bw/2,ty-10);

  for(let k=0;k<n;k++){
    let bg='#1e2130',border='#2a2d3a',tc='#b0b8d0';
    if(found.some(f=>k>=f&&k<f+m)){bg='#1b3a1f';border='#69f0ae';tc='#69f0ae';}
    else if(spurious.includes(k-s+s)&&k>=s&&k<s+m){bg='#3a0a0a';border='#e53935';tc='#ef9a9a';}
    else if(k>=s&&k<s+m){bg='#2a1f00';border='#ffd740';tc='#ffd740';}
    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),ty,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(startX+k*(bw+gap),ty,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(T[k],startX+k*(bw+gap)+bw/2,ty+bh/2);
  }

  // hash bar under window
  const barY=ty+bh+8;
  const barX=startX+s*(bw+gap);
  const barW=m*(bw+gap)-gap;
  const isMatch=rks.th===rks.ph;
  ctx.fillStyle=isMatch?(T.slice(s,s+m)===P?'rgba(105,240,174,0.15)':'rgba(229,57,53,0.15)'):'rgba(92,107,192,0.1)';
  ctx.fillRect(barX,barY,barW,18);
  ctx.strokeStyle=isMatch?(T.slice(s,s+m)===P?'#69f0ae':'#e53935'):'#5c6bc0';
  ctx.lineWidth=1;ctx.strokeRect(barX,barY,barW,18);
  ctx.fillStyle=isMatch?(T.slice(s,s+m)===P?'#69f0ae':'#ef9a9a'):'#7986cb';
  ctx.font=`13px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText(`h=${rks.th}`,barX+barW/2,barY+9);
}

window.rkRestart=function(){
  if(rkTimer){clearInterval(rkTimer);rkTimer=null;document.getElementById('rk-auto-btn').textContent='⏩ 자동';}
  const T=document.getElementById('rk-T').value||'2359031415267399';
  const P=document.getElementById('rk-P').value||'31415';
  if(P.length>T.length)return;
  const m=P.length;
  let hh=1;for(let i=0;i<m-1;i++)hh=(hh*RD)%RQ;
  const ph=hashStr(P,m);
  const th=hashStr(T,m);
  rks={T,P,m,ph,th,hh,s:0,found:[],spurious:[],done:false};
  document.getElementById('rk-steps').textContent='0';
  document.getElementById('rk-hit').textContent='0';
  document.getElementById('rk-found').textContent='-';
  updateRkInfo();drawRk();
};

function updateRkInfo(){
  if(!rks)return;
  const {T,P,s,m,ph,th}=rks;
  const cur=T.slice(s,s+m);
  const hashMatch=th===ph;
  const realMatch=cur===P;
  let status=hashMatch?(realMatch?`<span style="color:#69f0ae">해시일치 + 실제일치 ✓</span>`:`<span style="color:#ef9a9a">해시일치 but 실제불일치 (Spurious Hit!)</span>`):`<span style="color:#7986cb">해시불일치 → 스킵</span>`;
  document.getElementById('rk-hash-line').innerHTML=
    `P hash("${P}") mod ${RQ} = <span style="color:#ffd740">${ph}</span><br>`+
    `T[${s}..${s+m-1}]="${cur}" hash = <span style="color:#ffd740">${th}</span> &nbsp; ${status}`;
}

window.rkStep=function(){
  if(!rks||rks.done)return;
  const {T,P,m,ph,hh}=rks;
  const n=T.length,s=rks.s;
  if(rks.th===ph){
    document.getElementById('rk-hit').textContent=parseInt(document.getElementById('rk-hit').textContent)+1;
    if(T.slice(s,s+m)===P){rks.found.push(s);document.getElementById('rk-found').textContent=rks.found.join(', ');}
    else rks.spurious.push(s);
  }
  if(s+1>n-m){rks.done=true;updateRkInfo();drawRk();return;}
  rks.th=((RD*(rks.th-(parseInt(T[s])*hh%RQ)+RQ)+parseInt(T[s+m]))%RQ+RQ)%RQ;
  rks.s++;
  document.getElementById('rk-steps').textContent=rks.s;
  updateRkInfo();drawRk();
};

window.rkAuto=function(){
  if(rkTimer){clearInterval(rkTimer);rkTimer=null;document.getElementById('rk-auto-btn').textContent='⏩ 자동';return;}
  if(!rks)rkRestart();
  document.getElementById('rk-auto-btn').textContent='⏸ 정지';
  rkTimer=setInterval(()=>{if(!rks||rks.done){clearInterval(rkTimer);rkTimer=null;document.getElementById('rk-auto-btn').textContent='⏩ 자동';return;}rkStep();},350);
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

$$p = n - \pi[n-1], \quad k = \begin{cases} n/p & n \bmod p = 0 \\ 1 & \text{otherwise} \end{cases}$$

$\pi[n-1]$ 은 겹치는 길이, $p = n - \pi[n-1]$ 이 겹치지 않는 최소 반복 단위다.

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

두 번 이상 등장하는 부분 문자열 중 가장 긴 것의 길이 $L$ 을 구하라.

**핵심 관찰:** 길이 $L$ 인 반복이 있으면 길이 $L-1$ 인 반복도 반드시 있다 → **이진탐색 가능**.

`check(L)` = "길이 $L$ 인 중복 부분문자열이 존재하냐?" 를 Rolling Hash로 $O(n)$ 에 구현.

**전체 복잡도:** $O(n \log n)$

{{< rawhtml >}}
<div style="margin:1.5rem 0;background:#0f1117;border-radius:12px;padding:16px;box-shadow:0 4px 24px rgba(0,0,0,.18);">
<div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
  <input id="bs-S" value="banana" maxlength="14" style="background:#1a1d27;border:1px solid #2a2d3a;border-radius:6px;padding:6px 10px;color:#e0e0e0;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:14px;width:160px;" placeholder="String S">
  <button onclick="bsRestart()" style="padding:6px 16px;border:none;border-radius:6px;background:#5c6bc0;cursor:pointer;font-size:13px;color:#fff;font-weight:600;" onmouseover="this.style.background='#7986cb'" onmouseout="this.style.background='#5c6bc0'">시작</button>
  <button onclick="bsStep()" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">▶ 다음</button>
  <button onclick="bsAuto()" id="bs-auto-btn" style="padding:6px 16px;border:none;border-radius:6px;background:#2a2d3a;cursor:pointer;font-size:13px;color:#b0b8d0;" onmouseover="this.style.background='#3a3f50'" onmouseout="this.style.background='#2a2d3a'">⏩ 자동</button>
</div>
<canvas id="bs-canvas" style="width:100%;border-radius:8px;background:#1a1d27;display:block;"></canvas>
<div style="display:flex;gap:10px;margin-top:10px;">
  <div style="flex:1;background:#1a1d27;border-left:3px solid #5c6bc0;border-radius:6px;padding:10px 14px;">
    <div id="bs-info" style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:16px;color:#b0b8d0;line-height:1.6;">시작 버튼을 누르세요.</div>
  </div>
  <div style="min-width:140px;background:#1a1d27;border-left:3px solid #37474f;border-radius:6px;padding:10px 14px;font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:15px;color:#b0b8d0;">
    <div style="font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#5c6bc0;margin-bottom:6px;">Binary Search</div>
    <div>left: <span id="bs-left" style="color:#90caf9;">-</span></div>
    <div>right: <span id="bs-right" style="color:#90caf9;">-</span></div>
    <div>mid: <span id="bs-mid" style="color:#ffd740;">-</span></div>
    <div>답: <span id="bs-ans" style="color:#69f0ae;">-</span></div>
  </div>
</div>
<p style="font-size:13px;color:#778;margin-top:8px;letter-spacing:.04em;text-transform:uppercase;">green = true (duplicate exists) · red = false · amber = current mid</p>
</div>
<script>
(function(){
const cv=document.getElementById('bs-canvas');
const ctx=cv.getContext('2d');
let W=560,H=160,dpr=1;
cv.style.aspectRatio='560/160';
function resize(){dpr=window.devicePixelRatio||1;const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);if(bss)drawBs();}
new ResizeObserver(resize).observe(cv);

let bss=null,bsTimer=null;
const MONO="'JetBrains Mono','Fira Code','Courier New',monospace";
const RD=256,RQ=1000003;

function hasDup(s,L){
  if(L===0)return true;
  const n=s.length;if(L>n)return false;
  let h=1;for(let i=0;i<L-1;i++)h=(h*RD)%RQ;
  let t=0;for(let i=0;i<L;i++)t=(RD*t+s.charCodeAt(i))%RQ;
  const seen=new Map();seen.set(t,[0]);
  for(let i=1;i<=n-L;i++){
    t=((RD*(t-s.charCodeAt(i-1)*h%RQ+RQ)+s.charCodeAt(i+L-1))%RQ+RQ)%RQ;
    if(seen.has(t)){for(const p of seen.get(t)){if(s.slice(p,p+L)===s.slice(i,i+L))return true;}seen.get(t).push(i);}
    else seen.set(t,[i]);
  }
  return false;
}

function buildSteps(s){
  const n=s.length;
  const steps=[];
  let left=0,right=n,ans=0;
  steps.push({left,right,mid:null,result:null,ans,msg:`이진탐색 시작: left=${left}, right=${right}`});
  while(left<=right){
    const mid=Math.floor((left+right)/2);
    const res=hasDup(s,mid);
    steps.push({left,right,mid,result:res,ans,msg:`check(${mid}) = ${res} → ${res?`left=${mid+1}`:`right=${mid-1}`}`});
    if(res){ans=mid;left=mid+1;}
    else right=mid-1;
  }
  steps.push({left,right,mid:null,result:null,ans,msg:`완료! 최장 반복 부분문자열 길이 = ${ans}`});
  return steps;
}

function drawBs(){
  if(!bss)return;
  ctx.clearRect(0,0,W,H);
  const {s,steps,idx}=bss;
  const n=s.length;
  const st=steps[idx];
  const bw=Math.min(Math.floor((W-60)/(n+1)),54);
  const bh=Math.max(42,Math.round(H*0.26));
  const gap=4;
  const startX=(W-(n+1)*(bw+gap))/2;
  const ty=18;
  const fs=Math.round(bh*0.43);

  // draw length boxes 0..n
  for(let L=0;L<=n;L++){
    let bg='#1e2130',border='#2a2d3a',tc='#8090a0';
    if(st.mid===L){bg='#2a1f00';border='#ffd740';tc='#ffd740';}
    else if(L<=bss.answers[idx]){bg='#1b3a1f';border='#43a047';tc='#69f0ae';}
    else if(st.result===false&&st.mid!==null&&L>st.mid){bg='#1e2130';border='#2a2d3a';tc='#37474f';}

    ctx.fillStyle=bg;ctx.beginPath();ctx.roundRect(startX+L*(bw+gap),ty,bw,bh,4);ctx.fill();
    ctx.strokeStyle=border;ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(startX+L*(bw+gap),ty,bw,bh,4);ctx.stroke();
    ctx.fillStyle=tc;ctx.font=`bold ${fs}px ${MONO}`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(L,startX+L*(bw+gap)+bw/2,ty+bh/2);
  }

  // left/right arrows
  if(st.left!==null&&st.left<=n){
    const lx=startX+st.left*(bw+gap);
    ctx.fillStyle='#90caf9';ctx.font=`13px sans-serif`;ctx.textAlign='center';ctx.textBaseline='top';
    ctx.fillText('L',lx+bw/2,ty+bh+4);
  }
  if(st.right!==null&&st.right>=0&&st.right<=n){
    const rx=startX+st.right*(bw+gap);
    ctx.fillStyle='#90caf9';ctx.font=`13px sans-serif`;ctx.textAlign='center';ctx.textBaseline='top';
    ctx.fillText('R',rx+bw/2,ty+bh+4);
  }
  if(st.mid!==null){
    const mx=startX+st.mid*(bw+gap);
    ctx.fillStyle='#ffd740';ctx.font=`13px sans-serif`;ctx.textAlign='center';ctx.textBaseline='top';
    ctx.fillText('M',mx+bw/2,ty+bh+18);
  }
}

window.bsRestart=function(){
  if(bsTimer){clearInterval(bsTimer);bsTimer=null;document.getElementById('bs-auto-btn').textContent='⏩ 자동';}
  const s=document.getElementById('bs-S').value||'banana';
  const steps=buildSteps(s);
  // precompute cumulative answers
  const answers=new Array(steps.length).fill(0);
  let maxAns=0;
  steps.forEach((st,i)=>{if(st.ans>maxAns)maxAns=st.ans;answers[i]=maxAns;});
  bss={s,steps,idx:0,answers};
  document.getElementById('bs-left').textContent='0';
  document.getElementById('bs-right').textContent=s.length;
  document.getElementById('bs-mid').textContent='-';
  document.getElementById('bs-ans').textContent='-';
  document.getElementById('bs-info').textContent=steps[0].msg;
  drawBs();
};
window.bsStep=function(){
  if(!bss||bss.idx>=bss.steps.length-1)return;
  bss.idx++;
  const st=bss.steps[bss.idx];
  document.getElementById('bs-info').textContent=st.msg;
  document.getElementById('bs-left').textContent=st.left;
  document.getElementById('bs-right').textContent=st.right;
  document.getElementById('bs-mid').textContent=st.mid??'-';
  document.getElementById('bs-ans').textContent=st.ans||'-';
  drawBs();
};
window.bsAuto=function(){
  if(bsTimer){clearInterval(bsTimer);bsTimer=null;document.getElementById('bs-auto-btn').textContent='⏩ 자동';return;}
  if(!bss)bsRestart();
  document.getElementById('bs-auto-btn').textContent='⏸ 정지';
  bsTimer=setInterval(()=>{if(!bss||bss.idx>=bss.steps.length-1){clearInterval(bsTimer);bsTimer=null;document.getElementById('bs-auto-btn').textContent='⏩ 자동';return;}bsStep();},600);
};
bsRestart();
})();
</script>
{{< /rawhtml >}}

---

## 7. 알고리즘 비교

| 알고리즘 | 시간복잡도 | 특징 |
|---|---|---|
| Naïve | $O(nm)$ | 단순, 최악 케이스에 매우 느림 |
| KMP | $O(n+m)$ | 항상 보장, $i$ 절대 뒤로 안 감 |
| Rabin-Karp | $O(n+m)$ expected | 여러 패턴 동시 검색에 유리 |

KMP와 Rabin-Karp 모두 $O(n+m)$ 이지만 접근이 다르다.

- **KMP**: $\pi$ 함수로 불일치 시 얼마나 건너뛸지 결정. 결정론적.
- **Rabin-Karp**: 해시로 빠르게 걸러내고 일치 시에만 검증. 확률론적.