import json
import os
import logging
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_language_specific_prompt(language):
    """Get language-specific instructions for FAQ generation"""
    language_prompts = {
        "en": {
            "system": "You are a helpful assistant that generates relevant FAQs based on provided content. You always output valid JSON.",
            "instruction": "Generate questions and answers in English.",
            "count": "Generate exactly {count} FAQs."
        },
        "vi": {
            "system": "Bạn là trợ lý hữu ích tạo các câu hỏi thường gặp dựa trên nội dung được cung cấp. Bạn luôn xuất ra JSON hợp lệ.",
            "instruction": "Tạo câu hỏi và câu trả lời bằng tiếng Việt.",
            "count": "Tạo chính xác {count} câu hỏi thường gặp."
        },
        "fr": {
            "system": "Vous êtes un assistant utile qui génère des FAQ pertinentes basées sur le contenu fourni. Vous produisez toujours un JSON valide.",
            "instruction": "Générez des questions et réponses en français.",
            "count": "Générez exactement {count} FAQ."
        },
        "es": {
            "system": "Eres un asistente útil que genera preguntas frecuentes relevantes basadas en el contenido proporcionado. Siempre produces JSON válido.",
            "instruction": "Genera preguntas y respuestas en español.",
            "count": "Genera exactamente {count} preguntas frecuentes."
        },
        "de": {
            "system": "Sie sind ein hilfreicher Assistent, der relevante FAQs basierend auf bereitgestellten Inhalten generiert. Sie geben immer gültiges JSON aus.",
            "instruction": "Generieren Sie Fragen und Antworten auf Deutsch.",
            "count": "Generieren Sie genau {count} FAQs."
        },
        "zh": {
            "system": "您是一个有用的助手，根据提供的内容生成相关的常见问题解答。您总是输出有效的JSON。",
            "instruction": "用中文生成问题和答案。",
            "count": "生成恰好{count}个常见问题解答。"
        },
        "ja": {
            "system": "あなたは、提供されたコンテンツに基づいて関連するFAQを生成する役立つアシスタントです。常に有効なJSONを出力します。",
            "instruction": "日本語で質問と回答を生成してください。",
            "count": "{count}件のFAQを正確に生成してください。"
        },
        "ko": {
            "system": "제공된 내용을 기반으로 관련 FAQ를 생성하는 유용한 어시스턴트입니다. 항상 유효한 JSON을 출력합니다.",
            "instruction": "한국어로 질문과 답변을 생성하세요.",
            "count": "정확히 {count}개의 FAQ를 생성하세요."
        }
    }
    return language_prompts.get(language, language_prompts["en"])

