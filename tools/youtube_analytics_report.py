#!/usr/bin/env python3
"""YouTube Analytics API で、動画ごとの視聴維持率・登録者増などを取得する。

使い方:
    python3 tools/youtube_analytics_report.py

事前に、secrets/youtube_analytics_client_secret.json と
secrets/youtube_analytics_token.json が必要（OAuth Playground経由で取得。
tools/README_youtube_analytics.md 参照）。

【注意】OAuth同意画面が「テスト」ステータスの間、refresh_tokenは発行から
7日で失効する。失効したらOAuth Playgroundで再発行し、
secrets/youtube_analytics_token.json を上書きすること。

tools/youtube_report.py（YouTube Data API、累計の視聴回数・高評価・
コメント）と役割が異なる。こちらは期間集計の視聴維持率・登録者増・
トラフィックソースなど、Data APIでは取れない指標を取得する。
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

HERE = pathlib.Path(__file__).parent
SECRETS_DIR = HERE.parent / "secrets"
CLIENT_SECRET_PATH = SECRETS_DIR / "youtube_analytics_client_secret.json"
TOKEN_PATH = SECRETS_DIR / "youtube_analytics_token.json"

TOKEN_URL = "https://oauth2.googleapis.com/token"
ANALYTICS_API = "https://youtubeanalytics.googleapis.com/v2/reports"
DATA_API = "https://www.googleapis.com/youtube/v3"


def get_access_token():
    if not CLIENT_SECRET_PATH.exists() or not TOKEN_PATH.exists():
        sys.exit("secrets/youtube_analytics_client_secret.json / "
                  "youtube_analytics_token.json が見つかりません。"
                  "OAuth Playgroundで取得してください。")
    client = json.loads(CLIENT_SECRET_PATH.read_text())
    token = json.loads(TOKEN_PATH.read_text())
    data = urllib.parse.urlencode({
        "client_id": client["client_id"],
        "client_secret": client["client_secret"],
        "refresh_token": token["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST",
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["access_token"]
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        if body.get("error") == "invalid_grant":
            sys.exit("refresh_tokenが失効しています（テストステータスは7日で失効）。"
                      "OAuth Playgroundで再発行し、"
                      "secrets/youtube_analytics_token.json を更新してください。")
        raise


def api_get(access_token, base, path, params):
    url = f"{base}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_channel_id_start_date_and_titles():
    """チャンネルID・最初の動画の公開日・videoId->タイトル を取る。

    このAnalytics専用トークン（yt-analytics.readonlyのみ）では
    Data APIの mine=true 系エンドポイントが403になるため、
    tools/youtube_auth.py で取得済みの youtube.readonly トークン
    （tools/youtube_report.py）を使い回す。
    """
    sys.path.insert(0, str(HERE))
    from youtube_report import (
        get_access_token as get_data_api_token,
        get_my_channel,
        get_uploads,
    )
    data_token = get_data_api_token()
    channel = get_my_channel(data_token)
    uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    uploads = get_uploads(data_token, uploads_id)

    dates = [v["snippet"]["publishedAt"][:10] for v in uploads]
    titles = {v["contentDetails"]["videoId"]: v["snippet"]["title"] for v in uploads}
    start_date = min(dates) if dates else str(date.today())
    return channel["id"], start_date, titles


def get_per_video_report(access_token, channel_id, start_date, end_date):
    return api_get(access_token, ANALYTICS_API, "", {
        "ids": f"channel=={channel_id}",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": "views,averageViewPercentage,averageViewDuration,subscribersGained,likes,comments",
        "dimensions": "video",
        "sort": "-views",
        "maxResults": 200,
    })


def main():
    access_token = get_access_token()
    channel_id, start_date, titles = get_channel_id_start_date_and_titles()
    end_date = str(date.today())

    report = get_per_video_report(access_token, channel_id, start_date, end_date)
    headers = report["columnHeaders"]
    col = {h["name"]: i for i, h in enumerate(headers)}

    print(f"集計期間: {start_date} 〜 {end_date}\n")
    print(f"{'視聴回数':>6}  {'平均視聴維持率':>8}  {'登録者増':>6}  {'高評価':>5}  {'コメント':>5}  タイトル")
    rows = []
    for row in report.get("rows", []):
        vid = row[col["video"]]
        title = titles.get(vid, vid)
        views = row[col["views"]]
        avg_pct = row[col["averageViewPercentage"]]
        subs = row[col["subscribersGained"]]
        likes = row[col["likes"]]
        comments = row[col["comments"]]
        rows.append((vid, title, views, avg_pct, subs, likes, comments))
        print(f"{views:6}  {avg_pct:13.1f}%  {subs:6}  {likes:5}  {comments:5}  {title}")

    out = HERE.parent / "docs" / "_youtube_analytics_raw.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"\n生データを保存しました: {out}")


if __name__ == "__main__":
    main()
