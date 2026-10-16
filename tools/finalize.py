#!/usr/bin/env python3
"""台本から、投稿用の最終ファイル（音声+テロップ焼き込み済み）まで一括で作る。

  python3 tools/finalize.py scripts/shorts/s036-zouazarashi-suimin.md

前提:
  - VOICEVOXエンジンが http://127.0.0.1:50021 で起動していること
  - assets/sXXX/build.py が書かれていて、f*.jpg/f*.mp4 が揃っていること
    （build.pyは画像の切り替えタイミングをSRTから読むので、このスクリプトが
    SRTを作り直した後に実行する）

やること（すべて自動・CapCut等の手作業は不要）:
  1. tools/gen_narration.py   台本 → ナレーション音声(wav)
  2. tools/make_srt.py        音声 → 実測タイミングのSRT
  3. assets/sXXX/build.py     画像 → 無音声の動画(sXXX.mp4)
  4. tools/make_ass.py        台本+SRT → テロップ(ASS、文節優先の改行・
                               強調語の色付け込み)
  5. ffmpeg                   動画+音声を合成し、さらにテロップを焼き込む
                               → assets/sXXX/sXXX-final.mp4（最終納品物）
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
FONTS_DIR = HERE.parent / "assets" / "fonts"


def run(cmd, **kw):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kw)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    script_path = pathlib.Path(sys.argv[1])
    sid = re.match(r"(s\d+)", script_path.stem)[1]
    out_dir = pathlib.Path("assets") / sid

    wav = out_dir / f"{sid}-narration.wav"
    txt = out_dir / f"{sid}-narration.txt"
    srt = out_dir / f"{sid}-narration.srt"
    ass = out_dir / f"{sid}-narration.ass"
    silent = out_dir / f"{sid}.mp4"
    with_audio = out_dir / f"{sid}-with-audio.mp4"
    final = out_dir / f"{sid}-final.mp4"

    print("① ナレーション生成")
    run([sys.executable, str(HERE / "gen_narration.py"), str(script_path)])

    print("② SRT生成（実測タイミング）")
    run([sys.executable, str(HERE / "make_srt.py"), str(wav), str(txt)])

    print("③ 無音声動画をビルド（build.pyが上のSRTから各カットの秒数を算出）")
    run([sys.executable, "build.py"], cwd=out_dir)

    print("④ テロップ(ASS)生成")
    run([sys.executable, str(HERE / "make_ass.py"), str(script_path), str(srt), str(ass)])

    print("⑤ 音声を合成")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(wav),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(with_audio)])

    print("⑥ テロップを焼き込み")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(with_audio),
         "-vf", f"ass={ass}:fontsdir={FONTS_DIR}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "copy", str(final)])

    print(f"\n完成: {final}")


if __name__ == "__main__":
    main()
