# screens/main_menu.py - USING WRIST FOR STABLE CURSOR
import sys
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import types
if "matplotlib" not in sys.modules:
    _mpl_stub = types.ModuleType("matplotlib")
    _mpl_stub.__path__ = []
    _plt_stub = types.ModuleType("matplotlib.pyplot")
    _mpl_stub.pyplot = _plt_stub
    sys.modules["matplotlib"] = _mpl_stub
    sys.modules["matplotlib.pyplot"] = _plt_stub

import pygame
import cv2
import mediapipe as mp
import numpy as np
import os
import time
import math
import threading
from core.audio_manager import audio_manager
from core.cursor_system import OneEuroFilter, game_cursor
from ui.button import Button
from core.version import APP_VERSION, APP_NAME, GITHUB_RELEASES_URL
from core.update_manager import UpdateManager, UpdateState


class MainMenu:

    def __init__(self, screen, enable_camera=True):

        self.screen = screen
        self.w, self.h = screen.get_size()
        self.enable_camera = enable_camera

        # ==========================================
        # HIGH-PRECISION GESTURE DETECTION
        # ==========================================

        # MediaPipe setup with higher recall and balanced tracking
        self.mp_hands = None
        self.hands = None
        self._use_tasks_api = False
        if enable_camera:
            try:
                # Priority 1: Modern MediaPipe Tasks API (MediaPipe >= 0.10.x) in robust IMAGE detection mode
                model_path = os.path.join("assets", "models", "hand_landmarker.task")
                if os.path.exists(model_path) and hasattr(mp, 'tasks') and hasattr(mp.tasks, 'vision'):
                    from mediapipe.tasks import python as mp_python
                    from mediapipe.tasks.python import vision as mp_vision
                    base_options = mp_python.BaseOptions(model_asset_path=model_path)
                    options = mp_vision.HandLandmarkerOptions(
                        base_options=base_options,
                        running_mode=mp_vision.RunningMode.VIDEO,
                        num_hands=1,
                        min_hand_detection_confidence=0.45,
                        min_hand_presence_confidence=0.45,
                        min_tracking_confidence=0.45
                    )
                    self.hands = mp_vision.HandLandmarker.create_from_options(options)
                    self._use_tasks_api = True
                    print(f"[OK] MediaPipe HandLandmarker Tasks API initialized from {model_path} (single hand optimized)!")
                elif hasattr(mp, 'solutions') and hasattr(mp.solutions, 'hands'):
                    self.mp_hands = mp.solutions.hands
                    # Optimized for AMD A4-6300 (Dual Core): use lightweight model_complexity=0 and single hand
                    self.hands = self.mp_hands.Hands(
                        max_num_hands=1,
                        min_detection_confidence=0.45,
                        min_tracking_confidence=0.45,
                        model_complexity=0
                    )
                    self._use_tasks_api = False
                    print("[OK] MediaPipe legacy solutions API initialized successfully!")
            except Exception as e:
                print(f"[WARN] MediaPipe hands init exception: {e}")
                self.hands = None

        # Camera setup (640x480 crisp capture with buffer size 1 for zero lag)
        self.camera_size = (160, 120)
        self.show_camera_overlay = False  # Set to False to remove the visual camera overlay box (Toggle with C)
        self.cap = self._open_camera() if enable_camera else None

        # Threaded Camera & MediaPipe Background Worker (60 FPS Unlocked)
        self.camera_running = enable_camera
        self.camera_lock = threading.Lock()
        self.latest_raw_frame = None
        self.latest_hand_landmarks = None
        self.latest_hand_detected = False
        self.latest_multiple_hands = False

        if self.cap is not None:
            self.camera_thread = threading.Thread(target=self._camera_worker, daemon=True)
            self.camera_thread.start()

        # Gesture state
        self.current_gesture = "NO HAND"
        self.cursor_pos = (self.w // 2, self.h // 2)
        self.camera_frame = None

        # Click tracking
        self.fist_start_time = 0
        self.peace_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False
        self.popup_state = None
        self.update_manager = UpdateManager(local_version=APP_VERSION)
        try:
            # Silent asynchronous background check on launch to detect new releases
            self.update_manager.check_for_updates()
        except Exception:
            pass
        self.update_check_btn_rect = None
        self.update_download_btn_rect = None
        self.update_cancel_btn_rect = None
        self.update_browser_btn_rect = None
        self.update_install_btn_rect = None
        self.update_retry_btn_rect = None
        self.footer_update_rect = None
        self.audio_dialog_rect = None
        self.audio_test_rect = None
        self.audio_done_rect = None

        # Multiple hands detection & warning HUD state
        self.multiple_hands_detected = False
        self.multiple_hands_timer = 0.0
        self.last_multi_hand_sound_time = 0.0
        self._multiple_hands_surf = None
        self.latest_multiple_hands = False
        self.MIN_HAND_SIZE = 0.055

        # Cursor sensitivity, active camera bounds & jitter suppression
        # Expanded bounds (0.15-0.85) provide comfortable full-screen reach without edge-pegging or twitchiness
        self.cursor_sensitivity = 2.0
        self.cam_x_min = 0.15
        self.cam_x_max = 0.85
        self.cam_y_min = 0.15
        self.cam_y_max = 0.85

        self.cursor_x = float(self.w // 2)
        self.cursor_y = float(self.h // 2)
        self.target_history = []
        self.hand_was_detected = False

        # OneEuroFilter tuned for jitter-free tracking and snappy zero-lag movement:
        # min_cutoff=0.18 eliminates camera sensor noise and resting hand tremor; beta=0.03 eliminates motion latency
        self.cursor_filter_x = OneEuroFilter(t0=time.time(), x0=self.cursor_x, min_cutoff=0.18, beta=0.03, d_cutoff=1.0)
        self.cursor_filter_y = OneEuroFilter(t0=time.time(), x0=self.cursor_y, min_cutoff=0.18, beta=0.03, d_cutoff=1.0)
        self.fist_anchor_x = None
        self.fist_anchor_y = None

        # Store last cursor position for when hand is lost
        self.last_cursor_x = self.w // 2
        self.last_cursor_y = self.h // 2

        # Hand grace period
        self.last_hand_time = time.time()
        self.HAND_GRACE = 1.5  # Keep cursor for 1.5 seconds after hand lost

        # Mouse activity tracking (only show mouse cursor when mouse is moved)
        self.mouse_active = False
        self.last_mouse_pos = pygame.mouse.get_pos()
        self.last_mouse_move_time = 0.0
        self.MOUSE_IDLE_TIMEOUT = 3.0  # Hide mouse cursor after 3 seconds of inactivity when no hand is present

        # ==========================================
        # STUDENT
        # ==========================================

        self.selected_student = None
        self.student_id = None

        # ==========================================
        # BACKGROUND
        # ==========================================

        bg_path = os.path.join("assets", "images", "menu_background.png")

        if os.path.exists(bg_path):
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.w, self.h))
        else:
            self.bg_image = None
            self.bg_color = (135, 206, 235)

        # ==========================================
        # FONTS
        # ==========================================

        self.title_font = pygame.font.SysFont("Comic Sans MS", 80, bold=True)
        self.button_font = pygame.font.SysFont("Comic Sans MS", 32, bold=True)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 22)
        self.dialogue_font = pygame.font.SysFont("Comic Sans MS", 30, bold=True)

        # ==========================================
        # LOAD IMAGES
        # ==========================================

        self.boy_image = None
        self.girl_image = None
        self.boy_avatar = None
        self.girl_avatar = None

        boy_path = os.path.join("assets", "images", "boy_in_uniform.png")
        girl_path = os.path.join("assets", "images", "girl_in_uniform.png")
        exit_btn_path = os.path.join("assets", "images", "exitbutton.png")

        boy_avatar_path = os.path.join("assets", "images", "boy.png")
        girl_avatar_path = os.path.join("assets", "images", "girl.png")

        # BOY IMAGE
        if os.path.exists(boy_path):
            self.boy_image = pygame.image.load(boy_path).convert_alpha()
            self.boy_image = pygame.transform.scale(self.boy_image, (280, 400))
            self.boy_x = 50
            self.boy_y = self.h - 450

        # GIRL IMAGE
        if os.path.exists(girl_path):
            self.girl_image = pygame.image.load(girl_path).convert_alpha()
            self.girl_image = pygame.transform.scale(self.girl_image, (280, 400))
            self.girl_x = self.w - 330
            self.girl_y = self.h - 450

        # BOY AVATAR
        if os.path.exists(boy_avatar_path):
            self.boy_avatar = pygame.image.load(boy_avatar_path).convert_alpha()
            self.boy_avatar = pygame.transform.scale(self.boy_avatar, (40, 40))

        # GIRL AVATAR
        if os.path.exists(girl_avatar_path):
            self.girl_avatar = pygame.image.load(girl_avatar_path).convert_alpha()
            self.girl_avatar = pygame.transform.scale(self.girl_avatar, (40, 40))

        # ==========================================
        # DIALOGUES - SIMPLE
        # ==========================================

        self.dialogue_lines = [
            "Welcome to Cognitive Maze!",
            "Let's learn and have fun together!",
            "Please select your student profile."
        ]
        self.current_line = 0
        self.dialogue_active = True

        # ==========================================
        # AUDIO & SOUND SYSTEM
        # ==========================================
        self.audio_manager = audio_manager
        self._active_audio_screen = "menu"
        self.audio_manager.play_scene_music("menu")

        # ==========================================
        # DIALOGUE BOX POSITION
        # ==========================================

        self.dialogue_box_width = 800
        self.dialogue_box_height = 180
        self.dialogue_box_x = self.w // 2 - self.dialogue_box_width // 2
        self.dialogue_box_y = self.h - self.dialogue_box_height - 40
        self.dialogue_rect = pygame.Rect(self.dialogue_box_x, self.dialogue_box_y,
                                         self.dialogue_box_width, self.dialogue_box_height)

        self.title_y = 20
        self.error_y = self.h - 90
        self.student_card_rect = None

        # ==========================================
        # BUTTONS
        # ==========================================
        self.setup_buttons()

        # ==========================================
        # SCREEN STATES
        # ==========================================

        self.current_screen = "menu"
        self.stage_select = None
        self.student_select = None
        self.tutorial = None
        self.leaderboard = None
        self.quarter1 = None
        self.quarter2 = None
        self.quarter3 = None
        self.quarter4 = None

        # ==========================================
        # MESSAGES
        # ==========================================
        self.show_no_student_message = False
        self.no_student_timer = 0

        # ==========================================
        # LIVE CLOUD HEALTH MONITOR & OFFLINE EVALUATION SYNC
        # ==========================================
        self.cloud_online = True
        self.cloud_pending_sync = 0
        self.cloud_last_checked = 0.0
        self.cloud_monitor_running = enable_camera

        if enable_camera:
            try:
                self._cloud_thread = threading.Thread(target=self._cloud_status_worker, daemon=True)
                self._cloud_thread.start()
            except Exception as e:
                print(f"[WARN] Cloud monitor thread init failed: {e}")

        print(f"[GAME] Simple Gesture Control Active!")
        print(f"   - WRIST movement controls cursor (stable when making fist)")
        print(f"   - Make a FIST and hold for {self.CLICK_HOLD_TIME} seconds to click")

    def _manual_cloud_probe(self):
        """Perform an immediate non-blocking health check and offline queue sync."""
        lock = getattr(self, '_cloud_probe_lock', None)
        if lock is None:
            self._cloud_probe_lock = threading.Lock()
            lock = self._cloud_probe_lock
        if not lock.acquire(blocking=False):
            return
        try:
            from db.connect_db import db
            if db:
                health = db.check_cloud_health(timeout=4)
                self.cloud_online = health.get("online", False)
                self.cloud_pending_sync = health.get("pending_sync", 0)
                self.cloud_last_checked = health.get("last_checked", time.time())
        except Exception:
            self.cloud_online = False
        finally:
            lock.release()

    def _cloud_status_worker(self):
        """Asynchronous daemon worker to probe live Vercel API and sync offline records periodically without blocking Pygame."""
        while getattr(self, 'cloud_monitor_running', True):
            in_active_stage = getattr(self, 'current_screen', 'menu') in (
                "quarter1", "quarter2", "quarter3", "quarter4", "tutorial"
            )
            if not in_active_stage or getattr(self, 'cloud_pending_sync', 0) > 0:
                self._manual_cloud_probe()

            # Check every 30 seconds (sleep in 1-second increments for responsive exit)
            for _ in range(30):
                if not getattr(self, 'cloud_monitor_running', True):
                    break
                time.sleep(1.0)

    # ==========================================
    # SIMPLE FIST DETECTION (USING FINGER TIPS)
    # ==========================================

    def _get_lm(self, hand_data, idx):
        """Extract (x, y, z) landmark coordinates from either list or MediaPipe structure"""
        if isinstance(hand_data, list):
            item = hand_data[idx]
            if len(item) >= 3:
                return float(item[0]), float(item[1]), float(item[2])
            return float(item[0]), float(item[1]), 0.0
        lm = hand_data.landmark[idx]
        return float(lm.x), float(lm.y), float(getattr(lm, 'z', 0.0))

    def _dist_2d(self, p1, p2):
        """Calculates 2D planar Euclidean distance between two landmarks (dx, dy)."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _dist_lm(self, p1, p2):
        """Calculates 3D Euclidean distance between two landmarks."""
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        dz = p1[2] - p2[2] if (len(p1) > 2 and len(p2) > 2) else 0.0
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def is_fist(self, hand_data):
        """Detect closed fist (at least 3 of 4 fingers curled into palm) with 2D projection and wrist depth invariance."""
        if hand_data is None:
            return False
        try:
            wrist = self._get_lm(hand_data, 0)
            closed_count = 0
            for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
                mcp = self._get_lm(hand_data, mcp_i)
                pip = self._get_lm(hand_data, pip_i)
                tip = self._get_lm(hand_data, tip_i)

                d2_mcp_pip = self._dist_2d(mcp, pip)
                d2_mcp_tip = self._dist_2d(mcp, tip)
                ratio_2d = (d2_mcp_tip / d2_mcp_pip) if d2_mcp_pip > 0.001 else 1.0

                d3_mcp_pip = self._dist_lm(mcp, pip)
                d3_mcp_tip = self._dist_lm(mcp, tip)
                ratio_3d = (d3_mcp_tip / d3_mcp_pip) if d3_mcp_pip > 0.001 else 1.0

                d_wrist_pip = self._dist_2d(wrist, pip)
                d_wrist_tip = self._dist_2d(wrist, tip)

                # In a curled finger:
                # 1) Knuckle ratio in 2D camera view or 3D is small (ratio < 1.20)
                # 2) OR Tip has curled inward closer to wrist than PIP knuckle
                is_curled = (min(ratio_2d, ratio_3d) < 1.20) or (d_wrist_tip < d_wrist_pip * 1.05)
                if is_curled:
                    closed_count += 1

            return closed_count >= 3
        except Exception:
            return False

    def is_open_hand(self, hand_data):
        """Detect open hand (at least 3 fingers extended away from palm)"""
        if hand_data is None:
            return False
        try:
            wrist = self._get_lm(hand_data, 0)
            open_count = 0
            for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
                mcp = self._get_lm(hand_data, mcp_i)
                pip = self._get_lm(hand_data, pip_i)
                tip = self._get_lm(hand_data, tip_i)

                d2_mcp_pip = self._dist_2d(mcp, pip)
                d2_mcp_tip = self._dist_2d(mcp, tip)
                ratio_2d = (d2_mcp_tip / d2_mcp_pip) if d2_mcp_pip > 0.001 else 1.0

                d3_mcp_pip = self._dist_lm(mcp, pip)
                d3_mcp_tip = self._dist_lm(mcp, tip)
                ratio_3d = (d3_mcp_tip / d3_mcp_pip) if d3_mcp_pip > 0.001 else 1.0

                d_wrist_pip = self._dist_2d(wrist, pip)
                d_wrist_tip = self._dist_2d(wrist, tip)

                # In an extended finger:
                # Tip is extended away from MCP (ratio > 1.85) AND further from wrist than PIP
                if max(ratio_2d, ratio_3d) > 1.85 and (d_wrist_tip > d_wrist_pip * 1.05):
                    open_count += 1

            return open_count >= 3
        except Exception:
            return False

    def is_peace_sign(self, hand_data):
        """Detect peace sign / digit 2 (index and middle fingers open, ring and pinky closed)"""
        if hand_data is None:
            return False
        try:
            wrist = self._get_lm(hand_data, 0)
            fingers = []
            for mcp_i, pip_i, dip_i, tip_i in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
                mcp = self._get_lm(hand_data, mcp_i)
                pip = self._get_lm(hand_data, pip_i)
                tip = self._get_lm(hand_data, tip_i)

                d2_mcp_pip = self._dist_2d(mcp, pip)
                d2_mcp_tip = self._dist_2d(mcp, tip)
                ratio_2d = (d2_mcp_tip / d2_mcp_pip) if d2_mcp_pip > 0.001 else 1.0

                d3_mcp_pip = self._dist_lm(mcp, pip)
                d3_mcp_tip = self._dist_lm(mcp, tip)
                ratio_3d = (d3_mcp_tip / d3_mcp_pip) if d3_mcp_pip > 0.001 else 1.0

                d_wrist_pip = self._dist_2d(wrist, pip)
                d_wrist_tip = self._dist_2d(wrist, tip)

                is_curled = (min(ratio_2d, ratio_3d) < 1.20) or (d_wrist_tip < d_wrist_pip * 1.05)
                is_extended = (max(ratio_2d, ratio_3d) > 1.85) and (d_wrist_tip > d_wrist_pip * 1.05)
                fingers.append((is_extended, is_curled))

            return fingers[0][0] and fingers[1][0] and fingers[2][1] and fingers[3][1]
        except Exception:
            return False

    def calculate_hand_proximity(self, hand_coords):
        """
        Calculates apparent physical scale/proximity of a hand from 21 normalized landmarks.
        Returns a float proportional to hand closeness to the camera lens.
        Uses rigid skeletal palm anatomy (wrist to MCPs) to remain invariant to gestures.
        """
        if not hand_coords or len(hand_coords) < 21:
            return 0.0
        try:
            wrist = hand_coords[0]
            idx_mcp = hand_coords[5]
            mid_mcp = hand_coords[9]
            pky_mcp = hand_coords[17]
            palm_len = math.hypot(wrist[0] - mid_mcp[0], wrist[1] - mid_mcp[1])
            palm_width = math.hypot(idx_mcp[0] - pky_mcp[0], idx_mcp[1] - pky_mcp[1])
            return (palm_len + palm_width) * 0.5
        except Exception:
            return 0.0

    def filter_and_select_hands(self, candidate_hands):
        """
        Filters out distant background hands and selects the hand nearest to camera.
        candidate_hands: list of 21-landmark coordinate lists
        Returns: (primary_coords, multiple_hands_detected, valid_hands)
        """
        if not candidate_hands:
            return None, False, []

        valid_hands = []
        for h in candidate_hands:
            if h and len(h) >= 21:
                size = self.calculate_hand_proximity(h)
                valid_hands.append({'coords': h, 'size': size})

        has_real_size = any(h['size'] > 0.0 for h in valid_hands)
        if has_real_size:
            min_size = getattr(self, 'MIN_HAND_SIZE', 0.055)
            filtered = [h for h in valid_hands if h['size'] >= min_size]
            valid_hands = filtered if filtered else [max(valid_hands, key=lambda x: x['size'])]

        if not valid_hands:
            return None, False, []

        multiple_hands = len(valid_hands) > 1

        prev_coords = getattr(self, 'latest_hand_coords', None)
        best_hand = None
        best_score = -1.0
        for h in valid_hands:
            score = h['size']
            if prev_coords and len(prev_coords) >= 21:
                prev_wrist = prev_coords[0]
                curr_wrist = h['coords'][0]
                dist = math.hypot(curr_wrist[0] - prev_wrist[0], curr_wrist[1] - prev_wrist[1])
                if dist < 0.15:
                    score += 0.03
            if score > best_score:
                best_score = score
                best_hand = h

        primary = best_hand['coords'] if best_hand else valid_hands[0]['coords']
        return primary, multiple_hands, valid_hands

    def _open_camera(self):
        """Discovers and initializes the best active webcam hardware across available device indices and backends."""
        # Prioritize Device 0 DirectShow for fastest Windows launch (<0.1s)
        fast_attempts = [
            (0, cv2.CAP_DSHOW, "DirectShow Device 0"),
            (0, cv2.CAP_MSMF, "Media Foundation Device 0"),
            (1, cv2.CAP_DSHOW, "DirectShow Device 1"),
            (0, cv2.CAP_ANY, "Default Device 0"),
        ]
        for idx, backend_flag, desc in fast_attempts:
            try:
                cap = cv2.VideoCapture(idx, backend_flag)
                if cap.isOpened():
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        try:
                            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                        except Exception:
                            pass
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        # Request 320x240 native capture for AMD A4-6300 dual-core hardware (reduces USB bus & memory bandwidth)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 320)
                        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 240)
                        print(f"[OK] Camera initialized via {desc} ({actual_w}x{actual_h} @ 30 FPS)!")
                        return cap
                    cap.release()
            except Exception:
                pass
        print("[WARN] No working camera found, falling back to mouse control.")
        return None

    def _camera_worker(self):
        """
        Asynchronous background worker for camera frame grabbing and MediaPipe ML inference.
        Specially optimized for AMD A4-6300 dual-core CPU desktop:
        - Limits OpenCV internal thread pool to 1 thread to avoid thread starvation on dual-core CPU.
        - Downscales camera frame directly to 320x240 for 75% memory/cache reduction and 4x faster MediaPipe inference (~10-12ms).
        - Hardware capture pacing prevents CPU burning when waiting for 30 FPS camera frames.
        """
        try:
            cv2.setNumThreads(1)
            if hasattr(cv2, 'ocl') and hasattr(cv2.ocl, 'setUseOpenCL'):
                cv2.ocl.setUseOpenCL(False)
        except Exception:
            pass

        # Pre-allocate L2-cache-friendly 320x240 buffers (230 KB each vs 921 KB at 640x480)
        small_bgr = np.empty((240, 320, 3), dtype=np.uint8)
        flipped_small = np.empty((240, 320, 3), dtype=np.uint8)
        rgb_buf = np.empty((240, 320, 3), dtype=np.uint8)

        while self.camera_running and self.cap is not None and self.cap.isOpened():
            try:
                # Direct hardware grab driven by camera sensor clock.
                # Flush stale DirectShow buffer backlog (< 2ms per grab means buffered stale frame):
                t0 = time.perf_counter()
                if not self.cap.grab():
                    time.sleep(0.002)
                    continue
                t_elapsed = time.perf_counter() - t0
                stale_drops = 0
                while t_elapsed < 0.002 and stale_drops < 4:
                    t0 = time.perf_counter()
                    if not self.cap.grab():
                        break
                    t_elapsed = time.perf_counter() - t0
                    stale_drops += 1

                ret, img = self.cap.retrieve()
                if not ret or img is None:
                    time.sleep(0.002)
                    continue

                now = time.time()

                # Zero-copy optimization: If native capture is 320x240, bypass resize entirely.
                # Fits comfortably inside AMD A4-6300's 1MB shared L2 cache and avoids 921KB frame copies.
                h, w = img.shape[:2]
                if w == 320 and h == 240:
                    cv2.flip(img, 1, dst=flipped_small)
                else:
                    cv2.resize(img, (320, 240), dst=small_bgr, interpolation=cv2.INTER_LINEAR)
                    cv2.flip(small_bgr, 1, dst=flipped_small)

                cv2.cvtColor(flipped_small, cv2.COLOR_BGR2RGB, dst=rgb_buf)
                preview = (
                    cv2.resize(flipped_small, self.camera_size, interpolation=cv2.INTER_NEAREST)
                    if (getattr(self, 'show_camera_overlay', False) or getattr(self, 'current_screen', '') == 'tutorial')
                    else None
                )

                # MediaPipe inference with instant detection & continuous temporal tracking
                coords = None
                multiple_hands = False
                if self.hands is not None:
                    try:
                        if getattr(self, '_use_tasks_api', False):
                            now_ms = int(now * 1000)
                            last_ms = getattr(self, '_last_video_timestamp_ms', 0)
                            if now_ms <= last_ms:
                                now_ms = last_ms + 1
                            self._last_video_timestamp_ms = now_ms

                            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_buf)
                            result = self.hands.detect_for_video(mp_img, now_ms)
                            raw_hands = []
                            if result and result.hand_landmarks:
                                for h_lms in result.hand_landmarks:
                                    raw_hands.append([(float(lm.x), float(lm.y), float(getattr(lm, 'z', 0.0))) for lm in h_lms])
                        else:
                            results = self.hands.process(rgb_buf)
                            raw_hands = []
                            if results and results.multi_hand_landmarks:
                                for h_lms in results.multi_hand_landmarks:
                                    raw_hands.append([(float(lm.x), float(lm.y), float(getattr(lm, 'z', 0.0))) for lm in h_lms.landmark])

                        coords, multiple_hands, _ = self.filter_and_select_hands(raw_hands)
                    except Exception:
                        coords = None
                        multiple_hands = False

                with self.camera_lock:
                    if preview is not None:
                        self.latest_raw_frame = preview
                    self.latest_hand_coords = coords
                    self.latest_hand_detected = (coords is not None and len(coords) == 21)
                    self.latest_multiple_hands = multiple_hands
                    self.latest_frame_id = getattr(self, 'latest_frame_id', 0) + 1
                    self.latest_frame_time = now

            except Exception:
                pass
            time.sleep(0.001)

    def update_gesture(self):
        """Update gesture detection - Instant read from threaded worker with 60 FPS continuous interpolation"""
        if self.cap is None or not self.cap.isOpened():
            if getattr(self, 'mouse_active', False):
                if time.time() - getattr(self, 'last_mouse_move_time', 0.0) <= self.MOUSE_IDLE_TIMEOUT:
                    curr_m = pygame.mouse.get_pos()
                    self.cursor_pos = curr_m
                    self.cursor_x, self.cursor_y = float(curr_m[0]), float(curr_m[1])
                else:
                    self.mouse_active = False
            game_cursor.update(self.cursor_pos, "NO HAND", 0, self.CLICK_HOLD_TIME, 0)
            return

        try:
            now_t = time.time()
            with self.camera_lock:
                img_preview = self.latest_raw_frame
                hand_coords = getattr(self, 'latest_hand_coords', None)
                hand_detected = getattr(self, 'latest_hand_detected', False)
                has_multi_hands = getattr(self, 'latest_multiple_hands', False)
                frame_id = getattr(self, 'latest_frame_id', 0)

            # Update multiple hands detection state and audio warning
            if has_multi_hands:
                if not getattr(self, 'multiple_hands_detected', False):
                    if hasattr(self, 'audio_manager') and self.audio_manager:
                        now_s = time.time()
                        if now_s - getattr(self, 'last_multi_hand_sound_time', 0.0) > 3.0:
                            self.audio_manager.play_sfx("timer_warning")
                            self.last_multi_hand_sound_time = now_s
                self.multiple_hands_detected = True
                self.multiple_hands_timer = now_t + 1.2
            elif now_t > getattr(self, 'multiple_hands_timer', 0.0):
                self.multiple_hands_detected = False

            if img_preview is not None:
                self.camera_frame = img_preview
            is_new_camera_frame = (frame_id != getattr(self, '_last_processed_frame_id', -1)) or (self.cap is None)

            if hand_detected and hand_coords and len(hand_coords) == 21:
                self.tracking_lost_frames = 0
                self.last_hand_time = now_t
                self.mouse_active = False
                self.last_mouse_pos = pygame.mouse.get_pos()

                # Detect gestures with relative palm scaling
                fist_detected = self.is_fist(hand_coords)
                open_detected = self.is_open_hand(hand_coords)
                peace_detected = self.is_peace_sign(hand_coords) if (not fist_detected and not open_detected) else False

                # 1. Rigid Palm Base Tracking:
                # Wrist (0), Index MCP (5), Middle MCP (9), Ring MCP (13), Pinky MCP (17)
                # 5-point rigid palm centroid suppresses raw landmark noise by ~55%:
                wrist = hand_coords[0]
                idx_mcp = hand_coords[5]
                mid_mcp = hand_coords[9]
                rng_mcp = hand_coords[13]
                pky_mcp = hand_coords[17]
                palm_x = (wrist[0] + idx_mcp[0] + mid_mcp[0] + rng_mcp[0] + pky_mcp[0]) / 5.0
                palm_y = (wrist[1] + idx_mcp[1] + mid_mcp[1] + rng_mcp[1] + pky_mcp[1]) / 5.0

                # Map palm position to screen coordinates with increased sensitivity bounds
                target_x = float(np.interp(palm_x, [self.cam_x_min, self.cam_x_max], [0, self.w]))
                target_y = float(np.interp(palm_y, [self.cam_y_min, self.cam_y_max], [0, self.h]))

                # Subtle sensor deadband at rest: absorbs webcam pixel noise & sensor shimmer
                prev_raw_x = getattr(self, '_last_raw_x', target_x)
                prev_raw_y = getattr(self, '_last_raw_y', target_y)
                raw_delta = math.hypot(target_x - prev_raw_x, target_y - prev_raw_y)
                if raw_delta < 2.5 and getattr(self, 'hand_was_detected', False):
                    target_x = prev_raw_x * 0.85 + target_x * 0.15
                    target_y = prev_raw_y * 0.85 + target_y * 0.15
                self._last_raw_x = target_x
                self._last_raw_y = target_y

                # If hand was just detected after a break, snap filter immediately
                was_just_acquired = not getattr(self, 'hand_was_detected', False)
                if was_just_acquired:
                    self.cursor_filter_x.reset(now_t, target_x)
                    self.cursor_filter_y.reset(now_t, target_y)
                    self.cursor_x = target_x
                    self.cursor_y = target_y
                    self.filtered_target_x = target_x
                    self.filtered_target_y = target_y
                    self.hand_vx = 0.0
                    self.hand_vy = 0.0
                    self.hand_was_detected = True
                    self._last_processed_frame_id = frame_id
                    self._last_cursor_update_t = now_t

                prev_cx = self.cursor_x
                prev_cy = self.cursor_y

                # Process OneEuroFilter whenever new camera frame arrived
                if is_new_camera_frame:
                    self._last_processed_frame_id = frame_id
                    self.filtered_target_x = self.cursor_filter_x(now_t, target_x)
                    self.filtered_target_y = self.cursor_filter_y(now_t, target_y)

                filt_x = getattr(self, 'filtered_target_x', target_x)
                filt_y = getattr(self, 'filtered_target_y', target_y)

                # Continuous 60 FPS Exponential Interpolation (Lerp)
                # Blends between camera frames without velocity overshoot or snapping back
                dt_frame = max(0.001, min(0.05, now_t - getattr(self, '_last_cursor_update_t', now_t)))
                self._last_cursor_update_t = now_t

                dist_to_target = math.hypot(filt_x - self.cursor_x, filt_y - self.cursor_y)
                # Adaptive lerp rate: fast response when moving, ultra-smooth dampening when aiming
                lerp_speed = 36.0 if dist_to_target > 35.0 else (18.0 if dist_to_target < 10.0 else 25.0)
                alpha = 1.0 - math.exp(-lerp_speed * dt_frame)

                smooth_x = self.cursor_x + (filt_x - self.cursor_x) * alpha
                smooth_y = self.cursor_y + (filt_y - self.cursor_y) * alpha

                # Click / Fist Stabilization:
                if fist_detected:
                    if self.fist_anchor_x is None:
                        self.fist_anchor_x = smooth_x
                        self.fist_anchor_y = smooth_y

                    anchor_dist = math.hypot(smooth_x - self.fist_anchor_x, smooth_y - self.fist_anchor_y)
                    # Hold anchor firmly while clicking; if user intentionally moves (> 28px), follow smoothly
                    if anchor_dist < 28.0:
                        self.cursor_x = self.fist_anchor_x
                        self.cursor_y = self.fist_anchor_y
                    else:
                        self.fist_anchor_x = None
                        self.fist_anchor_y = None
                        self.cursor_x = smooth_x
                        self.cursor_y = smooth_y
                else:
                    self.fist_anchor_x = None
                    self.fist_anchor_y = None
                    self.cursor_x = smooth_x
                    self.cursor_y = smooth_y

                # Clamp cursor within window
                self.cursor_x = max(0.0, min(float(self.w), self.cursor_x))
                self.cursor_y = max(0.0, min(float(self.h), self.cursor_y))
                self.cursor_pos = (int(round(self.cursor_x)), int(round(self.cursor_y)))

                # Update smoothed hand velocity for tracking-loss inertial bridging
                if not was_just_acquired:
                    vel_dt = max(0.016, dt_frame)
                    inst_vx = max(-1600.0, min(1600.0, (self.cursor_x - prev_cx) / vel_dt))
                    inst_vy = max(-1600.0, min(1600.0, (self.cursor_y - prev_cy) / vel_dt))
                    if fist_detected and self.fist_anchor_x is not None:
                        self.hand_vx = 0.0
                        self.hand_vy = 0.0
                    else:
                        self.hand_vx = getattr(self, 'hand_vx', 0.0) * 0.4 + inst_vx * 0.6
                        self.hand_vy = getattr(self, 'hand_vy', 0.0) * 0.4 + inst_vy * 0.6

                # Store last position for grace period
                self.last_cursor_x = self.cursor_x
                self.last_cursor_y = self.cursor_y

                # Deadlock-free gesture & click state machine with temporal persistence / debounce
                if fist_detected:
                    self.fist_missed_frames = 0
                    self.open_consecutive_frames = 0
                    self.last_fist_time = time.time()
                    if self.fist_start_time == 0 and not self.click_ready:
                        self.fist_start_time = time.time()

                    if self.fist_start_time > 0:
                        hold_time = time.time() - self.fist_start_time
                        if hold_time >= self.CLICK_HOLD_TIME and not self.click_ready:
                            self.click_ready = True
                            self.trigger_click()
                    self.current_gesture = "FIST"
                elif open_detected or peace_detected:
                    self.open_consecutive_frames = getattr(self, 'open_consecutive_frames', 0) + 1
                    # If actively charging a fist (before click triggers), require 2 consecutive open-hand frames to confirm release
                    if self.fist_start_time > 0 and not self.click_ready and self.open_consecutive_frames < 2:
                        self.current_gesture = "FIST"
                    else:
                        self.fist_start_time = 0
                        self.click_ready = False
                        self.last_fist_time = 0
                        self.fist_missed_frames = 0
                        self.current_gesture = "PEACE" if peace_detected else "OPEN"
                else:
                    self.open_consecutive_frames = 0
                    self.fist_missed_frames = getattr(self, 'fist_missed_frames', 0) + 1
                    # Debounce grace: allow up to 15 frames (~250ms) of ambiguous frames before canceling fist hold
                    if self.fist_start_time > 0 and self.fist_missed_frames <= 15:
                        self.current_gesture = "FIST"
                    else:
                        self.fist_start_time = 0
                        self.click_ready = False
                        self.last_fist_time = 0
                        self.current_gesture = "OPEN"

                if peace_detected:
                    self.peace_missed_frames = 0
                    if self.peace_start_time == 0:
                        self.peace_start_time = time.time()
                        print("[PEACE] Peace sign detected! Hold to pause/trigger...")

                    hold_time = time.time() - self.peace_start_time
                    if hold_time >= self.CLICK_HOLD_TIME and not getattr(self, 'peace_ready', False):
                        self.peace_ready = True
                        self.peace_start_time = 0
                        # When in active gameplay stage, pop up the universal in-game pause menu!
                        if self.current_screen in ["quarter1", "quarter2", "quarter3", "quarter4", "tutorial"]:
                            active_stage = getattr(self, self.current_screen, None)
                            if active_stage and hasattr(active_stage, 'pause_menu'):
                                active_stage.pause_menu.toggle_pause()
                                print(f"[PAUSE] Toggled in-game pause menu via Peace Sign on {self.current_screen} (is_paused={active_stage.pause_menu.is_paused})")
                        elif self.current_screen in ["stage_select", "stageselect"]:
                            if getattr(self, 'stage_select', None):
                                print("[PEACE] Peace Sign triggered in stage select! Returning to main menu...")
                                self.stage_select.return_to_main_menu()
                        elif self.current_screen == "menu":
                            if not self.popup_state:
                                self.popup_state = "confirm_exit"
                                print(f"[OK] PEACE SIGN TRIGGERED! Popup state: {self.popup_state}")
                else:
                    self.peace_missed_frames = getattr(self, 'peace_missed_frames', 0) + 1
                    if self.peace_missed_frames > 5:
                        self.peace_start_time = 0
                        self.peace_ready = False

            # HAND TRACKING LOSS HANDLING - Inertial bridge during momentary drops, then Grace Period
            else:
                self.tracking_lost_frames = getattr(self, 'tracking_lost_frames', 0) + 1
                if self.tracking_lost_frames <= 30 and getattr(self, 'hand_was_detected', False):
                    # Tracking bridge during 1-30 frames (~500ms) of momentary camera drop/occlusion:
                    # Keep smoothly floating / gentle damping, PRESERVE current gesture and fist hold!
                    decay = max(0.0, 1.0 - (self.tracking_lost_frames * 0.033))
                    self.cursor_x += getattr(self, 'hand_vx', 0.0) * 0.016 * decay
                    self.cursor_y += getattr(self, 'hand_vy', 0.0) * 0.016 * decay
                    self.cursor_x = max(0.0, min(float(self.w), self.cursor_x))
                    self.cursor_y = max(0.0, min(float(self.h), self.cursor_y))
                    self.cursor_pos = (int(round(self.cursor_x)), int(round(self.cursor_y)))
                    self.last_cursor_x = self.cursor_x
                    self.last_cursor_y = self.cursor_y
                    # Maintain current_gesture to prevent HUD strobe/jitter during momentary occlusion
                else:
                    elapsed = time.time() - self.last_hand_time
                    if elapsed < self.HAND_GRACE:
                        # Keep last cursor position
                        self.cursor_pos = (int(self.last_cursor_x), int(self.last_cursor_y))
                        if self.fist_start_time > 0 and elapsed < 0.6:
                            self.current_gesture = "FIST"
                        else:
                            self.current_gesture = "NO HAND (GRACE)"
                    else:
                        self.hand_was_detected = False
                        self.hand_vx = 0.0
                        self.hand_vy = 0.0
                        self.current_gesture = "NO HAND"
                        self.fist_start_time = 0
                        self.peace_start_time = 0
                        self.click_ready = False

                        # DO NOT automatically use mouse! Only activate if physical mouse moved!
                        if getattr(self, 'mouse_active', False):
                            if time.time() - getattr(self, 'last_mouse_move_time', 0.0) <= self.MOUSE_IDLE_TIMEOUT:
                                curr_m = pygame.mouse.get_pos()
                                self.cursor_pos = curr_m
                                self.cursor_x, self.cursor_y = float(curr_m[0]), float(curr_m[1])
                            else:
                                self.mouse_active = False

            # Update GameCursor with newest state
            game_cursor.update(
                self.cursor_pos,
                self.current_gesture,
                self.fist_start_time,
                self.CLICK_HOLD_TIME,
                self.peace_start_time
            )
        except Exception:
            pass

    # ==========================================
    # CLICK HANDLER
    def trigger_click(self, pos=None):
        """Handle click at cursor position"""
        if pos is None:
            pos = self.cursor_pos

        # If pop-up is active, intercept clicks!
        if self.popup_state:
            self.handle_popup_click(pos)
            return

        # Check cloud status badge click (Manual Re-sync / Diagnostic)
        if self.get_cloud_status_geometry().collidepoint(pos):
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.play_sfx("click")
            lock = getattr(self, '_cloud_probe_lock', None)
            if lock is None or not lock.locked():
                threading.Thread(target=self._manual_cloud_probe, daemon=True).start()
            return

        # Route click to active screen if not in menu
        if self.current_screen in ("stage_select", "stageselect") and self.stage_select:
            self.stage_select.trigger_click(pos)
            return
        elif self.current_screen == "student_select" and self.student_select:
            self.student_select.trigger_click(pos)
            return
        elif self.current_screen == "tutorial" and self.tutorial:
            self.tutorial.trigger_click(pos)
            return
        elif self.current_screen == "quarter1" and self.quarter1:
            self.quarter1.trigger_click(pos)
            return
        elif self.current_screen == "quarter2" and self.quarter2:
            self.quarter2.trigger_click(pos)
            return
        elif self.current_screen == "quarter3" and self.quarter3:
            self.quarter3.trigger_click(pos)
            return
        elif self.current_screen == "quarter4" and self.quarter4:
            self.quarter4.trigger_click(pos)
            return
        elif self.current_screen == "leaderboard" and self.leaderboard:
            self.leaderboard.trigger_click(pos)
            return

        # Check update notification pill in footer
        if getattr(self, 'footer_update_rect', None) and self.footer_update_rect.collidepoint(pos):
            self.open_audio_settings()
            return

        # Check dialogue box first
        if self.dialogue_active and self.dialogue_rect.collidepoint(pos):
            print("[DIALOG] Dialogue clicked!")
            self.next_dialogue()
            return

        # Check buttons
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                name = button.text if hasattr(button, 'text') and button.text else "EXIT"
                print(f"[BTN] Button clicked: {name}")
                if button.action:
                    button.action()
                return

        print("[FAIL] Nothing clicked")

    def handle_popup_click(self, pos):
        """Handle clicking inside confirmation and settings pop-ups"""
        if self.popup_state == "audio_settings":
            box_w, box_h = 620, 520
            box_x = (self.w - box_w) // 2
            box_y = (self.h - box_h) // 2
            dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)

            m_minus_rect = pygame.Rect(box_x + 40, box_y + 90, 42, 34)
            m_bar_rect = pygame.Rect(box_x + 92, box_y + 95, 240, 24)
            m_plus_rect = pygame.Rect(box_x + 342, box_y + 90, 42, 34)
            m_mute_rect = pygame.Rect(box_x + 398, box_y + 90, 180, 34)

            s_minus_rect = pygame.Rect(box_x + 40, box_y + 162, 42, 34)
            s_bar_rect = pygame.Rect(box_x + 92, box_y + 167, 240, 24)
            s_plus_rect = pygame.Rect(box_x + 342, box_y + 162, 42, 34)
            s_mute_rect = pygame.Rect(box_x + 398, box_y + 162, 180, 34)

            autostart_toggle_rect = pygame.Rect(box_x + box_w - 180, box_y + 222, 140, 36)

            if m_minus_rect.collidepoint(pos):
                self.audio_manager.set_music_volume(self.audio_manager.music_volume - 0.1)
                self.audio_manager.play_sfx("click")
            elif m_plus_rect.collidepoint(pos):
                self.audio_manager.set_music_volume(self.audio_manager.music_volume + 0.1)
                self.audio_manager.play_sfx("click")
            elif m_bar_rect.collidepoint(pos):
                vol = max(0.0, min(1.0, (pos[0] - m_bar_rect.x) / float(m_bar_rect.width)))
                self.audio_manager.set_music_volume(vol)
                self.audio_manager.play_sfx("click")
            elif m_mute_rect.collidepoint(pos):
                self.audio_manager.toggle_music_mute()
                self.audio_manager.play_sfx("click")

            elif s_minus_rect.collidepoint(pos):
                self.audio_manager.set_sfx_volume(self.audio_manager.sfx_volume - 0.1)
                self.audio_manager.play_sfx("click")
            elif s_plus_rect.collidepoint(pos):
                self.audio_manager.set_sfx_volume(self.audio_manager.sfx_volume + 0.1)
                self.audio_manager.play_sfx("click")
            elif s_bar_rect.collidepoint(pos):
                vol = max(0.0, min(1.0, (pos[0] - s_bar_rect.x) / float(s_bar_rect.width)))
                self.audio_manager.set_sfx_volume(vol)
                self.audio_manager.play_sfx("click")
            elif s_mute_rect.collidepoint(pos):
                self.audio_manager.toggle_sfx_mute()
                self.audio_manager.play_sfx("click")

            elif autostart_toggle_rect.collidepoint(pos):
                from core.autostart_manager import toggle_autostart
                new_state, msg = toggle_autostart()
                self._cached_autostart_enabled = bool(new_state)
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("click")
                self.autostart_status_msg = msg
                self.autostart_msg_timer = pygame.time.get_ticks() + 3500

            # Update Check Button
            elif getattr(self, 'update_check_btn_rect', None) and self.update_check_btn_rect.collidepoint(pos):
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("click")
                self.update_manager.check_for_updates()

            # In-App Download Start Button
            elif getattr(self, 'update_download_btn_rect', None) and self.update_download_btn_rect.collidepoint(pos):
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("click")
                self.update_manager.start_download()

            # In-App Download Cancel Button
            elif getattr(self, 'update_cancel_btn_rect', None) and self.update_cancel_btn_rect.collidepoint(pos):
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("click")
                self.update_manager.cancel_download()

            # In-App Install & Restart Button
            elif getattr(self, 'update_install_btn_rect', None) and self.update_install_btn_rect.collidepoint(pos):
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("success")
                self.update_manager.apply_update()

            # Retry Button
            elif getattr(self, 'update_retry_btn_rect', None) and self.update_retry_btn_rect.collidepoint(pos):
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("click")
                if self.update_manager.installer_download_url:
                    self.update_manager.start_download()
                else:
                    self.update_manager.check_for_updates()

            # Browser Fallback Button
            elif getattr(self, 'update_browser_btn_rect', None) and self.update_browser_btn_rect.collidepoint(pos):
                if hasattr(self, 'audio_manager'):
                    self.audio_manager.play_sfx("click")
                self.update_manager.open_download_page()

            # Bottom Sound Test / Done / Outside Dismiss
            elif getattr(self, 'audio_test_rect', None) and self.audio_test_rect.collidepoint(pos):
                self.audio_manager.play_sfx("success")
            elif getattr(self, 'audio_done_rect', None) and self.audio_done_rect.collidepoint(pos):
                self.audio_manager.play_sfx("click")
                self.popup_state = None
            elif getattr(self, 'audio_dialog_rect', None) and not self.audio_dialog_rect.collidepoint(pos):
                self.audio_manager.play_sfx("click")
                self.popup_state = None
            return

        box_w, box_h = 500, 260
        box_x = (self.w - box_w) // 2
        box_y = (self.h - box_h) // 2
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        btn_w, btn_h = 160, 42
        yes_rect = pygame.Rect(box_x + 60, box_y + 180, btn_w, btn_h)
        no_rect = pygame.Rect(box_x + box_w - 60 - btn_w, box_y + 180, btn_w, btn_h)

        if yes_rect.collidepoint(pos):
            print("[YES] Confirmation pop-up: YES clicked")
            if hasattr(self, 'audio_manager'):
                self.audio_manager.play_sfx("click")
            if self.popup_state == "confirm_exit":
                self.exit_game()
            elif self.popup_state == "confirm_new_activity":
                from db.save_system import delete_student_progress

                # Visual feedback card
                overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                font = getattr(self, 'dialogue_font', self.button_font)
                txt_surf = font.render("Resetting Past Progress & Starting New Game...", True, (255, 255, 255))
                rect = txt_surf.get_rect(center=(self.w // 2, self.h // 2))
                card_rect = rect.inflate(80, 40)
                pygame.draw.rect(self.screen, (15, 23, 42), card_rect, border_radius=12)
                pygame.draw.rect(self.screen, (239, 68, 68), card_rect, 3, border_radius=12)
                self.screen.blit(txt_surf, rect)
                pygame.display.flip()

                # Purge past progress in both game save files and live database
                delete_student_progress(
                    student_id=self.student_id,
                    student_db_id=getattr(self, 'student_db_id', None),
                    main_menu=self
                )
                self.popup_state = None
                
                # Refresh main menu buttons
                self.setup_buttons()
                
                # Start Tutorial for new activity
                print("[TUTORIAL] Starting New Activity: Launching Tutorial Screen...")
                self.current_screen = "tutorial"
                from screens.tutorial import TutorialScreen
                self.tutorial = TutorialScreen(self.screen, self)
            elif self.popup_state == "confirm_menu":
                from db.save_system import show_saving_and_exit
                show_saving_and_exit(self)
        elif no_rect.collidepoint(pos):
            print("[NO] Confirmation pop-up: NO clicked")
            if hasattr(self, 'audio_manager'):
                self.audio_manager.play_sfx("click")
            self.popup_state = None
        elif not dialog_rect.collidepoint(pos):
            # Click outside dialog modal dismisses it
            if hasattr(self, 'audio_manager'):
                self.audio_manager.play_sfx("click")
            self.popup_state = None

    def draw_audio_popup(self):
        """Draw the interactive Game & System Settings modal with Update Checking"""
        # 1. Cached Overlay
        if not hasattr(self, '_popup_dim_overlay') or self._popup_dim_overlay.get_size() != (self.w, self.h):
            self._popup_dim_overlay = pygame.Surface((self.w, self.h))
            if pygame.display.get_surface() is not None:
                try:
                    self._popup_dim_overlay = self._popup_dim_overlay.convert()
                except Exception:
                    pass
            self._popup_dim_overlay.fill((0, 0, 0))
            self._popup_dim_overlay.set_alpha(180)
        self.screen.blit(self._popup_dim_overlay, (0, 0))

        # 2. Centered dialog box (height 520px for updates & system options)
        box_w, box_h = 620, 520
        box_x = (self.w - box_w) // 2
        box_y = (self.h - box_h) // 2
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        self.audio_dialog_rect = dialog_rect

        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (56, 189, 248), dialog_rect, 3, border_radius=14)

        title_font = pygame.font.SysFont("Comic Sans MS", 22, bold=True)
        label_font = pygame.font.SysFont("Comic Sans MS", 15, bold=True)
        btn_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        small_font = pygame.font.SysFont("Comic Sans MS", 12)

        # Title
        title_surf = title_font.render("Game & System Settings", True, (56, 189, 248))
        self.screen.blit(title_surf, (box_x + (box_w - title_surf.get_width()) // 2, box_y + 14))

        # Top Divider
        pygame.draw.line(self.screen, (56, 189, 248), (box_x + 35, box_y + 48), (box_x + box_w - 35, box_y + 48), 2)

        # ---------------- Music Volume Row ----------------
        m_vol = self.audio_manager.music_volume
        m_muted = self.audio_manager.music_muted
        m_pct = int(m_vol * 100)
        m_label_color = (239, 68, 68) if m_muted else (241, 245, 249)
        m_label_text = f"Music Volume: {m_pct}% {'(MUTED)' if m_muted else ''}"
        self.screen.blit(label_font.render(m_label_text, True, m_label_color), (box_x + 40, box_y + 60))

        m_minus_rect = pygame.Rect(box_x + 40, box_y + 88, 42, 32)
        m_bar_rect = pygame.Rect(box_x + 92, box_y + 92, 240, 24)
        m_plus_rect = pygame.Rect(box_x + 342, box_y + 88, 42, 32)
        m_mute_rect = pygame.Rect(box_x + 398, box_y + 88, 180, 32)

        hover_m_minus = m_minus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_m_minus else (30, 41, 59), m_minus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (56, 189, 248), m_minus_rect, 2, border_radius=6)
        txt = btn_font.render("-", True, (255, 255, 255))
        self.screen.blit(txt, (m_minus_rect.centerx - txt.get_width() // 2, m_minus_rect.centery - txt.get_height() // 2))

        pygame.draw.rect(self.screen, (30, 41, 59), m_bar_rect, border_radius=5)
        fill_w = int(m_bar_rect.width * m_vol)
        if fill_w > 0:
            fill_color = (100, 116, 139) if m_muted else (56, 189, 248)
            pygame.draw.rect(self.screen, fill_color, (m_bar_rect.x, m_bar_rect.y, fill_w, m_bar_rect.height), border_radius=5)
        pygame.draw.rect(self.screen, (148, 163, 184), m_bar_rect, 2, border_radius=5)

        hover_m_plus = m_plus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_m_plus else (30, 41, 59), m_plus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (56, 189, 248), m_plus_rect, 2, border_radius=6)
        txt = btn_font.render("+", True, (255, 255, 255))
        self.screen.blit(txt, (m_plus_rect.centerx - txt.get_width() // 2, m_plus_rect.centery - txt.get_height() // 2))

        hover_m_mute = m_mute_rect.collidepoint(self.cursor_pos)
        mute_bg = (239, 68, 68) if m_muted else ((51, 65, 85) if hover_m_mute else (30, 41, 59))
        pygame.draw.rect(self.screen, mute_bg, m_mute_rect, border_radius=6)
        pygame.draw.rect(self.screen, (239, 68, 68) if m_muted else (56, 189, 248), m_mute_rect, 2, border_radius=6)
        txt = btn_font.render("UNMUTE" if m_muted else "MUTE BGM", True, (255, 255, 255))
        self.screen.blit(txt, (m_mute_rect.centerx - txt.get_width() // 2, m_mute_rect.centery - txt.get_height() // 2))

        # ---------------- SFX Volume Row ----------------
        s_vol = self.audio_manager.sfx_volume
        s_muted = self.audio_manager.sfx_muted
        s_pct = int(s_vol * 100)
        s_label_color = (239, 68, 68) if s_muted else (241, 245, 249)
        s_label_text = f"Sound Effects: {s_pct}% {'(MUTED)' if s_muted else ''}"
        self.screen.blit(label_font.render(s_label_text, True, s_label_color), (box_x + 40, box_y + 132))

        s_minus_rect = pygame.Rect(box_x + 40, box_y + 160, 42, 32)
        s_bar_rect = pygame.Rect(box_x + 92, box_y + 164, 240, 24)
        s_plus_rect = pygame.Rect(box_x + 342, box_y + 160, 42, 32)
        s_mute_rect = pygame.Rect(box_x + 398, box_y + 160, 180, 32)

        hover_s_minus = s_minus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_s_minus else (30, 41, 59), s_minus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (34, 197, 94), s_minus_rect, 2, border_radius=6)
        txt = btn_font.render("-", True, (255, 255, 255))
        self.screen.blit(txt, (s_minus_rect.centerx - txt.get_width() // 2, s_minus_rect.centery - txt.get_height() // 2))

        pygame.draw.rect(self.screen, (30, 41, 59), s_bar_rect, border_radius=5)
        fill_w = int(s_bar_rect.width * s_vol)
        if fill_w > 0:
            fill_color = (100, 116, 139) if s_muted else (34, 197, 94)
            pygame.draw.rect(self.screen, fill_color, (s_bar_rect.x, s_bar_rect.y, fill_w, s_bar_rect.height), border_radius=5)
        pygame.draw.rect(self.screen, (148, 163, 184), s_bar_rect, 2, border_radius=5)

        hover_s_plus = s_plus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_s_plus else (30, 41, 59), s_plus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (34, 197, 94), s_plus_rect, 2, border_radius=6)
        txt = btn_font.render("+", True, (255, 255, 255))
        self.screen.blit(txt, (s_plus_rect.centerx - txt.get_width() // 2, s_plus_rect.centery - txt.get_height() // 2))

        hover_s_mute = s_mute_rect.collidepoint(self.cursor_pos)
        mute_bg = (239, 68, 68) if s_muted else ((51, 65, 85) if hover_s_mute else (30, 41, 59))
        pygame.draw.rect(self.screen, mute_bg, s_mute_rect, border_radius=6)
        pygame.draw.rect(self.screen, (239, 68, 68) if s_muted else (34, 197, 94), s_mute_rect, 2, border_radius=6)
        txt = btn_font.render("UNMUTE" if s_muted else "MUTE SFX", True, (255, 255, 255))
        self.screen.blit(txt, (s_mute_rect.centerx - txt.get_width() // 2, s_mute_rect.centery - txt.get_height() // 2))

        # Divider 2
        pygame.draw.line(self.screen, (51, 65, 85), (box_x + 35, box_y + 206), (box_x + box_w - 35, box_y + 206), 1)

        # ---------------- Windows Startup Row ----------------
        if not hasattr(self, '_cached_autostart_supported'):
            from core.autostart_manager import is_autostart_enabled, is_autostart_supported
            self._cached_autostart_supported = is_autostart_supported()
            self._cached_autostart_enabled = is_autostart_enabled() if self._cached_autostart_supported else False
        is_supported = self._cached_autostart_supported
        is_enabled = getattr(self, '_cached_autostart_enabled', False) if is_supported else False

        self.screen.blit(label_font.render("Run on Windows Startup", True, (241, 245, 249)), (box_x + 40, box_y + 218))
        sub_text = "Launch Cognitive Play automatically on boot" if is_supported else "Supported only on Windows"
        self.screen.blit(small_font.render(sub_text, True, (148, 163, 184)), (box_x + 40, box_y + 242))

        autostart_toggle_rect = pygame.Rect(box_x + box_w - 180, box_y + 222, 140, 36)
        hover_toggle = autostart_toggle_rect.collidepoint(self.cursor_pos)

        if not is_supported:
            btn_bg = (51, 65, 85)
            border_col = (100, 116, 139)
            btn_label = "N/A"
        elif is_enabled:
            btn_bg = (16, 185, 129) if not hover_toggle else (5, 150, 105)
            border_col = (110, 231, 183)
            btn_label = "[ON] ENABLED"
        else:
            btn_bg = (51, 65, 85) if not hover_toggle else (71, 85, 105)
            border_col = (148, 163, 184)
            btn_label = "[OFF] DISABLED"

        pygame.draw.rect(self.screen, btn_bg, autostart_toggle_rect, border_radius=8)
        pygame.draw.rect(self.screen, border_col, autostart_toggle_rect, 2, border_radius=8)
        t_surf = btn_font.render(btn_label, True, (255, 255, 255))
        self.screen.blit(t_surf, (autostart_toggle_rect.centerx - t_surf.get_width() // 2, autostart_toggle_rect.centery - t_surf.get_height() // 2))

        # Divider 3
        pygame.draw.line(self.screen, (51, 65, 85), (box_x + 35, box_y + 274), (box_x + box_w - 35, box_y + 274), 1)

        # ---------------- Game Version & Updates Row ----------------
        self.screen.blit(label_font.render("Game Version & Updates", True, (241, 245, 249)), (box_x + 40, box_y + 286))
        ver_sub_text = f"Installed: v{APP_VERSION}  |  Official DepEd Math Release"
        self.screen.blit(small_font.render(ver_sub_text, True, (148, 163, 184)), (box_x + 40, box_y + 310))

        # Reset frame interactive update button rects
        self.update_check_btn_rect = None
        self.update_download_btn_rect = None
        self.update_cancel_btn_rect = None
        self.update_browser_btn_rect = None
        self.update_install_btn_rect = None
        self.update_retry_btn_rect = None

        # Check for Updates Button
        update_btn_rect = pygame.Rect(box_x + box_w - 180, box_y + 288, 140, 36)
        self.update_check_btn_rect = update_btn_rect
        hover_update = update_btn_rect.collidepoint(self.cursor_pos)
        is_chk = self.update_manager.is_checking()
        is_dl = self.update_manager.is_downloading()

        if is_chk or is_dl:
            u_bg = (51, 65, 85)
            u_border = (148, 163, 184)
            u_label = "Checking..." if is_chk else "Busy"
        else:
            u_bg = (14, 116, 144) if hover_update else (8, 145, 178)
            u_border = (103, 232, 249)
            u_label = "Check Updates"

        pygame.draw.rect(self.screen, u_bg, update_btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, u_border, update_btn_rect, 2, border_radius=8)
        u_surf = btn_font.render(u_label, True, (255, 255, 255))
        self.screen.blit(u_surf, (update_btn_rect.centerx - u_surf.get_width() // 2, update_btn_rect.centery - u_surf.get_height() // 2))

        # Update Status & Action Handling
        st = self.update_manager.state
        if st == UpdateState.IDLE:
            st_text = "Click to verify if a newer game version is available online."
            st_col = (148, 163, 184)
            self.screen.blit(small_font.render(st_text, True, st_col), (box_x + 40, box_y + 338))

        elif st == UpdateState.CHECKING:
            dots = "." * ((pygame.time.get_ticks() // 350) % 4)
            st_text = f"Connecting to update server{dots}"
            st_col = (250, 204, 21)
            self.screen.blit(small_font.render(st_text, True, st_col), (box_x + 40, box_y + 338))

        elif st == UpdateState.UP_TO_DATE:
            st_text = f"✓ You are running the latest version (v{APP_VERSION})!"
            st_col = (34, 197, 94)
            self.screen.blit(small_font.render(st_text, True, st_col), (box_x + 40, box_y + 338))

        elif st == UpdateState.UPDATE_AVAILABLE:
            st_text = f"★ New Version Available: v{self.update_manager.latest_version}!"
            self.screen.blit(label_font.render(st_text, True, (250, 204, 21)), (box_x + 40, box_y + 332))
            sub_text = "Download directly in-app or view on releases page:"
            self.screen.blit(small_font.render(sub_text, True, (148, 163, 184)), (box_x + 40, box_y + 354))

            # Primary: In-App Download Button
            inapp_rect = pygame.Rect(box_x + box_w - 270, box_y + 332, 145, 34)
            self.update_download_btn_rect = inapp_rect
            hover_inapp = inapp_rect.collidepoint(self.cursor_pos)
            inapp_bg = (16, 185, 129) if hover_inapp else (5, 150, 105)
            pygame.draw.rect(self.screen, inapp_bg, inapp_rect, border_radius=8)
            pygame.draw.rect(self.screen, (110, 231, 183), inapp_rect, 2, border_radius=8)
            inapp_txt = btn_font.render("Update In-App", True, (255, 255, 255))
            self.screen.blit(inapp_txt, (inapp_rect.centerx - inapp_txt.get_width() // 2, inapp_rect.centery - inapp_txt.get_height() // 2))

            # Secondary: Web Browser Button
            web_rect = pygame.Rect(box_x + box_w - 115, box_y + 332, 75, 34)
            self.update_browser_btn_rect = web_rect
            hover_web = web_rect.collidepoint(self.cursor_pos)
            web_bg = (51, 65, 85) if hover_web else (30, 41, 59)
            pygame.draw.rect(self.screen, web_bg, web_rect, border_radius=8)
            pygame.draw.rect(self.screen, (148, 163, 184), web_rect, 2, border_radius=8)
            web_txt = btn_font.render("Web ↗", True, (255, 255, 255))
            self.screen.blit(web_txt, (web_rect.centerx - web_txt.get_width() // 2, web_rect.centery - web_txt.get_height() // 2))

        elif st == UpdateState.DOWNLOADING:
            stats = self.update_manager.get_download_stats()
            st_text = f"Downloading update: {stats['pct']}% ({stats['mb_done']:.1f} MB / {stats['mb_total']:.1f} MB) • {stats['speed_str']}"
            self.screen.blit(small_font.render(st_text, True, (56, 189, 248)), (box_x + 40, box_y + 330))

            # Progress Bar
            bar_rect = pygame.Rect(box_x + 40, box_y + 352, box_w - 170, 16)
            pygame.draw.rect(self.screen, (30, 41, 59), bar_rect, border_radius=8)
            fill_w = max(4, int(bar_rect.width * stats['progress'])) if stats['progress'] > 0 else 0
            if fill_w > 0:
                pygame.draw.rect(self.screen, (16, 185, 129), (bar_rect.x, bar_rect.y, fill_w, bar_rect.height), border_radius=8)
            pygame.draw.rect(self.screen, (56, 189, 248), bar_rect, 2, border_radius=8)

            # Cancel Button
            cancel_rect = pygame.Rect(box_x + box_w - 115, box_y + 344, 75, 28)
            self.update_cancel_btn_rect = cancel_rect
            hover_cancel = cancel_rect.collidepoint(self.cursor_pos)
            c_bg = (185, 28, 28) if hover_cancel else (127, 29, 29)
            pygame.draw.rect(self.screen, c_bg, cancel_rect, border_radius=6)
            pygame.draw.rect(self.screen, (248, 113, 113), cancel_rect, 1, border_radius=6)
            c_txt = small_font.render("Cancel", True, (255, 255, 255))
            self.screen.blit(c_txt, (cancel_rect.centerx - c_txt.get_width() // 2, cancel_rect.centery - c_txt.get_height() // 2))

        elif st == UpdateState.READY_TO_INSTALL:
            st_text = f"✓ Update v{self.update_manager.latest_version} ready to install!"
            self.screen.blit(label_font.render(st_text, True, (34, 197, 94)), (box_x + 40, box_y + 330))
            sub_text = "Click to launch installer and restart the game cleanly:"
            self.screen.blit(small_font.render(sub_text, True, (148, 163, 184)), (box_x + 40, box_y + 354))

            install_rect = pygame.Rect(box_x + box_w - 240, box_y + 330, 200, 38)
            self.update_install_btn_rect = install_rect
            hover_install = install_rect.collidepoint(self.cursor_pos)
            inst_bg = (16, 185, 129) if hover_install else (5, 150, 105)
            pygame.draw.rect(self.screen, inst_bg, install_rect, border_radius=8)
            pygame.draw.rect(self.screen, (110, 231, 183), install_rect, 2, border_radius=8)
            inst_txt = btn_font.render("🚀 Install & Restart", True, (255, 255, 255))
            self.screen.blit(inst_txt, (install_rect.centerx - inst_txt.get_width() // 2, install_rect.centery - inst_txt.get_height() // 2))

        elif st == UpdateState.ERROR:
            err_reason = self.update_manager.download_error or self.update_manager.error_message or "Offline"
            st_text = f"Update error: {err_reason}"
            self.screen.blit(small_font.render(st_text, True, (244, 63, 94)), (box_x + 40, box_y + 330))
            sub_text = "You can retry or download directly from the website:"
            self.screen.blit(small_font.render(sub_text, True, (148, 163, 184)), (box_x + 40, box_y + 354))

            # Retry Button
            retry_rect = pygame.Rect(box_x + box_w - 220, box_y + 332, 95, 34)
            self.update_retry_btn_rect = retry_rect
            hover_retry = retry_rect.collidepoint(self.cursor_pos)
            ret_bg = (14, 116, 144) if hover_retry else (8, 145, 178)
            pygame.draw.rect(self.screen, ret_bg, retry_rect, border_radius=8)
            pygame.draw.rect(self.screen, (103, 232, 249), retry_rect, 2, border_radius=8)
            ret_txt = btn_font.render("Retry", True, (255, 255, 255))
            self.screen.blit(ret_txt, (retry_rect.centerx - ret_txt.get_width() // 2, retry_rect.centery - ret_txt.get_height() // 2))

            # Web Browser Button
            web_rect = pygame.Rect(box_x + box_w - 115, box_y + 332, 75, 34)
            self.update_browser_btn_rect = web_rect
            hover_web = web_rect.collidepoint(self.cursor_pos)
            web_bg = (51, 65, 85) if hover_web else (30, 41, 59)
            pygame.draw.rect(self.screen, web_bg, web_rect, border_radius=8)
            pygame.draw.rect(self.screen, (148, 163, 184), web_rect, 2, border_radius=8)
            web_txt = btn_font.render("Web ↗", True, (255, 255, 255))
            self.screen.blit(web_txt, (web_rect.centerx - web_txt.get_width() // 2, web_rect.centery - web_txt.get_height() // 2))

        # Bottom hint / hotkey info
        now = pygame.time.get_ticks()
        if hasattr(self, 'autostart_status_msg') and getattr(self, 'autostart_msg_timer', 0) > now:
            fb_surf = small_font.render(self.autostart_status_msg, True, (250, 204, 21))
            self.screen.blit(fb_surf, (box_x + (box_w - fb_surf.get_width()) // 2, box_y + 400))
        else:
            hint_surf = small_font.render("Hotkey: [M] Mute  |  [ [ ] / [ ] ] Volume  |  [F] Fullscreen  |  [F12 / PrtScn] Screenshot", True, (148, 163, 184))
            self.screen.blit(hint_surf, (box_x + (box_w - hint_surf.get_width()) // 2, box_y + 400))

        # ---------------- Bottom Action Buttons ----------------
        test_rect = pygame.Rect(box_x + 40, box_y + 445, 240, 46)
        done_rect = pygame.Rect(box_x + box_w - 280, box_y + 445, 240, 46)
        self.audio_test_rect = test_rect
        self.audio_done_rect = done_rect

        hover_test = test_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (59, 130, 246) if hover_test else (37, 99, 235), test_rect, border_radius=8)
        pygame.draw.rect(self.screen, (147, 197, 253), test_rect, 2, border_radius=8)
        t_txt = btn_font.render("Test Sound", True, (255, 255, 255))
        self.screen.blit(t_txt, (test_rect.centerx - t_txt.get_width() // 2, test_rect.centery - t_txt.get_height() // 2))

        hover_done = done_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (34, 197, 94) if hover_done else (22, 163, 74), done_rect, border_radius=8)
        pygame.draw.rect(self.screen, (134, 239, 172), done_rect, 2, border_radius=8)
        d_txt = btn_font.render("Close / Done", True, (255, 255, 255))
        self.screen.blit(d_txt, (done_rect.centerx - d_txt.get_width() // 2, done_rect.centery - d_txt.get_height() // 2))
    def draw_popup(self):
        """Draw confirmation pop-up or audio settings modal"""
        if not self.popup_state:
            return

        if self.popup_state == "audio_settings":
            self.draw_audio_popup()
            return

        # 1. Semi-transparent full-screen overlay (cached)
        if not hasattr(self, '_popup_dim_overlay') or self._popup_dim_overlay.get_size() != (self.w, self.h):
            self._popup_dim_overlay = pygame.Surface((self.w, self.h))
            if pygame.display.get_surface() is not None:
                try:
                    self._popup_dim_overlay = self._popup_dim_overlay.convert()
                except Exception:
                    pass
            self._popup_dim_overlay.fill((0, 0, 0))
            self._popup_dim_overlay.set_alpha(180)
        self.screen.blit(self._popup_dim_overlay, (0, 0))

        # 2. Centered dialog box
        box_w, box_h = 500, 260
        box_x = (self.w - box_w) // 2
        box_y = (self.h - box_h) // 2
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        
        # Slate background
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=12)
        # Gold/Yellow border
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=12)

        # 3. Text
        title_font = pygame.font.SysFont("Comic Sans MS", 24, bold=True)
        text_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)

        if self.popup_state == "confirm_exit":
            title_text = "Quit Game"
            body_text1 = "Are you sure you want to quit?"
            body_text2 = ""
        elif self.popup_state == "confirm_new_activity":
            title_text = "Start New Activity"
            body_text1 = "Are you sure to Start a new Activity?"
            body_text2 = "This will delete past progress in game and database."
        else:
            title_text = "Return to Menu"
            body_text1 = "Are you sure you want to"
            body_text2 = "return to the main menu?"

        # Draw Title
        title_surf = title_font.render(title_text, True, (218, 165, 32))
        self.screen.blit(title_surf, (box_x + (box_w - title_surf.get_width()) // 2, box_y + 30))

        # Divider line
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 40, box_y + 75), (box_x + box_w - 40, box_y + 75), 2)

        # Draw Body text
        body_surf1 = text_font.render(body_text1, True, (241, 245, 249))
        if body_text2:
            body_surf2 = text_font.render(body_text2, True, (241, 245, 249))
            self.screen.blit(body_surf1, (box_x + (box_w - body_surf1.get_width()) // 2, box_y + 95))
            self.screen.blit(body_surf2, (box_x + (box_w - body_surf2.get_width()) // 2, box_y + 125))
        else:
            self.screen.blit(body_surf1, (box_x + (box_w - body_surf1.get_width()) // 2, box_y + 110))

        # 4. Buttons
        btn_w, btn_h = 160, 42
        yes_rect = pygame.Rect(box_x + 60, box_y + 180, btn_w, btn_h)
        no_rect = pygame.Rect(box_x + box_w - 60 - btn_w, box_y + 180, btn_w, btn_h)

        # Yes button hover & draw
        yes_hover = yes_rect.collidepoint(self.cursor_pos)
        yes_bg = (239, 68, 68) if yes_hover else (30, 41, 59) # Red on hover, dark slate on idle
        yes_fg = (255, 255, 255) if yes_hover else (241, 245, 249)
        pygame.draw.rect(self.screen, yes_bg, yes_rect, border_radius=6)
        pygame.draw.rect(self.screen, (239, 68, 68), yes_rect, 2, border_radius=6)
        
        btn_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
        yes_label = "Yes, quit" if self.popup_state == "confirm_exit" else ("Yes, restart" if self.popup_state == "confirm_new_activity" else "Yes, return")
        yes_text_surf = btn_font.render(yes_label, True, yes_fg)
        self.screen.blit(yes_text_surf, (yes_rect.x + (btn_w - yes_text_surf.get_width()) // 2, yes_rect.y + (btn_h - yes_text_surf.get_height()) // 2))

        # No button hover & draw
        no_hover = no_rect.collidepoint(self.cursor_pos)
        no_bg = (34, 197, 94) if no_hover else (30, 41, 59) # Green on hover, dark slate on idle
        no_fg = (255, 255, 255) if no_hover else (241, 245, 249)
        pygame.draw.rect(self.screen, no_bg, no_rect, border_radius=6)
        pygame.draw.rect(self.screen, (34, 197, 94), no_rect, 2, border_radius=6)
        
        no_text_surf = btn_font.render("No, cancel", True, no_fg)
        self.screen.blit(no_text_surf, (no_rect.x + (btn_w - no_text_surf.get_width()) // 2, no_rect.y + (btn_h - no_text_surf.get_height()) // 2))

    def next_dialogue(self):
        """Go to next dialogue line"""
        self.current_line += 1
        if self.current_line >= len(self.dialogue_lines):
            self.dialogue_active = False
            print("[OK] Dialogue finished!")
        else:
            print(f"[BOOK] Next: {self.dialogue_lines[self.current_line]}")

    # ==========================================
    # BUTTON ACTIONS
    # ==========================================

    def setup_buttons(self):
        """Set up main menu buttons dynamically based on student save progress."""
        from db.save_system import check_save_exists
        
        bw = 440
        bh = 58
        gap = 14
        exit_btn_path = os.path.join("assets", "images", "exitbutton.png")
        
        has_save = False
        if self.selected_student and self.student_id:
            try:
                from db.save_system import load_student_progress
                save_data = load_student_progress(self.student_id)
                if save_data:
                    q_data = save_data.get("completed_quarters", {})
                    completed_count = sum(1 for q, d in q_data.items() if isinstance(d, dict) and d.get("completed"))
                    self.selected_student["progress"] = int((completed_count / 4.0) * 100)
                    self.selected_student["score"] = sum(d.get("score", 0) for q, d in q_data.items() if isinstance(d, dict))
            except Exception:
                pass
            has_save = check_save_exists(self.student_id)
            
        # Exit button is always present
        self.exit_btn = Button(
            (30, 30, 200, 70),
            text="",
            font=self.button_font,
            bg_color=None,
            text_color=(255, 255, 255),
            action=self.confirm_exit_game,
            image_path=exit_btn_path
        )
        
        # Settings / Sound button on top right
        sound_btn_w = 196
        sound_btn_h = 34
        sound_btn_x = self.w - sound_btn_w - 20
        sound_btn_y = 22
        is_muted = self.audio_manager.music_muted and self.audio_manager.sfx_muted
        sound_text = "MUTED" if is_muted else f"{int(self.audio_manager.music_volume * 100)}%"
        sound_btn_font = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.sound_btn = Button(
            (sound_btn_x, sound_btn_y, sound_btn_w, sound_btn_h),
            text=f"SETTINGS ({sound_text})",
            font=sound_btn_font,
            bg_color=(30, 41, 59),
            text_color=(255, 215, 0) if not is_muted else (239, 68, 68),
            action=self.open_audio_settings
        )

        select_btn_text = "CHANGE STUDENT" if self.selected_student else "SELECT STUDENT"

        if has_save:
            # Case: Selected student has existing save progress -> 5 vertical buttons
            total_height = (bh * 5) + (gap * 4)
            start_y = (self.h // 2) - (total_height // 2)
            
            self.select_student_btn = Button(
                (self.w // 2 - bw // 2, start_y, bw, bh),
                text=select_btn_text,
                font=self.button_font,
                bg_color=(255, 215, 0),
                text_color=(0, 0, 0),
                action=self.select_student,
                image_path=None
            )
            
            self.continue_activity_btn = Button(
                (self.w // 2 - bw // 2, start_y + bh + gap, bw, bh),
                text="CONTINUE ACTIVITY",
                font=self.button_font,
                bg_color=(46, 204, 113),
                text_color=(255, 255, 255),
                action=self.continue_activity,
                image_path=None
            )
            
            self.start_new_activity_btn = Button(
                (self.w // 2 - bw // 2, start_y + (bh + gap) * 2, bw, bh),
                text="START NEW ACTIVITY",
                font=self.button_font,
                bg_color=(231, 76, 60),
                text_color=(255, 255, 255),
                action=self.confirm_start_new_activity,
                image_path=None
            )

            self.leaderboard_btn = Button(
                (self.w // 2 - bw // 2, start_y + (bh + gap) * 3, bw, bh),
                text="LEADERBOARD",
                font=self.button_font,
                bg_color=(245, 158, 11),
                text_color=(15, 23, 42),
                action=self.show_leaderboard,
                image_path=None
            )

            self.settings_btn = Button(
                (self.w // 2 - bw // 2, start_y + (bh + gap) * 4, bw, bh),
                text="SETTINGS",
                font=self.button_font,
                bg_color=(59, 130, 246),
                text_color=(255, 255, 255),
                action=self.open_audio_settings,
                image_path=None
            )
            
            self.buttons = [self.select_student_btn, self.continue_activity_btn, self.start_new_activity_btn, self.leaderboard_btn, self.settings_btn, self.exit_btn, self.sound_btn]
        else:
            # Case: No saved progress or no student selected -> 4 vertical buttons
            total_height = (bh * 4) + (gap * 3)
            start_y = (self.h // 2) - (total_height // 2)
            
            self.select_student_btn = Button(
                (self.w // 2 - bw // 2, start_y, bw, bh),
                text=select_btn_text,
                font=self.button_font,
                bg_color=(255, 215, 0),
                text_color=(0, 0, 0),
                action=self.select_student,
                image_path=None
            )
            
            self.start_activity_btn = Button(
                (self.w // 2 - bw // 2, start_y + bh + gap, bw, bh),
                text="START ACTIVITY",
                font=self.button_font,
                bg_color=(46, 204, 113),
                text_color=(255, 255, 255),
                action=self.start_activity,
                image_path=None
            )

            self.leaderboard_btn = Button(
                (self.w // 2 - bw // 2, start_y + (bh + gap) * 2, bw, bh),
                text="LEADERBOARD",
                font=self.button_font,
                bg_color=(245, 158, 11),
                text_color=(15, 23, 42),
                action=self.show_leaderboard,
                image_path=None
            )

            self.settings_btn = Button(
                (self.w // 2 - bw // 2, start_y + (bh + gap) * 3, bw, bh),
                text="SETTINGS",
                font=self.button_font,
                bg_color=(59, 130, 246),
                text_color=(255, 255, 255),
                action=self.open_audio_settings,
                image_path=None
            )
            
            self.buttons = [self.select_student_btn, self.start_activity_btn, self.leaderboard_btn, self.settings_btn, self.exit_btn, self.sound_btn]

    def open_audio_settings(self):
        self.audio_manager.play_sfx("click")
        try:
            from core.autostart_manager import is_autostart_enabled, is_autostart_supported
            self._cached_autostart_supported = is_autostart_supported()
            self._cached_autostart_enabled = is_autostart_enabled() if self._cached_autostart_supported else False
        except Exception:
            self._cached_autostart_supported = False
            self._cached_autostart_enabled = False
        self.popup_state = "audio_settings"

    open_settings = open_audio_settings

    def show_leaderboard(self):
        print("[TROPHY] LEADERBOARD clicked! Loading Hall of Fame rankings...")
        self.fist_start_time = 0
        self.click_ready = True
        self.current_screen = "leaderboard"
        from screens.leaderboard import LeaderboardScreen
        self.leaderboard = LeaderboardScreen(self.screen, self)

    def select_student(self):
        print(f"[DATA] SELECT STUDENT clicked!")
        self.fist_start_time = 0
        self.click_ready = True
        self.current_screen = "student_select"
        from screens.studentselect import StudentSelect
        self.student_select = StudentSelect(self.screen, self)

    def start_activity(self):
        print(f"[GAME] START ACTIVITY clicked!")
        self.fist_start_time = 0
        self.click_ready = False
        if not self.selected_student:
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.play_sfx("wrong")
            self.show_no_student_message = True
            self.no_student_timer = pygame.time.get_ticks() + 2000
            return

        if hasattr(self, 'audio_manager') and self.audio_manager:
            self.audio_manager.play_sfx("click")

        from db.save_system import is_tutorial_completed, delete_student_progress
        # Fresh activity start: purge any leftover stale database/sync records for clean session
        delete_student_progress(
            student_id=self.student_id,
            student_db_id=getattr(self, 'student_db_id', None),
            main_menu=self
        )

        if not is_tutorial_completed(self.student_id):
            print("[TUTORIAL] New player detected! Launching Tutorial Screen...")
            self.current_screen = "tutorial"
            from screens.tutorial import TutorialScreen
            self.tutorial = TutorialScreen(self.screen, self)
            return

        self.current_screen = "stage_select"
        from screens.stageselect import StageSelect
        self.stage_select = StageSelect(self.screen, self)

    def continue_activity(self):
        print("[GAME] CONTINUE ACTIVITY clicked!")
        self.fist_start_time = 0
        self.click_ready = False
        if not self.selected_student:
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.play_sfx("wrong")
            self.show_no_student_message = True
            self.no_student_timer = pygame.time.get_ticks() + 2000
            return

        if hasattr(self, 'audio_manager') and self.audio_manager:
            self.audio_manager.play_sfx("click")
            
        from db.save_system import load_student_progress, apply_student_progress
        save_data = load_student_progress(self.student_id)
        if save_data:
            apply_student_progress(self, save_data)
        else:
            print("[WARN] Save progress not found, starting new activity instead.")
            self.start_activity()

    def confirm_start_new_activity(self):
        print("[REFRESH] START NEW ACTIVITY clicked! Requesting confirmation popup...")
        if not self.selected_student:
            if hasattr(self, 'audio_manager') and self.audio_manager:
                self.audio_manager.play_sfx("wrong")
            self.show_no_student_message = True
            self.no_student_timer = pygame.time.get_ticks() + 2000
            return
        if hasattr(self, 'audio_manager') and self.audio_manager:
            self.audio_manager.play_sfx("click")
        self.popup_state = "confirm_new_activity"

    def confirm_exit_game(self):
        print("[DOOR] ESC / EXIT clicked! Requesting 'Are you sure you want to quit?' confirmation popup...")
        if hasattr(self, 'audio_manager'):
            self.audio_manager.play_sfx("click")
        self.popup_state = "confirm_exit"

    def exit_game(self):
        print("[DOOR] EXIT clicked!")
        self.camera_running = False
        self.cloud_monitor_running = False
        from db.save_system import save_student_progress
        save_student_progress(self)
        
        if self.stage_select:
            self.stage_select.cleanup()
        if self.quarter1:
            self.quarter1.cleanup()
        if self.quarter2:
            self.quarter2.cleanup()
        if self.quarter3:
            self.quarter3.cleanup()
        if self.quarter4:
            self.quarter4.cleanup()
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        cv2.destroyAllWindows()
        pygame.quit()
        raise SystemExit

    # ==========================================
    # UPDATE
    # ==========================================

    def update(self):
        # Sync background music dynamically with active screen/quarter
        if self.current_screen != getattr(self, '_active_audio_screen', None):
            self._active_audio_screen = self.current_screen
            self.audio_manager.play_scene_music(self.current_screen)

        if self.current_screen == "menu":
            now_save_t = time.time()
            cur_sid = self.student_id if self.selected_student else None
            if (cur_sid != getattr(self, '_last_checked_save_sid', object())) or (now_save_t - getattr(self, '_last_save_check_t', 0.0) > 1.5):
                from db.save_system import check_save_exists
                self._last_checked_save_sid = cur_sid
                self._last_save_check_t = now_save_t
                curr_has_save = check_save_exists(cur_sid) if cur_sid else False
                if getattr(self, '_last_has_save_state', None) != curr_has_save:
                    self._last_has_save_state = curr_has_save
                    self.setup_buttons()

            self.update_gesture()
            if not self.popup_state:
                # Update sound button dynamic text
                if getattr(self, 'sound_btn', None):
                    is_muted = self.audio_manager.music_muted and self.audio_manager.sfx_muted
                    sound_text = "MUTED" if is_muted else f"{int(self.audio_manager.music_volume * 100)}%"
                    self.sound_btn.text = f"SETTINGS ({sound_text})"
                    self.sound_btn.text_color = (255, 215, 0) if not is_muted else (239, 68, 68)

                # Update button hover states (only when hand or active mouse is present)
                is_cursor_active = (self.current_gesture in ["FIST", "OPEN", "PEACE", "NO HAND (GRACE)"]) or getattr(self, 'mouse_active', False)
                for b in self.buttons:
                    b.hovered = is_cursor_active and b.rect.collidepoint(self.cursor_pos)

        elif self.current_screen in ["stage_select", "stageselect"] and self.stage_select:
            self.update_gesture()
            if self.stage_select:
                self.stage_select.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture,
                    getattr(self, 'peace_start_time', 0)
                )
                if not self.popup_state and self.stage_select:
                    self.stage_select.update()

        elif self.current_screen == "student_select" and self.student_select:
            self.update_gesture()
            if self.student_select:
                self.student_select.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.student_select:
                    self.student_select.update()

        elif self.current_screen == "tutorial" and self.tutorial:
            self.update_gesture()
            if self.tutorial:
                self.tutorial.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.tutorial:
                    self.tutorial.update()

        elif self.current_screen == "quarter1" and self.quarter1:
            self.update_gesture()
            if self.quarter1:
                self.quarter1.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.quarter1:
                    self.quarter1.update()

        elif self.current_screen == "quarter2" and self.quarter2:
            self.update_gesture()
            if self.quarter2:
                self.quarter2.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.quarter2:
                    self.quarter2.update()

        elif self.current_screen == "quarter3" and self.quarter3:
            self.update_gesture()
            if self.quarter3:
                self.quarter3.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.quarter3:
                    self.quarter3.update()

        elif self.current_screen == "quarter4" and self.quarter4:
            self.update_gesture()
            if self.quarter4:
                self.quarter4.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.quarter4:
                    self.quarter4.update()

        elif self.current_screen == "leaderboard" and self.leaderboard:
            self.update_gesture()
            if self.leaderboard:
                self.leaderboard.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state and self.leaderboard:
                    self.leaderboard.update()

    def handle_event(self, event):
        # Global audio & camera hotkeys (bypass when typing text input in active screens)
        if event.type == pygame.KEYDOWN:
            _typing_active = (
                (self.current_screen == "quarter3" and getattr(self, "quarter3", None) is not None
                 and getattr(self.quarter3, "quiz_state", 0) == 1
                 and getattr(self.quarter3, "q_type", "") == "identification")
                or (self.current_screen == "student_select" and getattr(self, "student_select", None) is not None
                    and getattr(self.student_select, "search_active", False))
            )
            if not _typing_active:
                if event.key == pygame.K_m:
                    self.audio_manager.toggle_master_mute()
                    return
                elif event.key == pygame.K_LEFTBRACKET:
                    self.audio_manager.set_music_volume(self.audio_manager.music_volume - 0.1)
                    return
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.audio_manager.set_music_volume(self.audio_manager.music_volume + 0.1)
                    return
                elif event.key == pygame.K_c and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    self.show_camera_overlay = not getattr(self, 'show_camera_overlay', False)
                    return

        # Always synchronize mouse coordinates on hardware mouse motion and clicks
        if event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
            if event.type == pygame.MOUSEBUTTONDOWN or (hasattr(event, 'rel') and (event.rel[0] != 0 or event.rel[1] != 0)):
                self.mouse_active = True
                self.last_mouse_move_time = time.time()
                self.last_mouse_pos = event.pos
                if self.current_gesture == "NO HAND":
                    self.cursor_pos = event.pos
                    self.cursor_x, self.cursor_y = float(event.pos[0]), float(event.pos[1])

        # If popup is active, intercept clicks and key events!
        if self.popup_state:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.cursor_pos = event.pos
                self.handle_popup_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.cursor_pos = event.pos
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    if self.popup_state == "confirm_exit":
                        self.exit_game()
                    elif self.popup_state == "confirm_new_activity":
                        box_w, box_h = 500, 260
                        box_x = (self.w - box_w) // 2
                        box_y = (self.h - box_h) // 2
                        self.handle_popup_click((box_x + 80, box_y + 195))
                    elif self.popup_state == "confirm_menu":
                        from db.save_system import show_saving_and_exit
                        show_saving_and_exit(self)
                    else:
                        self.handle_popup_click(self.cursor_pos)
                elif event.key == pygame.K_ESCAPE:
                    self.popup_state = None
                    if hasattr(self, 'audio_manager'):
                        self.audio_manager.play_sfx("click")
                elif event.key == pygame.K_y:
                    if self.popup_state == "confirm_exit":
                        self.exit_game()
                    elif self.popup_state == "confirm_new_activity":
                        box_w, box_h = 500, 260
                        box_x = (self.w - box_w) // 2
                        box_y = (self.h - box_h) // 2
                        self.handle_popup_click((box_x + 80, box_y + 195))
                elif event.key == pygame.K_n:
                    self.popup_state = None
                    if hasattr(self, 'audio_manager'):
                        self.audio_manager.play_sfx("click")
            return

        if self.current_screen == "menu":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.cursor_pos = event.pos
                self.trigger_click()
            elif event.type == pygame.MOUSEMOTION:
                self.cursor_pos = event.pos
                for b in self.buttons:
                    b.hovered = b.rect.collidepoint(self.cursor_pos)
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.trigger_click()
                elif event.key == pygame.K_ESCAPE:
                    self.confirm_exit_game()
                elif event.key in [pygame.K_u, pygame.K_F8, pygame.K_F9] or (event.key == pygame.K_b and bool(pygame.key.get_mods() & (pygame.KMOD_CTRL | pygame.KMOD_SHIFT))):
                    if self.selected_student:
                        current_lifted = self.last_stage_select_data.get("barriers_lifted", False)
                        self.last_stage_select_data["barriers_lifted"] = not current_lifted
                        if not current_lifted:
                            print("[MAIN MENU CHEAT] Unlock All Stages shortcut activated: All Quarters (1-4) Unlocked!")
                            if hasattr(self, 'audio_manager') and self.audio_manager:
                                self.audio_manager.play_sfx("success")
                        else:
                            print("[MAIN MENU CHEAT] Unlock shortcut toggled off: Barriers & Progression Restored!")
                            if hasattr(self, 'audio_manager') and self.audio_manager:
                                self.audio_manager.play_sfx("snap")
        elif self.current_screen in ("stage_select", "stageselect") and self.stage_select:
            result = self.stage_select.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.stage_select = None
        elif self.current_screen == "student_select" and self.student_select:
            result = self.student_select.handle_event(event)
            if result in ["back", "select"]:
                self.current_screen = "menu"
                self.student_select = None
        elif self.current_screen == "tutorial" and self.tutorial:
            result = self.tutorial.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.tutorial = None
        elif self.current_screen == "quarter1" and self.quarter1:
            result = self.quarter1.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.quarter1 = None
        elif self.current_screen == "quarter2" and self.quarter2:
            result = self.quarter2.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.quarter2 = None
        elif self.current_screen == "quarter3" and self.quarter3:
            result = self.quarter3.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.quarter3 = None
        elif self.current_screen == "quarter4" and self.quarter4:
            result = self.quarter4.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.quarter4 = None
        elif self.current_screen == "leaderboard" and self.leaderboard:
            result = self.leaderboard.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.leaderboard = None
                self.setup_buttons()

    # ==========================================
    # DRAW
    # ==========================================

    def draw_selected_student_card(self):
        """Renders a sleek, modern glassmorphic profile card displaying only the active selected student.
        If no student is selected, nothing is rendered.
        Dynamically positioned in the exact vertical middle between the Cognitive Maze title and the buttons."""
        if not self.selected_student:
            self.student_card_rect = None
            return

        card_w = 640
        card_h = 64
        card_x = self.w // 2 - card_w // 2

        # Dynamically calculate the middle position between the Cognitive Maze title and the top action button
        title_h = self.title_font.size("COGNITIVE MAZE")[1] if hasattr(self, "title_font") else 112
        title_bottom = self.title_y + title_h + 4  # Includes title shadow/glow offset
        buttons_top = self.select_student_btn.rect.top if getattr(self, "select_student_btn", None) else (self.h // 2 - 100)

        available_space = max(card_h, buttons_top - title_bottom)
        card_y = title_bottom + (available_space - card_h) // 2
        self.student_card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

        # Card background surface with subtle slate alpha (cached)
        border_col = (217, 119, 6) # Warm Amber / Gold border
        if not hasattr(self, '_student_card_surf') or self._student_card_surf.get_size() != (card_w, card_h):
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(card_surf, (15, 23, 42, 225), (0, 0, card_w, card_h), border_radius=16)
            pygame.draw.rect(card_surf, border_col, (0, 0, card_w, card_h), 2, border_radius=16)
            if pygame.display.get_surface() is not None:
                try:
                    card_surf = card_surf.convert_alpha()
                except Exception:
                    pass
            self._student_card_surf = card_surf
        self.screen.blit(self._student_card_surf, (card_x, card_y))

        # Circular Avatar Icon
        av_cx = card_x + 36
        av_cy = card_y + card_h // 2
        pygame.draw.circle(self.screen, (30, 41, 59), (av_cx, av_cy), 22)
        pygame.draw.circle(self.screen, border_col, (av_cx, av_cy), 22, 2)

        gender = str(self.selected_student.get("gender", "male")).lower()
        if gender == "female" and getattr(self, "girl_avatar", None):
            self.screen.blit(self.girl_avatar, self.girl_avatar.get_rect(center=(av_cx, av_cy)))
        elif getattr(self, "boy_avatar", None):
            self.screen.blit(self.boy_avatar, self.boy_avatar.get_rect(center=(av_cx, av_cy)))
        else:
            av_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
            av_txt = av_font.render(gender[0].upper() if gender else "S", True, (255, 255, 255))
            self.screen.blit(av_txt, av_txt.get_rect(center=(av_cx, av_cy)))

        # Student Name
        first = str(self.selected_student.get("first_name") or "").strip()
        last = str(self.selected_student.get("last_name") or "").strip()
        full_name = f"{first} {last}".strip() or "Active Student"
        if len(full_name) > 26:
            full_name = full_name[:24] + "..."

        name_font = pygame.font.SysFont("Comic Sans MS", 17, bold=True)
        pill_font = pygame.font.SysFont("Segoe UI", 11, bold=True)
        metric_font = pygame.font.SysFont("Segoe UI", 13, bold=True)

        name_shadow = name_font.render(full_name, True, (0, 0, 0))
        name_surf = name_font.render(full_name, True, (255, 255, 255))
        self.screen.blit(name_shadow, (card_x + 72 + 1, card_y + 8 + 1))
        self.screen.blit(name_surf, (card_x + 72, card_y + 8))

        # Grade Level Pill
        level = self.selected_student.get("level") or self.selected_student.get("grade_level") or "Grade 2"
        pill_text = pill_font.render(str(level), True, (56, 189, 248))
        pw = pill_text.get_width() + 16
        px = card_x + 72 + name_surf.get_width() + 12
        pygame.draw.rect(self.screen, (8, 47, 73), (px, card_y + 9, pw, 20), border_radius=10)
        pygame.draw.rect(self.screen, (14, 116, 144), (px, card_y + 9, pw, 20), 1, border_radius=10)
        self.screen.blit(pill_text, (px + 8, card_y + 10))

        # Student ID Pill
        sid = self.selected_student.get("student_id") or self.selected_student.get("studentId")
        if sid:
            id_text = pill_font.render(f"ID: {sid}", True, (203, 213, 225))
            iw = id_text.get_width() + 16
            ix = px + pw + 8
            pygame.draw.rect(self.screen, (30, 41, 59), (ix, card_y + 9, iw, 20), border_radius=10)
            pygame.draw.rect(self.screen, (71, 85, 105), (ix, card_y + 9, iw, 20), 1, border_radius=10)
            self.screen.blit(id_text, (ix + 8, card_y + 10))

        # Row 2: Score & Progress
        score = self.selected_student.get("score", 0)
        prog = self.selected_student.get("progress", 0)

        # Gold star icon polygon
        star_cx = card_x + 80
        star_cy = card_y + 42
        star_pts = []
        for i in range(10):
            r = 7 if i % 2 == 0 else 3.2
            ang = i * math.pi / 5 - math.pi / 2
            star_pts.append((star_cx + r * math.cos(ang), star_cy + r * math.sin(ang)))
        pygame.draw.polygon(self.screen, (250, 204, 21), star_pts)
        pygame.draw.polygon(self.screen, (217, 119, 6), star_pts, 1)

        score_surf = metric_font.render(f"Score: {score} pts", True, (251, 191, 36))
        self.screen.blit(score_surf, (card_x + 92, card_y + 34))

        prog_label = metric_font.render(f"Progress: {prog}%", True, (74, 222, 128))
        self.screen.blit(prog_label, (card_x + 238, card_y + 34))

        # Progress Bar
        bx = card_x + 356
        by = card_y + 38
        bw = 240
        bh = 10
        fill_w = max(0, min(bw, int(bw * (prog / 100.0))))
        pygame.draw.rect(self.screen, (30, 41, 59), (bx, by, bw, bh), border_radius=5)
        if fill_w > 0:
            pygame.draw.rect(self.screen, (34, 197, 94), (bx, by, fill_w, bh), border_radius=5)
        pygame.draw.rect(self.screen, (51, 65, 85), (bx, by, bw, bh), 1, border_radius=5)

    def get_gesture_hud_geometry(self):
        """Calculates non-overlapping coordinates for the gesture status badge."""
        pill_w = 184
        pill_h = 36
        if self.current_screen in ["student_select", "leaderboard"]:
            # On student selection and leaderboard, avoid the top-left back button
            pill_x = 165
            pill_y = 22
        elif self.current_screen == "menu":
            # On main menu, place cleanly below the Exit button (30, 30, 200, 70) to prevent overlap
            pill_x = 30
            pill_y = 112
        else:
            # On all gameplay quarters, tutorial, and stage_select:
            # Position at Top-Left to ensure zero collision with top-right Guide and Pause buttons
            pill_x = 20
            pill_y = 18
        return pill_x, pill_y, pill_w, pill_h

    def draw_camera_feed(self):
        # Always draw the real-time Gesture Status HUD badge!
        self.draw_gesture_hud()

        # Always draw the real-time Live Cloud Connection Status indicator!
        self.draw_cloud_status()

        # Draw Multiple Hands Warning sign if 2+ hands detected in view
        self.draw_multiple_hands_warning()

    def draw_multiple_hands_warning(self):
        """Draws an eye-catching, zero-allocation warning banner at top-center when multiple hands are detected."""
        if not getattr(self, 'multiple_hands_detected', False):
            return

        w, h = 540, 38
        x = (self.w - w) // 2
        y = 62

        if not hasattr(self, '_multiple_hands_surf') or self._multiple_hands_surf is None:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((185, 28, 28, 235))  # Vivid red-orange warning alert
            pygame.draw.rect(surf, (254, 202, 202), (0, 0, w, h), 2, border_radius=10)

            font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
            txt = font.render("[!] MULTIPLE HANDS DETECTED - PLEASE USE 1 HAND ONLY", True, (255, 255, 255))
            surf.blit(txt, ((w - txt.get_width()) // 2, (h - txt.get_height()) // 2))

            if pygame.display.get_surface() is not None:
                try:
                    surf = surf.convert_alpha()
                except Exception:
                    pass
            self._multiple_hands_surf = surf

        # Pulsing gold border for dynamic visibility without allocation
        pulse_val = 0.5 + 0.5 * math.sin(time.time() * 6.0)
        border_col = (int(245 + 10 * pulse_val), int(158 + 40 * pulse_val), 11)
        self.screen.blit(self._multiple_hands_surf, (x, y))
        pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=10)

        # Only draw live raw video stream when camera preview is enabled (toggle with C key)
        if getattr(self, 'show_camera_overlay', False) and self.camera_frame is not None:
            cur_fid = getattr(self, 'latest_frame_id', -1)
            if getattr(self, '_cached_cam_fid', -2) != cur_fid or not hasattr(self, '_cached_cam_surf'):
                camera_frame_rgb = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
                cam_surf = pygame.surfarray.make_surface(np.swapaxes(camera_frame_rgb, 0, 1))
                cam_surf = pygame.transform.scale(cam_surf, (120, 90))
                if pygame.display.get_surface() is not None:
                    try:
                        cam_surf = cam_surf.convert()
                    except Exception:
                        pass
                self._cached_cam_surf = cam_surf
                self._cached_cam_fid = cur_fid

            pill_x, pill_y, pill_w, pill_h = self.get_gesture_hud_geometry()
            camera_x = pill_x
            camera_y = pill_y + pill_h + 38

            pygame.draw.rect(self.screen, (255, 255, 255), (camera_x - 2, camera_y - 2, 124, 94), 2, border_radius=6)
            self.screen.blit(self._cached_cam_surf, (camera_x, camera_y))

    def get_cloud_status_geometry(self):
        """Calculates placement coordinates for the Live Cloud Status badge."""
        badge_w = 176
        badge_h = 26
        if self.current_screen == "menu":
            # Directly beneath the top-right Settings button (self.w - 216, 22, 196, 34)
            badge_x = self.w - 206
            badge_y = 62
        elif self.current_screen in ["student_select", "leaderboard"]:
            # Placed cleanly to the left of the Refresh button (avoiding overlap with Refresh at self.w - 150..154)
            badge_x = self.w - 154 - badge_w - 14
            badge_y = 26
        elif self.current_screen == "stage_select":
            # Stacked neatly below the Gesture HUD at top-left
            badge_x = 20
            badge_y = 58
        else:
            # All gameplay quarters and tutorial: top-left stacked below Gesture HUD
            badge_x = 20
            badge_y = 58
        return pygame.Rect(badge_x, badge_y, badge_w, badge_h)

    def draw_cloud_status(self):
        """Renders the sleek real-time Cloud Connection Status badge and tooltip."""
        badge_rect = self.get_cloud_status_geometry()
        is_online = getattr(self, 'cloud_online', True)
        pending = getattr(self, 'cloud_pending_sync', 0)

        # Micro-pulse animation for status dot (breathing effect)
        t = time.time()
        pulse = 0.75 + 0.25 * math.sin(t * 3.5)

        if is_online:
            if pending > 0:
                status_text = f"CLOUD: SYNCING ({pending})"
                dot_col = (56, 189, 248)  # Sky blue
                border_col = (14, 116, 144)
                text_col = (224, 242, 254)
            else:
                status_text = "CLOUD: ONLINE"
                dot_col = (34, 197, 94)  # Emerald green
                border_col = (22, 163, 74)
                text_col = (220, 252, 231)
        else:
            if pending > 0:
                status_text = f"OFFLINE ({pending} QUEUED)"
            else:
                status_text = "OFFLINE (SAVED)"
            dot_col = (245, 158, 11)  # Warm Amber
            border_col = (217, 119, 6)
            text_col = (254, 243, 199)

        # Draw Badge Background Pill (reusing cached buffer to eliminate per-frame allocations)
        if not hasattr(self, '_cloud_badge_surf') or self._cloud_badge_surf.get_size() != (badge_rect.width, badge_rect.height):
            self._cloud_badge_surf = pygame.Surface((badge_rect.width, badge_rect.height), pygame.SRCALPHA)
        badge_surf = self._cloud_badge_surf
        badge_surf.fill((15, 23, 42, 220))
        pygame.draw.rect(badge_surf, border_col, (0, 0, badge_rect.width, badge_rect.height), 1, border_radius=7)
        self.screen.blit(badge_surf, (badge_rect.x, badge_rect.y))

        # Draw Glowing Status Dot
        dot_cx = badge_rect.x + 14
        dot_cy = badge_rect.y + badge_rect.height // 2
        glow_r = int(6 * pulse)
        # Soft outer aura (reuse cached aura buffer)
        aura_dim = glow_r * 2 + 4
        if not hasattr(self, '_cloud_aura_surf') or self._cloud_aura_surf.get_size() != (aura_dim, aura_dim):
            self._cloud_aura_surf = pygame.Surface((aura_dim, aura_dim), pygame.SRCALPHA)
        aura_surf = self._cloud_aura_surf
        aura_surf.fill((0, 0, 0, 0))
        aura_col = (*dot_col, int(60 * pulse))
        pygame.draw.circle(aura_surf, aura_col, (glow_r + 2, glow_r + 2), glow_r)
        self.screen.blit(aura_surf, (dot_cx - glow_r - 2, dot_cy - glow_r - 2))
        # Solid center dot
        pygame.draw.circle(self.screen, dot_col, (dot_cx, dot_cy), 4)

        # Draw Status Label
        status_font = pygame.font.SysFont("Segoe UI", 11, bold=True)
        lbl_surf = status_font.render(status_text, True, text_col)
        self.screen.blit(lbl_surf, (badge_rect.x + 26, badge_rect.y + 5))

        # Interactive Tooltip on Hover
        if badge_rect.collidepoint(self.cursor_pos):
            if is_online:
                tt_text = "Connected to Live Database. Grades sync automatically."
                tt_border = (34, 197, 94)
            else:
                if pending > 0:
                    tt_text = f"Offline Mode. {pending} grade record(s) queued for auto-upload."
                else:
                    tt_text = "Offline Mode. Progress is safely saved locally on device."
                tt_border = (245, 158, 11)

            tt_font = pygame.font.SysFont("Segoe UI", 11)
            tt_surf = tt_font.render(tt_text, True, (255, 255, 255))
            tt_w = tt_surf.get_width() + 16
            tt_h = 24
            tt_x = min(self.w - tt_w - 10, max(10, badge_rect.x))
            tt_y = badge_rect.bottom + 6

            if not hasattr(self, '_cloud_tt_box') or self._cloud_tt_box.get_size() != (tt_w, tt_h):
                self._cloud_tt_box = pygame.Surface((tt_w, tt_h), pygame.SRCALPHA)
            tt_box = self._cloud_tt_box
            tt_box.fill((10, 15, 29, 240))
            pygame.draw.rect(tt_box, tt_border, (0, 0, tt_w, tt_h), 1, border_radius=6)
            self.screen.blit(tt_box, (tt_x, tt_y))
            self.screen.blit(tt_surf, (tt_x + 8, tt_y + 4))

    def draw_gesture_hud(self):
        """Always renders a sleek real-time Gesture Status badge so the student always sees hand/gesture status."""
        hud_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)

        if self.current_gesture == "FIST":
            hold_time = time.time() - self.fist_start_time if self.fist_start_time > 0 else 0
            pct = min(100, int((hold_time / self.CLICK_HOLD_TIME) * 100))
            label = f"FIST: HOLD {pct}%"
            border_col = (250, 204, 21)   # Yellow
            text_col = (254, 240, 138)
            fill_pct = pct / 100.0
        elif self.current_gesture == "PEACE":
            hold_time = time.time() - getattr(self, 'peace_start_time', 0) if getattr(self, 'peace_start_time', 0) > 0 else 0
            pct = min(100, int((hold_time / self.CLICK_HOLD_TIME) * 100))
            if self.current_screen in ["quarter1", "quarter2", "quarter3", "quarter4", "tutorial"]:
                label = f"PEACE: PAUSE {pct}%"
            elif self.current_screen in ["stage_select", "stageselect"]:
                label = f"PEACE: MENU {pct}%"
            else:
                label = f"PEACE: CONFIRM {pct}%"
            border_col = (34, 197, 94)    # Emerald green
            text_col = (187, 247, 208)
            fill_pct = pct / 100.0
        elif self.current_gesture == "OPEN":
            label = "HAND: OPEN"
            border_col = (56, 189, 248)   # Cyan
            text_col = (224, 242, 254)
            fill_pct = 0.0
        elif "GRACE" in self.current_gesture:
            label = "HOLDING..."
            border_col = (148, 163, 184)
            text_col = (241, 245, 249)
            fill_pct = 0.0
        else:
            label = "SEEKING HAND..."
            border_col = (100, 116, 139)  # Slate
            text_col = (203, 213, 225)
            fill_pct = 0.0

        pill_x, pill_y, pill_w, pill_h = self.get_gesture_hud_geometry()

        # Semi-transparent background with progress indicator (reusing cached buffer)
        if not hasattr(self, '_gesture_hud_pill_surf') or self._gesture_hud_pill_surf.get_size() != (pill_w, pill_h):
            self._gesture_hud_pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pill_surf = self._gesture_hud_pill_surf
        pill_surf.fill((15, 23, 42, 225))
        if fill_pct > 0:
            fill_w = int((pill_w - 4) * fill_pct)
            r, g, b = border_col
            pygame.draw.rect(pill_surf, (r, g, b, 80), (2, 2, fill_w, pill_h - 4), border_radius=6)
        pygame.draw.rect(pill_surf, border_col, (0, 0, pill_w, pill_h), 2, border_radius=8)
        self.screen.blit(pill_surf, (pill_x, pill_y))

        # Text label
        txt_surf = hud_font.render(label, True, text_col)
        self.screen.blit(txt_surf, txt_surf.get_rect(center=(pill_x + pill_w // 2, pill_y + pill_h // 2 - 1)))

    def draw_cursor(self):
        if self.current_gesture != "NO HAND":
            if self.fist_start_time > 0:
                color = (255, 200, 0)  # Yellow when holding fist
                hold_time = time.time() - self.fist_start_time
                pct = min(1.0, hold_time / self.CLICK_HOLD_TIME)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)
                # Draw loading progress bar under cursor
                pygame.draw.rect(self.screen, (30, 41, 59), (self.cursor_pos[0] - 20, self.cursor_pos[1] + 20, 40, 6))
                pygame.draw.rect(self.screen, (255, 200, 0), (self.cursor_pos[0] - 20, self.cursor_pos[1] + 20, int(40 * pct), 6))
            elif getattr(self, 'peace_start_time', 0) > 0:
                color = (34, 197, 94)  # Green when holding peace sign
                hold_time = time.time() - self.peace_start_time
                pct = min(1.0, hold_time / self.CLICK_HOLD_TIME)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)
                # Draw loading progress bar under cursor
                pygame.draw.rect(self.screen, (30, 41, 59), (self.cursor_pos[0] - 20, self.cursor_pos[1] + 20, 40, 6))
                pygame.draw.rect(self.screen, (34, 197, 94), (self.cursor_pos[0] - 20, self.cursor_pos[1] + 20, int(40 * pct), 6))
            else:
                color = (255, 255, 255)  # White normally
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)
        elif getattr(self, 'mouse_active', False):
            # Only draw mouse / targeting crosshair when physical mouse has actually moved!
            pygame.draw.circle(self.screen, (255, 255, 255), self.cursor_pos, 13, 2)
            pygame.draw.circle(self.screen, (56, 189, 248), self.cursor_pos, 4)
            # Subtle crosshair pings
            cx, cy = self.cursor_pos
            pygame.draw.line(self.screen, (255, 255, 255), (cx - 17, cy), (cx - 13, cy), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (cx + 13, cy), (cx + 17, cy), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, cy - 17), (cx, cy - 13), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, cy + 13), (cx, cy + 17), 2)
        else:
            # No hand detected and mouse is idle: do NOT draw any cursor
            pass

    def draw_version_footer(self):
        """Draws the version badge and update notification pill on the main menu."""
        ver_text = f"Cognitive Quest v{APP_VERSION}"
        ver_surf = self.small_font.render(ver_text, True, (148, 163, 184))
        self.screen.blit(ver_surf, (20, self.h - 26))

        if getattr(self, 'update_manager', None) and self.update_manager.has_update():
            latest = self.update_manager.latest_version or "New"
            st = self.update_manager.state
            p_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)

            if st == UpdateState.DOWNLOADING:
                stats = self.update_manager.get_download_stats()
                pill_w, pill_h = 240, 26
                pill_x = 20 + ver_surf.get_width() + 16
                pill_y = self.h - 30
                pill_rect = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
                self.footer_update_rect = pill_rect
                hover = pill_rect.collidepoint(self.cursor_pos)
                bg = (14, 116, 144) if hover else (8, 145, 178)
                pygame.draw.rect(self.screen, bg, pill_rect, border_radius=13)
                pygame.draw.rect(self.screen, (103, 232, 249), pill_rect, 2, border_radius=13)
                txt = p_font.render(f"⬇ Updating: {stats['pct']}% ({stats['mb_done']:.1f}/{stats['mb_total']:.1f} MB)", True, (255, 255, 255))
                self.screen.blit(txt, (pill_rect.centerx - txt.get_width() // 2, pill_rect.centery - txt.get_height() // 2))

            elif st == UpdateState.READY_TO_INSTALL:
                pill_w, pill_h = 240, 26
                pill_x = 20 + ver_surf.get_width() + 16
                pill_y = self.h - 30
                pill_rect = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
                self.footer_update_rect = pill_rect
                hover = pill_rect.collidepoint(self.cursor_pos)
                bg = (16, 185, 129) if hover else (5, 150, 105)
                pygame.draw.rect(self.screen, bg, pill_rect, border_radius=13)
                pygame.draw.rect(self.screen, (110, 231, 183), pill_rect, 2, border_radius=13)
                txt = p_font.render("🚀 Update Ready - Install & Restart!", True, (255, 255, 255))
                self.screen.blit(txt, (pill_rect.centerx - txt.get_width() // 2, pill_rect.centery - txt.get_height() // 2))

            else:
                pill_w, pill_h = 210, 26
                pill_x = 20 + ver_surf.get_width() + 16
                pill_y = self.h - 30
                pill_rect = pygame.Rect(pill_x, pill_y, pill_w, pill_h)
                self.footer_update_rect = pill_rect
                hover = pill_rect.collidepoint(self.cursor_pos)
                bg = (234, 88, 12) if hover else (180, 83, 9)
                pygame.draw.rect(self.screen, bg, pill_rect, border_radius=13)
                pygame.draw.rect(self.screen, (253, 186, 116), pill_rect, 2, border_radius=13)
                txt = p_font.render(f"★ Update v{latest} Available!", True, (255, 255, 255))
                self.screen.blit(txt, (pill_rect.centerx - txt.get_width() // 2, pill_rect.centery - txt.get_height() // 2))
        else:
            self.footer_update_rect = None

    def draw(self):
        if self.current_screen == "menu":
            # BACKGROUND
            if self.bg_image:
                self.screen.blit(self.bg_image, (0, 0))
            else:
                for i in range(self.h):
                    color_ratio = i / self.h
                    r = int(135 * (1 - color_ratio) + 100 * color_ratio)
                    g = int(206 * (1 - color_ratio) + 150 * color_ratio)
                    b = int(235 * (1 - color_ratio) + 200 * color_ratio)
                    pygame.draw.line(self.screen, (r, g, b), (0, i), (self.w, i))

            if not hasattr(self, '_menu_dim_overlay') or self._menu_dim_overlay.get_size() != (self.w, self.h):
                self._menu_dim_overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
                self._menu_dim_overlay.fill((0, 0, 0, 60))
                if pygame.display.get_surface() is not None:
                    try:
                        self._menu_dim_overlay = self._menu_dim_overlay.convert_alpha()
                    except Exception:
                        pass
            self.screen.blit(self._menu_dim_overlay, (0, 0))

            # TITLE
            for offset in range(3, 0, -1):
                glow = self.title_font.render("COGNITIVE MAZE", True, (255, 255, 150))
                tx = self.w // 2 - glow.get_width() // 2
                self.screen.blit(glow, (tx, self.title_y - offset))

            title = self.title_font.render("COGNITIVE MAZE", True, (255, 255, 255))
            title_shadow = self.title_font.render("COGNITIVE MAZE", True, (0, 0, 0))
            tx = self.w // 2 - title.get_width() // 2
            self.screen.blit(title_shadow, (tx + 4, self.title_y + 4))
            self.screen.blit(title, (tx, self.title_y))

            # CHARACTERS
            if self.boy_image:
                self.screen.blit(self.boy_image, (self.boy_x, self.boy_y))
            if self.girl_image:
                self.screen.blit(self.girl_image, (self.girl_x, self.girl_y))

            # DIALOGUE BOX
            if self.dialogue_active and self.current_line < len(self.dialogue_lines):
                if not hasattr(self, '_dialogue_surface') or self._dialogue_surface.get_size() != (self.dialogue_box_width, self.dialogue_box_height):
                    self._dialogue_surface = pygame.Surface((self.dialogue_box_width, self.dialogue_box_height))
                    if pygame.display.get_surface() is not None:
                        try:
                            self._dialogue_surface = self._dialogue_surface.convert()
                        except Exception:
                            pass
                    self._dialogue_surface.fill((255, 255, 255))
                    self._dialogue_surface.set_alpha(240)
                self.screen.blit(self._dialogue_surface, (self.dialogue_box_x, self.dialogue_box_y))

                pygame.draw.rect(self.screen, (100, 100, 150),
                                 (self.dialogue_box_x, self.dialogue_box_y,
                                  self.dialogue_box_width, self.dialogue_box_height), 3, border_radius=15)

                # Draw avatar
                avatar_x = self.dialogue_box_x + 30
                avatar_y = self.dialogue_box_y + 25

                if self.current_line == 0 or self.current_line == 2:
                    if self.boy_avatar:
                        self.screen.blit(self.boy_avatar, (avatar_x, avatar_y))
                        speaker_text_x = avatar_x + 50
                    else:
                        pygame.draw.circle(self.screen, (52, 152, 219), (avatar_x + 20, avatar_y + 20), 20)
                        speaker_text_x = avatar_x + 50
                    speaker = "BOY"
                else:
                    if self.girl_avatar:
                        self.screen.blit(self.girl_avatar, (avatar_x, avatar_y))
                        speaker_text_x = avatar_x + 50
                    else:
                        pygame.draw.circle(self.screen, (231, 76, 60), (avatar_x + 20, avatar_y + 20), 20)
                        speaker_text_x = avatar_x + 50
                    speaker = "GIRL"

                speaker_text = self.dialogue_font.render(speaker, True, (40, 40, 40))
                self.screen.blit(speaker_text, (speaker_text_x, self.dialogue_box_y + 35))

                dialogue_text = self.dialogue_font.render(self.dialogue_lines[self.current_line], True, (40, 40, 40))
                self.screen.blit(dialogue_text, (self.dialogue_box_x + 30, self.dialogue_box_y + 80))

                continue_text = self.small_font.render("Make fist to continue...", True, (150, 150, 150))
                self.screen.blit(continue_text, (self.dialogue_box_x + self.dialogue_box_width - 200,
                                                 self.dialogue_box_y + self.dialogue_box_height - 30))

            # SELECTED STUDENT PROFILE CARD
            self.draw_selected_student_card()

            # ERROR MESSAGE (e.g. Please select a student first!)
            if self.show_no_student_message and pygame.time.get_ticks() < self.no_student_timer:
                error_w = 420
                error_h = 44
                if not hasattr(self, '_error_bg_surf'):
                    err_surf = pygame.Surface((error_w, error_h), pygame.SRCALPHA)
                    err_surf.fill((220, 38, 38, 235))
                    pygame.draw.rect(err_surf, (254, 202, 202), (0, 0, error_w, error_h), 2, border_radius=12)
                    if pygame.display.get_surface() is not None:
                        try:
                            err_surf = err_surf.convert_alpha()
                        except Exception:
                            pass
                    self._error_bg_surf = err_surf
                self.screen.blit(self._error_bg_surf, (self.w // 2 - error_w // 2, self.error_y))
                msg = self.small_font.render("Please select a student first!", True, (255, 255, 255))
                self.screen.blit(msg, (self.w // 2 - msg.get_width() // 2, self.error_y + 8))
            else:
                self.show_no_student_message = False

            # DRAW BUTTONS
            for b in self.buttons:
                b.draw(self.screen)

            # VERSION BADGE & UPDATE PILL
            self.draw_version_footer()

            self.draw_camera_feed()

        elif self.current_screen in ("stage_select", "stageselect") and self.stage_select:
            self.stage_select.draw()
            self.draw_camera_feed()

        elif self.current_screen == "student_select" and self.student_select:
            self.student_select.draw()
            self.draw_camera_feed()

        elif self.current_screen == "tutorial" and self.tutorial:
            self.tutorial.draw()
            self.draw_camera_feed()

        elif self.current_screen == "quarter1" and self.quarter1:
            self.quarter1.draw()
            self.draw_camera_feed()

        elif self.current_screen == "quarter2" and self.quarter2:
            self.quarter2.draw()
            self.draw_camera_feed()

        elif self.current_screen == "quarter3" and self.quarter3:
            self.quarter3.draw()
            self.draw_camera_feed()

        elif self.current_screen == "quarter4" and self.quarter4:
            self.quarter4.draw()
            self.draw_camera_feed()

        elif self.current_screen == "leaderboard" and self.leaderboard:
            self.leaderboard.draw()
            self.draw_camera_feed()

        # Draw confirmation pop-up if active (above normal screens)
        if self.popup_state:
            self.draw_popup()

        # CURSOR IS ALWAYS DRAWN LAST TO REMAIN AT THE TOPMOST Z-LAYER
        self.draw_cursor()