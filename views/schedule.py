"""일정관리 탭 (3순위) — 진행 현황 + 월 달력 + 배포 일정."""
import streamlit as st
import pandas as pd
from datetime import date
from core import schedule_logic, schema, calendar_view

_DOW = ["일", "월", "화", "수", "목", "금", "토"]
_TRACK_COLOR = {"공식": "#1f74e0", "배포형": "#2bb673"}


def _calendar_html(grid: list) -> str:
    def col(track):
        return _TRACK_COLOR.get(str(track).strip(), "#8a94a6")

    def day_color(i):
        return "#e23b3b" if i == 0 else ("#1f74e0" if i == 6 else "#26324a")

    out = ['<table style="width:100%;border-collapse:collapse;table-layout:fixed;'
           'font-family:Pretendard,-apple-system,sans-serif">']
    out.append("<tr>" + "".join(
        f'<th style="padding:6px;border:1px solid #e6ebf3;background:#f4f6fa;'
        f'font-size:12px;color:{day_color(i)}">{d}</th>' for i, d in enumerate(_DOW)) + "</tr>")
    for wk in grid:
        out.append("<tr>")
        for i, cell in enumerate(wk):
            if not cell["day"]:
                out.append('<td style="border:1px solid #eef1f6;background:#fafbfd;'
                           'height:104px;vertical-align:top"></td>')
                continue
            chips = "".join(
                f'<div style="margin-top:3px;padding:2px 5px;border-radius:5px;'
                f'background:{col(e.get("track",""))};color:#fff;font-size:10px;'
                f'line-height:1.3;word-break:keep-all">{e.get("task","")}</div>'
                for e in cell["events"])
            out.append(
                f'<td style="border:1px solid #eef1f6;height:104px;vertical-align:top;padding:4px">'
                f'<div style="font-size:12px;font-weight:700;color:{day_color(i)}">{cell["day"]}</div>'
                f'{chips}</td>')
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


def render_schedule(sheets, month: str):
    st.subheader("📅 일정관리")
    df = sheets.read(schema.SHEET_SCHEDULE)

    f1, f2 = st.columns(2)
    channel = f1.selectbox("채널", ["전체"] + schema.CHANNELS, key="sch_channel")
    status_f = f2.selectbox("상태", ["전체"] + schema.SCHEDULE_STATUSES, key="sch_status")

    rows = schedule_logic.annotate(df.to_dict("records"), date.today())
    if channel != "전체":
        rows = [r for r in rows if r.get("channel") == channel]
    if status_f != "전체":
        rows = [r for r in rows if r["status"] == status_f]

    view = pd.DataFrame(rows)
    if not view.empty:
        st.dataframe(view[["title", "channel", "publish_plan_date", "status", "dday"]],
                     use_container_width=True, hide_index=True)

    st.markdown("##### 일정 편집")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True,
                            column_config={"status": st.column_config.SelectboxColumn(options=schema.SCHEDULE_STATUSES)},
                            key="sch_editor")
    if st.button("일정 저장", key="sch_save"):
        sheets.overwrite(schema.SHEET_SCHEDULE, edited)
        st.success("저장 완료")

    # --- 월 달력 ---
    st.divider()
    st.markdown("#### 📆 달력")
    _idx = schema.MONTHS.index(month) if month in schema.MONTHS else schema.MONTHS.index(schema.DEFAULT_MONTH)
    c_sel, _c_rest = st.columns([1, 3])
    cal_month = c_sel.selectbox("달력 월 선택", schema.MONTHS, index=_idx,
                                key="cal_month", label_visibility="collapsed",
                                help="다른 달의 달력을 보려면 선택하세요")
    try:
        yy, mm = int(cal_month[:4]), int(cal_month[5:7])
    except (ValueError, IndexError):
        yy, mm = date.today().year, date.today().month
    cal_rows = sheets.read(schema.SHEET_CALENDAR).to_dict("records")
    cal_rows = [e for e in cal_rows if str(e.get("date", ""))[:7] == cal_month]
    grid = calendar_view.month_grid(yy, mm, cal_rows)
    st.markdown(_calendar_html(grid), unsafe_allow_html=True)
    st.caption("🟦 공식   🟩 배포형   ⬜ 기타 · 워크플로 일정")
    if not cal_rows:
        st.info(f"📭 **{cal_month}** 에 등록된 달력 일정이 없습니다. "
                f"아래 ✏️ 편집기에서 직접 추가하세요.")

    with st.expander("✏️ 달력 일정 직접 입력 / 편집"):
        st.caption("행을 추가/수정하고 저장하면 위 달력에 즉시 반영됩니다. 날짜는 YYYY-MM-DD 형식.")
        cal_df = sheets.read(schema.SHEET_CALENDAR)
        cal_edit = st.data_editor(
            cal_df, num_rows="dynamic", use_container_width=True, key="cal_editor",
            column_config={
                "date": st.column_config.TextColumn("날짜 (YYYY-MM-DD)", width="small"),
                "task": st.column_config.TextColumn("일정 내용", width="large"),
                "track": st.column_config.SelectboxColumn("구분", options=schema.TRACKS),
            })
        if st.button("달력 일정 저장", key="cal_save"):
            sheets.overwrite(schema.SHEET_CALENDAR, cal_edit)
            st.success("저장 완료")
            st.rerun()

    # --- 배포 일정 (직접 편집) ---
    st.divider()
    st.markdown("#### 🚀 배포 일정")
    dist = sheets.read(schema.SHEET_DISTRIBUTION)

    # 그룹별 건수 요약
    seen = []
    for grp in dist["group"].tolist():
        if str(grp).strip() and grp not in seen:
            seen.append(grp)
    if seen:
        summary = "　·　".join(f"{grp} {int((dist['group'] == grp).sum())}건" for grp in seen)
        st.caption(summary)

    st.caption("표에서 셀을 더블클릭해 수정하거나 맨 아래 빈 행에 입력하세요. 행 삭제는 행 선택 후 휴지통. "
               "같은 **그룹**명끼리 묶입니다. 배포일은 YYYY-MM-DD 형식. 수정 후 **저장**을 누르세요.")
    dist_edit = st.data_editor(
        dist, num_rows="dynamic", use_container_width=True, hide_index=True, key="dist_editor",
        column_config={
            "group": st.column_config.TextColumn(
                "그룹", help="예: 배포형 (5월 작성) / 공식블로그 / 변경심의 — 같은 이름끼리 묶입니다"),
            "blogger": st.column_config.TextColumn("블로거"),
            "publish_date": st.column_config.TextColumn("배포일 (YYYY-MM-DD)"),
            "approval_no": st.column_config.TextColumn("심의필"),
            "landing_url": st.column_config.TextColumn("랜딩URL", width="medium"),
            "note": st.column_config.TextColumn("비고"),
            "publish_url": st.column_config.TextColumn("발행URL", width="medium"),
        })
    if st.button("배포 일정 저장", key="dist_save", type="primary"):
        sheets.overwrite(schema.SHEET_DISTRIBUTION, dist_edit)
        st.success("저장 완료")
        st.rerun()
