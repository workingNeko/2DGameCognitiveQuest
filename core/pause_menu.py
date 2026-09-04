# core/pause_menu.py - Universal In-Stage Pause System for Cognitive Quest
import pygame

class InGamePauseMenu:
    """
    Universal In-Stage Pause Menu component for Quarters 1–4.
    Provides:
    - On-screen pause button (compatible with gesture fist & mouse clicks).
    - Timer freezing while paused.
    - Interactive modal with Resume, Audio Settings, and Return to Stage Select.
    - Keyboard shortcut support (ESC, P).
    """

    def __init__(self, screen, width, height, main_menu, return_callback):
        self.screen = screen
        self.width = width
        self.height = height
        self.main_menu = main_menu
        self.return_callback = return_callback
        self.is_paused = False

        # Top-right Pause Button
        self.btn_w = 114
        self.btn_h = 36
        self.btn_x = self.width - self.btn_w - 20
        self.btn_y = 18
        self.pause_btn_rect = pygame.Rect(self.btn_x, self.btn_y, self.btn_w, self.btn_h)

        # Modal geometry
        self.modal_w = 460
        self.modal_h = 300
        self.modal_x = (self.width - self.modal_w) // 2
        self.modal_y = (self.height - self.modal_h) // 2

        self.resume_rect = pygame.Rect(self.modal_x + 50, self.modal_y + 85, 360, 48)
        self.audio_rect = pygame.Rect(self.modal_x + 50, self.modal_y + 145, 360, 48)
        self.exit_rect = pygame.Rect(self.modal_x + 50, self.modal_y + 205, 360, 48)

    def get_font(self, size, bold=False):
        for name in ["Comic Sans MS", "Segoe UI", "Arial"]:
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                pass
        return pygame.font.Font(None, size)

    def handle_event(self, event):
        """Processes keyboard toggle for pause (ESC or P)."""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_p]:
                self.toggle_pause()
                return True
        return False

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if hasattr(self.main_menu, 'audio_manager'):
            self.main_menu.audio_manager.play_sfx("click")

    def handle_click(self, pos):
        """Handles cursor or mouse clicks on pause button or modal."""
        # 1. Check Pause Button toggle
        if self.pause_btn_rect.collidepoint(pos):
            self.toggle_pause()
            return True

        # 2. If Paused, intercept modal clicks
        if self.is_paused:
            if self.resume_rect.collidepoint(pos):
                self.is_paused = False
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("click")
                return True

            elif self.audio_rect.collidepoint(pos):
                if hasattr(self.main_menu, 'open_audio_settings'):
                    self.main_menu.open_audio_settings()
                return True

            elif self.exit_rect.collidepoint(pos):
                self.is_paused = False
                if hasattr(self.main_menu, 'audio_manager'):
                    self.main_menu.audio_manager.play_sfx("click")
                if callable(self.return_callback):
                    try:
                        self.return_callback(completed=False)
                    except TypeError:
                        self.return_callback()
                return True

            # Intercept all clicks when paused so gameplay behind doesn't trigger
            return True

        return False

    def draw_button(self, cursor_pos):
        """Draws the on-screen pause button in the top corner."""
        hov = self.pause_btn_rect.collidepoint(cursor_pos)
        bg = (51, 65, 85) if hov else (30, 41, 59)
        border = (255, 215, 0) if hov else (148, 163, 184)
        fg = (255, 215, 0) if hov else (241, 245, 249)

        pygame.draw.rect(self.screen, bg, self.pause_btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, border, self.pause_btn_rect, 2, border_radius=8)

        font = self.get_font(15, bold=True)
        txt = font.render("⏸ PAUSE", True, fg)
        self.screen.blit(txt, txt.get_rect(center=self.pause_btn_rect.center))

    def draw_modal(self, cursor_pos):
        """Draws the pause modal overlay."""
        if not self.is_paused:
            return

        # Semi-transparent overlay
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 185))
        self.screen.blit(dim, (0, 0))

        # Centered Dialog Box
        modal_rect = pygame.Rect(self.modal_x, self.modal_y, self.modal_w, self.modal_h)
        pygame.draw.rect(self.screen, (15, 23, 42), modal_rect, border_radius=16)
        pygame.draw.rect(self.screen, (255, 215, 0), modal_rect, 3, border_radius=16)

        # Title
        t_font = self.get_font(24, bold=True)
        btn_font = self.get_font(16, bold=True)

        title = t_font.render("⏸ GAME PAUSED", True, (255, 215, 0))
        self.screen.blit(title, title.get_rect(center=(self.modal_x + self.modal_w // 2, self.modal_y + 40)))

        # 1. Resume Button (Green)
        r_hov = self.resume_rect.collidepoint(cursor_pos)
        r_bg = (34, 197, 94) if r_hov else (22, 163, 74)
        pygame.draw.rect(self.screen, r_bg, self.resume_rect, border_radius=10)
        pygame.draw.rect(self.screen, (134, 239, 172), self.resume_rect, 2, border_radius=10)
        r_txt = btn_font.render("▶  Resume Game", True, (255, 255, 255))
        self.screen.blit(r_txt, r_txt.get_rect(center=self.resume_rect.center))

        # 2. Audio Settings Button (Blue)
        s_hov = self.audio_rect.collidepoint(cursor_pos)
        s_bg = (59, 130, 246) if s_hov else (37, 99, 235)
        pygame.draw.rect(self.screen, s_bg, self.audio_rect, border_radius=10)
        pygame.draw.rect(self.screen, (191, 219, 254), self.audio_rect, 2, border_radius=10)
        s_txt = btn_font.render("🔊  Audio & Sound Settings", True, (255, 255, 255))
        self.screen.blit(s_txt, s_txt.get_rect(center=self.audio_rect.center))

        # 3. Return to Stage Select Button (Red)
        e_hov = self.exit_rect.collidepoint(cursor_pos)
        e_bg = (239, 68, 68) if e_hov else (185, 28, 28)
        pygame.draw.rect(self.screen, e_bg, self.exit_rect, border_radius=10)
        pygame.draw.rect(self.screen, (254, 202, 202), self.exit_rect, 2, border_radius=10)
        e_txt = btn_font.render("🏠  Return to Stage Select", True, (255, 255, 255))
        self.screen.blit(e_txt, e_txt.get_rect(center=self.exit_rect.center))
