"""Figures for Kukie Serving.06 (kukie-counter). python3 figs.py <blog-repo> -> writes figs.json"""
import json, sys
sys.path.insert(0, sys.argv[1] + "/.claude/skills/blog-figures")
from svgkit import Fig, BLUE, ORANGE, GREEN, PURPLE, GRAY, RED, SEC, C, BG, MONO, esc

A = {
    "s3": "3-baseline-limit--측정-기준선에서-정하는-한도",
    "s4": "4-stream-timing--카운터가-재는-ttft-와-itl",
    "s5": "5-adaptive-limit--꼬리-지연-되먹임-한도",
    "s6": "6-brake--대기-수와-kv-사용률-기준-거절",
    "s7": "7-load-test--kukie-gpu-실측",
    "s8": "8-review--리뷰에서-고친-것",
    "s9": "9-limits--확인-못-한-것과-남은-일",
}
OUT = {}


def wrap(html):
    return html.replace('<div style="overflow-x:auto;margin:1.4rem 0;">',
                        '<div style="overflow-x:auto;margin:1.4rem auto;">', 1)


def nc(f, cx, cy, n, color):
    f.plain_badge(cx, cy, n, color)


def codepanel(f, x, y, w, title, rows, lh=15, top=30):
    """rows: (indent, text, num, color). Returns bottom y."""
    h = top + lh * len(rows) + 10
    f.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{SEC}" fill-opacity="0.05" stroke="{SEC}" stroke-width="1.2"/>')
    f.text(x + 12, y + 18, title, 8.6, weight="600", mono=True, opacity="0.85")
    yy = y + top
    for ind, s, n, col in rows:
        if n:
            f.raw(f'<rect x="{x+24}" y="{yy-3}" width="{w-30}" height="{lh}" rx="3" fill="{col}" fill-opacity="0.1"/>')
            nc(f, x + 13, yy + 4.5, n, col)
        f.text(x + 30 + ind * 14, yy + 8, s, 7.8, mono=True, pre=True)
        yy += lh
    return y + h


def numbox(f, x, y, w, h, n, color, title, lines):
    f.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{color}" fill-opacity="0.08" stroke="{color}" stroke-width="1.2"/>')
    nc(f, x + 14, y + 14, n, color)
    f.text(x + 28, y + 18, title, 10, color, weight="600")
    yy = y + 34
    for ln in lines:
        mono = ln.startswith("`")
        f.text(x + 12, yy, ln[1:] if mono else ln, 7.8 if mono else 8.5, mono=mono, pre=mono)
        yy += 14


