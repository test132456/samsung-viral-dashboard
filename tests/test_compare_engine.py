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


def test_hashtags_excluded_from_comparison():
    from core import compare_engine
    txt = "준법감시인확인필 제00-0-0000호 (4078) #삼성화재다이렉트#해외여행보험 #일본여행"
    sents = compare_engine._sentences(txt)
    assert any("준법감시인확인필" in s for s in sents)   # 번호 줄은 남고
    assert not any("#" in s for s in sents)              # 해시태그는 전부 제외


def test_notice_number_change_not_polluted_by_hashtags():
    from core import compare_engine
    a = "준법감시인확인필 제00-0-0000호 #해외여행보험 #일본여행"
    b = "준법감시인확인필 제26-1-4731호 #해외여행보험 #일본여행"
    rep = compare_engine.compare(a, b, {})
    # 번호만 바뀌고 해시태그는 그대로 → 변경 블록에 해시태그가 섞이면 안 됨
    for ch in rep["changed_list"]:
        assert "#" not in ch["from"] and "#" not in ch["to"]


def test_revision_request_categorizes_and_directs():
    from core import compare_engine as ce
    a = "정말 중요하게 생각해야. 동반가입과 요청시 확인."
    b = "가장 중요하게 생각해야. 동반 가입과 요청 시 확인."
    rep = ce.compare(a, b, {})
    txt = ce.revision_request(rep, blogger="여름", approved_title="원고 제목")
    assert "<수정 요청 · 여름>" in txt
    assert "가장 → 정말" in txt                 # 문구: 현재(발행) → 수정(원고)
    assert "동반 가입과 → 동반가입과" in txt      # 띄어쓰기 섹션
    assert "문구 수정" in txt and "띄어쓰기" in txt
    assert "제목 확인" in txt


def test_revision_request_no_change():
    from core import compare_engine as ce
    txt = ce.revision_request(ce.compare("같은 문장이에요.", "같은 문장이에요.", {}))
    assert "수정 사항 없음" in txt


def test_revision_request_punctuation_category():
    from core import compare_engine as ce
    a = "무슨 일이 생기겠어 … 라는 생각이 들어요."   # 원고: … 있음
    b = "무슨 일이 생기겠어 라는 생각이 들어요."      # 발행: … 없음
    txt = ce.revision_request(ce.compare(a, b, {}), blogger="여름")
    assert "문장부호 수정" in txt
    assert "…" in txt   # 문장부호(…) 차이가 잡힘
