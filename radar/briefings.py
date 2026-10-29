"""브리핑 모음 페이지(docs/briefings/index.html) 생성

사용: python3 radar/briefings.py
"""
import html
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from common import BRIEF_DIR, list_briefings, now_kst  # noqa: E402

WD = "월화수목금토일"
CSS = """
:root{--ink:#1C1B1B;--g1:#8D8B8B;--g3:#5F5D5C;--or:#E49000;--line:#E7E4E2;--bg:#FAF8F6}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;word-break:keep-all;line-height:1.5}
.w{max-width:860px;margin:0 auto;padding:0 16px}header{padding:22px 0 14px}
.org{font-size:12.5px;color:var(--g1)}.org b{color:var(--g3)}h1{margin:2px 0 0;font-size:24px;font-weight:800}
.bar{display:flex;height:4px}.bar i{flex:1}.bar i:nth-child(1){background:#D80024}.bar i:nth-child(2){background:#E49000}.bar i:nth-child(3){background:#F2DF4E}.bar i:nth-child(4){background:#E478A8}
.sub{display:flex;justify-content:space-between;align-items:center;margin:16px 0 8px;font-size:13px;color:var(--g1)}.sub a{color:var(--ink);font-weight:700}
ol{list-style:none;margin:0 0 30px;padding:0;border-top:3px solid var(--or)}
li{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 4px;border-bottom:1px solid var(--line)}
li:first-child{background:var(--bg)}.d{font-size:17px;font-weight:800}.d small{font-size:12.5px;color:var(--g1);font-weight:500;margin-left:6px}
.new{display:inline-block;font-size:10.5px;font-weight:800;color:#fff;background:var(--or);padding:0 6px;margin-left:6px;vertical-align:2px}
a.pdf{font-size:13px;font-weight:800;color:var(--ink);text-decoration:none;border:1.5px solid var(--ink);padding:5px 12px;white-space:nowrap}
.empty{padding:24px 4px;color:var(--g1)}
footer{border-top:2px solid var(--ink);padding:10px 0 30px;font-size:12px;color:var(--g1)}footer b{color:var(--ink)}
"""


def main():
    briefs = list_briefings()
    items = []
    for i, (d, f, size) in enumerate(briefs):
        dt = date(int(d[:4]), int(d[4:6]), int(d[6:]))
        new = '<span class="new">최신</span>' if i == 0 else ""
        items.append(f'<li><span class="d">{dt:%Y. %m. %d.}<small>({WD[dt.weekday()]}) 일일 이슈 브리핑 · {size/1024:,.0f}KB</small>{new}</span>'
                     f'<a class="pdf" href="{html.escape(f)}" target="_blank" rel="noopener">PDF 보기</a></li>')
    body = "".join(items) or '<li class="empty">아직 등록된 브리핑이 없음</li>'
    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>브리핑 모음 - MICE 이슈 레이더</title><style>{CSS}</style></head><body>
<header class="w"><div class="org">발주 <b>한국관광공사</b> · 수행 <b>(주)서던포스트</b></div><h1>MICE 이슈 레이더 · 일일 이슈 브리핑</h1></header>
<div class="bar"><i></i><i></i><i></i><i></i></div>
<main class="w"><div class="sub"><span>총 {len(briefs):,}건 · A4 1쪽 PDF</span><a href="../">← 이슈 레이더 메인</a></div><ol>{body}</ol></main>
<footer class="w">갱신 {now_kst():%Y-%m-%d %H:%M} KST · 발주 한국관광공사 · 수행 <b>(주)서던포스트</b></footer>
</body></html>"""
    os.makedirs(BRIEF_DIR, exist_ok=True)
    with open(os.path.join(BRIEF_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"docs/briefings/index.html 생성: {len(briefs)}건")


if __name__ == "__main__":
    main()
