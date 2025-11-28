from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from prophecycm.combat.status_effects import DispelCondition, DurationType, StatusEffect
from prophecycm.core import Serializable
from prophecycm.core_ids import DEFAULT_ID_REGISTRY, ensure_typed_id
from prophecycm.items.item import Equipment, EquipmentSlot, Item
from prophecycm.rules.abilities import ABILITIES
from prophecycm.rules.skills import SKILL_TO_ABILITY


class FeatStackingRule(Enum):
    UNIQUE = "unique"
    STACKABLE = "stackable"


def _safe_slot_conversion(raw_slot: object) -> EquipmentSlot | None:
    try:
        return raw_slot if isinstance(raw_slot, EquipmentSlot) else EquipmentSlot(str(raw_slot))
    except ValueError:
        return None


@dataclass
class AbilityScore(Serializable):
    name: str = ""
    score: int = 10
    modifier: int = 0
    base_score: int | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AbilityScore":
        return cls(
            name=data.get("name", ""),
            score=int(data.get("score", 10)),
            modifier=int(data.get("modifier", 0)),
            base_score=(
                int(data["base_score"]) if data.get("base_score") is not None else None
            ),
        )


@dataclass
class Skill(Serializable):
    name: str
    key_ability: str
    proficiency: str = "untrained"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Skill":
        return cls(
            name=data.get("name", ""),
            key_ability=data.get("key_ability", ""),
            proficiency=data.get("proficiency", "untrained"),
        )


@dataclass
class Race(Serializable):
    id: str = ""
    name: str = ""
    subrace_id: str | None = None
    ability_bonuses: Dict[str, int] = field(default_factory=dict)
    bonuses: Dict[str, int] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
    proficiency_packs: Dict[str, List[str]] = field(default_factory=dict)
    feature_progression: Dict[int, Dict[str, object]] = field(default_factory=dict)
    spell_progression: Dict[int, Dict[str, int]] = field(default_factory=dict)
    choice_slots: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Race":
        race_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(data.get("id", "race.unknown"), expected_prefix="race", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes),
            expected_prefix="race",
        )
        return cls(
            id=race_id,
            name=data.get("name", ""),
            subrace_id=data.get("subrace_id"),
            ability_bonuses=data.get("ability_bonuses", {}),
            bonuses=data.get("bonuses", {}),
            traits=list(data.get("traits", [])),
            proficiency_packs=data.get("proficiency_packs", {}),
            feature_progression=data.get("feature_progression", {}),
            spell_progression=data.get("spell_progression", {}),
            choice_slots=data.get("choice_slots", {}),
        )


@dataclass
class Class(Serializable):
    id: str = ""
    name: str = ""
    archetype_id: str | None = None
    hit_die: int = 6
    save_proficiencies: List[str] = field(default_factory=list)
    ability_bonuses: Dict[str, int] = field(default_factory=dict)
    bonuses: Dict[str, int] = field(default_factory=dict)
    proficiency_packs: Dict[str, List[str]] = field(default_factory=dict)
    feature_progression: Dict[int, Dict[str, object]] = field(default_factory=dict)
    spell_progression: Dict[int, Dict[str, int]] = field(default_factory=dict)
    choice_slots: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Class":
        class_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(data.get("id", "class.unknown"), expected_prefix="class", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes),
            expected_prefix="class",
        )
        return cls(
            id=class_id,
            name=data.get("name", ""),
            archetype_id=data.get("archetype_id"),
            hit_die=int(data.get("hit_die", 6)),
            save_proficiencies=list(data.get("save_proficiencies", [])),
            ability_bonuses=data.get("ability_bonuses", {}),
            bonuses=data.get("bonuses", {}),
            proficiency_packs=data.get("proficiency_packs", {}),
            feature_progression=data.get("feature_progression", {}),
            spell_progression=data.get("spell_progression", {}),
            choice_slots=data.get("choice_slots", {}),
        )


@dataclass
class Feat(Serializable):
    id: str
    name: str
    description: str = ""
    modifiers: Dict[str, int] = field(default_factory=dict)
    required_level: int | None = None
    required_abilities: Dict[str, int] = field(default_factory=dict)
    required_classes: List[str] = field(default_factory=list)
    required_archetypes: List[str] = field(default_factory=list)
    stacking_rule: FeatStackingRule = field(default=FeatStackingRule.UNIQUE)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Feat":
        raw_rule = data.get("stacking_rule", FeatStackingRule.UNIQUE.value)
        stacking_rule = (
            raw_rule
            if isinstance(raw_rule, FeatStackingRule)
            else FeatStackingRule(str(raw_rule))
            if raw_rule is not None
            else FeatStackingRule.UNIQUE
        )
        feat_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(data.get("id", "feat.unknown"), expected_prefix="feat", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes),
            expected_prefix="feat",
        )
        return cls(
            id=feat_id,
            name=data.get("name", ""),
            description=data.get("description", ""),
            modifiers=data.get("modifiers", {}),
            required_level=(
                int(data["required_level"])
                if data.get("required_level") is not None
                else None
            ),
            required_abilities={k: int(v) for k, v in data.get("required_abilities", {}).items()},
            required_classes=list(data.get("required_classes", [])),
            required_archetypes=list(data.get("required_archetypes", [])),
            stacking_rule=stacking_rule,
        )


