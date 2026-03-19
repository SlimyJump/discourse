import ssl
from urllib.request import Request, urlopen

import feedparser

YOUTUBE_FEED_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCXIJgqnII2ZOINSWNOGFThA"
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


def print_top_results(feed_url: str, limit: int = 10) -> None:
    feed = parse_feed(feed_url)
    print(f"length of feed results {len(feed.entries)}")
    if len(feed.entries) == 0:
        http_info = getattr(feed, "_http_info", {})
        print(f"http status: {http_info.get('status')}")
        print(f"content type: {http_info.get('content_type')}")
        print(f"bytes read: {getattr(feed, '_content_length', 0)}")
        if getattr(feed, "bozo", 0):
            print(f"parse error: {getattr(feed, 'bozo_exception', None)}")

    for idx, item in enumerate(top_results(feed, limit), start=1):
        print(f"{idx}. {item['title']}")
        print(f"   description: {item['description']}")
        print(f"   video_id: {item['video_id']}")


print_top_results(YOUTUBE_FEED_URL, limit=10)


############# GET TRANSCRIPT

# from youtube_transcript_api import YouTubeTranscriptApi

# ytt_api = YouTubeTranscriptApi()

# #### rick roll
# #### transcript = ytt_api.fetch("dQw4w9WgXcQ")
# transcript = ytt_api.fetch("o-He1C-fU-s")

# for entry in transcript[:5]:
#     print(entry.text)
