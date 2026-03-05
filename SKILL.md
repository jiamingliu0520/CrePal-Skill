---
name: crepal-video-creator
description: "Crepal AI Video Creator — connects to Crepal's cloud AI Video Agent to create videos on behalf of the user. Use this skill when users want to create AI-generated videos, short films, or any video content. This skill handles session management, message relay, and balance monitoring through the Crepal API."
metadata:
---

# Crepal AI Video Creator

This skill acts as a bridge between the user and Crepal's cloud-based AI Video Agent. When a user wants to create an AI video, OpenClaw uses this skill to:

1. Create a task session on the Crepal cloud service
2. Relay progress messages (text, images, video links) from the cloud agent back to the user
3. Handle balance issues and guide the user through top-up if needed

All video generation work happens on Crepal's cloud servers. OpenClaw's role is to manage the communication.

---

## Step 1 — Check API Key

Before doing anything, read `metadata.json` (located in this skill's root directory) and check the `api_key` field.

**If `api_key` is empty or missing:**

Tell the user:

> You haven't configured your Crepal API Key yet. Please click the link below to get your API Key, then send it to me:
> https://www.crepal.ai/api_key

Once the user provides the key, write it into `metadata.json`:

```json
{
  "api_key": "<user_provided_key>",
  "base_url": "https://crepal.pro",
  "api_key_url": "https://www.crepal.ai/api_key"
}
```

**If `api_key` is present**, proceed to Step 2.

---

## Step 2 — Create a Session

Collect the user's video creation request as a `query` string. Then run:

```bash
python scripts/create_session.py <base_url> <api_key> "<query>"
```

- `base_url` and `api_key` come from `metadata.json`
- `query` is the user's video request in their own words

**On success** (exit code 0): the script prints JSON to stdout containing `sessionId`. Save this value.

**On exit code 2** (insufficient balance): stderr contains `INSUFFICIENT_BALANCE|<payment_url>`. Jump to the "Insufficient Balance" section below.

**On exit code 1** (other error): report the error to the user.

---

## Step 3 — Poll for Messages

Start the polling script in the background:

```bash
python scripts/poll_session.py <base_url> <api_key> <session_id> --notify <openclaw_target>
```

- `session_id` is from Step 2
- `--notify` is the OpenClaw target ID for message delivery

This script runs continuously and handles everything automatically:

- **New text messages** from the cloud agent are forwarded to the user via `openclaw message send`
- **Media messages** (images, videos) include the media URL alongside the text
- **Session end**: the script sends a completion notification and exits
- **Insufficient balance**: the script sends a top-up prompt with the Stripe payment link and exits with code 2

You do not need to do anything while the script is running. It will forward all messages on its own.

---

## Insufficient Balance

When balance is insufficient (detected during session creation or polling), the user receives a message like:

> ⚠️ Your Crepal account balance is insufficient to continue the current task.
> Please click the link below to top up: <stripe_payment_url>
> After topping up, tell me "continue" and I will notify the cloud service to resume your task.

**When the user says they have topped up and want to continue**, do the following:

1. Call the resume script:

```bash
python scripts/resume_session.py <base_url> <api_key> <session_id>
```

2. If successful, restart the polling script:

```bash
python scripts/poll_session.py <base_url> <api_key> <session_id> --notify <openclaw_target>
```

3. Tell the user the task has resumed.

---

## Script Reference

| Script | Purpose | Key Args |
|--------|---------|----------|
| `scripts/create_session.py` | Create a new session | `base_url`, `api_key`, `query` |
| `scripts/poll_session.py` | Poll & forward messages | `base_url`, `api_key`, `session_id`, `--notify` |
| `scripts/resume_session.py` | Resume after top-up | `base_url`, `api_key`, `session_id` |

All scripts use only Python standard library (`urllib`, `json`, `subprocess`) — no pip dependencies required.

---

## API Endpoints (Placeholder)

These are placeholder paths. Replace with actual endpoints when available.

| Action | Method | Path |
|--------|--------|------|
| Create session | POST | `/api/session/create` |
| Poll messages | POST | `/api/session/poll` |
| Resume session | POST | `/api/session/resume` |
