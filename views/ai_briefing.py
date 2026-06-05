"""AI브리핑 모니터링 탭 (4순위 · 클린 코퍼레이트 톤)."""
import streamlit as st
import pandas as pd
from datetime import date
from core import kpi, schema
from views import ui


def render_ai_briefing(sheets, month: str):
    st.subheader("🤖 AI 브리핑 모니터링")
    df = sheets.read(schema.SHEET_BRIEFING)
    roll = kpi.briefing_rollup(df.to_dict("records"), month)
    st.markdown(ui.kpi_cards([
        {"icon": "📡", "tone": "red", "label": f"{month} 노출 횟수", "value": roll["exposed_count"], "sub": "AI브리핑 노출"},
        {"icon": "🔑", "tone": "blue", "label": "노출 키워드 수", "value": roll["keyword_count"], "sub": "고유 키워드"},
        {"icon": "🗂️", "tone": "violet", "label": "콘텐츠 유형 수", "value": len(roll["by_type"]), "sub": "정보/비교/후기"},
    ]), unsafe_allow_html=True)
    if roll["by_type"]:
        st.bar_chart(pd.Series(roll["by_type"]))

    st.markdown("##### ✏️ 기록 추가")
    with st.form("briefing_form", clear_on_submit=True):
        d = st.date_input("날짜", value=date.today(), key="brf_date")
        kw = st.text_input("검색어", key="brf_kw")
        a1, a2 = st.columns(2)
        ai_exp = a1.selectbox("AI브리핑 노출", ["Y", "N"], key="brf_ai")
        sf_exp = a2.selectbox("삼성화재 노출", ["Y", "N"], key="brf_sf")
        ctype = st.selectbox("노출 콘텐츠 유형", schema.CONTENT_TYPES, key="brf_type")
        if st.form_submit_button("기록 추가"):
            sheets.append(schema.SHEET_BRIEFING, {
                "date": d.isoformat(), "keyword": kw, "ai_briefing_exposed": ai_exp,
                "samsung_exposed": sf_exp, "content_type": ctype})
            st.success("기록 완료")

    st.dataframe(df, use_container_width=True, hide_index=True)
