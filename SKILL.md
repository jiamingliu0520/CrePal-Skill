---
name: ai-video-creator
description: "End-to-end AI video creation workflow — from concept to final cut. Use when users want to create AI videos, need help with script planning, character design, storyboarding, video generation, or editing and export. Also applicable when working with tools like Sora, RunwayML, Kling, Pika, etc. This Skill has a built-in self-improvement mechanism that continuously accumulates directing tips, image prompt techniques, and video prompt techniques."
metadata:
---

# AI Video Creation Skill

Turn any idea into a polished AI-generated video. Five phases + a continuously growing knowledge base.

---

## Phase 1 — Concept Planning & Script

**Goal**: Lock down the creative direction and write a timecoded script before touching any tools.

### Creative Brief (Fill This Out First)

```
Concept / Core Message:
Target Platform:      Douyin | YouTube | Bilibili | Xiaohongshu | Instagram Reels | Other
Duration:
Tone:                 Cinematic | Warm | Humorous | Suspenseful | Educational
Target Audience:
Reference Videos:
```

### Directing Tips

**Analyze the idea / input:**
- Distill the core message — summarize in one sentence "what should the viewer remember after watching"
- Find the emotional anchor — decide what the viewer should *feel*, not just *know*
- Determine the narrative structure: Hook → Conflict/Curiosity → Climax → Closing CTA; or Problem → Solution → Result
- Do not skip this step and jump straight to scripting — a script without direction wastes time at every subsequent stage

**Analyze the audience:**
- The audience dictates tone, pacing, and visual style
- Young audience (18–25): fast pace, first 3 seconds must hook hard, conversational copy, vertical format
- Professional / business audience: steady pace, data / case-study driven, horizontal format
- General interest audience: story first, don't lecture, let the visuals speak
- Ask yourself: "In what context will this person encounter this video? Why would they stop scrolling?"

**Plan the shot-by-shot script (from script to shots):**
- Write the text script first, then break it into shots — not the other way around
- Each time segment should carry only one visual idea; don't cram two things in at once
- Shot duration reference: hook 3–5s, narrative segments 5–10s, CTA 5–8s
- Visual rhythm = editing rhythm: tense segments use short shots with fast cuts; emotional segments use long shots with slow push-ins
- Explicitly mark "silent" segments in the script — unmarked segments will default to having narration

### Script Format

Segment by timecode, three lines per segment:

```
[00:00–00:05]
Visual: Close-up of hand pouring coffee, steam rising, dark background
Voiceover / Dialogue: (Silent — ambient sound only)
On-screen Text: —

[00:05–00:18]
Visual: Character sitting by a window, soft morning light, relaxed atmosphere
Voiceover / Dialogue: "Every morning deserves a ritual."
On-screen Text: —
```

---

## Phase 2 — Character & Scene Design

**Goal**: Establish unified visual standards for characters and key scenes before generating any video.

### Character Reference Sheet

Every named character needs a generated reference image with the following documented:

```
Character Name:
Age / Gender / Body Type:
Clothing Style:
Signature Features:
Required Expression Range: (e.g., neutral, smile, surprised)
Reference Image File:
```

### AI Image Generation Prompt Techniques

**General Structure:**
```
[Subject description], [Clothing / Accessories], [Expression / Action], [Lighting],
[Background], [Composition: full body / upper body / portrait], [Style keywords],
[Quality keywords]
```

#### High-Resolution Realistic Portraits

```
a 28-year-old East Asian woman with shoulder-length black hair,
wearing a cream linen shirt, soft smile, looking at camera,
natural window light from the left, neutral gray background,
upper body portrait, photorealistic, shot on Sony A7IV,
85mm f/1.4, shallow depth of field, skin texture visible,
8K, RAW photo
```

**Key Points:**
- Specify camera model and lens parameters (e.g., `shot on Canon EOS R5, 50mm f/1.2`) — this is 10x more effective than just writing "photorealistic"
- Use `skin texture visible, pores, fine hair` etc. to boost realism
- Be specific about lighting: `soft diffused window light from upper left`, don't just write `good lighting`
- Simpler backgrounds yield sharper subjects: `neutral gray background` or `clean white studio`
- Negative prompts: `blurry, cartoon, illustration, painting, deformed, extra fingers`

#### Cartoon / Illustration Style

```
a cheerful girl with big round eyes and twin tails,
wearing a yellow raincoat, jumping in a puddle,
rainy city street, colorful reflections,
Pixar 3D animation style, vibrant colors, soft studio lighting,
4K, clean render
```

