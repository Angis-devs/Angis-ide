"""Error types for Angis."""

from __future__ import annotations


class AngisError(Exception):
    """Base class for safe user-facing Angis errors."""


class AngisSyntaxError(AngisError):
    """Raised when source text cannot be tokenized or parsed."""


class AmbiguityError(AngisError):
    """Raised when a phrase matches multiple intents too closely."""

    def __init__(self, phrase: str, candidates: list[str]) -> None:
        shown = ", ".join(candidates)
        super().__init__(
            f"Unclear phrase: {phrase!r}. It could mean: {shown}. "
            "Try using a more direct phrasing."
        )
        self.phrase = phrase
        self.candidates = candidates


class AngisRuntimeError(AngisError):
    """Raised when valid Angis code fails at runtime."""
