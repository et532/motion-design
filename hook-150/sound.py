# .venv/bin/python -I hook-150/sound.py   (from ~/motion-design; assemble.py runs it) -> hook-150/out/audio.wav
# The music and the typing for the whole cut, placed from hook-150/out/timeline.json (where each shot starts, every
# typed key and the shots' beats on the film's clock). Synthesized like the main film's sound.py (same instruments):
# warm but upbeat; 118 BPM, D A Bm G.
#   the hook: a pad that opens up, a quiet plucked arpeggio and a heartbeat kick from "150 people" (with a soft hit), a
#             swell into a low boom on the "rest?" zoom, a shimmer as the white dots fill in
#   Vince's "Meeting people is easy / hard": darker, the arpeggio and a ticking pulse
#   "Introducing Peepl": a riser into a hit on the cut to "Peepl", then the groove: four-on-the-floor kick, clap on 2 and
#             4, offbeat hats, a bouncing eighth-note bass, the plucked arpeggio
#   the memory playing back: half-time, softer (felt notes); a bloom when play is tapped
#   the last scene: blooms as the discs and pills come in, a swell into a boom on "Peepl", the full chord, ringing out
#   typing: the user's typing recording (assets/sound/typing.wav) at its own speed, quietly, under each run of typing,
#             softened a little and given a touch of room so it sits in
import json
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt

TL = json.load(open('hook-150/out/timeline.json'))
SEG = {s['name']: s for s in TL['segments']}
SR, DUR = 44100, TL['total']
rng = np.random.default_rng(7)
out = np.zeros(int(SR * (DUR + 3)))
keys_out = np.zeros_like(out)


def lp(x, fc, n=2): return sosfilt(butter(n, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, n=2): return sosfilt(butter(n, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, n=2): return sosfilt(butter(n, [lo, hi], 'band', fs=SR, output='sos'), x)
def put(t, x, g=1.0, buf=None):
    buf = out if buf is None else buf
    if t is None: return
    i = int(t * SR)
    if i < 0:
        x = x[-i:]; i = 0
    if i >= len(buf): return
    buf[i:i + len(x)] += x[:len(buf) - i] * g
def tt(d): return np.arange(int(SR * d)) / SR
def noise(d): return rng.standard_normal(int(SR * d))
def kick():
    t = tt(0.4); f = 46 + 70 * np.exp(-t * 26); return lp(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9), 180)
def pad(freqs, d, a=0.6, fc=700):  # warm detuned saw pad, slow attack
    t = tt(d); x = np.zeros_like(t)
    for f in freqs:
        for dt in (-0.004, 0.0, 0.004):
            ph = (f * (1 + dt) * t) % 1.0; x += (2 * ph - 1)
    x = lp(x, fc, 2) / (len(freqs) * 3); return x * np.minimum(1, t / a) * np.minimum(1, (d - t) / 0.6)
def sub(f, d=2.0):
    t = tt(d); return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.4)
def whoosh(d=0.6, fc=1100):
    t = tt(d); n = lp(noise(d), fc); f = np.linspace(0, 1, len(t)); return n * np.sin(np.pi * f) ** 2 * 1.6
def swell(d=1.0, fc=900):
    t = tt(d); n = lp(noise(d), fc); return n * (t / d) ** 2 * 1.8
def boom():
    t = tt(1.6); return lp(np.sin(2 * np.pi * (36 + 50 * np.exp(-t * 10)) * t) * np.exp(-t * 2.6) + noise(1.6) * np.exp(-t * 25) * 0.25, 400)
def felt(f, d=0.9):  # soft felt-piano note
    t = tt(d); return lp((np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 4.5) * np.minimum(1, t / 0.008), 1100)
def bloom(f, d=1.2):  # soft sine swell
    t = tt(d); return np.sin(2 * np.pi * f * t) * np.sin(np.pi * (t / d)) ** 2 * 0.8
# The user's typing recording, played as it is (its own speed): it types from 2.35s to 9.2s
REC, _sr = sf.read('hook-150/assets/sound/typing.wav')
if REC.ndim > 1: REC = REC.mean(1)
REC_SPAN = (int(2.35 * SR), int(9.2 * SR))

