# core/pathfinder_guide.py
"""
Quest Pathfinder & Visual Guide Trail System for Cognitive Quest 2D.
Provides:
1. Hierarchy-Aware Objective Tracking: Dynamically determines the active quest target
   (Station 1 -> Station 2 -> ... -> Station 5/6 -> Stage Mentor / Altar -> Goal Portal)
   across all 4 Quarters (Quarter 1 to Quarter 4) and all 12 Maps.
2. Grid BFS Pathfinder: Finds the shortest walkable path on map tile grids.
3. Radiant Celestial Starlight Trail: Animated, flowing breadcrumb motes with chevrons
   and soft glowing halos (sized compactly for a clean, non-intrusive aesthetic).
4. Dynamic Off-Screen Compass & Objective Beacon: Points the player directly to the
   active target with distance indicators when off-screen.
"""

import pygame
import math
import time
import collections
from .font_manager import get_font, sanitize_text

THEME_TRAIL_COLORS = {
    "forest": {
        "trail": (34, 197, 94),        # Emerald Green
        "glow": (250, 204, 21),        # Gold
        "chevron": (254, 240, 138),
        "pill_bg": (20, 83, 45),
        "pill_border": (250, 204, 21)
    },
    "fiesta": {
        "trail": (245, 158, 11),       # Amber Gold
        "glow": (254, 240, 138),       # Warm Cream
        "chevron": (239, 68, 68),      # Fiesta Red
        "pill_bg": (120, 53, 15),
        "pill_border": (251, 191, 36)
    },
    "desert": {
        "trail": (217, 119, 6),        # Bronze Gold
        "glow": (253, 224, 71),        # Sun Yellow
        "chevron": (234, 88, 12),      # Terracotta
        "pill_bg": (113, 63, 18),
        "pill_border": (253, 224, 71)
    },
    "water": {
        "trail": (14, 165, 233),       # Sky Blue
        "glow": (186, 230, 253),       # Cyan Foam
        "chevron": (59, 130, 246),
        "pill_bg": (12, 74, 110),
        "pill_border": (56, 189, 248)
    }
}

STATION_NAMES = {
    "quarter1": {
        1: "Circle Guardian",
        2: "Heart Guardian",
        3: "Square Guardian",
        4: "Star Guardian",
        5: "Diamond Guardian"
    },
    "quarter2": {
        1: "Sari-Sari Store (Aling Nena)",
        2: "Sorbetes Cart (Mang Pedring)",
        3: "Jeepney Terminal (Kuya Jomar)",
        4: "Fruit Stand (Ate Maria)",
        5: "Parol Workshop (Mang Carding)"
    },
    "quarter3": {
        1: "Desert Sage 1",
        2: "Desert Sage 2",
        3: "Desert Sage 3",
        4: "Desert Sage 4",
        5: "Desert Sage 5"
    },
    "quarter4": {
        1: "Water Guardian 1",
        2: "Water Guardian 2",
        3: "Water Guardian 3",
        4: "Water Guardian 4",
        5: "Water Guardian 5",
        6: "Water Guardian 6"
    }
}


