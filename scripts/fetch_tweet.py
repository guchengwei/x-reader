#!/usr/bin/env python3
"""
X Tweet Fetcher - Fetch tweets and replies without login
Combines FxTwitter API + Camofox/Nitter + rebrowser-playwright
"""

import json
import re
import sys
import argparse
import urllib.request
import urllib.error
import subprocess
from typing import Optional, Dict, List, Any


def parse_tweet_url(url: str) -> tuple:
    """Extract username and tweet_id from X/Twitter URL."""
    patterns = [
        r'(?:x\.com|twitter\.com)/(\w+)/status/(\d+)',
        r'(?:nitter\.net)/(\w+)/status/(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"Cannot parse tweet URL: {url}")


def fetch_fxtwitter(username: str, tweet_id: str) -> Optional[Dict]:
    """Method 1: FxTwitter API - Get tweet text, stats, quotes."""
    api_url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("code") != 200:
            return None

        tweet = data["tweet"]
        result = {
            "text": tweet.get("text", ""),
            "author": tweet.get("author", {}).get("name", ""),
            "screen_name": tweet.get("author", {}).get("screen_name", ""),
            "likes": tweet.get("likes", 0),
            "retweets": tweet.get("retweets", 0),
            "bookmarks": tweet.get("bookmarks", 0),
            "views": tweet.get("views", 0),
            "replies_count": tweet.get("replies", 0),
            "created_at": tweet.get("created_at", ""),
            "is_note_tweet": tweet.get("is_note_tweet", False),
            "lang": tweet.get("lang", ""),
        }

        # Include quote tweet if present
        if tweet.get("quote"):
            qt = tweet["quote"]
            result["quote"] = {
                "text": qt.get("text", ""),
                "author": qt.get("author", {}).get("name", ""),
                "screen_name": qt.get("author", {}).get("screen_name", ""),
                "likes": qt.get("likes", 0),
                "retweets": qt.get("retweets", 0),
                "views": qt.get("views", 0),
            }

        return result
    except Exception as e:
        print(f"[FxTwitter] Error: {e}", file=sys.stderr)
        return None


def fetch_nitter_replies(username: str, tweet_id: str, camofox_port: int = 9377) -> Optional[List[Dict]]:
    """Method 2: Camofox + Nitter - Get reply threads."""
    import time

    nitter_url = f"https://nitter.net/{username}/status/{tweet_id}"

    try:
        # Create tab
        create_data = json.dumps({
            "userId": "tweet-fetcher",
            "sessionKey": f"replies-{tweet_id}",
            "url": nitter_url
        }).encode()

        req = urllib.request.Request(
            f"http://localhost:{camofox_port}/tabs",
            data=create_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            tab_data = json.loads(resp.read().decode())

        tab_id = tab_data.get("tabId")
        if not tab_id:
            return None

        # Wait for page to load
        time.sleep(8)

        # Get snapshot
        snap_url = f"http://localhost:{camofox_port}/tabs/{tab_id}/snapshot?userId=tweet-fetcher"
        req = urllib.request.Request(snap_url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            snap_data = json.loads(resp.read().decode())

        snapshot = snap_data.get("snapshot", "")

        # Parse replies from snapshot
        replies = []
        lines = snapshot.split("\n")
        current_reply = {}

        for line in lines:
            line = line.strip()
            # Match reply author
            if 'link "@' in line and '/url: /' in line:
                match = re.search(r'@(\w+)', line)
                if match:
                    if current_reply.get("author") and current_reply.get("author") != username:
                        replies.append(current_reply)
                    current_reply = {"author": f"@{match.group(1)}", "text": ""}

            # Match reply text
            if line.startswith("- text:") and current_reply.get("author"):
                text = line.replace("- text:", "").strip()
                if text and text != " " and "Replying to" not in text:
                    current_reply["text"] = text

        # Add last reply
        if current_reply.get("author") and current_reply.get("text") and current_reply["author"] != f"@{username}":
            replies.append(current_reply)

        # Close tab
        try:
            close_req = urllib.request.Request(
                f"http://localhost:{camofox_port}/tabs/{tab_id}",
                method="DELETE"
            )
            urllib.request.urlopen(close_req, timeout=5)
        except Exception:
            pass

        return replies if replies else []

    except Exception as e:
        print(f"[Nitter] Error: {e}", file=sys.stderr)
        return None


def fetch_rebrowser(username: str, tweet_id: str) -> Optional[str]:
    """Method 3: rebrowser-playwright - Full page fallback."""
    tweet_url = f"https://x.com/{username}/status/{tweet_id}"

    js_code = f"""
    const {{ chromium }} = require('rebrowser-playwright');
    (async () => {{
        const browser = await chromium.launch({{ headless: true }});
        const page = await browser.newPage();
        await page.goto('{tweet_url}', {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
        await page.waitForTimeout(5000);
        const title = await page.title();
        const text = await page.innerText('body').catch(() => '');
        console.log(JSON.stringify({{ title, text: text.substring(0, 5000) }}));
        await browser.close();
    }})().catch(e => {{ console.error(e.message); process.exit(1); }});
    """

    try:
        result = subprocess.run(
            ["node", "-e", js_code],
            capture_output=True, text=True, timeout=45
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return data.get("text", "")
    except Exception as e:
        print(f"[rebrowser] Error: {e}", file=sys.stderr)

    return None


def fetch_tweet(url: str, include_replies: bool = False, full: bool = False) -> Dict[str, Any]:
    """Fetch tweet using all available methods."""
    username, tweet_id = parse_tweet_url(url)
    result = {"url": url, "username": username, "tweet_id": tweet_id}

    # Method 1: FxTwitter API (always try)
    print(f"[1/3] FxTwitter API...", file=sys.stderr)
    tweet_data = fetch_fxtwitter(username, tweet_id)
    if tweet_data:
        result["tweet"] = tweet_data
        print(f"  ✅ Got tweet text ({len(tweet_data['text'])} chars)", file=sys.stderr)
    else:
        print(f"  ❌ FxTwitter failed", file=sys.stderr)

    # Method 2: Camofox + Nitter (if replies requested)
    if include_replies or full:
        print(f"[2/3] Camofox + Nitter (replies)...", file=sys.stderr)
        replies = fetch_nitter_replies(username, tweet_id)
        if replies is not None:
            result["replies"] = replies
            print(f"  ✅ Got {len(replies)} replies", file=sys.stderr)
        else:
            print(f"  ❌ Nitter replies failed", file=sys.stderr)

    # Method 3: rebrowser-playwright (if full requested)
    if full:
        print(f"[3/3] rebrowser-playwright (full page)...", file=sys.stderr)
        page_text = fetch_rebrowser(username, tweet_id)
        if page_text:
            result["full_page"] = page_text[:3000]
            print(f"  ✅ Got full page ({len(page_text)} chars)", file=sys.stderr)
        else:
            print(f"  ❌ rebrowser failed", file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Fetch tweets and replies from X/Twitter without login"
    )
    parser.add_argument("--url", "-u", required=True, help="Tweet URL")
    parser.add_argument("--replies", "-r", action="store_true", help="Include replies (Camofox + Nitter)")
    parser.add_argument("--full", "-f", action="store_true", help="Full fetch (all methods)")
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()
    result = fetch_tweet(args.url, include_replies=args.replies, full=args.full)

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
