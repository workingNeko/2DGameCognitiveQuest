# assets/sounds/generate_theme_music.py
"""
Thematic Background Music Generator for Cognitive Quest Quarters:
- Quarter 1 (Shapes & Medieval Forest): q1_forest_shapes.wav
- Quarter 2 (Division & Philippine Barrio Fiesta): q2_barrio_fiesta.wav
- Quarter 3 (Fractions & Ancient Sun Temple): q3_sun_temple.wav
- Quarter 4 (Time, Angles & Castle Clocktower): q4_clocktower_castle.wav

Generates high-quality, seamlessly looping 16-bit stereo 44.1kHz WAV tracks.
Zero external dependencies beyond numpy and standard python wave module.
"""

import os
import sys
import wave
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

SAMPLE_RATE = 44100

def note_to_freq(note_name):
    """Convert note name (e.g. 'C4', 'D#5', 'Gb3', 'A4') to Hz."""
    notes = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
             'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
             'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    letter = note_name[:-1]
    octave = int(note_name[-1])
    semitones = notes[letter] + (octave - 4) * 12 - 9 # A4 is 0 offset
    return 440.0 * (2.0 ** (semitones / 12.0))


def apply_adsr(length, attack, decay, sustain_level, release, sample_rate=SAMPLE_RATE):
    """Compute ADSR envelope vector of given sample length."""
    a_samples = int(attack * sample_rate)
    d_samples = int(decay * sample_rate)
    r_samples = int(release * sample_rate)
    s_samples = max(0, length - a_samples - d_samples - r_samples)

    env = []
    # Attack
    if a_samples > 0:
        env.append(np.linspace(0.0, 1.0, a_samples))
    # Decay
    if d_samples > 0:
        env.append(np.linspace(1.0, sustain_level, d_samples))
    # Sustain
    if s_samples > 0:
        env.append(np.full(s_samples, sustain_level))
    # Release
    if r_samples > 0:
        env.append(np.linspace(s_samples > 0 and sustain_level or 1.0, 0.0, r_samples))

    if not env:
        return np.ones(length)
    res = np.concatenate(env)
    if len(res) < length:
        res = np.pad(res, (0, length - len(res)))
    elif len(res) > length:
        res = res[:length]
    return res


def synthesize_instrument(freq, duration, inst_type='flute', sample_rate=SAMPLE_RATE):
    """Synthesizes an instrument tone with characteristic harmonics and ADSR."""
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples, False)

    if inst_type == 'flute':
        # Gentle breathy vibrato, rich 1st and 2nd harmonics
        vibrato = 1.0 + 0.015 * np.sin(2 * np.pi * 5.0 * t)
        phase = 2 * np.pi * freq * vibrato * t
        wave = (0.75 * np.sin(phase) +
                0.20 * np.sin(2 * phase) +
                0.05 * np.sin(3 * phase))
        env = apply_adsr(n_samples, 0.04, 0.08, 0.75, 0.08, sample_rate)
        return wave * env

    elif inst_type == 'lute':
        # Plucked string: quick attack, harmonic richness, rapid exponential decay
        wave = (0.60 * np.sin(2 * np.pi * freq * t) +
                0.25 * np.sin(2 * np.pi * 2 * freq * t) +
                0.10 * np.sin(2 * np.pi * 3 * freq * t) +
                0.05 * np.sin(2 * np.pi * 4 * freq * t))
        decay_rate = 4.0 + (freq / 200.0)
        env = np.exp(-t * decay_rate)
        return wave * env

    elif inst_type == 'marimba':
        # Wooden bar mallet: sharp pop attack, woody overtones
        wave = (0.70 * np.sin(2 * np.pi * freq * t) +
                0.22 * np.sin(2 * np.pi * 3.8 * freq * t) +
                0.08 * np.sin(2 * np.pi * 9.2 * freq * t))
        decay_rate = 6.0 + (freq / 150.0)
        env = np.exp(-t * decay_rate)
        return wave * env

    elif inst_type == 'bell' or inst_type == 'celesta':
        # Metallic chime: bright, shimmering inharmonic partials
        wave = (0.50 * np.sin(2 * np.pi * freq * t) +
                0.28 * np.sin(2 * np.pi * 2.76 * freq * t) +
                0.15 * np.sin(2 * np.pi * 5.4 * freq * t) +
                0.07 * np.sin(2 * np.pi * 8.9 * freq * t))
        env = np.exp(-t * 3.2)
        return wave * env

    elif inst_type == 'sitar':
        # Buzzing sympathetic resonance: harmonics with slow decay
        wave = (0.45 * np.sin(2 * np.pi * freq * t) +
                0.25 * np.sin(2 * np.pi * 2 * freq * t) +
                0.15 * np.sin(2 * np.pi * 3 * freq * t) +
                0.10 * np.sin(2 * np.pi * 4 * freq * t) +
                0.05 * np.sin(2 * np.pi * 5 * freq * t))
        # Jawari buzzing modulation
        buzz = 1.0 + 0.15 * np.sin(2 * np.pi * 12.0 * t)
        env = np.exp(-t * 2.8)
        return wave * buzz * env

    elif inst_type == 'bass':
        # Warm, deep fundamental bass
        wave = (0.80 * np.sin(2 * np.pi * freq * t) +
                0.18 * np.sin(2 * np.pi * 2 * freq * t) +
                0.02 * np.sin(2 * np.pi * 3 * freq * t))
        env = apply_adsr(n_samples, 0.02, 0.1, 0.8, 0.08, sample_rate)
        return wave * env

    elif inst_type == 'pad':
        # Warm ethereal synth pad
        vibrato = 1.0 + 0.008 * np.sin(2 * np.pi * 4.0 * t)
        phase = 2 * np.pi * freq * vibrato * t
        wave = (0.60 * np.sin(phase) +
                0.25 * np.sin(2 * phase) +
                0.15 * np.sin(3 * phase))
        env = apply_adsr(n_samples, 0.15, 0.15, 0.7, 0.20, sample_rate)
        return wave * env

    else:
        # Default simple tone
        return np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.0)


