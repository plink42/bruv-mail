import re
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ExtractedTask:
    title: str
    due_date: datetime | None
    confidence: float


def _derive_due_date(text: str, now: datetime) -> datetime | None:
    lowered = text.lower()
    if "tomorrow" in lowered:
        return now + timedelta(days=1)
    if "today" in lowered:
        return now

    match = re.search(r"\bby\s+(\d{4}-\d{2}-\d{2})\b", lowered)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            return None
    return None


def extract_tasks(parsed) -> list[ExtractedTask]:
    text_parts = [parsed.subject or "", parsed.body_text or ""]
    combined_text = "\n".join(text_parts)
    lowered = combined_text.lower()

    trigger_phrases = ["todo", "to do", "action required", "please", "remind me"]
    if not any(phrase in lowered for phrase in trigger_phrases):
        return []

    now = datetime.utcnow()
    due_date = _derive_due_date(combined_text, now)
    title = (parsed.subject or "Untitled task").strip()[:180]

    confidence = 0.55
    if "action required" in lowered:
        confidence = 0.75
    elif "remind me" in lowered or "todo" in lowered or "to do" in lowered:
        confidence = 0.65

    return [ExtractedTask(title=title or "Untitled task", due_date=due_date, confidence=confidence)]
