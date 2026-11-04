# main.py
import os
import sys
import types

# Lightweight matplotlib stub so mediapipe.tasks.python.vision.drawing_utils
# never drags ~40 MB of matplotlib.pyplot into RAM or frozen builds on AMD A4-6300.
if "matplotlib" not in sys.modules:
    _mpl_stub = types.ModuleType("matplotlib")
    _mpl_stub.__path__ = []
    _plt_stub = types.ModuleType("matplotlib.pyplot")
    _mpl_stub.pyplot = _plt_stub
    sys.modules["matplotlib"] = _mpl_stub
    sys.modules["matplotlib.pyplot"] = _plt_stub

# Ensure matplotlib uses headless Agg backend to prevent Tk/GUI backend dependencies
os.environ["MPLBACKEND"] = "Agg"

# Low-overhead CPU thread scheduling optimized for AMD A4-6300 (Dual Core / Dual Thread):
# Prevents libraries (OpenMP, BLAS, NumPy, OpenCV, XNNPACK) from spawning competing thread pools
# that starve the Pygame main game loop and cause micro-stutters.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TF_NUM_INTEROP_THREADS"] = "1"
os.environ["TF_NUM_INTRAOP_THREADS"] = "1"
os.environ["SDL_RENDER_SCALE_QUALITY"] = "0"

try:
    import cv2
    cv2.setNumThreads(1)
    if hasattr(cv2, 'ocl') and hasattr(cv2.ocl, 'setUseOpenCL'):
        cv2.ocl.setUseOpenCL(False)
except Exception:
    pass

# Ensure current working directory is always the application's root directory.
# On Windows startup/boot, Windows launches applications with cwd = C:\Windows\System32.
if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(os.path.abspath(sys.executable))
    meipass_dir = getattr(sys, "_MEIPASS", os.path.join(app_dir, "_internal"))
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
    meipass_dir = app_dir

try:
    os.chdir(app_dir)
except Exception as e:
    print(f"[WARN] Failed to set working directory to {app_dir}: {e}")

# In PyInstaller frozen builds, ensure runtime assets and data directories exist in working dir
if getattr(sys, "frozen", False):
    import shutil
    for folder_name in ("assets", "datasets", "db"):
        target_folder = os.path.join(app_dir, folder_name)
        internal_folder = os.path.join(meipass_dir, folder_name)
        if not os.path.exists(target_folder) and os.path.exists(internal_folder):
            try:
                shutil.copytree(internal_folder, target_folder, dirs_exist_ok=True)
                print(f"[AUTO-RESTORE] Restored {folder_name} from _internal bundle.")
            except Exception as e:
                print(f"[WARN] Failed to auto-restore {folder_name}: {e}")

    layout_file = os.path.join(app_dir, "layout_config.json")
    internal_layout = os.path.join(meipass_dir, "layout_config.json")
    if not os.path.exists(layout_file) and os.path.exists(internal_layout):
        try:
            shutil.copy2(internal_layout, layout_file)
        except Exception:
            pass

    # Ensure writable user save and cache directories exist
    os.makedirs(os.path.join(app_dir, "db", "saves"), exist_ok=True)
    os.makedirs(os.path.join(app_dir, "db", "cache"), exist_ok=True)

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Safe stdout/stderr redirection for GUI windowed executables
class NullWriter:
    def write(self, s): pass
    def flush(self): pass
    def reconfigure(self, **kwargs): pass

if sys.stdout is None:
    sys.stdout = NullWriter()
else:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = NullWriter()
else:
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
try:
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception:
    pass
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

    # Set up fullscreen display with hardware double-buffering
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN | pygame.DOUBLEBUF)
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