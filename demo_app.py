"""데모 모드 진입점 — 구글시트/Claude 없이 샘플 데이터로 대시보드 미리보기.

실행: streamlit run demo_app.py
저장/기록은 임시 메모리(세션)에만 반영되며 새로고침 시 초기화된다.
production 진입점은 app.py (구글시트 + Claude 연결).
"""
import streamlit as st
from core.mock_sheets import MockSheets
from demo_data import SEED
from views import home, schedule, influencers, qa, reviews, compare, ai_briefing

st.set_page_config(page_title="[데모] 삼성화재 바이럴 운영 대시보드", layout="wide")


@st.cache_resource
def get_demo_sheets():
    return MockSheets(SEED)


sheets = get_demo_sheets()
claude = None  # 데모에서는 AI 2차검수 비활성 (규칙검수는 동작)

st.title("삼성화재 해외여행보험 바이럴 운영 대시보드")
st.caption("바이럴 운영 PM + QA 관리 시스템  ·  🔶 데모 모드 (샘플 데이터 · 구글시트/AI 미연결)")
st.info("샘플 데이터로 동작하는 미리보기입니다. 저장·기록은 임시 메모리에만 반영되고 새로고침하면 초기화됩니다.", icon="🔶")

month = st.sidebar.text_input("운영월 (YYYY-MM)", value="2026-06")
st.sidebar.caption("데모: 기준일 2026-06-05 가정")

tabs = st.tabs(["🏠 홈", "📅 일정관리", "👥 체험단관리", "🔍 QA검수",
                "📋 심의관리", "🔀 심의본비교", "🤖 AI브리핑"])
with tabs[0]: home.render_home(sheets, month)
with tabs[1]: schedule.render_schedule(sheets, month)
with tabs[2]: influencers.render_influencers(sheets)
with tabs[3]: qa.render_qa(sheets, claude)
with tabs[4]: reviews.render_reviews(sheets)
with tabs[5]: compare.render_compare(sheets)
with tabs[6]: ai_briefing.render_ai_briefing(sheets, month)
