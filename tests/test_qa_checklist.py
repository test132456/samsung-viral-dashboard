from core import qa_checklist


def _full_body():
    """가이드 플로우를 모두 갖춘 본문."""
    return ("본 글은 유료광고를 포함합니다. 해외여행보험 안내드립니다. "
            "항공기 지연 결항 보상(지수형)(국내 출국) 특약 가입 시, 가입 금액 한도로 보장. "
            "본 광고는 상품 가입을 권유하는 목적입니다. 준법감시인확인필 제00호. "
            "#해외여행보험 #항공기지연 #해외여행자보험")


def test_all_pass(refs):
    title = "해외여행보험 가입 전 꼭 보세요"  # 키워드로 시작
    items = qa_checklist.evaluate(title, _full_body(), refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["제목 키워드 시작"] == "ok"
    assert "제목 25자 이내" not in by            # 25자 제한 항목 제거됨
    assert by["유료광고 문안(상단)"] == "ok"
    assert by["특약 보장문장"] == "ok"
    assert by["고지문구(하단)"] == "ok"
    assert by["해시태그(최하단)"] == "ok"


def test_keyword_not_at_start_is_warn(refs):
    items = qa_checklist.evaluate("여행 갈 때 해외여행보험 추천", "본문", refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["제목 키워드 시작"] == "warn"


def test_benefit_sentence_missing_fails(refs):
    # 특약은 언급하나 '가입 금액 한도로 보장' 문장이 없음
    body = "항공기 지연 결항 보상(지수형)(국내 출국) 특약 을 소개합니다. 좋아요."
    items = qa_checklist.evaluate("해외여행보험 안내", body, refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["특약 보장문장"] == "fail"


def test_benefit_sentence_spacing_tolerant(refs):
    body = "항공기 지연 특약 가입시, 가입금액 한도로 보장 됩니다."  # 띄어쓰기 달라도 인식
    items = qa_checklist.evaluate("해외여행보험", body, refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["특약 보장문장"] == "ok"


def test_hashtags_and_notice_position(refs):
    # 해시태그 없음 → fail
    items = qa_checklist.evaluate("해외여행보험 안내", "해시태그 없는 본문 특약", refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["해시태그(최하단)"] == "fail"


def test_long_title_ok_now(refs):
    # 25자 넘어도 이상 없어야 함 (제목 길이 항목 제거)
    long_title = "해외여행보험" + "가" * 30
    by = {i["name"]: i["status"] for i in qa_checklist.evaluate(long_title, "본문", refs)}
    assert "제목 25자 이내" not in by
    assert by["제목 키워드 시작"] == "ok"   # 여전히 키워드로 시작하니 통과


def test_summary_counts(refs):
    items = qa_checklist.evaluate("", "", refs)
    s = qa_checklist.summary(items)
    assert s["ok"] + s["warn"] + s["fail"] == len(items)
    assert 0 <= s["pass_rate"] <= 100


def test_official_blog_marks_paid_ad_na(refs):
    items = qa_checklist.evaluate("해외여행보험 안내", "유료광고 없는 본문입니다", refs, is_official=True)
    by = {i["name"]: i["status"] for i in items}
    assert by["유료광고 문안(상단)"] == "na"


def test_experience_blog_checks_paid_ad(refs):
    items = qa_checklist.evaluate("해외여행보험 안내", "유료광고 포함 본문입니다", refs, is_official=False)
    by = {i["name"]: i["status"] for i in items}
    assert by["유료광고 문안(상단)"] in ("ok", "warn")


def test_url_step(refs):
    body_url = "삼성화재 해외여행보험 가입 https://direct.samsungfire.com/mall/PP030701_001.html 여기서"
    by = {i["name"]: i["status"] for i in qa_checklist.evaluate("해외여행보험", body_url, refs)}
    assert by["가입 링크(URL)"] == "ok"
    by2 = {i["name"]: i["status"] for i in qa_checklist.evaluate("해외여행보험", "링크 없는 본문", refs)}
    assert by2["가입 링크(URL)"] == "warn"
    # 플로우 7단계 (맞춤법 / 제목 키워드 / 유료광고 / 특약 보장문장 / 가입 링크 / 고지문구 / 해시태그)
    assert len(qa_checklist.NAMES) == 7
    assert qa_checklist.NAMES[0] == "맞춤법 검사"


def test_spellcheck_flow_step(refs):
    # 오탈자 있으면 맞춤법 검사 = fail + 어느 단어인지 detail에
    items = qa_checklist.evaluate("해외여행보험", "유렵 여행 스케쥴 확인", refs)
    d = {i["name"]: i for i in items}
    assert d["맞춤법 검사"]["status"] == "fail"
    assert "유렵→유럽" in d["맞춤법 검사"]["detail"]
    # 오탈자 없으면 ok
    ok = {i["name"]: i for i in qa_checklist.evaluate("해외여행보험", "정상 본문입니다", refs)}
    assert ok["맞춤법 검사"]["status"] == "ok"


def test_spellcheck_flow_naver_blocked_is_warn(refs):
    # 네이버 차단(naver_ok=False) + 사전 오탈자 없음 → 초록 'ok'가 아니라 '△ warn'으로 정직하게
    blocked = {i["name"]: i for i in qa_checklist.evaluate(
        "해외여행보험", "정상 본문입니다", refs, typos=[], naver_ok=False)}
    assert blocked["맞춤법 검사"]["status"] == "warn"
    assert "네이버" in blocked["맞춤법 검사"]["detail"]
