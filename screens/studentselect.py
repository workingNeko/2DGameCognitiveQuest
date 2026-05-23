import pygame
import os
import json



class StudentSelect:
    def __init__(self, screen, main_menu):

        self.screen = screen
        self.main_menu = main_menu

        self.width, self.height = screen.get_size()

        # =====================================================
        # BACKGROUND
        # =====================================================
        bg_path = os.path.join(
            "assets",
            "images",
            "menu_background.png"
        )

        if os.path.exists(bg_path):

            self.bg_image = pygame.image.load(
                bg_path
            ).convert()

            self.bg_image = pygame.transform.scale(
                self.bg_image,
                (self.width, self.height)
            )

        else:
            self.bg_image = None

        # =====================================================
        # FONTS
        # =====================================================
        self.title_font = pygame.font.SysFont(
            "Comic Sans MS",
            54,
            bold=True
        )

        self.font = pygame.font.SysFont(
            "Comic Sans MS",
            28
        )

        self.small_font = pygame.font.SysFont(
            "Comic Sans MS",
            20
        )

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

        # keyboard selected index
        self.selected_index = 0

        # scroll position
        self.scroll_offset = 0

        # layout
        self.item_height = 90

        # =====================================================
        # BUTTONS
        # =====================================================
        self.back_button = pygame.Rect(
            30,
            25,
            120,
            50
        )

        self.refresh_button = pygame.Rect(
            self.width - 150,
            25,
            120,
            50
        )

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
    # LOAD GENDER ICONS
    # =========================================================
    def load_gender_icons(self):

        try:

            boy_path = os.path.join(
                "assets",
                "images",
                "boy.png"
            )

            girl_path = os.path.join(
                "assets",
                "images",
                "girl.png"
            )

            if os.path.exists(boy_path):

                self.boy_icon = pygame.image.load(
                    boy_path
                ).convert_alpha()

                self.boy_icon = pygame.transform.scale(
                    self.boy_icon,
                    (40, 40)
                )

            if os.path.exists(girl_path):

                self.girl_icon = pygame.image.load(
                    girl_path
                ).convert_alpha()

                self.girl_icon = pygame.transform.scale(
                    self.girl_icon,
                    (40, 40)
                )

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

            if not db.connection or not db.connection.is_connected():
                db.connect()

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

                gender = self.get_gender_from_extra_data(
                    student.get("extra_data")
                )

                self.students.append({
                    "student_id": student["student_id"],
                    "first_name": student["firstName"],
                    "last_name": student["lastName"],
                    "score": student.get("score", 0),
                    "progress": student.get("progress", 0),
                    "level": student.get("level", "Level 1"),
                    "gender": gender
                })

            print(f"Loaded {len(self.students)} students")

            if not self.students:
                self.show_message("No students found.", 3000)

        except Exception as e:

            print(f"Database Error: {e}")

            self.show_message(
                "Error loading students.",
                3000
            )

            self.students = []

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
        self.main_menu.student_id = student['student_id']  # ADD THIS LINE

        self.main_menu.current_screen = "menu"

        self.show_message(
            f"Selected: {student['first_name']} {student['last_name']}",
            2000
        )

        print(f"Selected Student: {student['first_name']} {student['last_name']} (ID: {student['student_id']})")

    # =========================================================
    # DRAW BUTTON
    # =========================================================
    def draw_button(self, rect, text):

        mouse_pos = pygame.mouse.get_pos()

        hovered = rect.collidepoint(mouse_pos)

        color = (
            self.BUTTON_HOVER
            if hovered
            else self.BUTTON_COLOR
        )

        pygame.draw.rect(
            self.screen,
            color,
            rect,
            border_radius=14
        )

        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            rect,
            2,
            border_radius=14
        )

        txt = self.small_font.render(
            text,
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            txt,
            txt.get_rect(center=rect.center)
        )

    # =========================================================
    # DRAW STUDENT LIST
    # =========================================================
    def draw_student_list(self):

        list_rect = pygame.Rect(
            70,
            130,
            self.width - 140,
            self.height - 220
        )

        # PANEL
        panel = pygame.Surface(
            (list_rect.width, list_rect.height),
            pygame.SRCALPHA
        )

        panel.fill((255, 255, 255, 230))

        self.screen.blit(panel, list_rect.topleft)

        pygame.draw.rect(
            self.screen,
            self.BORDER_COLOR,
            list_rect,
            3,
            border_radius=18
        )

        old_clip = self.screen.get_clip()

        self.screen.set_clip(list_rect)

        y = list_rect.y + 15

        for index, student in enumerate(self.students):

            draw_y = y + (
                (index - self.scroll_offset)
                * self.item_height
            )

            # skip invisible items
            if draw_y < list_rect.y - 100:
                continue

            if draw_y > list_rect.bottom:
                continue

            item_rect = pygame.Rect(
                list_rect.x + 15,
                draw_y,
                list_rect.width - 35,
                78
            )

            # selected item
            if index == self.selected_index:
                card_color = self.SELECTED_COLOR
            else:
                card_color = (245, 248, 255)

            pygame.draw.rect(
                self.screen,
                card_color,
                item_rect,
                border_radius=14
            )

            pygame.draw.rect(
                self.screen,
                self.BORDER_COLOR,
                item_rect,
                2,
                border_radius=14
            )

            # ICON
            icon_x = item_rect.x + 15
            icon_y = item_rect.y + 18

            if student["gender"] == "male" and self.boy_icon:
                self.screen.blit(
                    self.boy_icon,
                    (icon_x, icon_y)
                )

            elif student["gender"] == "female" and self.girl_icon:
                self.screen.blit(
                    self.girl_icon,
                    (icon_x, icon_y)
                )

            # NAME
            name_x = icon_x + 60

            full_name = (
                f"{student['first_name']} "
                f"{student['last_name']}"
            )

            name_surface = self.font.render(
                full_name,
                True,
                self.TEXT_COLOR
            )

            self.screen.blit(
                name_surface,
                (name_x, item_rect.y + 8)
            )

            # INFO
            info = (
                f"Score: {student['score']}   "
                f"Progress: {student['progress']}%   "
                f"Level: {student['level']}"
            )

            info_surface = self.small_font.render(
                info,
                True,
                (90, 90, 120)
            )

            self.screen.blit(
                info_surface,
                (name_x, item_rect.y + 42)
            )

        self.screen.set_clip(old_clip)

        # =====================================================
        # SCROLLBAR
        # =====================================================
        total_height = len(self.students) * self.item_height

        visible_height = list_rect.height

        if total_height > visible_height:

            scrollbar_height = max(
                50,
                int(
                    visible_height *
                    (visible_height / total_height)
                )
            )

            max_scroll = max(
                1,
                len(self.students) - 1
            )

            scrollbar_y = (
                list_rect.y +
                (
                    self.scroll_offset / max_scroll
                )
                *
                (
                    visible_height - scrollbar_height
                )
            )

            scrollbar_rect = pygame.Rect(
                list_rect.right - 10,
                scrollbar_y,
                6,
                scrollbar_height
            )

            pygame.draw.rect(
                self.screen,
                (120, 140, 180),
                scrollbar_rect,
                border_radius=10
            )

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
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 70))

        self.screen.blit(overlay, (0, 0))

        # TITLE
        title = self.title_font.render(
            "Select Student",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, 70)
            )
        )

        # STUDENT LIST
        self.draw_student_list()

        # BUTTONS
        self.draw_button(
            self.back_button,
            "Back"
        )

        self.draw_button(
            self.refresh_button,
            "Refresh"
        )

        # INSTRUCTIONS
        instructions = self.small_font.render(
            "↑ ↓ = Navigate   |   ENTER = Select   |   ESC = Back",
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            instructions,
            (
                self.width // 2 -
                instructions.get_width() // 2,
                self.height - 30
            )
        )

        # MESSAGE
        if (
            self.message and
            pygame.time.get_ticks() < self.message_timer
        ):

            msg_surface = self.small_font.render(
                self.message,
                True,
                (255, 255, 255)
            )

            msg_rect = msg_surface.get_rect(
                center=(self.width // 2, self.height - 65)
            )

            pygame.draw.rect(
                self.screen,
                (40, 40, 40),
                msg_rect.inflate(25, 12),
                border_radius=10
            )

            self.screen.blit(msg_surface, msg_rect)

    # =========================================================
    # HANDLE EVENTS
    # =========================================================
    def handle_event(self, event):

        # =====================================================
        # MOUSE
        # =====================================================
        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = event.pos

            if self.back_button.collidepoint(mouse_pos):
                return "back"

            if self.refresh_button.collidepoint(mouse_pos):

                self.load_students()

                return "refresh"

        # =====================================================
        # KEYBOARD
        # =====================================================
        elif event.type == pygame.KEYDOWN:

            # DOWN
            if event.key == pygame.K_DOWN:

                if self.selected_index < len(self.students) - 1:

                    self.selected_index += 1

                    # scroll down
                    visible_count = (
                        (self.height - 220) //
                        self.item_height
                    )

                    if (
                        self.selected_index >=
                        self.scroll_offset + visible_count
                    ):
                        self.scroll_offset += 1

            # UP
            elif event.key == pygame.K_UP:

                if self.selected_index > 0:

                    self.selected_index -= 1

                    # scroll up
                    if self.selected_index < self.scroll_offset:
                        self.scroll_offset -= 1

            # ENTER
            elif event.key == pygame.K_RETURN:

                if self.students:

                    self.select_student(
                        self.students[self.selected_index]
                    )

                    return "select"

            # ESCAPE
            elif event.key == pygame.K_ESCAPE:
                return "back"

        return None

    # =========================================================
    # UPDATE
    # =========================================================
    def update(self):
        pass