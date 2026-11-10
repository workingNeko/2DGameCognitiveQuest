# core/visual_effects.py
"""
Centralized Visual Juice & Effects Engine for Cognitive Quest 2D.
Provides:
- DustParticleSystem: Organic footstep dust puffs when walking or sprinting.
- SparkleParticleSystem: Radiant glowing sparkles for portals, collectibles, and quest markers.
- ScreenShake: Mathematically accurate physical trauma-based camera shake.
- ObjectPulsing & AuraGlow: Soft sinusoidal breathing glows for interactive items.
- SceneTransition: Smooth alpha fade-to-black and fade-in transitions.
"""

import math
import random
import time
import pygame


_DUST_CACHE = {}
_SPARKLE_CACHE = {}
_AURA_CACHE = {}
_BEACON_CACHE = {}
_PEDESTAL_CACHE = {}
_NPC_BADGE_CACHE = {}


def _maybe_convert_alpha(surf):
    if pygame.display.get_surface() is not None:
        try:
            return surf.convert_alpha()
        except Exception:
            pass
    return surf


class DustParticle:
    """A single dust puff particle that expands and fades out."""
    __slots__ = ('x', 'y', 'vx', 'vy', 'radius', 'max_radius', 'color', 'alpha', 'life', 'max_life')

    def __init__(self, x, y, vx=0.0, vy=0.0, radius=3.0, max_radius=6.0, color=(210, 195, 170), life=0.35):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = float(radius)
        self.max_radius = float(max_radius)
        self.color = color
        self.alpha = 180.0
        self.life = float(life)
        self.max_life = float(life)

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False
        progress = 1.0 - (self.life / self.max_life)
        self.x += self.vx * dt * 60.0
        self.y += self.vy * dt * 60.0
        self.radius = self.radius + (self.max_radius - self.radius) * progress
        self.alpha = max(0.0, 180.0 * (1.0 - progress))
        return True

    def draw(self, surface, camera_offset=(0, 0)):
        if self.alpha <= 0:
            return
        draw_x = int(self.x - camera_offset[0])
        draw_y = int(self.y - camera_offset[1])
        r = max(1, int(self.radius))

        # Check bounds
        sw, sh = surface.get_size()
        if draw_x + r < 0 or draw_x - r > sw or draw_y + r < 0 or draw_y - r > sh:
            return

        has_disp = pygame.display.get_surface() is not None
        alpha_q = max(1, min(15, int(self.alpha) // 12))
        c_q = (self.color[0] & 0xF8, self.color[1] & 0xF8, self.color[2] & 0xF8)
        key = (r, c_q, alpha_q, has_disp)
        dust_surf = _DUST_CACHE.get(key)
        if dust_surf is None:
            dust_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dust_surf, (*c_q, min(255, alpha_q * 12)), (r + 1, r + 1), r)
            dust_surf = _maybe_convert_alpha(dust_surf)
            if len(_DUST_CACHE) > 512:
                _DUST_CACHE.pop(next(iter(_DUST_CACHE)))
            _DUST_CACHE[key] = dust_surf
        surface.blit(dust_surf, (draw_x - r - 1, draw_y - r - 1))


class DustParticleSystem:
    """Manages footstep dust particles with terrain color tinting."""
    def __init__(self, max_particles=60):
        self.particles = []
        self.max_particles = max_particles
        self.spawn_timer = 0.0

    def emit_footstep(self, x, y, direction="down", speed_boost=False, terrain_color=(215, 200, 175)):
        """Emits 2-4 dust puff particles at character feet."""
        count = 4 if speed_boost else 2
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.3, 1.2) * (1.6 if speed_boost else 1.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * 0.5 - 0.2  # slight upward bias
            radius = random.uniform(2.0, 3.5) if not speed_boost else random.uniform(3.0, 5.0)
            max_radius = radius * random.uniform(1.6, 2.2)
            life = random.uniform(0.25, 0.45)
            # Add slight tint jitter
            tint = (
                min(255, max(0, terrain_color[0] + random.randint(-15, 15))),
                min(255, max(0, terrain_color[1] + random.randint(-15, 15))),
                min(255, max(0, terrain_color[2] + random.randint(-15, 15))),
            )
            self.particles.append(DustParticle(
                x + random.uniform(-4, 4),
                y + random.uniform(-2, 2),
                vx=vx,
                vy=vy,
                radius=radius,
                max_radius=max_radius,
                color=tint,
                life=life
            ))

    def update(self, dt):
        alive = []
        for p in self.particles:
            if p.update(dt):
                alive.append(p)
        self.particles = alive

    def draw(self, surface, camera_offset=(0, 0)):
        for p in self.particles:
            p.draw(surface, camera_offset)

    def clear(self):
        self.particles.clear()


class SparkleParticle:
    """A twinkling star or diamond sparkle particle."""
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'color', 'life', 'max_life', 'sparkle_type')

    def __init__(self, x, y, vx=0.0, vy=0.0, size=5.0, color=(255, 220, 100), life=0.6, sparkle_type="cross"):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.size = float(size)
        self.color = color
        self.life = float(life)
        self.max_life = float(life)
        self.sparkle_type = sparkle_type

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False
        self.x += self.vx * dt * 60.0
        self.y += self.vy * dt * 60.0
        return True

    def draw(self, surface, camera_offset=(0, 0)):
        if self.life <= 0:
            return
        draw_x = int(self.x - camera_offset[0])
        draw_y = int(self.y - camera_offset[1])
        sw, sh = surface.get_size()
        if draw_x < -20 or draw_x > sw + 20 or draw_y < -20 or draw_y > sh + 20:
            return

        progress = 1.0 - (self.life / self.max_life)
        # Sinusoidal brightness: starts at 0, peaks at middle, fades to 0
        brightness = math.sin(progress * math.pi)
        alpha = int(255 * brightness)
        current_size = max(1.0, self.size * brightness)

        if alpha <= 5:
            return

        has_disp = pygame.display.get_surface() is not None
        sz_int = max(1, int(current_size))
        alpha_q = max(1, min(16, (alpha + 8) // 16))
        a_val = min(255, alpha_q * 16)
        c_rgb = (self.color[0], self.color[1], self.color[2])
        key = (self.sparkle_type, c_rgb, sz_int, alpha_q, has_disp)
        sparkle_surf = _SPARKLE_CACHE.get(key)
        if sparkle_surf is None:
            sz = sz_int * 2 + 4
            sparkle_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
            cx = sz // 2
            cy = sz // 2
            col = (*c_rgb, a_val)
            if self.sparkle_type == "cross":
                pygame.draw.line(sparkle_surf, col, (cx - sz_int, cy), (cx + sz_int, cy), 1)
                pygame.draw.line(sparkle_surf, col, (cx, cy - sz_int), (cx, cy + sz_int), 1)
                pygame.draw.circle(sparkle_surf, (255, 255, 255, a_val), (cx, cy), max(1, sz_int // 2))
            else:
                pygame.draw.circle(sparkle_surf, col, (cx, cy), sz_int)
                pygame.draw.circle(sparkle_surf, (255, 255, 255, a_val), (cx, cy), max(1, int(sz_int * 0.4)))
            sparkle_surf = _maybe_convert_alpha(sparkle_surf)
            if len(_SPARKLE_CACHE) > 512:
                _SPARKLE_CACHE.pop(next(iter(_SPARKLE_CACHE)))
            _SPARKLE_CACHE[key] = sparkle_surf
        cx = sparkle_surf.get_width() // 2
        surface.blit(sparkle_surf, (draw_x - cx, draw_y - cx))


class SparkleParticleSystem:
    """Manages glistening portal sparkles, item pickups, and achievement bursts."""
    def __init__(self, max_particles=100):
        self.particles = []
        self.max_particles = max_particles

    def spawn_ambient_aura(self, cx, cy, radius=24, color=(255, 215, 0), count=1):
        """Spawns ambient floating sparkles around an interactive center."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(radius * 0.2, radius)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            vy = random.uniform(-0.6, -0.2)  # drifting upwards
            vx = random.uniform(-0.2, 0.2)
            life = random.uniform(0.5, 0.9)
            size = random.uniform(3.0, 6.0)
            stype = random.choice(["cross", "diamond"])
            self.particles.append(SparkleParticle(px, py, vx, vy, size, color, life, stype))

    def spawn_burst(self, cx, cy, count=15, color=(255, 220, 80), speed_range=(1.0, 3.5)):
        """Spawns an explosive burst of outward sparkles."""
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(speed_range[0], speed_range[1])
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.4, 0.75)
            size = random.uniform(3.5, 7.0)
            self.particles.append(SparkleParticle(cx, cy, vx, vy, size, color, life, "cross"))

    def update(self, dt):
        alive = []
        for p in self.particles:
            if p.update(dt):
                alive.append(p)
        self.particles = alive

    def draw(self, surface, camera_offset=(0, 0)):
        for p in self.particles:
            p.draw(surface, camera_offset)

    def clear(self):
        self.particles.clear()


class ScreenShake:
    """
    Physical trauma-based screen shake system.
    Formula: Shake = Trauma^2 * Max_Angle/Offset.
    Provides smooth, natural, high-impact feedback without jarring artifacts.
    """
    def __init__(self, max_offset=12.0, max_angle=0.04, decay_rate=1.8):
        self.trauma = 0.0          # Range [0.0, 1.0]
        self.max_offset = float(max_offset)
        self.max_angle = float(max_angle)
        self.decay_rate = float(decay_rate)
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.angle = 0.0
        self._time = 0.0

    def add_trauma(self, amount):
        """Adds trauma (capped at 1.0). e.g., 0.3 for gentle bump, 0.6 for hit, 1.0 for huge impact."""
        self.trauma = min(1.0, self.trauma + float(amount))

    def update(self, dt):
        if self.trauma <= 0.0:
            self.offset_x = 0.0
            self.offset_y = 0.0
            self.angle = 0.0
            return

        self._time += dt * 45.0  # Frequency
        self.trauma = max(0.0, self.trauma - self.decay_rate * dt)
        shake_intensity = self.trauma * self.trauma

        # 2D Perlin-like pseudo-random displacement using multiple sine harmonics
        self.offset_x = (math.sin(self._time * 1.1) + 0.5 * math.sin(self._time * 2.3)) * self.max_offset * shake_intensity
        self.offset_y = (math.cos(self._time * 1.3) + 0.5 * math.cos(self._time * 2.7)) * self.max_offset * shake_intensity
        self.angle = math.sin(self._time * 0.9) * self.max_angle * shake_intensity

    def get_offset(self):
        """Returns current (dx, dy) pixel translation for camera or rendering offset."""
        return int(round(self.offset_x)), int(round(self.offset_y))


class SceneTransition:
    """
    Smooth alpha fade-to-black and fade-in scene transition manager.
    """
    IDLE = "idle"
    FADING_OUT = "fading_out"  # Screen fades to black
    FADED_BLACK = "faded_black" # Fully black hold
    FADING_IN = "fading_in"   # Screen fades back in

    def __init__(self, screen_size=(800, 600)):
        self.width, self.height = screen_size
        self.state = self.IDLE
        self.timer = 0.0
        self.duration = 0.4
        self.alpha = 0.0
        self.on_faded_callback = None
        self.color = (0, 0, 0)
        self._surf = pygame.Surface(screen_size)

    def start_fade_out(self, duration=0.35, on_faded=None, color=(0, 0, 0)):
        """Begins fading to black."""
        self.state = self.FADING_OUT
        self.duration = max(0.05, duration)
        self.timer = 0.0
        self.alpha = 0.0
        self.on_faded_callback = on_faded
        self.color = color

    def start_fade_in(self, duration=0.35, color=(0, 0, 0)):
        """Begins fading in from black."""
        self.state = self.FADING_IN
        self.duration = max(0.05, duration)
        self.timer = 0.0
        self.alpha = 255.0
        self.color = color

    def update(self, dt):
        if self.state == self.IDLE:
            return

        self.timer += dt
        progress = min(1.0, self.timer / self.duration)

        if self.state == self.FADING_OUT:
            # Smoothstep curve for premium feel
            smooth = progress * progress * (3.0 - 2.0 * progress)
            self.alpha = smooth * 255.0
            if progress >= 1.0:
                self.alpha = 255.0
                self.state = self.FADED_BLACK
                if self.on_faded_callback:
                    cb = self.on_faded_callback
                    self.on_faded_callback = None
                    cb()

        elif self.state == self.FADING_IN:
            smooth = progress * progress * (3.0 - 2.0 * progress)
            self.alpha = (1.0 - smooth) * 255.0
            if progress >= 1.0:
                self.alpha = 0.0
                self.state = self.IDLE

    def draw(self, surface):
        if self.alpha <= 0.0 or self.state == self.IDLE:
            return
        if surface.get_size() != (self.width, self.height):
            self.width, self.height = surface.get_size()
            self._surf = pygame.Surface((self.width, self.height))

        self._surf.fill(self.color)
        self._surf.set_alpha(int(self.alpha))
        surface.blit(self._surf, (0, 0))

    def is_active(self):
        return self.state != self.IDLE


def get_pulse_value(frequency=2.0, min_val=0.75, max_val=1.0, offset=0.0):
    """Calculates a smooth sinusoidal pulse value between min_val and max_val."""
    t = time.time() * frequency + offset
    sine = (math.sin(t) + 1.0) * 0.5
    return min_val + (max_val - min_val) * sine


def draw_aura_glow(surface, center, radius=24, color=(255, 215, 0), pulse=True, pulse_speed=2.5, pulse_range=(0.7, 1.0)):
    """
    Renders a soft, glowing radial aura underneath interactive NPCs, portals, or stations.
    """
    cx, cy = int(center[0]), int(center[1])
    scale = get_pulse_value(frequency=pulse_speed, min_val=pulse_range[0], max_val=pulse_range[1]) if pulse else 1.0
    r = max(4, int(radius * scale))

    sw, sh = surface.get_size()
    if cx + r < 0 or cx - r > sw or cy + r < 0 or cy - r > sh:
        return

    has_disp = pygame.display.get_surface() is not None
    c_rgb = (color[0], color[1], color[2])
    key = (r, c_rgb, has_disp)
    glow_surf = _AURA_CACHE.get(key)
    if glow_surf is None:
        glow_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        center_surf = (r + 2, r + 2)
        pygame.draw.circle(glow_surf, (*c_rgb, 35), center_surf, r)
        pygame.draw.circle(glow_surf, (*c_rgb, 70), center_surf, int(r * 0.65))
        pygame.draw.circle(glow_surf, (*c_rgb, 120), center_surf, int(r * 0.35))
        glow_surf = _maybe_convert_alpha(glow_surf)
        if len(_AURA_CACHE) > 256:
            _AURA_CACHE.pop(next(iter(_AURA_CACHE)))
        _AURA_CACHE[key] = glow_surf

    surface.blit(glow_surf, (cx - r - 2, cy - r - 2))


def draw_beacon_marker(surface, cx, cy, color=(255, 215, 0), beacon_type="exclamation", offset_y=-35):
    """
    Renders an animated floating quest marker / beacon above an NPC or interactive station.
    Features high-contrast dual border, pointer arrow chevron, and radiant pulsing aura.
    """
    cx, cy = int(cx), int(cy)
    float_y = cy + offset_y + int(math.sin(time.time() * 4.2) * 5)
    # Multi-tier radiant glow halo
    draw_aura_glow(surface, (cx, float_y), radius=18, color=color, pulse=True, pulse_speed=3.6)

    sz = 19
    pad = 4
    pw, ph = (sz + pad) * 2, (sz + pad) * 2 + 6
    bcx, bcy = pw // 2, sz + pad
    has_disp = pygame.display.get_surface() is not None
    c_rgb = (color[0], color[1], color[2])
    key = (c_rgb, beacon_type, has_disp)
    badge_surf = _BEACON_CACHE.get(key)
    if badge_surf is None:
        badge_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        # 1. Drop shadow offset
        shadow_pts = [
            (bcx, bcy - sz + 2),
            (bcx + sz, bcy + 2),
            (bcx, bcy + sz + 6),
            (bcx - sz, bcy + 2)
        ]
        pygame.draw.polygon(badge_surf, (0, 0, 0, 95), shadow_pts)

        # 2. Main diamond badge points + bottom pointer arrow
        diamond_pts = [
            (bcx, bcy - sz),
            (bcx + sz, bcy),
            (bcx, bcy + sz),
            (bcx - sz, bcy)
        ]
        # Outer dark high-contrast contour
        pygame.draw.polygon(badge_surf, (15, 23, 42, 240), diamond_pts)
        # Vibrant core fill
        pygame.draw.polygon(badge_surf, (*c_rgb, 245), [
            (bcx, bcy - sz + 2),
            (bcx + sz - 2, bcy),
            (bcx, bcy + sz - 2),
            (bcx - sz + 2, bcy)
        ])
        # Inner white highlight border
        pygame.draw.polygon(badge_surf, (255, 255, 255, 230), [
            (bcx, bcy - sz + 2),
            (bcx + sz - 2, bcy),
            (bcx, bcy + sz - 2),
            (bcx - sz + 2, bcy)
        ], 2)

        # 3. Downward pointer chevron tip at bottom
        pointer_pts = [
            (bcx - 5, bcy + sz - 2),
            (bcx + 5, bcy + sz - 2),
            (bcx, bcy + sz + 6)
        ]
        pygame.draw.polygon(badge_surf, (15, 23, 42, 240), pointer_pts)
        pygame.draw.polygon(badge_surf, (*c_rgb, 245), [
            (bcx - 3, bcy + sz - 2),
            (bcx + 3, bcy + sz - 2),
            (bcx, bcy + sz + 4)
        ])

        # 4. Bold, crisp iconography
        dark_ink = (20, 20, 30)
        if beacon_type == "exclamation":
            pygame.draw.line(badge_surf, dark_ink, (bcx, bcy - 8), (bcx, bcy + 1), 3)
            pygame.draw.circle(badge_surf, dark_ink, (bcx, bcy + 6), 2)
        elif beacon_type == "question":
            pygame.draw.circle(badge_surf, dark_ink, (bcx, bcy + 6), 2)
            pygame.draw.arc(badge_surf, dark_ink, pygame.Rect(bcx - 5, bcy - 9, 10, 10), 0, math.pi, 3)
            pygame.draw.line(badge_surf, dark_ink, (bcx, bcy - 4), (bcx, bcy + 2), 3)
        elif beacon_type == "check":
            # Crisp high-contrast checkmark marker for correct question answer
            p1 = (bcx - 6, bcy + 1)
            p2 = (bcx - 1, bcy + 6)
            p3 = (bcx + 7, bcy - 5)
            pygame.draw.lines(badge_surf, (255, 255, 255), False, [p1, p2, p3], 4)
            pygame.draw.lines(badge_surf, dark_ink, False, [p1, p2, p3], 2)
        elif beacon_type == "cross":
            # Red/dark cross for incorrect attempt
            pygame.draw.line(badge_surf, (255, 255, 255), (bcx - 5, bcy - 5), (bcx + 5, bcy + 5), 4)
            pygame.draw.line(badge_surf, (255, 255, 255), (bcx + 5, bcy - 5), (bcx - 5, bcy + 5), 4)
            pygame.draw.line(badge_surf, dark_ink, (bcx - 5, bcy - 5), (bcx + 5, bcy + 5), 2)
            pygame.draw.line(badge_surf, dark_ink, (bcx + 5, bcy - 5), (bcx - 5, bcy + 5), 2)

        badge_surf = _maybe_convert_alpha(badge_surf)
        _BEACON_CACHE[key] = badge_surf

    surface.blit(badge_surf, (cx - bcx, float_y - bcy))


def draw_npc_ground_pedestal(surface, cx, cy, rx=18, ry=8, is_active=False, color=(255, 215, 0), pulse_phase=0.0):
    """
    Renders an optimized, memoized grounding shadow and interactive pedestal ring beneath an NPC.
    Separates pixel art characters from background floor tiles and highlights quest targets.
    """
    cx, cy = int(cx), int(cy)
    sw, sh = surface.get_size()
    if cx + rx + 10 < 0 or cx - rx - 10 > sw or cy + ry + 10 < 0 or cy - ry - 10 > sh:
        return

    has_disp = pygame.display.get_surface() is not None
    c_rgb = (color[0], color[1], color[2])

    if is_active:
        # Pre-cache 8 discrete pulse phases to eliminate runtime surface creation on low-spec hardware
        pulse_idx = int((((math.sin(pulse_phase) + 1.0) * 0.5) * 7.99))
        key = ("active", rx, ry, c_rgb, pulse_idx, has_disp)
        pedestal_surf = _PEDESTAL_CACHE.get(key)
        if pedestal_surf is None:
            pad = 8
            pw, ph = (rx + pad) * 2, (ry + pad) * 2
            pedestal_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pcx, pcy = pw // 2, ph // 2
            # 1. Base dark ground contact shadow
            pygame.draw.ellipse(pedestal_surf, (0, 0, 0, 110), (pcx - rx, pcy - ry, rx * 2, ry * 2))
            # 2. Glowing pulse outer ring
            scale = 0.9 + 0.25 * (pulse_idx / 7.0)
            p_alpha = int(75 + 115 * (pulse_idx / 7.0))
            prx, pry = max(2, int(rx * scale)), max(2, int(ry * scale))
            pygame.draw.ellipse(pedestal_surf, (*c_rgb, p_alpha // 2), (pcx - prx - 2, pcy - pry - 2, (prx + 2) * 2, (pry + 2) * 2))
            pygame.draw.ellipse(pedestal_surf, (*c_rgb, p_alpha), (pcx - prx, pcy - pry, prx * 2, pry * 2), 2)
            # 3. Bright inner accent ring
            pygame.draw.ellipse(pedestal_surf, (255, 255, 255, min(255, p_alpha + 40)), (pcx - rx + 3, pcy - ry + 2, (rx - 3) * 2, (ry - 2) * 2), 1)
            pedestal_surf = _maybe_convert_alpha(pedestal_surf)
            if len(_PEDESTAL_CACHE) > 256:
                _PEDESTAL_CACHE.pop(next(iter(_PEDESTAL_CACHE)))
            _PEDESTAL_CACHE[key] = pedestal_surf
        surface.blit(pedestal_surf, (cx - pedestal_surf.get_width() // 2, cy - pedestal_surf.get_height() // 2))
    else:
        # Muted ambient ground pedestal for upcoming / idle interactive NPCs
        key = ("ambient", rx, ry, c_rgb, has_disp)
        pedestal_surf = _PEDESTAL_CACHE.get(key)
        if pedestal_surf is None:
            pad = 4
            pw, ph = (rx + pad) * 2, (ry + pad) * 2
            pedestal_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            pcx, pcy = pw // 2, ph // 2
            # Base dark ground shadow
            pygame.draw.ellipse(pedestal_surf, (0, 0, 0, 95), (pcx - rx, pcy - ry, rx * 2, ry * 2))
            # Soft subtle ambient interactive ring
            pygame.draw.ellipse(pedestal_surf, (*c_rgb, 60), (pcx - rx + 1, pcy - ry + 1, (rx - 1) * 2, (ry - 1) * 2), 1)
            pedestal_surf = _maybe_convert_alpha(pedestal_surf)
            if len(_PEDESTAL_CACHE) > 256:
                _PEDESTAL_CACHE.pop(next(iter(_PEDESTAL_CACHE)))
            _PEDESTAL_CACHE[key] = pedestal_surf
        surface.blit(pedestal_surf, (cx - pedestal_surf.get_width() // 2, cy - pedestal_surf.get_height() // 2))


def draw_npc_overhead_badge(surface, cx, top_y, text, is_active=False, badge_color=(255, 215, 0), offset_y=-12):
    """
    Renders a crisp, pre-cached floating name / station pill tag above an NPC.
    """
    if not text:
        return
    cx, top_y = int(cx), int(top_y)
    sw, sh = surface.get_size()
    if cx + 120 < 0 or cx - 120 > sw or top_y + 40 < 0 or top_y - 60 > sh:
        return

    has_disp = pygame.display.get_surface() is not None
    clean_text = str(text).strip()
    if len(clean_text) > 24:
        clean_text = clean_text[:22] + ".."
    c_rgb = (badge_color[0], badge_color[1], badge_color[2])
    key = (clean_text, is_active, c_rgb, has_disp)

    badge_surf = _NPC_BADGE_CACHE.get(key)
    if badge_surf is None:
        from .font_manager import get_font
        font = get_font("Comic Sans MS", 11, bold=True)
        is_cleared = "✓" in clean_text or "Correct" in clean_text
        display_str = f"★ {clean_text}" if (is_active and not is_cleared) else clean_text

        if is_cleared:
            text_color = (240, 253, 244)
            bg_color = (6, 78, 59, 230)
            border_color = (74, 222, 128, 255)
            border_width = 2
        elif is_active:
            text_color = (254, 240, 138)
            bg_color = (15, 23, 42, 215)
            border_color = (*c_rgb, 240)
            border_width = 2
        else:
            text_color = (241, 245, 249)
            bg_color = (15, 23, 42, 160)
            border_color = (148, 163, 184, 140)
            border_width = 1

        t_surf = font.render(display_str, True, text_color)
        tw, th = t_surf.get_size()
        pw, ph = tw + 14, th + 6
        badge_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        # Background pill
        pygame.draw.rect(badge_surf, bg_color, (0, 0, pw, ph), border_radius=ph // 2)
        # Border
        pygame.draw.rect(badge_surf, border_color, (0, 0, pw, ph), width=border_width, border_radius=ph // 2)
        # Text
        badge_surf.blit(t_surf, (7, 3))
        badge_surf = _maybe_convert_alpha(badge_surf)
        if len(_NPC_BADGE_CACHE) > 256:
            _NPC_BADGE_CACHE.pop(next(iter(_NPC_BADGE_CACHE)))
        _NPC_BADGE_CACHE[key] = badge_surf

    bw = badge_surf.get_width()
    bh = badge_surf.get_height()
    surface.blit(badge_surf, (cx - bw // 2, top_y + offset_y - bh))


def build_composite_title_letters(title_text, title_font, main_color, outline_color, glow_color, pad=6):
    """
    Pre-bakes each letter's glow + outline + main glyph onto a single padded SRCALPHA surface once at load time.
    Eliminates 3 .copy() heap allocations and 9-26 blits per letter per frame on AMD A4-6300.
    """
    letters = []
    for ch in title_text:
        glow = title_font.render(ch, False, glow_color)
        outline = title_font.render(ch, False, outline_color)
        main = title_font.render(ch, False, main_color)
        w, h = main.get_size()
        comp = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        glow_copy = glow.copy()
        glow_copy.set_alpha(51)
        for gx, gy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, -3), (-3, 3), (3, 3)):
            comp.blit(glow_copy, (pad + gx, pad + gy))
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)):
            comp.blit(outline, (pad + ox, pad + oy))
        comp.blit(main, (pad, pad))
        comp = _maybe_convert_alpha(comp)
        letters.append({
            "comp": comp,
            "main": main,
            "pad": pad,
            "width": w,
            "last_alpha": 255,
        })
    return letters


def draw_composite_title_wave(surface, title_letters, title_total_width, title_spacing, pixel_font_size, timer):
    """Draws the animated area title wave using 1 blit per letter and zero heap allocations."""
    sw, sh = surface.get_size()
    alpha = 255
    if timer >= 4.0:
        fade = max(0.0, min(1.0, (timer - 4.0) / 1.0))
        alpha = int(255 * (1.0 - fade))
    if alpha <= 0:
        return

    base_y = sh // 2 - pixel_font_size // 2
    if timer < 0.35:
        t = timer / 0.35
        ease = 1.0 - (1.0 - t) ** 3
        y = base_y - (1.0 - ease) * 40
    else:
        y = base_y

    x = sw // 2 - title_total_width // 2
    for i, data in enumerate(title_letters):
        phase = timer * 8.0 - i * 0.55
        offset = math.sin(phase) * 12.0 if -math.pi <= phase <= math.pi else 0.0
        comp = data["comp"]
        if data.get("last_alpha", 255) != alpha:
            comp.set_alpha(alpha)
            data["last_alpha"] = alpha
        pad = data["pad"]
        surface.blit(comp, (int(x - pad), int(y + offset - pad)))
        x += data["width"] + title_spacing

