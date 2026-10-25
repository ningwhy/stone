#!/usr/bin/env python3
"""Synthesize the soundtrack: four quiet guqin-era pieces and the effects that go with them.

Everything is built from oscillators and filtered noise at 44.1 kHz, then written as Ogg
Vorbis next to the other art. There is no sample library here on purpose: the score is
pentatonic and slow, the instruments are a handful of partials each, and a generated file
is a few kilobytes where a sampled pack would be tens of megabytes.

Instruments
  zheng  plucked zither   - additive partials, 1/n amplitude, fast per-partial decay
  xiao   bamboo flute     - subtractive tone, breath noise, vibrato, slow attack
  qin    guqin            - low plucked tone with scrape, long body
  pipa   pear lute        - bright plucked tone, short decay, tremolo
  qing   singing bowl     - inharmonic metal partials, long ring

Effects
  step    footfall on boards or stone
  tap     UI chime (qing strike)
  door    wooden door: squeak then a low thud
  page    turning a page
  bell    distant temple bell
  chair   sedan poles creaking

Usage:  python3 scripts/build_audio.py [--only NAME ...]
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'public/assets/audio'
SR = 44100

# D-gong pentatonic. Every piece stays inside these five degrees; the tunes are slow,
# mostly stepwise, and leave rests on purpose -- 红楼 is a quiet house.
DEG = {
    'D3': 146.832, 'E3': 164.814, 'F#3': 184.997, 'A3': 220.000, 'B3': 246.942,
    'D4': 293.665, 'E4': 329.628, 'F#4': 369.994, 'A4': 440.000, 'B4': 493.883,
    'D5': 587.330, 'E5': 659.255, 'F#5': 739.989, 'A5': 880.000, 'B5': 987.767,
    'D6': 1174.66,
}


def note(name: str) -> float:
    return DEG[name]


# ---------------------------------------------------------------- envelopes

def exp_env(t: np.ndarray, attack: float, decay: float) -> np.ndarray:
    """Percussive envelope: linear attack then exponential decay to zero."""
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-6))
    env = a * d
    return env


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

def zheng(freq: float, dur: float, gain: float = 1.0, brightness: float = 1.0) -> np.ndarray:
    """Additive plucked string: 18 partials, 1/n tilt, faster decay higher up."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    partials = 18
    for k in range(1, partials + 1):
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
        pluck = np.random.default_rng(7).standard_normal(n)
        pluck[: max(2, int(0.004 * SR))] *= np.linspace(1, 0, max(2, int(0.004 * SR)))
        out += 0.05 * gain * pluck
    return out * brightness


def xiao(freq: float, dur: float, gain: float = 1.0, vibrato: float = 1.0) -> np.ndarray:
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
    env = flute_env(t, 0.09, 0.22, 1.0)
    return gain * env * (tone + breath)


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
    n = len(base)
    trem = 1 + 0.09 * np.sin(2 * np.pi * 11.5 * np.arange(n) / SR)
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


def simple_band(x: np.ndarray, center: float, q: float) -> np.ndarray:
    """One-pole-ish resonant band via FFT; used for breath, footsteps, wood."""
    n = len(x)
    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    response = 1 / (1 + ((freqs - center) / (center / max(q, 0.5))) ** 2)
    return np.fft.irfft(spec * response, n)


# ---------------------------------------------------------------- effects

def fx_step(variant: int) -> np.ndarray:
    """Footfall: short filtered noise. Boards ring, stone does not."""
    dur = 0.16
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(101 + variant)
    noise = rng.standard_normal(n)
    if variant == 0:      # boards
        body = simple_band(noise, 760, 2.4)
        knock = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045)
        sig = body * 0.9 + knock * 0.25
    else:                 # stone
        body = simple_band(noise, 320, 1.8)
        sig = body * 1.0
    return sig * exp_env(t, 0.004, 0.055) * 0.9


def fx_tap() -> np.ndarray:
    """UI chime: a small qing, high and short."""
    return qing(note('D5'), 1.6, 0.5) * 0.8


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
    sig = qing(note('D3'), 6.0, 0.85)
    # distance: roll the top off and thin it out
    return simple_lowpass(sig, 900) * 0.75


