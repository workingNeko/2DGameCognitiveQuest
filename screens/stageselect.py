# screens/stageselect.py - UPDATED with image-based back button

import pygame
import math
import random
import sys
import os

# ============================================================
# CONSTANTS
# ============================================================
FPS = 60
DT = 1 / FPS  # Fixed delta time

# ============================================================
# COLORS
# ============================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BG_TOP = (50, 120, 255)
BG_BOTTOM = (20, 40, 120)

LOCKED = (120, 120, 120)

PATH = (90, 90, 130)
PATH_ACTIVE = (255, 220, 120)

QUARTER_COLORS = [
    (255, 140, 0),
    (50, 205, 50),
    (65, 105, 225),
    (186, 85, 211),
]


# ============================================================
# HELPERS
# ============================================================
def lerp(a, b, t):
    return a + (b - a) * t


def ease_out(t):
    return 1 - (1 - t) * (1 - t)


# ============================================================
# PARTICLES
# ============================================================
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 6)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.life = 1.0
        self.size = random.randint(3, 7)

        self.color = random.choice([
            (255, 255, 255),
            (255, 215, 0),
            (255, 120, 120),
            (120, 255, 255),
            (255, 200, 100)
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= DT * 1.2

    def draw(self, screen):
        if self.life <= 0:
            return

        alpha = int(255 * self.life)
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(
            surf,
            (*self.color, alpha),
            (10, 10),
            self.size
        )
        screen.blit(surf, (self.x - 10, self.y - 10))


# ============================================================
# PARTICLE SYSTEM
# ============================================================
class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, amount=40):
        for _ in range(amount):
            self.particles.append(Particle(x, y))

    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)


# ============================================================
# QUARTER NODE
# ============================================================
class QuarterNode:
    def __init__(self, parent, x, y, index, title, color):
        self.parent = parent
        self.x = x
        self.y = y
        self.index = index
        self.title = title
        self.color = color

        self.unlocked = False
        self.completed = False

        self.scale = 1.0
        self.hover = False

        self.unlock_anim = 0.0
        self.click_anim = 0.0

    def unlock(self):
        self.unlocked = True
        self.unlock_anim = 1.0

    def get_rect(self):
        size = int(130 * self.scale)
        return pygame.Rect(
            self.x - size // 2,
            self.y - size // 2,
            size,
            size
        )

    def update(self, mouse_pos):
        # Hover effect
        self.hover = self.get_rect().collidepoint(mouse_pos)
        target_scale = 1.1 if self.hover else 1.0
        self.scale += (target_scale - self.scale) * 8 * DT

        # Decay animations
        self.unlock_anim = max(0.0, self.unlock_anim - DT * 2)
        self.click_anim = max(0.0, self.click_anim - DT * 3)

    def on_click(self, particle_system):
        if self.unlocked:
            self.click_anim = 0.5
            particle_system.burst(self.x, self.y, 80)
            print(f"✨ Quarter {self.index} selected! ✨")
            return True
        else:
            particle_system.burst(self.x, self.y, 20)
            print(f"🔒 Quarter {self.index} is locked!")
            return False

    def draw(self, screen):
        rect = self.get_rect()
        color = self.color if self.unlocked else LOCKED

        # UNLOCK GLOW EFFECT
        if self.unlock_anim > 0:
            glow_size = int(180 * self.unlock_anim)
            glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow,
                (255, 255, 180, 70),
                (glow_size, glow_size),
                glow_size
            )
            screen.blit(glow, (self.x - glow_size, self.y - glow_size))

        # CLICK PULSE EFFECT
        if self.click_anim > 0:
            pulse_scale = 1 + (self.click_anim * 0.3)
            pulse_size = int(130 * pulse_scale)
            pulse_rect = pygame.Rect(
                self.x - pulse_size // 2,
                self.y - pulse_size // 2,
                pulse_size,
                pulse_size
            )
            pygame.draw.rect(
                screen,
                (255, 255, 255),
                pulse_rect,
                4,
                border_radius=30
            )

        # SHADOW
        shadow_rect = rect.move(0, 8)
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=30)

        # MAIN BUTTON
        pygame.draw.rect(screen, color, rect, border_radius=30)
        pygame.draw.rect(screen, WHITE, rect, 5, border_radius=30)

        # QUARTER NUMBER
        num_text = self.parent.quarter_font.render(str(self.index), True, WHITE)
        num_rect = num_text.get_rect(center=(self.x, self.y - 15))
        screen.blit(num_text, num_rect)

        # TITLE LABEL
        label = self.parent.small_font.render(self.title, True, WHITE)
        label_rect = label.get_rect(center=(self.x, self.y + 35))
        screen.blit(label, label_rect)


