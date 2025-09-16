from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import logging
import os
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Platform-specific path configurations
PLATFORM_PATHS = {
    "facebook": [
        "",
        "/about",
        "/about_profile_transparency",
        "/about_details"
    ],
    "x": [
        ""
    ],
    "instagram": [
        ""
    ],
    "default": [
        ""
    ]
}

def save_rendered_html(url, html_file="page.html", headless=True):
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=headless, slow_mo=200)
                logger.info("Using Chromium browser")
            except Exception as e:
                logger.warning(f"Chromium launch failed, trying Firefox: {e}")
                browser = p.firefox.launch(headless=headless, slow_mo=200)
                logger.info("Using Firefox browser")

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                page.wait_for_timeout(20000)
                # page.wait_for_selector("[data_pagelet]", timeout=30000)
                time.sleep(2)

                html = page.content()

                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"Successfully saved rendered HTML to {html_file}")

            except PlaywrightTimeoutError:
                logger.error(f"Timeout when loading {url}")
                return False
            finally:
                browser.close()

        return True
    except Exception as e:
        logger.error(f"Error in save_rendered_html: {e}")
        return False
    
def detect_platform_from_url(url):
    """
    Detect platform from URL
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    
    if 'facebook.com' in domain:
        return 'facebook'
    elif 'twitter.com' in domain or 'x.com' in domain:
        return 'x'
    elif 'instagram.com' in domain:
        return 'instagram'
    else:
        return 'default'
    
def get_paths_for_platform(platform):
    """
    Get the appropriate paths for a given platform
    """
    return PLATFORM_PATHS.get(platform, PLATFORM_PATHS['default'])
    
def save_multiple_pages(base_url, paths=None, output_dir="html_pages", headless=True, platform=None):
    """
    Save multiple pages from the same domain to HTML files
    
    Args:
        base_url: The base URL (e.g., "https://www.facebook.com/diemthongnhat")
        paths: List of paths to scrape (e.g., ["", "/about", "/about_profile_transparency"])
        output_dir: Directory to save HTML files
        headless: Whether to run browser in headless mode
        platform: Platform name (optional, will auto-detect from URL if not provided)
    """
    # Auto-detect platform if not provided
    if platform is None:
        platform = detect_platform_from_url(base_url)

    # Use provided paths or platform-specific paths
    if paths is None:
        paths = get_paths_for_platform(platform)

    logger.info(f"Using platform: {platform}")

    # Extract page name from URL for directory naming
    parsed_url = urlparse(base_url)
    page_name = parsed_url.path.strip("/").split("/")[-1] if parsed_url.path else parsed_url.netloc.replace("www.", "")
    
    # Create output directory using the page name
    output_dir = page_name
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    for path in paths:
        # Construct full URL
        full_url = base_url.rstrip("/") + path
        
        # Create filename from path
        if path == "" or path == "/":
            filename = "main"
        else:
            filename = path.lstrip("/").replace("/", "_")
            if not filename:
                filename = "main"
            
        html_file = os.path.join(output_dir, f"{filename}.html")
        
        logger.info(f"Scraping {full_url} → {html_file}")
        success = save_rendered_html(full_url, html_file, headless)
        results[full_url] = {"success": success, "file": html_file}
        
        # Add a small delay between requests
        time.sleep(2)
    
    return results

if __name__ == "__main__":
    # save_rendered_html("https://www.facebook.com/diemthongnhat", "diemthongnhat_fb.html")

    # Facebook example
    fb_url = "https://www.facebook.com/mancity"
    fb_results = save_multiple_pages(fb_url, platform="facebook")
    
    # Twitter/X example
    x_url = "https://x.com/ManUtd"
    x_results = save_multiple_pages(x_url, platform="x")
    
    # Instagram example
    ig_url = "https://www.instagram.com/leomessi"
    ig_results = save_multiple_pages(ig_url, platform="instagram")

    # Print results
    print("\nScraping Results:")
    for platform_results in [fb_results, x_results, ig_results]:
        for url, data in platform_results.items():
            status = "✓ SUCCESS" if data["success"] else "✗ FAILED"
            print(f"{status}: {data['file']}")
