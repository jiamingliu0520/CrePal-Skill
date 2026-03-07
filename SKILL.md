---
name: crepal
description: A one-stop AI video editing and generation tool. Use this skill when the user wants to generate, edit, or manipulate videos using the Crepal API. Supports fully automated "auto-pilot" mode that completes the entire video creation workflow without user intervention.
---

# Crepal — AI Video Creator Skill

## Overview

Crepal is a one-stop AI video creation tool. This skill connects OpenClaw to CrePal's API so you can create videos through natural conversation.

---

## Ground Rules

These apply to **everything** you do with this skill.

1. **Never show raw technical output to the user.** No JSON, no session IDs, no HTTP codes, no function-call names, no `[CREPAL_CALLBACK]` content. Summarize in plain, friendly language — as if texting a friend.
2. **Never stay silent after receiving an `agentMsg`.** Always either reply to CrePal or call `confirm_generate`. No exceptions.
3. **The `confirm_generate` API is the ONLY way to start video rendering.** Sending a chat message like "please generate" does nothing. You must call the dedicated endpoint.
4. **Translate errors into actionable advice.** Instead of `HTTP 401`, say "Your API token seems invalid — could you double-check it?"
5. **Keep progress updates to one sentence.** e.g. "CrePal 问了视频风格，我帮你选了温馨的，正在继续…"

---

## Configuration — `metadata.json`

Stored in the skill root directory. Read it on **every** invocation.

  ```json
  {
  "api_key": "",
  "user_channel": "",
  "auto_pilot": false,
  "last_session_id": ""
}
```

| Field | Purpose |
|-------|---------|
| `api_key` | CrePal API token. Used as `Authorization: Bearer <api_key>`. |
| `user_channel` | User's messaging address (e.g. `telegram:123456789`). Required for callbacks & notifications. |
| `auto_pilot` | `true` = full automation; `false` = step-by-step with user approval. |
| `last_session_id` | Most recent session ID for easy resumption. |

### First-Run Setup

If `api_key`, `user_channel`, or both are empty:

