"""Claude API 래퍼 — QA 2차 문맥 검수."""
from __future__ import annotations
import json
import anthropic

# 모델명: 배포 시 최신 모델 ID로 확인
_HAIKU = "claude-haiku-4-5"
_SONNET = "claude-sonnet-4-5"

_PROMPT = """당신은 보험 광고 심의 검수자입니다. 아래 심의 가이드를 기준으로,
규칙 기반 검사가 놓칠 수 있는 '과장·단정·우회 표현 또는 맥락상 오인 소지'만 찾으세요.
이미 명백한 금지단어는 별도 처리되므로 제외합니다.

[심의 가이드]
{guide}

[원고]
{text}

JSON 배열로만 답하세요. 각 항목: {{"snippet": "문제 문장", "reason": "사유", "suggestion": "수정안"}}
문제 없으면 []"""


class ClaudeClient:
    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)

    def judge_expressions(self, text: str, guide: str, hard: bool = False) -> list[dict]:
        model = _SONNET if hard else _HAIKU
        msg = self._client.messages.create(
            model=model, max_tokens=1500,
            messages=[{"role": "user",
                       "content": _PROMPT.format(guide=guide[:4000], text=text[:6000])}],
        )
        raw = msg.content[0].text.strip()
        try:
            start, end = raw.find("["), raw.rfind("]")
            return json.loads(raw[start:end + 1]) if start >= 0 else []
        except (json.JSONDecodeError, ValueError):
            return []
