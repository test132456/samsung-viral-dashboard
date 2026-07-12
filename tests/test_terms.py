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
