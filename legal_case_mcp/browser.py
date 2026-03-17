from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from . import config

_playwright = None
_browser: Browser | None = None
_context: BrowserContext | None = None


async def _ensure_browser() -> BrowserContext:
    global _playwright, _browser, _context
    if _context is not None:
        return _context
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=config.HEADLESS)
    _context = await _browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        locale="ko-KR",
    )
    _context.set_default_timeout(config.TIMEOUT_MS)
    return _context


async def get_page() -> Page:
    ctx = await _ensure_browser()
    page = await ctx.new_page()
    return page


async def close_browser() -> None:
    global _playwright, _browser, _context
    if _context:
        await _context.close()
        _context = None
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
