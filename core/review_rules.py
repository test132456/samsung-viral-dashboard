"""심의 지적사항 자동 점검(표현·문구). 전부 순수 함수 — 네트워크/AI 없음.

정확도 등급:
  '정확' = 규칙 기반 결정적 검출(이중공백·최상급 단어)
  '후보' = 문맥 판단이 필요한 휴리스틱(등·단정 인과·특약 병기·제한 누락) → 사람이 최종 확인
각 검사는 [{"hit": 표시어, "context": 주변문맥}] 리스트를 돌려준다.
"""
from __future__ import annotations
import re

# #4 최상급/과장 표현 (문맥 무관 지양) — '가장','제일'은 단어경계로 오탐 방지
_SUPERLATIVES = ["최고", "최상", "최강", "최적", "무조건", "유일", "완벽", "100%"]
_SUP_BOUNDARY = ["가장", "제일"]      # 뒤에 공백이 와야 최상급(가장자리·제일교회 등 제외)

# #1 단정적 인과: 원인 연결어 + 부정적 결과 (예: "음식 섭취로 인해 식중독에 걸렸다")
_CAUSE = r"(?:로 인해|로 인한|때문에|탓에|때문인)"
_OUTCOME = r"(걸렸|걸린|걸립|발병|감염|사망|생겼|생긴|유발|초래|악화|부작용)"

# #5 지급제한 안내 판단용 키워드
_BENEFIT_KW = ["보장", "보상", "지급"]
_LIMIT_KW = ["제한", "면책", "보상하지 않", "보상되지 않", "보상 제외", "지급되지 않",
             "지급하지 않", "지급 제한", "부지급", "감액", "자기부담", "예외", "제외"]


def _ctx(text: str, start: int, end: int, pad: int = 28) -> str:
    s, e = max(0, start - pad), min(len(text), end + pad)
    seg = text[s:e].replace("\n", " ").strip()
    return ("…" if s > 0 else "") + seg + ("…" if e < len(text) else "")


def check_double_space(text: str) -> list[dict]:
    """#6 띄어쓰기 2칸 이상 (정확). 글자 사이에 낀 2+ 공백만."""
    text = text or ""
    out = []
    for m in re.finditer(r"(?<=\S) {2,}(?=\S)", text):
        out.append({"hit": f"공백 {len(m.group())}칸", "context": _ctx(text, m.start(), m.end())})
    return out


def check_superlatives(text: str) -> list[dict]:
    """#4 최상급·단정 표현 (정확)."""
    text = text or ""
    out, seen = [], set()
    for w in _SUPERLATIVES:
        for m in re.finditer(re.escape(w), text):
            key = (w, m.start())
            if key in seen:
                continue
            seen.add(key)
            out.append({"hit": w, "context": _ctx(text, m.start(), m.start() + len(w))})
    for w in _SUP_BOUNDARY:
        for m in re.finditer(re.escape(w) + r"(?=\s)", text):
            out.append({"hit": w, "context": _ctx(text, m.start(), m.start() + len(w))})
    return out


def check_vague_deung(text: str) -> list[dict]:
    """#3 모호·포괄 표현 '등'(후보). ' 등'(앞 공백) + 조사/구두점만 — 평등·등록 등 단어는 제외."""
    text = text or ""
    out = []
    for m in re.finditer(r"(?<=[가-힣]) 등(?=[\s.,)]|을|를|이|가|의|으로|에서|과|와|도|만|$)", text):
        out.append({"hit": "등", "context": _ctx(text, m.start() + 1, m.start() + 2)})
    return out


def check_causal_assertion(text: str) -> list[dict]:
    """#1 단정적 인과 표현(후보). 원인 연결어 + 부정적 결과."""
    text = text or ""
    out = []
    pat = re.compile(r"[^.\n]{0,22}" + _CAUSE + r"[^.\n]{0,22}?" + _OUTCOME + r"[^.\n]{0,3}")
    for m in pat.finditer(text):
        out.append({"hit": "단정적 인과", "context": _ctx(text, m.start(), m.end(), pad=4)})
    return out


def check_rider_naming(text: str, riders: list[str] | None) -> list[dict]:
    """#2 특약명 '특약' 병기(후보). 공식 담보 핵심어가 나오는데 근처(뒤 14자)에 '특약'이 없으면 표시."""
    text = text or ""
    out, seen = [], set()
    for r in riders or []:
        core = re.split(r"[(（]", str(r).replace("특약", ""))[0].strip()
        if len(core) < 3 or core in seen or core not in text:
            continue
        seen.add(core)
        for m in re.finditer(re.escape(core), text):
            # 핵심어 뒤 32자 안에 '특약'이 있으면 정식명 병기로 간주(괄호 부기 담보명 대응)
            around = text[m.start():m.end() + 32]
            if "특약" not in around:
                out.append({"hit": core, "context": _ctx(text, m.start(), m.end())})
                break
    return out


def check_limitation_notice(text: str) -> list[dict]:
    """#5 지급제한 안내 누락(후보, 문서 단위). 보장·지급은 말하는데 제한/면책 안내가 전혀 없으면 표시."""
    text = text or ""
    if any(k in text for k in _BENEFIT_KW) and not any(k in text for k in _LIMIT_KW):
        return [{"hit": "제한사항 안내 없음",
                 "context": "보장·지급 내용은 있으나 지급 제한·면책 안내 문구가 안 보입니다. 누락 여부 확인 필요."}]
    return []


# (규칙키, 아이콘, 제목, 등급, 검사함수) — riders 필요한 건 check_all에서 주입
RULES = [
    ("double_space", "␣", "띄어쓰기 2칸 이상", "정확", check_double_space),
    ("superlative", "⛔", "최상급·단정 표현", "정확", check_superlatives),
    ("deung", "≈", "모호·포괄 표현 ‘등’", "후보", check_vague_deung),
    ("causal", "⚠️", "단정적 인과 표현", "후보", check_causal_assertion),
    ("rider_naming", "📑", "특약명 ‘특약’ 병기", "후보", None),
    ("limitation", "🚧", "지급 제한 안내 누락", "후보", check_limitation_notice),
]


def check_all(text: str, riders: list[str] | None = None) -> list[dict]:
    """전 규칙 실행 → [{key, icon, title, grade, hits:[...]}]. hits 없는 규칙도 포함(통과 표시용)."""
    results = []
    for key, icon, title, grade, fn in RULES:
        if key == "rider_naming":
            hits = check_rider_naming(text, riders)
        else:
            hits = fn(text)
        results.append({"key": key, "icon": icon, "title": title, "grade": grade, "hits": hits})
    return results
