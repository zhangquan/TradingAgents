"""
Language utilities for TradingAgents.

This module provides common language instruction functions used across all agents.
"""

def get_language_instruction(language_code: str) -> str:
    """
    Get language instruction based on language code.
    
    Args:
        language_code: Language code (e.g., 'zh-CN', 'en-US', 'ja-JP')
        
    Returns:
        str: Language instruction for AI models
    """
    # Normalize language code
    normalized_code = normalize_language_code(language_code)
    
    language_instructions = {
        "zh-CN": "请使用简体中文输出所有分析报告和结论。请确保使用专业的中文金融术语，保持报告的专业性和可读性。",
        "zh-TW": "請使用繁體中文輸出所有分析報告和結論。請確保使用專業的繁體中文金融術語，保持報告的專業性和可讀性。",
        "ja-JP": "すべての分析レポートと結論を日本語で出力してください。専門的な日本語の金融用語を使用し、レポートの専門性と可読性を保ってください。",
        "ko-KR": "모든 분석 보고서와 결론을 한국어로 출력해주세요. 전문적인 한국어 금융 용어를 사용하여 보고서의 전문성과 가독성을 유지해주세요.",
        "fr-FR": "Veuillez produire tous les rapports d'analyse et conclusions en français. Utilisez une terminologie financière française professionnelle pour maintenir la qualité et la lisibilité des rapports.",
        "de-DE": "Bitte geben Sie alle Analyseberichte und Schlussfolgerungen auf Deutsch aus. Verwenden Sie professionelle deutsche Finanzterminologie, um die Qualität und Lesbarkeit der Berichte zu gewährleisten.",
        "es-ES": "Por favor, produzca todos los informes de análisis y conclusiones en español. Utilice terminología financiera española profesional para mantener la calidad y legibilidad de los informes.",
        "pt-BR": "Por favor, produza todos os relatórios de análise e conclusões em português brasileiro. Use terminologia financeira brasileira profissional para manter a qualidade e legibilidade dos relatórios.",
        "it-IT": "Si prega di produrre tutti i rapporti di analisi e conclusioni in italiano. Utilizzare terminologia finanziaria italiana professionale per mantenere la qualità e leggibilità dei rapporti.",
        "ru-RU": "Пожалуйста, предоставьте все аналитические отчеты и выводы на русском языке. Используйте профессиональную русскую финансовую терминологию для поддержания качества и читаемости отчетов.",
        "ar-SA": "يرجى تقديم جميع تقارير التحليل والاستنتاجات باللغة العربية. استخدم المصطلحات المالية العربية المهنية للحفاظ على جودة ووضوح التقارير.",
        "hi-IN": "कृपया सभी विश्लेषण रिपोर्ट और निष्कर्ष हिंदी में प्रदान करें। रिपोर्ट की गुणवत्ता और पठनीयता बनाए रखने के लिए पेशेवर हिंदी वित्तीय शब्दावली का उपयोग करें।",
        "en-US": "Please provide all analysis reports and conclusions in English. Use professional English financial terminology to maintain the quality and readability of the reports."
    }
    
    return language_instructions.get(normalized_code, language_instructions["en-US"])


def normalize_language_code(language_code: str) -> str:
    """
    Normalize language code to supported format.
    
    Args:
        language_code: Language code (e.g., 'zh', 'en', 'zh-CN')
        
    Returns:
        str: Normalized language code
    """
    if not language_code or language_code.lower() in ['auto', 'detect']:
        return "en-US"
    
    # Convert to lowercase for comparison
    code = language_code.lower().strip()
    
    # Map common language codes to supported ones
    language_map = {
        "zh": "zh-CN",
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
        "zh-hk": "zh-TW",
        "zh-hant": "zh-TW",
        "zh-hans": "zh-CN",
        "en": "en-US",
        "en-us": "en-US",
        "en-gb": "en-US",
        "ja": "ja-JP",
        "ja-jp": "ja-JP",
        "ko": "ko-KR",
        "ko-kr": "ko-KR",
        "fr": "fr-FR",
        "fr-fr": "fr-FR",
        "de": "de-DE",
        "de-de": "de-DE",
        "es": "es-ES",
        "es-es": "es-ES",
        "pt": "pt-BR",
        "pt-br": "pt-BR",
        "pt-pt": "pt-BR",
        "it": "it-IT",
        "it-it": "it-IT",
        "ru": "ru-RU",
        "ru-ru": "ru-RU",
        "ar": "ar-SA",
        "ar-sa": "ar-SA",
        "hi": "hi-IN",
        "hi-in": "hi-IN"
    }
    
    return language_map.get(code, "en-US")


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