**Key Points:**
- Be specific with style anchors: `Pixar style` / `Studio Ghibli watercolor` / `flat vector illustration` / `Makoto Shinkai style`
- Don't mix styles — use only one style anchor per image
- Exaggerated features help achieve a cartoon look: `big expressive eyes, round face, exaggerated proportions`
- Specify color saturation: `vibrant saturated colors` or `pastel muted tones`

#### Image-to-Image / Reference Image Control

```
Usage: Upload reference image + text prompt describing desired modifications

Prompt example (with reference image):
same character, same clothing, different pose — now sitting at a desk,
warm indoor lighting, bookshelf in background,
maintain exact face features and hairstyle,
photorealistic, consistent with reference
```

**Key Points:**
- The core of I2I is "clearly state what should remain unchanged" — `same face, same outfit, same hairstyle`
- Only change what you want to change; lock everything else with `maintain` / `keep` / `same as reference`
- Denoising strength controls the degree of change: 0.3–0.5 for minor changes, 0.6–0.8 for major changes
- If using ControlNet / IP-Adapter etc., specify control type: `face reference`, `pose reference`, `style reference`

### Consistency Rules
- Generate the character reference image first, before creating any shots that include that character
- Use the same reference image as I2V input for all shots featuring that character — this is the most effective method for maintaining character consistency across shots
- Lock down the color palette (2–3 primary colors) at this stage; all subsequent prompts should reference this palette

---

## Phase 3 — Storyboard & Asset Generation

**Goal**: Plan shot by shot, generating first-frame images, last-frame images, and necessary audio assets for each shot.

### Shot Table Format

| # | Duration | Shot Size | Visual Description | Camera Move | VO / SFX | First Frame | Last Frame |
|---|----------|-----------|-------------------|-------------|----------|-------------|------------|
| 01 | 4s | Close-up | Slow-mo coffee drip, dark background, steam | Static | — | To generate | — |
| 02 | 6s | Medium | Character by window, city background | Slow push | VO line 1 | To generate | To generate |

**Shot size abbreviations**: Close-up · Medium close-up · Medium · Wide · Extreme wide · Aerial
**Camera moves**: Static · Push in · Pull back · Pan left · Pan right · Tilt up · Tilt down · Orbit · Handheld

### First Frame & Last Frame Generation

For shots with significant motion or transitions, generate static images for the start and end frames separately, then use them as I2V input.

**First Frame Prompt Pattern:**
```
[Subject + starting pose/position], [Environment], [Lighting],
[Precise shot size], [Style keywords], sharp focus, no motion blur
```

**Last Frame Prompt Pattern:**
```
[Subject + ending pose/position], [Environment], [Same lighting as first frame],
[Same shot size as first frame], [Same style keywords as first frame], sharp focus, no motion blur
```

**Why do this:** Generating static frames first lets you validate the visual look without spending video generation credits; feeding both first and last frames to tools like RunwayML / Kling significantly improves motion coherence.

### Audio Asset Planning

Document audio requirements for each shot alongside the shot table:

```
Shot 02 — Voiceover: "Every morning deserves a ritual."
  Voice style: warm, slow, female, with subtle breeze ambient underneath
  Tool: ElevenLabs

Shot 03 — SFX: Ceramic cup placed on marble, a soft clink
  Tool: Freesound sourcing / ElevenLabs SFX generation
```

---

## Phase 4 — Video Generation

**Goal**: Generate video shot by shot using the right tools and prompt patterns, documenting every attempt.

### Tool Selection

| Requirement | Recommended Tool |
|-------------|-----------------|
| Highest quality realism, complex physics | Sora |
| Cinematic look, precise camera control | RunwayML Gen-3 |
| Fast iteration, character animation | Pika 2.0 |
| Chinese scenes, cost-effective, I2V | Kling |
| Smooth fluid motion | Hailuo |

### AI Video Generation Prompt Techniques

**General Structure:**
```
[Subject + action], [Environment], [Lighting],
[Camera movement], [Style keywords], [Mood / Color tone],
Duration: Xs
```

#### Describing Visual Details

- Be specific about subject actions: "a woman slowly lifts a cup to her lips" — don't just write "a woman drinking"
- Layer the environment: describe foreground / midground / background separately
- Be explicit about lighting direction and quality: `warm golden hour light from the right, long shadows on the ground`
- Material and detail boost realism: `steam rising from the cup, condensation on the glass, fabric wrinkles`

#### Camera Angles

