#!/usr/bin/env python3
"""YouTube Data API / Analytics API 用のOAuth認証（デバイスフロー）。

使い方:
    python3 tools/youtube_auth.py

このスクリプトを実行すると、認証用のURLとコードが表示される。
それをスマホ/PCのブラウザで開いてコードを入力し、Googleアカウントで
チャンネルへのアクセスを許可すると、このスクリプトが自動でリフレッシュ
トークンを取得して secrets/youtube_token.json に保存する。

secrets/ 以下は .gitignore で除外されており、リポジトリにはコミットされない。
一度認証すれば、以後は tools/youtube_report.py がこのトークンを使って
再認証なしにAPIを呼び出せる（リフレッシュトークンは長期間有効）。
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
SECRETS_DIR = HERE.parent / "secrets"
CLIENT_SECRET_PATH = SECRETS_DIR / "youtube_client_secret.json"
TOKEN_PATH = SECRETS_DIR / "youtube_token.json"

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# 動画の統計情報（YouTube Data API）を読み取り専用で使う。
# 【重要】yt-analytics.readonly（YouTube Analytics API）はGoogle側の制限で
# デバイスフローでは使えない（invalid_scopeで拒否される）。視聴維持率・
# トラフィックソース等が必要な場合は、別途「ウェブアプリケーション」型の
# OAuthクライアント＋OAuth Playgroundでリフレッシュトークンを取得する
# 方式が必要（tools/README_youtube_analytics.md 参照）。
SCOPES = "https://www.googleapis.com/auth/youtube.readonly"


def load_client():
    if not CLIENT_SECRET_PATH.exists():
        sys.exit(f"見つかりません: {CLIENT_SECRET_PATH}\n"
                  "先にGoogle CloudでOAuthクライアントID（TVとその他の入力制限のある"
                  "デバイス）を作成し、client_id / client_secret をこのファイルに保存してください。")
    return json.loads(CLIENT_SECRET_PATH.read_text())


def post_form(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def request_device_code(client_id):
    return post_form(DEVICE_CODE_URL, {"client_id": client_id, "scope": SCOPES})


def poll_for_token(client_id, client_secret, device_code, interval):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }
    while True:
        time.sleep(interval)
        try:
            return post_form(TOKEN_URL, data)
        except urllib.error.HTTPError as e:
            payload = json.loads(e.read())
            err = payload.get("error")
            if err == "authorization_pending":
                continue
            if err == "slow_down":
                interval += 2
                continue
            raise RuntimeError(f"認証に失敗しました: {payload}")


def main():
    client = load_client()
    client_id = client["client_id"]
    client_secret = client["client_secret"]

    device = request_device_code(client_id)
    print("\n以下のURLをスマホかPCのブラウザで開いて、コードを入力してください。\n")
    print(f"  URL : {device['verification_url']}")
    print(f"  コード: {device['user_code']}\n")
    print("入力して許可すると、このまま自動で認証が完了します…")

    token = poll_for_token(client_id, client_secret, device["device_code"],
                            device.get("interval", 5))

    if "refresh_token" not in token:
        sys.exit(f"refresh_tokenが取得できませんでした: {token}")

    SECRETS_DIR.mkdir(exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token, indent=2, ensure_ascii=False))
    print(f"\n認証完了。トークンを保存しました: {TOKEN_PATH}")
    print("以後は tools/youtube_report.py がこのトークンを使って自動でデータ取得します。")


if __name__ == "__main__":
    main()
