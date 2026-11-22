# -*- coding: utf-8 -*-
"""to seek the unseen (v2) — short, beat-cut collage edit. Photos + quotes + small clips, no backgrounds.
1080x1920, 30 fps, 120 BPM grid, no audio. Every photo/clip is shown at native resolution or smaller."""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit as E
from edit import (W, H, FPS, F32, clamp, sm, eout, eio, lerp, prog, lerp3, tone, kb, kb_map, paste, Text,
                  typewriter, post, leak, screen, CREAM, GOLD, SILVER, WARM, AMBER, GOLDT, COLD, PAPER_C)

LANG = E.LANG
CLIPDIR = os.path.join(E.S, 'clips')
BEAT = 0.5  # 120 BPM

TX = {
 'en': dict(
  hook1='I was looked at,', hook2='but I wasn’t seen.',
  normal='nobody realizes that some people expend tremendous energy merely to be normal.',
  tired='I am strangely tired, not from having talked so much, but at the mere thought of what I still have to say.',
  absurd='the absurd does not liberate; it binds.',
  refuse='man is the only creature who refuses to be what he is.',
  happy='one must imagine Sisyphus happy.',
  despair='there is no love of life without despair of life.',
  autumn='autumn is a second spring, when every leaf is a flower.',
  coffee='real generosity toward the future lies in giving all to the present.', coffee2='damn fine coffee.',
  tears='live to the point of tears.',
  world='the world is beautiful, and outside it there is no salvation.',
  love='I know of only one duty, and that is to love.',
  secret='when I look at my life and its secret colours, I feel like bursting into tears.',
  winter0='in the depth of winter,', winter='I finally learned that within me there lay an invincible summer.',
  attr='— albert camus', outro1='you were never unseen.', outro2='to seek the unseen.'),
 'es': dict(
  hook1='me miraban,', hook2='pero no me veían.',
  normal='nadie se da cuenta de que algunas personas gastan una energía tremenda solo para ser normales.',
  tired='estoy extrañamente cansado, no por haber hablado tanto, sino ante la sola idea de lo que aún me queda por decir.',
  absurd='lo absurdo no libera; ata.',
  refuse='el hombre es la única criatura que se niega a ser lo que es.',
  happy='hay que imaginarse a Sísifo feliz.',
  despair='no hay amor de vivir sin desesperación de vivir.',
  autumn='el otoño es una segunda primavera, donde cada hoja es una flor.',
  coffee='la verdadera generosidad con el futuro consiste en darlo todo al presente.', coffee2='damn fine coffee.',
  tears='vivir hasta las lágrimas.',
  world='el mundo es bello, y fuera de él no hay salvación.',
  love='no conozco más que un deber, y es el de amar.',
  secret='cuando miro mi vida y sus colores secretos, siento ganas de echarme a llorar.',
  winter0='en lo más profundo del invierno,', winter='aprendí por fin que había en mí un verano invencible.',
  attr='— albert camus', outro1='nunca fuiste invisible.', outro2='to seek the unseen.'),
}[LANG]

HL = {'seen.', 'veían.', 'happy.', 'feliz.', 'tears.', 'lágrimas.', 'love.', 'amar.', 'flower.', 'flor.',
      'invincible', 'summer.', 'verano', 'invencible.', 'secret', 'colours,', 'colores', 'secretos,', 'normal.', 'normales.',
      'binds.', 'ata.', 'present.', 'presente.', 'salvation.', 'salvación.'}

def T(key, y, size=70, maxw=900, color=CREAM, hl_color=GOLD, fkey='serif_i', shadow=0.85, glow=14):
    return Text(TX[key], fkey, size, y, color=color, maxw=maxw, shadow=shadow, glow=glow, hl=HL, hl_color=hl_color)

# ------------------------------------------------------------------ clips
_CL = {}
def clip_arr(name):
    if name not in _CL:
        _CL[name] = np.load(f'{CLIPDIR}/{name}.npy')
    return _CL[name]

