import textwrap
from pathlib import Path

from prophecycm.dialogue.loader import DialogueScript, load_dialogue_script


def test_loads_branching_dialogue(tmp_path: Path) -> None:
    dialogue_text = textwrap.dedent(
        """
        [intro] Speaker=npc.prince-alderic
        Aldric greets you at the map-table.

        > [accept] Take the mark -> end
          effect: set_flag flag=briefing.alderic.canonical value=True
          effect: advance_quest quest_id=quest.main-quest-aodhan success=True
        > [ask] Ask for more details -> intro
          condition: flag_equals flag=briefing.alderic.canonical value=False
        """
    )
    path = tmp_path / "branching.txt"
    path.write_text(dialogue_text, encoding="utf-8")

    script = load_dialogue_script(path)
    assert isinstance(script, DialogueScript)
    assert script.start_node_id == "intro"
    intro_node = script.nodes["intro"]
    assert intro_node.text.startswith("Aldric greets you")
    assert len(intro_node.choices) == 2
    accept_choice = next(choice for choice in intro_node.choices if choice.id == "accept")
    assert any(effect.kind == "advance_quest" for effect in accept_choice.effects)
    ask_choice = next(choice for choice in intro_node.choices if choice.id == "ask")
    assert any(condition.kind == "flag_equals" for condition in ask_choice.conditions)
    assert accept_choice.next_node_id is None


def test_fallback_linear_dialogue(tmp_path: Path) -> None:
    missing_path = tmp_path / "does-not-exist.txt"
    beats = ["First", "Second"]
    script = load_dialogue_script(missing_path, fallback_beats=beats, flag_id="briefing.flag", quest_id="quest")

    assert script.start_node_id == "beat-1"
    assert len(script.nodes) == 3  # two beats + decision
    decision = script.nodes["decision"]
    assert any(choice.id == "accept" for choice in decision.choices)
    accept_choice = next(choice for choice in decision.choices if choice.id == "accept")
    assert any(effect.kind == "advance_quest" for effect in accept_choice.effects)
