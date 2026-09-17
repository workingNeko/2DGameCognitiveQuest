# core/npc_dialog_system.py
"""
High-Engagement RPG Dialogue and Instruction Modal System for Cognitive Quest 2D.
Provides:
1. InstructionModal: High-fidelity popup modal displayed on map entry explaining
   objectives, customized with [Player Name] and dismissible with Fist Hold / Click / Spacebar.
2. NPCGreetingDialog: Smooth Proximity Trigger dialogue box presenting the NPC's persona
   and greeting line, prompting player to hold a closed fist for 0.9s or click to trigger
   the dynamic quiz question.
"""

import pygame
import math
import time
from .font_manager import get_font, sanitize_text
from .vector_icons import draw_vector_star, draw_vector_lightbulb

THEME_PALETTES = {
    "forest": {
        "border": (34, 197, 94),        # Emerald Green
        "glow": (74, 222, 128),
        "header_bg": (20, 83, 45),
        "title_color": (250, 204, 21),   # Gold
        "accent": (250, 204, 21),
        "button_bg": (22, 101, 52),
        "button_hover": (34, 197, 94)
    },
    "fiesta": {
        "border": (245, 158, 11),       # Amber Gold
        "glow": (251, 191, 36),
        "header_bg": (120, 53, 15),
        "title_color": (254, 240, 138),  # Warm Cream
        "accent": (239, 68, 68),        # Fiesta Crimson
        "button_bg": (180, 83, 9),
        "button_hover": (245, 158, 11)
    },
    "desert": {
        "border": (217, 119, 6),        # Bronze Gold
        "glow": (251, 191, 36),
        "header_bg": (113, 63, 18),
        "title_color": (253, 224, 71),   # Sun Yellow
        "accent": (234, 88, 12),        # Terracotta
        "button_bg": (161, 98, 7),
        "button_hover": (217, 119, 6)
    },
    "water": {
        "border": (14, 165, 233),       # Sky Blue
        "glow": (56, 189, 248),
        "header_bg": (12, 74, 110),
        "title_color": (186, 230, 253),  # Cyan Foam
        "accent": (59, 130, 246),
        "button_bg": (3, 105, 161),
        "button_hover": (14, 165, 233)
    }
}


def wrap_text(text, font, max_width):
    """Utility to split text into wrapped lines for rendering."""
    words = text.split(" ")
    lines = []
    current_line = []
    for word in words:
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


