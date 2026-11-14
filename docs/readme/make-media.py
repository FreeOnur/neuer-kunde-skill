#!/usr/bin/env python3
"""Turns the frames from capture.mjs into animated WebP (much smaller than GIF, plays on GitHub)
and the stills into WebP. Usage: python3 make-media.py <frames-dir> <out-dir>"""
import glob, os, sys
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

def anim(folder, name, width, ms, quality=72, step=1, hold_end=0):
    files = sorted(glob.glob(f"{src}/{folder}/*.png"))[::step]
    if not files:
        return
    frames = []
    for f in files:
        im = Image.open(f).convert("RGB")
        frames.append(im.resize((width, round(im.height * width / im.width)), Image.LANCZOS))
    durations = [ms] * len(frames)
    durations[0] = max(ms, 900)          # hold the first frame a moment
    durations[-1] = max(ms, hold_end)    # and the last one
    p = f"{out}/{name}.webp"
    frames[0].save(p, save_all=True, append_images=frames[1:], duration=durations, loop=0, quality=quality, method=6)
    print(f"{name}.webp {len(frames)} frames {os.path.getsize(p) // 1024} KB")

anim("hero3d", "motion-3d-world", 900, 85, quality=66, hold_end=1600)
anim("swipe", "motion-phone-swipe", 360, 70, hold_end=1200)
for k in ("tischlerei-frastanz", "friseur-feldkirch", "gasthaus-bludenz"):
    anim(f"concept-{k}", f"motion-concept-{k}", 800, 95, hold_end=1500)

for p in sorted(glob.glob(f"{src}/stills/*.png")):
    n = os.path.splitext(os.path.basename(p))[0]
    im = Image.open(p).convert("RGB")
    im.thumbnail((1600, 1600))
    im.save(f"{out}/shot-{n}.webp", "WEBP", quality=82, method=6)
    print(f"shot-{n}.webp {os.path.getsize(f'{out}/shot-{n}.webp') // 1024} KB")

# SMTN: the site's own short screen recording (from the Löwen site's work section), as animated WebP:
#   ffmpeg -i smtn.webm -t 5.4 -vf "fps=12,scale=800:-1:flags=lanczos" -c:v libwebp_anim -quality 70 -loop 0 motion-smtn.webp
