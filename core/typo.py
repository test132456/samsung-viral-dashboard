"""오탈자 검수 — 자주 틀리는 한국어 오타 사전 기반. 순수 함수.

'항상 틀린 형태'만 넣어 오탐을 줄였다(문맥 필요한 애매한 건 제외).
새 오타가 발견되면 TYPOS 에 '오타: 올바른표기' 로 한 줄 추가하면 된다.
"""
from __future__ import annotations

# 오타(as-is) → 올바른 표기(to-be)
TYPOS = {
    "유렵": "유럽",
    "몇일": "며칠",
    "오랫만": "오랜만",
    "왠만": "웬만",
    "금새": "금세",
    "희안": "희한",
    "설레임": "설렘",
    "역활": "역할",
    "어떻해": "어떡해",
    "되요": "돼요",
    "되서": "돼서",
    "됬": "됐",
    "페키지": "패키지",
    "스케쥴": "스케줄",
    "메뉴얼": "매뉴얼",
    "카달로그": "카탈로그",
    "악세사리": "액세서리",
    "레크레이션": "레크리에이션",
    "뇌졸증": "뇌졸중",
    "폭팔": "폭발",
    "일사분란": "일사불란",
    "가벼히": "가벼이",
    "간지르": "간질이",
    "구렛나루": "구레나룻",
    "닥달": "닦달",
}


def check_typos(text: str) -> list[dict]:
    """원고에서 오타 사전에 걸리는 표기를 찾아 [{as_is, to_be, count, snippet}] 반환."""
    text = text or ""
    out = []
    for bad, good in TYPOS.items():
        if bad == good or bad not in text:
            continue
        idx = text.find(bad)
        cnt = text.count(bad)
        s, e = max(0, idx - 12), min(len(text), idx + len(bad) + 12)
        snippet = ("…" if s > 0 else "") + text[s:e].replace("\n", " ").strip() + ("…" if e < len(text) else "")
        out.append({"as_is": bad, "to_be": good, "count": cnt, "snippet": snippet})
    return out
