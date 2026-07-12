from core import compare_engine


def test_ignores_zerowidth_and_whitespace(refs):
    approved = "첫 문장입니다.\n둘째 문장입니다.\n셋째 문장입니다."
    # 발행본: 공백 중복 + zero-width(​) + 빈 줄 — 내용은 동일
    published = "첫  문장입니다.​\n\n둘째   문장입니다.\n​\n셋째 문장입니다."
    rep = compare_engine.compare(approved, published, refs)
    assert rep["match_rate"] == 100.0
    assert rep["changed"] == 0 and rep["deleted"] == 0 and rep["added"] == 0


def test_short_fragments_dropped(refs):
    # 단독 부호/한 글자 조각은 문장으로 잡히지 않아 허위 diff가 안 생긴다
    approved = "안녕하세요 여행자보험 안내입니다."
    published = "안녕하세요 여행자보험 안내입니다.\n.\n​\nㅁ"
    rep = compare_engine.compare(approved, published, refs)
    assert rep["added"] == 0 and rep["match_rate"] == 100.0


def test_spacing_only_change_labeled(refs):
    rep = compare_engine.compare("가입되어있어요.", "가입되어 있어요.", refs)
    assert rep["changed_list"] and rep["changed_list"][0]["kind"] == "spacing"


def test_content_change_labeled(refs):
    rep = compare_engine.compare("국내 병원비를 보장합니다.", "해외 병원비를 보장합니다.", refs)
    assert rep["changed_list"] and rep["changed_list"][0]["kind"] == "content"


def test_notice_detected_by_disclosure_marker(refs):
    # 발행본에 실제 고지문구 마커(준법감시인확인필/광고료 등)가 있으면 정상
    assert compare_engine.compare("본문", "준법감시인확인필 제26-1-4731호", refs)["notice_ok"] is True
    assert compare_engine.compare("본문", "소정의 광고비(원고료)를 받아 작성", refs)["notice_ok"] is True
    assert compare_engine.compare("본문", "그냥 여행 후기입니다", refs)["notice_ok"] is False
