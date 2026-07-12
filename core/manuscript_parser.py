"""워드(.docx) 원고 파서.

워드 중간의 구분 표(순번/이름/URL/제목 2열 표)를 기준으로 여러 명의 원고를 분리한다.
parse_docx_sections(file_bytes) -> [{order, name, url, title, body}]
all_text(file_bytes) -> str   (구분 표가 없을 때 전체 본문)
"""
from __future__ import annotations
import io
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

_LABELS = ("순번", "이름", "URL", "제목")


def _divider_info(tbl: Table) -> dict | None:
    """표가 '순번/이름/URL/제목' 구분 표면 그 값을 반환, 아니면 None."""
    found = {}
    for row in tbl.rows:
        cells = row.cells
        if len(cells) >= 2:
            key = cells[0].text.strip()
            if key in _LABELS:
                found[key] = cells[1].text.strip()
    if "이름" in found or "제목" in found:
        return {"order": found.get("순번", ""), "name": found.get("이름", ""),
                "url": found.get("URL", ""), "title": found.get("제목", "")}
    return None


def parse_docx_sections(file_bytes: bytes) -> list[dict]:
    doc = Document(io.BytesIO(file_bytes))
    sections: list[dict] = []
    current: dict | None = None
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:tbl"):
            tbl = Table(child, doc)
            info = _divider_info(tbl)
            if info is not None:
                current = {**info, "_body": []}
                sections.append(current)
                continue
            if current is not None:  # 일반 표 → 본문에 셀 텍스트 포함
                for row in tbl.rows:
                    for cell in row.cells:
                        t = cell.text.strip()
                        if t:
                            current["_body"].append(t)
        elif child.tag == qn("w:p"):
            if current is not None:
                t = Paragraph(child, doc).text.strip()
                if t:
                    current["_body"].append(t)
    out = []
    for s in sections:
        out.append({"order": s["order"], "name": s["name"], "url": s["url"],
                    "title": s["title"], "body": "\n".join(s["_body"])})
    return out


def all_text(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
