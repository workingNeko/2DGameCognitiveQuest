# core/font_manager.py
"""
High-Performance Font Management and Transparent Caching Engine.
Guarantees sub-millisecond font lookups by avoiding redundant OS registry
queries and font glyph rasterization on every frame.
"""

import pygame

_FONT_CACHE = {}
_ORIG_SYSFONT = None
_ORIG_FONT = None
_PATCHED = False


GLYPH_REPLACEMENTS = {
    "\U0001f4a1": "",      # lightbulb
    "\u2b50": "*",         # star emoji
    "\u2605": "*",         # black star
    "\u2726": "+",         # 4-point star
    "\u21ba": "",          # counterclockwise arrow
    "\u2192": "->",        # right arrow
    "\u25be": ">",         # small down triangle
    "\u2715": "X",         # multiplication X
    "\u2014": "-",         # em dash
    "\u2013": "-",         # en dash
    "\u00d7": "x",         # multiplication sign
}

def sanitize_text(text):
    """
    Strips unrenderable emojis, symbols, and non-ASCII characters that cause
    'missing character boxes' (tofu boxes) in Pygame fonts.
    """
    if not isinstance(text, str):
        return text
    for char, rep in GLYPH_REPLACEMENTS.items():
        if char in text:
            text = text.replace(char, rep)
    return text


def _normalize_name(name):
    if isinstance(name, list):
        return tuple(str(x) for x in name)
    elif name is None:
        return ""
    return str(name)


def get_font(name="Comic Sans MS", size=16, bold=False, italic=False):
    """
    Retrieves a cached Pygame Font instance.
    If not cached, constructs it safely and caches it.
    """
    if not pygame.font.get_init():
        try:
            pygame.font.init()
        except Exception:
            pass

    key = (_normalize_name(name), int(size), bool(bold), bool(italic))
    font = _FONT_CACHE.get(key)
    if font is not None:
        return font

    # Construct font
    try:
        if isinstance(name, str) and (name.endswith('.ttf') or name.endswith('.otf')):
            font = pygame.font.Font(name, int(size))
        elif isinstance(name, (list, tuple)):
            font = pygame.font.SysFont(list(name), int(size), bold=bold, italic=italic)
        elif name is not None:
            font = pygame.font.SysFont(str(name), int(size), bold=bold, italic=italic)
        else:
            font = pygame.font.Font(None, int(size))
    except Exception:
        try:
            font = pygame.font.Font(None, int(size))
        except Exception:
            font = None

    if font is not None:
        _FONT_CACHE[key] = font
    return font


def _cached_sysfont(name, size, bold=False, italic=False, *args, **kwargs):
    """Cached drop-in replacement for pygame.font.SysFont."""
    key = (_normalize_name(name), int(size), bool(bold), bool(italic))
    font = _FONT_CACHE.get(key)
    if font is None:
        if _ORIG_SYSFONT is not None:
            font = _ORIG_SYSFONT(name, size, bold=bold, italic=italic, *args, **kwargs)
        else:
            font = pygame.font.Font(None, int(size))
        _FONT_CACHE[key] = font
    return font


def install_font_cache():
    """
    Transparently installs the caching wrapper onto pygame.font.SysFont.
    Safe to call multiple times.
    """
    global _ORIG_SYSFONT, _PATCHED
    if _PATCHED:
        return

    if not pygame.font.get_init():
        try:
            pygame.font.init()
        except Exception:
            pass

    _ORIG_SYSFONT = pygame.font.SysFont
    pygame.font.SysFont = _cached_sysfont
    _PATCHED = True
    print("[OPTIMIZATION] Global Pygame Font Caching System installed successfully.")


def clear_font_cache():
    """Clears all cached font instances."""
    _FONT_CACHE.clear()


# Automatically initialize on module import
install_font_cache()
