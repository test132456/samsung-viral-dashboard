"""QA검수 탭 (1순위) — 워드 다중 원고 분리 + 이름 필터 + QA + 구조 체크리스트."""
import streamlit as st
import docx, io
from datetime import date
from core import qa_engine, schema, qa_checklist, manuscript_parser
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
    st.subheader("🔍 원고 QA 자동검수")

    up = st.file_uploader("원고 업로드 (.docx/.txt) — 여러 명 원고가 든 워드도 자동 분리",
                          type=["docx", "txt"], key="qa_uploader")
    title_default, text_default, _url = _load_upload(up)

    col_in, col_opt = st.columns([3, 1])
    with col_opt:
        use_ai = st.toggle("AI 2차검수", value=bool(claude), key="qa_use_ai")
        content_id = st.text_input("content_id (선택)", key="qa_cid")
        title = st.text_input("제목", value=title_default, placeholder="원고 제목 (체크리스트용)")
    with col_in:
        text = st.text_area("원고 텍스트", value=text_default, height=260)

    if st.button("검수 실행", type="primary", disabled=not text.strip(), key="qa_run"):
        refs = _refs_from_sheets(sheets)
        judge = (lambda t: claude.judge_expressions(t, "")) if (use_ai and claude) else None
        st.session_state["qa_report"] = qa_engine.run_qa(text, refs, ai_judge=judge)
        st.session_state["qa_checklist"] = qa_checklist.evaluate(title, text, refs)

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

        if st.button("결과 시트에 저장", key="qa_save"):
            sheets.append(schema.SHEET_QA, {
                "content_id": content_id, "qa_score": report["qa_score"],
                "banned_count": report["banned_count"], "rider_error_count": report["rider_error_count"],
                "missing_phrase": "Y" if report["missing_phrase"] else "N",
                "price_found": "Y" if report["price_found"] else "N",
                "checked_at": date.today().isoformat()})
            st.success("저장 완료")
