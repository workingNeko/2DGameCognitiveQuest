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
        # Bromen NPC (animated & interactive teleport)
        self.npc_bromen_sprites = self.load_npc_sprites_animated(self.NPC_PATH_BROMEN, "bromen")
        self.npc_bromen_teleport_sprites = self.load_bromen_teleport_sprites()
        self.npc_bromen_anim_frame = 0
        self.npc_bromen_anim_timer = 0
        self.npc_bromen_x = 0
        self.npc_bromen_y = 0
        self.npc_bromen_tile_x = 0
        self.npc_bromen_tile_y = 0
        self.npc_bromen_found = False
        self.bromen_dialogue_state = 0  # 0: idle, 1: dialogue active, 2: teleporting, 3: disappeared
        self.bromen_dialogue_index = 0
        self.bromen_teleport_frame = 0
        self.bromen_teleport_timer = 0
        self.bromen_dialogue_lines = [
            ("Bromen", "Greetings! I am Bromen, master of the final realm."),
            ("Student", "Are you guarding the entrance to Quarter 4?"),
            ("Bromen", "Indeed! Prove your mastery inside. I shall await you there!"),
            ("Bromen", "*Teleports away*")
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
        self.camera_x = self.player_x + TILE_SIZE // 2 - (self.width // 2) / ZOOM
        self.camera_y = self.player_y + TILE_SIZE // 2 - (self.height // 2) / ZOOM
        
        # Apply camera boundaries
        max_cam_x = max(0, self.MAP_WIDTH - self.width / ZOOM)
        max_cam_y = max(0, self.MAP_HEIGHT - self.height / ZOOM)
        self.camera_x = max(0, min(self.camera_x, max_cam_x))
        self.camera_y = max(0, min(self.camera_y, max_cam_y))

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

        print(f"✅ StageSelect initialized with map: {self.ROWS}x{self.COLS}")
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

    def load_bromen_teleport_sprites(self):
        frames = []
        for i in range(8):
            filename = f"sprite_bromen_teleport{i:02d}.png"
            path = os.path.join(self.NPC_PATH_BROMEN, filename)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                frames.append(scaled)
                print(f"✅ Loaded Bromen teleport frame: {filename}")
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
            
            # Load Old Man walking left sprites
            self.npc_oldman_left_sprites = []
            for name in ["oldmanleft.png", "oldmanleft1.png", "oldmanleft2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_left_sprites.append(scaled)
                    print(f"✅ Loaded Old Man walking frame: {name}")
                else:
                    print(f"⚠️ Walking frame not found at: {path}")

            # Load Old Man walking down sprites
            self.npc_oldman_down_sprites = []
            for name in ["oldman.png", "oldmandown1.png", "oldmandown2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_down_sprites.append(scaled)
                    print(f"✅ Loaded Old Man down frame: {name}")
                else:
                    print(f"⚠️ Down frame not found at: {path}")

            # Load Old Man walking right sprites
            self.npc_oldman_right_sprites = []
            for name in ["oldmanright.png", "oldmanright1.png", "oldmanright2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_right_sprites.append(scaled)
                    print(f"✅ Loaded Old Man right frame: {name}")
                else:
                    print(f"⚠️ Right frame not found at: {path}")

            # Load Old Man walking up sprites
            self.npc_oldman_up_sprites = []
            for name in ["oldmanup.png", "oldmanup1.png", "oldmanup2.png"]:
                path = os.path.join(self.NPC_PATH_OLDMAN, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_oldman_up_sprites.append(scaled)
                    print(f"✅ Loaded Old Man up frame: {name}")
                else:
                    print(f"⚠️ Up frame not found at: {path}")
        except Exception as e:
            print(f"❌ Error loading Oldman: {e}")
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((200, 200, 200))
            self.npc_oldman_sprite = placeholder

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
                self.npc_skeleton_sprite = placeholder

            # Load Skeleton walking left sprites
            self.npc_skeleton_left_sprites = []
            for name in ["skeleton_left.png", "skeleton_left_1.png", "skeleton_left_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_left_sprites.append(scaled)
                    print(f"✅ Loaded Skeleton left frame: {name}")

            # Load Skeleton walking down sprites
            self.npc_skeleton_down_sprites = []
            for name in ["skeleton_down.png", "skeleton_down_1.png", "skeleton_down_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_down_sprites.append(scaled)
                    print(f"✅ Loaded Skeleton down frame: {name}")

            # Load Skeleton walking right sprites
            self.npc_skeleton_right_sprites = []
            for name in ["skeleton_right.png", "skeleton_right_1.png", "skeleton_right_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_right_sprites.append(scaled)
                    print(f"✅ Loaded Skeleton right frame: {name}")

            # Load Skeleton walking up sprites
            self.npc_skeleton_up_sprites = []
            for name in ["skeleton_up.png", "skeleton_up_1.png", "skeleton_up_2.png"]:
                path = os.path.join(self.NPC_PATH_SKELETON, name)
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    self.npc_skeleton_up_sprites.append(scaled)
                    print(f"✅ Loaded Skeleton up frame: {name}")
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
    # LOAD STATIC PORTALS - MODIFIED to use self.render_map
    # ============================================================
    def load_static_portals(self):
        # Use render_map for portal detection
        for y, row in enumerate(self.render_map):
            row_list = list(row)
            modified = False
            for x, c in enumerate(row):
                if c == 'r':
                    portal = self.Portal(x, y, 'right', is_static=True)
                    portal.set_animation(self.portal_frames_cache['right'])
                    self.portals.append(portal)
                    row_list[x] = '6'
                    modified = True
                elif c == 'l':
                    portal = self.Portal(x, y, 'left', is_static=True)
                    portal.set_animation(self.portal_frames_cache['left'])
                    self.portals.append(portal)
                    row_list[x] = '6'
                    modified = True
                elif c == 'u':
                    portal = self.Portal(x, y, 'up', is_static=True)
                    portal.set_animation(self.portal_frames_cache['up'])
                    self.portals.append(portal)
                    row_list[x] = '7'
                    modified = True
                elif c == 'd':
                    portal = self.Portal(x, y, 'down', is_static=True)
                    portal.set_animation(self.portal_frames_cache['down'])
                    self.portals.append(portal)
                    row_list[x] = '7'
                    modified = True
            if modified:
                self.render_map[y] = ''.join(row_list)

    # ============================================================
    # COLLISION - MODIFIED to use npc_positions_data
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
            # Check if it's a left portal (goes to Quarter1 - map1/map2/map3 randomized)
            if current_portal.direction == 'left':
                map_name = random.choice(["map1.txt", "map2.txt", "map3.txt"])
                print(f"🎮 Entering Quarter 1 - {map_name}")
                self.main_menu.current_screen = "quarter1"
                self.main_menu.quarter1 = Quarter1(self.screen, self.main_menu, map_name)
                self.main_menu.stage_select = None
                return True
            # Check if it's an up portal (goes to Quarter4 - map10.txt to map12.txt)
            elif current_portal.direction == 'up':
                map_name = random.choice(["map10.txt", "map11.txt", "map12.txt"])
                print(f"🎮 Entering Quarter 4 - {map_name}")
                self.main_menu.current_screen = "quarter4"
                self.main_menu.quarter4 = Quarter4(self.screen, self.main_menu, map_name)
                self.main_menu.stage_select = None
                return True
            # Check if it's a right portal (goes to Quarter3 - map7.txt to map9.txt)
            elif current_portal.direction == 'right':
                map_name = random.choice(["map7.txt", "map8.txt", "map9.txt"])
                print(f"🎮 Entering Quarter 3 - {map_name}")
                self.main_menu.current_screen = "quarter3"
                self.main_menu.quarter3 = Quarter3(self.screen, self.main_menu, map_name)
                self.main_menu.stage_select = None
                return True
            # Check if it's a down portal (goes to Quarter2 - map4.txt to map6.txt)
            elif current_portal.direction == 'down':
                map_name = random.choice(["map4.txt", "map5.txt", "map6.txt"])
                print(f"🎮 Entering Quarter 2 - {map_name}")
                self.main_menu.current_screen = "quarter2"
                self.main_menu.quarter2 = Quarter2(self.screen, self.main_menu, map_name)
                self.main_menu.stage_select = None
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
        self.camera_x = self.player_x + TILE_SIZE // 2 - (self.width // 2) / ZOOM
        self.camera_y = self.player_y + TILE_SIZE // 2 - (self.height // 2) / ZOOM
        
        # Apply camera boundaries
        max_cam_x = max(0, self.MAP_WIDTH - self.width / ZOOM)
        max_cam_y = max(0, self.MAP_HEIGHT - self.height / ZOOM)
        self.camera_x = max(0, min(self.camera_x, max_cam_x))
        self.camera_y = max(0, min(self.camera_y, max_cam_y))

        print(f"✅ Switched to new map: {self.map_loader.current_map_name}")

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
    # TRIGGER CLICK (called from main_menu)
    # ============================================================
    def trigger_click(self, pos):
        if self.oldman_dialogue_state == 1:
            self.oldman_dialogue_index += 1
            if self.oldman_dialogue_index >= len(self.dialogue_lines):
                self.oldman_dialogue_state = 2
                self.player_block_timer = 3.0
                print("🧙‍♂️ Dialog complete! Old Man starts moving left.")
            return

        if self.skeleton_dialogue_state == 1:
            self.skeleton_dialogue_index += 1
            if self.skeleton_dialogue_index >= len(self.skeleton_dialogue_lines):
                self.skeleton_dialogue_state = 2
                print("☠️ Dialog complete! Skeleton starts moving right to portal.")
            return

        if self.knight_dialogue_state == 1:
            self.knight_dialogue_index += 1
            if self.knight_dialogue_index >= len(self.knight_dialogue_lines):
                self.knight_dialogue_state = 2
                print("⚔️ Dialog complete! Knight starts moving down to portal.")
            return

        if self.bromen_dialogue_state == 1:
            self.bromen_dialogue_index += 1
            if self.bromen_dialogue_index >= len(self.bromen_dialogue_lines):
                self.bromen_dialogue_state = 2
                self.bromen_teleport_frame = 0
                self.bromen_teleport_timer = 0
                print("✨ Dialogue complete! Bromen starts teleporting away.")
            return

        # Trigger teleport on click/hold when standing on a portal
        if (self.oldman_dialogue_state in (0, 3)) and (self.skeleton_dialogue_state in (0, 3)) and (self.knight_dialogue_state in (0, 3)) and (self.bromen_dialogue_state in (0, 3)):
            current_portal = None
            for portal in self.portals:
                if portal.contains_position(self.player_x, self.player_y):
                    current_portal = portal
                    break
            
            if current_portal and self.teleport_cooldown <= 0:
                # Teleport to respective Quarter
                if current_portal.direction == 'left':
                    map_name = random.choice(["map1.txt", "map2.txt", "map3.txt"])
                    print(f"🎮 Entering Quarter 1 - {map_name}")
                    self.main_menu.current_screen = "quarter1"
                    self.main_menu.quarter1 = Quarter1(self.screen, self.main_menu, map_name)
                    self.main_menu.stage_select = None
                elif current_portal.direction == 'up':
                    map_name = random.choice(["map10.txt", "map11.txt", "map12.txt"])
                    print(f"🎮 Entering Quarter 4 - {map_name}")
                    self.main_menu.current_screen = "quarter4"
                    self.main_menu.quarter4 = Quarter4(self.screen, self.main_menu, map_name)
                    self.main_menu.stage_select = None
                elif current_portal.direction == 'right':
                    map_name = random.choice(["map7.txt", "map8.txt", "map9.txt"])
                    print(f"🎮 Entering Quarter 3 - {map_name}")
                    self.main_menu.current_screen = "quarter3"
                    self.main_menu.quarter3 = Quarter3(self.screen, self.main_menu, map_name)
                    self.main_menu.stage_select = None
                elif current_portal.direction == 'down':
                    map_name = random.choice(["map4.txt", "map5.txt", "map6.txt"])
                    print(f"🎮 Entering Quarter 2 - {map_name}")
                    self.main_menu.current_screen = "quarter2"
                    self.main_menu.quarter2 = Quarter2(self.screen, self.main_menu, map_name)
                    self.main_menu.stage_select = None

    # ============================================================
    # UPDATE
    # ============================================================
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        self.frame_counter += 1

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
                if dist < TILE_SIZE * 1.5:
                    self.bromen_dialogue_state = 1
                    self.bromen_dialogue_index = 0
                    
                    # Face each other
                    dx = self.npc_bromen_x - self.player_x
                    dy = self.npc_bromen_y - self.player_y
                    if abs(dx) > abs(dy):
                        self.player_dir = "left" if dx < 0 else "right"
                    else:
                        self.player_dir = "up" if dy < 0 else "down"

        # Update Bromen Teleport Animation
        if self.bromen_dialogue_state == 2:
            self.bromen_teleport_timer += 1
            if self.bromen_teleport_timer >= 6:
                self.bromen_teleport_timer = 0
                self.bromen_teleport_frame += 1
                if self.bromen_teleport_frame >= len(self.npc_bromen_teleport_sprites):
                    # Teleport finished! Disappear
                    self.bromen_dialogue_state = 3
                    self.npc_bromen_found = False
                    
                    # Remove NPC collision obstacle so player can pass
                    if 'B' in self.npc_positions_data:
                        self.npc_positions_data['B'] = []
                    
                    # Update self.game_map so the player can walk through
                    for r_idx, r_str in enumerate(self.game_map):
                        if 'B' in r_str:
                            self.game_map[r_idx] = r_str.replace('B', '8')
                            
                    print("✨ Bromen finished teleporting and disappeared from stage select!")


        # Proximity interaction check for Old Man NPC
        if self.npc_oldman_found:
            if self.oldman_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                oldman_center_x = self.npc_oldman_x + TILE_SIZE // 2
                oldman_center_y = self.npc_oldman_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - oldman_center_x, player_center_y - oldman_center_y)
                if dist < TILE_SIZE * 1.5:
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
                    
                print("🧙‍♂️ Old Man reached portal and disappeared from stage select!")

        # Proximity interaction check for Skeleton NPC
        if self.npc_skeleton_found:
            if self.skeleton_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                skeleton_center_x = self.npc_skeleton_x + TILE_SIZE // 2
                skeleton_center_y = self.npc_skeleton_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - skeleton_center_x, player_center_y - skeleton_center_y)
                if dist < TILE_SIZE * 1.5:
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
                        
                print("☠️ Skeleton reached portal and disappeared from stage select!")

        # Proximity interaction check for Knight NPC
        if self.npc_knight_found:
            if self.knight_dialogue_state == 0:
                player_center_x = self.player_x + TILE_SIZE // 2
                player_center_y = self.player_y + TILE_SIZE // 2
                knight_center_x = self.npc_knight_x + TILE_SIZE // 2
                knight_center_y = self.npc_knight_y + TILE_SIZE // 2
                dist = math.hypot(player_center_x - knight_center_x, player_center_y - knight_center_y)
                if dist < TILE_SIZE * 1.5:
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
                        
                print("⚔️ Knight reached down portal and disappeared from stage select!")

        # Update player movement using cursor from main menu
        self.update_player_movement()

        # Update portal animations
        for portal in self.portals:
            portal.update_animation()

        # Update camera
        self.update_camera()

    # ============================================================
    # UPDATE PLAYER MOVEMENT
    # ============================================================
    def update_player_movement(self):
        # Block movement during active dialogue or while Old Man / Skeleton / Knight / Bromen is in sequence
        if self.oldman_dialogue_state in (1, 2) or self.skeleton_dialogue_state in (1, 2) or self.knight_dialogue_state in (1, 2) or self.bromen_dialogue_state in (1, 2) or self.player_block_timer > 0:
            return

        vx, vy = 0, 0

        # Only move if hand is detected
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
            image = self.tile_images.get(c, self.fallback_tile)
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

        # Draw NPCs (before player so player is on top)
        # Bromen - Idle, Teleporting, or Quest Exclamation
        if self.npc_bromen_found:
            if self.bromen_dialogue_state == 2:
                if self.npc_bromen_teleport_sprites and self.bromen_teleport_frame < len(self.npc_bromen_teleport_sprites):
                    sprite = self.npc_bromen_teleport_sprites[self.bromen_teleport_frame]
                    self.draw_npc_static(self.npc_bromen_x, self.npc_bromen_y, sprite)
            else:
                if self.npc_bromen_sprites:
                    self.draw_npc_animated(self.npc_bromen_x, self.npc_bromen_y,
                                           self.npc_bromen_sprites, self.npc_bromen_anim_frame)
                
                # Draw quest exclamation mark above Bromen's head if dialogue hasn't started and player is in proximity
                if self.bromen_dialogue_state == 0:
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
                
                # Draw quest exclamation mark above Skeleton's head if dialogue hasn't started and player is in proximity
                if self.skeleton_dialogue_state == 0:
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
                
                # Draw quest exclamation mark above Knight's head if dialogue hasn't started and player is in proximity
                if self.knight_dialogue_state == 0:
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

    # ============================================================
    # DRAW UI
    # ============================================================
    def draw_ui(self):
        # Draw cursor from main menu (same as main menu)
        if self.hand_detected:
            if self.fist_start_time > 0:
                color = (255, 200, 0)  # Yellow when holding fist
            else:
                color = (255, 255, 255)  # White normally

            pygame.draw.circle(self.screen, color, self.cursor_pos, 15, 2)
            pygame.draw.circle(self.screen, (255, 100, 100), self.cursor_pos, 4)

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
                f"Left Portal → Quarter 1 | Up Portal → Quarter 4",
                f"Right Portal → Quarter 3 | Down Portal → Quarter 2",
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

        # Render dialogue lines
        y_offset = box_y + 45
        for line in lines:
            line_surface = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(line_surface, (box_x + 20, y_offset))
            y_offset += 24

        # Continue indicator (blinking)
        if (self.frame_counter // 30) % 2 == 0:
            prompt = "Hold Fist or Press Space to continue..."
            prompt_surface = self.small_font.render(prompt, True, (180, 180, 180))
            self.screen.blit(prompt_surface, (box_x + box_width - prompt_surface.get_width() - 20, box_y + box_height - 25))

    # ============================================================
    # HANDLE EVENT
    # ============================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.oldman_dialogue_state == 1:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.oldman_dialogue_index += 1
                    if self.oldman_dialogue_index >= len(self.dialogue_lines):
                        self.oldman_dialogue_state = 2
                        self.player_block_timer = 3.0
                        print("🧙‍♂️ Dialog complete! Old Man starts moving left.")
                    return "dialogue_advance"
            elif self.skeleton_dialogue_state == 1:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.skeleton_dialogue_index += 1
                    if self.skeleton_dialogue_index >= len(self.skeleton_dialogue_lines):
                        self.skeleton_dialogue_state = 2
                        print("☠️ Dialog complete! Skeleton starts moving right.")
                    return "dialogue_advance"
            elif self.knight_dialogue_state == 1:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.knight_dialogue_index += 1
                    if self.knight_dialogue_index >= len(self.knight_dialogue_lines):
                        self.knight_dialogue_state = 2
                        print("⚔️ Dialog complete! Knight starts moving down.")
                    return "dialogue_advance"
            elif self.bromen_dialogue_state == 1:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.bromen_dialogue_index += 1
                    if self.bromen_dialogue_index >= len(self.bromen_dialogue_lines):
                        self.bromen_dialogue_state = 2
                        self.bromen_teleport_frame = 0
                        self.bromen_teleport_timer = 0
                        print("✨ Dialogue complete! Bromen starts teleporting away.")
                    return "dialogue_advance"

            if event.key == pygame.K_ESCAPE:
                if self.main_menu:
                    self.main_menu.current_screen = "menu"
                    self.main_menu.stage_select = None
                return "back"
            elif event.key == pygame.K_i:
                self.show_info = not self.show_info
        return None

    # ============================================================
    # CLEANUP
    # ============================================================
    def cleanup(self):
        cv2.destroyAllWindows()