| Angle | Keywords | Emotional Effect |
|-------|----------|-----------------|
| Eye level | `eye level`, `straight on` | Neutral, objective |
| Low angle | `low angle`, `worm's eye view` | Authority, power |
| High angle | `high angle`, `bird's eye view` | Smallness, vulnerability |
| Dutch angle | `dutch angle`, `tilted frame` | Unease, tension |
| Over-the-shoulder | `over-the-shoulder`, `OTS shot` | Dialogue, immersion |
| First person | `POV shot`, `first person view` | Immersive experience |

#### Camera Movement Trajectories

| Movement | Keywords | Use Cases |
|----------|----------|-----------|
| Push in | `dolly in`, `push in`, `slow zoom in` | Focus on subject, build tension |
| Pull back | `dolly out`, `pull back`, `reveal shot` | Reveal environment, end a segment |
| Lateral track | `tracking shot`, `lateral dolly` | Follow a moving subject |
| Orbit | `orbit shot`, `arc around subject` | 360° showcase, epic feel |
| Crane | `crane up`, `crane down`, `jib shot` | Emotional rise/fall, scene transitions |
| Handheld | `handheld`, `shaky cam` | Documentary feel, tension |
| Stabilizer | `steadicam`, `gimbal smooth` | Smooth follow |
| Aerial | `drone shot`, `aerial flyover` | Establishing shots, large-scale scenes |

**Common Generation Issues & Fixes:**

| Issue | Fix |
|-------|-----|
| Frame drift / jitter | Add `stabilized`, `locked-off camera`, `tripod shot` |
| Character deformation / distortion | Simplify prompt; use reference image instead of text description for characters |
| Wrong style | Reference a specific director / film: `in the style of Wong Kar-wai` |
| Garbled text | Never let AI generate text within video — add all text in post-production |
| Motion too fast / too slow | Explicitly write `slow motion`, `languid pace` or `dynamic fast-cut` |

### Generation Log

Document every attempt for each shot:

```
Shot 02 — V1
Tool: RunwayML Gen-3
Prompt: [Full prompt]
Result: shot-02-v1.mp4
Status: ❌ Rejected — character drifts out of frame at 3s

Shot 02 — V2
Prompt: [Modified prompt] + "subject stays centered in frame"
Result: shot-02-v2.mp4
Status: ✅ Approved
```

---

## Phase 5 — Editing, Rendering & Export

**Goal**: Assemble approved clips in storyboard order, overlay audio, color grade, and export platform-ready files.

### Editing Checklist

```
- [ ] All shots arranged in storyboard order
- [ ] Voiceover and music synced with visuals
- [ ] Sound effects placed at correct timecodes
- [ ] On-screen text / subtitles added (do not rely on AI-generated text within video)
- [ ] Color grading complete — matches the color palette locked in Phase 2
- [ ] Transition review — cut on action whenever possible
- [ ] First 3 seconds review — is the hook strong enough on mute?
- [ ] Pacing review — every extra second must earn its place
```

### Automated Composition Script `scripts/compose_video.py`

When all shot clips, voiceover, and background music are ready, use this script to compose the final video in one step. It calls ffmpeg to handle: clip concatenation, trim alignment, transitions, multi-track audio mixing, subtitle burn-in, and encoding/export.

**When to use this script:**
- All shots have been generated in Phase 4 and marked as "Approved"
- Audio assets (voiceover, music, SFX) are ready
- You want to skip opening DaVinci / Premiere for manual assembly and compose directly from the command line

