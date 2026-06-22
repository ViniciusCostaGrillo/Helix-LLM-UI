import os
from datetime import datetime
from typing import Any, Dict
from crawl4ai import AsyncWebCrawler
from backend.crawler.base import BaseCrawlerEngine
from backend.utils.custom_logger import setup_logger

logger = setup_logger("crawler.crawl4ai")


class Crawl4AIEngine(BaseCrawlerEngine):
    """Crawl4AI Scraper Engine.
    
    Crawls websites and outputs cleaned markdown and text suitable for RAG parsing.
    """

    async def crawl(self, url: str, output_dir: str) -> Dict[str, Any]:
        logger.info(f"Starting Crawl4AI crawl for: {url}")
        os.makedirs(output_dir, exist_ok=True)

        markdown_path = os.path.join(output_dir, "page.md")
        html_path = os.path.join(output_dir, "page.html")

        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)

                # Save extracted markdown
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(result.markdown)

                # Save raw HTML content
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(result.html)

            metadata = {
                "url": url,
                "engine": "crawl4ai",
                "crawled_at": datetime.utcnow().isoformat(),
                "success": result.success,
            }

            logger.info(f"Crawl4AI crawl completed successfully for: {url}")
            return {
                "screenshot_path": None,
                "html_path": html_path,
                "markdown_path": markdown_path,
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"Crawl4AI crawl failed for {url}: {e}", exc_info=True)
            raise
