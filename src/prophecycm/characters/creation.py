from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Mapping

from prophecycm.characters.player import AbilityScore, Class, Feat, PlayerCharacter, Race, Skill
from prophecycm.core import Serializable
from prophecycm.core_ids import DEFAULT_ID_REGISTRY, ensure_typed_id
from prophecycm.items import Equipment, Item
from prophecycm.rules import SKILL_IDS, SKILL_TO_ABILITY

LOGGER = logging.getLogger(__name__)


class AbilityGenerationMethod(str, Enum):
    POINT_BUY = "point_buy"
    STANDARD_ARRAY = "standard_array"


_DEFAULT_POINT_BUY_COSTS: Dict[int, int] = {
    8: 0,
    9: 1,
    10: 2,
    11: 3,
    12: 4,
    13: 5,
    14: 7,
    15: 9,
}


@dataclass
class GearBundle(Serializable):
    id: str
    label: str
    description: str = ""
    item_ids: List[str] = field(default_factory=list)

    def resolve_items(self, catalog_items: Mapping[str, Item]) -> List[Item]:
        resolved: List[Item] = []
        for item_id in self.item_ids:
            if item_id not in catalog_items:
                raise ValueError(f"Unknown item id '{item_id}' in gear bundle '{self.id}'")
            resolved.append(catalog_items[item_id])
        return resolved

@dataclass
class Background(Serializable):
    id: str
    name: str
    starting_skills: List[str] = field(default_factory=list)
    starting_item_ids: List[str] = field(default_factory=list)

    def resolve_items(self, catalog_items: Mapping[str, Item]) -> List[Item]:
        resolved: List[Item] = []
        for item_id in self.starting_item_ids:
            if item_id not in catalog_items:
                raise ValueError(f"Unknown item id '{item_id}' for background '{self.id}'")
            resolved.append(catalog_items[item_id])
        return resolved

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Background":
        if isinstance(data, str):
            return cls(id=data, name=data)
        starting_skills = data.get("starting_skills") or data.get("background_starting_skills", [])
        starting_items = data.get("starting_item_ids") or data.get("background_starting_items", [])
        return cls(
            id=data.get("id", data.get("name", "")),
            name=data.get("name", data.get("id", "")),
            starting_skills=list(starting_skills),
            starting_item_ids=list(starting_items),
        )


