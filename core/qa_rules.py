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


def check_riders(text: str, riders: list[dict]) -> list[dict]:
    """약관 정식 특약명 대조. 오기재(common_mistakes) 발견 시 정식명 제안.
    단, 오기재 문자열이 정식명의 일부로 등장한 위치는 위반으로 보지 않는다."""
    hits = []
    for r in riders:
        official = r["official_name"]
        official_spans = [(p, p + len(official)) for p in _find_positions(text, official)]
        for mistake in r.get("common_mistakes", []):
            for pos in _find_positions(text, mistake):
                inside_official = any(s <= pos < e for s, e in official_spans)
                if inside_official:
                    continue
                hits.append({"found": mistake, "official_name": official, "position": pos})
    return hits


_PRICE_RE = re.compile(r"\d{1,3}(?:,\d{3})*\s*원")

def check_price(text: str) -> list[dict]:
    """보험료성 금액(숫자+원) 탐지 → 경고용."""
    return [{"amount": m.group().replace(" ", ""), "position": m.start()}
            for m in _PRICE_RE.finditer(text)]
