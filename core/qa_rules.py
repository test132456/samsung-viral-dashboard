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
