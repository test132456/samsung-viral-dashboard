"""자료실 — 저장소에 번들된 약관/작성가이드 최신본을 제공.

reference/ 폴더에 약관·가이드 파일을 두면 심의전 원고 검수가 자동으로 최신본을 쓴다.
(해외여행보험 바이럴은 약관·가이드가 고정이라 매번 올릴 필요 없이 한 번만 갱신)
최신화 = reference/ 파일 교체 후 재배포.
"""
from __future__ import annotations
import glob
import os
import time

_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reference")

_TERMS_PATTERNS = ["*약관*.pdf", "*약관*.docx", "*약관*.txt", "*terms*.pdf", "*terms*.docx", "*terms*.txt"]
_GUIDE_PATTERNS = ["*가이드*.pptx", "*guide*.pptx", "*.pptx"]


def _find(patterns: list[str]) -> str | None:
    for pat in patterns:
        hits = sorted(glob.glob(os.path.join(_DIR, pat)))
        if hits:
            return hits[0]
    return None


def _meta(path: str | None) -> dict | None:
    if not path or not os.path.exists(path):
        return None
    return {"path": path, "name": os.path.basename(path),
            "updated": time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path)))}


def terms_meta() -> dict | None:
    return _meta(_find(_TERMS_PATTERNS))


def guide_meta() -> dict | None:
    return _meta(_find(_GUIDE_PATTERNS))


def _read(path: str | None) -> bytes | None:
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def terms_bytes() -> bytes | None:
    m = terms_meta()
    return _read(m["path"]) if m else None


def guide_bytes() -> bytes | None:
    m = guide_meta()
    return _read(m["path"]) if m else None