def clip_L(name, tl, w=None, speed=1.0, offset=0.0, mode='pingpong'):
    a = clip_arr(name); n = len(a)
    k = int((tl * speed + offset) * FPS)
    if mode == 'pingpong' and n > 1:
        p = k % (2 * n - 2); k = p if p < n else 2 * n - 2 - p
    elif mode == 'hold':
        k = min(max(k, 0), n - 1)
    else:
        k %= n
    f = a[k]
    if w is not None and w < f.shape[1]:
        h = int(round(f.shape[0] * w / f.shape[1]))
        f = np.asarray(Image.fromarray(f).resize((w, h), Image.LANCZOS))
    return f.astype(F32) / 255

def photo(name, w, h, tl, D, z0=1.0, z1=1.05, c0=(0.5, 0.5), c1=(0.5, 0.45)):
    return kb(name, w, h, clamp(tl / D), z0, z1, c0, c1)

# ------------------------------------------------------------------ print element
def mk(L, grade, border=12, dim=1.0, lift=0.045, contrast=1.07):
    rgb = tone(L, *grade, lift=lift, contrast=contrast) * dim
    if border == 0:
        return rgb
    h, w = L.shape
    c = np.empty((h + 2 * border, w + 2 * border, 3), F32); c[:] = np.asarray(PAPER_C, F32) * dim
    c[border:border + h, border:border + w] = rgb
    return c

def put(fr, c, cx, cy, tl, t_in=0.0, angle=0.0, enter='pop', dur=0.22, shadow=0.75):
    p = eout(prog(tl, t_in, t_in + dur))
    if p <= 0:
        return
    s = 0.9 + 0.1 * p if enter in ('pop', 'drop') else 1.0
    ox = oy = 0.0
    if enter == 'drop': oy = -(1 - p) * 90
    elif enter == 'slide_l': ox = -(1 - p) * 600
    elif enter == 'slide_r': ox = (1 - p) * 600
    elif enter == 'up': oy = (1 - p) * 400
    im = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8))
    if s < 0.999:
        im = im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.BILINEAR)
    a = Image.new('L', im.size, 255)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True); a = a.rotate(angle, resample=Image.BICUBIC, expand=True)
    arr = np.asarray(im, F32) / 255; al = np.asarray(a, F32) / 255
    alpha = min(1.0, p * 1.8)
    if enter != 'cut':  # gentle life after landing
        ox += 5 * math.sin(tl * 0.9 + cx * 0.01); oy += 4 * math.cos(tl * 0.7 + cy * 0.01)
    x0, y0 = cx + ox - im.size[0] / 2, cy + oy - im.size[1] / 2
    if shadow:
        pad = 44
        sa = Image.new('L', (a.size[0] + 2 * pad, a.size[1] + 2 * pad), 0); sa.paste(a, (pad, pad))
        sh = np.asarray(sa.filter(ImageFilter.GaussianBlur(18)), F32) / 255
        paste(fr, np.zeros(sh.shape + (3,), F32), int(x0 - pad + 10), int(y0 - pad + 20), sh, shadow * alpha)
    paste(fr, arr, int(round(x0)), int(round(y0)), al, alpha)

def blank():
    return np.zeros((H, W, 3), F32) + np.asarray((0.012, 0.011, 0.012), F32)

# ------------------------------------------------------------------ blocks
def fit(name, maxw, maxh):
    sw, sh = E.img_L(name).size
    s = min(1.0, maxw / sw, maxh / sh)
    return int(sw * s), int(sh * s)

