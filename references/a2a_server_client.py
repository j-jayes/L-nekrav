"""Minimal A2A v1.0 reference for a2a-sdk 1.2.3: card, executor, FastAPI mounting,
in-process test pattern, SDK streaming client and raw httpx JSON-RPC.

Run:  uv run python references/a2a_server_client.py         (in-process + live server on :8766)
      uv run python references/a2a_server_client.py serve   (server only)
"""

import asyncio
import json
import subprocess
import sys
import time
import uuid

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.helpers import (
    get_data_parts,
    get_text_parts,
    new_data_part,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)
from fastapi import FastAPI

PORT = 8766
BASE = f"http://127.0.0.1:{PORT}"
MODES = ["text/plain", "application/json"]

# ---------------------------------------------------------------- 1. card
CARD = AgentCard(
    name="lonekrav-advisor",
    description="SSYK and salary navigator for Swedish work permits.",
    version="0.1.0",
    supported_interfaces=[
        AgentInterface(url=f"{BASE}/a2a", protocol_binding="JSONRPC", protocol_version="1.0")
    ],
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=MODES,
    default_output_modes=MODES,
    skills=[
        AgentSkill(
            id="advise",
            name="Occupation and salary advice",
            description="Finds plausible SSYK codes and their salary consequences.",
            tags=["ssyk", "salary"],
            examples=["Data engineer in Malmö, 42 000 SEK"],
            input_modes=MODES,
            output_modes=MODES,
        )
    ],
)


# ---------------------------------------------------------------- 2. executor
class AdvisorExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        msg = context.message
        texts = get_text_parts(msg.parts)  # list[str]
        datas = get_data_parts(msg.parts)  # list[dict] (MessageToDict of the Value)
        data = datas[0] if datas else {}

        # The v2 handler requires a Task event before any status update.
        if context.current_task is None:
            await event_queue.enqueue_event(new_task_from_user_message(msg))
        up = TaskUpdater(event_queue, context.task_id, context.context_id)

        if data.get("simulate") == "unavailable":
            await up.failed(up.new_agent_message([new_text_part("Agent unavailable: LLM backend down.")]))
            return

        await up.start_work(up.new_agent_message([new_text_part("Searching occupations...")]))
        for tool, result in [
            ("search_occupations", {"hits": [{"ssyk": "2512", "score": 0.91}]}),
            ("get_salary", {"ssyk": "2512", "median": 52000, "table": "AM0110"}),
        ]:
            await up.add_artifact(
                [new_data_part({"kind": "ui_sync", "tool": tool, "args": data, "result": result})],
                name=f"ui_sync:{tool}",
            )
        memo = f"## Memo\n\nQuery: *{texts[0] if texts else ''}*\n\nSSYK 2512 fits."
        await up.add_artifact([new_text_part(memo, media_type="text/markdown")], name="memo", last_chunk=True)
        await up.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(event_queue, context.task_id, context.context_id).cancel()


def build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/v1/health")  # an existing, unrelated route
    def health():
        return {"ok": True}

    handler = DefaultRequestHandler(
        agent_executor=AdvisorExecutor(), task_store=InMemoryTaskStore(), agent_card=CARD
    )
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(CARD),  # /.well-known/agent-card.json
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/a2a"),
    )
    return app


def user_message(text: str, data: dict) -> Message:
    return Message(
        role=Role.ROLE_USER,
        message_id=str(uuid.uuid4()),
        parts=[new_text_part(text), new_data_part(data)],
    )


def describe(ev) -> str:
    """Works for both server-side events and client StreamResponse."""
    name = type(ev).__name__
    if name == "StreamResponse":
        name = ev.WhichOneof("payload")
        ev = getattr(ev, name)
        name = type(ev).__name__
    if name == "Task":
        return f"Task state={TaskState.Name(ev.status.state)}"
    if name == "TaskStatusUpdateEvent":
        t = get_text_parts(ev.status.message.parts)
        return f"Status state={TaskState.Name(ev.status.state)} text={t}"
    if name == "TaskArtifactUpdateEvent":
        kinds = [p.WhichOneof("content") for p in ev.artifact.parts]
        extra = get_data_parts(ev.artifact.parts) or get_text_parts(ev.artifact.parts)
        return f"Artifact name={ev.artifact.name} part_kinds={kinds} -> {str(extra)[:70]}"
    return name


# ---------------------------------------------------------------- 3. in-process
async def in_process() -> None:
    handler = DefaultRequestHandler(
        agent_executor=AdvisorExecutor(), task_store=InMemoryTaskStore(), agent_card=CARD
    )
    for data in ({"city": "Malmö"}, {"simulate": "unavailable"}):
        req = SendMessageRequest(message=user_message("data engineer", data))
        events = [e async for e in handler.on_message_send_stream(req, ServerCallContext())]
        print(f"  in-process {data}:")
        for e in events:
            print("    ", describe(e))
    await handler.aclose()


# ---------------------------------------------------------------- 4. live
async def live() -> None:
    async def show_wire(request: httpx.Request):
        if request.method == "POST":
            body = json.loads(request.content)
            print(f"  [wire] POST {request.url.path} method={body['method']} "
                  f"A2A-Version={request.headers.get('A2A-Version')}")

    async with httpx.AsyncClient(timeout=30, event_hooks={"request": [show_wire]}) as hc:
        r = await hc.get(f"{BASE}/.well-known/agent-card.json")
        cj = r.json()
        print("  httpx GET card:", r.status_code, "interfaces=", cj["supportedInterfaces"],
              "capabilities=", cj["capabilities"])
        print("  health route still there:", (await hc.get(f"{BASE}/api/v1/health")).json())

        card = await A2ACardResolver(hc, BASE).get_agent_card()
        print("  resolved card:", card.name, "streaming=", card.capabilities.streaming)
        client = ClientFactory(ClientConfig(streaming=True, httpx_client=hc)).create(card)
        req = SendMessageRequest(message=user_message("data engineer", {"city": "Malmö"}))
        async for sr in client.send_message(req):
            print("    SDK client <-", describe(sr))

        # raw JSON-RPC streaming POST
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "SendStreamingMessage",
            "params": {"message": {
                "messageId": str(uuid.uuid4()), "role": "ROLE_USER",
                "parts": [{"text": "data engineer"}, {"data": {"simulate": "unavailable"}}],
            }},
        }
        async with hc.stream("POST", f"{BASE}/a2a", json=payload,
                             headers={"A2A-Version": "1.0", "Accept": "text/event-stream"}) as resp:
            print("  raw content-type:", resp.headers["content-type"])
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    print("    raw <-", line[5:].strip()[:160])


def main() -> None:
    if sys.argv[1:] == ["serve"]:
        import uvicorn
        uvicorn.run(build_app(), host="127.0.0.1", port=PORT, log_level="warning")
        return
    print("== 3. in-process via DefaultRequestHandler.on_message_send_stream")
    asyncio.run(in_process())
    print("== 4. live server on", PORT)
    srv = subprocess.Popen([sys.executable, __file__, "serve"])
    try:
        for _ in range(50):
            try:
                httpx.get(f"{BASE}/api/v1/health", timeout=0.5)
                break
            except httpx.TransportError:
                time.sleep(0.2)
        asyncio.run(live())
    finally:
        srv.terminate()
        srv.wait(5)
        print("  server stopped, exit", srv.returncode)


if __name__ == "__main__":
    main()
