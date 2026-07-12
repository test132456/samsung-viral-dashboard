import io
from docx import Document
from core import manuscript_parser


def _make_docx(entries):
    """entries: [(순번, 이름, url, 제목, [본문줄...])] → docx bytes."""
    d = Document()
    for order, name, url, title, body_lines in entries:
        t = d.add_table(rows=4, cols=2)
        t.cell(0, 0).text, t.cell(0, 1).text = "순번", order
        t.cell(1, 0).text, t.cell(1, 1).text = "이름", name
        t.cell(2, 0).text, t.cell(2, 1).text = "URL", url
        t.cell(3, 0).text, t.cell(3, 1).text = "제목", title
        for line in body_lines:
            d.add_paragraph(line)
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


def test_splits_by_blogger():
    data = _make_docx([
        ("(1)", "제아", "https://blog.naver.com/jea", "제아 제목", ["제아 본문 첫 줄", "둘째 줄"]),
        ("(2)", "여름", "https://blog.naver.com/hylim1224", "여름 제목입니다", ["여름 본문 첫 줄"]),
    ])
    secs = manuscript_parser.parse_docx_sections(data)
    assert len(secs) == 2
    assert [s["name"] for s in secs] == ["제아", "여름"]
    summer = [s for s in secs if s["name"] == "여름"][0]
    assert summer["title"] == "여름 제목입니다"
    assert summer["url"] == "https://blog.naver.com/hylim1224"
    assert "여름 본문 첫 줄" in summer["body"]
    assert "제아 본문" not in summer["body"]   # 다른 사람 본문 섞이지 않음


def test_no_divider_returns_empty_sections():
    d = Document()
    d.add_paragraph("구분 표 없는 일반 원고")
    b = io.BytesIO(); d.save(b)
    assert manuscript_parser.parse_docx_sections(b.getvalue()) == []
    assert "일반 원고" in manuscript_parser.all_text(b.getvalue())


def test_strikethrough_excluded_and_counted():
    d = Document()
    t = d.add_table(rows=4, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = "순번", "(1)"
    t.cell(1, 0).text, t.cell(1, 1).text = "이름", "여름"
    t.cell(2, 0).text, t.cell(2, 1).text = "URL", "https://x"
    t.cell(3, 0).text, t.cell(3, 1).text = "제목", "제목입니다"
    p = d.add_paragraph()
    p.add_run("정상 문장입니다 ")
    dele = p.add_run("삭제된 부분입니다")
    dele.font.strike = True
    b = io.BytesIO(); d.save(b)
    secs = manuscript_parser.parse_docx_sections(b.getvalue())
    assert len(secs) == 1
    assert "정상 문장입니다" in secs[0]["body"]
    assert "삭제된 부분" not in secs[0]["body"]        # 취소선 제외
    assert secs[0]["deleted"] and "삭제된 부분입니다" in secs[0]["deleted"][0]
