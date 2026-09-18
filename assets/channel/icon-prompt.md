# チャンネルアイコン 生成プロンプト（ChatGPT用）

**カラス限定はやめた。** このチャンネルはカラス・ハト・ダンゴムシ・アリ・セミ・ネコ・ゴキブリなど
多様な身近な生き物を扱う。特定の1種をアイコンにすると、その種の専門チャンネルに見えてしまい、
コンセプト（「その辺にいる生き物の、誰も答えられない『なぜ』」）と噛み合わない。

代わりに、**チャンネルの核である「なぜ？」という問いかけそのもの**をロゴ化する。
種に依存しないので、どんな生き物を扱う回でも違和感がない。

**必ず守ってほしい条件は、この2つ。**（Pillow版の試作で実際に確認済みの教訓）

1. **正方形（1:1）。** YouTubeのアイコンは正方形でトリミングされる
2. **単純な塊＋差し色の点、に還元できる形にする。** 48px以下（コメント欄・登録者一覧の表示サイズ）
   に縮小したとき、細かい線や複数パーツがあると潰れて判別できなくなることを実際に確認した。
   「？」マーク1つ、という最小限の形に絞る

---

## デザインの狙い

「？」の**点の部分**を、生き物の**丸い目**に置き換える。曲線部分（フックの上のカーブ）は、
そのまま「？」として読めつつ、心なしか動物の耳やしっぽのようにも見える丸みを持たせる。
特定の種を描かずに「生き物の気配のする問いかけマーク」にするのが狙い。

## プロンプト

```
A minimalist YouTube channel icon, square 1:1 format. A single large bold question
mark ("?") rendered as a solid flat black shape, filling most of the frame, centered
with even margin on all sides. Solid flat dark forest-green background (#1B4332),
completely plain, no gradient, no texture, no vignette. The question mark's curved
hook is thick, chunky, and softly rounded — friendly and organic rather than a sharp
typographic character, with a subtle hint of an animal's ear or tail curling at the
top, but it must still read clearly and immediately as a question mark, not as an
animal. The dot at the bottom of the question mark is replaced by a single round
solid bright yellow circle (#FFD60A), like a single curious eye — this is the only
accent color in the whole image. Flat vector logo style, no gradients, no drop
shadows, no 3D shading, no outline stroke, no internal linework. The whole shape
must stay bold and simple enough to read instantly as "a question mark with one
yellow eye" even when scaled down to 48x48 pixels. No text, no letters, no words,
no numbers, no logos, no watermark, no signature anywhere in the image.
```

## 受け取ったあと

1. **48pxと16pxに縮小して、「？」と黄色い点がわかるか確認する**
2. 正方形で出てこなかった場合は中央基準でクロップする
3. `assets/channel/icon.png` を上書きし、`docs/01-channel-concept.md` §7 の記述も更新する

---

## 参考：不採用にしたカラス版

最初はカラスの頭部クローズアップ（頭・くちばし・目だけ、全身は不採用）で作っていた。
形としては48pxでも「鳥の顔」と判別できるところまで詰められたが、**種を1つに固定する時点で
このチャンネルの設計と合わない**と判断し、方向を変えた。単純な塊に絞り込む・小サイズで検証する、
という工程自体はそのまま今回に引き継いでいる。