1. **Welcome** the user — introduce CrePal briefly.
2. **Collect `user_channel`** — ask for their messaging platform address (`platform:id`). This is mandatory; without it, callbacks cannot be delivered.
3. **Collect `api_key`** — direct them to [crepal.ai](https://crepal.ai) to get a token.
4. **Ask about auto-pilot** — explain the two modes and store their choice.
5. **Write all values** to `metadata.json` immediately.

**Pre-flight (every invocation):** If `user_channel` or `api_key` is empty → ask before doing anything else.

---

## Auto-Pilot Mode

Active when `auto_pilot` is `true`, or the user explicitly asks for full automation. You complete the entire pipeline without pausing for user input.

### ⚠️ Execution Model — FOREGROUND, NOT BACKGROUND

**You MUST run `poll_session.py` in the foreground** (i.e. `background: false` or simply `exec`). Wait for it to finish and capture its stdout. Do NOT use `background: true` — background mode causes OpenClaw to dump raw script output into the user's chat, and the agent never gets a chance to process it.

The script outputs **only the `agentMsg` text** to stdout (no JSON, no metadata). You capture this text, process it via the Decision Tree, and act on it — all in the same turn.

### Step 1 — Create Session & Poll

1. `POST /api/openclaw/chat/session/create` with the user's video description as `content`.
2. Save `sessionId` → `metadata.json` → `last_session_id`.
3. Tell the user briefly: "正在和 CrePal 沟通你的视频需求，请稍等…"
4. **Run `poll_session.py` in FOREGROUND** (no `--callback`, no `--notify`):
   ```
   python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SID>"
   ```
5. **Capture stdout** — it contains only the `agentMsg` text from CrePal.
6. **Go to Step 2** with the captured `agentMsg`.

### Step 2 — Process `agentMsg` (SILENT & IMMEDIATE)

You now have the `agentMsg` text. **Do NOT show it raw to the user.** Classify it and act:

#### Case A — Credit Error
`agentMsg` mentions "insufficient credits", "余额不足", etc.
→ **Exit auto-pilot.** Go to Recharge workflow.

#### Case B — Script Ready → CALL `confirm_generate` NOW 🔴
Match if **ANY** of these are true:
- Keywords: "generate", "render", "ready to produce", "开始生成", "准备生成", "是否生成视频"
- Script is "confirmed", "finalized", "complete", "done", "完成", "确认"
- CrePal says "anything else?", "want to proceed?", "shall I continue?" after a script
- **3+ rounds have passed** and no new questions in the latest `agentMsg`
- You replied "looks good" last round and no new questions came back

→ **IMMEDIATELY go to Step 3.** Do NOT reply via `message/send`. Call the `confirm_generate` API right now.

**⚠️ When in doubt between B and C/D, always choose B.** Better to generate early than loop forever.

#### Case C — CrePal Asks a Question
`agentMsg` asks a question or offers choices (e.g. "What style?", "(A)... (B)...").
→ Compose a direct answer based on the user's original description. Send via `message/send`. Then **re-poll** (go to Step 2½).

#### Case D — Script Draft Needs Feedback
`agentMsg` shows a draft and asks "what do you think?"
→ Reply "Looks great, please continue" via `message/send`. Then **re-poll**.

#### Case E — Anything Else
→ Reply "Looks good, please continue" via `message/send`. Then **re-poll**. Never stay silent.

### Step 2½ — Re-poll After Reply (Cases C/D/E)

After sending a reply to CrePal:

1. Tell the user in **one friendly sentence** what you did (e.g. "我帮你选了温馨风格，正在等 CrePal 回复…").
2. **Run `poll_session.py` in FOREGROUND again** (same command as Step 1, no flags).
3. Capture stdout → go back to **Step 2** with the new `agentMsg`.
4. **Repeat** until you reach Case A or B.

**🛑 LOOP GUARD:** If you've been through 3+ rounds and the latest `agentMsg` has no clear new questions → treat it as Case B and call `confirm_generate`.

### Step 3 — Confirm & Generate 🔴

This step **starts video rendering**. Without it, the user gets nothing.

1. `POST /api/openclaw/script/confirm_generate` with `{"sessionId": "..."}`.
   This is a **dedicated API call** — NOT a chat message via `message/send`.
2. Tell the user: "剧本已确认，视频片段正在生成中，请稍等…"
3. **Run `poll_session.py` in FOREGROUND** to wait for rendering to finish:
   ```
   python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SID>"
   ```
4. When the script finishes (all segments rendered), **go to Step 4**.

### Step 4 — Compose & Download 🎬

After all video segments are rendered, you must compose the final video and get the download URL.

1. `POST /api/openclaw/download/start` with:
  ```json
   { "sessionId": "...", "watermark": false, "resolution": 1080 }
   ```
   - `watermark`: `false` by default (no watermark). Set `true` if user explicitly requests one.
   - `resolution`: `1080` by default. Use `720` only if user requests lower quality.
   - Returns `downloadId` and estimated `duration` (seconds).
2. Tell the user: "视频片段已全部完成，正在合成最终成片…"
3. **Run `poll_download.py` in FOREGROUND** to wait for composing to finish:
   ```
   python3 scripts/poll_download.py "https://crepal.ai" "<TOKEN>" "<DOWNLOAD_ID>"
   ```
4. **Capture stdout** — it contains only the `resultUrl` (the download link).
5. **Present the download link** to the user in a friendly message:
   - "你的视频已经做好了！🎉 点击下载：<resultUrl>"
6. If the download fails (script exits with code 1), tell the user: "合成视频时遇到了问题，请稍后重试。"

---

## Manual Mode

Active when `auto_pilot` is `false`. You pause at each step for user input.

1. Call the relevant API endpoint (create session / send message / confirm generate).
2. Save `sessionId` to `metadata.json`.
3. **Run `poll_session.py` in FOREGROUND** (no flags). Capture the `agentMsg` from stdout.
4. Present the `agentMsg` content to the user **in friendly language** (never raw). Wait for their input.
5. Optionally also pass `--notify "<CHANNEL>"` if you want the user to get a push notification.

**Confirming generation in manual mode:**
- User says "looks good" / "continue" about a **script** → use `message/send`.
- User says "start generating the video" → use `confirm_generate`.

**Composing the final video (after rendering is done):**
1. Call `POST /api/openclaw/download/start` with `sessionId`, `watermark`, `resolution`.
2. Run `poll_download.py` in FOREGROUND. Capture `resultUrl` from stdout.
3. Present the download link to the user.

---

## Recharge Workflow

Triggered when `agentMsg` or any API response mentions insufficient credits.

1. Exit auto-pilot (if active).
2. `POST /api/openclaw/subscription/config` — get subscription plans.
3. Present plans with `stripeLink` to the user.
4. Optionally `POST /api/openclaw/one_time_products/config` — get one-time credit packs.
5. After user recharges, resume via `message/send`.

---

## API Reference

**Auth:** `Authorization: Bearer <api_key>` on all requests.  
**Base URL:** `https://crepal.ai`

### Create Session
`POST /api/openclaw/chat/session/create`
  ```json
{ "content": "Help me generate a short video script" }
```
Returns `sessionId`, `messageId`, `status`.

### Send Message
`POST /api/openclaw/chat/message/send`
```json
{ "sessionId": "...", "content": "Continue improving this video script" }
```
Returns `sessionId`, `messageId`, `status`.

### Check Session Ended
`POST /api/openclaw/chat/session/check_end`
```json
{ "sessionId": "..." }
```
Returns `{ "data": { "sessionId", "isEnded", "agentMsg" } }`.  
**Note:** `poll_session.py` automates this — you rarely call it directly.

### Confirm Script & Generate
`POST /api/openclaw/script/confirm_generate`
  ```json
{ "sessionId": "..." }
```
Starts video rendering. You **must** poll afterwards.

### Start Download (Compose Final Video)
`POST /api/openclaw/download/start`
```json
{ "sessionId": "...", "watermark": false, "resolution": 1080 }
```
- `watermark` (boolean): whether to add watermark. Default `false`.
- `resolution` (integer): `720` or `1080`. Default `1080`.
- Returns `downloadId` (string) and `duration` (estimated seconds).

### Check Download Status
`POST /api/openclaw/download/check`
```json
{ "downloadId": "..." }
```
Returns `{ "data": { "status": "pending|success|failed", "resultUrl": "..." } }`.
- `resultUrl` is the download link when `status` is `"success"`.
- **Note:** `poll_download.py` automates this — you rarely call it directly.

### Get Subscription Config
`POST /api/openclaw/subscription/config`  
No body. Returns `subscriptions[]` with `planType`, `price`, `stripeLink`, etc.

### Get One-Time Products
`POST /api/openclaw/one_time_products/config`  
No body. Returns `canPurchase`, `products[]` with `price`, `credits`, `stripeLink`.

---

## Resources

### `metadata.json`
Persistent config. Read on startup, write whenever values change.

### `scripts/poll_session.py`
Polls `check_end` every 5 s until `isEnded` is true.

**Output behavior:**
- **No flags (foreground mode):** prints only `agentMsg` text to stdout. All debug to stderr. **This is the primary mode.**
- **`--callback <ch>`:** stdout is **completely silent**. Sends `[CREPAL_CALLBACK]` message via openclaw CLI. (Fallback mode.)
- **`--notify <ch>`:** sends a short user-facing notification via openclaw CLI.
- **`--openclaw-path <path>`:** override auto-discovery of openclaw executable.

`<ch>` = `user_channel` from `metadata.json`.

```bash
# Primary: foreground, agent captures stdout (use this in auto-pilot)
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SID>"

# With user notification (final step or manual mode)
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SID>" --notify "<CHANNEL>"
```

### `scripts/poll_download.py`
Polls `download/check` every 5 s until `status` is `success` or `failed`.

**Output:** prints only the `resultUrl` to stdout when done. All debug to stderr.

```bash
python3 scripts/poll_download.py "https://crepal.ai" "<TOKEN>" "<DOWNLOAD_ID>"
```
