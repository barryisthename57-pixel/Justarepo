# config.py
import os

# Get video URL(s) from environment variable
VIDEO_URL = os.getenv('VIDEO_URL', '')
VIDEO_URLS_STRING = os.getenv('VIDEO_URLS', '')

# Parse video URLs
if VIDEO_URLS_STRING:
    # Multiple URLs separated by comma
    VIDEO_URLS = [url.strip() for url in VIDEO_URLS_STRING.split(',') if url.strip()]
elif VIDEO_URL:
    # Single URL
    VIDEO_URLS = [VIDEO_URL]
else:
    # Default fallback (REPLACE WITH YOUR VIDEO!)
    VIDEO_URLS = [
        "https://rumble.com/v5qn8jj-example-video.html"
    ]

# Get reload interval (default: 2 minutes)
RELOAD_INTERVAL = int(os.getenv('RELOAD_INTERVAL', '120'))

# Get number of tabs (default: 10)
NUM_TABS = int(os.getenv('NUM_TABS', '10'))

# Log configuration
print("=" * 70)
print("⚙️  CONFIGURATION LOADED")
print("=" * 70)
print(f"📹 Video URLs: {len(VIDEO_URLS)}")
for i, url in enumerate(VIDEO_URLS[:3], 1):
    print(f"   {i}. {url[:65]}...")
if len(VIDEO_URLS) > 3:
    print(f"   ... and {len(VIDEO_URLS) - 3} more")
print(f"📺 Number of Tabs: {NUM_TABS}")
print(f"🔄 Cycle Interval: {RELOAD_INTERVAL}s ({RELOAD_INTERVAL/60:.1f} minutes)")
print("=" * 70)
print()
