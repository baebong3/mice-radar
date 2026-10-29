"""메인 페이지(docs/index.html) 생성 - 헤드라인 · 주요 뉴스 · 주제별 동향

사용: python3 radar/build.py --days 7

같은 사안을 여러 매체가 보도한 경우 제목 유사도로 묶어 1건으로 보여주고(○○ 外 N개 매체),
주제 가중치 · 보도 매체 수 · 최신성으로 헤드라인과 주요 뉴스를 고른다. 외부 패키지·CDN 없음.
"""
import argparse
import html
import os
import re
import sys
from collections import Counter
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from common import CATEGORIES, DOCS, TRACKS, connect, list_briefings, now_kst  # noqa: E402

WD = "월화수목금토일"
WEIGHT = {"리스크·쟁점": 6, "정책·예산": 5, "발주처": 5, "유치·개최": 4, "통계·실적": 3.5,
          "지자체·시설": 3, "해외·경쟁국": 2.5, "산업 동향": 2.5, "전시회 개최·참가": 0.5, "기타": 0}
COLOR = {"리스크·쟁점": "#D80024", "정책·예산": "#E49000", "발주처": "#E478A8", "유치·개최": "#1C1B1B",
         "통계·실적": "#0B7A4B", "해외·경쟁국": "#5F5D5C", "지자체·시설": "#8D6E00", "산업 동향": "#7A5AA6",
         "전시회 개최·참가": "#A6A3A1", "기타": "#A6A3A1"}
DESC = {"리스크·쟁점": "국정감사 · 적자 · 무산 · 예산 삭감 등", "정책·예산": "정부 · 국회 · 지자체 제도와 예산",
        "발주처": "한국관광공사 · 코리아MICE뷰로", "유치·개최": "국제회의 · 기업회의 유치와 개최",
        "통계·실적": "참가자 · 경제효과 · 순위 · 폐막 실적", "해외·경쟁국": "해외 MICE 시장과 경쟁 도시",
        "지자체·시설": "컨벤션센터 건립 · 확장 · 운영", "산업 동향": "MICE 산업 전반 · 비즈니스 관광",
        "전시회 개최·참가": "개별 전시회 개막 · 기업 참가 안내"}
TRACK_TAG = {"MICE 유치": "유치", "전시·컨벤션": "전시"}

