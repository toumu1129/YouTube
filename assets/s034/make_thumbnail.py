#!/usr/bin/env python3
"""s034 のサムネイル用カード（thumb.jpg）を作る。

  python3 make_thumbnail.py

YouTube Shortsはサムネイル画像を別添付できず、動画の先頭フレームが
そのままサムネイルになる。そこで実写素材（f1.jpgの元になった写真）に
目を引く文字を合成したカードを作り、build.pyが動画の先頭に
THUMBNAIL_DUR秒だけ挿入する。

素材: https://www.pexels.com/photo/mesmerizing-close-up-of-a-cuttlefish-underwater-32841309/
（Esteban Carriazo、商用可・クレジット表記不要）の元画像（f1.jpgと同じ写真、
f1.jpgより上に余白を残した別クロップ）を使用。
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
SRC_URL = "https://images.pexels.com/photos/32841309/pexels-photo-32841309.jpeg?auto=compress&cs=tinysrgb&w=3840"
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
W, H = 1080, 1920
LINES = ["好物のために", "我慢する、、、"]


def cover_crop(im, ow, oh, x_anchor=0.5, y_anchor=0.5):
    w, h = im.size
    scale = max(ow / w, oh / h)
    nw, nh = round(w * scale), round(h * scale)
    im2 = im.resize((nw, nh), Image.LANCZOS)
    x = round((nw - ow) * x_anchor)
    y = round((nh - oh) * y_anchor)
    return im2.crop((x, y, x + ow, y + oh))


def fade_overlay(w, fade_h, alpha_top=150, gamma=1.5):
    """上端が最も暗く、fade_hにかけて滑らかに透明になる黒グラデーション。"""
    col = Image.new("L", (1, fade_h))
    for y in range(fade_h):
        a = int(alpha_top * (1 - y / fade_h) ** gamma)
        col.putpixel((0, y), a)
    alpha = col.resize((w, fade_h))
    black = Image.new("RGBA", (w, fade_h), (0, 0, 0, 255))
    black.putalpha(alpha)
    return black


def main():
    import urllib.request
    src_path = HERE / "_thumb_src.jpg"
    if not src_path.exists():
        urllib.request.urlretrieve(SRC_URL, src_path)

    im = Image.open(src_path).convert("RGB")
    im = cover_crop(im, W, H, x_anchor=0.42, y_anchor=0.48)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay.paste(fade_overlay(W, 750), (0, 0))
    im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT_PATH, 116)
    y = 90
    for line in LINES:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=12)
        x = (W - (bbox[2] - bbox[0])) / 2 - bbox[0]
        draw.text((x, y), line, font=font, fill=(255, 214, 0),
                   stroke_width=12, stroke_fill=(0, 0, 0))
        y += 190

    im.save(HERE / "thumb.jpg", quality=95)
    src_path.unlink()
    print("thumb.jpg")


if __name__ == "__main__":
    main()
