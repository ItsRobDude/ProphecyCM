"""Minimal bootstrapping to validate object creation and serialization."""

from prophecycm.content import seed_save_file


def main() -> None:
    save = seed_save_file()
    print(save.to_json())


if __name__ == "__main__":
    main()
