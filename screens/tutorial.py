# screens/tutorial.py - Live Interactive Gameplay Showcase Tutorial
import pygame
import os
import sys
import math
import time
import cv2
import numpy as np

TILE_SIZE = 32
ZOOM = 1.50
SPEED = 4.5

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
                    print(f"🌀 Tutorial Exit Portal ('r') mapped at tile: ({c_idx}, {r_idx})")

        self.portal_anim_frame = 0
        self.portal_anim_timer = 0

        # Camera
        self.camera_x = 0
        self.camera_y = 0

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

        print("🎓 Live Interactive Gameplay Tutorial Initialized!")

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
                    print(f"✅ Loaded tutorial map from: {self.map_path} ({len(lines)}x{len(lines[0])})")
                    return lines
            except Exception as e:
                print(f"⚠️ Error reading tutorial map file: {e}")

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
            'G': "grass1.png",
            'P': "pathway1.png",
            'r': "pathway1.png",
            'T': "tree.png",
            '#': "wall.png"
        }
        for key, filename in tile_map.items():
            path = os.path.join(self.OBJECTS_PATH, filename)
            try:
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    tiles[key] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                else:
                    p = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    p.fill((34, 197, 94) if key == 'G' else ((180, 83, 9) if key == 'P' else (22, 101, 52)))
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
                print(f"⚠️ Error loading tutorial portal frame {filename}: {e}")

        if not frames:
            p = pygame.Surface((TILE_SIZE * 3, TILE_SIZE * 3), pygame.SRCALPHA)
            pygame.draw.circle(p, (74, 222, 128), (TILE_SIZE * 3 // 2, TILE_SIZE * 3 // 2), TILE_SIZE * 3 // 2)
            frames.append(p)
        else:
            print(f"✅ Loaded {len(frames)} portal animation frames for Tutorial!")
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
        # Update camera
        target_cam_x = self.player_x - (self.width / ZOOM) / 2
        target_cam_y = self.player_y - (self.height / ZOOM) / 2
        self.camera_x += (target_cam_x - self.camera_x) * 0.1
        self.camera_y += (target_cam_y - self.camera_y) * 0.1

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
            print("🎓 Player approached Guide NPC: Automatically Triggered Question Dialogue!")

        if self.phase == 4 and portal_dist < 1.8 * TILE_SIZE:
            print("🎉 Exit Portal Entered! Tutorial Complete!")
            self.finish_tutorial()

    def update_player_movement(self):
        vx, vy = 0, 0
        current_speed = SPEED

        # Pure Gesture Steering
        center_x, center_y = self.width // 2, self.height // 2
        cursor_x, cursor_y = self.cursor_pos
        dx = cursor_x - center_x
        dy = cursor_y - center_y

        dist_factor = 1.3 if (abs(dx) > 160 or abs(dy) > 160) else 1.0
        g_speed = current_speed * dist_factor

        if abs(dx) > 45:
            vx = g_speed if dx > 0 else -g_speed
            self.player_dir = "right" if dx > 0 else "left"

        if abs(dy) > 45:
            vy = g_speed if dy > 0 else -g_speed
            self.player_dir = "down" if dy > 0 else "up"

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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.trigger_click(event.pos)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.finish_tutorial()

    def trigger_click(self, pos=None):
        if pos is None:
            pos = self.cursor_pos

        # 1. Skip Button (Top Right)
        skip_rect = pygame.Rect(self.width - 220, 20, 200, 46)
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
                print("🎓 Opening Sample Quiz Modal!")
                return

        # 3. Phase 3: Sample Quiz Dialog Clicks
        if self.quiz_state == 1:
            box_w, box_h = 580, 380
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            button_w, button_h = 500, 44
            button_x = box_x + (box_w - button_w) // 2
            button_y_start = box_y + 130
            spacing = 52

            for i in range(4):
                if i == self.eliminated_choice:
                    continue
                btn_rect = pygame.Rect(button_x, button_y_start + i * spacing, button_w, button_h)
                if btn_rect.collidepoint(pos):
                    if i == self.sample_question["correct"]:
                        self.quiz_state = 3 # Correct
                        print("✅ Correct Answer in Tutorial Quiz!")
                    else:
                        self.quiz_attempts += 1
                        self.eliminated_choice = i
                        self.wrong_feedback_msg = "Almost! You have 1 try remaining. Pick again! ⭐"
                        self.quiz_state = 2 if self.quiz_attempts < 2 else 3
                        print("❌ Wrong Answer in Tutorial Quiz -> Showing 2-Attempt Mechanics!")
                    return

        # Retry / Continue Dialog Clicks
        elif self.quiz_state == 2:
            box_w, box_h = 580, 260
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 180, 220, 46)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 1
                return

        elif self.quiz_state == 3:
            box_w, box_h = 580, 260
            box_x = (self.width - box_w) // 2
            box_y = (self.height - box_h) // 2
            btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 175, 220, 46)
            if btn_rect.collidepoint(pos):
                self.quiz_state = 0
                self.phase = 4
                print("🎓 Tutorial Phase 4: Portal Unlocked! Guide student to Exit Portal.")
                return

    def finish_tutorial(self):
        from db.save_system import set_tutorial_completed
        student_id = getattr(self.main_menu, 'student_id', None)
        if student_id:
            set_tutorial_completed(self.main_menu, student_id, completed=True)

        print("🚀 Tutorial Complete! Opening Stage Select...")
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

        # 8. Prominent Skip Button
        skip_rect = pygame.Rect(self.width - 220, 20, 200, 46)
        skip_hov = skip_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if skip_hov else (30, 41, 59), skip_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 215, 0) if skip_hov else (203, 213, 225), skip_rect, 2, border_radius=12)
        skip_txt = self.skip_font.render("SKIP TUTORIAL >>", True, (255, 255, 255))
        self.screen.blit(skip_txt, skip_txt.get_rect(center=skip_rect.center))

        # 9. Render Quiz Modal Dialogs
        if self.quiz_state == 1:
            self.draw_sample_quiz_dialog()
            self.draw_quiz_gesture_demo()
        elif self.quiz_state == 2:
            self.draw_sample_wrong_dialog()
        elif self.quiz_state == 3:
            self.draw_sample_correct_dialog()

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

        # 1. In-World Animated Guide Trail (Floor Chevrons)
        if self.phase == 1:
            pl_sx = (self.player_x - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
            pl_sy = (self.player_y - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2
            npc_sx = (self.npc_tile_x * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
            npc_sy = (self.npc_tile_y * TILE_SIZE - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2

            # Only draw if player is to the left of the NPC
            if npc_sx > pl_sx + 20:
                step = 36 * ZOOM
                offset = (now * 0.04) % step
                cur_x = pl_sx + offset
                while cur_x < npc_sx - 20:
                    pulse_r = int((4 + math.sin(now * 0.01 + cur_x * 0.1) * 1.5) * ZOOM)
                    p1 = (cur_x - 6 * ZOOM, pl_sy - 8 * ZOOM)
                    p2 = (cur_x + 4 * ZOOM, pl_sy)
                    p3 = (cur_x - 6 * ZOOM, pl_sy + 8 * ZOOM)
                    pygame.draw.lines(self.screen, (255, 215, 0), False, [p1, p2, p3], 3)
                    pygame.draw.circle(self.screen, (254, 240, 138), (int(cur_x), int(pl_sy)), pulse_r)
                    cur_x += step

        elif self.phase == 4:
            pl_sx = (self.player_x - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
            pl_sy = (self.player_y - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2
            p_sx = (self.portal_tile_x * TILE_SIZE - self.camera_x) * ZOOM + (TILE_SIZE * ZOOM) / 2
            p_sy = (self.portal_tile_y * TILE_SIZE - self.camera_y) * ZOOM + (TILE_SIZE * ZOOM) / 2

            if p_sx > pl_sx + 20:
                step = 36 * ZOOM
                offset = (now * 0.04) % step
                cur_x = pl_sx + offset
                while cur_x < p_sx - 20:
                    pulse_r = int((4 + math.sin(now * 0.01 + cur_x * 0.1) * 1.5) * ZOOM)
                    p1 = (cur_x - 6 * ZOOM, pl_sy - 8 * ZOOM)
                    p2 = (cur_x + 4 * ZOOM, pl_sy)
                    p3 = (cur_x - 6 * ZOOM, pl_sy + 8 * ZOOM)
                    pygame.draw.lines(self.screen, (74, 222, 128), False, [p1, p2, p3], 3)
                    pygame.draw.circle(self.screen, (187, 247, 208), (int(cur_x), int(pl_sy)), pulse_r)
                    cur_x += step

        # 2. Bottom-Left Demonstration HUD Card
        if self.phase in [1, 4] and self.quiz_state == 0:
            card_w, card_h = 320, 100
            card_x = 30
            card_y = self.height - card_h - 24

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill((15, 23, 42, 230))
            self.screen.blit(card_surf, (card_x, card_y))
            border_col = (245, 158, 11) if self.phase == 1 else (34, 197, 94)
            pygame.draw.rect(self.screen, border_col, (card_x, card_y, card_w, card_h), 2, border_radius=12)

            # Text instructions
            if self.phase == 1:
                t1 = self.dialog_btn_font.render("🖐️ STEERING DEMO", True, (255, 215, 0))
                t2 = self.ui_font.render("Move hand away from center", True, (255, 255, 255))
                t3 = self.ui_font.render("towards the Guide NPC ➡️", True, (203, 213, 225))
            else:
                t1 = self.dialog_btn_font.render("🌀 PORTAL UNLOCKED", True, (74, 222, 128))
                t2 = self.ui_font.render("Walk into the glowing Exit Portal", True, (255, 255, 255))
                t3 = self.ui_font.render("to enter Stage Select ➡️", True, (203, 213, 225))

            self.screen.blit(t1, (card_x + 14, card_y + 12))
            self.screen.blit(t2, (card_x + 14, card_y + 44))
            self.screen.blit(t3, (card_x + 14, card_y + 68))

            # Right Side: Animated Hand Motion Demo Sub-panel
            sub_cx = card_x + card_w - 50
            sub_cy = card_y + card_h // 2
            pygame.draw.circle(self.screen, (30, 41, 59), (sub_cx, sub_cy), 32)
            pygame.draw.circle(self.screen, border_col, (sub_cx, sub_cy), 32, 1)

            # Center target crosshair
            pygame.draw.circle(self.screen, (71, 85, 105), (sub_cx, sub_cy), 6)

            # Animated hand moving right
            hand_slide = (math.sin(now * 0.005) + 1) / 2 # 0.0 to 1.0
            animated_hand_x = sub_cx - 15 + hand_slide * 30
            # Draw moving hand cursor
            pygame.draw.line(self.screen, border_col, (sub_cx - 10, sub_cy), (int(animated_hand_x), sub_cy), 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(animated_hand_x), sub_cy), 10)
            pygame.draw.circle(self.screen, border_col, (int(animated_hand_x), sub_cy), 10, 2)
            h_lbl = self.ui_font.render("🖐️", True, (0, 0, 0))
            self.screen.blit(h_lbl, h_lbl.get_rect(center=(int(animated_hand_x), sub_cy)))

    def draw_quiz_gesture_demo(self):
        """Draws an animated demonstration over Choice B showing how to hold a fist to click"""
        now = pygame.time.get_ticks()
        box_w, box_h = 580, 380
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        button_w, button_h = 500, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 130
        spacing = 52

        # Choice B is index 1
        target_btn_y = button_y_start + 1 * spacing
        btn_center_x = button_x + button_w - 45
        btn_center_y = target_btn_y + button_h // 2

        # 2.4-second looping cycle
        cycle = (now % 2400) / 2400.0 # 0.0 to 1.0

        demo_card_x = box_x + box_w + 16
        demo_card_y = target_btn_y - 20
        if demo_card_x + 200 < self.width:
            d_rect = pygame.Rect(demo_card_x, demo_card_y, 200, 90)
            d_surf = pygame.Surface((200, 90), pygame.SRCALPHA)
            d_surf.fill((15, 23, 42, 230))
            self.screen.blit(d_surf, d_rect)
            pygame.draw.rect(self.screen, (251, 191, 36), d_rect, 2, border_radius=10)

            t1 = self.ui_font.render("✊ HOW TO SELECT:", True, (255, 215, 0))
            t2 = self.ui_font.render("Hold Fist (0.9s)", True, (255, 255, 255))
            self.screen.blit(t1, (demo_card_x + 10, demo_card_y + 10))
            self.screen.blit(t2, (demo_card_x + 10, demo_card_y + 32))

            # Progress bar demo in card
            p_bar_rect = pygame.Rect(demo_card_x + 10, demo_card_y + 58, 180, 16)
            pygame.draw.rect(self.screen, (30, 41, 59), p_bar_rect, border_radius=6)
            fill_w = int(180 * min(1.0, cycle * 1.3))
            pygame.draw.rect(self.screen, (255, 215, 0), (demo_card_x + 10, demo_card_y + 58, fill_w, 16), border_radius=6)
            pygame.draw.rect(self.screen, (255, 255, 255), p_bar_rect, 1, border_radius=6)

        # Draw animated pulsing fist icon right on Choice B
        hold_charge = min(1.0, cycle * 1.3)
        pygame.draw.circle(self.screen, (255, 255, 255), (btn_center_x, btn_center_y), 18, 2)
        if hold_charge > 0.1:
            pygame.draw.circle(self.screen, (255, 215, 0), (btn_center_x, btn_center_y), int(18 * hold_charge))
        icon_txt = "✊" if hold_charge > 0.2 else "🖐️"
        f_surf = self.ui_font.render(icon_txt, True, (0, 0, 0) if hold_charge > 0.5 else (255, 255, 255))
        self.screen.blit(f_surf, f_surf.get_rect(center=(btn_center_x, btn_center_y)))

    # ============================================================
    # TOP VISUAL GAMEPLAY BANNER
    # ============================================================
    def draw_top_banner(self):
        bw, bh = min(720, self.width - 260), 56
        bx = 30
        by = 16

        banner_rect = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(self.screen, (15, 23, 42), banner_rect, border_radius=14)
        pygame.draw.rect(self.screen, (245, 158, 11), banner_rect, 2, border_radius=14)

        if self.phase == 1:
            txt = "🖐️ Move your hand in front of the camera to walk close to the Guide NPC!"
            color = (255, 215, 0)
        elif self.phase == 3:
            txt = "⭐ Select your choice by holding a FIST (0.9s) over the answer!"
            color = (251, 191, 36)
        else:
            txt = "🌀 Exit Portal open! Walk into the glowing portal to start your adventure!"
            color = (74, 222, 128)

        msg_surf = self.banner_font.render(txt, True, color)
        self.screen.blit(msg_surf, msg_surf.get_rect(center=banner_rect.center))

    # ============================================================
    # SAMPLE QUIZ MODAL DIALOGS
    # ============================================================
    def draw_sample_quiz_dialog(self):
        box_w, box_h = 580, 380
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=16)
        pygame.draw.rect(self.screen, (245, 158, 11), dialog_rect, 3, border_radius=16)

        header_surf = pygame.Surface((box_w - 36, 40), pygame.SRCALPHA)
        header_surf.fill((30, 41, 59, 230))
        self.screen.blit(header_surf, (box_x + 18, box_y + 12))
        pygame.draw.rect(self.screen, (245, 158, 11), (box_x + 18, box_y + 12, box_w - 36, 40), 1, border_radius=8)

        title = self.dialog_header_font.render("Guide Sage • Tutorial Question", True, (255, 215, 0))
        self.screen.blit(title, (box_x + 30, box_y + 18))

        q_txt = self.dialog_q_font.render(self.sample_question["question"], True, (255, 255, 255))
        self.screen.blit(q_txt, (box_x + 30, box_y + 70))

        if self.wrong_feedback_msg:
            fb_surf = self.ui_font.render(self.wrong_feedback_msg, True, (252, 211, 77))
            self.screen.blit(fb_surf, (box_x + 30, box_y + 98))

        button_w, button_h = 500, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 130
        spacing = 52

        for i, choice_text in enumerate(self.sample_question["choices"]):
            b_y = button_y_start + i * spacing
            btn_rect = pygame.Rect(button_x, b_y, button_w, button_h)
            is_elim = (i == self.eliminated_choice)
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
            self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_sample_wrong_dialog(self):
        box_w, box_h = 580, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (220, 38, 38), dialog_rect, 3, border_radius=14)

        speaker = self.dialog_header_font.render("Guide Sage", True, (239, 68, 68))
        self.screen.blit(speaker, (box_x + 25, box_y + 20))

        m1 = self.dialog_q_font.render("Hmm, that is not correct.", True, (255, 255, 255))
        m2 = self.dialog_choice_font.render("You have 1 try remaining! Think carefully and try again. ⭐", True, (253, 230, 138))
        self.screen.blit(m1, (box_x + 25, box_y + 75))
        self.screen.blit(m2, (box_x + 25, box_y + 110))

        btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 180, 220, 46)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if is_hov else (153, 27, 27), btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Try Again", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))

    def draw_sample_correct_dialog(self):
        box_w, box_h = 580, 260
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))

        dialog_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), dialog_rect, border_radius=14)
        pygame.draw.rect(self.screen, (22, 163, 74), dialog_rect, 3, border_radius=14)

        speaker = self.dialog_header_font.render("Guide Sage", True, (22, 163, 74))
        self.screen.blit(speaker, (box_x + 25, box_y + 20))

        m1 = self.dialog_q_font.render("Outstanding! That is correct!", True, (255, 255, 255))
        m2 = self.dialog_choice_font.render("The Exit Portal has been unlocked. Step through to begin! ⭐", True, (253, 230, 138))
        self.screen.blit(m1, (box_x + 25, box_y + 75))
        self.screen.blit(m2, (box_x + 25, box_y + 110))

        btn_rect = pygame.Rect(box_x + (box_w - 220) // 2, box_y + 175, 220, 46)
        is_hov = btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (34, 197, 94) if is_hov else (30, 41, 59), btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255), btn_rect, 2, border_radius=12)

        c_surf = self.dialog_btn_font.render("Continue >>", True, (255, 255, 255))
        self.screen.blit(c_surf, c_surf.get_rect(center=btn_rect.center))
