"""Interactive bootstrapper for the ProphecyCM demo content."""

from __future__ import annotations

from pathlib import Path

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


def _handle_new_game_flow(flow: StartMenuNewGameFlow) -> bool:
    print(f"\n{flow.label}")
    if flow.description:
        print(flow.description)

    if flow.content_warning:
        accepted = _render_content_warning(flow.content_warning)
        if not accepted:
            print("Returning to start menu...\n")
            return False

    creation_config = flow.require_character_creation()
    print("Starting character creation...")
    print(f"Available races: {[race.name for race in creation_config.races]}")
    print(f"Available classes: {[char_class.name for char_class in creation_config.classes]}")
    print("(Character creator UI would launch here.)")
    return True


def main() -> None:
    catalog = ContentCatalog.load(CONTENT_ROOT)
    start_menu = load_start_menu_config(CONTENT_ROOT / "start_menu.yaml", catalog)

    while True:
        selection = _render_menu(start_menu)
        if isinstance(selection, StartMenuOption):
            _handle_save_selection(selection)
            break

        if _handle_new_game_flow(selection):
            break


if __name__ == "__main__":
    main()
