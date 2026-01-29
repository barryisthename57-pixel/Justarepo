# config.py
import os

VIDEO_URL = os.getenv('VIDEO_URL', '')
VIDEO_URLS_STRING = os.getenv('VIDEO_URLS', '')

if VIDEO_URLS_STRING:
    VIDEO_URLS = [url.strip() for url in VIDEO_URLS_STRING.split(',') if url.strip()]
elif VIDEO_URL:
    VIDEO_URLS = [VIDEO_URL]
else:
    VIDEO_URLS = ["https://rumble.com/v74zzpo-your-video.html"]

RELOAD_INTERVAL = int(os.getenv('RELOAD_INTERVAL', '120'))
NUM_TABS = int(os.getenv('NUM_TABS', '10'))

print("=" * 70)
print("💰 MONETIZED BOT CONFIGURATION")
print("=" * 70)
print(f"📹 Videos: {len(VIDEO_URLS)}")
for i, url in enumerate(VIDEO_URLS, 1):
    print(f"   {i}. {url}")
print(f"📺 Tabs: {NUM_TABS}")
print(f"🔄 Cycle: {RELOAD_INTERVAL}s ({RELOAD_INTERVAL/60:.1f} min)")
print("=" * 70)
print()
