# core/puzzles/currency_puzzle.py - Decoupled Philippine Currency Cognitive Puzzle
"""
Decoupled Philippine Currency Matching Puzzle for Cognitive Quest.

Extracted from monolithic Quarter 2 scene script into a standalone data-driven module.
Focuses on Numerical Reasoning, Working Memory, and Philippine Currency literacy (BSP NGC).

Target Hardware Constraint:
- AMD A4-6300 APU: Vector-rendered banknotes and coins are generated once and cached.
- Dragging uses simple point-in-rect without re-allocating textures.
"""

from typing import Optional, Dict, Any, Tuple, List
import pygame
from core.puzzles.base_puzzle import BaseCognitivePuzzle
from core.font_manager import get_font
from core.philippine_currency import PHILIPPINE_CURRENCY


class CurrencyItem:
    """Represents a draggable coin or banknote in the currency puzzle."""
    __slots__ = (
        'item_id', 'currency_key', 'value', 'label', 'color', 'is_coin',
        'rect', 'initial_pos', 'is_in_tray', 'is_dragging', 'drag_offset_x', 'drag_offset_y',
        'surface'
    )

    def __init__(
        self,
        item_id: int,
        currency_key: str,
        value: int,
        label: str,
        color: Tuple[int, int, int],
        is_coin: bool,
        surface: pygame.Surface,
        initial_pos: Tuple[int, int]
    ):
        self.item_id: int = item_id
        self.currency_key: str = currency_key
        self.value: int = value
        self.label: str = label
        self.color: Tuple[int, int, int] = color
        self.is_coin: bool = is_coin
        self.surface: pygame.Surface = surface
        self.initial_pos: Tuple[int, int] = initial_pos
        self.rect: pygame.Rect = pygame.Rect(initial_pos[0], initial_pos[1], surface.get_width(), surface.get_height())
        self.is_in_tray: bool = False
        self.is_dragging: bool = False
        self.drag_offset_x: int = 0
        self.drag_offset_y: int = 0


