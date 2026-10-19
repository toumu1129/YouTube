#!/usr/bin/env python3
"""動画の最後に、チャンネル紹介の一言を2.5秒だけ追加する。

  python3 tools/add_outro.py assets/sXXX/sXXX-final.mp4

本編の最後のフレームを静止画として伸ばし、そこに「最新の研究に基づく
生き物雑学」「毎日19時投稿」の2行を、虫眼鏡・時計のアイコン付きで
フェードイン表示してから、本編の末尾に結合する。音声はこの2.5秒だけ
無音を足す（ナレーションを継ぎ足すわけではない）。

【重要】最後のフレームは sXXX-final.mp4（テロップ焼き込み済み）からでは
なく、同じフォルダの sXXX-with-audio.mp4（テロップ焼き込み前）から取る。
sXXX-final.mp4からそのまま取ると、本編最後のテロップ文字が凍結されて
新しい一言と重なってしまうため。

出力は <入力>（拡張子の前に何も付けず）を上書きする。元のファイルを
残したい場合は、先にコピーしておくこと。

アイコンはPILで描画する白塗り・黒フチのベクター調の絵（本編テロップと
同じ配色）。OpenAIの画像生成や絵文字フォントには頼らない
（libassがカラー絵文字を正しく描画できないため）。
"""
import math
import pathlib
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT_PATH = HERE.parent / "assets" / "fonts" / "BIZUDGothic-Bold.ttf"

OW, OH = 1080, 1920
OUTRO_DURATION = 2.5   # 秒
FADE_IN = 0.4          # 秒
POS_Y = 1460           # 本編テロップと同じ縦位置（中心）
FONT_SIZE = 66
ICON_SIZE = 72
GAP = 24               # アイコンと文字の間隔(px)
LINE_GAP = 20          # 行間(px)
OUTLINE_W = 7
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
SS = 4                 # アイコンのスーパーサンプリング倍率

OUTRO_LINES = [
    ("magnifier", "最新の研究に基づく生き物雑学"),
    ("clock", "毎日19時投稿"),
]