def add_note(track, start_time, duration, freq, inst_type, pan=0.0, vol=0.5, sample_rate=SAMPLE_RATE):
    """
    Renders note into track (stereo: (samples, 2)).
    pan: -1.0 (left) to 1.0 (right).
    vol: 0.0 to 1.0.
    Wraps overflow around to beginning to create a perfectly seamless loop!
    """
    note = synthesize_instrument(freq, duration, inst_type, sample_rate) * vol
    n_samples = len(note)
    start_idx = int(start_time * sample_rate)

    left_gain = np.sqrt(0.5 * (1.0 - pan))
    right_gain = np.sqrt(0.5 * (1.0 + pan))

    total_len = len(track)
    for i in range(n_samples):
        target_idx = (start_idx + i) % total_len
        track[target_idx, 0] += note[i] * left_gain
        track[target_idx, 1] += note[i] * right_gain


def add_percussion(track, start_time, perc_type, pan=0.0, vol=0.4, sample_rate=SAMPLE_RATE):
    """Adds synthesized rhythmic percussion hits."""
    start_idx = int(start_time * sample_rate)
    total_len = len(track)

    left_gain = np.sqrt(0.5 * (1.0 - pan))
    right_gain = np.sqrt(0.5 * (1.0 + pan))

    if perc_type == 'woodblock':
        dur = 0.05
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (np.sin(2 * np.pi * 900 * t) + 0.3 * np.sin(2 * np.pi * 1400 * t)) * np.exp(-t * 80) * vol
    elif perc_type == 'shaker':
        dur = 0.06
        n = int(dur * sample_rate)
        noise = (np.random.rand(n) * 2.0 - 1.0)
        t = np.linspace(0, dur, n, False)
        hit = noise * np.exp(-t * 50) * (vol * 0.4)
    elif perc_type == 'tick':
        # Clock tick / pendulum
        dur = 0.03
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120) * vol
    elif perc_type == 'tock':
        dur = 0.03
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 100) * vol
    elif perc_type == 'drum':
        # Ancient frame drum / bongo
        dur = 0.16
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        pitch = 110 * np.exp(-t * 15)
        hit = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 18) * vol
    else:
        dur = 0.05
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = np.sin(2 * np.pi * 500 * t) * np.exp(-t * 60) * vol

    for i in range(len(hit)):
        idx = (start_idx + i) % total_len
        track[idx, 0] += hit[i] * left_gain
        track[idx, 1] += hit[i] * right_gain


