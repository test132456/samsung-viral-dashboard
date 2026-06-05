"""심의본비교 탭 (2순위)."""
import streamlit as st
from datetime import date
from core import compare_engine, fetcher, schema
from views.qa import _refs_from_sheets, _read_docx


def render_compare(sheets):
    st.subheader("🔀 심의 완료본 vs 실제 발행본 비교")
    content_id = st.text_input("content_id (선택)")
    col_l, col_r = st.columns(2)
    with col_l:
        up = st.file_uploader("심의 완료본 (.docx/.txt)", type=["docx", "txt"], key="appr")
        approved = _read_docx(up) if (up and up.name.endswith(".docx")) else (up.read().decode("utf-8", "ignore") if up else "")
        approved = st.text_area("심의 완료본 텍스트", value=approved, height=240)
    with col_r:
        url = st.text_input("발행 URL")
        published = st.session_state.get("pub_text", "")
        if st.button("URL 자동수집"):
            try:
                published = fetcher.fetch_naver_text(url)
                st.session_state["pub_text"] = published
                st.success("수집 성공")
            except fetcher.FetchError as e:
                st.error(str(e))
        published = st.text_area("발행본 텍스트 (자동수집 실패 시 직접 붙여넣기)", value=published, height=240)

    if st.button("비교 실행", type="primary", disabled=not (approved.strip() and published.strip())):
        rep = compare_engine.compare(approved, published, _refs_from_sheets(sheets))
        c = st.columns(4)
        c[0].metric("일치율", f"{rep['match_rate']}%")
        c[1].metric("변경", rep["changed"]); c[2].metric("삭제", rep["deleted"]); c[3].metric("추가", rep["added"])
        b = st.columns(3)
        b[0].metric("고지문구", "정상" if rep["notice_ok"] else "이상")
        b[1].metric("해시태그", "정상" if rep["hashtag_ok"] else "이상")
        b[2].metric("특약명", "정상" if rep["rider_ok"] else "이상")
        for ch in rep["changed_list"]:
            st.warning(f"변경: {ch['from']} → {ch['to']}")
        for d in rep["deleted_list"]:
            st.error(f"삭제됨: {d}")
        for ad in rep["added_list"]:
            st.success(f"추가됨: {ad}")
        if st.button("결과 시트에 저장"):
            sheets.append(schema.SHEET_COMPARE, {
                "content_id": content_id, "match_rate": rep["match_rate"],
                "changed": rep["changed"], "deleted": rep["deleted"], "added": rep["added"],
                "notice_ok": "Y" if rep["notice_ok"] else "N",
                "rider_ok": "Y" if rep["rider_ok"] else "N",
                "checked_at": date.today().isoformat()})
            st.success("저장 완료")
