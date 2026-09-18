#!/usr/bin/env python3
"""台本(.md)から、VOICEVOX(青山龍星)でナレーション音声を生成する。

使い方:
    python3 tools/gen_narration.py scripts/shorts/s004-semi-isshukan.md

- 台本の「# 台本」表からナレーション列を読み、通しで1本の音声にする
  （テロップと完全一致させるため、この列の文字列を一切変えない）
- 「# 読み指定」表の表記→読みの置換は、TTSに渡すテキストだけに適用する
  （画面のテロップ・SRT用テキストは元の表記のまま）
- 出力は assets/sXXX/sXXX-narration.wav と、SRT生成用のテキスト
  assets/sXXX/sXXX-narration.txt（読み指定を反映しない、元のナレーション文）

VOICEVOXエンジンが http://127.0.0.1:50021 で起動している必要がある
(このコンテナでは /root/voicevox_engine/linux-cpu-x64/run で起動する)。

生成後は次を実行して字幕を作る:
    python3 tools/make_srt.py assets/sXXX/sXXX-narration.wav assets/sXXX/sXXX-narration.txt
"""
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ENGINE = "http://127.0.0.1:50021"
SPEAKER = 13  # 青山龍星 ノーマル


def parse_table(lines, i):
    """i行目がヘッダ行の markdown table を [[セル,...], ...] で返す。次に読む行番号も返す。"""
    rows = []
    i += 2  # ヘッダ行 + 区切り線(---)をスキップ
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def parse_script(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    narration_rows, reading_rows = None, None
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == "# 台本":
            j = i + 1
            while not lines[j].strip().startswith("|"):
                j += 1
            narration_rows, _ = parse_table(lines, j)
        elif line.strip() == "# 読み指定":
            j = i + 1
            while not lines[j].strip().startswith("|"):
                j += 1
            reading_rows, _ = parse_table(lines, j)
        i += 1

    if not narration_rows:
        sys.exit("「# 台本」の表が見つからない")
    narration = "".join(row[1] for row in narration_rows)

    readings = []
    if reading_rows:
        for row in reading_rows:
            hyoki, yomi = row[0], row[1]
            # 表の空白は見やすさのためのもの。TTSに空白を渡すと不要な間が入るので取り除く
            yomi = yomi.replace(" ", "").replace("　", "")
            if hyoki and yomi:
                readings.append((hyoki, yomi))
    # 長い表記から先に置換する（短い表記が長い表記の一部を壊すのを防ぐ）
    readings.sort(key=lambda p: -len(p[0]))
    return narration, readings


def apply_readings(text, readings):
    for hyoki, yomi in readings:
        text = text.replace(hyoki, yomi)
    return text


def synthesize(text, speaker=SPEAKER):
    def post(path, params, body=None):
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        req = urllib.request.Request(f"{ENGINE}{path}?{qs}", method="POST")
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, data=data, timeout=120) as res:
            return res.read()

    query = json.loads(post("/audio_query", {"text": text, "speaker": speaker}))
    wav = post("/synthesis", {"speaker": speaker}, body=query)
    return wav


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    script_path = pathlib.Path(sys.argv[1])
    sid = re.match(r"(s\d+)", script_path.stem)[1]
    out_dir = pathlib.Path("assets") / sid
    out_dir.mkdir(parents=True, exist_ok=True)

    narration, readings = parse_script(script_path)
    tts_text = apply_readings(narration, readings)

    print(f"台本: {narration}")
    if readings:
        print(f"読み置換後(TTS入力のみ): {tts_text}")

    wav_bytes = synthesize(tts_text)

    wav_path = out_dir / f"{sid}-narration.wav"
    txt_path = out_dir / f"{sid}-narration.txt"
    wav_path.write_bytes(wav_bytes)
    txt_path.write_text(narration + "\n", encoding="utf-8")

    print(f"\n完成: {wav_path}")
    print(f"完成: {txt_path}")
    print(f"\n次: python3 tools/make_srt.py {wav_path} {txt_path}")


if __name__ == "__main__":
    main()
