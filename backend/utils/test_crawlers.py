import os
import sys
import asyncio
from dotenv import load_dotenv
from backend.crawler.playwright_engine import PlaywrightEngine
from backend.crawler.crawl4ai_engine import Crawl4AIEngine
from backend.crawler.firecrawl_engine import FirecrawlEngine

# Load local environment variables (.env)
load_dotenv()

async def run_crawler_tests():
    print("Running Crawler Engines validation tests...")
    url = "https://example.com"
    base_output = "storage/test_crawl"
    success = True

    # 1. Test Playwright Engine
    print("\n--- Testing Playwright Engine ---")
    pw_dir = os.path.join(base_output, "playwright")
    try:
        pw_engine = PlaywrightEngine()
        res = await pw_engine.crawl(url, pw_dir)
        
        assert os.path.exists(res["screenshot_path"]), "Playwright screenshot missing"
        assert os.path.exists(res["html_path"]), "Playwright html missing"
        assert res["metadata"]["engine"] == "playwright", "Playwright engine metadata incorrect"
        
        print("PASS - Playwright Engine")
        print(f"  Screenshot: {res['screenshot_path']}")
        print(f"  HTML: {res['html_path']}")
    except Exception as e:
        print(f"FAIL - Playwright Engine ({e})")
        success = False

    # 2. Test Crawl4AI Engine
    print("\n--- Testing Crawl4AI Engine ---")
    c4_dir = os.path.join(base_output, "crawl4ai")
    try:
        c4_engine = Crawl4AIEngine()
        res = await c4_engine.crawl(url, c4_dir)
        
        assert os.path.exists(res["html_path"]), "Crawl4AI html missing"
        assert os.path.exists(res["markdown_path"]), "Crawl4AI markdown missing"
        assert res["metadata"]["engine"] == "crawl4ai", "Crawl4AI engine metadata incorrect"
        
        print("PASS - Crawl4AI Engine")
        print(f"  HTML: {res['html_path']}")
        print(f"  Markdown: {res['markdown_path']}")
    except Exception as e:
        print(f"FAIL - Crawl4AI Engine ({e})")
        success = False

    # 3. Test Firecrawl Engine
    print("\n--- Testing Firecrawl Engine ---")
    fc_dir = os.path.join(base_output, "firecrawl")
    try:
        # Firecrawl requires a valid API key (which is set in our .env)
        fc_engine = FirecrawlEngine()
        res = await fc_engine.crawl(url, fc_dir)
        
        assert os.path.exists(res["html_path"]), "Firecrawl html missing"
        assert os.path.exists(res["markdown_path"]), "Firecrawl markdown missing"
        assert res["metadata"]["engine"] == "firecrawl", "Firecrawl engine metadata incorrect"
        
        print("PASS - Firecrawl Engine")
        print(f"  HTML: {res['html_path']}")
        print(f"  Markdown: {res['markdown_path']}")
    except Exception as e:
        print(f"FAIL - Firecrawl Engine ({e})")
        # Do not fail the whole suite if it is just a rate-limiting or key usage issue,
        # but print warning
        print("  Warning: Firecrawl API check failed. Please check if key is valid or rate limited.")
        # We will not mark the whole run as failed because Firecrawl API depends on third-party quotas
        # but let's let the user know

    if success:
        print("\nAll local crawler engines passed tests successfully!")
        sys.exit(0)
    else:
        print("\nSome crawler engine tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_crawler_tests())
