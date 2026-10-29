"""브리핑 모음 페이지(docs/briefings/index.html) 생성

사용: python3 radar/briefings.py
"""
import base64
import html
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from common import BRIEF_DIR, DOCS, list_briefings, now_kst  # noqa: E402

WD = "월화수목금토일"
FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gaegu:wght@400;700&family=Jua&family=Nanum+Brush+Script&family=Permanent+Marker&display=swap">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">"""

CSS = """
:root{--paper:#fff;--ink:#2b2f45;--navy:#16193A;--sub:#4a5068;--mute:#7b8197;--rule:#d9dbe6;--wash:#f5f6fa;--cream:#FFF6E5;--yel:#FFC845;--red:#D9472B;
--f-body:"Pretendard","Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif;--f-title:"Jua","Noto Sans KR",sans-serif;--f-hand:"Gaegu","Noto Sans KR",sans-serif;--f-mark:"Permanent Marker","Jua",cursive;--f-brush:"Nanum Brush Script","Jua",cursive}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.6;word-break:keep-all;overflow-wrap:break-word;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:inherit;text-decoration:none}.wrap{max-width:880px;margin:0 auto;padding:14px 20px 40px}
.sk{position:relative}.sk-frame{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible;z-index:0}.sk>*:not(.sk-frame){position:relative;z-index:1}
.org{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding:4px 2px 10px}
.org .l{display:flex;align-items:center;gap:14px}.kto{display:block;width:118px;height:40px;background:url(KTO_URI) left center/contain no-repeat}
.org .vl{width:1px;height:30px;background:var(--rule)}.org .cap{font-family:var(--f-hand);font-size:16px;font-weight:700;color:var(--sub);line-height:1.25}.org .cap small{display:block;font-size:13px;font-weight:400;color:var(--mute)}
.org .r{display:flex;align-items:center;gap:10px;font-family:var(--f-hand);font-size:14px;color:var(--mute)}.sp{display:block;width:104px;height:24px;background:url(SP_URI) right center/contain no-repeat}
.mast{position:relative;background:var(--navy);color:var(--cream);border-radius:22px 30px 20px 28px/28px 20px 30px 22px;padding:14px 26px 28px;overflow:hidden}
.mast::after{content:"";position:absolute;left:0;right:0;bottom:0;height:16px;background:repeating-linear-gradient(90deg,rgba(255,246,229,.55) 0 2px,transparent 2px 12px),repeating-linear-gradient(90deg,rgba(255,200,69,.95) 0 3px,transparent 3px 60px);background-size:auto 9px,auto 16px;background-repeat:repeat-x;background-position:0 100%,0 100%;filter:url(#rough-f)}
.m-top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-family:var(--f-hand);font-size:16px;font-weight:700;color:rgba(255,246,229,.82);border-bottom:2px dashed rgba(255,246,229,.3);padding-bottom:8px}
.m-kick{font-family:var(--f-mark);font-size:14px;letter-spacing:.08em;color:var(--yel);transform:rotate(-1.5deg);display:inline-block}.m-top a{color:var(--yel);text-decoration:underline;text-underline-offset:3px}
.m-main{display:flex;align-items:center;justify-content:center;gap:18px;margin:12px 0 4px;flex-wrap:wrap}
.m-en{position:relative;margin:0;font-family:var(--f-mark);font-weight:400;font-size:clamp(40px,7vw,72px);line-height:.95;color:var(--cream);transform:rotate(-2.5deg);padding-bottom:.12em}
.m-scribble{position:absolute;left:4%;bottom:-.04em;width:96%;height:.16em;overflow:visible}
.m-ko{position:relative;transform:rotate(2deg);padding-left:16px}.m-ko::before{content:"";position:absolute;left:0;top:6%;bottom:6%;width:4px;border-radius:3px;background:var(--yel);transform:rotate(-3deg)}
.m-ko b{display:block;font-family:var(--f-brush);font-weight:400;font-size:clamp(44px,6.5vw,68px);line-height:.9;color:var(--cream)}
.m-ko span{display:block;font-family:var(--f-hand);font-weight:700;font-size:16px;letter-spacing:.08em;color:var(--yel);margin-top:4px}
.m-tag{text-align:center;margin:6px 0 4px;font-family:var(--f-title);font-size:16px;color:rgba(255,246,229,.9)}
.sub{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;margin:24px 0 12px}
.sub h2{font-family:var(--f-title);font-weight:400;font-size:30px;margin:0;line-height:1}.sub .n{font-family:var(--f-hand);font-size:15px;color:var(--sub)}
ol{list-style:none;margin:0;padding:0;display:grid;gap:10px}
li{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:14px 18px;min-width:0}
.d{font-family:var(--f-title);font-size:21px;line-height:1.2}.d small{display:block;font-family:var(--f-body);font-size:13px;color:var(--mute);margin-top:3px}
.new{display:inline-block;font-family:var(--f-title);font-size:13px;color:var(--navy);background:var(--yel);padding:1px 9px;margin-left:8px;vertical-align:3px;border-radius:255px 15px 225px 15px/15px 225px 15px 255px;transform:rotate(-2deg)}
a.pdf{font-family:var(--f-title);font-size:15px;color:#fff;background:var(--navy);padding:7px 16px;white-space:nowrap;border-radius:255px 15px 225px 15px/15px 225px 15px 255px}a.pdf:hover{background:var(--red)}
.empty{font-family:var(--f-hand);font-size:16px;color:var(--mute);padding:20px 4px}
.foot{margin-top:30px;display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--mute)}
.foot .r{display:flex;align-items:center;gap:10px;font-family:var(--f-hand);font-size:14px}
@media(max-width:640px){.org .cap{display:none}.kto{width:100px;height:34px}.m-main{flex-direction:column;gap:6px}.m-ko{padding-left:0;text-align:center}.m-ko::before{display:none}li{flex-direction:column;align-items:flex-start}.d{font-size:19px}}
"""
SCRIBBLE = """<svg class="m-scribble" viewBox="0 0 300 14" preserveAspectRatio="none" aria-hidden="true"><path d="M3 9 C60 3 120 12 180 6 S270 4 297 8" stroke="#FFC845" stroke-width="4.5" fill="none" stroke-linecap="round"/><path d="M40 12 C110 8 190 13 262 9" stroke="#FFC845" stroke-width="2.2" fill="none" stroke-linecap="round" opacity=".7"/></svg>"""
ROUGH_DEFS = """<svg width="0" height="0" aria-hidden="true" style="position:absolute"><filter id="rough-f"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/><feDisplacementMap in="SourceGraphic" scale="3.2"/></filter></svg>"""
JS = """(function(){if(!window.rough)return;var SEED=11,INK='#3a3f55';
function frame(el,i){var old=el.querySelector(':scope > svg.sk-frame');if(old)old.remove();var w=el.offsetWidth,h=el.offsetHeight;if(!w||!h)return;
var svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('class','sk-frame');svg.setAttribute('viewBox','0 0 '+w+' '+h);
svg.appendChild(rough.svg(svg).rectangle(2,2,w-4,h-4,{stroke:el.dataset.skStroke||INK,strokeWidth:1.2,roughness:1.3,bowing:1.4,fill:'none',seed:SEED+i}));el.insertBefore(svg,el.firstChild);}
function run(){document.querySelectorAll('.sk').forEach(frame);}var t;function rerun(){clearTimeout(t);t=setTimeout(run,150);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();if(document.fonts&&document.fonts.ready)document.fonts.ready.then(rerun);window.addEventListener('resize',rerun);})();"""


def data_uri(name):
    p = os.path.join(DOCS, "assets", name)
    if not os.path.exists(p):
        return ""
    with open(p, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def main():
    briefs = list_briefings()
    now = now_kst()
    items = []
    for i, (d, f, size) in enumerate(briefs):
        dt = date(int(d[:4]), int(d[4:6]), int(d[6:]))
        new = '<span class="new">최신</span>' if i == 0 else ""
        items.append(f'<li class="sk"><span class="d">{dt:%Y. %m. %d.} ({WD[dt.weekday()]}){new}<small>제{len(briefs) - i}호 · 일일 이슈 브리핑 · A4 1쪽 · {size / 1024:,.0f}KB</small></span>'
                     f'<a class="pdf" href="{html.escape(f)}" target="_blank" rel="noopener">PDF 열기 →</a></li>')
    body = "".join(items) or '<li class="empty">아직 등록된 브리핑이 없음</li>'
    kto, sp = data_uri("kto_signature.png"), data_uri("southernpost.png")
    css = CSS.replace("KTO_URI", kto).replace("SP_URI", sp)
    brand_logo = '<span class="kto" role="img" aria-label="한국관광공사"></span><span class="vl"></span>' if kto else ""
    sp_logo = '<span class="sp" role="img" aria-label="서던포스트"></span>' if sp else "<b>(주)서던포스트</b>"
    org_l = ('<span class="kto" role="img" aria-label="한국관광공사"></span><span class="vl"></span>' if kto else "") + \
        '<div class="cap">MICE 산업 일일 이슈 모니터링<small>일일 이슈 브리핑 모음 · A4 1쪽 PDF</small></div>'
    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>일일 이슈 브리핑 - MICE 이슈 레이더</title>{FONT_LINKS}<style>{css}</style></head><body>{ROUGH_DEFS}<div class="wrap">
<div class="org"><div class="l">{org_l}</div><div class="r"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></div>
<header class="mast"><div class="m-top"><span class="m-kick">KTO · MICE ISSUE RADAR</span><a href="../">← 이슈 레이더 메인으로</a></div>
<div class="m-main"><h1 class="m-en">MICE{SCRIBBLE}</h1><div class="m-ko"><b>일일 이슈 브리핑</b><span>날짜별 PDF 모음</span></div></div>
<p class="m-tag">매일 아침 수집 데이터에서 주요 이슈 3건과 트랙별 동향을 추려 A4 한 장에 담은 브리핑</p></header>
<main><div class="sub"><h2>브리핑 모음</h2><span class="n">총 {len(briefs):,}호 · 최신순</span></div><ol>{body}</ol></main>
<footer class="foot"><span>갱신 {now:%Y-%m-%d %H:%M} KST · 자료원 : https://baebong3.github.io/mice-radar/</span><div class="r"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></footer>
</div><script src="../assets/rough.min.js"></script><script>{JS}</script></body></html>"""
    os.makedirs(BRIEF_DIR, exist_ok=True)
    with open(os.path.join(BRIEF_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"docs/briefings/index.html 생성: {len(briefs)}건")


if __name__ == "__main__":
    main()
