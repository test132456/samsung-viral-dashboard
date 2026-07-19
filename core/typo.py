"""오탈자 검수 — (1) 자주 틀리는 한국어 오타 사전 + (2) 네이버 맞춤법 검사기(있으면).

사전(check_typos)은 항상 동작하는 신뢰 기준. 네이버(spellcheck_naver)는 임의 오타까지
잡아주지만 비공식이라 실패할 수 있어, 실패 시 조용히 [] 를 돌려 사전만으로 동작한다.
"""
from __future__ import annotations
import difflib
import re

import requests

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
_SPELL_URL = "https://m.search.naver.com/p/csearch/ocontent/util/SpellerProxy"
_URL_RE = re.compile(r"https?://\S+|\S+@\S+\.\S+")   # URL·이메일
_TAG_RE = re.compile(r"#[가-힣A-Za-z0-9_]+")           # 해시태그
# 고지/법적 bo일러플레이트 — 고정 문구라 맞춤법 검사에서 제외(별도 '고지문구' 체크에서 검증)
_LEGAL_MARKERS = ("준법감시인확인필", "예금자보호", "심의필", "보험협회", "생명보험협회", "손해보험협회")


def _clean_for_spell(text: str) -> str:
    """맞춤법 검사에 넣기 전 URL·이메일·해시태그 및 고지문구 줄 제거
    (네이버가 URL/해시태그/법적문구를 엉뚱하게 교정하는 오탐 방지)."""
    out = []
    for ln in (text or "").split("\n"):
        ln = _TAG_RE.sub(" ", _URL_RE.sub(" ", ln))
        if any(m in ln for m in _LEGAL_MARKERS):
            continue  # 고지문구 줄 통째 제외
        out.append(ln)
    return "\n".join(out)

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
    # --- 외래어 표기 (거의 항상 틀림) ---
    "컨텐츠": "콘텐츠",
    "컨텐트": "콘텐트",
    "메세지": "메시지",
    "리더쉽": "리더십",
    "멤버쉽": "멤버십",
    "파트너쉽": "파트너십",
    "스폰서쉽": "스폰서십",
    "워크샵": "워크숍",
    "프리젠테이션": "프레젠테이션",
    "비지니스": "비즈니스",
    "악세서리": "액세서리",
    "초콜렛": "초콜릿",
    "쵸콜릿": "초콜릿",
    "케잌": "케이크",
    "케익": "케이크",
    "소세지": "소시지",
    "쥬스": "주스",
    "케찹": "케첩",
    "부페": "뷔페",
    "바베큐": "바비큐",
    "알콜": "알코올",
    "앙콜": "앙코르",
    "밧데리": "배터리",
    "리모콘": "리모컨",
    "로보트": "로봇",
    "도너츠": "도넛",
    "데뷰": "데뷔",
    "렌트카": "렌터카",
    "넌센스": "난센스",
    "판넬": "패널",
    "심포지움": "심포지엄",
    "나레이션": "내레이션",
    "팜플렛": "팸플릿",
    "팜플릿": "팸플릿",
    "플랜카드": "플래카드",
    "앙케이트": "앙케트",
    "앰블런스": "앰뷸런스",
    "컨셉트": "콘셉트",
    # --- 한글 자주 틀림 (문맥 무관하게 항상 틀림) ---
    "되써": "됐어",
    "됫": "됐",
    "뵈요": "봬요",
    "할께": "할게",
    "갈께": "갈게",
    "줄께": "줄게",
    "볼께": "볼게",
    "올께": "올게",
    "그럴께": "그럴게",
    "있을께": "있을게",
    "드릴께": "드릴게",
    "할꺼": "할 거",
    "갈꺼": "갈 거",
    "될꺼": "될 거",
    "깨끗히": "깨끗이",
    "틈틈히": "틈틈이",
    "일일히": "일일이",
    "곰곰히": "곰곰이",
    "웬지": "왠지",
    "왠일": "웬일",
    "왠걸": "웬걸",
    "어의없": "어이없",
    "않되": "안 되",
    "않돼": "안 돼",
    "어짜피": "어차피",
    "설겆이": "설거지",
    "찌게": "찌개",
    "육계장": "육개장",
    "떡볶기": "떡볶이",
    "떡복이": "떡볶이",
    "떡복기": "떡볶이",
    "짜집기": "짜깁기",
    "감사함니다": "감사합니다",
    "쇼파": "소파",
    "까페": "카페",
    "라이센스": "라이선스",
    "갯수": "개수",
    "오랜동안": "오랫동안",
    "할려고": "하려고",
    "갈려고": "가려고",
    "볼려고": "보려고",
    "부시시": "부스스",
    # --- 여행/현장 제보 오타 ---
    "국젯선": "국제선",
    "일봉": "일본",
    "팻스": "패스",
    "케릭터": "캐릭터",
    # --- 종결어미 오타 (한 클래스 통째로 잡음) ---
    "슴니다": "습니다",
    "함니다": "합니다",
    "읍니다": "습니다",
}


