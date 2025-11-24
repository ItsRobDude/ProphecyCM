from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from prophecycm.core import Serializable


class DurationType(str, Enum):
    TURNS = "turns"
    ENCOUNTER = "encounter"
    REST = "rest"


class StackingRule(str, Enum):
    STACK = "stack"
    REFRESH = "refresh"
    REPLACE = "replace"


class DispelCondition(str, Enum):
    ANY = "any"
    MAGIC_ONLY = "magic_only"
    NONE = "none"


@dataclass
class StatusEffect(Serializable):
    id: str
    name: str
    duration: int
    modifiers: Dict[str, int] = field(default_factory=dict)
    source: str = ""
    stacking_rule: StackingRule = StackingRule.STACK
    max_stacks: int = 1
    current_stacks: int = 1
    duration_type: DurationType = DurationType.TURNS
    dispel_condition: DispelCondition = DispelCondition.ANY

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "StatusEffect":
        stacking_rule = data.get("stacking_rule", StackingRule.STACK)
        duration_type = data.get("duration_type", DurationType.TURNS)
        dispel_condition = data.get("dispel_condition", DispelCondition.ANY)
        if not isinstance(stacking_rule, StackingRule):
            stacking_rule = StackingRule(str(stacking_rule))
        if not isinstance(duration_type, DurationType):
            duration_type = DurationType(str(duration_type))
        if not isinstance(dispel_condition, DispelCondition):
            dispel_condition = DispelCondition(str(dispel_condition))

        return cls(
            id=data["id"],
            name=data.get("name", ""),
            duration=int(data.get("duration", 0)),
            modifiers=data.get("modifiers", {}),
            source=data.get("source", ""),
            stacking_rule=stacking_rule,
            max_stacks=int(data.get("max_stacks", 1)),
            current_stacks=int(data.get("current_stacks", 1)),
            duration_type=duration_type,
            dispel_condition=dispel_condition,
        )

    def to_dict(self) -> Dict[str, object]:
        payload = super().to_dict()
        payload["stacking_rule"] = self.stacking_rule.value
        payload["duration_type"] = self.duration_type.value
        payload["dispel_condition"] = self.dispel_condition.value
        return payload

    def tick(self, tick_type: DurationType = DurationType.TURNS) -> bool:
        if self.duration_type == tick_type and self.duration > 0:
            self.duration -= 1
        return self.is_active()

    def is_active(self) -> bool:
        return self.duration > 0 or self.duration == -1

    def can_be_dispelled(self, dispel_type: DispelCondition = DispelCondition.ANY) -> bool:
        if self.dispel_condition == DispelCondition.NONE:
            return False
        if self.dispel_condition == DispelCondition.ANY:
            return True
        return dispel_type == self.dispel_condition

    def combine(self, incoming: "StatusEffect") -> None:
        self.stacking_rule = incoming.stacking_rule
        self.max_stacks = max(self.max_stacks, incoming.max_stacks)
        if incoming.stacking_rule == StackingRule.REPLACE:
            self.modifiers = dict(incoming.modifiers)
            self.current_stacks = incoming.current_stacks
            self.duration = incoming.duration
        elif incoming.stacking_rule == StackingRule.REFRESH:
            self.duration = incoming.duration
            self.current_stacks = min(incoming.current_stacks, self.max_stacks)
        else:
            self.current_stacks = min(self.max_stacks, self.current_stacks + incoming.current_stacks)
            self.duration = max(self.duration, incoming.duration)

    def total_modifiers(self) -> Dict[str, int]:
        return {key: value * self.current_stacks for key, value in self.modifiers.items()}
