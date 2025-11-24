import random

from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.player import AbilityScore, PlayerCharacter, Class, Race, Skill
from prophecycm.combat.engine import AttackResult, resolve_attack, roll_dice, roll_initiative, use_consumable_in_combat
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


def test_roll_initiative_sorts_entries():
    pc = build_pc()
    creatures = [build_creature("creature-a", dex=14), build_creature("creature-b", dex=10)]
    rng = random.Random(1)
    order = roll_initiative(pc, creatures, rng)
    initiatives = [entry.initiative for entry in order]
    assert initiatives == sorted(initiatives, reverse=True)
    assert any(entry.ref.kind == "pc" for entry in order)


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
