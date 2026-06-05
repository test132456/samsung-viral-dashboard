"""홈 탭 — KPI 카드 + 마감 임박 + 최근 QA."""
import streamlit as st
from datetime import date
from core import kpi, schedule_logic, schema


def render_home(sheets, month: str):
    schedule = sheets.read(schema.SHEET_SCHEDULE).to_dict("records")
    reviews = sheets.read(schema.SHEET_REVIEWS).to_dict("records")
    qa = sheets.read(schema.SHEET_QA).to_dict("records")
    briefing = sheets.read(schema.SHEET_BRIEFING).to_dict("records")

    k = kpi.aggregate_kpis(schedule, reviews, qa, briefing, month)
    c = st.columns(5)
    c[0].metric("진행중 원고", k["in_progress"])
    c[1].metric("심의 대기", k["review_waiting"])
    c[2].metric("심의 완료", k["review_done"])
    c[3].metric("발행 완료", k["published"])
    c[4].metric("AI브리핑 노출", k["briefing_exposed"])

    st.markdown("##### ⏰ 이번주 마감 임박")
    for r in schedule_logic.upcoming_deadlines(schedule, date.today(), top_n=5):
        st.write(f"- **{r.get('title','(제목없음)')}** · {r.get('channel','')} · {r['status']} · {r['dday']}")

    st.markdown("##### 🔍 최근 QA 결과")
    if qa:
        last = qa[-1]
        st.write(f"점수 **{last.get('qa_score','-')}** · 금지표현 {last.get('banned_count','-')} · 특약오류 {last.get('rider_error_count','-')}")
    else:
        st.caption("QA 기록 없음")
