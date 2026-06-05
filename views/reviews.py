"""심의관리 탭."""
import streamlit as st
from core import kpi, schema


def render_reviews(sheets):
    st.subheader("📋 심의관리")
    df = sheets.read(schema.SHEET_REVIEWS)
    counts = kpi.review_status_counts(df.to_dict("records"))
    cols = st.columns(len(schema.REVIEW_STATUSES))
    for i, s in enumerate(schema.REVIEW_STATUSES):
        cols[i].metric(s, counts.get(s, 0))

    status_f = st.selectbox("상태", ["전체"] + schema.REVIEW_STATUSES)
    view = df if status_f == "전체" else df[df["status"] == status_f]
    st.dataframe(view, use_container_width=True, hide_index=True)

    st.markdown("##### 심의 편집")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True,
                            column_config={"status": st.column_config.SelectboxColumn(options=schema.REVIEW_STATUSES)})
    if st.button("심의 저장"):
        sheets.overwrite(schema.SHEET_REVIEWS, edited)
        st.success("저장 완료")
