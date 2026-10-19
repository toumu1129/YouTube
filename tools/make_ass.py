#!/usr/bin/env python3
"""SRTと台本から、CapCut手動テロップと同じ見た目のASS字幕を作る。

  python3 tools/make_ass.py scripts/shorts/s036-zouazarashi-suimin.md \
      assets/s036/s036-narration.srt assets/s036/s036-narration.ass

ユーザーが実際にCapCutで編集した動画3本（カマキリ・ミツバチ・ゾウアザラシ）
を解析して決めたスタイル:
  - フォント: BIZ UDGothic Bold（学術的な印象にしたいという要望で、
    元のRounded Mplus 1c Blackから変更。assets/fonts/BIZUDGothic-Bold.ttf）
  - 白文字＋太い黒フチ、強調語だけ黄色（実測 RGB 235,203,15 相当）
  - テロップの垂直方向の「中心」が、1行でも2行でも常に同じ位置に来る
    （画面下からの実測: 1行の中心1458.5px、2行の中心1460.5px、ほぼ一致）
    → ASSのAlignment依存のマージン積み上げではなく、\\pos+\\an5で
      毎カード同じ中心座標に固定する
  - 1行あたりの文字数は、make_srt.pyの「12字まで目一杯詰める」より
    もっと短い。実測では「1文節(て形・助詞の切れ目)につき1行」に近く、
    make_srt.pyが1枚のSRTカードとして確定した長い文節（音声の無音検出
    による区切り）を、表示上はさらに複数のテロップカードに割って
    見せている（同じ発話区間の時間を文字数比で配分）。

強調語の着色は「台本の# 台本表の強調語列」を、分割後の各カードの表示
文字列に対して順番に1回だけ割り当てる（同じ語が2回出ても2回目以降は
ハイライトしない誤爆を避けるため）。
"""
import pathlib
import re
import sys

OW, OH = 1080, 1920
POS_X, POS_Y = OW // 2, 1460   # テロップの中心（実測値）
FONT_NAME = "BIZ UDGothic"
FONT_SIZE = 78
OUTLINE = 7
HIGHLIGHT_BGR = "14CCFF"   # ASS は &HBBGGRR&。RGB(255,204,20) 相当の黄色
WHITE_BGR = "FFFFFF"

MAX_LINE = 10   # 1行の目安文字数（make_srt.pyのMAX_PER_LN=12より短い）
MIN_LINE = 3    # これより短い断片は作らない

# 行の切れ目として良い位置（良い順）。make_srt.pyのBREAK_TIERSと考え方は
# 同じだが、「文節ごとに改行する」という今回の目的に合わせて「の」
# 「から」「まで」などの助詞・接続表現を追加で含めている。
# 2文字以上の語は、単純な文字単位の包含チェックだと誤爆する
# （例:「より」のために「取り」の「り」まで高評価になってしまう）ので、
# 末尾一致で個別にチェックする。
TIER0_CHARS = "、。！？"
# 「は/が/を/に」は主語・目的語など文の骨格を切り出す強い助詞なので最優先。
# 「へ/で/も/と/の」は名詞句の内部をつなぐことが多い弱い助詞なので、
# 単体の「るたてりいだ」などと同じtier2に落とす（例:「他の言葉と」を
# 「他の」で割らず、ひとまとまりのまま次の行に送れるようにするため）。
TIER1_CHARS = "はがをに"
TIER1_SUFFIXES = ("から", "まで", "より", "ながら")
TIER2_CHARS = "へでもとのるたてりいだ"
TIER2_SUFFIXES = ("だけ", "まま", "ので", "けど", "ことで")
NO_SPLIT = {"こと", "もの", "ため", "よう", "ます", "ませ", "でし", "まし", "れる", "られ",
            "です", "ない", "とい", "いう", "って", "った", "ある", "いる",
            "では", "には", "とは", "もは", "へは", "らは", "とっ"}
FORMAL_N = {"こと", "もの", "ため", "よう", "とき", "ところ"}
TIER_W = 2.5

# 「ながら」の内側（な|がら、なが|ら）や「とき」の内側（と|き）のように、
# 2文字以上の語の途中を誤って切らないよう、語を構成する隣接2文字を
# すべてNO_SPLIT扱いにする（FORMAL_N自体も語の説明用途しか使わないが、
# 内部分割の禁止には使うのでここでまとめて含める）。
_SUFFIX_NO_SPLIT = {
    suf[k - 1:k + 1]
    for suf in TIER1_SUFFIXES + TIER2_SUFFIXES + tuple(FORMAL_N)
    for k in range(1, len(suf))
}


