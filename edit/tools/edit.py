# -*- coding: utf-8 -*-
"""to seek the unseen — Albert Camus vertical edit renderer (1080x1920, 30 fps, no audio)."""
import numpy as np, math, os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))  # tools/ (fonts/ y src/)
W, H, FPS = 1080, 1920, 30
LANG = os.environ.get('EDIT_LANG', 'en')
F32 = np.float32

FONTS = {
    'serif_i': S + '/fonts/eb-garamond-latin-400-italic.woff',
    'serif': S + '/fonts/eb-garamond-latin-400-normal.woff',
    'corm_i': S + '/fonts/cormorant-garamond-latin-500-italic.woff',
    'fell_i': S + '/fonts/im-fell-english-latin-400-italic.woff',
    'type': S + '/fonts/special-elite-latin-400-normal.woff',
}
CREAM = (0.96, 0.93, 0.86)
GOLD = (1.0, 0.80, 0.46)
INK = (0.15, 0.11, 0.09)

TX = {
 'en': dict(
  intro1='to seek the unseen.', intro2='(for anyone who has ever felt invisible)',
  winter='in the depth of winter…',
  unseen1='I was looked at,', unseen2='but I wasn’t seen.',
  red='the unreasonable silence of the world.', red_attr='— the myth of sisyphus',
  sis='the struggle itself toward the heights is enough to fill a man’s heart.',
  happy='one must imagine Sisyphus happy.',
  autumn='autumn is a second spring, when every leaf is a flower.',
  coffee='real generosity toward the future lies in giving all to the present.',
  coffee2='damn fine coffee.',
  secret1='when I look at my life and its secret colours, I feel like bursting into tears.',
  secret2='and yet, someone out there sees your secret colours.',
  climax0='in the depth of winter,',
  climax='I finally learned that within me there lay an invincible summer.',
  climax_hl=('invincible', 'summer.'),
  attr='— albert camus',
  outro1='you were never unseen.', outro2='to seek the unseen  ·  albert camus, 1913–1960'),
 'es': dict(
  intro1='to seek the unseen.', intro2='(para quien alguna vez se sintió invisible)',
  winter='en lo más profundo del invierno…',
  unseen1='me miraban,', unseen2='pero no me veían.',
  red='el silencio irrazonable del mundo.', red_attr='— el mito de sísifo',
  sis='la lucha por llegar a las cumbres basta para llenar un corazón de hombre.',
  happy='hay que imaginarse a Sísifo feliz.',
  autumn='el otoño es una segunda primavera, donde cada hoja es una flor.',
  coffee='la verdadera generosidad con el futuro consiste en darlo todo al presente.',
  coffee2='damn fine coffee.',
  secret1='cuando miro mi vida y sus colores secretos, siento ganas de echarme a llorar.',
  secret2='y aun así, alguien ahí fuera ve tus colores secretos.',
  climax0='en lo más profundo del invierno,',
  climax='aprendí por fin que había en mí un verano invencible.',
  climax_hl=('verano', 'invencible.'),
  attr='— albert camus',
  outro1='nunca fuiste invisible.', outro2='to seek the unseen  ·  albert camus, 1913–1960'),
}[LANG]

# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))
def sm(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def eout(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def eio(x):
    x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def lerp(a, b, t):
    return a + (b - a) * t
def prog(t, a, b):
    return clamp((t - a) / (b - a))
def lerp3(a, b, t):
    return tuple(lerp(x, y, t) for x, y in zip(a, b))

# ------------------------------------------------------------------ images
_C = {}
def img_L(name):
    k = ('L', name)
    if k not in _C:
        # native-resolution source crops (no upscaling anywhere)
        im = Image.open(f'{S}/src/{name}.png').convert('L')
        _C[k] = im
    return _C[k]

MAXS = {}
def kb_params(name, ow, oh, t, z0, z1, c0, c1):
    im0 = img_L(name); sw0, sh0 = im0.size
    e = eio(t); z = lerp(z0, z1, e)
    s0 = max(ow / sw0, oh / sh0) * z          # scale relative to ORIGINAL pixels
    if s0 > MAXS.get(name, 0):
        MAXS[name] = s0
        if s0 > 1.001:
            print(f'WARNING upscale {name} {s0:.3f}', file=sys.stderr)
    cx, cy = lerp(c0[0], c1[0], e), lerp(c0[1], c1[1], e)
    vw, vh = ow / s0, oh / s0
    cx = clamp(cx * sw0, vw / 2, sw0 - vw / 2); cy = clamp(cy * sh0, vh / 2, sh0 - vh / 2)
    return s0, cx, cy

def kb_map(name, ow, oh, t, z0, z1, c0, c1, u, v):
    """where normalized source point (u,v) lands in the output"""
    s0, cx, cy = kb_params(name, ow, oh, t, z0, z1, c0, c1)
    sw0, sh0 = img_L(name).size
    return (u * sw0 - cx) * s0 + ow / 2, (v * sh0 - cy) * s0 + oh / 2

def prepared(name, ow, oh, zmax):
    k = ('P', name, ow, oh, round(zmax, 3))
    if k not in _C:
        im = img_L(name); sw, sh = im.size
        s = max(ow / sw, oh / sh) * zmax
        if s < 1:
            im = im.resize((max(1, round(sw * s)), max(1, round(sh * s))), Image.LANCZOS)
        _C[k] = im
    return _C[k]

def kb(name, ow, oh, t, z0, z1, c0, c1, rot=0.0):
    """Ken-Burns crop. returns float32 luminance (oh, ow) in 0..1"""
    zmax = max(z0, z1)
    s0, cx0, cy0 = kb_params(name, ow, oh, t, z0, z1, c0, c1)
    sw0 = img_L(name).size[0]
    im = prepared(name, ow, oh, zmax); sw, sh = im.size
    r = sw / sw0                      # pre-downscale ratio of the working copy
    s = s0 / r; cx, cy = cx0 * r, cy0 * r
    vw, vh = ow / s, oh / s
    if rot:
        a = math.radians(rot); ca, sa = math.cos(a) / s, math.sin(a) / s
        # map output (x,y) around its centre into source around (cx,cy)
        ox, oy = ow / 2, oh / 2
        data = (ca, sa, cx - ca * ox - sa * oy, -sa, ca, cy + sa * ox - ca * oy)
    else:
        data = (1 / s, 0, cx - vw / 2, 0, 1 / s, cy - vh / 2)
    out = im.transform((ow, oh), Image.AFFINE, data, resample=Image.BICUBIC)
    return np.asarray(out, dtype=F32) / 255.0

def tone(L, sh, hi, lift=0.035, top=0.965, contrast=1.06, gamma=1.0):
    L = np.clip((L - 0.5) * contrast + 0.5, 0, 1)
    if gamma != 1.0:
        L = L ** gamma
    L = lift + (top - lift) * L
    sh = np.asarray(sh, F32); hi = np.asarray(hi, F32)
    Lx = L[..., None]
    return (Lx * (sh + (hi - sh) * Lx)).astype(F32)

COLD = ((0.84, 0.94, 1.10), (0.98, 1.0, 1.03))
SILVER = ((0.93, 0.97, 1.04), (1.02, 1.0, 0.97))
WARM = ((1.02, 0.92, 0.80), (1.07, 1.0, 0.86))
AMBER = ((1.06, 0.86, 0.66), (1.10, 0.99, 0.80))
GOLDT = ((1.10, 0.84, 0.58), (1.12, 1.0, 0.78))

def blend(dst, src, a):
    """dst (h,w,3), src (h,w,3) or color tuple, a (h,w) alpha"""
    a3 = a[..., None]
    if isinstance(src, tuple):
        src = np.asarray(src, F32)
    dst *= (1 - a3); dst += src * a3

def paste(fr, arr, x, y, alpha=None, a_mul=1.0, mode='normal'):
    """paste arr (h,w,3) at integer pos with optional alpha (h,w)"""
    h, w = arr.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(fr.shape[1], x + w), min(fr.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = arr[y0 - y:y1 - y, x0 - x:x1 - x]
    d = fr[y0:y1, x0:x1]
    if alpha is None:
        a = None
    else:
        a = alpha[y0 - y:y1 - y, x0 - x:x1 - x] * a_mul
    if mode == 'add':
        d += sub * (a[..., None] if a is not None else a_mul)
    elif mode == 'screen':
        s = sub * (a[..., None] if a is not None else a_mul)
        d[:] = 1 - (1 - d) * (1 - s)
    else:
        if a is None:
            if a_mul >= 1:
                d[:] = sub
            else:
                d *= (1 - a_mul); d += sub * a_mul
        else:
            blend(d, sub, a)

# ------------------------------------------------------------------ text
_FONT = {}
def font(key, size):
    k = (key, size)
    if k not in _FONT:
        _FONT[k] = ImageFont.truetype(FONTS[key], size)
    return _FONT[k]

class Text:
    def __init__(self, text, fkey, size, y, color=CREAM, maxw=900, lh=1.24, cx=W / 2,
                 shadow=0.62, glow=11, hl=(), hl_color=GOLD, anchor='center', ink=False, track=0):
        f = font(fkey, size)
        self.items = []
        paras = text.split('\n')
        lines = []
        sp = f.getlength(' ') + track
        def wrap(words, mw):
            out = []; cur = []; cw = 0
            for wd in words:
                wl = f.getlength(wd)
                if cur and cw + sp + wl > mw:
                    out.append(cur); cur = [wd]; cw = wl
                else:
                    cw = cw + (sp if cur else 0) + wl; cur.append(wd)
            out.append(cur)
            return out
        for p in paras:
            words = p.split(' ')
            base = wrap(words, maxw)
            if len(base) > 1:  # balance: narrowest width that keeps the same line count
                lo, hi = maxw * 0.4, maxw
                for _ in range(18):
                    mid = (lo + hi) / 2
                    if len(wrap(words, mid)) > len(base): lo = mid
                    else: hi = mid
                base = wrap(words, hi + 0.5)
            lines += base
        lhp = size * lh
        y0 = y - (len(lines) * lhp) / 2 if anchor == 'center' else y
        self.bottom = y0 + len(lines) * lhp
        pad = int(glow * 2.6) + 6
        asc, desc = f.getmetrics()
        idx = 0
        for li, ln in enumerate(lines):
            tw = sum(f.getlength(w) for w in ln) + sp * (len(ln) - 1)
            x = cx - tw / 2
            for wd in ln:
                wl = f.getlength(wd)
                cw, ch = int(math.ceil(wl)) + 2 * pad, asc + desc + 2 * pad
                im = Image.new('L', (cw, ch), 0)
                ImageDraw.Draw(im).text((pad, pad), wd, font=f, fill=255)
                a = np.asarray(im, F32) / 255
                ab = np.asarray(im.filter(ImageFilter.GaussianBlur(5)), F32) / 255
                sa = np.asarray(im.filter(ImageFilter.GaussianBlur(glow)), F32) / 255
                sa = np.clip(sa * 2.2, 0, 1)
                col = hl_color if wd in hl else color
                self.items.append(dict(a=a, ab=ab, sa=sa, x=int(round(x - pad)), y=int(round(y0 + li * lhp - pad)),
                                       col=np.asarray(col, F32), i=idx))
                x += wl + sp; idx += 1
        self.n = idx
        self.shadow = shadow
        self.ink = ink

    def draw(self, fr, t, t0, per=0.12, fade=0.55, t_out=None, out=0.6, rise=18, alpha=1.0, order=None):
        if t < t0:
            return
        for it in self.items:
            st = t0 + it['i'] * per
            p = eout(prog(t, st, st + fade))
            if t_out is not None:
                p *= 1 - sm(prog(t, t_out, t_out + out))
            p *= alpha
            if p <= 0.003:
                continue
            dy = int(round((1 - p) * rise)) if t_out is None or t < t_out else 0
            x, y = it['x'], it['y'] + dy
            h, w = it['a'].shape
            x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
            if x1 <= x0 or y1 <= y0:
                continue
            sl = (slice(y0 - y, y1 - y), slice(x0 - x, x1 - x))
            d = fr[y0:y1, x0:x1]
            if self.shadow > 0:
                sa = it['sa'][sl] * (self.shadow * p)
                d *= (1 - sa[..., None])
            k = sm(p * 1.4)
            a = (it['ab'][sl] * (1 - k) + it['a'][sl] * k) * p
            blend(d, (float(it['col'][0]), float(it['col'][1]), float(it['col'][2])), a)

def typewriter(fr, text, t, t0, cps, fkey, size, cy, color=CREAM, cursor=True, alpha=1.0, glow=8):
    f = font(fkey, size)
    n = int(max(0, (t - t0)) * cps)
    full_w = f.getlength(text)
    x0 = int(W / 2 - full_w / 2)
    asc, desc = f.getmetrics()
    pad = 30
    im = Image.new('L', (int(full_w) + 2 * pad + 40, asc + desc + 2 * pad), 0)
    dr = ImageDraw.Draw(im)
    s = text[:min(n, len(text))]
    if s:
        dr.text((pad, pad), s, font=f, fill=255)
    if cursor and t >= t0 - 0.6:
        blink = (int(t * 2.2) % 2 == 0) or n < len(text)
        if blink:
            cx = pad + f.getlength(s) + 4
            dr.rectangle([cx, pad + 4, cx + 3, pad + asc + desc - 4], fill=200)
    a = np.asarray(im, F32) / 255 * alpha
    sa = np.clip(np.asarray(im.filter(ImageFilter.GaussianBlur(glow)), F32) / 255 * 2, 0, 1) * 0.6 * alpha
    y = int(cy - (asc + desc) / 2 - pad)
    x = x0 - pad
    h, w = a.shape
    d = fr[y:y + h, x:x + w]
    d *= (1 - sa[..., None])
    blend(d, color, a)

# ------------------------------------------------------------------ particles
_SPR = {}
def disc(r, soft=1.5, bokeh=False):
    k = (round(r * 2) / 2, soft, bokeh)
    if k not in _SPR:
        r = k[0]; n = int(math.ceil(r * 2.4)) + 3
        yy, xx = np.mgrid[0:2 * n + 1, 0:2 * n + 1].astype(F32) - n
        d = np.sqrt(xx * xx + yy * yy) / max(r, 0.6)
        if bokeh:
            a = np.clip((1.0 - d) / 0.12, 0, 1) * (0.55 + 0.45 * np.clip(d, 0, 1) ** 3)
        else:
            a = np.exp(-(d * 1.35) ** 2 * soft)
        _SPR[k] = a.astype(F32)
    return _SPR[k]

class Flakes:
    def __init__(self, n, seed, rmin, rmax, vmin, vmax, alpha, soft=1.5, bokeh=False, wind=12, amp=(8, 40)):
        g = np.random.default_rng(seed)
        self.x = g.uniform(-60, W + 60, n); self.y = g.uniform(-60, H + 60, n)
        self.r = g.uniform(rmin, rmax, n); self.v = g.uniform(vmin, vmax, n)
        self.amp = g.uniform(*amp, n); self.f = g.uniform(0.08, 0.35, n); self.ph = g.uniform(0, 6.28, n)
        self.al = g.uniform(0.45, 1.0, n) * alpha; self.tw = g.uniform(0.5, 2.5, n)
        self.soft, self.bokeh, self.wind = soft, bokeh, wind

    def draw(self, fr, teff, tsw, color=(1, 1, 1), amul=1.0, mode='normal', twinkle=0.0):
        if amul <= 0.002:
            return
        col = np.asarray(color, F32)
        Hh = H + 120
        ys = (self.y + self.v * teff + 60) % Hh - 60
        xs = (self.x + self.amp * np.sin(self.f * 6.283 * tsw + self.ph) + self.wind * teff + 60) % (W + 120) - 60
        for i in range(len(self.x)):
            sp = disc(self.r[i], self.soft, self.bokeh)
            h, w = sp.shape
            x, y = int(xs[i] - w / 2), int(ys[i] - h / 2)
            a_m = self.al[i] * amul
            if twinkle:
                a_m *= 1 - twinkle * (0.5 + 0.5 * math.sin(tsw * self.tw[i] * 6.0 + self.ph[i]))
            x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
            if x1 <= x0 or y1 <= y0:
                continue
            a = sp[y0 - y:y1 - y, x0 - x:x1 - x] * a_m
            d = fr[y0:y1, x0:x1]
            if mode == 'add':
                d += col * a[..., None]
            else:
                blend(d, col, a)

def make_leaf(g, size, color, kind):
    s = size * 2
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    c = s / 2
    pts = []
    if kind == 0:  # maple-ish
        for k in range(160):
            th = k / 160 * 2 * math.pi
            lobe = abs(math.cos(2.5 * (th - math.pi / 2))) ** 0.6
            r = (0.30 + 0.62 * lobe) * (0.92 + 0.08 * math.sin(th * 17)) * s * 0.42
            if math.sin(th) > 0.82:  # notch at stem
                r *= 0.55
            pts.append((c + r * math.cos(th), c - r * math.sin(th) * 0.95))
    else:  # birch / beech
        for k in range(120):
            u = k / 119
            hw = (math.sin(math.pi * u) ** 0.85) * s * (0.20 if kind == 1 else 0.27)
            yy = c - s * 0.40 + u * s * 0.80
            serr = 1 + 0.06 * math.sin(u * 60)
            pts.append((c + hw * serr, yy))
        for k in range(119, -1, -1):
            u = k / 119
            hw = (math.sin(math.pi * u) ** 0.85) * s * (0.20 if kind == 1 else 0.27)
            yy = c - s * 0.40 + u * s * 0.80
            serr = 1 + 0.06 * math.sin(u * 60 + 1)
            pts.append((c - hw * serr, yy))
    r, gg, b = [int(v * 255) for v in color]
    dr.polygon(pts, fill=(r, gg, b, 255))
    # tonal variation
    arr = np.asarray(im).astype(F32)
    yy, xx = np.mgrid[0:s, 0:s].astype(F32) / s
    shade = 0.82 + 0.3 * (1 - yy) * (0.6 + 0.4 * xx) + 0.08 * np.sin(xx * 23 + yy * 9)
    arr[..., :3] *= shade[..., None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGBA')
    dr = ImageDraw.Draw(im)
    vein = (int(r * 0.6), int(gg * 0.55), int(b * 0.5), 200)
    if kind == 0:
        for th in [90, 18, 162, -36, 216]:
            a = math.radians(th)
            dr.line([(c, c + s * 0.1), (c + math.cos(a) * s * 0.36, c - math.sin(a) * s * 0.36)], fill=vein, width=max(1, s // 70))
        dr.line([(c, c + s * 0.1), (c, c + s * 0.47)], fill=vein, width=max(2, s // 45))
    else:
        dr.line([(c, c - s * 0.38), (c, c + s * 0.47)], fill=vein, width=max(2, s // 55))
        for k in range(1, 7):
            yv = c - s * 0.36 + k * s * 0.1
            for sgn in (-1, 1):
                dr.line([(c, yv), (c + sgn * s * 0.17, yv - s * 0.08)], fill=vein, width=max(1, s // 90))
    im = im.resize((size, size), Image.LANCZOS)
    return im

class Leaves:
    PAL = [(0.66, 0.24, 0.07), (0.86, 0.50, 0.12), (0.78, 0.60, 0.22), (0.52, 0.12, 0.06), (0.60, 0.36, 0.14), (0.90, 0.40, 0.10)]
    def __init__(self, n, seed):
        g = np.random.default_rng(seed)
        self.L = []
        for i in range(n):
            depth = g.uniform(0, 1)
            size = int(lerp(46, 150, depth ** 1.6))
            spr = make_leaf(g, size, self.PAL[i % len(self.PAL)], int(g.integers(0, 3)))
            if depth > 0.85:
                spr = spr.filter(ImageFilter.GaussianBlur(4 + 6 * (depth - 0.85) / 0.15))
            elif depth < 0.25:
                spr = spr.filter(ImageFilter.GaussianBlur(1.6))
            self.L.append(dict(spr=spr, x=g.uniform(-50, W + 50), y=g.uniform(-200, H), v=lerp(70, 210, depth) * g.uniform(.8, 1.2),
                               amp=g.uniform(30, 110), f=g.uniform(0.15, 0.4), ph=g.uniform(0, 6.28), rot=g.uniform(0, 360),
                               rs=g.uniform(-70, 70), fs=g.uniform(0.6, 2.2), a=lerp(0.75, 1.0, depth), depth=depth))
        self.L.sort(key=lambda d: d['depth'])

    def draw(self, fr, t, amul=1.0, layer=None):
        for d in self.L:
            if layer == 'back' and d['depth'] > 0.85: continue
            if layer == 'front' and d['depth'] <= 0.85: continue
            y = (d['y'] + d['v'] * t + 200) % (H + 400) - 200
            x = d['x'] + d['amp'] * math.sin(d['f'] * 6.283 * t + d['ph']) + 25 * t
            fl = math.cos(d['fs'] * t + d['ph'])
            spr = d['spr']; w, h = spr.size
            sw = max(3, int(w * (0.18 + 0.82 * abs(fl))))
            im = spr.resize((sw, h), Image.BILINEAR).rotate(d['rot'] + d['rs'] * t + 25 * math.sin(t * 1.3 + d['ph']), resample=Image.BICUBIC, expand=True)
            arr = np.asarray(im, F32) / 255
            rgb = arr[..., :3] * (0.75 + 0.25 * abs(fl)); a = arr[..., 3]
            hh, ww = a.shape
            paste(fr, rgb, int(x - ww / 2), int(y - hh / 2), a, d['a'] * amul)

# ------------------------------------------------------------------ post fx
_G = {}
def grain_fields():
    if 'g' not in _G:
        g = np.random.default_rng(7)
        fl = []
        for i in range(6):
            n = g.normal(0, 1, (H // 2 + 80, W // 2 + 80)).astype(F32)
            im = Image.fromarray(np.clip(n * 40 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.45))
            im = im.resize(((W // 2 + 80) * 2, (H // 2 + 80) * 2), Image.BILINEAR)
            fl.append(((np.asarray(im, F32) - 128) / 40).astype(np.float16))
        _G['g'] = fl
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.62)) ** 2)
        _G['vig'] = (1 - 0.62 * np.clip((r - 0.42) / 0.75, 0, 1) ** 1.7).astype(F32)
    return _G['g'], _G['vig']

def bloom(fr, strength=0.22, thr=0.6, rad=14):
    small = fr[::4, ::4]
    hl = np.clip((small - thr) / (1 - thr), 0, 1)
    im = Image.fromarray((hl * 255).astype(np.uint8), 'RGB').filter(ImageFilter.GaussianBlur(rad)).resize((W, H), Image.BILINEAR)
    b = np.asarray(im, F32) / 255 * strength
    return 1 - (1 - fr) * (1 - b)

def leak(t, centers, size=(270, 480)):
    """warm light leak: list of (cx,cy,rx,ry,color,intensity) in normalized coords"""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(F32)
    out = np.zeros((h, w, 3), F32)
    for cx, cy, rx, ry, col, it in centers:
        if it <= 0: continue
        d = ((xx / w - cx) / rx) ** 2 + ((yy / h - cy) / ry) ** 2
        out += np.exp(-d)[..., None] * np.asarray(col, F32) * it
    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGB').resize((W, H), Image.BILINEAR)
    return np.asarray(im, F32) / 255

def screen(fr, layer):
    return 1 - (1 - fr) * (1 - layer)

def post(fr, fidx, t, grain=0.055, vig=1.0, bl=0.22, dust=True):
    fields, vg = grain_fields()
    fr = bloom(fr, bl)
    # subtle exposure flicker
    fl = 1 + 0.012 * math.sin(t * 23.0) * math.sin(t * 3.7) + 0.006 * math.sin(t * 61)
    fr *= fl
    if vig:
        fr *= (1 - vig + vig * vg)[..., None]
    g = np.random.default_rng(fidx * 7919 + 13)
    if dust:
        for _ in range(int(g.integers(0, 4))):
            x, y = int(g.uniform(0, W)), int(g.uniform(0, H)); r = g.uniform(1.0, 3.2)
            sp = disc(r, 2.0)
            col = (0.02, 0.02, 0.02) if g.random() < 0.6 else (0.95, 0.93, 0.9)
            hh, ww = sp.shape
            paste(fr, np.ones((hh, ww, 3), F32) * np.asarray(col, F32), x - ww // 2, y - hh // 2, sp, 0.55)
        if g.random() < 0.07:
            x = int(g.uniform(80, W - 80)); a = g.uniform(0.05, 0.14)
            fr[:, x:x + 2] = fr[:, x:x + 2] * (1 - a) + 0.9 * a
        if g.random() < 0.02:  # hair
            x, y = int(g.uniform(100, W - 300)), int(g.uniform(100, H - 300))
            im = Image.new('L', (220, 220), 0); dd = ImageDraw.Draw(im)
            pts = [(10 + k * 10, 110 + 40 * math.sin(k * 0.6 + g.random())) for k in range(21)]
            dd.line(pts, fill=255, width=2)
            a = np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), F32) / 255
            paste(fr, np.zeros((220, 220, 3), F32), x, y, a, 0.5)
    f = fields[fidx % 6]
    ox, oy = int(g.integers(0, 150)), int(g.integers(0, 150))
    gr = f[oy:oy + H, ox:ox + W].astype(F32)
    L = fr.mean(axis=2)
    amp = grain * (0.35 + 2.6 * L * (1 - L))
    fr += (gr * amp)[..., None]
    return np.clip(fr, 0, 1)

# ------------------------------------------------------------------ shared backgrounds
def paper():
    if 'paper' not in _G:
        g = np.random.default_rng(3)
        lo = g.normal(0, 1, (24, 14)).astype(F32)
        lo = np.asarray(Image.fromarray(((lo * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), F32) / 255
        fine = g.normal(0, 1, (H, W)).astype(F32)
        fine = np.asarray(Image.fromarray(np.clip(fine * 30 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9)), F32) / 255 - 0.5
        fib = g.normal(0, 1, (H // 4, W)).astype(F32)
        fib = np.asarray(Image.fromarray(np.clip(fib * 40 + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2)), F32) / 255 - 0.5
        base = np.asarray((0.90, 0.85, 0.75), F32)
        p = base * (0.93 + 0.09 * lo[..., None]) + 0.05 * fine[..., None] + 0.03 * fib[..., None]
        yy, xx = np.mgrid[0:H, 0:W].astype(F32)
        r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
        p *= (1 - 0.35 * np.clip(r - 0.25, 0, 1) ** 1.4)[..., None] * np.asarray((1, 0.985, 0.96), F32)
        _G['paper'] = p.astype(F32)
    return _G['paper'].copy()

# ================================================================== SCENES
SNOW_FAR = Flakes(260, 1, 1.2, 2.6, 60, 120, 0.75, wind=10)
SNOW_MID = Flakes(90, 2, 3.0, 5.5, 110, 190, 0.85, wind=16)
SNOW_NEAR = Flakes(14, 3, 16, 34, 200, 320, 0.22, bokeh=True, wind=25, amp=(20, 60))
DUST = Flakes(70, 11, 1.0, 2.6, -14, -4, 0.7, wind=6, amp=(10, 30))
PAPER_C = (0.95, 0.93, 0.88)

def snow(fr, t, amul=1.0, color=(1, 1, 1)):
    SNOW_FAR.draw(fr, t, t, color, 0.8 * amul)
    SNOW_MID.draw(fr, t, t, color, 0.9 * amul)
    SNOW_NEAR.draw(fr, t, t, color, amul)

def vgrad(top, bot, pw=1.0):
    v = (np.linspace(0, 1, H, dtype=F32) ** pw)[:, None, None]
    return (np.asarray(top, F32) * (1 - v) + np.asarray(bot, F32) * v) * np.ones((1, W, 1), F32)

def shadow_sprite(w, h, rad=28):
    k = ('shadow', w, h, rad)
    if k not in _C:
        pad = rad * 3
        im = Image.new('L', (w + 2 * pad, h + 2 * pad), 0)
        ImageDraw.Draw(im).rectangle([pad, pad, pad + w, pad + h], fill=255)
        _C[k] = (np.asarray(im.filter(ImageFilter.GaussianBlur(rad)), F32) / 255, pad)
    return _C[k]

def hero(fr, name, w, h, t, D, z0, z1, c0, c1, cx, cy, grade, border=14, bottom=None, frame_col=PAPER_C,
         alpha=1.0, shadow=0.7, lift=0.045, contrast=1.08, post_fn=None):
    """un-rotated print with live Ken-Burns inside (scale <= native). (cx,cy) = centre of the card"""
    bottom = border if bottom is None else bottom
    L = kb(name, w, h, t / D, z0, z1, c0, c1)
    pic = tone(L, *grade, lift=lift, contrast=contrast)
    if post_fn:
        post_fn(pic)
    cw, ch = w + 2 * border, h + border + bottom
    card = np.empty((ch, cw, 3), F32); card[:] = np.asarray(frame_col, F32)
    card[border:border + h, border:border + w] = pic
    x, y = int(round(cx - cw / 2)), int(round(cy - ch / 2))
    if shadow:
        sh, pad = shadow_sprite(cw, ch, 26)
        paste(fr, np.zeros(sh.shape + (3,), F32), x - pad + 10, y - pad + 20, sh, shadow * alpha)
    paste(fr, card, x, y, None, alpha)
    return x, y, cw, ch

class Card:
    """static rotated print; luminance cached, toned per frame (cheap)."""
    def __init__(self, name, w, h, c=(0.5, 0.5), z=1.0, angle=0.0, border=12, bottom=None):
        bottom = border if bottom is None else bottom
        L = kb(name, w, h, 0, z, z, c, c)
        cw, ch = w + 2 * border, h + border + bottom
        pad = 60
        Wc, Hc = cw + 2 * pad, ch + 2 * pad
        Lc = np.zeros((Hc, Wc), F32); pm = np.zeros((Hc, Wc), F32); ca = np.zeros((Hc, Wc), F32)
        Lc[pad + border:pad + border + h, pad + border:pad + border + w] = L
        pm[pad + border:pad + border + h, pad + border:pad + border + w] = 1
        ca[pad:pad + ch, pad:pad + cw] = 1
        sa = np.asarray(Image.fromarray((ca * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(16)), F32) / 255
        def rot(a, res=Image.BICUBIC):
            im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).rotate(angle, resample=res, expand=False)
            return np.asarray(im, F32) / 255
        self.L, self.pm, self.ca, self.sa = rot(Lc), rot(pm), rot(ca), rot(sa)
        self.w, self.h = Wc, Hc

    def draw(self, fr, cx, cy, grade, alpha=1.0, lift=0.045, contrast=1.06, dim=1.0, shadow=0.75):
        if alpha <= 0.003:
            return
        rgb = tone(self.L, *grade, lift=lift, contrast=contrast) * dim
        pm = self.pm[..., None]
        rgb = rgb * pm + np.asarray(PAPER_C, F32) * dim * (1 - pm)
        x, y = int(round(cx - self.w / 2)), int(round(cy - self.h / 2))
        paste(fr, np.zeros((self.h, self.w, 3), F32), x + 10, y + 18, self.sa, shadow * alpha)
        paste(fr, rgb, x, y, self.ca, alpha)

_CARDS = {}
def card(key, *a, **k):
    if key not in _CARDS:
        _CARDS[key] = Card(*a, **k)
    return _CARDS[key]

def charcoal():
    if 'charcoal' not in _G:
        p = paper()
        _G['charcoal'] = (p * np.asarray((0.075, 0.072, 0.075), F32) / np.asarray((0.90, 0.85, 0.75), F32)).astype(F32)
    return _G['charcoal'].copy()

# ---------- 1 intro
def sc_intro(t, D):
    fr = np.zeros((H, W, 3), F32) + np.asarray((0.018, 0.016, 0.02), F32)
    SNOW_FAR.draw(fr, t, t, (0.9, 0.92, 1.0), 0.55 * sm(prog(t, 0.6, 2.5)))
    SNOW_NEAR.draw(fr, t, t, (0.9, 0.92, 1.0), 0.6 * sm(prog(t, 1.0, 3.0)))
    typewriter(fr, TX['intro1'], t, 0.7, 11, 'type', 58, 900, CREAM)
    T_INTRO2.draw(fr, t, 2.75, per=0.07, fade=0.8)
    return fr

# ---------- 2 winter: night woods in fog (Twin Peaks firs), a single print
_PN = {}
def pine_layer(seed, n, ybase, hmin, hmax, wf=0.30, xs=None, fill_below=True, bw=1.0):
    g = np.random.default_rng(seed)
    M = 240
    SS = 2
    im = Image.new('L', ((W + 2 * M) * SS, H * SS), 0); dr = ImageDraw.Draw(im)
    if xs is None:
        xs = np.sort(g.uniform(-M * 0.8, W + M * 0.8, n))
    for x in xs:
        hgt = g.uniform(hmin, hmax); base = ybase + g.uniform(-25, 25)
        top = base - hgt; wmax = hgt * wf * g.uniform(0.85, 1.15)
        X = (x + M) * SS
        dr.line([(X, top * SS), (X, (base + 400) * SS)], fill=255, width=int(max(2, wmax * 0.06) * SS))
        step = max(3.0, hgt / 120)
        yb = top + 2
        while yb < base:
            fr_ = (yb - top) / hgt
            for side in (-1, 1):
                half = wmax * (fr_ ** 0.85) * g.uniform(0.55, 1.15) + 2
                droop = g.uniform(0.15, 0.45)
                tip = (X + side * half * SS, (yb + droop * half) * SS)
                mid = (X + side * half * 0.55 * SS, (yb + droop * half * 0.25) * SS)
                wdt = int(max(1, (1.2 + 3.5 * fr_) * bw * SS))
                dr.line([(X, yb * SS), mid, tip], fill=255, width=wdt)
                if half > 12:
                    for _ in range(2):
                        u = g.uniform(0.3, 0.9)
                        px, py = X + side * half * u * SS, (yb + droop * half * u * u) * SS
                        dr.line([(px, py), (px + side * half * 0.18 * SS, py + half * 0.22 * SS)], fill=255, width=max(1, wdt - 1))
            yb += step * g.uniform(0.7, 1.3)
    if fill_below:
        dr.rectangle([0, (ybase + 30) * SS, (W + 2 * M) * SS, H * SS], fill=255)
    return np.asarray(im.resize((W + 2 * M, H), Image.LANCZOS), F32) / 255

def woods(fr, t, warm=0.0):
    if 'far' not in _PN:
        far = pine_layer(41, 34, 1440, 200, 360)
        _PN['far'] = np.asarray(Image.fromarray((far * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), F32) / 255
        mid = pine_layer(42, 20, 1600, 330, 520)
        _PN['mid'] = np.asarray(Image.fromarray((mid * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), F32) / 255
        _PN['near'] = pine_layer(43, 0, 2150, 1500, 1750, wf=0.24, xs=[-60, 30, 1060, 1150, 1240], fill_below=False, bw=1.3)
    M = 240
    yy = np.linspace(0, 1, H, dtype=F32)[:, None]
    for key, col, sp in (('far', (0.33, 0.37, 0.43), 3), ('mid', (0.13, 0.15, 0.19), 6)):
        off = int(M - 60 + sp * t) % (2 * M)
        blend(fr, col, _PN[key][:, off:off + W])
        band = np.exp(-((yy - (0.76 if key == 'far' else 0.84)) / 0.05) ** 2) * 0.30
        blend(fr, (0.62, 0.66, 0.72), np.broadcast_to(band, (H, W)))
    # snowy ground
    g_ = np.clip((yy - 0.875) / 0.06, 0, 1) * 0.75
    blend(fr, (0.60, 0.64, 0.70), np.broadcast_to(g_, (H, W)))
    off = int(M - 60 + 14 * t) % (2 * M)
    blend(fr, (0.02, 0.025, 0.035), _PN['near'][:, off:off + W])

def sc_winter(t, D):
    fr = vgrad((0.025, 0.03, 0.045), (0.32, 0.35, 0.40), 1.6)
    SNOW_FAR.draw(fr, t + 4.5, t + 4.5, (0.9, 0.93, 1.0), 0.6)
    woods(fr, t)
    hero(fr, 'paris', 680, 680, t, D, 1.0, 1.055, (0.5, 0.5), (0.5, 0.42), W / 2, 560, COLD, border=14, bottom=14,
         alpha=eout(prog(t, 0.0, 1.0)))
    SNOW_MID.draw(fr, t + 4.5, t + 4.5, (1, 1, 1), 0.9)
    SNOW_NEAR.draw(fr, t + 4.5, t + 4.5, (1, 1, 1), 1.0)
    T_WINTER.draw(fr, t, 1.1, per=0.16, fade=0.8)
    return fr

# ---------- 3 unseen: three prints on charcoal
def sc_unseen(t, D):
    fr = charcoal()
    seen = sm(prog(t, 3.9, 5.0))
    specs = [('enavant', 480, 432, (0.5, 0.5), -3.0, (300, 400), 0.0, (-1, 0)),
             ('lighting', 504, 454, (0.5, 0.5), 2.5, (790, 650), 0.25, (1, 0)),
             ('cig', 436, 392, (0.5, 0.5), -1.5, (400, 1030), 0.5, (-1, 0))]
    for nm, w, h, c, ang, (cx, cy), dl, (dx, dy) in specs:
        p = eout(prog(t, dl, dl + 1.0))
        if p <= 0: continue
        cd = card('u_' + nm, nm, w, h, c, 1.0, ang)
        drift = 8 * math.sin(t * 0.5 + cx)
        dim = 1 - 0.55 * seen
        gr = lerp3(SILVER[0], (1, 1, 1), seen), lerp3(SILVER[1], (1, 1, 1), seen)
        cd.draw(fr, cx + dx * (1 - p) * 700 + drift, cy + dy * (1 - p) * 700, gr, alpha=p, contrast=1.1 - 0.4 * seen, dim=dim)
    T_UNSEEN1.draw(fr, t, 1.5, per=0.15, fade=0.7)
    T_UNSEEN2.draw(fr, t, 3.4, per=0.16, fade=0.8)
    return fr

# ---------- 4 red room
_RR = {}
def rr_grid():
    if 'yy' not in _RR:
        _RR['yy'], _RR['xx'] = np.mgrid[0:H, 0:W].astype(F32)
    return _RR

def curtains(t, h):
    st = rr_grid()
    xx, yy = st['xx'][:h], st['yy'][:h]
    sway = 0.55 * np.sin(yy / 520 + t * 0.7 + xx / 260) + 0.25 * np.sin(yy / 230 - t * 0.45)
    ph = xx / 64.0 * 2 * np.pi / 1.4 + sway + 0.35 * np.sin(xx / 37.0)
    s = (0.5 + 0.5 * np.cos(ph)) ** 1.5
    s2 = 0.5 + 0.5 * np.cos(ph * 0.5 + 1.3)
    shade = 0.25 + 0.75 * (0.75 * s + 0.25 * s2)
    vg = (0.55 + 0.45 * np.clip(yy / h, 0, 1) ** 0.6)
    col = np.asarray((0.55, 0.035, 0.05), F32) * (shade * vg)[..., None]
    col += np.asarray((0.25, 0.03, 0.03), F32) * (s ** 6 * vg)[..., None]
    return col

def sm_arr(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

def chevron_floor(t, hz, speed=55.0):
    st = rr_grid()
    h = H - hz
    yy = st['yy'][:h] + 1.0
    xx = st['xx'][:h]
    f = 900.0; cam_h = 260.0
    z = f * cam_h / (yy + 10.0)
    X = (xx - W / 2) * z / f
    zig = np.abs(((X / 170.0) % 1.0) - 0.5) * 2 * 60.0
    v = (z + speed * t + zig) / 85.0
    fv = v % 1.0
    dv = np.abs(np.gradient(v, axis=0)) + np.abs(np.gradient(v, axis=1)) + 1e-4
    w = np.clip(dv * 0.9, 0.002, 0.5)
    stripe = np.clip(sm_arr((fv - 0.5) / w + 0.5) - sm_arr((fv - 1.0) / w + 0.5) + sm_arr(fv / w + 0.5) - 1.0, 0, 1)
    light = np.asarray((0.86, 0.82, 0.74), F32); dark = np.asarray((0.04, 0.035, 0.035), F32)
    col = dark + (light - dark) * stripe[..., None]
    fog = np.exp(-(z - 230) / 900.0).clip(0, 1)[..., None]
    return (col * fog + np.asarray((0.06, 0.0, 0.01), F32) * (1 - fog)).astype(F32)

def sc_red(t, D):
    hz = 1360
    fr = np.zeros((H, W, 3), F32)
    fr[:hz] = curtains(t, hz)
    fr[hz:] = chevron_floor(t, hz)
    yy = np.arange(H, dtype=F32)
    fr *= (1 - np.exp(-((yy - hz) / 26.0) ** 2) * 0.6)[:, None, None]
    # gilded frame (homecoming-portrait nod) at native resolution
    w, h = 400, 596
    hero(fr, 'gesture', w, h, t, D, 1.0, 1.02, (0.5, 0.5), (0.5, 0.45), W / 2, 700 + 5 * math.sin(t * 0.9), WARM,
         border=22, frame_col=(0.55, 0.45, 0.28), shadow=0.85)
    # inner dark fillet on the frame
    strobe = 1.0
    for c in (1.6, 3.7, 4.35):
        strobe -= 0.45 * math.exp(-((t - c) / 0.05) ** 2)
    fr *= strobe
    fr = screen(fr, leak(t, [(0.5, -0.05, 0.6, 0.25, (0.9, 0.4, 0.3), 0.35)]))
    T_RED.draw(fr, t, 0.9, per=0.14, fade=0.7)
    T_RED_ATTR.draw(fr, t, 2.6, per=0.05, fade=0.6)
    return fr

# ---------- 5 sisyphus (procedural)
def ground(x):
    return 1760 - 600 * sm(clamp((x + 80) / 1200))

def ground_d(x):
    return (ground(x + 1) - ground(x - 1)) / 2

_SIS = {}
def sis_static():
    if 'sky' in _SIS:
        return _SIS
    yy, xx = np.mgrid[0:H, 0:W].astype(F32)
    v = yy / H
    top = np.asarray((0.05, 0.05, 0.075), F32); mid = np.asarray((0.36, 0.24, 0.20), F32); hor = np.asarray((0.92, 0.62, 0.36), F32)
    a = np.clip(v / 0.62, 0, 1)[..., None]
    sky = top * (1 - a) + mid * a
    b = np.clip((v - 0.45) / 0.25, 0, 1)[..., None] ** 1.3
    sky = sky * (1 - b) + hor * b
    sx, sy, sr = 700, 1250, 210
    d = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
    glow = np.exp(-(np.maximum(d - sr, 0) / 260.0) ** 1.2)[..., None] * np.asarray((1.0, 0.72, 0.42), F32) * 0.55
    sky = 1 - (1 - sky) * (1 - glow)
    disc_ = np.clip((sr - d) / 2.5, 0, 1)[..., None]
    sky = sky * (1 - disc_) + np.asarray((1.0, 0.90, 0.70), F32) * disc_
    im = Image.new('L', (W * 2, H * 2), 0)
    pts = [(x * 2, ground(x) * 2) for x in range(-10, W + 11, 4)] + [(W * 2 + 20, H * 2 + 20), (-20, H * 2 + 20)]
    ImageDraw.Draw(im).polygon(pts, fill=255)
    hill = np.asarray(im.resize((W, H), Image.LANCZOS), F32) / 255
    im2 = Image.new('L', (W * 2, H * 2), 0)
    pts2 = [(x * 2, (1430 + 40 * math.sin(x / 170) + 25 * math.sin(x / 61)) * 2) for x in range(-10, W + 11, 4)] + [(W * 2 + 20, H * 2 + 20), (-20, H * 2 + 20)]
    ImageDraw.Draw(im2).polygon(pts2, fill=255)
    far = np.asarray(im2.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2)), F32) / 255
    _SIS.update(sky=sky.astype(F32), hill=hill, far=far)
    return _SIS

def ik(a, b, l1, l2, bend):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    d = max(1e-3, min(math.hypot(dx, dy), l1 + l2 - 0.01))
    ang = math.atan2(dy, dx)
    c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    off = math.acos(c) * bend
    return (ax + l1 * math.cos(ang + off), ay + l1 * math.sin(ang + off))

def draw_sisyphus(X, t):
    SS = 2
    ox, oy = int(X - 260), int(ground(X) - 520)
    cw, ch = 760, 640
    im = Image.new('L', (cw * SS, ch * SS), 0)
    dr = ImageDraw.Draw(im)
    def P(p):
        return ((p[0] - ox) * SS, (p[1] - oy) * SS)
    def line(a, b, w):
        dr.line([P(a), P(b)], fill=255, width=int(w * SS))
        for q in (a, b):
            r = w / 2 * SS; c = P(q)
            dr.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    phi = 2 * math.pi * 0.36 * t
    gy = ground(X)
    bob = 3.5 * math.sin(2 * phi)
    hip = (X, gy - 110 - bob)
    lean = math.radians(54 + 2 * math.sin(2 * phi))
    sh = (hip[0] + 98 * math.sin(lean), hip[1] - 98 * math.cos(lean))
    head = (sh[0] + 33 * math.sin(lean + 0.2), sh[1] - 33 * math.cos(lean + 0.2))
    R = 92
    bx = sh[0] + R
    for _ in range(8):
        nx, ny = ground_d(bx), -1.0
        nn = math.hypot(nx, ny); nx, ny = nx / nn, ny / nn
        c = (bx + R * nx, ground(bx) + R * ny)
        ct = (c[0] - R * 0.93, c[1] - R * 0.36)
        dd = math.hypot(ct[0] - sh[0], ct[1] - sh[1])
        bx += (84 - dd)
    cpx = P(c); rr = R * SS
    dr.ellipse([cpx[0] - rr, cpx[1] - rr, cpx[0] + rr, cpx[1] + rr], fill=255)
    for k in (1, 0):
        pk = phi + k * math.pi
        fx = X - 42 - 44 * math.cos(pk)
        fy = ground(fx) - 5 - 15 * max(0.0, math.sin(pk))
        knee = ik(hip, (fx, fy), 62, 60, -1)
        line(hip, knee, 21); line(knee, (fx, fy), 16)
        line((fx - 6, fy + 2), (fx + 20, fy + 2 + ground_d(fx) * 26), 10)
    line(hip, sh, 33)
    line(((hip[0] + sh[0]) / 2, (hip[1] + sh[1]) / 2), sh, 37)
    nk = (sh[0] + 14 * math.sin(lean + .2), sh[1] - 14 * math.cos(lean + .2))
    line(sh, nk, 14)
    hr = 18 * SS; hp = P(head)
    dr.ellipse([hp[0] - hr, hp[1] - hr, hp[0] + hr, hp[1] + hr], fill=255)
    for off in ((0, 0), (-3, -16)):
        tgt = (c[0] - R * 0.93 + off[0], c[1] - R * 0.36 + off[1])
        el = ik(sh, tgt, 47, 45, 1)
        line(sh, el, 14); line(el, tgt, 12)
    m = im.resize((cw, ch), Image.LANCZOS)
    return np.asarray(m, F32) / 255, ox, oy

def sc_sis(t, D):
    st = sis_static()
    fr = st['sky'].copy()
    DUST.draw(fr, t, t, (1.0, 0.85, 0.6), 0.5, mode='add', twinkle=0.6)
    blend(fr, (0.20, 0.12, 0.10), st['far'] * 0.85)
    for k, (bx0, by0, sp) in enumerate(((120, 640, 38), (260, 560, 30), (60, 720, 44))):
        x = bx0 + sp * t; y = by0 - 6 * t + 10 * math.sin(t * 0.8 + k)
        fl = 9 * math.sin(t * 7 + k * 2)
        im = Image.new('L', (60, 40), 0)
        ImageDraw.Draw(im).line([(8, 20 - fl), (30, 22), (52, 20 - fl)], fill=255, width=3)
        a = np.asarray(im.filter(ImageFilter.GaussianBlur(0.6)), F32) / 255
        paste(fr, np.zeros((40, 60, 3), F32) + 0.06, int(x), int(y), a, 0.85)
    sil = (0.035, 0.022, 0.02)
    blend(fr, sil, st['hill'])
    m, ox, oy = draw_sisyphus(lerp(250, 610, t / D), t)
    paste(fr, np.zeros(m.shape + (3,), F32) + np.asarray(sil, F32), ox, oy, m)
    T_SIS.draw(fr, t, 0.8, per=0.12, fade=0.7)
    T_ATTR_SIS.draw(fr, t, 3.8, per=0.05, fade=0.6)
    return screen(fr, leak(t, [(0.65, 0.65, 0.5, 0.3, (1.0, 0.6, 0.3), 0.25 + 0.05 * math.sin(t))]))

# ---------- 6 happy: the smiling print held against the dusk
def sc_happy(t, D):
    st = sis_static()
    fr = st['sky'][::-1].copy() * 0.55 + vgrad((0.10, 0.06, 0.05), (0.04, 0.03, 0.03)) * 0.45
    DUST.draw(fr, t + 7, t + 7, (1.0, 0.88, 0.65), 0.5, mode='add', twinkle=0.5)
    hero(fr, 'smile', 620, 835, t, D, 1.0, 1.08, (0.5, 0.5), (0.46, 0.36), W / 2, 640, GOLDT, border=14, lift=0.05, contrast=1.05)
    fr = screen(fr, leak(t, [(0.95, 0.05, 0.55, 0.35, (1.0, 0.65, 0.35), 0.5), (0.2, 0.9, 0.4, 0.3, (0.9, 0.4, 0.2), 0.2 * sm(prog(t, 1, 3)))]))
    T_HAPPY.draw(fr, t, 0.5, per=0.13, fade=0.7)
    return fr

# ---------- 7 autumn
LEAVES = None
_AU = {}
def warm_bokeh(t, seed=8, n=34, base=(14, 8, 5), cols=((255, 160, 70), (255, 200, 110), (220, 110, 50)), drift=0.006, it=0.45):
    if seed not in _AU:
        g = np.random.default_rng(seed)
        _AU[seed] = [(g.uniform(0, 1), g.uniform(0, 1), g.uniform(0.02, 0.07), int(g.integers(0, len(cols))), g.uniform(0.3, 0.9), g.uniform(-1, 1)) for _ in range(n)]
    w, h = 270, 480
    im = Image.new('RGB', (w, h), base); dr = ImageDraw.Draw(im)
    for x, y, r, ci, a, vx in _AU[seed]:
        xx = ((x + vx * drift * t) % 1) * w; yy = y * h; rr = r * w
        c = tuple(int(v * a * it) for v in cols[ci])
        dr.ellipse([xx - rr, yy - rr, xx + rr, yy + rr], fill=c)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BICUBIC), F32) / 255

def sc_autumn(t, D):
    global LEAVES
    if LEAVES is None:
        LEAVES = Leaves(22, 5)
    fr = warm_bokeh(t)
    LEAVES.draw(fr, t + 3, layer='back')
    hero(fr, 'cat', 640, 934, t, D, 1.0, 1.08, (0.5, 0.5), (0.48, 0.36), W / 2, 620, AMBER, border=14, lift=0.05)
    fr = screen(fr, leak(t, [(0.0, 0.2, 0.5, 0.4, (1.0, 0.5, 0.15), 0.3), (1.0, 0.85, 0.4, 0.3, (0.9, 0.35, 0.1), 0.22)]))
    T_AUTUMN.draw(fr, t, 0.9, per=0.13, fade=0.7)
    LEAVES.draw(fr, t + 3, layer='front')
    return fr

# ---------- 8 coffee: rain on the window, steam from his cup
_CF = {}
CUP = (0.530, 0.706)
def coffee_static():
    if 'drops' in _CF:
        return _CF
    g = np.random.default_rng(21)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for _ in range(700):
        x, y = g.uniform(0, W), g.uniform(0, H); r = g.uniform(1.5, 6.5) * (1 if g.random() < .85 else 1.8)
        dr.ellipse([x - r, y - r * 1.15, x + r, y + r * 1.15], fill=(10, 8, 6, 70))
        dr.ellipse([x - r * 0.45, y - r * 0.7, x + r * 0.05, y - r * 0.2], fill=(255, 235, 210, 150))
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(0.8)), F32) / 255
    _CF['drops'] = (a[..., :3].copy(), a[..., 3].copy())
    _CF['streaks'] = [(g.uniform(40, W - 40), g.uniform(0, H), g.uniform(120, 340), g.uniform(3, 6)) for _ in range(9)]
    return _CF

def steam(pic, t, X, Y):
    cw, ch = 300, 460
    im = Image.new('L', (cw, ch), 0); dr = ImageDraw.Draw(im)
    for k in range(5):
        ph = k * 1.7
        pts = []
        for j in range(46):
            u = j / 45
            yy = ch - 20 - u * (ch - 40)
            amp = 8 + 55 * u
            xx = cw / 2 + (k - 2) * 7 + amp * math.sin(5.5 * u - 1.6 * t + ph) + 18 * u * math.sin(0.7 * t + k)
            pts.append((xx, yy, u))
        for j in range(len(pts) - 1):
            u = pts[j][2]
            inten = int(255 * (math.sin(math.pi * min(1, u * 1.15)) ** 1.2) * (0.55 + 0.45 * math.sin(t * 1.3 + k * 2.1 + u * 4)))
            dr.line([pts[j][:2], pts[j + 1][:2]], fill=max(0, inten), width=int(6 + 14 * u))
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(10)), F32) / 255 * 0.62
    paste(pic, np.ones((ch, cw, 3), F32) * np.asarray((0.97, 0.95, 0.92), F32), int(X - cw / 2), int(Y - ch + 18), a, 1.0)

def sc_coffee(t, D):
    st = coffee_static()
    fr = warm_bokeh(t, seed=9, n=46, base=(12, 8, 7), cols=((255, 170, 80), (255, 200, 120), (230, 120, 60), (140, 170, 190)), drift=0.01, it=0.55)
    drgb, da = st['drops']
    blend(fr, drgb, da * 0.8)
    for x, y0, v, wdt in st['streaks']:
        y = (y0 + v * t) % (H + 300) - 150
        y_a, y_b = max(0, int(y - 160)), min(H, int(y + 10))
        if y_b <= y_a: continue
        yy = np.arange(y_a, y_b)
        a = np.clip(1 - (y - yy) / 160.0, 0, 1)[:, None] * 0.35
        xs = slice(int(x - wdt / 2), int(x + wdt / 2))
        fr[y_a:y_b, xs] = fr[y_a:y_b, xs] * (1 - a[..., None]) + np.asarray((1, 0.9, 0.78), F32) * a[..., None]
    pw, ph = 950, 628
    args = ('cafe', pw, ph, t / D, 1.0, 1.035, (0.5, 0.5), (0.56, 0.5))
    def add_steam(pic):
        X, Y = kb_map(*args, *CUP)
        steam(pic, t, X, Y)
    hero(fr, 'cafe', pw, ph, t, D, 1.0, 1.035, (0.5, 0.5), (0.56, 0.5), W / 2, 960, WARM, border=14, post_fn=add_steam)
    fr = screen(fr, leak(t, [(0.15, 0.95, 0.5, 0.25, (1.0, 0.55, 0.2), 0.28)]))
    T_COFFEE.draw(fr, t, 0.8, per=0.12, fade=0.7)
    typewriter(fr, TX['coffee2'], t, 3.6, 12, 'type', 34, 1370, CREAM, cursor=True, alpha=0.85)
    return fr

# ---------- 9 secret colours (polaroids on paper)
_PL = {}
def polaroid(name, pw, ph, c, rot_seed):
    k = (name, pw, ph)
    if k in _PL:
        return _PL[k]
    L = kb(name, pw, ph, 0, 1.0, 1.0, c, c)
    rgb = tone(L, *WARM, lift=0.06, contrast=1.04)
    b, bb = 24, 88
    cw, ch = pw + 2 * b, ph + b + bb
    cardi = np.zeros((ch, cw, 3), F32) + np.asarray(PAPER_C, F32)
    cardi[b:b + ph, b:b + pw] = rgb
    pad = 70
    canvas = Image.new('RGBA', (cw + 2 * pad, ch + 2 * pad), (0, 0, 0, 0))
    shadow = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(shadow).rectangle([pad + 10, pad + 18, pad + cw + 10, pad + ch + 18], fill=150)
    canvas.paste((30, 20, 15, 255), (0, 0), shadow.filter(ImageFilter.GaussianBlur(18)))
    canvas.paste(Image.fromarray((np.clip(cardi, 0, 1) * 255).astype(np.uint8), 'RGB'), (pad, pad))
    tape = Image.new('RGBA', (170, 52), (232, 220, 186, 150)).rotate(-8 + 16 * (rot_seed % 2), expand=True, resample=Image.BICUBIC)
    canvas.alpha_composite(tape, (pad + cw // 2 - tape.size[0] // 2, pad - 28))
    _PL[k] = canvas
    return canvas

def sc_secret(t, D):
    fr = paper()
    specs = [('bed', 450, 448, (0.5, 0.5), 290, 470, -7, 0.0),
             ('tree', 340, 437, (0.5, 0.5), 790, 500, 6, 0.35),
             ('facepalm', 640, 356, (0.5, 0.5), 540, 1470, -3, 0.7)]
    wash = sm(prog(t, 1.6, 3.6)) * 0.6
    if wash > 0:
        lk = leak(t, [(0.25, 0.30, 0.35, 0.18, (0.95, 0.55, 0.60), 0.6), (0.78, 0.36, 0.3, 0.16, (0.45, 0.62, 0.90), 0.55),
                      (0.55, 0.78, 0.4, 0.18, (0.95, 0.80, 0.40), 0.6), (0.35, 0.58, 0.3, 0.12, (0.60, 0.85, 0.65), 0.45)], size=(108, 192))
        fr = fr * (1 - wash * lk * 0.55)
    for nm, pw, ph, c, cx, cy, rot, dl in specs:
        p = eout(prog(t, dl, dl + 0.9))
        if p <= 0: continue
        cv = polaroid(nm, pw, ph, c, int(rot))
        ang = rot + 1.5 * math.sin(t * 0.6 + rot) + (1 - p) * 8
        im = cv.rotate(ang, resample=Image.BICUBIC, expand=True)
        arr = np.asarray(im, F32) / 255
        hh, ww = arr.shape[:2]
        paste(fr, arr[..., :3], int(cx - ww / 2 + 6 * math.sin(t * 0.5 + rot)), int(cy - hh / 2 + 5 * math.cos(t * 0.4 + rot) - (1 - p) * 40), arr[..., 3], p)
    T_SECRET1.draw(fr, t, 0.9, per=0.09, fade=0.6, t_out=4.3, out=0.6)
    T_SECRET2.draw(fr, t, 4.8, per=0.13, fade=0.7)
    return fr

# ---------- 10 film strip (two strips, parallax)
_FS = {}
STRIP_NAMES = ['paris', 'coat', 'smile', 'cat', 'bed', 'lighting', 'enavant', 'cig', 'couch', 'facepalm', 'cafe', 'sketch']
def strip():
    if 'strip' in _FS:
        return _FS
    sw, cw, chh, pitch = 640, 520, 370, 410
    n = len(STRIP_NAMES)
    Ht = pitch * n
    s = np.zeros((Ht, sw, 3), F32) + np.asarray((0.045, 0.035, 0.03), F32)
    hm = Image.new('L', (sw, Ht), 0); dh = ImageDraw.Draw(hm)
    for y in range(10, Ht, 52):
        for x in (16, sw - 16 - 30):
            dh.rounded_rectangle([x, y, x + 30, y + 20], radius=5, fill=255)
    holes = np.asarray(hm, F32) / 255
    s = s * (1 - holes[..., None]) + np.asarray((0.85, 0.80, 0.70), F32) * holes[..., None]
    for i, nm in enumerate(STRIP_NAMES):
        L = kb(nm, cw, chh, 0, 1.0, 1.0, (0.5, 0.42), (0.5, 0.42))
        s[i * pitch + 20:i * pitch + 20 + chh, (sw - cw) // 2:(sw + cw) // 2] = tone(L, *WARM, lift=0.05)
    _FS.update(strip=np.concatenate([s, s[:H + 600]], axis=0), Ht=Ht, sw=sw)
    return _FS

def strip_view(off, v, angle, alpha_mul=1.0):
    st = strip()
    acc = None
    nsub = 4
    for k in range(nsub):
        o = int(off - v / FPS * k / nsub) % st['Ht']
        crop = st['strip'][o:o + H + 400]
        acc = crop.copy() if acc is None else acc + crop
    acc /= nsub
    im = Image.fromarray((np.clip(acc, 0, 1) * 255).astype(np.uint8)).rotate(angle, resample=Image.BICUBIC, expand=True)
    a = Image.new('L', (st['sw'], acc.shape[0]), 255).rotate(angle, resample=Image.BICUBIC, expand=True)
    return np.asarray(im, F32) / 255, np.asarray(a, F32) / 255 * alpha_mul

def sc_film(t, D):
    fr = vgrad((0.03, 0.025, 0.02), (0.06, 0.045, 0.035))
    off = 300 * t + 420 * t * t; v = 300 + 840 * t
    arr, a = strip_view(-off * 0.55 + 2000, v * 0.55, 9, 0.35)
    hh, ww = a.shape
    paste(fr, arr * 0.6, (W - ww) // 2 - 330, (H - hh) // 2, a)
    arr, a = strip_view(off, v, -5)
    hh, ww = a.shape
    paste(fr, arr, (W - ww) // 2 + 40, (H - hh) // 2, a)
    return fr

# ---------- 11 climax: a constellation of prints turning to summer
EMBERS = Flakes(140, 31, 1.5, 4.5, 60, 150, 0.9, wind=8, amp=(10, 45))
_CL = {}
def climax_teff(t):
    if 'tab' not in _CL:
        ts = np.linspace(0, 10, 3001)
        vm = 1 - 1.7 * np.array([sm(prog(x, 2.2, 4.6)) for x in ts])
        te = np.concatenate([[0], np.cumsum((vm[1:] + vm[:-1]) / 2 * np.diff(ts))])
        _CL['tab'] = (ts, te)
    ts, te = _CL['tab']
    return float(np.interp(t, ts, te))

CONST = [  # name, w, h, centre(x,y), angle, delay
    ('paris', 290, 290, (190, 250), -7, 0.35),
    ('smile', 250, 337, (545, 215), 3, 0.5),
    ('cat', 236, 344, (890, 260), 6, 0.65),
    ('lighting', 270, 243, (150, 680), -4, 0.8),
    ('sketch', 240, 246, (935, 690), 4, 0.95),
    ('bed', 300, 298, (185, 1080), 5, 1.1),
    ('cafe', 336, 222, (560, 1110), -3, 1.25),
    ('enavant', 290, 261, (905, 1075), -5, 1.4),
]
def sc_climax(t, D):
    w = sm(prog(t, 2.2, 5.0))
    fr = vgrad(lerp3((0.03, 0.035, 0.05), (0.09, 0.05, 0.03), w), lerp3((0.10, 0.11, 0.14), (0.20, 0.11, 0.05), w), 1.3)
    te = climax_teff(t)
    col = lerp3((1, 1, 1), (1.0, 0.78, 0.42), w)
    EMBERS.draw(fr, te + 20, t + 20, col, 0.55, mode='normal' if w < 0.5 else 'add', twinkle=0.5 * w)
    for nm, cw, ch, (cx, cy), ang, dl in CONST:
        p = eout(prog(t, dl, dl + 0.8))
        if p <= 0: continue
        d = math.hypot(cx - 540, cy - 680) / 600
        wk = sm(prog(t, 2.4 + 1.2 * d, 3.6 + 1.2 * d))
        gr = lerp3(COLD[0], GOLDT[0], wk), lerp3(COLD[1], GOLDT[1], wk)
        cd = card('c_' + nm, nm, cw, ch, (0.5, 0.45), 1.0, ang, border=10)
        cd.draw(fr, cx + 4 * math.sin(t * 0.7 + cx), cy - (1 - p) * 50 + 4 * math.cos(t * 0.6 + cy), gr, alpha=p, dim=0.92)
    gr = lerp3(COLD[0], GOLDT[0], w), lerp3(COLD[1], GOLDT[1], w)
    hero(fr, 'coat', 600, 404, t, D, 1.0, 1.18, (0.5, 0.5), (0.5, 0.30), W / 2, 680, gr, border=14,
         alpha=eout(prog(t, 0.0, 0.7)), shadow=0.9)
    SNOW_NEAR.draw(fr, te + 20, t + 20, col, 0.7)
    # gentle darkening under the text
    yy = np.linspace(0, 1, H, dtype=F32)[:, None, None]
    fr *= 1 - 0.55 * np.clip((yy - 0.62) / 0.15, 0, 1)
    fr = screen(fr, leak(t, [(0.0, 1.0, 0.7, 0.45, (1.0, 0.55, 0.2), 0.55 * w), (1.0, 0.1, 0.5, 0.3, (1.0, 0.75, 0.4), 0.3 * w)]))
    T_CLIMAX0.draw(fr, t, 0.2, per=0.05, fade=0.9, alpha=0.75)
    T_CLIMAX.draw(fr, t, 1.3, per=0.2, fade=0.8)
    T_ATTR.draw(fr, t, 4.8, per=0.06, fade=0.7)
    return fr

# ---------- 12 outro
_OUT = {}
def sc_outro(t, D):
    fr = paper()
    if 'sk' not in _OUT:
        im = img_L('sketch')
        w = 540; h = int(round(im.size[1] * w / im.size[0]))
        L = np.asarray(im.resize((w, h), Image.LANCZOS), F32) / 255
        L = np.clip(L / np.percentile(L, 92), 0, 1)
        yy, xx = np.mgrid[0:h, 0:w].astype(F32)
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
        fade = np.clip((1.0 - r) / 0.22, 0, 1)
        _OUT['sk'] = (1 - (1 - L) * fade).astype(F32)
    sk = _OUT['sk']
    a = sm(prog(t, 0.0, 1.6))
    h, w = sk.shape
    x, y = (W - w) // 2, 380
    fr[y:y + h, x:x + w] *= (1 - a * (1 - sk))[..., None]
    T_OUTRO1.draw(fr, t, 1.2, per=0.16, fade=0.8)
    T_OUTRO2.draw(fr, t, 2.9, per=0.05, fade=0.8)
    fr *= (1 - sm(prog(t, D - 1.1, D)))
    return fr

# ------------------------------------------------------------------ text objects
T_INTRO2 = Text(TX['intro2'], 'serif_i', 38, 990, color=(0.80, 0.78, 0.74), maxw=900, shadow=0.5)
T_WINTER = Text(TX['winter'], 'serif_i', 78, 1130, maxw=880, shadow=0.8)
T_UNSEEN1 = Text(TX['unseen1'], 'serif_i', 84, 1330, maxw=950, shadow=0.8, glow=14)
T_UNSEEN2 = Text(TX['unseen2'], 'serif_i', 84, 1440, maxw=950, shadow=0.8, glow=14)
T_RED = Text(TX['red'], 'serif_i', 70, 200, maxw=900, shadow=0.75)
T_RED_ATTR = Text(TX['red_attr'], 'type', 30, 1100, color=(0.88, 0.82, 0.72), shadow=0.8)
T_SIS = Text(TX['sis'], 'serif_i', 68, 330, maxw=900, shadow=0.45)
T_ATTR_SIS = Text(TX['attr'], 'type', 30, 520, color=(0.85, 0.80, 0.72), shadow=0.4)
T_HAPPY = Text(TX['happy'], 'serif_i', 82, 1290, maxw=860, shadow=0.75, hl=('happy.', 'feliz.'))
T_AUTUMN = Text(TX['autumn'], 'serif_i', 74, 1320, maxw=900, shadow=0.8, hl=('flower.', 'flor.'), hl_color=(1.0, 0.78, 0.50))
T_COFFEE = Text(TX['coffee'], 'serif_i', 64, 410, maxw=920, shadow=0.7)
T_SECRET1 = Text(TX['secret1'], 'serif_i', 60, 1000, color=INK, maxw=920, shadow=0.0, hl=('secret', 'colours,', 'colores', 'secretos,'), hl_color=(0.55, 0.22, 0.25))
T_SECRET2 = Text(TX['secret2'], 'serif_i', 66, 1000, color=INK, maxw=900, shadow=0.0, hl=('secret', 'colours.', 'colores', 'secretos.'), hl_color=(0.55, 0.22, 0.25))
T_CLIMAX0 = Text(TX['climax0'], 'serif_i', 50, 1300, color=(0.86, 0.88, 0.92), maxw=900, shadow=0.7)
T_CLIMAX = Text(TX['climax'], 'serif_i', 70, 1450, maxw=900, shadow=0.75, hl=TX['climax_hl'], hl_color=GOLD)
T_ATTR = Text(TX['attr'], 'type', 30, 1620, color=(0.92, 0.86, 0.76), shadow=0.6)
T_OUTRO1 = Text(TX['outro1'], 'serif_i', 80, 1110, color=INK, maxw=900, shadow=0.0)
T_OUTRO2 = Text(TX['outro2'], 'type', 26, 1230, color=(0.35, 0.28, 0.22), maxw=1000, shadow=0.0)

# ------------------------------------------------------------------ timeline
TL = [
    (sc_intro, 0.0, 4.8, None, 0),
    (sc_winter, 4.0, 10.4, 'black', 0.9),
    (sc_unseen, 9.6, 16.4, 'blur', 0.8),
    (sc_red, 15.7, 22.0, 'chevron', 0.7),
    (sc_sis, 21.2, 28.0, 'black', 0.8),
    (sc_happy, 27.2, 31.8, 'burn', 0.8),
    (sc_autumn, 31.0, 37.8, 'fade', 0.8),
    (sc_coffee, 37.0, 43.8, 'blur', 0.8),
    (sc_secret, 43.0, 50.6, 'burn', 0.8),
    (sc_film, 50.1, 53.0, 'fade', 0.5),
    (sc_climax, 52.6, 60.8, 'flash', 0.4),
    (sc_outro, 59.6, 66.0, 'fade', 1.2),
]
DUR = 66.0
NFRAMES = int(DUR * FPS)

def blur_frame(fr, r):
    im = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, F32) / 255

def transition(kind, a, b, p, t):
    if kind == 'fade':
        e = sm(p); return a * (1 - e) + b * e
    if kind == 'black':
        return a * (1 - sm(p * 2)) if p < 0.5 else b * sm(p * 2 - 1)
    if kind == 'blur':
        r = 22 * math.sin(math.pi * p); e = sm(p)
        m = a * (1 - e) + b * e
        return blur_frame(m, r) if r > 0.6 else m
    if kind == 'burn':
        e = sm(p); m = a * (1 - e) + b * e
        k = math.sin(math.pi * p)
        lk = leak(t, [(lerp(-0.2, 1.2, p), 0.5, 0.45, 0.8, (1.0, 0.58, 0.26), 0.7 * k), (0.5, 0.5, 0.9, 0.9, (1.0, 0.82, 0.6), 0.18 * k * k)])
        return screen(m, lk)
    if kind == 'flash':
        e = sm(p); m = a * (1 - e) + b * e
        k = math.sin(math.pi * p) ** 1.5
        return m * (1 - k) + np.asarray((1.0, 0.97, 0.92), F32) * k
    if kind == 'chevron':
        e = eio(p)
        xx = np.arange(W, dtype=F32)
        tri = np.abs(((xx / 135.0) % 1.0) - 0.5) * 2 * 90
        edge = -120 + e * (H + 240) + tri
        yy = np.arange(H, dtype=F32)[:, None]
        m = np.clip((edge[None, :] - yy) / 3.0, 0, 1)
        border = np.clip(1 - np.abs(edge[None, :] - yy - 10) / 8.0, 0, 1) * 0.9
        out = a * (1 - m[..., None]) + b * m[..., None]
        return out * (1 - border[..., None]) + np.asarray((0.86, 0.82, 0.74), F32) * border[..., None]
    return b

def render_frame(fi):
    t = fi / FPS
    act = [(fn, s, e, tr, td) for fn, s, e, tr, td in TL if s <= t < e]
    if not act:
        fr = np.zeros((H, W, 3), F32)
    elif len(act) == 1:
        fn, s, e, tr, td = act[0]
        fr = fn(t - s, e - s)
    else:
        (fa, sa, ea, _, _), (fb, sb, eb, tr, td) = act[0], act[1]
        fr = transition(tr, fa(t - sa, ea - sa), fb(t - sb, eb - sb), (t - sb) / td, t)
    cur = act[-1][0] if act else None
    paperish = cur in (sc_secret, sc_outro)
    return post(fr, fi, t, grain=0.040 if paperish else 0.048, vig=0.55 if paperish else 1.0, bl=0.12 if paperish else 0.2)

def to_u8(fr):
    return (np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'preview':
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        for ts in sys.argv[3:]:
            fi = int(round(float(ts) * FPS))
            Image.fromarray(to_u8(render_frame(fi))).save(f'{out}/f_{float(ts):06.2f}.png')
            print('ok', ts, flush=True)
    elif cmd == 'render':
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                              '-x264-params', 'keyint=60:min-keyint=30', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out],
                             stdin=subprocess.PIPE)
        import time; t0 = time.time()
        for fi in range(a, b):
            p.stdin.write(to_u8(render_frame(fi)).tobytes())
            if (fi - a) % 30 == 0:
                print(f'{out}: {fi}/{b} {time.time() - t0:.0f}s', flush=True)
        p.stdin.close(); p.wait()
        print('done', out, 'maxscale', {k: round(v, 3) for k, v in MAXS.items()}, flush=True)
