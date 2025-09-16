# Language Configuration Guide

## Overview

The TradingAgents platform provides comprehensive multilingual support for all analysis reports and system interactions. The news analyst and all other agents support language configuration to generate reports in your preferred language.

## Supported Languages

The platform supports 16 languages with proper localization:

| Language Code | Language Name | Native Name |
|---------------|---------------|-------------|
| `zh-CN` | Simplified Chinese | 简体中文 |
| `zh-TW` | Traditional Chinese | 繁體中文 |
| `en-US` | English | English |
| `ja-JP` | Japanese | 日本語 |
| `ko-KR` | Korean | 한국어 |
| `fr-FR` | French | Français |
| `de-DE` | German | Deutsch |
| `es-ES` | Spanish | Español |
| `it-IT` | Italian | Italiano |
| `pt-PT` | Portuguese | Português |
| `pt-BR` | Brazilian Portuguese | Português (Brasil) |
| `ru-RU` | Russian | Русский |
| `ar-SA` | Arabic | العربية |
| `hi-IN` | Hindi | हिन्दी |
| `th-TH` | Thai | ไทย |
| `vi-VN` | Vietnamese | Tiếng Việt |

## Configuration Methods

### 1. User Interface Configuration

Access language settings through the Settings page:

1. Navigate to **Settings** → **Language Settings**
2. Configure two language options:
   - **Default Language**: System interface language
   - **Report Language**: Analysis report output language
3. Choose from:
   - `auto`: Automatic detection based on browser settings
   - Any of the supported language codes above

### 2. Environment Variables

Set system-wide language defaults using environment variables:

```bash
# Default system language
export DEFAULT_LANGUAGE="zh-CN"

# Report output language
export REPORT_LANGUAGE="zh-CN"
```

### 3. HTTP Headers

The system automatically detects language preferences from HTTP `Accept-Language` headers:

```http
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
```

### 4. API Configuration

When creating scheduled analysis tasks, language is automatically detected from:
1. User preferences (highest priority)
2. HTTP Accept-Language headers
3. System defaults (fallback)

## Language Processing Features

### Intelligent Language Normalization

The system accepts various input formats and normalizes them:

```python
# All of these resolve to 'zh-CN':
"zh"
"chinese"
"zh_cn" 
"zh-CN"
"simplified chinese"
```

### Automatic Fallback

If an unsupported language is requested:
1. System logs a warning
2. Falls back to English (`en-US`)
3. Continues processing without errors

### Browser Language Detection

The platform parses complex `Accept-Language` headers:
- Respects quality values (`q` parameters)
- Finds the best matching supported language
- Falls back gracefully for unsupported languages

## News Analyst Language Support

The news analyst has enhanced language support with:

### Comprehensive System Prompts

Each language receives culturally appropriate instructions:

**English Example:**
```
Please provide all analysis reports and conclusions in English.
```

**Chinese Example:**
```
请使用简体中文输出所有分析报告和结论。
```

**Japanese Example:**
```
すべての分析レポートと結論を日本語で出力してください。
```

### Enhanced Report Structure

The news analyst generates structured reports with:
- Language-appropriate section headers
- Culturally relevant analysis perspectives
- Localized financial terminology
- Proper date and number formatting

### Multi-source News Analysis

Supports news analysis from various sources in different languages:
- Global news aggregation
- Regional market perspectives
- Cross-cultural market sentiment analysis

## Implementation Details

### Language Utilities Module

The `tradingagents.agents.utils.language_utils` module provides:

```python
from tradingagents.agents.utils.language_utils import (
    get_language_instruction,
    normalize_language_code,
    is_language_supported,
    get_language_display_name,
    detect_language_from_accept_header,
    get_language_config_for_agent,
    get_supported_languages
)

# Get language instruction for AI models
instruction = get_language_instruction("zh-CN")

# Normalize various language code formats
normalized = normalize_language_code("chinese")  # Returns "zh-CN"

# Check language support
supported = is_language_supported("ja-JP")  # Returns True

# Get display name
display = get_language_display_name("ko-KR")  # Returns "한국어"

# Detect from HTTP headers
lang = detect_language_from_accept_header("zh-CN,zh;q=0.9,en;q=0.8")

# Get configuration for agents
lang_code, instruction = get_language_config_for_agent(config)
```