# ------------------------------------------------------------------ 1. Overview
def overview():
    f = Fig("s6ov", 760, 458, "카운터 한 Pod 안의 요청 경로(키 확인, 자리 얻기, 전달과 재기)와 한도를 정하는 세 루프(기준선 읽기 30초, 조절기 5초, 브레이크 2초), 그리고 쿠버네티스 API 와 GPU 노드의 vLLM")
    f.comp(16, 24, 118, 56, BLUE, "클라이언트", lines=["OpenAI 호환 요청", "`stream: true"])
    f.comp(16, 100, 118, 56, GRAY, "앞단 경로", lines=["게이트웨이·커넥터", "Serving.07"], dashed=True)
    f.arrow("M75,82 L75,98", BLUE)
    f.area(148, 16, 596, 398, "kukie-gpu 클러스터", pill=("EKS", GRAY))
    f.area(158, 44, 386, 270, "일반 노드", pill=("t3.large", GRAY))
    f.group(168, 70, 366, 234, "Pod kukie-counter · ns kukie-gpu")
    # request path
    f.comp(178, 92, 100, 64, BLUE, "키 확인", lines=["키 해시 대조", "틀리면 401"])
    f.comp(300, 92, 100, 64, BLUE, "자리 얻기", lines=["브레이크면 429", "한도 찼으면 429"])
    f.comp(422, 92, 102, 64, BLUE, "전달·재기", lines=["SSE 그대로 전달", "TTFT·ITL 기록"])
    f.arrow("M136,128 L176,128", BLUE)
    f.arrow("M280,124 L298,124", BLUE)
    f.arrow("M402,124 L420,124", BLUE)
    f.badge(510, 104, 2, BLUE, A["s4"], "스톱워치")
    # loops
    f.comp(178, 200, 100, 64, ORANGE, "기준선 읽기", lines=["30초마다 list", "시작값을 정함"])
    f.comp(300, 200, 100, 64, ORANGE, "조절기", lines=["5초마다 판단", "+1 또는 ×0.7"])
    f.comp(422, 200, 102, 64, ORANGE, "브레이크", lines=["2초마다 읽기", "대기·KV 확인"])
    f.badge(264, 212, 1, ORANGE, A["s3"], "기준선 한도")
    f.badge(386, 212, 3, ORANGE, A["s5"], "적응형 한도")
    f.badge(510, 212, 4, ORANGE, A["s6"], "브레이크")
    f.arrow("M228,198 L228,178 L330,178 L330,158", ORANGE, dashed=True)
    f.arrow("M350,198 L350,158", ORANGE, dashed=True)
    f.arrow("M473,198 L473,178 L370,178 L370,158", ORANGE, dashed=True)
    f.text(279, 173, "시작값", 8, ORANGE, "middle")
    f.text(355, 191, "한도", 8, ORANGE)
    f.text(422, 173, "브레이크", 8, ORANGE, "middle")
    f.text(300, 290, "한도와 브레이크는 모델 서버마다 limiter 하나에 모인다", 8, opacity="0.8")
    # API
    f.comp(158, 326, 386, 76, GRAY, "쿠버네티스 API", "AWS 가 관리",
           lines=["ServedModel gpt-oss-20b · ns llm", "`status.baseline.maxConcurrency: 16", "오븐이 측정을 마치고 적는다"])
    f.arrow("M228,266 L228,322", GRAY, dashed=True)
    f.text(234, 290, "list", 8, GRAY)
    # GPU node
    f.area(556, 44, 176, 270, "GPU 노드", pill=("g6e.xlarge", GREEN))
    f.group(566, 70, 156, 234, "Pod vLLM · ns llm")
    f.comp(576, 92, 136, 172, GREEN, "vLLM", "v0.32.0", rpad=32,
           lines=["gpt-oss-20b, L40S 1장", None, "`/v1/completions", "응답 스트림(SSE)", None, "`/metrics", "대기 수, KV 사용률"])
    f.badge(698, 104, 5, GREEN, A["s7"], "실측")
    f.arrow("M526,146 L574,146", BLUE)
    f.arrow("M526,222 L574,222", ORANGE, dashed=True)
    f.step_strip(424, [("3 기준선 한도", A["s3"]), ("4 스톱워치", A["s4"]), ("5 적응형 한도", A["s5"]),
                       ("6 브레이크", A["s6"]), ("7 실측", A["s7"]), ("8 리뷰", A["s8"]), ("9 한계", A["s9"])])
    f.text(380, 454, "파랑 요청 경로 · 주황 한도를 정하는 루프 · 초록 모델 서버 · 회색 쿠버네티스 · 점선 상자는 Serving.07", 8, anchor="middle", opacity="0.75")
    OUT["ov"] = wrap(f.html(caption="번호와 아래 띠를 누르면 해당 절로 이동한다"))


# ------------------------------------------------------------------ 3.1 Discovery sequence
def discovery():
    f = Fig("s6dc", 760, 336, "ServedModel 을 만들고 측정한 뒤 지울 때 카운터의 30초 list 가 경로와 한도를 바꾸는 순서. 2026-11-10 실측 시각")
    lanes = [(200, "사람·오븐", GRAY), (420, "쿠버네티스 API", GRAY), (630, "kukie-counter", BLUE)]
    for x, t, col in lanes:
        f.raw(f'<rect x="{x-70}" y="14" width="140" height="28" rx="8" fill="{col}" fill-opacity="0.1" stroke="{col}" stroke-width="1.2"/>')
        f.text(x, 32, t, 10, col, "middle", "600")
        f.line(f"M{x},44 L{x},322")
    f.text(24, 32, "시각(KST)", 9, weight="600")

    def row(y, t):
        f.text(24, y + 3, t, 8.3, mono=True)

    row(66, "16:06:31")
    f.arrow("M204,66 L414,66", GRAY)
    f.text(309, 61, "ServedModel 생성", 8.3, anchor="middle")
    row(96, "30초마다")
    f.arrow("M626,96 L426,96", BLUE, dashed=True)
    f.text(526, 91, "GET …/servedmodels (list)", 8, anchor="middle", mono=True)
    f.arrow("M426,112 L622,112", GRAY, dashed=True)
    f.text(526, 107, "목록 전체", 8, anchor="middle")
    row(140, "16:06:33")
    f.note(630, 140, "경로 생김 · 한도 4 · no_baseline", BLUE, 200)
    row(184, "16:21:08")
    f.note(200, 184, "측정 끝 · 동시 16 통과", GRAY, 150)
    f.arrow("M204,206 L414,206", GRAY)
    f.text(309, 201, "status.baseline 적기", 8.3, anchor="middle", mono=True)
    row(236, "16:21:33")
    f.arrow("M626,236 L426,236", BLUE, dashed=True)
    f.text(526, 231, "list", 8, anchor="middle")
    f.note(630, 260, "한도 12 = floor(16 × 0.8)", BLUE, 200)
    f.note(630, 282, "baseline / measured", BLUE, 200)
    row(306, "16:22:33")
    f.note(630, 306, "삭제 뒤 list · 경로 빠짐, 새 요청 404", BLUE, 220)
    OUT["dc"] = wrap(f.html(caption="카운터는 watch 없이 30초마다 목록 전체를 다시 읽는다. 기준선이 바뀐 지 25초 뒤 한도가 12 가 됐다"))


