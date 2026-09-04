# assets/sounds/generate_theme_music.py
"""
High-Fidelity Thematic Background Music Synthesizer for Cognitive Quest Quarters:
- Quarter 1 (Shapes & Medieval Forest): q1_forest_shapes.wav
  * Whimsical Celtic/Zelda-style adventure with acoustic folk harp, playful whistle, pizzicato strings, and woodland percussion.
- Quarter 2 (Division & Philippine Barrio Fiesta): q2_barrio_fiesta.wav
  * Upbeat tropical celebration with bouncy marimba/kulintang, fiesta clave, and Latin tumbao bass.
- Quarter 3 (Fractions & Ancient Sun Temple): q3_sun_temple.wav
  * Exhilarating Middle Eastern desert action with authentic Darbuka Maqsum groove, acoustic Oud/Kanun, and soaring Egyptian Ney flute.
- Quarter 4 (Time, Angles & Castle Clocktower): q4_clocktower_castle.wav
  * Intricate Baroque Clockwork Allegro with dual-ear pendulum ticking, glistening music box/celesta gear runs, and noble castle French horns.

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


def synthesize_instrument(freq, duration, inst_type='flute', sample_rate=SAMPLE_RATE):
    """
    Synthesizes rich acoustic and fantasy instrument timbres:
    - fm_pluck (acoustic guitar / folk harp / lute)
    - whistle (Celtic tin whistle / wooden recorder)
    - celesta (crystal-clear music box / gear chimes)
    - strings (lush detuned string ensemble)
    - pizzicato (snappy orchestral string pluck)
    - oud (snappy Middle Eastern acoustic lute with characteristic snap)
    - ney (haunting Middle Eastern desert reed flute)
    - horn (majestic noble French horn / castle brass)
    - bass (warm upright / sub-bass)
    - marimba (woody tropical mallet)
    """
    n_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, n_samples, False)

    if inst_type == 'fm_pluck':
        # Organic acoustic guitar / folk harp using Chowning FM synthesis
        decay_rate = 3.5 + (freq / 350.0)
        mod_env = np.exp(-t * 9.0)
        amp_env = np.exp(-t * decay_rate)
        # Dynamic modulation gives string transient that mellows into warm resonance
        mod = 2.8 * mod_env * np.sin(2 * np.pi * freq * t)
        tone = (0.75 * np.sin(2 * np.pi * freq * t + mod) +
                0.20 * np.sin(2 * np.pi * 2 * freq * t) +
                0.05 * np.sin(2 * np.pi * 3 * freq * t))
        return tone * amp_env

    elif inst_type == 'whistle' or inst_type == 'flute':
        # Celtic tin whistle / wooden recorder: soft attack, subtle breath chiff, expressive vibrato
        vib_delay = int(sample_rate * 0.05)
        vib_ramp = np.ones(n_samples)
        if vib_delay < n_samples:
            vib_ramp[:vib_delay] = np.linspace(0.0, 1.0, vib_delay)
        vibrato = 1.0 + 0.014 * vib_ramp * np.sin(2 * np.pi * 5.6 * t)
        phase = 2 * np.pi * freq * vibrato * t
        
        # Fundamental with gentle 2nd and 3rd harmonics + breath
        tone = (0.78 * np.sin(phase) +
                0.18 * np.sin(2 * phase) +
                0.04 * np.sin(3 * phase))
        
        # Soft envelope
        att_s = min(int(sample_rate * 0.035), n_samples // 4)
        rel_s = min(int(sample_rate * 0.06), n_samples // 4)
        env = np.ones(n_samples)
        if att_s > 0:
            env[:att_s] = np.linspace(0.0, 1.0, att_s)
        if rel_s > 0:
            env[-rel_s:] = np.linspace(1.0, 0.0, rel_s)
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
        env = np.exp(-t * 12.0) # Fast staccato decay
        return tone * env

    elif inst_type == 'strings':
        # Lush detuned string ensemble (chorus warmth)
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

    elif inst_type == 'oud':
        # Middle Eastern acoustic lute / Oud: snappy attack, slight bend, dry resonant body
        mod_oud = 3.2 * np.exp(-t * 12.0) * np.sin(2 * np.pi * freq * t)
        tone = (0.65 * np.sin(2 * np.pi * freq * t + mod_oud) +
                0.22 * np.sin(2 * np.pi * 2 * freq * t) +
                0.13 * np.sin(2 * np.pi * 3 * freq * t))
        env = np.exp(-t * 5.2)
        return tone * env

    elif inst_type == 'ney':
        # Ancient Middle Eastern desert reed flute: smoky vibrato, harmonic overtones
        vib = 1.0 + 0.016 * np.sin(2 * np.pi * 5.2 * t)
        ph = 2 * np.pi * freq * vib * t
        tone = (0.68 * np.sin(ph) +
                0.22 * np.sin(2 * ph) +
                0.10 * np.sin(3 * ph))
        att_s = min(int(sample_rate * 0.04), n_samples // 4)
        rel_s = min(int(sample_rate * 0.07), n_samples // 4)
        env = np.ones(n_samples)
        if att_s > 0:
            env[:att_s] = np.linspace(0.0, 1.0, att_s)
        if rel_s > 0:
            env[-rel_s:] = np.linspace(1.0, 0.0, rel_s)
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
    """Renders high-quality percussion hits with loop wraparound."""
    start_idx = int(start_time * sample_rate)
    total_len = len(track)
    left_gain = np.sqrt(0.5 * (1.0 - pan))
    right_gain = np.sqrt(0.5 * (1.0 + pan))

    if perc_type == 'darbuka_dum':
        # Authentic Middle Eastern deep resonant drum thump
        dur = 0.22
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        pitch = 140 * np.exp(-t * 16) + 55
        hit = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 14) * (vol * 1.2)

    elif perc_type == 'darbuka_tek':
        # Sharp Middle Eastern rim click
        dur = 0.05
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (np.sin(2 * np.pi * 2400 * t) * 0.7 + np.sin(2 * np.pi * 900 * t) * 0.3) * np.exp(-t * 90) * vol

    elif perc_type == 'tambourine':
        # Shimmering brass jingle
        dur = 0.09
        n = int(dur * sample_rate)
        noise = (np.random.rand(n) * 2.0 - 1.0)
        t = np.linspace(0, dur, n, False)
        jingle = (np.sin(2 * np.pi * 4800 * t) + np.sin(2 * np.pi * 7200 * t)) * 0.4
        hit = (noise * 0.6 + jingle) * np.exp(-t * 38) * vol

    elif perc_type == 'folk_kick':
        # Soft acoustic bass drum
        dur = 0.18
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        pitch = 110 * np.exp(-t * 22) + 48
        hit = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 18) * vol

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
               0.30 * np.sin(2 * np.pi * 524 * t) + # minor 3rd
               0.20 * np.sin(2 * np.pi * 660 * t) +
               0.15 * np.sin(2 * np.pi * 880 * t)) * np.exp(-t * 2.5) * vol

    elif perc_type == 'gong':
        # Exotic golden temple chime / gong
        dur = 1.5
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (0.45 * np.sin(2 * np.pi * 293.66 * t) + # D4
               0.30 * np.sin(2 * np.pi * 370 * t) +    # F#4
               0.25 * np.sin(2 * np.pi * 587.33 * t) + # D5
               0.15 * np.sin(2 * np.pi * 880 * t)) * np.exp(-t * 2.0) * vol

    elif perc_type == 'shaker':
        dur = 0.06
        n = int(dur * sample_rate)
        noise = (np.random.rand(n) * 2.0 - 1.0)
        t = np.linspace(0, dur, n, False)
        hit = noise * np.exp(-t * 55) * vol * 0.4

    elif perc_type == 'woodblock':
        dur = 0.045
        n = int(dur * sample_rate)
        t = np.linspace(0, dur, n, False)
        hit = (np.sin(2 * np.pi * 850 * t) + 0.3 * np.sin(2 * np.pi * 1350 * t)) * np.exp(-t * 85) * vol

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
# 1. QUARTER 1: "The Whispering Forest" (Shapes & Old Man Theme)
# Whimsical Celtic/Zelda Folk Adventure: Acoustic guitar arpeggios,
# playful tin whistle melody, pizzicato strings, and woodland percussion.
# ======================================================================
def generate_quarter1(output_path):
    bpm = 116
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Cascading Acoustic Guitar / Folk Harp Fingerpicking Arpeggios
    # Chords: G, C, D, G, Em, C, Am, D7
    chords_folk = [
        ['G3', 'D4', 'G4', 'B4', 'D5', 'B4', 'G4', 'D4'],
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        ['D3', 'A3', 'D4', 'F#4', 'A4', 'F#4', 'D4', 'A3'],
        ['G3', 'D4', 'G4', 'B4', 'D5', 'B4', 'G4', 'D4'],
        ['E3', 'B3', 'E4', 'G4', 'B4', 'G4', 'E4', 'B3'],
        ['C3', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3'],
        ['A2', 'E3', 'A3', 'C4', 'E4', 'C4', 'A3', 'E3'],
        ['D3', 'A3', 'C4', 'F#4', 'A4', 'F#4', 'D4', 'A3']
    ]

    for bar_idx, bar in enumerate(chords_folk):
        bar_start = bar_idx * 4 * beat_dur
        for step_idx, note_name in enumerate(bar):
            t = bar_start + step_idx * (beat_dur * 0.5)
            # Alternating stereo pan for wide acoustic guitar feel
            pan = -0.38 if step_idx % 2 == 0 else 0.28
            add_note(track, t, beat_dur * 0.95, note_to_freq(note_name), 'fm_pluck', pan=pan, vol=0.34)

    # 2. Playful Celtic Tin Whistle Lead Melody (Catchy & Memorable!)
    whistle_melody = [
        # Bar 1: D5 (1 beat), G5 (1 beat), A5 (0.5), B5 (1.5)
        (0.0, 1.0, 'D5', 0.28), (1.0, 1.0, 'G5', 0.30), (2.0, 0.5, 'A5', 0.26), (2.5, 1.5, 'B5', 0.32),
        # Bar 2: C6 (1 beat), B5 (0.5), A5 (0.5), G5 (1.5), E5 (0.5)
        (4.0, 1.0, 'C6', 0.30), (5.0, 0.5, 'B5', 0.28), (5.5, 0.5, 'A5', 0.26), (6.0, 1.5, 'G5', 0.30), (7.5, 0.5, 'E5', 0.24),
        # Bar 3: A5 (1.5), B5 (0.5), A5 (1.0), F#5 (1.0)
        (8.0, 1.5, 'A5', 0.28), (9.5, 0.5, 'B5', 0.26), (10.0, 1.0, 'A5', 0.28), (11.0, 1.0, 'F#5', 0.26),
        # Bar 4: G5 (2.5), D5 (1.0)
        (12.0, 2.5, 'G5', 0.32), (15.0, 1.0, 'D5', 0.26),
        # Bar 5 (Climb): B5 (1.5), C6 (0.5), D6 (1.5), B5 (0.5)
        (16.0, 1.5, 'B5', 0.32), (17.5, 0.5, 'C6', 0.30), (18.0, 1.5, 'D6', 0.36), (19.5, 0.5, 'B5', 0.30),
        # Bar 6: C6 (1.0), E6 (1.0), D6 (1.5), B5 (0.5)
        (20.0, 1.0, 'C6', 0.32), (21.0, 1.0, 'E6', 0.35), (22.0, 1.5, 'D6', 0.34), (23.5, 0.5, 'B5', 0.28),
        # Bar 7: A5 (1.0), B5 (0.5), C6 (0.5), B5 (1.0), A5 (1.0)
        (24.0, 1.0, 'A5', 0.30), (25.0, 0.5, 'B5', 0.28), (25.5, 0.5, 'C6', 0.30), (26.0, 1.0, 'B5', 0.28), (27.0, 1.0, 'A5', 0.28),
        # Bar 8: G5 (3.0 beats warm sustained resolution)
        (28.0, 3.0, 'G5', 0.34)
    ]

    for start_beat, dur_beats, note_name, vol in whistle_melody:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.96,
                 note_to_freq(note_name), 'whistle', pan=0.15, vol=vol)

    # 3. Whimsical Pizzicato Strings Countermelody (Storybook charm)
    pizz_riffs = [
        (3.0, 'D5'), (3.5, 'G5'), (7.0, 'B5'), (7.5, 'G5'),
        (11.0, 'D5'), (11.5, 'F#5'), (15.0, 'B5'), (15.5, 'G5'),
        (19.0, 'D5'), (19.5, 'B5'), (23.0, 'G5'), (23.5, 'E5'),
        (27.0, 'F#5'), (27.5, 'D5'), (31.0, 'D5'), (31.5, 'B4')
    ]
    for b_pos, n_name in pizz_riffs:
        add_note(track, b_pos * beat_dur, beat_dur * 0.6,
                 note_to_freq(n_name), 'pizzicato', pan=-0.4, vol=0.28)

    # 4. Warm Bouncy Acoustic Walking Bass
    bass_pattern = [
        (0.0, 'G2'), (1.5, 'D2'), (2.0, 'G2'), (3.0, 'B1'),
        (4.0, 'C2'), (5.5, 'G1'), (6.0, 'C2'), (7.0, 'E2'),
        (8.0, 'D2'), (9.5, 'A1'), (10.0, 'D2'), (11.0, 'F#1'),
        (12.0, 'G2'), (13.5, 'D2'), (14.0, 'G2'), (15.0, 'B1'),
        (16.0, 'E2'), (17.5, 'B1'), (18.0, 'E2'), (19.0, 'G1'),
        (20.0, 'C2'), (21.5, 'G1'), (22.0, 'C2'), (23.0, 'E2'),
        (24.0, 'A1'), (25.5, 'E1'), (26.0, 'A1'), (27.0, 'C2'),
        (28.0, 'D2'), (29.5, 'A1'), (30.0, 'D2'), (31.0, 'G1')
    ]
    for start_beat, note_name in bass_pattern:
        add_note(track, start_beat * beat_dur, beat_dur * 0.85,
                 note_to_freq(note_name), 'bass', pan=0.0, vol=0.40)

    # 5. Woodland Folk Percussion (Soft kick on 1 & 3, Tambourine on 2 & 4)
    for b in range(bars * 4):
        t = b * beat_dur
        # Soft kick on beats 1 and 3
        if b % 2 == 0:
            add_percussion(track, t, 'folk_kick', pan=0.0, vol=0.35)
        # Tambourine jingle on beats 2 and 4
        else:
            add_percussion(track, t, 'tambourine', pan=0.35, vol=0.24)
        # Shaker on 16th offbeats
        add_percussion(track, t + beat_dur * 0.5, 'shaker', pan=-0.25, vol=0.14)
        if b % 4 == 3:
            add_percussion(track, t + beat_dur * 0.75, 'woodblock', pan=0.15, vol=0.18)

    # Apply stereo room reverb
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

    # 1. Festive Marimba / Kulintang Pattern (Bouncy, syncopated Philippine fiesta vibe)
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
                 note_to_freq(note_name), 'celesta', pan=0.3, vol=0.26)

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
        if b % 4 in [0, 3]:
            add_percussion(track, t, 'woodblock', pan=0.15, vol=0.25)

    reverbed = apply_stereo_reverb(track, wet=0.16)
    save_wav(reverbed, output_path)


# ======================================================================
# 3. QUARTER 3: "Sands of the Sun Pharaoh" (Fractions & Sun Temple Theme)
# High-energy Middle Eastern Desert Adventure: Authentic Darbuka Maqsum groove,
# syncopated Oud riffs, hypnotic strings, and soaring Egyptian Ney flute.
# Scale: D Harmonic Minor / Hijaz (D - Eb - F# - G - A - Bb - C)
# ======================================================================
def generate_quarter3(output_path):
    bpm = 120
    beat_dur = 60.0 / bpm
    bars = 8
    total_duration = bars * 4 * beat_dur
    total_samples = int(total_duration * SAMPLE_RATE)
    track = np.zeros((total_samples, 2), dtype=np.float32)

    # 1. Driving Middle Eastern Darbuka / Doumbek Groove (Maqsum / Malfuf)
    for b in range(bars * 4):
        t = b * beat_dur
        # Beat 1: Heavy resonant DUM
        if b % 4 == 0:
            add_percussion(track, t, 'darbuka_dum', pan=0.0, vol=0.55)
        # Beat 2: Sharp rim TAK
        elif b % 4 == 1:
            add_percussion(track, t, 'darbuka_tek', pan=0.25, vol=0.36)
            add_percussion(track, t + beat_dur * 0.5, 'darbuka_tek', pan=-0.25, vol=0.26)
        # Beat 3: Syncopated mid DUM
        elif b % 4 == 2:
            add_percussion(track, t, 'darbuka_dum', pan=0.0, vol=0.45)
        # Beat 4: Sharp rim TAK
        elif b % 4 == 3:
            add_percussion(track, t, 'darbuka_tek', pan=0.25, vol=0.38)

        # Shimmering Egyptian brass tambourine (Riq) pulse on all 16ths
        add_percussion(track, t, 'tambourine', pan=-0.35, vol=0.15)
        add_percussion(track, t + beat_dur * 0.5, 'tambourine', pan=0.35, vol=0.18)

    # Golden Temple Gong accents at phrase starts (Bar 1 and Bar 5)
    add_percussion(track, 0.0, 'gong', pan=0.0, vol=0.50)
    add_percussion(track, 16.0 * beat_dur, 'gong', pan=0.0, vol=0.45)

    # 2. Syncopated Acoustic Oud & Kanun Lute Riff (Driving rhythmic 16ths)
    # D Hijaz chords: Dm, Eb, Dm, Gm, Eb, A7, Dm
    oud_riff = [
        # Bar 1 (D)
        (0.0, 'D3'), (0.5, 'A3'), (1.0, 'D4'), (1.5, 'F#4'), (2.0, 'A4'), (2.5, 'F#4'), (3.0, 'Eb4'), (3.5, 'D4'),
        # Bar 2 (Eb)
        (4.0, 'Eb3'), (4.5, 'Bb3'), (5.0, 'Eb4'), (5.5, 'G4'), (6.0, 'Bb4'), (6.5, 'G4'), (7.0, 'F#4'), (7.5, 'Eb4'),
        # Bar 3 (Dm)
        (8.0, 'D3'), (8.5, 'A3'), (9.0, 'D4'), (9.5, 'F#4'), (10.0, 'A4'), (10.5, 'F#4'), (11.0, 'Eb4'), (11.5, 'D4'),
        # Bar 4 (Gm)
        (12.0, 'G2'), (12.5, 'D3'), (13.0, 'G3'), (13.5, 'Bb3'), (14.0, 'D4'), (14.5, 'Bb3'), (15.0, 'A3'), (15.5, 'G3'),
        # Bar 5 (D)
        (16.0, 'D3'), (16.5, 'A3'), (17.0, 'D4'), (17.5, 'F#4'), (18.0, 'A4'), (18.5, 'F#4'), (19.0, 'Eb4'), (19.5, 'D4'),
        # Bar 6 (Eb)
        (20.0, 'Eb3'), (20.5, 'Bb3'), (21.0, 'Eb4'), (21.5, 'G4'), (22.0, 'Bb4'), (22.5, 'G4'), (23.0, 'F#4'), (23.5, 'Eb4'),
        # Bar 7 (A7)
        (24.0, 'A2'), (24.5, 'E3'), (25.0, 'A3'), (25.5, 'C#4'), (26.0, 'E4'), (26.5, 'C#4'), (27.0, 'Bb3'), (27.5, 'A3'),
        # Bar 8 (Dm resolution)
        (28.0, 'D3'), (28.5, 'A3'), (29.0, 'D4'), (29.5, 'F#4'), (30.0, 'A4'), (30.5, 'D4'), (31.0, 'A3'), (31.5, 'D3')
    ]

    for start_beat, note_name in oud_riff:
        pan = -0.32 if (start_beat % 1.0) == 0 else 0.28
        add_note(track, start_beat * beat_dur, beat_dur * 0.75,
                 note_to_freq(note_name), 'oud', pan=pan, vol=0.35)

    # 3. Hypnotic Desert Strings Ostinato
    strings_chords = [
        (0.0, 4.0, 'D4'), (4.0, 4.0, 'Eb4'), (8.0, 4.0, 'D4'), (12.0, 4.0, 'G4'),
        (16.0, 4.0, 'D4'), (20.0, 4.0, 'Eb4'), (24.0, 4.0, 'C#4'), (28.0, 4.0, 'D4')
    ]
    for b_start, b_len, note_name in strings_chords:
        add_note(track, b_start * beat_dur, b_len * beat_dur * 0.95,
                 note_to_freq(note_name), 'strings', pan=-0.25, vol=0.22)

    # 4. Soaring Egyptian Ney Flute Solo (Thrilling & Exotic!)
    ney_melody = [
        # Bar 1: D5 (1.0), Eb5 (0.5), F#5 (1.5), Eb5 (0.5), D5 (0.5)
        (0.0, 1.0, 'D5'), (1.0, 0.5, 'Eb5'), (1.5, 1.5, 'F#5'), (3.0, 0.5, 'Eb5'), (3.5, 0.5, 'D5'),
        # Bar 2: G5 (1.5), F#5 (0.5), Eb5 (1.0), D5 (1.0)
        (4.0, 1.5, 'G5'), (5.5, 0.5, 'F#5'), (6.0, 1.0, 'Eb5'), (7.0, 1.0, 'D5'),
        # Bar 3: A5 (1.5), Bb5 (0.5), C6 (1.0), Bb5 (0.5), A5 (0.5)
        (8.0, 1.5, 'A5'), (9.5, 0.5, 'Bb5'), (10.0, 1.0, 'C6'), (11.0, 0.5, 'Bb5'), (11.5, 0.5, 'A5'),
        # Bar 4: F#5 (2.0), Eb5 (1.0), D5 (1.0)
        (12.0, 2.0, 'F#5'), (14.0, 1.0, 'Eb5'), (15.0, 1.0, 'D5'),
        # Bar 5: Higher octave climb! D6 (1.0), Eb6 (0.5), F#6 (1.5), Eb6 (0.5)
        (16.0, 1.0, 'D6'), (17.0, 0.5, 'Eb6'), (17.5, 1.5, 'F#6'), (19.0, 0.5, 'Eb6'), (19.5, 0.5, 'D6'),
        # Bar 6: C6 (1.0), Bb5 (1.0), A5 (1.0), G5 (1.0)
        (20.0, 1.0, 'C6'), (21.0, 1.0, 'Bb5'), (22.0, 1.0, 'A5'), (23.0, 1.0, 'G5'),
        # Bar 7: F#5 (1.0), G5 (0.5), A5 (0.5), Eb5 (1.0), F#5 (1.0)
        (24.0, 1.0, 'F#5'), (25.0, 0.5, 'G5'), (25.5, 0.5, 'A5'), (26.0, 1.0, 'Eb5'), (27.0, 1.0, 'F#5'),
        # Bar 8: Resolution to D5 (3.0 beats)
        (28.0, 3.0, 'D5')
    ]

    for start_beat, dur_beats, note_name in ney_melody:
        add_note(track, start_beat * beat_dur, dur_beats * beat_dur * 0.95,
                 note_to_freq(note_name), 'ney', pan=0.20, vol=0.36)

    # 5. Deep Desert Bass
    desert_bass = [
        (0.0, 'D2'), (4.0, 'Eb2'), (8.0, 'D2'), (12.0, 'G1'),
        (16.0, 'D2'), (20.0, 'Eb2'), (24.0, 'A1'), (28.0, 'D2')
    ]
    for start_beat, note_name in desert_bass:
        add_note(track, start_beat * beat_dur, 4.0 * beat_dur * 0.88,
                 note_to_freq(note_name), 'bass', pan=0.0, vol=0.45)

    reverbed = apply_stereo_reverb(track, wet=0.24)
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
    # Intricate 16th-note Baroque gear runs: Am, Dm, F, E7, C, G, F, E7
    gears_melody = [
        # Bar 1 (Am)
        ['A4', 'C5', 'E5', 'A5', 'E5', 'C5', 'A4', 'C5'],
        # Bar 2 (Dm)
        ['F4', 'A4', 'D5', 'F5', 'D5', 'A4', 'F4', 'A4'],
        # Bar 3 (F)
        ['C4', 'F4', 'A4', 'C5', 'A4', 'F4', 'C4', 'F4'],
        # Bar 4 (E7)
        ['B3', 'E4', 'G#4', 'B4', 'D5', 'B4', 'G#4', 'E4'],
        # Bar 5 (C)
        ['C4', 'E4', 'G4', 'C5', 'E5', 'C5', 'G4', 'E4'],
        # Bar 6 (G)
        ['D4', 'G4', 'B4', 'D5', 'G5', 'D5', 'B4', 'G4'],
        # Bar 7 (F)
        ['C4', 'F4', 'A4', 'C5', 'F5', 'C5', 'A4', 'F4'],
        # Bar 8 (E7)
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
        # Bar 1: E5 (1.5), A5 (1.5), B5 (1.0)
        (0.0, 1.5, 'E5'), (1.5, 1.5, 'A5'), (3.0, 1.0, 'B5'),
        # Bar 2: C6 (2.0), B5 (1.0), A5 (1.0)
        (4.0, 2.0, 'C6'), (6.0, 1.0, 'B5'), (7.0, 1.0, 'A5'),
        # Bar 3: F5 (1.5), A5 (1.5), D6 (1.0)
        (8.0, 1.5, 'F5'), (9.5, 1.5, 'A5'), (11.0, 1.0, 'D6'),
        # Bar 4: B5 (2.5), G#5 (1.5)
        (12.0, 2.5, 'B5'), (14.5, 1.5, 'G#5'),
        # Bar 5: E5 (1.0), G5 (1.0), C6 (1.5), D6 (0.5)
        (16.0, 1.0, 'E5'), (17.0, 1.0, 'G5'), (18.0, 1.5, 'C6'), (19.5, 0.5, 'D6'),
        # Bar 6: E6 (2.0), D6 (1.0), B5 (1.0)
        (20.0, 2.0, 'E6'), (22.0, 1.0, 'D6'), (23.0, 1.0, 'B5'),
        # Bar 7: C6 (1.0), A5 (1.0), F5 (1.0), B5 (1.0)
        (24.0, 1.0, 'C6'), (25.0, 1.0, 'A5'), (26.0, 1.0, 'F5'), (27.0, 1.0, 'B5'),
        # Bar 8: A5 (3.0 beats grand grandfather clock resolution)
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

    print("Synthesizing enhanced thematic soundtracks...")
    generate_quarter1(q1_path)
    generate_quarter2(q2_path)
    generate_quarter3(q3_path)
    generate_quarter4(q4_path)
    print("All enhanced soundtracks generated and verified successfully!")


if __name__ == "__main__":
    main()
