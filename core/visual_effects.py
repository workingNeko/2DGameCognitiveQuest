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

        dust_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        col = (*self.color, int(self.alpha))
        pygame.draw.circle(dust_surf, col, (r + 1, r + 1), r)
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

        sz = int(current_size * 2) + 4
        sparkle_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        cx = sz // 2
        cy = sz // 2
        col = (*self.color, alpha)

        if self.sparkle_type == "cross":
            # 4-pointed star cross
            arm = int(current_size)
            pygame.draw.line(sparkle_surf, col, (cx - arm, cy), (cx + arm, cy), 1)
            pygame.draw.line(sparkle_surf, col, (cx, cy - arm), (cx, cy + arm), 1)
            pygame.draw.circle(sparkle_surf, (255, 255, 255, alpha), (cx, cy), max(1, arm // 2))
        else:
            # Soft glowing diamond / circle
            pygame.draw.circle(sparkle_surf, col, (cx, cy), max(1, int(current_size)))
            pygame.draw.circle(sparkle_surf, (255, 255, 255, alpha), (cx, cy), max(1, int(current_size * 0.4)))

        surface.blit(sparkle_surf, (draw_x - cx, draw_y - cy))


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

    glow_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
    center_surf = (r + 2, r + 2)

    # 3-layer gradient falloff
    pygame.draw.circle(glow_surf, (*color, 35), center_surf, r)
    pygame.draw.circle(glow_surf, (*color, 70), center_surf, int(r * 0.65))
    pygame.draw.circle(glow_surf, (*color, 120), center_surf, int(r * 0.35))

    surface.blit(glow_surf, (cx - r - 2, cy - r - 2))


def draw_beacon_marker(surface, cx, cy, color=(255, 215, 0), beacon_type="exclamation", offset_y=-35):
    """
    Renders an animated floating quest marker / beacon above an NPC or interactive station.
    """
    float_y = cy + offset_y + int(math.sin(time.time() * 3.5) * 4)
    draw_aura_glow(surface, (cx, float_y), radius=14, color=color, pulse=True, pulse_speed=3.0)

    # Draw marker diamond badge
    sz = 16
    badge_surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
    bcx, bcy = sz, sz
    
    diamond_pts = [
        (bcx, bcy - sz + 2),
        (bcx + sz - 2, bcy),
        (bcx, bcy + sz - 2),
        (bcx - sz + 2, bcy)
    ]
    pygame.draw.polygon(badge_surf, (*color, 230), diamond_pts)
    pygame.draw.polygon(badge_surf, (255, 255, 255, 255), diamond_pts, 2)

    # Inner symbol
    if beacon_type == "exclamation":
        pygame.draw.line(badge_surf, (20, 20, 25), (bcx, bcy - 6), (bcx, bcy + 1), 2)
        pygame.draw.circle(badge_surf, (20, 20, 25), (bcx, bcy + 5), 1)
    elif beacon_type == "question":
        # Question mark dot
        pygame.draw.circle(badge_surf, (20, 20, 25), (bcx, bcy + 5), 1)
        pygame.draw.arc(badge_surf, (20, 20, 25), pygame.Rect(bcx - 4, bcy - 7, 8, 8), 0, math.pi, 2)
        pygame.draw.line(badge_surf, (20, 20, 25), (bcx, bcy - 3), (bcx, bcy + 2), 2)

    surface.blit(badge_surf, (cx - bcx, float_y - bcy))
