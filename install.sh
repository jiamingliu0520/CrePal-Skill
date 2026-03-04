#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/jiamingliu0520/CrePal-Skill.git"
ZIP_URL="https://github.com/jiamingliu0520/CrePal-Skill/archive/refs/heads/main.zip"
INSTALL_DIR="${CREPAL_SKILL_DIR:-CrePal-Skill}"

echo "==> Installing CrePal-Skill into ./${INSTALL_DIR} ..."

if command -v git &>/dev/null; then
  git clone "$REPO_URL" "$INSTALL_DIR"
elif command -v curl &>/dev/null; then
  tmpzip="$(mktemp /tmp/crepal-skill-XXXXXX.zip)"
  curl -fsSL "$ZIP_URL" -o "$tmpzip"
  unzip -qo "$tmpzip" -d /tmp
  mv /tmp/CrePal-Skill-main "$INSTALL_DIR"
  rm -f "$tmpzip"
elif command -v wget &>/dev/null; then
  tmpzip="$(mktemp /tmp/crepal-skill-XXXXXX.zip)"
  wget -q "$ZIP_URL" -O "$tmpzip"
  unzip -qo "$tmpzip" -d /tmp
  mv /tmp/CrePal-Skill-main "$INSTALL_DIR"
  rm -f "$tmpzip"
else
  echo "ERROR: git, curl, or wget is required but none were found." >&2
  exit 1
fi

echo ""
echo "==> CrePal-Skill installed successfully!"
echo "    Location: $(cd "$INSTALL_DIR" && pwd)"
echo ""
echo "    Next steps:"
echo "      1. Copy SKILL.md to your Cursor skills directory"
echo "      2. Start creating AI videos!"
