#!/usr/bin/env python3
"""
compose_video.py — Compose multiple video clips and audio tracks into a single video using ffmpeg.

Usage:
  python scripts/compose_video.py config.json

config.json example:

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

Dependencies:
  - Python 3.8+
  - ffmpeg / ffprobe installed and available in PATH
"""

import json
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found in PATH. Install it first.")
        sys.exit(1)
    if not shutil.which("ffprobe"):
        print("ERROR: ffprobe not found in PATH. Install it first.")
        sys.exit(1)


def get_duration(filepath: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", filepath],
        capture_output=True, text=True,
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def build_concat_filter(clips: list, resolution: str, fps: int) -> tuple[list, str, int]:
    """Build ffmpeg filter_complex for clip concatenation with optional transitions.

    Returns (input_args, filter_complex_string, number_of_clips).
    """
    width, height = resolution.split("x")
    input_args = []
    filter_parts = []

    for i, clip in enumerate(clips):
        input_args += ["-i", clip["file"]]

        trim_start = clip.get("trim_start", 0)
        trim_end = clip.get("trim_end")

        trim_filter = f"trim=start={trim_start}"
        if trim_end is not None:
            trim_filter += f":end={trim_end}"

        filter_parts.append(
            f"[{i}:v]{trim_filter},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={fps},format=yuv420p[v{i}]"
        )

    # xfade transitions between consecutive clips
    n = len(clips)
    if n == 1:
        filter_parts.append(f"[v0]null[vout]")
    else:
        offsets = []
        cumulative = 0.0
        for i, clip in enumerate(clips):
            start = clip.get("trim_start", 0)
            end = clip.get("trim_end")
            if end is not None:
                dur = end - start
            else:
                dur = get_duration(clip["file"]) - start
            if i > 0:
                prev_trans_dur = clips[i - 1].get("transition_duration", 0)
                cumulative -= prev_trans_dur
            offsets.append(cumulative)
            cumulative += dur

        current_label = "v0"
        for i in range(1, n):
            transition = clips[i - 1].get("transition", "fade")
            trans_dur = clips[i - 1].get("transition_duration", 0)

            if trans_dur > 0:
                out_label = f"vx{i}" if i < n - 1 else "vout"
                offset = offsets[i]
                filter_parts.append(
                    f"[{current_label}][v{i}]xfade=transition={transition}"
                    f":duration={trans_dur}:offset={offset:.3f}[{out_label}]"
                )
                current_label = out_label
            elif i == n - 1:
                # Last pair, no transition — just concat
                filter_parts.append(
                    f"[{current_label}][v{i}]concat=n=2:v=1:a=0[vout]"
                )
            else:
                out_label = f"vx{i}"
                filter_parts.append(
                    f"[{current_label}][v{i}]concat=n=2:v=1:a=0[{out_label}]"
                )
                current_label = out_label

    filter_complex = ";\n".join(filter_parts)
    return input_args, filter_complex, n


def build_audio_filter(
    clips: list, audio_tracks: list, n_video_inputs: int
) -> tuple[list, str]:
    """Build audio mixing filter.

    Returns (additional_input_args, audio_filter_string).
    """
    input_args = []
    amix_inputs = []

    # Mute original video audio and create silent base from clips
    # We'll extract audio from each clip and concatenate
    audio_parts = []
    for i, clip in enumerate(clips):
        trim_start = clip.get("trim_start", 0)
        trim_end = clip.get("trim_end")
        atrim = f"atrim=start={trim_start}"
        if trim_end is not None:
            atrim += f":end={trim_end}"
        audio_parts.append(f"[{i}:a]{atrim},asetpts=PTS-STARTPTS[ca{i}]")

    if len(clips) == 1:
        audio_parts.append(f"[ca0]acopy[clipaudio]")
    else:
        labels = "".join(f"[ca{i}]" for i in range(len(clips)))
        audio_parts.append(f"{labels}concat=n={len(clips)}:v=0:a=1[clipaudio]")

    amix_inputs.append("[clipaudio]")

    # Additional audio tracks
    for j, track in enumerate(audio_tracks):
        idx = n_video_inputs + j
        input_args += ["-i", track["file"]]

        volume = track.get("volume", 1.0)
        start_at = track.get("start_at", 0)
        fade_in = track.get("fade_in", 0)
        fade_out = track.get("fade_out", 0)

        chain = f"[{idx}:a]volume={volume}"
        if fade_in > 0:
            chain += f",afade=t=in:d={fade_in}"
        if fade_out > 0:
            chain += f",areverse,afade=t=in:d={fade_out},areverse"
        if start_at > 0:
            chain += f",adelay={int(start_at * 1000)}|{int(start_at * 1000)}"
        label = f"a{j}"
        audio_parts.append(f"{chain}[{label}]")
        amix_inputs.append(f"[{label}]")

    n_audio = len(amix_inputs)
    if n_audio == 1:
        audio_parts.append(f"{amix_inputs[0]}acopy[aout]")
    else:
        mix_in = "".join(amix_inputs)
        audio_parts.append(
            f"{mix_in}amix=inputs={n_audio}:duration=longest:normalize=0[aout]"
        )

    return input_args, ";\n".join(audio_parts)


def compose(config: dict, config_dir: Path):
    clips = config["clips"]
    resolution = config.get("resolution", "1920x1080")
    fps = config.get("fps", 24)
    bitrate = config.get("bitrate", "20M")
    output = config["output"]
    audio_tracks = config.get("audio_tracks", [])
    subtitle = config.get("subtitle")

    # Resolve paths relative to config file location
    for clip in clips:
        clip["file"] = str(config_dir / clip["file"])
    for track in audio_tracks:
        track["file"] = str(config_dir / track["file"])
    if subtitle:
        subtitle = str(config_dir / subtitle)
    output = str(config_dir / output)

    # Build video filter
    video_input_args, video_filter, n_clips = build_concat_filter(clips, resolution, fps)

    # Build audio filter
    has_audio_tracks = len(audio_tracks) > 0
    has_clip_audio = True  # assume clips may have audio
    audio_input_args, audio_filter = build_audio_filter(clips, audio_tracks, n_clips)

    # Combine filters
    full_filter = video_filter + ";\n" + audio_filter

    # Subtitle burn-in
    if subtitle:
        full_filter = full_filter.replace(
            "[vout]",
            f"[vpre];\n[vpre]subtitles={_escape_filter_path(subtitle)}[vout]",
            1,
        )

    cmd = (
        ["ffmpeg", "-y"]
        + video_input_args
        + audio_input_args
        + [
            "-filter_complex", full_filter,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "slow",
            "-b:v", bitrate,
            "-c:a", "aac",
            "-b:a", "320k",
            "-movflags", "+faststart",
            output,
        ]
    )

    print("=" * 60)
    print("ffmpeg command:")
    print(" ".join(cmd))
    print("=" * 60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("STDERR:", result.stderr)
        print(f"\nERROR: ffmpeg exited with code {result.returncode}")
        sys.exit(result.returncode)

    print(f"\nDone! Output: {output}")


def compose_simple(config: dict, config_dir: Path):
    """Simpler concat-only mode: no transitions, just join clips + optional audio overlay.

    Falls back to this when clips don't need xfade and user wants a quick assembly.
    """
    clips = config["clips"]
    resolution = config.get("resolution", "1920x1080")
    fps = config.get("fps", 24)
    bitrate = config.get("bitrate", "20M")
    output = str(config_dir / config["output"])
    audio_tracks = config.get("audio_tracks", [])
    subtitle = config.get("subtitle")

    width, height = resolution.split("x")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for clip in clips:
            filepath = str(config_dir / clip["file"])
            f.write(f"file '{filepath}'\n")

            trim_start = clip.get("trim_start", 0)
            trim_end = clip.get("trim_end")
            if trim_start > 0:
                f.write(f"inpoint {trim_start}\n")
            if trim_end is not None:
                f.write(f"outpoint {trim_end}\n")
        concat_list = f.name

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
               f"fps={fps},format=yuv420p",
    ]

    for track in audio_tracks:
        cmd += ["-i", str(config_dir / track["file"])]

    if audio_tracks:
        audio_filter_parts = []
        for j, track in enumerate(audio_tracks):
            vol = track.get("volume", 1.0)
            start_at = track.get("start_at", 0)
            fade_in = track.get("fade_in", 0)
            fade_out = track.get("fade_out", 0)
            chain = f"[{j + 1}:a]volume={vol}"
            if fade_in > 0:
                chain += f",afade=t=in:d={fade_in}"
            if fade_out > 0:
                chain += f",areverse,afade=t=in:d={fade_out},areverse"
            if start_at > 0:
                chain += f",adelay={int(start_at * 1000)}|{int(start_at * 1000)}"
            audio_filter_parts.append(f"{chain}[a{j}]")

        n = len(audio_tracks) + 1  # +1 for original audio from concat
        labels = f"[0:a]" + "".join(f"[a{j}]" for j in range(len(audio_tracks)))
        audio_filter_parts.append(
            f"{labels}amix=inputs={n}:duration=longest:normalize=0[aout]"
        )
        cmd += ["-filter_complex", ";\n".join(audio_filter_parts), "-map", "0:v", "-map", "[aout]"]
    else:
        cmd += ["-c:a", "aac"]

    if subtitle:
        sub_path = str(config_dir / subtitle)
        cmd[-1:] = []  # remove last to inject subtitle filter
        cmd += ["-vf", cmd[cmd.index("-vf") + 1] + f",subtitles={_escape_filter_path(sub_path)}"]

    cmd += [
        "-c:v", "libx264",
        "-preset", "slow",
        "-b:v", bitrate,
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        output,
    ]

    print("=" * 60)
    print("ffmpeg command (simple concat):")
    print(" ".join(cmd))
    print("=" * 60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    Path(concat_list).unlink(missing_ok=True)

    if result.returncode != 0:
        print("STDERR:", result.stderr)
        print(f"\nERROR: ffmpeg exited with code {result.returncode}")
        sys.exit(result.returncode)

    print(f"\nDone! Output: {output}")


def _escape_filter_path(path: str) -> str:
    """Escape special chars for ffmpeg filter path arguments."""
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def main():
    if len(sys.argv) < 2:
        print("Usage: python compose_video.py <config.json>")
        print()
        print("Create a config.json with clips, audio_tracks, and output settings.")
        print("Run with --example to print a sample config.")
        sys.exit(1)

    if sys.argv[1] == "--example":
        example = {
            "output": "final_output.mp4",
            "resolution": "1920x1080",
            "fps": 24,
            "bitrate": "20M",
            "clips": [
                {"file": "shot-01.mp4", "trim_start": 0, "trim_end": 4,
                 "transition": "fade", "transition_duration": 0.5},
                {"file": "shot-02.mp4", "trim_start": 0, "trim_end": 6},
                {"file": "shot-03.mp4"},
            ],
            "audio_tracks": [
                {"file": "voiceover.mp3", "start_at": 5.0, "volume": 1.0},
                {"file": "bgm.mp3", "start_at": 0, "volume": 0.3,
                 "fade_in": 2.0, "fade_out": 3.0},
            ],
            "subtitle": "subtitles.srt",
        }
        print(json.dumps(example, indent=2, ensure_ascii=False))
        sys.exit(0)

    check_ffmpeg()

    config_path = Path(sys.argv[1]).resolve()
    config_dir = config_path.parent

    with open(config_path) as f:
        config = json.load(f)

    has_transitions = any(
        clip.get("transition_duration", 0) > 0 for clip in config["clips"]
    )

    if has_transitions:
        compose(config, config_dir)
    else:
        compose_simple(config, config_dir)


if __name__ == "__main__":
    main()
