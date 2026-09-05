# screens/quarter4.py - Quarter 4 Map Handler (map11.txt)

import pygame
import os
import sys
import cv2
import numpy as np
import time
import random
import math
from .map_loader import MapLoader
from core.camera_system import LoLCamera

try:
    from db import db
except ImportError:
    try:
        from db.connect_db import db
    except ImportError:
        db = None

# ============================================================
# SETTINGS
# ============================================================
TILE_SIZE = 32
FPS = 60
SPEED = 2.2

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
    def __init__(self, screen, main_menu, map_name=None):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()
        self.map_name = map_name if map_name else "map11.txt"

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

        # 10-Minute Stage Timer
        self.stage_time_limit = 600.0
        self.stage_time_remaining = 600.0
        self.time_up_dialog_active = False
        self.timer_warning_played = False

        # Universal In-Stage Pause Menu
        from core.pause_menu import InGamePauseMenu
        self.pause_menu = InGamePauseMenu(self.screen, self.width, self.height, self.main_menu, self.return_to_stage_select, restart_callback=self.restart_level)

        # 3-Star Victory Report Card & Celebration Particles
        from core.report_card import VictoryReportCard, CelebrationParticleSystem
        self.celebration_particles = CelebrationParticleSystem()
        self.victory_card = VictoryReportCard(self.screen, self.width, self.height, self.main_menu,
                                              quarter_id="quarter4",
                                              replay_callback=self.restart_level,
                                              continue_callback=self.finish_and_return_to_hub)

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

        self.NPC_PATH_AQUA_SPRITE = os.path.join(
            self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "quarter4", "aqua_sprite"
        )
        self.NPC_PATH_CORAL_SAGE = os.path.join(
            self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "quarter4", "coral_sage"
        )
        self.NPC_PATH_TIDE_KNIGHT = os.path.join(
            self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "quarter4", "tide_knight"
        )
        self.NPC_PATH_AXOLOTL = os.path.join(
            self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "quarter4", "axolotl"
        )
        self.NPC_PATH_SEA_DRAKE = os.path.join(
            self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "quarter4", "sea_drake"
        )
        self.NPC_PATH_WATER_ELDER = os.path.join(
            self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "quarter4", "water_elder"
        )

        # ============================================================
        # MAP LOADER
        # ============================================================
        self.map_loader = MapLoader(self.BASE_DIR)
        self.current_map_name = map_name

        # Load the specified map
        if not self.map_loader.load_map(map_name):
            print(f"[FAIL] Failed to load {map_name}")
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
        self.lol_camera = LoLCamera(self.width, self.height, zoom=ZOOM)
        self.camera_x = 0
        self.camera_y = 0

        # ============================================================
        # LOAD TILE IMAGES
        # ============================================================
        self.tile_images = self.load_tile_images()
        self.fallback_tile = self.tile_images.get('G')
        if not self.fallback_tile:
            self.fallback_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.fallback_tile.fill((34, 197, 94))

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
        self.bromen_proximity_cooldown_end = 0  # Cooldown timestamp for proximity check
        self.key_puzzle_active = False
        self.key_puzzle_solved = False
        self.emblem_puzzle_active = False
        self.emblem_puzzle_solved = False
        # Map 12 Addition Equation Puzzle State
        self.addition_slots = []
        self.addition_pieces = []
        self.dragged_addition_piece = None
        self.addition_puzzle_solved = False
        self.addition_is_correct = False
        self.addition_continue_btn_rect = None
        self.addition_reset_btn_rect = None
        self.addition_equation_target = (7, 5, 12)
        self.award_anim_active = False
        self.award_anim_start_time = 0
        self.award_key_index = 1
        self.award_key_sprite = None
        self.load_key_puzzle_assets()
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
        self.lol_camera.snap_to(self.player_x, self.player_y, TILE_SIZE, self.MAP_WIDTH, self.MAP_HEIGHT)
        self.camera_x = self.lol_camera.camera_x
        self.camera_y = self.lol_camera.camera_y

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

        # Map 12 Unique Mechanic: The Lotus Raft & Canal Rapids Cruise
        self.is_map12 = "map12" in str(self.map_name).lower()
        self.raft_x = 30.0 * TILE_SIZE
        self.raft_y = 9.0 * TILE_SIZE
        self.raft_target_x = 36.0 * TILE_SIZE
        self.raft_speed = 75.0  # pixels/second
        self.raft_state = "docked_west"  # 'docked_west', 'ready_to_sail', 'sailing', 'docked_east'
        self.raft_passenger = False
        self.raft_wake_particles = []
        self.water_particles = []
        self.valve_names = [
            "Circle Sluice (Top-Left)",
            "Star Sluice (Bottom-Left)",
            "Knight Sluice (Top-Right)",
            "Sage Sluice (Bottom-Right)",
            "North Aqueduct Sluice",
            "South Aqueduct Sluice"
        ]
        self.valve_colors = [
            (56, 189, 248),   # Cyan
            (250, 204, 21),   # Gold
            (99, 102, 241),   # Royal Cobalt
            (168, 85, 247),   # Amethyst Purple
            (34, 197, 94),    # Emerald Green
            (244, 63, 94)     # Coral Rose
        ]

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
                    print(f"[LOC] Quiz Station {num} found at: ({x}, {y})")

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

        print(f"[OK] Quarter4 initialized with map: {self.map_name}")
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

        # Map 12: Guarantee Boat Guardian Bromen is stationed at (29, 9) directly in front of the Lotus Raft at (30, 9)
        if getattr(self, 'is_map12', False):
            self.npc_bromen_tile_x = 29
            self.npc_bromen_tile_y = 9
            self.npc_bromen_x = 29 * TILE_SIZE
            self.npc_bromen_y = 9 * TILE_SIZE
            self.npc_bromen_found = True
            if 'B' not in self.npc_positions_data:
                self.npc_positions_data['B'] = []
            if (29, 9) not in self.npc_positions_data['B']:
                self.npc_positions_data['B'].append((29, 9))
            print(f"[Bromen] Boat Guardian Bromen stationed at ({self.npc_bromen_tile_x}, {self.npc_bromen_tile_y}) directly guarding the Lotus Raft (30, 9)!")

    # ============================================================
    # LOAD TILE IMAGES
    # ============================================================
    def load_tile_images(self):
        def load_tile(filename, is_q4=False, subfolder=None):
            if is_q4:
                if subfolder:
                    path = os.path.join(self.OBJECTS_PATH, "quarter4tiles", subfolder, filename)
                else:
                    path = os.path.join(self.OBJECTS_PATH, "quarter4tiles", filename)
                    if not os.path.exists(path):
                        doorkeys_p = os.path.join(self.OBJECTS_PATH, "quarter4tiles", "Doorkeys", filename)
                        if os.path.exists(doorkeys_p):
                            path = doorkeys_p
            else:
                path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                return image
            except Exception:
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((34, 197, 94))
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

        # Quarter 4 Top-down Doors (Closed and Open states)
        tiles["["] = load_tile("door_topdown_left.png", is_q4=True, subfolder="Doorkeys")
        tiles["]"] = load_tile("door_topdown_right.png", is_q4=True, subfolder="Doorkeys")
        tiles["{"] = load_tile("door_topdown_left_open.png", is_q4=True, subfolder="Doorkeys")
        tiles["}"] = load_tile("door_topdown_right_open.png", is_q4=True, subfolder="Doorkeys")
        
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
            print(f"[WARN] NPC path does not exist: {npc_path}")
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

        print(f"[OK] Loaded {len(frames)} frames for {npc_name}")
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
            1: {
                "name": "Aqua Sprite Marina",
                "title": "Guardian of the Azure Fountain",
                "frames": load_frames(self.NPC_PATH_AQUA_SPRITE, "aquasprite"),
                "anim_frame": 0,
                "anim_timer": 0
            },
            2: {
                "name": "Coral Sage Sheldon",
                "title": "Elder of the Geyser Basin",
                "frames": load_frames(self.NPC_PATH_CORAL_SAGE, "coralsage"),
                "anim_frame": 0,
                "anim_timer": 0
            },
            3: {
                "name": "Tide Knight Finneas",
                "title": "Champion of the Torrent Gate",
                "frames": load_frames(self.NPC_PATH_TIDE_KNIGHT, "tideknight"),
                "anim_frame": 0,
                "anim_timer": 0
            },
            4: {
                "name": "Axolotl Scholar Lani",
                "title": "Keeper of the Pearl Falls",
                "frames": load_frames(self.NPC_PATH_AXOLOTL, "axolotl"),
                "anim_frame": 0,
                "anim_timer": 0
            },
            5: {
                "name": "River Drake Coral",
                "title": "Sentinel of the Grand Aqueduct",
                "frames": load_frames(self.NPC_PATH_SEA_DRAKE, "seadrake"),
                "anim_frame": 0,
                "anim_timer": 0
            },
            6: {
                "name": "Whirlpool Elder Glaucus",
                "title": "Master of Oceanic Currents",
                "frames": load_frames(self.NPC_PATH_WATER_ELDER, "waterelder"),
                "anim_frame": 0,
                "anim_timer": 0
            },
        }
        print("[OK] Loaded 6 Animated Water-Themed Station NPCs for Quarter 4 Evaluation")


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
        self.portals = []
        # Use game_map for portal detection so markers are never lost
        for y, row in enumerate(self.game_map):
            row_list = list(self.render_map[y]) if y < len(self.render_map) else []
            game_row_list = list(row)
            modified = False
            for x, c in enumerate(row):
                if c in ['r', 'l', 'u', 'd']:
                    dir_map = {'r': 'right', 'l': 'left', 'u': 'up', 'd': 'down'}
                    p_dir = dir_map[c]
                    # Check if an existing portal of the same direction already covers this area
                    already_covered = any(
                        p.direction == p_dir and abs(p.tile_x - x) <= 2 and abs(p.tile_y - y) <= 2
                        for p in self.portals
                    )
                    if not already_covered:
                        portal = self.Portal(x, y, p_dir, is_static=True)
                        portal.set_animation(self.portal_frames_cache[p_dir])
                        self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = 'G'
                    game_row_list[x] = 'G'
                    modified = True
            if modified:
                if row_list and y < len(self.render_map):
                    self.render_map[y] = ''.join(row_list)
                self.game_map[y] = ''.join(game_row_list)

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

        # If currently sailing aboard the Lotus Raft, lock manual movement
        if getattr(self, 'raft_passenger', False):
            return False

        for cx, cy in corners:
            col = int(cx // TILE_SIZE)
            row = int(cy // TILE_SIZE)
            if row < 0 or row >= self.ROWS or col < 0 or col >= self.COLS:
                return False
            if row >= len(self.game_map) or col >= len(self.game_map[row]):
                return False
            tile = self.game_map[row][col]

            if tile not in self.WALKABLE_TILES:
                # Map 12: Allow stepping on the docked raft when docked at the East Pier
                if getattr(self, 'is_map12', False) and getattr(self, 'raft_state', None) == 'docked_east':
                    if row == 9 and col in [35, 36]:
                        continue
                return False

            # Block entire 2-block wide closed double doors span
            if not (self.key_puzzle_solved or self.emblem_puzzle_solved):
                if col > 0 and self.game_map[row][col - 1] == '[':
                    return False
                if col < len(self.game_map[row]) - 1 and self.game_map[row][col + 1] == ']':
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

    def save_quarter4_game_result(self):
        import threading
        threading.Thread(target=self._run_save_quarter4_game_result, daemon=True).start()

    def _run_save_quarter4_game_result(self):
        try:
            if not db:
                return
            student_db_id = getattr(self.main_menu, 'student_db_id', None)
            if not student_db_id:
                return
            total_questions = min(6, len(self.quiz_questions))
            correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
            percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 0.0
            score = int(correct_answers * 20)

            assessment_id = db.get_assessment_id(quarter=4)
            if assessment_id:
                print(f"[LOG] Linked Quarter 4 result to Assessment ID: {assessment_id}")

            feedback_msg = f"Completed Quarter 4 (Water Temple). Answered {correct_answers} of {total_questions} questions correctly on first attempt."
            grade_level = getattr(self.main_menu, 'selected_student', {}).get('level', 'Grade 2')

            success = db.save_game_result(
                student_id=student_db_id,
                score=score,
                total_questions=total_questions,
                correct_answers=correct_answers,
                percentage=percentage,
                feedback=feedback_msg,
                grade_level=grade_level,
                assessment_id=assessment_id
            )
            if success:
                print(f"[WIN] Successfully saved Quarter 4 Game Result to Database for Student DB ID {student_db_id}!")
                print(f"   Score: {score}/{total_questions} ({percentage:.1f}%)")
        except Exception as e:
            print(f"[WARN] Error saving Quarter 4 game result: {e}")

    # ============================================================
    # RETURN TO STAGE SELECT
    # ============================================================
    def return_to_stage_select(self, completed=True):
        """Return to the stage select screen"""
        if self.main_menu:
            if completed:
                self.save_quarter4_game_result()
                try:
                    total_questions = min(6, len(self.quiz_questions)) if hasattr(self, 'quiz_questions') and self.quiz_questions else 6
                    correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
                    percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 100.0
                    score = int(correct_answers * 20)
                    from db.save_system import mark_quarter_completed
                    mark_quarter_completed(self.main_menu, "quarter4", score=score, percentage=percentage, total_questions=total_questions)
                    if hasattr(self.main_menu, 'audio_manager'):
                        self.main_menu.audio_manager.play_sfx("victory_fanfare")
                        self.main_menu.audio_manager.play_sfx("portal_warp")
                except Exception as e:
                    print(f"[WARN] Error recording Quarter 4 completion: {e}")

            self.main_menu.current_screen = "stage_select"
            self.main_menu.quarter4 = None
            # Recreate the stage select to reset position
            from .stageselect import StageSelect
            self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
            print("[HOME] Returning to stage select")
            if completed:
                self.completed = True
            
            # Save student progress immediately to record quarter completion
            from db.save_system import save_student_progress
            save_student_progress(self.main_menu)
            
        return "back"

    def restart_level(self):
        """Restarts the current Quarter 4 level."""
        from screens.quarter4 import Quarter4
        self.main_menu.quarter4 = Quarter4(self.screen, self.main_menu, self.map_name)

    def finish_and_return_to_hub(self):
        """Callback invoked by Victory Report Card to transition back to stage select."""
        self.return_to_stage_select(completed=True)

    # ============================================================
    # CHECK PORTAL TELEPORT
    # ============================================================
    def check_portal_teleport_on_hold(self):
        # Allow portal check when waiting (state 0) or completed (state 6 or puzzle solved)
        if self.quiz_state not in [0, 6] and not getattr(self, 'key_puzzle_solved', False) and not getattr(self, 'addition_puzzle_solved', False):
            return False

        current_portal = None
        p_rect = pygame.Rect(self.player_x + 4, self.player_y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        p_center_x = self.player_x + TILE_SIZE // 2
        p_center_y = self.player_y + TILE_SIZE // 2

        for portal in self.portals:
            port_rect = pygame.Rect(portal.get_world_x(), portal.get_world_y(), portal.get_width_pixels(), portal.get_height_pixels())
            if port_rect.colliderect(p_rect) or portal.contains_position(p_center_x, p_center_y):
                current_portal = portal
                break

        if current_portal and self.teleport_cooldown <= 0:
            if current_portal.direction == self.goal_portal_direction:
                # Goal portal is unlocked once evaluation/puzzle is completed
                is_unlocked = (
                    self.quiz_state >= 6 or 
                    getattr(self, 'key_puzzle_solved', False) or 
                    getattr(self, 'addition_puzzle_solved', False)
                )
                if not is_unlocked:
                    return False
                print(f"[TARGET] Goal reached! Showing 3-Star Victory Report Card in Quarter 4...")
                self.save_quarter4_game_result()
                total_questions = min(6, len(self.quiz_questions)) if hasattr(self, 'quiz_questions') and self.quiz_questions else 6
                correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
                percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 100.0
                score = int(correct_answers * 20)
                from db.save_system import mark_quarter_completed
                mark_quarter_completed(self.main_menu, "quarter4", score=score, percentage=percentage, total_questions=total_questions)
                self.victory_card.show(total_questions=total_questions, correct_first_try=correct_answers, score=score)
                return True

            # Regular portal teleport (to another portal on same map) - requires fist hold or space
            if self.fist_closed:
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
        self.lol_camera.update(
            self.player_x,
            self.player_y,
            cursor_pos=self.cursor_pos,
            map_width=self.MAP_WIDTH,
            map_height=self.MAP_HEIGHT,
            tile_size=TILE_SIZE,
            enable_edge_scroll=True
        )
        self.camera_x = self.lol_camera.camera_x
        self.camera_y = self.lol_camera.camera_y

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
        if hasattr(self, 'victory_card') and self.victory_card.active:
            res = self.victory_card.handle_click(pos)
            if res:
                return

        if self.pause_menu.handle_click(pos):
            return

        if getattr(self, 'time_up_dialog_active', False):
            box_w, box_h = 560, 260
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            retry_rect = pygame.Rect(box_x + 40, box_y + 175, 220, 46)
            exit_rect = pygame.Rect(box_x + box_w - 260, box_y + 175, 220, 46)
            if retry_rect.collidepoint(pos):
                self.stage_time_remaining = 600.0
                self.time_up_dialog_active = False
                from screens.quarter4 import Quarter4
                self.main_menu.quarter4 = Quarter4(self.screen, self.main_menu, self.map_name)
                return
            elif exit_rect.collidepoint(pos):
                self.time_up_dialog_active = False
                from screens.stageselect import StageSelect
                self.main_menu.current_screen = "stage_select"
                self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
                self.main_menu.quarter4 = None
                return
            return

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
                        if hasattr(self.main_menu, 'audio_manager'):
                            self.main_menu.audio_manager.play_sfx("correct")
                            self.main_menu.audio_manager.play_sfx("star_chime")
                        if hasattr(self, 'celebration_particles'):
                            self.celebration_particles.spawn_burst(self.width // 2, self.height // 2, count=30)
                        print(f"* Correct answer selected for Station {self.quiz_station_index}!")
                    else:
                        self.first_attempt_correct[self.current_question_index + 1] = False
                        self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
                        
                        if hasattr(self.main_menu, 'audio_manager'):
                            self.main_menu.audio_manager.play_sfx("wrong")
                        if self.station_attempts[self.quiz_station_index] < 2:
                            # 1st wrong attempt: Give player 1 more try
                            self.quiz_state = 2
                            print(f"[FAIL] Incorrect answer selected! (Attempt 1 of 2)")
                        else:
                            # 2nd wrong attempt: Out of tries! Recorded as wrong, but award emblem so game proceeds
                            self.quiz_state = 4
                            self.answered_stations.add(self.quiz_station_index)
                            print(f"[FAIL] Incorrect answer on 2nd try! Out of tries. Station {self.quiz_station_index} emblem awarded.")
                    
                    save_student_progress(self.main_menu)
                    break
 
        # State 2: Incorrect answer feedback click (1 try remaining)
        elif self.quiz_state == 2:
            box_w, box_h = 560, 290
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 225, 200, 42)
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
                self.trigger_award_animation(self.quiz_station_index)
                save_student_progress(self.main_menu)

        # State 4: Out of tries reveal screen click (Player gets key and continues)
        elif self.quiz_state == 4:
            box_w, box_h = 560, 260
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 200) // 2, box_y + 195, 200, 42)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 0
                self.trigger_award_animation(self.quiz_station_index)
                save_student_progress(self.main_menu)
                
        # State 5: Final speech click
        elif self.quiz_state == 5:
            # Guard against accidental click passthrough from the puzzle button
            if pygame.time.get_ticks() - getattr(self, 'final_dialog_open_time', 0) < 400:
                return
            box_w, box_h = 550, 300
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 210, 240, 42)
            if btn_rect.collidepoint(pos):
                if getattr(self, 'is_map12', False):
                    self.quiz_state = 0
                    self.raft_state = "ready_to_sail"
                    print("[BOAT] Bromen dismissed! Step onto the Lotus Raft to sail!")
                else:
                    self.quiz_state = 6
                save_student_progress(self.main_menu)
                print("[TUTORIAL] Quarter 4 evaluation completed!")

        # Bromen Proximity Dialogue click
        elif self.bromen_dialogue_state in [1, 2]:
            if hasattr(self, 'bromen_btn_rect') and self.bromen_btn_rect.collidepoint(pos):
                if self.bromen_dialogue_state == 1:
                    self.bromen_dialogue_state = 0
                    # Disable Bromen proximity check for 5 seconds so player can freely relocate
                    self.bromen_proximity_cooldown_end = pygame.time.get_ticks() + 5000
                else:
                    self.bromen_dialogue_state = 0
                    self.key_puzzle_active = True
                    self.emblem_puzzle_active = True
                    if getattr(self, 'is_map12', False):
                        self.init_addition_puzzle()
                    else:
                        self.init_key_puzzle()
                save_student_progress(self.main_menu)

        # Key / Addition Puzzle clicks
        elif self.key_puzzle_active or self.emblem_puzzle_active:
            if getattr(self, 'is_map12', False):
                if getattr(self, 'addition_is_correct', False) and hasattr(self, 'addition_continue_btn_rect'):
                    if self.addition_continue_btn_rect and self.addition_continue_btn_rect.collidepoint(pos):
                        self.key_puzzle_solved = True
                        self.emblem_puzzle_solved = True
                        self.key_puzzle_active = False
                        self.emblem_puzzle_active = False
                        self.final_dialog_open_time = pygame.time.get_ticks()
                        self.raft_state = "ready_to_sail"
                        self.quiz_state = 5  # Final dialogue from Bromen
                        self.bromen_dialogue_state = 3
                        self.npc_bromen_tile_x = 29
                        self.npc_bromen_tile_y = 8
                        self.npc_bromen_x = 29 * TILE_SIZE
                        self.npc_bromen_y = 8 * TILE_SIZE
                        if 'B' in self.npc_positions_data:
                            self.npc_positions_data['B'] = [(29, 8)]
                        print("[BOAT] Addition helm puzzle solved! Bromen untethered the Lotus Raft!")
                        return
                if hasattr(self, 'addition_reset_btn_rect') and self.addition_reset_btn_rect and self.addition_reset_btn_rect.collidepoint(pos):
                    self.reset_addition_puzzle()
                    return
            else:
                if getattr(self, 'key_puzzle_all_placed', False) and hasattr(self, 'key_puzzle_continue_btn_rect'):
                    if self.key_puzzle_continue_btn_rect and self.key_puzzle_continue_btn_rect.collidepoint(pos):
                        self.key_puzzle_solved = True
                        self.emblem_puzzle_solved = True
                        self.key_puzzle_active = False
                        self.emblem_puzzle_active = False
                        self.final_dialog_open_time = pygame.time.get_ticks()
                        self.open_dungeon_doors()
                        self.quiz_state = 5
                        self.bromen_dialogue_state = 3
                        return
                if hasattr(self, 'reset_btn_rect') and self.reset_btn_rect and self.reset_btn_rect.collidepoint(pos):
                    self.init_key_puzzle()

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = min(0.05, max(0.001, self.clock.tick(FPS) / 1000.0))
        self.frame_counter += 1

        if self.pause_menu.is_paused:
            return

        # Update celebration particles & victory report card
        if hasattr(self, 'celebration_particles'):
            self.celebration_particles.update(dt)
        if hasattr(self, 'victory_card') and self.victory_card.active:
            self.victory_card.update(dt)
            return

        # Update Map 12 water particles
        if getattr(self, 'is_map12', False):
            self.update_particles()

        # 10-Minute Stage Timer
        if not getattr(self, 'completed', False) and not self.time_up_dialog_active:
            self.stage_time_remaining = max(0.0, self.stage_time_remaining - dt)
            if self.stage_time_remaining <= 60.0 and not getattr(self, 'timer_warning_played', False):
                self.timer_warning_played = True
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("timer_warning")
            if self.stage_time_remaining <= 0.0:
                self.stage_time_remaining = 0.0
                self.time_up_dialog_active = True
                print("[TIME] Quarter 4 Time's Up!")

        if self.time_up_dialog_active:
            return

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
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            for num, pos in self.quiz_stations.items():
                is_answered = num in self.answered_stations
                if num == 5 and (6 not in self.quiz_stations):
                    is_answered = (5 in self.answered_stations) and (6 in self.answered_stations)
                
                if not is_answered:
                    npc_center_x = pos[0] * TILE_SIZE + TILE_SIZE // 2
                    npc_center_y = pos[1] * TILE_SIZE + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - npc_center_x, player_center_y - npc_center_y)
                    if dist < TILE_SIZE * 1.5:
                        if num == 5 and 5 in self.answered_stations and (6 not in self.quiz_stations):
                            self.quiz_station_index = 6
                            self.current_question_index = 5
                        else:
                            self.quiz_station_index = num
                            self.current_question_index = num - 1
                        self.quiz_state = 1
                        self.selected_choice_index = -1
                        print(f"[Bromen] Interacting with Station {self.quiz_station_index} NPC!")
                        break

        # Map 12: Lotus Raft sailing logic
        if getattr(self, 'is_map12', False):
            # Ready to sail once the helm lock puzzle with Guardian Bromen is solved
            if self.key_puzzle_solved and self.raft_state == "docked_west":
                self.raft_state = "ready_to_sail"
                print("[WAVE] Helm lock solved! Lotus Raft is untethered and ready to sail!")

            # Check if player is near the Lotus Raft when ready to sail
            if self.raft_state == "ready_to_sail":
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                raft_center_x = self.raft_x + TILE_SIZE // 2
                raft_center_y = self.raft_y + TILE_SIZE // 2
                dist_to_raft = math.hypot(player_center_x - raft_center_x, player_center_y - raft_center_y)
                if dist_to_raft < TILE_SIZE * 1.5:
                    self.raft_state = "sailing"
                    self.raft_passenger = True
                    print("[BOAT] Player hopped on the Lotus Raft! Sailing down the canal rapids!")
                    if hasattr(self, 'sound_snap') and self.sound_snap:
                        try:
                            self.sound_snap.play()
                        except Exception:
                            pass

            # Update sailing animation and movement
            if self.raft_state == "sailing":
                self.raft_x += self.raft_speed * dt
                self.player_x = self.raft_x
                self.player_y = self.raft_y
                # Add wake foam behind the raft
                if random.random() < 0.65:
                    self.raft_wake_particles.append({
                        'x': self.raft_x - 12 + random.uniform(-4, 4),
                        'y': self.raft_y + 16 + random.uniform(-6, 6),
                        'vx': random.uniform(-1.2, -0.3),
                        'vy': random.uniform(-0.6, 0.6),
                        'radius': random.uniform(3, 6),
                        'life': 1.0
                    })
                # Check arrival at East Dock
                if self.raft_x >= self.raft_target_x:
                    self.raft_x = self.raft_target_x
                    self.raft_state = "docked_east"
                    self.raft_passenger = False
                    self.player_x = 37.0 * TILE_SIZE
                    self.player_y = 9.0 * TILE_SIZE
                    self.quiz_state = 6  # Unlock exit portal!
                    self.open_dungeon_doors()
                    self.save_quarter4_game_result()
                    print("[WIN] Lotus Raft docked at East Pier! Portal unlocked!")
                    if hasattr(self, 'sound_correct') and self.sound_correct:
                        try:
                            self.sound_correct.play()
                        except Exception:
                            pass

        elif len(self.answered_stations) >= 6 and not self.npc_bromen_found and self.quiz_state == 0:
            self.quiz_state = 6
            self.open_dungeon_doors()
            self.save_quarter4_game_result()
            print("[WIN] All 6 Golden Keys collected! Exit portal unlocked!")

        # Proximity check for Bromen (Boat Guardian on Map 12, Final obstacle on other maps)
        now = pygame.time.get_ticks()
        if (self.quiz_state == 0 and 
            not (self.key_puzzle_active or self.emblem_puzzle_active) and 
            self.bromen_dialogue_state == 0 and 
            self.npc_bromen_found and 
            not self.key_puzzle_solved and
            now >= getattr(self, 'bromen_proximity_cooldown_end', 0)):
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            bromen_center_x = self.npc_bromen_x + TILE_SIZE // 2
            bromen_center_y = self.npc_bromen_y + TILE_SIZE // 2
            dist = math.hypot(player_center_x - bromen_center_x, player_center_y - bromen_center_y)
            if dist < TILE_SIZE * 1.5:
                if len(self.answered_stations) >= 6:
                    self.bromen_dialogue_state = 2  # Ready for Key Lock Block Puzzle
                    print(f"[Bromen] All 6 Sluices open! Interacting with Bromen! state={self.bromen_dialogue_state}")
                else:
                    self.bromen_dialogue_state = 1  # Not enough sluices open
                    print(f"[LOCKED] Bromen: Canal not full yet ({len(self.answered_stations)}/6)")

        # Update Bromen animation
        if self.npc_bromen_found and self.npc_bromen_sprites:
            self.npc_bromen_anim_timer += 1
            if self.npc_bromen_anim_timer >= 6:
                self.npc_bromen_anim_timer = 0
                self.npc_bromen_anim_frame = (self.npc_bromen_anim_frame + 1) % len(self.npc_bromen_sprites)

        # Update Key Lock Box Puzzle (or Addition Puzzle on Map 12)
        if self.key_puzzle_active or self.emblem_puzzle_active:
            if getattr(self, 'is_map12', False):
                self.update_addition_puzzle()
            else:
                self.update_key_puzzle()

        self.update_player_movement()
        self.check_portal_teleport_on_hold()

        for portal in self.portals:
            portal.update_animation()

        self.update_camera()

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        if self.quiz_state in [1, 2, 3, 4, 5] or self.key_puzzle_active or self.emblem_puzzle_active or self.bromen_dialogue_state in [1, 2] or (hasattr(self, 'player_block_timer') and self.player_block_timer > 0):
            self.anim_frame = 0
            return

        vx, vy = 0, 0
        current_speed = SPEED

        # Hand Gesture / Cursor Directional Controls (Pure Gesture Navigation)
        player_screen_x = (self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM
        player_screen_y = (self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM
        cursor_x, cursor_y = self.cursor_pos
        dx = cursor_x - player_screen_x
        dy = cursor_y - player_screen_y

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
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("footstep_stone")
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

            # For transparent floor props (fountains, statues, pots, pillars, braziers, chests, banners, doors), draw clean floor first
            if c in ["F", "*", "S", "C", "|", "R", "$", "H", "[", "]", "{", "}"]:
                floor_img = self.tile_images.get("G", self.fallback_tile)
                scaled_floor = pygame.transform.scale(floor_img, (scaled_size, scaled_size))
                self.screen.blit(scaled_floor, (screen_x, screen_y))
            # For lily pads on water, draw water first
            elif c == "L":
                water_img = self.tile_images.get("W", self.fallback_tile)
                scaled_water = pygame.transform.scale(water_img, (scaled_size, scaled_size))
                self.screen.blit(scaled_water, (screen_x, screen_y))

            image = self.tile_images.get(c, self.fallback_tile)

            # ONLY the door tiles are stretched (2 blocks in length, 1 block in width/thickness)
            if c == "[":
                # Left closed door: 2 blocks horizontally, 1 block vertically
                scaled_image = pygame.transform.scale(image, (scaled_size * 2, scaled_size))
                self.screen.blit(scaled_image, (screen_x, screen_y))
            elif c == "]":
                # Right closed door: 2 blocks horizontally, 1 block vertically, anchored on right wall
                scaled_image = pygame.transform.scale(image, (scaled_size * 2, scaled_size))
                self.screen.blit(scaled_image, (screen_x - scaled_size, screen_y))
            elif c == "{":
                # Left open door: 1 block horizontally, 2 blocks vertically along left wall
                scaled_image = pygame.transform.scale(image, (scaled_size, scaled_size * 2))
                self.screen.blit(scaled_image, (screen_x, screen_y - scaled_size))
            elif c == "}":
                # Right open door: 1 block horizontally, 2 blocks vertically along right wall
                scaled_image = pygame.transform.scale(image, (scaled_size, scaled_size * 2))
                self.screen.blit(scaled_image, (screen_x, screen_y - scaled_size))
            else:
                # ALL other standard tiles are strictly 1 block x 1 block
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

    def update_particles(self):
        # When all 6 stations answered on map12, spray particles from twin fountains at (22, 8) and (22, 10)
        if len(self.answered_stations) >= 6 and random.random() < 0.45:
            for fx, fy in [(22, 8), (22, 10)]:
                world_fx = fx * TILE_SIZE + TILE_SIZE // 2
                world_fy = fy * TILE_SIZE + TILE_SIZE // 2
                for _ in range(2):
                    self.water_particles.append({
                        'x': world_fx + random.uniform(-10, 10),
                        'y': world_fy - random.uniform(2, 6),
                        'vx': random.uniform(-1.5, 1.5),
                        'vy': random.uniform(-3.8, -1.8),
                        'color': random.choice([(56, 189, 248), (147, 197, 253), (255, 255, 255), (250, 204, 21)]),
                        'radius': random.uniform(2, 4),
                        'life': 1.0
                    })

        # Update existing particles
        alive_particles = []
        for p in self.water_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.12  # Gravity
            p['life'] -= 0.025
            if p['life'] > 0:
                alive_particles.append(p)
        self.water_particles = alive_particles

        # Update raft wake foam particles
        alive_wake = []
        for p in getattr(self, 'raft_wake_particles', []):
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.03
            if p['life'] > 0:
                alive_wake.append(p)
        self.raft_wake_particles = alive_wake

    def draw_canal_rapids(self):
        if not getattr(self, 'is_map12', False):
            return

        answered = len(self.answered_stations)
        flow_speed = 1.0 + (answered * 0.4)

        # Draw water rapids across the canal flume on row 9, cols 30 to 35
        for col in range(30, 36):
            sx = (col * TILE_SIZE - self.camera_x) * ZOOM
            sy = (9 * TILE_SIZE - self.camera_y) * ZOOM
            if not (-TILE_SIZE <= sx <= self.width + TILE_SIZE and -TILE_SIZE <= sy <= self.height + TILE_SIZE):
                continue

            streak_offset = (self.frame_counter * flow_speed * 1.5 + col * 12) % (TILE_SIZE * ZOOM)
            y_offset = (math.sin(self.frame_counter * 0.1 + col) + 1) * (TILE_SIZE * ZOOM * 0.35)

            line_len = int(14 * ZOOM)
            streak_x = sx + streak_offset
            streak_y = sy + y_offset

            alpha = min(180, 40 + answered * 22)
            streak_surf = pygame.Surface((line_len, max(2, int(2 * ZOOM))), pygame.SRCALPHA)
            streak_surf.fill((255, 255, 255, alpha))
            self.screen.blit(streak_surf, (streak_x - line_len // 2, streak_y))

            if answered >= 6:
                sparkle_pulse = (math.sin(self.frame_counter * 0.15 + col * 2) + 1) * 0.5
                if sparkle_pulse > 0.6:
                    sp_r = max(1, int(2 * ZOOM))
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(sx + 16 * ZOOM), int(sy + 12 * ZOOM)), sp_r)

    def draw_lotus_raft(self):
        if not getattr(self, 'is_map12', False):
            return

        rx = (self.raft_x - self.camera_x) * ZOOM
        ry = (self.raft_y - self.camera_y) * ZOOM

        if not (-80 <= rx <= self.width + 80 and -80 <= ry <= self.height + 80):
            return

        bob = math.sin(self.frame_counter * 0.12) * (3 * ZOOM)
        draw_y = ry + bob

        # 1. Trailing wake particles
        for p in getattr(self, 'raft_wake_particles', []):
            px = (p['x'] - self.camera_x) * ZOOM
            py = (p['y'] - self.camera_y) * ZOOM
            if 0 <= px <= self.width and 0 <= py <= self.height:
                alpha = int(200 * p['life'])
                pr = max(1, int(p['radius'] * ZOOM))
                wake_s = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
                pygame.draw.circle(wake_s, (255, 255, 255, alpha), (pr, pr), pr)
                pygame.draw.circle(wake_s, (147, 197, 253, alpha // 2), (pr, pr), pr + 1, 1)
                self.screen.blit(wake_s, (px - pr, py - pr))

        # 2. Water ripples around the hull
        hull_w = int(38 * ZOOM)
        hull_h = int(24 * ZOOM)
        cx = rx + (TILE_SIZE * ZOOM) // 2
        cy = draw_y + (TILE_SIZE * ZOOM) // 2

        ripple_w = hull_w + int((math.sin(self.frame_counter * 0.08) + 1) * 4 * ZOOM)
        ripple_h = hull_h + int((math.sin(self.frame_counter * 0.08) + 1) * 2 * ZOOM)
        ripple_surf = pygame.Surface((ripple_w + 4, ripple_h + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(ripple_surf, (255, 255, 255, 60), (2, 2, ripple_w, ripple_h), 2)
        self.screen.blit(ripple_surf, (cx - ripple_w // 2, cy - ripple_h // 2))

        # 3. Raft Wooden Hull
        raft_rect = pygame.Rect(cx - hull_w // 2, cy - hull_h // 2, hull_w, hull_h)
        shadow_rect = pygame.Rect(cx - hull_w // 2, cy - hull_h // 2 + int(3 * ZOOM), hull_w, hull_h)
        pygame.draw.rect(self.screen, (15, 23, 42, 160), shadow_rect, border_radius=int(6 * ZOOM))

        pygame.draw.rect(self.screen, (146, 64, 14), raft_rect, border_radius=int(6 * ZOOM))
        inner_rect = pygame.Rect(raft_rect.x + int(2 * ZOOM), raft_rect.y + int(2 * ZOOM),
                                 raft_rect.w - int(4 * ZOOM), raft_rect.h - int(4 * ZOOM))
        pygame.draw.rect(self.screen, (180, 83, 9), inner_rect, border_radius=int(4 * ZOOM))
        pygame.draw.rect(self.screen, (250, 204, 21), raft_rect, max(1, int(2 * ZOOM)), border_radius=int(6 * ZOOM))

        # 4. Lotus Flower Crest / Prow
        lotus_r = int(7 * ZOOM)
        pygame.draw.circle(self.screen, (244, 114, 182), (int(cx + hull_w // 2 - 4 * ZOOM), int(cy)), lotus_r)
        pygame.draw.circle(self.screen, (253, 224, 71), (int(cx + hull_w // 2 - 4 * ZOOM), int(cy)), int(lotus_r * 0.45))

        # 5. Lantern on Bow
        lantern_x = int(cx + hull_w // 2 - 2 * ZOOM)
        lantern_y = int(cy - 6 * ZOOM)
        glow_r = int(12 * ZOOM)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (253, 224, 71, 75), (glow_r, glow_r), glow_r)
        self.screen.blit(glow_surf, (lantern_x - glow_r, lantern_y - glow_r))
        pygame.draw.circle(self.screen, (255, 255, 255), (lantern_x, lantern_y), max(1, int(2 * ZOOM)))

        # 6. Boarding Banner Pill when ready to sail
        if self.raft_state == "ready_to_sail":
            prompt_font = pygame.font.SysFont("Comic Sans MS", int(11 * ZOOM), bold=True)
            prompt_text = "HOP ON THE RAFT!"
            p_surf = prompt_font.render(prompt_text, True, (15, 23, 42))
            pw = p_surf.get_width() + 14
            ph = p_surf.get_height() + 8

            b_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            b_surf.fill((250, 204, 21, 230))
            pygame.draw.rect(b_surf, (255, 255, 255), (0, 0, pw, ph), 2, border_radius=8)
            b_surf.blit(p_surf, (7, 4))

            prompt_y = cy - hull_h // 2 - ph - int(8 * ZOOM) + int(math.sin(self.frame_counter * 0.15) * 3 * ZOOM)
            self.screen.blit(b_surf, (cx - pw // 2, prompt_y))

    def draw_water_particles(self):
        if not getattr(self, 'is_map12', False):
            return
        for p in getattr(self, 'water_particles', []):
            sx = (p['x'] - self.camera_x) * ZOOM
            sy = (p['y'] - self.camera_y) * ZOOM
            if 0 <= sx <= self.width and 0 <= sy <= self.height:
                pr = max(1, int(p['radius'] * ZOOM))
                pygame.draw.circle(self.screen, p['color'], (int(sx), int(sy)), pr)

    # ============================================================
    # DRAW PLAYER
    # ============================================================
    def draw_player(self):
        screen_x = (self.player_x - self.camera_x) * ZOOM
        screen_y = (self.player_y - self.camera_y) * ZOOM

        if getattr(self, 'raft_passenger', False):
            bob = math.sin(self.frame_counter * 0.12) * (3 * ZOOM)
            screen_y += bob

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

        # Draw visible tiles using render_map (First pass: Floor and standard tiles, skipping doors and trees)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char not in ['T', '[', ']', '{', '}']:
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw 2-block wide doors on top of floor tiles
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char in ['[', ']', '{', '}']:
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Map 12 Canal Water Rapids
        self.draw_canal_rapids()

        # Draw Station Pedestal Rings on the ground
        if hasattr(self, 'quiz_stations'):
            for num, pos in self.quiz_stations.items():
                is_answered = num in self.answered_stations
                if num == 5 and (6 not in self.quiz_stations):
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
                if num == 5 and (6 not in self.quiz_stations):
                    is_answered = (5 in self.answered_stations) and (6 in self.answered_stations)

                if num in self.station_npcs and not is_answered and self.quiz_state < 6:
                    data = self.station_npcs[num]
                    frame = data["frames"][data["anim_frame"]]

                    # Shimmering water pedestal aura under water guardian
                    aura_w = int(TILE_SIZE * ZOOM * 1.3)
                    aura_h = int(TILE_SIZE * ZOOM * 0.6)
                    aura_surf = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)
                    pulse = math.sin(self.frame_counter * 0.1 + num) * 0.25 + 0.75
                    g_color = self.valve_colors[num - 1] if hasattr(self, 'valve_colors') and 1 <= num <= len(self.valve_colors) else (56, 189, 248)
                    pygame.draw.ellipse(aura_surf, (*g_color, int(45 * pulse)), (0, 0, aura_w, aura_h))
                    pygame.draw.ellipse(aura_surf, (255, 255, 255, int(70 * pulse)), (aura_w // 4, aura_h // 4, aura_w // 2, aura_h // 2))
                    ax = int((pos[0] * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM - aura_w) / 2)
                    ay = int((pos[1] * TILE_SIZE - self.camera_y) * ZOOM + TILE_SIZE * ZOOM * 0.65)
                    self.screen.blit(aura_surf, (ax, ay))

                    self.draw_npc_static(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, frame)

        # Draw Bromen
        if self.npc_bromen_found and self.npc_bromen_sprites:
            frame = self.npc_bromen_sprites[self.npc_bromen_anim_frame]
            self.draw_npc_static(self.npc_bromen_x, self.npc_bromen_y, frame)

        # Draw Lotus Raft before drawing the player (so player stands on deck)
        self.draw_lotus_raft()

        self.draw_player()
        self.draw_water_particles()

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

        # Draw Key Lock Box Puzzle overlay (or Addition Puzzle on Map 12)
        if self.key_puzzle_active or self.emblem_puzzle_active:
            if getattr(self, 'is_map12', False):
                self.draw_addition_puzzle()
            else:
                self.draw_key_puzzle()

        self.draw_ui()

        # Draw Golden Key award animation (flies down to Objectives HUD)
        self.draw_key_award_animation()

        # Draw 10-Minute Stage Timer HUD
        self.draw_stage_timer_hud()

        # Draw Time's Up modal dialog if timer expired
        if self.time_up_dialog_active:
            self.draw_time_up_dialog()

        # In-Game Universal Pause Button & Modal
        self.pause_menu.draw_button(self.cursor_pos)
        if self.pause_menu.is_paused:
            self.pause_menu.draw_modal(self.cursor_pos)

        # Draw Celebration Particles
        if hasattr(self, 'celebration_particles'):
            self.celebration_particles.draw(self.screen)

        # Draw 3-Star Victory Report Card Modal
        if hasattr(self, 'victory_card') and self.victory_card.active:
            self.victory_card.draw(self.cursor_pos)

    # ============================================================
    # DRAW UI
    # ============================================================
    def draw_ui(self):
        # Draw Objectives HUD Box at the bottom center of the screen
        if self.is_quiz_map:
            box_w, box_h = 390, 85
            box_x = (self.width - box_w) // 2
            box_y = self.height - box_h - 15
            
            # Translucent slate blue background
            bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            bg_surf.fill((16, 32, 44, 225))
            self.screen.blit(bg_surf, (box_x, box_y))
            
            # Border: Cyan/Gold when exploring, Emerald Green when complete
            border_color = (0, 210, 230) if self.quiz_state < 6 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_w, box_h), 2, border_radius=10)
            
            # Header title in Gold
            title_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
            header_title = "TEMPLE AQUEDUCT & LOTUS RAFT" if getattr(self, 'is_map12', False) else "WATER TEMPLE OBJECTIVES"
            title_surf = title_font.render(header_title, True, (255, 215, 0))
            self.screen.blit(title_surf, (box_x + 15, box_y + 8))
            
            if getattr(self, 'is_map12', False):
                # 6 Glowing Circular Sluice Pips
                pip_r = 6
                pip_spacing = 8
                start_pip_x = box_x + box_w - 20 - (6 * (pip_r * 2 + pip_spacing) - pip_spacing)
                for s_idx in range(1, 7):
                    px = start_pip_x + (s_idx - 1) * (pip_r * 2 + pip_spacing) + pip_r
                    py = box_y + 15
                    is_done = s_idx in self.answered_stations
                    color = self.valve_colors[s_idx - 1]
                    if is_done:
                        pygame.draw.circle(self.screen, (*color, 90), (px, py), pip_r + 3)
                        pygame.draw.circle(self.screen, color, (px, py), pip_r)
                        pygame.draw.circle(self.screen, (255, 255, 255), (px - 2, py - 2), 2)
                    else:
                        pygame.draw.circle(self.screen, (30, 45, 60), (px, py), pip_r)
                        pygame.draw.circle(self.screen, (70, 90, 110), (px, py), pip_r, 1)
            else:
                # 6 Segmented Progress Pips for Golden Keys (Standard Map 10/11)
                pip_w, pip_h = 16, 8
                pip_spacing = 5
                start_pip_x = box_x + box_w - 15 - (6 * (pip_w + pip_spacing) - pip_spacing)
                for s_idx in range(1, 7):
                    px = start_pip_x + (s_idx - 1) * (pip_w + pip_spacing)
                    py = box_y + 11
                    is_done = s_idx in self.answered_stations
                    pip_color = (250, 204, 21) if is_done else (40, 60, 75)
                    pygame.draw.rect(self.screen, pip_color, (px, py, pip_w, pip_h), border_radius=3)
                    pygame.draw.rect(self.screen, (255, 255, 255) if is_done else (20, 35, 45), (px, py, pip_w, pip_h), 1, border_radius=3)
            
            # Details font
            item_font = pygame.font.SysFont("Comic Sans MS", 12)
            
            q_count = len(self.answered_stations)
            if getattr(self, 'is_map12', False):
                obj1 = f"- Canal Water Sluices: {q_count}/6 Opened"
                obj1_color = (255, 255, 255) if q_count < 6 else (34, 197, 94)
                obj1_surf = item_font.render(obj1, True, obj1_color)
                self.screen.blit(obj1_surf, (box_x + 15, box_y + 30))
                
                if q_count < 6:
                    obj2 = f"- Water Canal: {q_count}/6 Full (Open all 6 to fill canal)"
                    obj2_color = (244, 63, 94)
                elif not self.key_puzzle_solved:
                    obj2 = "- Canal Full! Talk to Guardian Bromen at dock to unlock raft!"
                    obj2_color = (250, 204, 21)
                elif self.raft_state == "ready_to_sail":
                    obj2 = "- Raft Untethered! Walk onto Lotus Raft to sail!"
                    obj2_color = (34, 197, 94)
                elif self.raft_state == "sailing":
                    obj2 = "- Sailing across rapids to Portal Island!"
                    obj2_color = (56, 189, 248)
                else:
                    obj2 = "- Arrived! Step into the Portal to finish Quarter 4!"
                    obj2_color = (34, 197, 94)
                obj2_surf = item_font.render(obj2, True, obj2_color)
                self.screen.blit(obj2_surf, (box_x + 15, box_y + 52))
            else:
                obj1 = f"- Golden Keys: {q_count}/6 collected"
                obj1_color = (255, 255, 255) if q_count < 6 else (34, 197, 94)
                obj1_surf = item_font.render(obj1, True, obj1_color)
                self.screen.blit(obj1_surf, (box_x + 15, box_y + 30))
                
                if len(self.answered_stations) < 6:
                    obj2 = "- Doors & Portal: LOCKED (Collect all 6 Golden Keys)"
                    obj2_color = (244, 63, 94)
                elif self.quiz_state < 6:
                    obj2 = "- Keys Gathered! Approach Bromen to open double doors" if self.npc_bromen_found else "- All 6 Keys Gathered! Step into portal to finish"
                    obj2_color = (250, 204, 21)
                else:
                    obj2 = "- Double Doors Open! Step into portal to finish" if self.npc_bromen_found else "- Portal Unlocked! Step into portal to finish"
                    obj2_color = (34, 197, 94)
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
                f"Goal: Reach the {self.goal_portal_direction} portal >> Return to town",
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
        # Allow LoL camera to process middle mouse drag or Spacebar recentering
        self.lol_camera.handle_event(event)

        if hasattr(self, 'victory_card') and self.victory_card.active:
            if self.victory_card.handle_event(event):
                return "blocked"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                res = self.victory_card.handle_click(event.pos)
                if res:
                    return "blocked"

        if self.pause_menu.handle_event(event):
            return "blocked"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.main_menu:
                    from db.save_system import show_saving_and_exit
                    show_saving_and_exit(self.main_menu)
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.check_portal_teleport_on_hold():
                    return "back"
                elif self.quiz_state == 0:
                    self.lol_camera.recenter()
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.cursor_pos = event.pos
            self.trigger_click(event.pos)
            
            if (self.key_puzzle_active or self.emblem_puzzle_active) and not (self.key_puzzle_solved or self.emblem_puzzle_solved):
                if getattr(self, 'is_map12', False):
                    if not getattr(self, 'addition_is_correct', False):
                        for piece in reversed(getattr(self, 'addition_pieces', [])):
                            piece_rect = pygame.Rect(piece["x"], piece["y"], piece["w"], piece["h"])
                            if piece_rect.collidepoint(event.pos):
                                self.dragged_addition_piece = piece
                                self.drag_offset_x = piece["x"] - event.pos[0]
                                self.drag_offset_y = piece["y"] - event.pos[1]
                                break
                else:
                    for piece in self.key_puzzle_pieces:
                        if not piece["is_placed"]:
                            piece_rect = pygame.Rect(piece["x"], piece["y"], 48, 92)
                            if piece_rect.collidepoint(event.pos):
                                self.dragged_key = piece
                                self.drag_offset_x = piece["x"] - event.pos[0]
                                self.drag_offset_y = piece["y"] - event.pos[1]
                                break
                            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if getattr(self, 'is_map12', False) and getattr(self, 'dragged_addition_piece', None):
                self.drop_addition_piece()
            elif (self.key_puzzle_active or self.emblem_puzzle_active) and self.dragged_key:
                now = pygame.time.get_ticks()
                key_center_x = self.dragged_key["x"] + 24
                key_center_y = self.dragged_key["y"] + 46
                
                target_slot = None
                for slot in self.key_puzzle_slots:
                    if not slot["is_filled"]:
                        dist = math.hypot(key_center_x - slot["target_x"], key_center_y - slot["target_y"])
                        if dist < 55:
                            target_slot = slot
                            break
                            
                if target_slot:
                    self.dragged_key["x"] = target_slot["target_x"] - 19
                    self.dragged_key["y"] = target_slot["target_y"] - 54
                    self.dragged_key["is_placed"] = True
                    self.dragged_key["slot_id"] = target_slot["id"]
                    self.dragged_key["inserting"] = True
                    self.dragged_key["insert_start_time"] = now
                    self.dragged_key["turning"] = False
                    self.dragged_key["turn_angle"] = 0.0
                    target_slot["is_filled"] = True
                    target_slot["key_id"] = self.dragged_key["id"]
                else:
                    self.dragged_key["x"] = self.dragged_key["deck_x"]
                    self.dragged_key["y"] = self.dragged_key["deck_y"]
                self.dragged_key = None
                
        elif event.type == pygame.MOUSEMOTION:
            self.cursor_pos = event.pos
            if getattr(self, 'is_map12', False) and getattr(self, 'dragged_addition_piece', None):
                self.dragged_addition_piece["x"] = event.pos[0] + self.drag_offset_x
                self.dragged_addition_piece["y"] = event.pos[1] + self.drag_offset_y
            elif (self.key_puzzle_active or self.emblem_puzzle_active) and self.dragged_key:
                self.dragged_key["x"] = event.pos[0] + self.drag_offset_x
                self.dragged_key["y"] = event.pos[1] + self.drag_offset_y
                
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
        npc_data = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = npc_data.get("name", "Water Guardian")
        speaker_title = npc_data.get("title", "")

        speaker_surf = speaker_font.render(speaker_name, True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 16))

        if speaker_title:
            sub_font = pygame.font.SysFont("Comic Sans MS", 12)
            sub_surf = sub_font.render(speaker_title, True, (148, 163, 184))
            self.screen.blit(sub_surf, (box_x + 25, box_y + 40))
            pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 58), (box_x + 240, box_y + 58), 2)
        else:
            pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 180, box_y + 48), 2)

        # Draw animated avatar in top right corner of dialog
        if "frames" in npc_data and npc_data["frames"]:
            avatar = pygame.transform.scale(npc_data["frames"][npc_data.get("anim_frame", 0)], (44, 44))
            pygame.draw.circle(self.screen, (30, 58, 138), (box_x + box_w - 45, box_y + 35), 24)
            pygame.draw.circle(self.screen, (56, 189, 248), (box_x + box_w - 45, box_y + 35), 24, 2)
            self.screen.blit(avatar, (box_x + box_w - 67, box_y + 13))

        q_data = self.quiz_questions[self.current_question_index]
        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        wrapped_q = self.wrap_text(q_data["question"], q_font, box_w - 50)
        
        y_text = box_y + 68
        for line in wrapped_q:
            txt_surf = q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 22

        button_w, button_h = 500, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 130
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

        box_w, box_h = 560, 290
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=12)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=12)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        npc_data = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = npc_data.get("name", "Water Guardian")
        speaker_surf = speaker_font.render(speaker_name, True, (239, 68, 68))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 16))

        # Avatar in dialog
        if "frames" in npc_data and npc_data["frames"]:
            avatar = pygame.transform.scale(npc_data["frames"][npc_data.get("anim_frame", 0)], (38, 38))
            pygame.draw.circle(self.screen, (69, 10, 10), (box_x + box_w - 45, box_y + 35), 22)
            pygame.draw.circle(self.screen, (239, 68, 68), (box_x + box_w - 45, box_y + 35), 22, 2)
            self.screen.blit(avatar, (box_x + box_w - 64, box_y + 16))

        q_font = pygame.font.SysFont("Comic Sans MS", 15)
        msg_surf1 = q_font.render("Hmm, that is not quite correct.", True, (255, 255, 255))
        msg_surf2 = q_font.render("You have 1 try remaining! Think carefully.", True, (255, 215, 0))
        self.screen.blit(msg_surf1, (box_x + 25, box_y + 48))
        self.screen.blit(msg_surf2, (box_x + 25, box_y + 72))

        # Pedagogical Educational Hint Box
        from core.hints import get_educational_hint
        current_q = self.quiz_questions[self.current_question_index] if self.current_question_index < len(self.quiz_questions) else {}
        q_text = current_q.get("question", "")
        hint_text = get_educational_hint("quarter4", q_text)

        hint_box = pygame.Rect(box_x + 20, box_y + 104, box_w - 40, 105)
        pygame.draw.rect(self.screen, (30, 41, 59), hint_box, border_radius=8)
        pygame.draw.rect(self.screen, (245, 158, 11), hint_box, 1, border_radius=8)

        hint_title_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        hint_body_font = pygame.font.SysFont("Comic Sans MS", 13)
        h_title = hint_title_font.render("💡 Pedagogical Hint:", True, (255, 215, 0))
        self.screen.blit(h_title, (hint_box.x + 12, hint_box.y + 6))

        # Text wrap
        words = hint_text.split(" ")
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if hint_body_font.size(" ".join(cur))[0] > (hint_box.width - 24):
                cur.pop()
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))

        hy = hint_box.y + 30
        for hl in lines[:3]:
            h_surf = hint_body_font.render(hl, True, (241, 245, 249))
            self.screen.blit(h_surf, (hint_box.x + 12, hy))
            hy += 22

        button_w, button_h = 200, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 225
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
        npc_data = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = npc_data.get("name", "Water Guardian")
        speaker_surf = speaker_font.render(speaker_name, True, (245, 158, 11))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 15))

        # Avatar in dialog
        if "frames" in npc_data and npc_data["frames"]:
            avatar = pygame.transform.scale(npc_data["frames"][npc_data.get("anim_frame", 0)], (38, 38))
            pygame.draw.circle(self.screen, (69, 36, 6), (box_x + box_w - 45, box_y + 35), 22)
            pygame.draw.circle(self.screen, (245, 158, 11), (box_x + box_w - 45, box_y + 35), 22, 2)
            self.screen.blit(avatar, (box_x + box_w - 64, box_y + 16))

        q_data = self.quiz_questions[self.current_question_index]
        correct_choice_text = q_data["choices"][q_data["correct"]]

        q_font = pygame.font.SysFont("Comic Sans MS", 15)
        msg1 = q_font.render(f"Out of tries! The correct answer was: {correct_choice_text}", True, (255, 255, 255))
        if getattr(self, 'is_map12', False):
            msg2 = q_font.render("The Aqueduct Sluice still opened so your quest can continue!", True, (255, 215, 0))
        else:
            msg2 = q_font.render("You still received the Golden Key so your quest can continue!", True, (255, 215, 0))
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
        npc_data = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = npc_data.get("name", "Water Guardian")
        speaker_surf = speaker_font.render(speaker_name, True, (22, 163, 74))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        # Avatar in dialog
        if "frames" in npc_data and npc_data["frames"]:
            avatar = pygame.transform.scale(npc_data["frames"][npc_data.get("anim_frame", 0)], (38, 38))
            pygame.draw.circle(self.screen, (20, 83, 45), (box_x + box_w - 45, box_y + 35), 22)
            pygame.draw.circle(self.screen, (34, 197, 94), (box_x + box_w - 45, box_y + 35), 22, 2)
            self.screen.blit(avatar, (box_x + box_w - 64, box_y + 16))

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

        box_w, box_h = 560, 300
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=8)

        speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        if getattr(self, 'is_map12', False):
            speaker_name = "Guardian Bromen (Lotus Raft Guardian)"
            speech_lines = [
                "Splendid addition, young voyager! The helm's rune equation is restored!",
                "The Lotus Raft is untethered and floating on the rapids!",
                "Walk onto the pier and hop aboard the raft to sail to the portal!"
            ]
            btn_label = "Step Aboard the Raft"
        else:
            speaker_name = "Guardian Bromen"
            speech_lines = [
                "Outstanding work, student! The Ancient Lock Block has been solved.",
                "The heavy double doors have swung open!",
                "Proceed through the doorway and step into the portal to finish."
            ]
            btn_label = "Pass Through Doors"

        speaker_surf = speaker_font.render(speaker_name, True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + speaker_surf.get_width() + 25, box_y + 48), 2)

        q_font = pygame.font.SysFont("Comic Sans MS", 15)
        y_text = box_y + 65
        for line in speech_lines:
            txt_surf = q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 24

        button_w, button_h = 240, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 210
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (218, 165, 32)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect, 3, border_radius=12)

        c_surf = speaker_font.render(btn_label, True, (255, 255, 255) if not is_hovered else (0, 0, 0))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def generate_plain_key_surface(self, width, height):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        
        gold_fill = (250, 204, 21)
        gold_border = (180, 83, 9)
        
        w, h = width, height
        ring_r = int(w * 0.38)
        ring_center = (w // 2, int(h * 0.22))
        
        # Outer Ring
        pygame.draw.circle(surf, gold_border, ring_center, ring_r)
        pygame.draw.circle(surf, gold_fill, ring_center, ring_r - 3)
        # Inner Ring Cutout
        inner_r = int(ring_r * 0.48)
        pygame.draw.circle(surf, gold_border, ring_center, inner_r)
        pygame.draw.circle(surf, (0, 0, 0, 0), ring_center, inner_r - 2)
        
        # Stem
        stem_w = int(w * 0.16)
        stem_top = ring_center[1] + int(ring_r * 0.6)
        stem_bottom = int(h * 0.88)
        stem_rect = pygame.Rect(w // 2 - stem_w // 2, stem_top, stem_w, stem_bottom - stem_top)
        pygame.draw.rect(surf, gold_border, (stem_rect.x - 2, stem_rect.y, stem_rect.w + 4, stem_rect.h + 2), border_radius=3)
        pygame.draw.rect(surf, gold_fill, stem_rect, border_radius=2)
        
        # Teeth
        tooth_w = int(w * 0.28)
        tooth_h = int(h * 0.08)
        pygame.draw.rect(surf, gold_border, (w // 2, stem_bottom - tooth_h * 2 - 2, tooth_w + 2, tooth_h + 4), border_radius=2)
        pygame.draw.rect(surf, gold_fill, (w // 2, stem_bottom - tooth_h * 2, tooth_w, tooth_h), border_radius=2)
        
        pygame.draw.rect(surf, gold_border, (w // 2, stem_bottom - tooth_h + 2, tooth_w - 4 + 2, tooth_h - 2 + 4), border_radius=2)
        pygame.draw.rect(surf, gold_fill, (w // 2, stem_bottom - tooth_h + 4, tooth_w - 4, tooth_h - 2), border_radius=2)
        
        return surf

    def trigger_award_animation(self, key_idx=None):
        self.award_anim_active = True
        self.award_anim_start_time = pygame.time.get_ticks()
        self.award_key_index = key_idx if key_idx is not None else self.quiz_station_index
        if hasattr(self, 'sound_snap') and self.sound_snap:
            try:
                self.sound_snap.play()
            except Exception:
                pass
        elif hasattr(self, 'sound_correct') and self.sound_correct:
            try:
                self.sound_correct.play()
            except Exception:
                pass

    def draw_key_award_animation(self):
        # Draw Golden Key award animation (flies down to bottom-center Water Temple Objectives HUD)
        if not self.award_anim_active:
            return

        elapsed = (pygame.time.get_ticks() - self.award_anim_start_time) / 1000.0
        if elapsed < 0:
            return

        if elapsed > 1.3:
            self.award_anim_active = False
            return

        # Sprite to draw: Golden Key
        sprite_to_draw = getattr(self, 'award_key_sprite', None)
        if sprite_to_draw is None:
            sprite_to_draw = getattr(self, 'puzzle_key_img', None)

        key_num = getattr(self, 'award_key_index', self.quiz_station_index)
        total_keys = len(self.answered_stations)

        if getattr(self, 'is_map12', False):
            valve_name = self.valve_names[key_num - 1] if 1 <= key_num <= len(self.valve_names) else "Aqueduct Sluice"
            if total_keys < 6:
                banner_text = f"{valve_name.upper()} OPENED! ({total_keys}/6) - Canal Filling with Water!"
            else:
                banner_text = f"ALL 6 SLUICES OPEN! (6/6) - THE LOTUS RAFT IS READY TO SAIL!"
            valve_color = self.valve_colors[key_num - 1] if 1 <= key_num <= len(self.valve_colors) else (56, 189, 248)
        else:
            banner_text = f"NEW GOLDEN KEY #{key_num} COLLECTED! ({total_keys}/6)"

        # Target bottom center Objectives HUD position
        box_w, box_h = 370, 85
        target_x = self.width // 2
        target_y = self.height - box_h // 2 - 15

        if elapsed <= 0.4:
            # Phase 1: Pop up in center of screen with scale up effect
            scale = min(1.3, 1.3 * (elapsed / 0.4))
            alpha = 255
            x = self.width // 2
            y = self.height // 2 - 20
        else:
            # Phase 2: Glide smoothly down to Objectives HUD box and fade into it
            t = min(1.0, (elapsed - 0.4) / 0.9)
            ease_t = t * t * (3 - 2 * t)
            scale = 1.3 * (1.0 - t * 0.75)
            alpha = int(255 * (1.0 - t * 0.9))
            x = self.width // 2
            start_y = self.height // 2 - 20
            y = start_y + ease_t * (target_y - start_y)

        # Draw Golden Aura / Glow behind the key or Radiant Sluice Emblem on Map 12
        if getattr(self, 'is_map12', False):
            pr = int(36 * scale)
            if pr > 0:
                try:
                    glow_r = int(pr * 1.8)
                    glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    g_alpha = int(min(170, alpha * 0.7))
                    pygame.draw.circle(glow_surf, (*valve_color, g_alpha), (glow_r, glow_r), glow_r)
                    pygame.draw.circle(glow_surf, (255, 255, 255, min(230, g_alpha + 50)), (glow_r, glow_r), int(glow_r * 0.5))
                    self.screen.blit(glow_surf, (x - glow_r, y - glow_r))

                    # Outer water droplet / sluice jewel
                    pearl_surf = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
                    pygame.draw.circle(pearl_surf, valve_color, (pr, pr), pr)
                    pygame.draw.circle(pearl_surf, (255, 255, 255), (pr, pr), pr, max(2, int(2 * scale)))
                    pygame.draw.circle(pearl_surf, (255, 255, 255), (int(pr * 0.7), int(pr * 0.7)), max(2, int(pr * 0.3)))
                    if alpha < 255:
                        pearl_surf.set_alpha(alpha)
                    self.screen.blit(pearl_surf, (x - pr, y - pr))
                except Exception as e:
                    print(f"Error drawing award emblem: {e}")
        elif sprite_to_draw:
            base_w, base_h = 95, 210
            w = int(base_w * scale)
            h = int(base_h * scale)
            if w > 0 and h > 0:
                try:
                    glow_radius = int(max(w, h) * 0.6)
                    if glow_radius > 0:
                        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                        glow_alpha = int(min(170, alpha * 0.65))
                        pygame.draw.circle(glow_surf, (250, 204, 21, glow_alpha), (glow_radius, glow_radius), glow_radius)
                        pygame.draw.circle(glow_surf, (255, 255, 255, min(220, glow_alpha + 40)), (glow_radius, glow_radius), int(glow_radius * 0.45))
                        self.screen.blit(glow_surf, (x - glow_radius, y - glow_radius))

                    scaled_key = pygame.transform.smoothscale(sprite_to_draw, (w, h))
                    if alpha < 255:
                        scaled_key.set_alpha(alpha)
                    self.screen.blit(scaled_key, (x - w // 2, y - h // 2))
                except Exception as e:
                    print(f"Error drawing award key: {e}")

        # Draw Banner Pill during initial reveal (Phase 1)
        if elapsed <= 0.5:
            banner_alpha = 255 if elapsed <= 0.4 else int(255 * (1.0 - (elapsed - 0.4) / 0.1))
            award_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
            text_surf = award_font.render(banner_text, True, (255, 215, 0))
            
            bw = text_surf.get_width() + 24
            bh = text_surf.get_height() + 14
            bg_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            bg_surf.fill((15, 23, 42, int(banner_alpha * 0.85)))
            pygame.draw.rect(bg_surf, (255, 215, 0, banner_alpha), (0, 0, bw, bh), 2, border_radius=12)
            
            bx = x - bw // 2
            by = y - (int(210 * scale) // 2) - bh - 10
            self.screen.blit(bg_surf, (bx, by))
            
            if banner_alpha < 255:
                text_surf.set_alpha(banner_alpha)
            self.screen.blit(text_surf, (bx + 12, by + 7))

    def load_key_puzzle_assets(self):
        self.puzzle_block_img = None
        self.puzzle_key_img = None
        self.award_key_sprite = None
        
        doorkeys_dir = os.path.join(self.OBJECTS_PATH, "quarter4tiles", "Doorkeys")
        block_path = os.path.join(doorkeys_dir, "block_hires.png")
        if not os.path.exists(block_path):
            block_path = os.path.join(doorkeys_dir, "block.png")
            
        if os.path.exists(block_path):
            try:
                img = pygame.image.load(block_path).convert_alpha()
                self.puzzle_block_img = pygame.transform.smoothscale(img, (470, 470))
            except Exception as e:
                print(f"Error loading block image: {e}")
                
        key_path = os.path.join(doorkeys_dir, "key_hires.png")
        if not os.path.exists(key_path):
            key_path = os.path.join(doorkeys_dir, "key.png")
            
        if os.path.exists(key_path):
            try:
                raw_k = pygame.image.load(key_path).convert_alpha()
                self.award_key_sprite = raw_k
                self.puzzle_key_img = pygame.transform.smoothscale(raw_k, (44, 105))
            except Exception as e:
                print(f"Error loading key image: {e}")

        # Load inserted key handle sprite (only handle is visible when inserted into keyhole)
        self.puzzle_key_handle_img = None
        handle_path = os.path.join(doorkeys_dir, "key_handle_hires.png")
        if not os.path.exists(handle_path):
            handle_path = os.path.join(doorkeys_dir, "key_handle.png")
        if os.path.exists(handle_path):
            try:
                raw_h = pygame.image.load(handle_path).convert_alpha()
                self.puzzle_key_handle_img = pygame.transform.smoothscale(raw_h, (76, 76))
            except Exception as e:
                print(f"Error loading key handle image: {e}")

        if self.award_key_sprite is None:
            self.award_key_sprite = self.generate_plain_key_surface(100, 220)

    # Legacy alias
    def load_emblem_puzzle_assets(self):
        self.load_key_puzzle_assets()

    def load_puzzle_sounds(self):
        self.sound_correct = None
        self.sound_snap = None
        try:
            am = getattr(self.main_menu, 'audio_manager', None) if hasattr(self, 'main_menu') else None
            if not am:
                from core.audio_manager import audio_manager
                am = audio_manager

            if am:
                self.sound_correct = am.get_sound("correct")
                self.sound_snap = am.get_sound("snap")
        except Exception as e:
            print(f"Sound load warning: {e}")

    def init_key_puzzle(self):
        self.key_puzzle_pieces = []
        self.key_puzzle_slots = []
        self.dragged_key = None
        self.dragged_emblem = None
        self.key_puzzle_solved = False
        self.key_puzzle_solved_time = 0
        self.key_puzzle_all_placed = False
        self.all_placed_start_time = 0
        self.keys_turning_started = False
        
        box_w, box_h = 820, 560
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        
        block_x = box_x + 30
        block_y = box_y + 45
        block_w, block_h = 470, 470
        
        # 6 Keyhole slots (2 rows of 3 columns) precisely aligned to the front-view brass keyholes
        slot_rel = [
            (0.285, 0.347), (0.500, 0.348), (0.708, 0.347),
            (0.285, 0.663), (0.499, 0.663), (0.708, 0.664)
        ]
        
        for idx, (rx, ry) in enumerate(slot_rel):
            sx = block_x + int(rx * block_w)
            sy = block_y + int(ry * block_h)
            self.key_puzzle_slots.append({
                "id": idx,
                "target_x": sx,
                "target_y": sy,
                "is_filled": False,
                "key_id": None
            })
            
        deck_x = box_x + 525
        deck_y = box_y + 45
        deck_w = 265
        deck_h = 470
        
        num_keys = min(6, len(self.answered_stations))
        if num_keys < 6 and self.bromen_dialogue_state >= 2:
            num_keys = 6
            
        for i in range(num_keys):
            row = i // 2
            col = i % 2
            px = deck_x + 38 + col * 105
            py = deck_y + 50 + row * 125
            
            self.key_puzzle_pieces.append({
                "id": i,
                "x": px,
                "y": py,
                "deck_x": px,
                "deck_y": py,
                "is_placed": False,
                "slot_id": None,
                "turn_angle": 0.0,
                "turning": False,
                "turn_start_time": 0
            })

    # Legacy alias
    def init_emblem_puzzle(self):
        self.init_key_puzzle()

    def open_dungeon_doors(self):
        """Transition closed doors '[' and ']' on the map to open doors '{' and '}', and make them walkable."""
        doors_opened = 0
        new_game_map = []
        for r_idx, row in enumerate(self.game_map):
            row_chars = list(row)
            for c_idx, ch in enumerate(row_chars):
                if ch == '[':
                    row_chars[c_idx] = '{'
                    doors_opened += 1
                elif ch == ']':
                    row_chars[c_idx] = '}'
                    doors_opened += 1
            new_game_map.append("".join(row_chars))
        self.game_map = new_game_map

        new_render_map = []
        for r_idx, row in enumerate(self.render_map):
            row_chars = list(row)
            for c_idx, ch in enumerate(row_chars):
                if ch == '[':
                    row_chars[c_idx] = '{'
                elif ch == ']':
                    row_chars[c_idx] = '}'
            new_render_map.append("".join(row_chars))
        self.render_map = new_render_map

        # Make open doors walkable
        self.WALKABLE_TILES.update({"{", "}", "G", "P"})
        print(f"[DOOR] Dungeon double doors unlocked and swung open! ({doors_opened} panels opened)")

    def update_key_puzzle(self):
        if not (self.key_puzzle_active or getattr(self, 'emblem_puzzle_active', False)):
            return
            
        now = pygame.time.get_ticks()
        
        # Update key insertion and turning animations for each placed key
        for piece in self.key_puzzle_pieces:
            if piece.get("inserting", False):
                elapsed = now - piece["insert_start_time"]
                progress = min(1.0, elapsed / 350.0)
                piece["insert_progress"] = progress
                if progress >= 1.0:
                    piece["inserting"] = False
                    piece["turning"] = True
                    piece["turn_start_time"] = now
                    piece["turn_angle"] = 0.0
                    if self.sound_snap:
                        try:
                            self.sound_snap.play()
                        except Exception:
                            pass
            elif piece.get("turning", False):
                elapsed = now - piece["turn_start_time"]
                progress = min(1.0, elapsed / 450.0)
                ease = 1.0 - (1.0 - progress) * (1.0 - progress)
                piece["turn_progress"] = ease
                piece["turn_angle"] = 90.0 * ease
                if progress >= 1.0:
                    piece["turning"] = False
                    piece["turn_progress"] = 1.0
                    piece["turn_angle"] = 90.0
                    if self.sound_snap:
                        try:
                            self.sound_snap.play()
                        except Exception:
                            pass
            
        # Check if all 6 keys are placed, inserted, and turned
        if len(self.key_puzzle_pieces) == 6 and all(p.get("is_placed", False) and not p.get("inserting", False) and not p.get("turning", False) for p in self.key_puzzle_pieces):
            if self.key_puzzle_solved_time == 0:
                self.key_puzzle_solved_time = now
                self.key_puzzle_all_placed = True
                if self.sound_correct:
                    try:
                        self.sound_correct.play()
                    except Exception:
                        pass
            else:
                self.key_puzzle_all_placed = True
                    
        # Track gesture fist coordinates if hand is active
        if self.hand_detected and self.fist_closed:
            if not self.dragged_key:
                for piece in self.key_puzzle_pieces:
                    if not piece["is_placed"]:
                        piece_rect = pygame.Rect(piece["x"], piece["y"], 48, 92)
                        if piece_rect.collidepoint(self.cursor_pos):
                            self.dragged_key = piece
                            self.drag_offset_x = piece["x"] - self.cursor_pos[0]
                            self.drag_offset_y = piece["y"] - self.cursor_pos[1]
                            break
            if self.dragged_key:
                self.dragged_key["x"] = self.cursor_pos[0] + self.drag_offset_x
                self.dragged_key["y"] = self.cursor_pos[1] + self.drag_offset_y
        else:
            if self.dragged_key:
                key_center_x = self.dragged_key["x"] + 24
                key_center_y = self.dragged_key["y"] + 46
                
                target_slot = None
                for slot in self.key_puzzle_slots:
                    if not slot["is_filled"]:
                        dist = math.hypot(key_center_x - slot["target_x"], key_center_y - slot["target_y"])
                        if dist < 55:
                            target_slot = slot
                            break
                            
                if target_slot:
                    self.dragged_key["x"] = target_slot["target_x"] - 19
                    self.dragged_key["y"] = target_slot["target_y"] - 54
                    self.dragged_key["is_placed"] = True
                    self.dragged_key["slot_id"] = target_slot["id"]
                    self.dragged_key["inserting"] = True
                    self.dragged_key["insert_start_time"] = now
                    self.dragged_key["turning"] = False
                    self.dragged_key["turn_angle"] = 0.0
                    self.dragged_key["turn_progress"] = 0.0
                    target_slot["is_filled"] = True
                    target_slot["key_id"] = self.dragged_key["id"]
                else:
                    self.dragged_key["x"] = self.dragged_key["deck_x"]
                    self.dragged_key["y"] = self.dragged_key["deck_y"]
                self.dragged_key = None

    # Legacy alias
    def update_emblem_puzzle(self):
        self.update_key_puzzle()

    def draw_key_puzzle(self):
        if not (self.key_puzzle_active or getattr(self, 'emblem_puzzle_active', False)):
            return
            
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))
        
        box_w, box_h = 820, 560
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        
        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((15, 23, 42, 245))
        self.screen.blit(bg_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (218, 165, 32), (box_x, box_y, box_w, box_h), 3, border_radius=14)
        
        title_font = pygame.font.SysFont("Comic Sans MS", 22, bold=True)
        title_text = "ANCIENT LOTUS RAFT HELM PUZZLE" if getattr(self, 'is_map12', False) else "ANCIENT KEY LOCK PUZZLE"
        title_surf = title_font.render(title_text, True, (255, 215, 0))
        self.screen.blit(title_surf, (box_x + (box_w - title_surf.get_width()) // 2, box_y + 10))
        
        block_x = box_x + 30
        block_y = box_y + 45
        block_w, block_h = 470, 470
        
        # Draw the 6-slot lock block
        if self.puzzle_block_img:
            self.screen.blit(self.puzzle_block_img, (block_x, block_y))
        else:
            pygame.draw.rect(self.screen, (40, 45, 55), (block_x, block_y, block_w, block_h), border_radius=10)
        pygame.draw.rect(self.screen, (120, 135, 155), (block_x, block_y, block_w, block_h), 2, border_radius=10)
        
        # Draw slot indicator glowing rune auras on empty slots
        for slot in self.key_puzzle_slots:
            sx = slot["target_x"]
            sy = slot["target_y"]
            if not slot["is_filled"]:
                pulse = int(math.sin(self.frame_counter * 0.12) * 3)
                pygame.draw.circle(self.screen, (0, 220, 255, 140), (sx, sy), 26 + pulse, 2)
                pygame.draw.circle(self.screen, (250, 204, 21, 50), (sx, sy), 16)
            else:
                pygame.draw.circle(self.screen, (56, 232, 198, 180), (sx, sy), 28, 2)
                
        # Draw Key Rack / Tray
        deck_x = box_x + 525
        deck_y = box_y + 45
        deck_w = 265
        deck_h = 470
        
        deck_surf = pygame.Surface((deck_w, deck_h), pygame.SRCALPHA)
        deck_surf.fill((16, 28, 44, 235))
        self.screen.blit(deck_surf, (deck_x, deck_y))
        pygame.draw.rect(self.screen, (218, 165, 32), (deck_x, deck_y, deck_w, deck_h), 2, border_radius=12)
        
        # Pedestals for keys in deck
        for i in range(6):
            row = i // 2
            col = i % 2
            px = deck_x + 38 + col * 105
            py = deck_y + 50 + row * 125
            ped_surf = pygame.Surface((56, 100), pygame.SRCALPHA)
            ped_surf.fill((10, 18, 30, 180))
            pygame.draw.rect(ped_surf, (50, 75, 100, 120), (0, 0, 56, 100), 1, border_radius=8)
            self.screen.blit(ped_surf, (px - 4, py - 4))
        
        label_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        hint_font = pygame.font.SysFont("Comic Sans MS", 11)
        placed_count = sum(1 for p in self.key_puzzle_pieces if p["is_placed"])
        
        if placed_count < 6:
            deck_lbl = label_font.render(f"GOLDEN KEYS ({placed_count}/6 INSERTED)", True, (255, 215, 0))
            hint_txt = hint_font.render("Drag each key to insert & turn in keyholes", True, (180, 220, 240))
        else:
            deck_lbl = label_font.render("ALL 6 KEYS INSERTED & TURNED!", True, (56, 232, 198))
            hint_txt = hint_font.render("Ancient Lock Mechanism Disengaged!", True, (255, 215, 0))

        self.screen.blit(deck_lbl, (deck_x + (deck_w - deck_lbl.get_width()) // 2, deck_y + 15))
        self.screen.blit(hint_txt, (deck_x + (deck_w - hint_txt.get_width()) // 2, deck_y + 36))
        
        # Draw unplaced keys (full key with shaft and bit)
        for piece in self.key_puzzle_pieces:
            if not piece["is_placed"] and piece != self.dragged_key:
                if self.puzzle_key_img:
                    self.screen.blit(self.puzzle_key_img, (piece["x"], piece["y"]))
                    
        # Draw placed keys (sliding into keyhole during insert, then edge-on vertical line turning into horizontal clover handle)
        handle_sprite = getattr(self, 'puzzle_key_handle_img', None)
        if handle_sprite is None:
            handle_sprite = getattr(self, 'puzzle_key_img', None)

        for piece in self.key_puzzle_pieces:
            if piece["is_placed"]:
                slot_id = piece.get("slot_id")
                if slot_id is not None and slot_id < len(self.key_puzzle_slots):
                    sx = self.key_puzzle_slots[slot_id]["target_x"]
                    sy = self.key_puzzle_slots[slot_id]["target_y"]
                    
                    if piece.get("inserting", False):
                        # Visible sliding insertion: key shaft enters keyhole
                        t = piece.get("insert_progress", 0.0)
                        key_w, key_h = 38, 108
                        start_y = sy - key_h + 10
                        end_y = sy - 20
                        curr_y = start_y + t * (end_y - start_y)
                        
                        clip_rect = pygame.Rect(sx - key_w // 2 - 10, sy - key_h - 20, key_w + 20, int(sy - (sy - key_h - 20) + 15))
                        prev_clip = self.screen.get_clip()
                        self.screen.set_clip(clip_rect)
                        
                        if self.puzzle_key_img:
                            self.screen.blit(self.puzzle_key_img, (sx - key_w // 2, int(curr_y)))
                            
                        self.screen.set_clip(prev_clip)
                    else:
                        # Key is inserted: starts as a thin vertical line (facing back / edge-on), then turns horizontally!
                        angle = piece.get("turn_angle", 0.0)
                        turn_prog = piece.get("turn_progress", 1.0 if not piece.get("turning", False) else 0.0)
                        if handle_sprite:
                            yaw_rad = math.radians(90.0 * (1.0 - turn_prog))
                            scale_x = max(0.16, math.cos(yaw_rad))
                            cur_w = max(12, int(76 * scale_x))
                            cur_h = 76
                            
                            scaled_handle = pygame.transform.smoothscale(handle_sprite, (cur_w, cur_h))
                            rotated_surf = pygame.transform.rotozoom(scaled_handle, -angle, 1.0)
                            rot_rect = rotated_surf.get_rect(center=(sx, sy))
                            self.screen.blit(rotated_surf, rot_rect)
                        
        # Draw dragged key with golden glow
        if self.dragged_key and self.puzzle_key_img:
            glow_surf = pygame.Surface((64, 108), pygame.SRCALPHA)
            glow_surf.fill((255, 215, 0, 90))
            self.screen.blit(glow_surf, (self.dragged_key["x"] - 8, self.dragged_key["y"] - 8))
            self.screen.blit(self.puzzle_key_img, (self.dragged_key["x"], self.dragged_key["y"]))
            pygame.draw.rect(self.screen, (250, 204, 21), (self.dragged_key["x"] - 2, self.dragged_key["y"] - 2, 52, 96), 2, border_radius=6)
            
        # Draw Solved Victory Card & Continue Button when all 6 keys are turned
        if self.key_puzzle_solved_time > 0 or getattr(self, 'key_puzzle_all_placed', False):
            card_w, card_h = 560, 160
            card_x = box_x + (box_w - card_w) // 2
            card_y = box_y + (box_h - card_h) // 2
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill((15, 23, 42, 250))
            self.screen.blit(card_surf, card_rect)
            pygame.draw.rect(self.screen, (34, 197, 94), card_rect, 3, border_radius=14)

            # Header text
            s_font = pygame.font.SysFont("Comic Sans MS", 20, bold=True)
            if getattr(self, 'is_map12', False):
                h_text = "HELM UNLOCKED! RAFT READY!"
                sub_text = "All 6 elemental rudders aligned! The Lotus Raft is untethered!"
                btn_text = "Continue to Lotus Raft"
            else:
                h_text = "ANCIENT LOCK SOLVED!"
                sub_text = "All 6 Golden Keys inserted! Double doors ready to open!"
                btn_text = "Open Double Doors"

            h_surf = s_font.render(h_text, True, (250, 204, 21))
            self.screen.blit(h_surf, (card_x + (card_w - h_surf.get_width()) // 2, card_y + 18))

            sub_font = pygame.font.SysFont("Comic Sans MS", 13)
            sub_surf = sub_font.render(sub_text, True, (255, 255, 255))
            self.screen.blit(sub_surf, (card_x + (card_w - sub_surf.get_width()) // 2, card_y + 52))

            # Continue Button
            btn_w, btn_h = 320, 46
            btn_x = card_x + (card_w - btn_w) // 2
            btn_y = card_y + 92
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            is_hover = btn_rect.collidepoint(self.cursor_pos)

            btn_bg = (34, 197, 94) if is_hover else (22, 101, 52)
            pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

            b_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
            b_surf = b_font.render(btn_text, True, (255, 255, 255))
            self.screen.blit(b_surf, b_surf.get_rect(center=btn_rect.center))
            self.key_puzzle_continue_btn_rect = btn_rect
            
        # Reset Button
        reset_rect = pygame.Rect(deck_x + (deck_w - 160) // 2, deck_y + deck_h - 55, 160, 38)
        is_hover = reset_rect.collidepoint(self.cursor_pos)
        r_color = (255, 215, 0) if is_hover else (30, 41, 59)
        t_color = (0, 0, 0) if is_hover else (255, 255, 255)
        
        pygame.draw.rect(self.screen, r_color, reset_rect, border_radius=8)
        pygame.draw.rect(self.screen, (218, 165, 32), reset_rect, 2, border_radius=8)
        btn_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        btn_txt = btn_font.render("Reset Keys", True, t_color)
        self.screen.blit(btn_txt, btn_txt.get_rect(center=reset_rect.center))
        self.reset_btn_rect = reset_rect

    # Legacy alias
    def draw_emblem_puzzle(self):
        self.draw_key_puzzle()

    # ============================================================
    # MAP 12: SCATTERED ADDITION EQUATION PUZZLE
    # ============================================================
    def init_addition_puzzle(self):
        """Initializes the scattered addition equation puzzle for Map 12.
        Students drag scattered stone runes (2 numbers, +, =, sum) into 5 slots
        to restore the balanced addition equation: [ Num ] [ + ] [ Num ] [ = ] [ Sum ].
        """
        self.addition_slots = []
        self.addition_pieces = []
        self.dragged_addition_piece = None
        self.addition_puzzle_solved = False
        self.addition_puzzle_solved_time = 0
        self.addition_is_correct = False
        self.addition_continue_btn_rect = None
        self.addition_reset_btn_rect = None

        addition_problems = [
            (3, 4, 7),
            (5, 4, 9),
            (6, 4, 10),
            (7, 5, 12),
            (8, 5, 13),
            (8, 6, 14),
            (9, 6, 15),
            (10, 5, 15),
            (8, 7, 15),
            (9, 7, 16),
            (9, 8, 17),
            (10, 8, 18),
            (12, 6, 18),
            (10, 10, 20),
        ]
        num1, num2, total = random.choice(addition_problems)
        self.addition_equation_target = (num1, num2, total)

        box_w, box_h = 860, 540
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # 5 Target Slots across the Altar
        slot_w, slot_h = 104, 104
        slot_gap = 26
        total_slots_w = 5 * slot_w + 4 * slot_gap
        slot_start_x = box_x + (box_w - total_slots_w) // 2
        slot_y = box_y + 130

        slot_hints = ["[ ? ]", "+", "[ ? ]", "=", "[ ? ]"]
        self.addition_slots = []
        for i in range(5):
            sx = slot_start_x + i * (slot_w + slot_gap)
            self.addition_slots.append({
                "id": i,
                "x": sx,
                "y": slot_y,
                "w": slot_w,
                "h": slot_h,
                "hint": slot_hints[i],
                "placed_piece_id": None
            })

        # 5 Pieces
        raw_pieces = [
            {"id": 0, "text": str(num1), "type": "num", "val": num1},
            {"id": 1, "text": "+", "type": "op", "val": "+"},
            {"id": 2, "text": str(num2), "type": "num", "val": num2},
            {"id": 3, "text": "=", "type": "eq", "val": "="},
            {"id": 4, "text": str(total), "type": "num", "val": total}
        ]

        shuffled_ids = [0, 1, 2, 3, 4]
        while True:
            random.shuffle(shuffled_ids)
            if shuffled_ids != [0, 1, 2, 3, 4] and shuffled_ids != [2, 1, 0, 3, 4] and shuffled_ids != [4, 3, 0, 1, 2]:
                break

        tray_y = box_y + 355
        self.addition_pieces = []
        for tray_idx, p_id in enumerate(shuffled_ids):
            p_data = raw_pieces[p_id].copy()
            px = slot_start_x + tray_idx * (slot_w + slot_gap)
            py = tray_y
            p_data.update({
                "x": px,
                "y": py,
                "w": slot_w,
                "h": slot_h,
                "home_x": px,
                "home_y": py,
                "slot_id": None,
                "is_placed": False
            })
            self.addition_pieces.append(p_data)

    def drop_addition_piece(self):
        if not self.dragged_addition_piece:
            return
        piece = self.dragged_addition_piece
        piece_cx = piece["x"] + piece["w"] // 2
        piece_cy = piece["y"] + piece["h"] // 2

        target_slot = None
        for slot in self.addition_slots:
            slot_rect = pygame.Rect(slot["x"] - 15, slot["y"] - 15, slot["w"] + 30, slot["h"] + 30)
            if slot_rect.collidepoint((piece_cx, piece_cy)):
                target_slot = slot
                break

        if target_slot:
            # If target slot occupied by another piece, swap or return home
            if target_slot["placed_piece_id"] is not None and target_slot["placed_piece_id"] != piece["id"]:
                other_piece = next((p for p in self.addition_pieces if p["id"] == target_slot["placed_piece_id"]), None)
                if other_piece:
                    if piece["slot_id"] is not None:
                        prev_slot = next((s for s in self.addition_slots if s["id"] == piece["slot_id"]), None)
                        if prev_slot:
                            prev_slot["placed_piece_id"] = other_piece["id"]
                            other_piece["slot_id"] = prev_slot["id"]
                            other_piece["x"] = prev_slot["x"]
                            other_piece["y"] = prev_slot["y"]
                            other_piece["is_placed"] = True
                    else:
                        other_piece["placed_piece_id"] = None
                        other_piece["slot_id"] = None
                        other_piece["x"] = other_piece["home_x"]
                        other_piece["y"] = other_piece["home_y"]
                        other_piece["is_placed"] = False

            # Free previous slot if different
            if piece["slot_id"] is not None and (target_slot["placed_piece_id"] != piece["id"]):
                for s in self.addition_slots:
                    if s["id"] == piece["slot_id"] and s["id"] != target_slot["id"]:
                        s["placed_piece_id"] = None

            # Snap into slot
            piece["x"] = target_slot["x"]
            piece["y"] = target_slot["y"]
            piece["slot_id"] = target_slot["id"]
            piece["is_placed"] = True
            target_slot["placed_piece_id"] = piece["id"]
            if hasattr(self, 'sound_snap') and self.sound_snap:
                try:
                    self.sound_snap.play()
                except Exception:
                    pass
        else:
            if piece["slot_id"] is not None:
                for s in self.addition_slots:
                    if s["id"] == piece["slot_id"]:
                        s["placed_piece_id"] = None
            piece["slot_id"] = None
            piece["is_placed"] = False
            piece["x"] = piece["home_x"]
            piece["y"] = piece["home_y"]

        self.dragged_addition_piece = None

    def reset_addition_puzzle(self):
        for slot in getattr(self, 'addition_slots', []):
            slot["placed_piece_id"] = None
        for piece in getattr(self, 'addition_pieces', []):
            piece["slot_id"] = None
            piece["is_placed"] = False
            piece["x"] = piece["home_x"]
            piece["y"] = piece["home_y"]
        self.addition_is_correct = False
        self.addition_puzzle_solved = False
        self.key_puzzle_all_placed = False
        self.dragged_addition_piece = None

    def update_addition_puzzle(self):
        if not (self.key_puzzle_active or getattr(self, 'emblem_puzzle_active', False)):
            return

        now = pygame.time.get_ticks()

        # Check if all 5 slots are filled
        all_filled = all(s["placed_piece_id"] is not None for s in getattr(self, 'addition_slots', []))
        if all_filled:
            id_to_p = {p["id"]: p for p in self.addition_pieces}
            slot_pieces = [id_to_p[s["placed_piece_id"]] for s in self.addition_slots]
            is_valid = False

            # Standard: a + b = c
            if slot_pieces[1]["text"] == "+" and slot_pieces[3]["text"] == "=":
                if slot_pieces[0]["type"] == "num" and slot_pieces[2]["type"] == "num" and slot_pieces[4]["type"] == "num":
                    if slot_pieces[0]["val"] + slot_pieces[2]["val"] == slot_pieces[4]["val"]:
                        is_valid = True
            # Reversed: c = a + b
            elif slot_pieces[1]["text"] == "=" and slot_pieces[3]["text"] == "+":
                if slot_pieces[0]["type"] == "num" and slot_pieces[2]["type"] == "num" and slot_pieces[4]["type"] == "num":
                    if slot_pieces[0]["val"] == slot_pieces[2]["val"] + slot_pieces[4]["val"]:
                        is_valid = True

            if is_valid:
                if not self.addition_is_correct:
                    self.addition_is_correct = True
                    self.addition_puzzle_solved = True
                    self.key_puzzle_all_placed = True
                    self.addition_puzzle_solved_time = now
                    if hasattr(self, 'sound_correct') and self.sound_correct:
                        try:
                            self.sound_correct.play()
                        except Exception:
                            pass
            else:
                self.addition_is_correct = False
        else:
            self.addition_is_correct = False

        # Gesture fist drag & drop handling
        if self.hand_detected and self.fist_closed:
            if not self.dragged_addition_piece and not self.addition_is_correct:
                for piece in reversed(getattr(self, 'addition_pieces', [])):
                    piece_rect = pygame.Rect(piece["x"], piece["y"], piece["w"], piece["h"])
                    if piece_rect.collidepoint(self.cursor_pos):
                        self.dragged_addition_piece = piece
                        self.drag_offset_x = piece["x"] - self.cursor_pos[0]
                        self.drag_offset_y = piece["y"] - self.cursor_pos[1]
                        break
        elif self.dragged_addition_piece and not self.fist_closed and self.hand_detected:
            self.drop_addition_piece()

    def draw_addition_puzzle(self):
        if not (self.key_puzzle_active or getattr(self, 'emblem_puzzle_active', False)):
            return

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 860, 540
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Main Panel
        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((15, 23, 42, 250))
        self.screen.blit(bg_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (218, 165, 32), (box_x, box_y, box_w, box_h), 3, border_radius=16)

        # Header Title
        title_font = pygame.font.SysFont("Comic Sans MS", 22, bold=True)
        title_surf = title_font.render("ANCIENT LOTUS RAFT HELM PUZZLE", True, (255, 215, 0))
        self.screen.blit(title_surf, (box_x + (box_w - title_surf.get_width()) // 2, box_y + 12))

        sub_font = pygame.font.SysFont("Comic Sans MS", 13)
        sub_text = "The rudder runes were scattered by the rapids! Arrange them into a correct addition equation:"
        sub_surf = sub_font.render(sub_text, True, (203, 213, 225))
        self.screen.blit(sub_surf, (box_x + (box_w - sub_surf.get_width()) // 2, box_y + 44))

        # Altar Deck Background
        altar_rect = pygame.Rect(box_x + 25, box_y + 75, box_w - 50, 185)
        altar_surf = pygame.Surface((altar_rect.w, altar_rect.h), pygame.SRCALPHA)
        altar_surf.fill((10, 18, 30, 220))
        self.screen.blit(altar_surf, altar_rect)
        pygame.draw.rect(self.screen, (56, 189, 248, 140), altar_rect, 2, border_radius=12)

        deck_lbl_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
        deck_lbl = deck_lbl_font.render("ANCIENT EQUATION PEDESTAL", True, (148, 163, 184))
        self.screen.blit(deck_lbl, (altar_rect.x + 16, altar_rect.y + 10))

        # Draw 5 Slots
        hint_font = pygame.font.SysFont("Comic Sans MS", 28, bold=True)
        for slot in getattr(self, 'addition_slots', []):
            s_rect = pygame.Rect(slot["x"], slot["y"], slot["w"], slot["h"])
            pygame.draw.rect(self.screen, (24, 34, 52), s_rect, border_radius=12)
            pulse = int(math.sin(self.frame_counter * 0.1 + slot["id"]) * 2)
            glow_color = (56, 189, 248) if slot["placed_piece_id"] is None else (34, 197, 94)
            pygame.draw.rect(self.screen, glow_color, s_rect, 2 + pulse, border_radius=12)

            if slot["placed_piece_id"] is None:
                h_surf = hint_font.render(slot["hint"], True, (71, 85, 105))
                self.screen.blit(h_surf, h_surf.get_rect(center=s_rect.center))

        # Scattered Tray Background
        tray_rect = pygame.Rect(box_x + 25, box_y + 280, box_w - 50, 225)
        tray_surf = pygame.Surface((tray_rect.w, tray_rect.h), pygame.SRCALPHA)
        tray_surf.fill((12, 22, 36, 220))
        self.screen.blit(tray_surf, tray_rect)
        pygame.draw.rect(self.screen, (218, 165, 32, 160), tray_rect, 2, border_radius=12)

        tray_lbl = deck_lbl_font.render("SCATTERED RUNE TABLETS (DRAG TO SLOTS)", True, (250, 204, 21))
        self.screen.blit(tray_lbl, (tray_rect.x + 16, tray_rect.y + 10))

        # Status text
        status_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        all_filled = all(s["placed_piece_id"] is not None for s in getattr(self, 'addition_slots', []))
        if all_filled:
            if getattr(self, 'addition_is_correct', False):
                status_txt = status_font.render("Perfect! The addition equation is balanced and correct!", True, (34, 197, 94))
            else:
                status_txt = status_font.render("Equation not balanced yet! Try swapping the numbers or sum.", True, (251, 191, 36))
        else:
            status_txt = status_font.render("Drag each rune tablet into an altar pedestal to build: [Number] + [Number] = [Sum]", True, (147, 197, 253))
        self.screen.blit(status_txt, (tray_rect.x + 16, tray_rect.y + 35))

        # Draw Home pedestals in tray
        for piece in getattr(self, 'addition_pieces', []):
            ped_rect = pygame.Rect(piece["home_x"] + 6, piece["home_y"] + 6, piece["w"] - 12, piece["h"] - 12)
            pygame.draw.rect(self.screen, (19, 30, 46), ped_rect, border_radius=10)
            pygame.draw.rect(self.screen, (51, 65, 85), ped_rect, 1, border_radius=10)

        # Draw Pieces (non-dragged first)
        num_font = pygame.font.SysFont("Comic Sans MS", 36, bold=True)
        sym_font = pygame.font.SysFont("Comic Sans MS", 44, bold=True)

        def draw_piece_card(p, is_hover=False, is_dragged=False):
            p_rect = pygame.Rect(p["x"], p["y"], p["w"], p["h"])
            s_rect = pygame.Rect(p["x"] + 3, p["y"] + (8 if is_dragged else 4), p["w"], p["h"])
            pygame.draw.rect(self.screen, (8, 12, 20), s_rect, border_radius=14)

            if p["type"] == "num":
                c_bg = (30, 41, 59) if not is_hover else (51, 65, 85)
                b_col = (250, 204, 21)
                t_surf = num_font.render(p["text"], True, (253, 224, 71))
            elif p["type"] == "op":
                c_bg = (12, 74, 110) if not is_hover else (3, 105, 161)
                b_col = (56, 189, 248)
                t_surf = sym_font.render("+", True, (224, 242, 254))
            else:
                c_bg = (15, 76, 92) if not is_hover else (19, 99, 120)
                b_col = (45, 212, 191)
                t_surf = sym_font.render("=", True, (204, 251, 241))

            pygame.draw.rect(self.screen, c_bg, p_rect, border_radius=14)
            pygame.draw.rect(self.screen, b_col, p_rect, 3 if not is_dragged else 4, border_radius=14)
            self.screen.blit(t_surf, t_surf.get_rect(center=p_rect.center))

        for piece in getattr(self, 'addition_pieces', []):
            if piece is not self.dragged_addition_piece:
                p_rect = pygame.Rect(piece["x"], piece["y"], piece["w"], piece["h"])
                is_hov = p_rect.collidepoint(self.cursor_pos)
                draw_piece_card(piece, is_hover=is_hov, is_dragged=False)

        # Draw Dragged Piece on top
        if self.dragged_addition_piece:
            p = self.dragged_addition_piece
            glow_surf = pygame.Surface((p["w"] + 24, p["h"] + 24), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (255, 215, 0, 75), (0, 0, p["w"] + 24, p["h"] + 24), border_radius=18)
            self.screen.blit(glow_surf, (p["x"] - 12, p["y"] - 12))
            draw_piece_card(p, is_hover=True, is_dragged=True)

        # Reset Button in bottom right
        reset_w, reset_h = 140, 36
        reset_x = box_x + box_w - reset_w - 40
        reset_y = box_y + box_h - reset_h - 18
        reset_rect = pygame.Rect(reset_x, reset_y, reset_w, reset_h)
        is_reset_hov = reset_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (234, 179, 8) if is_reset_hov else (30, 41, 59), reset_rect, border_radius=8)
        pygame.draw.rect(self.screen, (218, 165, 32), reset_rect, 2, border_radius=8)
        rst_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
        rst_surf = rst_font.render("Reset Runes", True, (0, 0, 0) if is_reset_hov else (255, 255, 255))
        self.screen.blit(rst_surf, rst_surf.get_rect(center=reset_rect.center))
        self.addition_reset_btn_rect = reset_rect

        # Solved Victory Card Overlay
        if getattr(self, 'addition_is_correct', False):
            card_w, card_h = 580, 180
            card_x = box_x + (box_w - card_w) // 2
            card_y = box_y + (box_h - card_h) // 2
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill((15, 23, 42, 252))
            self.screen.blit(card_surf, card_rect)
            pygame.draw.rect(self.screen, (34, 197, 94), card_rect, 3, border_radius=16)

            id_to_p = {p["id"]: p for p in self.addition_pieces}
            slot_pieces = [id_to_p[s["placed_piece_id"]] for s in self.addition_slots]
            eq_str = f"{slot_pieces[0]['text']} {slot_pieces[1]['text']} {slot_pieces[2]['text']} {slot_pieces[3]['text']} {slot_pieces[4]['text']}"

            v_title_font = pygame.font.SysFont("Comic Sans MS", 20, bold=True)
            v_title = v_title_font.render("EQUATION RESTORED! HELM UNLOCKED!", True, (250, 204, 21))
            self.screen.blit(v_title, (card_x + (card_w - v_title.get_width()) // 2, card_y + 16))

            v_sub_font = pygame.font.SysFont("Comic Sans MS", 15, bold=True)
            v_sub = v_sub_font.render(f"{eq_str} is Balanced & Correct!", True, (56, 189, 248))
            self.screen.blit(v_sub, (card_x + (card_w - v_sub.get_width()) // 2, card_y + 50))

            v_desc_font = pygame.font.SysFont("Comic Sans MS", 12)
            v_desc = v_desc_font.render("Guardian Bromen untethered the Lotus Raft for your voyage!", True, (255, 255, 255))
            self.screen.blit(v_desc, (card_x + (card_w - v_desc.get_width()) // 2, card_y + 78))

            btn_w, btn_h = 320, 46
            btn_x = card_x + (card_w - btn_w) // 2
            btn_y = card_y + 114
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            is_hover = btn_rect.collidepoint(self.cursor_pos)

            btn_bg = (34, 197, 94) if is_hover else (22, 101, 52)
            pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

            btn_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
            btn_surf = btn_font.render("Continue to Lotus Raft", True, (255, 255, 255))
            self.screen.blit(btn_surf, btn_surf.get_rect(center=btn_rect.center))
            self.addition_continue_btn_rect = btn_rect

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
        speaker_name = "Guardian Bromen (Lotus Raft Guardian)" if getattr(self, 'is_map12', False) else "Guardian Bromen"
        speaker_surf = speaker_font.render(speaker_name, True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + speaker_surf.get_width() + 25, box_y + 48), 2)

        q_font = pygame.font.SysFont("Comic Sans MS", 16)
        if self.bromen_dialogue_state == 1:
            if getattr(self, 'is_map12', False):
                line1 = "Halt, young voyager! The Lotus Raft is safely moored."
                line2 = f"The canal is not yet full enough to carry us across."
                line3 = f"Open all 6 Aqueduct Sluices in the temple chambers! ({len(self.answered_stations)}/6 Sluices Opened)"
                btn_text = "I will go open the sluices!"
            else:
                line1 = "Halt, student! The double doors and portal are sealed."
                line2 = f"You must first collect all 6 Golden Keys from the"
                line3 = f"guardians in this chamber. (Current: {len(self.answered_stations)}/6 Keys)"
                btn_text = "I will go search for them"
        else:
            if getattr(self, 'is_map12', False):
                line1 = "Marvelous! All 6 Aqueduct Sluices are open and the canal is full!"
                line2 = "Before we sail, the ancient rudder equation was scattered by the rapids!"
                line3 = "Arrange the scattered runes into a correct addition equation to unlock the helm!"
                btn_text = "Solve Addition Puzzle"
            else:
                line1 = "Excellent! You have collected all 6 Golden Keys."
                line2 = "To unlock the double doors, you must now insert and turn"
                line3 = "the keys into the 6 slots on the Ancient Lock Block."
                btn_text = "Unlock the Ancient Box"

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
            active_target_idx = None
            for s_idx in range(1, 7):
                if s_idx in self.quiz_stations and s_idx not in self.answered_stations:
                    active_target_idx = s_idx
                    break
            if active_target_idx is not None:
                st_x, st_y = self.quiz_stations[active_target_idx]
                npc_name = self.station_npcs.get(active_target_idx, {}).get("name", f"Guardian {active_target_idx}")
                target_info = (st_x, st_y, npc_name)
            elif getattr(self, 'is_map12', False):
                if not self.key_puzzle_solved and self.npc_bromen_found:
                    target_info = (self.npc_bromen_tile_x, self.npc_bromen_tile_y, "Guardian Bromen")
                elif getattr(self, 'raft_state', None) in ["docked_west", "ready_to_sail"]:
                    target_info = (29, 9, "Lotus Raft")
                else:
                    target_info = (48, 9, "Exit Portal")
            elif self.npc_bromen_found and not (self.key_puzzle_solved or self.emblem_puzzle_solved):
                target_info = (self.npc_bromen_tile_x, self.npc_bromen_tile_y, "Bromen (Ancient Lock Block)")

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

    def draw_stage_timer_hud(self):
        """Draws the sleek 10-minute digital stopwatch timer HUD at top center"""
        now = pygame.time.get_ticks()
        mins = int(self.stage_time_remaining // 60)
        secs = int(self.stage_time_remaining % 60)

        hud_w, hud_h = 160, 38
        hud_x = (self.width - hud_w) // 2
        hud_y = 16

        # Color based on remaining time
        if self.stage_time_remaining > 120:
            border_col = (245, 158, 11)
            txt_col = (255, 255, 255)
            border_w = 2
        elif self.stage_time_remaining > 60:
            border_col = (251, 191, 36)
            txt_col = (253, 230, 138)
            border_w = 2
        else:
            pulse = (math.sin(now * 0.008) + 1) / 2
            border_col = (239, 68, 68) if pulse > 0.3 else (255, 255, 255)
            txt_col = (254, 202, 202)
            border_w = 3

        # Translucent Background
        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        hud_surf.fill((15, 23, 42, 220))
        self.screen.blit(hud_surf, (hud_x, hud_y))
        pygame.draw.rect(self.screen, border_col, (hud_x, hud_y, hud_w, hud_h), border_w, border_radius=10)

        # Draw mini analog clock icon
        clock_cx = hud_x + 22
        clock_cy = hud_y + hud_h // 2
        pygame.draw.circle(self.screen, border_col, (clock_cx, clock_cy), 9, 2)
        pygame.draw.line(self.screen, border_col, (clock_cx, clock_cy), (clock_cx, clock_cy - 5), 2)
        pygame.draw.line(self.screen, border_col, (clock_cx, clock_cy), (clock_cx + 4, clock_cy), 2)

        t_font = self.get_ui_font(16, bold=True)
        t_surf = t_font.render(f"{mins:02d}:{secs:02d}", True, txt_col)
        self.screen.blit(t_surf, t_surf.get_rect(center=(hud_x + 95, hud_y + hud_h // 2)))

    def draw_time_up_dialog(self):
        """Draws a modal dialog when the 10-minute timer runs out"""
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        self.screen.blit(dim, (0, 0))

        box_w, box_h = 560, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (15, 23, 42), (box_x, box_y, box_w, box_h), border_radius=16)
        pygame.draw.rect(self.screen, (239, 68, 68), (box_x, box_y, box_w, box_h), 3, border_radius=16)

        t_font = self.get_ui_font(24, bold=True)
        msg_font = self.get_ui_font(18)
        btn_font = self.get_ui_font(16, bold=True)

        title = t_font.render("TIME'S UP!", True, (239, 68, 68))
        self.screen.blit(title, title.get_rect(center=(box_x + box_w // 2, box_y + 36)))

        m1 = msg_font.render("Your 10-minute stage time limit has expired.", True, (255, 255, 255))
        m2 = msg_font.render("Would you like to try again or return to Stage Select?", True, (203, 213, 225))
        self.screen.blit(m1, m1.get_rect(center=(box_x + box_w // 2, box_y + 85)))
        self.screen.blit(m2, m2.get_rect(center=(box_x + box_w // 2, box_y + 115)))

        # Button 1: Retry Quarter
        retry_rect = pygame.Rect(box_x + 40, box_y + 175, 220, 46)
        r_hov = retry_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (245, 158, 11) if r_hov else (30, 41, 59), retry_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), retry_rect, 2, border_radius=10)
        r_txt = btn_font.render("Retry Quarter", True, (15, 23, 42) if r_hov else (255, 255, 255))
        self.screen.blit(r_txt, r_txt.get_rect(center=retry_rect.center))

        # Button 2: Return to Stage Select
        exit_rect = pygame.Rect(box_x + box_w - 260, box_y + 175, 220, 46)
        e_hov = exit_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if e_hov else (30, 41, 59), exit_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), exit_rect, 2, border_radius=10)
        e_txt = btn_font.render("Stage Select", True, (255, 255, 255))
        self.screen.blit(e_txt, e_txt.get_rect(center=exit_rect.center))

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()