# ------------------------------------------------------------------ 3.2 probe chart
def probe():
    f = Fig("s6pb", 760, 360, "동시 8 부터 40 까지의 ITL p95 막대와 SLA 50ms 선. 24 까지 통과, 28 부터 실패. 아래 줄은 vLLM 대기 최대값과 대기가 0 보다 컸던 표본 비율")
    conc = [8, 12, 16, 20, 24, 28, 32, 40]
    itl = [13.6, 15.6, 17.7, 17.4, 30.1, 51.6, 88.7, 92.9]
    wmax = [0, 6, 2, 10, 12, 20, 17, 30]
    wpct = ["0%", "1%", "1%", "1%", "1%", "2%", "3%", "3%"]
    x0, step, base, k = 150, 74, 214, 1.8
    f.text(24, 28, "ITL p95 (ms)", 9, weight="600")
    for v in (0, 25, 50, 75, 100):
        y = base - v * k
        f.line(f"M{x0-20},{y} L{x0+step*7+40},{y}", SEC, True, 0.6)
        f.text(x0 - 26, y + 3, str(v), 8, anchor="end", opacity="0.7")
    ysla = base - 50 * k
    f.raw(f'<path d="M{x0-20},{ysla} L{x0+step*7+40},{ysla}" stroke="{RED}" stroke-width="1.3" stroke-dasharray="6 4"/>')
    f.text(x0 + step * 7 + 44, ysla + 3, "SLA 50", 8.3, RED)
    for i, (c, v) in enumerate(zip(conc, itl)):
        cx = x0 + i * step
        col = GREEN if v <= 50 else RED
        h = v * k
        f.raw(f'<rect x="{cx-17}" y="{base-h}" width="34" height="{h}" rx="3" fill="{col}" fill-opacity="0.25" stroke="{col}" stroke-width="1.1"/>')
        f.text(cx, base - h - 5, f"{v}", 8.3, anchor="middle", weight="600")
        f.text(cx, base + 14, str(c), 9, anchor="middle", weight="600")
    f.text(x0 - 26, base + 14, "동시", 8.3, anchor="end")
    # markers
    def mark(i, label, col, y):
        cx = x0 + i * step
        f.raw(f'<path d="M{cx},{base+22} L{cx},{y-12}" stroke="{col}" stroke-width="1"/>')
        f.pill(cx - 70, y - 12, 140, label, col)
    mark(2, "2배 단계 측정의 결과 16", GRAY, 254)
    mark(4, "촘촘히 잰 한계 24", GREEN, 254)
    f.pill(x0 + 2 * step - 70 - 0, 280 - 4, 140, "× 0.8 → 한도 12", ORANGE)
    # waiting rows
    f.text(x0 - 26, 314, "대기 최대", 8.3, anchor="end")
    f.text(x0 - 26, 334, "대기>0 표본", 8.3, anchor="end")
    for i, (w, p) in enumerate(zip(wmax, wpct)):
        cx = x0 + i * step
        f.chip(cx - 24, 302, 48, 18, ORANGE, str(w), center=True)
        f.chip(cx - 24, 324, 48, 18, GRAY, p, center=True)
    OUT["pb"] = wrap(f.html(caption="2026-11-10 탐침. 대기는 단계 시작의 몰림 순간에만 생기고, 꾸준한 부하에서는 동시 40 까지 0 이었다"))


