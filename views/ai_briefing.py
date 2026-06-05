"""AI브리핑 모니터링 탭 (4순위)."""
import streamlit as st
import pandas as pd
from datetime import date
from core import kpi, schema


def render_ai_briefing(sheets, month: str):
    st.subheader("🤖 AI 브리핑 모니터링")
    df = sheets.read(schema.SHEET_BRIEFING)
    roll = kpi.briefing_rollup(df.to_dict("records"), month)
    c = st.columns(3)
    c[0].metric(f"{month} 노출 횟수", roll["exposed_count"])
    c[1].metric("노출 키워드 수", roll["keyword_count"])
    c[2].metric("콘텐츠 유형 수", len(roll["by_type"]))
    if roll["by_type"]:
        st.bar_chart(pd.Series(roll["by_type"]))

    st.markdown("##### 기록 추가")
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
