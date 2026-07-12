"""가이드 '요청 및 참고 사항' + '필수 고지문구 삽입' 점검 — 항목별 충족 여부 + 원고 근거(evidence).

각 항목: {group, name, status: 'ok'|'warn'|'fail'|'na', detail, evidence}
 evidence = 원고에서 해당 요건이 어떻게 들어갔는지 보여주는 발췌(HTML, 매칭어 <b>).
사용자가 직접 눈으로 확인할 수 있도록 근거 문장을 함께 돌려준다.
"""
from __future__ import annotations
import re

_URL_RE = re.compile(r"https?://[^\s)\]]+")
_TAG_RE = re.compile(r"#[가-힣A-Za-z0-9_]+")

BRAND = "삼성화재 다이렉트"
PRODUCT = "해외여행보험"
RELATED = ["여행자보험", "해외여행 여행자보험", "해외여행자보험"]
REQUIRED_TAGS = ["#삼성화재다이렉트", "#삼성화재다이렉트해외여행보험", "#해외여행보험",
                 "#항공지연", "#지연결항", "#해외여행자보험", "#해외여행보험추천", "#해외여행보험후기"]
# 타 보험사(삼성화재 제외) — 언급 지양 대상
COMPETITORS = ["현대해상", "DB손해보험", "DB손보", "KB손해보험", "KB손보", "메리츠화재",
               "한화손해보험", "롯데손해보험", "흥국화재", "MG손해보험", "하나손해보험",
               "캐롯손해보험", "NH농협손해보험", "농협손해보험", "신한EZ손해보험",
               "처브손해보험", "AXA손해보험", "라이나생명", "동부화재"]
PAID_MARKERS = ["소정의 광고비", "광고비(원고료)", "원고료", "유료광고", "광고비"]
ALLOWED_HOST = "samsungfire.com"
_HEAD, _TAIL = 0.25, 0.30


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _snip(body: str, needle: str, w: int = 35) -> str:
    """needle 주변 발췌(±w자) — 매칭어를 <b>로 강조. 없으면 ''."""
    i = body.find(needle)
    if i < 0:
        return ""
    s, e = max(0, i - w), min(len(body), i + len(needle) + w)
    frag = _esc(body[s:e].replace("\n", " ").strip())
    frag = frag.replace(_esc(needle), f"<b>{_esc(needle)}</b>")
    return ("…" if s > 0 else "") + frag + ("…" if e < len(body) else "")


# [기타 혜택] 소구 항목 (슬라이드3)
BENEFITS = {
    "동반가입 할인": ["동반가입"],
    "재가입 할인": ["재가입"],
    "우리말 도움 서비스": ["우리말 도움", "우리말도움"],
    "모바일 가입": ["모바일 가입", "모바일가입"],
    "인천공항 가입데스크": ["인천공항 가입", "가입데스크"],
}


