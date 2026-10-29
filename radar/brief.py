"""일일 이슈 브리핑 A4 1쪽 PDF 생성기 (손그림 서식)

사용:
  python3 radar/brief.py content.json --fonts node_modules --out /tmp/이슈브리핑_20261029.pdf
  (--html 경로를 주면 HTML도 남김, --pdf 없이 HTML만 만들려면 --out 생략)

content.json 구조는 radar/brief_example.json 참고. 디자인(글꼴·색·배치)은 이 파일이 정하고,
브리핑 내용(이슈·동향·과업 반영사항)만 JSON으로 받는다. 글꼴은 npm 패키지에서 읽는다:
  npm install pretendard @fontsource/gaegu @fontsource/jua @fontsource/nanum-brush-script @fontsource/permanent-marker
"""
import argparse
import base64
import html
import json
import os
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from common import DOCS  # noqa: E402

WD = "월화수목금토일"
CATS = ["리스크·쟁점", "정책·예산", "발주처", "유치·개최", "통계·실적", "해외·경쟁국", "지자체·시설"]
COLOR = {"리스크·쟁점": "#D9472B", "정책·예산": "#E3A51C", "발주처": "#E0457B", "유치·개최": "#1D3FA6",
         "통계·실적": "#1A8A4A", "해외·경쟁국": "#7A4BD6", "지자체·시설": "#0AA39A", "산업 동향": "#B07C00", "전시회 개최·참가": "#7B8197"}
TRACK_COLOR = {"MICE 유치": "#D9472B", "전시·컨벤션": "#E3A51C"}

