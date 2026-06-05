from core import schedule_gen


def test_month_drafts_july():
    ev = schedule_gen.month_drafts(2026, 7)
    assert len(ev) == 17
    assert all(e["date"].startswith("2026-07") for e in ev)
    # 이번달(7월) / 다음달(8월) 라벨이 모두 등장
    tasks = " ".join(e["task"] for e in ev)
    assert "(7월)" in tasks and "(8월)" in tasks
    # 트랙 분류 존재
    tracks = {e["track"] for e in ev}
    assert "공식" in tracks and "배포형" in tracks


def test_december_rolls_to_january():
    ev = schedule_gen.month_drafts(2026, 12)
    tasks = " ".join(e["task"] for e in ev)
    assert "(12월)" in tasks and "(1월)" in tasks   # 다음달 = 1월
    assert all(int(e["date"][8:10]) <= 31 for e in ev)


def test_generate_multiple_months():
    ev = schedule_gen.generate(["2026-07", "2026-08", "2026-09"])
    assert len(ev) == 17 * 3
    months = {e["date"][:7] for e in ev}
    assert months == {"2026-07", "2026-08", "2026-09"}
