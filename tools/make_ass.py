#!/usr/bin/env python3
"""SRTと台本から、CapCut手動テロップと同じ見た目のASS字幕を作る。

  python3 tools/make_ass.py scripts/shorts/s036-zouazarashi-suimin.md \
      assets/s036/s036-narration.srt assets/s036/s036-narration.ass

ユーザーが実際にCapCutで編集した動画3本（s033/s031/s036相当）を解析して
決めたスタイル:
  - フォント: Rounded Mplus 1c Black（assets/fonts/MPLUSRounded1c-Black.ttf）
  - 白文字＋太い黒フチ、強調語だけ黄色（実測 RGB 235,203,15 相当）
  - 1行最大12字・最大2行（make_srt.pyのwrap()と同じ基準。SRTの改行をそのまま使う）
  - 画面下から約15〜19%のマージンを空けて配置

強調語の着色は「台本の# 台本表の強調語列」をSRTの各カードの表示文字列
（改行・読点除去後）に対して順番に1回だけ割り当てる（同じ語が2回出ても
2回目以降はハイライトしない誤爆を避けるため）。
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make_srt import BREAK_TIERS, NO_SPLIT, FORMAL_N, TIER_W, MAX_PER_LN  # noqa: E402

OW, OH = 1080, 1920
FONT_NAME = "Rounded Mplus 1c Black"
FONT_SIZE = 78
OUTLINE = 7
MARGIN_V = 300
HIGHLIGHT_BGR = "14CCFF"   # ASS は &HBBGGRR&。RGB(255,204,20) 相当の黄色
WHITE_BGR = "FFFFFF"


def parse_table(lines, i):
    rows = []
    i += 2
    while i < len(lines) and lines[i].strip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def parse_emphasis_words(script_path):
    lines = pathlib.Path(script_path).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == "# 台本":
            j = i + 1
            while not lines[j].strip().startswith("|"):
                j += 1
            rows, _ = parse_table(lines, j)
            words = [row[2] for row in rows if len(row) > 2 and row[2].strip() and row[2].strip() != "—"]
            return words
        i += 1
    return []


def parse_srt(srt_path):
    blocks = pathlib.Path(srt_path).read_text(encoding="utf-8").strip().split("\n\n")
    cards = []
    for b in blocks:
        lines = b.splitlines()
        m = re.search(r"(\d\d:\d\d:[\d,]+) --> (\d\d:\d\d:[\d,]+)", lines[1])
        text = "\n".join(lines[2:])
        cards.append((m[1], m[2], text))
    return cards


def _break_point(s, max_len):
    """sの先頭からmax_len字以内で切る、良い位置を1つ返す（make_srt.wrap()と同じ評価基準）。"""
    best = None
    for i in range(1, min(len(s), max_len) + 1):
        if i < len(s) and s[i - 1:i + 1] in NO_SPLIT:
            continue
        tier = next((n for n, chars in enumerate(BREAK_TIERS) if s[i - 1] in chars), len(BREAK_TIERS))
        if s[max(0, i - 2):i] in FORMAL_N:
            tier = len(BREAK_TIERS)
        score = tier * TIER_W + (max_len - i)
        if best is None or score < best[0]:
            best = (score, i)
    return best[1] if best else max_len


def safe_wrap(text, max_len=MAX_PER_LN):
    """make_srt.wrap()が『2行12字に収まらない』として諦めた長い文節を、
    3行以上に分けてでも必ず画面内に収める（CapCutでの手直しに相当する処理）。
    すでに\\nで改行済みのテキストはそのまま返す。
    """
    if "\n" in text or len(text) <= max_len:
        return text
    lines = []
    s = text
    while len(s) > max_len:
        i = _break_point(s, max_len)
        lines.append(s[:i])
        s = s[i:]
    lines.append(s)
    return "\n".join(lines)


def insert_tags(text, start, end, open_tag, close_tag):
    """textの「改行を除いた文字インデックス」start:endの範囲をタグで囲む。"""
    out = []
    idx = 0
    opened = closed = False
    for ch in text:
        if not opened and idx == start:
            out.append(open_tag)
            opened = True
        out.append(ch)
        if ch != "\n":
            idx += 1
        if opened and not closed and idx == end:
            out.append(close_tag)
            closed = True
    if opened and not closed:
        out.append(close_tag)
    return "".join(out)


def ass_timestamp(srt_ts):
    # "00:00:01,234" -> "0:00:01.23"（ASSはセンチ秒）
    h, m, rest = srt_ts.split(":")
    s, ms = rest.split(",")
    cs = round(int(ms) / 10)
    return f"{int(h)}:{m}:{s}.{cs:02d}"


HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OW}
PlayResY: {OH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT_NAME},{FONT_SIZE},&H00{WHITE_BGR}&,&H000000FF&,&H00000000&,&H00000000&,1,0,0,0,100,100,0,0,1,{OUTLINE},0,2,60,60,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    script_path, srt_path, out_path = sys.argv[1:4]

    emphasis_words = parse_emphasis_words(script_path)
    cards = parse_srt(srt_path)

    lines = [HEADER]
    used = [False] * len(emphasis_words)
    for start_ts, end_ts, text in cards:
        text = safe_wrap(text)
        joined = text.replace("\n", "")
        ass_text = text
        for wi, word in enumerate(emphasis_words):
            if used[wi]:
                continue
            idx = joined.find(word)
            if idx == -1:
                continue
            ass_text = insert_tags(
                text, idx, idx + len(word),
                f"{{\\c&H{HIGHLIGHT_BGR}&}}", f"{{\\c&H{WHITE_BGR}&}}",
            )
            used[wi] = True
            break
        ass_text = ass_text.replace("\n", "\\N")
        lines.append(
            f"Dialogue: 0,{ass_timestamp(start_ts)},{ass_timestamp(end_ts)},Default,,0,0,0,,{ass_text}\n"
        )

    pathlib.Path(out_path).write_text("".join(lines), encoding="utf-8")
    unmatched = [w for w, u in zip(emphasis_words, used) if not u]
    if unmatched:
        print(f"⚠ SRTの表示文字列中に見つからず色付けできなかった強調語: {unmatched}")
    print(out_path)


if __name__ == "__main__":
    main()