def fx_chair() -> np.ndarray:
    """Sedan poles creaking under load: two dry wood rubs."""
    dur = 1.1
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(505)
    out = np.zeros(n)
    for i, (at, f0) in enumerate([(0.06, 150), (0.42, 128)]):
        seg = np.zeros(n)
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

def make_ir(seconds: float = 2.6, decay: float = 2.4) -> np.ndarray:
    """A small hall: exponentially decaying noise with a few early reflections."""
    n = int(seconds * SR)
    rng = np.random.default_rng(909)
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


# ---------------------------------------------------------------- the pieces

def render(fn, seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SR))


def piece_garden() -> tuple[np.ndarray, float]:
    """Daytime in the garden: zheng arpeggios under a slow xiao line. The default."""
    bpm = 52.0
    beat = 60.0 / bpm
    bars = 16
    bar = 4 * beat
    total = bars * bar + 3.0
    bus = np.zeros(int(total * SR))

    def place(sig: np.ndarray, at: float, gain: float = 1.0) -> None:
        i = int(at * SR)
        if i >= len(bus):
            return
        end = min(len(bus), i + len(sig))
        bus[i:end] += sig[:end - i] * gain

    # xiao melody: four phrases, mostly stepwise, ending home on D.
    # (bar, beat-within-bar, note, length-in-beats)
    melody = [
        (0, 0.0, 'D4', 1.5), (0, 1.5, 'E4', 1.0), (0, 2.5, 'F#4', 1.0), (0, 3.5, 'A4', 2.0),
        (2, 1.0, 'B4', 1.0), (2, 2.0, 'A4', 1.0), (2, 3.0, 'F#4', 2.0),
        (4, 1.0, 'E4', 1.0), (4, 2.0, 'D4', 2.5),
        (5, 0.5, 'D4', 1.0), (5, 1.5, 'E4', 1.0), (5, 2.5, 'F#4', 1.0), (5, 3.5, 'A4', 2.0),
        (7, 1.0, 'B4', 1.0), (7, 2.0, 'D5', 1.0), (7, 3.0, 'B4', 2.0),
        (9, 1.0, 'A4', 1.0), (9, 2.0, 'F#4', 1.0), (9, 3.0, 'E4', 2.0),
        (11, 1.0, 'D4', 1.0), (11, 2.0, 'E4', 1.0), (11, 3.0, 'F#4', 2.0),
        (13, 1.0, 'A4', 1.5), (13, 2.5, 'B4', 1.0), (13, 3.5, 'A4', 1.5),
        (15, 1.0, 'F#4', 1.0), (15, 2.0, 'E4', 1.0), (15, 3.0, 'D4', 3.5),
    ]
    for bar_i, beat_i, name, length in melody:
        place(xiao(note(name), length * beat + 0.4, 0.30), bar_i * bar + beat_i * beat)

    # zheng: one arpeggio on bar 1 as the opening figure, then sparse answers.
    place(zheng(note('D3'), 2.2, 0.30), 0.0)
    place(zheng(note('A3'), 2.2, 0.26), 0.30)
    place(zheng(note('D4'), 2.4, 0.22), 0.60)
    for bar_i in (2, 4, 6, 8, 10, 12, 14):
        if bar_i % 4 == 2:
            for j, nm in enumerate(('A3', 'D4', 'F#4')):
                place(zheng(note(nm), 1.8, 0.16), bar_i * bar + j * 0.34)
        elif bar_i % 4 == 0:
            place(zheng(note('D4'), 2.0, 0.17), bar_i * bar + 0.4)
            place(zheng(note('B4'), 1.6, 0.12), bar_i * bar + 0.8)

    # a sustained pad an octave under everything, barely there
    pad_n = int(total * SR)
    t = np.arange(pad_n) / SR
    pad = (np.sin(2 * np.pi * note('D3') * t) * 0.5
           + np.sin(2 * np.pi * note('A3') * t) * 0.3
           + np.sin(2 * np.pi * note('D4') * t) * 0.16)
    pad *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)
    bus += pad * 0.035

    # loop point: the last note is still ringing when the first bar returns
    return bus, total


