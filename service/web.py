"""이슈레이더 웹 앱 (FastAPI)

  uvicorn service.web:app --reload
"""
import hashlib
import os
import re
import secrets
import threading
import time
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import BackgroundTasks, Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, jobs, mailer, reports
from .db import connect

HERE = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(_app):
    if config.SCHEDULER:
        threading.Thread(target=_scheduler, daemon=True).start()
    yield


app = FastAPI(title=config.SERVICE_NAME, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))
templates.env.globals.update(service=config.SERVICE_NAME, plans=config.PLANS)
templates.env.filters["pretty_date"] = config.pretty_date

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s.]{2,}$")
COOKIE = "sid"
MESSAGES = {
    "added": "주제를 등록했습니다. 첫 수집이 끝나면 핵심 뉴스가 나타납니다.",
    "dup": "이미 등록한 주제입니다.",
    "limit": "현재 요금제에서 등록할 수 있는 주제 수를 모두 썼습니다.",
    "bad": "주제는 2~40자로 입력해 주십시오.",
    "removed": "주제를 삭제했습니다.",
    "mail_on": "일일 리포트 메일을 다시 받습니다.",
    "mail_off": "일일 리포트 메일을 받지 않습니다.",
    "expired": "로그인 링크가 만료됐거나 이미 사용됐습니다. 다시 요청해 주십시오.",
    "form": "화면이 오래돼 요청을 처리하지 못했습니다. 다시 시도해 주십시오.",
    "deleted": "계정과 등록 정보를 모두 삭제했습니다.",
}


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def get_db():
    con = connect()
    try:
        yield con
    finally:
        con.close()


def current(request: Request, con):
    """(사용자 행, CSRF 토큰) 또는 (None, None)"""
    sid = request.cookies.get(COOKIE)
    if not sid:
        return None, None
    row = con.execute(
        "select u.*, s.csrf from sessions s join users u on u.id=s.user_id where s.token_hash=? and s.expires_at>?",
        (sha(sid), config.now_kst().isoformat())).fetchone()
    return (row, row["csrf"]) if row else (None, None)


def page(request, name, **ctx):
    ctx.setdefault("user", None)
    ctx["message"] = MESSAGES.get(request.query_params.get("m", ""))
    return templates.TemplateResponse(request, name, ctx)


def go(path, m=None):
    return RedirectResponse(path + (f"?m={m}" if m else ""), status_code=303)


def norm_topic(q):
    q = re.sub(r"\s+", " ", q or "").strip()
    return q, q.lower()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, con=Depends(get_db)):
    user, _ = current(request, con)
    if user:
        return go("/app")
    return page(request, "home.html")


@app.get("/plans", response_class=HTMLResponse)
def plans(request: Request, con=Depends(get_db)):
    user, csrf = current(request, con)
    return page(request, "plans.html", user=user, csrf=csrf, tab="settings")


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return page(request, "login.html")


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(""), con=Depends(get_db)):
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return page(request, "login.html", error="이메일 주소를 확인해 주십시오.", email=email)
    now = config.now_kst()
    recent = con.execute("select count(*) from login_tokens where email=? and created_at>?",
                         (email, (now - timedelta(hours=1)).isoformat())).fetchone()[0]
    link = None
    if recent < config.LOGIN_REQUESTS_PER_HOUR:
        token = secrets.token_urlsafe(32)
        con.execute("insert into login_tokens(token_hash,email,expires_at,created_at) values(?,?,?,?)",
                    (sha(token), email, (now + timedelta(minutes=config.LOGIN_TOKEN_MINUTES)).isoformat(),
                     now.isoformat()))
        con.commit()
        link = f"{config.BASE_URL}/auth?token={token}"
        try:
            mailer.send(email, f"[{config.SERVICE_NAME}] 로그인 링크",
                        f"아래 링크를 열면 로그인됩니다. {config.LOGIN_TOKEN_MINUTES}분 동안 한 번만 쓸 수 있습니다.\n\n{link}\n\n"
                        "요청한 적이 없다면 이 메일은 무시하셔도 됩니다.")
        except Exception as e:  # noqa: BLE001
            print(f"  ! 로그인 메일 발송 실패: {e}")
    # 가입 여부나 발송 제한 여부를 드러내지 않도록 항상 같은 화면을 보여준다
    return page(request, "login_sent.html", email=email, dev_link=link if config.DEV else None)