### Agent Integration

All agents use the centralized language configuration:

```python
from tradingagents.agents.utils.language_utils import get_language_config_for_agent

def create_news_analyst(llm, toolkit, polygon_toolkit, config=None):
    def news_analyst_node(state):
        # Get language configuration
        effective_config = config or toolkit.config
        language_code, language_instruction = get_language_config_for_agent(effective_config)
        
        # Use language instruction in system message
        system_message = f"Your analysis instructions... {language_instruction}"
```

## Best Practices

### For Developers

1. **Always use language utilities**: Don't hardcode language logic
2. **Handle fallbacks gracefully**: Ensure the system works even with invalid language codes
3. **Test with multiple languages**: Verify functionality across different language settings
4. **Log language decisions**: Help with debugging and user support

### For Users

1. **Set preferences once**: Configure your preferred languages in Settings
2. **Use 'auto' for convenience**: Let the system detect your browser language
3. **Test with sample reports**: Verify language output meets your needs
4. **Provide feedback**: Report any language-specific issues

### For Administrators

1. **Monitor language usage**: Track which languages are most requested
2. **Configure environment defaults**: Set appropriate system-wide defaults
3. **Review logs**: Check for unsupported language requests
4. **Update documentation**: Keep language support information current

## Troubleshooting

### Common Issues

**Reports not in expected language:**
1. Check user preferences in Settings
2. Verify browser language settings
3. Review system environment variables
4. Check application logs for warnings

**Language not supported:**
1. Verify the language code format
2. Check the supported languages list
3. Use the closest supported alternative
4. Submit a feature request for new languages

**Mixed language output:**
1. Ensure consistent configuration across all settings
2. Clear browser cache and cookies
3. Restart the application
4. Check for conflicting environment variables

### Debug Commands

```bash
# Test language utilities
uv run python -c "
from tradingagents.agents.utils.language_utils import *
print('Supported:', get_supported_languages())
print('Normalized zh:', normalize_language_code('zh'))
print('Instruction:', get_language_instruction('zh-CN'))
"

# Check current configuration
uv run python -c "
from tradingagents.default_config import DEFAULT_CONFIG
print('Default language:', DEFAULT_CONFIG['default_language'])
print('Report language:', DEFAULT_CONFIG['report_language'])
"
```

## API Reference

### Language Configuration Endpoints

**GET /system/config**
- Returns current language configuration
- Includes supported languages list

**POST /system/preferences**
- Updates user language preferences
- Accepts `default_language` and `report_language` parameters

### Language Detection Headers

The system respects standard HTTP language headers:
- `Accept-Language`: Primary language preference detection
- `Content-Language`: For API request content language

## Future Enhancements

### Planned Features

1. **Dynamic language switching**: Change language without restart
2. **Regional variants**: Support for country-specific language variants
3. **Custom translations**: User-defined terminology translations
4. **Language learning**: AI adaptation to user language preferences
5. **Voice synthesis**: Text-to-speech in multiple languages

### Contributing New Languages

To add support for a new language:

1. Add language code and instruction to `language_instructions` dictionary
2. Add normalization mappings in `normalize_language_code()`
3. Update `SUPPORTED_LANGUAGES` dictionary
4. Add UI options in frontend settings
5. Test thoroughly with sample reports
6. Update documentation

Example contribution:
```python
# In language_utils.py
language_instructions = {
    # ... existing languages ...
    "nl-NL": "Gelieve alle analyserapporten en conclusies in het Nederlands te verstrekken.",
}

SUPPORTED_LANGUAGES = {
    # ... existing languages ...
    "nl-NL": "Nederlands",
}
```

## Conclusion

The TradingAgents platform provides robust multilingual support with intelligent language detection, comprehensive fallback mechanisms, and seamless integration across all components. The news analyst and all other agents fully support this language configuration system, ensuring users receive analysis reports in their preferred language with appropriate cultural context and terminology.