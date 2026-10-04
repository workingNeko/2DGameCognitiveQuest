# core/cursor_system.py
"""
Magical Game Cursor & Gesture System for Cognitive Quest 2D.
Kid-Friendly Edition (Designed for Grade 2 / 7-8 Year Olds):
- Magic Wand & Radiant Star Pointer with drop shadow and jewel core.
- Contextual state morphing (Default, NPC Talk, Portal Warp, Quiz Station, UI Button).
- Enchanting Rainbow Stardust Motion Trail with twinkling micro-stars.
- Celebratory sparkle click ripples and bubble pings.
- Quick-response 0.22s dwell hold time to eliminate arm and hand fatigue.
- Smooth 1-Euro Filter for jitter-free wrist tracking.
"""

import math
import random
import time
from collections import deque
import pygame


class OneEuroFilter:
    """
    1-Euro Filter for real-time noisy signal smoothing with dynamic velocity-based cutoff frequency.
    Paper: Casiez et al., CHI 2012 ("1 € filter: a simple speed-based low-pass filter for noisy input in interactive systems")
    - At low speed (aiming / steady hand): cutoff frequency is low (~min_cutoff), completely eliminating jitter.
    - At high speed (swiping / flicking): cutoff frequency dynamically rises, providing instant 0-lag tracking.
    """
    def __init__(self, t0=0.0, x0=0.0, dx0=0.0, min_cutoff=0.85, beta=0.015, d_cutoff=1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def _alpha(self, rate, cutoff):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate if rate > 0 else 0.016
        return 1.0 / (1.0 + tau / te)

    def filter(self, t, x):
        t_e = t - self.t_prev
        if t_e <= 0.0:
            return self.x_prev

        rate = max(10.0, min(240.0, 1.0 / t_e))
        dx = (x - self.x_prev) * rate
        edx = self.dx_prev + self._alpha(rate, self.d_cutoff) * (dx - self.dx_prev)
        cutoff = self.min_cutoff + self.beta * abs(edx)
        x_hat = self.x_prev + self._alpha(rate, cutoff) * (x - self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = edx
        self.t_prev = t
        return x_hat

    def __call__(self, t, x):
        return self.filter(t, x)

    def reset(self, t=0.0, x=0.0):
        self.x_prev = float(x)
        self.dx_prev = 0.0
        self.t_prev = float(t)


class CursorState:
    DEFAULT = "default"
    HOVER_NPC = "hover_npc"
    HOVER_PORTAL = "hover_portal"
    HOVER_QUIZ = "hover_quiz"
    HOVER_BUTTON = "hover_button"


class CursorTheme:
    MAGIC_STAR = "magic_star"
    GOLD_MOBA = "gold_moba"


# Rainbow Palette for Grade 2 Stardust Motion Trail
RAINBOW_COLORS = [
    (244, 63, 94),   # Bright Rose / Pink
    (249, 115, 22),  # Vivid Orange
    (250, 204, 21),  # Golden Star Yellow
    (34, 197, 94),   # Emerald Green
    (6, 182, 212),   # Radiant Cyan
    (168, 85, 247),  # Magical Purple
]


class GameCursor:
    def __init__(self, theme=CursorTheme.MAGIC_STAR):
        self.cursor_pos = (400, 300)
        self.current_state = CursorState.DEFAULT
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.peace_start_time = 0
        # Quick-response 0.22s dwell time tailored for Grade 2 children
        self.click_hold_time = 0.22
        self.theme = theme

        # Click ripples & sparkle bursts: list of dicts
        self.ripples = []
        self.click_sparkles = []

        # Rainbow stardust motion trail: deque of (x, y, timestamp, color_index)
        self.trail = deque(maxlen=14)
        self.last_trail_time = 0
        self.trail_color_counter = 0

        # Fonts (safely initialized)
        if not pygame.font.get_init():
            try:
                pygame.font.init()
            except Exception:
                pass
        try:
            self.font_small = pygame.font.SysFont("Comic Sans MS", 12, bold=True)
            self.font_pct = pygame.font.SysFont("Arial", 11, bold=True)
        except Exception:
            self.font_small = None
            self.font_pct = None

        # Pulse animation timer
        self.anim_t = 0.0

        # Pre-rendered pointer cache
        self._pointer_surfs = {}
        self._init_pointer_surfaces()

        # Low-spec optimization: Reusable surfaces
        self._meter_surf = pygame.Surface((72, 72), pygame.SRCALPHA)
        self._trail_cache = {}
        self._init_trail_cache()

    def _init_trail_cache(self):
        """Pre-renders rainbow particle stamps for zero-heap motion trails."""
        for c_idx, col in enumerate(RAINBOW_COLORS):
            for s in range(1, 6):
                for a_idx in range(1, 16):
                    a_val = min(255, a_idx * 16)
                    tsurf = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(tsurf, (*col, a_val), (s + 1, s + 1), s)
                    if s >= 3:
                        pygame.draw.circle(tsurf, (255, 255, 255, min(255, a_val + 40)), (s + 1, s + 1), max(1, s // 2))
                    self._trail_cache[(c_idx, s, a_idx)] = tsurf

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
            self._pointer_surfs[state] = self._render_magic_star_pointer(state)

    def _render_magic_star_pointer(self, state):
        """
        Renders a delightful Magic Star Wand cursor tailored for Grade 2 children:
        - Angled magical wand handle with gold/silver banding
        - Radiant 5-pointed glowing star tip
        - Sparkling jewel core and state badges
        """
        surf = pygame.Surface((52, 52), pygame.SRCALPHA)

        # Theme color palette by state
        if state == CursorState.HOVER_NPC:
            star_primary = (251, 146, 60)   # Friendly Coral / Peach
            star_core = (254, 215, 170)
            gem_col = (239, 68, 68)         # Ruby core
            glow_col = (251, 146, 60, 95)
            wand_col = (217, 119, 6)
        elif state == CursorState.HOVER_PORTAL:
            star_primary = (6, 182, 212)    # Mystic Cyan
            star_core = (165, 243, 252)
            gem_col = (34, 211, 238)
            glow_col = (6, 182, 212, 110)
            wand_col = (14, 116, 144)
        elif state == CursorState.HOVER_QUIZ:
            star_primary = (168, 85, 247)   # Magic Purple
            star_core = (233, 213, 255)
            gem_col = (192, 132, 252)
            glow_col = (168, 85, 247, 105)
            wand_col = (126, 34, 206)
        elif state == CursorState.HOVER_BUTTON:
            star_primary = (250, 204, 21)   # Sunburst Gold
            star_core = (254, 249, 195)
            gem_col = (59, 130, 246)        # Sapphire core
            glow_col = (250, 204, 21, 115)
            wand_col = (180, 83, 9)
        else:  # DEFAULT
            star_primary = (250, 204, 21)   # Golden Star
            star_core = (254, 240, 138)
            gem_col = (56, 189, 248)        # Sky Blue core
            glow_col = (250, 204, 21, 80)
            wand_col = (161, 98, 7)

        # 1. Soft Ambient Halo Aura
        star_cx, star_cy = 12, 12
        pygame.draw.circle(surf, glow_col, (star_cx, star_cy), 14)
        pygame.draw.circle(surf, (glow_col[0], glow_col[1], glow_col[2], glow_col[3] // 2), (star_cx, star_cy), 18)

        # 2. Wand Handle (Slanted polished staff angled at 45 degrees)
        # Shadow of handle
        pygame.draw.line(surf, (15, 23, 42, 160), (star_cx + 5, star_cy + 5), (star_cx + 22, star_cy + 22), 4)
        # Main wand shaft
        pygame.draw.line(surf, (15, 23, 42), (star_cx + 4, star_cy + 4), (star_cx + 20, star_cy + 20), 3)
        pygame.draw.line(surf, wand_col, (star_cx + 4, star_cy + 4), (star_cx + 19, star_cy + 19), 2)
        # Metallic silver/gold bands on wand
        pygame.draw.line(surf, (254, 240, 138), (star_cx + 8, star_cy + 8), (star_cx + 9, star_cy + 9), 2)
        pygame.draw.line(surf, (254, 240, 138), (star_cx + 14, star_cy + 14), (star_cx + 15, star_cy + 15), 2)

        # 3. 5-Pointed Star Head
        num_points = 5
        outer_r = 11
        inner_r = 4.8
        star_pts = []
        for i in range(num_points * 2):
            angle = i * math.pi / float(num_points) - math.pi / 2.0
            r = outer_r if i % 2 == 0 else inner_r
            star_pts.append((star_cx + r * math.cos(angle), star_cy + r * math.sin(angle)))

        # Drop shadow of star
        shadow_star = [(px + 1.5, py + 1.5) for px, py in star_pts]
        pygame.draw.polygon(surf, (15, 23, 42, 170), shadow_star)

        # Dark outline for maximum contrast on any background
        pygame.draw.polygon(surf, (15, 23, 42), star_pts)

        # Outer star body
        inner_star_pts = []
        for i in range(num_points * 2):
            angle = i * math.pi / float(num_points) - math.pi / 2.0
            r = (outer_r - 1.2) if i % 2 == 0 else (inner_r - 0.6)
            inner_star_pts.append((star_cx + r * math.cos(angle), star_cy + r * math.sin(angle)))
        pygame.draw.polygon(surf, star_primary, inner_star_pts)

        # Inner highlight core
        highlight_star_pts = []
        for i in range(num_points * 2):
            angle = i * math.pi / float(num_points) - math.pi / 2.0
            r = (outer_r * 0.55) if i % 2 == 0 else (inner_r * 0.45)
            highlight_star_pts.append((star_cx + r * math.cos(angle), star_cy + r * math.sin(angle)))
        pygame.draw.polygon(surf, star_core, highlight_star_pts)

        # Sparkling Jewel Center
        pygame.draw.circle(surf, gem_col, (star_cx, star_cy), 3)
        pygame.draw.circle(surf, (255, 255, 255), (star_cx - 1, star_cy - 1), 1)

        # 4. Contextual State Badges
        if state == CursorState.HOVER_NPC:
            # Cute speech bubble badge
            bx, by = 26, 12
            pygame.draw.ellipse(surf, (255, 255, 255), (bx, by, 15, 12))
            pygame.draw.ellipse(surf, (30, 41, 59), (bx, by, 15, 12), 1)
            pygame.draw.circle(surf, (239, 68, 68), (bx + 4, by + 6), 1)
            pygame.draw.circle(surf, (245, 158, 11), (bx + 7, by + 6), 1)
            pygame.draw.circle(surf, (34, 197, 94), (bx + 10, by + 6), 1)
        elif state == CursorState.HOVER_PORTAL:
            # Swirling cosmic portal ring
            px, py = 26, 12
            pygame.draw.circle(surf, (34, 211, 238), (px, py), 6, 2)
            pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)
        elif state == CursorState.HOVER_QUIZ:
            # Twinkling diamond badge
            qx, qy = 26, 12
            pygame.draw.line(surf, (250, 204, 21), (qx - 5, qy), (qx + 5, qy), 2)
            pygame.draw.line(surf, (250, 204, 21), (qx, qy - 5), (qx, qy + 5), 2)
            pygame.draw.circle(surf, (255, 255, 255), (qx, qy), 2)

        return surf

    def update(self, cursor_pos, current_gesture="NO HAND", fist_start_time=0, click_hold_time=0.22, peace_start_time=0):
        """Update cursor tracking, rainbow motion trail, and particle animations."""
        self.cursor_pos = cursor_pos
        self.current_gesture = current_gesture
        self.fist_start_time = fist_start_time
        self.peace_start_time = peace_start_time
        self.click_hold_time = click_hold_time
        self.anim_t += 0.05

        # Record rainbow stardust motion trail
        now = time.time()
        if now - self.last_trail_time > 0.018:
            self.last_trail_time = now
            self.trail_color_counter = (self.trail_color_counter + 1) % len(RAINBOW_COLORS)
            self.trail.append((cursor_pos[0], cursor_pos[1], now, self.trail_color_counter))

        # Update active ripples
        alive_ripples = []
        for r in self.ripples:
            elapsed = now - r["start_time"]
            if elapsed < r["duration"]:
                alive_ripples.append(r)
        self.ripples = alive_ripples

        # Update celebratory click sparkles
        alive_sparkles = []
        for s in self.click_sparkles:
            s["life"] -= 0.016
            if s["life"] > 0:
                s["x"] += s["vx"]
                s["y"] += s["vy"]
                alive_sparkles.append(s)
        self.click_sparkles = alive_sparkles

    def set_hover_state(self, state):
        """Change contextual hover state."""
        self.current_state = state

    def add_click_ripple(self, pos, ripple_type="move"):
        """
        Spawns a cheerful Grade-2 celebratory click ripple and sparkle burst.
        ripple_type: 'move' (cyan/emerald ping), 'interact' (golden sparkle ping), 'attack' (crimson ping)
        """
        if ripple_type == "interact":
            color = (250, 204, 21)   # Golden Star
        elif ripple_type == "attack":
            color = (239, 68, 68)    # Ruby
        else:
            color = (6, 182, 212)    # Radiant Cyan / Bubble

        now = time.time()
        self.ripples.append({
            "x": pos[0],
            "y": pos[1],
            "start_time": now,
            "duration": 0.35,
            "color": color,
            "type": ripple_type
        })

        # Spawn 6 mini-star sparkle particles around click
        for _ in range(6):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1.2, 2.8)
            self.click_sparkles.append({
                "x": float(pos[0]),
                "y": float(pos[1]),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": random.uniform(0.2, 0.4),
                "max_life": 0.4,
                "color": random.choice(RAINBOW_COLORS),
                "size": random.uniform(2.5, 4.5)
            })

    def draw(self, surface):
        """Draws the magical rainbow motion trail, click sparkles, star wand pointer, and gesture meter."""
        now = time.time()
        cx, cy = self.cursor_pos

        # 1. DRAW ENCHANTING RAINBOW STARDUST MOTION TRAIL
        if len(self.trail) > 1:
            trail_list = list(self.trail)
            for i in range(len(trail_list) - 1):
                p1 = trail_list[i]
                age = now - p1[2]
                if age < 0.28:
                    progress = 1.0 - (age / 0.28)
                    size = max(1, min(5, int(4.5 * progress)))
                    alpha_idx = max(1, min(15, int(progress * 15)))
                    c_idx = p1[3] % len(RAINBOW_COLORS)
                    cached_dot = self._trail_cache.get((c_idx, size, alpha_idx))
                    if cached_dot:
                        surface.blit(cached_dot, (p1[0] - size - 1, p1[1] - size - 1))

        # 2. DRAW CELEBRATORY CLICK SPARKLES
        for s in self.click_sparkles:
            prog = max(0.0, s["life"] / s["max_life"])
            alpha = int(255 * prog)
            r = max(1, int(s["size"] * prog))
            sp_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(sp_surf, (*s["color"], alpha), (r + 1, r + 1), r)
            pygame.draw.circle(sp_surf, (255, 255, 255, alpha), (r + 1, r + 1), max(1, r // 2))
            surface.blit(sp_surf, (int(s["x"]) - r - 1, int(s["y"]) - r - 1))

        # 3. DRAW EXPANDING BUBBLE CLICK RIPPLES
        for r in self.ripples:
            elapsed = now - r["start_time"]
            progress = min(1.0, elapsed / r["duration"])
            alpha = int(240 * (1.0 - progress))
            if alpha <= 0:
                continue

            max_radius = 28
            cur_radius = int(8 + (max_radius - 8) * progress)
            r_surf = pygame.Surface((cur_radius * 2 + 20, cur_radius * 2 + 20), pygame.SRCALPHA)
            rx, ry = cur_radius + 10, cur_radius + 10
            col = r["color"]
            col_rgba = (*col, alpha)

            # Outer expanding glowing bubble ring
            pygame.draw.circle(r_surf, col_rgba, (rx, ry), cur_radius, 2)
            # Inner white starburst ring
            inner_radius = max(2, int(cur_radius * 0.55))
            pygame.draw.circle(r_surf, (255, 255, 255, min(255, alpha + 30)), (rx, ry), inner_radius, 1)

            # 4 Cardinal Star Points (Magical Spark Ring)
            d_dist = cur_radius + 3
            for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
                px = rx + int(math.cos(angle) * d_dist)
                py = ry + int(math.sin(angle) * d_dist)
                pygame.draw.circle(r_surf, (254, 240, 138, alpha), (px, py), 2)

            surface.blit(r_surf, (r["x"] - rx, r["y"] - ry))

        # 4. DRAW RADIAL GESTURE CHARGE METER (FIST OR PEACE HOLD)
        hold_time = 0
        is_charging = False
        charge_col = (250, 204, 21)

        if self.fist_start_time > 0:
            hold_time = now - self.fist_start_time
            is_charging = True
            charge_col = (250, 204, 21)  # Golden Yellow
        elif self.peace_start_time > 0:
            hold_time = now - self.peace_start_time
            is_charging = True
            charge_col = (34, 197, 94)   # Emerald Green

        if is_charging:
            pct = min(1.0, hold_time / max(0.05, self.click_hold_time))
            radius = 22
            meter_surf = self._meter_surf
            meter_surf.fill((0, 0, 0, 0))
            mx = radius + 14
            my = radius + 14

            # Background translucent ring
            pygame.draw.circle(meter_surf, (15, 23, 42, 170), (mx, my), radius, 5)

            # Draw clockwise glowing arc
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
                    pygame.draw.lines(meter_surf, (255, 255, 255), False, arc_pts, 1)

                # Leading glowing star at tip of arc
                tip_a = start_angle + sweep
                tip_x = mx + math.cos(tip_a) * radius
                tip_y = my + math.sin(tip_a) * radius
                pygame.draw.circle(meter_surf, (255, 255, 255), (int(tip_x), int(tip_y)), 3)
                pygame.draw.circle(meter_surf, (*charge_col, 160), (int(tip_x), int(tip_y)), 5)

            surface.blit(meter_surf, (cx - mx + 12, cy - my + 12))

            # Percentage text with friendly drop shadow
            pct_str = f"{int(pct * 100)}%"
            if self.font_pct:
                shadow_surf = self.font_pct.render(pct_str, True, (15, 23, 42))
                pct_surf = self.font_pct.render(pct_str, True, charge_col)
                surface.blit(shadow_surf, (cx - pct_surf.get_width() // 2 + 13, cy + radius + 15))
                surface.blit(pct_surf, (cx - pct_surf.get_width() // 2 + 12, cy + radius + 14))

        # 5. DRAW BASE MAGIC STAR WAND SPRITE
        active_surf = self._pointer_surfs.get(self.current_state, self._pointer_surfs[CursorState.DEFAULT])
        # Position pointer star tip directly at (cx, cy)
        surface.blit(active_surf, (cx - 12, cy - 12))


# Lazy global instance accessor
_game_cursor = None

def get_game_cursor():
    global _game_cursor
    if _game_cursor is None:
        _game_cursor = GameCursor()
    return _game_cursor

class _LazyGameCursorProxy:
    def __getattr__(self, name):
        return getattr(get_game_cursor(), name)

game_cursor = _LazyGameCursorProxy()
