"""시트 탭명·컬럼명·상태값 단일 출처(single source of truth)."""

# --- 시트 탭명 ---
SHEET_SCHEDULE = "schedule"
SHEET_INFLUENCERS = "influencers"
SHEET_REVIEWS = "reviews"
SHEET_QA = "qa_results"
SHEET_COMPARE = "compare_results"
SHEET_BRIEFING = "ai_briefing"
SHEET_REF_BANNED = "ref_banned"
SHEET_REF_REQUIRED = "ref_required"
SHEET_REF_RIDERS = "ref_riders"
SHEET_REF_KEYWORDS = "ref_keywords"
SHEET_CALENDAR = "calendar_events"
SHEET_DISTRIBUTION = "distribution"
SHEET_CITATIONS = "ai_citations"

ALL_SHEETS = [
    SHEET_SCHEDULE, SHEET_INFLUENCERS, SHEET_REVIEWS, SHEET_QA,
    SHEET_COMPARE, SHEET_BRIEFING, SHEET_REF_BANNED, SHEET_REF_REQUIRED,
    SHEET_REF_RIDERS, SHEET_REF_KEYWORDS, SHEET_CALENDAR, SHEET_DISTRIBUTION,
    SHEET_CITATIONS,
]

# --- 컬럼 정의 (탭 생성 시 헤더로 사용) ---
COLS = {
    SHEET_SCHEDULE: ["content_id", "title", "channel", "draft_request_date",
                     "draft_submit_date", "review_submit_date", "review_done_date",
                     "publish_plan_date", "publish_actual_date", "status"],
    SHEET_INFLUENCERS: ["blogger_name", "url", "visitors", "category", "score",
                        "selected", "draft_submitted", "review_done", "published", "publish_url"],
    SHEET_REVIEWS: ["content_id", "title", "review_submit_date", "status",
                    "revision_count", "review_done_date"],
    SHEET_QA: ["content_id", "qa_score", "banned_count", "rider_error_count",
               "missing_phrase", "price_found", "checked_at"],
    SHEET_COMPARE: ["content_id", "match_rate", "changed", "deleted", "added",
                    "notice_ok", "rider_ok", "checked_at"],
    SHEET_BRIEFING: ["date", "keyword", "ai_briefing_exposed", "samsung_exposed", "content_type"],
    SHEET_REF_BANNED: ["term", "note"],
    SHEET_REF_REQUIRED: ["phrase", "type", "note"],
    SHEET_REF_RIDERS: ["official_name", "common_mistakes"],
    SHEET_REF_KEYWORDS: ["keyword", "type"],
    SHEET_CALENDAR: ["date", "task", "track"],
    SHEET_DISTRIBUTION: ["group", "blogger", "publish_date", "approval_no", "landing_url", "note", "publish_url"],
    SHEET_CITATIONS: ["date", "tool", "keyword", "queries", "cited"],
}

# --- 상태값/분류 ---
SCHEDULE_STATUSES = ["예정", "진행중", "완료", "지연"]
REVIEW_STATUSES = ["작성중", "심의접수", "수정요청", "심의완료", "발행완료"]
CHANNELS = ["공식블로그", "배포형"]
CONTENT_TYPES = ["정보형", "비교형", "후기형"]
TRACKS = ["공식", "배포형", ""]
AI_TOOLS = ["ChatGPT", "Gemini", "Perplexity", "Copilot", "Claude"]

# 운영월 드롭다운 범위: 2026-01 ~ 2027-12
MONTHS = [f"{y}-{m:02d}" for y in (2026, 2027) for m in range(1, 13)]
DEFAULT_MONTH = "2026-06"
