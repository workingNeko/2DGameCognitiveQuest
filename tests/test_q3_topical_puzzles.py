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

print("Testing Unified Quarter 3 Sun Temple Fraction Match across map7, map8, and map9...")
for map_file in ["map7.txt", "map8.txt", "map9.txt"]:
    q3 = Quarter3(screen, menu, map_file)
    q3.init_fraction_match()
    assert len(q3.fraction_match_slots) == 4, f"{map_file}: expected 4 slots"
    assert len(q3.fraction_match_pieces) == 4, f"{map_file}: expected 4 visual cards"

    for s in q3.fraction_match_slots:
        low_eq = f"{s['equation']} {s['factor_desc']}".lower()
        assert "minute" not in low_eq and "hour" not in low_eq and "clock" not in low_eq
        print(f"  [{map_file}] Slot: {s['equation']} ({s['factor_desc']})")

    q3.draw()
    q3.auto_solve_fraction_match()
    assert q3.fraction_match_all_placed, f"{map_file}: auto_solve_fraction_match did not place all 4 cards!"
    q3.draw()
    q3.cleanup()

print("\nALL QUARTER 3 SUN TEMPLE FRACTION MATCH CHECKS VERIFIED SUCCESSFULLY!")
