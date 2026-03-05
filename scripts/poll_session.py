#!/usr/bin/env python3
import sys
import time
import json
import urllib.request
import urllib.error
import subprocess
import argparse

def poll_session(base_url, token, session_id, notify_target):
    url = f"{base_url.rstrip('/')}/api/openclaw/chat/session/check_end"
    headers = {
        "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token,
        "Content-Type": "application/json"
    }
    data = json.dumps({"sessionId": session_id}).encode('utf-8')

    print(f"Polling {url} for session {session_id} every 5 seconds...", file=sys.stderr)
    
    while True:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode('utf-8')
                res_json = json.loads(res_body)
                
                if 'error' in res_json and res_json['error'].get('code') != 0:
                    print(f"\nAPI Error: {res_json['error']}", file=sys.stderr)
                    sys.exit(1)
                
                data_obj = res_json.get('data', {})
                if data_obj.get('isEnded') is True:
                    print("\n[OK] Session ended.", file=sys.stderr)
                    agent_msg = data_obj.get('agentMsg', '')
                    if not agent_msg:
                        agent_msg = "（返回内容为空）"
                        
                    print(json.dumps(data_obj, ensure_ascii=False, indent=2))
                    
                    # 主动通知用户
                    if notify_target:
                        msg = f"✨ 你的 Crepal 视频任务跑完啦！\n会话ID: {session_id}\n返回内容: {agent_msg}"
                        subprocess.run(["openclaw", "message", "send", "--target", notify_target, "--message", msg])
                        
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll Crepal Session")
    parser.add_argument("base_url", help="Base URL")
    parser.add_argument("token", help="Auth Token")
    parser.add_argument("session_id", help="Session ID")
    parser.add_argument("--notify", help="OpenClaw target ID to notify when done (e.g., user:ou_xxx)")
    
    args = parser.parse_args()
    poll_session(args.base_url, args.token, args.session_id, args.notify)