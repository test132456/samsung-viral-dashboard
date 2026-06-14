from core import qa_checklist


def test_all_pass(refs):
    title = "해외여행보험 가입 전 꼭 보세요"  # 키워드 시작 + 25자 이내
    body = ("본 글은 유료광고를 포함합니다. 해외여행보험 안내. "
            "유료광고 본 광고는 상품 가입을 권유하는 목적입니다. "
            "자세히 보기 https://direct.samsungfire.com/vd/x")
    items = qa_checklist.evaluate(title, body, refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["제목 키워드 시작"] == "ok"
    assert by["제목 25자 이내"] == "ok"
    assert by["유료광고 문안(상단)"] == "ok"
    assert by["하단 가입 링크"] == "ok"


def test_keyword_not_at_start_is_warn(refs):
    items = qa_checklist.evaluate("여행 갈 때 해외여행보험 추천", "본문", refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["제목 키워드 시작"] == "warn"


def test_long_title_and_missing_link_fail(refs):
    long_title = "해외여행보험" + "가" * 30
    items = qa_checklist.evaluate(long_title, "유료광고 없는 본문, 링크도 없음", refs)
    by = {i["name"]: i["status"] for i in items}
    assert by["제목 25자 이내"] == "fail"
    assert by["하단 가입 링크"] == "fail"


def test_summary_counts(refs):
    items = qa_checklist.evaluate("", "", refs)
    s = qa_checklist.summary(items)
    assert s["ok"] + s["warn"] + s["fail"] == len(items)
    assert 0 <= s["pass_rate"] <= 100
