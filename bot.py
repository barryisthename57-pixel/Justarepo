# bot.py - COMPLETE AND FIXED
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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1440, 'height': 900},
    {'width': 1366, 'height': 768},
]

AUTOPLAY_SCRIPT = """
(async function() {
    console.log('[RUMBLE-MONETIZED] Starting autoplay script...');
    
    let playAttempts = 0;
    const maxAttempts = 60;
    
    function tryPlay() {
        playAttempts++;
        console.log('[RUMBLE-MONETIZED] Attempt #' + playAttempts);
        
        const videos = document.querySelectorAll('video');
        console.log('[RUMBLE-MONETIZED] Found ' + videos.length + ' video(s)');
        
        videos.forEach((v, index) => {
            try {
                if (v.readyState < 3) {
                    console.log('[RUMBLE-MONETIZED] Video ' + index + ' not ready, loading...');
                    v.load();
                }
                
                v.muted = true;
                v.volume = 0;
                v.autoplay = true;
                v.playsInline = true;
                v.removeAttribute('data-click-to-play');
                
                const playPromise = v.play();
                if (playPromise) {
                    playPromise.then(() => {
                        console.log('[RUMBLE-MONETIZED] ✅ Video ' + index + ' PLAYING at ' + v.currentTime.toFixed(2) + 's');
                    }).catch(err => {
                        console.log('[RUMBLE-MONETIZED] ❌ Play failed: ' + err.name);
                        setTimeout(() => {
                            v.muted = true;
                            v.play().catch(() => {});
                        }, 500);
                    });
                }
                
                v.dispatchEvent(new Event('play'));
                
            } catch(e) {
                console.log('[RUMBLE-MONETIZED] Error on video ' + index + ': ' + e.message);
            }
        });
        
        const playSelectors = [
            'button[aria-label*="play" i]',
            'button[title*="play" i]',
            '.media-play-button',
            '.play-button',
            '[class*="PlayButton"]',
            '[class*="play-button"]',
            '[data-action="play"]',
            'button[type="button"]',
            '.vjs-big-play-button',
            'div[role="button"]'
        ];
        
        playSelectors.forEach(selector => {
            try {
                const buttons = document.querySelectorAll(selector);
                buttons.forEach(btn => {
                    if (btn && btn.offsetParent !== null) {
                        btn.click();
                        console.log('[RUMBLE-MONETIZED] Clicked: ' + selector);
                    }
                });
            } catch(e) {}
        });
        
        videos.forEach((v, i) => {
            try {
                v.click();
                console.log('[RUMBLE-MONETIZED] Clicked video ' + i);
            } catch(e) {}
        });
        
        if (videos.length > 0) {
            try {
                videos[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            } catch(e) {}
        }
    }
    
    try {
        Object.defineProperty(document, 'hidden', {
            configurable: true,
            get: () => false
        });
        Object.defineProperty(document, 'visibilityState', {
            configurable: true,
            get: () => 'visible'
        });
        console.log('[RUMBLE-MONETIZED] Visibility overridden');
    } catch(e) {}
    
    window.addEventListener('blur', (e) => e.stopImmediatePropagation(), true);
    window.addEventListener('focus', (e) => e.stopImmediatePropagation(), true);
    
    tryPlay();
    
    let interval = setInterval(() => {
        if (playAttempts >= maxAttempts) {
            clearInterval(interval);
            console.log('[RUMBLE-MONETIZED] Max attempts reached');
            return;
        }
        
        const videos = document.querySelectorAll('video');
        let anyPlaying = false;
        
        videos.forEach(v => {
            if (!v.paused && v.currentTime > 0) {
                anyPlaying = true;
            }
        });
        
        if (anyPlaying) {
            console.log('[RUMBLE-MONETIZED] ✅✅✅ Video confirmed playing, stopping attempts');
            clearInterval(interval);
        } else {
            tryPlay();
        }
    }, 500);
    
    const observer = new MutationObserver(() => tryPlay());
    observer.observe(document.body, { childList: true, subtree: true });
    
    ['DOMContentLoaded', 'load', 'canplay', 'loadedmetadata'].forEach(event => {
        window.addEventListener(event, tryPlay);
    });
    
    console.log('[RUMBLE-MONETIZED] ✅ Script fully activated');
})();
"""

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
            'confirmed_playing': 0,
            'total_cycles': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def check_resources(self):
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()
        ram_available_gb = memory.available / (1024 ** 3)
        ram_total_gb = memory.total / (1024 ** 3)
        
        logger.info("=" * 70)
        logger.info("🖥️  SYSTEM RESOURCES")
        logger.info("=" * 70)
        logger.info(f"💾 Total RAM: {ram_total_gb:.2f} GB")
        logger.info(f"💾 Available RAM: {ram_available_gb:.2f} GB")
        logger.info(f"🔧 CPU Cores: {cpu_count}")
        logger.info(f"📊 Target Tabs: {self.num_tabs}")
        logger.info("=" * 70)
    
    async def inject_autoplay(self, page):
        try:
            await page.evaluate(AUTOPLAY_SCRIPT)
            return True
        except Exception as e:
            logger.error(f"Injection failed: {str(e)[:80]}")
            return False
    
    async def wait_for_playback(self, page, tab_index, max_wait=15):
        logger.info(f"⏳ Tab {tab_index + 1}: Waiting for playback (max {max_wait}s)...")
        
        for i in range(max_wait):
            try:
                is_playing = await page.evaluate("""
                    () => {
                        const videos = document.querySelectorAll('video');
                        for (let v of videos) {
                            if (!v.paused && v.currentTime > 0 && v.readyState >= 3) {
                                return {
                                    playing: true,
                                    time: v.currentTime,
                                    ready: v.readyState,
                                    duration: v.duration
                                };
                            }
                        }
                        return { playing: false };
                    }
                """)
                
                if is_playing['playing']:
                    logger.info(f"✅ Tab {tab_index + 1}: Confirmed playing after {i+1}s!")
                    logger.info(f"   Time: {is_playing['time']:.1f}s / {is_playing['duration']:.1f}s")
                    return True
                
            except:
                pass
            
            await asyncio.sleep(1)
        
        logger.warning(f"⚠️  Tab {tab_index + 1}: Playback not confirmed after {max_wait}s")
        return False
    
    async def open_tab(self, url, tab_index):
        try:
            context = await self.browser.new_context(
                viewport=random.choice(VIEWPORTS),
                user_agent=random.choice(USER_AGENTS),
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            page = await context.new_page()
            
            page.on("console", lambda msg: 
                logger.debug(f"[Tab {tab_index + 1}] {msg.text}") if 'RUMBLE-MONETIZED' in msg.text else None
            )
            
            logger.info(f"🌐 Tab {tab_index + 1}: Loading {url[:70]}...")
            
            await page.goto(url, wait_until='networkidle', timeout=90000)
            await asyncio.sleep(4)
            
            logger.info(f"💉 Tab {tab_index + 1}: Injecting autoplay...")
            await self.inject_autoplay(page)
            
            is_confirmed = await self.wait_for_playback(page, tab_index, max_wait=15)
            
            if is_confirmed:
                logger.info(f"✅✅✅ Tab {tab_index + 1}: MONETIZED VIDEO PLAYING!")
                self.stats['confirmed_playing'] += 1
            else:
                logger.warning(f"⚠️  Tab {tab_index + 1}: Could not confirm playback")
                logger.info(f"   (Counting as view anyway - script may still work)")
            
            self.stats['total_views'] += 1
            return context, page
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_index + 1}: {str(e)[:120]}")
            self.stats['errors'] += 1
            return None, None
    
    async def close_tab(self, context, page, tab_index):
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            logger.info(f"🗑️  Tab {tab_index + 1}: Closed")
        except:
            pass
    
    async def cycle_tab(self, old_context, old_page, tab_index):
        try:
            await asyncio.sleep(random.uniform(0.5, 2))
            logger.info(f"🔄 Tab {tab_index + 1}: Cycling...")
            
            await self.close_tab(old_context, old_page, tab_index)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            url = random.choice(self.video_urls)
            return await self.open_tab(url, tab_index)
            
        except Exception as e:
            logger.error(f"❌ Cycle error: {str(e)[:120]}")
            self.stats['errors'] += 1
            return None, None
    
    def print_stats(self):
        runtime = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        memory = psutil.virtual_memory()
        
        if runtime > 0:
            views_per_hour = (self.stats['total_views'] / runtime) * 60
            views_per_day = views_per_hour * 24
        else:
            views_per_hour = views_per_day = 0
        
        try:
            process = psutil.Process(os.getpid())
            process_ram_gb = process.memory_info().rss / (1024 ** 3)
        except:
            process_ram_gb = 0
        
        success_rate = (self.stats['confirmed_playing'] / max(self.stats['total_views'], 1)) * 100
        
        logger.info("=" * 70)
        logger.info("📊 STATISTICS")
        logger.info("=" * 70)
        logger.info(f"⏱️  Runtime: {runtime:.1f} min ({runtime/60:.1f} hrs)")
        logger.info(f"📺 Active Tabs: {len(self.pages)}/{self.num_tabs}")
        logger.info(f"👁️  Total Views: {self.stats['total_views']}")
        logger.info(f"✅ Confirmed Playing: {self.stats['confirmed_playing']} ({success_rate:.0f}%)")
        logger.info(f"🔄 Cycles: {self.stats['total_cycles']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info(f"💾 Bot RAM: {process_ram_gb:.2f} GB")
        logger.info(f"💾 System RAM: {memory.percent}%")
        logger.info(f"")
        logger.info(f"💰 MONETIZATION PROJECTION:")
        logger.info(f"   Views/day: {views_per_day:,.0f}")
        logger.info(f"   Confirmed/day: {(self.stats['confirmed_playing']/max(runtime,0.1))*60*24:,.0f}")
        logger.info("=" * 70)
    
    async def cycle_all_tabs(self):
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 CYCLE {self.stats['total_cycles'] + 1}")
        logger.info(f"{'='*70}\n")
        
        new_contexts = []
        new_pages = []
        
        for i in range(len(self.pages)):
            old_ctx = self.contexts[i] if i < len(self.contexts) else None
            old_pg = self.pages[i] if i < len(self.pages) else None
            
            new_ctx, new_pg = await self.cycle_tab(old_ctx, old_pg, i)
            
            if new_ctx and new_pg:
                new_contexts.append(new_ctx)
                new_pages.append(new_pg)
            
            await asyncio.sleep(random.uniform(1, 2))
        
        self.contexts = new_contexts
        self.pages = new_pages
        self.stats['total_cycles'] += 1
        
        logger.info(f"\n✅ Cycle complete: {len(self.pages)} active\n")
        self.print_stats()
    
    async def cycle_loop(self):
        while True:
            interval = random.uniform(self.reload_interval * 0.9, self.reload_interval * 1.1)
            logger.info(f"\n⏰ Next cycle: {interval:.0f}s ({interval/60:.1f} min)")
            await asyncio.sleep(interval)
            
            if len(self.pages) > 0:
                await self.cycle_all_tabs()
            else:
                logger.warning("No active tabs to cycle!")
    
    async def run(self):
        self.check_resources()
        
        logger.info("\n" + "=" * 70)
        logger.info("💰 RUMBLE MONETIZED BOT STARTING")
        logger.info("=" * 70)
        logger.info("Strategy: Direct monetized URLs for revenue")
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
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            logger.info("📂 Opening monetized video tabs...\n")
            
            batch_size = 2
            for batch_start in range(0, self.num_tabs, batch_size):
                batch_end = min(batch_start + batch_size, self.num_tabs)
                
                tasks = [
                    self.open_tab(random.choice(self.video_urls), i)
                    for i in range(batch_start, batch_end)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for ctx, pg in results:
                    if ctx and pg and not isinstance(ctx, Exception):
                        self.contexts.append(ctx)
                        self.pages.append(pg)
                
                logger.info(f"Progress: {len(self.pages)}/{self.num_tabs}\n")
                await asyncio.sleep(3)
            
            logger.info(f"\n✅ Setup complete: {len(self.pages)} tabs\n")
            self.print_stats()
            
            logger.info("\n🔁 Starting cycle loop...\n")
            
            try:
                await self.cycle_loop()
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping...")
            finally:
                for i, (ctx, pg) in enumerate(zip(self.contexts, self.pages)):
                    await self.close_tab(ctx, pg, i)
                await self.browser.close()


if __name__ == "__main__":
    from config import VIDEO_URLS, RELOAD_INTERVAL, NUM_TABS
    
    bot = RumbleBot(VIDEO_URLS, RELOAD_INTERVAL, NUM_TABS)
    asyncio.run(bot.run())
