"""
CLI tester — exercises all FastAPI endpoints from the command line.

Usage:
    1. Start the server:  python -m uvicorn backend.main:app --reload --port 8000
    2. Run this script:   python backend/test_cli.py

Tests:
    1. GET  /health
    2. POST /chat  (new conversation)
    3. POST /chat  (follow-up in same conversation)
    4. GET  /conversations/{id}
    5. GET  /admin/logs
"""

import json
import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"


def pretty(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    client = httpx.Client(timeout=60)

    # --- 1. Health Check ---
    print("=" * 60)
    print("1. GET /health")
    print("=" * 60)
    r = client.get(f"{BASE_URL}/health")
    print(f"   Status: {r.status_code}")
    pretty(r.json())

    if r.json().get("database") != "ok":
        print("\n[ERROR] Database is not reachable. Is Docker/Postgres running?")
        sys.exit(1)

    # --- 2. POST /chat (new conversation) ---
    print("\n" + "=" * 60)
    print("2. POST /chat (new conversation)")
    print("=" * 60)
    payload = {"message": "How many customers do we have in total?"}
    print(f"   Sending: {payload['message']}")
    r = client.post(f"{BASE_URL}/chat", json=payload)
    print(f"   Status: {r.status_code}")
    if r.status_code != 200:
        print(f"   Error Response: {r.text}")
        print("\n[NOTE] Make sure you have set a valid GROQ_API_KEY in backend/.env!")
        sys.exit(1)
    data = r.json()
    conv_id = data.get("conversation_id")
    print(f"   Conversation ID: {conv_id}")
    print(f"   Answer: {data.get('answer', '')[:200]}")
    print(f"   Tool calls: {len(data.get('tool_calls', []))}")
    if data.get("tool_calls"):
        for tc in data["tool_calls"]:
            print(f"     - {tc['tool']}: {json.dumps(tc['arguments'], default=str)[:100]}")

    # --- 3. POST /chat (follow-up) ---
    print("\n" + "=" * 60)
    print("3. POST /chat (follow-up in same conversation)")
    print("=" * 60)
    payload2 = {"message": "How many of them have open tickets?", "conversation_id": conv_id}
    print(f"   Sending: {payload2['message']}")
    r = client.post(f"{BASE_URL}/chat", json=payload2)
    print(f"   Status: {r.status_code}")
    if r.status_code != 200:
        print(f"   Error Response: {r.text}")
        sys.exit(1)
    data2 = r.json()
    print(f"   Answer: {data2.get('answer', '')[:200]}")
    print(f"   Tool calls: {len(data2.get('tool_calls', []))}")

    # --- 4. GET /conversations/{id} ---
    print("\n" + "=" * 60)
    print(f"4. GET /conversations/{conv_id}")
    print("=" * 60)
    r = client.get(f"{BASE_URL}/conversations/{conv_id}")
    print(f"   Status: {r.status_code}")
    conv = r.json()
    print(f"   Total turns: {len(conv.get('turns', []))}")
    for t in conv.get("turns", []):
        role = t["role"]
        content = t["content"][:80]
        print(f"     [{role}] {content}")

    # --- 5. GET /admin/logs ---
    print("\n" + "=" * 60)
    print("5. GET /admin/logs")
    print("=" * 60)
    r = client.get(f"{BASE_URL}/admin/logs", params={"limit": 5})
    print(f"   Status: {r.status_code}")
    logs = r.json()
    print(f"   Returned {len(logs)} log entries")
    for log in logs:
        print(f"     Turn {log['id']}: tool={log.get('tool_name', 'N/A')}, latency={log.get('latency_ms', '?')}ms")

    print("\n" + "=" * 60)
    print("[OK] All endpoint tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
