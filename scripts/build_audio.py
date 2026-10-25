#!/usr/bin/env python3
"""Synthesize the soundtrack: six pieces, one for each world in the story.

Everything is built from oscillators and filtered noise at 44.1 kHz, then written as Ogg
Opus next to the other art. There is no sample library here on purpose: the score is a
handful of partials per instrument, and a generated file is tens of kilobytes where a
sampled pack would be tens of megabytes.

Why six pieces, and why they sound different from each other
------------------------------------------------------------
The first version scored four worlds inside a single D-gong pentatonic scale, within
1.9 dB of one loudness, every tune slow and mostly stepwise. Measured, the four came out
alike on every axis a listener actually separates music by:

    piece          RMS   top pitch class   onsets/s   spectral centroid
    bgm-garden    -26.1        D             0.74          1242 Hz
    bgm-night     -27.1        D             0.24           584 Hz
    bgm-interior  -28.0        A             0.14          2304 Hz
    bgm-myth      -27.4        D             0.14           849 Hz

Three of four had their centre of gravity on the same pitch class, and three of four were
within 0.1 onsets/s of each other -- which is what "配得很差" sounds like from the outside:
one piece played everywhere. So the three axes are now assigned per piece on purpose, and
`scripts/check_audio.py` re-measures them so the difference cannot rot away silently.

  piece          mode   root   tempo   leading voice            register   density
  bgm-garden     gong   D      58      xiao over zheng arpeggio  middle     flowing
  bgm-street     gong   G      76      pipa ostinato + woodblock bright     busy
  bgm-water      yu     B      66      zheng ripple over a drone low        rippling
  bgm-night      shang  E      42      qin, long rests, one bell deep       very sparse
  bgm-interior   zhi    A      50      qin states, pipa answers  upper      conversational
  bgm-myth       jue    F#     36      bowls, gong chimes, drone vast       almost none

Modes are pentatonic degrees counted from the tonic: gong [0,2,4,7,9] is the settled day
mode, yu [0,3,5,8,10] the aching one, jue [0,3,5,8,10] a floating relation of it, shang
[0,2,5,7,10] grey and inward, zhi [0,2,5,7,9] open. Six roots put six different pitch
classes at the centre of the six pieces.

Instruments
  zheng  plucked zither   - additive partials, fast per-partial decay
  xiao   bamboo flute     - subtractive tone, breath noise, vibrato, slow attack
  qin    guqin            - low plucked tone with scrape, long body
  pipa   pear lute        - bright plucked tone, short decay, tremolo
  qing   singing bowl     - inharmonic metal partials, long ring
  muyu   wood block       - dry knock: two decaying sines over a noise click
  yunluo small gong set   - bright metal cluster, quick ring, thinner than qing

Effects are keyed by the surface walked on, doored by the act of entering a room.

Usage:  python3 scripts/build_audio.py [--only NAME ...]
"""
from __future__ import annotations

import argparse
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/assets/audio'
SR = 44100

# Pentatonic modes as semitone steps above the tonic. Counting degrees from 0 lets a tune
# be written as numbers and then transposed by changing nothing but the mode and root.
MODES = {
    'gong': (0, 2, 4, 7, 9),
    'shang': (0, 2, 5, 7, 10),
    'jue': (0, 3, 5, 8, 10),
    'zhi': (0, 2, 5, 7, 9),
    'yu': (0, 3, 5, 8, 10),
}


class Mode:
    """A pentatonic mode on a root. Degree 0 is the tonic, 5 the octave, -5 the one below."""

    def __init__(self, name: str, root: float):
        self.steps = MODES[name]
        self.root = root

    def f(self, degree: int) -> float:
        octave, step = divmod(int(degree), 5)
        return self.root * (2 ** octave) * (2 ** (self.steps[step] / 12))


# Every piece gets its own tonic pitch class, so no two gravitate to the same note. The
# octave is chosen per instrument range: the tune should sit where the leading voice lives,
# not an octave under it where everything turns to mud.
GARDEN = Mode('gong', 293.665)      # D4 - xiao tune sits D4..D5, zheng answers an octave down
STREET = Mode('gong', 196.000)      # G3 - pipa ostinato low, the calls over it mid-range
WATER = Mode('yu', 246.942)         # B3 - low, and it wants to fall
NIGHT = Mode('shang', 164.814)      # E3 - grey, inward, low enough to cost something
INTERIOR = Mode('zhi', 220.000)     # A3 - open, affirmative
MYTH = Mode('jue', 184.997)         # F#3 - floating, resolves nowhere

# One more per chapter. A stage theme says where you are; the chapter says what kind of
# story you are in, and the two are different axes. These four are the floor the whole
# book stands on, and each one gets a key, a tempo and a voice of its own.
#
# The keys are chosen to be clear of the six scene pieces as well as of each other, so a
# chapter piece and a scene piece never sound like the same tune: D, G, B, E, A and F# are
# taken by the scenes, and the chapters use Bb, C, Db and Eb. A reader who hears ten
# distinct pieces should be able to place each one.
BOOK_ONE = Mode('yu', 233.082)      # Bb3 - 甄士隐的园子: a minor key, and a cold moon over it
BOOK_TWO = Mode('zhi', 261.626)     # C4 - 冷子兴的生意: open and practical, a man making plans
BOOK_THREE = Mode('gong', 277.183)  # Db3 - 进京: the settled mode, one step under the garden
BOOK_FOUR = Mode('shang', 155.563)  # Eb3 - 官场: grey and low, the sound of a case being argued


# ---------------------------------------------------------------- envelopes

def exp_env(t: np.ndarray, attack: float, decay: float) -> np.ndarray:
    """Percussive envelope: linear attack then exponential decay to zero."""
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-6))
    return a * d


def flute_env(t: np.ndarray, attack: float, release: float, sustain: float) -> np.ndarray:
    """Slow swell, hold, then a breathy release -- how a xiao is actually blown."""
    total = t[-1] if len(t) else 1.0
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    r_start = total - release
    r = np.clip((total - t) / max(release, 1e-6), 0, 1)
    hold = t < r_start
    env = np.where(hold, a, np.minimum(a, r))
    # a hair of noise on the swell so the attack is never a pure tone
    return env * (1.0 - 0.25 * sustain * (1 - np.exp(-t / 0.4)))


