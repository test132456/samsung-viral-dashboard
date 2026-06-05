"""일정 상태·D-day 계산. 순수 함수."""
from __future__ import annotations
from datetime import date, datetime


def _parse(d) -> date | None:
    if not d or str(d).strip() == "":
        return None
    try:
        return datetime.strptime(str(d).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def dday_label(target, today: date) -> str:
    d = _parse(target)
    if d is None:
        return ""
    diff = (d - today).days
    if diff < 0:
        return "지연"
    if diff == 0:
        return "D-DAY"
    return f"D-{diff}"


def compute_status(row: dict, today: date) -> str:
    """발행 완료 > 지연 > 진행중 > 예정 순으로 판정."""
    if _parse(row.get("publish_actual_date")):
        return "완료"
    plan = _parse(row.get("publish_plan_date"))
    if plan and plan < today:
        return "지연"
    started = any(_parse(row.get(k)) for k in
                  ("draft_submit_date", "review_submit_date", "review_done_date"))
    return "진행중" if started else "예정"


def annotate(rows: list[dict], today: date) -> list[dict]:
    """각 행에 status, dday(발행예정일 기준) 부가."""
    out = []
    for r in rows:
        r = dict(r)
        r["status"] = compute_status(r, today)
        r["dday"] = dday_label(r.get("publish_plan_date"), today)
        out.append(r)
    return out


def upcoming_deadlines(rows: list[dict], today: date, top_n: int = 5) -> list[dict]:
    """발행예정일 임박/지연 순 상위 N (완료 제외)."""
    annotated = [r for r in annotate(rows, today) if r["status"] != "완료"]
    def key(r):
        d = _parse(r.get("publish_plan_date"))
        return (d - today).days if d else 9999
    return sorted(annotated, key=key)[:top_n]
