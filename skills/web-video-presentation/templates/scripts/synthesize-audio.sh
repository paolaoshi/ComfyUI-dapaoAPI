#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────
# synthesize-audio.sh — provider-agnostic TTS runner.
#
# Reads audio-segments.json (produced by extract-narrations.ts) and
# writes one mp3 per segment under public/audio/<chapter>/<N>.mp3.
#
# This file itself does NOT know how to call any TTS engine. It loads
# a provider adapter from tts-providers/<name>.sh which must expose:
#
#   tts_synthesize <text> <out_path> [<voice>]   (required)
#   tts_check                                    (optional)
#   tts_install_help                             (optional)
#
# See tts-providers/README.md for the full contract and copy-pasteable
# recipes for adding more providers (OpenAI / ElevenLabs / edge-tts /
# Azure / etc.).
#
# Choosing a provider:
#   PRESENTATION_TTS=<name>       env var  (default: minimax)
#   --provider=<name>             CLI flag (overrides env)
#
# Choosing a voice (provider decides what's valid):
#   PRESENTATION_TTS_VOICE=<id>   env var
#   --voice=<id>                  CLI flag (overrides env)
#
# Other flags:
#   --force                       re-synthesize even if mp3 exists
#
# Behavior:
#   • Serial calls (TTS APIs commonly rate-limit parallel requests).
#   • Skips segments whose mp3 already exists — rerun safely after a
#     partial failure. Pass --force to re-synthesize all.
#   • Prints progress per segment with elapsed time.
#
# Examples:
#   npm run synthesize-audio
#   npm run synthesize-audio -- --force
#   PRESENTATION_TTS=openai npm run synthesize-audio
#   npm run synthesize-audio -- --provider=elevenlabs --voice=Rachel
# ────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SEGMENTS="$ROOT/audio-segments.json"
OUT_DIR="$ROOT/public/audio"
PROVIDERS_DIR="$SCRIPT_DIR/tts-providers"

PROVIDER="${PRESENTATION_TTS:-minimax}"
VOICE="${PRESENTATION_TTS_VOICE:-}"
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --force)         FORCE=true ;;
    --voice=*)       VOICE="${arg#--voice=}" ;;
    --provider=*)    PROVIDER="${arg#--provider=}" ;;
    -h|--help)
      sed -n '2,46p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "✗ unknown arg: $arg" >&2; exit 1 ;;
  esac
done

PROVIDER_FILE="$PROVIDERS_DIR/$PROVIDER.sh"

# ── Pre-flight ────────────────────────────────────────────────────────
if [[ ! -f "$SEGMENTS" ]]; then
  echo "✗ $SEGMENTS not found. Run: npm run extract-narrations" >&2
  exit 1
fi
if ! command -v jq >/dev/null; then
  echo "✗ jq is required to read audio-segments.json" >&2
  echo "  Install: brew install jq   (or apt-get install jq, etc.)" >&2
  exit 1
fi
if [[ ! -f "$PROVIDER_FILE" ]]; then
  echo "✗ TTS provider '$PROVIDER' not found at $PROVIDER_FILE" >&2
  echo >&2
  echo "  Available providers:" >&2
  for f in "$PROVIDERS_DIR"/*.sh; do
    [[ -f "$f" ]] || continue
    echo "    • $(basename "$f" .sh)" >&2
  done
  echo >&2
  echo "  To add your own, see $PROVIDERS_DIR/README.md" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$PROVIDER_FILE"

if ! declare -F tts_synthesize >/dev/null; then
  echo "✗ provider '$PROVIDER' does not define tts_synthesize" >&2
  echo "  See $PROVIDERS_DIR/README.md for the contract." >&2
  exit 1
fi

if declare -F tts_check >/dev/null; then
  if ! tts_check; then
    echo >&2
    if declare -F tts_install_help >/dev/null; then
      tts_install_help
    fi
    exit 1
  fi
fi

# ── Main loop ─────────────────────────────────────────────────────────
total=$(jq 'length' "$SEGMENTS")
i=0
synthesized=0
skipped=0
failed=0

while IFS= read -r row; do
  i=$((i + 1))
  chapter=$(echo "$row" | jq -r '.chapter')
  step=$(echo "$row" | jq -r '.step')
  text=$(echo "$row" | jq -r '.text')
  out="$OUT_DIR/$chapter/$step.mp3"

  if [[ -f "$out" && "$FORCE" != true ]]; then
    skipped=$((skipped + 1))
    printf "[%3d/%d] %-20s skip (exists)\n" "$i" "$total" "$chapter/$step.mp3"
    continue
  fi

  mkdir -p "$(dirname "$out")"
  start=$(date +%s)
  if tts_synthesize "$text" "$out" "$VOICE"; then
    elapsed=$(( $(date +%s) - start ))
    synthesized=$((synthesized + 1))
    printf "[%3d/%d] %-20s ✓ %ss\n" "$i" "$total" "$chapter/$step.mp3" "$elapsed"
  else
    failed=$((failed + 1))
    printf "[%3d/%d] %-20s ✗ FAILED\n" "$i" "$total" "$chapter/$step.mp3" >&2
  fi
done < <(jq -c '.[]' "$SEGMENTS")

echo
echo "✓ done (provider=$PROVIDER) — synthesized $synthesized, skipped $skipped, failed $failed"
[[ $failed -eq 0 ]] || exit 2
