"""
NexusClaw Browser Automation — Playwright-based web interaction.
"""
import os, asyncio, json
from pathlib import Path

SCREENSHOT_DIR = Path("/home/greench/nexusclaw/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

class BrowserTools:
    def __init__(self):
        self.page = None
        self.context = None
        self.browser = None
    
    async def _get_page(self):
        if self.page is None:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            self.browser = await pw.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            self.page = await self.context.new_page()
        return self.page
    
    async def navigate(self, url: str) -> dict:
        try:
            page = await self._get_page()
            response = await page.goto(url, timeout=15000)
            title = await page.title()
            return {"ok": True, "url": url, "title": title, "status": response.status if response else None}
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url}
    
    async def screenshot(self, name: str = "") -> dict:
        try:
            page = await self._get_page()
            name = name or f"screenshot_{len(list(SCREENSHOT_DIR.glob('*.png')))}"
            path = SCREENSHOT_DIR / f"{name}.png"
            await page.screenshot(path=str(path), full_page=True)
            return {"ok": True, "path": str(path), "url": page.url}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def click(self, selector: str) -> dict:
        try:
            page = await self._get_page()
            await page.click(selector, timeout=5000)
            return {"ok": True, "selector": selector}
        except Exception as e:
            return {"ok": False, "error": str(e), "selector": selector}
    
    async def type_text(self, selector: str, text: str) -> dict:
        try:
            page = await self._get_page()
            await page.fill(selector, text, timeout=5000)
            return {"ok": True, "selector": selector, "chars": len(text)}
        except Exception as e:
            return {"ok": False, "error": str(e), "selector": selector}
    
    async def evaluate(self, js: str) -> dict:
        try:
            page = await self._get_page()
            result = await page.evaluate(js)
            return {"ok": True, "result": str(result)[:2000]}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def get_text(self, selector: str) -> dict:
        try:
            page = await self._get_page()
            text = await page.text_content(selector)
            return {"ok": True, "selector": selector, "text": text[:5000]}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def close(self) -> dict:
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

# Sync wrappers
def navigate(url: str) -> dict:
    return asyncio.get_event_loop().run_until_complete(BrowserTools().navigate(url))

def screenshot(name: str = "") -> dict:
    return asyncio.get_event_loop().run_until_complete(BrowserTools().screenshot(name))

def click(selector: str) -> dict:
    return asyncio.get_event_loop().run_until_complete(BrowserTools().click(selector))

def type_text(selector: str, text: str) -> dict:
    return asyncio.get_event_loop().run_until_complete(BrowserTools().type_text(selector, text))

def close() -> dict:
    return asyncio.get_event_loop().run_until_complete(BrowserTools().close())
