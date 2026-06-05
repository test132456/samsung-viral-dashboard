"""월별 바이럴 운영 초안 일정 자동 생성 (6월 실제 운영 패턴 기반 템플릿).

month_drafts(year, month) -> [{date, task, track}]  : 해당 월의 표준 워크플로 일정
generate(months) -> [...]                           : 여러 달 한꺼번에
'({m}월)'=이번달, '({n}월)'=다음달 작업을 의미한다 (예: 6월에 7월 콘텐츠 준비).
"""
from __future__ import annotations
import calendar as _cal

# (일, 작업 템플릿, 트랙) — 6월 캘린더 패턴을 그대로 옮긴 표준 사이클
_TEMPLATE = [
    (1,  "배포형 모집 ({n}월)", "배포형"),
    (5,  "공식 업로드 ({m}월) - 1건", "공식"),
    (8,  "바이럴 방향성 확정 ({n}월)", ""),
    (8,  "배포형 작성 ({n}월)", "배포형"),
    (8,  "공식 작성 ({n}월)", "공식"),
    (11, "배포형 배포 ({m}월) - 2건", "배포형"),
    (12, "배포형 심의, 수정 ({n}월)", "배포형"),
    (12, "공식 심의, 수정 ({n}월)", "공식"),
    (15, "배포형 심의, 수정 ({n}월)", "배포형"),
    (15, "공식 심의, 수정 ({n}월)", "공식"),
    (17, "배포형 배포 ({m}월) - 2건", "배포형"),
    (22, "배포형 배포 ({m}월) - 2건", "배포형"),
    (24, "공식 업로드 ({m}월) - 1건", "공식"),
    (24, "배포형 심의 완료 ({n}월)", "배포형"),
    (24, "공식 심의 완료 ({n}월)", "공식"),
    (25, "배포형 배포 ({m}월) - 2건", "배포형"),
    (30, "배포형 배포 ({m}월) - 2건", "배포형"),
]


def month_drafts(year: int, month: int) -> list[dict]:
    last = _cal.monthrange(year, month)[1]
    n_label = month + 1 if month < 12 else 1
    out = []
    for day, tmpl, track in _TEMPLATE:
        d = min(day, last)
        out.append({
            "date": f"{year:04d}-{month:02d}-{d:02d}",
            "task": tmpl.format(m=month, n=n_label),
            "track": track,
        })
    return out


def generate(months: list[str]) -> list[dict]:
    """months: ['2026-07', ...] → 모든 달의 초안 이벤트 합본."""
    out = []
    for ym in months:
        out.extend(month_drafts(int(ym[:4]), int(ym[5:7])))
    return out
