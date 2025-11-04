import requests

ACCESS_TOKEN = "linkedin_access_token"
ORG_ID = "urn:li:organization:123456789"

headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({ORG_ID})"
res = requests.get(url, headers=headers)
posts = res.json()["elements"]

news = []
for p in posts:
    content = p["specificContent"]["com.linkedin.ugc.ShareContent"]
    text = content["shareCommentary"]["text"]
    image = ""
    if "media" in content:
        image = content["media"][0].get("originalUrl", "")
    news.append({
        "text": text,
        "image": image,
        "date": p["created"]["time"]
    })

print(news)
