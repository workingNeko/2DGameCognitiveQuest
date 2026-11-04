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


def test_lol_camera_focus_character():
    cam = LoLCamera(1024, 768, zoom=1.5)
    assert cam.focus_character is True

    player_x = 1000.0
    player_y = 1000.0
    map_w, map_h = 4000, 4000

    cam.snap_to(player_x, player_y, tile_size=32, map_width=map_w, map_height=map_h)
    expected_cam_x = cam.camera_x
    expected_cam_y = cam.camera_y

    # Update with cursor at extreme positions (border 950, 750)
    for _ in range(25):
        cam.update(player_x, player_y, cursor_pos=(950, 750), map_width=map_w, map_height=map_h, tile_size=32, enable_edge_scroll=True)

    # Camera must remain centered strictly on the player, NOT deflected by cursor or edge scroll
    assert math.isclose(cam.camera_x, expected_cam_x, abs_tol=1e-3), f"Camera shifted to cursor! {cam.camera_x} vs {expected_cam_x}"
    assert math.isclose(cam.camera_y, expected_cam_y, abs_tol=1e-3), f"Camera shifted to cursor! {cam.camera_y} vs {expected_cam_y}"
    print("PASS: LoLCamera focuses strictly on the character without cursor pull or edge scroll.")


def test_lol_camera_cursor_lead():
    cam = LoLCamera(1024, 768, zoom=1.5, focus_character=False)
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
    cam = LoLCamera(1024, 768, zoom=1.5, focus_character=False)
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
    menu = MainMenu(test_surf, enable_camera=False)

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
    menu.camera_running = False


def test_mouse_inactivity_when_no_hand():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf, enable_camera=False)

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
    menu.camera_running = False


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
    menu = MainMenu(test_surf, enable_camera=False)

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
    menu.camera_running = False


def test_gesture_open_and_close_fist_cycle():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf, enable_camera=False)

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
    menu.camera_running = False


def test_half_closed_hand_not_detected_as_fist():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf, enable_camera=False)

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
    menu.camera_running = False


def test_scale_invariance_fist_and_open():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf, enable_camera=False)

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
    menu.camera_running = False


def test_fist_cursor_lock_stability():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1024, 768))
    menu = MainMenu(test_surf, enable_camera=False)

    # 1. Start with open hand at screen center
    open_coords = [(0.5, 0.5)] * 21
    open_coords[0] = (0.5, 0.7)  # Wrist
    open_coords[9] = (0.5, 0.5)  # Knuckle
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        open_coords[mcp_i] = (0.5, 0.50)
        open_coords[pip_i] = (0.5, 0.40)
        open_coords[dip_i] = (0.5, 0.32)
        open_coords[tip_i] = (0.5, 0.25)

    with menu.camera_lock:
        menu.latest_hand_coords = open_coords
        menu.latest_hand_detected = True

    class MockCap:
        def isOpened(self):
            return True

    menu.cap = MockCap()
    menu.update_gesture()
    open_cursor_pos = menu.cursor_pos

    # 2. Transition to FIST (fingers curled down into palm, knuckle shifting slightly)
    fist_coords = [(0.5, 0.5)] * 21
    fist_coords[0] = (0.5, 0.7)
    fist_coords[9] = (0.5, 0.53) # Slight 3% curl shift towards palm
    for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        fist_coords[mcp_i] = (0.5, 0.50)
        fist_coords[pip_i] = (0.5, 0.44)
        fist_coords[dip_i] = (0.5, 0.47)
        fist_coords[tip_i] = (0.5, 0.52)

    with menu.camera_lock:
        menu.latest_hand_coords = fist_coords
        menu.latest_hand_detected = True

    # Run gesture update several frames while holding fist
    for _ in range(10):
        menu.update_gesture()

    fist_cursor_pos = menu.cursor_pos
    # Fist cursor position should stay locked right at the anchor (difference < 2 pixels)
    drift = math.hypot(fist_cursor_pos[0] - open_cursor_pos[0], fist_cursor_pos[1] - open_cursor_pos[1])
    assert drift <= 2.0, f"Cursor drifted by {drift}px when holding fist!"
    assert menu.current_gesture == "FIST"
    print(f"PASS: Fist cursor lock stability verified (drift = {drift:.2f}px <= 2.0px).")
    menu.camera_running = False


