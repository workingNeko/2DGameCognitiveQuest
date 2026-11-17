# core/dev_cheats.py
"""
Centralized Developer Cheats & Debug Navigation Suite for Cognitive Maze.
Provides simple single-key function shortcuts (F1-F8) and mnemonic key chords
(Ctrl+S, Ctrl+N, Ctrl+W, Ctrl+P, Ctrl+A, U, Ctrl+Shift+R) for rapid game testing,
level design, and automated QA.

Target Hardware Compliant (AMD A4-6300 dual-core):
- Pre-caches rendered font glyphs and surfaces to avoid per-frame allocations.
- Zero CPU/GC overhead when HUD is idle.
"""

import math
import random
import time
import pygame

from core.font_manager import install_font_cache
install_font_cache()


class DevCheatManager:
    """Singleton manager for developer shortcuts, speed boosts, no-clip, and debug overlay."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.overlay_visible = False
        self.dev_superspeed = False
        self.dev_noclip = False

        # Toast state
        self.toast_msg = ""
        self.toast_until = 0
        self.toast_panel_surf = None
        self.toast_panel_pos = (0, 0)

        # Cached HUD surface to guarantee zero per-frame heap allocations
        self._cached_hud_surf = None
        self._cached_hud_w = 340
        self._cached_hud_h = 300
        self._cached_hud_key = None

    def show_toast(self, main_menu, message, sfx="click"):
        """Displays a clean developer toast notification in the top center/right."""
        self.toast_msg = message
        self.toast_until = pygame.time.get_ticks() + 2500

        font = pygame.font.SysFont("Comic Sans MS", 13, bold=True)
        txt_surf = font.render(message, True, (255, 255, 255))
        pad_x, pad_y = 16, 8
        panel_w = txt_surf.get_width() + pad_x * 2
        panel_h = txt_surf.get_height() + pad_y * 2

        self.toast_panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(self.toast_panel_surf, (15, 23, 42, 235), (0, 0, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(self.toast_panel_surf, (250, 204, 21), (0, 0, panel_w, panel_h), 2, border_radius=8)
        self.toast_panel_surf.blit(txt_surf, (pad_x, pad_y))
        self.toast_panel_surf = self.toast_panel_surf.convert_alpha()

        scr_w = main_menu.w if hasattr(main_menu, 'w') else 1280
        self.toast_panel_pos = ((scr_w - panel_w) // 2, 22)

        if sfx and hasattr(main_menu, 'audio_manager') and main_menu.audio_manager:
            main_menu.audio_manager.play_sfx(sfx)

    def toggle_overlay(self, main_menu):
        """Toggles the Developer Cheats HUD Guide on/off."""
        self.overlay_visible = not self.overlay_visible
        msg = "⚡ DEV CHEATS: Guide HUD ON" if self.overlay_visible else "⚡ DEV CHEATS: Guide HUD OFF"
        self.show_toast(main_menu, msg, sfx="click")

    def toggle_superspeed(self, main_menu):
        """Toggles player sprint speed between normal (2.5) and dev speed (6.0)."""
        self.dev_superspeed = not self.dev_superspeed
        main_menu.dev_superspeed = self.dev_superspeed

        for attr in ('stage_select', 'quarter1', 'quarter2', 'quarter3', 'quarter4', 'tutorial'):
            obj = getattr(main_menu, attr, None)
            if obj:
                obj.dev_superspeed = self.dev_superspeed

        if self.dev_superspeed:
            self.show_toast(main_menu, "⚡ DEV CHEAT: Super Speed ON (6.0)", sfx="success")
        else:
            self.show_toast(main_menu, "⚡ DEV CHEAT: Super Speed OFF (2.5)", sfx="snap")

    def toggle_noclip(self, main_menu):
        """Toggles walking through walls, barricades, water, and obstacles."""
        self.dev_noclip = not self.dev_noclip
        main_menu.dev_noclip = self.dev_noclip

        for attr in ('stage_select', 'quarter1', 'quarter2', 'quarter3', 'quarter4', 'tutorial'):
            obj = getattr(main_menu, attr, None)
            if obj:
                obj.dev_noclip = self.dev_noclip

        if self.dev_noclip:
            self.show_toast(main_menu, "⚡ DEV CHEAT: No-Clip ON (Pass Through Walls)", sfx="success")
        else:
            self.show_toast(main_menu, "⚡ DEV CHEAT: No-Clip OFF", sfx="snap")

    def complete_stage(self, main_menu):
        """Auto-completes question stations, solves puzzles, unlocks exit portal & teleports."""
        curr = getattr(main_menu, 'current_screen', '')
        screen_obj = getattr(main_menu, curr, None)

        if curr in ('quarter1', 'quarter2', 'quarter3', 'quarter4') and screen_obj:
            if hasattr(screen_obj, 'complete_all_objectives_shortcut'):
                screen_obj.complete_all_objectives_shortcut()
                self.show_toast(main_menu, f"⚡ DEV CHEAT: {curr.upper()} Objectives Completed & Portal Unlocked!", sfx="victory_fanfare")
                return True
        elif curr in ('stage_select', 'stageselect') or screen_obj is getattr(main_menu, 'stage_select', None):
            self.unlock_all(main_menu)
            return True

        self.show_toast(main_menu, "⚡ DEV CHEAT: Complete Stage triggered", sfx="success")
        return False

    def auto_answer_quiz(self, main_menu):
        """Instantly selects the correct answer in the active question/quiz dialog."""
        curr = getattr(main_menu, 'current_screen', '')
        screen_obj = getattr(main_menu, curr, None)

        if screen_obj and getattr(screen_obj, 'quiz_state', 0) == 1:
            questions = getattr(screen_obj, 'quiz_questions', [])
            q_idx = getattr(screen_obj, 'current_question_index', 0)
            if questions and 0 <= q_idx < len(questions):
                q_data = questions[q_idx]
                c_idx = q_data.get("correct", 0)
                if isinstance(c_idx, str) and c_idx.isdigit():
                    c_idx = int(c_idx)

                # Advance quiz state to correct (state 3)
                screen_obj.quiz_state = 3
                screen_obj.current_correct_phrase = "⚡ Developer Cheat: Correct Answer Auto-Submitted!"
                if hasattr(screen_obj, 'eliminated_choices'):
                    screen_obj.eliminated_choices.clear()

                if hasattr(screen_obj, 'celebration_particles'):
                    w = getattr(screen_obj, 'width', 1280)
                    h = getattr(screen_obj, 'height', 720)
                    screen_obj.celebration_particles.spawn_burst(w // 2, h // 2, count=25)

                self.show_toast(main_menu, f"⚡ DEV CHEAT: Correct Answer #{c_idx + 1} Submitted!", sfx="correct")
                return True

        self.show_toast(main_menu, "⚡ DEV CHEAT: No active question quiz dialog open", sfx="snap")
        return False

    def unlock_all(self, main_menu):
        """Unlocks all Quarters (1-4), removes hub barriers, and unlocks all Summative Assessments."""
        # 1. Main menu persistent data
        if not hasattr(main_menu, 'last_stage_select_data') or not isinstance(main_menu.last_stage_select_data, dict):
            main_menu.last_stage_select_data = {}
        main_menu.last_stage_select_data["barriers_lifted"] = True

        # 2. Stage select active instance
        if hasattr(main_menu, 'stage_select') and main_menu.stage_select:
            st_sel = main_menu.stage_select
            st_sel.barriers_lifted = True
            st_sel.completed_quarters = {'quarter1': True, 'quarter2': True, 'quarter3': True, 'quarter4': True}
            st_sel.locked_portal_banner_msg = "Shortcut: All Stages & Portals Unlocked! (Q1-Q4)"
            st_sel.locked_portal_banner_timer = 3.0

            # Unlock all cards in the summative assessment modal
            if hasattr(st_sel, 'summative_modal_cards'):
                for c in st_sel.summative_modal_cards:
                    c["locked"] = False

        self.show_toast(main_menu, "⚡ DEV CHEAT: All Stages & Assessments Unlocked!", sfx="success")

    def teleport_to_portal(self, main_menu):
        """Teleports player directly to the active exit portal."""
        curr = getattr(main_menu, 'current_screen', '')
        screen_obj = getattr(main_menu, curr, None)
        if screen_obj is None and curr in ('stage_select', 'stageselect'):
            screen_obj = getattr(main_menu, 'stage_select', None)

        if screen_obj and hasattr(screen_obj, 'portals') and screen_obj.portals:
            p = screen_obj.portals[0]
            if hasattr(p, 'get_world_x') and hasattr(p, 'get_world_y'):
                screen_obj.player_x = p.get_world_x()
                screen_obj.player_y = p.get_world_y()
            elif hasattr(p, 'tile_x') and hasattr(p, 'tile_y'):
                screen_obj.player_x = p.tile_x * 32
                screen_obj.player_y = p.tile_y * 32
            elif hasattr(p, 'x') and hasattr(p, 'y'):
                screen_obj.player_x = p.x * 32
                screen_obj.player_y = p.y * 32
            elif hasattr(p, 'rect'):
                screen_obj.player_x = p.rect.centerx - 16
                screen_obj.player_y = p.rect.centery - 16

            if hasattr(screen_obj, 'lol_camera') and screen_obj.lol_camera:
                map_w = getattr(screen_obj, 'MAP_WIDTH', 50)
                map_h = getattr(screen_obj, 'MAP_HEIGHT', 50)
                screen_obj.lol_camera.snap_to(screen_obj.player_x, screen_obj.player_y, 32, map_w, map_h)
            self.show_toast(main_menu, "⚡ DEV CHEAT: Teleported to Exit Portal!", sfx="snap")
            return True

        self.show_toast(main_menu, "⚡ DEV CHEAT: No active portal found to teleport to", sfx="snap")
        return False

    def reset_progress(self, main_menu):
        """Clears all stage progression for the selected student to allow clean testing."""
        if hasattr(main_menu, 'selected_student') and main_menu.selected_student:
            st = main_menu.selected_student
            st["completed_quarters"] = {}
            st["quarter_grades"] = {}
            st["scores"] = {}
            st["progress"] = {}
            from db.save_system import save_student_progress
            save_student_progress(main_menu)

        if hasattr(main_menu, 'stage_select') and main_menu.stage_select:
            main_menu.stage_select.completed_quarters = {}
            main_menu.stage_select.barriers_lifted = False
            main_menu.stage_select.oldman_dialogue_state = 0
            main_menu.stage_select.bromen_dialogue_state = 0
            main_menu.stage_select.skeleton_dialogue_state = 0
            main_menu.stage_select.knight_dialogue_state = 0

        self.show_toast(main_menu, "⚡ DEV CHEAT: Student Progress Reset to Clean Slate!", sfx="snap")

    def handle_event(self, event, main_menu):
        """Processes developer cheat hotkeys globally. Returns True if a cheat was handled."""
        if event.type != pygame.KEYDOWN:
            return False

        # Bypass single-letter cheats when student is actively typing in a search bar or identification quiz
        _typing_active = (
            (getattr(main_menu, 'current_screen', '') == "quarter3"
             and getattr(main_menu, 'quarter3', None) is not None
             and getattr(main_menu.quarter3, "quiz_state", 0) == 1
             and getattr(main_menu.quarter3, "q_type", "") == "identification")
            or (getattr(main_menu, 'current_screen', '') == "student_select"
                and getattr(main_menu, 'student_select', None) is not None
                and getattr(main_menu.student_select, "search_active", False))
        )

        key = event.key
        mods = getattr(event, 'mod', 0) or (pygame.key.get_mods() if hasattr(pygame.key, 'get_mods') else 0)
        ctrl = bool(mods & pygame.KMOD_CTRL)
        shift = bool(mods & pygame.KMOD_SHIFT)

        # 1. Toggle Dev HUD Guide: [F1] or [~] or [Ctrl+H]
        if key in (pygame.K_F1, pygame.K_BACKQUOTE) or (ctrl and key == pygame.K_h):
            self.toggle_overlay(main_menu)
            return True

        # 2. Super Speed (6.0): [F3] or [Ctrl+S]
        if key == pygame.K_F3 or (ctrl and key == pygame.K_s):
            self.toggle_superspeed(main_menu)
            return True

        # 3. No-Clip (Walk Through Walls): [F4] or [Ctrl+N]
        if key == pygame.K_F4 or (ctrl and key == pygame.K_n):
            self.toggle_noclip(main_menu)
            return True

        # 4. Complete Stage & Objectives: [F5] or [Ctrl+W]
        if key == pygame.K_F5 or (ctrl and key == pygame.K_w):
            self.complete_stage(main_menu)
            return True

        # 5. Auto-Answer Current Question: [F6] or [Ctrl+A]
        if key == pygame.K_F6 or (ctrl and key == pygame.K_a):
            self.auto_answer_quiz(main_menu)
            return True

        # 6. Unlock All Stages & Assessments: [F7] or ([U] when not typing)
        if key == pygame.K_F7 or (not _typing_active and not ctrl and key == pygame.K_u):
            self.unlock_all(main_menu)
            return True

        # 7. Teleport to Exit Portal: [F8] or [Ctrl+P]
        if key == pygame.K_F8 or (ctrl and key == pygame.K_p):
            self.teleport_to_portal(main_menu)
            return True

        # 8. Reset Student Progress: [Ctrl+Shift+R]
        if ctrl and shift and key == pygame.K_r:
            self.reset_progress(main_menu)
            return True

        return False

    def draw(self, screen, main_menu):
        """Draws developer cheat overlay HUD and active toast banner with zero allocations."""
        now = pygame.time.get_ticks()

        # 1. Render Toast Banner
        if self.toast_until > now and self.toast_panel_surf is not None:
            screen.blit(self.toast_panel_surf, self.toast_panel_pos)

        # 2. Render Dev Cheat Overlay HUD (F1)
        if self.overlay_visible:
            # Rebuild cache only when status changes
            curr_key = (self.dev_superspeed, self.dev_noclip, getattr(main_menu, 'current_screen', ''))
            if self._cached_hud_surf is None or self._cached_hud_key != curr_key:
                self._cached_hud_surf = self._build_hud_surface(main_menu)
                self._cached_hud_key = curr_key

            screen.blit(self._cached_hud_surf, (20, 20))

    def _build_hud_surface(self, main_menu):
        """Builds a cached semi-transparent developer HUD card."""
        w, h = self._cached_hud_w, self._cached_hud_h
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Glass panel styling
        pygame.draw.rect(surf, (15, 23, 42, 235), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(surf, (56, 189, 248), (0, 0, w, h), 2, border_radius=10)

        title_font = pygame.font.SysFont("Comic Sans MS", 14, bold=True)
        body_font = pygame.font.SysFont("Comic Sans MS", 11)
        key_font = pygame.font.SysFont("Comic Sans MS", 11, bold=True)

        # Title bar
        t_surf = title_font.render("⚡ DEVELOPER CHEATS", True, (250, 204, 21))
        f1_tag = body_font.render("[F1] Close", True, (148, 163, 184))
        surf.blit(t_surf, (14, 12))
        surf.blit(f1_tag, (w - f1_tag.get_width() - 14, 14))

        pygame.draw.line(surf, (51, 65, 85), (12, 38), (w - 12, 38), 1)

        # Shortcut rows
        rows = [
            ("[F1] / [~]", "Toggle This Cheats HUD"),
            ("[F3] / [Ctrl+S]", f"Super Speed: {'6.0 (ACTIVE)' if self.dev_superspeed else 'OFF (2.5)'}"),
            ("[F4] / [Ctrl+N]", f"No-Clip (Walls): {'ON (ACTIVE)' if self.dev_noclip else 'OFF'}"),
            ("[F5] / [Ctrl+W]", "Complete Stage & Win"),
            ("[F6] / [Ctrl+A]", "Auto-Answer Quiz Correct"),
            ("[F7] / [U]", "Unlock All Stages/Assess"),
            ("[F8] / [Ctrl+P]", "Teleport to Exit Portal"),
            ("[Ctrl+Shift+R]", "Reset Student Progress"),
        ]

        y = 48
        for k_text, desc_text in rows:
            # Highlight active toggles
            is_active = (
                ("Super Speed" in desc_text and self.dev_superspeed)
                or ("No-Clip" in desc_text and self.dev_noclip)
            )
            col_k = (250, 204, 21) if is_active else (56, 189, 248)
            col_d = (74, 222, 128) if is_active else (226, 232, 240)

            k_surf = key_font.render(k_text, True, col_k)
            d_surf = body_font.render(desc_text, True, col_d)
            surf.blit(k_surf, (14, y))
            surf.blit(d_surf, (126, y))
            y += 26

        pygame.draw.line(surf, (51, 65, 85), (12, y + 2), (w - 12, y + 2), 1)

        # Status footer
        curr_screen = getattr(main_menu, 'current_screen', 'main_menu')
        stat_text = f"Screen: {curr_screen.upper()} | Speed: {'6.0' if self.dev_superspeed else '2.5'}"
        stat_surf = body_font.render(stat_text, True, (148, 163, 184))
        surf.blit(stat_surf, (14, y + 8))

        return surf.convert_alpha()
