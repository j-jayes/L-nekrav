"""The advisor's tool loop: a chat model calls Lönekrav's MCP tools until it can write a memo.

Orchestration only (plan, Complexity Tracking): the tools are the MCP server's own (research R6),
and the memo's guarantees come from `core.advisor.finalise_memo`.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

from lonekrav.core.advisor import AdvisorRequest, finalise_memo

MAX_ROUNDS = 8
OPENROUTER_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-haiku-5.5"  # research R9, checked 2026-10-22

SYSTEM_PROMPT = """\
You are Lönekrav's advisor for Swedish work permits. You help a job seeker, or someone advising
them, see which SSYK 2012 occupation codes plausibly describe a job and what each code means for
the work-permit salary requirement.

Work only from Lönekrav's tools:
1. Call search_occupations on the job ad with parse_ad true and mode "full".
2. Pick the plausible codes: those whose official duties match the ad, usually two or three.
3. If there is an offer, call compare_occupations with those codes and the offer. Without an
   offer, call get_occupation_salary for each code, and do not judge eligibility.
4. Optionally, call get_occupation_market for the plausible codes, to mention how many ads are
   open now or what the code pays on average in the applicant's area, each figure with its source
   and date. Never use open ads or pay as a reason to prefer or rank a code.

Then write a short memo in Markdown, in English, with the Swedish SSYK titles next to the English:
- For each plausible code: why its duties match or do not match the ad, the salary threshold that
  applies, and, with an offer, whether it passes and any warnings.
- State that the code on the offer must match the duties actually performed. Never suggest a code
  because its threshold is lower, and never rank codes by threshold.
- Every amount, percentage and date must come from a tool result in this conversation. Cite the
  legal sources and their checked-on dates from those results.
- Describe where an offer sits in the market only with the bracket market_position gives (for
  example "between the median and the 75th percentile"). For any figure marked is_simulated, call
  it an estimate, not an SCB figure.
- Say that this is information, not legal advice.
"""


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON text, as the model wrote it


@dataclass(frozen=True)
class Reply:
    content: str | None
    tool_calls: list[ToolCall]


class ChatModel(Protocol):
    async def __call__(self, messages: list[dict], tools: list[dict]) -> Reply: ...


class Tools(Protocol):
    async def specs(self) -> list[dict]: ...
    async def call(self, name: str, args: dict) -> tuple[bool, Any]: ...  # (is_error, payload)


@dataclass(frozen=True)
class Progress:
    text: str


@dataclass(frozen=True)
class ToolResult:
    tool: str
    args: dict
    result: Any


@dataclass(frozen=True)
class Memo:
    text: str


class RoundLimit(Exception):
    pass


def _user_message(request: AdvisorRequest | str) -> str:
    if isinstance(request, str):
        return request
    offer = (f"Offer (JSON):\n{request.offer.model_dump_json(indent=1)}" if request.offer
             else "No offer given: do not check eligibility.")
    return (f"Job ad:\n{request.ad}\n\nApplicant background:\n{request.background or 'not given'}"
            f"\n\n{offer}")


def _decode_objects(args: dict, parameters: dict) -> dict:
    """Small models sometimes send an object argument as JSON text, even with a stray closing
    brace; take its leading object, but only where the tool's schema does not ask for a string."""
    props = parameters.get("properties", {})
    out = {}
    for name, value in args.items():
        if isinstance(value, str) and props.get(name, {}).get("type") != "string":
            try:
                decoded, _ = json.JSONDecoder().raw_decode(value.strip())
            except json.JSONDecodeError:
                decoded = value
            value = decoded if isinstance(decoded, dict) else value
        out[name] = value
    return out


async def run(request: AdvisorRequest | str, model: ChatModel,
              tools: Tools) -> AsyncIterator[Progress | ToolResult | Memo]:
    specs = await tools.specs()
    parameters = {s["function"]["name"]: s["function"].get("parameters", {}) for s in specs}
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": _user_message(request)}]
    called: list[str] = []
    for _ in range(MAX_ROUNDS):
        reply = await model(messages, specs)
        if not reply.tool_calls:
            yield Memo(finalise_memo(reply.content or "", called))
            return
        messages.append({"role": "assistant", "content": reply.content, "tool_calls": [
            {"id": c.id, "type": "function",
             "function": {"name": c.name, "arguments": c.arguments}} for c in reply.tool_calls]})
        for c in reply.tool_calls:
            yield Progress(f"Calling {c.name}")
            try:
                args = json.loads(c.arguments or "{}")
            except json.JSONDecodeError as e:
                is_error, payload = True, f"Arguments are not valid JSON: {e}"
            else:
                if isinstance(args, dict):
                    args = _decode_objects(args, parameters.get(c.name, {}))
                    is_error, payload = await tools.call(c.name, args)
                else:
                    is_error, payload = True, "Arguments must be a JSON object."
            if is_error:
                yield Progress(f"{c.name} failed; the model is told why")
            else:
                called.append(c.name)
                yield ToolResult(c.name, args, payload)
            messages.append({"role": "tool", "tool_call_id": c.id,
                             "content": payload if is_error else json.dumps(payload)})
    raise RoundLimit(f"Stopped after {MAX_ROUNDS} model rounds without a memo.")


class McpTools:
    """The MCP server's tools over the in-memory transport: the advisor's only tools (R6)."""

    def __init__(self, mcp):
        from fastmcp import Client

        self.client = Client(mcp)

    async def __aenter__(self) -> McpTools:  # noqa: PYI034
        await self.client.__aenter__()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.client.__aexit__(*exc)

    async def specs(self) -> list[dict]:
        return [{"type": "function", "function": {"name": t.name, "description": t.description,
                                                  "parameters": t.input_schema}}
                for t in await self.client.list_tools()]

    async def call(self, name: str, args: dict) -> tuple[bool, Any]:
        r = await self.client.call_tool(name, args, raise_on_error=False)
        return (True, r.content[0].text) if r.is_error else (False, r.structured_content)


def openrouter_model(key: str, model: str = DEFAULT_MODEL) -> ChatModel:
    """One client for the app's lifetime, made at start-up, so nothing is lazily shared (FR-018)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(base_url=OPENROUTER_URL, api_key=key, timeout=30, max_retries=1)

    async def chat(messages: list[dict], tools: list[dict]) -> Reply:
        r = await client.chat.completions.create(model=model, messages=messages, tools=tools)
        m = r.choices[0].message
        return Reply(m.content, [ToolCall(c.id, c.function.name, c.function.arguments)
                                 for c in m.tool_calls or []])
    return chat
