"""QA 구조 체크리스트 — 제목/본문의 위치·형식 조건 점검. 순수 함수.

각 항목: {name, status: 'ok'|'warn'|'fail', detail}
 ✓ ok=충족 / △ warn=부분충족·위치미흡 / ✕ fail=미충족
"""
from __future__ import annotations
import re

_URL_RE = re.compile(r"https?://\S+")
TITLE_MAX = 25            # 제목 글자수 상한
HEAD_RATIO = 0.20         # 본문 '첫 부분' 비율
TAIL_RATIO = 0.20         # 본문 '하단' 비율

# 체크리스트 항목명 (evaluate/blank 공통)
NAMES = [
    "제목 키워드 시작",
    f"제목 {TITLE_MAX}자 이내",
    "유료광고 문안(상단)",
    "필수 고지문구",
    "하단 가입 링크",
]


def blank() -> list[dict]:
    """검수 전 미리보기용 — 모든 항목 pending(–)."""
    return [{"name": n, "status": "pending", "detail": "검수 전"} for n in NAMES]


def evaluate(title: str, body: str, refs: dict) -> list[dict]:
    title = (title or "").strip()
    body = body or ""
    keywords = [k["keyword"] for k in refs.get("keywords", []) if k.get("type") == "키워드"]
    required = [str(r.get("phrase", "")) for r in refs.get("required", []) if r.get("phrase")]
    head = body[:max(60, int(len(body) * HEAD_RATIO))]
    tail = body[-max(80, int(len(body) * TAIL_RATIO)):] if body else ""

    items = []

    # ① 제목 키워드 시작점
    if title and any(title.startswith(k) for k in keywords):
        items.append({"name": "제목 키워드 시작", "status": "ok", "detail": "제목이 핵심 키워드로 시작"})
    elif title and any(k in title for k in keywords):
        items.append({"name": "제목 키워드 시작", "status": "warn", "detail": "키워드 있으나 맨 앞 아님"})
    else:
        items.append({"name": "제목 키워드 시작", "status": "fail", "detail": "제목에 핵심 키워드 없음"})

    # ② 제목 글자수 (≤ TITLE_MAX)
    n = len(title)
    if not title:
        items.append({"name": f"제목 {TITLE_MAX}자 이내", "status": "fail", "detail": "제목 미입력"})
    elif n <= TITLE_MAX:
        items.append({"name": f"제목 {TITLE_MAX}자 이내", "status": "ok", "detail": f"{n}자"})
    elif n <= TITLE_MAX + 5:
        items.append({"name": f"제목 {TITLE_MAX}자 이내", "status": "warn", "detail": f"{n}자 (약간 초과)"})
    else:
        items.append({"name": f"제목 {TITLE_MAX}자 이내", "status": "fail", "detail": f"{n}자 (초과)"})

    # ③ 유료광고 문안 (본문 첫 부분)
    if "유료광고" in head:
        items.append({"name": "유료광고 문안(상단)", "status": "ok", "detail": "본문 첫 부분에 표기"})
    elif "유료광고" in body:
        items.append({"name": "유료광고 문안(상단)", "status": "warn", "detail": "표기 있으나 상단 아님"})
    else:
        items.append({"name": "유료광고 문안(상단)", "status": "fail", "detail": "유료광고 표기 없음"})

    # ④ 필수 고지문구 (ref_required 기준 — 예보법·준법감시인확인필 등)
    if not required:
        items.append({"name": "필수 고지문구", "status": "warn", "detail": "고지문구 기준 미설정"})
    else:
        present = [p for p in required if p in body]
        if len(present) == len(required):
            items.append({"name": "필수 고지문구", "status": "ok", "detail": "고지문구 모두 포함"})
        elif present:
            items.append({"name": "필수 고지문구", "status": "warn", "detail": f"{len(present)}/{len(required)} 포함"})
        else:
            items.append({"name": "필수 고지문구", "status": "fail", "detail": "고지문구 없음"})

    # ⑤ 본문 하단 가입 링크
    if _URL_RE.search(tail):
        items.append({"name": "하단 가입 링크", "status": "ok", "detail": "본문 하단에 링크"})
    elif _URL_RE.search(body):
        items.append({"name": "하단 가입 링크", "status": "warn", "detail": "링크 있으나 하단 아님"})
    else:
        items.append({"name": "하단 가입 링크", "status": "fail", "detail": "가입 링크 없음"})

    return items


def summary(items: list[dict]) -> dict:
    """ok/warn/fail 개수 + 통과율(ok 기준)."""
    ok = sum(1 for i in items if i["status"] == "ok")
    warn = sum(1 for i in items if i["status"] == "warn")
    fail = sum(1 for i in items if i["status"] == "fail")
    total = len(items) or 1
    return {"ok": ok, "warn": warn, "fail": fail, "pass_rate": round(ok / total * 100)}
