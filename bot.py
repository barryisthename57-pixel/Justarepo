# bot.py
import asyncio
from playwright.async_api import async_playwright
import random
import psutil
import logging
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1366, 'height': 768},
    {'width': 1280, 'height': 720},
    {'width': 1440, 'height': 900},
    {'width': 1536, 'height': 864},
]

class RumbleBot:
    def __init__(self, video_urls, reload_interval=120, num_tabs=10):
        self.video_urls = video_urls
        self.reload_interval = reload_interval
        self.num_tabs = num_tabs
        self.pages = []
        self.contexts = []
        self.browser = None
        
        self.stats = {
            'total_views': 0,
            'total_cycles': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def check_resources(self):
        """Check system resources"""
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        
        ram_available_gb = memory.available / (1024 ** 3)
        ram_total_gb = memory.total / (1024 ** 3)
        
        logger.info("=" * 70)
        logger.info("🖥️  SYSTEM RESOURCES")
        logger.info("=" * 70)
        logger.info(f"💾 Total RAM: {ram_total_gb:.2f} GB")
        logger.info(f"💾 Available RAM: {ram_available_gb:.2f} GB")
        logger.info(f"💾 RAM Usage: {memory.percent}%")
        logger.info(f"🔧 CPU Cores: {cpu_count}")
        logger.info("=" * 70)
        
        # Calculate safe tab count
        max_safe_tabs = min(int((ram_available_gb - 2) / 0.2), 200)
        
        if self.num_tabs > max_safe_tabs:
            logger.warning(f"⚠️  Requested {self.num_tabs} tabs")
            logger.warning(f"⚠️  Recommended max: {max_safe_tabs} tabs")
            logger.warning(f"⚠️  Continuing anyway...")
        
        logger.info(f"📊 Target Tabs: {self.num_tabs}")
        logger.info("=" * 70)
    
    async def open_tab(self, url, tab_index):
        """Open a fresh tab with video"""
        try:
            # Create new isolated context
            context = await self.browser.new_context(
                viewport=random.choice(VIEWPORTS),
                user_agent=random.choice(USER_AGENTS),
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            page = await context.new_page()
            
            # Navigate to video
            logger.info(f"🌐 Tab {tab_index + 1}: Opening {url[:60]}...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Random human-like delay
            await asyncio.sleep(random.uniform(1.5, 3))
            
            # Try to play video
            played = await page.evaluate("""
                async () => {
                    const videos = document.querySelectorAll('video');
                    if (videos.length === 0) return false;
                    
                    for (let v of videos) {
                        v.muted = true;
                        try {
                            await v.play();
                            return true;
                        } catch (e) {
                            console.log('Play failed:', e);
                        }
                    }
                    return false;
                }
            """)
            
            if played:
                logger.info(f"✅ Tab {tab_index + 1}: Playing video")
                self.stats['total_views'] += 1
            else:
                logger.warning(f"⚠️  Tab {tab_index + 1}: Video might not be playing")
                self.stats['total_views'] += 1  # Count it anyway
            
            return context, page
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1} error: {str(e)[:120]}")
            self.stats['errors'] += 1
            return None, None
    
    async def close_tab(self, context, page, tab_index):
        """Close a tab and its context"""
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            logger.info(f"🗑️  Tab {tab_index + 1}: Closed")
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1} close error: {str(e)[:80]}")
    
    async def cycle_tab(self, old_context, old_page, tab_index):
        """Close old tab and open new one (simulates new visitor)"""
        try:
            # Random delay before cycling (simulate human behavior)
            await asyncio.sleep(random.uniform(0.5, 2))
            
            logger.info(f"🔄 Tab {tab_index + 1}: Cycling (close → open new)")
            
            # Close old tab
            await self.close_tab(old_context, old_page, tab_index)
            
            # Small gap between close and open
            await asyncio.sleep(random.uniform(0.3, 1))
            
            # Open fresh tab
            url = random.choice(self.video_urls)
            new_context, new_page = await self.open_tab(url, tab_index)
            
            return new_context, new_page
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1} cycle error: {str(e)[:120]}")
            self.stats['errors'] += 1
            return None, None
    
    def print_stats(self):
        """Print current statistics"""
        runtime = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        # Calculate projections
        if runtime > 0:
            views_per_min = self.stats['total_views'] / runtime
            views_per_hour = views_per_min * 60
            views_per_day = views_per_hour * 24
        else:
            views_per_hour = 0
            views_per_day = 0
        
        # Get process-specific RAM usage
        try:
            process = psutil.Process(os.getpid())
            process_ram_mb = process.memory_info().rss / (1024 * 1024)
            process_ram_gb = process_ram_mb / 1024
        except:
            process_ram_gb = 0
        
        logger.info("=" * 70)
        logger.info("📊 STATISTICS")
        logger.info("=" * 70)
        logger.info(f"⏱️  Runtime: {runtime:.1f} minutes ({runtime/60:.1f} hours)")
        logger.info(f"📺 Active Tabs: {len(self.pages)}/{self.num_tabs}")
        logger.info(f"👁️  Total Views: {self.stats['total_views']:,}")
        logger.info(f"🔄 Total Cycles: {self.stats['total_cycles']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info("")
        logger.info(f"💻 BOT RESOURCE USAGE:")
        logger.info(f"   RAM (bot): {process_ram_gb:.2f} GB ({process_ram_mb:.0f} MB)")
        logger.info(f"   RAM (system): {memory.percent}% ({memory.used / (1024**3):.1f} GB used)")
        logger.info(f"   CPU: {cpu}%")
        logger.info("")
        logger.info(f"📈 PROJECTIONS:")
        logger.info(f"   Views/hour: {views_per_hour:,.0f}")
        logger.info(f"   Views/day: {views_per_day:,.0f}")
        logger.info(f"   Views/month: {views_per_day * 30:,.0f}")
        logger.info("=" * 70)
    
    async def cycle_all_tabs(self):
        """Close all tabs and reopen fresh ones"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 CYCLE {self.stats['total_cycles'] + 1}: Closing & reopening all tabs")
        logger.info(f"{'='*70}\n")
        
        new_contexts = []
        new_pages = []
        
        # Cycle tabs one by one (more natural than all at once)
        for i in range(len(self.pages)):
            old_context = self.contexts[i] if i < len(self.contexts) else None
            old_page = self.pages[i] if i < len(self.pages) else None
            
            new_context, new_page = await self.cycle_tab(old_context, old_page, i)
            
            if new_context and new_page:
                new_contexts.append(new_context)
                new_pages.append(new_page)
            
            # Stagger the cycling (don't hammer server)
            if i < len(self.pages) - 1:
                await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Update tab lists
        self.contexts = new_contexts
        self.pages = new_pages
        
        self.stats['total_cycles'] += 1
        
        logger.info(f"\n✅ Cycle complete: {len(self.pages)} tabs active\n")
        self.print_stats()
    
    async def cycle_loop(self):
        """Main loop - cycle tabs at intervals"""
        while True:
            # Add random variance to interval (more human-like)
            random_interval = random.uniform(
                self.reload_interval * 0.9,
                self.reload_interval * 1.1
            )
            
            logger.info(f"\n⏰ Next cycle in {random_interval:.0f} seconds ({random_interval/60:.1f} minutes)")
            await asyncio.sleep(random_interval)
            
            if len(self.pages) == 0:
                logger.warning("⚠️  No active tabs to cycle!")
                continue
            
            await self.cycle_all_tabs()
    
    async def run(self):
        """Main bot runner"""
        self.check_resources()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🚀 RUMBLE BOT STARTING")
        logger.info("=" * 70)
        logger.info(f"📺 Target Tabs: {self.num_tabs}")
        logger.info(f"🔄 Cycle Interval: {self.reload_interval}s ({self.reload_interval/60:.1f} min)")
        logger.info(f"📹 Video Pool: {len(self.video_urls)} URL(s)")
        logger.info(f"🎯 Strategy: Close & Reopen (Fresh sessions)")
        logger.info("=" * 70)
        logger.info("")
        
        async with async_playwright() as p:
            # Launch browser
            self.browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--mute-audio',
                    '--disable-extensions',
                    '--disable-background-networking',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            logger.info("📂 Opening initial tabs...\n")
            
            # Open initial tabs in small batches
            batch_size = 3
            for batch_start in range(0, self.num_tabs, batch_size):
                batch_end = min(batch_start + batch_size, self.num_tabs)
                
                logger.info(f"📦 Batch {(batch_start // batch_size) + 1}: Tabs {batch_start + 1}-{batch_end}")
                
                tasks = [
                    self.open_tab(
                        random.choice(self.video_urls),
                        i
                    )
                    for i in range(batch_start, batch_end)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for context, page in results:
                    if context and page and not isinstance(context, Exception):
                        self.contexts.append(context)
                        self.pages.append(page)
                
                logger.info(f"   Progress: {len(self.pages)}/{self.num_tabs} tabs opened")
                
                # Delay between batches
                if batch_end < self.num_tabs:
                    await asyncio.sleep(2)
            
            logger.info("")
            
            if len(self.pages) == 0:
                logger.error("❌ FATAL: No tabs could be opened!")
                logger.error("Check if video URLs are correct and accessible")
                return
            
            logger.info(f"✅ Initial setup complete: {len(self.pages)}/{self.num_tabs} tabs active\n")
            self.print_stats()
            
            logger.info(f"\n🔁 Starting cycle loop...\n")
            
            try:
                await self.cycle_loop()
            except KeyboardInterrupt:
                logger.info("\n\n🛑 SHUTDOWN REQUESTED")
            except Exception as e:
                logger.error(f"\n❌ FATAL ERROR: {e}")
            finally:
                logger.info("\n🧹 Cleaning up...")
                for i, (context, page) in enumerate(zip(self.contexts, self.pages)):
                    await self.close_tab(context, page, i)
                await self.browser.close()
                logger.info("✅ Cleanup complete")
                self.print_stats()


if __name__ == "__main__":
    # Import config
    from config import VIDEO_URLS, RELOAD_INTERVAL, NUM_TABS
    
    # Create and run bot
    bot = RumbleBot(
        video_urls=VIDEO_URLS,
        reload_interval=RELOAD_INTERVAL,
        num_tabs=NUM_TABS
    )
    
    asyncio.run(bot.run())
