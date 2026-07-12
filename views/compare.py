"""심의본비교 탭 (2순위)."""
import streamlit as st
from datetime import date
from core import compare_engine, fetcher, schema, manuscript_parser
from views import ui
from views.qa import _refs_from_sheets


def _approved_from_upload(up) -> str:
    """심의본 업로드 → 텍스트. docx는 다중 원고 분리 + 블로거 선택."""
    if up is None:
        return ""
    data = up.getvalue()
    if not up.name.lower().endswith(".docx"):
        return data.decode("utf-8", "ignore")
    secs = manuscript_parser.parse_docx_sections(data)
    if len(secs) >= 2:
        names = [s["name"] or f"섹션 {i + 1}" for i, s in enumerate(secs)]
        pick = st.selectbox("블로거 선택 (여러 명 원고)", names, key="cmp_blogger")
        sec = secs[names.index(pick)]
        st.caption(f"✅ **{sec['name']}** 원고 추출" + (f" · 표기 URL: {sec['url']}" if sec['url'] else ""))
        return sec["body"]
    if len(secs) == 1:
        return secs[0]["body"]
    return manuscript_parser.all_text(data)


def render_compare(sheets):
    st.subheader("🔀 원고 ↔ 발행물 비교")
    st.caption("워드 원고(이름 선택)와 네이버 발행 URL을 자동수집해 문장 단위로 비교")
    content_id = st.text_input("content_id (선택)", key="cmp_cid")
    col_l, col_r = st.columns(2)
    with col_l:
        up = st.file_uploader("심의 완료본 (.docx/.txt) — 여러 명 원고 자동 분리",
                              type=["docx", "txt"], key="appr")
        approved = st.text_area("심의 완료본 텍스트", value=_approved_from_upload(up), height=240)
    with col_r:
        url = st.text_input("발행 URL", key="cmp_url")
        published = st.session_state.get("pub_text", "")
        if st.button("URL 자동수집", key="cmp_fetch"):
            try:
                published = fetcher.fetch_naver_text(url)
                st.session_state["pub_text"] = published
                st.success("수집 성공")
            except fetcher.FetchError as e:
                st.error(str(e))
        published = st.text_area("발행본 텍스트 (자동수집 실패 시 직접 붙여넣기)", value=published, height=240)

    if st.button("비교 실행", type="primary", disabled=not (approved.strip() and published.strip()), key="cmp_run"):
        st.session_state["compare_report"] = compare_engine.compare(approved, published, _refs_from_sheets(sheets))
        st.session_state["compare_cid"] = content_id

    rep = st.session_state.get("compare_report")
    if rep:
        mr = rep["match_rate"]
        mr_tone = "green" if mr >= 95 else ("amber" if mr >= 80 else "red")
        st.markdown(ui.kpi_cards([
            {"icon": "🎯", "tone": mr_tone, "label": "일치율", "value": f"{mr}%", "sub": "심의본 대비"},
            {"icon": "✏️", "tone": "amber" if rep["changed"] else "green",
             "label": "변경 문장", "value": f'{rep["changed"]}건', "sub": "수정됨"},
            {"icon": "🗑️", "tone": "red" if rep["deleted"] else "green",
             "label": "삭제 문장", "value": f'{rep["deleted"]}건', "sub": "발행본서 빠짐"},
            {"icon": "➕", "tone": "blue" if rep["added"] else "green",
             "label": "추가 문장", "value": f'{rep["added"]}건', "sub": "발행본에 추가"},
        ]), unsafe_allow_html=True)
        st.markdown(ui.kpi_cards([
            {"icon": "📢", "tone": "green" if rep["notice_ok"] else "red",
             "label": "고지문구", "value": "정상" if rep["notice_ok"] else "이상", "sub": "필수문구 유지"},
            {"icon": "#️⃣", "tone": "green" if rep["hashtag_ok"] else "red",
             "label": "해시태그", "value": "정상" if rep["hashtag_ok"] else "이상", "sub": "필수 해시태그"},
            {"icon": "📑", "tone": "green" if rep["rider_ok"] else "red",
             "label": "특약명", "value": "정상" if rep["rider_ok"] else "이상", "sub": "특약명 유지"},
        ]), unsafe_allow_html=True)
        for ch in rep["changed_list"]:
            st.warning(f"변경: {ch['from']} → {ch['to']}")
        for d in rep["deleted_list"]:
            st.error(f"삭제됨: {d}")
        for ad in rep["added_list"]:
            st.success(f"추가됨: {ad}")
        if st.button("결과 시트에 저장", key="cmp_save"):
            sheets.append(schema.SHEET_COMPARE, {
                "content_id": st.session_state.get("compare_cid", ""), "match_rate": rep["match_rate"],
                "changed": rep["changed"], "deleted": rep["deleted"], "added": rep["added"],
                "notice_ok": "Y" if rep["notice_ok"] else "N",
                "rider_ok": "Y" if rep["rider_ok"] else "N",
                "checked_at": date.today().isoformat()})
            st.success("저장 완료")
