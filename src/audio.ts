/**
 * A small Web Audio engine for the soundtrack.
 *
 * It deliberately does not hang off Phaser's sound manager: GameMap rebuilds the whole
 * Phaser.Game whenever the story moves to another map, which would re-fetch and re-decode
 * every audio file each time. One AudioContext owned here survives the whole session, and
 * each file is decoded once.
 *
 * Everything is quiet on purpose. The pieces sit around -30 dBFS RMS and the master gains
 * start at half; a reader who wants silence gets it from the settings panel, and the
 * choice is remembered.
 */

export type AudioPrefs = { bgm: number; sfx: number };

const PREFS_KEY = 'honglou.audio.v1';
const DEFAULTS: AudioPrefs = { bgm: 0.5, sfx: 0.75 };

/** Map a stage theme onto one of the four pieces. Anything unlisted gets the garden. */
const BGM_BY_THEME: Record<string, string> = {
  garden: 'bgm-garden',
  river: 'bgm-garden',
  // the street reuses the garden piece on purpose: it is the same daylight, and a fifth
  // track would only thin the ones that matter
  street: 'bgm-garden',
  day: 'bgm-garden',
  night: 'bgm-night',
  interior: 'bgm-interior',
  formal: 'bgm-interior',
  myth: 'bgm-myth',
  dream: 'bgm-myth',
  ruins: 'bgm-myth',
};

const FADE_SECONDS = 1.4;
const MIN_STEP_GAP = 0.26;

function readPrefs(): AudioPrefs {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    if (!raw) return { ...DEFAULTS };
    const parsed = JSON.parse(raw) as Partial<AudioPrefs>;
    return {
      bgm: clamp01(typeof parsed.bgm === 'number' ? parsed.bgm : DEFAULTS.bgm),
      sfx: clamp01(typeof parsed.sfx === 'number' ? parsed.sfx : DEFAULTS.sfx),
    };
  } catch { return { ...DEFAULTS }; }
}

function clamp01(value: number) { return Math.max(0, Math.min(1, value)); }

class AudioEngine {
  private ctx: AudioContext | null = null;
  private master: GainNode | null = null;
  private bgmBus: GainNode | null = null;
  private sfxBus: GainNode | null = null;
  private buffers = new Map<string, AudioBuffer>();
  private loading = new Map<string, Promise<AudioBuffer>>();
  private current: { name: string; gain: GainNode; source: AudioBufferSourceNode } | null = null;
  private prefs: AudioPrefs = readPrefs();
  private unlocked = false;
  private wantedTheme: string | null = null;
  private warmQueue: string[] = [];
  private lastStep = 0;
  private failed = false;

  /** Browsers hold the context suspended until a gesture; call this from the first one. */
  unlock() {
    if (this.unlocked) { void this.ctx?.resume(); return; }
    try {
      const ctx = new AudioContext();
      const master = ctx.createGain();
      master.gain.value = 0.9;
      master.connect(ctx.destination);
      const bgmBus = ctx.createGain();
      bgmBus.gain.value = this.prefs.bgm;
      bgmBus.connect(master);
      const sfxBus = ctx.createGain();
      sfxBus.gain.value = this.prefs.sfx;
      sfxBus.connect(master);
      this.ctx = ctx; this.master = master; this.bgmBus = bgmBus; this.sfxBus = sfxBus;
      this.unlocked = true;
      // effects a stage asked for before the gesture now decode
      const queued = this.warmQueue.splice(0);
      for (const name of queued) this.load(name);
      void ctx.resume().then(() => { if (this.wantedTheme) this.startBgm(this.wantedTheme); });
    } catch {
      this.failed = true;   // no Web Audio (very old browser): the game still runs silent
    }
  }

  get ready() { return this.unlocked && !this.failed; }

  private load(name: string): Promise<AudioBuffer> | null {
    if (!this.ctx) return null;
    const cached = this.buffers.get(name);
    if (cached) return Promise.resolve(cached);
    const inFlight = this.loading.get(name);
    if (inFlight) return inFlight;
    const url = `${import.meta.env.BASE_URL}assets/audio/${name}.ogg`.replace(/\/+/g, '/');
    const job = fetch(url)
      .then(response => {
        if (!response.ok) throw new Error(`${url} -> ${response.status}`);
        return response.arrayBuffer();
      })
      .then(data => this.ctx!.decodeAudioData(data))
      .then(buffer => { this.buffers.set(name, buffer); return buffer; })
      .catch(error => { console.warn(`audio: ${name} unavailable`, error); throw error; })
      .finally(() => { this.loading.delete(name); });
    this.loading.set(name, job);
    return job;
  }

