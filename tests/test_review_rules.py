from core import review_rules as rr


def test_double_space():
    assert len(rr.check_double_space("가입 시,  가입 금액 한도")) == 1   # 2칸
    assert rr.check_double_space("정상 한 칸 문장입니다.") == []
    assert len(rr.check_double_space("앞   뒤")) == 1                  # 3칸도 1건


def test_superlatives_boundary():
    d = {h["hit"] for h in rr.check_superlatives("이건 가장 좋은 최고의 상품, 무조건 추천")}
    assert "가장" in d and "최고" in d and "무조건" in d
    # 오탐 방지: '가장자리'(가장+자, 공백 없음)는 안 잡힘
    assert rr.check_superlatives("책상 가장자리에 두었다") == []


def test_vague_deung_no_false_positive():
    assert len(rr.check_vague_deung("호텔 등을 예약했다")) == 1        # '등'=기타
    assert rr.check_vague_deung("평등을 지향한다") == []               # 평등
    assert rr.check_vague_deung("회원 등록 등급 확인") == []           # 등록/등급


def test_causal_assertion():
    hits = rr.check_causal_assertion("상한 음식 섭취로 인해 식중독에 걸렸다.")
    assert len(hits) == 1
    assert rr.check_causal_assertion("여행 준비물을 챙겼다.") == []


def test_causal_narrative_food_illness():
    # 명시적 인과어 없이 '먹었 … 식중독' 서술도 잡음(음식→식중독 단정 암시)
    narr = "고기며 라멘 막 먹었었거든요? 근데 다음날 병원 가보니 식중독이라는 거 있죠"
    assert len(rr.check_causal_assertion(narr)) >= 1
    # '상비약 먹고'는 음식이 아니므로 제외(오탐 방지)
    assert rr.check_causal_assertion("상비약만 먹고 버텼는데 동생이 식중독 증상이었대요") == []
    # 일반 식중독 보장 설명(섭취 서술 없음)은 안 잡음
    assert rr.check_causal_assertion("식중독 보장 특약으로 대비하세요.") == []


def test_rider_naming_needs_특약():
    riders = ["항공기 지연 결항 보상(지수형)(국내 출국) 특약"]
    # 정식명(핵심어 + 괄호부기 + 특약)으로 쓰면 통과
    ok = "항공기 지연 결항 보상(지수형)(국내 출국) 특약 에 가입하세요"
    assert rr.check_rider_naming(ok, riders) == []
    # 핵심어만 쓰고 근처에 '특약' 없으면 후보
    bad = "항공기 지연 결항 보상 을 꼭 챙기세요. 여행 잘 다녀오세요 정말로."
    assert len(rr.check_rider_naming(bad, riders)) == 1


def test_limitation_notice():
    assert len(rr.check_limitation_notice("이 상품은 보장이 좋고 지급이 빠릅니다.")) == 1
    assert rr.check_limitation_notice("보장 내용과 함께 면책 사항, 지급 제한도 안내드립니다.") == []


def test_check_all_shape():
    res = rr.check_all("가장 좋은 상품, 호텔 등을 보장합니다.", ["수하물 지연 손실 특약"])
    keys = {r["key"] for r in res}
    assert keys == {"double_space", "superlative", "deung", "causal", "rider_naming", "limitation"}
    assert all("grade" in r and "hits" in r and "title" in r for r in res)
