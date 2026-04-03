"""
Agent orchestrator — sets up and runs the OpenAI Agent SDK weather agent.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def run_agent(user_message: str) -> str:
    """
    Run the weather agent with a user message and return the response.
    Uses the OpenAI Agent SDK for autonomous tool calling.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return (
            "The AI agent is not configured. "
            "Please set the OPENAI_API_KEY in your .env file."
        )

    try:
        from agents import Agent, Runner
        import json

        from .prompts import SYSTEM_PROMPT
        from . import tools

        # Define the agent with tool functions
        agent = Agent(
            name="Weather Assistant",
            instructions=SYSTEM_PROMPT,
            tools=[
                tools.get_weather,
                tools.get_forecast,
                tools.search_location,
                tools.get_videos,
                tools.query_history,
            ],
        )

        # Run synchronously
        result = Runner.run_sync(agent, user_message)

        return result.final_output

    except ImportError as e:
        logger.error("OpenAI Agents SDK not available: %s", e)
        return "AI agent dependencies are not installed."
    except Exception as e:
        logger.error("Agent execution failed: %s", e)
        return f"Agent encountered an error: {str(e)}"
