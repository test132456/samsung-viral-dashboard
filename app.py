"""삼성화재 바이럴 운영 대시보드 진입점.

시크릿(gcp_service_account + SPREADSHEET_ID)이 있으면 구글시트에 연결하고,
없으면 내장 기준데이터로 시트 없이 단독 동작한다(업로드 기반 검수·비교).
"""
import streamlit as st
import os
from datetime import date
from core.sheets import Sheets
from core.claude_client import ClaudeClient
from core import schema
from views import qa, compare, ai_briefing, ui

st.set_page_config(page_title="삼성화재 바이럴 운영 대시보드", layout="wide")


@st.cache_resource
def get_sheets():
    """시크릿 있으면 구글시트, 없으면 내장 기준데이터(MockSheets)로 폴백.
    반환: (sheets, connected: bool)."""
    try:
        sa = dict(st.secrets["gcp_service_account"])
        sid = st.secrets["SPREADSHEET_ID"]
    except Exception:
        sa = sid = None
    if sa and sid:
        try:
            s = Sheets(sa, sid)
            s.ensure_tabs()
            return s, True
        except Exception as e:
            st.warning(f"구글시트 연결 실패 — 내장 기준으로 동작합니다. ({e})")
    from core.mock_sheets import MockSheets
    from demo_data import SEED
    return MockSheets(dict(SEED)), False


@st.cache_resource
def get_claude():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        key = None
    return ClaudeClient(key) if key else None


# (선택) 발행물 수집 우회 설정 — 시크릿에 있으면 env 로 넘김
#  · NAVER_PROXY_URL: 본인 프록시(예: Cloudflare Worker) — 원본 HTML 그대로(이미지 포함) 가장 확실
#  · JINA_API_KEY: Jina Reader 키 — 텍스트 위주, 간편
try:
    for _k in ("NAVER_PROXY_URL", "JINA_API_KEY"):
        _v = st.secrets.get(_k)
        if _v:
            os.environ[_k] = _v
except Exception:
    pass

st.markdown(ui.GLOBAL_CSS, unsafe_allow_html=True)
st.title("삼성화재 해외여행보험 바이럴 운영 대시보드")

sheets, connected = get_sheets()
claude = get_claude()
st.caption("바이럴 운영 PM + QA 관리 시스템"
           + ("" if connected else "  ·  시트 미연결(내장 기준으로 동작 · AI 노출현황은 샘플)"))

PAGES = ["📝 심의전 원고 검수", "🔀 원고↔발행물 비교", "🤖 AI 노출현황"]
st.sidebar.markdown(
    '<div class="vh-brand"><div class="vh-logo">SF</div>'
    '<div><div class="vh-bt">삼성화재 바이럴</div><div class="vh-bs">운영 PM + QA</div></div></div>'
    '<div class="vh-mlabel">MENU</div>', unsafe_allow_html=True)
page = st.sidebar.radio("메뉴", PAGES, label_visibility="collapsed", key="nav")
st.sidebar.divider()
_cur = date.today().strftime("%Y-%m")
_default = schema.MONTHS.index(_cur) if _cur in schema.MONTHS else schema.MONTHS.index(schema.DEFAULT_MONTH)
month = st.sidebar.selectbox("운영월", schema.MONTHS, index=_default, key="op_month")

if page == "📝 심의전 원고 검수":
    qa.render_qa(sheets, claude)
elif page == "🔀 원고↔발행물 비교":
    compare.render_compare(sheets)
elif page == "🤖 AI 노출현황":
    ai_briefing.render_ai_briefing(sheets, month)
