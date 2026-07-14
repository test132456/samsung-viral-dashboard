from views import ui


def test_diff_pair_highlights_only_changed_char():
    old = "이후 여행 일정을 조율하는 방식이"
    new = "이후 여행 일정을 조율하는 방식히"
    a, b = ui.diff_pair(old, new)
    # 발행: '히'만 빨강 강조, 나머지는 평문
    assert '조율하는 방식' in b
    assert 'background:#ffd6d6' in b and '>히</span>' in b
    assert '히' not in b.replace('>히</span>', '')      # '히'는 강조 span 안에만
    # 원고: '이'가 취소선으로
    assert 'line-through">이</span>' in a
    # 공통 부분은 강조 없음
    assert 'background' not in a


def test_diff_pair_escapes_html():
    a, b = ui.diff_pair("a<b", "a>b")
    assert "&lt;" in a and "&gt;" in b       # < > 이스케이프
    assert "<b" not in a.replace("&lt;", "")


def test_diff_pair_identical():
    a, b = ui.diff_pair("같은 문장", "같은 문장")
    assert a == "같은 문장" and b == "같은 문장"   # 강조 없음
