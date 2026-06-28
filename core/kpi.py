"""홈 KPI 및 탭 집계. 순수 함수."""
from __future__ import annotations


def _in_month(d: str, month: str) -> bool:
    return bool(d) and str(d).strip()[:7] == month


def _num(v) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0.0


def aggregate_kpis(schedule, reviews, qa, briefing, month: str) -> dict:
    """month는 briefing_exposed 집계에만 적용된다. 나머지 KPI(진행중·심의·발행)는
    월 필터 없이 현재 상태 기준 전체를 집계한다."""
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
    keywords = {r.get("keyword") for r in exposed if r.get("keyword")}
    types = {r.get("content_type") for r in exposed if r.get("content_type")}
    return {"exposed_count": len(exposed),
            "keyword_count": len(keywords),
            "by_type": {t: sum(1 for r in exposed if r.get("content_type") == t) for t in types}}


def briefing_daily(rows, month: str) -> dict:
    """월 내 AI브리핑 노출(Y)의 일별 건수. {date: count}."""
    daily = {}
    for r in rows:
        if str(r.get("ai_briefing_exposed", "")).upper() == "Y" and _in_month(r.get("date", ""), month):
            d = str(r.get("date", "")).strip()[:10]
            daily[d] = daily.get(d, 0) + 1
    return dict(sorted(daily.items()))


def citation_summary(rows, month: str) -> dict:
    """AI 툴별 인용률(= 인용수/질의수) 집계. month 필터.
    반환: {by_tool:{tool:rate%}, overall_rate, total_queries, total_cited}."""
    tools: dict[str, dict] = {}
    for r in rows:
        if not _in_month(r.get("date", ""), month):
            continue
        tool = str(r.get("tool", "")).strip()
        if not tool:
            continue
        t = tools.setdefault(tool, {"queries": 0.0, "cited": 0.0})
        t["queries"] += _num(r.get("queries"))
        t["cited"] += _num(r.get("cited"))
    by_tool = {tool: (round(v["cited"] / v["queries"] * 100, 1) if v["queries"] else 0.0)
               for tool, v in tools.items()}
    tq = sum(v["queries"] for v in tools.values())
    tc = sum(v["cited"] for v in tools.values())
    return {"by_tool": by_tool, "overall_rate": round(tc / tq * 100, 1) if tq else 0.0,
            "total_queries": int(tq), "total_cited": int(tc)}


def qa_summary(rows, month: str) -> dict:
    """QA 검수 요약 — 최근 점수(전체 마지막) + 당월 검수 건수."""
    latest_score = None
    if rows:
        try:
            latest_score = int(float(rows[-1].get("qa_score", 0)))
        except (ValueError, TypeError):
            latest_score = None
    count = sum(1 for r in rows if _in_month(r.get("checked_at", ""), month))
    return {"latest_score": latest_score, "count": count}


def compare_summary(rows, month: str) -> dict:
    """심의본 비교 요약 — 당월 평균 일치율 + 건수."""
    m = [r for r in rows if _in_month(r.get("checked_at", ""), month)]
    rates = [_num(r.get("match_rate")) for r in m if str(r.get("match_rate", "")).strip() != ""]
    avg = round(sum(rates) / len(rates), 1) if rates else None
    return {"avg_match": avg, "count": len(m)}