class CurrencyPuzzle(BaseCognitivePuzzle):
    """
    Decoupled Philippine Currency Puzzle Engine.
    Player drags coins and bills to match an exact target amount.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_machine=None,
        audio_manager=None,
        screen_size: Tuple[int, int] = (1280, 720)
    ):
        self.target_value: int = 150
        self.items: List[CurrencyItem] = []
        self.dragged_item: Optional[CurrencyItem] = None
        self.source_bank_rect: pygame.Rect = pygame.Rect(60, 120, 480, 480)
        self.target_tray_rect: pygame.Rect = pygame.Rect(620, 120, 580, 480)
        self.current_sum: int = 0

        super().__init__(config=config, state_machine=state_machine, audio_manager=audio_manager, screen_size=screen_size)

    def load_config(self, config: Dict[str, Any]) -> None:
        self.puzzle_id = config.get("id", "q2_currency")
        self.title = config.get("title", "Quarter 2 Philippine Currency Matching")
        self.quarter = config.get("quarter", 2)
        self.cognitive_domain = config.get("cognitive_domain", "Numerical Reasoning")
        self.target_value = int(config.get("target_value", 150))
        self.time_limit = float(config.get("time_limit", 120.0))

        denominations = config.get("denominations", ["bill_20", "bill_50", "bill_100", "coin_10", "coin_5", "coin_1"])
        self._init_currency_items(denominations)

    def _init_currency_items(self, denominations: List[str]) -> None:
        self.items.clear()
        self.dragged_item = None
        self.current_sum = 0
        self.is_completed = False

        font_label = get_font("Comic Sans MS", 18, bold=True)
        item_id = 0

        # Create item representations
        start_x = self.source_bank_rect.x + 20
        start_y = self.source_bank_rect.y + 20
        col_gap = 150
        row_gap = 85

        for i, key in enumerate(denominations):
            curr_info = PHILIPPINE_CURRENCY.get(key)
            if not curr_info:
                val = 20
                label = f"₱{val}"
                color = (200, 100, 50)
                is_coin = False
            else:
                val = curr_info.get("value", 20)
                label = curr_info.get("symbol", f"₱{val}")
                color = curr_info.get("main_color", (200, 100, 50))
                is_coin = curr_info.get("type") == "coin"

            # Create memoized surface
            if is_coin:
                w, h = 60, 60
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (w // 2, h // 2), 28)
                pygame.draw.circle(surf, (255, 255, 255), (w // 2, h // 2), 28, 2)
                txt = font_label.render(label, True, (255, 255, 255))
                surf.blit(txt, ((w - txt.get_width()) // 2, (h - txt.get_height()) // 2))
            else:
                w, h = 130, 65
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(surf, color, (0, 0, w, h), border_radius=6)
                pygame.draw.rect(surf, (255, 255, 255), (0, 0, w, h), width=2, border_radius=6)
                txt = font_label.render(label, True, (255, 255, 255))
                surf.blit(txt, ((w - txt.get_width()) // 2, (h - txt.get_height()) // 2))

            gx = (i % 3) * col_gap
            gy = (i // 3) * row_gap
            pos = (start_x + gx, start_y + gy)

            item = CurrencyItem(item_id, key, val, label, color, is_coin, surf, pos)
            self.items.append(item)
            item_id += 1

    def _recalculate_sum(self) -> None:
        self.current_sum = sum(item.value for item in self.items if item.is_in_tray)
        if self.current_sum == self.target_value:
            self.is_completed = True
            self.score = max(100, int(1000 - (self.time_elapsed * 5) - (self.mistakes * 25)))
            self._play_sfx("victory")

    def update(self, dt: float) -> None:
        if not self.is_active or self.is_completed:
            return

        self.time_elapsed += dt

        if self.dragged_item:
            mx, my = pygame.mouse.get_pos()
            self.dragged_item.rect.x = mx - self.dragged_item.drag_offset_x
            self.dragged_item.rect.y = my - self.dragged_item.drag_offset_y

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        if not self.is_active:
            return False

        if self.close_btn_rect.collidepoint(pos):
            self.close()
            return True

        if self.is_completed:
            return True

        # Check pickup from top of stack
        for item in reversed(self.items):
            if item.rect.collidepoint(pos):
                item.is_dragging = True
                item.drag_offset_x = pos[0] - item.rect.x
                item.drag_offset_y = pos[1] - item.rect.y
                self.dragged_item = item

                self.items.remove(item)
                self.items.append(item)
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

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragged_item:
                item = self.dragged_item
                item.is_dragging = False
                self.dragged_item = None

                # Check if dropped in Target Tray
                if self.target_tray_rect.colliderect(item.rect):
                    item.is_in_tray = True
                else:
                    # Return to initial bank pos
                    item.is_in_tray = False
                    item.rect.topleft = item.initial_pos

                self._recalculate_sum()
                return True

        return True

    def draw(self, screen: pygame.Surface) -> None:
        if not self.is_active:
            return

        self.draw_common_ui(screen)

        # Title
        title_font = get_font("Comic Sans MS", 28, bold=True)
        title_surf = title_font.render(self.title, True, (255, 235, 120))
        screen.blit(title_surf, ((self.screen_width - title_surf.get_width()) // 2, 25))

        # Target banner
        sub_font = get_font("Comic Sans MS", 22, bold=True)
        target_text = f"Target Amount: ₱{self.target_value}   |   Current Tray Sum: ₱{self.current_sum}"
        target_color = (100, 255, 120) if self.current_sum == self.target_value else (255, 220, 100)
        target_surf = sub_font.render(target_text, True, target_color)
        screen.blit(target_surf, ((self.screen_width - target_surf.get_width()) // 2, 65))

        # Bank Container
        pygame.draw.rect(screen, (30, 35, 50), self.source_bank_rect, border_radius=10)
        pygame.draw.rect(screen, (80, 100, 140), self.source_bank_rect, width=2, border_radius=10)
        bank_lbl = sub_font.render("Available Currency (Bank)", True, (180, 200, 220))
        screen.blit(bank_lbl, (self.source_bank_rect.x + 15, self.source_bank_rect.y - 28))

        # Tray Container
        pygame.draw.rect(screen, (20, 45, 35), self.target_tray_rect, border_radius=10)
        pygame.draw.rect(screen, (50, 180, 100), self.target_tray_rect, width=2, border_radius=10)
        tray_lbl = sub_font.render("Cash Register Tray (Drop Here)", True, (120, 230, 150))
        screen.blit(tray_lbl, (self.target_tray_rect.x + 15, self.target_tray_rect.y - 28))

        # Draw items (non-dragged first)
        for item in self.items:
            if not item.is_dragging:
                screen.blit(item.surface, item.rect.topleft)

        # Draw dragged item on top
        if self.dragged_item:
            screen.blit(self.dragged_item.surface, self.dragged_item.rect.topleft)
            pygame.draw.rect(screen, (255, 255, 100), self.dragged_item.rect, 2)

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
            v_surf = v_font.render("Exact Change Matched! +100 Points", True, (255, 255, 255))
            screen.blit(v_surf, (victory_rect.centerx - (v_surf.get_width() // 2), victory_rect.y + 25))

            v_desc = sub_font.render(f"Solved in {self.time_elapsed:.1f}s | Press ESC to Exit", True, (200, 255, 200))
            screen.blit(v_desc, (victory_rect.centerx - (v_desc.get_width() // 2), victory_rect.y + 80))
