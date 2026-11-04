# core/puzzles/base_puzzle.py - Abstract Base Cognitive Puzzle Architecture
"""
Abstract Base Class for Cognitive Quest Puzzles.

Decouples cognitive minigame logic, UI interaction, event handling, and rendering
from scene scripts into a clean, modular, lifecycle-driven system.

Target Hardware Constraint:
- AMD A4-6300 APU (Dual-Core, 1MB L2 cache, 0MB L3 cache, Radeon HD 8370D).
- Zero per-frame memory allocations in update() and draw() hot loops.
- All surface transformations cached / memoized.
- Input strictly isolated from player overworld walking.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import pygame
from core.state_machine import State, UIStateMachine


class BaseCognitivePuzzle(ABC):
    """
    Base class that every cognitive puzzle in Cognitive Quest must inherit from.
    Provides standard lifecycle management, state machine integration, and event isolation.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        state_machine: Optional[UIStateMachine] = None,
        audio_manager: Optional[Any] = None,
        screen_size: Tuple[int, int] = (1280, 720)
    ):
        self.config: Dict[str, Any] = config or {}
        self.state_machine: Optional[UIStateMachine] = state_machine
        self.audio_manager: Optional[Any] = audio_manager
        self.screen_width, self.screen_height = screen_size

        self.puzzle_id: str = self.config.get("id", "generic_puzzle")
        self.title: str = self.config.get("title", "Cognitive Puzzle")
        self.quarter: int = self.config.get("quarter", 1)
        self.cognitive_domain: str = self.config.get("cognitive_domain", "Working Memory")
        self.time_limit: float = float(self.config.get("time_limit", 120.0))
        self.time_elapsed: float = 0.0

        self.is_active: bool = False
        self.is_completed: bool = False
        self.score: int = 0
        self.mistakes: int = 0

        # Close button UI rect
        self.close_btn_rect = pygame.Rect(self.screen_width - 80, 20, 60, 40)

        # Call subclass initialization if config provided
        if self.config:
            self.load_config(self.config)

    def _play_sfx(self, sfx_name: str) -> None:
        """Plays puzzle sound effect compatibly across AudioManager.play_sfx and mock play_sound."""
        am = self.audio_manager
        if am is None:
            try:
                from core.audio_manager import audio_manager as _default_am
                am = _default_am
            except Exception:
                return
        if hasattr(am, 'play_sfx'):
            sfx_map = {
                "victory": "victory_fanfare",
                "error": "wrong",
                "click": "click",
                "snap": "snap",
            }
            am.play_sfx(sfx_map.get(sfx_name, sfx_name))
        elif hasattr(am, 'play_sound'):
            am.play_sound(sfx_name)

    @abstractmethod
    def load_config(self, config: Dict[str, Any]) -> None:
        """
        Parse and initialize puzzle components from a data-driven configuration dictionary.
        Must be implemented by concrete puzzles.
        """
        pass

    def open(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Activates the puzzle and pushes State.CognitivePuzzle to the State Machine.
        Freezes player overworld movement and pauses scene logic.
        """
        self.is_active = True
        self.time_elapsed = 0.0
        if self.state_machine:
            ctx = {"puzzle_id": self.puzzle_id, "quarter": self.quarter}
            if context:
                ctx.update(context)
            self.state_machine.push(State.CognitivePuzzle, ctx)

    def close(self, completed: bool = False) -> None:
        """
        Deactivates the puzzle and pops State.CognitivePuzzle, returning to State.Exploration.
        """
        self.is_active = False
        if completed:
            self.is_completed = True
        if self.state_machine and self.state_machine.current_state == State.CognitivePuzzle:
            self.state_machine.pop()

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Per-frame game loop update.
        Must avoid heap allocations in hot loops.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """
        Render puzzle UI, pieces, and feedback.
        Must use memoized surfaces or direct blits.
        """
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process user input events (keyboard, mouse motion, mouse buttons).
        Returns True if the event was consumed by the puzzle UI, blocking underlying handlers.
        """
        pass

    @abstractmethod
    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """
        Handle mouse click down at pos (x, y).
        Returns True if the click was consumed by a puzzle element or button.
        """
        pass

    def draw_common_ui(self, screen: pygame.Surface) -> None:
        """
        Renders common puzzle HUD elements: Darkened overlay, Title bar, Close button, and Timer.
        Zero allocation by using cached state machine dim surface.
        """
        if self.state_machine:
            self.state_machine.render_dim_overlay(screen, alpha=160)

        # Close button [X]
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.close_btn_rect.collidepoint(mouse_pos)
        btn_color = (220, 53, 69) if is_hover else (160, 40, 50)
        pygame.draw.rect(screen, btn_color, self.close_btn_rect, border_radius=6)
        pygame.draw.rect(screen, (255, 255, 255), self.close_btn_rect, width=2, border_radius=6)

        # Close button X icon
        cx = self.close_btn_rect.centerx
        cy = self.close_btn_rect.centery
        pygame.draw.line(screen, (255, 255, 255), (cx - 8, cy - 8), (cx + 8, cy + 8), 3)
        pygame.draw.line(screen, (255, 255, 255), (cx - 8, cy + 8), (cx + 8, cy - 8), 3)

    def is_solved(self) -> bool:
        """Returns True if puzzle completion criteria are met."""
        return self.is_completed

    def get_score(self) -> Dict[str, Any]:
        """Returns performance metrics for cognitive telemetry and reporting."""
        return {
            "puzzle_id": self.puzzle_id,
            "title": self.title,
            "quarter": self.quarter,
            "cognitive_domain": self.cognitive_domain,
            "completed": self.is_completed,
            "score": self.score,
            "mistakes": self.mistakes,
            "time_elapsed": round(self.time_elapsed, 2)
        }

    def reset(self) -> None:
        """Resets the puzzle state for replay."""
        self.time_elapsed = 0.0
        self.is_completed = False
        self.score = 0
        self.mistakes = 0
        if self.config:
            self.load_config(self.config)
