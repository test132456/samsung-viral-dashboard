from core import compare_engine

def test_compare_identical_full_match(refs):
    t = "해외여행보험 안내. 유료광고. 본 광고는 상품 가입을 권유하는 목적. #해외여행보험"
    rep = compare_engine.compare(t, t, refs)
    assert rep["match_rate"] == 100.0
    assert rep["changed"] == 0 and rep["deleted"] == 0 and rep["added"] == 0

def test_compare_detects_sentence_changes(refs):
    approved = "첫 문장입니다.\n둘째 문장입니다.\n셋째 문장입니다."
    published = "첫 문장입니다.\n둘째 문장 변경됨.\n셋째 문장입니다.\n넷째 추가 문장."
    rep = compare_engine.compare(approved, published, refs)
    assert rep["match_rate"] < 100.0
    assert rep["changed"] >= 1      # 둘째 문장 변경 (replace)
    assert rep["added"] >= 1        # 넷째 문장 추가 (insert)

def test_compare_missing_notice_flagged(refs):
    approved = "유료광고. 본 광고는 상품 가입을 권유하는 목적. #해외여행보험"
    published = "그냥 후기입니다."   # 고지문구/해시태그 누락
    rep = compare_engine.compare(approved, published, refs)
    assert rep["notice_ok"] is False

def test_compare_changed_count_matches_list(refs):
    approved = "문장 하나.\n문장 둘.\n문장 셋."
    published = "문장 하나.\n완전히 다른 내용 한 줄."
    rep = compare_engine.compare(approved, published, refs)
    assert rep["changed"] == len(rep["changed_list"])
    assert rep["changed"] >= 1