# ---------------------------------------------------------------- instruments

def zheng(freq: float, dur: float, gain: float = 1.0, brightness: float = 1.0,
          seed: int = 7) -> np.ndarray:
    """Additive plucked string: numbered partials, 1/n tilt, faster decay higher up."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 19):
        f = freq * k
        if f > SR / 2 - 2000:
            break
        amp = gain / (k ** 1.15)
        decay = 1.6 / (1 + 0.55 * (k - 1))
        env = exp_env(t, 0.002, decay)
        # slight detune keeps the upper partials from sounding synthetic
        detune = 1 + (0.0006 if k % 2 else -0.0006)
        out += amp * env * np.sin(2 * np.pi * f * detune * t + 0.6 * k)
    # the pluck itself: a very short bright noise
    if n > 40:
        pluck = np.random.default_rng(seed).standard_normal(n)
        window = max(2, int(0.004 * SR))
        pluck[:window] *= np.linspace(1, 0, window)
        out += 0.05 * gain * pluck
    return out * brightness


def xiao(freq: float, dur: float, gain: float = 1.0, vibrato: float = 1.0,
         breathiness: float = 1.0, attack: float = 0.09) -> np.ndarray:
    """Bamboo flute: triangle-leaning tone, breath band, vibrato, slow swell."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + vibrato * 0.011 * np.sin(2 * np.pi * 5.3 * t) \
              + vibrato * 0.004 * np.sin(2 * np.pi * 6.9 * t + 1.1)
    phase = 2 * np.pi * freq * np.cumsum(vib) / SR
    tone = (np.sin(phase) + 0.32 * np.sin(2 * phase) + 0.12 * np.sin(3 * phase)
            + 0.05 * np.sin(4 * phase))
    # breath noise through a band around the tone
    rng = np.random.default_rng(11)
    noise = rng.standard_normal(n)
    breath = simple_band(noise, freq * 2.6, 3.0) * 0.05
    breath += simple_band(noise, 2600, 2.2) * 0.018
    env = flute_env(t, attack, min(0.22, dur * 0.45), 1.0)
    return gain * env * (tone + breath * breathiness)


def qin(freq: float, dur: float, gain: float = 1.0) -> np.ndarray:
    """Guqin: darker than the zheng, longer body, a scrape on the attack."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 11):
        f = freq * k
        if f > SR / 2 - 1500:
            break
        amp = gain / (k ** 1.5)
        env = exp_env(t, 0.006, 3.4 / (1 + 0.4 * (k - 1)))
        out += amp * env * np.sin(2 * np.pi * f * t)
    rng = np.random.default_rng(23)
    scrape = simple_band(rng.standard_normal(n), freq * 4, 1.6) * 0.05
    scrape *= exp_env(t, 0.05, 0.5)
    return out + scrape


def pipa(freq: float, dur: float, gain: float = 1.0) -> np.ndarray:
    """Pipa: bright, short, with the tremolo a lute is played with."""
    base = zheng(freq, dur, gain, brightness=1.35)
    trem = 1 + 0.09 * np.sin(2 * np.pi * 11.5 * np.arange(len(base)) / SR)
    return base * trem


def qing(freq: float, dur: float, gain: float = 1.0) -> np.ndarray:
    """Singing bowl: inharmonic partials, the ratios a metal bowl actually rings on."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, ratio in enumerate([1.0, 2.76, 5.40, 8.93, 13.34, 17.9]):
        if k == 0:
            amp, decay = gain, 4.2
        else:
            amp, decay = gain / (k + 1.4), 4.2 / (1 + 0.9 * k)
        f = freq * ratio
        if f > SR / 2 - 500:
            break
        out += amp * exp_env(t, 0.003, decay) * np.sin(2 * np.pi * f * t + 0.4 * k)
    return out


def muyu(freq: float = 900.0, gain: float = 1.0, seed: int = 77) -> np.ndarray:
    """Wood block: the dry knock a street player keeps time on, no pitch worth naming."""
    dur = 0.13
    n = int(dur * SR)
    t = np.arange(n) / SR
    # two decaying partials slightly apart is what makes it read as wood, not noise
    body = (np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.016)
            + 0.6 * np.sin(2 * np.pi * freq * 2.41 * t) * np.exp(-t / 0.009))
    click = simple_band(np.random.default_rng(seed).standard_normal(n), freq * 1.8, 1.2)
    click *= np.exp(-t / 0.006)
    return gain * (body * 0.7 + click * 0.35)


def yunluo(freq: float, dur: float = 1.8, gain: float = 1.0) -> np.ndarray:
    """Small gong: bright metal, quicker ring than the bowl, thinner high partials."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, ratio in enumerate([1.0, 2.4, 4.1, 6.7, 9.2]):
        f = freq * ratio
        if f > SR / 2 - 500:
            break
        amp = gain / (1 + 1.5 * k)
        out += amp * exp_env(t, 0.002, 1.1 / (1 + 1.1 * k)) * np.sin(2 * np.pi * f * t + 0.9 * k)
    return out


def drone(freq: float, dur: float, gain: float = 1.0, beat: float = 0.07,
          noise: float = 0.0) -> np.ndarray:
    """A sustained bed: two voices detuned just enough to breathe against each other."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.sin(2 * np.pi * freq * t) * 0.6
    out += np.sin(2 * np.pi * freq * 1.003 * t) * 0.4
    out += np.sin(2 * np.pi * freq * 2 * t) * 0.14
    if noise:
        bed = simple_band(np.random.default_rng(31).standard_normal(n), freq * 3, 1.1)
        bed *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.03 * t)
        out += bed * noise
    return gain * out * (0.55 + 0.45 * np.sin(2 * np.pi * beat * t))


def simple_band(x: np.ndarray, center: float, q: float) -> np.ndarray:
    """Resonant band via FFT; used for breath, footsteps, wood, water."""
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    response = 1 / (1 + ((freqs - center) / (center / max(q, 0.5))) ** 2)
    return np.fft.irfft(spec * response, n)


