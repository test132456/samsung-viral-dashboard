"""심의본 vs 발행본 문장단위 diff + 누락체크. 순수 함수."""
from __future__ import annotations
import re
import difflib


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[.\n!?]+", text)
    return [s.strip() for s in parts if s.strip()]


def compare(approved: str, published: str, refs: dict) -> dict:
    a, b = _sentences(approved), _sentences(published)
    sm = difflib.SequenceMatcher(None, a, b)
    match_rate = round(sm.ratio() * 100, 1)

    changed = deleted = added = 0
    changed_list, deleted_list, added_list = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            changed += max(i2 - i1, j2 - j1)
            changed_list.append({"from": " ".join(a[i1:i2]), "to": " ".join(b[j1:j2])})
        elif tag == "delete":
            deleted += (i2 - i1)
            deleted_list += a[i1:i2]
        elif tag == "insert":
            added += (j2 - j1)
            added_list += b[j1:j2]

    required = [r["phrase"] for r in refs.get("required", [])]
    notice_ok = all(p in published for p in required) if required else True
    tags = [k["keyword"] for k in refs.get("keywords", []) if k.get("type") == "해시태그"]
    hashtag_ok = (any(("#" + t) in published for t in tags)) if tags else True
    riders = [r["official_name"] for r in refs.get("riders", [])]
    rider_ok = all((r in approved) <= (r in published) for r in riders) if riders else True

    return {
        "match_rate": match_rate,
        "changed": changed, "deleted": deleted, "added": added,
        "changed_list": changed_list, "deleted_list": deleted_list, "added_list": added_list,
        "notice_ok": notice_ok, "hashtag_ok": hashtag_ok, "rider_ok": rider_ok,
    }
