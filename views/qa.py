"""심의전 원고 검수 탭 — 워드 다중원고 분리 + 이름 필터 + 심의 문구 QA + 약관 대조 + 구조 체크리스트."""
import streamlit as st
import docx, io
from datetime import date
from core import qa_engine, schema, qa_checklist, manuscript_parser, terms, guide
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
    if len(secs) >= 2:
        names = [s["name"] or f"섹션 {i + 1}" for i, s in enumerate(secs)]
        st.info(f"이 워드에 원고 **{len(secs)}건**이 있습니다. 검수할 블로거를 선택하세요.")
        pick = st.selectbox("블로거 선택", names, key="qa_blogger")
        sec = secs[names.index(pick)]
        st.caption(f"✅ **{sec['name']}** 원고 자동 추출" + (f" · 표기 URL: {sec['url']}" if sec['url'] else ""))
        return sec["title"], sec["body"], sec["url"]
    if len(secs) == 1:
        return secs[0]["title"], secs[0]["body"], secs[0]["url"]
    return "", manuscript_parser.all_text(data), ""


def render_qa(sheets, claude=None):
    st.subheader("📝 심의전 원고 검수")
    st.caption("발행 전 초안 원고를 심의 넣기 전에 점검 — 금지·과장 문구, 약관 특약명 대조, 구조 체크리스트")

    up = st.file_uploader("초안 원고 업로드 (.docx/.txt) — 여러 명 원고가 든 워드도 자동 분리",
                          type=["docx", "txt"], key="qa_uploader")
    title_default, text_default, _url = _load_upload(up)

    col_in, col_opt = st.columns([3, 1])
    with col_opt:
        post_type = st.radio("원고 유형", ["체험단(배포형)", "공식블로그"], key="qa_type")
        is_official = post_type == "공식블로그"
        use_ai = st.toggle("AI 2차검수", value=bool(claude), key="qa_use_ai")
        title = st.text_input("제목", value=title_default, placeholder="원고 제목 (체크리스트용)")
        terms_up = st.file_uploader("약관 파일 (pdf/docx/txt)", type=["pdf", "docx", "txt"], key="qa_terms")
        guide_up = st.file_uploader("작성 가이드 (pptx)", type=["pptx"], key="qa_guide")
    with col_in:
        text = st.text_area("원고 텍스트", value=text_default, height=260)

    if st.button("검수 실행", type="primary", disabled=not text.strip(), key="qa_run"):
        refs = _refs_from_sheets(sheets)
        if is_official:  # 공식블로그는 유료광고 문구 불필요 → 필수문구에서 제외
            refs = {**refs, "required": [r for r in refs.get("required", [])
                                         if "유료광고" not in str(r.get("phrase", ""))]}
        judge = (lambda t: claude.judge_expressions(t, "")) if (use_ai and claude) else None
        st.session_state["qa_report"] = qa_engine.run_qa(text, refs, ai_judge=judge)
        st.session_state["qa_checklist"] = qa_checklist.evaluate(title, text, refs, is_official=is_official)

    # 구조 체크리스트 — 검수 전에도 미리보기 표시
    st.markdown("##### 📋 구조 체크리스트")
    cl = st.session_state.get("qa_checklist")
    st.markdown(ui.checklist_table(cl or qa_checklist.blank()), unsafe_allow_html=True)
    if cl:
        cs = qa_checklist.summary(cl)
        st.caption(f"✓ 충족 {cs['ok']} · △ 부분 {cs['warn']} · ✕ 미충족 {cs['fail']} · 통과율 {cs['pass_rate']}%  "
                   f"· ④ 필수 고지문구는 ref_required(필수문구) 시트 기준입니다.")
    else:
        st.caption("제목·원고 입력 후 '검수 실행'을 누르면 위 5개 항목이 ✓ / △ / ✕ 로 채워집니다.")

    # 📜 약관 대조 (약관 파일 업로드 시)
    if terms_up is not None:
        tdata = terms_up.getvalue()
        _name = terms_up.name.lower()
        if _name.endswith(".pdf"):
            tt = manuscript_parser.read_pdf(tdata)
        elif _name.endswith(".docx"):
            tt = manuscript_parser.all_text(tdata)
        else:
            tt = tdata.decode("utf-8", "ignore")
        official = terms.extract_riders(tt)
        st.markdown("##### 📜 약관 대조")
        if _name.endswith(".pdf") and len(tt.strip()) < 50:
            st.warning("PDF에서 텍스트가 거의 추출되지 않았습니다 — 스캔(이미지) PDF일 수 있어요. "
                       "텍스트 PDF나 docx로 올리면 특약명이 인식됩니다.")
        if text.strip() and official:
            cov = terms.coverage(text, official)
            st.markdown(ui.kpi_cards([
                {"icon": "📗", "tone": "blue", "label": "약관 특약명", "value": f'{cov["total"]}개', "sub": "업로드 약관"},
                {"icon": "✅", "tone": "green" if cov["included_count"] else "gray",
                 "label": "원고 정확 표기", "value": f'{cov["included_count"]}개', "sub": "약관과 일치"},
            ]), unsafe_allow_html=True)
            if cov["included"]:
                st.success("원고에 약관 정식명 그대로 표기된 특약:\n" + "\n".join(f"- {o}" for o in cov["included"]))
            else:
                st.warning("원고에서 약관 정식 특약명과 정확히 일치하는 표기를 찾지 못했습니다 "
                           "— 특약명 오기 가능(위 QA '특약명 오류'도 함께 확인).")
        else:
            st.caption(f"약관에서 특약명 {len(official)}개 추출됨. 원고 텍스트를 입력하면 대조합니다.")
        with st.expander(f"약관에서 추출한 특약명 목록 ({len(official)}개)"):
            st.write("\n".join(f"- {o}" for o in official) if official else "추출된 특약명이 없습니다.")

    # 📗 작성 가이드 준수 체크 (가이드 PPT 업로드 시)
    if guide_up is not None:
        g = guide.parse_guide(guide.extract_text(guide_up.getvalue()))
        st.markdown("##### 📗 작성 가이드 준수 체크")
        if text.strip():
            gc = guide.check(text, g)
            st.markdown(ui.kpi_cards([
                {"icon": "🚫", "tone": "red" if gc["banned_hits"] else "green",
                 "label": "가이드 금지표현", "value": f'{len(gc["banned_hits"])}건', "sub": "발견"},
                {"icon": "#️⃣", "tone": "green" if not gc["tags_missing"] else "amber",
                 "label": "필수 해시태그", "value": f'{len(gc["tags_included"])}/{gc["tags_total"]}', "sub": "포함"},
                {"icon": "🔑", "tone": "green" if gc["keyword_ok"] else "amber",
                 "label": "'해외여행보험' 키워드", "value": f'{gc["keyword_count"]}개', "sub": "가이드 3~5개"},
            ]), unsafe_allow_html=True)
            if gc["banned_hits"]:
                st.error("가이드 금지표현: " + ", ".join(f"'{b}'" for b in gc["banned_hits"]))
            if gc["tags_missing"]:
                st.warning("누락된 필수 해시태그: " + " ".join(gc["tags_missing"]))
            if not gc["keyword_ok"]:
                st.info(f"'해외여행보험' 키워드 {gc['keyword_count']}개 — 가이드 권장 3~5개")
            if not gc["banned_hits"] and not gc["tags_missing"] and gc["keyword_ok"]:
                st.success("가이드 주요 항목(금지표현·해시태그·키워드) 준수 확인")
        else:
            st.caption(f"가이드에서 금지표현 {len(g['banned'])}개·해시태그 {len(g['hashtags'])}개 추출. 원고를 입력하면 대조합니다.")
        with st.expander("가이드에서 추출한 기준 보기"):
            st.write("**금지표현**: " + (", ".join(g["banned"]) or "-"))
            st.write("**필수 해시태그**: " + (" ".join(g["hashtags"]) or "-"))

    report = st.session_state.get("qa_report")
    if report:
        score = report["qa_score"]
        score_tone = "green" if score >= 85 else ("amber" if score >= 70 else "red")
        st.markdown(ui.kpi_cards([
            {"icon": "🎯", "tone": score_tone, "label": "QA 점수", "value": score, "sub": "100점 만점"},
            {"icon": "🚫", "tone": "red" if report["banned_count"] else "green",
             "label": "금지표현", "value": f'{report["banned_count"]}건', "sub": "사전 매칭"},
            {"icon": "📑", "tone": "red" if report["rider_error_count"] else "green",
             "label": "특약명 오류", "value": f'{report["rider_error_count"]}건', "sub": "약관 대조"},
            {"icon": "📋", "tone": "red" if report["missing_phrase"] else "green",
             "label": "필수문구 누락", "value": "있음" if report["missing_phrase"] else "없음", "sub": "고지·유료광고"},
            {"icon": "💰", "tone": "amber" if report["price_found"] else "green",
             "label": "보험료 기재", "value": "발견" if report["price_found"] else "없음", "sub": "금액 탐지"},
        ]), unsafe_allow_html=True)

        if report["banned"]:
            st.error("금지표현: " + ", ".join(f"'{b['term']}'" for b in report["banned"]))
        for r in report["riders"]:
            st.warning(f"특약명: ❌ '{r['found']}' → ✅ {r['official_name']}")
        if report["missing_required"]:
            st.warning("필수문구 누락: " + ", ".join(m["phrase"] for m in report["missing_required"]))
        if report["missing_keywords"]:
            st.info("필수 키워드 누락: " + ", ".join(report["missing_keywords"]))
        for f in report["ai_findings"]:
            st.warning(f"AI: {f.get('snippet','')} — {f.get('reason','')} → {f.get('suggestion','')}")
