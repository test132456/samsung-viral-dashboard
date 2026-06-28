from core import kpi


def test_qa_summary():
    rows = [{"qa_score": "88", "checked_at": "2026-06-01"},
            {"qa_score": "42", "checked_at": "2026-06-10"},
            {"qa_score": "70", "checked_at": "2026-05-30"}]
    out = kpi.qa_summary(rows, "2026-06")
    assert out["latest_score"] == 70          # 전체 마지막 행
    assert out["count"] == 2                   # 당월(6월) 2건


def test_qa_summary_empty():
    out = kpi.qa_summary([], "2026-06")
    assert out["latest_score"] is None and out["count"] == 0


def test_compare_summary_avg():
    rows = [{"match_rate": "98", "checked_at": "2026-06-01"},
            {"match_rate": "90", "checked_at": "2026-06-02"},
            {"match_rate": "50", "checked_at": "2026-05-01"}]
    out = kpi.compare_summary(rows, "2026-06")
    assert out["avg_match"] == 94.0            # (98+90)/2
    assert out["count"] == 2


def test_compare_summary_empty():
    out = kpi.compare_summary([], "2026-06")
    assert out["avg_match"] is None and out["count"] == 0
