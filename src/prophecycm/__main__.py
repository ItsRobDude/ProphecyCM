"""Interactive bootstrapper for the ProphecyCM demo content."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from prophecycm.characters.creation import (
    AbilityGenerationMethod,
    CharacterCreationSelection,
    GearBundle,
)
from prophecycm.content import ContentCatalog, load_start_menu_config
from prophecycm.ui.start_menu_config import (
    ContentWarning,
    StartMenuConfig,
    StartMenuNewGameFlow,
    StartMenuOption,
)


CONTENT_ROOT = Path(__file__).resolve().parents[2] / "docs" / "data-model" / "fixtures"


def _print_header(start_menu: StartMenuConfig) -> None:
    print("=" * 60)
    print(start_menu.title)
    if start_menu.subtitle:
        print(start_menu.subtitle)
    print("=" * 60)


def _render_menu(start_menu: StartMenuConfig) -> StartMenuOption | StartMenuNewGameFlow:
    new_game_flow = start_menu.build_new_game_flow()

    while True:
        _print_header(start_menu)
        print("Select an option:")

        choices: list[StartMenuOption | StartMenuNewGameFlow] = [
            *start_menu.options,
            new_game_flow,
        ]

        for idx, option in enumerate(choices, start=1):
            description = getattr(option, "description", "")
            print(f"  {idx}. {option.label}")
            if description:
                print(f"     {description}")

        raw_choice = input("Enter a number: ").strip()
        if not raw_choice.isdigit():
            print("Please enter a valid number.\n")
            continue

        choice = int(raw_choice)
        if 1 <= choice <= len(choices):
            return choices[choice - 1]

        print("Selection out of range. Try again.\n")


def _render_content_warning(warning: ContentWarning) -> bool:
    print(f"\n{warning.title}")
    print("-" * len(warning.title))
    print(warning.message)
    for bullet in warning.bullet_points:
        print(f"  • {bullet}")

    prompt = f"{warning.accept_label} (y) / {warning.decline_label} (n): "
    response = input(prompt).strip().lower()
    return response.startswith("y")


def _handle_save_selection(option: StartMenuOption) -> None:
    save = option.save_file
    print("\nLoading existing adventure...")
    print(f"Slot {save.slot}: {option.label}")
    if option.description:
        print(option.description)
    if option.metadata:
        print(f"Metadata: {option.metadata}")
    print("Launching save file...")


def _handle_new_game_flow(flow: StartMenuNewGameFlow) -> CharacterCreationSelection | None:
    print(f"\n{flow.label}")
    if flow.description:
        print(flow.description)

    if flow.content_warning:
        accepted = _render_content_warning(flow.content_warning)
        if not accepted:
            print("Returning to start menu...\n")
            return None

    selection = _run_character_creation(flow)
    return selection


def _prompt_choice(prompt: str, options: Sequence[object], *, display_attr: str = "label") -> object:
    while True:
        print(prompt)
        for idx, option in enumerate(options, start=1):
            label = getattr(option, display_attr, str(option))
            print(f"  {idx}. {label}")

        raw_choice = input("Enter a number: ").strip()
        if raw_choice.isdigit():
            idx = int(raw_choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("Invalid choice. Please try again.\n")


def _prompt_multi_choice(
    prompt: str, options: Sequence[object], *, max_choices: int, display_attr: str = "label"
) -> List[object]:
    if max_choices <= 0 or not options:
        return []
    print(prompt)
    for idx, option in enumerate(options, start=1):
        label = getattr(option, display_attr, str(option))
        print(f"  {idx}. {label}")
    print(f"Select up to {max_choices} (comma-separated), or press Enter for none.")

    while True:
        raw = input("Your choices: ").strip()
        if not raw:
            return []
        try:
            indices = {int(part.strip()) for part in raw.split(",") if part.strip()}
        except ValueError:
            print("Please enter numbers separated by commas.\n")
            continue

        if not indices:
            return []
        if any(idx < 1 or idx > len(options) for idx in indices):
            print("One or more selections were out of range. Try again.\n")
            continue
        if len(indices) > max_choices:
            print(f"Please pick no more than {max_choices} options.\n")
            continue
        return [options[idx - 1] for idx in sorted(indices)]


def _prompt_text(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("A value is required. Please try again.\n")


def _select_background(backgrounds: Sequence[str]) -> str:
    options = [type("_BG", (), {"label": bg})() for bg in backgrounds]
    choice = _prompt_choice("Choose a background:", options)
    return getattr(choice, "label")


def _select_race_and_class(flow: StartMenuNewGameFlow) -> tuple[str, str]:
    race = _prompt_choice("Choose a race:", flow.require_character_creation().races, display_attr="name")
    char_class = _prompt_choice(
        "Choose a class:", flow.require_character_creation().classes, display_attr="name"
    )
    return race.id, char_class.id


def _prompt_ability_method(config: StartMenuNewGameFlow) -> AbilityGenerationMethod:
    methods: list[AbilityGenerationMethod] = []
    creation = config.require_character_creation()
    if creation.standard_array:
        methods.append(AbilityGenerationMethod.STANDARD_ARRAY)
    if creation.point_buy_costs:
        methods.append(AbilityGenerationMethod.POINT_BUY)

    labels = [f"{idx + 1}. {method.value.replace('_', ' ').title()}" for idx, method in enumerate(methods)]
    print("Select an ability generation method:")
    for label in labels:
        print(f"  {label}")

    while True:
        raw = input("Enter a number: ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(methods):
                return methods[idx - 1]
        print("Invalid choice. Please try again.\n")


def _assign_standard_array(abilities: Sequence[str], array: Sequence[int]) -> dict[str, int]:
    remaining = list(array)
    assignments: dict[str, int] = {}
    for ability in abilities:
        prompt = f"Assign a score to {ability.title()} (remaining: {remaining}):"
        while True:
            raw = input(prompt + " ").strip()
            if not raw.isdigit():
                print("Enter a number from the remaining array values.\n")
                continue
            score = int(raw)
            if score not in remaining:
                print("That value has already been used or is not available.\n")
                continue
            assignments[ability] = score
            remaining.remove(score)
            break
    return assignments


def _assign_point_buy(abilities: Sequence[str], *, costs: dict[int, int], budget: int) -> dict[str, int]:
    allowed_scores = sorted(costs)
    remaining_budget = budget
    assignments: dict[str, int] = {}

    print("Point buy costs:")
    for score in allowed_scores:
        print(f"  {score}: {costs[score]} points")
    print(f"Total budget: {budget}\n")

    for ability in abilities:
        while True:
            raw = input(f"Choose a score for {ability.title()} (budget remaining {remaining_budget}): ").strip()
            if not raw.isdigit():
                print("Enter a numeric score from the allowed list.\n")
                continue
            score = int(raw)
            if score not in costs:
                print("That score is not permitted by the rules.\n")
                continue
            cost = costs[score]
            if cost > remaining_budget:
                print("Not enough budget for that score. Choose a lower value.\n")
                continue
            assignments[ability] = score
            remaining_budget -= cost
            break
    return assignments


def _select_skills_and_feats(flow: StartMenuNewGameFlow) -> tuple[list[str], list[str]]:
    creation = flow.require_character_creation()
    skill_names = list(creation.skill_catalog)
    trained_skills = [skill.label for skill in _prompt_multi_choice(
        "Choose trained skills:",
        [type("_Skill", (), {"label": name})() for name in skill_names],
        max_choices=creation.skill_choices,
    )]

    feat_options = creation.feats
    chosen_feats = _prompt_multi_choice(
        "Choose feats:", feat_options, max_choices=creation.feat_choices, display_attr="name"
    )
    return trained_skills, [feat.id for feat in chosen_feats]


def _select_gear_bundle(bundles: Iterable[GearBundle]) -> str | None:
    bundle_list = list(bundles)
    if not bundle_list:
        return None
    choice = _prompt_choice("Select a starting gear bundle:", bundle_list)
    return choice.id if isinstance(choice, GearBundle) else getattr(choice, "id", None)


def _run_character_creation(flow: StartMenuNewGameFlow) -> CharacterCreationSelection | None:
    creation = flow.require_character_creation()
    print("\n=== Character Creation ===")

    name = _prompt_text("Enter your character's name: ")
    background = _select_background(creation.backgrounds)
    race_id, class_id = _select_race_and_class(flow)

    ability_method = _prompt_ability_method(flow)
    if ability_method == AbilityGenerationMethod.STANDARD_ARRAY:
        ability_scores = _assign_standard_array(creation.ability_names or [], creation.standard_array or [])
    else:
        ability_scores = _assign_point_buy(
            creation.ability_names or [],
            costs=creation.point_buy_costs,
            budget=creation.point_buy_total,
        )

    trained_skills, feat_ids = _select_skills_and_feats(flow)
    gear_bundle_id = _select_gear_bundle(creation.gear_bundles)

    print("\nCharacter preview:")
    print(f"Name: {name}")
    print(f"Background: {background}")
    print(f"Race: {race_id}")
    print(f"Class: {class_id}")
    print(f"Ability method: {ability_method.value}")
    print(f"Ability scores: {ability_scores}")
    print(f"Skills: {trained_skills or 'None'}")
    print(f"Feats: {feat_ids or 'None'}")
    print(f"Gear bundle: {gear_bundle_id or 'None'}")

    confirm = input("Confirm and start adventure? (y/n): ").strip().lower()
    if not confirm.startswith("y"):
        print("Character creation cancelled. Returning to start menu.\n")
        return None

    return CharacterCreationSelection(
        name=name,
        background=background,
        race_id=race_id,
        class_id=class_id,
        ability_method=ability_method,
        ability_scores=ability_scores,
        trained_skills=trained_skills,
        feat_ids=feat_ids,
        gear_bundle_id=gear_bundle_id,
    )


def main() -> None:
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(CONTENT_ROOT / "start_menu.yaml", catalog)

    while True:
        selection = _render_menu(start_menu)
        if isinstance(selection, StartMenuOption):
            _handle_save_selection(selection)
            break

        creation_selection = _handle_new_game_flow(selection)
        if creation_selection:
            new_save = start_menu.start_new_game(
                catalog=catalog, selection=creation_selection, slot=0, start_option_id=start_menu.options[0].id
            )
            print("\nNew game ready!")
            print(f"Slot: {new_save.slot}")
            print(f"Adventurer: {new_save.game_state.pc.name}")
            print(f"Starting at: {new_save.game_state.current_location_id}")
            print("Enjoy your journey into Silverthorn!")
            break


if __name__ == "__main__":
    main()
