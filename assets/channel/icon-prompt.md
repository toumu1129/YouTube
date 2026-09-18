# チャンネルアイコン 生成プロンプト（ChatGPT用）

## 現状（v3・製作中）

v2（純粋な「？」＋黄色い点）は縮小しても判別できたが、**「動物」の要素が一切なく、
トリビアだけしか伝わらない**という指摘を受けた。動物＋雑学の両方が伝わる形に作り直す。

**やり方：別々のパーツを足さない。** 「耳のついた？」のように動物パーツを追加すると、
要素が増えて小サイズでの視認性が落ちる（これはv1のカラス版で確認済みの失敗パターン）。
代わりに、**「？」の形そのものが生き物の体になっている**、1つの形に両方を兼務させる。

具体的には：小さな生き物が、体（首から尻尾）を「？」の形にくねらせてこちらを覗いている。
体のカーブがそのまま「？」のフックになり、丸い頭が「？」の上のふくらみになり、
黄色い目1つが「？」の点の役割を果たす。**遠目には「？」に見え、近くで見ると生き物とわかる。**

種は特定しない（カラス・ネコ・ネズミのどれとも取れる、丸い頭に丸い耳2つの汎用的な生き物）。

## 必ず守ってほしい条件

1. **正方形（1:1）**
2. **全体のシルエットは、大きく見て「？」の形として読めること。** これが崩れると
   v1（カラス全身）と同じ理由で小サイズで潰れる
3. **要素は「体のカーブ＋小さな丸耳2つ＋黄色い目1つ」だけ。** 表情線・毛並み・鼻づらなどの
   細部は入れない。増やすほど48px以下で潰れる
4. 種を特定する描写（くちばし、猫のひげ、特定の毛色パターンなど）は入れない

## プロンプト

```
A minimalist YouTube channel icon, square 1:1 format. A single small generic
creature — not identifiable as any specific species, just a simple round-headed
animal — with its head and long curving neck/body bent into the exact shape of a
large question mark ("?"), as if the animal itself IS the question mark. The
creature is peeking out curiously from the top of the curve. Rendered as one solid
flat black silhouette with no internal linework, no fur texture, no outline stroke.
Two small simple rounded ears sit on top of the head, subtle and small enough not
to break the overall "?" silhouette when viewed from a distance. One single round
eye is rendered as a solid bright yellow circle (#FFD60A) positioned where the head
curls at the top of the question mark — this is the only accent color in the whole
image, and it doubles visually as "the dot of the question mark" when the shape is
viewed as a whole. The body tapers down and curls into the lower hook and tail of
the question mark shape, ending in a small rounded tip (no visible legs, paws, or
feet — just a smooth tapering silhouette like a tail). Solid flat dark forest-green
background (#1B4332), completely plain, no gradient, no texture, no vignette. Flat
vector logo style, no gradients, no drop shadows, no 3D shading. The whole design
must be simple and bold enough that, at a glance, it instantly reads as a question
mark shape, and on closer look reveals the animal (ears + eye). It must remain
legible as both at small sizes, down to 48x48 pixels. No text, no letters, no
words, no numbers, no logos, no watermark, no signature anywhere in the image.
```

## 受け取ったあと

1. まず**目を細めて遠目で見る（または縮小する）。「？」に見えるか。**
2. 次に**48px・16pxに縮小する。** 耳と目が潰れて単なる「？」に戻ってしまうなら、
   それはそれで許容範囲（v2の代わりとして最低限は成立する）。理想は48pxで動物とわかること
3. 種が特定できてしまう見た目（くちばしっぽい、猫っぽい）になっていたら、その旨を伝えて
   「もっと種を特定できない、丸い頭のシルエットにして」と再生成を頼む
4. 良ければ `assets/channel/icon.png` を上書きし、`docs/01-channel-concept.md` §7 を更新する

---

## 記録：これまでの経緯

### v1（不採用）— カラスの頭部クローズアップ
頭・くちばし・目だけのシルエット。48pxでも「鳥の顔」と判別できたが、
**種を1つに固定するとチャンネルの「多様な生き物を扱う」というコンセプトと噛み合わない**ため不採用。

### v2（不採用）— 純粋な「？」＋黄色い点
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
48px・16pxでも「？」と黄色い点は判別できたが、**「動物」の要素が伝わらない**という
指摘を受けて不採用。トリビア（？）は表現できていたが、動物＋雑学の2軸のうち片方が欠けていた。