def save_wav(track, file_path, sample_rate=SAMPLE_RATE):
    """Normalizes and saves track as 16-bit stereo PCM WAV file."""
    # Peak normalization to -1.0 dB (~0.89)
    peak = np.max(np.abs(track))
    if peak > 0:
        norm_track = track * (0.88 / peak)
    else:
        norm_track = track

    # Soft limiter to prevent any digital clipping
    norm_track = np.tanh(norm_track * 1.1) * 0.90

    int_track = (norm_track * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_track.tobytes())
    print(f"🎵 Generated soundtrack: {file_path} ({len(track)/sample_rate:.2f}s loop)")


# ======================================================================
# 1. QUARTER 1: Medieval Forest & Geometric Wonder (Shapes Theme)
# Pastoral D Dorian: Plucked lute, wooden flute melody, warm acoustic bass
# ======================================================================
def generate_quarter1(output_path):
    bpm = 104
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Lute Arpeggios (Continuous flowing medieval pattern)
    # Chords: Dm (D-F-A), C (C-E-G), Bb (Bb-D-F), C (C-E-G), Dm, G/B, Bb, A
    chords_lute = [
        ['D3', 'A3', 'D4', 'F4', 'A4', 'F4', 'D4', 'A3'],
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        ['Bb2', 'F3', 'Bb3', 'D4', 'F4', 'D4', 'Bb3', 'F3'],
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        ['D3', 'A3', 'D4', 'F4', 'A4', 'F4', 'D4', 'A3'],
        ['G2', 'D3', 'G3', 'B3', 'D4', 'B3', 'G3', 'D3'],
        ['Bb2', 'F3', 'Bb3', 'D4', 'F4', 'D4', 'Bb3', 'F3'],
        ['A2', 'E3', 'A3', 'C#4', 'E4', 'C#4', 'A3', 'E3']
    ]

    for bar_idx, bar in enumerate(chords_lute):
        bar_start = bar_idx * 4 * beat_dur
        for step_idx, note_name in enumerate(bar):
            t = bar_start + step_idx * (beat_dur * 0.5)
            pan = -0.35 if step_idx % 2 == 0 else -0.15
            add_note(track, t, beat_dur * 0.9, note_to_freq(note_name), 'lute', pan=pan, vol=0.32)

    # 2. Wooden Flute Pastoral Melody
    flute_melody = [
        # Bar 1: D5 (1 beat), F5 (1 beat), E5 (0.5), D5 (0.5), A4 (1)
        (0.0, 1.0, 'D5', 0.25), (1.0, 1.0, 'F5', 0.25), (2.0, 0.5, 'E5', 0.22), (2.5, 0.5, 'D5', 0.22), (3.0, 1.0, 'A4', 0.20),
        # Bar 2: C5 (1), E5 (1), G5 (1.5), F5 (0.5)
        (4.0, 1.0, 'C5', 0.24), (5.0, 1.0, 'E5', 0.26), (6.0, 1.5, 'G5', 0.28), (7.5, 0.5, 'F5', 0.22),
        # Bar 3: D5 (1.5), F5 (0.5), Bb4 (1), D5 (1)
        (8.0, 1.5, 'D5', 0.26), (9.5, 0.5, 'F5', 0.24), (10.0, 1.0, 'Bb4', 0.22), (11.0, 1.0, 'D5', 0.24),
        # Bar 4: C5 (2), rest, E5 (1)
        (12.0, 2.0, 'C5', 0.25), (15.0, 1.0, 'E5', 0.22),
        # Bar 5: F5 (1.5), G5 (0.5), A5 (1.5), G5 (0.5)
        (16.0, 1.5, 'F5', 0.28), (17.5, 0.5, 'G5', 0.26), (18.0, 1.5, 'A5', 0.32), (19.5, 0.5, 'G5', 0.26),
        # Bar 6: F5 (1), D5 (1), B4 (2)
        (20.0, 1.0, 'F5', 0.26), (21.0, 1.0, 'D5', 0.24), (22.0, 2.0, 'B4', 0.26),
        # Bar 7: D5 (1), F5 (1), E5 (1), D5 (1)
        (24.0, 1.0, 'D5', 0.26), (25.0, 1.0, 'F5', 0.26), (26.0, 1.0, 'E5', 0.24), (27.0, 1.0, 'D5', 0.24),
        # Bar 8: C#5 (2), D5 (2) - resolution
        (28.0, 2.0, 'C#5', 0.26), (30.0, 2.0, 'D5', 0.30)
    ]

    for start_beat, dur_beats, note_name, vol in flute_melody:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.96,
                 note_to_freq(note_name), 'flute', pan=0.25, vol=vol)

    # 3. Warm Forest Bass
    bass_notes = [
        ('D2', 4), ('C2', 4), ('Bb1', 4), ('C2', 4),
        ('D2', 4), ('G1', 4), ('Bb1', 4), ('A1', 4)
    ]
    curr_beat = 0.0
    for note_name, dur_beats in bass_notes:
        add_note(track, curr_beat * beat_dur, dur_beats * beat_dur * 0.92,
                 note_to_freq(note_name), 'bass', pan=0.0, vol=0.38)
        curr_beat += dur_beats

    # 4. Light Woodland Percussion (Soft woodblock on beat 2 & 4, shaker)
    for b in range(bars * 4):
        t = b * beat_dur
        add_percussion(track, t, 'shaker', pan=0.3, vol=0.18)
        add_percussion(track, t + beat_dur * 0.5, 'shaker', pan=-0.3, vol=0.12)
        if b % 2 == 1:
            add_percussion(track, t, 'woodblock', pan=0.1, vol=0.22)

    save_wav(track, output_path)


