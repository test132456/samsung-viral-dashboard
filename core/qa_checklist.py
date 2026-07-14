"""QA 원고 작성 플로우 점검 — 가이드(원고 작성 예시 플로우) 순서대로 구조 점검. 순수 함수.

가이드 플로우: 제목 → 유료광고 문안 → 특약 소개(+★보장문장) → 가입 링크(URL) → 고지문구(하단) → 해시태그(최하단)
각 항목: {name, status: 'ok'|'warn'|'fail'|'na', detail}
 ✓ ok=충족 / △ warn=부분충족·위치미흡 / ✕ fail=미충족 / — na=해당없음
"""
from __future__ import annotations
import re
from core import qa_rules

HEAD_RATIO = 0.20         # 본문 '첫 부분(상단)' 비율
TAIL_RATIO = 0.25         # 본문 '하단' 비율
_TAG_RE = re.compile(r"#[가-힣A-Za-z0-9_]+")
_URL_RE = re.compile(r"https?://\S+")
# ★ 특약 보장문장 패턴: "(담보명) 특약 가입 시, 가입 금액 한도로 보장"
_BENEFIT_RE = re.compile(r"가입금액한도")

# 체크리스트 항목명 (evaluate/blank 공통, 가이드 플로우 순서)
NAMES = [
    "제목 키워드 시작",
    "유료광고 문안(상단)",
    "특약 보장문장",
    "가입 링크(URL)",
    "고지문구(하단)",
    "해시태그(최하단)",
]


def blank() -> list[dict]:
    """검수 전 미리보기용 — 모든 항목 pending(–)."""
    return [{"name": n, "status": "pending", "detail": "검수 전"} for n in NAMES]


def evaluate(title: str, body: str, refs: dict, is_official: bool = False) -> list[dict]:
    """is_official=True(공식블로그)면 유료광고 문안은 '해당없음'(na) 처리."""
    title = (title or "").strip()
    body = body or ""
    keywords = [k["keyword"] for k in refs.get("keywords", []) if k.get("type") == "키워드"]
    head = body[:max(60, int(len(body) * HEAD_RATIO))]
    tail = body[-max(80, int(len(body) * TAIL_RATIO)):] if body else ""
    body_norm, tail_norm = qa_rules._norm(body), qa_rules._norm(tail)

    items = []

    # ① 제목 키워드 시작점
    if title and any(title.startswith(k) for k in keywords):
        items.append({"name": "제목 키워드 시작", "status": "ok", "detail": "제목이 핵심 키워드로 시작"})
    elif title and any(k in title for k in keywords):
        items.append({"name": "제목 키워드 시작", "status": "warn", "detail": "키워드 있으나 맨 앞 아님"})
    else:
        items.append({"name": "제목 키워드 시작", "status": "fail", "detail": "제목에 핵심 키워드 없음"})

    # ② 유료광고 문안 (본문 첫 부분) — 공식블로그는 해당없음
    if is_official:
        items.append({"name": "유료광고 문안(상단)", "status": "na", "detail": "공식블로그 · 해당없음"})
    elif "유료광고" in head or "원고료" in head or "광고비" in head:
        items.append({"name": "유료광고 문안(상단)", "status": "ok", "detail": "본문 첫 부분에 표기"})
    elif "유료광고" in body or "원고료" in body or "광고비" in body:
        items.append({"name": "유료광고 문안(상단)", "status": "warn", "detail": "표기 있으나 상단 아님"})
    else:
        items.append({"name": "유료광고 문안(상단)", "status": "fail", "detail": "유료광고 문안 없음"})

    # ③ ★ 특약 보장문장 — 특약 보장 언급 시 '(담보명) 특약 가입 시, 가입 금액 한도로 보장' 문장 필수
    n_benefit = len(_BENEFIT_RE.findall(body_norm))
    if "특약" not in body:
        items.append({"name": "특약 보장문장", "status": "warn", "detail": "특약 소개 문단이 없음"})
    elif n_benefit == 0:
        items.append({"name": "특약 보장문장", "status": "fail", "detail": "'가입 금액 한도로 보장' 문장 누락"})
    else:
        items.append({"name": "특약 보장문장", "status": "ok", "detail": f"보장문장 {n_benefit}곳"})

    # ④ 원고 내 URL(가입 링크) — 심의 후 삽입 예정일 수 있어 없으면 △
    urls = _URL_RE.findall(body)
    sf = [u for u in urls if "samsungfire.com" in u]
    if sf:
        items.append({"name": "가입 링크(URL)", "status": "ok", "detail": "삼성화재 가입 링크 포함"})
    elif urls:
        items.append({"name": "가입 링크(URL)", "status": "warn", "detail": f"URL {len(urls)}개 · 삼성화재 가입 링크인지 확인"})
    else:
        items.append({"name": "가입 링크(URL)", "status": "warn", "detail": "URL 없음 (심의 후 가입 링크 삽입 예정)"})

    # ⑤ 고지문구 (하단 배치) — ref_required 중 '고지' 유형 기준
    gojib = [r for r in refs.get("required", []) if "고지" in str(r.get("type", ""))] \
        or refs.get("required", [])
    if not gojib:
        items.append({"name": "고지문구(하단)", "status": "warn", "detail": "고지문구 기준 미설정"})
    else:
        present = [r for r in gojib if qa_rules._phrase_present(body_norm, r.get("phrase", ""))]
        in_tail = [r for r in gojib if qa_rules._phrase_present(tail_norm, r.get("phrase", ""))]
        if not present:
            items.append({"name": "고지문구(하단)", "status": "fail", "detail": "고지문구 없음"})
        elif in_tail:
            items.append({"name": "고지문구(하단)", "status": "ok", "detail": "하단에 고지문구 포함"})
        else:
            items.append({"name": "고지문구(하단)", "status": "warn", "detail": "고지문구 있으나 하단 아님"})

    # ⑥ 해시태그 (최하단 배치)
    tags = _TAG_RE.findall(body)
    tail_tags = _TAG_RE.findall(tail)
    if not tags:
        items.append({"name": "해시태그(최하단)", "status": "fail", "detail": "해시태그 없음"})
    elif len(tags) >= 3 and tail_tags:
        items.append({"name": "해시태그(최하단)", "status": "ok", "detail": f"{len(tags)}개 · 하단"})
    elif tail_tags:
        items.append({"name": "해시태그(최하단)", "status": "warn", "detail": f"{len(tags)}개 (권장 3개+)"})
    else:
        items.append({"name": "해시태그(최하단)", "status": "warn", "detail": f"{len(tags)}개 · 하단 아님"})

    return items


def summary(items: list[dict]) -> dict:
    """ok/warn/fail 개수 + 통과율(ok 기준). na(해당없음)는 분모에서 제외."""
    ok = sum(1 for i in items if i["status"] == "ok")
    warn = sum(1 for i in items if i["status"] == "warn")
    fail = sum(1 for i in items if i["status"] == "fail")
    applicable = sum(1 for i in items if i["status"] != "na") or 1
    return {"ok": ok, "warn": warn, "fail": fail, "pass_rate": round(ok / applicable * 100)}
