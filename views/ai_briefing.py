"""AI 노출 현황 탭 — AI 인용률 + AI브리핑 노출 (가로 세부 탭)."""
import streamlit as st
import pandas as pd
from datetime import date
from core import kpi, schema
from views import ui

_TONES = ["green", "amber", "violet", "red", "gray"]


def render_ai_briefing(sheets, month: str):
    st.subheader("🤖 AI 노출 현황")
    sub_cite, sub_brief = st.tabs(["🔎 AI 인용률", "📊 AI브리핑 노출"])
    with sub_cite:
        _render_citations(sheets, month)
    with sub_brief:
        _render_briefing(sheets, month)


def _render_citations(sheets, month: str):
    st.caption(f"{month} · 삼성화재 해외여행보험이 AI 툴(ChatGPT·Gemini 등) 답변에 인용된 비율(일별)")
    df = sheets.read(schema.SHEET_CITATIONS)
    summ = kpi.citation_summary(df.to_dict("records"), month)

    cards = [{"icon": "📊", "tone": "blue", "label": "전체 인용률",
              "value": f'{summ["overall_rate"]}%',
              "sub": f'{summ["total_cited"]}/{summ["total_queries"]} 질의'}]
    for i, (tool, rate) in enumerate(summ["by_tool"].items()):
        cards.append({"icon": "🤖", "tone": _TONES[i % len(_TONES)],
                      "label": tool, "value": f"{rate}%", "sub": "인용률"})
    st.markdown(ui.kpi_cards(cards), unsafe_allow_html=True)

    if not df.empty:
        dff = df[df["date"].astype(str).str[:7] == month].copy()
        if not dff.empty:
            dff["queries"] = pd.to_numeric(dff["queries"], errors="coerce").fillna(0)
            dff["cited"] = pd.to_numeric(dff["cited"], errors="coerce").fillna(0)
            g = dff.groupby(["date", "tool"], as_index=False)[["queries", "cited"]].sum()
            g["인용률(%)"] = (g["cited"] / g["queries"].replace(0, pd.NA) * 100).round(1)
            pivot = g.pivot(index="date", columns="tool", values="인용률(%)")
            st.markdown("###### 일별 인용률 추이 (%)")
            st.line_chart(pivot)

    st.markdown("###### ✏️ 인용률 기록 추가")
    with st.form("cite_form", clear_on_submit=True):
        cc = st.columns(5)
        cd = cc[0].date_input("날짜", value=date.today(), key="cite_date")
        ctool = cc[1].selectbox("AI 툴", schema.AI_TOOLS, key="cite_tool")
        ckw = cc[2].text_input("검색어", value="해외여행보험", key="cite_kw")
        cq = cc[3].number_input("질의 수", min_value=0, value=20, step=1, key="cite_q")
        cci = cc[4].number_input("인용 수", min_value=0, value=0, step=1, key="cite_c")
        if st.form_submit_button("기록 추가"):
            sheets.append(schema.SHEET_CITATIONS, {
                "date": cd.isoformat(), "tool": ctool, "keyword": ckw,
                "queries": int(cq), "cited": int(cci)})
            st.success("기록 완료")
            st.rerun()
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_briefing(sheets, month: str):
    st.caption(f"{month} · 네이버 AI 브리핑 노출 기록 (노출 기준 비공개 → 내부 데이터 축적용)")
    df = sheets.read(schema.SHEET_BRIEFING)
    rows = df.to_dict("records")
    roll = kpi.briefing_rollup(rows, month)
    st.markdown(ui.kpi_cards([
        {"icon": "📡", "tone": "red", "label": f"{month} 노출 횟수", "value": roll["exposed_count"], "sub": "AI브리핑 노출"},
        {"icon": "🔑", "tone": "blue", "label": "노출 키워드 수", "value": roll["keyword_count"], "sub": "고유 키워드"},
        {"icon": "🗂️", "tone": "violet", "label": "콘텐츠 유형 수", "value": len(roll["by_type"]), "sub": "정보/비교/후기"},
    ]), unsafe_allow_html=True)

    daily = kpi.briefing_daily(rows, month)
    if daily:
        st.markdown("###### 일별 노출 추이 (건)")
        st.bar_chart(pd.Series(daily, name="노출 건수"))
    if roll["by_type"]:
        st.markdown("###### 콘텐츠 유형별 (건)")
        st.bar_chart(pd.Series(roll["by_type"]))

    st.markdown("###### ✏️ 노출 기록 추가")
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
            st.rerun()
    st.dataframe(df, use_container_width=True, hide_index=True)
