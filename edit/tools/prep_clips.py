"""Extrae los clips de los vídeos del repo (recortados sin subtítulos ni logos, resolución nativa) -> tools/clips/*.npy"""
import os, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, 'clips'); os.makedirs(OUT, exist_ok=True)
V1 = 'WhatsApp Video 2026-11-22 at 12.19.17 (1).mp4'; V2 = 'WhatsApp Video 2026-11-22 at 12.19.17 (2).mp4'; V3 = 'WhatsApp Video 2026-11-22 at 12.19.17.mp4'
CLIPS = {  # nombre: (vídeo, inicio, duración, x, y, w, h, recortar_cortes)
    'interview': (V1, 16.5, 7.4, 300, 40, 500, 460, True),
    'chess': (V1, 5.47, 0.46, 170, 75, 560, 430, True),
    'coffee': (V3, 11.5, 0.93, 0, 232, 576, 540, True),
    'wolf': (V3, 12.5, 1.4, 0, 232, 576, 540, True),
    'talk': (V3, 7.0, 1.4, 0, 232, 576, 540, True),
    'nobel_close': (V2, 22.5, 2.5, 5, 217, 350, 176, True),
    'nobel_cer': (V2, 12.0, 2.5, 5, 217, 350, 172, False),
    'nobel_tails': (V2, 15.0, 3.0, 5, 217, 350, 172, True),
    'nobel_woman': (V2, 25.0, 4.5, 5, 217, 350, 176, True),
}
for n, (f, st, du, x, y, w, h, trim) in CLIPS.items():
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(st), '-t', str(du), '-i', os.path.join(REPO, f),
                          '-vf', f'fps=30,crop={w}:{h}:{x}:{y},format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w)
    if trim:  # keep the longest shot (drops frames from neighbouring scenes)
        d = np.abs(np.diff(a.astype(np.float32), axis=0)).mean(axis=(1, 2))
        b = [0] + [i + 1 for i, v in enumerate(d) if v > 18] + [len(a)]
        s0, s1 = max(zip(b[:-1], b[1:]), key=lambda s: s[1] - s[0]); a = a[s0:s1]
    np.save(os.path.join(OUT, n + '.npy'), a); print(n, a.shape)
