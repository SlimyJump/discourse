import ssl
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi

YOUTUBE_FEED_URL_A = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCXIJgqnII2ZOINSWNOGFThA"
)
YOUTUBE_FEED_URL_B = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCupvZG-5ko_eiXAupbDfxWw"
)


def fetch_feed_bytes(url: str) -> tuple[bytes, dict]:
    context = build_ssl_context()
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=15, context=context) as response:
        content = response.read()
        info = {
            "status": getattr(response, "status", None),
            "content_type": response.headers.get("Content-Type", ""),
        }
    return content, info


def build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def parse_feed(url: str) -> feedparser.FeedParserDict:
    content, info = fetch_feed_bytes(url)
    feed = feedparser.parse(content)
    feed._http_info = info
    feed._content_length = len(content)
    return feed


def extract_video_id(entry: feedparser.FeedParserDict) -> str:
    video_id = entry.get("yt_videoid")
    if video_id:
        return video_id

    link = entry.get("link", "")
    if "watch?v=" in link:
        return link.split("watch?v=", 1)[1].split("&", 1)[0]

    return ""


def top_results(feed: feedparser.FeedParserDict, limit: int = 10) -> list[dict]:
    results: list[dict] = []
    for entry in feed.entries[:limit]:
        results.append(
            {
                "title": entry.get("title", "").strip(),
                "description": entry.get("summary", entry.get("description", "")).strip(),
                "video_id": extract_video_id(entry),
            }
        )
    return results


def build_team_list(feed_url: str, limit: int = 10) -> list[tuple[str, str, str]]:
    feed = parse_feed(feed_url)
    if len(feed.entries) == 0:
        http_info = getattr(feed, "_http_info", {})
        print(f"length of feed results {len(feed.entries)}")
        print(f"http status: {http_info.get('status')}")
        print(f"content type: {http_info.get('content_type')}")
        print(f"bytes read: {getattr(feed, '_content_length', 0)}")
        if getattr(feed, "bozo", 0):
            print(f"parse error: {getattr(feed, 'bozo_exception', None)}")

    results = top_results(feed, limit)
    return [(item["title"], item["description"], item["video_id"]) for item in results]


Team_A_List = build_team_list(YOUTUBE_FEED_URL_A, limit=10)
Team_B_List = build_team_list(YOUTUBE_FEED_URL_B, limit=10)


print(f"  Team_A_List len  {len(Team_A_List)}")
print(f"  Team_B_List len  {len(Team_B_List)}")

exit()

############# GET TRANSCRIPT

team_a_list = Team_A_List
team_b_list = Team_B_List


def fetch_transcript_text(video_id: str) -> str | None:
    if not video_id:
        return None
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
    except Exception as exc:
        print(f"transcript fetch failed for {video_id}: {exc}")
        return None

    return "\n".join(entry.text for entry in transcript)


def save_transcript_files(prefix: str, items: list[tuple[str, str, str]]) -> None:
    for _title, _description, video_id in items:
        transcript_text = fetch_transcript_text(video_id)
        if not transcript_text:
            continue

        filename = f"{prefix}{video_id}.txt"
        Path(filename).write_text(transcript_text, encoding="utf-8")


save_transcript_files("team_a_", team_a_list)
save_transcript_files("team_b_", team_b_list)