def _passport_key(sess, timeout):
    try:
        r = sess.get("https://search.naver.com/search.naver",
                     params={"where": "nexearch", "query": "맞춤법 검사기"},
                     headers={"User-Agent": _UA}, timeout=timeout)
        m = re.search(r"passportKey=([A-Za-z0-9%]+)", r.text)
        return m.group(1) if m else None
    except Exception:
        return None


def _chunks(text, size=480):
    out, cur = [], ""
    for part in re.split(r"(?<=[.!?\n])", text):
        if cur and len(cur) + len(part) > size:
            out.append(cur)
            cur = ""
        cur += part
    if cur.strip():
        out.append(cur)
    return out


def spellcheck_naver(text: str, timeout: int = 6) -> str | None:
    """네이버 맞춤법 검사기로 교정된 전체 텍스트 반환. 실패하면 None(→ 사전만 사용)."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        import json
        sess = requests.Session()
        pk = _passport_key(sess, timeout)
        out = []
        for chunk in _chunks(text):
            params = {"passportKey": pk or "", "where": "nexearch",
                      "color_blindness": "0", "q": chunk}
            r = sess.get(_SPELL_URL, params=params, timeout=timeout,
                         headers={"User-Agent": _UA, "Referer": "https://search.naver.com/"})
            try:
                data = r.json()
            except Exception:
                m = re.search(r"\((\{.*\})\)\s*$", r.text, re.S)
                data = json.loads(m.group(1)) if m else {}
            html_ = (((data.get("message") or {}).get("result") or {}).get("html")) or ""
            if not html_:
                return None  # 형식이 바뀌었거나 차단 → 폴백
            out.append(re.sub(r"<[^>]+>", "", html_).replace("&nbsp;", " "))
        return "".join(out)
    except Exception:
        return None


def diff_corrections(original: str, corrected: str) -> list[dict]:
    """원문 vs 네이버 교정문 diff → [{as_is, to_be, count, context}] (단어 단위).
    오탈자만 남긴다: '띄어쓰기만 다른' 교정(네이버가 과도하게 붙이거나 띄운 것)은 제외."""
    original, corrected = original or "", corrected or ""
    if not corrected:
        return []
    o = re.sub(r"\s+", " ", original).strip()
    c = re.sub(r"\s+", " ", corrected).strip()
    if not c or o == c:
        return []
    raw_lines = [ln.strip() for ln in original.split("\n") if ln.strip()]
    _nl = lambda s: re.sub(r"\s+", " ", s).strip()
    sm = difflib.SequenceMatcher(None, o, c, autojunk=False)
    out, seen = [], set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        while i1 > 0 and not o[i1 - 1].isspace():
            i1 -= 1
        while i2 < len(o) and not o[i2].isspace():
            i2 += 1
        while j1 > 0 and not c[j1 - 1].isspace():
            j1 -= 1
        while j2 < len(c) and not c[j2].isspace():
            j2 += 1
        a, b = o[i1:i2].strip(), c[j1:j2].strip()
        if not a or not b or a == b or a in seen:
            continue
        if a.replace(" ", "") == b.replace(" ", ""):  # 띄어쓰기만 다름 → 오탈자 아님
            continue
        seen.add(a)
        ctx = next((ln for ln in raw_lines if a in _nl(ln)), a)
        out.append({"as_is": a, "to_be": b, "count": original.count(a) or 1, "context": ctx})
    return out


def naver_typos(text: str) -> list[dict]:
    """네이버 맞춤법 기반 오탈자만 반환(URL·해시태그 제외, 띄어쓰기 제외). 실패 시 []."""
    clean = _clean_for_spell(text)
    corrected = spellcheck_naver(clean)
    return diff_corrections(clean, corrected or "")


def check_typos(text: str) -> list[dict]:
    """원고에서 오타 사전에 걸리는 표기를 찾아 [{as_is, to_be, count, context}] 반환.
    context = 오타가 들어있는 '줄 전체'(길면 오타 주변만 잘라 …로 표시)."""
    text = text or ""
    lines = text.split("\n")
    out = []
    for bad, good in TYPOS.items():
        if bad == good or bad not in text:
            continue
        cnt = text.count(bad)
        ctx = next((ln.strip() for ln in lines if bad in ln), bad)
        if len(ctx) > 110:  # 너무 긴 줄은 오타 주변만
            i = ctx.find(bad)
            s, e = max(0, i - 45), min(len(ctx), i + len(bad) + 45)
            ctx = ("…" if s > 0 else "") + ctx[s:e].strip() + ("…" if e < len(ctx) else "")
        out.append({"as_is": bad, "to_be": good, "count": cnt, "context": ctx})
    return out
