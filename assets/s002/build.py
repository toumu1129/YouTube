#!/usr/bin/env python3
"""s002 の動画を組み立てる。

  python3 build.py            # 出力: s002.mp4（1080x1920 / 30fps / 音声なし）

【重要】各カットの秒数は、この場で決め打ちしない。
`s002-narration.srt`（tools/make_srt.py が音声の無音を実測して作ったもの）から逆算する。
理由は s020/build.py の冒頭コメント、および assets/s020/README.md を参照。

s002は画像ではなく動画クリップ5本（フリー素材2本＋Kling生成3本）を使う。
クリップの長さと必要な尺が一致しないところは、以下のように処理する：

- ①②（f1-2-walk.mp4、16秒）：同じ1本の連続したショットを、①の終わりから
  ②を続けて切り出す（ハトが同じ個体・同じ歩きなので、途中で頭出しし直さない）。
- ③（f3-mechanism.mp4、8.04秒）：頭固定→追いつくの動きを見せるカット。
  0.5倍速にすると必要な尺（約13秒）を上回るので、0.5倍速にしたうえで
  必要な秒数だけ使う。頭が止まる瞬間・追いつく瞬間も見やすくなる一石二鳥。
- ④（f4-treadmill.mp4、8.04秒）：必要な尺にわずかに足りないので、
  過不足ぶんだけ再生速度を微調整して過不足なく尺を合わせる（体感できない程度の差）。
- ⑤（f5-eye.mp4、20秒）：必要な尺だけ先頭から使う。
"""
import re, subprocess, pathlib, imageio_ffmpeg

HERE = pathlib.Path(__file__).parent
FF   = imageio_ffmpeg.get_ffmpeg_exe()
OW, OH, FPS = 1080, 1920, 30
ENC  = "-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -r 30 -an".split()

# どの動画が、SRT の何枚目〜何枚目のカードに対応するか（1始まり・両端含む）。
IMAGE_CARDS = [
    ("f1-2-walk.mp4", 1,  2,  False),  # ①ハトは、首を振っていません。
    ("f1-2-walk.mp4", 3,  5,  False),  # ②歩くたびにカクカク…（①の続きを再生）
    ("f3-mechanism.mp4", 6, 11, True), # ③実際は逆です…正体です。（0.5倍速）
    ("f4-treadmill.mp4", 12, 15, False), # ④頭を止めるのは…振らなくなります。
    ("f5-eye.mp4", 16, 17, False),     # ⑤平和の象徴ともいえるハトは…
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
    """IMAGE_CARDS と実測タイムラインから、各カットの (動画, 秒数, 0.5倍速か) を出す。

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
    for i, (vid, _, _, half_speed) in enumerate(IMAGE_CARDS):
        dur = round(bounds[i + 1] - bounds[i], 3)
        cuts.append((vid, dur, half_speed))
    return cuts, bounds

CUTS, _BOUNDS = cuts_from_srt(HERE / "s002-narration.srt")

def probe_duration(path):
    out = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])

def render_segment(vid, dur, half_speed, src_start, out_path):
    src = HERE / vid
    scale = f"scale={OW}:{OH}:flags=lanczos"
    if half_speed:
        # 0.5倍速にしたうえで、必要な秒数だけ使う
        cmd = [FF, "-y", "-loglevel", "error", "-i", str(src),
               "-vf", f"setpts=2.0*PTS,{scale}", "-t", str(dur)]
    elif src_start is not None:
        cmd = [FF, "-y", "-loglevel", "error", "-ss", str(src_start), "-i", str(src),
               "-vf", scale, "-t", str(dur)]
    else:
        # 尺がわずかに足りない場合、過不足ぶんだけ速度を微調整して合わせる
        src_dur = probe_duration(src)
        speed_pts = dur / src_dur
        cmd = [FF, "-y", "-loglevel", "error", "-i", str(src),
               "-vf", f"setpts={speed_pts}*PTS,{scale}", "-t", str(dur)]
    subprocess.run(cmd + ENC + [str(out_path)], check=True)

def main():
    print("カット秒数（s002-narration.srt から実測で算出）")
    for vid, dur, half_speed in CUTS:
        print(f"  {vid:18}{dur:6.2f}s" + ("  ← 0.5倍速" if half_speed else ""))
    print(f"  合計 {sum(d for _, d, _ in CUTS):.2f}s\n")

    segs = []
    # ①②は同じソースの連続したショットとして、①の終わりから②を続けて切り出す
    cursor = 0.0
    for i, (vid, dur, half_speed) in enumerate(CUTS, 1):
        seg = HERE / f"_seg{i}.mp4"
        src_start = None
        if vid == "f1-2-walk.mp4":
            src_start = cursor
            cursor += dur
        elif vid == "f5-eye.mp4":
            src_start = 0.0
        render_segment(vid, dur, half_speed, src_start, seg)
        segs.append(seg)

    lst = HERE / "_segs.txt"
    lst.write_text("".join(f"file '{s.name}'\n" for s in segs))
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(HERE / "s002.mp4")], check=True)
    print("s002.mp4")

if __name__ == "__main__":
    main()
