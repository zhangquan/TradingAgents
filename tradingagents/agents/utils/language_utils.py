"""
Language utilities for TradingAgents.

This module provides common language instruction functions used across all agents.
It supports multiple languages and provides robust error handling for language configuration.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

def normalize_language_code(language_code: str) -> str:
    """
    Normalize language code to standard format.
    
    Args:
        language_code: Input language code (various formats)
        
    Returns:
        str: Normalized language code (e.g., 'zh-CN', 'en-US')
    """
    if not language_code:
        return "en-US"
    
    # Convert to lowercase for processing
    code = language_code.lower().strip()
    
    # Handle common variations and normalizations
    normalization_map = {
        # Chinese variants
        "zh": "zh-CN",
        "zh_cn": "zh-CN", 
        "zh-cn": "zh-CN",
        "chinese": "zh-CN",
        "simplified chinese": "zh-CN",
        "zh_tw": "zh-TW",
        "zh-tw": "zh-TW",
        "traditional chinese": "zh-TW",
        
        # English variants
        "en": "en-US",
        "en_us": "en-US",
        "en-us": "en-US",
        "english": "en-US",
        "american english": "en-US",
        
        # Japanese
        "ja": "ja-JP",
        "ja_jp": "ja-JP",
        "ja-jp": "ja-JP",
        "japanese": "ja-JP",
        
        # Korean
        "ko": "ko-KR",
        "ko_kr": "ko-KR",
        "ko-kr": "ko-KR",
        "korean": "ko-KR",
        
        # French
        "fr": "fr-FR",
        "fr_fr": "fr-FR",
        "fr-fr": "fr-FR",
        "french": "fr-FR",
        
        # German
        "de": "de-DE",
        "de_de": "de-DE",
        "de-de": "de-DE",
        "german": "de-DE",
        
        # Spanish
        "es": "es-ES",
        "es_es": "es-ES",
        "es-es": "es-ES",
        "spanish": "es-ES",
        
        # Italian
        "it": "it-IT",
        "it_it": "it-IT",
        "it-it": "it-IT",
        "italian": "it-IT",
        
        # Portuguese
        "pt": "pt-PT",
        "pt_pt": "pt-PT",
        "pt-pt": "pt-PT",
        "portuguese": "pt-PT",
        "pt_br": "pt-BR",
        "pt-br": "pt-BR",
        "brazilian portuguese": "pt-BR",
        
        # Russian
        "ru": "ru-RU",
        "ru_ru": "ru-RU",
        "ru-ru": "ru-RU",
        "russian": "ru-RU",
        
        # Arabic
        "ar": "ar-SA",
        "ar_sa": "ar-SA",
        "ar-sa": "ar-SA",
        "arabic": "ar-SA",
        
        # Hindi
        "hi": "hi-IN",
        "hi_in": "hi-IN",
        "hi-in": "hi-IN",
        "hindi": "hi-IN",
        
        # Thai
        "th": "th-TH",
        "th_th": "th-TH",
        "th-th": "th-TH",
        "thai": "th-TH",
        
        # Vietnamese
        "vi": "vi-VN",
        "vi_vn": "vi-VN",
        "vi-vn": "vi-VN",
        "vietnamese": "vi-VN",
    }
    
    normalized = normalization_map.get(code)
    if normalized:
        return normalized
    
    # If no mapping found, check if it's already in correct format
    if len(code) == 5 and code[2] == '-':
        # Convert to proper case (e.g., 'zh-cn' -> 'zh-CN')
        parts = code.split('-')
        return f"{parts[0].lower()}-{parts[1].upper()}"
    
    # Default fallback
    logger.warning(f"Could not normalize language code: {language_code}, using en-US")
    return "en-US"

def get_language_instruction(language_code: str) -> str:
    """
    Get language instruction based on language code.
    
    Args:
        language_code: Language code (e.g., 'zh-CN', 'en-US', 'ja-JP')
        
    Returns:
        str: Language instruction for AI models
    """
    if not language_code or not isinstance(language_code, str):
        logger.warning(f"Invalid language code provided: {language_code}, defaulting to en-US")
        language_code = "en-US"
    
    # Normalize language code
    language_code = normalize_language_code(language_code)
    
    language_instructions = {
        "zh-CN": "请使用简体中文输出所有分析报告和结论。",
        "zh-TW": "請使用繁體中文輸出所有分析報告和結論。",
        "ja-JP": "すべての分析レポートと結論を日本語で出力してください。",
        "ko-KR": "모든 분석 보고서와 결론을 한국어로 출력해주세요.",
        "fr-FR": "Veuillez produire tous les rapports d'analyse et conclusions en français.",
        "de-DE": "Bitte geben Sie alle Analyseberichte und Schlussfolgerungen auf Deutsch aus.",
        "es-ES": "Por favor, produzca todos los informes de análisis y conclusiones en español.",
        "it-IT": "Si prega di fornire tutti i rapporti di analisi e le conclusioni in italiano.",
        "pt-PT": "Por favor, forneça todos os relatórios de análise e conclusões em português.",
        "pt-BR": "Por favor, forneça todos os relatórios de análise e conclusões em português brasileiro.",
        "ru-RU": "Пожалуйста, предоставьте все аналитические отчеты и выводы на русском языке.",
        "ar-SA": "يرجى تقديم جميع التقارير التحليلية والاستنتاجات باللغة العربية.",
        "hi-IN": "कृपया सभी विश्लेषण रिपोर्ट और निष्कर्ष हिंदी में प्रदान करें।",
        "th-TH": "กรุณาจัดทำรายงานการวิเคราะห์และข้อสรุปทั้งหมดเป็นภาษาไทย",
        "vi-VN": "Vui lòng cung cấp tất cả các báo cáo phân tích và kết luận bằng tiếng Việt.",
        "en-US": "Please provide all analysis reports and conclusions in English."
    }
    
    instruction = language_instructions.get(language_code)
    if not instruction:
        logger.warning(f"Language code '{language_code}' not supported, defaulting to English")
        instruction = language_instructions["en-US"]
    
    return instruction


def get_language_instruction_from_config(config: dict) -> str:
    """
    Get language instruction from config dictionary.
    
    Args:
        config: Configuration dictionary containing 'report_language'
        
    Returns:
        str: Language instruction for AI models
    """
    if not config:
        return get_language_instruction("en-US")
    
    report_language = config.get("report_language", "en-US")
    return get_language_instruction(report_language)


# List of supported languages for reference
SUPPORTED_LANGUAGES = {
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文", 
    "en-US": "English",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
    "fr-FR": "Français",
    "de-DE": "Deutsch",
    "es-ES": "Español",
    "it-IT": "Italiano",
    "pt-PT": "Português",
    "pt-BR": "Português (Brasil)",
    "ru-RU": "Русский",
    "ar-SA": "العربية",
    "hi-IN": "हिन्दी",
    "th-TH": "ไทย",
    "vi-VN": "Tiếng Việt"
}

def get_supported_languages() -> Dict[str, str]:
    """
    Get dictionary of all supported languages.
    
    Returns:
        Dict[str, str]: Language code to display name mapping
    """
    return SUPPORTED_LANGUAGES.copy()

def is_language_supported(language_code: str) -> bool:
    """
    Check if a language code is supported.
    
    Args:
        language_code: Language code to check
        
    Returns:
        bool: True if language is supported, False otherwise
    """
    normalized_code = normalize_language_code(language_code)
    return normalized_code in SUPPORTED_LANGUAGES

def get_language_display_name(language_code: str) -> str:
    """
    Get the display name for a language code.
    
    Args:
        language_code: Language code (e.g., 'zh-CN')
        
    Returns:
        str: Display name for the language (e.g., '简体中文')
    """
    normalized_code = normalize_language_code(language_code)
    return SUPPORTED_LANGUAGES.get(normalized_code, "English")

def detect_language_from_accept_header(accept_language_header: str) -> str:
    """
    Detect preferred language from HTTP Accept-Language header.
    
    Args:
        accept_language_header: HTTP Accept-Language header value
        
    Returns:
        str: Best matching supported language code
    """
    if not accept_language_header:
        return "en-US"
    
    # Parse Accept-Language header (simplified parsing)
    languages = []
    for lang_range in accept_language_header.split(','):
        lang_range = lang_range.strip()
        if ';' in lang_range:
            lang, quality = lang_range.split(';', 1)
            try:
                q = float(quality.split('=')[1])
            except (ValueError, IndexError):
                q = 1.0
        else:
            lang, q = lang_range, 1.0
        
        languages.append((lang.strip(), q))
    
    # Sort by quality score (descending)
    languages.sort(key=lambda x: x[1], reverse=True)
    
    # Find first supported language
    for lang, _ in languages:
        normalized = normalize_language_code(lang)
        if is_language_supported(normalized):
            return normalized
    
    return "en-US"

def get_language_config_for_agent(config: Optional[Dict[str, Any]], 
                                  fallback_language: str = "en-US") -> Tuple[str, str]:
    """
    Get language configuration for an agent from config dictionary.
    
    Args:
        config: Configuration dictionary
        fallback_language: Fallback language if none specified in config
        
    Returns:
        Tuple[str, str]: (language_code, language_instruction)
    """
    if not config:
        language_code = fallback_language
    else:
        language_code = config.get("report_language") or config.get("default_language") or fallback_language
    
    # Handle 'auto' setting
    if language_code == "auto":
        language_code = fallback_language
    
    normalized_code = normalize_language_code(language_code)
    instruction = get_language_instruction(normalized_code)
    
    return normalized_code, instruction
