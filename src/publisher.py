"""
publisher.py - Social media publishing integration.

Currently supports Twitter (X) via tweepy v2 API.
Requires environment variables:
  TWITTER_API_KEY, TWITTER_API_SECRET,
  TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
"""

import os
from pathlib import Path


REQUIRED_ENV_VARS = [
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_SECRET",
]


def _check_twitter_credentials() -> dict[str, str]:
    """Validate that all required Twitter env vars are set.

    Returns:
        Dict of credential name -> value.

    Raises:
        EnvironmentError: If any required variable is missing.
    """
    creds: dict[str, str] = {}
    missing = []
    for var in REQUIRED_ENV_VARS:
        val = os.environ.get(var)
        if not val:
            missing.append(var)
        else:
            creds[var] = val

    if missing:
        raise EnvironmentError(
            f"Missing Twitter credentials: {', '.join(missing)}. "
            "Set them as environment variables."
        )
    return creds


def publish_to_twitter(
    image_path: Path,
    caption: str = "",
) -> str:
    """Upload an image and post a tweet.

    Args:
        image_path: Path to the image file (PNG, JPEG, WebP).
        caption: Tweet text to accompany the image.

    Returns:
        URL of the published tweet.

    Raises:
        EnvironmentError: If Twitter credentials are missing.
        FileNotFoundError: If the image file doesn't exist.
        RuntimeError: If the Twitter API call fails.
    """
    image_path = Path(image_path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    creds = _check_twitter_credentials()

    try:
        import tweepy
    except ImportError as e:
        raise RuntimeError(
            "tweepy is required for Twitter posting. "
            "Install it with: pip install 'tweepy>=4.14.0'"
        ) from e

    # v1.1 API for media upload (v2 doesn't support media upload directly)
    auth = tweepy.OAuth1UserHandler(
        creds["TWITTER_API_KEY"],
        creds["TWITTER_API_SECRET"],
        creds["TWITTER_ACCESS_TOKEN"],
        creds["TWITTER_ACCESS_SECRET"],
    )
    api_v1 = tweepy.API(auth)

    # Upload media
    try:
        media = api_v1.media_upload(str(image_path))
    except tweepy.TweepyException as e:
        raise RuntimeError(f"Twitter media upload failed: {e}") from e

    # v2 client for creating the tweet
    client = tweepy.Client(
        consumer_key=creds["TWITTER_API_KEY"],
        consumer_secret=creds["TWITTER_API_SECRET"],
        access_token=creds["TWITTER_ACCESS_TOKEN"],
        access_token_secret=creds["TWITTER_ACCESS_SECRET"],
    )

    try:
        response = client.create_tweet(
            text=caption,
            media_ids=[media.media_id],
        )
    except tweepy.TweepyException as e:
        raise RuntimeError(f"Twitter post failed: {e}") from e

    tweet_id = response.data["id"]
    # Extract username for URL (best-effort)
    try:
        me = client.get_me()
        username = me.data.username
    except Exception:
        username = "i"

    return f"https://x.com/{username}/status/{tweet_id}"
