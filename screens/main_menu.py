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

import pygame
import cv2
import mediapipe as mp
import numpy as np
import os
import time
import math
import threading
from core.audio_manager import audio_manager
from ui.button import Button
from screens.stageselect import StageSelect
from screens.studentselect import StudentSelect
from screens.tutorial import TutorialScreen
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4
from screens.leaderboard import LeaderboardScreen


class MainMenu:

    def __init__(self, screen):

        self.screen = screen
        self.w, self.h = screen.get_size()

        # ==========================================
        # SIMPLE GESTURE DETECTION
        # ==========================================

        # MediaPipe setup
        self.mp_hands = None
        self.hands = None
        try:
            if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'hands'):
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    max_num_hands=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
        except Exception as e:
            print(f"[WARN] MediaPipe hands init exception: {e}")
            self.hands = None

        # Camera setup
        self.camera_size = (160, 120)
        self.show_camera_overlay = False  # Set to False to remove the visual camera overlay box
        self.cap = None
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                print("[OK] Camera initialized!")
            else:
                print("[WARN] Camera not available, falling back to mouse control.")
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
        except Exception as e:
            print(f"[WARN] Camera init exception: {e}")
            self.cap = None

        # Threaded Camera & MediaPipe Background Worker (60 FPS Unlocked)
        self.camera_running = True
        self.camera_lock = threading.Lock()
        self.latest_raw_frame = None
        self.latest_hand_landmarks = None
        self.latest_hand_detected = False

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

        # Cursor smoothing & jitter suppression
        self.cursor_x = float(self.w // 2)
        self.cursor_y = float(self.h // 2)
        self.target_history = []

        # Store last cursor position for when hand is lost
        self.last_cursor_x = self.w // 2
        self.last_cursor_y = self.h // 2

        # Hand grace period
        self.last_hand_time = time.time()
        self.HAND_GRACE = 1.0  # Keep cursor for 1 second after hand lost

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
            "Welcome to Cognitive Play!",
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

        # ==========================================
        # BUTTONS
        # ==========================================
        self.setup_buttons()

        self.title_y = 40
        self.student_info_y = self.h - 90
        self.error_y = self.h - 150

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
        # AUTOMATIC BACKGROUND OFFLINE EVALUATION SYNC
        # ==========================================
        try:
            from db.connect_db import db
            if db:
                threading.Thread(target=db.sync_offline_results, daemon=True).start()
        except Exception:
            pass

        print(f"[GAME] Simple Gesture Control Active!")
        print(f"   - WRIST movement controls cursor (stable when making fist)")
        print(f"   - Make a FIST and hold for {self.CLICK_HOLD_TIME} seconds to click")

    # ==========================================
    # SIMPLE FIST DETECTION (USING FINGER TIPS)
    # ==========================================

    def is_fist(self, hand_data):
        """Detect closed fist (all fingers folded into palm)"""
        if hand_data is None:
            return False
        try:
            if isinstance(hand_data, list):
                wrist = hand_data[0]
                knuckle_dists = [math.hypot(hand_data[k][0] - wrist[0], hand_data[k][1] - wrist[1]) for k in [6, 10, 14, 18]]
                tip_dists = [math.hypot(hand_data[t][0] - wrist[0], hand_data[t][1] - wrist[1]) for t in [8, 12, 16, 20]]
            else:
                wrist = hand_data.landmark[0]
                knuckle_dists = [math.hypot(hand_data.landmark[k].x - wrist.x, hand_data.landmark[k].y - wrist.y) for k in [6, 10, 14, 18]]
                tip_dists = [math.hypot(hand_data.landmark[t].x - wrist.x, hand_data.landmark[t].y - wrist.y) for t in [8, 12, 16, 20]]

            # A finger is truly folded/closed if its tip is closer to the wrist than its middle knuckle
            closed_fingers = [tip_dists[i] < knuckle_dists[i] * 1.05 for i in range(4)]
            return sum(closed_fingers) >= 3
        except Exception:
            return False

    def is_peace_sign(self, hand_data):
        """Detect peace sign / digit 2 (index and middle fingers open, ring and pinky closed)"""
        if hand_data is None:
            return False
        try:
            if isinstance(hand_data, list):
                wrist = hand_data[0]
                knuckle_dists = [math.hypot(hand_data[k][0] - wrist[0], hand_data[k][1] - wrist[1]) for k in [6, 10, 14, 18]]
                tip_dists = [math.hypot(hand_data[t][0] - wrist[0], hand_data[t][1] - wrist[1]) for t in [8, 12, 16, 20]]
            else:
                wrist = hand_data.landmark[0]
                knuckle_dists = [math.hypot(hand_data.landmark[k].x - wrist.x, hand_data.landmark[k].y - wrist.y) for k in [6, 10, 14, 18]]
                tip_dists = [math.hypot(hand_data.landmark[t].x - wrist.x, hand_data.landmark[t].y - wrist.y) for t in [8, 12, 16, 20]]

            # Index and Middle open, Ring and Pinky closed
            closed_fingers = [tip_dists[i] < knuckle_dists[i] * 1.05 for i in range(4)]
            return (not closed_fingers[0]) and (not closed_fingers[1]) and closed_fingers[2] and closed_fingers[3]
        except Exception:
            return False

    def _camera_worker(self):
        """Asynchronous background worker for camera frame grabbing and MediaPipe ML inference (60 FPS Locked)"""
        while self.camera_running and self.cap is not None and self.cap.isOpened():
            try:
                ret, img = self.cap.read()
                if not ret or img is None:
                    time.sleep(0.01)
                    continue

                img = cv2.flip(img, 1)
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                preview = cv2.resize(img, self.camera_size) if getattr(self, 'show_camera_overlay', False) else None

                results = self.hands.process(rgb) if self.hands is not None else None
                coords = None
                if results and results.multi_hand_landmarks:
                    try:
                        coords = [(float(lm.x), float(lm.y)) for lm in results.multi_hand_landmarks[0].landmark]
                    except Exception:
                        coords = None

                with self.camera_lock:
                    self.latest_raw_frame = preview
                    self.latest_hand_coords = coords
                    self.latest_hand_detected = (coords is not None and len(coords) == 21)

            except Exception:
                pass
            time.sleep(0.005)

    def update_gesture(self):
        """Update gesture detection - Instant read from threaded worker (0ms latency, 60 FPS)"""
        if self.cap is None or not self.cap.isOpened():
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.cursor_pos = (mouse_x, mouse_y)
            return

        try:
            with self.camera_lock:
                img_preview = self.latest_raw_frame
                hand_coords = getattr(self, 'latest_hand_coords', None)
                hand_detected = getattr(self, 'latest_hand_detected', False)

            if img_preview is not None:
                self.camera_frame = img_preview

            if hand_detected and hand_coords and len(hand_coords) == 21:
                self.last_hand_time = time.time()

                # 1. Use Stable Palm Center (blend between wrist 0 and middle MCP 9)
                wrist = hand_coords[0]
                knuckle = hand_coords[9]
                palm_x = wrist[0] * 0.35 + knuckle[0] * 0.65
                palm_y = wrist[1] * 0.35 + knuckle[1] * 0.65

                # Map palm position to screen coordinates with slight edge padding
                raw_target_x = float(np.interp(palm_x, [0.12, 0.88], [0, self.w]))
                raw_target_y = float(np.interp(palm_y, [0.12, 0.88], [0, self.h]))

                # 2. Rolling 3-frame filter to reject high-frequency sensor noise outliers
                if not hasattr(self, 'target_history'):
                    self.target_history = []
                self.target_history.append((raw_target_x, raw_target_y))
                if len(self.target_history) > 3:
                    self.target_history.pop(0)

                target_x = sum(p[0] for p in self.target_history) / len(self.target_history)
                target_y = sum(p[1] for p in self.target_history) / len(self.target_history)

                # 3. Distance from current smoothed cursor
                dx = target_x - self.cursor_x
                dy = target_y - self.cursor_y
                dist = math.hypot(dx, dy)

                # Detect gestures first so we can stabilize the cursor during clicks
                fist_detected = self.is_fist(hand_coords)
                peace_detected = self.is_peace_sign(hand_coords)

                # 4. Adaptive Jitter Deadzone & Silk-Smooth Interpolation
                if fist_detected:
                    # Click Stabilization: when holding a fist, lock cursor still to prevent drifting off buttons!
                    if dist < 12.0:
                        smooth = 0.0  # Rock-solid lock on target
                    else:
                        smooth = 0.06
                elif dist < 4.5:
                    # Deadzone: eliminate camera micro-tremors completely when hand is held steady
                    smooth = 0.0
                elif dist < 15.0:
                    # Precision aim zone (hovering over buttons): silk-smooth interpolation
                    smooth = 0.12
                elif dist < 50.0:
                    # Normal movement: fluid and natural
                    smooth = 0.28
                else:
                    # Fast swipe: immediate responsive tracking
                    smooth = 0.52

                if smooth > 0.0:
                    self.cursor_x = self.cursor_x * (1 - smooth) + target_x * smooth
                    self.cursor_y = self.cursor_y * (1 - smooth) + target_y * smooth

                # Clamp cursor within window
                self.cursor_x = max(0.0, min(float(self.w), self.cursor_x))
                self.cursor_y = max(0.0, min(float(self.h), self.cursor_y))
                self.cursor_pos = (int(round(self.cursor_x)), int(round(self.cursor_y)))

                # Store last position for grace period
                self.last_cursor_x = self.cursor_x
                self.last_cursor_y = self.cursor_y

                if fist_detected:
                    if self.fist_start_time == 0:
                        self.fist_start_time = time.time()
                        print("[FIST] Fist detected! Hold to click...")

                    hold_time = time.time() - self.fist_start_time

                    if hold_time >= self.CLICK_HOLD_TIME and not self.click_ready:
                        self.click_ready = True
                        print(f"[OK] CLICK! (Held for {hold_time:.1f}s)")
                        self.trigger_click()
                else:
                    if self.fist_start_time != 0:
                        print("[HAND] Fist released")
                    self.fist_start_time = 0
                    self.click_ready = False

                if peace_detected:
                    if self.peace_start_time == 0:
                        self.peace_start_time = time.time()
                        print("[PEACE] Peace sign detected! Hold to trigger confirmation...")

                    hold_time = time.time() - self.peace_start_time
                    if hold_time >= self.CLICK_HOLD_TIME:
                        self.peace_start_time = 0
                        if not self.popup_state:
                            if self.current_screen == "menu":
                                self.popup_state = "confirm_exit"
                            else:
                                self.popup_state = "confirm_menu"
                            print(f"[OK] PEACE SIGN TRIGGERED! Popup state: {self.popup_state}")
                else:
                    self.peace_start_time = 0

                self.current_gesture = "FIST" if fist_detected else ("PEACE" if peace_detected else "OPEN")

            # HAND GRACE PERIOD - keep cursor position for a while after hand is lost
            else:
                elapsed = time.time() - self.last_hand_time
                if elapsed < self.HAND_GRACE:
                    # Keep last cursor position
                    self.cursor_pos = (int(self.last_cursor_x), int(self.last_cursor_y))
                    self.current_gesture = "NO HAND (GRACE)"
                else:
                    self.current_gesture = "NO HAND"
                    self.fist_start_time = 0
                    self.peace_start_time = 0
                    self.click_ready = False
                    if pygame.mouse.get_focused():
                        m_pos = pygame.mouse.get_pos()
                        self.cursor_pos = m_pos
                        self.cursor_x, self.cursor_y = float(m_pos[0]), float(m_pos[1])
        except Exception:
            pass

    # ==========================================
    # CLICK HANDLER
    def trigger_click(self):
        """Handle click at cursor position"""
        pos = self.cursor_pos
        print(f"[MOUSE] Click at: {pos}")

        # If pop-up is active, intercept clicks!
        if self.popup_state:
            self.handle_popup_click(pos)
            return

        # Route click to active screen if not in menu
        if self.current_screen == "stage_select" and self.stage_select:
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
            box_w, box_h = 580, 360
            box_x = (self.w - box_w) // 2
            box_y = (self.h - box_h) // 2

            m_minus_rect = pygame.Rect(box_x + 40, box_y + 105, 42, 34)
            m_bar_rect = pygame.Rect(box_x + 92, box_y + 110, 240, 24)
            m_plus_rect = pygame.Rect(box_x + 342, box_y + 105, 42, 34)
            m_mute_rect = pygame.Rect(box_x + 398, box_y + 105, 140, 34)

            s_minus_rect = pygame.Rect(box_x + 40, box_y + 190, 42, 34)
            s_bar_rect = pygame.Rect(box_x + 92, box_y + 195, 240, 24)
            s_plus_rect = pygame.Rect(box_x + 342, box_y + 190, 42, 34)
            s_mute_rect = pygame.Rect(box_x + 398, box_y + 190, 140, 34)

            test_rect = pygame.Rect(box_x + 50, box_y + 280, 220, 46)
            done_rect = pygame.Rect(box_x + box_w - 270, box_y + 280, 220, 46)

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

            elif test_rect.collidepoint(pos):
                self.audio_manager.play_sfx("success")
            elif done_rect.collidepoint(pos):
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
        """Draw the interactive Audio & Sound Settings modal"""
        # 1. Overlay
        overlay = pygame.Surface((self.w, self.h))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        # 2. Centered dialog box
        box_w, box_h = 580, 360
        box_x = (self.w - box_w) // 2
        box_y = (self.h - box_h) // 2
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (56, 189, 248), dialog_rect, 3, border_radius=14)

        title_font = pygame.font.SysFont("Comic Sans MS", 22, bold=True)
        label_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
        btn_font = pygame.font.SysFont("Comic Sans MS", 15, bold=True)
        small_font = pygame.font.SysFont("Comic Sans MS", 13)

        # Title
        title_surf = title_font.render("Audio & Sound Settings", True, (56, 189, 248))
        self.screen.blit(title_surf, (box_x + (box_w - title_surf.get_width()) // 2, box_y + 22))

        # Divider
        pygame.draw.line(self.screen, (56, 189, 248), (box_x + 35, box_y + 60), (box_x + box_w - 35, box_y + 60), 2)

        # ---------------- Music Volume Row ----------------
        m_vol = self.audio_manager.music_volume
        m_muted = self.audio_manager.music_muted
        m_pct = int(m_vol * 100)
        m_label_color = (239, 68, 68) if m_muted else (241, 245, 249)
        m_label_text = f"Music Volume: {m_pct}% {'(MUTED)' if m_muted else ''}"
        self.screen.blit(label_font.render(m_label_text, True, m_label_color), (box_x + 40, box_y + 75))

        # Buttons and Slider
        m_minus_rect = pygame.Rect(box_x + 40, box_y + 105, 42, 34)
        m_bar_rect = pygame.Rect(box_x + 92, box_y + 110, 240, 24)
        m_plus_rect = pygame.Rect(box_x + 342, box_y + 105, 42, 34)
        m_mute_rect = pygame.Rect(box_x + 398, box_y + 105, 140, 34)

        # Draw Music Minus [-]
        hover_m_minus = m_minus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_m_minus else (30, 41, 59), m_minus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (56, 189, 248), m_minus_rect, 2, border_radius=6)
        txt = btn_font.render("-", True, (255, 255, 255))
        self.screen.blit(txt, (m_minus_rect.centerx - txt.get_width() // 2, m_minus_rect.centery - txt.get_height() // 2))

        # Draw Music Bar
        pygame.draw.rect(self.screen, (30, 41, 59), m_bar_rect, border_radius=5)
        fill_w = int(m_bar_rect.width * m_vol)
        if fill_w > 0:
            fill_color = (100, 116, 139) if m_muted else (56, 189, 248)
            pygame.draw.rect(self.screen, fill_color, (m_bar_rect.x, m_bar_rect.y, fill_w, m_bar_rect.height), border_radius=5)
        pygame.draw.rect(self.screen, (148, 163, 184), m_bar_rect, 2, border_radius=5)

        # Draw Music Plus [+]
        hover_m_plus = m_plus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_m_plus else (30, 41, 59), m_plus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (56, 189, 248), m_plus_rect, 2, border_radius=6)
        txt = btn_font.render("+", True, (255, 255, 255))
        self.screen.blit(txt, (m_plus_rect.centerx - txt.get_width() // 2, m_plus_rect.centery - txt.get_height() // 2))

        # Draw Music Mute Button
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
        self.screen.blit(label_font.render(s_label_text, True, s_label_color), (box_x + 40, box_y + 160))

        s_minus_rect = pygame.Rect(box_x + 40, box_y + 190, 42, 34)
        s_bar_rect = pygame.Rect(box_x + 92, box_y + 195, 240, 24)
        s_plus_rect = pygame.Rect(box_x + 342, box_y + 190, 42, 34)
        s_mute_rect = pygame.Rect(box_x + 398, box_y + 190, 140, 34)

        # Draw SFX Minus [-]
        hover_s_minus = s_minus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_s_minus else (30, 41, 59), s_minus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (34, 197, 94), s_minus_rect, 2, border_radius=6)
        txt = btn_font.render("-", True, (255, 255, 255))
        self.screen.blit(txt, (s_minus_rect.centerx - txt.get_width() // 2, s_minus_rect.centery - txt.get_height() // 2))

        # Draw SFX Bar
        pygame.draw.rect(self.screen, (30, 41, 59), s_bar_rect, border_radius=5)
        fill_w = int(s_bar_rect.width * s_vol)
        if fill_w > 0:
            fill_color = (100, 116, 139) if s_muted else (34, 197, 94)
            pygame.draw.rect(self.screen, fill_color, (s_bar_rect.x, s_bar_rect.y, fill_w, s_bar_rect.height), border_radius=5)
        pygame.draw.rect(self.screen, (148, 163, 184), s_bar_rect, 2, border_radius=5)

        # Draw SFX Plus [+]
        hover_s_plus = s_plus_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if hover_s_plus else (30, 41, 59), s_plus_rect, border_radius=6)
        pygame.draw.rect(self.screen, (34, 197, 94), s_plus_rect, 2, border_radius=6)
        txt = btn_font.render("+", True, (255, 255, 255))
        self.screen.blit(txt, (s_plus_rect.centerx - txt.get_width() // 2, s_plus_rect.centery - txt.get_height() // 2))

        # Draw SFX Mute Button
        hover_s_mute = s_mute_rect.collidepoint(self.cursor_pos)
        mute_bg = (239, 68, 68) if s_muted else ((51, 65, 85) if hover_s_mute else (30, 41, 59))
        pygame.draw.rect(self.screen, mute_bg, s_mute_rect, border_radius=6)
        pygame.draw.rect(self.screen, (239, 68, 68) if s_muted else (34, 197, 94), s_mute_rect, 2, border_radius=6)
        txt = btn_font.render("UNMUTE" if s_muted else "MUTE SFX", True, (255, 255, 255))
        self.screen.blit(txt, (s_mute_rect.centerx - txt.get_width() // 2, s_mute_rect.centery - txt.get_height() // 2))

        # Hotkey hint
        hint_surf = small_font.render("Hotkey: [M] Toggle Mute  |  [ [ ] / [ ] ] Adjust Volume", True, (148, 163, 184))
        self.screen.blit(hint_surf, (box_x + (box_w - hint_surf.get_width()) // 2, box_y + 242))

        # ---------------- Bottom Action Buttons ----------------
        test_rect = pygame.Rect(box_x + 50, box_y + 280, 220, 46)
        done_rect = pygame.Rect(box_x + box_w - 270, box_y + 280, 220, 46)

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

        # 1. Semi-transparent full-screen overlay
        overlay = pygame.Surface((self.w, self.h))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

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
        if self.selected_student:
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
        
        # Sound Settings button on top right
        sound_btn_w = 170
        sound_btn_h = 50
        sound_btn_x = self.w - sound_btn_w - 30
        sound_btn_y = 30
        is_muted = self.audio_manager.music_muted and self.audio_manager.sfx_muted
        sound_text = "MUTED" if is_muted else f"SOUND {int(self.audio_manager.music_volume * 100)}%"
        self.sound_btn = Button(
            (sound_btn_x, sound_btn_y, sound_btn_w, sound_btn_h),
            text=f"SOUND: {sound_text}",
            font=self.small_font,
            bg_color=(30, 41, 59),
            text_color=(255, 215, 0) if not is_muted else (239, 68, 68),
            action=self.open_audio_settings
        )

        if has_save:
            # Case: Selected student has existing save progress -> 4 vertical buttons
            total_height = (bh * 4) + (gap * 3)
            start_y = (self.h // 2) - (total_height // 2)
            
            self.select_student_btn = Button(
                (self.w // 2 - bw // 2, start_y, bw, bh),
                text="SELECT STUDENT",
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
            
            self.buttons = [self.select_student_btn, self.continue_activity_btn, self.start_new_activity_btn, self.leaderboard_btn, self.exit_btn, self.sound_btn]
        else:
            # Case: No saved progress or no student selected -> 3 vertical buttons
            total_height = (bh * 3) + (gap * 2)
            start_y = (self.h // 2) - (total_height // 2)
            
            self.select_student_btn = Button(
                (self.w // 2 - bw // 2, start_y, bw, bh),
                text="SELECT STUDENT",
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
            
            self.buttons = [self.select_student_btn, self.start_activity_btn, self.leaderboard_btn, self.exit_btn, self.sound_btn]

    def open_audio_settings(self):
        self.audio_manager.play_sfx("click")
        self.popup_state = "audio_settings"

    def show_leaderboard(self):
        print("[TROPHY] LEADERBOARD clicked! Loading Hall of Fame rankings...")
        self.current_screen = "leaderboard"
        self.leaderboard = LeaderboardScreen(self.screen, self)

    def select_student(self):
        print(f"[DATA] SELECT STUDENT clicked!")
        self.current_screen = "student_select"
        self.student_select = StudentSelect(self.screen, self)

    def start_activity(self):
        print(f"[GAME] START ACTIVITY clicked!")
        if not self.selected_student:
            self.show_no_student_message = True
            self.no_student_timer = pygame.time.get_ticks() + 2000
            return

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
            self.tutorial = TutorialScreen(self.screen, self)
            return

        self.current_screen = "stage_select"
        self.stage_select = StageSelect(self.screen, self)

    def continue_activity(self):
        print("[GAME] CONTINUE ACTIVITY clicked!")
        if not self.selected_student:
            self.show_no_student_message = True
            self.no_student_timer = pygame.time.get_ticks() + 2000
            return
            
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
            self.show_no_student_message = True
            self.no_student_timer = pygame.time.get_ticks() + 2000
            return
        self.popup_state = "confirm_new_activity"

    def confirm_exit_game(self):
        print("[DOOR] ESC / EXIT clicked! Requesting 'Are you sure you want to quit?' confirmation popup...")
        if hasattr(self, 'audio_manager'):
            self.audio_manager.play_sfx("click")
        self.popup_state = "confirm_exit"

    def exit_game(self):
        print("[DOOR] EXIT clicked!")
        self.camera_running = False
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
            self.update_gesture()
            if not self.popup_state:
                # Update sound button dynamic text
                if getattr(self, 'sound_btn', None):
                    is_muted = self.audio_manager.music_muted and self.audio_manager.sfx_muted
                    sound_text = "MUTED" if is_muted else f"SOUND {int(self.audio_manager.music_volume * 100)}%"
                    self.sound_btn.text = f"SOUND: {sound_text}"
                    self.sound_btn.text_color = (255, 215, 0) if not is_muted else (239, 68, 68)

                # Update button hover states
                for b in self.buttons:
                    b.hovered = b.rect.collidepoint(self.cursor_pos)

        elif self.current_screen == "stage_select" and self.stage_select:
            self.update_gesture()
            if self.stage_select:
                self.stage_select.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
                if not self.popup_state:
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
                if not self.popup_state:
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
                if not self.popup_state:
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
                if not self.popup_state:
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
                if not self.popup_state:
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
                if not self.popup_state:
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
                if not self.popup_state:
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
                if not self.popup_state:
                    self.leaderboard.update()

    def handle_event(self, event):
        # Global audio hotkeys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.audio_manager.toggle_master_mute()
                return
            elif event.key == pygame.K_LEFTBRACKET:
                self.audio_manager.set_music_volume(self.audio_manager.music_volume - 0.1)
                return
            elif event.key == pygame.K_RIGHTBRACKET:
                self.audio_manager.set_music_volume(self.audio_manager.music_volume + 0.1)
                return
            elif event.key == pygame.K_c:
                self.show_camera_overlay = not getattr(self, 'show_camera_overlay', False)
                print(f"[CAM] Webcam preview box toggled: {self.show_camera_overlay}")
                return

        # If popup is active, intercept clicks and key events!
        if self.popup_state:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_popup_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
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
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.trigger_click()
                elif event.key == pygame.K_ESCAPE:
                    self.confirm_exit_game()
        elif self.current_screen == "stage_select" and self.stage_select:
            result = self.stage_select.handle_event(event)
            if result == "back":
                self.current_screen = "menu"
                self.stage_select = None
        elif self.current_screen == "student_select" and self.student_select:
            result = self.student_select.handle_event(event)
            if result == "back":
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

    def draw_camera_feed(self):
        # Always draw the real-time Gesture Status HUD badge!
        self.draw_gesture_hud()

        # Only draw live raw video stream when camera preview is enabled (toggle with C key)
        if getattr(self, 'show_camera_overlay', False) and self.camera_frame is not None:
            camera_frame_rgb = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            camera_surface = pygame.surfarray.make_surface(np.swapaxes(camera_frame_rgb, 0, 1))
            camera_surface = pygame.transform.scale(camera_surface, (120, 90))

            camera_x = self.w - 130
            camera_y = 52

            pygame.draw.rect(self.screen, (255, 255, 255), (camera_x - 2, camera_y - 2, 124, 94), 2, border_radius=6)
            self.screen.blit(camera_surface, (camera_x, camera_y))

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

        pill_w = 184
        pill_h = 32
        pill_x = self.w - pill_w - 12
        pill_y = 10

        # Semi-transparent background with progress indicator
        pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
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
        else:
            # Clean, always-visible mouse / targeting cursor so cursor never disappears!
            pygame.draw.circle(self.screen, (255, 255, 255), self.cursor_pos, 13, 2)
            pygame.draw.circle(self.screen, (56, 189, 248), self.cursor_pos, 4)
            # Subtle crosshair pings
            cx, cy = self.cursor_pos
            pygame.draw.line(self.screen, (255, 255, 255), (cx - 17, cy), (cx - 13, cy), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (cx + 13, cy), (cx + 17, cy), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, cy - 17), (cx, cy - 13), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (cx, cy + 13), (cx, cy + 17), 2)

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

            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 60))
            self.screen.blit(overlay, (0, 0))

            # TITLE
            for offset in range(3, 0, -1):
                glow = self.title_font.render("COGNITIVE PLAY", True, (255, 255, 150))
                tx = self.w // 2 - glow.get_width() // 2
                self.screen.blit(glow, (tx, self.title_y - offset))

            title = self.title_font.render("COGNITIVE PLAY", True, (255, 255, 255))
            title_shadow = self.title_font.render("COGNITIVE PLAY", True, (0, 0, 0))
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
                dialogue_surface = pygame.Surface((self.dialogue_box_width, self.dialogue_box_height))
                dialogue_surface.fill((255, 255, 255))
                dialogue_surface.set_alpha(240)
                self.screen.blit(dialogue_surface, (self.dialogue_box_x, self.dialogue_box_y))

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

            # SELECTED STUDENT INFO
            if self.selected_student:
                student_name = f"{self.selected_student['first_name']} {self.selected_student['last_name']}"
                info_bg = pygame.Surface((400, 40))
                info_bg.fill((0, 0, 0))
                info_bg.set_alpha(180)
                self.screen.blit(info_bg, (self.w // 2 - 200, self.student_info_y))
                student_text = self.small_font.render(f"Selected Student: {student_name}", True, (255, 215, 0))
                self.screen.blit(student_text, (self.w // 2 - student_text.get_width() // 2, self.student_info_y + 5))

            # ERROR MESSAGE (commented out for testing)
            if self.show_no_student_message and pygame.time.get_ticks() < self.no_student_timer:
                error_bg = pygame.Surface((380, 45))
                error_bg.fill((231, 76, 60))
                error_bg.set_alpha(220)
                self.screen.blit(error_bg, (self.w // 2 - 190, self.error_y))
                msg = self.small_font.render("Please select a student first!", True, (255, 255, 255))
                self.screen.blit(msg, (self.w // 2 - msg.get_width() // 2, self.error_y + 12))
            else:
                self.show_no_student_message = False

            # DRAW BUTTONS
            for b in self.buttons:
                b.draw(self.screen)

            self.draw_camera_feed()

        elif self.current_screen == "stage_select" and self.stage_select:
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