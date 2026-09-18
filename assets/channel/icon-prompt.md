# チャンネルアイコン 生成プロンプト（ChatGPT用）

Pillowで描いた現行版（[`icon.png`](icon.png)）を、AI画像生成で作り直すためのプロンプト。

**必ず守ってほしい条件は、この2つ。**

1. **正方形（1:1）。** YouTubeのアイコンは正方形でトリミングされる
2. **頭部のクローズアップだけ。全身にしない。** 48px以下（コメント欄・登録者一覧の表示サイズ）に
   縮小したとき、脚や尾があると潰れて黒い塊にしかならないことを、Pillow版で実際に確認済み。
   頭・くちばし・目だけに絞れば、48pxでも「鳥の顔」と判別できる

---

## プロンプト

```
A minimalist YouTube channel icon, square 1:1 format. A close-up, front-three-quarter
view of a crow's head and beak only — no body, no wings, no legs, no perch, no
background scenery. Solid flat dark forest-green background (#1B4332), completely
plain, no gradient, no texture, no vignette. The crow's head is a single smooth
solid black silhouette shape with no internal linework, no feather texture, no
outline stroke. One single round eye rendered as a solid bright yellow dot (#FFD60A)
— this is the only accent color in the whole image. The beak is short and pointed,
angled slightly downward. The silhouette should be bold, chunky, and geometrically
simple enough to still read clearly as "a bird's head with one yellow eye" when
scaled down to 48x48 pixels. Flat vector logo style, no gradients, no shadows, no
3D shading, no realistic feather detail. Centered composition with even margin on
all sides. No text, no letters, no words, no numbers, no logos, no watermark, no
signature anywhere in the image.
```

## 受け取ったあと

1. **48pxと16pxに縮小して、鳥の頭とわかるか確認する。** Pillow版で最初に作った全身シルエットは
   ここで不合格になった（脚と尾が潰れて黒い塊になった）
2. 正方形で出てこなかった場合は中央基準でクロップする
3. `assets/channel/icon.png` を上書きして、`docs/01-channel-concept.md` §7 の記述も
   「Pillowで生成」から「ChatGPTで生成」に直す
