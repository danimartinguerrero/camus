# -*- coding: utf-8 -*-
"""Quote cards (TikTok photo carousel) + an autumn slideshow edit built from the same cards.
usage: quotes.py cards <lang> <outdir> | video <lang> <out.mp4> | info"""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit as E
from edit import W, H, FPS, F32, sm, eio, eout, prog, lerp, font, post, leak, screen

INK = (30, 27, 26)
INK_SOFT = (52, 47, 44)

Q = {
 'en': [
  ('title', 'quotes for the ones\nwho feel unseen', None),
  ('q', '“… it’s awful not to be loved. It’s the worst thing in the world … It makes you mean, and violent, and cruel.”', 'John Steinbeck, East of Eden'),
  ('q', '“I had to go through a time of isolation in order to come to terms with who and what I was.”', 'James Baldwin, The Art of Fiction'),
  ('q', '“How many years does it take to forget a minute.”', 'Anonymous'),
  ('q', '“And yet the only exciting life is the imaginary one.”', 'Virginia Woolf'),
  ('q', '“But once in a while the odd thing happens. Once in a while the dream comes true, and the whole pattern of life is altered. Once in a while the moon turns blue.”', 'W. H. Auden'),
  ('q', '“And the writing is still: to you, with you, about you, because of you and for you.”', 'Nizar Qabbani'),
  ('q', '“What is done in love is done well.”', 'Vincent van Gogh'),
  ('end', 'to seek the unseen.', None),
 ],
 'es': [
  ('title', 'frases para quien\nse siente invisible', None),
  ('q', '“… es horrible no ser amado. Es lo peor del mundo … Te vuelve mezquino, y violento, y cruel.”', 'John Steinbeck, Al este del Edén'),
  ('q', '“Tuve que atravesar un tiempo de aislamiento para llegar a aceptar quién y qué era yo.”', 'James Baldwin, The Art of Fiction'),
  ('q', '“¿Cuántos años hacen falta para olvidar un minuto?”', 'Anónimo'),
  ('q', '“Y, sin embargo, la única vida emocionante es la imaginaria.”', 'Virginia Woolf'),
  ('q', '“Pero de vez en cuando ocurre lo extraño. De vez en cuando el sueño se cumple, y todo el dibujo de la vida cambia. De vez en cuando la luna se vuelve azul.”', 'W. H. Auden'),
  ('q', '“Y la escritura sigue siendo: a ti, contigo, sobre ti, por ti y para ti.”', 'Nizar Qabbani'),
  ('q', '“Lo que se hace con amor, está bien hecho.”', 'Vincent van Gogh'),
  ('end', 'to seek the unseen.', None),
 ],
}