**Prerequisites:**
- Python 3.8+
- ffmpeg and ffprobe installed (`brew install ffmpeg` or your system's package manager)

**Usage:**

1. Create a `config.json` describing all assets to compose:

```json
{
  "output": "final_output.mp4",
  "resolution": "1920x1080",
  "fps": 24,
  "bitrate": "20M",
  "clips": [
    {
      "file": "shot-01.mp4",
      "trim_start": 0,
      "trim_end": 4,
      "transition": "fade",
      "transition_duration": 0.5
    },
    {
      "file": "shot-02.mp4",
      "trim_start": 0,
      "trim_end": 6
    },
    {
      "file": "shot-03.mp4"
    }
  ],
  "audio_tracks": [
    {
      "file": "voiceover.mp3",
      "start_at": 5.0,
      "volume": 1.0
    },
    {
      "file": "bgm.mp3",
      "start_at": 0,
      "volume": 0.3,
      "fade_in": 2.0,
      "fade_out": 3.0
    }
  ],
  "subtitle": "subtitles.srt"
}
```

2. Run the script:

```bash
python scripts/compose_video.py config.json
```

3. View example configuration:

```bash
python scripts/compose_video.py --example
```

**config.json Field Reference:**

| Field | Description |
|-------|-------------|
| `output` | Output filename |
| `resolution` | Output resolution, e.g., `1920x1080` / `1080x1920` (vertical) |
| `fps` | Frame rate; use 24 for cinematic, 30 for social |
| `bitrate` | Video bitrate, e.g., `20M` |
| `clips[].file` | Clip file path (relative to config.json directory) |
| `clips[].trim_start` / `trim_end` | Trim start/end in seconds; omit to use the full clip |
| `clips[].transition` | Transition type to next clip: `fade` / `wipeleft` / `slideright` etc. |
| `clips[].transition_duration` | Transition duration (seconds); omit for a hard cut |
| `audio_tracks[].file` | Audio file path |
| `audio_tracks[].start_at` | Start time on the timeline in seconds |
| `audio_tracks[].volume` | Volume multiplier; 1.0 = original, 0.3 = 30% |
| `audio_tracks[].fade_in` / `fade_out` | Fade in/out duration (seconds) |
| `subtitle` | SRT subtitle file path; will be burned into the video |

**Typical Workflow:**
1. After Phase 4, populate the `clips` array with all "Approved" clip filenames
2. Add voiceover and background music to `audio_tracks`; set volume and start positions
3. If subtitles exist, fill in the `subtitle` field
4. Set `resolution` based on target platform (horizontal `1920x1080` / vertical `1080x1920`)
5. Run the script to get the final cut

### Recommended Tools

| Task | Tool |
|------|------|
| Quick composition (CLI) | `scripts/compose_video.py` (built into this Skill) |
| Full editing + color grading | DaVinci Resolve (free) |
| Quick social editing + auto subtitles | CapCut |
| Professional NLE | Adobe Premiere / Final Cut Pro |
| Audio noise reduction | Adobe Podcast (free, browser-based) |
| AI voiceover | ElevenLabs |
| AI music | Suno AI / Udio |

### Platform Export Specifications

| Platform | Aspect Ratio | Resolution | Max Duration |
|----------|-------------|------------|--------------|
| Douyin / TikTok / Reels / Shorts | 9:16 | 1080×1920 | 60s–15min |
| YouTube | 16:9 | 1920×1080 | Unlimited |
| Bilibili | 16:9 | 1920×1080 | 4 hours |
| Xiaohongshu | 3:4 | 1080×1440 | 15min |

**General Export Settings (script defaults):**
- Codec: H.264 (libx264, preset slow)
- Bitrate: 20 Mbps (adjustable in config.json)
- Audio: AAC 320kbps, stereo
- Frame rate: 24fps (adjustable in config.json)
- Container: MP4 with faststart enabled (optimized for web playback)

---

## Self-Improvement Mechanism

This Skill has a built-in continuous learning loop — every creation accumulates experience, making the next one automatically better.

### When to Log

| Trigger | Log To | Category |
|---------|--------|----------|
| Discovered a useful prompt technique | `.learnings/LEARNINGS.md` | `prompt_technique` |
| Found a fix after repeated prompt failures | `.learnings/LEARNINGS.md` | `prompt_fix` |
| Discovered a tool's gotcha / limitation | `.learnings/LEARNINGS.md` | `tool_gotcha` |
| User corrected a directing / scripting judgment | `.learnings/LEARNINGS.md` | `directing_correction` |
| Found a better narrative structure or pacing | `.learnings/LEARNINGS.md` | `directing_technique` |
| Video generation command / API error | `.learnings/ERRORS.md` | error |
| User requested a capability not yet supported | `.learnings/FEATURE_REQUESTS.md` | feature |

### Log Format

```markdown
## [LRN-YYYYMMDD-XXX] category

**Logged**: ISO-8601 timestamp
**Priority**: low | medium | high | critical
**Status**: pending

### Summary
One-sentence description

### Details
Full context: what happened, what went wrong, what went right

### Suggested Action
Specific steps to take next time a similar situation arises

### Metadata
- Source: conversation | error | user_feedback
- Tags: prompt, image_gen, video_gen, directing, editing
---
```

### Knowledge Promotion Rules

When a learning is verified as effective (`Status: resolved`) and applicable across all projects:

- **Prompt techniques** (image/video) → Merge back into the corresponding "Prompt Techniques" section of this SKILL.md
- **Directing tips** → Merge back into the "Directing Tips" section of this SKILL.md
- **Tool experience** → Merge back into the "Tool Selection" or "Common Issues" tables of this SKILL.md
- **Cross-project universal workflows** → Promote to `AGENTS.md`
- **Tool-specific gotchas** → Promote to `TOOLS.md`
- **Aesthetic / style preferences** → Promote to `SOUL.md`

**Core principle: At the end of every creation, ask yourself "What from this session can be directly reused next time?" — write it down.**