# ---------------------------------------------------------------- effects

def fx_step(kind: str, seed: int = 0) -> np.ndarray:
    """A footfall on one surface: boards ring, stone does not, earth only whispers."""
    dur = {'board': 0.17, 'stone': 0.15, 'earth': 0.18}[kind]
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(101 + seed)
    noise = rng.standard_normal(n)
    if kind == 'board':
        body = simple_band(noise, 760, 2.4)
        knock = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045)
        sig = body * 0.9 + knock * 0.28
        sig += simple_band(noise, 2100, 1.6) * 0.05      # the boards.
    elif kind == 'stone':
        body = simple_band(noise, 320, 1.8)
        click = simple_band(noise, 2600, 1.2) * np.exp(-t / 0.012)
        sig = body * 1.0 + click * 0.12
    else:  # earth, the lane out past the city wall: no impact, only a brush of grit
        body = simple_band(noise, 1500, 0.9)
        low = simple_band(noise, 220, 1.1) * 0.25
        sig = body * 0.55 + low
    return sig * exp_env(t, 0.004, {'board': 0.055, 'stone': 0.04, 'earth': 0.07}[kind]) * 0.9


def fx_oar() -> np.ndarray:
    """A pole or an oar in water: the push is low, the drip afterwards is high."""
    dur = 0.55
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(606)
    push = simple_band(rng.standard_normal(n), 190, 1.4) * np.exp(-((t - 0.05) ** 2) / 0.02)
    push += np.sin(2 * np.pi * 88 * t) * np.exp(-((t - 0.05) ** 2) / 0.03) * 0.35
    # the water that falls back off the blade
    drip = simple_band(rng.standard_normal(n), 2400, 2.2) * np.exp(-((t - 0.17) ** 2) / 0.012)
    return push * 0.85 + drip * 0.5


def fx_tap() -> np.ndarray:
    """UI chime: a small bowl, high and short."""
    return qing(587.330, 1.6, 0.5) * 0.8


def fx_door() -> np.ndarray:
    """Wooden door: a slow squeak, then a low thud as it seats."""
    dur = 1.5
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(303)
    # hinge squeak: a gliding resonance with noise in it
    f = 95 + 55 * (1 - np.exp(-t / 0.35)) + 8 * np.sin(2 * np.pi * 7 * t)
    squeak = simple_band(rng.standard_normal(n), 1.0, 0.6)
    squeak = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + squeak * 0.10
    squeak *= np.exp(-((t - 0.55) ** 2) / 0.16)
    thud = np.sin(2 * np.pi * 62 * t) * np.exp(-((t - 0.62) ** 2) / 0.09) * 0.55
    thud += simple_band(rng.standard_normal(n), 240, 1.2) * np.exp(-((t - 0.62) ** 2) / 0.05) * 0.18
    return squeak + thud


def fx_page() -> np.ndarray:
    """Turning a page: high-band noise with two rustles."""
    dur = 0.42
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(404)
    noise = rng.standard_normal(n)
    hi = simple_band(noise, 3400, 0.9)
    rustle = hi * (np.exp(-((t - 0.10) ** 2) / 0.035) + 0.7 * np.exp(-((t - 0.24) ** 2) / 0.05))
    return rustle * 0.5


def fx_bell() -> np.ndarray:
    """Distant temple bell: one low strike with a long, quiet tail."""
    return simple_lowpass(qing(146.832, 6.0, 0.85), 900) * 0.75


def fx_chair() -> np.ndarray:
    """Sedan poles working under a load: two dry wood rubs, slightly out of step."""
    dur = 1.1
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(505)
    out = np.zeros(n)
    for i, (at, f0) in enumerate([(0.06, 150), (0.42, 128)]):
        f = f0 + 22 * np.sin(2 * np.pi * (6 + 3 * i) * t) * np.exp(-t / 0.3)
        seg = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
        seg += simple_band(rng.standard_normal(n), f0 * 5, 2.0) * 0.12
        seg *= np.exp(-((t - at) ** 2) / 0.045)
        out += seg
    return out


def simple_lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(spec / (1 + (freqs / cutoff) ** 2), n)


# ---------------------------------------------------------------- reverb & mix

def make_ir(seconds: float = 2.6, decay: float = 2.4, seed: int = 909) -> np.ndarray:
    """A small hall: exponentially decaying noise with a few early reflections."""
    n = int(seconds * SR)
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal(n)
    env = np.exp(-np.arange(n) / (decay * SR))
    # early reflections give the tail a room instead of a garage
    for at, gain in [(0.011, .5), (0.019, .42), (0.027, .34), (0.041, .26), (0.063, .2)]:
        i = int(at * SR)
        if i < n:
            ir[i] += gain * rng.standard_normal()
    ir *= env
    # predelay keeps the dry signal clear of the wash
    ir = np.concatenate([np.zeros(int(0.018 * SR)), ir])
    ir /= np.sqrt((ir ** 2).sum() + 1e-9)
    return ir


def reverb(sig: np.ndarray, ir: np.ndarray, wet: float = 0.28) -> np.ndarray:
    n = len(sig)
    spec = np.fft.rfft(sig, n + len(ir))
    wet_sig = np.fft.irfft(spec * np.fft.rfft(ir, n + len(ir)), n + len(ir))[:n]
    return sig * (1 - wet) + wet_sig * wet


def normalize(sig: np.ndarray, target_rms: float) -> np.ndarray:
    rms = float(np.sqrt((sig ** 2).mean()))
    if rms < 1e-9:
        return sig
    sig = sig * (target_rms / rms)
    return np.clip(sig, -0.98, 0.98)


def soften(sig: np.ndarray, cutoff: float) -> np.ndarray:
    """Roll the top off so a bright pluck does not hiss on laptop speakers."""
    n = len(sig)
    spec = np.fft.rfft(sig)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(spec / (1 + (freqs / cutoff) ** 2), n)