class InstructionModal:
    """
    RPG Map Instructions Modal shown at the start of each map.
    Explains the sequential quest steps and goals.
    """
    def __init__(self, screen, width, height, audio_manager=None):
        self.screen = screen
        self.width = width
        self.height = height
        self.audio_manager = audio_manager

        self.active = False
        self.data = None
        self.theme_key = "forest"

        # Dimensions - Scaled up for optimal classroom & student legibility
        self.box_w = min(self.width - 60, 860)
        self.box_h = min(self.height - 60, 560)
        self.box_x = (self.width - self.box_w) // 2
        self.box_y = (self.height - self.box_h) // 2

        self.btn_w = min(self.box_w - 80, 420)
        self.btn_h = 52
        self.btn_x = self.box_x + (self.box_w - self.btn_w) // 2
        self.btn_y = self.box_y + self.box_h - 68

        self.dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.dim_overlay.fill((6, 10, 18, 190))

        self.pulse = 0.0
        self.shown_count = 0

    @property
    def title(self):
        return self.data.get("title", "") if self.data else ""

    @property
    def subtitle(self):
        return self.data.get("subtitle", "") if self.data else ""

    @property
    def steps(self):
        return self.data.get("steps", []) if self.data else []

    def show(self, instructions_data):
        self.data = instructions_data
        self.theme_key = instructions_data.get("theme", "forest")
        self.active = True
        self.shown_count += 1
        if self.audio_manager:
            try:
                self.audio_manager.play_sfx("portal_transition")
            except Exception:
                pass

    def hide(self):
        if self.active:
            self.active = False
            if self.audio_manager:
                try:
                    self.audio_manager.play_sfx("click")
                except Exception:
                    pass

    @property
    def is_visible(self):
        return self.active

    @is_visible.setter
    def is_visible(self, val):
        self.active = bool(val)

    def is_active(self):
        return self.active

    def update(self, dt=0.016, cursor_pos=None, fist_pct=0.0, **kwargs):
        if self.active:
            self.pulse += dt * 3.0
            self.fist_hold_pct = kwargs.get("fist_hold_pct", fist_pct)

    def get_button_rect(self):
        return pygame.Rect(self.btn_x, self.btn_y, self.btn_w, self.btn_h)

    def handle_click(self, cursor_pos):
        if not self.active:
            return False
        btn_rect = self.get_button_rect()
        if btn_rect.collidepoint(cursor_pos):
            self.hide()
            return True
        # Clicking outside or anywhere on modal dismisses it as well
        modal_rect = pygame.Rect(self.box_x, self.box_y, self.box_w, self.box_h)
        if modal_rect.collidepoint(cursor_pos):
            self.hide()
            return True
        return False

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self.hide()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_click(event.pos)
        return False

    def handle_fist_hold(self, is_fist, hold_time, click_hold_time):
        if not self.active:
            return False
        if is_fist and hold_time >= click_hold_time:
            self.hide()
            return True
        return False

    def draw(self, cursor_pos, fist_hold_pct=None):
        if not self.active or not self.data:
            return
        if fist_hold_pct is None:
            fist_hold_pct = getattr(self, 'fist_hold_pct', 0.0)

        theme = THEME_PALETTES.get(self.theme_key, THEME_PALETTES["forest"])
        self.screen.blit(self.dim_overlay, (0, 0))

        # Outer drop shadow
        shadow = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 160))
        self.screen.blit(shadow, (self.box_x + 6, self.box_y + 8))

        # Main parchment / card surface
        card_rect = pygame.Rect(self.box_x, self.box_y, self.box_w, self.box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), card_rect, border_radius=16)
        pygame.draw.rect(self.screen, theme["border"], card_rect, 3, border_radius=16)
        # Inner hairline
        pygame.draw.rect(self.screen, theme["glow"], card_rect.inflate(-6, -6), 1, border_radius=12)

        # Header banner box
        hdr_h = 80
        hdr_rect = pygame.Rect(self.box_x + 14, self.box_y + 14, self.box_w - 28, hdr_h)
        pygame.draw.rect(self.screen, theme["header_bg"], hdr_rect, border_radius=12)
        pygame.draw.rect(self.screen, theme["border"], hdr_rect, 2, border_radius=12)

        # Title & Subtitle Typography - Prominent & Highly Readable for Elementary Students
        title_font = get_font("Comic Sans MS", 23, bold=True)
        sub_font = get_font("Comic Sans MS", 16, italic=True)
        body_font = get_font("Comic Sans MS", 17, bold=True)
        bullet_font = get_font("Comic Sans MS", 15)

        title_surf = title_font.render(sanitize_text(self.data.get("title", "QUEST OBJECTIVES")), True, theme["title_color"])
        t_rect = title_surf.get_rect(center=(hdr_rect.centerx, hdr_rect.top + 26))
        self.screen.blit(title_surf, t_rect)

        sub_surf = sub_font.render(sanitize_text(self.data.get("subtitle", "")), True, (241, 245, 249))
        s_rect = sub_surf.get_rect(center=(hdr_rect.centerx, hdr_rect.top + 54))
        self.screen.blit(sub_surf, s_rect)

        # Steps list
        cur_y = self.box_y + 106
        max_content_w = self.box_w - 70

        for step in self.data.get("steps", []):
            st_title = step.get("title", "")
            if st_title:
                st_surf = body_font.render(sanitize_text(st_title), True, theme["accent"])
                self.screen.blit(st_surf, (self.box_x + 36, cur_y))
                cur_y += 26

            for bullet in step.get("bullets", []):
                wrapped = wrap_text(bullet, bullet_font, max_content_w - 30)
                for i, w_line in enumerate(wrapped):
                    prefix = "  • " if i == 0 else "    "
                    b_surf = bullet_font.render(sanitize_text(prefix + w_line), True, (226, 232, 240))
                    self.screen.blit(b_surf, (self.box_x + 40, cur_y))
                    cur_y += 22
            cur_y += 8

        # CTA Button at bottom
        btn_rect = self.get_button_rect()
        is_hovered = btn_rect.collidepoint(cursor_pos)
        btn_bg = theme["button_hover"] if is_hovered else theme["button_bg"]

        # Button shadow
        pygame.draw.rect(self.screen, (0, 0, 0, 100), btn_rect.move(2, 2), border_radius=12)
        pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=12)
        pygame.draw.rect(self.screen, (255, 255, 255) if is_hovered else theme["glow"], btn_rect, 2, border_radius=12)

        # Fist hold progress fill
        if fist_hold_pct > 0.0:
            fill_w = int(self.btn_w * min(1.0, fist_hold_pct))
            fill_rect = pygame.Rect(self.btn_x, self.btn_y, fill_w, self.btn_h)
            fill_surf = pygame.Surface((fill_w, self.btn_h), pygame.SRCALPHA)
            fill_surf.fill((255, 255, 255, 70))
            self.screen.blit(fill_surf, fill_rect)

        btn_font = get_font("Comic Sans MS", 17, bold=True)
        btn_text = "Let's Begin Quest! >>" if not is_hovered else "Click or Hold Fist to Begin!"
        if fist_hold_pct > 0.0:
            btn_text = f"Holding Fist: {int(fist_hold_pct * 100)}%"

        btn_surf = btn_font.render(sanitize_text(btn_text), True, (255, 255, 255))
        b_rect = btn_surf.get_rect(center=btn_rect.center)
        self.screen.blit(btn_surf, b_rect)


