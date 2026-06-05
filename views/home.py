"""홈 탭 — KPI 카드 + 마감 임박 + 최근 QA (클린 코퍼레이트 디자인 / A안)."""
import streamlit as st
from datetime import date
from core import kpi, schedule_logic, schema

_CSS = """
<style>
.vh-wrap{font-family:'Pretendard',-apple-system,'Segoe UI',sans-serif;font-variant-numeric:tabular-nums;}
.vh-kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:4px 0 22px;}
.vh-k{background:#fff;border-radius:14px;padding:16px 16px 15px;border:1px solid #eef2f8;
      box-shadow:0 6px 18px rgba(37,99,235,.07);transition:transform .2s,box-shadow .2s;}
.vh-k:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(37,99,235,.13);}
.vh-ic{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;margin-bottom:11px;}
.vh-lab{font-size:11.5px;color:#8a94a6;font-weight:600;letter-spacing:-.2px;}
.vh-num{font-size:32px;font-weight:800;letter-spacing:-1.5px;color:#16213d;margin-top:3px;line-height:1;}
.vh-sub{font-size:11px;margin-top:7px;font-weight:600;color:#9aa4b4;}
.vh-grid2{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;}
.vh-panel{background:#fff;border-radius:14px;padding:18px 20px;border:1px solid #eef2f8;box-shadow:0 6px 18px rgba(20,30,55,.05);}
.vh-panel h3{font-size:13.5px;font-weight:800;color:#16213d;margin:0 0 12px;}
.vh-row{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid #f2f5f9;}
.vh-row:last-child{border:none;}
.vh-t{font-size:12.5px;font-weight:600;color:#26324a;}
.vh-s{font-size:10.5px;color:#8a94a6;margin-top:2px;}
.vh-pill{font-size:10px;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap;}
.p-prog{background:#e7f0ff;color:#2563eb;}.p-wait{background:#fff4e2;color:#d98300;}
.p-late{background:#ffeaea;color:#e23b3b;}.p-done{background:#e4f7ec;color:#1d9d5f;}
.vh-dd{font-size:11px;font-weight:800;white-space:nowrap;}
.vh-dd.soon{color:#e23b3b;}.vh-dd.ok{color:#9aa4b4;}
.vh-empty{font-size:12px;color:#9aa4b4;padding:14px 0;}
.vh-ring{width:92px;height:92px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:4px auto 12px;}
.vh-ring i{width:70px;height:70px;border-radius:50%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;font-style:normal;}
.vh-ring b{font-size:24px;font-weight:800;color:#16213d;}
.vh-ring span{font-size:9px;color:#9aa4b4;}
.vh-qrow{display:flex;justify-content:space-between;font-size:12px;padding:6px 0;color:#5b6678;}
.vh-qrow b{color:#16213d;}
</style>
"""

_KPI_STYLE = [
    ("📝", "#e7f0ff", "#2563eb", "진행중 원고", "in_progress", "작성·심의 진행"),
    ("⏳", "#fff4e2", "#d98300", "심의 대기", "review_waiting", "심의 접수됨"),
    ("✅", "#efe9ff", "#6b46c9", "심의 완료", "review_done", "당월 누적"),
    ("🚀", "#e4f7ec", "#1d9d5f", "발행 완료", "published", "당월 누적"),
    ("🤖", "#ffeaea", "#e23b3b", "AI브리핑 노출", "briefing_exposed", "당월 노출"),
]

_PILL = {"진행중": "p-prog", "지연": "p-late", "예정": "p-wait", "완료": "p-done"}


def _kpi_html(k: dict) -> str:
    cards = []
    for icon, bg, fg, label, key, sub in _KPI_STYLE:
        cards.append(
            f'<div class="vh-k"><div class="vh-ic" style="background:{bg};color:{fg}">{icon}</div>'
            f'<div class="vh-lab">{label}</div><div class="vh-num">{k.get(key, 0)}</div>'
            f'<div class="vh-sub">{sub}</div></div>')
    return '<div class="vh-kpis">' + "".join(cards) + "</div>"


def _dday_class(dday: str) -> str:
    if dday in ("지연", "D-DAY"):
        return "soon"
    if dday.startswith("D-"):
        try:
            return "soon" if int(dday[2:]) <= 3 else "ok"
        except ValueError:
            return "ok"
    return "ok"


def _deadline_html(rows: list) -> str:
    if not rows:
        return '<div class="vh-empty">예정된 마감이 없습니다.</div>'
    out = []
    for r in rows:
        status = r.get("status", "")
        pill = _PILL.get(status, "p-wait")
        dday = r.get("dday", "") or ""
        title = r.get("title") or "(제목 없음)"
        chan = r.get("channel", "")
        out.append(
            f'<div class="vh-row"><div><div class="vh-t">{title}</div><div class="vh-s">{chan}</div></div>'
            f'<span class="vh-pill {pill}">{status}</span>'
            f'<span class="vh-dd {_dday_class(dday)}">{dday}</span></div>')
    return "".join(out)


def _qa_html(qa: list) -> str:
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
    miss = "있음" if str(last.get("missing_phrase", "")).upper() in ("Y", "TRUE", "1") else "없음"
    price = "발견" if str(last.get("price_found", "")).upper() in ("Y", "TRUE", "1") else "없음"
    rows = (
        f'<div class="vh-qrow"><span>금지표현</span><b>{last.get("banned_count", 0)}건</b></div>'
        f'<div class="vh-qrow"><span>특약명 오류</span><b>{last.get("rider_error_count", 0)}건</b></div>'
        f'<div class="vh-qrow"><span>필수문구 누락</span>'
        f'<b style="color:{"#e23b3b" if miss == "있음" else "#16213d"}">{miss}</b></div>'
        f'<div class="vh-qrow"><span>보험료 기재</span><b>{price}</b></div>')
    return ring + rows


def render_home(sheets, month: str):
    schedule = schedule_logic.annotate(
        sheets.read(schema.SHEET_SCHEDULE).to_dict("records"), date.today())
    reviews = sheets.read(schema.SHEET_REVIEWS).to_dict("records")
    qa = sheets.read(schema.SHEET_QA).to_dict("records")
    briefing = sheets.read(schema.SHEET_BRIEFING).to_dict("records")

    k = kpi.aggregate_kpis(schedule, reviews, qa, briefing, month)
    deadlines = schedule_logic.upcoming_deadlines(schedule, date.today(), top_n=5)

    html = (
        _CSS + '<div class="vh-wrap">'
        + _kpi_html(k)
        + '<div class="vh-grid2">'
        + '<div class="vh-panel"><h3>⏰ 이번주 마감 임박</h3>' + _deadline_html(deadlines) + '</div>'
        + '<div class="vh-panel"><h3>🔍 최근 QA 결과</h3>' + _qa_html(qa) + '</div>'
        + '</div></div>')
    st.markdown(html, unsafe_allow_html=True)
