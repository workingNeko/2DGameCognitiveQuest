# core/screenshot_manager.py - High-Performance In-Game Screenshot System
import ctypes
from ctypes import wintypes
from datetime import datetime
import io
import os
import pygame


def get_screenshots_directory():
    """Returns the dedicated directory for game screenshots (Pictures/CognitiveMaze)."""
    try:
        user_pictures = os.path.join(os.path.expanduser("~"), "Pictures", "CognitiveMaze")
        os.makedirs(user_pictures, exist_ok=True)
        return user_pictures
    except Exception:
        pass
    
    fallback_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(fallback_dir, exist_ok=True)
    return fallback_dir


def copy_surface_to_windows_clipboard(surface):
    """Copies a Pygame surface directly to the Windows Clipboard as DIB (Device-Independent Bitmap).
    Allows players to immediately paste (Ctrl + V) into Discord, Docs, Messenger, Paint, etc.
    """
    if os.name != 'nt':
        return False

    try:
        bio = io.BytesIO()
        pygame.image.save(surface, bio, "BMP")
        bmp_data = bio.getvalue()
        # DIB payload starts at byte 14 (skipping the 14-byte BITMAPFILEHEADER)
        dib_data = bmp_data[14:]

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]

        GMEM_MOVEABLE = 0x0002
        CF_DIB = 8

        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib_data))
        if not h_mem:
            return False

        p_mem = kernel32.GlobalLock(h_mem)
        if not p_mem:
            return False

        ctypes.memmove(p_mem, dib_data, len(dib_data))
        kernel32.GlobalUnlock(h_mem)

        if user32.OpenClipboard(None):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_DIB, h_mem)
            user32.CloseClipboard()
            return True
        return False
    except Exception as e:
        print(f"[SCREENSHOT] Clipboard copy failed: {e}")
        return False


def capture_screenshot(surface=None):
    """Captures the active game screen, writes a timestamped PNG to Pictures/CognitiveMaze,
    and copies the frame directly to the Windows clipboard.
    Returns:
        (filepath, success)
    """
    if surface is None:
        surface = pygame.display.get_surface()

    if surface is None:
        return None, False

    try:
        target_dir = get_screenshots_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CognitiveMaze_{timestamp}.png"
        filepath = os.path.join(target_dir, filename)

        # Save to disk
        pygame.image.save(surface, filepath)

        # Copy to Windows clipboard
        copy_surface_to_windows_clipboard(surface)

        print(f"[SCREENSHOT] Saved: {filepath} & copied to clipboard")
        return filepath, True
    except Exception as e:
        print(f"[ERROR] Failed to capture screenshot: {e}")
        return None, False
