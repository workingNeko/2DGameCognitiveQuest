import os
import sys

# Ensure headless execution
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.stageselect import StageSelect

class MockAudioManager:
    def __init__(self):
        self.played = []
    def play_sfx(self, name):
        self.played.append(name)
    def play_bgm(self, *args, **kwargs):
        pass

class MockMainMenu:
    def __init__(self):
        self.screen = screen
        self.audio_manager = MockAudioManager()
        self.selected_student = {"id": 999999, "name": "Tester", "gender": "male"}
        self.student_id = 999999
        self.current_screen = "stage_select"
        self.stage_select = None

def test_map_integrity():
    map_path = os.path.join("assets", "map", "map.txt")
    with open(map_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\r\n") for line in f if line.strip()]
    assert len(lines) == 27, f"Expected 27 rows, got {len(lines)}"
    for idx, line in enumerate(lines):
        assert len(line) == 53, f"Row {idx} length expected 53, got {len(line)}"
        assert "D" not in line, f"Pyramid tile 'D' found in row {idx}!"
    print("[PASS] Map dimensions (27x53) and pyramid tile removal verified.")

def test_stage_select_interactables():
    menu = MockMainMenu()
    stage = StageSelect(menu.screen, menu)

    # 1. Verify 4 interactables loaded
    assert len(stage.interactables) == 4, f"Expected 4 interactables, got {len(stage.interactables)}"
    obj_ids = [obj["id"] for obj in stage.interactables]
    expected_ids = ["fountain", "chest", "monolith", "lake"]
    for eid in expected_ids:
        assert eid in obj_ids, f"Missing interactable {eid}"
    print(f"[PASS] All 4 interactables initialized: {obj_ids}")

    # 2. Test Fountain interaction
    fountain = next(o for o in stage.interactables if o["id"] == "fountain")
    stage.player_x = fountain["world_x"]
    stage.player_y = fountain["world_y"] + 20
    stage.update()
    assert stage.nearby_interactable == fountain, "Player should be near fountain"

    # Trigger interaction via key
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    result = stage.handle_event(event)
    assert result == "interactable_triggered", f"Expected 'interactable_triggered', got {result}"
    assert stage.interactable_dialogue_state == 1, "Dialogue state should be 1"
    assert stage.active_interactable == fountain, "Active interactable should be fountain"
    assert "chime" in menu.audio_manager.played, "Chime SFX should have played"

    # Advance dialogue
    while stage.interactable_dialogue_state == 1:
        stage.advance_dialogue()
        stage.advance_dialogue()

    assert stage.interactable_dialogue_state == 0, "Dialogue should be finished"
    assert stage.active_interactable is None, "Active interactable should be reset"
    print("[PASS] Fountain interaction and dialogue cycling verified.")

    # 3. Test Supply Chest interaction and opening animation
    chest = next(o for o in stage.interactables if o["id"] == "chest")
    stage.player_x = chest["world_x"]
    stage.player_y = chest["world_y"] + 20
    stage.update()
    assert stage.nearby_interactable == chest, "Player should be near chest"

    assert not chest["opened"]
    stage.trigger_interactable(chest)
    assert chest["opened"] is True
    assert "wood_snap" in menu.audio_manager.played, "Wood snap SFX should have played"

    # Simulate frames to ensure chest finishes opening
    for _ in range(60):
        stage.update()
    assert chest["frame"] == 3, f"Chest frame should be 3, got {chest['frame']}"

    while stage.interactable_dialogue_state == 1:
        stage.advance_dialogue()
        stage.advance_dialogue()
    print("[PASS] Supply chest opening animation and dialogue verified.")

    # 4. Test Sun Monolith interaction
    monolith = next(o for o in stage.interactables if o["id"] == "monolith")
    stage.player_x = monolith["world_x"]
    stage.player_y = monolith["world_y"] + 20
    stage.update()
    stage.trigger_interactable(monolith)
    assert stage.interactable_dialogue_state == 1
    assert "portal_warp" in menu.audio_manager.played
    while stage.interactable_dialogue_state == 1:
        stage.advance_dialogue()
        stage.advance_dialogue()
    print("[PASS] Sun monolith interaction verified.")

    # 5. Test Wishing Lake interaction
    lake = next(o for o in stage.interactables if o["id"] == "lake")
    stage.player_x = lake["world_x"]
    stage.player_y = lake["world_y"] + 20
    stage.update()
    stage.trigger_interactable(lake)
    assert stage.interactable_dialogue_state == 1
    assert "coin" in menu.audio_manager.played
    while stage.interactable_dialogue_state == 1:
        stage.advance_dialogue()
        stage.advance_dialogue()
    print("[PASS] Wishing lake interaction verified.")

    # 6. Test Render / Draw without errors
    stage.update()
    stage.draw()

    # Test drawing during active dialogue
    stage.trigger_interactable(fountain)
    stage.update()
    stage.draw()
    print("[PASS] StageSelect draw cycle executed cleanly.")

if __name__ == "__main__":
    test_map_integrity()
    test_stage_select_interactables()
    print("\nALL INTERACTIVE HUB TESTS PASSED!")