def loop_seam(bus: np.ndarray, seconds: float = 2.0) -> np.ndarray:
    """Restate the opening bars quietly at the end, so the loop point joins two
    similar moments instead of silence-to-full-band. Without this a piece whose last
    note has fully decayed clicks back in at the top of bar one."""
    tail = bus[-int(seconds * SR):].copy()
    head = bus[:int(seconds * SR)] * 0.55
    n = min(len(tail), len(head))
    tail[:n] += head[:n]
    bus[-int(seconds * SR):] = tail
    return bus


def to_stereo(sig: np.ndarray, width: float = 0.6) -> np.ndarray:
    """Give the mono bus a little width: the plucks sit slightly right, the flute left."""
    n = len(sig)
    t = np.arange(n) / SR
    drift = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)
    left = sig * (1 - width * 0.5 * drift)
    right = sig * (1 - width * 0.5 * (1 - drift))
    return np.stack([left, right], axis=1)


# ---------------------------------------------------------------- piece helpers

def placer(bus: np.ndarray):
    """Add rendered notes onto a bus at musical times."""
    def place(sig: np.ndarray, at: float, gain: float = 1.0) -> None:
        i = int(at * SR)
        if i >= len(bus):
            return
        end = min(len(bus), i + len(sig))
        bus[i:end] += sig[:end - i] * gain
    return place




# ---------------------------------------------------------------- the pieces

def piece_garden() -> tuple[np.ndarray, float]:
    """The courtyard by day. gong on D: xiao sings, zheng answers, pipa ties the phrases.
    The busiest of the indoor-outdoor worlds, and the reference the rest are tuned against."""
    m = GARDEN
    bpm = 58.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 16
    total = bars * bar + 3.0
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # Four couplets: a question of two bars, an answer of two. The last couplet lands on
    # the tonic a third higher than it began, which is the only arc this piece needs.
    # (bar, beat-in-bar, degree, beats long)
    melody = [
        (0, 0.0, 0, 1.5), (0, 1.5, 1, 0.5), (0, 2.0, 2, 1.0), (0, 3.0, 3, 1.5),
        (1, 1.0, 2, 1.0), (1, 2.0, 1, 2.0),
        (2, 0.5, 2, 1.0), (2, 1.5, 3, 0.5), (2, 2.0, 4, 1.0), (2, 3.0, 3, 1.5),
        (3, 1.0, 2, 1.0), (3, 2.0, 1, 2.5),
        (4, 0.0, 3, 1.0), (4, 1.0, 4, 1.0), (4, 2.0, 5, 2.0),
        (5, 1.0, 4, 1.0), (5, 2.0, 3, 2.0),
        (6, 0.5, 2, 1.0), (6, 1.5, 3, 1.0), (6, 2.5, 4, 1.0), (6, 3.5, 5, 1.5),
        (7, 1.5, 4, 1.0), (7, 2.5, 3, 2.0),
        (8, 0.0, 5, 1.5), (8, 1.5, 4, 0.5), (8, 2.0, 3, 1.0), (8, 3.0, 2, 1.5),
        (9, 1.0, 3, 1.0), (9, 2.0, 4, 2.0),
        (10, 0.5, 5, 1.0), (10, 1.5, 4, 1.0), (10, 2.5, 3, 1.5),
        (11, 0.5, 2, 1.0), (11, 1.5, 1, 2.5),
        (12, 0.0, 0, 1.0), (12, 1.0, 2, 1.0), (12, 2.0, 3, 2.0),
        (13, 1.0, 4, 1.0), (13, 2.0, 5, 2.0),
        (14, 0.5, 4, 1.0), (14, 1.5, 3, 1.0), (14, 2.5, 2, 1.5),
        (15, 0.5, 1, 1.0), (15, 1.5, 0, 4.0),
    ]
    for bar_i, beat_i, deg, length in melody:
        place(xiao(m.f(deg), length * beat + 0.35, 0.30), bar_i * bar + beat_i * beat)

    # zheng: an answering roll under each couplet close, and a figure on the odd bars
    for bar_i in range(0, bars, 2):
        at = bar_i * bar
        place(zheng(m.f(-5), 2.4, 0.24), at)
        place(zheng(m.f(-3), 2.2, 0.20), at + 0.18)
        place(zheng(m.f(-1), 2.2, 0.17), at + 0.36)
        place(zheng(m.f(2), 2.0, 0.13), at + 0.54)
    for bar_i in range(1, bars, 2):
        at = bar_i * bar + beat
        place(zheng(m.f(3), 1.6, 0.11), at)
        place(zheng(m.f(5), 1.4, 0.09), at + 0.22)

    # pipa: three-note filigree where the voice rests, once per couplet
    for bar_i, deg0 in [(1, 5), (5, 6), (9, 7), (13, 6)]:
        for j, d in enumerate((deg0, deg0 - 1, deg0 - 3)):
            place(pipa(m.f(d), 0.5, 0.10), bar_i * bar + 2.5 * beat + j * 0.16)

    place(drone(m.f(-5), total, 0.030), 0.0)
    return bus, total


