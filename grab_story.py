import time
from pathlib import Path

import feedparser
from newspaper import Article

RSS_FEEDS = {
    "cnn": "https://rss.cnn.com/rss/cnn_topstories.rss",
    "fox": "https://moxie.foxnews.com/google-publisher/latest.xml",
}
MAX_ARTICLES_PER_FEED = 5
OUTPUT_DIR = Path("articles")
OUTPUT_DIR.mkdir(exist_ok=True)


def collect_urls(feeds: dict[str, str], per_feed: int) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    seen: set[str] = set()
    for source, feed_url in feeds.items():
        feed = feedparser.parse(feed_url)
        count = 0
        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in seen:
                continue
            seen.add(link)
            urls.append((source, link))
            count += 1
            if count >= per_feed:
                break
    return urls


def fetch_article(url: str) -> Article | None:
    article = Article(url)
    try:
        article.download()
        article.parse()
    except Exception as exc:
        print(f"failed to fetch {url}: {exc}")
        return None
    return article


def slugify(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in (" ", "-", "_") else "" for ch in text)
    return "-".join(cleaned.lower().split())[:80] or "article"


URLS = collect_urls(RSS_FEEDS, MAX_ARTICLES_PER_FEED)

for source, url in URLS:
    time.sleep(10)
    article = fetch_article(url)
    if not article or not article.text:
        continue

    filename = f"{source}_{slugify(article.title)}.txt"
    path = OUTPUT_DIR / filename
    path.write_text(f"{article.title}\n\n{article.text}", encoding="utf-8")
