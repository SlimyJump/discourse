import ssl
from pathlib import Path
from urllib.request import Request, urlopen

import feedparser
from youtube_transcript_api import YouTubeTranscriptApi

YOUTUBE_SEARCH_QUERY_A = "california fox news"
YOUTUBE_SEARCH_QUERY_B = "california cnn"
CHANNEL_NAME_A = "Fox News"
CHANNEL_NAME_B = "CNN"
SEARCH_PAGE_LIMIT = 6
DISCOURSE_DIR = Path("discourse")
DISCOURSE_DIR.mkdir(exist_ok=True)


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


def has_transcript(video_id: str) -> bool:
    try:
        YouTubeTranscriptApi.list_transcripts(video_id)
        return True
    except Exception:
        return False


def extract_channel_name(entry: feedparser.FeedParserDict) -> str:
    author = entry.get("author") or entry.get("author_detail", {}).get("name", "")
    return str(author).strip()


def make_search_url(query: str) -> str:
    normalized = "+".join(query.strip().split())
    return f"https://www.youtube.com/feeds/videos.xml?search_query={normalized}"


def get_next_link(feed: feedparser.FeedParserDict) -> str:
    for link in feed.get("feed", {}).get("links", []):
        if link.get("rel") == "next":
            return link.get("href", "")
    return ""


def build_team_list(
    search_query: str,
    channel_name: str,
    limit: int = 10,
    page_limit: int = SEARCH_PAGE_LIMIT,
) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()
    url = make_search_url(search_query)
    pages_fetched = 0

    while url and len(results) < limit and pages_fetched < page_limit:
        feed = parse_feed(url)
        pages_fetched += 1

        if len(feed.entries) == 0:
            http_info = getattr(feed, "_http_info", {})
            print(f"length of feed results {len(feed.entries)}")
            print(f"http status: {http_info.get('status')}")
            print(f"content type: {http_info.get('content_type')}")
            print(f"bytes read: {getattr(feed, '_content_length', 0)}")
            if getattr(feed, "bozo", 0):
                print(f"parse error: {getattr(feed, 'bozo_exception', None)}")
            break

        for entry in feed.entries:
            if len(results) >= limit:
                break

            if extract_channel_name(entry) != channel_name:
                continue

            video_id = extract_video_id(entry)
            if not video_id or video_id in seen_ids:
                continue

            if not has_transcript(video_id):
                continue

            seen_ids.add(video_id)
            results.append(
                (
                    entry.get("title", "").strip(),
                    entry.get("summary", entry.get("description", "")).strip(),
                    video_id,
                )
            )

        url = get_next_link(feed)

    return results


Team_A_List = build_team_list(
    YOUTUBE_SEARCH_QUERY_A, CHANNEL_NAME_A, limit=10, page_limit=SEARCH_PAGE_LIMIT
)
Team_B_List = build_team_list(
    YOUTUBE_SEARCH_QUERY_B, CHANNEL_NAME_B, limit=10, page_limit=SEARCH_PAGE_LIMIT
)


print(f"  Team_A_List len  {len(Team_A_List)}")
print(f"  Team_B_List len  {len(Team_B_List)}")

for _title, _description, video_id in Team_A_List:
 

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
        (DISCOURSE_DIR / filename).write_text(transcript_text, encoding="utf-8")


save_transcript_files("team_a_", team_a_list)
save_transcript_files("team_b_", team_b_list)
