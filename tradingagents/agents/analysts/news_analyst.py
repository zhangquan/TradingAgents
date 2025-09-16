from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.language_utils import get_language_config_for_agent


def create_news_analyst(llm, toolkit, polygon_toolkit, config=None):
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # Get language configuration - prefer passed config, fallback to toolkit.config
        effective_config = config or toolkit.config
        language_code, language_instruction = get_language_config_for_agent(effective_config)

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_google_news]
        else:
            tools = [
                toolkit.get_finnhub_news,
                toolkit.get_reddit_news,
                toolkit.get_google_news,
            ]

        system_message = (
            "You are a professional news analyst specializing in financial markets and macroeconomic trends. Your task is to analyze recent news and developments over the past week that could impact trading decisions and market conditions."
            "\n\nYour analysis should include:"
            "\n- Global macroeconomic developments and their market implications"
            "\n- Company-specific news and announcements relevant to the target ticker"
            "\n- Geopolitical events affecting market sentiment"
            "\n- Central bank policies and monetary developments"
            "\n- Industry trends and sector-specific news"
            "\n- Market-moving events and their potential impact"
            "\n\nGuidelines:"
            "\n- Provide detailed, nuanced analysis rather than generic statements"
            "\n- Focus on actionable insights for traders and investors"
            "\n- Cite specific news sources and events when possible"
            "\n- Assess both immediate and longer-term market implications"
            "\n- Consider multiple perspectives and potential scenarios"
            "\n\nFormat your response with clear sections and conclude with a comprehensive Markdown table summarizing key findings, their market impact, and trading implications."
            f"\n\n{language_instruction}"
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

        return {
            "messages": [result],
            "news_report": report,
        }

    return news_analyst_node


