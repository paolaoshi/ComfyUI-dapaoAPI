"""Shared dapaoAI LLM model catalogue.

All long-term-maintenance nodes that need an LLM should import this tuple so
the UI choices and backend validation cannot drift apart.
"""

LLM_MODEL_OPTIONS = (
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "claude-fable-5",
    "claude-opus-4-8",
    "claude-opus-5",
    "claude-sonnet-5",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
)

DEFAULT_LLM_MODEL = "gemini-3.7-flash"

# Conservative client-side limits used only for history budgeting. The relay
# remains the source of truth and may expose larger limits for a mapped model.
LLM_MODEL_CAPABILITIES = {
    model: {
        "context_limit": 200_000 if model.startswith("claude-") else 1_048_576 if model.startswith("gemini-") else 128_000,
        "max_output": 65_536,
        "supports_images": True,
        # The relay currently exposes chat-completions semantics.  Native
        # video parts are therefore kept disabled and the chat material node
        # sends uniformly sampled 2K PNG frames instead.  Gemini mappings are
        # the project-declared family for OpenAI-compatible input_audio.
        "supports_video": False,
        "supports_audio": model.startswith("gemini-"),
    }
    for model in LLM_MODEL_OPTIONS
}


__all__ = [
    "DEFAULT_LLM_MODEL",
    "LLM_MODEL_CAPABILITIES",
    "LLM_MODEL_OPTIONS",
]
