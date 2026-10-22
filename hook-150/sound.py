# .venv/bin/python -I hook-150/sound.py   (from ~/motion-design; assemble.py runs it) -> hook-150/out/audio.wav
# The music and the typing for the whole cut, placed from hook-150/out/timeline.json (where each shot starts, every
# typed key and the shots' beats on the film's clock). Synthesized like the main film's sound.py (same instruments):
# warm, low-passed; 100 BPM, Dmaj7 Bm7 Gmaj7 A.
#   the hook: sparse and ambient (pad, a low drone, felt notes); a soft hit on "150 people", a swell into a low boom on
#             the "rest?" zoom, a shimmer as the white dots fill in
#   Vince's "Meeting people is easy / hard": the same bed, a little darker, a ticking pulse
#   "Introducing Peepl": a swell into a hit on the cut to "Peepl", then the beat (soft kick, brush) for the product
#   the memory playing back: the beat drops out, intimate; a bloom when play is tapped
#   the last scene: blooms as the discs and pills come in, a swell into a boom on "Peepl", the full chord, ringing out
#   typing: a short keyboard click (a bright tick and a soft body) on every typed letter, a little different each time
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
def key():  # a keyboard key: a bright tick and a soft wooden body, each a little different
    d = 0.07; t = tt(d)
    tick = bp(noise(d), 2500, 7000) * np.exp(-t * 900)
    body = lp(noise(d), 900) * np.exp(-t * 110) * 0.9
    tone = np.sin(2 * np.pi * rng.uniform(170, 230) * t) * np.exp(-t * 60) * 0.35
    return (tick * rng.uniform(0.7, 1.0) + body + tone) * rng.uniform(0.75, 1.0)

BEAT = 0.6; BAR = 4 * BEAT
CH = [(146.83, 185.0, 220.0, 277.18), (123.47, 146.83, 185.0, 220.0), (98.0, 123.47, 146.83, 185.0), (110.0, 138.59, 164.81, 220.0)]  # Dmaj7 Bm7 Gmaj7 A
ROOT = [73.42, 61.74, 49.0, 55.0]
S = lambda name: SEG[name]['start']
E = lambda name: SEG[name]['start'] + SEG[name]['dur']
cue = lambda name, c: SEG[name]['cues'].get(c)
groove = [(cue('intro', 'cut'), S('moment')), (S('ask'), S('end') + 0.4)]   # where the beat plays
in_groove = lambda t: any(a is not None and a <= t < b for a, b in groove)
dark = lambda t: S('problem') <= t < E('problem')

# The bed: a pad per bar (darker under Vince's "hard" shot), a low drone; softer in the hook and the memory
for bar in range(int(DUR / BAR) + 1):
    t = bar * BAR; c = CH[bar % 4]
    quiet = t < S('problem') or S('moment') <= t < E('moment')
    put(t, pad(c, BAR + 0.5, a=0.8, fc=520 if dark(t) else 700), 0.22 if quiet else 0.34)
    put(t, sub(ROOT[bar % 4], BAR + 0.2), 0.14 if quiet else 0.22)
# Felt notes and the beat
for b in range(int(DUR / BEAT) + 1):
    t = b * BEAT; c = CH[(b // 4) % 4]
    if in_groove(t):
        put(t, kick(), 0.5)
        if b % 2 == 1: put(t, hp(lp(noise(0.08), 5500), 3000) * np.exp(-tt(0.08) * 60), 0.05)  # brush
        if b % 4 in (0, 2): put(t, felt(c[(b // 2) % 4] * 2), 0.14)
    elif t < S('problem'):
        if b % 4 == 0: put(t, felt(c[(b // 4) % 4] * 2, 1.4), 0.12)
    elif dark(t):
        put(t, hp(noise(0.03), 4000) * np.exp(-tt(0.03) * 120), 0.03)  # ticking pulse
    elif S('moment') <= t < E('moment'):
        if b % 2 == 0: put(t, felt(c[(b // 2) % 4] * 2, 1.2), 0.12)
    else:
        if b % 4 == 0: put(t, felt(c[0] * 2, 1.2), 0.1)

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

# Typing
for s in TL['segments']:
    for k in s['keys']:
        put(k, key(), 0.62, keys_out)

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
print(f'audio: {n / SR:.2f}s, {sum(len(s["keys"]) for s in TL["segments"])} keys')
