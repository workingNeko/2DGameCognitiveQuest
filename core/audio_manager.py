# core/audio_manager.py - Centralized Audio & Sound Management System
import os
import sys
import json
import pygame
import numpy as np

# Safe stdout for Windows console
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


class AudioManager:
    """
    Centralized Audio and Sound System for Cognitive Quest.
    Handles background music, sound effects, volume control, mute states,
    and persistent audio preferences. Safe for low-spec hardware (Raspberry Pi).
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True

        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_file = os.path.join(self.BASE_DIR, "db", "saves", "audio_settings.json")
        self.default_music_path = os.path.join(self.BASE_DIR, "assets", "sounds", "backgroundgamesoundloop.wav")

        # Scene-to-soundtrack mapping for thematic audio
        self.SCENE_MUSIC_MAP = {
            "menu": "backgroundgamesoundloop.wav",
            "stage_select": "backgroundgamesoundloop.wav",
            "student_select": "backgroundgamesoundloop.wav",
            "tutorial": "backgroundgamesoundloop.wav",
            "leaderboard": "backgroundgamesoundloop.wav",
            "quarter1": "q1_forest_shapes.wav",
            "quarter2": "q2_barrio_fiesta.wav",
            "quarter3": "q3_sun_temple.wav",
            "quarter4": "q4_clocktower_castle.wav",
        }

        # Audio state
        self.available = False
        self.current_music_path = None
        self.music_volume = 0.5   # 0.0 to 1.0
        self.sfx_volume = 0.7     # 0.0 to 1.0
        self.music_muted = False
        self.sfx_muted = False

        # SFX Cache
        self.sfx_cache = {}

        # 1. Initialize Pygame Mixer safely
        self._init_mixer()

        # 2. Load persistent settings if available
        self.load_settings()

        # 3. Pre-synthesize common zero-dependency sound effects
        if self.available:
            self._generate_core_sfx()

    def _init_mixer(self):
        """Initializes pygame.mixer safely with graceful fallback for Raspberry Pi/Linux."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.available = True
            print("[AUDIO] AudioManager initialized successfully.")
        except Exception as e:
            self.available = False
            print(f"[WARN] AudioManager warning: Failed to initialize audio mixer: {e}")

    # ============================================================
    # PERSISTENCE (SAVE / LOAD)
    # ============================================================

    def load_settings(self):
        """Loads volume and mute settings from disk."""
        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.music_volume = float(data.get("music_volume", 0.5))
                self.sfx_volume = float(data.get("sfx_volume", 0.7))
                self.music_muted = bool(data.get("music_muted", False))
                self.sfx_muted = bool(data.get("sfx_muted", False))

                # Clamp values
                self.music_volume = max(0.0, min(1.0, self.music_volume))
                self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))

            self._apply_music_volume()
        except Exception as e:
            print(f"[WARN] AudioManager: Error reading audio settings: {e}")

    def save_settings(self):
        """Persists current volume and mute settings to disk."""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            data = {
                "music_volume": round(self.music_volume, 2),
                "sfx_volume": round(self.sfx_volume, 2),
                "music_muted": self.music_muted,
                "sfx_muted": self.sfx_muted
            }
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[WARN] AudioManager: Error saving audio settings: {e}")

    # ============================================================
    # BACKGROUND MUSIC (BGM)
    # ============================================================

    def play_scene_music(self, scene_name, fade_ms=600):
        """
        Plays the appropriate background music track for a game scene or quarter.
        Smoothly crossfades when changing scenes and ignores redundant calls if
        the same track is already playing.
        """
        if not self.available:
            return

        track_filename = self.SCENE_MUSIC_MAP.get(scene_name, "backgroundgamesoundloop.wav")
        track_path = os.path.join(self.BASE_DIR, "assets", "sounds", track_filename)

        # Fallback to default music if custom track doesn't exist
        if not os.path.exists(track_path):
            track_path = self.default_music_path

        # If already playing this music, do not restart
        if self.current_music_path == track_path and pygame.mixer.music.get_busy():
            self._apply_music_volume()
            return

        print(f"[MUSIC] AudioManager: Transitioning music for '{scene_name}' -> {os.path.basename(track_path)}")
        self.play_music(track_path, loop=-1, fade_ms=fade_ms)

    def play_music(self, path=None, loop=-1, fade_ms=500):
        """Plays background music safely. If path is None, uses default music."""
        if not self.available:
            return

        music_path = path or self.default_music_path
        if not os.path.isabs(music_path):
            music_path = os.path.join(self.BASE_DIR, music_path)

        if not os.path.exists(music_path):
            print(f"[WARN] AudioManager: Music file not found: {music_path}")
            return

        try:
            # If already playing this exact music track, ensure volume is updated and continue
            if self.current_music_path == music_path and pygame.mixer.music.get_busy():
                self._apply_music_volume()
                return

            self.current_music_path = music_path
            pygame.mixer.music.load(music_path)
            self._apply_music_volume()
            if fade_ms > 0:
                pygame.mixer.music.play(loop, fade_ms=fade_ms)
            else:
                pygame.mixer.music.play(loop)
        except Exception as e:
            print(f"[WARN] AudioManager: Exception playing music: {e}")

    def _apply_music_volume(self):
        """Internal helper to apply volume and mute state to Pygame mixer."""
        if not self.available:
            return
        try:
            actual_vol = 0.0 if self.music_muted else self.music_volume
            pygame.mixer.music.set_volume(actual_vol)
        except Exception:
            pass

    def stop_music(self):
        if self.available:
            try:
                pygame.mixer.music.stop()
                self.current_music_path = None
            except Exception:
                pass

    def pause_music(self):
        if self.available:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def unpause_music(self):
        if self.available:
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass

    def set_music_volume(self, volume):
        """Sets music volume from 0.0 to 1.0 and saves settings."""
        self.music_volume = max(0.0, min(1.0, float(volume)))
        self._apply_music_volume()
        self.save_settings()

    def toggle_music_mute(self):
        """Toggles music mute on/off."""
        self.music_muted = not self.music_muted
        self._apply_music_volume()
        self.save_settings()
        return self.music_muted

    # ============================================================
    # SOUND EFFECTS (SFX)
    # ============================================================

    def set_sfx_volume(self, volume):
        """Sets SFX volume from 0.0 to 1.0 and saves settings."""
        self.sfx_volume = max(0.0, min(1.0, float(volume)))
        self.save_settings()

    def toggle_sfx_mute(self):
        """Toggles SFX mute on/off."""
        self.sfx_muted = not self.sfx_muted
        self.save_settings()
        return self.sfx_muted

    def toggle_master_mute(self):
        """Toggles both music and SFX mute together."""
        # If either is unmuted, mute both; if both are muted, unmute both
        if not self.music_muted or not self.sfx_muted:
            self.music_muted = True
            self.sfx_muted = True
        else:
            self.music_muted = False
            self.sfx_muted = False
        self._apply_music_volume()
        self.save_settings()
        return self.music_muted

    def play_sfx(self, sound_name_or_obj, volume_scale=1.0):
        """
        Plays a sound effect by name (e.g. 'click', 'snap', 'success', 'correct', 'bell')
        or directly from a pygame.mixer.Sound object.
        """
        if not self.available or self.sfx_muted:
            return None

        sound = None
        if isinstance(sound_name_or_obj, pygame.mixer.Sound):
            sound = sound_name_or_obj
        elif isinstance(sound_name_or_obj, str):
            sound = self.sfx_cache.get(sound_name_or_obj)
            if sound is None:
                # Try loading from assets/sounds/
                custom_path = os.path.join(self.BASE_DIR, "assets", "sounds", sound_name_or_obj)
                if not custom_path.endswith((".wav", ".ogg")):
                    custom_path += ".wav"
                if os.path.exists(custom_path):
                    try:
                        sound = pygame.mixer.Sound(custom_path)
                        self.sfx_cache[sound_name_or_obj] = sound
                    except Exception:
                        sound = None

        if sound is not None:
            try:
                eff_vol = max(0.0, min(1.0, self.sfx_volume * volume_scale))
                sound.set_volume(eff_vol)
                sound.play()
                return sound
            except Exception:
                pass
        return None

    def get_sound(self, name_or_obj):
        """Returns a pygame.mixer.Sound instance by name from cache or None."""
        if not self.available:
            return None
        if isinstance(name_or_obj, pygame.mixer.Sound):
            return name_or_obj
        if isinstance(name_or_obj, str):
            sound = self.sfx_cache.get(name_or_obj)
            if sound is not None:
                eff_vol = 0.0 if self.sfx_muted else self.sfx_volume
                sound.set_volume(eff_vol)
                return sound
        return None

    # ============================================================
    # SYNTHESIZED SOUND EFFECTS ENGINE (Zero-Dependency Waveforms)
    # ============================================================

    def _generate_core_sfx(self):
        """Generates crisp, retro/arcade sound effects directly in memory."""
        sr = 44100
        try:
            # 1. UI Click
            t_clk = np.linspace(0, 0.04, int(sr * 0.04), False)
            w_clk = np.sin(2 * np.pi * 1200 * t_clk) * np.exp(-t_clk * 90)
            a_clk = (w_clk * 26000).astype(np.int16)
            self.sfx_cache["click"] = pygame.sndarray.make_sound(np.column_stack((a_clk, a_clk)))

            # 2. Snap / Pop (Jigsaw / Tile snap)
            t_snp = np.linspace(0, 0.08, int(sr * 0.08), False)
            w_snp = np.sin(2 * np.pi * 880 * t_snp) * np.exp(-t_snp * 35)
            a_snp = (w_snp * 28000).astype(np.int16)
            self.sfx_cache["snap"] = pygame.sndarray.make_sound(np.column_stack((a_snp, a_snp)))

            # 3. Correct (Dual Harmonic Bright Ding)
            t_cor = np.linspace(0, 0.35, int(sr * 0.35), False)
            w_cor = (0.6 * np.sin(2 * np.pi * 1046.5 * t_cor) + 0.4 * np.sin(2 * np.pi * 1318.5 * t_cor)) * np.exp(-t_cor * 10)
            a_cor = (w_cor * 28000).astype(np.int16)
            self.sfx_cache["correct"] = pygame.sndarray.make_sound(np.column_stack((a_cor, a_cor)))

            # 4. Success / Fanfare (C-Major Arpeggio: C5, E5, G5, C6)
            t_suc = np.linspace(0, 0.65, int(sr * 0.65), False)
            notes = [523.25, 659.25, 783.99, 1046.50]
            w_suc = np.zeros_like(t_suc)
            for idx, freq in enumerate(notes):
                d = idx * 0.11
                nt = t_suc - d
                started = nt >= 0
                w_suc += np.sin(2 * np.pi * freq * nt) * np.exp(-8 * nt) * started * 0.3
            w_suc = np.clip(w_suc, -1.0, 1.0)
            a_suc = (w_suc * 30000).astype(np.int16)
            self.sfx_cache["success"] = pygame.sndarray.make_sound(np.column_stack((a_suc, a_suc)))

            # 5. Wrong / Error (Low descending buzz)
            t_wrg = np.linspace(0, 0.28, int(sr * 0.28), False)
            w_wrg = (0.7 * np.sin(2 * np.pi * 220 * t_wrg) + 0.3 * np.sin(2 * np.pi * 165 * t_wrg)) * np.exp(-t_wrg * 8)
            a_wrg = (w_wrg * 26000).astype(np.int16)
            self.sfx_cache["wrong"] = pygame.sndarray.make_sound(np.column_stack((a_wrg, a_wrg)))

            # 6. Ice Cream / Sorbetes Bell ("Kling-kling")
            t_bel = np.linspace(0, 0.35, int(sr * 0.35), False)
            w_bel = (0.6 * np.sin(2 * np.pi * 1568 * t_bel) + 0.4 * np.sin(2 * np.pi * 2093 * t_bel)) * np.exp(-t_bel * 10)
            a_bel = (w_bel * 30000).astype(np.int16)
            self.sfx_cache["bell"] = pygame.sndarray.make_sound(np.column_stack((a_bel, a_bel)))

            # 7. Coin Clink
            t_coin = np.linspace(0, 0.18, int(sr * 0.18), False)
            w_coin = (0.7 * np.sin(2 * np.pi * 2489 * t_coin) + 0.3 * np.sin(2 * np.pi * 3322 * t_coin)) * np.exp(-t_coin * 20)
            a_coin = (w_coin * 30000).astype(np.int16)
            self.sfx_cache["coin"] = pygame.sndarray.make_sound(np.column_stack((a_coin, a_coin)))

            # 8. Test Chime
            t_chm = np.linspace(0, 0.4, int(sr * 0.4), False)
            w_chm = (0.5 * np.sin(2 * np.pi * 880 * t_chm) + 0.5 * np.sin(2 * np.pi * 1174.66 * t_chm)) * np.exp(-t_chm * 8)
            a_chm = (w_chm * 28000).astype(np.int16)
            self.sfx_cache["chime"] = pygame.sndarray.make_sound(np.column_stack((a_chm, a_chm)))

            # 9. Jeepney Horn ("Beep-beep")
            t_hrn = np.linspace(0, 0.28, int(sr * 0.28), False)
            w_hrn = 0.5 * np.sin(2 * np.pi * 440 * t_hrn) + 0.5 * np.sin(2 * np.pi * 554 * t_hrn)
            env_hrn = np.ones_like(t_hrn)
            env_hrn[-int(sr * 0.04):] = np.linspace(1, 0, int(sr * 0.04))
            a_hrn = (w_hrn * env_hrn * 28000).astype(np.int16)
            self.sfx_cache["horn"] = pygame.sndarray.make_sound(np.column_stack((a_hrn, a_hrn)))

            # 10. Cash Register / Sukli Chime
            t_reg = np.linspace(0, 0.3, int(sr * 0.3), False)
            w_reg = (0.5 * np.sin(2 * np.pi * 1046 * t_reg) + 0.5 * np.sin(2 * np.pi * 1318 * t_reg)) * np.exp(-t_reg * 12)
            a_reg = (w_reg * 30000).astype(np.int16)
            self.sfx_cache["cash_register"] = pygame.sndarray.make_sound(np.column_stack((a_reg, a_reg)))

            # 11. Bamboo / Wood Construction Knock
            t_wd = np.linspace(0, 0.07, int(sr * 0.07), False)
            w_wd = np.sin(2 * np.pi * 650 * t_wd) * np.exp(-t_wd * 45)
            a_wd = (w_wd * 28000).astype(np.int16)
            self.sfx_cache["wood_snap"] = pygame.sndarray.make_sound(np.column_stack((a_wd, a_wd)))

            # 12. Portal Warp / Teleport (Ascending pitch swirl whoosh)
            t_prt = np.linspace(0, 0.45, int(sr * 0.45), False)
            freq_prt = 300 + 1400 * (t_prt / 0.45)**1.5
            w_prt = (0.7 * np.sin(2 * np.pi * freq_prt * t_prt) +
                     0.3 * np.sin(2 * np.pi * freq_prt * 1.5 * t_prt))
            env_prt = np.sin(np.pi * (t_prt / 0.45))
            a_prt = (w_prt * env_prt * 26000).astype(np.int16)
            self.sfx_cache["portal_warp"] = pygame.sndarray.make_sound(np.column_stack((a_prt, a_prt)))

            # 13. Timer Warning (Double urgency chime)
            t_wrn = np.linspace(0, 0.35, int(sr * 0.35), False)
            w_wrn = (0.6 * np.sin(2 * np.pi * 880 * t_wrn) + 0.4 * np.sin(2 * np.pi * 1760 * t_wrn)) * np.exp(-t_wrn * 15)
            pip2_idx = int(sr * 0.15)
            t_pip2 = t_wrn[pip2_idx:] - 0.15
            w_wrn[pip2_idx:] += (0.6 * np.sin(2 * np.pi * 1046 * t_pip2) + 0.4 * np.sin(2 * np.pi * 2093 * t_pip2)) * np.exp(-t_pip2 * 15)
            a_wrn = (np.clip(w_wrn, -1.0, 1.0) * 28000).astype(np.int16)
            self.sfx_cache["timer_warning"] = pygame.sndarray.make_sound(np.column_stack((a_wrn, a_wrn)))

            # 14. Victory Fanfare (Grand ceremonial brass arpeggio: C4, G4, C5, E5, G5, C6)
            t_fan = np.linspace(0, 1.1, int(sr * 1.1), False)
            fan_notes = [(0.0, 261.63), (0.12, 392.0), (0.24, 523.25), (0.36, 659.25), (0.48, 783.99), (0.60, 1046.5)]
            w_fan = np.zeros_like(t_fan)
            for onset, f in fan_notes:
                dt_fan = t_fan - onset
                active = dt_fan >= 0
                env = np.exp(-dt_fan * (3.5 if onset < 0.60 else 1.8)) * active
                tone = np.sin(2 * np.pi * f * dt_fan) + 0.3 * np.sin(2 * np.pi * 2 * f * dt_fan)
                w_fan += tone * env * 0.25
            a_fan = (np.clip(w_fan, -1.0, 1.0) * 29000).astype(np.int16)
            self.sfx_cache["victory_fanfare"] = pygame.sndarray.make_sound(np.column_stack((a_fan, a_fan)))

        except Exception as e:
            print(f"[WARN] AudioManager: Warning synthesizing core SFX: {e}")


# Global Singleton Instance
audio_manager = AudioManager()