# ------------------------------------------------------------------ 4. Stream timing
def stream():
    f = Fig("s6st", 760, 470, "스트림 하나에서 모델을 기다린 시간과 클라이언트에 쓴 시간을 나누어 TTFT 와 토큰 간격을 재는 방식, 그리고 그 일을 하는 streamTimer 코드")
    L0 = 170
    f.text(24, 70, "모델을 기다림", 9, GREEN, weight="600")
    f.text(24, 82, "(읽기 안)", 8, opacity="0.7")
    f.text(24, 108, "클라이언트에 씀", 9, GRAY, weight="600")
    f.text(24, 120, "(읽기 밖)", 8, opacity="0.7")
    waits = [(170, 300), (310, 330), (338, 358), (420, 440), (448, 470), (478, 498), (506, 526)]
    writes = [(300, 310), (330, 338), (358, 420), (440, 448), (470, 478), (498, 506)]
    for a, b in waits:
        f.raw(f'<rect x="{a}" y="64" width="{b-a}" height="22" rx="3" fill="{GREEN}" fill-opacity="0.22" stroke="{GREEN}" stroke-width="1"/>')
    for a, b in writes:
        f.raw(f'<rect x="{a}" y="102" width="{b-a}" height="22" rx="3" fill="{GRAY}" fill-opacity="0.18" stroke="{GRAY}" stroke-width="1"/>')
    f.text(235, 79, "프리필", 8.3, anchor="middle")
    f.text(389, 117, "느린 클라이언트", 8, anchor="middle")
    f.text(560, 79, "…", 10, anchor="middle")
    # read ends (chunks)
    def chunk(x, kind):
        if kind == "role":
            f.raw(f'<circle cx="{x}" cy="54" r="4.5" fill="{BG}" stroke="{GRAY}" stroke-width="1.4"/>')
        else:
            f.raw(f'<circle cx="{x}" cy="54" r="4.5" fill="{BLUE}"/>')
    chunk(300, "role")
    chunk(330, "text")
    chunk(358, "text")
    chunk(440, "text")
    chunk(464, "text"); chunk(474, "text")
    chunk(498, "text"); chunk(526, "text")
    f.raw(f'<path d="M{L0},40 L{L0},136" stroke="{C}" stroke-width="1"/>')
    f.text(L0, 36, "전달 시작", 8, anchor="middle")
    # brackets
    f.raw(f'<path d="M170,146 L170,152 L330,152 L330,146" fill="none" stroke="{BLUE}" stroke-width="1.2"/>')
    f.text(250, 166, "TTFT = 시작부터 첫 글 조각까지 − 쓴 시간", 8.3, anchor="middle")
    f.raw(f'<path d="M358,146 L358,152 L440,152 L440,146" fill="none" stroke="{BLUE}" stroke-width="1.2"/>')
    f.text(399, 166, "간격 = 기다린 시간만", 8.3, anchor="middle")
    f.raw(f'<path d="M640,48 L700,48" stroke="none"/>')
    f.raw(f'<circle cx="600" cy="62" r="4.5" fill="{BG}" stroke="{GRAY}" stroke-width="1.4"/>')
    f.text(610, 65, "역할만 든 조각", 8.3)
    f.raw(f'<circle cx="600" cy="80" r="4.5" fill="{BLUE}"/>')
    f.text(610, 83, "글이 든 조각", 8.3)
    f.text(592, 104, "막대 길이는 설명용", 8, opacity="0.7")
    nc(f, 300, 32, 2, ORANGE)
    nc(f, 389, 140, 1, GRAY)
    nc(f, 236, 186, 3, BLUE)
    nc(f, 469, 32, 4, GREEN)
    f.text(469, 20, "한 읽기에 두 조각", 8, anchor="middle")
    rows = [
        (0, "func (t *streamTimer) beforeRead(now time.Time) {", None, None),
        (1, "if !t.lastReturn.IsZero() {", None, None),
        (2, "t.outside += now.Sub(t.lastReturn)", 1, GRAY),
        (1, "}", None, None),
        (1, "t.lastReturn = now", None, None),
        (0, "}", None, None),
        (0, "func (t *streamTimer) afterRead(now time.Time, p []byte) {", None, None),
        (1, "wait := now.Sub(t.lastReturn)", None, None),
        (1, "t.lastReturn = now", None, None),
        (1, "token := t.scan(p)", 2, ORANGE),
        (1, "switch {", None, None),
        (1, "case !token:", None, None),
        (2, "t.sinceToken += wait", None, None),
        (1, "case t.ttft == 0:", 3, BLUE),
        (2, "t.ttft = max(now.Sub(t.start)-t.outside, time.Nanosecond)", 3, BLUE),
        (1, "default:", 4, GREEN),
        (2, "gap := (t.sinceToken + wait).Seconds()", 4, GREEN),
    ]
    codepanel(f, 16, 200, 440, "counter/adaptive.go (발췌)", rows, lh=15)
    numbox(f, 470, 200, 274, 56, 1, GRAY, "쓴 시간", ["읽기와 읽기 사이는 클라이언트에 쓰는 시간이다", "더해 두었다가 TTFT 에서 뺀다"])
    numbox(f, 470, 262, 274, 56, 2, ORANGE, "글 표지 찾기", ["content, reasoning, arguments, text 가 빈", "문자열이 아닐 때만. 역할 조각은 치지 않는다"])
    numbox(f, 470, 324, 274, 56, 3, BLUE, "첫 토큰", ["처음 글이 든 읽기에서 TTFT 를 정한다", "입력 4,096 토큰 초과 요청은 표본에서 뺀다"])
    numbox(f, 470, 386, 274, 70, 4, GREEN, "토큰 간격", ["글이 든 읽기 사이에 모델을 기다린 시간", "한 읽기에 조각이 여럿이어도 간격 하나", "요청마다 p95 를 구해 창에 넣는다"])
    OUT["st"] = wrap(f.html(caption="카운터는 읽기 안의 시간만 더한다. 느리게 받는 클라이언트가 모델을 느려 보이게 하지 못한다"))


