from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseCrawlerEngine(ABC):
    """Abstract Base Class specifying crawler engine requirements.
    
    All scraper implementations must conform to this interface to satisfy SOLID principles.
    """

    @abstractmethod
    async def crawl(self, url: str, output_dir: str) -> Dict[str, Any]:
        """Crawls a website, saves screenshots and documents, and returns path metadata.

        Args:
            url: The website URL to crawl.
            output_dir: Directory where crawled assets (HTML, markdown, screenshot) should be saved.

        Returns:
            Dict containing path details:
                - "screenshot_path": Path to full page screenshot (or None)
                - "html_path": Path to raw HTML content file
                - "markdown_path": Path to clean markdown content file (or None)
                - "metadata": Dict of metadata details (title, crawled time, status, engine name)
        """
        pass
