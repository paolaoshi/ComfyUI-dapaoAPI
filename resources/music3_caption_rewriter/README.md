# Music 3 Caption Resources

This runtime resource bundle contains the static style indexes and caption
templates used by `DapaoMusic3CaptionPromptNode`. It is derived from the
user-provided MiniMax Music 3 `music-caption-rewriter` skill.

The node follows progressive disclosure at runtime: it routes to at most two
style-family indexes and loads at most three complete templates. It does not
scan the full template library during a normal request and does not require
the external reference-project path after installation.