# ------------------------------------------------------------------ 5. Adaptive tick
def adaptive():
    f = Fig("s6ad", 760, 540, "조절기 tick 의 판단 순서 코드와 각 갈래의 뜻. 표본 부족, SLA 초과 시 0.7 배, 80 에서 100 퍼센트 사이 유지, 쿨다운, 덜 참, 1 올리기, 바꾸면 표본 비우기")
    rows = [
        (0, "switch {", None, None),
        (0, "case !enoughITL && !enoughTTFT:", 1, GRAY),
        (1, "d.reason = adaptiveTooFewSamples", None, None),
        (0, "case enoughITL && d.itlP95 > slaITL:", 2, RED),
        (1, "d.reason = adaptiveDecreaseITL", None, None),
        (0, "case enoughTTFT && d.ttftP95 > slaTTFT:", 2, RED),
        (1, "d.reason = adaptiveDecreaseTTFT", None, None),
        (0, "case !enoughITL || d.itlP95 > slaITL*adaptiveHeadroom ||", 3, ORANGE),
        (1, "(enoughTTFT && d.ttftP95 > slaTTFT*adaptiveHeadroom),", 3, ORANGE),
        (1, "!enoughTTFT && slowTTFT >= adaptiveRaiseSlowTTFT:", 3, ORANGE),
        (1, "d.reason = adaptiveHold", None, None),
        (0, "case cooling:", 4, PURPLE),
        (1, "d.reason = adaptiveCooling", None, None),
        (0, "case float64(windowPeak) < adaptiveFill*float64(a.limit):", 5, BLUE),
        (1, "d.reason = adaptiveNotFull", None, None),
        (0, "case a.limit >= cfg.MaxLimit:", None, None),
        (1, "d.reason = adaptiveAtMax", None, None),
        (0, "default:", 6, GREEN),
        (1, "d.reason = adaptiveIncrease", None, None),
        (0, "}", None, None),
        (0, "switch d.reason {", None, None),
        (0, "case adaptiveDecreaseITL, adaptiveDecreaseTTFT:", 2, RED),
        (1, "d.limit = max(1, int(math.Floor(float64(a.limit)*adaptiveDecrease)))", 2, RED),
        (1, "a.cooldown = adaptiveCooldownTicks", 4, PURPLE),
        (0, "case adaptiveIncrease:", 6, GREEN),
        (1, "d.limit = a.limit + 1", 6, GREEN),
        (0, "}", None, None),
        (0, "…", None, None),
        (1, "a.gen++", 7, GRAY),
        (1, "a.samples = a.samples[:0]", 7, GRAY),
    ]
    codepanel(f, 16, 14, 440, "counter/adaptive.go tick (발췌)", rows, lh=16)
    bx, bw = 470, 274
    numbox(f, bx, 14, bw, 52, 1, GRAY, "표본 부족", ["ITL 요청 10개·간격 200개, TTFT 요청 20개 미만", ])
    numbox(f, bx, 80, bw, 52, 2, RED, "SLA 초과 → × 0.7", ["ITL 50ms 또는 TTFT 1초를 넘으면 내린다"])
    numbox(f, bx, 146, bw, 66, 3, ORANGE, "여유 폭 → 그대로", ["둘 중 하나라도 SLA 의 80~100%", "TTFT 표본 20개 미만 중 느린 것 2개 이상(#43)"])
    numbox(f, bx, 226, bw, 52, 4, PURPLE, "쿨다운", ["내린 뒤 3번(15초)은 올리지 않는다"])
    numbox(f, bx, 292, bw, 66, 5, BLUE, "덜 참 → 그대로", ["30초 창의 최고 처리 중 수가 한도의 90% 미만", "손님이 적을 때 근거 없이 오르지 않게"])
    numbox(f, bx, 372, bw, 52, 6, GREEN, "한도 + 1", ["둘 다 SLA 의 80% 안이고 한도까지 찼을 때"])
    numbox(f, bx, 452, bw, 66, 7, GRAY, "한도 세대", ["바꾸면 표본을 비운다. 다음 판단은", "새 한도로 시작한 요청 10개가 끝난 뒤다"])
    OUT["ad"] = wrap(f.html(caption="5초마다 위에서부터 처음 맞는 갈래 하나를 고른다. 내리는 조건이 올리는 조건보다 먼저다"))


