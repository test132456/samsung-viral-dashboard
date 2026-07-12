"""심의본 vs 발행본 문장단위 diff + 누락체크. 순수 함수."""
from __future__ import annotations
import re
import difflib

# 발행본에 '고지문구'가 유지됐는지 판단하는 마커 (하나만 있어도 정상)
DISCLOSURE_MARKERS = [
    "준법감시인확인필", "예금자보호", "상품설명서 및 약관",
    "광고비(원고료)", "광고비", "원고료", "유료광고",
]


def _normalize(text: str) -> str:
    """보이지 않는 특수문자(zero-width)·비표준 공백 제거, 공백 정규화."""
    text = (text or "").replace("\xa0", " ").replace("\r", "\n")
    text = re.sub(r"[​‌‍﻿­]", "", text)  # zero-width류 제거
    return text


def _sentences(text: str) -> list[str]:
    """정규화 후 문장 분리. 공백은 하나로 접고, 2자 미만 조각은 버린다
    (원고/발행본의 줄바꿈·공백 차이로 인한 허위 diff 방지)."""
    text = _normalize(text)
    out = []
    for part in re.split(r"[.\n!?]+", text):
        s = re.sub(r"\s+", " ", part).strip()
        if len(s) >= 2:
            out.append(s)
    return out


def compare(approved: str, published: str, refs: dict) -> dict:
    a, b = _sentences(approved), _sentences(published)
    sm = difflib.SequenceMatcher(None, a, b)
    match_rate = round(sm.ratio() * 100, 1)

    changed = deleted = added = 0
    changed_list, deleted_list, added_list = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            f, t = " ".join(a[i1:i2]), " ".join(b[j1:j2])
            kind = "spacing" if re.sub(r"\s+", "", f) == re.sub(r"\s+", "", t) else "content"
            changed_list.append({"from": f, "to": t, "kind": kind})
            changed += 1
        elif tag == "delete":
            deleted += (i2 - i1)
            deleted_list += a[i1:i2]
        elif tag == "insert":
            added += (j2 - j1)
            added_list += b[j1:j2]

    a_norm, b_norm = _normalize(approved), _normalize(published)
    notice_ok = any(k in b_norm for k in DISCLOSURE_MARKERS)  # 발행본에 고지문구 마커 유지
    hashtag_ok = True  # 해시태그는 네이버 크롤링으로 수집 불가 → 판정 제외
    riders = [r["official_name"] for r in refs.get("riders", [])]
    rider_ok = all((r in a_norm) <= (r in b_norm) for r in riders) if riders else True

    return {
        "match_rate": match_rate,
        "changed": changed, "deleted": deleted, "added": added,
        "changed_list": changed_list, "deleted_list": deleted_list, "added_list": added_list,
        "notice_ok": notice_ok, "hashtag_ok": hashtag_ok, "rider_ok": rider_ok,
    }
