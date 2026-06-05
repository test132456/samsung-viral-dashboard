"""QA 오케스트레이션: 규칙 레이어 → (선택) AI 레이어 → 점수·리포트."""
from __future__ import annotations
from typing import Callable, Optional
from core import qa_rules


def run_qa(text: str, refs: dict, ai_judge: Optional[Callable[[str], list]] = None) -> dict:
    """refs: {banned, required, riders, keywords}. ai_judge: text->findings(없으면 규칙만)."""
    banned = qa_rules.check_banned(text, refs.get("banned", []))
    prices = qa_rules.check_price(text)
    riders = qa_rules.check_riders(text, refs.get("riders", []))
    missing_req = qa_rules.check_required(text, refs.get("required", []))
    kw = qa_rules.check_keywords(text, refs.get("keywords", []))

    ai_findings = []
    if ai_judge is not None:
        ai_findings = ai_judge(text) or []

    # 감점 규칙 (100 만점)
    score = 100
    score -= 8 * len(banned)
    score -= 10 * len(riders)
    score -= 12 * len(missing_req)
    score -= 5 if prices else 0
    score -= 5 * len(kw["missing_keywords"])
    score -= 3 if not kw["has_required_hashtag"] else 0
    score -= 4 * len(ai_findings)
    score = max(0, min(100, score))

    return {
        "qa_score": score,
        "banned": banned, "banned_count": len(banned),
        "riders": riders, "rider_error_count": len(riders),
        "prices": prices, "price_found": bool(prices),
        "missing_required": missing_req, "missing_phrase": bool(missing_req),
        "missing_keywords": kw["missing_keywords"],
        "has_required_hashtag": kw["has_required_hashtag"],
        "ai_findings": ai_findings,
    }
