from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from prophecycm.core import Serializable


@dataclass
class Condition(Serializable):
    """Simple boolean condition for quests and travel requirements."""

    subject: str
    key: str
    comparator: str = "=="
    value: object = True

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Condition":
        return cls(
            subject=data.get("subject", "flag"),
            key=data.get("key", ""),
            comparator=data.get("comparator", "=="),
            value=data.get("value", True),
        )


@dataclass
class QuestEffect(Serializable):
    """Side-effects applied when a quest step resolves."""

    flags: Dict[str, object] = field(default_factory=dict)
    reputation_changes: Dict[str, int] = field(default_factory=dict)
    relationship_changes: Dict[str, int] = field(default_factory=dict)
    rewards: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "QuestEffect":
        return cls(
            flags=data.get("flags", {}),
            reputation_changes=data.get("reputation_changes", {}),
            relationship_changes=data.get("relationship_changes", {}),
            rewards=data.get("rewards", {}),
        )


@dataclass
class QuestStep(Serializable):
    """A single quest step with entry conditions and branching outcomes."""

    id: str
    description: str
    entry_conditions: List[Condition] = field(default_factory=list)
    success_next: Optional[str] = None
    failure_next: Optional[str] = None
    success_effects: QuestEffect = field(default_factory=QuestEffect)
    failure_effects: QuestEffect = field(default_factory=QuestEffect)

    def is_available(self, flags: Dict[str, Any]) -> bool:
        def _compare(lhs: Any, comparator: str, rhs: Any) -> bool:
            if comparator == "==":
                return lhs == rhs
            if comparator == "!=":
                return lhs != rhs
            if comparator == ">=":
                return lhs >= rhs
            if comparator == "<=":
                return lhs <= rhs
            if comparator == ">":
                return lhs > rhs
            if comparator == "<":
                return lhs < rhs
            return False

        for cond in self.entry_conditions:
            lhs = flags.get(cond.key) if cond.subject == "flag" else flags.get(cond.key)
            if not _compare(lhs, cond.comparator, cond.value):
                return False
        return True

    def resolve_effects(self, success: bool = True) -> List[QuestEffect]:
        return [self.success_effects if success else self.failure_effects]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "QuestStep":
        return cls(
            id=data["id"],
            description=data.get("description", ""),
            entry_conditions=[Condition.from_dict(c) for c in data.get("entry_conditions", [])],
            success_next=data.get("success_next"),
            failure_next=data.get("failure_next"),
            success_effects=QuestEffect.from_dict(data.get("success_effects", {})),
            failure_effects=QuestEffect.from_dict(data.get("failure_effects", {})),
        )


@dataclass
class Quest(Serializable):
    id: str
    title: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    steps: List[QuestStep] = field(default_factory=list)
    stage: int = 0
    status: str = "active"
    rewards: Dict[str, int] = field(default_factory=dict)
    step_map: Dict[str, QuestStep] = field(default_factory=dict)
    current_step: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.step_map:
            self.step_map = {step.id: step for step in self.steps}
        if not self.steps and self.step_map:
            self.steps = list(self.step_map.values())

    def available_steps(self, flags: Dict[str, Any]) -> List[QuestStep]:
        return [step for step in self.step_map.values() if step.is_available(flags)]

    def apply_step_result(self, flags: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """Apply effects for the current step and advance to the next step if defined."""

        if self.current_step is None or self.current_step not in self.step_map:
            return flags

        step = self.step_map[self.current_step]
        for effect in step.resolve_effects(success):
            for key, value in effect.flags.items():
                flags[key] = value
        if success and step.success_next:
            self.current_step = step.success_next
        elif not success and step.failure_next:
            self.current_step = step.failure_next
        return flags

    def get_current_step(self) -> Optional[QuestStep]:
        if 0 <= self.stage < len(self.steps):
            return self.steps[self.stage]
        return None

    def find_step_index(self, step_id: str | None) -> Optional[int]:
        if step_id is None:
            return None
        for idx, step in enumerate(self.steps):
            if step.id == step_id:
                return idx
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Quest":
        steps_data = data.get("steps", {})
        if isinstance(steps_data, list):
            step_list = [QuestStep.from_dict(step) for step in steps_data]
            step_map = {step.id: step for step in step_list}
        else:
            step_map = {step_id: QuestStep.from_dict({"id": step_id, **step}) for step_id, step in steps_data.items()}
            step_list = list(step_map.values())
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            objectives=list(data.get("objectives", [])),
            steps=step_list,
            stage=int(data.get("stage", 0)),
            status=data.get("status", "active"),
            rewards=data.get("rewards", {}),
            step_map=step_map,
            current_step=data.get("current_step"),
        )
