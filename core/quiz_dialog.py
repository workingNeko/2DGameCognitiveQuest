# core/quiz_dialog.py - High-Engagement RPG Quest Question Dialog for Cognitive Quest
import pygame
import math
import time
import re
from .font_manager import get_font
from .vector_icons import draw_vector_star, draw_vector_lightbulb, draw_vector_gem

def clean_choice_text(choice_text):
    """
    Strips redundant leading 'A. ', 'B) ', '[C]', etc. from choice text
    since the jewel badge [A], [B], [C], [D] already displays the letter.
    """
    s = str(choice_text).strip()
    cleaned = re.sub(r'^(?:\[[A-Da-d]\]|\([A-Da-d]\)|[A-Da-d]\s*[.:\-\u2013\u2014\)])\s*', '', s)
    return cleaned if cleaned else s


class RPGQuizDialog:
    """
    Universal RPG Quest Dialogue Box for Quarters 1-4.
    Provides:
    - Live animated character portrait in ornate frame.
    - Station Gem Progress Bar showing completed, active, and upcoming stations.
    - Game-show style [A], [B], [C], [D] jewel-toned choice badges.
    - Smooth hover slide micro-animations (+8px ease-in) and glowing borders.
    - 50:50 eliminated option support with grayed-out styling.
    - Educational hint feedback banners.
    - Centralized hit-testing for mouse and gesture controllers.
    """

    BADGE_COLORS = {
        0: {"bg": (225, 29, 72), "border": (251, 113, 133), "label": "A"},   # Ruby Crimson
        1: {"bg": (37, 99, 235), "border": (96, 165, 250), "label": "B"},    # Sapphire Blue
        2: {"bg": (16, 185, 129), "border": (52, 211, 153), "label": "C"},   # Emerald Green
        3: {"bg": (217, 119, 6), "border": (251, 191, 36), "label": "D"}     # Amber Gold
    }

    def __init__(self, screen, width, height, audio_manager=None):
        self.screen = screen
        self.width = width
        self.height = height
        self.audio_manager = audio_manager

        # Dialog Box Dimensions - Scaled up for optimal classroom & student legibility
        self.box_w = min(self.width - 40, 960)
        self.box_h = min(self.height - 30, 570)
        self.box_x = (self.width - self.box_w) // 2
        self.box_y = (self.height - self.box_h) // 2

        # Button Layout Geometry
        self.btn_w = min(self.box_w - 60, 840)
        self.btn_h = 56
        self.btn_x = self.box_x + (self.box_w - self.btn_w) // 2
        self.button_y_start = self.box_y + 240
        self.spacing = 65

        # Pre-allocated transparent dim surface
        self.dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.dim_overlay.fill((8, 12, 22, 175))

        # Hover animation state: float slide offset for each choice (0.0 to 8.0)
        self.hover_offsets = [0.0, 0.0, 0.0, 0.0]
        self.last_hovered_index = -1

        # Pulse timer for active station jewel in progress bar
        self.pulse_timer = 0.0
        self.is_visible = False

    def update(self, dt=0.016):
        """Updates internal pulse and animation timers."""
        self.pulse_timer += dt

    def get_button_rect(self, index, slide_offset=0.0):
        """Calculates the rectangular hitbox for choice index (0..3)."""
        b_y = self.button_y_start + index * self.spacing
        return pygame.Rect(self.btn_x + int(slide_offset), b_y, self.btn_w, self.btn_h)

    def get_clicked_choice(self, cursor_pos, eliminated_choices=None):
        """
        Returns index (0..3) of choice button clicked, or None if none clicked.
        Respects 50:50 eliminated choices.
        """
        if cursor_pos is None or not isinstance(cursor_pos, (tuple, list)) or len(cursor_pos) < 2 or not isinstance(cursor_pos[0], (int, float)):
            return None

        if eliminated_choices is None:
            eliminated_choices = set()

        for i in range(4):
            if i in eliminated_choices:
                continue
            # Use base rect for hit testing to prevent flickering on slide edge
            rect = self.get_button_rect(i, slide_offset=0.0)
            if rect.collidepoint(cursor_pos):
                return i
        return None

    def wrap_text(self, text, font, max_width):
        """Wraps string into lines that fit within max_width."""
        if text is None:
            return []
        text = str(text)
        words = text.split(" ")
        lines = []
        current_line = []

        for word in words:
            if not word:
                continue
            # Handle long unbroken word
            if font.size(word)[0] > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                chunk = ""
                for char in word:
                    if font.size(chunk + char)[0] <= max_width:
                        chunk += char
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = char
                if chunk:
                    current_line = [chunk]
                continue

            test_line = " ".join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def draw(
        self,
        cursor_pos,
        q_data,
        speaker_name,
        speaker_subtitle,
        sprite_frame=None,
        station_idx=1,
        total_stations=5,
        eliminated_choices=None,
        hint_msg=None
    ):
        """
        Renders the complete RPG-style Question Dialog.
        """
        if cursor_pos is None or not isinstance(cursor_pos, (tuple, list)) or len(cursor_pos) < 2 or not isinstance(cursor_pos[0], (int, float)):
            cursor_pos = (-1000, -1000)

        if not isinstance(q_data, dict):
            q_data = {"question": str(q_data or ""), "choices": []}

        speaker_name = str(speaker_name or "")
        speaker_subtitle = str(speaker_subtitle or "")

        if eliminated_choices is None:
            eliminated_choices = set()

        # 1. Full-screen backdrop dimming
        self.screen.blit(self.dim_overlay, (0, 0))

        box_x = self.box_x
        box_y = self.box_y
        box_w = self.box_w
        box_h = self.box_h

        # 2. Outer Soft Drop Shadow
        if not hasattr(self, '_shadow_surf') or self._shadow_surf.get_size() != (box_w, box_h):
            self._shadow_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            self._shadow_surf.fill((0, 0, 0, 140))
        self.screen.blit(self._shadow_surf, (box_x + 6, box_y + 8))

        # 3. Main Container (Midnight Slate with Dual Ornate Golden Rim)
        main_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), main_rect, border_radius=18)
        # Outer Gold Rim
        pygame.draw.rect(self.screen, (217, 119, 6), main_rect, 3, border_radius=18)
        # Inner Radiant Hairline
        pygame.draw.rect(self.screen, (253, 224, 71), main_rect.inflate(-6, -6), 1, border_radius=15)

        # 4. Top Header Banner Ribbon
        header_h = 86
        if not hasattr(self, '_header_surf') or self._header_surf.get_size() != (box_w - 12, header_h):
            self._header_surf = pygame.Surface((box_w - 12, header_h), pygame.SRCALPHA)
            self._header_surf.fill((30, 41, 59, 230))
        self.screen.blit(self._header_surf, (box_x + 6, box_y + 6))
        pygame.draw.line(self.screen, (71, 85, 105), (box_x + 6, box_y + 6 + header_h), (box_x + box_w - 6, box_y + 6 + header_h), 2)

        # 5. Live Character Portrait Frame (Top Left)
        text_x = box_x + 30
        if sprite_frame is not None:
            avatar_center_x = box_x + 54
            avatar_center_y = box_y + 48
            avatar_radius = 32

            # Deep velvet circle backdrop
            pygame.draw.circle(self.screen, (10, 15, 29), (avatar_center_x, avatar_center_y), avatar_radius + 2)
            # Golden Frame Rings
            pygame.draw.circle(self.screen, (245, 158, 11), (avatar_center_x, avatar_center_y), avatar_radius + 2, 2)
            pygame.draw.circle(self.screen, (253, 224, 71), (avatar_center_x, avatar_center_y), avatar_radius, 1)

            # Blit Live Animated Sprite
            try:
                orig_w, orig_h = sprite_frame.get_size()
                scale_factor = min(58.0 / max(1, orig_w), 58.0 / max(1, orig_h))
                target_w = max(1, int(orig_w * scale_factor))
                target_h = max(1, int(orig_h * scale_factor))
                scaled_avatar = pygame.transform.scale(sprite_frame, (target_w, target_h))
                dest_x = avatar_center_x - target_w // 2
                dest_y = avatar_center_y - target_h // 2
                self.screen.blit(scaled_avatar, (dest_x, dest_y))
            except Exception:
                pass
            text_x = box_x + 104

        # 7. Station Gem Progress Bar (Top Right)
        total_st = max(1, total_stations)
        gem_start_x = box_x + box_w - 28 - (total_st - 1) * 32
        gem_y = box_y + 48

        # Connecting quest track line
        if total_st > 1:
            pygame.draw.line(
                self.screen,
                (71, 85, 105),
                (gem_start_x, gem_y),
                (gem_start_x + (total_st - 1) * 32, gem_y),
                4
            )

        pulse = 0.5 + 0.5 * math.sin(time.time() * 5.0)

        for s in range(1, total_st + 1):
            gx = gem_start_x + (s - 1) * 32
            if s < station_idx:
                # Completed: Bright glowing emerald gem with crisp vector star
                pygame.draw.circle(self.screen, (16, 185, 129), (gx, gem_y), 11)
                pygame.draw.circle(self.screen, (255, 255, 255), (gx, gem_y), 11, 1)
                draw_vector_star(self.screen, gx, gem_y, radius=7, color=(255, 255, 255))
            elif s == station_idx:
                # Active Station: Radiant pulsing amber gem with vector sparkle diamond
                glow_r = int(12 + pulse * 3.0)
                pygame.draw.circle(self.screen, (245, 158, 11), (gx, gem_y), glow_r, 2)
                pygame.draw.circle(self.screen, (251, 191, 36), (gx, gem_y), 11)
                draw_vector_gem(self.screen, gx, gem_y, radius=7, color=(15, 23, 42), highlight_color=(254, 240, 138))
            else:
                # Locked upcoming station: Dark slate socket
                pygame.draw.circle(self.screen, (30, 41, 59), (gx, gem_y), 9)
                pygame.draw.circle(self.screen, (71, 85, 105), (gx, gem_y), 9, 1)

        # 6. Speaker Typography - Large & Clear
        max_header_w = max(120, gem_start_x - text_x - 16)
        title_font = get_font(["Comic Sans MS", "Segoe UI"], 25, bold=True)
        sub_font = get_font(["Segoe UI", "Tahoma", "Comic Sans MS"], 17)

        name_surf = title_font.render(speaker_name, True, (251, 191, 36))
        if name_surf.get_width() > max_header_w:
            name_font_small = get_font(["Comic Sans MS", "Segoe UI"], 20, bold=True)
            name_surf = name_font_small.render(speaker_name, True, (251, 191, 36))
        self.screen.blit(name_surf, (text_x, box_y + 16))

        sub_surf = sub_font.render(speaker_subtitle, True, (148, 163, 184))
        if sub_surf.get_width() > max_header_w:
            sub_font_small = get_font(["Segoe UI", "Tahoma", "Comic Sans MS"], 14)
            sub_surf = sub_font_small.render(speaker_subtitle, True, (148, 163, 184))
            if sub_surf.get_width() > max_header_w:
                trunc_sub = speaker_subtitle
                while len(trunc_sub) > 4 and sub_font_small.size(trunc_sub + "...")[0] > max_header_w:
                    trunc_sub = trunc_sub[:-1]
                sub_surf = sub_font_small.render(trunc_sub + "...", True, (148, 163, 184))
        self.screen.blit(sub_surf, (text_x, box_y + 48))

        # 8. Question Prompt - Extra Large & Highly Readable for Grade 2 Students
        q_text = q_data.get("question", "")
        q_font_size = 24 if len(q_text) < 130 else 22
        q_font = get_font(["Segoe UI", "Comic Sans MS"], q_font_size, bold=True)
        wrapped_q = self.wrap_text(q_text, q_font, box_w - 60)

        y_text = box_y + 96
        line_height = 32 if q_font_size == 24 else 28
        for line in wrapped_q:
            txt_surf = q_font.render(line, True, (248, 250, 252))
            self.screen.blit(txt_surf, (box_x + 30, y_text))
            y_text += line_height

        # 9. Pedagogical / 50:50 Hint Banner
        content_bottom = y_text
        if hint_msg:
            hint_font = get_font(["Segoe UI", "Comic Sans MS"], 17, bold=True)
            draw_vector_lightbulb(self.screen, box_x + 40, y_text + 14, size=8)
            hint_surf = hint_font.render(f"Hint: {hint_msg}", True, (252, 211, 77))
            self.screen.blit(hint_surf, (box_x + 58, y_text + 4))
            content_bottom = y_text + 30

        # Dynamically position choice buttons so they NEVER collide with question or hint
        desired_button_y = max(box_y + 240, content_bottom + 14)
        max_button_y = box_y + box_h - (3 * self.spacing + self.btn_h + 14)
        self.button_y_start = min(desired_button_y, max_button_y)

        # 10. Game-Show Style Choice Buttons ([A], [B], [C], [D]) - Large 21pt Bold Fonts
        choices = q_data.get("choices", [])[:4]
        badge_font = get_font(["Segoe UI", "Arial"], 22, bold=True)
        choice_font = get_font(["Segoe UI", "Comic Sans MS"], 21, bold=True)

        current_hovered_index = -1

        for i, choice_text in enumerate(choices):
            is_elim = i in eliminated_choices
            base_rect = self.get_button_rect(i, slide_offset=0.0)
            is_hov = base_rect.collidepoint(cursor_pos) and not is_elim

            if is_hov:
                current_hovered_index = i

            # Smooth slide animation easing towards target
            target_offset = 8.0 if is_hov else 0.0
            self.hover_offsets[i] += (target_offset - self.hover_offsets[i]) * 0.3
            curr_slide = self.hover_offsets[i]

            btn_rect = self.get_button_rect(i, slide_offset=curr_slide)

            # Button Card Background
            if is_elim:
                card_bg = (15, 23, 42)
                card_border = (51, 65, 85)
                text_color = (100, 116, 139)
                border_width = 1
            elif is_hov:
                card_bg = (30, 41, 59)
                card_border = (255, 255, 255)
                text_color = (255, 255, 255)
                border_width = 2
            else:
                card_bg = (15, 23, 42)
                card_border = (71, 85, 105)
                text_color = (226, 232, 240)
                border_width = 1

            # Soft drop shadow for hovered card
            if is_hov:
                shadow_rect = btn_rect.move(3, 3)
                pygame.draw.rect(self.screen, (0, 0, 0, 70), shadow_rect, border_radius=12)

            pygame.draw.rect(self.screen, card_bg, btn_rect, border_radius=12)
            pygame.draw.rect(self.screen, card_border, btn_rect, border_width, border_radius=12)

            # Left Jewel-Toned Letter Badge (Enlarged)
            badge_cfg = self.BADGE_COLORS.get(i, {"bg": (100, 100, 100), "border": (150, 150, 150), "label": chr(65 + i)})
            badge_rect = pygame.Rect(btn_rect.x + 10, btn_rect.y + 8, 40, 40)

            if is_elim:
                pygame.draw.rect(self.screen, (30, 41, 59), badge_rect, border_radius=10)
                pygame.draw.rect(self.screen, (71, 85, 105), badge_rect, 1, border_radius=10)
                x_surf = badge_font.render("X", True, (100, 116, 139))
                self.screen.blit(x_surf, x_surf.get_rect(center=badge_rect.center))
            else:
                badge_bg = badge_cfg["bg"]
                badge_border = badge_cfg["border"]
                if is_hov:
                    badge_bg = (15, 23, 42)
                    badge_border = (255, 255, 255)

                pygame.draw.rect(self.screen, badge_bg, badge_rect, border_radius=10)
                pygame.draw.rect(self.screen, badge_border, badge_rect, 2, border_radius=10)
                b_lbl = badge_font.render(badge_cfg["label"], True, (255, 255, 255))
                self.screen.blit(b_lbl, b_lbl.get_rect(center=badge_rect.center))

            # Choice text next to badge (stripped of redundant leading letter, auto-scaled if wide)
            display_text = clean_choice_text(choice_text)
            avail_w = btn_rect.width - 78
            choice_surf = choice_font.render(display_text, True, text_color)
            if choice_surf.get_width() > avail_w:
                smaller_font = get_font(["Segoe UI", "Comic Sans MS"], 18, bold=True)
                choice_surf = smaller_font.render(display_text, True, text_color)
                if choice_surf.get_width() > avail_w:
                    tiny_font = get_font(["Segoe UI", "Comic Sans MS"], 15, bold=True)
                    choice_surf = tiny_font.render(display_text, True, text_color)
            txt_rect = choice_surf.get_rect(midleft=(btn_rect.x + 64, btn_rect.centery))
            self.screen.blit(choice_surf, txt_rect)

        # Audio tick feedback when entering new hovered choice
        if current_hovered_index != self.last_hovered_index:
            if current_hovered_index != -1 and self.audio_manager:
                try:
                    self.audio_manager.play_sfx("click")
                except Exception:
                    pass
            self.last_hovered_index = current_hovered_index


QuizDialog = RPGQuizDialog

