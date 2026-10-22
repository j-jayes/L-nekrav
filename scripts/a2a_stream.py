"""Fetch lonekrav-advisor's agent card and stream one message, printing every event as it arrives.

    uv run lonekrav-serve &
    uv run python scripts/a2a_stream.py --ad-file ad.txt --background "MSc, 5 years Python" \\
        --offer '{"monthly_salary_sek": 52000, "fte_percent": 100,
                  "application_type": "first_permit", "filed_on": "2026-10-01"}'

Uses the a2a-sdk client, so the method on the wire is A2A v1.0's SendStreamingMessage (the 0.3
name was message/stream). `ui_sync` results are cut to their first 300 characters; the memo is
printed in full. Model time is the total minus the time spent inside tool calls, which is the gap
between each "Calling <tool>" status and the event that follows it.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.helpers import new_data_part
from a2a.types import Message, Role, SendMessageRequest
from google.protobuf.json_format import MessageToDict


def parts_of(obj) -> list[dict]:
    return MessageToDict(obj).get("parts", [])


async def main(args: argparse.Namespace) -> None:
    ad = Path(args.ad_file).read_text() if args.ad_file else args.ad
    data = {"ad": ad} | ({"background": args.background} if args.background else {}) | (
        {"offer": json.loads(args.offer)} if args.offer else {})
    async with httpx.AsyncClient(timeout=120) as http:
        t0 = time.perf_counter()
        card = await A2ACardResolver(http, args.url).get_agent_card()
        c = MessageToDict(card)
        print(f"GET {args.url}/.well-known/agent-card.json  ({(time.perf_counter() - t0) * 1000:.0f} ms)")
        print(f"  name={c['name']} version={c['version']} streaming={c['capabilities']['streaming']}")
        print(f"  interface={c['supportedInterfaces'][0]}")
        print(f"  description={c['description']}")
        print(f"  skill={c['skills'][0]['id']}: {c['skills'][0]['description']}\n")

        client = ClientFactory(ClientConfig(streaming=True, httpx_client=http)).create(card)
        msg = Message(role=Role.ROLE_USER, message_id=str(uuid4()), parts=[new_data_part(data)])
        print(f"SendStreamingMessage: data part with keys {sorted(data)}\n")
        t0 = last = time.perf_counter()
        in_tool, tool_time, memo = None, 0.0, None
        async for sr in client.send_message(SendMessageRequest(message=msg)):
            now = time.perf_counter()
            if in_tool:
                tool_time += now - last
                in_tool = None
            last = now
            kind = sr.WhichOneof("payload")
            stamp = f"{now - t0:6.2f}s  {kind:<14}"
            if kind == "task":
                print(stamp, MessageToDict(sr.task)["status"]["state"])
            elif kind == "status_update":
                status = MessageToDict(sr.status_update)["status"]
                text = " ".join(p.get("text", "") for p in parts_of(sr.status_update.status.message))
                print(stamp, status["state"], text)
                in_tool = text.startswith("Calling ")
            elif kind == "artifact_update":
                a = sr.artifact_update.artifact
                (part,) = parts_of(a)
                if a.name == "memo":
                    memo = part["text"]
                    print(stamp, a.name, f"{part.get('mediaType')}, {len(memo)} characters")
                else:
                    print(stamp, a.name, "data:", json.dumps(part["data"], ensure_ascii=False)[:300], "…")
            else:
                print(stamp, MessageToDict(getattr(sr, kind)))
        total = time.perf_counter() - t0
    if memo:
        print("\n--- memo ---\n" + memo + "\n--- end memo ---")
    print(f"\ntotal {total:.2f} s; in tool calls {tool_time:.2f} s; model and overhead "
          f"{total - tool_time:.2f} s")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default="http://localhost:8000")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--ad")
    src.add_argument("--ad-file")
    p.add_argument("--background")
    p.add_argument("--offer", help="JSON object with the eligibility fields, without a code")
    asyncio.run(main(p.parse_args()))
