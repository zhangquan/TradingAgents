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
    language_instructions = {
        "zh-CN": "请使用简体中文输出所有分析报告和结论。",
        "zh-TW": "請使用繁體中文輸出所有分析報告和結論。",
        "ja-JP": "すべての分析レポートと結論を日本語で出力してください。",
        "ko-KR": "모든 분석 보고서와 결론을 한국어로 출력해주세요.",
        "fr-FR": "Veuillez produire tous les rapports d'analyse et conclusions en français.",
        "de-DE": "Bitte geben Sie alle Analyseberichte und Schlussfolgerungen auf Deutsch aus.",
        "es-ES": "Por favor, produzca todos los informes de análisis y conclusiones en español.",
        "en-US": "Please provide all analysis reports and conclusions in English."
    }
    
    return language_instructions.get(language_code, language_instructions["en-US"])


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
    "zh-TW": "繁体中文", 
    "en-US": "English",
    "ja-JP": "日本語",
    "ko-KR": "한국어",
    "fr-FR": "Français",
    "de-DE": "Deutsch",
    "es-ES": "Español"
}
