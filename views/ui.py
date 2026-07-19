"""공통 UI 헬퍼 — 모든 탭 동일 톤(클린 코퍼레이트 / A안).

GLOBAL_CSS 는 app.py·demo_app.py 에서 1회 주입한다.
kpi_cards()/pill()/section() 으로 카드·배지·섹션 헤더를 일관되게 렌더한다.
"""
from __future__ import annotations
import difflib
import html
import re

GLOBAL_CSS = """
<style>
.vh-wrap{font-family:'Pretendard',-apple-system,'Segoe UI',sans-serif;font-variant-numeric:tabular-nums;}
.vh-sec{font-size:14px;font-weight:800;color:#16213d;margin:6px 0 12px;letter-spacing:-.3px;}
/* ===== A안: 그라데이션 페이지 헤더 ===== */
.vh-phead{background:linear-gradient(135deg,#0c2f8f,#2f7bea);border-radius:14px;padding:17px 22px;
  margin:2px 0 18px;box-shadow:0 10px 26px rgba(18,50,130,.24);}
.vh-phead h2{font-size:18px;font-weight:800;color:#fff;letter-spacing:-.4px;margin:0;line-height:1.25;}
.vh-phead p{font-size:12px;color:#d3e3ff;margin:5px 0 0;font-weight:600;}
.vh-kpis{display:grid;gap:14px;margin:4px 0 20px;}
.vh-k{background:#fff;border-radius:14px;padding:16px 16px 15px;border:1px solid #eef2f8;
      box-shadow:0 6px 18px rgba(37,99,235,.07);transition:transform .2s,box-shadow .2s;}
.vh-k:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(37,99,235,.13);}
.vh-ic{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;margin-bottom:11px;}
.vh-lab{font-size:11.5px;color:#8a94a6;font-weight:600;letter-spacing:-.2px;}
.vh-num{font-size:30px;font-weight:800;letter-spacing:-1.4px;color:#16213d;margin-top:3px;line-height:1;}
.vh-sub{font-size:11px;margin-top:7px;font-weight:600;color:#9aa4b4;}
.vh-grid2{display:grid;grid-template-columns:1.5fr 1fr;gap:16px;}
.vh-panel{background:#fff;border-radius:14px;padding:18px 20px;border:1px solid #eef2f8;box-shadow:0 6px 18px rgba(20,30,55,.05);}
.vh-panel h3{font-size:13.5px;font-weight:800;color:#16213d;margin:0 0 12px;}
.vh-row{display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;padding:10px 0;border-bottom:1px solid #f2f5f9;}
.vh-row:last-child{border:none;}
.vh-t{font-size:12.5px;font-weight:600;color:#26324a;}
.vh-s{font-size:10.5px;color:#8a94a6;margin-top:2px;}
.vh-pill{font-size:10px;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap;}
.p-prog{background:#e7f0ff;color:#2563eb;}.p-wait{background:#fff4e2;color:#d98300;}
.p-late{background:#ffeaea;color:#e23b3b;}.p-done{background:#e4f7ec;color:#1d9d5f;}
.p-mute{background:#eef1f6;color:#7a8597;}
.vh-dd{font-size:11px;font-weight:800;white-space:nowrap;}
.vh-dd.soon{color:#e23b3b;}.vh-dd.ok{color:#9aa4b4;}
.vh-empty{font-size:12px;color:#9aa4b4;padding:14px 0;}
.vh-ring{width:92px;height:92px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:4px auto 12px;}
.vh-ring i{width:70px;height:70px;border-radius:50%;background:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;font-style:normal;}
.vh-ring b{font-size:24px;font-weight:800;color:#16213d;}.vh-ring span{font-size:9px;color:#9aa4b4;}
.vh-qrow{display:flex;justify-content:space-between;font-size:12px;padding:6px 0;color:#5b6678;}.vh-qrow b{color:#16213d;}
.vh-chk{width:100%;border-collapse:collapse;table-layout:fixed;margin:6px 0;}
.vh-chk th{background:#2c3e74;color:#fff;font-size:11.5px;font-weight:700;padding:9px 6px;border:2px solid #fff;text-align:center;line-height:1.3;}
.vh-chk td{padding:12px 6px;border:2px solid #fff;text-align:center;vertical-align:middle;}
.vh-chk .sym{font-size:20px;font-weight:800;line-height:1;}
.vh-chk .det{font-size:10px;margin-top:5px;line-height:1.25;}
.chk-ok{background:#d8f3e3;} .chk-warn{background:#fff3cd;} .chk-fail{background:#fbdada;} .chk-pending{background:#f1f3f7;} .chk-na{background:#eef1f6;}
.chk-ok .sym,.chk-ok .det{color:#1d7a4c;} .chk-warn .sym,.chk-warn .det{color:#b9760a;} .chk-fail .sym,.chk-fail .det{color:#c23636;}
.chk-pending .sym,.chk-pending .det{color:#9aa4b4;} .chk-na .sym,.chk-na .det{color:#9aa4b4;}
/* ===== 상세 섹션(A안): 헤더·칩·근거 행 ===== */
.vh-shd{display:flex;align-items:center;gap:9px;margin:20px 0 11px;}
.vh-shd-ic{width:27px;height:27px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;}
.vh-shd-t{font-size:14px;font-weight:800;color:#16213d;letter-spacing:-.3px;}
.vh-shd-s{margin-left:auto;font-size:11.5px;font-weight:800;border-radius:20px;padding:4px 12px;}
.vh-glabel{font-size:12px;font-weight:800;color:#2c3e74;margin:14px 0 5px;padding-left:9px;border-left:3px solid #2f7bea;}
.vh-sum{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;font-weight:800;border-radius:10px;padding:8px 14px;margin-bottom:10px;}
.vh-sum.ok{color:#1d7a4c;background:#e4f7ec;border:1px solid #bfe9d0;}
.vh-sum.bad{color:#fff;background:#e23b3b;box-shadow:0 5px 14px rgba(226,59,59,.32);}
.vh-chips{display:flex;flex-wrap:wrap;gap:7px;}
.vh-cp{font-size:11.5px;color:#5f8a72;background:#f1f7f3;border:1px solid #dfece5;border-radius:20px;padding:4px 11px;}
.vh-cf{font-size:11.5px;font-weight:800;color:#fff;background:#e23b3b;border-radius:20px;padding:5px 12px;box-shadow:0 4px 11px rgba(226,59,59,.3);}
.vh-cwarn{font-size:11.5px;font-weight:800;color:#8a5a00;background:#ffe7b3;border:1px solid #f3d08a;border-radius:20px;padding:4px 11px;}
.vh-ev{background:#fff;border:1px solid #eef2f8;border-left:4px solid #cbd5e6;border-radius:10px;padding:11px 14px;margin:8px 0;box-shadow:0 4px 12px rgba(20,30,55,.05);}
.vh-ev-top{display:flex;align-items:center;gap:10px;}
.vh-ev-dot{width:22px;height:22px;border-radius:50%;color:#fff;font-weight:800;font-size:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0;}
.vh-ev-name{font-size:13px;font-weight:800;color:#16213d;flex:1;min-width:0;}
.vh-ev-badge{font-size:10.5px;font-weight:800;border-radius:20px;padding:3px 11px;white-space:nowrap;}
.vh-ev-d{font-size:11px;color:#6b7688;font-weight:600;margin:5px 0 0 32px;}
.vh-ev-q{font-size:11.5px;color:#3e4c66;background:#f6f8fc;border-left:3px solid #c3d0e6;border-radius:0 7px 7px 0;padding:7px 11px;margin:7px 0 0 32px;line-height:1.55;}
/* ===== 사이드바 모던 내비 (A안) ===== */
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:4px;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label{
  display:flex;align-items:center;width:100%;padding:10px 12px;border-radius:10px;
  margin:0;cursor:pointer;position:relative;transition:background .15s;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover{background:#f4f7fc;}
section[data-testid="stSidebar"] div[role="radiogroup"] input{position:absolute;opacity:0;width:0;height:0;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child:not(:has(p)){display:none !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] label p{font-size:13.5px !important;font-weight:600;color:#5b6678;margin:0;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked){background:#e7f0ff;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p{color:#1f5fd0;font-weight:700 !important;}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked)::before{
  content:"";position:absolute;left:0;top:8px;bottom:8px;width:3px;border-radius:3px;background:#2563eb;}
.vh-brand{display:flex;align-items:center;gap:10px;padding:2px 2px 14px;}
.vh-logo{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#0c4da2,#2f7bea);
  color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;}
.vh-bt{font-size:12.5px;font-weight:800;line-height:1.2;color:#16213d;}
.vh-bs{font-size:9.5px;color:#9aa4b4;}
.vh-mlabel{font-size:10px;font-weight:800;letter-spacing:1.2px;color:#aab3c2;padding:2px 4px 4px;}
/* ===== 로딩 오버레이 (화면 중앙 · 쿠키 굽기) ===== */
.vh-ovl{position:fixed;inset:0;z-index:2147483000;display:flex;flex-direction:column;gap:16px;
  align-items:center;justify-content:center;background:rgba(247,249,253,.86);backdrop-filter:blur(3px);}
.vh-ovl-cake{position:relative;width:84px;height:84px;}
.vh-ovl-cake span{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-size:64px;line-height:1;opacity:0;filter:drop-shadow(0 9px 15px rgba(180,120,40,.28));
  animation:vhsweet 3.6s ease-in-out infinite;}
.vh-ovl-cake span:nth-child(2){animation-delay:.9s;}
.vh-ovl-cake span:nth-child(3){animation-delay:1.8s;}
.vh-ovl-cake span:nth-child(4){animation-delay:2.7s;}
@keyframes vhsweet{
  0%,4%{opacity:0;transform:translateY(13px) scale(.78) rotate(-9deg);}
  10%,20%{opacity:1;transform:translateY(-6px) scale(1.06) rotate(7deg);}
  26%,100%{opacity:0;transform:translateY(-15px) scale(.85) rotate(0);}}
.vh-ovl-msg{font-size:15px;font-weight:800;color:#2c3e74;letter-spacing:-.2px;}
.vh-ovl-dots{display:flex;gap:7px;}
.vh-ovl-dots i{width:9px;height:9px;border-radius:50%;background:#2f7bea;display:inline-block;animation:vhdot .9s ease-in-out infinite;}
.vh-ovl-dots i:nth-child(2){animation-delay:.15s;}
.vh-ovl-dots i:nth-child(3){animation-delay:.3s;}
@keyframes vhdot{0%,100%{opacity:.25;transform:translateY(0);}50%{opacity:1;transform:translateY(-6px);}}
</style>
"""

