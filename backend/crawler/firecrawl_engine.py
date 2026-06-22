import os
from datetime import datetime
from typing import Any, Dict
from firecrawl import FirecrawlApp
from backend.crawler.base import BaseCrawlerEngine
from backend.utils.custom_logger import setup_logger

logger = setup_logger("crawler.firecrawl")


class FirecrawlEngine(BaseCrawlerEngine):
    """Firecrawl Scraper Engine.
    
    Interfaces with Firecrawl API to retrieve clean markdown layouts and HTML files.
    """

    def __init__(self, api_key: str = None):
        # Fallback to configured env variable
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            logger.warning("Firecrawl API Key is missing. Requests will fail if targeting remote API.")

    async def crawl(self, url: str, output_dir: str) -> Dict[str, Any]:
        logger.info(f"Starting Firecrawl crawl for: {url}")
        os.makedirs(output_dir, exist_ok=True)

        markdown_path = os.path.join(output_dir, "page.md")
        html_path = os.path.join(output_dir, "page.html")

        if not self.api_key:
            raise ValueError("Firecrawl API key is required but not configured.")

        try:
            # Initialize SDK client
            app = FirecrawlApp(api_key=self.api_key)

            # Scrape url formats (flat keyword args in v4 SDK)
            scrape_result = app.scrape_url(url, formats=["markdown", "html"])

            # Save markdown content (attributes on Document object)
            markdown_content = getattr(scrape_result, "markdown", "") or ""
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # Save HTML content (fallback to raw_html if html is None)
            html_content = getattr(scrape_result, "html", "") or getattr(scrape_result, "raw_html", "") or ""
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Safely extract metadata fields from Document object
            metadata_obj = getattr(scrape_result, "metadata", None)
            title = ""
            description = ""
            if metadata_obj:
                if hasattr(metadata_obj, "title"):
                    title = metadata_obj.title or ""
                elif isinstance(metadata_obj, dict):
                    title = metadata_obj.get("title", "")
                if hasattr(metadata_obj, "description"):
                    description = metadata_obj.description or ""
                elif isinstance(metadata_obj, dict):
                    description = metadata_obj.get("description", "")

            metadata = {
                "url": url,
                "engine": "firecrawl",
                "crawled_at": datetime.utcnow().isoformat(),
                "title": title,
                "description": description,
            }

            logger.info(f"Firecrawl crawl completed successfully for: {url}")
            return {
                "screenshot_path": None,
                "html_path": html_path,
                "markdown_path": markdown_path,
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"Firecrawl crawl failed for {url}: {e}", exc_info=True)
            raise
