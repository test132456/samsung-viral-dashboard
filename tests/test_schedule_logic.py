from datetime import date
from core import schedule_logic

def test_dday_label():
    today = date(2026, 6, 5)
    assert schedule_logic.dday_label("2026-06-08", today) == "D-3"
    assert schedule_logic.dday_label("2026-06-06", today) == "D-1"
    assert schedule_logic.dday_label("2026-06-05", today) == "D-DAY"
    assert schedule_logic.dday_label("2026-06-03", today) == "지연"
    assert schedule_logic.dday_label("", today) == ""

def test_compute_status_done():
    row = {"publish_actual_date": "2026-06-01"}
    assert schedule_logic.compute_status(row, date(2026, 6, 5)) == "완료"

def test_compute_status_late():
    row = {"publish_plan_date": "2026-06-03", "publish_actual_date": ""}
    assert schedule_logic.compute_status(row, date(2026, 6, 5)) == "지연"

def test_compute_status_in_progress():
    row = {"draft_submit_date": "2026-06-02", "publish_plan_date": "2026-06-20", "publish_actual_date": ""}
    assert schedule_logic.compute_status(row, date(2026, 6, 5)) == "진행중"

def test_compute_status_planned():
    row = {"publish_plan_date": "2026-06-20"}
    assert schedule_logic.compute_status(row, date(2026, 6, 5)) == "예정"
