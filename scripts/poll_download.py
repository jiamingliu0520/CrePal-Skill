#!/usr/bin/env python3
"""
poll_download.py — Poll Crepal download/compose task until completion.

Usage (foreground, agent captures stdout):
    python3 poll_download.py "https://crepal.ai" "<TOKEN>" "<DOWNLOAD_ID>"

Output:
  - stdout: ONLY the resultUrl (one line) when status == "success".
            Nothing is printed to stdout on failure or while pending.
  - stderr: all debug / progress info.
  - Exit code 0 = success, 1 = failure or error.
"""
import sys
import os
import time
import json
import urllib.request
import urllib.error
import argparse


def _log(tag, msg):
    print(f"[{tag}] {msg}", file=sys.stderr)


def poll_download(base_url, token, download_id):
    url = f"{base_url.rstrip('/')}/api/openclaw/download/check"
    headers = {
        "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    body = json.dumps({"downloadId": download_id}).encode("utf-8")

    _log("poll", f"Polling download {download_id} every 5s...")

    time.sleep(3)

    while True:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                res_json = json.loads(response.read().decode("utf-8"))

                if "error" in res_json and res_json["error"].get("code") != 0:
                    _log("poll", f"API Error: {res_json['error']}")
                    sys.exit(1)

                data_obj = res_json.get("data", {})
                status = data_obj.get("status", "")

                if status == "success":
                    result_url = data_obj.get("resultUrl", "")
                    _log("poll", f"Download ready! status=success")
                    if result_url:
                        print(result_url)  # stdout: only the URL
                    else:
                        _log("poll", "WARNING: status=success but resultUrl is empty.")
                    return

                elif status == "failed":
                    _log("poll", "Download FAILED.")
                    sys.exit(1)

                else:
                    # status == "pending" or unknown
                    print(".", end="", flush=True, file=sys.stderr)

        except urllib.error.HTTPError as e:
            _log("poll", f"HTTP {e.code}: {e.read().decode('utf-8')}")
            sys.exit(1)
        except Exception as e:
            _log("poll", f"Error: {e}")
            sys.exit(1)

        time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Poll Crepal download task until completion.",
        epilog="Prints the resultUrl to stdout when done.",
    )
    parser.add_argument("base_url", help="Base URL (e.g. https://crepal.ai)")
    parser.add_argument("token", help="Auth Token")
    parser.add_argument("download_id", help="Download task ID from /download/start")

    args = parser.parse_args()
    poll_download(args.base_url, args.token, args.download_id)
