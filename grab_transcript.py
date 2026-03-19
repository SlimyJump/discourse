import ssl
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi
from youtubesearchpython import VideosSearch

YOUTUBE_SEARCH_QUERY_A = "california fox news"
YOUTUBE_SEARCH_QUERY_B = "california cnn"
CHANNEL_ID_A = "UCXIJgqnII2ZOINSWNOGFThA"
CHANNEL_ID_B = "UCupvZG-5ko_eiXAupbDfxWw"
CHANNEL_NAME_A = "Fox News"
CHANNEL_NAME_B = "CNN"
DISCOURSE_DIR = Path("discourse")
DISCOURSE_DIR.mkdir(exist_ok=True)


def has_transcript(video_id: str) -> bool:
    try:
        YouTubeTranscriptApi.list_transcripts(video_id)
        return True
    except Exception:
        return False


def normalize_description(item: dict) -> str:
    snippet = item.get("descriptionSnippet")
    if isinstance(snippet, list):
        return " ".join(part.get("text", "") for part in snippet).strip()
    return str(item.get("description", "")).strip()


def extract_channel_id(item: dict) -> str:
    channel = item.get("channel")
    if isinstance(channel, dict):
        return str(channel.get("id", "")).strip()
    if isinstance(channel, list) and channel:
        return str(channel[0].get("id", "")).strip()
    return str(item.get("channelId", "")).strip()


def extract_channel_name(item: dict) -> str:
    channel = item.get("channel")
    if isinstance(channel, dict):
        return str(channel.get("name", "")).strip()
    if isinstance(channel, list) and channel:
        return str(channel[0].get("name", "")).strip()
    return str(item.get("channelName", "")).strip()


def is_expected_channel(
    item: dict,
    channel_id: str,
    channel_name: str,
) -> bool:
    extracted_id = extract_channel_id(item)
    if extracted_id and channel_id and extracted_id == channel_id:
        return True

    extracted_name = extract_channel_name(item)
    if extracted_name and channel_name:
        return extracted_name.casefold() == channel_name.casefold()

    return False


def ensure_httpx_compatible() -> None:
    try:
        import httpx
    except Exception:
        return

    version = getattr(httpx, "__version__", "")
    digits = []
    for part in version.split("."):
        try:
            digits.append(int(part))
        except ValueError:
            break
    major_minor = tuple(digits[:2]) if digits else (0, 0)
    if major_minor >= (0, 28):
        raise RuntimeError(
            "youtube-search-python requires httpx<0.28. "
            "Install a compatible version: python -m pip install \"httpx<0.28\""
        )


def youtube_search_python_search(
    query: str,
    channel_id: str,
    channel_name: str,
    limit: int,
    page_limit: int = 8,
) -> list[tuple[str, str, str]]:
    ensure_httpx_compatible()
    results: list[tuple[str, str, str]] = []
    seen_ids: set[str] = set()
    search = VideosSearch(query, limit=50)
    pages_fetched = 0
    total_items = 0
    channel_matches = 0
    transcript_matches = 0

    while len(results) < limit and pages_fetched < page_limit:
        data = search.result()
        page_items = data.get("result", [])
        total_items += len(page_items)
        for item in page_items:
            if len(results) >= limit:
                break

            if not is_expected_channel(item, channel_id, channel_name):
                continue
            channel_matches += 1

            video_id = item.get("id", "")
            if not video_id or video_id in seen_ids:
                continue

            if not has_transcript(video_id):
                continue
            transcript_matches += 1

            seen_ids.add(video_id)
            results.append(
                (
                    str(item.get("title", "")).strip(),
                    normalize_description(item),
                    video_id,
                )
            )

        pages_fetched += 1
        if len(results) < limit and data.get("result"):
            search.next()
        else:
            break

    if not results:
        print(
            "youtube-search-python debug: "
            f"total_items={total_items} "
            f"channel_matches={channel_matches} "
            f"transcript_matches={transcript_matches}"
        )
        sample = (data.get("result") or [])[:3]
        for idx, item in enumerate(sample, start=1):
            print(f"sample {idx} id={item.get('id')} title={item.get('title')!r}")
            print(f"  channel={item.get('channel')}")
            print(
                "  channelId="
                f"{item.get('channelId')} channelName={item.get('channelName')}"
            )

    return results


def build_team_list(
    search_query: str,
    channel_id: str,
    channel_name: str,
    limit: int = 10,
) -> list[tuple[str, str, str]]:
    print("Using youtube-search-python.")
    return youtube_search_python_search(search_query, channel_id, channel_name, limit)


Team_A_List = build_team_list(
    YOUTUBE_SEARCH_QUERY_A, CHANNEL_ID_A, CHANNEL_NAME_A, limit=10
)
Team_B_List = build_team_list(
    YOUTUBE_SEARCH_QUERY_B, CHANNEL_ID_B, CHANNEL_NAME_B, limit=10
)


print(f"  Team_A_List len  {len(Team_A_List)}")
print(f"  Team_B_List len  {len(Team_B_List)}")

# for _title, _description, video_id in Team_A_List:
 

############# GET TRANSCRIPT

team_a_list = Team_A_List
team_b_list = Team_B_List


def fetch_transcript_text(video_id: str) -> str | None:
    if not video_id:
        return None
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
    except Exception as exc:
        # print(f"transcript fetch failed for {video_id}: {exc}")
        print(f"transcript fetch failed for {video_id}")
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
