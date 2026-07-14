from views import ui


def test_diff_pair_highlights_only_changed_char():
    old = "이후 여행 일정을 조율하는 방식이"
    new = "이후 여행 일정을 조율하는 방식히"
    a, b = ui.diff_pair(old, new)
    # 발행: '히'만 빨강 강조
    assert 'background:#ffd6d6' in b and '>히</span>' in b
    # 원고: '이'가 취소선으로
    assert 'line-through' in a and '>이</span>' in a
    # 딱 한 군데만 강조 + 공통 접두부는 그대로
    assert a.count('<span') == 1 and b.count('<span') == 1
    assert a.startswith('이후 여행 일정을 조율하는 방식')
    assert b.startswith('이후 여행 일정을 조율하는 방식')


def test_diff_pair_shows_space_marker():
    # 발행에서 공백이 추가된 경우 → ␣ 로 보이게
    a, b = ui.diff_pair("해외여행보험이에요", "해외여행보험 이에요")
    assert "␣" in b                       # 추가된 공백이 기호로 표시
    assert "<span" in b                    # 강조 span 안에
    # 원고에서 공백이 빠진 경우도 표시
    a2, b2 = ui.diff_pair("특약 이나", "특약이나")
    assert "␣" in a2 and "line-through" in a2


def test_diff_pair_escapes_html():
    a, b = ui.diff_pair("a<b", "a>b")
    assert "&lt;" in a and "&gt;" in b       # < > 이스케이프
    assert "<b" not in a.replace("&lt;", "")


def test_diff_pair_identical():
    a, b = ui.diff_pair("같은 문장", "같은 문장")
    assert a == "같은 문장" and b == "같은 문장"   # 강조 없음
