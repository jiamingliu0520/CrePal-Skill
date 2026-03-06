#!/usr/bin/env python3
"""
poll_session.py — Poll Crepal session status and notify user when done.

Features:
  - Polls the check_end endpoint every 5 seconds until the session ends.
  - Smart discovery of the `openclaw` executable (PATH, NVM, common locations).
  - --openclaw-path override for explicit control.
  - Robust error handling: notification failure never crashes the main flow.
"""
import sys
import os
import glob
import time
import json
import shutil
import urllib.request
import urllib.error
import subprocess
import argparse


# ---------------------------------------------------------------------------
# OpenClaw executable discovery
# ---------------------------------------------------------------------------

def find_openclaw_executable(explicit_path=None):
    """
    Locate the openclaw executable. Priority order:
      1. Explicit path provided via --openclaw-path (highest priority)
      2. shutil.which — whatever is on the current PATH
      3. NVM node versions (~/.nvm/versions/node/v*/bin/openclaw)
      4. Common global install locations (/usr/local/bin, /usr/bin, etc.)
      5. Relative to this script's location (npm global installs)

    Returns the absolute path to the executable, or None if not found.
    """
    # 1. Explicit override
    if explicit_path:
        if os.path.isfile(explicit_path) and os.access(explicit_path, os.X_OK):
            print(f"[discovery] Using explicit openclaw path: {explicit_path}", file=sys.stderr)
            return explicit_path
        else:
            print(f"[discovery] WARNING: Explicit path '{explicit_path}' is not a valid executable, falling back to auto-discovery.", file=sys.stderr)

    # 2. shutil.which — respects current PATH
    found = shutil.which("openclaw")
    if found:
        print(f"[discovery] Found openclaw via PATH: {found}", file=sys.stderr)
        return found

    # 3. NVM directories — search for the latest node version
    home = os.path.expanduser("~")
    nvm_pattern = os.path.join(home, ".nvm", "versions", "node", "v*", "bin", "openclaw")
    nvm_matches = sorted(glob.glob(nvm_pattern), reverse=True)  # latest version first
    for match in nvm_matches:
        if os.path.isfile(match) and os.access(match, os.X_OK):
            print(f"[discovery] Found openclaw via NVM: {match}", file=sys.stderr)
            return match

    # 4. Common global locations
    common_paths = [
        "/usr/local/bin/openclaw",
        "/usr/bin/openclaw",
        "/opt/homebrew/bin/openclaw",
        os.path.join(home, ".local", "bin", "openclaw"),
    ]
    for p in common_paths:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            print(f"[discovery] Found openclaw at common path: {p}", file=sys.stderr)
            return p

    # 5. Relative to this script (npm global structure: .../lib/node_modules/.../scripts/poll_session.py → .../bin/openclaw)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Walk up to find a bin/ sibling
        candidate = os.path.normpath(os.path.join(script_dir, "..", "..", "..", "bin", "openclaw"))
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            print(f"[discovery] Found openclaw relative to script: {candidate}", file=sys.stderr)
            return candidate
    except Exception:
        pass

    print("[discovery] WARNING: Could not find openclaw executable anywhere.", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Notification helper
# ---------------------------------------------------------------------------

def send_notification(openclaw_path, notify_target, session_id, agent_msg):
    """Send a notification via openclaw CLI. Never raises — logs errors to stderr."""
    if not openclaw_path:
        print("[notify] Skipping notification: openclaw executable not found.", file=sys.stderr)
        return

    msg = (
        f"✨ Your Crepal video task is done!\n"
        f"Session ID: {session_id}\n"
        f"Response: {agent_msg}"
    )
    cmd = [openclaw_path, "message", "send", "--target", notify_target, "--message", msg]
    print(f"[notify] Executing: {' '.join(cmd)}", file=sys.stderr)

    try:
        # Inject the executable's directory into PATH for the subprocess
        env = os.environ.copy()
        if os.path.isabs(openclaw_path):
            bin_dir = os.path.dirname(openclaw_path)
            env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"[notify] Notification sent successfully. stdout: {result.stdout.strip()}", file=sys.stderr)
        else:
            print(
                f"[notify] Failed to send notification. exit_code={result.returncode}\n"
                f"  stderr: {result.stderr.strip()}",
                file=sys.stderr,
            )
    except FileNotFoundError:
        print(f"[notify] Error: Executable not found at '{cmd[0]}'.", file=sys.stderr)
    except Exception as e:
        print(f"[notify] Error sending notification: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

def poll_session(base_url, token, session_id, notify_target, openclaw_path_override):
    url = f"{base_url.rstrip('/')}/api/openclaw/chat/session/check_end"
    headers = {
        "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    data = json.dumps({"sessionId": session_id}).encode("utf-8")

    # Resolve openclaw executable once, before entering the loop
    openclaw_bin = find_openclaw_executable(openclaw_path_override) if notify_target else None

    print(f"Polling {url} for session {session_id} every 5 seconds...", file=sys.stderr)
    time.sleep(5)

    while True:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)

                if "error" in res_json and res_json["error"].get("code") != 0:
                    print(f"\nAPI Error: {res_json['error']}", file=sys.stderr)
                    sys.exit(1)

                data_obj = res_json.get("data", {})
                if data_obj.get("isEnded") is True:
                    print("\n[OK] Session ended.", file=sys.stderr)
                    agent_msg = data_obj.get("agentMsg", "") or "(empty response)"

                    # Always output result to stdout (consumed by the caller / agent)
                    print(json.dumps(data_obj, ensure_ascii=False, indent=2))

                    # Notify user (best-effort, never crashes)
                    if notify_target:
                        send_notification(openclaw_bin, notify_target, session_id, agent_msg)

                    return
                else:
                    print(".", end="", flush=True, file=sys.stderr)

        except urllib.error.HTTPError as e:
            print(f"\nHTTP Error {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

        time.sleep(5)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll Crepal Session")
    parser.add_argument("base_url", help="Base URL (e.g. https://crepal.ai)")
    parser.add_argument("token", help="Auth Token")
    parser.add_argument("session_id", help="Session ID")
    parser.add_argument("--notify", help="OpenClaw target ID to notify when done (e.g., user:ou_xxx)")
    parser.add_argument(
        "--openclaw-path",
        help="Absolute path to openclaw executable (optional, auto-discovered if omitted)",
        default=None,
    )

    args = parser.parse_args()
    poll_session(args.base_url, args.token, args.session_id, args.notify, args.openclaw_path)
