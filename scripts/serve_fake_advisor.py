"""Serve Lönekrav with a scripted advisor model, for the drawer's end-to-end test (Feature 004 T046).

    PORT=8011 uv run python scripts/serve_fake_advisor.py
    (cd frontend && BASE_URL=http://127.0.0.1:8011 npx playwright test e2e/advisor.spec.ts)

The real app, index and tools, with a model that always does the same thing: search the ad, look
up 2512's salary, compare 2512 and 2511, then write a short memo. Each step waits a second, so a
test can see the chart change before the memo arrives. No key and no network are needed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import uvicorn

from lonekrav.app import create_app
from lonekrav.protocols.agent.loop import Reply, ToolCall

STEP_SECONDS = 1.0


def call(name: str, args: dict, id_: str) -> Reply:
    return Reply(None, [ToolCall(id_, name, json.dumps(args))])


class ScriptedModel:
    """Replays the script for every run; the first message is the user's ad."""

    async def __call__(self, messages: list[dict], tools: list[dict]) -> Reply:
        await asyncio.sleep(STEP_SECONDS)
        step = sum(m["role"] == "assistant" for m in messages)
        script = [
            call("search_occupations", {"request": {"text": "backend developer", "mode": "fast"}}, "c1"),
            call("get_occupation_salary", {"code": "2512"}, "c2"),
            call("compare_occupations", {"request": {"codes": ["2512", "2511"]}}, "c3"),
            Reply("## Memo\n\nCode **2512** fits the duties; 2511 is shown for comparison.", []),
        ]
        return script[min(step, len(script) - 1)]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    uvicorn.run(create_app(chat_model=ScriptedModel()), host="127.0.0.1",
                port=int(os.environ.get("PORT", "8011")), access_log=False)
