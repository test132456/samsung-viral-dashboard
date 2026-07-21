from core import req_check


def _full_body():
    return ("*이 포스팅은 삼성화재 다이렉트로부터 소정의 광고비(원고료)를 받아 작성되었습니다\n"
            "삼성화재 다이렉트 해외여행보험 소개입니다. 여행자보험과 비교해 장점이 큽니다. "
            "해외여행보험 가입 팁과 해외여행보험 추천 이유를 정리했어요.\n"
            "가입 링크 https://direct.samsungfire.com/mall/PP030701_001.html\n"
            "준법감시인확인필 제00호\n"
            "#삼성화재다이렉트 #삼성화재다이렉트해외여행보험 #해외여행보험 #항공지연 "
            "#지연결항 #해외여행자보험 #해외여행보험추천 #해외여행보험후기")


def test_full_manuscript_passes():
    title = "해외여행보험 출국 귀국 항공기 지연 보상 추천"
    items = req_check.evaluate(title, _full_body(), is_official=False)
    by = {i["name"]: i for i in items}
    assert by["브랜드·보험명 정확 표기"]["status"] == "ok"
    assert by["타 보험사 언급 지양"]["status"] == "ok"
    assert by["필수 해시태그 포함"]["status"] == "ok"
    assert by["허용 상품 링크만 사용"]["status"] == "ok"
    assert by["유료광고 문안(상단)"]["status"] == "ok"
    assert by["준법감시인확인필(하단)"]["status"] == "ok"
    assert "이미지" not in " ".join(by)                       # 이미지 항목 제외됨
    assert "<b>" in by["브랜드·보험명 정확 표기"]["evidence"]   # 근거에 매칭어 강조


def test_competitor_mention_flagged():
    items = req_check.evaluate("해외여행보험", "현대해상 여행자보험도 좋아요")
    by = {i["name"]: i for i in items}
    assert by["타 보험사 언급 지양"]["status"] == "fail"
    assert "현대해상" in by["타 보험사 언급 지양"]["detail"]


def test_foreign_link_flagged():
    items = req_check.evaluate("해외여행보험", "링크 https://hi.example.com/x 참고")
    by = {i["name"]: i for i in items}
    assert by["허용 상품 링크만 사용"]["status"] == "fail"


def test_keyword_count_excludes_hashtags():
    body = "해외여행보험 소개 #해외여행보험 #해외여행보험추천 #해외여행보험후기"  # 본문 1개
    items = req_check.evaluate("t", body)
    by = {i["name"]: i for i in items}
    assert "1개" in by["'해외여행보험' 키워드 3개 이상"]["detail"]
    assert by["'해외여행보험' 키워드 3개 이상"]["status"] == "warn"     # 1개 < 3 → 부족


def test_keyword_count_three_or_more_ok():
    # 3개 이상이면 상한 없이 충족(6개도 ok) — 사용자 요청 반영
    by3 = {i["name"]: i for i in req_check.evaluate("t", "해외여행보험 " * 3)}
    assert by3["'해외여행보험' 키워드 3개 이상"]["status"] == "ok"
    by6 = {i["name"]: i for i in req_check.evaluate("t", "해외여행보험 " * 6)}
    assert by6["'해외여행보험' 키워드 3개 이상"]["status"] == "ok"      # 예전엔 warn, 이제 ok


def test_title_keyword_after_brand_prefix_is_ok():
    # 브랜드 접두어 '삼성화재 다이렉트' 뒤 키워드도 '시작점 배치'로 인정
    assert req_check.title_starts_with_keyword("삼성화재 다이렉트 해외여행보험으로 안전하게", "해외여행보험")
    assert req_check.title_starts_with_keyword("해외여행보험 가입 방법", "해외여행보험")
    assert req_check.title_starts_with_keyword("삼성화재 해외여행보험 추천", "해외여행보험")
    # 브랜드 접두어 없이 뒤에 묻히면 시작점 아님
    assert not req_check.title_starts_with_keyword("안전한 여행을 위한 해외여행보험", "해외여행보험")
    # evaluate 상태: 접두어 뒤 키워드 → ok
    by = {i["name"]: i for i in req_check.evaluate("삼성화재 다이렉트 해외여행보험으로 안전하게", "본문")}
    assert by["제목 키워드 시작"]["status"] == "ok"


def test_link_placeholder_counts_as_ok():
    # '링크 삽입' 자리표시 문구가 있으면 링크 없어도 충족(ok)
    ok = {i["name"]: i for i in req_check.evaluate("t", "가입은 아래 링크 삽입 예정입니다.")}
    assert ok["허용 상품 링크만 사용"]["status"] == "ok"
    assert ok["하단 가입 링크"]["status"] == "ok"                # 하단 가입 링크도 동일 적용
    # 자리표시도 실제 링크도 없으면 warn 유지
    warn = {i["name"]: i for i in req_check.evaluate("t", "가입하세요 좋은 상품입니다.")}
    assert warn["허용 상품 링크만 사용"]["status"] == "warn"
    assert warn["하단 가입 링크"]["status"] == "warn"


def test_official_blog_paid_ad_na():
    items = req_check.evaluate("해외여행보험", "본문", is_official=True)
    by = {i["name"]: i for i in items}
    assert by["유료광고 문안(상단)"]["status"] == "na"


def test_discount_order_rule():
    # 올바른 순서: 동반가입 > 재가입 > 중복적용 (띄어쓰기·중간 문구 있어도 인정)
    ok_body = "동반가입할인 10%, 재가입할인 5%, 중복적용 가능합니다."
    by_ok = {i["name"]: i for i in req_check.evaluate("t", ok_body)}
    assert by_ok["할인 중복적용 순서"]["status"] == "ok"
    # 실제 원고 문장 형태(띄어쓰기·줄바꿈 포함)도 충족
    real = "동반가입 할인은\n재가입 할인과 중복 적용된답니다."
    assert {i["name"]: i for i in req_check.evaluate("t", real)}["할인 중복적용 순서"]["status"] == "ok"
    # 순서가 이어지지 않으면 warn(확인 필요) — 하드 fail 아님(오검 방지)
    bad_body = "재가입할인 먼저, 동반가입할인 나중, 중복적용 가능"
    by_bad = {i["name"]: i for i in req_check.evaluate("t", bad_body)}
    assert by_bad["할인 중복적용 순서"]["status"] == "warn"
    # 중복적용 미언급 → na
    by_na = {i["name"]: i for i in req_check.evaluate("t", "혜택 설명 없음")}
    assert by_na["할인 중복적용 순서"]["status"] == "na"


def test_rider_name_consolidation():
    rv = {"ok": ["여행중 휴대품 손해(분실제외) 특약"], "mismatch": [], "unused": []}
    by = {i["name"]: i for i in req_check.evaluate("t", "여행중 휴대품 손해(분실제외) 특약 가입", rider_result=rv)}
    assert by["정확한 담보명 기재"]["status"] == "ok"
    rv2 = {"ok": [], "mismatch": ["항공기 지연 결항 보상(지수형)(국내 출국) 특약"], "unused": []}
    by2 = {i["name"]: i for i in req_check.evaluate("t", "항공기 지연 특약", rider_result=rv2)}
    assert by2["정확한 담보명 기재"]["status"] == "fail"
