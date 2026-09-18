# main.py
import os
import sys

# Ensure current working directory is always the application's root directory.
# On Windows startup/boot, Windows launches applications with cwd = C:\Windows\System32.
if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

try:
    os.chdir(app_dir)
except Exception as e:
    print(f"[WARN] Failed to set working directory to {app_dir}: {e}")

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Reconfigure stdout and stderr to UTF-8 to support emojis and prevent crashes on Windows consoles
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Handle CLI flags before Pygame display initialization
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg in ("--autostart-enable", "--enable-autostart", "-ae"):
        from core.autostart_manager import enable_autostart
        ok, msg = enable_autostart()
        print(f"[AUTOSTART] {msg}")
        sys.exit(0 if ok else 1)
    elif arg in ("--autostart-disable", "--disable-autostart", "-ad"):
        from core.autostart_manager import disable_autostart
        ok, msg = disable_autostart()
        print(f"[AUTOSTART] {msg}")
        sys.exit(0 if ok else 1)
    elif arg in ("--autostart-status", "--status-autostart", "-as"):
        from core.autostart_manager import get_status_text, is_autostart_enabled
        enabled = is_autostart_enabled()
        print(f"[AUTOSTART] Status: {get_status_text()}")
        sys.exit(0 if enabled else 1)
    elif arg in ("--help", "-h"):
        print("Cognitive Play - Educational Games Launcher")
        print("Options:")
        print("  --enable-autostart, --autostart-enable   Register game to launch on Windows boot")
        print("  --disable-autostart, --autostart-disable Remove game from Windows boot")
        print("  --status-autostart, --autostart-status  Check current Windows boot registration")
        print("  --help, -h                              Show this help message")
        sys.exit(0)

# Initialize Pygame and font system before importing any game screens
import pygame
pygame.init()
pygame.font.init()

from core.font_manager import install_font_cache
install_font_cache()

from screens.main_menu import MainMenu


def main():
    # Get display info for fullscreen
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

    # Set up fullscreen display
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Cognitive Maze - Educational Games")

    # Set up clock for FPS
    clock = pygame.time.Clock()

    # Create the main menu
    main_menu = MainMenu(screen)

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                from db.save_system import save_student_progress
                save_student_progress(main_menu)
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                pygame.display.toggle_fullscreen()
            else:
                main_menu.handle_event(event)

        # Update
        main_menu.update()

        # Draw
        main_menu.draw()

        # Update display
        pygame.display.flip()

        # Control frame rate
        clock.tick(60)  # 60 FPS

    # Quit the game
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()