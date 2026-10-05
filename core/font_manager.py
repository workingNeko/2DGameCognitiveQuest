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
    # Variation Selectors & Control Characters
    "\ufe0e": "",           # text presentation selector
    "\ufe0f": "",           # emoji variation selector
    "\ufeff": "",           # zero-width non-breaking space / BOM
    "\u200b": "",           # zero-width space
    "\u200c": "",           # zero-width non-joiner
    "\u200d": "",           # zero-width joiner
    "\u00ad": "",           # soft hyphen
    "\u00a0": " ",          # non-breaking space
    "\u202f": " ",          # narrow no-break space
    "\u2000": " ", "\u2001": " ", "\u2002": " ", "\u2003": " ", "\u2004": " ", "\u2005": " ",
    "\u2006": " ", "\u2007": " ", "\u2008": " ", "\u2009": " ", "\u200a": " ",

    # Smart Quotes & Apostrophes
    "\u2018": "'",          # left single curly quote
    "\u2019": "'",          # right single curly quote / apostrophe
    "\u201a": "'",          # single low-9 quote
    "\u201b": "'",          # single high-reversed-9 quote
    "\u201c": '"',          # left double curly quote
    "\u201d": '"',          # right double curly quote
    "\u201e": '"',          # double low-9 quote
    "\u201f": '"',          # double high-reversed-9 quote
    "\u00ab": '"',          # left-pointing double angle quote
    "\u00bb": '"',          # right-pointing double angle quote
    "\u2039": "'",          # single left-pointing angle quote
    "\u203a": "'",          # single right-pointing angle quote
    "\u2032": "'",          # prime (feet/minutes)
    "\u2033": '"',          # double prime (inches/seconds)
    "\u2035": "'",          # reversed prime
    "\u00b4": "'",          # acute accent
    "\u0060": "'",          # grave accent

    # Dashes & Hyphens
    "\u2014": "-",          # em dash
    "\u2013": "-",          # en dash
    "\u2015": "-",          # horizontal bar
    "\u2012": "-",          # figure dash
    "\u2010": "-",          # hyphen
    "\u2011": "-",          # non-breaking hyphen
    "\u2212": "-",          # mathematical minus sign

    # Arrows & Directional Indicators
    "\u2192": "->",         # right arrow
    "\u2190": "<-",         # left arrow
    "\u2191": "^",          # up arrow
    "\u2193": "v",          # down arrow
    "\u2794": "->",         # heavy wide-headed rightwards arrow
    "\u27a4": "->",         # black rightwards arrowhead
    "\u27a1": "->",         # black rightwards arrow
    "\u279c": "->",         # heavy round-tipped rightwards arrow
    "\u21d2": "=>",         # rightwards double arrow
    "\u21d0": "<=",         # leftwards double arrow
    "\u21ba": "",           # counterclockwise arrow
    "\u21bb": "",           # clockwise arrow
    "\u25c4": "<",          # left pointer
    "\u25ba": ">",          # right pointer
    "\u25b2": "^",          # up triangle
    "\u25bc": "v",          # down triangle
    "\u25be": ">",          # small down triangle
    "\u25b6": ">",          # black right-pointing triangle
    "\u25c0": "<",          # black left-pointing triangle
    "\u23e9": ">>",         # fast-forward
    "\u23ea": "<<",         # fast-rewind
    "\u23f8": "||",         # pause
    "\u23f5": ">",          # play button
    "\u23f4": "<",          # reverse play

    # Stars, Badges & Sparkles
    "\u2b50": "*",          # star emoji
    "\u2605": "*",          # black star
    "\u2606": "*",          # white star
    "\u2726": "+",          # 4-point star
    "\u2727": "*",          # white 4-pointed star
    "\u2728": "*",          # sparkles emoji
    "\u272a": "*",          # circled white star
    "\u2730": "*",          # shadowed star
    "\u273f": "*",          # black florette
    "\u2740": "*",          # white florette
    "\u2742": "*",          # circled open centre eight pointed star
    "\u2743": "*",          # heavy teardrop-spoked asterisk
    "\u274a": "*",          # eight teardrop-spoked asterisk
    "\U0001f31f": "*",      # glowing star
    "\U0001f320": "*",      # shooting star
    "\U0001f3c6": "[Trophy]",# trophy emoji
    "\U0001f389": "*",      # party popper emoji
    "\U0001f451": "[Crown]", # crown emoji

    # Checks, Crosses & Math Symbols
    "\u2713": "v",          # check mark
    "\u2714": "v",          # heavy check mark
    "\u2705": "[OK]",       # white heavy check mark
    "\u2715": "x",          # multiplication X
    "\u2716": "x",          # heavy multiplication X
    "\u2717": "x",          # ballot X
    "\u2718": "x",          # heavy ballot X
    "\u274c": "[X]",        # cross mark
    "\u274e": "[X]",        # negative squared cross mark
    "\u00d7": "x",          # multiplication sign
    "\u00f7": "/",          # division sign
    "\u2264": "<=",         # less-than or equal
    "\u2265": ">=",         # greater-than or equal
    "\u2260": "!=",         # not equal to
    "\u2248": "~",          # almost equal to
    "\u00b1": "+/-",        # plus-minus
    "\u221a": "sqrt",       # square root
    "\u00b2": "^2",         # superscript 2
    "\u00b3": "^3",         # superscript 3
    "\u00bd": "1/2",        # vulgar fraction 1/2
    "\u00bc": "1/4",        # vulgar fraction 1/4
    "\u00be": "3/4",        # vulgar fraction 3/4
    "\u00b0": " deg",       # degree sign
    "\u03c0": "pi",         # greek pi
    "\u221e": "inf",        # infinity
    "\u2220": "angle ",     # angle
    "\u25b3": "triangle ",  # white up-pointing triangle
    "\u2070": "^0", "\u2071": "^1", "\u2074": "^4", "\u2075": "^5",
    "\u2076": "^6", "\u2077": "^7", "\u2078": "^8", "\u2079": "^9",
    "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3", "\u2084": "4",
    "\u2085": "5", "\u2086": "6", "\u2087": "7", "\u2088": "8", "\u2089": "9",

    # Bullets, Dots & Geometric Shapes
    "\u2022": "-",          # bullet point
    "\u2023": ">",          # triangular bullet
    "\u2043": "-",          # hyphen bullet
    "\u25e6": "o",          # white bullet
    "\u25aa": "-",          # black small square
    "\u25ab": "-",          # white small square
    "\u25a0": "-",          # black square
    "\u25a1": "[]",         # white square
    "\u25cf": "*",          # black circle
    "\u25cb": "o",          # white circle
    "\u25c6": "*",          # black diamond
    "\u25c7": "*",          # white diamond
    "\u25c8": "*",          # white diamond containing black small diamond
    "\u25ca": "*",          # lozenge
    "\u2026": "...",        # ellipsis

    # Currency
    "\u20b1": "P",          # Philippine Peso
    "\u0024": "$",          # Dollar
    "\u00a2": "c",          # Cent
    "\u00a3": "GBP ",       # Pound
    "\u00a5": "JPY ",       # Yen
    "\u20ac": "EUR ",       # Euro

    # Gestures, Emojis & Icon Characters
    "\U0001f590": "",       # raised hand with fingers splayed
    "\u270b": "",           # raised hand
    "\U0001f91a": "",       # raised back of hand
    "\u270a": "",           # raised fist
    "\U0001f44a": "",       # oncoming fist
    "\U0001f91b": "",       # left-facing fist
    "\U0001f91c": "",       # right-facing fist
    "\u270c": "",           # victory hand / peace sign
    "\U0001f44d": "",       # thumbs up
    "\U0001f44e": "",       # thumbs down
    "\U0001f446": "",       # pointing up
    "\U0001f447": "",       # pointing down
    "\U0001f448": "",       # pointing left
    "\U0001f449": "",       # pointing right
    "\U0001f44b": "",       # waving hand
    "\U0001f4a1": "",       # lightbulb
    "\U0001f3af": "",       # dartboard / target
    "\U0001f5fa": "",       # map
    "\U0001f512": "",       # lock emoji
    "\U0001f513": "",       # unlock emoji
    "\U0001f4f7": "",       # camera emoji
    "\U0001f4f8": "",       # camera with flash
    "\U0001f534": "(Live)", # large red circle
    "\U0001f7e2": "(OK)",   # large green circle
    "\U0001f7e1": "(Wait)", # large yellow circle
    "\U0001f9d9": "",       # mage / wizard
    "\U0001f525": "",       # fire
    "\U0001f4da": "",       # books
    "\U0001f4d6": "",       # open book
    "\U0001f4dd": "",       # memo
    "\U0001f4c8": "",       # chart increasing
    "\U0001f4c9": "",       # chart decreasing
    "\U0001f9e9": "",       # puzzle piece
    "\U0001f91d": "",       # handshake
    "\U0001f464": "",       # bust in silhouette
    "\U0001f465": "",       # busts in silhouette
    "\U0001f308": "",       # rainbow
    "\U0001f514": "",       # bell
    "\U0001f515": "",       # bell with slash
    "\u2757": "!",          # heavy exclamation mark
    "\u2753": "?",          # heavy question mark
    "\u26a0": "[!]",        # warning sign
    "\u23f0": "",           # alarm clock
    "\u23f3": "",           # hourglass not done
    "\u231b": "",           # hourglass done
    "\u2699": "",           # gear
}


