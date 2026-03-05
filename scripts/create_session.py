#!/usr/bin/env python3
"""
create_session.py — Create a new Crepal AI Video Agent session.

Usage:
  python scripts/create_session.py <base_url> <api_key> <query>

Outputs session_id to stdout on success.
Exit codes:
  0 - success
  1 - general error
  2 - insufficient balance (paymentUrl printed to stderr)
"""

import sys
import json
import urllib.request
import urllib.error


def create_session(base_url: str, api_key: str, query: str) -> dict:
    url = f"{base_url.rstrip('/')}/api/session/create"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps({"query": query, "apiKey": api_key}).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    code = res.get("code", -1)
    data = res.get("data", {})

    if data.get("insufficientBalance"):
        payment_url = data.get("paymentUrl", "")
        print(f"INSUFFICIENT_BALANCE|{payment_url}", file=sys.stderr)
        sys.exit(2)

    if code != 0:
        print(f"API error (code={code}): {json.dumps(res, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    session_id = data.get("sessionId", "")
    if not session_id:
        print(f"No sessionId in response: {json.dumps(res, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    return {"sessionId": session_id}


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_session.py <base_url> <api_key> <query>", file=sys.stderr)
        sys.exit(1)

    result = create_session(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, ensure_ascii=False))
