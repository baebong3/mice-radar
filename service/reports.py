"""주제별 핵심 뉴스 저장과 사용자별 리포트 조립"""
import json
from html import escape

from . import config
from .summarize import summarize


def build_digest(con, topic_id, query, day, summarizer=summarize):
    """그날 새로 들어온 기사로 핵심 뉴스를 골라 저장한다. 기사 수를 돌려준다."""
    arts = [dict(r) for r in con.execute(
        "select title, url, media, summary from articles where topic_id=? and collected_on=? order by id",
        (topic_id, day))]
    items, method = summarizer(query, arts)
    con.execute(
        "insert into digests(topic_id,date,items,method,article_count) values(?,?,?,?,?)"
        " on conflict(topic_id,date) do update set items=excluded.items, method=excluded.method,"
        " article_count=excluded.article_count",
        (topic_id, day, json.dumps(items, ensure_ascii=False), method, len(arts)))
    con.commit()
    return len(arts)


def topic_block(con, topic_id, query, day=None):
    """주제 하나의 핵심 뉴스와 기사 목록. day가 없으면 기사가 있었던 가장 최근 날."""
    if day:
        d = con.execute("select * from digests where topic_id=? and date=?", (topic_id, day)).fetchone()
    else:
        d = con.execute("select * from digests where topic_id=? order by article_count>0 desc, date desc limit 1",
                        (topic_id,)).fetchone()
    block = {"id": topic_id, "query": query, "date": d["date"] if d else None,
             "items": json.loads(d["items"]) if d else [], "method": d["method"] if d else "none",
             "count": d["article_count"] if d else 0, "articles": []}
    if d:
        block["articles"] = [dict(r) for r in con.execute(
            "select title, url, media from articles where topic_id=? and collected_on=? order by id limit ?",
            (topic_id, d["date"], config.ARTICLES_PER_TOPIC))]
    return block


def user_topics(con, user_id):
    return con.execute(
        "select t.id, t.query, t.last_collected_at from subscriptions s join topics t on t.id=s.topic_id"
        " where s.user_id=? order by s.created_at, t.id", (user_id,)).fetchall()


def user_report(con, user_id, day=None):
    return [topic_block(con, t["id"], t["query"], day) for t in user_topics(con, user_id)]


def _meta(item):
    more = f" 외 {item['count'] - 1}건" if item["count"] > 1 else ""
    return f"{item['media']}{more}".strip()


def render_email(blocks, day, unsub_url):
    """(제목, 본문 텍스트, 본문 HTML)"""
    blocks = [b for b in blocks if b["count"]] + [b for b in blocks if not b["count"]]
    first = next((b["items"][0]["title"] for b in blocks if b["items"]), "")
    subject = f"[{config.SERVICE_NAME}] {day[5:7]}/{day[8:]} 핵심 뉴스 · {first}"[:120]
    text = [f"{config.SERVICE_NAME} · {day} 핵심 뉴스", ""]
    html = [
        '<div style="max-width:560px;margin:0 auto;font-family:-apple-system,\'Malgun Gothic\',sans-serif;'
        'color:#1b2430;line-height:1.55">',
        f'<p style="font-size:13px;color:#6b7785;margin:0">{escape(day)}</p>',
        '<h1 style="font-size:22px;margin:2px 0 8px">오늘의 핵심 뉴스</h1>',
    ]
    for b in blocks:
        text.append(f"■ {b['query']}")
        html.append(f'<h2 style="font-size:16px;margin:26px 0 4px;padding:6px 10px;background:#14324f;color:#fff;'
                    f'border-radius:6px">{escape(b["query"])}</h2>')
        if not b["count"]:
            text += ["  새 기사가 없습니다.", ""]
            html.append('<p style="margin:8px 0;color:#6b7785;font-size:14px">새 기사가 없습니다.</p>')
            continue
        for i, it in enumerate(b["items"], 1):
            text.append(f"  {i}. {it['title']} ({_meta(it)})")
            if it["summary"]:
                text.append(f"     {it['summary']}")
            text.append(f"     {it['url']}")
            html.append(
                '<table role="presentation" style="border-collapse:collapse;margin:12px 0"><tr>'
                f'<td style="vertical-align:top;padding-right:10px;font-size:22px;font-weight:800;color:#d2452d">{i}</td>'
                f'<td><a href="{escape(it["url"], quote=True)}" style="color:#1b2430;font-weight:700;font-size:16px;'
                f'text-decoration:none">{escape(it["title"])}</a>'
                + (f'<div style="font-size:14px;margin-top:2px">{escape(it["summary"])}</div>' if it["summary"] else "")
                + f'<div style="font-size:12px;color:#6b7785;margin-top:2px">{escape(_meta(it))}</div></td></tr></table>')
        text.append("")
        html.append(f'<p style="margin:0;font-size:12px;color:#6b7785">새 기사 {b["count"]}건 중에서 골랐습니다.</p>')
    app_url = f"{config.BASE_URL}/app"
    text += [f"앱에서 보기: {app_url}", f"수신 거부: {unsub_url}"]
    html.append(
        f'<p style="margin-top:28px;padding-top:14px;border-top:1px solid #dde3ea;font-size:12px;color:#6b7785">'
        f'<a href="{escape(app_url, quote=True)}" style="color:#6b7785">앱에서 전체 기사 보기</a> · '
        f'<a href="{escape(unsub_url, quote=True)}" style="color:#6b7785">수신 거부</a></p></div>')
    return subject, "\n".join(text), "".join(html)
