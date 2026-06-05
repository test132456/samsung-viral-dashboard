"""삼성화재 바이럴 운영 대시보드 진입점."""
import streamlit as st
from datetime import date
from core.sheets import Sheets
from core.claude_client import ClaudeClient
from views import home, schedule, influencers, qa, reviews, compare, ai_briefing

st.set_page_config(page_title="삼성화재 바이럴 운영 대시보드", layout="wide")


@st.cache_resource
def get_sheets():
    info = dict(st.secrets["gcp_service_account"])
    s = Sheets(info, st.secrets["SPREADSHEET_ID"])
    s.ensure_tabs()
    return s


@st.cache_resource
def get_claude():
    key = st.secrets.get("ANTHROPIC_API_KEY")
    return ClaudeClient(key) if key else None


st.title("삼성화재 해외여행보험 바이럴 운영 대시보드")
st.caption("바이럴 운영 PM + QA 관리 시스템")

try:
    sheets = get_sheets()
except Exception as e:
    st.error(f"구글시트 연결 실패: {e}")
    st.stop()
claude = get_claude()

month = st.sidebar.text_input("운영월 (YYYY-MM)", value=date.today().strftime("%Y-%m"), key="op_month")

tabs = st.tabs(["🏠 홈", "📅 일정관리", "👥 체험단관리", "🔍 QA검수",
                "📋 심의관리", "🔀 심의본비교", "🤖 AI브리핑"])
with tabs[0]: home.render_home(sheets, month)
with tabs[1]: schedule.render_schedule(sheets, month)
with tabs[2]: influencers.render_influencers(sheets)
with tabs[3]: qa.render_qa(sheets, claude)
with tabs[4]: reviews.render_reviews(sheets)
with tabs[5]: compare.render_compare(sheets)
with tabs[6]: ai_briefing.render_ai_briefing(sheets, month)