def clean_json_response(json_text):
    """
    Clean JSON response by removing invalid control characters and markdown formatting
    """
    # Remove markdown code block formatting
    json_text = re.sub(r'^```json\s*', '', json_text)
    json_text = re.sub(r'^```\s*', '', json_text)
    json_text = re.sub(r'\s*```$', '', json_text)
    
    # Remove invalid control characters
    json_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', json_text)

    # Remove trailing commas
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)

    # Ensure proper quoting
    json_text = re.sub(r'([{:,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_text)
    
    return json_text.strip()

def format_content_for_prompt(content, max_depth=3, current_depth=0):
    """
    Recursively format JSON content into a readable string for the prompt
    Handles any JSON structure dynamically
    """
    if current_depth > max_depth:
        return "[Content too deep to display]"
    
    formatted_text = ""
    
    if isinstance(content, dict):
        for key, value in content.items():
            # Skip empty values
            if value is None or value == "":
                continue
                
            # Format the key in a human-readable way
            readable_key = key.replace('_', ' ').title()
            
            if isinstance(value, dict):
                formatted_text += f"{readable_key}:\n"
                formatted_text += format_content_for_prompt(value, max_depth, current_depth + 1)
                formatted_text += "\n"
            elif isinstance(value, list):
                formatted_text += f"{readable_key}:\n"
                for i, item in enumerate(value):
                    if isinstance(item, (dict, list)):
                        formatted_text += f"  {i+1}. "
                        formatted_text += format_content_for_prompt(item, max_depth, current_depth + 1)
                    else:
                        formatted_text += f"  - {item}\n"
                formatted_text += "\n"
            else:
                formatted_text += f"{readable_key}: {value}\n"
    
    elif isinstance(content, list):
        for i, item in enumerate(content):
            if isinstance(item, (dict, list)):
                formatted_text += f"{i+1}. "
                formatted_text += format_content_for_prompt(item, max_depth, current_depth + 1)
            else:
                formatted_text += f"- {item}\n"
    
    else:
        formatted_text += f"{content}\n"
    
    return formatted_text

def run_faq(json_file, out_file, platform, language="en", faq_count=10):
    try:
        # Validate platform
        valid_platforms = ["facebook", "instagram", "x", "default"]
        if platform not in valid_platforms:
            logger.error(f"Invalid platform '{platform}'. Choose from {valid_platforms}.")
            return False
        
        # Validate FAQ count
        if not isinstance(faq_count, int) or faq_count < 1 or faq_count > 50:
            logger.error("FAQ count must be an integer between 1 and 50, got {faq_count}")
            return False
        
        if not os.path.exists(json_file):
            logger.error(f"JSON file not found: {json_file}")
            return False

        with open(json_file, "r", encoding="utf-8") as f:
            content = json.load(f)

        # Format the content for the prompt
        formatted_content = format_content_for_prompt(content)

        platform_context = {
            "facebook": {
                "en": "Facebook page", 
                "vi": "Trang Facebook",
                "fr": "Page Facebook",
                "es": "Página de Facebook",
                "de": "Facebook-Seite",
                "zh": "Facebook页面",
                "ja": "Facebookページ",
                "ko": "Facebook 페이지"
            },
            "instagram": {
                "en": "Instagram profile", 
                "vi": "Hồ sơ Instagram", 
                "fr": "Profil Instagram",
                "es": "Perfil de Instagram",
                "de": "Instagram-Profil",
                "zh": "Instagram个人资料",
                "ja": "Instagramプロファイル",
                "ko": "Instagram 프로필"
            },
            "x": {
                "en": "X (Twitter) profile", 
                "vi": "Hồ sơ X (Twitter)",
                "fr": "Profil X (Twitter)",
                "es": "Perfil de X (Twitter)",
                "de": "X (Twitter)-Profil",
                "zh": "X（Twitter）个人资料",
                "ja": "X（Twitter）プロファイル",
                "ko": "X (Twitter) 프로필"
            }
        }

        lang_prompt = get_language_specific_prompt(language)
        platform_context_text = platform_context.get(platform, {}).get(language, "social media page")
        count_instruction = lang_prompt['count'].format(count=faq_count)

        prompt = f"""
        You are a social media assistant. Based on the following {platform_context_text} content, generate a list of {faq_count} relevant FAQs and answers a visitor might ask.
        
        IMPORTANT:
        - {lang_prompt['instruction']}
        - {count_instruction}
        - Generate questions that can be answered based on the content provided below.
        - Make answers concise but informative, drawing directly from the provided content.
        - Ensure questions are natural and likely to be asked by real users

        Content:
        {formatted_content}

        Format your output as a JSON array like this:
        [
        {{ "question": "Q1", "answer": "A1" }},
        ...
        ]
        Only return JSON, no other text.
        """

        # Choose the LLM
        client = OpenAI(
            base_url="https://api.mistral.ai/v1",
            api_key=MISTRAL_API_KEY,
        )

        response = client.chat.completions.create(
            model="mistral-medium",
            messages=[
                {"role": "system", "content": lang_prompt['system']},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        # Parse the output
        faq_json_text = response.choices[0].message.content.strip()

        # Clean the JSON response
        faq_json_text = clean_json_response(faq_json_text)

        logger.info(f"Cleaned API response: {faq_json_text}")

        # Try to parse the JSON
        try:
            faq_list = json.loads(faq_json_text)
            if len(faq_list) > faq_count:
                faq_list = faq_list[:faq_count]
                logger.info(f"Limited FAQ list to {faq_count} items.")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.info("Extract FAQ content without JSON parsing...")
        
            faq_pattern = r'\{[^{}]*"question"\s*:\s*"[^"]*"[^{}]*"answer"\s*:\s*"[^"]*"[^{}]*\}'
            faq_matches = re.findall(faq_pattern, faq_json_text, re.DOTALL)

            if not faq_matches:
                logger.error("No FAQ content found in response")
                return False
            
            # Save output as markdown directly from the raw text
            with open(out_file, "w", encoding="utf-8") as f:
                f.write("### Frequently Asked Questions\n\n")
                
                question_pattern = r'"question"\s*:\s*"([^"]*)"'
                answer_pattern = r'"answer"\s*:\s*"([^"]*)"'
                
                for i, faq_match in enumerate(faq_matches, 1):
                    question_match = re.search(question_pattern, faq_match)
                    answer_match = re.search(answer_pattern, faq_match)
                    
                    if question_match and answer_match:
                        question = question_match.group(1)
                        answer = answer_match.group(1)
                        f.write(f"**Q{i}. {question}**\n\n")
                        f.write(f"{answer}\n\n")
                    else:
                        logger.warning(f"Could not extract content from FAQ item {i}")
            
            logger.info(f"Successfully generated FAQ in {language}: {out_file}")
            return True

        # Save output as markdown
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"### Frequently Asked Questions\n\n")
            for i, faq in enumerate(faq_list, 1):
                f.write(f"**Q{i}. {faq['question']}**\n\n")
                f.write(f"{faq['answer']}\n\n")

        logger.info(f"Successfully generated FAQ in {language}: {out_file}")
        return True

    except Exception as e:
        logger.error(f"Error in run_faq: {e}")
        return False

if __name__ == "__main__":
    run_faq("mancity_fb.json", "mancity_fb_faq.md", "facebook")
    run_faq("ManUtd_x.json", "ManUtd_x_faq.md", "x")
    run_faq("leomessi_ig.json", "leomessi_ig_faq.md", "instagram")
