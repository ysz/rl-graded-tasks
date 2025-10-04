"""Central configuration for model defaults and pricing."""

from __future__ import annotations

DEFAULT_MODEL = "claude-3-5-haiku-latest"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 800

TOKEN_COST_DENOMINATOR = 1_000_000
MODEL_PRICING = {
    # Prices are USD per million tokens per Anthropic public sheet.
    "claude-3-haiku-20240307": {
        "input": 0.25,
        "output": 1.25,
    },
    "claude-3-5-haiku-20241022": {
        "input": 0.8,
        "output": 4.00,
    },
    "claude-3-5-haiku-latest": {
        "input": 0.8,
        "output": 4.00,
    },
}


def get_model_pricing(model: str) -> dict[str, float] | None:
    """Return pricing info for a model if known."""

    return MODEL_PRICING.get(model)


__all__ = [
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_TOP_P",
    "MODEL_PRICING",
    "TOKEN_COST_DENOMINATOR",
    "get_model_pricing",
]