def piece_night() -> tuple[np.ndarray, float]:
    """Night: the same scale, an octave of air between the notes, one bell."""
    bpm = 46.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 12
    total = bars * bar + 4.0
    bus = np.zeros(int(total * SR))

    def place(sig: np.ndarray, at: float, gain: float = 1.0) -> None:
        i = int(at * SR)
        if i >= len(bus):
            return
        end = min(len(bus), i + len(sig))
        bus[i:end] += sig[:end - i] * gain

    melody = [
        (1, 0.0, 'A3', 2.0), (1, 2.0, 'B3', 2.0),
        (3, 0.0, 'D4', 3.0),
        (5, 1.0, 'E4', 1.5), (5, 2.5, 'D4', 2.0),
        (7, 0.0, 'A3', 4.0),
        (9, 0.0, 'B3', 1.5), (9, 1.5, 'D4', 1.5), (9, 3.0, 'E4', 3.0),
        (11, 0.5, 'D4', 4.5),
    ]
    for bar_i, beat_i, name, length in melody:
        place(xiao(note(name), length * beat + 0.6, 0.26, vibrato=0.7), bar_i * bar + beat_i * beat)

    place(qing(note('D3'), 5.0, 0.42), 0.4)
    place(qing(note('A3'), 4.5, 0.26), bars * bar - 2.0)

    for bar_i in (0, 4, 8):
        place(qin(note('D3'), 3.6, 0.20), bar_i * bar + 0.2)
    place(qin(note('A3'), 3.2, 0.15), 6 * bar + 0.4)

    pad_n = int(total * SR)
    t = np.arange(pad_n) / SR
    pad = np.sin(2 * np.pi * note('D3') * t) * 0.6 + np.sin(2 * np.pi * note('A3') * t) * 0.4
    pad *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t)
    bus += pad * 0.03
    return bus, total


def piece_interior() -> tuple[np.ndarray, float]:
    """Inside the house: guqin single tones, a pipa answer, nothing hurried."""
    bpm = 44.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 12
    total = bars * bar + 4.5
    bus = np.zeros(int(total * SR))

    def place(sig: np.ndarray, at: float, gain: float = 1.0) -> None:
        i = int(at * SR)
        if i >= len(bus):
            return
        end = min(len(bus), i + len(sig))
        bus[i:end] += sig[:end - i] * gain

    # qin states the phrase, pipa answers two bars later, a third higher
    qin_notes = [
        (0, 0.0, 'D3', 3.0), (0, 3.0, 'A3', 2.5),
        (2, 0.5, 'B3', 2.0), (2, 2.5, 'A3', 2.0),
        (4, 0.0, 'F#3', 2.5), (4, 2.5, 'E3', 2.5),
        (6, 0.0, 'D3', 4.0),
        (8, 0.0, 'A3', 2.0), (8, 2.0, 'B3', 1.5), (8, 3.5, 'D4', 2.5),
        (10, 0.0, 'A3', 2.0), (10, 2.0, 'F#3', 2.0),
    ]
    for bar_i, beat_i, name, length in qin_notes:
        place(qin(note(name), length * beat + 0.8, 0.34), bar_i * bar + beat_i * beat)

    pipa_notes = [
        (3, 1.0, 'D4', 1.0), (3, 2.0, 'E4', 1.0), (3, 3.0, 'F#4', 1.0),
        (5, 1.0, 'A4', 1.0), (5, 2.0, 'B4', 1.0), (5, 3.0, 'A4', 1.0),
        (9, 1.0, 'D5', 1.0), (9, 2.0, 'B4', 1.0), (9, 3.0, 'A4', 1.0),
        (11, 1.0, 'F#4', 1.0), (11, 2.0, 'E4', 1.0), (11, 3.0, 'D4', 2.0),
    ]
    for bar_i, beat_i, name, length in pipa_notes:
        place(pipa(note(name), length * beat + 0.3, 0.13), bar_i * bar + beat_i * beat)

    place(xiao(note('D4'), 6 * beat, 0.12), 6 * bar)
    return bus, total


