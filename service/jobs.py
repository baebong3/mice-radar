"""일일 작업과 관리 명령

  python -m service.jobs daily              수집 → 요약 → 메일 발송 (cron에서 하루 한 번)
  python -m service.jobs set-plan 이메일 요금제   요금제 변경 (결제 연동 전 수동 처리)
  python -m service.jobs stats              가입자·주제 현황
"""
import argparse
import sys
import time

from . import collector, config, mailer, reports
from .db import connect


def active_topics(con):
    return con.execute(
        "select distinct t.id, t.query from topics t join subscriptions s on s.topic_id=t.id"
        " join users u on u.id=s.user_id order by t.id").fetchall()


def refresh_topic(con, topic_id, query, day=None, fetcher=None):
    """주제 하나를 수집하고 그날 요약을 다시 만든다."""
    day = day or config.today_kst()
    n = collector.collect_topic(con, topic_id, query, day, fetcher)
    reports.build_digest(con, topic_id, query, day)
    return n


def refresh_topic_by_id(topic_id):
    """주제를 새로 등록했을 때 웹에서 바로 부르는 백그라운드 작업"""
    con = connect()
    try:
        row = con.execute("select id, query from topics where id=?", (topic_id,)).fetchone()
        if row:
            refresh_topic(con, row["id"], row["query"])
    finally:
        con.close()


def send_reports(con, day):
    sent = skipped = failed = 0
    users = con.execute(
        "select * from users u where mail_on=1 and exists(select 1 from subscriptions s where s.user_id=u.id)"
        " and not exists(select 1 from deliveries d where d.user_id=u.id and d.date=?)", (day,)).fetchall()
    for u in users:
        blocks = reports.user_report(con, u["id"], day)
        status = "empty"
        if any(b["count"] for b in blocks):
            unsub = f"{config.BASE_URL}/unsubscribe?t={u['unsub_token']}"
            subject, text, html = reports.render_email(blocks, day, unsub)
            try:
                status = mailer.send(u["email"], subject, text, html, {
                    "List-Unsubscribe": f"<{unsub}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"})
                sent += 1
            except Exception as e:  # noqa: BLE001
                print(f"  ! 발송 실패 user={u['id']}: {e}", file=sys.stderr)
                failed += 1
                continue  # 기록하지 않아 다음 실행 때 다시 보낸다
        else:
            skipped += 1
        con.execute("insert or ignore into deliveries(user_id,date,status,sent_at) values(?,?,?,?)",
                    (u["id"], day, status, config.now_kst().strftime("%Y-%m-%d %H:%M:%S")))
        con.commit()
    return {"sent": sent, "empty": skipped, "failed": failed}


def daily(con=None, fetcher=None, pause=1.0):
    own = con is None
    con = con or connect()
    day = config.today_kst()
    topics = active_topics(con)
    ok = fail = 0
    for t in topics:
        n = refresh_topic(con, t["id"], t["query"], day, fetcher)
        if n is None:
            fail += 1
        else:
            ok += 1
        time.sleep(pause)
    result = {"date": day, "topics": len(topics), "collect_ok": ok, "collect_fail": fail,
              **send_reports(con, day)}
    con.execute("delete from login_tokens where expires_at < ?", (config.now_kst().isoformat(),))
    con.execute("delete from sessions where expires_at < ?", (config.now_kst().isoformat(),))
    con.execute("delete from articles where collected_on < date(?, '-90 day')", (day,))
    con.commit()
    if own:
        con.close()
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("daily")
    sp = sub.add_parser("set-plan")
    sp.add_argument("email")
    sp.add_argument("plan", choices=list(config.PLAN_LIMIT))
    sub.add_parser("stats")
    a = ap.parse_args()
    if a.cmd == "daily":
        print(daily())
        return
    con = connect()
    if a.cmd == "set-plan":
        cur = con.execute("update users set plan=? where email=?", (a.plan, a.email.strip().lower()))
        con.commit()
        print("변경했습니다." if cur.rowcount else "해당 이메일의 가입자가 없습니다.")
    elif a.cmd == "stats":
        for label, q in [("가입자", "select count(*) from users"),
                         ("수집 중인 주제", "select count(distinct topic_id) from subscriptions"),
                         ("구독", "select count(*) from subscriptions")]:
            print(f"{label}: {con.execute(q).fetchone()[0]}")
        for r in con.execute("select plan, count(*) from users group by plan"):
            print(f"  요금제 {r[0]}: {r[1]}명")


if __name__ == "__main__":
    main()
