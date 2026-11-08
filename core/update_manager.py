# core/update_manager.py - Non-blocking In-App Update Manager for Cognitive Quest
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser

from .version import (
    APP_VERSION,
    GITHUB_API_LATEST_RELEASE,
    GITHUB_RELEASES_URL,
    RAW_VERSION_URL,
    compare_versions,
)


def _create_ssl_context():
    """Builds a resilient SSL context using certifi bundle, Windows cert store, or unverified fallback."""
    try:
        import ssl
    except ImportError:
        return None

    # 1. Try bundled certifi bundle if available (shipped in PyInstaller _internal/certifi/cacert.pem)
    try:
        import certifi
        ca_path = certifi.where()
        if ca_path and os.path.exists(ca_path):
            return ssl.create_default_context(cafile=ca_path)
    except Exception:
        pass

    # 2. Try default system certificates
    try:
        return ssl.create_default_context()
    except Exception:
        pass

    # 3. Fallback unverified context
    try:
        return ssl._create_unverified_context()
    except Exception:
        return None


def _urlopen_resilient(req, timeout=8.0):
    """Executes urllib.request.urlopen with SSL resilience for educational/proxy environments."""
    ctx = _create_ssl_context()
    try:
        if ctx is not None:
            return urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.URLError as e:
        err_msg = str(e).lower()
        if "certificate_verify_failed" in err_msg or "ssl" in err_msg or "certificate" in err_msg:
            try:
                import ssl
                unverified_ctx = ssl._create_unverified_context()
                return urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx)
            except Exception:
                raise e
        raise e


class UpdateState:
    IDLE = "IDLE"
    CHECKING = "CHECKING"
    UP_TO_DATE = "UP_TO_DATE"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    DOWNLOADING = "DOWNLOADING"
    READY_TO_INSTALL = "READY_TO_INSTALL"
    ERROR = "ERROR"


