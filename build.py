"""메인 페이지(docs/index.html) 생성 - 최근 N일 수집 기사 + 브리핑 건수

사용: python3 radar/build.py --days 7
"""
import argparse
import html
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, DOCS, TRACKS, connect, list_briefings, now_kst  # noqa: E402

WD = "월화수목금토일"
CSS = """
:root{--ink:#1C1B1B;--g1:#8D8B8B;--g2:#A6A3A1;--g3:#5F5D5C;--or:#E49000;--red:#D80024;--line:#E7E4E2;--bg:#FAF8F6;--chip:#EFECEA}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;word-break:keep-all;line-height:1.5}
a{color:inherit}.w{max-width:1120px;margin:0 auto;padding:0 16px}
header{padding:22px 0 14px}.org{font-size:12.5px;color:var(--g1)}.org b{color:var(--g3)}
h1{margin:2px 0 0;font-size:26px;font-weight:800;letter-spacing:-.02em}
.bar{display:flex;height:4px}.bar i{flex:1}.bar i:nth-child(1){background:#D80024}.bar i:nth-child(2){background:#E49000}.bar i:nth-child(3){background:#F2DF4E}.bar i:nth-child(4){background:#E478A8}
.kpi{display:grid;grid-template-columns:repeat(4,1fr);border-top:3px solid var(--or);margin:18px 0}
.kpi div{padding:10px 12px;border-left:1px solid var(--line)}.kpi div:first-child{border-left:0}
.kpi b{display:block;font-size:22px;font-weight:800}.kpi span{font-size:13px;font-weight:700}.kpi small{display:block;font-size:11.5px;color:var(--g1)}
.kpi div:first-child b{color:var(--or)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px}
.box{border:1px solid var(--line)}.box h2{margin:0;padding:8px 12px;color:#fff;font-size:15px;display:flex;justify-content:space-between}
.t0 h2{background:var(--red)}.t1 h2{background:var(--or)}
.day{padding:6px 12px 2px;font-size:12px;font-weight:800;color:var(--g3);background:var(--bg);border-top:1px solid var(--line)}
ul{list-style:none;margin:0;padding:0 12px 6px}li{padding:7px 0;border-bottom:1px solid var(--line)}li:last-child{border-bottom:0}
li a{font-weight:700;font-size:14px;text-decoration:none}li a:hover{text-decoration:underline}
.m{font-size:11.5px;color:var(--g1)}.c{display:inline-block;font-size:10.5px;font-weight:700;padding:0 6px;margin-right:4px;background:var(--chip);color:var(--g3);border-radius:2px}
.c.hot{background:var(--or);color:#fff}
details{padding:4px 12px 10px;font-size:12.5px;color:var(--g1)}details li a{font-weight:500;font-size:12.5px}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap}
.btn{display:inline-block;padding:8px 14px;border:1.5px solid var(--ink);font-weight:800;font-size:13px;text-decoration:none}
footer{border-top:2px solid var(--ink);padding:10px 0 30px;font-size:12px;color:var(--g1);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}footer b{color:var(--ink)}
@media(max-width:760px){.cols{grid-template-columns:1fr}.kpi{grid-template-columns:1fr 1fr}.kpi div:nth-child(3){border-left:0}}
"""


def esc(s):
    return html.escape(s or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()

    con = connect()
    now = now_kst()
    since = (now - timedelta(days=a.days - 1)).strftime("%Y-%m-%d")
    rows = con.execute(
        "select url,track,title,media,date,category from news where date>=? order by date desc, collected_at desc",
        (since,)).fetchall()
    total, last = con.execute("select count(*), max(collected_at) from news").fetchone()
    briefs = list_briefings()

    cols = []
    for i, tr in enumerate(TRACKS):
        trs = [r for r in rows if r[1] == tr]
        main_rows = [r for r in trs if r[5] != "기타"]
        etc = [r for r in trs if r[5] == "기타"]
        parts = [f'<section class="box t{i}"><h2><span>{esc(tr)}</span><span>{len(main_rows)}건</span></h2>']
        cur = None
        for url, _, title, media, date, cat in main_rows:
            if date != cur:
                if cur is not None:
                    parts.append("</ul>")
                cur = date
                parts.append(f'<div class="day">{esc(date)}</div><ul>')
            hot = " hot" if cat in CATEGORIES[:3] else ""
            parts.append(f'<li><span class="c{hot}">{esc(cat)}</span><a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>'
                         f'<div class="m">{esc(media)} · {esc(date)}</div></li>')
        if cur is not None:
            parts.append("</ul>")
        if not main_rows:
            parts.append('<ul><li class="m">최근 수집분 없음</li></ul>')
        if etc:
            parts.append(f'<details><summary>분류 외(기타) {len(etc)}건</summary><ul>')
            parts += [f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a> <span class="m">{esc(m)} · {esc(d)}</span></li>'
                      for u, _, t, m, d, _ in etc]
            parts.append("</ul></details>")
        parts.append("</section>")
        cols.append("".join(parts))

    by_tr = " · ".join(f"{t} {sum(1 for r in rows if r[1]==t)}" for t in TRACKS)
    latest = f'최신 {briefs[0][0][:4]}.{briefs[0][0][4:6]}.{briefs[0][0][6:]}' if briefs else "아직 없음"
    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MICE 이슈 레이더</title><style>{CSS}</style></head><body>
<header class="w"><div class="top"><div><div class="org">발주 <b>한국관광공사</b> · 수행 <b>(주)서던포스트</b></div><h1>MICE 이슈 레이더</h1></div>
<a class="btn" href="briefings/">일일 이슈 브리핑 {len(briefs)}건 →</a></div></header>
<div class="bar"><i></i><i></i><i></i><i></i></div>
<main class="w">
<div class="kpi">
<div><b>{len(rows):,}</b><span>최근 {a.days}일 수집</span><small>{esc(by_tr)}</small></div>
<div><b>{total:,}</b><span>누적 수집</span><small>최종 수집 {esc(last or '-')} KST</small></div>
<div><b>{len(briefs):,}</b><span>일일 브리핑</span><small>{latest}</small></div>
<div><b>{since[5:].replace('-', '.')} ~ {now.strftime('%m.%d')}</b><span>표시 기간</span><small>보도일 기준 · 매일 08:30 KST 자동수집</small></div>
</div>
<div class="cols">{''.join(cols)}</div>
</main>
<footer class="w"><span>자료원 : Google News RSS 자동수집 (MICE 유치·전시·컨벤션 2개 트랙) · 페이지 생성 {now.strftime('%Y-%m-%d %H:%M')} KST</span><span>발주 한국관광공사 · 수행 <b>(주)서던포스트</b></span></footer>
</body></html>"""
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"docs/index.html 생성: 최근 {a.days}일 {len(rows)}건, 브리핑 {len(briefs)}건")


if __name__ == "__main__":
    main()
