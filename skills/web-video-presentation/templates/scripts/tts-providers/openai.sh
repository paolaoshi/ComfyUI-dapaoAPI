# ────────────────────────────────────────────────────────────────────
# OpenAI TTS provider — uses the Audio Speech REST API via curl.
#
# Docs:    https://platform.openai.com/docs/api-reference/audio/createSpeech
# Env:     OPENAI_API_KEY=sk-...     required
#          OPENAI_BASE_URL=https://api.openai.com/v1   optional (for proxies / Azure-OpenAI)
#          OPENAI_TTS_MODEL=tts-1    optional (tts-1 = fast, tts-1-hd = higher quality)
# Voices:  alloy / echo / fable / onyx / nova / shimmer
#          (default: alloy)
#
# Strengths: many agents already have OPENAI_API_KEY set; predictable
# pricing; very fast.
# ────────────────────────────────────────────────────────────────────

tts_check() {
  if ! command -v curl >/dev/null; then
    echo "✗ curl not found in PATH." >&2
    return 1
  fi
  if ! command -v jq >/dev/null; then
    echo "✗ jq is required to build the request payload safely." >&2
    return 1
  fi
  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "✗ OPENAI_API_KEY is not set." >&2
    return 1
  fi
}

tts_install_help() {
  cat <<'EOF' >&2
To use the OpenAI provider:

  Set your key:    export OPENAI_API_KEY=sk-...
                   (get one at https://platform.openai.com/api-keys)
  Optional:        export OPENAI_BASE_URL=https://your-proxy/v1
                   export OPENAI_TTS_MODEL=tts-1-hd   # higher quality, ~2× cost

Install deps (only if missing):
  curl  — brew install curl  / apt-get install curl
  jq    — brew install jq    / apt-get install jq

Or pick another provider:  PRESENTATION_TTS=<name> npm run synthesize-audio
EOF
}

tts_synthesize() {
  local text="$1"
  local out="$2"
  local voice="${3:-}"
  [[ -z "$voice" ]] && voice="alloy"

  local base="${OPENAI_BASE_URL:-https://api.openai.com/v1}"
  local model="${OPENAI_TTS_MODEL:-tts-1}"

  local payload
  payload=$(jq -n \
    --arg t "$text" \
    --arg v "$voice" \
    --arg m "$model" \
    '{model:$m, input:$t, voice:$v, response_format:"mp3"}')

  # On HTTP error curl with -f exits non-zero, runner marks FAILED.
  # We capture stderr so a single segment's API error doesn't spam,
  # but if every segment fails the user should run with `bash -x`.
  curl -fsS -o "$out" -X POST "$base/audio/speech" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null
}
