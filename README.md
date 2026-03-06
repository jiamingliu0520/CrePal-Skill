<p align="center">
  <img src="https://www.crepal.ai/logo.png" alt="CrePal" width="120">
</p>

<h1 align="center">CrePal — AI Video Agent Skill</h1>

<p align="center">
  <strong>A one-stop AI video editing and generation tool. Connect your personal AI assistant to CrePal's cloud API.</strong>
</p>

<p align="center">
  <a href="https://crepal.ai"><img src="https://img.shields.io/badge/Website-crepal.ai-0A0A0A?style=for-the-badge&logo=safari&logoColor=white" alt="Website"></a>
  <a href="https://crepal.ai"><img src="https://img.shields.io/badge/Get_API_Token-→-6C63FF?style=for-the-badge" alt="API Token"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
</p>

<br>

## What is CrePal?

**CrePal** is a one-stop AI video editing and generation tool. This Skill guides the AI and the user through setting up and using the CrePal API for script writing, video generation, and confirm-and-render workflows.

Before using it, get an **API access token** by visiting [crepal.ai](https://crepal.ai) to register or log in. Store the token securely and send it in the `Authorization: Bearer <TOKEN>` header for all subsequent requests.

<br>

## Workflow Overview

### Asynchronous tasks (create session, send message, confirm script & generate)

When starting a task that takes time (creating a session, chatting, or generating video):

1. Call the relevant API:
   - Create session: `POST https://crepal.ai/api/openclaw/chat/session/create`
   - Send message: `POST https://crepal.ai/api/openclaw/chat/message/send`
   - Confirm script & generate: `POST https://crepal.ai/api/openclaw/script/confirm_generate`
2. Extract the `sessionId` from the response.
3. **Run `scripts/poll_session.py` in the background** to poll session status. Use `exec` with `background=true` so you aren't blocked, and pass `--notify "user:<user_id>"` so the script notifies the user when the task is complete.

### Insufficient credits & recharge

If the API response or agent message indicates insufficient credits (e.g. "insufficient credits", "please recharge"):

1. **Immediately** call the **Get Subscription Config** endpoint: `POST https://crepal.ai/api/openclaw/subscription/config`.
2. Parse the returned `subscriptions` list and present the plans (price, description, privileges) and their `stripeLink` to the user for top-up.
3. Once the user confirms they have recharged, resume the task via `POST https://crepal.ai/api/openclaw/chat/message/send` (e.g. send "Recharged, continue" to the active `sessionId`).

<br>

## Quick Start

### 1. Get your API Token

Visit [crepal.ai](https://crepal.ai) to register or log in and generate your API access token.

### 2. Install the Skill

**One-line install (recommended):** The script installs to `~/.openclaw/skills/crepal`. OpenClaw will pick it up automatically — no copying or extra configuration.

```bash
curl -fsSL https://raw.githubusercontent.com/jiamingliu0520/CrePal-Skill/main/install.sh | bash
```

Or clone into the same path manually:

```bash
git clone https://github.com/jiamingliu0520/CrePal-Skill.git ~/.openclaw/skills/crepal
```

### 3. Configure

The first time you ask your agent to create a video, it will prompt you for the API token. Provide it and the agent will store it securely and use `Authorization: Bearer <TOKEN>` for subsequent requests.

### 4. Create a video

Describe what you want in natural language, for example:

> *"Help me generate a 30-second product teaser script."*

The agent will create a session, send messages, and when needed run `poll_session.py` in the background, notifying you via OpenClaw when the task is done.

<br>

## API Endpoints Summary

| Action | Method | Endpoint |
|--------|--------|----------|
| Create session | `POST` | `https://crepal.ai/api/openclaw/chat/session/create` |
| Send message | `POST` | `https://crepal.ai/api/openclaw/chat/message/send` |
| Check session ended | `POST` | `https://crepal.ai/api/openclaw/chat/session/check_end` |
| Get subscription config (plans & Stripe links) | `POST` | `https://crepal.ai/api/openclaw/subscription/config` |
| Get one-time products config (credits, etc.) | `POST` | `https://crepal.ai/api/openclaw/one_time_products/config` |
| Confirm script & generate video | `POST` | `https://crepal.ai/api/openclaw/script/confirm_generate` |

All requests require a valid token in the header: `Authorization: Bearer <TOKEN>`.

See [SKILL.md](SKILL.md) for request/response details.

<br>

## Project Structure

```
crepal-video-creator/
├── SKILL.md              # Skill definition (read by OpenClaw / AI)
├── install.sh            # One-line installer (default: ~/.openclaw/skills/crepal; set CREPAL_SKILL_DIR to override)
├── README.md
└── scripts/
    └── poll_session.py   # Poll session status; optionally notify user when done
```

### `scripts/poll_session.py`

Polls the `check_end` endpoint every 5 seconds and exits when `isEnded` is `true`, printing the final `agentMsg`. Can optionally notify the user via OpenClaw.

**Usage (run in background):**

```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --notify "user:<USER_ID>" &
```

<br>

## Requirements

- **Python 3.8+** (standard library only — no third-party packages)
- **OpenClaw** installed and configured ([Getting started](https://docs.openclaw.ai/start/getting-started))
- **CrePal API token** ([Get one at crepal.ai](https://crepal.ai))

<br>

## FAQ

**Q: How long does video generation take?**  
It depends on complexity and queue. You can use polling or `poll_session.py` to get notified when the task is done.

**Q: What if I run out of credits?**  
The agent will call the subscription config endpoint and show you the plans and Stripe top-up links. After recharging, send "Recharged, continue" to the current session to resume.

**Q: Can I use this without OpenClaw?**  
Yes. `poll_session.py` is a standalone script you can run from the command line. The full experience (session creation, messaging, automatic notification) works with OpenClaw and this Skill.

<br>

## License

[MIT](LICENSE)

<br>

<p align="center">
  <sub>Built by <a href="https://crepal.ai">CrePal</a> — One-stop AI video creation.</sub>
</p>