# 팔레트 (아이콘 배경/글자색)
TONE = {
    "blue": ("#e7f0ff", "#2563eb"),
    "amber": ("#fff4e2", "#d98300"),
    "violet": ("#efe9ff", "#6b46c9"),
    "green": ("#e4f7ec", "#1d9d5f"),
    "red": ("#ffeaea", "#e23b3b"),
    "gray": ("#eef1f6", "#7a8597"),
}

_PILL_KIND = {"prog": "p-prog", "wait": "p-wait", "late": "p-late", "done": "p-done", "mute": "p-mute"}


def kpi_cards(cards: list[dict], per_row: int | None = None) -> str:
    """cards: [{icon, tone, label, value, sub}]. tone 은 TONE 키.
    per_row 지정 시 한 줄에 그 개수만큼 두고 나머지는 다음 줄로 자동 줄바꿈."""
    n = per_row or max(1, len(cards))
    out = [f'<div class="vh-wrap"><div class="vh-kpis" style="grid-template-columns:repeat({n},1fr)">']
    for c in cards:
        tone = c.get("tone", "gray")
        bg, fg = TONE.get(tone, TONE["gray"])
        num_color = fg if tone in ("red", "amber") else "#16213d"  # 경고/위험만 숫자 강조
        out.append(
            f'<div class="vh-k" style="border-top:4px solid {fg}">'
            f'<div class="vh-ic" style="background:{bg};color:{fg}">{c.get("icon","")}</div>'
            f'<div class="vh-lab">{c.get("label","")}</div>'
            f'<div class="vh-num" style="color:{num_color}">{c.get("value","")}</div>'
            f'<div class="vh-sub">{c.get("sub","")}</div></div>')
    out.append("</div></div>")
    return "".join(out)


