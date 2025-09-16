from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.language_utils import (
    get_language_instruction, 
    normalize_language_code, 
    detect_language_from_text,
    get_language_specific_news_sources
)


def create_news_analyst(llm, toolkit, polygon_toolkit, config=None):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # Get language configuration - prefer passed config, fallback to toolkit.config
        effective_config = config or toolkit.config
        report_language = effective_config.get("report_language", "en-US")
        
        # Normalize language code and get language-specific instructions
        normalized_language = normalize_language_code(report_language)
        language_instruction = get_language_instruction(normalized_language)
        
        # Get language-specific news sources for better context
        language_sources = get_language_specific_news_sources(normalized_language)
        
        # If language is set to auto, we'll detect it from news content later
        auto_detect = report_language.lower() in ['auto', 'detect']

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_google_news]
        else:
            tools = [
                toolkit.get_finnhub_news,
                toolkit.get_reddit_news,
                toolkit.get_google_news,
            ]

        # Create language-specific system message
        base_message = "You are a news researcher tasked with analyzing recent news and trends over the past week. Please write a comprehensive report of the current state of the world that is relevant for trading and macroeconomics. Look at news from EODHD, and finnhub to be comprehensive. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
        
        # Add language-specific news sources context
        if language_sources and normalized_language != "en-US":
            sources_context = f" Pay special attention to news from these sources: {', '.join(language_sources[:5])}."
            base_message += sources_context
        
        system_message = (
            base_message
            + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
            + f""" {language_instruction}"""
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
            
            # If auto-detection is enabled, detect language from the report content
            if auto_detect and report:
                detected_language = detect_language_from_text(report)
                if detected_language != normalized_language:
                    # Re-generate the report with the detected language
                    detected_normalized = normalize_language_code(detected_language)
                    detected_instruction = get_language_instruction(detected_normalized)
                    detected_sources = get_language_specific_news_sources(detected_normalized)
                    
                    # Update system message with detected language
                    updated_base_message = base_message
                    if detected_sources and detected_normalized != "en-US":
                        sources_context = f" Pay special attention to news from these sources: {', '.join(detected_sources[:5])}."
                        updated_base_message += sources_context
                    
                    updated_system_message = (
                        updated_base_message
                        + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
                        + f""" {detected_instruction}"""
                    )
                    
                    # Re-run with detected language
                    updated_prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                "You are a helpful AI assistant, collaborating with other assistants."
                                " Use the provided tools to progress towards answering the question."
                                " If you are unable to fully answer, that's OK; another assistant with different tools"
                                " will help where you left off. Execute what you can to make progress."
                                " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                                " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                                " You have access to the following tools: {tool_names}.\n{system_message}"
                                "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
                            ),
                            MessagesPlaceholder(variable_name="messages"),
                        ]
                    )
                    
                    updated_prompt = updated_prompt.partial(system_message=updated_system_message)
                    updated_prompt = updated_prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
                    updated_prompt = updated_prompt.partial(current_date=current_date)
                    updated_prompt = updated_prompt.partial(ticker=ticker)
                    
                    updated_chain = updated_prompt | llm.bind_tools(tools)
                    updated_result = updated_chain.invoke(state["messages"])
                    
                    if len(updated_result.tool_calls) == 0:
                        report = updated_result.content
                        result = updated_result

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node


