import feedparser

feed = feedparser.parse(
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCXIJgqnII2ZOINSWNOGFThA"
)

print(f' length of feed results  {len(feed.entries)}')

video_ids = [entry.yt_videoid for entry in feed.entries[:10]]

print(video_ids)


############# GET TRANSCRIPT

# from youtube_transcript_api import YouTubeTranscriptApi

# ytt_api = YouTubeTranscriptApi()

# #### rick roll
# #### transcript = ytt_api.fetch("dQw4w9WgXcQ")
# transcript = ytt_api.fetch("o-He1C-fU-s")

# for entry in transcript[:5]:
#     print(entry.text)