CSS = """
:root{--ink:#1C1B1B;--g1:#8D8B8B;--g2:#A6A3A1;--g3:#5F5D5C;--or:#E49000;--or2:#C47A00;--red:#D80024;--line:#E7E4E2;--bg:#FAF8F6;--chip:#EFECEA;--soft:#FDF4E3}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#fff;color:var(--ink);font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;word-break:keep-all;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}a:hover .tt,a.tt:hover{text-decoration:underline;text-underline-offset:3px}
.w{max-width:1160px;margin:0 auto;padding:0 16px}
header .w{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;padding-top:22px;padding-bottom:14px;flex-wrap:wrap}
.org{font-size:12.5px;color:var(--g1)}.org b{color:var(--g3)}
h1{margin:2px 0 0;font-size:27px;font-weight:800;letter-spacing:-.02em}
.hr{text-align:right}.hr .d{font-size:19px;font-weight:800}.hr .s{font-size:12.5px;color:var(--g1)}
.bar{display:flex;height:4px}.bar i{flex:1}.bar i:nth-child(1){background:#D80024}.bar i:nth-child(2){background:#E49000}.bar i:nth-child(3){background:#F2DF4E}.bar i:nth-child(4){background:#E478A8}
.strip{background:var(--bg);border-bottom:1px solid var(--line)}
.strip .w{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-top:9px;padding-bottom:9px;flex-wrap:wrap}
.flt{display:flex;gap:6px;flex-wrap:wrap}.flt button{font:inherit;font-size:13px;font-weight:700;padding:5px 13px;border:1px solid var(--line);background:#fff;color:var(--g3);cursor:pointer;border-radius:999px}
.flt button.on{background:var(--ink);border-color:var(--ink);color:#fff}
.meta{font-size:12.5px;color:var(--g1)}.meta b{color:var(--ink)}
.lbl{font-size:12px;font-weight:800;color:var(--or);letter-spacing:.04em}
h2{margin:2px 0 0;font-size:21px;font-weight:800;letter-spacing:-.01em}
.sec{margin-top:30px}.sh{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:12px;flex-wrap:wrap}.sh .n{font-size:12.5px;color:var(--g1)}
.chip{display:inline-block;font-size:11.5px;font-weight:700;padding:1px 8px;border-radius:2px;color:#fff;white-space:nowrap}
.tg{display:inline-block;font-size:11px;font-weight:700;padding:0 6px;border:1px solid var(--line);color:var(--g3);border-radius:2px;white-space:nowrap}
.hero{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:16px;margin-top:22px}
.hl{border:1px solid var(--line);border-left:5px solid var(--or);padding:20px 22px;background:#fff}
.hl .tt{display:block;font-size:27px;font-weight:800;line-height:1.32;letter-spacing:-.02em;margin:10px 0 8px}
.src{font-size:13px;color:var(--g1)}.src b{color:var(--g3)}
.rel{margin:14px 0 0;padding:12px 0 0;border-top:1px dashed var(--line);list-style:none}
.rel li{font-size:13.5px;padding:3px 0;display:flex;gap:8px}.rel li span{color:var(--g1);white-space:nowrap;font-size:12.5px}
.rel li a{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.kp{border:1px solid var(--line);display:grid;grid-template-columns:1fr 1fr;border-top:3px solid var(--or)}
.kp>div{padding:12px 14px;border-bottom:1px solid var(--line)}.kp>div:nth-child(odd){border-right:1px solid var(--line)}
.kp>div>b{display:block;font-size:24px;font-weight:800;line-height:1.2}.kp>div:first-child>b{color:var(--or)}
.kp>div>span{font-size:12.5px;font-weight:700}.kp small{display:block;font-size:11.5px;color:var(--g1)}
.kp .cats{grid-column:1/-1;border-right:0!important;border-bottom:0}
.cb{display:flex;height:8px;margin:6px 0 6px;border-radius:2px;overflow:hidden}.cb i{display:block}
.lg{display:flex;flex-wrap:wrap;gap:2px 10px;font-size:11.5px;color:var(--g3)}.lg i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:0}
.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.card{border:1px solid var(--line);border-top:3px solid var(--c);padding:14px 15px 13px;display:flex;flex-direction:column;gap:8px;background:#fff}
.card .tt{font-size:16.5px;font-weight:800;line-height:1.38;flex:1}
.nav{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}
.nav a{font-size:13px;font-weight:700;padding:5px 11px;border:1px solid var(--line);border-radius:999px;color:var(--g3)}
.nav a i{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:0}.nav a em{font-style:normal;color:var(--g1);margin-left:4px;font-weight:500}
.topics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;align-items:start}
.tp{border:1px solid var(--line);background:#fff;scroll-margin-top:12px}.tp.full{grid-column:1/-1}
.tp h3{margin:0;padding:11px 14px 10px;display:flex;align-items:baseline;gap:8px;border-bottom:1px solid var(--line);font-size:16px;font-weight:800}
.tp h3 i{display:inline-block;width:10px;height:10px;border-radius:50%;flex:none}.tp h3 small{font-size:12px;color:var(--g1);font-weight:500;flex:1}.tp h3 b{font-size:13px;color:var(--g3)}
.tp ul{list-style:none;margin:0;padding:2px 14px}
.tp li{padding:9px 0;border-bottom:1px solid var(--line)}.tp li:last-child{border-bottom:0}
.tp li .tt{font-size:14.5px;font-weight:700;line-height:1.42}
.tp li .m{font-size:12px;color:var(--g1);margin-top:2px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.tp li .m .many{color:var(--or2);font-weight:700}
.tp.full ul{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:24px}
.tp.full li{border-bottom:1px solid var(--line)!important}
details.more{border-top:1px solid var(--line)}details.more summary{cursor:pointer;padding:8px 14px;font-size:12.5px;font-weight:700;color:var(--g3);list-style:none}
details.more summary::before{content:"+ "}details.more[open] summary::before{content:"− "}
.empty{padding:14px;color:var(--g1);font-size:13px}
.etc{margin-top:14px;border:1px solid var(--line);background:var(--bg)}.etc summary{cursor:pointer;padding:10px 14px;font-size:13px;color:var(--g3);font-weight:700}
.etc ul{list-style:none;margin:0;padding:0 14px 10px;columns:2;column-gap:24px}.etc li{font-size:12.5px;padding:3px 0;break-inside:avoid;color:var(--g3)}.etc li span{color:var(--g1)}
footer{margin-top:36px;border-top:2px solid var(--ink)}footer .w{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;padding-top:12px;padding-bottom:34px;font-size:12px;color:var(--g1)}footer b{color:var(--ink)}
body.f-유치 [data-tr]:not([data-tr~="유치"]),body.f-전시 [data-tr]:not([data-tr~="전시"]){display:none}
@media(max-width:980px){.hero{grid-template-columns:minmax(0,1fr)}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:680px){.topics,.tp.full ul{grid-template-columns:1fr}.cards{grid-template-columns:1fr}.hl .tt{font-size:22px}.hl{padding:16px}.etc ul{columns:1}h1{font-size:23px}.hr{text-align:left}}
"""