def piece_myth() -> tuple[np.ndarray, float]:
    """The mythic scenes: bowls and a bare flute, almost no movement."""
    bpm = 40.0
    beat = 60.0 / bpm
    bar = 4 * beat
    bars = 10
    total = bars * bar + 5.0
    bus = np.zeros(int(total * SR))

    def place(sig: np.ndarray, at: float, gain: float = 1.0) -> None:
        i = int(at * SR)
        if i >= len(bus):
            return
        end = min(len(bus), i + len(sig))
        bus[i:end] += sig[:end - i] * gain

    bowls = [
        (0.0, 'D3', 0.5), (1.5, 'A3', 0.34), (3.0, 'D4', 0.24),
        (5.0, 'B3', 0.3), (6.5, 'E4', 0.2),
        (9.0, 'D3', 0.44), (10.5, 'F#4', 0.2),
        (13.0, 'A3', 0.34), (14.5, 'D4', 0.26),
        (17.0, 'B3', 0.3), (18.5, 'A4', 0.22),
        (21.0, 'D4', 0.3), (22.5, 'A3', 0.3), (24.0, 'D3', 0.42),
    ]
    for at, name, gain in bowls:
        place(qing(note(name), 5.5, gain), at * beat)

    place(xiao(note('A4'), 8 * beat, 0.20, vibrato=0.5), 8 * beat)
    place(xiao(note('D5'), 8 * beat, 0.16, vibrato=0.5), 24 * beat)
    place(xiao(note('A4'), 6 * beat, 0.14, vibrato=0.5), 32 * beat)
    return bus, total


# ---------------------------------------------------------------- assembly

PIECES = {
    'bgm-garden': (piece_garden, -25.0),
    'bgm-night': (piece_night, -26.0),
    'bgm-interior': (piece_interior, -27.0),
    'bgm-myth': (piece_myth, -27.0),
}

EFFECTS = {
    'sfx-step-a': lambda: fx_step(0),
    'sfx-step-b': lambda: fx_step(1),
    'sfx-tap': fx_tap,
    'sfx-door': fx_door,
    'sfx-page': fx_page,
    'sfx-bell': fx_bell,
    'sfx-chair': fx_chair,
}


def write_ogg(stereo: np.ndarray, path: Path, quality: int) -> None:
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
                    '-c:a', 'libopus', '-b:a', f'{quality * 16}k', '-f', 'ogg', str(path)], check=True)
    wav_path.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    ir = make_ir()
    made = []
    for name, (fn, rms) in PIECES.items():
        if args.only and name not in args.only:
            continue
        bus, total = fn()
        bus = normalize(bus, 10 ** (rms / 20))
        bus = reverb(bus, ir, wet=0.30)
        if name == 'bgm-garden':
            bus = soften(bus, 6500)   # the zither is the brightest voice; keep it warm
        bus = loop_seam(bus)
        stereo = to_stereo(bus)
        # fade only long enough to kill a click at the seam; a long fade makes the
        # loop breathe once per cycle
        fade = int(0.15 * SR)
        stereo[-fade:] *= np.linspace(1, 0, fade)[:, None]
        stereo[:fade] *= np.linspace(0, 1, fade)[:, None]
        path = OUT / f'{name}.ogg'
        write_ogg(stereo, path, 5)
        made.append((name, path.stat().st_size, total))
    for name, fn in EFFECTS.items():
        if args.only and name not in args.only:
            continue
        sig = normalize(fn(), 10 ** (-15.0 / 20))
        sig = reverb(sig, ir, wet=0.12 if name.startswith('sfx-step') else 0.2)
        path = OUT / f'{name}.ogg'
        write_ogg(to_stereo(sig), path, 6)
        made.append((name, path.stat().st_size, len(sig) / SR))
    for name, size, dur in made:
        print(f'{name:16s} {dur:6.1f}s  {size/1024:7.1f} KB')
    print(f'build_audio: {len(made)} files in {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