class QuestPathfinderGuide:
    """
    Modular Pathfinder & Starlight Trail Renderer attached to Quarter stages.
    """
    def __init__(self, quarter_instance, quarter_id="quarter1", theme="forest"):
        self.q = quarter_instance
        self.quarter_id = quarter_id
        self.theme_key = theme

        # Pathfinder caching
        self.last_calc_time = 0.0
        self.cached_path_world = []
        self.last_player_tile = (-1, -1)
        self.last_target_tile = (-1, -1)
        self.current_target_info = None

        self.font = get_font("Comic Sans MS", 13, bold=True)
        self.active = True

    def update_theme(self, theme_key):
        self.theme_key = theme_key

    def _extract_portal_tile(self, portal):
        """Safely extracts tile coordinates from a portal object."""
        if portal is None:
            return None
        if hasattr(portal, 'tile_x') and hasattr(portal, 'tile_y'):
            return (int(portal.tile_x), int(portal.tile_y))
        elif hasattr(portal, 'x') and hasattr(portal, 'y'):
            # In Quarter1, 2, 3 and StageSelect, Portal.x and Portal.y are already tile coordinates (< 150)
            tx = portal.x if portal.x < 150 else int(portal.x // 32)
            ty = portal.y if portal.y < 150 else int(portal.y // 32)
            return (int(tx), int(ty))
        return None

    def get_active_hierarchy_target(self):
        """
        Determines the current objective target based on stage progression hierarchy:
        Stations 1..5/6 -> Stage Mentor / Altar -> Goal Portal.
        For Stage Select: Guides to the active/unlocked quarter or guardian NPC.
        Returns: (tile_x, tile_y, target_name, is_portal) or None
        """
        # ====================================================
        # 0. STAGE SELECT HUB NAVIGATION
        # ====================================================
        if self.quarter_id == "stageselect":
            # Check completed quarters
            is_comp = getattr(self.q, 'is_quarter_completed', lambda q: False)
            q1_done = is_comp('quarter1')
            q2_done = is_comp('quarter2')
            q3_done = is_comp('quarter3')
            q4_done = is_comp('quarter4')

            def find_portal_coords(direction):
                for p in getattr(self.q, 'portals', []):
                    if getattr(p, 'direction', None) == direction:
                        return self._extract_portal_tile(p)
                return None

            # Quarter 1: West corridor (Old Man -> Left Portal)
            if not q1_done:
                self.update_theme("forest")
                if getattr(self.q, 'oldman_dialogue_state', 0) == 0:
                    tx = getattr(self.q, 'npc_oldman_tile_x', 5)
                    ty = getattr(self.q, 'npc_oldman_tile_y', 12)
                    return (tx, ty, "Old Man (Quarter 1 Guide)", False)
                else:
                    p_pos = find_portal_coords('left') or (0, 12)
                    return (p_pos[0], p_pos[1], "Quarter 1: Geometry Forest", True)

            # Quarter 2: South corridor (Knight -> Up Portal)
            elif not q2_done:
                self.update_theme("fiesta")
                if getattr(self.q, 'knight_dialogue_state', 0) == 0:
                    tx = getattr(self.q, 'npc_knight_tile_x', 25)
                    ty = getattr(self.q, 'npc_knight_tile_y', 23)
                    return (tx, ty, "Knight (Quarter 2 Guardian)", False)
                else:
                    p_pos = find_portal_coords('up') or (25, 25)
                    return (p_pos[0], p_pos[1], "Quarter 2: Barrio Fiesta", True)

            # Quarter 3: East corridor (Skeleton -> Right Portal)
            elif not q3_done:
                self.update_theme("desert")
                if getattr(self.q, 'skeleton_dialogue_state', 0) == 0:
                    tx = getattr(self.q, 'npc_skeleton_tile_x', 47)
                    ty = getattr(self.q, 'npc_skeleton_tile_y', 12)
                    return (tx, ty, "Skeleton (Quarter 3 Guardian)", False)
                else:
                    p_pos = find_portal_coords('right') or (52, 12)
                    return (p_pos[0], p_pos[1], "Quarter 3: Monetary Desert", True)

            # Quarter 4: North corridor (Bromen -> Down Portal)
            elif not q4_done:
                self.update_theme("water")
                if getattr(self.q, 'bromen_dialogue_state', 0) == 0:
                    tx = getattr(self.q, 'npc_bromen_tile_x', 25)
                    ty = getattr(self.q, 'npc_bromen_tile_y', 3)
                    return (tx, ty, "Bromen (Quarter 4 Guardian)", False)
                else:
                    p_pos = find_portal_coords('down') or (25, 0)
                    return (p_pos[0], p_pos[1], "Quarter 4: Aquatic Temple", True)

            # All Quarters Completed: Center Sanctuary
            else:
                self.update_theme("forest")
                tx = getattr(self.q, 'npc_oldman_tile_x', 5)
                ty = getattr(self.q, 'npc_oldman_tile_y', 12)
                return (tx, ty, "Grand Champion Sanctuary", False)

        # ====================================================
        # IN-STAGE QUARTERS 1 - 4
        # ====================================================
        st_idx = getattr(self.q, 'quiz_station_index', 1)
        quiz_state = getattr(self.q, 'quiz_state', 0)
        quiz_stations = getattr(self.q, 'quiz_stations', {})
        map_name = getattr(self.q, 'map_name', getattr(self.q, 'current_map_name', '')).lower()

        max_stations = 6 if self.quarter_id == "quarter4" and 6 in quiz_stations else 5

        # ----------------------------------------------------
        # 1. QUIZ STATIONS (Hierarchy 1 to 5 or 6)
        # ----------------------------------------------------
        if st_idx <= max_stations and quiz_state < 6:
            # Check if current station has valid tile coords
            if st_idx in quiz_stations:
                tx, ty = quiz_stations[st_idx]
                station_names_map = STATION_NAMES.get(self.quarter_id, {})
                t_name = station_names_map.get(st_idx, f"Station {st_idx}")
                return (tx, ty, t_name, False)

        # ----------------------------------------------------
        # 2. STAGE MENTOR / ALTAR / MINIGAME
        # ----------------------------------------------------
        # Quarter 1: Old Man Riddle (Map 1), Shape Altar (Map 2), Jigsaw Altar (Map 3)
        if self.quarter_id == "quarter1":
            if "map1" in map_name:
                oldman_answered = getattr(self.q, 'oldman_riddle_answered', False) or getattr(self.q, 'riddle_answered', False)
                if not oldman_answered:
                    tx = getattr(self.q, 'npc_oldman_tile_x', 49)
                    ty = getattr(self.q, 'npc_oldman_tile_y', 2)
                    if tx > 0 and ty > 0:
                        return (tx, ty, "Forest Mentor (Old Man)", False)
                else:
                    # Point directly to Map 1 Exit Portal to Map 2
                    all_portals = getattr(self.q, 'portals', []) + getattr(self.q, 'locked_portals', [])
                    for p in all_portals:
                        coords = self._extract_portal_tile(p)
                        if coords:
                            return (coords[0], coords[1], "Portal to Map 2", True)
                    if hasattr(self.q, 'portal_tile_x') and hasattr(self.q, 'portal_tile_y'):
                        if self.q.portal_tile_x > 0 and self.q.portal_tile_y > 0:
                            return (self.q.portal_tile_x, self.q.portal_tile_y, "Portal to Map 2", True)
                    return (52, 3, "Portal to Map 2", True)

            elif "map2" in map_name:
                puzzle_solved = getattr(self.q, 'puzzle_solved', False)
                if not puzzle_solved:
                    tx = getattr(self.q, 'npc_oldman_tile_x', 46)
                    ty = getattr(self.q, 'npc_oldman_tile_y', 16)
                    if tx > 0 and ty > 0:
                        return (tx, ty, "Shape Altar Guardian", False)
                else:
                    all_portals = getattr(self.q, 'portals', []) + getattr(self.q, 'locked_portals', [])
                    for p in all_portals:
                        coords = self._extract_portal_tile(p)
                        if coords:
                            return (coords[0], coords[1], "Portal to Map 3", True)
                    if hasattr(self.q, 'portal_tile_x') and hasattr(self.q, 'portal_tile_y'):
                        if self.q.portal_tile_x > 0 and self.q.portal_tile_y > 0:
                            return (self.q.portal_tile_x, self.q.portal_tile_y, "Portal to Map 3", True)
                    return (49, 16, "Portal to Map 3", True)

            elif "map3" in map_name:
                puzzle_solved = getattr(self.q, 'puzzle_solved', False)
                if not puzzle_solved:
                    tx = getattr(self.q, 'npc_oldman_tile_x', 18)
                    ty = getattr(self.q, 'npc_oldman_tile_y', 1)
                    if tx > 0 and ty > 0:
                        return (tx, ty, "Grand Mosaic Altar", False)
                else:
                    all_portals = getattr(self.q, 'portals', []) + getattr(self.q, 'locked_portals', [])
                    for p in all_portals:
                        coords = self._extract_portal_tile(p)
                        if coords:
                            return (coords[0], coords[1], "Quarter 1 Exit Portal", True)
                    if hasattr(self.q, 'portal_tile_x') and hasattr(self.q, 'portal_tile_y'):
                        if self.q.portal_tile_x > 0 and self.q.portal_tile_y > 0:
                            return (self.q.portal_tile_x, self.q.portal_tile_y, "Quarter 1 Exit Portal", True)
                    return (20, 0, "Quarter 1 Exit Portal", True)

        # Quarter 2: Barrio Leader / Master Carpenter / Hermano Mayor
        elif self.quarter_id == "quarter2":
            if getattr(self.q, 'npc_oldman_found', False) and quiz_state == 5:
                tx = getattr(self.q, 'npc_oldman_tile_x', 0)
                ty = getattr(self.q, 'npc_oldman_tile_y', 0)
                if tx > 0 and ty > 0:
                    mentor_name = "Barrio Leader"
                    if "map5" in map_name:
                        mentor_name = "Master Carpenter"
                    elif "map6" in map_name:
                        mentor_name = "Hermano Mayor"
                    return (tx, ty, mentor_name, False)

        # Quarter 3: Desert Vault Keeper / Pharaoh Altar
        elif self.quarter_id == "quarter3":
            if getattr(self.q, 'npc_oldman_found', False) and quiz_state in [5, 6]:
                tx = getattr(self.q, 'npc_oldman_tile_x', 0)
                ty = getattr(self.q, 'npc_oldman_tile_y', 0)
                if tx > 0 and ty > 0:
                    return (tx, ty, "Desert Vault Keeper", False)

        # Quarter 4: Temple Elder / Guardian Bromen
        elif self.quarter_id == "quarter4":
            if getattr(self.q, 'bromen_dialogue_state', 0) not in [0, 3] and hasattr(self.q, 'bromen_npc_x'):
                bx = int(round(self.q.bromen_npc_x / 32))
                by = int(round(self.q.bromen_npc_y / 32))
                if bx > 0 and by > 0:
                    return (bx, by, "Guardian Bromen", False)

        # ----------------------------------------------------
        # 3. GOAL PORTAL FALLBACK
        # ----------------------------------------------------
        all_portals = getattr(self.q, 'portals', []) + getattr(self.q, 'locked_portals', [])
        if all_portals:
            coords = self._extract_portal_tile(all_portals[0])
            if coords:
                return (coords[0], coords[1], "Goal Portal", True)

        if hasattr(self.q, 'portal_tile_x') and hasattr(self.q, 'portal_tile_y'):
            if self.q.portal_tile_x > 0 and self.q.portal_tile_y > 0:
                return (self.q.portal_tile_x, self.q.portal_tile_y, "Goal Portal", True)

        return None

    def find_walkable_path(self, start, end):
        """BFS pathfinding from start (x, y) to end (x, y) on tile grid."""
        if start == end:
            return [start]

        game_map = getattr(self.q, 'game_map', [])
        walkable = getattr(self.q, 'WALKABLE_TILES', {"G", "#", "1", "2", "3", "4", "5", "6", "P", "B", "r", "l", "u", "d"})
        rows = len(game_map)
        if rows == 0:
            return []
        cols = len(game_map[0])

        # If end tile is solid/non-walkable, find adjacent walkable neighbors
        end_targets = {end}
        if 0 <= end[1] < rows and 0 <= end[0] < cols:
            if game_map[end[1]][end[0]] not in walkable:
                adj = []
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = end[0] + dx, end[1] + dy
                    if 0 <= ny < rows and 0 <= nx < cols and game_map[ny][nx] in walkable:
                        adj.append((nx, ny))
                if adj:
                    end_targets = set(adj)

        queue = collections.deque([[start]])
        seen = {start}
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr in end_targets:
                if curr != end:
                    return path + [end]
                return path

            cx, cy = curr
            for dx, dy in directions:
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < rows and 0 <= nx < cols:
                    tile = game_map[ny][nx]
                    if tile in walkable and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        queue.append(path + [(nx, ny)])

        # Fallback straight direct line if enclosed
        return [start, end]

    def update(self, dt=0.016):
        """Recalculate path periodically or when positions shift."""
        now = time.time()
        tile_size = 32
        player_x = getattr(self.q, 'player_x', 0)
        player_y = getattr(self.q, 'player_y', 0)
        pl_tx = int(round(player_x / tile_size))
        pl_ty = int(round(player_y / tile_size))

        target_info = self.get_active_hierarchy_target()
        self.current_target_info = target_info

        if not target_info:
            self.cached_path_world = []
            return

        tgt_tx, tgt_ty, tgt_name, is_portal = target_info

        # Check if recalculation is required
        needs_recalc = (
            now - self.last_calc_time > 0.25 or
            (pl_tx, pl_ty) != self.last_player_tile or
            (tgt_tx, tgt_ty) != self.last_target_tile or
            len(self.cached_path_world) == 0
        )

        if needs_recalc:
            self.last_calc_time = now
            self.last_player_tile = (pl_tx, pl_ty)
            self.last_target_tile = (tgt_tx, tgt_ty)

            grid_path = self.find_walkable_path((pl_tx, pl_ty), (tgt_tx, tgt_ty))
            if grid_path:
                # Convert to world pixel coordinates
                world_pts = []
                # First point: exact player center
                world_pts.append((player_x + tile_size / 2, player_y + tile_size / 2))
                # Intermediate tiles
                for tx, ty in grid_path[1:-1]:
                    world_pts.append((tx * tile_size + tile_size / 2, ty * tile_size + tile_size / 2))
                # Final point: target center
                world_pts.append((tgt_tx * tile_size + tile_size / 2, tgt_ty * tile_size + tile_size / 2))

                # Smooth out points (remove redundant colinear points)
                self.cached_path_world = self._simplify_path(world_pts)
            else:
                self.cached_path_world = []

    def _simplify_path(self, pts):
        if len(pts) <= 2:
            return pts
        res = [pts[0]]
        for i in range(1, len(pts) - 1):
            p_prev = res[-1]
            p_curr = pts[i]
            p_next = pts[i + 1]
            # Check if p_prev, p_curr, p_next form a straight line
            dx1 = p_curr[0] - p_prev[0]
            dy1 = p_curr[1] - p_prev[1]
            dx2 = p_next[0] - p_curr[0]
            dy2 = p_next[1] - p_curr[1]
            cross = dx1 * dy2 - dy1 * dx2
            if abs(cross) > 1e-4:
                res.append(p_curr)
        res.append(pts[-1])
        return res

    def draw(self):
        """
        Draws the compact, radiant starlight trail along the path
        and off-screen directional compass badge.
        """
        if not self.active or not self.cached_path_world or len(self.cached_path_world) < 2:
            return

        # Suppress if pause menu, quiz dialog, instruction modal, or stage select dialogue is actively open
        if getattr(self.q, 'pause_menu', None) and getattr(self.q.pause_menu, 'is_paused', False):
            return
        if getattr(self.q, 'quiz_state', 0) in [1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 20, 21, 22]:
            return
        if getattr(self.q, 'instruction_modal', None) and getattr(self.q.instruction_modal, 'is_visible', False):
            return
        if getattr(self.q, 'greeting_dialog', None) and getattr(self.q.greeting_dialog, 'is_visible', False):
            return
        if getattr(self.q, 'portal_transition_active', False):
            return
        if getattr(self.q, 'puzzle_active', False):
            return
        if getattr(self.q, 'oldman_dialogue_state', 0) == 1:
            return
        if getattr(self.q, 'knight_dialogue_state', 0) == 1:
            return
        if getattr(self.q, 'skeleton_dialogue_state', 0) == 1:
            return
        if getattr(self.q, 'bromen_dialogue_state', 0) == 1:
            return
        if getattr(self.q, 'interactable_dialogue_state', 0) == 1:
            return

        camera_x = getattr(self.q, 'camera_x', 0)
        camera_y = getattr(self.q, 'camera_y', 0)
        zoom = getattr(self.q, 'lol_camera', None).zoom if getattr(self.q, 'lol_camera', None) else 1.50
        screen = self.q.screen
        sw, sh = screen.get_size()

        theme_data = THEME_TRAIL_COLORS.get(self.theme_key, THEME_TRAIL_COLORS["forest"])
        trail_color = theme_data["trail"]
        glow_color = theme_data["glow"]
        chevron_color = theme_data["chevron"]

        now_ms = pygame.time.get_ticks()
        t = now_ms * 0.001

        # Transform world path into screen coordinates
        screen_pts = []
        for wx, wy in self.cached_path_world:
            sx = (wx - camera_x) * zoom
            sy = (wy - camera_y) * zoom
            screen_pts.append((sx, sy))

        # Calculate polyline segment lengths
        seg_lengths = []
        total_len = 0.0
        for i in range(len(screen_pts) - 1):
            p1 = screen_pts[i]
            p2 = screen_pts[i + 1]
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            seg_lengths.append(dist)
            total_len += dist

        if total_len < 15:
            return

        # ----------------------------------------------------
        # 1. ANIMATED STARLIGHT MOTES & CHEVRONS ("A little bit smaller")
        # ----------------------------------------------------
        step_dist = 24.0 * zoom  # Compact distance between trail motes
        offset = (now_ms * 0.035) % step_dist

        # Halo surface for performance
        pulse_base = 3.2 * zoom
        d_size = max(2.5, 3.2 * zoom)
        ch_size = max(2.5, 3.5 * zoom)

        cur_d = offset
        while cur_d < total_len - 10:
            # Find point along polyline at distance cur_d
            acc = 0.0
            pt = None
            angle = 0.0
            for i, seg_len in enumerate(seg_lengths):
                if acc + seg_len >= cur_d:
                    ratio = (cur_d - acc) / seg_len if seg_len > 0 else 0
                    p1 = screen_pts[i]
                    p2 = screen_pts[i + 1]
                    px = p1[0] + (p2[0] - p1[0]) * ratio
                    py = p1[1] + (p2[1] - p1[1]) * ratio
                    pt = (px, py)
                    angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
                    break
                acc += seg_len

            if pt and -40 <= pt[0] <= sw + 40 and -40 <= pt[1] <= sh + 40:
                pulse_r = int((pulse_base + math.sin(t * 4.5 + cur_d * 0.08) * 0.8 * zoom))

                # Soft glowing halo
                halo_surf = pygame.Surface((pulse_r * 4, pulse_r * 4), pygame.SRCALPHA)
                pygame.draw.circle(halo_surf, (*glow_color, 45), (pulse_r * 2, pulse_r * 2), pulse_r * 2)
                screen.blit(halo_surf, (int(pt[0] - pulse_r * 2), int(pt[1] - pulse_r * 2)))

                # Diamond Starlight Mote (compact)
                diamond = [
                    (pt[0], pt[1] - d_size),
                    (pt[0] + d_size, pt[1]),
                    (pt[0], pt[1] + d_size),
                    (pt[0] - d_size, pt[1])
                ]
                pygame.draw.polygon(screen, glow_color, diamond)
                pygame.draw.polygon(screen, trail_color, diamond, 1)

                # Directional Chevron Arrow (flows along path tangent)
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                tip_x = pt[0] + cos_a * (ch_size + 4)
                tip_y = pt[1] + sin_a * (ch_size + 4)

                # Perp vector
                perp_x = -sin_a * (ch_size * 0.8)
                perp_y = cos_a * (ch_size * 0.8)

                base_x = tip_x - cos_a * ch_size
                base_y = tip_y - sin_a * ch_size

                wing1 = (base_x + perp_x, base_y + perp_y)
                wing2 = (base_x - perp_x, base_y - perp_y)

                pygame.draw.lines(screen, chevron_color, False, [wing1, (tip_x, tip_y), wing2], 2)

            cur_d += step_dist

        # ----------------------------------------------------
        # 2. DYNAMIC COMPASS / OFF-SCREEN POINTER PILL
        # ----------------------------------------------------
        if self.current_target_info:
            tgt_tx, tgt_ty, tgt_name, is_portal = self.current_target_info
            target_sx = (tgt_tx * 32 + 16 - camera_x) * zoom
            target_sy = (tgt_ty * 32 + 16 - camera_y) * zoom

            is_on_screen = (40 <= target_sx <= sw - 60 and 40 <= target_sy <= sh - 80)

            # On-screen gentle target beacon
            if is_on_screen:
                bob = math.sin(now_ms * 0.008) * 3 * zoom
                beacon_rect = pygame.Rect(target_sx - 7 * zoom, target_sy - 28 * zoom + bob, 14 * zoom, 14 * zoom)
                pygame.draw.rect(screen, glow_color, beacon_rect, border_radius=3)
                pygame.draw.rect(screen, (0, 0, 0), beacon_rect, 1, border_radius=3)
                excl_surf = self.font.render("!", True, (15, 23, 42))
                screen.blit(excl_surf, excl_surf.get_rect(center=beacon_rect.center))
            else:
                # Off-screen pointer pill clamped at screen perimeter
                pl_sx = screen_pts[0][0]
                pl_sy = screen_pts[0][1]
                dx = target_sx - pl_sx
                dy = target_sy - pl_sy
                dist_tiles = int(math.hypot(dx, dy) / (32 * zoom))
                angle = math.atan2(dy, dx)

                clamp_radius = min(sw, sh) * 0.38
                clamp_x = max(70, min(sw - 70, pl_sx + math.cos(angle) * clamp_radius))
                clamp_y = max(60, min(sh - 70, pl_sy + math.sin(angle) * clamp_radius))

                ptr_text = f">> {tgt_name} ({dist_tiles}m)"
                ptr_surf = self.font.render(sanitize_text(ptr_text), True, (255, 255, 255))
                pw, ph = ptr_surf.get_width() + 16, 26
                p_rect = pygame.Rect(clamp_x - pw // 2, clamp_y - ph // 2, pw, ph)

                # Shadow
                pygame.draw.rect(screen, (0, 0, 0, 140), p_rect.move(2, 2), border_radius=8)
                # Pill background
                pygame.draw.rect(screen, theme_data["pill_bg"], p_rect, border_radius=8)
                pygame.draw.rect(screen, theme_data["pill_border"], p_rect, 2, border_radius=8)
                screen.blit(ptr_surf, (p_rect.x + 8, p_rect.y + 4))
