import feedparser
import json

feeds = {
    "cnn": "http://rss.cnn.com/rss/cnn_topstories.rss",
    "fox": "http://feeds.foxnews.com/foxnews/latest"
}

all_articles = []

for source, url in feeds.items():
    feed = feedparser.parse(url)

    for entry in feed.entries:
        article = {
            "source": source,
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", "")
        }
        all_articles.append(article)

# Save to file
with open("news.json", "w") as f:
    json.dump(all_articles, f, indent=2)

print(f"Saved {len(all_articles)} articles")