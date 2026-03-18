from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()

#### rick roll
#### transcript = ytt_api.fetch("dQw4w9WgXcQ")
transcript = ytt_api.fetch("o-He1C-fU-s")

for entry in transcript[:5]:
    print(entry.text)