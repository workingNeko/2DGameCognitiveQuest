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
        self._cancel_requested = False
        self._download_thread = None

        self._lock = threading.Lock()
        self._worker_thread = None

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
                                "body": "Official update released on GitHub.",
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

    def start_download(self, on_progress=None, on_complete=None):
        """Starts asynchronous in-app download of the update installer on a daemon thread."""
        with self._lock:
            if self.state == UpdateState.DOWNLOADING:
                return False
            if not self.installer_download_url and not self.latest_version:
                self.error_message = "No update asset available for download."
                self.state = UpdateState.ERROR
                return False

            temp_dir = tempfile.gettempdir()
            fname = self.installer_asset_name or f"CognitiveMaze-Setup-{self.latest_version}.exe"
            target_path = os.path.join(temp_dir, fname)

            # Fast-path: if installer was already completely downloaded previously
            if (
                os.path.exists(target_path)
                and os.path.getsize(target_path) > 0
                and (self.installer_expected_size <= 0 or os.path.getsize(target_path) == self.installer_expected_size)
            ):
                self.installer_path = target_path
                self.download_progress = 1.0
                self.downloaded_bytes = os.path.getsize(target_path)
                self.total_bytes = self.downloaded_bytes
                self.state = UpdateState.READY_TO_INSTALL
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
        """Streaming network I/O worker yielding CPU time to preserve 60 FPS on AMD A4-6300."""
        CHUNK_SIZE = 64 * 1024  # 64 KB chunk size
        downloaded = 0
        total = self.total_bytes
        last_speed_time = time.time()
        last_speed_bytes = 0
        speed_bps = 0.0

        try:
            req = urllib.request.Request(
                self.installer_download_url,
                headers={
                    "User-Agent": f"CognitiveQuest-Client/{self.local_version}",
                    "Accept": "application/octet-stream,application/vnd.github.v3.raw,*/*"
                }
            )
            with _urlopen_resilient(req, timeout=15.0) as resp:
                content_len_header = resp.headers.get("Content-Length")
                if content_len_header and content_len_header.isdigit():
                    total = int(content_len_header)
                    with self._lock:
                        self.total_bytes = total

                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

                with open(tmp_path, "wb") as f:
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
                            speed_bps = (downloaded - last_speed_bytes) / dt
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

                        # Yield CPU to ensure Pygame main thread and MediaPipe thread never stutter
                        time.sleep(0.001)

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
                return

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                raise IOError("Downloaded file is empty or missing.")

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

    def cancel_download(self):
        """Requests cancellation of active background download."""
        with self._lock:
            if self.state == UpdateState.DOWNLOADING:
                self._cancel_requested = True

    def apply_update(self):
        """Launches the downloaded installer and terminates the current game process
        so Windows can cleanly overwrite game files without file lock conflicts.
        """
        target = self.installer_path
        if not target or not os.path.exists(target):
            print(f"[ERROR] Installer file does not exist: {target}")
            return False

        try:
            import pygame

            print(f"[UPDATER] Spawning installer: {target}")
            if os.name == 'nt':
                # Launch detached installer so it runs independently of this python process
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen([target], creationflags=DETACHED_PROCESS, close_fds=True)
            else:
                subprocess.Popen([target])

            # Terminate Pygame & python cleanly to unlock files immediately
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
