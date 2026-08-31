# screens/quarter4.py - Quarter 4 Map Handler (map10.txt)

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

# Camera zoom settings - PERMANENT ZOOM
ZOOM = 1.50  # Fixed zoom level

# Portal settings
PORTAL_SIZES = {
    'right': (3, 3),  # 3 tiles wide, 3 tiles tall (square)
    'left': (2, 3),   # 2 tile wide, 3 tiles tall (vertical strip)
    'up': (3, 3),     # 3 tiles wide, 3 tiles tall (square)
    'down': (3, 2)    # 3 tiles wide, 2 tile tall (horizontal strip)
}


class Quarter4:
    def __init__(self, screen, main_menu, map_name):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()
        self.map_name = map_name  # 'map10.txt'

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

        self.NPC_PATH_CIRCLE = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "CircleNPC"
        )

        self.NPC_PATH_STAR = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "StarNPC"
        )

        self.NPC_PATH_NUM3 = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "Number3NPC"
        )

        self.NPC_PATH_NUM4 = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "NPC",
            "Number4NPC"
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
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "P"}

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
        self.station_npcs = {}
        self.load_station_npcs()
        self.npc_bromen_sprites = self.load_npc_sprites_animated(self.NPC_PATH_BROMEN, "bromen")
        self.npc_bromen_anim_frame = 0
        self.npc_bromen_anim_timer = 0
        self.npc_bromen_x = 0
        self.npc_bromen_y = 0
        self.npc_bromen_tile_x = 0
        self.npc_bromen_tile_y = 0
        self.npc_bromen_found = False
        self.bromen_dialogue_state = 0  # 0: idle, 1: not enough, 2: ready, 3: completed
        self.emblem_puzzle_active = False
        self.emblem_puzzle_solved = False
        self.load_emblem_puzzle_assets()
        self.load_puzzle_sounds()

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

        # Snap camera immediately to player on load
        target_cam_x = self.player_x + TILE_SIZE // 2 - (self.width // 2) / ZOOM
        target_cam_y = self.player_y + TILE_SIZE // 2 - (self.height // 2) / ZOOM
        max_cam_x = max(0, self.MAP_WIDTH - self.width / ZOOM)
        max_cam_y = max(0, self.MAP_HEIGHT - self.height / ZOOM)
        self.camera_x = max(0, min(target_cam_x, max_cam_x))
        self.camera_y = max(0, min(target_cam_y, max_cam_y))

        for y, row in enumerate(self.render_map):
            if "P" in row:
                self.render_map[y] = row.replace("P", "G")

        # Initialize NPC positions from map data
        self._init_npc_positions()

        # ============================================================
        # LOAD PORTALS
        # ============================================================
        self.portals = []
        self.portal_frames_cache = self.load_portal_frames()
        self.load_static_portals()

        # Teleport cooldown
        self.teleport_cooldown = 0
        self.TELEPORT_COOLDOWN_TIME = 1.0

        # Goal portal tracking
        self.goal_portal_direction = self.portals[0].direction if self.portals else 'right'

        # ============================================================
        # UI & QUIZ STATE SYSTEM
        # ============================================================
        self.show_info = True
        self.font = pygame.font.SysFont("Comic Sans MS", 16)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 12)

        # Clock for delta time
        self.clock = pygame.time.Clock()
        self.frame_counter = 0

        # Completion flag
        self.completed = False
        self.is_quiz_map = True
        self.answered_stations = set()

        self.quiz_state = 0  # 0: waiting proximity, 1: dialog Q, 2: wrong try again, 3: correct phrase transition, 4: out of tries reveal, 5: final speech, 6: quiz complete
        self.quiz_station_index = 1  # current active station (1-6)
        self.current_question_index = 0
        self.first_attempt_correct = {1: True, 2: True, 3: True, 4: True, 5: True, 6: True}
        self.station_attempts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        self.selected_choice_index = -1  # choice highlighted

        # Station Standby Directions based on Map Name and User Requests
        self.station_directions = {
            1: "left",
            2: "left",
            3: "left",
            4: "right",
            5: "right",
            6: "right"
        }

        # Scan map for quiz stations 1, 2, 3, 4, 5, 6
        self.quiz_stations = {}
        for y, row in enumerate(self.game_map):
            for x, c in enumerate(row):
                if c in ['1', '2', '3', '4', '5', '6']:
                    num = int(c)
                    self.quiz_stations[num] = (x, y)
                    print(f"📍 Quiz Station {num} found at: ({x}, {y})")

        # Correct answer random responses
        self.current_correct_phrase = ""
        self.correct_phrases = [
            "Splendid! Your mathematical intellect is top-tier!",
            "Excellent! That's correct, onto the next challenge!",
            "Superb! Your logic is unbreakable, adventurer!"
        ]

        self.player_block_timer = 0.0

        # Curated review questions (2 shapes Q1, 2 geometry Q2, 2 arithmetic/fractions Q3)
        self.quiz_questions = [
            {
                "question": "Which shape has 5 sharp points and is colored yellow?",
                "choices": ["A. Circle", "B. Heart", "C. Square", "D. Star"],
                "correct": 3  # D
            },
            {
                "question": "I have 4 equal straight sides and 4 square corners. What shape am I?",
                "choices": ["A. Diamond", "B. Square", "C. Triangle", "D. Heart"],
                "correct": 1  # B
            },
            {
                "question": "If you add up all three interior angles of any triangle, what is the total sum?",
                "choices": ["A. 90 degrees", "B. 180 degrees", "C. 360 degrees", "D. 270 degrees"],
                "correct": 1  # B
            },
            {
                "question": "Which polygon has exactly 5 straight sides and 5 vertices?",
                "choices": ["A. Pentagon", "B. Hexagon", "C. Octagon", "D. Triangle"],
                "correct": 0  # A
            },
            {
                "question": "Farmer Ben arranged golden apples into 3 equal rows with 4 apples in each row. What multiplication sentence matches this array?",
                "choices": ["A. 3 + 4 = 7", "B. 3 x 4 = 12", "C. 3 + 3 + 3 = 9", "D. 4 + 4 = 8"],
                "correct": 1  # B
            },
            {
                "question": "A pizza is cut into 2 equal slices. If you eat 1 slice, what fraction of the pizza did you eat?",
                "choices": ["A. 1/3 (One-Third)", "B. 1/4 (One-Fourth)", "C. 1/2 (One-Half)", "D. 2/2 (Whole)"],
                "correct": 2  # C
            }
        ]

        print(f"✅ Quarter4 initialized with map: {self.map_name}")
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
                if marker == 'B' or marker == 'O':
                    self.npc_bromen_tile_x = x
                    self.npc_bromen_tile_y = y
                    self.npc_bromen_x = x * TILE_SIZE
                    self.npc_bromen_y = y * TILE_SIZE
                    self.npc_bromen_found = True
                    print(f"Bromen NPC (via {marker}) at: ({x}, {y})")
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
        def load_tile(filename, is_q4=False):
            if is_q4:
                path = os.path.join(self.OBJECTS_PATH, "quarter4tiles", filename)
            else:
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

        # Overwrite T and G with Q4 tiles for Quarter 4 Maps
        tiles["T"] = load_tile("dungeon1.png", is_q4=True)
        tiles["G"] = load_tile("floor.png", is_q4=True)
        tiles["W"] = load_tile("water.png", is_q4=True)
        tiles["F"] = load_tile("fountain.png", is_q4=True)
        tiles["*"] = load_tile("fountain.png", is_q4=True)
        tiles["S"] = load_tile("statue.png", is_q4=True)
        tiles["C"] = load_tile("pot.png", is_q4=True)
        tiles["|"] = load_tile("pillar.png", is_q4=True)
        tiles["L"] = load_tile("lily.png", is_q4=True)
        tiles["R"] = load_tile("torch.png", is_q4=True)
        tiles["$"] = load_tile("chest.png", is_q4=True)
        tiles["H"] = load_tile("banner.png", is_q4=True)
        
        # Map quiz stations and player spawn tiles to render on the smooth slate floor texture
        for k in ["1", "2", "3", "4", "5", "6", "P"]:
            tiles[k] = tiles["G"]

        # New Q4 tiles (Dungeon boundaries)
        q4_tiles = {
            "Z": "dungeon1.png",
            "M": "dungeon2.png",
            "n": "dungeon3.png",
            "s": "dungeon4.png",
            "t": "dungeon5.png",
            "J": "dungeon6.png",
            "Q": "dungeon7.png",
            "V": "dungeon8.png",
            "X": "dungeon9.png",
            "Y": "dungeon10.png"
        }

        for key, filename in q4_tiles.items():
            tiles[key] = load_tile(filename, is_q4=True)

        return tiles

    # ============================================================
    # LOAD PLAYER SPRITES
    # ============================================================
    def load_player_sprites(self):
        prefix = "boy"
        if hasattr(self, 'main_menu') and self.main_menu and getattr(self.main_menu, 'selected_student', None):
            gender = self.main_menu.selected_student.get("gender")
            if gender:
                gender = str(gender).lower()
                if gender in ["female", "girl", "f"]:
                    prefix = "female"

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
            "down": [load_sprite(f"{prefix}_down_1.png"), load_sprite(f"{prefix}_down_2.png")],
            "left": [load_sprite(f"{prefix}_left_1.png"), load_sprite(f"{prefix}_left_2.png")],
            "right": [load_sprite(f"{prefix}_right_1.png"), load_sprite(f"{prefix}_right_2.png")],
            "up": [load_sprite(f"{prefix}_up_1.png"), load_sprite(f"{prefix}_up_2.png")]
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
            except Exception:
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
    def load_station_npcs(self):
        def load_frames(folder_path, prefix):
            frames = []
            for i in range(8):
                filename = f"sprite_{prefix}{i:02d}.png"
                path = os.path.join(folder_path, filename)
                try:
                    if os.path.exists(path):
                        img = pygame.image.load(path).convert_alpha()
                        scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                        frames.append(scaled)
                except Exception as e:
                    print(f"Error loading frame {path}: {e}")
            if not frames:
                # Try loading standard sprite if animated frames are not found
                static_path = os.path.join(folder_path, f"{prefix}.png")
                if os.path.exists(static_path):
                    try:
                        img = pygame.image.load(static_path).convert_alpha()
                        scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                        frames.append(scaled)
                    except Exception as e:
                        print(f"Error loading static fallback: {e}")
                else:
                    placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    placeholder.fill((255, 180, 0))
                    frames.append(placeholder)
            return frames

        # Load knight static sprite
        knight_frames = []
        knight_path = os.path.join(self.NPC_PATH_KNIGHT, "knight.png")
        try:
            if os.path.exists(knight_path):
                img = pygame.image.load(knight_path).convert_alpha()
                knight_frames.append(pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)))
        except Exception as e:
            print(f"Error loading knight: {e}")
        if not knight_frames:
            p = pygame.Surface((TILE_SIZE, TILE_SIZE))
            p.fill((100, 100, 255))
            knight_frames.append(p)

        # Load oldman static sprite
        oldman_frames = []
        oldman_path = os.path.join(self.NPC_PATH_OLDMAN, "oldman.png")
        try:
            if os.path.exists(oldman_path):
                img = pygame.image.load(oldman_path).convert_alpha()
                oldman_frames.append(pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)))
        except Exception as e:
            print(f"Error loading oldman: {e}")
        if not oldman_frames:
            p = pygame.Surface((TILE_SIZE, TILE_SIZE))
            p.fill((255, 100, 100))
            oldman_frames.append(p)

        self.station_npcs = {
            1: {"name": "Circle Guardian (Q1)", "frames": load_frames(self.NPC_PATH_CIRCLE, "circlenpc"), "anim_frame": 0, "anim_timer": 0},
            2: {"name": "Star Guardian (Q1)", "frames": load_frames(self.NPC_PATH_STAR, "starnpc"), "anim_frame": 0, "anim_timer": 0},
            3: {"name": "Knight Guardian (Q2)", "frames": knight_frames, "anim_frame": 0, "anim_timer": 0},
            4: {"name": "Sage Guardian (Q2)", "frames": oldman_frames, "anim_frame": 0, "anim_timer": 0},
            5: {"name": "Number 3 Guardian (Q3)", "frames": load_frames(self.NPC_PATH_NUM3, "number3npc"), "anim_frame": 0, "anim_timer": 0},
            6: {"name": "Number 4 Guardian (Q3)", "frames": load_frames(self.NPC_PATH_NUM4, "number4npc"), "anim_frame": 0, "anim_timer": 0},
        }
        print("✅ Loaded 6 Animated/Static Station NPCs for Quarter 4 Evaluation")


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

            # Get width/height tile count
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
        # PORTAL ANIMATION INNER CLASS
        # ============================================================
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
                self.frame_delay = 5  # Speed: update frame every 5 updates

            def update(self):
                self.timer += 1
                if self.timer >= self.frame_delay:
                    self.timer = 0
                    self.current_frame = (self.current_frame + 1) % len(self.frames)

            def draw(self, screen, camera_x, camera_y, zoom, screen_width, screen_height):
                screen_x = (self.x - camera_x) * zoom
                screen_y = (self.y - camera_y) * zoom

                # Draw check within screen boundary
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

        cache = {}
        for d, size in PORTAL_SIZES.items():
            cache[d] = load_portal_frames(d, size[0], size[1])
        return cache

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
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    modified = True
            if modified:
                self.render_map[y] = ''.join(row_list)

    # ============================================================
    # COLLISION
    # ============================================================
    def can_move(self, nx, ny):
        # Check all 4 corners of the player's bounding box (with 4 pixels padding for smooth movement)
        padding = 4
        corners = [
            (nx + padding, ny + padding),
            (nx + TILE_SIZE - padding - 1, ny + padding),
            (nx + padding, ny + TILE_SIZE - padding - 1),
            (nx + TILE_SIZE - padding - 1, ny + TILE_SIZE - padding - 1)
        ]

        npc_positions = []
        for marker, positions in self.npc_positions_data.items():
            npc_positions.extend(positions)

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

            for npc_col, npc_row in npc_positions:
                if col == npc_col and row == npc_row:
                    player_col = int(self.player_x // TILE_SIZE)
                    player_row = int(self.player_y // TILE_SIZE)
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
                        # Walkable tiles are walkable. Skeletons/Bromen respect map obstacles.
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
            self.main_menu.quarter4 = None
            # Recreate the stage select to reset position
            from .stageselect import StageSelect
            self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
            print("🏠 Returning to stage select")
            self.completed = True
            
            # Save student progress immediately to record quarter completion
            from db.save_system import save_student_progress
            save_student_progress(self.main_menu)
            
        return "back"

    # ============================================================
    # CHECK PORTAL TELEPORT
    # ============================================================
    def check_portal_teleport_on_hold(self):
        if self.quiz_state != 0 and self.quiz_state != 6:
            return False
        current_portal = None
        for portal in self.portals:
            if portal.contains_position(self.player_x, self.player_y):
                current_portal = portal
                break

        if current_portal and self.fist_closed and self.teleport_cooldown <= 0:
            if current_portal.direction == self.goal_portal_direction:
                # Portal is locked until the quiz is completed
                if self.quiz_state < 6:
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
    def trigger_click(self, pos):
        from db.save_system import save_student_progress
        
        # State 1: Quiz Question dialogue click
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
                        self.answered_stations.add(self.quiz_station_index)
                        print(f"✨ Correct answer selected for Station {self.quiz_station_index}!")
                    else:
                        self.first_attempt_correct[self.current_question_index + 1] = False
                        self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
                        
                        if self.station_attempts[self.quiz_station_index] < 2:
                            # 1st wrong attempt: Give player 1 more try
                            self.quiz_state = 2
                            print(f"❌ Incorrect answer selected! (Attempt 1 of 2)")
                        else:
                            # 2nd wrong attempt: Out of tries! Recorded as wrong, but award emblem so game proceeds
                            self.quiz_state = 4
                            self.answered_stations.add(self.quiz_station_index)
                            print(f"❌ Incorrect answer on 2nd try! Out of tries. Station {self.quiz_station_index} emblem awarded.")
                    
                    save_student_progress(self.main_menu)
                    break
 
        # State 2: Incorrect answer feedback click (1 try remaining)
        elif self.quiz_state == 2:
            box_w, box_h = 520, 250
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 160, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                save_student_progress(self.main_menu)
            
        # State 3: Correct answer transition screen click
        elif self.quiz_state == 3:
            box_w, box_h = 500, 240
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 140, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 0
                save_student_progress(self.main_menu)

        # State 4: Out of tries reveal screen click (Player gets emblem and continues)
        elif self.quiz_state == 4:
            box_w, box_h = 560, 260
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 195, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 0
                save_student_progress(self.main_menu)
                
        # State 5: Final speech click
        elif self.quiz_state == 5:
            box_w, box_h = 550, 300
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 210, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 6
                save_student_progress(self.main_menu)
                print("🎓 Quarter 4 evaluation completed!")

        # Bromen Proximity Dialogue click
        elif self.bromen_dialogue_state in [1, 2]:
            if hasattr(self, 'bromen_btn_rect') and self.bromen_btn_rect.collidepoint(pos):
                if self.bromen_dialogue_state == 1:
                    self.bromen_dialogue_state = 0
                    # Push back player to prevent instant trigger loop
                    self.player_x -= SPEED * 8
                else:
                    self.bromen_dialogue_state = 0
                    self.emblem_puzzle_active = True
                    self.init_emblem_puzzle()
                save_student_progress(self.main_menu)

        # Emblem Puzzle reset button click
        elif self.emblem_puzzle_active:
            if hasattr(self, 'reset_btn_rect') and self.reset_btn_rect.collidepoint(pos):
                self.init_emblem_puzzle()

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1

        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt

        if hasattr(self, 'player_block_timer') and self.player_block_timer > 0:
            self.player_block_timer -= dt

        # Update animations for all 6 Shape/Number Station NPCs
        if hasattr(self, 'station_npcs') and self.station_npcs:
            for num, data in self.station_npcs.items():
                if len(data["frames"]) > 1:
                    data["anim_timer"] += 1
                    if data["anim_timer"] >= 6:
                        data["anim_timer"] = 0
                        data["anim_frame"] = (data["anim_frame"] + 1) % len(data["frames"])

        # Proximity interaction check for any unanswered Station NPC
        if self.quiz_state == 0 and hasattr(self, 'quiz_stations'):
            import math
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            for num, pos in self.quiz_stations.items():
                is_answered = num in self.answered_stations
                if num == 5:
                    is_answered = (5 in self.answered_stations) and (6 in self.answered_stations)
                
                if not is_answered:
                    npc_center_x = pos[0] * TILE_SIZE + TILE_SIZE // 2
                    npc_center_y = pos[1] * TILE_SIZE + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - npc_center_x, player_center_y - npc_center_y)
                    if dist < TILE_SIZE * 1.5:
                        if num == 5 and 5 in self.answered_stations:
                            self.quiz_station_index = 6
                            self.current_question_index = 5
                        else:
                            self.quiz_station_index = num
                            self.current_question_index = num - 1
                        self.quiz_state = 1
                        self.selected_choice_index = -1
                        print(f"🧙‍♂️ Interacting with Station {self.quiz_station_index} NPC!")
                        break

        # Proximity check for Bromen (Final obstacle) - Only activates once all objectives are completed
        if self.quiz_state == 0 and not self.emblem_puzzle_active and self.bromen_dialogue_state == 0 and self.npc_bromen_found:
            if len(self.answered_stations) >= 6:
                import math
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                bromen_center_x = self.npc_bromen_x + TILE_SIZE // 2
                bromen_center_y = self.npc_bromen_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - bromen_center_x, player_center_y - bromen_center_y)
                if dist < TILE_SIZE * 1.5:
                    self.bromen_dialogue_state = 2  # Ready for Mural Puzzle
                    print(f"🧙‍♂️ Objectives complete! Interacting with Bromen! state={self.bromen_dialogue_state}")

        # Update Bromen animation
        if self.npc_bromen_found and self.npc_bromen_sprites:
            self.npc_bromen_anim_timer += 1
            if self.npc_bromen_anim_timer >= 6:
                self.npc_bromen_anim_timer = 0
                self.npc_bromen_anim_frame = (self.npc_bromen_anim_frame + 1) % len(self.npc_bromen_sprites)

        # Update Emblem Puzzle if active
        if self.emblem_puzzle_active:
            self.update_emblem_puzzle()

        self.update_player_movement()
        self.check_portal_teleport_on_hold()

        for portal in self.portals:
            portal.update_animation()

        self.update_camera()

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        if self.quiz_state in [1, 2, 3, 4, 5] or self.emblem_puzzle_active or self.bromen_dialogue_state in [1, 2] or (hasattr(self, 'player_block_timer') and self.player_block_timer > 0):
            self.anim_frame = 0
            return

        vx, vy = 0, 0
        current_speed = SPEED

        # Hand Gesture / Cursor Directional Controls (Pure Gesture Navigation)
        center_x, center_y = self.width // 2, self.height // 2
        cursor_x, cursor_y = self.cursor_pos
        dx = cursor_x - center_x
        dy = cursor_y - center_y

        # Dynamic speed scaling: faster when hand is stretched further out
        dist_factor = 1.3 if (abs(dx) > 160 or abs(dy) > 160) else 1.0
        g_speed = current_speed * dist_factor

        if abs(dx) > 45:
            vx = g_speed if dx > 0 else -g_speed
            if dx > 0:
                self.player_dir = "right"
            elif dx < 0:
                self.player_dir = "left"

        if abs(dy) > 45:
            vy = g_speed if dy > 0 else -g_speed
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
            if self.anim_timer >= 8:
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
            scaled_size = int(TILE_SIZE * ZOOM)

            # For transparent floor props (fountains, statues, pots, pillars, braziers, chests, banners), draw clean floor first
            if c in ["F", "*", "S", "C", "|", "R", "$", "H"]:
                floor_img = self.tile_images.get("G", self.fallback_tile)
                scaled_floor = pygame.transform.scale(floor_img, (scaled_size, scaled_size))
                self.screen.blit(scaled_floor, (screen_x, screen_y))
            # For lily pads on water, draw water first
            elif c == "L":
                water_img = self.tile_images.get("W", self.fallback_tile)
                scaled_water = pygame.transform.scale(water_img, (scaled_size, scaled_size))
                self.screen.blit(scaled_water, (screen_x, screen_y))

            image = self.tile_images.get(c, self.fallback_tile)
            scaled_image = pygame.transform.scale(image, (scaled_size, scaled_size))
            self.screen.blit(scaled_image, (screen_x, screen_y))

            # Stardew Valley animated wave glints on water tiles
            if c in ['W', 'L']:
                shimmer = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                alpha = int(12 + 8 * math.sin((world_x * 0.03 + self.frame_counter * 0.05)))
                shimmer.fill((180, 230, 255, alpha))
                self.screen.blit(shimmer, (screen_x, screen_y))

            # Temple Aqua Brazier Pulsing Glow
            if c == 'R':
                glow = pygame.Surface((scaled_size * 2, scaled_size * 2), pygame.SRCALPHA)
                pulse = 0.5 + 0.5 * math.sin(self.frame_counter * 0.1)
                glow_alpha = int(25 + 15 * pulse)
                pygame.draw.circle(glow, (0, 230, 255, glow_alpha), (scaled_size, scaled_size), int(scaled_size * 0.85))
                pygame.draw.circle(glow, (200, 255, 255, int(glow_alpha * 0.6)), (scaled_size, scaled_size), int(scaled_size * 0.45))
                self.screen.blit(glow, (screen_x - scaled_size // 2, screen_y - scaled_size // 2))

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

        # Draw visible tiles using render_map (First pass: Skip trees)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char != 'T':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Station Pedestal Rings on the ground
        if hasattr(self, 'quiz_stations'):
            for num, pos in self.quiz_stations.items():
                is_answered = num in self.answered_stations
                if num == 5:
                    is_answered = (5 in self.answered_stations) and (6 in self.answered_stations)

                cx = (pos[0] * TILE_SIZE + TILE_SIZE // 2 - self.camera_x) * ZOOM
                cy = (pos[1] * TILE_SIZE + TILE_SIZE // 2 - self.camera_y) * ZOOM

                if -60 <= cx <= self.width + 60 and -60 <= cy <= self.height + 60:
                    base_r = int((TILE_SIZE // 2 + 5) * ZOOM)
                    ring_surf = pygame.Surface((base_r * 2 + 12, base_r * 2 + 12), pygame.SRCALPHA)
                    center_pt = (base_r + 6, base_r + 6)
                    if is_answered:
                        pygame.draw.circle(ring_surf, (56, 232, 198, 90), center_pt, base_r, 3)
                        pygame.draw.circle(ring_surf, (56, 232, 198, 40), center_pt, base_r - 4)
                    else:
                        pulse = int(math.sin(self.frame_counter * 0.12) * 3)
                        r = base_r + pulse
                        pygame.draw.circle(ring_surf, (255, 215, 0, 140), center_pt, r, 3)
                        pygame.draw.circle(ring_surf, (0, 240, 255, 50), center_pt, max(1, r - 5))
                    self.screen.blit(ring_surf, (cx - base_r - 6, cy - base_r - 6))

        # Only draw portals when quiz is complete
        if self.quiz_state == 6:
            for portal in self.portals:
                portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height)

        # Draw Station NPCs at coordinates 1, 2, 3, 4, 5, 6
        if hasattr(self, 'quiz_stations') and hasattr(self, 'station_npcs'):
            for num, pos in self.quiz_stations.items():
                is_answered = num in self.answered_stations
                if num == 5:
                    is_answered = (5 in self.answered_stations) and (6 in self.answered_stations)

                if num in self.station_npcs and not is_answered and self.quiz_state < 6:
                    data = self.station_npcs[num]
                    frame = data["frames"][data["anim_frame"]]
                    self.draw_npc_static(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, frame)

        # Draw Bromen
        if self.npc_bromen_found and self.npc_bromen_sprites:
            frame = self.npc_bromen_sprites[self.npc_bromen_anim_frame]
            self.draw_npc_static(self.npc_bromen_x, self.npc_bromen_y, frame)

        self.draw_player()

        # Draw visible tree tiles on top of everything (Second pass)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char == 'T':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Active Objective NPC Indicator and Off-Screen Compass Pointer
        self.draw_offscreen_compass_pointer()

        # Draw quiz dialog overlays
        if self.quiz_state == 1:
            self.draw_quiz_dialog()
        elif self.quiz_state == 2:
            self.draw_wrong_dialog()
        elif self.quiz_state == 3:
            self.draw_correct_dialog()
        elif self.quiz_state == 4:
            self.draw_out_of_tries_dialog()
        elif self.quiz_state == 5:
            self.draw_final_dialog()

        # Draw Bromen proximity dialogue
        if self.bromen_dialogue_state in [1, 2]:
            self.draw_bromen_dialog()

        # Draw Emblem Puzzle overlay
        if self.emblem_puzzle_active:
            self.draw_emblem_puzzle()

        self.draw_ui()

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
            box_w, box_h = 360, 85
            box_x = (self.width - box_w) // 2
            box_y = self.height - box_h - 15
            
            # Translucent slate blue background
            bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            bg_surf.fill((16, 32, 44, 215))
            self.screen.blit(bg_surf, (box_x, box_y))
            
            # Border: Cyan/Gold when exploring, Emerald Green when complete
            border_color = (0, 210, 230) if self.quiz_state < 6 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_w, box_h), 2, border_radius=10)
            
            # Header title in Gold
            title_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
            title_surf = title_font.render("WATER TEMPLE OBJECTIVES", True, (255, 215, 0))
            self.screen.blit(title_surf, (box_x + 15, box_y + 8))
            
            # 6 Segmented Progress Pips for Grade 2 visual feedback
            pip_w, pip_h = 16, 8
            pip_spacing = 5
            start_pip_x = box_x + box_w - 15 - (6 * (pip_w + pip_spacing) - pip_spacing)
            for s_idx in range(1, 7):
                px = start_pip_x + (s_idx - 1) * (pip_w + pip_spacing)
                py = box_y + 11
                is_done = s_idx in self.answered_stations
                pip_color = (56, 232, 198) if is_done else (40, 60, 75)
                pygame.draw.rect(self.screen, pip_color, (px, py, pip_w, pip_h), border_radius=3)
                pygame.draw.rect(self.screen, (255, 255, 255) if is_done else (20, 35, 45), (px, py, pip_w, pip_h), 1, border_radius=3)
            
            # Details font
            item_font = pygame.font.SysFont("Comic Sans MS", 12)
            
            # Quiz completion progress item
            q_count = len(self.answered_stations)
            obj1 = f"• Quiz Progress: {q_count}/6 questions answered"
            obj1_color = (255, 255, 255) if q_count < 6 else (34, 197, 94)
            obj1_surf = item_font.render(obj1, True, obj1_color)
            self.screen.blit(obj1_surf, (box_x + 15, box_y + 30))
            
            # Goal portal state item
            if len(self.answered_stations) < 6:
                obj2 = "• Portal Status: LOCKED (Answer all 6 questions)"
                obj2_color = (244, 63, 94)  # Rose
            elif self.quiz_state < 6:
                obj2 = "• Emblems Collected! Approach Bromen to open gate"
                obj2_color = (255, 215, 0)  # Gold
            else:
                obj2 = "• Portal Status: OPEN (Enter the portal to finish!)"
                obj2_color = (34, 197, 94)  # Green
            obj2_surf = item_font.render(obj2, True, obj2_color)
            self.screen.blit(obj2_surf, (box_x + 15, box_y + 52))

        if self.show_info:
            npc_status = []
            if hasattr(self, 'station_npcs'):
                for k, v in self.station_npcs.items():
                    if k not in self.answered_stations:
                        npc_status.append(v["name"])

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
                    from db.save_system import show_saving_and_exit
                    show_saving_and_exit(self.main_menu)
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.cursor_pos = event.pos
            self.trigger_click(event.pos)
            
            if self.emblem_puzzle_active and not self.emblem_puzzle_solved:
                for piece in self.emblem_puzzle_pieces:
                    if not piece["is_placed"]:
                        piece_rect = pygame.Rect(piece["x"], piece["y"], 75, 75)
                        if piece_rect.collidepoint(event.pos):
                            self.dragged_emblem = piece
                            self.drag_offset_x = piece["x"] - event.pos[0]
                            self.drag_offset_y = piece["y"] - event.pos[1]
                            break
                            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.emblem_puzzle_active and self.dragged_emblem:
                matching_slot = None
                for slot in self.emblem_puzzle_slots:
                    if slot["name"] == self.dragged_emblem["name"]:
                        matching_slot = slot
                        break
                if matching_slot:
                    dist = math.hypot(self.dragged_emblem["x"] - matching_slot["target_x"], self.dragged_emblem["y"] - matching_slot["target_y"])
                    if dist < 45:
                        self.dragged_emblem["x"] = matching_slot["target_x"]
                        self.dragged_emblem["y"] = matching_slot["target_y"]
                        self.dragged_emblem["is_placed"] = True
                        if self.sound_snap:
                            try:
                                self.sound_snap.play()
                            except Exception:
                                pass
                    else:
                        self.dragged_emblem["x"] = self.dragged_emblem["deck_x"]
                        self.dragged_emblem["y"] = self.dragged_emblem["deck_y"]
                self.dragged_emblem = None
                
        elif event.type == pygame.MOUSEMOTION:
            self.cursor_pos = event.pos
            if self.emblem_puzzle_active and self.dragged_emblem:
                self.dragged_emblem["x"] = event.pos[0] + self.drag_offset_x
                self.dragged_emblem["y"] = event.pos[1] + self.drag_offset_y
                
        return None

    # ============================================================
    # QUIZ DIALOGUE DRAWING METHODS
    # ============================================================
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
        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = speaker_font.render(speaker_name, True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 120, box_y + 48), 2)

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

        box_w, box_h = 520, 250
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = speaker_font.render(speaker_name, True, (220, 38, 38))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        msg_surf1 = q_font.render("Hmm, that is not correct.", True, (255, 255, 255))
        msg_surf2 = q_font.render("You have 1 try remaining! Think carefully.", True, (255, 215, 0))
        self.screen.blit(msg_surf1, (box_x + 25, box_y + 65))
        self.screen.blit(msg_surf2, (box_x + 25, box_y + 95))

        button_w, button_h = 200, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 160
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (220, 38, 38)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render("Try Again", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_out_of_tries_dialog(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(160)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 560, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (245, 158, 11), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = speaker_font.render(speaker_name, True, (245, 158, 11))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 15))

        q_data = self.quiz_questions[self.current_question_index]
        correct_choice_text = q_data["choices"][q_data["correct"]]

        q_font = pygame.font.SysFont("Comic Sans MS", 15)
        msg1 = q_font.render(f"Out of tries! The correct answer was: {correct_choice_text}", True, (255, 255, 255))
        msg2 = q_font.render("You still received the Emblem piece so your quest can continue!", True, (255, 215, 0))
        self.screen.blit(msg1, (box_x + 25, box_y + 60))
        self.screen.blit(msg2, (box_x + 25, box_y + 105))

        button_w, button_h = 200, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 195
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (245, 158, 11)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render("Continue", True, (255, 255, 255))
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
        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
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
        speaker_surf = speaker_font.render("Bromen", True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 120, box_y + 48), 2)

        q_font = pygame.font.SysFont("Comic Sans MS", 15)
        speech_lines = [
            "Outstanding, young adventurer! You have solved all my challenges.",
            "You know your mathematics and logical reasoning very well.",
            "I will now activate the portal. Step through to return to safety!"
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
        bg_color = (30, 41, 59) if not is_hovered else (218, 165, 32)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render("Activate Portal", True, (255, 255, 255) if not is_hovered else (0, 0, 0))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def load_emblem_puzzle_assets(self):
        self.emblem_puzzle_bg = None
        self.emblem_images = {}
        
        puzzle_dir = os.path.join(self.OBJECTS_PATH, "quarter4tiles", "EmblemPuzzle")
        bg_path = os.path.join(puzzle_dir, "background.png")
        if os.path.exists(bg_path):
            try:
                self.emblem_puzzle_bg = pygame.image.load(bg_path).convert()
                self.emblem_puzzle_bg = pygame.transform.smoothscale(self.emblem_puzzle_bg, (500, 500))
            except Exception as e:
                print(f"Error loading puzzle background: {e}")
                
        names = ["fish", "octopus", "starfish", "coin", "chest", "turtle"]
        for name in names:
            p_path = os.path.join(puzzle_dir, f"{name}.png")
            if os.path.exists(p_path):
                try:
                    img = pygame.image.load(p_path).convert_alpha()
                    self.emblem_images[name] = pygame.transform.smoothscale(img, (75, 75))
                except Exception as e:
                    print(f"Error loading emblem {name}: {e}")

    def load_puzzle_sounds(self):
        self.sound_correct = None
        self.sound_snap = None
        try:
            correct_path = os.path.join(self.BASE_DIR, "assets", "sounds", "correct.wav")
            if os.path.exists(correct_path):
                self.sound_correct = pygame.mixer.Sound(correct_path)
            snap_path = os.path.join(self.BASE_DIR, "assets", "sounds", "snap.wav")
            if os.path.exists(snap_path):
                self.sound_snap = pygame.mixer.Sound(snap_path)
        except Exception as e:
            print(f"Sound load warning: {e}")

    def init_emblem_puzzle(self):
        self.emblem_puzzle_pieces = []
        self.emblem_puzzle_slots = []
        self.dragged_emblem = None
        self.emblem_puzzle_solved = False
        self.emblem_puzzle_solved_time = 0
        
        box_w, box_h = 800, 560
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        
        mural_x = box_x + 30
        mural_y = box_y + 40
        
        slot_defs = [
            {"name": "fish", "tx": 100, "ty": 120},
            {"name": "octopus", "tx": 250, "ty": 110},
            {"name": "starfish", "tx": 400, "ty": 130},
            {"name": "coin", "tx": 90, "ty": 380},
            {"name": "chest", "tx": 250, "ty": 370},
            {"name": "turtle", "tx": 410, "ty": 390}
        ]
        
        for sd in slot_defs:
            self.emblem_puzzle_slots.append({
                "name": sd["name"],
                "target_x": mural_x + sd["tx"],
                "target_y": mural_y + sd["ty"]
            })
            
        deck_x = box_x + 560
        deck_y = box_y + 40
        deck_w = 210
        deck_h = 500
        
        import random
        shuffled_names = ["fish", "octopus", "starfish", "coin", "chest", "turtle"]
        random.shuffle(shuffled_names)
        
        for idx, name in enumerate(shuffled_names):
            row = idx // 2
            col = idx % 2
            px = deck_x + 25 + col * 90
            py = deck_y + 60 + row * 130
            
            self.emblem_puzzle_pieces.append({
                "name": name,
                "x": px,
                "y": py,
                "deck_x": px,
                "deck_y": py,
                "is_placed": False
            })

    def update_emblem_puzzle(self):
        if not self.emblem_puzzle_active:
            return
            
        if all(p["is_placed"] for p in self.emblem_puzzle_pieces):
            if self.emblem_puzzle_solved_time == 0:
                self.emblem_puzzle_solved_time = pygame.time.get_ticks()
            else:
                current_time = pygame.time.get_ticks()
                if current_time - self.emblem_puzzle_solved_time > 1800:
                    self.emblem_puzzle_solved = True
                    self.emblem_puzzle_active = False
                    self.quiz_state = 5  # final congrats speech!
                    self.bromen_dialogue_state = 3
                    if self.sound_correct:
                        try:
                            self.sound_correct.play()
                        except Exception:
                            pass
                    return
                    
        # Track gesture fist coordinates if hand is active
        if self.hand_detected and self.fist_closed:
            if not self.dragged_emblem:
                for piece in self.emblem_puzzle_pieces:
                    if not piece["is_placed"]:
                        piece_rect = pygame.Rect(piece["x"], piece["y"], 75, 75)
                        if piece_rect.collidepoint(self.cursor_pos):
                            self.dragged_emblem = piece
                            self.drag_offset_x = piece["x"] - self.cursor_pos[0]
                            self.drag_offset_y = piece["y"] - self.cursor_pos[1]
                            break
            if self.dragged_emblem:
                self.dragged_emblem["x"] = self.cursor_pos[0] + self.drag_offset_x
                self.dragged_emblem["y"] = self.cursor_pos[1] + self.drag_offset_y
        else:
            if self.dragged_emblem:
                matching_slot = None
                for slot in self.emblem_puzzle_slots:
                    if slot["name"] == self.dragged_emblem["name"]:
                        matching_slot = slot
                        break
                        
                if matching_slot:
                    dist = math.hypot(self.dragged_emblem["x"] - matching_slot["target_x"], self.dragged_emblem["y"] - matching_slot["target_y"])
                    if dist < 45:
                        self.dragged_emblem["x"] = matching_slot["target_x"]
                        self.dragged_emblem["y"] = matching_slot["target_y"]
                        self.dragged_emblem["is_placed"] = True
                        if self.sound_snap:
                            try:
                                self.sound_snap.play()
                            except Exception:
                                pass
                    else:
                        self.dragged_emblem["x"] = self.dragged_emblem["deck_x"]
                        self.dragged_emblem["y"] = self.dragged_emblem["deck_y"]
                self.dragged_emblem = None

    def draw_emblem_puzzle(self):
        if not self.emblem_puzzle_active:
            return
            
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        box_w, box_h = 800, 560
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        
        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((15, 23, 42, 240))
        self.screen.blit(bg_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (218, 165, 32), (box_x, box_y, box_w, box_h), 3, border_radius=12)
        
        title_font = pygame.font.SysFont("Comic Sans MS", 22, bold=True)
        title_surf = title_font.render("Ancient Shipwreck Mural Puzzle", True, (255, 215, 0))
        self.screen.blit(title_surf, (box_x + (box_w - title_surf.get_width()) // 2, box_y + 12))
        
        mural_x = box_x + 30
        mural_y = box_y + 40
        if self.emblem_puzzle_bg:
            self.screen.blit(self.emblem_puzzle_bg, (mural_x, mural_y))
        else:
            pygame.draw.rect(self.screen, (30, 41, 59), (mural_x, mural_y, 500, 500), border_radius=8)
        pygame.draw.rect(self.screen, (100, 116, 139), (mural_x, mural_y, 500, 500), 2, border_radius=8)
        
        deck_x = box_x + 560
        deck_y = box_y + 40
        deck_w = 210
        deck_h = 500
        pygame.draw.rect(self.screen, (30, 41, 59), (deck_x, deck_y, deck_w, deck_h), border_radius=12)
        pygame.draw.rect(self.screen, (100, 116, 139), (deck_x, deck_y, deck_w, deck_h), 2, border_radius=12)
        
        label_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        deck_lbl = label_font.render("COLLECTED EMBLEMS", True, (218, 165, 32))
        self.screen.blit(deck_lbl, (deck_x + (deck_w - deck_lbl.get_width()) // 2, deck_y + 15))
        
        for slot in self.emblem_puzzle_slots:
            name = slot["name"]
            sx = slot["target_x"]
            sy = slot["target_y"]
            
            if name in self.emblem_images:
                orig = self.emblem_images[name]
                silh = orig.copy()
                silh.fill((0, 0, 0, 140), special_flags=pygame.BLEND_RGBA_MULT)
                pygame.draw.circle(self.screen, (255, 215, 0), (sx + 37, sy + 37), 40, 1)
                self.screen.blit(silh, (sx, sy))
                
        for piece in self.emblem_puzzle_pieces:
            name = piece["name"]
            if name in self.emblem_images:
                if not piece["is_placed"] and piece != self.dragged_emblem:
                    self.screen.blit(self.emblem_images[name], (piece["x"], piece["y"]))
                    
        for piece in self.emblem_puzzle_pieces:
            name = piece["name"]
            if name in self.emblem_images:
                if piece["is_placed"]:
                    self.screen.blit(self.emblem_images[name], (piece["x"], piece["y"]))
                    pygame.draw.rect(self.screen, (56, 232, 198), (piece["x"], piece["y"], 75, 75), 2, border_radius=6)
                    
        if self.dragged_emblem:
            name = self.dragged_emblem["name"]
            if name in self.emblem_images:
                self.screen.blit(self.emblem_images[name], (self.dragged_emblem["x"], self.dragged_emblem["y"]))
                pygame.draw.rect(self.screen, (250, 204, 21), (self.dragged_emblem["x"], self.dragged_emblem["y"], 75, 75), 2, border_radius=6)
                
        reset_rect = pygame.Rect(deck_x + 30, deck_y + deck_h - 60, 150, 40)
        is_hover = reset_rect.collidepoint(self.cursor_pos)
        r_color = (255, 215, 0) if is_hover else (30, 41, 59)
        t_color = (0, 0, 0) if is_hover else (255, 255, 255)
        
        pygame.draw.rect(self.screen, r_color, reset_rect, border_radius=8)
        pygame.draw.rect(self.screen, (218, 165, 32), reset_rect, 2, border_radius=8)
        btn_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        btn_txt = btn_font.render("Reset Puzzle", True, t_color)
        self.screen.blit(btn_txt, btn_txt.get_rect(center=reset_rect.center))
        
        self.reset_btn_rect = reset_rect

    def draw_bromen_dialog(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 580, 240
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        speaker_surf = speaker_font.render("Guardian Bromen", True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 180, box_y + 48), 2)

        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        if self.bromen_dialogue_state == 1:
            line1 = "Halt, student! The exit portal is sealed."
            line2 = f"You must first collect all 6 sacred emblems from the"
            line3 = f"guardians in this crypt. (Current: {len(self.answered_stations)}/6)"
            btn_text = "I will go search for them"
        else:
            line1 = "Excellent! You have collected all 6 emblems."
            line2 = "To unlock the gate, you must now place the emblems"
            line3 = "onto the correct slots on the ancient shipwreck mural."
            btn_text = "Solve the Mural Puzzle"

        y_text = box_y + 65
        for line in [line1, line2, line3]:
            txt_surf = q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 25

        button_w, button_h = 300, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 170
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

        c_surf = q_font.render(btn_text, True, text_color)
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

        self.bromen_btn_rect = btn_rect

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

    def get_ui_font(self, size, bold=False):
        """Returns a high-legibility system font for UI elements"""
        return pygame.font.SysFont(["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial", "Comic Sans MS"], size, bold=bold)

    def draw_offscreen_compass_pointer(self):
        """Draw Active Objective NPC Indicator and Off-Screen Compass Pointer for Quarter 4"""
        import math

        target_info = None

        # 1. Target Determination
        if self.quiz_state == 0:
            if self.quiz_station_index <= 6 and hasattr(self, 'quiz_stations') and self.quiz_station_index in self.quiz_stations:
                if self.quiz_station_index not in self.answered_stations:
                    st_x, st_y = self.quiz_stations[self.quiz_station_index]
                    npc_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", f"Guardian {self.quiz_station_index}")
                    target_info = (st_x, st_y, npc_name)
            elif self.npc_bromen_found and not self.emblem_puzzle_solved:
                target_info = (self.npc_bromen_tile_x, self.npc_bromen_tile_y, "Bromen (Master Emblem)")

        if target_info:
            st_x, st_y, npc_name = target_info
            screen_npc_x = (st_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (st_y * TILE_SIZE - self.camera_y) * ZOOM

            # On-Screen Floating Objective Badge (Always visible over active target NPC)
            bob = math.sin(self.frame_counter * 0.15) * 3 * ZOOM
            badge_x = screen_npc_x + (TILE_SIZE * ZOOM) / 2 - 8 * ZOOM
            badge_y = screen_npc_y - 20 * ZOOM + bob

            badge_rect = pygame.Rect(badge_x, badge_y, 16 * ZOOM, 16 * ZOOM)
            pygame.draw.rect(self.screen, (255, 215, 0), badge_rect, border_radius=4)
            pygame.draw.rect(self.screen, (0, 0, 0), badge_rect, 1, border_radius=4)

            excl_font = pygame.font.SysFont("Comic Sans MS", int(14 * ZOOM), bold=True)
            excl_surf = excl_font.render("!", True, (0, 0, 0))
            excl_rect = excl_surf.get_rect(center=badge_rect.center)
            self.screen.blit(excl_surf, excl_rect)

            # Small pill name tag over active NPC
            name_font = self.get_ui_font(int(10 * ZOOM), bold=True)
            name_surf = name_font.render(f"{npc_name}", True, (255, 235, 120))
            tag_w = name_surf.get_width() + 10
            tag_h = name_surf.get_height() + 4
            tag_x = screen_npc_x + (TILE_SIZE * ZOOM) / 2 - tag_w / 2
            tag_y = badge_y - tag_h - 2

            tag_bg = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
            tag_bg.fill((15, 23, 42, 210))
            self.screen.blit(tag_bg, (tag_x, tag_y))
            pygame.draw.rect(self.screen, (255, 215, 0), (tag_x, tag_y, tag_w, tag_h), 1, border_radius=4)
            self.screen.blit(name_surf, (tag_x + 5, tag_y + 2))

            # Off-Screen Directional Compass Pointer
            is_on_screen = (40 <= screen_npc_x <= self.width - 60 and 40 <= screen_npc_y <= self.height - 110)
            if not is_on_screen:
                player_screen_x = (self.player_x - self.camera_x) * ZOOM
                player_screen_y = (self.player_y - self.camera_y) * ZOOM

                dx = screen_npc_x - player_screen_x
                dy = screen_npc_y - player_screen_y
                dist_tiles = int(math.hypot(self.player_x - st_x * TILE_SIZE, self.player_y - st_y * TILE_SIZE) // TILE_SIZE)

                angle = math.atan2(dy, dx)
                margin = 55
                clamp_x = max(margin, min(self.width - margin, player_screen_x + math.cos(angle) * 180))
                clamp_y = max(margin, min(self.height - 100, player_screen_y + math.sin(angle) * 180))

                # Draw glowing radar pointer pill
                ptr_font = self.get_ui_font(12, bold=True)
                ptr_text = f">> {npc_name} ({dist_tiles}m)"
                ptr_surf = ptr_font.render(ptr_text, True, (15, 23, 42))
                pw = ptr_surf.get_width() + 16
                ph = 26

                ptr_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)
                pygame.draw.rect(self.screen, (255, 215, 0), ptr_rect, border_radius=8)
                pygame.draw.rect(self.screen, (255, 255, 255), ptr_rect, 2, border_radius=8)
                self.screen.blit(ptr_surf, (ptr_rect.x + 8, ptr_rect.y + 4))

        # 2. Exit Portal Compass Pointer (When stage is completed)
        if self.quiz_state == 6 and self.portals:
            exit_p = self.portals[0]
            portal_cx = exit_p.get_center_x()
            portal_cy = exit_p.get_center_y()
            screen_p_x = (portal_cx - self.camera_x) * ZOOM
            screen_p_y = (portal_cy - self.camera_y) * ZOOM
            is_on_screen = (40 <= screen_p_x <= self.width - 60 and 40 <= screen_p_y <= self.height - 110)
            if not is_on_screen:
                player_screen_x = (self.player_x - self.camera_x) * ZOOM
                player_screen_y = (self.player_y - self.camera_y) * ZOOM
                dx = screen_p_x - player_screen_x
                dy = screen_p_y - player_screen_y
                dist_tiles = int(math.hypot(self.player_x - portal_cx, self.player_y - portal_cy) // TILE_SIZE)
                angle = math.atan2(dy, dx)
                margin = 55
                clamp_x = max(margin, min(self.width - margin, player_screen_x + math.cos(angle) * 180))
                clamp_y = max(margin, min(self.height - 100, player_screen_y + math.sin(angle) * 180))

                ptr_font = self.get_ui_font(12, bold=True)
                ptr_text = f">> Exit Portal ({dist_tiles}m)"
                ptr_surf = ptr_font.render(ptr_text, True, (15, 23, 42))
                pw = ptr_surf.get_width() + 16
                ph = 26

                ptr_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)
                pygame.draw.rect(self.screen, (74, 222, 128), ptr_rect, border_radius=8)
                pygame.draw.rect(self.screen, (255, 255, 255), ptr_rect, 2, border_radius=8)
                self.screen.blit(ptr_surf, (ptr_rect.x + 8, ptr_rect.y + 4))

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()