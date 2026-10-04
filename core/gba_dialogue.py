# core/gba_dialogue.py
"""
Game Boy Advance (GBA) Pokemon Emerald/Ruby Style Dialogue Box & Portrait System for Cognitive Quest 2D.
Renders authentic retro GBA dialogue frames with:
- Crisp dark outer border and inner white text canvas
- Signature left and right vertical crimson/coral accent bars with dark separator lines
- Character bust portrait of in-game NPCs & Player positioned naturally above the box on the right
- Deep Indigo Blue typography with Soft Periwinkle drop shadow
- Animated typewriter text rendering and retro blinking continue indicator
"""

import os
import math
import time
import pygame
from .font_manager import get_font, sanitize_text

# Cached portrait surfaces
_PORTRAIT_CACHE = {}
_BOX_SURFACE_CACHE = {}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _safe_load_image(path):
    """Safely loads an image handling display initialized or uninitialized states."""
    try:
        img = pygame.image.load(path)
        if pygame.display.get_surface() is not None:
            try:
                return img.convert_alpha()
            except Exception:
                return img
        return img
    except Exception:
        return None


def is_female_student(student_info):
    """Accurately checks whether the active student profile is female."""
    if isinstance(student_info, dict):
        gender = str(student_info.get("gender") or student_info.get("Gender") or student_info.get("sex") or "").strip().lower()
        if gender in ["female", "girl", "f", "woman"]:
            return True
        name = str(student_info.get("first_name") or student_info.get("name") or student_info.get("username") or "").strip().lower()
        if name in ["jessuny", "sarah", "maria", "anna", "princess", "lani"]:
            return True
    return False


def get_player_portrait(student_info=None, target_size=(230, 230)):
    """
    Loads and caches the authentic user player character portrait:
    - boy_front.png for male / default student
    - female_front.png (or girl_front.png) for female student
    """
    female = is_female_student(student_info)
    cache_key = ("player_portrait", female, target_size)
    if cache_key in _PORTRAIT_CACHE:
        return _PORTRAIT_CACHE[cache_key]

    surf = None
    if female:
        candidate_paths = [
            os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "player", "female_front.png"),
            os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "player", "girl_front.png"),
            os.path.join(BASE_DIR, "assets", "images", "girl.png"),
        ]
    else:
        candidate_paths = [
            os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "player", "boy_front.png"),
            os.path.join(BASE_DIR, "assets", "images", "boy.png"),
        ]

    for p in candidate_paths:
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)
                break

    if surf is None:
        fallback_path = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "player", "boy_front.png")
        if os.path.exists(fallback_path):
            img = _safe_load_image(fallback_path)
            if img:
                surf = pygame.transform.scale(img, target_size)

    _PORTRAIT_CACHE[cache_key] = surf
    return surf


def is_student_speaker(speaker_name, student_info=None):
    """Checks if the current dialogue speaker is the student/player."""
    if not speaker_name:
        return False
    sp_lower = str(speaker_name).strip().lower()
    if any(k in sp_lower for k in ["student", "player", "adventurer", "you", "hero"]):
        return True
    if isinstance(student_info, dict):
        first_name = str(student_info.get("first_name") or student_info.get("name") or student_info.get("username") or "").strip().lower()
        if first_name and (first_name in sp_lower or sp_lower == first_name):
            return True
    return False


