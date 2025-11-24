from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prophecycm.core import Serializable


@dataclass
class QuestCondition(Serializable):
    """Simple flag-based condition for gating quest steps."""

    flag: str
    equals: Any | None = None
    min_value: int | None = None
    description: str = ""

    def is_met(self, flags: Dict[str, Any]) -> bool:
        if self.flag not in flags:
            return False
        value = flags[self.flag]
        if self.equals is not None and value != self.equals:
            return False
        if self.min_value is not None:
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                return False
            if numeric_value < self.min_value:
                return False
        return True

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "QuestCondition":
        return cls(
            flag=str(data.get("flag", "")),
            equals=data.get("equals"),
            min_value=(None if data.get("min_value") is None else int(data.get("min_value", 0))),
            description=data.get("description", ""),
        )


@dataclass
class QuestEffect(Serializable):
    """Effects applied when a step resolves."""

    set_flags: Dict[str, Any] = field(default_factory=dict)
    rewards: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "QuestEffect":
        return cls(
            set_flags=data.get("set_flags", {}),
            rewards=data.get("rewards", {}),
        )


@dataclass
class QuestStep(Serializable):
    """A quest step with conditional entry and branching resolution."""

    id: str
    description: str
    entry_conditions: List[QuestCondition] = field(default_factory=list)
    success_next: Optional[str] = None
    failure_next: Optional[str] = None
    success_effects: List[QuestEffect] = field(default_factory=list)
    failure_effects: List[QuestEffect] = field(default_factory=list)

    def is_available(self, flags: Dict[str, Any]) -> bool:
        return all(condition.is_met(flags) for condition in self.entry_conditions)

    def resolve_effects(self, success: bool = True) -> List[QuestEffect]:
        return self.success_effects if success else self.failure_effects

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "QuestStep":
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            entry_conditions=[QuestCondition.from_dict(cond) for cond in data.get("entry_conditions", [])],
            success_next=data.get("success_next"),
            failure_next=data.get("failure_next"),
            success_effects=[QuestEffect.from_dict(effect) for effect in data.get("success_effects", [])],
            failure_effects=[QuestEffect.from_dict(effect) for effect in data.get("failure_effects", [])],
        )


@dataclass
class Quest(Serializable):
    id: str
    title: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    stage: int = 0
    status: str = "active"
    rewards: Dict[str, int] = field(default_factory=dict)
    steps: Dict[str, QuestStep] = field(default_factory=dict)
    current_step: Optional[str] = None

    def available_steps(self, flags: Dict[str, Any]) -> List[QuestStep]:
        return [step for step in self.steps.values() if step.is_available(flags)]

    def apply_step_result(self, flags: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """Apply effects for the current step and advance to the next step if defined."""

        if self.current_step is None or self.current_step not in self.steps:
            return flags

        step = self.steps[self.current_step]
        for effect in step.resolve_effects(success):
            for key, value in effect.set_flags.items():
                flags[key] = value
        if success and step.success_next:
            self.current_step = step.success_next
        elif not success and step.failure_next:
            self.current_step = step.failure_next
        return flags

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Quest":
        steps_data = data.get("steps", {})
        steps = {step_id: QuestStep.from_dict({"id": step_id, **step}) for step_id, step in steps_data.items()}
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            objectives=list(data.get("objectives", [])),
            stage=int(data.get("stage", 0)),
            status=data.get("status", "active"),
            rewards=data.get("rewards", {}),
            steps=steps,
            current_step=data.get("current_step"),
        )
