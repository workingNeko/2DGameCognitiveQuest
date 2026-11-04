# core/version.py - Canonical Version Definition and SemVer Utilities
import re

APP_VERSION = "1.0.0"
APP_NAME = "Cognitive Quest: DepEd Grade 2 Mathematics"
GITHUB_REPO = "workingNeko/2DGameCognitiveQuest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
GITHUB_API_LATEST_RELEASE = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RAW_VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/master/version.json"


def parse_version(v_str):
    """Parses a version string into a tuple of integers for reliable semantic comparison.
    Examples:
        '1.0.0'   -> (1, 0, 0)
        'v1.2.3'  -> (1, 2, 3)
        '2.1-beta'-> (2, 1, 0)
    """
    if not v_str:
        return (0, 0, 0)
    
    clean_str = str(v_str).strip().lower()
    if clean_str.startswith('v'):
        clean_str = clean_str[1:].strip()
        
    parts = re.findall(r'\d+', clean_str)
    if not parts:
        return (0, 0, 0)
        
    parsed = tuple(int(p) for p in parts[:3])
    # Pad with zeros if fewer than 3 components (e.g., '1.2' -> (1, 2, 0))
    while len(parsed) < 3:
        parsed += (0,)
    return parsed


def compare_versions(local_ver, remote_ver):
    """Compares local_ver against remote_ver.
    Returns:
         1 if remote_ver > local_ver (Newer version available)
         0 if remote_ver == local_ver (Up to date)
        -1 if remote_ver < local_ver (Local version is newer / dev build)
    """
    local_tuple = parse_version(local_ver)
    remote_tuple = parse_version(remote_ver)
    
    if remote_tuple > local_tuple:
        return 1
    elif remote_tuple == local_tuple:
        return 0
    else:
        return -1

