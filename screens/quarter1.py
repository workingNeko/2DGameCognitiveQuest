# screens/quarter1.py - Quarter 1 Map Handler

import pygame
import os
import sys
import cv2
import numpy as np
import time
from .map_loader import MapLoader

# ============================================================
# SETTINGS
# ============================================================
TILE_SIZE = 32
FPS = 60
SPEED = 4

# Camera zoom settings - PERMANENT ZOOM
ZOOM = 1.50  # Fixed zoom level

# Portal settings
PORTAL_SIZES = {
    'right': (3, 3),  # 3 tiles wide, 3 tiles tall (square)
    'left': (2, 3),  # 2 tile wide, 3 tiles tall (vertical strip)
    'up': (3, 3),  # 3 tiles wide, 3 tiles tall (square)
    'down': (3, 2)  # 3 tiles wide, 2 tile tall (horizontal strip)
}


class Quarter1:
    def __init__(self, screen, main_menu, map_name):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()
        self.map_name = map_name  # 'map1.txt' or 'map2.txt'
        self.is_quiz_map = any(m in self.map_name.lower() for m in ["map1", "map2", "map3"])

        # ============================================================
        # GESTURE SYSTEM - USE MAIN MENU'S DATA
        # ============================================================
        self.cursor_pos = (self.width // 2, self.height // 2)
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False
        self.hand_detected = False
        self.fist_closed = False

        # For tracking clicks to prevent multiple triggers
        self.last_click_time = 0
        self.click_cooldown = 0.5

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

        self.NPC_PATH_BROMEN = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "bromen"
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

        self.NPC_PATH_BALL = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "Ball"
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

        self.NPC_PATH_KNIGHT = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "knight"
        )

        # ============================================================
        # MAP LOADER
        # ============================================================
        self.map_loader = MapLoader(self.BASE_DIR)
        self.current_map_name = map_name

        # Load the specified map
        if not self.map_loader.load_map(map_name):
            print(f"❌ Failed to load {map_name}")
            self._create_default_map()
        else:
            # Use the loaded map data
            self.game_map = self.map_loader.game_map
            self.ROWS = self.map_loader.rows
            self.COLS = self.map_loader.cols
            self.MAP_WIDTH = self.COLS * TILE_SIZE
            self.MAP_HEIGHT = self.ROWS * TILE_SIZE
            self.current_map_name = self.map_loader.current_map_name

            # Get NPC positions from map loader
            self.npc_positions_data = self.map_loader.npc_positions

            # Replace NPC markers with walkable tiles for rendering
            self.render_map = self.map_loader.replace_npc_markers_with_walkable_tiles()

            # Scan map for quiz stations 1, 2, 3, 4, 5
            self.quiz_stations = {}
            for y, row in enumerate(self.game_map):
                for x, c in enumerate(row):
                    if c in ['1', '2', '3', '4', '5']:
                        num = int(c)
                        self.quiz_stations[num] = (x, y)
                        print(f"📍 Quiz Station {num} found at: ({x}, {y})")

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
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8","P"}

        # ============================================================
        # LOAD PLAYER SPRITES
        # ============================================================
        self.player_sprites = self.load_player_sprites()
        self.anim_frame = 0
        self.anim_timer = 0

        # ============================================================
        # LOAD NPC SPRITES
        # ============================================================
        # Bromen NPC (animated)
        self.npc_bromen_sprites = self.load_npc_sprites_animated(self.NPC_PATH_BROMEN, "bromen")
        self.npc_bromen_anim_frame = 0
        self.npc_bromen_anim_timer = 0
        self.npc_bromen_x = 0
        self.npc_bromen_y = 0
        self.npc_bromen_tile_x = 0
        self.npc_bromen_tile_y = 0
        self.npc_bromen_found = False

        # Oldman NPC (static)
        self.npc_oldman_sprite = None
        self.npc_oldman_x = 0
        self.npc_oldman_y = 0
        self.npc_oldman_tile_x = 0
        self.npc_oldman_tile_y = 0
        self.npc_oldman_found = False
        self.npc_oldman_left_sprites = []
        self.npc_oldman_right_sprites = []
        self.npc_oldman_up_sprites = []
        self.npc_oldman_down_sprites = []

        # Skeleton NPC (static)
        self.npc_skeleton_sprite = None
        self.npc_skeleton_x = 0
        self.npc_skeleton_y = 0
        self.npc_skeleton_tile_x = 0
        self.npc_skeleton_tile_y = 0
        self.npc_skeleton_found = False

        # Knight NPC (static & interactive)
        self.npc_knight_sprite = None
        self.npc_knight_x = 0
        self.npc_knight_y = 0
        self.npc_knight_tile_x = 0
        self.npc_knight_tile_y = 0
        self.npc_knight_found = False
        self.npc_knight_left_sprites = []
        self.npc_knight_down_sprites = []
        self.npc_knight_right_sprites = []
        self.npc_knight_up_sprites = []
        self.npc_knight_dir = "down"
        self.npc_knight_anim_frame = 0
        self.npc_knight_anim_timer = 0

        # ============================================================
        # LOAD STATIC NPC SPRITES
        # ============================================================
        self.load_static_npc_sprites()

        # ============================================================
        # SPAWN PLAYER AND FIND NPCS
        # ============================================================
        self.player_x = 0
        self.player_y = 0
        self.player_dir = "down"

        # Spawn player at 'P' position from map
        if self.map_loader.player_start:
            start_x, start_y = self.map_loader.player_start
            self.player_x = start_x * TILE_SIZE
            self.player_y = start_y * TILE_SIZE
            print(f"Player spawned at: ({start_x}, {start_y})")
        else:
            # Fallback: find P in map
            for y, row in enumerate(self.game_map):
                for x, c in enumerate(row):
                    if c == "P":
                        self.player_x = x * TILE_SIZE
                        self.player_y = y * TILE_SIZE
                        print(f"Player spawned at: ({x}, {y})")
                        break
                if self.player_x != 0:
                    break
        for y, row in enumerate(self.render_map):
            if "P" in row:
                self.render_map[y] = row.replace("P", "G")
        # Initialize NPC positions from map data
        self._init_npc_positions()

        # Overwrite Old Man position to Quiz Station 1 for map1.txt quiz sequence
        self.locked_portals = []
        self.shape_npcs = {}
        self.active_shape_id = None

        if self.is_quiz_map and hasattr(self, 'quiz_stations'):
            self.npc_oldman_found = False  # Disable single ball NPC
            shape_names = {
                1: "circle",
                2: "heart",
                3: "square",
                4: "star",
                5: "diamond"
            }
            for num, pos in self.quiz_stations.items():
                if num in shape_names:
                    self.shape_npcs[num] = {
                        "id": num,
                        "name": shape_names[num],
                        "tile_x": pos[0],
                        "tile_y": pos[1],
                        "x": pos[0] * TILE_SIZE,
                        "y": pos[1] * TILE_SIZE,
                        "answered": False
                    }
                    print(f"🏀 Spawned Shape NPC {num}: {shape_names[num]} at ({pos[0]}, {pos[1]})")
        else:
            self.npc_oldman_found = False

        # Shape Quiz state variables
        self.quiz_state = 0  # 0: waiting proximity, 1: dialog Q, 2: wrong try again, 3: correct phrase transition, 4: pathfinding walking, 5: final speech, 6: quiz complete
        self.quiz_station_index = 1  # current station (1-5)
        self.current_question_index = 0
        self.selected_choice_index = -1  # choice highlighted

        # Shape NPC animations
        self.shape_npc_anim_frame = 0
        self.shape_npc_anim_timer = 0

        # Station Standby Directions
        if "map2" in self.map_name.lower():
            self.station_directions = {
                1: "left",
                2: "up",
                3: "left",
                4: "left",
                5: "right"
            }
        elif "map3" in self.map_name.lower():
            self.station_directions = {
                1: "right",
                2: "right",
                3: "right",
                4: "left",
                5: "left"
            }
        else:
            self.station_directions = {
                1: "right",
                2: "left",
                3: "left",
                4: "down",
                5: "left"
            }
        self.npc_oldman_dir = self.station_directions.get(1, "right")

        # ============================================================
        # AREA TITLE ANIMATION
        # ============================================================
        self.title_elapsed = 0.0
        self.title_duration = 5.0
        self.title_active = True

        # Load Pixelfont
        self.pixel_font_path = "assets/fonts/Pixelfont.otf"
        self.pixel_font_size = 72
        try:
            self.title_font = pygame.font.Font(self.pixel_font_path, self.pixel_font_size)
        except Exception:
            self.title_font = pygame.font.SysFont("Consolas", self.pixel_font_size, bold=True)

        self.title_text = "Geometry Forest"
        self.title_spacing = 12

        self.title_text_color = (255, 255, 255) # White
        self.title_outline_color = (0, 0, 0) # Black outline
        self.title_glow_color = (180, 180, 180) # Grey glow

        # Pre-render letters
        self.title_letters = []
        for ch in self.title_text:
            glow = self.title_font.render(ch, False, self.title_glow_color)
            outline = self.title_font.render(ch, False, self.title_outline_color)
            main = self.title_font.render(ch, False, self.title_text_color)
            self.title_letters.append({
                "glow": glow,
                "outline": outline,
                "main": main,
                "width": main.get_width()
            })
        self.title_total_width = sum(l["width"] for l in self.title_letters) + self.title_spacing * (len(self.title_text) - 1)

        # Correct answer random responses
        self.current_correct_phrase = ""
        self.correct_phrases = [
            "Amazing! now let's go to the next one!",
            "That's great! Now to the next one!",
            "You're good at this, Now let's go to the next one!"
        ]

        # Old Man walking animations
        self.npc_oldman_anim_frame = 0
        self.npc_oldman_anim_timer = 0
        self.player_block_timer = 0
        self.npc_oldman_path = []

        # Questions List
        self.quiz_questions = [
            {
                "question": "Which shape is half of a circle?",
                "choices": ["A. Triangle", "B. Half circle", "C. Rectangle", "D. Square"],
                "correct": 1  # B
            },
            {
                "question": "A whole circle is cut into four equal parts. What is one part called?",
                "choices": ["A. Half circle", "B. Quarter circle", "C. Triangle", "D. Rectangle"],
                "correct": 1  # B
            },
            {
                "question": "Which group of shapes can be combined to make a house?",
                "choices": ["A. One square and one triangle", "B. Two circles", "C. Three rectangles only", "D. One quarter circle only"],
                "correct": 0  # A
            },
            {
                "question": "A shape is moved one step to the right without turning or flipping it. What is this movement called?",
                "choices": ["A. Rotation", "B. Reflection", "C. Slide (Translation)", "D. Fold"],
                "correct": 2  # C
            },
            {
                "question": "Which figure is a composite figure?",
                "choices": ["A. A single square", "B. A single circle", "C. A shape made by joining a rectangle and a triangle", "D. A single triangle"],
                "correct": 2  # C
            }
        ]

        # ============================================================
        # LOAD PORTALS
        # ============================================================
        self.portals = []
        self.portal_frames_cache = self.load_portal_frames()
        self.load_static_portals()

        # Teleport cooldown
        self.teleport_cooldown = 0
        self.TELEPORT_COOLDOWN_TIME = 1.0

        # Goal portal tracking - which portal completes the level
        self.goal_portal_direction = self.portals[0].direction if self.portals else ('right' if self.is_quiz_map else 'up')

        # ============================================================
        # UI
        # ============================================================
        self.show_info = True
        self.font = pygame.font.SysFont("Comic Sans MS", 16)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 12)

        # Clock for delta time
        self.clock = pygame.time.Clock()
        self.frame_counter = 0

        # Completion flag
        self.completed = False

        print(f"✅ Quarter1 initialized with map: {self.map_name}")
        print(f"   Goal portal: {self.goal_portal_direction}")
        print(f"   Portals loaded: {len(self.portals)}")

    # ============================================================
    # CREATE DEFAULT MAP (fallback)
    # ============================================================
    def _create_default_map(self):
        """Create a default map if loading fails"""
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
    # INIT NPC POSITIONS
    # ============================================================
    def _init_npc_positions(self):
        """Initialize NPC positions from map data"""
        # Reset NPC flags
        self.npc_bromen_found = False
        self.npc_oldman_found = False
        self.npc_skeleton_found = False
        self.npc_knight_found = False

        # Set positions from map data
        for marker, positions in self.npc_positions_data.items():
            for x, y in positions:
                if marker == 'B':
                    self.npc_bromen_tile_x = x
                    self.npc_bromen_tile_y = y
                    self.npc_bromen_x = x * TILE_SIZE
                    self.npc_bromen_y = y * TILE_SIZE
                    self.npc_bromen_found = True
                    print(f"Bromen NPC at: ({x}, {y})")
                elif marker == 'O':
                    if not self.is_quiz_map:
                        self.npc_oldman_tile_x = x
                        self.npc_oldman_tile_y = y
                        self.npc_oldman_x = x * TILE_SIZE
                        self.npc_oldman_y = y * TILE_SIZE
                        self.npc_oldman_found = True
                        print(f"Oldman NPC at: ({x}, {y})")
                elif marker == 'S':
                    self.npc_skeleton_tile_x = x
                    self.npc_skeleton_tile_y = y
                    self.npc_skeleton_x = x * TILE_SIZE
                    self.npc_skeleton_y = y * TILE_SIZE
                    self.npc_skeleton_found = True
                    print(f"Skeleton NPC at: ({x}, {y})")
                elif marker == 'K':
                    self.npc_knight_tile_x = x
                    self.npc_knight_tile_y = y
                    self.npc_knight_x = x * TILE_SIZE
                    self.npc_knight_y = y * TILE_SIZE
                    self.npc_knight_found = True
                    print(f"Knight NPC at: ({x}, {y})")

    # ============================================================
    # LOAD TILE IMAGES
    # ============================================================
    def load_tile_images(self):
        def load_tile(filename):
            path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                return image
            except Exception:
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((100, 100, 100))
                pygame.draw.rect(placeholder, (255, 0, 0), placeholder.get_rect(), 2)
                return placeholder

        def load_large_tile(name, w_pixels, h_pixels):
            path = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "tiles", "quarter1tiles", name)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    return pygame.transform.scale(img, (w_pixels, h_pixels))
                except Exception as e:
                    print(f"Error loading large tile {name}: {e}")
            placeholder = pygame.Surface((w_pixels, h_pixels))
            placeholder.fill((150, 100, 100))
            return placeholder

        tiles = {}
        tiles["X"] = load_large_tile("obstacle1.png", 64, 96)
        tiles["Y"] = load_large_tile("obstacle2.png", 64, 96)
        tiles["Z"] = load_large_tile("obstacle3.png", 64, 96)

        tile_files = [
            ("#", "003.png"), ("G", "002.png"), ("1", "002.png"), ("2", "002.png"),
            ("3", "002.png"), ("4", "002.png"), ("5", "002.png"), ("6", "010.png"),
            ("7", "008.png"), ("8", "007.png"), ("+", "012.png"), ("-", "013.png"),
            ("/", "014.png"), ("*", "015.png"), ("T", "quarter1tiles/100.png"), ("W", "019.png"),
            ("!", "020.png"), ("@", "022.png"), (")", "021.png"), ("$", "026.png"),
            ("%", "025.png"), ("^", "027.png"), ("&", "023.png"), ("(", "024.png"),
            ("<", "028.png"), (">", "029.png"), (";", "030.png"), (":", "032.png"),
            ("P", "034.png"), ("C", "032.png"), ("S", "036.png"), ("R", "037.png"),
            ("E", "033.png"), ("|", "035.png"), ("D", "pyramid.png")
        ]

        for key, filename in tile_files:
            tiles[key] = load_tile(filename)

        # Load 16 autotile images for walls ('T')
        self.autotile_images = {}
        autotile_dir = os.path.join(self.OBJECTS_PATH, "quarter1tiles")
        for idx in range(16):
            tile_path = os.path.join(autotile_dir, f"{idx}.png")
            if os.path.exists(tile_path):
                try:
                    img = pygame.image.load(tile_path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.autotile_images[idx] = img
                except Exception as e:
                    print(f"Error loading autotile {idx}: {e}")

        return tiles

    def get_autotile_index(self, row, col):
        def is_wall(r, c):
            if r < 0 or r >= self.ROWS or c < 0 or c >= self.COLS:
                return True
            if r < len(self.render_map) and c < len(self.render_map[r]):
                return self.render_map[r][c] == 'T'
            return False

        n = 1 if is_wall(row - 1, col) else 0
        e = 1 if is_wall(row, col + 1) else 0
        s = 1 if is_wall(row + 1, col) else 0
        w = 1 if is_wall(row, col - 1) else 0

        val = n * 8 + e * 4 + s * 2 + w

        val_map = {
            0: 0,   # 0000 -> layout 0
            1: 1,   # 0001 -> layout 1
            2: 2,   # 0010 -> layout 2
            3: 3,   # 0011 -> layout 3
            4: 1,   # 0100 -> layout 1
            5: 1,   # 0101 -> layout 1
            6: 4,   # 0110 -> layout 4
            7: 6,   # 0111 -> layout 6
            8: 2,   # 1000 -> layout 2
            9: 5,   # 1001 -> layout 5
            10: 2,  # 1010 -> layout 2
            11: 13, # 1011 -> layout 13
            12: 14, # 1100 -> layout 14
            13: 7,  # 1101 -> layout 7
            14: 12, # 1110 -> layout 12
            15: 8   # 1111 -> layout 8
        }
        return val_map.get(val, 0)

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
    # LOAD ANIMATED NPC SPRITES (Bromen)
    # ============================================================
    def load_npc_sprites_animated(self, npc_path, npc_name):
        frames = []

        if not os.path.exists(npc_path):
            print(f"⚠️ NPC path does not exist: {npc_path}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((255, 200, 100))
            pygame.draw.circle(placeholder, (0, 0, 0), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
            pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4), 3)
            pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2 + 4, TILE_SIZE // 2 - 4), 3)
            frames.append(placeholder)
            return frames

        for i in range(11):
            filename = f"sprite_{npc_name}{i:02d}.png"
            path = os.path.join(npc_path, filename)
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    frames.append(img)
                else:
                    if frames:
                        frames.append(frames[0].copy())
                    else:
                        placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                        placeholder.fill((255, 200, 0))
                        frames.append(placeholder)
            except Exception as e:
                if frames:
                    frames.append(frames[0].copy())
                else:
                    placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    placeholder.fill((255, 200, 0))
                    frames.append(placeholder)

        print(f"✅ Loaded {len(frames)} frames for {npc_name}")
        return frames

    # ============================================================
    # LOAD STATIC NPC SPRITES (Oldman, Skeleton, Knight)
    # ============================================================
    def load_static_npc_sprites(self):
        # Load Shape NPC sprites if it's a quiz map
        self.shape_sprites = {}
        if self.is_quiz_map:
            shape_info = {
                1: ("CircleNPC", "sprite_circlenpc"),
                2: ("HeartNPC", "sprite_heartnpc"),
                3: ("SquareNPC", "sprite_squarenpc"),
                4: ("StarNPC", "sprite_starnpc"),
                5: ("DiamondNPC", "sprite_diamondnpc")
            }
            for num, (folder, prefix) in shape_info.items():
                frames = []
                for idx in range(8):
                    filename = f"{prefix}{idx:02d}.png"
                    path = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", folder, filename)
                    if os.path.exists(path):
                        try:
                            img = pygame.image.load(path).convert_alpha()
                            scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                            frames.append(scaled)
                        except Exception as e:
                            print(f"❌ Error loading shape frame {num} ({idx}): {e}")
                if len(frames) == 8:
                    self.shape_sprites[num] = frames
                    print(f"🏀 Loaded 8 animation frames for shape {num} ({folder})")
                else:
                    print(f"⚠️ Failed to load 8 frames for shape {num} ({folder})")

        # Load Ball instead of Oldman
        ball_frames = []
        try:
            for idx in range(16):
                filename = f"sprite_ball{idx:02d}.png"
                path = os.path.join(self.NPC_PATH_BALL, filename)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    ball_frames.append(scaled)
                    print(f"✅ Loaded Ball frame: {filename}")
                else:
                    print(f"⚠️ Ball frame not found at: {path}")

            if ball_frames:
                self.npc_oldman_sprite = ball_frames[0]
                self.npc_oldman_left_sprites = ball_frames
                self.npc_oldman_right_sprites = ball_frames
                self.npc_oldman_up_sprites = ball_frames
                self.npc_oldman_down_sprites = ball_frames
                print("🏀 Loaded Ball sprites to replace Old Man")
            else:
                raise FileNotFoundError("No ball frames found")

        except Exception as e:
            print(f"❌ Error loading Ball: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((200, 100, 100))
            self.npc_oldman_sprite = placeholder
            self.npc_oldman_left_sprites = [placeholder.copy()]
            self.npc_oldman_right_sprites = [placeholder.copy()]
            self.npc_oldman_up_sprites = [placeholder.copy()]
            self.npc_oldman_down_sprites = [placeholder.copy()]

        # Load Skeleton
        skeleton_path = os.path.join(self.NPC_PATH_SKELETON, "skeleton.png")
        try:
            if os.path.exists(skeleton_path):
                img = pygame.image.load(skeleton_path).convert_alpha()
                self.npc_skeleton_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"✅ Loaded Skeleton sprite")
            else:
                print(f"⚠️ Skeleton sprite not found at: {skeleton_path}")
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((255, 255, 255))
                pygame.draw.circle(placeholder, (0, 0, 0), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
                pygame.draw.circle(placeholder, (255, 200, 200), (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4), 3)
                pygame.draw.circle(placeholder, (255, 200, 200), (TILE_SIZE // 2 + 4, TILE_SIZE // 2 - 4), 3)
                font = pygame.font.SysFont(None, 10)
                text = font.render("SKEL", True, (0, 0, 0))
                placeholder.blit(text, (2, TILE_SIZE - 12))
                self.npc_skeleton_sprite = placeholder
        except Exception as e:
            print(f"❌ Error loading Skeleton: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((255, 255, 255))
            self.npc_skeleton_sprite = placeholder

        # Load Knight
        knight_path = os.path.join(self.NPC_PATH_KNIGHT, "knight.png")
        try:
            if os.path.exists(knight_path):
                img = pygame.image.load(knight_path).convert_alpha()
                self.npc_knight_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"✅ Loaded Knight sprite")
            else:
                print(f"⚠️ Knight sprite not found at: {knight_path}")
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((192, 192, 192))
                self.npc_knight_sprite = placeholder

            # Load Knight walking left sprites
            self.npc_knight_left_sprites = []
            for name in ["knight_left.png", "knight_left_1.png", "knight_left_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_left_sprites.append(scaled)
                    print(f"✅ Loaded Knight left frame: {name}")

            # Load Knight walking down sprites
            self.npc_knight_down_sprites = []
            for name in ["knight_down.png", "knight_down_1.png", "knight_down_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_down_sprites.append(scaled)
                    print(f"✅ Loaded Knight down frame: {name}")

            # Load Knight walking right sprites
            self.npc_knight_right_sprites = []
            for name in ["knight_right.png", "knight_right_1.png", "knight_right_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_right_sprites.append(scaled)
                    print(f"✅ Loaded Knight right frame: {name}")

            # Load Knight walking up sprites
            self.npc_knight_up_sprites = []
            for name in ["knight_up.png", "knight_up_1.png", "knight_up_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_up_sprites.append(scaled)
                    print(f"✅ Loaded Knight up frame: {name}")
        except Exception as e:
            print(f"❌ Error loading Knight: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((192, 192, 192))
            self.npc_knight_sprite = placeholder

    # ============================================================
    # PORTAL SPRITE ANIMATION CLASS
    # ============================================================
    class PortalSpriteAnimation:
        def __init__(self, frames, x, y, direction, width_tiles, height_tiles):
            self.frames = frames
            self.current_frame = 0
            self.animation_timer = 0
            self.frame_delay = 3
            self.x = x
            self.y = y
            self.direction = direction
            self.width_tiles = width_tiles
            self.height_tiles = height_tiles
            self.width = TILE_SIZE * width_tiles
            self.height = TILE_SIZE * height_tiles

        def update(self):
            if self.frames:
                self.animation_timer += 1
                if self.animation_timer >= self.frame_delay:
                    self.animation_timer = 0
                    self.current_frame = (self.current_frame + 1) % len(self.frames)

        def get_current_image(self):
            if self.frames and self.current_frame < len(self.frames):
                return self.frames[self.current_frame]
            return None

        def draw(self, screen, camera_x, camera_y, zoom, screen_width, screen_height):
            screen_x = (self.x - camera_x) * zoom
            screen_y = (self.y - camera_y) * zoom

            if (-self.width * zoom <= screen_x <= screen_width + self.width * zoom and
                    -self.height * zoom <= screen_y <= screen_height + self.height * zoom):
                portal_img = self.get_current_image()
                if portal_img:
                    scaled_width = int(self.width * zoom)
                    scaled_height = int(self.height * zoom)
                    scaled_img = pygame.transform.scale(portal_img, (scaled_width, scaled_height))
                    screen.blit(scaled_img, (screen_x, screen_y))

    # ============================================================
    # PORTAL CLASS
    # ============================================================
    class Portal:
        def __init__(self, x, y, direction, is_static=False):
            self.x = x
            self.y = y
            self.direction = direction
            self.is_static = is_static
            self.width_tiles, self.height_tiles = PORTAL_SIZES[direction]
            self.animation = None

        def get_world_x(self):
            return self.x * TILE_SIZE

        def get_world_y(self):
            return self.y * TILE_SIZE

        def get_width_pixels(self):
            return self.width_tiles * TILE_SIZE

        def get_height_pixels(self):
            return self.height_tiles * TILE_SIZE

        def get_center_x(self):
            return self.x * TILE_SIZE + (self.width_tiles * TILE_SIZE) // 2

        def get_center_y(self):
            return self.y * TILE_SIZE + (self.height_tiles * TILE_SIZE) // 2

        def set_animation(self, frames):
            self.animation = Quarter1.PortalSpriteAnimation(
                frames,
                self.get_world_x(),
                self.get_world_y(),
                self.direction,
                self.width_tiles,
                self.height_tiles
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

                if self.direction == 'right':
                    color = (0, 255, 0)
                elif self.direction == 'left':
                    color = (255, 0, 0)
                elif self.direction == 'up':
                    color = (0, 0, 255)
                else:
                    color = (255, 255, 0)

                pygame.draw.rect(screen, color, (screen_x, screen_y, scaled_width, scaled_height))
                pygame.draw.rect(screen, (255, 255, 255), (screen_x, screen_y, scaled_width, scaled_height), 3)

        def contains_position(self, world_x, world_y):
            portal_left = self.get_world_x()
            portal_right = portal_left + self.get_width_pixels()
            portal_top = self.get_world_y()
            portal_bottom = portal_top + self.get_height_pixels()
            return (portal_left <= world_x < portal_right and
                    portal_top <= world_y < portal_bottom)

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
                        if direction == 'right':
                            surf.fill((0, 255, 0))
                        elif direction == 'left':
                            surf.fill((255, 0, 0))
                        elif direction == 'up':
                            surf.fill((0, 0, 255))
                        elif direction == 'down':
                            surf.fill((255, 255, 0))
                        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 3)
                        frames.append(surf)
                except Exception:
                    surf = pygame.Surface((TILE_SIZE * width_tiles, TILE_SIZE * height_tiles))
                    surf.fill((128, 128, 128))
                    frames.append(surf)
            return frames if frames else None

        return {
            'right': load_portal_frames('right', PORTAL_SIZES['right'][0], PORTAL_SIZES['right'][1]),
            'left': load_portal_frames('left', PORTAL_SIZES['left'][0], PORTAL_SIZES['left'][1]),
            'up': load_portal_frames('up', PORTAL_SIZES['up'][0], PORTAL_SIZES['up'][1]),
            'down': load_portal_frames('down', PORTAL_SIZES['down'][0], PORTAL_SIZES['down'][1])
        }

    # ============================================================
    # LOAD STATIC PORTALS
    # ============================================================
    def load_static_portals(self):
        for y, row in enumerate(self.render_map):
            row_list = list(row)
            modified = False
            for x, c in enumerate(row):
                if c == 'r':
                    portal = self.Portal(x, y, 'right', is_static=True)
                    portal.set_animation(self.portal_frames_cache['right'])
                    if self.is_quiz_map:
                        self.locked_portals.append(portal)
                    else:
                        self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    if self.is_quiz_map:
                        self.locked_portals.append(portal)
                    else:
                        self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    if self.is_quiz_map:
                        self.locked_portals.append(portal)
                    else:
                        self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    if self.is_quiz_map:
                        self.locked_portals.append(portal)
                    else:
                        self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
            if modified:
                self.render_map[y] = ''.join(row_list)

    def spawn_portals(self):
        for portal in self.locked_portals:
            self.portals.append(portal)
        self.locked_portals = []
        print(f"🏀 Spawned and unlocked portals: {len(self.portals)}")

    # ============================================================
    # COLLISION
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

            # Check XYZ obstacles in the immediate neighborhood of the corner (col, row)
            # An XYZ obstacle at (c, r) occupies columns c, c+1 and its vertical collision line is at c*TILE_SIZE + 32.
            # So we check rows r near the player corner row, and columns c near the player corner col.
            for r in range(row - 1, row + 3):
                for c in range(col - 1, col + 2):
                    if 0 <= r < len(self.game_map) and 0 <= c < len(self.game_map[r]):
                        if self.game_map[r][c] in ['X', 'Y', 'Z']:
                            # Obstacle base is at (c, r)
                            line_x = c * TILE_SIZE + 32
                            y_start = (r - 2) * TILE_SIZE
                            y_end = (r + 1) * TILE_SIZE
                            
                            # Player bounding box corners
                            p_left = nx + padding
                            p_right = nx + TILE_SIZE - padding
                            p_top = ny + padding
                            p_bottom = ny + TILE_SIZE - padding
                            
                            # Check if player overlaps the vertical line horizontally and vertically
                            if p_left <= line_x <= p_right:
                                if p_bottom > y_start and p_top < y_end:
                                    return False

            npc_positions = []
            for marker, positions in self.npc_positions_data.items():
                npc_positions.extend(positions)

            player_col = int(self.player_x // TILE_SIZE)
            player_row = int(self.player_y // TILE_SIZE)

            for npc_col, npc_row in npc_positions:
                if col == npc_col and row == npc_row:
                    if player_col == npc_col and player_row == npc_row:
                        continue
                    return False
        return True

    # ============================================================
    # BFS PATHFINDER
    # ============================================================
    def find_path(self, start, end):
        """BFS pathfinder from start (col, row) to end (col, row) on the grid"""
        import collections
        if start == end:
            return [start]
        queue = collections.deque([[start]])
        seen = {start}
        
        # Directions: Right, Left, Down, Up
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        
        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == end:
                return path
                
            curr_x, curr_y = curr
            for dx, dy in directions:
                nxt = (curr_x + dx, curr_y + dy)
                nx, ny = nxt
                if 0 <= ny < self.ROWS and 0 <= nx < self.COLS:
                    if ny < len(self.game_map) and nx < len(self.game_map[ny]):
                        tile = self.game_map[ny][nx]
                        # Walkable tiles are walkable. We ignore other temporary collision overlays for oldman
                        if tile in self.WALKABLE_TILES and nxt not in seen:
                            seen.add(nxt)
                            queue.append(path + [nxt])
        return []

    # ============================================================
    # RETURN TO STAGE SELECT
    # ============================================================
    def return_to_stage_select(self):
        """Return to the stage select screen"""
        if self.main_menu:
            self.main_menu.current_screen = "stage_select"
            self.main_menu.quarter1 = None
            # Recreate the stage select to reset position
            from .stageselect import StageSelect
            self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
            print("🏠 Returning to stage select")
            self.completed = True
        return "back"

    # ============================================================
    # CHECK PORTAL TELEPORT
    # ============================================================
    def check_portal_teleport_on_hold(self):
        current_portal = None
        for portal in self.portals:
            if portal.contains_position(self.player_x, self.player_y):
                current_portal = portal
                break

        if current_portal and self.fist_closed and self.teleport_cooldown <= 0:
            # Check if this is the goal portal
            if current_portal.direction == self.goal_portal_direction:
                if self.is_quiz_map and self.quiz_state < 6:
                    return False
                print(f"🎯 Goal reached! Returning to stage select...")
                self.return_to_stage_select()
                return True

            # Regular portal teleport (to another portal on same map)
            other_portals = [p for p in self.portals if p != current_portal]
            if other_portals:
                target_portal = other_portals[0]
                self.player_x = target_portal.get_center_x() - TILE_SIZE // 2
                self.player_y = target_portal.get_center_y() - TILE_SIZE // 2
                self.teleport_cooldown = self.TELEPORT_COOLDOWN_TIME
                return True
        return False

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
        self.hand_detected = current_gesture != "NO HAND"
        self.fist_closed = fist_start_time > 0

    # ============================================================
    # TRIGGER CLICK
    # ============================================================
    # ============================================================
    # TRIGGER CLICK
    # ============================================================
    def trigger_click(self, pos):
        if not self.is_quiz_map:
            return
            
        import random
        
        # State 1: Dialog with choices
        if self.quiz_state == 1:
            box_w, box_h = 580, 370
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            
            button_w, button_h = 500, 42
            button_x = box_x + (box_w - button_w) // 2
            button_y_start = box_y + 125
            spacing = 52
            
            q_data = self.quiz_questions[self.current_question_index]
            
            for i in range(len(q_data["choices"])):
                b_y = button_y_start + i * spacing
                btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)
                
                if btn_rect.collidepoint(pos):
                    if i == q_data["correct"]:
                        self.current_correct_phrase = random.choice(self.correct_phrases)
                        self.quiz_state = 3
                        print(f"✅ Correct answer selected: {q_data['choices'][i]}")
                    else:
                        self.quiz_state = 2
                        print(f"❌ Incorrect answer selected: {q_data['choices'][i]}")
                    break
                    
        # State 2: Wrong answer retry screen click
        elif self.quiz_state == 2:
            box_w, box_h = 500, 240
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 140, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
            
        # State 3: Correct answer transition screen click
        elif self.quiz_state == 3:
            box_w, box_h = 500, 240
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 140, 200, 42)
            if btn_rect.collidepoint(pos):
                if self.is_quiz_map:
                    self.shape_npcs[self.active_shape_id]['answered'] = True
                    answered_count = sum(1 for s in self.shape_npcs.values() if s['answered'])
                    if answered_count == 5:
                        self.spawn_portals()
                        self.quiz_state = 5
                    else:
                        self.quiz_state = 0
                else:
                    self.current_question_index += 1
                    if self.current_question_index < 5:
                        self.quiz_state = 0
                    else:
                        self.quiz_state = 5
                
        # State 5: Final speech click
        elif self.quiz_state == 5:
            box_w, box_h = 550, 300
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 210, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 6
                self.npc_oldman_found = False
                print("🧙‍♂️ Old Man disappeared from Quarter 1")

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1
        # Update cooldowns
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt

        # Update block timer
        if self.player_block_timer > 0:
            self.player_block_timer = max(0.0, self.player_block_timer - dt)

        # Update Area Title animation elapsed time
        if self.title_active:
            self.title_elapsed += dt
            if self.title_elapsed >= self.title_duration:
                self.title_active = False

        if self.npc_bromen_sprites and self.npc_bromen_found:
            self.npc_bromen_anim_timer += 1
            if self.npc_bromen_anim_timer >= 5:
                self.npc_bromen_anim_timer = 0
                self.npc_bromen_anim_frame = (self.npc_bromen_anim_frame + 1) % len(self.npc_bromen_sprites)

        # Update Shape NPC animation frame
        if self.is_quiz_map:
            self.shape_npc_anim_timer += 1
            if self.shape_npc_anim_timer >= 5:
                self.shape_npc_anim_timer = 0
                self.shape_npc_anim_frame = (self.shape_npc_anim_frame + 1) % 8

        # Proximity interaction check for Shape NPCs
        if self.quiz_state == 0 and self.is_quiz_map:
            import math
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            
            for num, npc in self.shape_npcs.items():
                if not npc["answered"]:
                    npc_center_x = npc["x"] + TILE_SIZE // 2
                    npc_center_y = npc["y"] + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - npc_center_x, player_center_y - npc_center_y)
                    if dist < TILE_SIZE * 1.5:
                        p_dx = npc["x"] - self.player_x
                        p_dy = npc["y"] - self.player_y
                        if abs(p_dx) > abs(p_dy):
                            self.player_dir = "right" if p_dx > 0 else "left"
                        else:
                            self.player_dir = "down" if p_dy > 0 else "up"
                        
                        self.active_shape_id = num
                        self.current_question_index = num - 1
                        self.quiz_state = 1
                        self.selected_choice_index = -1
                        print(f"🏀 Interacted with Shape NPC {num}: {npc['name']} (Q{num-1})")
                        break

        self.update_player_movement()
        self.check_portal_teleport_on_hold()

        for portal in self.portals:
            portal.update_animation()

        self.update_camera()

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        if self.quiz_state in [1, 2, 3, 5] or self.player_block_timer > 0:
            self.anim_frame = 0
            return

        vx, vy = 0, 0

        if self.hand_detected:
            center_x, center_y = self.width // 2, self.height // 2
            cursor_x, cursor_y = self.cursor_pos
            dx = cursor_x - center_x
            dy = cursor_y - center_y

            if abs(dx) > 60:
                vx = SPEED if dx > 0 else -SPEED
                if dx > 0:
                    self.player_dir = "right"
                elif dx < 0:
                    self.player_dir = "left"

            if abs(dy) > 60:
                vy = SPEED if dy > 0 else -SPEED
                if dy > 0:
                    self.player_dir = "down"
                elif dy < 0:
                    self.player_dir = "up"

        new_x = self.player_x + vx
        new_y = self.player_y + vy

        if self.can_move(new_x, self.player_y):
            self.player_x = new_x
        if self.can_move(self.player_x, new_y):
            self.player_y = new_y

        if vx != 0 or vy != 0:
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_frame = 0

    # ============================================================
    # DRAW TILE
    # ============================================================
    def draw_tile(self, c, world_x, world_y):
        screen_x = (world_x - self.camera_x) * ZOOM
        screen_y = (world_y - self.camera_y) * ZOOM

        margin = TILE_SIZE * ZOOM * 2
        if (-margin <= screen_x <= self.width + margin and
                -margin <= screen_y <= self.height + margin):
            if False:  # Disabled autotiling to use solid 100.png directly
                col = int(world_x / TILE_SIZE)
                row = int(world_y / TILE_SIZE)
                idx = self.get_autotile_index(row, col)
                image = self.autotile_images.get(idx, self.tile_images.get('T', self.fallback_tile))
            else:
                image = self.tile_images.get(c, self.fallback_tile)
                if c in ['X', 'Y', 'Z']:
                    w = int(64 * ZOOM)
                    h = int(96 * ZOOM)
                    scaled_image = pygame.transform.scale(image, (w, h))
                    screen_y_shifted = screen_y - int(64 * ZOOM)
                    self.screen.blit(scaled_image, (screen_x, screen_y_shifted))
                else:
                    scaled_size = int(TILE_SIZE * ZOOM)
                    scaled_image = pygame.transform.scale(image, (scaled_size, scaled_size))
                    self.screen.blit(scaled_image, (screen_x, screen_y))

    # ============================================================
    # DRAW NPC
    # ============================================================
    def draw_npc_animated(self, x, y, sprites, anim_frame):
        if not sprites:
            return

        screen_x = (x - self.camera_x) * ZOOM
        screen_y = (y - self.camera_y) * ZOOM

        if (-TILE_SIZE * ZOOM <= screen_x <= self.width + TILE_SIZE * ZOOM and
                -TILE_SIZE * ZOOM <= screen_y <= self.height + TILE_SIZE * ZOOM):
            frame_index = min(anim_frame, len(sprites) - 1)
            sprite = sprites[frame_index]
            scaled_size = int(TILE_SIZE * ZOOM)
            scaled_sprite = pygame.transform.scale(sprite, (scaled_size, scaled_size))
            self.screen.blit(scaled_sprite, (screen_x, screen_y))

    def draw_npc_static(self, x, y, sprite):
        if sprite is None:
            return

        screen_x = (x - self.camera_x) * ZOOM
        screen_y = (y - self.camera_y) * ZOOM

        if (-TILE_SIZE * ZOOM <= screen_x <= self.width + TILE_SIZE * ZOOM and
                -TILE_SIZE * ZOOM <= screen_y <= self.height + TILE_SIZE * ZOOM):
            scaled_size = int(TILE_SIZE * ZOOM)
            scaled_sprite = pygame.transform.scale(sprite, (scaled_size, scaled_size))
            self.screen.blit(scaled_sprite, (screen_x, screen_y))

    def draw_answered_checkmark(self, x, y):
        screen_x = (x - self.camera_x) * ZOOM
        screen_y = (y - self.camera_y) * ZOOM
        if (-TILE_SIZE * ZOOM <= screen_x <= self.width + TILE_SIZE * ZOOM and
                -TILE_SIZE * ZOOM <= screen_y <= self.height + TILE_SIZE * ZOOM):
            center_x = screen_x + (TILE_SIZE * ZOOM) // 2
            tip_y = screen_y - int(10 * ZOOM)
            p1 = (center_x - int(6 * ZOOM), tip_y - int(2 * ZOOM))
            p2 = (center_x - int(1 * ZOOM), tip_y + int(4 * ZOOM))
            p3 = (center_x + int(6 * ZOOM), tip_y - int(5 * ZOOM))
            pygame.draw.lines(self.screen, (34, 197, 94), False, [p1, p2, p3], int(3 * ZOOM))

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
    # DRAW
    # ============================================================
    def draw(self):
        self.screen.fill((0, 0, 0))

        start_col = max(0, int(self.camera_x / TILE_SIZE) - 2)
        end_col = min(self.COLS, int((self.camera_x + self.width / ZOOM) / TILE_SIZE) + 3)
        start_row = max(0, int(self.camera_y / TILE_SIZE) - 2)
        end_row = min(self.ROWS, int((self.camera_y + self.height / ZOOM) / TILE_SIZE) + 3)

        # Pass 1: Base Grass/Ground Layer (Grass first everywhere, then paths/non-obstacles)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    # Always draw grass first as base
                    self.draw_tile('G', col * TILE_SIZE, row * TILE_SIZE)
                    
                    # Draw path / floor / interactive tiles on top of grass (skip T and XYZ obstacles)
                    tile_char = self.render_map[row][col]
                    if tile_char not in ['T', 'X', 'Y', 'Z', 'G']:
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        if not self.is_quiz_map or self.quiz_state == 6:
            for portal in self.portals:
                portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height)

        if self.npc_bromen_found:
            self.draw_npc_animated(self.npc_bromen_x, self.npc_bromen_y,
                                   self.npc_bromen_sprites, self.npc_bromen_anim_frame)

        # Draw Shape NPCs
        if self.is_quiz_map:
            for num, npc in self.shape_npcs.items():
                sprite_data = self.shape_sprites.get(num)
                if sprite_data:
                    if isinstance(sprite_data, list) and len(sprite_data) > 0:
                        current_frame = sprite_data[self.shape_npc_anim_frame]
                        self.draw_npc_static(npc["x"], npc["y"], current_frame)
                    else:
                        self.draw_npc_static(npc["x"], npc["y"], sprite_data)
                
                # Draw checkmark above NPC if answered
                if npc["answered"]:
                    self.draw_answered_checkmark(npc["x"], npc["y"])

        if self.npc_skeleton_found:
            self.draw_npc_static(self.npc_skeleton_x, self.npc_skeleton_y,
                                 self.npc_skeleton_sprite)

        if self.npc_knight_found:
            sprites = None
            if self.npc_knight_dir == "left":
                sprites = self.npc_knight_left_sprites
            elif self.npc_knight_dir == "right":
                sprites = self.npc_knight_right_sprites
            elif self.npc_knight_dir == "up":
                sprites = self.npc_knight_up_sprites
            else:
                sprites = self.npc_knight_down_sprites

            if sprites:
                self.draw_npc_static(self.npc_knight_x, self.npc_knight_y,
                                     sprites[0])
            elif self.npc_knight_sprite:
                self.draw_npc_static(self.npc_knight_x, self.npc_knight_y,
                                     self.npc_knight_sprite)

        self.draw_player()

        # Pass 3: T Obstacles
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char == 'T':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Pass 4: XYZ Obstacles
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char in ['X', 'Y', 'Z']:
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)
        self.draw_ui()

        # Draw floating exclamation mark if active and player is in proximity
        if self.quiz_state == 0 and self.is_quiz_map and self.npc_oldman_found:
            import math
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            oldman_center_x = self.npc_oldman_x + TILE_SIZE // 2
            oldman_center_y = self.npc_oldman_y + TILE_SIZE // 2
            dist = math.hypot(player_center_x - oldman_center_x, player_center_y - oldman_center_y)
            if dist < TILE_SIZE * 3.0:
                screen_x = (self.npc_oldman_x - self.camera_x) * ZOOM
                screen_y = (self.npc_oldman_y - self.camera_y) * ZOOM
                excl_font = pygame.font.SysFont("Comic Sans MS", int(18 * ZOOM), bold=True)
                excl_surf = excl_font.render("!", True, (255, 0, 0))  # Red indicator
                bounce = math.sin(self.frame_counter * 0.1) * 4 * ZOOM
                excl_x = screen_x + (TILE_SIZE * ZOOM) // 2 - excl_surf.get_width() // 2
                excl_y = screen_y - excl_surf.get_height() - 4 * ZOOM + bounce
                shadow_surf = excl_font.render("!", True, (0, 0, 0))
                self.screen.blit(shadow_surf, (excl_x + 1, excl_y + 1))
                self.screen.blit(excl_surf, (excl_x, excl_y))

        # Centered Dialog overlays for Shape Quiz
        if self.is_quiz_map:
            if self.quiz_state == 1:
                self.draw_quiz_dialog()
            elif self.quiz_state == 2:
                self.draw_wrong_dialog()
            elif self.quiz_state == 3:
                self.draw_correct_dialog()
            elif self.quiz_state == 5:
                self.draw_final_dialog()

        # Draw Area Title Animation
        if self.title_active:
            import math
            timer = self.title_elapsed
            
            # Alpha fading
            alpha = 255
            FADE_START = 4.0
            FADE_DURATION = 1.0
            if timer >= FADE_START:
                fade = (timer - FADE_START) / FADE_DURATION
                fade = max(0, min(fade, 1))
                alpha = int(255 * (1 - fade))
                
            # Slide animation
            BASE_Y = self.height // 2 - self.pixel_font_size // 2
            SLIDE_TIME = 0.35
            if timer < SLIDE_TIME:
                t = timer / SLIDE_TIME
                ease = 1 - (1 - t) ** 3
                y = BASE_Y - (1 - ease) * 40
            else:
                y = BASE_Y
                
            # Draw letters centered
            x = self.width // 2 - self.title_total_width // 2
            
            for i, data in enumerate(self.title_letters):
                phase = timer * 8 - i * 0.55
                offset = 0
                
                # Single traveling wave
                if -math.pi <= phase <= math.pi:
                    offset = math.sin(phase) * 12
                    
                glow = data["glow"].copy()
                outline = data["outline"].copy()
                main = data["main"].copy()
                
                glow.set_alpha(alpha // 5)
                outline.set_alpha(alpha)
                main.set_alpha(alpha)
                
                # Glow
                for gx in (-5, 0, 5):
                    for gy in (-5, 0, 5):
                        self.screen.blit(glow, (x + gx, y + gy + offset))
                        
                # Outline
                for ox in (-2, -1, 1, 2):
                    for oy in (-2, -1, 1, 2):
                        self.screen.blit(outline, (x + ox, y + oy + offset))
                        
                # Main text
                self.screen.blit(main, (x, y + offset))
                
                x += data["width"] + self.title_spacing

    def draw_quiz_dialog(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 580, 370
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_name = "Old Man"
        if self.is_quiz_map and self.active_shape_id is not None:
            npc_data = self.shape_npcs.get(self.active_shape_id)
            if npc_data:
                speaker_name = f"{npc_data['name'].capitalize()} NPC"
        
        speaker_surf = speaker_font.render(speaker_name, True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 25 + speaker_surf.get_width(), box_y + 48), 2)

        q_data = self.quiz_questions[self.current_question_index]
        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        wrapped_q = self.wrap_text(q_data["question"], q_font, box_w - 50)
        
        y_text = box_y + 60
        for line in wrapped_q:
            txt_surf = q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 22

        button_w, button_h = 500, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 125
        spacing = 52
        
        for i, choice in enumerate(q_data["choices"]):
            b_y = button_y_start + i * spacing
            btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)
            is_hovered = btn_rect.collidepoint(self.cursor_pos)
            
            if is_hovered:
                bg_color = (255, 215, 0)
                text_color = (0, 0, 0)
            else:
                bg_color = (30, 41, 59)
                text_color = (255, 255, 255)
            
            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)
            
            c_surf = q_font.render(choice, True, text_color)
            c_rect = c_surf.get_rect(center=btn_rect.center)
            self.screen.blit(c_surf, c_rect)

    def draw_wrong_dialog(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 500, 240
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_name = "Old Man"
        if self.is_quiz_map and self.active_shape_id is not None:
            npc_data = self.shape_npcs.get(self.active_shape_id)
            if npc_data:
                speaker_name = f"{npc_data['name'].capitalize()} NPC"
        
        speaker_surf = speaker_font.render(speaker_name, True, (220, 38, 38))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        msg_surf = q_font.render("Hmm, that is not correct. Try again, young adventurer!", True, (255, 255, 255))
        self.screen.blit(msg_surf, (box_x + 25, box_y + 70))

        button_w, button_h = 200, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 140
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (220, 38, 38)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render("Try Again", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_correct_dialog(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 500, 240
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (22, 163, 74), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_name = "Old Man"
        if self.is_quiz_map and self.active_shape_id is not None:
            npc_data = self.shape_npcs.get(self.active_shape_id)
            if npc_data:
                speaker_name = f"{npc_data['name'].capitalize()} NPC"
        
        speaker_surf = speaker_font.render(speaker_name, True, (22, 163, 74))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        msg_surf = q_font.render(self.current_correct_phrase, True, (255, 255, 255))
        self.screen.blit(msg_surf, (box_x + 25, box_y + 70))

        button_w, button_h = 200, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 140
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (22, 163, 74)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render("Continue", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_final_dialog(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 550, 300
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_surf = speaker_font.render("Old Man", True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 120, box_y + 48), 2)

        q_font = pygame.font.SysFont("Comic Sans MS", 15)
        speech_lines = [
            "Outstanding, young adventurer! You know your shapes very well.",
            "The Geometry Forest is peaceful once again because of your wisdom.",
            "Keep exploring and learning. There are many more adventures",
            "waiting for a brave student like you!"
        ]
        
        y_text = box_y + 65
        for line in speech_lines:
            txt_surf = q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 24

        button_w, button_h = 200, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 210
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        if is_hovered:
            bg_color = (255, 215, 0)
            text_color = (0, 0, 0)
        else:
            bg_color = (30, 41, 59)
            text_color = (255, 255, 255)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render("Finish", True, text_color)
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

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
    # DRAW UI
    # ============================================================
    def draw_ui(self):
        if self.hand_detected:
            if self.fist_start_time > 0:
                color = (255, 200, 0)
            else:
                color = (255, 255, 255)

            pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
            pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

        # Draw Objectives HUD Box at the bottom center of the screen
        if self.is_quiz_map:
            box_w, box_h = 340, 80
            box_x = (self.width - box_w) // 2
            box_y = self.height - box_h - 20
            
            # Translucent slate blue background (alpha = 190)
            bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            bg_surf.fill((15, 23, 42, 190))
            self.screen.blit(bg_surf, (box_x, box_y))
            
            # Border: Gold when locked, Green when complete
            border_color = (218, 165, 32) if self.quiz_state < 6 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_w, box_h), 2, border_radius=8)
            
            # Header title in Gold
            title_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
            title_surf = title_font.render("CURRENT OBJECTIVES", True, (255, 215, 0))
            self.screen.blit(title_surf, (box_x + 15, box_y + 8))
            
            # Details font
            item_font = pygame.font.SysFont("Comic Sans MS", 12)
            
            # Quiz completion progress item
            if self.is_quiz_map:
                q_count = sum(1 for s in self.shape_npcs.values() if s['answered'])
            else:
                q_count = min(self.current_question_index, 5)
            obj1 = f"• Quiz Progress: {q_count}/5 questions answered"
            obj1_color = (255, 255, 255) if q_count < 5 else (34, 197, 94)
            obj1_surf = item_font.render(obj1, True, obj1_color)
            self.screen.blit(obj1_surf, (box_x + 15, box_y + 28))
            
            # Goal portal state item
            if self.quiz_state < 6:
                obj2 = "• Portal Status: LOCKED"
                obj2_color = (244, 63, 94)  # Rose
            else:
                obj2 = "• Portal Status: OPEN (Enter the portal to exit!)"
                obj2_color = (34, 197, 94)  # Green
            obj2_surf = item_font.render(obj2, True, obj2_color)
            self.screen.blit(obj2_surf, (box_x + 15, box_y + 48))

        if self.show_info:
            npc_status = []
            if self.npc_bromen_found:
                npc_status.append("Bromen")
            if self.npc_oldman_found:
                npc_status.append("Oldman")
            if self.npc_skeleton_found:
                npc_status.append("Skeleton")
            if self.npc_knight_found:
                npc_status.append("Knight")

            npc_text = ", ".join(npc_status) if npc_status else "None"

            info_lines = [
                f"Map: {self.map_name}",
                f"Goal: Reach the {self.goal_portal_direction} portal → Return to town",
                f"Position: ({self.player_x // TILE_SIZE}, {self.player_y // TILE_SIZE})",
                f"Portals: {len(self.portals)}",
                f"NPCs: {npc_text}",
                f"Hand: {'YES' if self.hand_detected else 'NO'}",
                f"Gesture: {self.current_gesture}",
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
    # HANDLE EVENT
    # ============================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.main_menu:
                    self.main_menu.current_screen = "menu"
                    self.main_menu.quarter1 = None
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.quiz_state in [1, 2, 3, 5]:
                    self.trigger_click(self.cursor_pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.trigger_click(event.pos)
        return None

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()