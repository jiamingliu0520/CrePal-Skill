---
name: crepal
description: A one-stop AI video editing and generation tool. Use this skill when the user wants to generate, edit, or manipulate videos using the Crepal API. Supports fully automated "auto-pilot" mode that completes the entire video creation workflow without user intervention.
---

# Crepal

## Overview

Crepal is a powerful one-stop AI video editing and generation tool. This skill guides the AI and the user through the process of setting up and using the Crepal API for video-related tasks.

---

## 🗣️ Communication Guidelines: What to Show the User

**The user is NOT a developer.** They don't care about API responses, JSON payloads, session IDs, HTTP status codes, or function call results. You MUST filter and translate all technical outputs into plain, friendly language before presenting anything to the user.

### NEVER show the user:
- Raw API responses or JSON bodies (e.g. `{"data":{"sessionId":"550e8400...","isEnded":true}}`)
- HTTP status codes (e.g. `200 OK`, `POST https://crepal.ai/api/...`)
- Session IDs, message IDs, or any UUID strings
- Function/tool call names, parameters, or return values
- Stack traces, error objects, or technical error messages
- Internal workflow state (e.g. "Running poll_session.py with --callback...")
- The `[CREPAL_CALLBACK]` message content — this is an internal system signal, NOT for the user. NEVER display it, quote it, or paraphrase it. Process it silently and act on it.

### ALWAYS do this instead:
- **Summarize the result** in one or two natural sentences. Think: "If I were texting a friend, how would I say this?"
- **Translate errors** into actionable advice: instead of `HTTP 401 Unauthorized`, say "Your API token seems invalid. Could you double-check it?"
- **Report progress** in human terms: instead of `isEnded=false, polling...`, say "CrePal is still working on it, I'll let you know when it's ready."
- **Extract the meaningful content** from `agentMsg` and present just the creative parts (script text, style choices, etc.)

### Examples

| ❌ Bad (raw dump) | ✅ Good (summarized) |
|---|---|
| `POST /api/openclaw/chat/session/create returned 200: {"data":{"sessionId":"550e8400-e29b-41d4-a716-446655440000"}}` | "I've started a new video session with CrePal. Working on your request now..." |
| `poll_session.py exited. Output: {"sessionId":"550e...","isEnded":true,"agentMsg":"Here is your script:\n1. Opening shot..."}` | "CrePal has drafted a script for you! Here's what they came up with: *(then show the script content only)*" |
| `Error: urllib.error.HTTPError: HTTP Error 401: Unauthorized` | "It looks like your API token isn't working. Could you check if it's still valid? You can get a new one at crepal.ai." |
| `Running: python3 scripts/poll_session.py "https://crepal.ai" "eyJhb..." "550e8400..." --callback "telegram:123" &` | *(Don't say anything about this. It's an internal action.)* |
| `agentMsg: "insufficient credits, please recharge"` | "It looks like your CrePal account needs more credits. Let me pull up the pricing options for you..." |

### The Decision Rule

Before showing ANYTHING to the user, ask yourself:
1. **Does the user need to know this to make a decision or take an action?** → If yes, summarize it in plain language.
2. **Is this just an internal technical step?** → If yes, keep it to yourself. Say nothing.
3. **Is this an error the user can fix?** → If yes, explain what happened and what they should do, in simple terms.
4. **Is this creative content from CrePal (script, style choices, etc.)?** → If yes, present it nicely, without the technical wrapper.

---

## Persistent Configuration: `metadata.json`

This skill stores user configuration in `metadata.json` (located in the skill root directory alongside this file).

**Structure:**
```json
{
  "api_key": "",
  "user_channel": "",
  "auto_pilot": false,
  "last_session_id": ""
}
```

