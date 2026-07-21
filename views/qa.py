"""심의전 원고 검수 탭 — 워드 다중원고 분리 + 이름 필터 + 심의 문구 QA + 약관 대조 + 구조 체크리스트."""
import streamlit as st
import docx, io
from datetime import date
from core import (qa_engine, schema, qa_checklist, manuscript_parser, terms, guide,
                  req_check, typo, library, review_rules)
from views import ui


# 오타 사전(TYPOS)/검사 로직이 바뀌면 +1 → 배포 시 st.cache_data 캐시 자동 무효화
_TYPO_LOGIC_VER = 2


@st.cache_data(show_spinner=False)
def _spellcheck(text: str, logic_ver: int):
    """오탈자 = 사전(항상, 신뢰) + 네이버 맞춤법(가능하면). text 기준 캐시.
    logic_ver 는 캐시 키에 포함돼 사전/로직 변경 시 캐시를 무효화한다(_TYPO_LOGIC_VER).
    반환: (오탈자목록, naver_ok). 네이버가 막히면 naver_ok=False + 사전 결과만."""
    items = list(typo.check_typos(text))
    clean = typo._clean_for_spell(text)
    corrected = typo.spellcheck_naver(clean)  # 실패/차단 시 None
    naver_ok = corrected is not None
    if naver_ok:
        for it in typo.diff_corrections(clean, corrected):
            # 이미 사전/이전 항목이 같은 교정을 (조사만 다르게) 커버하면 건너뜀
            dup = any(e["as_is"] in it["as_is"] and e["to_be"] in it["to_be"] for e in items)
            if not dup and it["to_be"] not in it["as_is"]:
                items.append(it)
    return items[:60], naver_ok


def _refs_from_sheets(sheets) -> dict:
    banned = sheets.read(schema.SHEET_REF_BANNED)["term"].dropna().tolist()
    required = sheets.read(schema.SHEET_REF_REQUIRED).to_dict("records")
    riders_df = sheets.read(schema.SHEET_REF_RIDERS)
    riders = [{"official_name": r["official_name"],
               "common_mistakes": [m.strip() for m in str(r["common_mistakes"]).split(",") if m.strip()]}
              for r in riders_df.to_dict("records")]
    keywords = sheets.read(schema.SHEET_REF_KEYWORDS).to_dict("records")
    return {"banned": banned, "required": required, "riders": riders, "keywords": keywords}


def _read_docx(file) -> str:
    d = docx.Document(io.BytesIO(file.read()))
    return "\n".join(p.text for p in d.paragraphs)


def _load_upload(up):
    """업로드 파일 → (title_default, text_default, url). docx는 다중 원고 분리+블로거 선택.
    선택한 블로거명은 st.session_state['qa_blogger_name']에 저장(수정요청 양식용)."""
    st.session_state["qa_blogger_name"] = ""
    if up is None:
        return "", "", ""
    data = up.getvalue()
    if not up.name.lower().endswith(".docx"):
        return "", data.decode("utf-8", "ignore"), ""
    secs = manuscript_parser.parse_docx_sections(data)
    sec = None
    if len(secs) >= 2:
        names = [s["name"] or f"섹션 {i + 1}" for i, s in enumerate(secs)]
        st.info(f"이 워드에 원고 **{len(secs)}건**이 있습니다. 검수할 블로거를 선택하세요.")
        pick = st.selectbox("블로거 선택", names, key="qa_blogger")
        sec = secs[names.index(pick)]
    elif len(secs) == 1:
        sec = secs[0]
    if sec is not None:
        st.caption(f"✅ **{sec['name'] or '원고'}** 자동 추출" + (f" · 표기 URL: {sec['url']}" if sec['url'] else ""))
        if sec.get("deleted"):
            st.markdown(ui.deleted_html(sec["deleted"]), unsafe_allow_html=True)
        st.session_state["qa_blogger_name"] = sec.get("name", "")
        return sec["title"], sec["body"], sec["url"]
    return "", manuscript_parser.all_text(data), ""