def make_flurry(names):
    def fn(fr, tl, D):
        k = min(len(names) - 1, int(tl / (D / len(names))))
        nm = names[k]
        w, h = fit(nm, 980, 1250)
        w, h = int(w * 0.92), int(h * 0.92)
        local = tl - k * D / len(names)
        L = kb(nm, w, h, local / (D / len(names)), 1.0, 1.07, (0.5, 0.5), (0.5, 0.5))
        put(fr, mk(L, SILVER if k % 2 else WARM), W / 2, 860, 1.0, 0, angle=(-2.5 if k % 2 else 2.5), shadow=0.6)
    return fn

T_HOOK1 = T('hook1', 1330, 84); T_HOOK2 = T('hook2', 1440, 84)
def b_hook(fr, tl, D):
    d = 1 - 0.5 * sm(prog(tl, 1.75, 2.2))
    gr = lerp3(SILVER[0], (1, 1, 1), 1 - d), lerp3(SILVER[1], (1, 1, 1), 1 - d)
    put(fr, mk(photo('lighting', 600, 540, tl, D, 1.0, 1.05), gr, dim=d), 540, 600, tl, 0.0)
    put(fr, mk(kb('enavant', 420, 378, 0, 1, 1, (.5, .5), (.5, .5)), gr, dim=d), 285, 1000, tl, 1.0, angle=-4, enter='slide_l')
    put(fr, mk(kb('cig', 380, 342, 0, 1, 1, (.5, .5), (.5, .5)), gr, dim=d), 800, 1040, tl, 1.5, angle=4, enter='slide_r')
    T_HOOK1.draw(fr, tl, 0.45, per=0.07, fade=0.3, rise=10)
    T_HOOK2.draw(fr, tl, 1.75, per=0.09, fade=0.3, rise=10)

T_NORMAL = T('normal', 1360, 64)
def b_normal(fr, tl, D):
    put(fr, mk(photo('facepalm', 1080, 600, tl, D, 1.0, 1.06, (.5, .5), (.55, .45)), SILVER, border=0), 540, 380, tl, 0, enter='cut', shadow=0)
    put(fr, mk(kb('gesture', 300, 448, 0, 1, 1, (.5, .5), (.5, .5)), WARM), 250, 900, tl, 0.5, angle=-4, enter='slide_l')
    put(fr, mk(clip_L('nobel_close', tl, 350), SILVER), 760, 800, tl, 1.0, angle=3, enter='drop')
    T_NORMAL.draw(fr, tl, 0.25, per=0.05, fade=0.3, rise=10)

T_TIRED = T('tired', 1330, 60)
def b_tired(fr, tl, D):
    put(fr, mk(clip_L('interview', tl, 500, mode='hold'), SILVER), 540, 560, tl, 0)
    put(fr, mk(kb('bed', 330, 328, 0, 1, 1, (.5, .5), (.5, .5)), WARM), 220, 930, tl, 1.0, angle=-5, enter='slide_l')
    T_TIRED.draw(fr, tl, 0.3, per=0.05, fade=0.3, rise=10)

T_ABSURD = T('absurd', 1340, 76)
def b_absurd(fr, tl, D):
    put(fr, mk(clip_L('chess', tl, 560, speed=0.5), SILVER), 540, 620, tl, 0, angle=-2)
    put(fr, mk(kb('gesture', 300, 448, 0, 1, 1, (.5, .5), (.5, .5)), SILVER), 850, 990, tl, 0.5, angle=5, enter='drop')
    T_ABSURD.draw(fr, tl, 0.2, per=0.06, fade=0.3, rise=10)

T_REFUSE = T('refuse', 1330, 70)
def b_refuse(fr, tl, D):
    put(fr, mk(photo('coat', 660, 444, tl, D, 1.0, 1.08, (.5, .5), (.5, .35)), SILVER), 540, 560, tl, 0)
    put(fr, mk(kb('cig', 380, 342, 0, 1, 1, (.5, .5), (.5, .5)), SILVER), 290, 930, tl, 0.5, angle=-4, enter='slide_l')
    T_REFUSE.draw(fr, tl, 0.2, per=0.06, fade=0.3, rise=10)