def get_in_game_portrait(speaker_name=None, student_info=None, target_size=(230, 230)):
    """
    Loads and caches the character sprite portrait for dialogue:
    - If speaker is Student / Player -> Loads user's character (boy_front.png or female_front.png)
    - If speaker is Quarter NPC -> Loads that quarter NPC's authentic in-game sprite!
    """
    if speaker_name is None or is_student_speaker(speaker_name, student_info):
        return get_player_portrait(student_info, target_size)

    speaker_clean = str(speaker_name).strip()
    sp_lower = speaker_clean.lower()

    cache_key = (sp_lower, target_size)
    if cache_key in _PORTRAIT_CACHE:
        return _PORTRAIT_CACHE[cache_key]

    surf = None
    # 1. Old Man Wizard (Quarter 1 & Stage Select Sanctuary)
    if any(k in sp_lower for k in ["old", "mentor", "wizard", "sanctuary"]):
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "oldman", "oldman.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)

    # 2. Skeleton Guardian (Quarter 3 Monetary Desert Guardian)
    elif any(k in sp_lower for k in ["skeleton", "desert", "pharaoh", "ancient"]):
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "skeleton", "skeleton.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)

    # 3. Knight Guardian (Quarter 2 Barangay Kalye Guardian)
    elif any(k in sp_lower for k in ["knight", "kalye", "barangay", "guard"]):
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "knight", "knight.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)

    # 4. Bromen Guardian (Quarter 4 Water Temple Guardian)
    elif any(k in sp_lower for k in ["bromen", "water", "aqueduct", "voyager"]):
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "bromen", "bromen.png")
        if not os.path.exists(p):
            p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "NPC", "bromen", "sprite_bromen00.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)

    # 5. Quarter 1 Shape NPCs
    elif "circle" in sp_lower:
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "tiles", "quarter1tiles", "puzzleimages", "CircleNPC.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)
    elif "heart" in sp_lower:
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "tiles", "quarter1tiles", "puzzleimages", "HeartNPC.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)
    elif "square" in sp_lower:
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "tiles", "quarter1tiles", "puzzleimages", "SquareNPC.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)
    elif "star" in sp_lower:
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "tiles", "quarter1tiles", "puzzleimages", "StarNPC.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)
    elif "diamond" in sp_lower:
        p = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "tiles", "quarter1tiles", "puzzleimages", "DiamondNPC.png")
        if os.path.exists(p):
            img = _safe_load_image(p)
            if img:
                surf = pygame.transform.scale(img, target_size)

    # Default fallback to player
    if surf is None:
        surf = get_player_portrait(student_info, target_size)

    _PORTRAIT_CACHE[cache_key] = surf
    return surf


