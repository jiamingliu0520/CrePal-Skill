<p align="center">
  <img src="https://www.crepal.ai/logo.png" alt="CrePal" width="120">
</p>

<h1 align="center">CrePal — AI Video Agent Skill</h1>

<p align="center">
  <strong>Give your personal AI agent the power to create videos, end to end.</strong>
</p>

<p align="center">
  <a href="https://www.crepal.ai"><img src="https://img.shields.io/badge/Website-crepal.ai-0A0A0A?style=for-the-badge&logo=safari&logoColor=white" alt="Website"></a>
  <a href="https://www.crepal.ai/api_key"><img src="https://img.shields.io/badge/Get_API_Key-→-6C63FF?style=for-the-badge" alt="API Key"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"></a>
</p>

<br>

## What is CrePal?

**CrePal** is a general-purpose AI video agent that lives in the cloud. It can orchestrate computers, phones, and generative models to produce complete videos autonomously — from script and storyboard all the way through rendering and export.

By installing the **CrePal Skill**, you connect your personal AI assistant (via [OpenClaw](https://openclaw.ai)) to CrePal's cloud agent. Once connected, a single natural-language request is all it takes:

> *"Make a 30-second product launch teaser for our new headphones."*

CrePal handles the rest — planning the narrative, designing characters, generating shots, composing audio, and delivering the final cut — while streaming progress updates back to you in real time.

<br>

## How It Works

```
You ──→ OpenClaw ──→ CrePal Skill ──→ CrePal Cloud Agent
                                          │
                                          ├─ Script & storyboard
                                          ├─ Character & scene design
                                          ├─ Video generation (Sora, Runway, Kling, Pika …)
                                          ├─ Audio (voiceover, music, SFX)
                                          └─ Editing & final render
                                          │
                  You ←── OpenClaw ←──────┘  (real-time progress + deliverables)
```

1. **You describe what you want** — in plain language, any language.
2. **OpenClaw reads the CrePal Skill** and creates a session on the cloud agent.
3. **The cloud agent works autonomously** — scripting, generating, composing.
4. **Progress streams back to you** — text updates, preview images, video links — delivered through whichever channel you use (WhatsApp, Telegram, Slack, Discord, etc.).
5. **You receive the finished video** when the session completes.

<br>

## Quick Start

### 1. Get your API Key

Visit **[crepal.ai/api_key](https://www.crepal.ai/api_key)** to generate a personal API key.

### 2. Install the Skill

Clone this repository into your OpenClaw skills directory:

```bash
git clone https://github.com/jiamingliu0520/CrePal-Skill.git \
  ~/.openclaw/workspace/skills/crepal-video-creator
```

Or run the install script:

```bash
bash install.sh
```

### 3. Configure

When you first ask your agent to create a video, it will prompt you for the API key. Paste it in, and you're ready to go.

The key is stored locally in `metadata.json` (git-ignored, never uploaded).

### 4. Create a Video

Just tell your agent:

> *"Create a 60-second cinematic travel video of Tokyo at night."*

That's it. Sit back and watch the progress roll in.

<br>

## Features

| Capability | Description |
|---|---|
| **End-to-end automation** | From concept to final cut — no manual steps required. |
| **Real-time streaming** | Text updates, images, and video links delivered as the agent works. |
| **Multi-tool orchestration** | Leverages Sora, RunwayML, Kling, Pika, ElevenLabs, and more. |
| **Balance monitoring** | Automatic alerts when credits run low, with a one-click top-up link. |
| **Session resume** | Top up and say "continue" — the agent picks up right where it left off. |
| **Zero dependencies** | Pure Python standard library. No `pip install` needed. |

<br>

## Project Structure

```
crepal-video-creator/
├── SKILL.md                   # Skill definition (read by OpenClaw)
├── metadata.json              # Local config: API key + base URL (git-ignored)
├── install.sh                 # One-line installer
├── README.md
└── scripts/
    ├── create_session.py      # Create a new cloud session
    ├── poll_session.py        # Poll for messages & forward to OpenClaw
    └── resume_session.py      # Resume a session after balance top-up
```

<br>

## API Endpoints

> **Note:** These are placeholder paths. They will be updated when the production API is finalized.

| Action | Method | Endpoint |
|---|---|---|
| Create session | `POST` | `/api/session/create` |
| Poll messages | `POST` | `/api/session/poll` |
| Resume session | `POST` | `/api/session/resume` |

All requests require a valid API key passed via the `Authorization: Bearer <key>` header.

<br>

## Requirements

- **Python 3.8+** (standard library only — no third-party packages)
- **OpenClaw** installed and configured ([Getting started](https://docs.openclaw.ai/start/getting-started))
- A **CrePal API key** ([Get one here](https://www.crepal.ai/api_key))

<br>

## FAQ

**Q: How long does a video take?**
It depends on complexity. A simple 15-second clip may take a few minutes; a multi-scene cinematic piece can take longer. You'll see real-time progress throughout.

**Q: What happens if I run out of credits?**
The agent pauses and sends you a Stripe top-up link. After payment, just say "continue" and it resumes automatically.

**Q: Can I use this without OpenClaw?**
The scripts are standalone Python — you can call them directly from the command line. But the full experience (real-time message relay, multi-channel delivery) requires OpenClaw.

**Q: What video generation models are supported?**
CrePal's cloud agent selects the best model for each shot. Currently supported: Sora, RunwayML Gen-3, Kling, Pika 2.0, Hailuo, and more.

<br>

## License

[MIT](LICENSE)

<br>

<p align="center">
  <sub>Built by <a href="https://www.crepal.ai">CrePal</a> — Creative AI, on autopilot.</sub>
</p>
