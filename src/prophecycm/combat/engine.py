from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Literal, Optional, Sequence

from prophecycm.characters.creature import Creature, CreatureAction
from prophecycm.characters.player import AbilityScore, PlayerCharacter
from prophecycm.core import Serializable
from prophecycm.items.item import Consumable


@dataclass
class CombatantRef(Serializable):
    kind: Literal["pc", "creature", "npc"]
    id: str

    @classmethod
    def from_dict(cls, data: dict[str, object] | "CombatantRef") -> "CombatantRef":  # type: ignore[override]
        if isinstance(data, cls):
            return data
        return cls(**data)


@dataclass
class TurnOrderEntry(Serializable):
    ref: CombatantRef
    initiative: int
    is_conscious: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, object] | "TurnOrderEntry") -> "TurnOrderEntry":  # type: ignore[override]
        if isinstance(data, cls):
            return data
        ref = data.get("ref") if isinstance(data, dict) else None
        ref_obj = CombatantRef.from_dict(ref) if isinstance(ref, (dict, CombatantRef)) else ref
        remaining = {k: v for k, v in data.items() if k != "ref"} if isinstance(data, dict) else {}
        return cls(ref=ref_obj, **remaining)


@dataclass
class EncounterState(Serializable):
    id: str
    participants: List[CombatantRef]
    turn_order: List[TurnOrderEntry]
    active_index: int = 0
    round: int = 1
    difficulty: str = "standard"
    meta: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, object] | "EncounterState") -> "EncounterState":  # type: ignore[override]
        if isinstance(data, cls):
            return data

        participants_raw = data.get("participants", []) if isinstance(data, dict) else []
        turn_order_raw = data.get("turn_order", []) if isinstance(data, dict) else []

        participants = [CombatantRef.from_dict(p) for p in participants_raw]
        turn_order = [TurnOrderEntry.from_dict(entry) for entry in turn_order_raw]

        payload = dict(data) if isinstance(data, dict) else {}
        payload["participants"] = participants
        payload["turn_order"] = turn_order
        return cls(**payload)


@dataclass
class TurnContext(Serializable):
    actor: CombatantRef
    remaining_ap: int = 3


@dataclass
class CombatLogEntry(Serializable):
    round: int
    actor: CombatantRef
    action: str
    target: Optional[CombatantRef]
    message: str


@dataclass
class EncounterResult(Serializable):
    state: EncounterState
    context: TurnContext
    log: List[CombatLogEntry]
    status: Literal["ongoing", "victory", "defeat", "fled"] = "ongoing"
    rewards: Optional[dict[str, object]] = None


@dataclass
class AttackResult(Serializable):
    hit: bool
    crit: bool
    damage: int
    target_died: bool


def roll_dice(expression: str, rng: Optional[random.Random] = None) -> int:
    """Parse and roll a simple NdM(+/-)K dice expression."""

    rng = rng or random.Random()
    match = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", expression.strip())
    if not match:
        return 0

    num, die, modifier = match.groups()
    total = sum(rng.randint(1, int(die)) for _ in range(int(num)))
    if modifier:
        total += int(modifier)
    return total


def roll_initiative(
    pc: PlayerCharacter,
    creatures: List[Creature],
    rng: random.Random,
    allies: Optional[Sequence[Creature]] = None,
) -> List[TurnOrderEntry]:
    entries_with_keys: List[tuple[TurnOrderEntry, tuple[float, float, str, float]]] = []

    pc_dex_mod = pc.abilities.get("dexterity", AbilityScore()).modifier
    pc_init_roll = rng.randint(1, 20) + pc.initiative
    entries_with_keys.append(
        (
            TurnOrderEntry(CombatantRef("pc", pc.id), pc_init_roll),
            (-pc_init_roll, -pc_dex_mod, pc.id, rng.random()),
        )
    )

    allies = allies or []
    for ally in allies:
        dex_mod = ally.abilities.get("dexterity", AbilityScore()).modifier
        init_mod = dex_mod + ally.proficiency_bonus
        roll = rng.randint(1, 20) + init_mod
        entries_with_keys.append(
            (
                TurnOrderEntry(CombatantRef("npc", ally.id), roll),
                (-roll, -dex_mod, ally.id, rng.random()),
            )
        )

    for creature in creatures:
        dex_mod = creature.abilities.get("dexterity", AbilityScore()).modifier
        init_mod = dex_mod + creature.proficiency_bonus
        roll = rng.randint(1, 20) + init_mod
        entries_with_keys.append(
            (
                TurnOrderEntry(CombatantRef("creature", creature.id), roll),
                (-roll, -dex_mod, creature.id, rng.random()),
            )
        )

    entries_with_keys.sort(key=lambda entry: entry[1])
    return [entry for entry, _ in entries_with_keys]


