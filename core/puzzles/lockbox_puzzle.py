# core/puzzles/lockbox_puzzle.py - Decoupled Algebraic Key Lockbox Puzzle
"""
Decoupled Key Lockbox & Algebraic Equation Cognitive Puzzle for Quarter 4.

Extracted from monolithic Quarter 4 scene script.
Focuses on Algebraic Reasoning, Deductive Logic, and Symbol Manipulation.

Target Hardware Constraint:
- Target Hardware: Dials and keys rendered via cached vector primitives.
- Zero allocations during interaction.
"""

from typing import Optional, Dict, Any, Tuple, List
import pygame
from core.puzzles.base_puzzle import BaseCognitivePuzzle
from core.font_manager import get_font


class KeyItem:
    __slots__ = ('key_id', 'value', 'label', 'rect', 'is_selected')

    def __init__(self, key_id: int, value: int, label: str, rect: pygame.Rect):
        self.key_id = key_id
        self.value = value
        self.label = label
        self.rect = rect
        self.is_selected = False


class LockboxPuzzle(BaseCognitivePuzzle):
    """
    Decoupled Algebraic Lockbox Puzzle Engine.
    Player deduces the correct key or dial combination to unlock the ancient chest.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_machine=None,
        audio_manager=None,
        screen_size: Tuple[int, int] = (1280, 720)
    ):
        self.target_solution: int = 5
        self.clue_expression: str = "2x + 4 = 14  -->  x = ?"
        self.keys: List[KeyItem] = []
        self.selected_key: Optional[KeyItem] = None
        self.chest_rect: pygame.Rect = pygame.Rect(440, 160, 400, 240)
        self.unlock_btn_rect: pygame.Rect = pygame.Rect(540, 580, 200, 50)

        super().__init__(config=config, state_machine=state_machine, audio_manager=audio_manager, screen_size=screen_size)

    def load_config(self, config: Dict[str, Any]) -> None:
        self.puzzle_id = config.get("id", "q4_lockbox")
        self.title = config.get("title", "Summative Assessment Algebraic Key Lockbox")
        self.quarter = config.get("quarter", 4)
        self.cognitive_domain = config.get("cognitive_domain", "Algebraic Deductive Reasoning")
        self.target_solution = int(config.get("target_solution", 5))
        self.clue_expression = config.get("clue_expression", "2x + 4 = 14  (Solve for x)")
        self.time_limit = float(config.get("time_limit", 120.0))

        options = config.get("key_options", [3, 4, 5, 7, 8])
        self._init_keys(options)

    def _init_keys(self, options: List[int]) -> None:
        self.keys.clear()
        self.selected_key = None
        self.is_completed = False
        self.mistakes = 0

        total_keys = len(options)
        key_w, key_h = 90, 80
        spacing = 30
        total_w = (total_keys * key_w) + ((total_keys - 1) * spacing)
        start_x = (self.screen_width - total_w) // 2
        start_y = 440

        for i, val in enumerate(options):
            rx = start_x + (i * (key_w + spacing))
            rect = pygame.Rect(rx, start_y, key_w, key_h)
            self.keys.append(KeyItem(i, val, f"Key {val}", rect))

    def update(self, dt: float) -> None:
        if not self.is_active or self.is_completed:
            return
        self.time_elapsed += dt

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        if not self.is_active:
            return False

        if self.close_btn_rect.collidepoint(pos):
            self.close()
            return True

        if self.is_completed:
            return True

        # Check key selection
        for key in self.keys:
            if key.rect.collidepoint(pos):
                for other in self.keys:
                    other.is_selected = False
                key.is_selected = True
                self.selected_key = key
                self._play_sfx("click")
                return True

        # Check Unlock button
        if self.unlock_btn_rect.collidepoint(pos):
            if self.selected_key and self.selected_key.value == self.target_solution:
                self.is_completed = True
                self.score = max(100, int(1000 - (self.time_elapsed * 5) - (self.mistakes * 25)))
                self._play_sfx("victory")
            else:
                self.mistakes += 1
                self._play_sfx("error")
            return True

        return True

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_click(event.pos)

        return True

    def draw(self, screen: pygame.Surface) -> None:
        if not self.is_active:
            return

        self.draw_common_ui(screen)

        # Title
        title_font = get_font("Comic Sans MS", 28, bold=True)
        title_surf = title_font.render(self.title, True, (255, 235, 120))
        screen.blit(title_surf, ((self.screen_width - title_surf.get_width()) // 2, 25))

        # Chest Graphic
        pygame.draw.rect(screen, (70, 45, 20), self.chest_rect, border_radius=12)
        pygame.draw.rect(screen, (200, 160, 40), self.chest_rect, width=4, border_radius=12)

        # Keyhole & lock
        kh_center = (self.chest_rect.centerx, self.chest_rect.centery + 30)
        pygame.draw.circle(screen, (20, 20, 20), kh_center, 18)
        pygame.draw.polygon(screen, (20, 20, 20), [
            (kh_center[0] - 8, kh_center[1]),
            (kh_center[0] + 8, kh_center[1]),
            (kh_center[0] + 12, kh_center[1] + 25),
            (kh_center[0] - 12, kh_center[1] + 25)
        ])

        # Clue inscription
        clue_font = get_font("Comic Sans MS", 22, bold=True)
        clue_surf = clue_font.render(self.clue_expression, True, (255, 240, 180))
        screen.blit(clue_surf, (self.chest_rect.centerx - (clue_surf.get_width() // 2), self.chest_rect.y + 35))

        # Keys
        key_font = get_font("Comic Sans MS", 20, bold=True)
        for key in self.keys:
            if key.is_selected:
                pygame.draw.rect(screen, (240, 200, 60), key.rect, border_radius=10)
                pygame.draw.rect(screen, (255, 255, 255), key.rect, width=3, border_radius=10)
                txt_col = (20, 20, 20)
            else:
                pygame.draw.rect(screen, (60, 70, 90), key.rect, border_radius=10)
                pygame.draw.rect(screen, (130, 150, 180), key.rect, width=2, border_radius=10)
                txt_col = (230, 230, 250)

            k_txt = key_font.render(str(key.value), True, txt_col)
            screen.blit(k_txt, (key.rect.centerx - (k_txt.get_width() // 2), key.rect.centery - (k_txt.get_height() // 2)))

        # Unlock Button
        btn_hover = self.unlock_btn_rect.collidepoint(pygame.mouse.get_pos())
        btn_col = (180, 140, 30) if btn_hover else (140, 100, 20)
        pygame.draw.rect(screen, btn_col, self.unlock_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 240, 100), self.unlock_btn_rect, width=2, border_radius=8)

        btn_txt = clue_font.render("Insert Key", True, (255, 255, 255))
        screen.blit(btn_txt, (self.unlock_btn_rect.centerx - (btn_txt.get_width() // 2), self.unlock_btn_rect.centery - (btn_txt.get_height() // 2)))

        # Victory Banner
        if self.is_completed:
            victory_w, victory_h = 560, 140
            victory_rect = pygame.Rect(
                (self.screen_width - victory_w) // 2,
                (self.screen_height - victory_h) // 2,
                victory_w, victory_h
            )
            pygame.draw.rect(screen, (15, 65, 30), victory_rect, border_radius=12)
            pygame.draw.rect(screen, (60, 240, 120), victory_rect, width=3, border_radius=12)

            v_font = get_font("Comic Sans MS", 32, bold=True)
            v_surf = v_font.render("Lockbox Unlocked! +100 Points", True, (255, 255, 255))
            screen.blit(v_surf, (victory_rect.centerx - (v_surf.get_width() // 2), victory_rect.y + 25))

            v_desc = clue_font.render(f"Solved in {self.time_elapsed:.1f}s | Mistakes: {self.mistakes} | Press ESC to Exit", True, (200, 255, 200))
            screen.blit(v_desc, (victory_rect.centerx - (v_desc.get_width() // 2), victory_rect.y + 80))
