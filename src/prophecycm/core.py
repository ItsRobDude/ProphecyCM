from __future__ import annotations

"""Core utilities and base classes shared across the ProphecyCM codebase."""

from dataclasses import asdict
import json
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="Serializable")


class Serializable:
    """Simple dataclass-aware serialization mixin."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls(**data)

    @classmethod
    def from_json(cls: Type[T], payload: str) -> T:
        return cls.from_dict(json.loads(payload))