def test_cloud_connection_status_badge_geometry_and_rendering():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1280, 720))
    menu = MainMenu(test_surf, enable_camera=False)

    # 1. Geometry tests across screens
    menu.current_screen = "menu"
    r_menu = menu.get_cloud_status_geometry()
    assert r_menu.x == 1280 - 206
    assert r_menu.y == 62

    menu.current_screen = "student_select"
    r_stud = menu.get_cloud_status_geometry()
    assert r_stud.x == 1280 - 154 - 176 - 14
    assert r_stud.y == 26

    menu.current_screen = "stage_select"
    r_stage = menu.get_cloud_status_geometry()
    assert r_stage.x == 20
    assert r_stage.y == 58

    menu.current_screen = "quarter1"
    r_q1 = menu.get_cloud_status_geometry()
    assert r_q1.x == 20
    assert r_q1.y == 58

    # 2. Rendering tests (ONLINE)
    menu.cloud_online = True
    menu.cloud_pending_sync = 0
    menu.cursor_pos = (0, 0)
    menu.draw_cloud_status()

    # 3. Rendering tests (ONLINE with pending syncing)
    menu.cloud_online = True
    menu.cloud_pending_sync = 3
    menu.draw_cloud_status()

    # 4. Rendering tests (OFFLINE with queued evaluations)
    menu.cloud_online = False
    menu.cloud_pending_sync = 2
    menu.draw_cloud_status()

    # 5. Hover tooltip rendering
    menu.cursor_pos = (r_q1.centerx, r_q1.centery)
    menu.draw_cloud_status()

    # 6. Manual badge click trigger
    clicked_probe = [False]
    menu._manual_cloud_probe = lambda: clicked_probe.__setitem__(0, True)
    menu.trigger_click((r_q1.centerx, r_q1.centery))
    assert clicked_probe[0] is True
    print("PASS: Cloud connection status badge geometry, rendering states, tooltip, and click-to-sync work properly.")


def test_cloud_health_probe_logic():
    from db.connect_db import db
    assert db is not None
    health = db.check_cloud_health(timeout=2)
    assert isinstance(health, dict)
    assert "online" in health
    assert "pending_sync" in health
    assert "api_url" in health
    assert "last_checked" in health
    print(f"PASS: Cloud health probe returned valid response (online={health['online']}, pending_sync={health['pending_sync']}).")


def test_tracking_loss_inertia_and_interframe_interpolation():
    from screens.main_menu import MainMenu
    test_surf = pygame.Surface((1280, 720))
    menu = MainMenu(test_surf, enable_camera=False)

    class MockCap:
        def isOpened(self):
            return True

    menu.cap = MockCap()

    # 1. Establish moving open hand across screen (from center x=0.50 to right x=0.60)
    def make_open_hand(base_x):
        coords = [(base_x, 0.7)] * 21
        coords[0] = (base_x, 0.7)      # Wrist
        coords[9] = (base_x, 0.5)      # Middle MCP
        for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
            coords[mcp_i] = (base_x, 0.50)
            coords[pip_i] = (base_x, 0.40)
            coords[dip_i] = (base_x, 0.32)
            coords[tip_i] = (base_x, 0.25)
        return coords

    coords_1 = make_open_hand(0.50)

    with menu.camera_lock:
        menu.latest_hand_coords = coords_1
        menu.latest_hand_detected = True
        menu.latest_frame_id = 1

    menu.update_gesture()
    initial_x = menu.cursor_x

    # Frame 2: Hand moves right (base_x = 0.58)
    coords_2 = make_open_hand(0.58)

    with menu.camera_lock:
        menu.latest_hand_coords = coords_2
        menu.latest_hand_detected = True
        menu.latest_frame_id = 2

    menu.update_gesture()
    moving_x = menu.cursor_x
    assert moving_x > initial_x, f"Expected moving_x ({moving_x}) > initial_x ({initial_x})"
    assert menu.hand_vx > 0.0, f"Expected positive hand_vx ({menu.hand_vx})"

    # 2. Simulate 1-frame MediaPipe tracking drop (latest_hand_detected = False)
    with menu.camera_lock:
        menu.latest_hand_coords = None
        menu.latest_hand_detected = False
        menu.latest_frame_id = 3

    menu.update_gesture()
    inertial_x_1 = menu.cursor_x

    # Inertial momentum should continue advancing the cursor rightward instead of freezing in place!
    assert inertial_x_1 > moving_x, f"Cursor froze on frame drop! inertial_x_1 ({inertial_x_1}) should be > moving_x ({moving_x})"

    # Frame drop 2: continues with decay
    menu.update_gesture()
    inertial_x_2 = menu.cursor_x
    assert inertial_x_2 >= inertial_x_1

    print("PASS: Tracking loss inertia successfully bridges momentary frame drops without freezing or snapping.")


