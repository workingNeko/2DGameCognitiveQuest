# screens/tutorial.py - Interactive New Player Tutorial for Controls & Gameplay
import pygame
import os
import sys
import math
import time

class TutorialScreen:
    def __init__(self, screen, main_menu):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()

        # Gesture tracking state
        self.cursor_pos = (self.width // 2, self.height // 2)
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False
        self.hand_detected = False

        # Tutorial slide index (0 to 4)
        self.current_slide = 0
        self.total_slides = 5

        # Interactive practice state (Slide 4)
        self.practice_charge = 0.0
        self.practice_completed = False
        self.practice_pulse_timer = 0.0

        # Animation timer
        self.anim_timer = 0.0

        # Fonts
        self.title_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 34, bold=True)
        self.subtitle_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 22, bold=True)
        self.body_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18)
        self.bold_body_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18, bold=True)
        self.badge_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 14, bold=True)
        self.button_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18, bold=True)

        # Background
        bg_path = os.path.join("assets", "images", "menu_background.png")
        if os.path.exists(bg_path):
            try:
                raw_bg = pygame.image.load(bg_path).convert()
                self.bg_image = pygame.transform.scale(raw_bg, (self.width, self.height))
            except Exception:
                self.bg_image = None
        else:
            self.bg_image = None

        print("🎓 Tutorial Screen Initialized!")

    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        """Receives gesture data from main menu"""
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME
        self.current_gesture = current_gesture
        self.hand_detected = (current_gesture not in ["NO HAND", "NO HAND (GRACE)"])

    def update(self):
        """Update animation and interactive practice"""
        self.anim_timer += 0.05
        self.practice_pulse_timer += 0.08

        # If on Slide 4 (Interactive Practice), check if cursor is over the practice target
        if self.current_slide == 4 and not self.practice_completed:
            box_w, box_h = min(960, self.width - 80), min(600, self.height - 80)
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2

            target_center = (box_x + box_w // 2, box_y + 270)
            dist = math.hypot(self.cursor_pos[0] - target_center[0], self.cursor_pos[1] - target_center[1])

            if dist < 65 and self.fist_start_time > 0:
                # Charging up with fist hold
                hold_time = time.time() - self.fist_start_time
                self.practice_charge = min(1.0, hold_time / self.CLICK_HOLD_TIME)
                if self.practice_charge >= 1.0:
                    self.practice_completed = True
                    print("🎉 Interactive Practice Completed!")
            elif dist < 65 and pygame.mouse.get_pressed()[0]:
                # Mouse hold fallback
                self.practice_charge = min(1.0, self.practice_charge + 0.03)
                if self.practice_charge >= 1.0:
                    self.practice_completed = True
                    print("🎉 Interactive Practice Completed via Mouse!")
            else:
                if self.practice_charge < 1.0:
                    self.practice_charge = max(0.0, self.practice_charge - 0.04)

    def handle_event(self, event):
        """Handle keyboard & mouse events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.trigger_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
                self.next_slide()
            elif event.key == pygame.K_LEFT:
                self.prev_slide()
            elif event.key == pygame.K_ESCAPE:
                self.finish_tutorial()

    def trigger_click(self, pos=None):
        """Handle click at cursor position"""
        if pos is None:
            pos = self.cursor_pos

        box_w, box_h = min(960, self.width - 80), min(600, self.height - 80)
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # 1. Skip Button (Top Right)
        skip_rect = pygame.Rect(box_x + box_w - 180, box_y + 14, 160, 40)
        if skip_rect.collidepoint(pos):
            self.finish_tutorial()
            return

        # 2. Tab Headers (Click to jump to any slide)
        tab_w = (box_w - 60) // self.total_slides
        for i in range(self.total_slides):
            t_rect = pygame.Rect(box_x + 30 + i * tab_w, box_y + 64, tab_w - 8, 36)
            if t_rect.collidepoint(pos):
                self.current_slide = i
                return

        # 3. Bottom Navigation Buttons
        btn_y = box_y + box_h - 60
        prev_rect = pygame.Rect(box_x + 30, btn_y, 140, 44)
        next_rect = pygame.Rect(box_x + box_w - 170, btn_y, 140, 44)
        start_rect = pygame.Rect(box_x + box_w - 220, btn_y, 190, 44)

        if self.current_slide > 0 and prev_rect.collidepoint(pos):
            self.prev_slide()
            return

        if self.current_slide < self.total_slides - 1 and next_rect.collidepoint(pos):
            self.next_slide()
            return

        if (self.current_slide == self.total_slides - 1 or self.practice_completed) and start_rect.collidepoint(pos):
            self.finish_tutorial()
            return

        # Interactive practice orb click
        if self.current_slide == 4:
            target_center = (box_x + box_w // 2, box_y + 270)
            dist = math.hypot(pos[0] - target_center[0], pos[1] - target_center[1])
            if dist < 65:
                self.practice_completed = True

    def next_slide(self):
        if self.current_slide < self.total_slides - 1:
            self.current_slide += 1
        else:
            self.finish_tutorial()

    def prev_slide(self):
        if self.current_slide > 0:
            self.current_slide -= 1

    def finish_tutorial(self):
        """Saves tutorial completion and proceeds to Stage Select"""
        from db.save_system import set_tutorial_completed
        student_id = getattr(self.main_menu, 'student_id', None)
        if student_id:
            set_tutorial_completed(self.main_menu, student_id, completed=True)

        print("🚀 Tutorial Finished! Opening Stage Select...")
        from screens.stageselect import StageSelect
        self.main_menu.current_screen = "stage_select"
        self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)

    # ============================================================
    # DRAWING ROUTINES
    # ============================================================
    def draw(self):
        # 1. Background
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill((15, 23, 42))

        # Dim overlay
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        # 2. Main Parchment Container Box
        box_w, box_h = min(960, self.width - 80), min(600, self.height - 80)
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        main_box = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), main_box, border_radius=16)
        pygame.draw.rect(self.screen, (245, 158, 11), main_box, 3, border_radius=16)
        pygame.draw.rect(self.screen, (251, 191, 36), main_box.inflate(-6, -6), 1, border_radius=12)

        # 3. Header Bar
        title_surf = self.title_font.render("COGNITIVE PLAY: HOW TO PLAY", True, (255, 215, 0))
        self.screen.blit(title_surf, (box_x + 30, box_y + 16))

        # Skip Button (Top Right)
        skip_rect = pygame.Rect(box_x + box_w - 180, box_y + 14, 160, 40)
        skip_hov = skip_rect.collidepoint(self.cursor_pos)
        skip_bg = (220, 38, 38) if skip_hov else (30, 41, 59)
        pygame.draw.rect(self.screen, skip_bg, skip_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 215, 0) if skip_hov else (203, 213, 225), skip_rect, 2, border_radius=10)
        skip_txt = self.button_font.render("SKIP TUTORIAL >>", True, (255, 255, 255))
        self.screen.blit(skip_txt, skip_txt.get_rect(center=skip_rect.center))

        # 4. Slide Progress Tabs (Top)
        tab_names = ["1. Hand Steering", "2. Fist Click", "3. Objective Compass", "4. Quiz & Rewards", "5. Quick Practice"]
        tab_w = (box_w - 60) // self.total_slides
        for i, tname in enumerate(tab_names):
            t_rect = pygame.Rect(box_x + 30 + i * tab_w, box_y + 64, tab_w - 8, 36)
            is_active = (i == self.current_slide)
            is_hov = t_rect.collidepoint(self.cursor_pos)

            if is_active:
                bg_col = (245, 158, 11)
                txt_col = (15, 23, 42)
                border_col = (255, 255, 255)
            elif is_hov:
                bg_col = (51, 65, 85)
                txt_col = (255, 255, 255)
                border_col = (245, 158, 11)
            else:
                bg_col = (30, 41, 59)
                txt_col = (148, 163, 184)
                border_col = (71, 85, 105)

            pygame.draw.rect(self.screen, bg_col, t_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_col, t_rect, 1 if not is_active else 2, border_radius=8)

            lbl = self.badge_font.render(tname, True, txt_col)
            self.screen.blit(lbl, lbl.get_rect(center=t_rect.center))

        # 5. Content Area based on Slide
        content_rect = pygame.Rect(box_x + 30, box_y + 115, box_w - 60, box_h - 190)
        pygame.draw.rect(self.screen, (20, 29, 48), content_rect, border_radius=12)
        pygame.draw.rect(self.screen, (51, 65, 85), content_rect, 1, border_radius=12)

        if self.current_slide == 0:
            self.draw_slide_hand_steering(content_rect)
        elif self.current_slide == 1:
            self.draw_slide_fist_click(content_rect)
        elif self.current_slide == 2:
            self.draw_slide_compass_radar(content_rect)
        elif self.current_slide == 3:
            self.draw_slide_quiz_progression(content_rect)
        elif self.current_slide == 4:
            self.draw_slide_interactive_practice(content_rect)

        # 6. Bottom Navigation Controls
        btn_y = box_y + box_h - 58
        if self.current_slide > 0:
            prev_rect = pygame.Rect(box_x + 30, btn_y, 140, 42)
            prev_hov = prev_rect.collidepoint(self.cursor_pos)
            pygame.draw.rect(self.screen, (30, 41, 59) if not prev_hov else (51, 65, 85), prev_rect, border_radius=8)
            pygame.draw.rect(self.screen, (148, 163, 184), prev_rect, 1, border_radius=8)
            p_txt = self.button_font.render("< Previous", True, (255, 255, 255))
            self.screen.blit(p_txt, p_txt.get_rect(center=prev_rect.center))

        if self.current_slide < self.total_slides - 1:
            next_rect = pygame.Rect(box_x + box_w - 170, btn_y, 140, 42)
            next_hov = next_rect.collidepoint(self.cursor_pos)
            pygame.draw.rect(self.screen, (245, 158, 11) if not next_hov else (251, 191, 36), next_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), next_rect, 2, border_radius=8)
            n_txt = self.button_font.render("Next Step >", True, (15, 23, 42))
            self.screen.blit(n_txt, n_txt.get_rect(center=next_rect.center))
        else:
            start_rect = pygame.Rect(box_x + box_w - 220, btn_y, 190, 42)
            start_hov = start_rect.collidepoint(self.cursor_pos)
            bg_start = (34, 197, 94) if not start_hov else (74, 222, 128)
            pygame.draw.rect(self.screen, bg_start, start_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 2, border_radius=8)
            s_txt = self.button_font.render("Start Adventure! >>", True, (15, 23, 42))
            self.screen.blit(s_txt, s_txt.get_rect(center=start_rect.center))

    # ============================================================
    # SLIDE 1: HAND STEERING & CURSOR
    # ============================================================
    def draw_slide_hand_steering(self, rect):
        # Header
        h_surf = self.subtitle_font.render("🖐️ Hand Movement & Directional Steering", True, (255, 215, 0))
        self.screen.blit(h_surf, (rect.left + 30, rect.top + 20))

        # Left Column: Instructions
        lines = [
            "1. Stand or sit in front of your camera.",
            "2. Move your open hand to steer the on-screen cursor.",
            "3. Directional Steering: Move your hand away from the center to make",
            "   your character walk in that direction (Left, Right, Up, Down).",
            "4. The further you stretch your hand, the faster your character walks!",
            "5. The camera tracks your character smoothly through the quest world."
        ]
        y_off = rect.top + 65
        for line in lines:
            col = (255, 255, 255) if not line.startswith("   ") else (203, 213, 225)
            fnt = self.bold_body_font if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") else self.body_font
            txt = fnt.render(line, True, col)
            self.screen.blit(txt, (rect.left + 30, y_off))
            y_off += 28

        # Right Column: Visual Diagram
        diag_rect = pygame.Rect(rect.right - 280, rect.top + 40, 250, 220)
        pygame.draw.rect(self.screen, (15, 23, 42), diag_rect, border_radius=12)
        pygame.draw.rect(self.screen, (245, 158, 11), diag_rect, 2, border_radius=12)

        cx, cy = diag_rect.centerx, diag_rect.centery
        # Directional compass circle
        pygame.draw.circle(self.screen, (51, 65, 85), (cx, cy), 65, 2)
        pygame.draw.circle(self.screen, (245, 158, 11), (cx, cy), 15, 2)

        # Floating Hand Indicator animation
        h_x = cx + math.cos(self.anim_timer) * 45
        h_y = cy + math.sin(self.anim_timer) * 45
        pygame.draw.line(self.screen, (251, 191, 36), (cx, cy), (int(h_x), int(h_y)), 2)
        pygame.draw.circle(self.screen, (255, 215, 0), (int(h_x), int(h_y)), 12)
        pygame.draw.circle(self.screen, (255, 255, 255), (int(h_x), int(h_y)), 12, 2)

        diag_lbl = self.badge_font.render("Move Hand to Walk", True, (254, 240, 138))
        self.screen.blit(diag_lbl, diag_lbl.get_rect(center=(cx, diag_rect.bottom - 20)))

    # ============================================================
    # SLIDE 2: FIST CLICK & INTERACTIONS
    # ============================================================
    def draw_slide_fist_click(self, rect):
        h_surf = self.subtitle_font.render("✊ Fist Click & Interaction Gestures", True, (255, 215, 0))
        self.screen.blit(h_surf, (rect.left + 30, rect.top + 20))

        lines = [
            "1. Hover your cursor over buttons, challenge NPCs, or answer choices.",
            "2. Make a FIST (close all fingers into your palm) to begin clicking.",
            "3. Hold your fist closed for 0.9 seconds to confirm your selection!",
            "   A yellow charging ring will fill up to show your progress.",
            "4. Peace Sign (✌️): Hold a peace sign gesture anytime to trigger quick",
            "   pause / main menu confirmation."
        ]
        y_off = rect.top + 65
        for line in lines:
            col = (255, 255, 255) if not line.startswith("   ") else (203, 213, 225)
            fnt = self.bold_body_font if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") else self.body_font
            txt = fnt.render(line, True, col)
            self.screen.blit(txt, (rect.left + 30, y_off))
            y_off += 28

        # Visual Diagram
        diag_rect = pygame.Rect(rect.right - 280, rect.top + 40, 250, 220)
        pygame.draw.rect(self.screen, (15, 23, 42), diag_rect, border_radius=12)
        pygame.draw.rect(self.screen, (34, 197, 94), diag_rect, 2, border_radius=12)

        cx, cy = diag_rect.centerx, diag_rect.centery - 10
        # Button mock
        btn_mock = pygame.Rect(cx - 75, cy - 25, 150, 50)
        pygame.draw.rect(self.screen, (245, 158, 11), btn_mock, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_mock, 2, border_radius=8)
        b_txt = self.badge_font.render("SELECT OPTION", True, (15, 23, 42))
        self.screen.blit(b_txt, b_txt.get_rect(center=btn_mock.center))

        # Animated Fist Cursor & Progress Ring
        charge_pct = (math.sin(self.anim_timer * 1.5) + 1) / 2
        pygame.draw.circle(self.screen, (255, 255, 255), (cx + 40, cy + 20), 16, 2)
        pygame.draw.circle(self.screen, (255, 215, 0), (cx + 40, cy + 20), int(16 * charge_pct))

        diag_lbl = self.badge_font.render("Hold Fist (0.9s) to Select", True, (74, 222, 128))
        self.screen.blit(diag_lbl, diag_lbl.get_rect(center=(cx, diag_rect.bottom - 20)))

    # ============================================================
    # SLIDE 3: OBJECTIVE COMPASS & RADAR
    # ============================================================
    def draw_slide_compass_radar(self, rect):
        h_surf = self.subtitle_font.render("📍 Objective Badges & Off-Screen Compass Radar", True, (255, 215, 0))
        self.screen.blit(h_surf, (rect.left + 30, rect.top + 20))

        lines = [
            "1. On-Screen Quest Badges: Active challenge NPCs display a bouncing yellow",
            "   diamond '!' badge and name tag above them.",
            "2. Off-Screen Compass Pointer: If your target is far away across the map,",
            "   a gold directional radar pill shows you the direction & distance:",
            "   Example: >> Circle Guardian (15m)",
            "3. Exit Portals: When all stage challenges are cleared, an emerald green",
            "   compass pointer guides you directly to the unlocked Exit Portal!"
        ]
        y_off = rect.top + 65
        for line in lines:
            col = (255, 255, 255) if not line.startswith("   ") else (203, 213, 225)
            fnt = self.bold_body_font if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") else self.body_font
            txt = fnt.render(line, True, col)
            self.screen.blit(txt, (rect.left + 30, y_off))
            y_off += 28

        # Visual Diagram showing Radar Pointers
        diag_rect = pygame.Rect(rect.right - 280, rect.top + 40, 250, 220)
        pygame.draw.rect(self.screen, (15, 23, 42), diag_rect, border_radius=12)
        pygame.draw.rect(self.screen, (245, 158, 11), diag_rect, 2, border_radius=12)

        cx, cy = diag_rect.centerx, diag_rect.centery - 15

        # Gold Station Pointer Mock
        p1_rect = pygame.Rect(cx - 100, cy - 35, 200, 32)
        pygame.draw.rect(self.screen, (255, 215, 0), p1_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), p1_rect, 2, border_radius=8)
        p1_txt = self.badge_font.render(">> Station NPC (12m)", True, (15, 23, 42))
        self.screen.blit(p1_txt, p1_txt.get_rect(center=p1_rect.center))

        # Green Exit Portal Pointer Mock
        p2_rect = pygame.Rect(cx - 100, cy + 15, 200, 32)
        pygame.draw.rect(self.screen, (74, 222, 128), p2_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), p2_rect, 2, border_radius=8)
        p2_txt = self.badge_font.render(">> Exit Portal (18m)", True, (15, 23, 42))
        self.screen.blit(p2_txt, p2_txt.get_rect(center=p2_rect.center))

        diag_lbl = self.badge_font.render("Follow Dynamic Radar Pointers", True, (254, 240, 138))
        self.screen.blit(diag_lbl, diag_lbl.get_rect(center=(cx, diag_rect.bottom - 20)))

    # ============================================================
    # SLIDE 4: QUIZ & 2-ATTEMPT GUARANTEED PROGRESSION
    # ============================================================
    def draw_slide_quiz_progression(self, rect):
        h_surf = self.subtitle_font.render("⭐ 2-Attempt Quiz Rule & Guaranteed Progression", True, (255, 215, 0))
        self.screen.blit(h_surf, (rect.left + 30, rect.top + 20))

        lines = [
            "1. Approach challenge NPCs to open clean multiple-choice math questions.",
            "2. Attempt 1 (Try Your Best): If you answer correctly, you receive instant",
            "   praise and a quest artifact (Jigsaw Piece, Bahay Kubo, Keystone)!",
            "3. Attempt 2 (Gentle Retry): If incorrect on try 1, you get a friendly retry",
            "   screen to review the choices and try one more time.",
            "4. Guaranteed Progression: Even after 2 tries, the correct answer is revealed",
            "   and you STILL receive the quest reward so your adventure never stops!"
        ]
        y_off = rect.top + 65
        for line in lines:
            col = (255, 255, 255) if not line.startswith("   ") else (203, 213, 225)
            fnt = self.bold_body_font if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") else self.body_font
            txt = fnt.render(line, True, col)
            self.screen.blit(txt, (rect.left + 30, y_off))
            y_off += 28

        # Visual Diagram
        diag_rect = pygame.Rect(rect.right - 280, rect.top + 40, 250, 220)
        pygame.draw.rect(self.screen, (15, 23, 42), diag_rect, border_radius=12)
        pygame.draw.rect(self.screen, (245, 158, 11), diag_rect, 2, border_radius=12)

        cx, cy = diag_rect.centerx, diag_rect.centery - 10
        # Retry card mock
        r_box = pygame.Rect(cx - 90, cy - 30, 180, 60)
        pygame.draw.rect(self.screen, (30, 41, 59), r_box, border_radius=8)
        pygame.draw.rect(self.screen, (245, 158, 11), r_box, 2, border_radius=8)
        r_txt1 = self.badge_font.render("Attempt 1: Retry Feedback", True, (255, 215, 0))
        r_txt2 = self.badge_font.render("Attempt 2: Solution Reveal", True, (74, 222, 128))
        self.screen.blit(r_txt1, (r_box.left + 10, r_box.top + 10))
        self.screen.blit(r_txt2, (r_box.left + 10, r_box.top + 32))

        diag_lbl = self.badge_font.render("Guaranteed Quest Progression", True, (254, 240, 138))
        self.screen.blit(diag_lbl, diag_lbl.get_rect(center=(cx, diag_rect.bottom - 20)))

    # ============================================================
    # SLIDE 5: INTERACTIVE GESTURE PRACTICE
    # ============================================================
    def draw_slide_interactive_practice(self, rect):
        h_surf = self.subtitle_font.render("🎯 Practice Your Fist Click Gesture!", True, (255, 215, 0))
        self.screen.blit(h_surf, (rect.left + 30, rect.top + 20))

        sub_txt = self.body_font.render("Move your cursor over the Power Orb below and HOLD A FIST for 0.9s to charge it up:", True, (241, 245, 249))
        self.screen.blit(sub_txt, (rect.left + 30, rect.top + 60))

        cx, cy = rect.centerx, rect.top + 155

        # Glowing Power Orb Target
        pulse = math.sin(self.practice_pulse_timer) * 4
        orb_r = int(50 + pulse)

        if self.practice_completed:
            orb_col = (34, 197, 94)
            border_col = (255, 255, 255)
            label_text = "GREAT JOB! READY!"
        else:
            orb_col = (30, 58, 138) if self.practice_charge < 0.1 else (245, 158, 11)
            border_col = (251, 191, 36)
            label_text = f"HOLD FIST {int(self.practice_charge * 100)}%"

        # Outer charging ring
        pygame.draw.circle(self.screen, (51, 65, 85), (cx, cy), orb_r + 12, 4)
        if self.practice_charge > 0 or self.practice_completed:
            charged_r = orb_r + 12
            pygame.draw.circle(self.screen, (34, 197, 94) if self.practice_completed else (255, 215, 0), (cx, cy), charged_r, 4)

        # Orb Center
        pygame.draw.circle(self.screen, orb_col, (cx, cy), orb_r)
        pygame.draw.circle(self.screen, border_col, (cx, cy), orb_r, 3)

        o_lbl = self.bold_body_font.render(label_text, True, (255, 255, 255))
        self.screen.blit(o_lbl, o_lbl.get_rect(center=(cx, cy)))

        # Status Banner
        if self.practice_completed:
            status_txt = self.subtitle_font.render("✨ You have mastered the gesture controls! Click 'Start Adventure' below to begin.", True, (74, 222, 128))
            self.screen.blit(status_txt, status_txt.get_rect(center=(cx, rect.bottom - 30)))
        else:
            status_txt = self.body_font.render("(You can also click the orb or click 'Start Adventure' whenever you are ready)", True, (148, 163, 184))
            self.screen.blit(status_txt, status_txt.get_rect(center=(cx, rect.bottom - 30)))
