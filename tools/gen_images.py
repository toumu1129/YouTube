#!/usr/bin/env python3
"""台本の「# 画像生成プロンプト」表から、OpenAI Images APIで素材画像を作る。

  python3 tools/gen_images.py scripts/shorts/sXXX-yyy.md
  python3 tools/gen_images.py scripts/shorts/sXXX-yyy.md --dry-run   # APIを呼ばず内容確認だけ
  python3 tools/gen_images.py scripts/shorts/sXXX-yyy.md --force     # 既存ファイルも作り直す

台本の「# 画像生成プロンプト」表（ファイル名 | プロンプト の2列）を読み、
OpenAI Images API (gpt-image-2) で1080x1920相当の画像を生成し、
cover crop で正確に1080x1920へ切り出して assets/sXXX/<ファイル名> に保存する。

環境変数 OPENAI_API_KEY が必要。このクラウド環境では、セッションの
環境設定（タイトルバーの環境メニュー → 編集）のNetwork secretsか
環境変数にOPENAI_API_KEYを登録しておくこと。チャットにキーを直接
貼らないこと。

課金が発生するAPIなので、**既に存在するファイルは上書きしない**
（作り直したいときは先に手でファイルを消すか --force を使う）。
"""
import argparse
import base64
import io
import pathlib
import re
import sys

OW, OH = 1080, 1920
GEN_SIZE = "1088x1920"   # OpenAI Images APIは16の倍数しか受け付けないので、
                          # 9:16(1080x1920)に最も近いサイズをここで生成し、
                          # 後でcover cropして正確な1080x1920にする。
MODEL = "gpt-image-2"
QUALITY = "high"


def parse_table(lines, i):
    rows = []
    i += 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def parse_prompts(script_path):
    lines = pathlib.Path(script_path).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "# 画像生成プロンプト":
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("|"):
                j += 1
            rows, _ = parse_table(lines, j)
            return [(row[0], row[1]) for row in rows if len(row) >= 2 and row[0].strip() and row[1].strip()]
        i += 1
    return []


def cover_crop(im, ow, oh, x_anchor=0.5, y_anchor=0.5):
    from PIL import Image
    w, h = im.size
    scale = max(ow / w, oh / h)
    nw, nh = round(w * scale), round(h * scale)
    im2 = im.resize((nw, nh), Image.LANCZOS)
    x = round((nw - ow) * x_anchor)
    y = round((nh - oh) * y_anchor)
    return im2.crop((x, y, x + ow, y + oh))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("script_path")
    ap.add_argument("--force", action="store_true", help="既にあるファイルも作り直す")
    ap.add_argument("--dry-run", action="store_true", help="APIを呼ばず、対象とプロンプトを表示するだけ")
    args = ap.parse_args()

    script_path = pathlib.Path(args.script_path)
    sid = re.match(r"(s\d+)", script_path.stem)[1]
    out_dir = pathlib.Path("assets") / sid
    out_dir.mkdir(parents=True, exist_ok=True)

    prompts = parse_prompts(script_path)
    if not prompts:
        sys.exit("台本に「# 画像生成プロンプト」の表（中身入り）が見つからない")

    targets, skipped = [], []
    for filename, prompt in prompts:
        out_path = out_dir / filename
        if out_path.exists() and not args.force:
            skipped.append(out_path)
            continue
        targets.append((out_path, prompt))

    for p in skipped:
        print(f"skip（既存。作り直すなら --force）: {p}")
    for out_path, prompt in targets:
        print(f"--- {out_path} ---\n{prompt}\n")

    if not targets:
        print("生成対象なし")
        return
    if args.dry_run:
        print(f"[dry-run] {len(targets)}件を生成予定（実行していません）")
        return

    import os
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("環境変数 OPENAI_API_KEY が設定されていない（チャットには貼らず、環境設定に登録すること）")

    from openai import OpenAI
    from PIL import Image

    client = OpenAI()
    for out_path, prompt in targets:
        print(f"生成中: {out_path}")
        result = client.images.generate(
            model=MODEL, prompt=prompt, size=GEN_SIZE, quality=QUALITY, n=1,
        )
        raw = base64.b64decode(result.data[0].b64_json)
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im = cover_crop(im, OW, OH)
        im.save(out_path, quality=95)
        print(f"  完成: {out_path}")


if __name__ == "__main__":
    main()
