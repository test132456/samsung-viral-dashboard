"""워드(.docx) 원고 파서.

워드 중간의 구분 표(순번/이름/URL/제목 2열 표)를 기준으로 여러 명의 원고를 분리한다.
취소선(빨간 줄) 텍스트는 '삭제 표시'로 보고 본문에서 제외하되 개수를 세어 알려준다.
parse_docx_sections(file_bytes) -> [{order, name, url, title, body, deleted}]
all_text(file_bytes) -> str   (구분 표가 없을 때 전체 본문, 취소선 제외)
"""
from __future__ import annotations
import io
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

_LABELS = ("순번", "이름", "URL", "제목")


def _para_parts(paragraph: Paragraph) -> tuple[str, str]:
    """문단을 (보이는 텍스트, 취소선=삭제 텍스트)로 분리."""
    visible, struck = [], []
    for run in paragraph.runs:
        if not run.text:
            continue
        if run.font.strike:
            struck.append(run.text)
        else:
            visible.append(run.text)
    return "".join(visible), "".join(struck)


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
                current = {**info, "_body": [], "_deleted": []}
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
                vis, struck = _para_parts(Paragraph(child, doc))
                if vis.strip():
                    current["_body"].append(vis.strip())
                if struck.strip():
                    current["_deleted"].append(struck.strip())
    out = []
    for s in sections:
        out.append({"order": s["order"], "name": s["name"], "url": s["url"],
                    "title": s["title"], "body": "\n".join(s["_body"]), "deleted": s["_deleted"]})
    return out


def all_text(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    out = []
    for p in doc.paragraphs:
        vis, _ = _para_parts(p)
        if vis.strip():
            out.append(vis.strip())
    return "\n".join(out)


def count_images(file_bytes: bytes) -> int:
    """워드 문서에 삽입된 이미지 수(인라인+플로팅) — a:blip 요소 기준."""
    doc = Document(io.BytesIO(file_bytes))
    return sum(1 for el in doc.element.iter() if el.tag.endswith("}blip"))


def read_pdf(file_bytes: bytes) -> str:
    """PDF 전체 텍스트 추출(pypdf). 스캔본(이미지 PDF)은 텍스트가 거의 안 나올 수 있음."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)