def draw_icon(name, size):
    s = size * SS
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = int(OUTLINE_W * SS * 0.9)
    if name == "magnifier":
        r = int(s * 0.33)
        cx, cy = int(s * 0.42), int(s * 0.42)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=BLACK, width=lw)
        inner = int(r * 0.62)
        d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner],
                   fill=(0, 0, 0, 0), outline=BLACK, width=int(lw * 0.5))
        handle_w = int(s * 0.17)
        x0, y0 = cx + int(r * 0.72), cy + int(r * 0.72)
        x1, y1 = int(s * 0.92), int(s * 0.92)
        d.line([x0, y0, x1, y1], fill=BLACK, width=handle_w + lw, joint="curve")
        d.line([x0, y0, x1, y1], fill=WHITE, width=handle_w, joint="curve")
        he = handle_w // 2
        d.ellipse([x1 - he - lw // 2, y1 - he - lw // 2, x1 + he + lw // 2, y1 + he + lw // 2], fill=BLACK)
        d.ellipse([x1 - he, y1 - he, x1 + he, y1 + he], fill=WHITE)
    elif name == "clock":
        r = int(s * 0.42)
        cx, cy = s // 2, s // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=BLACK, width=lw)
        hand_w = int(s * 0.07)
        for ang_deg, length_ratio in [(-90, 0.5), (30, 0.3)]:
            ang = math.radians(ang_deg)
            ex = cx + length_ratio * r * math.cos(ang)
            ey = cy + length_ratio * r * math.sin(ang)
            d.line([cx, cy, ex, ey], fill=BLACK, width=hand_w + int(lw * 0.6), joint="curve")
        cr = int(s * 0.045)
        d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=BLACK)
    else:
        raise ValueError(f"unknown icon: {name}")
    return im.resize((size, size), Image.LANCZOS)


def build_overlay_png(out_path):
    font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)

    rows = []
    max_row_w = 0
    for icon_name, text in OUTRO_LINES:
        bbox = d.textbbox((0, 0), text, font=font, stroke_width=OUTLINE_W)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        row_w = ICON_SIZE + GAP + tw
        row_h = max(ICON_SIZE, th)
        rows.append((icon_name, text, tw, th, bbox, row_w, row_h))
        max_row_w = max(max_row_w, row_w)

    total_h = sum(r[6] for r in rows) + LINE_GAP * (len(rows) - 1)
    canvas = Image.new("RGBA", (OW, total_h + 20), (0, 0, 0, 0))
    cd = ImageDraw.Draw(canvas)

    y = 10
    for icon_name, text, tw, th, bbox, row_w, row_h in rows:
        x0 = (OW - row_w) // 2
        icon_im = draw_icon(icon_name, ICON_SIZE)
        canvas.paste(icon_im, (x0, y + (row_h - ICON_SIZE) // 2), icon_im)
        text_x = x0 + ICON_SIZE + GAP
        text_y = y + (row_h - th) // 2 - bbox[1]
        cd.text((text_x, text_y), text, font=font, fill=WHITE, stroke_width=OUTLINE_W, stroke_fill=BLACK)
        y += row_h + LINE_GAP

    canvas.save(out_path)
    return canvas.size


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    video_path = pathlib.Path(sys.argv[1])
    work = video_path.parent
    with_audio_path = video_path.with_name(video_path.name.replace("-final.mp4", "-with-audio.mp4"))
    if not with_audio_path.exists() or with_audio_path == video_path:
        raise FileNotFoundError(
            f"テロップ焼き込み前のファイルが見つかりません: {with_audio_path}\n"
            "（sXXX-final.mp4 からそのまま最後のフレームを取ると、テロップ文字が"
            "凍結されて新しい一言と重なってしまうため、sXXX-with-audio.mp4 が必要です）"
        )
    last_frame = work / "_outro_lastframe.jpg"
    overlay_png = work / "_outro_overlay.png"
    outro_seg = work / "_outro_seg.mp4"
    out_with_outro = work / "_outro_final.mp4"

    print("① 最後のフレームを取得（テロップ焼き込み前のファイルから）")
    run([FF, "-y", "-loglevel", "error", "-sseof", "-1.0", "-i", str(with_audio_path),
         "-frames:v", "1", str(last_frame)])

    print("② アイコン付きの一言を描画")
    size = build_overlay_png(overlay_png)
    overlay_y = POS_Y - size[1] // 2
    print(f"  {overlay_png}  {size}")

    print("③ 末尾用の静止画クリップ(音声は無音)を作成し、フェードインを焼き込み")
    run([FF, "-y", "-loglevel", "error",
         "-loop", "1", "-t", str(OUTRO_DURATION), "-i", str(last_frame),
         "-f", "lavfi", "-t", str(OUTRO_DURATION), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
         "-loop", "1", "-t", str(OUTRO_DURATION), "-r", "30", "-i", str(overlay_png),
         "-filter_complex",
         f"[0:v]scale={OW}:{OH}[bg];"
         f"[2:v]format=rgba,fade=t=in:st=0:d={FADE_IN}:alpha=1[ov];"
         f"[bg][ov]overlay=x=0:y={overlay_y}[v]",
         "-map", "[v]", "-map", "1:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest",
         str(outro_seg)])

    print("④ 本編の末尾に結合")
    run([FF, "-y", "-loglevel", "error",
         "-i", str(video_path), "-i", str(outro_seg),
         "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]",
         "-map", "[outv]", "-map", "[outa]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k",
         str(out_with_outro)])

    out_with_outro.replace(video_path)
    for p in (last_frame, overlay_png, outro_seg):
        p.unlink(missing_ok=True)
    print(f"\n完成: {video_path}（末尾に{OUTRO_DURATION}秒のチャンネル紹介を追加）")


if __name__ == "__main__":
    main()
