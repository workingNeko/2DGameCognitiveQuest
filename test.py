import pygame
import math
import os

# ============================================================
# INITIALIZE
# ============================================================
pygame.init()

WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spawn Plains Area Title")
clock = pygame.time.Clock()

# ============================================================
# FONT
# ============================================================
FONT_PATH = "assets/fonts/Pixelfont.otf"
FONT_SIZE = 72

try:
    font = pygame.font.Font(FONT_PATH, FONT_SIZE)
except Exception:
    print(f"Could not load {FONT_PATH}")
    print("Using default font instead.")
    font = pygame.font.SysFont("Consolas", FONT_SIZE, bold=True)

TEXT = "Spawn Plains"

# ============================================================
# COLORS
# ============================================================
BACKGROUND = (38, 46, 58)

TEXT_COLOR = (225, 255, 205)
OUTLINE_COLOR = (24, 64, 24)
GLOW_COLOR = (130, 255, 130)

# ============================================================
# TIMING
# ============================================================
CYCLE_TIME = 5.0          # Repeat every 5 seconds
SLIDE_TIME = 0.35         # Slide from top
WAVE_TIME = 1.35          # Single wave duration
FADE_START = 2.0          # Fade begins
FADE_DURATION = 1.0

BASE_Y = 90
LETTER_SPACING = 12

# ============================================================
# PRE-RENDER LETTERS
# ============================================================
letters = []

for ch in TEXT:

    glow = font.render(ch, False, GLOW_COLOR)
    outline = font.render(ch, False, OUTLINE_COLOR)
    main = font.render(ch, False, TEXT_COLOR)

    letters.append({
        "glow": glow,
        "outline": outline,
        "main": main,
        "width": main.get_width()
    })

total_width = sum(l["width"] for l in letters) + LETTER_SPACING * (len(TEXT) - 1)

# ============================================================
# MAIN LOOP
# ============================================================
start_ticks = pygame.time.get_ticks()

running = True

while running:

    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BACKGROUND)

    elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
    timer = elapsed % CYCLE_TIME

    # --------------------------------------------------------
    # Alpha
    # --------------------------------------------------------
    alpha = 255

    if timer >= FADE_START:
        fade = (timer - FADE_START) / FADE_DURATION
        fade = max(0, min(fade, 1))
        alpha = int(255 * (1 - fade))

    # --------------------------------------------------------
    # Slide animation
    # --------------------------------------------------------
    if timer < SLIDE_TIME:
        t = timer / SLIDE_TIME
        ease = 1 - (1 - t) ** 3
        y = BASE_Y - (1 - ease) * 30
    else:
        y = BASE_Y

    # --------------------------------------------------------
    # Draw letters
    # --------------------------------------------------------
    x = WIDTH // 2 - total_width // 2

    for i, data in enumerate(letters):

        phase = timer * 8 - i * 0.55

        offset = 0

        # Single traveling wave
        if -math.pi <= phase <= math.pi:
            offset = math.sin(phase) * 12

        glow = data["glow"].copy()
        outline = data["outline"].copy()
        main = data["main"].copy()

        glow.set_alpha(alpha // 5)
        outline.set_alpha(alpha)
        main.set_alpha(alpha)

        # Glow
        for gx in (-5, 0, 5):
            for gy in (-5, 0, 5):
                screen.blit(glow, (x + gx, y + gy + offset))

        # Outline
        for ox in (-2, -1, 1, 2):
            for oy in (-2, -1, 1, 2):
                screen.blit(outline, (x + ox, y + oy + offset))

        # Main text
        screen.blit(main, (x, y + offset))

        x += data["width"] + LETTER_SPACING

    pygame.display.flip()

pygame.quit()