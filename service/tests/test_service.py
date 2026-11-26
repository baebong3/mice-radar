"""python -m unittest service.tests.test_service  (저장소 루트에서 실행)"""
import glob
import html
import os
import pathlib
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

_TMP = tempfile.mkdtemp()
os.environ.update(RADAR_DB=os.path.join(_TMP, "t.db"), RADAR_OUTBOX=os.path.join(_TMP, "outbox"),
                  RADAR_DEV="1", SMTP_HOST="", RADAR_BASE_URL="http://testserver")
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

from fastapi.testclient import TestClient  # noqa: E402

from service import collector, config, jobs, reports, summarize, web  # noqa: E402
from service.db import connect  # noqa: E402


def rss(*titles):
    titles = [html.escape(t) for t in titles]
    items = "".join(
        f"<item><title>{t} - 테스트일보</title><link>https://example.com/{abs(hash(t))}</link>"
        f"<pubDate>Thu, 26 Nov 2026 01:00:00 GMT</pubDate><description>&lt;a&gt;{t}&lt;/a&gt; 발췌</description>"
        f"<source url='https://example.com'>테스트일보</source></item>" for t in titles)
    return f"<rss><channel>{items}</channel></rss>".encode()


def fake_fetch(url):
    return rss("환율 급등 <script>alert(1)</script>", "두 번째 기사", "두 번째  기사")


collector.fetch = fake_fetch  # 주제 등록 직후 백그라운드 수집도 가짜 RSS를 쓰게 한다


def login(client, email):
    r = client.post("/login", data={"email": email})
    token = re.search(r"/auth\?token=([\w-]+)", r.text).group(1)
    assert client.get(f"/auth?token={token}").status_code == 200  # 미리 열어도 소모되지 않는다
    r = client.post("/auth", data={"token": token}, follow_redirects=False)
    assert r.headers["location"] == "/app"
    return token


def csrf(client):
    return re.search(r'name="csrf" value="([^"]+)"', client.get("/settings").text).group(1)


def add(client, q, token=None):
    return client.post("/topics", data={"query": q, "csrf": token or csrf(client)}, follow_redirects=False)