def piece_street() -> tuple[np.ndarray, float]:
    """Outside the walls, going about business. Same mode as the garden but a tonic a fourth
    away, so the street never sounds like the courtyard it leads out of; the pipa ostinato
    never stops and a wood block counts it off. Densest piece here by a wide margin."""
    m = STREET
    bpm = 76.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 16
    total = bars * bar + 2.6
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # The ostinato never stops, which is the point: a street keeps going whether or not
    # anyone is listening. Two bars of it, four notes to a bar, then a pivot.
    # The ostinato has to keep landing on the tonic or the ear adopts whichever note it
    # hears most, and an earlier figure here spent so long on the mediant that the piece
    # measured as being in B instead of its own G.
    ostinato = [0, 2, 0, 4, 0, 2, 0, 3]
    for bar_i in range(bars):
        for j, deg in enumerate(ostinato):
            at = bar_i * bar + j * beat
            # every second note is an eighth ahead of the beat, so the figure swings
            if j % 2:
                at += beat * 0.5
            place(pipa(m.f(deg), beat * 1.2, 0.075 + 0.02 * (j % 2)), at)

    # wood block on two and four, with a pickup into the next bar. The pitches are tuned
    # into the mode rather than left arbitrary: an untuned knock throws its own weight into
    # the chroma reading and argues with the tonic it is supposed to be counting.
    for bar_i in range(bars):
        place(muyu(784, 0.20), bar_i * bar + beat)
        place(muyu(1176, 0.16), bar_i * bar + 3 * beat)
        place(muyu(1568, 0.10), bar_i * bar + 3.5 * beat)

    # low pluck on the downbeat: this is what the pavements are walking around
    for bar_i in range(0, bars, 2):
        place(pipa(m.f(-5), 1.6, 0.16), bar_i * bar)
        place(pipa(m.f(-2), 1.2, 0.09), bar_i * bar + 2 * beat)

    # short calls over the top: three-and-a-half-bar phrases, each ending differently
    # Short calls over the top, each starting or ending on the tonic -- a phrase that hangs
    # on a note other than G is how this piece ended up sounding like somebody else's key.
    calls = [
        (0, 0.0, 5, 1.0), (0, 1.0, 5, 0.5), (0, 1.5, 4, 0.5), (0, 2.0, 2, 1.0),
        (2, 0.0, 3, 1.0), (2, 1.0, 2, 0.5), (2, 1.5, 0, 0.5), (2, 2.0, 0, 2.0),
        (5, 0.0, 0, 1.0), (5, 1.0, 2, 0.5), (5, 1.5, 4, 0.5), (5, 2.0, 5, 1.0),
        (6, 3.0, 2, 1.5),
        (8, 0.0, 5, 0.5), (8, 0.5, 6, 0.5), (8, 1.0, 5, 1.0), (8, 2.0, 4, 1.0),
        (10, 0.0, 2, 1.0), (10, 1.0, 0, 1.0), (10, 2.0, 0, 2.0),
        (12, 0.0, 0, 0.5), (12, 0.5, 2, 0.5), (12, 1.0, 4, 1.0), (12, 2.0, 5, 1.0),
        (13, 0.0, 5, 2.0),
        (14, 1.0, 2, 1.0), (14, 2.0, 0, 1.0), (14, 3.0, 0, 2.5),
    ]
    for bar_i, beat_i, deg, length in calls:
        place(xiao(m.f(deg), length * beat + 0.25, 0.20, attack=0.05),
              bar_i * bar + beat_i * beat)

    place(drone(m.f(-5), total, 0.022), 0.0)
    return bus, total


def piece_water() -> tuple[np.ndarray, float]:
    """The Grand Canal, going north. yu on B: the minor relation of the mode wants to fall,
    so the ripple figure keeps rolling downhill and never quite settles. Made for the river
    stage, which used to borrow the garden piece and sound like a courtyard with a leak."""
    m = WATER
    bpm = 66.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 14
    total = bars * bar + 3.4
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # The ripple: eighth-notes in a four-note arch, each note clipped short and light. At
    # every 8th note there is an onset, which is what puts this piece top of the density
    # table without it ever getting loud.
    arch = [0, 2, 4, 5, 4, 2, 1, 0]
    eighth = beat / 2
    for bar_i in range(bars):
        # the figure is an octave down on the odd bars, which reads as the far bank
        low = bar_i % 4 in (2, 3)
        for j, deg in enumerate(arch):
            at = bar_i * bar + j * eighth
            d = deg - 5 if low else deg
            place(zheng(m.f(d), 0.62, 0.055 + 0.015 * (j % 2)), at)

    # A lolling low voice under it: the swell that answers every fourth bar.
    for bar_i in range(0, bars, 4):
        place(qin(m.f(-5), 3.2, 0.24), bar_i * bar)
        place(qin(m.f(-3), 2.6, 0.13), bar_i * bar + 2 * beat)

    # From the bank: someone practising a flute, too far to hear the breath.
    heard = [(1, 0.0, 5, 2.5), (3, 1.0, 7, 3.0),
             (6, 0.0, 6, 2.0), (6, 2.5, 5, 2.5),
             (10, 0.5, 4, 3.5), (12, 1.0, 5, 2.0), (12, 3.5, 4, 3.0)]
    for bar_i, beat_i, deg, length in heard:
        place(xiao(m.f(deg), length * beat + 0.6, 0.13, vibrato=0.6, breathiness=0.7),
              bar_i * bar + beat_i * beat)

    # the hull itself: a low pad with water noise in it, barely audible, never absent
    place(drone(m.f(-10), total, 0.030, beat=0.05, noise=0.25), 0.0)
    return bus, total


def piece_night() -> tuple[np.ndarray, float]:
    """Night in the house. shang on E: grey, with each note costing more than it did in the
    day. Most of this piece is the room being quiet; the rests are written in, not left to
    chance, which is why the density comes out an order of magnitude below anything else."""
    m = NIGHT
    bpm = 42.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 12
    total = bars * bar + 5.0
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # One note to a phrase, and whole bars given back to silence. The tune is the story of
    # someone awake who has nothing to say about it.
    # One note to a phrase, and whole bars given back to silence. The tune is the story of
    # someone awake who has nothing to say about it. Four of the six phrases close on the
    # tonic: shang on E only reads as E if it keeps coming home to it.
    lines = [
        (0, 0.0, 0, 3.0), (0, 3.5, 3, 2.5),
        (2, 0.0, 2, 4.0),
        (4, 1.0, 0, 2.0), (4, 3.5, -1, 3.0),
        (6, 0.0, 0, 4.0),
        (8, 0.5, 3, 1.0), (8, 2.0, 4, 1.0), (8, 3.5, 2, 3.0),
        (10, 0.0, 2, 1.5), (10, 2.0, 0, 2.5), (10, 3.5, 0, 5.0),
    ]
    for bar_i, beat_i, deg, length in lines:
        # Kept inside the low degrees of the mode: shang on E3 already sits under the
        # garden's D4 daylight, and nothing here is asked to climb for it.
        place(qin(m.f(deg), length * beat + 1.2, 0.26),
              bar_i * bar + beat_i * beat)

    # A held flute note once, high and thin, then nothing again for six bars. Both notes
    # are on the tonic: any fifth in this register comes back as its own harmonic anyway,
    # and the piece has no business spending its very few notes off E.
    place(xiao(m.f(5), 6 * beat, 0.16, vibrato=0.5, breathiness=1.3, attack=0.5), 1 * bar)
    place(xiao(m.f(0), 4 * beat, 0.13, vibrato=0.5, breathiness=1.3, attack=0.5), 7 * bar)

    # two bells: one to begin the watch, one to end it. They are struck on the tonic and
    # its fifth, not an octave down -- below about 90 Hz a bell stops being a bell and
    # becomes a thump nobody can localise.
    place(simple_lowpass(qing(m.f(0), 6.0, 0.40), 780), 0.3)
    place(simple_lowpass(qing(m.f(0), 5.0, 0.22), 900), bars * bar - 1.5)

    # The drone carries the tonic through the rests, which is most of this piece; without
    # it the silence between phrases lets whichever degree was last heard decide the key.
    place(drone(m.f(-5), total, 0.05, beat=0.03), 0.0)
    return bus, total