# ============================================================
# PATH SYSTEM
# ============================================================
class PathSystem:
    def __init__(self, stages):
        self.stages = stages
        self.progress = 0.0
        self.target = 0
        self.energy_particles = []

    def unlock_next(self):
        if self.target < len(self.stages) - 1:
            self.target += 1
            return True
        return False

    def update(self):
        # Smooth progress interpolation
        self.progress += (self.target - self.progress) * 5 * DT

        # Add occasional energy particles
        if random.random() < 0.25 and self.progress > 0:
            x, y = self.get_pos()
            self.energy_particles.append(Particle(x, y))

        # Update energy particles
        self.energy_particles = [p for p in self.energy_particles if p.life > 0]
        for p in self.energy_particles:
            p.update()

    def get_pos(self):
        i = int(self.progress)
        t = self.progress - i

        if i >= len(self.stages) - 1:
            i = len(self.stages) - 2
            t = 1.0

        a = self.stages[i]
        b = self.stages[i + 1]
        t = ease_out(t)

        x = lerp(a.x, b.x, t)
        y = lerp(a.y, b.y, t)
        return x, y

    def draw(self, screen):
        # BASE PATH
        for i in range(len(self.stages) - 1):
            a = self.stages[i]
            b = self.stages[i + 1]
            pygame.draw.line(screen, PATH, (a.x, a.y), (b.x, b.y), 14)

        # ACTIVE PATH
        for i in range(int(self.progress)):
            if i < len(self.stages) - 1:
                a = self.stages[i]
                b = self.stages[i + 1]
                pygame.draw.line(screen, PATH_ACTIVE, (a.x, a.y), (b.x, b.y), 10)

        # Partial active path segment
        if self.progress > 0 and self.progress < len(self.stages) - 1:
            i = int(self.progress)
            t = self.progress - i
            a = self.stages[i]
            b = self.stages[i + 1]
            partial_x = lerp(a.x, b.x, t)
            partial_y = lerp(a.y, b.y, t)
            pygame.draw.line(screen, PATH_ACTIVE, (a.x, a.y), (partial_x, partial_y), 10)

        # ENERGY BALL
        if self.progress > 0:
            x, y = self.get_pos()
            pygame.draw.circle(screen, (255, 255, 200, 100), (int(x), int(y)), 18)
            pygame.draw.circle(screen, (255, 255, 120), (int(x), int(y)), 12)
            pygame.draw.circle(screen, WHITE, (int(x), int(y)), 6)

        # ENERGY PARTICLES
        for p in self.energy_particles:
            p.draw(screen)


