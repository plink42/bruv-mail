import email
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from email.policy import default


@dataclass
class ParsedEmail:
    message_id: str
    subject: str
    from_addr: str
    to_addrs: str
    date: datetime | None
    body_text: str | None
    body_html: str | None


def parse_email(raw_bytes):
    msg = email.message_from_bytes(raw_bytes, policy=default)

    body_text = None
    body_html = None

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body_text = part.get_content()
        elif part.get_content_type() == "text/html":
            body_html = part.get_content()

    parsed_date = None
    if msg["Date"]:
        try:
            parsed_date = parsedate_to_datetime(msg["Date"])
        except (TypeError, ValueError):
            parsed_date = None

    return ParsedEmail(
        message_id=msg["Message-ID"] or "",
        subject=msg["Subject"] or "",
        from_addr=msg["From"] or "",
        to_addrs=", ".join(msg.get_all("To", [])),
        date=parsed_date,
        body_text=body_text,
        body_html=body_html,
    )
