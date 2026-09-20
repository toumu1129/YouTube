#!/usr/bin/env python3
"""s009 の動画を組み立てる。

  python3 build.py            # 出力: s009.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s009-narration.srt`（tools/make_srt.py が音声の無音を実測して作ったもの）から逆算する。
理由は s020/build.py の冒頭コメント、および assets/s020/README.md を参照。

s009は静止画4枚（f1〜f4.jpg）＋動画1本（f5-river.mp4、川面）の構成。
- ①②のサケ、③の3段階図解、④の実験図解は、はっきり写った実写素材が
  無料素材サイト（Pexels/Pixabay）で見つからなかった（濁った滝の遠景に
  小さく写る程度）。実物が確認できない/著しく不鮮明な素材を使うより、
  内容が正確に伝わるAI生成イラストを使う方針とし、`gen_diagrams.py`で
  生成した（プロンプトは prompts.json 参照）。1080x1920で生成済みなので
  追加のクロップ・スケールはしない。
- ⑤川面はサケが写る必要がないので実写（Pexels）を使用。必要な秒数だけ
  先頭から使う。
"""
import re, subprocess, pathlib, imageio_ffmpeg

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの素材が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
IMAGE_CARDS = [
    ("f1.jpg",       1,  2,  "image"),  # ①サケは、生まれた川に戻ってきます。
    ("f2.jpg",       3,  4,  "image"),  # ②何千キロも離れた海から、なぜ間違えないのでしょう。
    ("f3.jpg",       5,  10, "image"),  # ③覚えているのは…河口から上流へとたどっていきます。
    ("f4.jpg",       11, 14, "image"),  # ④鼻をふさいだサケは…確かめられました。
    ("f5-river.mp4", 15, 18, "video"),  # ⑤匂いの記憶を手がかりに…生まれ故郷に帰りましたか？
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

CUTS, _BOUNDS = cuts_from_srt(HERE / "s009-narration.srt")

def render_cut(src, dur, kind, out_path):
    if kind == "video":
        cmd = [FF, "-y", "-loglevel", "error", "-i", str(HERE / src),
               "-vf", f"scale={OW}:{OH}:flags=lanczos", "-t", str(dur)]
    else:
        cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", str(HERE / src)]
    subprocess.run(cmd + ENC + [str(out_path)], check=True)

def main():
    print("カット秒数（s009-narration.srt から実測で算出）")
    for src, dur, kind in CUTS:
        print(f"  {src:16}{dur:6.2f}s  ({kind})")
    print(f"  合計 {sum(d for _, d, _ in CUTS):.2f}s\n")

    segs = []
    for i, (src, dur, kind) in enumerate(CUTS, 1):
        seg = HERE / f"_seg{i}.mp4"
        render_cut(src, dur, kind, seg)
        segs.append(seg)

    lst = HERE / "_segs.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(HERE / "s009.mp4")], check=True)
    print("s009.mp4")

if __name__ == "__main__":
    main()
