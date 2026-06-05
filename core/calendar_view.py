"""월 달력 그리드 생성 (일요일 시작). 순수 함수 — UI를 모름."""
from __future__ import annotations
import calendar as _cal
import datetime


def _to_date_str(v) -> str:
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime("%Y-%m-%d")
    return str(v).strip()[:10] if v else ""


def month_grid(year: int, month: int, events: list[dict]) -> list[list[dict]]:
    """events: [{date:'YYYY-MM-DD', task, track}, ...].

    반환: 주 단위 리스트. 각 주는 7개 셀(일~토 순). 셀:
      {day: int|None, date: 'YYYY-MM-DD'|'', in_month: bool, events: [event,...]}
    day=None 은 달력 앞뒤 빈 칸(이전/다음 달).
    """
    by_date: dict[str, list[dict]] = {}
    for e in events:
        d = _to_date_str(e.get("date", ""))
        if d:
            by_date.setdefault(d, []).append(e)

    weeks = _cal.Calendar(firstweekday=6).monthdayscalendar(year, month)  # 6 = 일요일 시작
    grid: list[list[dict]] = []
    for wk in weeks:
        row = []
        for day in wk:
            if day == 0:
                row.append({"day": None, "date": "", "in_month": False, "events": []})
            else:
                ds = f"{year:04d}-{month:02d}-{day:02d}"
                row.append({"day": day, "date": ds, "in_month": True, "events": by_date.get(ds, [])})
        grid.append(row)
    return grid
