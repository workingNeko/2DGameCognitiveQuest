# screens/quarter2.py - Quarter 2 Market Adventure Game
# Focus: Number and Algebra (NA) & Measurement and Geometry (MG)
# Topics: Philippine coins and bills, addition, subtraction, measurement, patterns
# Simplified for Grade 2 students

import pygame
import os
import sys
import cv2
import numpy as np
import time
import random
import math
from .map_loader import MapLoader

# ============================================================
# SETTINGS
# ============================================================
TILE_SIZE = 32
FPS = 60
SPEED = 4

# Camera zoom settings
ZOOM = 1.50

# Portal settings
PORTAL_SIZES = {
    'right': (3, 3),
    'left': (2, 3),
    'up': (3, 3),
    'down': (3, 2)
}


class Quarter2:
    def __init__(self, screen, main_menu, map_name):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()
        self.map_name = map_name

        # ============================================================
        # GAME STATE
        # ============================================================
        self.game_state = "market"  # market, minigame, complete
        self.current_stall = 0
        self.total_score = 0
        self.max_score = 50  # 5 stalls * 10 points
        self.completed = False

        # ============================================================
        # GESTURE SYSTEM
        # ============================================================
        self.cursor_pos = (self.width // 2, self.height // 2)
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False
        self.hand_detected = False
        self.fist_closed = False

        # ============================================================
        # MOUSE MOVEMENT
        # ============================================================
        self.mouse_target_x = None
        self.mouse_target_y = None
        self.mouse_moving = False
        self.mouse_move_timer = 0

        # ============================================================
        # PATHS
        # ============================================================
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.PLAYER_PATH = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "player"
        )

        self.OBJECTS_PATH = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "tiles"
        )

        self.PORTAL_PATH = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "portal"
        )

        self.NPC_PATH_OLDMAN = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "oldman"
        )

        self.NPC_PATH_SKELETON = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "skeleton"
        )

        # ============================================================
        # MAP LOADER
        # ============================================================
        self.map_loader = MapLoader(self.BASE_DIR)

        if not self.map_loader.load_map(map_name):
            self._create_default_map()
        else:
            self.game_map = self.map_loader.game_map
            self.ROWS = self.map_loader.rows
            self.COLS = self.map_loader.cols
            self.MAP_WIDTH = self.COLS * TILE_SIZE
            self.MAP_HEIGHT = self.ROWS * TILE_SIZE
            self.npc_positions_data = self.map_loader.npc_positions
            self.render_map = self.map_loader.replace_npc_markers_with_walkable_tiles()

        # ============================================================
        # CAMERA
        # ============================================================
        self.camera_x = 0
        self.camera_y = 0

        # ============================================================
        # LOAD TILE IMAGES
        # ============================================================
        self.tile_images = self.load_tile_images()
        self.fallback_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.fallback_tile.fill((100, 100, 100))
        pygame.draw.rect(self.fallback_tile, (255, 0, 0), self.fallback_tile.get_rect(), 2)

        # ============================================================
        # WALKABLE TILES
        # ============================================================
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "P", "r", "l", "u", "d"}

        # ============================================================
        # LOAD PLAYER SPRITES
        # ============================================================
        self.player_sprites = self.load_player_sprites()
        self.anim_frame = 0
        self.anim_timer = 0

        # ============================================================
        # SPAWN PLAYER
        # ============================================================
        self.player_x = 0
        self.player_y = 0
        self.player_dir = "down"

        if self.map_loader.player_start:
            start_x, start_y = self.map_loader.player_start
            self.player_x = start_x * TILE_SIZE
            self.player_y = start_y * TILE_SIZE
            print(f"✅ Player spawned at: ({start_x}, {start_y})")
        else:
            for y, row in enumerate(self.game_map):
                for x, c in enumerate(row):
                    if c == "P":
                        self.player_x = x * TILE_SIZE
                        self.player_y = y * TILE_SIZE
                        print(f"✅ Player spawned at: ({x}, {y})")
                        break
                if self.player_x != 0:
                    break

        for y, row in enumerate(self.render_map):
            if "P" in row:
                self.render_map[y] = row.replace("P", "G")

        # ============================================================
        # MARKET STALLS SYSTEM
        # ============================================================
        self.stall_positions = {}
        self.stall_completed_status = {1: False, 2: False, 3: False, 4: False, 5: False}

        for y, row in enumerate(self.game_map):
            for x, c in enumerate(row):
                if c in ['1', '2', '3', '4', '5']:
                    self.stall_positions[int(c)] = (x * TILE_SIZE, y * TILE_SIZE)
                    print(f"📍 Stall {c} found at: ({x}, {y})")

        # Stall themes based on Quarter 2 curriculum
        self.stall_themes = {
            1: {"name": "Money Counter", "icon": "💰", "topic": "Philippine Coins & Bills"},
            2: {"name": "Addition Shop", "icon": "➕", "topic": "Addition up to ₱1000"},
            3: {"name": "Subtraction Stand", "icon": "➖", "topic": "Subtraction less than 1000"},
            4: {"name": "Measurement Lab", "icon": "📏", "topic": "Length and Distance"},
            5: {"name": "Pattern Studio", "icon": "🔢", "topic": "Number Patterns"}
        }

        print(f"✅ Found {len(self.stall_positions)} stalls")

        # ============================================================
        # MINIGAME STATE
        # ============================================================
        self.minigame_active = False
        self.minigame_type = None
        self.current_stall_index = 1
        self.minigame_score = 0
        self.minigame_attempts = 0
        self.max_attempts = 3
        self.show_feedback = False
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_timer = 0

        self.current_question = None
        self.selected_answer = -1
        self.answer_buttons = []

        # ============================================================
        # PORTALS
        # ============================================================
        self.portals = []
        self.portal_frames_cache = self.load_portal_frames()
        self.load_static_portals()
        self.teleport_cooldown = 0
        self.TELEPORT_COOLDOWN_TIME = 1.0
        self.goal_portal_direction = 'right'

        # Track if player is on portal
        self.on_goal_portal = False

        # ============================================================
        # UI
        # ============================================================
        self.show_info = True
        self.font = pygame.font.SysFont("Comic Sans MS", 16)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 12)
        self.big_font = pygame.font.SysFont("Comic Sans MS", 24, bold=True)
        self.title_font = pygame.font.SysFont("Comic Sans MS", 32, bold=True)

        # ============================================================
        # CLOCK - FIXED: Added clock initialization
        # ============================================================
        self.clock = pygame.time.Clock()
        self.frame_counter = 0

        print(f"✅ Quarter2 Market initialized with map: {self.map_name}")
        print(f"   Stalls found: {len(self.stall_positions)}")
        print(f"   Portals found: {len(self.portals)}")
        print(f"   Goal portal: {self.goal_portal_direction}")

    # ============================================================
    # LOAD TILE IMAGES
    # ============================================================
    def load_tile_images(self):
        def load_tile(filename):
            path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                return image
            except Exception:
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((100, 100, 100))
                pygame.draw.rect(placeholder, (255, 255, 255), placeholder.get_rect(), 1)
                return placeholder

        tiles = {}
        tile_files = [
            ("#", "003.png"), ("G", "002.png"), ("1", "011.png"), ("2", "009.png"),
            ("3", "006.png"), ("4", "004.png"), ("5", "005.png"), ("6", "010.png"),
            ("7", "008.png"), ("8", "007.png"), ("+", "012.png"), ("-", "013.png"),
            ("/", "014.png"), ("*", "015.png"), ("T", "016.png"), ("W", "019.png"),
            ("!", "020.png"), ("@", "022.png"), (")", "021.png"), ("$", "026.png"),
            ("%", "025.png"), ("^", "027.png"), ("&", "023.png"), ("(", "024.png"),
            ("<", "028.png"), (">", "029.png"), (";", "030.png"), (":", "032.png"),
            ("P", "034.png"), ("C", "032.png"), ("S", "036.png"), ("R", "037.png"),
            ("E", "033.png"), ("|", "035.png"), ("D", "pyramid.png")
        ]

        for key, filename in tile_files:
            tiles[key] = load_tile(filename)

        return tiles

    # ============================================================
    # LOAD PLAYER SPRITES
    # ============================================================
    def load_player_sprites(self):
        def load_sprite(name):
            path = os.path.join(self.PLAYER_PATH, name)
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            except Exception:
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((100, 100, 255))
                pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 3)
                return placeholder

        return {
            "down": [load_sprite("boy_down_1.png"), load_sprite("boy_down_2.png")],
            "left": [load_sprite("boy_left_1.png"), load_sprite("boy_left_2.png")],
            "right": [load_sprite("boy_right_1.png"), load_sprite("boy_right_2.png")],
            "up": [load_sprite("boy_up_1.png"), load_sprite("boy_up_2.png")]
        }

    # ============================================================
    # PORTAL CLASS
    # ============================================================
    class Portal:
        def __init__(self, x, y, direction, is_static=False):
            self.tile_x = x
            self.tile_y = y
            self.direction = direction
            self.is_static = is_static
            self.animation = None
            size = PORTAL_SIZES.get(direction, (3, 3))
            self.width_tiles = size[0]
            self.height_tiles = size[1]

        def get_world_x(self):
            return self.tile_x * TILE_SIZE

        def get_world_y(self):
            return self.tile_y * TILE_SIZE

        def get_width_pixels(self):
            return self.width_tiles * TILE_SIZE

        def get_height_pixels(self):
            return self.height_tiles * TILE_SIZE

        def get_center_x(self):
            return self.get_world_x() + self.get_width_pixels() // 2

        def get_center_y(self):
            return self.get_world_y() + self.get_height_pixels() // 2

        def set_animation(self, frames):
            if frames:
                self.animation = self.PortalAnimation(
                    frames, self.get_world_x(), self.get_world_y(),
                    self.direction, self.width_tiles, self.height_tiles
                )

        def update_animation(self):
            if self.animation:
                self.animation.update()

        def draw(self, screen, camera_x, camera_y, zoom, screen_width, screen_height):
            if self.animation:
                self.animation.draw(screen, camera_x, camera_y, zoom, screen_width, screen_height)
            else:
                screen_x = (self.get_world_x() - camera_x) * zoom
                screen_y = (self.get_world_y() - camera_y) * zoom
                scaled_width = int(self.get_width_pixels() * zoom)
                scaled_height = int(self.get_height_pixels() * zoom)
                color = {'right': (0, 255, 0), 'left': (255, 0, 0),
                         'up': (0, 0, 255), 'down': (255, 255, 0)}.get(self.direction, (255, 255, 255))

                pygame.draw.rect(screen, color, (screen_x, screen_y, scaled_width, scaled_height))
                pygame.draw.rect(screen, (255, 255, 255), (screen_x, screen_y, scaled_width, scaled_height), 3)

        def contains_position(self, world_x, world_y):
            portal_left = self.get_world_x()
            portal_right = portal_left + self.get_width_pixels()
            portal_top = self.get_world_y()
            portal_bottom = portal_top + self.get_height_pixels()
            return (portal_left <= world_x < portal_right and
                    portal_top <= world_y < portal_bottom)

        class PortalAnimation:
            def __init__(self, frames, x, y, direction, width_tiles, height_tiles):
                self.frames = frames
                self.x = x
                self.y = y
                self.direction = direction
                self.width_tiles = width_tiles
                self.height_tiles = height_tiles
                self.current_frame = 0
                self.timer = 0
                self.frame_delay = 5

            def update(self):
                self.timer += 1
                if self.timer >= self.frame_delay:
                    self.timer = 0
                    self.current_frame = (self.current_frame + 1) % len(self.frames)

            def draw(self, screen, camera_x, camera_y, zoom, screen_width, screen_height):
                screen_x = (self.x - camera_x) * zoom
                screen_y = (self.y - camera_y) * zoom
                w_pixels = self.width_tiles * TILE_SIZE * zoom
                h_pixels = self.height_tiles * TILE_SIZE * zoom
                if (-w_pixels <= screen_x <= screen_width + w_pixels and
                        -h_pixels <= screen_y <= screen_height + h_pixels):
                    frame_img = self.frames[self.current_frame]
                    scaled_img = pygame.transform.scale(frame_img, (int(w_pixels), int(h_pixels)))
                    screen.blit(scaled_img, (screen_x, screen_y))

    # ============================================================
    # LOAD PORTAL FRAMES
    # ============================================================
    def load_portal_frames(self):
        def load_portal_frames(direction, width_tiles, height_tiles):
            frames = []
            for i in range(9):
                filename = f"sprite_{direction}_portal{i}.png"
                path = os.path.join(self.PORTAL_PATH, filename)
                try:
                    if os.path.exists(path):
                        img = pygame.image.load(path).convert_alpha()
                        scaled_width = TILE_SIZE * width_tiles
                        scaled_height = TILE_SIZE * height_tiles
                        img = pygame.transform.scale(img, (scaled_width, scaled_height))
                        frames.append(img)
                    else:
                        surf = pygame.Surface((TILE_SIZE * width_tiles, TILE_SIZE * height_tiles))
                        surf.fill((128, 128, 128))
                        frames.append(surf)
                except Exception:
                    surf = pygame.Surface((TILE_SIZE * width_tiles, TILE_SIZE * height_tiles))
                    surf.fill((128, 128, 128))
                    frames.append(surf)
            return frames if frames else None

        cache = {}
        for d, size in PORTAL_SIZES.items():
            cache[d] = load_portal_frames(d, size[0], size[1])
        return cache

    # ============================================================
    # LOAD STATIC PORTALS
    # ============================================================
    def load_static_portals(self):
        print("🔍 Loading portals from map...")
        for y, row in enumerate(self.render_map):
            row_list = list(row)
            modified = False
            for x, c in enumerate(row):
                if c == 'r':
                    portal = self.Portal(x, y, 'right', is_static=True)
                    portal.set_animation(self.portal_frames_cache['right'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                    print(f"✅ Found RIGHT portal at: ({x}, {y})")
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                    print(f"✅ Found LEFT portal at: ({x}, {y})")
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                    print(f"✅ Found UP portal at: ({x}, {y})")
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                    print(f"✅ Found DOWN portal at: ({x}, {y})")
            if modified:
                self.render_map[y] = ''.join(row_list)

        if len(self.portals) == 0:
            print("⚠️ No portals found in the map!")

    # ============================================================
    # CREATE DEFAULT MAP
    # ============================================================
    def _create_default_map(self):
        self.game_map = [
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
            "G######################################G",
            "G#     #                              #G",
            "G#     #   GGGGGG   GGGGGG   GGGGGG   #G",
            "G#     #   G    G   G    G   G    G   #G",
            "G#     #   G    G   G    G   G    G   #G",
            "G#     #   GGGGGG   GGGGGG   GGGGGG   #G",
            "G#     #                              #G",
            "G#     ################################G",
            "G#                                    #G",
            "G#                                    #G",
            "G######################################G",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
        ]
        self.ROWS = len(self.game_map)
        self.COLS = max(len(r) for r in self.game_map) if self.game_map else 0
        self.MAP_WIDTH = self.COLS * TILE_SIZE
        self.MAP_HEIGHT = self.ROWS * TILE_SIZE
        self.render_map = self.game_map.copy()
        self.npc_positions_data = {}

    # ============================================================
    # CAN MOVE
    # ============================================================
    def can_move(self, nx, ny):
        padding = 4
        corners = [
            (nx + padding, ny + padding),
            (nx + TILE_SIZE - padding - 1, ny + padding),
            (nx + padding, ny + TILE_SIZE - padding - 1),
            (nx + TILE_SIZE - padding - 1, ny + TILE_SIZE - padding - 1)
        ]

        for cx, cy in corners:
            col = int(cx // TILE_SIZE)
            row = int(cy // TILE_SIZE)
            if row < 0 or row >= self.ROWS or col < 0 or col >= self.COLS:
                return False
            if row >= len(self.game_map) or col >= len(self.game_map[row]):
                return False
            tile = self.game_map[row][col]

            if tile not in self.WALKABLE_TILES:
                return False

        return True

    # ============================================================
    # UPDATE CAMERA
    # ============================================================
    def update_camera(self):
        target_x = self.player_x + TILE_SIZE // 2 - (self.width // 2) / ZOOM
        target_y = self.player_y + TILE_SIZE // 2 - (self.height // 2) / ZOOM
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1

        min_cam_x = 0
        max_cam_x = max(0, self.MAP_WIDTH - self.width / ZOOM)
        min_cam_y = 0
        max_cam_y = max(0, self.MAP_HEIGHT - self.height / ZOOM)

        self.camera_x = max(min_cam_x, min(self.camera_x, max_cam_x))
        self.camera_y = max(min_cam_y, min(self.camera_y, max_cam_y))

    # ============================================================
    # UPDATE GESTURE
    # ============================================================
    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME
        self.current_gesture = current_gesture
        self.hand_detected = current_gesture not in ["NO HAND", "NO HAND (GRACE)"]
        self.fist_closed = fist_start_time > 0

        if self.hand_detected:
            self.mouse_moving = False
            self.mouse_target_x = None
            self.mouse_target_y = None

    # ============================================================
    # START MINIGAME
    # ============================================================
    def start_minigame(self, stall_number):
        """Start a minigame based on the stall number"""
        self.minigame_active = True
        self.current_stall_index = stall_number
        self.minigame_score = 0
        self.minigame_attempts = 0
        self.show_feedback = False
        self.selected_answer = -1
        self.answer_buttons = []

        # Generate question based on stall type
        if stall_number == 1:
            self.generate_money_question()
        elif stall_number == 2:
            self.generate_addition_question()
        elif stall_number == 3:
            self.generate_subtraction_question()
        elif stall_number == 4:
            self.generate_measurement_question()
        elif stall_number == 5:
            self.generate_pattern_question()

        print(f"🎮 Starting minigame: {self.stall_themes[stall_number]['name']}")

    # ============================================================
    # GRADE 2 SIMPLIFIED MINIGAME QUESTION GENERATORS
    # ============================================================
    def generate_money_question(self):
        """Generate a simple money counting question for Grade 2"""
        # Use simpler combinations: 20, 50, 100 peso bills only (no 500 or 1000 for Grade 2)
        bills = [20, 50, 100]
        num_bills = random.randint(2, 3)
        selected_bills = random.choices(bills, k=num_bills)
        total = sum(selected_bills)

        wrong_answers = []
        while len(wrong_answers) < 3:
            wrong = total + random.randint(-50, 50)
            if wrong != total and wrong > 0 and wrong not in wrong_answers:
                wrong_answers.append(wrong)

        choices = [total] + wrong_answers
        random.shuffle(choices)

        self.current_question = {
            "question": f"Count the money: {', '.join(['₱' + str(b) for b in selected_bills])}",
            "choices": [f"₱{c}" for c in choices],
            "correct": choices.index(total)
        }

    def generate_addition_question(self):
        """Generate a simple addition question for Grade 2"""
        # Simple 2-digit addition without regrouping
        num1 = random.randint(10, 50)
        num2 = random.randint(10, 50)
        # Make sure sum is less than 100
        total = num1 + num2

        wrong_answers = []
        while len(wrong_answers) < 3:
            wrong = total + random.randint(-10, 10)
            if wrong != total and wrong > 0 and wrong not in wrong_answers:
                wrong_answers.append(wrong)

        choices = [total] + wrong_answers
        random.shuffle(choices)

        self.current_question = {
            "question": f"What is {num1} + {num2}?",
            "choices": [str(c) for c in choices],
            "correct": choices.index(total)
        }

    def generate_subtraction_question(self):
        """Generate a simple subtraction question for Grade 2"""
        # Simple 2-digit subtraction without regrouping
        num1 = random.randint(30, 99)
        num2 = random.randint(10, num1 - 10)
        total = num1 - num2

        wrong_answers = []
        while len(wrong_answers) < 3:
            wrong = total + random.randint(-10, 10)
            if wrong != total and wrong > 0 and wrong not in wrong_answers:
                wrong_answers.append(wrong)

        choices = [total] + wrong_answers
        random.shuffle(choices)

        self.current_question = {
            "question": f"What is {num1} - {num2}?",
            "choices": [str(c) for c in choices],
            "correct": choices.index(total)
        }

    def generate_measurement_question(self):
        """Generate a simple measurement question for Grade 2"""
        # Simple comparisons: which is longer/shorter?
        pairs = [
            ("pencil", 15, "book", 25),
            ("chair", 45, "table", 70),
            ("ruler", 30, "book", 25),
            ("door", 200, "window", 150),
            ("phone", 15, "tablet", 25)
        ]

        obj1, len1, obj2, len2 = random.choice(pairs)

        question_text = f"Which is longer, a {obj1} ({len1} cm) or a {obj2} ({len2} cm)?"
        correct_answer = 0 if len1 > len2 else 1

        choices = [f"{obj1} ({len1} cm)", f"{obj2} ({len2} cm)"]

        self.current_question = {
            "question": question_text,
            "choices": choices,
            "correct": correct_answer
        }

    def generate_pattern_question(self):
        """Generate a simple pattern question for Grade 2"""
        # Simple patterns with small numbers and simple differences
        patterns = [
            ([2, 4, 6, 8], 10),
            ([5, 10, 15, 20], 25),
            ([3, 6, 9, 12], 15),
            ([1, 3, 5, 7], 9),
            ([10, 20, 30, 40], 50),
            ([2, 5, 8, 11], 14),
            ([1, 4, 7, 10], 13)
        ]

        pattern, next_num = random.choice(patterns)
        pattern_str = ", ".join(str(p) for p in pattern)

        wrong_answers = []
        while len(wrong_answers) < 3:
            wrong = next_num + random.randint(-3, 3)
            if wrong != next_num and wrong > 0 and wrong not in wrong_answers:
                wrong_answers.append(wrong)

        choices = [next_num] + wrong_answers
        random.shuffle(choices)

        self.current_question = {
            "question": f"What is the next number in the pattern?\n{pattern_str}, ...?",
            "choices": [str(c) for c in choices],
            "correct": choices.index(next_num)
        }

    # ============================================================
    # CHECK ANSWER
    # ============================================================
    def check_answer(self, choice_index):
        """Check if the selected answer is correct"""
        if self.current_question is None:
            return

        self.selected_answer = choice_index
        correct = choice_index == self.current_question["correct"]

        if correct:
            self.minigame_score = 10
            self.feedback_text = "✅ Correct! +10 points!"
            self.feedback_color = (34, 197, 94)
            self.show_feedback = True
            self.feedback_timer = 60
            self.stall_completed_status[self.current_stall_index] = True
            print(f"✅ Correct answer! Stall {self.current_stall_index} completed!")
        else:
            self.minigame_attempts += 1
            self.feedback_text = f"❌ Try again! (Attempt {self.minigame_attempts}/{self.max_attempts})"
            self.feedback_color = (244, 63, 94)
            self.show_feedback = True
            self.feedback_timer = 60

            if self.minigame_attempts >= self.max_attempts:
                self.feedback_text = "❌ Moving to next stall."
                self.minigame_score = 0
                self.stall_completed_status[self.current_stall_index] = True
                self.feedback_timer = 90
                print(f"❌ Max attempts reached for stall {self.current_stall_index}")

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        if self.minigame_active:
            self.mouse_moving = False
            self.mouse_target_x = None
            self.mouse_target_y = None
            self.anim_frame = 0
            return

        vx, vy = 0, 0
        movement_triggered = False

        if self.hand_detected and self.current_gesture not in ["NO HAND", "NO HAND (GRACE)"]:
            center_x, center_y = self.width // 2, self.height // 2
            cursor_x, cursor_y = self.cursor_pos
            dx = cursor_x - center_x
            dy = cursor_y - center_y

            if abs(dx) > 60:
                vx = SPEED if dx > 0 else -SPEED
                self.player_dir = "right" if dx > 0 else "left"
                movement_triggered = True

            if abs(dy) > 60:
                vy = SPEED if dy > 0 else -SPEED
                self.player_dir = "down" if dy > 0 else "up"
                movement_triggered = True

            self.mouse_moving = False
            self.mouse_target_x = None
            self.mouse_target_y = None

        elif self.mouse_moving and self.mouse_target_x is not None and self.mouse_target_y is not None:
            dx = self.mouse_target_x - self.player_x
            dy = self.mouse_target_y - self.player_y
            distance = math.hypot(dx, dy)

            if distance > 5:
                if distance > 0:
                    dx = dx / distance
                    dy = dy / distance
                vx = int(dx * SPEED)
                vy = int(dy * SPEED)
                self.player_dir = "right" if dx > 0 else "left" if abs(dx) > abs(dy) else "down" if dy > 0 else "up"
                movement_triggered = True
            else:
                self.mouse_moving = False
                self.mouse_target_x = None
                self.mouse_target_y = None
                movement_triggered = False

        new_x = self.player_x + vx
        new_y = self.player_y + vy

        if self.can_move(new_x, self.player_y):
            self.player_x = new_x
        if self.can_move(self.player_x, new_y):
            self.player_y = new_y

        if movement_triggered:
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_frame = 0

    # ============================================================
    # CHECK STALL INTERACTION
    # ============================================================
    def check_stall_interaction(self):
        """Check if player is near a stall and interact"""
        player_tile_x = self.player_x // TILE_SIZE
        player_tile_y = self.player_y // TILE_SIZE

        for stall_num, pos in self.stall_positions.items():
            stall_tile_x = pos[0] // TILE_SIZE
            stall_tile_y = pos[1] // TILE_SIZE

            if abs(player_tile_x - stall_tile_x) <= 1 and abs(player_tile_y - stall_tile_y) <= 1:
                if not self.minigame_active and not self.stall_completed_status[stall_num]:
                    self.start_minigame(stall_num)
                    return True
        return False

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1

        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt

        # Update feedback timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer == 0:
                self.show_feedback = False
                if self.stall_completed_status[self.current_stall_index]:
                    self.minigame_active = False
                    self.current_question = None
                    self.selected_answer = -1
                    self.total_score += self.minigame_score
                    print(f"💰 Stall {self.current_stall_index} completed! Total Score: {self.total_score}")

        # Check if all stalls are completed
        completed_stalls = sum(1 for v in self.stall_completed_status.values() if v)
        if completed_stalls >= 5 and self.game_state != "complete":
            self.game_state = "complete"
            print("🎉 All stalls completed! Portal unlocked!")
            print("📍 Enter the RIGHT portal (marked with 'r' on the map) to return!")

        # Only allow movement and interaction if not in minigame
        if not self.minigame_active:
            self.update_player_movement()
            self.check_stall_interaction()

        # Check portal teleport
        self.check_portal_teleport_on_hold()

        # Update portals
        for portal in self.portals:
            portal.update_animation()

        # Update camera
        self.update_camera()

    # ============================================================
    # CHECK PORTAL TELEPORT
    # ============================================================
    def check_portal_teleport_on_hold(self):
        current_portal = None
        for portal in self.portals:
            if portal.contains_position(self.player_x, self.player_y):
                current_portal = portal
                break

        if current_portal:
            if current_portal.direction == self.goal_portal_direction:
                if self.game_state == "complete":
                    print("✅ Goal portal activated! Returning to stage select...")
                    self.return_to_stage_select()
                    return True
                else:
                    print("🔒 Portal locked! Complete all stalls first!")
                    return False

            # Regular portal teleport (to another portal on same map)
            other_portals = [p for p in self.portals if p != current_portal]
            if other_portals and self.fist_closed and self.teleport_cooldown <= 0:
                target_portal = other_portals[0]
                self.player_x = target_portal.get_center_x() - TILE_SIZE // 2
                self.player_y = target_portal.get_center_y() - TILE_SIZE // 2
                self.teleport_cooldown = self.TELEPORT_COOLDOWN_TIME
                print(f"🔄 Teleported to {target_portal.direction} portal!")
                return True
        return False

    # ============================================================
    # RETURN TO STAGE SELECT
    # ============================================================
    def return_to_stage_select(self):
        if self.main_menu:
            self.main_menu.current_screen = "stage_select"
            self.main_menu.quarter2 = None
            from .stageselect import StageSelect
            self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
            print("🏠 Returning to stage select")
            self.completed = True
        return "back"

    # ============================================================
    # TRIGGER CLICK
    # ============================================================
    def trigger_click(self, pos):
        print(f"🖱️ Quarter2 Market click at: {pos}")

        # Handle minigame clicks
        if self.minigame_active and self.current_question:
            box_w, box_h = 580, 420
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2

            button_w, button_h = 500, 42
            button_x = box_x + (box_w - button_w) // 2
            button_y_start = box_y + 140
            spacing = 52

            for i in range(len(self.current_question["choices"])):
                b_y = button_y_start + i * spacing
                btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)
                if btn_rect.collidepoint(pos):
                    if not self.show_feedback:
                        self.check_answer(i)
                    break

        # Handle mouse movement (click on ground)
        elif not self.minigame_active:
            world_x = (pos[0] / ZOOM) + self.camera_x
            world_y = (pos[1] / ZOOM) + self.camera_y

            col = int(world_x // TILE_SIZE)
            row = int(world_y // TILE_SIZE)

            if 0 <= row < self.ROWS and 0 <= col < self.COLS:
                tile = self.game_map[row][col]
                if tile in self.WALKABLE_TILES:
                    self.mouse_target_x = world_x
                    self.mouse_target_y = world_y
                    self.mouse_moving = True
                    self.mouse_move_timer = 0.5

    # ============================================================
    # DRAW TILE
    # ============================================================
    def draw_tile(self, c, world_x, world_y):
        screen_x = (world_x - self.camera_x) * ZOOM
        screen_y = (world_y - self.camera_y) * ZOOM

        margin = TILE_SIZE * ZOOM * 2
        if (-margin <= screen_x <= self.width + margin and
                -margin <= screen_y <= self.height + margin):
            image = self.tile_images.get(c, self.fallback_tile)
            scaled_size = int(TILE_SIZE * ZOOM)
            scaled_image = pygame.transform.scale(image, (scaled_size, scaled_size))
            self.screen.blit(scaled_image, (screen_x, screen_y))

    # ============================================================
    # DRAW PLAYER
    # ============================================================
    def draw_player(self):
        screen_x = (self.player_x - self.camera_x) * ZOOM
        screen_y = (self.player_y - self.camera_y) * ZOOM

        if (-TILE_SIZE * ZOOM <= screen_x <= self.width + TILE_SIZE * ZOOM and
                -TILE_SIZE * ZOOM <= screen_y <= self.height + TILE_SIZE * ZOOM):
            sprite = self.player_sprites[self.player_dir][self.anim_frame]
            scaled_size = int(TILE_SIZE * ZOOM)
            scaled_sprite = pygame.transform.scale(sprite, (scaled_size, scaled_size))
            self.screen.blit(scaled_sprite, (screen_x, screen_y))

    # ============================================================
    # DRAW STALLS
    # ============================================================
    def draw_stalls(self):
        """Draw stall markers on the map"""
        for stall_num, pos in self.stall_positions.items():
            screen_x = (pos[0] - self.camera_x) * ZOOM
            screen_y = (pos[1] - self.camera_y) * ZOOM

            if -TILE_SIZE * ZOOM <= screen_x <= self.width + TILE_SIZE * ZOOM and \
                    -TILE_SIZE * ZOOM <= screen_y <= self.height + TILE_SIZE * ZOOM:

                is_completed = self.stall_completed_status[stall_num]
                bg_color = (34, 197, 94) if is_completed else (139, 69, 19)

                stall_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE * ZOOM, TILE_SIZE * ZOOM)
                pygame.draw.rect(self.screen, bg_color, stall_rect)
                pygame.draw.rect(self.screen, (255, 215, 0), stall_rect, 2)

                if is_completed:
                    check_font = pygame.font.SysFont("Arial", int(30 * ZOOM))
                    check_surf = check_font.render("✓", True, (255, 255, 255))
                    check_rect = check_surf.get_rect(center=(screen_x + TILE_SIZE * ZOOM // 2,
                                                             screen_y + TILE_SIZE * ZOOM // 2))
                    self.screen.blit(check_surf, check_rect)
                else:
                    icon_font = pygame.font.SysFont("Arial", int(20 * ZOOM))
                    icon = self.stall_themes[stall_num]["icon"]
                    icon_surf = icon_font.render(icon, True, (255, 255, 255))
                    icon_rect = icon_surf.get_rect(center=(screen_x + TILE_SIZE * ZOOM // 2,
                                                           screen_y + TILE_SIZE * ZOOM // 2 - 8))
                    self.screen.blit(icon_surf, icon_rect)

                    num_font = pygame.font.SysFont("Arial", int(12 * ZOOM), bold=True)
                    num_surf = num_font.render(str(stall_num), True, (255, 255, 0))
                    num_rect = num_surf.get_rect(center=(screen_x + TILE_SIZE * ZOOM // 2,
                                                         screen_y + TILE_SIZE * ZOOM - int(10 * ZOOM)))
                    self.screen.blit(num_surf, num_rect)

                name_font = pygame.font.SysFont("Comic Sans MS", int(8 * ZOOM))
                name_surf = name_font.render(self.stall_themes[stall_num]["name"], True, (255, 255, 255))
                name_rect = name_surf.get_rect(center=(screen_x + TILE_SIZE * ZOOM // 2,
                                                       screen_y - int(10 * ZOOM)))
                if name_rect.y > 0:
                    self.screen.blit(name_surf, name_rect)

    # ============================================================
    # DRAW MINIGAME
    # ============================================================
    def draw_minigame(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 580, 420
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=8)

        stall_info = self.stall_themes.get(self.current_stall_index, {"name": "Stall", "topic": ""})
        title_font = pygame.font.SysFont("Comic Sans MS", 20, bold=True)
        title_surf = title_font.render(f"{stall_info['icon']} {stall_info['name']}", True, (255, 215, 0))
        self.screen.blit(title_surf, (box_x + 25, box_y + 15))

        topic_font = pygame.font.SysFont("Comic Sans MS", 14)
        topic_surf = topic_font.render(stall_info['topic'], True, (200, 200, 200))
        self.screen.blit(topic_surf, (box_x + 25, box_y + 40))

        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 60), (box_x + box_w - 25, box_y + 60), 1)

        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        wrapped_q = self.wrap_text(self.current_question["question"], q_font, box_w - 50)

        y_text = box_y + 75
        for line in wrapped_q:
            txt_surf = q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 22

        button_w, button_h = 500, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 140
        spacing = 52

        for i, choice in enumerate(self.current_question["choices"]):
            b_y = button_y_start + i * spacing
            btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)

            if self.selected_answer == i:
                bg_color = (34, 197, 94) if i == self.current_question["correct"] else (244, 63, 94)
            else:
                is_hovered = btn_rect.collidepoint(self.cursor_pos)
                bg_color = (200, 100, 255) if is_hovered else (30, 41, 59)

            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

            c_surf = q_font.render(choice, True, (255, 255, 255))
            c_rect = c_surf.get_rect(center=btn_rect.center)
            self.screen.blit(c_surf, c_rect)

        if self.show_feedback:
            feedback_y = button_y_start + (len(self.current_question["choices"]) * spacing) + 20
            fb_surf = q_font.render(self.feedback_text, True, self.feedback_color)
            fb_rect = fb_surf.get_rect(center=(box_x + box_w // 2, feedback_y))
            self.screen.blit(fb_surf, fb_rect)

        score_y = box_y + box_h - 30
        score_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
        score_surf = score_font.render(f"Score: {self.total_score + self.minigame_score}", True, (255, 215, 0))
        self.screen.blit(score_surf, (box_x + box_w - score_surf.get_width() - 25, score_y))

        attempts_surf = score_font.render(f"Attempts: {self.minigame_attempts}/{self.max_attempts}", True,
                                          (200, 200, 200))
        self.screen.blit(attempts_surf, (box_x + 25, score_y))

    # ============================================================
    # DRAW UI
    # ============================================================
    def draw_ui(self):
        if self.hand_detected:
            color = (255, 200, 0) if self.fist_start_time > 0 else (255, 255, 255)
            pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
            pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        box_w, box_h = 340, 120
        box_x = 20
        box_y = self.height - box_h - 20

        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((15, 23, 42, 190))
        self.screen.blit(bg_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (218, 165, 32), (box_x, box_y, box_w, box_h), 2, border_radius=8)

        title_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        title_surf = title_font.render("🎯 MARKET ADVENTURE", True, (255, 215, 0))
        self.screen.blit(title_surf, (box_x + 15, box_y + 8))

        item_font = pygame.font.SysFont("Comic Sans MS", 14)
        score_surf = item_font.render(f"⭐ Score: {self.total_score}/50", True, (255, 255, 255))
        self.screen.blit(score_surf, (box_x + 15, box_y + 32))

        completed = sum(1 for v in self.stall_completed_status.values() if v)
        stalls_surf = item_font.render(f"🏪 Stalls: {completed}/5 completed", True, (255, 255, 255))
        self.screen.blit(stalls_surf, (box_x + 15, box_y + 52))

        bar_x = box_x + 15
        bar_y = box_y + 75
        bar_w = box_w - 30
        bar_h = 10
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        progress = completed / 5
        pygame.draw.rect(self.screen, (34, 197, 94), (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=5)

        inst_font = pygame.font.SysFont("Comic Sans MS", 11)
        inst_surf = inst_font.render("Walk to a stall to start the minigame!", True, (200, 200, 200))
        self.screen.blit(inst_surf, (box_x + 15, box_y + 92))

        if self.game_state == "complete":
            portal_surf = self.big_font.render("✨ PORTAL OPEN! ✨", True, (34, 197, 94))
            portal_rect = portal_surf.get_rect(center=(self.width // 2, 60))
            for i in range(5, 0, -1):
                glow_surf = self.big_font.render("✨ PORTAL OPEN! ✨", True, (34, 197, 94, 50 - i * 10))
                glow_surf.set_alpha(50 - i * 10)
                self.screen.blit(glow_surf, (portal_rect.x - i, portal_rect.y - i))
            self.screen.blit(portal_surf, portal_rect)
        else:
            portal_status = self.big_font.render("🔒 Complete all stalls", True, (244, 63, 94))
            portal_rect = portal_status.get_rect(center=(self.width // 2, 60))
            self.screen.blit(portal_status, portal_rect)

        if self.show_info:
            info_lines = [
                f"Map: {self.map_name}",
                f"Position: ({self.player_x // TILE_SIZE}, {self.player_y // TILE_SIZE})",
                f"Hand: {'YES' if self.hand_detected else 'NO'}",
                f"Press ESC to return to menu"
            ]

            y_offset = 10
            for line in info_lines:
                text = self.small_font.render(line, True, (255, 255, 255))
                text_bg = pygame.Surface((text.get_width() + 4, text.get_height() + 4))
                text_bg.set_alpha(180)
                text_bg.fill((0, 0, 0))
                self.screen.blit(text_bg, (8, y_offset - 2))
                self.screen.blit(text, (10, y_offset))
                y_offset += 18

    # ============================================================
    # WRAP TEXT
    # ============================================================
    def wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    # ============================================================
    # DRAW - MAIN DRAW METHOD
    # ============================================================
    def draw(self):
        self.screen.fill((0, 0, 0))

        start_col = max(0, int(self.camera_x / TILE_SIZE) - 2)
        end_col = min(self.COLS, int((self.camera_x + self.width / ZOOM) / TILE_SIZE) + 3)
        start_row = max(0, int(self.camera_y / TILE_SIZE) - 2)
        end_row = min(self.ROWS, int((self.camera_y + self.height / ZOOM) / TILE_SIZE) + 3)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char != 'T':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw portals
        for portal in self.portals:
            if portal.direction == self.goal_portal_direction and self.game_state != "complete":
                screen_x = (portal.get_world_x() - self.camera_x) * ZOOM
                screen_y = (portal.get_world_y() - self.camera_y) * ZOOM
                scaled_width = int(portal.get_width_pixels() * ZOOM)
                scaled_height = int(portal.get_height_pixels() * ZOOM)
                pygame.draw.rect(self.screen, (100, 0, 0), (screen_x, screen_y, scaled_width, scaled_height))
                pygame.draw.rect(self.screen, (255, 0, 0), (screen_x, screen_y, scaled_width, scaled_height), 3)
                lock_font = pygame.font.SysFont("Arial", int(30 * ZOOM))
                lock_surf = lock_font.render("🔒", True, (255, 255, 255))
                lock_rect = lock_surf.get_rect(center=(screen_x + scaled_width // 2, screen_y + scaled_height // 2))
                self.screen.blit(lock_surf, lock_rect)
            else:
                portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height)

        self.draw_stalls()
        self.draw_player()

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char == 'T':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        if self.minigame_active and self.current_question:
            self.draw_minigame()

        self.draw_ui()

    # ============================================================
    # HANDLE EVENT
    # ============================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.main_menu:
                    self.main_menu.current_screen = "menu"
                    self.main_menu.quarter2 = None
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info
        return None

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()