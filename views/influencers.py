"""체험단관리 탭."""
import streamlit as st
from core import kpi, schema


def render_influencers(sheets):
    st.subheader("👥 체험단관리")
    df = sheets.read(schema.SHEET_INFLUENCERS)
    rows = df.to_dict("records")
    s = kpi.influencer_summary(rows)
    c = st.columns(4)
    c[0].metric("선정", s["selected"]); c[1].metric("원고 제출", s["submitted"])
    c[2].metric("발행 완료", s["published"]); c[3].metric("발행율", f"{s['publish_rate']}%")

    f1, f2, f3 = st.columns(3)
    cats = ["전체"] + sorted({str(r.get("category", "")) for r in rows if r.get("category")})
    cat = f1.selectbox("카테고리", cats)
    sel = f2.selectbox("선정여부", ["전체", "Y", "N"])
    pub = f3.selectbox("발행여부", ["전체", "Y", "N"])
    view = df.copy()
    if cat != "전체": view = view[view["category"].astype(str) == cat]
    if sel != "전체": view = view[view["selected"].astype(str).str.upper() == sel]
    if pub != "전체": view = view[view["published"].astype(str).str.upper() == pub]
    st.dataframe(view, use_container_width=True, hide_index=True)

    st.markdown("##### 체험단 편집")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("체험단 저장"):
        sheets.overwrite(schema.SHEET_INFLUENCERS, edited)
        st.success("저장 완료")
