# core/autosave_manager.py - Power-Interruption Resilient Autosave System
"""
Autosave Manager for Cognitive Maze.
Provides periodic and event-triggered background autosaving to protect student progress
against unexpected power interruptions, brownouts, or sudden system shutdowns.

Target Hardware Constraint:
- AMD A4-6300 APU (Dual-Core, 2 Threads, 3.7 GHz, 1MB L2 cache, 0MB L3 cache, Radeon HD 8370D).
- Zero per-frame allocations during hot game loop (60 FPS maintained).
- Pre-baked surfaces with hardware alpha-blending for the autosave badge.
- Atomic filesystem sync (fsync) guarantees valid files on physical media.
"""

import time
import math
import pygame
from core.font_manager import get_font


class AutosaveManager:
    """
    Manages background autosaving and on-screen save notifications.
    Safeguards student progress in case of power interruptions.
    """

    def __init__(self, main_menu, interval_seconds: float = 30.0):
        self.main_menu = main_menu
        self.interval_seconds = max(10.0, float(interval_seconds))
        self.min_event_interval = 1.5  # Debounce event-driven saves

        self.last_save_time = 0.0
        self.last_state_signature = None

        # On-screen feedback badge timing
        self.indicator_duration = 2.0  # Seconds the badge stays visible
        self.indicator_timer = 0.0

        # Pre-baked surface cache for zero per-frame heap allocations
        self._badge_w = 144
        self._badge_h = 28
        self._badge_base_surf = None
        self._badge_draw_surf = None
        self._init_cached_surfaces()

    def _init_cached_surfaces(self) -> None:
        """Pre-renders the autosave badge surface once to prevent allocations during 60 FPS gameplay."""
        try:
            base = pygame.Surface((self._badge_w, self._badge_h), pygame.SRCALPHA)
            # Translucent dark slate pill
            pygame.draw.rect(base, (15, 23, 42, 230), (0, 0, self._badge_w, self._badge_h), border_radius=14)
            # Glowing emerald green border
            pygame.draw.rect(base, (34, 197, 94, 210), (0, 0, self._badge_w, self._badge_h), 2, border_radius=14)

            # Glowing green dot indicator
            dot_x = 16
            dot_y = self._badge_h // 2
            pygame.draw.circle(base, (34, 197, 94, 90), (dot_x, dot_y), 6)
            pygame.draw.circle(base, (74, 222, 128, 255), (dot_x, dot_y), 3)

            # Text: "AUTOSAVED"
            font = get_font("Comic Sans MS", 11, bold=True)
            txt_surf = font.render("AUTOSAVED", True, (240, 253, 244))
            base.blit(txt_surf, (28, (self._badge_h - txt_surf.get_height()) // 2))

            if pygame.display.get_surface() is not None:
                try:
                    base = base.convert_alpha()
                except Exception:
                    pass

            self._badge_base_surf = base
            self._badge_draw_surf = base.copy()
        except Exception as e:
            print(f"[WARN] Failed to initialize autosave badge surface: {e}")
            self._badge_base_surf = None
            self._badge_draw_surf = None

    def notify_saved(self) -> None:
        """Called whenever a save operation completes to trigger the on-screen badge."""
        self.indicator_timer = self.indicator_duration
        self.last_save_time = time.time()

    def _compute_state_signature(self) -> tuple:
        """Computes a compact tuple representing player progress to detect meaningful changes."""
        mm = self.main_menu
        if not mm:
            return None

        screen = getattr(mm, 'current_screen', '')
        if screen == 'stage_select' and getattr(mm, 'stage_select', None):
            ss = mm.stage_select
            return (
                'ss',
                int(getattr(ss, 'player_x', 0)),
                int(getattr(ss, 'player_y', 0)),
                getattr(ss, 'oldman_dialogue_state', 0),
                getattr(ss, 'knight_dialogue_state', 0),
                getattr(ss, 'skeleton_dialogue_state', 0),
                getattr(ss, 'bromen_dialogue_state', 0),
                getattr(ss, 'barriers_lifted', False)
            )
        elif screen in ('quarter1', 'quarter2', 'quarter3', 'quarter4'):
            q = getattr(mm, screen, None)
            if q:
                ans_count = len(getattr(q, 'answered_stations', [])) if hasattr(q, 'answered_stations') else 0
                return (
                    screen,
                    getattr(q, 'map_name', ''),
                    int(getattr(q, 'player_x', 0)),
                    int(getattr(q, 'player_y', 0)),
                    getattr(q, 'quiz_state', 0),
                    getattr(q, 'quiz_station_index', 0),
                    getattr(q, 'current_question_index', 0),
                    ans_count,
                    getattr(q, 'puzzle_solved', False) or getattr(q, 'addition_puzzle_solved', False)
                )
        return None

    def trigger_autosave(self, reason: str = "periodic", force: bool = False) -> bool:
        """Triggers an atomic save of current student progress."""
        if not self.main_menu:
            return False

        # Student must be logged in
        has_student = bool(getattr(self.main_menu, 'selected_student', None) or getattr(self.main_menu, 'student_id', None))
        if not has_student:
            return False

        # Only autosave in active gameplay screens
        active_screens = ("stage_select", "stageselect", "quarter1", "quarter2", "quarter3", "quarter4")
        if getattr(self.main_menu, 'current_screen', '') not in active_screens:
            return False

        # Avoid saving when pause menu or exit pop-ups are active
        if getattr(self.main_menu, 'popup_state', None):
            return False

        now = time.time()
        if not force and (now - self.last_save_time < self.min_event_interval):
            return False

        try:
            from db.save_system import save_student_progress
            ok = save_student_progress(self.main_menu)
            if ok:
                self.last_save_time = now
                self.last_state_signature = self._compute_state_signature()
                self.indicator_timer = self.indicator_duration
                return True
        except Exception as e:
            print(f"[WARN] Autosave failed ({reason}): {e}")
        return False

    def update(self, dt: float = 0.016) -> None:
        """Frame update hook to count down indicator and trigger periodic autosaves."""
        # 1. Update indicator timer
        if self.indicator_timer > 0.0:
            self.indicator_timer = max(0.0, self.indicator_timer - dt)

        # 2. Check periodic autosave timer
        now = time.time()
        if now - self.last_save_time >= self.interval_seconds:
            # Check if student is logged in and in gameplay
            active_screens = ("stage_select", "stageselect", "quarter1", "quarter2", "quarter3", "quarter4")
            curr_screen = getattr(self.main_menu, 'current_screen', '')
            has_student = bool(getattr(self.main_menu, 'selected_student', None) or getattr(self.main_menu, 'student_id', None))

            if has_student and curr_screen in active_screens and not getattr(self.main_menu, 'popup_state', None):
                curr_sig = self._compute_state_signature()
                # Only write to disk if state changed (moved, answered, progressed) or 60s max elapsed
                if curr_sig != self.last_state_signature or (now - self.last_save_time >= self.interval_seconds * 2):
                    self.trigger_autosave(reason="periodic_timer")

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the subtle autosave indicator badge at top-right with smooth fade."""
        if self.indicator_timer <= 0.0 or not self._badge_base_surf or not surface:
            return

        # Alpha curve: fast fade-in (0.2s), steady hold, smooth fade-out (0.5s)
        fade_in_time = 0.2
        fade_out_time = 0.5
        elapsed = self.indicator_duration - self.indicator_timer

        if elapsed < fade_in_time:
            alpha = int(240 * (elapsed / fade_in_time))
        elif self.indicator_timer < fade_out_time:
            alpha = int(240 * (self.indicator_timer / fade_out_time))
        else:
            alpha = 240

        alpha = max(0, min(240, alpha))
        if alpha <= 0:
            return

        # Position: neatly beneath top-right HUD buttons (Guide/Pause buttons are at y=18, h=36)
        screen_w = surface.get_width()
        badge_x = screen_w - self._badge_w - 20
        badge_y = 62

        # In StageSelect or MainMenu, align under pause button / upper-right
        self._badge_draw_surf.blit(self._badge_base_surf, (0, 0))
        self._badge_draw_surf.set_alpha(alpha)
        surface.blit(self._badge_draw_surf, (badge_x, badge_y))