def draw_gba_dialogue(
    screen,
    screen_width,
    screen_height,
    speaker_name,
    text_content,
    char_index=None,
    student_info=None,
    frame_counter=0,
    show_portrait=True,
    portrait_override=None
):
    """
    Draws a 16-bit GBA Pokemon Emerald/Ruby style RPG dialogue box.
    Renders the speaker's in-game portrait:
    - User's Character (boy_front.png / female_front.png) when the student speaks
    - Quarter NPC Guardian sprite when the NPC speaks
    
    Parameters:
    - screen: Pygame surface to render on
    - screen_width, screen_height: Screen dimensions
    - speaker_name: String name of the current speaker (e.g. "Skeleton", "Old Man", "Student")
    - text_content: The full dialogue string to display
    - char_index: Float or int for typewriter progression (if None, draws full text)
    - student_info: Optional dict of active student profile for gender-accurate player portraits
    - frame_counter: Animation tick for blinking indicators
    - show_portrait: Boolean whether to render character bust behind the box
    - portrait_override: Optional explicit Surface to override the portrait
    """
    if not text_content:
        return

    # Box dimensions
    box_w = min(screen_width - 40, 840)
    box_h = 168
    box_x = (screen_width - box_w) // 2
    box_y = screen_height - box_h - 16

    # ----------------------------------------------------
    # 1. DRAW SPEAKER CHARACTER PORTRAIT (Layered Behind Box on Right)
    # ----------------------------------------------------
    portrait_surf = None
    if show_portrait:
        if portrait_override is not None:
            portrait_surf = portrait_override
        else:
            portrait_surf = get_in_game_portrait(speaker_name, student_info, target_size=(230, 230))

    if portrait_surf:
        pw, ph = portrait_surf.get_size()
        # Position bust on the right side so lower chest is covered by the box top edge
        px = box_x + box_w - pw - 24
        py = box_y - int(ph * 0.68)
        screen.blit(portrait_surf, (px, py))

    # ----------------------------------------------------
    # 2. DRAW GBA POKEMON STYLE DIALOGUE BOX FRAME
    # ----------------------------------------------------
    # Outer dark charcoal border (4px)
    pygame.draw.rect(screen, (34, 34, 38), (box_x, box_y, box_w, box_h), border_radius=8)

    # Inner crisp white canvas
    inner_x = box_x + 4
    inner_y = box_y + 4
    inner_w = box_w - 8
    inner_h = box_h - 8
    pygame.draw.rect(screen, (255, 255, 255), (inner_x, inner_y, inner_w, inner_h), border_radius=6)

    # Subtle inner bevel outline
    pygame.draw.rect(screen, (220, 224, 232), (inner_x + 1, inner_y + 1, inner_w - 2, inner_h - 2), width=1, border_radius=5)

    # Signature Left Vertical Crimson Accent Bar
    bar_w = 16
    left_bar_x = inner_x + 1
    pygame.draw.rect(screen, (218, 59, 59), (left_bar_x, inner_y + 1, bar_w, inner_h - 2))
    # Vertical dark separator line
    pygame.draw.line(screen, (34, 34, 38), (left_bar_x + bar_w, inner_y), (left_bar_x + bar_w, inner_y + inner_h), 2)
    # Left bar inner highlight
    pygame.draw.line(screen, (244, 114, 114), (left_bar_x + 1, inner_y + 2), (left_bar_x + 1, inner_y + inner_h - 2), 1)

    # Signature Right Vertical Crimson Accent Bar
    right_bar_x = inner_x + inner_w - bar_w - 1
    pygame.draw.rect(screen, (218, 59, 59), (right_bar_x, inner_y + 1, bar_w, inner_h - 2))
    # Vertical dark separator line
    pygame.draw.line(screen, (34, 34, 38), (right_bar_x, inner_y), (right_bar_x, inner_y + inner_h), 2)
    # Right bar inner shadow
    pygame.draw.line(screen, (168, 38, 38), (right_bar_x + bar_w - 1, inner_y + 2), (right_bar_x + bar_w - 1, inner_y + inner_h - 2), 1)

    # ----------------------------------------------------
    # 3. SPEAKER NAME BADGE (GBA Header Pill)
    # ----------------------------------------------------
    if speaker_name:
        badge_font = get_font("Comic Sans MS", 16, bold=True)
        is_student = is_student_speaker(speaker_name, student_info)
        
        display_name = speaker_name
        if is_student and isinstance(student_info, dict) and student_info.get("first_name"):
            display_name = student_info.get("first_name")

        name_clean = sanitize_text(display_name)
        text_sz = badge_font.size(name_clean)
        tag_w = text_sz[0] + 30
        tag_h = 28
        tag_x = box_x + 28
        tag_y = box_y - 14

        # Dark border pill
        pygame.draw.rect(screen, (34, 34, 38), (tag_x, tag_y, tag_w, tag_h), border_radius=6)
        # Inner white pill
        pygame.draw.rect(screen, (255, 255, 255), (tag_x + 2, tag_y + 2, tag_w - 4, tag_h - 4), border_radius=4)

        # Name colors
        sp_low = speaker_name.lower()
        if is_student:
            name_col = (22, 163, 74)      # Emerald Green for Player
        elif "old" in sp_low:
            name_col = (217, 119, 6)      # Amber / Wizard Gold
        elif "skeleton" in sp_low:
            name_col = (147, 51, 234)     # Purple / Sage
        elif "knight" in sp_low:
            name_col = (37, 99, 235)      # Blue / Knight
        elif "bromen" in sp_low:
            name_col = (13, 148, 136)     # Cyan / Aqua
        else:
            name_col = (56, 80, 136)      # Indigo Blue

        name_surf = badge_font.render(name_clean, True, name_col)
        screen.blit(name_surf, (tag_x + 15, tag_y + 4))

    # ----------------------------------------------------
    # 4. TYPOGRAPHY (GBA Indigo Blue with Periwinkle Drop Shadow)
    # ----------------------------------------------------
    body_font = get_font("Comic Sans MS", 23, bold=True)
    text_color = (52, 76, 136)         # Classic Pokemon GBA Indigo Blue
    shadow_color = (164, 180, 214)     # Soft Periwinkle Lavender Drop Shadow

    text_start_x = box_x + 36
    text_max_w = box_w - 72

    # Wrap words
    words = str(text_content).split(" ")
    lines = []
    current_line = []
    for word in words:
        if not word:
            continue
        if body_font.size(word)[0] > text_max_w:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
            chunk = ""
            for char in word:
                if body_font.size(chunk + char)[0] <= text_max_w:
                    chunk += char
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = char
            if chunk:
                current_line = [chunk]
            continue

        current_line.append(word)
        test_str = " ".join(current_line)
        if body_font.size(test_str)[0] > text_max_w:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    # Render lines with typewriter char clipping
    chars_left = len(text_content) if char_index is None else int(char_index)
    line_y = box_y + 36

    for line in lines:
        if chars_left <= 0:
            break
        visible_text = line[:chars_left]
        chars_left -= len(line) + 1

        clean_line = sanitize_text(visible_text)
        # Drop shadow (+2, +2)
        sh_surf = body_font.render(clean_line, True, shadow_color)
        screen.blit(sh_surf, (text_start_x + 2, line_y + 2))
        # Main text
        txt_surf = body_font.render(clean_line, True, text_color)
        screen.blit(txt_surf, (text_start_x, line_y))

        line_y += 36

    # ----------------------------------------------------
    # 5. RETRO BOUNCING CONTINUE INDICATOR (GBA Down Triangle)
    # ----------------------------------------------------
    is_finished = (char_index is None or char_index >= len(text_content))
    if is_finished:
        t = time.time()
        bounce_y = int(math.sin(t * 8.0) * 3.0)
        arrow_x = box_x + box_w - 38
        arrow_y = box_y + box_h - 22 + bounce_y

        # Draw red GBA chevron triangle with dark border
        tri_points = [
            (arrow_x - 8, arrow_y - 7),
            (arrow_x + 8, arrow_y - 7),
            (arrow_x, arrow_y + 5)
        ]
        pygame.draw.polygon(screen, (218, 59, 59), tri_points)
        pygame.draw.polygon(screen, (34, 34, 38), tri_points, 2)

        # Soft prompt label on bottom left
        prompt_font = get_font("Comic Sans MS", 14, bold=True)
        prompt_surf = prompt_font.render("Hold Fist / Click / Space to continue >>", True, (148, 163, 184))
        screen.blit(prompt_surf, (text_start_x, box_y + box_h - 24))
    else:
        prompt_font = get_font("Comic Sans MS", 14, bold=True)
        prompt_surf = prompt_font.render("Hold Fist / Click to advance...", True, (180, 190, 205))
        screen.blit(prompt_surf, (text_start_x, box_y + box_h - 24))


class GBADialogueBox:
    """Object-oriented wrapper around draw_gba_dialogue."""
    def __init__(self, screen, audio_manager=None):
        self.screen = screen
        self.audio_manager = audio_manager
        self.dialogue_text = ""
        self.speaker_name = ""
        self.char_index = 0.0
        self.student_info = None
        self.is_active = False

    def set_dialogue(self, text, speaker_name="", student_info=None):
        self.dialogue_text = str(text or "")
        self.speaker_name = str(speaker_name or "")
        self.student_info = student_info
        self.char_index = 0.0
        self.is_active = bool(self.dialogue_text)

    def update(self, dt=0.016):
        if self.is_active:
            self.char_index += dt * 35.0

    def draw(self, screen=None):
        if not self.is_active:
            return
        target_screen = screen or self.screen
        sw, sh = target_screen.get_size()
        draw_gba_dialogue(
            target_screen,
            sw,
            sh,
            self.speaker_name,
            self.dialogue_text,
            char_index=self.char_index,
            student_info=self.student_info
        )