BEAT = 60 / 118; BAR = 4 * BEAT                             # 118 BPM
CH = [(146.83, 220.0, 293.66, 369.99), (110.0, 164.81, 220.0, 277.18), (123.47, 185.0, 246.94, 293.66), (98.0, 146.83, 196.0, 246.94)]  # D A Bm G
ROOT = [73.42, 55.0, 61.74, 49.0]
S = lambda name: SEG[name]['start']
E = lambda name: SEG[name]['start'] + SEG[name]['dur']
cue = lambda name, c: SEG[name]['cues'].get(c)
DROP = cue('intro', 'cut')                                    # "Peepl": the beat comes in
groove = [(DROP, S('moment')), (S('ask'), S('end') + 0.6)]    # the full beat
in_groove = lambda t: any(a is not None and a <= t < b for a, b in groove)
dark = lambda t: S('problem') <= t < E('problem')
memory = lambda t: S('moment') <= t < E('moment')
ending = lambda t: t >= S('end') + 0.6

def pluck(f, d=0.32, fc=2600):  # a bright, short plucked note
    t = tt(d); x = 2 * ((f * t) % 1.0) - 1 + 0.5 * np.sin(2 * np.pi * f * t)
    return lp(x * np.exp(-t * 11) * np.minimum(1, t / 0.003), fc)
def bass(f, d=0.26):  # a round, short bass note
    t = tt(d); x = np.sin(2 * np.pi * f * t) + 0.3 * (2 * ((f * t) % 1.0) - 1)
    return lp(x * np.exp(-t * 7) * np.minimum(1, t / 0.006), 420)
def hat(open_=False):
    d = 0.2 if open_ else 0.05; t = tt(d); return hp(noise(d), 7000) * np.exp(-t * (16 if open_ else 70))
def clap():
    d = 0.18; t = tt(d); n = bp(noise(d), 900, 3200)
    env = sum(np.exp(-np.maximum(0, t - o) * 140) * (t >= o) for o in (0, 0.011, 0.022)) * 0.6 + np.exp(-t * 18) * 0.5
    return n * env

# The bed: a pad per bar that opens up through the hook and is brightest in the groove (darker under Vince's "hard"
# shot), and a sub
for bar in range(int(DUR / BAR) + 1):
    t = bar * BAR; c = CH[bar % 4]
    if t < S('problem'): fc = 500 + 700 * t / max(1, S('problem'))
    elif dark(t): fc = 600
    elif in_groove(t) or ending(t): fc = 1300
    else: fc = 900
    put(t, pad(c, BAR + 0.5, a=0.5, fc=fc), 0.24 if (t < S('problem') or memory(t)) else 0.3)
    put(t, sub(ROOT[bar % 4], BAR + 0.2), 0.12 if t < S('problem') else 0.18)

# Eighth notes: the arpeggio (from the hook on, quiet at first), the bass and drums in the groove, half-time in the memory
ARP = [0, 1, 2, 3, 2, 1, 3, 2]
for e8 in range(int(DUR / (BEAT / 2)) + 1):
    t = e8 * BEAT / 2; b = e8 // 2; c = CH[(b // 4) % 4]; r = ROOT[(b // 4) % 4]; on = e8 % 2 == 0
    note = c[ARP[e8 % 8]] * 2
    if in_groove(t):
        put(t, pluck(note), 0.07)
        put(t, bass(r * 2 if e8 % 4 == 2 else r), 0.32)
        if on: put(t, kick(), 0.6)
        else: put(t, hat(True), 0.035)
        if on and b % 2 == 1: put(t, clap(), 0.22)
        put(t + 0.004, hat(), 0.02)
    elif t < S('problem'):
        snap = cue('hook', 'snap') or 0
        if t >= snap: put(t, pluck(note, 0.28, 1800), 0.035 + 0.03 * t / max(1, S('problem')))
        if t >= snap and on and b % 2 == 0: put(t, kick(), 0.28)            # a heartbeat
    elif dark(t):
        put(t, pluck(note, 0.25, 1300), 0.03)
        if on: put(t, hat(), 0.03)
        if on and b % 2 == 0: put(t, kick(), 0.3)
    elif memory(t):
        if e8 % 8 == 0: put(t, kick(), 0.4)
        if e8 % 8 == 4: put(t, clap(), 0.12)
        if on: put(t, felt(note, 1.0), 0.09)
    elif ending(t):
        if on: put(t, pluck(note, 0.4, 2200), 0.06)
        if e8 % 4 == 0: put(t, bass(r, 0.5), 0.25)
    else:
        if on: put(t, pluck(note, 0.28, 1800), 0.05)
        if on and b % 2 == 0: put(t, kick(), 0.35)
# A riser into the drop
put(DROP - 2.0 if DROP else None, swell(2.0, 2400), 0.16)

# Moments
put(cue('hook', 'snap'), boom(), 0.45); put(cue('hook', 'snap'), bloom(293.66, 1.6), 0.08)
z = cue('hook', 'restZoom')
put(z - 1.2 if z else None, swell(1.2, 800), 0.18); put(z, boom(), 0.75)
w = cue('hook', 'white')
for i, f in enumerate((587.33, 739.99, 880.0, 1108.73)):  # the white dots: a shimmer
    put(w + i * 0.12 if w else None, bloom(f, 1.6), 0.05)
