# config.py
import os

# Get videos from environment variable or use defaults
VIDEO_URLS_STRING = os.getenv('VIDEO_URLS', '')

if VIDEO_URLS_STRING:
    # Split by comma if provided
    VIDEO_URLS = [url.strip() for url in VIDEO_URLS_STRING.split(',')]
else:
    # Default videos (REPLACE THESE!)
    VIDEO_URLS = [
        "https://rumble.com/v5qn8jj-video-1.html",
        "https://rumble.com/v5qn8jk-video-2.html",
        "https://rumble.com/v5qn8jl-video-3.html",
    ]

# Get reload interval from env or default to 120 seconds (2 minutes)
RELOAD_INTERVAL = int(os.getenv('RELOAD_INTERVAL', '120'))

# Get number of tabs from env or default to 10
NUM_TABS = int(os.getenv('NUM_TABS', '10'))

print(f"Config loaded: {len(VIDEO_URLS)} videos, {NUM_TABS} tabs, {RELOAD_INTERVAL}s reload")
