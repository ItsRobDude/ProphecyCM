from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from prophecycm.dialogue.model import DialogueChoice, DialogueCondition, DialogueEffect, DialogueNode


@dataclass
class DialogueScript:
    """Represents a parsed branching dialogue."""

    nodes: Dict[str, DialogueNode]
    start_node_id: str


_NODE_HEADER = re.compile(r"^\[(?P<node_id>[^\]]+)\]\s*Speaker\s*=\s*(?P<speaker_id>.+)$")
_CHOICE_LINE = re.compile(
    r"^>\s*\[(?P<choice_id>[^\]]+)\]\s*(?P<choice_text>.*?)(?:\s*->\s*(?P<next>[\w\.-]+|END))?$",
    flags=re.IGNORECASE,
)


def _coerce_value(raw: str) -> object:
    lowered = raw.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if raw.isdigit():
        return int(raw)
    try:
        return float(raw)
    except ValueError:
        return raw


def _parse_params(param_text: str | None) -> Dict[str, object]:
    if not param_text:
        return {}
    params: Dict[str, object] = {}
    for token in shlex.split(param_text):
        if "=" not in token:
            continue
        key, raw_value = token.split("=", 1)
        params[key.strip()] = _coerce_value(raw_value.strip())
    return params


def _finalize_choice(choices: List[DialogueChoice], pending: DialogueChoice | None) -> None:
    if pending is not None:
        choices.append(pending)


def _flush_node(
    nodes: Dict[str, DialogueNode],
    node_id: str | None,
    speaker_id: str | None,
    text_lines: Iterable[str],
    choices: List[DialogueChoice],
) -> None:
    if node_id is None or speaker_id is None:
        return
    text = "\n".join(line.rstrip() for line in text_lines).strip()
    nodes[node_id] = DialogueNode(id=node_id, speaker_id=speaker_id.strip(), text=text, choices=list(choices))


def _parse_dialogue_text(text: str) -> DialogueScript:
    nodes: Dict[str, DialogueNode] = {}
    current_node: tuple[str | None, str | None] = (None, None)
    text_lines: List[str] = []
    choices: List[DialogueChoice] = []
    pending_choice: DialogueChoice | None = None
    start_node: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue

        header_match = _NODE_HEADER.match(line)
        if header_match:
            _finalize_choice(choices, pending_choice)
            _flush_node(nodes, current_node[0], current_node[1], text_lines, choices)
            node_id = header_match.group("node_id")
            speaker_id = header_match.group("speaker_id")
            current_node = (node_id, speaker_id)
            text_lines = []
            choices = []
            pending_choice = None
            if start_node is None:
                start_node = node_id
            continue

        choice_match = _CHOICE_LINE.match(line)
        if choice_match:
            _finalize_choice(choices, pending_choice)
            next_id = choice_match.group("next")
            pending_choice = DialogueChoice(
                id=choice_match.group("choice_id"),
                text=choice_match.group("choice_text").strip(),
                next_node_id=None if not next_id or next_id.upper() == "END" else next_id,
            )
            continue

        stripped = line.lstrip()
        if stripped.lower().startswith("effect:") and pending_choice is not None:
            _, _, remainder = stripped.partition(":")
            kind, _, param_text = remainder.strip().partition(" ")
            pending_choice.effects.append(DialogueEffect(kind=kind, params=_parse_params(param_text)))
            continue

        if stripped.lower().startswith("condition:") and pending_choice is not None:
            _, _, remainder = stripped.partition(":")
            kind, _, param_text = remainder.strip().partition(" ")
            pending_choice.conditions.append(DialogueCondition(kind=kind, params=_parse_params(param_text)))
            continue

        text_lines.append(line)

    _finalize_choice(choices, pending_choice)
    _flush_node(nodes, current_node[0], current_node[1], text_lines, choices)

    if start_node is None:
        raise ValueError("Dialogue script contained no node headers to anchor a start node.")

    return DialogueScript(nodes=nodes, start_node_id=start_node)


def _build_linear_dialogue(beats: List[str], *, flag_id: str | None = None, quest_id: str | None = None) -> DialogueScript:
    nodes: Dict[str, DialogueNode] = {}
    active_beats = beats or ["Prince Alderic shares the canonical route in measured tones."]
    start_id = "beat-1"

    for idx, beat in enumerate(active_beats):
        node_id = f"beat-{idx + 1}"
        next_id = f"beat-{idx + 2}" if idx + 1 < len(active_beats) else "decision"
        choice_id = f"continue-{idx + 1}"
        nodes[node_id] = DialogueNode(
            id=node_id,
            speaker_id="npc.prince-alderic",
            text=beat.strip(),
            choices=[DialogueChoice(id=choice_id, text="Continue", next_node_id=next_id)],
        )

    decision_choices: List[DialogueChoice] = []
    if quest_id:
        accept_effects = [DialogueEffect(kind="advance_quest", params={"quest_id": quest_id, "success": True})]
    else:
        accept_effects = []
    if flag_id:
        accept_effects.append(DialogueEffect(kind="set_flag", params={"flag": flag_id, "value": True}))
        decline_effects = [DialogueEffect(kind="set_flag", params={"flag": flag_id, "value": False})]
    else:
        decline_effects = []

    decision_choices.append(DialogueChoice(id="accept", text="Accept Alderic's charge", effects=accept_effects))
    decision_choices.append(DialogueChoice(id="decline", text="Step back from the table", effects=decline_effects))

    nodes["decision"] = DialogueNode(
        id="decision",
        speaker_id="npc.prince-alderic",
        text="Alderic awaits your response, the Mark of Ciara glinting between you.",
        choices=decision_choices,
    )

    return DialogueScript(nodes=nodes, start_node_id=start_id)


def load_dialogue_script(
    path: Path,
    *,
    fallback_beats: List[str] | None = None,
    flag_id: str | None = None,
    quest_id: str | None = None,
) -> DialogueScript:
    """Parse a branching dialogue text file into runtime dialogue nodes.

    The expected format is a lightly structured text document:

    * Nodes start with ``[node.id] Speaker=npc.id``.
    * Dialogue text continues until a choice line is encountered.
    * Choices begin with ``> [choice.id] Choice text -> next_node_id``.
    * Optional indented ``effect:`` and ``condition:`` lines attach metadata to the
      most recent choice using space-separated ``key=value`` parameters.

    If the provided ``path`` does not exist, the loader builds a linear fallback
    script from ``fallback_beats`` so existing tests can continue to run without
    the authored branching file.
    """

    if path.exists():
        return _parse_dialogue_text(path.read_text(encoding="utf-8"))

    beats = fallback_beats or []
    return _build_linear_dialogue(beats, flag_id=flag_id, quest_id=quest_id)
