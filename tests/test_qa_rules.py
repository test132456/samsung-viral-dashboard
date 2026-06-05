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