def pill(text: str, kind: str = "wait") -> str:
    return f'<span class="vh-pill {_PILL_KIND.get(kind, "p-wait")}">{text}</span>'


def section(title: str) -> str:
    return f'<div class="vh-wrap"><div class="vh-sec">{title}</div></div>'


def page_header(title: str, subtitle: str = "") -> str:
    """A안 그라데이션 페이지 헤더."""
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    return f'<div class="vh-wrap"><div class="vh-phead"><h2>{title}</h2>{sub}</div></div>'


def subhead(icon: str, title: str, tone: str = "blue", stat: str = "") -> str:
    """상세 섹션 헤더 — 아이콘 칩 + 제목 + (우측) 요약 배지."""
    bg, fg = TONE.get(tone, TONE["blue"])
    s = f'<span class="vh-shd-s" style="background:{bg};color:{fg}">{stat}</span>' if stat else ""
    return (f'<div class="vh-wrap"><div class="vh-shd">'
            f'<span class="vh-shd-ic" style="background:{bg};color:{fg}">{icon}</span>'
            f'<span class="vh-shd-t">{title}</span>{s}</div></div>')


def group_label(text: str) -> str:
    return f'<div class="vh-wrap"><div class="vh-glabel">{text}</div></div>'


def _mark_ws(seg: str) -> str:
    """바뀐 구간 안의 공백을 눈에 보이는 기호(␣)로 치환 — 띄어쓰기 차이가 보이게."""
    return seg.replace(" ", "␣").replace("\t", "␣")