# ------------------------------------------------------------------ 6. Brake lanes
def brake():
    f = Fig("s6bk", 760, 330, "2초마다 읽는 vLLM 대기 수로 브레이크가 걸리는 경우와 걸리지 않는 경우 세 가지. 한 번의 몰림, 연속된 대기, 읽기 실패")
    x0, step = 196, 64
    f.text(24, 28, "2초마다 /metrics 읽기", 9, weight="600")
    for i in range(8):
        f.text(x0 + i * step + 23, 28, f"{i*2}초", 8, anchor="middle", opacity="0.7")

    def lane(y, title, sub, cells, band, result, rcol):
        f.text(24, y + 14, title, 9.5, weight="600")
        f.text(24, y + 28, sub, 8, opacity="0.75")
        if band:
            a, b = band
            f.raw(f'<rect x="{x0 + a*step - 6}" y="{y-6}" width="{(b-a)*step + 58}" height="36" rx="6" fill="{RED}" fill-opacity="0.08" stroke="{RED}" stroke-width="1" stroke-dasharray="4 3"/>')
            f.text(x0 + a*step - 2, y - 10, "브레이크 waiting · 새 요청 429", 8, RED, weight="600")
        for i, (s, kind) in enumerate(cells):
            x = x0 + i * step
            col = {"0": GRAY, "w": ORANGE, "x": GRAY}[kind]
            f.chip(x, y, 46, 24, col, s, gone=(kind == "x"), center=True)
        f.text(x0, y + 44, result, 8.5, rcol)

    lane(48, "동시 40 시작 몰림", "1차 실측",
         [("대기 7", "w"), ("0", "0"), ("0", "0"), ("0", "0"), ("0", "0"), ("0", "0"), ("0", "0"), ("0", "0")],
         None, "연속 1번에서 끊김 → 걸리지 않음. 몰림 순간은 막지 않는다", GREEN)
    lane(132, "9,000단어 입력", "2차 실측",
         [("0", "0"), ("대기", "w"), ("대기 14", "w"), ("대기", "w"), ("대기", "w"), ("대기", "w"), ("0", "0"), ("0", "0")],
         (2, 5), "2번 연속에서 걸림 → 새 요청 429, 0 이 보인 읽기에서 바로 풂. 두 번에 거절 74건", RED)
    lane(216, "모델이 뜨기 전", "Service 없음",
         [("실패", "x")] * 8, None, "읽기 실패는 걸지 않는다(걸려 있으면 푼다). 실패 279번을 지표로만 셌다", GREEN)
    f.text(24, 316, "칸의 위치는 조건을 보이는 도식이다. 2차 실측의 첫 브레이크는 약 8초 걸려 있었다", 8, opacity="0.75")
    OUT["bk"] = wrap(f.html(caption="브레이크는 한도를 바꾸지 않는다. 그 순간의 새 요청만 막는다"))


