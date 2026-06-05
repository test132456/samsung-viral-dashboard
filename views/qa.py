"""QA검수 탭 (1순위)."""
import streamlit as st
import docx, io
from datetime import date
from core import qa_engine, schema


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


def render_qa(sheets, claude=None):
    st.subheader("🔍 원고 QA 자동검수")
    col_in, col_opt = st.columns([3, 1])
    with col_opt:
        use_ai = st.toggle("AI 2차검수", value=bool(claude))
        content_id = st.text_input("content_id (선택)")
    with col_in:
        up = st.file_uploader("원고 업로드 (.docx/.txt)", type=["docx", "txt"])
        text = ""
        if up:
            text = _read_docx(up) if up.name.endswith(".docx") else up.read().decode("utf-8", "ignore")
        text = st.text_area("원고 텍스트", value=text, height=260)

    if st.button("검수 실행", type="primary", disabled=not text.strip()):
        guide = ""  # 심의가이드 텍스트는 ref 시트 note 합본 또는 secrets로 주입 가능
        judge = (lambda t: claude.judge_expressions(t, guide)) if (use_ai and claude) else None
        report = qa_engine.run_qa(text, _refs_from_sheets(sheets), ai_judge=judge)
        st.session_state["qa_report"] = report
        st.session_state["qa_text"] = text

    report = st.session_state.get("qa_report")
    if report:
        c = st.columns(5)
        c[0].metric("QA 점수", report["qa_score"])
        c[1].metric("금지표현", report["banned_count"])
        c[2].metric("특약명 오류", report["rider_error_count"])
        c[3].metric("필수문구 누락", "있음" if report["missing_phrase"] else "없음")
        c[4].metric("보험료 기재", "발견" if report["price_found"] else "없음")

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

        if st.button("결과 시트에 저장"):
            sheets.append(schema.SHEET_QA, {
                "content_id": content_id, "qa_score": report["qa_score"],
                "banned_count": report["banned_count"], "rider_error_count": report["rider_error_count"],
                "missing_phrase": "Y" if report["missing_phrase"] else "N",
                "price_found": "Y" if report["price_found"] else "N",
                "checked_at": date.today().isoformat()})
            st.success("저장 완료")
