# core/puzzles/puzzle_factory.py - Data-Driven Cognitive Puzzle Factory & Registry
"""
Puzzle Factory and Registry for Cognitive Quest.

Enables data-driven puzzle instantiation:
- Reads JSON puzzle configuration files from datasets/puzzles/
- Instantiates concrete puzzle engines dynamically via PuzzleRegistry
- Injects UIStateMachine and AudioManager dependencies cleanly
- Caches parsed configuration payloads to avoid disk I/O in the game loop

Target Hardware Constraint:
- Target Hardware: Zero disk hits during gameplay; configs cached on first load.
"""

import os
import json
from typing import Dict, Type, Optional, Any, Tuple
from core.puzzles.base_puzzle import BaseCognitivePuzzle
from core.puzzles.jigsaw_puzzle import JigsawPuzzle
from core.puzzles.currency_puzzle import CurrencyPuzzle
from core.puzzles.array_matrix_puzzle import ArrayMatrixPuzzle
from core.puzzles.lockbox_puzzle import LockboxPuzzle
from core.paths import resolve_path


class PuzzleRegistry:
    """Registry maintaining mapping between puzzle type keys and puzzle classes."""

    _registry: Dict[str, Type[BaseCognitivePuzzle]] = {
        "jigsaw": JigsawPuzzle,
        "currency": CurrencyPuzzle,
        "philippine_currency": CurrencyPuzzle,
        "array_matrix": ArrayMatrixPuzzle,
        "solar_array": ArrayMatrixPuzzle,
        "lockbox": LockboxPuzzle,
        "key_lockbox": LockboxPuzzle,
    }

    @classmethod
    def register(cls, type_name: str, puzzle_cls: Type[BaseCognitivePuzzle]) -> None:
        """Register a new puzzle implementation dynamically."""
        cls._registry[type_name.lower()] = puzzle_cls

    @classmethod
    def get(cls, type_name: str) -> Optional[Type[BaseCognitivePuzzle]]:
        """Retrieve puzzle class by type name."""
        return cls._registry.get(type_name.lower())

    @classmethod
    def list_types(cls) -> list:
        """List all registered puzzle type names."""
        return list(cls._registry.keys())


class PuzzleFactory:
    """
    Factory for instantiating cognitive puzzles from data configurations or JSON files.
    """

    _config_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_json_config(cls, file_path: str) -> Dict[str, Any]:
        """Loads and caches a JSON configuration from disk."""
        abs_path = resolve_path(file_path)
        if abs_path in cls._config_cache:
            return cls._config_cache[abs_path]

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Puzzle config file not found: {abs_path}")

        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cls._config_cache[abs_path] = data
        return data

    @classmethod
    def create_puzzle(
        cls,
        puzzle_type_or_config: Any,
        state_machine=None,
        audio_manager=None,
        screen_size: Tuple[int, int] = (1280, 720)
    ) -> BaseCognitivePuzzle:
        """
        Instantiates a puzzle instance.
        puzzle_type_or_config can be:
        1. A type string (e.g. 'jigsaw')
        2. A dictionary containing 'type' and configuration parameters
        """
        if isinstance(puzzle_type_or_config, str):
            p_type = puzzle_type_or_config
            cfg = {"type": p_type}
        elif isinstance(puzzle_type_or_config, dict):
            cfg = puzzle_type_or_config
            p_type = cfg.get("type", "jigsaw")
        else:
            raise ValueError(f"Invalid puzzle configuration type: {type(puzzle_type_or_config)}")

        puzzle_cls = PuzzleRegistry.get(p_type)
        if not puzzle_cls:
            raise ValueError(
                f"Unknown puzzle type '{p_type}'. Registered types: {PuzzleRegistry.list_types()}"
            )

        return puzzle_cls(
            config=cfg,
            state_machine=state_machine,
            audio_manager=audio_manager,
            screen_size=screen_size
        )

    @classmethod
    def from_json(
        cls,
        json_path: str,
        state_machine=None,
        audio_manager=None,
        screen_size: Tuple[int, int] = (1280, 720)
    ) -> BaseCognitivePuzzle:
        """Instantiates a puzzle directly from a JSON configuration file."""
        config = cls.load_json_config(json_path)
        return cls.create_puzzle(
            config,
            state_machine=state_machine,
            audio_manager=audio_manager,
            screen_size=screen_size
        )

    @classmethod
    def clear_cache(cls) -> None:
        """Clears cached JSON configurations."""
        cls._config_cache.clear()
