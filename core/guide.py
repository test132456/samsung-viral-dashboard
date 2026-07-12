"""블로그 작성 가이드(.pptx) 파서 & 원고-가이드 준수 체크. 순수 함수.

extract_text(pptx_bytes)  가이드 PPT 전체 텍스트(표는 'a | b | c'로)
parse_guide(text)         가이드에서 금지표현·필수 해시태그 추출
check(manuscript, guide)  원고를 가이드 기준으로 점검
"""
from __future__ import annotations
import io
import re

_QUOTES = "‘’\"'＇「」“”"
_HEADER_TERMS = {"불가 표현", "불가표현", "불가 표현 ", "예시", "사유"}


def extract_text(pptx_bytes: bytes) -> str:
    from pptx import Presentation
    prs = Presentation(io.BytesIO(pptx_bytes))
    lines = []
    for slide in prs.slides:
        for sh in slide.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip():
                lines.append(sh.text_frame.text.strip())
            if sh.has_table:
                for row in sh.table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    if any(cells):
                        lines.append(" | ".join(cells))
    return "\n".join(lines)


def parse_guide(text: str) -> dict:
    text = text or ""
    # 필수 해시태그
    hashtags = []
    for h in re.findall(r"#[가-힣A-Za-z0-9]+", text):
        if h not in hashtags:
            hashtags.append(h)
    # 금지표현: '표현 불가' 섹션의 표 첫 칸
    banned = []
    if "표현 불가" in text:
        section = text.split("표현 불가", 1)[1]
        for line in section.splitlines():
            if "|" not in line:
                continue
            raw = line.split("|")[0].strip().strip(_QUOTES).strip()
            if not (2 <= len(raw) <= 25) or raw in _HEADER_TERMS:
                continue
            # '빈번하게, 자주'처럼 각 부분이 모두 2자 이상이면 개별 단어로 분리
            parts = [p.strip() for p in raw.split(",")]
            cands = parts if len(parts) > 1 and all(len(p) >= 2 for p in parts) else [raw]
            for c in cands:
                c = c.strip().strip("~").strip()
                if 2 <= len(c) <= 25 and c not in _HEADER_TERMS and c not in banned:
                    banned.append(c)
    return {"hashtags": hashtags, "banned": banned}


def check(manuscript: str, guide: dict) -> dict:
    ms = manuscript or ""
    banned_hits = [b for b in guide.get("banned", []) if b in ms]
    tags = guide.get("hashtags", [])
    tags_missing = [t for t in tags if t not in ms]
    tags_included = [t for t in tags if t in ms]
    kw_count = ms.count("해외여행보험")
    return {
        "banned_hits": banned_hits,
        "tags_total": len(tags), "tags_included": tags_included, "tags_missing": tags_missing,
        "keyword_count": kw_count,          # '해외여행보험' 등장 횟수 (가이드: 3~5개)
        "keyword_ok": 3 <= kw_count <= 5,
    }
