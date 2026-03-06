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

The agent MUST complete the **entire** video creation pipeline automatically, without pausing for user input at intermediate steps. The flow is:

### Step 1 — Create Session
1. Call `POST https://crepal.ai/api/openclaw/chat/session/create` with the user's video description as `content`.
2. Extract `sessionId` from the response. Write it to `metadata.json` → `last_session_id`.
3. Run `scripts/poll_session.py` in the background to poll until the session ends.
4. When polling completes, read the `agentMsg` from the output.

### Step 2 — Auto-Reply Loop
5. **Read the `agentMsg`** returned by CrePal. This is typically a question or a script draft.
6. **Use your AI judgment** to compose an appropriate reply. For example:
   - If CrePal asks about video style/tone → choose a reasonable option based on the user's original description.
   - If CrePal presents a script draft and asks for confirmation → reply with "Looks good, please continue" or similar affirmative.
   - If CrePal asks for specific details the user didn't provide → make a sensible default choice and proceed.
7. Call `POST https://crepal.ai/api/openclaw/chat/message/send` with the `sessionId` and your auto-generated reply as `content`.
8. Run `scripts/poll_session.py` again in the background to poll this new round.
9. When polling completes, read the new `agentMsg`.
10. **Repeat steps 5–9** until CrePal indicates the script is finalized and ready for video generation.

### Step 3 — Confirm & Generate
11. When CrePal's `agentMsg` indicates the script is complete and ready for rendering (e.g. mentions "generate", "render", "start producing"):
    - Call `POST https://crepal.ai/api/openclaw/script/confirm_generate` with the `sessionId`.
    - Run `scripts/poll_session.py` in the background with `--notify` to track generation progress and notify the user when done.
12. **Report to the user** that video generation has started, and they will be notified when it's complete.

### Important Auto-Pilot Rules
- **Never skip the confirm_generate step.** The auto-reply loop handles script refinement only. Video generation must still go through the dedicated endpoint.
- **If credits are insufficient** at any point, **immediately exit auto-pilot** and follow the "Insufficient Credits & Recharge" workflow below.
- **If an error occurs**, stop and report to the user with the error details.
- **Keep the user informed** with brief progress updates (e.g. "CrePal asked about style, I chose 'modern and energetic'. Now refining the script...").

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
3. **Run `scripts/poll_session.py` in the background** to poll the session status. Use `exec` with `background=true` so you aren't blocked, and pass `--notify "user:<user_id>"` so the script automatically sends a message to the user when the task is complete.
4. When polling completes, present the `agentMsg` to the user and **wait for their input** before proceeding.

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
A polling script that takes the base URL, token, and session ID, and pings the `check_end` endpoint every 5 seconds. It exits and prints the final `agentMsg` only when `isEnded` becomes `true`. Features smart `openclaw` executable discovery for reliable notifications.

**Usage (Run in Background):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --notify "user:<USER_ID>"
```

**With explicit openclaw path:**
```bash
OPENCLAW_BIN=$(which openclaw)
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --notify "user:<USER_ID>" --openclaw-path "$OPENCLAW_BIN"
```
