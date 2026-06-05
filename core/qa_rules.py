"""QA 규칙 레이어 — 모두 순수 함수. text + 기준리스트 → 위반 리스트."""
from __future__ import annotations
import re


def _find_positions(text: str, needle: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(needle), text)]


def check_banned(text: str, banned: list[str]) -> list[dict]:
    """금지표현 사전 매칭. 각 hit: {term, position}."""
    hits = []
    for term in banned:
        for pos in _find_positions(text, term):
            hits.append({"term": term, "position": pos})
    return hits


_PRICE_RE = re.compile(r"\d{1,3}(?:,\d{3})*\s*원")

def check_price(text: str) -> list[dict]:
    """보험료성 금액(숫자+원) 탐지 → 경고용."""
    return [{"amount": m.group().replace(" ", ""), "position": m.start()}
            for m in _PRICE_RE.finditer(text)]
