"""약관 파일 파싱 & 원고-약관 특약명 대조. 순수 함수.

extract_riders(text)          약관 텍스트에서 특약명 후보 추출
coverage(manuscript, official) 원고에 약관 정식 특약명이 정확히 포함됐는지 대조
"""
from __future__ import annotations
import re


def extract_riders(terms_text: str) -> list[str]:
    """약관에서 '...특약'으로 끝나는 특약명 후보를 줄 단위로 추출(중복 제거)."""
    out, seen = [], set()
    for raw in re.split(r"[\n\r]+", terms_text or ""):
        line = raw.strip()
        if "특약" not in line:
            continue
        m = re.search(r"^(.{2,58}?특약)", line)
        name = (m.group(1) if m else line).strip()
        name = re.sub(r"^\s*(?:제?\s*\d+\s*[.)관조항호]|[·•\-*])\s*", "", name)  # 번호/불릿 제거
        name = name.strip()
        if 4 <= len(name) <= 60 and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def _head(name: str) -> str:
    """특약명 핵심 머리말(괄호 제거 후 앞 2어절) — 오기 탐지용."""
    core = re.sub(r"[()（）]", " ", name).split("특약")[0].strip()
    toks = core.split()
    return "".join(toks[:2])


def verify_usage(manuscript: str, ref_names: list[str]) -> dict:
    """원고가 참조하는 특약을 정식명(가이드/약관 기준)과 대조.
    ok=정확 표기 / mismatch=핵심어는 있으나 정식명 불일치(오기 의심) / unused=원고 미언급.
    형제 특약(같은 머리말)이 정확히 쓰였으면 그 머리말은 오기로 잡지 않는다."""
    ms = manuscript or ""
    msn = _norm(ms)
    names = [n for n in ref_names if n]
    present_heads = {_head(n) for n in names if n in ms or _norm(n) in msn}
    ok, mismatch, unused = [], [], []
    for n in names:
        if n in ms or _norm(n) in msn:
            ok.append(n)
            continue
        h = _head(n)
        if h and h in msn and h not in present_heads:
            mismatch.append(n)
        else:
            unused.append(n)
    return {"ok": ok, "mismatch": mismatch, "unused": unused,
            "ok_count": len(ok), "mismatch_count": len(mismatch)}


_TERMS_STOP = {"여행중", "보상", "보상금", "추가비용", "재발급비용", "특약", "국내", "출국",
               "제외", "지수형", "이상", "시간", "일이상", "입원", "손해", "손실", "분실제외",
               "보험", "여행", "및"}


def _core_tokens(name: str) -> list[str]:
    """특약명에서 표기 차이에 강한 핵심어만 추출(괄호·일반어 제거)."""
    core = re.sub(r"[()（）]", " ", name or "")
    return [t for t in re.split(r"[\s·]+", core) if len(t) >= 2 and t not in _TERMS_STOP]


def confirmed_count(riders: list[str], terms_text: str) -> int:
    """정식 특약명들이 약관에서 확인되는지 — 핵심어가 모두 등장하면 확인(표기 차이 허용)."""
    raw = _norm(terms_text)
    n = 0
    for r in riders:
        ts = _core_tokens(r)
        if ts and all(t in raw for t in ts):
            n += 1
    return n


def coverage(manuscript: str, official: list[str]) -> dict:
    """약관 정식 특약명이 원고에 정확히(그대로) 들어있는지 대조.
    included=원고에 정확히 표기된 약관 특약명 / missing=원고에 없는 약관 특약명."""
    ms = manuscript or ""
    names = [o for o in official if o]
    included = [o for o in names if o in ms]
    missing = [o for o in names if o not in ms]
    return {"total": len(names), "included": included, "missing": missing,
            "included_count": len(included)}
