from prophecycm.characters import AbilityScore, Creature, CreatureAction, CreatureTierTemplate, NPC, NPCScalingProfile


def test_npc_applies_scaling_to_attached_stat_block_only():
    base_creature = Creature(
        id="creature-test",
        name="Test Beast",
        level=2,
        role="brute",
        hit_die=8,
        armor_class=12,
        abilities={
            "strength": AbilityScore(name="strength", score=14),
            "dexterity": AbilityScore(name="dexterity", score=12),
            "constitution": AbilityScore(name="constitution", score=13),
        },
        actions=[CreatureAction(name="Claw", attack_ability="strength", to_hit_bonus=1, damage_dice="1d6", damage_bonus=1)],
        save_proficiencies=["fortitude"],
    )

    npc = NPC(
        id="npc-beast-handler",
        archetype="enemy",
        faction_id="rogues",
        disposition="hostile",
        stat_block=base_creature,
        scaling=NPCScalingProfile(base_level=2, attack_progression=1, damage_progression=1),
    )

    scaled = npc.scaled_stat_block(player_level=6, difficulty="hard")

    assert scaled is not None
    assert scaled.level >= base_creature.level
    assert scaled.proficiency_bonus >= base_creature.proficiency_bonus
    assert scaled.hit_points > base_creature.hit_points
    assert scaled.actions[0].to_hit_bonus > base_creature.actions[0].to_hit_bonus
    assert scaled.actions[0].damage_bonus > base_creature.actions[0].damage_bonus

    # Base creature remains unscaled to keep authored stats intact.
    assert base_creature.level == 2


def test_creatures_track_permanent_death_when_hit_points_drop():
    creature = Creature(
        id="creature-husk",
        name="Husk",
        level=1,
        role="minion",
        hit_die=6,
        armor_class=11,
        abilities={
            "strength": AbilityScore(name="strength", score=8),
            "dexterity": AbilityScore(name="dexterity", score=10),
            "constitution": AbilityScore(name="constitution", score=10),
        },
        actions=[CreatureAction(name="Swipe", attack_ability="strength", to_hit_bonus=0, damage_dice="1d4", damage_bonus=0)],
    )

    creature.apply_damage(creature.hit_points + 5)
    assert creature.is_alive is False
    assert creature.current_hit_points == 0

    # Recomputing stats should not revive the creature.
    creature.recompute_statistics()
    assert creature.is_alive is False
    assert creature.current_hit_points == 0


def test_creature_parses_adjustment_notes_into_tiers():
    notes = "\n".join(
        [
            "For a Less Difficult Encounter: Reduce hit points and damage output.",
            "For a More Difficult Encounter: Increase hit points and attack bonus.",
        ]
    )

    creature = Creature.from_dict(
        {
            "id": "creature-tiered",
            "name": "Tiered Foe",
            "level": 5,
            "role": "elite",
            "hit_die": 8,
            "armor_class": 12,
            "abilities": {
                "strength": {"score": 14},
                "dexterity": {"score": 14},
                "constitution": {"score": 14},
            },
            "actions": [
                {
                    "name": "Strike",
                    "attack_ability": "strength",
                    "to_hit_bonus": 5,
                    "damage_dice": "1d8",
                    "damage_bonus": 3,
                }
            ],
            "adjustment_notes": notes,
        }
    )

    difficulties = sorted(tier.difficulty for tier in creature.tiers)
    assert difficulties == ["easy", "hard"]
    assert any(tier.level_adjustment == -1 for tier in creature.tiers)
    assert any(tier.level_adjustment == 1 for tier in creature.tiers)


def test_npc_scaling_prefers_tier_templates_for_progression():
    base_creature = Creature(
        id="tiered-creature",
        name="Tiered Beast",
        level=5,
        role="brute",
        hit_die=8,
        armor_class=12,
        abilities={
            "strength": AbilityScore(name="strength", score=16),
            "dexterity": AbilityScore(name="dexterity", score=14),
            "constitution": AbilityScore(name="constitution", score=14),
        },
        actions=[CreatureAction(name="Claw", attack_ability="strength", to_hit_bonus=5, damage_dice="1d8", damage_bonus=3)],
        tiers=[
            CreatureTierTemplate(
                name="less_difficult",
                difficulty="easy",
                level_adjustment=-1,
                attack_adjustment=-1,
                damage_adjustment=-1,
                hit_point_adjustment=-5,
                armor_class_adjustment=-1,
            ),
            CreatureTierTemplate(
                name="more_difficult",
                difficulty="hard",
                level_adjustment=1,
                attack_adjustment=1,
                damage_adjustment=2,
                hit_point_adjustment=8,
                armor_class_adjustment=1,
            ),
        ],
        save_proficiencies=["fortitude"],
    )

    npc = NPC(
        id="npc-tiered",
        archetype="enemy",
        faction_id="rogues",
        disposition="hostile",
        stat_block=base_creature,
        scaling=NPCScalingProfile(base_level=5, attack_progression=1, damage_progression=1),
    )

    intro_scaled = npc.scaled_stat_block(player_level=3, difficulty="easy")
    assert intro_scaled is not None
    assert intro_scaled.applied_tier == "less_difficult"
    assert intro_scaled.level == 4
    assert intro_scaled.hit_points < base_creature.hit_points
    assert intro_scaled.actions[0].to_hit_bonus == 4
    assert intro_scaled.actions[0].damage_bonus == 2

    advanced_scaled = npc.scaled_stat_block(player_level=8, difficulty="hard")
    assert advanced_scaled is not None
    assert advanced_scaled.applied_tier == "more_difficult"
    assert advanced_scaled.level == 8
    assert advanced_scaled.hit_points > base_creature.hit_points
    assert advanced_scaled.actions[0].to_hit_bonus == 8
    assert advanced_scaled.actions[0].damage_bonus == 7


def test_npc_scaling_preserves_tier_bonuses_at_same_level():
    base_creature = Creature(
        id="tiered-creature",
        name="Tiered Beast",
        level=5,
        role="brute",
        hit_die=8,
        armor_class=12,
        abilities={
            "strength": AbilityScore(name="strength", score=16),
            "dexterity": AbilityScore(name="dexterity", score=14),
            "constitution": AbilityScore(name="constitution", score=14),
        },
        actions=[CreatureAction(name="Claw", attack_ability="strength", to_hit_bonus=5, damage_dice="1d8", damage_bonus=3)],
        tiers=[
            CreatureTierTemplate(
                name="more_difficult",
                difficulty="hard",
                level_adjustment=1,
                attack_adjustment=1,
                damage_adjustment=2,
                hit_point_adjustment=8,
                armor_class_adjustment=1,
            ),
        ],
        save_proficiencies=["fortitude"],
    )

    npc = NPC(
        id="npc-tiered",
        archetype="enemy",
        faction_id="rogues",
        disposition="hostile",
        stat_block=base_creature,
        scaling=NPCScalingProfile(base_level=5, attack_progression=1, damage_progression=1),
    )

    scaled = npc.scaled_stat_block(player_level=5, difficulty="hard")
    assert scaled is not None
    assert scaled.applied_tier == "more_difficult"
    assert scaled.level == 5
    assert scaled.hit_points > base_creature.hit_points
    # Tier bonuses should not be erased by progression when the encounter level matches the base creature level.
    assert scaled.actions[0].to_hit_bonus == 6
    assert scaled.actions[0].damage_bonus == 5
