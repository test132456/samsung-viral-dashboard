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


def coverage(manuscript: str, official: list[str]) -> dict:
    """약관 정식 특약명이 원고에 정확히(그대로) 들어있는지 대조.
    included=원고에 정확히 표기된 약관 특약명 / missing=원고에 없는 약관 특약명."""
    ms = manuscript or ""
    names = [o for o in official if o]
    included = [o for o in names if o in ms]
    missing = [o for o in names if o not in ms]
    return {"total": len(names), "included": included, "missing": missing,
            "included_count": len(included)}