def _qa_revision(blogger, typos, gc, rv, report, gojib, paid, is_official):
    """심의전 검수 발견사항 → 실행사 수정 요청 문구(복붙용)."""
    blocks = [f"<수정 요청 (심의 전) · {blogger}>" if blogger else "<수정 요청 (심의 전)>", ""]
    n = [1]

    def sec(title, lines):
        lines = [x for x in lines if x]
        if lines:
            blocks.append(f"{n[0]}. {title}")
            blocks.extend(lines)
            blocks.append("")
            n[0] += 1

    sec("맞춤법·오탈자 (현재 → 수정)", [f"• {t['as_is']} → {t['to_be']}" for t in typos])
    banned = [f"• '{b}' 표현 삭제/순화" for b in (gc["banned_hits"] if gc else [])]
    banned += [f"• '{b['term']}' 표현 삭제/순화" for b in report.get("banned", [])]
    sec("표현불가 문구 (삭제/순화)", list(dict.fromkeys(banned)))
    sec("특약명 정정 (정식명으로 표기)", [f"• {m}" for m in rv.get("mismatch", [])])
    miss = []
    if not is_official and paid and not paid.get("present"):
        miss.append("• 유료광고 문안 추가 (본문 상단)")
    if gojib and not gojib.get("present"):
        miss.append("• 고지문구 추가 (본문 하단)")
    if gc and gc.get("tags_missing"):
        miss.append("• 누락 해시태그 추가: " + " ".join(gc["tags_missing"]))
    sec("필수 항목 누락 (추가 필요)", miss)
    if n[0] == 1:
        blocks.append("수정 사항 없음 — 원고가 기준에 부합합니다.")
    return "\n".join(blocks).strip()


@st.cache_data(show_spinner=False)
def _terms_text(data: bytes, name: str) -> str:
    """약관 파일(pdf/docx/txt) → 텍스트. bytes 기준 캐시."""
    n = (name or "").lower()
    if n.endswith(".pdf"):
        return manuscript_parser.read_pdf(data)
    if n.endswith(".docx"):
        return manuscript_parser.all_text(data)
    return data.decode("utf-8", "ignore")


@st.cache_data(show_spinner=False)
def _guide_parsed(data: bytes) -> dict:
    """가이드 PPT 파싱(무거움) → 캐시."""
    return guide.parse_guide(guide.extract_text(data))


@st.cache_data(show_spinner=False)
def _doc_pages(data: bytes):
    """워드 페이지 매핑(무거움) → 캐시."""
    return manuscript_parser.paragraph_pages(data)


