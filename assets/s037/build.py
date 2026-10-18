#!/usr/bin/env python3
"""s037 の動画を組み立てる。

  python3 build.py            # 出力: s037.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s037-narration.srt`（tools/make_srt.py が音声の無音を実測して作ったもの。
発話区間13=文節13で一致、手直し不要）から逆算する。
理由は s020/build.py の冒頭コメント、および assets/s020/README.md を参照。

s037は静止画4枚（f1/f2/f3/f4.jpg）＋動画1本（f5.mp4）の構成。
- f1.jpg（テッポウウオのアップ）、f5.mp4（泳ぐテッポウウオ）はPexels実写。
- f2.jpg（画面の顔写真に水を吐く様子）、f3.jpg（並んだ顔写真）は生成AI。
- f4.jpg（白黒ポートレート）はPexels実写だが、ナレーションが指す
  「条件をそろえた顔写真」そのものではない代用（ユーザー了承済み、
  詳細は scripts/shorts/s037-teppouuo-kao.md の素材表を参照）。
"""
import re, subprocess, pathlib, imageio_ffmpeg

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの素材が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
IMAGE_CARDS = [
    ("f1.jpg", 1, 2,   "image"),  # ①テッポウウオは、人間の顔を見分けることができます。
    ("f2.jpg", 3, 5,   "image"),  # ②研究チームが、テッポウウオに水を吐かせて…実験を行いました。
    ("f3.jpg", 6, 7,   "image"),  # ③初めて見る顔を18人分混ぜても…見分け続けました。
    ("f4.jpg", 8, 10,  "image"),  # ④髪型や肌の色、画像の明るさを…見分けられたのです。
    ("f5.mp4", 11, 13, "video"),  # ⑤テッポウウオは、大きな脳を持たなくても…生き物でした。
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
    """IMAGE_CARDS と実測タイムラインから、各カットの (素材, 秒数, 種類) を出す。

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
    for i, (src, _, _, kind) in enumerate(IMAGE_CARDS):
        dur = round(bounds[i + 1] - bounds[i], 3)
        cuts.append((src, dur, kind))
    return cuts, bounds

CUTS, _BOUNDS = cuts_from_srt(HERE / "s037-narration.srt")

def render_cut(src, dur, kind, out_path):
    if kind == "video":
        cmd = [FF, "-y", "-loglevel", "error", "-i", str(HERE / src),
               "-vf", f"scale={OW}:{OH}:flags=lanczos", "-t", str(dur)]
    else:
        cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", str(HERE / src)]
    subprocess.run(cmd + ENC + [str(out_path)], check=True)

def main():
    print("カット秒数（s037-narration.srt から実測で算出）")
    for src, dur, kind in CUTS:
        print(f"  {src:10}{dur:6.2f}s  ({kind})")
    print(f"  合計 {sum(d for _, d, _ in CUTS):.2f}s\n")

    segs = []
    for i, (src, dur, kind) in enumerate(CUTS, 1):
        seg = HERE / f"_seg{i}.mp4"
        render_cut(src, dur, kind, seg)
        segs.append(seg)

    lst = HERE / "_segs.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(HERE / "s037.mp4")], check=True)
    print("s037.mp4")

if __name__ == "__main__":
    main()