def diff_pair(old: str, new: str) -> tuple[str, str]:
    """문자 단위 비교 → (원고 HTML, 발행 HTML). 달라진 글자만 강조.
    원고: 원본 글자를 연빨강 취소선, 발행: 바뀐 글자를 빨강 하이라이트.
    바뀐 부분이 공백이면 ␣ 기호로 보이게 표시한다."""
    old, new = old or "", new or ""
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    a, b = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        ta, tb = html.escape(old[i1:i2]), html.escape(new[j1:j2])
        if tag == "equal":
            a.append(ta)
            b.append(tb)
            continue
        if ta:
            a.append(f'<span style="background:#ffe3e3;color:#c23636;text-decoration:line-through;'
                     f'border-radius:3px;padding:0 2px">{_mark_ws(ta)}</span>')
        if tb:
            b.append(f'<span style="background:#ffd6d6;color:#b3231f;font-weight:800;'
                     f'border-radius:3px;padding:0 2px">{_mark_ws(tb)}</span>')
    return "".join(a), "".join(b)


def loading_overlay(msg: str = "굽는 중…") -> str:
    """화면 중앙 로딩 오버레이 HTML — 디저트(쿠키·케이크·컵케이크·도넛)가 번갈아 등장.
    st.empty() 자리표시자에 넣고 끝나면 empty()."""
    sweets = "".join(f"<span>{e}</span>" for e in ("🍪", "🍰", "🧁", "🍩"))
    return ('<div class="vh-wrap"><div class="vh-ovl">'
            f'<div class="vh-ovl-cake">{sweets}</div>'
            '<div class="vh-ovl-dots"><i></i><i></i><i></i></div>'
            f'<div class="vh-ovl-msg">{msg}</div></div></div>')


_CHK_SYM = {"ok": "✓", "warn": "△", "fail": "✕", "pending": "–", "na": "—"}


def deleted_html(deleted: list[str], limit: int = 15) -> str:
    """워드에서 삭제 표시(취소선)된 문장을 취소선 스타일로 렌더 (검수 제외 안내)."""
    if not deleted:
        return ""
    rows = "".join(
        f'<div style="text-decoration:line-through;color:#c23636;font-size:12.5px;margin:3px 0">{d}</div>'
        for d in deleted[:limit])
    extra = (f'<div style="font-size:11px;color:#9aa4b4;margin-top:3px">…외 {len(deleted) - limit}군데</div>'
             if len(deleted) > limit else "")
    return (f'<div class="vh-wrap"><div style="background:#fff5f5;border:1px solid #f3d0d0;'
            f'border-radius:10px;padding:10px 14px;margin:6px 0">'
            f'<div style="font-size:12px;font-weight:700;color:#c23636;margin-bottom:5px">'
            f'🗑️ 삭제 표시된 부분 {len(deleted)}군데 — 본문 검수에서 제외됨</div>{rows}{extra}</div></div>')


def _sum_pill(ok: bool, text: str) -> str:
    return f'<div class="vh-sum {"ok" if ok else "bad"}">{"✓" if ok else "✕"} {text}</div>'