def render_qa(sheets, claude=None):
    st.markdown(ui.page_header("📝 심의전 원고 검수",
                               "발행 전 초안 원고를 심의 넣기 전에 점검 — 금지·과장 문구, 약관 특약명 대조, 작성 플로우"),
                unsafe_allow_html=True)

    up = st.file_uploader("초안 원고 업로드 (.docx/.txt) — 여러 명 원고가 든 워드도 자동 분리",
                          type=["docx", "txt"], key="qa_uploader")
    title_default, text_default, _url = _load_upload(up)

    col_in, col_opt = st.columns([3, 1])
    with col_opt:
        post_type = st.radio("원고 유형", ["체험단(배포형)", "공식블로그"], key="qa_type")
        is_official = post_type == "공식블로그"
        title = st.text_input("제목", value=title_default, placeholder="원고 제목 (체크리스트용)")
        # 📚 자료실: 약관·가이드는 여기에 등록된 최신본을 자동 사용
        _tm, _gm = library.terms_meta(), library.guide_meta()
        st.markdown(
            "📚 **자료실** (최신본 자동 사용)  \n"
            + (f"• 작성가이드 ✅ {_gm['updated']}" if _gm else "• 작성가이드 ⬜ 미등록") + "  \n"
            + (f"• 약관 ✅ {_tm['updated']}" if _tm else "• 약관 ⬜ 미등록"))
        with st.expander("이번 검수만 다른 파일 쓰기 (선택)"):
            terms_up = st.file_uploader("약관 (pdf/docx/txt)", type=["pdf", "docx", "txt"], key="qa_terms")
            guide_up = st.file_uploader("작성 가이드 (pptx)", type=["pptx"], key="qa_guide")
    with col_in:
        text = st.text_area("원고 텍스트", value=text_default, height=260)

    if st.button("검수 실행", type="primary", disabled=not text.strip(), key="qa_run"):
        _ov = st.empty()
        _ov.markdown(ui.loading_overlay("원고 굽는 중… 심의 문구·특약명 살펴보는 중"), unsafe_allow_html=True)
        try:
            refs = _refs_from_sheets(sheets)
            if is_official:  # 공식블로그는 유료광고 문구 불필요 → 필수문구에서 제외
                refs = {**refs, "required": [r for r in refs.get("required", [])
                                             if "유료광고" not in (str(r.get("type", "")) + str(r.get("phrase", "")))]}
            _typos, _naver_ok = _spellcheck(text, _TYPO_LOGIC_VER)  # 사전 + 네이버 맞춤법
            st.session_state["qa_typos"] = _typos
            st.session_state["qa_naver_ok"] = _naver_ok
            st.session_state["qa_report"] = qa_engine.run_qa(text, refs, ai_judge=None)
            st.session_state["qa_checklist"] = qa_checklist.evaluate(
                title, text, refs, is_official=is_official)
        finally:
            _ov.empty()

    # 원고 작성 플로우 점검 — 검수 전에도 미리보기 표시 (가이드 플로우 순서)
    st.markdown("##### 📝 원고 작성 플로우 점검")
    cl = st.session_state.get("qa_checklist")
    st.markdown(ui.flow_checklist(cl or qa_checklist.blank()), unsafe_allow_html=True)
    if cl:
        cs = qa_checklist.summary(cl)
        st.caption(f"✓ 충족 {cs['ok']} · △ 부분 {cs['warn']} · ✕ 미충족 {cs['fail']} · 통과율 {cs['pass_rate']}%  "
                   f"· 가이드 '원고 작성 예시 플로우' 기준 (제목→유료광고→특약 보장문장→가입 링크→고지문구→해시태그) · 오탈자는 아래 별도 섹션")
    else:
        st.caption("제목·원고 입력 후 '검수 실행'을 누르면 가이드 플로우 항목이 ✓ / △ / ✕ 로 채워집니다.")

    # ===== 통합 검수 결과 (검수 실행 후) =====
    report = st.session_state.get("qa_report")
    if not report:
        return

    # ── 결과 데이터 계산 (파일 파싱 등 무거운 작업은 캐시 + 중앙 오버레이로 감쌈) ──
    _ov2 = st.empty()
    _ov2.markdown(ui.loading_overlay("원고 살펴보는 중… 가이드·약관 대조"), unsafe_allow_html=True)
    try:
        # 약관·가이드: 업로드가 있으면 그걸, 없으면 자료실 최신본 사용
        guide_data = guide_up.getvalue() if guide_up is not None else library.guide_bytes()
        terms_data = terms_up.getvalue() if terms_up is not None else library.terms_bytes()
        terms_name = terms_up.name if terms_up is not None else (library.terms_meta() or {}).get("name", "약관.pdf")
        g = _guide_parsed(guide_data) if guide_data else None
        gc = guide.check(text, g) if g else None
        # 특약명 기준 = 가이드 '메인 담보명' (미인식 시 정식 기본값). 약관은 특약명 소스로 쓰지 않음
        guide_riders = g.get("riders", []) if g else []
        ref_riders = guide_riders or guide.DEFAULT_RIDERS
        rider_src = "가이드" if guide_riders else "가이드 기본"
        rv = terms.verify_usage(text, ref_riders)
        # (선택) 약관이 있으면 정식 특약명이 약관에서도 확인되는지 교차확인(핵심어 기준)
        terms_confirm = None
        if terms_data:
            terms_confirm = terms.confirmed_count(ref_riders, _terms_text(terms_data, terms_name))
        typos = st.session_state.get("qa_typos") or typo.check_typos(text)
        rs = report.get("required_status", [])
        # 원고 쪽수(추정) — 잘못된 부분 위치 표시용 (워드 업로드 시)
        pages = (_doc_pages(up.getvalue())
                 if (up is not None and up.name.lower().endswith(".docx")) else None)

        def pg(s):
            p = manuscript_parser.find_page(pages, s) if pages else None
            return f" · 원고 {p}쪽" if p else ""

        req_items = req_check.evaluate(title, text, is_official=is_official, rider_result=rv, page_of=pg)
    finally:
        _ov2.empty()

    def _req(*keys):
        for it in rs:
            blob = str(it.get("type", "")) + str(it.get("phrase", ""))
            if any(k in blob for k in keys):
                return it
        return None
    gojib, paid = _req("고지"), _req("유료광고", "원고료", "광고비")
    kwc = gc["keyword_count"] if gc else text.count("해외여행보험")

    st.markdown("##### ✅ 검수 결과 요약")
    cards = [
        # --- 1줄: 규제·약관 ---
        ({"icon": "🚫", "tone": "red" if gc["banned_hits"] else "green", "label": "표현불가 문구",
          "value": f'{len(gc["banned_hits"])}건', "sub": "가이드 기준 사용"} if gc else
         {"icon": "🚫", "tone": "gray", "label": "표현불가 문구", "value": "–", "sub": "자료실 없음"}),
        {"icon": "🔤", "tone": "red" if typos else "green", "label": "오탈자",
         "value": f'{len(typos)}건', "sub": "오타 사전"},
        {"icon": "⛔", "tone": "red" if report["banned_count"] else "green", "label": "금지표현(사전)",
         "value": f'{report["banned_count"]}건', "sub": "기본 사전"},
        {"icon": "📑", "tone": "red" if rv["mismatch_count"] else "green", "label": "특약명",
         "value": (f'{rv["mismatch_count"]}건 오기' if rv["mismatch_count"] else "정상"), "sub": f"{rider_src} 담보명"},
        ({"icon": "📢", "tone": "green" if gojib["present"] else "red", "label": "고지문구",
          "value": "포함" if gojib["present"] else "누락", "sub": "법정 고지"} if gojib else
         {"icon": "📢", "tone": "gray", "label": "고지문구", "value": "–", "sub": "기준 없음"}),
        # --- 2줄: 표기·형식 ---
        ({"icon": "💸", "tone": "gray", "label": "유료광고 표기", "value": "해당없음", "sub": "공식블로그"} if is_official else
         ({"icon": "💸", "tone": "green" if paid["present"] else "red", "label": "유료광고 표기",
           "value": "포함" if paid["present"] else "누락", "sub": "체험단 필수"} if paid else
          {"icon": "💸", "tone": "gray", "label": "유료광고 표기", "value": "–", "sub": "기준 없음"})),
        ({"icon": "#️⃣", "tone": "green" if not gc["tags_missing"] else "amber", "label": "필수 해시태그",
          "value": f'{len(gc["tags_included"])}/{gc["tags_total"]}', "sub": "포함"} if gc else
         {"icon": "#️⃣", "tone": "gray", "label": "필수 해시태그", "value": "–", "sub": "자료실 없음"}),
        {"icon": "🔑", "tone": "green" if kwc >= 3 else "amber", "label": "'해외여행보험' 키워드",
         "value": f'{kwc}개', "sub": "가이드 3개 이상"},
        {"icon": "💰", "tone": "amber" if report["price_found"] else "green", "label": "보험료 기재",
         "value": "발견" if report["price_found"] else "없음", "sub": "금액 탐지"},
    ]
    st.markdown(ui.kpi_cards(cards, per_row=4), unsafe_allow_html=True)

    # --- 오탈자 검수 (as-is → to-be) ---
    _naver_ok = st.session_state.get("qa_naver_ok")
    if typos:
        st.markdown(ui.subhead("🔤", "맞춤법 검사 (오탈자)", "red", stat=f"{len(typos)}건 · 확인 필요"),
                    unsafe_allow_html=True)
        st.markdown(ui.typo_detail(typos, page_of=pg), unsafe_allow_html=True)
        if _naver_ok:
            st.caption("오타 사전 + 네이버 맞춤법 검사기 기준 · 문맥상 맞는 표현이면 무시하세요")
        else:
            st.caption("⚠️ **오타 사전 기준만** 표시 · 네이버 맞춤법 검사기가 이 서버에서 차단돼 미동작 "
                       "→ 사전에 없는 오타는 못 잡을 수 있어요")
    elif _naver_ok is False:
        st.info("🔤 사전 기준 오탈자는 없습니다. 단, **네이버 맞춤법 검사기가 이 서버(클라우드)에서 차단돼** "
                "임의 오타는 확인하지 못했어요. 정확한 맞춤법 확인이 필요하면 로컬 실행 또는 별도 검사기를 권장합니다.")

    # --- 표현불가 문구 전체 대조 ---
    if g and g["banned"]:
        _used = sum(1 for b in g["banned"] if b in text)
        st.markdown(ui.subhead("🚫", "표현불가 문구 점검", "red" if _used else "green",
                               stat=f"{len(g['banned'])}개 중 {_used}개 사용"), unsafe_allow_html=True)
        st.markdown(ui.banned_detail(g["banned"], text, page_of=pg), unsafe_allow_html=True)
    if report["banned"]:
        st.error("기본 사전 금지표현: " + ", ".join(f"'{b['term']}'{pg(b['term'])}" for b in report["banned"]))

    # --- 심의 표현 점검 (단정·최상급·모호표현·특약병기·제한안내·이중공백) ---
    _rev = review_rules.check_all(text, ref_riders)
    _rev_items = sum(1 for r in _rev if r["hits"])          # 지적된 '항목 수'(건수 아님 — '등' 과다 표시 방지)
    st.markdown(ui.subhead("🔎", "심의 표현 점검", "amber" if _rev_items else "green",
                           stat=(f"{_rev_items}개 항목 확인" if _rev_items else "지적 없음")), unsafe_allow_html=True)
    if _rev_items:
        st.markdown(ui.review_detail(_rev, page_of=pg), unsafe_allow_html=True)
    st.caption("**정확**=규칙 기반 자동 검출(이중공백·최상급) · **후보**=문맥 판단 필요, 사람이 최종 확인. "
               "‘등’·‘가장/제일’은 지양 대상이라 자주 잡히지만 문맥상 정상이면 무시하세요. "
               "**특약·담보는 반드시 정식 담보명(괄호 수식어+‘특약’)으로** — 아래 ‘특약명 대조’의 정식명 목록 참고.")

    # --- 특약명 상세 (가이드 정식 담보명 기준) ---
    st.markdown(ui.subhead("📑", "특약명 대조", "red" if rv["mismatch_count"] else "green",
                           stat=f"{rider_src} · {rv['ok_count']}/{len(ref_riders)} 정확"), unsafe_allow_html=True)
    st.markdown(ui.rider_detail(rv, len(ref_riders), page_of=pg), unsafe_allow_html=True)
    if terms_confirm is not None:
        st.caption(f"📎 약관 교차확인: 정식 특약명 {len(ref_riders)}개 중 {terms_confirm}개가 업로드한 약관에서도 확인됨")
    with st.expander(f"{rider_src} 정식 특약명 {len(ref_riders)}개 보기"):
        st.write("\n".join(f"- {r}" for r in ref_riders))

    # --- 가이드 요청·참고 사항 점검 (항목별 ✓/✕ + 원고 근거) ---
    rq = req_check.summary(req_items)
    _rq_tone = "green" if rq["fail"] == 0 else "red"
    st.markdown(ui.subhead("📋", "가이드 요청사항 점검", _rq_tone,
                           stat=f"통과율 {rq['pass_rate']}% · ✕{rq['fail']}"), unsafe_allow_html=True)
    _page_note = " · 잘못된 부분은 원고 쪽수(추정) 표시" if pages else ""
    st.caption(f"각 항목이 원고에 어떻게 반영됐는지 근거 문장을 함께 보여줍니다{_page_note}.")
    for grp in ["요청·참고 사항", "담보·혜택", "필수 고지문구"]:
        gi = [it for it in req_items if it["group"] == grp]
        if gi:
            st.markdown(ui.group_label(grp), unsafe_allow_html=True)
            st.markdown(ui.evidence_checklist(gi), unsafe_allow_html=True)

    # --- 키워드 ---
    if report["missing_keywords"]:
        st.info("필수 키워드 누락: " + ", ".join(report["missing_keywords"]))

    # ✉️ 수정 요청 양식 (심의 전) — 접이식, 발견사항을 실행사에 전달용
    st.divider()
    _bn = st.session_state.get("qa_blogger_name", "")
    with st.expander(f"✉️ 수정 요청 양식 (심의 전){f' · {_bn}' if _bn else ''}  (클릭해서 펼치기)", expanded=False):
        st.caption("검수에서 발견된 사항을 실행사에 보낼 수정 요청입니다. 복사 버튼으로 복사해 전달하세요.")
        st.code(_qa_revision(_bn, typos, gc, rv, report, gojib, paid, is_official), language=None)
