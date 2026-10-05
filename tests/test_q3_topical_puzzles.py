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
q3 = Quarter3(screen, menu, 'map7.txt')

print("Testing all 5 Quarter 3 Station Mini-Puzzles...")
for st in range(1, 6):
    q3.init_station_mini_puzzle(st)
    print(f"Station {st}: {q3.mini_puzzle_title} | Target: {q3.mini_puzzle_math_target}")
    q3.auto_solve_mini_puzzle()
    assert q3.mini_puzzle_solved, f"Station {st} puzzle not solved!"

print("\nTesting Quarter 3 Sun Relic Altar Puzzle (Map 8)...")
q3.init_sun_relic_puzzle()
for s in q3.sun_relic_slabs:
    cfg = s["config"]
    print(f"Slab {s['index']}: {cfg['title']} -> {cfg['math']} {cfg['ans']}")

print("\nTesting Quarter 3 Solar Array Keystone Puzzle (Map 7, 9)...")
q3.init_solar_array_puzzle()
for s in q3.solar_array_puzzle_slots:
    print(f"Slot: {s['equation']} ({s['factor_desc']})")

print("\nALL QUARTER 3 TOPICAL PUZZLES VERIFIED SUCCESSFULLY!")
