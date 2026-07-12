"""홈 탭 — 활성 기능 요약 (QA검수 · 심의본비교 · AI 노출현황)."""
import streamlit as st
from core import kpi, schema
from views import ui


def _qa_panel_html(qa: list) -> str:
    if not qa:
        return '<div class="vh-empty">아직 QA 검수 기록이 없습니다. QA검수 탭에서 원고를 검수해보세요.</div>'
    last = qa[-1]
    try:
        score = int(float(last.get("qa_score", 0)))
    except (ValueError, TypeError):
        score = 0
    color = "#2bb673" if score >= 85 else ("#f5a623" if score >= 70 else "#e23b3b")
    ring = (f'<div class="vh-ring" style="background:conic-gradient({color} 0 {score}%,#eaeef5 {score}% 100%)">'
            f'<i><b>{score}</b><span>QA 점수</span></i></div>')
    miss = str(last.get("missing_phrase", "")).upper() in ("Y", "TRUE", "1")
    price = str(last.get("price_found", "")).upper() in ("Y", "TRUE", "1")
    rows = (
        f'<div class="vh-qrow"><span>금지표현</span><b>{last.get("banned_count", 0)}건</b></div>'
        f'<div class="vh-qrow"><span>특약명 오류</span><b>{last.get("rider_error_count", 0)}건</b></div>'
        f'<div class="vh-qrow"><span>필수문구 누락</span>'
        f'<b style="color:{"#e23b3b" if miss else "#16213d"}">{"있음" if miss else "없음"}</b></div>'
        f'<div class="vh-qrow"><span>보험료 기재</span><b>{"발견" if price else "없음"}</b></div>')
    return ring + rows


def _citation_panel_html(cite: dict) -> str:
    if not cite["by_tool"]:
        return '<div class="vh-empty">AI 인용률 기록이 없습니다. AI 노출현황 탭에서 기록을 추가하세요.</div>'
    rows = "".join(f'<div class="vh-qrow"><span>{t}</span><b>{r}%</b></div>'
                   for t, r in cite["by_tool"].items())
    rows += (f'<div class="vh-qrow" style="border-top:1px solid #eef2f8;margin-top:6px;padding-top:9px">'
             f'<span><b>전체</b></span><b>{cite["overall_rate"]}%</b></div>')
    return rows


def render_home(sheets, month: str):
    qa = sheets.read(schema.SHEET_QA).to_dict("records")
    citations = sheets.read(schema.SHEET_CITATIONS).to_dict("records")
    briefing = sheets.read(schema.SHEET_BRIEFING).to_dict("records")

    qas = kpi.qa_summary(qa, month)
    cite = kpi.citation_summary(citations, month)
    brief = kpi.briefing_rollup(briefing, month)

    score = qas["latest_score"]
    score_tone = "gray" if score is None else ("green" if score >= 85 else ("amber" if score >= 70 else "red"))

    cards_html = ui.kpi_cards([
        {"icon": "🎯", "tone": score_tone, "label": "최근 QA 점수",
         "value": score if score is not None else "—", "sub": "마지막 검수"},
        {"icon": "🔍", "tone": "blue", "label": "이번달 QA 검수",
         "value": f'{qas["count"]}건', "sub": month},
        {"icon": "📊", "tone": "violet", "label": "AI 인용률",
         "value": f'{cite["overall_rate"]}%', "sub": f'{cite["total_cited"]}/{cite["total_queries"]} 질의'},
        {"icon": "📡", "tone": "red", "label": "AI브리핑 노출",
         "value": brief["exposed_count"], "sub": month},
    ])

    panels = (
        '<div class="vh-wrap"><div class="vh-grid2">'
        '<div class="vh-panel"><h3>🔍 최근 QA 결과</h3>' + _qa_panel_html(qa) + '</div>'
        '<div class="vh-panel"><h3>📊 AI 인용률 (툴별)</h3>' + _citation_panel_html(cite) + '</div>'
        '</div></div>')

    st.markdown(cards_html + panels, unsafe_allow_html=True)
