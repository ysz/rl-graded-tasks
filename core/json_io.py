from __future__ import annotations

import json
from typing import Any, Mapping

from jsonschema import ValidationError, validate

from .schema import ENVELOPE_JSON_SCHEMA, Envelope


class EnvelopeParseError(ValueError):
    """Raised when the unified envelope cannot be parsed or validated."""


def _load_json_payload(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        raise EnvelopeParseError("Empty response")

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise EnvelopeParseError("Could not locate a JSON object")
        candidate = stripped[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise EnvelopeParseError("Invalid JSON object") from exc


def parse_envelope(payload: Any) -> dict[str, Any]:
    """Parse and validate the unified envelope."""
    if isinstance(payload, Envelope):
        return payload.model_dump()

    if isinstance(payload, Mapping):
        data = dict(payload)
    elif isinstance(payload, (str, bytes)):
        as_text = payload.decode() if isinstance(payload, bytes) else payload
        data = _load_json_payload(as_text)
    else:
        raise EnvelopeParseError("Envelope must be a mapping or JSON text")

    if not isinstance(data, Mapping):
        raise EnvelopeParseError("Envelope root must be an object")

    try:
        validate(data, ENVELOPE_JSON_SCHEMA)
    except ValidationError as exc:
        raise EnvelopeParseError(f"Envelope does not match schema: {exc.message}") from exc

    try:
        envelope = Envelope.model_validate(data)
    except Exception as exc:
        raise EnvelopeParseError("Envelope failed validation") from exc

    return envelope.model_dump()


__all__ = ["parse_envelope", "EnvelopeParseError"]
