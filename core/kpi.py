"""홈 KPI 및 탭 집계. 순수 함수."""
from __future__ import annotations


def _in_month(d: str, month: str) -> bool:
    return bool(d) and str(d).strip()[:7] == month


def aggregate_kpis(schedule, reviews, qa, briefing, month: str) -> dict:
    in_progress = sum(1 for r in schedule if r.get("status") == "진행중")
    published = sum(1 for r in schedule if r.get("status") == "완료")
    review_waiting = sum(1 for r in reviews if r.get("status") == "심의접수")
    review_done = sum(1 for r in reviews if r.get("status") in ("심의완료", "발행완료"))
    briefing_exposed = sum(1 for r in briefing
                           if str(r.get("ai_briefing_exposed", "")).upper() == "Y" and _in_month(r.get("date", ""), month))
    return {"in_progress": in_progress, "review_waiting": review_waiting,
            "review_done": review_done, "published": published,
            "briefing_exposed": briefing_exposed}


def review_status_counts(rows) -> dict:
    out = {}
    for r in rows:
        s = r.get("status", "")
        out[s] = out.get(s, 0) + 1
    return out


def influencer_summary(rows) -> dict:
    selected = sum(1 for r in rows if str(r.get("selected", "")).upper() == "Y")
    submitted = sum(1 for r in rows if str(r.get("draft_submitted", "")).upper() == "Y")
    published = sum(1 for r in rows if str(r.get("published", "")).upper() == "Y")
    rate = round(published / selected * 100, 1) if selected else 0.0
    return {"selected": selected, "submitted": submitted, "published": published, "publish_rate": rate}


def briefing_rollup(rows, month: str) -> dict:
    m = [r for r in rows if _in_month(r.get("date", ""), month)]
    exposed = [r for r in m if str(r.get("ai_briefing_exposed", "")).upper() == "Y"]
    return {"exposed_count": len(exposed),
            "keyword_count": len({r.get("keyword") for r in exposed}),
            "by_type": {t: sum(1 for r in exposed if r.get("content_type") == t)
                        for t in {r.get("content_type") for r in exposed}}}
