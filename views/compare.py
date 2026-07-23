"""심의본비교 탭 (2순위)."""
import streamlit as st
from datetime import date
from core import compare_engine, fetcher, schema, manuscript_parser
from views import ui
from views.qa import _refs_from_sheets

# 파라미터 목록에서 숨길 기능(비트래킹) 파라미터
_HIDE_PARAMS = {"state"}


# 페이지 계산 로직(paragraph_pages)이 바뀌면 이 숫자를 +1 → 배포 시 st.cache_data 캐시 자동 무효화.
# (st.cache_data 는 '캐시된 함수 자신'만 보고, 그 안에서 호출하는 함수 변경은 감지 못 하므로 필요)
_PAGES_LOGIC_VER = 2


@st.cache_data(show_spinner=False)
def _cmp_pages(data: bytes, logic_ver: int):
    """업로드한 심의본(docx)의 문단별 추정 페이지 — 수정 위치 안내용.
    logic_ver 는 캐시 키에 포함돼 로직 변경 시 캐시를 무효화한다(_PAGES_LOGIC_VER)."""
    return manuscript_parser.paragraph_pages(data)


def _approved_from_upload(up) -> str:
    """심의본 업로드 → 텍스트. docx는 다중 원고 분리 + 블로거 선택.
    선택한 블로거 구간의 이미지는 st.session_state['cmp_man_images'] 에 저장(이미지 비교용)."""
    st.session_state["cmp_man_images"] = []
    st.session_state["cmp_sel_name"] = ""
    st.session_state["cmp_sel_title"] = ""
    if up is None:
        return ""
    data = up.getvalue()
    if not up.name.lower().endswith(".docx"):
        return data.decode("utf-8", "ignore")
    secs = manuscript_parser.parse_docx_sections(data)
    sec = None
    if len(secs) >= 2:
        names = [s["name"] or f"섹션 {i + 1}" for i, s in enumerate(secs)]
        pick = st.selectbox("블로거 선택 (여러 명 원고)", names, key="cmp_blogger")
        sec = secs[names.index(pick)]
    elif len(secs) == 1:
        sec = secs[0]
    if sec is not None:
        st.caption(f"✅ **{sec['name'] or '원고'}** 추출" + (f" · 표기 URL: {sec['url']}" if sec['url'] else ""))
        if sec.get("deleted"):
            st.markdown(ui.deleted_html(sec["deleted"]), unsafe_allow_html=True)
        st.session_state["cmp_man_images"] = sec.get("images", [])
        st.session_state["cmp_sel_name"] = sec.get("name", "")
        st.session_state["cmp_sel_title"] = sec.get("title", "")
        return sec["body"]
    # 구분표 없는 단일 원고 → 문서 전체 이미지
    st.session_state["cmp_man_images"] = manuscript_parser.extract_images(data)
    return manuscript_parser.all_text(data)


