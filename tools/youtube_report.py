#!/usr/bin/env python3
"""YouTube Data API で、自分のチャンネルの動画一覧と統計を取得する。

使い方:
    python3 tools/youtube_report.py

事前に tools/youtube_auth.py で secrets/youtube_token.json を作成しておくこと。
リフレッシュトークンで毎回アクセストークンを取り直すため、再認証は不要。

取得できるのは YouTube Data API の範囲（動画ごとの累計 視聴回数・高評価数・
コメント数、公開日、タイトルなど）。視聴維持率・トラフィックソース・
登録者増などは YouTube Analytics API が必要で別方式（README参照）。
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
SECRETS_DIR = HERE.parent / "secrets"
CLIENT_SECRET_PATH = SECRETS_DIR / "youtube_client_secret.json"
TOKEN_PATH = SECRETS_DIR / "youtube_token.json"

TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/youtube/v3"


def get_access_token():
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
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def api_get(access_token, path, params):
    url = f"{API_BASE}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_my_channel(access_token):
    data = api_get(access_token, "channels", {
        "part": "snippet,statistics,contentDetails",
        "mine": "true",
    })
    return data["items"][0]


def get_uploads(access_token, uploads_playlist_id):
    """アップロード済み動画をすべて（新しい順）取得する。"""
    videos = []
    page_token = None
    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = api_get(access_token, "playlistItems", params)
        videos.extend(data["items"])
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return videos

def get_video_stats(access_token, video_ids):
    """videoId -> statistics のマップ。50件ずつまとめて取得。"""
    stats = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        data = api_get(access_token, "videos", {
            "part": "statistics,contentDetails,snippet",
            "id": ",".join(batch),
        })
        for item in data["items"]:
            stats[item["id"]] = item
    return stats


def main():
    if not TOKEN_PATH.exists():
        sys.exit("先に python3 tools/youtube_auth.py で認証してください。")

    access_token = get_access_token()
    channel = get_my_channel(access_token)

    print(f"チャンネル: {channel['snippet']['title']}")
    print(f"登録者数  : {channel['statistics'].get('subscriberCount', '非公開')}")
    print(f"総視聴回数: {channel['statistics']['viewCount']}")
    print(f"総動画数  : {channel['statistics']['videoCount']}\n")

    uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    uploads = get_uploads(access_token, uploads_id)
    video_ids = [v["contentDetails"]["videoId"] for v in uploads]
    stats = get_video_stats(access_token, video_ids)

    print(f"{'公開日':10}  {'視聴回数':>8}  {'高評価':>6}  {'コメント':>6}  タイトル")
    rows = []
    for v in uploads:
        vid = v["contentDetails"]["videoId"]
        s = stats.get(vid, {}).get("statistics", {})
        published = v["snippet"]["publishedAt"][:10]
        title = v["snippet"]["title"]
        rows.append((published, vid, title,
                      int(s.get("viewCount", 0)),
                      int(s.get("likeCount", 0)),
                      int(s.get("commentCount", 0))))

    rows.sort(key=lambda r: r[0])
    for published, vid, title, views, likes, comments in rows:
        print(f"{published}  {views:8}  {likes:6}  {comments:6}  {title}")

    out = HERE.parent / "docs" / "_youtube_stats_raw.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"\n生データを保存しました: {out}")


if __name__ == "__main__":
    main()
