# bot_parallel.py - ALL TABS LOAD AT ONCE!
import asyncio
from playwright.async_api import async_playwright
import random
import psutil
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

MOBILE_USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
]

MOBILE_VIEWPORTS = [
    {'width': 412, 'height': 915},
    {'width': 360, 'height': 800},
]

AUTOPLAY_SCRIPT = """
(function() {
    console.log('[PARALLEL-BOT] Starting autoplay...');
    
    let attempts = 0;
    const maxAttempts = 40;
    
    function tryPlay() {
        attempts++;
        const videos = document.querySelectorAll('video');
        
        videos.forEach((v, i) => {
            try {
                if (v.readyState < 3) v.load();
                
                v.muted = true;
                v.autoplay = true;
                v.playsInline = true;
                
                v.play().then(() => {
                    console.log('[PARALLEL-BOT] ✅ Video ' + i + ' playing');
                }).catch(() => {
                    setTimeout(() => {
                        v.muted = true;
                        v.play();
                    }, 500);
                });
            } catch(e) {}
        });
        
        const selectors = ['button[aria-label*="play" i]', '.vjs-big-play-button', '.play-button'];
        selectors.forEach(sel => {
            try {
                document.querySelectorAll(sel).forEach(btn => {
                    if (btn) btn.click();
                });
            } catch(e) {}
        });
    }
    
    try {
        Object.defineProperty(document, 'hidden', { get: () => false });
        Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
    } catch(e) {}
    
    tryPlay();
    
    const interval = setInterval(() => {
        if (attempts >= maxAttempts) {
            clearInterval(interval);
            return;
        }
        
        const videos = document.querySelectorAll('video');
        let anyPlaying = false;
        videos.forEach(v => {
            if (!v.paused && v.currentTime > 0) anyPlaying = true;
        });
        
        if (!anyPlaying) tryPlay();
    }, 500);
    
    const observer = new MutationObserver(() => tryPlay());
    observer.observe(document.body, { childList: true, subtree: true });
})();
"""

