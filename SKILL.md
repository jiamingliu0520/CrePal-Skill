---
name: crepal
description: A one-stop AI video editing and generation tool. Use this skill when the user wants to generate, edit, or manipulate videos using the Crepal API. The first step for any user is to go to https://crepal.ai to obtain an API access token, which must be stored for authenticating subsequent HTTP API calls.
---

# Crepal

## Overview

Crepal is a powerful one-stop AI video editing and generation tool. This skill guides the AI and the user through the process of setting up and using the Crepal API for video-related tasks.

## Initial Setup & Authentication

Before using any Crepal API endpoints, the user must obtain an API access token.

1.  **Direct the User:** Instruct the user to visit [https://crepal.ai](https://crepal.ai) to register/login and generate their API access token.
2.  **Store the Token:** Once the user provides the token, store it securely so it can be included in the `Authorization` header of subsequent HTTP requests.

## Workflow: Asynchronous Tasks

Whenever you start a task that takes time (creating, chatting, or generating videos):
1. Call the relevant API endpoint:
   - Create a session (`/api/openclaw/chat/session/create`)
   - Send a message (`/api/openclaw/chat/message/send`)
   - Confirm script & generate (`/api/openclaw/script/confirm_generate`)
2. Extract the `sessionId` from the response (or from your existing context).
3. **Run `scripts/poll_session.py` in the background** to poll the session status. Use `exec` with `background=true` so you aren't blocked, and pass `--notify "user:<user_id>"` so the script automatically sends a message to the user when the task is complete.

## Workflow: Confirming Generation

When the API (via the polling script) returns an `agentMsg` asking the user for confirmation to start generating the video (e.g., "Please confirm whether to start generating the video"), and the user replies with an affirmative response (e.g., "yes", "confirm"):
1. **DO NOT** use the `/api/openclaw/chat/message/send` endpoint.
2. **INSTEAD**, use the `/api/openclaw/script/confirm_generate` endpoint with the `sessionId` to trigger the actual video generation.
3. Extract the `sessionId` from the response and run `scripts/poll_session.py` in the background as usual to track the generation progress.

## Workflow: Insufficient Credits & Recharge

If at any point the agent message (`agentMsg`) or any API response indicates insufficient credits (e.g., "insufficient credits", "please recharge"):
1. You **MUST IMMEDIATELY** call the **Get Subscription Config** endpoint (`/api/openclaw/subscription/config`).
2. Parse the returned `subscriptions` list.
3. Present the subscription plans (price, description, privileges) and their corresponding `stripeLink` to the user so they can top up.
4. Once the user confirms they have recharged, you can resume their task using `/api/openclaw/chat/message/send` (e.g., sending "Recharged, continue" to the active `sessionId`).

## API Endpoints

- **Authentication:** All HTTP API calls to Crepal must include the obtained access token, typically as a Bearer token in the `Authorization` header: `Authorization: Bearer <TOKEN>`.

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

## Resources

### scripts/

#### `poll_session.py`
A polling script that takes the base URL, token, and session ID, and pings the `check_end` endpoint every 5 seconds. It exits and prints the final `agentMsg` only when `isEnded` becomes `true`.

**Usage (Run in Background):**
```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --notify "user:<USER_ID>" &
```