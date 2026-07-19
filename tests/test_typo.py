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


# --- 네이버 맞춤법 교정 diff (순수 함수) ---

def test_diff_corrections_word_pairs():
    # 원문 vs (네이버가 돌려줬다고 가정한) 교정문 → as_is→to_be 쌍
    orig = "여행 준비물을 챙기고 출발햇어요."
    corrected = "여행 준비물을 챙기고 출발했어요."
    r = typo.diff_corrections(orig, corrected)
    d = {x["as_is"]: x["to_be"] for x in r}
    assert d.get("출발햇어요.") == "출발했어요."
    assert all(x["count"] >= 1 and "context" in x for x in r)


def test_diff_corrections_identical_is_empty():
    assert typo.diff_corrections("같은 문장.", "같은 문장.") == []
    assert typo.diff_corrections("문장.", "") == []


def test_spellcheck_naver_none_is_safe():
    # 네이버 실패(None)를 흉내 → diff 는 [] 여야 하고 예외가 없어야 함
    assert typo.diff_corrections("아무 문장.", None) == []


def test_diff_corrections_ignores_spacing_only():
    # 띄어쓰기만 다른 교정(네이버 과교정)은 오탈자에서 제외
    assert typo.diff_corrections("여행자보험을 챙겨요.", "여행자 보험을 챙겨요.") == []


def test_no_false_positives_on_clean_text():
    # 정상 문장에서 오탈자를 잘못 잡으면 안 됨(오탐 = 신뢰 하락)
    clean = ("이번 여름 유럽 여행을 준비하며 콘텐츠를 꼼꼼히 확인했습니다. "
             "리더십을 발휘해 여행자 보험도 미리 가입했어요.")
    assert typo.check_typos(clean) == []


def test_expanded_dict_loanword_and_ending_rule():
    d = {x["as_is"]: x["to_be"] for x in typo.check_typos("컨텐츠를 만들었슴니다. 리더쉽 케잌 뵈요 어짜피")}
    assert d.get("컨텐츠") == "콘텐츠"
    assert d.get("슴니다") == "습니다"      # ~슴니다 종결어미 오타 클래스
    assert d.get("리더쉽") == "리더십"
    assert d.get("케잌") == "케이크"
    assert d.get("어짜피") == "어차피"


def test_clean_for_spell_strips_url_tag_legal():
    txt = ("유렵 여행 https://www.samsungfire.com/travel 이메일 a@b.com\n"
           "준법감시인확인필 제26-1-4731호 예금자보호\n"
           "#삼성화재 #해외여행보험")
    c = typo._clean_for_spell(txt)
    assert "http" not in c and "@" not in c        # URL·이메일 제거
    assert "#" not in c                             # 해시태그 제거
    assert "준법감시인확인필" not in c              # 고지문구 줄 제거
    assert "유렵" in c                              # 본문은 유지