T_HAPPY = T('happy', 1300, 86)
def b_happy(fr, tl, D):
    put(fr, mk(photo('smile', 600, 807, tl, D, 1.0, 1.15, (.5, .5), (.45, .32)), GOLDT), 540, 620, tl, 0)
    T_HAPPY.draw(fr, tl, 0.25, per=0.1, fade=0.3, rise=10)
    k = math.exp(-((tl - 0.85) / 0.12) ** 2)
    if k > 0.01:
        fr[:] = screen(fr, leak(tl, [(0.8, 0.2, 0.6, 0.5, (1.0, 0.7, 0.35), 0.6 * k)]))

T_DESPAIR = T('despair', 1340, 72)
def b_despair(fr, tl, D):
    put(fr, mk(photo('paris', 680, 680, tl, D, 1.0, 1.05, (.5, .5), (.5, .4)), COLD), 540, 590, tl, 0)
    put(fr, mk(clip_L('wolf', tl, 300), COLD), 830, 970, tl, 0.5, angle=4, enter='drop')
    T_DESPAIR.draw(fr, tl, 0.2, per=0.06, fade=0.3, rise=10)

LEAVES = None
T_AUTUMN = T('autumn', 1350, 72, hl_color=(1.0, 0.76, 0.48))
def b_autumn(fr, tl, D):
    global LEAVES
    if LEAVES is None:
        LEAVES = E.Leaves(12, 9)
    put(fr, mk(photo('cat', 600, 876, tl, D, 1.0, 1.08, (.5, .5), (.48, .35)), AMBER), 600, 610, tl, 0)
    put(fr, mk(kb('tree', 300, 385, 0, 1, 1, (.5, .5), (.5, .5)), AMBER), 250, 960, tl, 0.5, angle=-6, enter='slide_l')
    T_AUTUMN.draw(fr, tl, 0.2, per=0.06, fade=0.3, rise=10)
    LEAVES.draw(fr, tl + 2, amul=0.9)

T_COFFEE = T('coffee', 1310, 62)
def b_coffee(fr, tl, D):
    args = ('cafe', 950, 628, clamp(tl / D), 1.0, 1.035, (.5, .5), (.56, .5))
    L = kb(*args)
    c = mk(L, WARM)
    X, Y = kb_map(*args, 0.530, 0.706)
    E.steam(c, tl, X + 12, Y + 12)
    put(fr, c, 540, 540, tl, 0)
    put(fr, mk(clip_L('coffee', tl, 340, speed=0.7), WARM), 800, 930, tl, 0.5, angle=3, enter='drop')
    T_COFFEE.draw(fr, tl, 0.2, per=0.05, fade=0.3, rise=10)
    typewriter(fr, TX['coffee2'], tl, 1.3, 16, 'type', 34, 1520, CREAM, cursor=True, alpha=0.85)

T_TEARS = T('tears', 1160, 92)
def b_tears(fr, tl, D):
    put(fr, mk(photo('couch', 1080, 409, tl, D, 1.0, 1.05), WARM, border=0), 540, 520, tl, 0, enter='cut', shadow=0)
    put(fr, mk(clip_L('nobel_close', tl, 350, offset=1.0), SILVER), 540, 830, tl, 0.2, angle=-2, enter='drop')
    T_TEARS.draw(fr, tl, 0.15, per=0.08, fade=0.25, rise=10)

T_WORLD = T('world', 1340, 68)
def b_world(fr, tl, D):
    put(fr, mk(photo('gesture', 400, 597, tl, D, 1.0, 1.02), WARM), 320, 640, tl, 0, angle=-3)
    put(fr, mk(clip_L('nobel_cer', tl, 350, mode='hold'), SILVER), 770, 930, tl, 0.5, angle=3, enter='slide_r')
    T_WORLD.draw(fr, tl, 0.2, per=0.06, fade=0.3, rise=10)

