"""LangChain agent chains wiring together the LLM, tools, and memory."""

from __future__ import annotations

from typing import Any

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain_core.tools import Tool

from config import settings
from memory_short import ShortTermMemory
from tools_gmail import get_message, list_messages, send_message
from tools_google_calendar import create_event, delete_event, list_events
from tools_google_drive import list_files


# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a helpful AI assistant with access to the user's Gmail, \
Google Calendar, and Google Drive. Use the provided tools to answer requests. \
Always explain what you are doing.

Chat history:
{chat_history}

Tools available: {tools}
Tool names: {tool_names}

Question: {input}
{agent_scratchpad}"""

_PROMPT = PromptTemplate(
    input_variables=["chat_history", "tools", "tool_names", "input", "agent_scratchpad"],
    template=_SYSTEM_PROMPT,
)


# ── Tool definitions ──────────────────────────────────────────────────────────

def _build_tools() -> list[Tool]:
    """Construct the list of LangChain :class:`Tool` objects exposed to the agent.

    Returns:
        List of configured :class:`langchain_core.tools.Tool` instances.
    """
    return [
        Tool(
            name="ListEmails",
            func=lambda q: str(list_messages(query=q, max_results=5)),
            description=(
                "List emails. Input should be a Gmail search query string, "
                "e.g. 'is:unread'. Returns a list of message stubs."
            ),
        ),
        Tool(
            name="ReadEmail",
            func=lambda msg_id: str(get_message(msg_id)),
            description=(
                "Read a specific email. Input must be a Gmail message ID. "
                "Returns subject, from, to, date, and body."
            ),
        ),
        Tool(
            name="SendEmail",
            func=lambda args: str(
                send_message(*[a.strip() for a in args.split(",", 2)])
            ),
            description=(
                "Send an email. Input must be: to, subject, body — "
                "comma-separated. Example: 'user@example.com, Hello, Hi there!'"
            ),
        ),
        Tool(
            name="ListCalendarEvents",
            func=lambda _: str(list_events(max_results=10)),
            description="List the next 10 upcoming calendar events. No input needed.",
        ),
        Tool(
            name="CreateCalendarEvent",
            func=lambda args: str(
                create_event(*[a.strip() for a in args.split(",", 3)])
            ),
            description=(
                "Create a calendar event. Input: summary, start_datetime, end_datetime "
                "(RFC 3339) — comma-separated."
            ),
        ),
        Tool(
            name="DeleteCalendarEvent",
            func=lambda event_id: str(delete_event(event_id.strip())),
            description="Delete a calendar event by its ID.",
        ),
        Tool(
            name="ListDriveFiles",
            func=lambda q: str(list_files(query=q, max_results=10)),
            description=(
                "List files in Google Drive. Input is an optional Drive query string, "
                "e.g. 'mimeType=\\'application/pdf\\''. Leave empty to list all."
            ),
        ),
    ]


# ── Chain factory ─────────────────────────────────────────────────────────────

def build_agent_executor(
    memory: ShortTermMemory,
    model: str | None = None,
    temperature: float | None = None,
) -> AgentExecutor:
    """Construct a LangChain :class:`AgentExecutor` backed by Ollama.

    Args:
        memory: The session's short-term memory instance.
        model: Override the default Ollama model name.
        temperature: Override the sampling temperature.

    Returns:
        A ready-to-run :class:`AgentExecutor`.
    """
    llm = Ollama(
        base_url=settings.ollama_base_url,
        model=model or settings.ollama_model,
        temperature=temperature if temperature is not None else settings.llm_temperature,
    )

    tools = _build_tools()

    agent = create_react_agent(llm=llm, tools=tools, prompt=_PROMPT)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory._memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )


async def run_agent(
    user_message: str,
    memory: ShortTermMemory,
    model: str | None = None,
    temperature: float | None = None,
) -> str:
    """Run the agent on *user_message* and return the final answer.

    Args:
        user_message: The user's input text.
        memory: The active session's short-term memory.
        model: Optional Ollama model override.
        temperature: Optional temperature override.

    Returns:
        The agent's final response string.
    """
    executor = build_agent_executor(memory, model=model, temperature=temperature)
    result: dict[str, Any] = await executor.ainvoke({"input": user_message})
    return result.get("output", "")
