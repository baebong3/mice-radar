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
CSS = """
:root{--ink:#1C1B1B;--g1:#8D8B8B;--g3:#5F5D5C;--or:#E49000;--or2:#C47A00;--line:#E7E4E2;--line2:#DEDBD9;--bg:#FAF8F6}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--ink);font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;word-break:keep-all;overflow-wrap:break-word;line-height:1.5;-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:inherit;text-decoration:none}
.w{max-width:900px;margin:0 auto;padding:0 20px}
.bar{display:flex;height:5px}.bar i{flex:1}.bar i:nth-child(1){background:#D80024}.bar i:nth-child(2){background:#E49000}.bar i:nth-child(3){background:#F2DF4E}.bar i:nth-child(4){background:#E478A8}
header{border-bottom:1px solid var(--line)}header .w{display:flex;justify-content:space-between;align-items:center;gap:16px;padding-top:18px;padding-bottom:16px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:16px}.kto{display:block;height:38px;width:112px;background:url(KTO_URI) left center/contain no-repeat}.brand .vl{width:1px;height:40px;background:var(--line2)}
.cap{font-size:12px;color:var(--g1)}.cap b{color:var(--g3);font-weight:700}h1{margin:1px 0 0;font-size:24px;font-weight:800;letter-spacing:-.02em;line-height:1.2}
.back{font-size:13px;font-weight:700;color:var(--g3);border:1px solid var(--line2);padding:7px 12px;white-space:nowrap}.back:hover{border-color:var(--ink);color:var(--ink)}
.sub{display:flex;justify-content:space-between;align-items:flex-end;margin:26px 0 0;padding-bottom:10px;border-bottom:1px solid var(--ink);flex-wrap:wrap;gap:8px}
.lbl{font-size:12px;font-weight:800;color:var(--or);letter-spacing:.06em}.lbl::before{content:"◆";font-size:9px;margin-right:6px;vertical-align:1px}
h2{margin:3px 0 0;font-size:20px;font-weight:800}.sub .n{font-size:12px;color:var(--g1)}
ol{list-style:none;margin:0 0 30px;padding:0}
li{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:14px 4px;border-bottom:1px solid var(--line)}
li:first-child{background:var(--bg);padding-left:14px;padding-right:14px;border-left:3px solid var(--or)}
.d{font-size:17px;font-weight:800;letter-spacing:-.01em}.d small{display:block;font-size:12.5px;color:var(--g1);font-weight:500;margin-top:1px}
.new{display:inline-block;font-size:10.5px;font-weight:800;color:#fff;background:var(--or);padding:1px 7px;margin-left:8px;vertical-align:2px}
a.pdf{font-size:13px;font-weight:800;color:var(--ink);border:1px solid var(--ink);padding:7px 14px;white-space:nowrap}a.pdf:hover{background:var(--ink);color:#fff}
.empty{padding:28px 4px;color:var(--g1);font-size:13.5px}
footer{margin-top:40px;border-top:1px solid var(--ink)}footer .w{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;padding-top:14px;padding-bottom:36px;font-size:12px;color:var(--g1)}
footer .fr{display:flex;align-items:center;gap:12px}.sp{display:block;width:112px;height:25px;background:url(SP_URI) right center/contain no-repeat}
@media(max-width:680px){.cap{display:none}h1{font-size:21px}.kto{height:32px;width:94px}.brand .vl{height:34px}}
"""


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
        items.append(f'<li><span class="d">{dt:%Y. %m. %d.} ({WD[dt.weekday()]}){new}<small>일일 이슈 브리핑 · A4 1쪽 · {size / 1024:,.0f}KB</small></span>'
                     f'<a class="pdf" href="{html.escape(f)}" target="_blank" rel="noopener">PDF 보기</a></li>')
    body = "".join(items) or '<li class="empty">아직 등록된 브리핑이 없음</li>'
    kto, sp = data_uri("kto_signature.png"), data_uri("southernpost.png")
    css = CSS.replace("KTO_URI", kto).replace("SP_URI", sp)
    brand_logo = '<span class="kto" role="img" aria-label="한국관광공사"></span><span class="vl"></span>' if kto else ""
    sp_logo = '<span class="sp" role="img" aria-label="서던포스트"></span>' if sp else "<b>(주)서던포스트</b>"
    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>일일 이슈 브리핑 - MICE 이슈 레이더</title><style>{css}</style></head><body>
<div class="bar"><i></i><i></i><i></i><i></i></div>
<header><div class="w"><div class="brand">{brand_logo}<div><div class="cap">한국관광공사 <b>MICE 산업 일일 이슈 모니터링</b></div><h1>MICE 이슈 레이더</h1></div></div><a class="back" href="../">← 이슈 레이더 메인</a></div></header>
<main class="w"><div class="sub"><div><div class="lbl">브리핑 모음</div><h2>일일 이슈 브리핑</h2></div><span class="n">총 {len(briefs):,}건 · 최신순</span></div><ol>{body}</ol></main>
<footer><div class="w"><span>갱신 {now:%Y-%m-%d %H:%M} KST · 자료원 : https://baebong3.github.io/mice-radar/</span><div class="fr"><span>발주 한국관광공사 · 수행</span>{sp_logo}</div></div></footer>
</body></html>"""
    os.makedirs(BRIEF_DIR, exist_ok=True)
    with open(os.path.join(BRIEF_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"docs/briefings/index.html 생성: {len(briefs)}건")


if __name__ == "__main__":
    main()
