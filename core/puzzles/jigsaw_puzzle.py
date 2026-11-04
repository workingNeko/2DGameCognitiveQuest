# core/puzzles/jigsaw_puzzle.py - Decoupled Data-Driven Jigsaw Puzzle
"""
Decoupled Jigsaw Puzzle Engine for Cognitive Quest.

Extracted from monolithic scene script into a standalone, data-driven module.
Handles grid decomposition, piece shuffling, drag-and-drop mechanics, snap tolerance,
and completion validation.

Target Hardware Constraint:
- AMD A4-6300 APU: Piece surfaces are sliced and memoized once during load_config().
- No dynamic surface allocations during dragging or rendering loops.
"""

import os
import random
from typing import Optional, Dict, Any, Tuple, List
import pygame
from core.puzzles.base_puzzle import BaseCognitivePuzzle
from core.font_manager import get_font


class JigsawPiece:
    """Represents a single jigsaw tile with its target and current screen coordinates."""
    __slots__ = (
        'piece_id', 'correct_col', 'correct_row', 'current_rect',
        'target_rect', 'is_snapped', 'is_dragging', 'drag_offset_x', 'drag_offset_y',
        'surface'
    )

    def __init__(self, piece_id: int, col: int, row: int, surface: pygame.Surface, target_rect: pygame.Rect):
        self.piece_id: int = piece_id
        self.correct_col: int = col
        self.correct_row: int = row
        self.surface: pygame.Surface = surface
        self.target_rect: pygame.Rect = target_rect
        self.current_rect: pygame.Rect = target_rect.copy()
        self.is_snapped: bool = False
        self.is_dragging: bool = False
        self.drag_offset_x: int = 0
        self.drag_offset_y: int = 0


