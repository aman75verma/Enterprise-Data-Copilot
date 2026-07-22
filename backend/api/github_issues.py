import argparse
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GITHUB_API_BASE_URL = "https://api.github.com"
DEFAULT_REPO = "supabase/supabase"


class LiveIssueTrackerError(RuntimeError):
    pass


class LiveIssueTrackerClient:
    def __init__(self, repo: str = DEFAULT_REPO, token: str | None = None):
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")

    @property
    def headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "enterprise-data-copilot",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def list_open_issues(self, per_page: int = 10, labels: str | None = None) -> list[dict[str, Any]]:
        query = f"repo:{self.repo} is:issue state:open"
        if labels:
            query += f" label:{labels}"
        data = self._get("/search/issues", params={"q": query, "sort": "updated", "per_page": per_page})
        return [self._summarize_issue(issue) for issue in data.get("items", [])]

    def get_issue(self, issue_number: int) -> dict[str, Any]:
        issue = self._get(f"/repos/{self.repo}/issues/{issue_number}")
        if "pull_request" in issue:
            raise LiveIssueTrackerError(f"#{issue_number} is a pull request, not an issue")
        return self._summarize_issue(issue, include_body=True)

    def search_issues(self, keyword: str, state: str = "open", per_page: int = 10) -> list[dict[str, Any]]:
        query = f"repo:{self.repo} is:issue {keyword.strip()}"
        if state:
            query += f" state:{state}"
        data = self._get("/search/issues", params={"q": query, "per_page": per_page})
        return [self._summarize_issue(issue) for issue in data.get("items", [])]

    def count_open_issues_by_label(self, label: str) -> int:
        data = self._get(
            "/search/issues",
            params={"q": f"repo:{self.repo} is:issue state:open label:{label}", "per_page": 1},
        )
        return int(data["total_count"])

    def list_labels(self, per_page: int = 100) -> list[str]:
        data = self._get(f"/repos/{self.repo}/labels", params={"per_page": per_page})
        return [label["name"] for label in data]

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{GITHUB_API_BASE_URL}{path}"
        try:
            with httpx.Client(timeout=20) as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            message = exc.response.text[:500]
            raise LiveIssueTrackerError(f"GitHub API returned {exc.response.status_code}: {message}") from exc
        except httpx.HTTPError as exc:
            raise LiveIssueTrackerError(f"GitHub API request failed: {exc}") from exc

    @staticmethod
    def _summarize_issue(issue: dict[str, Any], include_body: bool = False) -> dict[str, Any]:
        summary = {
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "labels": [label["name"] for label in issue.get("labels", [])],
            "url": issue["html_url"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue["comments"],
        }
        if include_body:
            summary["body"] = issue.get("body") or ""
        return summary


def print_issues(issues: list[dict[str, Any]]) -> None:
    for issue in issues:
        labels = ", ".join(issue["labels"]) or "no labels"
        print(f"#{issue['number']} [{issue['state']}] {issue['title']}")
        print(f"  labels: {labels}")
        print(f"  {issue['url']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the live issue tracker for Supabase issues.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    open_parser = subparsers.add_parser("open", help="List recent open issues")
    open_parser.add_argument("--per-page", type=int, default=10)

    search_parser = subparsers.add_parser("search", help="Search open issues by keyword")
    search_parser.add_argument("keyword")
    search_parser.add_argument("--state", default="open")
    search_parser.add_argument("--per-page", type=int, default=10)

    get_parser = subparsers.add_parser("get", help="Fetch one issue by number")
    get_parser.add_argument("issue_number", type=int)

    labels_parser = subparsers.add_parser("labels", help="List repository labels")
    labels_parser.add_argument("--per-page", type=int, default=100)

    count_parser = subparsers.add_parser("count-label", help="Count open issues with a label")
    count_parser.add_argument("label")

    args = parser.parse_args()
    client = LiveIssueTrackerClient()

    if args.command == "open":
        print_issues(client.list_open_issues(per_page=args.per_page))
    elif args.command == "search":
        print_issues(client.search_issues(args.keyword, state=args.state, per_page=args.per_page))
    elif args.command == "get":
        print_issues([client.get_issue(args.issue_number)])
    elif args.command == "labels":
        for label in client.list_labels(per_page=args.per_page):
            print(label)
    elif args.command == "count-label":
        print(client.count_open_issues_by_label(args.label))


if __name__ == "__main__":
    main()
