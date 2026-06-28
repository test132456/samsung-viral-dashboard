"""데모 모드 진입점 — 구글시트/Claude 없이 샘플 데이터로 대시보드 미리보기.

실행: streamlit run demo_app.py
저장/기록은 임시 메모리(세션)에만 반영되며 새로고침 시 초기화된다.
production 진입점은 app.py (구글시트 + Claude 연결).
"""
import os
import streamlit as st
from core.mock_sheets import MockSheets
from core import schema
from demo_data import SEED
from views import home, schedule, qa, reviews, compare, ai_briefing, ui

st.set_page_config(page_title="[데모] 삼성화재 바이럴 운영 대시보드", layout="wide")


@st.cache_resource
def get_demo_sheets():
    """샘플 시드로 시작하되, 같은 폴더에 '바이럴 일정.xlsx'가 있으면
    달력 일정을 엑셀 전체(전월 포함)로 교체해 모든 달을 채운다(로컬 미리보기용)."""
    seed = dict(SEED)
    base_cal = list(SEED.get(schema.SHEET_CALENDAR, []))
    xlsx = os.path.join(os.path.dirname(os.path.abspath(__file__)), "바이럴 일정.xlsx")
    if os.path.exists(xlsx):
        try:
            from core import viral_parser
            events, _dist = viral_parser.parse(xlsx)
            if events:
                base_cal = events
        except Exception:
            pass
    # 7~12월 초안 일정 자동 생성해 미리 채워둠 (데모)
    from core import schedule_gen
    seed[schema.SHEET_CALENDAR] = base_cal + schedule_gen.generate(
        [f"2026-{m:02d}" for m in range(7, 13)])
    return MockSheets(seed)


sheets = get_demo_sheets()
claude = None  # 데모에서는 AI 2차검수 비활성 (규칙검수는 동작)

st.markdown(ui.GLOBAL_CSS, unsafe_allow_html=True)
st.title("삼성화재 해외여행보험 바이럴 운영 대시보드")
st.caption("바이럴 운영 PM + QA 관리 시스템  ·  🔶 데모 모드 (샘플 데이터 · 구글시트/AI 미연결)")
st.info("샘플 데이터로 동작하는 미리보기입니다. 저장·기록은 임시 메모리에만 반영되고 새로고침하면 초기화됩니다.", icon="🔶")

PAGES = ["🏠 홈", "🔍 QA검수", "🔀 심의본비교", "🤖 AI 노출현황"]
page = st.sidebar.radio("메뉴", PAGES, label_visibility="collapsed", key="nav")
st.sidebar.divider()
month = st.sidebar.selectbox("운영월", schema.MONTHS,
                             index=schema.MONTHS.index(schema.DEFAULT_MONTH), key="op_month")
st.sidebar.caption("데모: 기준일 2026-06-05 가정 · 6월에 샘플 데이터 있음")

if page == "🏠 홈":
    home.render_home(sheets, month)
elif page == "🔍 QA검수":
    qa.render_qa(sheets, claude)
elif page == "🔀 심의본비교":
    compare.render_compare(sheets)
elif page == "🤖 AI 노출현황":
    ai_briefing.render_ai_briefing(sheets, month)
