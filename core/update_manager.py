# core/update_manager.py - Non-blocking Update Manager for Cognitive Quest
import json
import os
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


class UpdateState:
    IDLE = "IDLE"
    CHECKING = "CHECKING"
    UP_TO_DATE = "UP_TO_DATE"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    ERROR = "ERROR"


class UpdateManager:
    """Manages version check requests asynchronously on a background daemon thread,
    ensuring the Pygame 60 FPS main thread never stalls on low-spec target hardware.
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
        self._lock = threading.Lock()
        self._worker_thread = None

    def is_checking(self):
        with self._lock:
            return self.state == UpdateState.CHECKING

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

    def has_update(self):
        with self._lock:
            return self.state == UpdateState.UPDATE_AVAILABLE

    def check_for_updates(self, on_complete=None):
        """Spawns a single background thread to check for updates if not already checking."""
        with self._lock:
            if self.state == UpdateState.CHECKING:
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
        """Background worker executing the network request with a 4-second timeout."""
        result_state = UpdateState.ERROR
        error_msg = None
        latest_ver = None
        rel_name = None
        rel_notes = ""
        dl_url = GITHUB_RELEASES_URL
        pub_at = None

        headers = {
            "User-Agent": f"CognitiveQuest-Client/{self.local_version}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Step 1: Try GitHub Releases API
        fetched_data = None
        try:
            req = urllib.request.Request(GITHUB_API_LATEST_RELEASE, headers=headers)
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    raw_content = resp.read().decode("utf-8")
                    fetched_data = json.loads(raw_content)
        except urllib.error.HTTPError as e:
            # 404 means no release published yet; 403 can mean GitHub rate limit
            if e.code == 404:
                error_msg = "No releases published yet."
            elif e.code == 403:
                error_msg = "GitHub API rate limit reached."
        except Exception as e:
            error_msg = "Connection timed out or network offline."

        # Step 2: Fallback to raw repository version.json if Releases API returned nothing
        if not fetched_data:
            try:
                req_raw = urllib.request.Request(RAW_VERSION_URL, headers={"User-Agent": f"CognitiveQuest/{self.local_version}"})
                with urllib.request.urlopen(req_raw, timeout=3.0) as resp_raw:
                    if resp_raw.status == 200:
                        raw_data = json.loads(resp_raw.read().decode("utf-8"))
                        fetched_data = {
                            "tag_name": raw_data.get("version"),
                            "name": raw_data.get("name", f"Version {raw_data.get('version')}"),
                            "body": raw_data.get("notes", ""),
                            "html_url": raw_data.get("download_url", GITHUB_RELEASES_URL),
                            "published_at": raw_data.get("date"),
                        }
            except Exception:
                pass

        # Step 3: Parse and compare if data retrieved
        if fetched_data:
            latest_ver = fetched_data.get("tag_name") or fetched_data.get("version") or ""
            rel_name = fetched_data.get("name") or f"Version {latest_ver}"
            rel_notes = fetched_data.get("body") or ""
            dl_url = fetched_data.get("html_url") or GITHUB_RELEASES_URL
            pub_at = fetched_data.get("published_at")

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
                error_msg = "Unable to connect to update server."
            result_state = UpdateState.ERROR

        # Step 4: Apply results thread-safely
        with self._lock:
            self.state = result_state
            self.latest_version = latest_ver
            self.release_name = rel_name
            self.release_notes = rel_notes
            self.download_url = dl_url
            self.published_at = pub_at
            self.error_message = error_msg
            self.last_checked_time = time.time()

        if on_complete and callable(on_complete):
            try:
                on_complete(self)
            except Exception:
                pass

    def open_download_page(self):
        """Safely opens the release / download URL in the user's default browser."""
        target_url = self.download_url or GITHUB_RELEASES_URL
        try:
            webbrowser.open(target_url)
            return True
        except Exception as e:
            print(f"[WARN] Failed to open browser for updates: {e}")
            return False
