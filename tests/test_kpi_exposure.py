from core import kpi


def test_citation_summary_rates():
    rows = [
        {"date": "2026-06-01", "tool": "ChatGPT", "queries": "10", "cited": "4"},
        {"date": "2026-06-02", "tool": "ChatGPT", "queries": "10", "cited": "6"},
        {"date": "2026-06-01", "tool": "Gemini", "queries": "20", "cited": "5"},
        {"date": "2026-05-30", "tool": "Gemini", "queries": "100", "cited": "99"},  # 다른 달 → 제외
    ]
    out = kpi.citation_summary(rows, "2026-06")
    assert out["by_tool"]["ChatGPT"] == 50.0      # 10/20
    assert out["by_tool"]["Gemini"] == 25.0       # 5/20
    assert out["total_queries"] == 40
    assert out["total_cited"] == 15
    assert out["overall_rate"] == 37.5


def test_citation_summary_handles_zero_and_blank():
    rows = [{"date": "2026-06-01", "tool": "", "queries": "5", "cited": "1"},
            {"date": "2026-06-01", "tool": "Copilot", "queries": "0", "cited": "0"}]
    out = kpi.citation_summary(rows, "2026-06")
    assert "" not in out["by_tool"]               # 빈 tool 제외
    assert out["by_tool"]["Copilot"] == 0.0       # 0 질의 → 0%, no crash


def test_briefing_daily_counts():
    rows = [{"date": "2026-06-01", "ai_briefing_exposed": "Y"},
            {"date": "2026-06-01", "ai_briefing_exposed": "Y"},
            {"date": "2026-06-03", "ai_briefing_exposed": "Y"},
            {"date": "2026-06-03", "ai_briefing_exposed": "N"},
            {"date": "2026-05-01", "ai_briefing_exposed": "Y"}]
    out = kpi.briefing_daily(rows, "2026-06")
    assert out == {"2026-06-01": 2, "2026-06-03": 1}
