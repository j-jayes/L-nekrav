"""A2A adapter (contracts/a2a.md): the agent card and JSON-RPC endpoint for lonekrav-advisor."""

from __future__ import annotations

import os
from importlib.metadata import version

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

from lonekrav.protocols.agent.executor import AdvisorExecutor
from lonekrav.protocols.agent.loop import ChatModel

PUBLIC_URL = "http://localhost:8000"  # LONEKRAV_PUBLIC_URL overrides it (Feature 004 FR-028)
MODES = ["text/plain", "application/json"]


def card(base_url: str) -> AgentCard:
    """The agent card, with its interface at `{base_url}/a2a`."""
    return AgentCard(
        name="lonekrav-advisor",
        description=("Reads a job ad, the applicant's background and the offer, and writes an "
                     "honest-fit memo: every plausible SSYK 2012 code with its Swedish work-permit "
                     "salary consequences, from Lönekrav's own data. It uses a third-party language "
                     "model (via OpenRouter), which receives the ad, background and offer you send."),
        version=version("lonekrav"),
        supported_interfaces=[AgentInterface(url=f"{base_url.rstrip('/')}/a2a",
                                             protocol_binding="JSONRPC", protocol_version="1.0")],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=MODES,
        default_output_modes=MODES,
        skills=[AgentSkill(
            id="honest-fit-memo", name="Honest-fit occupation and salary memo",
            description=("Send one data part {ad, background?, offer?} (offer: monthly_salary_sek, "
                         "fte_percent, application_type, filed_on, ...) or the ad as text. Streams "
                         "progress, a ui_sync artifact per tool result, and a markdown memo."),
            tags=["ssyk", "work-permit", "salary", "sweden"],
            examples=["A backend developer ad with an offer of a monthly salary for a first permit"],
            input_modes=MODES, output_modes=MODES)],
    )


def add_a2a(app, mcp, model: ChatModel | None) -> None:
    agent_card = card(os.environ.get("LONEKRAV_PUBLIC_URL") or PUBLIC_URL)
    handler = DefaultRequestHandler(agent_executor=AdvisorExecutor(mcp, model),
                                    task_store=InMemoryTaskStore(), agent_card=agent_card)
    add_a2a_routes_to_fastapi(app, agent_card_routes=create_agent_card_routes(agent_card),
                              jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/a2a"))
