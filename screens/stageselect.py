# screens/stageselect.py - Stage Selection Screen (Using Main Menu's Gesture System)

import pygame
import os
import sys
import cv2
import numpy as np
import time
import math
import random
from screens.map_loader import MapLoader
from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4
from core.camera_system import LoLCamera

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
    'right': (2, 3),  # 2 tiles wide, 3 tiles tall (vertical strip matching east corridor)
    'left': (2, 3),   # 2 tiles wide, 3 tiles tall (vertical strip matching west corridor)
    'up': (3, 2),     # 3 tiles wide, 2 tiles tall (horizontal strip matching south corridor)
    'down': (3, 2)    # 3 tiles wide, 2 tiles tall (horizontal strip matching north corridor)
}


class StageSelect:
    def __init__(self, screen, main_menu):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()

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
        self.locked_portal_banner_msg = ""
        self.locked_portal_banner_timer = 0.0

        # Grand Finale Celebration State
        self.grand_finale_active = False
        self.grand_finale_dismissed = False
        self.grand_finale_fanfare_played = False
        self.confetti_particles = []

        from db.save_system import get_completed_quarters, is_game_completed
        student_id = getattr(self.main_menu, 'student_id', None)
        self.completed_quarters = get_completed_quarters(student_id)
        if is_game_completed(student_id):
            self.grand_finale_active = True

        # Portal Warp Screen Transition State (3-Second Black Loading Screen)
        self.portal_transition_active = False
        self.portal_transition_timer = 0.0
        self.portal_transition_duration = 3.0
        self.portal_transition_target = None
        self.portal_transition_origin = (self.width // 2, self.height // 2)
        self.portal_transition_particles = []
        self.portal_transition_stars = []
        self.portal_transition_theme = None
        self.portal_transition_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.portal_loaded_screen = None
        self.portal_loading_done = False

        # Typewriter Dialogue State
        self.dialogue_char_index = 0.0
        self.dialogue_typing_speed = 38.0  # characters per second
        self.dialogue_active_key = None
        self.dialogue_sound_timer = 0.0

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

        self.MAP_PATH = os.path.join(self.BASE_DIR, "assets", "map", "map.txt")

        # ============================================================
        # MAP LOADER
        # ============================================================
        self.map_loader = MapLoader(self.BASE_DIR)

        # Load initial map (map.txt)
        if not self.map_loader.load_map("map.txt"):
            # Fallback to default map if loading fails
            self._create_default_map()
        else:
            # Use the loaded map data
            self.game_map = self.map_loader.game_map
            self.ROWS = self.map_loader.rows
            self.COLS = self.map_loader.cols
            self.MAP_WIDTH = self.COLS * TILE_SIZE
            self.MAP_HEIGHT = self.ROWS * TILE_SIZE

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
        # Seamless grass fallback so missing/unmapped characters never show error boxes
        self.fallback_tile = self.tile_images.get('G')
        if not self.fallback_tile:
            self.fallback_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.fallback_tile.fill((34, 197, 94))

        # ============================================================
        # WALKABLE TILES
        # ============================================================
        self.WALKABLE_TILES = {"G", "#", "1", "2", "3", "4", "5", "6", "7", "8", "P", "l", "r", "u", "d"}

        # ============================================================
        # LOAD PLAYER SPRITES
        # ============================================================
        self.player_sprites = self.load_player_sprites()
        self.anim_frame = 0
        self.anim_timer = 0

        # ============================================================
        # LOAD NPC SPRITES
        # ============================================================
        # Bromen NPC (animated & interactive)
        self.npc_bromen_sprites = self.load_npc_sprites_animated(self.NPC_PATH_BROMEN, "bromen")
        self.npc_bromen_teleport_sprites = self.load_bromen_teleport_sprites()
        self.npc_bromen_up_sprites = []
        self.npc_bromen_dir = "down"
        self.npc_bromen_anim_frame = 0
        self.npc_bromen_anim_timer = 0
        self.npc_bromen_x = 0
        self.npc_bromen_y = 0
        self.npc_bromen_tile_x = 0
        self.npc_bromen_tile_y = 0
        self.npc_bromen_found = False
        self.bromen_dialogue_state = 0  # 0: idle, 1: dialogue active, 2: walking to portal, 3: disappeared
        self.bromen_dialogue_index = 0
        self.bromen_teleport_frame = 0
        self.bromen_teleport_timer = 0
        self.player_following_target = None  # 'oldman', 'skeleton', 'knight', 'bromen', or None
        self.bromen_dialogue_lines = [
            ("Bromen", "Greetings! I am Bromen, master of the final realm."),
            ("Student", "Are you guarding the entrance to Quarter 4?"),
            ("Bromen", "Indeed! Follow me to the north portal to enter Quarter 4."),
            ("Bromen", "Let us go!")
        ]

        # Oldman NPC (static & interactive)
        self.npc_oldman_sprite = None
        self.npc_oldman_x = 0
        self.npc_oldman_y = 0
        self.npc_oldman_tile_x = 0
        self.npc_oldman_tile_y = 0
        self.npc_oldman_found = False
        self.oldman_dialogue_state = 0  # 0: idle, 1: dialogue active, 2: walking, 3: disappeared
        self.oldman_dialogue_index = 0
        self.npc_oldman_left_sprites = []
        self.npc_oldman_down_sprites = []
        self.npc_oldman_right_sprites = []
        self.npc_oldman_up_sprites = []
        self.npc_oldman_dir = "down"
        self.npc_oldman_anim_frame = 0
        self.npc_oldman_anim_timer = 0
        self.player_block_timer = 0
        self.dialogue_lines = [
            ("Old Man", "Ah, young adventurer! You look brave and clever."),
            ("Old Man", "Deep inside the Geometry Forest, the magical Shapes have become lost. Only a true student adventurer can help them find their way."),
            ("Old Man", "Do you want to explore the Geometry Forest?"),
            ("Student", "Yes! I'll help!"),
            ("Old Man", "Excellent! Along the way, you must answer my questions about shapes and angles. If you answer correctly, the forest will guide you safely to the next path."),
            ("Old Man", "Stay sharp, observe carefully, and remember what you have learned."),
            ("Old Man", "Now... Follow me!")
        ]

        # Skeleton NPC (static & interactive)
        self.npc_skeleton_sprite = None
        self.npc_skeleton_x = 0
        self.npc_skeleton_y = 0
        self.npc_skeleton_tile_x = 0
        self.npc_skeleton_tile_y = 0
        self.npc_skeleton_found = False
        self.skeleton_dialogue_state = 0  # 0: idle, 1: dialogue active, 2: walking, 3: disappeared
        self.skeleton_dialogue_index = 0
        self.npc_skeleton_left_sprites = []
        self.npc_skeleton_down_sprites = []
        self.npc_skeleton_right_sprites = []
        self.npc_skeleton_up_sprites = []
        self.npc_skeleton_dir = "down"
        self.npc_skeleton_anim_frame = 0
        self.npc_skeleton_anim_timer = 0
        self.skeleton_dialogue_lines = [
            ("Skeleton", "Hi"),
            ("Student", "Hello")
        ]

        # Knight NPC (static & interactive)
        self.npc_knight_sprite = None
        self.npc_knight_x = 0
        self.npc_knight_y = 0
        self.npc_knight_tile_x = 0
        self.npc_knight_tile_y = 0
        self.npc_knight_found = False
        self.knight_dialogue_state = 0  # 0: idle, 1: dialogue active, 2: walking, 3: disappeared
        self.knight_dialogue_index = 0
        self.npc_knight_left_sprites = []
        self.npc_knight_down_sprites = []
        self.npc_knight_right_sprites = []
        self.npc_knight_up_sprites = []
        self.npc_knight_dir = "down"
        self.npc_knight_anim_frame = 0
        self.npc_knight_anim_timer = 0
        self.knight_dialogue_lines = [
            ("Knight", "Halt, student! Beyond this portal lies Quarter 2."),
            ("Student", "I am ready for the challenge!"),
            ("Knight", "Walk through the portal down below to proceed. Best of luck!")
        ]

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

        # Initialize NPC positions from map data
        self._init_npc_positions()

        # Center camera directly on player spawn without sliding
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

        # ============================================================
        # UI
        # ============================================================
        self.show_info = True
        self.font = pygame.font.SysFont("Comic Sans MS", 16)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 12)

        # Clock for delta time
        self.clock = pygame.time.Clock()
        self.frame_counter = 0

        print(f"[OK] StageSelect initialized with map: {self.ROWS}x{self.COLS}")
        print(f"   Walkable tiles: {self.WALKABLE_TILES}")
        print(f"   Portals loaded: {len(self.portals)}")
        print(f"   Bromen NPC found: {self.npc_bromen_found}")
        print(f"   Oldman NPC found: {self.npc_oldman_found}")
        print(f"   Skeleton NPC found: {self.npc_skeleton_found}")
        print(f"   Knight NPC found: {self.npc_knight_found}")

        # ============================================================
        # AREA TITLE ANIMATION (test.py logic)
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

        self.title_text = "Spawn Plains"
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

    # ============================================================
    # NEW METHOD - Create default map
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
    # NEW METHOD - Initialize NPC positions
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
        def load_tile(filename):
            path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                image = pygame.image.load(path).convert_alpha()
                image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
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
            print(f"[WARNING] NPC path does not exist: {npc_path}")
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

    def load_bromen_teleport_sprites(self):
        frames = []
        for i in range(8):
            filename = f"sprite_bromen_teleport{i:02d}.png"
            path = os.path.join(self.NPC_PATH_BROMEN, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                frames.append(scaled)
                print(f"[OK] Loaded Bromen teleport frame: {filename}")
        return frames

    # ============================================================
    # LOAD STATIC NPC SPRITES (Oldman, Skeleton, Knight)
    # ============================================================
    def load_static_npc_sprites(self):
        # Load Bromen walking up sprites
        self.npc_bromen_up_sprites = []
        for name in ["bromen_up_1.png", "bromen_up_2.png"]:
            path = os.path.join(self.NPC_PATH_BROMEN, name)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.npc_bromen_up_sprites.append(scaled)
                print(f"[OK] Loaded Bromen up frame: {name}")

        # Load Oldman
        oldman_path = os.path.join(self.NPC_PATH_OLDMAN, "oldman.png")
        try:
            if os.path.exists(oldman_path):
                img = pygame.image.load(oldman_path).convert_alpha()
                self.npc_oldman_sprite = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                print(f"[OK] Loaded Oldman sprite")
            else:
                print(f"[WARNING] Oldman sprite not found at: {oldman_path}")
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((200, 200, 200))
                pygame.draw.circle(placeholder, (0, 0, 0), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
                pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4), 3)
                pygame.draw.circle(placeholder, (255, 255, 255), (TILE_SIZE // 2 + 4, TILE_SIZE // 2 - 4), 3)
                font = pygame.font.SysFont(None, 10)
                text = font.render("OLD", True, (0, 0, 0))
                placeholder.blit(text, (4, TILE_SIZE - 12))
                self.npc_oldman_sprite = placeholder
            
            # Load Old Man walking left sprites
            self.npc_oldman_left_sprites = []
            for name in ["oldmanleft.png", "oldmanleft1.png", "oldmanleft2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_left_sprites.append(scaled)
                    print(f"[OK] Loaded Old Man walking frame: {name}")
                else:
                    print(f"[WARNING] Walking frame not found at: {path}")

            # Load Old Man walking down sprites
            self.npc_oldman_down_sprites = []
            for name in ["oldman.png", "oldmandown1.png", "oldmandown2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_down_sprites.append(scaled)
                    print(f"[OK] Loaded Old Man down frame: {name}")
                else:
                    print(f"[WARNING] Down frame not found at: {path}")

            # Load Old Man walking right sprites
            self.npc_oldman_right_sprites = []
            for name in ["oldmanright.png", "oldmanright1.png", "oldmanright2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_right_sprites.append(scaled)
                    print(f"[OK] Loaded Old Man right frame: {name}")
                else:
                    print(f"[WARNING] Right frame not found at: {path}")

            # Load Old Man walking up sprites
            self.npc_oldman_up_sprites = []
            for name in ["oldmanup.png", "oldmanup1.png", "oldmanup2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_up_sprites.append(scaled)
                    print(f"[OK] Loaded Old Man up frame: {name}")
                else:
                    print(f"[WARNING] Up frame not found at: {path}")
        except Exception as e:
            print(f"[ERROR] Error loading Oldman: {e}")
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
                print(f"[WARNING] Skeleton sprite not found at: {skeleton_path}")
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((255, 255, 255))
                self.npc_skeleton_sprite = placeholder

            # Load Skeleton walking left sprites
            self.npc_skeleton_left_sprites = []
            for name in ["skeleton_left.png", "skeleton_left_1.png", "skeleton_left_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_left_sprites.append(scaled)
                    print(f"[OK] Loaded Skeleton left frame: {name}")

            # Load Skeleton walking down sprites
            self.npc_skeleton_down_sprites = []
            for name in ["skeleton_down.png", "skeleton_down_1.png", "skeleton_down_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_down_sprites.append(scaled)
                    print(f"[OK] Loaded Skeleton down frame: {name}")

            # Load Skeleton walking right sprites
            self.npc_skeleton_right_sprites = []
            for name in ["skeleton_right.png", "skeleton_right_1.png", "skeleton_right_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_right_sprites.append(scaled)
                    print(f"[OK] Loaded Skeleton right frame: {name}")

            # Load Skeleton walking up sprites
            self.npc_skeleton_up_sprites = []
            for name in ["skeleton_up.png", "skeleton_up_1.png", "skeleton_up_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_up_sprites.append(scaled)
                    print(f"[OK] Loaded Skeleton up frame: {name}")
        except Exception as e:
            print(f"[ERROR] Error loading Skeleton: {e}")
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
                print(f"[WARNING] Knight sprite not found at: {knight_path}")
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
            print(f"[ERROR] Error loading Knight: {e}")
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
            self.animation = StageSelect.PortalSpriteAnimation(
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
            screen_x = (self.get_world_x() - camera_x) * zoom
            screen_y = (self.get_world_y() - camera_y) * zoom
            scaled_width = int(self.get_width_pixels() * zoom)
            scaled_height = int(self.get_height_pixels() * zoom)

            # Soft radiant pulsating aura glow behind the portal
            glow_surf = pygame.Surface((scaled_width + 20, scaled_height + 20), pygame.SRCALPHA)
            aura_rgb = (34, 197, 94) if self.direction == 'left' else (
                (59, 130, 246) if self.direction == 'up' else (
                    (245, 158, 11) if self.direction == 'right' else (168, 85, 247)
                )
            )
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1.0) * 0.5
            alpha = int(70 + 45 * pulse)
            pygame.draw.ellipse(glow_surf, (*aura_rgb, alpha), (0, 0, scaled_width + 20, scaled_height + 20))
            screen.blit(glow_surf, (screen_x - 10, screen_y - 10))

            if self.animation:
                self.animation.draw(screen, camera_x, camera_y, zoom, screen_width, screen_height)

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
    # LOAD STATIC PORTALS - Detect from game_map
    # ============================================================
    def load_static_portals(self):
        self.portals = []
        # Use game_map for portal detection so markers are never lost
        for y, row in enumerate(self.game_map):
            row_list = list(self.render_map[y]) if y < len(self.render_map) else []
            modified = False
            for x, c in enumerate(row):
                if c == 'r':
                    portal = self.Portal(x, y, 'right', is_static=True)
                    portal.set_animation(self.portal_frames_cache['right'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = '6'
                        modified = True
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = '6'
                        modified = True
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = '7'
                        modified = True
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    self.portals.append(portal)
                    if row_list and x < len(row_list):
                        row_list[x] = '7'
                        modified = True
            if modified and y < len(self.render_map):
                self.render_map[y] = ''.join(row_list)

    # ============================================================
    # QUARTER PROGRESSION & UNLOCK STATUS
    # ============================================================
    def is_quarter_completed(self, qid):
        """Returns True if the specified quarter is recorded as completed."""
        if not hasattr(self, 'completed_quarters') or not self.completed_quarters:
            from db.save_system import get_completed_quarters
            student_id = getattr(self.main_menu, 'student_id', None)
            self.completed_quarters = get_completed_quarters(student_id)
        return self.completed_quarters.get(qid, {}).get("completed", False)

    def is_quarter_unlocked(self, qid):
        """Sequential gating: Q1 is open; Q2 requires Q1; Q3 requires Q2; Q4 requires Q3."""
        if qid == "quarter1":
            return True
        elif qid == "quarter2":
            return self.is_quarter_completed("quarter1")
        elif qid == "quarter3":
            return self.is_quarter_completed("quarter2")
        elif qid == "quarter4":
            return self.is_quarter_completed("quarter3")
        return False

    # ============================================================
    # COLLISION - MODIFIED to use npc_positions_data & Sequential Path Gating
    # ============================================================
    def can_move(self, nx, ny):
        col = int(nx // TILE_SIZE)
        row = int(ny // TILE_SIZE)
        if row < 0 or row >= self.ROWS or col < 0 or col >= self.COLS:
            return False
        if row >= len(self.game_map) or col >= len(self.game_map[row]):
            return False
        tile = self.game_map[row][col]

        # Check if tile is walkable
        if tile not in self.WALKABLE_TILES:
            return False

        # Sequential Corridor Barriers:
        # 1. South Corridor to Quarter 2 (Row >= 16 in cols 25-27)
        if col in (25, 26, 27) and row >= 16:
            if not self.is_quarter_unlocked("quarter2"):
                if self.locked_portal_banner_timer <= 0:
                    self.locked_portal_banner_msg = "Complete Quarter 1 to unlock the path to Quarter 2!"
                    self.locked_portal_banner_timer = 2.5
                return False

        # 2. East Corridor to Quarter 3 (Col >= 28 in rows 12-14)
        if row in (12, 13, 14) and col >= 28:
            if not self.is_quarter_unlocked("quarter3"):
                if self.locked_portal_banner_timer <= 0:
                    self.locked_portal_banner_msg = "Complete Quarter 2 to unlock the path to Quarter 3!"
                    self.locked_portal_banner_timer = 2.5
                return False

        # 3. North Corridor to Quarter 4 (Row <= 11 in cols 25-27)
        if col in (25, 26, 27) and row <= 11:
            if not self.is_quarter_unlocked("quarter4"):
                if self.locked_portal_banner_timer <= 0:
                    self.locked_portal_banner_msg = "Complete Quarter 3 to unlock the path to Quarter 4!"
                    self.locked_portal_banner_timer = 2.5
                return False

        # Check if any NPC is at this position (obstacle)
        npc_positions = []
        for marker, positions in self.npc_positions_data.items():
            npc_positions.extend(positions)

        player_col = int(self.player_x // TILE_SIZE)
        player_row = int(self.player_y // TILE_SIZE)

        for npc_col, npc_row in npc_positions:
            if col == npc_col and row == npc_row:
                # Allow if player is already on this NPC tile (teleport case)
                if player_col == npc_col and player_row == npc_row:
                    return True
                return False  # Block movement into NPC

        return True

    def save_ss_state(self):
        """Helper to save Stage Select states to main_menu"""
        if self.main_menu:
            self.main_menu.last_stage_select_data = {
                "player_x": self.player_x,
                "player_y": self.player_y,
                "oldman_dialogue_state": self.oldman_dialogue_state,
                "knight_dialogue_state": self.knight_dialogue_state,
                "skeleton_dialogue_state": self.skeleton_dialogue_state,
                "bromen_dialogue_state": self.bromen_dialogue_state,
                "player_following_target": self.player_following_target
            }

    def _preload_quarter_worker(self, qid):
        """Threaded worker that pre-loads the target Quarter during the 3-second black LOADING screen."""
        try:
            if qid == "quarter1":
                map_name = random.choice(["map1.txt", "map2.txt", "map3.txt"])
                print(f"[STAGE] Background pre-loading Quarter 1 - {map_name}")
                from screens.quarter1 import Quarter1
                loaded = Quarter1(self.screen, self.main_menu, map_name)
            elif qid == "quarter2":
                map_name = random.choice(["map4.txt", "map5.txt", "map6.txt"])
                print(f"[STAGE] Background pre-loading Quarter 2 - {map_name}")
                from screens.quarter2 import Quarter2
                loaded = Quarter2(self.screen, self.main_menu, map_name)
            elif qid == "quarter3":
                map_name = random.choice(["map7.txt", "map8.txt", "map9.txt"])
                print(f"[STAGE] Background pre-loading Quarter 3 - {map_name}")
                from screens.quarter3 import Quarter3
                loaded = Quarter3(self.screen, self.main_menu, map_name)
            elif qid == "quarter4":
                map_name = random.choice(["map10.txt", "map11.txt", "map12.txt"])
                print(f"[STAGE] Background pre-loading Quarter 4 - {map_name}")
                from screens.quarter4 import Quarter4
                loaded = Quarter4(self.screen, self.main_menu, map_name)
            else:
                loaded = None
            self.portal_loaded_screen = loaded
        except Exception as e:
            print(f"[STAGE WARN] Preload exception for {qid}: {e}")
            self.portal_loaded_screen = None
        finally:
            self.portal_loading_done = True

    def enter_quarter(self, qid):
        """Initiate centralized portal transition with 3-second black LOADING screen and background preload."""
        if getattr(self, 'portal_transition_active', False):
            return

        self.portal_transition_active = True
        self.portal_transition_timer = 0.0
        self.portal_transition_duration = 3.0  # 3 seconds as requested
        self.portal_transition_target = qid
        self.portal_loading_done = False
        self.portal_loaded_screen = None
        self.player_following_target = False  # Stop walking follow

        # Compute screen position of player/portal for radial effect center
        center_x = int((self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM)
        center_y = int((self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM)
        if not (0 <= center_x <= self.width and 0 <= center_y <= self.height):
            center_x, center_y = self.width // 2, self.height // 2
        self.portal_transition_origin = (center_x, center_y)

        # Initialize particles, LOADING letter models, and theme
        self._init_portal_transition_fx(qid)

        # Start asynchronous pre-load worker in a background thread to hide all loading delay
        import threading
        threading.Thread(target=self._preload_quarter_worker, args=(qid,), daemon=True).start()

        # Play transition sound effect
        if hasattr(self.main_menu, 'audio_manager'):
            snd = self.main_menu.audio_manager.play_sfx("portal_transition")
            if snd is None:
                self.main_menu.audio_manager.play_sfx("portal_warp")

    def _finish_portal_transition(self):
        """Execute screen change to target quarter once warp transition completes."""
        qid = self.portal_transition_target
        self.portal_transition_active = False

        self.save_ss_state()
        from db.save_system import save_student_progress
        save_student_progress(self.main_menu)

        # Use pre-loaded instance from background thread or fallback to direct load
        if qid == "quarter1":
            if self.portal_loaded_screen:
                self.main_menu.quarter1 = self.portal_loaded_screen
            else:
                map_name = random.choice(["map1.txt", "map2.txt", "map3.txt"])
                print(f"[STAGE] Entering Quarter 1 - {map_name}")
                from screens.quarter1 import Quarter1
                self.main_menu.quarter1 = Quarter1(self.screen, self.main_menu, map_name)
            self.main_menu.current_screen = "quarter1"
        elif qid == "quarter2":
            if self.portal_loaded_screen:
                self.main_menu.quarter2 = self.portal_loaded_screen
            else:
                map_name = random.choice(["map4.txt", "map5.txt", "map6.txt"])
                print(f"[STAGE] Entering Quarter 2 - {map_name}")
                from screens.quarter2 import Quarter2
                self.main_menu.quarter2 = Quarter2(self.screen, self.main_menu, map_name)
            self.main_menu.current_screen = "quarter2"
        elif qid == "quarter3":
            if self.portal_loaded_screen:
                self.main_menu.quarter3 = self.portal_loaded_screen
            else:
                map_name = random.choice(["map7.txt", "map8.txt", "map9.txt"])
                print(f"[STAGE] Entering Quarter 3 - {map_name}")
                from screens.quarter3 import Quarter3
                self.main_menu.quarter3 = Quarter3(self.screen, self.main_menu, map_name)
            self.main_menu.current_screen = "quarter3"
        elif qid == "quarter4":
            if self.portal_loaded_screen:
                self.main_menu.quarter4 = self.portal_loaded_screen
            else:
                map_name = random.choice(["map10.txt", "map11.txt", "map12.txt"])
                print(f"[STAGE] Entering Quarter 4 - {map_name}")
                from screens.quarter4 import Quarter4
                self.main_menu.quarter4 = Quarter4(self.screen, self.main_menu, map_name)
            self.main_menu.current_screen = "quarter4"

        self.portal_loaded_screen = None
        self.main_menu.stage_select = None

    def _init_portal_transition_fx(self, qid):
        """Initialize theme palettes, swirling energy vortex, hyperspace star particles, and LOADING text."""
        palettes = {
            "quarter1": {
                "name": "QUARTER 1",
                "title": "GEOMETRY FOREST",
                "realm": "Geometry & Polygon Realm",
                "primary": (34, 197, 94),
                "secondary": (56, 189, 248),
                "accent": (250, 204, 21),
                "void": (6, 32, 20),
            },
            "quarter2": {
                "name": "QUARTER 2",
                "title": "BARRIOS' FIESTA",
                "realm": "Market & Arithmetic Realm",
                "primary": (245, 158, 11),
                "secondary": (239, 68, 68),
                "accent": (253, 224, 71),
                "void": (36, 15, 6),
            },
            "quarter3": {
                "name": "QUARTER 3",
                "title": "MONETARY DESERT",
                "realm": "Solar Desert & Fractions Realm",
                "primary": (234, 179, 8),
                "secondary": (249, 115, 22),
                "accent": (254, 240, 138),
                "void": (40, 24, 6),
            },
            "quarter4": {
                "name": "QUARTER 4",
                "title": "UNDERWATER DUNGEON",
                "realm": "Aquatic Sluices & Grand Finale",
                "primary": (56, 189, 248),
                "secondary": (168, 85, 247),
                "accent": (216, 180, 254),
                "void": (10, 20, 42),
            },
        }
        self.portal_transition_theme = palettes.get(qid, palettes["quarter1"])

        # Pre-render LOADING... letters in pixel font with theme primary glow
        theme_glow = self.portal_transition_theme.get("primary", (180, 180, 180))
        self.loading_text = "LOADING..."
        self.loading_spacing = 10
        self.loading_letters = []
        for ch in self.loading_text:
            glow = self.title_font.render(ch, False, theme_glow)
            outline = self.title_font.render(ch, False, (0, 0, 0))
            main = self.title_font.render(ch, False, (255, 255, 255))
            self.loading_letters.append({
                "glow": glow,
                "outline": outline,
                "main": main,
                "width": main.get_width()
            })
        self.loading_total_width = sum(l["width"] for l in self.loading_letters) + self.loading_spacing * (len(self.loading_text) - 1)

        # Ambient floating particle stars
        self.portal_transition_stars = []
        for _ in range(50):
            star_ang = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 180)
            color = random.choice([
                (255, 255, 255),
                self.portal_transition_theme["accent"],
                self.portal_transition_theme["primary"]
            ])
            self.portal_transition_stars.append({
                "angle": star_ang,
                "dist": random.uniform(20, self.width // 2),
                "speed": speed,
                "length": random.uniform(4, 12),
                "color": color,
                "width": random.randint(2, 4)
            })

    def _update_portal_transition(self, dt):
        """Update positions of ambient drifting particles."""
        for s in self.portal_transition_stars:
            s["dist"] += s["speed"] * dt

    # ============================================================
    # CHECK PORTAL TELEPORT - Load Quarter1, Quarter2, Quarter3, or Quarter4
    # ============================================================
    def check_portal_teleport_on_hold(self):
        current_portal = None
        for portal in self.portals:
            if portal.contains_position(self.player_x, self.player_y):
                current_portal = portal
                break

        if current_portal and self.fist_closed and self.teleport_cooldown <= 0:
            # Check if it's a left portal (goes to Quarter1)
            if current_portal.direction == 'left':
                if self.oldman_dialogue_state == 0 and not self.is_quarter_completed('quarter1'):
                    print("[LOCKED] Quarter 1 Portal Locked! Talk to the Old Man first.")
                    self.locked_portal_banner_msg = "Talk to the Old Man first to unlock Quarter 1!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                self.enter_quarter("quarter1")
                return True
            # Check if it's an up portal (goes to Quarter2)
            elif current_portal.direction == 'up':
                if not self.is_quarter_unlocked('quarter2'):
                    print("[LOCKED] Quarter 2 Locked! Complete Quarter 1 first.")
                    self.locked_portal_banner_msg = "Complete Quarter 1 to unlock Quarter 2!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                if self.knight_dialogue_state == 0 and not self.is_quarter_completed('quarter2'):
                    print("[LOCKED] Quarter 2 Portal Locked! Talk to the Knight first.")
                    self.locked_portal_banner_msg = "Talk to the Knight first to unlock Quarter 2!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                self.enter_quarter("quarter2")
                return True
            # Check if it's a right portal (goes to Quarter3)
            elif current_portal.direction == 'right':
                if not self.is_quarter_unlocked('quarter3'):
                    print("[LOCKED] Quarter 3 Locked! Complete Quarter 2 first.")
                    self.locked_portal_banner_msg = "Complete Quarter 2 to unlock Quarter 3!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                if self.skeleton_dialogue_state == 0 and not self.is_quarter_completed('quarter3'):
                    print("[LOCKED] Quarter 3 Portal Locked! Talk to the Skeleton first.")
                    self.locked_portal_banner_msg = "Talk to the Skeleton first to unlock Quarter 3!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                self.enter_quarter("quarter3")
                return True
            # Check if it's a down portal (goes to Quarter4)
            elif current_portal.direction == 'down':
                if not self.is_quarter_unlocked('quarter4'):
                    print("[LOCKED] Quarter 4 Locked! Complete Quarter 3 first.")
                    self.locked_portal_banner_msg = "Complete Quarter 3 to unlock Quarter 4!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                if self.bromen_dialogue_state == 0 and not self.is_quarter_completed('quarter4'):
                    print("[LOCKED] Quarter 4 Portal Locked! Talk to Bromen first.")
                    self.locked_portal_banner_msg = "Talk to Bromen first to unlock Quarter 4!"
                    self.locked_portal_banner_timer = 2.5
                    return False
                self.enter_quarter("quarter4")
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
    # NEW METHOD - Switch to new map (kept for compatibility)
    # ============================================================
    def _switch_to_new_map(self):
        """Switch to a newly loaded map"""
        # Update map data
        self.game_map = self.map_loader.game_map
        self.ROWS = self.map_loader.rows
        self.COLS = self.map_loader.cols
        self.MAP_WIDTH = self.COLS * TILE_SIZE
        self.MAP_HEIGHT = self.ROWS * TILE_SIZE
        self.render_map = self.map_loader.replace_npc_markers_with_walkable_tiles()
        self.npc_positions_data = self.map_loader.npc_positions

        # Spawn player at new start position
        if self.map_loader.player_start:
            start_x, start_y = self.map_loader.player_start
            self.player_x = start_x * TILE_SIZE
            self.player_y = start_y * TILE_SIZE
            print(f"Player teleported to: ({start_x}, {start_y})")
        else:
            # Fallback: find P in map
            for y, row in enumerate(self.game_map):
                for x, c in enumerate(row):
                    if c == "P":
                        self.player_x = x * TILE_SIZE
                        self.player_y = y * TILE_SIZE
                        break
                if self.player_x != 0:
                    break

        # Reset and reload portals
        self.portals = []
        self.load_static_portals()

        # Re-initialize NPC positions
        self._init_npc_positions()

        # Center camera directly on player without sliding
        self.lol_camera.snap_to(self.player_x, self.player_y, TILE_SIZE, self.MAP_WIDTH, self.MAP_HEIGHT)
        self.camera_x = self.lol_camera.camera_x
        self.camera_y = self.lol_camera.camera_y

        print(f"[OK] Switched to new map: {self.map_loader.current_map_name}")

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
    # UPDATE GESTURE (called from main_menu)
    # ============================================================
    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        """Update gesture data from main menu"""
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME
        self.current_gesture = current_gesture

        # Check if hand is detected (not NO HAND)
        self.hand_detected = current_gesture != "NO HAND"

        # Check if fist is closed (fist_start_time > 0 means fist is being held)
        self.fist_closed = fist_start_time > 0

    # ============================================================
    # ADVANCE DIALOGUE / SKIP CUTSCENE
    # ============================================================
    def advance_dialogue(self):
        """Advances active NPC dialogue. If dialogue finishes, triggers NPC move & player follow.
        If player is already following, calling advance immediately enters the portal."""
        if getattr(self, 'portal_transition_active', False):
            return True

        if self.player_following_target:
            # Skip follow cutscene and enter immediately
            if self.player_following_target == 'oldman':
                self.enter_quarter("quarter1")
            elif self.player_following_target == 'knight':
                self.enter_quarter("quarter2")
            elif self.player_following_target == 'skeleton':
                self.enter_quarter("quarter3")
            elif self.player_following_target == 'bromen':
                self.enter_quarter("quarter4")
            return True

        # Check if active dialogue line is still typing: fast forward on first press
        active_line_len = None
        if self.oldman_dialogue_state == 1 and self.oldman_dialogue_index < len(self.dialogue_lines):
            active_line_len = len(self.dialogue_lines[self.oldman_dialogue_index][1])
        elif self.skeleton_dialogue_state == 1 and self.skeleton_dialogue_index < len(self.skeleton_dialogue_lines):
            active_line_len = len(self.skeleton_dialogue_lines[self.skeleton_dialogue_index][1])
        elif self.knight_dialogue_state == 1 and self.knight_dialogue_index < len(self.knight_dialogue_lines):
            active_line_len = len(self.knight_dialogue_lines[self.knight_dialogue_index][1])
        elif self.bromen_dialogue_state == 1 and self.bromen_dialogue_index < len(self.bromen_dialogue_lines):
            active_line_len = len(self.bromen_dialogue_lines[self.bromen_dialogue_index][1])

        if active_line_len is not None and self.dialogue_char_index < active_line_len:
            self.dialogue_char_index = float(active_line_len)
            return True

        # Text is fully typed: reset typewriter and advance to next line or action
        self.dialogue_char_index = 0.0
        self.dialogue_sound_timer = 0.0
        self.dialogue_active_key = None

        if self.oldman_dialogue_state == 1:
            self.oldman_dialogue_index += 1
            if self.oldman_dialogue_index >= len(self.dialogue_lines):
                self.oldman_dialogue_state = 2
                self.player_following_target = 'oldman'
                self.player_block_timer = 0
                if 'O' in self.npc_positions_data:
                    self.npc_positions_data['O'] = []
                print("[Old Man] Dialog complete! Old Man starts moving left and player follows.")
            return True

        if self.skeleton_dialogue_state == 1:
            self.skeleton_dialogue_index += 1
            if self.skeleton_dialogue_index >= len(self.skeleton_dialogue_lines):
                self.skeleton_dialogue_state = 2
                self.player_following_target = 'skeleton'
                self.player_block_timer = 0
                if 'S' in self.npc_positions_data:
                    self.npc_positions_data['S'] = []
                print("[Skeleton] Dialog complete! Skeleton starts moving right to portal and player follows.")
            return True

        if self.knight_dialogue_state == 1:
            self.knight_dialogue_index += 1
            if self.knight_dialogue_index >= len(self.knight_dialogue_lines):
                self.knight_dialogue_state = 2
                self.player_following_target = 'knight'
                self.player_block_timer = 0
                if '1' in self.npc_positions_data:
                    self.npc_positions_data['1'] = []
                print("[Knight] Dialog complete! Knight starts moving down to portal and player follows.")
            return True

        if self.bromen_dialogue_state == 1:
            self.bromen_dialogue_index += 1
            if self.bromen_dialogue_index >= len(self.bromen_dialogue_lines):
                self.bromen_dialogue_state = 2
                self.player_following_target = 'bromen'
                self.player_block_timer = 0
                if 'B' in self.npc_positions_data:
                    self.npc_positions_data['B'] = []
                print("* Dialogue complete! Bromen starts moving north to portal and player follows.")
            return True

        return False

    # ============================================================
    # TRIGGER CLICK (called from main_menu)
    # ============================================================
    def trigger_click(self, pos):
        if getattr(self, 'portal_transition_active', False):
            return

        # Check Grand Finale modal interaction
        if self.grand_finale_active:
            card_w, card_h = 620, 450
            card_x = (self.width - card_w) // 2
            card_y = (self.height - card_h) // 2
            btn_rect = pygame.Rect(card_x + (card_w - 280) // 2, card_y + 375, 280, 44)
            if btn_rect.collidepoint(pos):
                self.grand_finale_active = False
                self.grand_finale_dismissed = True
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("click")
            return

        from db.save_system import is_game_completed
        if is_game_completed(getattr(self.main_menu, 'student_id', None)):
            finale_btn_rect = pygame.Rect(self.width - 170, 12, 150, 36)
            if finale_btn_rect.collidepoint(pos):
                self.grand_finale_active = True
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("victory_fanfare")
                return

        # Advance active dialogue or skip cutscene
        if self.advance_dialogue():
            return

        # Trigger teleport on click/hold when standing on a portal (Only if NPC has been spoken to)
        current_portal = None
        for portal in self.portals:
            if portal.contains_position(self.player_x, self.player_y):
                current_portal = portal
                break
        
        if current_portal and self.teleport_cooldown <= 0:
            if current_portal.direction == 'left':
                if self.oldman_dialogue_state == 0 and not self.is_quarter_completed('quarter1'):
                    self.locked_portal_banner_msg = "Talk to the Old Man first to unlock Quarter 1!"
                    self.locked_portal_banner_timer = 1.0
                else:
                    self.enter_quarter("quarter1")
            elif current_portal.direction == 'up':
                if not self.is_quarter_unlocked('quarter2'):
                    self.locked_portal_banner_msg = "Complete Quarter 1 to unlock Quarter 2!"
                    self.locked_portal_banner_timer = 2.0
                elif self.knight_dialogue_state == 0 and not self.is_quarter_completed('quarter2'):
                    self.locked_portal_banner_msg = "Talk to the Knight first to unlock Quarter 2!"
                    self.locked_portal_banner_timer = 1.5
                else:
                    self.enter_quarter("quarter2")
            elif current_portal.direction == 'right':
                if not self.is_quarter_unlocked('quarter3'):
                    self.locked_portal_banner_msg = "Complete Quarter 2 to unlock Quarter 3!"
                    self.locked_portal_banner_timer = 2.0
                elif self.skeleton_dialogue_state == 0 and not self.is_quarter_completed('quarter3'):
                    self.locked_portal_banner_msg = "Talk to the Skeleton first to unlock Quarter 3!"
                    self.locked_portal_banner_timer = 1.5
                else:
                    self.enter_quarter("quarter3")
            elif current_portal.direction == 'down':
                if not self.is_quarter_unlocked('quarter4'):
                    self.locked_portal_banner_msg = "Complete Quarter 3 to unlock Quarter 4!"
                    self.locked_portal_banner_timer = 2.0
                elif self.bromen_dialogue_state == 0 and not self.is_quarter_completed('quarter4'):
                    self.locked_portal_banner_msg = "Talk to Bromen first to unlock Quarter 4!"
                    self.locked_portal_banner_timer = 1.5
                else:
                    self.enter_quarter("quarter4")

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1

        # Check Portal Warp Screen Transition (3-second black LOADING screen)
        if self.portal_transition_active:
            self.portal_transition_timer += dt
            self._update_portal_transition(dt)
            if self.portal_transition_timer >= self.portal_transition_duration and (getattr(self, 'portal_loading_done', False) or self.portal_transition_timer >= 5.0):
                self._finish_portal_transition()
            return

        # Update Grand Finale Confetti & Fanfare
        if self.grand_finale_active:
            if not self.grand_finale_fanfare_played:
                self.grand_finale_fanfare_played = True
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("victory_fanfare")
            if len(self.confetti_particles) < 60:
                self.confetti_particles.append({
                    "x": random.randint(0, self.width),
                    "y": random.randint(-40, 0),
                    "vx": random.uniform(-1.5, 1.5),
                    "vy": random.uniform(2.0, 5.0),
                    "color": random.choice([(255, 215, 0), (59, 130, 246), (34, 197, 94), (239, 68, 68), (168, 85, 247), (236, 72, 153)]),
                    "size": random.randint(4, 8)
                })
            for p in self.confetti_particles:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                if p["y"] > self.height:
                    p["y"] = random.randint(-20, 0)
                    p["x"] = random.randint(0, self.width)

        # Update Area Title animation elapsed time
        if self.title_active:
            self.title_elapsed += dt
            if self.title_elapsed >= self.title_duration:
                self.title_active = False

        # Update cooldowns
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt

        # Update block timer
        if self.player_block_timer > 0:
            self.player_block_timer = max(0.0, self.player_block_timer - dt)

        # Update locked portal banner timer
        if self.locked_portal_banner_timer > 0:
            self.locked_portal_banner_timer = max(0.0, self.locked_portal_banner_timer - dt)

        # Update Typewriter Dialogue
        active_dialogue_text = None
        current_dialogue_key = None
        if self.oldman_dialogue_state == 1 and self.oldman_dialogue_index < len(self.dialogue_lines):
            active_dialogue_text = self.dialogue_lines[self.oldman_dialogue_index][1]
            current_dialogue_key = ('oldman', self.oldman_dialogue_index)
        elif self.skeleton_dialogue_state == 1 and self.skeleton_dialogue_index < len(self.skeleton_dialogue_lines):
            active_dialogue_text = self.skeleton_dialogue_lines[self.skeleton_dialogue_index][1]
            current_dialogue_key = ('skeleton', self.skeleton_dialogue_index)
        elif self.knight_dialogue_state == 1 and self.knight_dialogue_index < len(self.knight_dialogue_lines):
            active_dialogue_text = self.knight_dialogue_lines[self.knight_dialogue_index][1]
            current_dialogue_key = ('knight', self.knight_dialogue_index)
        elif self.bromen_dialogue_state == 1 and self.bromen_dialogue_index < len(self.bromen_dialogue_lines):
            active_dialogue_text = self.bromen_dialogue_lines[self.bromen_dialogue_index][1]
            current_dialogue_key = ('bromen', self.bromen_dialogue_index)

        if current_dialogue_key != self.dialogue_active_key:
            self.dialogue_active_key = current_dialogue_key
            self.dialogue_char_index = 0.0
            self.dialogue_sound_timer = 0.0

        if active_dialogue_text:
            text_len = len(active_dialogue_text)
            if self.dialogue_char_index < text_len:
                prev_char_int = int(self.dialogue_char_index)
                self.dialogue_char_index = min(float(text_len), self.dialogue_char_index + self.dialogue_typing_speed * dt)
                new_char_int = int(self.dialogue_char_index)
                self.dialogue_sound_timer += dt
                if new_char_int > prev_char_int and self.dialogue_sound_timer >= 0.045:
                    self.dialogue_sound_timer = 0.0
                    char_just_typed = active_dialogue_text[min(new_char_int - 1, text_len - 1)]
                    if char_just_typed not in (' ', '\t', '\n'):
                        if hasattr(self.main_menu, 'audio_manager'):
                            self.main_menu.audio_manager.play_sfx("dialogue_blip")

        # Update Bromen NPC idle animation
        if self.npc_bromen_sprites and self.npc_bromen_found and self.bromen_dialogue_state == 0:
            self.npc_bromen_anim_timer += 1
            if self.npc_bromen_anim_timer >= 5:
                self.npc_bromen_anim_timer = 0
                self.npc_bromen_anim_frame = (self.npc_bromen_anim_frame + 1) % len(self.npc_bromen_sprites)

        # Proximity interaction check for Bromen NPC
        if self.npc_bromen_found:
            if self.bromen_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                bromen_center_x = self.npc_bromen_x + TILE_SIZE // 2
                bromen_center_y = self.npc_bromen_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - bromen_center_x, player_center_y - bromen_center_y)
                if dist < TILE_SIZE * 2.5:
                    if not self.is_quarter_unlocked('quarter4'):
                        if self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Complete Quarter 3 to unlock Quarter 4!"
                            self.locked_portal_banner_timer = 2.0
                    else:
                        self.bromen_dialogue_state = 1
                        self.bromen_dialogue_index = 0
                        
                        # Face each other
                        dx = self.npc_bromen_x - self.player_x
                        dy = self.npc_bromen_y - self.player_y
                        if abs(dx) > abs(dy):
                            self.player_dir = "left" if dx < 0 else "right"
                        else:
                            self.player_dir = "up" if dy < 0 else "down"

        # Update Bromen walking to north portal (y <= 0)
        if self.bromen_dialogue_state == 2:
            if self.npc_bromen_y > 0:
                self.npc_bromen_y -= 2
                self.npc_bromen_dir = "up"
                self.npc_bromen_anim_timer += 1
                if self.npc_bromen_anim_timer >= 10:
                    self.npc_bromen_anim_timer = 0
                    if self.npc_bromen_up_sprites:
                        self.npc_bromen_anim_frame = (self.npc_bromen_anim_frame + 1) % len(self.npc_bromen_up_sprites)
            else:
                self.npc_bromen_y = 0
                self.bromen_dialogue_state = 3
                self.npc_bromen_found = False
                
                # Remove NPC collision obstacle so player can pass
                if 'B' in self.npc_positions_data:
                    self.npc_positions_data['B'] = []
                
                # Update self.game_map so the player can walk through
                for r_idx, r_str in enumerate(self.game_map):
                    if 'B' in r_str:
                        self.game_map[r_idx] = r_str.replace('B', '8')
                        
                print("* Bromen reached north portal and disappeared from stage select!")


        # Proximity interaction check for Old Man NPC
        if self.npc_oldman_found:
            if self.oldman_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                oldman_center_x = self.npc_oldman_x + TILE_SIZE // 2
                oldman_center_y = self.npc_oldman_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - oldman_center_x, player_center_y - oldman_center_y)
                if dist < TILE_SIZE * 2.5:
                    self.oldman_dialogue_state = 1
                    self.oldman_dialogue_index = 0
                    
                    # Face the Old Man
                    dx = self.npc_oldman_x - self.player_x
                    dy = self.npc_oldman_y - self.player_y
                    if abs(dx) > abs(dy):
                        self.player_dir = "left" if dx < 0 else "right"
                    else:
                        self.player_dir = "up" if dy < 0 else "down"
                        
                    # Face the Player
                    dx_om = self.player_x - self.npc_oldman_x
                    dy_om = self.player_y - self.npc_oldman_y
                    if abs(dx_om) > abs(dy_om):
                        self.npc_oldman_dir = "right" if dx_om > 0 else "left"
                    else:
                        self.npc_oldman_dir = "down" if dy_om > 0 else "up"
                else:
                    self.npc_oldman_dir = "down"

        # Update Old Man walking to left portal (x = 0)
        if self.oldman_dialogue_state == 2:
            target_y = (self.npc_oldman_tile_y + 1) * TILE_SIZE
            if self.npc_oldman_y < target_y:
                # Walk 1 tile down first
                self.npc_oldman_y += 2
                self.npc_oldman_dir = "down"
                self.npc_oldman_anim_timer += 1
                if self.npc_oldman_anim_timer >= 10:
                    self.npc_oldman_anim_timer = 0
                    if self.npc_oldman_down_sprites:
                        self.npc_oldman_anim_frame = (self.npc_oldman_anim_frame + 1) % len(self.npc_oldman_down_sprites)
            else:
                # Face left and walk to the left portal
                self.npc_oldman_x -= 2
                self.npc_oldman_dir = "left"
                self.npc_oldman_anim_timer += 1
                if self.npc_oldman_anim_timer >= 10:
                    self.npc_oldman_anim_timer = 0
                    if self.npc_oldman_left_sprites:
                        self.npc_oldman_anim_frame = (self.npc_oldman_anim_frame + 1) % len(self.npc_oldman_left_sprites)

            if self.npc_oldman_x <= 0:
                self.npc_oldman_x = 0
                self.oldman_dialogue_state = 3
                self.npc_oldman_found = False
                
                # Remove NPC collision obstacle so player can pass
                if 'O' in self.npc_positions_data:
                    self.npc_positions_data['O'] = []
                
                # Update self.game_map so the player can walk through
                row_list = list(self.game_map[12])
                if row_list[5] == 'O':
                    row_list[5] = '6'
                    self.game_map[12] = "".join(row_list)
                    
                print("[Old Man] Old Man reached portal and disappeared from stage select!")

        # Proximity interaction check for Skeleton NPC
        if self.npc_skeleton_found:
            if self.skeleton_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                skeleton_center_x = self.npc_skeleton_x + TILE_SIZE // 2
                skeleton_center_y = self.npc_skeleton_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - skeleton_center_x, player_center_y - skeleton_center_y)
                if dist < TILE_SIZE * 2.5:
                    if not self.is_quarter_unlocked('quarter3'):
                        if self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Complete Quarter 2 to unlock Quarter 3!"
                            self.locked_portal_banner_timer = 2.0
                    else:
                        self.skeleton_dialogue_state = 1
                        self.skeleton_dialogue_index = 0
                        
                        # Face the Skeleton
                        dx = self.npc_skeleton_x - self.player_x
                        dy = self.npc_skeleton_y - self.player_y
                        if abs(dx) > abs(dy):
                            self.player_dir = "left" if dx < 0 else "right"
                        else:
                            self.player_dir = "up" if dy < 0 else "down"
                            
                        # Face the Player
                        dx_sk = self.player_x - self.npc_skeleton_x
                        dy_sk = self.player_y - self.npc_skeleton_y
                        if abs(dx_sk) > abs(dy_sk):
                            self.npc_skeleton_dir = "right" if dx_sk > 0 else "left"
                        else:
                            self.npc_skeleton_dir = "down" if dy_sk > 0 else "up"
                else:
                    self.npc_skeleton_dir = "down"

        # Update Skeleton walking to right portal
        if self.skeleton_dialogue_state == 2:
            target_y = (self.npc_skeleton_tile_y + 1) * TILE_SIZE
            target_x_max = (len(self.game_map[0]) - 1) * TILE_SIZE
            if self.npc_skeleton_y < target_y:
                # Walk 1 tile down first if needed
                self.npc_skeleton_y += 2
                self.npc_skeleton_dir = "down"
                self.npc_skeleton_anim_timer += 1
                if self.npc_skeleton_anim_timer >= 10:
                    self.npc_skeleton_anim_timer = 0
                    if self.npc_skeleton_down_sprites:
                        self.npc_skeleton_anim_frame = (self.npc_skeleton_anim_frame + 1) % len(self.npc_skeleton_down_sprites)
            else:
                # Face right and walk to the right portal
                self.npc_skeleton_x += 2
                self.npc_skeleton_dir = "right"
                self.npc_skeleton_anim_timer += 1
                if self.npc_skeleton_anim_timer >= 10:
                    self.npc_skeleton_anim_timer = 0
                    if self.npc_skeleton_right_sprites:
                        self.npc_skeleton_anim_frame = (self.npc_skeleton_anim_frame + 1) % len(self.npc_skeleton_right_sprites)

            if self.npc_skeleton_x >= target_x_max:
                self.npc_skeleton_x = target_x_max
                self.skeleton_dialogue_state = 3
                self.npc_skeleton_found = False
                
                # Remove NPC collision obstacle so player can pass
                if 'S' in self.npc_positions_data:
                    self.npc_positions_data['S'] = []
                
                # Update self.game_map so the player can walk through
                for r_idx, r_str in enumerate(self.game_map):
                    if 'S' in r_str:
                        self.game_map[r_idx] = r_str.replace('S', '6')
                        
                print("[Skeleton] Skeleton reached portal and disappeared from stage select!")

        # Proximity interaction check for Knight NPC
        if self.npc_knight_found:
            if self.knight_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                knight_center_x = self.npc_knight_x + TILE_SIZE // 2
                knight_center_y = self.npc_knight_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - knight_center_x, player_center_y - knight_center_y)
                if dist < TILE_SIZE * 2.5:
                    if not self.is_quarter_unlocked('quarter2'):
                        if self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Complete Quarter 1 to unlock Quarter 2!"
                            self.locked_portal_banner_timer = 2.0
                    else:
                        self.knight_dialogue_state = 1
                        self.knight_dialogue_index = 0
                        
                        # Face the Knight
                        dx = self.npc_knight_x - self.player_x
                        dy = self.npc_knight_y - self.player_y
                        if abs(dx) > abs(dy):
                            self.player_dir = "left" if dx < 0 else "right"
                        else:
                            self.player_dir = "up" if dy < 0 else "down"
                            
                        # Face the Player
                        dx_kn = self.player_x - self.npc_knight_x
                        dy_kn = self.player_y - self.npc_knight_y
                        if abs(dx_kn) > abs(dy_kn):
                            self.npc_knight_dir = "right" if dx_kn > 0 else "left"
                        else:
                            self.npc_knight_dir = "down" if dy_kn > 0 else "up"
                else:
                    self.npc_knight_dir = "down"

        # Update Knight walking to down portal
        if self.knight_dialogue_state == 2:
            target_y_max = (len(self.game_map) - 1) * TILE_SIZE
            if self.npc_knight_y < target_y_max:
                self.npc_knight_y += 2
                self.npc_knight_dir = "down"
                self.npc_knight_anim_timer += 1
                if self.npc_knight_anim_timer >= 10:
                    self.npc_knight_anim_timer = 0
                    if self.npc_knight_down_sprites:
                        self.npc_knight_anim_frame = (self.npc_knight_anim_frame + 1) % len(self.npc_knight_down_sprites)

            if self.npc_knight_y >= target_y_max:
                self.npc_knight_y = target_y_max
                self.knight_dialogue_state = 3
                self.npc_knight_found = False
                
                # Remove NPC collision obstacle so player can pass
                if 'K' in self.npc_positions_data:
                    self.npc_positions_data['K'] = []
                
                # Update self.game_map so the player can walk through
                for r_idx, r_str in enumerate(self.game_map):
                    if 'K' in r_str:
                        self.game_map[r_idx] = r_str.replace('K', '7')
                        
                print("[Knight] Knight reached down portal and disappeared from stage select!")

        # Update player following NPC
        if self.player_following_target:
            self.update_player_following()
        else:
            # Update player movement using cursor from main menu
            self.update_player_movement()

        # Check automatic portal teleport when touching a portal
        if self.teleport_cooldown <= 0:
            for portal in self.portals:
                p_rect = pygame.Rect(self.player_x + 4, self.player_y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
                port_rect = pygame.Rect(portal.get_world_x(), portal.get_world_y(), portal.get_width_pixels(), portal.get_height_pixels())
                if port_rect.colliderect(p_rect) or portal.contains_position(self.player_x + TILE_SIZE // 2, self.player_y + TILE_SIZE // 2):
                    if portal.direction == 'left':
                        if self.oldman_dialogue_state >= 2 or self.player_following_target == 'oldman' or self.is_quarter_completed('quarter1'):
                            self.enter_quarter("quarter1")
                            return
                        elif self.oldman_dialogue_state == 0 and self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Talk to the Old Man first to unlock Quarter 1!"
                            self.locked_portal_banner_timer = 2.0
                    elif portal.direction == 'right':
                        if not self.is_quarter_unlocked('quarter3'):
                            if self.locked_portal_banner_timer <= 0:
                                self.locked_portal_banner_msg = "Complete Quarter 2 to unlock Quarter 3!"
                                self.locked_portal_banner_timer = 2.0
                        elif self.skeleton_dialogue_state >= 2 or self.player_following_target == 'skeleton' or self.is_quarter_completed('quarter3'):
                            self.enter_quarter("quarter3")
                            return
                        elif self.skeleton_dialogue_state == 0 and self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Talk to the Skeleton first to unlock Quarter 3!"
                            self.locked_portal_banner_timer = 2.0
                    elif portal.direction == 'up':
                        if not self.is_quarter_unlocked('quarter2'):
                            if self.locked_portal_banner_timer <= 0:
                                self.locked_portal_banner_msg = "Complete Quarter 1 to unlock Quarter 2!"
                                self.locked_portal_banner_timer = 2.0
                        elif self.knight_dialogue_state >= 2 or self.player_following_target == 'knight' or self.is_quarter_completed('quarter2'):
                            self.enter_quarter("quarter2")
                            return
                        elif self.knight_dialogue_state == 0 and self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Talk to the Knight first to unlock Quarter 2!"
                            self.locked_portal_banner_timer = 2.0
                    elif portal.direction == 'down':
                        if not self.is_quarter_unlocked('quarter4'):
                            if self.locked_portal_banner_timer <= 0:
                                self.locked_portal_banner_msg = "Complete Quarter 3 to unlock Quarter 4!"
                                self.locked_portal_banner_timer = 2.0
                        elif self.bromen_dialogue_state >= 2 or self.player_following_target == 'bromen' or self.is_quarter_completed('quarter4'):
                            self.enter_quarter("quarter4")
                            return
                        elif self.bromen_dialogue_state == 0 and self.locked_portal_banner_timer <= 0:
                            self.locked_portal_banner_msg = "Talk to Bromen first to unlock Quarter 4!"
                            self.locked_portal_banner_timer = 2.0

        # Update portal animations
        for portal in self.portals:
            portal.update_animation()

        # Update camera
        self.update_camera()

    # ============================================================
    # UPDATE PLAYER FOLLOWING (Auto-follow NPC towards portal)
    # ============================================================
    def update_player_following(self):
        if not self.player_following_target:
            return

        moved = False

        if self.player_following_target == 'oldman':
            # Follow Old Man leftwards towards Left Portal (x=0, y=13*TILE_SIZE)
            hallway_y = 13 * TILE_SIZE
            follow_speed = 3.5 if (not self.npc_oldman_found or self.oldman_dialogue_state >= 3) else 2.0
            if abs(self.player_y - hallway_y) > 2:
                if self.player_y < hallway_y:
                    self.player_y += follow_speed
                    self.player_dir = "down"
                else:
                    self.player_y -= follow_speed
                    self.player_dir = "up"
                moved = True
            else:
                self.player_y = hallway_y
                if self.npc_oldman_found and self.oldman_dialogue_state == 2:
                    target_x = self.npc_oldman_x + 36
                else:
                    target_x = 0
                
                if self.player_x > target_x:
                    self.player_x -= follow_speed
                    self.player_dir = "left"
                    moved = True
                else:
                    if not self.npc_oldman_found or self.oldman_dialogue_state >= 3:
                        self.enter_quarter("quarter1")
                        return

        elif self.player_following_target == 'skeleton':
            # Follow Skeleton rightwards towards Right Portal (x=52*TILE_SIZE, y=13*TILE_SIZE)
            hallway_y = 13 * TILE_SIZE
            follow_speed = 3.5 if (not self.npc_skeleton_found or self.skeleton_dialogue_state >= 3) else 2.0
            if abs(self.player_y - hallway_y) > 2:
                if self.player_y < hallway_y:
                    self.player_y += follow_speed
                    self.player_dir = "down"
                else:
                    self.player_y -= follow_speed
                    self.player_dir = "up"
                moved = True
            else:
                self.player_y = hallway_y
                if self.npc_skeleton_found and self.skeleton_dialogue_state == 2:
                    target_x = self.npc_skeleton_x - 36
                else:
                    target_x = (self.COLS - 1) * TILE_SIZE
                
                if self.player_x < target_x:
                    self.player_x += follow_speed
                    self.player_dir = "right"
                    moved = True
                else:
                    if not self.npc_skeleton_found or self.skeleton_dialogue_state >= 3:
                        self.enter_quarter("quarter3")
                        return

        elif self.player_following_target == 'knight':
            # Follow Knight downwards towards Down Portal (x=25*TILE_SIZE, y=25*TILE_SIZE)
            corridor_x = 25 * TILE_SIZE
            follow_speed = 3.5 if (not self.npc_knight_found or self.knight_dialogue_state >= 3) else 2.0
            if abs(self.player_x - corridor_x) > 2:
                if self.player_x < corridor_x:
                    self.player_x += follow_speed
                    self.player_dir = "right"
                else:
                    self.player_x -= follow_speed
                    self.player_dir = "left"
                moved = True
            else:
                self.player_x = corridor_x
                if self.npc_knight_found and self.knight_dialogue_state == 2:
                    target_y = self.npc_knight_y - 36
                else:
                    target_y = (self.ROWS - 1) * TILE_SIZE
                
                if self.player_y < target_y:
                    self.player_y += follow_speed
                    self.player_dir = "down"
                    moved = True
                else:
                    if not self.npc_knight_found or self.knight_dialogue_state >= 3:
                        self.enter_quarter("quarter2")
                        return

        elif self.player_following_target == 'bromen':
            # Follow Bromen upwards towards North Portal (x=25*TILE_SIZE, y=0)
            corridor_x = 25 * TILE_SIZE
            follow_speed = 3.5 if (not self.npc_bromen_found or self.bromen_dialogue_state >= 3) else 2.0
            if abs(self.player_x - corridor_x) > 2:
                if self.player_x < corridor_x:
                    self.player_x += follow_speed
                    self.player_dir = "right"
                else:
                    self.player_x -= follow_speed
                    self.player_dir = "left"
                moved = True
            else:
                self.player_x = corridor_x
                if self.npc_bromen_found and self.bromen_dialogue_state == 2:
                    target_y = self.npc_bromen_y + 36
                else:
                    target_y = 0
                
                if self.player_y > target_y:
                    self.player_y -= follow_speed
                    self.player_dir = "up"
                    moved = True
                else:
                    if not self.npc_bromen_found or self.bromen_dialogue_state >= 3:
                        self.enter_quarter("quarter4")
                        return

        # Animate player while moving
        if moved:
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("footstep_stone")
        else:
            self.anim_frame = 0

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        # Block manual movement during active dialogue, while following an NPC, or during block timer
        if self.oldman_dialogue_state == 1 or self.skeleton_dialogue_state == 1 or self.knight_dialogue_state == 1 or self.bromen_dialogue_state == 1 or self.player_following_target or self.player_block_timer > 0:
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

        # Collision move
        new_x = self.player_x + vx
        new_y = self.player_y + vy

        if self.can_move(new_x, self.player_y):
            self.player_x = new_x
        if self.can_move(self.player_x, new_y):
            self.player_y = new_y

        # Animation
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
    # DRAW CORRIDOR FORCEFIELDS / BARRIERS FOR LOCKED QUARTERS
    # ============================================================
    def draw_corridor_barriers(self):
        """Renders animated glowing magical plasma forcefields, dual crystal pylons, and sleek badges across locked corridors."""
        t = pygame.time.get_ticks() * 0.001
        pulse = 0.5 + 0.5 * math.sin(t * 4.0)
        font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], max(11, int(11 * ZOOM)), bold=True)

        barriers = []
        # Quarter 2 (South corridor): row 16, cols 25, 26, 27
        if not self.is_quarter_unlocked('quarter2'):
            barriers.append({
                'world_x': 25 * TILE_SIZE,
                'world_y': 16 * TILE_SIZE,
                'width_tiles': 3,
                'height_tiles': 1,
                'label': "COMPLETE Q1 TO UNLOCK",
                'color': (239, 68, 68),
                'pylon_axis': 'horizontal'
            })

        # Quarter 3 (East corridor): col 28, rows 12, 13, 14
        if not self.is_quarter_unlocked('quarter3'):
            barriers.append({
                'world_x': 28 * TILE_SIZE,
                'world_y': 12 * TILE_SIZE,
                'width_tiles': 1,
                'height_tiles': 3,
                'label': "COMPLETE Q2 TO UNLOCK",
                'color': (239, 68, 68),
                'pylon_axis': 'vertical'
            })

        # Quarter 4 (North corridor): row 11, cols 25, 26, 27
        if not self.is_quarter_unlocked('quarter4'):
            barriers.append({
                'world_x': 25 * TILE_SIZE,
                'world_y': 11 * TILE_SIZE,
                'width_tiles': 3,
                'height_tiles': 1,
                'label': "COMPLETE Q3 TO UNLOCK",
                'color': (239, 68, 68),
                'pylon_axis': 'horizontal'
            })

        for b in barriers:
            bx = (b['world_x'] - self.camera_x) * ZOOM
            by = (b['world_y'] - self.camera_y) * ZOOM
            bw = int(b['width_tiles'] * TILE_SIZE * ZOOM)
            bh = int(b['height_tiles'] * TILE_SIZE * ZOOM)

            # Only draw if on screen
            if -bw <= bx <= self.width + bw and -bh <= by <= self.height + bh:
                # 1. Outer Radiant Ambient Forcefield Glow
                glow_pad = int(8 * ZOOM)
                glow_surf = pygame.Surface((bw + glow_pad * 2, bh + glow_pad * 2), pygame.SRCALPHA)
                glow_alpha = int(45 + 30 * pulse)
                pygame.draw.rect(glow_surf, (239, 68, 68, glow_alpha), (0, 0, bw + glow_pad * 2, bh + glow_pad * 2), border_radius=10)
                self.screen.blit(glow_surf, (bx - glow_pad, by - glow_pad))

                # 2. Main High-Energy Plasma Surface
                plasma_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                plasma_alpha = int(140 + 70 * pulse)
                pygame.draw.rect(plasma_surf, (220, 38, 38, plasma_alpha), (0, 0, bw, bh), border_radius=6)

                # 3. Dynamic Moving Laser Grid Scanlines
                if b['pylon_axis'] == 'horizontal':
                    laser_y = int(bh * (0.5 + 0.35 * math.sin(t * 6.0)))
                    pygame.draw.line(plasma_surf, (255, 255, 255, 240), (0, laser_y), (bw, laser_y), 3)
                    for i in range(4):
                        scan_x = int((t * 60 + i * (bw / 3.0)) % bw)
                        pygame.draw.line(plasma_surf, (254, 202, 202, 160), (scan_x, 0), (min(bw, scan_x + int(14 * ZOOM)), bh), 2)
                else:
                    laser_x = int(bw * (0.5 + 0.35 * math.sin(t * 6.0)))
                    pygame.draw.line(plasma_surf, (255, 255, 255, 240), (laser_x, 0), (laser_x, bh), 3)
                    for i in range(4):
                        scan_y = int((t * 60 + i * (bh / 3.0)) % bh)
                        pygame.draw.line(plasma_surf, (254, 202, 202, 160), (0, scan_y), (bw, min(bh, scan_y + int(14 * ZOOM))), 2)

                self.screen.blit(plasma_surf, (bx, by))

                # 4. Vibrant Neon Electric Border
                pygame.draw.rect(self.screen, (254, 202, 202), (bx, by, bw, bh), 2, border_radius=6)

                # 5. Dual Energy Emitter Pylons on Corridor Walls
                pylon_size = int(9 * ZOOM)
                if b['pylon_axis'] == 'horizontal':
                    pylons = [
                        (bx - pylon_size // 2, by + bh // 2),
                        (bx + bw - pylon_size // 2, by + bh // 2)
                    ]
                else:
                    pylons = [
                        (bx + bw // 2, by - pylon_size // 2),
                        (bx + bw // 2, by + bh - pylon_size // 2)
                    ]

                for px, py in pylons:
                    pygame.draw.circle(self.screen, (30, 41, 59), (int(px), int(py)), pylon_size)
                    pygame.draw.circle(self.screen, (251, 191, 36), (int(px), int(py)), pylon_size, 2)
                    crystal_r = int((pylon_size - 3) * (0.8 + 0.3 * pulse))
                    pygame.draw.circle(self.screen, (239, 68, 68), (int(px), int(py)), crystal_r)
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(px), int(py)), max(1, crystal_r // 2))

                # 6. Sleek Holographic Security Shield Badge
                badge_bob = math.sin(t * 4.0) * 3
                badge_w, badge_h = int(172 * ZOOM), int(26 * ZOOM)
                center_x = bx + bw / 2
                center_y = by + bh / 2 + badge_bob
                badge_rect = pygame.Rect(center_x - badge_w // 2, center_y - badge_h // 2, badge_w, badge_h)

                shadow_rect = badge_rect.copy()
                shadow_rect.y += 2
                pygame.draw.rect(self.screen, (0, 0, 0, 180), shadow_rect, border_radius=8)
                pygame.draw.rect(self.screen, (15, 23, 42), badge_rect, border_radius=8)
                border_color = (248, 113, 113) if pulse > 0.5 else (239, 68, 68)
                pygame.draw.rect(self.screen, border_color, badge_rect, 2, border_radius=8)

                lbl_surf = font.render(b['label'], True, (254, 240, 138) if pulse > 0.5 else (255, 255, 255))
                self.screen.blit(lbl_surf, lbl_surf.get_rect(center=badge_rect.center))

    # ============================================================
    # DRAW TILE
    # ============================================================
    def draw_tile(self, c, world_x, world_y):
        screen_x = (world_x - self.camera_x) * ZOOM
        screen_y = (world_y - self.camera_y) * ZOOM

        margin = TILE_SIZE * ZOOM * 2
        if (-margin <= screen_x <= self.width + margin and
                -margin <= screen_y <= self.height + margin):
            # Gracefully fallback to grass G tile so missing character boxes never render
            image = self.tile_images.get(c, self.tile_images.get('G', self.fallback_tile))
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
    # DRAW - MODIFIED to use self.render_map
    # ============================================================
    def draw(self):
        self.screen.fill((0, 0, 0))

        # Draw visible tiles using render_map
        start_col = max(0, int(self.camera_x / TILE_SIZE) - 2)
        end_col = min(self.COLS, int((self.camera_x + self.width / ZOOM) / TILE_SIZE) + 3)
        start_row = max(0, int(self.camera_y / TILE_SIZE) - 2)
        end_row = min(self.ROWS, int((self.camera_y + self.height / ZOOM) / TILE_SIZE) + 3)

        # Draw visible tiles using render_map (First pass: Skip trees and draw grass under them)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char == 'T':
                        # Draw grass under the tree so there is no black void under the player
                        self.draw_tile('G', col * TILE_SIZE, row * TILE_SIZE)
                    else:
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw portals
        for portal in self.portals:
            portal.draw(self.screen, self.camera_x, self.camera_y, ZOOM, self.width, self.height)

        # Draw Corridor Energy Forcefields for Locked Quarters
        self.draw_corridor_barriers()

        # Draw Portal Status Badges above portals (CLEARED / OPEN / LOCKED)
        DIR_MAP = {
            'left': 'quarter1',
            'up': 'quarter2',
            'right': 'quarter3',
            'down': 'quarter4'
        }
        for portal in self.portals:
            qid = DIR_MAP.get(portal.direction)
            if qid:
                sx = (portal.get_center_x() - self.camera_x) * ZOOM
                sy = (portal.get_world_y() - self.camera_y) * ZOOM
                bob = math.sin(self.frame_counter * 0.08) * 3
                
                badge_w, badge_h = int(105 * ZOOM), int(24 * ZOOM)
                bx = sx - badge_w // 2
                if portal.direction == 'down':
                    by = sy + portal.get_height_pixels() * ZOOM + 8 + bob
                else:
                    by = sy - badge_h - 8 + bob
                badge_rect = pygame.Rect(bx, by, badge_w, badge_h)
                
                b_font = pygame.font.SysFont("Comic Sans MS", int(11 * ZOOM), bold=True)
                
                if self.is_quarter_completed(qid):
                    # CLEARED (Gold)
                    pygame.draw.rect(self.screen, (15, 23, 42), badge_rect, border_radius=6)
                    pygame.draw.rect(self.screen, (255, 215, 0), badge_rect, 2, border_radius=6)
                    b_txt = b_font.render("CLEARED", True, (255, 215, 0))
                    self.screen.blit(b_txt, b_txt.get_rect(center=badge_rect.center))
                elif self.is_quarter_unlocked(qid):
                    # OPEN (Emerald green)
                    pygame.draw.rect(self.screen, (15, 23, 42), badge_rect, border_radius=6)
                    pygame.draw.rect(self.screen, (34, 197, 94), badge_rect, 2, border_radius=6)
                    b_txt = b_font.render("OPEN", True, (34, 197, 94))
                    self.screen.blit(b_txt, b_txt.get_rect(center=badge_rect.center))
                else:
                    # LOCKED (Ruby red)
                    pygame.draw.rect(self.screen, (15, 23, 42), badge_rect, border_radius=6)
                    pygame.draw.rect(self.screen, (239, 68, 68), badge_rect, 2, border_radius=6)
                    b_txt = b_font.render("LOCKED", True, (248, 113, 113))
                    self.screen.blit(b_txt, b_txt.get_rect(center=badge_rect.center))

        # Draw NPCs (before player so player is on top)
        # Bromen - Idle, Walking Up, or Quest Exclamation
        if self.npc_bromen_found:
            if self.bromen_dialogue_state == 2:
                if self.npc_bromen_up_sprites:
                    self.draw_npc_animated(self.npc_bromen_x, self.npc_bromen_y,
                                           self.npc_bromen_up_sprites, self.npc_bromen_anim_frame)
                elif self.npc_bromen_sprites:
                    self.draw_npc_animated(self.npc_bromen_x, self.npc_bromen_y,
                                           self.npc_bromen_sprites, self.npc_bromen_anim_frame)
            else:
                if self.npc_bromen_sprites:
                    self.draw_npc_animated(self.npc_bromen_x, self.npc_bromen_y,
                                           self.npc_bromen_sprites, self.npc_bromen_anim_frame)
                
                # Draw quest exclamation mark above Bromen's head if dialogue hasn't started and quarter is unlocked
                if self.bromen_dialogue_state == 0 and self.is_quarter_unlocked('quarter4'):
                    player_center_x = self.player_x + TILE_SIZE // 2
                    player_center_y = self.player_y + TILE_SIZE // 2
                    bro_center_x = self.npc_bromen_x + TILE_SIZE // 2
                    bro_center_y = self.npc_bromen_y + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - bro_center_x, player_center_y - bro_center_y)
                    
                    if dist < TILE_SIZE * 3.0:
                        screen_x = (self.npc_bromen_x - self.camera_x) * ZOOM
                        screen_y = (self.npc_bromen_y - self.camera_y) * ZOOM
                        
                        excl_font = pygame.font.SysFont("Comic Sans MS", int(18 * ZOOM), bold=True)
                        excl_surf = excl_font.render("!", True, (255, 0, 0))
                        
                        bounce = math.sin(self.frame_counter * 0.1) * 4 * ZOOM
                        
                        excl_x = screen_x + (TILE_SIZE * ZOOM) // 2 - excl_surf.get_width() // 2
                        excl_y = screen_y - excl_surf.get_height() - 4 * ZOOM + bounce
                        
                        shadow_surf = excl_font.render("!", True, (0, 0, 0))
                        self.screen.blit(shadow_surf, (excl_x + 1, excl_y + 1))
                        self.screen.blit(excl_surf, (excl_x, excl_y))

        # Oldman - Static or Animated Walking
        if self.npc_oldman_found:
            if self.oldman_dialogue_state == 2:
                target_y = (self.npc_oldman_tile_y + 1) * TILE_SIZE
                if self.npc_oldman_y < target_y and self.npc_oldman_down_sprites:
                    self.draw_npc_animated(self.npc_oldman_x, self.npc_oldman_y,
                                           self.npc_oldman_down_sprites, self.npc_oldman_anim_frame)
                elif self.npc_oldman_left_sprites:
                    self.draw_npc_animated(self.npc_oldman_x, self.npc_oldman_y,
                                           self.npc_oldman_left_sprites, self.npc_oldman_anim_frame)
                else:
                    self.draw_npc_static(self.npc_oldman_x, self.npc_oldman_y,
                                         self.npc_oldman_sprite)
            else:
                sprites = None
                if self.npc_oldman_dir == "left":
                    sprites = self.npc_oldman_left_sprites
                elif self.npc_oldman_dir == "right":
                    sprites = self.npc_oldman_right_sprites
                elif self.npc_oldman_dir == "up":
                    sprites = self.npc_oldman_up_sprites
                else:
                    sprites = self.npc_oldman_down_sprites

                if sprites:
                    self.draw_npc_static(self.npc_oldman_x, self.npc_oldman_y,
                                         sprites[0])
                else:
                    self.draw_npc_static(self.npc_oldman_x, self.npc_oldman_y,
                                         self.npc_oldman_sprite)
                
                # Draw quest exclamation mark above the Old Man's head if dialogue hasn't started and player is in proximity
                if self.oldman_dialogue_state == 0:
                    player_center_x = self.player_x + TILE_SIZE // 2
                    player_center_y = self.player_y + TILE_SIZE // 2
                    oldman_center_x = self.npc_oldman_x + TILE_SIZE // 2
                    oldman_center_y = self.npc_oldman_y + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - oldman_center_x, player_center_y - oldman_center_y)
                    
                    if dist < TILE_SIZE * 3.0:
                        screen_x = (self.npc_oldman_x - self.camera_x) * ZOOM
                        screen_y = (self.npc_oldman_y - self.camera_y) * ZOOM
                        
                        # Create floating quest indicator font matching visual aesthetics
                        excl_font = pygame.font.SysFont("Comic Sans MS", int(18 * ZOOM), bold=True)
                        excl_surf = excl_font.render("!", True, (255, 0, 0))  # Red color
                        
                        # Bounce animation (floating micro-animation)
                        bounce = math.sin(self.frame_counter * 0.1) * 4 * ZOOM
                        
                        excl_x = screen_x + (TILE_SIZE * ZOOM) // 2 - excl_surf.get_width() // 2
                        excl_y = screen_y - excl_surf.get_height() - 4 * ZOOM + bounce
                        
                        # Blit drop shadow
                        shadow_surf = excl_font.render("!", True, (0, 0, 0))
                        self.screen.blit(shadow_surf, (excl_x + 1, excl_y + 1))
                        # Blit main exclamation
                        self.screen.blit(excl_surf, (excl_x, excl_y))

        # Skeleton - Static or Animated Walking
        if self.npc_skeleton_found:
            if self.skeleton_dialogue_state == 2:
                target_y = (self.npc_skeleton_tile_y + 1) * TILE_SIZE
                if self.npc_skeleton_y < target_y and self.npc_skeleton_down_sprites:
                    self.draw_npc_animated(self.npc_skeleton_x, self.npc_skeleton_y,
                                           self.npc_skeleton_down_sprites, self.npc_skeleton_anim_frame)
                elif self.npc_skeleton_right_sprites:
                    self.draw_npc_animated(self.npc_skeleton_x, self.npc_skeleton_y,
                                           self.npc_skeleton_right_sprites, self.npc_skeleton_anim_frame)
                else:
                    self.draw_npc_static(self.npc_skeleton_x, self.npc_skeleton_y,
                                         self.npc_skeleton_sprite)
            else:
                sprites = None
                if self.npc_skeleton_dir == "left":
                    sprites = self.npc_skeleton_left_sprites
                elif self.npc_skeleton_dir == "right":
                    sprites = self.npc_skeleton_right_sprites
                elif self.npc_skeleton_dir == "up":
                    sprites = self.npc_skeleton_up_sprites
                else:
                    sprites = self.npc_skeleton_down_sprites

                if sprites:
                    self.draw_npc_static(self.npc_skeleton_x, self.npc_skeleton_y,
                                         sprites[0])
                else:
                    self.draw_npc_static(self.npc_skeleton_x, self.npc_skeleton_y,
                                         self.npc_skeleton_sprite)
                
                # Draw quest exclamation mark above Skeleton's head if dialogue hasn't started and quarter is unlocked
                if self.skeleton_dialogue_state == 0 and self.is_quarter_unlocked('quarter3'):
                    player_center_x = self.player_x + TILE_SIZE // 2
                    player_center_y = self.player_y + TILE_SIZE // 2
                    skel_center_x = self.npc_skeleton_x + TILE_SIZE // 2
                    skel_center_y = self.npc_skeleton_y + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - skel_center_x, player_center_y - skel_center_y)
                    
                    if dist < TILE_SIZE * 3.0:
                        screen_x = (self.npc_skeleton_x - self.camera_x) * ZOOM
                        screen_y = (self.npc_skeleton_y - self.camera_y) * ZOOM
                        
                        excl_font = pygame.font.SysFont("Comic Sans MS", int(18 * ZOOM), bold=True)
                        excl_surf = excl_font.render("!", True, (255, 0, 0))
                        
                        bounce = math.sin(self.frame_counter * 0.1) * 4 * ZOOM
                        
                        excl_x = screen_x + (TILE_SIZE * ZOOM) // 2 - excl_surf.get_width() // 2
                        excl_y = screen_y - excl_surf.get_height() - 4 * ZOOM + bounce
                        
                        shadow_surf = excl_font.render("!", True, (0, 0, 0))
                        self.screen.blit(shadow_surf, (excl_x + 1, excl_y + 1))
                        self.screen.blit(excl_surf, (excl_x, excl_y))

        # Knight - Static or Animated Walking
        if self.npc_knight_found:
            if self.knight_dialogue_state == 2:
                if self.npc_knight_down_sprites:
                    self.draw_npc_animated(self.npc_knight_x, self.npc_knight_y,
                                           self.npc_knight_down_sprites, self.npc_knight_anim_frame)
                else:
                    self.draw_npc_static(self.npc_knight_x, self.npc_knight_y,
                                         self.npc_knight_sprite)
            else:
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
                else:
                    self.draw_npc_static(self.npc_knight_x, self.npc_knight_y,
                                         self.npc_knight_sprite)
                
                # Draw quest exclamation mark above Knight's head if dialogue hasn't started and quarter is unlocked
                if self.knight_dialogue_state == 0 and self.is_quarter_unlocked('quarter2'):
                    player_center_x = self.player_x + TILE_SIZE // 2
                    player_center_y = self.player_y + TILE_SIZE // 2
                    knt_center_x = self.npc_knight_x + TILE_SIZE // 2
                    knt_center_y = self.npc_knight_y + TILE_SIZE // 2
                    dist = math.hypot(player_center_x - knt_center_x, player_center_y - knt_center_y)
                    
                    if dist < TILE_SIZE * 3.0:
                        screen_x = (self.npc_knight_x - self.camera_x) * ZOOM
                        screen_y = (self.npc_knight_y - self.camera_y) * ZOOM
                        
                        excl_font = pygame.font.SysFont("Comic Sans MS", int(18 * ZOOM), bold=True)
                        excl_surf = excl_font.render("!", True, (255, 0, 0))
                        
                        bounce = math.sin(self.frame_counter * 0.1) * 4 * ZOOM
                        
                        excl_x = screen_x + (TILE_SIZE * ZOOM) // 2 - excl_surf.get_width() // 2
                        excl_y = screen_y - excl_surf.get_height() - 4 * ZOOM + bounce
                        
                        shadow_surf = excl_font.render("!", True, (0, 0, 0))
                        self.screen.blit(shadow_surf, (excl_x + 1, excl_y + 1))
                        self.screen.blit(excl_surf, (excl_x, excl_y))

        # Draw player
        self.draw_player()

        # Draw visible tree tiles on top of everything (Second pass)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if row < len(self.render_map) and col < len(self.render_map[row]):
                    tile_char = self.render_map[row][col]
                    if tile_char == 'T':
                        self.draw_tile(tile_char, col * TILE_SIZE, row * TILE_SIZE)

        # Draw Area Title Animation
        if self.title_active:
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

        # Draw UI
        self.draw_ui()

        # Draw Dialogue Box
        self.draw_dialogue_box()

        # Draw Portal Warp Transition
        if self.portal_transition_active:
            self.draw_portal_transition()

    def draw_portal_transition(self):
        """Renders 3-second black loading screen with animated wave LOADING text and glowing energy capsule bar."""
        if not self.portal_transition_active or not self.portal_transition_theme:
            return

        # 1. Solid Pure Black Background to completely conceal loading delay
        self.screen.fill((0, 0, 0))

        theme = self.portal_transition_theme
        timer = self.portal_transition_timer
        progress = max(0.0, min(1.0, timer / self.portal_transition_duration))

        # 2. Ambient drifting star sparkles in the dark void
        for s in self.portal_transition_stars:
            sx = int(self.width // 2 + math.cos(s["angle"]) * (s["dist"] % (self.width // 2)))
            sy = int(self.height // 2 + math.sin(s["angle"]) * (s["dist"] % (self.height // 2)))
            if 0 <= sx < self.width and 0 <= sy < self.height:
                s_alpha = int(180 * (math.sin(timer * 4.0 + s["dist"]) * 0.4 + 0.6))
                s_surf = pygame.Surface((s["width"] * 2, s["width"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(s_surf, (*s["color"], s_alpha), (s["width"], s["width"]), s["width"])
                self.screen.blit(s_surf, (sx - s["width"], sy - s["width"]))

        # 3. Animated "LOADING..." Title (Traveling Sine Wave identical to Quarter Titles)
        base_y = self.height // 2 - 50
        x = self.width // 2 - self.loading_total_width // 2

        for i, data in enumerate(self.loading_letters):
            phase = timer * 7.0 - i * 0.45
            offset = math.sin(phase) * 12

            glow = data["glow"].copy()
            outline = data["outline"].copy()
            main = data["main"].copy()

            # Thematic Glow
            for gx in (-5, 0, 5):
                for gy in (-5, 0, 5):
                    self.screen.blit(glow, (x + gx, base_y + gy + offset))

            # Outline
            for ox in (-2, -1, 1, 2):
                for oy in (-2, -1, 1, 2):
                    self.screen.blit(outline, (x + ox, base_y + oy + offset))

            # Main text
            self.screen.blit(main, (x, base_y + offset))

            x += data["width"] + self.loading_spacing

        # 4. Premium Futuristic Energy Loading Bar (Centrally Focused, No Bottom Subtitle)
        bar_w = min(540, self.width - 100)
        bar_h = 24
        bar_x = (self.width - bar_w) // 2
        bar_y = base_y + 80
        primary_col = theme.get("primary", (56, 189, 248))
        accent_col = theme.get("accent", (250, 204, 21))

        # Soft ambient neon glow under the bar
        glow_surf = pygame.Surface((bar_w + 32, bar_h + 32), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*primary_col, 45), (0, 0, bar_w + 32, bar_h + 32), border_radius=18)
        self.screen.blit(glow_surf, (bar_x - 16, bar_y - 16))

        # Track background (Deep metallic glass)
        pygame.draw.rect(self.screen, (15, 23, 42), (bar_x, bar_y, bar_w, bar_h), border_radius=12)
        pygame.draw.rect(self.screen, (51, 65, 85), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=12)
        pygame.draw.rect(self.screen, primary_col, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=12)

        # Fill progress with smooth capsule rounding
        inner_margin = 3
        max_fill_w = bar_w - inner_margin * 2
        fill_w = int(max_fill_w * progress)

        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x + inner_margin, bar_y + inner_margin, fill_w, bar_h - inner_margin * 2)

            # Draw primary gradient base fill
            fill_surf = pygame.Surface((fill_w, fill_rect.height), pygame.SRCALPHA)
            fill_surf.fill(primary_col)

            # Horizontal gradient shading towards accent color
            for col_i in range(fill_w):
                ratio = col_i / float(max(1, max_fill_w))
                blend_r = int(primary_col[0] + (accent_col[0] - primary_col[0]) * ratio)
                blend_g = int(primary_col[1] + (accent_col[1] - primary_col[1]) * ratio)
                blend_b = int(primary_col[2] + (accent_col[2] - primary_col[2]) * ratio)
                pygame.draw.line(fill_surf, (blend_r, blend_g, blend_b), (col_i, 0), (col_i, fill_rect.height))

            # Glassy top specular reflection
            top_shine = pygame.Surface((fill_w, fill_rect.height // 2), pygame.SRCALPHA)
            top_shine.fill((255, 255, 255, 65))
            fill_surf.blit(top_shine, (0, 0))

            # Animated sweeping shimmer streak across the fill
            shimmer_cycle = (timer * 340) % (max_fill_w + 100) - 50
            if 0 <= shimmer_cycle < fill_w + 30:
                s_left = max(0, int(shimmer_cycle - 20))
                s_right = min(fill_w, int(shimmer_cycle + 20))
                if s_right > s_left:
                    shimmer_strip = pygame.Surface((s_right - s_left, fill_rect.height), pygame.SRCALPHA)
                    shimmer_strip.fill((255, 255, 255, 90))
                    fill_surf.blit(shimmer_strip, (s_left, 0))

            self.screen.blit(fill_surf, fill_rect.topleft)

            # Glowing energy tip spark at head of the progress bar
            spark_x = bar_x + inner_margin + fill_w
            spark_y = bar_y + bar_h // 2
            pulse_rad = int(math.sin(timer * 12.0) * 2 + 5)

            # Outer aura
            pygame.draw.circle(self.screen, (*accent_col, 180), (spark_x, spark_y), pulse_rad + 6, 2)
            pygame.draw.circle(self.screen, accent_col, (spark_x, spark_y), pulse_rad + 3)
            # Bright white center core
            pygame.draw.circle(self.screen, (255, 255, 255), (spark_x, spark_y), max(2, pulse_rad - 1))

        # 5. Crisp Centered Percentage Label inside the loading bar
        percent_str = f"{int(progress * 100)}%"
        pct_font = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
        # Drop shadow for readability
        pct_shadow = pct_font.render(percent_str, True, (0, 0, 0))
        pct_surf = pct_font.render(percent_str, True, (255, 255, 255))
        pct_center = (bar_x + bar_w // 2, bar_y + bar_h // 2)
        self.screen.blit(pct_shadow, pct_shadow.get_rect(center=(pct_center[0] + 1, pct_center[1] + 1)))
        self.screen.blit(pct_surf, pct_surf.get_rect(center=pct_center))

    # ============================================================
    # DRAW UI
    # ============================================================
    def draw_ui(self):
        # Refresh completed quarters status
        from db.save_system import get_completed_quarters, is_game_completed
        student_id = getattr(self.main_menu, 'student_id', None)
        self.completed_quarters = get_completed_quarters(student_id)

        # Draw Top HUD Stage Progress Tracker
        num_cleared = sum(1 for q in ['quarter1', 'quarter2', 'quarter3', 'quarter4'] if self.completed_quarters.get(q, {}).get("completed", False))
        hud_w, hud_h = 300, 36
        hud_x = (self.width - hud_w) // 2
        hud_y = 12
        hud_rect = pygame.Rect(hud_x, hud_y, hud_w, hud_h)
        pygame.draw.rect(self.screen, (15, 23, 42), hud_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 215, 0), hud_rect, 2, border_radius=8)

        hud_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        t_surf = hud_font.render(f"Quarters Mastered: {num_cleared}/4", True, (241, 245, 249))
        self.screen.blit(t_surf, (hud_x + 14, hud_y + 7))

        # 4 Golden Stars / Gem Medals
        star_x = hud_x + 212
        for i in range(4):
            is_on = i < num_cleared
            cx = star_x + i * 20
            cy = hud_y + hud_h // 2
            s_col = (255, 215, 0) if is_on else (71, 85, 105)
            pygame.draw.circle(self.screen, s_col, (cx, cy), 6)
            if is_on:
                pygame.draw.circle(self.screen, (254, 240, 138), (cx, cy), 3)
            pygame.draw.circle(self.screen, (255, 255, 255) if is_on else (51, 65, 85), (cx, cy), 6, 1)

        # Draw Locked Notification Banner if active
        if self.locked_portal_banner_timer > 0 and self.locked_portal_banner_msg:
            banner_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
            msg_surf = banner_font.render(self.locked_portal_banner_msg, True, (254, 242, 242))
            
            bw = msg_surf.get_width() + 40
            bh = 38
            bx = (self.width - bw) // 2
            by = 56
            
            b_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            b_surf.fill((15, 23, 42, 238))
            pygame.draw.rect(b_surf, (239, 68, 68), (0, 0, bw, bh), 2, border_radius=8)
            self.screen.blit(b_surf, (bx, by))
            
            # Drop shadow + main banner text
            sh_surf = banner_font.render(self.locked_portal_banner_msg, True, (0, 0, 0))
            self.screen.blit(sh_surf, (bx + 21, by + 9))
            self.screen.blit(msg_surf, (bx + 20, by + 8))

        # Reopen Grand Finale Button if all 4 completed
        if is_game_completed(student_id) and not self.grand_finale_active:
            btn_r = pygame.Rect(self.width - 170, 12, 150, 36)
            hov = btn_r.collidepoint(self.cursor_pos)
            bg = (245, 158, 11) if hov else (217, 119, 6)
            pygame.draw.rect(self.screen, bg, btn_r, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), btn_r, 2, border_radius=8)
            btn_txt = hud_font.render("Victory Card", True, (255, 255, 255))
            self.screen.blit(btn_txt, btn_txt.get_rect(center=btn_r.center))

        # Draw Grand Finale Modal if active
        if self.grand_finale_active:
            self.draw_grand_finale_popup()

        # Info panel
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
                f"Zoom: {ZOOM}x (Permanent)",
                f"Position: ({self.player_x // TILE_SIZE}, {self.player_y // TILE_SIZE})",
                f"Portals: {len(self.portals)}",
                f"NPCs: {npc_text}",
                f"Hand: {'YES' if self.hand_detected else 'NO'}",
                f"Gesture: {self.current_gesture}",
                f"Left Portal >> Quarter 1 | Up Portal >> Quarter 4",
                f"Right Portal >> Quarter 3 | Down Portal >> Quarter 2",
                f"Pause: Top-Right / Hold Fist"
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
    # DRAW DIALOGUE BOX
    # ============================================================
    def draw_dialogue_box(self):
        if self.oldman_dialogue_state == 1:
            speaker, text = self.dialogue_lines[self.oldman_dialogue_index]
        elif self.skeleton_dialogue_state == 1:
            speaker, text = self.skeleton_dialogue_lines[self.skeleton_dialogue_index]
        elif self.knight_dialogue_state == 1:
            speaker, text = self.knight_dialogue_lines[self.knight_dialogue_index]
        elif self.bromen_dialogue_state == 1:
            speaker, text = self.bromen_dialogue_lines[self.bromen_dialogue_index]
        else:
            return

        # Dialogue box layout
        box_width = self.width - 80
        box_height = 130
        box_x = 40
        box_y = self.height - box_height - 40

        # Background (semi-transparent black)
        dialogue_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(dialogue_surface, (20, 20, 20, 220), (0, 0, box_width, box_height), border_radius=10)
        pygame.draw.rect(dialogue_surface, (255, 215, 0, 255), (0, 0, box_width, box_height), width=3, border_radius=10) # Gold border
        self.screen.blit(dialogue_surface, (box_x, box_y))

        # Render speaker name
        if speaker == "Old Man":
            name_color = (255, 215, 0)
        elif speaker == "Skeleton":
            name_color = (200, 100, 255) # Cyan/Purple for Skeleton
        elif speaker == "Knight":
            name_color = (100, 200, 255) # Cyan/Blue for Knight
        elif speaker == "Bromen":
            name_color = (255, 180, 50) # Orange/Gold for Bromen
        else:
            name_color = (100, 255, 100) # Green for Student / Player

        name_text = self.font.render(speaker, True, name_color)
        self.screen.blit(name_text, (box_x + 20, box_y + 15))

        # Wrap text and render
        max_width = box_width - 40
        words = text.split(" ")
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_str = " ".join(current_line)
            if self.font.size(test_str)[0] > max_width:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        # Render dialogue lines with typewriter effect
        chars_remaining = int(self.dialogue_char_index)
        y_offset = box_y + 45
        for line in lines:
            if chars_remaining <= 0:
                break
            visible_line = line[:chars_remaining]
            chars_remaining -= len(line) + 1
            line_surface = self.font.render(visible_line, True, (255, 255, 255))
            self.screen.blit(line_surface, (box_x + 20, y_offset))
            y_offset += 24

        # Continue indicator
        is_finished = (self.dialogue_char_index >= len(text))
        if is_finished:
            if (self.frame_counter // 30) % 2 == 0:
                prompt = "Hold Fist to continue ▾"
                prompt_surface = self.small_font.render(prompt, True, (255, 215, 0))
                self.screen.blit(prompt_surface, (box_x + box_width - prompt_surface.get_width() - 20, box_y + box_height - 25))
        else:
            prompt = "Hold Fist to advance..."
            prompt_surface = self.small_font.render(prompt, True, (160, 160, 160))
            self.screen.blit(prompt_surface, (box_x + box_width - prompt_surface.get_width() - 20, box_y + box_height - 25))

    # ============================================================
    # HANDLE EVENT
    # ============================================================
    def handle_event(self, event):
        # Allow LoL camera to process middle mouse drag or Spacebar recentering
        self.lol_camera.handle_event(event)

        if getattr(self, 'portal_transition_active', False):
            return "handled"

        if self.grand_finale_active:
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN]:
                self.grand_finale_active = False
                self.grand_finale_dismissed = True
                return "handled"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.trigger_click(event.pos)
                return "handled"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.trigger_click(event.pos)
            return "handled"

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if self.advance_dialogue():
                    return "dialogue_advance"

                # If standing on a portal, allow Space/Enter to enter
                current_portal = None
                for portal in self.portals:
                    if portal.contains_position(self.player_x, self.player_y):
                        current_portal = portal
                        break
                if current_portal and self.teleport_cooldown <= 0:
                    if current_portal.direction == 'left':
                        if self.oldman_dialogue_state >= 2 or self.is_quarter_completed('quarter1'):
                            self.enter_quarter("quarter1")
                            return "quarter_entered"
                    elif current_portal.direction == 'up':
                        if self.is_quarter_unlocked('quarter2') and (self.knight_dialogue_state >= 2 or self.is_quarter_completed('quarter2')):
                            self.enter_quarter("quarter2")
                            return "quarter_entered"
                    elif current_portal.direction == 'right':
                        if self.is_quarter_unlocked('quarter3') and (self.skeleton_dialogue_state >= 2 or self.is_quarter_completed('quarter3')):
                            self.enter_quarter("quarter3")
                            return "quarter_entered"
                    elif current_portal.direction == 'down':
                        if self.is_quarter_unlocked('quarter4') and (self.bromen_dialogue_state >= 2 or self.is_quarter_completed('quarter4')):
                            self.enter_quarter("quarter4")
                            return "quarter_entered"

            if event.key == pygame.K_ESCAPE:
                if self.main_menu:
                    self.main_menu.current_screen = "menu"
                    self.main_menu.stage_select = None
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info
        return None

    # ============================================================
    # GRAND FINALE CEREMONY POPUP
    # ============================================================
    def draw_grand_finale_popup(self):
        # 1. Semi-transparent backdrop overlay
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 205))
        self.screen.blit(dim, (0, 0))

        # 2. Render Confetti & Celebration Sparkles
        for p in self.confetti_particles:
            pygame.draw.circle(self.screen, p["color"], (int(p["x"]), int(p["y"])), p["size"])

        # 3. Centered Victory Modal Card
        card_w, card_h = 620, 450
        card_x = (self.width - card_w) // 2
        card_y = (self.height - card_h) // 2
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        pygame.draw.rect(self.screen, (15, 23, 42), card_rect, border_radius=16)
        pygame.draw.rect(self.screen, (255, 215, 0), card_rect, 4, border_radius=16)

        # Fonts
        t_font = pygame.font.SysFont("Comic Sans MS", 21, bold=True)
        sub_font = pygame.font.SysFont("Comic Sans MS", 13)
        row_font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)

        # Title Header
        title = t_font.render("QUEST COMPLETE: GRAND CHAMPION!", True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(card_x + card_w // 2, card_y + 35)))

        sub = sub_font.render("Outstanding achievement! You have mastered all 4 Quarters of Cognitive Quest!", True, (226, 232, 240))
        self.screen.blit(sub, sub.get_rect(center=(card_x + card_w // 2, card_y + 65)))

        # Summary rows for Q1-Q4
        quarters_info = [
            ("quarter1", "Quarter 1: Storybook Meadow", "Shapes & Jigsaw Puzzles"),
            ("quarter2", "Quarter 2: Barangay Geometry", "Patterns & Bahay Kubo"),
            ("quarter3", "Quarter 3: Oasis Mirage", "Math Explorations & Caravan"),
            ("quarter4", "Quarter 4: Celestial Clocktower", "Water Temple Chrono Gears"),
        ]

        row_y = card_y + 95
        total_pts = 0
        for qid, title_str, desc_str in quarters_info:
            qdata = self.completed_quarters.get(qid, {})
            score = qdata.get("score", 100)
            pct = qdata.get("percentage", 100.0)
            total_pts += score

            row_rect = pygame.Rect(card_x + 30, row_y, card_w - 60, 52)
            pygame.draw.rect(self.screen, (30, 41, 59), row_rect, border_radius=8)
            pygame.draw.rect(self.screen, (51, 65, 85), row_rect, 1, border_radius=8)

            lbl_surf = row_font.render(f"{title_str}  ({desc_str})", True, (248, 250, 252))
            self.screen.blit(lbl_surf, (card_x + 45, row_y + 8))

            val_str = f"[Cleared]  Score: {score} pts  ({pct:.0f}%)"
            val_surf = sub_font.render(val_str, True, (255, 215, 0))
            self.screen.blit(val_surf, (card_x + 45, row_y + 28))

            row_y += 58

        # Total Cumulative Mastery Summary
        total_txt = row_font.render(f"Cumulative Score: {total_pts} / 400 pts   -   Rank: Cognitive Master (Master Tier)", True, (52, 211, 153))
        self.screen.blit(total_txt, total_txt.get_rect(center=(card_x + card_w // 2, card_y + 348)))

        # Close / Celebrate Button
        btn_rect = pygame.Rect(card_x + (card_w - 280) // 2, card_y + 375, 280, 44)
        hov = btn_rect.collidepoint(self.cursor_pos)
        bg = (34, 197, 94) if hov else (22, 163, 74)
        pygame.draw.rect(self.screen, bg, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, (134, 239, 172), btn_rect, 2, border_radius=10)
        btn_lbl = row_font.render("Celebrate & Explore!", True, (255, 255, 255))
        self.screen.blit(btn_lbl, btn_lbl.get_rect(center=btn_rect.center))

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()