class ParallelBot:
    def __init__(self, video_urls, reload_interval=60, num_tabs=11):
        self.video_urls = video_urls
        self.reload_interval = reload_interval
        self.num_tabs = num_tabs
        self.pages = []
        self.contexts = []
        self.browser = None
        
        self.stats = {
            'total_views': 0,
            'confirmed_playing': 0,
            'total_cycles': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def open_tab_fast(self, url, tab_index):
        """Open tab WITHOUT waiting for playback confirmation"""
        try:
            context = await self.browser.new_context(
                viewport=random.choice(MOBILE_VIEWPORTS),
                user_agent=random.choice(MOBILE_USER_AGENTS),
                locale='en-US',
                timezone_id='America/New_York',
                is_mobile=True,
                has_touch=True,
            )
            
            page = await context.new_page()
            
            # Load page (don't wait for networkidle, just domcontentloaded)
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            logger.info(f"✅ Tab {tab_index + 1}: Loaded")
            
            self.stats['total_views'] += 1
            return context, page
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1}: {str(e)[:80]}")
            self.stats['errors'] += 1
            return None, None
    
    async def inject_autoplay_all(self):
        """Inject autoplay into ALL tabs at once"""
        logger.info(f"💉 Injecting autoplay into all {len(self.pages)} tabs...")
        
        tasks = []
        for i, page in enumerate(self.pages):
            if page:
                tasks.append(self.inject_to_page(page, i))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"✅ Autoplay injected into all tabs!")
    
    async def inject_to_page(self, page, tab_index):
        """Inject autoplay script to one page"""
        try:
            await page.evaluate(AUTOPLAY_SCRIPT)
            logger.info(f"   💉 Tab {tab_index + 1}: Script injected")
        except Exception as e:
            logger.error(f"   ❌ Tab {tab_index + 1}: Injection failed")
    
    async def verify_playback_all(self):
        """Check playback on all tabs at once"""
        logger.info(f"🔍 Verifying playback on all tabs...")
        
        tasks = []
        for i, page in enumerate(self.pages):
            if page:
                tasks.append(self.check_playback(page, i))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        playing_count = sum(1 for r in results if r is True)
        self.stats['confirmed_playing'] += playing_count
        
        logger.info(f"✅ {playing_count}/{len(self.pages)} tabs confirmed playing")
    
    async def check_playback(self, page, tab_index):
        """Check if video is playing on one page"""
        try:
            is_playing = await page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    return v && !v.paused && v.currentTime > 0;
                }
            """)
            
            if is_playing:
                logger.info(f"   ✅ Tab {tab_index + 1}: PLAYING")
                return True
            else:
                logger.info(f"   ⚠️  Tab {tab_index + 1}: Not playing")
                return False
        except:
            return False
    
    async def close_all_tabs(self):
        """Close all tabs at once"""
        logger.info(f"🗑️  Closing all {len(self.pages)} tabs...")
        
        tasks = []
        for context, page in zip(self.contexts, self.pages):
            tasks.append(self.close_tab(context, page))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.contexts = []
        self.pages = []
        
        logger.info(f"✅ All tabs closed")
    
    async def close_tab(self, context, page):
        """Close one tab"""
        try:
            if page:
                await page.close()
            if context:
                await context.close()
        except:
            pass
    
    def print_stats(self):
        runtime = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        
        if runtime > 0:
            views_per_min = self.stats['total_views'] / runtime
            views_per_hour = views_per_min * 60
            views_per_day = views_per_hour * 24
        else:
            views_per_hour = views_per_day = 0
        
        success_rate = (self.stats['confirmed_playing'] / max(self.stats['total_views'], 1)) * 100
        
        logger.info("=" * 70)
        logger.info("📊 PARALLEL BOT STATISTICS")
        logger.info("=" * 70)
        logger.info(f"⏱️  Runtime: {runtime:.1f} min ({runtime/60:.1f} hrs)")
        logger.info(f"📺 Active Tabs: {len(self.pages)}/{self.num_tabs}")
        logger.info(f"👁️  Total Views: {self.stats['total_views']}")
        logger.info(f"✅ Confirmed Playing: {self.stats['confirmed_playing']} ({success_rate:.0f}%)")
        logger.info(f"🔄 Cycles: {self.stats['total_cycles']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info(f"")
        logger.info(f"💰 PROJECTIONS:")
        logger.info(f"   Views/hour: {views_per_hour:,.0f}")
        logger.info(f"   Views/day: {views_per_day:,.0f}")
        logger.info(f"   Views/month: {views_per_day * 30:,.0f}")
        logger.info(f"   Est. earnings/day (at $1 CPM): ${views_per_day/1000:.2f}")
        logger.info("=" * 70)
    
    async def open_all_tabs_parallel(self):
        """Open ALL tabs at the same time"""
        logger.info(f"📂 Opening {self.num_tabs} tabs in PARALLEL...")
        
        start_time = asyncio.get_event_loop().time()
        
        # Create all tab opening tasks
        tasks = [
            self.open_tab_fast(random.choice(self.video_urls), i)
            for i in range(self.num_tabs)
        ]
        
        # Run ALL tasks at once!
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful tabs
        for context, page in results:
            if context and page and not isinstance(context, Exception):
                self.contexts.append(context)
                self.pages.append(page)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        logger.info(f"✅ Opened {len(self.pages)}/{self.num_tabs} tabs in {elapsed:.1f}s")
        
        return len(self.pages)
    
    async def cycle_all_tabs_parallel(self):
        """Close all tabs and reopen in parallel"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 CYCLE {self.stats['total_cycles'] + 1}")
        logger.info(f"{'='*70}\n")
        
        # Close all tabs at once
        await self.close_all_tabs()
        
        # Small delay
        await asyncio.sleep(1)
        
        # Reopen all tabs at once
        await self.open_all_tabs_parallel()
        
        # Wait for pages to settle
        await asyncio.sleep(3)
        
        # Inject autoplay into all tabs at once
        await self.inject_autoplay_all()
        
        # Wait for autoplay to work
        await asyncio.sleep(5)
        
        # Verify playback on all tabs at once
        await self.verify_playback_all()
        
        self.stats['total_cycles'] += 1
        
        self.print_stats()
    
    async def cycle_loop(self):
        """Main loop - cycle all tabs in parallel"""
        while True:
            interval = random.uniform(self.reload_interval * 0.9, self.reload_interval * 1.1)
            logger.info(f"\n⏰ Next cycle in {interval:.0f}s ({interval/60:.1f} min)")
            await asyncio.sleep(interval)
            
            await self.cycle_all_tabs_parallel()
    
    async def run(self):
        logger.info("\n" + "=" * 70)
        logger.info("🚀 PARALLEL LOADING BOT")
        logger.info("=" * 70)
        logger.info(f"Strategy: All tabs load at once, then inject autoplay")
        logger.info(f"Tabs: {self.num_tabs}")
        logger.info(f"Reload: {self.reload_interval}s ({self.reload_interval/60:.1f} min)")
        logger.info("=" * 70 + "\n")
        
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--autoplay-policy=no-user-gesture-required',
                    '--mute-audio',
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            
            # INITIAL SETUP - ALL AT ONCE
            logger.info("🚀 INITIAL SETUP (PARALLEL)\n")
            
            await self.open_all_tabs_parallel()
            
            await asyncio.sleep(3)
            
            await self.inject_autoplay_all()
            
            await asyncio.sleep(5)
            
            await self.verify_playback_all()
            
            logger.info(f"\n✅ SETUP COMPLETE: {len(self.pages)} tabs active\n")
            self.print_stats()
            
            logger.info("\n🔁 Starting parallel cycle loop...\n")
            
            try:
                await self.cycle_loop()
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping...")
            finally:
                await self.close_all_tabs()
                await self.browser.close()


if __name__ == "__main__":
    from config import VIDEO_URLS, RELOAD_INTERVAL, NUM_TABS
    
    bot = ParallelBot(VIDEO_URLS, RELOAD_INTERVAL, NUM_TABS)
    asyncio.run(bot.run())
