"""체험단관리 탭 (클린 코퍼레이트 톤)."""
import streamlit as st
from core import kpi, schema
from views import ui


def render_influencers(sheets):
    st.subheader("👥 체험단관리")
    df = sheets.read(schema.SHEET_INFLUENCERS)
    rows = df.to_dict("records")
    s = kpi.influencer_summary(rows)
    st.markdown(ui.kpi_cards([
        {"icon": "👥", "tone": "blue", "label": "선정", "value": s["selected"], "sub": "선정된 블로거"},
        {"icon": "📝", "tone": "amber", "label": "원고 제출", "value": s["submitted"], "sub": "제출 완료"},
        {"icon": "🚀", "tone": "green", "label": "발행 완료", "value": s["published"], "sub": "발행됨"},
        {"icon": "📈", "tone": "violet", "label": "발행율", "value": f'{s["publish_rate"]}%', "sub": "선정 대비"},
    ]), unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    cats = ["전체"] + sorted({str(r.get("category", "")) for r in rows if r.get("category")})
    cat = f1.selectbox("카테고리", cats, key="inf_cat")
    sel = f2.selectbox("선정여부", ["전체", "Y", "N"], key="inf_sel")
    pub = f3.selectbox("발행여부", ["전체", "Y", "N"], key="inf_pub")
    view = df.copy()
    if cat != "전체":
        view = view[view["category"].astype(str) == cat]
    if sel != "전체":
        view = view[view["selected"].astype(str).str.upper() == sel]
    if pub != "전체":
        view = view[view["published"].astype(str).str.upper() == pub]
    st.dataframe(view, use_container_width=True, hide_index=True)

    st.markdown("##### ✏️ 체험단 편집")
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="inf_editor")
    if st.button("체험단 저장", key="inf_save"):
        sheets.overwrite(schema.SHEET_INFLUENCERS, edited)
        st.success("저장 완료")
