from core import calendar_view


def test_month_grid_june_2026_layout():
    events = [{"date": "2026-06-05", "task": "공식 업로드", "track": "공식"},
              {"date": "2026-06-11", "task": "배포형 배포", "track": "배포형"}]
    g = calendar_view.month_grid(2026, 6, events)
    # 첫 칸은 일요일(2026-06-01은 월요일이므로 첫 주 index0=빈칸, index1=1일)
    assert g[0][0]["day"] is None
    assert g[0][1]["day"] == 1
    # 모든 실제 날짜 1~30 존재
    days = [c["day"] for wk in g for c in wk if c["day"]]
    assert days[0] == 1 and days[-1] == 30 and len(days) == 30


def test_month_grid_places_events_on_dates():
    events = [{"date": "2026-06-05", "task": "공식 업로드", "track": "공식"}]
    g = calendar_view.month_grid(2026, 6, events)
    cell = [c for wk in g for c in wk if c["date"] == "2026-06-05"][0]
    assert len(cell["events"]) == 1
    assert cell["events"][0]["task"] == "공식 업로드"


def test_month_grid_handles_datetime_and_empty():
    import datetime
    events = [{"date": datetime.datetime(2026, 6, 9, 0, 0), "task": "심의", "track": ""},
              {"date": "", "task": "무시됨", "track": ""}]
    g = calendar_view.month_grid(2026, 6, events)
    cell = [c for wk in g for c in wk if c["date"] == "2026-06-09"][0]
    assert cell["events"][0]["task"] == "심의"
