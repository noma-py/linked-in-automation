import os
import json
import requests
from github import Github
from datetime import datetime
from dotenv import load_dotenv

# ladda env variabler api nycklar etc
load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
ORG_URN = os.getenv("LINKEDIN_ORG_URN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# === steg 1: Hämta inlägg från LinkedIn ===
def fetch_linkedin_posts():
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({ORG_URN})"
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    data = res.json()
    posts = []

    for p in data.get("elements", []):
        content = p.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
        text = content.get("shareCommentary", {}).get("text", "")
        media_url = ""
        if "media" in content and content["media"]:
            media_url = content["media"][0].get("originalUrl", "")

        post = {
            "text": text.strip(),
            "image": media_url,
            "created": datetime.utcfromtimestamp(
                p["created"]["time"] / 1000
            ).strftime("%Y-%m-%d"),
            "link": f"https://www.linkedin.com/feed/update/{p['id'].split(':')[-1]}"
        }
        posts.append(post)

    return posts


# === steg 2: Spara som JSON ===
def save_json(posts, filename="news.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    print(f"Sparade {len(posts)} poster till {filename}")


# === steg 3: Ladda upp till GitHub ===
def upload_to_github(filepath):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        file = repo.get_contents("news.json")
        repo.update_file(file.path, "Update news.json", content, file.sha, branch="main")
        print("news.json uppdaterad på GitHub")
    except Exception:
        repo.create_file("news.json", "Create news.json", content, branch="main")
        print("news.json skapad på GitHub")


if __name__ == "__main__":
    posts = fetch_linkedin_posts()
    save_json(posts)
    upload_to_github("news.json")
