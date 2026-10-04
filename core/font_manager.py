# core/font_manager.py
"""
High-Performance Font Management and Transparent Caching Engine.
Guarantees sub-millisecond font lookups by avoiding redundant OS registry
queries and font glyph rasterization on every frame.
Safely sanitizes unsupported unicode glyphs to eliminate missing-character boxes ('tofu').
"""

import pygame

_FONT_CACHE = {}
_ORIG_SYSFONT = None
_ORIG_FONT = None
_PATCHED = False


GLYPH_REPLACEMENTS = {
    "\U0001f4a1": "",       # lightbulb
    "\U0001f3af": "",       # dartboard / target
    "\U0001f5fa": "",       # map
    "\ufe0f": "",           # variation selector
    "\U0001f512": "",       # lock emoji
    "\U0001f513": "",       # unlock emoji
    "\U0001f3c6": "",       # trophy emoji
    "\U0001f389": "",       # party popper emoji
    "\u2713": "v",          # check mark
    "\u2714": "v",          # heavy check mark
    "\u2b50": "*",          # star emoji
    "\u2605": "*",          # black star
    "\u2726": "+",          # 4-point star
    "\u21ba": "",           # counterclockwise arrow
    "\u21bb": "",           # clockwise arrow
    "\u2192": "->",         # right arrow
    "\u2190": "<-",         # left arrow
    "\u2191": "^",          # up arrow
    "\u2193": "v",          # down arrow
    "\u25c4": "<",          # left pointer
    "\u25ba": ">",          # right pointer
    "\u25b2": "^",          # up triangle
    "\u25bc": "v",          # down triangle
    "\u25be": ">",          # small down triangle
    "\u2715": "X",          # multiplication X
    "\u2014": "-",          # em dash
    "\u2013": "-",          # en dash
    "\u00d7": "x",          # multiplication sign
    "\u00f7": "/",          # division sign
    "\u00b0": " deg",       # degree sign
    "\u2022": "-",          # bullet point
    "\u2026": "...",        # ellipsis
    "\u20b1": "P",          # Philippine Peso fallback
    "\u00a0": " ",          # non-breaking space
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
    # Filter out any lingering high-unicode surrogate/emoji characters > 0xFFFF
    clean_chars = [ch for ch in text if ord(ch) <= 0xFFFF]
    return "".join(clean_chars)


if not pygame.font.get_init():
    try:
        pygame.font.init()
    except Exception:
        pass

_ORIG_FONT = pygame.font.Font


class SafeFont(_ORIG_FONT):
    """
    Drop-in subclass of pygame.font.Font that sanitizes unrenderable glyphs
    before rendering or size calculation, preventing missing character tofu boxes.
    """
    def __init__(self, filename_or_fileobj=None, size=16, bold=False, italic=False):
        super().__init__(filename_or_fileobj, size)
        if bold:
            try:
                self.set_bold(True)
            except Exception:
                pass
        if italic:
            try:
                self.set_italic(True)
            except Exception:
                pass

    def render(self, text, antialias, color, background=None):
        if isinstance(text, str):
            text = sanitize_text(text)
        elif text is not None:
            text = sanitize_text(str(text))
        else:
            text = ""
        if background is not None:
            return super().render(text, antialias, color, background)
        return super().render(text, antialias, color)

    def size(self, text):
        if isinstance(text, str):
            text = sanitize_text(text)
        elif text is not None:
            text = sanitize_text(str(text))
        else:
            text = ""
        return super().size(text)


def _normalize_name(name):
    if isinstance(name, list):
        return tuple(str(x) for x in name)
    elif name is None:
        return ""
    return str(name)


def get_font(name="Comic Sans MS", size=16, bold=False, italic=False):
    """
    Retrieves a cached Pygame SafeFont instance.
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
            font = SafeFont(name, int(size), bold=bold, italic=italic)
        elif isinstance(name, (list, tuple)):
            font = _cached_sysfont(list(name), int(size), bold=bold, italic=italic)
        elif name is not None:
            font = _cached_sysfont(str(name), int(size), bold=bold, italic=italic)
        else:
            font = SafeFont(None, int(size), bold=bold, italic=italic)
    except Exception:
        try:
            font = SafeFont(None, int(size), bold=bold, italic=italic)
        except Exception:
            font = None

    if font is not None:
        _FONT_CACHE[key] = font
    return font


def _cached_sysfont(name, size, bold=False, italic=False, *args, **kwargs):
    """Cached drop-in replacement for pygame.font.SysFont using SafeFont."""
    key = (_normalize_name(name), int(size), bool(bold), bool(italic))
    font = _FONT_CACHE.get(key)
    if font is None:
        try:
            if _ORIG_SYSFONT is not None:
                font = _ORIG_SYSFONT(name, size, bold=bold, italic=italic, constructor=SafeFont)
            else:
                font = SafeFont(None, int(size), bold=bold, italic=italic)
        except Exception:
            font = SafeFont(None, int(size), bold=bold, italic=italic)
        _FONT_CACHE[key] = font
    return font


def install_font_cache():
    """
    Transparently installs the caching wrapper and SafeFont onto pygame.font.
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
    pygame.font.Font = SafeFont

    _PATCHED = True
    print("[OPTIMIZATION] Global Pygame Font Caching & SafeFont System installed successfully.")


def clear_font_cache():
    """Clears all cached font instances."""
    _FONT_CACHE.clear()


# Automatically initialize on module import
install_font_cache()