@app.get("/auth", response_class=HTMLResponse)
def auth_confirm(request: Request, token: str = ""):
    # 메일 보안 검사가 링크를 미리 열어도 토큰이 소모되지 않도록 버튼을 한 번 더 누르게 한다
    return page(request, "auth.html", token=token)


@app.post("/auth")
def auth(token: str = Form(""), con=Depends(get_db)):
    now = config.now_kst()
    row = con.execute("select email from login_tokens where token_hash=? and expires_at>?",
                      (sha(token), now.isoformat())).fetchone()
    if not row:
        return go("/login", "expired")
    con.execute("delete from login_tokens where token_hash=?", (sha(token),))
    con.execute("insert or ignore into users(email,unsub_token,created_at) values(?,?,?)",
                (row["email"], secrets.token_urlsafe(24), now.isoformat()))
    uid = con.execute("select id from users where email=?", (row["email"],)).fetchone()[0]
    sid = secrets.token_urlsafe(32)
    con.execute("insert into sessions(token_hash,user_id,csrf,expires_at) values(?,?,?,?)",
                (sha(sid), uid, secrets.token_urlsafe(24), (now + timedelta(days=config.SESSION_DAYS)).isoformat()))
    con.commit()
    resp = go("/app")
    resp.set_cookie(COOKIE, sid, max_age=config.SESSION_DAYS * 86400, httponly=True, samesite="lax",
                    secure=config.BASE_URL.startswith("https://"))
    return resp


@app.post("/logout")
def logout(request: Request, csrf: str = Form(""), con=Depends(get_db)):
    user, token = current(request, con)
    if user and secrets.compare_digest(csrf, token):
        con.execute("delete from sessions where token_hash=?", (sha(request.cookies[COOKIE]),))
        con.commit()
    resp = go("/")
    resp.delete_cookie(COOKIE)
    return resp


def member_page(request, con, name, **ctx):
    user, csrf = current(request, con)
    if not user:
        return go("/login")
    blocks = reports.user_report(con, user["id"])
    return page(request, name, user=user, csrf=csrf, blocks=blocks, today=config.today_kst(),
                limit=config.PLAN_LIMIT.get(user["plan"], 5), plan_name=config.PLAN_NAME.get(user["plan"], "무료"),
                **ctx)


@app.get("/app", response_class=HTMLResponse)
def today(request: Request, con=Depends(get_db)):
    """첫 화면: 주제별 오늘의 핵심 뉴스 3개"""
    return member_page(request, con, "today.html", tab="today", suggested=config.SUGGESTED)


@app.get("/topics", response_class=HTMLResponse)
def topics(request: Request, con=Depends(get_db)):
    return member_page(request, con, "topics.html", tab="topics")


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request, con=Depends(get_db)):
    return member_page(request, con, "settings.html", tab="settings")


def guard(request, con, csrf):
    """로그인과 CSRF를 확인한다. 통과하면 사용자 행, 아니면 None."""
    user, token = current(request, con)
    if not user or not secrets.compare_digest(csrf or "", token):
        return None
    return user


