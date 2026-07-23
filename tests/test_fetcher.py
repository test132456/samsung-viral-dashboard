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


def test_extract_links_and_candidates():
    from core import fetcher
    html = """
    <div class="se-main-container">
      <p>본문 <a href="https://blog.naver.com/me/1">내부글</a></p>
      <div class="se-oglink"><a href="https://tinyurl.com/abc123"><b>삼성화재 다이렉트</b></a></div>
      <a href="https://direct.samsungfire.com/ria/x?utm_term=F2606VR0030">직접</a>
    </div>"""
    links = fetcher.extract_links(html)
    assert "https://tinyurl.com/abc123" in links
    assert "https://blog.naver.com/me/1" in links       # 모든 http 링크 수집
    cands = fetcher.tracking_link_candidates(links)
    assert "https://tinyurl.com/abc123" in cands
    assert any("samsungfire.com" in c for c in cands)
    assert not any("blog.naver.com" in c for c in cands)  # 내부 링크는 후보 제외


def test_naver_candidates_order():
    from core import fetcher
    cands = fetcher._naver_candidates("https://blog.naver.com/agi45/224353088412")
    # PostView(PC) 먼저 → 모바일 → 원본 (403 대비 여러 형태 재시도)
    assert cands[0] == "https://blog.naver.com/PostView.naver?blogId=agi45&logNo=224353088412"
    assert any("m.blog.naver.com/agi45/224353088412" in c for c in cands)
    # 블로그 글 형태가 아니면 원본만
    assert fetcher._naver_candidates("https://example.com/x") == ["https://example.com/x"]


def test_resolve_redirects_shortcircuits_on_utm_term():
    from core import fetcher
    # URL에 이미 utm_term 이 있으면 네트워크 접속 없이 그대로 반환(광고주 서버 타임아웃 회피)
    u = "https://direct.samsungfire.com/vd/overture_index.jsp?OTK=x&utm_source=naver&utm_term=F2606VR0030"
    assert fetcher.resolve_redirects(u) == u
    assert fetcher.parse_link_params(u)["term"] == "F2606VR0030"
