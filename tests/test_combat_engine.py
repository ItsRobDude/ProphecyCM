import random

from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.player import AbilityScore, PlayerCharacter, Class, Race, Skill
from prophecycm.combat.engine import (
    AttackResult,
    CombatantRef,
    EncounterState,
    EncounterResult,
    start_encounter,
    process_turn_commands,
    resolve_attack,
    roll_dice,
    roll_initiative,
    use_consumable_in_combat,
)
from prophecycm.items.item import Consumable


def build_pc() -> PlayerCharacter:
    abilities = {
        "strength": AbilityScore(name="strength", score=14),
        "dexterity": AbilityScore(name="dexterity", score=12),
        "constitution": AbilityScore(name="constitution", score=12),
        "wisdom": AbilityScore(name="wisdom", score=10),
        "intelligence": AbilityScore(name="intelligence", score=10),
        "charisma": AbilityScore(name="charisma", score=8),
    }
    skills = {"perception": Skill(name="perception", key_ability="wisdom", proficiency="trained")}
    return PlayerCharacter(
        id="pc-aria",
        name="Aria",
        background="ranger",
        abilities=abilities,
        skills=skills,
        race=Race(id="human", name="Human"),
        character_class=Class(id="ranger", name="Ranger", hit_die=10, save_proficiencies=["fortitude", "reflex"]),
    )


def build_creature(creature_id: str, dex: int = 12, hit_die: int = 6) -> Creature:
    abilities = {
        "strength": AbilityScore(name="strength", score=12),
        "dexterity": AbilityScore(name="dexterity", score=dex),
        "constitution": AbilityScore(name="constitution", score=12),
        "wisdom": AbilityScore(name="wisdom", score=10),
    }
    actions = [CreatureAction(name="Claw", attack_ability="strength", damage_dice="1d6", damage_bonus=1)]
    return Creature(
        id=creature_id,
        name="Wolf",
        level=1,
        role="brute",
        hit_die=hit_die,
        armor_class=12,
        abilities=abilities,
        actions=actions,
    )


def build_companion(companion_id: str, dex: int = 12) -> Creature:
    companion = build_creature(companion_id, dex=dex)
    companion.name = "Companion"
    return companion


def test_roll_initiative_sorts_entries():
    pc = build_pc()
    creatures = [build_creature("creature-a", dex=14), build_creature("creature-b", dex=10)]
    rng = random.Random(1)
    order = roll_initiative(pc, creatures, rng)
    initiatives = [entry.initiative for entry in order]
    assert initiatives == sorted(initiatives, reverse=True)
    assert any(entry.ref.kind == "pc" for entry in order)


def test_roll_initiative_includes_allies():
    pc = build_pc()
    companion = build_companion("ally-1", dex=16)
    creatures = [build_creature("creature-a", dex=8)]
    rng = random.Random(2)

    order = roll_initiative(pc, creatures, rng, allies=[companion])

    initiatives = [entry.initiative for entry in order]
    assert initiatives == sorted(initiatives, reverse=True)
    assert CombatantRef("npc", companion.id) in [entry.ref for entry in order]


def test_resolve_attack_hits_and_kills_target():
    rng = random.Random(0)
    attacker = build_creature("attacker", dex=10)
    defender = build_creature("defender", dex=10, hit_die=4)
    defender.armor_class = 8
    action = attacker.actions[0]
    action.to_hit_bonus = 10
    defender.current_hit_points = 2
    result = resolve_attack(attacker, defender, action, rng)
    assert isinstance(result, AttackResult)
    assert result.hit
    assert defender.current_hit_points <= 0
    assert not defender.is_alive


def test_roll_dice_parses_expression():
    rng = random.Random(0)
    assert roll_dice("2d4+1", rng) >= 3


def test_use_consumable_heals_creature_and_consumes_charge():
    pc = build_pc()
    creature = build_creature("wounded")
    creature.apply_damage(2)
    potion = Consumable(id="healing-potion", name="Healing Potion", effect_id="heal_5", charges=1)
    pc.inventory.append(potion)
    healed = use_consumable_in_combat(pc, potion, creature)
    assert healed
    assert creature.current_hit_points == creature.hit_points
    assert potion not in pc.inventory


def test_process_turn_consumes_ap_and_targets_enemy():
    rng = random.Random(2)
    pc = build_pc()
    creatures = [build_creature("wolf", dex=8)]
    encounter = start_encounter("enc-1", pc, creatures, rng)
    action = CreatureAction(name="Quick Shot", attack_ability="dexterity", damage_dice="1d4", to_hit_bonus=5)
    command = {"type": "attack", "target": CombatantRef("creature", creatures[0].id), "action": action}

    result: EncounterResult = process_turn_commands(encounter, pc, creatures, [command], rng)

    assert result.context.remaining_ap == 2
    assert creatures[0].current_hit_points < creatures[0].hit_points
    assert any(entry.target and entry.target.id == creatures[0].id for entry in result.log)