def _tier_at(s, i):
    """位置i（s[:i] / s[i:]に切る）の良さをtier番号で返す（小さいほど良い）。"""
    for suf in TIER1_SUFFIXES:
        if s[max(0, i - len(suf)):i] == suf:
            return 1
    ch = s[i - 1]
    if ch in TIER0_CHARS:
        return 0
    if ch in TIER1_CHARS:
        return 1
    for suf in TIER2_SUFFIXES:
        if s[max(0, i - len(suf)):i] == suf:
            return 2
    if ch in TIER2_CHARS:
        return 2
    return 3


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
    """SRTを [(開始秒, 終了秒, 改行・読点除去済みテキスト), ...] にする。"""
    blocks = pathlib.Path(srt_path).read_text(encoding="utf-8").strip().split("\n\n")

    def to_sec(ts):
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    cards = []
    for b in blocks:
        lines = b.splitlines()
        m = re.search(r"(\d\d:\d\d:[\d,]+) --> (\d\d:\d\d:[\d,]+)", lines[1])
        text = "".join(lines[2:])  # 既存の改行(\n)は捨てて、ここで作り直す
        cards.append((to_sec(m[1]), to_sec(m[2]), text))
    return cards


def _break_point(s, max_len, min_len=MIN_LINE):
    """sの先頭 [min_len, max_len] 字の範囲で切る、一番良い位置を返す。

    tierが同じなら、sの中央に近い位置を優先する（make_srt.wrap()と同じ
    発想）。これにより「文の前半だけ短く切って後が長く余る」のを防ぎ、
    2つの文節の長さがなるべく揃う位置で切れる。
    """
    best = None
    lo = min(min_len, len(s))
    hi = min(len(s), max_len)
    mid = len(s) / 2
    for i in range(lo, hi + 1):
        if i < len(s) and (s[i - 1:i + 1] in NO_SPLIT or s[i - 1:i + 1] in _SUFFIX_NO_SPLIT):
            continue
        tier = _tier_at(s, i)
        if s[max(0, i - 2):i] in FORMAL_N:
            tier = 3
        score = tier * TIER_W + abs(i - mid)
        if best is None or score < best[0]:
            best = (score, i)
    return best[1] if best else hi


def chunk_lines(text, max_len=MAX_LINE):
    """textを、1行max_len字以内の「行」のリストに分割する（文節優先）。"""
    lines = []
    s = text
    while len(s) > max_len:
        i = _break_point(s, max_len)
        lines.append(s[:i])
        s = s[i:]
    if s:
        lines.append(s)
    return lines


def split_into_cards(start, end, text):
    """1つのSRTカード(音声の無音検出による区切り)を、1〜2行のテロップカード
    何枚かに割る。各カードの時間は、元の区間を文字数比で配分する
    （実際の発話内でのタイミングは分からないため、文字数からの近似）。
    """
    lines = chunk_lines(text)
    sub_cards = [lines[i:i + 2] for i in range(0, len(lines), 2)]

    total_chars = sum(len(ln) for card in sub_cards for ln in card)
    t = start
    out = []
    for i, card in enumerate(sub_cards):
        chars = sum(len(ln) for ln in card)
        dur = (end - start) * chars / total_chars if total_chars else 0
        card_end = end if i == len(sub_cards) - 1 else t + dur
        out.append((t, card_end, "\n".join(card)))
        t = card_end
    return out


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


def ass_timestamp(sec):
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {OW}
PlayResY: {OH}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT_NAME},{FONT_SIZE},&H00{WHITE_BGR}&,&H000000FF&,&H00000000&,&H00000000&,1,0,0,0,100,100,0,0,1,{OUTLINE},0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    script_path, srt_path, out_path = sys.argv[1:4]

    emphasis_words = parse_emphasis_words(script_path)
    srt_cards = parse_srt(srt_path)

    all_cards = []
    for start, end, text in srt_cards:
        all_cards.extend(split_into_cards(start, end, text))

    lines = [HEADER]
    used = [False] * len(emphasis_words)
    for start, end, text in all_cards:
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
        pos = f"{{\\an5\\pos({POS_X},{POS_Y})}}"
        lines.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},Default,,0,0,0,,{pos}{ass_text}\n"
        )

    pathlib.Path(out_path).write_text("".join(lines), encoding="utf-8")
    unmatched = [w for w, u in zip(emphasis_words, used) if not u]
    if unmatched:
        print(f"⚠ 色付けできなかった強調語（分割後のカードをまたいでいる可能性）: {unmatched}")
    print(f"{out_path}  ({len(all_cards)}カード、元のSRTは{len(srt_cards)}カード)")


if __name__ == "__main__":
    main()