def sanitize_text(text):
    """
    Strips unrenderable emojis, symbols, control chars, and non-ASCII characters that cause
    'missing character boxes' (tofu boxes) in Pygame fonts.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # 1. Apply explicit replacements
    for char, rep in GLYPH_REPLACEMENTS.items():
        if char in text:
            text = text.replace(char, rep)

    # 2. Filter any remaining high unicode or control characters that could trigger missing glyph boxes
    clean_chars = []
    for ch in text:
        code = ord(ch)
        # Allow standard printable ASCII (32-126) and common Western/Latin-1 Supplement (160-255 like accented letters ñ, é, etc.)
        if 32 <= code <= 126 or 160 <= code <= 255:
            clean_chars.append(ch)
        elif ch in ('\n', '\r', '\t'):
            clean_chars.append(' ')
        elif code < 32:
            # Drop unprintable ASCII control characters
            continue
        else:
            # Fallback: drop any unsupported Unicode dingbats / surrogate pairs
            continue

    return "".join(clean_chars)


def wrap_multiline_text(text, font, max_width):
    """
    Universal, robust text wrapping engine that handles explicit newlines,
    paragraphs, long words, and font size constraints without text overflow.
    Guarantees that every returned line fits within max_width.
    """
    if text is None:
        return []
    text = str(text)
    if not text.strip():
        return []

    # Split into paragraphs by explicit linebreaks
    raw_paragraphs = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    lines = []

    for para in raw_paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        words = para_clean.split(' ')
        current_line = []

        for word in words:
            if not word:
                continue

            # Check if a single unbroken word exceeds max_width
            word_w = font.size(word)[0] if font else len(word) * 10
            if word_w > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                # Sub-chunk the long word by characters
                chunk = ""
                for char in word:
                    test_chunk = chunk + char
                    test_w = font.size(test_chunk)[0] if font else len(test_chunk) * 10
                    if test_w <= max_width:
                        chunk = test_chunk
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = char
                if chunk:
                    current_line = [chunk]
                continue

            # Standard word wrapping
            test_line = " ".join(current_line + [word])
            test_w = font.size(test_line)[0] if font else len(test_line) * 10
            if test_w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

    return lines


# Universal alias
wrap_text = wrap_multiline_text


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
        clean = sanitize_text(text)
        if background is not None:
            return super().render(clean, antialias, color, background)
        return super().render(clean, antialias, color)

    def size(self, text):
        clean = sanitize_text(text)
        return super().size(clean)


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

