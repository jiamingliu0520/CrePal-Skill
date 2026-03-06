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

### Step 1 — Create Session

1. `POST /api/openclaw/chat/session/create` with the user's video description as `content`.
2. Save `sessionId` → `metadata.json` → `last_session_id`.
3. Run `poll_session.py` in background with **only `--callback`** (no `--notify` during intermediate rounds — you talk to the user yourself).
4. Yield control. A `[CREPAL_CALLBACK]` message will wake you up.

### Step 2 — Handle Callback (SILENT & IMMEDIATE)

When you see `[CREPAL_CALLBACK]{"sessionId":"...","agentMsg":"..."}`:

1. **Parse** the JSON. Extract `agentMsg`.
2. **Hide** — never show any part of the callback to the user.
3. **Classify & Act** — go through cases A → E in order. Execute the **first** match.

#### Case A — Credit Error
`agentMsg` mentions "insufficient credits", "余额不足", etc.
→ **Exit auto-pilot.** Go to Recharge workflow.

#### Case B — Script Ready → CALL `confirm_generate` NOW 🔴
Match if **ANY** of these are true:
- Keywords present: "generate", "render", "ready to produce", "开始生成", "准备生成", "是否生成视频"
- Script is "confirmed", "finalized", "complete", "done", "完成", "确认"
- CrePal says "anything else?", "want to proceed?", "shall I continue?" after showing a script
- **3+ callback rounds have passed** and the latest `agentMsg` has no new questions
- You replied "looks good" / "confirmed" last round and this round has no new questions

→ **IMMEDIATELY go to Step 3.** Do NOT reply via `message/send`. Do NOT ask the user. Call the `confirm_generate` API right now.

**⚠️ When in doubt between B and C/D, always choose B.** It's better to start generating slightly early than to loop forever. The user wants a video.

#### Case C — CrePal Asks a Question
`agentMsg` asks a question or offers choices (e.g. "What style?", "(A)... (B)... (C)...").
→ Compose a direct answer based on the user's original description. Send via `message/send`. Re-poll with `--callback`.

#### Case D — Script Draft Needs Feedback
`agentMsg` shows a draft and asks "what do you think?" / "does this look good?"
→ Reply "Looks great, please continue" via `message/send`. Re-poll.

#### Case E — Anything Else
→ Reply "Looks good, please continue" via `message/send`. Re-poll. Never stay silent.

---

**After acting (all cases):** tell the user in **one friendly sentence** what you did. No technical details.

**After C/D/E:** re-run `poll_session.py` with `--callback`, yield, wait for next callback → return to Step 2.

**🛑 YIELD SELF-CHECK — ask yourself before every yield:**
> "Have I gone through 3+ rounds? Is the script probably done? Should I call `confirm_generate` instead of looping again?"
> If the answer is "maybe yes" → call `confirm_generate` (Step 3). Do not loop again.

### Step 3 — Confirm & Generate 🔴

This is the step that **produces the video**. Without it, the user gets nothing.

1. `POST /api/openclaw/script/confirm_generate` with `{"sessionId": "..."}`.
   This is a **dedicated API call** — NOT a chat message via `message/send`.
2. Run `poll_session.py` with **`--callback` and `--notify`** (both appropriate now — the job is finishing).
3. Tell the user: "视频正在生成中！完成后我会通知你 🎬"

---

## Manual Mode

Active when `auto_pilot` is `false`. You pause at each step for user input.

1. Call the relevant API endpoint (create session / send message / confirm generate).
2. Save `sessionId` to `metadata.json`.
3. Run `poll_session.py` with `--callback` and `--notify`.
4. When callback arrives, present the `agentMsg` content to the user (in friendly language). Wait for their input.

**Confirming generation in manual mode:**
- User says "looks good" / "continue" about a **script** → use `message/send`.
- User says "start generating the video" → use `confirm_generate`.

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
Polls `check_end` every 5 s until `isEnded` is true. Key flags:

| Flag | Purpose |
|------|---------|
| `--callback <channel>` | Injects `[CREPAL_CALLBACK]{...}` into the conversation to wake up the AI agent. **Always use in auto-pilot.** |
| `--notify <channel>` | Sends a user-facing notification. **Only use in manual mode or the final generate step.** |
| `--openclaw-path <path>` | Override auto-discovery of the `openclaw` executable. |

`<channel>` = `user_channel` from `metadata.json`.

```bash
# Auto-pilot (intermediate rounds)
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SID>" --callback "<CHANNEL>"

# Auto-pilot (final generate) or Manual mode
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SID>" --callback "<CHANNEL>" --notify "<CHANNEL>"
```
