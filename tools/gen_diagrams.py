#!/usr/bin/env python3
"""台本の図解プロンプトを、OpenAI API(gpt-image-1)で一括生成する。

使い方:
    python3 tools/gen_diagrams.py assets/s0XX/prompts.json

APIキーは環境変数 OPENAI_API_KEY があればそれを使う。なければ
~/.openai_api_key（リポジトリの外、root権限のみ読み取り可）を読む。
このBashツールはコマンドごとに新しいシェルを起動し環境変数を引き継がないため、
セッションをまたいで `export` し続けるより、ファイルから読む方式のほうが確実。

prompts.json の形式:
    [
      {"out": "assets/s020/f2.jpg", "prompt": "A single realistic cow magnet ..."},
      {"out": "assets/s020/f3.jpg", "prompt": "Educational cutaway illustration ..."},
      {"out": "assets/s020/f4.jpg", "prompt": "Educational anatomical infographic ..."}
    ]

- 1024x1024で生成し、こちらで縦9:16(1080x1920)に中央基準で切り出して保存する
  (gpt-image-1は正方形/横/縦の限られた比率しか選べないため、
   縦長素材はこちらで仕上げるほうが確実)
- 生成後、各画像を [16, 48, 96] pxに縮小したコンタクトシートを
  同じフォルダに `_preview.jpg` として書き出す。小サイズでの視認性は
  毎回ここで確認すること（アイコン制作で「小さくすると潰れる」を
  何度も経験したのと同じ理由）
- 失敗した画像があっても他は続行し、最後にまとめて報告する
"""
import base64, json, os, pathlib, sys
from openai import OpenAI
from PIL import Image

OW, OH = 1080, 1920
KEY_FILE = pathlib.Path.home() / ".openai_api_key"

def get_api_key():
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    sys.exit(
        f"OPENAI_API_KEYが見つからない。環境変数で渡すか、{KEY_FILE} にキーだけを書いて保存すること。"
    )

def cover_crop(im, ow, oh):
    im = im.convert("RGB")
    s = max(ow / im.width, oh / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - ow) // 2, (im.height - oh) // 2
    return im.crop((l, t, l + ow, t + oh))

def contact_sheet(im, out_path):
    sizes = (16, 48, 96, 200)
    total_w = sum(sizes) + 10 * (len(sizes) - 1)
    sheet = Image.new("RGB", (total_w, 220), (40, 40, 40))
    x = 0
    for size in sizes:
        r = im.resize((size, size), Image.LANCZOS)
        sheet.paste(r, (x, (220 - size) // 2))
        x += size + 10
    sheet.save(out_path, quality=90)

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    jobs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    client = OpenAI(api_key=get_api_key())

    ok, failed = [], []
    for job in jobs:
        out = pathlib.Path(job["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"生成中: {out} ...")
        try:
            res = client.images.generate(
                model="gpt-image-1",
                prompt=job["prompt"],
                size="1024x1536",   # 縦長。9:16に近い比率を指定し、あとで正確に切り出す
                quality="high",
                n=1,
            )
            img_bytes = base64.b64decode(res.data[0].b64_json)
            raw = out.with_name(out.stem + "_raw.png")
            raw.write_bytes(img_bytes)

            im = cover_crop(Image.open(raw), OW, OH)
            im.save(out, quality=93)

            preview = out.with_name(out.stem + "_preview.jpg")
            contact_sheet(im, preview)

            ok.append(str(out))
            print(f"  完成: {out}  (確認用: {preview})")
        except Exception as e:
            failed.append((str(out), str(e)))
            print(f"  失敗: {out}  理由: {e}")

    print(f"\n完了 {len(ok)}件 / 失敗 {len(failed)}件")
    if failed:
        for out, err in failed:
            print(f"  ✕ {out}: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
