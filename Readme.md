# 🚀 Rumble View Bot

Automated Rumble video viewer using close & reopen tab strategy.

## Features

- ✅ Opens multiple browser tabs
- ✅ Plays videos automatically
- ✅ Cycles tabs (closes & reopens) at intervals
- ✅ Randomized user agents & viewports
- ✅ Resource monitoring
- ✅ Runs 24/7 on Railway

## Environment Variables

Set these in Railway dashboard:

### Required:
- `VIDEO_URL` - Your Rumble video URL
  - Example: `https://rumble.com/v5abc123-my-video.html`

### Optional:
- `VIDEO_URLS` - Multiple videos (comma-separated)
  - Example: `https://rumble.com/v1.html,https://rumble.com/v2.html`
- `NUM_TABS` - Number of tabs (default: 10)
- `RELOAD_INTERVAL` - Seconds between cycles (default: 120)

## Deployment

1. Fork/clone this repo
2. Connect to Railway
3. Set environment variables
4. Deploy!

## How It Works

1. Opens N tabs with your video
2. Plays video in each tab
3. After X seconds, closes all tabs
4. Opens fresh tabs (simulates new visitors)
5. Repeats forever

## Expected Performance

- **10 tabs, 2-min cycle**: ~7,200 views/day
- **50 tabs, 2-min cycle**: ~36,000 views/day
- **100 tabs, 2-min cycle**: ~72,000 views/day

## Strategy: Close & Reopen

Unlike traditional reload bots, this:
- Closes entire browser context
- Opens completely fresh tab
- Simulates different visitors
- Harder to detect as automation
- Bypasses rate limits better

## Monitoring

Check Railway logs to see:
- Tabs opening/closing
- View count increasing
- Resource usage
- Cycle statistics

## Legal Notice

This is for educational purposes. Use responsibly and follow Rumble's ToS.
