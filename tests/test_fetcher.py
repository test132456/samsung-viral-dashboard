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

def test_normalize_naver_url():
    assert fetcher._normalize_naver_url("https://blog.naver.com/abc/223456") == "https://m.blog.naver.com/abc/223456"
    # 이미 모바일이면 그대로
    assert fetcher._normalize_naver_url("https://m.blog.naver.com/abc/223456") == "https://m.blog.naver.com/abc/223456"
    # 네이버 블로그가 아니면 원본 유지
    assert fetcher._normalize_naver_url("https://example.com/post/1") == "https://example.com/post/1"