def test_allies_help_win_multi_enemy_encounter():
    rng = random.Random(4)
    pc = build_pc()
    companion = build_companion("ally-2", dex=14)
    enemies = [build_creature("gob-1", dex=8, hit_die=4), build_creature("gob-2", dex=8, hit_die=4)]
    for enemy in enemies:
        enemy.current_hit_points = 2
    pc_action = CreatureAction(name="Strike", attack_ability="strength", damage_dice="1d10", to_hit_bonus=10, damage_bonus=5)
    companion_action = CreatureAction(
        name="Assist", attack_ability="strength", damage_dice="1d8", to_hit_bonus=8, damage_bonus=4
    )
    rewards: list[dict] = []

    def reward_hook(enc: object, actor: object, foes: object) -> dict:
        payload = {"xp": 75}
        rewards.append(payload)
        return payload

    encounter = start_encounter("enc-allies", pc, enemies, rng, allies=[companion])
    pc_command = {"type": "attack", "target": CombatantRef("creature", enemies[0].id), "action": pc_action}
    pc_result = process_turn_commands(encounter, pc, enemies, [pc_command], rng, rewards_hook=reward_hook, allies=[companion])

    assert pc_result.status == "ongoing"
    assert enemies[0].is_alive is False

    # Advance to the companion's turn and finish the encounter
    companion_ref = CombatantRef("npc", companion.id)
    encounter.active_index = next(i for i, entry in enumerate(encounter.turn_order) if entry.ref == companion_ref)
    companion_command = {"type": "attack", "target": CombatantRef("creature", enemies[1].id), "action": companion_action}
    final_result = process_turn_commands(
        encounter, pc, enemies, [companion_command], rng, rewards_hook=reward_hook, allies=[companion]
    )

    assert final_result.status == "victory"
    assert len(rewards) == 1 and rewards[0]["xp"] == 75
    assert all(not enemy.is_alive for enemy in enemies)


def test_defeat_requires_all_allies_to_fall():
    rng = random.Random(6)
    pc = build_pc()
    companion = build_companion("ally-3", dex=12)
    enemy = build_creature("ogre", dex=10, hit_die=10)

    pc.apply_damage(pc.hit_points or 10)
    encounter = start_encounter("enc-down", pc, [enemy], rng, allies=[companion])
    companion_ref = CombatantRef("npc", companion.id)
    encounter.active_index = next(i for i, entry in enumerate(encounter.turn_order) if entry.ref.kind == "creature")

    crushing_blow = CreatureAction(
        name="Smash", attack_ability="strength", damage_dice="1d12", to_hit_bonus=12, damage_bonus=20
    )
    command = {"type": "attack", "target": companion_ref, "action": crushing_blow}
    result = process_turn_commands(encounter, pc, [enemy], [command], rng, allies=[companion])

    assert result.status == "defeat"


def test_victory_triggers_rewards_and_marks_end_of_combat():
    rng = random.Random(1)
    pc = build_pc()
    creatures = [build_creature("minion", dex=8, hit_die=4)]
    creatures[0].current_hit_points = 1
    encounter = start_encounter("enc-2", pc, creatures, rng)
    action = CreatureAction(name="Finisher", attack_ability="strength", damage_dice="1d12", to_hit_bonus=10, damage_bonus=5)
    rewards: list[dict] = []

    def reward_hook(enc: object, actor: object, foes: object) -> dict:
        payload = {"xp": 25, "loot": []}
        rewards.append(payload)
        return payload

    command = {"type": "attack", "target": CombatantRef("creature", creatures[0].id), "action": action}
    result = process_turn_commands(encounter, pc, creatures, [command], rng, rewards_hook=reward_hook)

    assert result.status == "victory"
    assert rewards and rewards[0]["xp"] == 25
    assert not creatures[0].is_alive


def test_defeat_and_flee_end_states():
    rng = random.Random(3)
    pc = build_pc()
    creatures = [build_creature("predator", dex=12)]
    pc.current_hit_points = 1
    encounter = start_encounter("enc-3", pc, creatures, rng)
    # Give creature the first turn so it can defeat the PC
    encounter.active_index = 1 if len(encounter.turn_order) > 1 else 0
    attack_command = {
        "type": "attack",
        "target": CombatantRef("pc", pc.id),
        "action": CreatureAction(name="Bite", attack_ability="strength", damage_dice="1d10", to_hit_bonus=10),
    }

    defeat_result = process_turn_commands(encounter, pc, creatures, [attack_command], rng)
    assert defeat_result.status == "defeat"

    flee_encounter = start_encounter("enc-4", pc, creatures, rng)
    flee_result = process_turn_commands(
        flee_encounter,
        pc,
        creatures,
        [{"type": "flee", "ap_cost": 3}],
        rng,
    )
    assert flee_result.status == "fled"


def test_process_turn_defaults_allies_from_encounter_meta():
    rng = random.Random(7)
    pc = build_pc()
    companion = build_companion("ally-meta", dex=14)
    enemy = build_creature("bandit", dex=10)
    enemy.armor_class = 8

    encounter = start_encounter("enc-meta", pc, [enemy], rng, allies=[companion])
    companion_ref = CombatantRef("npc", companion.id)
    encounter.active_index = next(i for i, entry in enumerate(encounter.turn_order) if entry.ref == companion_ref)

    assist_action = CreatureAction(name="Assist", attack_ability="strength", damage_dice="1d8", to_hit_bonus=12)
    command = {"type": "attack", "target": CombatantRef("creature", enemy.id), "action": assist_action}

    result = process_turn_commands(encounter, pc, [enemy], [command], rng)

    assert result.status in {"ongoing", "victory"}
    assert enemy.current_hit_points < enemy.hit_points
    assert result.log and result.log[0].actor == companion_ref
