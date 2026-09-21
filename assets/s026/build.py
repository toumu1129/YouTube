#!/usr/bin/env python3
"""s026 の動画を組み立てる。

  python3 build.py            # 出力: s026.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s026-narration.srt`（tools/make_srt.py が音声の無音を実測して作ったもの）から逆算する。
理由は s020/build.py の冒頭コメント、および assets/s020/README.md を参照。

s026は動画1本（f1.mp4、タコのアップ）＋静止画5枚（f2/f3/f3b/f4/f5.jpg）の構成。
- f1.mp4はPexelsの実写動画から、目とサイフォンが安定して見える5-9秒区間を
  1080x1920に切り出し済み（追加のクロップ・スケールはしない）。
- f2.jpg（タコの全身）、f5.jpg（岩陰で休むタコ）はPexelsの実写。
- f3.jpg（腕に浮かぶ青い血管の発光）、f3b.jpg（3つの心臓のX線風オーバーレイ）、
  f4.jpg（ジェット推進と心臓）は①②⑤の実写トーンに合わせ、フォトリアル指定で
  生成したAI画像（プロンプトはこのチャットのやりとり参照）。1080x1920で生成済み。
  ③は当初1枚(14秒)だったが表示時間が長すぎたため、f3(前半)とf3b(後半)の
  2カットに分割した。
"""
import re, subprocess, pathlib, imageio_ffmpeg

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの素材が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
IMAGE_CARDS = [
    ("f1.mp4",  1,  2,  "video"),  # ①タコの心臓は、3つあります。
    ("f2.jpg",  3,  4,  "image"),  # ②しかも血液は、赤ではなく青色です。
    ("f3.jpg",  5,  6,  "image"),  # ③前半 酸素を運ぶのに…からです。
    ("f3b.jpg", 7,  9,  "image"),  # ③後半 効率が悪いぶん…必要になりました。
    ("f4.jpg",  10, 13, "image"),  # ④さらに泳ぐときは…好むのです。
    ("f5.jpg",  14, 15, "image"),  # ⑤タコは、心臓をいたわりながら…かもしれません。
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

CUTS, _BOUNDS = cuts_from_srt(HERE / "s026-narration.srt")

def render_cut(src, dur, kind, out_path):
    if kind == "video":
        cmd = [FF, "-y", "-loglevel", "error", "-i", str(HERE / src),
               "-vf", f"scale={OW}:{OH}:flags=lanczos", "-t", str(dur)]
    else:
        cmd = [FF, "-y", "-loglevel", "error", "-loop", "1", "-t", str(dur), "-i", str(HERE / src)]
    subprocess.run(cmd + ENC + [str(out_path)], check=True)

def main():
    print("カット秒数（s026-narration.srt から実測で算出）")
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
                    "-i", str(lst), "-c", "copy", str(HERE / "s026.mp4")], check=True)
    print("s026.mp4")

if __name__ == "__main__":
    main()