JS = """
document.querySelectorAll('.flt button').forEach(function(b){b.addEventListener('click',function(){
document.querySelectorAll('.flt button').forEach(function(x){x.classList.toggle('on',x===b)});
document.body.className=b.dataset.f?'f-'+b.dataset.f:'';});});
"""


def esc(s):
    return html.escape(s or "", quote=True)


def clean_title(t, media):
    t = (t or "").strip()
    while media and t.endswith(" - " + media):
        t = t[: -len(" - " + media)].strip()
    return re.sub(r"\s+", " ", t)


MAJOR = ["연합뉴스", "뉴스1", "뉴시스", "KBS", "MBC", "SBS", "YTN", "한국경제", "매일경제", "서울경제", "머니투데이",
         "조선일보", "중앙일보", "동아일보", "한겨레", "경향신문", "한국일보", "아시아경제", "파이낸셜뉴스", "이데일리", "헤럴드경제", "아주경제", "국민일보", "세계일보"]


def grams(t):
    s = re.sub(r"[\s\W_]+", "", t.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def toks(t):
    t = re.sub(r"\[[^\]]*\]", " ", t)
    return {w for w in re.findall(r"[가-힣A-Za-z0-9]+", t) if len(w) >= 2}


def same_story(a, b):
    """bigram 겹침 계수 0.45 이상 또는 2글자 이상 단어 4개 이상 공유"""
    inter = len(a["g"] & b["g"])
    if inter / (min(len(a["g"]), len(b["g"])) or 1) >= 0.45:
        return True
    return len(a["t"] & b["t"]) >= 4


def cluster(rows):
    """같은 사안 묶기: 보도일 2일 이내 + 그룹 안 아무 기사와 same_story (최대 12건과 비교)"""
    groups = []
    for r in rows:
        r["g"], r["t"] = grams(r["title"]), toks(r["title"])
        d = date.fromisoformat(r["date"])
        hit = None
        for c in groups:
            if abs((c["d"] - d).days) > 2:
                continue
            if any(same_story(r, m) for m in c["items"][:12]):
                hit = c
                break
        if hit:
            hit["items"].append(r)
        else:
            groups.append({"items": [r], "d": d})
    out = []
    for c in groups:
        its = c["items"]
        cats = Counter(i["category"] for i in its if i["category"] != "기타")
        if cats:
            top = max(cats.values())
            cat = min((k for k, v in cats.items() if v == top), key=lambda k: CATEGORIES.index(k))
        else:
            cat = "기타"
        medias = []
        for i in its:
            if i["media"] and i["media"] not in medias:
                medias.append(i["media"])
        rep = sorted(its, key=lambda i: (i["media"] not in MAJOR, len(i["title"]) < 14, abs(len(i["title"]) - 34)))[0]
        out.append({
            "title": rep["title"], "url": rep["url"], "media": rep["media"] or (medias[0] if medias else ""),
            "n": max(len(medias), 1), "date": max(i["date"] for i in its), "cat": cat,
            "tracks": sorted({TRACK_TAG.get(i["track"], "") for i in its} - {""}),
            "items": its,
        })
    return out


def score(c, latest):
    age = (latest - date.fromisoformat(c["date"])).days
    return WEIGHT.get(c["cat"], 0) * 2 + min(c["n"], 10) * 1.2 - age * 2


def mdate(d):
    return f"{int(d[5:7])}.{int(d[8:10])}"


def src_line(c, cls="src"):
    more = f" 外 {c['n'] - 1}개 매체" if c["n"] > 1 else ""
    return f'<span class="{cls}"><b>{esc(c["media"])}</b>{more} · {mdate(c["date"])}</span>'


def tags(c):
    return "".join(f'<span class="tg">{t}</span>' for t in c["tracks"])


def chip(cat):
    return f'<span class="chip" style="background:{COLOR.get(cat, "#A6A3A1")}">{esc(cat)}</span>'


def dtr(c):
    return f' data-tr="{" ".join(c["tracks"])}"'


def item_li(c):
    more = f'<span class="many">外 {c["n"] - 1}개 매체</span>' if c["n"] > 1 else ""
    return (f'<li{dtr(c)}><a class="tt" href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["title"])}</a>'
            f'<div class="m"><span>{esc(c["media"])}</span>{more}<span>· {mdate(c["date"])}</span>{tags(c)}</div></li>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()

    con = connect()
    now = now_kst()
    since = (now - timedelta(days=a.days - 1)).strftime("%Y-%m-%d")
    raw = con.execute(
        "select url,track,title,media,date,category from news where date>=? and date<=? "
        "order by date desc, collected_at desc", (since, now.strftime("%Y-%m-%d"))).fetchall()
    total, last = con.execute("select count(*), max(collected_at) from news").fetchone()
    today_new = con.execute("select count(*) from news where substr(collected_at,1,10)=?",
                            (now.strftime("%Y-%m-%d"),)).fetchone()[0]
    briefs = list_briefings()

    rows = [{"url": u, "track": t, "title": clean_title(ti, m), "media": m or "", "date": d, "category": c or "기타"}
            for u, t, ti, m, d, c in raw if d]
    clusters = cluster(rows)
    latest = max((date.fromisoformat(c["date"]) for c in clusters), default=now.date())
    for c in clusters:
        c["score"] = score(c, latest)
    clusters.sort(key=lambda c: -c["score"])

    # 헤드라인 1건 + 주요 뉴스 4건 (전시회 안내·기타 제외, 같은 주제 최대 2건)
    pool = [c for c in clusters if c["cat"] not in ("기타", "전시회 개최·참가")]
    head = pool[0] if pool else None
    feats, per = [], Counter()
    for c in pool[1:]:
        if per[c["cat"]] >= 2:
            continue
        feats.append(c)
        per[c["cat"]] += 1
        if len(feats) == 4:
            break
    shown = {id(c) for c in ([head] if head else []) + feats}

    # ---- 헤드라인
    if head:
        rel = [i for i in head["items"] if i["url"] != head["url"]][:4]
        rel_html = "".join(
            f'<li><span>{esc(i["media"])}</span><a href="{esc(i["url"])}" target="_blank" rel="noopener">{esc(i["title"])}</a></li>'
            for i in rel)
        rel_html = f'<ul class="rel">{rel_html}</ul>' if rel_html else ""
        hero_l = (f'<article class="hl"><div class="lbl">오늘의 헤드라인</div>'
                  f'<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">{chip(head["cat"])}{tags(head)}</div>'
                  f'<a class="tt" href="{esc(head["url"])}" target="_blank" rel="noopener">{esc(head["title"])}</a>'
                  f'{src_line(head)}{rel_html}</article>')
    else:
        hero_l = '<article class="hl"><div class="lbl">오늘의 헤드라인</div><p class="empty">최근 수집된 MICE 관련 기사가 없음</p></article>'

    # ---- 지표 + 주제 구성 막대
    cat_cnt = Counter(c["cat"] for c in clusters if c["cat"] != "기타")
    tot_cat = sum(cat_cnt.values()) or 1
    cb = "".join(f'<i style="width:{cat_cnt[k] / tot_cat * 100:.2f}%;background:{COLOR[k]}"></i>' for k in CATEGORIES if cat_cnt[k])
    lg = "".join(f'<span><i style="background:{COLOR[k]}"></i>{esc(k)} {cat_cnt[k]}</span>' for k in CATEGORIES if cat_cnt[k])
    by_tr = " · ".join(f"{t} {sum(1 for r in rows if r['track'] == t):,}" for t in TRACKS)
    hero_r = (f'<aside class="kp">'
              f'<div><b>{today_new:,}</b><span>오늘 신규 수집</span><small>최종 {esc((last or "-")[5:16])} KST</small></div>'
              f'<div><b>{len(clusters):,}</b><span>최근 {a.days}일 사안</span><small>기사 {len(rows):,}건 묶음</small></div>'
              f'<div><b>{total:,}</b><span>누적 수집</span><small>{esc(by_tr)}</small></div>'
              f'<div><b>{len(briefs):,}</b><span>일일 브리핑</span><small><a href="briefings/" style="text-decoration:underline">모음 보기</a></small></div>'
              f'<div class="cats"><span>주제 구성</span><div class="cb">{cb}</div><div class="lg">{lg}</div></div></aside>')

    # ---- 주요 뉴스
    cards = "".join(
        f'<a class="card" style="--c:{COLOR[c["cat"]]}" href="{esc(c["url"])}" target="_blank" rel="noopener"{dtr(c)}>'
        f'<div style="display:flex;gap:5px;flex-wrap:wrap">{chip(c["cat"])}{tags(c)}</div>'
        f'<span class="tt">{esc(c["title"])}</span>{src_line(c)}</a>' for c in feats)

    # ---- 주제별 동향
    nav, boxes = [], []
    for k in CATEGORIES:
        cs = [c for c in clusters if c["cat"] == k and id(c) not in shown]
        if not cs and k == "전시회 개최·참가":
            continue
        slug = f"t{CATEGORIES.index(k)}"
        nav.append(f'<a href="#{slug}"><i style="background:{COLOR[k]}"></i>{esc(k)}<em>{len(cs)}</em></a>')
        full = k == "전시회 개최·참가"
        limit = 10 if full else 7
        lis = "".join(item_li(c) for c in cs[:limit])
        rest = "".join(item_li(c) for c in cs[limit:])
        body = f"<ul>{lis}</ul>" if lis else '<div class="empty">최근 보도 없음</div>'
        if rest:
            body += f'<details class="more"><summary>{len(cs) - limit}건 더 보기</summary><ul>{rest}</ul></details>'
        boxes.append(f'<section class="tp{" full" if full else ""}" id="{slug}"><h3><i style="background:{COLOR[k]}"></i>{esc(k)}'
                     f'<small>{DESC.get(k, "")}</small><b>{len(cs)}건</b></h3>{body}</section>')

    etc = [c for c in clusters if c["cat"] == "기타"]
    etc_html = ""
    if etc:
        etc_li = "".join(f'<li{dtr(c)}><a href="{esc(c["url"])}" target="_blank" rel="noopener">{esc(c["title"])}</a> '
                         f'<span>{esc(c["media"])} · {mdate(c["date"])}</span></li>' for c in etc)
        etc_html = (f'<details class="etc"><summary>분류 외 기사 {len(etc)}건 (자동 수집 잡음 포함) 펼치기</summary>'
                    f'<ul>{etc_li}</ul></details>')

    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MICE 이슈 레이더</title><meta name="description" content="한국관광공사 MICE 산업 일일 이슈 모니터링"><style>{CSS}</style></head><body>
<header><div class="w"><div><div class="org">발주 <b>한국관광공사</b> · 수행 <b>(주)서던포스트</b></div><h1>MICE 이슈 레이더</h1></div>
<div class="hr"><div class="d">{now:%Y. %m. %d.}</div><div class="s">({WD[now.weekday()]}) 최근 {a.days}일 · <a href="briefings/" style="text-decoration:underline">일일 브리핑 {len(briefs)}건</a></div></div></div></header>
<div class="bar"><i></i><i></i><i></i><i></i></div>
<div class="strip"><div class="w"><div class="flt"><button class="on" data-f="">전체</button><button data-f="유치">MICE 유치</button><button data-f="전시">전시·컨벤션</button></div>
<span class="meta">보도일 <b>{since[5:].replace('-', '.')} ~ {now:%m.%d}</b> · 같은 사안은 1건으로 묶음 · 매일 08:30 KST 자동수집</span></div></div>
<main class="w">
<div class="hero">{hero_l}{hero_r}</div>
<section class="sec"><div class="sh"><div><div class="lbl">주목</div><h2>주요 뉴스</h2></div><span class="n">주제 중요도 · 보도 매체 수 · 최신성 기준 자동 선정</span></div>
<div class="cards">{cards or '<p class="empty">해당 없음</p>'}</div></section>
<section class="sec"><div class="sh"><div><div class="lbl">주제별</div><h2>주제별 동향</h2></div><span class="n">주제를 누르면 해당 묶음으로 이동</span></div>
<nav class="nav">{''.join(nav)}</nav><div class="topics">{''.join(boxes)}</div>{etc_html}</section>
</main>
<footer><div class="w"><span>자료원 : Google News RSS 자동수집 (MICE 유치·전시·컨벤션 2개 트랙) · 주제 분류와 주요 뉴스 선정은 규칙 기반 자동 처리 · 생성 {now:%Y-%m-%d %H:%M} KST</span>
<span>발주 한국관광공사 · 수행 <b>(주)서던포스트</b></span></div></footer>
<script>{JS}</script>
</body></html>"""
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"docs/index.html 생성: 최근 {a.days}일 기사 {len(rows)}건 → 사안 {len(clusters)}건, 브리핑 {len(briefs)}건")


if __name__ == "__main__":
    main()