class UpdateManager:
    """Manages update checks and in-app streaming downloads asynchronously on a
    background daemon thread, ensuring the Pygame 60 FPS main thread never stalls
    on the primary AMD A4-6300 dual-core target hardware.
    """
    def __init__(self, local_version=None):
        self.local_version = local_version or APP_VERSION
        self.state = UpdateState.IDLE
        self.latest_version = None
        self.release_name = None
        self.release_notes = ""
        self.download_url = GITHUB_RELEASES_URL
        self.published_at = None
        self.error_message = None
        self.last_checked_time = 0.0

        # In-App streaming download metadata
        self.installer_download_url = None
        self.installer_asset_name = None
        self.installer_expected_size = 0
        self.installer_path = None
        self.download_progress = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.download_speed_bps = 0.0
        self.download_error = None
        self.auto_install = True
        self._pending_auto_install = False
        self._cancel_requested = False
        self._download_thread = None

        self._lock = threading.Lock()
        self._worker_thread = None

    def get_clean_latest_version(self):
        """Returns latest_version stripped of any leading 'v'/'V' prefix for clean UI display."""
        ver = self.latest_version
        if not ver:
            return ""
        return str(ver).strip().lstrip("vV")

    def consume_pending_auto_install(self):
        """Fast-path main-thread check: returns True once when an auto-install download completes."""
        if not self._pending_auto_install:
            return False
        with self._lock:
            if self._pending_auto_install and self.state == UpdateState.READY_TO_INSTALL:
                self._pending_auto_install = False
                return True
            return False

    def is_checking(self):
        with self._lock:
            return self.state == UpdateState.CHECKING

    def is_downloading(self):
        with self._lock:
            return self.state == UpdateState.DOWNLOADING

    def is_ready_to_install(self):
        with self._lock:
            return self.state == UpdateState.READY_TO_INSTALL

    def has_update(self):
        with self._lock:
            return self.state in (
                UpdateState.UPDATE_AVAILABLE,
                UpdateState.DOWNLOADING,
                UpdateState.READY_TO_INSTALL,
            )

    def reset(self):
        """Resets the updater to its initial idle state."""
        with self._lock:
            self.state = UpdateState.IDLE
            self.latest_version = None
            self.release_name = None
            self.release_notes = ""
            self.download_url = GITHUB_RELEASES_URL
            self.published_at = None
            self.error_message = None
            self.last_checked_time = 0.0

            self.installer_download_url = None
            self.installer_asset_name = None
            self.installer_expected_size = 0
            self.installer_path = None
            self.download_progress = 0.0
            self.downloaded_bytes = 0
            self.total_bytes = 0
            self.download_speed_bps = 0.0
            self.download_error = None
            self.auto_install = True
            self._pending_auto_install = False
            self._cancel_requested = False

    def check_for_updates(self, on_complete=None):
        """Spawns a single background thread to check for updates if not already checking."""
        with self._lock:
            if self.state in (UpdateState.CHECKING, UpdateState.DOWNLOADING):
                return False
            self.state = UpdateState.CHECKING
            self.error_message = None

        thread = threading.Thread(
            target=self._run_check_worker,
            args=(on_complete,),
            name="UpdateCheckerWorker",
            daemon=True
        )
        self._worker_thread = thread
        thread.start()
        return True

    def _run_check_worker(self, on_complete=None):
        """Background worker executing the network request with multi-strategy resilience."""
        result_state = UpdateState.ERROR
        error_msg = None
        latest_ver = None
        rel_name = None
        rel_notes = ""
        dl_url = GITHUB_RELEASES_URL
        pub_at = None
        installer_url = None
        installer_name = None
        installer_size = 0

        headers = {
            "User-Agent": f"CognitiveQuest-Client/{self.local_version}",
            "Accept": "application/vnd.github.v3+json",
        }
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        fetched_data = None

        # Tier 1: Try GitHub Releases REST API
        try:
            req = urllib.request.Request(GITHUB_API_LATEST_RELEASE, headers=headers)
            with _urlopen_resilient(req, timeout=7.0) as resp:
                if resp.status == 200:
                    raw_content = resp.read().decode("utf-8")
                    fetched_data = json.loads(raw_content)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                error_msg = "No releases published yet."
            elif e.code == 403:
                error_msg = "GitHub API rate limit reached."
        except Exception:
            error_msg = "Connection timed out or network offline."

        # Tier 2: Fallback to GitHub Web Releases Redirect (bypasses GitHub REST API 60 req/hr rate limits)
        if not fetched_data and (error_msg != "No releases published yet."):
            try:
                web_url = f"{GITHUB_RELEASES_URL}/latest"
                req_web = urllib.request.Request(web_url, headers=browser_headers)
                with _urlopen_resilient(req_web, timeout=7.0) as resp_web:
                    final_url = resp_web.geturl()
                    if "/releases/tag/" in final_url:
                        tag = final_url.split("/releases/tag/")[-1].strip("/#?")
                        if tag:
                            fetched_data = {
                                "tag_name": tag,
                                "name": f"Cognitive Maze {tag}",
                                "body": "Software update released on GitHub.",
                                "html_url": final_url,
                                "published_at": None,
                            }
                            error_msg = None
            except Exception:
                pass

        # Tier 3: Fallback to raw repository version.json if Releases API and Web redirect returned nothing
        if not fetched_data and (error_msg != "No releases published yet."):
            try:
                req_raw = urllib.request.Request(RAW_VERSION_URL, headers={"User-Agent": f"CognitiveQuest/{self.local_version}"})
                with _urlopen_resilient(req_raw, timeout=5.0) as resp_raw:
                    if resp_raw.status == 200:
                        raw_data = json.loads(resp_raw.read().decode("utf-8"))
                        fetched_data = {
                            "tag_name": raw_data.get("version"),
                            "name": raw_data.get("name", f"Version {raw_data.get('version')}"),
                            "body": raw_data.get("notes", ""),
                            "html_url": raw_data.get("download_url", GITHUB_RELEASES_URL),
                            "published_at": raw_data.get("date"),
                        }
                        error_msg = None
            except Exception:
                pass

        # Step 4: Parse and compare if data retrieved
        if fetched_data:
            latest_ver = fetched_data.get("tag_name") or fetched_data.get("version") or ""
            rel_name = fetched_data.get("name") or f"Version {latest_ver}"
            rel_notes = fetched_data.get("body") or ""
            dl_url = fetched_data.get("html_url") or GITHUB_RELEASES_URL
            pub_at = fetched_data.get("published_at")

            # Extract direct installer asset if present in GitHub release metadata
            for asset in fetched_data.get("assets", []):
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    installer_url = asset.get("browser_download_url")
                    installer_name = name
                    installer_size = asset.get("size", 0)
                    if "setup" in name.lower():
                        break

            # Fallback deterministic asset URL if assets list not included (Tier 2/3 fallback)
            if not installer_url and latest_ver:
                tag = latest_ver if latest_ver.startswith("v") else f"v{latest_ver}"
                installer_name = f"CognitiveMaze-Setup-{tag}.exe"
                installer_url = f"https://github.com/workingNeko/2DGameCognitiveQuest/releases/download/{tag}/{installer_name}"

            if latest_ver:
                cmp_res = compare_versions(self.local_version, latest_ver)
                if cmp_res == 1:
                    result_state = UpdateState.UPDATE_AVAILABLE
                else:
                    result_state = UpdateState.UP_TO_DATE
            else:
                result_state = UpdateState.UP_TO_DATE
        else:
            if not error_msg:
                error_msg = "Connection timed out or network offline."
            result_state = UpdateState.ERROR

        # Step 5: Apply results thread-safely
        with self._lock:
            self.state = result_state
            self.latest_version = latest_ver
            self.release_name = rel_name
            self.release_notes = rel_notes
            self.download_url = dl_url
            self.published_at = pub_at
            self.error_message = error_msg
            self.last_checked_time = time.time()
            self.installer_download_url = installer_url
            self.installer_asset_name = installer_name
            self.installer_expected_size = installer_size

        if on_complete and callable(on_complete):
            try:
                on_complete(self)
            except Exception:
                pass

    @staticmethod
    def _is_valid_installer_file(file_path, expected_size=0):
        """Verifies a downloaded installer exists, matches expected byte length,
        and is not an HTML captive-portal or error document.
        """
        if not file_path or not os.path.exists(file_path):
            return False
        try:
            size = os.path.getsize(file_path)
            if size <= 0:
                return False
            if expected_size and expected_size > 0 and size != expected_size:
                return False
            with open(file_path, "rb") as f:
                head = f.read(64).lstrip().lower()
            if head.startswith((b"<!doctype", b"<html", b"<?xml")):
                return False
            return True
        except Exception:
            return False

    def start_download(self, on_progress=None, on_complete=None, auto_install=True):
        """Starts asynchronous in-app download of the update installer on a daemon thread.
        When auto_install=True (default), automatically signals the main thread to install
        and restart the game silently once 100% downloaded and verified.
        """
        with self._lock:
            if self.state == UpdateState.DOWNLOADING:
                return False
            if not self.installer_download_url and not self.latest_version:
                self.error_message = "No update asset available for download."
                self.state = UpdateState.ERROR
                return False

            if not self.installer_download_url and self.latest_version:
                clean_ver = str(self.latest_version).strip().lstrip("vV")
                tag = f"v{clean_ver}"
                self.installer_asset_name = f"CognitiveMaze-Setup-{tag}.exe"
                self.installer_download_url = (
                    f"https://github.com/workingNeko/2DGameCognitiveQuest/releases/download/{tag}/{self.installer_asset_name}"
                )

            self.auto_install = bool(auto_install)
            self._pending_auto_install = False

            updates_dir = os.path.join(tempfile.gettempdir(), "CognitiveMazeUpdates")
            try:
                os.makedirs(updates_dir, exist_ok=True)
            except Exception:
                updates_dir = tempfile.gettempdir()

            clean_ver = self.get_clean_latest_version() or "latest"
            fname = self.installer_asset_name or f"CognitiveMaze-Setup-v{clean_ver}.exe"
            target_path = os.path.join(updates_dir, fname)

            # Fast-path: if verified installer was already completely downloaded previously
            if self._is_valid_installer_file(target_path, self.installer_expected_size):
                self.installer_path = target_path
                self.download_progress = 1.0
                self.downloaded_bytes = os.path.getsize(target_path)
                self.total_bytes = self.downloaded_bytes
                self.state = UpdateState.READY_TO_INSTALL
                self._pending_auto_install = self.auto_install
                if on_complete and callable(on_complete):
                    try:
                        on_complete(self)
                    except Exception:
                        pass
                return True

            self.state = UpdateState.DOWNLOADING
            self.download_progress = 0.0
            self.downloaded_bytes = 0
            self.total_bytes = self.installer_expected_size
            self.download_speed_bps = 0.0
            self.download_error = None
            self._cancel_requested = False

        tmp_path = target_path + ".tmp"
        thread = threading.Thread(
            target=self._run_download_worker,
            args=(target_path, tmp_path, on_progress, on_complete),
            name="UpdateDownloadWorker",
            daemon=True
        )
        self._download_thread = thread
        thread.start()
        return True

    def _run_download_worker(self, target_path, tmp_path, on_progress=None, on_complete=None):
        """Streaming network I/O worker with HTTP Range resume, integrity checks,
        and 2ms per-chunk CPU yields to preserve 60 FPS on AMD A4-6300 APU.
        """
        CHUNK_SIZE = 64 * 1024  # 64 KB chunk size
        MAX_ATTEMPTS = 3
        downloaded = 0
        total = self.total_bytes if self.total_bytes > 0 else self.installer_expected_size
        last_speed_time = time.time()
        last_speed_bytes = 0
        speed_bps = 0.0

        try:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

            last_err = None
            for attempt in range(MAX_ATTEMPTS):
                if self._cancel_requested:
                    break

                try:
                    req_headers = {
                        "User-Agent": f"CognitiveQuest-Client/{self.local_version}",
                        "Accept": "application/octet-stream,application/vnd.github.v3.raw,*/*",
                    }
                    resume_offset = downloaded if (downloaded > 0 and os.path.exists(tmp_path)) else 0
                    if resume_offset > 0:
                        req_headers["Range"] = f"bytes={resume_offset}-"

                    req = urllib.request.Request(self.installer_download_url, headers=req_headers)
                    with _urlopen_resilient(req, timeout=20.0) as resp:
                        raw_status = getattr(resp, "status", 200)
                        status_code = raw_status if isinstance(raw_status, int) else 200

                        if resume_offset > 0 and status_code == 206:
                            file_mode = "ab"
                            downloaded = resume_offset
                        else:
                            file_mode = "wb"
                            downloaded = 0
                            last_speed_bytes = 0
                            content_len_header = resp.headers.get("Content-Length") if hasattr(resp, "headers") and resp.headers else None
                            if isinstance(content_len_header, str) and content_len_header.isdigit():
                                total = int(content_len_header)
                                with self._lock:
                                    self.total_bytes = total

                        with open(tmp_path, file_mode) as f:
                            while True:
                                if self._cancel_requested:
                                    break

                                chunk = resp.read(CHUNK_SIZE)
                                if not chunk:
                                    break

                                f.write(chunk)
                                downloaded += len(chunk)

                                now = time.time()
                                dt = now - last_speed_time
                                if dt >= 0.4:
                                    speed_bps = max(0.0, (downloaded - last_speed_bytes) / dt)
                                    last_speed_time = now
                                    last_speed_bytes = downloaded

                                prog = (downloaded / total) if total > 0 else 0.0
                                with self._lock:
                                    self.downloaded_bytes = downloaded
                                    self.download_progress = min(1.0, max(0.0, prog))
                                    self.download_speed_bps = speed_bps

                                if on_progress and callable(on_progress):
                                    try:
                                        on_progress(self.download_progress, downloaded, total)
                                    except Exception:
                                        pass

                                # Yield CPU slice to ensure Pygame main thread and MediaPipe thread stay at 60 FPS
                                time.sleep(0.002)

                    if self._cancel_requested:
                        break

                    if total > 0 and downloaded < total:
                        raise IOError(f"Incomplete download ({downloaded} of {total} bytes received).")

                    last_err = None
                    break
                except Exception as attempt_err:
                    last_err = attempt_err
                    if self._cancel_requested:
                        break
                    if attempt + 1 < MAX_ATTEMPTS:
                        time.sleep(1.0 * (attempt + 1))
                    else:
                        raise last_err

            if self._cancel_requested:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                with self._lock:
                    self.state = UpdateState.UPDATE_AVAILABLE
                    self.download_progress = 0.0
                    self.downloaded_bytes = 0
                    self._pending_auto_install = False
                return

            if not self._is_valid_installer_file(tmp_path, expected_size=total if total > 0 else 0):
                raise IOError("Downloaded installer failed integrity check or is incomplete.")

            # Atomically replace tmp file with final installer path
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except Exception:
                    pass
            os.replace(tmp_path, target_path)

            with self._lock:
                self.installer_path = target_path
                self.download_progress = 1.0
                self.downloaded_bytes = os.path.getsize(target_path)
                self.total_bytes = self.downloaded_bytes
                self.state = UpdateState.READY_TO_INSTALL
                self._pending_auto_install = bool(self.auto_install)

            if on_complete and callable(on_complete):
                try:
                    on_complete(self)
                except Exception:
                    pass

        except Exception as e:
            if self._cancel_requested:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                with self._lock:
                    self.state = UpdateState.UPDATE_AVAILABLE
                    self.download_progress = 0.0
                    self.downloaded_bytes = 0
                    self._pending_auto_install = False
                return

            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            with self._lock:
                self.state = UpdateState.ERROR
                self.error_message = f"Download failed: {str(e)}"
                self.download_error = str(e)
                self._pending_auto_install = False

    def cancel_download(self):
        """Requests cancellation of active background download."""
        with self._lock:
            self._pending_auto_install = False
            if self.state == UpdateState.DOWNLOADING:
                self._cancel_requested = True

    @staticmethod
    def _write_windows_auto_update_script(installer_path, current_pid, app_dir="", exe_path="", needs_elevation=False):
        """Creates a self-deleting Windows helper script that waits for the current game PID
        to exit completely, runs Inno Setup silently into the exact installation directory
        without manual wizard prompts, relaunches CognitiveMaze.exe automatically, and cleans up.
        """
        script_dir = os.path.dirname(os.path.abspath(installer_path)) or tempfile.gettempdir()
        script_path = os.path.join(script_dir, "apply_cognitive_update.cmd")

        if needs_elevation and app_dir:
            ps_args = f"'/SILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS','/DIR=\"{app_dir}\"'"
            install_block = (
                f'powershell -NoProfile -WindowStyle Hidden -Command '
                f'"$p = Start-Process -FilePath \'{installer_path}\' -ArgumentList {ps_args} -Verb RunAs -Wait -PassThru; exit $p.ExitCode"\r\n'
            )
        elif app_dir:
            install_block = (
                f'"{installer_path}" /SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS /DIR="%APP_DIR%"\r\n'
            )
        else:
            install_block = (
                f'"{installer_path}" /SILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS\r\n'
            )

        script_content = (
            "@echo off\r\n"
            "setlocal\r\n"
            f'set "OLD_PID={int(current_pid)}"\r\n'
            f'set "INSTALLER={os.path.abspath(installer_path)}"\r\n'
            f'set "APP_DIR={app_dir}"\r\n'
            f'set "APP_EXE={exe_path}"\r\n'
            "set /a TRIES=0\r\n"
            ":wait_exit\r\n"
            'tasklist /FI "PID eq %OLD_PID%" /NH 2>NUL | findstr /R /C:"\\<%OLD_PID%\\>" >NUL\r\n'
            'if "%ERRORLEVEL%"=="0" (\r\n'
            "    set /a TRIES+=1\r\n"
            "    if %TRIES% LSS 20 (\r\n"
            "        ping -n 2 127.0.0.1 >NUL\r\n"
            "        goto wait_exit\r\n"
            "    )\r\n"
            ")\r\n"
            + install_block +
            'set "INST_ERR=%ERRORLEVEL%"\r\n'
            'if not "%APP_EXE%"=="" (\r\n'
            '    if exist "%APP_EXE%" (\r\n'
            '        start "" /D "%APP_DIR%" "%APP_EXE%"\r\n'
            "    )\r\n"
            ") else (\r\n"
            '    if exist "%LOCALAPPDATA%\\Programs\\Cognitive Maze\\CognitiveMaze.exe" (\r\n'
            '        start "" /D "%LOCALAPPDATA%\\Programs\\Cognitive Maze" "%LOCALAPPDATA%\\Programs\\Cognitive Maze\\CognitiveMaze.exe"\r\n'
            "    )\r\n"
            ")\r\n"
            'if "%INST_ERR%"=="0" (\r\n'
            '    del /F /Q "%INSTALLER%" >NUL 2>&1\r\n'
            ")\r\n"
            '(goto) 2>NUL & del /F /Q "%~f0" >NUL 2>&1\r\n'
        )
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_path

    def apply_update(self, on_before_exit=None):
        """Silently applies the downloaded update into the current installation directory,
        gracefully closes the running game to unlock all files, and automatically relaunches
        the updated game with zero manual installer clicks.
        """
        target = self.installer_path
        if not target or not os.path.exists(target):
            print(f"[ERROR] Installer file does not exist: {target}")
            return False

        with self._lock:
            self._pending_auto_install = False

        if on_before_exit and callable(on_before_exit):
            try:
                on_before_exit()
            except Exception as cb_err:
                print(f"[WARN] Pre-update shutdown hook warning: {cb_err}")

        try:
            from db.save_system import flush_pending_async_saves
            flush_pending_async_saves()
        except Exception:
            pass

        try:
            import pygame

            print(f"[UPDATER] Launching automatic in-app update from: {target}")
            if os.name == "nt":
                is_frozen = bool(getattr(sys, "frozen", False))
                exe_path = os.path.abspath(sys.executable) if is_frozen else ""
                app_dir = os.path.dirname(exe_path) if is_frozen else ""
                needs_elevation = False
                if app_dir:
                    probe_file = os.path.join(app_dir, f".upd_write_probe_{os.getpid()}")
                    try:
                        with open(probe_file, "w", encoding="utf-8") as pf:
                            pf.write("ok")
                        os.remove(probe_file)
                    except Exception:
                        needs_elevation = True

                script_path = self._write_windows_auto_update_script(
                    installer_path=target,
                    current_pid=os.getpid(),
                    app_dir=app_dir,
                    exe_path=exe_path,
                    needs_elevation=needs_elevation,
                )
                creation_flags = (
                    getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                    | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
                )
                subprocess.Popen(
                    ["cmd.exe", "/d", "/c", script_path],
                    creationflags=creation_flags,
                    close_fds=True,
                )
            else:
                subprocess.Popen([target])

            # Terminate Pygame & Python cleanly to unlock files immediately
            try:
                pygame.quit()
            except Exception:
                pass
            sys.exit(0)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to launch installer: {e}")
            with self._lock:
                self.state = UpdateState.ERROR
                self.error_message = f"Failed to start installer: {e}"
            return False

    def get_progress_pct(self):
        with self._lock:
            return int(self.download_progress * 100)

    def get_download_stats(self):
        with self._lock:
            mb_done = self.downloaded_bytes / (1024 * 1024)
            mb_total = self.total_bytes / (1024 * 1024) if self.total_bytes > 0 else 0.0
            pct = int(self.download_progress * 100)
            
            speed = self.download_speed_bps
            if speed >= 1024 * 1024:
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
            elif speed >= 1024:
                speed_str = f"{speed / 1024:.0f} KB/s"
            else:
                speed_str = f"{speed:.0f} B/s"

            return {
                "progress": self.download_progress,
                "pct": pct,
                "mb_done": mb_done,
                "mb_total": mb_total,
                "speed_str": speed_str,
                "error": self.download_error,
            }

    def open_download_page(self):
        """Safely opens the release / download URL in the user's default browser."""
        target_url = self.download_url or GITHUB_RELEASES_URL
        try:
            webbrowser.open(target_url)
            return True
        except Exception as e:
            print(f"[WARN] Failed to open browser for updates: {e}")
            return False
