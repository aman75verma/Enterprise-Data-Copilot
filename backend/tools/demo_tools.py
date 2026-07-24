import argparse
import json

from backend.tools.docs_tool import search_docs
from backend.tools.issue_tracker_tool import check_issue_tracker
from backend.tools.sql_tool import query_customer_db


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo Enterprise Data Copilot tools without an MCP client.")
    subparsers = parser.add_subparsers(dest="tool", required=True)

    sql_parser = subparsers.add_parser("query_customer_db")
    sql_parser.add_argument("sql_query")

    docs_parser = subparsers.add_parser("search_docs")
    docs_parser.add_argument("query")
    docs_parser.add_argument("--top-k", type=int, default=5)

    issues_parser = subparsers.add_parser("check_issue_tracker")
    issues_parser.add_argument("--keyword")
    issues_parser.add_argument("--issue-number", type=int)

    args = parser.parse_args()

    try:
        if args.tool == "query_customer_db":
            result = query_customer_db(args.sql_query)
        elif args.tool == "search_docs":
            result = search_docs(args.query, top_k=args.top_k)
        else:
            result = check_issue_tracker(keyword=args.keyword, issue_number=args.issue_number)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