# ------------------------------------------------------------------ 7.1 raise
def raise_chart():
    f = Fig("s6up", 760, 330, "1차 실측에서 한도가 16 에서 21 까지 10초에 1씩 오른 계단과 각 판단 때의 창 ITL. 21 에서 41ms 로 유지")
    def X(t):
        return 120 + (t + 15) * 6.6 if t <= 70 else 690
    def Y(l):
        return 250 - (l - 14) * 17
    f.text(24, 24, "한도", 9, weight="600")
    for l in range(14, 25, 2):
        f.line(f"M110,{Y(l)} L730,{Y(l)}", SEC, True, 0.5)
        f.text(104, Y(l) + 3, str(l), 8, anchor="end", opacity="0.7")
    for t in (0, 10, 20, 30, 40, 50, 60):
        f.text(X(t), 268, f"{t}", 8, anchor="middle", opacity="0.7")
    f.text(696, 268, "≈ 300", 8, anchor="middle", opacity="0.7")
    f.text(420, 284, "부하 시작부터 초", 8.3, anchor="middle")
    # first 10 s band
    f.raw(f'<rect x="{X(0)}" y="{Y(24)}" width="{X(10)-X(0)}" height="{Y(14)-Y(24)}" fill="{RED}" fill-opacity="0.07"/>')
    f.text(X(0) + 4, Y(24) + 12, "첫 10초", 8, RED)
    f.text(X(0) + 4, Y(24) + 24, "TTFT p95", 8, RED)
    f.text(X(0) + 4, Y(24) + 36, "1,025ms", 8, RED, weight="600")
    steps = [(-11, 16), (9, 17), (19, 18), (29, 19), (39, 20), (49, 21)]
    d = ""
    for i, (t, l) in enumerate(steps):
        nx = steps[i + 1][0] if i + 1 < len(steps) else 75
        d += (f"M{X(t)},{Y(l)} " if i == 0 else f"L{X(t)},{Y(l)} ") + f"L{X(nx) if nx <= 70 else 690},{Y(l)} "
    f.raw(f'<path d="{d}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    labels = [(9, 16, "18.2"), (19, 17, "18.4"), (29, 18, "18.2"), (39, 19, "19.1"), (49, 20, "40.0")]
    for t, l, s in labels:
        col = ORANGE if s == "40.0" else C
        f.raw(f'<circle cx="{X(t)}" cy="{Y(l+1)}" r="3" fill="{BLUE}"/>')
        f.text(X(t) - 4, Y(l) + 14, s, 8.3, col, "middle", "600" if col == ORANGE else None)
    f.text(560, Y(21) - 8, "21 에서 4분 넘게 hold · 창 ITL 40.9~41.5ms", 8.5, ORANGE, "middle", "600")
    f.text(130, Y(16) - 8, "start 16", 8.3, BLUE)
    f.text(X(30), Y(14) - 6, "숫자: 판단 때 창 ITL(ms), 직전 한도에서 시작한 요청으로 잰 값", 8, anchor="middle", opacity="0.75")
    f.chip(120, 296, 290, 20, BLUE, "0~50초 · 받음 218 · 429 537 · TTFT p95 217~1,025ms", center=True)
    f.chip(420, 296, 310, 20, GREEN, "50~300초 · 받음 1,264 · 429 2,363 · TTFT p95 215~222ms", center=True)
    OUT["up"] = wrap(f.html(caption="80% 경계(40ms)를 39.985ms 로 겨우 밑돌아 20 에서 한 번 더 올랐다. 21 의 41ms 는 여유 폭 안이라 머물렀다"))


# ------------------------------------------------------------------ 7.2 lower
def lower():
    f = Fig("s6dn", 760, 300, "긴 입력 두 시험에서 판단 차례마다 한도가 내려간 계단. 2,900단어는 23 에서 7 까지 연쇄로 내려간 뒤 6 에서 9 사이를 오가고, 9,000단어는 19 에서 2 까지 내려가도 ITL 122ms")

    def panel(x0, title, sub, seq, notes, extra):
        w, top, bot = 340, 40, 230
        f.raw(f'<rect x="{x0}" y="14" width="{w}" height="250" rx="10" fill="{SEC}" fill-opacity="0.04" stroke="{SEC}" stroke-width="1"/>')
        f.text(x0 + 12, 32, title, 10, weight="600")
        f.text(x0 + w - 12, 32, sub, 8, anchor="end", opacity="0.75")
        def Y(l):
            return bot - l * (bot - top - 10) / 24
        for l in (0, 8, 16, 24):
            f.line(f"M{x0+30},{Y(l)} L{x0+w-12},{Y(l)}", SEC, True, 0.5)
            f.text(x0 + 24, Y(l) + 3, str(l), 8, anchor="end", opacity="0.7")
        n = len(seq)
        sx = (w - 60) / max(n - 1, 1)
        pts = [(x0 + 44 + i * sx, Y(l)) for i, l in enumerate(seq)]
        d = f"M{pts[0][0]},{pts[0][1]}"
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            d += f" L{bx},{ay} L{bx},{by}"
        f.raw(f'<path d="{d}" fill="none" stroke="{BLUE}" stroke-width="1.8"/>')
        for i, ((px, py), l) in enumerate(zip(pts, seq)):
            col = BLUE if i == 0 else (RED if l < seq[i - 1] else GREEN)
            f.raw(f'<circle cx="{px}" cy="{py}" r="3.5" fill="{col}"/>')
            f.text(px + 7, py - 5, str(l), 8.5, col, "start", "600")
        for i, s, col in notes:
            px, py = pts[i]
            if i == len(seq) - 1:
                f.text(px - 7, py + 14, s, 8, col, "end")
            else:
                f.text(px + 7, py + 14, s, 8, col, "start")
        f.text(x0 + 12, 254, extra, 8.3, opacity="0.85")

    panel(24, "2,900단어 (약 3,700토큰)", "클라이언트 40", [23, 16, 11, 7, 8, 9, 6],
          [(0, "ITL 87~102", RED), (3, "ITL 17", GREEN), (5, "ITL 55", RED)],
          "그 뒤 6~9 를 오감. 내리기는 10초 간격")
    panel(396, "9,000단어 (약 1만 1천 토큰)", "클라이언트 40", [19, 13, 9, 6, 4, 2],
          [(5, "ITL 122", RED)],
          "브레이크 waiting 두 번, 거절 74 · KV 최대 16%")
    f.text(380, 288, "가로축은 판단 차례 · 빨강 점 내림 · 초록 점 올림", 8, anchor="middle", opacity="0.75")
    OUT["dn"] = wrap(f.html(caption="내린 뒤의 새 표본도 앞 한도로 들어온 긴 요청과 GPU 를 같이 써서 한 번 더 내렸다(DURO-237)"))


# ------------------------------------------------------------------ 7.3 cliff
def cliff():
    f = Fig("s6cl", 760, 320, "vLLM 에 직접 보낸 동시 16 부터 25 의 ITL 은 18.3 에서 21.0ms 로 완만하다. 카운터를 거친 한도 23 에서는 ITL 이 40.5 에서 41.3ms 지만 간격 평균은 19.3 에서 20.2ms 다")
    base, k = 230, 3.2
    def Y(v):
        return base - v * k
    f.text(24, 24, "ITL (ms)", 9, weight="600")
    for v in (0, 20, 40, 60):
        f.line(f"M70,{Y(v)} L740,{Y(v)}", SEC, True, 0.5)
        f.text(64, Y(v) + 3, str(v), 8, anchor="end", opacity="0.7")
    f.raw(f'<path d="M70,{Y(50)} L740,{Y(50)}" stroke="{RED}" stroke-width="1.2" stroke-dasharray="6 4"/>')
    f.text(736, Y(50) - 4, "SLA 50", 8, RED, "end")
    f.text(736, Y(40) - 4, "80% 40", 8, ORANGE, "end")
    f.raw(f'<path d="M70,{Y(40)} L740,{Y(40)}" stroke="{ORANGE}" stroke-width="1" stroke-dasharray="2 3"/>')
    conc = [16, 17, 18, 19, 20, 21, 22, 24, 25]
    itl = [18.3, 18.1, 18.5, 18.8, 19.2, 19.4, 19.5, 21.0, 21.0]
    x0, step = 96, 40
    f.raw(f'<rect x="{x0-22}" y="34" width="{step*9+4}" height="{base+36-34}" rx="8" fill="{GREEN}" fill-opacity="0.04" stroke="{GREEN}" stroke-width="1" stroke-dasharray="4 3"/>')
    f.text(x0 - 14, 48, "vLLM 에 직접 · 동시 수 고정, 단계마다 40초", 8.5, GREEN, weight="600")
    for i, (c, v) in enumerate(zip(conc, itl)):
        cx = x0 + i * step
        f.raw(f'<rect x="{cx-13}" y="{Y(v)}" width="26" height="{v*k}" rx="3" fill="{GREEN}" fill-opacity="0.25" stroke="{GREEN}" stroke-width="1"/>')
        f.text(cx, Y(v) - 4, f"{v}", 7.8, anchor="middle")
        f.text(cx, base + 14, str(c), 8.5, anchor="middle", weight="600")
    f.text(x0 + 4 * step, base + 28, "vLLM 실행 수", 8, anchor="middle", opacity="0.75")
    x1 = 470
    f.raw(f'<rect x="{x1-14}" y="34" width="284" height="{base+36-34}" rx="8" fill="{BLUE}" fill-opacity="0.04" stroke="{BLUE}" stroke-width="1" stroke-dasharray="4 3"/>')
    f.text(x1 - 6, 48, "카운터 경유 · 클라이언트 40", 8.5, BLUE, weight="600")

    def rng(cx, lo, hi, col, top, sub):
        f.raw(f'<rect x="{cx-26}" y="{Y(hi)}" width="52" height="{max((hi-lo)*k,3)}" rx="2" fill="{col}" fill-opacity="0.35" stroke="{col}" stroke-width="1"/>')
        f.raw(f'<rect x="{cx-26}" y="{Y(lo)}" width="52" height="{lo*k}" rx="2" fill="{col}" fill-opacity="0.1"/>')
        f.text(cx, Y(hi) - 4, f"{lo}~{hi}", 8, anchor="middle", weight="600")
        f.text(cx, base + 14, top, 8.5, anchor="middle", weight="600")
        f.text(cx, base + 28, sub, 8, anchor="middle", opacity="0.75")
    rng(x1 + 34, 18, 23, BLUE, "한도 ≤ 22", "ITL p95 가운데")
    rng(x1 + 128, 40.5, 41.3, ORANGE, "한도 23", "ITL p95 가운데")
    rng(x1 + 222, 19.3, 20.2, GRAY, "한도 23", "간격 평균")
    f.text(380, 300, "2ms 미만 간격(묶여 온 토큰)은 0 · 카운터 노드 CPU 최대 11%", 8.3, anchor="middle", opacity="0.85")
    OUT["cl"] = wrap(f.html(caption="GPU 속도는 그대로이고 일부 간격만 약 20ms 늦게 온다. 늦어지는 곳은 vLLM → 카운터 구간이나 카운터 안으로 본다(DURO-238)"))


for fn in (overview, discovery, probe, stream, adaptive, brake, raise_chart, lower, cliff):
    fn()
json.dump(OUT, open(sys.argv[2], "w"), ensure_ascii=False)
print("ok", list(OUT))
