# core/puzzles/__init__.py
"""
Data-Driven Cognitive Puzzle Subsystem.

Provides modular, decoupled cognitive minigames with lifecycle isolation,
zero-allocation rendering pipelines, and Pushdown Automata state integration.
"""

from .base_puzzle import BaseCognitivePuzzle
from .jigsaw_puzzle import JigsawPuzzle
from .currency_puzzle import CurrencyPuzzle
from .array_matrix_puzzle import ArrayMatrixPuzzle
from .lockbox_puzzle import LockboxPuzzle
from .puzzle_factory import PuzzleFactory, PuzzleRegistry

__all__ = [
    "BaseCognitivePuzzle",
    "JigsawPuzzle",
    "CurrencyPuzzle",
    "ArrayMatrixPuzzle",
    "LockboxPuzzle",
    "PuzzleFactory",
    "PuzzleRegistry"
]
