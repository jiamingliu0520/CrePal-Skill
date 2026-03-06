#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/jiamingliu0520/CrePal-Skill.git"
ZIP_URL="https://github.com/jiamingliu0520/CrePal-Skill/archive/refs/heads/main.zip"
DEFAULT_DIR="${HOME}/.openclaw/skills/crepal"
INSTALL_DIR="${CREPAL_SKILL_DIR:-$DEFAULT_DIR}"
IS_DEFAULT_PATH=
[ -z "${CREPAL_SKILL_DIR:-}" ] && IS_DEFAULT_PATH=1

if [ -d "$INSTALL_DIR" ] && [ -n "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]; then
  echo "==> Directory already exists and is not empty: $INSTALL_DIR" >&2
  echo "    Remove it or set CREPAL_SKILL_DIR to another path, then run again." >&2
  exit 1
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
echo "==> Installing CrePal-Skill into $INSTALL_DIR ..."

if command -v git &>/dev/null; then
  git clone "$REPO_URL" "$INSTALL_DIR"
elif command -v curl &>/dev/null; then
  tmpzip="$(mktemp /tmp/crepal-skill-XXXXXX.zip)"
  curl -fsSL "$ZIP_URL" -o "$tmpzip"
  unzip -qo "$tmpzip" -d /tmp
  mkdir -p "$INSTALL_DIR"
  cp -r /tmp/CrePal-Skill-main/. "$INSTALL_DIR"/
  rm -rf /tmp/CrePal-Skill-main "$tmpzip"
elif command -v wget &>/dev/null; then
  tmpzip="$(mktemp /tmp/crepal-skill-XXXXXX.zip)"
  wget -q "$ZIP_URL" -O "$tmpzip"
  unzip -qo "$tmpzip" -d /tmp
  mkdir -p "$INSTALL_DIR"
  cp -r /tmp/CrePal-Skill-main/. "$INSTALL_DIR"/
  rm -rf /tmp/CrePal-Skill-main "$tmpzip"
else
  echo "ERROR: git, curl, or wget is required but none were found." >&2
  exit 1
fi

echo ""
echo "==> CrePal-Skill installed successfully!"
echo "    Location: $INSTALL_DIR"
echo ""
if [ -n "${IS_DEFAULT_PATH:-}" ]; then
  echo "    Next: In OpenClaw, add or enable this skill (e.g. in Skills settings), then start creating AI videos!"
else
  echo "    Ensure this path is in OpenClaw's skills load path (e.g. ~/.openclaw/skills or workspace ./skills)."
  echo "    Then in OpenClaw, add or enable this skill in your Skills settings."
  echo ""
fi
