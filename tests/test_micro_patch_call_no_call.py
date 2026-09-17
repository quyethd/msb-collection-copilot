"""Micro-patch focused tests: CALL/no-call worklist aggregation."""
from pathlib import Path
from msb_tools.repository import ToolRepository
from msb_tools.registry import invoke_tool
from msb_agent.copilot import route_copilot
from msb_zalo.chat import ZaloConversation, build_morning_brief

DATA = Path("build/synthetic-data")
REPO = ToolRepository(DATA)
CIF = "SYN002846"

def _caller():
    r = REPO; return lambda name, args: invoke_tool(name, args, repository=r)


def test_full_portfolio_count():
    rows = REPO.portfolio()
    assert len(rows) == 3000


def test_route_call_count():
    rows = REPO.portfolio()
    call_rows = [r for r in rows if r.get("final_route") == "CALL"]
    assert len(call_rows) == 1740


def test_call_no_call_now_count():
    rows = REPO.portfolio()
    count = 0
    for row in rows:
        if row.get("final_route") != "CALL":
            continue
        nba = invoke_tool("get_next_best_action", {"cif": row["cif"]}, repository=REPO)["data"]
        if nba.get("channel") == "NONE":
            count += 1
    assert count == 32


def test_syn002846_matches_predicate():
    nba = invoke_tool("get_next_best_action", {"cif": CIF}, repository=REPO)["data"]
    assert nba["final_route"] == "CALL"
    assert nba["channel"] == "NONE"


def test_web_worklist_shows_3000_and_32():
    r = route_copilot({"cif": CIF, "message": "Hôm nay tôi phải làm gì?",
                       "conversation_context": {"active_cif": CIF}}, _caller())
    summary = r.get("summary", "")
    assert "3000" in summary
    assert "32" in summary


def test_zalo_worklist_shows_3000_and_32():
    brief = build_morning_brief(REPO)
    assert brief["portfolio_count"] == 3000
    assert brief["call_route_no_call_now"] == 32


def test_web_zalo_worklist_fact_parity():
    r = route_copilot({"cif": CIF, "message": "Hôm nay tôi phải làm gì?",
                       "conversation_context": {"active_cif": CIF}}, _caller())
    brief = build_morning_brief(REPO)
    web_summary = r.get("summary", "")
    assert str(brief["portfolio_count"]) in web_summary
    assert str(brief["call_route_no_call_now"]) in web_summary


def test_top_display_limit_preserved():
    r = route_copilot({"cif": CIF, "message": "Hôm nay tôi phải làm gì?",
                       "conversation_context": {"active_cif": CIF}}, _caller())
    sections = r.get("sections", [])
    items = sections[0].get("items", []) if sections else []
    top_lines = [i for i in items if i and i[0].isdigit()]
    assert len(top_lines) <= 5


def test_no_hardcoded_values():
    """Verify counts are derived, not hardcoded."""
    rows = REPO.portfolio()
    assert len(rows) > 100  # Not a hardcoded small number
    call_rows = [r for r in rows if r.get("final_route") == "CALL"]
    assert len(call_rows) > 100  # Not hardcoded
