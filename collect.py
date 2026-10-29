"""Google News RSS 수집기 - 트랙별 검색어로 최근 기사를 모아 data/news.db에 누적

사용: python3 radar/collect.py [--when 2d] [--rss-file 파일.xml --track 'MICE 유치']
"""
import argparse
import html
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import KST, QUERIES, classify, connect, now_kst  # noqa: E402

UA = "Mozilla/5.0 (compatible; mice-radar/1.0; +https://baebong3.github.io/mice-radar/)"


def rss_url(q, when):
    query = f"{q} when:{when}"
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"})


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                print(f"  ! 수집 실패: {e}", file=sys.stderr)
                return None
            time.sleep(2 * (i + 1))


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def parse(xml_bytes):
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  ! RSS 파싱 실패: {e}", file=sys.stderr)
        return items
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        src = it.find("source")
        media = (src.text or "").strip() if src is not None else ""
        if media and title.endswith(" - " + media):
            title = title[: -len(" - " + media)].strip()
        elif not media and " - " in title:
            title, media = title.rsplit(" - ", 1)
        pub = it.findtext("pubDate") or ""
        try:
            date = parsedate_to_datetime(pub).astimezone(KST).strftime("%Y-%m-%d")
        except Exception:  # noqa: BLE001
            date = ""
        summary = strip_tags(it.findtext("description") or "")
        if summary.startswith(title):
            summary = summary[len(title):].strip()
        if media and summary.endswith(media):
            summary = summary[: -len(media)].strip()
        if title and link:
            items.append({"title": html.unescape(title), "url": link, "media": media,
                          "date": date, "summary": summary[:400]})
    return items


def norm_title(t):
    return re.sub(r"[\s\W_]+", "", t)[:40]


def save(con, track, query, items, collected_at):
    seen = {norm_title(t) + "|" + (d or "") for t, d in con.execute(
        "select title, date from news where date >= date('now','-10 day')")}
    n = 0
    for it in items:
        key = norm_title(it["title"]) + "|" + it["date"]
        if key in seen:
            continue
        cur = con.execute(
            "insert or ignore into news(url,track,title,media,date,summary,note,category,source,collected_at)"
            " values(?,?,?,?,?,?,?,?,?,?)",
            (it["url"], track, it["title"], it["media"], it["date"], it["summary"],
             f"검색어: {query}", classify(it["title"], it["summary"]), "google_news_rss", collected_at))
        if cur.rowcount:
            n += 1
            seen.add(key)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--when", default="2d", help="Google News 기간 (예: 1d, 2d, 7d)")
    ap.add_argument("--rss-file", help="시험용 로컬 RSS 파일")
    ap.add_argument("--track", default="MICE 유치")
    a = ap.parse_args()

    con = connect()
    collected_at = now_kst().strftime("%Y-%m-%d %H:%M:%S")
    total = {}
    if a.rss_file:
        with open(a.rss_file, "rb") as f:
            items = parse(f.read())
        total[a.track] = save(con, a.track, "(로컬 파일)", items, collected_at)
    else:
        for track, qs in QUERIES.items():
            total[track] = 0
            for q in qs:
                data = fetch(rss_url(q, a.when))
                if not data:
                    continue
                items = parse(data)
                n = save(con, track, q, items, collected_at)
                total[track] += n
                print(f"[{track}] {q}: {len(items)}건 중 신규 {n}건")
                time.sleep(1)
    con.commit()
    allc = con.execute("select count(*) from news").fetchone()[0]
    print(f"신규 {sum(total.values())}건 {total} / 누적 {allc}건 / 수집시각 {collected_at} KST")


if __name__ == "__main__":
    main()
