# screens/main_menu.py - USING WRIST FOR STABLE CURSOR

import pygame
import cv2
import mediapipe as mp
import numpy as np
import os
import time
from ui.button import Button
from screens.stageselect import StageSelect
from screens.studentselect import StudentSelect
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4


class MainMenu:

    def __init__(self, screen):

        self.screen = screen
        self.w, self.h = screen.get_size()

        # ==========================================
        # SIMPLE GESTURE DETECTION
        # ==========================================

        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Camera setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.camera_size = (160, 120)
        print("✅ Camera initialized!")

        # Gesture state
        self.current_gesture = "NO HAND"
        self.cursor_pos = (self.w // 2, self.h // 2)
        self.camera_frame = None

        # Click tracking
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False

        # Cursor smoothing - USING WRIST (landmark 0) for stability
        self.cursor_x = float(self.w // 2)
        self.cursor_y = float(self.h // 2)

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
        # MUSIC
        # ==========================================

        self.bg_music = "assets/sounds/backgroundgamesoundloop.wav"
        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.load(self.bg_music)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
            except:
                print("Music not found.")

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

        bw = 300
        bh = 70
        gap = 20

        total_height = (bh * 2) + gap
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

        self.exit_btn = Button(
            (30, 30, 200, 70),
            text="",
            font=self.button_font,
            bg_color=None,
            text_color=(255, 255, 255),
            action=self.exit_game,
            image_path=exit_btn_path
        )

        self.buttons = [self.select_student_btn, self.start_activity_btn, self.exit_btn]

        self.title_y = 40
        self.student_info_y = self.h - 90
        self.error_y = self.h - 150

        # ==========================================
        # SCREEN STATES
        # ==========================================

        self.current_screen = "menu"
        self.stage_select = None
        self.student_select = None
        self.quarter1 = None
        self.quarter2 = None
        self.quarter3 = None
        self.quarter4 = None

        # ==========================================
        # MESSAGES
        # ==========================================

        self.show_no_student_message = False
        self.no_student_timer = 0

        print(f"🎮 Simple Gesture Control Active!")
        print(f"   - WRIST movement controls cursor (stable when making fist)")
        print(f"   - Make a FIST and hold for {self.CLICK_HOLD_TIME} seconds to click")

    # ==========================================
    # SIMPLE FIST DETECTION (USING FINGER TIPS)
    # ==========================================

    def is_fist(self, hand_landmarks):
        """Simple fist detection - checks if fingers are closed"""
        # Check if finger tips are below knuckles (closed)
        fingers = [
            hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y,  # Index
            hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y,  # Middle
            hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y,  # Ring
            hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y  # Pinky
        ]

        # If 3 or more fingers are closed, it's a fist
        return sum(fingers) >= 3

    def update_gesture(self):
        """Update gesture detection - USING WRIST FOR CURSOR (landmark 0)"""
        ret, img = self.cap.read()
        if not ret:
            return

        img = cv2.flip(img, 1)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Store camera frame for display
        self.camera_frame = cv2.resize(img, self.camera_size)

        results = self.hands.process(rgb)

        hand_detected = False

        if results.multi_hand_landmarks:
            hand_detected = True
            self.last_hand_time = time.time()

            for hand_landmarks in results.multi_hand_landmarks:
                # USE WRIST (landmark 0) FOR CURSOR - THIS WON'T MOVE WHEN YOU MAKE A FIST!
                wrist = hand_landmarks.landmark[0]

                # Map wrist position to screen coordinates
                target_x = np.interp(wrist.x, [0.1, 0.9], [0, self.w])
                target_y = np.interp(wrist.y, [0.1, 0.9], [0, self.h])

                # Smooth cursor movement
                smooth = .50
                self.cursor_x = self.cursor_x * (1 - smooth) + target_x * smooth
                self.cursor_y = self.cursor_y * (1 - smooth) + target_y * smooth
                self.cursor_pos = (int(self.cursor_x), int(self.cursor_y))

                # Store last position for grace period
                self.last_cursor_x = self.cursor_x
                self.last_cursor_y = self.cursor_y

                # Detect if fist is closed (using finger tips)
                fist_detected = self.is_fist(hand_landmarks)

                if fist_detected:
                    if self.fist_start_time == 0:
                        self.fist_start_time = time.time()
                        print("👊 Fist detected! Hold to click...")

                    hold_time = time.time() - self.fist_start_time

                    if hold_time >= self.CLICK_HOLD_TIME and not self.click_ready:
                        self.click_ready = True
                        print(f"✅ CLICK! (Held for {hold_time:.1f}s)")
                        self.trigger_click()
                else:
                    if self.fist_start_time != 0:
                        print("✋ Fist released")
                    self.fist_start_time = 0
                    self.click_ready = False

                self.current_gesture = "FIST" if fist_detected else "OPEN"

        # HAND GRACE PERIOD - keep cursor position for a while after hand is lost
        if not hand_detected:
            elapsed = time.time() - self.last_hand_time
            if elapsed < self.HAND_GRACE:
                # Keep last cursor position
                self.cursor_pos = (int(self.last_cursor_x), int(self.last_cursor_y))
                self.current_gesture = "NO HAND (GRACE)"
            else:
                self.current_gesture = "NO HAND"
                self.fist_start_time = 0
                self.click_ready = False

    # ==========================================
    # CLICK HANDLER
    # ==========================================

    def trigger_click(self):
        """Handle click at cursor position"""
        pos = self.cursor_pos
        print(f"🖱️ Click at: {pos}")

        # Route click to active screen if not in menu
        if self.current_screen == "stage_select" and self.stage_select:
            self.stage_select.trigger_click(pos)
            return
        elif self.current_screen == "student_select" and self.student_select:
            self.student_select.trigger_click(pos)
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

        # Check dialogue box first
        if self.dialogue_active and self.dialogue_rect.collidepoint(pos):
            print("💬 Dialogue clicked!")
            self.next_dialogue()
            return

        # Check buttons
        for button in self.buttons:
            if button.rect.collidepoint(pos):
                name = button.text if hasattr(button, 'text') and button.text else "EXIT"
                print(f"🔘 Button clicked: {name}")
                if button.action:
                    button.action()
                return

        print("❌ Nothing clicked")

    def next_dialogue(self):
        """Go to next dialogue line"""
        self.current_line += 1
        if self.current_line >= len(self.dialogue_lines):
            self.dialogue_active = False
            print("✅ Dialogue finished!")
        else:
            print(f"📖 Next: {self.dialogue_lines[self.current_line]}")

    # ==========================================
    # BUTTON ACTIONS
    # ==========================================

    def select_student(self):
        print(f"📋 SELECT STUDENT clicked!")
        self.current_screen = "student_select"
        self.student_select = StudentSelect(self.screen, self)

    def start_activity(self):
        print(f"🎮 START ACTIVITY clicked!")
        # COMMENTED OUT: Student select requirement for testing
        # if not self.selected_student:
        #     self.show_no_student_message = True
        #     self.no_student_timer = pygame.time.get_ticks() + 2000
        #     return
        self.current_screen = "stage_select"
        self.stage_select = StageSelect(self.screen, self)

    def exit_game(self):
        print("🚪 EXIT clicked!")
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
        self.cap.release()
        cv2.destroyAllWindows()
        pygame.quit()
        raise SystemExit

    # ==========================================
    # UPDATE
    # ==========================================

    def update(self):
        if self.current_screen == "menu":
            self.update_gesture()

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
                self.student_select.update()

        elif self.current_screen == "quarter1" and self.quarter1:
            self.update_gesture()
            if self.quarter1:
                self.quarter1.update_gesture(
                    self.cursor_pos,
                    self.fist_start_time,
                    self.CLICK_HOLD_TIME,
                    self.current_gesture
                )
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
                self.quarter4.update()

    def handle_event(self, event):
        if self.current_screen == "menu":
            pass
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

    # ==========================================
    # DRAW
    # ==========================================

    def draw_camera_feed(self):
        if self.camera_frame is not None:
            camera_frame_rgb = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            camera_surface = pygame.surfarray.make_surface(np.swapaxes(camera_frame_rgb, 0, 1))
            camera_surface = pygame.transform.scale(camera_surface, (120, 90))

            camera_x = self.w - 130
            camera_y = 10

            pygame.draw.rect(self.screen, (255, 255, 255), (camera_x - 2, camera_y - 2, 124, 94), 3, border_radius=5)
            self.screen.blit(camera_surface, (camera_x, camera_y))

            # Show gesture and progress
            if self.fist_start_time > 0:
                hold_time = time.time() - self.fist_start_time
                progress = min(100, (hold_time / self.CLICK_HOLD_TIME) * 100)

                bar_width = 100
                bar_height = 8
                bar_x = camera_x + 10
                bar_y = camera_y + 90 - 15
                pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * progress / 100), bar_height))

                text = self.small_font.render(f"HOLD {int(progress)}%", True, (255, 255, 0))
                text_x = camera_x + (120 - text.get_width()) // 2
                text_y = camera_y + 90 - 35
                self.screen.blit(text, (text_x, text_y))

            gesture_text = self.small_font.render(self.current_gesture, True, (0, 255, 0))
            text_x = camera_x + (120 - gesture_text.get_width()) // 2
            text_y = camera_y + 5
            self.screen.blit(gesture_text, (text_x, text_y))

    def draw_cursor(self):
        if self.current_gesture != "NO HAND":
            if self.fist_start_time > 0:
                color = (255, 200, 0)  # Yellow when holding fist
            else:
                color = (255, 255, 255)  # White normally

            pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
            pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

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
                student_text = self.small_font.render(f"✓ Selected: {student_name}", True, (255, 215, 0))
                self.screen.blit(student_text, (self.w // 2 - student_text.get_width() // 2, self.student_info_y + 5))

            # ERROR MESSAGE (commented out for testing)
            if self.show_no_student_message and pygame.time.get_ticks() < self.no_student_timer:
                error_bg = pygame.Surface((380, 45))
                error_bg.fill((231, 76, 60))
                error_bg.set_alpha(220)
                self.screen.blit(error_bg, (self.w // 2 - 190, self.error_y))
                msg = self.small_font.render("⚠ Please select a student first!", True, (255, 255, 255))
                self.screen.blit(msg, (self.w // 2 - msg.get_width() // 2, self.error_y + 8))
            else:
                self.show_no_student_message = False

            # DRAW CAMERA FEED & CURSOR
            self.draw_camera_feed()
            self.draw_cursor()

            # DRAW BUTTONS
            for b in self.buttons:
                b.draw(self.screen)

        elif self.current_screen == "stage_select" and self.stage_select:
            self.stage_select.draw()
            self.draw_camera_feed()
            # Draw cursor on top
            if self.current_gesture != "NO HAND":
                if self.fist_start_time > 0:
                    color = (255, 200, 0)
                else:
                    color = (255, 255, 255)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        elif self.current_screen == "student_select" and self.student_select:
            self.student_select.draw()
            self.draw_camera_feed()
            # Draw cursor on top
            if self.current_gesture != "NO HAND":
                if self.fist_start_time > 0:
                    color = (255, 200, 0)
                else:
                    color = (255, 255, 255)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        elif self.current_screen == "quarter1" and self.quarter1:
            self.quarter1.draw()
            self.draw_camera_feed()
            # Draw cursor on top
            if self.current_gesture != "NO HAND":
                if self.fist_start_time > 0:
                    color = (255, 200, 0)
                else:
                    color = (255, 255, 255)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        elif self.current_screen == "quarter2" and self.quarter2:
            self.quarter2.draw()
            self.draw_camera_feed()
            # Draw cursor on top
            if self.current_gesture != "NO HAND":
                if self.fist_start_time > 0:
                    color = (255, 200, 0)
                else:
                    color = (255, 255, 255)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        elif self.current_screen == "quarter3" and self.quarter3:
            self.quarter3.draw()
            self.draw_camera_feed()
            # Draw cursor on top
            if self.current_gesture != "NO HAND":
                if self.fist_start_time > 0:
                    color = (255, 200, 0)
                else:
                    color = (255, 255, 255)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        elif self.current_screen == "quarter4" and self.quarter4:
            self.quarter4.draw()
            self.draw_camera_feed()
            # Draw cursor on top
            if self.current_gesture != "NO HAND":
                if self.fist_start_time > 0:
                    color = (255, 200, 0)
                else:
                    color = (255, 255, 255)
                pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
                pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)