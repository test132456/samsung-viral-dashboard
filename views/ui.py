"""공통 UI 헬퍼 — 모든 탭 동일 톤(클린 코퍼레이트 / A안).

GLOBAL_CSS 는 app.py·demo_app.py 에서 1회 주입한다.
kpi_cards()/pill()/section() 으로 카드·배지·섹션 헤더를 일관되게 렌더한다.
"""
from __future__ import annotations

GLOBAL_CSS = """
<style>
.vh-wrap{font-family:'Pretendard',-apple-system,'Segoe UI',sans-serif;font-variant-numeric:tabular-nums;}
.vh-sec{font-size:14px;font-weight:800;color:#16213d;margin:6px 0 12px;letter-spacing:-.3px;}
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


def kpi_cards(cards: list[dict]) -> str:
    """cards: [{icon, tone, label, value, sub}]. tone 은 TONE 키."""
    n = max(1, len(cards))
    out = [f'<div class="vh-wrap"><div class="vh-kpis" style="grid-template-columns:repeat({n},1fr)">']
    for c in cards:
        bg, fg = TONE.get(c.get("tone", "gray"), TONE["gray"])
        out.append(
            f'<div class="vh-k"><div class="vh-ic" style="background:{bg};color:{fg}">{c.get("icon","")}</div>'
            f'<div class="vh-lab">{c.get("label","")}</div><div class="vh-num">{c.get("value","")}</div>'
            f'<div class="vh-sub">{c.get("sub","")}</div></div>')
    out.append("</div></div>")
    return "".join(out)


def pill(text: str, kind: str = "wait") -> str:
    return f'<span class="vh-pill {_PILL_KIND.get(kind, "p-wait")}">{text}</span>'


def section(title: str) -> str:
    return f'<div class="vh-wrap"><div class="vh-sec">{title}</div></div>'


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


def checklist_table(items: list[dict]) -> str:
    """items: [{name, status: ok|warn|fail, detail}] → 색상 체크리스트 표 HTML."""
    head = "".join(f"<th>{i['name']}</th>" for i in items)
    cells = "".join(
        f'<td class="chk-{i["status"]}"><div class="sym">{_CHK_SYM.get(i["status"], "-")}</div>'
        f'<div class="det">{i.get("detail", "")}</div></td>' for i in items)
    return f'<div class="vh-wrap"><table class="vh-chk"><tr>{head}</tr><tr>{cells}</tr></table></div>'