CSS = """
@page{size:A4 portrait;margin:0}
:root{--ink:#2b2f45;--navy:#16193A;--sub:#4a5068;--mute:#7b8197;--rule:#d9dbe6;--wash:#f5f6fa;--cream:#FFF6E5;--yel:#FFC845;--red:#D9472B;--green:#1A8A4A;
--f-body:"Pretendard","Noto Sans KR","Malgun Gothic",sans-serif;--f-title:"Jua","Pretendard",sans-serif;--f-hand:"Gaegu","Pretendard",sans-serif;--f-mark:"Permanent Marker","Jua",cursive;--f-brush:"Nanum Brush Script","Jua",cursive}
*{box-sizing:border-box}html,body{margin:0;padding:0;background:#fff}
body{font-family:var(--f-body);color:var(--ink);font-size:7.4pt;line-height:1.42;word-break:keep-all;overflow-wrap:break-word;print-color-adjust:exact;-webkit-print-color-adjust:exact;font-variant-numeric:tabular-nums}
.wrap{width:210mm;height:297mm;display:flex;flex-direction:column;padding:5.5mm 10mm 5mm;overflow:hidden}.wrap>*{flex:none}
.sk{position:relative}.sk-frame{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible;z-index:0}.sk>*:not(.sk-frame){position:relative;z-index:1}
/* 기관 띠 */
.org{display:flex;justify-content:space-between;align-items:center;gap:4mm;padding:0 1mm 1.8mm}
.org .l{display:flex;align-items:center;gap:3.5mm}.kto{display:block;height:8.4mm;width:25mm;background:url(KTO_URI) left center/contain no-repeat}
.org .vl{width:.3mm;height:8mm;background:#DEDBD9}.org .cap{font-family:var(--f-hand);font-size:9pt;font-weight:700;color:var(--sub);line-height:1.2}.org .cap small{display:block;font-size:7pt;font-weight:400;color:var(--mute)}
.org .r{display:flex;align-items:center;gap:2.5mm;font-family:var(--f-hand);font-size:7.5pt;color:var(--mute)}.sp{display:block;width:22mm;height:5.5mm;background:url(SP_URI) right center/contain no-repeat}
/* 제호 */
.mast{position:relative;background:var(--navy);color:var(--cream);border-radius:4mm 5.5mm 3.5mm 5mm/5mm 3.5mm 5.5mm 4mm;padding:2mm 5mm 4mm;overflow:hidden}
.mast::after{content:"";position:absolute;left:0;right:0;bottom:0;height:3mm;background:repeating-linear-gradient(90deg,rgba(255,246,229,.55) 0 .5mm,transparent .5mm 3mm),repeating-linear-gradient(90deg,rgba(255,200,69,.95) 0 .8mm,transparent .8mm 15mm);background-size:auto 1.8mm,auto 3mm;background-repeat:repeat-x;background-position:0 100%,0 100%}
.m-top{display:flex;justify-content:space-between;align-items:baseline;font-family:var(--f-hand);font-size:8pt;font-weight:700;color:rgba(255,246,229,.85);border-bottom:.4mm dashed rgba(255,246,229,.3);padding-bottom:1.2mm}
.m-kick{font-family:var(--f-mark);font-weight:400;font-size:7.5pt;letter-spacing:.08em;color:var(--yel);display:inline-block;transform:rotate(-1.5deg)}.m-top b{color:var(--cream)}
.m-main{display:flex;align-items:center;justify-content:space-between;gap:4mm;margin-top:1.2mm}
.m-word{display:flex;align-items:center;gap:4mm}
.m-en{position:relative;margin:0;font-family:var(--f-mark);font-weight:400;font-size:26pt;line-height:.95;color:var(--cream);transform:rotate(-2.5deg);padding-bottom:.1em}
.m-en small{font-size:.26em;letter-spacing:.06em;color:var(--yel);writing-mode:vertical-rl;transform:rotate(180deg);display:inline-block;vertical-align:top;margin:.3em .25em 0 0}
.m-scribble{position:absolute;left:4%;bottom:-.02em;width:96%;height:.16em;overflow:visible}
.m-ko{position:relative;transform:rotate(1.5deg);padding-left:3mm}.m-ko::before{content:"";position:absolute;left:0;top:8%;bottom:8%;width:.9mm;border-radius:1mm;background:var(--yel);transform:rotate(-3deg)}
.m-ko b{display:block;font-family:var(--f-brush);font-weight:400;font-size:24pt;line-height:.9;color:var(--cream)}.m-ko span{display:block;font-family:var(--f-hand);font-weight:700;font-size:7.6pt;letter-spacing:.06em;color:var(--yel);margin-top:.6mm}
.m-date{text-align:right}.m-date b{display:block;font-size:14pt;font-weight:800;line-height:1.05;letter-spacing:-.01em}.m-date span{display:block;font-family:var(--f-hand);font-size:8pt;font-weight:700;color:rgba(255,246,229,.85);margin-top:.5mm}
.m-date .no{display:inline-block;font-family:var(--f-title);font-size:8pt;color:var(--navy);background:var(--yel);padding:0 2mm;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;transform:rotate(-2deg);margin-bottom:1mm}
/* 과업·자료원 */
.task{display:flex;justify-content:space-between;align-items:center;gap:3mm;padding:1.4mm 1mm 0;font-family:var(--f-hand)}
.task .t{font-size:8.2pt;font-weight:700}.task .t em{font-style:normal;font-family:var(--f-mark);font-size:7pt;color:var(--red);margin-right:2mm;letter-spacing:.04em}.task .s{font-size:7.2pt;color:var(--mute)}
/* KPI */
.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:2.2mm;margin-top:1.6mm}
.kp{padding:1.6mm 3mm 1.4mm;display:flex;flex-direction:column;gap:.2mm}
.kp .desk{font-family:var(--f-title);font-size:7.6pt;color:var(--sub)}.kp .big{font-size:13.2pt;font-weight:800;line-height:1.15;letter-spacing:-.02em}.kp .big small{font-size:7pt;font-weight:700;margin-left:.5mm}.kp .big .g{color:var(--mute);font-weight:600;font-size:7.6pt;margin-left:1mm}
.kp:first-child .big{color:#D9472B}.kp .what{font-size:6.8pt;color:var(--sub)}.kp .what.red{color:var(--red);font-weight:800}
/* 중요도 분류 */
.cats{display:flex;align-items:center;gap:3.2mm;flex-wrap:wrap;padding:1.6mm 1mm 1.2mm;margin-top:1.8mm;border-top:.3mm dashed var(--rule);border-bottom:.3mm dashed var(--rule);font-family:var(--f-hand);font-size:7.6pt;font-weight:700}
.cats .lab{color:var(--mute);font-weight:400}.cats span i{display:inline-block;width:2mm;height:2mm;border-radius:.5mm;margin-right:1.2mm;vertical-align:-.1mm}
.cats .z{color:var(--mute)}.cats .z i{background:#cfd2dc}.cats b{color:var(--red);font-weight:800;margin-left:.7mm}
/* 섹션 머리 */
.sh{display:flex;align-items:baseline;gap:2.6mm;margin:2.2mm 0 1.3mm}.sh .lbl{font-family:var(--f-mark);font-size:7pt;color:var(--red);letter-spacing:.06em}
.sh h2{margin:0;font-family:var(--f-title);font-weight:400;font-size:12.2pt;line-height:1}.sh .n{margin-left:auto;font-family:var(--f-hand);font-size:7.2pt;color:var(--mute)}
/* 주요 이슈 카드 */
.issues{display:grid;grid-template-columns:1fr 1fr;gap:2.4mm}.card.full{grid-column:1/-1}
.card{padding:2mm 3mm 1.8mm;background:#fff}
.tags{display:flex;align-items:center;gap:1.4mm;flex-wrap:wrap;margin-bottom:1.2mm}
.tag{display:inline-block;font-family:var(--f-title);font-size:6.9pt;line-height:1.35;padding:.2mm 1.8mm;border-radius:.8mm;color:#fff}
.tag.n{font-size:7.6pt;background:var(--navy);padding:.2mm 2mm;border-radius:255px 15px 225px 15px/15px 225px 15px 255px}
.tag.o{background:transparent;color:var(--sub);box-shadow:inset 0 0 0 .3mm var(--rule)}.tag.ok{background:var(--green)}.tag.ng{background:var(--red)}
.card h3{margin:0 0 1mm;font-family:var(--f-title);font-weight:400;font-size:10.5pt;line-height:1.3}.card.half h3{font-size:9.5pt}
.card ul{margin:0;padding:0;list-style:none}.card li{position:relative;padding-left:3mm;font-size:7.2pt;line-height:1.42;margin-bottom:.5mm}
.card li::before{content:"";position:absolute;left:.4mm;top:.95em;width:1.3mm;height:1.3mm;border-radius:.3mm;background:var(--c,var(--ink))}
.card.full ul{columns:2;column-gap:5mm}.card.full li{break-inside:avoid}
.card .src{font-size:6.6pt;color:var(--mute);margin-top:1mm}.card .src b{color:var(--sub)}
.insight{margin-top:1.5mm;padding:1.4mm 2.4mm;background:var(--cream);border-left:.5mm solid var(--yel);font-size:7.1pt;line-height:1.42}.insight b{font-family:var(--f-title);font-weight:400;color:#B07C00;margin-right:1.2mm;font-size:7.6pt}
/* 트랙별 동향 */
.tracks{display:grid;grid-template-columns:1fr 1fr;gap:2.4mm}
.tr{padding:0 0 1mm}.tr h4{margin:0;padding:1.4mm 3mm;font-family:var(--f-title);font-weight:400;font-size:8.6pt;color:#fff;display:flex;justify-content:space-between;align-items:baseline;border-radius:.6mm .6mm 0 0}.tr h4 small{font-family:var(--f-hand);font-weight:700;font-size:7.2pt}
.tr .it{padding:1.1mm 3mm 1mm;border-top:.3mm dashed var(--rule)}.tr .it:first-of-type{border-top:0}
.tr .m{font-size:6.5pt;color:var(--mute)}.tr .m b{color:var(--red)}.tr .t{font-family:var(--f-title);font-weight:400;font-size:8.3pt;line-height:1.32;margin:.2mm 0}.tr .d{font-size:7.05pt;color:var(--sub);white-space:nowrap;overflow:hidden}.tr .d b{color:var(--ink)}
.tr .none{padding:1.6mm 3mm;font-size:7.2pt}.tr .none b{display:block;margin-bottom:.8mm}.tr .none li{font-size:6.8pt;color:var(--mute)}
/* 과업 반영사항 */
.acts{padding:1.2mm 3mm}.act{display:flex;gap:3mm;align-items:flex-start;padding:.8mm 0}.act+.act{border-top:.3mm dashed var(--rule)}
.act .lab{flex:none;width:21mm;font-family:var(--f-title);font-size:7.4pt;color:#fff;background:var(--navy);text-align:center;padding:.5mm 0;border-radius:255px 15px 225px 15px/15px 225px 15px 255px}
.act .tx{font-size:7.2pt;line-height:1.42}.act .tx b{color:var(--ink)}
/* 푸터 */
.foot{margin-top:auto;padding-top:1mm;display:flex;justify-content:space-between;align-items:flex-end;gap:4mm}
.foot .l{font-size:6.6pt;color:var(--mute);line-height:1.5}.foot .l b{color:var(--ink)}.foot .r{display:flex;align-items:center;gap:2.5mm;font-family:var(--f-hand);font-size:7pt;color:var(--mute)}
.sk-rule{display:block;width:100%;height:3mm;flex:0 0 100%}.foot{flex-wrap:wrap}.foot .sk-rule{height:2.4mm}
"""