def evaluate(title: str, body: str, is_official: bool = False,
             rider_result: dict | None = None) -> list[dict]:
    title = (title or "").strip()
    body = body or ""
    head = body[:max(80, int(len(body) * _HEAD))]
    tail = body[-max(100, int(len(body) * _TAIL)):] if body else ""
    links = _URL_RE.findall(body)
    body_no_tags = _TAG_RE.sub("", body)  # 본문 키워드 카운트(해시태그 제외)
    items = []

    def add(group, name, status, detail, evidence=""):
        items.append({"group": group, "name": name, "status": status,
                      "detail": detail, "evidence": evidence})

    G1 = "요청·참고 사항"
    # 1) 브랜드·보험명 정확 표기
    has_brand = "삼성화재" in body
    if has_brand and PRODUCT in body:
        ev = _snip(body, BRAND) or _snip(body, "삼성화재") or _snip(body, PRODUCT)
        add(G1, "브랜드·보험명 정확 표기", "ok", "삼성화재 다이렉트 · 해외여행보험", ev)
    elif PRODUCT in body:
        add(G1, "브랜드·보험명 정확 표기", "warn", "'삼성화재 다이렉트' 표기 확인 필요", _snip(body, PRODUCT))
    else:
        add(G1, "브랜드·보험명 정확 표기", "fail", "브랜드/보험명 미표기")

    # 2) 타 보험사·타 보험명 언급 지양
    hits = [c for c in COMPETITORS if c in body]
    if hits:
        add(G1, "타 보험사 언급 지양", "fail", f"타사 {len(hits)}건: " + ", ".join(hits), _snip(body, hits[0]))
    else:
        add(G1, "타 보험사 언급 지양", "ok", "타 보험사 언급 없음")

    # 3) 필수 해시태그 (하단)
    inc = [t for t in REQUIRED_TAGS if t in body]
    miss = [t for t in REQUIRED_TAGS if t not in body]
    ev_tags = _esc(" ".join(_TAG_RE.findall(tail)[:12]))
    if not miss:
        add(G1, "필수 해시태그 포함", "ok", f"{len(inc)}/{len(REQUIRED_TAGS)}", ev_tags)
    elif inc:
        add(G1, "필수 해시태그 포함", "warn", f"{len(inc)}/{len(REQUIRED_TAGS)} · 누락: " + " ".join(miss), ev_tags)
    else:
        add(G1, "필수 해시태그 포함", "fail", "필수 해시태그 없음")

    # 4-① '해외여행보험' 키워드 3~5개 (본문 기준, 해시태그 제외)
    kc = body_no_tags.count(PRODUCT)
    st = "ok" if 3 <= kc <= 5 else ("warn" if kc else "fail")
    add(G1, "'해외여행보험' 키워드 3~5개", st, f"본문 {kc}개 (필수 3~5개)")

    # 4-② 연관 키워드
    found = [r for r in RELATED if r in body]
    if found:
        add(G1, "연관 키워드 삽입", "ok", ", ".join(found), _snip(body, found[0]))
    else:
        add(G1, "연관 키워드 삽입", "warn", "여행자보험 등 연관 키워드 없음")

    # 4-④ 제목: 키워드 시작 + 25자 이내
    if title.startswith(PRODUCT) and len(title) <= 25:
        add(G1, "제목 키워드 시작·25자", "ok", f"{len(title)}자", _esc(title))
    elif PRODUCT in title:
        add(G1, "제목 키워드 시작·25자", "warn", f"{len(title)}자 · 키워드 위치/길이 확인", _esc(title))
    else:
        add(G1, "제목 키워드 시작·25자", "fail", "제목에 '해외여행보험' 없음", _esc(title))

    # 5) 허용 상품 링크만 (삼성화재 다이렉트 외 상품 링크 불가)
    foreign = [l for l in links if ALLOWED_HOST not in l]
    if foreign:
        add(G1, "허용 상품 링크만 사용", "fail", "삼성화재 외 링크 발견", _esc(foreign[0]))
    elif links:
        add(G1, "허용 상품 링크만 사용", "ok", "삼성화재 링크만 사용", _esc(links[0]))
    else:
        add(G1, "허용 상품 링크만 사용", "warn", "링크 없음 (심의 후 삽입 예정 가능)")

    G2 = "필수 고지문구"
    # 6) 유료광고 문안 (본문 첫 부분)
    marker = next((m for m in PAID_MARKERS if m in body), None)
    if is_official:
        add(G2, "유료광고 문안(상단)", "na", "공식블로그 · 해당없음")
    elif marker and any(m in head for m in PAID_MARKERS):
        add(G2, "유료광고 문안(상단)", "ok", "본문 첫 부분에 표기", _snip(body, marker))
    elif marker:
        add(G2, "유료광고 문안(상단)", "warn", "표기 있으나 상단 아님", _snip(body, marker))
    else:
        add(G2, "유료광고 문안(상단)", "fail", "유료광고 문안 없음")

    # 7) 하단 가입 링크 (direct.samsungfire.com/mall) — 심의 후 삽입 예정일 수 있음
    mall = [l for l in links if ALLOWED_HOST in l]
    if any(l in tail for l in mall):
        add(G2, "하단 가입 링크", "ok", "본문 하단에 가입 링크", _esc(mall[0]))
    elif mall:
        add(G2, "하단 가입 링크", "warn", "링크 있으나 하단 아님", _esc(mall[0]))
    else:
        add(G2, "하단 가입 링크", "warn", "가입 링크 없음 (심의 완료 후 삽입 예정)")

    # 8) 준법감시인확인필 (본문 하단) — 심의 후 번호 확정
    if "준법감시인확인필" in tail:
        add(G2, "준법감시인확인필(하단)", "ok", "본문 하단에 표기", _snip(body, "준법감시인확인필"))
    elif "준법감시인확인필" in body:
        add(G2, "준법감시인확인필(하단)", "warn", "표기 있으나 하단 아님", _snip(body, "준법감시인확인필"))
    else:
        add(G2, "준법감시인확인필(하단)", "warn", "없음 (심의 완료 후 번호 기입 예정)")

    G3 = "담보·혜택 (슬라이드3)"
    # 9) 정확한 담보명 기재 (약관/가이드 정식 특약명 그대로) — 특약명 대조 결과 연동
    if not rider_result:
        add(G3, "정확한 담보명 기재", "na", "특약명 기준 미설정 (가이드/약관 업로드 시 대조)")
    elif rider_result.get("mismatch"):
        mm = rider_result["mismatch"]
        add(G3, "정확한 담보명 기재", "fail", f"{len(mm)}건 오기 의심: " + ", ".join(mm[:2]),
            _snip(body, terms_head(mm[0])))
    elif rider_result.get("ok"):
        add(G3, "정확한 담보명 기재", "ok", f"{len(rider_result['ok'])}개 정식명 그대로 표기",
            _snip(body, rider_result["ok"][0]))
    else:
        add(G3, "정확한 담보명 기재", "warn", "원고에서 특약 언급 없음")

    # 10) ★ 할인 중복적용 순서 — '동반가입할인 > 재가입할인 > 중복적용 가능' 순
    i_d, i_j = body.find("동반가입"), body.find("재가입")
    i_o = body.find("중복적용")
    if i_o < 0:
        i_o = body.find("중복 적용")
    if i_o < 0:
        add(G3, "할인 중복적용 순서", "na", "중복적용 언급 없음 · 해당없음")
    elif i_d >= 0 and i_j >= 0 and i_d < i_j < i_o:
        add(G3, "할인 중복적용 순서", "ok", "동반가입 > 재가입 > 중복적용 순", _snip(body, "중복"))
    elif i_d >= 0 and i_j >= 0:
        add(G3, "할인 중복적용 순서", "fail",
            "순서 오류 — '동반가입할인 > 재가입할인 > 중복적용 가능' 순으로 기입", _snip(body, "중복"))
    else:
        add(G3, "할인 중복적용 순서", "warn", "동반가입·재가입 할인 언급 확인 필요", _snip(body, "중복"))

    # 11) 기타 혜택 소구 (참고) — 사용된 혜택 안내 (필수 아님)
    used = [name for name, kws in BENEFITS.items() if any(k in body for k in kws)]
    if used:
        add(G3, "기타 혜택 소구 (참고)", "ok", "언급: " + ", ".join(used))
    else:
        add(G3, "기타 혜택 소구 (참고)", "na", "해당없음 (선택 소구)")

    return items


def terms_head(name: str) -> str:
    """특약명에서 원고 대조용 머리말(괄호 앞부분) — evidence 검색에 사용."""
    return re.split(r"[(（]", name)[0].strip() or name


def summary(items: list[dict]) -> dict:
    ok = sum(1 for i in items if i["status"] == "ok")
    warn = sum(1 for i in items if i["status"] == "warn")
    fail = sum(1 for i in items if i["status"] == "fail")
    applicable = sum(1 for i in items if i["status"] != "na") or 1
    return {"ok": ok, "warn": warn, "fail": fail, "pass_rate": round(ok / applicable * 100)}
