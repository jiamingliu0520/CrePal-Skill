---
name: crepal
description: A one-stop AI video editing and generation tool. Use this skill when the user wants to generate, edit, or manipulate videos using the Crepal API. The first step for any user is to go to https://crepal.pro to obtain an API access token, which must be stored for authenticating subsequent HTTP API calls.
---

# Crepal

## Overview

Crepal is a powerful one-stop AI video editing and generation tool. This skill guides the AI and the user through the process of setting up and using the Crepal API for video-related tasks.

## Initial Setup & Authentication

Before using any Crepal API endpoints, the user must obtain an API access token.

1.  **Direct the User:** Instruct the user to visit [https://crepal.pro](https://crepal.pro) to register/login and generate their API access token.
2.  **Store the Token:** Once the user provides the token, store it securely so it can be included in the `Authorization` header of subsequent HTTP requests.

## Workflow: Creating or Sending Messages

Whenever you start a task to generate or edit a video via chat:
1. Create a session (`/api/openclaw/chat/session/create`) or send a message to an existing session (`/api/openclaw/chat/message/send`).
2. Extract the `sessionId` from the response.
3. **Run `scripts/poll_session.py` in the background** to poll the session status. Use `exec` with `background=true` so you aren't blocked, and pass `--notify "user:<user_id>"` so the script automatically sends a message to the user when the video is ready.

## API Endpoints

- **Authentication:** All HTTP API calls to Crepal must include the obtained access token, typically as a Bearer token in the `Authorization` header: `Authorization: Bearer <TOKEN>`.

### 1. 创建会话 (Create Session)
- **URL:** `POST https://crepal.pro/api/openclaw/chat/session/create`
- **Request Body:**
  ```json
  {
    "content": "帮我生成一个短视频脚本"
  }
  ```
- **Response Structure (Success 200):** Returns `sessionId`, `messageId`, and `status`.

### 2. 发送消息 (Send Message)
- **URL:** `POST https://crepal.pro/api/openclaw/chat/message/send`
- **Request Body:**
  ```json
  {
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "content": "继续完善这个视频脚本"
  }
  ```
- **Response Structure (Success 200):** Returns `sessionId`, `messageId`, and `status`.

### 3. 查询会话是否停止 (Check Session Ended)
- **URL:** `POST https://crepal.pro/api/openclaw/chat/session/check_end`
- **Description:** Checks if the session processing has ended. The included Python script `poll_session.py` automates polling this endpoint.
- **Request Body:** `{"sessionId": "..."}`
- **Response Structure (Success 200):**
  ```json
  {
    "data": {
      "sessionId": "string",
      "isEnded": true,
      "agentMsg": "生成的短视频脚本内容..."
    }
  }
  ```

## Resources

### scripts/

#### `poll_session.py`
A polling script that takes the base URL, token, and session ID, and pings the `check_end` endpoint every 5 seconds. It exits and prints the final `agentMsg` only when `isEnded` becomes `true`.

**Usage (Run in Background):**
```bash
python3 scripts/poll_session.py "https://crepal.pro" "<TOKEN>" "<SESSION_ID>" --notify "user:<USER_ID>" &
```