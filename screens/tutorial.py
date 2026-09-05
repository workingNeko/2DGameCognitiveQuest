# screens/tutorial.py - Live Interactive Gameplay Showcase Tutorial
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
        self.phase_banner_timer = 0.0
        self.phase_transition_timer = 0.0

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
        self.dialog_header_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 22, bold=True)
        self.dialog_q_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 20, bold=True)
        self.dialog_choice_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18, bold=True)
        self.dialog_btn_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 18, bold=True)
        self.ui_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 12, bold=True)
        self.skip_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 16, bold=True)

        # Universal In-Stage Pause Menu
        from core.pause_menu import InGamePauseMenu
        self.pause_menu = InGamePauseMenu(self.screen, self.width, self.height, self.main_menu, return_callback=self.finish_tutorial, restart_callback=self.restart_tutorial)

        print("[TUTORIAL] Live Interactive Gameplay Tutorial Initialized!")

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

        # Player Movement (Active during Phase 1, Phase 2, and Phase 4 when quiz modal is closed)
        if self.quiz_state == 0:
            self.update_player_movement()

        # Check Phase Transitions
        npc_dist = math.hypot(self.player_x - self.npc_tile_x * TILE_SIZE, self.player_y - self.npc_tile_y * TILE_SIZE)
        portal_dist = math.hypot(self.player_x - self.portal_tile_x * TILE_SIZE, self.player_y - self.portal_tile_y * TILE_SIZE)

        # Proximity to NPC immediately triggers the question dialogue
        if self.phase == 1 and npc_dist < 2.5 * TILE_SIZE:
            self.phase = 3
            self.quiz_state = 1
            print("[TUTORIAL] Player approached Guide NPC: Automatically Triggered Question Dialogue!")

        if self.phase == 4 and portal_dist < 1.8 * TILE_SIZE:
            print("[WIN] Exit Portal Entered! Tutorial Complete!")
            self.finish_tutorial()

    def update_player_movement(self):
        vx, vy = 0, 0
        current_speed = SPEED

        # 1. Gesture / Cursor Steering (relative to on-screen player position)
        player_screen_x = (self.player_x - self.camera_x + TILE_SIZE / 2) * ZOOM
        player_screen_y = (self.player_y - self.camera_y + TILE_SIZE / 2) * ZOOM
        cursor_x, cursor_y = self.cursor_pos
        dx = cursor_x - player_screen_x
        dy = cursor_y - player_screen_y

        dist_factor = 1.3 if (abs(dx) > 160 or abs(dy) > 160) else 1.0
        g_speed = current_speed * dist_factor

        if abs(dx) > 45:
            vx = g_speed if dx > 0 else -g_speed
            self.player_dir = "right" if dx > 0 else "left"

        if abs(dy) > 45:
            vy = g_speed if dy > 0 else -g_speed
            self.player_dir = "down" if dy > 0 else "up"

        # 2. Dual Keyboard Control (WASD / Arrow Keys)
        keys = pygame.key.get_pressed()
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

        new_x = self.player_x + vx
        new_y = self.player_y + vy

        # Collision with map boundaries & trees
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

    def can_move(self, x, y):
        # 16px collision box centered on player feet
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

        if hasattr(self, 'pause_menu') and self.pause_menu.is_paused:
            return "blocked"

        self.lol_camera.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.trigger_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.quiz_state == 0:
                self.lol_camera.recenter()
            elif event.key == pygame.K_ESCAPE:
                if hasattr(self, 'pause_menu'):
                    self.pause_menu.toggle_pause()
                else:
                    self.finish_tutorial()
            elif self.quiz_state == 1:
                # Keyboard quick-answers: 1/A, 2/B, 3/C, 4/D
                if event.key in [pygame.K_1, pygame.K_a]:
                    self.submit_quiz_answer(0)
                elif event.key in [pygame.K_2, pygame.K_b]:
                    self.submit_quiz_answer(1)
                elif event.key in [pygame.K_3, pygame.K_c]:
                    self.submit_quiz_answer(2)
                elif event.key in [pygame.K_4, pygame.K_d]:
                    self.submit_quiz_answer(3)
            elif self.quiz_state == 2 and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.quiz_state = 1
            elif self.quiz_state == 3 and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.quiz_state = 0
                self.phase = 4

    def submit_quiz_answer(self, choice_idx):
        if choice_idx == self.eliminated_choice:
            return
        if choice_idx == self.sample_question["correct"]:
            self.quiz_state = 3  # Correct
            print("[OK] Correct Answer in Tutorial Quiz!")
        else:
            self.quiz_attempts += 1
            self.eliminated_choice = choice_idx
            self.wrong_feedback_msg = "Almost! You have 1 try remaining. Pick again!"
            self.quiz_state = 2 if self.quiz_attempts < 2 else 3
            print("[FAIL] Wrong Answer in Tutorial Quiz -> Showing 2-Attempt Mechanics!")

    def trigger_click(self, pos=None):
        if pos is None:
            pos = self.cursor_pos

        # Check Pause Menu clicks first
        if hasattr(self, 'pause_menu') and self.pause_menu.handle_click(pos):
            return

        # 1. Skip Button (Top Right, beside Pause Button)
        skip_rect = pygame.Rect(self.width - 310, 18, 165, 36)
        if skip_rect.collidepoint(pos):
            self.finish_tutorial()
            return

        # 2. Phase 2: NPC Click Interaction
        if self.phase == 2 and self.quiz_state == 0:
            screen_npc_x = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM
            npc_rect = pygame.Rect(screen_npc_x - 20, screen_npc_y - 20, TILE_SIZE * ZOOM + 40, TILE_SIZE * ZOOM + 40)
            if npc_rect.collidepoint(pos) or math.hypot(self.player_x - self.npc_tile_x * TILE_SIZE, self.player_y - self.npc_tile_y * TILE_SIZE) < 3.0 * TILE_SIZE:
                self.phase = 3
                self.quiz_state = 1
                print("[TUTORIAL] Opening Sample Quiz Modal!")
                return

        # 3. Phase 3: Sample Quiz Dialog Clicks
        if self.quiz_state == 1:
            box_w, box_h = 600, 390
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            button_w, button_h = 560, 48
            button_x = box_x + (box_w - button_w) // 2
            button_y_start = box_y + 142
            spacing = 56

            for i in range(4):
                if i == self.eliminated_choice:
                    continue
                btn_rect = pygame.Rect(button_x, button_y_start + i * spacing, button_w, button_h)
                if btn_rect.collidepoint(pos):
                    self.submit_quiz_answer(i)
                    return

        # Retry / Continue Dialog Clicks
        elif self.quiz_state == 2:
            box_w, box_h = 600, 270
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 230) // 2, box_y + 180, 230, 48)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                return

        elif self.quiz_state == 3:
            box_w, box_h = 600, 280
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 195, 240, 48)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 0
                self.phase = 4
                print("[TUTORIAL] Tutorial Phase 4: Portal Unlocked! Guide student to Exit Portal.")
                return

    def finish_tutorial(self):
        from db.save_system import set_tutorial_completed
        student_id = getattr(self.main_menu, 'student_id', None)
        if student_id:
            set_tutorial_completed(self.main_menu, student_id, completed=True)

        print("[GO] Tutorial Complete! Opening Stage Select...")
        from screens.stageselect import StageSelect
        self.main_menu.current_screen = "stage_select"
        self.main_menu.stage_select = StageSelect(self.screen, self.main_menu)

    # ============================================================
    # DRAW LOOP
    # ============================================================
    def draw(self):
        self.screen.fill((15, 23, 42))

        # 1. Render World Tiles
        start_col = max(0, int(self.camera_x // TILE_SIZE))
        end_col = min(len(self.map_grid[0]), int((self.camera_x + self.width / ZOOM) // TILE_SIZE) + 2)
        start_row = max(0, int(self.camera_y // TILE_SIZE))
        end_row = min(len(self.map_grid), int((self.camera_y + self.height / ZOOM) // TILE_SIZE) + 2)

        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                tile_char = self.map_grid[r][c]
                t_surf = self.tile_sprites.get(tile_char, self.tile_sprites['G'])
                sx = (c * TILE_SIZE - self.camera_x) * ZOOM
                sy = (r * TILE_SIZE - self.camera_y) * ZOOM
                scaled_t = pygame.transform.scale(t_surf, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
                self.screen.blit(scaled_t, (sx, sy))

        # 2. Render Exit Portal (Only appears after question is answered)
        if self.phase == 4:
            p_sx = (self.portal_tile_x * TILE_SIZE - self.camera_x) * ZOOM
            p_sy = (self.portal_tile_y * TILE_SIZE - self.camera_y) * ZOOM
            if self.portal_frames:
                p_frame = self.portal_frames[self.portal_anim_frame]
                scaled_p = pygame.transform.scale(p_frame, (int(TILE_SIZE * 3 * ZOOM), int(TILE_SIZE * 3 * ZOOM)))
                self.screen.blit(scaled_p, (p_sx - int(TILE_SIZE * ZOOM), p_sy - int(TILE_SIZE * ZOOM)))

                # Glowing portal magic aura ring
                ring_radius = int((24 + math.sin(pygame.time.get_ticks() * 0.006) * 4) * ZOOM)
                pygame.draw.circle(self.screen, (74, 222, 128), (int(p_sx + (TILE_SIZE / 2) * ZOOM), int(p_sy + (TILE_SIZE / 2) * ZOOM)), ring_radius, 2)

        # 3. Render Guide NPC
        npc_sx = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM
        npc_sy = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM
        if self.npc_frames:
            npc_f = self.npc_frames[self.npc_anim_frame]
            scaled_npc = pygame.transform.scale(npc_f, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
            self.screen.blit(scaled_npc, (npc_sx, npc_sy))

        # 4. Render Player Character
        pl_sx = (self.player_x - self.camera_x) * ZOOM
        pl_sy = (self.player_y - self.camera_y) * ZOOM
        dir_sprites = self.player_sprites.get(self.player_dir, self.player_sprites["down"])
        pl_f = dir_sprites[self.anim_frame]
        scaled_pl = pygame.transform.scale(pl_f, (int(TILE_SIZE * ZOOM), int(TILE_SIZE * ZOOM)))
        self.screen.blit(scaled_pl, (pl_sx, pl_sy))

        # 5. Demonstration Animation Overlay (Visual guide trail, animated steering, and fist hold demo)
        self.draw_demonstration_overlay()

        # 6. Dynamic Compass Pointers & On-Screen Quest Badges
        self.draw_compass_and_badges()

        # 7. Top Visual Gameplay Banner
        self.draw_top_banner()

        # 8. Prominent Glassmorphism Skip Button
        skip_rect = pygame.Rect(self.width - 310, 18, 165, 36)
        skip_hov = skip_rect.collidepoint(self.cursor_pos)

        # Shadow
        shadow_rect = skip_rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(self.screen, (0, 0, 0, 140), shadow_rect, border_radius=10)

        # Body
        skip_surf = pygame.Surface((skip_rect.width, skip_rect.height), pygame.SRCALPHA)
        skip_bg = (220, 38, 38, 230) if skip_hov else (15, 23, 42, 235)
        pygame.draw.rect(skip_surf, skip_bg, (0, 0, skip_rect.width, skip_rect.height), border_radius=10)
        self.screen.blit(skip_surf, skip_rect.topleft)

        # Border
        border_col = (251, 191, 36) if skip_hov else (148, 163, 184)
        pygame.draw.rect(self.screen, border_col, skip_rect, 2, border_radius=10)

        # Text
        skip_txt = self.skip_font.render("Skip Tutorial", True, (255, 255, 255))
        self.screen.blit(skip_txt, (skip_rect.x + 14, skip_rect.y + 8))

        # [SKIP] Pill badge
        pill_rect = pygame.Rect(skip_rect.right - 54, skip_rect.y + 6, 44, 24)
        pygame.draw.rect(self.screen, (30, 41, 59), pill_rect, border_radius=6)
        pygame.draw.rect(self.screen, (251, 191, 36) if skip_hov else (100, 116, 139), pill_rect, 1, border_radius=6)
        esc_txt = self.ui_font.render("SKIP", True, (251, 191, 36) if skip_hov else (203, 213, 225))
        self.screen.blit(esc_txt, esc_txt.get_rect(center=pill_rect.center))

        # 9. Render Quiz Modal Dialogs
        if self.quiz_state == 1:
            self.draw_sample_quiz_dialog()
            self.draw_quiz_gesture_demo()
        elif self.quiz_state == 2:
            self.draw_sample_wrong_dialog()
        elif self.quiz_state == 3:
            self.draw_sample_correct_dialog()

        # 10. In-Game Universal Pause Button & Modal Overlay
        if hasattr(self, 'pause_menu'):
            self.pause_menu.draw_button(self.cursor_pos)
            if self.pause_menu.is_paused:
                self.pause_menu.draw_modal(self.cursor_pos)

    # ============================================================
    # DYNAMIC COMPASS & BADGES
    # ============================================================
    def draw_compass_and_badges(self):
        # Target = Guide NPC for Phase 1 & 2
        if self.phase in [1, 2]:
            st_x, st_y = self.npc_tile_x, self.npc_tile_y
            screen_npc_x = (st_x * TILE_SIZE - self.camera_x) * ZOOM
            screen_npc_y = (st_y * TILE_SIZE - self.camera_y) * ZOOM

            # On-Screen Diamond Badge '!'
            bob = math.sin(pygame.time.get_ticks() * 0.008) * 4 * ZOOM
            badge_x = screen_npc_x + (TILE_SIZE * ZOOM) / 2 - 8 * ZOOM
            badge_y = screen_npc_y - 22 * ZOOM + bob

            badge_rect = pygame.Rect(badge_x, badge_y, 16 * ZOOM, 16 * ZOOM)
            pygame.draw.rect(self.screen, (255, 215, 0), badge_rect, border_radius=4)
            pygame.draw.rect(self.screen, (0, 0, 0), badge_rect, 1, border_radius=4)
            excl_surf = self.ui_font.render("!", True, (0, 0, 0))
            self.screen.blit(excl_surf, excl_surf.get_rect(center=badge_rect.center))

            # Name Tag
            tag_surf = self.ui_font.render("Guide Sage", True, (255, 235, 120))
            tag_w, tag_h = tag_surf.get_width() + 10, tag_surf.get_height() + 4
            tag_rect = pygame.Rect(screen_npc_x + (TILE_SIZE * ZOOM) / 2 - tag_w / 2, badge_y - tag_h - 2, tag_w, tag_h)
            tag_bg = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
            tag_bg.fill((15, 23, 42, 210))
            self.screen.blit(tag_bg, tag_rect)
            pygame.draw.rect(self.screen, (255, 215, 0), tag_rect, 1, border_radius=4)
            self.screen.blit(tag_surf, (tag_rect.x + 5, tag_rect.y + 2))

            # Off-Screen Pointer Pill
            is_on_screen = (40 <= screen_npc_x <= self.width - 60 and 40 <= screen_npc_y <= self.height - 110)
            if not is_on_screen:
                player_screen_x = (self.player_x - self.camera_x) * ZOOM
                player_screen_y = (self.player_y - self.camera_y) * ZOOM
                dx = screen_npc_x - player_screen_x
                dy = screen_npc_y - player_screen_y
                dist_m = int(math.hypot(self.player_x - st_x * TILE_SIZE, self.player_y - st_y * TILE_SIZE) // TILE_SIZE)
                angle = math.atan2(dy, dx)
                clamp_x = max(60, min(self.width - 60, player_screen_x + math.cos(angle) * 180))
                clamp_y = max(60, min(self.height - 100, player_screen_y + math.sin(angle) * 180))

                ptr_text = f">> Guide Sage ({dist_m}m)"
                ptr_surf = self.ui_font.render(ptr_text, True, (15, 23, 42))
                pw, ph = ptr_surf.get_width() + 16, 26
                p_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)
                pygame.draw.rect(self.screen, (255, 215, 0), p_rect, border_radius=8)
                pygame.draw.rect(self.screen, (255, 255, 255), p_rect, 2, border_radius=8)
                self.screen.blit(ptr_surf, (p_rect.x + 8, p_rect.y + 4))

        # Target = Exit Portal for Phase 4
        elif self.phase == 4:
            p_cx = self.portal_tile_x * TILE_SIZE
            p_cy = self.portal_tile_y * TILE_SIZE
            screen_p_x = (p_cx - self.camera_x) * ZOOM
            screen_p_y = (p_cy - self.camera_y) * ZOOM
            is_on_screen = (40 <= screen_p_x <= self.width - 60 and 40 <= screen_p_y <= self.height - 110)
            if not is_on_screen:
                player_screen_x = (self.player_x - self.camera_x) * ZOOM
                player_screen_y = (self.player_y - self.camera_y) * ZOOM
                dx = screen_p_x - player_screen_x
                dy = screen_p_y - player_screen_y
                dist_m = int(math.hypot(self.player_x - p_cx, self.player_y - p_cy) // TILE_SIZE)
                angle = math.atan2(dy, dx)
                clamp_x = max(60, min(self.width - 60, player_screen_x + math.cos(angle) * 180))
                clamp_y = max(60, min(self.height - 100, player_screen_y + math.sin(angle) * 180))

                ptr_text = f">> Exit Portal ({dist_m}m)"
                ptr_surf = self.ui_font.render(ptr_text, True, (15, 23, 42))
                pw, ph = ptr_surf.get_width() + 16, 26
                p_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)
                pygame.draw.rect(self.screen, (74, 222, 128), p_rect, border_radius=8)
                pygame.draw.rect(self.screen, (255, 255, 255), p_rect, 2, border_radius=8)
                self.screen.blit(ptr_surf, (p_rect.x + 8, p_rect.y + 4))

    # ============================================================
    # DEMONSTRATION ANIMATION OVERLAY
    # ============================================================
    def draw_demonstration_overlay(self):
        """Draws visual demonstration animations guiding the player on screen"""
        now = pygame.time.get_ticks()
        t = now * 0.001

        # 1. Radiant Celestial Starlight Trail
        if self.phase in [1, 4]:
            pl_sx = (self.player_x - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
            pl_sy = (self.player_y - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2

            if self.phase == 1:
                target_sx = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
                target_sy = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2
                trail_color = (255, 215, 0)
                glow_color = (254, 240, 138)
            else:
                target_sx = (self.portal_tile_x * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
                target_sy = (self.portal_tile_y * TILE_SIZE - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2
                trail_color = (74, 222, 128)
                glow_color = (187, 247, 208)

            if target_sx > pl_sx + 20:
                step = 34 * ZOOM
                offset = (now * 0.05) % step
                cur_x = pl_sx + offset
                while cur_x < target_sx - 20:
                    pulse_r = int((5 + math.sin(t * 5.0 + cur_x * 0.1) * 2) * ZOOM)

                    # Outer soft glowing halo
                    halo_surf = pygame.Surface((pulse_r * 4, pulse_r * 4), pygame.SRCALPHA)
                    pygame.draw.circle(halo_surf, (*trail_color, 60), (pulse_r * 2, pulse_r * 2), pulse_r * 2)
                    self.screen.blit(halo_surf, (int(cur_x - pulse_r * 2), int(pl_sy - pulse_r * 2)))

                    # Diamond starlight mote
                    d_size = int(6 * ZOOM)
                    diamond = [
                        (cur_x, pl_sy - d_size),
                        (cur_x + d_size, pl_sy),
                        (cur_x, pl_sy + d_size),
                        (cur_x - d_size, pl_sy)
                    ]
                    pygame.draw.polygon(self.screen, glow_color, diamond)
                    pygame.draw.polygon(self.screen, trail_color, diamond, 1)

                    # Dynamic forward chevron
                    c_x = cur_x + 8 * ZOOM
                    p1 = (c_x - 4 * ZOOM, pl_sy - 6 * ZOOM)
                    p2 = (c_x + 4 * ZOOM, pl_sy)
                    p3 = (c_x - 4 * ZOOM, pl_sy + 6 * ZOOM)
                    pygame.draw.lines(self.screen, trail_color, False, [p1, p2, p3], 2)

                    cur_x += step

        # 2. Bottom-Left Demonstration Radar Card
        if self.phase in [1, 4] and self.quiz_state == 0:
            card_w, card_h = 336, 110
            card_x = 24
            card_y = self.height - card_h - 20

            # Drop shadow
            sh_rect = pygame.Rect(card_x, card_y + 3, card_w, card_h)
            pygame.draw.rect(self.screen, (0, 0, 0, 160), sh_rect, border_radius=16)

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill((15, 23, 42, 236))
            self.screen.blit(card_surf, (card_x, card_y))
            border_col = (245, 158, 11) if self.phase == 1 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_col, (card_x, card_y, card_w, card_h), 2, border_radius=16)

            # Header with status pill
            t_radar = self.dialog_btn_font.render("GESTURE RADAR", True, border_col)
            self.screen.blit(t_radar, (card_x + 16, card_y + 10))

            status_text = "[HAND DETECTED]" if self.hand_detected else "[GESTURE SCANNING...]"
            status_col = (74, 222, 128) if self.hand_detected else (56, 189, 248)
            stat_surf = self.ui_font.render(status_text, True, status_col)
            self.screen.blit(stat_surf, (card_x + 16, card_y + 34))

            # Gesture steering and action hints
            t_sub1 = self.ui_font.render("- Open Hand: Move away from center to steer", True, (226, 232, 240))
            t_sub2 = self.ui_font.render("- Sprint: Move hand further from center", True, (203, 213, 225))
            t_sub3 = self.ui_font.render("- Action: Hold Closed Fist (0.9s) to interact", True, (251, 191, 36))
            self.screen.blit(t_sub1, (card_x + 16, card_y + 54))
            self.screen.blit(t_sub2, (card_x + 16, card_y + 70))
            self.screen.blit(t_sub3, (card_x + 16, card_y + 86))

            # Right Side: Interactive Joystick Radar Display
            radar_cx = card_x + card_w - 52
            radar_cy = card_y + card_h // 2
            radar_r = 34

            pygame.draw.circle(self.screen, (30, 41, 59), (radar_cx, radar_cy), radar_r)
            pygame.draw.circle(self.screen, border_col, (radar_cx, radar_cy), radar_r, 1)
            # Center deadzone ring
            pygame.draw.circle(self.screen, (51, 65, 85), (radar_cx, radar_cy), 12, 1)
            # Reticle crosshair
            pygame.draw.line(self.screen, (71, 85, 105), (radar_cx - radar_r, radar_cy), (radar_cx + radar_r, radar_cy), 1)
            pygame.draw.line(self.screen, (71, 85, 105), (radar_cx, radar_cy - radar_r), (radar_cx, radar_cy + radar_r), 1)

            # Animated rotating radar sweep line
            sweep_angle = t * 3.5
            sweep_x = radar_cx + math.cos(sweep_angle) * (radar_r - 2)
            sweep_y = radar_cy + math.sin(sweep_angle) * (radar_r - 2)
            pygame.draw.line(self.screen, (*border_col, 180), (radar_cx, radar_cy), (int(sweep_x), int(sweep_y)), 1)

            # Real-time hand offset dot (relative to player on-screen position)
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
        """Draws an animated demonstration over Choice B showing how to hold a fist to click"""
        now = pygame.time.get_ticks()
        box_w, box_h = 600, 390
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        button_w, button_h = 560, 48
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 142
        spacing = 56

        # Choice B is index 1
        target_btn_y = button_y_start + 1 * spacing
        btn_center_x = button_x + button_w - 40
        btn_center_y = target_btn_y + button_h // 2

        # 2.4-second looping cycle
        cycle = (now % 2400) / 2400.0
        hold_charge = min(1.0, cycle * 1.3)

        # Draw animated pulsing hold circle right inside Choice B
        pygame.draw.circle(self.screen, (255, 255, 255), (btn_center_x, btn_center_y), 16, 2)
        if hold_charge > 0.05:
            pygame.draw.circle(self.screen, (251, 191, 36), (btn_center_x, btn_center_y), int(16 * hold_charge))
        pygame.draw.circle(self.screen, (239, 68, 68), (btn_center_x, btn_center_y), 4)

        # Floating tooltip card to the right of Choice B if screen fits
        demo_card_x = box_x + box_w + 16
        demo_card_y = target_btn_y - 24
        if demo_card_x + 210 < self.width:
            d_rect = pygame.Rect(demo_card_x, demo_card_y, 210, 96)
            d_surf = pygame.Surface((210, 96), pygame.SRCALPHA)
            d_surf.fill((15, 23, 42, 240))
            self.screen.blit(d_surf, d_rect)
            pygame.draw.rect(self.screen, (251, 191, 36), d_rect, 2, border_radius=12)

            t1 = self.ui_font.render("HOW TO SELECT:", True, (255, 215, 0))
            t2 = self.ui_font.render("Hold Fist (0.9s) on Choice", True, (255, 255, 255))
            pct = int(hold_charge * 100)
            t3 = self.ui_font.render(f"Charging: {pct}%", True, (254, 240, 138))
            self.screen.blit(t1, (demo_card_x + 12, demo_card_y + 10))
            self.screen.blit(t2, (demo_card_x + 12, demo_card_y + 28))
            self.screen.blit(t3, (demo_card_x + 12, demo_card_y + 46))

            # Progress bar demo in card
            p_bar_rect = pygame.Rect(demo_card_x + 12, demo_card_y + 68, 186, 16)
            pygame.draw.rect(self.screen, (30, 41, 59), p_bar_rect, border_radius=6)
            fill_w = int(186 * hold_charge)
            pygame.draw.rect(self.screen, (251, 191, 36), (demo_card_x + 12, demo_card_y + 68, fill_w, 16), border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), p_bar_rect, 1, border_radius=6)

    # ============================================================
    # TOP VISUAL GAMEPLAY BANNER
    # ============================================================
    def draw_top_banner(self):
        t = pygame.time.get_ticks() * 0.001
        bw = min(680, self.width - 335)
        bh = 58
        bx = 20
        by = 12

        banner_rect = pygame.Rect(bx, by, bw, bh)

        # Drop shadow
        sh_rect = banner_rect.copy()
        sh_rect.y += 3
        pygame.draw.rect(self.screen, (0, 0, 0, 160), sh_rect, border_radius=16)

        # Glassmorphism container
        b_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        b_surf.fill((15, 23, 42, 238))
        self.screen.blit(b_surf, banner_rect.topleft)

        # Pulse accent border
        pulse = 0.5 + 0.5 * math.sin(t * 3.0)
        if self.phase == 1:
            step_tag = "STEP 1/3: NAVIGATION"
            tag_col = (251, 191, 36)
            txt = "Move your open hand away from center to approach the Guide Sage!"
            border_col = (245, 158, 11)
        elif self.phase == 3:
            step_tag = "STEP 2/3: WISDOM TRIAL"
            tag_col = (234, 179, 8)
            txt = "Select your answer by closing and holding a FIST (0.9s) on your choice!"
            border_col = (234, 179, 8)
        else:
            step_tag = "STEP 3/3: PORTAL ODYSSEY"
            tag_col = (74, 222, 128)
            txt = "Exit Portal is active! Walk into the celestial portal to start your journey!"
            border_col = (34, 197, 94)

        pygame.draw.rect(self.screen, border_col, banner_rect, 2, border_radius=16)

        # Step tag badge on left
        tag_surf = self.ui_font.render(step_tag, True, tag_col)
        tw = tag_surf.get_width() + 16
        th = 22
        tag_rect = pygame.Rect(bx + 16, by + 10, tw, th)
        pygame.draw.rect(self.screen, (30, 41, 59), tag_rect, border_radius=6)
        pygame.draw.rect(self.screen, tag_col, tag_rect, 1, border_radius=6)
        self.screen.blit(tag_surf, (tag_rect.x + 8, tag_rect.y + 3))

        # Live pulsing beacon next to tag
        dot_x = tag_rect.right + 14
        dot_y = by + 21
        pygame.draw.circle(self.screen, (34, 197, 94), (dot_x, dot_y), int(4 + 2 * pulse))
        pygame.draw.circle(self.screen, (255, 255, 255), (dot_x, dot_y), 2)

        # Main instructional text
        msg_surf = self.banner_font.render(txt, True, (255, 255, 255))
        self.screen.blit(msg_surf, (bx + 16, by + 34))

    # ============================================================
    # SAMPLE QUIZ MODAL DIALOGS
    # ============================================================
    def draw_sample_quiz_dialog(self):
        box_w, box_h = 600, 390
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Dimmed backdrop
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        # Card shadow
        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=18)

        # Card body
        card_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        card_surf.fill((15, 23, 42, 245))
        self.screen.blit(card_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, (245, 158, 11), (box_x, box_y, box_w, box_h), 2, border_radius=18)

        # Header Bar
        h_w = box_w - 32
        h_h = 44
        h_x = box_x + 16
        h_y = box_y + 14
        h_surf = pygame.Surface((h_w, h_h), pygame.SRCALPHA)
        h_surf.fill((30, 41, 59, 240))
        self.screen.blit(h_surf, (h_x, h_y))
        pygame.draw.rect(self.screen, (251, 191, 36), (h_x, h_y, h_w, h_h), 1, border_radius=10)

        title = self.dialog_header_font.render("Guide Sage - Trial of Wisdom", True, (255, 215, 0))
        self.screen.blit(title, (h_x + 16, h_y + 9))

        # Question text card
        q_card_w = box_w - 32
        q_card_h = 48
        q_card_x = box_x + 16
        q_card_y = box_y + 68
        q_bg = pygame.Surface((q_card_w, q_card_h), pygame.SRCALPHA)
        q_bg.fill((20, 29, 47, 220))
        self.screen.blit(q_bg, (q_card_x, q_card_y))
        pygame.draw.rect(self.screen, (51, 65, 85), (q_card_x, q_card_y, q_card_w, q_card_h), 1, border_radius=8)

        q_txt = self.dialog_q_font.render(self.sample_question["question"], True, (255, 255, 255))
        self.screen.blit(q_txt, (q_card_x + 16, q_card_y + 12))

        # Optional feedback banner
        if self.wrong_feedback_msg:
            fb_surf = self.ui_font.render(self.wrong_feedback_msg, True, (252, 211, 77))
            self.screen.blit(fb_surf, (box_x + 18, box_y + 122))

        # Answer choices
        button_w, button_h = 560, 48
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 142
        spacing = 56

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
            else:
                bg_color = (30, 41, 59)
                text_color = (248, 250, 252)
                border_color = (71, 85, 105)
                badge_bg = (15, 23, 42)
                badge_fg = (251, 191, 36)

            pygame.draw.rect(self.screen, bg_color, btn_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_color, btn_rect, 2 if is_hov else 1, border_radius=10)

            # Letter pill badge
            pill_rect = pygame.Rect(btn_rect.x + 12, btn_rect.y + 10, 34, 28)
            pygame.draw.rect(self.screen, badge_bg, pill_rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, pill_rect, 1, border_radius=6)
            pill_txt = self.ui_font.render(letters[i], True, badge_fg)
            self.screen.blit(pill_txt, pill_txt.get_rect(center=pill_rect.center))

            # Option text
            raw_text = choice_text[3:] if len(choice_text) > 3 and choice_text[1] == '.' else choice_text
            display_text = f"Option {letters[i]}:  {raw_text}" if not is_elim else f"{choice_text}  [ Eliminated ]"
            c_surf = self.dialog_choice_font.render(display_text, True, text_color)
            self.screen.blit(c_surf, (btn_rect.x + 60, btn_rect.y + 13))

    def draw_sample_wrong_dialog(self):
        box_w, box_h = 600, 270
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=18)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=18)
        pygame.draw.rect(self.screen, (239, 68, 68), dialog_rect, 2, border_radius=18)

        # Header
        speaker = self.dialog_header_font.render("Guide Sage - Trial Feedback", True, (248, 113, 113))
        self.screen.blit(speaker, (box_x + 24, box_y + 20))

        # Attempts pill badge
        att_rect = pygame.Rect(box_x + box_w - 210, box_y + 18, 186, 28)
        pygame.draw.rect(self.screen, (30, 41, 59), att_rect, border_radius=6)
        pygame.draw.rect(self.screen, (251, 191, 36), att_rect, 1, border_radius=6)
        att_txt = self.ui_font.render("1 ATTEMPT REMAINING", True, (254, 240, 138))
        self.screen.blit(att_txt, att_txt.get_rect(center=att_rect.center))

        m1 = self.dialog_q_font.render("Hmm, that is not the right answer.", True, (255, 255, 255))
        m2 = self.dialog_choice_font.render("In your quest, you get 2 attempts per trial to prove your wisdom.", True, (203, 213, 225))
        self.screen.blit(m1, (box_x + 24, box_y + 75))
        self.screen.blit(m2, (box_x + 24, box_y + 110))

        btn_rect = pygame.Rect(box_x + (box_w - 230) // 2, box_y + 180, 230, 48)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if is_hov else (153, 27, 27), btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Try Again", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_sample_correct_dialog(self):
        box_w, box_h = 600, 280
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.screen.blit(dim, (0, 0))

        sh_rect = pygame.Rect(box_x, box_y + 4, box_w, box_h)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), sh_rect, border_radius=18)

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=18)
        pygame.draw.rect(self.screen, (34, 197, 94), dialog_rect, 2, border_radius=18)

        speaker = self.dialog_header_font.render("Guide Sage - Trial Mastered!", True, (74, 222, 128))
        self.screen.blit(speaker, (box_x + 24, box_y + 20))

        # Golden stars / medal badges drawn geometrically
        for s_i in range(3):
            sc_x = box_x + box_w - 85 + s_i * 22
            sc_y = box_y + 32
            pygame.draw.circle(self.screen, (251, 191, 36), (sc_x, sc_y), 7)
            pygame.draw.circle(self.screen, (254, 240, 138), (sc_x, sc_y), 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (sc_x, sc_y), 7, 1)

        m1 = self.dialog_q_font.render("Outstanding! 2 + 2 = 4 is correct!", True, (255, 255, 255))
        m2 = self.dialog_choice_font.render("The mystical Exit Portal has materialized on the path ahead.", True, (203, 213, 225))
        m3 = self.ui_font.render("Step through the glowing portal to embark on your cognitive quest!", True, (254, 240, 138))
        self.screen.blit(m1, (box_x + 24, box_y + 70))
        self.screen.blit(m2, (box_x + 24, box_y + 105))
        self.screen.blit(m3, (box_x + 24, box_y + 135))

        btn_rect = pygame.Rect(box_x + (box_w - 240) // 2, box_y + 195, 240, 48)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (34, 197, 94) if is_hov else (22, 101, 52), btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Continue >>", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

