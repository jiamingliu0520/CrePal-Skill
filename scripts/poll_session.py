#!/usr/bin/env python3
"""
poll_session.py — Poll Crepal session status until completion.

Output modes:
  - FOREGROUND (no --callback): prints ONLY the agentMsg text to stdout.
    The agent runs this script, awaits completion, captures stdout, and
    acts on the agentMsg directly. Nothing else is printed to stdout.
  - CALLBACK (--callback <channel>): stdout is completely silent. A compact
    [CREPAL_CALLBACK] message is injected into the conversation to wake
    the agent.

All debug/progress info goes to stderr only — never pollutes stdout.
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
    Locate the openclaw executable. Priority:
      1. Explicit --openclaw-path
      2. shutil.which (current PATH)
      3. NVM node versions (~/.nvm/versions/node/v*/bin/openclaw)
      4. Common global locations
      5. Relative to this script (npm global installs)
    Returns absolute path or None.
    """
    if explicit_path:
        if os.path.isfile(explicit_path) and os.access(explicit_path, os.X_OK):
            _log("discovery", f"Using explicit path: {explicit_path}")
            return explicit_path
        _log("discovery", f"WARNING: '{explicit_path}' not valid, falling back.")

    found = shutil.which("openclaw")
    if found:
        _log("discovery", f"Found via PATH: {found}")
        return found

    home = os.path.expanduser("~")
    nvm_pattern = os.path.join(home, ".nvm", "versions", "node", "v*", "bin", "openclaw")
    for match in sorted(glob.glob(nvm_pattern), reverse=True):
        if os.path.isfile(match) and os.access(match, os.X_OK):
            _log("discovery", f"Found via NVM: {match}")
            return match

    for p in [
        "/usr/local/bin/openclaw",
        "/usr/bin/openclaw",
        "/opt/homebrew/bin/openclaw",
        os.path.join(home, ".local", "bin", "openclaw"),
    ]:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            _log("discovery", f"Found at: {p}")
            return p

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.normpath(os.path.join(script_dir, "..", "..", "..", "bin", "openclaw"))
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            _log("discovery", f"Found relative to script: {candidate}")
            return candidate
    except Exception:
        pass

    _log("discovery", "WARNING: Could not find openclaw executable.")
    return None


def _log(tag, msg):
    """Print a debug message to stderr only."""
    print(f"[{tag}] {msg}", file=sys.stderr)


def _build_env(openclaw_path):
    """Build subprocess env with openclaw bin dir in PATH."""
    env = os.environ.copy()
    if openclaw_path and os.path.isabs(openclaw_path):
        bin_dir = os.path.dirname(openclaw_path)
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"
    return env


def _run_openclaw_cmd(openclaw_path, args_list, label="openclaw"):
    """Run an openclaw CLI command. Returns True on success. Never raises."""
    cmd = [openclaw_path] + args_list
    _log(label, f"Executing: {' '.join(cmd)}")
    try:
        env = _build_env(openclaw_path)
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            _log(label, f"Success.")
            return True
        else:
            _log(label, f"Failed (exit {result.returncode}): {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        _log(label, f"Executable not found at '{cmd[0]}'.")
        return False
    except Exception as e:
        _log(label, f"Error: {e}")
        return False


# ---------------------------------------------------------------------------
# Callback: Wake up OpenClaw via message injection
# ---------------------------------------------------------------------------

def send_callback(openclaw_path, callback_target, session_id, agent_msg):
    """Inject a compact [CREPAL_CALLBACK] message into the conversation."""
    if not openclaw_path:
        _log("callback", "Skipping: openclaw not found.")
        return
    payload = json.dumps({"sessionId": session_id, "agentMsg": agent_msg}, ensure_ascii=False)
    _run_openclaw_cmd(
        openclaw_path,
        ["message", "send", "--target", callback_target, "--message", f"[CREPAL_CALLBACK]{payload}"],
        label="callback",
    )


# ---------------------------------------------------------------------------
# Notification: User-facing message (manual mode / final step only)
# ---------------------------------------------------------------------------

def send_notification(openclaw_path, notify_target, session_id, agent_msg):
    """Send a friendly user-facing notification. Never raises."""
    if not openclaw_path:
        _log("notify", "Skipping: openclaw not found.")
        return
    # Keep it short and non-technical
    msg = f"✨ 你的视频已准备就绪！"
    _run_openclaw_cmd(
        openclaw_path,
        ["message", "send", "--target", notify_target, "--message", msg],
        label="notify",
    )


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

def poll_session(base_url, token, session_id, notify_target, callback_target, openclaw_path_override):
    url = f"{base_url.rstrip('/')}/api/openclaw/chat/session/check_end"
    headers = {
        "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    body = json.dumps({"sessionId": session_id}).encode("utf-8")

    need_openclaw = notify_target or callback_target
    openclaw_bin = find_openclaw_executable(openclaw_path_override) if need_openclaw else None

    _log("poll", f"Polling session {session_id} every 5s...")
    if callback_target:
        _log("poll", f"  callback → {callback_target}")
    if notify_target:
        _log("poll", f"  notify → {notify_target}")

    time.sleep(5)

    while True:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                res_json = json.loads(response.read().decode("utf-8"))

                if "error" in res_json and res_json["error"].get("code") != 0:
                    _log("poll", f"API Error: {res_json['error']}")
                    sys.exit(1)

                data_obj = res_json.get("data", {})
                if data_obj.get("isEnded") is True:
                    agent_msg = data_obj.get("agentMsg", "") or "(empty response)"
                    _log("poll", "Session ended.")

                    # --- stdout output ---
                    # If callback is set → stdout is SILENT (callback handles delivery)
                    # If no callback  → print ONLY the agentMsg (for foreground capture)
                    if not callback_target:
                        print(agent_msg)

                    # --- callback: wake up the agent ---
                    if callback_target:
                        send_callback(openclaw_bin, callback_target, session_id, agent_msg)

                    # --- notify: user-facing message ---
                    if notify_target:
                        send_notification(openclaw_bin, notify_target, session_id, agent_msg)

                    return
                else:
                    print(".", end="", flush=True, file=sys.stderr)

        except urllib.error.HTTPError as e:
            _log("poll", f"HTTP {e.code}: {e.read().decode('utf-8')}")
            sys.exit(1)
        except Exception as e:
            _log("poll", f"Error: {e}")
            sys.exit(1)

        time.sleep(5)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Poll Crepal session until completion.",
        epilog=(
            "Foreground: python3 poll_session.py URL TOKEN SID  (prints agentMsg to stdout)\n"
            "Background: python3 poll_session.py URL TOKEN SID --callback <CH>  (silent stdout, wakes agent)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("base_url", help="Base URL (e.g. https://crepal.ai)")
    parser.add_argument("token", help="Auth Token")
    parser.add_argument("session_id", help="Session ID")
    parser.add_argument("--callback", help="Channel to send [CREPAL_CALLBACK] to (wakes agent)", default=None)
    parser.add_argument("--notify", help="Channel to send user notification to", default=None)
    parser.add_argument("--openclaw-path", help="Explicit openclaw executable path", default=None)

    args = parser.parse_args()
    poll_session(args.base_url, args.token, args.session_id, args.notify, args.callback, args.openclaw_path)
