#!/usr/bin/env python3
"""台本(.md)から、VOICEVOX(青山龍星)でナレーション音声を生成する。

使い方:
    python3 tools/gen_narration.py scripts/shorts/s004-semi-isshukan.md

- 台本の「# 台本」表からナレーション列を読み、通しで1本の音声にする
  （テロップと完全一致させるため、この列の文字列を一切変えない）
- 「# 読み指定」表の表記→読みの置換は、TTSに渡すテキストだけに適用する
  （画面のテロップ・SRT用テキストは元の表記のまま）
- 「# 間の指定」表（任意）で、句読点の直前の文言を指定すると、
  その直後の間（ポーズ）だけを秒数分だけ伸ばせる
  （VOICEVOXは「。」「、」ごとに間を1つ生成するので、文節の一致で狙い撃ちする）
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

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make_srt import clauses as split_clauses  # noqa: E402

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
    narration_rows, reading_rows, pause_rows = None, None, None
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
        elif line.strip() == "# 間の指定":
            j = i + 1
            while not lines[j].strip().startswith("|"):
                j += 1
            pause_rows, _ = parse_table(lines, j)
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

    pauses = []
    if pause_rows:
        for row in pause_rows:
            marker, delta = row[0], row[1]
            if marker and delta:
                pauses.append((marker, float(delta)))
    return narration, readings, pauses


BRACKETS = str.maketrans("", "", "「」『』")


def apply_readings(text, readings):
    for hyoki, yomi in readings:
        text = text.replace(hyoki, yomi)
    # かぎ括弧はテロップの強調用の記号で、読み上げ対象ではない。
    # VOICEVOXは閉じ括弧を句読点のように扱い、直後に余計な間を作るので、
    # TTS入力からだけ取り除く（テロップ表示はそのまま「」を残す）。
    return text.translate(BRACKETS)


def find_pause_moras(query):
    """accent_phrases を順に見て、間(pause_mora)を持つものだけを順番に返す。

    VOICEVOXは「。」「、」ひとつにつき、直前のaccent_phraseにpause_moraを1つ持たせる。
    そのため、この並びは 読点/句点で割った文節の「区切りどうし」の並びと1対1で対応する
    （tools/make_srt.py の clauses(text, min_clause=0) と同じ順）。
    最後の文節の後ろには区切りが無い（音声の終わりなので）ため、
    間の数は文節の数より1つ少ない。
    """
    return [ap["pause_mora"] for ap in query["accent_phrases"] if ap.get("pause_mora")]


def apply_pauses(query, narration, pauses):
    if not pauses:
        return
    cs = split_clauses(narration, min_clause=0)
    pause_moras = find_pause_moras(query)
    if len(cs) - 1 != len(pause_moras):
        print(f"⚠ 間の指定を反映できない: 文節の区切り {len(cs)-1} ≠ 間 {len(pause_moras)}")
        return
    for marker, delta in pauses:
        idx = next((i for i, c in enumerate(cs[:-1]) if marker in c), None)
        if idx is None:
            print(f"⚠ 間の指定「{marker}」が台本中に見つからない（最後の文節は対象外）")
            continue
        pause_moras[idx]["vowel_length"] += delta
        print(f"  間を調整: 「{cs[idx]}」の直後 {delta:+.2f}秒")


def synthesize(text, speaker=SPEAKER, narration=None, pauses=None):
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
    if pauses:
        apply_pauses(query, narration, pauses)
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

    narration, readings, pauses = parse_script(script_path)
    tts_text = apply_readings(narration, readings)

    print(f"台本: {narration}")
    if readings:
        print(f"読み置換後(TTS入力のみ): {tts_text}")

    wav_bytes = synthesize(tts_text, narration=narration, pauses=pauses)

    wav_path = out_dir / f"{sid}-narration.wav"
    txt_path = out_dir / f"{sid}-narration.txt"
    wav_path.write_bytes(wav_bytes)
    txt_path.write_text(narration + "\n", encoding="utf-8")

    print(f"\n完成: {wav_path}")
    print(f"完成: {txt_path}")
    print(f"\n次: python3 tools/make_srt.py {wav_path} {txt_path}")


if __name__ == "__main__":
    main()