class FeatValidator:
    def __init__(self, character: "PlayerCharacter") -> None:
        self.character = character

    def validate(self, feat: "Feat", *, existing_feats: List["Feat"] | None = None) -> None:
        existing = existing_feats if existing_feats is not None else self.character.feats
        self._validate_prerequisites(feat)
        self._validate_stacking(feat, existing)

    def _validate_prerequisites(self, feat: "Feat") -> None:
        if feat.required_level is not None and self.character.level < feat.required_level:
            raise ValueError(f"{feat.name} requires level {feat.required_level}")

        for ability, minimum in feat.required_abilities.items():
            current = self.character.abilities.get(ability)
            if current is None or current.score < minimum:
                raise ValueError(
                    f"{feat.name} requires {ability} {minimum} (has {getattr(current, 'score', 0)})"
                )

        if feat.required_classes and self.character.character_class.id not in feat.required_classes:
            raise ValueError(f"{feat.name} requires one of classes: {', '.join(feat.required_classes)}")

        archetype = getattr(self.character.character_class, "archetype_id", None)
        if feat.required_archetypes and archetype not in feat.required_archetypes:
            raise ValueError(
                f"{feat.name} requires archetype in {', '.join(feat.required_archetypes)}"
            )

    def _validate_stacking(self, feat: "Feat", existing_feats: List["Feat"]) -> None:
        if feat.stacking_rule == FeatStackingRule.UNIQUE:
            if any(existing.id == feat.id for existing in existing_feats):
                raise ValueError(f"{feat.name} can only be taken once")


