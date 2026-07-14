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


def test_parse_link_params_utm_term():
    from core import fetcher
    url = ("https://direct.samsungfire.com/ria/pc/product/factory/?state=Front&product=travel"
           "&utm_source=naver&utm_campaign=m_blog_none&utm_term=F2606VR0030")
    r = fetcher.parse_link_params(url)
    assert r["term"] == "F2606VR0030"
    assert r["key"] == "utm_term"
    assert len(r["params"]) == 5


def test_parse_link_params_last_when_no_utm_term():
    from core import fetcher
    r = fetcher.parse_link_params("https://x.com/a?foo=1&code=ABC123")
    assert r["term"] == "ABC123" and r["key"] == "code"


def test_parse_link_params_no_query():
    from core import fetcher
    r = fetcher.parse_link_params("https://x.com/a")
    assert r["term"] is None and r["params"] == []


def test_is_shortener():
    from core import fetcher
    assert fetcher.is_shortener("https://tinyurl.com/abc")
    assert not fetcher.is_shortener("https://direct.samsungfire.com/x?y=1")
