# screens/tutorial.py - Live Interactive Gameplay Showcase & Gesture Video Demonstration Tutorial
import pygame
import os
import sys
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import math
import time
import cv2
import numpy as np
from core.camera_system import LoLCamera

TILE_SIZE = 32
ZOOM = 1.50
SPEED = 2.2

class TutorialScreen:
    def __init__(self, screen, main_menu):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()

        # Gesture tracking state
        self.cursor_pos = (self.width // 2, self.height // 2)
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9
        self.click_ready = False
        self.hand_detected = False

        # Paths
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.PLAYER_PATH = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "player")
        self.OBJECTS_PATH = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "tiles")
        self.NPC_PATH_OLDMAN = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "oldman")
        self.PORTAL_PATH = os.path.join(self.BASE_DIR, "assets", "images", "sprites", "objects", "portal")

        # Load Sprites & Tiles
        self.player_sprites = self.load_player_sprites()
        self.tile_sprites = self.load_tile_sprites()
        self.npc_frames = self.load_npc_sprites()
        self.portal_frames = self.load_portal_sprites()

        # Tutorial Map File (assets/map/tutorial_map.txt)
        self.map_path = os.path.join(self.BASE_DIR, "assets", "map", "tutorial_map.txt")
        self.map_grid = self.load_tutorial_map()

        # Player State
        self.player_x = 3 * TILE_SIZE
        self.player_y = 5 * TILE_SIZE
        self.player_dir = "right"
        self.anim_frame = 0
        self.anim_timer = 0

        # Guide NPC State
        self.npc_tile_x = 14
        self.npc_tile_y = 5
        self.npc_anim_frame = 0
        self.npc_anim_timer = 0

        # Exit Portal State (Scanned from 'r' in tutorial_map.txt)
        self.portal_tile_x = 20
        self.portal_tile_y = 5
        for r_idx, row in enumerate(self.map_grid):
            for c_idx, char in enumerate(row):
                if char == 'r':
                    self.portal_tile_x = c_idx
                    self.portal_tile_y = r_idx
                    print(f"[PORTAL] Tutorial Exit Portal ('r') mapped at tile: ({c_idx}, {r_idx})")

        self.portal_anim_frame = 0
        self.portal_anim_timer = 0

        # Map Dimensions & LoL Camera
        self.MAP_WIDTH = (len(self.map_grid[0]) if self.map_grid else 25) * TILE_SIZE
        self.MAP_HEIGHT = (len(self.map_grid) if self.map_grid else 12) * TILE_SIZE
        self.lol_camera = LoLCamera(self.width, self.height, zoom=ZOOM)
        self.lol_camera.snap_to(self.player_x, self.player_y, TILE_SIZE, self.MAP_WIDTH, self.MAP_HEIGHT)
        self.camera_x = self.lol_camera.camera_x
        self.camera_y = self.lol_camera.camera_y

        # Tutorial Gameplay Phase (1 = Move, 2 = Interact, 3 = Quiz, 4 = Exit Portal)
        self.phase = 1
        self.intro_dialog_open = True
        self.phase_banner_timer = 0.0
        self.phase_transition_timer = 0.0
        self.click_dest = None
        self._fist_click_triggered = False

        # Quiz Modal State for Phase 3
        self.quiz_state = 0 # 0=closed, 1=question open, 2=wrong retry, 3=correct
        self.eliminated_choice = None
        self.quiz_attempts = 0
        self.wrong_feedback_msg = ""
        self.sample_question = {
            "title": "Tutorial Challenge",
            "question": "What is 2 + 2?",
            "choices": ["A. 3", "B. 4", "C. 5", "D. 6"],
            "correct": 1
        }

        # Fonts
        self.banner_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 20, bold=True)
        self.dialog_header_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 25, bold=True)
        self.dialog_q_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 22, bold=True)
        self.dialog_choice_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 20, bold=True)
        self.dialog_btn_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 20, bold=True)
        self.card_title_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18, bold=True)
        self.huge_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 26, bold=True)
        self.intro_title_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 34, bold=True)
        self.ui_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 15, bold=True)
        self.skip_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 16, bold=True)

        # Introduction Cinematic Animation State
        self.intro_anim_active = True
        self.intro_anim_timer = 0.0
        self.intro_anim_duration = 3.2
        self.intro_sound_played = False
        self.intro_particles = []
        for _ in range(45):
            self.intro_particles.append({
                "x": float(self.width // 2 + (np.random.rand() - 0.5) * 700),
                "y": float(self.height // 2 + (np.random.rand() - 0.5) * 450),
                "vx": float((np.random.rand() - 0.5) * 50),
                "vy": float((np.random.rand() - 0.5) * 50 - 15),
                "size": float(np.random.rand() * 4 + 2),
                "color": (251, 191, 36) if np.random.rand() > 0.4 else (255, 255, 255),
                "phase": float(np.random.rand() * 6.28)
            })

        # Gesture-Only Demonstration Video State (Plays before interactive gameplay)
        self.demo_video_active = True
        self.demo_video_chapter = 0 # 0: Camera Setup, 1: Open Hand Walk, 2: Fist Click, 3: Live Practice Arena
        self.demo_video_timer = 0.0
        self.demo_video_playing = True
        self.demo_video_chapter_duration = 5.2
        self.demo_practice_clicked = False
        self.demo_practice_fist_hold = 0.0
        from core.report_card import CelebrationParticleSystem
        self.demo_practice_particles = CelebrationParticleSystem()

        # Universal In-Stage Pause Menu
        from core.pause_menu import InGamePauseMenu
        self.pause_menu = InGamePauseMenu(self.screen, self.width, self.height, self.main_menu, return_callback=self.finish_tutorial, restart_callback=self.restart_tutorial)

        # Particle FX & Interactive Practice Stars
        self.celebration_particles = CelebrationParticleSystem()
        self.practice_stars = [
            {"tile_x": 7, "tile_y": 5, "collected": False, "anim": 0.0},
            {"tile_x": 11, "tile_y": 5, "collected": False, "anim": 0.0}
        ]
        self.star_popup_text = ""
        self.star_popup_timer = 0.0

        # Performance Caches
        self._scaled_tile_cache = {}
        self._scaled_sprite_cache = {}
        self._dim_overlay = None

        print("[TUTORIAL] Live Interactive Gameplay Tutorial Initialized with Gesture Demonstration Video!")

    def restart_tutorial(self):
        """Restarts the tutorial screen."""
        from screens.tutorial import TutorialScreen
        self.main_menu.tutorial = TutorialScreen(self.screen, self.main_menu)

    # ============================================================
    # ASSET & MAP LOADERS
    # ============================================================
    def load_tutorial_map(self):
        """Loads the tutorial map from assets/map/tutorial_map.txt with fallback"""
        if os.path.exists(self.map_path):
            try:
                with open(self.map_path, "r") as f:
                    lines = [line.rstrip("\r\n") for line in f if line.strip()]
                if lines:
                    print(f"[OK] Loaded tutorial map from: {self.map_path} ({len(lines)}x{len(lines[0])})")
                    return lines
            except Exception as e:
                print(f"[WARN] Error reading tutorial map file: {e}")

        # Fallback grid
        return [
            "TTTTTTTTTTTTTTTTTTTTTTTT",
            "TGGGGGGGGGGGGGGGGGGGGGGGT",
            "TGGGGGGGGGGGGGGGGGGGGGGGT",
            "TGGPGGGGGGGGGGGGGGGGGGGGT",
            "TGGPGGGGGGGGGGGGGGGGGGGGT",
            "TGGPPPPPPPPPPPPPPPGGGGGGT",
            "TGGPGGGGGGGGGGGGGPGGGGGGT",
            "TGGPGGGGGGGGGGGGGPGGGGGGT",
            "TGGGGGGGGGGGGGGGGGGGGGGGT",
            "TGGGGGGGGGGGGGGGGGGGGGGGT",
            "TGGGGGGGGGGGGGGGGGGGGGGGT",
            "TTTTTTTTTTTTTTTTTTTTTTTT"
        ]

    def load_player_sprites(self):
        prefix = "boy"
        if hasattr(self, 'main_menu') and self.main_menu and getattr(self.main_menu, 'selected_student', None):
            gender = self.main_menu.selected_student.get("gender")
            if gender and str(gender).lower() in ["female", "girl", "f"]:
                prefix = "female"

        def load_sprite(name):
            path = os.path.join(self.PLAYER_PATH, name)
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            except Exception:
                p = pygame.Surface((TILE_SIZE, TILE_SIZE))
                p.fill((59, 130, 246))
                pygame.draw.circle(p, (255, 255, 255), (TILE_SIZE // 2, TILE_SIZE // 2), TILE_SIZE // 3)
                return p

        return {
            "down": [load_sprite(f"{prefix}_down_1.png"), load_sprite(f"{prefix}_down_2.png")],
            "left": [load_sprite(f"{prefix}_left_1.png"), load_sprite(f"{prefix}_left_2.png")],
            "right": [load_sprite(f"{prefix}_right_1.png"), load_sprite(f"{prefix}_right_2.png")],
            "up": [load_sprite(f"{prefix}_up_1.png"), load_sprite(f"{prefix}_up_2.png")]
        }

    def load_tile_sprites(self):
        tiles = {}
        tile_map = {
            'G': "002.png",
            'P': "034.png",
            'r': "034.png",
            'T': "016.png",
            '#': "003.png",
            '6': "010.png"
        }
        for key, filename in tile_map.items():
            path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    tiles[key] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                else:
                    p = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    p.fill((34, 197, 94))
                    tiles[key] = p
            except Exception:
                p = pygame.Surface((TILE_SIZE, TILE_SIZE))
                p.fill((34, 197, 94))
                tiles[key] = p
        return tiles

    def load_npc_sprites(self):
        frames = []
        for name in ["oldman.png", "oldmandown1.png", "oldmandown2.png"]:
            path = os.path.join(self.NPC_PATH_OLDMAN, name)
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    frames.append(pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)))
            except Exception:
                pass
        if not frames:
            p = pygame.Surface((TILE_SIZE, TILE_SIZE))
            p.fill((245, 158, 11))
            pygame.draw.circle(p, (255, 255, 255), (TILE_SIZE // 2, TILE_SIZE // 2), 12)
            frames.append(p)
        return frames

    def load_portal_sprites(self):
        frames = []
        for i in range(9):
            filename = f"sprite_right_portal{i}.png"
            path = os.path.join(self.PORTAL_PATH, filename)
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    scaled_width = TILE_SIZE * 3
                    scaled_height = TILE_SIZE * 3
                    frames.append(pygame.transform.scale(img, (scaled_width, scaled_height)))
            except Exception as e:
                print(f"[WARN] Error loading tutorial portal frame {filename}: {e}")

        if not frames:
            p = pygame.Surface((TILE_SIZE * 3, TILE_SIZE * 3), pygame.SRCALPHA)
            pygame.draw.circle(p, (74, 222, 128), (TILE_SIZE * 3 // 2, TILE_SIZE * 3 // 2), TILE_SIZE * 3 // 2)
            frames.append(p)
        else:
            print(f"[OK] Loaded {len(frames)} portal animation frames for Tutorial!")
        return frames

    # ============================================================
    # GESTURE & UPDATE
    # ============================================================
    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME
        self.current_gesture = current_gesture
        self.hand_detected = (current_gesture not in ["NO HAND", "NO HAND (GRACE)"])

    def update(self):
        if hasattr(self, 'pause_menu') and self.pause_menu.is_paused:
            return

        # 1. Introduction Cinematic Animation update
        if getattr(self, 'intro_anim_active', False):
            if not getattr(self, 'intro_sound_played', False):
                self.intro_sound_played = True
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("success")
            
            self.intro_anim_timer += 0.016
            for p in getattr(self, 'intro_particles', []):
                p["x"] += p["vx"] * 0.016
                p["y"] += p["vy"] * 0.016
                p["phase"] += 0.05
            
            if self.intro_anim_timer >= getattr(self, 'intro_anim_duration', 3.2):
                self.intro_anim_active = False
            return

        # 2. Demonstration Video update (Gesture-only training showcase)
        if getattr(self, 'demo_video_active', False):
            if getattr(self, 'demo_video_playing', True):
                self.demo_video_timer += 0.016
                if self.demo_video_timer >= getattr(self, 'demo_video_chapter_duration', 5.2):
                    self.demo_video_timer = 0.0
                    self.demo_video_chapter = (self.demo_video_chapter + 1) % 4

            if hasattr(self, 'demo_practice_particles'):
                self.demo_practice_particles.update(0.016)

            # Check proactive fist hold during Demonstration Video
            if self.fist_start_time > 0 and self.current_gesture == "FIST":
                hold = time.time() - self.fist_start_time
                if hold >= self.CLICK_HOLD_TIME and not getattr(self, '_fist_click_triggered', False):
                    self._fist_click_triggered = True
                    self.trigger_click(self.cursor_pos)
            else:
                self._fist_click_triggered = False
            return

        # Proactive gesture fist-hold click trigger in active gameplay
        if self.fist_start_time > 0 and self.current_gesture == "FIST":
            hold = time.time() - self.fist_start_time
            if hold >= self.CLICK_HOLD_TIME and not getattr(self, '_fist_click_triggered', False):
                self._fist_click_triggered = True
                print(f"[TUTORIAL] Fist click triggered in Tutorial at {self.cursor_pos}")
                self.trigger_click(self.cursor_pos)
        else:
            self._fist_click_triggered = False

        # Update LoL-style camera with cursor lead and edge scrolling
        self.lol_camera.update(
            self.player_x,
            self.player_y,
            cursor_pos=self.cursor_pos,
            map_width=self.MAP_WIDTH,
            map_height=self.MAP_HEIGHT,
            tile_size=TILE_SIZE,
            enable_edge_scroll=(self.quiz_state == 0)
        )
        self.camera_x = self.lol_camera.camera_x
        self.camera_y = self.lol_camera.camera_y

        # Animate NPC & Portal
        self.npc_anim_timer += 0.05
        self.npc_anim_frame = int(self.npc_anim_timer) % len(self.npc_frames)

        self.portal_anim_timer += 0.15
        self.portal_anim_frame = int(self.portal_anim_timer) % len(self.portal_frames)

        # Update Particle System
        if hasattr(self, 'celebration_particles'):
            self.celebration_particles.update(0.016)

        # Update & Check Practice Star Collection (Interactive Steering Demonstration)
        if self.phase in [1, 2] and self.quiz_state == 0:
            for star in self.practice_stars:
                star["anim"] += 0.05
                if not star["collected"]:
                    s_dist = math.hypot(self.player_x - star["tile_x"] * TILE_SIZE, self.player_y - star["tile_y"] * TILE_SIZE)
                    if s_dist < 1.8 * TILE_SIZE:
                        star["collected"] = True
                        star_sx = (star["tile_x"] * TILE_SIZE - self.camera_x + TILE_SIZE / 2) * ZOOM
                        star_sy = (star["tile_y"] * TILE_SIZE - self.camera_y + TILE_SIZE / 2) * ZOOM
                        if hasattr(self, 'celebration_particles'):
                            self.celebration_particles.spawn_burst(int(star_sx), int(star_sy), count=30)
                        if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                            self.main_menu.audio_manager.play_sfx("star_chime")
                        
                        collected_count = sum(1 for s in self.practice_stars if s["collected"])
                        if collected_count == 1:
                            self.star_popup_text = "⭐ Star 1/2 Caught! Great Gesture Steering!"
                        else:
                            self.star_popup_text = "⭐ All Stars Caught! Steer to Guide Sage!"
                        self.star_popup_timer = 2.5
                        print(f"[TUTORIAL] Collected Practice Star at ({star['tile_x']}, {star['tile_y']})!")

        if self.star_popup_timer > 0:
            self.star_popup_timer -= 0.016

        # Player Movement (Active during Phase 1, Phase 2, and Phase 4 when quiz modal is closed)
        if self.quiz_state == 0:
            self.update_player_movement()

        # Check Phase Transitions
        npc_dist = math.hypot(self.player_x - self.npc_tile_x * TILE_SIZE, self.player_y - self.npc_tile_y * TILE_SIZE)
        portal_dist = math.hypot(self.player_x - self.portal_tile_x * TILE_SIZE, self.player_y - self.portal_tile_y * TILE_SIZE)

        # Proximity to NPC immediately triggers the question dialogue
        if self.phase in [1, 2] and npc_dist < 2.5 * TILE_SIZE:
            self.phase = 3
            self.quiz_state = 1
            self.click_dest = None
            print("[TUTORIAL] Player approached Guide NPC: Automatically Triggered Question Dialogue!")

        if self.phase == 4 and portal_dist < 1.8 * TILE_SIZE:
            print("[WIN] Exit Portal Entered! Tutorial Complete!")
            self.finish_tutorial()

    def update_player_movement(self):
        vx, vy = 0, 0
        current_speed = SPEED

        # Check keyboard controls (development fallback)
        keys = pygame.key.get_pressed()
        has_key_input = (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d] or
                         keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s])
        if has_key_input:
            if getattr(self, 'intro_dialog_open', False):
                self.intro_dialog_open = False
            self.click_dest = None
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                vx = -current_speed
                self.player_dir = "left"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                vx = current_speed
                self.player_dir = "right"
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                vy = -current_speed
                self.player_dir = "up"
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                vy = current_speed
                self.player_dir = "down"

        # Check Click-to-Move Destination
        elif getattr(self, 'click_dest', None) is not None:
            player_screen_x = (self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM
            player_screen_y = (self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM
            cursor_x, cursor_y = self.cursor_pos
            cd_dx = cursor_x - player_screen_x
            cd_dy = cursor_y - player_screen_y
            if abs(cd_dx) > 65 or abs(cd_dy) > 65:
                self.click_dest = None
            else:
                cdx = self.click_dest[0] - self.player_x
                cdy = self.click_dest[1] - self.player_y
                cd_dist = math.hypot(cdx, cdy)
                if cd_dist > 6.0:
                    vx = (cdx / cd_dist) * current_speed
                    vy = (cdy / cd_dist) * current_speed
                    if abs(cdx) > abs(cdy):
                        self.player_dir = "right" if cdx > 0 else "left"
                    else:
                        self.player_dir = "down" if cdy > 0 else "up"
                else:
                    self.click_dest = None

        # Universal Hand Gesture / Cursor Steering
        if getattr(self, 'click_dest', None) is None and not has_key_input:
            player_screen_x = (self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM
            player_screen_y = (self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM
            cursor_x, cursor_y = self.cursor_pos
            dx = cursor_x - player_screen_x
            dy = cursor_y - player_screen_y

            deadzone = 45.0
            if abs(dx) > deadzone or abs(dy) > deadzone:
                if getattr(self, 'intro_dialog_open', False):
                    self.intro_dialog_open = False

                if abs(dx) > deadzone:
                    vx = current_speed if dx > 0 else -current_speed
                if abs(dy) > deadzone:
                    vy = current_speed if dy > 0 else -current_speed

                if abs(dx) > abs(dy):
                    self.player_dir = "right" if dx > 0 else "left"
                else:
                    self.player_dir = "down" if dy > 0 else "up"

        # Apply movement with collision
        moved_x, moved_y = False, False
        if vx != 0 and self.can_move(self.player_x + vx, self.player_y):
            self.player_x += vx
            moved_x = True
        if vy != 0 and self.can_move(self.player_x, self.player_y + vy):
            self.player_y += vy
            moved_y = True

        if getattr(self, 'click_dest', None) is not None and (vx != 0 or vy != 0):
            if not moved_x and not moved_y:
                self.click_dest = None

        if vx != 0 or vy != 0:
            self.anim_timer += 1
            if self.anim_timer >= 16:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("footstep_stone")
        else:
            self.anim_frame = 0

    def can_move(self, x, y):
        feet_rect = pygame.Rect(x + 6, y + 16, 20, 14)
        for r, row in enumerate(self.map_grid):
            for c, tile in enumerate(row):
                if tile == 'T' or tile == '#':
                    tile_rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if feet_rect.colliderect(tile_rect):
                        return False
        return True

    # ============================================================
    # EVENT & CLICK HANDLERS
    # ============================================================
    def handle_event(self, event):
        if hasattr(self, 'pause_menu') and self.pause_menu.handle_event(event):
            return "blocked"

        # 1. Intro Animation Skip
        if getattr(self, 'intro_anim_active', False):
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
               (event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]):
                self.intro_anim_active = False
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("click")
                return

        # 2. Demonstration Video Event Handling
        if getattr(self, 'demo_video_active', False):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.cursor_pos = event.pos
                self.handle_demo_video_click(event.pos)
                return
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    # Advance chapter or launch
                    if self.demo_video_chapter < 3:
                        self.demo_video_chapter += 1
                        self.demo_video_timer = 0.0
                    else:
                        self.demo_video_active = False
                    if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                        self.main_menu.audio_manager.play_sfx("click")
                    return
                elif event.key == pygame.K_ESCAPE:
                    self.demo_video_active = False
                    if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                        self.main_menu.audio_manager.play_sfx("click")
                    return
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    self.demo_video_chapter = min(3, self.demo_video_chapter + 1)
                    self.demo_video_timer = 0.0
                    return
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    self.demo_video_chapter = max(0, self.demo_video_chapter - 1)
                    self.demo_video_timer = 0.0
                    return

        self.lol_camera.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.cursor_pos = event.pos
            self.trigger_click(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.cursor_pos = event.pos
        elif event.type == pygame.KEYDOWN:
            combined_mod = pygame.key.get_mods() if hasattr(pygame.key, 'get_mods') else 0
            ctrl_pressed = bool(combined_mod & pygame.KMOD_CTRL)
            shift_pressed = bool(combined_mod & pygame.KMOD_SHIFT)

            pressed_keys = pygame.key.get_pressed() if hasattr(pygame.key, 'get_pressed') else None
            if pressed_keys is not None:
                if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
                    ctrl_pressed = True
                if pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]:
                    shift_pressed = True

            is_complete_shortcut = (
                event.key in [pygame.K_F7, pygame.K_F10]
                or ((ctrl_pressed or shift_pressed) and event.key in [pygame.K_c, pygame.K_o])
                or event.key in [pygame.K_c, pygame.K_o]
            )
            if is_complete_shortcut:
                self.phase = 4
                self.quiz_state = 0
                self.intro_anim_active = False
                self.intro_dialog_open = False
                self.demo_video_active = False
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("success")
                return "shortcut_complete"

            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                if getattr(self, 'intro_dialog_open', False) and self.phase == 1 and self.quiz_state == 0:
                    self.intro_dialog_open = False
                    if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                        self.main_menu.audio_manager.play_sfx("dialogue_blip")
                    return
                if self.quiz_state == 0:
                    npc_dist = math.hypot(self.player_x - self.npc_tile_x * TILE_SIZE, self.player_y - self.npc_tile_y * TILE_SIZE)
                    portal_dist = math.hypot(self.player_x - self.portal_tile_x * TILE_SIZE, self.player_y - self.portal_tile_y * TILE_SIZE)
                    if npc_dist < 3.5 * TILE_SIZE and self.phase in [1, 2, 3]:
                        if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                            self.main_menu.audio_manager.play_sfx("dialogue_blip")
                        self.phase = 3
                        self.quiz_state = 1
                        self.click_dest = None
                    elif portal_dist < 3.0 * TILE_SIZE and self.phase == 4:
                        self.finish_tutorial()
                    else:
                        self.lol_camera.recenter()
                elif self.quiz_state == 1:
                    self.trigger_click(self.cursor_pos)
                elif self.quiz_state == 2:
                    self.quiz_state = 1
                elif self.quiz_state == 3:
                    self.quiz_state = 0
                    self.phase = 4
            elif event.key == pygame.K_ESCAPE:
                if getattr(self, 'intro_dialog_open', False):
                    self.intro_dialog_open = False
                elif hasattr(self, 'pause_menu'):
                    self.pause_menu.toggle_pause()
                else:
                    self.finish_tutorial()
            elif self.quiz_state == 1:
                if event.key in [pygame.K_1, pygame.K_a]:
                    self.submit_quiz_answer(0)
                elif event.key in [pygame.K_2, pygame.K_b]:
                    self.submit_quiz_answer(1)
                elif event.key in [pygame.K_3, pygame.K_c]:
                    self.submit_quiz_answer(2)
                elif event.key in [pygame.K_4, pygame.K_d]:
                    self.submit_quiz_answer(3)

    def submit_quiz_answer(self, choice_idx):
        if choice_idx == self.eliminated_choice:
            return
        if choice_idx == self.sample_question["correct"]:
            self.quiz_state = 3  # Correct
            if hasattr(self, 'celebration_particles'):
                self.celebration_particles.spawn_burst(self.width // 2, self.height // 2, count=35)
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("correct")
                self.main_menu.audio_manager.play_sfx("star_chime")
            print("[OK] Correct Answer in Tutorial Quiz!")
        else:
            self.quiz_attempts += 1
            self.eliminated_choice = choice_idx
            self.wrong_feedback_msg = "Almost! You have 1 try remaining. Pick again!"
            self.quiz_state = 2 if self.quiz_attempts < 2 else 3
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("wrong")
            print("[FAIL] Wrong Answer in Tutorial Quiz -> Showing 2-Attempt Mechanics!")

    def handle_demo_video_click(self, pos):
        """Processes user clicks or fist-hold selections inside the Demonstration Video Player"""
        vw = min(1060, self.width - 40)
        vh = min(580, self.height - 40)
        vx = (self.width - vw) // 2
        vy = (self.height - vh) // 2

        # 1. Skip Video Button (Top Right)
        skip_btn = pygame.Rect(vx + vw - 160, vy + 14, 144, 34)
        if skip_btn.collidepoint(pos):
            self.demo_video_active = False
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            return

        # 2. Chapter Navigation Tabs
        tab_y = vy + 60
        tab_w = (vw - 40 - 30) // 4
        tab_h = 38
        for i in range(4):
            tx = vx + 20 + i * (tab_w + 10)
            t_rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            if t_rect.collidepoint(pos):
                self.demo_video_chapter = i
                self.demo_video_timer = 0.0
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("click")
                return

        # 3. Control Bar Buttons (Bottom)
        bar_y = vy + vh - 58
        prev_btn = pygame.Rect(vx + 24, bar_y, 110, 40)
        play_btn = pygame.Rect(vx + 144, bar_y, 110, 40)
        next_btn = pygame.Rect(vx + 264, bar_y, 110, 40)
        start_btn = pygame.Rect(vx + vw - 270, bar_y, 246, 40)

        if prev_btn.collidepoint(pos):
            self.demo_video_chapter = max(0, self.demo_video_chapter - 1)
            self.demo_video_timer = 0.0
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            return

        if play_btn.collidepoint(pos):
            self.demo_video_playing = not self.demo_video_playing
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            return

        if next_btn.collidepoint(pos):
            self.demo_video_chapter = min(3, self.demo_video_chapter + 1)
            self.demo_video_timer = 0.0
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            return

        if start_btn.collidepoint(pos):
            self.demo_video_active = False
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("success")
            return

        # 4. Interactive Practice Test Button inside Chapter 3
        if self.demo_video_chapter == 3:
            practice_btn = pygame.Rect(vx + 60, vy + 280, 360, 60)
            if practice_btn.collidepoint(pos):
                self.demo_practice_clicked = True
                if hasattr(self, 'demo_practice_particles'):
                    self.demo_practice_particles.spawn_burst(practice_btn.centerx, practice_btn.centery, count=40)
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("correct")
                    self.main_menu.audio_manager.play_sfx("star_chime")

    def trigger_click(self, pos=None):
        if pos is None:
            pos = self.cursor_pos

        # Check Pause Menu clicks first
        if hasattr(self, 'pause_menu') and self.pause_menu.handle_click(pos):
            return
        if hasattr(self, 'pause_menu') and self.pause_menu.is_paused:
            return

        # If in active gameplay phase or quiz, bypass intro/demo
        if self.phase > 1 or self.quiz_state > 0:
            self.intro_anim_active = False
            self.demo_video_active = False

        # Skip intro animation on any click
        if getattr(self, 'intro_anim_active', False):
            self.intro_anim_active = False
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            return

        # Demonstration Video Clicks
        if getattr(self, 'demo_video_active', False):
            self.handle_demo_video_click(pos)
            return

        # 1. Skip Button (Top Right)
        skip_rect = pygame.Rect(self.width - 310, 18, 165, 36)
        if skip_rect.collidepoint(pos):
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")
            self.finish_tutorial()
            return

        # 2. Welcome Dialogue Dismissal
        if getattr(self, 'intro_dialog_open', False) and self.phase == 1 and self.quiz_state == 0:
            box_w = min(self.width - 40, 960)
            box_h = 440
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            welcome_rect = pygame.Rect(box_x, box_y, box_w, box_h)

            screen_npc_x = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM
            npc_rect = pygame.Rect(screen_npc_x - 30, screen_npc_y - 30, TILE_SIZE * ZOOM + 60, TILE_SIZE * ZOOM + 60)

            self.intro_dialog_open = False
            if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                self.main_menu.audio_manager.play_sfx("click")

            if npc_rect.collidepoint(pos):
                self.phase = 3
                self.quiz_state = 1
                self.click_dest = None
                print("[TUTORIAL] Opening Sample Quiz Modal via click/interact!")
                return
            if welcome_rect.collidepoint(pos):
                return

        # 3. Guide Sage NPC Interaction
        if self.quiz_state == 0 and self.phase in [1, 2, 3]:
            screen_npc_x = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM
            npc_rect = pygame.Rect(screen_npc_x - 30, screen_npc_y - 30, TILE_SIZE * ZOOM + 60, TILE_SIZE * ZOOM + 60)
            player_npc_dist = math.hypot(self.player_x - self.npc_tile_x * TILE_SIZE, self.player_y - self.npc_tile_y * TILE_SIZE)
            is_fist_interact = (self.current_gesture == "FIST" and player_npc_dist < 3.5 * TILE_SIZE)
            if npc_rect.collidepoint(pos) or is_fist_interact:
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("dialogue_blip")
                self.phase = 3
                self.quiz_state = 1
                self.click_dest = None
                print("[TUTORIAL] Opening Sample Quiz Modal via click/interact!")
                return

        # 4. Phase 4: Exit Portal Click Interaction
        if self.phase == 4 and self.quiz_state == 0:
            p_sx = (self.portal_tile_x * TILE_SIZE - self.camera_x) * ZOOM
            p_sy = (self.portal_tile_y * TILE_SIZE - self.camera_y) * ZOOM
            portal_rect = pygame.Rect(p_sx - 40, p_sy - 40, TILE_SIZE * 3 * ZOOM + 80, TILE_SIZE * 3 * ZOOM + 80)
            portal_dist = math.hypot(self.player_x - self.portal_tile_x * TILE_SIZE, self.player_y - self.portal_tile_y * TILE_SIZE)
            is_fist_portal = (self.current_gesture == "FIST" and portal_dist < 3.0 * TILE_SIZE)
            if portal_rect.collidepoint(pos) or is_fist_portal or portal_dist < 1.8 * TILE_SIZE:
                print("[WIN] Exit Portal Clicked/Entered! Tutorial Complete!")
                self.finish_tutorial()
                return

        # 5. Phase 3: Sample Quiz Dialog Clicks
        if self.quiz_state == 1:
            box_w, box_h = 780, 480
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            button_w, button_h = 740, 52
            button_x = box_x + (box_w - button_w) // 2
            button_y_start = box_y + 160
            spacing = 64

            # Check floating demonstration card click (Option B)
            target_btn_y = button_y_start + 1 * spacing
            demo_card_x = box_x + box_w + 16
            demo_card_y = target_btn_y - 24
            demo_card_rect = pygame.Rect(demo_card_x, demo_card_y, 220, 100)
            if demo_card_rect.collidepoint(pos):
                self.submit_quiz_answer(1)
                return

            for i in range(4):
                if i == self.eliminated_choice:
                    continue
                btn_rect = pygame.Rect(button_x, button_y_start + i * spacing - 2, button_w, button_h + 4)
                if btn_rect.collidepoint(pos):
                    self.submit_quiz_answer(i)
                    return

        # 6. Retry Dialog Clicks
        elif self.quiz_state == 2:
            box_w, box_h = 740, 340
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 250, 260, 52)
            card_rect = pygame.Rect(box_x, box_y, box_w, box_h)
            if btn_rect.collidepoint(pos) or card_rect.collidepoint(pos):
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("click")
                self.quiz_state = 1
                return

        # 7. Correct Dialog Clicks
        elif self.quiz_state == 3:
            box_w, box_h = 740, 340
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 250, 260, 52)
            card_rect = pygame.Rect(box_x, box_y, box_w, box_h)
            if btn_rect.collidepoint(pos) or card_rect.collidepoint(pos):
                if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
                    self.main_menu.audio_manager.play_sfx("click")
                self.quiz_state = 0
                self.phase = 4
                print("[TUTORIAL] Tutorial Phase 4: Portal Unlocked! Guide student to Exit Portal.")
                return

        # 8. Click-to-Move on walkable ground
        if self.quiz_state == 0 and not getattr(self, 'intro_dialog_open', False):
            world_x = pos[0] / ZOOM + self.camera_x
            world_y = pos[1] / ZOOM + self.camera_y
            self.click_dest = (world_x, world_y)
            print(f"[TUTORIAL] Click-to-move destination set at ({world_x:.1f}, {world_y:.1f})")

    def finish_tutorial(self):
        from db.save_system import set_tutorial_completed
        student_id = getattr(self.main_menu, 'student_id', None)
        if student_id is not None:
            set_tutorial_completed(self.main_menu, student_id, completed=True)
        
        print("[GO] Tutorial Complete! Opening Stage Select...")
        from screens.stageselect import StageSelect
        self.main_menu.current_screen = "stage_select"
        self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)
        if hasattr(self.main_menu, 'audio_manager') and self.main_menu.audio_manager:
            self.main_menu.audio_manager.play_sfx("stage_enter")

    # ============================================================
    # MAIN DRAW PIPELINE
    # ============================================================
    def draw(self):
        self.screen.fill((15, 23, 42))

        # 1. Render Map Tiles
        start_col = max(0, int(self.camera_x // TILE_SIZE))
        end_col = min(len(self.map_grid[0]) if self.map_grid else 0, int((self.camera_x + self.width / ZOOM) // TILE_SIZE) + 2)
        start_row = max(0, int(self.camera_y // TILE_SIZE))
        end_row = min(len(self.map_grid), int((self.camera_y + self.height / ZOOM) // TILE_SIZE) + 2)

        for r in range(start_row, end_row):
            row_str = self.map_grid[r]
            for c in range(start_col, min(len(row_str), end_col)):
                tile_type = row_str[c]
                tile_surf = self.tile_sprites.get(tile_type, self.tile_sprites.get('G'))
                if tile_surf:
                    screen_x = int((c * TILE_SIZE - self.camera_x) * ZOOM)
                    screen_y = int((r * TILE_SIZE - self.camera_y) * ZOOM)
                    scaled_size = int(TILE_SIZE * ZOOM) + 1
                    if scaled_size not in self._scaled_tile_cache:
                        self._scaled_tile_cache[scaled_size] = {}
                    if tile_type not in self._scaled_tile_cache[scaled_size]:
                        self._scaled_tile_cache[scaled_size][tile_type] = pygame.transform.scale(tile_surf, (scaled_size, scaled_size))
                    self.screen.blit(self._scaled_tile_cache[scaled_size][tile_type], (screen_x, screen_y))

        # 2. Render Practice Stars (Interactive Steering Objects)
        t_sec = pygame.time.get_ticks() * 0.001
        for star in self.practice_stars:
            if not star["collected"]:
                st_x = (star["tile_x"] * TILE_SIZE - self.camera_x + TILE_SIZE / 2) * ZOOM
                st_y = (star["tile_y"] * TILE_SIZE - self.camera_y + TILE_SIZE / 2) * ZOOM
                bob_y = st_y + math.sin(t_sec * 5.0 + star["tile_x"]) * 6 * ZOOM
                pulse_r = int((14 + math.sin(t_sec * 6.0) * 3) * ZOOM)

                # Outer soft aura
                halo_surf = pygame.Surface((pulse_r * 4, pulse_r * 4), pygame.SRCALPHA)
                pygame.draw.circle(halo_surf, (251, 191, 36, 120), (pulse_r * 2, pulse_r * 2), pulse_r * 2)
                self.screen.blit(halo_surf, (int(st_x - pulse_r * 2), int(bob_y - pulse_r * 2)))

                # 5-pointed star polygon
                star_pts = []
                for i in range(10):
                    r = (14 if i % 2 == 0 else 6.5) * ZOOM
                    ang = i * math.pi / 5 - math.pi / 2
                    star_pts.append((st_x + r * math.cos(ang), bob_y + r * math.sin(ang)))
                pygame.draw.polygon(self.screen, (254, 240, 138), star_pts)
                pygame.draw.polygon(self.screen, (245, 158, 11), star_pts, int(2 * ZOOM))

        # 3. Render Guide NPC (Oldman Sage)
        if self.npc_frames:
            npc_screen_x = int((self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM)
            npc_screen_y = int((self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM)
            npc_scaled = pygame.transform.scale(self.npc_frames[self.npc_anim_frame], (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
            self.screen.blit(npc_scaled, (npc_screen_x, npc_screen_y))

        # 4. Render Exit Portal
        if self.portal_frames:
            portal_screen_x = int((self.portal_tile_x * TILE_SIZE - self.camera_x) * ZOOM)
            portal_screen_y = int((self.portal_tile_y * TILE_SIZE - self.camera_y) * ZOOM)
            portal_scaled = pygame.transform.scale(self.portal_frames[self.portal_anim_frame], (int(TILE_SIZE * 3 * ZOOM), int(TILE_SIZE * 3 * ZOOM)))
            self.screen.blit(portal_scaled, (portal_screen_x, portal_screen_y))

        # 5. Render Player Hero
        pl_sx = int((self.player_x - self.camera_x) * ZOOM)
        pl_sy = int((self.player_y - self.camera_y) * ZOOM)
        dir_sprites = self.player_sprites.get(self.player_dir, self.player_sprites["down"])
        player_frame = dir_sprites[self.anim_frame]
        scaled_player = pygame.transform.scale(player_frame, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
        self.screen.blit(scaled_player, (pl_sx, pl_sy))

        # 6. Floating Star Pickup Celebration Popup
        if self.star_popup_timer > 0 and self.star_popup_text:
            p_pop_y = pl_sy - 30 * ZOOM - (2.5 - self.star_popup_timer) * 15
            pop_surf = self.ui_font.render(self.star_popup_text, True, (255, 255, 255))
            pop_w, pop_h = pop_surf.get_width() + 20, pop_surf.get_height() + 8
            pop_rect = pygame.Rect(pl_sx + (TILE_SIZE * ZOOM) / 2 - pop_w / 2, p_pop_y, pop_w, pop_h)

            pop_bg = pygame.Surface((pop_w, pop_h), pygame.SRCALPHA)
            pop_bg.fill((20, 83, 45, 220))
            self.screen.blit(pop_bg, pop_rect)
            pygame.draw.rect(self.screen, (251, 191, 36), pop_rect, 2, border_radius=8)
            self.screen.blit(pop_surf, pop_surf.get_rect(center=pop_rect.center))

        # 7. Celebration Particles
        if hasattr(self, 'celebration_particles'):
            self.celebration_particles.draw(self.screen)

        # 7b. Introduction Cinematic Animation (if active)
        if getattr(self, 'intro_anim_active', False):
            self.draw_intro_animation()
            if hasattr(self, 'pause_menu') and self.pause_menu.is_paused:
                self.pause_menu.draw_modal(self.cursor_pos)
            return

        # 7c. Demonstration Video Player (Gesture-Only Video Showcase & Practice)
        if getattr(self, 'demo_video_active', False):
            self.draw_demonstration_video()
            if hasattr(self, 'pause_menu') and self.pause_menu.is_paused:
                self.pause_menu.draw_modal(self.cursor_pos)
            return

        # 8. Demonstration Animation Overlay (Visual guide trail, animated steering, and radar)
        self.draw_demonstration_overlay()

        # 9. Dynamic Compass Pointers & On-Screen Quest Badges
        self.draw_compass_and_badges()

        # 10. Top Visual Gameplay Banner
        self.draw_top_banner()

        # 11. Prominent Glassmorphism Skip Button
        skip_rect = pygame.Rect(self.width - 310, 18, 165, 36)
        skip_hov = skip_rect.collidepoint(self.cursor_pos)

        shadow_rect = skip_rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(self.screen, (0, 0, 0, 140), shadow_rect, border_radius=10)

        skip_surf = pygame.Surface((skip_rect.width, skip_rect.height), pygame.SRCALPHA)
        skip_bg = (220, 38, 38, 230) if skip_hov else (15, 23, 42, 235)
        pygame.draw.rect(skip_surf, skip_bg, (0, 0, skip_rect.width, skip_rect.height), border_radius=10)
        self.screen.blit(skip_surf, skip_rect.topleft)

        border_col = (251, 191, 36) if skip_hov else (148, 163, 184)
        pygame.draw.rect(self.screen, border_col, skip_rect, 2, border_radius=10)

        skip_txt = self.skip_font.render("Skip Tutorial", True, (255, 255, 255))
        self.screen.blit(skip_txt, (skip_rect.x + 14, skip_rect.y + 8))

        pill_rect = pygame.Rect(skip_rect.right - 54, skip_rect.y + 6, 44, 24)
        pygame.draw.rect(self.screen, (30, 41, 59), pill_rect, border_radius=6)
        pygame.draw.rect(self.screen, (251, 191, 36) if skip_hov else (100, 116, 139), pill_rect, 1, border_radius=6)
        esc_txt = self.ui_font.render("SKIP", True, (251, 191, 36) if skip_hov else (203, 213, 225))
        self.screen.blit(esc_txt, esc_txt.get_rect(center=pill_rect.center))

        # 11b. Real-Time Hand Gesture & Input Tracker Helper
        self.draw_hand_tracker_helper()

        # 12. Render Welcome Dialogue or Quiz Modal Dialogs
        if getattr(self, 'intro_dialog_open', False) and self.quiz_state == 0 and self.phase == 1:
            self.draw_welcome_dialog()
        elif self.quiz_state == 1:
            self.draw_sample_quiz_dialog()
            self.draw_quiz_gesture_demo()
        elif self.quiz_state == 2:
            self.draw_sample_wrong_dialog()
        elif self.quiz_state == 3:
            self.draw_sample_correct_dialog()

        # 13. In-Game Universal Pause Button & Modal Overlay
        if hasattr(self, 'pause_menu'):
            self.pause_menu.draw_button(self.cursor_pos)
            if self.pause_menu.is_paused:
                self.pause_menu.draw_modal(self.cursor_pos)

    # ============================================================
    # CINEMATIC INTRODUCTION ANIMATION
    # ============================================================
    def draw_intro_animation(self):
        """Renders a cinematic, magical, and joyful introduction animation welcoming Grade 2 students"""
        t_anim = getattr(self, 'intro_anim_timer', 0.0)
        t_dur = getattr(self, 'intro_anim_duration', 3.2)
        now = pygame.time.get_ticks()
        t = now * 0.001

        fade_alpha = 255
        if t_anim > 2.4:
            fade_alpha = max(0, int(255 * (1.0 - (t_anim - 2.4) / 0.8)))

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 15, 30, min(240, fade_alpha)))
        self.screen.blit(overlay, (0, 0))

        for p in getattr(self, 'intro_particles', []):
            px, py = p["x"], p["y"]
            p_size = p["size"] + math.sin(t * 4.0 + p["phase"]) * 1.5
            p_alpha = max(0, min(255, int(p.get("alpha", 200) * (fade_alpha / 255.0))))
            p_surf = pygame.Surface((int(p_size * 4), int(p_size * 4)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p["color"], p_alpha), (int(p_size * 2), int(p_size * 2)), int(p_size))
            self.screen.blit(p_surf, (int(px - p_size * 2), int(py - p_size * 2)))

        cx, cy = self.width // 2, self.height // 2 + 10

        ring_r1 = int(110 + math.sin(t * 3.0) * 8)
        ring_r2 = int(140 + math.cos(t * 2.5) * 6)
        
        rune_surf = pygame.Surface((ring_r2 * 2 + 40, ring_r2 * 2 + 40), pygame.SRCALPHA)
        r_cx, r_cy = ring_r2 + 20, ring_r2 + 20

        pygame.draw.circle(rune_surf, (251, 191, 36, min(80, fade_alpha)), (r_cx, r_cy), ring_r1, 2)
        pygame.draw.circle(rune_surf, (254, 240, 138, min(100, fade_alpha)), (r_cx, r_cy), ring_r2, 1)

        for i in range(8):
            ang = i * (math.pi / 4.0) + t * 0.8
            p1_x = r_cx + math.cos(ang) * (ring_r1 - 10)
            p1_y = r_cy + math.sin(ang) * (ring_r1 - 10)
            p2_x = r_cx + math.cos(ang) * (ring_r2 + 10)
            p2_y = r_cy + math.sin(ang) * (ring_r2 + 10)
            pygame.draw.line(rune_surf, (251, 191, 36, min(140, fade_alpha)), (p1_x, p1_y), (p2_x, p2_y), 2)
            pygame.draw.circle(rune_surf, (255, 255, 255, min(200, fade_alpha)), (int(p2_x), int(p2_y)), 3)

        self.screen.blit(rune_surf, (cx - r_cx, cy - r_cy))

        emblem_r = 70
        emblem_glow = pygame.Surface((emblem_r * 4, emblem_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(emblem_glow, (251, 191, 36, min(60, fade_alpha)), (emblem_r * 2, emblem_r * 2), emblem_r * 2)
        self.screen.blit(emblem_glow, (cx - emblem_r * 2, cy - emblem_r * 2))

        pygame.draw.circle(self.screen, (30, 41, 59), (cx, cy), emblem_r)
        pygame.draw.circle(self.screen, (251, 191, 36), (cx, cy), emblem_r, 4)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), emblem_r - 4, 1)

        dir_sprites = self.player_sprites.get(self.player_dir, self.player_sprites["down"])
        hero_frame = dir_sprites[self.anim_frame]
        hero_big = pygame.transform.scale(hero_frame, (80, 80))
        self.screen.blit(hero_big, hero_big.get_rect(center=(cx, cy - 2)))

        badge_y = cy + emblem_r + 14
        badge_w, badge_h = 250, 32
        b_rect = pygame.Rect(cx - badge_w // 2, badge_y, badge_w, badge_h)
        pygame.draw.rect(self.screen, (15, 23, 42), b_rect, border_radius=10)
        pygame.draw.rect(self.screen, (251, 191, 36), b_rect, 2, border_radius=10)
        badge_txt = self.card_title_font.render("⭐ HERO IN TRAINING ⭐", True, (254, 240, 138))
        self.screen.blit(badge_txt, badge_txt.get_rect(center=b_rect.center))

        banner_drop_t = min(1.0, t_anim / 0.7)
        ease_y = 1 - pow(1 - banner_drop_t, 3)
        target_by = 38
        start_by = -140
        banner_y = int(start_by + (target_by - start_by) * ease_y)

        bw, bh = min(740, self.width - 40), 96
        bx = (self.width - bw) // 2
        banner_rect = pygame.Rect(bx, banner_y, bw, bh)

        sh_rect = banner_rect.copy()
        sh_rect.y += 4
        pygame.draw.rect(self.screen, (0, 0, 0, min(160, fade_alpha)), sh_rect, border_radius=18)

        b_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        b_surf.fill((15, 23, 42, min(245, fade_alpha)))
        self.screen.blit(b_surf, banner_rect.topleft)
        pygame.draw.rect(self.screen, (245, 158, 11), banner_rect, 3, border_radius=18)
        pygame.draw.rect(self.screen, (251, 191, 36), (bx + 3, banner_y + 3, bw - 6, bh - 6), 1, border_radius=15)

        tag_surf = self.ui_font.render("🌟 COGNITIVE QUEST ACADEMY 🌟", True, (251, 191, 36))
        self.screen.blit(tag_surf, tag_surf.get_rect(center=(self.width // 2, banner_y + 20)))

        title_surf = self.intro_title_font.render("TUTORIAL TRAINING GROUNDS", True, (255, 255, 255))
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, banner_y + 50)))

        sub_surf = self.ui_font.render("Welcome, young hero! Learn your magic gesture controls to begin your journey!", True, (203, 213, 225))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, banner_y + 76)))

        ribbon_y = cy + emblem_r + 60
        rw, rh = min(680, self.width - 40), 40
        rx = (self.width - rw) // 2
        r_rect = pygame.Rect(rx, ribbon_y, rw, rh)

        pygame.draw.rect(self.screen, (30, 41, 59), r_rect, border_radius=12)
        pygame.draw.rect(self.screen, (74, 222, 128), r_rect, 1, border_radius=12)

        flow_txt = self.card_title_font.render("🖐️ Open Hand Walk   ➔   ⭐ Catch Stars   ➔   ✊ Hold Fist to Click!", True, (255, 255, 255))
        self.screen.blit(flow_txt, flow_txt.get_rect(center=r_rect.center))

        skip_pulse = 0.5 + 0.5 * math.sin(t * 6.0)
        skip_col = (int(251 * (0.7 + 0.3 * skip_pulse)), int(191 * (0.7 + 0.3 * skip_pulse)), 36)
        skip_txt = self.card_title_font.render("▶  Hold Fist ✊ or Select to Begin Video Demo  ◀", True, skip_col)
        self.screen.blit(skip_txt, skip_txt.get_rect(center=(self.width // 2, self.height - 36)))

    # ============================================================
    # GESTURE-ONLY DEMONSTRATION VIDEO SHOWCASE
    # ============================================================
    def draw_demonstration_video(self):
        """
        Renders a rich, animated, interactive Demonstration Video presentation.
        Focuses 100% on webcam gesture controls with 4 animated chapters:
        1. 📷 Camera & Hand Setup
        2. 🖐️ Open Hand Walking & Directional Steering
        3. ✊ Closed Fist to Hold-to-Click & Select
        4. 🎯 Interactive Live Practice Arena
        """
        now = pygame.time.get_ticks()
        t = now * 0.001

        # 1. Dimmed Cinema Backdrop
        if self._dim_overlay is None or self._dim_overlay.get_size() != (self.width, self.height):
            self._dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dim_overlay.fill((10, 15, 30, 240))
        self.screen.blit(self._dim_overlay, (0, 0))

        # Floating ambient stars
        for p in getattr(self, 'intro_particles', []):
            px, py = p["x"], p["y"]
            p_size = p["size"] + math.sin(t * 3.0 + p["phase"])
            p_surf = pygame.Surface((int(p_size * 4), int(p_size * 4)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p["color"], 90), (int(p_size * 2), int(p_size * 2)), int(p_size))
            self.screen.blit(p_surf, (int(px - p_size * 2), int(py - p_size * 2)))

        # 2. Main Video Player Frame
        vw = min(1060, self.width - 40)
        vh = min(580, self.height - 40)
        vx = (self.width - vw) // 2
        vy = (self.height - vh) // 2

        # Video Player Drop Shadow
        sh_rect = pygame.Rect(vx, vy + 4, vw, vh)
        pygame.draw.rect(self.screen, (0, 0, 0, 200), sh_rect, border_radius=22)

        # Video Player Body
        v_body = pygame.Surface((vw, vh), pygame.SRCALPHA)
        v_body.fill((15, 23, 42, 252))
        self.screen.blit(v_body, (vx, vy))
        pygame.draw.rect(self.screen, (245, 158, 11), (vx, vy, vw, vh), 3, border_radius=22)
        pygame.draw.rect(self.screen, (251, 191, 36), (vx + 3, vy + 3, vw - 6, vh - 6), 1, border_radius=19)

        # 3. Video Header Bar
        hdr_h = 50
        pygame.draw.rect(self.screen, (30, 41, 59), (vx + 4, vy + 4, vw - 8, hdr_h), border_top_left_radius=19, border_top_right_radius=19)
        pygame.draw.line(self.screen, (51, 65, 85), (vx + 4, vy + 4 + hdr_h), (vx + vw - 4, vy + 4 + hdr_h), 2)

        # Pulsing Red Recording Dot & Live Demonstration Tag
        pulse_rec = 0.5 + 0.5 * math.sin(t * 5.0)
        rec_dot_x = vx + 24
        rec_dot_y = vy + 28
        pygame.draw.circle(self.screen, (239, 68, 68), (rec_dot_x, rec_dot_y), int(6 + 2 * pulse_rec))
        pygame.draw.circle(self.screen, (255, 255, 255), (rec_dot_x, rec_dot_y), 3)

        rec_txt = self.card_title_font.render("DEMONSTRATION VIDEO: HOW GESTURE CONTROLS WORK", True, (255, 255, 255))
        self.screen.blit(rec_txt, (rec_dot_x + 16, vy + 16))

        # Skip Video Button (Top Right)
        skip_btn = pygame.Rect(vx + vw - 160, vy + 12, 144, 34)
        skip_hov = skip_btn.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if skip_hov else (51, 65, 85), skip_btn, border_radius=8)
        pygame.draw.rect(self.screen, (251, 191, 36) if skip_hov else (148, 163, 184), skip_btn, 1, border_radius=8)
        sk_txt = self.ui_font.render("Skip Video ⏩", True, (255, 255, 255))
        self.screen.blit(sk_txt, sk_txt.get_rect(center=skip_btn.center))

        # 4. Chapter Timeline Navigation Tabs
        tab_y = vy + 60
        tab_w = (vw - 40 - 30) // 4
        tab_h = 38
        chapters = [
            ("📷 1. Camera Setup", (56, 189, 248)),
            ("🖐️ 2. Open Hand Walk", (74, 222, 128)),
            ("✊ 3. Fist to Click", (251, 191, 36)),
            ("🎯 4. Live Test", (244, 63, 94))
        ]

        for i, (label, accent_col) in enumerate(chapters):
            tx = vx + 20 + i * (tab_w + 10)
            t_rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            is_hov = t_rect.collidepoint(self.cursor_pos)
            is_active = (self.demo_video_chapter == i)
            if is_active:
                if i == 0:
                    bg_c = (30, 58, 138)
                elif i == 1:
                    bg_c = (20, 83, 45)
                elif i == 2:
                    bg_c = (120, 53, 15)
                else:
                    bg_c = (136, 19, 55)
            else:
                bg_c = (30, 41, 59)

            bdr_c = accent_col if is_active else ((100, 116, 139) if not is_hov else (255, 255, 255))

            pygame.draw.rect(self.screen, bg_c, t_rect, border_radius=10)
            pygame.draw.rect(self.screen, bdr_c, t_rect, 2 if is_active else 1, border_radius=10)

            t_col = (255, 255, 255) if is_active else ((203, 213, 225) if not is_hov else (255, 255, 255))
            tab_surf = self.ui_font.render(label, True, t_col)
            self.screen.blit(tab_surf, tab_surf.get_rect(center=t_rect.center))

        # 5. Main Chapter Animation Display & Instructions
        stage_x = vx + 20
        stage_y = tab_y + tab_h + 14
        stage_w = vw - 40
        stage_h = vh - 180

        # Subdivide stage: Left 52% = Animated Screen, Right 48% = Instructions Card
        screen_w = int(stage_w * 0.53)
        info_w = stage_w - screen_w - 18
        info_x = stage_x + screen_w + 18

        # Left Animated Video Screen
        screen_rect = pygame.Rect(stage_x, stage_y, screen_w, stage_h)
        pygame.draw.rect(self.screen, (10, 15, 26), screen_rect, border_radius=14)
        pygame.draw.rect(self.screen, (51, 65, 85), screen_rect, 2, border_radius=14)

        # Right Instruction Card
        info_rect = pygame.Rect(info_x, stage_y, info_w, stage_h)
        pygame.draw.rect(self.screen, (20, 29, 47), info_rect, border_radius=14)
        pygame.draw.rect(self.screen, (71, 85, 105), info_rect, 2, border_radius=14)

        # RENDER CHAPTER CONTENT
        if self.demo_video_chapter == 0:
            self.draw_demo_chapter_camera(screen_rect, info_rect, t)
        elif self.demo_video_chapter == 1:
            self.draw_demo_chapter_walking(screen_rect, info_rect, t)
        elif self.demo_video_chapter == 2:
            self.draw_demo_chapter_fist(screen_rect, info_rect, t)
        else:
            self.draw_demo_chapter_practice(screen_rect, info_rect, t)

        # 6. Bottom Video Player Control Bar
        bar_y = vy + vh - 58
        prev_btn = pygame.Rect(vx + 24, bar_y, 110, 40)
        play_btn = pygame.Rect(vx + 144, bar_y, 110, 40)
        next_btn = pygame.Rect(vx + 264, bar_y, 110, 40)

        # Draw Prev Button
        p_hov = prev_btn.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if not p_hov else (71, 85, 105), prev_btn, border_radius=10)
        pygame.draw.rect(self.screen, (148, 163, 184), prev_btn, 1, border_radius=10)
        p_txt = self.ui_font.render("◀ Prev Scene", True, (255, 255, 255))
        self.screen.blit(p_txt, p_txt.get_rect(center=prev_btn.center))

        # Draw Play/Pause Button
        pl_hov = play_btn.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if not pl_hov else (71, 85, 105), play_btn, border_radius=10)
        pygame.draw.rect(self.screen, (148, 163, 184), play_btn, 1, border_radius=10)
        pl_txt = self.ui_font.render("⏸ Pause" if self.demo_video_playing else "▶ Play", True, (251, 191, 36) if not self.demo_video_playing else (255, 255, 255))
        self.screen.blit(pl_txt, pl_txt.get_rect(center=play_btn.center))

        # Draw Next Button
        n_hov = next_btn.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (51, 65, 85) if not n_hov else (71, 85, 105), next_btn, border_radius=10)
        pygame.draw.rect(self.screen, (148, 163, 184), next_btn, 1, border_radius=10)
        n_txt = self.ui_font.render("Next Scene ▶", True, (255, 255, 255))
        self.screen.blit(n_txt, n_txt.get_rect(center=next_btn.center))

        # Progress Timeline Scrubber
        scrub_x = vx + 390
        scrub_w = vw - 390 - 290
        scrub_h = 10
        scrub_y = bar_y + 15
        s_rect = pygame.Rect(scrub_x, scrub_y, scrub_w, scrub_h)
        pygame.draw.rect(self.screen, (30, 41, 59), s_rect, border_radius=5)
        
        chap_prog = min(1.0, self.demo_video_timer / max(0.1, self.demo_video_chapter_duration))
        total_prog = (self.demo_video_chapter + chap_prog) / 4.0
        fill_scrub = int(scrub_w * total_prog)
        if fill_scrub > 0:
            pygame.draw.rect(self.screen, (245, 158, 11), (scrub_x, scrub_y, fill_scrub, scrub_h), border_radius=5)
        pygame.draw.rect(self.screen, (71, 85, 105), s_rect, 1, border_radius=5)

        # Start Tutorial Adventure CTA Button (Right)
        start_btn = pygame.Rect(vx + vw - 270, bar_y, 246, 40)
        st_hov = start_btn.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (245, 158, 11) if st_hov else (180, 83, 9), start_btn, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255) if st_hov else (251, 191, 36), start_btn, 2, border_radius=10)

        # Fist Hold Progress on Start Button
        fist_fill_pct = 0.0
        if self.fist_start_time > 0 and self.current_gesture == "FIST":
            fist_fill_pct = min(1.0, (time.time() - self.fist_start_time) / self.CLICK_HOLD_TIME)
            if fist_fill_pct > 0:
                fill_w = int(246 * fist_fill_pct)
                f_surf = pygame.Surface((fill_w, 40), pygame.SRCALPHA)
                f_surf.fill((255, 255, 255, 90))
                self.screen.blit(f_surf, (vx + vw - 270, bar_y))

        st_label = "🚀 Begin Adventure!" if fist_fill_pct == 0 else f"Starting: {int(fist_fill_pct * 100)}%"
        st_txt = self.card_title_font.render(st_label, True, (255, 255, 255))
        self.screen.blit(st_txt, st_txt.get_rect(center=start_btn.center))

    # ============================================================
    # DEMO CHAPTER 0: CAMERA SETUP
    # ============================================================
    def draw_demo_chapter_camera(self, screen_rect, info_rect, t):
        cx, cy = screen_rect.centerx, screen_rect.centery

        # Laptop & Webcam Diagram
        laptop_w, laptop_h = 240, 150
        laptop_x = cx - laptop_w // 2
        laptop_y = cy - laptop_h // 2 - 20

        # Laptop Screen
        pygame.draw.rect(self.screen, (30, 41, 59), (laptop_x, laptop_y, laptop_w, laptop_h), border_radius=12)
        pygame.draw.rect(self.screen, (56, 189, 248), (laptop_x, laptop_y, laptop_w, laptop_h), 2, border_radius=12)

        # Mini Screen Inner Display
        inner_w, inner_h = laptop_w - 24, laptop_h - 30
        inner_rect = pygame.Rect(laptop_x + 12, laptop_y + 16, inner_w, inner_h)
        pygame.draw.rect(self.screen, (15, 23, 42), inner_rect, border_radius=6)

        # Webcam Lens on top
        cam_lens_x = cx
        cam_lens_y = laptop_y + 8
        pygame.draw.circle(self.screen, (56, 189, 248), (cam_lens_x, cam_lens_y), 4)
        pygame.draw.circle(self.screen, (34, 197, 94), (cam_lens_x, cam_lens_y), 2)

        # Green Light Beam Cone radiating from webcam
        cone_pts = [
            (cam_lens_x, cam_lens_y),
            (laptop_x - 30, laptop_y + laptop_h + 80),
            (laptop_x + laptop_w + 30, laptop_y + laptop_h + 80)
        ]
        cone_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surf, (34, 197, 94, 35), cone_pts)
        self.screen.blit(cone_surf, (0, 0))

        # Animated Hand Silhouette rising in the beam
        hand_bob = math.sin(t * 4.0) * 8
        hand_x = cx
        hand_y = cy + 50 + hand_bob

        hand_surf = self.huge_font.render("🖐️", True, (74, 222, 128))
        self.screen.blit(hand_surf, hand_surf.get_rect(center=(hand_x, hand_y)))

        # Animated Green Tracking Brackets around Hand
        b_size = 40
        b_x, b_y = hand_x - b_size // 2, hand_y - b_size // 2
        pygame.draw.rect(self.screen, (34, 197, 94), (b_x, b_y, b_size, b_size), 2, border_radius=6)
        
        lock_txt = self.ui_font.render("✓ HAND DETECTED", True, (34, 197, 94))
        self.screen.blit(lock_txt, lock_txt.get_rect(center=(hand_x, hand_y + 36)))

        # Instructions on Right Card
        ix, iy = info_rect.x + 20, info_rect.y + 20
        h_txt = self.dialog_header_font.render("📷 Step 1: Camera Setup", True, (56, 189, 248))
        self.screen.blit(h_txt, (ix, iy))

        sub1 = self.card_title_font.render("Sit in front of your webcam", True, (255, 255, 255))
        self.screen.blit(sub1, (ix, iy + 40))

        lines = [
            "1. Position yourself comfortably in front of camera.",
            "2. Raise your hand with palm facing webcam.",
            "3. Keep your hand visible and well-lit.",
            "4. A green tracking reticle will lock onto your hand!"
        ]
        for idx, line in enumerate(lines):
            l_surf = self.ui_font.render(line, True, (203, 213, 225))
            self.screen.blit(l_surf, (ix, iy + 80 + idx * 28))

        # Live Webcam Feed if available in main menu
        if getattr(self.main_menu, 'camera_frame', None) is not None:
            try:
                camera_frame_rgb = cv2.cvtColor(self.main_menu.camera_frame, cv2.COLOR_BGR2RGB)
                camera_surface = pygame.surfarray.make_surface(np.swapaxes(camera_frame_rgb, 0, 1))
                camera_surface = pygame.transform.scale(camera_surface, (140, 105))
                c_preview_x = info_rect.x + 20
                c_preview_y = info_rect.bottom - 125
                pygame.draw.rect(self.screen, (34, 197, 94), (c_preview_x - 2, c_preview_y - 2, 144, 109), 2, border_radius=8)
                self.screen.blit(camera_surface, (c_preview_x, c_preview_y))

                prev_lbl = self.ui_font.render("🔴 Live Camera Feed", True, (74, 222, 128))
                self.screen.blit(prev_lbl, (c_preview_x + 155, c_preview_y + 20))
                det_status = "Status: 🖐️ Hand Ready!" if self.hand_detected else "Status: Show hand to camera"
                det_lbl = self.ui_font.render(det_status, True, (251, 191, 36) if self.hand_detected else (148, 163, 184))
                self.screen.blit(det_lbl, (c_preview_x + 155, c_preview_y + 48))
            except Exception:
                pass

    # ============================================================
    # DEMO CHAPTER 1: OPEN HAND WALKING
    # ============================================================
    def draw_demo_chapter_walking(self, screen_rect, info_rect, t):
        cx, cy = screen_rect.centerx, screen_rect.centery

        # Arena field backdrop
        field_r = 110
        pygame.draw.circle(self.screen, (20, 83, 45), (cx, cy), field_r)
        pygame.draw.circle(self.screen, (74, 222, 128), (cx, cy), field_r, 2)
        pygame.draw.circle(self.screen, (34, 197, 94, 60), (cx, cy), 35, 1)

        # 4 Direction Arrows
        arrow_dist = 85
        arrows = [
            ("⬆️", (cx, cy - arrow_dist), "UP"),
            ("⬇️", (cx, cy + arrow_dist), "DOWN"),
            ("⬅️", (cx - arrow_dist, cy), "LEFT"),
            ("➡️", (cx + arrow_dist, cy), "RIGHT")
        ]
        for a_char, (ax, ay), a_label in arrows:
            pygame.draw.circle(self.screen, (15, 23, 42), (ax, ay), 18)
            pygame.draw.circle(self.screen, (74, 222, 128), (ax, ay), 18, 1)
            a_surf = self.ui_font.render(a_char, True, (255, 255, 255))
            self.screen.blit(a_surf, a_surf.get_rect(center=(ax, ay)))

        # Animated Hand & Hero simulation (Cycle: Right -> Up -> Left -> Down)
        cycle_t = (t * 0.8) % 4.0
        if cycle_t < 1.0:
            h_dx, h_dy = math.sin(cycle_t * math.pi) * 60, 0
            cur_dir = "right"
        elif cycle_t < 2.0:
            sub_t = cycle_t - 1.0
            h_dx, h_dy = 0, -math.sin(sub_t * math.pi) * 60
            cur_dir = "up"
        elif cycle_t < 3.0:
            sub_t = cycle_t - 2.0
            h_dx, h_dy = -math.sin(sub_t * math.pi) * 60, 0
            cur_dir = "left"
        else:
            sub_t = cycle_t - 3.0
            h_dx, h_dy = 0, math.sin(sub_t * math.pi) * 60
            cur_dir = "down"

        # Footprint starlight particles
        for s_i in range(4):
            fp_x = cx + (h_dx * s_i / 4.0)
            fp_y = cy + (h_dy * s_i / 4.0)
            pygame.draw.circle(self.screen, (251, 191, 36), (int(fp_x), int(fp_y)), 3)

        # Draw Hero Sprite walking
        dir_sprites = self.player_sprites.get(cur_dir, self.player_sprites["down"])
        anim_f = int(t * 8) % len(dir_sprites)
        h_sprite = pygame.transform.scale(dir_sprites[anim_f], (48, 48))
        self.screen.blit(h_sprite, h_sprite.get_rect(center=(cx + h_dx, cy + h_dy)))

        # Draw Floating Open Hand Cursor leading the hero
        lead_x = cx + h_dx * 1.35
        lead_y = cy + h_dy * 1.35
        hand_icon = self.huge_font.render("🖐️", True, (74, 222, 128))
        self.screen.blit(hand_icon, hand_icon.get_rect(center=(lead_x, lead_y)))

        # Connecting guidance laser
        pygame.draw.line(self.screen, (74, 222, 128), (cx + h_dx, cy + h_dy), (lead_x, lead_y), 2)

        # Instructions on Right Card
        ix, iy = info_rect.x + 20, info_rect.y + 20
        h_txt = self.dialog_header_font.render("🖐️ Step 2: Open Hand Walking", True, (74, 222, 128))
        self.screen.blit(h_txt, (ix, iy))

        sub1 = self.card_title_font.render("Spread fingers to steer hero", True, (255, 255, 255))
        self.screen.blit(sub1, (ix, iy + 40))

        lines = [
            "1. Keep your fingers open (🖐️ OPEN HAND).",
            "2. Move your hand in the direction you want to walk.",
            "3. Move hand UP ⬆️, DOWN ⬇️, LEFT ⬅️, or RIGHT ➡️.",
            "4. Your hero runs where your hand leads!",
            "⭐ Steer over glowing stars to collect them!"
        ]
        for idx, line in enumerate(lines):
            l_surf = self.ui_font.render(line, True, (203, 213, 225))
            self.screen.blit(l_surf, (ix, iy + 80 + idx * 28))

    # ============================================================
    # DEMO CHAPTER 2: FIST HOLD TO CLICK
    # ============================================================
    def draw_demo_chapter_fist(self, screen_rect, info_rect, t):
        cx, cy = screen_rect.centerx, screen_rect.centery

        # Mock Math Question Button Demonstration
        btn_w, btn_h = 320, 54
        btn_x = cx - btn_w // 2
        btn_y = cy - btn_h // 2 - 20
        b_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        # 2.4s Demonstration cycle
        cycle = (t * 0.9) % 2.4
        hold_prog = min(1.0, cycle / 1.6)
        is_selected = (cycle > 1.6)

        btn_bg = (20, 83, 45) if is_selected else (30, 41, 59)
        btn_bdr = (34, 197, 94) if is_selected else (251, 191, 36)
        pygame.draw.rect(self.screen, btn_bg, b_rect, border_radius=12)
        pygame.draw.rect(self.screen, btn_bdr, b_rect, 2, border_radius=12)

        # Option B (4) Label
        b_txt_str = "Option B: 4  [ 2 + 2 = 4 ] ✓" if is_selected else "Option B: 4  [ 2 + 2 = 4 ]"
        b_txt = self.card_title_font.render(b_txt_str, True, (255, 255, 255))
        self.screen.blit(b_txt, (btn_x + 20, btn_y + 16))

        # Animated Hand over Button: Transitions from 🖐️ to ✊
        hand_target_x = btn_x + btn_w - 40
        hand_target_y = btn_y + btn_h // 2

        if is_selected:
            h_icon = "✊"
            ring_col = (34, 197, 94)
        elif hold_prog > 0.1:
            h_icon = "✊"
            ring_col = (251, 191, 36)
        else:
            h_icon = "🖐️"
            ring_col = (148, 163, 184)

        # Golden circular progress arc
        ring_r = 22
        pygame.draw.circle(self.screen, (30, 41, 59), (hand_target_x, hand_target_y), ring_r)
        pygame.draw.circle(self.screen, ring_col, (hand_target_x, hand_target_y), ring_r, 2)

        if hold_prog > 0:
            arc_steps = max(3, int(hold_prog * 36))
            start_ang = -math.pi / 2
            sweep = 2 * math.pi * hold_prog
            pts = [(hand_target_x, hand_target_y)]
            for s in range(arc_steps + 1):
                ang = start_ang + sweep * s / arc_steps
                pts.append((hand_target_x + math.cos(ang) * (ring_r - 2), hand_target_y + math.sin(ang) * (ring_r - 2)))
            if len(pts) > 2:
                pygame.draw.polygon(self.screen, ring_col, pts)

        h_surf = self.dialog_header_font.render(h_icon, True, (255, 255, 255))
        self.screen.blit(h_surf, h_surf.get_rect(center=(hand_target_x, hand_target_y)))

        # Status text below button
        pct_num = 100 if is_selected else int(hold_prog * 100)
        status_str = f"✊ HOLD FIST: {pct_num}%  ➔  [ CLICK TRIGGERED! 🎉 ]" if is_selected else f"✊ HOLD FIST: {pct_num}% (Keep holding...)"
        st_surf = self.card_title_font.render(status_str, True, (74, 222, 128) if is_selected else (251, 191, 36))
        self.screen.blit(st_surf, st_surf.get_rect(center=(cx, btn_y + btn_h + 36)))

        # Instructions on Right Card
        ix, iy = info_rect.x + 20, info_rect.y + 20
        h_txt = self.dialog_header_font.render("✊ Step 3: Hold Fist to Click", True, (251, 191, 36))
        self.screen.blit(h_txt, (ix, iy))

        sub1 = self.card_title_font.render("Close hand into a ball to select", True, (255, 255, 255))
        self.screen.blit(sub1, (ix, iy + 40))

        lines = [
            "1. Move cursor over any button or answer choice.",
            "2. Close your hand into a tight FIST (✊).",
            "3. Hold steady for 0.9 seconds.",
            "4. The Golden Progress Ring fills up 100%!",
            "5. Button clicks with joyful sound and sparkles! ✨"
        ]
        for idx, line in enumerate(lines):
            l_surf = self.ui_font.render(line, True, (203, 213, 225))
            self.screen.blit(l_surf, (ix, iy + 80 + idx * 28))

    # ============================================================
    # DEMO CHAPTER 3: INTERACTIVE LIVE PRACTICE ARENA
    # ============================================================
    def draw_demo_chapter_practice(self, screen_rect, info_rect, t):
        cx, cy = screen_rect.centerx, screen_rect.centery

        # Interactive Practice Test Button
        practice_btn = pygame.Rect(cx - 160, cy - 40, 320, 64)
        is_hov = practice_btn.collidepoint(self.cursor_pos)

        # Fist Hold Progress
        fist_hold = 0.0
        if self.fist_start_time > 0 and self.current_gesture == "FIST":
            fist_hold = min(1.0, (time.time() - self.fist_start_time) / self.CLICK_HOLD_TIME)

        btn_bg = (20, 83, 45) if self.demo_practice_clicked else ((245, 158, 11) if is_hov else (30, 41, 59))
        pygame.draw.rect(self.screen, btn_bg, practice_btn, border_radius=14)
        pygame.draw.rect(self.screen, (251, 191, 36), practice_btn, 2, border_radius=14)

        if fist_hold > 0:
            fill_w = int(320 * fist_hold)
            f_surf = pygame.Surface((fill_w, 64), pygame.SRCALPHA)
            f_surf.fill((255, 255, 255, 90))
            self.screen.blit(f_surf, practice_btn.topleft)

        btn_title = "🎉 SUCCESS! GESTURE MASTERED!" if self.demo_practice_clicked else ("✊ HOLD FIST HERE TO TEST!" if fist_hold == 0 else f"✊ CHARGING: {int(fist_hold * 100)}%")
        p_txt = self.card_title_font.render(btn_title, True, (255, 255, 255))
        self.screen.blit(p_txt, p_txt.get_rect(center=practice_btn.center))

        # Real-time hand indicator in Practice Box
        hud_bg = pygame.Rect(cx - 160, cy + 44, 320, 36)
        pygame.draw.rect(self.screen, (15, 23, 42), hud_bg, border_radius=8)
        pygame.draw.rect(self.screen, (51, 65, 85), hud_bg, 1, border_radius=8)

        if self.hand_detected:
            g_txt = f"Webcam Hand Detected: {self.current_gesture} ✓"
            g_col = (74, 222, 128)
        else:
            g_txt = "📷 Waiting for hand in front of camera..."
            g_col = (251, 191, 36)
        h_status = self.ui_font.render(g_txt, True, g_col)
        self.screen.blit(h_status, h_status.get_rect(center=hud_bg.center))

        if hasattr(self, 'demo_practice_particles'):
            self.demo_practice_particles.draw(self.screen)

        # Instructions on Right Card
        ix, iy = info_rect.x + 20, info_rect.y + 20
        h_txt = self.dialog_header_font.render("🎯 Step 4: Try It Live!", True, (244, 63, 94))
        self.screen.blit(h_txt, (ix, iy))

        sub1 = self.card_title_font.render("Practice your gestures now!", True, (255, 255, 255))
        self.screen.blit(sub1, (ix, iy + 40))

        lines = [
            "1. Move your hand to guide the cursor onto the test button.",
            "2. Make a tight closed fist (✊).",
            "3. Watch the progress ring charge up and click!",
            "4. When ready, click 'Begin Adventure' below to play!"
        ]
        for idx, line in enumerate(lines):
            l_surf = self.ui_font.render(line, True, (203, 213, 225))
            self.screen.blit(l_surf, (ix, iy + 80 + idx * 28))

    # ============================================================
    # REAL-TIME HAND TRACKER HELPER HUD (100% GESTURE FOCUSED)
    # ============================================================
    def draw_hand_tracker_helper(self):
        """
        Renders a cheerful, real-time live gesture status card.
        Shows 2nd grade students exactly what hand gesture is being detected by webcam:
        - 🖐️ OPEN HAND = Walking (with steering direction)
        - ✊ CLOSED FIST = Selecting (with live 360-degree loading ring and % counter)
        - 📷 NO HAND = Friendly prompt to raise open hand in front of webcam
        """
        w, h = 280, 68
        x = self.width - w - 20
        y = 62

        sh_rect = pygame.Rect(x, y + 2, w, h)
        pygame.draw.rect(self.screen, (0, 0, 0, 160), sh_rect, border_radius=14)

        card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        card_surf.fill((15, 23, 42, 235))
        self.screen.blit(card_surf, (x, y))

        if self.hand_detected:
            if self.current_gesture == "FIST":
                border_col = (251, 191, 36)
                pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=14)

                icon_rect = pygame.Rect(x + 10, y + 10, 48, 48)
                pygame.draw.rect(self.screen, (30, 41, 59), icon_rect, border_radius=10)
                pygame.draw.rect(self.screen, (251, 191, 36), icon_rect, 1, border_radius=10)
                f_txt = self.card_title_font.render("✊", True, (251, 191, 36))
                self.screen.blit(f_txt, f_txt.get_rect(center=icon_rect.center))

                t1 = self.banner_font.render("FIST DETECTED!", True, (251, 191, 36))
                self.screen.blit(t1, (x + 66, y + 10))

                fist_hold = 0.0
                if self.fist_start_time > 0:
                    fist_hold = min(1.0, (time.time() - self.fist_start_time) / max(0.01, self.CLICK_HOLD_TIME))

                pct = int(fist_hold * 100)
                sub_str = f"Holding to Click: {pct}%" if fist_hold > 0 else "Hold steady to Select!"
                t2 = self.ui_font.render(sub_str, True, (254, 240, 138))
                self.screen.blit(t2, (x + 66, y + 32))

                bar_rect = pygame.Rect(x + 66, y + 48, 200, 10)
                pygame.draw.rect(self.screen, (30, 41, 59), bar_rect, border_radius=5)
                if fist_hold > 0:
                    fill_w = int(200 * fist_hold)
                    pygame.draw.rect(self.screen, (251, 191, 36), (x + 66, y + 48, fill_w, 10), border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), bar_rect, 1, border_radius=5)

            else:
                border_col = (34, 197, 94)
                pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=14)

                icon_rect = pygame.Rect(x + 10, y + 10, 48, 48)
                pygame.draw.rect(self.screen, (30, 41, 59), icon_rect, border_radius=10)
                pygame.draw.rect(self.screen, (34, 197, 94), icon_rect, 1, border_radius=10)
                f_txt = self.card_title_font.render("🖐️", True, (74, 222, 128))
                self.screen.blit(f_txt, f_txt.get_rect(center=icon_rect.center))

                t1 = self.banner_font.render("OPEN HAND (WALK)", True, (74, 222, 128))
                self.screen.blit(t1, (x + 66, y + 10))

                t2 = self.ui_font.render(f"Steering: {self.player_dir.upper()} ➔", True, (203, 213, 225))
                self.screen.blit(t2, (x + 66, y + 32))

                t3 = self.ui_font.render("Move hand away to walk!", True, (148, 163, 184))
                self.screen.blit(t3, (x + 66, y + 48))

        else:
            border_col = (251, 191, 36)
            pygame.draw.rect(self.screen, border_col, (x, y, w, h), 2, border_radius=14)

            icon_rect = pygame.Rect(x + 10, y + 10, 48, 48)
            pygame.draw.rect(self.screen, (30, 41, 59), icon_rect, border_radius=10)
            pygame.draw.rect(self.screen, (251, 191, 36), icon_rect, 1, border_radius=10)
            f_txt = self.card_title_font.render("🖐️", True, (251, 191, 36))
            self.screen.blit(f_txt, f_txt.get_rect(center=icon_rect.center))

            t1 = self.banner_font.render("SHOW HAND TO CAMERA", True, (251, 191, 36))
            self.screen.blit(t1, (x + 66, y + 10))

            t2 = self.ui_font.render("Raise hand in webcam view", True, (203, 213, 225))
            self.screen.blit(t2, (x + 66, y + 32))

            t3 = self.ui_font.render("🖐️ Open = Walk  |  ✊ Fist = Click", True, (148, 163, 184))
            self.screen.blit(t3, (x + 66, y + 48))

    # ============================================================
    # BOUNCING TARGET MARKER HELPER
    # ============================================================
    def draw_bouncing_marker(self, cx, cy, label, color, glow_color=(254, 240, 138)):
        t = pygame.time.get_ticks() * 0.001
        bob = math.sin(t * 6.0) * 8 * ZOOM
        arrow_y = cy - 36 * ZOOM + bob

        pulse_r = int((16 + math.sin(t * 5.0) * 4) * ZOOM)
        ring_surf = pygame.Surface((pulse_r * 4, pulse_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*color, 75), (pulse_r * 2, pulse_r * 2), pulse_r * 2)
        pygame.draw.circle(ring_surf, (*glow_color, 180), (pulse_r * 2, pulse_r * 2), pulse_r, int(2 * ZOOM))
        self.screen.blit(ring_surf, (int(cx - pulse_r * 2), int(cy - pulse_r * 2)))

        aw = int(14 * ZOOM)
        ah = int(18 * ZOOM)
        arrow_pts = [
            (cx - aw // 2, arrow_y - ah),
            (cx + aw // 2, arrow_y - ah),
            (cx + aw // 2, arrow_y - ah // 3),
            (cx + aw, arrow_y - ah // 3),
            (cx, arrow_y),
            (cx - aw, arrow_y - ah // 3),
            (cx - aw // 2, arrow_y - ah // 3)
        ]
        shadow_pts = [(px + 2, py + 2) for px, py in arrow_pts]
        pygame.draw.polygon(self.screen, (0, 0, 0, 150), shadow_pts)
        pygame.draw.polygon(self.screen, color, arrow_pts)
        pygame.draw.polygon(self.screen, (255, 255, 255), arrow_pts, max(1, int(2 * ZOOM)))

        if label:
            tag_surf = self.ui_font.render(label, True, (255, 255, 255))
            tw, th = tag_surf.get_width() + 16, tag_surf.get_height() + 6
            tag_rect = pygame.Rect(cx - tw // 2, arrow_y - ah - th - 4, tw, th)

            tag_bg = pygame.Surface((tw, th), pygame.SRCALPHA)
            tag_bg.fill((15, 23, 42, 235))
            self.screen.blit(tag_bg, tag_rect)
            pygame.draw.rect(self.screen, color, tag_rect, 2, border_radius=8)
            self.screen.blit(tag_surf, tag_surf.get_rect(center=tag_rect.center))

    # ============================================================
    # DYNAMIC COMPASS & TARGET MARKERS
    # ============================================================
    def draw_compass_and_badges(self):
        t = pygame.time.get_ticks() * 0.001
        
        if self.phase in [1, 2] and self.quiz_state == 0:
            uncollected_stars = [s for s in self.practice_stars if not s["collected"]]
            if uncollected_stars:
                target_star = uncollected_stars[0]
                st_sx = (target_star["tile_x"] * TILE_SIZE - self.camera_x + TILE_SIZE / 2) * ZOOM
                st_sy = (target_star["tile_y"] * TILE_SIZE - self.camera_y + TILE_SIZE / 2) * ZOOM
                self.draw_bouncing_marker(st_sx, st_sy, "⭐ Catch Me!", (251, 191, 36), (254, 240, 138))
            else:
                screen_npc_x = (self.npc_tile_x * TILE_SIZE - self.camera_x + TILE_SIZE / 2) * ZOOM
                screen_npc_y = (self.npc_tile_y * TILE_SIZE - self.camera_y + TILE_SIZE / 2) * ZOOM
                player_npc_dist = math.hypot(self.player_x - self.npc_tile_x * TILE_SIZE, self.player_y - self.npc_tile_y * TILE_SIZE)
                label = "✊ Hold Fist to Speak!" if player_npc_dist < 3.5 * TILE_SIZE else "🧙 Sage: Walk to Me!"
                self.draw_bouncing_marker(screen_npc_x, screen_npc_y, label, (245, 158, 11), (254, 240, 138))

            st_x, st_y = self.npc_tile_x, self.npc_tile_y
            screen_npc_x = (st_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (st_y * TILE_SIZE - self.camera_y) * ZOOM
            is_on_screen = (40 <= screen_npc_x <= self.width - 60 and 40 <= screen_npc_y <= self.height - 110)
            if not is_on_screen:
                player_screen_x = (self.player_x - self.camera_x) * ZOOM
                player_screen_y = (self.player_y - self.camera_y) * ZOOM
                dx = screen_npc_x - player_screen_x
                dy = screen_npc_y - player_screen_y
                dist_m = int(math.hypot(self.player_x - st_x * TILE_SIZE, self.player_y - st_y * TILE_SIZE) // TILE_SIZE)
                angle = math.atan2(dy, dx)
                clamp_x = max(80, min(self.width - 80, player_screen_x + math.cos(angle) * 180))
                clamp_y = max(60, min(self.height - 100, player_screen_y + math.sin(angle) * 180))

                ptr_text = f"▶  Guide Sage ({dist_m}m)"
                ptr_surf = self.ui_font.render(ptr_text, True, (15, 23, 42))
                pw, ph = ptr_surf.get_width() + 20, 30
                p_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)
                pygame.draw.rect(self.screen, (255, 215, 0), p_rect, border_radius=10)
                pygame.draw.rect(self.screen, (255, 255, 255), p_rect, 2, border_radius=10)
                self.screen.blit(ptr_surf, ptr_surf.get_rect(center=p_rect.center))

        elif self.phase == 4 and self.quiz_state == 0:
            p_cx = (self.portal_tile_x * TILE_SIZE + (TILE_SIZE * 3) / 2)
            p_cy = (self.portal_tile_y * TILE_SIZE + (TILE_SIZE * 3) / 2)
            screen_p_x = (p_cx - self.camera_x) * ZOOM
            screen_p_y = (p_cy - self.camera_y) * ZOOM

            self.draw_bouncing_marker(screen_p_x, screen_p_y - 10, "🌀 Magic Portal (Jump In!)", (34, 197, 94), (187, 247, 208))

            npc_sx = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM
            npc_sy = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM
            cheer_surf = self.ui_font.render("🎉 Step into the glowing Portal!", True, (255, 255, 255))
            cw, ch = cheer_surf.get_width() + 16, cheer_surf.get_height() + 8
            c_rect = pygame.Rect(npc_sx + (TILE_SIZE * ZOOM) / 2 - cw / 2, npc_sy - ch - 12, cw, ch)
            pygame.draw.rect(self.screen, (15, 23, 42), c_rect, border_radius=8)
            pygame.draw.rect(self.screen, (74, 222, 128), c_rect, 2, border_radius=8)
            self.screen.blit(cheer_surf, cheer_surf.get_rect(center=c_rect.center))

            is_on_screen = (40 <= screen_p_x <= self.width - 60 and 40 <= screen_p_y <= self.height - 110)
            if not is_on_screen:
                player_screen_x = (self.player_x - self.camera_x) * ZOOM
                player_screen_y = (self.player_y - self.camera_y) * ZOOM
                dx = screen_p_x - player_screen_x
                dy = screen_p_y - player_screen_y
                dist_m = int(math.hypot(self.player_x - self.portal_tile_x * TILE_SIZE, self.player_y - self.portal_tile_y * TILE_SIZE) // TILE_SIZE)
                angle = math.atan2(dy, dx)
                clamp_x = max(80, min(self.width - 80, player_screen_x + math.cos(angle) * 180))
                clamp_y = max(60, min(self.height - 100, player_screen_y + math.sin(angle) * 180))

                ptr_text = f"▶  Exit Portal ({dist_m}m)"
                ptr_surf = self.ui_font.render(ptr_text, True, (15, 23, 42))
                pw, ph = ptr_surf.get_width() + 20, 30
                p_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)
                pygame.draw.rect(self.screen, (74, 222, 128), p_rect, border_radius=10)
                pygame.draw.rect(self.screen, (255, 255, 255), p_rect, 2, border_radius=10)
                self.screen.blit(ptr_surf, ptr_surf.get_rect(center=p_rect.center))

    # ============================================================
    # DEMONSTRATION OVERLAY & GESTURE RADAR
    # ============================================================
    def draw_demonstration_overlay(self):
        now = pygame.time.get_ticks()
        t = now * 0.001

        # Radiant Starlight Trail
        if self.phase in [1, 4]:
            pl_sx = (self.player_x - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
            pl_sy = (self.player_y - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2

            if self.phase == 1:
                target_sx = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
                target_sy = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2
                trail_color = (245, 158, 11)
                glow_color = (254, 240, 138)
            else:
                target_sx = (self.portal_tile_x * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
                target_sy = (self.portal_tile_y * TILE_SIZE - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2
                trail_color = (34, 197, 94)
                glow_color = (187, 247, 208)

            if target_sx > pl_sx + 20:
                pygame.draw.line(self.screen, trail_color, (pl_sx, pl_sy), (target_sx, target_sy), int(6 * ZOOM))
                pygame.draw.line(self.screen, (255, 255, 255), (pl_sx, pl_sy), (target_sx, target_sy), int(2 * ZOOM))

                step = 36 * ZOOM
                offset = (now * 0.045) % step
                cur_x = pl_sx + offset
                while cur_x < target_sx - 20:
                    pulse_r = int((8 + math.sin(t * 5.0 + cur_x * 0.1) * 2.5) * ZOOM)
                    halo_surf = pygame.Surface((pulse_r * 4, pulse_r * 4), pygame.SRCALPHA)
                    pygame.draw.circle(halo_surf, (*trail_color, 80), (pulse_r * 2, pulse_r * 2), pulse_r * 2)
                    self.screen.blit(halo_surf, (int(cur_x - pulse_r * 2), int(pl_sy - pulse_r * 2)))

                    d_size = int(8 * ZOOM)
                    diamond = [
                        (cur_x, pl_sy - d_size),
                        (cur_x + d_size, pl_sy),
                        (cur_x, pl_sy + d_size),
                        (cur_x - d_size, pl_sy)
                    ]
                    pygame.draw.polygon(self.screen, glow_color, diamond)
                    pygame.draw.polygon(self.screen, (255, 255, 255), diamond, 2)

                    c_x = cur_x + 10 * ZOOM
                    p1 = (c_x - 5 * ZOOM, pl_sy - 7 * ZOOM)
                    p2 = (c_x + 5 * ZOOM, pl_sy)
                    p3 = (c_x - 5 * ZOOM, pl_sy + 7 * ZOOM)
                    pygame.draw.lines(self.screen, (15, 23, 42), False, [p1, p2, p3], 5)
                    pygame.draw.lines(self.screen, (255, 255, 255), False, [p1, p2, p3], 3)
                    cur_x += step

        # Bottom-Left Gesture Quest Checklist Card
        if self.phase in [1, 4] and self.quiz_state == 0:
            card_w, card_h = 360, 134
            card_x = 24
            card_y = self.height - card_h - 20

            sh_rect = pygame.Rect(card_x, card_y + 3, card_w, card_h)
            pygame.draw.rect(self.screen, (0, 0, 0, 160), sh_rect, border_radius=16)

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill((15, 23, 42, 240))
            self.screen.blit(card_surf, (card_x, card_y))
            border_col = (245, 158, 11) if self.phase == 1 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_col, (card_x, card_y, card_w, card_h), 2, border_radius=16)

            t_radar = self.card_title_font.render("🎯 GESTURE CONTROLS", True, border_col)
            self.screen.blit(t_radar, (card_x + 16, card_y + 8))

            status_text = "[🖐️ WEBCAM ACTIVE]" if self.hand_detected else "[📷 WAITING FOR HAND]"
            status_col = (74, 222, 128) if self.hand_detected else (251, 191, 36)
            stat_surf = self.ui_font.render(status_text, True, status_col)
            self.screen.blit(stat_surf, (card_x + 16, card_y + 30))

            chk1 = "✓" if any(s["collected"] for s in self.practice_stars) or self.phase >= 3 else " "
            chk2 = "✓" if self.phase >= 3 else " "
            chk3 = "✓" if self.phase == 4 else " "

            t_sub1 = self.ui_font.render(f"[{chk1}] 1. Open Hand (🖐️): Steer Hero", True, (226, 232, 240))
            t_sub2 = self.ui_font.render(f"[{chk2}] 2. Hold Fist (✊): Talk to Sage", True, (251, 191, 36))
            t_sub3 = self.ui_font.render(f"[{chk3}] 3. Walk into Portal to Finish", True, (74, 222, 128))
            t_sub4 = self.ui_font.render("   (Collect stars on the road!)", True, (148, 163, 184))

            self.screen.blit(t_sub1, (card_x + 16, card_y + 50))
            self.screen.blit(t_sub2, (card_x + 16, card_y + 68))
            self.screen.blit(t_sub3, (card_x + 16, card_y + 86))
            self.screen.blit(t_sub4, (card_x + 16, card_y + 104))

            # Joystick Radar Display
            radar_cx = card_x + card_w - 48
            radar_cy = card_y + 68
            radar_r = 30

            pygame.draw.circle(self.screen, (30, 41, 59), (radar_cx, radar_cy), radar_r)
            pygame.draw.circle(self.screen, border_col, (radar_cx, radar_cy), radar_r, 1)
            pygame.draw.circle(self.screen, (51, 65, 85), (radar_cx, radar_cy), 10, 1)
            pygame.draw.line(self.screen, (71, 85, 105), (radar_cx - radar_r, radar_cy), (radar_cx + radar_r, radar_cy), 1)
            pygame.draw.line(self.screen, (71, 85, 105), (radar_cx, radar_cy - radar_r), (radar_cx, radar_cy + radar_r), 1)

            sweep_angle = t * 3.5
            sweep_x = radar_cx + math.cos(sweep_angle) * (radar_r - 2)
            sweep_y = radar_cy + math.sin(sweep_angle) * (radar_r - 2)
            pygame.draw.line(self.screen, (*border_col, 180), (radar_cx, radar_cy), (int(sweep_x), int(sweep_y)), 1)

            player_screen_x = (self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM
            player_screen_y = (self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM
            cur_x, cur_y = self.cursor_pos
            dx = (cur_x - player_screen_x) / 300.0
            dy = (cur_y - player_screen_y) / 300.0
            dist = math.hypot(dx, dy)
            if dist > 1.0:
                dx /= dist
                dy /= dist
            hand_dot_x = radar_cx + int(dx * (radar_r - 6))
            hand_dot_y = radar_cy + int(dy * (radar_r - 6))

            pygame.draw.line(self.screen, (255, 255, 255), (radar_cx, radar_cy), (hand_dot_x, hand_dot_y), 1)
            pygame.draw.circle(self.screen, (239, 68, 68), (hand_dot_x, hand_dot_y), 5)
            pygame.draw.circle(self.screen, (255, 255, 255), (hand_dot_x, hand_dot_y), 5, 1)

    def draw_quiz_gesture_demo(self):
        now = pygame.time.get_ticks()
        box_w, box_h = 780, 480
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        button_w, button_h = 740, 52
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 160
        spacing = 64

        target_btn_y = button_y_start + 1 * spacing
        btn_center_x = button_x + button_w - 46
        btn_center_y = target_btn_y + button_h // 2

        cycle = (now % 2400) / 2400.0
        hold_charge = min(1.0, cycle * 1.3)

        pygame.draw.circle(self.screen, (255, 255, 255), (btn_center_x, btn_center_y), 18, 2)
        if hold_charge > 0.05:
            pygame.draw.circle(self.screen, (251, 191, 36), (btn_center_x, btn_center_y), int(18 * hold_charge))
        pygame.draw.circle(self.screen, (239, 68, 68), (btn_center_x, btn_center_y), 5)

        demo_card_x = box_x + box_w + 16
        demo_card_y = target_btn_y - 24
        if demo_card_x + 220 < self.width:
            d_rect = pygame.Rect(demo_card_x, demo_card_y, 220, 100)
            d_surf = pygame.Surface((220, 100), pygame.SRCALPHA)
            d_surf.fill((15, 23, 42, 245))
            self.screen.blit(d_surf, d_rect)
            pygame.draw.rect(self.screen, (251, 191, 36), d_rect, 2, border_radius=12)

            t1 = self.ui_font.render("⭐ HOW TO ANSWER:", True, (255, 215, 0))
            t2 = self.ui_font.render("Option B (4) is Correct!", True, (255, 255, 255))
            pct = int(hold_charge * 100)
            t3 = self.ui_font.render(f"Hold Closed Fist ✊: {pct}%", True, (254, 240, 138))
            self.screen.blit(t1, (demo_card_x + 12, demo_card_y + 10))
            self.screen.blit(t2, (demo_card_x + 12, demo_card_y + 28))
            self.screen.blit(t3, (demo_card_x + 12, demo_card_y + 46))

            p_bar_rect = pygame.Rect(demo_card_x + 12, demo_card_y + 68, 196, 18)
            pygame.draw.rect(self.screen, (30, 41, 59), p_bar_rect, border_radius=6)
            fill_w = int(196 * hold_charge)
            pygame.draw.rect(self.screen, (251, 191, 36), (demo_card_x + 12, demo_card_y + 68, fill_w, 18), border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), p_bar_rect, 1, border_radius=6)

    # ============================================================
    # TOP VISUAL BANNER (100% GESTURE FOCUSED)
    # ============================================================
    def draw_top_banner(self):
        t = pygame.time.get_ticks() * 0.001
        bw = min(680, self.width - 335)
        bh = 58
        bx = 20
        by = 12

        banner_rect = pygame.Rect(bx, by, bw, bh)
        sh_rect = banner_rect.copy()
        sh_rect.y += 3
        pygame.draw.rect(self.screen, (0, 0, 0, 160), sh_rect, border_radius=16)

        b_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        b_surf.fill((15, 23, 42, 238))
        self.screen.blit(b_surf, banner_rect.topleft)

        pulse = 0.5 + 0.5 * math.sin(t * 3.0)
        uncollected = any(not s["collected"] for s in self.practice_stars)
        if self.phase == 1 and uncollected:
            step_tag = "🌟 STEP 1: CATCH STARS"
            tag_col = (251, 191, 36)
            txt = "Move open hand 🖐️ in front of camera to steer hero to Stars!"
            border_col = (245, 158, 11)
        elif self.phase in [1, 2]:
            step_tag = "🧙 STEP 2: MEET SAGE"
            tag_col = (251, 191, 36)
            txt = "Stars collected! Steer open hand 🖐️ over to the Wise Guide Sage!"
            border_col = (245, 158, 11)
        elif self.phase == 3:
            step_tag = "✨ STEP 3: SOLVE RIDDLE"
            tag_col = (234, 179, 8)
            txt = "Hold a Closed Fist ✊ on Option B (4) to select your answer!"
            border_col = (234, 179, 8)
        else:
            step_tag = "🌀 STEP 4: MAGIC PORTAL"
            tag_col = (74, 222, 128)
            txt = "Great job! Steer your hero with open hand 🖐️ into the Magic Portal!"
            border_col = (34, 197, 94)

        pygame.draw.rect(self.screen, border_col, banner_rect, 2, border_radius=16)

        tag_surf = self.ui_font.render(step_tag, True, tag_col)
        tw = tag_surf.get_width() + 16
        th = 22
        tag_rect = pygame.Rect(bx + 16, by + 10, tw, th)
        pygame.draw.rect(self.screen, (30, 41, 59), tag_rect, border_radius=6)
        pygame.draw.rect(self.screen, tag_col, tag_rect, 1, border_radius=6)
        self.screen.blit(tag_surf, (tag_rect.x + 8, tag_rect.y + 3))

        dot_x = tag_rect.right + 14
        dot_y = by + 21
        pygame.draw.circle(self.screen, (34, 197, 94), (dot_x, dot_y), int(4 + 2 * pulse))
        pygame.draw.circle(self.screen, (255, 255, 255), (dot_x, dot_y), 2)

        msg_surf = self.banner_font.render(txt, True, (255, 255, 255))
        self.screen.blit(msg_surf, (bx + 16, by + 34))

    # ============================================================
    # 3-CARD WELCOME DIALOG (100% GESTURE FOCUSED)
    # ============================================================
    def draw_welcome_dialog(self):
        """Presents a 3-Card Visual Action Guide for Grade 2 students focused 100% on gesture controls"""
        box_w = min(self.width - 40, 960)
        box_h = 440
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        if self._dim_overlay is None or self._dim_overlay.get_size() != (self.width, self.height):
            self._dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dim_overlay.fill((0, 0, 0, 160))
        self.screen.blit(self._dim_overlay, (0, 0))

        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=20)

        card_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        card_surf.fill((15, 23, 42, 248))
        self.screen.blit(card_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (245, 158, 11), (box_x, box_y, box_w, box_h), 3, border_radius=20)
        pygame.draw.rect(self.screen, (251, 191, 36), (box_x + 3, box_y + 3, box_w - 6, box_h - 6), 1, border_radius=17)

        # Header with Guide Sage Portrait
        p_size = 64
        p_x = box_x + 20
        p_y = box_y + 16
        p_rect = pygame.Rect(p_x, p_y, p_size, p_size)

        pygame.draw.rect(self.screen, (30, 41, 59), p_rect, border_radius=12)
        pygame.draw.rect(self.screen, (251, 191, 36), p_rect, 2, border_radius=12)

        if self.npc_frames:
            scaled_npc = pygame.transform.scale(self.npc_frames[self.npc_anim_frame], (p_size - 8, p_size - 8))
            self.screen.blit(scaled_npc, (p_x + 4, p_y + 4))

        name_x = p_x + p_size + 16
        name_y = box_y + 16
        name_surf = self.dialog_header_font.render("🧙 Wise Guide Sage — Magic Gesture Controls", True, (255, 215, 0))
        self.screen.blit(name_surf, (name_x, name_y))

        sub_surf = self.card_title_font.render("Master your magic hands-free controls in 3 fun steps!", True, (203, 213, 225))
        self.screen.blit(sub_surf, (name_x, name_y + 32))

        # 3 Big Visual Action Cards
        card_margin = 14
        total_card_w = box_w - 40
        c_w = (total_card_w - card_margin * 2) // 3
        c_h = 240
        c_y = box_y + 92

        # Card 1: 🖐️ HOW TO WALK
        c1_x = box_x + 20
        c1_rect = pygame.Rect(c1_x, c_y, c_w, c_h)
        pygame.draw.rect(self.screen, (30, 41, 59), c1_rect, border_radius=14)
        pygame.draw.rect(self.screen, (34, 197, 94), c1_rect, 2, border_radius=14)

        pill1 = pygame.Rect(c1_x + 14, c_y + 12, c_w - 28, 26)
        pygame.draw.rect(self.screen, (20, 83, 45), pill1, border_radius=6)
        pygame.draw.rect(self.screen, (74, 222, 128), pill1, 1, border_radius=6)
        p1_txt = self.card_title_font.render("1. HOW TO WALK", True, (187, 247, 208))
        self.screen.blit(p1_txt, p1_txt.get_rect(center=pill1.center))

        g1_txt = self.huge_font.render("🖐️", True, (74, 222, 128))
        self.screen.blit(g1_txt, g1_txt.get_rect(center=(c1_x + c_w // 2, c_y + 72)))

        t_w1 = self.card_title_font.render("Open Hand Gesture", True, (255, 255, 255))
        self.screen.blit(t_w1, t_w1.get_rect(center=(c1_x + c_w // 2, c_y + 112)))

        d1 = self.ui_font.render("• Show open hand to webcam", True, (203, 213, 225))
        d2 = self.ui_font.render("• Move hand Up, Down, Left, Right", True, (203, 213, 225))
        d3 = self.ui_font.render("• Hero runs where hand leads!", True, (74, 222, 128))
        self.screen.blit(d1, (c1_x + 18, c_y + 142))
        self.screen.blit(d2, (c1_x + 18, c_y + 168))
        self.screen.blit(d3, (c1_x + 18, c_y + 194))

        # Card 2: ⭐ CATCH STARS
        c2_x = c1_x + c_w + card_margin
        c2_rect = pygame.Rect(c2_x, c_y, c_w, c_h)
        pygame.draw.rect(self.screen, (30, 41, 59), c2_rect, border_radius=14)
        pygame.draw.rect(self.screen, (251, 191, 36), c2_rect, 2, border_radius=14)

        pill2 = pygame.Rect(c2_x + 14, c_y + 12, c_w - 28, 26)
        pygame.draw.rect(self.screen, (120, 53, 15), pill2, border_radius=6)
        pygame.draw.rect(self.screen, (251, 191, 36), pill2, 1, border_radius=6)
        p2_txt = self.card_title_font.render("2. CATCH STARS", True, (254, 240, 138))
        self.screen.blit(p2_txt, p2_txt.get_rect(center=pill2.center))

        g2_txt = self.huge_font.render("⭐  ⭐", True, (251, 191, 36))
        self.screen.blit(g2_txt, g2_txt.get_rect(center=(c2_x + c_w // 2, c_y + 72)))

        t_w2 = self.card_title_font.render("Shiny Wisdom Stars", True, (255, 255, 255))
        self.screen.blit(t_w2, t_w2.get_rect(center=(c2_x + c_w // 2, c_y + 112)))

        d4 = self.ui_font.render("• Steer hero over shiny stars", True, (203, 213, 225))
        d5 = self.ui_font.render("• Catch all 2 practice stars", True, (203, 213, 225))
        d6 = self.ui_font.render("• Unlocks the Sage's trial!", True, (254, 240, 138))
        self.screen.blit(d4, (c2_x + 18, c_y + 142))
        self.screen.blit(d5, (c2_x + 18, c_y + 168))
        self.screen.blit(d6, (c2_x + 18, c_y + 194))

        # Card 3: ✊ HOW TO CLICK
        c3_x = c2_x + c_w + card_margin
        c3_rect = pygame.Rect(c3_x, c_y, c_w, c_h)
        pygame.draw.rect(self.screen, (30, 41, 59), c3_rect, border_radius=14)
        pygame.draw.rect(self.screen, (244, 63, 94), c3_rect, 2, border_radius=14)

        pill3 = pygame.Rect(c3_x + 14, c_y + 12, c_w - 28, 26)
        pygame.draw.rect(self.screen, (136, 19, 55), pill3, border_radius=6)
        pygame.draw.rect(self.screen, (251, 113, 133), pill3, 1, border_radius=6)
        p3_txt = self.card_title_font.render("3. HOW TO CLICK", True, (254, 205, 211))
        self.screen.blit(p3_txt, p3_txt.get_rect(center=pill3.center))

        g3_txt = self.huge_font.render("✊", True, (251, 113, 133))
        self.screen.blit(g3_txt, g3_txt.get_rect(center=(c3_x + c_w // 2, c_y + 72)))

        t_w3 = self.card_title_font.render("Close Fist to Click", True, (255, 255, 255))
        self.screen.blit(t_w3, t_w3.get_rect(center=(c3_x + c_w // 2, c_y + 112)))

        d7 = self.ui_font.render("• Close fingers into tight fist (✊)", True, (203, 213, 225))
        d8 = self.ui_font.render("• Hold steady for 0.9 seconds", True, (203, 213, 225))
        d9 = self.ui_font.render("• Golden ring fills up to Select!", True, (251, 191, 36))
        self.screen.blit(d7, (c3_x + 18, c_y + 142))
        self.screen.blit(d8, (c3_x + 18, c_y + 168))
        self.screen.blit(d9, (c3_x + 18, c_y + 194))

        # CTA Button
        btn_w = 380
        btn_h = 48
        btn_x = box_x + (box_w - btn_w) // 2
        btn_y = box_y + box_h - btn_h - 18
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        is_hov = btn_rect.collidepoint(self.cursor_pos)
        btn_bg = (245, 158, 11) if is_hov else (180, 83, 9)

        pygame.draw.rect(self.screen, (0, 0, 0, 120), btn_rect.move(2, 2), border_radius=14)
        pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255) if is_hov else (251, 191, 36), btn_rect, 2, border_radius=14)

        fist_hold_pct = 0.0
        if self.fist_start_time > 0 and self.current_gesture == "FIST":
            fist_hold_pct = min(1.0, (time.time() - self.fist_start_time) / self.CLICK_HOLD_TIME)

        if fist_hold_pct > 0.0:
            fill_w = int(btn_w * fist_hold_pct)
            fill_rect = pygame.Rect(btn_x, btn_y, fill_w, btn_h)
            fill_surf = pygame.Surface((fill_w, btn_h), pygame.SRCALPHA)
            fill_surf.fill((255, 255, 255, 80))
            self.screen.blit(fill_surf, fill_rect)

        btn_txt_str = "Start Adventure! 🚀 (Hold Fist ✊)" if fist_hold_pct == 0.0 else f"Starting: {int(fist_hold_pct * 100)}%"
        btn_txt = self.dialog_btn_font.render(btn_txt_str, True, (255, 255, 255))
        self.screen.blit(btn_txt, btn_txt.get_rect(center=btn_rect.center))

    # ============================================================
    # SAMPLE QUIZ MODAL DIALOGS
    # ============================================================
    def draw_sample_quiz_dialog(self):
        box_w, box_h = 780, 480
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        if self._dim_overlay is None or self._dim_overlay.get_size() != (self.width, self.height):
            self._dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dim_overlay.fill((0, 0, 0, 160))
        self.screen.blit(self._dim_overlay, (0, 0))

        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=18)

        card_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        card_surf.fill((15, 23, 42, 245))
        self.screen.blit(card_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (245, 158, 11), (box_x, box_y, box_w, box_h), 2, border_radius=18)

        # Header Bar with Guide Sage portrait
        h_w = box_w - 32
        h_h = 48
        h_x = box_x + 16
        h_y = box_y + 14
        h_surf = pygame.Surface((h_w, h_h), pygame.SRCALPHA)
        h_surf.fill((30, 41, 59, 240))
        self.screen.blit(h_surf, (h_x, h_y))
        pygame.draw.rect(self.screen, (251, 191, 36), (h_x, h_y, h_w, h_h), 1, border_radius=10)

        if self.npc_frames:
            s_port = pygame.transform.scale(self.npc_frames[self.npc_anim_frame], (34, 34))
            self.screen.blit(s_port, (h_x + 10, h_y + 7))

        title = self.dialog_header_font.render("Guide Sage — Trial of Wisdom (Demonstration)", True, (255, 215, 0))
        self.screen.blit(title, (h_x + 52, h_y + 8))

        # Question card with visual star math
        q_card_w = box_w - 32
        q_card_h = 68
        q_card_x = box_x + 16
        q_card_y = box_y + 72
        q_bg = pygame.Surface((q_card_w, q_card_h), pygame.SRCALPHA)
        q_bg.fill((20, 29, 47, 220))
        self.screen.blit(q_bg, (q_card_x, q_card_y))
        pygame.draw.rect(self.screen, (51, 65, 85), (q_card_x, q_card_y, q_card_w, q_card_h), 1, border_radius=8)

        q_txt = self.dialog_q_font.render(self.sample_question["question"], True, (255, 255, 255))
        self.screen.blit(q_txt, (q_card_x + 18, q_card_y + 8))

        v_math = self.ui_font.render("Visual Guide:  [ 2 ⭐ ]  +  [ 2 ⭐ ]  =  [ 4 ⭐ ]", True, (254, 240, 138))
        self.screen.blit(v_math, (q_card_x + 18, q_card_y + 38))

        if self.wrong_feedback_msg:
            fb_surf = self.ui_font.render(self.wrong_feedback_msg, True, (252, 211, 77))
            self.screen.blit(fb_surf, (box_x + 20, box_y + 144))

        button_w, button_h = 740, 52
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 160
        spacing = 64

        letters = ["A", "B", "C", "D"]
        for i, choice_text in enumerate(self.sample_question["choices"]):
            b_y = button_y_start + i * spacing
            btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)
            is_elim = (i == self.eliminated_choice)
            is_hov = btn_rect.collidepoint(self.cursor_pos) and not is_elim

            if is_elim:
                bg_color = (20, 25, 35)
                text_color = (100, 116, 139)
                border_color = (51, 65, 85)
                badge_bg = (30, 41, 59)
                badge_fg = (100, 116, 139)
            elif is_hov:
                bg_color = (251, 191, 36)
                text_color = (15, 23, 42)
                border_color = (255, 255, 255)
                badge_bg = (15, 23, 42)
                badge_fg = (251, 191, 36)
            elif i == 1:
                bg_color = (30, 41, 59)
                text_color = (248, 250, 252)
                border_color = (251, 191, 36)
                badge_bg = (15, 23, 42)
                badge_fg = (251, 191, 36)
            else:
                bg_color = (30, 41, 59)
                text_color = (248, 250, 252)
                border_color = (71, 85, 105)
                badge_bg = (15, 23, 42)
                badge_fg = (251, 191, 36)

            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, border_color, btn_rect, 2 if (is_hov or i == 1) else 1, border_radius=12)

            pill_rect = pygame.Rect(btn_rect.x + 14, btn_rect.y + 8, 38, 36)
            pygame.draw.rect(self.screen, badge_bg, pill_rect, border_radius=8)
            pygame.draw.rect(self.screen, border_color, pill_rect, 1, border_radius=8)
            pill_txt = self.dialog_choice_font.render(letters[i], True, badge_fg)
            self.screen.blit(pill_txt, pill_txt.get_rect(center=pill_rect.center))

            raw_text = choice_text[3:] if len(choice_text) > 3 and choice_text[1] == '.' else choice_text
            display_text = f"Option {letters[i]}:  {raw_text}" if not is_elim else f"{choice_text}  [ Eliminated ]"
            c_surf = self.dialog_choice_font.render(display_text, True, text_color)
            self.screen.blit(c_surf, (btn_rect.x + 66, btn_rect.y + 12))

    def draw_sample_wrong_dialog(self):
        box_w, box_h = 760, 350
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        if self._dim_overlay is None or self._dim_overlay.get_size() != (self.width, self.height):
            self._dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dim_overlay.fill((0, 0, 0, 160))
        self.screen.blit(self._dim_overlay, (0, 0))

        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=18)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=18)
        pygame.draw.rect(self.screen, (239, 68, 68), dialog_rect, 3, border_radius=18)

        p_size = 76
        p_x = box_x + 22
        p_y = box_y + 20
        p_rect = pygame.Rect(p_x, p_y, p_size, p_size)
        pygame.draw.rect(self.screen, (30, 41, 59), p_rect, border_radius=12)
        pygame.draw.rect(self.screen, (239, 68, 68), p_rect, 2, border_radius=12)

        if self.npc_frames:
            scaled_npc = pygame.transform.scale(self.npc_frames[self.npc_anim_frame], (p_size - 8, p_size - 8))
            self.screen.blit(scaled_npc, (p_x + 4, p_y + 4))

        speaker = self.dialog_header_font.render("Guide Sage — Second Chance Trial", True, (248, 113, 113))
        self.screen.blit(speaker, (p_x + p_size + 18, box_y + 20))

        role = self.ui_font.render("Trial Feedback & Guidance", True, (148, 163, 184))
        self.screen.blit(role, (p_x + p_size + 18, box_y + 48))

        att_rect = pygame.Rect(box_x + box_w - 230, box_y + 18, 204, 32)
        pygame.draw.rect(self.screen, (30, 41, 59), att_rect, border_radius=8)
        pygame.draw.rect(self.screen, (251, 191, 36), att_rect, 1, border_radius=8)
        att_txt = self.ui_font.render("1 ATTEMPT REMAINING", True, (254, 240, 138))
        self.screen.blit(att_txt, att_txt.get_rect(center=att_rect.center))

        m1 = self.dialog_q_font.render("Almost! In this quest, you get 2 attempts per trial.", True, (255, 255, 255))
        m2 = self.dialog_choice_font.render("Tip: Think about what 2 plus 2 equals (2 + 2 = 4).", True, (203, 213, 225))
        m3 = self.ui_font.render("Hold a Closed Fist ✊ (0.9s) on Option B to pick again!", True, (254, 240, 138))
        self.screen.blit(m1, (box_x + 28, box_y + 114))
        self.screen.blit(m2, (box_x + 28, box_y + 154))
        self.screen.blit(m3, (box_x + 28, box_y + 194))

        btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 270, 260, 52)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if is_hov else (153, 27, 27), btn_rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=14)

        c_surf = self.dialog_btn_font.render("Try Again (Hold Fist ✊)", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_sample_correct_dialog(self):
        box_w, box_h = 760, 350
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        if self._dim_overlay is None or self._dim_overlay.get_size() != (self.width, self.height):
            self._dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._dim_overlay.fill((0, 0, 0, 160))
        self.screen.blit(self._dim_overlay, (0, 0))

        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=18)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=18)
        pygame.draw.rect(self.screen, (34, 197, 94), dialog_rect, 3, border_radius=18)

        p_size = 76
        p_x = box_x + 22
        p_y = box_y + 20
        p_rect = pygame.Rect(p_x, p_y, p_size, p_size)
        pygame.draw.rect(self.screen, (30, 41, 59), p_rect, border_radius=12)
        pygame.draw.rect(self.screen, (34, 197, 94), p_rect, 2, border_radius=12)

        if self.npc_frames:
            scaled_npc = pygame.transform.scale(self.npc_frames[self.npc_anim_frame], (p_size - 8, p_size - 8))
            self.screen.blit(scaled_npc, (p_x + 4, p_y + 4))

        speaker = self.dialog_header_font.render("Guide Sage — Trial Mastered!", True, (74, 222, 128))
        self.screen.blit(speaker, (p_x + p_size + 18, box_y + 20))

        role = self.ui_font.render("Portal Odyssey Unlocked", True, (148, 163, 184))
        self.screen.blit(role, (p_x + p_size + 18, box_y + 48))

        for s_i in range(3):
            sc_x = box_x + box_w - 95 + s_i * 26
            sc_y = box_y + 34
            pygame.draw.circle(self.screen, (251, 191, 36), (sc_x, sc_y), 8)
            pygame.draw.circle(self.screen, (254, 240, 138), (sc_x, sc_y), 5)
            pygame.draw.circle(self.screen, (255, 255, 255), (sc_x, sc_y), 8, 1)

        m1 = self.dialog_q_font.render("Outstanding! 2 + 2 = 4 is correct! Full stars earned!", True, (255, 255, 255))
        m2 = self.dialog_choice_font.render("The mystical Exit Portal has materialized on the path ahead.", True, (203, 213, 225))
        m3 = self.ui_font.render("Step through the glowing portal with your Open Hand 🖐️!", True, (254, 240, 138))
        self.screen.blit(m1, (box_x + 28, box_y + 114))
        self.screen.blit(m2, (box_x + 28, box_y + 154))
        self.screen.blit(m3, (box_x + 28, box_y + 194))

        btn_rect = pygame.Rect(box_x + (box_w - 260) // 2, box_y + 270, 260, 52)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (34, 197, 94) if is_hov else (22, 101, 52), btn_rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=14)

        c_surf = self.dialog_btn_font.render("Continue >> (Hold Fist ✊)", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))
