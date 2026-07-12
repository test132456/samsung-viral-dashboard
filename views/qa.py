"""심의전 원고 검수 탭 — 워드 다중원고 분리 + 이름 필터 + 심의 문구 QA + 약관 대조 + 구조 체크리스트."""
import streamlit as st
import docx, io
from datetime import date
from core import qa_engine, schema, qa_checklist, manuscript_parser, terms, guide, req_check
from views import ui


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
    """업로드 파일 → (title_default, text_default, url). docx는 다중 원고 분리+블로거 선택."""
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
        return sec["title"], sec["body"], sec["url"]
    return "", manuscript_parser.all_text(data), ""


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
        use_ai = st.toggle("AI 2차검수", value=bool(claude), key="qa_use_ai")
        title = st.text_input("제목", value=title_default, placeholder="원고 제목 (체크리스트용)")
        terms_up = st.file_uploader("약관 파일 (선택 · 특약명 교차확인용)", type=["pdf", "docx", "txt"], key="qa_terms")
        guide_up = st.file_uploader("작성 가이드 (pptx)", type=["pptx"], key="qa_guide")
    with col_in:
        text = st.text_area("원고 텍스트", value=text_default, height=260)

    if st.button("검수 실행", type="primary", disabled=not text.strip(), key="qa_run"):
        _ov = st.empty()
        _ov.markdown(ui.loading_overlay("🍪 원고 굽는 중… 심의 문구·특약명 살펴보는 중"), unsafe_allow_html=True)
        try:
            refs = _refs_from_sheets(sheets)
            if is_official:  # 공식블로그는 유료광고 문구 불필요 → 필수문구에서 제외
                refs = {**refs, "required": [r for r in refs.get("required", [])
                                             if "유료광고" not in (str(r.get("type", "")) + str(r.get("phrase", "")))]}
            judge = (lambda t: claude.judge_expressions(t, "")) if (use_ai and claude) else None
            st.session_state["qa_report"] = qa_engine.run_qa(text, refs, ai_judge=judge)
            st.session_state["qa_checklist"] = qa_checklist.evaluate(title, text, refs, is_official=is_official)
        finally:
            _ov.empty()

    # 원고 작성 플로우 점검 — 검수 전에도 미리보기 표시 (가이드 플로우 순서)
    st.markdown("##### 📝 원고 작성 플로우 점검")
    cl = st.session_state.get("qa_checklist")
    st.markdown(ui.flow_checklist(cl or qa_checklist.blank()), unsafe_allow_html=True)
    if cl:
        cs = qa_checklist.summary(cl)
        st.caption(f"✓ 충족 {cs['ok']} · △ 부분 {cs['warn']} · ✕ 미충족 {cs['fail']} · 통과율 {cs['pass_rate']}%  "
                   f"· 가이드 '원고 작성 예시 플로우' 기준 (제목→유료광고→특약 보장문장→고지문구→해시태그)")
    else:
        st.caption("제목·원고 입력 후 '검수 실행'을 누르면 가이드 플로우 항목이 ✓ / △ / ✕ 로 채워집니다.")

    # ===== 통합 검수 결과 (검수 실행 후) =====
    report = st.session_state.get("qa_report")
    if not report:
        return

    # ── 결과 데이터 계산 (파일 파싱 등 무거운 작업은 캐시 + 중앙 오버레이로 감쌈) ──
    _ov2 = st.empty()
    _ov2.markdown(ui.loading_overlay("🍪 원고 살펴보는 중… 가이드·약관 대조"), unsafe_allow_html=True)
    try:
        g = _guide_parsed(guide_up.getvalue()) if guide_up is not None else None
        gc = guide.check(text, g) if g else None
        # 특약명 기준 = 가이드 '메인 담보명' (미인식 시 정식 기본값). 약관 PDF는 특약명 소스로 쓰지 않음
        guide_riders = g.get("riders", []) if g else []
        ref_riders = guide_riders or guide.DEFAULT_RIDERS
        rider_src = "가이드" if guide_riders else "가이드 기본"
        rv = terms.verify_usage(text, ref_riders)
        # (선택) 약관 PDF 업로드 시 정식 특약명이 약관에서도 확인되는지 교차확인
        terms_confirm = None
        if terms_up is not None:
            rawn = terms._norm(_terms_text(terms_up.getvalue(), terms_up.name))
            terms_confirm = sum(1 for r in ref_riders if terms._norm(r) in rawn)
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
         {"icon": "🚫", "tone": "gray", "label": "표현불가 문구", "value": "–", "sub": "가이드 미업로드"}),
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
         {"icon": "#️⃣", "tone": "gray", "label": "필수 해시태그", "value": "–", "sub": "가이드 미업로드"}),
        {"icon": "🔑", "tone": "green" if 3 <= kwc <= 5 else "amber", "label": "'해외여행보험' 키워드",
         "value": f'{kwc}개', "sub": "가이드 3~5개"},
        {"icon": "💰", "tone": "amber" if report["price_found"] else "green", "label": "보험료 기재",
         "value": "발견" if report["price_found"] else "없음", "sub": "금액 탐지"},
    ]
    st.markdown(ui.kpi_cards(cards, per_row=4), unsafe_allow_html=True)

    # --- 표현불가 문구 전체 대조 ---
    if g and g["banned"]:
        st.markdown("###### 🚫 표현불가 문구 점검 (사용 ✕ / 미사용 ✓)")
        st.markdown(ui.banned_detail(g["banned"], text, page_of=pg), unsafe_allow_html=True)
    if report["banned"]:
        st.error("기본 사전 금지표현: " + ", ".join(f"'{b['term']}'{pg(b['term'])}" for b in report["banned"]))

    # --- 특약명 상세 (가이드 정식 담보명 기준) ---
    st.markdown(f"###### 📑 특약명 대조 ({rider_src} 담보명 기준 · 정확 ✓ / 오기 의심 ✕)")
    st.markdown(ui.rider_detail(rv, len(ref_riders), page_of=pg), unsafe_allow_html=True)
    if terms_confirm is not None:
        st.caption(f"📎 약관 교차확인: 정식 특약명 {len(ref_riders)}개 중 {terms_confirm}개가 업로드한 약관에서도 확인됨")
    with st.expander(f"{rider_src} 정식 특약명 {len(ref_riders)}개 보기"):
        st.write("\n".join(f"- {r}" for r in ref_riders))

    # --- 가이드 요청·참고 사항 점검 (항목별 ✓/✕ + 원고 근거) ---
    rq = req_check.summary(req_items)
    st.markdown("##### 📋 가이드 요청사항 점검 (원고 근거 표시)")
    _page_note = " · 잘못된 부분은 원고 쪽수(추정) 표시" if pages else ""
    st.caption(f"✓ 충족 {rq['ok']} · △ 확인 {rq['warn']} · ✕ 미충족 {rq['fail']} · 통과율 {rq['pass_rate']}%  "
               f"— 각 항목이 원고에 어떻게 반영됐는지 근거 문장을 함께 보여줍니다{_page_note}.")
    for grp in ["요청·참고 사항", "담보·혜택", "필수 고지문구"]:
        gi = [it for it in req_items if it["group"] == grp]
        if gi:
            st.markdown(f"**{grp}**")
            st.markdown(ui.evidence_checklist(gi), unsafe_allow_html=True)

    # --- 키워드 / AI ---
    if report["missing_keywords"]:
        st.info("필수 키워드 누락: " + ", ".join(report["missing_keywords"]))
    for f in report["ai_findings"]:
        st.warning(f"AI: {f.get('snippet','')} — {f.get('reason','')} → {f.get('suggestion','')}")
