---
name: crepal
description: A one-stop AI video editing and generation tool. Use this skill when the user wants to generate, edit, or manipulate videos using the Crepal API. Supports fully automated "auto-pilot" mode that completes the entire video creation workflow without user intervention.
---

# Crepal

## Overview

Crepal is a powerful one-stop AI video editing and generation tool. This skill guides the AI and the user through the process of setting up and using the Crepal API for video-related tasks.

---

## Persistent Configuration: `metadata.json`

This skill stores user configuration in `metadata.json` (located in the skill root directory alongside this file).

**Structure:**
```json
{
  "api_key": "",
  "auto_pilot": false,
  "last_session_id": ""
}
```

| Field | Description |
|-------|-------------|
| `api_key` | The user's CrePal API access token. Used in `Authorization: Bearer <api_key>` header. |
| `auto_pilot` | Whether the user prefers auto-pilot mode (see below). Persisted across sessions. |
| `last_session_id` | The most recent session ID, for easy resumption. |

### Reading & Writing `metadata.json`

- **On every skill invocation**, first read `metadata.json` to check if `api_key` is already stored.
- If `api_key` is empty or missing, prompt the user to provide it (direct them to [crepal.ai](https://crepal.ai) to register/login).
- Once the user provides the token, **write it back** to `metadata.json` immediately so it persists for future sessions.
- Update `last_session_id` whenever a new session is created.
- Update `auto_pilot` when the user expresses a preference.

---

## Initial Setup & First-Run Experience

When this skill is first invoked (i.e. `api_key` in `metadata.json` is empty):

1. **Welcome the user:** Introduce CrePal as a one-stop AI video creation tool.
2. **Direct the user to get an API token:** Instruct them to visit [https://crepal.ai](https://crepal.ai) to register/login and generate their API access token.
3. **Store the token:** Once the user provides the token, write it to `metadata.json` → `api_key`.
4. **Ask about auto-pilot:** Proactively ask the user:

   > "Would you like me to use **auto-pilot mode**? In this mode, I'll automatically handle all of CrePal's questions and confirmations, completing the entire video from script to final render in one go — you just describe what you want and sit back. Otherwise, I'll pause at each step for your review. Which do you prefer?"

5. **Store the preference:** Write the user's choice to `metadata.json` → `auto_pilot` (`true` or `false`).

---

## Workflow: Auto-Pilot Mode (Full Automation)

When `auto_pilot` is `true` in `metadata.json`, OR the user explicitly asks for full automation:

The agent MUST complete the **entire** video creation pipeline automatically, without pausing for user input at intermediate steps.

### ⚠️ CRITICAL RULE: NEVER LEAVE AN `agentMsg` UNANSWERED

**This is the #1 rule of auto-pilot mode.** Every time you receive an `agentMsg` from CrePal via polling, you MUST take action on it — either reply via `message/send`, or trigger `confirm_generate`. There is NO scenario in auto-pilot where you read an `agentMsg` and then stop or wait for the user. If you find yourself about to present an `agentMsg` to the user and wait — STOP — that is wrong in auto-pilot mode. You must reply yourself and keep the loop going.

### How the Callback Wake-Up Works

`poll_session.py` supports a `--callback` parameter. When the script detects `isEnded=true`, it uses `openclaw message send` to inject a `[CREPAL_CALLBACK]` message back into the conversation. This message triggers OpenClaw's message-receive pipeline, **waking up the AI agent** so it can immediately process the `agentMsg` and continue the auto-pilot loop — no human nudge required.

**IMPORTANT:** In auto-pilot mode, you MUST always pass `--callback "user:<user_id>"` when running `poll_session.py`. Without it, the script only prints to stdout and the AI agent will NOT wake up to continue.

### Step 1 — Create Session
1. Call `POST https://crepal.ai/api/openclaw/chat/session/create` with the user's video description as `content`.
2. Extract `sessionId` from the response. Write it to `metadata.json` → `last_session_id`.
3. Run `scripts/poll_session.py` in the background **with `--callback "user:<user_id>"`** so the script will wake you up when CrePal responds.
4. **You may now yield control.** When the polling completes, a `[CREPAL_CALLBACK]` message will appear in the conversation containing the `agentMsg`. This is your wake-up signal.
5. **→ When you receive a `[CREPAL_CALLBACK]` message, immediately proceed to the Decision Tree below.**

### Step 2 — Decision Tree (MANDATORY on every `[CREPAL_CALLBACK]`)

**Every time** you receive a `[CREPAL_CALLBACK]` message, extract the `agentMsg` from it and classify it. Go through this checklist in order:

| # | Condition | Action |
|---|-----------|--------|
| A | `agentMsg` contains "insufficient credits" / "please recharge" / credit-related errors | **EXIT auto-pilot.** Follow the "Insufficient Credits & Recharge" workflow. |
| B | `agentMsg` indicates the script is finalized and ready for video generation (e.g. contains words like "generate the video", "start rendering", "ready to produce", "shall I generate", or presents a final script summary with no further questions) | **Go to Step 3 — Confirm & Generate.** |
| C | `agentMsg` asks a question, requests a choice, or presents options (e.g. "What style?", "Which tone?", "Do you prefer A or B?") | **Compose a reply** using your AI judgment based on the user's original description, then **send it** via `message/send`. |
| D | `agentMsg` presents a script draft / outline and asks for confirmation or feedback (e.g. "Here's the script, what do you think?", "Does this look good?") | **Reply with an affirmative** like "Looks great, please continue" or "Confirmed, go ahead" via `message/send`. |
| E | `agentMsg` is any other content that doesn't clearly fit above categories | **Default: Reply with** "Looks good, please continue" via `message/send`. Never stay silent. |

**After sending a reply (cases C, D, E):**
1. Run `scripts/poll_session.py` again in the background **with `--callback`** to poll this new round.
2. **Yield control and wait** for the next `[CREPAL_CALLBACK]` message.
3. **→ When callback arrives, return to this Decision Tree. Repeat until you reach case A or B.**

### Step 3 — Confirm & Generate
1. Call `POST https://crepal.ai/api/openclaw/script/confirm_generate` with the `sessionId`.
2. Run `scripts/poll_session.py` in the background with `--callback` and `--notify` to track generation progress, wake up the agent, and notify the user when done.
3. **Report to the user** that video generation has started, and they will be notified when it's complete.

### Auto-Pilot Safety Rules
- **NEVER leave an `agentMsg` without a response.** If in doubt, reply "Looks good, please continue".
- **NEVER skip the `confirm_generate` step.** The auto-reply loop handles script refinement only. Video generation MUST go through the dedicated `/script/confirm_generate` endpoint.
- **If credits are insufficient** at any point, **immediately exit auto-pilot** and follow the "Insufficient Credits & Recharge" workflow below.
- **If an API error occurs**, stop and report to the user with the error details.
- **Keep the user informed** with brief progress updates after each round (e.g. "Round 2: CrePal asked about style, I chose 'modern and energetic'. Waiting for next response...").

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
3. **Run `scripts/poll_session.py` in the background** with `--callback "user:<user_id>"` and `--notify "user:<user_id>"`. The callback wakes you up when the task is done; the notify sends a user-facing message.
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

**Usage — Auto-Pilot (callback + notify):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "user:<USER_ID>" --notify "user:<USER_ID>"
```

**Usage — Manual mode (notify only):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "user:<USER_ID>" --notify "user:<USER_ID>"
```

**With explicit openclaw path:**
```bash
OPENCLAW_BIN=$(which openclaw)
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "user:<USER_ID>" --openclaw-path "$OPENCLAW_BIN"
```
