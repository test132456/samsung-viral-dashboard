from core import qa_rules

def test_check_banned_finds_terms(refs):
    text = "이 보험은 무조건 전부 보장 됩니다. 걱정 없이 가입하세요."
    hits = qa_rules.check_banned(text, refs["banned"])
    terms = {h["term"] for h in hits}
    assert "무조건" in terms
    assert "전부 보장" in terms
    assert "걱정 없이" in terms

def test_check_banned_clean(refs):
    hits = qa_rules.check_banned("안전한 여행 되세요.", refs["banned"])
    assert hits == []

def test_check_price_detects_won():
    text = "보험료 7,700원부터 시작합니다. 최대 12,000원."
    hits = qa_rules.check_price(text)
    amounts = {h["amount"] for h in hits}
    assert "7,700원" in amounts
    assert "12,000원" in amounts

def test_check_price_none():
    assert qa_rules.check_price("보험료 안내는 별도 문의.") == []

def test_check_riders_flags_wrong_name(refs):
    text = "항공기 지연 특약으로 보상받으세요."
    hits = qa_rules.check_riders(text, refs["riders"])
    assert len(hits) == 1
    assert hits[0]["found"] == "항공기 지연 특약"
    assert hits[0]["official_name"] == "항공기 지연 결항 보상(지수형)(국내 출국) 특약"

def test_check_riders_ok_when_official_used(refs):
    text = "항공기 지연 결항 보상(지수형)(국내 출국) 특약 안내."
    assert qa_rules.check_riders(text, refs["riders"]) == []

def test_check_required_missing(refs):
    text = "해외여행보험 안내드립니다."
    result = qa_rules.check_required(text, refs["required"])
    missing = {m["phrase"] for m in result}
    assert "유료광고" in missing
    assert "본 광고는 상품 가입을 권유하는 목적" in missing

def test_check_required_present(refs, clean_text):
    assert qa_rules.check_required(clean_text, refs["required"]) == []

def test_check_keywords(refs):
    text = "여행 갈 때 보험 챙기세요."
    result = qa_rules.check_keywords(text, refs["keywords"])
    assert result["missing_keywords"]
    assert "해외여행보험" in result["missing_keywords"]
    assert result["has_required_hashtag"] is False
