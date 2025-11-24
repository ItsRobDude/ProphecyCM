from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable


@dataclass
class Location(Serializable):
    id: str
    name: str
    biome: str
    faction_control: str
    points_of_interest: List[str] = field(default_factory=list)
    encounter_tables: Dict[str, List[str]] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)
    danger_level: str = "stable"
    tags: List[str] = field(default_factory=list)
    fast_travel_requires_visit: bool = True
    visited: bool = False

    def is_connected(self, destination_id: str) -> bool:
        return destination_id in self.connections

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Location":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            biome=data.get("biome", ""),
            faction_control=data.get("faction_control", ""),
            points_of_interest=list(data.get("points_of_interest", [])),
            encounter_tables=data.get("encounter_tables", {}),
            connections=list(data.get("connections", [])),
            danger_level=data.get("danger_level", "stable"),
            tags=list(data.get("tags", [])),
            fast_travel_requires_visit=bool(data.get("fast_travel_requires_visit", True)),
            visited=bool(data.get("visited", False)),
        )
