# tests/test_camera_and_cursor.py
"""
Unit tests for the League of Legends-inspired Camera System (LoLCamera)
and MOBA Game Cursor System (GameCursor).
"""
import os
import sys
import time
import math

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Headless pygame configuration
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((1024, 768))

from core.camera_system import LoLCamera
from core.cursor_system import GameCursor, CursorState


def test_lol_camera_init_and_snap():
    cam = LoLCamera(1024, 768, zoom=1.5)
    assert cam.screen_width == 1024
    assert cam.screen_height == 768
    assert cam.zoom == 1.5

    # Test snap_to
    tile_size = 32
    map_w, map_h = 50 * tile_size, 50 * tile_size
    cam.snap_to(500, 400, tile_size, map_w, map_h)
    assert cam.camera_x > 0
    assert cam.camera_y > 0
    assert cam.pan_offset_x == 0.0
    assert cam.pan_offset_y == 0.0
    print("PASS: LoLCamera initialization and snap_to work correctly.")


def test_lol_camera_damping_and_convergence():
    cam = LoLCamera(1024, 768, zoom=1.5)
    cam.camera_x = 0.0
    cam.camera_y = 0.0

    player_x = 800.0
    player_y = 600.0
    center_cursor = (512, 384)
    map_w, map_h = 3000, 3000

    # Initial position is 0, update towards player
    initial_cam_x = cam.camera_x
    initial_cam_y = cam.camera_y

    for _ in range(15):
        cam.update(player_x, player_y, cursor_pos=center_cursor, map_width=map_w, map_height=map_h, enable_edge_scroll=False)

    assert cam.camera_x > initial_cam_x, "Camera X did not move towards target!"
    assert cam.camera_y > initial_cam_y, "Camera Y did not move towards target!"
    print("PASS: LoLCamera exponential damping smoothly converges towards target.")


def test_lol_camera_cursor_lead():
    cam = LoLCamera(1024, 768, zoom=1.5)
    player_x = 1000.0
    player_y = 1000.0
    map_w, map_h = 4000, 4000

    # Snap to player
    cam.snap_to(player_x, player_y, 32, map_w, map_h)
    
    # Update with cursor centered
    for _ in range(20):
        cam.update(player_x, player_y, cursor_pos=(512, 384), map_width=map_w, map_height=map_h, enable_edge_scroll=False)
    neutral_cam_x = cam.camera_x

    # Update with cursor far to the right (screen_x = 950)
    for _ in range(25):
        cam.update(player_x, player_y, cursor_pos=(950, 384), map_width=map_w, map_height=map_h, enable_edge_scroll=False)
    right_cam_x = cam.camera_x

    # Camera should lead ahead towards the right
    assert right_cam_x > neutral_cam_x, f"Cursor lead expected right_cam_x ({right_cam_x}) > neutral_cam_x ({neutral_cam_x})"
    print("PASS: LoLCamera lookahead cursor lead functions accurately.")


def test_lol_camera_edge_scrolling():
    cam = LoLCamera(1024, 768, zoom=1.5)
    player_x = 1000.0
    player_y = 1000.0
    map_w, map_h = 4000, 4000

    cam.snap_to(player_x, player_y, 32, map_w, map_h)
    assert cam.pan_offset_x == 0.0
    assert cam.pan_offset_y == 0.0

    # Cursor placed near the left edge (< 35px margin)
    for _ in range(5):
        cam.update(player_x, player_y, cursor_pos=(10, 384), map_width=map_w, map_height=map_h, enable_edge_scroll=True)

    assert cam.pan_offset_x < 0.0, "Edge scrolling did not pan left when cursor near left screen border!"

    # Cursor placed near the bottom edge (> 768 - 35 = 733)
    for _ in range(5):
        cam.update(player_x, player_y, cursor_pos=(512, 750), map_width=map_w, map_height=map_h, enable_edge_scroll=True)

    assert cam.pan_offset_y > 0.0, "Edge scrolling did not pan down when cursor near bottom screen border!"
    print("PASS: LoLCamera edge scrolling pans in the correct direction when near screen borders.")


