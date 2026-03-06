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

Before using it, get an **API access token** by visiting [crepal.ai](https://crepal.ai) to register or log in. The token is stored in `metadata.json` and sent in the `Authorization: Bearer <TOKEN>` header for all subsequent requests.

<br>

## ✨ Key Features

### 🤖 Auto-Pilot Mode

After first-time setup, the agent will ask if you want to enable **auto-pilot mode**. When enabled:

- You just describe what video you want in natural language
- The agent **automatically handles all of CrePal's questions** — choosing styles, confirming scripts, making sensible decisions
- The entire flow from script creation to final video rendering runs **in one shot**
- You get notified when the video is done

### 🔧 Manual Mode

Prefer more control? In manual mode, the agent pauses at each step and presents CrePal's questions/drafts for your review before proceeding.

### 💾 Persistent Configuration

User settings (API key, messaging channel, auto-pilot preference, last session) are stored in `metadata.json` — no need to re-enter your info every time.

<br>

## Workflow Overview

### Auto-Pilot (fully automated)

```
You: "Make me a 30-second product teaser for a coffee brand"
  ↓
Agent: Creates session → Auto-answers CrePal's questions →
       Confirms script → Triggers video generation → Notifies you when done ✅
```

### Manual (step-by-step)

```
You: "Make me a 30-second product teaser for a coffee brand"
  ↓
Agent: Creates session → Shows you CrePal's questions →
       Waits for your input → Sends your reply → ... →
       Asks if you want to generate → Triggers generation → Notifies you ✅
```

### Insufficient credits & recharge

If the API response indicates insufficient credits:

1. **Immediately** calls the **Get Subscription Config** endpoint: `POST https://crepal.ai/api/openclaw/subscription/config`.
2. Presents the plans (price, description, privileges) and `stripeLink` to you for top-up.
3. Once you confirm recharge, resumes the task.

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

### 3. First-Run Setup

The first time you invoke the skill, the agent will:
1. Ask for your **messaging channel address** (e.g. Telegram chat ID) so it can send you callbacks and notifications
2. Ask for your **CrePal API token** and store it in `metadata.json`
3. Ask whether you prefer **auto-pilot** or **manual** mode
4. Save all your settings for future sessions

### 4. Create a video

Describe what you want in natural language, for example:

> *"Help me generate a 30-second product teaser script."*

The agent will handle the rest based on your mode preference.

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
├── metadata.json         # Persistent config (API key, preferences)
├── install.sh            # One-line installer
├── README.md
└── scripts/
    └── poll_session.py   # Poll session status; smart openclaw discovery; notify user when done
```

### `metadata.json`

Stores user configuration persistently:
- `api_key` — CrePal API access token
- `user_channel` — User's messaging channel address (e.g. `telegram:123456789`), used to send callbacks and notifications
- `auto_pilot` — Whether auto-pilot mode is enabled
- `last_session_id` — Most recent session ID for easy resumption

### `scripts/poll_session.py`

Polls the `check_end` endpoint every 5 seconds and exits when `isEnded` is `true`. Features:
- **Callback wake-up** (`--callback`) — Injects a `[CREPAL_CALLBACK]` message into the conversation to wake up the AI agent, enabling true auto-pilot without human intervention
- **User notification** (`--notify`) — Sends a user-facing notification when the task is done
- **Smart openclaw discovery** — Finds the `openclaw` executable via PATH, NVM, common locations

**Usage — Auto-Pilot (callback only, no --notify during intermediate rounds):**

```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "telegram:123456789"
```

**Usage — Final generate step or Manual mode (callback + notify):**

```bash
python3 scripts/poll_session.py "https://crepal.ai" "<TOKEN>" "<SESSION_ID>" --callback "telegram:123456789" --notify "telegram:123456789"
```

<br>

## Requirements

- **Python 3.8+** (standard library only — no third-party packages)
- **OpenClaw** installed and configured ([Getting started](https://docs.openclaw.ai/start/getting-started))
- **CrePal API token** ([Get one at crepal.ai](https://crepal.ai))

<br>

## FAQ

**Q: How long does video generation take?**  
It depends on complexity and queue. The `poll_session.py` script monitors progress and notifies you when done.

**Q: What if I run out of credits?**  
The agent will call the subscription config endpoint and show you the plans and Stripe top-up links. After recharging, the task resumes automatically.

**Q: Can I switch between auto-pilot and manual mode?**  
Yes! Just tell the agent "switch to manual mode" or "switch to auto-pilot". Your preference is saved in `metadata.json`.

**Q: Can I use this without OpenClaw?**  
Yes. `poll_session.py` is a standalone script you can run from the command line. The full experience (session creation, messaging, automatic notification) works best with OpenClaw and this Skill.

<br>

## License

[MIT](LICENSE)

<br>

<p align="center">
  <sub>Built by <a href="https://crepal.ai">CrePal</a> — One-stop AI video creation.</sub>
</p>
