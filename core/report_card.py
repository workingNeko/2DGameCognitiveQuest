# core/report_card.py - Universal 3-Star Victory Report Card for Cognitive Quest
import pygame
import math
import random

class CelebrationParticleSystem:
    """Lightweight particle system for star sparkles and celebration bursts."""
    def __init__(self):
        self.particles = []

    def spawn_burst(self, x, y, count=25, colors=None):
        if colors is None:
            colors = [
                (255, 215, 0),   # Gold
                (255, 255, 255), # White sparkle
                (245, 158, 11),  # Amber
                (59, 130, 246),  # Blue
                (34, 197, 94),   # Green
                (236, 72, 153)   # Pink
            ]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 7.5)
            self.particles.append({
                "x": float(x),
                "y": float(y),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - random.uniform(1.0, 3.0),
                "gravity": 0.15,
                "size": random.uniform(4.0, 8.0),
                "color": random.choice(colors),
                "life": 1.0,
                "decay": random.uniform(0.012, 0.024),
                "shape": random.choice(["star", "circle", "sparkle"])
            })

    def update(self, dt=0.016):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += p["gravity"]
            p["life"] -= p["decay"]
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, screen):
        for p in self.particles:
            alpha = max(0, min(255, int(p["life"] * 255)))
            size = max(1, int(p["size"] * p["life"]))
            px, py = int(p["x"]), int(p["y"])

            if p["shape"] == "circle":
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p["color"][:3], alpha), (size, size), size)
                screen.blit(s, (px - size, py - size))
            elif p["shape"] == "star":
                # 4-pointed sparkle
                s = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                c = size * 2
                col = (*p["color"][:3], alpha)
                pygame.draw.line(s, col, (c - size * 2, c), (c + size * 2, c), max(1, size // 2))
                pygame.draw.line(s, col, (c, c - size * 2), (c, c + size * 2), max(1, size // 2))
                screen.blit(s, (px - c, py - c))
            else:
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                s.fill((*p["color"][:3], alpha))
                screen.blit(s, (px - size, py - size))


class VictoryReportCard:
    """
    Pedagogical 3-Star Victory Report Card Modal.
    Displays:
    - Stage Clear celebration title with star chime and victory fanfare
    - 3 Animated Stars rating based on accuracy
    - Score and accuracy percentage
    - Replay Stage and Return to Hub interactive buttons
    """
    def __init__(self, screen, width, height, main_menu, quarter_id="quarter1",
                 replay_callback=None, continue_callback=None):
        self.screen = screen
        self.width = width
        self.height = height
        self.main_menu = main_menu
        self.quarter_id = quarter_id
        self.replay_callback = replay_callback
        self.continue_callback = continue_callback

        self.active = False
        self.particles = CelebrationParticleSystem()
        self.elapsed = 0.0

        # Stats
        self.total_questions = 5
        self.correct_first_try = 5
        self.score = 100
        self.percentage = 100.0
        self.stars_earned = 3
        self.stage_title = "STAGE CLEAR!"

        # Star animation triggers
        self.star_anim_timers = [0.0, 0.0, 0.0]
        self.star_sound_played = [False, False, False]
        self.fanfare_played = False

        # Card geometry
        self.card_w = 620
        self.card_h = 470
        self.card_x = (self.width - self.card_w) // 2
        self.card_y = (self.height - self.card_h) // 2

        # Buttons
        btn_w = 230
        btn_h = 48
        btn_y = self.card_y + self.card_h - 75
        self.replay_rect = pygame.Rect(self.card_x + 55, btn_y, btn_w, btn_h)
        self.continue_rect = pygame.Rect(self.card_x + self.card_w - btn_w - 55, btn_y, btn_w, btn_h)

    def get_font(self, size, bold=False):
        for name in ["Comic Sans MS", "Segoe UI", "Arial"]:
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                pass
        return pygame.font.Font(None, size)

    def _play_sfx(self, name):
        mgr = getattr(self.main_menu, 'audio_manager', None)
        if mgr is not None:
            try:
                mgr.play_sfx(name)
            except Exception:
                pass

    def show(self, total_questions=5, correct_first_try=5, score=None, stage_title=None):
        """Activates and initializes the victory report card."""
        self.active = True
        self.elapsed = 0.0
        self.total_questions = max(1, total_questions)
        self.correct_first_try = max(0, min(correct_first_try, self.total_questions))
        self.percentage = (self.correct_first_try / float(self.total_questions)) * 100.0
        
        if score is not None:
            self.score = score
        else:
            self.score = int(self.correct_first_try * 20)

        # Star calculation:
        # 3 Stars: >= 80% (4/5 or 5/5)
        # 2 Stars: >= 60% (3/5)
        # 1 Star:  < 60%  (Effort reward)
        if self.percentage >= 80.0:
            self.stars_earned = 3
        elif self.percentage >= 60.0:
            self.stars_earned = 2
        else:
            self.stars_earned = 1

        if stage_title:
            self.stage_title = stage_title
        else:
            q_names = {
                "quarter1": "Quarter 1: Geometric Explorer",
                "quarter2": "Quarter 2: Fractions & Values",
                "quarter3": "Quarter 3: Master of Operations",
                "quarter4": "Quarter 4: Logic & Data Realm"
            }
            self.stage_title = q_names.get(self.quarter_id, "STAGE CLEAR!")

        self.star_sound_played = [False, False, False]
        self.fanfare_played = False

        # Spawn initial fireworks
        self.particles.spawn_burst(self.width // 2, self.card_y + 120, count=40)

        # Play victory sound
        self._play_sfx("victory_fanfare")
        self.fanfare_played = True

    def update(self, dt=0.016):
        if not self.active:
            return
        self.elapsed += dt
        self.particles.update(dt)

        # Staggered star reveal sound
        star_delay = 0.35
        for i in range(self.stars_earned):
            trigger_time = 0.3 + (i * star_delay)
            if self.elapsed >= trigger_time and not self.star_sound_played[i]:
                self.star_sound_played[i] = True
                self._play_sfx("star_chime")
                # Spawn star burst at star location
                star_cx = self.card_x + self.card_w // 2 + (i - 1) * 110
                star_cy = self.card_y + 135
                self.particles.spawn_burst(star_cx, star_cy, count=15, colors=[(255, 215, 0), (255, 255, 255)])

    def _draw_star(self, surface, center_x, center_y, radius, filled=True, scale=1.0):
        """Draws a crisp geometric 5-point star."""
        points = []
        outer_r = radius * scale
        inner_r = outer_r * 0.42
        angle_offset = -math.pi / 2  # Point straight up

        for i in range(10):
            r = outer_r if i % 2 == 0 else inner_r
            angle = angle_offset + (i * math.pi / 5)
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            points.append((x, y))

        if filled:
            # Golden star fill with bright rim
            pygame.draw.polygon(surface, (255, 215, 0), points)
            pygame.draw.polygon(surface, (255, 250, 200), points, 2)
        else:
            # Muted unfilled star outline
            pygame.draw.polygon(surface, (51, 65, 85), points)
            pygame.draw.polygon(surface, (100, 116, 139), points, 2)

    def draw(self, cursor_pos):
        if not self.active:
            return

        # Dimmed backdrop
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 205))
        self.screen.blit(dim, (0, 0))

        # Main Card Panel
        card_rect = pygame.Rect(self.card_x, self.card_y, self.card_w, self.card_h)
        pygame.draw.rect(self.screen, (15, 23, 42), card_rect, border_radius=20)
        pygame.draw.rect(self.screen, (255, 215, 0), card_rect, 3, border_radius=20)

        # Title
        t_font = self.get_font(24, bold=True)
        s_font = self.get_font(15, bold=True)
        h_font = self.get_font(18, bold=True)
        b_font = self.get_font(15)

        title_surf = t_font.render("VICTORY REPORT CARD", True, (255, 215, 0))
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.card_x + self.card_w // 2, self.card_y + 36)))

        subtitle_surf = s_font.render(self.stage_title, True, (148, 163, 184))
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(self.card_x + self.card_w // 2, self.card_y + 66)))

        # Draw the 3 Star Badges
        star_delay = 0.35
        for i in range(3):
            star_cx = self.card_x + self.card_w // 2 + (i - 1) * 110
            star_cy = self.card_y + 140
            earned = (i < self.stars_earned)

            # Pop-in scale animation
            scale = 1.0
            if earned:
                star_time = self.elapsed - (0.3 + i * star_delay)
                if star_time < 0:
                    earned = False  # Not popped in yet
                elif star_time < 0.2:
                    scale = 1.0 + math.sin((star_time / 0.2) * math.pi) * 0.35

            self._draw_star(self.screen, star_cx, star_cy, 36, filled=earned, scale=scale)

        # Mastery Badge
        if self.stars_earned == 3:
            badge_text = "⭐⭐⭐ OUTSTANDING MASTER!"
            badge_color = (255, 215, 0)
        elif self.stars_earned == 2:
            badge_text = "⭐⭐ GREAT EFFORT - ALMOST PERFECT!"
            badge_color = (56, 189, 248)
        else:
            badge_text = "⭐ STAGE COMPLETE - KEEP PRACTICING!"
            badge_color = (251, 146, 60)

        badge_surf = h_font.render(badge_text, True, badge_color)
        self.screen.blit(badge_surf, badge_surf.get_rect(center=(self.card_x + self.card_w // 2, self.card_y + 205)))

        # Stats Card inside modal
        stat_box = pygame.Rect(self.card_x + 55, self.card_y + 235, self.card_w - 110, 130)
        pygame.draw.rect(self.screen, (30, 41, 59), stat_box, border_radius=12)
        pygame.draw.rect(self.screen, (51, 65, 85), stat_box, 1, border_radius=12)

        # Stat 1: Score
        score_lbl = b_font.render("Stage Score:", True, (148, 163, 184))
        score_val = h_font.render(f"{self.score} PTS", True, (255, 215, 0))
        self.screen.blit(score_lbl, (stat_box.x + 25, stat_box.y + 22))
        self.screen.blit(score_val, (stat_box.x + stat_box.width - score_val.get_width() - 25, stat_box.y + 20))

        # Stat 2: First-Try Accuracy
        acc_lbl = b_font.render("First-Try Accuracy:", True, (148, 163, 184))
        acc_val = h_font.render(f"{self.correct_first_try} / {self.total_questions} ({int(self.percentage)}%)", True, (34, 197, 94))
        self.screen.blit(acc_lbl, (stat_box.x + 25, stat_box.y + 56))
        self.screen.blit(acc_val, (stat_box.x + stat_box.width - acc_val.get_width() - 25, stat_box.y + 54))

        # Stat 3: Pedagogical Encouragement Tip
        if self.percentage >= 80.0:
            tip_msg = "Outstanding mastery! You have unlocked the next challenges."
        elif self.percentage >= 60.0:
            tip_msg = "Good understanding! Try replaying to earn a perfect 3-star rating!"
        else:
            tip_msg = "Review the concepts and replay the stage to hone your skills!"

        tip_surf = b_font.render(tip_msg, True, (203, 213, 225))
        self.screen.blit(tip_surf, tip_surf.get_rect(center=(stat_box.centerx, stat_box.y + 102)))

        # 1. Replay Button
        rep_hov = self.replay_rect.collidepoint(cursor_pos)
        rep_bg = (59, 130, 246) if rep_hov else (37, 99, 235)
        pygame.draw.rect(self.screen, rep_bg, self.replay_rect, border_radius=10)
        pygame.draw.rect(self.screen, (191, 219, 254), self.replay_rect, 2, border_radius=10)
        rep_txt = h_font.render("↺ Replay Stage", True, (255, 255, 255))
        self.screen.blit(rep_txt, rep_txt.get_rect(center=self.replay_rect.center))

        # 2. Continue Button
        con_hov = self.continue_rect.collidepoint(cursor_pos)
        con_bg = (34, 197, 94) if con_hov else (22, 163, 74)
        pygame.draw.rect(self.screen, con_bg, self.continue_rect, border_radius=10)
        pygame.draw.rect(self.screen, (134, 239, 172), self.continue_rect, 2, border_radius=10)
        con_txt = h_font.render("Continue to Hub →", True, (255, 255, 255))
        self.screen.blit(con_txt, con_txt.get_rect(center=self.continue_rect.center))

        # Draw celebratory particles
        self.particles.draw(self.screen)

    def handle_click(self, pos):
        if not self.active:
            return None

        if self.replay_rect.collidepoint(pos):
            self.active = False
            self._play_sfx("click")
            if callable(self.replay_callback):
                self.replay_callback()
            return "replay"

        if self.continue_rect.collidepoint(pos):
            self.active = False
            self._play_sfx("click")
            if callable(self.continue_callback):
                self.continue_callback()
            return "continue"

        # Intercept clicks while victory card is shown
        return "handled"

    def handle_event(self, event):
        if not self.active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                self.active = False
                if callable(self.continue_callback):
                    self.continue_callback()
                return True
            elif event.key == pygame.K_r:
                self.active = False
                if callable(self.replay_callback):
                    self.replay_callback()
                return True
        return False
