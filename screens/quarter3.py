import pygame
import os
import sys
import cv2
import numpy as np
import time
import math
import random
import collections
from .map_loader import MapLoader

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


class Quarter3:
    def __init__(self, screen, main_menu, map_name):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()
        self.map_name = map_name  # 'map3.txt'

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

        self.QUARTER3_TILES_PATH = os.path.join(
            self.BASE_DIR,
            "assets",
            "images",
            "sprites",
            "objects",
            "tiles",
            "quarter3tiles"
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

        self.NPC_PATH_NUM1 = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "Number1NPC")
        self.NPC_PATH_NUM2 = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "Number2NPC")
        self.NPC_PATH_NUM3 = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "Number3NPC")
        self.NPC_PATH_NUM4 = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "Number4NPC")
        self.NPC_PATH_NUM5 = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "Number5NPC")

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
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "P", "B", "r", "l", "u", "d"}

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

        # Station Shape NPCs (Circle, Square, Star, Diamond, Heart)
        self.station_npcs = {}
        self.load_station_shape_npcs()

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

        # ============================================================
        # LOAD PORTALS
        # ============================================================
        self.portals = []
        self.portal_frames_cache = self.load_portal_frames()
        self.load_static_portals()

        # Teleport cooldown
        self.teleport_cooldown = 0
        self.TELEPORT_COOLDOWN_TIME = 1.0

        # Goal portal tracking - for map3.txt the goal is 'left' portal
        self.goal_portal_direction = self.portals[0].direction if self.portals else 'left'

        # ============================================================
        # UI & REUSABLE FONTS
        # ============================================================
        self.show_info = True
        self.font = pygame.font.SysFont("Comic Sans MS", 16)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 12)
        self.dialog_header_font = pygame.font.SysFont("Comic Sans MS", 17, bold=True)
        self.dialog_q_font = pygame.font.SysFont("Comic Sans MS", 15, bold=True)
        self.dialog_choice_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        self.dialog_badge_font = pygame.font.SysFont("Comic Sans MS", 15, bold=True)
        self.dialog_hint_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        self.dialog_speaker_font = pygame.font.SysFont("Comic Sans MS", 18, bold=True)
        self.dialog_btn_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
        self.dialog_msg_font = pygame.font.SysFont("Comic Sans MS", 16, bold=True)
        self.dialog_regular_font = pygame.font.SysFont("Comic Sans MS", 15)
        self.dialog_stat_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)

        # Pre-created cached surfaces for high performance and zero allocations in draw()
        shadow_w = int(24 * ZOOM)
        shadow_h = int(10 * ZOOM)
        self.contact_shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.contact_shadow_surf, (0, 0, 0, 80), (0, 0, shadow_w, shadow_h))

        plat_w = int(36 * ZOOM)
        plat_h = int(16 * ZOOM)
        self.plat_active_surf = pygame.Surface((plat_w, plat_h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.plat_active_surf, (251, 191, 36, 140), (0, 0, plat_w, plat_h))
        pygame.draw.ellipse(self.plat_active_surf, (255, 215, 0, 240), (0, 0, plat_w, plat_h), 2)

        self.plat_inactive_surf = pygame.Surface((plat_w, plat_h), pygame.SRCALPHA)
        pygame.draw.ellipse(self.plat_inactive_surf, (30, 41, 59, 120), (0, 0, plat_w, plat_h))
        pygame.draw.ellipse(self.plat_inactive_surf, (147, 197, 253, 200), (0, 0, plat_w, plat_h), 2)

        # Generate High-Resolution Icon Engine Cache for all UI Icons
        self.generate_icon_cache()

        # Clock for delta time
        self.clock = pygame.time.Clock()
        self.frame_counter = 0

        # Completion flag
        self.completed = False

        self.is_quiz_map = True
        self.quiz_state = 0  # 0: waiting proximity, 1: dialog Q, 2: wrong try again, 3: correct phrase transition, 4: out of tries reveal, 5: final speech, 6: quiz complete
        self.quiz_station_index = 1  # current station (1-5)
        self.current_question_index = 0
        self.first_attempt_correct = {1: True, 2: True, 3: True, 4: True, 5: True}
        self.station_attempts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.selected_choice_index = -1  # choice highlighted

        # 50:50 Wizard Hint & friendly elimination tracking
        self.eliminated_choices = set()
        self.wrong_feedback_msg = ""

        # Station Standby Directions based on Map Name
        if self.map_name == "map8.txt":
            self.station_directions = {
                1: "right",
                2: "right",
                3: "right",
                4: "right",
                5: "right"
            }
        elif self.map_name == "map9.txt":
            self.station_directions = {
                1: "left",
                2: "left",
                3: "left",
                4: "left",
                5: "left"
            }
        else: # Default for map7.txt
            self.station_directions = {
                1: "left",
                2: "up",
                3: "down",
                4: "left",
                5: "left"
            }

        # Scan map for quiz stations 1, 2, 3, 4, 5
        self.quiz_stations = {}
        for y, row in enumerate(self.game_map):
            for x, c in enumerate(row):
                if c in ['1', '2', '3', '4', '5']:
                    num = int(c)
                    self.quiz_stations[num] = (x, y)
                    print(f"📍 Quiz Station {num} found at: ({x}, {y})")

        # Correct answer random responses
        self.current_correct_phrase = ""
        self.correct_phrases = [
            "Splendid! Your mathematical knowledge shines bright!",
            "Outstanding! That is correct, onto the next challenge!",
            "Superb! You are a brilliant math explorer!"
        ]
        self.player_block_timer = 0.0
        self.ident_input_text = ""

        # DepEd MATATAG Grade 2 Quarter 3 Multiple Choice Questions
        self.quiz_questions = [
            {
                "station": 1,
                "title": "🍎 MULTIPLICATION ARRAYS",
                "question": "Farmer Ben arranged golden apples into 3 equal rows with 4 apples in each row. What is the total product of 3 × 4?",
                "q_type": "multiple_choice",
                "choices": ["A. 7 apples", "B. 10 apples", "C. 12 apples", "D. 15 apples"],
                "correct": 2,  # C. 12
                "visual_type": "array",
                "visual_rows": 3,
                "visual_cols": 4,
                "hint": "Count the total number of apples across all 3 rows of 4!"
            },
            {
                "station": 2,
                "title": "🥥 REPEATED ADDITION",
                "question": "Which repeated addition sentence matches 4 groups with 2 coconuts in each group?",
                "q_type": "multiple_choice",
                "choices": ["A. 4 + 4", "B. 2 + 2 + 2 + 2", "C. 4 + 2", "D. 2 + 4 + 2"],
                "correct": 1,  # B. 2 + 2 + 2 + 2
                "visual_type": "groups",
                "visual_groups": 4,
                "visual_items_per_group": 2,
                "hint": "Think about which addition sentence adds 2 coconuts four times!"
            },
            {
                "station": 3,
                "title": "🎁 EQUAL SHARING DIVISION",
                "question": "You gathered 10 gold coins to share equally between 2 treasure chests. How many coins belong in each chest (10 ÷ 2)?",
                "q_type": "multiple_choice",
                "choices": ["A. 3 coins", "B. 4 coins", "C. 5 coins", "D. 8 coins"],
                "correct": 2,  # C. 5 coins
                "visual_type": "sharing",
                "visual_total": 10,
                "visual_chests": 2,
                "hint": "Divide the 10 coins into 2 equal piles to find how many go in each chest!"
            },
            {
                "station": 4,
                "title": "🍕 UNIT FRACTIONS (ONE-HALF)",
                "question": "The Sacred Sun Disk is divided into 2 equal parts. What unit fraction represents 1 shaded part out of 2?",
                "q_type": "multiple_choice",
                "choices": ["A. 1/4 (One-Fourth)", "B. 1/3 (One-Third)", "C. 1/2 (One-Half)", "D. 2/2 (Whole)"],
                "correct": 2,  # C. 1/2
                "visual_type": "fraction_circle",
                "visual_slices": 2,
                "visual_shaded": 1,
                "hint": "A unit fraction has 1 on top (numerator) and total equal parts on the bottom!"
            },
            {
                "station": 5,
                "title": "🍫 UNIT FRACTIONS (ONE-THIRD)",
                "question": "The golden ingot bar is divided into 3 equal segments. What unit fraction represents 1 shaded segment out of 3?",
                "q_type": "multiple_choice",
                "choices": ["A. 1/3 (One-Third)", "B. 1/2 (One-Half)", "C. 1/4 (One-Fourth)", "D. 3/1"],
                "correct": 0,  # A. 1/3
                "visual_type": "fraction_bar",
                "visual_segments": 3,
                "visual_shaded": 1,
                "hint": "A unit fraction has 1 on top (numerator) and total equal parts on the bottom!"
            }
        ]

        # Load dynamic questions from Database / Vercel API
        self.load_database_questions()

        # ============================================================
        # EXPLORER'S CARAVAN & COMPANION WAGON SYSTEM
        # ============================================================
        self.player_trail = collections.deque(maxlen=40)
        self.caravan_x = self.player_x - 32
        self.caravan_y = self.player_y
        self.caravan_dir = "right"
        self.caravan_bob_timer = 0.0
        self.caravan_wheel_rot = 0.0
        self.caravan_cargo = []  # Upgraded with each answered question
        self.caravan_upgrade_banner_text = ""
        self.caravan_upgrade_banner_sub = ""
        self.caravan_upgrade_banner_timer = 0.0
        self.caravan_sparkles = []
        self.caravan_music_notes = []
        self.speed_boost_timer = 0.0
        self.caravan_riding = False
        self.caravan_ride_path = []
        self.caravan_ride_index = 0

        # Cargo catalog corresponding to each Station Challenge
        self.station_cargo_rewards = {
            1: {"name": "Apple Baskets", "icon_key": "apple", "count": "12 Apples", "color": (239, 68, 68), "desc": "3 Rows of 4 Crisp Apples!"},
            2: {"name": "Coconut Crates", "icon_key": "coconut", "count": "8 Coconuts", "color": (180, 83, 9), "desc": "4 Groups of 2 Sweet Coconuts!"},
            3: {"name": "Golden Chests", "icon_key": "chest", "count": "10 Gold Coins", "color": (245, 158, 11), "desc": "2 Chests of 5 Shared Coins!"},
            4: {"name": "Royal Pizza Feast", "icon_key": "pizza", "count": "1/2 Feast", "color": (217, 119, 6), "desc": "1 out of 2 Delicious Slices!"},
            5: {"name": "Sun Cocoa Relic", "icon_key": "chocolate", "count": "1/3 Relic", "color": (168, 85, 247), "desc": "1 out of 3 Royal Cocoa Bars!"},
        }

        # Map 8 Golden Aqueduct Bridge Construction
        if self.map_name == "map8.txt":
            self.bridge_tiles = [(40, 7), (41, 7), (42, 7), (43, 7), (44, 7)]
            self.built_bridge_count = 0
            for bx, by in self.bridge_tiles:
                if by < len(self.game_map) and bx < len(self.game_map[by]):
                    self.game_map[by] = self.game_map[by][:bx] + "w" + self.game_map[by][bx+1:]
                    self.render_map[by] = self.render_map[by][:bx] + "w" + self.render_map[by][bx+1:]
        else:
            self.bridge_tiles = []
            self.built_bridge_count = 0

        # Cinematic Drone Camera Pan State
        self.camera_pan_active = False
        self.camera_pan_timer = 0.0
        self.camera_pan_duration = 2.4
        self.camera_pan_burst_done = False
        self.camera_pan_target_col = 0
        self.camera_pan_target_row = 0
        self.camera_pan_origin_x = 0.0
        self.camera_pan_origin_y = 0.0
        self.camera_pan_dest_x = 0.0
        self.camera_pan_dest_y = 0.0

        # Sun Relic Altar Jigsaw System
        self.sun_relic_active = False
        self.sun_relic_solved = False
        self.sun_relic_solved_time = 0
        self.dragged_slab = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.sun_relic_slabs = []
        self.load_puzzle_sounds()

        # ============================================================
        # 🏺 3 DISTINCT GAMEPLAY MODES FOR QUARTER 3
        # ============================================================
        self.is_caravan_mode = (self.map_name == "map7.txt")       # Map 7: Explorer's Royal Caravan
        self.is_relic_hunt_mode = (self.map_name == "map8.txt")    # Map 8: In-World Relic Hunt & Causeway Bridge
        self.is_puzzle_hybrid_mode = (self.map_name == "map9.txt") # Map 9: Sacred Citadel Mini-Puzzles & Altar

        # Map 8 Relic Hunt Data
        self.relic_stage = 1
        self.relic_items = []
        self.relic_target_count = 0
        self.relic_collected_count = 0
        self.relic_item_type = "apple"
        self.relic_quest_title = ""
        self.relic_quest_math = ""
        self.relic_quest_hint = ""
        self.relic_pickup_particles = []
        self.relic_float_time = 0.0
        self.relic_stage_complete = False
        self.relic_banner_text = ""
        self.relic_banner_sub = ""
        self.relic_banner_timer = 0.0

        # ============================================================
        # 🏛️ CITADEL OF THE SUN: KEYSTONE ALTAR SYSTEM (MAP 9 GAMEPLAY)
        # ============================================================
        self.citadel_keystones = {
            1: {"num": 1, "roman": "I", "name": "Apple Array Scepter", "math": "3 × 4", "color": (239, 68, 68), "icon": "apple"},
            2: {"num": 2, "roman": "II", "name": "Coconut Oasis Orb", "math": "4 × 2", "color": (180, 83, 9), "icon": "coconut"},
            3: {"num": 3, "roman": "III", "name": "Scarab Coin Chalice", "math": "10 ÷ 2", "color": (234, 179, 8), "icon": "chest"},
            4: {"num": 4, "roman": "IV", "name": "Solar Half Keystone", "math": "1/2", "color": (245, 158, 11), "icon": "sun_disk"},
            5: {"num": 5, "roman": "V", "name": "Golden Ingot Prism", "math": "1/3", "color": (217, 119, 6), "icon": "ingot"}
        }
        self.citadel_collected_keystones = []
        self.citadel_banner_text = ""
        self.citadel_banner_sub = ""
        self.citadel_banner_timer = 0.0

        # ============================================================
        # 🧩 MAP 9 INTERACTIVE MINI-PUZZLES STATE
        # ============================================================
        self.mini_puzzle_active = False
        self.mini_puzzle_station = 1
        self.mini_puzzle_solved = False
        self.mini_puzzle_solved_time = 0
        self.mini_puzzle_dragged_item = None
        self.mini_puzzle_drag_offset_x = 0
        self.mini_puzzle_drag_offset_y = 0
        self.mini_puzzle_slots = []
        self.mini_puzzle_items = []
        self.mini_puzzle_title = ""
        self.mini_puzzle_sub = ""
        self.mini_puzzle_math_target = ""
        self.mini_puzzle_type = "array"

        # Initialize High-Performance Surface & Sprite Cache for Raspberry Pi (60 FPS)
        self.init_cached_surfaces()

        if self.is_relic_hunt_mode:
            self.spawn_relic_stage(1)

        print(f"✅ Quarter3 initialized with map: {self.map_name}")
        print(f"   Goal portal: {self.goal_portal_direction}")
        print(f"   Portals loaded: {len(self.portals)}")

    # ============================================================
    # ⚡ RASPBERRY PI HIGH-PERFORMANCE PRE-CACHING (60 FPS)
    # ============================================================
    def init_cached_surfaces(self):
        """Pre-renders static backdrop, pre-scales all tiles/sprites, and pre-allocates overlays for 60 FPS on Raspberry Pi"""
        self.scaled_tile_size = int(TILE_SIZE * ZOOM)

        # 1. Pre-scale all tile images to match standard tile grid size (48x48 at 1.5x zoom)
        self.scaled_tile_images = {}
        for k, img in self.tile_images.items():
            self.scaled_tile_images[k] = pygame.transform.scale(img, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha()
        self.scaled_fallback_tile = pygame.transform.scale(self.fallback_tile, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha()

        # 2. Pre-scale player sprites
        self.scaled_player_sprites = {}
        for direction, frames in self.player_sprites.items():
            self.scaled_player_sprites[direction] = [
                pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in frames
            ]

        # 3. Pre-scale animated NPC Bromen frames
        if hasattr(self, 'npc_bromen_sprites') and self.npc_bromen_sprites:
            self.npc_bromen_sprites = [
                pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_bromen_sprites
            ]

        # 4. Pre-scale Station Number NPCs
        if hasattr(self, 'station_npcs') and self.station_npcs:
            for st_num, data in self.station_npcs.items():
                data["frames"] = [
                    pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in data["frames"]
                ]

        # 5. Pre-scale static & walking NPCs
        if getattr(self, 'npc_oldman_sprite', None):
            self.npc_oldman_sprite = pygame.transform.scale(self.npc_oldman_sprite, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha()
        if getattr(self, 'npc_knight_sprite', None):
            self.npc_knight_sprite = pygame.transform.scale(self.npc_knight_sprite, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha()
        if getattr(self, 'npc_knight_left_sprites', None):
            self.npc_knight_left_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_knight_left_sprites]
        if getattr(self, 'npc_knight_right_sprites', None):
            self.npc_knight_right_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_knight_right_sprites]
        if getattr(self, 'npc_knight_down_sprites', None):
            self.npc_knight_down_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_knight_down_sprites]
        if getattr(self, 'npc_knight_up_sprites', None):
            self.npc_knight_up_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_knight_up_sprites]

        # 6. Pre-render sand tile bubble accent directly baked into tiles
        self.cached_tile_bubble = pygame.Surface((self.scaled_tile_size, self.scaled_tile_size), pygame.SRCALPHA)
        pygame.draw.circle(self.cached_tile_bubble, (255, 255, 255, 70), (self.scaled_tile_size // 2, self.scaled_tile_size // 2), self.scaled_tile_size // 3)
        for tile_k in ['G', '1', '2', '3', '4', '5', 'P']:
            if tile_k in self.scaled_tile_images:
                self.scaled_tile_images[tile_k].blit(self.cached_tile_bubble, (0, 0))

        # 7. Pre-render static Math Sky Backdrop
        self.cached_math_bg = pygame.Surface((self.width, self.height))
        self.cached_math_bg.fill((237, 248, 255))
        pastel_colors = [(255, 204, 102), (153, 234, 255), (200, 255, 200), (255, 178, 214), (198, 186, 255)]
        for i, color in enumerate(pastel_colors):
            cx = (self.width // 5) * ((i % 5) + 1) - 30
            cy = 40 + ((i // 5) * 80)
            pygame.draw.circle(self.cached_math_bg, color, (cx, cy), 38, 0)
        for i in range(12):
            x = (i * 97) % self.width
            y = (i * 43) % (self.height // 2)
            pygame.draw.circle(self.cached_math_bg, (255, 255, 255), (x, y), 2, 0)
        math_font = pygame.font.SysFont("Comic Sans MS", 22, bold=True)
        for label, x_pos in [("+", 70), ("=", 180), ("3", 290), ("×", 390), ("7", 520), ("-", 610)]:
            text = math_font.render(label, True, (59, 130, 246))
            self.cached_math_bg.blit(text, (x_pos, 18))

        # 8. Pre-render full-screen dimming overlays
        self.dialog_dim_overlay = pygame.Surface((self.width, self.height))
        self.dialog_dim_overlay.fill((0, 0, 0))
        self.dialog_dim_overlay.set_alpha(175)

        self.wrong_dialog_dim_overlay = pygame.Surface((self.width, self.height))
        self.wrong_dialog_dim_overlay.fill((0, 0, 0))
        self.wrong_dialog_dim_overlay.set_alpha(160)

        # 9. Pre-render HUD & Banner glassmorphic background surfaces
        self.quest_hud_bg = pygame.Surface((760, 68), pygame.SRCALPHA)
        self.quest_hud_bg.fill((15, 23, 42, 220))

        self.banner_bg = pygame.Surface((640, 68), pygame.SRCALPHA)
        self.banner_bg.fill((15, 23, 42, 230))

        self.obj_hud_bg = pygame.Surface((340, 80), pygame.SRCALPHA)
        self.obj_hud_bg.fill((15, 23, 42, 190))

        # 10. Pre-render Item & Caravan contact shadows
        self.relic_shadow_surf = pygame.Surface((int(22 * ZOOM), int(8 * ZOOM)), pygame.SRCALPHA)
        pygame.draw.ellipse(self.relic_shadow_surf, (0, 0, 0, 75), (0, 0, int(22 * ZOOM), int(8 * ZOOM)))

        self.caravan_shadow_surf = pygame.Surface((int(32 * ZOOM), int(14 * ZOOM)), pygame.SRCALPHA)
        pygame.draw.ellipse(self.caravan_shadow_surf, (0, 0, 0, 80), (0, 0, int(32 * ZOOM), int(14 * ZOOM)))

        # 11. Pre-render Caravan HUD components
        self.caravan_hud_bg = pygame.Surface((360, 68), pygame.SRCALPHA)
        self.caravan_hud_bg.fill((15, 23, 42, 204))

        self.caravan_slot_active_bg = pygame.Surface((56, 34), pygame.SRCALPHA)
        self.caravan_slot_active_bg.fill((30, 41, 59, 204))

        self.caravan_slot_empty_bg = pygame.Surface((56, 34), pygame.SRCALPHA)
        self.caravan_slot_empty_bg.fill((20, 29, 47, 180))

        # 12. Pre-render Active Station Pulsing Auras (8 animation steps)
        self.cached_station_auras = []
        for step in range(8):
            pulse = (math.sin(step * (math.pi / 4)) + 1) * 0.5
            aura_w = int((32 + pulse * 6) * ZOOM)
            aura_h = int((16 + pulse * 3) * ZOOM)
            aura_s = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_s, (251, 191, 36, int(90 + pulse * 60)), (0, 0, aura_w, aura_h))
            pygame.draw.ellipse(aura_s, (255, 215, 0, int(180 + pulse * 75)), (0, 0, aura_w, aura_h), 2)
            self.cached_station_auras.append(aura_s)

        # 13. Pre-render Info Panel Glassmorphic Backdrop
        self.info_panel_bg = pygame.Surface((280, 160), pygame.SRCALPHA)
        self.info_panel_bg.fill((0, 0, 0, 180))
        pygame.draw.rect(self.info_panel_bg, (51, 65, 85, 200), (0, 0, 280, 160), 1, border_radius=6)

        # 14. Scaled Icon Cache mapping (icon_key, target_size) -> pre-scaled Surface
        self._scaled_icon_cache = {}

    # ============================================================
    # DATABASE INTEGRATION
    # ============================================================
    def load_database_questions(self):
        if not self.is_quiz_map:
            return
        try:
            if not db:
                return
            questions_result = db.get_questions(quarter=3)
            if not questions_result or len(questions_result) == 0:
                print("ℹ️ No custom database questions found for Quarter 3. Using default curriculum questions.")
                return

            mapped_questions = []
            for idx, row in enumerate(questions_result):
                prompt = row.get("prompt") or row.get("question") or ""
                opt_a = row.get("optionA") or row.get("option_a")
                opt_b = row.get("optionB") or row.get("option_b")
                opt_c = row.get("optionC") or row.get("option_c")
                opt_d = row.get("optionD") or row.get("option_d")
                correct_answer = row.get("correctAnswer") or row.get("correct_answer")

                raw_options = [opt for opt in [opt_a, opt_b, opt_c, opt_d] if opt is not None and str(opt).strip() != ""]
                if not raw_options:
                    continue

                choices = []
                choice_letters = ["A", "B", "C", "D"]
                for c_i, opt in enumerate(raw_options):
                    prefix = f"{choice_letters[c_i]}. " if c_i < len(choice_letters) else f"{c_i+1}. "
                    choices.append(f"{prefix}{opt}")

                ans = str(correct_answer).upper().strip()
                if ans == "A" or ans == "OPTION_A" or ans.endswith("A") or ans == "0":
                    correct_idx = 0
                elif ans == "B" or ans == "OPTION_B" or ans.endswith("B") or ans == "1":
                    correct_idx = 1
                elif ans == "C" or ans == "OPTION_C" or ans.endswith("C") or ans == "2":
                    correct_idx = 2
                elif ans == "D" or ans == "OPTION_D" or ans.endswith("D") or ans == "3":
                    correct_idx = 3
                else:
                    correct_idx = 0
                    for c_i, opt in enumerate(raw_options):
                        if opt and str(opt).strip().lower() == ans.lower():
                            correct_idx = c_i
                            break

                station_num = idx + 1
                mapped_questions.append({
                    "station": station_num,
                    "title": f"⭐ CHALLENGE {station_num}",
                    "question": prompt,
                    "q_type": "multiple_choice",
                    "choices": choices,
                    "correct": correct_idx,
                    "hint": row.get("hint") or "Examine the choices carefully and select the best answer below! ⭐"
                })

            if mapped_questions:
                for i in range(min(5, len(mapped_questions))):
                    if i < len(self.quiz_questions):
                        orig = self.quiz_questions[i]
                        if "visual_type" in orig and not mapped_questions[i].get("visual_type"):
                            mapped_questions[i]["visual_type"] = orig["visual_type"]
                        self.quiz_questions[i] = mapped_questions[i]
                    else:
                        self.quiz_questions.append(mapped_questions[i])

                print(f"✅ Successfully loaded {len(mapped_questions)} dynamic question(s) from Database for Quarter 3!")
        except Exception as e:
            print(f"⚠️ Exception loading database questions for Quarter 3: {e}")

    def save_results_to_database(self):
        if not self.is_quiz_map:
            return
        try:
            if not db:
                return
            student_db_id = getattr(self.main_menu, 'student_db_id', None)
            if not student_db_id:
                print("⚠️ No student_db_id available in main_menu. Skipping database record.")
                return
            total_questions = min(5, len(self.quiz_questions))
            correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
            percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 0.0
            score = float(correct_answers)

            assessment_id = db.get_assessment_id(quarter=3)
            if assessment_id:
                print(f"📝 Linked Quarter 3 result to Assessment ID: {assessment_id}")

            feedback_msg = f"Completed Quarter 3 (Math Explorations). Answered {correct_answers} of {total_questions} questions correctly on the first attempt."
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
                print(f"🎉 Successfully saved Quarter 3 Game Result to Database for Student DB ID {student_db_id}!")
                print(f"   Score: {score}/{total_questions} ({percentage}%)")
            else:
                print("⚠️ Failed to save Quarter 3 game results via Database API.")
        except Exception as e:
            print(f"⚠️ Exception saving Quarter 3 game results: {e}")

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
                    pass
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
        def load_tile(filename, is_q3=False):
            if is_q3:
                path = os.path.join(self.QUARTER3_TILES_PATH, filename)
            else:
                path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                w_orig, h_orig = image.get_size()
                
                # Custom scaling rules
                if "tree" in filename:
                    if "very_tall" in filename:
                        target_h = 160  # 5 tiles tall
                    elif "medium_clean" in filename:
                        target_h = 128  # 4 tiles tall
                    elif "medium_moss" in filename or "medium_clean" not in filename:
                        target_h = 96   # 3 tiles tall
                    else:
                        target_h = 110
                    target_w = max(1, int(w_orig * (target_h / h_orig)))
                    image = pygame.transform.scale(image, (target_w, target_h))
                elif ("ruin" in filename or "rock" in filename) and not any(filename.startswith(f"ruin{i}") for i in range(1, 11)):
                    # Ruins/walls/stones: scale by 2.0
                    image = pygame.transform.scale(image, (int(w_orig * 2), int(h_orig * 2)))
                else:
                    # Everything else: exactly 1 block tall (32x32)
                    image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                return image
            except Exception:
                if is_q3:
                    return load_tile(filename, is_q3=False)
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

        # Overwrite G and T with Q3 tiles for Quarter 3 Maps
        tiles["G"] = load_tile("sand.png", is_q3=True)
        tiles["T"] = load_tile("dead_tree.png", is_q3=True)
        for k in ["1", "2", "3", "4", "5", "P"]:
            tiles[k] = tiles["G"]

        # New Q3 tiles
        q3_tiles = {
            "w": "tumbleweed.png",
            "Z": "brick1.png",
            "M": "brick2.png",
            "n": "brick3.png",
            "s": "brick4.png",
            "t": "brick5.png",
            "J": "brick6.png",
            "Q": "brick7.png",
            "V": "brick8.png",
            "X": "brick9.png",
            "Y": "brick10.png"
        }

        for key, filename in q3_tiles.items():
            tiles[key] = load_tile(filename, is_q3=True)

        # Golden Aqueduct Causeway Bridge Tile 'B'
        golden_bridge = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        golden_bridge.fill((217, 119, 6))
        pygame.draw.rect(golden_bridge, (245, 158, 11), (2, 2, 28, 28), border_radius=4)
        pygame.draw.rect(golden_bridge, (251, 191, 36), (4, 4, 24, 24), border_radius=3)
        pygame.draw.rect(golden_bridge, (254, 240, 138), (4, 4, 24, 24), 2, border_radius=3)
        pygame.draw.line(golden_bridge, (217, 119, 6), (4, 16), (28, 16), 2)
        pygame.draw.line(golden_bridge, (217, 119, 6), (16, 4), (16, 28), 2)
        tiles["B"] = golden_bridge

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
        # Load Oldman
        oldman_path = os.path.join(self.NPC_PATH_OLDMAN, "oldman.png")
        try:
            if os.path.exists(oldman_path):
                img = pygame.image.load(oldman_path).convert_alpha()
                self.npc_oldman_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"✅ Loaded Oldman sprite")
            else:
                print(f"⚠️ Oldman sprite not found at: {oldman_path}")
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((200, 200, 200))
                pygame.draw.circle(placeholder, (0, 0, 0), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
                pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4), 3)
                pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2 + 4, TILE_SIZE // 2 - 4), 3)
                font = pygame.font.SysFont(None, 10)
                text = font.render("OLD", True, (0, 0, 0))
                placeholder.blit(text, (4, TILE_SIZE - 12))
                self.npc_oldman_sprite = placeholder
        except Exception as e:
            print(f"❌ Error loading Oldman: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((200, 200, 200))
            self.npc_oldman_sprite = placeholder

        pass

    def load_station_shape_npcs(self):
        """Load 8-frame animations for 5 shape NPCs assigned to stations 1-5"""
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
                    print(f"⚠️ Error loading frame {path}: {e}")
            if not frames:
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((255, 180, 0))
                frames.append(placeholder)
            return frames

        self.station_npcs = {
            1: {"name": "Number 1 Guardian", "frames": load_frames(self.NPC_PATH_NUM1, "number1npc"), "anim_frame": 0, "anim_timer": 0},
            2: {"name": "Number 2 Guardian", "frames": load_frames(self.NPC_PATH_NUM2, "number2npc"), "anim_frame": 0, "anim_timer": 0},
            3: {"name": "Number 3 Guardian", "frames": load_frames(self.NPC_PATH_NUM3, "number3npc"), "anim_frame": 0, "anim_timer": 0},
            4: {"name": "Number 4 Guardian", "frames": load_frames(self.NPC_PATH_NUM4, "number4npc"), "anim_frame": 0, "anim_timer": 0},
            5: {"name": "Number 5 Guardian", "frames": load_frames(self.NPC_PATH_NUM5, "number5npc"), "anim_frame": 0, "anim_timer": 0},
        }
        print("✅ Loaded 5 Animated Number Character Station NPCs (Number 1-5)")

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
            self.animation = Quarter3.PortalSpriteAnimation(
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
    def clear_portal_overlapping_tiles(self):
        """Only remove the 2 brick wall tiles exactly at the portal spawn position when activated"""
        for portal in self.portals:
            p_x, p_y = portal.x, portal.y
            w, h = portal.width_tiles, portal.height_tiles
            for r in range(p_y, min(len(self.render_map), p_y + h)):
                row_list = list(self.render_map[r])
                modified = False
                for c in range(p_x, min(len(row_list), p_x + w)):
                    if row_list[c] in ['Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y']:
                        row_list[c] = 'G'
                        modified = True
                if modified:
                    self.render_map[r] = ''.join(row_list)

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

    def find_path(self, start, end):
        """BFS pathfinder from start (col, row) to end (col, row) on the grid"""
        import collections
        
        # Clamp start/end to valid grid range
        start = (max(0, min(self.COLS - 1, int(start[0]))), max(0, min(self.ROWS - 1, int(start[1]))))
        end = (max(0, min(self.COLS - 1, int(end[0]))), max(0, min(self.ROWS - 1, int(end[1]))))
        
        # If start tile is not walkable, search nearest walkable neighbor
        if start[1] < len(self.game_map) and start[0] < len(self.game_map[start[1]]):
            if self.game_map[start[1]][start[0]] not in self.WALKABLE_TILES:
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    sx, sy = start[0] + dx, start[1] + dy
                    if 0 <= sy < self.ROWS and 0 <= sx < self.COLS:
                        if sy < len(self.game_map) and sx < len(self.game_map[sy]):
                            if self.game_map[sy][sx] in self.WALKABLE_TILES:
                                start = (sx, sy)
                                break

        # If end tile is not walkable, search nearest walkable neighbor
        if end[1] < len(self.game_map) and end[0] < len(self.game_map[end[1]]):
            if self.game_map[end[1]][end[0]] not in self.WALKABLE_TILES:
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, 1)]:
                    ex, ey = end[0] + dx, end[1] + dy
                    if 0 <= ey < self.ROWS and 0 <= ex < self.COLS:
                        if ey < len(self.game_map) and ex < len(self.game_map[ey]):
                            if self.game_map[ey][ex] in self.WALKABLE_TILES:
                                end = (ex, ey)
                                break

        if start == end:
            return [start]

        queue = collections.deque([[start]])
        seen = {start}
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
                        if (tile in self.WALKABLE_TILES or nxt == end) and nxt not in seen:
                            seen.add(nxt)
                            queue.append(path + [nxt])
        return []

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
    # RETURN TO STAGE SELECT
    # ============================================================
    def return_to_stage_select(self):
        """Return to the stage select screen"""
        if self.main_menu:
            # Save results to database on completion
            self.save_results_to_database()
            self.main_menu.current_screen = "stage_select"
            self.main_menu.quarter3 = None
            try:
                from screens.stageselect import StageSelect
            except ImportError:
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
                if self.quiz_state < 6:
                    return False
                print(f"🎯 Goal reached! Returning to stage select...")
                self.return_to_stage_select()
                return True

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
        if hasattr(self, 'camera_pan_active') and self.camera_pan_active:
            # During cinematic drone camera pan, camera position is controlled by pan routine
            min_cam_x = 0
            max_cam_x = max(0, self.MAP_WIDTH - self.width / ZOOM)
            min_cam_y = 0
            max_cam_y = max(0, self.MAP_HEIGHT - self.height / ZOOM)
            self.camera_x = max(min_cam_x, min(self.camera_x, max_cam_x))
            self.camera_y = max(min_cam_y, min(self.camera_y, max_cam_y))
            return

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

    def submit_identification_answer(self):
        """Validates student's answer in Identification Question Mode"""
        import random
        q_data = self.quiz_questions[self.current_question_index]
        clean_input = self.ident_input_text.strip().lower().replace(" ", "")

        if not clean_input:
            self.wrong_feedback_msg = "Please type or tap an answer using the keypad first! ⭐"
            return

        is_correct = False
        valid_answers = q_data.get("ident_answers", [])
        for ans in valid_answers:
            if clean_input == ans.strip().lower().replace(" ", ""):
                is_correct = True
                break

        if is_correct:
            self.current_correct_phrase = random.choice(self.correct_phrases)
            self.quiz_state = 3
            self.eliminated_choices.clear()
            self.wrong_feedback_msg = ""
            if self.success_sound:
                self.success_sound.play()
            print(f"✅ Correct identification answer submitted: {self.ident_input_text}")
        else:
            if hasattr(self, 'first_attempt_correct') and (self.current_question_index + 1) in self.first_attempt_correct:
                self.first_attempt_correct[self.current_question_index + 1] = False
            
            self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
            if self.station_attempts[self.quiz_station_index] < 2:
                self.quiz_state = 2
                print(f"❌ Incorrect identification answer submitted: {self.ident_input_text} (Attempt 1 of 2)")
            else:
                self.quiz_state = 4
                print(f"❌ Incorrect identification on 2nd try! Out of tries. Station {self.quiz_station_index} cleared for progression.")
                
            if self.snap_sound:
                self.snap_sound.play()
            self.wrong_feedback_msg = f"Almost there! Check the visual model ({q_data.get('hint', '')}) and try again! 💡"
            print(f"❌ Incorrect identification answer: '{self.ident_input_text}'. Expected one of: {valid_answers}")
            
        from db.save_system import save_student_progress
        save_student_progress(self.main_menu)

    def advance_station_progress(self):
        """Executes guaranteed reward & station progression after answering or out-of-tries"""
        import random
        self.eliminated_choices.clear()
        self.wrong_feedback_msg = ""
        self.ident_input_text = ""

        # Map 7 Reward: Load Cargo onto Explorer's Caravan
        if self.is_caravan_mode and self.quiz_station_index in self.station_cargo_rewards:
            reward = self.station_cargo_rewards[self.quiz_station_index]
            self.caravan_cargo.append(reward)
            self.caravan_upgrade_banner_text = f"📦 CARAVAN UPGRADE: {reward['name']} Loaded!"
            self.caravan_upgrade_banner_sub = f"⚡ Speed Rush Activated! {reward['desc']}"
            self.caravan_upgrade_banner_timer = 4.0
            self.speed_boost_timer = 5.0  # 5 seconds of lightning sprint!

            # Spawn celebration sparkles and music notes
            for _ in range(20):
                self.caravan_sparkles.append({
                    "x": self.caravan_x + random.randint(0, 32),
                    "y": self.caravan_y + random.randint(0, 32),
                    "vx": random.uniform(-2.5, 2.5),
                    "vy": random.uniform(-3.5, -0.5),
                    "color": random.choice([(255, 255, 255), (251, 191, 36), (56, 189, 248), (239, 68, 68), (34, 197, 94)]),
                    "life": random.uniform(0.8, 1.5),
                    "rad": random.randint(3, 6)
                })
            print(f"🐪 Caravan Upgraded! Loaded {reward['name']} (Total Cargo: {len(self.caravan_cargo)}/5)")

        # Map 9 Reward: Unlock Sacred Math Keystone
        elif self.is_puzzle_hybrid_mode and self.quiz_station_index in self.citadel_keystones:
            st_num = self.quiz_station_index
            keystone = self.citadel_keystones[st_num]
            self.citadel_collected_keystones.append(keystone)
            self.citadel_banner_text = f"🏛️ SUN KEYSTONE {st_num}/5 UNLOCKED!"
            self.citadel_banner_sub = f"✨ {keystone['name']} ({keystone['math']}) slotted into Citadel Altar!"
            self.citadel_banner_timer = 4.0
            self.speed_boost_timer = 5.0

            for _ in range(25):
                self.caravan_sparkles.append({
                    "x": self.player_x + random.randint(0, 32),
                    "y": self.player_y + random.randint(0, 32),
                    "vx": random.uniform(-3, 3),
                    "vy": random.uniform(-4, 0),
                    "color": keystone["color"],
                    "life": random.uniform(1.0, 1.8),
                    "rad": random.randint(3, 7)
                })
            print(f"🏛️ Citadel Keystone {st_num} Acquired: {keystone['name']}")

        elif self.is_relic_hunt_mode:
            self.speed_boost_timer = 6.0

        # In-World Bridge Construction and Camera Pan for Map 8
        st_num = self.quiz_station_index
        if hasattr(self, 'bridge_tiles') and self.bridge_tiles and st_num <= len(self.bridge_tiles):
            bx, by = self.bridge_tiles[st_num - 1]
            if by < len(self.game_map) and bx < len(self.game_map[by]):
                self.game_map[by] = self.game_map[by][:bx] + "B" + self.game_map[by][bx+1:]
                self.render_map[by] = self.render_map[by][:bx] + "B" + self.render_map[by][bx+1:]
                self.built_bridge_count = st_num

                # Initiate Cinematic Drone Camera Pan
                self.camera_pan_active = True
                self.camera_pan_timer = 0.0
                self.camera_pan_duration = 2.4
                self.camera_pan_burst_done = False
                self.camera_pan_target_col = bx
                self.camera_pan_target_row = by
                self.camera_pan_origin_x = self.camera_x
                self.camera_pan_origin_y = self.camera_y

                t_cx = (bx * TILE_SIZE + TILE_SIZE // 2) - (self.width // 2) / ZOOM
                t_cy = (by * TILE_SIZE + TILE_SIZE // 2) - (self.height // 2) / ZOOM
                min_cam_x, max_cam_x = 0, max(0, self.MAP_WIDTH - self.width / ZOOM)
                min_cam_y, max_cam_y = 0, max(0, self.MAP_HEIGHT - self.height / ZOOM)
                self.camera_pan_dest_x = max(min_cam_x, min(t_cx, max_cam_x))
                self.camera_pan_dest_y = max(min_cam_y, min(t_cy, max_cam_y))

                self.quiz_state = 7  # State 7: Camera Pan sequence
                print(f"🏗️ Aqueduct Bridge Segment {st_num}/5 materialized at ({bx}, {by})! Camera panning...")
                return

        if self.quiz_station_index < 5:
            self.quiz_station_index += 1
            self.current_question_index += 1
            self.quiz_state = 0
            print(f"✅ Advanced to Quiz Station {self.quiz_station_index}")
        else:
            self.current_question_index += 1
            if self.is_puzzle_hybrid_mode:
                # In Map 9 Hybrid mode, completing question 5 activates the Grand Sun Temple Altar Jigsaw!
                self.quiz_state = 8
                self.init_sun_relic_puzzle()
                print("🏛️ All 5 Map 9 Stations Solved! Grand Sun Temple Altar Puzzle Opened!")
            else:
                self.quiz_state = 5

    def trigger_click(self, pos):
        if getattr(self, 'time_up_dialog_active', False):
            box_w, box_h = 560, 260
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            retry_rect = pygame.Rect(box_x + 40, box_y + 175, 220, 46)
            exit_rect = pygame.Rect(box_x + box_w - 260, box_y + 175, 220, 46)
            if retry_rect.collidepoint(pos):
                self.stage_time_remaining = 600.0
                self.time_up_dialog_active = False
                from screens.quarter3 import Quarter3
                self.main_menu.quarter3 = Quarter3(self.screen, self.main_menu, "map7.txt")
                return
            elif exit_rect.collidepoint(pos):
                self.time_up_dialog_active = False
                from screens.stageselect import StageSelect
                self.main_menu.current_screen = "stage_select"
                self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
                self.main_menu.quarter3 = None
                return
            return

        import random
        from db.save_system import save_student_progress
        
        # State 1: Multiple Choice Answer Selection (No icons)
        if self.quiz_state == 1:
            box_w, box_h = 580, 380
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            q_data = self.quiz_questions[self.current_question_index]

            button_w, button_h = 500, 44
            button_x = box_x + (box_w - button_w) // 2
            button_y_start = box_y + 130
            spacing = 52

            for i, choice in enumerate(q_data["choices"][:4]):
                if i in self.eliminated_choices:
                    continue

                b_y = button_y_start + i * spacing
                btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)

                if btn_rect.collidepoint(pos):
                    if i == q_data["correct"]:
                        self.current_correct_phrase = random.choice(self.correct_phrases)
                        self.quiz_state = 3
                        self.eliminated_choices.clear()
                        self.wrong_feedback_msg = ""
                        if self.success_sound:
                            self.success_sound.play()
                        print(f"✅ Correct answer selected: {q_data['choices'][i]}")
                    else:
                        # 50:50 Wizard Hint: eliminate the clicked wrong choice and give gentle encouragement
                        self.eliminated_choices.add(i)
                        self.wrong_feedback_msg = "Almost there! Try picking again! ⭐"
                        if hasattr(self, 'first_attempt_correct') and (self.current_question_index + 1) in self.first_attempt_correct:
                            self.first_attempt_correct[self.current_question_index + 1] = False
                        
                        self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
                        if self.station_attempts[self.quiz_station_index] < 2:
                            self.quiz_state = 2
                            print(f"❌ Incorrect choice selected: {q_data['choices'][i]} (Attempt 1 of 2)")
                        else:
                            self.quiz_state = 4
                            print(f"❌ Incorrect choice on 2nd try! Out of tries. Station {self.quiz_station_index} cleared for progression.")
                        
                        if self.snap_sound:
                            self.snap_sound.play()
                    save_student_progress(self.main_menu)
                    break
                    
        # State 2: Retry click fallback
        elif self.quiz_state == 2:
            box_w, box_h = 600, 290
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 190, 220, 46)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                save_student_progress(self.main_menu)
            
        # State 3: Correct answer transition screen click -> Award Cargo & Speed Rush!
        elif self.quiz_state == 3:
            box_w, box_h = 600, 280
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 180, 220, 46)
            if btn_rect.collidepoint(pos):
                self.advance_station_progress()
                save_student_progress(self.main_menu)

        # State 4: Out of tries reveal screen click -> Guaranteed progression!
        elif self.quiz_state == 4:
            box_w, box_h = 620, 290
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 190, 220, 46)
            if btn_rect.collidepoint(pos):
                self.advance_station_progress()
                save_student_progress(self.main_menu)

        # State 9: Station Hands-On Mini-Puzzle Click Handling
        elif self.quiz_state == 9:
            self.handle_station_mini_puzzle_click(pos)

        # State 8: Sun Relic Altar Jigsaw Click Handling
        elif self.quiz_state == 8:
            if self.sun_relic_solved:
                self.quiz_state = 6
                self.clear_portal_overlapping_tiles()
                return
            if not self.dragged_slab:
                for slab in self.sun_relic_slabs:
                    if not slab["is_placed"]:
                        s_rect = pygame.Rect(slab["x"], slab["y"], slab["slot_w"], slab["slot_h"])
                        if s_rect.collidepoint(pos):
                            # Click-to-slot magnetic snap
                            slab["x"] = slab["target_x"]
                            slab["y"] = slab["target_y"]
                            slab["is_placed"] = True
                            if self.snap_sound:
                                self.snap_sound.play()
                            print(f"🧩 Slab {slab['index']} ({slab['config']['math']}) clicked into altar!")
                            if all(s["is_placed"] for s in self.sun_relic_slabs):
                                self.sun_relic_solved = True
                                self.sun_relic_solved_time = pygame.time.get_ticks()
                                if self.success_sound:
                                    self.success_sound.play()
                            break
                
        # State 5: Final speech click -> Hop onto Caravan and Ride to Goal Portal!
        elif self.quiz_state == 5:
            box_w, box_h = 640, 340
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 245, 220, 46)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 6
                self.clear_portal_overlapping_tiles()
                self.save_results_to_database()
                save_student_progress(self.main_menu)
                
                # Calculate BFS path from current Caravan position to Goal Portal
                start_tile = (int((self.caravan_x + TILE_SIZE // 2) // TILE_SIZE), 
                              int((self.caravan_y + TILE_SIZE // 2) // TILE_SIZE))
                goal_tile = (47, 16)
                if self.portals:
                    goal_tile = (self.portals[0].x, self.portals[0].y)
                
                self.caravan_ride_path = self.find_path(start_tile, goal_tile)
                self.caravan_ride_index = 0
                self.caravan_riding = True
                self.caravan_upgrade_banner_text = "👑 ROYAL EXPEDITION COMPLETE! 🌟"
                self.caravan_upgrade_banner_sub = "Caravan carrying player to the Portal! 🚀"
                self.caravan_upgrade_banner_timer = 999.0
                print(f"🚀 Caravan Ride Started! Path length: {len(self.caravan_ride_path)} tiles to {goal_tile}")

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1

        # 10-Minute Stage Timer
        if not getattr(self, 'completed', False) and not self.time_up_dialog_active:
            self.stage_time_remaining = max(0.0, self.stage_time_remaining - dt)
            if self.stage_time_remaining <= 0.0:
                self.stage_time_remaining = 0.0
                self.time_up_dialog_active = True
                print("⏰ Quarter 3 Time's Up!")

        if self.time_up_dialog_active:
            return

        # Update animations for all 5 Shape Station NPCs
        if hasattr(self, 'station_npcs'):
            for num, data in self.station_npcs.items():
                data["anim_timer"] += 1
                if data["anim_timer"] >= 6:
                    data["anim_timer"] = 0
                    data["anim_frame"] = (data["anim_frame"] + 1) % len(data["frames"])

        if hasattr(self, 'player_block_timer') and self.player_block_timer > 0:
            self.player_block_timer -= dt

        if self.npc_bromen_sprites and self.npc_bromen_found:
            self.npc_bromen_anim_timer += 1
            if self.npc_bromen_anim_timer >= 5:
                self.npc_bromen_anim_timer = 0
                self.npc_bromen_anim_frame = (self.npc_bromen_anim_frame + 1) % len(self.npc_bromen_sprites)

        # Relic Hunt Active Loop in Map 8
        if self.is_relic_hunt_mode and self.quiz_state == 0:
            self.update_relic_hunt(dt)

        # Proximity interaction check for active Station NPC (Exact 42px radius)
        if self.quiz_state == 0 and hasattr(self, 'quiz_stations') and self.quiz_station_index in self.quiz_stations:
            st_x, st_y = self.quiz_stations[self.quiz_station_index]
            npc_center_x = st_x * TILE_SIZE + TILE_SIZE // 2
            npc_center_y = st_y * TILE_SIZE + TILE_SIZE // 2
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            dist = math.hypot(player_center_x - npc_center_x, player_center_y - npc_center_y)
            if dist < 42:
                if self.is_relic_hunt_mode:
                    if self.relic_collected_count >= self.relic_target_count:
                        # Collectibles complete -> Open Guardian Question Trial
                        self.quiz_state = 1
                        self.current_question_index = self.quiz_station_index - 1
                        self.selected_choice_index = -1
                        self.eliminated_choices.clear()
                        self.wrong_feedback_msg = ""
                        self.ident_input_text = ""
                        print(f"📜 Guardian {self.quiz_station_index} Challenge Opened! (Type: {self.quiz_questions[self.current_question_index].get('q_type', 'multiple_choice')})")
                    else:
                        # Still missing required supplies in the maze
                        needed = self.relic_target_count - self.relic_collected_count
                        self.relic_banner_text = f"🔒 Shrine Needs {needed} more {self.relic_item_type.upper()}S!"
                        self.relic_banner_sub = f"Collect all supplies in the desert maze before taking the Guardian's Trial!"
                        self.relic_banner_timer = 2.0
                else:
                    # Pure Multiple Choice Question Mode (Map 7 & Map 9)
                    self.quiz_state = 1
                    self.current_question_index = self.quiz_station_index - 1
                    self.selected_choice_index = -1
                    self.eliminated_choices.clear()
                    self.wrong_feedback_msg = ""
                    self.ident_input_text = ""
                    print(f"📜 Station {self.quiz_station_index} Multiple Choice Challenge Opened!")

        # Skeleton walking sequence along BFS path
        if self.quiz_state == 4:
            if hasattr(self, 'npc_skeleton_path') and self.npc_skeleton_path_index < len(self.npc_skeleton_path):
                t_col, t_row = self.npc_skeleton_path[self.npc_skeleton_path_index]
                target_x = t_col * TILE_SIZE
                target_y = t_row * TILE_SIZE
                
                dx = target_x - self.npc_skeleton_x
                dy = target_y - self.npc_skeleton_y
                
                move_speed = 2  # Walk speed: 2 pixels per frame
                
                if abs(dx) > abs(dy):
                    self.npc_skeleton_dir = "right" if dx > 0 else "left"
                else:
                    self.npc_skeleton_dir = "down" if dy > 0 else "up"
                
                if abs(dx) <= move_speed and abs(dy) <= move_speed:
                    self.npc_skeleton_x = target_x
                    self.npc_skeleton_y = target_y
                    self.npc_skeleton_tile_x = t_col
                    self.npc_skeleton_tile_y = t_row
                    self.npc_skeleton_path_index += 1
                else:
                    if dx != 0:
                        self.npc_skeleton_x += move_speed if dx > 0 else -move_speed
                    if dy != 0:
                        self.npc_skeleton_y += move_speed if dy > 0 else -move_speed
                
                self.npc_skeleton_anim_timer += 1
                if self.npc_skeleton_anim_timer >= 10:
                    self.npc_skeleton_anim_timer = 0
                    self.npc_skeleton_anim_frame = (self.npc_skeleton_anim_frame + 1) % 3
            else:
                self.quiz_state = 0
                self.npc_skeleton_anim_frame = 0
                self.npc_skeleton_anim_timer = 0
                self.npc_skeleton_dir = self.station_directions.get(self.quiz_station_index, "right")



        # State 7: Camera Pan sequence for in-world bridge construction
        if self.quiz_state == 7:
            self.camera_pan_timer += dt
            t = self.camera_pan_timer / self.camera_pan_duration
            
            # Phase 1: 0.0 - 0.8s -> Pan from player to bridge
            if t < 0.33:
                sub_t = t / 0.33
                smooth = (1 - math.cos(sub_t * math.pi)) / 2
                self.camera_x = self.camera_pan_origin_x + (self.camera_pan_dest_x - self.camera_pan_origin_x) * smooth
                self.camera_y = self.camera_pan_origin_y + (self.camera_pan_dest_y - self.camera_pan_origin_y) * smooth
            # Phase 2: 0.33 - 0.66s -> Hold and burst sparkles on newly materialized stone
            elif t < 0.66:
                self.camera_x = self.camera_pan_dest_x
                self.camera_y = self.camera_pan_dest_y
                if not self.camera_pan_burst_done:
                    self.camera_pan_burst_done = True
                    if self.snap_sound:
                        self.snap_sound.play()
                    # Spawn 25 golden dust particles at the bridge tile
                    tile_world_x = self.camera_pan_target_col * TILE_SIZE
                    tile_world_y = self.camera_pan_target_row * TILE_SIZE
                    for _ in range(25):
                        self.caravan_sparkles.append({
                            "x": tile_world_x + random.randint(0, 32),
                            "y": tile_world_y + random.randint(0, 32),
                            "vx": random.uniform(-3, 3),
                            "vy": random.uniform(-4, 0),
                            "color": random.choice([(255, 215, 0), (251, 191, 36), (245, 158, 11), (255, 255, 255)]),
                            "life": random.uniform(1.0, 1.8),
                            "rad": random.randint(3, 7)
                        })
            # Phase 3: 0.66 - 1.0s -> Pan back to player
            else:
                sub_t = (t - 0.66) / 0.34
                smooth = (1 - math.cos(sub_t * math.pi)) / 2
                self.camera_x = self.camera_pan_dest_x + (self.camera_pan_origin_x - self.camera_pan_dest_x) * smooth
                self.camera_y = self.camera_pan_dest_y + (self.camera_pan_origin_y - self.camera_pan_dest_y) * smooth
                
            if self.camera_pan_timer >= self.camera_pan_duration:
                self.camera_pan_active = False
                if self.quiz_station_index < 5:
                    self.quiz_station_index += 1
                    self.current_question_index += 1
                    self.quiz_state = 0
                    if self.is_relic_hunt_mode:
                        self.spawn_relic_stage(self.quiz_station_index)
                else:
                    if self.is_relic_hunt_mode:
                        self.quiz_state = 6
                        self.quiz_station_index = 6
                        self.clear_portal_overlapping_tiles()
                        self.relic_banner_text = "☀️ GOLDEN CAUSEWAY COMPLETE!"
                        self.relic_banner_sub = "The bridge is open! Cross to the Eastern Sun Portal Sanctum!"
                        self.relic_banner_timer = 5.0
                    else:
                        # Station 5 answered and 5th bridge tile built -> Open Sun Relic Altar!
                        self.quiz_state = 8
                        self.init_sun_relic_puzzle()

        # State 8: Sun Relic Altar Jigsaw Update
        if self.quiz_state == 8:
            self.update_sun_relic_puzzle(dt)

        # State 9: Station Hands-On Mini-Puzzle Update
        if self.quiz_state == 9:
            self.update_station_mini_puzzle(dt)
        if self.caravan_upgrade_banner_timer > 0:
            self.caravan_upgrade_banner_timer -= dt
            if self.caravan_upgrade_banner_timer <= 0:
                self.caravan_upgrade_banner_text = ""

        if self.citadel_banner_timer > 0:
            self.citadel_banner_timer -= dt
            if self.citadel_banner_timer <= 0:
                self.citadel_banner_text = ""

        # Update Speed Boost & Wind Sprites
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= dt
            if random.random() < 0.35:
                self.caravan_sparkles.append({
                    "x": self.player_x + random.randint(4, 28),
                    "y": self.player_y + random.randint(20, 32),
                    "vx": random.uniform(-1.2, 1.2),
                    "vy": random.uniform(-2.0, -0.5),
                    "color": random.choice([(255, 255, 255), (251, 191, 36), (56, 189, 248), (34, 197, 94)]),
                    "life": 0.6,
                    "rad": random.randint(2, 5)
                })

        # Update Caravan Sparkles
        surviving_sparkles = []
        for p in self.caravan_sparkles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.10 # gravity
            p["life"] -= dt
            if p["life"] > 0:
                surviving_sparkles.append(p)
        self.caravan_sparkles = surviving_sparkles

        # Update Caravan Music Notes (Map 7 only)
        if not self.is_relic_hunt_mode and len(self.caravan_cargo) > 0 and random.random() < 0.04:
            self.caravan_music_notes.append({
                "x": self.caravan_x + random.randint(8, 24),
                "y": self.caravan_y - 6,
                "vx": random.uniform(-0.6, 0.6),
                "vy": -1.2,
                "char": random.choice(["🎵", "🎶", "✨", "💖", "⭐"]),
                "color": random.choice([(255, 215, 0), (244, 114, 182), (56, 189, 248), (34, 197, 94)]),
                "life": 1.2
            })

        surviving_notes = []
        for n in self.caravan_music_notes:
            n["x"] += n["vx"]
            n["y"] += n["vy"]
            n["life"] -= dt
            if n["life"] > 0:
                surviving_notes.append(n)
        self.caravan_music_notes = surviving_notes

        # Automatic Caravan Ride to Goal Portal Sequence
        if self.caravan_riding and self.quiz_state == 6:
            if self.caravan_ride_path and self.caravan_ride_index < len(self.caravan_ride_path):
                t_col, t_row = self.caravan_ride_path[self.caravan_ride_index]
                target_x = t_col * TILE_SIZE
                target_y = t_row * TILE_SIZE
                
                dx = target_x - self.caravan_x
                dy = target_y - self.caravan_y
                ride_speed = 6  # Swift celebratory victory gallop
                
                if abs(dx) > abs(dy):
                    self.caravan_dir = "right" if dx > 0 else "left"
                else:
                    self.caravan_dir = "down" if dy > 0 else "up"
                    
                if abs(dx) <= ride_speed and abs(dy) <= ride_speed:
                    self.caravan_x = target_x
                    self.caravan_y = target_y
                    self.caravan_ride_index += 1
                else:
                    if dx != 0:
                        self.caravan_x += ride_speed if dx > 0 else -ride_speed
                    if dy != 0:
                        self.caravan_y += ride_speed if dy > 0 else -ride_speed
                        
                self.caravan_wheel_rot += 0.35
                self.caravan_bob_timer += 0.25
                
                # Player rides comfortably on the Caravan!
                self.player_x = self.caravan_x
                self.player_y = self.caravan_y - 8 + math.sin(self.caravan_bob_timer) * 2
                self.player_dir = self.caravan_dir
                
                # Burst celebration sparkles along the ride
                if random.random() < 0.45:
                    self.caravan_sparkles.append({
                        "x": self.caravan_x + random.randint(4, 28),
                        "y": self.caravan_y + random.randint(10, 24),
                        "vx": random.uniform(-1.5, 1.5),
                        "vy": random.uniform(-2.5, -0.5),
                        "color": random.choice([(255, 255, 255), (251, 191, 36), (56, 189, 248), (239, 68, 68), (34, 197, 94)]),
                        "life": 0.8,
                        "rad": random.randint(3, 5)
                    })
            else:
                # Reached Portal! Finish level and return to stage select
                print("🎯 Caravan safely arrived at Goal Portal! Returning to stage select...")
                self.caravan_riding = False
                self.return_to_stage_select()
                return
        elif self.is_caravan_mode:
            # Update Caravan Follower AI during normal gameplay (Map 7 only)
            if len(self.player_trail) >= 12:
                tx, ty, tdir = self.player_trail[-12]
                dx = tx - self.caravan_x
                dy = ty - self.caravan_y
                self.caravan_x += dx * 0.16
                self.caravan_y += dy * 0.16
                if abs(dx) > abs(dy):
                    self.caravan_dir = "right" if dx > 0 else "left"
                elif abs(dy) > 1:
                    self.caravan_dir = "down" if dy > 0 else "up"
                if abs(dx) > 0.5 or abs(dy) > 0.5:
                    self.caravan_wheel_rot += 0.25
                    self.caravan_bob_timer += 0.20

        self.update_player_movement()
        self.check_portal_teleport_on_hold()

        for portal in self.portals:
            portal.update_animation()

        self.update_camera()

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        if self.caravan_riding or self.quiz_state in [1, 2, 3, 4, 5, 8, 9] or (hasattr(self, 'player_block_timer') and self.player_block_timer > 0):
            self.anim_frame = 0
            return

        vx, vy = 0, 0
        base_speed = SPEED * (1.65 if self.speed_boost_timer > 0 else 1.0)

        # Hand Gesture / Cursor Directional Controls (Pure Gesture Navigation)
        center_x, center_y = self.width // 2, self.height // 2
        cursor_x, cursor_y = self.cursor_pos
        dx = cursor_x - center_x
        dy = cursor_y - center_y

        # Dynamic speed scaling: faster when hand is stretched further out
        dist_factor = 1.3 if (abs(dx) > 160 or abs(dy) > 160) else 1.0
        g_speed = base_speed * dist_factor

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
            self.player_trail.append((self.player_x, self.player_y, self.player_dir))
            self.anim_timer += 1
            if self.anim_timer >= (5 if self.speed_boost_timer > 0 else 8):
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_frame = 0

    # ============================================================
    # DRAW MATH THEME BACKDROP (60 FPS Pre-Rendered Cache)
    # ============================================================
    def draw_math_background(self):
        self.screen.blit(self.cached_math_bg, (0, 0))

    # ============================================================
    # DRAW TILE (Direct Pre-Scaled Blit - Zero Runtime Allocations)
    # ============================================================
    def draw_tile(self, c, world_x, world_y):
        screen_x = int((world_x - self.camera_x) * ZOOM)
        screen_y = int((world_y - self.camera_y) * ZOOM)

        margin = self.scaled_tile_size
        if -margin <= screen_x <= self.width and -margin <= screen_y <= self.height:
            image = self.scaled_tile_images.get(c, self.scaled_fallback_tile)
            self.screen.blit(image, (screen_x, screen_y))

    # ============================================================
    # DRAW NPC (Direct Pre-Scaled Blit)
    # ============================================================
    def draw_npc_animated(self, x, y, sprites, anim_frame):
        if not sprites:
            return
        screen_x = int((x - self.camera_x) * ZOOM)
        screen_y = int((y - self.camera_y) * ZOOM)

        if -self.scaled_tile_size <= screen_x <= self.width + self.scaled_tile_size and \
           -self.scaled_tile_size <= screen_y <= self.height + self.scaled_tile_size:
            frame_index = min(anim_frame, len(sprites) - 1)
            self.screen.blit(sprites[frame_index], (screen_x, screen_y))

    def draw_npc_static(self, x, y, sprite):
        if sprite is None:
            return
        screen_x = int((x - self.camera_x) * ZOOM)
        screen_y = int((y - self.camera_y) * ZOOM)

        if -self.scaled_tile_size <= screen_x <= self.width + self.scaled_tile_size and \
           -self.scaled_tile_size <= screen_y <= self.height + self.scaled_tile_size:
            self.screen.blit(sprite, (screen_x, screen_y))

    # ============================================================
    # DRAW PLAYER (Direct Pre-Scaled Blit)
    # ============================================================
    def draw_player(self):
        screen_x = int((self.player_x - self.camera_x) * ZOOM)
        screen_y = int((self.player_y - self.camera_y) * ZOOM)

        if -self.scaled_tile_size <= screen_x <= self.width + self.scaled_tile_size and \
           -self.scaled_tile_size <= screen_y <= self.height + self.scaled_tile_size:
            sprite = self.scaled_player_sprites[self.player_dir][self.anim_frame]
            self.screen.blit(sprite, (screen_x, screen_y))

    # ============================================================
    # DRAW
    # ============================================================
    def draw(self):
        self.draw_math_background()

        start_col = max(0, int(self.camera_x / TILE_SIZE) - 2)
        end_col = min(self.COLS, int((self.camera_x + self.width / ZOOM) / TILE_SIZE) + 3)
        start_row = max(0, int(self.camera_y / TILE_SIZE) - 2)
        end_row = min(self.ROWS, int((self.camera_y + self.height / ZOOM) / TILE_SIZE) + 3)

        # Draw visible tiles using render_map (First pass: Skip trees/tumbleweeds and draw sand under them)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    # If it's a tree, tumbleweed, or one of the brick tiles, draw sand under it first
                    if tile_char in ['T', 'w', 'Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y']:
                        self.draw_tile('G', col * TILE_SIZE, row * TILE_SIZE)
                    
                    # Now draw the actual tile (unless it is tree/tumbleweed, which are drawn in second pass)
                    if tile_char != 'T' and tile_char != 'w':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)



        if self.npc_bromen_found:
            self.draw_npc_animated(self.npc_bromen_x, self.npc_bromen_y,
                                   self.npc_bromen_sprites, self.npc_bromen_anim_frame)

        if self.npc_oldman_found:
            self.draw_npc_static(self.npc_oldman_x, self.npc_oldman_y,
                                 self.npc_oldman_sprite)

        # Draw Station NPCs at coordinates 1, 2, 3, 4, 5 (disappear when question is completed)
        if hasattr(self, 'quiz_stations') and hasattr(self, 'station_npcs'):
            for num, pos in self.quiz_stations.items():
                # Only draw NPCs for stations that have not been completed yet
                if num in self.station_npcs and num >= self.quiz_station_index and self.quiz_state < 6:
                    data = self.station_npcs[num]
                    frame = data["frames"][data["anim_frame"]]
                    
                    # If this is the currently active station, draw pre-cached glowing interaction aura
                    if num == self.quiz_station_index and self.quiz_state == 0:
                        aura_idx = (self.frame_counter // 4) % len(self.cached_station_auras)
                        aura_surf = self.cached_station_auras[aura_idx]
                        cx = (pos[0] * TILE_SIZE + TILE_SIZE // 2 - self.camera_x) * ZOOM
                        cy = (pos[1] * TILE_SIZE + TILE_SIZE - self.camera_y) * ZOOM
                        self.screen.blit(aura_surf, (cx - aura_surf.get_width() // 2, cy - aura_surf.get_height() // 2))

                    self.draw_npc_static(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, frame)

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

        # Draw Caravan Companion Cart (Map 7 only)
        if self.is_caravan_mode:
            self.draw_caravan()

        # Draw in-world Relic Items & Pickup Sparks for Map 8
        if self.is_relic_hunt_mode:
            self.draw_relic_items()
            self.draw_relic_pickup_particles()

        self.draw_player()

        # Draw Sparkle Particles
        self.draw_caravan_sparkles()

        # Draw visible tree and tumbleweed tiles on top of everything (Second pass)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char == 'T' or tile_char == 'w':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Activated Portals on top of map tiles & trees (no brick wall overlap)
        if self.quiz_state == 6:
            for portal in self.portals:
                portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height)

        # Draw Top HUD
        if self.is_relic_hunt_mode:
            self.draw_relic_quest_hud()
            if self.relic_banner_timer > 0:
                self.draw_relic_stage_banner()
        elif self.is_puzzle_hybrid_mode:
            self.draw_citadel_hud()
            if self.citadel_banner_timer > 0:
                self.draw_citadel_banner()
        elif self.is_caravan_mode:
            # Draw Caravan Inventory HUD at top right
            self.draw_caravan_hud()

            # Draw Celebratory Upgrade Banner if active
            if self.caravan_upgrade_banner_text and self.caravan_upgrade_banner_timer > 0:
                self.draw_caravan_upgrade_banner()

        # Draw Active Objective NPC Indicator and Off-Screen Compass Pointer
        self.draw_offscreen_compass_pointer()

        # Draw quiz dialog overlays if opened
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
        elif self.quiz_state == 8:
            self.draw_sun_relic_puzzle()
        elif self.quiz_state == 9:
            self.draw_station_mini_puzzle()

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

        # Draw 10-Minute Stage Timer HUD
        self.draw_stage_timer_hud()

        # Draw Time's Up modal dialog if timer expired
        if self.time_up_dialog_active:
            self.draw_time_up_dialog()

        # Draw Objectives HUD Box at the bottom center of the screen
        if self.is_quiz_map:
            box_w, box_h = 340, 80
            box_x = (self.width - box_w) // 2
            box_y = self.height - box_h - 20
            
            # Translucent slate blue background (alpha = 190)
            self.screen.blit(self.obj_hud_bg, (box_x, box_y))
            
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

            self.screen.blit(self.info_panel_bg, (6, 6))
            y_offset = 10
            for line in info_lines:
                text = self.small_font.render(line, True, (255, 255, 255))
                self.screen.blit(text, (12, y_offset))
                y_offset += 18

    # ============================================================
    # 🏺 IN-WORLD RELIC HUNT & SHRINE ALTAR SYSTEM (MAP 8)
    # ============================================================
    def spawn_relic_stage(self, stage_num):
        """Spawns mathematical relic items in the desert maze for the given stage"""
        self.relic_items = []
        self.relic_collected_count = 0
        self.relic_stage_complete = False
        self.relic_stage = stage_num

        if stage_num == 1:
            # Stage 1: Multiplication Array (3 Rows × 4 Apples = 12)
            self.relic_target_count = 12
            self.relic_item_type = "apple"
            self.relic_quest_title = "STAGE 1 • 🍎 THE GOLDEN ORCHARD TRIAL"
            self.relic_quest_math = "3 Rows × 4 Apples = 12 Total Apples"
            self.relic_quest_hint = "Gather all 12 Golden Apples and bring them to Shrine 1!"
            coords = [(46, 18), (45, 18), (44, 18), (43, 18), (42, 18), (41, 18), (40, 18), (39, 18), (38, 18), (37, 18), (36, 18), (35, 18)]
            glow = (239, 68, 68)

        elif stage_num == 2:
            # Stage 2: Repeated Addition (4 Groups of 2 = 8)
            self.relic_target_count = 8
            self.relic_item_type = "coconut"
            self.relic_quest_title = "STAGE 2 • 🥥 THE REPEATED ADDITION TRAIL"
            self.relic_quest_math = "4 Groups of 2 Coconuts = 2 + 2 + 2 + 2 = 8"
            self.relic_quest_hint = "Gather 8 Coconuts along the oasis path and deliver to Shrine 2!"
            coords = [(32, 18), (30, 18), (28, 18), (26, 18), (23, 18), (21, 18), (19, 18), (17, 18)]
            glow = (180, 83, 9)

        elif stage_num == 3:
            # Stage 3: Equal Sharing Division (10 Coins ÷ 2 Chests = 5)
            self.relic_target_count = 10
            self.relic_item_type = "coin"
            self.relic_quest_title = "STAGE 3 • 🎁 EQUAL SHARING DIVISION"
            self.relic_quest_math = "10 Scarab Coins ÷ 2 Chests = 5 Coins Each"
            self.relic_quest_hint = "Collect all 10 Golden Coins to split between the 2 Shrine Chests!"
            coords = [(14, 17), (14, 16), (13, 15), (11, 15), (10, 15), (9, 14), (9, 12), (9, 11), (7, 11), (5, 11)]
            glow = (234, 179, 8)

        elif stage_num == 4:
            # Stage 4: Unit Fraction One-Half (1 / 2)
            self.relic_target_count = 2
            self.relic_item_type = "sun_disk"
            self.relic_quest_title = "STAGE 4 • 🍕 SACRED UNIT FRACTION (ONE-HALF)"
            self.relic_quest_math = "2 Halves (1/2 + 1/2) = 1 Whole Solar Disk"
            self.relic_quest_hint = "Gather both 2 Sun Disk Halves (1/2 each) and deliver to Shrine 4!"
            coords = [(3, 10), (4, 7)]
            glow = (245, 158, 11)

        elif stage_num == 5:
            # Stage 5: Unit Fraction One-Third (1 / 3)
            self.relic_target_count = 3
            self.relic_item_type = "ingot"
            self.relic_quest_title = "STAGE 5 • 🍫 SACRED UNIT FRACTION (ONE-THIRD)"
            self.relic_quest_math = "3 Segments (1/3 + 1/3 + 1/3) = 1 Whole Ingot Bar"
            self.relic_quest_hint = "Gather all 3 Ingot Segments (1/3 each) and deliver to Shrine 5!"
            coords = [(4, 3), (14, 3), (24, 3)]
            glow = (217, 119, 6)
        else:
            return

        for idx, (tx, ty) in enumerate(coords):
            self.relic_items.append({
                "id": idx,
                "tile_x": tx,
                "tile_y": ty,
                "x": tx * TILE_SIZE,
                "y": ty * TILE_SIZE,
                "type": self.relic_item_type,
                "glow_color": glow,
                "collected": False
            })

        self.relic_banner_text = f"✨ {self.relic_quest_title}"
        self.relic_banner_sub = self.relic_quest_math
        self.relic_banner_timer = 4.0
        print(f"🏺 Relic Stage {stage_num} spawned with {len(self.relic_items)} items!")

    def update_relic_hunt(self, dt):
        """Updates in-world relic item pickup detection, animations, and banner timers"""
        self.relic_float_time += dt

        if self.relic_banner_timer > 0:
            self.relic_banner_timer -= dt

        # Update sparkle particles
        surviving_particles = []
        for p in self.relic_pickup_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= dt
            if p["life"] > 0:
                surviving_particles.append(p)
        self.relic_pickup_particles = surviving_particles

        # Player item collection check
        player_cx = self.player_x + TILE_SIZE // 2
        player_cy = self.player_y + TILE_SIZE // 2

        for item in self.relic_items:
            if not item["collected"]:
                item_cx = item["tile_x"] * TILE_SIZE + TILE_SIZE // 2
                item_cy = item["tile_y"] * TILE_SIZE + TILE_SIZE // 2
                dist = math.hypot(player_cx - item_cx, player_cy - item_cy)
                
                if dist < 28:
                    item["collected"] = True
                    self.relic_collected_count += 1
                    if self.snap_sound:
                        self.snap_sound.play()

                    # Spawn 10 pickup sparkles
                    for _ in range(10):
                        self.relic_pickup_particles.append({
                            "x": item_cx,
                            "y": item_cy,
                            "vx": random.uniform(-2.0, 2.0),
                            "vy": random.uniform(-3.0, -0.5),
                            "color": item["glow_color"],
                            "life": 0.7,
                            "rad": random.randint(3, 6)
                        })

                    if self.relic_collected_count >= self.relic_target_count:
                        self.relic_stage_complete = True
                        self.relic_banner_text = "✨ ALL SUPPLIES GATHERED! ✨"
                        self.relic_banner_sub = f"Deliver them to Guardian {self.quiz_station_index}'s Shrine Altar!"
                        self.relic_banner_timer = 4.0

    def draw_relic_items(self):
        """Draws all active, floating mathematical relic items in the world"""
        for item in self.relic_items:
            if item["collected"]:
                continue

            screen_x = (item["x"] - self.camera_x) * ZOOM
            screen_y = (item["y"] - self.camera_y) * ZOOM

            if (-TILE_SIZE * ZOOM <= screen_x <= self.width + TILE_SIZE * ZOOM and
                    -TILE_SIZE * ZOOM <= screen_y <= self.height + TILE_SIZE * ZOOM):
                float_offset = math.sin(self.relic_float_time * 4.0 + item["id"]) * 4.0
                cx = screen_x + (TILE_SIZE * ZOOM) // 2
                cy = screen_y + (TILE_SIZE * ZOOM) // 2 + float_offset

                # 1. Contact shadow (Pre-rendered cache)
                self.screen.blit(self.relic_shadow_surf, (cx - self.relic_shadow_surf.get_width() // 2, screen_y + TILE_SIZE * ZOOM - 6))

                # 2. Glowing pulse aura
                pulse_r = int(14 * ZOOM + math.sin(self.relic_float_time * 5.0 + item["id"]) * 2)
                pygame.draw.circle(self.screen, item["glow_color"], (int(cx), int(cy)), pulse_r, 1)

                # 3. Vector Item Graphic
                itype = item["type"]
                if itype == "apple":
                    pygame.draw.circle(self.screen, (220, 38, 38), (int(cx), int(cy)), int(10 * ZOOM))
                    pygame.draw.circle(self.screen, (254, 202, 202), (int(cx - 3 * ZOOM), int(cy - 3 * ZOOM)), int(3 * ZOOM))
                    pygame.draw.polygon(self.screen, (34, 197, 94), [
                        (cx, cy - 9 * ZOOM),
                        (cx + 6 * ZOOM, cy - 14 * ZOOM),
                        (cx + 2 * ZOOM, cy - 9 * ZOOM)
                    ])
                elif itype == "coconut":
                    pygame.draw.ellipse(self.screen, (120, 53, 15), (cx - 10 * ZOOM, cy - 8 * ZOOM, 20 * ZOOM, 16 * ZOOM))
                    pygame.draw.circle(self.screen, (67, 56, 202), (int(cx - 3 * ZOOM), int(cy - 2 * ZOOM)), int(2 * ZOOM))
                    pygame.draw.circle(self.screen, (67, 56, 202), (int(cx + 3 * ZOOM), int(cy - 2 * ZOOM)), int(2 * ZOOM))
                    pygame.draw.circle(self.screen, (67, 56, 202), (int(cx), int(cy + 2 * ZOOM)), int(2 * ZOOM))
                elif itype == "coin":
                    pygame.draw.circle(self.screen, (234, 179, 8), (int(cx), int(cy)), int(9 * ZOOM))
                    pygame.draw.circle(self.screen, (254, 240, 138), (int(cx), int(cy)), int(9 * ZOOM), 2)
                    pygame.draw.circle(self.screen, (202, 138, 4), (int(cx), int(cy)), int(5 * ZOOM), 1)
                elif itype == "sun_disk":
                    pygame.draw.circle(self.screen, (245, 158, 11), (int(cx), int(cy)), int(11 * ZOOM))
                    pygame.draw.rect(self.screen, (15, 23, 42), (cx - 12 * ZOOM, cy, 24 * ZOOM, 12 * ZOOM))
                    pygame.draw.line(self.screen, (254, 240, 138), (cx - 11 * ZOOM, cy), (cx + 11 * ZOOM, cy), 2)
                elif itype == "ingot":
                    pygame.draw.rect(self.screen, (217, 119, 6), (cx - 10 * ZOOM, cy - 6 * ZOOM, 20 * ZOOM, 12 * ZOOM), border_radius=3)
                    pygame.draw.rect(self.screen, (251, 191, 36), (cx - 10 * ZOOM, cy - 6 * ZOOM, 20 * ZOOM, 12 * ZOOM), 2, border_radius=3)
                    pygame.draw.line(self.screen, (254, 240, 138), (cx - 8 * ZOOM, cy), (cx + 8 * ZOOM, cy), 1)

    def draw_relic_pickup_particles(self):
        """Draws pickup sparkle bursts in world space (0 runtime allocations)"""
        for p in self.relic_pickup_particles:
            sx = (p["x"] - self.camera_x) * ZOOM
            sy = (p["y"] - self.camera_y) * ZOOM
            if 0 <= sx <= self.width and 0 <= sy <= self.height:
                r = max(1, int(p["rad"] * (p["life"] / 0.7)))
                pygame.draw.circle(self.screen, p["color"], (int(sx), int(sy)), r)

    def draw_relic_quest_hud(self):
        """Draws the active Quest Objective & Real-time Inventory bar at the top of the screen"""
        hud_w, hud_h = 760, 68
        hud_x = (self.width - hud_w) // 2
        hud_y = 12

        # Blit pre-rendered slate glassmorphic background
        self.screen.blit(self.quest_hud_bg, (hud_x, hud_y))

        # Glowing border: Emerald if stage complete, Gold otherwise
        border_c = (52, 211, 153) if self.relic_stage_complete else (245, 158, 11)
        pygame.draw.rect(self.screen, border_c, (hud_x, hud_y, hud_w, hud_h), 2, border_radius=12)

        # Stage Badge Pill (Left)
        badge_w, badge_h = 96, 46
        badge_x = hud_x + 12
        badge_y = hud_y + 11
        pygame.draw.rect(self.screen, (30, 41, 59), (badge_x, badge_y, badge_w, badge_h), border_radius=8)
        pygame.draw.rect(self.screen, border_c, (badge_x, badge_y, badge_w, badge_h), 2, border_radius=8)

        st_lbl = self.dialog_stat_font.render(f"STAGE {self.relic_stage}", True, (255, 215, 0))
        self.screen.blit(st_lbl, (badge_x + (badge_w - st_lbl.get_width()) // 2, badge_y + 4))

        # Item icon
        self.render_icon(self.relic_item_type if self.relic_item_type in self.icon_cache else "star_gold",
                         (badge_x + badge_w // 2, badge_y + 30), (18, 18))

        # Center Text: Quest Title & Math Concept
        q_surf = self.dialog_header_font.render(self.relic_quest_title, True, (255, 255, 255))
        self.screen.blit(q_surf, (hud_x + 120, hud_y + 10))

        math_c = (52, 211, 153) if self.relic_stage_complete else (253, 230, 138)
        m_surf = self.dialog_hint_font.render(f"💡 {self.relic_quest_math}", True, math_c)
        self.screen.blit(m_surf, (hud_x + 120, hud_y + 36))

        # Right Side: Inventory Progress Bar & Counter
        p_bar_w, p_bar_h = 160, 16
        p_bar_x = hud_x + hud_w - p_bar_w - 20
        p_bar_y = hud_y + 36

        # Background track
        pygame.draw.rect(self.screen, (30, 41, 59), (p_bar_x, p_bar_y, p_bar_w, p_bar_h), border_radius=6)
        pygame.draw.rect(self.screen, (71, 85, 105), (p_bar_x, p_bar_y, p_bar_w, p_bar_h), 1, border_radius=6)

        # Filled progress
        fill_pct = min(1.0, self.relic_collected_count / max(1, self.relic_target_count))
        fill_w = int(p_bar_w * fill_pct)
        if fill_w > 0:
            fill_c = (34, 197, 94) if self.relic_stage_complete else (245, 158, 11)
            pygame.draw.rect(self.screen, fill_c, (p_bar_x, p_bar_y, fill_w, p_bar_h), border_radius=6)

        # Counter text above progress bar
        cnt_txt = f"Collected: {self.relic_collected_count} / {self.relic_target_count}"
        cnt_surf = self.dialog_stat_font.render(cnt_txt, True, (255, 215, 0) if not self.relic_stage_complete else (34, 197, 94))
        self.screen.blit(cnt_surf, (p_bar_x + (p_bar_w - cnt_surf.get_width()) // 2, hud_y + 12))

    def draw_relic_stage_banner(self):
        """Draws prominent floating banner for stage start, completion, and delivery alerts"""
        b_w, b_h = 640, 68
        b_x = (self.width - b_w) // 2
        b_y = 90

        self.screen.blit(self.banner_bg, (b_x, b_y))
        pygame.draw.rect(self.screen, (251, 191, 36), (b_x, b_y, b_w, b_h), 2, border_radius=12)

        t1 = self.dialog_header_font.render(self.relic_banner_text, True, (255, 215, 0))
        self.screen.blit(t1, (b_x + (b_w - t1.get_width()) // 2, b_y + 10))

        if self.relic_banner_sub:
            t2 = self.dialog_hint_font.render(self.relic_banner_sub, True, (253, 230, 138))
            self.screen.blit(t2, (b_x + (b_w - t2.get_width()) // 2, b_y + 36))

    # ============================================================
    # HIGH-RESOLUTION VECTOR ICON ENGINE
    # ============================================================
    def generate_icon_cache(self):
        """Generates crisp, anti-aliased vector icon surfaces for 100% reliable rendering without font dependency"""
        self.icon_cache = {}
        
        # 1. Apple Icon (32x32)
        apple = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.line(apple, (120, 53, 15), (16, 8), (18, 3), 3)
        pygame.draw.ellipse(apple, (34, 197, 94), (18, 2, 8, 5))
        pygame.draw.circle(apple, (220, 38, 38), (12, 18), 10)
        pygame.draw.circle(apple, (239, 68, 68), (20, 18), 10)
        pygame.draw.circle(apple, (220, 38, 38), (16, 20), 9)
        pygame.draw.circle(apple, (254, 202, 202), (11, 14), 3)
        self.icon_cache["apple"] = apple

        # 2. Coconut Icon (32x32)
        coconut = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(coconut, (34, 197, 94), (6, 2, 12, 6))
        pygame.draw.ellipse(coconut, (22, 163, 74), (14, 2, 12, 6))
        pygame.draw.circle(coconut, (120, 53, 15), (16, 18), 11)
        pygame.draw.circle(coconut, (180, 83, 9), (16, 18), 9)
        pygame.draw.circle(coconut, (69, 26, 3), (13, 15), 2)
        pygame.draw.circle(coconut, (69, 26, 3), (19, 15), 2)
        pygame.draw.circle(coconut, (69, 26, 3), (16, 20), 2)
        self.icon_cache["coconut"] = coconut

        # 3. Golden Treasure Chest Icon (32x32)
        chest = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(chest, (180, 83, 9), (4, 12, 24, 16), border_radius=4)
        pygame.draw.rect(chest, (245, 158, 11), (4, 8, 24, 8), border_radius=4)
        pygame.draw.rect(chest, (251, 191, 36), (4, 8, 24, 20), 2, border_radius=4)
        pygame.draw.line(chest, (71, 85, 105), (10, 8), (10, 27), 2)
        pygame.draw.line(chest, (71, 85, 105), (22, 8), (22, 27), 2)
        pygame.draw.circle(chest, (255, 255, 255), (16, 16), 3)
        pygame.draw.circle(chest, (245, 158, 11), (16, 16), 2)
        self.icon_cache["chest"] = chest

        # 4. Pizza Slice Icon (32x32)
        pizza = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.polygon(pizza, (245, 158, 11), [(16, 28), (4, 8), (28, 8)])
        pygame.draw.ellipse(pizza, (180, 83, 9), (3, 5, 26, 7))
        pygame.draw.ellipse(pizza, (217, 119, 6), (4, 6, 24, 5))
        pygame.draw.circle(pizza, (220, 38, 38), (13, 14), 3)
        pygame.draw.circle(pizza, (220, 38, 38), (19, 16), 3)
        pygame.draw.circle(pizza, (220, 38, 38), (15, 22), 2)
        self.icon_cache["pizza"] = pizza

        # 5. Chocolate Bar Icon (32x32)
        choco = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(choco, (69, 26, 3), (6, 6, 20, 22), border_radius=3)
        pygame.draw.rect(choco, (120, 53, 15), (7, 7, 18, 20), border_radius=2)
        pygame.draw.rect(choco, (180, 83, 9), (8, 8, 7, 8), border_radius=1)
        pygame.draw.rect(choco, (180, 83, 9), (17, 8, 7, 8), border_radius=1)
        pygame.draw.rect(choco, (180, 83, 9), (8, 18, 7, 8), border_radius=1)
        pygame.draw.rect(choco, (180, 83, 9), (17, 18, 7, 8), border_radius=1)
        pygame.draw.rect(choco, (245, 158, 11), (6, 20, 20, 8), border_radius=2)
        self.icon_cache["chocolate"] = choco

        # 6. Lock Icon (32x32)
        lock = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.arc(lock, (203, 213, 225), (10, 4, 12, 14), 0, math.pi, 3)
        pygame.draw.rect(lock, (245, 158, 11), (7, 13, 18, 15), border_radius=4)
        pygame.draw.rect(lock, (251, 191, 36), (7, 13, 18, 15), 2, border_radius=4)
        pygame.draw.circle(lock, (15, 23, 42), (16, 18), 2)
        pygame.draw.line(lock, (15, 23, 42), (16, 18), (16, 23), 2)
        self.icon_cache["lock"] = lock

        # 7. Crown Icon (32x32)
        crown = pygame.Surface((32, 32), pygame.SRCALPHA)
        c_poly = [(4, 24), (28, 24), (27, 10), (20, 17), (16, 7), (12, 17), (5, 10)]
        pygame.draw.polygon(crown, (245, 158, 11), c_poly)
        pygame.draw.polygon(crown, (255, 255, 255), c_poly, 2)
        pygame.draw.circle(crown, (239, 68, 68), (5, 10), 3)
        pygame.draw.circle(crown, (59, 130, 246), (16, 7), 3)
        pygame.draw.circle(crown, (239, 68, 68), (27, 10), 3)
        pygame.draw.rect(crown, (251, 191, 36), (4, 22, 24, 5), border_radius=2)
        self.icon_cache["crown"] = crown

        # 8. Caravan Icon (32x32)
        caravan = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(caravan, (120, 53, 15), (4, 14, 18, 12), border_radius=3)
        pygame.draw.rect(caravan, (220, 38, 38), (2, 8, 22, 7), border_radius=3)
        pygame.draw.circle(caravan, (245, 158, 11), (7, 26), 4)
        pygame.draw.circle(caravan, (245, 158, 11), (19, 26), 4)
        pygame.draw.circle(caravan, (217, 119, 6), (26, 16), 5)
        self.icon_cache["caravan"] = caravan

        # 9. Gold Star Icon (28x28)
        star_gold = pygame.Surface((28, 28), pygame.SRCALPHA)
        pts = []
        for step in range(10):
            r = 13 if step % 2 == 0 else 6
            a = step * (math.pi / 5) - math.pi / 2
            pts.append((14 + r * math.cos(a), 14 + r * math.sin(a)))
        pygame.draw.polygon(star_gold, (245, 158, 11), pts)
        pygame.draw.polygon(star_gold, (254, 240, 138), pts, 2)
        self.icon_cache["star_gold"] = star_gold

        # 10. Silver/Empty Star Icon (28x28)
        star_silver = pygame.Surface((28, 28), pygame.SRCALPHA)
        pts_s = []
        for step in range(10):
            r = 13 if step % 2 == 0 else 6
            a = step * (math.pi / 5) - math.pi / 2
            pts_s.append((14 + r * math.cos(a), 14 + r * math.sin(a)))
        pygame.draw.polygon(star_silver, (30, 41, 59), pts_s)
        pygame.draw.polygon(star_silver, (100, 116, 139), pts_s, 2)
        self.icon_cache["star_empty"] = star_silver

        # 11. Red Elimination Cross (28x28)
        cross = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(cross, (185, 28, 28), (14, 14), 12)
        pygame.draw.line(cross, (255, 255, 255), (8, 8), (20, 20), 3)
        pygame.draw.line(cross, (255, 255, 255), (8, 20), (20, 8), 3)
        self.icon_cache["cross"] = cross

        # 12. Elemental Gem Icons: Earth/Leaf (A), Ice/Snow (B), Solar/Sun (C), Ruby/Fire (D)
        leaf = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(leaf, (16, 185, 129), (3, 4, 18, 16))
        pygame.draw.ellipse(leaf, (52, 211, 153), (3, 4, 18, 16), 2)
        pygame.draw.line(leaf, (255, 255, 255), (4, 18), (18, 6), 2)
        self.icon_cache["elem_earth"] = leaf

        ice = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.line(ice, (147, 197, 253), (12, 2), (12, 22), 3)
        pygame.draw.line(ice, (147, 197, 253), (2, 12), (22, 12), 3)
        pygame.draw.line(ice, (147, 197, 253), (5, 5), (19, 19), 2)
        pygame.draw.line(ice, (147, 197, 253), (5, 19), (19, 5), 2)
        self.icon_cache["elem_ice"] = ice

        sun = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(sun, (245, 158, 11), (12, 12), 6)
        for s_step in range(8):
            s_a = s_step * (math.pi / 4)
            pygame.draw.line(sun, (251, 191, 36), (12 + 7 * math.cos(s_a), 12 + 7 * math.sin(s_a)), 
                                                  (12 + 10 * math.cos(s_a), 12 + 10 * math.sin(s_a)), 2)
        self.icon_cache["elem_sun"] = sun

        fire = pygame.Surface((24, 24), pygame.SRCALPHA)
        f_pts = [(12, 2), (18, 10), (16, 20), (12, 22), (8, 20), (6, 10)]
        pygame.draw.polygon(fire, (239, 68, 68), f_pts)
        pygame.draw.polygon(fire, (251, 191, 36), [(12, 9), (15, 14), (14, 19), (12, 20), (10, 19), (9, 14)])
        self.icon_cache["elem_fire"] = fire

    def render_icon(self, icon_key, center_pos, target_size=(24, 24)):
        """Blits the requested icon from cache scaled to target_size centered at center_pos (0 allocations per frame)"""
        if hasattr(self, 'icon_cache') and icon_key in self.icon_cache:
            cache_key = (icon_key, target_size)
            if not hasattr(self, '_scaled_icon_cache'):
                self._scaled_icon_cache = {}
            if cache_key not in self._scaled_icon_cache:
                raw_surf = self.icon_cache[icon_key]
                if raw_surf.get_size() != target_size:
                    self._scaled_icon_cache[cache_key] = pygame.transform.scale(raw_surf, target_size).convert_alpha()
                else:
                    self._scaled_icon_cache[cache_key] = raw_surf.convert_alpha()
            scaled = self._scaled_icon_cache[cache_key]
            rect = scaled.get_rect(center=center_pos)
            self.screen.blit(scaled, rect)
    def draw_caravan(self):
        """Renders the companion camel/pony and upgradable cargo cart"""
        cx = (self.caravan_x - self.camera_x) * ZOOM
        cy = (self.caravan_y - self.camera_y) * ZOOM
        
        # Margin culling
        if not (-64 * ZOOM <= cx <= self.width + 64 * ZOOM and -64 * ZOOM <= cy <= self.height + 64 * ZOOM):
            return

        cart_sz = int(TILE_SIZE * ZOOM)
        bob = math.sin(self.caravan_bob_timer) * 3
        
        # 1. Soft ground contact shadow (Pre-rendered cache)
        self.screen.blit(self.caravan_shadow_surf, (cx + cart_sz // 2 - self.caravan_shadow_surf.get_width() // 2, cy + cart_sz - self.caravan_shadow_surf.get_height() // 2 + 2))

        # 2. Wooden Cart Base (Rich mahogany box)
        cart_rect = pygame.Rect(cx + 4, cy + 8 + bob, cart_sz - 8, cart_sz - 12)
        pygame.draw.rect(self.screen, (120, 53, 15), cart_rect, border_radius=6)
        pygame.draw.rect(self.screen, (180, 83, 9), cart_rect.inflate(-4, -4), border_radius=4)
        pygame.draw.rect(self.screen, (245, 158, 11), cart_rect, 2, border_radius=6)

        # 3. Rotating Iron Wheels
        wheel_r = int(7 * ZOOM)
        w1_x = cart_rect.left + 4
        w2_x = cart_rect.right - 4
        w_y = cart_rect.bottom - 2
        for wx in [w1_x, w2_x]:
            pygame.draw.circle(self.screen, (30, 41, 59), (wx, w_y), wheel_r)
            pygame.draw.circle(self.screen, (245, 158, 11), (wx, w_y), wheel_r, 2)
            # Wheel spokes rotating
            spoke_dx = math.cos(self.caravan_wheel_rot) * (wheel_r - 2)
            spoke_dy = math.sin(self.caravan_wheel_rot) * (wheel_r - 2)
            pygame.draw.line(self.screen, (255, 255, 255), (wx - spoke_dx, w_y - spoke_dy), (wx + spoke_dx, w_y + spoke_dy), 2)

        # 4. Striped Silk Canopy / Roof
        canopy_rect = pygame.Rect(cart_rect.left - 2, cart_rect.top - 12, cart_rect.width + 4, 14)
        pygame.draw.rect(self.screen, (220, 38, 38), canopy_rect, border_radius=4)
        for st_i in range(0, canopy_rect.width, 8):
            pygame.draw.rect(self.screen, (245, 158, 11), (canopy_rect.left + st_i, canopy_rect.top, 4, canopy_rect.height))
        pygame.draw.rect(self.screen, (255, 215, 0), canopy_rect, 2, border_radius=4)

        # 5. Visible Loaded Cargo inside the cart!
        cargo_count = len(self.caravan_cargo)
        if cargo_count >= 1: # Apples
            pygame.draw.circle(self.screen, (239, 68, 68), (cart_rect.centerx - 8, cart_rect.centery - 2), 6)
            pygame.draw.circle(self.screen, (239, 68, 68), (cart_rect.centerx - 2, cart_rect.centery - 5), 5)
            pygame.draw.circle(self.screen, (34, 197, 94), (cart_rect.centerx - 2, cart_rect.centery - 8), 2)
        if cargo_count >= 2: # Coconuts
            pygame.draw.circle(self.screen, (120, 53, 15), (cart_rect.centerx + 6, cart_rect.centery - 3), 6)
            pygame.draw.circle(self.screen, (180, 83, 9), (cart_rect.centerx + 6, cart_rect.centery - 3), 4)
        if cargo_count >= 3: # Golden Chest
            ch_box = pygame.Rect(cart_rect.centerx - 6, cart_top := cart_rect.top + 2, 14, 10)
            pygame.draw.rect(self.screen, (245, 158, 11), ch_box, border_radius=2)
            pygame.draw.rect(self.screen, (255, 255, 255), ch_box, 1, border_radius=2)
        if cargo_count >= 4: # Pizza Feast
            pygame.draw.circle(self.screen, (217, 119, 6), (cart_rect.left + 6, cart_rect.centery - 4), 6)
            pygame.draw.circle(self.screen, (239, 68, 68), (cart_rect.left + 5, cart_rect.centery - 5), 2)
        if cargo_count >= 5: # Legendary Sun Relic Gem
            gem_pulse = math.sin(pygame.time.get_ticks() / 150) * 3
            pygame.draw.circle(self.screen, (168, 85, 247), (cart_rect.centerx, canopy_rect.top - 8), int(8 + gem_pulse), 2)
            pygame.draw.circle(self.screen, (255, 215, 0), (cart_rect.centerx, canopy_rect.top - 8), 5)

        # 6. Chibi Desert Companion (Camel/Pony Mascot in front)
        companion_offset_x = 18 if self.caravan_dir == "right" else (-18 if self.caravan_dir == "left" else 0)
        companion_offset_y = 16 if self.caravan_dir == "down" else (-16 if self.caravan_dir == "up" else 4)
        m_cx = cx + cart_sz // 2 + companion_offset_x
        m_cy = cy + cart_sz // 2 + companion_offset_y + bob * 0.5
        
        # Mascot Body
        pygame.draw.circle(self.screen, (217, 119, 6), (int(m_cx), int(m_cy)), int(10 * ZOOM))
        # Mascot Head with Bobbing
        h_bob = math.sin(self.caravan_bob_timer * 1.5) * 2
        pygame.draw.circle(self.screen, (245, 158, 11), (int(m_cx + (3 if self.caravan_dir == "right" else -3)), int(m_cy - 8 + h_bob)), int(7 * ZOOM))
        # Eyes
        pygame.draw.circle(self.screen, (0, 0, 0), (int(m_cx + (4 if self.caravan_dir == "right" else -2)), int(m_cy - 9 + h_bob)), 2)
        # Gold Halter / Reins
        pygame.draw.line(self.screen, (245, 158, 11), (int(m_cx), int(m_cy)), (int(cart_rect.centerx), int(cart_rect.centery)), 2)

        # 7. Happy Music Notes
        for note in self.caravan_music_notes:
            n_x = (note["x"] - self.camera_x) * ZOOM
            n_y = (note["y"] - self.camera_y) * ZOOM
            n_surf = self.dialog_hint_font.render(note["char"], True, note["color"])
            self.screen.blit(n_surf, (n_x, n_y))

    def draw_caravan_hud(self):
        """Draws the expedition inventory rack in the top center with pre-rendered glassmorphic surfaces (0 allocations per frame)"""
        hud_w, hud_h = 360, 68
        hud_x = (self.width - hud_w) // 2
        hud_y = 14
        
        # Blit pre-rendered glassmorphic rack surface
        self.screen.blit(self.caravan_hud_bg, (hud_x, hud_y))
        
        # Border
        border_col = (34, 197, 94) if len(self.caravan_cargo) == 5 else (245, 158, 11)
        pygame.draw.rect(self.screen, border_col, (hud_x, hud_y, hud_w, hud_h), 2, border_radius=12)
        
        # Header with decorative icons
        c_count = len(self.caravan_cargo)
        status_txt = "ROYAL EXPEDITION (5/5 FULL!)" if c_count == 5 else f"EXPEDITION CARAVAN ({c_count}/5)"
        h_surf = self.dialog_stat_font.render(status_txt, True, (255, 215, 0) if c_count < 5 else (34, 197, 94))
        self.screen.blit(h_surf, (hud_x + (hud_w - h_surf.get_width()) // 2, hud_y + 8))
        
        # Header Icon Left and Right
        icon_type = "crown" if c_count == 5 else "caravan"
        self.render_icon(icon_type, (hud_x + 24, hud_y + 16), (20, 20))
        self.render_icon(icon_type, (hud_x + hud_w - 24, hud_y + 16), (20, 20))
        
        # 5 Cargo item slots centered
        slot_w = 56
        slot_h = 34
        gap = 8
        total_slots_w = 5 * slot_w + 4 * gap
        start_sx = hud_x + (hud_w - total_slots_w) // 2
        
        for idx in range(5):
            sx = start_sx + idx * (slot_w + gap)
            sy = hud_y + 26
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)
            
            if idx < len(self.caravan_cargo):
                item = self.caravan_cargo[idx]
                self.screen.blit(self.caravan_slot_active_bg, (sx, sy))
                pygame.draw.rect(self.screen, item["color"], s_rect, 2, border_radius=8)
                
                # Render crisp vector cargo icon
                self.render_icon(item.get("icon_key", "chest"), s_rect.center, (24, 24))
            else:
                self.screen.blit(self.caravan_slot_empty_bg, (sx, sy))
                pygame.draw.rect(self.screen, (51, 65, 85), s_rect, 1, border_radius=8)
                
                # Render crisp lock icon
                self.render_icon("lock", s_rect.center, (18, 18))

    def draw_caravan_upgrade_banner(self):
        """Draws celebratory gold banner when new cargo is loaded onto the caravan"""
        b_w, b_h = 580, 60
        b_x = (self.width - b_w) // 2
        b_y = 120
        b_rect = pygame.Rect(b_x, b_y, b_w, b_h)
        
        pygame.draw.rect(self.screen, (22, 163, 74), b_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), b_rect, 3, border_radius=12)
        
        t_surf = self.dialog_header_font.render(self.caravan_upgrade_banner_text, True, (255, 255, 255))
        self.screen.blit(t_surf, t_surf.get_rect(center=(b_rect.centerx, b_rect.top + 20)))
        
        sub_surf = self.dialog_stat_font.render(self.caravan_upgrade_banner_sub, True, (254, 240, 138))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(b_rect.centerx, b_rect.bottom - 16)))

    def draw_citadel_hud(self):
        """Draws the Sacred Math Keystone Rack for Map 9 (Citadel of the Sun)"""
        hud_w, hud_h = 420, 72
        hud_x = (self.width - hud_w) // 2
        hud_y = 14
        
        # Blit pre-rendered glassmorphic rack surface
        self.screen.blit(self.caravan_hud_bg, (hud_x, hud_y))
        
        c_count = len(self.citadel_collected_keystones)
        border_col = (34, 197, 94) if c_count == 5 else (245, 158, 11)
        pygame.draw.rect(self.screen, border_col, (hud_x, hud_y, hud_w, hud_h), 2, border_radius=12)
        
        # Header Title
        status_txt = "🏛️ SUN CITADEL ALTAR (5/5 READY!)" if c_count == 5 else f"🏛️ SUN CITADEL KEYSTONES ({c_count}/5)"
        h_surf = self.dialog_stat_font.render(status_txt, True, (255, 215, 0) if c_count < 5 else (34, 197, 94))
        self.screen.blit(h_surf, (hud_x + (hud_w - h_surf.get_width()) // 2, hud_y + 6))
        
        # 5 Keystone Sockets
        slot_w = 68
        slot_h = 36
        gap = 10
        total_slots_w = 5 * slot_w + 4 * gap
        start_sx = hud_x + (hud_w - total_slots_w) // 2
        
        romans = ["I", "II", "III", "IV", "V"]
        for idx in range(5):
            sx = start_sx + idx * (slot_w + gap)
            sy = hud_y + 28
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)
            
            if idx < len(self.citadel_collected_keystones):
                keystone = self.citadel_collected_keystones[idx]
                pygame.draw.rect(self.screen, (15, 23, 42), s_rect, border_radius=8)
                pygame.draw.rect(self.screen, keystone["color"], s_rect, 2, border_radius=8)
                
                # Math badge inside
                lbl_surf = self.small_font.render(keystone["math"], True, (255, 255, 255))
                self.screen.blit(lbl_surf, lbl_surf.get_rect(center=s_rect.center))
            else:
                pygame.draw.rect(self.screen, (20, 25, 38), s_rect, border_radius=8)
                pygame.draw.rect(self.screen, (71, 85, 105), s_rect, 1, border_radius=8)
                
                r_surf = self.dialog_hint_font.render(romans[idx], True, (100, 116, 139))
                self.screen.blit(r_surf, r_surf.get_rect(center=s_rect.center))

    def draw_citadel_banner(self):
        """Draws celebratory gold banner when a sacred keystone is earned in Map 9"""
        b_w, b_h = 620, 64
        b_x = (self.width - b_w) // 2
        b_y = 110
        b_rect = pygame.Rect(b_x, b_y, b_w, b_h)
        
        pygame.draw.rect(self.screen, (15, 23, 42), b_rect, border_radius=12)
        pygame.draw.rect(self.screen, (245, 158, 11), b_rect, 2, border_radius=12)
        
        t_surf = self.dialog_stat_font.render(self.citadel_banner_text, True, (255, 215, 0))
        self.screen.blit(t_surf, (b_x + (b_w - t_surf.get_width()) // 2, b_y + 8))
        
        sub_surf = self.dialog_hint_font.render(self.citadel_banner_sub, True, (254, 240, 138))
        self.screen.blit(sub_surf, (b_x + (b_w - sub_surf.get_width()) // 2, b_y + 34))

    def draw_caravan_sparkles(self):
        """Draws wind dash trails and celebration sparkles"""
        for p in self.caravan_sparkles:
            sx = (p["x"] - self.camera_x) * ZOOM
            sy = (p["y"] - self.camera_y) * ZOOM
            r = max(1, int(p["rad"] * ZOOM * (p["life"] / 1.0)))
            pygame.draw.circle(self.screen, p["color"], (int(sx), int(sy)), r)

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

            # Physical Keyboard Typing in Identification Question Mode (State 1)
            elif self.quiz_state == 1:
                q_data = self.quiz_questions[self.current_question_index]
                if q_data.get("q_type") == "identification":
                    if event.key == pygame.K_BACKSPACE:
                        self.ident_input_text = self.ident_input_text[:-1]
                    elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                        self.submit_identification_answer()
                    elif event.unicode and (event.unicode.isalnum() or event.unicode in "/+ -"):
                        if len(self.ident_input_text) < 14:
                            self.ident_input_text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.trigger_click(event.pos)

        return None

    # ============================================================
    # SMART CRA AUTO-VISUALIZER (100% Dynamic for ANY Teacher Question)
    # ============================================================
    def draw_auto_visualizer(self, q_data, vis_rect):
        """Smart CRA Auto-Visualizer: Dynamically parses question text to render visual models"""
        import re
        pygame.draw.rect(self.screen, (20, 29, 47), vis_rect, border_radius=12)
        pygame.draw.rect(self.screen, (51, 65, 85), vis_rect, 2, border_radius=12)
        
        v_type = q_data.get("visual_type", "")
        q_text = q_data.get("question", "").lower()
        nums = [int(n) for n in re.findall(r'\b\d+\b', q_text)]

        # Dynamic detection if not explicitly set
        if not v_type:
            frac_match = re.search(r'(\d+)/(\d+)', q_text)
            frac_part_match = re.search(r'(\d+)\s*(?:part|parts|slice|slices|segment|segments)?\s*out\s*of\s*(\d+)', q_text)
            
            if frac_match:
                v_type = "fraction_circle"
                q_data["visual_shaded"] = int(frac_match.group(1))
                q_data["visual_slices"] = int(frac_match.group(2))
            elif frac_part_match:
                v_type = "fraction_circle"
                q_data["visual_shaded"] = int(frac_part_match.group(1))
                q_data["visual_slices"] = int(frac_part_match.group(2))
            elif "1/2" in q_text or "half" in q_text or "halves" in q_text or "pizza" in q_text:
                v_type = "fraction_circle"
                q_data["visual_shaded"] = 1
                q_data["visual_slices"] = 2
            elif "1/3" in q_text or "third" in q_text or "thirds" in q_text or "bar" in q_text or "chocolate" in q_text:
                v_type = "fraction_bar"
                q_data["visual_shaded"] = 1
                q_data["visual_segments"] = 3
            elif "1/4" in q_text or "fourth" in q_text or "fourths" in q_text or "quarter" in q_text:
                v_type = "fraction_circle"
                q_data["visual_shaded"] = 1
                q_data["visual_slices"] = 4
            elif "row" in q_text or "array" in q_text or "×" in q_text or "times" in q_text or "multiply" in q_text:
                v_type = "array"
            elif "group" in q_text or "+" in q_text or "basket" in q_text or "plate" in q_text or "box" in q_text:
                v_type = "groups"
            elif "share" in q_text or "divide" in q_text or "÷" in q_text or "equally" in q_text:
                v_type = "sharing"

        # 1. Multiplication Array (Dynamic rows & cols extracted from text)
        if v_type == "array":
            rows = q_data.get("visual_rows", nums[0] if len(nums) >= 1 else 3)
            cols = q_data.get("visual_cols", nums[1] if len(nums) >= 2 else 4)
            rows = min(5, max(1, rows))
            cols = min(6, max(1, cols))

            r_rad = min(14, 110 // (rows * 2), 260 // (cols * 2))
            spacing_x = min(42, (vis_rect.width - 200) // cols)
            spacing_y = min(36, (vis_rect.height - 40) // rows)
            start_x = vis_rect.centerx - ((cols - 1) * spacing_x) // 2
            start_y = vis_rect.centery - ((rows - 1) * spacing_y) // 2 - 8

            for r in range(rows):
                for c in range(cols):
                    ax = start_x + c * spacing_x
                    ay = start_y + r * spacing_y
                    pygame.draw.circle(self.screen, (239, 68, 68), (ax, ay), r_rad)
                    pygame.draw.circle(self.screen, (248, 113, 113), (ax - 3, ay - 3), max(2, r_rad // 3))
                    pygame.draw.circle(self.screen, (34, 197, 94), (ax + 2, ay - r_rad), 3)

            lbl = self.dialog_stat_font.render(f"🍎 Visual Model: {rows} Rows with {cols} Apples in Each Row", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 2. Repeated Addition / Groups (Dynamic group count & items extracted from text)
        elif v_type == "groups":
            groups = q_data.get("visual_groups", nums[0] if len(nums) >= 1 else 4)
            items_per_group = q_data.get("visual_items_per_group", nums[1] if len(nums) >= 2 else 2)
            groups = min(5, max(1, groups))
            items_per_group = min(5, max(1, items_per_group))

            plate_w = min(110, (vis_rect.width - 60) // groups - 10)
            start_x = vis_rect.centerx - ((groups * plate_w + (groups - 1) * 10) // 2)

            for g_i in range(groups):
                px = start_x + g_i * (plate_w + 10) + plate_w // 2
                py = vis_rect.centery - 8
                pygame.draw.ellipse(self.screen, (120, 53, 15), (px - plate_w // 2, py - 20, plate_w, 40))
                pygame.draw.ellipse(self.screen, (180, 83, 9), (px - plate_w // 2, py - 20, plate_w, 40), 2)
                
                for c_i in range(items_per_group):
                    cx = px - ((items_per_group - 1) * 16) // 2 + c_i * 16
                    cy = py - 4
                    pygame.draw.circle(self.screen, (67, 56, 202), (cx, cy), 8)
                    pygame.draw.circle(self.screen, (129, 140, 248), (cx - 2, cy - 2), 3)

            lbl = self.dialog_stat_font.render(f"🥥 Visual Model: {groups} Groups with {items_per_group} Coconuts in Each Group", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 3. Equal Sharing Division (Dynamic total & chests extracted from text)
        elif v_type == "sharing":
            chests = q_data.get("visual_chests", nums[1] if len(nums) >= 2 else 2)
            total = q_data.get("visual_total", nums[0] if len(nums) >= 1 else 10)
            chests = min(4, max(1, chests))

            # Draw central gold coin supply pool above chests
            coin_pool_y = vis_rect.centery - 42
            p_lbl = self.dialog_hint_font.render(f"✨ Total: {total} Gold Coins to Divide", True, (254, 240, 138))
            self.screen.blit(p_lbl, (vis_rect.centerx - p_lbl.get_width() // 2, coin_pool_y - 18))

            draw_pool_coins = min(12, total)
            start_pool_x = vis_rect.centerx - ((draw_pool_coins - 1) * 18) // 2
            for co_i in range(draw_pool_coins):
                coin_x = start_pool_x + co_i * 18
                pygame.draw.circle(self.screen, (234, 179, 8), (coin_x, coin_pool_y), 7)
                pygame.draw.circle(self.screen, (254, 240, 138), (coin_x - 2, coin_pool_y - 2), 2)

            # Draw chests below
            chest_w = min(160, (vis_rect.width - 60) // chests - 20)
            start_x = vis_rect.centerx - ((chests * chest_w + (chests - 1) * 20) // 2)

            for ch_i in range(chests):
                cx = start_x + ch_i * (chest_w + 20)
                cy = vis_rect.centery - 12
                ch_rect = pygame.Rect(cx, cy, chest_w, 48)
                pygame.draw.rect(self.screen, (30, 41, 59), ch_rect, border_radius=8)
                pygame.draw.rect(self.screen, (245, 158, 11), ch_rect, 2, border_radius=8)
                
                c_lbl = self.dialog_stat_font.render(f"🎁 Chest {ch_i+1}", True, (253, 230, 138))
                self.screen.blit(c_lbl, (cx + chest_w // 2 - c_lbl.get_width() // 2, cy + 12))

            lbl = self.dialog_stat_font.render(f"🎁 Visual Model: Share {total} Gold Coins Equally between {chests} Chests", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 4. Fraction Circle (Dynamic slices & shaded parts extracted from text)
        elif v_type == "fraction_circle":
            slices = q_data.get("visual_slices", 2)
            shaded = q_data.get("visual_shaded", 1)
            slices = max(2, min(8, slices))
            shaded = max(1, min(slices, shaded))

            cx, cy = vis_rect.centerx, vis_rect.centery - 10
            radius = 48
            
            pygame.draw.circle(self.screen, (180, 83, 9), (cx, cy), radius + 4, 3)
            
            for si in range(slices):
                start_angle = (2 * math.pi / slices) * si - math.pi / 2
                end_angle = (2 * math.pi / slices) * (si + 1) - math.pi / 2
                poly = [(cx, cy)]
                for step_i in range(16):
                    a = start_angle + (end_angle - start_angle) * (step_i / 15)
                    poly.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
                
                is_sh = si < shaded
                col = (245, 158, 11) if is_sh else (51, 65, 85)
                pygame.draw.polygon(self.screen, col, poly)
                pygame.draw.polygon(self.screen, (255, 255, 255), poly, 2)
                
                if is_sh:
                    mid_a = (start_angle + end_angle) / 2
                    px = cx + radius * 0.55 * math.cos(mid_a)
                    py = cy + radius * 0.55 * math.sin(mid_a)
                    pygame.draw.circle(self.screen, (220, 38, 38), (int(px), int(py)), 4)

            lbl = self.dialog_stat_font.render(f"🍕 Visual Model: {shaded} Shaded Part out of {slices} Equal Parts", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 5. Fraction Bar (Dynamic segments & shaded parts extracted from text)
        elif v_type == "fraction_bar":
            segments = q_data.get("visual_segments", 3)
            shaded = q_data.get("visual_shaded", 1)
            segments = max(2, min(8, segments))
            shaded = max(1, min(segments, shaded))

            bar_w = 360
            bar_h = 50
            bx = vis_rect.centerx - bar_w // 2
            by = vis_rect.centery - 30
            seg_w = bar_w / segments

            for si in range(segments):
                seg_rect = pygame.Rect(bx + si * seg_w, by, seg_w, bar_h)
                is_sh = si < shaded
                col = (217, 119, 6) if is_sh else (30, 41, 59)
                pygame.draw.rect(self.screen, col, seg_rect, border_radius=6)
                pygame.draw.rect(self.screen, (255, 255, 255), seg_rect, 2, border_radius=6)
                
                txt = f"Part {si+1} (Shaded)" if is_sh else f"Part {si+1}"
                txt_surf = self.dialog_hint_font.render(txt, True, (255, 255, 255))
                self.screen.blit(txt_surf, txt_surf.get_rect(center=seg_rect.center))

            lbl = self.dialog_stat_font.render(f"🍫 Visual Model: {shaded} Shaded Segment out of {segments} Equal Segments", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 6. General Fallback (Non-math / General Knowledge / Science / English)
        else:
            hint_txt = q_data.get("hint", "Examine the choices carefully and select the best answer below! ⭐")
            # Stylized Challenge Crest
            pygame.draw.circle(self.screen, (30, 41, 59), (vis_rect.centerx, vis_rect.centery - 18), 24)
            pygame.draw.circle(self.screen, (245, 158, 11), (vis_rect.centerx, vis_rect.centery - 18), 24, 2)
            c_icon = self.dialog_speaker_font.render("🏆", True, (255, 215, 0))
            self.screen.blit(c_icon, c_icon.get_rect(center=(vis_rect.centerx, vis_rect.centery - 18)))
            
            h_surf = self.dialog_hint_font.render(f"💡 {hint_txt}", True, (253, 230, 138))
            self.screen.blit(h_surf, (vis_rect.centerx - h_surf.get_width() // 2, vis_rect.bottom - 26))

    # ============================================================
    # QUIZ DIALOGUE DRAWING METHODS (Clean & Icon-Free)
    # ============================================================
    def draw_quiz_dialog(self):
        self.screen.blit(self.dialog_dim_overlay, (0, 0))

        box_w, box_h = 580, 380
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Outer Parchment Box
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (245, 158, 11), dialog_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, (251, 191, 36), dialog_rect.inflate(-6, -6), 1, border_radius=12)

        # Header ribbon
        header_surf = pygame.Surface((box_w - 36, 40), pygame.SRCALPHA)
        header_surf.fill((30, 41, 59, 230))
        self.screen.blit(header_surf, (box_x + 18, box_y + 12))
        pygame.draw.rect(self.screen, (245, 158, 11), (box_x + 18, box_y + 12, box_w - 36, 40), 1, border_radius=8)

        q_data = self.quiz_questions[self.current_question_index]
        st_title = q_data.get("title", f"Challenge {self.quiz_station_index}")
        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = self.dialog_header_font.render(f"{speaker_name} • {st_title}", True, (255, 215, 0))
        self.screen.blit(speaker_surf, (box_x + 30, box_y + 18))

        # Station progress pill (Top Right)
        st_pill = pygame.Rect(box_x + box_w - 140, box_y + 16, 120, 30)
        pygame.draw.rect(self.screen, (15, 23, 42), st_pill, border_radius=6)
        pygame.draw.rect(self.screen, (245, 158, 11), st_pill, 1, border_radius=6)
        st_txt = self.dialog_stat_font.render(f"STATION {self.quiz_station_index}/5", True, (254, 240, 138))
        self.screen.blit(st_txt, st_txt.get_rect(center=st_pill.center))

        # Question Prompt
        wrapped_q = self.wrap_text(q_data["question"], self.dialog_q_font, box_w - 50)
        y_text = box_y + 62
        for line in wrapped_q:
            txt_surf = self.dialog_q_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 22

        # 50:50 Hint feedback bubble if a choice was eliminated
        if self.wrong_feedback_msg:
            fb_surf = self.dialog_hint_font.render(self.wrong_feedback_msg, True, (252, 211, 77))
            self.screen.blit(fb_surf, (box_x + 25, y_text + 4))

        # Clean vertical stacked choice buttons (No icons)
        button_w, button_h = 500, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 130
        spacing = 52

        for i, choice_text in enumerate(q_data["choices"][:4]):
            b_y = button_y_start + i * spacing
            btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)
            is_elim = i in self.eliminated_choices
            is_hov = btn_rect.collidepoint(self.cursor_pos) and not is_elim

            if is_elim:
                bg_color = (20, 25, 35)
                text_color = (100, 110, 120)
                border_color = (50, 55, 65)
            elif is_hov:
                bg_color = (255, 215, 0)
                text_color = (15, 23, 42)
                border_color = (255, 255, 255)
            else:
                bg_color = (30, 41, 59)
                text_color = (255, 255, 255)
                border_color = (71, 85, 105)

            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

            c_surf = self.dialog_choice_font.render(choice_text, True, text_color)
            c_rect = c_surf.get_rect(center=btn_rect.center)
            self.screen.blit(c_surf, c_rect)

    def draw_wrong_dialog(self):
        self.screen.blit(self.wrong_dialog_dim_overlay, (0, 0))

        box_w, box_h = 580, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=14)

        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = self.dialog_speaker_font.render(speaker_name, True, (239, 68, 68))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        msg1 = self.dialog_msg_font.render("Hmm, that is not correct.", True, (255, 255, 255))
        msg2 = self.dialog_hint_font.render("You have 1 try remaining! Think carefully and try again. ⭐", True, (253, 230, 138))
        self.screen.blit(msg1, (box_x + 25, box_y + 75))
        self.screen.blit(msg2, (box_x + 25, box_y + 110))

        button_w, button_h = 220, 46
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 180
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        bg_c = (220, 38, 38) if is_hov else (153, 27, 27)

        pygame.draw.rect(self.screen, bg_c, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Try Again", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_out_of_tries_dialog(self):
        self.screen.blit(self.dialog_dim_overlay, (0, 0))

        box_w, box_h = 600, 270
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (245, 158, 11), dialog_rect, 3, border_radius=14)

        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = self.dialog_speaker_font.render(speaker_name, True, (245, 158, 11))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        q_data = self.quiz_questions[self.current_question_index]
        if "correct" in q_data and "choices" in q_data:
            correct_choice_text = q_data["choices"][q_data["correct"]]
        elif "ident_answers" in q_data and q_data["ident_answers"]:
            correct_choice_text = q_data["ident_answers"][0]
        else:
            correct_choice_text = "See solution above"

        msg1 = self.dialog_msg_font.render(f"Out of tries! The correct answer was: {correct_choice_text}", True, (255, 255, 255))
        
        if self.is_caravan_mode:
            reward_text = "You still received the Caravan Cargo so your quest can continue!"
        elif self.is_puzzle_hybrid_mode:
            reward_text = "You still received the Sun Keystone so your quest can continue!"
        elif hasattr(self, 'bridge_tiles') and self.bridge_tiles:
            reward_text = "You still received the Bridge piece so your quest can continue!"
        else:
            reward_text = "You completed this challenge so your quest can continue!"
            
        msg2 = self.dialog_hint_font.render(reward_text, True, (253, 230, 138))
        self.screen.blit(msg1, (box_x + 25, box_y + 70))
        self.screen.blit(msg2, (box_x + 25, box_y + 105))

        button_w, button_h = 220, 46
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 180
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (245, 158, 11) if is_hovered else (30, 41, 59)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Continue", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_correct_dialog(self):
        self.screen.blit(self.dialog_dim_overlay, (0, 0))

        box_w, box_h = 580, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (22, 163, 74), dialog_rect, 3, border_radius=14)

        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = self.dialog_speaker_font.render(speaker_name, True, (22, 163, 74))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))

        msg_surf = self.dialog_msg_font.render(self.current_correct_phrase, True, (255, 255, 255))
        self.screen.blit(msg_surf, (box_x + 25, box_y + 75))

        button_w, button_h = 220, 46
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 175
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (22, 163, 74)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Continue", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_final_dialog(self):
        self.screen.blit(self.dialog_dim_overlay, (0, 0))

        box_w, box_h = 620, 320
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=14)

        speaker_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", "Guardian")
        speaker_surf = self.dialog_speaker_font.render(speaker_name, True, (218, 165, 32))
        self.screen.blit(speaker_surf, (box_x + 25, box_y + 20))
        pygame.draw.line(self.screen, (218, 165, 32), (box_x + 25, box_y + 48), (box_x + 25 + speaker_surf.get_width() + 10, box_y + 48), 2)

        speech_lines = [
            "Outstanding, young mathematician! You solved all my challenges.",
            "Your mastery of multiplication, division, and fractions is amazing!",
            "I will now activate the portal. Step through to continue your quest!"
        ]
        
        y_text = box_y + 70
        for line in speech_lines:
            txt_surf = self.dialog_regular_font.render(line, True, (255, 255, 255))
            self.screen.blit(txt_surf, (box_x + 25, y_text))
            y_text += 26

        button_w, button_h = 240, 46
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 235
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (30, 41, 59) if not is_hovered else (218, 165, 32)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Ride Royal Caravan", True, (255, 255, 255))
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
    # SUN RELIC ALTAR SOUND SYNTHESIS
    # ============================================================
    def load_puzzle_sounds(self):
        try:
            self.snap_sound = self.generate_snap_sound()
            self.success_sound = self.generate_success_sound()
            print("🔊 Sun Relic sound effects synthesized successfully.")
        except Exception as e:
            print(f"⚠️ Error loading puzzle sounds: {e}")
            self.snap_sound = None
            self.success_sound = None

    def generate_snap_sound(self):
        import numpy as np
        sample_rate = 22050
        duration = 0.12
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 880
        sound_data = np.sin(2 * np.pi * frequency * t) * 0.4 * np.exp(-25 * t)
        audio_data = (sound_data * 32767).astype(np.int16)
        try:
            return pygame.mixer.Sound(buffer=audio_data.tobytes())
        except Exception:
            return None

    def generate_success_sound(self):
        import numpy as np
        sample_rate = 22050
        duration = 0.8
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        notes = [523.25, 659.25, 784.99, 1046.50]  # C5, E5, G5, C6 arpeggio chord
        sound_data = np.zeros_like(t)
        for idx, freq in enumerate(notes):
            delay = idx * 0.12
            note_t = t - delay
            started = note_t >= 0
            note_sound = np.sin(2 * np.pi * freq * note_t) * 0.25 * started
            note_decay = np.exp(-8 * note_t) * started
            sound_data += note_sound * note_decay
        sound_data = np.clip(sound_data, -1.0, 1.0)
        audio_data = (sound_data * 32767).astype(np.int16)
        try:
            return pygame.mixer.Sound(buffer=audio_data.tobytes())
        except Exception:
            return None

    # ============================================================
    # SUN RELIC ALTAR JIGSAW SYSTEM (MAP 8)
    # ============================================================
    def init_sun_relic_puzzle(self):
        """Initializes the 5 sacred math relic slabs for the Sun Temple Altar"""
        box_w, box_h = 800, 520
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        
        slot_w, slot_h = 110, 110
        gap = 20
        total_slots_w = 5 * slot_w + 4 * gap
        start_sx = box_x + (box_w - total_slots_w) // 2
        altar_y = box_y + 110
        deck_y = box_y + 320
        
        import random
        shuffled_indices = list(range(5))
        random.shuffle(shuffled_indices)
        
        slab_configs = [
            {"idx": 0, "title": "Array", "math": "3 × 4", "ans": "= 12", "color": (239, 68, 68), "border": (248, 113, 113), "icon_key": "apple"},
            {"idx": 1, "title": "Groups", "math": "4 × 2", "ans": "= 8", "color": (180, 83, 9), "border": (217, 119, 6), "icon_key": "coconut"},
            {"idx": 2, "title": "Sharing", "math": "10 ÷ 2", "ans": "= 5", "color": (245, 158, 11), "border": (251, 191, 36), "icon_key": "chest"},
            {"idx": 3, "title": "Half", "math": "1/2", "ans": "Fraction", "color": (217, 119, 6), "border": (245, 158, 11), "icon_key": "pizza"},
            {"idx": 4, "title": "Third", "math": "1/3", "ans": "Fraction", "color": (168, 85, 247), "border": (192, 132, 252), "icon_key": "chocolate"},
        ]
        
        self.sun_relic_slabs = []
        for i, cfg in enumerate(slab_configs):
            shuf_pos = shuffled_indices[i]
            target_x = start_sx + i * (slot_w + gap)
            target_y = altar_y
            deck_x = start_sx + shuf_pos * (slot_w + gap)
            
            # Pre-render Slab Surface
            slab_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            pygame.draw.rect(slab_surf, (15, 23, 42), (0, 0, slot_w, slot_h), border_radius=12)
            pygame.draw.rect(slab_surf, cfg["color"], (3, 3, slot_w - 6, slot_h - 6), border_radius=10)
            pygame.draw.rect(slab_surf, cfg["border"], (0, 0, slot_w, slot_h), 2, border_radius=12)
            
            # Icon in center-top
            if cfg["icon_key"] in self.icon_cache:
                ic = pygame.transform.scale(self.icon_cache[cfg["icon_key"]], (32, 32))
                slab_surf.blit(ic, ic.get_rect(center=(slot_w // 2, 32)))
                
            # Math label
            m_txt = self.dialog_btn_font.render(cfg["math"], True, (255, 255, 255))
            slab_surf.blit(m_txt, m_txt.get_rect(center=(slot_w // 2, 65)))
            
            sub_txt = self.small_font.render(cfg["ans"], True, (254, 240, 138))
            slab_surf.blit(sub_txt, sub_txt.get_rect(center=(slot_w // 2, 88)))
            
            self.sun_relic_slabs.append({
                "index": i,
                "config": cfg,
                "surface": slab_surf,
                "x": deck_x,
                "y": deck_y,
                "deck_x": deck_x,
                "deck_y": deck_y,
                "target_x": target_x,
                "target_y": target_y,
                "slot_w": slot_w,
                "slot_h": slot_h,
                "is_placed": False
            })
            
        self.sun_relic_active = True
        self.sun_relic_solved = False
        self.sun_relic_solved_time = 0
        self.dragged_slab = None
        print("🏛️ Sun Relic Altar Jigsaw initialized with 5 Mathematical Slabs!")

    def update_sun_relic_puzzle(self, dt):
        if self.sun_relic_solved:
            if hasattr(self, 'sun_relic_solved_time') and self.sun_relic_solved_time > 0:
                if pygame.time.get_ticks() - self.sun_relic_solved_time > 1800:
                    self.sun_relic_active = False
                    self.quiz_state = 6  # Open Goal Exit Portal!
                    self.clear_portal_overlapping_tiles()
                    print("🌟 Sun Relic Altar Restored! Goal Exit Portal Unlocked!")
            return

        # Gesture fist drag & drop
        if self.hand_detected and self.fist_closed:
            if not self.dragged_slab:
                for slab in self.sun_relic_slabs:
                    if not slab["is_placed"]:
                        s_rect = pygame.Rect(slab["x"], slab["y"], slab["slot_w"], slab["slot_h"])
                        if s_rect.collidepoint(self.cursor_pos):
                            self.dragged_slab = slab
                            self.drag_offset_x = slab["x"] - self.cursor_pos[0]
                            self.drag_offset_y = slab["y"] - self.cursor_pos[1]
                            break
            if self.dragged_slab:
                self.dragged_slab["x"] = self.cursor_pos[0] + self.drag_offset_x
                self.dragged_slab["y"] = self.cursor_pos[1] + self.drag_offset_y
        else:
            if self.dragged_slab:
                self.release_dragged_slab()

    # ============================================================
    # 🧩 MAP 9 INTERACTIVE STATION MINI-PUZZLES
    # ============================================================
    def init_station_mini_puzzle(self, station_num):
        """Initializes the hands-on concrete manipulative puzzle for Station 1-5 in Map 9"""
        self.mini_puzzle_station = station_num
        self.mini_puzzle_solved = False
        self.mini_puzzle_solved_time = 0
        self.mini_puzzle_active = True
        self.mini_puzzle_dragged_item = None
        self.mini_puzzle_drag_offset_x = 0
        self.mini_puzzle_drag_offset_y = 0
        self.mini_puzzle_slots = []
        self.mini_puzzle_items = []
        
        box_w, box_h = 760, 480
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        if station_num == 1:
            # 🍎 Station 1: 3x4 Multiplication Array Builder
            self.mini_puzzle_title = "🧩 PUZZLE 1 • 🍎 BUILD THE 3 × 4 ARRAY"
            self.mini_puzzle_sub = "Click or drag 12 Golden Apples to fill the 3 rows of 4 grid!"
            self.mini_puzzle_math_target = "3 Rows × 4 Apples = 12 Total Apples"
            self.mini_puzzle_type = "array"
            
            grid_start_x = box_x + 220
            grid_start_y = box_y + 110
            slot_sz = 60
            slot_gap = 14
            for r in range(3):
                for c in range(4):
                    sx = grid_start_x + c * (slot_sz + slot_gap)
                    sy = grid_start_y + r * (slot_sz + slot_gap)
                    self.mini_puzzle_slots.append({
                        "id": r * 4 + c, "row": r, "col": c,
                        "x": sx, "y": sy, "w": slot_sz, "h": slot_sz,
                        "filled": False
                    })
            
            # Tray of 12 apples below
            tray_start_x = box_x + 55
            tray_start_y = box_y + 360
            for i in range(12):
                tx = tray_start_x + i * 55
                ty = tray_start_y
                self.mini_puzzle_items.append({
                    "id": i, "icon": "apple", "color": (239, 68, 68),
                    "x": tx, "y": ty, "deck_x": tx, "deck_y": ty,
                    "w": 44, "h": 44, "is_placed": False, "slot_id": None
                })

        elif station_num == 2:
            # 🥥 Station 2: Repeated Addition 4 Groups of 2 Coconuts
            self.mini_puzzle_title = "🧩 PUZZLE 2 • 🥥 GROUP THE COCONUTS (2 + 2 + 2 + 2)"
            self.mini_puzzle_sub = "Place 2 Coconuts into each of the 4 Oasis Baskets!"
            self.mini_puzzle_math_target = "4 Groups of 2 = 2 + 2 + 2 + 2 = 8 Coconuts"
            self.mini_puzzle_type = "groups"
            
            basket_w, basket_h = 140, 110
            basket_start_x = box_x + 60
            basket_y = box_y + 120
            for b in range(4):
                bx = basket_start_x + b * 165
                self.mini_puzzle_slots.append({
                    "id": b, "title": f"Group {b+1}",
                    "x": bx, "y": basket_y, "w": basket_w, "h": basket_h,
                    "capacity": 2, "count": 0, "filled": False
                })
                
            # Tray of 8 coconuts
            tray_start_x = box_x + 100
            tray_start_y = box_y + 355
            for i in range(8):
                tx = tray_start_x + i * 70
                ty = tray_start_y
                self.mini_puzzle_items.append({
                    "id": i, "icon": "coconut", "color": (180, 83, 9),
                    "x": tx, "y": ty, "deck_x": tx, "deck_y": ty,
                    "w": 48, "h": 48, "is_placed": False, "slot_id": None
                })

        elif station_num == 3:
            # 🎁 Station 3: Equal Sharing Division (10 Coins ÷ 2 Chests)
            self.mini_puzzle_title = "🧩 PUZZLE 3 • 🎁 EQUAL SHARING DIVISION (10 ÷ 2)"
            self.mini_puzzle_sub = "Share 10 Scarab Coins equally between the 2 Golden Chests (5 each)!"
            self.mini_puzzle_math_target = "10 Coins ÷ 2 Chests = 5 Coins Each"
            self.mini_puzzle_type = "sharing"
            
            chest_w, chest_h = 280, 130
            self.mini_puzzle_slots.append({
                "id": 0, "title": "Chest A (Needs 5)",
                "x": box_x + 70, "y": box_y + 120, "w": chest_w, "h": chest_h,
                "capacity": 5, "count": 0, "filled": False
            })
            self.mini_puzzle_slots.append({
                "id": 1, "title": "Chest B (Needs 5)",
                "x": box_x + 410, "y": box_y + 120, "w": chest_w, "h": chest_h,
                "capacity": 5, "count": 0, "filled": False
            })
            
            # Tray of 10 gold coins
            tray_start_x = box_x + 75
            tray_start_y = box_y + 355
            for i in range(10):
                tx = tray_start_x + i * 62
                ty = tray_start_y
                self.mini_puzzle_items.append({
                    "id": i, "icon": "coin", "color": (234, 179, 8),
                    "x": tx, "y": ty, "deck_x": tx, "deck_y": ty,
                    "w": 44, "h": 44, "is_placed": False, "slot_id": None
                })

        elif station_num == 4:
            # 🍕 Station 4: Unit Fraction (1 / 2) Solar Disk
            self.mini_puzzle_title = "🧩 PUZZLE 4 • 🍕 UNIT FRACTION (ONE-HALF = 1/2)"
            self.mini_puzzle_sub = "Slot 1 shaded half out of 2 equal parts into the Solar Keystone!"
            self.mini_puzzle_math_target = "1 Part out of 2 Equal Parts = 1/2"
            self.mini_puzzle_type = "fraction_half"
            
            self.mini_puzzle_slots.append({
                "id": 0, "title": "Left Half (1/2)", "x": box_x + 220, "y": box_y + 130, "w": 140, "h": 140, "filled": False
            })
            self.mini_puzzle_slots.append({
                "id": 1, "title": "Right Half (1/2)", "x": box_x + 400, "y": box_y + 130, "w": 140, "h": 140, "filled": False
            })
            
            # 2 Halves
            self.mini_puzzle_items.append({
                "id": 0, "icon": "sun_disk", "color": (245, 158, 11),
                "x": box_x + 230, "y": box_y + 340, "deck_x": box_x + 230, "deck_y": box_y + 340,
                "w": 120, "h": 80, "is_placed": False, "slot_id": None, "label": "Half A (1/2)"
            })
            self.mini_puzzle_items.append({
                "id": 1, "icon": "sun_disk", "color": (245, 158, 11),
                "x": box_x + 410, "y": box_y + 340, "deck_x": box_x + 410, "deck_y": box_y + 340,
                "w": 120, "h": 80, "is_placed": False, "slot_id": None, "label": "Half B (1/2)"
            })

        elif station_num == 5:
            # 🍫 Station 5: Unit Fraction (1 / 3) Ingot Bar
            self.mini_puzzle_title = "🧩 PUZZLE 5 • 🍫 UNIT FRACTION (ONE-THIRD = 1/3)"
            self.mini_puzzle_sub = "Slot the 3 equal segments (1/3 each) to assemble the Whole Ingot Bar!"
            self.mini_puzzle_math_target = "3 Segments (1/3 + 1/3 + 1/3) = 1 Whole Bar"
            self.mini_puzzle_type = "fraction_third"
            
            bar_start_x = box_x + 130
            bar_y = box_y + 140
            seg_w, seg_h = 150, 100
            for i in range(3):
                self.mini_puzzle_slots.append({
                    "id": i, "title": f"Segment {i+1} (1/3)",
                    "x": bar_start_x + i * 170, "y": bar_y, "w": seg_w, "h": seg_h,
                    "filled": False
                })
                
            tray_start_x = box_x + 130
            tray_start_y = box_y + 340
            for i in range(3):
                self.mini_puzzle_items.append({
                    "id": i, "icon": "ingot", "color": (217, 119, 6),
                    "x": tray_start_x + i * 170, "y": tray_start_y,
                    "deck_x": tray_start_x + i * 170, "deck_y": tray_start_y,
                    "w": 140, "h": 70, "is_placed": False, "slot_id": None, "label": "1/3 Ingot"
                })

    def update_station_mini_puzzle(self, dt):
        """Updates gesture dragging and completion state for station mini-puzzle"""
        if self.mini_puzzle_solved:
            return

        # Gesture fist drag & drop
        if self.hand_detected and self.fist_closed:
            if not self.mini_puzzle_dragged_item:
                for item in self.mini_puzzle_items:
                    if not item["is_placed"]:
                        i_rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                        if i_rect.collidepoint(self.cursor_pos):
                            self.mini_puzzle_dragged_item = item
                            self.mini_puzzle_drag_offset_x = item["x"] - self.cursor_pos[0]
                            self.mini_puzzle_drag_offset_y = item["y"] - self.cursor_pos[1]
                            break
            if self.mini_puzzle_dragged_item:
                self.mini_puzzle_dragged_item["x"] = self.cursor_pos[0] + self.mini_puzzle_drag_offset_x
                self.mini_puzzle_dragged_item["y"] = self.cursor_pos[1] + self.mini_puzzle_drag_offset_y
        else:
            if self.mini_puzzle_dragged_item:
                self.release_mini_puzzle_dragged_item()

    def release_mini_puzzle_dragged_item(self):
        """Snaps dragged mini puzzle item into the nearest valid slot or returns to tray"""
        if not self.mini_puzzle_dragged_item:
            return
        item = self.mini_puzzle_dragged_item
        item_center = (item["x"] + item["w"] // 2, item["y"] + item["h"] // 2)
        
        placed = False
        for slot in self.mini_puzzle_slots:
            slot_rect = pygame.Rect(slot["x"], slot["y"], slot["w"], slot["h"])
            if slot_rect.collidepoint(item_center):
                if self.mini_puzzle_type == "array" or "fraction" in self.mini_puzzle_type:
                    if not slot["filled"]:
                        item["x"] = slot["x"] + (slot["w"] - item["w"]) // 2
                        item["y"] = slot["y"] + (slot["h"] - item["h"]) // 2
                        item["is_placed"] = True
                        item["slot_id"] = slot["id"]
                        slot["filled"] = True
                        placed = True
                        if self.snap_sound:
                            self.snap_sound.play()
                        break
                elif self.mini_puzzle_type in ["groups", "sharing"]:
                    if slot["count"] < slot["capacity"]:
                        slot["count"] += 1
                        # Place side by side in container
                        idx_in_slot = slot["count"] - 1
                        item["x"] = slot["x"] + 15 + (idx_in_slot % 3) * 45
                        item["y"] = slot["y"] + 30 + (idx_in_slot // 3) * 40
                        item["is_placed"] = True
                        item["slot_id"] = slot["id"]
                        if slot["count"] >= slot["capacity"]:
                            slot["filled"] = True
                        placed = True
                        if self.snap_sound:
                            self.snap_sound.play()
                        break

        if not placed:
            item["x"] = item["deck_x"]
            item["y"] = item["deck_y"]

        self.mini_puzzle_dragged_item = None
        self.check_mini_puzzle_completion()

    def handle_station_mini_puzzle_click(self, pos):
        """Handles click interactions: auto-slotting items, clicking Quick Assemble, or proceeding to question"""
        box_w, box_h = 760, 480
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # 1. If solved, check proceed button
        if self.mini_puzzle_solved:
            btn_rect = pygame.Rect(box_x + (box_w - 320) // 2, box_y + box_h - 60, 320, 46)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                self.current_question_index = self.quiz_station_index - 1
                self.selected_choice_index = -1
                self.eliminated_choices.clear()
                self.wrong_feedback_msg = ""
                self.ident_input_text = ""
                print(f"📖 Transitioned from Mini-Puzzle to Station {self.quiz_station_index} Multiple Choice Question!")
                return

        # 2. Quick Assemble / Auto-Place Button
        quick_btn = pygame.Rect(box_x + box_w - 180, box_y + 14, 160, 36)
        if quick_btn.collidepoint(pos):
            self.auto_solve_mini_puzzle()
            return

        # 3. Direct Item Click-to-Snap
        for item in self.mini_puzzle_items:
            if not item["is_placed"]:
                i_rect = pygame.Rect(item["x"], item["y"], item["w"], item["h"])
                if i_rect.collidepoint(pos):
                    # Snap to next available slot
                    for slot in self.mini_puzzle_slots:
                        if self.mini_puzzle_type in ["array", "fraction_half", "fraction_third"]:
                            if not slot["filled"]:
                                item["x"] = slot["x"] + (slot["w"] - item["w"]) // 2
                                item["y"] = slot["y"] + (slot["h"] - item["h"]) // 2
                                item["is_placed"] = True
                                item["slot_id"] = slot["id"]
                                slot["filled"] = True
                                if self.snap_sound:
                                    self.snap_sound.play()
                                break
                        elif self.mini_puzzle_type in ["groups", "sharing"]:
                            if slot["count"] < slot["capacity"]:
                                slot["count"] += 1
                                idx_in_slot = slot["count"] - 1
                                item["x"] = slot["x"] + 15 + (idx_in_slot % 3) * 45
                                item["y"] = slot["y"] + 30 + (idx_in_slot // 3) * 40
                                item["is_placed"] = True
                                item["slot_id"] = slot["id"]
                                if slot["count"] >= slot["capacity"]:
                                    slot["filled"] = True
                                if self.snap_sound:
                                    self.snap_sound.play()
                                break
                    self.check_mini_puzzle_completion()
                    return

    def auto_solve_mini_puzzle(self):
        """Automatically fills all slots for hands-free or quick progression"""
        if self.mini_puzzle_type in ["array", "fraction_half", "fraction_third"]:
            for slot, item in zip(self.mini_puzzle_slots, self.mini_puzzle_items):
                item["x"] = slot["x"] + (slot["w"] - item["w"]) // 2
                item["y"] = slot["y"] + (slot["h"] - item["h"]) // 2
                item["is_placed"] = True
                item["slot_id"] = slot["id"]
                slot["filled"] = True
        elif self.mini_puzzle_type in ["groups", "sharing"]:
            item_idx = 0
            for slot in self.mini_puzzle_slots:
                slot["count"] = slot["capacity"]
                slot["filled"] = True
                for i in range(slot["capacity"]):
                    if item_idx < len(self.mini_puzzle_items):
                        it = self.mini_puzzle_items[item_idx]
                        it["x"] = slot["x"] + 15 + (i % 3) * 45
                        it["y"] = slot["y"] + 30 + (i // 3) * 40
                        it["is_placed"] = True
                        it["slot_id"] = slot["id"]
                        item_idx += 1
        if self.success_sound:
            self.success_sound.play()
        self.check_mini_puzzle_completion()

    def check_mini_puzzle_completion(self):
        """Checks if all required slots are filled to mark mini-puzzle as solved"""
        if all(slot["filled"] for slot in self.mini_puzzle_slots):
            if not self.mini_puzzle_solved:
                self.mini_puzzle_solved = True
                self.mini_puzzle_solved_time = pygame.time.get_ticks()
                if self.success_sound:
                    self.success_sound.play()
                print(f"🎉 Station {self.mini_puzzle_station} Mini-Puzzle Solved!")

    def draw_station_mini_puzzle(self):
        """Renders the hands-on concrete mathematical manipulative puzzle overlay (60 FPS Pre-Cached)"""
        self.screen.blit(self.dialog_dim_overlay, (0, 0))
        
        box_w, box_h = 760, 480
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Dialog Card Container
        pygame.draw.rect(self.screen, (15, 23, 42), (box_x, box_y, box_w, box_h), border_radius=16)
        border_c = (34, 197, 94) if self.mini_puzzle_solved else (245, 158, 11)
        pygame.draw.rect(self.screen, border_c, (box_x, box_y, box_w, box_h), 3, border_radius=16)

        # Header Title
        h_surf = self.dialog_header_font.render(self.mini_puzzle_title, True, (255, 215, 0) if not self.mini_puzzle_solved else (34, 197, 94))
        self.screen.blit(h_surf, (box_x + 24, box_y + 14))

        # Instructions / Target Math
        sub_txt = self.mini_puzzle_math_target if self.mini_puzzle_solved else self.mini_puzzle_sub
        sub_surf = self.dialog_hint_font.render(sub_txt, True, (253, 230, 138) if not self.mini_puzzle_solved else (187, 247, 208))
        self.screen.blit(sub_surf, (box_x + 24, box_y + 44))

        # Quick Assemble Button (top right)
        if not self.mini_puzzle_solved:
            quick_btn = pygame.Rect(box_x + box_w - 180, box_y + 14, 160, 36)
            is_hov = quick_btn.collidepoint(self.cursor_pos)
            pygame.draw.rect(self.screen, (30, 41, 59) if not is_hov else (217, 119, 6), quick_btn, border_radius=10)
            pygame.draw.rect(self.screen, (245, 158, 11), quick_btn, 2, border_radius=10)
            q_txt = self.dialog_stat_font.render("✨ Auto-Assemble", True, (255, 255, 255))
            self.screen.blit(q_txt, q_txt.get_rect(center=quick_btn.center))

        # Draw Sockets / Containers
        for slot in self.mini_puzzle_slots:
            s_rect = pygame.Rect(slot["x"], slot["y"], slot["w"], slot["h"])
            s_bg = (30, 41, 59) if not slot["filled"] else (16, 185, 129, 60)
            pygame.draw.rect(self.screen, (30, 41, 59), s_rect, border_radius=10)
            s_border = (34, 197, 94) if slot["filled"] else (71, 85, 105)
            pygame.draw.rect(self.screen, s_border, s_rect, 2, border_radius=10)
            
            if "title" in slot:
                t_surf = self.small_font.render(slot["title"], True, (203, 213, 225))
                self.screen.blit(t_surf, (slot["x"] + 10, slot["y"] + 8))

        # Draw Tray Rack
        tray_y = box_y + 335
        t_rack = pygame.Rect(box_x + 24, tray_y, box_w - 48, 75)
        pygame.draw.rect(self.screen, (10, 15, 28), t_rack, border_radius=12)
        pygame.draw.rect(self.screen, (51, 65, 85), t_rack, 1, border_radius=12)
        tray_lbl = self.small_font.render("ITEM TRAY (Click or drag items to place in slots):", True, (148, 163, 184))
        self.screen.blit(tray_lbl, (box_x + 36, tray_y - 18))

        # Draw Items (Non-dragged first)
        for item in self.mini_puzzle_items:
            if item is not self.mini_puzzle_dragged_item:
                self.render_mini_puzzle_item(item)

        # Draw Dragged item on top with glow
        if self.mini_puzzle_dragged_item:
            self.render_mini_puzzle_item(self.mini_puzzle_dragged_item, is_dragged=True)

        # Bottom Proceed Button when Solved
        if self.mini_puzzle_solved:
            btn_rect = pygame.Rect(box_x + (box_w - 380) // 2, box_y + box_h - 60, 380, 46)
            is_hov = btn_rect.collidepoint(self.cursor_pos)
            pygame.draw.rect(self.screen, (22, 163, 74) if is_hov else (16, 185, 129), btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)
            p_txt = self.dialog_btn_font.render("🎉 Solved! Take Question Challenge →", True, (255, 255, 255))
            self.screen.blit(p_txt, p_txt.get_rect(center=btn_rect.center))

    def render_mini_puzzle_item(self, item, is_dragged=False):
        """Renders crisp vector mathematical manipulative item (Apple, Coconut, Coin, Fraction Disk, Ingot)"""
        ix = item["x"]
        iy = item["y"]
        iw = item["w"]
        ih = item["h"]
        cx = ix + iw // 2
        cy = iy + ih // 2

        if is_dragged:
            pygame.draw.circle(self.screen, (255, 255, 255), (int(cx), int(cy)), int(iw // 2 + 4), 2)

        itype = item["icon"]
        if itype == "apple":
            self.render_icon("apple", (cx, cy), (iw, ih))
        elif itype == "coconut":
            self.render_icon("coconut", (cx, cy), (iw, ih))
        elif itype == "coin":
            self.render_icon("chest", (cx, cy), (iw, ih))
        elif itype == "sun_disk":
            pygame.draw.circle(self.screen, (245, 158, 11), (int(cx), int(cy)), int(ih // 2 - 4))
            pygame.draw.circle(self.screen, (254, 240, 138), (int(cx), int(cy)), int(ih // 2 - 4), 2)
            if "label" in item:
                lbl = self.dialog_stat_font.render(item["label"], True, (255, 255, 255))
                self.screen.blit(lbl, lbl.get_rect(center=(cx, cy)))
        elif itype == "ingot":
            b_rect = pygame.Rect(ix + 4, iy + 4, iw - 8, ih - 8)
            pygame.draw.rect(self.screen, (217, 119, 6), b_rect, border_radius=8)
            pygame.draw.rect(self.screen, (251, 191, 36), b_rect, 2, border_radius=8)
            if "label" in item:
                lbl = self.dialog_stat_font.render(item["label"], True, (255, 255, 255))
                self.screen.blit(lbl, lbl.get_rect(center=b_rect.center))

    def release_dragged_slab(self):
        if not self.dragged_slab:
            return
        slab = self.dragged_slab
        dist = math.hypot(slab["x"] - slab["target_x"], slab["y"] - slab["target_y"])
        if dist < 45:
            slab["x"] = slab["target_x"]
            slab["y"] = slab["target_y"]
            slab["is_placed"] = True
            if self.snap_sound:
                self.snap_sound.play()
            print(f"🧩 Slab {slab['index']} ({slab['config']['math']}) magnetically slotted!")
            
            if all(s["is_placed"] for s in self.sun_relic_slabs):
                self.sun_relic_solved = True
                self.sun_relic_solved_time = pygame.time.get_ticks()
                if self.success_sound:
                    self.success_sound.play()
                print("🎉 All 5 Sun Relic Slabs assembled into the Temple Altar!")
        else:
            slab["x"] = slab["deck_x"]
            slab["y"] = slab["deck_y"]
            print(f"🧩 Slab {slab['index']} returned to deck.")
        self.dragged_slab = None

    def draw_sun_relic_puzzle(self):
        self.screen.blit(self.dialog_dim_overlay, (0, 0))
        
        box_w, box_h = 800, 520
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        
        # Sacred Altar Box
        pygame.draw.rect(self.screen, (15, 23, 42), (box_x, box_y, box_w, box_h), border_radius=16)
        border_c = (34, 197, 94) if self.sun_relic_solved else (245, 158, 11)
        pygame.draw.rect(self.screen, border_c, (box_x, box_y, box_w, box_h), 3, border_radius=16)
        
        # Header
        h_title = "👑 SUN TEMPLE RELIC ALTAR (5/5 ASSEMBLED!)" if self.sun_relic_solved else "🏛️ THE SACRED SUN RELIC ALTAR"
        h_surf = self.dialog_header_font.render(h_title, True, (255, 215, 0) if not self.sun_relic_solved else (34, 197, 94))
        self.screen.blit(h_surf, (box_x + (box_w - h_surf.get_width()) // 2, box_y + 16))
        
        sub_title = "Assemble the 5 Sacred Math Slabs into the Sun Altar to open the Portal!" if not self.sun_relic_solved else "✨ The Ancient Sun Disc is fully restored! Portal activated!"
        sub_surf = self.dialog_hint_font.render(sub_title, True, (253, 230, 138))
        self.screen.blit(sub_surf, (box_x + (box_w - sub_surf.get_width()) // 2, box_y + 48))
        
        # Draw Altar Sockets (Upper Row)
        slot_w, slot_h = 110, 110
        gap = 20
        total_slots_w = 5 * slot_w + 4 * gap
        start_sx = box_x + (box_w - total_slots_w) // 2
        altar_y = box_y + 110
        
        for i in range(5):
            sx = start_sx + i * (slot_w + gap)
            sy = altar_y
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)
            
            # Glowing socket base
            pygame.draw.rect(self.screen, (30, 41, 59), s_rect, border_radius=12)
            pygame.draw.rect(self.screen, (71, 85, 105), s_rect, 2, border_radius=12)
            
            # Roman numeral / socket label
            romans = ["I", "II", "III", "IV", "V"]
            r_surf = self.dialog_header_font.render(romans[i], True, (100, 116, 139))
            self.screen.blit(r_surf, r_surf.get_rect(center=s_rect.center))
            
        # Draw Deck Rack (Lower Row)
        deck_y = box_y + 320
        d_rack = pygame.Rect(start_sx - 10, deck_y - 10, total_slots_w + 20, slot_h + 20)
        pygame.draw.rect(self.screen, (10, 15, 28), d_rack, border_radius=14)
        pygame.draw.rect(self.screen, (51, 65, 85), d_rack, 1, border_radius=14)
        
        # Draw Slabs (Non-dragged first, then dragged slab on top)
        for slab in self.sun_relic_slabs:
            if slab is not self.dragged_slab:
                self.screen.blit(slab["surface"], (slab["x"], slab["y"]))
                
        if self.dragged_slab:
            self.screen.blit(self.dragged_slab["surface"], (self.dragged_slab["x"], self.dragged_slab["y"]))
            pygame.draw.rect(self.screen, (255, 255, 255), (self.dragged_slab["x"], self.dragged_slab["y"], self.dragged_slab["slot_w"], self.dragged_slab["slot_h"]), 3, border_radius=12)

    def get_ui_font(self, size, bold=False):
        """Returns a high-legibility system font for UI elements"""
        return pygame.font.SysFont(["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial", "Comic Sans MS"], size, bold=bold)

    def draw_offscreen_compass_pointer(self):
        """Draw Active Objective NPC Indicator and Off-Screen Compass Pointer for Quarter 3"""
        import math
        
        # 1. Target determination for Active Station NPC
        if self.quiz_state == 0 and hasattr(self, 'quiz_stations') and self.quiz_station_index in self.quiz_stations:
            st_x, st_y = self.quiz_stations[self.quiz_station_index]
            npc_name = self.station_npcs.get(self.quiz_station_index, {}).get("name", f"Station {self.quiz_station_index}")
            
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
        time_str = f"⏱️ {mins:02d}:{secs:02d}"

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

        t_font = self.get_ui_font(16, bold=True)
        t_surf = t_font.render(time_str, True, txt_col)
        self.screen.blit(t_surf, t_surf.get_rect(center=(hud_x + hud_w // 2, hud_y + hud_h // 2)))

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

        title = t_font.render("⏰ TIME'S UP!", True, (239, 68, 68))
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
        r_txt = btn_font.render("Retry Quarter 🔄", True, (15, 23, 42) if r_hov else (255, 255, 255))
        self.screen.blit(r_txt, r_txt.get_rect(center=retry_rect.center))

        # Button 2: Return to Stage Select
        exit_rect = pygame.Rect(box_x + box_w - 260, box_y + 175, 220, 46)
        e_hov = exit_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if e_hov else (30, 41, 59), exit_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), exit_rect, 2, border_radius=10)
        e_txt = btn_font.render("Stage Select 🗺️", True, (255, 255, 255))
        self.screen.blit(e_txt, e_txt.get_rect(center=exit_rect.center))

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()