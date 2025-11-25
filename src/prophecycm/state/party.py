from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable
from prophecycm.characters import PlayerCharacter


def _dedupe(sequence: List[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for entry in sequence:
        if entry in seen:
            continue
        seen.add(entry)
        ordered.append(entry)
    return ordered


@dataclass
class PartyRoster(Serializable):
    leader_id: str = ""
    active_companions: List[str] = field(default_factory=list)
    reserve_companions: List[str] = field(default_factory=list)
    shared_resources: Dict[str, int] = field(default_factory=dict)
    companion_settings: Dict[str, Dict[str, object]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object] | None, default_leader_id: str = "") -> "PartyRoster":
        data = data or {}
        return cls(
            leader_id=str(data.get("leader_id", default_leader_id)),
            active_companions=list(data.get("active_companions", [])),
            reserve_companions=list(data.get("reserve_companions", [])),
            shared_resources={k: int(v) for k, v in data.get("shared_resources", {}).items()},
            companion_settings={k: dict(v) for k, v in data.get("companion_settings", {}).items()},
        )

    def __post_init__(self) -> None:
        self.active_companions = _dedupe(self.active_companions)
        self.reserve_companions = _dedupe(self.reserve_companions)

    def ensure_member(self, companion_id: str, *, active: bool = True) -> None:
        """Add or move a companion into the desired slot, removing duplicates."""

        if not companion_id:
            return
        self.active_companions = [c for c in self.active_companions if c != companion_id]
        self.reserve_companions = [c for c in self.reserve_companions if c != companion_id]
        if active:
            self.active_companions.append(companion_id)
        else:
            self.reserve_companions.append(companion_id)

    def sync_with_pc(self, pc: PlayerCharacter) -> None:
        """Guarantee the party roster includes the player character."""

        if not self.leader_id:
            self.leader_id = pc.id
        if pc.id not in self.active_companions and pc.id not in self.reserve_companions:
            self.active_companions.insert(0, pc.id)
        elif pc.id in self.reserve_companions:
            self.reserve_companions = [c for c in self.reserve_companions if c != pc.id]
            self.active_companions.insert(0, pc.id)
        self.active_companions = _dedupe(self.active_companions)
