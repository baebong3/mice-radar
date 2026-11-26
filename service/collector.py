"""주제별 Google News RSS 수집 (radar/collect.py의 수집 방식을 주제 단위로 옮긴 것)"""
import html
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from . import config

UA = "Mozilla/5.0 (compatible; issue-radar/1.0)"


def rss_url(query, when):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} when:{when}", "hl": "ko", "gl": "KR", "ceid": "KR:ko"})


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
        if not media and " - " in title:
            title, media = title.rsplit(" - ", 1)
        while media and title.endswith(" - " + media):
            title = title[: -len(" - " + media)].strip()
        try:
            date = parsedate_to_datetime(it.findtext("pubDate") or "").astimezone(config.KST).strftime("%Y-%m-%d")
        except Exception:  # noqa: BLE001
            date = ""
        summary = strip_tags(it.findtext("description") or "")
        if summary.startswith(title):
            summary = summary[len(title):].strip()
        if media and summary.endswith(media):
            summary = summary[: -len(media)].strip()
        if title and link.startswith(("http://", "https://")):
            items.append({"title": html.unescape(title), "url": link, "media": media,
                          "date": date, "summary": summary[:400]})
    return items


def title_key(t):
    return re.sub(r"[\s\W_]+", "", t)[:40]


def save(con, topic_id, items, day):
    """새 기사만 저장하고 저장 건수를 돌려준다. 같은 제목은 열흘 안에서 한 번만 받는다."""
    seen = {r[0] for r in con.execute(
        "select title_key from articles where topic_id=? and collected_on >= date(?, '-10 day')",
        (topic_id, day))}
    n = 0
    for it in items:
        key = title_key(it["title"])
        if key in seen:
            continue
        cur = con.execute(
            "insert or ignore into articles(topic_id,url,title,title_key,media,date,summary,collected_on)"
            " values(?,?,?,?,?,?,?,?)",
            (topic_id, it["url"], it["title"], key, it["media"], it["date"], it["summary"], day))
        if cur.rowcount:
            n += 1
            seen.add(key)
    con.execute("update topics set last_collected_at=? where id=?",
                (config.now_kst().strftime("%Y-%m-%d %H:%M:%S"), topic_id))
    con.commit()
    return n


def collect_topic(con, topic_id, query, day=None, fetcher=None):
    """주제 하나를 수집한다. 수집에 실패하면 None, 성공하면 새 기사 수."""
    data = (fetcher or fetch)(rss_url(query, config.COLLECT_WHEN))
    if not data:
        return None
    return save(con, topic_id, parse(data), day or config.today_kst())