class ServiceTest(unittest.TestCase):
    def setUp(self):
        con = connect()
        for t in ("users", "login_tokens", "sessions", "topics", "subscriptions", "articles", "digests", "deliveries"):
            con.execute(f"delete from {t}")
        con.commit()
        con.close()
        for f in glob.glob(os.path.join(config.OUTBOX, "*.eml")):
            os.remove(f)
        self.c = TestClient(web.app)

    def test_parse_and_dedupe(self):
        items = collector.parse(fake_fetch(""))
        self.assertEqual(items[1]["title"], "두 번째 기사")
        self.assertEqual(items[1]["media"], "테스트일보")
        con = connect()
        con.execute("insert into topics(id,query,norm,created_at) values(1,'x','x','')")
        self.assertEqual(collector.save(con, 1, items, "2026-11-26"), 2)  # 띄어쓰기만 다른 제목은 하나로
        self.assertEqual(collector.save(con, 1, items, "2026-11-27"), 0)
        con.close()

    def test_login_token_single_use(self):
        token = login(self.c, "a@example.com")
        r = TestClient(web.app).post("/auth", data={"token": token}, follow_redirects=False)
        self.assertIn("m=expired", r.headers["location"])

    def test_requires_login_and_csrf(self):
        anon = TestClient(web.app)
        self.assertEqual(anon.get("/app", follow_redirects=False).headers["location"], "/login")
        login(self.c, "a@example.com")
        self.assertIn("m=form", add(self.c, "위조 요청", token="wrong").headers["location"])
        self.assertNotIn("위조 요청", self.c.get("/app").text)

    def test_topic_limit_and_plan(self):
        login(self.c, "a@example.com")
        self.assertIn("m=bad", add(self.c, "a").headers["location"])
        for i in range(5):
            self.assertIn("m=added", add(self.c, f"주제 {i}").headers["location"])
        self.assertIn("m=dup", add(self.c, "주제  0").headers["location"])
        self.assertIn("m=limit", add(self.c, "여섯 번째").headers["location"])
        con = connect()
        con.execute("update users set plan='plus'")
        con.commit()
        con.close()
        self.assertIn("m=added", add(self.c, "여섯 번째").headers["location"])

    def test_dashboard_escapes_and_shows_articles(self):
        login(self.c, "a@example.com")
        add(self.c, "반도체 <b>수출</b>")
        page = self.c.get("/app").text
        self.assertIn("새 기사 2건", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertNotIn("<b>수출</b>", page)

    def test_topics_are_private_and_shared_collection(self):
        login(self.c, "a@example.com")
        add(self.c, "공유 주제")
        other = TestClient(web.app)
        login(other, "b@example.com")
        add(other, "공유 주제")
        con = connect()
        self.assertEqual(con.execute("select count(*) from topics").fetchone()[0], 1)
        tid = con.execute("select id from topics").fetchone()[0]
        con.close()
        other.post(f"/topics/{tid}/delete", data={"csrf": csrf(other)})
        self.assertIn("공유 주제", self.c.get("/app").text)  # 남의 삭제가 내 구독을 지우지 않는다
        self.c.post(f"/topics/{tid}/delete", data={"csrf": csrf(self.c)})
        con = connect()
        self.assertEqual(con.execute("select count(*) from topics").fetchone()[0], 0)
        self.assertEqual(con.execute("select count(*) from articles").fetchone()[0], 0)
        con.close()

    def test_daily_sends_once_and_unsubscribe(self):
        login(self.c, "a@example.com")
        add(self.c, "반도체")
        r = jobs.daily(fetcher=fake_fetch, pause=0)
        self.assertEqual((r["sent"], r["failed"], r["collect_ok"]), (1, 0, 1))
        self.assertEqual(jobs.daily(fetcher=fake_fetch, pause=0)["sent"], 0)  # 같은 날 두 번 보내지 않는다
        mails = [pathlib.Path(f).read_text(encoding="utf-8", errors="replace")
                 for f in glob.glob(os.path.join(config.OUTBOX, "*.eml"))]
        report = [m for m in mails if "List-Unsubscribe" in m]
        self.assertEqual(len(report), 1)
        con = connect()
        token = con.execute("select unsub_token from users").fetchone()[0]
        self.assertEqual(self.c.get(f"/unsubscribe?t={token}").status_code, 200)
        self.assertEqual(con.execute("select mail_on from users").fetchone()[0], 1)  # GET만으로는 꺼지지 않는다
        self.c.post(f"/unsubscribe?t={token}")
        self.assertEqual(con.execute("select mail_on from users").fetchone()[0], 0)
        con.execute("delete from deliveries")
        con.commit()
        con.close()
        self.assertEqual(jobs.daily(fetcher=fake_fetch, pause=0)["sent"], 0)

    def test_collect_failure_and_empty_day(self):
        login(self.c, "a@example.com")
        add(self.c, "반도체")
        con = connect()
        con.execute("delete from articles")
        con.execute("delete from digests")
        con.commit()
        con.close()
        r = jobs.daily(fetcher=lambda url: None, pause=0)
        self.assertEqual((r["collect_fail"], r["sent"], r["empty"]), (1, 0, 1))

    def test_email_render_escapes(self):
        blocks = [{"query": "<i>q</i>", "count": 1, "method": "coverage", "articles": [],
                   "items": [{"title": "<u>t</u>", "summary": "<b>x</b>", "url": 'https://e.com/?a="b"',
                              "media": "m", "count": 3}]}]
        subject, text, body = reports.render_email(blocks, "2026-11-26", "http://testserver/unsubscribe?t=1")
        for raw in ("<i>q</i>", "<b>x</b>", "<u>t</u>", '?a="b"'):
            self.assertNotIn(raw, body)
        self.assertIn("m 외 2건", text)

    def test_top3_by_coverage(self):
        def art(i, title):
            return {"title": title, "url": f"https://e.com/{i}", "media": f"매체{i}", "summary": ""}
        arts = [art(1, "단독 보도 하나"), art(2, "정부, 반도체 특별법 시행령 입법예고"),
                art(3, "반도체 특별법 시행령 입법예고…정부 발표"), art(4, "환율 1400원 돌파"),
                art(5, "정부 반도체 특별법 시행령 입법 예고"), art(6, "원·달러 환율 1400원 돌파 마감"),
                art(7, "또 다른 단독"), art(8, "세 번째 단독")]
        items, method = summarize.summarize("q", arts)
        self.assertEqual(method, "coverage")
        self.assertEqual([(i["url"][-1], i["count"]) for i in items], [("2", 3), ("4", 2), ("1", 1)])
        self.assertEqual(summarize.summarize("q", []), ([], "none"))
        self.assertEqual(len(summarize.summarize("q", arts[:1])[0]), 1)

    def test_llm_response_parsing(self):
        arts = [{"title": f"제목{i}", "url": f"https://e.com/{i}", "media": "m", "summary": ""} for i in range(1, 6)]
        text = ('{"items":[{"headline":"가","summary":"요약","articles":[3,1]},{"headline":"나","summary":"","articles":[99]},'
                '{"headline":"다","summary":"s","articles":[2]},{"headline":"라","summary":"s","articles":[4]},'
                '{"headline":"마","summary":"s","articles":[5]}]}')
        items = summarize.items_from_json(text, arts)
        self.assertEqual([(i["title"], i["url"][-1], i["count"]) for i in items], [("가", "3", 2), ("다", "2", 1), ("라", "4", 1)])
        self.assertEqual(summarize.items_from_json("고장난 응답", arts), [])

    def test_pages_render(self):
        login(self.c, "a@example.com")
        self.assertIn("첫 주제를 골라", self.c.get("/app").text)
        add(self.c, "반도체")
        self.assertEqual(self.c.get("/app").text.count('class="rank"'), 2)
        svg = self.c.get("/cover.svg", params={"q": "반도체"})
        self.assertEqual(svg.headers["content-type"], "image/svg+xml")
        self.assertEqual(svg.text, self.c.get("/cover.svg", params={"q": " 반도체 "}).text)  # 같은 주제는 같은 그림
        self.assertNotEqual(svg.text, self.c.get("/cover.svg", params={"q": "환율"}).text)
        ET.fromstring(svg.text)
        for path in ("/topics", "/settings", "/plans"):
            self.assertEqual(self.c.get(path).status_code, 200, path)
        self.assertEqual(TestClient(web.app).get("/").text.count('class="rank"'), 3)

    def test_account_delete(self):
        login(self.c, "a@example.com")
        add(self.c, "반도체")
        self.c.post("/account/delete", data={"csrf": csrf(self.c)})
        con = connect()
        for t in ("users", "sessions", "subscriptions", "topics", "articles"):
            self.assertEqual(con.execute(f"select count(*) from {t}").fetchone()[0], 0, t)
        con.close()


if __name__ == "__main__":
    unittest.main()