T_LOVE = T('love', 1330, 72)
def b_love(fr, tl, D):
    put(fr, mk(photo('bed', 600, 597, tl, D, 1.0, 1.08, (.5, .5), (.45, .4)), WARM), 540, 610, tl, 0)
    put(fr, mk(clip_L('nobel_woman', tl, 350, mode='hold'), WARM), 770, 980, tl, 0.4, angle=-3, enter='drop')
    T_LOVE.draw(fr, tl, 0.2, per=0.07, fade=0.3, rise=10)

MOSAIC = ['paris', 'coat', 'smile', 'cat', 'bed', 'lighting', 'enavant', 'cig', 'gesture', 'sketch', 'cafe', 'facepalm']
_MZ = {}
T_SECRET = T('secret', 960, 70, hl_color=(1.0, 0.70, 0.66), shadow=0.95, glow=18)
def b_secret(fr, tl, D):
    if not _MZ:
        g = np.random.default_rng(4)
        _MZ['order'] = g.permutation(12)
        for i, nm in enumerate(MOSAIC):
            _MZ[nm] = kb(nm, 356, 476, 0, 1.0, 1.0, (.5, .45), (.5, .45))
    dim = 1 - 0.6 * sm(prog(tl, 0.55, 0.9))
    for i, nm in enumerate(MOSAIC):
        r, c = divmod(i, 3)
        rank = int(np.where(_MZ['order'] == i)[0][0])
        a = sm(prog(tl, rank * 0.04, rank * 0.04 + 0.12))
        if a <= 0: continue
        gr = WARM if (r + c) % 2 else SILVER
        rgb = tone(_MZ[nm], *gr, lift=0.04, contrast=1.06) * dim
        paste(fr, rgb, c * 360 + 2, r * 480 + 2, None, a)
    T_SECRET.draw(fr, tl, 0.6, per=0.06, fade=0.3, rise=10)

T_WIN0 = T('winter0', 1250, 50, color=(0.86, 0.88, 0.92))
T_WIN = T('winter', 1400, 72)
T_ATTR = Text(TX['attr'], 'type', 30, 1600, color=(0.92, 0.86, 0.76), shadow=0.6)
def b_winter(fr, tl, D):
    w = sm(prog(tl, 1.6, 3.0))
    gr = lerp3(COLD[0], GOLDT[0], w), lerp3(COLD[1], GOLDT[1], w)
    put(fr, mk(kb('cat', 240, 350, 0, 1, 1, (.5, .45), (.5, .45)), gr), 190, 950, tl, 1.0, angle=-6, enter='slide_l')
    put(fr, mk(kb('enavant', 280, 252, 0, 1, 1, (.5, .5), (.5, .5)), gr), 890, 980, tl, 1.25, angle=6, enter='slide_r')
    put(fr, mk(clip_L('interview', tl, 500, offset=3.7, mode='hold'), gr), 540, 560, tl, 0)
    fr[:] = screen(fr, leak(tl, [(0.0, 1.0, 0.7, 0.45, (1.0, 0.55, 0.2), 0.5 * w), (1.0, 0.0, 0.5, 0.3, (1.0, 0.75, 0.4), 0.3 * w)]))
    T_WIN0.draw(fr, tl, 0.15, per=0.04, fade=0.3, alpha=0.8)
    T_WIN.draw(fr, tl, 0.9, per=0.12, fade=0.35, rise=10)
    T_ATTR.draw(fr, tl, 2.6, per=0.04, fade=0.4)

T_OUT1 = T('outro1', 1260, 82)
def b_outro(fr, tl, D):
    put(fr, mk(kb('sketch', 540, 555, 0, 1, 1, (.5, .5), (.5, .5)), WARM, lift=0.03, contrast=1.02), 540, 690, tl, 0, dur=0.6)
    T_OUT1.draw(fr, tl, 0.5, per=0.1, fade=0.4, rise=10)
    typewriter(fr, TX['outro2'], tl, 1.4, 14, 'type', 34, 1390, (0.85, 0.80, 0.72), cursor=True, alpha=0.9)
    fr *= 1 - sm(prog(tl, D - 0.9, D))

