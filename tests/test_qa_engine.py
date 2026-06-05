from core import qa_engine

def test_run_qa_aggregates_rule_violations(refs):
    text = "이 보험 무조건 전부 보장! 항공기 지연 특약, 보험료 7,700원."
    report = qa_engine.run_qa(text, refs, ai_judge=None)  # 규칙만
    assert report["banned_count"] >= 2
    assert report["rider_error_count"] == 1
    assert report["price_found"] is True
    assert report["missing_phrase"] is True       # 유료광고/고지 없음
    assert 0 <= report["qa_score"] <= 100
    assert report["qa_score"] < 100

def test_run_qa_clean_scores_high(refs, clean_text):
    report = qa_engine.run_qa(clean_text, refs, ai_judge=None)
    assert report["banned_count"] == 0
    assert report["rider_error_count"] == 0
    assert report["qa_score"] >= 90

def test_run_qa_uses_ai_judge(refs, clean_text):
    calls = []
    def fake_judge(text):
        calls.append(text)
        return [{"snippet": "걱정 마세요", "reason": "단정", "suggestion": "참고하세요"}]
    report = qa_engine.run_qa(clean_text, refs, ai_judge=fake_judge)
    assert len(calls) == 1
    assert len(report["ai_findings"]) == 1
