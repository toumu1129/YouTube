#!/usr/bin/env python3
"""③「保護施設のネコを2組に分けた実験」の比較図解を作る（f3-diagram.jpg）。

AI画像生成は文字・図表の描画精度が低く使えないため（s004で実写に切り替えた
経緯と同じ理由）、PILで直接描く。1080x1920、動画本体に静止画として使う。

内容：箱あり／箱なしの2群が、それぞれ何日でストレス値が安定したかを
1本のタイムライン上の点で示し、その差（7日）を矢印とラベルで示す。
出典の数字（Vinke et al. 2014）以外の値は作図の都合の概算。
"""
import pathlib
from PIL import Image, ImageDraw, ImageFont

OW, OH = 1080, 1920
BG = (30, 28, 26)          # 落ち着いた暖かいダークグレー（猫写真の暖色と合わせる）
INK = (245, 242, 236)      # 白系の文字
MUTED = (150, 145, 138)    # 補助線・補助文字
ACCENT = (255, 209, 60)    # 強調語と同じアクセント黄（docs/03-shorts-format.md準拠）
LINE_W = 6

FONT_DIR = pathlib.Path("/usr/share/fonts/opentype/ipafont-gothic")
def font(size):
    return ImageFont.truetype(str(FONT_DIR / "ipag.ttf"), size)

def center_text(d, xy, text, f, fill, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor)

def timeline_row(d, y, label, day_stable, max_day, color, f_label, f_num):
    x0, x1 = 140, OW - 140
    # ラベル
    center_text(d, (x0, y - 90), label, f_label, INK, anchor="lm")
    # ベースライン
    d.line([(x0, y), (x1, y)], fill=MUTED, width=LINE_W)
    d.ellipse([x0 - 10, y - 10, x0 + 10, y + 10], fill=MUTED)
    # 安定した点
    x_stable = x0 + (x1 - x0) * (day_stable / max_day)
    d.line([(x0, y), (x_stable, y)], fill=color, width=LINE_W)
    d.ellipse([x_stable - 20, y - 20, x_stable + 20, y + 20], fill=color)
    center_text(d, (x_stable, y - 55), "安定", f_num, color, anchor="mm")
    return x_stable

def main():
    im = Image.new("RGB", (OW, OH), BG)
    d = ImageDraw.Draw(im)

    f_label = font(56)
    f_num = font(40)
    f_gap = font(64)
    f_gap_small = font(36)

    max_day = 14
    y1, y2 = 760, 1020

    x_hako_ari = timeline_row(d, y1, "箱あり", 5, max_day, ACCENT, f_label, f_num)
    x_hako_nashi = timeline_row(d, y2, "箱なし", 12, max_day, (210, 120, 90), f_label, f_num)

    # 差を示す縦の補助線＋「7日」ラベル
    top_y, bot_y = y1 - 130, y2 + 90
    mid_x = (x_hako_ari + x_hako_nashi) / 2
    d.line([(x_hako_ari, top_y), (x_hako_ari, bot_y)], fill=MUTED, width=3)
    d.line([(x_hako_nashi, top_y), (x_hako_nashi, bot_y)], fill=MUTED, width=3)
    d.line([(x_hako_ari, bot_y - 10), (x_hako_nashi, bot_y - 10)], fill=ACCENT, width=5)
    center_text(d, (mid_x, bot_y + 60), "7日早い", f_gap, ACCENT, anchor="mm")

    out = pathlib.Path(__file__).parent / "f3-diagram.jpg"
    im.save(out, quality=93)
    print(out)

if __name__ == "__main__":
    main()
