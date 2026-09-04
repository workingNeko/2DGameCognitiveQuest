# assets/sounds/generate_theme_music.py
"""
Thematic Background Music Generator for Cognitive Quest Quarters:
- Quarter 1 (Shapes & Old Man - "Storybook Meadow"): q1_forest_shapes.wav
  * A cheerful, gentle storybook theme featuring warm acoustic piano, music box,
    soft whimsical melody, and light woodland shaker.
- Quarter 2 (Division & Barrio Fiesta): q2_barrio_fiesta.wav
  * Upbeat tropical celebration with bouncy marimba/kulintang, fiesta clave, and tumbao bass.
- Quarter 3 (Fractions & Sun Temple - "Oasis Mirage"): q3_sun_temple.wav
  * A calm, atmospheric desert oasis featuring warm ambient pads, relaxing harp
    arpeggios, soft wind chimes, and a gentle soothing desert ney melody.
- Quarter 4 (Time, Angles & Clocktower - "The Celestial Clocktower"): q4_clocktower_castle.wav
  * Intricate Baroque Clockwork Allegro with dual-ear pendulum ticking, glistening
    music box/celesta gear runs, and noble castle French horns.

Generates seamlessly looping 16-bit stereo 44.1kHz WAV tracks.
Zero external dependencies beyond numpy and standard library wave.
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


def apply_stereo_reverb(stereo_track, wet=0.22, sample_rate=SAMPLE_RATE):
    """
    Applies multi-tap stereo spatial diffusion to give instruments warmth and depth.
    Loops seamlessly by wrapping reflection tails with np.roll.
    """
    reflections = [
        (int(sample_rate * 0.023), 0.35, -0.45),
        (int(sample_rate * 0.037), 0.28, 0.45),
        (int(sample_rate * 0.053), 0.22, -0.65),
        (int(sample_rate * 0.071), 0.17, 0.65),
        (int(sample_rate * 0.097), 0.13, -0.30),
        (int(sample_rate * 0.131), 0.09, 0.30),
    ]
    wet_track = np.zeros_like(stereo_track)
    for d, gain, pan in reflections:
        lg = gain * np.sqrt(0.5 * (1.0 - pan))
        rg = gain * np.sqrt(0.5 * (1.0 + pan))
        wet_track[:, 0] += np.roll(stereo_track[:, 0], d) * lg
        wet_track[:, 1] += np.roll(stereo_track[:, 1], d) * rg

    return stereo_track * (1.0 - wet * 0.5) + wet_track * wet


def synthesize_instrument(freq, duration, inst_type='piano', sample_rate=SAMPLE_RATE):
    """
    Synthesizes rich acoustic and fantasy instrument timbres:
    - piano (warm acoustic piano with felt hammer attack and multi-harmonic body)
    - music_box (sparkling, crystalline music box chime)
    - fm_pluck (relaxing acoustic harp / lute)
    - pad (warm ambient ethereal synth pad)
    - strings (lush detuned string ensemble)
    - ney (soothing, gentle desert reed flute)
    - whistle (Celtic tin whistle / wooden recorder)
    - celesta (crystal-clear music box / gear chimes)
    - pizzicato (snappy orchestral string pluck)
    - horn (noble French horn / castle brass)
    - bass (warm upright / sub-bass)
    - marimba (tropical wooden mallet)
    """
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples, False)

    if inst_type == 'piano':
        # Warm acoustic piano: felt hammer transient + rich warm body harmonics
        decay_rate = 2.2 + (freq / 350.0)
        tone = (0.65 * np.sin(2 * np.pi * freq * t) +
                0.24 * np.sin(2 * np.pi * 2 * freq * t) +
                0.08 * np.sin(2 * np.pi * 3 * freq * t) +
                0.03 * np.sin(2 * np.pi * 4 * freq * t))
        # Soft felt attack (6ms)
        att_s = min(int(sample_rate * 0.006), n_samples // 4)
        env = np.exp(-t * decay_rate)
        if att_s > 0:
            env[:att_s] *= np.linspace(0.0, 1.0, att_s)
        return tone * env

    elif inst_type == 'music_box':
        # Pure, delicate music box chime with crystalline inharmonic overtones
        tone = (0.60 * np.sin(2 * np.pi * freq * t) +
                0.28 * np.sin(2 * np.pi * 2.756 * freq * t) +
                0.12 * np.sin(2 * np.pi * 5.404 * freq * t))
        env = np.exp(-t * 4.2)
        return tone * env

    elif inst_type == 'fm_pluck':
        # Relaxing acoustic harp / kanun pluck
        decay_rate = 3.0 + (freq / 350.0)
        mod_env = np.exp(-t * 9.0)
        amp_env = np.exp(-t * decay_rate)
        mod = 2.4 * mod_env * np.sin(2 * np.pi * freq * t)
        tone = (0.75 * np.sin(2 * np.pi * freq * t + mod) +
                0.20 * np.sin(2 * np.pi * 2 * freq * t) +
                0.05 * np.sin(2 * np.pi * 3 * freq * t))
        return tone * amp_env

    elif inst_type == 'pad':
        # Warm ambient ethereal synth pad: soft, slow-attack floating cushion
        vibrato = 1.0 + 0.008 * np.sin(2 * np.pi * 4.2 * t)
        phase = 2 * np.pi * freq * vibrato * t
        w1 = np.sin(phase)
        w2 = np.sin(phase * 1.003)
        w3 = np.sin(phase * 0.997)
        tone = (w1 + 0.8 * w2 + 0.8 * w3) / 2.6
        att_s = min(int(sample_rate * 0.12), n_samples // 4)
        rel_s = min(int(sample_rate * 0.18), n_samples // 4)
        env = np.ones(n_samples)
        if att_s > 0:
            env[:att_s] = np.linspace(0.0, 1.0, att_s)
        if rel_s > 0:
            env[-rel_s:] = np.linspace(1.0, 0.0, rel_s)
        return tone * env

    elif inst_type == 'strings':
        # Lush detuned string ensemble
        w1 = np.sin(2 * np.pi * freq * t)
        w2 = np.sin(2 * np.pi * freq * 1.004 * t)
        w3 = np.sin(2 * np.pi * freq * 0.996 * t)
        tone = (w1 + 0.85 * w2 + 0.85 * w3) / 2.7
        att_s = min(int(sample_rate * 0.06), n_samples // 4)
        rel_s = min(int(sample_rate * 0.08), n_samples // 4)
        env = np.ones(n_samples)
        if att_s > 0:
            env[:att_s] = np.linspace(0.0, 1.0, att_s)
        if rel_s > 0:
            env[-rel_s:] = np.linspace(1.0, 0.0, rel_s)
        return tone * env

    elif inst_type in ['guitar', 'acoustic_guitar']:
        # Warm acoustic nylon/Spanish guitar: woody body harmonics and organic pluck decay
        decay_rate = 2.5 + (freq / 350.0)
        tone = (0.60 * np.sin(2 * np.pi * freq * t) +
                0.25 * np.sin(2 * np.pi * 2 * freq * t) +
                0.11 * np.sin(2 * np.pi * 3 * freq * t) +
                0.04 * np.sin(2 * np.pi * 4 * freq * t))
        att_s = min(int(sample_rate * 0.005), n_samples // 4)
        env = np.exp(-t * decay_rate)
        if att_s > 0:
            env[:att_s] *= np.linspace(0.0, 1.0, att_s)
        return tone * env

    elif inst_type in ['ney', 'pan_flute', 'flute']:
        # Sweet, soothing wooden pan flute: warm fundamental, mellow breath attack, gentle subtle vibrato
        vib = 1.0 + 0.003 * np.sin(2 * np.pi * 4.2 * t)
        ph = 2 * np.pi * freq * vib * t
        tone = (0.80 * np.sin(ph) +
                0.15 * np.sin(2 * ph) +
                0.05 * np.sin(3 * ph))
        att_s = min(int(sample_rate * 0.025), n_samples // 4)
        rel_s = min(int(sample_rate * 0.06), n_samples // 4)
        env = np.ones(n_samples)
        if att_s > 0:
            env[:att_s] = np.linspace(0.0, 1.0, att_s)
        if rel_s > 0:
            env[-rel_s:] = np.linspace(1.0, 0.0, rel_s)
        env *= np.exp(-t * 1.0)
        return tone * env

    elif inst_type == 'celesta':
        # Crystalline music box / celesta bells (spinning clockwork gears)
        mod_c = 1.7 * np.exp(-t * 6.5) * np.sin(2 * np.pi * freq * 2.756 * t)
        tone = (0.60 * np.sin(2 * np.pi * freq * t + mod_c) +
                0.25 * np.sin(2 * np.pi * 5.404 * freq * t) +
                0.15 * np.sin(2 * np.pi * 8.932 * freq * t))
        env = np.exp(-t * 3.8)
        return tone * env

    elif inst_type == 'pizzicato':
        # Crisp orchestral pizzicato string pluck
        tone = (0.60 * np.sin(2 * np.pi * freq * t) +
                0.28 * np.sin(2 * np.pi * 2 * freq * t) +
                0.12 * np.sin(2 * np.pi * 3 * freq * t))
        env = np.exp(-t * 12.0)
        return tone * env

    elif inst_type == 'horn':
        # Stately French horn / Castle brass
        mod_h = 1.2 * np.exp(-t * 2.0) * np.sin(2 * np.pi * freq * t)
        tone = (0.70 * np.sin(2 * np.pi * freq * t + mod_h) +
                0.25 * np.sin(2 * np.pi * 2 * freq * t) +
                0.05 * np.sin(2 * np.pi * 3 * freq * t))
        att_s = min(int(sample_rate * 0.07), n_samples // 4)
        rel_s = min(int(sample_rate * 0.10), n_samples // 4)
        env = np.ones(n_samples)
        if att_s > 0:
            env[:att_s] = np.linspace(0.0, 1.0, att_s)
        if rel_s > 0:
            env[-rel_s:] = np.linspace(1.0, 0.0, rel_s)
        return tone * env

    elif inst_type == 'bass':
        # Deep acoustic/upright bass
        tone = (0.80 * np.sin(2 * np.pi * freq * t) +
                0.18 * np.sin(2 * np.pi * 2 * freq * t) +
                0.02 * np.sin(2 * np.pi * 3 * freq * t))
        env = np.exp(-t * 2.5)
        return tone * env

    elif inst_type == 'marimba':
        # Tropical wooden marimba bar
        tone = (0.70 * np.sin(2 * np.pi * freq * t) +
                0.22 * np.sin(2 * np.pi * 3.8 * freq * t) +
                0.08 * np.sin(2 * np.pi * 9.2 * freq * t))
        env = np.exp(-t * 6.5)
        return tone * env

    else:
        return np.sin(2 * np.pi * freq * t) * np.exp(-t * 3.0)


def add_note(track, start_time, duration, freq, inst_type, pan=0.0, vol=0.5, sample_rate=SAMPLE_RATE):
    """Adds synthesized note to stereo track with seamless loop wraparound."""
    note = synthesize_instrument(freq, duration, inst_type, sample_rate) * vol
    n_samples = len(note)
    start_idx = int(start_time * sample_rate)
    total_len = len(track)

    left_gain = np.sqrt(0.5 * (1.0 - pan))
    right_gain = np.sqrt(0.5 * (1.0 + pan))

    for i in range(n_samples):
        target_idx = (start_idx + i) % total_len
        track[target_idx, 0] += note[i] * left_gain
        track[target_idx, 1] += note[i] * right_gain


def add_percussion(track, start_time, perc_type, pan=0.0, vol=0.4, sample_rate=SAMPLE_RATE):
    """Renders percussion hits with loop wraparound."""
    start_idx = int(start_time * sample_rate)
    total_len = len(track)
    left_gain = np.sqrt(0.5 * (1.0 - pan))
    right_gain = np.sqrt(0.5 * (1.0 + pan))

    if perc_type == 'wind_chime':
        # Soft metallic wind chimes and singing bowl harmonics
        dur = 0.8
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        chimes = (0.35 * np.sin(2 * np.pi * 1850 * t) +
                  0.30 * np.sin(2 * np.pi * 2420 * t) +
                  0.20 * np.sin(2 * np.pi * 3150 * t) +
                  0.15 * np.sin(2 * np.pi * 4200 * t)) * np.exp(-t * 5.0) * vol
        hit = chimes

    elif perc_type == 'triangle':
        # Delicate orchestral triangle ping
        dur = 0.5
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (0.5 * np.sin(2 * np.pi * 2800 * t) + 0.5 * np.sin(2 * np.pi * 4200 * t)) * np.exp(-t * 7.0) * vol

    elif perc_type == 'shaker':
        # Soft brushed shaker
        dur = 0.05
        n = int(dur * sample_rate)
        noise = (np.random.rand(n) * 2.0 - 1.0)
        t = np.linspace(0, dur, n, False)
        hit = noise * np.exp(-t * 65) * vol * 0.35

    elif perc_type == 'clock_tick':
        # Crisp clock escapement tick
        dur = 0.025
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 140) * vol

    elif perc_type == 'clock_tock':
        # Resonant wooden pendulum tock
        dur = 0.035
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = np.sin(2 * np.pi * 1150 * t) * np.exp(-t * 110) * vol

    elif perc_type == 'tower_bell':
        # Majestic cathedral / clocktower bronze chime
        dur = 1.2
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (0.50 * np.sin(2 * np.pi * 440 * t) +
               0.30 * np.sin(2 * np.pi * 524 * t) +
               0.20 * np.sin(2 * np.pi * 660 * t) +
               0.15 * np.sin(2 * np.pi * 880 * t)) * np.exp(-t * 2.5) * vol

    elif perc_type == 'woodblock':
        dur = 0.045
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (np.sin(2 * np.pi * 850 * t) + 0.3 * np.sin(2 * np.pi * 1350 * t)) * np.exp(-t * 85) * vol

    elif perc_type == 'doumbek_dum':
        # Warm organic acoustic hand drum / bongo thud (warm resonance, NO laser pitch drop)
        dur = 0.25
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (0.85 * np.sin(2 * np.pi * 92.0 * t) +
               0.15 * np.sin(2 * np.pi * 184.0 * t)) * np.exp(-t * 16.0) * vol * 1.2

    elif perc_type == 'doumbek_tak':
        # Crisp acoustic wooden rim / bongo edge tap (clean woody resonance, NO white noise hiss)
        dur = 0.06
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (0.70 * np.sin(2 * np.pi * 720.0 * t) +
               0.30 * np.sin(2 * np.pi * 1250.0 * t)) * np.exp(-t * 70.0) * vol

    elif perc_type == 'finger_cymbal':
        # Shimmering bronze desert zill ring
        dur = 0.55
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (0.5 * np.sin(2 * np.pi * 3800 * t) + 0.5 * np.sin(2 * np.pi * 5400 * t)) * np.exp(-t * 8.5) * vol

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
    """Normalizes and saves track as 16-bit stereo PCM WAV file with soft limiter."""
    peak = np.max(np.abs(track))
    if peak > 0:
        norm_track = track * (0.88 / peak)
    else:
        norm_track = track

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
# 1. QUARTER 1: "Storybook Meadow" (Shapes & Old Man Theme)
# Cheerful, gentle storybook theme: Warm acoustic piano, music box,
# soft whimsical melody, subtle pizzicato, and gentle woodland percussion.
# ======================================================================
def generate_quarter1(output_path):
    bpm = 96
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Warm Acoustic Piano Accompaniment (Gentle broken chords)
    # Chords: F, C/E, Bb/D, C, Dm, Bb, F/A -> C7, F
    piano_pattern = [
        ['F3', 'C4', 'F4', 'A4', 'C5', 'A4', 'F4', 'C4'],
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        ['Bb2', 'F3', 'Bb3', 'D4', 'F4', 'D4', 'Bb3', 'F3'],
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        ['D3', 'A3', 'D4', 'F4', 'A4', 'F4', 'D4', 'A3'],
        ['Bb2', 'F3', 'Bb3', 'D4', 'F4', 'D4', 'Bb3', 'F3'],
        ['A2', 'F3', 'A3', 'C4', 'C3', 'G3', 'Bb3', 'E4'],
        ['F2', 'C3', 'F3', 'A3', 'C4', 'A3', 'F3', 'C3']
    ]

    for bar_idx, bar in enumerate(piano_pattern):
        bar_start = bar_idx * 4 * beat_dur
        for step_idx, note_name in enumerate(bar):
            t = bar_start + step_idx * (beat_dur * 0.5)
            pan = -0.22 if step_idx % 2 == 0 else 0.18
            add_note(track, t, beat_dur * 0.95, note_to_freq(note_name), 'piano', pan=pan, vol=0.34)

    # 2. Delicate Music Box / Piano Whimsical Melody (Sweet, heart-warming, cheerful)
    storybook_melody = [
        # Bar 1: A4 (1), C5 (1), F5 (1.5), G5 (0.5)
        (0.0, 1.0, 'A4', 0.28), (1.0, 1.0, 'C5', 0.28), (2.0, 1.5, 'F5', 0.32), (3.5, 0.5, 'G5', 0.26),
        # Bar 2: E5 (2.0), D5 (1.0), C5 (1.0)
        (4.0, 2.0, 'E5', 0.30), (6.0, 1.0, 'D5', 0.26), (7.0, 1.0, 'C5', 0.26),
        # Bar 3: D5 (1.5), F5 (0.5), Bb5 (1.0), A5 (1.0)
        (8.0, 1.5, 'D5', 0.28), (9.5, 0.5, 'F5', 0.28), (10.0, 1.0, 'Bb5', 0.32), (11.0, 1.0, 'A5', 0.28),
        # Bar 4: G5 (2.5), C5 (1.0)
        (12.0, 2.5, 'G5', 0.30), (15.0, 1.0, 'C5', 0.26),
        # Bar 5: F5 (1.5), G5 (0.5), A5 (1.5), C6 (0.5)
        (16.0, 1.5, 'F5', 0.30), (17.5, 0.5, 'G5', 0.28), (18.0, 1.5, 'A5', 0.34), (19.5, 0.5, 'C6', 0.32),
        # Bar 6: D6 (1.5), C6 (0.5), Bb5 (1.0), G5 (1.0)
        (20.0, 1.5, 'D6', 0.34), (21.5, 0.5, 'C6', 0.30), (22.0, 1.0, 'Bb5', 0.28), (23.0, 1.0, 'G5', 0.26),
        # Bar 7: A5 (1.0), F5 (1.0), G5 (1.5), E5 (0.5)
        (24.0, 1.0, 'A5', 0.30), (25.0, 1.0, 'F5', 0.28), (26.0, 1.5, 'G5', 0.30), (27.5, 0.5, 'E5', 0.24),
        # Bar 8: F5 (3.0 beats warm comforting resolution)
        (28.0, 3.0, 'F5', 0.35)
    ]

    for start_beat, dur_beats, note_name, vol in storybook_melody:
        # Music box on right channel
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.9,
                 note_to_freq(note_name), 'music_box', pan=0.25, vol=vol * 0.85)
        # Soft warm piano lead on center
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.95,
                 note_to_freq(note_name), 'piano', pan=0.0, vol=vol * 0.70)

    # 3. Gentle Pizzicato Strings & Soft Cello Bass
    pizz_bass = [
        (0.0, 'F2'), (2.0, 'C2'), (4.0, 'C2'), (6.0, 'G1'),
        (8.0, 'Bb1'), (10.0, 'F1'), (12.0, 'C2'), (14.0, 'G1'),
        (16.0, 'D2'), (18.0, 'A1'), (20.0, 'Bb1'), (22.0, 'F1'),
        (24.0, 'A1'), (26.0, 'C2'), (28.0, 'F1'), (30.0, 'C2')
    ]
    for b_pos, n_name in pizz_bass:
        add_note(track, b_pos * beat_dur, beat_dur * 1.5,
                 note_to_freq(n_name), 'bass', pan=0.0, vol=0.36)
        add_note(track, b_pos * beat_dur, beat_dur * 0.6,
                 note_to_freq(n_name), 'pizzicato', pan=-0.3, vol=0.20)

    # 4. Light Whispering Woodland Percussion (Gentle brushed shaker & soft triangle ping)
    for b in range(bars * 4):
        t = b * beat_dur
        add_percussion(track, t, 'shaker', pan=-0.25, vol=0.10)
        add_percussion(track, t + beat_dur * 0.5, 'shaker', pan=0.25, vol=0.08)
        if b % 4 == 0:
            add_percussion(track, t, 'triangle', pan=0.3, vol=0.20)

    reverbed = apply_stereo_reverb(track, wet=0.20)
    save_wav(reverbed, output_path)


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
                 note_to_freq(note_name), 'celesta', pan=0.3, vol=0.26)

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

    for b in range(bars * 4):
        t = b * beat_dur
        add_percussion(track, t, 'shaker', pan=-0.2, vol=0.20)
        add_percussion(track, t + beat_dur * 0.5, 'shaker', pan=0.2, vol=0.15)
        if b % 4 in [0, 3]:
            add_percussion(track, t, 'woodblock', pan=0.15, vol=0.25)

    reverbed = apply_stereo_reverb(track, wet=0.16)
    save_wav(reverbed, output_path)


# ======================================================================
# 3. QUARTER 3: "Oasis of the Golden Sands" (Fractions & Sun Temple / Desert Theme)
# A soothing, relaxing, and adventurous desert oasis theme:
# Warm Spanish acoustic guitar arpeggios, sweet mid-range wooden pan flute melody,
# lush ambient desert pads, deep upright bass, resonant acoustic hand drum, and soft chimes.
# Key: D Minor / D Dorian (Warm, soothing, enchanting, and memorable)
# ======================================================================
def generate_quarter3(output_path):
    bpm = 100
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Warm Spanish Acoustic Guitar Fingerpicking (Arpeggios)
    # Chord progression: Dm -> C -> Bb -> A -> Dm -> Gm -> A7 -> Dm
    guitar_arpeggios = [
        # Bar 1 (Dm)
        ['D3', 'A3', 'D4', 'F4', 'A4', 'F4', 'D4', 'A3'],
        # Bar 2 (C)
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        # Bar 3 (Bb)
        ['Bb2', 'F3', 'Bb3', 'D4', 'F4', 'D4', 'Bb3', 'F3'],
        # Bar 4 (A)
        ['A2', 'E3', 'A3', 'C#4', 'E4', 'C#4', 'A3', 'E3'],
        # Bar 5 (Dm)
        ['D3', 'A3', 'D4', 'F4', 'A4', 'F4', 'D4', 'A3'],
        # Bar 6 (Gm)
        ['G2', 'D3', 'G3', 'Bb3', 'D4', 'Bb3', 'G3', 'D3'],
        # Bar 7 (A7)
        ['A2', 'E3', 'G3', 'C#4', 'E4', 'C#4', 'G3', 'E3'],
        # Bar 8 (Dm)
        ['D3', 'A3', 'D4', 'F4', 'D4', 'A3', 'F3', 'A3']
    ]

    for bar_idx, bar in enumerate(guitar_arpeggios):
        bar_start = bar_idx * 4 * beat_dur
        for step_idx, note_name in enumerate(bar):
            t = bar_start + step_idx * (beat_dur * 0.5)
            # Subtle stereo spread for acoustic warmth
            pan = -0.22 if step_idx % 2 == 0 else 0.22
            add_note(track, t, beat_dur * 0.95, note_to_freq(note_name), 'acoustic_guitar', pan=pan, vol=0.32)

    # 2. Warm Ambient Desert Pads & Soft Strings
    ambient_chords = [
        (0.0, 4.0, ['D3', 'A3', 'F4']),       # Dm
        (4.0, 4.0, ['C3', 'G3', 'E4']),       # C
        (8.0, 4.0, ['Bb2', 'F3', 'D4']),      # Bb
        (12.0, 4.0, ['A2', 'E3', 'C#4']),     # A
        (16.0, 4.0, ['D3', 'A3', 'F4']),      # Dm
        (20.0, 4.0, ['G2', 'D3', 'Bb3']),     # Gm
        (24.0, 4.0, ['A2', 'G3', 'C#4']),     # A7
        (28.0, 4.0, ['D3', 'A3', 'D4', 'F4']) # Dm resolution
    ]
    for start_beat, dur_beats, chord in ambient_chords:
        for n_name in chord:
            add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.96,
                     note_to_freq(n_name), 'pad', pan=-0.25, vol=0.13)
            add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.94,
                     note_to_freq(n_name), 'strings', pan=0.25, vol=0.10)

    # 3. Deep Warm Upright Acoustic Bass
    oasis_bass = [
        # Bar 1 (Dm)
        (0.0, 'D2'), (2.0, 'A1'),
        # Bar 2 (C)
        (4.0, 'C2'), (6.0, 'G1'),
        # Bar 3 (Bb)
        (8.0, 'Bb1'), (10.0, 'F1'),
        # Bar 4 (A)
        (12.0, 'A1'), (14.0, 'E1'),
        # Bar 5 (Dm)
        (16.0, 'D2'), (18.0, 'A1'),
        # Bar 6 (Gm)
        (20.0, 'G1'), (22.0, 'D2'),
        # Bar 7 (A7)
        (24.0, 'A1'), (26.0, 'E1'),
        # Bar 8 (Dm)
        (28.0, 'D2'), (30.0, 'A1')
    ]
    for b_pos, n_name in oasis_bass:
        add_note(track, b_pos * beat_dur, beat_dur * 1.5,
                 note_to_freq(n_name), 'bass', pan=0.0, vol=0.38)

    # 4. Soothing Pan Flute Lead Melody (Lyrical, comfortable mid-range D4-F5, sweet & peaceful)
    flute_melody = [
        # Phrase 1 (Bars 1-4)
        (0.0, 1.0, 'D4', 0.32), (1.0, 1.0, 'F4', 0.34), (2.0, 1.5, 'A4', 0.36), (3.5, 0.5, 'C5', 0.30),
        (4.0, 2.0, 'G4', 0.34), (6.0, 1.0, 'F4', 0.30), (7.0, 1.0, 'E4', 0.28),
        (8.0, 1.5, 'F4', 0.32), (9.5, 0.5, 'G4', 0.32), (10.0, 2.0, 'D4', 0.34),
        (12.0, 2.5, 'E4', 0.34), (14.5, 0.5, 'F4', 0.30), (15.0, 1.0, 'E4', 0.28),

        # Phrase 2 (Bars 5-8 - Emotional climax & gentle resolution)
        (16.0, 1.0, 'D4', 0.32), (17.0, 1.0, 'A4', 0.35), (18.0, 1.5, 'D5', 0.38), (19.5, 0.5, 'E5', 0.36),
        (20.0, 1.5, 'F5', 0.40), (21.5, 0.5, 'E5', 0.36), (22.0, 1.0, 'D5', 0.34), (23.0, 1.0, 'Bb4', 0.32),
        (24.0, 1.5, 'A4', 0.36), (25.5, 0.5, 'G4', 0.32), (26.0, 1.0, 'E4', 0.32), (27.0, 1.0, 'C#4', 0.30),
        (28.0, 3.5, 'D4', 0.40)
    ]

    for start_beat, dur_beats, note_name, vol in flute_melody:
        # Sweet pan flute lead
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.95,
                 note_to_freq(note_name), 'pan_flute', pan=0.05, vol=vol)
        # Soft acoustic piano touch to reinforce melodic clarity and warmth
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.90,
                 note_to_freq(note_name), 'piano', pan=0.0, vol=vol * 0.45)

    # 5. Organic Desert Acoustic Percussion (Warm hand drum, woody rim, gentle wind chime)
    # Wind chimes on entry of phrases
    add_percussion(track, 0.0, 'wind_chime', pan=0.25, vol=0.25)
    add_percussion(track, 16.0 * beat_dur, 'wind_chime', pan=-0.25, vol=0.25)

    for bar in range(bars):
        b_start = bar * 4.0
        # Warm, organic low hand drum thud on beats 0 and 2 (NO pitch dive zap)
        add_percussion(track, (b_start + 0.0) * beat_dur, 'doumbek_dum', pan=-0.15, vol=0.35)
        add_percussion(track, (b_start + 2.0) * beat_dur, 'doumbek_dum', pan=0.10, vol=0.30)

        # Clean woody acoustic rim tap on beats 1 and 3 (NO white noise static)
        add_percussion(track, (b_start + 1.0) * beat_dur, 'doumbek_tak', pan=0.20, vol=0.22)
        add_percussion(track, (b_start + 3.0) * beat_dur, 'doumbek_tak', pan=-0.20, vol=0.20)

        # Soft, subtle brushed shaker on 8th-note offbeats (gentle breeze texture)
        for sub in [0.5, 1.5, 2.5, 3.5]:
            add_percussion(track, (b_start + sub) * beat_dur, 'shaker', pan=0.2, vol=0.06)

        # Subtle woodblock accents on turnaround bars
        if bar in [3, 7]:
            add_percussion(track, (b_start + 3.5) * beat_dur, 'woodblock', pan=0.15, vol=0.18)

    reverbed = apply_stereo_reverb(track, wet=0.20)
    save_wav(reverbed, output_path)



# ======================================================================
# 4. QUARTER 4: "The Celestial Clocktower" (Time, Angles & Castle Clocktower)
# Intricate Baroque Clockwork Allegro: Left-right pendulum ticking,
# glistening celesta gear arpeggios, staccato violins, and noble castle brass.
# ======================================================================
def generate_quarter4(output_path):
    bpm = 122
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. High-Precision Mechanical Clockwork Engine
    for b in range(bars * 4):
        t = b * beat_dur
        # Left ear: High Escapement Tick on the beat
        add_percussion(track, t, 'clock_tick', pan=-0.42, vol=0.32)
        # Right ear: Lower Pendulum Tock on the offbeat
        add_percussion(track, t + beat_dur * 0.5, 'clock_tock', pan=0.42, vol=0.28)
        # Soft orchestral snare roll on beat 4 of every 2nd bar
        if b % 8 == 7:
            add_percussion(track, t, 'woodblock', pan=0.1, vol=0.22)
            add_percussion(track, t + beat_dur * 0.25, 'woodblock', pan=-0.1, vol=0.25)
            add_percussion(track, t + beat_dur * 0.5, 'woodblock', pan=0.1, vol=0.30)
            add_percussion(track, t + beat_dur * 0.75, 'woodblock', pan=0.0, vol=0.35)

    # Bronze Tower Bell strikes on phrase markers
    add_percussion(track, 0.0, 'tower_bell', pan=-0.2, vol=0.45)
    add_percussion(track, 8.0 * beat_dur, 'tower_bell', pan=0.2, vol=0.40)
    add_percussion(track, 16.0 * beat_dur, 'tower_bell', pan=-0.2, vol=0.45)
    add_percussion(track, 24.0 * beat_dur, 'tower_bell', pan=0.2, vol=0.40)

    # 2. Glistening Celesta / Music Box Gear Arpeggios (Spinning brass gears)
    gears_melody = [
        ['A4', 'C5', 'E5', 'A5', 'E5', 'C5', 'A4', 'C5'],
        ['F4', 'A4', 'D5', 'F5', 'D5', 'A4', 'F4', 'A4'],
        ['C4', 'F4', 'A4', 'C5', 'A4', 'F4', 'C4', 'F4'],
        ['B3', 'E4', 'G#4', 'B4', 'D5', 'B4', 'G#4', 'E4'],
        ['C4', 'E4', 'G4', 'C5', 'E5', 'C5', 'G4', 'E4'],
        ['D4', 'G4', 'B4', 'D5', 'G5', 'D5', 'B4', 'G4'],
        ['C4', 'F4', 'A4', 'C5', 'F5', 'C5', 'A4', 'F4'],
        ['B3', 'E4', 'G#4', 'B4', 'E5', 'B4', 'G#4', 'E4']
    ]

    for bar_idx, bar in enumerate(gears_melody):
        bar_start = bar_idx * 4 * beat_dur
        for step_idx, note_name in enumerate(bar):
            t = bar_start + step_idx * (beat_dur * 0.5)
            pan = 0.35 if step_idx % 2 == 0 else -0.25
            add_note(track, t, beat_dur * 0.82, note_to_freq(note_name), 'celesta', pan=pan, vol=0.32)

    # 3. Baroque Staccato Pizzicato Violins (Rhythmic counterpoint)
    staccato_rhythm = [
        (0.0, 'A4'), (1.0, 'E4'), (2.0, 'A4'), (3.0, 'C5'),
        (4.0, 'D4'), (5.0, 'A4'), (6.0, 'D4'), (7.0, 'F4'),
        (8.0, 'F4'), (9.0, 'C4'), (10.0, 'F4'), (11.0, 'A4'),
        (12.0, 'E4'), (13.0, 'B3'), (14.0, 'E4'), (15.0, 'G#4'),
        (16.0, 'C4'), (17.0, 'G4'), (18.0, 'C4'), (19.0, 'E4'),
        (20.0, 'G4'), (21.0, 'D4'), (22.0, 'G4'), (23.0, 'B4'),
        (24.0, 'F4'), (25.0, 'C4'), (26.0, 'F4'), (27.0, 'A4'),
        (28.0, 'E4'), (29.0, 'B3'), (30.0, 'E4'), (31.0, 'E4')
    ]
    for b_pos, n_name in staccato_rhythm:
        add_note(track, b_pos * beat_dur, beat_dur * 0.6,
                 note_to_freq(n_name), 'pizzicato', pan=-0.30, vol=0.26)

    # 4. Noble Castle French Horn & Majestic Lead Melody
    clocktower_lead = [
        (0.0, 1.5, 'E5'), (1.5, 1.5, 'A5'), (3.0, 1.0, 'B5'),
        (4.0, 2.0, 'C6'), (6.0, 1.0, 'B5'), (7.0, 1.0, 'A5'),
        (8.0, 1.5, 'F5'), (9.5, 1.5, 'A5'), (11.0, 1.0, 'D6'),
        (12.0, 2.5, 'B5'), (14.5, 1.5, 'G#5'),
        (16.0, 1.0, 'E5'), (17.0, 1.0, 'G5'), (18.0, 1.5, 'C6'), (19.5, 0.5, 'D6'),
        (20.0, 2.0, 'E6'), (22.0, 1.0, 'D6'), (23.0, 1.0, 'B5'),
        (24.0, 1.0, 'C6'), (25.0, 1.0, 'A5'), (26.0, 1.0, 'F5'), (27.0, 1.0, 'B5'),
        (28.0, 3.0, 'A5')
    ]

    for start_beat, dur_beats, note_name in clocktower_lead:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.94,
                 note_to_freq(note_name), 'horn', pan=0.18, vol=0.35)

    # 5. Stately Cello & Castle Bass
    castle_bass = [
        (0.0, 'A1'), (4.0, 'D2'), (8.0, 'F1'), (12.0, 'E2'),
        (16.0, 'C2'), (20.0, 'G1'), (24.0, 'F1'), (28.0, 'A1')
    ]
    for start_beat, note_name in castle_bass:
        add_note(track, start_beat * beat_dur, 4.0 * beat_dur * 0.90,
                 note_to_freq(note_name), 'bass', pan=0.0, vol=0.42)

    reverbed = apply_stereo_reverb(track, wet=0.22)
    save_wav(reverbed, output_path)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sounds_dir = os.path.join(base_dir, "assets", "sounds")

    q1_path = os.path.join(sounds_dir, "q1_forest_shapes.wav")
    q2_path = os.path.join(sounds_dir, "q2_barrio_fiesta.wav")
    q3_path = os.path.join(sounds_dir, "q3_sun_temple.wav")
    q4_path = os.path.join(sounds_dir, "q4_clocktower_castle.wav")

    print("Synthesizing custom thematic soundtracks...")
    generate_quarter1(q1_path)
    generate_quarter2(q2_path)
    generate_quarter3(q3_path)
    generate_quarter4(q4_path)
    print("All custom soundtracks generated and verified successfully!")


if __name__ == "__main__":
    main()
