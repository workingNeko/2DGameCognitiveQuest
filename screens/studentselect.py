import pygame
import os
import json
import time

# Import db - make sure this exists in your project
try:
    from db import db
except ImportError:
    # Fallback for testing without database
    db = None
    print("Warning: db module not found, using mock data for testing")


class StudentSelect:
    def __init__(self, screen, main_menu):
        self.screen = screen
        self.main_menu = main_menu

        self.width, self.height = screen.get_size()

        # =====================================================
        # GESTURE SYSTEM (ADDED)
        # =====================================================
        self.cursor_pos = (self.width // 2, self.height // 2)
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.3
        self.click_ready = False

        # For tracking clicks to prevent multiple triggers
        self.last_click_time = -10.0
        self.click_cooldown = 0.2  # seconds between clicks

        # =====================================================
        # BACKGROUND
        # =====================================================
        bg_path = os.path.join("assets", "images", "menu_background.png")

        if os.path.exists(bg_path):
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
        else:
            self.bg_image = None

        # =====================================================
        # FONTS
        # =====================================================
        self.title_font = pygame.font.SysFont("Comic Sans MS", 54, bold=True)
        self.font = pygame.font.SysFont("Comic Sans MS", 28)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 20)

        # =====================================================
        # COLORS
        # =====================================================
        self.TEXT_COLOR = (40, 40, 90)
        self.BORDER_COLOR = (110, 130, 180)
        self.BUTTON_COLOR = (70, 100, 170)
        self.BUTTON_HOVER = (100, 130, 210)
        self.GREEN = (120, 255, 150)
        self.SELECTED_COLOR = (180, 220, 255)

        # =====================================================
        # LOAD ICONS
        # =====================================================
        self.boy_icon = None
        self.girl_icon = None
        self.load_gender_icons()

        # =====================================================
        # =====================================================
        # STUDENT DATA & SMOOTH DRAG SCROLLING
        # =====================================================
        self.students = []
        self.selected_student = None
        self.selected_index = 0
        self.scroll_offset = 0
        self.scroll_y = 0.0
        self.target_scroll_y = 0.0
        self.max_scroll_y = 0.0
        self.item_height = 90

        # Mouse Drag & Hold state
        self.is_mouse_dragging = False
        self.is_scrollbar_dragging = False
        self.mouse_drag_start_y = 0
        self.mouse_drag_start_scroll = 0.0
        self.mouse_drag_dist = 0.0

        # Gesture Fist Drag & Hold state
        self.is_gesture_dragging = False
        self.gesture_drag_start_y = 0
        self.gesture_drag_start_scroll = 0.0
        self.gesture_drag_dist = 0.0

        # =====================================================
        # BUTTONS
        # =====================================================
        self.back_button = pygame.Rect(30, 25, 120, 50)
        self.refresh_button = pygame.Rect(self.width - 150, 25, 120, 50)

        # =====================================================
        # MESSAGE
        # =====================================================
        self.message = None
        self.message_timer = 0

        # =====================================================
        # LOAD STUDENTS
        # =====================================================
        self.load_students()

    # =========================================================
    # GESTURE METHODS (ADDED)
    # =========================================================
    # =========================================================
    # GESTURE METHODS (ADDED)
    # =========================================================
    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        """Update gesture data, drag-to-scroll, and proactive dwell selection"""
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME
        self.current_gesture = current_gesture

        list_rect = pygame.Rect(40, 120, self.width - 80, self.height - 200)
        total_content_h = len(self.students) * self.item_height + 20
        self.max_scroll_y = max(0.0, float(total_content_h - list_rect.height))

        # Fist Gesture Drag & Hold to Scroll vs Dwell Select
        if current_gesture == "FIST":
            if not self.is_gesture_dragging:
                self.is_gesture_dragging = True
                self.gesture_drag_start_y = cursor_pos[1]
                self.gesture_drag_start_scroll = self.target_scroll_y
                self.is_actively_scrolling = False
            else:
                dy_total = cursor_pos[1] - self.gesture_drag_start_y

                # If user moved vertically by more than 18px, activate DRAG SCROLL MODE
                if (abs(dy_total) > 18.0 or getattr(self, 'is_actively_scrolling', False)) and self.max_scroll_y > 0:
                    self.is_actively_scrolling = True
                    # Reset dwell timer so scrolling does not select students
                    self.fist_start_time = time.time()
                    if self.main_menu:
                        self.main_menu.fist_start_time = time.time()

                    # Fluid drag scroll
                    self.target_scroll_y = max(0.0, min(self.max_scroll_y, self.gesture_drag_start_scroll - dy_total * 1.35))

                # Edge auto-scroll when dragging near top/bottom list bounds
                if cursor_pos[1] < list_rect.y + 40 and dy_total < -15.0 and self.max_scroll_y > 0:
                    self.is_actively_scrolling = True
                    self.fist_start_time = time.time()
                    if self.main_menu:
                        self.main_menu.fist_start_time = time.time()
                    proximity = max(0.1, min(1.0, (list_rect.y + 40 - cursor_pos[1]) / 40.0))
                    self.target_scroll_y = max(0.0, self.target_scroll_y - proximity * 12.0)
                elif cursor_pos[1] > list_rect.bottom - 40 and dy_total > 15.0 and self.max_scroll_y > 0:
                    self.is_actively_scrolling = True
                    self.fist_start_time = time.time()
                    if self.main_menu:
                        self.main_menu.fist_start_time = time.time()
                    proximity = max(0.1, min(1.0, (cursor_pos[1] - (list_rect.bottom - 40)) / 40.0))
                    self.target_scroll_y = min(self.max_scroll_y, self.target_scroll_y + proximity * 12.0)

            # Dwell Select Mode: If user is holding fist STILL over a card (not actively dragging)
            if not getattr(self, 'is_actively_scrolling', False):
                if self.fist_start_time > 0:
                    hold_time = time.time() - self.fist_start_time
                    if hold_time >= self.CLICK_HOLD_TIME and not getattr(self, '_fist_click_triggered', False):
                        self._fist_click_triggered = True
                        if self.main_menu:
                            self.main_menu.click_ready = True
                        self.trigger_click(self.cursor_pos)
        else:
            self.is_gesture_dragging = False
            self.is_actively_scrolling = False
            self._fist_click_triggered = False

    def trigger_click(self, pos):
        """Handle click at cursor position - called from main_menu or handle_event"""
        # Check cooldown to prevent multiple rapid clicks
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_click_time < self.click_cooldown:
            return None

        self.last_click_time = current_time
        self.cursor_pos = pos

        # Check BACK button
        if self.back_button.collidepoint(pos):
            print("[BACK] Back to main menu")
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            if self.main_menu:
                self.main_menu.current_screen = "menu"
                self.main_menu.student_select = None
                self.main_menu.fist_start_time = 0
                self.main_menu.click_ready = True
                self.main_menu.last_click_time = time.time()
            return "back"

        # Check REFRESH button
        if self.refresh_button.collidepoint(pos):
            print("[REFRESH] Refresh students")
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            self.load_students()
            return "refresh"

        # Check student list items and scrollbar
        return self.check_student_click(pos)

    def check_student_click(self, pos):
        """Check if a student item or scrollbar was clicked with generous row hitboxes within list bounds"""
        list_rect = pygame.Rect(40, 120, self.width - 80, self.height - 200)

        # Click must be inside list_rect
        if not list_rect.collidepoint(pos):
            return None

        total_content_h = len(self.students) * self.item_height + 20
        self.max_scroll_y = max(0.0, float(total_content_h - list_rect.height))

        # Check scrollbar click (right edge margin)
        if self.max_scroll_y > 0 and pos[0] >= list_rect.right - 25:
            track_y = list_rect.y + 12
            track_h = list_rect.height - 24
            thumb_h = max(36, int(track_h * (list_rect.height / float(total_content_h))))
            ratio = (pos[1] - track_y - thumb_h / 2.0) / float(max(1, track_h - thumb_h))
            self.target_scroll_y = max(0.0, min(self.max_scroll_y, ratio * self.max_scroll_y))
            return "scroll"

        # 1. Primary: Exact hit detection against visible rendered cards
        for index, student in enumerate(self.students):
            draw_y = list_rect.y + 15 + (index * self.item_height) - int(self.scroll_y)
            if draw_y + self.item_height - 12 < list_rect.y or draw_y > list_rect.bottom:
                continue
            item_rect = pygame.Rect(list_rect.x + 15, draw_y, list_rect.width - 45, self.item_height - 12)
            if item_rect.collidepoint(pos) or (draw_y - 4 <= pos[1] <= draw_y + self.item_height - 6 and list_rect.x <= pos[0] <= list_rect.right - 25):
                self.selected_index = index
                self.select_student(student)
                print(f"[USER] Selected student: {student.get('first_name', '')} {student.get('last_name', '')}".strip())
                return "select"

        # 2. Secondary: Robust index calculation with smooth scroll offset
        if list_rect.x <= pos[0] <= list_rect.right - 25:
            y_rel = pos[1] - (list_rect.y + 15) + self.scroll_y
            row_idx = int(y_rel // self.item_height)

            if 0 <= row_idx < len(self.students):
                student = self.students[row_idx]
                self.selected_index = row_idx
                self.select_student(student)
                print(f"[USER] Selected student (row calc): {student.get('first_name', '')} {student.get('last_name', '')}".strip())
                return "select"

        return None

    # =========================================================
    # LOAD GENDER ICONS
    # =========================================================
    def load_gender_icons(self):
        try:
            boy_path = os.path.join("assets", "images", "boy.png")
            girl_path = os.path.join("assets", "images", "girl.png")

            if os.path.exists(boy_path):
                self.boy_icon = pygame.image.load(boy_path).convert_alpha()
                self.boy_icon = pygame.transform.scale(self.boy_icon, (40, 40))

            if os.path.exists(girl_path):
                self.girl_icon = pygame.image.load(girl_path).convert_alpha()
                self.girl_icon = pygame.transform.scale(self.girl_icon, (40, 40))

        except Exception as e:
            print(f"Icon Error: {e}")

    # =========================================================
    # GET GENDER
    # =========================================================
    def get_gender_from_extra_data(self, extra_data):
        if not extra_data:
            return None

        try:
            if isinstance(extra_data, str):
                data = json.loads(extra_data)
            else:
                data = extra_data

            gender = data.get("Gender") or data.get("gender")

            if gender:
                gender = str(gender).lower()
                if gender in ["m", "male"]:
                    return "male"
                elif gender in ["f", "female"]:
                    return "female"

            return None

        except Exception:
            return None

    # =========================================================
    # LOAD STUDENTS
    # =========================================================
    def load_students(self):
        try:
            if db:
                results = db.get_students()
                if results is not None and len(results) > 0:
                    self.students = []
                    for student in results:
                        # Map keys from the API response (camelCase in Vercel JSON!)
                        full_name = student.get("fullName") or student.get("full_name") or student.get("name")
                        first = student.get("first_name") or (full_name if full_name else "Unknown")
                        last = student.get("last_name") or ""
                        self.students.append({
                            "id": student.get("id"),
                            "student_id": str(student.get("studentId") or student.get("student_id") or "MOCK-ID"),
                            "first_name": first,
                            "last_name": last,
                            "score": 0,
                            "progress": 0,
                            "level": student.get("gradeLevel") or student.get("grade_level", "Grade 2"),
                            "gender": str(student.get("gender", "male")).lower(),
                            "section": student.get("section", ""),
                            "avatarColor": student.get("avatarColor", "")
                        })
                    print(f"[OK] Loaded {len(self.students)} students from Vercel API")
                else:
                    self.load_mock_students()
            else:
                self.load_mock_students()
        except Exception as e:
            print(f"API Student Roster Error: {e}")
            self.load_mock_students()

        # Connect with saved progress if available to reflect real scores & progress
        try:
            from db.save_system import load_student_progress
            for s in self.students:
                sid = s.get("student_id")
                if sid:
                    save_data = load_student_progress(sid)
                    if save_data:
                        q_data = save_data.get("completed_quarters", {})
                        completed_count = sum(1 for q, d in q_data.items() if isinstance(d, dict) and d.get("completed"))
                        s["progress"] = int((completed_count / 4.0) * 100)
                        s["score"] = sum(d.get("score", 0) for q, d in q_data.items() if isinstance(d, dict))
        except Exception as e:
            print(f"Student progress sync error: {e}")

        # Pre-select currently active student if one is already selected
        if getattr(self.main_menu, 'student_id', None):
            for idx, s in enumerate(self.students):
                if s.get("student_id") == self.main_menu.student_id:
                    self.selected_index = idx
                    self.selected_student = s
                    break

        if not self.students:
            self.show_message("No students found.", 3000)

    def load_mock_students(self):
        """Mock student data for testing without database"""
        self.students = [
            {"id": 1, "student_id": "MOCK-01", "first_name": "John", "last_name": "Smith",
             "score": 85, "progress": 75, "level": "Level 2", "gender": "male"},
            {"id": 2, "student_id": "MOCK-02", "first_name": "Emma", "last_name": "Johnson",
             "score": 92, "progress": 88, "level": "Level 3", "gender": "female"},
            {"id": 3, "student_id": "MOCK-03", "first_name": "Michael", "last_name": "Brown",
             "score": 78, "progress": 65, "level": "Level 1", "gender": "male"},
            {"id": 4, "student_id": "MOCK-04", "first_name": "Sophia", "last_name": "Davis",
             "score": 95, "progress": 92, "level": "Level 3", "gender": "female"},
            {"id": 5, "student_id": "MOCK-05", "first_name": "James", "last_name": "Wilson",
             "score": 70, "progress": 60, "level": "Level 1", "gender": "male"},
        ]
        print(f"[DATA] Loaded {len(self.students)} mock students for testing")

    # =========================================================
    # MESSAGE
    # =========================================================
    def show_message(self, text, duration=2000):
        self.message = text
        self.message_timer = pygame.time.get_ticks() + duration

    # =========================================================
    # SELECT STUDENT
    # =========================================================
    def select_student(self, student):
        if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
            self.main_menu.audio_manager.play_sfx("click")
        self.selected_student = student
        if self.main_menu:
            self.main_menu.selected_student = student
            self.main_menu.student_id = str(student.get('student_id') or "")
            self.main_menu.student_db_id = student.get('id')  # Store the primary key ID from database

            self.main_menu.current_screen = "menu"
            self.main_menu.student_select = None
            self.main_menu.fist_start_time = 0
            self.main_menu.click_ready = True
            self.main_menu.last_click_time = time.time()
            
            # Refresh main menu buttons dynamically to check for saved progress
            if hasattr(self.main_menu, 'setup_buttons'):
                self.main_menu.setup_buttons()

        first = student.get('first_name') or ""
        last = student.get('last_name') or ""
        display_name = f"{first} {last}".strip()
        self.show_message(f"Selected: {display_name}", 2000)
        print(f"Selected Student: {display_name} (ID: {student.get('student_id')}, DB ID: {student.get('id')})")

    # =========================================================
    # DRAW BUTTON (with hover detection from cursor)
    # =========================================================
    def is_cursor_active(self):
        return (self.current_gesture in ["FIST", "OPEN", "PEACE", "NO HAND (GRACE)"]) or (self.main_menu and getattr(self.main_menu, 'mouse_active', False))

    def draw_button(self, rect, text):
        hovered = self.is_cursor_active() and rect.collidepoint(self.cursor_pos)
        color = self.BUTTON_HOVER if hovered else self.BUTTON_COLOR

        pygame.draw.rect(self.screen, color, rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=14)

        txt = self.small_font.render(text, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    # =========================================================
    # DRAW STUDENT LIST (with hover detection from cursor)
    # =========================================================
    def draw_student_list(self):
        list_rect = pygame.Rect(40, 120, self.width - 80, self.height - 200)

        # PANEL
        panel = pygame.Surface((list_rect.width, list_rect.height), pygame.SRCALPHA)
        panel.fill((255, 255, 255, 235))
        self.screen.blit(panel, list_rect.topleft)

        # Outer border with soft shadow
        shadow_rect = list_rect.inflate(4, 4)
        pygame.draw.rect(self.screen, (20, 30, 60, 40), shadow_rect, 2, border_radius=20)
        pygame.draw.rect(self.screen, self.BORDER_COLOR, list_rect, 3, border_radius=18)

        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)

        y = list_rect.y + 15

        cursor_active = self.is_cursor_active()

        for index, student in enumerate(self.students):
            draw_y = y + (index * self.item_height) - int(self.scroll_y)

            if draw_y < list_rect.y - 100 or draw_y > list_rect.bottom + 20:
                continue

            item_rect = pygame.Rect(list_rect.x + 15, draw_y, list_rect.width - 45, 78)

            # Highlight if hovered by cursor
            is_hovered = cursor_active and list_rect.collidepoint(self.cursor_pos) and (draw_y - 4 <= self.cursor_pos[1] <= draw_y + self.item_height - 6 and list_rect.x <= self.cursor_pos[0] <= list_rect.right - 25)

            is_fist_charging = is_hovered and self.current_gesture == "FIST" and self.fist_start_time > 0 and not getattr(self, 'is_actively_scrolling', False)
            hold_pct = 0.0
            if is_fist_charging:
                hold_pct = min(1.0, max(0.0, (time.time() - self.fist_start_time) / max(0.01, self.CLICK_HOLD_TIME)))

            if index == self.selected_index:
                card_color = self.SELECTED_COLOR
                border_col = (70, 130, 240)
                border_width = 3
            elif is_fist_charging:
                card_color = (254, 249, 195)  # Warm golden charging glow
                border_col = (234, 179, 8)
                border_width = 3
            elif is_hovered:
                card_color = (220, 235, 255)  # Lighter hover color
                border_col = (130, 160, 230)
                border_width = 2
            else:
                card_color = (248, 250, 255)
                border_col = self.BORDER_COLOR
                border_width = 2

            pygame.draw.rect(self.screen, card_color, item_rect, border_radius=14)
            pygame.draw.rect(self.screen, border_col, item_rect, border_width, border_radius=14)

            # Draw charging progress bar on card during fist hold
            if is_fist_charging and hold_pct > 0.05:
                charge_bar_w = int((item_rect.width - 24) * hold_pct)
                pygame.draw.rect(self.screen, (220, 220, 230), (item_rect.x + 12, item_rect.bottom - 6, item_rect.width - 24, 4), border_radius=2)
                pygame.draw.rect(self.screen, (234, 179, 8), (item_rect.x + 12, item_rect.bottom - 6, charge_bar_w, 4), border_radius=2)

            # ICON / AVATAR BOX
            icon_x = item_rect.x + 15
            icon_y = item_rect.y + 18
            icon_drawn = False

            gender = str(student.get("gender", "")).lower()
            if gender in ["male", "m", "boy"] and self.boy_icon:
                self.screen.blit(self.boy_icon, (icon_x, icon_y))
                icon_drawn = True
            elif gender in ["female", "f", "girl"] and self.girl_icon:
                self.screen.blit(self.girl_icon, (icon_x, icon_y))
                icon_drawn = True
            elif self.boy_icon:
                self.screen.blit(self.boy_icon, (icon_x, icon_y))
                icon_drawn = True

            if not icon_drawn:
                # Stylized vibrant avatar circle with student initial
                badge_col = (59, 130, 246) if gender in ["male", "m", "boy"] else (236, 72, 153) if gender in ["female", "f", "girl"] else (99, 102, 241)
                pygame.draw.circle(self.screen, badge_col, (icon_x + 20, icon_y + 20), 20)
                pygame.draw.circle(self.screen, (255, 255, 255), (icon_x + 20, icon_y + 20), 20, 2)
                initial = (student.get("first_name", "S")[:1] or "S").upper()
                init_surf = self.font.render(initial, True, (255, 255, 255))
                self.screen.blit(init_surf, init_surf.get_rect(center=(icon_x + 20, icon_y + 20)))

            # NAME
            name_x = icon_x + 60
            avail_w = max(100, item_rect.right - name_x - 30)
            full_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip() or "Student"
            name_surface = self.font.render(full_name, True, self.TEXT_COLOR)
            if name_surface.get_width() > avail_w:
                name_surface = self.small_font.render(full_name, True, self.TEXT_COLOR)
                if name_surface.get_width() > avail_w:
                    trunc_name = full_name
                    while len(trunc_name) > 3 and self.small_font.size(trunc_name + "...")[0] > avail_w:
                        trunc_name = trunc_name[:-1]
                    name_surface = self.small_font.render(trunc_name + "...", True, self.TEXT_COLOR)
            self.screen.blit(name_surface, (name_x, item_rect.y + 10))

            # INFO
            info = f"Score: {student.get('score', 0)}   Progress: {student.get('progress', 0)}%   Level: {student.get('level', 1)}"
            info_surface = self.small_font.render(info, True, (90, 90, 120))
            if info_surface.get_width() > avail_w:
                from core.font_manager import get_font
                tiny_f = get_font("Comic Sans MS", 16)
                info_surface = tiny_f.render(info, True, (90, 90, 120))
            self.screen.blit(info_surface, (name_x, item_rect.y + 44))

        # Subtle Top / Bottom scroll fades when content overflows
        if self.scroll_y > 10.0:
            top_fade = pygame.Surface((list_rect.width - 25, 18), pygame.SRCALPHA)
            for i in range(18):
                alpha = int(120 * (1.0 - i / 18.0))
                pygame.draw.line(top_fade, (210, 225, 245, alpha), (0, i), (list_rect.width - 25, i))
            self.screen.blit(top_fade, (list_rect.x, list_rect.y))

        if self.max_scroll_y > 0 and self.scroll_y < self.max_scroll_y - 10.0:
            bot_fade = pygame.Surface((list_rect.width - 25, 18), pygame.SRCALPHA)
            for i in range(18):
                alpha = int(120 * (i / 18.0))
                pygame.draw.line(bot_fade, (210, 225, 245, alpha), (0, i), (list_rect.width - 25, i))
            self.screen.blit(bot_fade, (list_rect.x, list_rect.bottom - 18))

        self.screen.set_clip(old_clip)

        # SCROLLBAR
        total_content_h = len(self.students) * self.item_height + 20
        self.max_scroll_y = max(0.0, float(total_content_h - list_rect.height))

        if self.max_scroll_y > 0:
            track_rect = pygame.Rect(list_rect.right - 18, list_rect.y + 12, 10, list_rect.height - 24)
            # Track pill background
            pygame.draw.rect(self.screen, (215, 225, 240, 160), track_rect, border_radius=6)

            thumb_h = max(36, int(track_rect.height * (list_rect.height / float(total_content_h))))
            ratio = self.scroll_y / self.max_scroll_y if self.max_scroll_y > 0 else 0.0
            thumb_y = track_rect.y + ratio * (track_rect.height - thumb_h)
            thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_h)

            thumb_hover = (self.is_cursor_active() and thumb_rect.collidepoint(self.cursor_pos)) or self.is_scrollbar_dragging
            thumb_col = (90, 130, 220) if thumb_hover else (130, 155, 195)
            pygame.draw.rect(self.screen, thumb_col, thumb_rect, border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255, 180), thumb_rect, 1, border_radius=6)

    # =========================================================
    # DRAW GESTURE CURSOR
    # =========================================================
    def draw_cursor(self):
        pass

    # =========================================================
    # DRAW SCREEN
    # =========================================================
    def draw(self):
        # BACKGROUND
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill((180, 220, 255))

        # DARK OVERLAY
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        self.screen.blit(overlay, (0, 0))

        # TITLE
        title = self.title_font.render("Select Student", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 70)))

        # STUDENT LIST
        self.draw_student_list()

        # BUTTONS
        self.draw_button(self.back_button, "Back")
        self.draw_button(self.refresh_button, "Refresh")

        # GESTURE INSTRUCTION (ADDED)
        gesture_display = "FIST" if self.current_gesture == "FIST" else "OPEN HAND"
        if self.current_gesture == "NO HAND":
            gesture_display = "NO HAND"

        instruction = self.small_font.render(
            f"Gesture: {gesture_display}  |  Hold FIST on student to select  |  Move FIST to scroll",
            True,
            (255, 240, 180)
        )
        self.screen.blit(instruction, (self.width // 2 - instruction.get_width() // 2, self.height - 65))

        # MESSAGE
        if self.message and pygame.time.get_ticks() < self.message_timer:
            msg_surface = self.small_font.render(self.message, True, (255, 255, 255))
            msg_rect = msg_surface.get_rect(center=(self.width // 2, self.height - 30))
            pygame.draw.rect(self.screen, (40, 40, 40), msg_rect.inflate(25, 12), border_radius=10)
            self.screen.blit(msg_surface, msg_rect)

    # =========================================================
    # HANDLE EVENTS
    # =========================================================
    def handle_event(self, event):
        list_rect = pygame.Rect(40, 120, self.width - 80, self.height - 200)
        total_content_h = len(self.students) * self.item_height + 20
        self.max_scroll_y = max(0.0, float(total_content_h - list_rect.height))

        if event.type == pygame.MOUSEMOTION:
            self.cursor_pos = event.pos
            if self.is_scrollbar_dragging and self.max_scroll_y > 0:
                track_y = list_rect.y + 12
                track_h = list_rect.height - 24
                thumb_h = max(36, int(track_h * (list_rect.height / float(total_content_h))))
                ratio = (event.pos[1] - track_y - thumb_h / 2.0) / float(max(1, track_h - thumb_h))
                self.target_scroll_y = max(0.0, min(self.max_scroll_y, ratio * self.max_scroll_y))
                return "scroll"
            elif self.is_mouse_dragging and self.max_scroll_y > 0:
                dy = event.pos[1] - self.mouse_drag_start_y
                self.mouse_drag_dist += abs(dy)
                self.target_scroll_y = max(0.0, min(self.max_scroll_y, self.mouse_drag_start_scroll - dy))
                return "scroll"
            return None

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.cursor_pos = event.pos
                if self.back_button.collidepoint(event.pos):
                    return self.trigger_click(event.pos)
                elif self.refresh_button.collidepoint(event.pos):
                    return self.trigger_click(event.pos)
                elif list_rect.collidepoint(event.pos):
                    # Check if clicking on scrollbar track or thumb
                    if event.pos[0] >= list_rect.right - 25 and self.max_scroll_y > 0:
                        self.is_scrollbar_dragging = True
                        track_y = list_rect.y + 12
                        track_h = list_rect.height - 24
                        thumb_h = max(36, int(track_h * (list_rect.height / float(total_content_h))))
                        ratio = (event.pos[1] - track_y - thumb_h / 2.0) / float(max(1, track_h - thumb_h))
                        self.target_scroll_y = max(0.0, min(self.max_scroll_y, ratio * self.max_scroll_y))
                        return "scroll"
                    else:
                        self.is_mouse_dragging = True
                        self.mouse_drag_start_y = event.pos[1]
                        self.mouse_drag_start_scroll = self.target_scroll_y
                        self.mouse_drag_dist = 0.0
                        return self.trigger_click(event.pos)
                return self.trigger_click(event.pos)

            elif event.button == 4:  # Wheel up
                self.target_scroll_y = max(0.0, self.target_scroll_y - self.item_height)
                return "scroll"
            elif event.button == 5:  # Wheel down
                self.target_scroll_y = min(self.max_scroll_y, self.target_scroll_y + self.item_height)
                return "scroll"

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                was_dragging = (self.is_mouse_dragging and self.mouse_drag_dist > 15.0) or self.is_scrollbar_dragging
                self.is_mouse_dragging = False
                self.is_scrollbar_dragging = False
                if was_dragging:
                    return "scroll"

        elif event.type == pygame.MOUSEWHEEL:
            self.target_scroll_y = max(0.0, min(self.max_scroll_y, self.target_scroll_y - event.y * self.item_height))
            return "scroll"

        elif event.type == pygame.KEYDOWN:
            # DOWN
            if event.key == pygame.K_DOWN:
                if self.selected_index < len(self.students) - 1:
                    self.selected_index += 1
                    visible_count = max(1, (self.height - 220) // self.item_height)
                    if self.selected_index >= self.scroll_offset + visible_count:
                        self.target_scroll_y = min(self.max_scroll_y, (self.selected_index - visible_count + 1) * self.item_height)

            # UP
            elif event.key == pygame.K_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    if self.selected_index < self.scroll_offset:
                        self.target_scroll_y = max(0.0, self.selected_index * self.item_height)

            # ENTER
            elif event.key == pygame.K_RETURN:
                if self.students:
                    self.select_student(self.students[self.selected_index])
                    return "select"

            # ESCAPE
            elif event.key == pygame.K_ESCAPE:
                if self.main_menu:
                    self.main_menu.current_screen = "menu"
                    self.main_menu.student_select = None
                return "back"

        return None

    # =========================================================
    # UPDATE (smooth scrolling interpolation & gestures)
    # =========================================================
    def update(self):
        """Update method - called every frame from main_menu"""
        list_rect = pygame.Rect(40, 120, self.width - 80, self.height - 200)
        total_content_h = len(self.students) * self.item_height + 20
        self.max_scroll_y = max(0.0, float(total_content_h - list_rect.height))

        # Clamp target scroll
        self.target_scroll_y = max(0.0, min(self.max_scroll_y, self.target_scroll_y))

        # Smooth exponential interpolation
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * 0.35
        if abs(self.target_scroll_y - self.scroll_y) < 0.5:
            self.scroll_y = self.target_scroll_y

        self.scroll_offset = int(self.scroll_y // self.item_height)