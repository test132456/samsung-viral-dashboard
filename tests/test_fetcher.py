from core import fetcher

SAMPLE_HTML = """
<html><body>
<div class="se-main-container">
  <p class="se-text-paragraph">해외여행보험 후기입니다.</p>
  <p class="se-text-paragraph">항공기 지연 결항 보상 특약 좋아요.</p>
</div>
</body></html>
"""

def test_extract_text_from_naver_html():
    text = fetcher.extract_text(SAMPLE_HTML)
    assert "해외여행보험 후기입니다." in text
    assert "항공기 지연 결항 보상 특약 좋아요." in text

def test_extract_text_empty_returns_blank():
    assert fetcher.extract_text("<html><body></body></html>").strip() == ""
