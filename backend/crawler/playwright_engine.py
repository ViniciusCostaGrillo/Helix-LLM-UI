import os
from datetime import datetime
from typing import Any, Dict
from playwright.async_api import async_playwright
from backend.crawler.base import BaseCrawlerEngine
from backend.utils.custom_logger import setup_logger

logger = setup_logger("crawler.playwright")


class PlaywrightEngine(BaseCrawlerEngine):
    """Playwright Scraper Engine.
    
    Launches a headless browser to render JavaScript, fetch content, and take screenshots.
    """

    async def crawl(self, url: str, output_dir: str) -> Dict[str, Any]:
        logger.info(f"Starting Playwright crawl for: {url}")
        os.makedirs(output_dir, exist_ok=True)

        screenshot_path = os.path.join(output_dir, "screenshot.png")
        html_path = os.path.join(output_dir, "page.html")

        try:
            async with async_playwright() as p:
                # Launch headless browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Set viewport size
                await page.set_viewport_size({"width": 1280, "height": 800})

                # Navigate and wait for network activity to settle
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Capture full-page screenshot
                await page.screenshot(path=screenshot_path, full_page=True)

                # Capture HTML page content
                html_content = await page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                title = await page.title()
                await browser.close()

            metadata = {
                "title": title,
                "url": url,
                "engine": "playwright",
                "crawled_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Playwright crawl completed successfully for: {url}")
            return {
                "screenshot_path": screenshot_path,
                "html_path": html_path,
                "markdown_path": None,
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"Playwright crawl failed for {url}: {e}", exc_info=True)
            raise
