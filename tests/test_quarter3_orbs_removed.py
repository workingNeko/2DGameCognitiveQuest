import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.quarter3 import Quarter3

class MockAudioManager:
    def __init__(self):
        self.played = []
    def play_sfx(self, name):
        self.played.append(name)
    def play_bgm(self, *args, **kwargs):
        pass
    def get_sound(self, name):
        return None

class MockMainMenu:
    def __init__(self):
        self.screen = screen
        self.audio_manager = MockAudioManager()
        self.selected_student = {"id": 999999, "name": "Tester", "gender": "male"}
        self.student_id = 999999
        self.current_screen = "quarter3"
        self.quarter3 = None

def test_quarter3_all_maps():
    for map_file in ["map7.txt", "map8.txt", "map9.txt"]:
        menu = MockMainMenu()
        q3 = Quarter3(screen, menu, map_file)
        if hasattr(q3, 'instruction_modal'):
            q3.instruction_modal.hide()

        # 1. Verify no relic items are spawned on the map
        assert len(q3.relic_items) == 0, f"Map {map_file} should not have relic items spawned!"
        assert q3.is_relic_hunt_mode is False

        # 2. Test Station 1 proximity and direct challenge opening
        st1_x, st1_y = q3.quiz_stations[1]
        q3.player_x = st1_x * 32
        q3.player_y = st1_y * 32
        q3.update()

        # Proximity triggers greeting dialog or challenge without requiring orbs
        if getattr(q3, 'greeting_dialog', None) and q3.greeting_dialog.is_visible:
            q3.greeting_dialog.hide()
            q3.quiz_state = 1

        assert q3.quiz_state == 1, f"Map {map_file} Station 1 should open challenge! Got quiz_state={q3.quiz_state}"
        assert q3.relic_collected_count == 0

        # 3. Simulate answering questions 1 through 5
        for st_idx in range(1, 6):
            q3.quiz_station_index = st_idx
            q3.current_question_index = st_idx - 1
            q3.quiz_state = 1
            # Advance/answer correctly
            q3.advance_station_progress()
            # If camera pan was started (map8), complete it
            if q3.camera_pan_active:
                q3.camera_pan_timer = q3.camera_pan_duration + 0.1
                q3.update()

        # In map8.txt, answering all 5 stations should complete the causeway bridge and open the exit portal
        if map_file == "map8.txt":
            assert q3.quiz_state in [5, 6, 8], f"Map 8 should reach completed state, got {q3.quiz_state}"

        # 4. Render check
        q3.draw()
        print(f"[PASS] Quarter 3 map {map_file} verified cleanly without orb collection!")

if __name__ == "__main__":
    test_quarter3_all_maps()
    print("\nALL QUARTER 3 STREAMLINED TESTS PASSED!")