_PAPER = {}
def paper_bg(w, h):
    k = (w, h)
    if k not in _PAPER:
        g = np.random.default_rng(12)
        lo = g.normal(0, 1, (20, 12)).astype(F32)
        lo = np.asarray(Image.fromarray(((lo * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), F32) / 255
        fine = g.normal(0, 1, (h, w)).astype(F32)
        fine = np.asarray(Image.fromarray(np.clip(fine * 28 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), F32) / 255 - 0.5
        base = np.asarray((0.928, 0.920, 0.908), F32)
        p = base * (0.992 + 0.014 * lo[..., None]) + 0.016 * fine[..., None]
        yy, xx = np.mgrid[0:h, 0:w].astype(F32)
        r = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)
        p *= (1 - 0.10 * np.clip(r - 0.3, 0, 1))[..., None]
        _PAPER[k] = (np.clip(p, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(_PAPER[k].copy())

def wrap(f, text, maxw):
    out = []
    for para in text.split('\n'):
        words = para.split(' ')
        def greedy(mw):
            lines, cur = [], ''
            for wd in words:
                t = (cur + ' ' + wd).strip()
                if cur and f.getlength(t) > mw:
                    lines.append(cur); cur = wd
                else:
                    cur = t
            lines.append(cur); return lines
        base = greedy(maxw)
        if len(base) > 1:  # balanced
            lo, hi = maxw * 0.5, maxw
            for _ in range(16):
                mid = (lo + hi) / 2
                if len(greedy(mid)) > len(base): lo = mid
                else: hi = mid
            base = greedy(hi + 0.5)
        out += base
    return out

def card(kind, text, author, s=1.0):
    """render one 1080x1920 card (scaled by s) as PIL RGB"""
    w, h = int(round(W * s)), int(round(H * s))
    im = paper_bg(w, h)
    dr = ImageDraw.Draw(im)
    if kind == 'title':
        f = font('serif_i', int(round(76 * s)))
        lines = text.split('\n')
        lh = 92 * s
        y0 = h / 2 - len(lines) * lh / 2
        for i, ln in enumerate(lines):
            dr.text((w / 2, y0 + i * lh + lh / 2), ln, font=f, fill=INK, anchor='mm')
        return im
    if kind == 'end':
        f = font('serif_i', int(round(58 * s)))
        dr.text((w / 2, h / 2), text, font=f, fill=INK_SOFT, anchor='mm')
        return im
    n = len(text)
    size = 64 if n < 70 else 58 if n < 130 else 52
    f = font('serif', int(round(size * s)))
    lines = wrap(f, text, 820 * s)
    lh = size * 1.42 * s
    block_w = max(f.getlength(l) for l in lines)
    fa = font('serif_i', int(round(44 * s)))
    gap = 110 * s
    total = len(lines) * lh + gap + 50 * s
    y0 = h / 2 - total / 2 - 20 * s
    x0 = w / 2 - block_w / 2
    for i, ln in enumerate(lines):
        dr.text((x0, y0 + i * lh), ln, font=f, fill=INK)
    dr.text((w / 2, y0 + len(lines) * lh + gap), '— ' + author, font=fa, fill=INK, anchor='mt')
    return im

# ---------------------------------------------------------------- video
ZOOM = 1.05
def durations(items):
    d = []
    for kind, text, _ in items:
        if kind == 'title': d.append(2.2)
        elif kind == 'end': d.append(2.4)
        else: d.append(2.6 + min(1.8, len(text) / 80))
    return d

XF = 0.7
_BIG = {}
def big(i, items):
    if i not in _BIG:
        k, t, a = items[i]
        _BIG[i] = card(k, t, a, ZOOM)
    return _BIG[i]

def view(i, items, p):
    im = big(i, items); sw, sh = im.size
    z = lerp(1.0, ZOOM, eio(p))          # zoom 1.0 -> 1.05: scale stays <= 1 vs the big render
    s = (W / sw) * z
    vw, vh = W / s, H / s
    x0, y0 = (sw - vw) / 2, (sh - vh) / 2
    out = im.transform((W, H), Image.AFFINE, (1 / s, 0, x0, 0, 1 / s, y0), resample=Image.BICUBIC)
    return np.asarray(out, F32) / 255

LEAVES = None
def render_frame(fi, items, starts, durs):
    global LEAVES
    if LEAVES is None:
        LEAVES = E.Leaves(9, 23)
    t = fi / FPS
    i = max(k for k in range(len(starts)) if starts[k] <= t)
    p = (t - starts[i]) / (durs[i] + XF)
    fr = view(i, items, p)
    # crossfade into the next card during the last XF seconds
    if i + 1 < len(items) and t > starts[i] + durs[i]:
        e = sm((t - starts[i] - durs[i]) / XF)
        nb = view(i + 1, items, (t - starts[i + 1]) / (durs[i + 1] + XF))
        fr = fr * (1 - e) + nb * e
    LEAVES.draw(fr, t + 4, amul=0.85)
    fr = screen(fr, leak(t, [(0.95, 0.05, 0.6, 0.35, (1.0, 0.72, 0.42), 0.16 + 0.04 * math.sin(t * 0.7)),
                            (0.0, 1.0, 0.5, 0.3, (1.0, 0.6, 0.3), 0.10)]))
    total = starts[-1] + durs[-1]
    fr *= 1 - sm(prog(t, total - 0.8, total))
    fr *= sm(prog(t, 0, 0.5)) * 0.85 + 0.15 if t < 0.5 else 1
    return post(fr, fi, t, grain=0.03, vig=0.35, bl=0.04, dust=True)

def timeline(items):
    durs = durations(items)
    starts = []; t = 0.0
    for d in durs:
        starts.append(t); t += d
    return starts, durs, t

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'cards':
        lang, out = sys.argv[2], sys.argv[3]
        os.makedirs(out, exist_ok=True)
        for i, (k, t, a) in enumerate(Q[lang]):
            card(k, t, a).save(f'{out}/{i + 1:02d}.jpg', quality=95, subsampling=0)
        print('ok', out)
    elif cmd in ('video', 'info'):
        lang = sys.argv[2]
        items = Q[lang]
        starts, durs, total = timeline(items)
        n = int(round(total * FPS))
        if cmd == 'info':
            print('total', total, 'frames', n); sys.exit()
        a, b, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(a, min(b, n)):
            fr = render_frame(fi, items, starts, durs)
            p.stdin.write((np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait(); print('done', out)