c0 = cue('intro', 'cut')
put(c0 - 1.0 if c0 else None, swell(1.0, 1000), 0.2); put(c0, boom(), 0.7); put(c0, pad(CH[0], 3.0, a=0.05, fc=1400), 0.25)
put(cue('intro', 'hl'), bloom(587.33, 0.9), 0.07)
put(cue('intro', 'zoom'), whoosh(0.8, 900), 0.12)
for name, c in (('intro', 'out'), ('create', 'pull'), ('moment', 'pull'), ('find', 'pull')):
    put(cue(name, c), whoosh(1.0, 800), 0.12)
for name in ('intro', 'create', 'moment', 'find'):  # taps
    t = cue(name, 'tap'); put(t, lp(noise(0.05), 2000) * np.exp(-tt(0.05) * 80), 0.25)
put(cue('moment', 'tap'), bloom(440.0, 2.0), 0.09); put(cue('moment', 'tap'), bloom(554.37, 2.0), 0.06)
put(cue('create', 'made'), bloom(659.25, 1.4), 0.07)
put(cue('find', 'note'), bloom(587.33, 1.2), 0.06)
for s in TL['segments'][1:]:  # soft air under each crossfade
    put(s['start'] - 0.2, whoosh(s['xd'] + 0.4, 700), 0.07)
# The end: a swell into a boom on the wordmark, the full chord ringing out
we = cue('end', 'peepl') or S('end') + 1.3
for i, f in enumerate((587.33, 739.99, 880.0)):   # the discs and the pills coming in
    put((cue('end', 'pills') or we - 0.7) + i * 0.22, bloom(f, 1.2), 0.05)
put(we - 1.3, swell(1.3, 1100), 0.25); put(we, boom(), 0.85)
put(we, pad((73.42, 146.83, 220.0, 277.18, 369.99), DUR - we + 0.5, a=0.1, fc=1600), 0.5)
for i, f in enumerate((587.33, 739.99, 880.0)):
    put(we + 0.5 + i * 0.35, felt(f, 2.5), 0.12)

# Typing: wherever text is being typed (letters less than 0.4s apart make one run), the next stretch of the recording
# plays at its own speed for as long as the run, faded in and out; the keys don't have to match the letters
cursor = REC_SPAN[0]
for seg in TL['segments']:
    ks = sorted(seg['keys']); runs = []
    for k in ks:
        if runs and k - runs[-1][1] < 0.4: runs[-1][1] = k
        else: runs.append([k, k])
    for a0, a1 in runs:
        n = int((a1 - a0 + 0.2) * SR)
        if cursor + n > REC_SPAN[1]: cursor = REC_SPAN[0]
        clip = REC[cursor:cursor + n].copy(); cursor += n
        fi, fo = int(0.03 * SR), int(0.12 * SR)
        clip[:fi] *= np.linspace(0, 1, fi); clip[-fo:] *= np.linspace(1, 0, fo)
        put(a0 - 0.02, clip, 1.1, keys_out)

# The keys: softened a little at the top, a short room (a 120ms decaying tail) so they sit in the music
keys_out = lp(keys_out, 9000)
ir = rng.standard_normal(int(0.12 * SR)) * np.exp(-np.arange(int(0.12 * SR)) / SR * 40) * 0.035; ir[0] = 1.0
from scipy.signal import fftconvolve
keys_out = fftconvolve(keys_out, ir)[:len(keys_out)]
# Mix: music a little under the keys; level to about -14 LUFS (the studio's rule; RMS -15 dBFS here), soft-limit only
# the peaks over -3 dBFS, fade in and out
mix = lp(out, 9000) + keys_out
mix = mix[:int(SR * DUR)]
mix *= 10 ** (-15 / 20) / (np.sqrt(np.mean(mix ** 2)) + 1e-9)
th = 10 ** (-3 / 20)
over = np.abs(mix) > th
mix[over] = np.sign(mix[over]) * (th + (1 - th) * np.tanh((np.abs(mix[over]) - th) / (1 - th)))
n = len(mix); fi, fo = int(SR * 0.3), int(SR * 2.0)
mix[:fi] *= np.linspace(0, 1, fi); mix[n - fo:] *= np.linspace(1, 0, fo)
sf.write('hook-150/out/audio.wav', np.stack([mix, mix], 1).astype(np.float32), SR)
print(f'audio: {n / SR:.2f}s')