def render_compare(sheets):
    st.markdown(ui.page_header("🔀 원고 ↔ 발행물 비교",
                               "워드 원고(이름 선택)와 네이버 발행 URL을 자동수집해 문장 단위로 비교"),
                unsafe_allow_html=True)
    # 업로더는 상단 전체폭 → 아래 좌/우 높이가 자연스럽게 맞음
    up = st.file_uploader("심의 완료본 (.docx/.txt) — 여러 명 원고 자동 분리",
                          type=["docx", "txt"], key="appr")

    # 1줄: 블로거 선택(좌) ↔ 발행 URL·자동수집(우)
    row1_l, row1_r = st.columns(2)
    with row1_l:
        approved_default = _approved_from_upload(up)   # 블로거 선택 + 추출 안내 + 삭제표시
    with row1_r:
        url = st.text_input("발행 URL", key="cmp_url")
        published = st.session_state.get("pub_text", "")
        if st.button("URL 자동수집", key="cmp_fetch"):
            _ov = st.empty()
            _ov.markdown(ui.loading_overlay("네이버 발행글 가져오는 중…"), unsafe_allow_html=True)
            try:
                post = fetcher.fetch_naver_post(url)
                published = post["text"]
                st.session_state["pub_text"] = published
                st.session_state["pub_title"] = post.get("title", "")
                st.success(f"수집 성공 · 발행 제목: 《{post['title']}》" if post.get("title") else "수집 성공")
            except fetcher.FetchError as e:
                st.error(str(e))
            finally:
                _ov.empty()

    # 2줄: 심의 완료본 텍스트(좌) ↔ 발행본 텍스트(우) — 같은 줄에서 시작해 높이 정렬
    row2_l, row2_r = st.columns(2)
    with row2_l:
        approved = st.text_area("심의 완료본 텍스트", value=approved_default, height=260)
    with row2_r:
        published = st.text_area("발행본 텍스트", value=published, height=260,
                                 help="URL 자동수집이 안 되면 발행글 내용을 직접 붙여넣으세요.")

    if st.button("비교 실행", type="primary", disabled=not (approved.strip() and published.strip()), key="cmp_run"):
        _ov = st.empty()
        _ov.markdown(ui.loading_overlay("원고 ↔ 발행물 비교하는 중…"), unsafe_allow_html=True)
        try:
            st.session_state["compare_report"] = compare_engine.compare(approved, published, _refs_from_sheets(sheets))
        finally:
            _ov.empty()

    rep = st.session_state.get("compare_report")
    if rep:
        st.markdown(ui.kpi_cards([
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

        # 제목 대조 — 원고(심의) 제목 vs 발행 제목
        _man_title = st.session_state.get("cmp_sel_title", "")
        _pub_title = st.session_state.get("pub_title", "")
        if _man_title or _pub_title:
            _n = lambda s: (s or "").replace(" ", "").strip()
            _same = bool(_man_title and _pub_title and _n(_man_title) == _n(_pub_title))
            _tone = "#2bb673" if _same else "#f5a623"
            st.markdown(
                f'<div style="border-left:4px solid {_tone};background:#f7f9fc;padding:8px 12px;'
                f'border-radius:6px;margin:6px 0 10px;font-size:12.5px;font-family:Pretendard,sans-serif">'
                f'<b>📌 제목 대조</b> · {"일치" if _same else "확인 필요"}<br>'
                f'<span style="color:#5b6678">📄 원고: {_man_title or "(제목 없음)"}<br>'
                f'📤 발행: {_pub_title or "(수집 안 됨 — URL 자동수집 시 표시)"}</span></div>',
                unsafe_allow_html=True)

        def _blk(color, bg, body):
            st.markdown(f'<div style="border-left:4px solid {color};background:{bg};padding:9px 13px;'
                        f'border-radius:6px;margin-bottom:7px;font-family:Pretendard,sans-serif">{body}</div>',
                        unsafe_allow_html=True)

        # 원고(심의본) 기준 페이지 — 수정 필요한 영역을 원고에서 바로 찾도록
        _pages = (_cmp_pages(up.getvalue(), _PAGES_LOGIC_VER)
                  if (up is not None and up.name.lower().endswith(".docx")) else None)

        def _pg(s):
            p = manuscript_parser.find_page(_pages, s) if _pages else None
            return f' · 원고 약 {p}쪽' if p else ""

        LIMIT = 15
        changed = [c for c in rep["changed_list"] if c["from"].strip() or c["to"].strip()]
        deleted = [d for d in rep["deleted_list"] if d.strip()]
        added = [a for a in rep["added_list"] if a.strip()]
        changed.sort(key=lambda c: c.get("kind") == "spacing")  # 내용변경 먼저, 띄어쓰기 나중
        _sp = sum(1 for c in changed if c.get("kind") == "spacing")
        st.markdown("###### 문장 비교 결과")
        st.caption("🔤 표시는 **띄어쓰기만 다른 항목(내용 동일·참고용)**입니다. 바뀐 공백은 **␣** 기호로 표시돼요."
                   + (f" · 띄어쓰기 차이 {_sp}건" if _sp else ""))
        if _pages:
            st.caption("📄 '원고 약 N쪽'은 **추정값**이에요(이미지·표가 많으면 실제와 몇 쪽 차이날 수 있음). "
                       "정확히 찾으려면 원고에서 해당 **문장을 검색(Ctrl+F)**하세요.")
        if not (changed or deleted or added):
            st.success("원고와 발행본이 문장 단위로 일치합니다.")
        for ch in changed[:LIMIT]:
            _a, _b = ui.diff_pair(ch["from"].strip(), ch["to"].strip())
            _a, _b = (_a or "(빈 문장)"), (_b or "(빈 문장)")
            _loc = _pg(ch["from"])
            if ch.get("kind") == "spacing":
                _blk("#b3bccb", "#f4f6fa",
                     f'<div style="font-size:11px;font-weight:700;color:#7a8597">🔤 띄어쓰기 차이 (내용 동일·참고용){_loc}</div>'
                     f'<div style="font-size:12.5px;color:#5b6678;margin-top:3px">📄 원고: {_a}</div>'
                     f'<div style="font-size:12.5px;color:#5b6678;margin-top:2px">📤 발행: {_b}</div>')
            else:
                _blk("#f5a623", "#fff8ec",
                     f'<div style="font-size:11px;font-weight:700;color:#d98300">✏️ 변경 (바뀐 글자 빨강){_loc}</div>'
                     f'<div style="font-size:12.5px;color:#8a6d3b;margin-top:3px">📄 원고: {_a}</div>'
                     f'<div style="font-size:12.5px;color:#16213d;margin-top:2px">📤 발행: {_b}</div>')
        for d in deleted[:LIMIT]:
            _blk("#e23b3b", "#ffecec",
                 f'<div style="font-size:11px;font-weight:700;color:#e23b3b">🗑️ 원고에만 있음 (발행본서 빠짐){_pg(d)}</div>'
                 f'<div style="font-size:12.5px;color:#16213d;margin-top:2px">{d}</div>')
        for a in added[:LIMIT]:
            _blk("#2bb673", "#eafaf0",
                 '<div style="font-size:11px;font-weight:700;color:#1d9d5f">➕ 발행본에만 있음 (원고엔 없음)</div>'
                 f'<div style="font-size:12.5px;color:#16213d;margin-top:2px">{a}</div>')
        _extra = max(0, len(changed) - LIMIT) + max(0, len(deleted) - LIMIT) + max(0, len(added) - LIMIT)
        if _extra:
            st.caption(f"… 외 {_extra}건 더 있음 (유형별 상위 {LIMIT}건만 표시)")

        # ✉️ 실행사 수정 요청 메일 양식 (복붙용) — 접었다 펼치기
        _blogger = st.session_state.get("cmp_sel_name", "")
        with st.expander(f"✉️ 수정 요청 메일 양식{f' · {_blogger}' if _blogger else ''}  (클릭해서 펼치기)",
                         expanded=False):
            st.caption("발행글을 원고(심의본)에 맞추기 위한 수정 요청입니다. 우측 상단 복사 버튼으로 복사해 실행사에 전달하세요.")
            st.code(compare_engine.revision_request(
                rep, blogger=_blogger,
                approved_title=st.session_state.get("cmp_sel_title", "")), language=None)

    # ===== 발행 링크 트래킹 코드 확인 =====
    st.divider()
    st.markdown(ui.subhead("🔗", "발행 링크 트래킹 코드 확인", "blue"), unsafe_allow_html=True)
    st.caption("위 **발행 URL** 을 넣고 '발행글에서 자동 찾기'를 누르면, 본문 맨 아래 링크(tinyurl 등)를 찾아 "
               "원본까지 따라가 맨 끝 파라미터(utm_term = 매체·캠페인 코드)를 보여줍니다. 자동으로 안 되면 링크를 직접 붙여넣으세요.")

    def _resolve_and_parse(u):
        final = fetcher.resolve_redirects(u) if fetcher.is_shortener(u) else u
        return {"final": final, "found": u, **fetcher.parse_link_params(final)}

    c_auto, c_manual = st.columns([1, 1])
    with c_auto:
        auto = st.button("🔎 발행글에서 자동 찾기", key="cmp_linkauto", disabled=not url.strip())
    link = st.text_input("또는 링크 직접 붙여넣기", key="cmp_link")
    with c_manual:
        manual = st.button("이 링크로 확인", key="cmp_linkparam", disabled=not link.strip())

    if auto:
        _ovl = st.empty()
        _ovl.markdown(ui.loading_overlay("발행글에서 링크 찾는 중…"), unsafe_allow_html=True)
        try:
            cands = fetcher.tracking_link_candidates(fetcher.fetch_naver_links(url))
            result = None
            for u in cands[:6]:
                info = _resolve_and_parse(u)
                if info.get("term"):
                    result = info
                    break
            if result is None:
                result = (_resolve_and_parse(cands[0]) if cands
                          else {"error": "발행글에서 링크를 찾지 못했습니다. 링크를 직접 붙여넣어 주세요."})
            st.session_state["link_info"] = result
        except fetcher.FetchError as e:
            st.session_state["link_info"] = {"error": str(e)}
        finally:
            _ovl.empty()

    if manual:
        _ovl = st.empty()
        _ovl.markdown(ui.loading_overlay("링크 확인하는 중…"), unsafe_allow_html=True)
        try:
            st.session_state["link_info"] = _resolve_and_parse(link.strip())
        except fetcher.FetchError as e:
            st.session_state["link_info"] = {"error": str(e)}
        finally:
            _ovl.empty()

    _li = st.session_state.get("link_info")
    if _li:
        if _li.get("error"):
            st.error(_li["error"])
        elif _li.get("term"):
            st.markdown(ui.kpi_cards([
                {"icon": "🎯", "tone": "blue", "label": f"트래킹 코드 ({_li['key']})",
                 "value": _li["term"], "sub": "링크 맨 끝 파라미터"},
            ]), unsafe_allow_html=True)
            if _li.get("found") and _li["found"] != _li["final"]:
                st.caption(f"🔗 발행글 링크: {_li['found']} → 원본으로 이동")
            with st.expander("링크 전체 파라미터 보기"):
                st.markdown("**최종 URL**")
                st.code(_li["final"], language=None)
                for k, v in _li["params"]:
                    if k in _HIDE_PARAMS:   # 트래킹과 무관한 기능 파라미터는 숨김
                        continue
                    st.markdown(f"- `{k}` = {v}")
        else:
            st.warning("이 링크엔 파라미터(=값)가 없습니다. utm_term 같은 추적 파라미터가 붙은 링크인지 확인해 주세요.")
            st.code(_li.get("final", ""), language=None)

    # ===== 이미지 비교 (순서대로 나란히) =====
    st.divider()
    st.markdown(ui.subhead("🖼️", "이미지 비교 (순서대로)", "blue"), unsafe_allow_html=True)
    st.caption("심의 원고(워드)와 발행글 사진을 같은 순번끼리 나란히 보여줍니다. "
               "발행글의 스티커·이모티콘은 자동 제외해 순번이 밀리지 않습니다. (워드 원고 업로드 + 발행 URL 필요)")
    _img_ready = up is not None and up.name.lower().endswith(".docx") and bool(url.strip())
    if st.button("이미지 비교", key="cmp_img", disabled=not _img_ready):
        _ovi = st.empty()
        _ovi.markdown(ui.loading_overlay("이미지 불러오는 중…"), unsafe_allow_html=True)
        try:
            man = st.session_state.get("cmp_man_images", [])[:25]   # 선택한 블로거 구간 이미지
            pub_urls = fetcher.fetch_naver_images(url)[:25]
            pub = []
            for u in pub_urls:
                try:
                    pub.append(fetcher.fetch_image(u))
                except Exception:
                    pub.append(None)  # 다운로드 실패 → 링크로 대체 표시
            st.session_state["img_cmp"] = {"man": man, "pub": pub, "urls": pub_urls}
        except fetcher.FetchError as e:
            st.session_state["img_cmp"] = {"error": str(e)}
        finally:
            _ovi.empty()

    ic = st.session_state.get("img_cmp")
    if ic:
        if ic.get("error"):
            st.error(ic["error"])
        else:
            n, m = len(ic["man"]), len(ic["pub"])
            st.markdown(ui.kpi_cards([
                {"icon": "📄", "tone": "blue", "label": "심의 원고 이미지", "value": f"{n}장", "sub": "워드 삽입"},
                {"icon": "📤", "tone": "blue", "label": "발행글 이미지", "value": f"{m}장", "sub": "네이버"},
                {"icon": "🔢", "tone": "green" if n == m else "red", "label": "장수 일치",
                 "value": "일치" if n == m else f"{abs(n - m)}장 차이", "sub": "심의 vs 발행"},
            ], per_row=3), unsafe_allow_html=True)
            if n != m:
                st.warning(f"이미지 장수가 다릅니다 (심의 {n}장 · 발행 {m}장). 빠지거나 추가된 이미지가 있는지 아래에서 확인하세요.")
            st.caption("여러 명 원고면 위에서 **선택한 블로거 구간의 이미지**만 비교합니다 (블로거를 바꾸면 다시 눌러주세요).")
            for i in range(max(n, m)):
                c1, c2 = st.columns(2)
                with c1:
                    if i < n:
                        st.image(ic["man"][i], caption=f"심의 {i + 1}", use_container_width=True)
                    else:
                        st.markdown(f"**심의 {i + 1}** — ❌ 없음")
                with c2:
                    if i < m and ic["pub"][i] is not None:
                        st.image(ic["pub"][i], caption=f"발행 {i + 1}", use_container_width=True)
                    elif i < m:
                        st.markdown(f"**발행 {i + 1}** — 이미지 로드 실패 · [원본 열기]({ic['urls'][i]})")
                    else:
                        st.markdown(f"**발행 {i + 1}** — ❌ 없음")
