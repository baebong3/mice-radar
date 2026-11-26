"""주제별 요약 저장과 사용자별 리포트 조립"""
import json
from html import escape

from . import config
from .summarize import summarize


def build_digest(con, topic_id, query, day, summarizer=summarize):
    """그날 새로 들어온 기사로 주제 요약을 만들어 저장한다. 기사 수를 돌려준다."""
    arts = [dict(r) for r in con.execute(
        "select title, media, summary from articles where topic_id=? and collected_on=? order by id",
        (topic_id, day))]
    lines, method = summarizer(query, arts)
    con.execute(
        "insert into digests(topic_id,date,lines,method,article_count) values(?,?,?,?,?)"
        " on conflict(topic_id,date) do update set lines=excluded.lines, method=excluded.method,"
        " article_count=excluded.article_count",
        (topic_id, day, json.dumps(lines, ensure_ascii=False), method, len(arts)))
    con.commit()
    return len(arts)


def topic_block(con, topic_id, query, day=None):
    """주제 하나의 요약과 기사 목록. day가 없으면 가장 최근 요약."""
    if day:
        d = con.execute("select * from digests where topic_id=? and date=?", (topic_id, day)).fetchone()
    else:
        d = con.execute("select * from digests where topic_id=? order by date desc limit 1", (topic_id,)).fetchone()
    block = {"id": topic_id, "query": query, "date": d["date"] if d else None,
             "lines": json.loads(d["lines"]) if d else [], "method": d["method"] if d else "none",
             "count": d["article_count"] if d else 0, "articles": []}
    if d:
        block["articles"] = [dict(r) for r in con.execute(
            "select title, url, media, date from articles where topic_id=? and collected_on=? order by id limit ?",
            (topic_id, d["date"], config.ARTICLES_PER_TOPIC))]
    return block


def user_topics(con, user_id):
    return con.execute(
        "select t.id, t.query, t.last_collected_at from subscriptions s join topics t on t.id=s.topic_id"
        " where s.user_id=? order by s.created_at, t.id", (user_id,)).fetchall()


def user_report(con, user_id, day=None):
    return [topic_block(con, t["id"], t["query"], day) for t in user_topics(con, user_id)]


def render_email(blocks, day, unsub_url):
    """(제목, 본문 텍스트, 본문 HTML)"""
    total = sum(b["count"] for b in blocks)
    subject = f"[{config.SERVICE_NAME}] {day} 일일 리포트 · 새 기사 {total}건"
    text = [f"{config.SERVICE_NAME} 일일 리포트 ({day})", ""]
    html = [
        '<div style="max-width:640px;margin:0 auto;font-family:-apple-system,\'Malgun Gothic\',sans-serif;'
        'color:#1b2430;line-height:1.6">',
        f'<p style="font-size:13px;color:#6b7785;margin:0">{escape(day)} 일일 리포트</p>',
        f'<h1 style="font-size:22px;margin:4px 0 20px">{escape(config.SERVICE_NAME)}</h1>',
    ]
    for b in blocks:
        text += [f"■ {b['query']} (새 기사 {b['count']}건)"]
        html.append(
            f'<h2 style="font-size:17px;margin:24px 0 6px;padding-top:14px;border-top:2px solid #14324f">'
            f'{escape(b["query"])} <span style="font-size:13px;font-weight:400;color:#6b7785">'
            f'새 기사 {b["count"]}건</span></h2>')
        if not b["count"]:
            text += ["  새 기사가 없습니다.", ""]
            html.append('<p style="margin:0;color:#6b7785">새 기사가 없습니다.</p>')
            continue
        label = "핵심 이슈" if b["method"] == "llm" else "주요 기사"
        text += [f"  [{label}]"] + [f"  - {ln}" for ln in b["lines"]] + ["  [기사]"]
        html.append(f'<p style="margin:8px 0 2px;font-size:13px;font-weight:700;color:#d2452d">{label}</p><ul '
                    'style="margin:0;padding-left:20px">'
                    + "".join(f"<li>{escape(ln)}</li>" for ln in b["lines"]) + "</ul>")
        html.append('<p style="margin:12px 0 2px;font-size:13px;font-weight:700;color:#6b7785">기사</p>'
                    '<ul style="margin:0;padding-left:20px;font-size:14px">')
        for a in b["articles"]:
            text.append(f"  - {a['title']} ({a['media']}) {a['url']}")
            html.append(f'<li><a href="{escape(a["url"], quote=True)}" style="color:#14324f">{escape(a["title"])}</a>'
                        f' <span style="color:#6b7785">{escape(a["media"] or "")}</span></li>')
        html.append("</ul>")
        text.append("")
    app_url = f"{config.BASE_URL}/app"
    text += [f"주제 관리: {app_url}", f"수신 거부: {unsub_url}"]
    html.append(
        f'<p style="margin-top:28px;padding-top:14px;border-top:1px solid #dde3ea;font-size:12px;color:#6b7785">'
        f'<a href="{escape(app_url, quote=True)}" style="color:#6b7785">주제 관리</a> · '
        f'<a href="{escape(unsub_url, quote=True)}" style="color:#6b7785">수신 거부</a></p></div>')
    return subject, "\n".join(text), "".join(html)
