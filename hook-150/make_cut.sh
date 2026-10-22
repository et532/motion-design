#!/bin/zsh
# The whole cut, rendered shot by shot, joined (assemble.py), with music and typing sounds (sound.py):
#   1. the hook (index.html)
#   2. Vince's "Meeting people is easy / Remembering them is hard" shot (his first version, commit 964dee0, from a
#      temporary copy that plays only that shot on its night background; each line holds ~0.45s after it finishes,
#      see vince_copy.py). 0.4s crossfade in: his night background is close to the hook's.
#   3. "Introducing Peepl" (intro.html), on the light background, brought in by a 0.6s soft wipe from the left, like the
#      wipes Vince's film uses between its night and day scenes. It ends on the pale background once the phone leaves.
#   4. "Speak into the mic" and the new profile (create.html), on the same pale background (0.3s crossfade).
#   5. Vince's "Every person. Every story." and "Remember the connection. Not just their name." (his v17 film, temporary
#      copy: headline before the cards, crossfades instead of his wipes), 0.8s crossfade in.
#   6. A moment plays back (moment.html?v=card: the collapsed card widens and opens; ?v=button is the other version),
#      0.8s crossfade in. Halfway through the memory it pulls back to the phone, "Play it back." fades in, they leave.
#   7. Vince's "Ask your own notes." and its three prompts (v17 copy: prompts after the headline, smoother highlight,
#      a beat, then it all fades out), 0.8s crossfade in.
#   8. Find someone (find.html): "I want to find someone to go climbing with me" typed in a search box that fills the
#      frame, pulled back to the box, then to the phone (on Vince's night background); send, the recorded results, "Why
#      Jordan" (glass); the note and the phone leave. 0.8s crossfade in.
#   9. The last scene (end.html, from the user's still): the mindmap's discs and three people's pills slide in on the
#      right, then "Peepl" and "Remember the stories of the people you meet". 0.8s crossfade in, at its own pace (1x).
# Speeds (user's call): everything 1.4x (the last scene is timed at its own pace), except "Speak into the mic" to the new profile (create.html, 1x) and the phone
# part of find.html (1x; its typing is 1.4x, easing to 1x while the box settles, before the phone). Vince's first shot
# was at 65% and is now 0.65 x 1.4 = 91%.
# Run from anywhere:  zsh ~/motion-design/hook-150/make_cut.sh [draft|final]
#   draft (default): 30fps, 2 sub-frames of motion blur. For checking timing while iterating.
#   final: 60fps, 8 sub-frames. For versions to share.
# Each shot goes through render_segment.mjs (fast JPEG capture); the studio's render.mjs is left as it is.
# Output: hook-150/out/peepl-film-draft.mp4 (and hook-150/out/timeline.json, audio.wav)
set -e
MODE=${1:-draft}
case "$MODE" in
  draft) FPS=30; SUB=2 ;;
  final) FPS=60; SUB=8 ;;
  *) echo "usage: make_cut.sh [draft|final]"; exit 1 ;;
esac
echo "$MODE: ${FPS}fps, $SUB sub-frames"
cd "$HOME/motion-design"
export PATH="$HOME/motion-design/bin:$PATH"
O=hook-150/out
mkdir -p $O

# What a page says about itself once it's ready (window.<expr>)
ask() { node -e "import('playwright').then(async({chromium})=>{const b=await chromium.launch({args:['--allow-file-access-from-files']});const p=await b.newPage();await p.goto('file://'+process.cwd()+'/$1');await p.evaluate(()=>window.ready);console.log(await p.evaluate(()=>$2));await b.close()})"; }
seg() { local name=$1 page=$2 from=$3 to=$4; shift 4
  node hook-150/render_segment.mjs --page "$page" --from "$from" --to "$to" --fps "$FPS" --sub "$SUB" --out "$O/$name.mp4" --map "$O/$name.json" "$@"; }
vince() { python3 hook-150/vince_copy.py "$1" > ".cut-$1.tmp.html" || { rm -f ".cut-$1.tmp.html"; exit 1; }; }

seg hook hook-150/index.html 0 "$(ask hook-150/index.html window.DURATION)" --speed 1.4

git show 964dee0:index.html | vince problem
seg problem .cut-problem.tmp.html 2.4 6.5 --speed 0.91
rm -f .cut-problem.tmp.html

seg intro hook-150/intro.html 0 "$(ask hook-150/intro.html window.DURATION)" --speed 1.4
seg create hook-150/create.html 0 "$(ask hook-150/create.html window.DURATION)" --speed 1

# Vince's v17 shots (his file is not changed): each from just before it (his background alone)
vince story < index.html
R=($(ask .cut-story.tmp.html "[window.filmTime(window.BGT.field)-0.9,window.filmTime(window.BGT.moments+3.9)].map((x)=>x.toFixed(3)).join(' ')"))
seg story .cut-story.tmp.html $R[1] $R[2] --speed 1.4
rm -f .cut-story.tmp.html

seg moment "hook-150/moment.html?v=card" 0 "$(ask 'hook-150/moment.html?v=card' window.DURATION)" --speed 1.4

vince ask < index.html
R=($(ask .cut-ask.tmp.html "[window.filmTime(window.BGT.ask)-0.9,window.filmTime(window.BGT.ask+4.1)].map((x)=>x.toFixed(3)).join(' ')"))
seg ask .cut-ask.tmp.html $R[1] $R[2] --speed 1.4
rm -f .cut-ask.tmp.html

R=($(ask hook-150/find.html "[window.DURATION, ...window.RAMP].join(' ')"))
seg find hook-150/find.html 0 $R[1] --speedmap "$R[2]:1.4,$R[3]:1"

seg end hook-150/end.html 0 "$(ask hook-150/end.html window.DURATION)" --speed 1

# Join them (crossfades), work out where every typed key lands, make the sound, put it all together
python3 hook-150/assemble.py "$FPS"
echo done