# ======================================================================
# 2. QUARTER 2: Philippine Barrio Fiesta (Division & Sari-Sari Store Theme)
# Upbeat G Major: Tropical marimba/kulintang, syncopated fiesta rhythm
# ======================================================================
def generate_quarter2(output_path):
    bpm = 124
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Festive Marimba / Kulintang Pattern (Bouncy, syncopated Philippine fiesta vibe)
    # Chords: G major, C major, D major, G major, Em, C, D, G
    marimba_ostinato = [
        # Bar 1 (G)
        (0.0, 0.5, 'G4'), (0.5, 0.5, 'B4'), (1.0, 0.5, 'D5'), (1.75, 0.5, 'B4'), (2.5, 0.5, 'G4'), (3.0, 0.5, 'D5'),
        # Bar 2 (C)
        (4.0, 0.5, 'G4'), (4.5, 0.5, 'C5'), (5.0, 0.5, 'E5'), (5.75, 0.5, 'C5'), (6.5, 0.5, 'G4'), (7.0, 0.5, 'E5'),
        # Bar 3 (D)
        (8.0, 0.5, 'A4'), (8.5, 0.5, 'D5'), (9.0, 0.5, 'F#5'), (9.75, 0.5, 'D5'), (10.5, 0.5, 'A4'), (11.0, 0.5, 'F#5'),
        # Bar 4 (G)
        (12.0, 0.5, 'G4'), (12.5, 0.5, 'B4'), (13.0, 0.5, 'D5'), (13.5, 0.5, 'G5'), (14.25, 0.5, 'D5'), (15.0, 0.5, 'B4'),
        # Bar 5 (Em)
        (16.0, 0.5, 'E4'), (16.5, 0.5, 'G4'), (17.0, 0.5, 'B4'), (17.75, 0.5, 'E5'), (18.5, 0.5, 'B4'), (19.0, 0.5, 'G4'),
        # Bar 6 (C)
        (20.0, 0.5, 'C4'), (20.5, 0.5, 'E4'), (21.0, 0.5, 'G4'), (21.75, 0.5, 'C5'), (22.5, 0.5, 'G4'), (23.0, 0.5, 'E4'),
        # Bar 7 (D7)
        (24.0, 0.5, 'D4'), (24.5, 0.5, 'F#4'), (25.0, 0.5, 'A4'), (25.75, 0.5, 'C5'), (26.5, 0.5, 'A4'), (27.0, 0.5, 'F#4'),
        # Bar 8 (G)
        (28.0, 0.5, 'G4'), (28.5, 0.5, 'B4'), (29.0, 0.5, 'D5'), (29.5, 0.5, 'G5'), (30.0, 1.0, 'G5'), (31.0, 0.5, 'D5')
    ]

    for start_beat, dur_beats, note_name in marimba_ostinato:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.9,
                 note_to_freq(note_name), 'marimba', pan=-0.25, vol=0.35)

    # 2. Cheerful Fiesta Lead Horn / Bell Chime
    lead_melody = [
        (0.0, 1.0, 'B5'), (1.0, 0.5, 'A5'), (1.5, 0.5, 'G5'), (2.0, 1.5, 'D5'), (3.5, 0.5, 'G5'),
        (4.0, 1.0, 'E5'), (5.0, 0.5, 'G5'), (5.5, 0.5, 'C6'), (6.0, 2.0, 'B5'),
        (8.0, 1.0, 'A5'), (9.0, 0.5, 'B5'), (9.5, 0.5, 'C6'), (10.0, 1.5, 'D6'), (11.5, 0.5, 'B5'),
        (12.0, 2.5, 'G5'), (15.0, 1.0, 'D5'),
        (16.0, 1.0, 'G5'), (17.0, 0.5, 'F#5'), (17.5, 0.5, 'E5'), (18.0, 1.5, 'B5'), (19.5, 0.5, 'E5'),
        (20.0, 1.0, 'G5'), (21.0, 0.5, 'A5'), (21.5, 0.5, 'B5'), (22.0, 2.0, 'A5'),
        (24.0, 1.0, 'F#5'), (25.0, 1.0, 'A5'), (26.0, 1.0, 'C6'), (27.0, 1.0, 'D6'),
        (28.0, 2.0, 'B5'), (30.0, 2.0, 'G5')
    ]

    for start_beat, dur_beats, note_name in lead_melody:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.92,
                 note_to_freq(note_name), 'bell', pan=0.3, vol=0.26)

    # 3. Bouncy Tropical Bassline (Latin/Fiesta Tumbao)
    bass_pattern = [
        (0.0, 'G2'), (1.5, 'D2'), (2.5, 'G2'), (3.5, 'B1'),
        (4.0, 'C2'), (5.5, 'G1'), (6.5, 'C2'), (7.5, 'E2'),
        (8.0, 'D2'), (9.5, 'A1'), (10.5, 'D2'), (11.5, 'F#1'),
        (12.0, 'G2'), (13.5, 'D2'), (14.5, 'G2'), (15.5, 'D2'),
        (16.0, 'E2'), (17.5, 'B1'), (18.5, 'E2'), (19.5, 'G1'),
        (20.0, 'C2'), (21.5, 'G1'), (22.5, 'C2'), (23.5, 'E2'),
        (24.0, 'D2'), (25.5, 'A1'), (26.5, 'D2'), (27.5, 'F#1'),
        (28.0, 'G2'), (29.5, 'D2'), (30.5, 'G1'), (31.5, 'G2')
    ]

    for start_beat, note_name in bass_pattern:
        add_note(track, start_beat * beat_dur, beat_dur * 0.75,
                 note_to_freq(note_name), 'bass', pan=0.0, vol=0.42)

    # 4. Fiesta Shaker & Clave
    for b in range(bars * 4):
        t = b * beat_dur
        add_percussion(track, t, 'shaker', pan=-0.2, vol=0.20)
        add_percussion(track, t + beat_dur * 0.5, 'shaker', pan=0.2, vol=0.15)
        # Clave / Woodblock accents on 0, 1.5, 3
        if b % 4 in [0, 3]:
            add_percussion(track, t, 'woodblock', pan=0.15, vol=0.25)

    save_wav(track, output_path)