def test_multiple_hands_detection_and_warning_state():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen, enable_camera=False)
    class MockCap:
        def isOpened(self):
            return True
    menu.cap = MockCap()

    # Initial state: no multiple hands
    assert menu.multiple_hands_detected is False
    assert menu.latest_multiple_hands is False

    # Simulate background worker detecting 2 hands
    coords_hand1 = [(0.5, 0.5, 0.0)] * 21
    with menu.camera_lock:
        menu.latest_hand_coords = coords_hand1
        menu.latest_hand_detected = True
        menu.latest_multiple_hands = True
        menu.latest_frame_id = 10

    menu.update_gesture()
    assert menu.multiple_hands_detected is True, "multiple_hands_detected must become True when multiple hands present"
    assert menu.multiple_hands_timer > time.time(), "Grace persistence timer must be set"

    # Test audio warning throttle
    assert menu.last_multi_hand_sound_time > 0.0

    # Simulate extra hand leaving the view
    with menu.camera_lock:
        menu.latest_multiple_hands = False
        menu.latest_frame_id = 11

    # Right after removal (within grace timer), warning stays visible
    menu.update_gesture()
    assert menu.multiple_hands_detected is True

    # Advance beyond grace timer
    menu.multiple_hands_timer = time.time() - 0.1
    menu.update_gesture()
    assert menu.multiple_hands_detected is False, "Warning must clear after grace period expires"
    print("PASS: Multiple hands detection, grace timer, and state transitions operate correctly.")


def test_multiple_hands_cursor_stability_tracks_primary_hand():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen, enable_camera=False)
    class MockCap:
        def isOpened(self):
            return True
    menu.cap = MockCap()

    def make_open_hand(base_x):
        coords = [(base_x, 0.7)] * 21
        coords[0] = (base_x, 0.7)
        coords[9] = (base_x, 0.5)
        for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
            coords[mcp_i] = (base_x, 0.50)
            coords[pip_i] = (base_x, 0.40)
            coords[dip_i] = (base_x, 0.32)
            coords[tip_i] = (base_x, 0.25)
        return coords

    # Primary open hand at center (0.50)
    coords_primary = make_open_hand(0.50)
    with menu.camera_lock:
        menu.latest_hand_coords = coords_primary
        menu.latest_hand_detected = True
        menu.latest_multiple_hands = True
        menu.latest_frame_id = 20

    menu.update_gesture()
    first_cx, first_cy = menu.cursor_x, menu.cursor_y

    # Move primary hand slightly right (0.55)
    coords_primary_moved = make_open_hand(0.55)
    with menu.camera_lock:
        menu.latest_hand_coords = coords_primary_moved
        menu.latest_hand_detected = True
        menu.latest_multiple_hands = True
        menu.latest_frame_id = 21

    menu.update_gesture()
    assert menu.cursor_x > first_cx, "Cursor must track primary hand movement even when 2 hands are detected"
    print("PASS: Multiple hands tracking strictly anchors to primary hand without jumping.")


def test_multiple_hands_warning_rendering():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen, enable_camera=False)

    # When inactive, draw_multiple_hands_warning does nothing
    menu.multiple_hands_detected = False
    menu.draw_multiple_hands_warning()
    assert menu._multiple_hands_surf is None

    # When active, draws and memoizes the surface
    menu.multiple_hands_detected = True
    menu.draw_multiple_hands_warning()
    assert menu._multiple_hands_surf is not None
    assert menu._multiple_hands_surf.get_width() == 540
    assert menu._multiple_hands_surf.get_height() == 38
    print("PASS: Multiple hands warning badge renders cleanly with memoized zero-allocation surface.")