class NPCGreetingDialog:
    """
    Proximity Trigger Dialogue Box.
    Opens smoothly when the player is within range of an active NPC.
    Displays persona name, role, greeting text, animated portrait,
    and prompts the player to hold a closed fist for 0.9s or click to begin.
    """
    def __init__(self, screen, width, height, audio_manager=None):
        self.screen = screen
        self.width = width
        self.height = height
        self.audio_manager = audio_manager

        self.active = False
        self.script_data = None
        self.sprite_frame = None
        self.target_station_idx = 1
        self.theme_key = "forest"

        # Dimensions - Scaled up and placed dead-center of the screen
        self.box_w = min(self.width - 60, 840)
        self.box_h = min(int(self.height * 0.42), 260)
        self.box_x = (self.width - self.box_w) // 2
        self.box_y = (self.height - self.box_h) // 2

        self.btn_w = min(self.box_w - 80, 440)
        self.btn_h = 48
        self.btn_x = self.box_x + (self.box_w - self.btn_w) // 2
        self.btn_y = self.box_y + self.box_h - 58

        self.dim_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.dim_overlay.fill((6, 10, 18, 140))

        self.pulse = 0.0
        self.open_time = 0.0

    def show(self, *args, **kwargs):
        """
        Supports:
          show(script_data, sprite_frame=None, station_idx=1, theme="forest")
          show(speaker_name, speaker_title, greeting_text, sprite_frame=None)
        """
        if args and isinstance(args[0], dict):
            self.script_data = args[0]
            self.sprite_frame = kwargs.get("sprite_frame") or (args[1] if len(args) > 1 else None)
            self.target_station_idx = kwargs.get("station_idx", 1)
            self.theme_key = kwargs.get("theme", "forest")
        elif args:
            speaker_name = args[0]
            speaker_title = args[1] if len(args) > 1 else ""
            greeting_text = args[2] if len(args) > 2 else ""
            self.script_data = {
                "name": speaker_name,
                "role": speaker_title,
                "greeting": greeting_text
            }
            self.sprite_frame = kwargs.get("sprite_frame") or (args[3] if len(args) > 3 else None)
            self.target_station_idx = kwargs.get("station_idx", 1)
            self.theme_key = kwargs.get("theme", "forest")
        else:
            self.script_data = {}

        self.active = True
        self.open_time = time.time()
        if self.audio_manager:
            try:
                self.audio_manager.play_sfx("menu_open")
            except Exception:
                pass

    def hide(self):
        self.active = False
        self.script_data = None

    @property
    def is_visible(self):
        return self.active

    @is_visible.setter
    def is_visible(self, val):
        self.active = bool(val)

    def is_active(self):
        return self.active

    def update(self, dt=0.016, cursor_pos=None, fist_pct=0.0, **kwargs):
        if self.active:
            self.pulse += dt * 3.5
            self.fist_hold_pct = kwargs.get("fist_hold_pct", fist_pct)

    def get_button_rect(self):
        return pygame.Rect(self.btn_x, self.btn_y, self.btn_w, self.btn_h)

    @property
    def btn_rect(self):
        return self.get_button_rect()

    def handle_click(self, cursor_pos):
        if not self.active:
            return False
        # Clicking the CTA button or anywhere on the speech box triggers question!
        box_rect = pygame.Rect(self.box_x, self.box_y, self.box_w, self.box_h)
        if box_rect.collidepoint(cursor_pos):
            if self.audio_manager:
                try:
                    self.audio_manager.play_sfx("click")
                except Exception:
                    pass
            self.hide()
            return True
        return False

    def handle_fist_hold(self, is_fist, hold_time, click_hold_time):
        if not self.active:
            return False
        if is_fist and hold_time >= click_hold_time:
            if self.audio_manager:
                try:
                    self.audio_manager.play_sfx("click")
                except Exception:
                    pass
            self.hide()
            return True
        return False

    def draw(self, cursor_pos, fist_hold_pct=None):
        if not self.active or not self.script_data:
            return
        if fist_hold_pct is None:
            fist_hold_pct = getattr(self, 'fist_hold_pct', 0.0)

        theme = THEME_PALETTES.get(self.theme_key, THEME_PALETTES["forest"])

        # Soft backdrop dimming to focus attention on the centered objective NPC popup
        if hasattr(self, 'dim_overlay') and self.dim_overlay:
            self.screen.blit(self.dim_overlay, (0, 0))

        # Soft backdrop shadow
        shadow = pygame.Surface((self.box_w, self.box_h), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 140))
        self.screen.blit(shadow, (self.box_x + 4, self.box_y + 6))

        # Main box
        box_rect = pygame.Rect(self.box_x, self.box_y, self.box_w, self.box_h)
        pygame.draw.rect(self.screen, (15, 23, 42), box_rect, border_radius=16)
        pygame.draw.rect(self.screen, theme["border"], box_rect, 3, border_radius=16)
        pygame.draw.rect(self.screen, theme["glow"], box_rect.inflate(-6, -6), 1, border_radius=12)

        # Portrait frame on left
        p_size = 84
        p_x = self.box_x + 20
        p_y = self.box_y + 18
        p_rect = pygame.Rect(p_x, p_y, p_size, p_size)

        pygame.draw.rect(self.screen, (30, 41, 59), p_rect, border_radius=12)
        pygame.draw.rect(self.screen, theme["accent"], p_rect, 2, border_radius=12)

        if self.sprite_frame:
            try:
                scaled_sprite = pygame.transform.smoothscale(self.sprite_frame, (p_size - 8, p_size - 8))
                self.screen.blit(scaled_sprite, (p_x + 4, p_y + 4))
            except Exception:
                pass
        else:
            # Fallback vector icon
            draw_vector_star(self.screen, p_rect.centerx, p_rect.centery, radius=18, color=theme["accent"])

        # Speaker Badge - Larger, Clearer Fonts
        name_font = get_font("Comic Sans MS", 21, bold=True)
        role_font = get_font("Comic Sans MS", 15, italic=True)
        speech_font = get_font("Comic Sans MS", 17)

        speaker_name = self.script_data.get("name", "Guardian")
        speaker_role = self.script_data.get("role", f"Station {self.target_station_idx}")

        n_surf = name_font.render(sanitize_text(speaker_name), True, theme["title_color"])
        self.screen.blit(n_surf, (p_x + p_size + 18, p_y + 2))

        r_surf = role_font.render(sanitize_text(speaker_role), True, (148, 163, 184))
        self.screen.blit(r_surf, (p_x + p_size + 18, p_y + 28))

        # Proximity Greeting Speech lines
        greeting_text = self.script_data.get("greeting", "")
        max_speech_w = self.box_w - (p_size + 56)
        wrapped_lines = wrap_text(greeting_text, speech_font, max_speech_w)

        gy = p_y + 56
        for line in wrapped_lines[:3]:
            l_surf = speech_font.render(sanitize_text(line), True, (241, 245, 249))
            self.screen.blit(l_surf, (p_x + p_size + 18, gy))
            gy += 25

        # CTA Bottom Button / Bar
        btn_rect = self.get_button_rect()
        is_hovered = btn_rect.collidepoint(cursor_pos)
        btn_bg = theme["button_hover"] if is_hovered else theme["button_bg"]

        pygame.draw.rect(self.screen, (0, 0, 0, 90), btn_rect.move(2, 2), border_radius=10)
        pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255) if is_hovered else theme["border"], btn_rect, 2, border_radius=10)

        # Fist hold progress fill
        if fist_hold_pct > 0.0:
            fill_w = int(self.btn_w * min(1.0, fist_hold_pct))
            fill_rect = pygame.Rect(self.btn_x, self.btn_y, fill_w, self.btn_h)
            fill_surf = pygame.Surface((fill_w, self.btn_h), pygame.SRCALPHA)
            fill_surf.fill((255, 255, 255, 80))
            self.screen.blit(fill_surf, fill_rect)

        btn_font = get_font("Comic Sans MS", 15, bold=True)
        if fist_hold_pct > 0.0:
            c_text = f"Opening Challenge: {int(fist_hold_pct * 100)}%"
        else:
            c_text = "Hold Closed Fist (0.9s) or Click to Begin!" if not is_hovered else "Click or Hold Fist to Open Question!"

        c_surf = btn_font.render(sanitize_text(c_text), True, (255, 255, 255))
        c_rect = c_surf.get_rect(center=btn_rect.center)
        self.screen.blit(c_surf, c_rect)
