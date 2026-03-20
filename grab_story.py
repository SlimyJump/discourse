import requests
import feedparser
import certifi
import json

feeds = {
    "cnn": "http://rss.cnn.com/rss/cnn_topstories.rss",
    "fox": "http://feeds.foxnews.com/foxnews/latest"
}

all_articles = []

for source, url in feeds.items():

    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        verify=certifi.where()
    )

    feed = feedparser.parse(response.content)


    print("Bozo:", feed.bozo)
    print("Entries:", len(feed.entries))

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