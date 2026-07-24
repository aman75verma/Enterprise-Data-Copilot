from typing import Any

from backend.api.github_issues import LiveIssueTrackerClient


def check_issue_tracker(keyword: str | None = None, issue_number: int | None = None) -> dict[str, Any]:
    client = LiveIssueTrackerClient()

    if issue_number is not None:
        return {"mode": "issue_number", "result": client.get_issue(issue_number)}

    if not keyword or not keyword.strip():
        raise ValueError("Provide either keyword or issue_number")

    return {
        "mode": "keyword",
        "results": client.search_issues(keyword=keyword, state="open", per_page=5),
    }
