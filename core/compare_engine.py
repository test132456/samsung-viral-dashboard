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
    (원고/발행본의 줄바꿈·공백 차이로 인한 허위 diff 방지).
    해시태그(#...)는 네이버 크롤링으로 안정적으로 못 가져오므로 비교 대상에서 제외한다."""
    text = _normalize(text)
    text = re.sub(r"#[0-9A-Za-z가-힣_]+", " ", text)  # 해시태그 제거
    out = []
    for part in re.split(r"[.\n!?]+", text):
        s = re.sub(r"\s+", " ", part).strip()
        if len(s) >= 2:
            out.append(s)
    return out


def _change_fragments(orig: str, pub: str) -> list[tuple[str, str]]:
    """원고(orig)↔발행(pub)에서 바뀐 구간마다 (발행조각=현재, 원고조각=수정)로 잘라 리스트로.
    변경 지점을 단어 경계까지 넓혀 읽기 좋게 한다. 순수 삽입/삭제면 한쪽이 ''."""
    def expand(s, lo, hi):
        while lo > 0 and not s[lo - 1].isspace():
            lo -= 1
        while hi < len(s) and not s[hi].isspace():
            hi += 1
        return lo, hi
    sm = difflib.SequenceMatcher(None, orig, pub, autojunk=False)
    out = []
    for tag, oa, ob, pa, pb in sm.get_opcodes():
        if tag == "equal":
            continue
        oa2, ob2 = expand(orig, oa, ob)
        pa2, pb2 = expand(pub, pa, pb)
        out.append((pub[pa2:pb2].strip(), orig[oa2:ob2].strip()))
    return out


def revision_request(rep: dict, blogger: str = "", approved_title: str = "") -> str:
    """비교 결과 → 실행사 수정 요청 메일 문구(복붙용). 발행을 원고(심의본)에 맞추는 방향(현재 → 수정)."""
    changed = rep.get("changed_list", [])
    deleted = [d.strip() for d in rep.get("deleted_list", []) if d.strip()]
    added = [a.strip() for a in rep.get("added_list", []) if a.strip()]

    blocks = [f"<수정 요청 · {blogger}>" if blogger else "<수정 요청>", ""]
    n = [1]

    def add_sec(title, lines):
        if lines:
            blocks.append(f"{n[0]}. {title}")
            blocks.extend(lines)
            blocks.append("")
            n[0] += 1

    # 변경 조각을 '문구 / 문장부호 / 띄어쓰기'로 각각 분류
    content_lines, punct_lines, spacing_lines, seen = [], [], [], set()
    nospace = lambda s: re.sub(r"\s+", "", s)
    nopunct = lambda s: re.sub(r"[\s.,…·∙•!?~\"'`()\[\]<>]+", "", s)
    for c in changed:
        for cur, want in _change_fragments(c["from"], c["to"]):  # from=원고, to=발행
            if cur and want and cur != want:
                line = f"• {cur} → {want}"
                if nospace(cur) == nospace(want):
                    bucket = spacing_lines
                elif nopunct(cur) == nopunct(want):
                    bucket = punct_lines
                else:
                    bucket = content_lines
            elif want and not cur:
                line, bucket = f"• (추가) {want}", content_lines
            elif cur and not want:
                line, bucket = f"• (삭제) {cur}", content_lines
            else:
                continue
            if line in seen:
                continue
            seen.add(line)
            bucket.append(line)

    add_sec("문구 수정 (현재 → 수정)", content_lines)
    add_sec("문장부호 수정 (현재 → 수정)", punct_lines)
    add_sec("발행에 누락 — 추가 필요", [f"• {d}" for d in deleted])
    add_sec("발행에만 있음 — 삭제 검토", [f"• {a}" for a in added])
    if approved_title:
        add_sec("제목 확인", [f"• 원고(심의) 제목: {approved_title}",
                           "• 발행 제목이 위와 다르면 함께 수정 요청"])
    add_sec("띄어쓰기 통일 (현재 → 수정)", spacing_lines)
    if n[0] == 1:
        blocks.append("수정 사항 없음 — 발행본이 원고와 일치합니다.")
    return "\n".join(blocks).strip()


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
