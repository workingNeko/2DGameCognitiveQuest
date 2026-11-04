# core/puzzles/array_matrix_puzzle.py - Decoupled Multiplication Array & Fraction Puzzle
"""
Decoupled Array Matrix & Fraction Cognitive Puzzle for Cognitive Quest Quarter 3.

Extracted and generalized from Solar Array / Fraction Bakery mini-puzzles.
Focuses on Numerical Multiplication, Visual Array Representation, and Fractional Partitioning.

Target Hardware Constraint:
- AMD A4-6300 APU: Cell geometry is pre-calculated into a list of pygame.Rect.
- Zero per-frame allocations during interactive cell toggling.
"""

from typing import Optional, Dict, Any, Tuple, List
import pygame
from core.puzzles.base_puzzle import BaseCognitivePuzzle
from core.font_manager import get_font


class ArrayCell:
    __slots__ = ('row', 'col', 'rect', 'is_selected')

    def __init__(self, row: int, col: int, rect: pygame.Rect):
        self.row = row
        self.col = col
        self.rect = rect
        self.is_selected = False


class ArrayMatrixPuzzle(BaseCognitivePuzzle):
    """
    Decoupled Array Matrix Puzzle Engine.
    Player toggles grid cells to fulfill a mathematical multiplication array or fraction quotient.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_machine=None,
        audio_manager=None,
        screen_size: Tuple[int, int] = (1280, 720)
    ):
        self.grid_rows: int = 4
        self.grid_cols: int = 6
        self.target_count: int = 12
        self.target_expression: str = "3 x 4 = 12"
        self.cells: List[ArrayCell] = []
        self.grid_container_rect: pygame.Rect = pygame.Rect(340, 140, 600, 420)
        self.submit_btn_rect: pygame.Rect = pygame.Rect(540, 580, 200, 50)

        super().__init__(config=config, state_machine=state_machine, audio_manager=audio_manager, screen_size=screen_size)

    def load_config(self, config: Dict[str, Any]) -> None:
        self.puzzle_id = config.get("id", "q3_array_matrix")
        self.title = config.get("title", "Quarter 3 Solar Array Matrix")
        self.quarter = config.get("quarter", 3)
        self.cognitive_domain = config.get("cognitive_domain", "Multiplicative Reasoning")
        self.grid_rows = int(config.get("rows", 4))
        self.grid_cols = int(config.get("cols", 6))
        self.target_count = int(config.get("target_count", 12))
        self.target_expression = config.get("target_expression", "Activate an array of 12 cells")
        self.time_limit = float(config.get("time_limit", 100.0))

        self._build_grid()

    def _build_grid(self) -> None:
        self.cells.clear()
        self.is_completed = False
        self.mistakes = 0

        cell_w = (self.grid_container_rect.width - ((self.grid_cols + 1) * 8)) // self.grid_cols
        cell_h = (self.grid_container_rect.height - ((self.grid_rows + 1) * 8)) // self.grid_rows

        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                cx = self.grid_container_rect.x + 8 + (c * (cell_w + 8))
                cy = self.grid_container_rect.y + 8 + (r * (cell_h + 8))
                rect = pygame.Rect(cx, cy, cell_w, cell_h)
                self.cells.append(ArrayCell(r, c, rect))

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

        # Check cell clicks
        for cell in self.cells:
            if cell.rect.collidepoint(pos):
                cell.is_selected = not cell.is_selected
                self._play_sfx("click")
                return True

        # Check Submit button
        if self.submit_btn_rect.collidepoint(pos):
            selected_count = sum(1 for c in self.cells if c.is_selected)
            if selected_count == self.target_count:
                self.is_completed = True
                self.score = max(100, int(1000 - (self.time_elapsed * 6) - (self.mistakes * 30)))
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

        # Title & instructions
        title_font = get_font("Comic Sans MS", 28, bold=True)
        title_surf = title_font.render(self.title, True, (255, 235, 120))
        screen.blit(title_surf, ((self.screen_width - title_surf.get_width()) // 2, 25))

        sub_font = get_font("Comic Sans MS", 20)
        selected_count = sum(1 for c in self.cells if c.is_selected)
        goal_text = f"Goal: {self.target_expression}  |  Currently Selected: {selected_count}/{self.target_count}"
        goal_surf = sub_font.render(goal_text, True, (160, 230, 255))
        screen.blit(goal_surf, ((self.screen_width - goal_surf.get_width()) // 2, 70))

        # Grid Container
        pygame.draw.rect(screen, (20, 30, 45), self.grid_container_rect, border_radius=12)
        pygame.draw.rect(screen, (50, 120, 190), self.grid_container_rect, width=3, border_radius=12)

        # Draw Cells
        for cell in self.cells:
            if cell.is_selected:
                pygame.draw.rect(screen, (40, 180, 220), cell.rect, border_radius=6)
                pygame.draw.rect(screen, (255, 255, 255), cell.rect, width=2, border_radius=6)
            else:
                pygame.draw.rect(screen, (40, 50, 70), cell.rect, border_radius=6)
                pygame.draw.rect(screen, (70, 85, 115), cell.rect, width=1, border_radius=6)

        # Submit Button
        btn_hover = self.submit_btn_rect.collidepoint(pygame.mouse.get_pos())
        btn_col = (40, 160, 80) if btn_hover else (30, 120, 60)
        pygame.draw.rect(screen, btn_col, self.submit_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), self.submit_btn_rect, width=2, border_radius=8)

        btn_txt = sub_font.render("Verify Array", True, (255, 255, 255))
        screen.blit(btn_txt, (self.submit_btn_rect.centerx - (btn_txt.get_width() // 2), self.submit_btn_rect.centery - (btn_txt.get_height() // 2)))

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
            v_surf = v_font.render("Matrix Calibrated! +100 Points", True, (255, 255, 255))
            screen.blit(v_surf, (victory_rect.centerx - (v_surf.get_width() // 2), victory_rect.y + 25))

            v_desc = sub_font.render(f"Solved in {self.time_elapsed:.1f}s | Mistakes: {self.mistakes} | Press ESC to Exit", True, (200, 255, 200))
            screen.blit(v_desc, (victory_rect.centerx - (v_desc.get_width() // 2), victory_rect.y + 80))