def piece_interior() -> tuple[np.ndarray, float]:
    """Inside, among people. zhi on A: qin states the phrase low, pipa takes it an octave
    up two bars later, and the second half of the piece moves into the upper register so
    there is somewhere for the loop to go."""
    m = INTERIOR
    bpm = 50.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 12
    total = bars * bar + 4.2
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # A section: qin says it plainly.
    # A section: qin says it plainly, and every phrase touches the tonic. An earlier draft
    # spread itself so evenly over the five degrees that the piece had no centre to hear.
    stately = [
        (0, 0.0, 0, 2.5), (0, 2.5, 3, 2.0),
        (2, 0.5, 2, 2.0), (2, 2.5, 0, 2.0),
        (4, 0.0, 2, 2.0), (4, 2.0, 1, 1.5), (4, 3.5, 0, 2.0),
    ]
    for bar_i, beat_i, deg, length in stately:
        place(qin(m.f(deg), length * beat + 0.9, 0.30), bar_i * bar + beat_i * beat)

    # B section: the same thought an octave higher, in the smaller voice. This is where
    # the register of the piece lifts, deliberately, halfway through the loop.
    answers = [
        (6, 0.0, 5, 1.0), (6, 1.0, 5, 0.5), (6, 1.5, 6, 0.5), (6, 2.0, 5, 1.0),
        (7, 0.0, 7, 1.5), (7, 2.0, 5, 2.0),
        (8, 0.5, 6, 1.0), (8, 1.5, 5, 1.0), (8, 2.5, 7, 1.0), (8, 3.5, 6, 1.5),
        (9, 1.0, 5, 1.0), (9, 2.0, 5, 2.0),
        (10, 0.0, 5, 1.0), (10, 1.0, 4, 1.0), (10, 2.0, 3, 2.0),
        (11, 1.0, 2, 1.0), (11, 2.0, 1, 1.0), (11, 3.0, 0, 2.5),
    ]
    for bar_i, beat_i, deg, length in answers:
        place(pipa(m.f(deg), length * beat + 0.35, 0.115), bar_i * bar + beat_i * beat)

    # a harmonic at the hinge between the two halves
    place(pipa(m.f(10), 1.4, 0.09), 5 * bar + 3 * beat)
    place(xiao(m.f(5), 5 * beat, 0.10, attack=0.4), 6 * bar)

    place(drone(m.f(-5), total, 0.026), 0.0)
    return bus, total


def piece_myth() -> tuple[np.ndarray, float]:
    """Before there was a house. jue on F#: the mode with no comfortable landing, so nothing
    resolves for the whole of it. Bowls, a small gong, and one very low drone the piece is
    floating on. No beat worth counting -- the strikes fall where they fall."""
    m = MYTH
    bpm = 36.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 10
    total = bars * bar + 5.0
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # Strikes, not bars: seconds counted from the top, so nothing marches.
    bowls = [
        (0.0, -5, 0.50), (2.6, 0, 0.30), (4.9, 3, 0.22),
        (8.4, -3, 0.34), (10.2, 5, 0.20),
        (13.6, -5, 0.44), (15.8, 7, 0.18),
        (19.0, 0, 0.32), (21.4, 3, 0.24),
        (25.0, 2, 0.30), (27.3, 8, 0.20),
        (30.6, 5, 0.26), (33.0, 3, 0.24), (35.5, 0, 0.40),
        (39.0, -5, 0.34), (41.8, 2, 0.22),
    ]
    for at, deg, gain in bowls:
        place(qing(m.f(deg), 5.5, gain), at)
    # a small gong answering the bowl twice, high, from elsewhere in the air
    for at, deg, gain in [(7.2, 10, 0.13), (23.6, 9, 0.11), (44.5, 10, 0.10)]:
        place(yunluo(m.f(deg), 2.2, gain), at)

    # the voice of the place itself: one long breath, mostly air, very high
    place(xiao(m.f(10), 8 * beat, 0.13, vibrato=0.35, breathiness=1.6, attack=0.8), 4.0)
    place(xiao(m.f(8), 7 * beat, 0.11, vibrato=0.35, breathiness=1.6, attack=0.8), 20.0)
    place(xiao(m.f(10), 9 * beat, 0.10, vibrato=0.35, breathiness=1.6, attack=0.9), 36.0)

    place(drone(m.f(-5), total, 0.034, beat=0.02, noise=0.12), 0.0)
    return bus, total


# ---------------------------------------------------------------- chapter pieces

