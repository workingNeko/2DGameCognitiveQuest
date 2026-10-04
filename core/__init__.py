# core/__init__.py
from .audio_manager import AudioManager, audio_manager
from .pause_menu import InGamePauseMenu
from .font_manager import get_font, install_font_cache, clear_font_cache
from .quiz_dialog import RPGQuizDialog
from .vector_icons import (
    draw_vector_star,
    draw_vector_lightbulb,
    draw_vector_arrow,
    draw_vector_replay,
    draw_vector_gem
)
from .visual_effects import (
    DustParticleSystem,
    SparkleParticleSystem,
    ScreenShake,
    SceneTransition,
    get_pulse_value,
    draw_aura_glow,
    draw_beacon_marker
)

__all__ = [
    "AudioManager",
    "audio_manager",
    "InGamePauseMenu",
    "get_font",
    "install_font_cache",
    "clear_font_cache",
    "RPGQuizDialog",
    "draw_vector_star",
    "draw_vector_lightbulb",
    "draw_vector_arrow",
    "draw_vector_replay",
    "draw_vector_gem",
    "DustParticleSystem",
    "SparkleParticleSystem",
    "ScreenShake",
    "SceneTransition",
    "get_pulse_value",
    "draw_aura_glow",
    "draw_beacon_marker"
]