@app.post("/topics")
def add_topic(request: Request, bg: BackgroundTasks, query: str = Form(""), csrf: str = Form(""),
              con=Depends(get_db)):
    user = guard(request, con, csrf)
    if not user:
        return go("/app", "form")
    q, norm = norm_topic(query)
    if not 2 <= len(q) <= 40:
        return go("/topics", "bad")
    now = config.now_kst().isoformat()
    con.execute("begin immediate")  # 동시에 여러 번 눌러도 한도를 넘지 않도록 잠근 뒤 센다
    if con.execute("select 1 from subscriptions s join topics t on t.id=s.topic_id where s.user_id=? and t.norm=?",
                   (user["id"], norm)).fetchone():
        con.rollback()
        return go("/topics", "dup")
    count = con.execute("select count(*) from subscriptions where user_id=?", (user["id"],)).fetchone()[0]
    if count >= config.PLAN_LIMIT.get(user["plan"], 5):
        con.rollback()
        return go("/topics", "limit")
    con.execute("insert or ignore into topics(query,norm,created_at) values(?,?,?)", (q, norm, now))
    topic = con.execute("select id, last_collected_at from topics where norm=?", (norm,)).fetchone()
    con.execute("insert into subscriptions(user_id,topic_id,created_at) values(?,?,?)", (user["id"], topic["id"], now))
    con.commit()
    if not topic["last_collected_at"]:
        bg.add_task(jobs.refresh_topic_by_id, topic["id"])
    return go("/app", "added")


@app.post("/topics/{topic_id}/delete")
def delete_topic(topic_id: int, request: Request, csrf: str = Form(""), con=Depends(get_db)):
    user = guard(request, con, csrf)
    if not user:
        return go("/app", "form")
    con.execute("delete from subscriptions where user_id=? and topic_id=?", (user["id"], topic_id))
    # 아무도 구독하지 않는 주제는 수집 자료와 함께 지운다
    con.execute("delete from topics where id=? and not exists(select 1 from subscriptions where topic_id=?)",
                (topic_id, topic_id))
    con.commit()
    return go("/topics", "removed")


@app.post("/settings/mail")
def set_mail(request: Request, on: int = Form(0), csrf: str = Form(""), con=Depends(get_db)):
    user = guard(request, con, csrf)
    if not user:
        return go("/app", "form")
    con.execute("update users set mail_on=? where id=?", (1 if on else 0, user["id"]))
    con.commit()
    return go("/settings", "mail_on" if on else "mail_off")


@app.post("/account/delete")
def delete_account(request: Request, csrf: str = Form(""), con=Depends(get_db)):
    user = guard(request, con, csrf)
    if not user:
        return go("/app", "form")
    con.execute("delete from users where id=?", (user["id"],))
    con.execute("delete from login_tokens where email=?", (user["email"],))
    con.execute("delete from topics where not exists(select 1 from subscriptions where topic_id=topics.id)")
    con.commit()
    resp = go("/", "deleted")
    resp.delete_cookie(COOKIE)
    return resp


@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_form(request: Request, t: str = ""):
    return page(request, "unsubscribe.html", t=t, done=False)


@app.post("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(request: Request, t: str = "", con=Depends(get_db)):
    # 메일 프로그램의 원클릭 수신 거부(List-Unsubscribe-Post)도 이 주소로 들어온다
    if t:
        con.execute("update users set mail_on=0 where unsub_token=?", (t,))
        con.commit()
    return page(request, "unsubscribe.html", t=t, done=True)


@app.get("/sw.js")
def service_worker():
    return FileResponse(os.path.join(HERE, "static", "sw.js"), media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(os.path.join(HERE, "static", "manifest.webmanifest"),
                        media_type="application/manifest+json")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    resp.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; script-src 'self'; frame-ancestors 'none'")
    return resp


def _scheduler():
    """RADAR_SCHEDULER=1일 때 매일 SEND_HOUR(KST)에 일일 작업을 돌린다. 서버를 한 대만 띄울 때 쓴다."""
    last = None
    while True:
        now = config.now_kst()
        if now.hour == config.SEND_HOUR and last != now.date():
            last = now.date()
            try:
                print("일일 작업:", jobs.daily())
            except Exception as e:  # noqa: BLE001
                print(f"  ! 일일 작업 실패: {e}")
        time.sleep(60)