def detect_language_from_text(text: str) -> str:
    """
    Detect language from text content (basic implementation).
    
    Args:
        text: Text content to analyze
        
    Returns:
        str: Detected language code
    """
    if not text:
        return "en-US"
    
    # Simple language detection based on character patterns
    text_lower = text.lower()
    
    # Chinese detection
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        # Check for Traditional Chinese characters
        if any(char in text for char in ['個', '們', '這', '那', '麼', '麼', '與', '與']):
            return "zh-TW"
        return "zh-CN"
    
    # Japanese detection
    if any('\u3040' <= char <= '\u309f' for char in text) or any('\u30a0' <= char <= '\u30ff' for char in text):
        return "ja-JP"
    
    # Korean detection
    if any('\uac00' <= char <= '\ud7af' for char in text):
        return "ko-KR"
    
    # Arabic detection
    if any('\u0600' <= char <= '\u06ff' for char in text):
        return "ar-SA"
    
    # Hindi detection
    if any('\u0900' <= char <= '\u097f' for char in text):
        return "hi-IN"
    
    # Cyrillic detection
    if any('\u0400' <= char <= '\u04ff' for char in text):
        return "ru-RU"
    
    # European languages detection based on common words
    # Use more specific patterns to avoid false positives
    french_words = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'que', 'pour', 'avec', 'dans', 'sur', 'par', 'une', 'un']
    german_words = ['der', 'die', 'das', 'und', 'ist', 'mit', 'für', 'von', 'zu', 'auf', 'in', 'an', 'bei', 'nach', 'über']
    spanish_words = ['el', 'la', 'los', 'las', 'de', 'del', 'en', 'que', 'por', 'para', 'con', 'sin', 'sobre', 'entre', 'hasta']
    italian_words = ['il', 'la', 'lo', 'gli', 'le', 'di', 'del', 'della', 'e', 'che', 'con', 'per', 'da', 'in', 'su']
    portuguese_words = ['o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'que', 'para', 'com', 'sem', 'sobre', 'entre', 'até']
    
    # Count matches for each language
    french_count = sum(1 for word in french_words if word in text_lower)
    german_count = sum(1 for word in german_words if word in text_lower)
    spanish_count = sum(1 for word in spanish_words if word in text_lower)
    italian_count = sum(1 for word in italian_words if word in text_lower)
    portuguese_count = sum(1 for word in portuguese_words if word in text_lower)
    
    # Return the language with the most matches, but require at least 2 matches
    language_counts = [
        ("fr-FR", french_count),
        ("de-DE", german_count),
        ("es-ES", spanish_count),
        ("it-IT", italian_count),
        ("pt-BR", portuguese_count)
    ]
    
    # Sort by count and return the language with highest count if >= 2
    language_counts.sort(key=lambda x: x[1], reverse=True)
    if language_counts[0][1] >= 2:
        return language_counts[0][0]
    
    return "en-US"


def get_language_specific_news_sources(language_code: str) -> list:
    """
    Get language-specific news sources for better news analysis.
    
    Args:
        language_code: Language code
        
    Returns:
        list: List of recommended news sources for the language
    """
    normalized_code = normalize_language_code(language_code)
    
    news_sources = {
        "zh-CN": [
            "新浪财经", "网易财经", "腾讯财经", "东方财富网", "同花顺", "雪球", "财新网"
        ],
        "zh-TW": [
            "鉅亨網", "經濟日報", "工商時報", "中時電子報", "聯合新聞網", "自由時報"
        ],
        "ja-JP": [
            "日経新聞", "朝日新聞", "読売新聞", "毎日新聞", "東洋経済", "ダイヤモンド"
        ],
        "ko-KR": [
            "조선일보", "중앙일보", "동아일보", "한국경제", "매일경제", "이데일리"
        ],
        "fr-FR": [
            "Les Échos", "Le Figaro", "Le Monde", "La Tribune", "Investir", "Capital"
        ],
        "de-DE": [
            "Handelsblatt", "FAZ", "Süddeutsche Zeitung", "Die Welt", "Manager Magazin", "Capital"
        ],
        "es-ES": [
            "El País", "El Mundo", "Expansión", "Cinco Días", "La Vanguardia", "ABC"
        ],
        "pt-BR": [
            "Valor Econômico", "Folha de S.Paulo", "O Globo", "Estadão", "Exame", "IstoÉ"
        ],
        "it-IT": [
            "Il Sole 24 Ore", "Corriere della Sera", "La Repubblica", "Il Messaggero", "Il Giornale"
        ],
        "ru-RU": [
            "Ведомости", "Коммерсантъ", "РБК", "Газета.Ru", "Lenta.ru", "Известия"
        ],
        "ar-SA": [
            "الاقتصادية", "الرياض", "الشرق الأوسط", "الوطن", "الجزيرة", "العربية"
        ],
        "hi-IN": [
            "बिजनेस स्टैंडर्ड", "द इकोनॉमिक टाइम्स", "मिंट", "फाइनेंशियल एक्सप्रेस", "द हिंदू बिजनेस लाइन"
        ]
    }
    
    return news_sources.get(normalized_code, news_sources["en-US"])


# List of supported languages for reference
SUPPORTED_LANGUAGES = {
    "zh-CN": "简体中文",
    "zh-TW": "繁体中文", 
    "en-US": "English",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
    "fr-FR": "Français",
    "de-DE": "Deutsch",
    "es-ES": "Español",
    "pt-BR": "Português (Brasil)",
    "it-IT": "Italiano",
    "ru-RU": "Русский",
    "ar-SA": "العربية",
    "hi-IN": "हिन्दी"
}
