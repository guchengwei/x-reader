# x-tweet-fetcher

🦞 Fetch tweets and replies from X/Twitter **without login or API keys**.

An [OpenClaw](https://github.com/openclaw/openclaw) skill that combines three methods to reliably extract tweet content and reply threads.

## How It Works

| Method | What It Fetches | Requires |
|--------|----------------|----------|
| **FxTwitter API** | Tweet text, stats, author, quotes | Nothing (free) |
| **Camofox + Nitter** | Reply threads / comments | [Camofox](https://github.com/nicepkg/camofox-browser) on port 9377 |
| **rebrowser-playwright** | Full page HTML (fallback) | `rebrowser-playwright` npm package |

## Quick Start

```bash
# Fetch tweet text + stats
python3 scripts/fetch_tweet.py --url "https://x.com/user/status/123456"

# Fetch tweet + replies
python3 scripts/fetch_tweet.py --url "https://x.com/user/status/123456" --replies

# Fetch everything
python3 scripts/fetch_tweet.py --url "https://x.com/user/status/123456" --full --pretty
```

## Example Output

```json
{
  "tweet": {
    "text": "Hello world!",
    "author": "username",
    "likes": 42,
    "retweets": 5,
    "views": 1200
  },
  "replies": [
    { "author": "@someone", "text": "Great tweet!" }
  ]
}
```

## Installation

### As OpenClaw Skill
Copy the `x-tweet-fetcher` folder to your OpenClaw skills directory.

### Standalone
```bash
git clone https://github.com/ythx-101/x-tweet-fetcher.git
cd x-tweet-fetcher

# Method 1 (FxTwitter) works out of the box - no dependencies
python3 scripts/fetch_tweet.py --url "https://x.com/..." 

# For Method 2 (replies), install and run Camofox
# For Method 3 (fallback), install rebrowser-playwright:
npm install rebrowser-playwright
```

## Why Three Methods?

- **FxTwitter API** is fast and reliable for tweet text, but can't fetch replies
- **Camofox + Nitter** renders JavaScript pages and can extract reply threads
- **rebrowser-playwright** bypasses bot detection for edge cases

Together they cover all scenarios without needing an X account or API key.

## Credits

Built by 🦞 小灵 (Xiaoling) & 林月 (Qingyue) as part of the [OpenClaw](https://github.com/openclaw/openclaw) ecosystem.

- [FxTwitter](https://github.com/FixTweet/FxTwitter) - Tweet embedding API
- [Camofox](https://github.com/nicepkg/camofox-browser) - Anti-detection browser
- [Nitter](https://github.com/zedeus/nitter) - Twitter alternative frontend
- [rebrowser-playwright](https://github.com/nicepkg/rebrowser-playwright) - Bot-bypass Playwright

## License

MIT
