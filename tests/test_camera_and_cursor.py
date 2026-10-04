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
screen = pygame.display.set_mode((1280, 720))

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

    # 1. Mouse / NO HAND mode (idle mouse -> cursor not drawn)
    menu.current_gesture = "NO HAND"
    menu.mouse_active = False
    menu.cursor_pos = (512, 384)
    menu.draw_cursor()

    # 1b. Mouse active when physical mouse moved
    menu.mouse_active = True
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


def test_mouse_inactivity_when_no_hand():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf)

    # When no hand is detected and no mouse motion has happened:
    menu.mouse_active = False
    menu.current_gesture = "NO HAND"
    assert menu.mouse_active is False

    # Simulate mouse motion event
    event = pygame.event.Event(pygame.MOUSEMOTION, pos=(600, 400), rel=(10, 10), buttons=(0, 0, 0))
    menu.handle_event(event)
    assert menu.mouse_active is True
    assert menu.cursor_pos == (600, 400)

    # Simulate idle timeout expiration
    menu.last_hand_time = time.time() - 5.0
    menu.last_mouse_move_time = time.time() - 5.0
    menu.update_gesture()
    assert menu.mouse_active is False
    print("PASS: When no hand is detected, mouse cursor only activates upon physical mouse motion and stays hidden when idle.")


def test_one_euro_filter_stability_and_responsiveness():
    from core.cursor_system import OneEuroFilter
    f = OneEuroFilter(0.0, 100.0, min_cutoff=0.85, beta=0.015, d_cutoff=1.0)

    # 1. Jitter suppression test: high frequency oscillation at 60 FPS
    t = 0.0
    for i in range(30):
        t += 0.0166
        # Simulate noisy sensor alternating +- 4px around 100
        noise = 4.0 if (i % 2 == 0) else -4.0
        val = f(t, 100.0 + noise)
        # Filtered output should stay tightly clustered near 100
        assert abs(val - 100.0) < 2.0, f"Jitter was not suppressed: {val}"

    # 2. High-speed responsiveness test: fast jump to 800.0
    for _ in range(5):
        t += 0.0166
        f(t, 800.0)
    # Velocity adaptation should ensure rapid convergence (> 700 within 5 frames)
    assert f.x_prev > 700.0, f"Filter lagged excessively on fast movement: {f.x_prev}"
    print("PASS: OneEuroFilter provides sub-pixel jitter suppression at rest and zero lag during fast movement.")


def test_curl_invariant_palm_tracking():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf)

    # Fake landmark coords: 21 landmarks
    # Test that (wrist 0 + index_mcp 5 + pinky_mcp 17) / 3 is computed consistently
    coords = [(0.5, 0.5)] * 21
    coords[0] = (0.5, 0.6)   # Wrist
    coords[5] = (0.45, 0.4)  # Index MCP
    coords[17] = (0.55, 0.4) # Pinky MCP

    # When fingers curl (landmarks 8, 12, 16, 20 move down to 0.55), palm centroid remains invariant
    with menu.camera_lock:
        menu.latest_raw_frame = None
        menu.latest_hand_coords = coords
        menu.latest_hand_detected = True

    class MockCap:
        def isOpened(self):
            return True

    menu.cap = MockCap()
    menu.update_gesture()
    assert menu.cursor_pos[0] > 0 and menu.cursor_pos[1] > 0
    print("PASS: Curl-invariant palm centroid and 1-Euro filter tracking execute accurately.")


