from prophecycm.characters import AbilityScore, Creature, CreatureAction, NPC, NPCScalingProfile


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
