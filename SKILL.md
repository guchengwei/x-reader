---
name: x-tweet-fetcher
description: Fetch tweets and replies from X/Twitter without login or API keys. Use when the user shares an X/Twitter link and wants to read the tweet content, or when you need to fetch tweet text, stats, or reply threads. Combines FxTwitter API (tweet text + stats), Camofox + Nitter (reply threads), and rebrowser-playwright (full page fallback). No X account or API key required.
---

# X Tweet Fetcher

Fetch tweets and replies from X/Twitter without authentication.

## Architecture

Three complementary methods, used in order:

| Method | Fetches | Requires |
|--------|---------|----------|
| **FxTwitter API** | Tweet text, stats, author, quotes | Nothing (free API) |
| **Camofox + Nitter** | Reply threads, comments | Camofox running on port 9377 |
| **rebrowser-playwright** | Full page HTML (fallback) | `rebrowser-playwright` npm package |

## Quick Start

### 1. Fetch tweet text + stats
```bash
python3 scripts/fetch_tweet.py --url "https://x.com/user/status/123456"
```

### 2. Fetch tweet + replies
```bash
python3 scripts/fetch_tweet.py --url "https://x.com/user/status/123456" --replies
```

### 3. Fetch everything (text + replies + full page)
```bash
python3 scripts/fetch_tweet.py --url "https://x.com/user/status/123456" --full
```

## Method Details

### Method 1: FxTwitter API (Primary)

Free, no auth, returns JSON with tweet text, author info, stats, and quoted tweets.

```
GET https://api.fxtwitter.com/{username}/status/{tweet_id}
```

**Returns**: text, author, likes, retweets, bookmarks, views, quotes, created_at

### Method 2: Camofox + Nitter (Replies)

Uses Camofox browser (port 9377) to render Nitter pages and extract reply threads.

**Requires**: Camofox running (`node server.js` in camofox-browser directory)

### Method 3: rebrowser-playwright (Fallback)

Full headless browser that can bypass bot detection. Loads the actual x.com page.

**Requires**: `npm install rebrowser-playwright`

## Output Format

```json
{
  "tweet": {
    "text": "...",
    "author": "...",
    "likes": 7,
    "retweets": 0,
    "bookmarks": 8,
    "views": 1756,
    "created_at": "...",
    "quote": { ... }
  },
  "replies": [
    { "author": "...", "text": "...", "likes": 1 }
  ]
}
```

## Installation

```bash
# Clone the skill
git clone https://github.com/anthropics-ai/x-tweet-fetcher.git

# Install dependencies (only needed for Method 3)
npm install rebrowser-playwright

# For Method 2, ensure Camofox is running
cd /path/to/camofox-browser && node server.js
```

## Notes

- Method 1 (FxTwitter) works everywhere, no setup needed
- Method 2 (Camofox + Nitter) requires Camofox browser service
- Method 3 (rebrowser-playwright) is a fallback for edge cases
- No X/Twitter account or API key required for any method