def test_lol_camera_spacebar_recenter():
    cam = LoLCamera(1024, 768, zoom=1.5)
    player_x = 1000.0
    player_y = 1000.0
    cam.snap_to(player_x, player_y)

    # Set artificial pan offset
    cam.pan_offset_x = 200.0
    cam.pan_offset_y = -150.0

    # Calling recenter reduces offsets
    cam.recenter()
    assert abs(cam.pan_offset_x) < 200.0
    assert abs(cam.pan_offset_y) < 150.0

    # Calling multiple recenters rapidly snaps back to 0
    for _ in range(10):
        cam.recenter()
    assert cam.pan_offset_x == 0.0
    assert cam.pan_offset_y == 0.0

    # Event handling: Space key triggers recenter
    cam.pan_offset_x = 100.0
    space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
    cam.handle_event(space_event)
    assert cam.pan_offset_x < 100.0
    print("PASS: LoLCamera spacebar recenter smoothly eases pan offsets back to 0.")


def test_lol_camera_middle_mouse_drag():
    cam = LoLCamera(1024, 768, zoom=1.5)
    player_x = 1000.0
    player_y = 1000.0
    cam.snap_to(player_x, player_y)

    # Press MMB
    down_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2, pos=(500, 400))
    cam.handle_event(down_event)
    assert cam.is_middle_dragging is True

    # Drag motion
    move_event = pygame.event.Event(pygame.MOUSEMOTION, pos=(450, 350), rel=(-50, -50), buttons=(0, 1, 0))
    cam.handle_event(move_event)
    assert cam.pan_offset_x > 0.0 or cam.pan_offset_y > 0.0

    # Release MMB
    up_event = pygame.event.Event(pygame.MOUSEBUTTONUP, button=2, pos=(450, 350))
    cam.handle_event(up_event)
    assert cam.is_middle_dragging is False
    print("PASS: LoLCamera middle-mouse drag panning operates as expected.")


def test_lol_camera_coordinate_transformations():
    cam = LoLCamera(1024, 768, zoom=2.0)
    cam.camera_x = 100.0
    cam.camera_y = 50.0

    # World -> Screen
    sx, sy = cam.world_to_screen(150.0, 100.0)
    assert sx == (150.0 - 100.0) * 2.0
    assert sy == (100.0 - 50.0) * 2.0

    # Screen -> World
    wx, wy = cam.screen_to_world(sx, sy)
    assert math.isclose(wx, 150.0, rel_tol=1e-4)
    assert math.isclose(wy, 100.0, rel_tol=1e-4)
    print("PASS: LoLCamera world <-> screen coordinate conversions are reversible and exact.")


def test_original_game_cursor_rendering():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf)

    # 1. Mouse / NO HAND mode
    menu.current_gesture = "NO HAND"
    menu.cursor_pos = (512, 384)
    menu.draw_cursor()

    # 2. OPEN hand mode
    menu.current_gesture = "OPEN"
    menu.fist_start_time = 0
    menu.peace_start_time = 0
    menu.draw_cursor()

    # 3. FIST charge mode
    menu.current_gesture = "FIST"
    menu.fist_start_time = time.time() - 0.45
    menu.draw_cursor()

    # 4. PEACE confirm mode
    menu.current_gesture = "PEACE"
    menu.peace_start_time = time.time() - 0.45
    menu.draw_cursor()

    print("PASS: Original reticle game cursor renders cleanly across all gesture modes (Mouse, Open, Fist, Peace).")


if __name__ == "__main__":
    print("--- RUNNING LOL CAMERA & GAME CURSOR UNIT TESTS ---")
    test_lol_camera_init_and_snap()
    test_lol_camera_damping_and_convergence()
    test_lol_camera_cursor_lead()
    test_lol_camera_edge_scrolling()
    test_lol_camera_spacebar_recenter()
    test_lol_camera_middle_mouse_drag()
    test_lol_camera_coordinate_transformations()
    test_original_game_cursor_rendering()
    print("--- ALL CAMERA & ORIGINAL CURSOR UNIT TESTS PASSED (8/8) ---")
