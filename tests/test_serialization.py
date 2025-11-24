from prophecycm.__main__ import demo_state
from prophecycm.state import SaveFile


def test_save_file_round_trip():
    save = demo_state()
    payload = save.to_json()
    loaded = SaveFile.from_json(payload)

    assert loaded.game_state.pc.name == save.game_state.pc.name
    assert loaded.slot == save.slot
