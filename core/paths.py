# core/paths.py - Centralized path resolution for dev and frozen builds
import os
import sys

_BASE_DIR = None


def get_base_dir():
    """
    Returns the root application directory containing 'assets', 'db', and 'datasets'.
    Works universally across development environments (python main.py),
    PyInstaller frozen builds, and installed desktop deployments.
    """
    global _BASE_DIR
    if _BASE_DIR is not None and os.path.isdir(os.path.join(_BASE_DIR, "assets")):
        return _BASE_DIR

    # 1. If running as a frozen PyInstaller binary (CognitiveMaze.exe)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        if os.path.isdir(os.path.join(exe_dir, "assets")):
            _BASE_DIR = exe_dir
            return _BASE_DIR

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.isdir(os.path.join(meipass, "assets")):
            _BASE_DIR = meipass
            return _BASE_DIR

        internal_dir = os.path.join(exe_dir, "_internal")
        if os.path.isdir(os.path.join(internal_dir, "assets")):
            _BASE_DIR = internal_dir
            return _BASE_DIR

        _BASE_DIR = exe_dir
        return _BASE_DIR

    # 2. Running from source (development)
    # Check parent of 'core' directory
    core_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(core_dir)
    if os.path.isdir(os.path.join(project_root, "assets")):
        _BASE_DIR = project_root
        return _BASE_DIR

    # Check current working directory
    cwd = os.getcwd()
    if os.path.isdir(os.path.join(cwd, "assets")):
        _BASE_DIR = cwd
        return _BASE_DIR

    _BASE_DIR = project_root
    return _BASE_DIR


def get_asset_path(*subpaths):
    """Returns absolute path to a file or folder inside 'assets'."""
    return os.path.join(get_base_dir(), "assets", *subpaths)


def get_db_path(*subpaths):
    """Returns absolute path to a file or folder inside 'db'."""
    return os.path.join(get_base_dir(), "db", *subpaths)


def get_dataset_path(*subpaths):
    """Returns absolute path to a file or folder inside 'datasets'."""
    return os.path.join(get_base_dir(), "datasets", *subpaths)


def resolve_path(path):
    """
    Safely resolves a path (relative or absolute) against base_dir.
    Checks direct path, relative to get_base_dir(), and relative to assets/.
    """
    if not path:
        return path
    if os.path.exists(path):
        return os.path.abspath(path)

    base = get_base_dir()
    cand = os.path.join(base, path)
    if os.path.exists(cand):
        return os.path.abspath(cand)

    cand_asset = os.path.join(base, "assets", path)
    if os.path.exists(cand_asset):
        return os.path.abspath(cand_asset)

    return os.path.abspath(cand)

