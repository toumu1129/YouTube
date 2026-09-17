# 図解3枚の生成プロンプト

**この3枚は実写が存在しない**（牛の胃の中、飲み込みの断面、牛用磁石）ため、生成するしかない。
以下をそのまま画像生成AIに貼れば作れる。**日本語モデルでも英語のまま入れたほうが精度が出る。**

共通の指定：
- **縦 9:16（1080×1920）**
- **文字を一切入れない**（テロップは編集で乗せるため。ここに文字が入ると二重になる）
- 背景は深緑 `#1B4332`、図はクリーム、金属はグレー、強調は黄 `#FFD60A`
- 上15%・下20%は**空けておく**（YouTubeのUIで隠れる）

---

## ② 0:03–0:07 牛用磁石

```
A single cylindrical alnico bar magnet lying on a plain deep forest-green
surface (#1B4332), with several rusty iron nails and one bent steel wire
clinging to it. Clean editorial product photography, soft directional studio
light, shallow depth of field, centred, vertical 9:16 composition with generous
empty margin at the top and bottom.
No text, no letters, no words, no numbers, no labels, no logos, no watermark.
```

## ③ 0:07–0:20 草ごと金属を飲み込む

```
Educational cutaway illustration of a dairy cow in profile, head lowered to
graze. A cutaway reveals the path from the mouth down the esophagus into the
body, and swallowed grass carrying small iron nails and a bent wire travelling
along that path. Flat vector infographic style, thick clean lines, deep
forest-green background (#1B4332), cream-coloured cow, warm grey metal, the
path marked in warm yellow. Vertical 9:16, centred, generous empty margin top
and bottom.
No text, no letters, no words, no numbers, no labels, no logos, no watermark.
```

## ④ 0:20–0:27 第二胃に磁石が留まる

```
Educational anatomical infographic: cross-section of a cow's four stomach
chambers arranged in a chain, drawn as a clean flat vector medical diagram.
A grey cylindrical bar magnet rests inside the SECOND chamber (the reticulum),
with several iron nails and a bent steel wire stuck to the magnet. Deep
forest-green background (#1B4332), cream-coloured chambers, grey metal, the
second chamber subtly outlined in warm yellow. Vertical 9:16, centred, generous
empty margin top and bottom.
No text, no letters, no words, no numbers, no labels, no logos, no watermark.
```

---

## 受け取ったあと

`assets/s020/` に `f2.jpg` `f3.jpg` `f4.jpg` として置けば、そのまま組み直せる。
1080×1920 でなくても、`cover` で自動的に切り出す。

## 注意

**生成した図が解剖学的に間違っていないか確認すること。** 特に④は、
- 胃は**4つ**（第一胃＝ルーメン／第二胃＝網胃／第三胃／第四胃）
- 磁石が留まるのは**2番目の網胃**

画像生成AIは胃の数を平気で間違える。[06-fact-checking.md](../../docs/06-fact-checking.md) の基準は
図にも適用される。
