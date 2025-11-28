from prophecycm.characters.player import AbilityScore, Class, PlayerCharacter, Race, Skill
from prophecycm.content import seed_save_file
from prophecycm.state import SaveFile


def test_save_file_round_trip():
    save = seed_save_file()
    payload = save.to_json()
    loaded = SaveFile.from_json(payload)

    assert loaded.game_state.pc.name == save.game_state.pc.name
    assert loaded.slot == save.slot


def test_player_character_skill_proficiencies_json_round_trip():
    abilities = {"wisdom": AbilityScore(name="wisdom", score=12)}
    skills = {"perception": Skill(name="perception", key_ability="wisdom", proficiency="trained")}

    pc = PlayerCharacter(
        id="pc-aria",
        name="Aria",
        background="ranger",
        abilities=abilities,
        skills=skills,
        race=Race(id="race.human", name="Human"),
        character_class=Class(id="class.ranger", name="Ranger"),
        skill_proficiencies={"perception"},
    )

    payload = pc.to_json()
    loaded = PlayerCharacter.from_json(payload)

    assert "perception" in loaded.skill_proficiencies
