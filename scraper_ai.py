from scrapegraphai.graphs import SmartScraperGraph
from scrapegraphai.utils import cleanup_html
import json
import os
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom exception for rate limiting
class RateLimitError(Exception):
    pass

# Add retry decorator for the scraper execution
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(RateLimitError)
)

def get_platform_specific_prompt(platform, language="en"):
    language_instructions = {
        "en": "Extract information in English.",
        "vi": "Trích xuất thông tin bằng tiếng Việt.",
        "fr": "Extrayez les informations en français.",
        "es": "Extraiga la información en español.",
        "de": "Extrahieren Sie die Informationen auf Deutsch.",
        "zh": "用中文提取信息。",
        "ja": "日本語で情報を抽出してください。",
        "ko": "한국어로 정보를 추출하세요."
    }

    instruction = language_instructions.get(language, "Extract information in English.")
    
    prompts = {
        "facebook": """
        {instruction}
        Extract the following from this Facebook page:
        1. Page description/bio in main.html
        2. Categories, Contact info, Websites and social links, Basic info in about.html
        3. Page transparency in about_profile_transparency.html
        4. Details about the page in about_details.html
        Do not include section headers or numbers in the output. Just provide a clean JSON structure.
        """,
        "x": """
        {instruction}
        Extract the following from this X (Twitter) profile:
        1. Profile information (name, username, bio, website, join date)
        2. Profile stats (following, followers, posts count)
        3. Recent posts/tweets content in main.html
        4. Profile details and highlights
        Do not include section headers or numbers in the output. Just provide a clean JSON structure.
        """,
        "instagram": """
        {instruction}
        Extract the following from this Instagram profile:
        1. Profile information (name, username, bio, website)
        2. Profile stats (posts, followers, following)
        3. Recent posts content in main.html
        4. Profile details and highlights
        Do not include section headers or numbers in the output. Just provide a clean JSON structure.
        """,
        "default": """
        {instruction}
        Extract key information from the page.
        Do not include section headers or numbers in the output. Just provide a clean JSON structure.
        """
    }
    return prompts.get(platform.lower(), f"{instruction} Extract key information from the page.")

def combine_html_files(html_files, base_url):
    combined_content = ""
    
    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Clean up each HTML file
            title, minimized_body, *_ = cleanup_html(
                html_content=html_content,
                base_url=base_url
            )
            
            # Add a separator with the filename
            filename = os.path.basename(html_file)
            combined_content += f"\n\n<!-- Content from {filename} -->\n{minimized_body}"
            
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
    
    return combined_content

def run_scraper_with_retry(html_files, base_url, json_file, platform="facebook", language="en"):
    try:
        # Validate platform
        valid_platforms = ["facebook", "x", "instagram", "default"]
        if platform not in valid_platforms:
            logger.error(f"Invalid platform '{platform}'. Choose from {valid_platforms}.")
            return False

        # Check if all HTML files exist
        for html_file in html_files:
            if not os.path.exists(html_file):
                logger.error(f"HTML file not found: {html_file}")
                return False
            
        # Combine all HTML files into a single source
        combined_source = combine_html_files(html_files, base_url)

        if not combined_source:
            logger.error("No HTML content to process")
            return False

        prompt = get_platform_specific_prompt(platform, language)

        graph_config = {
            "llm": {
                "model": "mistralai/mistral-small-2501",
                "api_key": MISTRAL_API_KEY,
                # "model_tokens": 8192
            }
        }

        # Run the scraper
        logger.info(f"Running scraper for {platform} in {language}...")
        scraper = SmartScraperGraph(
            prompt=prompt, 
            source=combined_source,
            config=graph_config
        )
        result = scraper.run()

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result["content"], f, ensure_ascii=False, indent=2)

        logger.info(f"Successfully extracted data to {json_file}")
        return True

    except Exception as e:
        if "429" in str(e) or "capacity" in str(e).lower():
            logger.warning(f"Rate limit hit, retrying... Error: {e}")
        else:
            logger.error(f"Error in run_scraper: {e}")
            return False

def run_scraper(html_files, base_url, json_file, platform="facebook", language="en"):
    """Wrapper function with retry logic"""
    return run_scraper_with_retry(html_files, base_url, json_file, platform, language)
    
if __name__ == "__main__":
    # run_scraper("diemthongnhat_fb.html", "https://www.facebook.com/diemthongnhat", "diemthongnhat_fb.json", "facebook")
    # Facebook example
    fb_html_files = [
        "mancity/main.html",
        "mancity/about.html", 
        "mancity/about_profile_transparency.html",
        "mancity/about_details.html"
    ]

    run_scraper(
        fb_html_files, 
        "https://www.facebook.com/mancity", 
        "mancity_fb.json", 
        "facebook"
    )

    # X (Twitter) example
    x_html_files = [
        "ManUtd/main.html",
        "ManUtd/with_replies.html"
    ]
    
    run_scraper(
        x_html_files, 
        "https://x.com/ManUtd", 
        "ManUtd_x.json", 
        "x"
    )

    # Instagram example
    ig_html_files = [
        "leomessi/main.html",
    ]
    
    run_scraper(
        ig_html_files, 
        "https://instagram.com/leomessi", 
        "leomessi_ig.json", 
        "instagram"
    )
    