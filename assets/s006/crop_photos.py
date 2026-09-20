#!/usr/bin/env python3
"""静止画3枚を1080x1920に中央基準でクロップ（gen_diagrams.pyのcover_cropと同じ考え方）。"""
import pathlib
from PIL import Image

OW, OH = 1080, 1920
HERE = pathlib.Path(__file__).parent

# (ファイル名, 水平方向のアンカー 0.0=左端基準 0.5=中央 1.0=右端基準)
JOBS = [
    ("f1-settled.jpg", 0.5),
    ("f4-peer.jpg", 0.5),
    ("f5-refuge.jpg", 0.5),
]

def cover_crop(im, ow, oh, x_anchor=0.5, y_anchor=0.5):
    im = im.convert("RGB")
    s = max(ow / im.width, oh / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l = round((im.width - ow) * x_anchor)
    t = round((im.height - oh) * y_anchor)
    return im.crop((l, t, l + ow, t + oh))

for name, x_anchor in JOBS:
    src = HERE / name
    im = cover_crop(Image.open(src), OW, OH, x_anchor=x_anchor)
    out = HERE / name.replace(".jpg", "-cropped.jpg")
    im.save(out, quality=93)
    print(out)
