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


_PRICE_RE = re.compile(r"(?<!\d)(?:\d{1,3}(?:,\d{3})+|\d+)\s*원")

def check_price(text: str) -> list[dict]:
    """보험료성 금액(숫자+원) 탐지 → 경고용."""
    return [{"amount": m.group().replace(" ", ""), "position": m.start()}
            for m in _PRICE_RE.finditer(text)]


def _norm(s: str) -> str:
    """띄어쓰기·개행 차이를 무시하기 위해 공백류를 모두 제거."""
    return re.sub(r"\s+", "", s or "")


def _variants(phrase: str) -> list[str]:
    """'예금자보호|준법감시인확인필' 처럼 '|' 로 대체표현을 여러 개 지정 가능."""
    return [v.strip() for v in (phrase or "").split("|") if v.strip()]


def _phrase_present(text_norm: str, phrase: str) -> bool:
    """대체표현 중 하나라도 (띄어쓰기 무시) 들어있으면 충족."""
    return any(_norm(v) in text_norm for v in _variants(phrase))


def check_required(text: str, required: list[dict]) -> list[dict]:
    """필수문구(유료광고·고지) 누락 검출. 없는 것만 반환.
    phrase 에 '|' 로 대체표현을 넣으면 그 중 하나만 있어도 충족하며, 띄어쓰기는 무시한다."""
    tn = _norm(text)
    return [{"phrase": r["phrase"], "type": r.get("type", "")}
            for r in required if not _phrase_present(tn, r["phrase"])]


def required_status(text: str, required: list[dict]) -> list[dict]:
    """표시용: 각 필수문구 항목의 포함/누락 여부와 허용 표현 목록."""
    tn = _norm(text)
    return [{"phrase": r["phrase"], "type": r.get("type", ""),
             "variants": _variants(r["phrase"]),
             "present": _phrase_present(tn, r["phrase"])}
            for r in required]


def check_keywords(text: str, keywords: list[dict]) -> dict:
    """필수 키워드 포함 여부 + 필수 해시태그 존재 여부."""
    kw = [k["keyword"] for k in keywords if k.get("type") == "키워드"]
    tags = [k["keyword"] for k in keywords if k.get("type") == "해시태그"]
    missing = [k for k in kw if k not in text]
    has_tag = any(("#" + t) in text for t in tags)
    return {"missing_keywords": missing, "has_required_hashtag": has_tag}
