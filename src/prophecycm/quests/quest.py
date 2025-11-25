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

    def resolve_effects(self, success: bool = True) -> List[QuestEffect]:
        return [self.success_effects if success else self.failure_effects]


@dataclass
class Quest(Serializable):
    id: str
    title: str
    summary: str
    objectives: List[str] = field(default_factory=list)
    steps: List[QuestStep] = field(default_factory=list)
    step_map: Dict[str, QuestStep] = field(default_factory=dict)
    stage: int = 0
    status: str = "active"
    rewards: Dict[str, int] = field(default_factory=dict)
    current_step: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.step_map:
            self.step_map = {step.id: step for step in self.steps}
        if not self.steps and self.step_map:
            self.steps = list(self.step_map.values())
        if self.current_step is None and self.steps:
            self.current_step = self.steps[self.stage].id

    def available_steps(self, flags: Dict[str, Any]) -> List[QuestStep]:
        return list(self.steps)

    def get_current_step(self) -> Optional[QuestStep]:
        if self.current_step:
            return self.step_map.get(self.current_step)
        if 0 <= self.stage < len(self.steps):
            self.current_step = self.steps[self.stage].id
            return self.steps[self.stage]
        return None

    def apply_step_result(self, flags: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """Apply effects for the current step and advance to the next step if defined."""

        if self.current_step is None:
            return flags

        step = next((s for s in self.steps if s.id == self.current_step), None)
        if step is None:
            return flags
        for effect in step.resolve_effects(success):
            for key, value in effect.flags.items():
                flags[key] = value
        if success and step.success_next:
            self.current_step = step.success_next
        elif not success and step.failure_next:
            self.current_step = step.failure_next
        return flags

        if 0 <= self.stage < len(self.steps):
            self.current_step = self.steps[self.stage].id
        else:
            self.current_step = None
        return flags

    def find_step_index(self, step_id: str | None) -> Optional[int]:
        if step_id is None:
            return None
        for idx, step in enumerate(self.steps):
            if step.id == step_id:
                return idx
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Quest":
        raw_steps = data.get("steps", [])
        steps: List[QuestStep] = []
        if isinstance(raw_steps, dict):
            iterable = raw_steps.items()
        else:
            iterable = [(step.get("id"), step) for step in raw_steps]

        for step_id, step in iterable:
            payload = dict(step)
            payload["id"] = step_id or step.get("id", "")
            steps.append(QuestStep.from_dict(payload))
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            objectives=list(data.get("objectives", [])),
            steps=steps,
            step_map=data.get("step_map", {}),
            stage=int(data.get("stage", 0)),
            status=data.get("status", "active"),
            rewards=data.get("rewards", {}),
            current_step=data.get("current_step"),
        )