# ============================================================
# STAGE SELECT - WITH IMAGE BACK BUTTON
# ============================================================
class StageSelect:
    def __init__(self, screen, main_menu=None):
        self.screen = screen
        self.main_menu = main_menu
        self.w, self.h = screen.get_size()

        # FONTS
        self.title_font = pygame.font.SysFont("Comic Sans MS", 60, bold=True)
        self.quarter_font = pygame.font.SysFont("Comic Sans MS", 34, bold=True)
        self.small_font = pygame.font.SysFont("Comic Sans MS", 20)

        # ====================================================
        # LOAD BACK BUTTON IMAGE (same as main_menu)
        # ====================================================
        self.back_image = None
        exit_btn_path = os.path.join("assets", "images", "exitbutton.png")

        if os.path.exists(exit_btn_path):
            try:
                self.back_image = pygame.image.load(exit_btn_path).convert_alpha()
                # Scale to reasonable size (matching main_menu)
                self.back_image = pygame.transform.scale(self.back_image, (200, 70))
                self.back_btn_rect = self.back_image.get_rect(topleft=(30, 30))
                self.use_image_button = True
                print("✅ Exit button image loaded for StageSelect")
            except Exception as e:
                print(f"Failed to load exit button image: {e}")
                self.use_image_button = False
                self.back_btn_rect = pygame.Rect(30, 30, 170, 55)
        else:
            print(f"Exit button image not found at: {exit_btn_path}")
            self.use_image_button = False
            self.back_btn_rect = pygame.Rect(30, 30, 200, 70)

        # GESTURE SYSTEM
        self.cursor_pos = (self.w // 2, self.h // 2)
        self.current_gesture = "NO HAND"
        self.fist_triggered = False
        self.fist_hold_timer = 0.0
        self.CLICK_HOLD_TIME = 0.9
        self.fist_start_time = 0

        # CURSOR SPEED BOOST
        self.cursor_speed_multiplier = 2.2
        self.last_cursor_pos = self.cursor_pos

        # QUARTERS POSITIONS
        center_x = self.w // 2
        self.quarters = [
            QuarterNode(self, center_x - 420, 420, 1, "1st Quarter", QUARTER_COLORS[0]),
            QuarterNode(self, center_x - 140, 260, 2, "2nd Quarter", QUARTER_COLORS[1]),
            QuarterNode(self, center_x + 140, 420, 3, "3rd Quarter", QUARTER_COLORS[2]),
            QuarterNode(self, center_x + 420, 260, 4, "4th Quarter", QUARTER_COLORS[3]),
        ]

        # First quarter unlocked by default
        self.quarters[0].unlock()

        # SYSTEMS
        self.path_system = PathSystem(self.quarters)
        self.particles = ParticleSystem()

        # Gesture unlock tracking
        self.unlock_hold_timer = 0.0
        self.UNLOCK_HOLD_TIME = 1.0

        print("✅ StageSelect initialized successfully!")

    # ========================================================
    # UPDATE GESTURE DATA - MATCHES main_menu.py CALL SIGNATURE
    # ========================================================
    def update_gesture(self, cursor_pos, fist_start_time, CLICK_HOLD_TIME, current_gesture):
        """Update gesture data - matches the call from main_menu.py"""
        # Store these values even if not used directly
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = CLICK_HOLD_TIME

        # Apply speed multiplier for responsive cursor
        if self.last_cursor_pos != cursor_pos:
            dx = cursor_pos[0] - self.last_cursor_pos[0]
            dy = cursor_pos[1] - self.last_cursor_pos[1]
            boosted_x = self.last_cursor_pos[0] + dx * self.cursor_speed_multiplier
            boosted_y = self.last_cursor_pos[1] + dy * self.cursor_speed_multiplier
            boosted_x = max(10, min(self.w - 10, boosted_x))
            boosted_y = max(10, min(self.h - 10, boosted_y))
            self.cursor_pos = (boosted_x, boosted_y)
            self.last_cursor_pos = cursor_pos
        else:
            self.cursor_pos = cursor_pos
            self.last_cursor_pos = cursor_pos

        self.current_gesture = current_gesture

    # ========================================================
    # TRIGGER CLICK AT CURRENT CURSOR POSITION
    # ========================================================
    def trigger_click(self, pos):
        """Trigger a click at the given position - called from main_menu"""
        self.cursor_pos = pos

        # Check BACK button (image button)
        if self.back_btn_rect.collidepoint(self.cursor_pos):
            print("⬅️ Back to menu")
            if self.main_menu:
                self.main_menu.current_screen = "menu"
                self.main_menu.stage_select = None
            return True

        # Check quarters
        for q in self.quarters:
            if q.get_rect().collidepoint(self.cursor_pos):
                q.on_click(self.particles)
                return True
        return False

    # ========================================================
    # CHECK GESTURE UNLOCK
    # ========================================================
    def check_gesture_unlock(self):
        hovered_quarter = None
        for q in self.quarters:
            if q.get_rect().collidepoint(self.cursor_pos):
                hovered_quarter = q
                break

        if self.current_gesture == "FIST" and hovered_quarter:
            next_unlock_index = self.path_system.target + 1

            if not hovered_quarter.unlocked and hovered_quarter.index - 1 == next_unlock_index:
                self.unlock_hold_timer += DT

                # Visual feedback
                if self.unlock_hold_timer > 0:
                    progress = min(1.0, self.unlock_hold_timer / self.UNLOCK_HOLD_TIME)
                    circle_radius = 20 + int(15 * progress)
                    for radius in range(3):
                        alpha = int(100 * (1 - radius / 3))
                        # Create a temporary surface for the circle with alpha
                        temp_surf = pygame.Surface((circle_radius * 2, circle_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(
                            temp_surf,
                            (100, 255, 100, alpha),
                            (circle_radius, circle_radius),
                            circle_radius - radius * 5,
                            3
                        )
                        self.screen.blit(temp_surf,
                                         (int(self.cursor_pos[0]) - circle_radius,
                                          int(self.cursor_pos[1]) - circle_radius))

                if self.unlock_hold_timer >= self.UNLOCK_HOLD_TIME:
                    current = self.path_system.target
                    if current < len(self.quarters) - 1:
                        self.particles.burst(self.quarters[current].x, self.quarters[current].y, 60)
                        self.path_system.unlock_next()
                        if self.path_system.target < len(self.quarters):
                            self.quarters[self.path_system.target].unlock()
                            print(f"🔓 Quarter {self.path_system.target + 1} UNLOCKED via gesture!")
                            self.particles.burst(self.quarters[self.path_system.target].x,
                                                 self.quarters[self.path_system.target].y, 100)
                            self.unlock_hold_timer = 0.0
                    else:
                        print("🏆 All quarters already unlocked!")
                        self.unlock_hold_timer = 0.0
            else:
                self.unlock_hold_timer = 0.0
        else:
            self.unlock_hold_timer = 0.0

    # ========================================================
    # UPDATE - NO PARAMETERS NEEDED!
    # ========================================================
    def update(self):
        # Update quarters
        for q in self.quarters:
            q.update(self.cursor_pos)

        # Update path system
        self.path_system.update()

        # Update particle effects
        self.particles.update()

        # Gesture fist detection for clicking
        # Use the fist_start_time from main_menu to determine if fist is being held
        if self.current_gesture == "FIST":
            if not self.fist_triggered:
                self.fist_hold_timer += DT
                if self.fist_hold_timer >= 0.1:  # Short hold for click
                    self.fist_triggered = True
                    # Use trigger_click with current cursor position
                    self.trigger_click(self.cursor_pos)
                    self.fist_hold_timer = 0.0
        else:
            self.fist_triggered = False
            self.fist_hold_timer = 0.0

        # Check for gesture-based unlocking
        self.check_gesture_unlock()

    # ========================================================
    # CLEANUP
    # ========================================================
    def cleanup(self):
        """Clean up resources if needed"""
        pass

    # ========================================================
    # EVENT HANDLER
    # ========================================================
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
        return None

    # ========================================================
    # DRAW
    # ========================================================
    def draw(self):
        # GRADIENT BACKGROUND
        for y in range(self.h):
            ratio = y / self.h
            r = int(lerp(BG_TOP[0], BG_BOTTOM[0], ratio))
            g = int(lerp(BG_TOP[1], BG_BOTTOM[1], ratio))
            b = int(lerp(BG_TOP[2], BG_BOTTOM[2], ratio))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.w, y))

        # TITLE
        title_shadow = self.title_font.render("SELECT QUARTER", True, BLACK)
        title = self.title_font.render("SELECT QUARTER", True, WHITE)
        self.screen.blit(title_shadow, (self.w // 2 - title.get_width() // 2 + 4, 54))
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, 50))

        # BACK BUTTON (using image like main_menu)
        if self.use_image_button and self.back_image:
            # Check if hovered for visual feedback
            if self.back_btn_rect.collidepoint(self.cursor_pos):
                # Draw highlight effect on hover
                glow_surf = pygame.Surface((self.back_btn_rect.width + 10, self.back_btn_rect.height + 10),
                                           pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (255, 255, 255, 60),
                                 (5, 5, self.back_btn_rect.width, self.back_btn_rect.height),
                                 border_radius=12)
                self.screen.blit(glow_surf, (self.back_btn_rect.x - 5, self.back_btn_rect.y - 5))

            # Draw the button image
            self.screen.blit(self.back_image, self.back_btn_rect.topleft)
        else:
            # Fallback to colored rectangle button
            hover = self.back_btn_rect.collidepoint(self.cursor_pos)
            btn_color = (100, 100, 140) if hover else (60, 60, 80)
            pygame.draw.rect(self.screen, btn_color, self.back_btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, WHITE, self.back_btn_rect, 3, border_radius=12)
            back_text = self.small_font.render("← BACK", True, WHITE)
            self.screen.blit(back_text, back_text.get_rect(center=self.back_btn_rect.center))

        # PATH
        self.path_system.draw(self.screen)

        # QUARTERS
        for q in self.quarters:
            q.draw(self.screen)

        # PARTICLES
        self.particles.draw(self.screen)

        # GESTURE UI
        gesture_display = "✊ FIST" if self.current_gesture == "FIST" else "🖐️ OPEN HAND"
        if self.current_gesture == "NO HAND":
            gesture_display = "👆 NO HAND"

        if self.unlock_hold_timer > 0:
            unlock_progress = int((self.unlock_hold_timer / self.UNLOCK_HOLD_TIME) * 100)
            progress_text = self.small_font.render(f"HOLD TO UNLOCK: {unlock_progress}%", True, (100, 255, 100))
            self.screen.blit(progress_text, (self.w // 2 - progress_text.get_width() // 2, self.h - 80))

        hint_surface = self.small_font.render(
            f"Gesture: {gesture_display}  |  FIST = Select  |  HOLD FIST on LOCKED = Unlock",
            True,
            (255, 240, 180)
        )
        self.screen.blit(hint_surface, (self.w // 2 - hint_surface.get_width() // 2, self.h - 45))

        # CUSTOM CURSOR
        cursor_glow_radius = 12
        # Outer glow
        glow_surf = pygame.Surface((cursor_glow_radius * 4, cursor_glow_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 200, 80),
                           (cursor_glow_radius * 2, cursor_glow_radius * 2), cursor_glow_radius + 4)
        self.screen.blit(glow_surf, (int(self.cursor_pos[0]) - cursor_glow_radius - 4,
                                     int(self.cursor_pos[1]) - cursor_glow_radius - 4))
        # Inner circle
        pygame.draw.circle(self.screen, WHITE,
                           (int(self.cursor_pos[0]), int(self.cursor_pos[1])), cursor_glow_radius - 2)
        pygame.draw.circle(self.screen, (255, 220, 100),
                           (int(self.cursor_pos[0]), int(self.cursor_pos[1])), cursor_glow_radius - 5)


# ============================================================
# MAIN GAME LOOP (Standalone Test)
# ============================================================
def main():
    pygame.init()
    screen_width = 1280
    screen_height = 720
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Cognitive Quest - Gesture Stage Select")
    clock = pygame.time.Clock()

    # Create stage select
    stage_select = StageSelect(screen)
    running = True

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Simulate gesture input with mouse
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        gesture = "FIST" if mouse_buttons[0] else "OPEN HAND"

        # Update stage select with matching signature
        stage_select.update_gesture(mouse_pos, 0, 0.3, gesture)
        stage_select.update()

        # Draw
        stage_select.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()