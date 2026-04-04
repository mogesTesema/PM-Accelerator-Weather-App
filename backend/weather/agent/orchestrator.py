"""
Agent orchestrator — sets up and runs the weather agent.

Supports multiple LLM backends in priority order:
1. OpenAI (OPENAI_API_KEY)
2. GitHub Models (GITHUB_OPENAI__API_TOKEN) — free, OpenAI-compatible
3. Groq (GROQ_API_KEY) — free tier, OpenAI-compatible
4. DeepSeek (DEEPSEEK_API_KEY) — budget-friendly, OpenAI-compatible
"""

import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_llm_config() -> dict | None:
    """
    Return {"api_key": ..., "base_url": ..., "model": ...} for the first
    available LLM backend, or None if nothing is configured.
    """
    if settings.OPENAI_API_KEY:
        return {
            "api_key": settings.OPENAI_API_KEY,
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
        }

    if settings.GITHUB_OPENAI_API_TOKEN:
        return {
            "api_key": settings.GITHUB_OPENAI_API_TOKEN,
            "base_url": settings.GITHUB_OPENAI_BASE_URL,
            "model": "gpt-4o-mini",
        }

    if settings.GROQ_API_KEY:
        return {
            "api_key": settings.GROQ_API_KEY,
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.3-70b-versatile",
        }

    if settings.DEEPSEEK_API_KEY:
        return {
            "api_key": settings.DEEPSEEK_API_KEY,
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
        }

    return None


# ── Tool definitions for the chat-completions function-calling API ──

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location (city, landmark, zip, or coordinates).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_query": {
                        "type": "string",
                        "description": "City name, zip code, landmark, or coordinates.",
                    }
                },
                "required": ["location_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "Get a 5-day / 3-hour forecast for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_query": {
                        "type": "string",
                        "description": "City name, zip code, landmark, or coordinates.",
                    }
                },
                "required": ["location_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_location",
            "description": "Resolve a location query to coordinates and details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "City name, zip code, landmark, or coordinates.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_videos",
            "description": "Search YouTube for travel/weather videos about a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "description": "Name of the location.",
                    }
                },
                "required": ["location_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_history",
            "description": "Query previously stored weather records from the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_name": {
                        "type": "string",
                        "description": "Optional filter by location name.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max records to return (default 10).",
                    },
                },
            },
        },
    },
]

# Map function names → actual tool callables
from weather.agent import tools as _tool_mod  # noqa: E402

TOOL_MAP = {
    "get_weather": _tool_mod.get_weather,
    "get_forecast": _tool_mod.get_forecast,
    "search_location": _tool_mod.search_location,
    "get_videos": _tool_mod.get_videos,
    "query_history": _tool_mod.query_history,
}


def _call_chat(cfg: dict, messages: list) -> dict:
    """Send a chat-completions request and return the JSON response."""
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "tools": TOOL_DEFS,
        "tool_choice": "auto",
    }
    resp = requests.post(
        f"{cfg['base_url']}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def run_agent(user_message: str) -> str:
    """
    Run the weather agent with a user message and return the response.
    Uses the OpenAI-compatible chat-completions API with function calling.
    """
    cfg = _get_llm_config()
    if cfg is None:
        return (
            "The AI agent is not configured. "
            "Please set at least one LLM API key in your .env file "
            "(OPENAI_API_KEY, GITHUB_OPENAI__API_TOKEN, GROQ_API_KEY, or DEEPSEEK_API_KEY)."
        )

    from .prompts import SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        # Allow up to 5 rounds of tool calls
        for _ in range(5):
            data = _call_chat(cfg, messages)
            choice = data["choices"][0]
            msg = choice["message"]

            # If the model wants to call tools
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                # Append the assistant message (with tool_calls) first
                messages.append(msg)

                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"]["arguments"])
                    logger.info("Agent calling tool: %s(%s)", fn_name, fn_args)

                    tool_fn = TOOL_MAP.get(fn_name)
                    if tool_fn:
                        result = tool_fn(**fn_args)
                    else:
                        result = {"error": f"Unknown tool: {fn_name}"}

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(result, default=str),
                        }
                    )
                # Loop back to get the model's next response
                continue

            # No tool calls — we have the final answer
            return msg.get("content", "")

        return "Agent exceeded maximum tool-call rounds."

    except requests.RequestException as e:
        logger.error("LLM API request failed: %s", e)
        return f"Agent encountered an API error: {str(e)}"
    except Exception as e:
        logger.error("Agent execution failed: %s", e)
        return f"Agent encountered an error: {str(e)}"
