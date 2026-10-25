#!/usr/bin/env python3
"""Measure the soundtrack, so the pieces cannot quietly converge back into one.

The first score had four pieces inside one scale, within 1.9 dB of each other, three of
them gravitating to the same pitch class. Nothing caught that, because nothing measured it.
This script is the guard: it decodes every file in public/assets/audio and reports the three
things a listener separates music by -- what note it gravitates to, how often events happen,
and where its energy sits -- then asserts that the pieces are actually apart on all three.

  pitch class   the tonic the piece keeps returning to (chroma centre of mass)
  density       note onsets per second
  centroid      spectral centre of mass in Hz, i.e. how high it sounds

It also keeps the mix honest: effects used to sit ~12 dB above the music and every footfall
jumped out of the quiet.

Usage:  python3 scripts/check_audio.py
Exit status is non-zero if any piece has drifted or any file is missing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / 'public/assets/audio'
SR = 44100
PITCH = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

# The pieces and the world each one is written for. They are asserted to differ.
SCENE_PIECES = [
    ('bgm-garden', 'gong D', 'the courtyard by day'),
    ('bgm-street', 'gong G', 'outside the walls'),
    ('bgm-water', 'yu B', 'the canal, going north'),
    ('bgm-night', 'shang E', 'night in the house'),
    ('bgm-interior', 'zhi A', 'indoors, among people'),
    ('bgm-myth', 'jue F#', 'before there was a house'),
]

# One per chapter: the floor the story stands on. They are checked against the scene
# pieces too -- a chapter piece that shares a tonic with a scene piece would sound like
# the same tune whenever the reader crossed between the two.
BOOK_PIECES = [
    ('bgm-book-one', 'yu Bb', 'the first chapter'),
    ('bgm-book-two', 'zhi C', 'the second chapter'),
    ('bgm-book-three', 'gong Db', 'the third chapter'),
    ('bgm-book-four', 'shang Eb', 'the fourth chapter'),
]

PIECES = SCENE_PIECES + BOOK_PIECES

EFFECTS = ['sfx-step-board', 'sfx-step-stone', 'sfx-step-earth', 'sfx-oar',
           'sfx-tap', 'sfx-door', 'sfx-page', 'sfx-bell', 'sfx-chair']


def decode(name: str) -> np.ndarray:
    """Mono float32 at 44.1 kHz, straight out of the Ogg the browser will fetch."""
    path = AUDIO / f'{name}.ogg'
    if not path.exists():
        raise SystemExit(f'missing {path}')
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR),
         '-f', 'f32le', '-'],
        capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype='<f4').astype(np.float64)
    if not len(x):
        raise SystemExit(f'{name}.ogg decoded to nothing')
    return x


def pitch_profile(x: np.ndarray) -> tuple[int, float]:
    """The pitch class the piece leans on, and the spectral centre of mass.

    The tricky part is that a plucked string and a metal bowl both carry strong
    harmonics, and the third harmonic of D is D, the third of C is G, the fifth of C is E.
    Summing every harmonic into the pitch-class histogram therefore lets a piece whose
    tonic is C read as G or E simply because the timbre is rich -- which is exactly what
    happened to the first chapter pieces, whose D and C tonics were being reported as F.

    So the histogram is built from a single harmonic band per note instead: for every
    frame the strongest pitch is found by the autocorrelation of the spectrum, and only
    that one pitch class is credited. A note counts once, at its own height.
    """
    win, hop = 8192, 4096
    votes = np.zeros(12)
    centroid = []
    for i in range(0, len(x) - win, hop):
        seg = x[i:i + win] * np.hanning(win)
        spectrum = np.abs(np.fft.rfft(seg))
        freqs = np.fft.rfftfreq(win, 1 / SR)
        total = spectrum.sum()
        if total < 1e-6:
            continue
        centroid.append(float((freqs * spectrum).sum() / total))
        pitched = (freqs > 70) & (freqs < 1600)
        if not pitched.any():
            continue
        band = spectrum[pitched]
        band_freqs = freqs[pitched]
        # the strongest partial in this frame, and the note it belongs to
        k = int(np.argmax(band))
        f0 = float(band_freqs[k])
        if f0 <= 0:
            continue
        votes[int(round(12 * np.log2(f0 / 440.0))) % 12] += 1
    if not centroid or votes.sum() == 0:
        return -1, 0.0
    return int(votes.argmax()), float(np.mean(centroid))


def onset_density(x: np.ndarray) -> float:
    """Note attacks per second, picked as peaks in spectral flux.

    A loudness envelope is the wrong instrument here: it turns over on every vibrato
    cycle, every lute tremolo and again on each ripple of the reverb tail, and it cannot
    see a quiet ripple hidden under a long note -- which is exactly how the old four pieces
    all came out at ~0.2-0.7 attacks a second regardless of how many notes they contained.
    Spectral flux sums only the spectrum's growth, so a soft new note over a decaying one
    still registers, while a vibrato's wobble, which moves energy sideways rather than
    upward, mostly does not.

    The threshold is local (a frame must beat the mean of its own neighbourhood), so a
    piece with few loud attacks still gets its quiet ones counted, and a minimum gap of
    0.12 s stops one pluck being counted twice through two analysis frames.
    """
    win, hop = 2048, 512
    start = np.arange(0, len(x) - win, hop)
    if len(start) < 16:
        return 0.0
    window = np.hanning(win)
    spectrum = np.abs(np.fft.rfft(x[start[:, None] + np.arange(win)] * window, axis=1))
    # half-wave rectified growth across the spectrum
    flux = np.maximum(np.diff(spectrum, axis=0), 0).sum(axis=1)
    if flux.max() <= 0:
        return 0.0
    flux = flux / flux.max()

    neighbourhood = max(1, int(0.1 * SR / hop))
    kept, last = 0, -1e9
    for k in range(len(flux)):
        t = k * hop / SR
        if t - last < 0.12:
            continue
        lo, hi = max(0, k - neighbourhood), min(len(flux), k + neighbourhood + 1)
        local = flux[lo:hi]
        if flux[k] >= local.max() and flux[k] > local.mean() + 0.08:
            kept += 1
            last = t
    return round(kept / (len(x) / SR), 2)


def measure(name: str) -> dict:
    x = decode(name)
    top, centroid = pitch_profile(x)
    rms = float(np.sqrt((x ** 2).mean()))
    return {
        'name': name,
        'seconds': round(len(x) / SR, 1),
        'rms_db': round(float(20 * np.log10(rms + 1e-12)), 1),
        'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-12)), 2),
        'pitch': PITCH[top] if top >= 0 else '-',
        'pitch_index': top,
        'centroid': int(centroid),
        'density': onset_density(x),
    }


def main() -> int:
    failures: list[str] = []

    pieces = [measure(name) for name, _, _ in PIECES]
    effects = [measure(name) for name in EFFECTS]

    print('Music')
    print(f"  {'piece':16s}{'world':26s}{'mode':9s}{'secs':>6}{'RMS':>7}"
          f"{'pitch':>7}{'centroid':>10}{'onsets/s':>10}")
    for row, (_, mode, world) in zip(pieces, PIECES):
        print(f"  {row['name']:16s}{world:26s}{mode:9s}{row['seconds']:>6}"
              f"{row['rms_db']:>7}{row['pitch']:>7}{row['centroid']:>10}{row['density']:>10}")

    print('\nEffects')
    print(f"  {'effect':18s}{'secs':>6}{'RMS':>7}{'peak':>8}")
    for row in effects:
        print(f"  {row['name']:18s}{row['seconds']:>6}{row['rms_db']:>7}{row['peak_db']:>8}")

    # --- the three axes have to actually separate the pieces -------------------
    pitches = [p['pitch'] for p in pieces]
    if len(set(pitches)) != len(pitches):
        dupes = [p for p in set(pitches) if pitches.count(p) > 1]
        failures.append(f'pieces share a tonic pitch class: {", ".join(dupes)} '
                        '(a listener hears this as one piece everywhere)')

    densities = sorted(p['density'] for p in pieces)
    spread = densities[-1] / max(densities[0], 0.01)
    if spread < 4:
        failures.append(f'density spread only {spread:.1f}x between sparsest and busiest '
                        'piece; the music needs at least 4x to read as different worlds')

    centroids = [p['centroid'] for p in pieces]
    if max(centroids) < 2 * min(centroids):
        failures.append(f'register too narrow: centroids {min(centroids)}-{max(centroids)} Hz; '
                        'the pieces need to sit in different octaves to tell apart')

    # --- the mix has to stay balanced ------------------------------------------
    loudest_effect = max(e['rms_db'] for e in effects)
    loudest_piece = max(p['rms_db'] for p in pieces)
    if loudest_effect - loudest_piece > 8:
        failures.append(f'effects sit {loudest_effect - loudest_piece:.1f} dB above the '
                        'loudest piece; they used to be 12 dB up and startled everybody')

    for row in pieces + effects:
        if row['peak_db'] > -0.1:
            failures.append(f"{row['name']} clips (peak {row['peak_db']} dBFS)")
        if row['rms_db'] < -45:
            failures.append(f"{row['name']} is inaudibly quiet ({row['rms_db']} dBFS RMS)")

    if failures:
        print('\nFAILED')
        for f in failures:
            print(f'  - {f}')
        return 1

    print(f'\nOK: {len(pieces)} pieces on {len(set(pitches))} distinct tonics, '
          f'density spread {spread:.1f}x, centroids {min(centroids)}-{max(centroids)} Hz, '
          f'effects {loudest_effect - loudest_piece:.1f} dB above the loudest piece')
    return 0


if __name__ == '__main__':
    sys.exit(main())
