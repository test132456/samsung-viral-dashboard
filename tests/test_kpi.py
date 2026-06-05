from core import kpi

def test_aggregate_kpis_counts():
    schedule = [{"status": "진행중"}, {"status": "진행중"}, {"status": "완료"}]
    reviews = [{"status": "심의접수", "review_done_date": ""},
               {"status": "심의완료", "review_done_date": "2026-06-02"},
               {"status": "발행완료", "review_done_date": "2026-06-03"}]
    qa = []
    briefing = [{"date": "2026-06-01", "ai_briefing_exposed": "Y"},
                {"date": "2026-06-02", "ai_briefing_exposed": "N"}]
    out = kpi.aggregate_kpis(schedule, reviews, qa, briefing, month="2026-06")
    assert out["in_progress"] == 2
    assert out["review_waiting"] == 1
    assert out["review_done"] == 2
    assert out["published"] == 1
    assert out["briefing_exposed"] == 1

def test_review_status_counts():
    rows = [{"status": "작성중"}, {"status": "작성중"}, {"status": "심의완료"}]
    out = kpi.review_status_counts(rows)
    assert out["작성중"] == 2 and out["심의완료"] == 1

def test_briefing_rollup_by_month():
    rows = [{"date": "2026-06-01", "keyword": "해외여행보험", "ai_briefing_exposed": "Y", "content_type": "정보형"},
            {"date": "2026-06-10", "keyword": "여행자보험", "ai_briefing_exposed": "Y", "content_type": "비교형"},
            {"date": "2026-05-01", "keyword": "해외여행보험", "ai_briefing_exposed": "Y", "content_type": "정보형"}]
    out = kpi.briefing_rollup(rows, "2026-06")
    assert out["exposed_count"] == 2
    assert out["keyword_count"] == 2
