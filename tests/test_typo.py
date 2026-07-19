from core import typo


def test_check_typos_finds_and_maps():
    r = typo.check_typos("유렵 포르투갈 여행, 스케쥴 확인하고 되요.")
    d = {x["as_is"]: x["to_be"] for x in r}
    assert d.get("유렵") == "유럽"
    assert d.get("스케쥴") == "스케줄"
    assert d.get("되요") == "돼요"
    assert all("context" in x and x["count"] >= 1 for x in r)


def test_no_typos():
    assert typo.check_typos("정상적인 문장입니다.") == []


def test_typo_count():
    r = typo.check_typos("유렵 그리고 또 유렵")
    assert r[0]["as_is"] == "유렵" and r[0]["count"] == 2
