from __future__ import annotations

from copy import deepcopy
from typing import Any


W5_KEYS = ("who", "what", "why", "how", "when")
SEMANTIC_FIELDS = {
    "audience": ("who",),
    "goal": ("what",),
    "product": ("what",),
    "category": ("what",),
    "use_case": ("why",),
    "sweetness": ("how",),
    "texture": ("how",),
    "flavor": ("how",),
    "nutrition": ("how",),
    "budget": ("how",),
    "needed_at": ("when",),
}


def empty_semantic_state() -> dict[str, dict[str, Any]]:
    return {key: {} for key in W5_KEYS}


def _put(state: dict[str, Any], field: str, value: Any) -> None:
    if field in SEMANTIC_FIELDS and value not in (None, "", "UNKNOWN", [], {}):
        state.setdefault(SEMANTIC_FIELDS[field][0], {})[field] = value


def normalize_semantic_state(raw: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    result = empty_semantic_state()
    for group in W5_KEYS:
        values = (raw or {}).get(group, {})
        if isinstance(values, dict):
            result[group].update({k: v for k, v in values.items() if v not in (None, "", "UNKNOWN")})
    # Accept flat LLM output as well as the canonical 5W shape.
    for field, value in (raw or {}).items():
        if field not in W5_KEYS:
            _put(result, field, value)
    return result


def apply_constraint_updates(current: dict[str, Any] | None, updates: dict[str, Any] | None) -> dict[str, Any]:
    """Apply explicit set/remove/retain semantics without sticky constraints."""
    result = normalize_semantic_state(current)
    updates = updates or {}
    for field, value in (updates.get("set") or {}).items():
        _put(result, field, value)
    for field in updates.get("remove") or []:
        if field in SEMANTIC_FIELDS:
            result[SEMANTIC_FIELDS[field][0]].pop(field, None)
    return result


def merge_understanding_state(previous: dict[str, Any] | None, semantic: dict[str, Any] | None, updates: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    base = normalize_semantic_state(previous)
    explicit = updates or {}
    result = apply_constraint_updates(base, explicit)
    # Semantic state fields are treated as current-turn facts; only non-empty
    # values overwrite their corresponding fields.
    for group, values in normalize_semantic_state(semantic).items():
        for field, value in values.items():
            _put(result, field, value)
    return deepcopy(result)


def semantic_from_constraints(constraints: dict[str, Any] | None) -> dict[str, Any]:
    """Map legacy flat recommendation constraints into the 5W state."""
    result: dict[str, Any] = {}
    for field in ("audience", "texture", "sweetness", "flavor", "nutrition", "category", "categories", "budget"):
        if constraints and constraints.get(field) not in (None, "", [], {}):
            result[field] = constraints[field]
    return result
