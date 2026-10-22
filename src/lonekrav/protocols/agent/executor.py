"""A2A executor for lonekrav-advisor: one message in, the loop's events out as A2A events.

contracts/a2a.md: a working status per step, a `ui_sync` data artifact per tool result, a
markdown `memo` artifact, then completed; invalid input, the round limit or a model failure end
the task as failed with a short cause and no request content (FR-005).
"""

from __future__ import annotations

import logging

from a2a.helpers import (
    get_data_parts,
    get_text_parts,
    new_data_part,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Message, TaskState
from pydantic import ValidationError

from lonekrav.core.adparse import AdText
from lonekrav.core.advisor import AdvisorRequest
from lonekrav.protocols.agent.loop import (
    ChatModel,
    McpTools,
    Memo,
    Progress,
    RoundLimit,
    ToolResult,
    run,
)

log = logging.getLogger("lonekrav.advisor")
UNAVAILABLE = "Agent unavailable: no model key is configured (set OPENROUTER_KEY in .env)."


def _request(message: Message) -> AdvisorRequest | str:
    """The data part as an AdvisorRequest, any text joining its background; else the text."""
    texts = [t for t in get_text_parts(message.parts) if t.strip()]
    if datas := get_data_parts(message.parts):
        data = dict(datas[0])
        if texts:
            data["background"] = "\n\n".join(filter(None, [data.get("background"), *texts]))
        return AdvisorRequest.model_validate(data)
    return AdText(text="\n\n".join(texts)).text


def _invalid(e: ValidationError) -> str:
    """Field and rule only: pydantic's `input` would echo the request (FR-005)."""
    return "Invalid input: " + "; ".join(
        f"{'.'.join(map(str, err['loc'])) or 'message'}: {err['msg']}" for err in e.errors())


class AdvisorExecutor(AgentExecutor):
    def __init__(self, mcp, model: ChatModel | None):
        self.mcp, self.model = mcp, model

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.current_task is None:  # the handler requires the Task first (research R7)
            await event_queue.enqueue_event(new_task_from_user_message(context.message))
        up = TaskUpdater(event_queue, context.task_id, context.context_id)

        def say(text: str) -> Message:
            return up.new_agent_message([new_text_part(text)])

        if self.model is None:  # research R8: declined, not broken
            await up.reject(say(UNAVAILABLE))
            return
        try:
            request = _request(context.message)
        except ValidationError as e:
            await up.failed(say(_invalid(e)))
            return
        await up.start_work(say("Reading the job ad"))
        try:
            async with McpTools(self.mcp) as tools:
                async for event in run(request, self.model, tools):
                    if isinstance(event, Progress):
                        await up.update_status(TaskState.TASK_STATE_WORKING, say(event.text))
                    elif isinstance(event, ToolResult):
                        await up.add_artifact([new_data_part({
                            "kind": "ui_sync", "tool": event.tool, "args": event.args,
                            "result": event.result})], name=f"ui_sync:{event.tool}")
                    elif isinstance(event, Memo):
                        memo = new_text_part(event.text, media_type="text/markdown")
                        await up.add_artifact([memo], name="memo", last_chunk=True)
        except RoundLimit as e:
            await up.failed(say(str(e)))
            return
        except Exception as e:  # noqa: BLE001 - the model service: timeouts, HTTP, API errors
            log.error("advisor run failed: %s", type(e).__name__)
            await up.failed(say(f"The model service failed ({type(e).__name__}). Try again later."))
            return
        await up.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(event_queue, context.task_id, context.context_id).cancel()
