"""일정관리 탭 (3순위)."""
import streamlit as st
import pandas as pd
from datetime import date
from core import schedule_logic, schema


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
