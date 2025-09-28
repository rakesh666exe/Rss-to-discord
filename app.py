import praw
import requests
import os
import json
import time

# ----------- CONFIGURE HERE -------------
reddit = praw.Reddit(
    client_id='ID',
    client_secret='SECRETCODE,
    username='REDDITNAME',
    password='ACCOUNTPASS',
    user_agent='discordwebhookbot'
)
WEBHOOK_URL = "WEBURL" # store your webhook in GitHub Secrets
SUBREDDIT = "SUBNAME"
POSTED_FILE = "posted.json"  # file to remember posted submissions

# Load already posted posts
if os.path.exists(POSTED_FILE):
    with open(POSTED_FILE, "r") as f:
        posted_posts = set(json.load(f))
else:
    posted_posts = set()


def post_to_discord(title, author, image, body, url, upvotes, comments, subreddit):
    embed = {
        "title": f"{title}",
        "url": url,
        "description": f"""**👤 Author:** [u/{author}](https://reddit.com/user/{author})

{body if body else '*No content*'}""",
        "color": 0xdf691a,
        "footer": {
            "text": f"⬆️ {upvotes} | 💬 {comments} | r/{subreddit}",
            "icon_url": "https://upload.wikimedia.org/wikipedia/en/thumb/b/bd/Reddit_Logo_Icon.svg/250px-Reddit_Logo_Icon.svg.png"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    if image and image.startswith("http"):
        embed["image"] = {"url": image}
    data = {"embeds": [embed]}
    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code != 204:
        print(f"Failed to send webhook: {response.status_code} {response.text}")


def get_best_image(submission):
    if submission.url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".gifv")):
        return submission.url
    if getattr(submission, "preview", None) and "images" in submission.preview:
        preview_url = submission.preview["images"][0]["source"]["url"]
        return preview_url.replace("&amp;", "&")
    return None


def main():
    subreddit_obj = reddit.subreddit(SUBREDDIT)
    new_posts = []

    # Collect posts that haven't been posted yet
    for submission in subreddit_obj.new(limit=100):
        if submission.id not in posted_posts:
            new_posts.append(submission)

    # Post in **reverse order** (oldest first)
    for submission in reversed(new_posts):
        image_url = get_best_image(submission)
        author_name = submission.author.name if submission.author else "unknown"
        post_to_discord(
            title=submission.title,
            author=author_name,
            image=image_url,
            body=submission.selftext[:2048],
            url="https://reddit.com" + submission.permalink,
            upvotes=submission.score,
            comments=submission.num_comments,
            subreddit=SUBREDDIT
        )
        posted_posts.add(submission.id)

    # Save updated posted posts
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted_posts), f)


if __name__ == "__main__":
    main()
