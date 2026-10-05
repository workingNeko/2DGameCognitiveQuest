import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((1280, 720), pygame.HIDDEN)

class MockMenu:
    def __init__(self):
        self.selected_student = {'first_name': 'Tester'}
        self.audio_manager = None
        self.cursor_pos = (640, 360)
        self.current_gesture = 'OPEN'
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False
        self.camera_frame = None

menu = MockMenu()
from screens.quarter3 import Quarter3

for map_name in ['map7.txt', 'map8.txt', 'map9.txt']:
    print(f"=== Testing Objective Trails for {map_name} ===")
    q3 = Quarter3(screen, menu, map_name)
    guide = q3.path_guide

    # Test stations 1 to 5
    for st in range(1, 6):
        q3.quiz_station_index = st
        for q_state in [0, 1, 2, 3, 4, 7, 8, 9]:
            q3.quiz_state = q_state
            target = guide.get_active_hierarchy_target()
            assert target is not None, f"Target is None for station {st} in state {q_state} on {map_name}!"
            tx, ty, t_name, is_portal = target
            expected_pos = q3.quiz_stations[st]
            assert (tx, ty) == expected_pos, f"Expected Station {st} pos {expected_pos}, got {t_name} at {(tx, ty)} in state {q_state}!"
            assert "Skeleton" not in t_name, f"Trail incorrectly points to Skeleton during Station {st} in state {q_state}!"
        print(f"  Station {st}: Confirmed trail consistently targets Station {st} in all states!")

    # Test after all 5 stations completed
    q3.quiz_station_index = 6
    q3.guardian_skeleton_state = 1
    q3.solar_array_puzzle_solved = False
    q3.quiz_state = 0
    target = guide.get_active_hierarchy_target()
    assert target is not None and "Skeleton" in target[2], f"Expected trail to target Skeleton after station 5, got {target}!"
    print(f"  All 5 Done: Trail correctly targets Skeleton Guardian -> {target[2]}")

    # Test after puzzle solved
    q3.solar_array_puzzle_solved = True
    q3.guardian_skeleton_state = 5
    q3.quiz_state = 6
    target = guide.get_active_hierarchy_target()
    assert target is not None and target[3] is True, f"Expected trail to target Goal Portal after puzzle solved, got {target}!"
    print(f"  Puzzle Solved: Trail correctly targets Goal Portal -> {target[2]}")

print("\nALL QUARTER 3 OBJECTIVE TRAIL TESTS PASSED 100%!")
