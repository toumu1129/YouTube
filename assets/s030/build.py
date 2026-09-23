#!/usr/bin/env python3
"""s030 の動画を組み立てる。

  python3 build.py            # 出力: s030.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s030-narration.srt`（tools/make_srt.py が音声の無音を実測して作ったもの）から逆算する。
理由は s020/build.py の冒頭コメント、および assets/s020/README.md を参照。

s030は動画2本（f1.mp4, f5.mp4）＋静止画3枚（f2/f3/f4.jpg）の構成。
- f1.mp4（アリのアップ、花で蜜を吸う）とf5.mp4（葉の上で働くアリたち）はPexelsの実写。
- f2.jpg（脚を怪我したアリの手当て）、f3.jpg（脚の部位と治療法の図解、太もも＝
  オレンジ／すね＝ブルー）、f4.jpg（体液の流れの図解、太もも＝密で遅い／すね＝
  速く streaking）は、切断手術の実写素材が存在しないため生成AIで作成
  （プロンプトはこのチャットのやりとり参照）。1080x1920で生成済み。
"""
import re, subprocess, pathlib, imageio_ffmpeg

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの素材が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
IMAGE_CARDS = [
    ("f1.mp4", 1, 2,   "video"),  # ①アリは、手術をします。
    ("f2.jpg", 3, 4,   "image"),  # ②怪我をしている仲間の脚を…あるのです。
    ("f3.jpg", 5, 8,   "image"),  # ③太ももに近い脚の怪我なら…上がります。
    ("f4.jpg", 9, 10,  "image"),  # ④太ももは血の流れが…しかないのです。
    ("f5.mp4", 11, 12, "video"),  # ⑤アリは、傷の深刻さを…かもしれません。
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

CUTS, _BOUNDS = cuts_from_srt(HERE / "s030-narration.srt")

def render_cut(src, dur, kind, out_path):
    if kind == "video":
        cmd = [FF, "-y", "-loglevel", "error", "-i", str(HERE / src),
               "-vf", f"scale={OW}:{OH}:flags=lanczos", "-t", str(dur)]
    else:
        cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", str(HERE / src)]
    subprocess.run(cmd + ENC + [str(out_path)], check=True)

def main():
    print("カット秒数（s030-narration.srt から実測で算出）")
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
                    "-i", str(lst), "-c", "copy", str(HERE / "s030.mp4")], check=True)
    print("s030.mp4")

if __name__ == "__main__":
    main()
