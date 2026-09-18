#!/usr/bin/env python3
"""s020 の動画を組み立てる。

  python3 build.py            # 出力: s020.mp4（1080x1920 / 30fps / 音声なし）

③（草ごと金属を飲み込む）だけは静止画のままだと12.5秒が持たないため、
1枚の図を「口元 → 食道の釘 → 胸」へ寄り移動させる。
図そのものが経路を描いているので、カメラの移動がそのまま説明になる。
"""
import subprocess, pathlib, imageio_ffmpeg
from PIL import Image

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# (画像, 秒数, 動かすか)
CUTS = [("f1.jpg", 2.88, False),   # 牛
        ("f2.jpg", 3.84, False),   # 牛用磁石
        ("f3.jpg", 12.48, True),   # 飲み込み ← ここだけ動かす
        ("f4.jpg", 6.72, False),   # 第二胃の磁石
        ("f5.jpg", 2.88, False)]   # 牛の顔アップ

# ③の寄り移動：ズームは固定し、移動だけで見せる。
# 元画像が9:16なので横に振れる余地が少なく、ズームを変えると「引き」に見えてしまう。
PAN = dict(zoom=1.45, start=(0.00, 0.83), end=(1.00, 0.17))   # (x, y) は振れ幅に対する割合

def render_pan(src, dur, outdir):
    im = Image.open(HERE/src).convert("RGB"); W, H = im.size
    cw = W/PAN["zoom"]; ch = cw*OH/OW
    tx, ty = W-cw, H-ch
    n = round(FPS*dur)
    outdir.mkdir(exist_ok=True)
    for f in outdir.glob("*.jpg"): f.unlink()
    for i in range(n):
        t = (lambda u: u*u*(3-2*u))(i/(n-1))          # 出入りをなめらかに
        x = (PAN["start"][0] + (PAN["end"][0]-PAN["start"][0])*t) * tx
        y = (PAN["start"][1] + (PAN["end"][1]-PAN["start"][1])*t) * ty
        im.crop((round(x), round(y), round(x+cw), round(y+ch))) \
          .resize((OW, OH), Image.LANCZOS).save(outdir/f"f{i:04d}.jpg", quality=92)
    return n

def main():
    segs = []
    for i, (img, dur, moving) in enumerate(CUTS, 1):
        seg = HERE/f"_seg{i}.mp4"
        if moving:
            d = HERE/"_pan"; render_pan(img, dur, d)
            cmd = [FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(d/"f%04d.jpg")]
        else:
            cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", str(HERE/img)]
        subprocess.run(cmd + ENC + [str(seg)], check=True)
        segs.append(seg)
    lst = HERE/"_segs.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(HERE/"s020.mp4")], check=True)
    print("s020.mp4")

if __name__ == "__main__":
    main()