def resolve_attack(
    attacker: Creature | PlayerCharacter,
    defender: Creature | PlayerCharacter,
    action: CreatureAction,
    rng: random.Random,
) -> AttackResult:
    ability = attacker.abilities.get(action.attack_ability, AbilityScore())
    attack_mod = ability.modifier + getattr(attacker, "proficiency_bonus", 0) + action.to_hit_bonus
    roll = rng.randint(1, 20)

    crit = roll == 20
    hit_roll = roll + attack_mod

    if crit or hit_roll >= defender.armor_class:
        base_damage = roll_dice(action.damage_dice, rng) + action.damage_bonus + ability.modifier
        if crit:
            base_damage *= 2
        defender.apply_damage(base_damage)
        return AttackResult(hit=True, crit=crit, damage=base_damage, target_died=not defender.is_alive)

    return AttackResult(hit=False, crit=False, damage=0, target_died=False)


def use_consumable_in_combat(
    pc: PlayerCharacter, item: Consumable, target: Creature | PlayerCharacter
) -> bool:
    if not item.usable_in_combat or item.charges <= 0:
        return False

    effect_id = item.effect_id
    healed = False
    if effect_id.startswith("heal_"):
        try:
            heal_amount = int(effect_id.split("_", 1)[1])
        except (ValueError, IndexError):
            heal_amount = 0
        healed = heal_amount > 0
        _apply_heal(target, heal_amount)
    elif effect_id in {"restore_health", "heal"}:
        healed = True
        _apply_heal(target, 25)
    else:
        # Future: map to StatusEffect templates
        healed = False

    item.charges -= 1
    if item.charges <= 0 and item in pc.inventory:
        pc.inventory.remove(item)

    return healed


def _apply_heal(target: Creature | PlayerCharacter, amount: int) -> None:
    if isinstance(target, Creature):
        target.heal(amount)
    else:
        target.heal(amount)


def start_encounter(
    encounter_id: str,
    pc: PlayerCharacter,
    creatures: List[Creature],
    rng: Optional[random.Random] = None,
    difficulty: str = "standard",
    allies: Optional[List[Creature]] = None,
) -> EncounterState:
    rng = rng or random.Random()
    allies = allies or []
    participants = [CombatantRef("pc", pc.id)] + [CombatantRef("npc", a.id) for a in allies]
    participants += [CombatantRef("creature", c.id) for c in creatures]
    turn_order = roll_initiative(pc, creatures, rng, allies=allies)
    return EncounterState(
        id=encounter_id,
        participants=participants,
        turn_order=turn_order,
        difficulty=difficulty,
        meta={"allies": list(allies)},
    )


def _lookup_combatant(
    ref: CombatantRef,
    pc: PlayerCharacter,
    creatures: Sequence[Creature],
    npcs: Optional[Sequence[Creature]] = None,
) -> Creature | PlayerCharacter:
    if ref.kind == "pc" and pc.id == ref.id:
        return pc
    if ref.kind == "creature":
        for creature in creatures:
            if creature.id == ref.id:
                return creature
    if ref.kind == "npc" and npcs is not None:
        for npc in npcs:
            if npc.id == ref.id:
                return npc
    raise KeyError(f"Unknown combatant {ref.kind}:{ref.id}")


def _mark_consciousness(encounter: EncounterState, registry: Dict[str, Creature | PlayerCharacter]) -> None:
    for entry in encounter.turn_order:
        actor_key = f"{entry.ref.kind}:{entry.ref.id}"
        actor = registry.get(actor_key)
        if actor is None:
            continue
        entry.is_conscious = getattr(actor, "is_alive", True)


def _check_end_conditions(
    pc: PlayerCharacter,
    creatures: Sequence[Creature],
    encounter: EncounterState,
    allies: Optional[Sequence[Creature]] = None,
) -> Optional[Literal["victory", "defeat"]]:
    allies = allies or []
    if not pc.is_alive and not any(ally.is_alive for ally in allies):
        return "defeat"
    remaining_creatures = [creature for creature in creatures if creature.is_alive]
    if not remaining_creatures:
        encounter.meta["rewards_pending"] = True
        return "victory"
    return None


