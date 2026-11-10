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
from core.paths import get_base_dir
from core.camera_system import LoLCamera
from core.font_manager import get_font
from core.visual_effects import (
    DustParticleSystem,
    draw_beacon_marker,
    draw_aura_glow,
    build_composite_title_letters,
    draw_composite_title_wave,
)
from core.npc_scripts import get_map_instructions, get_station_script, get_mentor_script
from core.npc_dialog_system import InstructionModal, NPCGreetingDialog
from core.state_machine import State, UIStateMachine

try:
    from db import db
except ImportError:
    try:
        from db.connect_db import db
    except ImportError:
        db = None

from db.save_system import save_student_progress

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
        self.timer_warning_played = False

        # Strict UI State Machine & Pushdown Automata
        from core.state_machine import State, UIStateMachine
        self.state_machine = UIStateMachine(initial_state=State.Exploration, host=self)

        # Universal In-Stage Pause Menu
        from core.pause_menu import InGamePauseMenu
        self.pause_menu = InGamePauseMenu(self.screen, self.width, self.height, self.main_menu, self.return_to_stage_select, restart_callback=self.restart_level, state_machine=self.state_machine)

        # Cognitive Array Matrix / Fraction Bakery Subsystem (Normal In-Engine Puzzle)
        self.array_puzzle = None

        # 3-Star Victory Report Card & Celebration Particles
        from core.report_card import VictoryReportCard, CelebrationParticleSystem
        self.celebration_particles = CelebrationParticleSystem()
        self.victory_card = VictoryReportCard(self.screen, self.width, self.height, self.main_menu,
                                              quarter_id="quarter3",
                                              replay_callback=self.restart_level,
                                              continue_callback=self.finish_and_return_to_hub)

        # Universal RPG Quest Question Dialog
        from core.quiz_dialog import RPGQuizDialog
        self.quiz_dialog = RPGQuizDialog(self.screen, self.width, self.height, getattr(self.main_menu, 'audio_manager', None))

        # Resolve Student Player Name
        self.player_name = "Student"
        if hasattr(self.main_menu, 'selected_student') and self.main_menu.selected_student:
            self.player_name = self.main_menu.selected_student.get('first_name') or self.main_menu.selected_student.get('username') or "Student"

        # NPC Instruction Modal & Proximity Greeting Dialog System
        self.instruction_modal = InstructionModal(self.screen, self.width, self.height)
        self.greeting_dialog = NPCGreetingDialog(self.screen, self.width, self.height)
        self.guide_btn_rect = pygame.Rect(self.width - 256, 18, 110, 36)
        self.fist_progress = 0.0

        # Dynamic Hierarchy Pathfinder & Starlight Visual Trail Guide
        from core.pathfinder_guide import QuestPathfinderGuide
        self.path_guide = QuestPathfinderGuide(self, quarter_id="quarter3", theme="desert")

        # Show Initial Map Instructions Popup
        map_instr = get_map_instructions(self.map_name, self.player_name)
        self.instruction_modal.show(map_instr)

        # Performance Overlay Cache
        self._dim_overlay = None

        # Visual Effects & Dust Footsteps
        self.dust_particles = DustParticleSystem(max_particles=30)

        # ============================================================
        # PATHS
        # ============================================================
        self.BASE_DIR = get_base_dir()

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

        # Skeleton NPC (Quarter 3 Portal Guardian & Solar Array Trial)
        self.npc_skeleton_sprite = None
        self.npc_skeleton_x = 0
        self.npc_skeleton_y = 0
        self.npc_skeleton_tile_x = 0
        self.npc_skeleton_tile_y = 0
        self.npc_skeleton_found = False
        self.npc_skeleton_left_sprites = []
        self.npc_skeleton_down_sprites = []
        self.npc_skeleton_right_sprites = []
        self.npc_skeleton_up_sprites = []
        self.npc_skeleton_dir = "left"
        self.npc_skeleton_anim_frame = 0
        self.npc_skeleton_anim_timer = 0

        # Guardian Skeleton State: 0 = waiting for stations, 1 = guarding portal (aura & badge), 2 = trial prompt modal, 3 = puzzle active, 4 = victory speech, 5 = portal unlocked
        self.guardian_skeleton_state = 0
        self.skeleton_guardian_active = True
        self.guardian_skeleton_proximity_cooldown = 0
        p_box_w = min(860, self.width - 40)
        p_box_h = 370
        p_box_x = (self.width - p_box_w) // 2
        p_box_y = (self.height - p_box_h) // 2
        p_diag_x = p_box_x + 24 + 140 + 24
        self.guardian_skeleton_btn_rect = pygame.Rect(p_diag_x, p_box_y + p_box_h - 76, 380, 52)
        self.guardian_skeleton_close_btn_rect = pygame.Rect(p_diag_x + 380 + 16, p_box_y + p_box_h - 76, 190, 52)
        self.guardian_skeleton_x_btn_rect = pygame.Rect(p_box_x + p_box_w - 38, p_box_y + 8, 28, 28)

        # Sun Temple Fraction Match (Guardian Skeleton Trial + Backwards-Compatible Aliases)
        self.fraction_match_active = False
        self.fraction_match_solved = False
        self.fraction_match_all_placed = False
        self.fraction_match_slots = []
        self.fraction_match_pieces = []
        self.dragged_fraction_piece = None
        self.selected_fraction_piece = None
        self.fraction_drag_offset_x = 0
        self.fraction_drag_offset_y = 0
        self.fraction_drag_start_pos = (0, 0)
        self.fraction_match_sparkles = []
        self.fraction_match_feedback_timer = 0.0
        self.fraction_match_feedback_kind = ""
        self._fraction_match_panel_surf = None

        self.solar_array_puzzle_active = False
        self.solar_array_puzzle_solved = False
        self.solar_array_puzzle_solved_time = 0
        self.solar_array_puzzle_all_placed = False
        self.solar_array_puzzle_slots = []
        self.solar_array_puzzle_pieces = []
        self.dragged_solar_piece = None
        self.solar_drag_offset_x = 0
        self.solar_drag_offset_y = 0
        self.solar_hovered_piece = None
        self.solar_hovered_slot = None
        self.solar_sparkles = []
        self.solar_puzzle_reset_btn_rect = None
        self.solar_puzzle_continue_btn_rect = None
        self.solar_puzzle_close_btn_rect = None
        self.solar_puzzle_x_btn_rect = None
        self.mouse_drag_active = False
        self.mouse_drag_start_pos = (0, 0)
        self.solar_matrix_rows = 1
        self.solar_matrix_cols = 4
        self.solar_matrix_row_completed = [False]
        self.solar_matrix_beam_alphas = [0.0]
        self.solar_matrix_challenge = None
        self.solar_array_target_equation = ''
        self.solar_array_factor_desc = ''

        # Legacy Fraction Bakery flags preserved as aliases
        self.fraction_bakery_active = False
        self.fraction_bakery_solved = False
        self.dragged_bakery_slice = None

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

        # Snap camera directly to player spawn
        self.lol_camera.snap_to(self.player_x, self.player_y, TILE_SIZE, self.MAP_WIDTH, self.MAP_HEIGHT)
        self.camera_x = self.lol_camera.camera_x
        self.camera_y = self.lol_camera.camera_y

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

        # Seamless portal warp transition variables
        self.warp_out_active = False
        self.warp_out_timer = 0.0
        self.warp_out_duration = 0.65

        # ============================================================
        # UI & REUSABLE FONTS
        # ============================================================
        self.show_info = False
        self.font = get_font("Comic Sans MS", 16)
        self.small_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 13, bold=True)
        self.dialog_header_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 24, bold=True)
        self.dialog_q_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 19, bold=True)
        self.dialog_choice_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 20, bold=True)
        self.dialog_badge_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 22, bold=True)
        self.dialog_hint_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 17, bold=True)
        self.dialog_speaker_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 24, bold=True)
        self.dialog_btn_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 20, bold=True)
        self.dialog_msg_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 19, bold=True)
        self.dialog_regular_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18)
        self.dialog_stat_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 16, bold=True)

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
                    print(f"[LOC] Quiz Station {num} found at: ({x}, {y})")

        # Correct answer random responses
        self.current_correct_phrase = ""
        self.correct_phrases = [
            "Splendid! Your mathematical knowledge shines bright!",
            "Outstanding! That is correct, onto the next challenge!",
            "Superb! You are a brilliant math explorer!"
        ]
        self.player_block_timer = 0.0
        self.ident_input_text = ""

        # Cloud-authoritative Questions List (0..N active cloud questions)
        self.quiz_questions = []
        self.active_station_count = 0

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

        # Sync questions strictly from the cloud / cloud cache (after bridge_tiles & banners exist)
        self.load_database_questions()

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

        # Puzzle Sound Synthesis
        self.sun_relic_active = False
        self.load_puzzle_sounds()

        # ============================================================
        # AREA TITLE ANIMATION
        # ============================================================
        self.title_elapsed = 0.0
        self.title_duration = 5.0
        self.title_active = True

        # Load Pixelfont
        self.pixel_font_path = os.path.join(self.BASE_DIR, "assets", "fonts", "Pixelfont.otf")
        self.pixel_font_size = 72
        try:
            self.title_font = pygame.font.Font(self.pixel_font_path, self.pixel_font_size)
        except Exception:
            self.title_font = pygame.font.SysFont("Consolas", self.pixel_font_size, bold=True)

        self.title_text = "Monetary Desert"
        self.title_spacing = 12

        self.title_text_color = (255, 255, 255) # White
        self.title_outline_color = (0, 0, 0) # Black outline
        self.title_glow_color = (180, 180, 180) # Grey glow

        # Pre-render composite letters (single blit per glyph during wave animation)
        self.title_letters = build_composite_title_letters(
            self.title_text,
            self.title_font,
            self.title_text_color,
            self.title_outline_color,
            self.title_glow_color,
        )
        self.title_total_width = sum(l["width"] for l in self.title_letters) + self.title_spacing * (len(self.title_text) - 1)

        # ============================================================
        # [QUEST] 3 DISTINCT GAMEPLAY MODES FOR QUARTER 3
        # ============================================================
        self.is_caravan_mode = (self.map_name == "map7.txt")       # Map 7: Explorer's Royal Caravan
        self.is_relic_hunt_mode = False                            # In-world orb collection removed so gameplay is clean and not complicated
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
        # CITADEL OF THE SUN: KEYSTONE ALTAR SYSTEM (MAP 9 GAMEPLAY)
        # ============================================================
        self.citadel_keystones = {
            1: {"num": 1, "roman": "I", "name": "Apple Array Scepter", "math": "3 x 4", "color": (239, 68, 68), "icon": "apple"},
            2: {"num": 2, "roman": "II", "name": "Coconut Oasis Orb", "math": "4 x 2", "color": (180, 83, 9), "icon": "coconut"},
            3: {"num": 3, "roman": "III", "name": "Scarab Coin Chalice", "math": "10 / 2", "color": (234, 179, 8), "icon": "chest"},
            4: {"num": 4, "roman": "IV", "name": "Solar Half Keystone", "math": "1/2", "color": (245, 158, 11), "icon": "sun_disk"},
            5: {"num": 5, "roman": "V", "name": "Golden Ingot Prism", "math": "1/3", "color": (217, 119, 6), "icon": "ingot"}
        }
        self.citadel_collected_keystones = []
        self.citadel_banner_text = ""
        self.citadel_banner_sub = ""
        self.citadel_banner_timer = 0.0

        # Backwards-compatible cognitive puzzle lock flag
        self.mini_puzzle_active = False

        # Initialize High-Performance Surface & Sprite Cache for AMD A4-6300 APU (60 FPS)
        self.init_cached_surfaces()

        print(f"[OK] Quarter3 initialized with map: {self.map_name}")
        print(f"   Goal portal: {self.goal_portal_direction}")
        print(f"   Portals loaded: {len(self.portals)}")

    # ============================================================
    # UI STATE MACHINE QUERIES & SYNCHRONIZATION
    # ============================================================
    def is_dialogue_active(self):
        """Checks if dialogue, quiz prompt, modal, or cinematic is active."""
        if getattr(self, 'quiz_dialog', None) and getattr(self.quiz_dialog, 'is_active', False):
            return True
        if getattr(self, 'quiz_state', 0) in [1, 2, 3, 4, 5, 7]:
            return True
        if getattr(self, 'instruction_modal', None) and getattr(self.instruction_modal, 'is_visible', False):
            return True
        if getattr(self, 'greeting_dialog', None) and getattr(self.greeting_dialog, 'is_visible', False):
            return True
        if getattr(self, 'time_up_dialog_active', False):
            return True
        if getattr(self, 'camera_pan_active', False):
            return True
        if getattr(self, 'victory_card', None) and getattr(self.victory_card, 'active', False):
            return True
        if getattr(self, 'ident_dialog_active', False):
            return True
        if getattr(self, 'guardian_skeleton_state', 0) == 2:
            return True
        return False

    def is_cognitive_puzzle_active(self):
        """Checks if an interactive cognitive puzzle / minigame UI is active."""
        if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False):
            return True
        if getattr(self, 'guardian_skeleton_state', 0) == 3:
            return True
        if getattr(self, 'mini_puzzle_active', False):
            return True
        if getattr(self, 'dragged_fraction_piece', None) is not None or getattr(self, 'dragged_solar_piece', None) is not None:
            return True
        return False

    def sync_ui_state(self):
        """Synchronizes the UIStateMachine PDA state with current gameplay flags."""
        from core.state_machine import State
        if self.is_cognitive_puzzle_active():
            if self.state_machine.current_state != State.CognitivePuzzle:
                self.state_machine.set_state(State.CognitivePuzzle)
        elif self.is_dialogue_active():
            if self.state_machine.current_state != State.Dialogue:
                self.state_machine.set_state(State.Dialogue)
        else:
            if self.state_machine.current_state != State.Exploration:
                self.state_machine.set_state(State.Exploration)

    # ============================================================
    # RASPBERRY PI HIGH-PERFORMANCE PRE-CACHING (60 FPS)
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


        # 4. Pre-scale Station Number NPCs
        if hasattr(self, 'station_npcs') and self.station_npcs:
            for st_num, data in self.station_npcs.items():
                data["frames"] = [
                    pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in data["frames"]
                ]

        # 5. Pre-scale static & walking NPCs (Oldman, Skeleton Guardian, Knight)
        if getattr(self, 'npc_oldman_sprite', None):
            self.npc_oldman_sprite = pygame.transform.scale(self.npc_oldman_sprite, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha()
        if getattr(self, 'npc_skeleton_sprite', None):
            self.npc_skeleton_sprite = pygame.transform.scale(self.npc_skeleton_sprite, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha()
        if getattr(self, 'npc_skeleton_left_sprites', None):
            self.npc_skeleton_left_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_skeleton_left_sprites]
        if getattr(self, 'npc_skeleton_right_sprites', None):
            self.npc_skeleton_right_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_skeleton_right_sprites]
        if getattr(self, 'npc_skeleton_down_sprites', None):
            self.npc_skeleton_down_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_skeleton_down_sprites]
        if getattr(self, 'npc_skeleton_up_sprites', None):
            self.npc_skeleton_up_sprites = [pygame.transform.scale(f, (self.scaled_tile_size, self.scaled_tile_size)).convert_alpha() for f in self.npc_skeleton_up_sprites]
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
        math_font = get_font("Comic Sans MS", 22, bold=True)
        for label, x_pos in [("+", 70), ("=", 180), ("3", 290), ("x", 390), ("7", 520), ("-", 610)]:
            text = math_font.render(label, True, (59, 130, 246))
            self.cached_math_bg.blit(text, (x_pos, 18))
        has_disp = pygame.display.get_surface() is not None
        if has_disp:
            self.cached_math_bg = self.cached_math_bg.convert()

        # 8. Pre-render full-screen dimming overlays
        self.dialog_dim_overlay = pygame.Surface((self.width, self.height))
        self.dialog_dim_overlay.fill((0, 0, 0))
        if has_disp:
            self.dialog_dim_overlay = self.dialog_dim_overlay.convert()
        self.dialog_dim_overlay.set_alpha(175)

        self.wrong_dialog_dim_overlay = pygame.Surface((self.width, self.height))
        self.wrong_dialog_dim_overlay.fill((0, 0, 0))
        if has_disp:
            self.wrong_dialog_dim_overlay = self.wrong_dialog_dim_overlay.convert()
        self.wrong_dialog_dim_overlay.set_alpha(160)

        # 9. Pre-render HUD & Banner glassmorphic background surfaces
        self.quest_hud_bg = pygame.Surface((760, 68), pygame.SRCALPHA)
        self.quest_hud_bg.fill((15, 23, 42, 220))

        self.banner_bg = pygame.Surface((640, 68), pygame.SRCALPHA)
        self.banner_bg.fill((15, 23, 42, 230))

        self.obj_hud_bg = pygame.Surface((480, 80), pygame.SRCALPHA)
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
        self._skel_portrait_surf = None
        self._skel_aura_cache = {}
        self._skel_sun_cache = {}
        self._npc_tag_bg_cache = {}
        self._hud_timer_surf = pygame.Surface((160, 38), pygame.SRCALPHA)
        self._hud_timer_surf.fill((15, 23, 42, 220))
        if pygame.display.get_surface() is not None:
            self._hud_timer_surf = self._hud_timer_surf.convert_alpha()

        # 15. Pre-render full static desert ground & foreground tree layers (eliminates Python tile loops)
        self.build_prerendered_map()

    def build_prerendered_map(self):
        """Pre-bakes static ground/walls and foreground trees/tumbleweeds into C-blittable map surfaces."""
        ts = self.scaled_tile_size
        map_w = max(1, self.COLS * ts)
        map_h = max(1, self.ROWS * ts)
        bg_surf = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
        fg_surf = pygame.Surface((map_w, map_h), pygame.SRCALPHA)

        sand_img = self.scaled_tile_images.get('G', self.scaled_fallback_tile)
        sand_under_set = {'T', 'w', 'Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y'}

        for row in range(min(self.ROWS, len(self.render_map))):
            row_str = self.render_map[row]
            dy = row * ts
            for col in range(min(self.COLS, len(row_str))):
                tile_char = row_str[col]
                dx = col * ts
                if tile_char in sand_under_set:
                    bg_surf.blit(sand_img, (dx, dy))
                if tile_char == 'T' or tile_char == 'w':
                    fg_surf.blit(self.scaled_tile_images.get(tile_char, self.scaled_fallback_tile), (dx, dy))
                else:
                    bg_surf.blit(self.scaled_tile_images.get(tile_char, self.scaled_fallback_tile), (dx, dy))

        if pygame.display.get_surface() is not None:
            self._bg_map_surface = bg_surf.convert_alpha()
            self._fg_trees_surface = fg_surf.convert_alpha()
        else:
            self._bg_map_surface = bg_surf
            self._fg_trees_surface = fg_surf

    def show_instructions(self):
        """Displays the map instructions modal with student context."""
        map_instr = get_map_instructions(self.map_name, self.player_name)
        if hasattr(self, 'instruction_modal'):
            self.instruction_modal.show(map_instr)

    # ============================================================
    # DATABASE INTEGRATION
    # ============================================================
    def load_database_questions(self):
        if not self.is_quiz_map:
            self.active_station_count = 0
            return

        from db.connect_db import map_cloud_questions
        mapped_questions = []
        try:
            if db:
                questions_result = db.get_questions(quarter=3)
                mapped_questions = map_cloud_questions(
                    questions_result,
                    default_hint="Examine the choices carefully and select the best answer below!",
                    allow_ident=True,
                )
        except Exception as e:
            print(f"[WARN] Exception loading cloud questions for Quarter 3: {e}")

        sorted_ids = sorted(self.quiz_stations.keys())
        active_count = min(len(sorted_ids), len(mapped_questions))
        active_ids = sorted_ids[:active_count]

        for idx, q_item in enumerate(mapped_questions[:active_count], start=1):
            q_item.setdefault("station", idx)
            q_item.setdefault("title", f"CHALLENGE {idx}")

        self.quiz_questions = mapped_questions[:active_count]
        self.active_station_count = active_count
        self.quiz_stations = {k: self.quiz_stations[k] for k in active_ids}
        self.station_npcs = {k: self.station_npcs[k] for k in active_ids if k in self.station_npcs}
        self.first_attempt_correct = {k: True for k in active_ids}
        self.station_attempts = {k: 0 for k in active_ids}

        if active_count == 0:
            self.quiz_station_index = 6
            self.current_question_index = 0
            self.guardian_skeleton_state = 1
            if getattr(self, 'bridge_tiles', None):
                for bx, by in self.bridge_tiles:
                    if 0 <= by < len(self.game_map) and 0 <= bx < len(self.game_map[by]):
                        self.game_map[by] = self.game_map[by][:bx] + "B" + self.game_map[by][bx + 1:]
                        self.render_map[by] = self.render_map[by][:bx] + "B" + self.render_map[by][bx + 1:]
                self.built_bridge_count = len(self.bridge_tiles)
            self.caravan_upgrade_banner_text = "NO CLOUD QUESTIONS SET"
            self.caravan_upgrade_banner_sub = "Speak with the Skeleton Guardian to begin the Sun Fraction Match!"
            self.caravan_upgrade_banner_timer = 6.0
            print("[CLOUD SYNC] Quarter 3 synced 0 active cloud questions — stations skipped, Skeleton Guardian unlocked.")
        else:
            self.quiz_station_index = active_ids[0]
            self.current_question_index = 0
            print(f"[CLOUD SYNC] Quarter 3 synced {active_count} cloud question(s) across {active_count} station(s).")

    def save_results_to_database(self):
        if getattr(self, '_results_saved_to_db', False):
            return
        self._results_saved_to_db = True
        import threading
        threading.Thread(target=self._run_save_results_to_database, daemon=True).start()

    def _run_save_results_to_database(self):
        if not self.is_quiz_map:
            return
        try:
            if not db:
                return
            total_questions = getattr(self, 'active_station_count', len(self.quiz_questions))
            if total_questions <= 0:
                print("[CLOUD SYNC] Quarter 3 completed with 0 cloud questions — skipping academic quiz score upload.")
                return
            student_db_id = getattr(self.main_menu, 'student_db_id', None)
            if not student_db_id and getattr(self.main_menu, 'selected_student', None):
                student_db_id = self.main_menu.selected_student.get('id')
            if not student_db_id:
                print("[WARN] No student_db_id available in main_menu. Skipping database record.")
                return
            correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
            percentage = (correct_answers / float(total_questions)) * 100.0
            score = int(round(percentage))

            assessment_id = db.get_assessment_id(quarter=3)
            if assessment_id:
                print(f"[LOG] Linked Quarter 3 result to Assessment ID: {assessment_id}")

            feedback_msg = f"Completed Quarter 3 (Math Explorations). Answered {correct_answers} of {total_questions} questions correctly on the first attempt."
            sel_student = getattr(self.main_menu, 'selected_student', None) or {}
            grade_level = sel_student.get('level') or sel_student.get('gradeLevel') or sel_student.get('grade_level') or 'Grade 2'

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
                print(f"Successfully saved Quarter 3 Game Result to Database for Student DB ID {student_db_id}!")
                print(f"   Score: {score}/{total_questions} ({percentage}%)")
            else:
                print("[WARN] Failed to save Quarter 3 game results via Database API.")
        except Exception as e:
            print(f"[WARN] Exception saving Quarter 3 game results: {e}")

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
        self.npc_oldman_found = False
        self.npc_skeleton_found = False
        self.npc_knight_found = False

        # Set positions from map data
        for marker, positions in self.npc_positions_data.items():
            for x, y in positions:
                if marker == 'B':
                    # 'B' in Quarter 3 maps represents golden aqueduct / bridge tiles, not an NPC
                    continue
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
                self.npc_oldman_sprite = placeholder
        except Exception as e:
            print(f"[FAIL] Error loading Oldman: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((200, 200, 200))
            self.npc_oldman_sprite = placeholder

        # Load Skeleton Guardian (Quarter 3 Guardian)
        skeleton_path = os.path.join(self.NPC_PATH_SKELETON, "skeleton.png")
        try:
            if os.path.exists(skeleton_path):
                img = pygame.image.load(skeleton_path).convert_alpha()
                self.npc_skeleton_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"[OK] Loaded Skeleton Guardian sprite")
            else:
                print(f"[WARN] Skeleton sprite not found at: {skeleton_path}")
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((220, 220, 220))
                self.npc_skeleton_sprite = placeholder

            self.npc_skeleton_left_sprites = []
            for name in ["skeleton_left.png", "skeleton_left_1.png", "skeleton_left_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_left_sprites.append(scaled)

            self.npc_skeleton_down_sprites = []
            for name in ["skeleton_down.png", "skeleton_down_1.png", "skeleton_down_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_down_sprites.append(scaled)

            self.npc_skeleton_right_sprites = []
            for name in ["skeleton_right.png", "skeleton_right_1.png", "skeleton_right_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_right_sprites.append(scaled)

            self.npc_skeleton_up_sprites = []
            for name in ["skeleton_up.png", "skeleton_up_1.png", "skeleton_up_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_up_sprites.append(scaled)
        except Exception as e:
            print(f"[FAIL] Error loading Skeleton Guardian: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((220, 220, 220))
            self.npc_skeleton_sprite = placeholder

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
                    print(f"[WARN] Error loading frame {path}: {e}")
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
        print("[OK] Loaded 5 Animated Number Character Station NPCs (Number 1-5)")

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
            self._scaled_cache = {}

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
                    cache_key = (self.current_frame, scaled_width, scaled_height)
                    scaled_img = self._scaled_cache.get(cache_key)
                    if scaled_img is None:
                        scaled_img = pygame.transform.scale(portal_img, (scaled_width, scaled_height))
                        if pygame.display.get_surface() is not None:
                            scaled_img = scaled_img.convert_alpha()
                        self._scaled_cache[cache_key] = scaled_img
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
                game_row_list = list(self.game_map[r]) if r < len(self.game_map) else []
                modified = False
                for c in range(p_x, min(len(row_list), p_x + w)):
                    if row_list[c] in ['Z', 'M', 'n', 's', 't', 'J', 'Q', 'V', 'X', 'Y']:
                        row_list[c] = 'G'
                        if game_row_list and c < len(game_row_list):
                            game_row_list[c] = 'G'
                        modified = True
                if modified:
                    self.render_map[r] = ''.join(row_list)
                    if game_row_list:
                        self.game_map[r] = ''.join(game_row_list)

    def load_static_portals(self):
        self.portals = []
        # Use game_map for portal detection so markers are never lost
        for y, row in enumerate(self.game_map):
            row_list = list(self.render_map[y]) if y < len(self.render_map) else []
            game_row_list = list(row)
            modified = False
            for x, c in enumerate(row):
                if c == 'r':
                    portal = self.Portal(x, y, 'right', is_static=True)
                    portal.set_animation(self.portal_frames_cache['right'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = 'G'
                    game_row_list[x] = 'G'
                    modified = True
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = 'G'
                    game_row_list[x] = 'G'
                    modified = True
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = 'G'
                    game_row_list[x] = 'G'
                    modified = True
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = 'G'
                    game_row_list[x] = 'G'
                    modified = True
            if modified:
                if row_list and y < len(self.render_map):
                    self.render_map[y] = ''.join(row_list)
                self.game_map[y] = ''.join(game_row_list)

        # Position Skeleton Guardian guarding the exit portal
        if self.map_name == "map7.txt":
            self.npc_skeleton_tile_x = 46
            self.npc_skeleton_tile_y = 16
            self.npc_skeleton_dir = "left"
            self.npc_skeleton_found = True
        elif self.map_name == "map8.txt":
            self.npc_skeleton_tile_x = 46
            self.npc_skeleton_tile_y = 7
            self.npc_skeleton_dir = "left"
            self.npc_skeleton_found = True
        elif self.map_name == "map9.txt":
            self.npc_skeleton_tile_x = 1
            self.npc_skeleton_tile_y = 10
            self.npc_skeleton_dir = "right"
            self.npc_skeleton_found = True
        elif self.portals:
            p = self.portals[0]
            if p.direction == 'right':
                self.npc_skeleton_tile_x = max(0, p.x - 1)
                self.npc_skeleton_tile_y = p.y
                self.npc_skeleton_dir = "left"
            elif p.direction == 'left':
                self.npc_skeleton_tile_x = min(self.COLS - 1, p.x + p.width_tiles)
                self.npc_skeleton_tile_y = p.y
                self.npc_skeleton_dir = "right"
            elif p.direction == 'up':
                self.npc_skeleton_tile_x = p.x
                self.npc_skeleton_tile_y = min(self.ROWS - 1, p.y + p.height_tiles)
                self.npc_skeleton_dir = "up"
            else:
                self.npc_skeleton_tile_x = p.x
                self.npc_skeleton_tile_y = max(0, p.y - 1)
                self.npc_skeleton_dir = "down"
            self.npc_skeleton_found = True
        else:
            self.npc_skeleton_tile_x = 46
            self.npc_skeleton_tile_y = 16
            self.npc_skeleton_dir = "left"
            self.npc_skeleton_found = True

        self.npc_skeleton_x = self.npc_skeleton_tile_x * TILE_SIZE
        self.npc_skeleton_y = self.npc_skeleton_tile_y * TILE_SIZE

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
    def return_to_stage_select(self, completed=True):
        """Return to the stage select screen"""
        if self.main_menu:
            # Save results to database on completion
            if completed:
                self.save_results_to_database()
                try:
                    total_questions = getattr(self, 'active_station_count', len(self.quiz_questions))
                    correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
                    percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 100.0
                    score = int(round(percentage)) if total_questions > 0 else 100
                    from db.save_system import mark_quarter_completed
                    mark_quarter_completed(self.main_menu, "quarter3", score=score, percentage=percentage, total_questions=total_questions)
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("victory_fanfare")
                        self.main_menu.audio_manager.play_sfx("portal_warp")
                except Exception as e:
                    print(f"[WARN] Error recording Quarter 3 completion: {e}")

            if completed:
                self.completed = True
            self.main_menu.current_screen = "stage_select"
            self.main_menu.quarter3 = None
            self.cleanup()
            try:
                from screens.stageselect import StageSelect
            except ImportError:
                from .stageselect import StageSelect
            self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
            print("[HOME] Returning to stage select")
            
            # Save student progress immediately to record quarter completion
            from db.save_system import save_student_progress
            save_student_progress(self.main_menu)
            
        return "back"

    def restart_level(self):
        """Restarts the current Quarter 3 level."""
        self.main_menu.quarter3 = None
        self.cleanup()
        from screens.quarter3 import Quarter3
        self.main_menu.quarter3 = Quarter3(self.screen, self.main_menu, self.map_name)

    def finish_and_return_to_hub(self):
        """Callback invoked by Victory Report Card to transition back to stage select."""
        self.return_to_stage_select(completed=True)

    # ============================================================
    # CHECK PORTAL TELEPORT
    # ============================================================
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
            is_goal_portal = (current_portal.direction == self.goal_portal_direction or current_portal.is_static)
            if is_goal_portal:
                puzzle_cleared = (
                    getattr(self, 'fraction_match_solved', False)
                    or getattr(self, 'solar_array_puzzle_solved', False)
                    or getattr(self, 'fraction_bakery_solved', False)
                )
                if self.quiz_state == 6 and puzzle_cleared:
                    print("* Entering Desert Sun Portal - Initiating seamless warp transition...")
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("portal_transition")
                    self.warp_out_active = True
                    self.warp_out_timer = self.warp_out_duration
                    return True
                else:
                    self.caravan_upgrade_banner_text = "PORTAL SEALED!"
                    self.caravan_upgrade_banner_sub = "Speak with the Skeleton Guardian to solve the Sun Fraction Match!"
                    self.caravan_upgrade_banner_timer = 4.0
                    if getattr(self, 'guardian_skeleton_state', 0) in [0, 1]:
                        self.guardian_skeleton_state = 2  # Open Skeleton Guardian trial prompt
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("incorrect")
                    self.teleport_cooldown = 1.5
                    return False

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
        if hasattr(self, 'camera_pan_active') and self.camera_pan_active:
            # During cinematic drone camera pan, camera position is controlled by pan routine
            min_cam_x = 0
            max_cam_x = max(0, self.MAP_WIDTH - self.width / ZOOM)
            min_cam_y = 0
            max_cam_y = max(0, self.MAP_HEIGHT - self.height / ZOOM)
            self.camera_x = max(min_cam_x, min(self.camera_x, max_cam_x))
            self.camera_y = max(min_cam_y, min(self.camera_y, max_cam_y))
            return

        self.lol_camera.update(
            self.player_x,
            self.player_y,
            cursor_pos=self.cursor_pos,
            map_width=self.MAP_WIDTH,
            map_height=self.MAP_HEIGHT,
            tile_size=TILE_SIZE,
            enable_edge_scroll=False
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

    def submit_identification_answer(self):
        """Validates student's answer in Identification Question Mode"""
        q_data = self.quiz_questions[self.current_question_index]
        clean_input = self.ident_input_text.strip().lower().replace(" ", "")

        if not clean_input:
            self.wrong_feedback_msg = "Please type or tap an answer using the keypad first! "
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
            if getattr(self.main_menu, 'audio_manager', None):
                self.main_menu.audio_manager.play_sfx("correct")
                self.main_menu.audio_manager.play_sfx("star_chime")
            if hasattr(self, 'celebration_particles'):
                self.celebration_particles.spawn_burst(self.width // 2, self.height // 2, count=30)
            if self.success_sound:
                self.success_sound.play()
            print(f"[OK] Correct identification answer submitted: {self.ident_input_text}")
        else:
            if hasattr(self, 'first_attempt_correct') and (self.current_question_index + 1) in self.first_attempt_correct:
                self.first_attempt_correct[self.current_question_index + 1] = False
            
            self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
            if getattr(self.main_menu, 'audio_manager', None):
                self.main_menu.audio_manager.play_sfx("wrong")
            if self.station_attempts[self.quiz_station_index] < 2:
                self.quiz_state = 2
                print(f"[FAIL] Incorrect identification answer submitted: {self.ident_input_text} (Attempt 1 of 2)")
            else:
                self.quiz_state = 4
                print(f"[FAIL] Incorrect identification on 2nd try! Out of tries. Station {self.quiz_station_index} cleared for progression.")
                
            if self.snap_sound:
                self.snap_sound.play()
            self.wrong_feedback_msg = f"Almost there! Check the visual model ({q_data.get('hint', '')}) and try again!"
            print(f"[FAIL] Incorrect identification answer: '{self.ident_input_text}'. Expected one of: {valid_answers}")
            
        from db.save_system import save_student_progress
        save_student_progress(self.main_menu)

    def advance_station_progress(self):
        """Executes guaranteed reward & station progression after answering or out-of-tries"""
        self.eliminated_choices.clear()
        self.wrong_feedback_msg = ""
        self.ident_input_text = ""
        self.speed_boost_timer = 3.0

        # Map 7 Reward: Load Cargo onto Explorer's Caravan
        if self.is_caravan_mode and self.quiz_station_index in self.station_cargo_rewards:
            reward = self.station_cargo_rewards[self.quiz_station_index]
            self.caravan_cargo.append(reward)
            self.caravan_upgrade_banner_text = f"CARAVAN UPGRADE: {reward['name']} Loaded!"
            self.caravan_upgrade_banner_sub = f"Speed Rush Activated! {reward['desc']}"
            self.caravan_upgrade_banner_timer = 3.0
            self.speed_boost_timer = 3.0  # 3 seconds of speed sprint!

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
            print(f"[CAMEL] Caravan Upgraded! Loaded {reward['name']} (Total Cargo: {len(self.caravan_cargo)}/5)")

        # Map 9 Reward: Unlock Sacred Math Keystone
        elif self.is_puzzle_hybrid_mode and self.quiz_station_index in self.citadel_keystones:
            st_num = self.quiz_station_index
            keystone = self.citadel_keystones[st_num]
            self.citadel_collected_keystones.append(keystone)
            self.citadel_banner_text = f"SUN KEYSTONE {st_num}/5 UNLOCKED!"
            self.citadel_banner_sub = f"{keystone['name']} ({keystone['math']}) slotted into Citadel Altar!"
            self.citadel_banner_timer = 3.0
            self.speed_boost_timer = 3.0

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
            print(f"Citadel Keystone {st_num} Acquired: {keystone['name']}")

        elif self.map_name == "map8.txt":
            self.speed_boost_timer = 3.0

        # In-World Bridge Construction and Camera Pan for Map 8 (scaled proportionally to 1..N cloud stations)
        tot_st = getattr(self, 'active_station_count', len(self.quiz_questions))
        st_num = self.quiz_station_index
        if hasattr(self, 'bridge_tiles') and self.bridge_tiles and tot_st > 0:
            target_bridges = max(1, min(len(self.bridge_tiles), int(round(st_num * len(self.bridge_tiles) / float(tot_st)))))
            if target_bridges > self.built_bridge_count:
                last_bx, last_by = self.bridge_tiles[target_bridges - 1]
                for b_idx in range(self.built_bridge_count, target_bridges):
                    bx, by = self.bridge_tiles[b_idx]
                    if by < len(self.game_map) and bx < len(self.game_map[by]):
                        self.game_map[by] = self.game_map[by][:bx] + "B" + self.game_map[by][bx+1:]
                        self.render_map[by] = self.render_map[by][:bx] + "B" + self.render_map[by][bx+1:]
                self.built_bridge_count = target_bridges
                self.build_prerendered_map()

                # Initiate Cinematic Drone Camera Pan
                self.camera_pan_active = True
                self.camera_pan_timer = 0.0
                self.camera_pan_duration = 2.4
                self.camera_pan_burst_done = False
                self.camera_pan_target_col = last_bx
                self.camera_pan_target_row = last_by
                self.camera_pan_origin_x = self.camera_x
                self.camera_pan_origin_y = self.camera_y

                t_cx = (last_bx * TILE_SIZE + TILE_SIZE // 2) - (self.width // 2) / ZOOM
                t_cy = (last_by * TILE_SIZE + TILE_SIZE // 2) - (self.height // 2) / ZOOM
                min_cam_x, max_cam_x = 0, max(0, self.MAP_WIDTH - self.width / ZOOM)
                min_cam_y, max_cam_y = 0, max(0, self.MAP_HEIGHT - self.height / ZOOM)
                self.camera_pan_dest_x = max(min_cam_x, min(t_cx, max_cam_x))
                self.camera_pan_dest_y = max(min_cam_y, min(t_cy, max_cam_y))

                self.quiz_state = 7  # State 7: Camera Pan sequence
                print(f"[BRIDGE] Aqueduct Bridge Segment {target_bridges}/{len(self.bridge_tiles)} materialized at ({last_bx}, {last_by})! Camera panning...")
                return

        if self.quiz_station_index < tot_st:
            self.quiz_station_index += 1
            self.current_question_index += 1
            self.quiz_state = 0
            print(f"[OK] Advanced to Quiz Station {self.quiz_station_index}")
        else:
            self.quiz_station_index = 6
            self.current_question_index = tot_st
            self.guardian_skeleton_state = 1
            self.quiz_state = 0
            if self.is_caravan_mode:
                self.caravan_x = self.player_x
                self.caravan_y = self.player_y
                self.caravan_dir = self.player_dir
                self.speed_boost_timer = 999.0
            self.caravan_upgrade_banner_text = f"ALL {tot_st} STATION(S) SOLVED!"
            self.caravan_upgrade_banner_sub = "Speak with the Skeleton Guardian to begin the Sun Fraction Match!"
            self.caravan_upgrade_banner_timer = 6.0
            print(f"[GUARDIAN] All {tot_st} station(s) solved! Skeleton Guardian activated at the exit portal!")

    def trigger_click(self, pos):
        self.sync_ui_state()
        from core.state_machine import State

        # 3-Star Victory Report Card Click Interactions (Replay Game / Continue to Hub)
        if hasattr(self, 'victory_card') and getattr(self.victory_card, 'active', False):
            res = self.victory_card.handle_click(pos)
            if res:
                return

        if self.pause_menu.handle_click(pos):
            return

        if self.state_machine.current_state == State.CognitivePuzzle:
            # Sun Temple Fraction Match Click Interactions
            if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'guardian_skeleton_state', 0) == 3:
                self.cursor_pos = pos
                handled = self.handle_fraction_match_mouse_down(pos)
                if handled and getattr(self, 'dragged_fraction_piece', None):
                    self.release_dragged_fraction_piece()
                return
            return

        if getattr(self, 'time_up_dialog_active', False):
            box_w, box_h = 700, 320
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            retry_rect = pygame.Rect(box_x + 50, box_y + 225, 270, 52)
            exit_rect = pygame.Rect(box_x + box_w - 320, box_y + 225, 270, 52)
            if retry_rect.collidepoint(pos):
                self.stage_time_remaining = 600.0
                self.time_up_dialog_active = False
                from screens.quarter3 import Quarter3
                self.main_menu.quarter3 = Quarter3(self.screen, self.main_menu, self.map_name)
                return
            elif exit_rect.collidepoint(pos):
                self.time_up_dialog_active = False
                from screens.stageselect import StageSelect
                self.main_menu.current_screen = "stage_select"
                self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
                self.main_menu.quarter3 = None
                return
            return

        # Sun Temple Fraction Match Click Interactions
        if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'guardian_skeleton_state', 0) == 3:
            if self.handle_fraction_match_mouse_down(pos):
                return
            return

        # Check Instruction Modal interaction
        if getattr(self, 'instruction_modal', None) and self.instruction_modal.is_visible:
            if self.instruction_modal.handle_click(pos):
                return
            return

        # Check HUD Guide Button click to re-open instructions
        if getattr(self, 'guide_btn_rect', None) and self.guide_btn_rect.collidepoint(pos):
            map_instr = get_map_instructions(self.map_name, self.player_name)
            self.instruction_modal.show(map_instr)
            return

        # Check NPC Greeting Dialog interaction
        if self.quiz_state == 0 and getattr(self, 'greeting_dialog', None) and self.greeting_dialog.is_visible:
            if self.greeting_dialog.handle_click(pos):
                self.greeting_dialog.hide()
                self.quiz_state = 1
                self.current_question_index = self.quiz_station_index - 1
                self.selected_choice_index = -1
                self.eliminated_choices.clear()
                self.station_attempts[self.quiz_station_index] = 0
                self.wrong_feedback_msg = ""
                self.ident_input_text = ""
                return
            return

        # Skeleton Guardian Trial Prompt Click Interaction
        if self.guardian_skeleton_state == 2:
            if getattr(self, 'guardian_skeleton_btn_rect', None) and self.guardian_skeleton_btn_rect.collidepoint(pos):
                self.guardian_skeleton_state = 3
                self.solar_array_puzzle_active = True
                self.init_solar_array_puzzle()
                if getattr(self.main_menu, 'audio_manager', None):
                    self.main_menu.audio_manager.play_sfx("portal_transition")
                return
            if getattr(self, 'guardian_skeleton_close_btn_rect', None) and self.guardian_skeleton_close_btn_rect.collidepoint(pos):
                self.guardian_skeleton_state = 1 if self.quiz_station_index >= 6 else 0
                self.guardian_skeleton_proximity_cooldown = 4.0
                return
            if getattr(self, 'guardian_skeleton_x_btn_rect', None) and self.guardian_skeleton_x_btn_rect.collidepoint(pos):
                self.guardian_skeleton_state = 1 if self.quiz_station_index >= 6 else 0
                self.guardian_skeleton_proximity_cooldown = 4.0
                return

        # Check clicking directly on the Skeleton Guardian sprite to talk
        if getattr(self, 'npc_skeleton_found', False) and not getattr(self, 'solar_array_puzzle_active', False):
            sx_screen = (self.npc_skeleton_x - self.camera_x) * ZOOM
            sy_screen = (self.npc_skeleton_y - self.camera_y) * ZOOM
            s_rect = pygame.Rect(sx_screen, sy_screen, TILE_SIZE * ZOOM, TILE_SIZE * ZOOM).inflate(36, 36)
            if s_rect.collidepoint(pos):
                self.guardian_skeleton_state = 2
                box_w = min(860, self.width - 40)
                box_h = 370
                box_x = (self.width - box_w) // 2
                box_y = (self.height - box_h) // 2
                diag_x = box_x + 24 + 140 + 24
                self.guardian_skeleton_btn_rect = pygame.Rect(diag_x, box_y + box_h - 76, 380, 52)
                self.guardian_skeleton_close_btn_rect = pygame.Rect(diag_x + 380 + 16, box_y + box_h - 76, 190, 52)
                self.guardian_skeleton_x_btn_rect = pygame.Rect(box_x + box_w - 38, box_y + 8, 28, 28)
                if getattr(self.main_menu, 'audio_manager', None):
                    self.main_menu.audio_manager.play_sfx("correct")
                return


        from db.save_system import save_student_progress
        
        # State 1: Multiple Choice Answer Selection (No icons)
        if self.quiz_state == 1:
            q_idx = max(0, min(self.current_question_index, len(self.quiz_questions) - 1)) if self.quiz_questions else 0
            q_data = self.quiz_questions[q_idx] if self.quiz_questions else {"question": "", "choices": [], "correct": 0}
            clicked_idx = self.quiz_dialog.get_clicked_choice(pos, self.eliminated_choices)

            if clicked_idx is not None and clicked_idx < len(q_data["choices"]):
                i = clicked_idx
                if i == q_data["correct"]:
                    self.current_correct_phrase = random.choice(self.correct_phrases)
                    self.quiz_state = 3
                    self.eliminated_choices.clear()
                    self.wrong_feedback_msg = ""
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("correct")
                        self.main_menu.audio_manager.play_sfx("star_chime")
                    if hasattr(self, 'celebration_particles'):
                        self.celebration_particles.spawn_burst(self.width // 2, self.height // 2, count=30)
                    if self.success_sound:
                        self.success_sound.play()
                    print(f"[OK] Correct answer selected: {q_data['choices'][i]}")
                else:
                    # 50:50 Wizard Hint: eliminate the clicked wrong choice and give gentle encouragement
                    self.eliminated_choices.add(i)
                    self.wrong_feedback_msg = "Almost there! Try picking again! "
                    if hasattr(self, 'first_attempt_correct') and (self.current_question_index + 1) in self.first_attempt_correct:
                        self.first_attempt_correct[self.current_question_index + 1] = False
                    
                    self.station_attempts[self.quiz_station_index] = self.station_attempts.get(self.quiz_station_index, 0) + 1
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("wrong")
                    if self.station_attempts[self.quiz_station_index] < 2:
                        self.quiz_state = 2
                        print(f"[FAIL] Incorrect choice selected: {q_data['choices'][i]} (Attempt 1 of 2)")
                    else:
                        self.quiz_state = 4
                        print(f"[FAIL] Incorrect choice on 2nd try! Out of tries. Station {self.quiz_station_index} cleared for progression.")
                    
                    if self.snap_sound:
                        self.snap_sound.play()
                save_student_progress(self.main_menu)
                    
        # State 2: Retry click fallback
        elif self.quiz_state == 2:
            box_w, box_h = 760, 360
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 280, 240, 50)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                save_student_progress(self.main_menu)
            
        # State 3: Correct answer transition screen click -> Award Cargo & Speed Rush!
        elif self.quiz_state == 3:
            box_w, box_h = 740, 330
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 245, 260, 50)
            if btn_rect.collidepoint(pos):
                self.advance_station_progress()
                save_student_progress(self.main_menu)

        # State 4: Out of tries reveal screen click -> Guaranteed progression without retrying!
        elif self.quiz_state == 4:
            box_w, box_h = 740, 340
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
            btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 260, 260, 50)
            if (hasattr(self, 'out_of_tries_btn_rect') and self.out_of_tries_btn_rect and self.out_of_tries_btn_rect.collidepoint(pos)) or btn_rect.collidepoint(pos) or box_rect.collidepoint(pos):
                self.station_attempts[self.quiz_station_index] = 0
                self.advance_station_progress()
                save_student_progress(self.main_menu)

        # State 5: Final speech click -> Direct player to the Skeleton Guardian!
        elif self.quiz_state == 5:
            box_w, box_h = 780, 420
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 340, 260, 50)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 0
                self.quiz_station_index = 6
                self.guardian_skeleton_state = 1
                self.caravan_riding = False
                if self.is_caravan_mode:
                    self.caravan_x = self.player_x
                    self.caravan_y = self.player_y
                    self.caravan_dir = self.player_dir
                    self.speed_boost_timer = 999.0
                self.caravan_upgrade_banner_text = "ALL 5 STATIONS SOLVED!"
                self.caravan_upgrade_banner_sub = "Speak with the Skeleton Guardian to begin the Sun Fraction Match!"
                self.caravan_upgrade_banner_timer = 6.0
                print("[GUARDIAN] Mentor dialogue cleared! Guided to Skeleton Guardian at the exit portal!")

        # Check Portal click or Click-to-Move when exploring the stage (only when no mini-game or puzzle is active)
        if self.state_machine.allows_movement() and self.quiz_state in [0, 6] and not self.is_minigame_or_puzzle_active():
            for portal in self.portals:
                screen_px = (portal.get_world_x() - self.camera_x) * ZOOM
                screen_py = (portal.get_world_y() - self.camera_y) * ZOOM
                pw = (portal.get_width_pixels() if hasattr(portal, 'get_width_pixels') else getattr(portal, 'width', TILE_SIZE)) * ZOOM
                ph = (portal.get_height_pixels() if hasattr(portal, 'get_height_pixels') else getattr(portal, 'height', TILE_SIZE)) * ZOOM
                portal_rect = pygame.Rect(screen_px, screen_py, pw, ph).inflate(24, 24)
                if portal_rect.collidepoint(pos):
                    self.click_dest = (portal.get_center_x() - TILE_SIZE // 2, portal.get_center_y() - TILE_SIZE // 2)
                    self.check_portal_teleport_on_hold()
                    return

            world_x = pos[0] / ZOOM + self.camera_x
            world_y = pos[1] / ZOOM + self.camera_y
            if self.can_move(world_x, world_y):
                self.click_dest = (world_x, world_y)
                return

    def handle_click(self, pos):
        """Standardized interface for clicking events, redirects to trigger_click"""
        return self.trigger_click(pos)

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = min(0.05, max(0.001, self.clock.tick() / 1000.0))
        self.frame_counter += 1

        self.sync_ui_state()

        if self.pause_menu.is_paused:
            return

        # If cognitive puzzle is active: world is paused & dimmed, stage timer is frozen
        if self.state_machine.is_world_paused():
            if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'guardian_skeleton_state', 0) == 3:
                self.update_solar_array_puzzle(dt)
            return

        # Update celebration particles & victory report card
        if hasattr(self, 'celebration_particles'):
            self.celebration_particles.update(dt)
        if hasattr(self, 'dust_particles'):
            self.dust_particles.update(dt)
        if hasattr(self, 'victory_card') and self.victory_card.active:
            self.victory_card.update(dt)
            return

        # Handle smooth warp-out transition to stage select
        if self.warp_out_active:
            self.warp_out_timer -= dt
            if self.warp_out_timer <= 0:
                self.warp_out_active = False
                self.save_results_to_database()
                total_questions = getattr(self, 'active_station_count', len(self.quiz_questions))
                correct_answers = sum(1 for k, v in self.first_attempt_correct.items() if k <= total_questions and v)
                percentage = (correct_answers / float(total_questions)) * 100.0 if total_questions > 0 else 100.0
                score = int(round(percentage)) if total_questions > 0 else 100
                from db.save_system import mark_quarter_completed
                mark_quarter_completed(self.main_menu, "quarter3", score=score, percentage=percentage, total_questions=total_questions)
                self.victory_card.show(total_questions=total_questions, correct_first_try=correct_answers, score=score)
            return

        # 10-Minute Stage Timer
        if not getattr(self, 'completed', False) and not self.time_up_dialog_active:
            self.stage_time_remaining = max(0.0, self.stage_time_remaining - dt)
            if self.stage_time_remaining <= 60.0 and not getattr(self, 'timer_warning_played', False):
                self.timer_warning_played = True
                if getattr(self.main_menu, 'audio_manager', None):
                    self.main_menu.audio_manager.play_sfx("timer_warning")
            if self.stage_time_remaining <= 0.0:
                self.stage_time_remaining = 0.0
                self.time_up_dialog_active = True
                print("[TIME] Quarter 3 Time's Up!")

        if self.time_up_dialog_active:
            return

        # Update Pathfinder Visual Guide Trail
        if hasattr(self, 'path_guide'):
            self.path_guide.update(dt)

        # Update animations for all 5 Shape Station NPCs
        if hasattr(self, 'station_npcs'):
            for num, data in self.station_npcs.items():
                data["anim_timer"] += 1
                if data["anim_timer"] >= 14:
                    data["anim_timer"] = 0
                    data["anim_frame"] = (data["anim_frame"] + 1) % len(data["frames"])

        if hasattr(self, 'player_block_timer') and self.player_block_timer > 0:
            self.player_block_timer -= dt

        # Update Area Title animation elapsed time
        if self.title_active:
            self.title_elapsed += dt
            if self.title_elapsed >= self.title_duration:
                self.title_active = False


        # Update Instruction Modal & handle Fist Hold dismiss
        if getattr(self, 'instruction_modal', None) and self.instruction_modal.is_visible:
            fist_pct = 0.0
            is_fist = (getattr(self, 'current_gesture', '') == "FIST") or getattr(self, 'fist_closed', False)
            if is_fist and getattr(self, 'fist_start_time', 0) > 0:
                elapsed = time.time() - self.fist_start_time
                fist_pct = min(1.0, elapsed / self.CLICK_HOLD_TIME)
                if elapsed >= self.CLICK_HOLD_TIME:
                    self.instruction_modal.hide()
                    self.fist_start_time = 0
                    if hasattr(self, 'sync_ui_state'):
                        self.sync_ui_state()
            self.instruction_modal.update(dt, self.cursor_pos, fist_pct)
            return

        # Update NPC Greeting Dialog & handle Fist Hold to start question
        if getattr(self, 'greeting_dialog', None) and self.greeting_dialog.is_visible:
            if hasattr(self, 'quiz_stations') and self.quiz_station_index in self.quiz_stations:
                st_x, st_y = self.quiz_stations[self.quiz_station_index]
                npc_cx = st_x * TILE_SIZE + TILE_SIZE // 2
                npc_cy = st_y * TILE_SIZE + TILE_SIZE // 2
                dist_away = math.hypot((self.player_x + TILE_SIZE // 2) - npc_cx, (self.player_y + TILE_SIZE // 2) - npc_cy)
                if dist_away > TILE_SIZE * 2.5:
                    self.greeting_dialog.hide()

            fist_pct = 0.0
            if self.fist_closed and self.fist_start_time > 0:
                elapsed = time.time() - self.fist_start_time
                fist_pct = min(1.0, elapsed / self.CLICK_HOLD_TIME)
                if elapsed >= self.CLICK_HOLD_TIME:
                    self.greeting_dialog.hide()
                    self.quiz_state = 1
                    self.current_question_index = self.quiz_station_index - 1
                    self.selected_choice_index = -1
                    self.eliminated_choices.clear()
                    self.wrong_feedback_msg = ""
                    self.ident_input_text = ""
                    self.fist_start_time = 0
            self.greeting_dialog.update(dt, self.cursor_pos, fist_pct)
            return

        # Proximity interaction check for active Station NPC
        if self.quiz_state == 0 and hasattr(self, 'quiz_stations') and self.quiz_station_index in self.quiz_stations:
            st_x, st_y = self.quiz_stations[self.quiz_station_index]
            npc_center_x = st_x * TILE_SIZE + TILE_SIZE // 2
            npc_center_y = st_y * TILE_SIZE + TILE_SIZE // 2
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            dist = math.hypot(player_center_x - npc_center_x, player_center_y - npc_center_y)
            if dist < TILE_SIZE * 1.8:
                if not self.greeting_dialog.is_visible and not self.instruction_modal.is_visible:
                    script = get_station_script(self.map_name, self.quiz_station_index)
                    speaker_name = script.get("npc_name", f"Sage {self.quiz_station_index}")
                    speaker_title = script.get("npc_title", f"Station {self.quiz_station_index}")
                    greeting_text = script.get("greeting", "Greetings, traveler!").replace("[Player Name]", self.player_name)
                    
                    sprite_frame = None
                    if hasattr(self, 'station_npcs') and self.quiz_station_index in self.station_npcs:
                        st_data = self.station_npcs[self.quiz_station_index]
                        if st_data.get("frames"):
                            anim_idx = st_data.get("anim_frame", 0) % len(st_data["frames"])
                            sprite_frame = st_data["frames"][anim_idx]
                            
                    self.greeting_dialog.show(speaker_name, speaker_title, greeting_text, sprite_frame=sprite_frame)

        # Proximity interaction check for Skeleton Guardian
        if getattr(self, 'npc_skeleton_found', False):
            skel_center_x = self.npc_skeleton_x + TILE_SIZE // 2
            skel_center_y = self.npc_skeleton_y + TILE_SIZE // 2
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            dist_skel = math.hypot(player_center_x - skel_center_x, player_center_y - skel_center_y)

            # Proximity prompt trigger when all 5 stations cleared
            if self.guardian_skeleton_state == 1 and self.quiz_station_index >= 6:
                if getattr(self, 'guardian_skeleton_proximity_cooldown', 0) > 0:
                    self.guardian_skeleton_proximity_cooldown -= dt
                elif dist_skel < TILE_SIZE * 3.2:
                    if not self.greeting_dialog.is_visible and not self.instruction_modal.is_visible:
                        self.guardian_skeleton_state = 2  # Open Guardian Trial Prompt modal
                        if getattr(self.main_menu, 'audio_manager', None):
                            self.main_menu.audio_manager.play_sfx("correct")

            # Smooth auto-dismiss if player walks far away while dialogue is open
            if self.guardian_skeleton_state == 2 and dist_skel > TILE_SIZE * 4.2:
                self.guardian_skeleton_state = 1 if self.quiz_station_index >= 6 else 0

            # MediaPipe Closed Fist Hold on Skeleton Guardian to talk in free roam
            if self.quiz_state == 0 and self.guardian_skeleton_state in [0, 1] and not getattr(self, 'solar_array_puzzle_active', False):
                sx_screen = (self.npc_skeleton_x - self.camera_x) * ZOOM
                sy_screen = (self.npc_skeleton_y - self.camera_y) * ZOOM
                s_rect = pygame.Rect(sx_screen, sy_screen, TILE_SIZE * ZOOM, TILE_SIZE * ZOOM).inflate(36, 36)
                if s_rect.collidepoint(self.cursor_pos) and self.fist_closed and self.fist_start_time > 0:
                    elapsed = time.time() - self.fist_start_time
                    if elapsed >= self.CLICK_HOLD_TIME:
                        self.fist_start_time = 0
                        self.guardian_skeleton_state = 2
                        if getattr(self.main_menu, 'audio_manager', None):
                            self.main_menu.audio_manager.play_sfx("correct")

        # MediaPipe Closed Fist Hold to start trial when talking to Skeleton Guardian
        if self.guardian_skeleton_state == 2:
            fist_pct = 0.0
            if self.fist_closed and self.fist_start_time > 0:
                elapsed = time.time() - self.fist_start_time
                fist_pct = min(1.0, elapsed / self.CLICK_HOLD_TIME)
                if elapsed >= self.CLICK_HOLD_TIME:
                    self.fist_start_time = 0
                    self.guardian_skeleton_state = 3
                    self.solar_array_puzzle_active = True
                    self.init_solar_array_puzzle()
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("portal_transition")
                    return
            self.guardian_fist_pct = fist_pct

        # Update Solar Array Keystone Math Puzzle
        if self.solar_array_puzzle_active or self.guardian_skeleton_state == 3:
            self.update_solar_array_puzzle(dt)

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
                tot_st = getattr(self, 'active_station_count', len(self.quiz_questions))
                self.camera_pan_active = False
                if self.quiz_station_index < tot_st:
                    self.quiz_station_index += 1
                    self.current_question_index += 1
                    self.quiz_state = 0
                else:
                    self.quiz_station_index = 6
                    self.current_question_index = tot_st
                    self.guardian_skeleton_state = 1
                    self.quiz_state = 0
                    if self.is_caravan_mode:
                        self.caravan_x = self.player_x
                        self.caravan_y = self.player_y
                        self.caravan_dir = self.player_dir
                        self.speed_boost_timer = 999.0
                    self.caravan_upgrade_banner_text = f"ALL {tot_st} STATION(S) SOLVED!"
                    self.caravan_upgrade_banner_sub = "Speak with the Skeleton Guardian to begin the Sun Fraction Match!"
                    self.caravan_upgrade_banner_timer = 6.0
                    if self.map_name == "map8.txt":
                        self.relic_banner_text = "GOLDEN CAUSEWAY COMPLETE!"
                        self.relic_banner_sub = "Cross the causeway to meet the Skeleton Guardian at the Sun Portal!"
                        self.relic_banner_timer = 5.0
                    print("[GUARDIAN] Camera pan complete! Skeleton Guardian activated at the exit portal!")

        if self.caravan_upgrade_banner_timer > 0:
            self.caravan_upgrade_banner_timer -= dt
            if self.caravan_upgrade_banner_timer <= 0:
                self.caravan_upgrade_banner_text = ""

        if self.citadel_banner_timer > 0:
            self.citadel_banner_timer -= dt
            if self.citadel_banner_timer <= 0:
                self.citadel_banner_text = ""

        # Update Speed Boost & Wind Sprites
        if self.speed_boost_timer > 0 and self.quiz_state in [0, 5, 6] and not getattr(self, 'camera_pan_active', False):
            self.speed_boost_timer = max(0.0, self.speed_boost_timer - dt)
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
        if self.is_caravan_mode and len(self.caravan_cargo) > 0 and random.random() < 0.04:
            self.caravan_music_notes.append({
                "x": self.caravan_x + random.randint(8, 24),
                "y": self.caravan_y - 6,
                "vx": random.uniform(-0.6, 0.6),
                "vy": -1.2,
                "kind": random.choice(["note", "sparkle"]),
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

        if self.is_caravan_mode:
            if self.quiz_state >= 5 or len(self.caravan_cargo) >= 5:
                # Player is riding inside the caravan!
                self.caravan_x = self.player_x
                self.caravan_y = self.player_y
                self.caravan_dir = self.player_dir
                if self.anim_frame > 0:
                    self.caravan_wheel_rot += 0.35
                    self.caravan_bob_timer += 0.25
                else:
                    self.caravan_bob_timer += 0.05
            else:
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
    # CHECK MINI-GAME / PUZZLE ACTIVE STATUS
    # ============================================================
    def is_minigame_or_puzzle_active(self):
        """Returns True if the player is currently playing a mini-game, puzzle, or interacting with a quiz/modal."""
        # 1. Hands-on mini-games and math puzzles in Quarter 3
        if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'guardian_skeleton_state', 0) in [2, 3]:
            return True
        if getattr(self, 'mini_puzzle_active', False):
            return True
        if getattr(self, 'dragged_fraction_piece', None) is not None or getattr(self, 'dragged_solar_piece', None) is not None:
            return True
        # 2. Quizzes, dialogues, modals, and camera pans
        if getattr(self, 'quiz_state', 0) in [1, 2, 3, 4, 5, 7]:
            return True
        if getattr(self, 'camera_pan_active', False):
            return True
        if getattr(self, 'quiz_dialog', None) and getattr(self.quiz_dialog, 'is_active', False):
            return True
        if getattr(self, 'instruction_modal', None) and getattr(self.instruction_modal, 'is_visible', False):
            return True
        if getattr(self, 'greeting_dialog', None) and getattr(self.greeting_dialog, 'is_visible', False):
            return True
        if getattr(self, 'time_up_dialog_active', False):
            return True
        if getattr(self, 'victory_card', None) and getattr(self.victory_card, 'active', False):
            return True
        if getattr(self, 'pause_menu', None) and getattr(self.pause_menu, 'is_paused', False):
            return True
        return False

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        # Freeze player and reset walking animation whenever inside a mini-game, puzzle, quiz, or dialog
        if not self.state_machine.allows_movement() or self.caravan_riding or self.is_minigame_or_puzzle_active() or (hasattr(self, 'player_block_timer') and self.player_block_timer > 0):
            self.click_dest = None
            self.anim_frame = 0
            self.anim_timer = 0
            return

        vx, vy = 0, 0
        base_speed = SPEED * (1.65 if self.speed_boost_timer > 0 else 1.0)

        # 1. Keyboard Controls Fallback
        keys = pygame.key.get_pressed()
        has_key_input = (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d] or
                         keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s])
        if has_key_input:
            self.click_dest = None
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                vx = -base_speed
                self.player_dir = "left"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                vx = base_speed
                self.player_dir = "right"
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                vy = -base_speed
                self.player_dir = "up"
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                vy = base_speed
                self.player_dir = "down"

        # 2. Click-to-Move Destination
        elif getattr(self, 'click_dest', None) is not None:
            cdx = self.click_dest[0] - self.player_x
            cdy = self.click_dest[1] - self.player_y
            cd_dist = math.hypot(cdx, cdy)
            if cd_dist > 6.0:
                vx = (cdx / cd_dist) * base_speed
                vy = (cdy / cd_dist) * base_speed
                if abs(cdx) > abs(cdy):
                    self.player_dir = "right" if cdx > 0 else "left"
                else:
                    self.player_dir = "down" if cdy > 0 else "up"
            else:
                self.click_dest = None

        # 3. Universal Hand Gesture / Active Cursor Steering
        if getattr(self, 'click_dest', None) is None and not has_key_input:
            is_hand_active = getattr(self, 'hand_detected', False) and getattr(self, 'current_gesture', 'NO HAND') not in ['NO HAND', 'NO HAND (GRACE)']
            is_mouse_active = getattr(self.main_menu, 'mouse_active', False) if self.main_menu else False

            if is_hand_active or is_mouse_active:
                player_screen_x = (self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM
                player_screen_y = (self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM
                cursor_x, cursor_y = self.cursor_pos
                dx = cursor_x - player_screen_x
                dy = cursor_y - player_screen_y

                deadzone = 45.0
                max_offset = max(abs(dx), abs(dy))
                if max_offset > deadzone:
                    # Smoothly ramp walk speed from 1.0x at deadzone (45px) to 1.35x at comfortable camera reach (105px)
                    dist_factor = min(1.35, 1.0 + ((max_offset - deadzone) / 60.0) * 0.35)
                    g_speed = base_speed * dist_factor
                    if abs(dx) > deadzone:
                        vx = g_speed if dx > 0 else -g_speed
                    if abs(dy) > deadzone:
                        vy = g_speed if dy > 0 else -g_speed

                    if abs(dx) > abs(dy):
                        self.player_dir = "right" if dx > 0 else "left"
                    else:
                        self.player_dir = "down" if dy > 0 else "up"

        new_x = self.player_x + vx
        new_y = self.player_y + vy

        moved_x, moved_y = False, False
        if self.can_move(new_x, self.player_y):
            self.player_x = new_x
            moved_x = True
        if self.can_move(self.player_x, new_y):
            self.player_y = new_y
            moved_y = True

        if getattr(self, 'click_dest', None) is not None and (vx != 0 or vy != 0):
            if not moved_x and not moved_y:
                self.click_dest = None

        if vx != 0 or vy != 0:
            self.player_trail.append((self.player_x, self.player_y, self.player_dir))
            self.anim_timer += 1
            if hasattr(self, 'dust_particles') and self.anim_timer % 8 == 0:
                self.dust_particles.emit_footstep(
                    (self.player_x + TILE_SIZE // 2) * ZOOM,
                    (self.player_y + TILE_SIZE - 2) * ZOOM,
                    direction=self.player_dir,
                    speed_boost=getattr(self, 'speed_boost_timer', 0) > 0,
                    terrain_color=(230, 200, 140)
                )
            if self.anim_timer >= (10 if self.speed_boost_timer > 0 else 16):
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
                if getattr(self.main_menu, 'audio_manager', None):
                    self.main_menu.audio_manager.play_sfx("footstep_wood")
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
        # When in caravan mode and all questions are finished, player is drawn inside the caravan wagon cart in draw_caravan()
        if self.is_caravan_mode and (self.quiz_state >= 5 or len(self.caravan_cargo) >= 5):
            return

        screen_x = int((self.player_x - self.camera_x) * ZOOM)
        screen_y = int((self.player_y - self.camera_y) * ZOOM)

        # Draw footstep dust beneath player feet
        if hasattr(self, 'dust_particles'):
            self.dust_particles.draw(self.screen, camera_offset=(self.camera_x * ZOOM, self.camera_y * ZOOM))

        if -self.scaled_tile_size <= screen_x <= self.width + self.scaled_tile_size and \
           -self.scaled_tile_size <= screen_y <= self.height + self.scaled_tile_size:
            sprite = self.scaled_player_sprites[self.player_dir][self.anim_frame]
            self.screen.blit(sprite, (screen_x, screen_y))

    # ============================================================
    # DRAW
    # ============================================================
    def draw(self):
        self.draw_math_background()

        cam_px = int(self.camera_x * ZOOM)
        cam_py = int(self.camera_y * ZOOM)
        dest_x = max(0, -cam_px)
        dest_y = max(0, -cam_py)
        src_x = max(0, cam_px)
        src_y = max(0, cam_py)
        src_w = max(0, self.width - dest_x)
        src_h = max(0, self.height - dest_y)
        view_rect = pygame.Rect(src_x, src_y, src_w, src_h)

        # Draw pre-rendered desert ground & walls in a single C-level blit
        if getattr(self, '_bg_map_surface', None) is not None and src_w > 0 and src_h > 0:
            self.screen.blit(self._bg_map_surface, (dest_x, dest_y), view_rect)

        # Draw Hierarchy Pathfinder Visual Guide Trail
        if hasattr(self, 'path_guide'):
            self.path_guide.draw()

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
                    
                    # If this is the currently active station, draw pre-cached glowing interaction aura and beacon
                    if num == self.quiz_station_index and self.quiz_state == 0:
                        aura_idx = (self.frame_counter // 4) % len(self.cached_station_auras)
                        aura_surf = self.cached_station_auras[aura_idx]
                        cx = (pos[0] * TILE_SIZE + TILE_SIZE // 2 - self.camera_x) * ZOOM
                        cy = (pos[1] * TILE_SIZE + TILE_SIZE - self.camera_y) * ZOOM
                        self.screen.blit(aura_surf, (cx - aura_surf.get_width() // 2, cy - aura_surf.get_height() // 2))
                        draw_beacon_marker(self.screen, cx, (pos[1] * TILE_SIZE - self.camera_y) * ZOOM, color=(251, 191, 36), beacon_type="question", offset_y=int(-30 * ZOOM))

                    self.draw_npc_static(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, frame)

        # Draw Skeleton Portal Guardian
        self.draw_skeleton_guardian()
        if getattr(self, 'guardian_skeleton_state', 0) in [1, 2, 3] and getattr(self, 'skeleton_guardian_active', True) and getattr(self, 'npc_skeleton_found', False):
            draw_beacon_marker(self.screen, (self.npc_skeleton_x + TILE_SIZE // 2 - self.camera_x) * ZOOM, (self.npc_skeleton_y - self.camera_y) * ZOOM, color=(168, 85, 247), beacon_type="exclamation", offset_y=int(-35 * ZOOM))

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

        # Draw Click-to-Move Target Beacon
        if getattr(self, 'click_dest', None) is not None:
            cd_screen_x = int((self.click_dest[0] - self.camera_x + TILE_SIZE // 2) * ZOOM)
            cd_screen_y = int((self.click_dest[1] - self.camera_y + TILE_SIZE // 2) * ZOOM)
            pulse = math.sin(self.frame_counter * 0.2) * 3 + 8
            pygame.draw.circle(self.screen, (56, 189, 248), (cd_screen_x, cd_screen_y), int(pulse), 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (cd_screen_x, cd_screen_y), 3)

        # Draw pre-rendered tree and tumbleweed tiles in a single C-level blit
        if getattr(self, '_fg_trees_surface', None) is not None and src_w > 0 and src_h > 0:
            self.screen.blit(self._fg_trees_surface, (dest_x, dest_y), view_rect)

        self.draw_player()

        # Draw Sparkle Particles
        self.draw_caravan_sparkles()

        # Draw Activated Portals on top of map tiles & trees (no brick wall overlap)
        if self.quiz_state == 6:
            for portal in self.portals:
                portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height)

        # Draw Top HUD
        if self.map_name == "map8.txt":
            if self.relic_banner_timer > 0:
                self.draw_relic_stage_banner()
        elif self.is_puzzle_hybrid_mode:
            self.draw_citadel_hud()
            if self.citadel_banner_timer > 0:
                self.draw_citadel_banner()
        elif self.is_caravan_mode:
            # Draw Caravan Inventory HUD at top right
            self.draw_caravan_hud()

        # Draw Celebratory Upgrade Banner if active on any map
        if self.caravan_upgrade_banner_text and self.caravan_upgrade_banner_timer > 0:
            self.draw_caravan_upgrade_banner()

        # Draw Active Objective NPC Indicator and Off-Screen Compass Pointer
        self.draw_offscreen_compass_pointer()

        # Draw dim overlay for State.CognitivePuzzle before minigame UI
        if self.state_machine.should_dim_world():
            self.state_machine.render_dim_overlay(self.screen, alpha=160)

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

        # Draw Skeleton Guardian Prompt & Sun Temple Fraction Match modals
        if self.guardian_skeleton_state == 2:
            self.draw_skeleton_guardian_prompt()
        elif self.guardian_skeleton_state == 3 or self.fraction_match_active or self.solar_array_puzzle_active or self.fraction_bakery_active:
            self.draw_solar_array_puzzle()

        # Draw Area Title Animation (zero-copy composite wave)
        if self.title_active:
            draw_composite_title_wave(
                self.screen,
                self.title_letters,
                self.title_total_width,
                self.title_spacing,
                self.pixel_font_size,
                self.title_elapsed,
            )

        self.draw_ui()

        # Draw smooth seamless warp-out transition overlay
        if self.warp_out_active:
            progress = max(0.0, min(1.0, 1.0 - (self.warp_out_timer / self.warp_out_duration)))
            if not hasattr(self, '_warp_overlay_surf') or self._warp_overlay_surf.get_size() != (self.width, self.height):
                self._warp_overlay_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._warp_overlay_surf.fill((254, 240, 138, int(progress * 255)))
            center = (self.width // 2, self.height // 2)
            max_r = int(math.hypot(self.width, self.height) / 2)
            r = int(progress * max_r)
            if r > 0:
                pygame.draw.circle(self._warp_overlay_surf, (245, 158, 11, int((1.0 - progress) * 230)), center, r, max(3, int(10 * ZOOM)))
                pygame.draw.circle(self._warp_overlay_surf, (255, 255, 255, int((1.0 - progress) * 200)), center, max(1, r - 8), max(2, int(4 * ZOOM)))
            self.screen.blit(self._warp_overlay_surf, (0, 0))

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

        # Draw Greeting Dialog overlay
        if getattr(self, 'greeting_dialog', None):
            self.greeting_dialog.draw(self.cursor_pos)

        # Draw Instruction Modal overlay
        if getattr(self, 'instruction_modal', None):
            self.instruction_modal.draw(self.cursor_pos)

    # ============================================================
    # DRAW UI
    # ============================================================
    def draw_ui(self):
        # Draw HUD Guide Button
        if getattr(self, 'guide_btn_rect', None):
            hov = self.guide_btn_rect.collidepoint(self.cursor_pos)
            bg = (30, 41, 59) if not hov else (51, 65, 85)
            pygame.draw.rect(self.screen, bg, self.guide_btn_rect, border_radius=8)
            pygame.draw.rect(self.screen, (251, 191, 36) if hov else (203, 213, 225), self.guide_btn_rect, 2, border_radius=8)
            g_font = self.get_ui_font(12, bold=True)
            g_text = g_font.render("[?] Guide", True, (251, 191, 36) if hov else (255, 255, 255))
            self.screen.blit(g_text, g_text.get_rect(center=self.guide_btn_rect.center))

        # Draw 10-Minute Stage Timer HUD
        self.draw_stage_timer_hud()

        # Draw Time's Up modal dialog if timer expired
        if self.time_up_dialog_active:
            self.draw_time_up_dialog()

        # Draw Objectives HUD Box at the bottom center of the screen
        if self.is_quiz_map:
            box_w, box_h = 480, 80
            box_x = (self.width - box_w) // 2
            box_y = self.height - box_h - 20
            
            # Translucent slate blue background (alpha = 190)
            self.screen.blit(self.obj_hud_bg, (box_x, box_y))
            
            # Border: Gold when locked, Green when complete
            border_color = (218, 165, 32) if self.quiz_state < 6 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_color, (box_x, box_y, box_w, box_h), 2, border_radius=8)
            
            # Header title in Gold
            title_font = get_font("Comic Sans MS", 12, bold=True)
            title_surf = title_font.render("CURRENT OBJECTIVES", True, (255, 215, 0))
            self.screen.blit(title_surf, (box_x + 15, box_y + 8))
            
            # Details font
            item_font = get_font("Comic Sans MS", 12)
            
            tot_st = getattr(self, 'active_station_count', len(self.quiz_questions))
            if tot_st <= 0:
                obj1 = "- Cloud Questions: None Assigned (0 in Cloud)"
                obj1_color = (56, 189, 248)
            else:
                q_count = tot_st if self.quiz_station_index >= 6 else min(self.current_question_index, tot_st)
                obj1 = f"- Quiz Progress: {q_count}/{tot_st} questions answered"
                obj1_color = (255, 255, 255) if q_count < tot_st else (34, 197, 94)
            obj1_surf = item_font.render(obj1, True, obj1_color)
            self.screen.blit(obj1_surf, (box_x + 15, box_y + 28))
            
            # Goal portal state item
            if self.quiz_state < 6:
                if self.quiz_station_index >= 6:
                    obj2 = "- Visit Skeleton Guardian for Sun Fraction Match!"
                    obj2_color = (250, 204, 21)
                else:
                    obj2 = "- Portal Status: LOCKED"
                    obj2_color = (244, 63, 94)  # Rose
            else:
                obj2 = "- Portal Status: OPEN (Enter the portal to exit!)"
                obj2_color = (34, 197, 94)  # Green
            obj2_surf = item_font.render(obj2, True, obj2_color)
            self.screen.blit(obj2_surf, (box_x + 15, box_y + 48))

        if self.show_info:
            npc_status = []
            if self.npc_oldman_found:
                npc_status.append("Oldman")
            if self.npc_skeleton_found:
                npc_status.append("Skeleton")
            if self.npc_knight_found:
                npc_status.append("Knight")

            npc_text = ", ".join(npc_status) if npc_status else "None"

            info_lines = [
                f"Map: {self.map_name}",
                f"Goal: Reach the {self.goal_portal_direction} portal >> Return to town",
                f"Position: ({self.player_x // TILE_SIZE}, {self.player_y // TILE_SIZE})",
                f"Portals: {len(self.portals)}",
                f"NPCs: {npc_text}",
                f"Hand: {'YES' if self.hand_detected else 'NO'}",
                f"Gesture: {self.current_gesture}",
                f"Pause: Top-Right / Hold Fist"
            ]

            self.screen.blit(self.info_panel_bg, (6, 6))
            y_offset = 10
            for line in info_lines:
                text = self.small_font.render(line, True, (255, 255, 255))
                self.screen.blit(text, (12, y_offset))
                y_offset += 18

    # ============================================================
    # [QUEST] IN-WORLD RELIC HUNT & SHRINE ALTAR SYSTEM (MAP 8)
    # ============================================================
    def spawn_relic_stage(self, stage_num):
        """Spawns mathematical relic items in the desert maze for the given stage"""
        self.relic_items = []
        self.relic_collected_count = 0
        self.relic_stage_complete = False
        self.relic_stage = stage_num

        if stage_num == 1:
            # Stage 1: Multiplication Array (3 Rows x 4 Apples = 12)
            self.relic_target_count = 12
            self.relic_item_type = "apple"
            self.relic_quest_title = "STAGE 1 - THE GOLDEN ORCHARD TRIAL"
            self.relic_quest_math = "3 Rows x 4 Apples = 12 Total Apples"
            self.relic_quest_hint = "Gather all 12 Golden Apples and bring them to Shrine 1!"
            coords = [(46, 18), (45, 18), (44, 18), (43, 18), (42, 18), (41, 18), (40, 18), (39, 18), (38, 18), (37, 18), (36, 18), (35, 18)]
            glow = (239, 68, 68)

        elif stage_num == 2:
            # Stage 2: Repeated Addition (4 Groups of 2 = 8)
            self.relic_target_count = 8
            self.relic_item_type = "coconut"
            self.relic_quest_title = "STAGE 2 - THE REPEATED ADDITION TRAIL"
            self.relic_quest_math = "4 Groups of 2 Coconuts = 2 + 2 + 2 + 2 = 8"
            self.relic_quest_hint = "Gather 8 Coconuts along the oasis path and deliver to Shrine 2!"
            coords = [(32, 18), (30, 18), (28, 18), (26, 18), (23, 18), (21, 18), (19, 18), (17, 18)]
            glow = (180, 83, 9)

        elif stage_num == 3:
            # Stage 3: Equal Sharing Division (10 Coins / 2 Chests = 5)
            self.relic_target_count = 10
            self.relic_item_type = "coin"
            self.relic_quest_title = "STAGE 3 - EQUAL SHARING DIVISION"
            self.relic_quest_math = "10 Scarab Coins / 2 Chests = 5 Coins Each"
            self.relic_quest_hint = "Collect all 10 Golden Coins to split between the 2 Shrine Chests!"
            coords = [(14, 17), (14, 16), (13, 15), (11, 15), (10, 15), (9, 14), (9, 12), (9, 11), (7, 11), (5, 11)]
            glow = (234, 179, 8)

        elif stage_num == 4:
            # Stage 4: Unit Fraction One-Half (1 / 2)
            self.relic_target_count = 2
            self.relic_item_type = "sun_disk"
            self.relic_quest_title = "STAGE 4 - SACRED UNIT FRACTION (ONE-HALF)"
            self.relic_quest_math = "2 Halves (1/2 + 1/2) = 1 Whole Solar Disk"
            self.relic_quest_hint = "Gather both 2 Sun Disk Halves (1/2 each) and deliver to Shrine 4!"
            coords = [(3, 10), (4, 7)]
            glow = (245, 158, 11)

        elif stage_num == 5:
            # Stage 5: Unit Fraction One-Third (1 / 3)
            self.relic_target_count = 3
            self.relic_item_type = "ingot"
            self.relic_quest_title = "STAGE 5 - SACRED UNIT FRACTION (ONE-THIRD)"
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

        self.relic_banner_text = f"{self.relic_quest_title}"
        self.relic_banner_sub = self.relic_quest_math
        self.relic_banner_timer = 4.0
        print(f"[QUEST] Relic Stage {stage_num} spawned with {len(self.relic_items)} items!")

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
                        self.relic_banner_text = "ALL SUPPLIES GATHERED!"
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
        m_surf = self.dialog_hint_font.render(f"{self.relic_quest_math}", True, math_c)
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
        """Renders the companion camel/pony and upgradable cargo cart (with player seated inside after completing all questions)"""
        cx = int((self.caravan_x - self.camera_x) * ZOOM)
        cy = int((self.caravan_y - self.camera_y) * ZOOM)
        
        # Margin culling
        if not (-64 * ZOOM <= cx <= self.width + 64 * ZOOM and -64 * ZOOM <= cy <= self.height + 64 * ZOOM):
            return

        cart_sz = int(TILE_SIZE * ZOOM)
        bob = math.sin(self.caravan_bob_timer) * 3
        is_player_riding = (self.quiz_state >= 5 or len(self.caravan_cargo) >= 5)

        # 1. Soft ground contact shadow (Pre-rendered cache)
        self.screen.blit(self.caravan_shadow_surf, (cx + cart_sz // 2 - self.caravan_shadow_surf.get_width() // 2, cy + cart_sz - self.caravan_shadow_surf.get_height() // 2 + 2))

        # 2. Wooden Cart Base (Rich mahogany box)
        cart_rect = pygame.Rect(cx + 4, cy + 8 + int(bob), cart_sz - 8, cart_sz - 12)
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

        # 4. Visible Loaded Cargo inside the cart
        cargo_count = len(self.caravan_cargo)
        if cargo_count >= 1: # Apples
            pygame.draw.circle(self.screen, (239, 68, 68), (cart_rect.left + 6, cart_rect.centery - 2), 5)
            pygame.draw.circle(self.screen, (34, 197, 94), (cart_rect.left + 6, cart_rect.centery - 6), 2)
        if cargo_count >= 2: # Coconuts
            pygame.draw.circle(self.screen, (120, 53, 15), (cart_rect.right - 6, cart_rect.centery - 2), 5)
            pygame.draw.circle(self.screen, (180, 83, 9), (cart_rect.right - 6, cart_rect.centery - 2), 3)
        if cargo_count >= 3: # Golden Chest
            ch_box = pygame.Rect(cart_rect.left + 2, cart_rect.top + 2, 10, 8)
            pygame.draw.rect(self.screen, (245, 158, 11), ch_box, border_radius=2)
            pygame.draw.rect(self.screen, (255, 255, 255), ch_box, 1, border_radius=2)
        if cargo_count >= 4: # Pizza Feast
            pygame.draw.circle(self.screen, (217, 119, 6), (cart_rect.right - 6, cart_rect.top + 5), 5)
            pygame.draw.circle(self.screen, (239, 68, 68), (cart_rect.right - 6, cart_rect.top + 4), 2)
        if cargo_count >= 5: # Legendary Sun Relic Gem (atop canopy or radiant center)
            gem_pulse = math.sin(pygame.time.get_ticks() / 150) * 3
            pygame.draw.circle(self.screen, (168, 85, 247), (cart_rect.centerx, cart_rect.top - 18), int(8 + gem_pulse), 2)
            pygame.draw.circle(self.screen, (255, 215, 0), (cart_rect.centerx, cart_rect.top - 18), 5)

        # 5. PLAYER SPRITE SEATED INSIDE THE CARAVAN CART (When all questions completed!)
        if is_player_riding:
            p_sprite = self.scaled_player_sprites[self.player_dir][self.anim_frame]
            px = cx + (cart_sz - p_sprite.get_width()) // 2
            py = cy + int(bob) - int(6 * ZOOM)
            
            # Draw player sitting inside cart
            self.screen.blit(p_sprite, (px, py))

            # Draw Front Guard Rail & Brass Trim over bottom of cart to seat player inside cleanly
            front_rail_rect = pygame.Rect(cart_rect.left, cart_rect.centery + 2, cart_rect.width, cart_rect.height // 2)
            pygame.draw.rect(self.screen, (146, 64, 14), front_rail_rect, border_radius=3)
            pygame.draw.rect(self.screen, (245, 158, 11), front_rail_rect, 2, border_radius=3)
            
            # Gold rivets on wagon rim
            pygame.draw.circle(self.screen, (255, 215, 0), (front_rail_rect.left + 4, front_rail_rect.centery), 2)
            pygame.draw.circle(self.screen, (255, 215, 0), (front_rail_rect.centerx, front_rail_rect.centery), 2)
            pygame.draw.circle(self.screen, (255, 215, 0), (front_rail_rect.right - 4, front_rail_rect.centery), 2)

            # Golden Navigator Crown / Sparkles above the player
            crown_cx = px + p_sprite.get_width() // 2
            crown_cy = py - 4
            pts_crown = [
                (crown_cx - 8, crown_cy),
                (crown_cx - 6, crown_cy - 6),
                (crown_cx - 3, crown_cy - 2),
                (crown_cx, crown_cy - 8),
                (crown_cx + 3, crown_cy - 2),
                (crown_cx + 6, crown_cy - 6),
                (crown_cx + 8, crown_cy)
            ]
            pygame.draw.polygon(self.screen, (255, 215, 0), pts_crown)
            pygame.draw.polygon(self.screen, (255, 255, 255), pts_crown, 1)

        # 6. Canopy Pillars & Striped Silk Canopy / Roof
        pillar_h = 16
        pygame.draw.line(self.screen, (180, 83, 9), (cart_rect.left + 2, cart_rect.top), (cart_rect.left + 2, cart_rect.top - pillar_h), 2)
        pygame.draw.line(self.screen, (180, 83, 9), (cart_rect.right - 2, cart_rect.top), (cart_rect.right - 2, cart_rect.top - pillar_h), 2)

        canopy_rect = pygame.Rect(cart_rect.left - 4, cart_rect.top - pillar_h - 4, cart_rect.width + 8, 14)
        pygame.draw.rect(self.screen, (220, 38, 38), canopy_rect, border_radius=5)
        for st_i in range(0, canopy_rect.width, 8):
            pygame.draw.rect(self.screen, (245, 158, 11), (canopy_rect.left + st_i, canopy_rect.top, 4, canopy_rect.height))
        pygame.draw.rect(self.screen, (255, 215, 0), canopy_rect, 2, border_radius=5)

        # 7. Chibi Desert Companion (Camel/Pony Mascot in front pulling the cart)
        companion_offset_x = 22 if self.caravan_dir == "right" else (-22 if self.caravan_dir == "left" else 0)
        companion_offset_y = 18 if self.caravan_dir == "down" else (-18 if self.caravan_dir == "up" else 4)
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

        # 8. Happy Music Notes (Crisp geometric vector notes & stars - zero missing font boxes)
        for note in self.caravan_music_notes:
            n_x = int((note["x"] - self.camera_x) * ZOOM)
            n_y = int((note["y"] - self.camera_y) * ZOOM)
            col = note["color"]
            if note.get("kind") == "sparkle":
                pygame.draw.circle(self.screen, col, (n_x, n_y), 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (n_x, n_y), 1)
            else:
                pygame.draw.circle(self.screen, col, (n_x, n_y), 3)
                pygame.draw.line(self.screen, col, (n_x + 2, n_y), (n_x + 2, n_y - 7), 2)
                pygame.draw.line(self.screen, col, (n_x + 2, n_y - 7), (n_x + 6, n_y - 5), 2)

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
        """Draws celebratory gold banner when new cargo is loaded onto the caravan or trial is active"""
        t_surf = self.dialog_header_font.render(self.caravan_upgrade_banner_text, True, (255, 255, 255))
        sub_surf = self.dialog_stat_font.render(self.caravan_upgrade_banner_sub, True, (254, 240, 138))
        
        b_w = max(640, max(t_surf.get_width(), sub_surf.get_width()) + 50)
        b_h = 60
        b_x = (self.width - b_w) // 2
        b_y = 120
        b_rect = pygame.Rect(b_x, b_y, b_w, b_h)
        
        pygame.draw.rect(self.screen, (22, 163, 74), b_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), b_rect, 3, border_radius=12)
        
        self.screen.blit(t_surf, t_surf.get_rect(center=(b_rect.centerx, b_rect.top + 20)))
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
        status_txt = "SUN CITADEL ALTAR (5/5 READY!)" if c_count == 5 else f"SUN CITADEL KEYSTONES ({c_count}/5)"
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

    def complete_all_objectives_shortcut(self):
        """Cheat/Debug shortcut to complete stations, teleport to Skeleton Guardian, enable dialogue, and unlock portal."""
        print("[CHEAT] Quarter 3 Complete Objectives shortcut activated!")
        
        # Tier 2: If already talking to Skeleton Guardian or inside the Sun Temple Fraction Match, solve the puzzle & unlock portal
        if getattr(self, 'guardian_skeleton_state', 0) in [2, 3, 4] or getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False):
            self.fraction_match_solved = True
            self.fraction_bakery_solved = True
            self.solar_array_puzzle_solved = True
            self.fraction_match_all_placed = True
            self.solar_array_puzzle_all_placed = True
            self.fraction_match_active = False
            self.fraction_bakery_active = False
            self.solar_array_puzzle_active = False
            self.guardian_skeleton_state = 5  # Unlocked portal
            self.quiz_state = 6  # Ready for exit portal
            if hasattr(self, 'clear_portal_overlapping_tiles'):
                self.clear_portal_overlapping_tiles()
            self.caravan_upgrade_banner_text = "SUN FRACTION MATCH SOLVED!"
            self.caravan_upgrade_banner_sub = "Desert Sun Exit Portal is Unlocked!"
            self.caravan_upgrade_banner_timer = 5.0
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("victory_fanfare")
        else:
            # Tier 1: Complete stations 1-5, build world structures, teleport player directly to Skeleton Guardian, and open dialog
            self.quiz_station_index = 6
            self.current_question_index = 5
            if hasattr(self, 'station_npc_info'):
                for s in self.station_npc_info.values():
                    s["answered"] = True
            if hasattr(self, 'shape_npcs'):
                for s in self.shape_npcs.values():
                    s["answered"] = True
                    
            # Aqueduct bridge tiles on Map 8
            if "map8" in str(self.map_name).lower():
                bridge_locs = getattr(self, 'bridge_tiles', None) or [(40, 7), (41, 7), (42, 7), (43, 7), (44, 7)]
                for bx, by in bridge_locs:
                    if 0 <= by < len(self.render_map) and 0 <= bx < len(self.render_map[by]):
                        row = list(self.render_map[by])
                        row[bx] = 'B'
                        self.render_map[by] = ''.join(row)
                    if 0 <= by < len(self.game_map) and 0 <= bx < len(self.game_map[by]):
                        row = list(self.game_map[by])
                        row[bx] = 'B'
                        self.game_map[by] = ''.join(row)
                self.built_bridge_count = len(bridge_locs)
                self.build_prerendered_map()
                        
            # Keystones on Map 9
            if hasattr(self, 'keystones_collected'):
                self.keystones_collected = {1: True, 2: True, 3: True, 4: True, 5: True}
            if hasattr(self, 'relic_pieces_collected'):
                self.relic_pieces_collected = 5
                
            self.fraction_match_solved = False
            self.fraction_match_active = False
            self.fraction_bakery_solved = False
            self.fraction_bakery_active = False
            self.solar_array_puzzle_solved = False
            self.solar_array_puzzle_active = False
            self.player_block_timer = 0
            self.camera_pan_active = False
            self.ident_dialog_active = False
            self.ident_input_text = ""
            self.quiz_state = 0
            
            # Teleport player directly in front of the Skeleton Guardian
            if getattr(self, 'npc_skeleton_found', False):
                gx, gy = self.npc_skeleton_tile_x, self.npc_skeleton_tile_y
                candidates = [(gx - 1, gy), (gx + 1, gy), (gx, gy + 1), (gx, gy - 1), (gx - 2, gy), (gx + 2, gy)]
                placed = False
                for cx, cy in candidates:
                    if 0 <= cy < len(self.game_map) and 0 <= cx < len(self.game_map[cy]):
                        if self.game_map[cy][cx] in self.WALKABLE_TILES:
                            self.player_x = cx * TILE_SIZE
                            self.player_y = cy * TILE_SIZE
                            self.player_tile_x = cx
                            self.player_tile_y = cy
                            placed = True
                            break
                if not placed:
                    self.player_x = self.npc_skeleton_x
                    self.player_y = self.npc_skeleton_y
                    self.player_tile_x = self.npc_skeleton_tile_x
                    self.player_tile_y = self.npc_skeleton_tile_y

                if self.player_x < self.npc_skeleton_x:
                    self.player_dir = "right"
                    self.npc_skeleton_dir = "left"
                elif self.player_x > self.npc_skeleton_x:
                    self.player_dir = "left"
                    self.npc_skeleton_dir = "right"
                elif self.player_y < self.npc_skeleton_y:
                    self.player_dir = "down"
                    self.npc_skeleton_dir = "up"
                else:
                    self.player_dir = "up"
                    self.npc_skeleton_dir = "down"

                # Snap camera immediately
                self.camera_x = self.player_x - (self.width / (2 * ZOOM)) + TILE_SIZE / 2
                self.camera_y = self.player_y - (self.height / (2 * ZOOM)) + TILE_SIZE / 2
                if hasattr(self, 'lol_camera'):
                    self.lol_camera.camera_x = self.camera_x
                    self.lol_camera.camera_y = self.camera_y

            # Immediately open the Skeleton Guardian Dialogue & Trial Prompt modal
            self.guardian_skeleton_state = 2
            box_w = min(860, self.width - 40)
            box_h = 370
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            diag_x = box_x + 24 + 140 + 24
            self.guardian_skeleton_btn_rect = pygame.Rect(diag_x, box_y + box_h - 76, 380, 52)
            self.guardian_skeleton_close_btn_rect = pygame.Rect(diag_x + 380 + 16, box_y + box_h - 76, 190, 52)
            self.guardian_skeleton_x_btn_rect = pygame.Rect(box_x + box_w - 38, box_y + 8, 28, 28)
            
            self.caravan_upgrade_banner_text = "ALL 5 STATIONS SOLVED!"
            self.caravan_upgrade_banner_sub = "Skeleton Guardian Trial Ready! Press Space or Click to begin!"
            self.caravan_upgrade_banner_timer = 5.0
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("success")
        
        if hasattr(self, 'instruction_modal'):
            self.instruction_modal.hide()
        if hasattr(self, 'greeting_dialog'):
            self.greeting_dialog.hide()
        if hasattr(self, 'mentor_dialog'):
            self.mentor_dialog.hide()

    # ============================================================
    # HANDLE EVENT
    # ============================================================
    def handle_event(self, event):
        self.sync_ui_state()

        # Allow LoL camera to process middle mouse drag or Spacebar recentering only when permitted
        if self.state_machine.allows_camera_pan():
            self.lol_camera.handle_event(event)

        if hasattr(self, 'victory_card') and self.victory_card.active:
            if self.victory_card.handle_event(event):
                return "blocked"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                res = self.victory_card.handle_click(event.pos)
                if res:
                    return "blocked"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False):
                self.close_fraction_match_modal()
                return "handled"
            if getattr(self, 'guardian_skeleton_state', 0) == 2:
                self.guardian_skeleton_state = 1 if self.quiz_station_index >= 6 else 0
                self.guardian_skeleton_proximity_cooldown = 4.0
                return "handled"
        # In-game pause menu (universal across all states)
        if self.pause_menu.handle_event(event):
            return "blocked"

        if self.pause_menu.is_paused:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.cursor_pos = event.pos
                self.pause_menu.handle_click(event.pos)
                return "blocked"
            elif event.type == pygame.MOUSEMOTION:
                self.cursor_pos = event.pos
                return "blocked"
            return "blocked"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.pause_menu.pause_btn_rect.collidepoint(event.pos):
                self.cursor_pos = event.pos
                self.pause_menu.toggle_pause()
                return "blocked"
        if self.state_machine.current_state == State.CognitivePuzzle:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.cursor_pos = event.pos
                if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'guardian_skeleton_state', 0) == 3:
                    handled = self.handle_solar_array_mouse_down(event.pos)
                    if handled:
                        return "handled"
                self.trigger_click(event.pos)
                return "handled"
            elif event.type == pygame.MOUSEMOTION:
                if not getattr(self, 'hand_detected', False) or getattr(self, 'current_gesture', 'NO HAND') in ['NO HAND', 'NO HAND (GRACE)']:
                    self.cursor_pos = event.pos
                if (getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False)) and getattr(self, 'mouse_drag_active', False):
                    active_piece = getattr(self, 'dragged_fraction_piece', None) or getattr(self, 'dragged_solar_piece', None)
                    if active_piece is not None:
                        active_piece["x"] = event.pos[0] - getattr(self, 'fraction_drag_offset_x', getattr(self, 'solar_drag_offset_x', 0))
                        active_piece["y"] = event.pos[1] - getattr(self, 'fraction_drag_offset_y', getattr(self, 'solar_drag_offset_y', 0))
                return "handled"
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.cursor_pos = event.pos
                if (getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False)) and getattr(self, 'mouse_drag_active', False):
                    self.mouse_drag_active = False
                    self.release_dragged_solar_piece()
                    return "handled"
                return "handled"
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_F7, pygame.K_F10]:
                    if getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False):
                        self.auto_solve_solar_array_puzzle()
                    return "handled"
                if event.key in [pygame.K_c, pygame.K_o]:
                    self.complete_all_objectives_shortcut()
                    return "shortcut_complete"
                if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_e] and getattr(self, 'solar_array_puzzle_all_placed', False):
                    self.complete_fraction_match_trial()
                    return "handled"
                return "handled"
            return "handled"


        if event.type == pygame.KEYDOWN:
            combined_mod = pygame.key.get_mods() if hasattr(pygame.key, 'get_mods') else 0
            ctrl_pressed = bool(combined_mod & pygame.KMOD_CTRL)
            shift_pressed = bool(combined_mod & pygame.KMOD_SHIFT)

            pressed_keys = pygame.key.get_pressed() if hasattr(pygame.key, 'get_pressed') else None
            if pressed_keys is not None:
                if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
                    ctrl_pressed = True
                if pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]:
                    shift_pressed = True

            is_typing = (self.quiz_state == 1 and hasattr(self, 'quiz_questions') and 0 <= self.current_question_index < len(self.quiz_questions) and self.quiz_questions[self.current_question_index].get("q_type") == "identification")
            is_complete_shortcut = (
                event.key in [pygame.K_F7, pygame.K_F10]
                or ((ctrl_pressed or shift_pressed) and event.key in [pygame.K_c, pygame.K_o])
                or (not is_typing and event.key in [pygame.K_c, pygame.K_o])
            )
            if is_complete_shortcut:
                self.complete_all_objectives_shortcut()
                return "shortcut_complete"

            if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_e]:
                if getattr(self, 'instruction_modal', None) and self.instruction_modal.is_visible:
                    self.instruction_modal.hide()
                    return "handled"
                elif getattr(self, 'greeting_dialog', None) and self.greeting_dialog.is_visible:
                    self.greeting_dialog.hide()
                    self.quiz_state = 1
                    self.selected_choice_index = -1
                    self.eliminated_choices.clear()
                    self.wrong_feedback_msg = ""
                    self.current_question_index = self.quiz_station_index - 1
                    if getattr(self, 'coin_clink', None):
                        self.coin_clink.play()
                    return "handled"
                elif getattr(self, 'guardian_skeleton_state', 0) == 2:
                    self.guardian_skeleton_state = 3
                    self.solar_array_puzzle_active = True
                    self.init_solar_array_puzzle()
                    if getattr(self.main_menu, 'audio_manager', None):
                        self.main_menu.audio_manager.play_sfx("portal_transition")
                    return "handled"
                elif getattr(self, 'npc_skeleton_found', False) and not getattr(self, 'solar_array_puzzle_active', False):
                    skel_center_x = self.npc_skeleton_x + TILE_SIZE // 2
                    skel_center_y = self.npc_skeleton_y + TILE_SIZE // 2
                    player_center_x = self.player_x + TILE_SIZE // 2
                    player_center_y = self.player_y + TILE_SIZE // 2
                    if math.hypot(player_center_x - skel_center_x, player_center_y - skel_center_y) < TILE_SIZE * 3.5:
                        self.guardian_skeleton_state = 2
                        box_w = min(860, self.width - 40)
                        box_h = 370
                        box_x = (self.width - box_w) // 2
                        box_y = (self.height - box_h) // 2
                        diag_x = box_x + 24 + 140 + 24
                        self.guardian_skeleton_btn_rect = pygame.Rect(diag_x, box_y + box_h - 76, 380, 52)
                        self.guardian_skeleton_close_btn_rect = pygame.Rect(diag_x + 380 + 16, box_y + box_h - 76, 190, 52)
                        self.guardian_skeleton_x_btn_rect = pygame.Rect(box_x + box_w - 38, box_y + 8, 28, 28)
                        if getattr(self.main_menu, 'audio_manager', None):
                            self.main_menu.audio_manager.play_sfx("correct")
                        return "handled"
                elif (getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False)) and getattr(self, 'solar_array_puzzle_all_placed', False):
                    self.complete_fraction_match_trial()
                    return "handled"
                elif self.quiz_state == 2:
                    self.quiz_state = 1
                    save_student_progress(self.main_menu)
                    return "handled"
                elif self.quiz_state in [3, 4]:
                    self.station_attempts[self.quiz_station_index] = 0
                    self.advance_station_progress()
                    save_student_progress(self.main_menu)
                    return "handled"
                if self.quiz_state == 0:
                    self.lol_camera.recenter()
            elif event.key == pygame.K_ESCAPE:
                if self.quiz_state in [1, 2]:
                    self.quiz_state = 0
                    self.eliminated_choices.clear()
                    self.ident_input_text = ""
                    self.station_attempts[self.quiz_station_index] = 0
                    return "handled"
                elif self.quiz_state == 4:
                    click_pos = self.out_of_tries_btn_rect.center if hasattr(self, 'out_of_tries_btn_rect') and self.out_of_tries_btn_rect else (self.width // 2, self.height // 2)
                    self.trigger_click(click_pos)
                    return "handled"
                if getattr(self, 'guardian_skeleton_state', 0) == 2:
                    self.guardian_skeleton_state = 1 if self.quiz_station_index >= 6 else 0
                    return "handled"
                if getattr(self, 'fraction_match_active', False) or getattr(self, 'solar_array_puzzle_active', False):
                    self.close_fraction_match_modal()
                    return "handled"
                if self.main_menu:
                    from db.save_system import show_saving_and_exit
                    show_saving_and_exit(self.main_menu)
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info

            # Physical Keyboard Typing in Identification Question Mode (State 1)
            elif self.quiz_state == 1 and self.quiz_questions and 0 <= self.current_question_index < len(self.quiz_questions):
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
            self.cursor_pos = event.pos
            if not self.pause_menu.is_paused and (
                getattr(self, 'fraction_match_active', False)
                or getattr(self, 'fraction_bakery_active', False)
                or getattr(self, 'solar_array_puzzle_active', False)
                or getattr(self, 'guardian_skeleton_state', 0) == 3
            ):
                self.handle_fraction_match_mouse_down(event.pos)
            else:
                self.trigger_click(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if (getattr(self, 'fraction_match_active', False) or getattr(self, 'fraction_bakery_active', False) or getattr(self, 'solar_array_puzzle_active', False)) and getattr(self, 'mouse_drag_active', False):
                self.mouse_drag_active = False
                self.release_dragged_solar_piece()
        elif event.type == pygame.MOUSEMOTION:
            if not getattr(self, 'hand_detected', False) or getattr(self, 'current_gesture', 'NO HAND') in ['NO HAND', 'NO HAND (GRACE)']:
                self.cursor_pos = event.pos

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
            elif "row" in q_text or "array" in q_text or "x" in q_text or "times" in q_text or "multiply" in q_text:
                v_type = "array"
            elif "group" in q_text or "+" in q_text or "basket" in q_text or "plate" in q_text or "box" in q_text:
                v_type = "groups"
            elif "share" in q_text or "divide" in q_text or "/" in q_text or "equally" in q_text:
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

            lbl = self.dialog_stat_font.render(f"Visual Model: {rows} Rows with {cols} Apples in Each Row", True, (253, 230, 138))
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

            lbl = self.dialog_stat_font.render(f"Visual Model: {groups} Groups with {items_per_group} Coconuts in Each Group", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 3. Equal Sharing Division (Dynamic total & chests extracted from text)
        elif v_type == "sharing":
            chests = q_data.get("visual_chests", nums[1] if len(nums) >= 2 else 2)
            total = q_data.get("visual_total", nums[0] if len(nums) >= 1 else 10)
            chests = min(4, max(1, chests))

            # Draw central gold coin supply pool above chests
            coin_pool_y = vis_rect.centery - 42
            p_lbl = self.dialog_hint_font.render(f"Total: {total} Gold Coins to Divide", True, (254, 240, 138))
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
                
                c_lbl = self.dialog_stat_font.render(f"Chest {ch_i+1}", True, (253, 230, 138))
                self.screen.blit(c_lbl, (cx + chest_w // 2 - c_lbl.get_width() // 2, cy + 12))

            lbl = self.dialog_stat_font.render(f"Visual Model: Share {total} Gold Coins Equally between {chests} Chests", True, (253, 230, 138))
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

            lbl = self.dialog_stat_font.render(f"Visual Model: {shaded} Shaded Part out of {slices} Equal Parts", True, (253, 230, 138))
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

            lbl = self.dialog_stat_font.render(f"Visual Model: {shaded} Shaded Segment out of {segments} Equal Segments", True, (253, 230, 138))
            self.screen.blit(lbl, (vis_rect.centerx - lbl.get_width() // 2, vis_rect.bottom - 24))

        # 6. General Fallback (Non-math / General Knowledge / Science / English)
        else:
            hint_txt = q_data.get("hint", "Examine the choices carefully and select the best answer below! ")
            # Stylized Challenge Crest
            pygame.draw.circle(self.screen, (30, 41, 59), (vis_rect.centerx, vis_rect.centery - 18), 24)
            pygame.draw.circle(self.screen, (245, 158, 11), (vis_rect.centerx, vis_rect.centery - 18), 24, 2)
            c_icon = self.dialog_speaker_font.render("", True, (255, 215, 0))
            self.screen.blit(c_icon, c_icon.get_rect(center=(vis_rect.centerx, vis_rect.centery - 18)))
            
            h_surf = self.dialog_hint_font.render(f"{hint_txt}", True, (253, 230, 138))
            self.screen.blit(h_surf, (vis_rect.centerx - h_surf.get_width() // 2, vis_rect.bottom - 26))

    # ============================================================
    # QUIZ DIALOGUE DRAWING METHODS (Clean & Icon-Free)
    # ============================================================
    def draw_quiz_dialog(self):
        q_idx = max(0, min(self.current_question_index, len(self.quiz_questions) - 1)) if self.quiz_questions else 0
        q_data = self.quiz_questions[q_idx] if self.quiz_questions else {"question": "", "choices": [], "correct": 0}
        st_title = q_data.get("title", f"Challenge {self.quiz_station_index}")
        npc_info = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = npc_info.get("name", "Guardian")
        speaker_subtitle = f"{st_title} - Oasis Mirage"

        # Get animated sprite frame
        sprite_frame = None
        if npc_info.get("frames"):
            frames = npc_info["frames"]
            anim_idx = npc_info.get("anim_frame", 0) % len(frames)
            sprite_frame = frames[anim_idx]

        tot_st = max(1, getattr(self, 'active_station_count', len(self.quiz_questions)))
        self.quiz_dialog.update(0.016)
        self.quiz_dialog.draw(
            cursor_pos=self.cursor_pos,
            q_data=q_data,
            speaker_name=speaker_name,
            speaker_subtitle=speaker_subtitle,
            sprite_frame=sprite_frame,
            station_idx=self.quiz_station_index,
            total_stations=tot_st,
            eliminated_choices=self.eliminated_choices,
            hint_msg=self.wrong_feedback_msg
        )

    def _get_dim_overlay(self):
        ov = getattr(self, '_dim_overlay', None)
        if ov is None or ov.get_size() != (self.width, self.height):
            ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            ov.fill((10, 15, 29, 170))
            if pygame.display.get_surface() is not None:
                try:
                    ov = ov.convert_alpha()
                except Exception:
                    pass
            self._dim_overlay = ov
        return ov

    def draw_wrong_dialog(self):
        self.screen.blit(self._get_dim_overlay(), (0, 0))

        box_w, box_h = 760, 360
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, (248, 113, 113), dialog_rect.inflate(-6, -6), 1, border_radius=12)

        script = get_station_script(self.map_name, self.quiz_station_index)
        npc_info = self.station_npcs.get(self.quiz_station_index, {})
        speaker = script.get("npc_name", npc_info.get("name", "Guardian"))
        speaker_title = script.get("npc_title", npc_info.get("title", f"Station {self.quiz_station_index}"))
        retry_msg = script.get("retry_line", "Think carefully about the fraction or grouping! You have 1 try remaining!").replace("[Player Name]", self.player_name)

        speaker_surf = self.dialog_header_font.render(f"{speaker} ({speaker_title}) - Try Again", True, (248, 113, 113))
        self.screen.blit(speaker_surf, (box_x + 28, box_y + 18))

        lines = self.wrap_text(retry_msg, self.dialog_q_font, box_w - 56)
        y_off = box_y + 56
        for l in lines[:2]:
            self.screen.blit(self.dialog_q_font.render(l, True, (255, 255, 255)), (box_x + 28, y_off))
            y_off += 26

        # Pedagogical Educational Hint Box
        from core.hints import get_educational_hint
        from core.vector_icons import draw_vector_lightbulb
        current_q = self.quiz_questions[self.current_question_index] if self.current_question_index < len(self.quiz_questions) else {}
        q_text = current_q.get("question", "")
        hint_text = get_educational_hint("quarter3", q_text)

        hint_box = pygame.Rect(box_x + 24, box_y + 124, box_w - 48, 130)
        pygame.draw.rect(self.screen, (30, 41, 59), hint_box, border_radius=10)
        pygame.draw.rect(self.screen, (245, 158, 11), hint_box, 2, border_radius=10)

        hint_title_font = self.get_ui_font(18, bold=True)
        hint_body_font = self.get_ui_font(16, bold=True)
        draw_vector_lightbulb(self.screen, hint_box.x + 22, hint_box.y + 18, size=7)
        h_title = hint_title_font.render("Pedagogical Hint:", True, (255, 215, 0))
        self.screen.blit(h_title, (hint_box.x + 38, hint_box.y + 9))

        # Text wrap
        words = hint_text.split(" ")
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if hint_body_font.size(" ".join(cur))[0] > (hint_box.width - 32):
                cur.pop()
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))

        hy = hint_box.y + 38
        for hl in lines[:3]:
            h_surf = hint_body_font.render(hl, True, (241, 245, 249))
            self.screen.blit(h_surf, (hint_box.x + 16, hy))
            hy += 26

        button_w, button_h = 240, 50
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 280
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        self.wrong_btn_rect = btn_rect
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        bg_c = (220, 38, 38) if is_hov else (153, 27, 27)

        pygame.draw.rect(self.screen, bg_c, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Try Again", True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    def draw_out_of_tries_dialog(self):
        self.screen.blit(self._get_dim_overlay(), (0, 0))

        box_w, box_h = 740, 340
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (245, 158, 11), dialog_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, (251, 191, 36), dialog_rect.inflate(-6, -6), 1, border_radius=12)

        script = get_station_script(self.map_name, self.quiz_station_index)
        npc_info = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = script.get("npc_name", npc_info.get("name", f"Station {self.quiz_station_index}"))
        reveal_msg = script.get("out_of_tries_line", "Here is the answer. Keep moving forward!").replace("[Player Name]", self.player_name)
        item_name = script.get("item_awarded", "Progression Item")

        speaker_surf = self.dialog_header_font.render(f"{speaker_name} — 2 Tries Exhausted", True, (245, 158, 11))
        self.screen.blit(speaker_surf, (box_x + 28, box_y + 18))

        q_data = self.quiz_questions[self.current_question_index] if self.quiz_questions and self.current_question_index < len(self.quiz_questions) else {}
        choices = q_data.get("choices", []) if isinstance(q_data, dict) else []
        c_idx = q_data.get("correct", 0) if isinstance(q_data, dict) else 0
        if isinstance(c_idx, str) and c_idx.isdigit():
            c_idx = int(c_idx)
        correct_choice_text = choices[c_idx] if isinstance(c_idx, int) and 0 <= c_idx < len(choices) else ""

        if correct_choice_text:
            ans_msg = f"Out of tries! The correct answer was: {correct_choice_text}"
        else:
            ans_msg = "You have used both of your 2 attempts for this challenge."
        lines = self.wrap_text(ans_msg, self.dialog_q_font, box_w - 56)
        y_off = box_y + 65
        for l in lines[:2]:
            self.screen.blit(self.dialog_q_font.render(l, True, (255, 255, 255)), (box_x + 28, y_off))
            y_off += 28

        reward_surf = self.dialog_hint_font.render(f"Acquired: {item_name}! Recorded as incorrect, but your quest continues!", True, (254, 240, 138))
        self.screen.blit(reward_surf, (box_x + 28, y_off + 10))

        button_w, button_h = 260, 50
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 260
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        self.out_of_tries_btn_rect = btn_rect

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (245, 158, 11) if is_hovered else (30, 41, 59)
        border_color = (255, 255, 255) if is_hovered else (245, 158, 11)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=12)

        c_surf = self.dialog_header_font.render("Continue Quest >>", True, (255, 255, 255) if not is_hovered else (15, 23, 42))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_correct_dialog(self):
        self.screen.blit(self._get_dim_overlay(), (0, 0))

        box_w, box_h = 740, 330
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (22, 163, 74), dialog_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, (74, 222, 128), dialog_rect.inflate(-6, -6), 1, border_radius=12)

        script = get_station_script(self.map_name, self.quiz_station_index)
        npc_info = self.station_npcs.get(self.quiz_station_index, {})
        speaker_name = script.get("npc_name", npc_info.get("name", "Guardian"))
        praise_msg = script.get("praise_line", self.current_correct_phrase).replace("[Player Name]", self.player_name)
        item_name = script.get("item_awarded", "Progression Item")

        speaker_surf = self.dialog_header_font.render(f"{speaker_name} - Well Done! (Correct)", True, (74, 222, 128))
        self.screen.blit(speaker_surf, (box_x + 28, box_y + 20))

        lines = self.wrap_text(praise_msg, self.dialog_q_font, box_w - 56)
        y_off = box_y + 75
        for l in lines[:2]:
            self.screen.blit(self.dialog_q_font.render(l, True, (255, 255, 255)), (box_x + 28, y_off))
            y_off += 30

        reward_surf = self.dialog_hint_font.render(f"Awarded: {item_name}!", True, (253, 230, 138))
        self.screen.blit(reward_surf, (box_x + 28, y_off + 10))

        button_w, button_h = 260, 50
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 245
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (22, 163, 74) if is_hovered else (30, 41, 59)
        border_color = (255, 255, 255) if is_hovered else (22, 163, 74)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=12)

        c_surf = self.dialog_header_font.render("Continue >>", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_final_dialog(self):
        self.screen.blit(self.dialog_dim_overlay, (0, 0))

        box_w, box_h = 780, 420
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (218, 165, 32), dialog_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, (255, 215, 0), dialog_rect.inflate(-6, -6), 1, border_radius=12)

        mentor = get_mentor_script(self.map_name)
        m_name = mentor.get("mentor_name", "Desert Vault Keeper")
        m_title = mentor.get("mentor_title", "Sun Citadel Guardian")
        complete_speech = mentor.get("complete_dialogue", "Outstanding! You have solved all challenges!").replace("[Player Name]", self.player_name)

        speaker_surf = self.dialog_header_font.render(f"{m_name} ({m_title})", True, (255, 215, 0))
        self.screen.blit(speaker_surf, (box_x + 28, box_y + 20))

        lines = self.wrap_text(complete_speech, self.dialog_q_font, box_w - 56)
        y_text = box_y + 75
        for line in lines[:5]:
            txt_surf = self.dialog_q_font.render(line, True, (248, 250, 252))
            self.screen.blit(txt_surf, (box_x + 28, y_text))
            y_text += 32

        button_w, button_h = 260, 50
        button_x = box_x + (box_w - button_w) // 2
        button_y = box_y + 340
        btn_rect = pygame.Rect(button_x, button_y, button_w, button_h)

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        bg_color = (218, 165, 32) if is_hovered else (30, 41, 59)
        border_color = (255, 255, 255) if is_hovered else (218, 165, 32)

        pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, border_color, btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Complete Quest >>", True, (255, 255, 255) if not is_hovered else (15, 23, 42))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)

    # ============================================================
    # ANCIENT SUN TEMPLE SOLAR ARRAY PUZZLE ENGINE (Skeleton Guardian)
    # ============================================================
    # ============================================================
    # THE SCALES OF ANUBIS: EQUAL SHARING DIVISION PUZZLE ENGINE
    # ============================================================
    def render_egyptian_scarab_surface(self, size, color=(217, 119, 6), accent_color=(56, 189, 248)):
        """Renders an authentic, ornate 3D Egyptian Scarab Amulet with gold casing and lapis wings"""
        import pygame
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2
        w = size - 4
        h = int(size * 0.88)
        bx = (size - w) // 2
        by = (size - h) // 2

        # Outer ornate gold bezel rim
        pygame.draw.ellipse(surf, (15, 23, 42), (bx - 1, by - 1, w + 2, h + 2))
        pygame.draw.ellipse(surf, (217, 119, 6), (bx, by, w, h), 2)

        # Deep Obsidian / Bronze Shell Base
        body_rect = pygame.Rect(bx + 2, by + 2, w - 4, h - 4)
        pygame.draw.ellipse(surf, (26, 32, 44), body_rect)
        pygame.draw.ellipse(surf, color, body_rect.inflate(-4, -4))

        # Sacred Dual Wings
        wing_w = (w - 8) // 2
        wing_h = h - 8
        left_wing = pygame.Rect(bx + 4, by + 4, wing_w, wing_h)
        right_wing = pygame.Rect(bx + 4 + wing_w, by + 4, wing_w, wing_h)
        pygame.draw.ellipse(surf, accent_color, left_wing)
        pygame.draw.ellipse(surf, accent_color, right_wing)
        pygame.draw.ellipse(surf, (255, 255, 255, 90), left_wing.inflate(-4, -4))
        pygame.draw.ellipse(surf, (255, 255, 255, 90), right_wing.inflate(-4, -4))

        # Center spine & wing seam
        pygame.draw.line(surf, (217, 119, 6), (cx, by + 4), (cx, by + h - 6), 2)

        # Solar Disk Jewel held by scarab
        disk_r = max(3, size // 8)
        pygame.draw.circle(surf, (251, 191, 36), (cx, by + disk_r + 1), disk_r)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 1, by + disk_r), max(1, disk_r // 2))

        return surf

    def render_solar_crystal_surface(self, size, color, accent_color=(255, 255, 255)):
        """Compatibility wrapper: returns ornate scarab gem surface"""
        return self.render_egyptian_scarab_surface(size, color, accent_color)

    def render_solar_gem_slab(self, item, width, height):
        """Compatibility wrapper: returns a rendered gem surface on a mini slab"""
        color = item.get("color", (245, 158, 11))
        accent = item.get("accent", (56, 189, 248))
        return self.render_egyptian_scarab_surface(min(width, height) - 6, color, accent)

    # ============================================================
    # SUN TEMPLE FRACTION MATCH (QUARTER 3 GUARDIAN MINI-GAME)
    # ============================================================
    SUN_TEMPLE_FRACTION_POOL = [
        {
            "id": "frac_1_2",
            "fraction_str": "1/2",
            "word_name": "One-Half",
            "parts_hint": "1 OF 2 EQUAL PARTS",
            "num": 1,
            "denom": 2,
            "shape": "circle",
            "color_accent": (251, 191, 36),
            "color_highlight": (254, 240, 138),
            "equation": "1/2 = One-Half",
            "desc": "1 shaded part out of 2 equal parts"
        },
        {
            "id": "frac_1_3",
            "fraction_str": "1/3",
            "word_name": "One-Third",
            "parts_hint": "1 OF 3 EQUAL PARTS",
            "num": 1,
            "denom": 3,
            "shape": "circle",
            "color_accent": (244, 63, 94),
            "color_highlight": (253, 164, 175),
            "equation": "1/3 = One-Third",
            "desc": "1 shaded part out of 3 equal parts"
        },
        {
            "id": "frac_2_3",
            "fraction_str": "2/3",
            "word_name": "Two-Thirds",
            "parts_hint": "2 OF 3 EQUAL PARTS",
            "num": 2,
            "denom": 3,
            "shape": "bar",
            "color_accent": (16, 185, 129),
            "color_highlight": (110, 231, 183),
            "equation": "2/3 = Two-Thirds",
            "desc": "2 shaded parts out of 3 equal parts"
        },
        {
            "id": "frac_1_4",
            "fraction_str": "1/4",
            "word_name": "One-Fourth",
            "parts_hint": "1 OF 4 EQUAL PARTS",
            "num": 1,
            "denom": 4,
            "shape": "grid2x2",
            "color_accent": (56, 189, 248),
            "color_highlight": (186, 230, 253),
            "equation": "1/4 = One-Fourth",
            "desc": "1 shaded part out of 4 equal parts"
        },
        {
            "id": "frac_3_4",
            "fraction_str": "3/4",
            "word_name": "Three-Fourths",
            "parts_hint": "3 OF 4 EQUAL PARTS",
            "num": 3,
            "denom": 4,
            "shape": "circle",
            "color_accent": (249, 115, 22),
            "color_highlight": (254, 215, 170),
            "equation": "3/4 = Three-Fourths",
            "desc": "3 shaded parts out of 4 equal parts"
        },
    ]

    def _conv_alpha(self, surf):
        if pygame.display.get_surface() is not None:
            return surf.convert_alpha()
        return surf

    def _render_fraction_shape_card(self, item, w, h, state="normal"):
        """Pre-renders a high-contrast visual fraction card (.convert_alpha()) with zero per-frame cost."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        if state == "selected":
            bg_col = (24, 42, 68)
            border_col = (56, 189, 248)
            border_w = 3
        elif state == "hover":
            bg_col = (26, 36, 58)
            border_col = (255, 215, 0)
            border_w = 3
        elif state == "placed":
            bg_col = (18, 38, 32)
            border_col = (74, 222, 128)
            border_w = 2
        else:
            bg_col = (18, 26, 44)
            border_col = (217, 119, 6)
            border_w = 2

        pygame.draw.rect(surf, bg_col, (0, 0, w, h), border_radius=10)
        pygame.draw.rect(surf, border_col, (0, 0, w, h), border_w, border_radius=10)
        pygame.draw.rect(surf, (45, 58, 82), (4, 4, w - 8, h - 8), 1, border_radius=8)

        # Subtle gold temple corner studs
        for cx_dot, cy_dot in [(10, 10), (w - 10, 10), (10, h - 10), (w - 10, h - 10)]:
            pygame.draw.circle(surf, (217, 119, 6), (cx_dot, cy_dot), 2)

        cx, cy = w // 2, h // 2
        num = item["num"]
        denom = item["denom"]
        fill_col = item["color_accent"]
        hi_col = item["color_highlight"]
        empty_col = (51, 65, 85)
        line_col = (248, 250, 252)
        shape = item["shape"]

        if shape == "circle":
            r = min(w, h) // 2 - 12
            pygame.draw.circle(surf, (8, 12, 22, 160), (cx + 2, cy + 3), r + 1)
            pygame.draw.circle(surf, empty_col, (cx, cy), r)

            slice_ang = (2.0 * math.pi) / denom
            steps = 28
            for s_idx in range(num):
                s_start = -math.pi / 2.0 + s_idx * slice_ang
                s_end = s_start + slice_ang
                pts = [(cx, cy)]
                for step in range(steps + 1):
                    ang = s_start + (s_end - s_start) * (step / steps)
                    pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
                pygame.draw.polygon(surf, fill_col, pts)

                mid_a = (s_start + s_end) * 0.5
                hx = int(cx + math.cos(mid_a) * (r * 0.55))
                hy = int(cy + math.sin(mid_a) * (r * 0.55))
                pygame.draw.circle(surf, hi_col, (hx, hy), 4)

            if denom == 2:
                pygame.draw.line(surf, line_col, (cx, cy - r), (cx, cy + r), 3)
            elif denom == 4:
                pygame.draw.line(surf, line_col, (cx, cy - r), (cx, cy + r), 3)
                pygame.draw.line(surf, line_col, (cx - r, cy), (cx + r, cy), 3)
            else:
                for k in range(denom):
                    ang = -math.pi / 2.0 + k * slice_ang
                    ex = int(round(cx + math.cos(ang) * r))
                    ey = int(round(cy + math.sin(ang) * r))
                    pygame.draw.line(surf, line_col, (cx, cy), (ex, ey), 3)
                pygame.draw.circle(surf, line_col, (cx, cy), 3)

            pygame.draw.circle(surf, line_col, (cx, cy), r, 3)

        elif shape == "bar":
            bw = min(168, w - 40)
            bh = min(66, h - 34)
            bx = cx - bw // 2
            by = cy - bh // 2
            pygame.draw.rect(surf, (8, 12, 22, 160), (bx + 2, by + 3, bw, bh), border_radius=8)
            pygame.draw.rect(surf, empty_col, (bx, by, bw, bh), border_radius=8)

            seg_w = bw // denom
            for s_idx in range(num):
                sx = bx + s_idx * seg_w
                sw = seg_w if s_idx < denom - 1 else (bw - s_idx * seg_w)
                pygame.draw.rect(surf, fill_col, (sx + 2, by + 2, sw - 2, bh - 4), border_radius=5)
                pygame.draw.circle(surf, hi_col, (sx + sw // 2, by + bh // 2), 4)

            for k in range(1, denom):
                dx = bx + k * seg_w
                pygame.draw.line(surf, line_col, (dx, by), (dx, by + bh - 1), 3)
            pygame.draw.rect(surf, line_col, (bx, by, bw, bh), 3, border_radius=8)

        else:  # grid2x2
            side = min(w - 56, h - 22)
            side = (side // 2) * 2
            half = side // 2
            gx = cx - half
            gy = cy - half
            pygame.draw.rect(surf, (8, 12, 22, 160), (gx + 2, gy + 3, side, side), border_radius=8)
            pygame.draw.rect(surf, empty_col, (gx, gy, side, side), border_radius=8)

            quads = [
                (gx + 2, gy + 2, half - 2, half - 2),
                (gx + half, gy + 2, half - 2, half - 2),
                (gx + 2, gy + half, half - 2, half - 2),
                (gx + half, gy + half, half - 2, half - 2),
            ]
            for q_idx in range(min(num, 4)):
                qr = quads[q_idx]
                pygame.draw.rect(surf, fill_col, qr, border_radius=4)
                pygame.draw.circle(surf, hi_col, (qr[0] + qr[2] // 2, qr[1] + qr[3] // 2), 4)

            pygame.draw.line(surf, line_col, (gx + half, gy), (gx + half, gy + side - 1), 3)
            pygame.draw.line(surf, line_col, (gx, gy + half), (gx + side - 1, gy + half), 3)
            pygame.draw.rect(surf, line_col, (gx, gy, side, side), 3, border_radius=8)

        return self._conv_alpha(surf)

    def _render_fraction_slot_surface(self, item, w, h, state="empty"):
        """Pre-renders a top-row Sun Altar target slot (.convert_alpha()) for empty/hover/matched states."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        accent_col = item["color_accent"]

        if state == "matched":
            bg_col = (18, 40, 32)
            border_col = (34, 197, 94)
            border_w = 3
        elif state == "hover":
            bg_col = (28, 38, 58)
            border_col = (255, 215, 0)
            border_w = 3
        else:
            bg_col = (24, 32, 47)
            border_col = (100, 116, 139)
            border_w = 2

        pygame.draw.rect(surf, bg_col, (0, 0, w, h), border_radius=12)
        pygame.draw.rect(surf, border_col, (0, 0, w, h), border_w, border_radius=12)

        # Top Fraction Symbol Header Pill
        hbar = pygame.Rect(6, 6, w - 12, 36)
        pygame.draw.rect(surf, (15, 23, 42), hbar, border_radius=8)
        pygame.draw.rect(surf, (34, 197, 94) if state == "matched" else accent_col, hbar, 1, border_radius=8)

        frac_font = self.get_ui_font(18, bold=True)
        hint_font = self.get_ui_font(10, bold=True)
        word_font = self.get_ui_font(13, bold=True)

        f_surf = frac_font.render(item["fraction_str"], True, (74, 222, 128) if state == "matched" else accent_col)
        surf.blit(f_surf, (hbar.x + 10, hbar.centery - f_surf.get_height() // 2))

        if state == "matched":
            m_lbl = hint_font.render("MATCHED!", True, (74, 222, 128))
            surf.blit(m_lbl, (hbar.right - m_lbl.get_width() - 10, hbar.centery - m_lbl.get_height() // 2))
        else:
            p_lbl = hint_font.render(item["parts_hint"], True, (203, 213, 225))
            surf.blit(p_lbl, (hbar.right - p_lbl.get_width() - 10, hbar.centery - p_lbl.get_height() // 2))

        # Word Name Subtitle ("One-Half", "One-Third", etc.)
        w_surf = word_font.render(item["word_name"], True, (255, 255, 255))
        surf.blit(w_surf, w_surf.get_rect(center=(w // 2, 56)))

        # Drop Zone Chamber
        drop_box = pygame.Rect(10, 74, w - 20, h - 84)
        if state != "matched":
            pygame.draw.rect(surf, (15, 23, 42), drop_box, border_radius=9)
            pygame.draw.rect(surf, (255, 215, 0) if state == "hover" else (71, 85, 105), drop_box, 1, border_radius=9)
            prompt_str = "Click or Drop Here" if state == "hover" else "Drop Matching Card"
            d_lbl = self.get_ui_font(11).render(prompt_str, True, (254, 240, 138) if state == "hover" else (148, 163, 184))
            surf.blit(d_lbl, d_lbl.get_rect(center=drop_box.center))

        return self._conv_alpha(surf)

    def _make_btn_surf(self, w, h, text, bg_col, border_col, txt_col, font_size=13, border_w=1):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, bg_col, (0, 0, w, h), border_radius=9)
        pygame.draw.rect(s, border_col, (0, 0, w, h), border_w, border_radius=9)
        t = self.get_ui_font(font_size, bold=True).render(text, True, txt_col)
        s.blit(t, t.get_rect(center=(w // 2, h // 2)))
        return self._conv_alpha(s)

    def init_fraction_match(self):
        """Initializes the single-round 4-Card Sun Temple Fraction Match mini-game."""
        self.fraction_match_active = True
        self.fraction_bakery_active = True
        self.solar_array_puzzle_active = True
        self.fraction_match_all_placed = False
        self.solar_array_puzzle_all_placed = False
        self.click_dest = None
        self.dragged_fraction_piece = None
        self.dragged_bakery_slice = None
        self.dragged_solar_piece = None
        self.selected_fraction_piece = None
        self.mouse_drag_active = False
        self.fraction_match_sparkles = []
        self.fraction_match_feedback_timer = 0.0
        self.fraction_match_feedback_kind = ""

        # Sample 4 distinct non-equivalent Grade 2 fractions for this round
        pool = random.sample(self.SUN_TEMPLE_FRACTION_POOL, 4)

        panel_w = min(1140, self.width - 60)
        panel_h = min(620, self.height - 50)
        panel_x = (self.width - panel_w) // 2
        panel_y = (self.height - panel_h) // 2
        self.fraction_match_panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        num_items = 4
        gap = 18
        slot_w = (panel_w - 60 - (num_items - 1) * gap) // num_items
        slot_h = 204
        slot_y = panel_y + 98

        # 1. Pre-bake Static Modal Panel Surface (Zero per-frame text/rect overhead)
        panel_surf = pygame.Surface((panel_w + 8, panel_h + 8), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (0, 0, 0, 155), (6, 6, panel_w, panel_h), border_radius=18)
        pygame.draw.rect(panel_surf, (15, 23, 42), (0, 0, panel_w, panel_h), border_radius=18)
        pygame.draw.rect(panel_surf, (217, 119, 6), (0, 0, panel_w, panel_h), 3, border_radius=18)
        pygame.draw.rect(panel_surf, (253, 224, 71), (6, 6, panel_w - 12, panel_h - 12), 1, border_radius=14)

        # Header Sun Emblem + Title
        h_font = self.get_ui_font(22, bold=True)
        sub_font = self.get_ui_font(13)
        h_surf = h_font.render("SUN TEMPLE FRACTION MATCH", True, (255, 215, 0))
        hx = (panel_w - h_surf.get_width()) // 2
        sun_cx = hx - 22
        sun_cy = 30
        pygame.draw.circle(panel_surf, (245, 158, 11), (sun_cx, sun_cy), 10)
        pygame.draw.circle(panel_surf, (254, 240, 138), (sun_cx, sun_cy), 6)
        for ray_i in range(8):
            ra = ray_i * (math.pi / 4.0)
            pygame.draw.line(
                panel_surf, (253, 224, 71),
                (int(sun_cx + math.cos(ra) * 11), int(sun_cy + math.sin(ra) * 11)),
                (int(sun_cx + math.cos(ra) * 15), int(sun_cy + math.sin(ra) * 15)), 2
            )
        panel_surf.blit(h_surf, (hx, 30 - h_surf.get_height() // 2))

        sub_surf = sub_font.render(
            "Drag each shaded shape card (or click a card, then click a slot) to match all 4 fractions!",
            True, (203, 213, 225)
        )
        panel_surf.blit(sub_surf, sub_surf.get_rect(center=(panel_w // 2, 58)))
        pygame.draw.line(panel_surf, (71, 85, 105), (30, 80), (panel_w - 30, 80), 1)

        # Bottom Tray Recessed Frame
        tray_rel = pygame.Rect(24, 348, panel_w - 48, 146)
        pygame.draw.rect(panel_surf, (10, 16, 30), tray_rel, border_radius=14)
        pygame.draw.rect(panel_surf, (71, 85, 105), tray_rel, 2, border_radius=14)
        self._fraction_match_panel_surf = self._conv_alpha(panel_surf)

        # 2. Top-Row Target Slots
        self.fraction_match_slots = []
        piece_w = slot_w - 24
        piece_h = 112

        for i, item in enumerate(pool):
            sx = panel_x + 30 + i * (slot_w + gap)
            s_rect = pygame.Rect(sx, slot_y, slot_w, slot_h)
            drop_x = sx + (slot_w - piece_w) // 2
            drop_y = slot_y + 78
            self.fraction_match_slots.append({
                "id": item["id"],
                "index": i,
                "rect": s_rect,
                "drop_pos": (drop_x, drop_y),
                "fraction_str": item["fraction_str"],
                "word_name": item["word_name"],
                "parts_hint": item["parts_hint"],
                "equation": item["equation"],
                "factor_desc": item["desc"],
                "color": item["color_accent"],
                "data": item,
                "matched": False,
                "matched_piece": None,
                "empty_surf": self._render_fraction_slot_surface(item, slot_w, slot_h, "empty"),
                "hover_surf": self._render_fraction_slot_surface(item, slot_w, slot_h, "hover"),
                "matched_surf": self._render_fraction_slot_surface(item, slot_w, slot_h, "matched"),
            })

        # 3. Bottom-Row Shuffled Visual Fraction Cards
        shuffled_pool = list(pool)
        for _ in range(6):
            random.shuffle(shuffled_pool)
            if any(shuffled_pool[idx]["id"] != pool[idx]["id"] for idx in range(num_items)):
                break

        tray_card_y = panel_y + 365
        self.fraction_match_pieces = []
        for i, item in enumerate(shuffled_pool):
            px_card = panel_x + 30 + i * (slot_w + gap) + (slot_w - piece_w) // 2
            p_rect = pygame.Rect(px_card, tray_card_y, piece_w, piece_h)
            tok_normal = self._render_fraction_shape_card(item, piece_w, piece_h, "normal")
            tok_hover = self._render_fraction_shape_card(item, piece_w, piece_h, "hover")
            tok_selected = self._render_fraction_shape_card(item, piece_w, piece_h, "selected")
            tok_placed = self._render_fraction_shape_card(item, piece_w, piece_h, "placed")
            self.fraction_match_pieces.append({
                "id": item["id"],
                "fraction_str": item["fraction_str"],
                "word_name": item["word_name"],
                "data": item,
                "orig_x": px_card,
                "orig_y": tray_card_y,
                "x": px_card,
                "y": tray_card_y,
                "w": piece_w,
                "h": piece_h,
                "rect": p_rect,
                "token_surf": tok_normal,
                "gem_surf": tok_normal,
                "hover_surf": tok_hover,
                "selected_surf": tok_selected,
                "placed_surf": tok_placed,
                "is_dragging": False,
                "is_placed": False,
                "target_slot_id": None,
            })

        # 4. Pre-baked Status & Feedback Surfaces
        st_font = self.get_ui_font(12, bold=True)
        self._fm_status_surfs = {}
        for cnt in range(5):
            if cnt < 4:
                txt = f"SHAPE CARD TRAY ({cnt}/4 MATCHED) - DRAG WITH FIST / MOUSE OR CLICK TO MATCH"
                col = (251, 191, 36)
            else:
                txt = "ALL 4 FRACTIONS MATCHED! CLICK UNLOCK SUN PORTAL >>"
                col = (74, 222, 128)
            self._fm_status_surfs[cnt] = self._conv_alpha(st_font.render(txt, True, col))

        self._fm_selected_hint_surf = self._conv_alpha(
            st_font.render("CARD SELECTED! NOW CLICK ITS MATCHING FRACTION SLOT ABOVE!", True, (56, 189, 248))
        )
        self._fm_wrong_hint_surf = self._conv_alpha(
            st_font.render("NOT QUITE! COUNT THE TOTAL EQUAL PARTS AND SHADED PARTS, THEN TRY AGAIN!", True, (252, 165, 165))
        )

        # 5. Action Buttons & Pre-baked Button Surfaces
        btn_y = panel_y + panel_h - 54
        self.fraction_match_close_btn_rect = pygame.Rect(panel_x + 30, btn_y, 185, 42)
        self.fraction_match_reset_btn_rect = pygame.Rect(panel_x + 228, btn_y, 148, 42)
        self.fraction_match_continue_btn_rect = pygame.Rect(panel_x + panel_w - 280, btn_y, 250, 42)
        self.fraction_match_x_btn_rect = pygame.Rect(panel_x + panel_w - 40, panel_y + 12, 28, 28)

        self.solar_puzzle_close_btn_rect = self.fraction_match_close_btn_rect
        self.solar_puzzle_reset_btn_rect = self.fraction_match_reset_btn_rect
        self.solar_puzzle_continue_btn_rect = self.fraction_match_continue_btn_rect
        self.solar_puzzle_x_btn_rect = self.fraction_match_x_btn_rect

        self._fm_btn_surfs = {
            "close_norm": self._make_btn_surf(185, 42, "Back to Desert [Esc]", (30, 41, 59), (100, 116, 139), (241, 245, 249)),
            "close_hov": self._make_btn_surf(185, 42, "Back to Desert [Esc]", (51, 65, 85), (203, 213, 225), (255, 255, 255)),
            "reset_norm": self._make_btn_surf(148, 42, "Reset Tray", (30, 41, 59), (100, 116, 139), (241, 245, 249)),
            "reset_hov": self._make_btn_surf(148, 42, "Reset Tray", (51, 65, 85), (203, 213, 225), (255, 255, 255)),
            "unlock_locked": self._make_btn_surf(250, 42, "Match 4/4 to Unlock", (24, 32, 47), (71, 85, 105), (148, 163, 184), font_size=12),
            "unlock_ready": self._make_btn_surf(250, 42, "Unlock Sun Portal >>", (22, 163, 74), (255, 255, 255), (255, 255, 255), font_size=14, border_w=2),
            "unlock_hov": self._make_btn_surf(250, 42, "Unlock Sun Portal >>", (255, 215, 0), (255, 255, 255), (15, 23, 42), font_size=14, border_w=2),
            "x_norm": self._make_btn_surf(28, 28, "X", (51, 65, 85), (100, 116, 139), (255, 255, 255), font_size=12),
            "x_hov": self._make_btn_surf(28, 28, "X", (220, 38, 38), (252, 165, 165), (255, 255, 255), font_size=12),
        }

        # Sync backwards-compatibility attributes
        self.solar_matrix_rows = 1
        self.solar_matrix_cols = num_items
        self.solar_array_puzzle_slots = self.fraction_match_slots
        self.solar_array_puzzle_pieces = self.fraction_match_pieces
        self.solar_array_target_equation = " | ".join(s["equation"] for s in self.fraction_match_slots)
        self.solar_array_factor_desc = "Match each visual shaded model to its unit or common fraction."
        self._sync_fraction_match_completion_flags()
        print(f"[SUN FRACTION MATCH] Initialized 4-card round: {[s['fraction_str'] for s in self.fraction_match_slots]}")

    def _sync_fraction_match_completion_flags(self):
        all_matched = bool(self.fraction_match_slots) and all(s["matched"] for s in self.fraction_match_slots)
        self.fraction_match_all_placed = all_matched
        self.solar_array_puzzle_all_placed = all_matched
        self.solar_matrix_row_completed = [all_matched]
        self.solar_matrix_beam_alphas = [1.0 if all_matched else 0.0]

    def _place_piece_into_slot(self, piece, slot, spawn_fx=True):
        slot["matched"] = True
        slot["matched_piece"] = piece
        piece["is_placed"] = True
        piece["is_dragging"] = False
        piece["target_slot_id"] = slot["id"]
        piece["x"], piece["y"] = slot["drop_pos"]
        piece["rect"].topleft = (piece["x"], piece["y"])
        if self.selected_fraction_piece is piece:
            self.selected_fraction_piece = None
        self.fraction_match_feedback_kind = ""
        self.fraction_match_feedback_timer = 0.0

        if spawn_fx:
            if getattr(self, 'snap_sound', None):
                self.snap_sound.play()
            for _ in range(14):
                self.fraction_match_sparkles.append({
                    "x": slot["rect"].centerx + random.randint(-45, 45),
                    "y": slot["rect"].centery + random.randint(-30, 35),
                    "vx": random.uniform(-2.4, 2.4),
                    "vy": random.uniform(-3.2, 0.6),
                    "color": random.choice([(255, 215, 0), (74, 222, 128), (255, 255, 255), slot["color"]]),
                    "life": 0.55,
                    "max_life": 0.55,
                    "rad": random.randint(3, 5),
                })

        self._sync_fraction_match_completion_flags()
        if self.fraction_match_all_placed and spawn_fx:
            self.solar_array_puzzle_solved_time = pygame.time.get_ticks()
            if getattr(self, 'success_sound', None):
                self.success_sound.play()
            if hasattr(self, 'celebration_particles'):
                self.celebration_particles.spawn_burst(self.width // 2, self.height // 2, count=36)

    def reset_fraction_match(self):
        """Returns all fraction cards back to their tray slots."""
        for slot in self.fraction_match_slots:
            slot["matched"] = False
            slot["matched_piece"] = None
        for piece in self.fraction_match_pieces:
            piece["is_placed"] = False
            piece["is_dragging"] = False
            piece["target_slot_id"] = None
            piece["x"] = piece["orig_x"]
            piece["y"] = piece["orig_y"]
            piece["rect"].topleft = (piece["orig_x"], piece["orig_y"])
        self.dragged_fraction_piece = None
        self.dragged_bakery_slice = None
        self.dragged_solar_piece = None
        self.selected_fraction_piece = None
        self.mouse_drag_active = False
        self.fraction_match_feedback_kind = ""
        self.fraction_match_feedback_timer = 0.0
        self._sync_fraction_match_completion_flags()
        if getattr(self, 'snap_sound', None):
            self.snap_sound.play()

    def auto_solve_fraction_match(self):
        """Developer/test helper: snaps all 4 fraction cards into their matching slots."""
        self.reset_fraction_match()
        slot_by_id = {s["id"]: s for s in self.fraction_match_slots}
        for piece in self.fraction_match_pieces:
            target_slot = slot_by_id.get(piece["id"])
            if target_slot and not target_slot["matched"]:
                self._place_piece_into_slot(piece, target_slot, spawn_fx=False)
        if getattr(self, 'success_sound', None):
            self.success_sound.play()

    def close_fraction_match_modal(self):
        """Closes the Sun Temple Fraction Match modal and returns to desert exploration."""
        self.fraction_match_active = False
        self.fraction_bakery_active = False
        self.solar_array_puzzle_active = False
        self.dragged_fraction_piece = None
        self.dragged_bakery_slice = None
        self.dragged_solar_piece = None
        self.selected_fraction_piece = None
        self.mouse_drag_active = False
        self.guardian_skeleton_state = 1 if self.quiz_station_index >= 6 else 0
        self.guardian_skeleton_proximity_cooldown = 4.0

    def complete_fraction_match_trial(self):
        """Finalizes the Sun Temple Fraction Match, unlocks the Sun Portal, and saves progress."""
        self.fraction_match_solved = True
        self.fraction_bakery_solved = True
        self.solar_array_puzzle_solved = True
        self.fraction_match_all_placed = True
        self.solar_array_puzzle_all_placed = True
        self.fraction_match_active = False
        self.fraction_bakery_active = False
        self.solar_array_puzzle_active = False
        self.dragged_fraction_piece = None
        self.dragged_bakery_slice = None
        self.dragged_solar_piece = None
        self.selected_fraction_piece = None
        self.guardian_skeleton_state = 5
        self.quiz_state = 6 if self.quiz_station_index >= 6 else 0
        if self.quiz_station_index >= 6:
            self.clear_portal_overlapping_tiles()
            self.save_results_to_database()
        self.caravan_upgrade_banner_text = "SUN FRACTION MATCH SOLVED!"
        self.caravan_upgrade_banner_sub = "The Sun Portal is open - step through to complete Quarter 3!"
        self.caravan_upgrade_banner_timer = 6.0
        try:
            from db.save_system import save_student_progress
            save_student_progress(self.main_menu)
        except Exception as e:
            print(f"[WARN] Failed to save student progress: {e}")
        if getattr(self.main_menu, 'audio_manager', None):
            self.main_menu.audio_manager.play_sfx("victory_fanfare")
            self.main_menu.audio_manager.play_sfx("portal_warp")
        if hasattr(self, 'celebration_particles'):
            self.celebration_particles.spawn_burst(self.width // 2, self.height // 2, count=45)

    def handle_fraction_match_mouse_down(self, pos):
        """Handles click, select-and-slot, and drag initiation in Sun Temple Fraction Match."""
        if not (getattr(self, 'fraction_match_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'fraction_bakery_active', False)):
            return False

        # 1. Close / Back Buttons
        if getattr(self, 'fraction_match_close_btn_rect', None) and self.fraction_match_close_btn_rect.collidepoint(pos):
            self.close_fraction_match_modal()
            return True
        if getattr(self, 'fraction_match_x_btn_rect', None) and self.fraction_match_x_btn_rect.collidepoint(pos):
            self.close_fraction_match_modal()
            return True

        # 2. Reset Tray Button
        if getattr(self, 'fraction_match_reset_btn_rect', None) and self.fraction_match_reset_btn_rect.collidepoint(pos):
            self.reset_fraction_match()
            return True

        # 3. Unlock Sun Portal Button (active once 4/4 matched)
        if getattr(self, 'fraction_match_continue_btn_rect', None) and self.fraction_match_continue_btn_rect.collidepoint(pos):
            if self.fraction_match_all_placed or self.solar_array_puzzle_all_placed:
                self.complete_fraction_match_trial()
            return True

        # 4. Click on a Top-Row Target Slot when a card was selected via tap/click
        if self.selected_fraction_piece is not None and not self.selected_fraction_piece["is_placed"]:
            for slot in self.fraction_match_slots:
                if slot["rect"].collidepoint(pos):
                    if not slot["matched"] and slot["id"] == self.selected_fraction_piece["id"]:
                        self._place_piece_into_slot(self.selected_fraction_piece, slot, spawn_fx=True)
                    else:
                        self.fraction_match_feedback_kind = "wrong"
                        self.fraction_match_feedback_timer = 2.2
                        if getattr(self, 'snap_sound', None):
                            self.snap_sound.play()
                    return True

        # 5. Grab an Unplaced Card from the Tray (supports both Drag-and-Drop & Tap-to-Select)
        for piece in reversed(self.fraction_match_pieces):
            if not piece["is_placed"]:
                hit_rect = pygame.Rect(piece["x"], piece["y"], piece["w"], piece["h"])
                if hit_rect.collidepoint(pos):
                    self.dragged_fraction_piece = piece
                    self.dragged_bakery_slice = piece
                    self.dragged_solar_piece = piece
                    piece["is_dragging"] = True
                    self.mouse_drag_active = True
                    self.fraction_drag_start_pos = pos
                    self.fraction_drag_offset_x = pos[0] - piece["x"]
                    self.fraction_drag_offset_y = pos[1] - piece["y"]
                    self.solar_drag_offset_x = self.fraction_drag_offset_x
                    self.solar_drag_offset_y = self.fraction_drag_offset_y
                    if getattr(self, 'snap_sound', None):
                        self.snap_sound.play()
                    return True

        return False

    def release_dragged_fraction_piece(self):
        """Drops a dragged visual fraction card onto a matching slot, selects on tap, or bounces back."""
        piece = self.dragged_fraction_piece or self.dragged_solar_piece
        if not piece:
            return

        piece_center = (piece["x"] + piece["w"] // 2, piece["y"] + piece["h"] // 2)
        start_pos = getattr(self, 'fraction_drag_start_pos', None)
        cur_pos = self.cursor_pos

        # Check if piece center (or cursor) lands inside any top-row slot
        hit_slot = None
        for slot in self.fraction_match_slots:
            padded = slot["rect"].inflate(16, 20)
            if padded.collidepoint(piece_center):
                hit_slot = slot
                break

        if hit_slot is not None:
            if not hit_slot["matched"] and hit_slot["id"] == piece["id"]:
                self._place_piece_into_slot(piece, hit_slot, spawn_fx=True)
            else:
                piece["x"] = piece["orig_x"]
                piece["y"] = piece["orig_y"]
                piece["rect"].topleft = (piece["orig_x"], piece["orig_y"])
                piece["is_dragging"] = False
                self.fraction_match_feedback_kind = "wrong"
                self.fraction_match_feedback_timer = 2.2
                if getattr(self, 'snap_sound', None):
                    self.snap_sound.play()
        else:
            # If user tapped without dragging (< 12px movement), toggle Tap-to-Select for easy slot clicking
            moved_dist = math.hypot(cur_pos[0] - start_pos[0], cur_pos[1] - start_pos[1]) if start_pos else 999.0
            piece["x"] = piece["orig_x"]
            piece["y"] = piece["orig_y"]
            piece["rect"].topleft = (piece["orig_x"], piece["orig_y"])
            piece["is_dragging"] = False
            if moved_dist < 12.0:
                if self.selected_fraction_piece is piece:
                    self.selected_fraction_piece = None
                else:
                    self.selected_fraction_piece = piece
                    self.fraction_match_feedback_kind = ""
                    self.fraction_match_feedback_timer = 0.0
            elif getattr(self, 'snap_sound', None):
                self.snap_sound.play()

        self.dragged_fraction_piece = None
        self.dragged_bakery_slice = None
        self.dragged_solar_piece = None
        self.mouse_drag_active = False
        self._sync_fraction_match_completion_flags()

    def update_fraction_match(self, dt):
        """Updates sparkles, feedback timer, and MediaPipe closed-fist drag-and-drop."""
        if not (getattr(self, 'fraction_match_active', False) or getattr(self, 'solar_array_puzzle_active', False) or getattr(self, 'fraction_bakery_active', False)):
            return

        if self.fraction_match_feedback_timer > 0.0:
            self.fraction_match_feedback_timer = max(0.0, self.fraction_match_feedback_timer - dt)
            if self.fraction_match_feedback_timer <= 0.0:
                self.fraction_match_feedback_kind = ""

        for sp in self.fraction_match_sparkles[:]:
            sp["x"] += sp["vx"]
            sp["y"] += sp["vy"]
            sp["life"] -= dt
            if sp["life"] <= 0:
                self.fraction_match_sparkles.remove(sp)

        # MediaPipe Closed-Fist Hold Dragging Support
        if self.fist_closed and not self.dragged_fraction_piece and not self.fraction_match_all_placed:
            for piece in reversed(self.fraction_match_pieces):
                if not piece["is_placed"]:
                    p_rect = pygame.Rect(piece["x"], piece["y"], piece["w"], piece["h"])
                    if p_rect.collidepoint(self.cursor_pos):
                        self.dragged_fraction_piece = piece
                        self.dragged_bakery_slice = piece
                        self.dragged_solar_piece = piece
                        piece["is_dragging"] = True
                        self.fraction_drag_start_pos = self.cursor_pos
                        self.fraction_drag_offset_x = self.cursor_pos[0] - piece["x"]
                        self.fraction_drag_offset_y = self.cursor_pos[1] - piece["y"]
                        self.solar_drag_offset_x = self.fraction_drag_offset_x
                        self.solar_drag_offset_y = self.fraction_drag_offset_y
                        if getattr(self, 'snap_sound', None):
                            self.snap_sound.play()
                        break

        if self.dragged_fraction_piece:
            is_mouse_held = pygame.mouse.get_pressed()[0] if pygame.mouse.get_pressed() else False
            if self.fist_closed or is_mouse_held or getattr(self, 'mouse_drag_active', False):
                self.dragged_fraction_piece["x"] = self.cursor_pos[0] - self.fraction_drag_offset_x
                self.dragged_fraction_piece["y"] = self.cursor_pos[1] - self.fraction_drag_offset_y
            else:
                self.release_dragged_fraction_piece()

    # Backwards-Compatible Aliases
    def init_fraction_bakery(self):
        self.init_fraction_match()

    def reset_fraction_bakery(self):
        self.reset_fraction_match()

    def auto_solve_fraction_bakery(self):
        self.auto_solve_fraction_match()

    def handle_fraction_bakery_mouse_down(self, pos):
        return self.handle_fraction_match_mouse_down(pos)

    def release_dragged_bakery_slice(self):
        self.release_dragged_fraction_piece()

    def update_fraction_bakery(self, dt):
        self.update_fraction_match(dt)

    def init_solar_array_puzzle(self):
        self.init_fraction_match()

    def update_anubis_pan_slots(self):
        pass

    def reset_solar_array_puzzle(self):
        self.reset_fraction_match()

    def handle_solar_array_mouse_down(self, pos):
        handled = self.handle_fraction_match_mouse_down(pos)
        self.dragged_solar_piece = self.dragged_fraction_piece
        return handled

    def release_dragged_solar_piece(self):
        if not getattr(self, 'dragged_fraction_piece', None) and getattr(self, 'dragged_solar_piece', None):
            self.dragged_fraction_piece = self.dragged_solar_piece
        self.release_dragged_fraction_piece()

    def auto_solve_solar_array_puzzle(self):
        self.auto_solve_fraction_match()

    def update_solar_array_puzzle(self, dt):
        self.update_fraction_match(dt)

    @property
    def skeleton_guardian_x(self):
        return getattr(self, 'npc_skeleton_x', 0)

    @property
    def skeleton_guardian_y(self):
        return getattr(self, 'npc_skeleton_y', 0)

    def draw_skeleton_guardian(self):
        """Draws the Skeleton Portal Guardian with interactive indicator and direction"""
        import math, pygame
        if not getattr(self, 'npc_skeleton_found', False):
            return

        screen_x = (self.npc_skeleton_x - self.camera_x) * ZOOM
        screen_y = (self.npc_skeleton_y - self.camera_y) * ZOOM

        skeleton_sprite = self.npc_skeleton_sprite
        if self.npc_skeleton_dir == "left" and self.npc_skeleton_left_sprites:
            skeleton_sprite = self.npc_skeleton_left_sprites[self.npc_skeleton_anim_frame % len(self.npc_skeleton_left_sprites)]
        elif self.npc_skeleton_dir == "right" and self.npc_skeleton_right_sprites:
            skeleton_sprite = self.npc_skeleton_right_sprites[self.npc_skeleton_anim_frame % len(self.npc_skeleton_right_sprites)]
        elif self.npc_skeleton_dir == "up" and self.npc_skeleton_up_sprites:
            skeleton_sprite = self.npc_skeleton_up_sprites[self.npc_skeleton_anim_frame % len(self.npc_skeleton_up_sprites)]
        elif self.npc_skeleton_dir == "down" and self.npc_skeleton_down_sprites:
            skeleton_sprite = self.npc_skeleton_down_sprites[self.npc_skeleton_anim_frame % len(self.npc_skeleton_down_sprites)]

        if skeleton_sprite:
            self.screen.blit(skeleton_sprite, (screen_x, screen_y))

        # Golden/Emerald Floor Aura when awaiting challenge or ready to talk
        if self.guardian_skeleton_state in [0, 1, 5]:
            pulse = (math.sin(self.frame_counter * 0.12) + 1) * 0.5
            if self.guardian_skeleton_state == 5:
                aura_alpha = int(70 + 40 * pulse)
                aura_col = (74, 222, 128)
            elif self.guardian_skeleton_state == 1:
                aura_alpha = int(90 + 70 * pulse)
                aura_col = (255, 215, 0)
            else:
                aura_alpha = int(50 + 40 * pulse)
                aura_col = (255, 215, 0)

            q_alpha = (aura_alpha // 10) * 10
            aura_key = (aura_col, q_alpha)
            aura_surf = self._skel_aura_cache.get(aura_key)
            if aura_surf is None:
                aura_w, aura_h = int(36 * ZOOM), int(16 * ZOOM)
                aura_surf = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)
                pygame.draw.ellipse(aura_surf, (*aura_col, q_alpha), (0, 0, aura_w, aura_h))
                if pygame.display.get_surface() is not None:
                    aura_surf = aura_surf.convert_alpha()
                self._skel_aura_cache[aura_key] = aura_surf
            self.screen.blit(aura_surf, (screen_x - int(2 * ZOOM), screen_y + int(22 * ZOOM)))

            # Floating Quest Indicator / Talk Bubble above Skeleton
            bob = math.sin(self.frame_counter * 0.15) * 3 * ZOOM
            player_center_x = self.player_x + TILE_SIZE // 2
            player_center_y = self.player_y + TILE_SIZE // 2
            skel_center_x = self.npc_skeleton_x + TILE_SIZE // 2
            skel_center_y = self.npc_skeleton_y + TILE_SIZE // 2
            is_near = math.hypot(player_center_x - skel_center_x, player_center_y - skel_center_y) < TILE_SIZE * 3.5

            if is_near and not getattr(self, 'fraction_match_active', False) and not getattr(self, 'fraction_bakery_active', False) and not getattr(self, 'solar_array_puzzle_active', False) and self.guardian_skeleton_state != 2:
                # Nearby interaction prompt badge
                prompt_txt = "[E / Click] Replay Fraction Match" if self.guardian_skeleton_state == 5 else "[E / Click] Talk: Sun Fraction Match"
                p_surf = self.get_ui_font(11, bold=True).render(prompt_txt, True, (15, 23, 42))
                pw, ph = p_surf.get_width() + 16, p_surf.get_height() + 8
                px = screen_x + (TILE_SIZE * ZOOM) / 2 - pw / 2
                py = screen_y - 28 * ZOOM + bob
                p_rect = pygame.Rect(px, py, pw, ph)
                pygame.draw.rect(self.screen, (74, 222, 128) if self.guardian_skeleton_state == 5 else (255, 215, 0), p_rect, border_radius=6)
                pygame.draw.rect(self.screen, (255, 255, 255), p_rect, 1, border_radius=6)
                self.screen.blit(p_surf, p_surf.get_rect(center=p_rect.center))
            elif self.guardian_skeleton_state == 1:
                badge_x = screen_x + (TILE_SIZE * ZOOM) / 2 - 8 * ZOOM
                badge_y = screen_y - 20 * ZOOM + bob
                badge_rect = pygame.Rect(badge_x, badge_y, 16 * ZOOM, 16 * ZOOM)
                pygame.draw.rect(self.screen, (255, 215, 0), badge_rect, border_radius=4)
                pygame.draw.rect(self.screen, (0, 0, 0), badge_rect, 1, border_radius=4)
                excl_surf = self.font.render("!", True, (0, 0, 0))
                self.screen.blit(excl_surf, excl_surf.get_rect(center=badge_rect.center))

    def draw_skeleton_guardian_prompt(self):
        """High-Engagement RPG Dialogue Modal when talking to the Skeleton Guardian"""
        if not hasattr(self, '_skel_prompt_dim') or self._skel_prompt_dim.get_size() != (self.width, self.height):
            s = pygame.Surface((self.width, self.height))
            s.fill((10, 15, 29))
            if pygame.display.get_surface() is not None:
                s = s.convert()
            s.set_alpha(185)
            self._skel_prompt_dim = s
        self.screen.blit(self._skel_prompt_dim, (0, 0))

        box_w = min(860, self.width - 40)
        box_h = 370
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Outer Temple Sanctuary Card with warm Egyptian bronze & gold filigree
        pygame.draw.rect(self.screen, (0, 0, 0, 160), (box_x + 6, box_y + 6, box_w, box_h), border_radius=18)
        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=18)
        pygame.draw.rect(self.screen, (217, 119, 6), dialog_rect, 3, border_radius=18)
        pygame.draw.rect(self.screen, (253, 224, 71), dialog_rect.inflate(-6, -6), 1, border_radius=14)

        # Top Header Bar
        hdr_rect = pygame.Rect(box_x + 3, box_y + 3, box_w - 6, 44)
        pygame.draw.rect(self.screen, (30, 41, 59), hdr_rect, border_top_left_radius=16, border_top_right_radius=16)
        pygame.draw.line(self.screen, (217, 119, 6), (box_x + 4, box_y + 47), (box_x + box_w - 4, box_y + 47), 2)

        hdr_title = self.dialog_header_font.render("Sun Temple Fraction Match - Guardian Encounter", True, (253, 224, 71))
        self.screen.blit(hdr_title, (box_x + 22, box_y + 10))

        # Close [✕] Button in Top-Right
        x_btn_rect = pygame.Rect(box_x + box_w - 38, box_y + 8, 28, 28)
        self.guardian_skeleton_x_btn_rect = x_btn_rect
        is_x_hov = x_btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if is_x_hov else (51, 65, 85), x_btn_rect, border_radius=6)
        x_surf = self.get_ui_font(13, bold=True).render("✕", True, (255, 255, 255))
        self.screen.blit(x_surf, x_surf.get_rect(center=x_btn_rect.center))

        # LEFT COLUMN: Skeleton Guardian Illuminated Shrine Portrait
        shrine_w, shrine_h = 140, 190
        shrine_x = box_x + 24
        shrine_y = box_y + 64
        shrine_rect = pygame.Rect(shrine_x, shrine_y, shrine_w, shrine_h)
        pygame.draw.rect(self.screen, (24, 32, 47), shrine_rect, border_radius=12)
        pygame.draw.rect(self.screen, (217, 119, 6), shrine_rect, 2, border_radius=12)
        pygame.draw.rect(self.screen, (253, 224, 71), shrine_rect.inflate(-4, -4), 1, border_radius=10)

        # Subtle golden sun backglow behind guardian
        pulse = (math.sin(self.frame_counter * 0.12) + 1) * 0.5
        sun_alpha = (int(40 + 35 * pulse) // 7) * 7
        sun_surf = self._skel_sun_cache.get(sun_alpha)
        if sun_surf is None:
            sun_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(sun_surf, (245, 158, 11, sun_alpha), (40, 40), 38)
            if pygame.display.get_surface() is not None:
                sun_surf = sun_surf.convert_alpha()
            self._skel_sun_cache[sun_alpha] = sun_surf
        self.screen.blit(sun_surf, (shrine_x + (shrine_w - 80) // 2, shrine_y + 14))

        # Draw Skeleton Sprite
        skel_sprite = getattr(self, 'npc_skeleton_sprite', None)
        if skel_sprite:
            if self._skel_portrait_surf is None:
                p_img = pygame.transform.scale(skel_sprite, (84, 84))
                if pygame.display.get_surface() is not None:
                    p_img = p_img.convert_alpha()
                self._skel_portrait_surf = p_img
            self.screen.blit(self._skel_portrait_surf, (shrine_x + (shrine_w - 84) // 2, shrine_y + 16))

        # Speaker Name Badge below portrait
        spk_tag = self.get_ui_font(11, bold=True).render("Skeleton Guardian", True, (255, 215, 0))
        role_tag = self.get_ui_font(10).render("Portal Keeper", True, (203, 213, 225))
        self.screen.blit(spk_tag, spk_tag.get_rect(center=(shrine_x + shrine_w // 2, shrine_y + 130)))
        self.screen.blit(role_tag, role_tag.get_rect(center=(shrine_x + shrine_w // 2, shrine_y + 155)))

        # RIGHT COLUMN: Spoken Dialogue & Context
        diag_x = shrine_x + shrine_w + 24
        diag_w = box_w - shrine_w - 72

        if getattr(self, 'fraction_match_solved', False) or getattr(self, 'fraction_bakery_solved', False) or getattr(self, 'solar_array_puzzle_solved', False):
            greeting = f"Champion of the Sun Temple, courageous adventurer {self.player_name}!"
            body = ("Your mastery of Fractions (Halves, Thirds, and Fourths) has restored all four Sun Relic slots! "
                    "The ancient shadow seal is broken, and the Desert Sun Portal is active! "
                    "Step through the portal to complete your journey, or replay the Fraction Match anytime!")
            btn_label = "Replay Fraction Match >>"
        elif self.quiz_station_index >= 6:
            tot_st = getattr(self, 'active_station_count', len(self.quiz_questions))
            greeting = f"Halt, victorious traveler {self.player_name}!"
            if tot_st == 0:
                body = ("No cloud station questions were set for this stage! To break the ancient shadow seal on this Portal, "
                        "complete the Sun Temple Fraction Match! Match each shaded shape card to its fraction slot "
                        "(1/2, 1/3, 2/3, 1/4, 3/4) to open the Sun Gate!")
            else:
                body = (f"You have conquered all {tot_st} Desert Station challenge(s)! To break the ancient shadow seal on this Portal, "
                        "complete the Sun Temple Fraction Match! Match each shaded shape card to its fraction slot "
                        "(1/2, 1/3, 2/3, 1/4, 3/4) to open the Sun Gate!")
            btn_label = "Begin Fraction Match >>"
        else:
            tot_st = getattr(self, 'active_station_count', len(self.quiz_questions))
            greeting = f"Greetings, brave traveler {self.player_name}!"
            body = (f"I am the Ancient Guardian of the Sun Temple Portal. While you still have "
                    f"station challenges remaining ({max(0, tot_st - (self.quiz_station_index - 1))} left), you may try "
                    f"the Sun Temple Fraction Match right now to practice matching visual Halves, Thirds, and Fourths!")
            btn_label = "Begin Fraction Match >>"

        g_surf = self.dialog_header_font.render(greeting, True, (255, 215, 0))
        self.screen.blit(g_surf, (diag_x, box_y + 68))

        lines = self.wrap_text(body, self.dialog_q_font, diag_w)
        text_y = box_y + 104
        for line in lines[:5]:
            line_surf = self.dialog_q_font.render(line, True, (241, 245, 249))
            self.screen.blit(line_surf, (diag_x, text_y))
            text_y += 26

        # -------------------------------------------------------------
        # ACTION BUTTONS AT BOTTOM
        # -------------------------------------------------------------
        # 1. Main Trial Button (Fist hold / Space / Click)
        btn_w, btn_h = 380, 52
        btn_x = diag_x
        btn_y = box_y + box_h - 76
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        self.guardian_skeleton_btn_rect = btn_rect

        is_hovered = btn_rect.collidepoint(self.cursor_pos)
        fist_pct = getattr(self, 'guardian_fist_pct', 0.0)

        bg_col = (245, 158, 11) if is_hovered else (217, 119, 6)
        pygame.draw.rect(self.screen, (0, 0, 0, 100), btn_rect.move(2, 2), border_radius=12)
        pygame.draw.rect(self.screen, bg_col, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255) if is_hovered else (253, 224, 71), btn_rect, 2, border_radius=12)

        # Fist Hold Progress Fill
        if fist_pct > 0.0:
            fill_w = int(btn_w * min(1.0, fist_pct))
            if fill_w > 0:
                if not hasattr(self, '_guardian_fill_surf') or self._guardian_fill_surf.get_size() != (btn_w, btn_h):
                    fs = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                    fs.fill((255, 255, 255, 90))
                    if pygame.display.get_surface() is not None:
                        fs = fs.convert_alpha()
                    self._guardian_fill_surf = fs
                self.screen.blit(self._guardian_fill_surf, (btn_x, btn_y), (0, 0, fill_w, btn_h))

        btn_txt = self.get_ui_font(14, bold=True).render(btn_label, True, (15, 23, 42) if is_hovered else (255, 255, 255))
        self.screen.blit(btn_txt, btn_txt.get_rect(center=(btn_rect.centerx, btn_rect.centery - 8)))

        sub_label = f"Holding Fist: {int(fist_pct * 100)}%" if fist_pct > 0 else "[Press Space / E / Click / Hold Fist]"
        sub_txt = self.get_ui_font(10).render(sub_label, True, (254, 240, 138))
        self.screen.blit(sub_txt, sub_txt.get_rect(center=(btn_rect.centerx, btn_rect.centery + 14)))

        # 2. Return to Desert / Dismiss Button
        cls_w, cls_h = 190, 52
        cls_x = btn_x + btn_w + 16
        cls_y = btn_y
        cls_rect = pygame.Rect(cls_x, cls_y, cls_w, cls_h)
        self.guardian_skeleton_close_btn_rect = cls_rect

        cls_hov = cls_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if cls_hov else (30, 41, 59), cls_rect, border_radius=12)
        pygame.draw.rect(self.screen, (203, 213, 225) if cls_hov else (100, 116, 139), cls_rect, 1, border_radius=12)
        cls_txt = self.get_ui_font(12, bold=True).render("Back to Desert [Esc]", True, (241, 245, 249))
        self.screen.blit(cls_txt, cls_txt.get_rect(center=cls_rect.center))

    def draw_fraction_match(self):
        """Renders the single-round 4-Card Sun Temple Fraction Match using 100% pre-baked surfaces."""
        if not getattr(self, 'fraction_match_slots', None) or getattr(self, '_fraction_match_panel_surf', None) is None:
            self.init_fraction_match()

        # 1. Cached Dim Overlay (.convert() + set_alpha)
        if getattr(self, '_fraction_match_dim_overlay', None) is None or self._fraction_match_dim_overlay.get_size() != (self.width, self.height):
            s = pygame.Surface((self.width, self.height))
            s.fill((10, 15, 29))
            if pygame.display.get_surface() is not None:
                s = s.convert()
            s.set_alpha(230)
            self._fraction_match_dim_overlay = s
        self.screen.blit(self._fraction_match_dim_overlay, (0, 0))

        # 2. Pre-baked Main Modal Panel
        panel_r = self.fraction_match_panel_rect
        px, py = panel_r.x, panel_r.y
        self.screen.blit(self._fraction_match_panel_surf, (px, py))

        cur = self.cursor_pos
        btns = self._fm_btn_surfs
        dragged_piece = self.dragged_fraction_piece or self.dragged_solar_piece
        selected_piece = self.selected_fraction_piece
        drag_center = (
            (int(dragged_piece["x"]) + dragged_piece["w"] // 2, int(dragged_piece["y"]) + dragged_piece["h"] // 2)
            if dragged_piece is not None else None
        )

        # 3. Close [X] Button
        x_r = self.fraction_match_x_btn_rect
        self.screen.blit(btns["x_hov" if x_r.collidepoint(cur) else "x_norm"], x_r.topleft)

        # 4. Top-Row Sun Altar Fraction Slots
        matched_cnt = 0
        for slot in self.fraction_match_slots:
            if slot["matched"]:
                matched_cnt += 1
                self.screen.blit(slot["matched_surf"], slot["rect"].topleft)
            else:
                is_slot_hov = (
                    (drag_center is not None and slot["rect"].inflate(16, 20).collidepoint(drag_center))
                    or (selected_piece is not None and slot["rect"].collidepoint(cur))
                )
                self.screen.blit(slot["hover_surf" if is_slot_hov else "empty_surf"], slot["rect"].topleft)

        # 5. Placed Visual Cards Inside Matched Slots
        for piece in self.fraction_match_pieces:
            if piece["is_placed"] and piece is not dragged_piece:
                self.screen.blit(piece["placed_surf"], (int(piece["x"]), int(piece["y"])))

        # 6. Pre-baked Status / Feedback Hint Line Above Tray
        if self.fraction_match_feedback_timer > 0.0 and self.fraction_match_feedback_kind == "wrong":
            st_surf = self._fm_wrong_hint_surf
        elif selected_piece is not None and not selected_piece["is_placed"]:
            st_surf = self._fm_selected_hint_surf
        else:
            st_surf = self._fm_status_surfs.get(matched_cnt)
        if st_surf is not None:
            self.screen.blit(st_surf, (px + (panel_r.w - st_surf.get_width()) // 2, py + 317))

        # 7. Unplaced Visual Shape Cards in Bottom Tray
        for piece in self.fraction_match_pieces:
            if not piece["is_placed"] and piece is not dragged_piece:
                ix, iy = int(piece["x"]), int(piece["y"])
                pygame.draw.rect(self.screen, (6, 10, 20), (ix + 3, iy + 4, piece["w"], piece["h"]), border_radius=10)
                if selected_piece is piece:
                    c_surf = piece["selected_surf"]
                elif piece["rect"].collidepoint(cur):
                    c_surf = piece["hover_surf"]
                else:
                    c_surf = piece["token_surf"]
                self.screen.blit(c_surf, (ix, iy))

        # 8. Bottom Control Buttons
        cls_r = self.fraction_match_close_btn_rect
        self.screen.blit(btns["close_hov" if cls_r.collidepoint(cur) else "close_norm"], cls_r.topleft)

        rst_r = self.fraction_match_reset_btn_rect
        self.screen.blit(btns["reset_hov" if rst_r.collidepoint(cur) else "reset_norm"], rst_r.topleft)

        cont_r = self.fraction_match_continue_btn_rect
        if self.fraction_match_all_placed or self.solar_array_puzzle_all_placed:
            self.screen.blit(btns["unlock_hov" if cont_r.collidepoint(cur) else "unlock_ready"], cont_r.topleft)
            if (self.frame_counter // 18) % 2 == 0:
                pygame.draw.rect(self.screen, (254, 240, 138), cont_r.inflate(4, 4), 2, border_radius=11)
        else:
            self.screen.blit(btns["unlock_locked"], cont_r.topleft)

        # 9. Active Dragged Card (Rendered on Top)
        if dragged_piece is not None:
            dx, dy = int(dragged_piece["x"]), int(dragged_piece["y"])
            pygame.draw.rect(self.screen, (6, 10, 20), (dx + 6, dy + 6, dragged_piece["w"], dragged_piece["h"]), border_radius=10)
            self.screen.blit(dragged_piece["hover_surf"], (dx, dy))

        # 10. Snap Sparkle Particles
        for sp in self.fraction_match_sparkles:
            life_pct = max(0.0, min(1.0, sp["life"] / sp["max_life"]))
            r = max(1, int(sp["rad"] * life_pct))
            pygame.draw.circle(self.screen, sp["color"], (int(sp["x"]), int(sp["y"])), r)

    def draw_fraction_bakery(self):
        """Backwards-compatible alias for Sun Temple Fraction Match rendering."""
        self.draw_fraction_match()

    def draw_solar_array_puzzle(self):
        """Backwards-compatible alias for Sun Temple Fraction Match rendering."""
        self.draw_fraction_match()

    def wrap_text(self, text, font, max_width):
        from core.font_manager import wrap_multiline_text
        return wrap_multiline_text(text, font, max_width)

    # ============================================================

    # SUN RELIC ALTAR SOUND SYNTHESIS
    # ============================================================
    def load_puzzle_sounds(self):
        try:
            am = getattr(self.main_menu, 'audio_manager', None) if hasattr(self, 'main_menu') else None
            if am:
                self.snap_sound = am.get_sound("snap")
                self.success_sound = am.get_sound("success")
            else:
                from core.audio_manager import audio_manager
                self.snap_sound = audio_manager.get_sound("snap") if audio_manager else None
                self.success_sound = audio_manager.get_sound("success") if audio_manager else None
            if not self.snap_sound:
                self.snap_sound = self.generate_snap_sound()
            if not self.success_sound:
                self.success_sound = self.generate_success_sound()
            print("[AUDIO] Sun Relic sound effects synthesized successfully.")
        except Exception as e:
            print(f"[WARN] Error loading puzzle sounds: {e}")
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

    def get_ui_font(self, size, bold=False):
        """Returns a high-legibility system font for UI elements"""
        from core.font_manager import get_font
        return get_font(["Segoe UI", "Tahoma", "Verdana", "Calibri", "Arial", "Comic Sans MS"], size, bold=bold)

    def draw_offscreen_compass_pointer(self):
        """Draw Active Objective NPC Indicator and Off-Screen Compass Pointer for Quarter 3"""
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

            excl_font = get_font("Comic Sans MS", int(14 * ZOOM), bold=True)
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

            tag_bg = self._npc_tag_bg_cache.get((tag_w, tag_h))
            if tag_bg is None:
                tag_bg = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
                tag_bg.fill((15, 23, 42, 210))
                if pygame.display.get_surface() is not None:
                    tag_bg = tag_bg.convert_alpha()
                self._npc_tag_bg_cache[(tag_w, tag_h)] = tag_bg
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

        # Translucent Background (cached)
        self.screen.blit(self._hud_timer_surf, (hud_x, hud_y))
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
        if self._dim_overlay is None or self._dim_overlay.get_size() != (self.width, self.height):
            self._dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dim_overlay.fill((0, 0, 0, 180))
        self.screen.blit(self._dim_overlay, (0, 0))

        box_w, box_h = 700, 320
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (15, 23, 42), (box_x, box_y, box_w, box_h), border_radius=16)
        pygame.draw.rect(self.screen, (239, 68, 68), (box_x, box_y, box_w, box_h), 3, border_radius=16)

        t_font = self.get_ui_font(28, bold=True)
        msg_font = self.get_ui_font(20, bold=True)
        btn_font = self.get_ui_font(19, bold=True)

        title = t_font.render("TIME'S UP!", True, (239, 68, 68))
        self.screen.blit(title, title.get_rect(center=(box_x + box_w // 2, box_y + 45)))

        m1 = msg_font.render("Your 10-minute stage time limit has expired.", True, (255, 255, 255))
        m2 = msg_font.render("Would you like to try again or return to Stage Select?", True, (203, 213, 225))
        self.screen.blit(m1, m1.get_rect(center=(box_x + box_w // 2, box_y + 105)))
        self.screen.blit(m2, m2.get_rect(center=(box_x + box_w // 2, box_y + 145)))

        # Button 1: Retry Quarter
        retry_rect = pygame.Rect(box_x + 50, box_y + 225, 270, 52)
        r_hov = retry_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (245, 158, 11) if r_hov else (30, 41, 59), retry_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), retry_rect, 2, border_radius=12)
        r_txt = btn_font.render("Retry Quarter", True, (15, 23, 42) if r_hov else (255, 255, 255))
        self.screen.blit(r_txt, r_txt.get_rect(center=retry_rect.center))

        # Button 2: Return to Stage Select
        exit_rect = pygame.Rect(box_x + box_w - 320, box_y + 225, 270, 52)
        e_hov = exit_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if e_hov else (30, 41, 59), exit_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), exit_rect, 2, border_radius=12)
        e_txt = btn_font.render("Stage Select", True, (255, 255, 255))
        self.screen.blit(e_txt, e_txt.get_rect(center=exit_rect.center))

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        self._bg_map_surface = None
        self._fg_obstacles_surface = None
        self._fraction_match_panel_surf = None
        self._fraction_match_dim_overlay = None
        if hasattr(self, '_fm_btn_surfs'):
            self._fm_btn_surfs.clear()
        if hasattr(self, '_fm_status_surfs'):
            self._fm_status_surfs.clear()
        self.fraction_match_slots = []
        self.fraction_match_pieces = []
        if hasattr(self, '_scaled_tile_cache'):
            self._scaled_tile_cache.clear()
        if hasattr(self, '_scaled_sprite_cache'):
            self._scaled_sprite_cache.clear()
        from core.font_manager import trim_transient_font_caches
        trim_transient_font_caches()
        cv2.destroyAllWindows()