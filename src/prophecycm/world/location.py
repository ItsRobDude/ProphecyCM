from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from prophecycm.core import Serializable


@dataclass
class TravelConnection(Serializable):
    target: str
    travel_time: int = 1
    danger: float = 1.0
    requirements: List[Dict[str, object]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "TravelConnection":
        return cls(
            target=data.get("target", ""),
            travel_time=int(data.get("travel_time", 1)),
            danger=float(data.get("danger", 1.0)),
            requirements=list(data.get("requirements", [])),
        )


@dataclass
class Location(Serializable):
    id: str
    name: str
    biome: str
    faction_control: str
    points_of_interest: List[str] = field(default_factory=list)
    encounter_tables: Dict[str, List[str]] = field(default_factory=dict)
    connections: List[TravelConnection] = field(default_factory=list)
    travel_rules: Dict[str, object] = field(default_factory=dict)
    danger_level: str = "low"

    def get_connection(self, target_id: str) -> TravelConnection | None:
        for connection in self.connections:
            if connection.target == target_id:
                return connection
        return None

    def get_encounter_table(self, context: str) -> List[str]:
        return self.encounter_tables.get(context, self.encounter_tables.get("default", []))

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Location":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            biome=data.get("biome", ""),
            faction_control=data.get("faction_control", ""),
            points_of_interest=list(data.get("points_of_interest", [])),
            encounter_tables=data.get("encounter_tables", {}),
            connections=[TravelConnection.from_dict(conn) for conn in data.get("connections", [])],
            travel_rules=data.get("travel_rules", {}),
            danger_level=data.get("danger_level", "low"),
        )
