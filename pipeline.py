import argparse
import save_url_to_html
import scraper_ai
import generate_faq
import logging
import os
import time
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLATFORM_MAP = {
    "fb": "facebook",
    "ig": "instagram", 
    "x": "x",
    "df": "default"
}

SUPPORTED_LANGUAGES = ["en", "vi", "es", "fr", "de", "zh", "ja", "ko"]

def run_pipeline(url, plf, out_file=None, language="en", faq_count=10):
    # Validate platform
    valid_platforms = ["fb", "ig", "x", "df"]
    if plf not in valid_platforms:
        logger.error(f"Invalid platform '{plf}'. Choose from {valid_platforms}.")
        return False
    
    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        logger.error(f"Unsupported language '{language}'. Choose from {SUPPORTED_LANGUAGES}.")
        return False
    
    # Validate FAQ count
    if not isinstance(faq_count, int) or faq_count < 1 or faq_count > 50:
        logger.error("FAQ count must be an integer between 1 and 50, got {faq_count}")
        return False
    
    platform = PLATFORM_MAP[plf]

    # 1. Save HTML
    parsed_url = urlparse(url)
    page_name = parsed_url.path.strip("/").split("/")[-1] if parsed_url.path else parsed_url.netloc.replace("www.", "")
    output_dir = page_name
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"[1/3] Saving rendered HTML from {url} → {output_dir}")
    results = save_url_to_html.save_multiple_pages(url, output_dir=output_dir, headless=True, platform=platform)

    if not all(data["success"] for data in results.values()):
        logger.error("Failed to save some HTML pages")
        logger.error("Results: %s", results)
        return False
    
    time.sleep(3)

    # 2. Scrape + clean
    json_file = f"{output_dir}_{plf}_{language}.json"
    logger.info(f"[2/3] Extracting structured data → {json_file}")

    html_files = []
    for result_url, data in results.items():
        if data["success"] and os.path.exists(data["file"]):
            html_files.append(data["file"])

    for html_file in html_files:
        if not os.path.exists(html_file):
            logger.error(f"HTML file not found: {html_file}")
            return False

    if not scraper_ai.run_scraper(html_files, url, json_file, platform=platform, language=language):
        logger.error("Failed to extract data")
        return False
    
    time.sleep(3)

    # 3. Generate FAQ
    if out_file is None:
        out_file = f"{output_dir}_{plf}_{language}_faq.md"

    logger.info(f"[3/3] Generating FAQ → {out_file}")

    if not os.path.exists(json_file):
        logger.error(f"JSON file not found: {json_file}")
        return False

    if not generate_faq.run_faq(json_file, out_file, platform=platform, language=language, faq_count=faq_count):
        logger.error("Failed to generate FAQ")
        return False

    logger.info("Pipeline finished successfully!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FAQ Generation Pipeline")
    parser.add_argument("--url", required=True, help="URL to scrape (facebook, x, instagram)")
    parser.add_argument("--plf", required=True, help="Platform identifier (fb, x, ins)")
    parser.add_argument("--out", required=False, help="Output markdown file (page name without extension)")
    parser.add_argument("--lang", required=False, default="en", help="Language code (en, vi, fr, es, de, zh, ja, ko)")
    parser.add_argument("--cnt", required=False, type=int, default=10, help="Number of FAQs to generate (1-50)")

    args = parser.parse_args()

    success = run_pipeline(args.url, args.plf, args.out, args.lang, args.cnt)
    exit(0 if success else 1)
