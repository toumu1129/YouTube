#!/usr/bin/env python3
"""s004 の動画を組み立てる。

  python3 build.py            # 出力: s004.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s004-narration.srt`（tools/make_srt.py が音声の無音を実測して作ったもの）から逆算する。
理由は s020/build.py の冒頭コメント、および assets/s020/README.md を参照。
"""
import re, subprocess, pathlib, imageio_ffmpeg

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの画像が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
# 台本の5ブロックと、s004-narration.txt の文で対応づけて決めた。
IMAGE_CARDS = [
    ("f1.jpg", 1,  1,  False),  # ①セミは1週間では死にません。
    ("f2.jpg", 2,  3,  False),  # ②地上に出たら1週間の命。そう習った人が多いはずです。（死んだセミ）
    ("f3.jpg", 4,  9,  False),  # ③この数字、実は…結果は、1週間どころでは…（別のアブラゼミ）
    ("f4.jpg", 10, 11, False),  # ④記録された最長は、アブラゼミで32日。（アブラゼミ）
    ("f5.jpg", 12, 14, False),  # ⑤ツクツクボウシで26日。…誰も数えていなかった数字だったんです。（ツクツクボウシ）
    ("f6.jpg", 15, 16, False),  # ⑥あなたの周りの常識も、実は間違っているかもしれません。（木漏れ日）
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

CUTS, _BOUNDS = cuts_from_srt(HERE / "s004-narration.srt")

def main():
    print("カット秒数（s004-narration.srt から実測で算出）")
    for img, dur, moving in CUTS:
        print(f"  {img:10}{dur:6.2f}s" + ("  ← 寄り移動" if moving else ""))
    print(f"  合計 {sum(d for _, d, _ in CUTS):.2f}s\n")

    segs = []
    for i, (img, dur, moving) in enumerate(CUTS, 1):
        seg = HERE/f"_seg{i}.mp4"
        cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", str(HERE/img)]
        subprocess.run(cmd + ENC + [str(seg)], check=True)
        segs.append(seg)
    lst = HERE/"_segs.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(HERE/"s004.mp4")], check=True)
    print("s004.mp4")

if __name__ == "__main__":
    main()
