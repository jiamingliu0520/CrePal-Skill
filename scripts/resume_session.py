#!/usr/bin/env python3
"""
resume_session.py — Resume a paused Crepal session after balance top-up.

Usage:
  python scripts/resume_session.py <base_url> <api_key> <session_id>

Outputs JSON result to stdout on success.
Exit codes:
  0 - success
  1 - error
"""

import sys
import json
import urllib.request
import urllib.error


def resume_session(base_url: str, api_key: str, session_id: str) -> dict:
    url = f"{base_url.rstrip('/')}/api/session/resume"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps({"sessionId": session_id, "apiKey": api_key}).encode("utf-8")

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
    if code != 0:
        print(f"API error (code={code}): {json.dumps(res, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    return res.get("data", {})


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python resume_session.py <base_url> <api_key> <session_id>", file=sys.stderr)
        sys.exit(1)

    result = resume_session(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, ensure_ascii=False))
