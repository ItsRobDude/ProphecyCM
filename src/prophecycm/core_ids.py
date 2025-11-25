from __future__ import annotations

"""Shared helpers for typed entity identifiers.

Identifiers follow the pattern ``<prefix>.<slug>`` where ``prefix`` is one of the
registered entity categories (``creature``, ``npc``, ``loc``, ``quest``,
``item``, ``faction``) and ``slug`` is a lowercase, dash/underscore separated
string. The helpers here centralize slug generation, validation, and collision
checks so that content parsing can enforce consistency across the project.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Set

DEFAULT_PREFIXES: Set[str] = {
    "class",
    "creature",
    "effect",
    "faction",
    "feat",
    "gear",
    "item",
    "level",
    "loc",
    "npc",
    "option",
    "pc",
    "quest",
    "race",
    "save",
    "skill",
    "start",
}
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_slug(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.lower()).strip("-")
    return slug or "unnamed"


def build_id(prefix: str, value: str) -> str:
    if prefix not in DEFAULT_PREFIXES:
        raise ValueError(f"Unknown id prefix '{prefix}'")
    return f"{prefix}.{normalize_slug(value)}"


def _pattern(allowed_prefixes: Iterable[str]) -> re.Pattern[str]:
    joined = "|".join(sorted(allowed_prefixes))
    return re.compile(rf"^(?:{joined})\.[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def ensure_typed_id(value: str, *, expected_prefix: str | None = None, allowed_prefixes: Iterable[str] = DEFAULT_PREFIXES) -> str:
    pattern = _pattern(allowed_prefixes)
    if pattern.match(value):
        prefix = value.split(".", 1)[0]
        if expected_prefix and prefix != expected_prefix:
            raise ValueError(f"Expected id with prefix '{expected_prefix}', got '{value}'")
        return value

    if expected_prefix is None:
        raise ValueError(f"Missing typed prefix for id '{value}'")
    return build_id(expected_prefix, value)


@dataclass
class IdRegistry:
    """Tracks known ids and enforces the typed-id convention."""

    allowed_prefixes: Set[str] = field(default_factory=lambda: set(DEFAULT_PREFIXES))
    registered: Dict[str, str] = field(default_factory=dict)

    def register(self, value: str, *, expected_prefix: str | None = None) -> str:
        typed = ensure_typed_id(value, expected_prefix=expected_prefix, allowed_prefixes=self.allowed_prefixes)
        prefix = typed.split(".", 1)[0]
        if typed in self.registered and self.registered[typed] != prefix:
            raise ValueError(f"ID collision for '{typed}' (expected {self.registered[typed]} vs {prefix})")
        self.registered.setdefault(typed, prefix)
        return typed

    def require_known(self, value: str, *, expected_prefix: str | None = None, allow_unregistered: bool = False) -> str:
        typed = ensure_typed_id(value, expected_prefix=expected_prefix, allowed_prefixes=self.allowed_prefixes)
        if not allow_unregistered and typed not in self.registered:
            raise ValueError(f"Unknown id '{typed}' (registry contains: {sorted(self.registered)})")
        return typed


DEFAULT_ID_REGISTRY = IdRegistry()

__all__ = [
    "DEFAULT_ID_REGISTRY",
    "DEFAULT_PREFIXES",
    "IdRegistry",
    "build_id",
    "ensure_typed_id",
    "normalize_slug",
]