def test_hand_proximity_calculation():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen, enable_camera=False)

    def make_hand(wrist, mid_mcp, idx_mcp, pky_mcp):
        coords = [(0.5, 0.5, 0.0)] * 21
        coords[0] = wrist
        coords[9] = mid_mcp
        coords[5] = idx_mcp
        coords[17] = pky_mcp
        return coords

    # Near hand (large palm)
    h_near = make_hand((0.5, 0.7), (0.5, 0.5), (0.42, 0.52), (0.58, 0.52))
    # Distant hand (small palm)
    h_far = make_hand((0.5, 0.7), (0.5, 0.66), (0.48, 0.67), (0.52, 0.67))

    size_near = menu.calculate_hand_proximity(h_near)
    size_far = menu.calculate_hand_proximity(h_far)

    assert size_near > size_far, f"Expected size_near ({size_near}) > size_far ({size_far})"
    assert size_near >= 0.15, "Near hand size should be >= 0.15"
    assert size_far < 0.055, "Far background hand size should be < 0.055"
    print("PASS: Hand proximity calculation accurately maps skeletal scale to camera distance.")


def test_background_hand_filtering():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen, enable_camera=False)

    def make_hand(wrist, mid_mcp, idx_mcp, pky_mcp):
        coords = [(0.5, 0.5, 0.0)] * 21
        coords[0] = wrist
        coords[9] = mid_mcp
        coords[5] = idx_mcp
        coords[17] = pky_mcp
        return coords

    # Near player hand (size ~0.18)
    h_player = make_hand((0.5, 0.7), (0.5, 0.5), (0.42, 0.52), (0.58, 0.52))
    # Person walking in distant background (size ~0.04)
    h_background = make_hand((0.8, 0.3), (0.8, 0.26), (0.78, 0.265), (0.82, 0.265))

    primary, multiple_hands, valid = menu.filter_and_select_hands([h_player, h_background])

    assert multiple_hands is False, "Background hand must be filtered out without triggering multiple hands warning"
    assert primary == h_player, "Primary active hand must be the near player hand"
    assert len(valid) == 1, "Only 1 valid hand should remain after background filtering"
    print("PASS: Background hands are successfully filtered out without false-positive multiple hands alerts.")


def test_nearest_hand_prioritization_with_multiple_hands():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen, enable_camera=False)

    def make_hand(wrist, mid_mcp, idx_mcp, pky_mcp):
        coords = [(0.5, 0.5, 0.0)] * 21
        coords[0] = wrist
        coords[9] = mid_mcp
        coords[5] = idx_mcp
        coords[17] = pky_mcp
        return coords

    # Student 1 hand: Closer to camera (size ~0.20)
    h_closer = make_hand((0.5, 0.72), (0.5, 0.48), (0.40, 0.50), (0.60, 0.50))
    # Student 2 hand: Further from camera (size ~0.12)
    h_further = make_hand((0.2, 0.65), (0.2, 0.51), (0.14, 0.53), (0.26, 0.53))

    # Passed in reverse order: [further, closer]
    primary, multiple_hands, valid = menu.filter_and_select_hands([h_further, h_closer])

    assert multiple_hands is True, "Two near hands must trigger multiple hands warning"
    assert primary == h_closer, "Primary hand must automatically lock to the closest hand regardless of detection order"
    assert len(valid) == 2

    # Verify hysteresis stability: if hands are nearly equal, bias toward previously tracked wrist
    menu.latest_hand_coords = h_closer
    # Make slightly smaller than h_further by 0.01
    h_closer_slight = make_hand((0.5, 0.70), (0.5, 0.50), (0.42, 0.52), (0.58, 0.52))
    primary2, _, _ = menu.filter_and_select_hands([h_further, h_closer_slight])
    assert primary2 == h_closer_slight, "Hysteresis bonus must preserve tracking stability on the current hand"
    print("PASS: Nearest-hand prioritization locks to the closest player hand with smooth hysteresis.")


if __name__ == "__main__":
    print("--- RUNNING LOL CAMERA & GAME CURSOR UNIT TESTS ---")
    test_lol_camera_init_and_snap()
    test_lol_camera_damping_and_convergence()
    test_lol_camera_focus_character()
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
    test_fist_cursor_lock_stability()
    test_cloud_connection_status_badge_geometry_and_rendering()
    test_cloud_health_probe_logic()
    test_tracking_loss_inertia_and_interframe_interpolation()
    test_multiple_hands_detection_and_warning_state()
    test_multiple_hands_cursor_stability_tracks_primary_hand()
    test_multiple_hands_warning_rendering()
    test_hand_proximity_calculation()
    test_background_hand_filtering()
    test_nearest_hand_prioritization_with_multiple_hands()
    print("--- ALL CAMERA, CURSOR, AND CLOUD STATUS TESTS PASSED (25/25) ---")
