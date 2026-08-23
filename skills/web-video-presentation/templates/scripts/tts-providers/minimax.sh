# ────────────────────────────────────────────────────────────────────
# MiniMax provider — uses the official mmx-cli.
#
# Docs:  https://platform.minimaxi.com/docs/token-plan/minimax-cli
# Repo:  https://github.com/MiniMax-AI/cli
#
# Strengths: Chinese narration quality is consistently good; lots of
# voice options; one-line CLI call.
# ────────────────────────────────────────────────────────────────────

tts_check() {
  if ! command -v mmx >/dev/null; then
    echo "✗ mmx CLI not found in PATH." >&2
    return 1
  fi
  if ! mmx auth status >/dev/null 2>&1; then
    echo "✗ mmx is not authenticated." >&2
    return 1
  fi
}

tts_install_help() {
  cat <<'EOF' >&2
To use the MiniMax provider:

  Install:  npm install -g mmx-cli
  Login:    mmx auth login --api-key sk-xxxxx
            (get a key at https://platform.minimaxi.com)

Or pick another provider:  PRESENTATION_TTS=<name> npm run synthesize-audio
See tts-providers/README.md for the list and how to add your own.
EOF
}

tts_synthesize() {
  local text="$1"
  local out="$2"
  local voice="${3:-}"

  # Branch instead of using an empty array — runner uses `set -u`, and
  # macOS-default bash 3.2 fires "unbound variable" on "${arr[@]}" when
  # arr is empty. The two-branch form is portable to old bash.
  if [[ -n "$voice" ]]; then
    mmx speech synthesize --voice "$voice" --text "$text" --out "$out" \
      >/dev/null 2>&1
  else
    mmx speech synthesize --text "$text" --out "$out" \
      >/dev/null 2>&1
  fi
}
