# core/vector_icons.py
"""
Native Pygame Vector Iconography Engine.
Draws crisp, mathematically accurate geometric icons (lightbulbs, stars,
arrows, replay arcs, and gems) directly onto Pygame surfaces.
Completely immune to font glyph missing-character boxes ('tofu').
"""

import math
import pygame


def draw_vector_star(surface, cx, cy, radius=8, color=(255, 215, 0), outline_color=(255, 255, 255), num_points=5):
    """
    Renders a mathematically sharp, symmetrical star polygon with an optional highlight rim.
    """
    points = []
    total_vertices = num_points * 2
    for i in range(total_vertices):
        angle = i * math.pi / float(num_points) - math.pi / 2.0
        r = radius if i % 2 == 0 else radius * 0.42
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    pygame.draw.polygon(surface, color, points)
    if outline_color:
        pygame.draw.polygon(surface, outline_color, points, 1)


def draw_vector_lightbulb(surface, cx, cy, size=7, glow=True):
    """
    Renders an amber radiant incandescent lightbulb with a glowing halo and screw base.
    """
    cx, cy = int(cx), int(cy)
    size = max(4, int(size))

    # Optional soft ambient glow
    if glow:
        glow_r = int(size * 1.5)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (251, 191, 36, 45), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (cx - glow_r, cy - 2 - glow_r))

    # Main rounded bulb head (Amber/Gold)
    pygame.draw.circle(surface, (251, 191, 36), (cx, cy - 2), size)
    # Bright shine highlight reflection
    highlight_r = max(1, size // 3)
    pygame.draw.circle(surface, (254, 240, 138), (cx - max(1, size // 3), cy - 2 - max(1, size // 3)), highlight_r)

    # Metallic screw base (Slate gray with subtle threading)
    base_w = max(3, int(size * 0.85))
    base_h = max(3, int(size * 0.6))
    base_x = cx - base_w // 2
    base_y = cy - 2 + int(size * 0.7)

    pygame.draw.rect(surface, (148, 163, 184), (base_x, base_y, base_w, base_h), border_radius=1)
    pygame.draw.line(surface, (100, 116, 139), (base_x, base_y + base_h // 2), (base_x + base_w - 1, base_y + base_h // 2), 1)

    # Contact point bottom tip
    pygame.draw.circle(surface, (71, 85, 105), (cx, base_y + base_h), max(1, base_w // 4))


def draw_vector_arrow(surface, cx, cy, size=10, direction="right", color=(255, 255, 255), line_width=2):
    """
    Renders a sleek action arrow with a shaft and triangular head.
    """
    cx, cy = int(cx), int(cy)
    half = max(3, int(size // 2))

    if direction == "right":
        pygame.draw.line(surface, color, (cx - half, cy), (cx + half - 2, cy), line_width)
        head_pts = [
            (cx + half - 5, cy - 4),
            (cx + half, cy),
            (cx + half - 5, cy + 4)
        ]
        pygame.draw.polygon(surface, color, head_pts)
    elif direction == "left":
        pygame.draw.line(surface, color, (cx - half + 2, cy), (cx + half, cy), line_width)
        head_pts = [
            (cx - half + 5, cy - 4),
            (cx - half, cy),
            (cx - half + 5, cy + 4)
        ]
        pygame.draw.polygon(surface, color, head_pts)
    elif direction == "down":
        pygame.draw.line(surface, color, (cx, cy - half), (cx, cy + half - 2), line_width)
        head_pts = [
            (cx - 4, cy + half - 5),
            (cx, cy + half),
            (cx + 4, cy + half - 5)
        ]
        pygame.draw.polygon(surface, color, head_pts)


def draw_vector_replay(surface, cx, cy, radius=7, color=(255, 255, 255), line_width=2):
    """
    Renders a 270-degree circular restart arc with an integrated arrow head.
    """
    cx, cy = int(cx), int(cy)
    radius = max(4, int(radius))

    arc_rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    # 270-degree arc from ~30 degrees to ~315 degrees
    pygame.draw.arc(surface, color, arc_rect, 0.5, 5.5, line_width)

    # Arrowhead at top-right tip of arc
    tip_angle = 0.5
    tip_x = cx + radius * math.cos(tip_angle)
    tip_y = cy - radius * math.sin(tip_angle)

    head_pts = [
        (tip_x - 3, tip_y - 4),
        (tip_x + 3, tip_y),
        (tip_x - 3, tip_y + 4)
    ]
    pygame.draw.polygon(surface, color, head_pts)


def draw_vector_gem(surface, cx, cy, radius=6, color=(251, 191, 36), highlight_color=(254, 240, 138)):
    """
    Renders a 4-pointed diamond sparkle gem with internal facets and highlight.
    """
    cx, cy = int(cx), int(cy)
    r = max(3, int(radius))
    narrow_r = max(2, int(r * 0.55))

    pts = [
        (cx, cy - r),
        (cx + narrow_r, cy),
        (cx, cy + r),
        (cx - narrow_r, cy)
    ]
    pygame.draw.polygon(surface, color, pts)
    if highlight_color:
        pygame.draw.polygon(surface, highlight_color, pts, 1)