# (fn, beats, entry fx)
SEQ = [
    (b_hook, 5, None),
    (make_flurry(['paris', 'cat', 'coat', 'smile']), 1, 'flash'),
    (b_normal, 6, 'flash'),
    (b_tired, 7, 'whip'),
    (make_flurry(['lighting', 'cig', 'enavant', 'gesture']), 1, 'flash'),
    (b_absurd, 4, 'flash'),
    (b_refuse, 4, 'whip'),
    (b_happy, 4, 'flash'),
    (make_flurry(['cat', 'bed', 'sketch', 'cafe']), 1, 'flash'),
    (b_despair, 5, 'flash'),
    (b_autumn, 5, 'whip'),
    (b_coffee, 5, 'flash'),
    (b_tears, 3, 'flash'),
    (b_world, 5, 'whip'),
    (b_love, 4, 'flash'),
    (make_flurry(['couch', 'facepalm', 'paris', 'smile']), 1, 'flash'),
    (b_secret, 6, 'flash'),
    (b_winter, 8, 'flash'),
    (b_outro, 6, 'fade'),
]
TL = []
_t = 0.0
for fn, beats, fx in SEQ:
    TL.append((fn, _t, beats * BEAT, fx)); _t += beats * BEAT
DUR = _t
NFRAMES = int(round(DUR * FPS))

def render_frame(fi):
    t = fi / FPS
    blk = TL[-1]
    for b in TL:
        if b[1] <= t < b[1] + b[2]:
            blk = b; break
    fn, st, D, fx = blk
    tl = t - st
    fr = blank()
    fn(fr, tl, D)
    if fn is not b_secret:  # centre the composition a little lower (bottom is black)
        fr = np.roll(fr, 90, axis=0); fr[:90] = blank()[:90]
    if fx == 'whip' and tl < 0.2:
        e = eout(tl / 0.2)
        acc = np.zeros_like(fr)
        for k in range(4):
            off = int((1 - e) * 520 + k * 22 * (1 - e))
            acc += np.roll(fr, off, axis=0) if off else fr
        fr = acc / 4
        cut = int((1 - e) * 520)
        if cut > 0: fr[:cut] *= 0.0
    elif fx == 'flash' and tl < 0.13:
        k = (1 - tl / 0.13) ** 1.5
        fr = fr * (1 - 0.85 * k) + np.asarray((1.0, 0.98, 0.95), F32) * 0.85 * k
    elif fx == 'fade' and tl < 0.3:
        fr *= sm(tl / 0.3)
    if fn is b_hook and 1.75 <= tl < 1.95:  # accent shake on "seen"
        a = int(10 * (1 - (tl - 1.75) / 0.2))
        fr = np.roll(fr, (a if fi % 2 else -a), axis=1)
    return post(fr, fi, t, grain=0.04, vig=0.6, bl=0.15)

def to_u8(fr):
    return (np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'info':
        print('duration', DUR, 'frames', NFRAMES)
        for fn, st, D, fx in TL:
            print(f'{st:6.2f} {D:4.1f} {fn.__name__}')
    elif cmd == 'preview':
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        for ts in sys.argv[3:]:
            fi = int(round(float(ts) * FPS))
            Image.fromarray(to_u8(render_frame(fi))).save(f'{out}/f_{float(ts):06.2f}.png')
        print('ok')
    elif cmd == 'render':
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                              '-x264-params', 'keyint=30:min-keyint=15', out], stdin=subprocess.PIPE)
        for fi in range(a, b):
            p.stdin.write(to_u8(render_frame(fi)).tobytes())
        p.stdin.close(); p.wait()
        print('done', out, {k: round(v, 3) for k, v in E.MAXS.items()}, flush=True)
