from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from prophecycm.core import Serializable


@dataclass
class DialogueCondition(Serializable):
    kind: str
    params: Dict[str, object] = field(default_factory=dict)


@dataclass
class DialogueEffect(Serializable):
    kind: str
    params: Dict[str, object] = field(default_factory=dict)


@dataclass
class DialogueChoice(Serializable):
    id: str
    text: str
    conditions: List[DialogueCondition] = field(default_factory=list)
    effects: List[DialogueEffect] = field(default_factory=list)
    next_node_id: Optional[str] = None


@dataclass
class DialogueNode(Serializable):
    id: str
    speaker_id: str
    text: str
    choices: List[DialogueChoice] = field(default_factory=list)
