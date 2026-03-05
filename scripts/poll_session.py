#!/usr/bin/env python3
"""
poll_session.py — Poll a Crepal session for new messages and forward them via OpenClaw.

Usage:
  python scripts/poll_session.py <base_url> <api_key> <session_id> [--notify <openclaw_target>]

The script polls the Crepal API every 5 seconds. When new messages arrive
(text or media), they are forwarded to the OpenClaw gateway. The script exits
when the session ends, balance is insufficient, or a fatal error occurs.

Exit codes:
  0 - session ended normally
  1 - error
  2 - insufficient balance (paymentUrl printed before exit)
"""

import sys
import time
import json
import signal
import urllib.request
import urllib.error
import subprocess
import argparse

_running = True


def _handle_signal(signum, frame):
    global _running
    _running = False
    print(f"\nReceived signal {signum}, stopping...", file=sys.stderr)


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def send_to_openclaw(target: str, message: str):
    if not target:
        print(message)
        return
    try:
        subprocess.run(
            ["openclaw", "message", "send", "--target", target, "--message", message],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        print(f"[warn] openclaw CLI not found, printing instead: {message}", file=sys.stderr)
        print(message)
    except subprocess.CalledProcessError as e:
        print(f"[warn] openclaw send failed: {e.stderr.decode()}", file=sys.stderr)
        print(message)


def format_message(msg: dict) -> str:
    msg_type = msg.get("type", "text")
    content = msg.get("content", "")
    media_url = msg.get("mediaUrl", "")
    media_type = msg.get("mediaType", "")

    if msg_type == "media" and media_url:
        label = {"video": "Video", "image": "Image"}.get(media_type, "File")
        if content:
            return f"{content}\n[{label}] {media_url}"
        return f"[{label}] {media_url}"

    return content


def poll_session(base_url: str, api_key: str, session_id: str, notify_target: str):
    url = f"{base_url.rstrip('/')}/api/session/poll"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps({"sessionId": session_id, "apiKey": api_key}).encode("utf-8")

    print(f"Polling session {session_id} every 5s ...", file=sys.stderr)
    last_message_index = 0

    while _running:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"HTTP {e.code}: {error_body}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Request error: {e}", file=sys.stderr)
            time.sleep(5)
            continue

        data = res.get("data", {})

        if data.get("insufficientBalance"):
            payment_url = data.get("paymentUrl", "")
            msg = (
                "⚠️ Your Crepal account balance is insufficient to continue the current task.\n"
                f"Please click the link below to top up: {payment_url}\n"
                'After topping up, tell me "continue" and I will notify the cloud service to resume your task.'
            )
            send_to_openclaw(notify_target, msg)
            print(f"Insufficient balance. paymentUrl={payment_url}", file=sys.stderr)
            sys.exit(2)

        messages = data.get("messages", [])
        new_messages = messages[last_message_index:]

        for msg in new_messages:
            formatted = format_message(msg)
            if formatted:
                send_to_openclaw(notify_target, formatted)

        if new_messages:
            last_message_index = len(messages)

        if data.get("isEnded"):
            agent_msg = data.get("agentMsg", "")
            final = agent_msg if agent_msg else "Task completed."
            send_to_openclaw(notify_target, f"✅ {final}")
            print("Session ended.", file=sys.stderr)
            return

        print(".", end="", flush=True, file=sys.stderr)
        time.sleep(5)

    print("\nStopped by signal.", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll Crepal session and forward messages")
    parser.add_argument("base_url", help="Crepal API base URL")
    parser.add_argument("api_key", help="Crepal API key")
    parser.add_argument("session_id", help="Session ID to poll")
    parser.add_argument("--notify", help="OpenClaw target to forward messages to (e.g. user:ou_xxx)")
    args = parser.parse_args()

    poll_session(args.base_url, args.api_key, args.session_id, args.notify)
