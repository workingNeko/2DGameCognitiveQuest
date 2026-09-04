# screens/quarter2.py - Quarter 2 Map Handler (map2.txt)

import pygame
import os
import sys
import cv2
import numpy as np
import time
import math
import random
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
SPEED = 2.2

# Camera zoom settings - PERMANENT ZOOM
ZOOM = 1.50  # Fixed zoom level

# Portal settings
PORTAL_SIZES = {
    'right': (1, 3),  # 1 tile wide, 3 tiles tall (vertical portal strip against right wall)
    'left': (1, 3),   # 1 tile wide, 3 tiles tall (vertical portal strip against left wall)
    'up': (3, 1),     # 3 tiles wide, 1 tile tall (horizontal portal strip against top wall)
    'down': (3, 1)    # 3 tiles wide, 1 tile tall (horizontal portal strip against bottom wall)
}


class Quarter2:
    def __init__(self, screen, main_menu, map_name):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()
        self.map_name = map_name  # 'map2.txt'
        self.is_quiz_map = True

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
        self.pause_menu = InGamePauseMenu(self.screen, self.width, self.height, self.main_menu, self.return_to_stage_select)

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
        self.camera_x = 0
        self.camera_y = 0

        # ============================================================
        # LOAD TILE IMAGES
        # ============================================================
        self.tile_images = self.load_tile_images()
        self.fallback_tile = self.tile_images.get('street_asphalt_0', self.tile_images.get('G'))
        if not self.fallback_tile:
            self.fallback_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.fallback_tile.fill((40, 45, 55))

        # ============================================================
        # WALKABLE TILES
        # ============================================================
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "P", "r", "l", "u", "d", "L", "H", "I", "a", "b", "c", "g", "h", "i", "F"}

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

        # Star NPC (for Station 5)
        self.npc_star_sprites = []
        self.npc_star_anim_frame = 0
        self.npc_star_anim_timer = 0

        # Distinct Filipino Character NPCs for Stations 1 to 5 (Topic Titles only, No NPC names)
        if self.map_name == "map5.txt":
            self.station_npc_info = {
                1: {
                    "name": "Station 1",
                    "title": "Bibingka & Unit Fractions (1/4 Slices)",
                    "dialog_title": "Fresh Bibingka Fraction Challenge",
                    "wrong_encouragement": "Check the Slices - Try Again",
                    "correct_praise": "Correct Fraction! - Well Done",
                    "target_math": "1 Slice out of 4 Equal Slices = 1/4 (One-fourth)",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                2: {
                    "name": "Station 2",
                    "title": "Equal Sharing & Division (20 / 4)",
                    "dialog_title": "Mango Harvest Division Challenge",
                    "wrong_encouragement": "Count the Baskets - Try Again",
                    "correct_praise": "Equal Sharing Mastered! - Well Done",
                    "target_math": "20 Mangoes / 4 Baskets = 5 Mangoes per Basket",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                3: {
                    "name": "Station 3",
                    "title": "3D Geometric Solids (Salakot Cone)",
                    "dialog_title": "Traditional Shape Crafting Challenge",
                    "wrong_encouragement": "Inspect the Shape Faces - Try Again",
                    "correct_praise": "Exact Geometric Shape! - Well Done",
                    "target_math": "Salakot Hat = Cone (1 Flat Circular Base + 1 Vertex)",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                4: {
                    "name": "Station 4",
                    "title": "Analog Clock Time Reading (8:30 AM)",
                    "dialog_title": "Fiesta Schedule Clock Challenge",
                    "wrong_encouragement": "Check the Clock Hands - Try Again",
                    "correct_praise": "Exactly On Time! - Well Done",
                    "target_math": "8:30 AM = Hour Hand between 8 & 9, Minute Hand at 6",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                5: {
                    "name": "Station 5",
                    "title": "Garden Perimeter & Measurement",
                    "dialog_title": "Bamboo Garden Perimeter Challenge",
                    "wrong_encouragement": "Measure All Outer Sides - Try Again",
                    "correct_praise": "Garden Perimeter Complete! - Well Done",
                    "target_math": "Perimeter = 5m + 3m + 5m + 3m = 16 Meters Total",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                }
            }
        else:
            self.station_npc_info = {
                1: {
                    "name": "Station 1",
                    "title": "Sari-Sari Store & Change (P50 - P35)",
                    "dialog_title": "Sari-Sari Store Change Challenge",
                    "wrong_encouragement": "Count the Change - Try Again",
                    "correct_praise": "Exact Change! - Well Done",
                    "target_math": "P50 Bill - P35 Purchase = P15 Change",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                2: {
                    "name": "Station 2",
                    "title": "Philippine Coins (P25 Combinations)",
                    "dialog_title": "P25 Sorbetes Coin Challenge",
                    "wrong_encouragement": "Count the Coins - Try Again",
                    "correct_praise": "Exact Payment! - Well Done",
                    "target_math": "P25 Cone = One P20 Coin + One P5 Coin",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                3: {
                    "name": "Station 3",
                    "title": "Jeepney Passenger Fare & Multiplication",
                    "dialog_title": "Jeepney Passenger Fare Challenge",
                    "wrong_encouragement": "Check the Fare - Try Again",
                    "correct_praise": "Full Fare Collected! - Well Done",
                    "target_math": "3 Students x P12 Fare = P36 Total Payment",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                4: {
                    "name": "Station 4",
                    "title": "Market Fruit Scale (Grams & Kilograms)",
                    "dialog_title": "Market Fruit Scale Challenge",
                    "wrong_encouragement": "Weigh the Fruit - Try Again",
                    "correct_praise": "Exact Weight Scale! - Well Done",
                    "target_math": "4 Mangoes x 500g = 2,000g = 2 Kilograms (2kg)",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                },
                5: {
                    "name": "Station 5",
                    "title": "Fiesta Budgeting & Money Comparison",
                    "dialog_title": "Fiesta Parol Budget Challenge",
                    "wrong_encouragement": "Check Your Budget - Try Again",
                    "correct_praise": "Budget is Enough! - Well Done",
                    "target_math": "P350 Budget > P300 Total Materials Cost",
                    "frames": [],
                    "anim_frame": 0,
                    "anim_timer": 0
                }
            }

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

        # Goal portal tracking - for map2.txt the goal is 'up' portal
        self.goal_portal_direction = self.portals[0].direction if self.portals else 'up'

        # Seamless portal warp transition variables
        self.warp_out_active = False
        self.warp_out_timer = 0.0
        self.warp_out_duration = 0.65

        # ============================================================
        # UI & TYPOGRAPHY TOKENS (Complete Philippine Peso P Support)
        # ============================================================
        self.font_family = ["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial"]
        self.show_info = True
        self.font = self.get_ui_font(16)
        self.small_font = self.get_ui_font(12)

        # High-Resolution Modal Dialog Typography Tokens
        self.dialog_header_font = self.get_ui_font(16, bold=True)
        self.dialog_q_font = self.get_ui_font(15)
        self.dialog_choice_font = self.get_ui_font(14, bold=True)
        self.dialog_badge_font = self.get_ui_font(16, bold=True)
        self.dialog_hint_font = self.get_ui_font(13, bold=True)
        self.dialog_stat_font = self.get_ui_font(13, bold=True)

        # 50:50 Wizard Hint & Option Elimination Tracking
        self.eliminated_choices = set()
        self.wrong_feedback_msg = ""

        # Festive Speed Rush & Celebration Particles
        self.speed_boost_timer = 0.0
        self.fiesta_sparkles = []

        # In-World Floating Barrio Banner System
        self.banner_text = ""
        self.banner_sub = ""
        self.banner_timer = 0.0

        # Traditional Bahay Kubo Progressive Construction (Map 5 specific)
        self.kubo_pieces_collected = 0
        self.kubo_tile_x = 14
        self.kubo_tile_y = 3
        self.camera_pan_active = False
        self.camera_pan_start_time = 0
        self.pan_start_cam_x = 0
        self.pan_start_cam_y = 0
        self.kubo_piece_placed_in_pan = False
        self.award_anim_active = False
        self.award_anim_piece_idx = 0
        self.award_anim_start_time = 0
        self.kubo_construction_particles = []

        self.kubo_pieces_info = {
            1: {
                "title": "HALIGI AT SAHIG (BAMBOO STILTS & FLOOR)",
                "sub": "4 Sturdy Bamboo Stilts & Slatted Floor Platform Erected!",
                "math": "Unit Fraction: 1/4 Completed",
                "color": (217, 119, 6)
            },
            2: {
                "title": "DINDING NA SAWALI (WOVEN WALLS)",
                "sub": "Hand-woven Bamboo Slat Lattice Walls Installed!",
                "math": "Division: 20 / 4 = 5 Completed",
                "color": (180, 83, 9)
            },
            3: {
                "title": "BINTANANG CAPIZ (SHELL WINDOWS)",
                "sub": "Authentic Sliding Capiz Shell Windows Attached!",
                "math": "3D Solids: Cone, Cylinder, Cube Completed",
                "color": (251, 191, 36)
            },
            4: {
                "title": "BUBONG NA PAWID (NIPA THATCH ROOF)",
                "sub": "High-pitched Palm Leaf Thatched Roof Placed!",
                "math": "Clock Time: 8:30 AM Completed",
                "color": (161, 98, 7)
            },
            5: {
                "title": "HAGDAN AT BALKONAHE (LADDER & FIESTA FLAGS)",
                "sub": "Bamboo Entryway Ladder, Porch & Fiesta Banderitas!",
                "math": "Perimeter: 16m Garden Completed",
                "color": (34, 197, 94)
            }
        }

        # Synthesize Zero-Dependency Sound Effects
        self.load_puzzle_sounds()

        # Clock for delta time
        self.clock = pygame.time.Clock()
        self.frame_counter = 0

        # Completion flag
        self.completed = False

        # Tile animation variables
        self.tile_anim_timer = 0
        self.tile_anim_frame = 0

        # Scan map for quiz stations 1, 2, 3, 4, 5
        self.quiz_stations = {}
        for y, row in enumerate(self.game_map):
            for x, c in enumerate(row):
                if c in ['1', '2', '3', '4', '5']:
                    num = int(c)
                    self.quiz_stations[num] = (x, y)
                    print(f"[LOC] Quiz Station {num} found at: ({x}, {y})")

        # Station Standby Directions
        self.station_directions = {
            1: "right",
            2: "right",
            3: "right",
            4: "right",
            5: "right"
        }
        self.npc_knight_path = []
        self.npc_knight_path_index = 0
        # Initialize Knight at station 1 if available
        if 1 in self.quiz_stations:
            self.npc_knight_tile_x, self.npc_knight_tile_y = self.quiz_stations[1]
            self.npc_knight_x = self.npc_knight_tile_x * TILE_SIZE
            self.npc_knight_y = self.npc_knight_tile_y * TILE_SIZE
            self.npc_knight_found = True
            print(f"[STORE] Barangay Characters spawned at Quiz Stations 1-5")

        # Quiz state variables
        self.quiz_state = 0  # 0: waiting proximity, 1: dialog Q, 2: wrong try again, 3: correct phrase transition, 4: out of tries reveal, 5: final speech, 6: quiz complete
        self.quiz_station_index = 1  # current station (1-5)
        self.current_question_index = 0
        self.first_attempt_correct = {1: True, 2: True, 3: True, 4: True, 5: True}
        self.station_attempts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.selected_choice_index = -1  # choice highlighted
        self.npc_knight_dir = self.station_directions.get(1, "right")

        # Correct answer random responses
        self.current_correct_phrase = ""
        self.correct_phrases = [
            "Great job! Your math calculation is accurate!",
            "Awesome! Let's head to the next barrio stall!",
            "Well done! The Barrio Fiesta continues!"
        ]

        # Questions List (DepEd Grade 2 Curriculum: Customized per Map - No NPC Names)
        if self.map_name == "map5.txt":
            self.quiz_questions = [
                {
                    "station": 1,
                    "title": "STATION 1 - BIBINGKA FRACTIONS (1/4)",
                    "question": "A fresh circular Bibingka was sliced into 4 equal parts. Juan ate 1 slice. What fraction part of the Bibingka did Juan eat?",
                    "choices": ["A. 1/2 (One-half)", "B. 1/4 (One-fourth)", "C. 1/3 (One-third)", "D. 3/4 (Three-fourths)"],
                    "correct": 1,
                    "visual_type": "bibingka_fraction",
                    "hint": "Count the equal slices: 1 slice eaten out of 4 equal slices = 1/4 (One-fourth / Sangkapat)!"
                },
                {
                    "station": 2,
                    "title": "STATION 2 - EQUAL SHARING DIVISION (20 / 4)",
                    "question": "There are 20 ripe Carabao mangoes divided equally into 4 woven bayong baskets. How many mangoes are in each basket? (20 / 4)",
                    "choices": ["A. 4 mangoes", "B. 5 mangoes", "C. 6 mangoes", "D. 8 mangoes"],
                    "correct": 1,
                    "visual_type": "mango_division",
                    "hint": "Divide 20 mangoes into 4 equal groups: 20 / 4 = 5 mangoes per basket (5 + 5 + 5 + 5 = 20)!"
                },
                {
                    "station": 3,
                    "title": "STATION 3 - 3D GEOMETRIC SOLIDS (CONE)",
                    "question": "A traditional farmer's Salakot hat is being crafted. Which 3D geometric solid has 1 flat circular base and 1 pointed top vertex?",
                    "choices": ["A. Cube", "B. Cylinder", "C. Cone", "D. Sphere"],
                    "correct": 2,
                    "visual_type": "salakot_cone",
                    "hint": "A Cone (like a traditional Salakot hat or ice cream cone) has 1 flat circular base and 1 pointed top vertex!"
                },
                {
                    "station": 4,
                    "title": "STATION 4 - ANALOG CLOCK TIME (8:30 AM)",
                    "question": "The Grand Fiesta Parade starts at 8:30 AM. How should the hands be positioned on the analog clock at 8:30?",
                    "choices": [
                        "A. Short hand between 8 and 9, Long hand pointing at 6",
                        "B. Short hand at 12, Long hand at 8",
                        "C. Short hand at 8, Long hand at 12",
                        "D. Short hand at 6, Long hand at 8"
                    ],
                    "correct": 0,
                    "visual_type": "analog_clock",
                    "hint": "At 8:30, the short hour hand is halfway between 8 and 9, and the long minute hand points directly at 6 (30 minutes)!"
                },
                {
                    "station": 5,
                    "title": "STATION 5 - GARDEN PERIMETER (5m + 3m + 5m + 3m)",
                    "question": "A rectangular bamboo vegetable garden has a length of 5 meters and width of 3 meters. What is the total perimeter around the garden?",
                    "choices": ["A. 8 meters", "B. 15 meters", "C. 16 meters", "D. 20 meters"],
                    "correct": 2,
                    "visual_type": "garden_perimeter",
                    "hint": "Add all 4 outer sides of the rectangle: 5m + 3m + 5m + 3m = 16 meters total perimeter!"
                }
            ]
        else:
            self.quiz_questions = [
                {
                    "station": 1,
                    "title": "STATION 1 - SARI-SARI STORE SUKLI",
                    "question": "A customer bought items worth P35 and paid with a P50 bill. How much change (Sukli) should be given back? (P50 - P35)",
                    "choices": ["A. P10", "B. P15", "C. P20", "D. P25"],
                    "correct": 1,
                    "visual_type": "sari_sukli",
                    "hint": "Subtract the cost from the bill: P50 - P35 = P15 (One P10 coin + One P5 coin)!"
                },
                {
                    "station": 2,
                    "title": "STATION 2 - P25 COIN COMBINATIONS",
                    "question": "A Double Ube-Cheese Sorbetes cone costs P25. Which combination of Philippine coins equals exactly P25?",
                    "choices": ["A. One P20 coin + One P5 coin", "B. Two P10 coins + One P1 coin", "C. Three P5 coins", "D. One P10 coin + One P5 coin"],
                    "correct": 0,
                    "visual_type": "sorbetes_coins",
                    "hint": "Count the values: P20 + P5 = P25 exact payment!"
                },
                {
                    "station": 3,
                    "title": "STATION 3 - JEEPNEY FARE MULTIPLICATION",
                    "question": "3 students rode the Jeepney. The fare is P12 per student. How much is the total fare payment? (3 x P12 or P12 + P12 + P12)",
                    "choices": ["A. P24", "B. P30", "C. P36", "D. P40"],
                    "correct": 2,
                    "visual_type": "jeepney_fare",
                    "hint": "Multiply 3 passengers by P12: 3 x 12 = P36 total fare!"
                },
                {
                    "station": 4,
                    "title": "STATION 4 - PALENGKE FRUIT SCALE (MASS)",
                    "question": "One Carabao mango weighs 500 grams (g). How many mangoes are needed to weigh exactly 2 Kilograms (2,000 g)? (500g x 4 = 2,000g = 2kg)",
                    "choices": ["A. 2 mangoes", "B. 3 mangoes", "C. 4 mangoes", "D. 5 mangoes"],
                    "correct": 2,
                    "visual_type": "market_scale",
                    "hint": "Remember that 1 Kilogram = 1,000g, so 2 Kilograms = 2,000g (500g + 500g + 500g + 500g = 2,000g = 4 mangoes)!"
                },
                {
                    "station": 5,
                    "title": "STATION 5 - FIESTA PAROL BUDGET (> < =)",
                    "question": "A budget for fiesta parol making is P350. The bamboo sticks cost P120 and the papel de hapon costs P180 (Total = P300). Is the budget enough? (P350 > P300)",
                    "choices": ["A. Yes, P350 is greater than P300 (P350 > P300)", "B. No, P350 is less than P300 (P350 < P300)", "C. No, the budget is exactly equal (P350 = P300)", "D. No, she needs P100 more"],
                    "correct": 0,
                    "visual_type": "fiesta_budget",
                    "hint": "Add the materials: P120 + P180 = P300. Since P350 is greater than P300 (P350 > P300), the budget is enough!"
                }
            ]

        # Load dynamic questions from Database / Vercel API
        self.load_database_questions()

        print(f"[OK] Quarter2 initialized with map: {self.map_name}")
        print(f"   Goal portal: {self.goal_portal_direction}")
        print(f"   Portals loaded: {len(self.portals)}")


    # ============================================================
    # DATABASE INTEGRATION
    # ============================================================
    def load_database_questions(self):
        if not self.is_quiz_map:
            return
        try:
            if not db:
                return
            questions_result = db.get_questions(quarter=2)
            if not questions_result or len(questions_result) == 0:
                print("[INFO] No custom database questions found for Quarter 2. Using default curriculum questions.")
                return

            mapped_questions = []
            for row in questions_result:
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
                for idx, opt in enumerate(raw_options):
                    prefix = f"{choice_letters[idx]}. " if idx < len(choice_letters) else f"{idx+1}. "
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
                    for idx, opt in enumerate(raw_options):
                        if opt and str(opt).strip().lower() == ans.lower():
                            correct_idx = idx
                            break

                mapped_questions.append({
                    "question": prompt,
                    "choices": choices,
                    "correct": correct_idx
                })

            if mapped_questions:
                # Blend with default questions if fewer than 5
                for i in range(min(5, len(mapped_questions))):
                    if i < len(self.quiz_questions):
                        orig = self.quiz_questions[i]
                        # Preserve original game-specific visual metadata and hint fallback
                        for key in ["visual_type", "station", "title", "hint"]:
                            if key in orig and not mapped_questions[i].get(key):
                                mapped_questions[i][key] = orig[key]
                        self.quiz_questions[i] = mapped_questions[i]
                    else:
                        self.quiz_questions.append(mapped_questions[i])

                print(f"[OK] Successfully loaded {len(mapped_questions)} dynamic question(s) from Database for Quarter 2!")
        except Exception as e:
            print(f"[WARN] Exception loading database questions for Quarter 2: {e}")

    def save_results_to_database(self):
        if not self.is_quiz_map:
            return
        try:
            if not db:
                return
            student_db_id = getattr(self.main_menu, 'student_db_id', None)
            if not student_db_id:
                print("[WARN] No student_db_id available in main_menu. Skipping database record.")
                return
            total_questions = min(5, len(self.quiz_questions))
            correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
            percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 0.0
            score = int(correct_answers * 20)  # 20 points per question -> 100 max points

            assessment_id = db.get_assessment_id(quarter=2)
            if assessment_id:
                print(f"[LOG] Linked Quarter 2 result to Assessment ID: {assessment_id}")

            feedback_msg = f"Completed Quarter 2 (Barangay Geometry). Answered {correct_answers} of {total_questions} questions correctly on the first attempt."
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
                print(f"[WIN] Successfully saved Quarter 2 Game Result to Database for Student DB ID {student_db_id}!")
                print(f"   Score: {score}/{total_questions} ({percentage}%)")
            else:
                print("[WARN] Failed to save Quarter 2 game results via Database API.")
        except Exception as e:
            print(f"[WARN] Exception saving Quarter 2 game results: {e}")

    # ============================================================
    # SYNTHESIZED SOUND EFFECTS ENGINE (Zero-Dependency Audio)
    # ============================================================
    def load_puzzle_sounds(self):
        try:
            if hasattr(self, 'main_menu') and hasattr(self.main_menu, 'audio_manager'):
                am = self.main_menu.audio_manager
            else:
                from core.audio_manager import audio_manager
                am = audio_manager

            self.sorbetes_bell = am.get_sound("bell")
            self.jeepney_horn = am.get_sound("horn")
            self.coin_clink = am.get_sound("coin")
            self.cash_register = am.get_sound("cash_register")
            self.snap_sound = am.get_sound("snap")
            self.success_sound = am.get_sound("success")
            self.wood_snap_sound = am.get_sound("wood_snap")

            if self.sorbetes_bell and self.coin_clink and self.snap_sound:
                print("[AUDIO] Quarter 2 sound effects retrieved from AudioManager.")
                return

            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2)
            sr = 44100

            # 1. Manong Sorbetero Bronze Bell ("Kling-kling!")
            t_bell = np.linspace(0, 0.35, int(sr * 0.35), False)
            w_bell = 0.6 * np.sin(2 * np.pi * 1568 * t_bell) + 0.4 * np.sin(2 * np.pi * 2093 * t_bell)
            env_bell = np.exp(-t_bell * 10)
            a_bell = (w_bell * env_bell * 32000).astype(np.int16)
            self.sorbetes_bell = pygame.sndarray.make_sound(np.column_stack((a_bell, a_bell)))

            # 2. Kuya Drayber Sarao Jeepney Horn ("Beep-beep!")
            t_horn = np.linspace(0, 0.28, int(sr * 0.28), False)
            w_horn = 0.5 * np.sin(2 * np.pi * 440 * t_horn) + 0.5 * np.sin(2 * np.pi * 554 * t_horn)
            env_horn = np.ones_like(t_horn)
            env_horn[-int(sr * 0.04):] = np.linspace(1, 0, int(sr * 0.04))
            a_horn = (w_horn * env_horn * 28000).astype(np.int16)
            self.jeepney_horn = pygame.sndarray.make_sound(np.column_stack((a_horn, a_horn)))

            # 3. Metallic Coin Clink ("Clink!")
            t_coin = np.linspace(0, 0.18, int(sr * 0.18), False)
            w_coin = 0.7 * np.sin(2 * np.pi * 2489 * t_coin) + 0.3 * np.sin(2 * np.pi * 3322 * t_coin)
            env_coin = np.exp(-t_coin * 20)
            a_coin = (w_coin * env_coin * 30000).astype(np.int16)
            self.coin_clink = pygame.sndarray.make_sound(np.column_stack((a_coin, a_coin)))

            # 4. Cash Register / Sukli Chime
            t_reg = np.linspace(0, 0.3, int(sr * 0.3), False)
            w_reg = 0.5 * np.sin(2 * np.pi * 1046 * t_reg) + 0.5 * np.sin(2 * np.pi * 1318 * t_reg)
            env_reg = np.exp(-t_reg * 12)
            a_reg = (w_reg * env_reg * 30000).astype(np.int16)
            self.cash_register = pygame.sndarray.make_sound(np.column_stack((a_reg, a_reg)))

            # 5. Snap / Selection Pop
            t_snap = np.linspace(0, 0.08, int(sr * 0.08), False)
            w_snap = np.sin(2 * np.pi * 900 * t_snap) * np.exp(-t_snap * 40)
            a_snap = (w_snap * 28000).astype(np.int16)
            self.snap_sound = pygame.sndarray.make_sound(np.column_stack((a_snap, a_snap)))

            # 6. Grand Fiesta Success Fanfare
            t_fan = np.linspace(0, 0.7, int(sr * 0.7), False)
            w_fan = (
                0.35 * np.sin(2 * np.pi * 523.25 * t_fan) +
                0.35 * np.sin(2 * np.pi * 659.25 * t_fan) +
                0.30 * np.sin(2 * np.pi * 783.99 * t_fan)
            )
            env_fan = np.ones_like(t_fan)
            env_fan[-int(sr * 0.15):] = np.linspace(1, 0, int(sr * 0.15))
            a_fan = (w_fan * env_fan * 32000).astype(np.int16)
            self.success_sound = pygame.sndarray.make_sound(np.column_stack((a_fan, a_fan)))

            # 7. Bamboo Construction Knock / Snap
            t_wood = np.linspace(0, 0.14, int(sr * 0.14), False)
            w_wood = (0.6 * np.sin(2 * np.pi * 320 * t_wood) + 0.4 * np.sin(2 * np.pi * 560 * t_wood)) * np.exp(-t_wood * 30)
            a_wood = (w_wood * 30000).astype(np.int16)
            self.wood_snap_sound = pygame.sndarray.make_sound(np.column_stack((a_wood, a_wood)))

            print("[AUDIO] Quarter 2 Barrio sound effects synthesized successfully.")
        except Exception as e:
            print(f"[WARN] Audio synthesis note: {e}")
            self.sorbetes_bell = None
            self.jeepney_horn = None
            self.coin_clink = None
            self.cash_register = None
            self.snap_sound = None
            self.success_sound = None
            self.wood_snap_sound = None

    # ============================================================
    # FONT ENGINE WITH PHILIPPINE PESO (P) SUPPORT
    # ============================================================
    def get_ui_font(self, size, bold=False):
        """Returns a high-legibility system font with full Philippine Peso (P) character support"""
        return pygame.font.SysFont(["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial"], size, bold=bold)

    # ============================================================
    # VECTOR PHILIPPINE CURRENCY & MEASUREMENT ENGINE
    # ============================================================
    def draw_peso_coin(self, surf, center_x, center_y, radius, value_str, style="gold"):
        """Draws crisp vector Philippine Peso coin (P1, P5, P10, P20)"""
        cx, cy = int(center_x), int(center_y)
        r = int(radius)
        if style == "bimetal_gold": # P20 coin (Bronze core, silver outer ring)
            pygame.draw.circle(surf, (203, 213, 225), (cx, cy), r)
            pygame.draw.circle(surf, (148, 163, 184), (cx, cy), r, 2)
            pygame.draw.circle(surf, (217, 119, 6), (cx, cy), int(r * 0.72))
            pygame.draw.circle(surf, (251, 191, 36), (cx, cy), int(r * 0.72), 2)
            val_col = (255, 255, 255)
        elif style == "bimetal_silver": # P10 coin (Silver core, brass ring)
            pygame.draw.circle(surf, (245, 158, 11), (cx, cy), r)
            pygame.draw.circle(surf, (217, 119, 6), (cx, cy), r, 2)
            pygame.draw.circle(surf, (226, 232, 240), (cx, cy), int(r * 0.72))
            pygame.draw.circle(surf, (148, 163, 184), (cx, cy), int(r * 0.72), 2)
            val_col = (15, 23, 42)
        elif style == "brass": # P5 coin
            pygame.draw.circle(surf, (234, 179, 8), (cx, cy), r)
            pygame.draw.circle(surf, (202, 138, 4), (cx, cy), r, 2)
            pygame.draw.circle(surf, (253, 224, 71), (cx, cy), int(r * 0.78), 1)
            val_col = (15, 23, 42)
        else: # P1 coin (Silver)
            pygame.draw.circle(surf, (203, 213, 225), (cx, cy), r)
            pygame.draw.circle(surf, (148, 163, 184), (cx, cy), r, 2)
            pygame.draw.circle(surf, (241, 245, 249), (cx, cy), int(r * 0.78), 1)
            val_col = (15, 23, 42)

        font = self.get_ui_font(max(9, int(r * 0.7)), bold=True)
        txt = font.render(value_str, True, val_col)
        surf.blit(txt, txt.get_rect(center=(cx, cy)))

    def draw_peso_bill(self, surf, x, y, w, h, val_str, bg_col, border_col):
        """Draws crisp vector Philippine Banknote (P20, P50, P100, P200, P500, P1000)"""
        b_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, bg_col, b_rect, border_radius=6)
        pygame.draw.rect(surf, border_col, b_rect, 2, border_radius=6)
        pygame.draw.rect(surf, (255, 255, 255, 60), b_rect.inflate(-6, -6), 1, border_radius=4)

        f_val = self.get_ui_font(max(10, int(h * 0.38)), bold=True)
        f_sub = self.get_ui_font(max(8, int(h * 0.22)), bold=True)

        v_surf = f_val.render(val_str, True, (255, 255, 255))
        surf.blit(v_surf, (x + 8, y + 4))

        p_surf = f_sub.render("PILIPINAS", True, (254, 240, 138))
        surf.blit(p_surf, (x + w - p_surf.get_width() - 8, y + 4))

        seal_rect = pygame.Rect(x + w // 2 - 8, y + h // 2 - 8, 16, 16)
        pygame.draw.circle(surf, (255, 255, 255, 120), seal_rect.center, 8)
        pygame.draw.circle(surf, border_col, seal_rect.center, 8, 1)

    def draw_money_visualizer(self, q_data, vis_rect):
        """Renders the authentic visual mathematical model for Grade 2 Quarter 2"""
        # Outer Card
        pygame.draw.rect(self.screen, (15, 23, 42), vis_rect, border_radius=12)
        pygame.draw.rect(self.screen, (218, 165, 32), vis_rect, 2, border_radius=12)

        v_type = q_data.get("visual_type", "")
        q_text = (q_data.get("question", "") + " " + q_data.get("title", "")).lower()

        # Station 1: Tomas' Sari-Sari Store Sukli Calculator
        if v_type == "sari_sukli" or "sukli" in q_text or "change" in q_text:
            # 1. P50 Bill on the left
            b_x = vis_rect.left + 24
            b_y = vis_rect.centery - 36
            self.draw_peso_bill(self.screen, b_x, b_y, 110, 56, "P50", (220, 38, 38), (248, 113, 113))
            
            # Minus sign
            m_font = self.get_ui_font(22, bold=True)
            m_surf = m_font.render("-", True, (255, 215, 0))
            self.screen.blit(m_surf, (b_x + 125, vis_rect.centery - 18))

            # 2. Purchase Cost Tag (P35) in the middle
            cost_rect = pygame.Rect(b_x + 155, vis_rect.centery - 34, 100, 52)
            pygame.draw.rect(self.screen, (30, 41, 59), cost_rect, border_radius=8)
            pygame.draw.rect(self.screen, (245, 158, 11), cost_rect, 2, border_radius=8)
            
            c_lbl = self.dialog_hint_font.render("Purchase:", True, (203, 213, 225))
            self.screen.blit(c_lbl, (cost_rect.x + (cost_rect.w - c_lbl.get_width()) // 2, cost_rect.y + 6))
            p_val = m_font.render("P35", True, (251, 191, 36))
            self.screen.blit(p_val, (cost_rect.x + (cost_rect.w - p_val.get_width()) // 2, cost_rect.y + 24))

            # Equals sign
            eq_surf = m_font.render("=", True, (255, 215, 0))
            self.screen.blit(eq_surf, (cost_rect.right + 15, vis_rect.centery - 18))

            # 3. Sukli Jar (P15 = P10 + P5) on the right
            jar_rect = pygame.Rect(cost_rect.right + 45, vis_rect.centery - 40, 180, 64)
            pygame.draw.rect(self.screen, (6, 78, 59), jar_rect, border_radius=10)
            pygame.draw.rect(self.screen, (34, 197, 94), jar_rect, 2, border_radius=10)
            
            j_lbl = self.dialog_hint_font.render("Exact Sukli: P15", True, (187, 247, 208))
            self.screen.blit(j_lbl, (jar_rect.x + (jar_rect.w - j_lbl.get_width()) // 2, jar_rect.y + 6))
            
            self.draw_peso_coin(self.screen, jar_rect.x + 55, jar_rect.y + 40, 15, "P10", "bimetal_silver")
            self.draw_peso_coin(self.screen, jar_rect.x + 125, jar_rect.y + 40, 14, "P5", "brass")

            lbl = self.dialog_stat_font.render("Sukli Model: P50 (Bayad) - P35 (Halaga) = P15 (Sukli)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 2: Manong Sorbetero Coin Combinations (P25)
        elif v_type == "sorbetes_coins" or "sorbetes" in q_text or "25" in q_text:
            # 1. Ice cream cone on left
            cone_rect = pygame.Rect(vis_rect.left + 35, vis_rect.centery - 42, 90, 70)
            pygame.draw.rect(self.screen, (30, 41, 59), cone_rect, border_radius=8)
            pygame.draw.rect(self.screen, (245, 158, 11), cone_rect, 2, border_radius=8)
            
            # Draw Ice Cream scoops (Ube & Cheese)
            pygame.draw.circle(self.screen, (147, 51, 234), (cone_rect.centerx, cone_rect.top + 20), 14)
            pygame.draw.circle(self.screen, (245, 158, 11), (cone_rect.centerx, cone_rect.top + 34), 13)
            # Cone waffle
            pygame.draw.polygon(self.screen, (180, 83, 9), [(cone_rect.centerx - 12, cone_rect.top + 38),
                                                            (cone_rect.centerx + 12, cone_rect.top + 38),
                                                            (cone_rect.centerx, cone_rect.bottom - 4)])
            
            # Equals sign
            m_font = self.get_ui_font(22, bold=True)
            eq_surf = m_font.render("=", True, (255, 215, 0))
            self.screen.blit(eq_surf, (cone_rect.right + 20, vis_rect.centery - 18))

            # 2. Coin Combination Wallet (One P20 coin + One P5 coin = P25)
            wallet_rect = pygame.Rect(cone_rect.right + 55, vis_rect.centery - 40, 360, 68)
            pygame.draw.rect(self.screen, (30, 41, 59), wallet_rect, border_radius=10)
            pygame.draw.rect(self.screen, (251, 191, 36), wallet_rect, 2, border_radius=10)

            w_lbl = self.dialog_hint_font.render("Target Amount: P25.00", True, (254, 240, 138))
            self.screen.blit(w_lbl, (wallet_rect.left + 16, wallet_rect.top + 8))

            # Draw P20 coin and P5 coin
            self.draw_peso_coin(self.screen, wallet_rect.left + 220, wallet_rect.centery + 4, 20, "P20", "bimetal_gold")
            plus_s = m_font.render("+", True, (255, 215, 0))
            self.screen.blit(plus_s, (wallet_rect.left + 252, wallet_rect.centery - 12))
            self.draw_peso_coin(self.screen, wallet_rect.left + 295, wallet_rect.centery + 4, 16, "P5", "brass")

            lbl = self.dialog_stat_font.render("Coin Value Model: One P20 Bimetal Coin + One P5 Coin = P25", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 3: Kuya Drayber "Bayad Po!" Jeepney Fare Multiplication
        elif v_type == "jeepney_fare" or "fare" in q_text or "jeep" in q_text or "pasada" in q_text:
            # 3 Passengers with P12 fare coins
            pass_w = 110
            start_x = vis_rect.left + 40
            for pi in range(3):
                p_rect = pygame.Rect(start_x + pi * (pass_w + 20), vis_rect.centery - 40, pass_w, 64)
                pygame.draw.rect(self.screen, (30, 41, 59), p_rect, border_radius=10)
                pygame.draw.rect(self.screen, (59, 130, 246), p_rect, 2, border_radius=10)
                
                p_txt = self.dialog_hint_font.render(f"Student {pi+1}", True, (147, 197, 253))
                self.screen.blit(p_txt, (p_rect.x + (p_rect.w - p_txt.get_width()) // 2, p_rect.y + 6))
                
                self.draw_peso_coin(self.screen, p_rect.centerx - 12, p_rect.y + 40, 13, "P10", "bimetal_silver")
                self.draw_peso_coin(self.screen, p_rect.centerx + 14, p_rect.y + 40, 11, "P2", "silver")

            # Equals / Total Fare
            m_font = self.get_ui_font(22, bold=True)
            eq_surf = m_font.render("=", True, (255, 215, 0))
            self.screen.blit(eq_surf, (start_x + 3 * (pass_w + 20), vis_rect.centery - 18))

            tot_rect = pygame.Rect(start_x + 3 * (pass_w + 20) + 25, vis_rect.centery - 40, 110, 64)
            pygame.draw.rect(self.screen, (6, 78, 59), tot_rect, border_radius=10)
            pygame.draw.rect(self.screen, (34, 197, 94), tot_rect, 2, border_radius=10)
            
            t_lbl = self.dialog_hint_font.render("Total Fare:", True, (187, 247, 208))
            self.screen.blit(t_lbl, (tot_rect.x + (tot_rect.w - t_lbl.get_width()) // 2, tot_rect.y + 8))
            t_val = m_font.render("P36", True, (251, 191, 36))
            self.screen.blit(t_val, (tot_rect.x + (tot_rect.w - t_val.get_width()) // 2, tot_rect.y + 28))

            lbl = self.dialog_stat_font.render("Rate Model: 3 Passengers x P12 = P12 + P12 + P12 = P36", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 4: Ate Maya Palengke Timbangan (Mass in g & kg)
        elif v_type == "market_scale" or "mango" in q_text or "scale" in q_text or "gram" in q_text or "kg" in q_text:
            # 1. Market Dial Scale (Timbangan) on left
            scale_cx = vis_rect.left + 120
            scale_cy = vis_rect.centery - 10
            r_scale = 36
            
            pygame.draw.circle(self.screen, (241, 245, 249), (scale_cx, scale_cy), r_scale)
            pygame.draw.circle(self.screen, (180, 83, 9), (scale_cx, scale_cy), r_scale, 3)
            # Ticks
            for step in range(8):
                ang = step * (math.pi / 4)
                pygame.draw.line(self.screen, (71, 85, 105),
                                 (scale_cx + int(26 * math.cos(ang)), scale_cy + int(26 * math.sin(ang))),
                                 (scale_cx + int(32 * math.cos(ang)), scale_cy + int(32 * math.sin(ang))), 2)
            # Pointer needle pointing to 2kg (top right)
            pygame.draw.line(self.screen, (220, 38, 38), (scale_cx, scale_cy), (scale_cx + 20, scale_cy - 20), 3)
            pygame.draw.circle(self.screen, (15, 23, 42), (scale_cx, scale_cy), 5)
            
            s_tag = self.dialog_hint_font.render("2.0 kg", True, (255, 215, 0))
            self.screen.blit(s_tag, (scale_cx - s_tag.get_width() // 2, scale_cy + r_scale + 4))

            # 2. 4 Carabao Mangoes (500g each)
            m_start_x = scale_cx + 80
            for mi in range(4):
                mx = m_start_x + mi * 75
                my = vis_rect.centery - 32
                m_rect = pygame.Rect(mx, my, 65, 52)
                pygame.draw.rect(self.screen, (30, 41, 59), m_rect, border_radius=8)
                pygame.draw.rect(self.screen, (234, 179, 8), m_rect, 2, border_radius=8)
                
                # Mango shape
                pygame.draw.ellipse(self.screen, (245, 158, 11), (mx + 12, my + 6, 26, 18))
                pygame.draw.circle(self.screen, (34, 197, 94), (mx + 36, my + 8), 3)
                
                g_lbl = self.dialog_stat_font.render("500g", True, (254, 240, 138))
                self.screen.blit(g_lbl, (mx + (m_rect.w - g_lbl.get_width()) // 2, my + 28))

            lbl = self.dialog_stat_font.render("Metric Mass Model: 4 Mangoes x 500g = 2,000g = 2 Kilograms (2kg)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 5: Lola Rosa Fiesta Budget Comparison (> < =)
        elif v_type == "fiesta_budget" or "budget" in q_text or "parol" in q_text or "greater" in q_text or ">" in q_text:
            # 1. Budget Card (P350)
            b_rect = pygame.Rect(vis_rect.left + 35, vis_rect.centery - 38, 160, 60)
            pygame.draw.rect(self.screen, (6, 78, 59), b_rect, border_radius=10)
            pygame.draw.rect(self.screen, (34, 197, 94), b_rect, 2, border_radius=10)
            
            b_lbl = self.dialog_hint_font.render("Lola's Budget:", True, (187, 247, 208))
            self.screen.blit(b_lbl, (b_rect.x + 12, b_rect.y + 6))
            m_font = self.get_ui_font(20, bold=True)
            b_val = m_font.render("P350.00", True, (254, 240, 138))
            self.screen.blit(b_val, (b_rect.x + 12, b_rect.y + 26))

            # 2. Relation Symbol ( > )
            rel_font = self.get_ui_font(28, bold=True)
            rel_surf = rel_font.render(">", True, (255, 215, 0))
            self.screen.blit(rel_surf, (b_rect.right + 25, vis_rect.centery - 22))

            # 3. Materials Cost (P120 + P180 = P300)
            cost_rect = pygame.Rect(b_rect.right + 75, vis_rect.centery - 38, 240, 60)
            pygame.draw.rect(self.screen, (30, 41, 59), cost_rect, border_radius=10)
            pygame.draw.rect(self.screen, (245, 158, 11), cost_rect, 2, border_radius=10)
            
            c_lbl = self.dialog_hint_font.render("Materials: P120 + P180", True, (203, 213, 225))
            self.screen.blit(c_lbl, (cost_rect.x + 12, cost_rect.y + 6))
            c_val = m_font.render("Total: P300.00", True, (251, 191, 36))
            self.screen.blit(c_val, (cost_rect.x + 12, cost_rect.y + 26))

            lbl = self.dialog_stat_font.render("Budget Comparison: P350 > P300 (Kasya ang Pera para sa Pista!)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 1 (Map 5): Aling Nena's Bibingka Fractions (1/4)
        elif v_type == "bibingka_fraction" or "bibingka" in q_text or "fraction" in q_text:
            b_cx = vis_rect.left + 80
            b_cy = vis_rect.centery - 8
            r_bib = 34
            # Banana leaf base
            pygame.draw.circle(self.screen, (22, 101, 52), (b_cx, b_cy), r_bib + 6)
            pygame.draw.circle(self.screen, (34, 197, 94), (b_cx, b_cy), r_bib + 6, 2)
            # Full Bibingka base
            pygame.draw.circle(self.screen, (254, 240, 138), (b_cx, b_cy), r_bib)
            # Highlight Juan's 1/4 slice (top right 0 to 90 deg)
            wedge_pts = [(b_cx, b_cy)]
            for deg in range(0, 91, 5):
                rad = math.radians(deg)
                wedge_pts.append((b_cx + r_bib * math.cos(rad), b_cy - r_bib * math.sin(rad)))
            pygame.draw.polygon(self.screen, (251, 191, 36), wedge_pts)
            pygame.draw.polygon(self.screen, (217, 119, 6), wedge_pts, 2)
            # Divider cuts (4 equal parts)
            pygame.draw.line(self.screen, (180, 83, 9), (b_cx - r_bib, b_cy), (b_cx + r_bib, b_cy), 2)
            pygame.draw.line(self.screen, (180, 83, 9), (b_cx, b_cy - r_bib), (b_cx, b_cy + r_bib), 2)
            
            # Card info
            f_rect = pygame.Rect(b_cx + 50, vis_rect.centery - 38, 380, 60)
            pygame.draw.rect(self.screen, (30, 41, 59), f_rect, border_radius=10)
            pygame.draw.rect(self.screen, (251, 191, 36), f_rect, 2, border_radius=10)
            
            m_font = self.get_ui_font(26, bold=True)
            f_val = m_font.render("1/4", True, (255, 215, 0))
            self.screen.blit(f_val, (f_rect.x + 20, f_rect.centery - 16))
            
            t1 = self.dialog_hint_font.render("- Numerator (1): 1 Slice eaten by Juan", True, (254, 240, 138))
            t2 = self.dialog_hint_font.render("- Denominator (4): 4 Total Equal Slices in the Bibingka", True, (187, 247, 208))
            self.screen.blit(t1, (f_rect.x + 85, f_rect.y + 8))
            self.screen.blit(t2, (f_rect.x + 85, f_rect.y + 30))

            lbl = self.dialog_stat_font.render("Unit Fraction Model: 1 part out of 4 equal parts = 1/4 (One-fourth / Sangkapat)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 2 (Map 5): Kuya Jun's Mango Harvest Division (20 / 4 = 5)
        elif v_type == "mango_division" or "division" in q_text or "basket" in q_text or "bayong" in q_text:
            start_x = vis_rect.left + 35
            b_w = 100
            for bi in range(4):
                bx = start_x + bi * (b_w + 14)
                by = vis_rect.centery - 38
                b_rect = pygame.Rect(bx, by, b_w, 60)
                pygame.draw.rect(self.screen, (30, 41, 59), b_rect, border_radius=8)
                pygame.draw.rect(self.screen, (245, 158, 11), b_rect, 2, border_radius=8)
                
                b_lbl = self.dialog_hint_font.render(f"Bayong {bi+1}", True, (254, 240, 138))
                self.screen.blit(b_lbl, (bx + (b_w - b_lbl.get_width()) // 2, by + 4))
                
                # 5 Mangoes in each basket
                for mi in range(5):
                    mx = bx + 12 + (mi % 3) * 26
                    my = by + 26 + (mi // 3) * 16
                    pygame.draw.ellipse(self.screen, (251, 191, 36), (mx, my, 18, 12))
                    pygame.draw.circle(self.screen, (34, 197, 94), (mx + 14, my + 2), 2)
                    
            lbl = self.dialog_stat_font.render("Division Model: 20 Mangoes / 4 Baskets = 5 Mangoes in Each Basket (5+5+5+5=20)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 3 (Map 5): Mang Berto's 3D Geometric Solids (Salakot Cone)
        elif v_type == "salakot_cone" or "cone" in q_text or "salakot" in q_text or "solid" in q_text:
            start_x = vis_rect.left + 40
            # 1. Cone (Salakot)
            c1_rect = pygame.Rect(start_x, vis_rect.centery - 40, 140, 64)
            pygame.draw.rect(self.screen, (6, 78, 59), c1_rect, border_radius=8)
            pygame.draw.rect(self.screen, (34, 197, 94), c1_rect, 2, border_radius=8)
            # Draw Cone
            pygame.draw.polygon(self.screen, (245, 158, 11), [(c1_rect.centerx, c1_rect.top + 8),
                                                              (c1_rect.centerx - 22, c1_rect.top + 40),
                                                              (c1_rect.centerx + 22, c1_rect.top + 40)])
            pygame.draw.ellipse(self.screen, (217, 119, 6), (c1_rect.centerx - 22, c1_rect.top + 34, 44, 12))
            l1 = self.dialog_hint_font.render("CONE (Salakot) - OK", True, (74, 222, 128))
            self.screen.blit(l1, (c1_rect.centerx - l1.get_width() // 2, c1_rect.bottom - 18))

            # 2. Cylinder (Bamboo Kawayan)
            c2_rect = pygame.Rect(start_x + 155, vis_rect.centery - 40, 140, 64)
            pygame.draw.rect(self.screen, (30, 41, 59), c2_rect, border_radius=8)
            pygame.draw.rect(self.screen, (59, 130, 246), c2_rect, 2, border_radius=8)
            pygame.draw.rect(self.screen, (34, 197, 94), (c2_rect.centerx - 16, c2_rect.top + 12, 32, 28))
            pygame.draw.ellipse(self.screen, (22, 101, 52), (c2_rect.centerx - 16, c2_rect.top + 6, 32, 12))
            pygame.draw.ellipse(self.screen, (22, 101, 52), (c2_rect.centerx - 16, c2_rect.top + 34, 32, 12))
            l2 = self.dialog_hint_font.render("CYLINDER (2 Bases)", True, (147, 197, 253))
            self.screen.blit(l2, (c2_rect.centerx - l2.get_width() // 2, c2_rect.bottom - 18))

            # 3. Cube (Bahay Box)
            c3_rect = pygame.Rect(start_x + 310, vis_rect.centery - 40, 140, 64)
            pygame.draw.rect(self.screen, (30, 41, 59), c3_rect, border_radius=8)
            pygame.draw.rect(self.screen, (148, 163, 184), c3_rect, 2, border_radius=8)
            pygame.draw.rect(self.screen, (218, 165, 32), (c3_rect.centerx - 16, c3_rect.top + 10, 32, 32), border_radius=2)
            l3 = self.dialog_hint_font.render("CUBE (6 Faces)", True, (203, 213, 225))
            self.screen.blit(l3, (c3_rect.centerx - l3.get_width() // 2, c3_rect.bottom - 18))

            lbl = self.dialog_stat_font.render("3D Geometric Solid: Salakot = Cone (May 1 Patag na Base at 1 Vertex sa Tuktok)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 4 (Map 5): Kapitan Dan's Analog Clock Time (8:30 AM)
        elif v_type == "analog_clock" or "clock" in q_text or "time" in q_text or "8:30" in q_text:
            c_cx = vis_rect.left + 85
            c_cy = vis_rect.centery - 8
            r_clock = 34
            pygame.draw.circle(self.screen, (248, 250, 252), (c_cx, c_cy), r_clock)
            pygame.draw.circle(self.screen, (218, 165, 32), (c_cx, c_cy), r_clock, 3)
            # Hour ticks
            for step in range(12):
                ang = step * (math.pi / 6)
                pygame.draw.line(self.screen, (71, 85, 105),
                                 (c_cx + int(26 * math.cos(ang)), c_cy + int(26 * math.sin(ang))),
                                 (c_cx + int(31 * math.cos(ang)), c_cy + int(31 * math.sin(ang))), 2)
            # Short hour hand at 8:30 (pointing halfway between 8 and 9)
            h_ang = math.radians(255 - 90)
            pygame.draw.line(self.screen, (59, 130, 246), (c_cx, c_cy),
                             (c_cx + int(18 * math.cos(h_ang)), c_cy + int(18 * math.sin(h_ang))), 4)
            # Long minute hand at 6 (pointing straight down at 30 mins)
            m_ang = math.radians(180 - 90)
            pygame.draw.line(self.screen, (239, 68, 68), (c_cx, c_cy),
                             (c_cx + int(26 * math.cos(m_ang)), c_cy + int(26 * math.sin(m_ang))), 3)
            pygame.draw.circle(self.screen, (15, 23, 42), (c_cx, c_cy), 4)

            # Digital readout & explanation card
            t_rect = pygame.Rect(c_cx + 55, vis_rect.centery - 38, 360, 60)
            pygame.draw.rect(self.screen, (30, 41, 59), t_rect, border_radius=10)
            pygame.draw.rect(self.screen, (34, 197, 94), t_rect, 2, border_radius=10)
            
            m_font = self.get_ui_font(22, bold=True)
            d_val = m_font.render("8:30 AM", True, (74, 222, 128))
            self.screen.blit(d_val, (t_rect.x + 20, t_rect.centery - 14))

            t1 = self.dialog_hint_font.render("- Short Hand: Halfway between 8 and 9 (Hour 8)", True, (254, 240, 138))
            t2 = self.dialog_hint_font.render("- Long Hand: Points directly at 6 (30 Minutes)", True, (187, 247, 208))
            self.screen.blit(t1, (t_rect.x + 115, t_rect.y + 8))
            self.screen.blit(t2, (t_rect.x + 115, t_rect.y + 30))

            lbl = self.dialog_stat_font.render("Analog Clock Model: Short Hand between 8 & 9 + Long Hand at 6 = 8:30 AM", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Station 5 (Map 5): Tito Dante's Bamboo Garden Perimeter (5m + 3m + 5m + 3m)
        elif v_type == "garden_perimeter" or "perimeter" in q_text or "garden" in q_text:
            g_rect = pygame.Rect(vis_rect.left + 45, vis_rect.centery - 36, 180, 56)
            pygame.draw.rect(self.screen, (20, 83, 45), g_rect, border_radius=6)
            pygame.draw.rect(self.screen, (217, 119, 6), g_rect, 3, border_radius=6)
            
            # Side dimension tags
            top_tag = self.dialog_hint_font.render("Length = 5m", True, (254, 240, 138))
            self.screen.blit(top_tag, (g_rect.centerx - top_tag.get_width() // 2, g_rect.top - 16))
            bot_tag = self.dialog_hint_font.render("Length = 5m", True, (254, 240, 138))
            self.screen.blit(bot_tag, (g_rect.centerx - bot_tag.get_width() // 2, g_rect.bottom + 2))
            left_tag = self.dialog_hint_font.render("3m", True, (187, 247, 208))
            self.screen.blit(left_tag, (g_rect.left - left_tag.get_width() - 4, g_rect.centery - 8))
            right_tag = self.dialog_hint_font.render("3m", True, (187, 247, 208))
            self.screen.blit(right_tag, (g_rect.right + 4, g_rect.centery - 8))

            # Formula card
            p_rect = pygame.Rect(g_rect.right + 40, vis_rect.centery - 38, 230, 60)
            pygame.draw.rect(self.screen, (30, 41, 59), p_rect, border_radius=10)
            pygame.draw.rect(self.screen, (251, 191, 36), p_rect, 2, border_radius=10)
            
            p1 = self.dialog_hint_font.render("Perimeter = 5m + 3m + 5m + 3m", True, (203, 213, 225))
            m_font = self.get_ui_font(20, bold=True)
            p2 = m_font.render("Total = 16 Meters", True, (251, 191, 36))
            self.screen.blit(p1, (p_rect.x + 12, p_rect.y + 6))
            self.screen.blit(p2, (p_rect.x + 12, p_rect.y + 26))

            lbl = self.dialog_stat_font.render("Perimeter Model: 5m + 3m + 5m + 3m = 16 Meters (Kabuuang Sukat ng Paligid)", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 22))

        # Dynamic Generic Fallback
        else:
            hint_txt = q_data.get("hint", "Suriin nang mabuti ang mga pagpipilian at piliin ang tamang sagot sa ibaba!")
            # Stylized Fiesta Coin Icon
            self.draw_peso_coin(self.screen, vis_rect.centerx, vis_rect.centery - 16, 22, "P", "bimetal_gold")
            
            h_surf = self.dialog_hint_font.render(f"{hint_txt}", True, (253, 230, 138))
            self.screen.blit(h_surf, (vis_rect.centerx - h_surf.get_width() // 2, vis_rect.bottom - 24))

    # ============================================================
    # RAYCASTING LINE-OF-SIGHT ENGINE (No triggering through walls)
    # ============================================================
    def has_line_of_sight(self, t1_x, t1_y, t2_x, t2_y):
        """Checks if there are no solid wall tiles between tile 1 and tile 2 using fine raycasting"""
        dx = abs(t2_x - t1_x)
        dy = abs(t2_y - t1_y)
        x, y = t1_x, t1_y
        n = 1 + dx + dy
        x_inc = 1 if t2_x > t1_x else -1
        y_inc = 1 if t2_y > t1_y else -1
        error = dx - dy
        dx *= 2
        dy *= 2

        for _ in range(n):
            if (x, y) != (t1_x, t1_y) and (x, y) != (t2_x, t2_y):
                if 0 <= y < len(self.game_map) and 0 <= x < len(self.game_map[y]):
                    c = self.game_map[y][x]
                    if c not in self.WALKABLE_TILES:
                        return False
            if error > 0:
                x += x_inc
                error -= dy
            elif error < 0:
                y += y_inc
                error += dx
            else:
                x += x_inc
                y += y_inc
                error -= dy
                error += dx
        return True

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
        def load_tile(filename, is_q2=False):
            if is_q2:
                path = os.path.join(self.OBJECTS_PATH, "quarter2tiles", filename)
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
                if is_q2:
                    return load_tile(filename, is_q2=False)
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((40, 45, 55))
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

        # Overwrite G and T with Q2 tiles for Quarter 2 Maps
        tiles["G"] = load_tile("grass.png", is_q2=True)
        tiles["T"] = load_tile("tree_pine_very_tall_clean.png", is_q2=True)

        # New Q2 tiles
        q2_tiles = {
            "a": "barrel_clean.png",
            "b": "barrel_moss.png",
            "c": "bush_large_flowers_1.png",
            "F": "bush_large_flowers_2.png",
            "g": "crate_clean_crossed.png",
            "h": "crate_clean_plain.png",
            "i": "crate_moss_crossed.png",
            "j": "fence_moss_horizontal_1.png",
            "o": "tree_pine_medium_clean.png",
            "p": "tree_pine_medium_moss.png",
            "q": "crate_moss_question.png",
            "Z": "ruin1.png",
            "M": "ruin2.png",
            "n": "ruin3.png",
            "s": "ruin4.png",
            "t": "ruin5.png",
            "J": "ruin6.png",
            "Q": "ruin7.png",
            "V": "ruin8.png",
            "X": "ruin9.png",
            "Y": "ruin10.png"
        }

        for key, filename in q2_tiles.items():
            tiles[key] = load_tile(filename, is_q2=True)

        # Animated Q2 tiles (chests and flags)
        for i in range(4):
            tiles[f"chest_green_{i}"] = load_tile(f"chest_green_{i}.png", is_q2=True)
            tiles[f"flag_hanging_red_{i}"] = load_tile(f"flag_hanging_red_{i}.png", is_q2=True)

        # Synthesize procedural geometric stone floor and polygon runes
        procedural_assets = self.generate_procedural_q2_assets()
        tiles.update(procedural_assets)
        tiles["a"] = procedural_assets["prop_planter_urn"]
        tiles["b"] = procedural_assets["prop_streetlamp"]
        tiles["c"] = procedural_assets["prop_park_bench"]
        tiles["g"] = procedural_assets["prop_fruit_crate"]
        tiles["h"] = procedural_assets["prop_bottle_crate"]
        tiles["i"] = procedural_assets["prop_ihawan"]
        tiles["F"] = procedural_assets["prop_planter_urn"]

        return tiles

    def generate_procedural_q2_assets(self):
        """Synthesizes rich authentic Filipino pixel-art tiles (Calle Crisologo stones, Bamboo fences, Bahay na Bato, Props)"""
        assets = {}

        # =========================================================================
        # 1. KALSADA / CALLE CRISOLOGO COBBLESTONE (Filipino Heritage Street)
        # =========================================================================
        for var in range(4):
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((226, 222, 214)) # Warm antique cobblestone base

            if var == 0:
                # Rounded Vigan River Cobblestones
                pygame.draw.rect(surf, (240, 236, 228), (2, 2, 13, 12), border_radius=3)
                pygame.draw.rect(surf, (198, 192, 182), (2, 2, 13, 12), 1, border_radius=3)
                pygame.draw.line(surf, (252, 250, 245), (4, 4), (11, 4), 1)
                
                pygame.draw.rect(surf, (234, 230, 222), (17, 2, 13, 12), border_radius=3)
                pygame.draw.rect(surf, (198, 192, 182), (17, 2, 13, 12), 1, border_radius=3)
                pygame.draw.line(surf, (248, 246, 240), (19, 4), (26, 4), 1)

                pygame.draw.rect(surf, (238, 234, 226), (9, 16, 14, 13), border_radius=3)
                pygame.draw.rect(surf, (198, 192, 182), (9, 16, 14, 13), 1, border_radius=3)
                pygame.draw.line(surf, (250, 248, 242), (11, 18), (19, 18), 1)

                pygame.draw.rect(surf, (232, 228, 220), (0, 16, 7, 13), border_radius=2)
                pygame.draw.rect(surf, (232, 228, 220), (25, 16, 7, 13), border_radius=2)
                pygame.draw.line(surf, (198, 192, 182), (7, 16), (7, 28), 1)
                pygame.draw.line(surf, (198, 192, 182), (24, 16), (24, 28), 1)

            elif var == 1:
                # Large Piedra China Granite Slabs
                pygame.draw.rect(surf, (238, 235, 228), (1, 1, 30, 30))
                pygame.draw.rect(surf, (196, 190, 180), (0, 0, 32, 32), 1)
                pygame.draw.line(surf, (252, 250, 245), (1, 1), (30, 1), 1)
                pygame.draw.line(surf, (252, 250, 245), (1, 1), (1, 30), 1)
                pygame.draw.line(surf, (186, 180, 170), (1, 30), (30, 30), 1)
                pygame.draw.line(surf, (186, 180, 170), (30, 1), (30, 30), 1)
                surf.set_at((8, 10), (170, 165, 155))
                surf.set_at((22, 18), (170, 165, 155))
                surf.set_at((14, 24), (170, 165, 155))

            elif var == 2:
                # Plaza Spanish Tile with Terracotta Floral Diamond
                for r in [1, 17]:
                    for c in [1, 17]:
                        pygame.draw.rect(surf, (236, 232, 224), (c, r, 14, 14))
                        pygame.draw.rect(surf, (202, 196, 186), (c, r, 14, 14), 1)
                        pygame.draw.line(surf, (250, 248, 242), (c+1, r+1), (c+12, r+1), 1)
                pygame.draw.polygon(surf, (205, 115, 80), [(16, 11), (21, 16), (16, 21), (11, 16)])
                pygame.draw.circle(surf, (245, 200, 70), (16, 16), 2)

            else:
                # Calzada Stone Road with dusty sandy seam
                surf.fill((234, 230, 222))
                pygame.draw.rect(surf, (206, 200, 190), (0, 0, 32, 32), 1)
                pygame.draw.line(surf, (248, 245, 238), (1, 1), (30, 1), 1)
                surf.set_at((12, 8), (180, 174, 164))
                surf.set_at((24, 20), (180, 174, 164))

            assets[f"street_asphalt_{var}"] = surf

        # =========================================================================
        # 2. BAKOD NA KAWAYAN (Authentic Filipino Bamboo Fence for Perimeter Border)
        # =========================================================================
        bamboo_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        for p in range(4):
            bx = p * 8 + 1
            pygame.draw.rect(bamboo_surf, (212, 184, 88), (bx, 2, 6, 29), border_radius=2)
            pygame.draw.line(bamboo_surf, (240, 220, 130), (bx + 1, 2), (bx + 1, 30), 1)
            pygame.draw.line(bamboo_surf, (168, 140, 55), (bx + 5, 2), (bx + 5, 30), 1)
            for ny in [8, 18, 28]:
                pygame.draw.line(bamboo_surf, (135, 105, 40), (bx - 1, ny), (bx + 6, ny), 1)
                pygame.draw.line(bamboo_surf, (245, 230, 160), (bx, ny - 1), (bx + 5, ny - 1), 1)
            pygame.draw.polygon(bamboo_surf, (230, 210, 140), [(bx, 4), (bx + 5, 1), (bx + 5, 4)])

        for ry in [10, 22]:
            pygame.draw.rect(bamboo_surf, (185, 155, 65), (0, ry, 32, 4))
            pygame.draw.line(bamboo_surf, (230, 205, 120), (0, ry), (31, ry), 1)
            pygame.draw.line(bamboo_surf, (130, 100, 35), (0, ry + 3), (31, ry + 3), 1)
            for p in range(4):
                tx = p * 8 + 2
                pygame.draw.line(bamboo_surf, (90, 60, 25), (tx, ry), (tx + 4, ry + 3), 1)
                pygame.draw.line(bamboo_surf, (90, 60, 25), (tx, ry + 3), (tx + 4, ry), 1)

        assets["street_wall_fence"] = bamboo_surf

        # =========================================================================
        # 3. AUTHENTIC FILIPINO ARCHITECTURE WALLS (NO FENCE IN TERRAIN)
        # =========================================================================
        # Style 0: Bahay na Bato - Capiz Shell Sliding Windows & Narra Wood
        capiz_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        capiz_surf.fill((120, 72, 40))
        pygame.draw.rect(capiz_surf, (85, 48, 24), (0, 0, 32, 4))
        pygame.draw.line(capiz_surf, (155, 100, 58), (0, 0), (31, 0), 1)
        pygame.draw.rect(capiz_surf, (60, 35, 18), (2, 5, 28, 22))
        for row in range(2):
            for col in range(4):
                wx = 3 + col * 7
                wy = 6 + row * 10
                pygame.draw.rect(capiz_surf, (245, 245, 238), (wx, wy, 6, 9))
                pygame.draw.rect(capiz_surf, (215, 225, 230), (wx + 1, wy + 1, 4, 7))
                pygame.draw.rect(capiz_surf, (100, 60, 32), (wx, wy, 6, 9), 1)
        pygame.draw.rect(capiz_surf, (95, 55, 30), (0, 28, 32, 4))
        for v in range(8):
            pygame.draw.line(capiz_surf, (55, 30, 15), (v * 4 + 1, 28), (v * 4 + 1, 31), 1)
        assets["street_wall_0"] = capiz_surf

        # Style 1: Vigan Piedra & Spanish Red Adobe Brick
        vigan_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        vigan_surf.fill((185, 88, 62))
        pygame.draw.rect(vigan_surf, (215, 95, 55), (0, 0, 32, 5))
        pygame.draw.line(vigan_surf, (245, 140, 95), (0, 0), (31, 0), 1)
        pygame.draw.line(vigan_surf, (135, 55, 32), (0, 4), (31, 4), 1)
        mortar = (230, 220, 205)
        pygame.draw.line(vigan_surf, mortar, (0, 13), (31, 13), 1)
        pygame.draw.line(vigan_surf, mortar, (0, 22), (31, 22), 1)
        pygame.draw.line(vigan_surf, mortar, (0, 31), (31, 31), 1)
        pygame.draw.line(vigan_surf, mortar, (16, 5), (16, 13), 1)
        pygame.draw.line(vigan_surf, mortar, (8, 13), (8, 22), 1)
        pygame.draw.line(vigan_surf, mortar, (24, 13), (24, 22), 1)
        pygame.draw.line(vigan_surf, mortar, (16, 22), (16, 31), 1)
        pygame.draw.line(vigan_surf, (210, 110, 80), (1, 6), (15, 6), 1)
        pygame.draw.line(vigan_surf, (210, 110, 80), (17, 6), (30, 6), 1)
        assets["street_wall_1"] = vigan_surf

        # Style 2: Sawali Woven Bamboo Lattice (Dinding na Sawali)
        sawali_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        sawali_surf.fill((218, 185, 120))
        pygame.draw.rect(sawali_surf, (140, 85, 45), (0, 0, 32, 32), 2)
        pygame.draw.rect(sawali_surf, (170, 110, 60), (1, 1, 30, 30), 1)
        weave_dark = (175, 140, 85)
        weave_light = (245, 218, 155)
        for offset in range(-32, 64, 8):
            pygame.draw.line(sawali_surf, weave_dark, (offset, 0), (offset + 32, 32), 1)
            pygame.draw.line(sawali_surf, weave_light, (offset + 2, 0), (offset + 34, 32), 1)
            pygame.draw.line(sawali_surf, weave_dark, (offset, 32), (offset + 32, 0), 1)
        assets["street_wall_2"] = sawali_surf

        # Style 3: Bahay na Bato Lower Stone (Piedra China Adobe with Moss)
        piedra_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        piedra_surf.fill((165, 160, 148))
        pygame.draw.rect(piedra_surf, (200, 195, 182), (0, 0, 32, 5))
        pygame.draw.line(piedra_surf, (235, 230, 218), (0, 0), (31, 0), 1)
        pygame.draw.line(piedra_surf, (115, 110, 100), (0, 4), (31, 4), 1)
        p_dark = (115, 110, 100)
        pygame.draw.line(piedra_surf, p_dark, (0, 14), (31, 14), 1)
        pygame.draw.line(piedra_surf, p_dark, (0, 23), (31, 23), 1)
        pygame.draw.line(piedra_surf, p_dark, (16, 5), (16, 14), 1)
        pygame.draw.line(piedra_surf, p_dark, (8, 14), (8, 23), 1)
        pygame.draw.line(piedra_surf, p_dark, (24, 14), (24, 23), 1)
        pygame.draw.line(piedra_surf, p_dark, (16, 23), (16, 31), 1)
        pygame.draw.circle(piedra_surf, (55, 145, 65), (6, 12), 3)
        pygame.draw.circle(piedra_surf, (40, 115, 50), (8, 14), 2)
        pygame.draw.circle(piedra_surf, (55, 145, 65), (25, 21), 3)
        pygame.draw.circle(piedra_surf, (40, 115, 50), (27, 23), 2)
        assets["street_wall_3"] = piedra_surf

        # =========================================================================
        # 4. AUTHENTIC FILIPINO STREET PROPS IN THE MIDDLE
        # =========================================================================
        # A: Softdrink Glass Bottle Crates (Coca-Cola / Royal Style)
        bottle_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(bottle_surf, (210, 40, 35), (4, 15, 24, 15), border_radius=2)
        pygame.draw.rect(bottle_surf, (160, 25, 20), (4, 15, 24, 15), 1, border_radius=2)
        for bx in [7, 13, 19, 25]:
            pygame.draw.rect(bottle_surf, (140, 205, 160), (bx, 9, 3, 7))
            pygame.draw.circle(bottle_surf, (255, 215, 40), (bx + 1, 9), 2)
        pygame.draw.rect(bottle_surf, (80, 15, 10), (12, 21, 8, 4), border_radius=1)
        assets["prop_bottle_crate"] = bottle_surf

        # B: Filipino Ihawan / Street BBQ Charcoal Grill
        ihawan_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(ihawan_surf, (50, 52, 60), (4, 14, 24, 10), border_radius=2)
        pygame.draw.line(ihawan_surf, (40, 42, 50), (6, 24), (4, 31), 2)
        pygame.draw.line(ihawan_surf, (40, 42, 50), (26, 24), (28, 31), 2)
        pygame.draw.rect(ihawan_surf, (235, 75, 30), (6, 13, 20, 3))
        pygame.draw.circle(ihawan_surf, (255, 195, 45), (10, 14), 2)
        pygame.draw.circle(ihawan_surf, (255, 195, 45), (18, 14), 2)
        pygame.draw.circle(ihawan_surf, (255, 240, 100), (14, 14), 1)
        for sx in [8, 14, 20]:
            pygame.draw.line(ihawan_surf, (190, 140, 70), (sx - 2, 9), (sx + 4, 15), 1)
            pygame.draw.rect(ihawan_surf, (140, 55, 25), (sx - 1, 10, 4, 4), border_radius=1)
        assets["prop_ihawan"] = ihawan_surf

        # C: Palayok with Calachuchi Blooms
        palayok_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(palayok_surf, (195, 95, 55), (16, 24), 8)
        pygame.draw.ellipse(palayok_surf, (220, 115, 70), (9, 16, 14, 4))
        pygame.draw.ellipse(palayok_surf, (150, 70, 35), (11, 17, 10, 2))
        pygame.draw.ellipse(palayok_surf, (45, 165, 75), (6, 8, 10, 12))
        pygame.draw.ellipse(palayok_surf, (60, 185, 90), (16, 8, 10, 12))
        pygame.draw.ellipse(palayok_surf, (35, 140, 60), (11, 4, 10, 14))
        for fx, fy in [(12, 9), (20, 11), (16, 6)]:
            pygame.draw.circle(palayok_surf, (255, 255, 255), (fx, fy), 3)
            pygame.draw.circle(palayok_surf, (255, 215, 50), (fx, fy), 1)
        assets["prop_planter_urn"] = palayok_surf

        # D: Barrio Wooden Streetlamp Post with Mini Parol
        post_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(post_surf, (95, 60, 30), (14, 2, 4, 28), border_radius=1)
        pygame.draw.line(post_surf, (135, 90, 50), (15, 2), (15, 30), 1)
        pygame.draw.rect(post_surf, (75, 45, 20), (8, 6, 16, 3))
        pygame.draw.circle(post_surf, (255, 235, 150, 80), (10, 13), 6)
        pygame.draw.rect(post_surf, (255, 210, 70), (8, 10, 4, 6), border_radius=1)
        pts = [(22, 9), (24, 12), (27, 12), (24, 14), (25, 17), (22, 15), (19, 17), (20, 14), (17, 12), (20, 12)]
        pygame.draw.polygon(post_surf, (245, 60, 50), pts)
        pygame.draw.circle(post_surf, (255, 220, 60), (22, 13), 2)
        assets["prop_streetlamp"] = post_surf

        # E: Bamboo Papag Bench with Native Salakot Hat
        bench_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        for bx in range(4, 28, 4):
            pygame.draw.rect(bench_surf, (215, 185, 100), (bx, 15, 3, 10), border_radius=1)
        pygame.draw.rect(bench_surf, (170, 140, 70), (2, 14, 28, 4), border_radius=1)
        pygame.draw.rect(bench_surf, (150, 120, 55), (4, 18, 3, 13))
        pygame.draw.rect(bench_surf, (150, 120, 55), (25, 18, 3, 13))
        pygame.draw.polygon(bench_surf, (230, 200, 120), [(16, 9), (11, 14), (21, 14)])
        pygame.draw.circle(bench_surf, (180, 140, 70), (16, 9), 1)
        assets["prop_park_bench"] = bench_surf

        # F: Carabao Mango & Calamansi Fruit Stand
        fruit_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(fruit_surf, (180, 130, 75), (5, 14, 22, 16), border_radius=1)
        pygame.draw.rect(fruit_surf, (140, 95, 45), (5, 14, 22, 16), 1, border_radius=1)
        pygame.draw.line(fruit_surf, (140, 95, 45), (5, 22), (26, 22), 1)
        pygame.draw.circle(fruit_surf, (255, 205, 40), (10, 13), 3)
        pygame.draw.circle(fruit_surf, (255, 190, 30), (15, 12), 3)
        pygame.draw.circle(fruit_surf, (255, 210, 50), (21, 13), 3)
        pygame.draw.circle(fruit_surf, (80, 190, 60), (12, 10), 2)
        pygame.draw.circle(fruit_surf, (80, 190, 60), (18, 10), 2)
        assets["prop_fruit_crate"] = fruit_surf

        # G: Pinoy Sorbetes Cart (Dirty Ice Cream Cart)
        cart_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(cart_surf, (245, 195, 35), [(2, 8), (30, 8), (26, 2), (6, 2)])
        pygame.draw.line(cart_surf, (215, 60, 45), (10, 2), (8, 8), 2)
        pygame.draw.line(cart_surf, (215, 60, 45), (22, 2), (24, 8), 2)
        pygame.draw.rect(cart_surf, (215, 60, 45), (4, 9, 24, 14), border_radius=2)
        pygame.draw.rect(cart_surf, (245, 195, 35), (8, 12, 16, 8), border_radius=1)
        pygame.draw.circle(cart_surf, (60, 65, 75), (8, 25), 5)
        pygame.draw.circle(cart_surf, (245, 195, 35), (8, 25), 3)
        pygame.draw.circle(cart_surf, (60, 65, 75), (24, 25), 5)
        pygame.draw.circle(cart_surf, (245, 195, 35), (24, 25), 3)
        assets["prop_sorbetes_cart"] = cart_surf

        # H: Sari-Sari Store Awning
        awning_surf = pygame.Surface((TILE_SIZE, 14), pygame.SRCALPHA)
        for s in range(4):
            scol = (225, 45, 45) if s % 2 == 0 else (245, 245, 250)
            pygame.draw.rect(awning_surf, scol, (s * 8, 0, 8, 14))
        assets["prop_sari_awning"] = awning_surf

        # I: Filipino Glowing Star Parol
        parol_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pts = [(16, 2), (20, 11), (30, 11), (22, 18), (25, 28), (16, 22), (7, 28), (10, 18), (2, 11), (12, 11)]
        pygame.draw.polygon(parol_surf, (255, 205, 40), pts)
        pygame.draw.polygon(parol_surf, (235, 60, 50), pts, 2)
        pygame.draw.circle(parol_surf, (255, 245, 160), (16, 15), 5)
        pygame.draw.line(parol_surf, (50, 180, 80), (10, 26), (6, 31), 2)
        pygame.draw.line(parol_surf, (235, 60, 50), (22, 26), (26, 31), 2)
        assets["prop_parol"] = parol_surf

        # J: Jeepney Stop Sign
        sign_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(sign_surf, (80, 85, 95), (14, 10, 4, 22))
        pygame.draw.circle(sign_surf, (30, 90, 175), (16, 10), 9)
        pygame.draw.circle(sign_surf, (245, 245, 250), (16, 10), 7)
        pygame.draw.rect(sign_surf, (220, 40, 40), (11, 8, 10, 4), border_radius=1)
        assets["prop_jeep_sign"] = sign_surf

        return assets

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

        print(f"[OK] Loaded {len(frames)} frames for {npc_name}")
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
                print(f"[OK] Loaded Oldman sprite")
            else:
                print(f"[WARN] Oldman sprite not found at: {oldman_path}")
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
            print(f"[FAIL] Error loading Oldman: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((200, 200, 200))
            self.npc_oldman_sprite = placeholder

        # Load Skeleton
        skeleton_path = os.path.join(self.NPC_PATH_SKELETON, "skeleton.png")
        try:
            if os.path.exists(skeleton_path):
                img = pygame.image.load(skeleton_path).convert_alpha()
                self.npc_skeleton_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"[OK] Loaded Skeleton sprite")
            else:
                print(f"[WARN] Skeleton sprite not found at: {skeleton_path}")
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
            print(f"[FAIL] Error loading Skeleton: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((255, 255, 255))
            self.npc_skeleton_sprite = placeholder

        # Load Knight
        knight_path = os.path.join(self.NPC_PATH_KNIGHT, "knight.png")
        try:
            if os.path.exists(knight_path):
                img = pygame.image.load(knight_path).convert_alpha()
                self.npc_knight_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"[OK] Loaded Knight sprite")
            else:
                print(f"[WARN] Knight sprite not found at: {knight_path}")
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
                    print(f"[OK] Loaded Knight left frame: {name}")

            # Load Knight walking down sprites
            self.npc_knight_down_sprites = []
            for name in ["knight_down.png", "knight_down_1.png", "knight_down_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_down_sprites.append(scaled)
                    print(f"[OK] Loaded Knight down frame: {name}")

            # Load Knight walking right sprites
            self.npc_knight_right_sprites = []
            for name in ["knight_right.png", "knight_right_1.png", "knight_right_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_right_sprites.append(scaled)
                    print(f"[OK] Loaded Knight right frame: {name}")

            # Load Knight walking up sprites
            self.npc_knight_up_sprites = []
            for name in ["knight_up.png", "knight_up_1.png", "knight_up_2.png"]:
                path = os.path.join(self.NPC_PATH_KNIGHT, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_knight_up_sprites.append(scaled)
                    print(f"[OK] Loaded Knight up frame: {name}")
        except Exception as e:
            print(f"[FAIL] Error loading Knight: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((192, 192, 192))
        # Load 5 Quarter 2 Filipino Street Character NPCs (Tomas, Sorbetero, Drayber, Maya, Lola Rosa)
        for num in range(1, 6):
            folder_name = f"Filipino{num}NPC"
            filipino_path = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", folder_name)
            frames = []
            try:
                for i in range(8):
                    f_name = f"sprite_filipino{num}npc{i:02d}.png"
                    f_path = os.path.join(filipino_path, f_name)
                    if os.path.exists(f_path):
                        img = pygame.image.load(f_path).convert_alpha()
                        frames.append(pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)))
                if frames and num in self.station_npc_info:
                    self.station_npc_info[num]["frames"] = frames
                    print(f"[OK] Loaded {len(frames)} frames for Filipino NPC {num}: {self.station_npc_info[num]['name']}")
            except Exception as e:
                print(f"[FAIL] Error loading Filipino NPC {num}: {e}")

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
            self.animation = Quarter2.PortalSpriteAnimation(
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

        def draw(self, screen, camera_x, camera_y, zoom, screen_width, screen_height, is_unlocked=True, frame_counter=0):
            screen_x = (self.get_world_x() - camera_x) * zoom
            screen_y = (self.get_world_y() - camera_y) * zoom
            scaled_width = int(self.get_width_pixels() * zoom)
            scaled_height = int(self.get_height_pixels() * zoom)

            if (-scaled_width <= screen_x <= screen_width + scaled_width and
                    -scaled_height <= screen_y <= screen_height + scaled_height):
                if is_unlocked:
                    center_px = (int(screen_x + scaled_width / 2), int(screen_y + scaled_height / 2))
                    pulse = (math.sin(frame_counter * 0.15) + 1) * 0.5
                    rad = int((scaled_width / 2) + pulse * 6 * zoom)
                    aura_surf = pygame.Surface((rad * 2 + 10, rad * 2 + 10), pygame.SRCALPHA)
                    pygame.draw.circle(aura_surf, (255, 215, 0, int(80 + 70 * pulse)), (rad + 5, rad + 5), rad)
                    pygame.draw.circle(aura_surf, (74, 222, 128, int(100 + 80 * (1 - pulse))), (rad + 5, rad + 5), int(rad * 0.75))
                    screen.blit(aura_surf, (center_px[0] - rad - 5, center_px[1] - rad - 5))

                    if self.animation:
                        self.animation.draw(screen, camera_x, camera_y, zoom, screen_width, screen_height)
                    else:
                        pygame.draw.rect(screen, (74, 222, 128), (screen_x, screen_y, scaled_width, scaled_height), border_radius=6)

                    # Overhead radiant banner
                    bob = math.sin(frame_counter * 0.12) * 3 * zoom
                    banner_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial"], int(10 * zoom), bold=True)
                    banner_surf = banner_font.render(">> EXIT PORTAL", True, (255, 235, 120))
                    bw = banner_surf.get_width() + 12
                    bh = banner_surf.get_height() + 4
                    bx = center_px[0] - bw / 2
                    by = screen_y - bh - 6 * zoom + bob

                    b_bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
                    b_bg.fill((15, 23, 42, 220))
                    screen.blit(b_bg, (bx, by))
                    pygame.draw.rect(screen, (255, 215, 0), (bx, by, bw, bh), 1, border_radius=4)
                    screen.blit(banner_surf, (bx + 6, by + 2))
                else:
                    # Stylized Dormant/Locked Gate Arch
                    gate_surf = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
                    gate_surf.fill((35, 40, 50, 190))
                    pygame.draw.rect(gate_surf, (150, 130, 100), (0, 0, scaled_width, scaled_height), 2, border_radius=4)
                    screen.blit(gate_surf, (screen_x, screen_y))

                    # Small lock indicator
                    lock_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial"], int(9 * zoom), bold=True)
                    lock_surf = lock_font.render("LOCKED", True, (248, 113, 113))
                    lx = screen_x + scaled_width / 2 - lock_surf.get_width() / 2
                    ly = screen_y + scaled_height / 2 - lock_surf.get_height() / 2
                    screen.blit(lock_surf, (lx, ly))

        def contains_position(self, world_x, world_y):
            # Check player center with generous margin for seamless collision
            px = world_x + TILE_SIZE // 2
            py = world_y + TILE_SIZE // 2
            portal_left = self.get_world_x()
            portal_right = portal_left + self.get_width_pixels()
            portal_top = self.get_world_y()
            portal_bottom = portal_top + self.get_height_pixels()
            return (portal_left - 12 <= px <= portal_right + 12 and
                    portal_top - 12 <= py <= portal_bottom + 12)

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
            game_row_list = list(self.game_map[y]) if y < len(self.game_map) else None
            modified = False
            for x, c in enumerate(row):
                if c == 'r':
                    portal = self.Portal(x, y, 'right', is_static=True)
                    portal.set_animation(self.portal_frames_cache['right'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    if game_row_list:
                        game_row_list[x] = 'G'
                    modified = True
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    if game_row_list:
                        game_row_list[x] = 'G'
                    modified = True
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    if game_row_list:
                        game_row_list[x] = 'G'
                    modified = True
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    self.portals.append(portal)
                    row_list[x] = 'G'
                    if game_row_list:
                        game_row_list[x] = 'G'
                    modified = True
            if modified:
                self.render_map[y] = ''.join(row_list)
                if game_row_list and y < len(self.game_map):
                    self.game_map[y] = ''.join(game_row_list)

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
                        # Walkable tiles are walkable. We ignore other temporary collision overlays
                        if tile in self.WALKABLE_TILES and nxt not in seen:
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

            npc_positions = []
            for marker, positions in self.npc_positions_data.items():
                npc_positions.extend(positions)

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
    def return_to_stage_select(self, completed=True):
        """Return to the stage select screen"""
        if self.main_menu:
            # Save results to database on completion
            if completed:
                self.save_results_to_database()
                try:
                    total_questions = min(5, len(self.quiz_questions)) if hasattr(self, 'quiz_questions') and self.quiz_questions else 5
                    correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
                    percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 100.0
                    score = int(correct_answers * 20)
                    from db.save_system import mark_quarter_completed
                    mark_quarter_completed(self.main_menu, "quarter2", score=score, percentage=percentage, total_questions=total_questions)
                    if hasattr(self.main_menu, 'audio_manager'):
                        self.main_menu.audio_manager.play_sfx("victory_fanfare")
                        self.main_menu.audio_manager.play_sfx("portal_warp")
                except Exception as e:
                    print(f"[WARN] Error recording Quarter 2 completion: {e}")

            self.main_menu.current_screen = "stage_select"
            self.main_menu.quarter2 = None
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

    def check_portal_teleport_on_hold(self):
        if self.warp_out_active:
            return False
        if self.quiz_state != 0 and self.quiz_state != 6:
            return False
        current_portal = None
        for portal in self.portals:
            if portal.contains_position(self.player_x, self.player_y):
                current_portal = portal
                break

        if current_portal and self.teleport_cooldown <= 0:
            # When all 5 challenges are cleared, stepping into the goal portal initiates seamless warp!
            if self.quiz_state == 6:
                if current_portal.direction == self.goal_portal_direction or current_portal.is_static:
                    print("* Entering Grand Fiesta Portal - Initiating seamless warp transition...")
                    self.warp_out_active = True
                    self.warp_out_timer = self.warp_out_duration
                    return True

            # If portal is locked, notify player
            if self.quiz_state < 6:
                return False

            # Regular portal teleport (to another portal on same map) if held
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
        if hasattr(self, 'camera_pan_active') and self.camera_pan_active and self.map_name == "map5.txt":
            now = pygame.time.get_ticks()
            elapsed = (now - self.camera_pan_start_time) / 1000.0
            
            # 3-phase pan:
            # Phase 1: 0.0 - 0.8s -> Smooth glide to Bahay Kubo Plaza
            # Phase 2: 0.8 - 2.0s -> Focus on Bahay Kubo as piece snaps in with fanfare/particles
            # Phase 3: 2.0 - 2.8s -> Smooth glide back to player
            kubo_target_x = (self.kubo_tile_x * TILE_SIZE + 48) - (self.width // 2) / ZOOM
            kubo_target_y = (self.kubo_tile_y * TILE_SIZE + 48) - (self.height // 2) / ZOOM
            
            player_target_x = self.player_x + TILE_SIZE // 2 - (self.width // 2) / ZOOM
            player_target_y = self.player_y + TILE_SIZE // 2 - (self.height // 2) / ZOOM
            
            if elapsed < 0.8:
                t = elapsed / 0.8
                ease_t = 0.5 - 0.5 * math.cos(t * math.pi)
                self.camera_x = self.pan_start_cam_x + (kubo_target_x - self.pan_start_cam_x) * ease_t
                self.camera_y = self.pan_start_cam_y + (kubo_target_y - self.pan_start_cam_y) * ease_t
            elif elapsed < 2.0:
                self.camera_x = kubo_target_x
                self.camera_y = kubo_target_y
                if not self.kubo_piece_placed_in_pan:
                    self.kubo_piece_placed_in_pan = True
                    self.spawn_kubo_construction_particles()
                    if self.wood_snap_sound:
                        self.wood_snap_sound.play()
                    elif self.snap_sound:
                        self.snap_sound.play()
            elif elapsed < 2.8:
                t = (elapsed - 2.0) / 0.8
                ease_t = 0.5 - 0.5 * math.cos(t * math.pi)
                self.camera_x = kubo_target_x + (player_target_x - kubo_target_x) * ease_t
                self.camera_y = kubo_target_y + (player_target_y - kubo_target_y) * ease_t
            else:
                self.camera_pan_active = False
                self.award_anim_active = False
        else:
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
    # TRIGGER CLICK (2x2 Elemental Cards with 50:50 Wizard Hint)
    # ============================================================
    def trigger_click(self, pos):
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
                from screens.quarter2 import Quarter2
                self.main_menu.quarter2 = Quarter2(self.screen, self.main_menu, "map2.txt")
                return
            elif exit_rect.collidepoint(pos):
                self.time_up_dialog_active = False
                from screens.stageselect import StageSelect
                self.main_menu.current_screen = "stage_select"
                self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
                self.main_menu.quarter2 = None
                return
            return

        import random
        from db.save_system import save_student_progress
        
        # State 1: Choice Button Selection (No icons)
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
                        
                        # Trigger station-specific authentic sounds
                        if self.quiz_station_index == 1 and self.cash_register:
                            self.cash_register.play()
                        elif self.quiz_station_index == 2 and self.sorbetes_bell:
                            self.sorbetes_bell.play()
                        elif self.quiz_station_index == 3 and self.jeepney_horn:
                            self.jeepney_horn.play()
                        elif self.quiz_station_index == 4 and self.coin_clink:
                            self.coin_clink.play()
                        elif self.quiz_station_index == 5 and self.success_sound:
                            self.success_sound.play()
                        elif self.coin_clink:
                            self.coin_clink.play()
                        
                        print(f"[OK] Correct answer selected: {q_data['choices'][i]}")
                    else:
                        # 50:50 Wizard Hint: eliminate clicked choice with gentle encouragement
                        self.eliminated_choices.add(i)
                        info = self.station_npc_info.get(self.quiz_station_index, {})
                        speaker = info.get("name", "Guardian")
                        self.wrong_feedback_msg = f"{speaker}: Almost there! Try picking again!"
                        if hasattr(self, 'first_attempt_correct') and (self.current_question_index + 1) in self.first_attempt_correct:
                            self.first_attempt_correct[self.current_question_index + 1] = False
                        
                        self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
                        if self.station_attempts[self.quiz_station_index] < 2:
                            # 1st wrong attempt: Give player 1 more try
                            self.quiz_state = 2
                            print(f"[FAIL] Incorrect choice selected: {q_data['choices'][i]} (Attempt 1 of 2)")
                        else:
                            # 2nd wrong attempt: Out of tries! Recorded as wrong, but award progression item
                            self.quiz_state = 4
                            print(f"[FAIL] Incorrect choice on 2nd try! Out of tries. Station {self.quiz_station_index} cleared for progression.")
                        
                        if self.snap_sound:
                            self.snap_sound.play()
                    
                    save_student_progress(self.main_menu)
                    break
                    
        # State 2: Wrong answer retry screen click (1 try remaining)
        elif self.quiz_state == 2:
            box_w, box_h = 520, 250
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 160, 220, 44)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                save_student_progress(self.main_menu)
            
        # State 3: Correct answer transition screen click -> Award Speed Rush & In-World Banner!
        elif self.quiz_state == 3:
            box_w, box_h = 520, 250
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 160, 220, 44)
            if btn_rect.collidepoint(pos):
                # Award 2-second Festive Sprint Speed Boost (SPEED = 4)!
                self.speed_boost_timer = 2.0
                cleared_info = self.station_npc_info.get(self.quiz_station_index, {})
                cleared_name = cleared_info.get("name", f"Station {self.quiz_station_index}")
                self.banner_text = f"STALL CLEARED: {cleared_name.upper()}!"
                self.banner_sub = "Festive Sprint active! Proceed to the next barrio stall!"
                self.banner_timer = 2.0

                current_st = self.quiz_station_index
                if self.map_name == "map5.txt":
                    self.kubo_pieces_collected = current_st
                    self.trigger_kubo_pan_sequence(current_st)

                if self.quiz_station_index < 5:
                    self.quiz_station_index += 1
                    self.current_question_index = self.quiz_station_index - 1
                    self.quiz_state = 0  # Immediate return to exploration!
                    print(f"[TARGET] Proceeding to Station {self.quiz_station_index}")
                else:
                    self.current_question_index = 5
                    self.quiz_state = 5
                
                save_student_progress(self.main_menu)

        # State 4: Out of tries reveal screen click -> Guaranteed progression!
        elif self.quiz_state == 4:
            box_w, box_h = 580, 270
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 190, 240, 44)
            if btn_rect.collidepoint(pos):
                self.eliminated_choices.clear()
                self.wrong_feedback_msg = ""
                self.speed_boost_timer = 2.0
                cleared_info = self.station_npc_info.get(self.quiz_station_index, {})
                cleared_name = cleared_info.get("name", f"Station {self.quiz_station_index}")
                self.banner_text = f"STALL CLEARED: {cleared_name.upper()}!"
                self.banner_sub = "Festive Sprint active! Proceed to the next barrio stall!"
                self.banner_timer = 2.0

                current_st = self.quiz_station_index
                if self.map_name == "map5.txt":
                    self.kubo_pieces_collected = current_st
                    self.trigger_kubo_pan_sequence(current_st)

                if self.quiz_station_index < 5:
                    self.quiz_station_index += 1
                    self.current_question_index = self.quiz_station_index - 1
                    self.quiz_state = 0
                    print(f"[TARGET] Proceeding to Station {self.quiz_station_index}")
                else:
                    self.current_question_index = 5
                    self.quiz_state = 5

                save_student_progress(self.main_menu)
                
        # State 5: Final speech click -> Unlock Grand Fiesta Portal & Warp Transition!
        elif self.quiz_state == 5:
            box_w, box_h = 620, 340
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 245, 220, 44)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 6
                self.save_results_to_database()
                save_student_progress(self.main_menu)
                self.banner_text = "GRAND FIESTA PORTAL UNLOCKED!"
                self.banner_sub = "Head to the Exit Portal at the end of the street to complete Quarter 2!"
                self.banner_timer = 999.0
                if self.success_sound:
                    self.success_sound.play()
                print("* Grand Fiesta Exit Portal unlocked!")

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1

        if self.pause_menu.is_paused:
            return

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
                print("[TIME] Quarter 2 Time's Up!")

        if self.time_up_dialog_active:
            return

        # Handle smooth warp-out transition to stage select
        if self.warp_out_active:
            self.warp_out_timer -= dt
            if self.warp_out_timer <= 0:
                self.warp_out_active = False
                self.return_to_stage_select()
            return

        # Update speed boost timer & banner timer
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= dt
        if self.banner_timer > 0:
            self.banner_timer -= dt

        # Update tile animation frame
        self.tile_anim_timer += 1
        if self.tile_anim_timer >= 12:
            self.tile_anim_timer = 0
            self.tile_anim_frame = (self.tile_anim_frame + 1) % 4

        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt

        # Update Bahay Kubo construction particles
        for cp in self.kubo_construction_particles[:]:
            cp["x"] += cp["vx"]
            cp["y"] += cp["vy"]
            cp["life"] -= dt
            if cp["life"] <= 0:
                self.kubo_construction_particles.remove(cp)

        # Update animations for all 5 Filipino character NPCs
        for num, info in self.station_npc_info.items():
            if info.get("frames"):
                info["anim_timer"] += 1
                if info["anim_timer"] >= 6:
                    info["anim_timer"] = 0
                    info["anim_frame"] = (info["anim_frame"] + 1) % len(info["frames"])

        # Proximity interaction check for current active station Guardian NPC (with Line-of-Sight wall check)
        if self.quiz_state == 0 and self.quiz_station_index in self.quiz_stations:
            st_x, st_y = self.quiz_stations[self.quiz_station_index]
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            p_tile_x = int(player_center_x // TILE_SIZE)
            p_tile_y = int(player_center_y // TILE_SIZE)
            npc_center_x = st_x * TILE_SIZE + TILE_SIZE // 2
            npc_center_y = st_y * TILE_SIZE + TILE_SIZE // 2
            dist = math.hypot(player_center_x - npc_center_x, player_center_y - npc_center_y)
            
            # Require close proximity (within 1.25 tiles) AND unobstructed line of sight (no wall in between)
            if dist < TILE_SIZE * 1.25 and self.has_line_of_sight(p_tile_x, p_tile_y, st_x, st_y):
                self.quiz_state = 1
                self.selected_choice_index = -1
                self.eliminated_choices.clear()
                self.wrong_feedback_msg = ""
                self.current_question_index = self.quiz_station_index - 1
                if self.coin_clink:
                    self.coin_clink.play()

        self.update_player_movement()
        self.check_portal_teleport_on_hold()

        for portal in self.portals:
            portal.update_animation()

        self.update_camera()

    # ============================================================
    # QUIZ DIALOGUE DRAWING METHODS (Glassmorphism & Live Visualizer)
    # ============================================================
    def draw_quiz_dialog(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 29, 175))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 580, 380
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Outer shadow
        shadow_rect = pygame.Rect(box_x + 6, box_y + 6, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 160), shadow_rect, border_radius=16)

        # Dialog main box (Dark Midnight Slate with Gold Trim)
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, (255, 215, 0), dialog_rect.inflate(-6, -6), 1, border_radius=12)

        # Speaker header ribbon
        header_surf = pygame.Surface((box_w - 36, 40), pygame.SRCALPHA)
        header_surf.fill((30, 41, 59, 230))
        self.screen.blit(header_surf, (box_x + 18, box_y + 12))
        pygame.draw.rect(self.screen, (218, 165, 32), (box_x + 18, box_y + 12, box_w - 36, 40), 1, border_radius=8)

        info = self.station_npc_info.get(self.quiz_station_index, {})
        d_title = info.get("title", f"Station {self.quiz_station_index}")
        speaker_surf = self.dialog_header_font.render(f"{d_title}", True, (255, 215, 0))
        self.screen.blit(speaker_surf, (box_x + 30, box_y + 18))

        # Station progress pill (Top Right)
        st_pill = pygame.Rect(box_x + box_w - 140, box_y + 16, 120, 30)
        pygame.draw.rect(self.screen, (15, 23, 42), st_pill, border_radius=6)
        pygame.draw.rect(self.screen, (245, 158, 11), st_pill, 1, border_radius=6)
        st_txt = self.dialog_stat_font.render(f"STATION {self.quiz_station_index}/5", True, (254, 240, 138))
        self.screen.blit(st_txt, st_txt.get_rect(center=st_pill.center))

        # Question Prompt
        q_data = self.quiz_questions[self.current_question_index]
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

        for i, choice in enumerate(q_data["choices"][:4]):
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

            c_surf = self.dialog_choice_font.render(choice, True, text_color)
            c_rect = c_surf.get_rect(center=btn_rect.center)
            self.screen.blit(c_surf, c_rect)

    def draw_wrong_dialog(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 29, 170))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 520, 250
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (0, 0, 0, 150), (box_x + 4, box_y + 4, box_w, box_h), border_radius=14)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=14)
        pygame.draw.rect(self.screen, (248, 113, 113), dialog_rect.inflate(-6, -6), 1, border_radius=10)

        info = self.station_npc_info.get(self.quiz_station_index, {})
        w_title = info.get("wrong_encouragement", "Barrio Stall - Try Again")
        speaker_surf = self.dialog_header_font.render(w_title, True, (248, 113, 113))
        self.screen.blit(speaker_surf, (box_x + 32, box_y + 18))

        msg_surf1 = self.dialog_q_font.render("That choice is not correct.", True, (255, 255, 255))
        msg_surf2 = self.dialog_hint_font.render("You have 1 try remaining! Think carefully and try again.", True, (254, 240, 138))
        self.screen.blit(msg_surf1, (box_x + 30, box_y + 68))
        self.screen.blit(msg_surf2, (box_x + 30, box_y + 98))

        button_w, button_h = 220, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 160
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (220, 38, 38) if is_hovered else (30, 41, 59)
        border_color = (255, 255, 255) if is_hovered else (220, 38, 38)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

        c_surf = self.dialog_header_font.render("Try Again", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_out_of_tries_dialog(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 29, 175))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 580, 270
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (0, 0, 0, 150), (box_x + 4, box_y + 4, box_w, box_h), border_radius=14)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (245, 158, 11), dialog_rect, 3, border_radius=14)
        pygame.draw.rect(self.screen, (251, 191, 36), dialog_rect.inflate(-6, -6), 1, border_radius=10)

        info = self.station_npc_info.get(self.quiz_station_index, {})
        speaker_name = info.get("name", f"Station {self.quiz_station_index}")
        speaker_surf = self.dialog_header_font.render(f"{speaker_name} - Out of Tries", True, (245, 158, 11))
        self.screen.blit(speaker_surf, (box_x + 30, box_y + 18))

        q_data = self.quiz_questions[self.current_question_index]
        correct_choice_text = q_data["choices"][q_data["correct"]]

        msg1 = self.dialog_q_font.render(f"Out of tries! The correct answer was: {correct_choice_text}", True, (255, 255, 255))
        reward_text = "You still received the Bahay Kubo piece so your quest can continue!" if self.map_name == "map5.txt" else "You completed this stall challenge so your quest can continue!"
        msg2 = self.dialog_hint_font.render(reward_text, True, (254, 240, 138))
        self.screen.blit(msg1, (box_x + 30, box_y + 68))
        self.screen.blit(msg2, (box_x + 30, box_y + 110))

        button_w, button_h = 240, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 190
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (245, 158, 11) if is_hovered else (30, 41, 59)
        border_color = (255, 255, 255) if is_hovered else (245, 158, 11)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

        c_surf = self.dialog_header_font.render("Continue Fiesta >>", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_correct_dialog(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 29, 170))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 540, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (0, 0, 0, 150), (box_x + 4, box_y + 4, box_w, box_h), border_radius=14)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (22, 163, 74), dialog_rect, 3, border_radius=14)
        pygame.draw.rect(self.screen, (74, 222, 128), dialog_rect.inflate(-6, -6), 1, border_radius=10)

        info = self.station_npc_info.get(self.quiz_station_index, {})
        c_title = info.get("correct_praise", "Well Done! (Correct Answer)")
        speaker_surf = self.dialog_header_font.render(c_title, True, (74, 222, 128))
        self.screen.blit(speaker_surf, (box_x + 32, box_y + 18))

        msg_surf = self.dialog_q_font.render(self.current_correct_phrase, True, (255, 255, 255))
        self.screen.blit(msg_surf, (box_x + 30, box_y + 75))

        t_math = info.get("target_math", "")
        if t_math:
            m_surf = self.dialog_hint_font.render(f"{t_math}", True, (253, 230, 138))
            self.screen.blit(m_surf, (box_x + 30, box_y + 110))

        button_w, button_h = 240, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 175
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (22, 163, 74) if is_hovered else (30, 41, 59)
        border_color = (255, 255, 255) if is_hovered else (22, 163, 74)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

        c_surf = self.dialog_header_font.render("Continue Fiesta >>", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_victory_speech(self):
        """Victory speech on clearing all 5 Barrio Challenges"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 29, 175))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 620, 340
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (0, 0, 0, 150), (box_x + 4, box_y + 4, box_w, box_h), border_radius=14)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=14)
        pygame.draw.rect(self.screen, (255, 215, 0), dialog_rect.inflate(-6, -6), 1, border_radius=10)

        speaker_surf = self.dialog_header_font.render("BARANGAY FIESTA - ALL TRIALS SOLVED!", True, (255, 215, 0))
        self.screen.blit(speaker_surf, (box_x + 30, box_y + 18))

        speech_lines = [
            "Congratulations, young adventurer! You have mastered Philippine Money,",
            "Sari-sari change, Jeepney fare multiplication, and Market scale weights!",
            "The Grand Fiesta Exit Portal is now fully open.",
            "Step into the portal at the end of the street to return to town!"
        ]

        y_text = box_y + 70
        for line in speech_lines:
            txt_surf = self.dialog_q_font.render(line, True, (248, 250, 252))
            self.screen.blit(txt_surf, (box_x + 30, y_text))
            y_text += 26

        button_w, button_h = 240, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 245
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (255, 215, 0) if is_hovered else (30, 41, 59)
        text_color = (15, 23, 42) if is_hovered else (255, 215, 0)
        border_color = (255, 255, 255) if is_hovered else (218, 165, 32)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=10)

        c_surf = self.dialog_header_font.render("Enter Portal >>", True, text_color)
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_final_dialog(self):
        self.draw_victory_speech()

    # ============================================================
    # [HOUSE] PROGRESSIVE BAHAY KUBO CONSTRUCTION (Map 5 Specific)
    # ============================================================
    def trigger_kubo_pan_sequence(self, piece_index):
        """Starts cinematic camera pan sequence to the Bahay Kubo plaza construction site in Map 5"""
        self.camera_pan_active = True
        self.camera_pan_start_time = pygame.time.get_ticks()
        self.pan_start_cam_x = self.camera_x
        self.pan_start_cam_y = self.camera_y
        self.kubo_piece_placed_in_pan = False
        
        self.award_anim_active = True
        self.award_anim_piece_idx = piece_index
        self.award_anim_start_time = pygame.time.get_ticks() + 900

    def spawn_kubo_construction_particles(self):
        """Spawns celebratory construction dust & golden sparkles at the Bahay Kubo site"""
        kx = self.kubo_tile_x * TILE_SIZE + 50
        ky = self.kubo_tile_y * TILE_SIZE + 40
        for _ in range(35):
            self.kubo_construction_particles.append({
                "x": kx + random.randint(-40, 40),
                "y": ky + random.randint(-30, 30),
                "vx": random.uniform(-2.5, 2.5),
                "vy": random.uniform(-4.0, -0.5),
                "color": random.choice([(255, 215, 0), (245, 158, 11), (254, 240, 138), (34, 197, 94), (255, 255, 255)]),
                "life": random.uniform(0.8, 1.4),
                "max_life": 1.4,
                "rad": random.randint(3, 6)
            })

    def draw_bahay_kubo(self):
        """Renders the Progressive Bahay Kubo on the Barrio Plaza for Map 5"""
        if self.map_name != "map5.txt":
            return

        world_x = self.kubo_tile_x * TILE_SIZE
        world_y = self.kubo_tile_y * TILE_SIZE
        sx = (world_x - self.camera_x) * ZOOM
        sy = (world_y - self.camera_y) * ZOOM
        
        # Don't draw if completely off-screen
        if sx < -200 or sx > self.width + 200 or sy < -200 or sy > self.height + 200:
            return

        # Base Plaza Cobblestone Patio
        patio_w, patio_h = int(120 * ZOOM), int(40 * ZOOM)
        patio_x = sx - int(10 * ZOOM)
        patio_y = sy + int(70 * ZOOM)
        pygame.draw.ellipse(self.screen, (71, 85, 105), (patio_x, patio_y, patio_w, patio_h))
        pygame.draw.ellipse(self.screen, (148, 163, 184), (patio_x, patio_y, patio_w, patio_h), 2)

        # Stage 0: Ground stakes and blueprint border
        if self.kubo_pieces_collected == 0:
            stake_pts = [
                (sx + 10 * ZOOM, sy + 75 * ZOOM),
                (sx + 90 * ZOOM, sy + 75 * ZOOM),
                (sx + 90 * ZOOM, sy + 95 * ZOOM),
                (sx + 10 * ZOOM, sy + 95 * ZOOM)
            ]
            pygame.draw.polygon(self.screen, (245, 158, 11), stake_pts, 2)
            sign_font = self.get_ui_font(10, bold=True)
            sign_txt = sign_font.render("BAHAY KUBO PLOT", True, (255, 215, 0))
            self.screen.blit(sign_txt, (sx + int(50 * ZOOM - sign_txt.get_width() // 2), sy + int(50 * ZOOM)))
            return

        # --- PIECE 1: BAMBOO STILTS & FLOOR PLATFORM (Piece >= 1) ---
        if self.kubo_pieces_collected >= 1:
            stilt_color = (180, 83, 9)
            stilt_hl = (217, 119, 6)
            stilt_w = max(2, int(4 * ZOOM))
            # 4 Sturdy bamboo legs
            leg_xs = [sx + 16 * ZOOM, sx + 38 * ZOOM, sx + 62 * ZOOM, sx + 84 * ZOOM]
            for lx in leg_xs:
                # Bamboo stilt with rings
                pygame.draw.line(self.screen, stilt_color, (lx, sy + 40 * ZOOM), (lx, sy + 88 * ZOOM), stilt_w)
                pygame.draw.line(self.screen, stilt_hl, (lx - 1, sy + 40 * ZOOM), (lx - 1, sy + 88 * ZOOM), 1)
                for ring_y in [sy + 52 * ZOOM, sy + 66 * ZOOM, sy + 78 * ZOOM]:
                    pygame.draw.line(self.screen, (251, 191, 36), (lx - 2, ring_y), (lx + 2, ring_y), 2)
            
            # Diagonal cross braces underneath
            pygame.draw.line(self.screen, (146, 64, 14), (leg_xs[0], sy + 80 * ZOOM), (leg_xs[1], sy + 45 * ZOOM), 2)
            pygame.draw.line(self.screen, (146, 64, 14), (leg_xs[2], sy + 80 * ZOOM), (leg_xs[3], sy + 45 * ZOOM), 2)

            # Slatted Bamboo Floor Platform
            fl_rect = pygame.Rect(sx + 10 * ZOOM, sy + 38 * ZOOM, 80 * ZOOM, 8 * ZOOM)
            pygame.draw.rect(self.screen, (217, 119, 6), fl_rect, border_radius=2)
            pygame.draw.rect(self.screen, (146, 64, 14), fl_rect, 1, border_radius=2)
            for sl in range(0, int(80 * ZOOM), int(6 * ZOOM)):
                pygame.draw.line(self.screen, (146, 64, 14), (fl_rect.x + sl, fl_rect.y), (fl_rect.x + sl, fl_rect.bottom), 1)

        # --- PIECE 2: WOVEN SAWALI WALLS (Piece >= 2) ---
        if self.kubo_pieces_collected >= 2:
            wall_rect = pygame.Rect(sx + 14 * ZOOM, sy + 6 * ZOOM, 72 * ZOOM, 34 * ZOOM)
            pygame.draw.rect(self.screen, (245, 158, 11), wall_rect)
            pygame.draw.rect(self.screen, (180, 83, 9), wall_rect, 2)
            
            # Sawali diagonal weave pattern
            for d in range(-int(34 * ZOOM), int(72 * ZOOM), int(8 * ZOOM)):
                pygame.draw.line(self.screen, (180, 83, 9), (wall_rect.x + d, wall_rect.y), (wall_rect.x + d + 34 * ZOOM, wall_rect.bottom), 1)
                pygame.draw.line(self.screen, (180, 83, 9), (wall_rect.x + d + 34 * ZOOM, wall_rect.y), (wall_rect.x + d, wall_rect.bottom), 1)

            # Doorway opening (Center-Right)
            door_rect = pygame.Rect(sx + 52 * ZOOM, sy + 14 * ZOOM, 18 * ZOOM, 26 * ZOOM)
            pygame.draw.rect(self.screen, (30, 41, 59), door_rect, border_radius=2)
            pygame.draw.rect(self.screen, (146, 64, 14), door_rect, 2, border_radius=2)

        # --- PIECE 3: CAPIZ SHELL WINDOWS (Piece >= 3) ---
        if self.kubo_pieces_collected >= 3:
            # Left Capiz Window (Propped open with bamboo stick)
            win_rect = pygame.Rect(sx + 20 * ZOOM, sy + 12 * ZOOM, 22 * ZOOM, 18 * ZOOM)
            pygame.draw.rect(self.screen, (15, 23, 42), win_rect)
            shutter_pts = [
                (win_rect.left - 4 * ZOOM, win_rect.top - 4 * ZOOM),
                (win_rect.right + 2 * ZOOM, win_rect.top - 6 * ZOOM),
                (win_rect.right + 2 * ZOOM, win_rect.bottom - 4 * ZOOM),
                (win_rect.left - 4 * ZOOM, win_rect.bottom - 2 * ZOOM)
            ]
            pygame.draw.polygon(self.screen, (254, 240, 138), shutter_pts)
            pygame.draw.polygon(self.screen, (180, 83, 9), shutter_pts, 1)
            pygame.draw.line(self.screen, (180, 83, 9),
                             ((shutter_pts[0][0] + shutter_pts[1][0]) / 2, (shutter_pts[0][1] + shutter_pts[1][1]) / 2),
                             ((shutter_pts[3][0] + shutter_pts[2][0]) / 2, (shutter_pts[3][1] + shutter_pts[2][1]) / 2), 1)
            pygame.draw.line(self.screen, (146, 64, 14), (win_rect.left + 4 * ZOOM, win_rect.bottom),
                             (shutter_pts[3][0] + 2 * ZOOM, shutter_pts[3][1]), 2)

        # --- PIECE 4: NIPA THATCH ROOF (Piece >= 4) ---
        if self.kubo_pieces_collected >= 4:
            roof_top = (sx + 50 * ZOOM, sy - 24 * ZOOM)
            roof_left = (sx + 4 * ZOOM, sy + 10 * ZOOM)
            roof_right = (sx + 96 * ZOOM, sy + 10 * ZOOM)
            roof_pts = [roof_top, roof_right, roof_left]
            
            pygame.draw.polygon(self.screen, (161, 98, 7), roof_pts)
            pygame.draw.polygon(self.screen, (113, 63, 18), roof_pts, 2)

            for layer in range(1, 5):
                ly = sy - 24 * ZOOM + layer * (34 * ZOOM / 5.0)
                spread = layer * (46 * ZOOM / 5.0)
                lx_start = sx + 50 * ZOOM - spread
                lx_end = sx + 50 * ZOOM + spread
                pygame.draw.line(self.screen, (202, 138, 4), (lx_start, ly), (lx_end, ly), 2)
                for fx in range(int(lx_start), int(lx_end), int(5 * ZOOM)):
                    pygame.draw.line(self.screen, (113, 63, 18), (fx, ly), (fx - 2, ly + 4 * ZOOM), 1)

            pygame.draw.line(self.screen, (251, 191, 36), (sx + 44 * ZOOM, sy - 24 * ZOOM), (sx + 56 * ZOOM, sy - 24 * ZOOM), 3)

        # --- PIECE 5: BAMBOO LADDER, BALCONY & FIESTA BANDERITAS (Piece == 5) ---
        if self.kubo_pieces_collected >= 5:
            lad_top_x = sx + 60 * ZOOM
            lad_top_y = sy + 38 * ZOOM
            lad_bot_x = sx + 68 * ZOOM
            lad_bot_y = sy + 88 * ZOOM
            pygame.draw.line(self.screen, (180, 83, 9), (lad_top_x - 3 * ZOOM, lad_top_y), (lad_bot_x - 3 * ZOOM, lad_bot_y), 3)
            pygame.draw.line(self.screen, (180, 83, 9), (lad_top_x + 9 * ZOOM, lad_top_y), (lad_bot_x + 9 * ZOOM, lad_bot_y), 3)
            for r_idx in range(5):
                rt = r_idx / 4.0
                rx1 = (lad_top_x - 3 * ZOOM) + (lad_bot_x - lad_top_x) * rt
                rx2 = (lad_top_x + 9 * ZOOM) + (lad_bot_x - lad_top_x) * rt
                ry = lad_top_y + (lad_bot_y - lad_top_y) * rt
                pygame.draw.line(self.screen, (251, 191, 36), (rx1, ry), (rx2, ry), 2)

            garland_colors = [(239, 68, 68), (59, 130, 246), (251, 191, 36), (34, 197, 94), (168, 85, 247)]
            for gi in range(8):
                gx1 = sx + 8 * ZOOM + gi * (10 * ZOOM)
                gy1 = sy + 8 * ZOOM
                g_tip = (gx1 + 5 * ZOOM, gy1 + 6 * ZOOM)
                g_col = garland_colors[gi % len(garland_colors)]
                pygame.draw.polygon(self.screen, g_col, [(gx1, gy1), (gx1 + 10 * ZOOM, gy1), g_tip])

            p_x = sx + 42 * ZOOM
            p_y = sy + 32 * ZOOM
            pygame.draw.circle(self.screen, (255, 215, 0), (int(p_x), int(p_y)), int(4 * ZOOM))
            pygame.draw.circle(self.screen, (255, 255, 255), (int(p_x), int(p_y)), int(2 * ZOOM))

        # Floating Landmark Name Badge
        b_name_font = self.get_ui_font(11, bold=True)
        b_label = f"BARANGAY BAHAY KUBO ({self.kubo_pieces_collected}/5)"
        b_surf = b_name_font.render(b_label, True, (255, 215, 0) if self.kubo_pieces_collected == 5 else (254, 240, 138))
        badge_w, badge_h = b_surf.get_width() + 14, 24
        badge_rect = pygame.Rect(sx + int(50 * ZOOM - badge_w // 2), sy - int(34 * ZOOM), badge_w, badge_h)
        
        bg_card = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        bg_card.fill((15, 23, 42, 220))
        self.screen.blit(bg_card, (badge_rect.x, badge_rect.y))
        pygame.draw.rect(self.screen, (218, 165, 32) if self.kubo_pieces_collected < 5 else (34, 197, 94), badge_rect, 1, border_radius=6)
        self.screen.blit(b_surf, (badge_rect.x + 7, badge_rect.y + 3))

        # Draw construction particles in world space
        for cp in self.kubo_construction_particles:
            cpx = (cp["x"] - self.camera_x) * ZOOM
            cpy = (cp["y"] - self.camera_y) * ZOOM
            if 0 <= cpx <= self.width and 0 <= cpy <= self.height:
                r = max(1, int(cp["rad"] * (cp["life"] / cp["max_life"])))
                pygame.draw.circle(self.screen, cp["color"], (int(cpx), int(cpy)), r)

    def draw_kubo_award_animation(self):
        """Draws floating cinematic award card when a new Bahay Kubo piece is assembled"""
        if not self.award_anim_active or self.map_name != "map5.txt":
            return

        now = pygame.time.get_ticks()
        if now < self.award_anim_start_time:
            return

        piece_idx = self.award_anim_piece_idx
        p_info = self.kubo_pieces_info.get(piece_idx, {})
        if not p_info:
            return

        card_w, card_h = 620, 110
        card_x = (self.width - card_w) // 2
        card_y = 65

        c_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        c_surf.fill((15, 23, 42, 235))
        self.screen.blit(c_surf, (card_x, card_y))

        pygame.draw.rect(self.screen, (34, 197, 94), (card_x, card_y, card_w, card_h), 2, border_radius=12)
        pygame.draw.rect(self.screen, (255, 215, 0), (card_x + 3, card_y + 3, card_w - 6, card_h - 6), 1, border_radius=10)

        h_txt = self.dialog_header_font.render(f"BAHAY KUBO PIECE {piece_idx}/5 ASSEMBLED!", True, (255, 215, 0))
        self.screen.blit(h_txt, h_txt.get_rect(center=(card_x + card_w // 2, card_y + 24)))

        t_txt = self.dialog_choice_font.render(p_info.get("title", ""), True, (74, 222, 128))
        self.screen.blit(t_txt, t_txt.get_rect(center=(card_x + card_w // 2, card_y + 54)))

        s_txt = self.dialog_hint_font.render(p_info.get("sub", ""), True, (254, 240, 138))
        self.screen.blit(s_txt, s_txt.get_rect(center=(card_x + card_w // 2, card_y + 82)))

    # ============================================================
    # WRAP TEXT HELPER
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
    # UPDATE PLAYER MOVEMENT (Sprint Boost & Particle Trails)
    # ============================================================
    def update_player_movement(self):
        if (hasattr(self, 'camera_pan_active') and self.camera_pan_active) or self.quiz_state in [1, 2, 3, 4, 5] or (hasattr(self, 'player_block_timer') and self.player_block_timer > 0):
            self.anim_frame = 0
            return

        current_speed = (SPEED * 1.4) if self.speed_boost_timer > 0 else SPEED
        vx, vy = 0, 0

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

        # Spawn festive sparkle particles during speed boost sprint
        if (vx != 0 or vy != 0) and self.speed_boost_timer > 0 and random.random() < 0.4:
            f_cols = [(255, 215, 0), (239, 68, 68), (34, 197, 94), (59, 130, 246), (245, 158, 11)]
            self.fiesta_sparkles.append({
                "x": self.player_x + TILE_SIZE // 2 + random.randint(-8, 8),
                "y": self.player_y + TILE_SIZE - random.randint(0, 8),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-1.0, -0.2),
                "color": random.choice(f_cols),
                "life": 0.5,
                "rad": random.randint(2, 4)
            })

        # Update sparkles
        for sp in self.fiesta_sparkles[:]:
            sp["x"] += sp["vx"]
            sp["y"] += sp["vy"]
            sp["life"] -= 0.016
            if sp["life"] <= 0:
                self.fiesta_sparkles.remove(sp)

        if vx != 0 or vy != 0:
            self.anim_timer += 1
            if self.anim_timer >= (5 if self.speed_boost_timer > 0 else 8):
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_frame = 0

    # ============================================================
    # DRAW TILE
    # ============================================================
    def draw_tile(self, c, world_x, world_y):
        tile_col = int(world_x // TILE_SIZE)
        tile_row = int(world_y // TILE_SIZE)

        # Base paver variation for terrain / underlay
        paver_var = (tile_col * 7 + tile_row * 13) % 4
        base_paver = self.tile_images.get(f"street_asphalt_{paver_var}", self.fallback_tile)

        is_border = (tile_col == 0 or tile_col == self.COLS - 1 or tile_row == 0 or tile_row == self.ROWS - 1)

        if is_border and c in {'Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y', '#'}:
            # Outer perimeter border uses the dedicated wooden spearhead fence
            image = self.tile_images.get("street_wall_fence", self.fallback_tile)
        elif c == 'G' or c in {'P', '1', '2', '3', '4', '5'}:
            image = base_paver
        elif c in {'Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y', '#'}:
            # Interior residential blocks: 4-5 tiles long per house style (NO FENCE in terrain!)
            var = ((tile_col // 5) * 3 + (tile_row // 4) * 2) % 4
            image = self.tile_images.get(f"street_wall_{var}", self.fallback_tile)
        elif c in {'a', 'b', 'c', 'g', 'h', 'i', 'F'}:
            # Street elements in the middle: draw cobblestone paver underneath
            prop_img = self.tile_images.get(c, self.fallback_tile)
            
            # Draw paver underlay first
            screen_x = (world_x - self.camera_x) * ZOOM
            screen_y = (world_y - self.camera_y) * ZOOM
            scaled_paver = pygame.transform.scale(base_paver, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
            self.screen.blit(scaled_paver, (screen_x, screen_y))
            
            image = prop_img
        elif c == 'f':
            image = self.tile_images.get(f"chest_green_{self.tile_anim_frame}", self.fallback_tile)
        elif c == 'k':
            image = self.tile_images.get(f"flag_hanging_red_{self.tile_anim_frame}", self.fallback_tile)
        else:
            image = self.tile_images.get(c, self.fallback_tile)

        w_img, h_img = image.get_size()
        
        # Calculate screen position based on camera and zoom
        screen_x = (world_x - self.camera_x) * ZOOM
        screen_y = (world_y - self.camera_y) * ZOOM
        
        # Center horizontally and align bottom of sprite with bottom of tile
        screen_x += (TILE_SIZE * ZOOM) / 2.0 - (w_img * ZOOM) / 2.0
        screen_y += (TILE_SIZE * ZOOM) - (h_img * ZOOM)
        
        scaled_w = int(w_img * ZOOM)
        scaled_h = int(h_img * ZOOM)
        
        margin = max(scaled_w, scaled_h) * 2
        if (-margin <= screen_x <= self.width + margin and
                -margin <= screen_y <= self.height + margin):
            scaled_image = pygame.transform.scale(image, (scaled_w, scaled_h))
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
        self.screen.fill((10, 14, 23))

        start_col = max(0, int(self.camera_x / TILE_SIZE) - 2)
        end_col = min(self.COLS, int((self.camera_x + self.width / ZOOM) / TILE_SIZE) + 3)
        start_row = max(0, int(self.camera_y / TILE_SIZE) - 2)
        end_row = min(self.ROWS, int((self.camera_y + self.height / ZOOM) / TILE_SIZE) + 3)

        # Draw visible tiles using render_map (First pass: Ground tiles and low obstacles)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char not in self.WALKABLE_TILES and tile_char not in ['r', 'l', 'u', 'd']:
                        # First draw concrete street under obstacles
                        self.draw_tile('G', col * TILE_SIZE, row * TILE_SIZE)
                        if tile_char not in {'T', 'o', 'p', 'k', 'Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y'}:
                            self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)
                    else:
                        # Draw concrete street under ladders, portals, and stations 1-5
                        if tile_char in {'L', 'H', 'I', 'r', 'l', 'u', 'd', '1', '2', '3', '4', '5'}:
                            self.draw_tile('G', col * TILE_SIZE, row * TILE_SIZE)
                        if tile_char not in {'1', '2', '3', '4', '5'}:
                            self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Piko (Hopscotch) Chalk Court on pavement near Station 4 (Ate Maya) if not cleared
        if 4 in self.quiz_stations and self.quiz_station_index <= 4 and self.quiz_state < 6:
            mx, my = self.quiz_stations[4]
            px_start = int(((mx - 2) * TILE_SIZE - self.camera_x) * ZOOM)
            py_start = int((my * TILE_SIZE - self.camera_y) * ZOOM)
            pw = int(24 * ZOOM)
            ph = int(14 * ZOOM)
            # Clean chalk blue hopscotch squares
            chalk_col = (160, 195, 230)
            pygame.draw.rect(self.screen, chalk_col, (px_start, py_start, pw, ph), 1)
            pygame.draw.rect(self.screen, chalk_col, (px_start, py_start + ph, pw, ph), 1)
            pygame.draw.rect(self.screen, chalk_col, (px_start - pw // 2, py_start + ph * 2, pw * 2, ph), 1)

        # Always draw portals: locked gate when quiz_state < 6, radiant active vortex when quiz_state == 6
        for portal in self.portals:
            portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height, is_unlocked=(self.quiz_state == 6), frame_counter=self.frame_counter)

        # Draw Active Filipino Street Character NPCs and their Landmark Props (Disappear when answered!)
        for num, (st_x, st_y) in self.quiz_stations.items():
            # Disappear NPC and props once their question is answered correctly!
            if num < self.quiz_station_index or self.quiz_state >= 6:
                continue

            info = self.station_npc_info.get(num, {})
            frames = info.get("frames", [])
            anim_frame = info.get("anim_frame", 0)
            world_x = st_x * TILE_SIZE
            world_y = st_y * TILE_SIZE

            # Station 2 Prop: Pinoy Sorbetes Cart next to Manong Sorbetero
            if num == 2 and "prop_sorbetes_cart" in self.tile_images:
                cart_img = self.tile_images["prop_sorbetes_cart"]
                cx = (st_x + 1) * TILE_SIZE
                cy = st_y * TILE_SIZE
                scaled_cart = pygame.transform.scale(cart_img, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
                self.screen.blit(scaled_cart, ((cx - self.camera_x) * ZOOM, (cy - self.camera_y) * ZOOM))

            # Station 3 Prop: Jeepney Route Sign next to Kuya Drayber
            if num == 3 and "prop_jeep_sign" in self.tile_images:
                sign_img = self.tile_images["prop_jeep_sign"]
                sx = (st_x + 1) * TILE_SIZE
                sy = st_y * TILE_SIZE
                scaled_sign = pygame.transform.scale(sign_img, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
                self.screen.blit(scaled_sign, ((sx - self.camera_x) * ZOOM, (sy - self.camera_y) * ZOOM))

            # Active Target NPC Floor Aura
            if num == self.quiz_station_index and self.quiz_state == 0:
                sx = (world_x - self.camera_x) * ZOOM
                sy = (world_y - self.camera_y) * ZOOM
                aura_surf = pygame.Surface((int(36 * ZOOM), int(16 * ZOOM)), pygame.SRCALPHA)
                pulse = (math.sin(self.frame_counter * 0.12) + 1) * 0.5
                aura_alpha = int(80 + 80 * pulse)
                pygame.draw.ellipse(aura_surf, (255, 215, 0, aura_alpha), (0, 0, int(36 * ZOOM), int(16 * ZOOM)))
                self.screen.blit(aura_surf, (sx - int(2 * ZOOM), sy + int(22 * ZOOM)))

            if frames:
                self.draw_npc_animated(world_x, world_y, frames, anim_frame)

        self.draw_player()

        # Draw visible tall tiles / painted cinder block walls (Second pass)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char in {'T', 'o', 'p', 'k', 'Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y'}:
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Progressive Traditional Bahay Kubo on Barrio Plaza in Map 5
        self.draw_bahay_kubo()

        # Station 1 Prop: Sari-Sari Store Awning above Tomas (if not cleared)
        if 1 in self.quiz_stations and self.quiz_station_index <= 1 and self.quiz_state < 6 and "prop_sari_awning" in self.tile_images:
            tx, ty = self.quiz_stations[1]
            awn_img = self.tile_images["prop_sari_awning"]
            scaled_awn = pygame.transform.scale(awn_img, (int(TILE_SIZE * ZOOM), int(14 * ZOOM)))
            self.screen.blit(scaled_awn, ((tx * TILE_SIZE - self.camera_x) * ZOOM, ((ty - 0.4) * TILE_SIZE - self.camera_y) * ZOOM))

        # Station 5 Prop: Glowing Christmas Parol Star on wall above Lola Rosa (if not cleared)
        if 5 in self.quiz_stations and self.quiz_station_index <= 5 and self.quiz_state < 6 and "prop_parol" in self.tile_images:
            lx, ly = self.quiz_stations[5]
            parol_img = self.tile_images["prop_parol"]
            scaled_parol = pygame.transform.scale(parol_img, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
            self.screen.blit(scaled_parol, ((lx * TILE_SIZE - self.camera_x) * ZOOM, ((ly - 1) * TILE_SIZE - self.camera_y) * ZOOM))

        # Tasteful Entrance Banderitas across starting arch (Row 1 only)
        if start_row <= 1 <= end_row:
            b_colors = [(230, 75, 60), (245, 195, 35), (50, 180, 80), (50, 150, 220), (160, 90, 180)]
            y_px = int((1 * TILE_SIZE - self.camera_y) * ZOOM)
            x_start = int((start_col * TILE_SIZE - self.camera_x) * ZOOM)
            x_end = int((end_col * TILE_SIZE - self.camera_x) * ZOOM)
            pygame.draw.line(self.screen, (100, 105, 115), (x_start, y_px), (x_end, y_px), 1)
            step = int(16 * ZOOM)
            for fx in range(x_start, x_end, step):
                fcol = b_colors[(fx // step) % len(b_colors)]
                pts = [(fx, y_px), (fx + step - 2, y_px), (fx + step // 2, y_px + int(8 * ZOOM))]
                pygame.draw.polygon(self.screen, fcol, pts)

        # Draw Active Objective NPC Indicator and Off-Screen Compass Pointer
        if self.quiz_state == 0 and self.quiz_station_index in self.quiz_stations:
            st_x, st_y = self.quiz_stations[self.quiz_station_index]
            npc_center_x = st_x * TILE_SIZE + TILE_SIZE // 2
            npc_center_y = st_y * TILE_SIZE + TILE_SIZE // 2
            
            screen_npc_x = (st_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (st_y * TILE_SIZE - self.camera_y) * ZOOM
            
            npc_name = self.station_npc_info.get(self.quiz_station_index, {}).get("name", f"Station {self.quiz_station_index}")
            
            # 1. On-Screen Floating Objective Badge (Always visible over active target NPC)
            bob = math.sin(self.frame_counter * 0.15) * 3 * ZOOM
            badge_x = screen_npc_x + (TILE_SIZE * ZOOM) / 2 - 8 * ZOOM
            badge_y = screen_npc_y - 20 * ZOOM + bob
            
            # Yellow Diamond Quest Badge
            badge_rect = pygame.Rect(badge_x, badge_y, 16 * ZOOM, 16 * ZOOM)
            pygame.draw.rect(self.screen, (255, 215, 0), badge_rect, border_radius=4)
            pygame.draw.rect(self.screen, (0, 0, 0), badge_rect, 1, border_radius=4)
            
            excl_surf = self.font.render("!", True, (0, 0, 0))
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

            # 2. Off-Screen Directional Compass Pointer (Guides Grade 2 student when NPC is off-screen)
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

        # 3. Off-Screen Directional Pointer for Exit Portal (When all 5 challenges cleared)
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

        # Draw Fiesta Sparkle Particles during Speed Boost Sprint & Mini-Puzzle Solved Celebration
        for sp in self.fiesta_sparkles:
            if sp.get("is_screen"):
                sx = sp["x"]
                sy = sp["y"]
            else:
                sx = (sp["x"] - self.camera_x) * ZOOM
                sy = (sp["y"] - self.camera_y) * ZOOM
            if 0 <= sx <= self.width and 0 <= sy <= self.height:
                base_r = sp.get("rad", sp.get("size", 3))
                life_pct = max(0.0, min(1.0, sp.get("life", 0.5) / sp.get("max_life", 0.5)))
                r = max(1, int(base_r * life_pct))
                pygame.draw.circle(self.screen, sp.get("color", (255, 215, 0)), (int(sx), int(sy)), r)

        # Draw In-World Floating Barrio Banner Alert (During Sprint or Portal Unlock)
        if self.banner_timer > 0 and self.banner_text:
            b_w, b_h = 680, 64
            b_x = (self.width - b_w) // 2
            b_y = 70
            
            b_surf = pygame.Surface((b_w, b_h), pygame.SRCALPHA)
            b_surf.fill((15, 23, 42, 230))
            self.screen.blit(b_surf, (b_x, b_y))
            pygame.draw.rect(self.screen, (245, 158, 11), (b_x, b_y, b_w, b_h), 2, border_radius=10)
            
            t_surf = self.dialog_header_font.render(self.banner_text, True, (255, 215, 0))
            self.screen.blit(t_surf, (b_x + (b_w - t_surf.get_width()) // 2, b_y + 10))
            
            s_surf = self.dialog_hint_font.render(self.banner_sub, True, (254, 240, 138))
            self.screen.blit(s_surf, (b_x + (b_w - s_surf.get_width()) // 2, b_y + 36))

        # Draw UI overlay
        if self.quiz_state == 1:
            self.draw_quiz_dialog()
        elif self.quiz_state == 2:
            self.draw_wrong_dialog()
        elif self.quiz_state == 3:
            self.draw_correct_dialog()
        elif self.quiz_state == 4:
            self.draw_out_of_tries_dialog()
        elif self.quiz_state == 5:
            self.draw_victory_speech()

        # Draw Cinematic Bahay Kubo Award Card Overlay in Map 5
        self.draw_kubo_award_animation()

        self.draw_ui()

        # Draw 10-Minute Stage Timer HUD
        self.draw_stage_timer_hud()

        # Draw Time's Up modal dialog if timer expired
        if self.time_up_dialog_active:
            self.draw_time_up_dialog()

        # Draw smooth seamless warp-out transition overlay
        if self.warp_out_active:
            progress = max(0.0, min(1.0, 1.0 - (self.warp_out_timer / self.warp_out_duration)))
            warp_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            warp_overlay.fill((254, 243, 199, int(progress * 255)))
            center = (self.width // 2, self.height // 2)
            max_r = int(math.hypot(self.width, self.height) / 2)
            r = int(progress * max_r)
            if r > 0:
                pygame.draw.circle(warp_overlay, (255, 215, 0, int((1.0 - progress) * 230)), center, r, max(3, int(10 * ZOOM)))
            self.screen.blit(warp_overlay, (0, 0))

        # In-Game Universal Pause Button & Modal
        self.pause_menu.draw_button(self.cursor_pos)
        if self.pause_menu.is_paused:
            self.pause_menu.draw_modal(self.cursor_pos)

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

        # HUD Objectives Box (Top/Bottom Center)
        if self.quiz_state in [0, 6]:
            box_w = 460
            box_h = 78
            box_x = (self.width - box_w) // 2
            box_y = self.height - box_h - 18

            # Translucent dark slate background
            hud_bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            hud_bg.fill((15, 23, 42, 220))
            self.screen.blit(hud_bg, (box_x, box_y))

            # Border: Gold when in progress, Emerald Green when complete
            border_color = (218, 165, 32) if self.quiz_state < 6 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_w, box_h), 2, border_radius=10)
            pygame.draw.rect(self.screen, (0, 0, 0, 120), (box_x + 2, box_y + 2, box_w - 4, box_h - 4), 1, border_radius=8)

            # Header title in Gold
            title_font = self.get_ui_font(13, bold=True)
            title_surf = title_font.render("BARANGAY KALYE OBJECTIVES", True, (255, 215, 0))
            self.screen.blit(title_surf, (box_x + 16, box_y + 8))

            # Details font
            item_font = self.get_ui_font(12, bold=True)

            if self.quiz_state < 6:
                cur_target_str = self.station_npc_info.get(self.quiz_station_index, {}).get("title", f"Station {self.quiz_station_index}")
                obj1 = f"Target: {cur_target_str}"
                obj1_surf = item_font.render(obj1, True, (255, 220, 80))
                self.screen.blit(obj1_surf, (box_x + 16, box_y + 32))

                if self.map_name == "map5.txt":
                    obj2 = f"Bahay Kubo: {self.kubo_pieces_collected}/5 Pieces Built (Portal Locked)"
                    obj2_surf = item_font.render(obj2, True, (254, 240, 138) if self.kubo_pieces_collected > 0 else (148, 163, 184))
                else:
                    cleared_count = max(0, self.quiz_station_index - 1)
                    obj2 = f"Progress: {cleared_count}/5 Stalls Cleared (Portal Locked)"
                    obj2_surf = item_font.render(obj2, True, (148, 163, 184) if cleared_count == 0 else (74, 222, 128))
                self.screen.blit(obj2_surf, (box_x + 16, box_y + 54))
            else:
                obj1 = "BAHAY KUBO FULLY CONSTRUCTED!" if self.map_name == "map5.txt" else "ALL BARANGAY CHALLENGES CLEARED!"
                obj1_surf = item_font.render(obj1, True, (74, 222, 128))
                self.screen.blit(obj1_surf, (box_x + 16, box_y + 32))

                obj2 = ">> Exit Portal Status: OPEN - Enter portal to return!"
                obj2_surf = item_font.render(obj2, True, (255, 215, 0))
                self.screen.blit(obj2_surf, (box_x + 16, box_y + 54))


        if self.show_info:
            npc_status = [self.station_npc_info.get(i, {}).get("name", f"Station {i}") for i in range(1, 6)]

            npc_text = ", ".join(npc_status) if npc_status else "None"

            info_lines = [
                f"Map: {self.map_name}",
                f"Goal: Reach the {self.goal_portal_direction} portal -> Return to town",
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
        return None

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