# ======================================================================
# 3. QUARTER 3: Ancient Sun Temple (Fractions & Desert Ruins Theme)
# Mystical E Phrygian / Harmonic Minor: Sitar, temple bells, desert drone
# ======================================================================
def generate_quarter3(output_path):
    bpm = 88
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Mystical Low Temple Drone (Continuous deep E2 + B2 drone)
    drone_samples = total_samples
    t_arr = np.linspace(0, total_duration, drone_samples, False)
    drone_w = (0.55 * np.sin(2 * np.pi * note_to_freq('E2') * t_arr) +
               0.28 * np.sin(2 * np.pi * note_to_freq('B2') * t_arr) +
               0.17 * np.sin(2 * np.pi * note_to_freq('E3') * t_arr))
    track[:, 0] += drone_w * 0.25
    track[:, 1] += drone_w * 0.25

    # 2. Atmospheric Temple Ethereal Pad
    # Chords: Em, Fmaj7 (Phrygian clash), G, Am, Em
    pad_chords = [
        (0.0, 4.0, ['E3', 'G3', 'B3']),
        (4.0, 4.0, ['F3', 'A3', 'C4']),
        (8.0, 4.0, ['E3', 'G#3', 'B3']), # Exotic major 3rd harmonic
        (12.0, 4.0, ['A3', 'C4', 'E4']),
        (16.0, 4.0, ['E3', 'G3', 'B3']),
        (20.0, 4.0, ['F3', 'A3', 'C4']),
        (24.0, 4.0, ['D#3', 'F#3', 'B3']),
        (28.0, 4.0, ['E3', 'G3', 'B3'])
    ]
    for start_beat, dur_beats, chord in pad_chords:
        for note_name in chord:
            add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.98,
                     note_to_freq(note_name), 'pad', pan=-0.2, vol=0.18)

    # 3. Sitar / Exotic Dulcimer Phrygian Lead Melody
    sitar_melody = [
        # Bar 1: E4 -> F4 -> G#4 (Phrygian dominant)
        (0.0, 1.0, 'E4'), (1.0, 0.5, 'F4'), (1.5, 0.5, 'E4'), (2.0, 1.5, 'G#4'), (3.5, 0.5, 'F4'),
        # Bar 2: E4 held, ornament
        (4.0, 2.0, 'E4'), (6.0, 0.75, 'B4'), (6.75, 0.5, 'C5'), (7.25, 0.75, 'B4'),
        # Bar 3: A4 -> G#4 -> F4
        (8.0, 1.5, 'A4'), (9.5, 0.5, 'G#4'), (10.0, 1.5, 'F4'), (11.5, 0.5, 'E4'),
        # Bar 4: D#4 -> E4
        (12.0, 2.0, 'D#4'), (14.0, 2.0, 'E4'),
        # Bar 5: Higher octave climb: E5 -> F5 -> G#5
        (16.0, 1.0, 'E5'), (17.0, 0.5, 'F5'), (17.5, 0.5, 'E5'), (18.0, 1.5, 'G#5'), (19.5, 0.5, 'F5'),
        # Bar 6: E5 -> B5 -> C6 -> B5
        (20.0, 1.5, 'E5'), (21.5, 0.5, 'B5'), (22.0, 1.0, 'C6'), (23.0, 1.0, 'B5'),
        # Bar 7: A5 -> G#5 -> F5
        (24.0, 1.0, 'A5'), (25.0, 1.0, 'G#5'), (26.0, 1.0, 'F5'), (27.0, 1.0, 'D#5'),
        # Bar 8: Resolution to E5
        (28.0, 3.0, 'E5'), (31.0, 1.0, 'B4')
    ]

    for start_beat, dur_beats, note_name in sitar_melody:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.95,
                 note_to_freq(note_name), 'sitar', pan=0.25, vol=0.36)

    # 4. Ancient Temple Percussion (Doumbek / Frame Drum "Dum - Tak - Tak")
    for b in range(bars * 4):
        t = b * beat_dur
        # Deep resonant dum on beat 1 and 3
        if b % 4 == 0:
            add_percussion(track, t, 'drum', pan=0.0, vol=0.45)
        elif b % 4 == 2:
            add_percussion(track, t, 'drum', pan=0.0, vol=0.35)
        # Crisp tak accents on offbeats
        if b % 2 == 1:
            add_percussion(track, t, 'woodblock', pan=0.3, vol=0.20)
        if b % 4 == 3:
            add_percussion(track, t + beat_dur * 0.5, 'tick', pan=-0.3, vol=0.22)

    save_wav(track, output_path)