def _advance_turn(encounter: EncounterState) -> None:
    if not encounter.turn_order:
        return
    starting_index = encounter.active_index
    while True:
        encounter.active_index = (encounter.active_index + 1) % len(encounter.turn_order)
        if encounter.active_index == 0:
            encounter.round += 1
        active_entry = encounter.turn_order[encounter.active_index]
        if active_entry.is_conscious:
            break
        if encounter.active_index == starting_index:
            break


def process_turn_commands(
    encounter: EncounterState,
    pc: PlayerCharacter,
    creatures: List[Creature],
    commands: List[dict],
    rng: Optional[random.Random] = None,
    rewards_hook: Optional[Callable[[EncounterState, PlayerCharacter, List[Creature]], dict[str, object]]] = None,
    allies: Optional[List[Creature]] = None,
) -> EncounterResult:
    rng = rng or random.Random()
    if allies is None:
        allies_data = encounter.meta.get("allies", [])
        if isinstance(allies_data, list):
            allies = [Creature.from_dict(ally) if isinstance(ally, dict) else ally for ally in allies_data]
        else:
            allies = []
    else:
        allies = allies or []
    log: List[CombatLogEntry] = []
    registry: Dict[str, Creature | PlayerCharacter] = {"pc:" + pc.id: pc}
    for creature in creatures:
        registry[f"creature:{creature.id}"] = creature
    for ally in allies:
        registry[f"npc:{ally.id}"] = ally

    active_entry = encounter.turn_order[encounter.active_index]
    context = TurnContext(actor=active_entry.ref)

    def append_log(action: str, target: Optional[CombatantRef], message: str) -> None:
        log.append(
            CombatLogEntry(
                round=encounter.round,
                actor=context.actor,
                action=action,
                target=target,
                message=message,
            )
        )

    outcome: Literal["ongoing", "victory", "defeat", "fled"] = "ongoing"
    rewards: Optional[dict[str, object]] = None

    for command in commands:
        if context.remaining_ap <= 0 or outcome != "ongoing":
            break

        action_type = command.get("type")
        cost = int(command.get("ap_cost", 1))
        target_ref = command.get("target")

        if action_type == "attack" and isinstance(target_ref, CombatantRef):
            attack_action = command.get("action")
            if not isinstance(attack_action, CreatureAction):
                continue
            attacker = _lookup_combatant(context.actor, pc, creatures, allies)
            defender = _lookup_combatant(target_ref, pc, creatures, allies)
            result = resolve_attack(attacker, defender, attack_action, rng)
            context.remaining_ap = max(0, context.remaining_ap - cost)
            append_log(
                "attack",
                target_ref,
                f"{attacker.name} attacks {defender.name}: {'hit' if result.hit else 'miss'} for {result.damage} damage",
            )
            registry[f"{target_ref.kind}:{target_ref.id}"] = defender
            _mark_consciousness(encounter, registry)
            end_state = _check_end_conditions(pc, creatures, encounter, allies)
            if end_state:
                outcome = end_state
        elif action_type == "item" and isinstance(target_ref, CombatantRef):
            item = command.get("item")
            if isinstance(item, Consumable):
                user = _lookup_combatant(context.actor, pc, creatures, allies)
                target = _lookup_combatant(target_ref, pc, creatures, allies)
                healed = use_consumable_in_combat(pc, item, target)
                append_log(
                    "item",
                    target_ref,
                    f"{getattr(user, 'name', 'Unknown')} uses {item.name} on {getattr(target, 'name', 'target')} ({'healed' if healed else 'no effect'})",
                )
                context.remaining_ap = max(0, context.remaining_ap - cost)
        elif action_type == "defend":
            append_log("defend", None, "Actor takes a defensive stance")
            context.remaining_ap = max(0, context.remaining_ap - cost)
        elif action_type == "flee":
            append_log("flee", None, f"{context.actor.kind}:{context.actor.id} flees the encounter")
            context.remaining_ap = 0
            outcome = "fled"
            break

    if outcome == "victory" and callable(rewards_hook):
        rewards = rewards_hook(encounter, pc, creatures)
    _advance_turn(encounter)

    return EncounterResult(state=encounter, context=context, log=log, status=outcome, rewards=rewards)
