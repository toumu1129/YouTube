#!/usr/bin/env python3
"""s020 の動画を組み立てる。

  python3 build.py            # 出力: s020.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s020.srt`（tools/make_srt.py が音声の無音を実測して作ったもの）から逆算する。

過去に一度、ここを「台本の秒数見積もり（0:00-0:03 / 0:03-0:07 / ...）を
そのまま比例配分」で決め打ちしていたことがあり、字幕だけ実測に直した結果、
**映像の切り替えと音声・字幕がずれる事故**が起きた（③→④の境界が3.76秒ずれた）。
字幕と映像の「尺の出どころ」を分けると、どちらか一方だけ直したときに必ずまた起きる。
だから両方を同じ SRT から生成する。

③（草ごと金属を飲み込む）だけは静止画のままだと尺が持たないため、
1枚の図を「口元 → 食道の釘 → 胸」へ寄り移動させる。
図そのものが経路を描いているので、カメラの移動がそのまま説明になる。
"""
import re, subprocess, pathlib, imageio_ffmpeg
from PIL import Image

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの画像が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
# 台本の5ブロックと、s020-narration.txt の文で対応づけて決めた。
IMAGE_CARDS = [
    ("f1.jpg", 1, 1,   False),  # ①牛は、磁石を飲みます。
    ("f2.jpg", 2, 3,   False),  # ②冗談ではありません。専用の磁石が売られています。
    ("f3.jpg", 4, 6,   True),   # ③牛は草を…そのまま胃に入ります。← ここだけ動かす
    ("f4.jpg", 7, 10,  False),  # ④金属は胃の壁を…集めておくんです。
    ("f5.jpg", 11, 12, False),  # ⑤一度飲んだら、一生入ったまま。
]

def srt_cards(path):
    """SRT を [(開始秒, 終了秒), ...] のリストにする（1始まりの番号に対応）。"""
    blocks = pathlib.Path(path).read_text(encoding="utf-8").strip().split("\n\n")
    def ts(s):
        hms, ms = s.split(",")
        h, m, sec = hms.split(":")
        return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000
    cards = []
    for b in blocks:
        m = re.search(r"(\d\d:\d\d:[\d,]+) --> (\d\d:\d\d:[\d,]+)", b)
        cards.append((ts(m[1]), ts(m[2])))
    return cards

def cuts_from_srt(srt_path):
    """IMAGE_CARDS と実測タイムラインから、各カットの (画像, 秒数, 動かすか) を出す。

    カット境界は「前ブロック最後のカードの終了」と「次ブロック先頭カードの開始」の
    中間点。最初は0秒から、最後はSRT全体の終了秒まで。
    """
    cards = srt_cards(srt_path)
    bounds = [0.0]
    for i in range(len(IMAGE_CARDS) - 1):
        _, _, end_i, _   = IMAGE_CARDS[i]
        _, start_j, _, _ = IMAGE_CARDS[i + 1]
        prev_end   = cards[end_i - 1][1]
        next_start = cards[start_j - 1][0]
        bounds.append(round((prev_end + next_start) / 2, 3))
    bounds.append(round(cards[-1][1], 3))

    cuts = []
    for i, (img, _, _, moving) in enumerate(IMAGE_CARDS):
        dur = round(bounds[i + 1] - bounds[i], 3)
        cuts.append((img, dur, moving))
    return cuts, bounds

CUTS, _BOUNDS = cuts_from_srt(HERE / "s020.srt")

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
    print("カット秒数（s020.srt から実測で算出）")
    for img, dur, moving in CUTS:
        print(f"  {img:10}{dur:6.2f}s" + ("  ← 寄り移動" if moving else ""))
    print(f"  合計 {sum(d for _, d, _ in CUTS):.2f}s\n")

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
