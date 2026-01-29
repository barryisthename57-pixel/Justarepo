# bot.py
import asyncio
from playwright.async_api import async_playwright
import random
import time
import psutil
import logging
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RumbleBot:
    def __init__(self, video_urls, reload_interval=120, num_tabs=10):
        self.video_urls = video_urls
        self.reload_interval = reload_interval
        self.num_tabs = num_tabs
        self.pages = []
        self.browser = None
        
        self.stats = {
            'total_views': 0,
            'total_reloads': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def check_resources(self):
        """Check system resources"""
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        ram_available_gb = memory.available / (1024 ** 3)
        ram_total_gb = memory.total / (1024 ** 3)
        
        logger.info("=" * 60)
        logger.info("🖥️  SYSTEM RESOURCES")
        logger.info("=" * 60)
        logger.info(f"💾 Total RAM: {ram_total_gb:.2f} GB")
        logger.info(f"💾 Available RAM: {ram_available_gb:.2f} GB")
        logger.info(f"💾 RAM Usage: {memory.percent}%")
        logger.info(f"🔧 CPU Cores: {cpu_count}")
        logger.info("=" * 60)
        
        # Conservative limit for Railway
        max_safe_tabs = min(int((ram_available_gb - 1) / 0.2), 20)
        
        if self.num_tabs > max_safe_tabs:
            logger.warning(f"⚠️  Requested {self.num_tabs} tabs, limiting to {max_safe_tabs}")
            self.num_tabs = max_safe_tabs
        
        logger.info(f"📊 Using {self.num_tabs} tabs")
        logger.info("=" * 60)
    
    async def open_tab(self, browser, url, tab_index):
        """Open single tab with video"""
        try:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1280, "height": 720})
            
            logger.info(f"🌐 Tab {tab_index + 1}: Loading {url[:60]}...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            await asyncio.sleep(2)
            
            # Auto-play video
            await page.evaluate("""
                () => {
                    const videos = document.querySelectorAll('video');
                    videos.forEach(v => {
                        v.muted = true;
                        v.play().catch(e => console.log('Play failed:', e));
                    });
                }
            """)
            
            logger.info(f"✅ Tab {tab_index + 1}: Playing")
            self.stats['total_views'] += 1
            
            return page
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1}: {str(e)[:150]}")
            self.stats['errors'] += 1
            return None
    
    async def reload_tab(self, page, tab_index):
        """Reload tab with random video"""
        try:
            url = random.choice(self.video_urls)
            
            logger.info(f"🔄 Tab {tab_index + 1}: Reloading...")
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(2)
            
            await page.evaluate("""
                () => {
                    const videos = document.querySelectorAll('video');
                    videos.forEach(v => {
                        v.muted = true;
                        v.play().catch(e => console.log('Play failed:', e));
                    });
                }
            """)
            
            self.stats['total_reloads'] += 1
            self.stats['total_views'] += 1
            
            logger.info(f"✅ Tab {tab_index + 1}: Reloaded")
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1} reload: {str(e)[:150]}")
            self.stats['errors'] += 1
    
    def print_stats(self):
        """Print statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        logger.info("=" * 60)
        logger.info("📊 STATISTICS")
        logger.info("=" * 60)
        logger.info(f"⏱️  Runtime: {runtime:.1f} minutes")
        logger.info(f"📺 Active Tabs: {len(self.pages)}")
        logger.info(f"👁️  Total Views: {self.stats['total_views']}")
        logger.info(f"🔄 Total Reloads: {self.stats['total_reloads']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info(f"💾 RAM: {memory.percent}% ({memory.used / (1024**3):.2f} GB)")
        logger.info(f"🔧 CPU: {cpu}%")
        logger.info("=" * 60)
    
    async def reload_loop(self):
        """Auto-reload loop"""
        while True:
            await asyncio.sleep(self.reload_interval)
            
            logger.info(f"\n🔄 RELOAD CYCLE - {len(self.pages)} tabs")
            
            if len(self.pages) == 0:
                logger.warning("⚠️  No active tabs to reload!")
                continue
            
            tasks = [
                self.reload_tab(page, i)
                for i, page in enumerate(self.pages)
                if page
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            self.print_stats()
    
    async def run(self):
        """Main runner"""
        self.check_resources()
        
        logger.info(f"\n🚀 STARTING BOT")
        logger.info(f"📺 Tabs: {self.num_tabs}")
        logger.info(f"🔄 Reload: Every {self.reload_interval}s ({self.reload_interval/60:.1f} min)")
        logger.info(f"📹 Videos: {len(self.video_urls)}")
        logger.info(f"🎯 Target: {self.video_urls[0][:80]}")
        
        async with async_playwright() as p:
            # FIXED: Better browser args for Railway/Docker
            self.browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--mute-audio',
                    '--no-first-run',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-breakpad',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                    '--disable-ipc-flooding-protection',
                    '--disable-renderer-backgrounding',
                    '--force-color-profile=srgb',
                    '--metrics-recording-only',
                    '--no-default-browser-check',
                    '--no-pings',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--disable-blink-features=AutomationControlled',
                    # REMOVED: '--single-process' (causes crashes)
                    # REMOVED: '--disable-web-security' (can cause issues)
                ]
            )
            
            logger.info("\n📂 Opening tabs in batches...")
            
            # Open in smaller batches with delays
            batch_size = 2  # Smaller batches for Railway
            for batch_start in range(0, self.num_tabs, batch_size):
                batch_end = min(batch_start + batch_size, self.num_tabs)
                
                logger.info(f"\n📦 Batch {(batch_start // batch_size) + 1}: Tabs {batch_start + 1}-{batch_end}")
                
                tasks = [
                    self.open_tab(
                        self.browser,
                        random.choice(self.video_urls),
                        i
                    )
                    for i in range(batch_start, batch_end)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for page in results:
                    if page and not isinstance(page, Exception):
                        self.pages.append(page)
                
                logger.info(f"✅ Progress: {len(self.pages)}/{self.num_tabs} tabs active")
                
                # Longer delay between batches
                if batch_end < self.num_tabs:
                    await asyncio.sleep(3)
            
            if len(self.pages) == 0:
                logger.error("❌ FAILED: No tabs could be opened!")
                logger.error("This might be a Railway resource issue or Rumble blocking")
                return
            
            self.print_stats()
            
            logger.info("\n🔁 Starting auto-reload loop...\n")
            
            try:
                await self.reload_loop()
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            finally:
                logger.info("Closing browser...")
                await self.browser.close()


# Main execution
if __name__ == "__main__":
    from config import VIDEO_URLS, RELOAD_INTERVAL, NUM_TABS
    
    bot = RumbleBot(
        video_urls=VIDEO_URLS,
        reload_interval=RELOAD_INTERVAL,
        num_tabs=NUM_TABS
    )
    
    asyncio.run(bot.run())