  /** Crossfade to the piece that belongs to this theme. Same theme is a no-op. */
  setTheme(theme: string) {
    const name = BGM_BY_THEME[theme] ?? BGM_BY_THEME.garden;
    this.wantedTheme = name;
    this.startBgm(name);
  }

  /** wantedTheme always holds a piece name, never a theme name -- otherwise turning the
   * music back on would map "bgm-myth" through the theme table and land on the garden. */
  private startBgm(name: string) {
    if (!this.ready) return;             // unlock() replays the request once the context exists
    if (this.current?.name === name) return;
    if (this.prefs.bgm <= 0) { this.stopBgm(); return; }
    const job = this.load(name);
    if (!job) return;
    job.then(buffer => {
      if (this.wantedTheme !== name || !this.ctx || !this.bgmBus) return;
      const ctx = this.ctx;
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.loop = true;
      const gain = ctx.createGain();
      gain.gain.value = 0;
      source.connect(gain).connect(this.bgmBus);
      const now = ctx.currentTime;
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(1, now + FADE_SECONDS);
      source.start();
      const previous = this.current;
      this.current = { name, gain, source };
      if (previous) {
        const old = previous.gain.gain;
        old.setValueAtTime(old.value, now);
        old.linearRampToValueAtTime(0, now + FADE_SECONDS);
        // stop only after the fade has finished, or the cut is audible
        previous.source.stop(now + FADE_SECONDS + 0.05);
      }
    }).catch(() => { /* a missing piece must never break the reading flow */ });
  }

  stopBgm() {
    if (!this.ctx || !this.current) return;
    const now = this.ctx.currentTime;
    const { gain, source } = this.current;
    gain.gain.cancelScheduledValues(now);
    gain.gain.setValueAtTime(gain.gain.value, now);
    gain.gain.linearRampToValueAtTime(0, now + 0.4);
    source.stop(now + 0.45);
    this.current = null;
  }

  /** Fetch and decode ahead of time so the first play of this effect has no gap.
   * Called while a stage preloads, which is before the reader has touched anything;
   * without the context there is nothing to decode into, so the names wait in a queue
   * and unlock() drains it. */
  warm(name: string) {
    if (!this.ctx) {
      if (!this.warmQueue.includes(name)) this.warmQueue.push(name);
      return;
    }
    this.load(name);
  }

  /** One-shot effect. `gap` throttles repeats (footsteps, creaking poles). */
  play(name: string, gap = 0) {
    if (!this.ready || this.prefs.sfx <= 0) return;
    const now = this.ctx!.currentTime;
    if (gap > 0 && now - this.lastStep < gap) return;
    this.lastStep = now;
    const job = this.load(name);
    if (!job) return;
    job.then(buffer => {
      if (!this.ctx || !this.sfxBus) return;
      const source = this.ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(this.sfxBus);
      source.start();
    }).catch(() => { /* silent is an acceptable outcome for an effect */ });
  }

  /** A footfall, alternating boards and stone so a walk does not machine-gun. */
  step(variant: 0 | 1) {
    this.play(variant ? 'sfx-step-b' : 'sfx-step-a', MIN_STEP_GAP);
  }

  setPrefs(next: Partial<AudioPrefs>) {
    const now = this.ctx?.currentTime ?? 0;
    this.prefs = {
      bgm: clamp01(next.bgm ?? this.prefs.bgm),
      sfx: clamp01(next.sfx ?? this.prefs.sfx),
    };
    try { localStorage.setItem(PREFS_KEY, JSON.stringify(this.prefs)); } catch { /* private mode */ }
    if (this.bgmBus) this.bgmBus.gain.setTargetAtTime(this.prefs.bgm, now, 0.08);
    if (this.sfxBus) this.sfxBus.gain.setTargetAtTime(this.prefs.sfx, now, 0.05);
    // turning the music off should fade the piece out, not mute a running one
    if (this.prefs.bgm <= 0) this.stopBgm();
    else if (this.wantedTheme) this.startBgm(this.wantedTheme);
  }

  getPrefs(): AudioPrefs { return { ...this.prefs }; }
}

export const audio = new AudioEngine();

// QA hook: the browser tests drive the soundtrack through this handle, the same way
// they reach the stage through window.__mapScene.
declare global { interface Window { __audio?: AudioEngine } }
if (typeof window !== 'undefined') window.__audio = audio;
