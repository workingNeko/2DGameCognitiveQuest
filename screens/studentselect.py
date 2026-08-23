import pygame
import os
import json

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
        self.last_click_time = 0
        self.click_cooldown = 0.5  # seconds between clicks

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
        # STUDENT DATA
        # =====================================================
        self.students = []
        self.selected_student = None
        self.selected_index = 0
        self.scroll_offset = 0
        self.item_height = 90

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
    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        """Update gesture data from main menu"""
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME
        self.current_gesture = current_gesture

    def trigger_click(self, pos):
        """Handle click at cursor position - called from main_menu"""
        # Check cooldown to prevent multiple rapid clicks
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_click_time < self.click_cooldown:
            return

        self.cursor_pos = pos

        # Check BACK button
        if self.back_button.collidepoint(pos):
            print("⬅️ Back to main menu")
            self.last_click_time = current_time
            if self.main_menu:
                self.main_menu.current_screen = "menu"
                self.main_menu.student_select = None
            return

        # Check REFRESH button
        if self.refresh_button.collidepoint(pos):
            print("🔄 Refresh students")
            self.last_click_time = current_time
            self.load_students()
            return

        # Check student list items
        self.check_student_click(pos)

    def check_student_click(self, pos):
        """Check if a student item was clicked"""
        list_rect = pygame.Rect(70, 130, self.width - 140, self.height - 220)

        # Check if click is within list area
        if not list_rect.collidepoint(pos):
            return

        # Calculate which student was clicked
        y_offset = pos[1] - (list_rect.y + 15)
        if y_offset < 0:
            return

        clicked_index = self.scroll_offset + (y_offset // self.item_height)

        if 0 <= clicked_index < len(self.students):
            self.selected_index = clicked_index
            self.select_student(self.students[clicked_index])

            # Visual feedback - show selected message
            student = self.students[clicked_index]
            print(f"👤 Selected student: {student['first_name']} {student['last_name']}")

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
        # Try to load from database, otherwise use mock data for testing
        try:
            if db and db.connection and db.connection.is_connected():
                query = """
                    SELECT
                        student_id,
                        firstName,
                        lastName,
                        score,
                        progress,
                        level,
                        extra_data
                    FROM student
                    WHERE status = 'Enrolled'
                    ORDER BY lastName, firstName
                """
                db.cursor.execute(query)
                results = db.cursor.fetchall()

                self.students = []

                for student in results:
                    gender = self.get_gender_from_extra_data(student.get("extra_data"))
                    self.students.append({
                        "student_id": student["student_id"],
                        "first_name": student["firstName"],
                        "last_name": student["lastName"],
                        "score": student.get("score", 0),
                        "progress": student.get("progress", 0),
                        "level": student.get("level", "Level 1"),
                        "gender": gender
                    })

                print(f"✅ Loaded {len(self.students)} students")
            else:
                # Mock data for testing
                self.load_mock_students()

        except Exception as e:
            print(f"Database Error: {e}")
            self.load_mock_students()

        if not self.students:
            self.show_message("No students found.", 3000)

    def load_mock_students(self):
        """Mock student data for testing without database"""
        self.students = [
            {"student_id": 1, "first_name": "John", "last_name": "Smith",
             "score": 85, "progress": 75, "level": "Level 2", "gender": "male"},
            {"student_id": 2, "first_name": "Emma", "last_name": "Johnson",
             "score": 92, "progress": 88, "level": "Level 3", "gender": "female"},
            {"student_id": 3, "first_name": "Michael", "last_name": "Brown",
             "score": 78, "progress": 65, "level": "Level 1", "gender": "male"},
            {"student_id": 4, "first_name": "Sophia", "last_name": "Davis",
             "score": 95, "progress": 92, "level": "Level 3", "gender": "female"},
            {"student_id": 5, "first_name": "James", "last_name": "Wilson",
             "score": 70, "progress": 60, "level": "Level 1", "gender": "male"},
        ]
        print(f"📋 Loaded {len(self.students)} mock students for testing")

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
        self.selected_student = student
        self.main_menu.selected_student = student
        self.main_menu.student_id = student['student_id']

        self.main_menu.current_screen = "menu"

        self.show_message(f"✅ Selected: {student['first_name']} {student['last_name']}", 2000)
        print(f"✅ Selected Student: {student['first_name']} {student['last_name']} (ID: {student['student_id']})")

    # =========================================================
    # DRAW BUTTON (with hover detection from cursor)
    # =========================================================
    def draw_button(self, rect, text):
        hovered = rect.collidepoint(self.cursor_pos)
        color = self.BUTTON_HOVER if hovered else self.BUTTON_COLOR

        pygame.draw.rect(self.screen, color, rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=14)

        txt = self.small_font.render(text, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    # =========================================================
    # DRAW STUDENT LIST (with hover detection from cursor)
    # =========================================================
    def draw_student_list(self):
        list_rect = pygame.Rect(70, 130, self.width - 140, self.height - 220)

        # PANEL
        panel = pygame.Surface((list_rect.width, list_rect.height), pygame.SRCALPHA)
        panel.fill((255, 255, 255, 230))
        self.screen.blit(panel, list_rect.topleft)

        pygame.draw.rect(self.screen, self.BORDER_COLOR, list_rect, 3, border_radius=18)

        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)

        y = list_rect.y + 15

        for index, student in enumerate(self.students):
            draw_y = y + ((index - self.scroll_offset) * self.item_height)

            if draw_y < list_rect.y - 100:
                continue
            if draw_y > list_rect.bottom:
                continue

            item_rect = pygame.Rect(list_rect.x + 15, draw_y, list_rect.width - 35, 78)

            # Check if cursor is hovering over this item
            is_hovered = item_rect.collidepoint(self.cursor_pos)

            if index == self.selected_index:
                card_color = self.SELECTED_COLOR
            elif is_hovered:
                card_color = (220, 230, 255)  # Lighter hover color
            else:
                card_color = (245, 248, 255)

            pygame.draw.rect(self.screen, card_color, item_rect, border_radius=14)
            pygame.draw.rect(self.screen, self.BORDER_COLOR, item_rect, 2, border_radius=14)

            # ICON
            icon_x = item_rect.x + 15
            icon_y = item_rect.y + 18

            if student["gender"] == "male" and self.boy_icon:
                self.screen.blit(self.boy_icon, (icon_x, icon_y))
            elif student["gender"] == "female" and self.girl_icon:
                self.screen.blit(self.girl_icon, (icon_x, icon_y))

            # NAME
            name_x = icon_x + 60
            full_name = f"{student['first_name']} {student['last_name']}"
            name_surface = self.font.render(full_name, True, self.TEXT_COLOR)
            self.screen.blit(name_surface, (name_x, item_rect.y + 8))

            # INFO
            info = f"Score: {student['score']}   Progress: {student['progress']}%   Level: {student['level']}"
            info_surface = self.small_font.render(info, True, (90, 90, 120))
            self.screen.blit(info_surface, (name_x, item_rect.y + 42))

        self.screen.set_clip(old_clip)

        # SCROLLBAR
        total_height = len(self.students) * self.item_height
        visible_height = list_rect.height

        if total_height > visible_height:
            scrollbar_height = max(50, int(visible_height * (visible_height / total_height)))
            max_scroll = max(1, len(self.students) - 1)
            scrollbar_y = list_rect.y + (self.scroll_offset / max_scroll) * (visible_height - scrollbar_height)
            scrollbar_rect = pygame.Rect(list_rect.right - 10, scrollbar_y, 6, scrollbar_height)
            pygame.draw.rect(self.screen, (120, 140, 180), scrollbar_rect, border_radius=10)

    # =========================================================
    # DRAW GESTURE CURSOR
    # =========================================================
    def draw_cursor(self):
        if self.current_gesture != "NO HAND":
            if self.fist_start_time > 0:
                color = (255, 200, 0)  # Yellow when holding fist
            else:
                color = (255, 255, 255)  # White normally

            pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
            pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

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
        gesture_display = "✊ FIST" if self.current_gesture == "FIST" else "🖐️ OPEN HAND"
        if self.current_gesture == "NO HAND":
            gesture_display = "👆 NO HAND"

        instruction = self.small_font.render(
            f"Gesture: {gesture_display}  |  FIST = Select student/button",
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

        # DRAW GESTURE CURSOR (ADDED)
        self.draw_cursor()

    # =========================================================
    # HANDLE EVENTS
    # =========================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # DOWN
            if event.key == pygame.K_DOWN:
                if self.selected_index < len(self.students) - 1:
                    self.selected_index += 1
                    visible_count = (self.height - 220) // self.item_height
                    if self.selected_index >= self.scroll_offset + visible_count:
                        self.scroll_offset += 1

            # UP
            elif event.key == pygame.K_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    if self.selected_index < self.scroll_offset:
                        self.scroll_offset -= 1

            # ENTER
            elif event.key == pygame.K_RETURN:
                if self.students:
                    self.select_student(self.students[self.selected_index])
                    return "select"

            # ESCAPE
            elif event.key == pygame.K_ESCAPE:
                return "back"

        return None

    # =========================================================
    # UPDATE (ADDED for gesture)
    # =========================================================
    def update(self):
        """Update method - called from main_menu"""
        pass