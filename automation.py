import os
import json
import requests
from github import Github
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ladda env variabler api nycklar etc
load_dotenv()

ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
ORG_URN = os.getenv("LINKEDIN_ORG_URN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
OPEN_AI_KEY= os.getenv("OPENAI_KEY")

client=OpenAI(OPEN_AI_KEY)

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
        rewriten_text=client.responses.create(
            model="gpt-5",
            input=f"""
                    Prompt to Re-Write LinkedIn → News

                    We are working with event and company communication.
                    The workflow is:
                    We first publish LinkedIn posts (forward-looking, engaging, call-to-action, e.g. “Meet us at…” or “We are excited to announce…”).
                    Then we need to re-write them into retroactive news entries for our website/press section.

                    Your task:
                    Take the LinkedIn post provided below and re-write it into a news entry.

                    Rules for the re-write:
                    - Tone shift:
                    LinkedIn → future-facing, promotional.
                    News → past-facing, factual, professional, reflective.
                    - Verb tense:
                    Change “We will be…” / “We are excited to announce…” → “We were…” / “Eneryield participated in…”.
                    - Content focus:
                    LinkedIn highlights invitation and call-to-action.
                    News highlights recap of participation, event focus, and what Eneryield did.
                    - Structure:
                    Headline: “Eneryield at [Event Name]” or “Eneryield participated in…”
                    First paragraph: Mention event name, location, dates, theme.
                    Second paragraph: What Eneryield did (exhibited, sponsored, spoke, etc.).
                    Optional detail: Session topics, solution showcased, key partners.
                    Closing: One professional CTA if relevant (“Contact us to learn more…”).
                    - Branding: Always write Eneryield IntelliView® with the ® symbol.
                    - Consistency: Keep style clean, professional, and suitable for a company news page.
                    - Follow Eneryield’s writing principles: precise technical language, no intensifiers like “very”, use “degradation” instead of “breakdowns”, and refer to the product as Eneryield IntelliView®.

                    Example Transformation:
                    LinkedIn post:
                    ⭐ Exciting Silver Sponsor Announcement!
                    We are proud to welcome Eneryield as the Silver Sponsor of the Global Outage Management Forum for DSOs!

                    News re-write:
                    Eneryield Silver Sponsor at the Global Outage Management Forum
                    Eneryield participated as a Silver Sponsor at the 10th Annual Global Outage Management Forum for DSOs, held in Berlin on April 3–4, 2025. The event brought together industry leaders to discuss innovations in outage management, grid reliability, and digital transformation.
                    As a sponsor, Eneryield supported discussions on shaping the future of reliable power distribution and presented its AI Fault Prediction and Analytics solution.

                    Now re-write the following LinkedIn post into a professional news entry according to these rules:

                    {text}
                    """,
            instructions="""
                    You are an assistant that rewrites LinkedIn posts into professional company news entries for Eneryield, following the company’s communication standards and tone.

                    Your purpose:
                    Transform forward-looking, engaging LinkedIn posts into factual, reflective, and professional news articles suitable for Eneryield’s website or press section.
                    """
        )
        media_url = ""
        if "media" in content and content["media"]:
            media_url = content["media"][0].get("originalUrl", "")

        post = {
            "text": rewriten_text.output_text.strip(),
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