class JigsawPuzzle(BaseCognitivePuzzle):
    """
    Decoupled Jigsaw / Spatial Reasoning Puzzle.
    Loads grid specifications, image asset, and snap tolerance from data configuration.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_machine=None,
        audio_manager=None,
        screen_size: Tuple[int, int] = (1280, 720)
    ):
        self.rows: int = 2
        self.cols: int = 2
        self.snap_tolerance: int = 35
        self.pieces: List[JigsawPiece] = []
        self.dragged_piece: Optional[JigsawPiece] = None
        self.board_rect: pygame.Rect = pygame.Rect(0, 0, 400, 400)
        self.tray_rect: pygame.Rect = pygame.Rect(0, 0, 400, 400)
        self.source_image: Optional[pygame.Surface] = None
        self.font = None

        super().__init__(config=config, state_machine=state_machine, audio_manager=audio_manager, screen_size=screen_size)

    def load_config(self, config: Dict[str, Any]) -> None:
        """Configures puzzle board dimensions, image source, and slices tiles."""
        self.puzzle_id = config.get("id", "q1_jigsaw")
        self.title = config.get("title", "Quarter 1 Geometric Jigsaw")
        self.quarter = config.get("quarter", 1)
        self.cognitive_domain = config.get("cognitive_domain", "Spatial Reasoning")
        self.rows = int(config.get("rows", 2))
        self.cols = int(config.get("cols", 3))
        self.snap_tolerance = int(config.get("snap_tolerance", 35))
        self.time_limit = float(config.get("time_limit", 90.0))

        board_w = int(config.get("board_width", 480))
        board_h = int(config.get("board_height", 360))
        board_x = (self.screen_width // 2) - board_w - 40
        board_y = (self.screen_height // 2) - (board_h // 2) + 20
        self.board_rect = pygame.Rect(board_x, board_y, board_w, board_h)

        tray_x = (self.screen_width // 2) + 40
        tray_y = board_y
        self.tray_rect = pygame.Rect(tray_x, tray_y, board_w, board_h)

        # Generate or load image
        image_path = config.get("image_path")
        if image_path and os.path.exists(image_path):
            loaded = pygame.image.load(image_path).convert_alpha()
            self.source_image = pygame.transform.smoothscale(loaded, (board_w, board_h))
        else:
            # Procedural fallback pattern (geometric gradients)
            self.source_image = pygame.Surface((board_w, board_h), pygame.SRCALPHA)
            self.source_image.fill((30, 60, 110))
            for i in range(0, board_w, 40):
                pygame.draw.line(self.source_image, (60, 120, 200), (i, 0), (i + 40, board_h), 2)
            pygame.draw.circle(self.source_image, (255, 200, 50), (board_w // 2, board_h // 2), min(board_w, board_h) // 3)

        self._slice_and_shuffle_pieces()

    def _slice_and_shuffle_pieces(self) -> None:
        """Slices source surface into grid pieces and places unsnapped pieces in tray."""
        self.pieces.clear()
        self.dragged_piece = None
        self.is_completed = False
        self.mistakes = 0

        piece_w = self.board_rect.width // self.cols
        piece_h = self.board_rect.height // self.rows

        piece_idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                target_x = self.board_rect.x + (c * piece_w)
                target_y = self.board_rect.y + (r * piece_h)
                target_rect = pygame.Rect(target_x, target_y, piece_w, piece_h)

                # Slice piece sub-surface memoized
                sub_surf = pygame.Surface((piece_w, piece_h), pygame.SRCALPHA)
                sub_surf.blit(self.source_image, (0, 0), pygame.Rect(c * piece_w, r * piece_h, piece_w, piece_h))
                # Add subtle inner border
                pygame.draw.rect(sub_surf, (200, 200, 220), (0, 0, piece_w, piece_h), 1)
                if pygame.display.get_surface() is not None:
                    try:
                        sub_surf = sub_surf.convert_alpha()
                    except Exception:
                        pass

                piece = JigsawPiece(piece_idx, c, r, sub_surf, target_rect)
                self.pieces.append(piece)
                piece_idx += 1

        # Scatter pieces into the tray area
        for p in self.pieces:
            rand_x = random.randint(self.tray_rect.x + 10, self.tray_rect.right - piece_w - 10)
            rand_y = random.randint(self.tray_rect.y + 10, self.tray_rect.bottom - piece_h - 10)
            p.current_rect.topleft = (rand_x, rand_y)
            p.is_snapped = False

    def update(self, dt: float) -> None:
        if not self.is_active or self.is_completed:
            return

        self.time_elapsed += dt

        # Update dragged piece position with mouse
        if self.dragged_piece:
            mx, my = pygame.mouse.get_pos()
            self.dragged_piece.current_rect.x = mx - self.dragged_piece.drag_offset_x
            self.dragged_piece.current_rect.y = my - self.dragged_piece.drag_offset_y

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        if not self.is_active:
            return False

        # Close button clicked
        if self.close_btn_rect.collidepoint(pos):
            self.close()
            return True

        if self.is_completed:
            return True

        # Check piece pickup (iterate backwards to pick top-rendered piece)
        for piece in reversed(self.pieces):
            if not piece.is_snapped and piece.current_rect.collidepoint(pos):
                piece.is_dragging = True
                piece.drag_offset_x = pos[0] - piece.current_rect.x
                piece.drag_offset_y = pos[1] - piece.current_rect.y
                self.dragged_piece = piece

                # Bring picked piece to the top of the render list
                self.pieces.remove(piece)
                self.pieces.append(piece)
                return True

        # Click inside board or tray consumed
        if self.board_rect.collidepoint(pos) or self.tray_rect.collidepoint(pos):
            return True

        return True  # Consume all clicks while puzzle overlay is active

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
            if self.dragged_piece:
                p = self.dragged_piece
                p.is_dragging = False
                self.dragged_piece = None

                # Test snap to target rect
                dist_x = abs(p.current_rect.x - p.target_rect.x)
                dist_y = abs(p.current_rect.y - p.target_rect.y)
                if dist_x <= self.snap_tolerance and dist_y <= self.snap_tolerance:
                    p.current_rect.topleft = p.target_rect.topleft
                    p.is_snapped = True
                    self._play_sfx("snap")

                    # Check overall completion
                    if all(piece.is_snapped for piece in self.pieces):
                        self.is_completed = True
                        self.score = max(100, int(1000 - (self.time_elapsed * 5) - (self.mistakes * 20)))
                        self._play_sfx("victory")
                else:
                    # If released over board but not matching target, count as mistake
                    if self.board_rect.colliderect(p.current_rect):
                        self.mistakes += 1

                return True

        return True  # Reroute and swallow all events during minigame

    def draw(self, screen: pygame.Surface) -> None:
        if not self.is_active:
            return

        # Common HUD & Dimmed World Background
        self.draw_common_ui(screen)

        # Title & Domain Banner
        title_font = get_font("Comic Sans MS", 30, bold=True)
        title_surf = title_font.render(self.title, True, (255, 235, 120))
        screen.blit(title_surf, ((self.screen_width - title_surf.get_width()) // 2, 25))

        subtitle_font = get_font("Comic Sans MS", 18)
        sub_text = f"Domain: {self.cognitive_domain} | Snapped: {sum(1 for p in self.pieces if p.is_snapped)}/{len(self.pieces)}"
        sub_surf = subtitle_font.render(sub_text, True, (200, 220, 240))
        screen.blit(sub_surf, ((self.screen_width - sub_surf.get_width()) // 2, 65))

        # Target Board Frame
        pygame.draw.rect(screen, (20, 30, 45), self.board_rect, border_radius=8)
        pygame.draw.rect(screen, (70, 130, 180), self.board_rect, width=3, border_radius=8)

        # Board grid guidelines
        piece_w = self.board_rect.width // self.cols
        piece_h = self.board_rect.height // self.rows
        for r in range(self.rows):
            for c in range(self.cols):
                cell_rect = pygame.Rect(self.board_rect.x + (c * piece_w), self.board_rect.y + (r * piece_h), piece_w, piece_h)
                pygame.draw.rect(screen, (35, 55, 80), cell_rect, 1)

        # Tray Frame
        pygame.draw.rect(screen, (25, 25, 35), self.tray_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 140), self.tray_rect, width=2, border_radius=8)

        # Draw Snapped Pieces first
        for piece in self.pieces:
            if piece.is_snapped:
                screen.blit(piece.surface, piece.current_rect.topleft)
                pygame.draw.rect(screen, (40, 200, 60), piece.current_rect, 1)

        # Draw Unsnapped Pieces (non-dragged)
        for piece in self.pieces:
            if not piece.is_snapped and not piece.is_dragging:
                screen.blit(piece.surface, piece.current_rect.topleft)
                pygame.draw.rect(screen, (240, 240, 255), piece.current_rect, 1)

        # Draw Currently Dragged Piece on top
        if self.dragged_piece:
            screen.blit(self.dragged_piece.surface, self.dragged_piece.current_rect.topleft)
            pygame.draw.rect(screen, (255, 230, 100), self.dragged_piece.current_rect, 2)

        # Completion Victory Banner
        if self.is_completed:
            victory_w, victory_h = 520, 140
            victory_rect = pygame.Rect(
                (self.screen_width - victory_w) // 2,
                (self.screen_height - victory_h) // 2,
                victory_w, victory_h
            )
            pygame.draw.rect(screen, (20, 70, 30), victory_rect, border_radius=12)
            pygame.draw.rect(screen, (50, 220, 100), victory_rect, width=3, border_radius=12)

            v_font = get_font("Comic Sans MS", 34, bold=True)
            v_surf = v_font.render("Puzzle Solved! +100 Quest Points", True, (255, 255, 255))
            screen.blit(v_surf, (victory_rect.centerx - (v_surf.get_width() // 2), victory_rect.y + 25))

            v_desc = subtitle_font.render(f"Time: {self.time_elapsed:.1f}s | Mistakes: {self.mistakes} | Press ESC to Exit", True, (200, 255, 200))
            screen.blit(v_desc, (victory_rect.centerx - (v_desc.get_width() // 2), victory_rect.y + 80))
