# python3 hook-150/assemble.py <fps>   (make_cut.sh runs it, from ~/motion-design, after rendering the shots)
# Joins the rendered shots with their crossfades, works out where each shot starts in the film from how long it really
# came out (speeds change their lengths), maps every typed key and every beat onto the film's clock
# (hook-150/out/timeline.json), makes the sound (sound.py -> out/audio.wav) and puts picture and sound together:
# hook-150/out/peepl-film-draft.mp4.
import json, subprocess, sys, bisect

FPS = int(sys.argv[1])
O = 'hook-150/out'
FF = 'ffmpeg'
# shot, how it comes in (ffmpeg xfade transition, seconds), seconds its last frame holds
SHOTS = [('hook', None, 0, 0), ('problem', 'fade', 0.4, 0), ('intro', 'smoothright', 0.6, 0), ('create', 'fade', 0.3, 0),
         ('story', 'fade', 0.8, 0), ('moment', 'fade', 0.8, 0), ('ask', 'fade', 0.8, 0), ('find', 'fade', 0.8, 0),
         ('end', 'fade', 0.8, 0)]

segs, start = [], 0.0
for i, (name, how, xd, hold) in enumerate(SHOTS):
    m = json.load(open(f'{O}/{name}.json'))
    dur = len(m['times']) / FPS + hold
    if i: start = segs[-1]['start'] + segs[-1]['dur'] - xd
    src = f'{O}/{name}.mp4'
    if hold:
        src = f'{O}/{name}-hold.mp4'
        subprocess.run([FF, '-y', '-loglevel', 'error', '-i', f'{O}/{name}.mp4', '-vf', f'tpad=stop_mode=clone:stop_duration={hold}',
                        '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', src], check=True)
    times = m['times']

    def at(ts, times=times, start=start):  # film time of a moment in the shot's own time
        if ts < times[0] or ts > times[-1] + 1 / FPS: return None
        j = max(1, bisect.bisect_left(times, ts)); j = min(j, len(times) - 1)
        t0, t1 = times[j - 1], times[j]
        f = (j - 1) + (0 if t1 == t0 else (ts - t0) / (t1 - t0))
        return start + f / FPS
    keys = [k for k in (at(x) for x in m['keys']) if k is not None]
    cues = {k: at(v) for k, v in m['cues'].items() if at(v) is not None}
    segs.append({'name': name, 'src': src, 'how': how, 'xd': xd, 'start': round(start, 4), 'dur': round(dur, 4), 'keys': keys, 'cues': cues})
total = segs[-1]['start'] + segs[-1]['dur']
json.dump({'fps': FPS, 'total': total, 'segments': segs}, open(f'{O}/timeline.json', 'w'), indent=1)
for s in segs: print(f"{s['name']:8s} {s['start']:7.2f} -> {s['start'] + s['dur']:7.2f}  keys {len(s['keys'])}")

# Picture: chain the crossfades
inputs, chain, last = [], [], '0:v'
for i, s in enumerate(segs):
    inputs += ['-i', s['src']]
    if i:
        out = 'v' if i == len(segs) - 1 else f'x{i}'
        chain.append(f"[{last}][{i}:v]xfade=transition={s['how']}:duration={s['xd']}:offset={s['start']:.4f}" + (',format=yuv420p' if out == 'v' else '') + f'[{out}]')
        last = out
subprocess.run([FF, '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', '[v]', '-c:v', 'libx264', '-crf', '16',
                '-r', str(FPS), f'{O}/peepl-film-silent.mp4'], check=True)
# Sound, then both together
subprocess.run(['.venv/bin/python', '-I', 'hook-150/sound.py'], check=True)
subprocess.run([FF, '-y', '-loglevel', 'error', '-i', f'{O}/peepl-film-silent.mp4', '-i', f'{O}/audio.wav', '-c:v', 'copy', '-c:a', 'aac',
                '-b:a', '192k', '-shortest', f'{O}/peepl-film-draft.mp4'], check=True)
print(f'film: {total:.2f}s')
