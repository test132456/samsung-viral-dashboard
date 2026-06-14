"""삼성화재 바이럴 운영 대시보드 진입점."""
import streamlit as st
from datetime import date
from core.sheets import Sheets
from core.claude_client import ClaudeClient
from core import schema
from views import home, schedule, qa, reviews, compare, ai_briefing, ui

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


st.markdown(ui.GLOBAL_CSS, unsafe_allow_html=True)
st.title("삼성화재 해외여행보험 바이럴 운영 대시보드")
st.caption("바이럴 운영 PM + QA 관리 시스템")

try:
    sheets = get_sheets()
except Exception as e:
    st.error(f"구글시트 연결 실패: {e}")
    st.stop()
claude = get_claude()

PAGES = ["🏠 홈", "📅 일정관리", "🔍 QA검수", "📋 심의관리", "🔀 심의본비교", "🤖 AI브리핑"]
page = st.sidebar.radio("메뉴", PAGES, label_visibility="collapsed", key="nav")
st.sidebar.divider()
_cur = date.today().strftime("%Y-%m")
_default = schema.MONTHS.index(_cur) if _cur in schema.MONTHS else schema.MONTHS.index(schema.DEFAULT_MONTH)
month = st.sidebar.selectbox("운영월", schema.MONTHS, index=_default, key="op_month")

if page == "🏠 홈":
    home.render_home(sheets, month)
elif page == "📅 일정관리":
    schedule.render_schedule(sheets, month)
elif page == "🔍 QA검수":
    qa.render_qa(sheets, claude)
elif page == "📋 심의관리":
    reviews.render_reviews(sheets)
elif page == "🔀 심의본비교":
    compare.render_compare(sheets)
elif page == "🤖 AI브리핑":
    ai_briefing.render_ai_briefing(sheets, month)
