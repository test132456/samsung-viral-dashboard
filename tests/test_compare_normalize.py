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
