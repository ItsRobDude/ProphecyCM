from __future__ import annotations

"""Core utilities and base classes shared across the ProphecyCM codebase."""

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="Serializable")


class Serializable:
    """Simple dataclass-aware serialization mixin."""

    def to_dict(self) -> Dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, (list, tuple, set, frozenset)):
                return [convert(v) for v in value]
            if isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            if is_dataclass(value):
                return convert(asdict(value))
            return value

        return convert(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls(**data)

    @classmethod
    def from_json(cls: Type[T], payload: str) -> T:
        return cls.from_dict(json.loads(payload))