# ======================================================================
# 4. QUARTER 4: Castle Clocktower & Celestial Mechanism (Time & Angles)
# Clockwork A Minor / C Major: Pendulum ticks, music box celesta arpeggios
# ======================================================================
def generate_quarter4(output_path):
    bpm = 110
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Continuous Mechanical Clockwork Ticking (Tic-Toc pendulum)
    for b in range(bars * 4):
        t = b * beat_dur
        # Beat: High Tick
        add_percussion(track, t, 'tick', pan=-0.25, vol=0.28)
        # Half-beat: Low Tock
        add_percussion(track, t + beat_dur * 0.5, 'tock', pan=0.25, vol=0.24)

    # 2. Celesta / Clock Chime Arpeggiated Gears (Am, F, Dm, E7, Am, G, F, E7)
    gears_pattern = [
        # Bar 1 (Am)
        ['A4', 'C5', 'E5', 'A5', 'E5', 'C5', 'A4', 'C5'],
        # Bar 2 (F)
        ['F4', 'A4', 'C5', 'F5', 'C5', 'A4', 'F4', 'A4'],
        # Bar 3 (Dm)
        ['D4', 'F4', 'A4', 'D5', 'A4', 'F4', 'D4', 'F4'],
        # Bar 4 (E)
        ['E4', 'G#4', 'B4', 'E5', 'B4', 'G#4', 'E4', 'G#4'],
        # Bar 5 (Am)
        ['A4', 'C5', 'E5', 'A5', 'E5', 'C5', 'A4', 'C5'],
        # Bar 6 (G)
        ['G4', 'B4', 'D5', 'G5', 'D5', 'B4', 'G4', 'B4'],
        # Bar 7 (F)
        ['F4', 'A4', 'C5', 'F5', 'C5', 'A4', 'F4', 'A4'],
        # Bar 8 (E)
        ['E4', 'G#4', 'B4', 'D5', 'B4', 'G#4', 'E4', 'B4']
    ]

    for bar_idx, bar in enumerate(gears_pattern):
        bar_start = bar_idx * 4 * beat_dur
        for step_idx, note_name in enumerate(bar):
            t = bar_start + step_idx * (beat_dur * 0.5)
            pan = 0.35 if step_idx % 2 == 0 else 0.15
            add_note(track, t, beat_dur * 0.85, note_to_freq(note_name), 'celesta', pan=pan, vol=0.28)

    # 3. Majestic Clocktower Horn / Pad Melody (Noble, regal, inquisitive)
    clocktower_lead = [
        # Bar 1: E5 (2), A5 (1.5), B5 (0.5)
        (0.0, 2.0, 'E5'), (2.0, 1.5, 'A5'), (3.5, 0.5, 'B5'),
        # Bar 2: C6 (2), B5 (1), A5 (1)
        (4.0, 2.0, 'C6'), (6.0, 1.0, 'B5'), (7.0, 1.0, 'A5'),
        # Bar 3: F5 (2), A5 (1), D6 (1)
        (8.0, 2.0, 'F5'), (10.0, 1.0, 'A5'), (11.0, 1.0, 'D6'),
        # Bar 4: B5 (2.5), G#5 (1.5)
        (12.0, 2.5, 'B5'), (14.5, 1.5, 'G#5'),
        # Bar 5: E5 (1.5), A5 (1.5), C6 (1)
        (16.0, 1.5, 'E5'), (17.5, 1.5, 'A5'), (19.0, 1.0, 'C6'),
        # Bar 6: D6 (1.5), B5 (1.5), G5 (1)
        (20.0, 1.5, 'D6'), (21.5, 1.5, 'B5'), (23.0, 1.0, 'G5'),
        # Bar 7: A5 (1.5), F5 (1.5), D5 (1)
        (24.0, 1.5, 'A5'), (25.5, 1.5, 'F5'), (27.0, 1.0, 'D5'),
        # Bar 8: E5 (2.0), A5 (2.0) - Grand grandfather clock resolution
        (28.0, 2.0, 'E5'), (30.0, 2.0, 'A5')
    ]

    for start_beat, dur_beats, note_name in clocktower_lead:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.94,
                 note_to_freq(note_name), 'pad', pan=-0.25, vol=0.34)

    # 4. Stately Bass Chords
    stately_bass = [
        (0.0, 'A1'), (4.0, 'F1'), (8.0, 'D2'), (12.0, 'E2'),
        (16.0, 'A1'), (20.0, 'G1'), (24.0, 'F1'), (28.0, 'E1')
    ]
    for start_beat, note_name in stately_bass:
        add_note(track, start_beat * beat_dur, 4.0 * beat_dur * 0.9,
                 note_to_freq(note_name), 'bass', pan=0.0, vol=0.40)

    save_wav(track, output_path)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sounds_dir = os.path.join(base_dir, "assets", "sounds")

    q1_path = os.path.join(sounds_dir, "q1_forest_shapes.wav")
    q2_path = os.path.join(sounds_dir, "q2_barrio_fiesta.wav")
    q3_path = os.path.join(sounds_dir, "q3_sun_temple.wav")
    q4_path = os.path.join(sounds_dir, "q4_clocktower_castle.wav")

    print("🎹 Starting synthesis of Cognitive Quest thematic soundtracks...")
    generate_quarter1(q1_path)
    generate_quarter2(q2_path)
    generate_quarter3(q3_path)
    generate_quarter4(q4_path)
    print("✨ All 4 quarter soundtracks generated successfully!")


if __name__ == "__main__":
    main()