def piece_book_one() -> tuple[np.ndarray, float]:
    """第一回. 甄士隐的园子、葫芦庙、青埂峰，一段「好了歌」式的开场：yu on D, slow, and
    led by the guqin, which is the instrument that sounds like someone thinking. The tune is
    deliberately unresolved at the end -- this chapter opens a wound, it does not close one."""
    m = BOOK_ONE
    bpm = 50.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 12
    total = bars * bar + 4.6
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # The guqin states a four-note phrase and leaves it hanging; a single high bowl answers
    # once per couplet, from somewhere off the path. The phrase keeps coming back to the
    # tonic -- an earlier version leaned on the fourth degree and the piece came out
    # sounding as if it were in another key altogether.
    phrase = [
        (0, 0.0, 0, 2.5), (0, 3.0, 2, 2.5),
        (2, 0.5, 0, 2.0), (2, 2.5, 2, 1.5), (2, 3.5, 1, 3.0),
        (4, 0.0, 0, 2.0), (4, 2.5, 0, 3.0),
        (6, 0.5, 3, 2.0), (6, 2.5, 1, 2.0), (6, 3.5, 0, 3.0),
        (8, 0.0, 0, 3.0), (8, 3.0, 2, 3.0),
        (10, 0.0, 1, 2.0), (10, 2.0, 0, 2.0), (10, 3.5, 4, 4.0),
    ]
    for bar_i, beat_i, deg, length in phrase:
        place(qin(m.f(deg), length * beat + 1.0, 0.28), bar_i * bar + beat_i * beat)

    for bar_i, deg in [(1, 7), (5, 6), (9, 5)]:
        place(qing(m.f(deg), 5.0, 0.20), bar_i * bar + 2 * beat)

    # a flute enters only in the last third, and it is the wrong mode for the occasion:
    # it keeps reaching for a note that is not there
    place(xiao(m.f(6), 5 * beat, 0.12, vibrato=0.45, breathiness=1.4, attack=0.6), 8 * bar)
    place(xiao(m.f(5), 4 * beat, 0.10, vibrato=0.45, breathiness=1.4, attack=0.6), 10 * bar)

    place(drone(m.f(-5), total, 0.032, beat=0.04), 0.0)
    return bus, total


def piece_book_two() -> tuple[np.ndarray, float]:
    """第二回. 冷子兴在扬州谋生、贾雨村复职赴任：zhi on C, quicker than the first book,
    and led by the pipa in a steady walking figure. This is the chapter about business --
    somebody arranging a journey -- so the music keeps moving without arriving anywhere."""
    m = BOOK_TWO
    bpm = 68.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 14
    total = bars * bar + 3.2
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # The walking figure: eighth notes that never quite settle, because the man in this
    # chapter never quite settles either. The tonic carries the downbeat of every bar --
    # an earlier figure ran on the third degree and the piece came out in the wrong key
    # entirely, which is what happens when a busy tune never lands on its own root.
    figure = [0, 2, 3, 2, 0, 0, 2, 3]
    eighth = beat / 2
    for bar_i in range(bars):
        low = bar_i % 4 == 3
        for j, deg in enumerate(figure):
            d = deg - 5 if low else deg
            gain = 0.06 + 0.02 * (j % 2)
            if j == 0:
                gain = 0.10                      # the root is always the loudest note
            place(pipa(m.f(d), 0.5, gain), bar_i * bar + j * eighth)

    # a zheng answers every second bar with a rolled figure, and it states the root first
    for bar_i in range(0, bars, 2):
        at = bar_i * bar
        for j, deg in enumerate((0, 2, 4)):
            place(zheng(m.f(deg - 5), 1.6, 0.13 if j == 0 else 0.10), at + j * 0.16)

    # one flute phrase, placed where the plan is made
    place(xiao(m.f(5), 4 * beat, 0.13, attack=0.12), 4 * bar)
    place(xiao(m.f(4), 3 * beat, 0.11, attack=0.12), 9 * bar)

    place(drone(m.f(-5), total, 0.024), 0.0)
    return bus, total


def piece_book_three() -> tuple[np.ndarray, float]:
    """第三回. 黛玉进京、荣国府初至：gong on E, the settled mode and the highest tonic of
    the ten, because this is the chapter where the world finally arrives. The xiao leads,
    and it is the only chapter piece that reaches its octave -- the arrival earns it."""
    m = BOOK_THREE
    bpm = 62.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 14
    total = bars * bar + 3.8
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # A rising line: the melody climbs a degree every couplet until it stands on the octave
    # in the last two bars, which is the whole shape of arriving somewhere. It starts and
    # ends on the tonic, so the key is stated rather than implied.
    line = [
        (0, 0.0, 0, 2.0), (0, 2.5, 2, 2.0),
        (2, 0.0, 0, 2.0), (2, 2.5, 3, 2.0),
        (4, 0.0, 0, 2.0), (4, 2.5, 4, 2.0),
        (6, 0.0, 0, 1.5), (6, 2.0, 4, 1.0), (6, 3.0, 5, 3.0),
        (8, 0.0, 0, 2.0), (8, 2.5, 2, 2.0),
        (10, 0.0, 0, 2.0), (10, 2.5, 5, 2.5),
        (12, 0.0, 0, 3.0), (12, 3.0, 5, 4.0),
    ]
    for bar_i, beat_i, deg, length in line:
        place(xiao(m.f(deg), length * beat + 0.35, 0.26), bar_i * bar + beat_i * beat)

    # the zheng grounds it an octave below, in a steady two-beat pulse
    for bar_i in range(bars):
        place(zheng(m.f(-5), 1.8, 0.13), bar_i * bar)
        place(zheng(m.f(-2), 1.4, 0.09), bar_i * bar + 2 * beat)

    place(qing(m.f(5), 4.5, 0.16), 12 * bar)
    place(drone(m.f(-5), total, 0.026), 0.0)
    return bus, total