SCRIBBLE = """<svg class="m-scribble" viewBox="0 0 300 14" preserveAspectRatio="none" aria-hidden="true"><path d="M3 9 C60 3 120 12 180 6 S270 4 297 8" stroke="#FFC845" stroke-width="4.5" fill="none" stroke-linecap="round"/><path d="M40 12 C110 8 190 13 262 9" stroke="#FFC845" stroke-width="2.2" fill="none" stroke-linecap="round" opacity=".7"/></svg>"""

JS = """(function(){if(!window.rough)return;var SEED=11,INK='#3a3f55';
function frame(el,i){var old=el.querySelector(':scope > svg.sk-frame');if(old)old.remove();var w=el.offsetWidth,h=el.offsetHeight;if(!w||!h)return;
var svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','sk-frame');svg.setAttribute('viewBox','0 0 '+w+' '+h);
svg.appendChild(rough.svg(svg).rectangle(1.5,1.5,w-3,h-3,{stroke:el.dataset.skStroke||INK,strokeWidth:el.dataset.skW||1.1,roughness:1.2,bowing:1.3,fill:'none',seed:SEED+i}));el.insertBefore(svg,el.firstChild);}
function rule(el,i){var old=el.querySelector(':scope > svg.sk-rule');if(old)old.remove();var w=el.clientWidth;var svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','sk-rule');svg.setAttribute('viewBox','0 0 '+w+' 12');
svg.appendChild(rough.svg(svg).line(2,6,w-2,6,{stroke:INK,strokeWidth:1.8,roughness:1.5,bowing:1,seed:SEED+i}));el.insertBefore(svg,el.firstChild);}
function run(){document.querySelectorAll('.sk').forEach(frame);document.querySelectorAll('.rule-before').forEach(rule);}
run();if(document.fonts&&document.fonts.ready)document.fonts.ready.then(run);window.__skDone=true;})();"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def data_uri(name):
    p = os.path.join(DOCS, "assets", name)
    if not os.path.exists(p):
        return ""
    with open(p, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def font_css(fonts_dir):
    """npm 패키지(@fontsource/*)의 CSS를 file:// 절대경로로 링크. Pretendard는 ~/.fonts 설치본 사용"""
    links = []
    for pkg in ["gaegu", "jua", "nanum-brush-script", "permanent-marker"]:
        p = os.path.abspath(os.path.join(fonts_dir, "@fontsource", pkg, "index.css"))
        if os.path.exists(p):
            links.append(f'<link rel="stylesheet" href="file://{p}">')
    return "".join(links)


def render(c, fonts_dir):
    d = date.fromisoformat(c["date"])
    k = c["kpi"]
    kto, sp = data_uri("kto_signature.png"), data_uri("southernpost.png")
    if not kto:
        raise SystemExit("로고 파일 없음: docs/assets/kto_signature.png")
    css = CSS.replace("KTO_URI", kto).replace("SP_URI", sp)
    rough_path = os.path.abspath(os.path.join(DOCS, "assets", "rough.min.js"))
    rough_js = open(rough_path, encoding="utf-8").read() if os.path.exists(rough_path) else ""

    tr_n = " · ".join(f"{t} {n:,}" for t, n in k["new_by_track"].items())
    period_cls = ' red' if k.get("period_warn") else ""
    kpis = [
        ("신규 수집", f'{k["new_total"]:,}<small>건</small>', tr_n),
        ("과업 관련 선별", f'{k["selected"]:,}<small>건</small><span class="g">→ 통합 {k["merged"]:,}건</span>', f'제외 {k["excluded"]:,}건 · 제외율 {k["excluded_pct"]}%'),
        ("누적 수집", f'{k["total"]:,}<small>건</small>', f'최종 수집 {esc(k["last"])} KST'),
        ("수집 대상 기간", f'{esc(k["period"])}', esc(k.get("period_note") or "보도일 기준 · 당일 수집분 반영")),
    ]
    kpi_html = '<div class="kpi">' + "".join(
        f'<div class="kp sk"><div class="desk">{esc(a)}</div><div class="big">{b}</div><div class="what{period_cls if i == 3 else ""}">{w}</div></div>'
        for i, (a, b, w) in enumerate(kpis)) + "</div>"

    cnt = c.get("counts", {})
    cats = '<div class="cats"><span class="lab">중요도 분류</span>' + "".join(
        (f'<span><i style="background:{COLOR[x]}"></i>{x}<b>{cnt.get(x, 0)}</b></span>' if cnt.get(x, 0) else f'<span class="z"><i></i>{x} 0</span>')
        for x in CATS) + "</div>"

    def card(it, full):
        col = COLOR.get(it["cat"], "#7B8197")
        ver = '<span class="tag ok">원문 검증</span>' if it.get("verified") else '<span class="tag ng">원문 미확인</span>'
        num = f'<span class="tag n">{it["rank"]} {esc(it["cat"])}</span>' if full else f'<span class="tag n" style="background:{col}">{it["rank"]}</span><span class="tag" style="background:{col}">{esc(it["cat"])}</span>'
        trk = "".join(f'<span class="tag o">{esc(t)}</span>' for t in it.get("tracks", []))
        lis = "".join(f"<li>{b}</li>" for b in it["bullets"])
        ins = f'<div class="insight"><b>시사점 :</b>{it["insight"]}</div>' if it.get("insight") else ""
        return (f'<article class="card sk {"full" if full else "half"}" data-sk-stroke="{col}" data-sk-w="1.4" style="--c:{col}">'
                f'<div class="tags">{num}{trk}{ver}</div><h3>{esc(it["title"])}</h3><ul>{lis}</ul><div class="src">{esc(it["source"])}</div>{ins}</article>')
    issues = c["issues"]
    issues_html = '<div class="issues">' + card(issues[0], True) + "".join(card(x, False) for x in issues[1:3]) + "</div>"

    def track_box(name):
        col = TRACK_COLOR[name]
        items = c["trends"].get(name) or []
        if items:
            body = "".join(f'<div class="it"><div class="m">{esc(x["date"])} · {x["media"]}</div><div class="t">{esc(x["title"])}</div><div class="d">{x["desc"]}</div></div>' for x in items)
        else:
            e = (c.get("trend_empty") or {}).get(name, {})
            body = f'<div class="none"><b>{esc(e.get("reason", "해당 트랙 선별 건 없음"))}</b><ul>' + "".join(f"<li>{esc(t)}</li>" for t in e.get("examples", [])) + "</ul></div>"
        return f'<section class="tr sk" data-sk-stroke="{col}"><h4 style="background:{col}">{esc(name)}<small>{len(items)}건</small></h4>{body}</section>'
    tracks_html = '<div class="tracks">' + track_box("MICE 유치") + track_box("전시·컨벤션") + "</div>"

    acts = '<section class="acts sk">' + "".join(f'<div class="act"><span class="lab">{esc(a["label"])}</span><div class="tx">{a["text"]}</div></div>' for a in c["actions"]) + "</section>"

    sp_logo = '<span class="sp" role="img" aria-label="서던포스트"></span>' if sp else "<b>(주)서던포스트</b>"
    vn = c.get("verified_count", sum(1 for x in issues if x.get("verified")))
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>MICE 이슈 레이더 일일 이슈 브리핑 {c["date"]}</title>{font_css(fonts_dir)}<style>{css}</style></head><body>
<div class="wrap">
<div class="org"><div class="l"><span class="kto" role="img" aria-label="한국관광공사"></span><span class="vl"></span><div class="cap">MICE 이슈 레이더<small>한국관광공사 MICE 산업 일일 이슈 모니터링 · 발주 한국관광공사 · 수행 (주)서던포스트</small></div></div>
<div class="r"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></div>
<header class="mast"><div class="m-top"><span class="m-kick">KTO · MICE ISSUE RADAR · DAILY</span><span>자료원 : mice-radar 자동수집 데이터베이스 (MICE 유치 · 전시·컨벤션 2개 트랙)</span></div>
<div class="m-main"><div class="m-word"><h1 class="m-en"><small>KTO</small>MICE{SCRIBBLE}</h1><div class="m-ko"><b>이슈 레이더</b><span>일일 이슈 브리핑</span></div></div>
<div class="m-date"><span class="no">제{c.get("no", 1)}호</span><b>{d:%Y. %m. %d.}</b><span>({WD[d.weekday()]}) 일일 이슈 브리핑</span></div></div></header>
<div class="task"><span class="t"><em>과업</em>한국관광공사 MICE 산업 일일 이슈 모니터링</span><span class="s">같은 사안은 1건으로 통합 · 주요 이슈는 원문 대조</span></div>
{kpi_html}{cats}
<div class="sh"><span class="lbl">TODAY</span><h2>주요 이슈</h2><span class="n">리스크·쟁점 → 정책·예산 → 발주처 → 유치·개최 → 통계·실적 순 중요도</span></div>{issues_html}
<div class="sh"><span class="lbl">TRACK</span><h2>트랙별 주요 동향</h2><span class="n">주요 이슈와 중복 없이 트랙별 3~4건</span></div>{tracks_html}
<div class="sh"><span class="lbl">ACTION</span><h2>과업 반영사항</h2></div>{acts}
<footer class="foot rule-before"><div class="l">자료원 : <b>https://baebong3.github.io/mice-radar/</b><br>누적 수집 {k["total"]:,}건 · 최종 수집 {esc(k["last"])} KST · 주요 이슈 3건 중 {vn}건 원문 대조 검증 완료</div>
<div class="r"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></footer>
</div><script>{rough_js}</script><script>{JS}</script></body></html>"""


def to_pdf(html_path, pdf_path):
    """Playwright가 있으면 글꼴 로딩을 기다렸다가 인쇄, 없으면 chromium CLI"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto("file://" + os.path.abspath(html_path))
            pg.wait_for_function("document.fonts.status==='loaded' && window.__skDone===true", timeout=20000)
            pg.wait_for_timeout(300)
            pg.evaluate("document.querySelectorAll('.sk').forEach(function(e){e.dispatchEvent(new Event('x'))})")
            pg.pdf(path=pdf_path, format="A4", print_background=True, prefer_css_page_size=True)
            b.close()
        return
    except ImportError:
        pass
    exe = "/opt/pw-browsers/chromium"
    if os.path.isdir(exe):
        out = subprocess.run(["find", "/opt/pw-browsers", "-name", "chrome", "-type", "f"], capture_output=True, text=True).stdout.split()
        exe = out[0] if out else "chromium"
    subprocess.run([exe, "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", "--virtual-time-budget=4000",
                    f"--print-to-pdf={pdf_path}", "file://" + os.path.abspath(html_path)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--fonts", default="node_modules", help="npm node_modules 경로")
    ap.add_argument("--html", help="HTML 저장 경로 (기본: PDF와 같은 이름)")
    ap.add_argument("--out", help="PDF 경로")
    a = ap.parse_args()
    with open(a.content, encoding="utf-8") as f:
        c = json.load(f)
    html_out = render(c, a.fonts)
    html_path = a.html or (os.path.splitext(a.out)[0] + ".html" if a.out else f"brief_{c['date'].replace('-', '')}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print("HTML:", html_path)
    if a.out:
        to_pdf(html_path, a.out)
        try:
            from pypdf import PdfReader
            n = len(PdfReader(a.out).pages)
            print(f"PDF: {a.out} ({n}쪽)")
            if n != 1:
                sys.exit(f"쪽수 {n} - 1쪽이 아님. 문장을 줄여 다시 만들 것")
        except ImportError:
            print("PDF:", a.out)


if __name__ == "__main__":
    main()