@dataclass
class CharacterCreationConfig(Serializable):
    races: List[Race] = field(default_factory=list)
    classes: List[Class] = field(default_factory=list)
    backgrounds: List[Background] = field(default_factory=list)
    feats: List[Feat] = field(default_factory=list)
    gear_bundles: List[GearBundle] = field(default_factory=list)
    ability_names: List[str] | None = field(default_factory=list)
    standard_array: List[int] | None = field(default_factory=list)
    point_buy_total: int = 27
    point_buy_costs: Dict[int, int] = field(default_factory=lambda: dict(_DEFAULT_POINT_BUY_COSTS))
    active_skills: List[str] = field(default_factory=list)
    skill_catalog: Dict[str, str] = field(default_factory=lambda: dict(SKILL_TO_ABILITY))
    skill_choices: int = 0
    feat_choices: int = 0
    bonus_feat_levels: List[int] = field(default_factory=list)
    bonus_ability_increase_levels: List[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "CharacterCreationConfig":
        raw_skill_catalog = data.get("skills", data.get("skill_catalog", {}))
        active_skills = data.get("active_skills") or list(raw_skill_catalog) or []
        return cls(
            races=[Race.from_dict(entry) for entry in data.get("races", [])],
            classes=[Class.from_dict(entry) for entry in data.get("classes", [])],
            backgrounds=[Background.from_dict(entry) for entry in data.get("backgrounds", [])],
            feats=[Feat.from_dict(entry) for entry in data.get("feats", [])],
            gear_bundles=[GearBundle.from_dict(entry) for entry in data.get("gear_bundles", [])],
            ability_names=list(data.get("ability_names", [])) or None,
            standard_array=list(data.get("standard_array", [])) or None,
            point_buy_total=int(data.get("point_buy_total", 27)),
            point_buy_costs={int(k): int(v) for k, v in data.get("point_buy_costs", _DEFAULT_POINT_BUY_COSTS).items()},
            active_skills=list(active_skills),
            skill_catalog={str(k): str(v) for k, v in raw_skill_catalog.items()},
            skill_choices=int(data.get("skill_choices", 0)),
            feat_choices=int(data.get("feat_choices", 0)),
            bonus_feat_levels=[int(level) for level in data.get("bonus_feat_levels", [])],
            bonus_ability_increase_levels=[
                int(level) for level in data.get("bonus_ability_increase_levels", [])
            ],
        )

    def __post_init__(self) -> None:
        if not self.ability_names:
            self.ability_names = [
                "strength",
                "dexterity",
                "constitution",
                "intelligence",
                "wisdom",
                "charisma",
            ]
        if not self.standard_array:
            self.standard_array = [15, 14, 13, 12, 10, 8]

        if not self.active_skills:
            self.active_skills = list(self.skill_catalog) or list(SKILL_TO_ABILITY)

        unknown_skills = sorted(set(self.active_skills) - set(SKILL_TO_ABILITY))
        if unknown_skills:
            raise ValueError(
                "Unknown skills provided in campaign configuration: "
                + ", ".join(unknown_skills)
            )

        omitted_registry_skills = [skill for skill in SKILL_IDS if skill not in self.active_skills]
        if omitted_registry_skills:
            LOGGER.info(
                "Canonical skills omitted by campaign whitelist: %s",
                ", ".join(omitted_registry_skills),
            )

        self.skill_catalog = {skill: SKILL_TO_ABILITY[skill] for skill in self.active_skills}

        for character_class in self.classes:
            if not character_class.class_skill_list:
                character_class.class_skill_list = list(self.skill_catalog)
            unknown_class_skills = [
                skill for skill in character_class.class_skill_list if skill not in self.skill_catalog
            ]
            if unknown_class_skills:
                raise ValueError(
                    f"Class '{character_class.id}' has unknown skills: {', '.join(sorted(unknown_class_skills))}"
                )


@dataclass
class CharacterCreationSelection(Serializable):
    name: str
    background_id: str
    race_id: str
    class_id: str
    ability_method: AbilityGenerationMethod
    ability_scores: Dict[str, int]
    trained_skills: List[str] = field(default_factory=list)
    feat_ids: List[str] = field(default_factory=list)
    gear_bundle_id: str | None = None
    level: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "CharacterCreationSelection":
        return cls(
            name=data.get("name", ""),
            background_id=data.get("background_id") or data.get("background", ""),
            race_id=data.get("race_id", ""),
            class_id=data.get("class_id", ""),
            ability_method=AbilityGenerationMethod(data.get("ability_method")),
            ability_scores=dict(data.get("ability_scores", {})),
            trained_skills=list(data.get("trained_skills", [])),
            feat_ids=list(data.get("feat_ids", [])),
            gear_bundle_id=data.get("gear_bundle_id"),
            level=int(data.get("level", 1)),
        )


@dataclass
class CharacterCreationResult(Serializable):
    character: PlayerCharacter
    pending_level_ups: List["LevelUpRequest"] = field(default_factory=list)


class CharacterCreator:
    def __init__(self, config: CharacterCreationConfig, catalog_items: Mapping[str, Item]):
        self.config = config
        self.catalog_items = catalog_items
        self._races = {race.id: race for race in config.races}
        self._classes = {char_class.id: char_class for char_class in config.classes}
        self._feats = {feat.id: feat for feat in config.feats}
        self._gear_bundles = {bundle.id: bundle for bundle in config.gear_bundles}
        self._backgrounds = {background.id: background for background in config.backgrounds}

    def build_character(self, selection: CharacterCreationSelection) -> CharacterCreationResult:
        race = self._resolve_race(selection.race_id)
        character_class = self._resolve_class(selection.class_id)

        background = self._resolve_background(selection.background_id)

        feats = self._select_feats(selection)
        skills = self._select_skills(selection, background, race, character_class)
        base_abilities = self._assign_abilities(selection)
        abilities = self._apply_ability_bonuses(base_abilities, race, character_class)
        inventory = list(self._select_background_items(background))
        inventory.extend(self._select_gear(selection))

        pc_id = DEFAULT_ID_REGISTRY.register(
            ensure_typed_id(
                selection.name,
                expected_prefix="pc",
                allowed_prefixes=DEFAULT_ID_REGISTRY.allowed_prefixes,
            ),
            expected_prefix="pc",
        )

        pc = PlayerCharacter(
            id=pc_id,
            name=selection.name,
            background=background.name,
            abilities=abilities,
            skills=skills,
            race=race,
            character_class=character_class,
            feats=feats,
            inventory=list(inventory),
            level=selection.level,
            scores_include_static_bonuses=True,
        )

        for item in inventory:
            if isinstance(item, Equipment):
                try:
                    pc.equip_item(item)
                except ValueError:
                    # If a bundle tries to equip conflicting gear, prefer inventory placement.
                    continue
        pending_level_ups = self._pending_class_feature_choices(pc, character_class)
        return CharacterCreationResult(character=pc, pending_level_ups=pending_level_ups)

    def _assign_abilities(self, selection: CharacterCreationSelection) -> Dict[str, int]:
        scores = {name: int(score) for name, score in selection.ability_scores.items()}
        expected = set(self.config.ability_names)
        missing = expected - set(scores)
        if missing:
            raise ValueError(f"Missing ability assignments for: {', '.join(sorted(missing))}")
        extra = set(scores) - expected
        if extra:
            raise ValueError(f"Unknown ability assignments provided: {', '.join(sorted(extra))}")

        if selection.ability_method == AbilityGenerationMethod.STANDARD_ARRAY:
            self._validate_standard_array(scores)
        elif selection.ability_method == AbilityGenerationMethod.POINT_BUY:
            self._validate_point_buy(scores)
        else:
            raise ValueError(f"Unknown ability generation method: {selection.ability_method}")

        return scores

    def _apply_ability_bonuses(
        self, scores: Dict[str, int], race: Race, character_class: Class
    ) -> Dict[str, AbilityScore]:
        merged = dict(scores)
        for bonus_source in (race.ability_bonuses, character_class.ability_bonuses):
            for ability, bonus in bonus_source.items():
                if ability in merged:
                    merged[ability] = merged.get(ability, 0) + int(bonus)
        return {name: AbilityScore(name=name, score=score) for name, score in merged.items()}

    def _validate_standard_array(self, scores: Mapping[str, int]) -> None:
        provided = sorted(scores.values())
        if provided != sorted(self.config.standard_array):
            raise ValueError("Ability scores must match the standard array exactly")

    def _validate_point_buy(self, scores: Mapping[str, int]) -> None:
        total = 0
        for ability, score in scores.items():
            if score not in self.config.point_buy_costs:
                raise ValueError(f"Score {score} for {ability} not allowed by point buy rules")
            total += self.config.point_buy_costs[score]
        if total > self.config.point_buy_total:
            raise ValueError(
                f"Point buy total {total} exceeds budget of {self.config.point_buy_total}"
            )

    def _select_skills(
        self,
        selection: CharacterCreationSelection,
        background: Background,
        race: Race,
        character_class: Class,
    ) -> Dict[str, Skill]:
        chosen = list(selection.trained_skills)
        expected_choices = character_class.skill_choice_count or self.config.skill_choices
        if expected_choices is not None and len(chosen) != expected_choices:
            raise ValueError(
                f"Expected {expected_choices} trained skills, got {len(chosen)}"
            )

        class_skill_list = set(character_class.class_skill_list or self.config.active_skills)
        unknown_selection = [skill for skill in chosen if skill not in self.config.skill_catalog]
        if unknown_selection:
            raise ValueError(f"Unknown skills selected: {', '.join(sorted(unknown_selection))}")

        disallowed = [skill for skill in chosen if skill not in class_skill_list]
        if disallowed:
            raise ValueError(
                f"Selected skills not allowed for class '{character_class.id}': {', '.join(sorted(disallowed))}"
            )

        invalid_class_skills = [
            skill for skill in character_class.class_skill_list if skill not in SKILL_TO_ABILITY
        ]
        if invalid_class_skills:
            raise ValueError(
                f"Class '{character_class.id}' references unknown skills: {', '.join(sorted(invalid_class_skills))}"
            )

        background_skills = list(background.starting_skills)
        unknown_background = [skill for skill in background_skills if skill not in self.config.skill_catalog]
        if unknown_background:
            raise ValueError(
                f"Background '{background.id}' has unknown skills: {', '.join(sorted(unknown_background))}"
            )

        race_skills = [skill for skill in getattr(race, "skill_proficiencies", [])]
        unknown_race_skills = [skill for skill in race_skills if skill not in self.config.skill_catalog]
        if unknown_race_skills:
            raise ValueError(
                f"Race '{race.id}' has unknown skills: {', '.join(sorted(unknown_race_skills))}"
            )

        auto_trained = set(chosen) | set(background_skills) | set(race_skills)

        skills: Dict[str, Skill] = {}
        for name, key_ability in self.config.skill_catalog.items():
            proficiency = "trained" if name in auto_trained else "untrained"
            skills[name] = Skill(name=name, key_ability=key_ability, proficiency=proficiency)
        return skills

    def _select_feats(self, selection: CharacterCreationSelection) -> List[Feat]:
        expected = self._expected_feat_count(selection.level)
        if len(selection.feat_ids) != expected:
            raise ValueError(
                f"Expected {expected} feats for level {selection.level}, got {len(selection.feat_ids)}"
            )

        feats: List[Feat] = []
        for feat_id in selection.feat_ids:
            feat = self._feats.get(feat_id)
            if not feat:
                raise ValueError(f"Unknown feat id '{feat_id}'")
            feats.append(feat)
        return feats

    def _expected_feat_count(self, level: int) -> int:
        baseline = self.config.feat_choices
        bonus = len([entry for entry in self.config.bonus_feat_levels if entry <= level])
        return baseline + bonus

    def _pending_class_feature_choices(
        self, character: PlayerCharacter, character_class: Class
    ) -> List["LevelUpRequest"]:
        from prophecycm.state.leveling import LevelUpRequest

        pending: List[LevelUpRequest] = []
        if character.level <= 1:
            return pending

        for tier in range(2, character.level + 1):
            features = character_class.feature_progression.get(tier, {})
            choice_slots = features.get("choice_slots") if isinstance(features, dict) else None
            if choice_slots:
                pending.append(
                    LevelUpRequest(
                        character_id=character.id,
                        character_type="pc",
                        target_level=tier,
                    )
                )
        return pending

    def _select_gear(self, selection: CharacterCreationSelection) -> Iterable[Item]:
        if not selection.gear_bundle_id:
            return []
        bundle = self._gear_bundles.get(selection.gear_bundle_id)
        if bundle is None:
            raise ValueError(f"Unknown gear bundle '{selection.gear_bundle_id}'")
        return bundle.resolve_items(self.catalog_items)

    def _select_background_items(self, background: Background) -> Iterable[Item]:
        return background.resolve_items(self.catalog_items)

    def _resolve_race(self, race_id: str) -> Race:
        try:
            return self._races[race_id]
        except KeyError as exc:
            raise ValueError(f"Unknown race id '{race_id}'") from exc

    def _resolve_class(self, class_id: str) -> Class:
        try:
            return self._classes[class_id]
        except KeyError as exc:
            raise ValueError(f"Unknown class id '{class_id}'") from exc

    def _resolve_background(self, background_id: str) -> Background:
        try:
            return self._backgrounds[background_id]
        except KeyError as exc:
            raise ValueError(f"Background '{background_id}' is not available") from exc
