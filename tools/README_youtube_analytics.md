# YouTube 実データ取得の仕組み（vidIQを使わない方法）

vidIQのクレジット制限を避けるため、YouTube Data API / Analytics API に
直接OAuth認証して実データを取得している。**2種類のOAuthクライアントが要る**
（片方だけでは全部の指標は取れない）。

## クライアント①: Data API用（デバイスフロー）

累計の**視聴回数・高評価数・コメント数**（`tools/youtube_report.py`）を取る。

- Google Cloudで種類「**TVとその他の入力制限のあるデバイス**」のOAuth
  クライアントを作成
- `secrets/youtube_client_secret.json` に `client_id` / `client_secret` を保存
- `python3 tools/youtube_auth.py` を実行 → 表示されるURL・コードをスマホ等で
  開いて許可 → `secrets/youtube_token.json` にリフレッシュトークンが保存される
- **このリフレッシュトークンは長期間有効**（毎回の再認証は不要）
- 実行: `python3 tools/youtube_report.py`

## クライアント②: Analytics API用（OAuth Playground経由）

期間集計の**視聴維持率・登録者増・トラフィックソース**など
（`tools/youtube_analytics_report.py`）を取る。

`yt-analytics.readonly` スコープはGoogle側の制限で**デバイスフローが
使えない**（`invalid_scope`エラー）。そのため別のOAuthクライアントと
OAuth Playgroundを使う。

1. Google Cloudで種類「**ウェブ アプリケーション**」のOAuthクライアントを
   別途作成。承認済みリダイレクトURIに
   `https://developers.google.com/oauthplayground` を登録
2. `secrets/youtube_analytics_client_secret.json` に `client_id` /
   `client_secret` / `redirect_uri` を保存
3. https://developers.google.com/oauthplayground/ を開く
4. 右上の歯車→「Use your own OAuth credentials」にチェックし①のIDとシークレットを入力
5. 左のリストから **YouTube Analytics API v2** →
   `https://www.googleapis.com/auth/yt-analytics.readonly` を選択
6. 「Authorize APIs」→チャンネルを持つGoogleアカウントで許可
7. 「Exchange authorization code for tokens」→表示された **Refresh token** を
   `secrets/youtube_analytics_token.json` の `refresh_token` に保存
8. 実行: `python3 tools/youtube_analytics_report.py`

### 【重要】このリフレッシュトークンは7日で失効する

OAuth同意画面が「テスト」ステータスのままだと、②のリフレッシュトークンは
**発行から7日で失効**する（Googleの仕様）。失効すると
`youtube_analytics_report.py` が「refresh_tokenが失効しています」と表示する
ので、その場合は手順3〜7を繰り返して `secrets/youtube_analytics_token.json`
を上書きすること。①（Data API）のトークンはこの制限を受けず長期間使える。

個人利用でこの7日ごとの手間が気になる場合は、OAuth同意画面を「本番」に
公開する方法もあるが、`yt-analytics.readonly` は制限付きスコープのため
Googleの審査が必要になる可能性がある。審査は手間がかかるため、当面は
7日ごとの再認証で運用する。

## secrets/ ディレクトリの中身（すべてgit管理外）

| ファイル | 内容 |
|---|---|
| `youtube_client_secret.json` | クライアント①のID・シークレット |
| `youtube_token.json` | クライアント①のリフレッシュトークン（長期有効） |
| `youtube_analytics_client_secret.json` | クライアント②のID・シークレット |
| `youtube_analytics_token.json` | クライアント②のリフレッシュトークン（7日で失効） |

## データの反映遅延に注意

YouTube Analytics APIには1〜2日のデータ反映遅延がある。投稿から日が浅い
動画は `youtube_analytics_report.py` のレポートにまだ出てこないことがある
（`youtube_report.py` の累計視聴回数・高評価数は反映が速い）。
