# core/minimap.py
"""
High-Performance Zero-Allocation Tactical Mini-Map & Radar Engine.
Specially engineered for 60 FPS on AMD A4-6300 APU (1MB L2 cache, dual-core):
- Pre-bakes the full terrain layout into a hardware-accelerated surface during level load.
- Performs zero per-frame surface creations or garbage collection allocations in draw loop.
- Renders player beacon, quest objectives, camera frustum, and stage portals with native vector primitives.
- Interactive and toggleable with [M] key or mouse / fist click on the radar widget.
"""

import math
import time
import pygame
from core.font_manager import get_font


class MiniMap:
    """
    Tactical Mini-Map HUD component for Cognitive Quest 2D.
    Works universally across Hub World (StageSelect) and All Quarters (Q1-Q4).
    """

    def __init__(
        self,
        game_map,
        walkable_tiles=None,
        tile_size=32,
        screen_width=1280,
        screen_height=720,
        width=280,
        height=180,
        theme="sanctuary",
        position="bottom_right",
        margin_y=None,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size
        self.theme = theme
        self.position = position
        self.margin_y_custom = margin_y

        # Map dimensions
        self.game_map = game_map or []
        self.map_rows = max(1, len(self.game_map))
        self.map_cols = max(1, max(len(r) for r in self.game_map)) if self.game_map else 1
        self.world_w = self.map_cols * self.tile_size
        self.world_h = self.map_rows * self.tile_size

        self.walkable_tiles = set(walkable_tiles) if walkable_tiles else {"G", "#", "P"}

        # Widget Geometry (Outer Container)
        self.width = width
        self.height = height
        self.visible = True  # Expanded by default

        self._calc_positions()

        # Inner Map Display Geometry (Aspect-Ratio Preserving)
        pad_x = 12
        pad_top = 28
        pad_bot = 10
        avail_w = self.width - pad_x * 2
        avail_h = self.height - pad_top - pad_bot

        map_aspect = self.map_cols / float(self.map_rows)
        box_aspect = avail_w / float(avail_h)

        if map_aspect >= box_aspect:
            self.inner_w = avail_w
            self.inner_h = max(24, int(avail_w / map_aspect))
        else:
            self.inner_h = avail_h
            self.inner_w = max(32, int(avail_h * map_aspect))

        self.inner_x_offset = pad_x + (avail_w - self.inner_w) // 2
        self.inner_y_offset = pad_top + (avail_h - self.inner_h) // 2

        # Pre-bake Static Surfaces
        self._bake_base_map()
        self._bake_frame_surfaces()
        self._init_badge_cache()

    def _calc_positions(self):
        """Calculates placement coordinates for the expanded card and minimized pill."""
        margin_x = 20
        margin_y = self.margin_y_custom if self.margin_y_custom is not None else 18

        if self.position == "bottom_right":
            self.container_x = self.screen_width - self.width - margin_x
            self.container_y = self.screen_height - self.height - margin_y
        elif self.position == "top_right":
            self.container_x = self.screen_width - self.width - margin_x
            self.container_y = margin_y
        else:
            self.container_x = self.screen_width - self.width - margin_x
            self.container_y = self.screen_height - self.height - margin_y

        self.container_rect = pygame.Rect(
            self.container_x, self.container_y, self.width, self.height
        )

        # Minimized Pill Rect
        self.pill_w = 124
        self.pill_h = 32
        self.pill_x = self.screen_width - self.pill_w - margin_x
        self.pill_y = self.screen_height - self.pill_h - margin_y
        self.pill_rect = pygame.Rect(self.pill_x, self.pill_y, self.pill_w, self.pill_h)

    def _bake_base_map(self):
        """Pre-renders the static terrain into an optimized hardware surface once."""
        surf = pygame.Surface((self.inner_w, self.inner_h), pygame.SRCALPHA)
        # Deep space background for non-walkable bounds
        surf.fill((15, 23, 42, 255))

        col_w = self.inner_w / float(self.map_cols)
        row_h = self.inner_h / float(self.map_rows)

        # Theme color palettes
        if self.theme == "desert" or self.theme == "quarter3":
            walk_color = (217, 119, 6)      # Warm Amber Stone
            hazard_color = (180, 83, 9)     # Quicksand
            wall_color = (69, 26, 3)        # Canyons
        elif self.theme == "water" or self.theme == "quarter4":
            walk_color = (14, 116, 144)     # Aqua Tiles
            hazard_color = (3, 105, 161)    # Deep Waters
            wall_color = (12, 74, 110)      # Aqueduct Walls
        elif self.theme == "kalye" or self.theme == "quarter2":
            walk_color = (100, 116, 139)    # Cobblestone Street
            hazard_color = (51, 65, 85)     # Buildings
            wall_color = (30, 41, 59)       # Rooftops
        else:
            # Sanctuary / Forest (Default)
            walk_color = (51, 65, 85)       # Slate Sanctuary Pathways
            hazard_color = (14, 116, 144)   # Water Moat
            wall_color = (30, 41, 59)       # Ancient Forest Trees

        # Render terrain blocks
        for r_idx in range(self.map_rows):
            if r_idx >= len(self.game_map):
                break
            row_str = self.game_map[r_idx]
            for c_idx in range(len(row_str)):
                tile = row_str[c_idx]
                bx = int(c_idx * col_w)
                by = int(r_idx * row_h)
                bw = max(1, int(math.ceil(col_w)))
                bh = max(1, int(math.ceil(row_h)))

                if tile in self.walkable_tiles:
                    pygame.draw.rect(surf, walk_color, (bx, by, bw, bh))
                elif tile in ('/', '~', 'w', 'W'):
                    pygame.draw.rect(surf, hazard_color, (bx, by, bw, bh))
                elif tile in ('T', '0', 'X', 'B', 'K', 'S', 'O'):
                    pygame.draw.rect(surf, wall_color, (bx, by, bw, bh))

        # Thin inner grid border
        pygame.draw.rect(surf, (71, 85, 105), (0, 0, self.inner_w, self.inner_h), 1)

        try:
            self._base_map_surf = surf.convert_alpha()
        except Exception:
            self._base_map_surf = surf

    def _bake_frame_surfaces(self):
        """Pre-renders frame containers for both expanded and minimized states."""
        # 1. Expanded Frame Surface
        exp_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        exp_surf.fill((15, 23, 42, 235))  # Midnight slate
        pygame.draw.rect(exp_surf, (251, 191, 36), (0, 0, self.width, self.height), 2, border_radius=12)

        # Header Banner Accent
        hdr_rect = pygame.Rect(0, 0, self.width, 24)
        pygame.draw.rect(exp_surf, (30, 41, 59, 240), hdr_rect, border_top_left_radius=12, border_top_right_radius=12)
        pygame.draw.line(exp_surf, (71, 85, 105), (0, 24), (self.width, 24), 1)

        # Header Title Text
        font = get_font("Comic Sans MS", 13, bold=True)
        txt = font.render("RADAR MAP [M]", True, (241, 245, 249))
        exp_surf.blit(txt, (12, 3))

        # Header Minimize Icon [_]
        pygame.draw.line(exp_surf, (148, 163, 184), (self.width - 24, 13), (self.width - 12, 13), 2)

        try:
            self._frame_surf = exp_surf.convert_alpha()
        except Exception:
            self._frame_surf = exp_surf

        # 2. Minimized Pill Surface
        pill_surf = pygame.Surface((self.pill_w, self.pill_h), pygame.SRCALPHA)
        pill_surf.fill((15, 23, 42, 230))
        pygame.draw.rect(pill_surf, (251, 191, 36), (0, 0, self.pill_w, self.pill_h), 2, border_radius=14)

        font_sm = get_font("Comic Sans MS", 13, bold=True)
        p_txt = font_sm.render("MAP [M]", True, (241, 245, 249))
        pill_surf.blit(p_txt, ((self.pill_w - p_txt.get_width()) // 2 + 6, 6))

        # Compass dot on pill
        pygame.draw.circle(pill_surf, (56, 189, 248), (16, self.pill_h // 2), 5)

        try:
            self._pill_surf = pill_surf.convert_alpha()
        except Exception:
            self._pill_surf = pill_surf

    def _init_badge_cache(self):
        """
        Pre-bakes high-contrast solid badge surfaces for minimap markers.
        Avoids per-frame allocations and font rasterizations in the draw loop,
        critical for the AMD A4-6300 dual-core target hardware budget.
        """
        self._badge_cache = {}
        font_num = get_font("Arial", 10, bold=True)
        font_npc = get_font("Arial", 11, bold=True)

        # 1. Active Question Station Badges (Pulsing Gold backing with dark number)
        for num in range(1, 16):
            surf = pygame.Surface((18, 18), pygame.SRCALPHA)
            pygame.draw.circle(surf, (15, 23, 42), (9, 9), 8)
            pygame.draw.circle(surf, (250, 204, 21), (9, 9), 7)
            txt = font_num.render(str(num), True, (15, 23, 42))
            surf.blit(txt, ((18 - txt.get_width()) // 2, (18 - txt.get_height()) // 2))
            try:
                self._badge_cache[("active", str(num))] = surf.convert_alpha()
            except Exception:
                self._badge_cache[("active", str(num))] = surf

        # Active default '?'
        surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(surf, (15, 23, 42), (9, 9), 8)
        pygame.draw.circle(surf, (250, 204, 21), (9, 9), 7)
        txt = font_num.render("?", True, (15, 23, 42))
        surf.blit(txt, ((18 - txt.get_width()) // 2, (18 - txt.get_height()) // 2))
        try:
            self._badge_cache[("active", "?")] = surf.convert_alpha()
        except Exception:
            self._badge_cache[("active", "?")] = surf

        # 2. Upcoming Question Station Badges (Vibrant Amber/Orange backing with dark number)
        for num in range(1, 16):
            surf = pygame.Surface((18, 18), pygame.SRCALPHA)
            pygame.draw.circle(surf, (15, 23, 42), (9, 9), 8)
            pygame.draw.circle(surf, (251, 146, 60), (9, 9), 7)
            txt = font_num.render(str(num), True, (15, 23, 42))
            surf.blit(txt, ((18 - txt.get_width()) // 2, (18 - txt.get_height()) // 2))
            try:
                self._badge_cache[("upcoming", str(num))] = surf.convert_alpha()
            except Exception:
                self._badge_cache[("upcoming", str(num))] = surf

        # Upcoming default '?'
        surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(surf, (15, 23, 42), (9, 9), 8)
        pygame.draw.circle(surf, (251, 146, 60), (9, 9), 7)
        txt = font_num.render("?", True, (15, 23, 42))
        surf.blit(txt, ((18 - txt.get_width()) // 2, (18 - txt.get_height()) // 2))
        try:
            self._badge_cache[("upcoming", "?")] = surf.convert_alpha()
        except Exception:
            self._badge_cache[("upcoming", "?")] = surf

        # 3. Completed Station Badges (Emerald Green with crisp white checkmark vector)
        surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(surf, (15, 23, 42), (9, 9), 8)
        pygame.draw.circle(surf, (34, 197, 94), (9, 9), 7)
        pygame.draw.lines(surf, (255, 255, 255), False, [(5, 9), (8, 12), (13, 6)], 2)
        try:
            comp_surf = surf.convert_alpha()
        except Exception:
            comp_surf = surf
        self._badge_cache[("completed", "✓")] = comp_surf
        self._badge_cache[("completed", "check")] = comp_surf
        self._badge_cache[("completed", "")] = comp_surf

        # 4. NPC / Mentor Story Badges (Rose Red with bold white '!')
        surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(surf, (15, 23, 42), (9, 9), 8)
        pygame.draw.circle(surf, (244, 63, 94), (9, 9), 7)
        txt = font_npc.render("!", True, (255, 255, 255))
        surf.blit(txt, ((18 - txt.get_width()) // 2, (18 - txt.get_height()) // 2))
        try:
            npc_surf = surf.convert_alpha()
        except Exception:
            npc_surf = surf
        self._badge_cache[("npc", "!")] = npc_surf
        self._badge_cache[("npc", "?")] = npc_surf
        self._badge_cache[("npc", "")] = npc_surf

    def toggle(self):
        """Toggles mini-map between expanded radar and compact pill."""
        self.visible = not self.visible
        return self.visible

    def handle_event(self, event):
        """Handles keyboard and click toggles. Returns True if event consumed."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.toggle()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_click(event.pos)
        return False

    def handle_click(self, pos):
        """Detects clicks on the mini-map widget to toggle expanded/minimized."""
        if not pos or not isinstance(pos, (tuple, list)) or len(pos) < 2:
            return False

        if self.visible:
            if self.container_rect.collidepoint(pos):
                self.toggle()
                return True
        else:
            if self.pill_rect.collidepoint(pos):
                self.toggle()
                return True
        return False

    def world_to_map(self, wx, wy):
        """Converts in-game world coordinates to mini-map pixel coordinates."""
        if self.world_w <= 0 or self.world_h <= 0:
            return 0, 0
        norm_x = max(0.0, min(1.0, wx / float(self.world_w)))
        norm_y = max(0.0, min(1.0, wy / float(self.world_h)))

        mx = self.container_x + self.inner_x_offset + int(norm_x * self.inner_w)
        my = self.container_y + self.inner_y_offset + int(norm_y * self.inner_h)
        return mx, my

    def draw(
        self,
        surface,
        player_pos,
        camera_pos=None,
        zoom=1.5,
        markers=None,
        cursor_pos=None,
        hold_pct=0.0,
    ):
        """
        Draws the radar mini-map with real-time zero-allocation vector overlays.
        """
        t = time.time()
        pulse = 0.5 + 0.5 * math.sin(t * 6.0)

        # ============================================================
        # 1. MINIMIZED STATE: Compact Pill
        # ============================================================
        if not self.visible:
            surface.blit(self._pill_surf, (self.pill_x, self.pill_y))

            # Pulsing compass gem
            cx = self.pill_x + 14
            cy = self.pill_y + self.pill_h // 2
            pygame.draw.circle(surface, (250, 204, 21), (cx, cy), int(3 + pulse * 1.5))

            # Fist charge feedback on pill if hovered
            if cursor_pos and self.pill_rect.collidepoint(cursor_pos) and hold_pct > 0.05:
                charge_w = int((self.pill_w - 12) * hold_pct)
                pygame.draw.rect(
                    surface,
                    (250, 204, 21),
                    (self.pill_x + 6, self.pill_y + self.pill_h - 4, charge_w, 2),
                    border_radius=1,
                )
            return

        # ============================================================
        # 2. EXPANDED RADAR STATE
        # ============================================================
        # Base container & baked terrain
        surface.blit(self._frame_surf, (self.container_x, self.container_y))
        map_draw_x = self.container_x + self.inner_x_offset
        map_draw_y = self.container_y + self.inner_y_offset
        surface.blit(self._base_map_surf, (map_draw_x, map_draw_y))

        # Camera Viewport Wireframe Frustum
        if camera_pos:
            cam_x, cam_y = camera_pos
            view_w = self.screen_width / float(zoom)
            view_h = self.screen_height / float(zoom)

            vx1, vy1 = self.world_to_map(cam_x, cam_y)
            vx2, vy2 = self.world_to_map(cam_x + view_w, cam_y + view_h)

            vw = max(4, vx2 - vx1)
            vh = max(4, vy2 - vy1)

            # Clamp viewport box within map display area
            box_rect = pygame.Rect(vx1, vy1, vw, vh)
            clip_rect = pygame.Rect(map_draw_x, map_draw_y, self.inner_w, self.inner_h)
            clamped = box_rect.clip(clip_rect)

            if clamped.width > 0 and clamped.height > 0:
                pygame.draw.rect(surface, (254, 240, 138), clamped, 1)

        # Draw In-Game Objective & Portal Markers
        if markers:
            for m in markers:
                mx, my = self.world_to_map(m.get("x", 0), m.get("y", 0))
                mtype = m.get("type", "station")
                status = m.get("status", "active")
                col = m.get("color", (250, 204, 21))

                if mtype == "goal":
                    # Exit Portal: Shining Star
                    r = int(6 + pulse * 2.5)
                    pygame.draw.circle(surface, (56, 189, 248), (mx, my), r)
                    pygame.draw.circle(surface, (255, 255, 255), (mx, my), 3)
                elif mtype == "portal":
                    # Wing portal
                    if status == "unlocked" or status == "completed":
                        p_col = (34, 197, 94)  # Emerald Green
                    elif status == "active":
                        p_col = (250, 204, 21)  # Pulsing Gold
                    else:
                        p_col = (100, 116, 139) # Locked Slate
                    pygame.draw.circle(surface, p_col, (mx, my), 5)
                    pygame.draw.circle(surface, (255, 255, 255), (mx, my), 2)
                elif mtype == "npc":
                    # Story / Mentor NPC (Old Man, Bromen, Skeleton, Knight)
                    badge = self._badge_cache.get(("npc", "!"))
                    if badge:
                        surface.blit(badge, (mx - 9, my - 9))
                    else:
                        pygame.draw.circle(surface, (244, 63, 94), (mx, my), 6)
                else:
                    # Quiz / Question Station (1-10)
                    label = str(m.get("label", m.get("num", "")))
                    if status == "active":
                        # Current Target: Radiant glowing beacon ring + solid gold numbered badge
                        r_glow = int(10.0 + pulse * 3.5)
                        pygame.draw.circle(surface, (250, 204, 21), (mx, my), r_glow, 1)
                        badge = self._badge_cache.get(("active", label)) or self._badge_cache.get(("active", "?"))
                        if badge:
                            surface.blit(badge, (mx - 9, my - 9))
                        else:
                            pygame.draw.circle(surface, (250, 204, 21), (mx, my), 7)
                    elif status == "completed":
                        # Cleared Station: Emerald green badge with checkmark
                        badge = self._badge_cache.get(("completed", "✓"))
                        if badge:
                            surface.blit(badge, (mx - 9, my - 9))
                        else:
                            pygame.draw.circle(surface, (34, 197, 94), (mx, my), 6)
                    else:
                        # Upcoming Station: Vibrant Amber/Orange numbered badge (Never invisible slate!)
                        badge = self._badge_cache.get(("upcoming", label)) or self._badge_cache.get(("upcoming", "?"))
                        if badge:
                            surface.blit(badge, (mx - 9, my - 9))
                        else:
                            pygame.draw.circle(surface, (251, 146, 60), (mx, my), 6)

        # Draw Player Marker (Hero Beacon)
        if player_pos:
            px, py = self.world_to_map(player_pos[0], player_pos[1])
            # Radiant outer pulse aura
            aura_r = int(7.0 + pulse * 3.0)
            pygame.draw.circle(surface, (56, 189, 248), (px, py), aura_r, 1)
            # Bright hero center dot
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 4)
            pygame.draw.circle(surface, (2, 132, 199), (px, py), 3)

        # Fist charge feedback on minimap container if hovered
        if cursor_pos and self.container_rect.collidepoint(cursor_pos) and hold_pct > 0.05:
            bar_w = int((self.width - 24) * hold_pct)
            pygame.draw.rect(
                surface,
                (250, 204, 21),
                (self.container_x + 12, self.container_y + self.height - 4, bar_w, 2),
                border_radius=1,
            )
