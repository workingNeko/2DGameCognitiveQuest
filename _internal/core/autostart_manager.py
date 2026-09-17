"""
core/autostart_manager.py - Windows Boot Autorun Integration for Cognitive Play

Provides robust management of Windows startup launch configuration via:
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run

Designed to seamlessly handle:
1. Standalone frozen executable (.exe) built with PyInstaller
2. Local development launchers (run_game.bat or pythonw.exe)
3. Non-Windows environments (graceful fallback)
"""

import os
import sys
import platform

REG_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "CognitivePlay"


def is_windows() -> bool:
    """Returns True if running on a Windows operating system."""
    return platform.system().lower() == "windows"


def is_autostart_supported() -> bool:
    """Returns True if Windows registry access (winreg) is available."""
    if not is_windows():
        return False
    try:
        import winreg  # noqa: F401
        return True
    except ImportError:
        return False


def get_application_directory() -> str:
    """Returns the absolute root directory of the game."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # Fallback to current file's grandparent (workspace root)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_executable_command() -> str:
    """
    Determines the appropriate command to execute on Windows boot.
    
    - If running as a compiled standalone .exe (sys.frozen), returns the quoted path to the .exe.
    - If running in development mode, looks for run_game.bat or an existing dist/.exe,
      or falls back to pythonw.exe with main.py.
    """
    app_dir = get_application_directory()

    # 1. Packaged standalone executable (PyInstaller / cx_Freeze / Nuitka)
    if getattr(sys, "frozen", False):
        exe_path = os.path.abspath(sys.executable)
        return f'"{exe_path}"'

    # 2. Check if a compiled dist executable already exists in the project
    dist_exe = os.path.join(app_dir, "dist", "CognitivePlay", "CognitivePlay.exe")
    if os.path.exists(dist_exe):
        return f'"{os.path.abspath(dist_exe)}"'

    # 3. Check for run_game.bat in workspace
    bat_path = os.path.join(app_dir, "run_game.bat")
    if os.path.exists(bat_path):
        return f'"{os.path.abspath(bat_path)}"'

    # 4. Fallback: pythonw.exe or python.exe executing main.py
    main_py = os.path.join(app_dir, "main.py")
    py_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(py_dir, "pythonw.exe")
    python_exec = pythonw if os.path.exists(pythonw) else sys.executable
    return f'"{os.path.abspath(python_exec)}" "{os.path.abspath(main_py)}"'


def is_autostart_enabled(app_name: str = APP_NAME) -> bool:
    """
    Checks whether the application is registered in Windows Startup.
    
    Returns:
        bool: True if entry exists and points to a command, False otherwise.
    """
    if not is_autostart_supported():
        return False

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, app_name)
            return bool(value and len(value.strip()) > 0)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[WARN] AutostartManager: Failed to query registry: {e}")
        return False


def enable_autostart(app_name: str = APP_NAME, custom_command: str = None) -> tuple[bool, str]:
    """
    Registers the application to launch automatically when Windows boots.
    
    Args:
        app_name (str): The registry value name (default: 'CognitivePlay').
        custom_command (str, optional): Custom execution string. If None, auto-detected.
        
    Returns:
        tuple[bool, str]: (Success boolean, Status message)
    """
    if not is_autostart_supported():
        return False, "Autostart is only supported on Windows systems."

    command = custom_command or get_executable_command()
    if not command:
        return False, "Could not resolve valid executable path for autostart."

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
        print(f"[AUTOSTART] Registered '{app_name}' to autorun: {command}")
        return True, f"Successfully enabled Windows startup autorun."
    except Exception as e:
        err_msg = f"Failed to register autostart in Windows registry: {e}"
        print(f"[ERROR] AutostartManager: {err_msg}")
        return False, err_msg


def disable_autostart(app_name: str = APP_NAME) -> tuple[bool, str]:
    """
    Removes the application from Windows Startup.
    
    Args:
        app_name (str): The registry value name (default: 'CognitivePlay').
        
    Returns:
        tuple[bool, str]: (Success boolean, Status message)
    """
    if not is_autostart_supported():
        return False, "Autostart is only supported on Windows systems."

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_SUBKEY, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ
        ) as key:
            # First check if the key exists before deleting
            try:
                winreg.QueryValueEx(key, app_name)
            except FileNotFoundError:
                return True, "Autostart is already disabled."

            winreg.DeleteValue(key, app_name)
        print(f"[AUTOSTART] Removed '{app_name}' from Windows Startup.")
        return True, "Successfully disabled Windows startup autorun."
    except FileNotFoundError:
        return True, "Autostart is already disabled."
    except Exception as e:
        err_msg = f"Failed to remove autostart entry: {e}"
        print(f"[ERROR] AutostartManager: {err_msg}")
        return False, err_msg


def toggle_autostart(app_name: str = APP_NAME) -> tuple[bool, str]:
    """
    Toggles the Windows startup state.
    
    Returns:
        tuple[bool, str]: (New enabled state, Status message)
    """
    current_state = is_autostart_enabled(app_name)
    if current_state:
        success, msg = disable_autostart(app_name)
        new_state = not success  # if disabled successfully, new_state is False
        return new_state, msg
    else:
        success, msg = enable_autostart(app_name)
        return success, msg


def get_status_text(app_name: str = APP_NAME) -> str:
    """Returns a short human-readable description of the current autostart status."""
    if not is_autostart_supported():
        return "Not supported on this OS"
    enabled = is_autostart_enabled(app_name)
    return "Enabled (Launches on boot)" if enabled else "Disabled (Manual launch only)"