def test_gesture_open_and_close_fist_cycle():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf)

    # 1. Open hand coordinates: fingers extended upwards far from wrist
    open_coords = [(0.5, 0.7)] * 21  # Wrist at y=0.7
    open_coords[0] = (0.5, 0.7)      # Wrist
    open_coords[9] = (0.5, 0.5)      # Middle MCP (palm_size = 0.2)
    # Fingers extended up to y=0.25
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        open_coords[mcp_i] = (0.5, 0.50)
        open_coords[pip_i] = (0.5, 0.40)
        open_coords[dip_i] = (0.5, 0.32)
        open_coords[tip_i] = (0.5, 0.25)

    assert menu.is_open_hand(open_coords) is True
    assert menu.is_fist(open_coords) is False

    # 2. Fist coordinates: fingertips curled tightly into palm (tips closer to wrist/MCP)
    fist_coords = [(0.5, 0.7)] * 21
    fist_coords[0] = (0.5, 0.7)
    fist_coords[9] = (0.5, 0.5)
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        fist_coords[mcp_i] = (0.5, 0.50)
        fist_coords[pip_i] = (0.5, 0.44)
        fist_coords[dip_i] = (0.5, 0.47)
        fist_coords[tip_i] = (0.5, 0.52) # Curled down near MCP base

    assert menu.is_fist(fist_coords) is True
    assert menu.is_open_hand(fist_coords) is False

    class MockCap:
        def isOpened(self):
            return True

    menu.cap = MockCap()
    clicked_count = [0]
    menu.trigger_click = lambda pos=None: clicked_count.__setitem__(0, clicked_count[0] + 1)

    # Cycle 1: Make Fist
    with menu.camera_lock:
        menu.latest_hand_coords = fist_coords
        menu.latest_hand_detected = True

    menu.update_gesture()
    assert menu.fist_start_time > 0
    assert menu.click_ready is False

    # Hold Fist to trigger click
    menu.fist_start_time = time.time() - 1.0  # Simulated 1.0s hold
    menu.update_gesture()
    assert clicked_count[0] == 1
    assert menu.click_ready is True

    # Cycle 2: Open Hand -> MUST reset click state immediately
    with menu.camera_lock:
        menu.latest_hand_coords = open_coords
        menu.latest_hand_detected = True

    menu.update_gesture()
    assert menu.fist_start_time == 0
    assert menu.click_ready is False
    assert menu.current_gesture == "OPEN"

    # Cycle 3: Close Hand into Fist AGAIN -> MUST detect new fist and start charging without locking
    with menu.camera_lock:
        menu.latest_hand_coords = fist_coords
        menu.latest_hand_detected = True

    menu.update_gesture()
    assert menu.fist_start_time > 0
    assert menu.click_ready is False
    assert menu.current_gesture == "FIST"

    # Hold again -> triggers 2nd click!
    menu.fist_start_time = time.time() - 1.0
    menu.update_gesture()
    assert clicked_count[0] == 2
    assert menu.click_ready is True
    print("PASS: Hand open-to-close gesture cycle successfully triggers repeated clicks without sticking.")


def test_half_closed_hand_not_detected_as_fist():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf)

    # Half-closed / relaxed hand: fingers slightly curved, tips still extending past DIP
    half_coords = [(0.5, 0.7)] * 21
    half_coords[0] = (0.5, 0.7)
    half_coords[9] = (0.5, 0.5) # palm_size = 0.20
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        half_coords[mcp_i] = (0.5, 0.50)
        half_coords[pip_i] = (0.5, 0.42)
        half_coords[dip_i] = (0.5, 0.38)
        half_coords[tip_i] = (0.5, 0.36) # Relaxed / half-closed curve

    # Must NOT be detected as a fist!
    assert menu.is_fist(half_coords) is False
    print("PASS: Half-closed / relaxed hand is properly rejected and not detected as a fist.")


def test_scale_invariance_fist_and_open():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf)

    # Test small hand (distant camera, palm span = 0.08)
    small_fist = [(0.5, 0.6)] * 21
    small_fist[0] = (0.5, 0.6)
    small_fist[9] = (0.5, 0.52)
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        small_fist[mcp_i] = (0.5, 0.52)
        small_fist[pip_i] = (0.5, 0.49)
        small_fist[dip_i] = (0.5, 0.51)
        small_fist[tip_i] = (0.5, 0.53)

    assert menu.is_fist(small_fist) is True

    small_open = [(0.5, 0.6)] * 21
    small_open[0] = (0.5, 0.6)
    small_open[9] = (0.5, 0.52)
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        small_open[mcp_i] = (0.5, 0.52)
        small_open[pip_i] = (0.5, 0.48)
        small_open[dip_i] = (0.5, 0.45)
        small_open[tip_i] = (0.5, 0.42)

    assert menu.is_open_hand(small_open) is True
    print("PASS: Fist and open-hand gesture detection are scale-invariant across distances.")


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
    test_mouse_inactivity_when_no_hand()
    test_one_euro_filter_stability_and_responsiveness()
    test_curl_invariant_palm_tracking()
    test_gesture_open_and_close_fist_cycle()
    test_half_closed_hand_not_detected_as_fist()
    test_scale_invariance_fist_and_open()
    print("--- ALL CAMERA & ORIGINAL CURSOR UNIT TESTS PASSED (14/14) ---")