| Field | Description |
|-------|-------------|
| `api_key` | The user's CrePal API access token. Used in `Authorization: Bearer <api_key>` header. |
| `user_channel` | The user's messaging channel address for OpenClaw to send messages back. This is how the agent finds and reaches the user. Format depends on platform, e.g. `telegram:123456789` (Telegram chat ID), `discord:987654321` (Discord channel ID), `slack:C0123ABCDEF` (Slack channel ID), etc. **This field is CRITICAL** — without it, callback and notification messages cannot be delivered. |
| `auto_pilot` | Whether the user prefers auto-pilot mode (see below). Persisted across sessions. |
| `last_session_id` | The most recent session ID, for easy resumption. |

### Reading & Writing `metadata.json`

- **On every skill invocation**, first read `metadata.json` to check if `api_key` and `user_channel` are already stored.
- If `api_key` is empty or missing, prompt the user to provide it (direct them to [crepal.ai](https://crepal.ai) to register/login).
- If `user_channel` is empty or missing, you **MUST** ask the user for it before proceeding (see "Initial Setup" below).
- Once obtained, **write values back** to `metadata.json` immediately so they persist for future sessions.
- Update `last_session_id` whenever a new session is created.
- Update `auto_pilot` when the user expresses a preference.

---

## Initial Setup & First-Run Experience

When this skill is first invoked (i.e. `api_key` or `user_channel` in `metadata.json` is empty):

1. **Welcome the user:** Introduce CrePal as a one-stop AI video creation tool.

2. **Collect the user's messaging channel address:**
   Ask the user for their messaging platform channel address. This is how you will send callback and notification messages back to them. Explain clearly:

   > "To send you progress updates and results, I need your messaging channel address. Please provide it in the format `platform:id`, for example:
   > - Telegram: `telegram:123456789` (your Telegram chat ID)
   > - Discord: `discord:987654321` (your Discord channel ID)
   > - Slack: `slack:C0123ABCDEF` (your Slack channel ID)
   >
   > You can usually find this in your OpenClaw account settings under 'Connected Channels'. What's your channel address?"

   Write the value to `metadata.json` → `user_channel`.

   **⚠️ This step is MANDATORY.** Without `user_channel`, the polling script cannot send callback messages, and the auto-pilot loop will break. Do NOT proceed until `user_channel` is stored.

3. **Direct the user to get an API token:** Instruct them to visit [https://crepal.ai](https://crepal.ai) to register/login and generate their API access token.

4. **Store the token:** Once the user provides the token, write it to `metadata.json` → `api_key`.

5. **Ask about auto-pilot:** Proactively ask the user:

   > "Would you like me to use **auto-pilot mode**? In this mode, I'll automatically handle all of CrePal's questions and confirmations, completing the entire video from script to final render in one go — you just describe what you want and sit back. Otherwise, I'll pause at each step for your review. Which do you prefer?"

6. **Store the preference:** Write the user's choice to `metadata.json` → `auto_pilot` (`true` or `false`).

### Pre-Flight Check (on EVERY skill invocation)

Before doing any work, verify these fields in `metadata.json`:
- `user_channel` — **MUST NOT be empty.** If empty, ask for it first.
- `api_key` — **MUST NOT be empty.** If empty, ask for it first.

---

## Workflow: Auto-Pilot Mode (Full Automation)

When `auto_pilot` is `true` in `metadata.json`, OR the user explicitly asks for full automation:

The agent MUST complete the **entire** video creation pipeline automatically, without pausing for user input at intermediate steps.

### ⚠️ CRITICAL RULE #1: NEVER LEAVE AN `agentMsg` UNANSWERED

**Every time you receive an `agentMsg` from CrePal via polling, you MUST take action on it** — either reply via `message/send`, or trigger `confirm_generate`. There is NO scenario in auto-pilot where you read an `agentMsg` and then stop or wait for the user. If you find yourself about to present an `agentMsg` to the user and wait — STOP — that is wrong in auto-pilot mode. You must reply yourself and keep the loop going.

### ⚠️ CRITICAL RULE #2: YOU MUST CALL `confirm_generate` TO START VIDEO GENERATION

**The video will NEVER be generated unless you explicitly call the `/api/openclaw/script/confirm_generate` endpoint.** This is a separate, dedicated API — sending a chat message like "please generate" does NOT trigger generation. You must call this endpoint yourself as a tool/function call. CrePal is waiting for this signal from YOU. If you don't call it, the entire workflow is incomplete and the user gets nothing.

**When to call it:** As soon as CrePal's script is finalized (see Decision Tree Case B below). Do NOT wait for the user to tell you. In auto-pilot mode, YOU are the one who presses the "generate" button.

### How the Callback Wake-Up Works

`poll_session.py` supports a `--callback` parameter. When the script detects `isEnded=true`, it uses `openclaw message send` to inject a `[CREPAL_CALLBACK]` message back into the conversation. This message triggers OpenClaw's message-receive pipeline, **waking up the AI agent** so it can immediately process the `agentMsg` and continue the auto-pilot loop — no human nudge required.

The callback message format is a compact single-line JSON:
```
[CREPAL_CALLBACK]{"sessionId":"...","agentMsg":"..."}
```

**IMPORTANT — Auto-pilot polling:**
- You MUST always pass `--callback "<user_channel>"` when running `poll_session.py`, where `<user_channel>` is `metadata.json` → `user_channel`.
- **Do NOT pass `--notify` in auto-pilot mode.** You (the AI agent) are the one who communicates with the user. The script should only wake you up; you then compose a friendly message yourself. Passing `--notify` causes a second, raw, ugly message to appear in the user's chat — this is strictly forbidden.

### Step 1 — Create Session
1. Call `POST https://crepal.ai/api/openclaw/chat/session/create` with the user's video description as `content`.
2. Extract `sessionId` from the response. Write it to `metadata.json` → `last_session_id`.
3. Run `scripts/poll_session.py` in the background **with ONLY `--callback "<user_channel>"`** (read `user_channel` from `metadata.json`). **No `--notify` in auto-pilot.**
4. **You may now yield control.** When the polling completes, a `[CREPAL_CALLBACK]` message will appear in the conversation. This is your wake-up signal.
5. **→ When you receive a `[CREPAL_CALLBACK]` message, immediately proceed to Step 2.**

### Step 2 — Receive `[CREPAL_CALLBACK]` & Take Action (IMMEDIATE, SILENT, MANDATORY)

#### ⛔ THE 3-SECOND PROTOCOL — What you MUST do when `[CREPAL_CALLBACK]` arrives

When you see a message starting with `[CREPAL_CALLBACK]`, you MUST execute the following steps **silently, immediately, and without showing any raw content to the user:**

1. **PARSE** — Extract the JSON payload after the `[CREPAL_CALLBACK]` prefix. Get `sessionId` and `agentMsg`.
2. **HIDE** — Do **NOT** display the callback message, the JSON, the `agentMsg` text, the session ID, or any part of the raw callback to the user. This is an internal system signal.
3. **CLASSIFY** — Read the `agentMsg` and classify it using the Decision Tree below.
4. **ACT** — Execute the action dictated by the Decision Tree. This means making an API call (`message/send` or `confirm_generate`) RIGHT NOW, in this same turn. Do not stop, do not wait, do not ask the user.
5. **BRIEF UPDATE** — After acting, send the user ONE short friendly sentence about what you did (e.g. "CrePal 问了我视频风格，我选了温馨风格，继续推进中…"). No technical details.

**🚫 FORBIDDEN BEHAVIORS when receiving `[CREPAL_CALLBACK]`:**
- ❌ Showing the raw callback text to the user
- ❌ Pasting the `agentMsg` content verbatim to the user
- ❌ Printing session IDs, JSON, or technical metadata
- ❌ Stopping and waiting for user input (in auto-pilot mode)
- ❌ Saying "I received a callback" or any meta-commentary about the system
- ❌ Doing nothing / staying silent

#### Decision Tree (MANDATORY on every `[CREPAL_CALLBACK]`)

Classify the `agentMsg` and go through this checklist **in order**:

##### Case A — Insufficient Credits
**Condition:** `agentMsg` contains credit-related errors (e.g. "insufficient credits", "please recharge", "余额不足", "请充值").
**Action:** **EXIT auto-pilot.** Follow the "Insufficient Credits & Recharge" workflow.

##### Case B — Script Ready → MUST CALL `confirm_generate` 🔴
**Condition:** The script is finalized and CrePal is ready for video generation. Look for ANY of these signals:
- CrePal explicitly says: "generate", "render", "start producing", "ready to generate", "shall I generate", "开始生成", "准备生成", "是否生成视频"
- CrePal presents a **final/complete script** without asking further questions
- CrePal says the script is "confirmed", "finalized", "complete", "done", "完成", "确认"
- CrePal asks "anything else?" or "want to proceed?" after showing a script
- There have been **3+ rounds** of back-and-forth and the latest `agentMsg` contains no new questions — assume the script is done
- You already replied "looks good" or "confirmed" in the previous round, and CrePal didn't ask any new questions

**Action:** **IMMEDIATELY call `POST https://crepal.ai/api/openclaw/script/confirm_generate`** with the `sessionId`. This is a dedicated API endpoint — you MUST call it as a tool/function call. Do NOT try to "confirm" by sending a chat message. See Step 3 below.

**⚠️ When in doubt, lean towards calling `confirm_generate`.** It's better to trigger generation slightly early than to loop forever without generating. The user wants a video — give them one.

##### Case C — CrePal Asks a Question or Offers Choices 🟡
**Condition:** `agentMsg` asks a question, requests a choice, or presents options (e.g. "What style?", "Which tone?", "Do you prefer A or B?", "(A) ... (B) ... (C) ...").
**Action — you MUST do ALL of these, in this order:**
1. **Read the user's original video description** to understand their intent.
2. **Compose a clear, direct answer** using your AI judgment. Pick the option that best matches the user's intent. For example:
   - If the user wanted a "heartwarming" video and CrePal offers "(A) Heartwarming (B) Realistic (C) Playful" → pick (A).
   - If unsure, pick the most universally appealing option.
   - Include brief reasoning if multiple choices are involved (e.g. "I'll go with (A) Heartwarming style, and no on-screen presenter — just a background narrator to keep the focus on the animals.").
3. **Send the reply** via `POST https://crepal.ai/api/openclaw/chat/message/send` with the `sessionId` and your composed answer as `content`.
4. **Run `poll_session.py`** again in the background with `--callback` (no `--notify`).
5. **Tell the user briefly** what you chose (e.g. "CrePal 问了几个创意问题，我帮你选了温馨风格，正在继续细化剧本…").

**🚫 Do NOT show the user CrePal's raw question text. Do NOT ask the user to answer. You are auto-pilot — YOU answer.**

##### Case D — Script Draft Needs Confirmation
**Condition:** `agentMsg` presents a script draft/outline and asks for confirmation or feedback (e.g. "Here's the script, what do you think?", "Does this look good?").
**Action:** Reply with an affirmative like "Looks great, please continue" or "Confirmed, go ahead" via `message/send`. Then re-poll with `--callback`.

##### Case E — Fallback (anything else)
**Condition:** `agentMsg` is any other content that doesn't clearly fit above categories.
**Action:** Reply with "Looks good, please continue" via `message/send`. Then re-poll with `--callback`. **Never stay silent.**

**After every reply (Cases C, D, E):**
1. Run `scripts/poll_session.py` again in the background with **only `--callback`**.
2. Yield control and wait for the next `[CREPAL_CALLBACK]`.
3. **→ When callback arrives, return to Step 2. Repeat until you reach Case A or B.**

### Step 3 — Confirm & Generate (THE FINAL STEP — NEVER SKIP THIS) 🔴

**This is the step that actually produces the video.** Without it, the user gets nothing.

1. Call `POST https://crepal.ai/api/openclaw/script/confirm_generate` with the following request body:
   ```json
   {
     "sessionId": "<the session ID from metadata.json or context>"
   }
   ```
   This is a **separate HTTP POST request** to the `/api/openclaw/script/confirm_generate` endpoint. It is NOT a chat message. You must make this API call directly.

2. After the API call succeeds, run `scripts/poll_session.py` in the background with **`--callback` and `--notify`** (both are appropriate here because the job is truly finishing — the notify message tells the user the video is ready).

3. **Tell the user** (in friendly language): "视频正在生成中！完成后我会立刻通知你 🎬"

**Common mistakes to avoid:**
- ❌ Sending "please generate the video" via `message/send` — this does NOT trigger generation.
- ❌ Asking the user "should I generate now?" — in auto-pilot mode, you decide, not the user.
- ❌ Stopping after the script is confirmed without calling `confirm_generate` — this leaves the job incomplete.
- ❌ Forgetting this step exists — always check: "Have I called `confirm_generate` yet?"

### Auto-Pilot Safety Rules
- **NEVER leave an `agentMsg` without a response.** If in doubt, reply "Looks good, please continue".
- **NEVER show raw callback content, JSON, session IDs, or technical output to the user.** Summarize in plain language only.
- **NEVER use `--notify` during intermediate polling rounds in auto-pilot.** Only `--callback` is used until the final generate step.
- **NEVER skip the `confirm_generate` step.** The auto-reply loop handles script refinement only. Video generation MUST go through the dedicated `/script/confirm_generate` endpoint. If the loop has gone 3+ rounds with no new questions, it's time to call `confirm_generate`.
- **If credits are insufficient** at any point, **immediately exit auto-pilot** and follow the "Insufficient Credits & Recharge" workflow below.
- **If an API error occurs**, stop and report to the user with the error details (in plain language).
- **Keep the user informed** with brief, friendly progress updates after each round (e.g. "CrePal 问了视频风格，我选了温馨风格。正在细化剧本…"). One sentence is enough. No tech jargon.

---

## Workflow: Manual Mode (Step-by-Step)

When `auto_pilot` is `false` in `metadata.json`, follow the original interactive workflow:

### Asynchronous Tasks
Whenever you start a task that takes time (creating, chatting, or generating videos):
1. Call the relevant API endpoint:
   - Create a session (`/api/openclaw/chat/session/create`)
   - Send a message (`/api/openclaw/chat/message/send`)
   - Confirm script & generate (`/api/openclaw/script/confirm_generate`)
2. Extract the `sessionId` from the response. Write it to `metadata.json` → `last_session_id`.
3. **Run `scripts/poll_session.py` in the background** with `--callback "<user_channel>"` and `--notify "<user_channel>"` (read `user_channel` from `metadata.json`). The callback wakes you up when the task is done; the notify sends a user-facing message.
4. When you receive a `[CREPAL_CALLBACK]` message, extract the `agentMsg` and present it to the user. **Wait for their input** before proceeding.

### Confirming Generation
**CRITICAL DISTINCTION:** Do not confuse confirming a script with confirming video generation.

- If the user says "continue", "looks good", or "confirm" in response to a **script outline**, you MUST use the regular `/api/openclaw/chat/message/send` endpoint.
- Only when the user explicitly requests to **"start generating the video"** OR the agent expressly asks "Should I start rendering/generating the final video now?" and the user agrees:
  1. **DO NOT** use `/api/openclaw/chat/message/send`.
  2. **INSTEAD**, use `/api/openclaw/script/confirm_generate` with the `sessionId`.
  3. Run `scripts/poll_session.py` in the background as usual.

---

## Workflow: Insufficient Credits & Recharge

If at any point the agent message (`agentMsg`) or any API response indicates insufficient credits (e.g., "insufficient credits", "please recharge"):

1. **IMMEDIATELY exit auto-pilot** (if active) and interact with the user directly.
2. Call the **Get Subscription Config** endpoint (`/api/openclaw/subscription/config`).
3. Parse the returned `subscriptions` list.
4. Present the subscription plans (price, description, privileges) and their corresponding `stripeLink` to the user so they can top up.
5. Once the user confirms they have recharged, resume the task using `/api/openclaw/chat/message/send` (e.g., sending "Recharged, continue" to the active `sessionId`).

---

## API Endpoints

- **Authentication:** All HTTP API calls to Crepal must include the `api_key` from `metadata.json`, as a Bearer token in the `Authorization` header: `Authorization: Bearer <api_key>`.
- **Base URL:** `https://crepal.ai`

### 1. Create Session
- **URL:** `POST https://crepal.ai/api/openclaw/chat/session/create`
- **Request Body:**
  ```json
  {
    "content": "Help me generate a short video script"
  }
  ```
- **Response Structure (Success 200):** Returns `sessionId`, `messageId`, and `status`.

### 2. Send Message
- **URL:** `POST https://crepal.ai/api/openclaw/chat/message/send`
- **Request Body:**
  ```json
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "content": "Continue improving this video script"
  }
  ```
- **Response Structure (Success 200):** Returns `sessionId`, `messageId`, and `status`.

### 3. Check Session Ended
- **URL:** `POST https://crepal.ai/api/openclaw/chat/session/check_end`
- **Description:** Checks if the session processing has ended. The included Python script `poll_session.py` automates polling this endpoint.
- **Request Body:** `{"sessionId": "..."}`
- **Response Structure (Success 200):**
  ```json
  {
    "data": {
      "sessionId": "string",
      "isEnded": true,
      "agentMsg": "Generated short video script content..."
    }
  }
  ```

### 4. Get Subscription Config
- **URL:** `POST https://crepal.ai/api/openclaw/subscription/config`
- **Description:** Get subscription tiers with price, period, description, privileges, and Stripe purchase links. No request body required.
- **Response Structure (Success 200):** Returns a `subscriptions` array containing `planType`, `price`, `description`, `privileges`, `stripeLink`, etc.

### 5. Get One-Time Products Config
- **URL:** `POST https://crepal.ai/api/openclaw/one_time_products/config`
- **Description:** Get one-time products (credits) with price, amount, and Stripe links. Subscription is required before purchase.
- **Response Structure (Success 200):** Returns a `canPurchase` boolean and a `products` array (containing `price`, `credits`, `stripeLink`, etc.). If `canPurchase` is false, a corresponding `reason` is also returned.

### 6. Confirm Script & Generate
- **URL:** `POST https://crepal.ai/api/openclaw/script/confirm_generate`
- **Description:** Confirm the current script and start rendering and generating the video. After calling this endpoint, you **must** run the `poll_session.py` script in the background to wait for the result.
- **Request Body:**
  ```json
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
  ```

---

## Resources

### `metadata.json`
Persistent configuration file. Read on startup, written whenever user config changes.

### `scripts/poll_session.py`
A polling script that pings the `check_end` endpoint every 5 seconds until `isEnded` becomes `true`. Features:
- **`--callback`** — Sends a `[CREPAL_CALLBACK]` message into the conversation to wake up the AI agent (critical for auto-pilot).
- **`--notify`** — Sends a user-facing notification when the task is done.
- **Smart openclaw discovery** — Finds the `openclaw` executable via PATH, NVM, common locations.

**Where does `<USER_CHANNEL>` come from?**
Read `user_channel` from `metadata.json`. Example values: `telegram:123456789`, `discord:987654321`, `slack:C0123ABCDEF`.

**Usage — Auto-Pilot (callback ONLY, no --notify):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "<USER_CHANNEL>"
```

**Usage — Auto-Pilot final generate step (callback + notify):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "<USER_CHANNEL>" --notify "<USER_CHANNEL>"
```

**Usage — Manual mode (callback + notify):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "<USER_CHANNEL>" --notify "<USER_CHANNEL>"
```

**With explicit openclaw path:**
```bash
OPENCLAW_BIN=$(which openclaw)
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "<USER_CHANNEL>" --openclaw-path "$OPENCLAW_BIN"
```
