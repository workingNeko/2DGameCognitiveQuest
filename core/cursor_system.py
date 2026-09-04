# core/cursor_system.py
"""
League of Legends-inspired Custom Game Cursor System.
Features:
- Stylized, vector-rendered golden MOBA pointer with drop shadow and jewel core.
- Contextual state morphing (Default, NPC Talk, Portal Warp, Quiz Station, UI Button).
- Animated expanding click ripples (LoL-style move ping and interact ping).
- Sleek radial gesture charging arc for fist/hold interactions.
- Smooth stardust motion trail.
"""

import pygame
import math
import time
from collections import deque


class CursorState:
    DEFAULT = "default"
    HOVER_NPC = "hover_npc"
    HOVER_PORTAL = "hover_portal"
    HOVER_QUIZ = "hover_quiz"
    HOVER_BUTTON = "hover_button"


class GameCursor:
    def __init__(self):
        self.cursor_pos = (400, 300)
        self.current_state = CursorState.DEFAULT
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.peace_start_time = 0
        self.click_hold_time = 0.9

        # Click ripples: list of dicts {x, y, start_time, duration, color, ripple_type}
        self.ripples = []

        # Motion trail: deque of (x, y, timestamp)
        self.trail = deque(maxlen=8)
        self.last_trail_time = 0

        # Fonts
        self.font_small = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
        self.font_pct = pygame.font.SysFont("Arial", 11, bold=True)

        # Pulse animation timer
        self.anim_t = 0.0

        # Pre-rendered base pointer cache
        self._pointer_surfs = {}
        self._init_pointer_surfaces()

    def _init_pointer_surfaces(self):
        """Pre-render high-quality cursor sprites for each state to ensure 60+ FPS."""
        states = [
            CursorState.DEFAULT,
            CursorState.HOVER_NPC,
            CursorState.HOVER_PORTAL,
            CursorState.HOVER_QUIZ,
            CursorState.HOVER_BUTTON,
        ]
        for state in states:
            self._pointer_surfs[state] = self._render_pointer_surface(state)

    def _render_pointer_surface(self, state):
        """Render a League of Legends styled pointer sprite."""
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)

        # Color palette by state
        if state == CursorState.HOVER_NPC:
            gold_dark = (180, 83, 9)
            gold_mid = (245, 158, 11)
            gold_light = (254, 240, 138)
            gem_col = (251, 191, 36)
            glow_col = (245, 158, 11, 70)
        elif state == CursorState.HOVER_PORTAL:
            gold_dark = (14, 116, 144)
            gold_mid = (6, 182, 212)
            gold_light = (165, 243, 252)
            gem_col = (34, 211, 238)
            glow_col = (6, 182, 212, 85)
        elif state == CursorState.HOVER_QUIZ:
            gold_dark = (126, 34, 206)
            gold_mid = (168, 85, 247)
            gold_light = (233, 213, 255)
            gem_col = (192, 132, 252)
            glow_col = (168, 85, 247, 80)
        elif state == CursorState.HOVER_BUTTON:
            gold_dark = (161, 98, 7)
            gold_mid = (234, 179, 8)
            gold_light = (254, 249, 195)
            gem_col = (59, 130, 246)
            glow_col = (234, 179, 8, 90)
        else:  # DEFAULT
            gold_dark = (120, 53, 15)
            gold_mid = (217, 119, 6)
            gold_light = (253, 224, 71)
            gem_col = (56, 189, 248)  # Sapphire core
            glow_col = (217, 119, 6, 45)

        # Ambient glow aura for interactable states
        if glow_col:
            pygame.draw.circle(surf, glow_col, (10, 10), 16)
            pygame.draw.circle(surf, (glow_col[0], glow_col[1], glow_col[2], glow_col[3] // 2), (10, 10), 22)

        # Drop shadow offset (+2, +2)
        shadow_pts = [(2, 2), (20, 16), (13, 17), (17, 26), (13, 28), (9, 19), (4, 23)]
        pygame.draw.polygon(surf, (15, 23, 42, 180), shadow_pts)

        # Dark border
        border_pts = [(0, 0), (18, 14), (11, 15), (15, 24), (11, 26), (7, 17), (2, 21)]
        pygame.draw.polygon(surf, (15, 23, 42), border_pts)

        # Outer gold body
        body_pts = [(1, 1), (16, 13), (10, 14), (14, 23), (11, 24), (8, 16), (3, 19)]
        pygame.draw.polygon(surf, gold_dark, body_pts)

        # Inner gold fill
        inner_pts = [(2, 3), (14, 12), (9, 13), (12, 20), (10, 21), (7, 15), (4, 17)]
        pygame.draw.polygon(surf, gold_mid, inner_pts)

        # High-light filigree ridge
        highlight_pts = [(2, 2), (12, 10), (7, 11), (3, 7)]
        pygame.draw.polygon(surf, gold_light, highlight_pts)

        # Jewel core (diamond socket)
        gem_pts = [(5, 7), (8, 5), (10, 8), (7, 10)]
        pygame.draw.polygon(surf, gem_col, gem_pts)
        pygame.draw.circle(surf, (255, 255, 255), (7, 7), 1)

        # Additional State Badges
        if state == CursorState.HOVER_NPC:
            # Talk / dialogue bubble icon next to pointer
            bubble_x, bubble_y = 20, 12
            pygame.draw.ellipse(surf, (255, 255, 255), (bubble_x, bubble_y, 14, 11))
            pygame.draw.ellipse(surf, (30, 41, 59), (bubble_x, bubble_y, 14, 11), 1)
            # 3 speech dots
            pygame.draw.circle(surf, (30, 41, 59), (bubble_x + 4, bubble_y + 5), 1)
            pygame.draw.circle(surf, (30, 41, 59), (bubble_x + 7, bubble_y + 5), 1)
            pygame.draw.circle(surf, (30, 41, 59), (bubble_x + 10, bubble_y + 5), 1)
        elif state == CursorState.HOVER_PORTAL:
            # Mystic portal ring symbol
            px, py = 22, 12
            pygame.draw.circle(surf, (34, 211, 238), (px, py), 6, 2)
            pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)
        elif state == CursorState.HOVER_QUIZ:
            # Sparkle / star indicator
            qx, qy = 22, 12
            pygame.draw.line(surf, (250, 204, 21), (qx - 5, qy), (qx + 5, qy), 2)
            pygame.draw.line(surf, (250, 204, 21), (qx, qy - 5), (qx, qy + 5), 2)
            pygame.draw.circle(surf, (255, 255, 255), (qx, qy), 2)

        return surf

    def update(self, cursor_pos, current_gesture="NO HAND", fist_start_time=0, click_hold_time=0.9, peace_start_time=0):
        """Update cursor tracking, trail, and ripple animations."""
        self.cursor_pos = cursor_pos
        self.current_gesture = current_gesture
        self.fist_start_time = fist_start_time
        self.peace_start_time = peace_start_time
        self.click_hold_time = click_hold_time
        self.anim_t += 0.05

        # Record stardust motion trail
        now = time.time()
        if now - self.last_trail_time > 0.02:
            self.last_trail_time = now
            self.trail.append((cursor_pos[0], cursor_pos[1], now))

        # Update active ripples
        alive_ripples = []
        for r in self.ripples:
            elapsed = now - r["start_time"]
            if elapsed < r["duration"]:
                alive_ripples.append(r)
        self.ripples = alive_ripples

    def set_hover_state(self, state):
        """Change contextual hover state."""
        self.current_state = state

    def add_click_ripple(self, pos, ripple_type="move"):
        """
        Spawn a League of Legends inspired expanding click ripple.
        ripple_type: 'move' (cyan/green ping) or 'interact' (golden ping)
        """
        if ripple_type == "interact":
            color = (245, 158, 11)  # Amber / Gold
        elif ripple_type == "attack":
            color = (239, 68, 68)   # Crimson Red
        else:
            color = (34, 197, 94)   # Emerald / Cyan move ping

        self.ripples.append({
            "x": pos[0],
            "y": pos[1],
            "start_time": time.time(),
            "duration": 0.38,
            "color": color,
            "type": ripple_type
        })

    def draw(self, surface):
        """Draw the motion trail, click ripples, LoL pointer, and radial charge arc."""
        now = time.time()
        cx, cy = self.cursor_pos

        # 1. DRAW STARDUST MOTION TRAIL
        if len(self.trail) > 1:
            trail_list = list(self.trail)
            for i in range(len(trail_list) - 1):
                p1 = trail_list[i]
                age = now - p1[2]
                if age < 0.25:
                    alpha = int(140 * (1.0 - age / 0.25))
                    size = max(1, int(4 * (1.0 - age / 0.25)))
                    dot_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(dot_surf, (253, 224, 71, alpha), (size, size), size)
                    surface.blit(dot_surf, (p1[0] - size, p1[1] - size))

        # 2. DRAW LEAGUE OF LEGENDS CLICK RIPPLES
        for r in self.ripples:
            elapsed = now - r["start_time"]
            progress = min(1.0, elapsed / r["duration"])
            alpha = int(240 * (1.0 - progress))
            if alpha <= 0:
                continue

            max_radius = 26
            cur_radius = int(8 + (max_radius - 8) * progress)

            r_surf = pygame.Surface((cur_radius * 2 + 20, cur_radius * 2 + 20), pygame.SRCALPHA)
            rx, ry = cur_radius + 10, cur_radius + 10
            col = r["color"]
            col_rgba = (col[0], col[1], col[2], alpha)

            # Outer expanding ripple ring
            pygame.draw.circle(r_surf, col_rgba, (rx, ry), cur_radius, 2)
            # Inner sharper ping ring
            inner_radius = max(2, int(cur_radius * 0.55))
            pygame.draw.circle(r_surf, (255, 255, 255, min(255, alpha + 30)), (rx, ry), inner_radius, 1)

            # Four cardinal diamond pings (classic LoL move indicator)
            d_dist = cur_radius + 3
            for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
                px = rx + int(math.cos(angle) * d_dist)
                py = ry + int(math.sin(angle) * d_dist)
                pygame.draw.circle(r_surf, col_rgba, (px, py), 2)

            surface.blit(r_surf, (r["x"] - rx, r["y"] - ry))

        # 3. DRAW RADIAL GESTURE CHARGE METER (FIST OR PEACE HOLD)
        hold_time = 0
        is_charging = False
        charge_col = (250, 204, 21)

        if self.fist_start_time > 0:
            hold_time = now - self.fist_start_time
            is_charging = True
            charge_col = (250, 204, 21)  # Golden yellow
        elif self.peace_start_time > 0:
            hold_time = now - self.peace_start_time
            is_charging = True
            charge_col = (34, 197, 94)   # Emerald green

        if is_charging:
            pct = min(1.0, hold_time / max(0.1, self.click_hold_time))
            radius = 22
            meter_surf = pygame.Surface(((radius + 12) * 2, (radius + 12) * 2), pygame.SRCALPHA)
            mx = radius + 12
            my = radius + 12

            # Background translucent ring
            pygame.draw.circle(meter_surf, (15, 23, 42, 160), (mx, my), radius, 4)

            # Draw clockwise filled arc
            if pct > 0:
                steps = max(3, int(pct * 48))
                start_angle = -math.pi / 2  # 12 o'clock
                sweep = 2 * math.pi * pct

                arc_pts = []
                for s in range(steps + 1):
                    a = start_angle + (sweep * s / steps)
                    ax = mx + math.cos(a) * radius
                    ay = my + math.sin(a) * radius
                    arc_pts.append((ax, ay))

                if len(arc_pts) >= 2:
                    pygame.draw.lines(meter_surf, charge_col, False, arc_pts, 4)

                # Leading spark at tip of arc
                tip_a = start_angle + sweep
                tip_x = mx + math.cos(tip_a) * radius
                tip_y = my + math.sin(tip_a) * radius
                pygame.draw.circle(meter_surf, (255, 255, 255), (int(tip_x), int(tip_y)), 3)

            surface.blit(meter_surf, (cx - mx, cy - my))

            # Percentage text
            pct_str = f"{int(pct * 100)}%"
            pct_surf = self.font_pct.render(pct_str, True, charge_col)
            surface.blit(pct_surf, (cx - pct_surf.get_width() // 2, cy + radius + 4))

        # 4. DRAW BASE MOBA POINTER SPRITE
        active_surf = self._pointer_surfs.get(self.current_state, self._pointer_surfs[CursorState.DEFAULT])
        surface.blit(active_surf, (cx, cy))


# Global singleton instance
game_cursor = GameCursor()