@dataclass
class PlayerCharacter(Serializable):
    id: str
    name: str
    background: str
    abilities: Dict[str, AbilityScore]
    skills: Dict[str, Skill]
    race: Race
    character_class: Class
    feats: List[Feat] = field(default_factory=list)
    inventory: List[Item] = field(default_factory=list)
    equipment: Dict[EquipmentSlot, Equipment] = field(default_factory=dict)
    status_effects: List[StatusEffect] = field(default_factory=list)
    level: int = 1
    xp: int = 0
    hit_points: int = 0
    current_hit_points: int | None = None
    is_alive: bool = True
    armor_class: int = 10
    saves: Dict[str, int] = field(default_factory=dict)
    save_proficiencies: set[str] = field(default_factory=set)
    initiative: int = 0
    proficiency_bonus: int = 2
    scores_include_static_bonuses: bool = False
    granted_features: List[str] = field(default_factory=list)
    spellcasting: Dict[str, int] = field(default_factory=dict)
    choice_slots: Dict[str, int] = field(default_factory=dict)
    available_proficiency_packs: Dict[str, List[str]] = field(default_factory=dict)
    skill_proficiencies: set[str] = field(default_factory=set)
    _cached_modifiers: Dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._validate_feats(self.feats)
        self.recompute_statistics()
        if self.current_hit_points is None:
            self.current_hit_points = self.hit_points
        self.current_hit_points = min(self.current_hit_points, self.hit_points)
        if self.current_hit_points <= 0:
            self.current_hit_points = 0
            self.is_alive = False

    def _validate_feats(self, feats: List["Feat"]) -> None:
        validator = FeatValidator(self)
        validated: List[Feat] = []
        for feat in feats:
            validator.validate(feat, existing_feats=validated)
            validated.append(feat)

    def add_feat(self, feat: "Feat", *, validate: bool = True) -> None:
        if validate:
            FeatValidator(self).validate(feat)
        self.feats.append(feat)
        self.recompute_statistics()

    def recompute_statistics(self) -> None:
        aggregated_modifiers = self._collect_modifiers()

        self.granted_features = list(self.race.traits)
        self.available_proficiency_packs = {
            **self.race.proficiency_packs,
            **self.character_class.proficiency_packs,
        }

        progression_modifiers = self._collect_progression_modifiers()
        for key, value in progression_modifiers.items():
            aggregated_modifiers[key] = aggregated_modifiers.get(key, 0) + value

        self._cached_modifiers = dict(aggregated_modifiers)

        self.choice_slots = self._collect_choice_slots()
        self.spellcasting = self._collect_spellcasting()

        self.skill_proficiencies = self._collect_skill_proficiencies()

        for ability_name, ability_score in self.abilities.items():
            bonus = aggregated_modifiers.get(ability_name, 0)
            base_score = ability_score.base_score
            if base_score is None:
                base_score = ability_score.score
                ability_score.base_score = base_score
            total_score = base_score + bonus
            ability_score.score = total_score
            ability_score.modifier = (total_score - 10) // 2

        self.proficiency_bonus = 2 + (self.level - 1) // 4

        con_mod = self.abilities.get("constitution", AbilityScore()).modifier
        dex_mod = self.abilities.get("dexterity", AbilityScore()).modifier
        base_hp = max(1, self.character_class.hit_die + con_mod)
        self.hit_points = self.level * base_hp + aggregated_modifiers.get("hit_points", 0)

        self.armor_class = 10 + dex_mod + aggregated_modifiers.get("armor_class", 0)

        self.save_proficiencies = self._collect_save_proficiencies()
        self.saves = {
            ability: self.get_save_modifier(ability, aggregated_modifiers) for ability in ABILITIES
        }
        legacy_saves = {
            legacy: ability_saves[ability]
            for ability, legacy in legacy_save_mapping.items()
            if ability in ability_saves
        }
        self.saves = {**ability_saves, **legacy_saves}

        self.initiative = dex_mod + self.proficiency_bonus + aggregated_modifiers.get("initiative", 0)

        if self.current_hit_points is not None:
            self.current_hit_points = min(self.current_hit_points, self.hit_points)
            if self.current_hit_points <= 0:
                self.is_alive = False

    def _collect_skill_proficiencies(self) -> set[str]:
        proficiencies: set[str] = set()

        for name, skill in self.skills.items():
            if str(skill.proficiency).lower() != "untrained":
                proficiencies.add(str(name).lower())

        for pack in (self.race.proficiency_packs, self.character_class.proficiency_packs):
            for entries in pack.values():
                for entry in entries:
                    if (skill_name := str(entry).lower()) in SKILL_TO_ABILITY:
                        proficiencies.add(skill_name)

        return proficiencies

    def _collect_modifiers(self) -> Dict[str, int]:
        modifiers: Dict[str, int] = {}

        def merge(source: Dict[str, int]) -> None:
            for key, value in source.items():
                modifiers[key] = modifiers.get(key, 0) + int(value)

        for bonus_source in (self.race.bonuses, self.character_class.bonuses):
            merge(bonus_source)

        for feat in self.feats:
            merge(feat.modifiers)

        for item in self.equipment.values():
            merge(getattr(item, "modifiers", {}))

        for effect in self.status_effects:
            merge(effect.total_modifiers())

        return modifiers

    def _collect_progression_modifiers(self) -> Dict[str, int]:
        modifiers: Dict[str, int] = {}

        def merge(source: Dict[str, int]) -> None:
            for key, value in source.items():
                modifiers[key] = modifiers.get(key, 0) + int(value)

        for entry in self._progression_entries(self.race.feature_progression):
            merge(entry.get("modifiers", {}))
            self._append_features(entry)
        for entry in self._progression_entries(self.character_class.feature_progression):
            merge(entry.get("modifiers", {}))
            self._append_features(entry)

        return modifiers

    def _collect_choice_slots(self) -> Dict[str, int]:
        slots: Dict[str, int] = {}

        def merge(source: Dict[str, int]) -> None:
            for key, value in source.items():
                slots[key] = slots.get(key, 0) + int(value)

        merge(self.race.choice_slots)
        merge(self.character_class.choice_slots)

        for entry in self._progression_entries(self.race.feature_progression):
            merge(entry.get("choice_slots", {}))
        for entry in self._progression_entries(self.character_class.feature_progression):
            merge(entry.get("choice_slots", {}))

        return slots

    def _collect_spellcasting(self) -> Dict[str, int]:
        spellcasting: Dict[str, int] = {}

        def merge(source: Dict[str, int]) -> None:
            for circle, value in source.items():
                spellcasting[str(circle)] = spellcasting.get(str(circle), 0) + int(value)

        for entry in self._progression_entries(self.race.feature_progression):
            merge(entry.get("spell_slots", {}))
        for entry in self._progression_entries(self.character_class.feature_progression):
            merge(entry.get("spell_slots", {}))

        for level, slots in self.race.spell_progression.items():
            try:
                level_int = int(level)
            except (TypeError, ValueError):
                continue
            if level_int <= self.level:
                merge(slots)
        for level, slots in self.character_class.spell_progression.items():
            try:
                level_int = int(level)
            except (TypeError, ValueError):
                continue
            if level_int <= self.level:
                merge(slots)

        return spellcasting

    def _progression_entries(self, progression: Dict[int, Dict[str, object]]) -> List[Dict[str, object]]:
        entries: List[Dict[str, object]] = []
        for level, payload in progression.items():
            try:
                level_int = int(level)
            except (TypeError, ValueError):
                continue
            if level_int <= self.level and isinstance(payload, dict):
                entries.append(payload)
        return entries

    def _append_features(self, entry: Dict[str, object]) -> None:
        features = entry.get("features", [])
        if isinstance(features, list):
            self.granted_features.extend(str(feature) for feature in features)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PlayerCharacter":
        abilities_data = data.get("abilities", {})
        abilities: Dict[str, AbilityScore] = {}
        for name, value in abilities_data.items():
            if isinstance(value, dict):
                abilities[name] = AbilityScore.from_dict({"name": name, **value})
            else:
                abilities[name] = AbilityScore(name=name, score=int(value))

        skills_data = data.get("skills", {})
        skills: Dict[str, Skill] = {}
        for name, value in skills_data.items():
            if isinstance(value, dict):
                skills[name] = Skill.from_dict({"name": name, **value})
            else:
                skills[name] = Skill(name=name, key_ability="", proficiency=str(value))

        feats = [Feat.from_dict(feat) for feat in data.get("feats", [])]
        equipment_data = data.get("equipment", {})

        pc_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(data["id"], expected_prefix="pc", allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes),
            expected_prefix="pc",
        )

        instance = cls(
            id=pc_id,
            name=data.get("name", ""),
            background=data.get("background", ""),
            abilities=abilities,
            skills=skills,
            race=Race.from_dict(data.get("race", {})),
            character_class=Class.from_dict(data.get("character_class", {})),
            feats=feats,
            inventory=[Item.from_dict(item) for item in data.get("inventory", [])],
            equipment={
                slot_value: Equipment.from_dict(equipment)
                for slot, equipment in equipment_data.items()
                if (slot_value := _safe_slot_conversion(slot)) is not None
            },
            status_effects=[StatusEffect.from_dict(effect) for effect in data.get("status_effects", [])],
            level=int(data.get("level", 1)),
            xp=int(data.get("xp", 0)),
            hit_points=int(data.get("hit_points", 0)),
            current_hit_points=data.get("current_hit_points"),
            is_alive=bool(data.get("is_alive", True)),
            armor_class=int(data.get("armor_class", 10)),
            saves=data.get("saves", {}),
            save_proficiencies=set(data.get("save_proficiencies", [])),
            initiative=int(data.get("initiative", 0)),
            proficiency_bonus=int(data.get("proficiency_bonus", 2)),
            scores_include_static_bonuses=bool(
                data.get("scores_include_static_bonuses", False)
            ),
        )
        return instance

    def to_dict(self) -> Dict[str, object]:
        payload = super().to_dict()
        payload["save_proficiencies"] = sorted(self.save_proficiencies)
        payload["equipment"] = {slot.value: item.to_dict() for slot, item in self.equipment.items()}
        return payload

    def add_status_effect(self, effect: StatusEffect) -> None:
        for existing in self.status_effects:
            if existing.id == effect.id:
                existing.combine(effect)
                break
        else:
            self.status_effects.append(effect)
        self.recompute_statistics()

    def apply_damage(self, amount: int) -> None:
        if not self.is_alive:
            return
        self.current_hit_points = max(0, (self.current_hit_points or 0) - max(0, amount))
        if self.current_hit_points == 0:
            self.is_alive = False

    def heal(self, amount: int) -> None:
        if not self.is_alive:
            return
        self.current_hit_points = min(self.hit_points, (self.current_hit_points or 0) + max(0, amount))

    def gain_xp(self, amount: int) -> List[int]:
        self.xp += max(0, amount)
        leveled_up: List[int] = []
        while True:
            next_level = self.level + 1
            threshold = XP_THRESHOLDS.get(next_level)
            if threshold is None or self.xp < threshold:
                break
            self.level = next_level
            self.recompute_statistics()
            if self.current_hit_points is None:
                self.current_hit_points = self.hit_points
            leveled_up.append(self.level)
        return leveled_up

    def tick_status_effects(self, tick_type: DurationType = DurationType.TURNS) -> None:
        self.status_effects = [effect for effect in self.status_effects if effect.tick(tick_type)]
        self.recompute_statistics()

    def dispel_status_effects(self, dispel_type: DispelCondition = DispelCondition.ANY) -> None:
        self.status_effects = [effect for effect in self.status_effects if not effect.can_be_dispelled(dispel_type)]
        self.recompute_statistics()

    def equip_item(self, item: Equipment) -> None:
        if not isinstance(item, Equipment):
            raise TypeError("Only equipment can be equipped")

        self._validate_equipment_requirements(item)

        if item.slot == EquipmentSlot.TWO_HAND:
            if EquipmentSlot.MAIN_HAND in self.equipment or EquipmentSlot.OFF_HAND in self.equipment:
                raise ValueError("Cannot equip a two-handed item while hands are occupied")
            self.equipment[EquipmentSlot.TWO_HAND] = item
        elif item.slot == EquipmentSlot.MAIN_HAND:
            if EquipmentSlot.TWO_HAND in self.equipment:
                raise ValueError("Cannot equip main-hand item while using two-handed weapon")
            self.equipment[EquipmentSlot.MAIN_HAND] = item
        elif item.slot == EquipmentSlot.OFF_HAND:
            if EquipmentSlot.TWO_HAND in self.equipment:
                raise ValueError("Cannot equip off-hand item while using two-handed weapon")
            if item.two_handed:
                raise ValueError("Off-hand items cannot be two-handed")
            self.equipment[EquipmentSlot.OFF_HAND] = item
        else:
            self.equipment[item.slot] = item

        if item not in self.inventory:
            self.inventory.append(item)

        self.recompute_statistics()

    def _validate_equipment_requirements(self, item: Equipment) -> None:
        requirements = getattr(item, "requirements", {}) or {}
        if not requirements:
            return

        required_level = requirements.get("level")
        if required_level is not None and self.level < int(required_level):
            raise ValueError(f"{item.name} requires level {required_level}")

        ability_requirements: Dict[str, int] = {}
        ability_requirements.update({k: int(v) for k, v in requirements.get("abilities", {}).items()})

        for key, value in requirements.items():
            if key in {"level", "classes", "class_tags", "abilities"}:
                continue
            if key in self.abilities and key not in ability_requirements:
                ability_requirements[key] = int(value)

        for ability, minimum in ability_requirements.items():
            current = self.abilities.get(ability)
            if current is None or current.score < minimum:
                raise ValueError(
                    f"{item.name} requires {ability} {minimum} (has {getattr(current, 'score', 0)})"
                )

        required_classes = requirements.get("classes")
        if required_classes:
            allowed_classes = {str(entry) for entry in required_classes}
            if self.character_class.id not in allowed_classes and self.character_class.name not in allowed_classes:
                raise ValueError(
                    f"{item.name} requires class in {', '.join(sorted(allowed_classes))}"
                )

        required_tags = requirements.get("class_tags")
        if required_tags:
            class_tags = set(getattr(self.character_class, "tags", []) or [])
            if not class_tags.intersection(set(map(str, required_tags))):
                raise ValueError(f"{item.name} requires class tag in {', '.join(map(str, required_tags))}")

    def unequip(self, slot: EquipmentSlot) -> Equipment | None:
        removed = self.equipment.pop(slot, None)
        self.recompute_statistics()
        return removed

    def _normalize_ability(self, ability: str) -> str:
        ability_name = str(ability).lower()
        if ability_name not in ABILITIES:
            raise KeyError(f"Unknown ability '{ability}'")
        return ability_name

    def _normalize_skill(self, skill: str) -> str:
        skill_name = str(skill).lower()
        if skill_name not in SKILL_TO_ABILITY:
            raise KeyError(f"Unknown skill '{skill}'")
        return skill_name

    def get_ability_score(self, ability: str) -> int:
        ability_name = self._normalize_ability(ability)
        return self.abilities[ability_name].score

    def get_ability_modifier(self, ability: str) -> int:
        ability_name = self._normalize_ability(ability)
        return self.abilities[ability_name].modifier

    def get_proficiency_bonus(self) -> int:
        return 2 + (self.level - 1) // 4

    def is_skill_proficient(self, skill: str) -> bool:
        skill_name = self._normalize_skill(skill)
        return skill_name in self.skill_proficiencies

    def get_skill_modifier(self, skill: str) -> int:
        skill_name = self._normalize_skill(skill)
        ability = SKILL_TO_ABILITY[skill_name]
        modifier = self.get_ability_modifier(ability)
        modifier += self._cached_modifiers.get(skill_name, 0)
        if self.is_skill_proficient(skill_name):
            modifier += self.proficiency_bonus
        return modifier
XP_THRESHOLDS: Dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
}