def piece_book_four() -> tuple[np.ndarray, float]:
    """第四回. 薛家进京、争夺金陵十二钗、官场交结：shang on Eb, the lowest tonic of the
    ten and the greyest mode. The qin and the bowl trade phrases at a slow, level pace --
    this chapter is an argument, and arguments do not have melodies, they have positions."""
    m = BOOK_FOUR
    bpm = 46.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 12
    total = bars * bar + 4.4
    bus = np.zeros(int(total * SR))
    place = placer(bus)

    # Two voices arguing: the qin says a phrase, the bowl answers a third below it, then
    # the qin says it again a degree higher. The pair never agrees on the tonic.
    low = [
        (0, 0.0, 0, 2.5), (0, 3.0, 3, 2.5),
        (3, 0.0, 2, 2.0), (3, 2.5, 0, 3.0),
        (6, 0.0, 1, 2.0), (6, 2.5, 4, 2.0), (6, 3.5, 3, 3.0),
        (9, 0.0, 2, 2.5), (9, 3.0, 0, 4.0),
    ]
    for bar_i, beat_i, deg, length in low:
        place(qin(m.f(deg), length * beat + 0.9, 0.26), bar_i * bar + beat_i * beat)
    answers = [(1, -3), (4, -2), (7, -3), (10, -5)]
    for bar_i, deg in answers:
        place(qing(m.f(deg), 4.4, 0.22), bar_i * bar + beat)

    # a low drone underneath, the one thing both sides stand on
    place(drone(m.f(-5), total, 0.040, beat=0.03), 0.0)
    # and a single distant strike at the very end, like a gavel
    place(simple_lowpass(qing(m.f(0), 5.0, 0.24), 700), bars * bar - 1.0)
    return bus, total


# ---------------------------------------------------------------- assembly

# Per-piece target loudness, room, top roll-off and width. The targets are deliberately
# NOT equal: a night scene should sit under the one before it -- that difference is part
# of what tells the reader where they are. Effects are normalised nearer the music than
# they used to be (see EFFECT_DB below) so a footfall is noticed rather than flinched at.
PIECES = {
    'bgm-garden':   dict(fn=piece_garden,   rms=-24.0, wet=0.26, soften=6800, width=0.55, ir=2.6),
    'bgm-street':   dict(fn=piece_street,   rms=-24.0, wet=0.20, soften=8500, width=0.70, ir=1.9),
    'bgm-water':    dict(fn=piece_water,    rms=-25.0, wet=0.30, soften=5200, width=0.80, ir=2.9),
    'bgm-night':    dict(fn=piece_night,    rms=-27.5, wet=0.34, soften=4200, width=0.45, ir=3.4),
    'bgm-interior': dict(fn=piece_interior, rms=-25.0, wet=0.24, soften=7200, width=0.50, ir=2.2),
    'bgm-myth':     dict(fn=piece_myth,     rms=-27.5, wet=0.38, soften=5600, width=0.85, ir=3.8),
    # The four chapter pieces sit a little under the scene pieces: they are the ground the
    # story stands on, and they should never crowd out what the reader is looking at.
    'bgm-book-one':   dict(fn=piece_book_one,   rms=-26.0, wet=0.30, soften=5000, width=0.60, ir=3.0),
    'bgm-book-two':   dict(fn=piece_book_two,   rms=-25.0, wet=0.22, soften=7400, width=0.65, ir=2.1),
    'bgm-book-three': dict(fn=piece_book_three, rms=-25.0, wet=0.28, soften=6600, width=0.75, ir=2.6),
    'bgm-book-four':  dict(fn=piece_book_four,  rms=-27.0, wet=0.34, soften=4600, width=0.50, ir=3.2),
}

# Effects sat 12 dB above the music, which is why every footfall jumped out of the quiet.
# These sit about 4 dB above their own pieces' target and are then trimmed by the sfx bus.
EFFECT_DB = {
    'sfx-step-board': -21.0,
    'sfx-step-stone': -21.0,
    'sfx-step-earth': -23.0,
    'sfx-oar': -22.0,
    'sfx-tap': -20.0,
    'sfx-door': -19.0,
    'sfx-page': -21.0,
    'sfx-bell': -20.0,
    'sfx-chair': -22.0,
}

EFFECTS = {
    'sfx-step-board': lambda: fx_step('board', 0),
    'sfx-step-stone': lambda: fx_step('stone', 1),
    'sfx-step-earth': lambda: fx_step('earth', 2),
    'sfx-oar': fx_oar,
    'sfx-tap': fx_tap,
    'sfx-door': fx_door,
    'sfx-page': fx_page,
    'sfx-bell': fx_bell,
    'sfx-chair': fx_chair,
}


def write_ogg(stereo: np.ndarray, path: Path, bitrate: int) -> None:
    pcm = np.clip(stereo, -1, 1)
    pcm16 = (pcm * 32767).astype('<i2')
    wav_path = path.with_suffix('.wav')
    with wave.open(str(wav_path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm16.tobytes())
    # libvorbis in this Homebrew ffmpeg is flagged experimental; libopus is not, and
    # opus-in-ogg decodes in every browser the game targets.
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(wav_path),
                    '-c:a', 'libopus', '-b:a', f'{bitrate}k', '-f', 'ogg', str(path)], check=True)
    wav_path.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for name, cfg in PIECES.items():
        if args.only and name not in args.only:
            continue
        bus, total = cfg['fn']()
        bus = normalize(bus, 10 ** (cfg['rms'] / 20))
        bus = reverb(bus, make_ir(cfg['ir']), wet=cfg['wet'])
        bus = soften(bus, cfg['soften'])
        bus = loop_seam(bus)
        stereo = to_stereo(bus, cfg['width'])
        # fade only long enough to kill a click at the seam; a long fade makes the
        # loop breathe once per cycle
        fade = int(0.15 * SR)
        stereo[-fade:] *= np.linspace(1, 0, fade)[:, None]
        stereo[:fade] *= np.linspace(0, 1, fade)[:, None]
        path = OUT / f'{name}.ogg'
        write_ogg(stereo, path, 56)
        made.append((name, path.stat().st_size, total))
    for name, fn in EFFECTS.items():
        if args.only and name not in args.only:
            continue
        sig = normalize(fn(), 10 ** (EFFECT_DB[name] / 20))
        sig = reverb(sig, make_ir(1.6), wet=0.14 if name.startswith('sfx-step') else 0.2)
        path = OUT / f'{name}.ogg'
        write_ogg(to_stereo(sig, 0.4), path, 40)
        made.append((name, path.stat().st_size, len(sig) / SR))
    for name, size, dur in made:
        print(f'{name:16s} {dur:6.1f}s  {size/1024:7.1f} KB')
    print(f'build_audio: {len(made)} files in {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
