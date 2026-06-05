"""심의관리 탭 (클린 코퍼레이트 톤)."""
import streamlit as st
from core import kpi, schema
from views import ui

_REV_TONE = {
    "작성중": ("✍️", "gray"),
    "심의접수": ("📨", "blue"),
    "수정요청": ("🔁", "amber"),
    "심의완료": ("✅", "violet"),
    "발행완료": ("🚀", "green"),
}


def render_reviews(sheets):
    st.subheader("📋 심의관리")
    df = sheets.read(schema.SHEET_REVIEWS)
    counts = kpi.review_status_counts(df.to_dict("records"))
    cards = []
    for stt in schema.REVIEW_STATUSES:
        icon, tone = _REV_TONE.get(stt, ("•", "gray"))
        cards.append({"icon": icon, "tone": tone, "label": stt, "value": counts.get(stt, 0), "sub": "건"})
    st.markdown(ui.kpi_cards(cards), unsafe_allow_html=True)

    status_f = st.selectbox("상태", ["전체"] + schema.REVIEW_STATUSES, key="rev_status")
    view = df if status_f == "전체" else df[df["status"] == status_f]
    st.dataframe(view, use_container_width=True, hide_index=True)

    st.markdown("##### ✏️ 심의 편집")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True,
                            column_config={"status": st.column_config.SelectboxColumn(options=schema.REVIEW_STATUSES)},
                            key="rev_editor")
    if st.button("심의 저장", key="rev_save"):
        sheets.overwrite(schema.SHEET_REVIEWS, edited)
        st.success("저장 완료")
