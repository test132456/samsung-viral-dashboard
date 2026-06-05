import pytest

@pytest.fixture
def refs():
    """가짜 기준데이터 (실제 시트 read 결과를 모방한 dict)."""
    return {
        "banned": ["무조건", "전부 보장", "훨씬", "걱정 없이", "모두", "빈번하게", "자주", "는 물론", "뿐만 아니라"],
        "required": [{"phrase": "유료광고", "type": "유료광고"},
                     {"phrase": "본 광고는 상품 가입을 권유하는 목적", "type": "고지"}],
        "riders": [{"official_name": "항공기 지연 결항 보상(지수형)(국내 출국) 특약",
                    "common_mistakes": ["항공기 지연 특약", "항공기지연특약"]}],
        "keywords": [{"keyword": "해외여행보험", "type": "키워드"},
                     {"keyword": "여행자보험", "type": "키워드"},
                     {"keyword": "해외여행보험", "type": "해시태그"}],
    }

@pytest.fixture
def clean_text():
    return ("이 글은 유료광고를 포함합니다. 해외여행보험 가입 시 항공기 지연 결항 보상(지수형)"
            "(국내 출국) 특약을 확인하세요. 본 광고는 상품 가입을 권유하는 목적입니다. #해외여행보험")
