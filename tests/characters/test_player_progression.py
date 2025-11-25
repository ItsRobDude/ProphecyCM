from prophecycm.characters import AbilityScore, Class, PlayerCharacter, Race, Skill


def test_recompute_applies_progressions_and_choices() -> None:
    race = Race(
        id="race-progression",
        name="Progressive Folk",
        traits=["keen-sight"],
        bonuses={"armor_class": 1},
        choice_slots={"languages": 1},
        feature_progression={
            1: {
                "features": ["shadow-step"],
                "modifiers": {"reflex": 1, "armor_class": 1},
                "spell_slots": {"1": 1},
            }
        },
    )
    character_class = Class(
        id="class-progression",
        name="Honed Adept",
        hit_die=8,
        save_proficiencies=["reflex", "fortitude"],
        feature_progression={
            2: {
                "features": ["battle-focus"],
                "modifiers": {"hit_points": 3},
                "choice_slots": {"fighting_styles": 1},
            },
            3: {"features": ["channel-divinity"], "spell_slots": {"1": 1, "2": 1}},
        },
        spell_progression={1: {"1": 2}},
        choice_slots={"skill_training": 1},
    )
    abilities = {
        "strength": AbilityScore(name="strength", score=10),
        "dexterity": AbilityScore(name="dexterity", score=12),
        "constitution": AbilityScore(name="constitution", score=12),
        "intelligence": AbilityScore(name="intelligence", score=10),
        "wisdom": AbilityScore(name="wisdom", score=10),
        "charisma": AbilityScore(name="charisma", score=10),
    }
    skills = {
        "perception": Skill(name="perception", key_ability="wisdom"),
        "stealth": Skill(name="stealth", key_ability="dexterity"),
    }

    pc = PlayerCharacter(
        id="pc-test",
        name="Test Hero",
        background="",
        abilities=abilities,
        skills=skills,
        race=race,
        character_class=character_class,
        level=3,
    )

    assert pc.armor_class == 13
    assert pc.saves["reflex"] == 4
    assert pc.hit_points == 30
    assert pc.choice_slots == {"languages": 1, "skill_training": 1, "fighting_styles": 1}
    assert pc.spellcasting == {"1": 4, "2": 1}
    assert set(pc.granted_features) == {
        "keen-sight",
        "shadow-step",
        "battle-focus",
        "channel-divinity",
    }
    assert pc.available_proficiency_packs == {}
