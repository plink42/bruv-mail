from email.utils import parseaddr


def classify_email(parsed):
    tags = []
    subject = (parsed.subject or "").lower()
    body = (parsed.body_text or "").lower()
    _, sender_addr = parseaddr(parsed.from_addr or "")
    sender_addr = sender_addr.lower()

    if "invoice" in subject:
        tags.append("finance")

    if "unsubscribe" in body:
        tags.append("newsletter")

    if sender_addr.endswith("@github.com"):
        tags.append("devops")

    return tags