def banned_detail(banned: list[str], manuscript: str, page_of=None) -> str:
    """가이드 표현불가문구 전체를 원고와 대조 — 사용은 강한 빨강(✕), 미사용은 조용한 초록(✓).
    page_of(term)→'쪽' 문자열을 넘기면 사용된 표현에 원고 쪽수를 붙인다."""
    if not banned:
        return ""
    ms = manuscript or ""
    used = [b for b in banned if b in ms]
    summary = _sum_pill(not used,
                        f"표현불가 {len(banned)}개 모두 미사용 · 통과" if not used
                        else f"{len(used)}건 사용 · 수정 필요")
    chips = ""
    for b in banned:
        if b in ms:
            chips += f'<span class="vh-cf">✕ {b}{page_of(b) if page_of else ""}</span>'
        else:
            chips += f'<span class="vh-cp">✓ {b}</span>'
    return f'<div class="vh-wrap">{summary}<div class="vh-chips">{chips}</div></div>'


def rider_detail(rv: dict, ref_total: int, page_of=None) -> str:
    """특약명 대조 — 정확표기는 조용한 초록(✓), 오기 의심은 강한 빨강(✕)."""
    ok = rv.get("ok", [])
    mism = rv.get("mismatch", [])
    unused = rv.get("unused", [])
    if not (ok or mism):
        return ('<div class="vh-wrap"><div class="vh-sum ok" style="color:#7a8597;background:#eef1f6;border-color:#dfe4ee">'
                f'· 기준 특약명 {ref_total}개 — 원고에서 언급된 특약 없음</div></div>')
    summary = _sum_pill(not mism,
                        f"기준 {ref_total}개 중 {len(ok)}개 정식명 정확" if not mism
                        else f"{len(mism)}건 오기 의심 · 정식명 확인 필요")
    chips = "".join(f'<span class="vh-cp">✓ {n}</span>' for n in ok)
    for n in mism:
        pagestr = page_of(re.split(r"[(（]", n)[0].strip()) if page_of else ""
        chips += f'<span class="vh-cf">✕ {n} (정식명 확인){pagestr}</span>'
    tail = f'<div style="font-size:10.5px;color:#9aa4b4;margin-top:7px">그 외 {len(unused)}개 미언급</div>' if unused else ""
    return f'<div class="vh-wrap">{summary}<div class="vh-chips">{chips}</div>{tail}</div>'


def typo_detail(typos: list[dict], page_of=None) -> str:
    """오탈자 목록 — [문맥 전체(오타 빨강 강조)] ▸ [오타]→[수정] · 몇 곳·원고 쪽수."""
    if not typos:
        return ""
    rows = []
    for t in typos:
        loc = page_of(t["as_is"]) if page_of else ""
        bad = html.escape(t["as_is"])
        ctx = html.escape(t.get("context", "")).replace(
            bad, f'<span style="color:#c23636;font-weight:800;background:#ffdada;'
                 f'border-radius:3px;padding:0 2px">{bad}</span>')
        rows.append(
            '<div style="padding:10px 13px;margin:6px 0;background:#fff5f5;border-left:4px solid #e23b3b;border-radius:9px">'
            f'<div style="font-size:12.5px;color:#40506b;line-height:1.55">{ctx}</div>'
            '<div style="font-size:13px;font-weight:800;margin-top:6px">'
            '<span style="color:#2563eb">▸</span> '
            f'<span style="color:#c23636;text-decoration:line-through">{bad}</span>'
            ' → '
            f'<span style="color:#1d7a4c">{html.escape(t["to_be"])}</span>'
            f'<span style="font-size:11px;color:#8a94a6;font-weight:600"> · {t.get("count", 1)}곳{loc}</span>'
            '</div></div>')
    return f'<div class="vh-wrap">{"".join(rows)}</div>'


