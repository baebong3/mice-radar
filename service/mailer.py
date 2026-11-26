"""메일 발송. SMTP 설정이 없으면 outbox 폴더에 .eml로 남긴다."""
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from . import config


def build(to, subject, text, html=None, headers=None):
    msg = EmailMessage()
    msg["From"] = config.MAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    for k, v in (headers or {}).items():
        msg[k] = v
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    return msg


def send(to, subject, text, html=None, headers=None):
    """발송 방식('smtp' 또는 'outbox')을 돌려준다. 실패하면 예외."""
    msg = build(to, subject, text, html, headers)
    if not config.SMTP_HOST:
        os.makedirs(config.OUTBOX, exist_ok=True)
        name = f"{time.strftime('%Y%m%d_%H%M%S')}_{abs(hash(msg['Message-ID'])) % 10**6:06d}.eml"
        with open(os.path.join(config.OUTBOX, name), "wb") as f:
            f.write(bytes(msg))
        return "outbox"
    ctx = ssl.create_default_context()
    if config.SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=30, context=ctx)
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30)
        server.starttls(context=ctx)
    with server:
        if config.SMTP_USER:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)
    return "smtp"
