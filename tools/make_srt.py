#!/usr/bin/env python3
"""ナレーション音声から、声と一致する字幕(SRT)を作る。

  python3 tools/make_srt.py <音声> <台本テキスト> [出力.srt]

台本テキストは、その回のナレーション全文（改行は自由）。
「。」「、」で文節に割り、音声の無音区間で検出した発話区間と突き合わせる。

**推定ではなく実測で合わせる。** AI音声は同じ文でも読む速さが揺れるので、
字数から時間を割り出すと必ずずれる。無音の位置は audio が答えを持っている。

区間数が合わない場合は、その旨を出して字数比で按分する（要手直し）。
"""
import re, subprocess, sys, pathlib
import imageio_ffmpeg

NOISE_DB   = -38     # これより静かなら無音とみなす
MIN_SIL    = 0.18    # この長さ以上の無音だけを区切りとして扱う
TAIL_GAP   = 0.06    # 次のカードが出る直前まで表示を残す
MAX_PER_LN = 12      # 1行の最大文字数（docs/03 の指定）
MIN_CLAUSE = 5       # これより短い文節は次に繋ぐ（AI音声は短い読点で息継ぎしない）

def speech_spans(audio):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = subprocess.run(
        [ff, "-i", str(audio), "-af", f"silencedetect=noise={NOISE_DB}dB:d={MIN_SIL}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    dur = None
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if m: dur = int(m[1])*3600 + int(m[2])*60 + float(m[3])
    sil = [(float(a), float(b)) for a, b in
           zip(re.findall(r"silence_start: ([\d.]+)", out),
               re.findall(r"silence_end: ([\d.]+)", out))]
    spans, t = [], 0.0
    for s, e in sil:
        if s > t: spans.append((t, s))
        t = e
    if dur and dur > t: spans.append((t, dur))
    return spans, dur

def clauses(text):
    """。と、で割る。区切り文字は前の文節に残す。

    ただし「牛は、」のような短い文節では AI音声が息継ぎしないため、
    MIN_CLAUSE 未満は次の文節に繋ぐ。ここを切ると発話区間と数が合わなくなる。
    """
    text = re.sub(r"\s+", "", text)
    raw = [c for c in re.findall(r"[^。、]*[。、]?", text) if c]
    out, buf = [], ""
    for c in raw:
        buf += c
        if len(buf) >= MIN_CLAUSE:
            out.append(buf); buf = ""
    if buf:
        if out: out[-1] += buf
        else:   out.append(buf)
    return out

# 改行してよい位置の優先順位。上から順に良い。
BREAK_TIERS = ("、。", "はがをにへでもと", "るたてりい")
# ここで割ってはいけない2文字（「心臓まで達すること|があります」のような折れを防ぐ）
NO_SPLIT = {"こと","もの","ため","よう","ます","ませ","でし","まし","れる","られ",
            "です","ない","とい","いう","って","った","ある","いる"}
# 形式名詞の語尾。ここの「と」「の」は助詞ではないので、折り位置として降格する
FORMAL_N = {"こと","もの","ため","よう","とき","ところ"}
TIER_W   = 2.5       # 折り位置の良さ（tier）と中央からの距離の重みづけ

def wrap(s):
    """1行 MAX_PER_LN 字で最大2行に折る。

    句読点 > 助詞 > 活用語尾 の順に折り位置を選び、
    両行とも MAX_PER_LN 以内で、なるべく中央に近いところで折る。
    """
    if len(s) <= MAX_PER_LN:
        return s
    mid = len(s) / 2
    best = None
    for i in range(1, len(s)):
        if len(s[:i]) > MAX_PER_LN or len(s[i:]) > MAX_PER_LN:
            continue
        if s[i-1:i+1] in NO_SPLIT:
            continue
        tier = next((n for n, chars in enumerate(BREAK_TIERS) if s[i-1] in chars), len(BREAK_TIERS))
        if s[max(0, i-2):i] in FORMAL_N:      # 「〜すること|が」のような折れを避ける
            tier = len(BREAK_TIERS)
        score = tier * TIER_W + abs(i - mid)
        if best is None or score < best[0]:
            best = (score, i)
    if best is None:                       # 12字×2行に収まらない → そのまま返して手直しに回す
        return s
    i = best[1]
    return s[:i] + "\n" + s[i:]

def ts(t):
    h, r = divmod(max(0.0, t), 3600); m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")

def main():
    audio, script = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    out = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else audio.with_suffix(".srt")
    cs = clauses(script.read_text(encoding="utf-8"))
    spans, dur = speech_spans(audio)

    if len(spans) == len(cs):
        print(f"発話区間 {len(spans)} = 文節 {len(cs)}  → 実測で対応")
        pairs = list(zip(cs, spans))
    else:
        print(f"⚠ 発話区間 {len(spans)} ≠ 文節 {len(cs)}  → 字数比で按分。要手直し")
        total = sum(len(c) for c in cs); t = 0.0; pairs = []
        for c in cs:
            d = dur * len(c) / total
            pairs.append((c, (t, t+d))); t += d

    lines = []
    for i, (c, (a, b)) in enumerate(pairs):
        end = (pairs[i+1][1][0] - TAIL_GAP) if i+1 < len(pairs) else (dur or b)
        lines.append(f"{i+1}\n{ts(a)} --> {ts(max(end, a+0.4))}\n{wrap(c)}\n")
    out.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{out}  ({len(pairs)}枚)")
    for i, (c, (a, _)) in enumerate(pairs):
        print(f"  {i+1:2d}  {a:6.2f}s  {c}")

if __name__ == "__main__":
    main()
