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
             "label": "변경", "value": f'{rep["changed"]}건', "sub": "수정됨"},
            {"icon": "🗑️", "tone": "red" if rep["deleted"] else "green",
             "label": "삭제", "value": f'{rep["deleted"]}건', "sub": "발행서 빠짐"},
            {"icon": "➕", "tone": "blue" if rep["added"] else "green",
             "label": "추가", "value": f'{rep["added"]}건', "sub": "발행에 추가"},
            {"icon": "📢", "tone": "green" if rep["notice_ok"] else "red",
             "label": "고지문구", "value": "정상" if rep["notice_ok"] else "이상", "sub": "발행본 유지"},
            {"icon": "📑", "tone": "green" if rep["rider_ok"] else "red",
             "label": "특약명", "value": "정상" if rep["rider_ok"] else "이상", "sub": "특약명 유지"},
        ]), unsafe_allow_html=True)
        st.caption("고지문구=발행본에 고지문구(예금자보호·준법감시인확인필·광고료 표기 등) 유지 · "
                   "특약명=심의본 특약명이 발행본에 유지 · **'이상'=누락/불일치**")

        def _blk(color, bg, body):
            st.markdown(f'<div style="border-left:4px solid {color};background:{bg};padding:9px 13px;'
                        f'border-radius:6px;margin-bottom:7px;font-family:Pretendard,sans-serif">{body}</div>',
                        unsafe_allow_html=True)

        LIMIT = 15
        changed = [c for c in rep["changed_list"] if c["from"].strip() or c["to"].strip()]
        deleted = [d for d in rep["deleted_list"] if d.strip()]
        added = [a for a in rep["added_list"] if a.strip()]
        changed.sort(key=lambda c: c.get("kind") == "spacing")  # 내용변경 먼저, 띄어쓰기 나중
        _sp = sum(1 for c in changed if c.get("kind") == "spacing")
        st.markdown("###### 문장 비교 결과")
        st.caption(f"🔤 표시는 **띄어쓰기만 다른 항목(내용 동일·참고용)**입니다." + (f" · 띄어쓰기 차이 {_sp}건" if _sp else ""))
        if not (changed or deleted or added):
            st.success("원고와 발행본이 문장 단위로 일치합니다.")
        for ch in changed[:LIMIT]:
            if ch.get("kind") == "spacing":
                _blk("#b3bccb", "#f4f6fa",
                     '<div style="font-size:11px;font-weight:700;color:#7a8597">🔤 띄어쓰기 차이 (내용 동일·참고용)</div>'
                     f'<div style="font-size:12.5px;color:#5b6678;margin-top:3px">📄 원고: {ch["from"].strip()}</div>'
                     f'<div style="font-size:12.5px;color:#5b6678;margin-top:2px">📤 발행: {ch["to"].strip()}</div>')
            else:
                _blk("#f5a623", "#fff8ec",
                     '<div style="font-size:11px;font-weight:700;color:#d98300">✏️ 변경</div>'
                     f'<div style="font-size:12.5px;color:#8a6d3b;margin-top:3px">📄 원고: {ch["from"].strip() or "(빈 문장)"}</div>'
                     f'<div style="font-size:12.5px;color:#16213d;margin-top:2px">📤 발행: {ch["to"].strip() or "(빈 문장)"}</div>')
        for d in deleted[:LIMIT]:
            _blk("#e23b3b", "#ffecec",
                 '<div style="font-size:11px;font-weight:700;color:#e23b3b">🗑️ 원고에만 있음 (발행본서 빠짐)</div>'
                 f'<div style="font-size:12.5px;color:#16213d;margin-top:2px">{d}</div>')
        for a in added[:LIMIT]:
            _blk("#2bb673", "#eafaf0",
                 '<div style="font-size:11px;font-weight:700;color:#1d9d5f">➕ 발행본에만 있음 (원고엔 없음)</div>'
                 f'<div style="font-size:12.5px;color:#16213d;margin-top:2px">{a}</div>')
        _extra = max(0, len(changed) - LIMIT) + max(0, len(deleted) - LIMIT) + max(0, len(added) - LIMIT)
        if _extra:
            st.caption(f"… 외 {_extra}건 더 있음 (유형별 상위 {LIMIT}건만 표시)")
