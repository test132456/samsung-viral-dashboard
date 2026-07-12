from core import terms

_TERMS = """제3관 특별약관
1. 항공기 지연 결항 보상(지수형)(국내 출국) 특약
2. 해외여행 실손의료비(상해) 특약
· 휴대품 손해 특약
일반 문장 (특약 단어만 포함, 특약명 아님)
"""


def test_extract_riders():
    riders = terms.extract_riders(_TERMS)
    assert "항공기 지연 결항 보상(지수형)(국내 출국) 특약" in riders
    assert "해외여행 실손의료비(상해) 특약" in riders
    assert "휴대품 손해 특약" in riders
    assert len(riders) >= 3


def test_coverage_included_and_missing():
    official = ["항공기 지연 결항 보상(지수형)(국내 출국) 특약",
                "해외여행 실손의료비(상해) 특약",
                "휴대품 손해 특약"]
    ms = "이 상품은 항공기 지연 결항 보상(지수형)(국내 출국) 특약과 휴대품 손해 특약을 포함합니다."
    cov = terms.coverage(ms, official)
    assert cov["total"] == 3
    assert "항공기 지연 결항 보상(지수형)(국내 출국) 특약" in cov["included"]
    assert "휴대품 손해 특약" in cov["included"]
    assert "해외여행 실손의료비(상해) 특약" in cov["missing"]
    assert cov["included_count"] == 2


def test_verify_usage_ok_and_mismatch():
    from core import terms
    ref = ["여행중 휴대품 손해(분실제외) 특약",
           "항공기 지연 결항 보상(지수형)(국내 출국) 특약"]
    ms = "이번엔 여행중 휴대품 손해(분실제외) 특약 과 항공기 지연 특약 을 넣음"
    rv = terms.verify_usage(ms, ref)
    assert "여행중 휴대품 손해(분실제외) 특약" in rv["ok"]      # 정확 표기
    assert "항공기 지연 결항 보상(지수형)(국내 출국) 특약" in rv["mismatch"]  # 오기 의심
    assert rv["ok_count"] == 1 and rv["mismatch_count"] == 1


def test_verify_usage_spacing_tolerant():
    from core import terms
    ref = ["수하물 지연(6시간 이상)·손실 추가비용 특약"]
    ms = "수하물지연(6시간 이상)·손실 추가비용특약 보장"   # 띄어쓰기 달라도 OK
    rv = terms.verify_usage(ms, ref)
    assert rv["ok"] == ref and rv["mismatch"] == []


def test_verify_usage_sibling_not_flagged():
    from core import terms
    ref = ["항공기 지연 결항 보상(지수형)(국내 출국) 특약",
           "항공기 지연 결항 보상(지수형)(국내 출국 제외) 특약"]
    ms = "항공기 지연 결항 보상(지수형)(국내 출국) 특약 가입"   # 하나를 정확히 사용
    rv = terms.verify_usage(ms, ref)
    assert ref[0] in rv["ok"]
    assert rv["mismatch"] == []      # 형제 특약을 오기로 잡지 않음
