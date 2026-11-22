"""Recorta las fotos del repo (quitando marcas de agua) a resolución nativa -> tools/src/*.png"""
import os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, 'src'); os.makedirs(OUT, exist_ok=True)
def crop(f, box, out):
    im = Image.open(os.path.join(REPO, f)).convert('RGB')
    if box:
        if all(isinstance(v, float) for v in box):
            w, h = im.size; box = (int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h))
        im = im.crop(box)
    im.save(os.path.join(OUT, out + '.png'))
crop('#AlbertCamus.jpeg', None, 'bed')
crop('#albertcamus  #paris.jpeg', None, 'paris')
crop('Albert Camus (1).jpeg', None, 'smile')
crop('Camus Beyond the Familiar Quote_ Guilt and The Fall.jpeg', (150, 420, 700, 985), 'sketch')
crop('WhatsApp Image 2026-11-22 at 12.19.16.jpeg', (215, 382, 1205, 1036), 'cafe')
crop('WhatsApp Image 2026-11-22 at 12.19.18 (1).jpeg', (0., 0., 1., 0.90), 'cig')
crop('WhatsApp Image 2026-11-22 at 12.19.18 (2).jpeg', (0., 0., 1., 0.90), 'enavant')
crop('WhatsApp Image 2026-11-22 at 12.19.18 (3).jpeg', (0., 0., 1., 0.90), 'lighting')
crop('WhatsApp Image 2026-11-22 at 13.35.56 (1).jpeg', (0, 0, 1320, 735), 'facepalm')
crop('albert camus.jpeg', None, 'coat')
crop('camus.jpeg', None, 'cat')
crop('descarga (6).jpeg', None, 'tree')
crop('descarga (7).jpeg', None, 'gesture')
crop('WhatsApp Image 2026-11-22 at 13.35.56 (3).jpeg', (0, 0, 1320, 500), 'couch')
print('ok ->', OUT)
