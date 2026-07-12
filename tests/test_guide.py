import io
from pptx import Presentation
from pptx.util import Inches
from core import guide


def _make_pptx():
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    tb = slide.shapes.add_textbox(Inches(0.3), Inches(0.3), Inches(9), Inches(1)).text_frame
    tb.text = "하단 해시태그: #삼성화재다이렉트 #해외여행보험 #항공지연"
    tb2 = slide.shapes.add_textbox(Inches(0.3), Inches(1.5), Inches(9), Inches(0.5)).text_frame
    tb2.text = "[표현 불가 문구]"
    tbl = slide.shapes.add_table(3, 3, Inches(0.3), Inches(2.2), Inches(9), Inches(2)).table
    tbl.cell(0, 0).text, tbl.cell(0, 1).text, tbl.cell(0, 2).text = "불가 표현", "사유", "예시"
    tbl.cell(1, 0).text, tbl.cell(1, 1).text, tbl.cell(1, 2).text = "무조건", "삭제 필요", "예시문"
    tbl.cell(2, 0).text, tbl.cell(2, 1).text, tbl.cell(2, 2).text = "빈번하게, 자주", "근거 없음", "예시문"
    b = io.BytesIO()
    prs.save(b)
    return b.getvalue()


def test_parse_guide():
    g = guide.parse_guide(guide.extract_text(_make_pptx()))
    assert "#해외여행보험" in g["hashtags"] and "#삼성화재다이렉트" in g["hashtags"]
    assert "무조건" in g["banned"]
    assert "빈번하게" in g["banned"] and "자주" in g["banned"]  # 콤마 분리


def test_check_against_manuscript():
    g = guide.parse_guide(guide.extract_text(_make_pptx()))
    ms = "이 보험 무조건 좋아요. #삼성화재다이렉트 해외여행보험 해외여행보험 해외여행보험 안내."
    res = guide.check(ms, g)
    assert "무조건" in res["banned_hits"]
    assert "#해외여행보험" in res["tags_missing"]     # 원고에 이 태그 없음
    assert "#삼성화재다이렉트" in res["tags_included"]
    assert res["keyword_count"] == 3 and res["keyword_ok"] is True