def required_detail(items: list[dict]) -> str:
    """필수문구 항목별 포함/누락을 정확히 나열. items: [{type, variants, present, phrase}]."""
    if not items:
        return ""
    rows = []
    for it in items:
        label = it.get("type") or (it["variants"][0] if it.get("variants") else it.get("phrase", ""))
        need = " / ".join(it.get("variants") or []) or it.get("phrase", "")
        if it.get("present"):
            rows.append(
                '<div style="display:flex;gap:8px;align-items:baseline;padding:8px 12px;margin:5px 0;'
                'background:#eafaf0;border:1px solid #cdeede;border-radius:9px">'
                '<span style="color:#1d9d5f;font-weight:800">✓</span>'
                f'<span style="font-size:12.5px;color:#16213d"><b>{label}</b> — 원고에 포함됨</span></div>')
        else:
            rows.append(
                '<div style="display:flex;gap:8px;align-items:baseline;padding:8px 12px;margin:5px 0;'
                'background:#ffecec;border:1px solid #f3caca;border-radius:9px">'
                '<span style="color:#e23b3b;font-weight:800">✕</span>'
                f'<span style="font-size:12.5px;color:#16213d"><b>{label}</b> — 누락 · 다음 중 하나 필요: '
                f'<span style="color:#c23636;font-weight:600">{need}</span></span></div>')
    return f'<div class="vh-wrap">{"".join(rows)}</div>'


_FLOW_C = {"ok": ("#1d9d5f", "#eafaf0", "✓"), "warn": ("#b9760a", "#fff8e6", "△"),
           "fail": ("#c23636", "#ffecec", "✕"), "pending": ("#9aa4b4", "#f4f6fa", "–"),
           "na": ("#9aa4b4", "#eef1f6", "—")}


def flow_checklist(items: list[dict]) -> str:
    """가이드 원고 작성 플로우를 세로 스텝으로 렌더 (번호·상태·설명)."""
    rows = []
    for idx, it in enumerate(items, 1):
        fg, bg, sym = _FLOW_C.get(it.get("status", "pending"), _FLOW_C["pending"])
        rows.append(
            f'<div style="display:flex;align-items:center;gap:12px;padding:9px 14px;margin:6px 0;'
            f'background:{bg};border-left:4px solid {fg};border-radius:9px">'
            f'<div style="width:22px;height:22px;border-radius:50%;background:{fg};color:#fff;font-weight:800;'
            f'font-size:12px;display:flex;align-items:center;justify-content:center;flex-shrink:0">{sym}</div>'
            f'<div style="flex:1;min-width:0"><div style="font-size:13px;font-weight:700;color:#16213d">'
            f'{idx}. {it["name"]}</div>'
            f'<div style="font-size:11.5px;color:#6b7688;margin-top:1px">{it.get("detail", "")}</div></div></div>')
    return f'<div class="vh-wrap">{"".join(rows)}</div>'


_BADGE = {"ok": "충족", "warn": "확인", "fail": "미충족", "na": "해당없음", "pending": "대기"}


def evidence_checklist(items: list[dict]) -> str:
    """항목별 상태 + 원고 근거 — 흰 카드 + 좌측 컬러바 + 상태 배지 + 인용 박스."""
    rows = []
    for it in items:
        status = it.get("status", "pending")
        fg, bg, sym = _FLOW_C.get(status, _FLOW_C["pending"])
        ev = it.get("evidence", "")
        detail = it.get("detail", "")
        d_html = f'<div class="vh-ev-d">{detail}</div>' if detail else ""
        q_html = f'<div class="vh-ev-q">원고: “{ev}”</div>' if ev else ""
        rows.append(
            f'<div class="vh-ev" style="border-left-color:{fg}">'
            f'<div class="vh-ev-top">'
            f'<span class="vh-ev-dot" style="background:{fg}">{sym}</span>'
            f'<span class="vh-ev-name">{it["name"]}</span>'
            f'<span class="vh-ev-badge" style="background:{bg};color:{fg}">{_BADGE.get(status, "")}</span>'
            f'</div>{d_html}{q_html}</div>')
    return f'<div class="vh-wrap">{"".join(rows)}</div>'


def checklist_table(items: list[dict]) -> str:
    """items: [{name, status: ok|warn|fail, detail}] → 색상 체크리스트 표 HTML."""
    head = "".join(f"<th>{i['name']}</th>" for i in items)
    cells = "".join(
        f'<td class="chk-{i["status"]}"><div class="sym">{_CHK_SYM.get(i["status"], "-")}</div>'
        f'<div class="det">{i.get("detail", "")}</div></td>' for i in items)
    return f'<div class="vh-wrap"><table class="vh-chk"><tr>{head}</tr><tr>{cells}</tr></table></div>'
