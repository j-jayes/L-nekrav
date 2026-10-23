"""The A2A adapter over a fixture index with a scripted model (contracts/a2a.md)."""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from lonekrav.core.advisor import THIRD_PARTY_NOTICE
from lonekrav.core.search import HONEST_FIT
from lonekrav.protocols.agent.loop import Reply, ToolCall

OFFER = {"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit",
         "filed_on": "2026-10-01"}
AD = "Backend Developer (Python)\n\nYou will build and maintain our APIs and cloud services."


def call(name, args, id_="c1"):
    return Reply(None, [ToolCall(id_, name, json.dumps(args))])


SCRIPT = (call("search_occupations", {"request": {"text": AD, "parse_ad": True}}),
          call("get_occupation_salary", {"code": "2512"}, "c2"),
          Reply("Code 2512 (Mjukvaru- och systemutvecklare) fits the duties.", []))


@pytest.fixture
def advisor(fixture_engine, salaries):
    """Make an app whose advisor uses `model`; yields a factory of TestClients."""
    from lonekrav.app import create_app

    engine, profiles = fixture_engine
    clients = []

    def make(model):
        client = TestClient(create_app(engine=engine, profiles=profiles, salaries=salaries,
                                       chat_model=model), raise_server_exceptions=False)
        clients.append(client.__enter__())
        return client
    yield make
    for c in clients:
        c.__exit__(None, None, None)


def message(parts, method="SendStreamingMessage", context_id=None):
    msg = {"messageId": "m1", "role": "ROLE_USER", "parts": parts}
    if context_id:
        msg["contextId"] = context_id
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": {"message": msg}}


def stream(client, parts, **kw):
    """POST a streamed message and return each SSE event's `result`."""
    with client.stream("POST", "/a2a", json=message(parts, **kw),
                       headers={"A2A-Version": "1.0"}) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        return [json.loads(line[5:])["result"] for line in r.iter_lines()
                if line.startswith("data:")]


def kind(event):
    (k,) = event
    if k == "task":
        return f"task:{event[k]['status']['state']}"
    if k == "statusUpdate":
        return f"status:{event[k]['status']['state']}"
    return f"artifact:{event[k]['artifact']['name']}"


def status_text(event):
    return " ".join(p["text"] for p in event["statusUpdate"]["status"]["message"]["parts"])


def test_agent_card(advisor, fake_model):
    card = advisor(fake_model()).get("/.well-known/agent-card.json").json()
    assert card["name"] == "lonekrav-advisor" and card["capabilities"]["streaming"] is True
    assert len(card["skills"]) == 1
    assert set(card["defaultInputModes"]) == {"text/plain", "application/json"}
    (iface,) = card["supportedInterfaces"]
    assert iface["url"].endswith("/a2a") and iface["protocolVersion"] == "1.0"
    assert "third-party" in card["description"] and "OpenRouter" in card["description"]


@pytest.mark.parametrize(("setting", "url"), [
    (None, "http://localhost:8000/a2a"),
    ("https://lonekrav.example.test", "https://lonekrav.example.test/a2a"),
    ("https://lonekrav.example.test/", "https://lonekrav.example.test/a2a"),
])
def test_card_url_follows_the_public_address(advisor, fake_model, monkeypatch, setting, url):
    # Feature 004 FR-028: the card names where the container is reachable.
    if setting is None:
        monkeypatch.delenv("LONEKRAV_PUBLIC_URL", raising=False)
    else:
        monkeypatch.setenv("LONEKRAV_PUBLIC_URL", setting)
    card = advisor(fake_model()).get("/.well-known/agent-card.json").json()
    assert card["supportedInterfaces"][0]["url"] == url


def test_streamed_run_events_in_order(advisor, fake_model):
    client = advisor(fake_model(*SCRIPT))
    events = stream(client, [{"data": {"ad": AD, "offer": OFFER}}])
    assert [kind(e) for e in events] == [
        "task:TASK_STATE_SUBMITTED", "status:TASK_STATE_WORKING",
        "status:TASK_STATE_WORKING", "artifact:ui_sync:search_occupations",
        "status:TASK_STATE_WORKING", "artifact:ui_sync:get_occupation_salary",
        "artifact:memo", "status:TASK_STATE_COMPLETED"]
    assert status_text(events[1]) == "Reading the job ad"
    assert status_text(events[2]) == "Calling search_occupations"


def test_ui_sync_carries_the_mcp_result(advisor, fake_model):
    from fastmcp import Client

    client = advisor(fake_model(*SCRIPT))
    events = stream(client, [{"data": {"ad": AD, "offer": OFFER}}])
    (part,) = next(e for e in events if kind(e) == "artifact:ui_sync:get_occupation_salary"
                   )["artifactUpdate"]["artifact"]["parts"]

    async def direct():
        async with Client(client.app.state.mcp) as c:
            return (await c.call_tool("get_occupation_salary", {"code": "2512"})).structured_content
    assert part["data"] == {"kind": "ui_sync", "tool": "get_occupation_salary",
                            "args": {"code": "2512"}, "result": asyncio.run(direct())}


def test_memo_is_markdown_and_guarded(advisor, fake_model):
    events = stream(advisor(fake_model(*SCRIPT)), [{"data": {"ad": AD, "offer": OFFER}}])
    (part,) = next(e for e in events if kind(e) == "artifact:memo")["artifactUpdate"][
        "artifact"]["parts"]
    assert part["mediaType"] == "text/markdown"
    assert part["text"].startswith("Code 2512") and HONEST_FIT in part["text"]
    assert part["text"].endswith(THIRD_PARTY_NOTICE)


def test_the_model_gets_the_structured_request(advisor, fake_model):
    model = fake_model(Reply("Memo.", []))
    stream(advisor(model), [{"data": {"ad": AD, "offer": OFFER}},
                            {"text": "Also speaks Swedish."}])
    user = model.seen[0][0][1]["content"]
    assert AD in user and "Also speaks Swedish." in user and '"fte_percent": 100' in user


def test_text_only_message(advisor, fake_model):
    model = fake_model(Reply("Memo.", []))
    events = stream(advisor(model), [{"text": AD}])
    assert kind(events[-1]) == "status:TASK_STATE_COMPLETED"
    assert model.seen[0][0][1]["content"] == AD


def rpc(client, method, params):
    r = client.post("/a2a", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                    headers={"A2A-Version": "1.0"})
    assert r.status_code == 200
    return r.json()


def test_invalid_offer_fails_before_any_model_call(advisor, fake_model):
    model = fake_model(*SCRIPT)
    events = stream(advisor(model), [{"data": {"ad": AD, "offer": OFFER | {"fte_percent": 0}}}])
    assert [kind(e) for e in events] == ["task:TASK_STATE_SUBMITTED", "status:TASK_STATE_FAILED"]
    assert "fte_percent" in status_text(events[-1]) and model.seen == []


def test_round_limit_fails_the_task(advisor, fake_model):
    from lonekrav.protocols.agent.loop import MAX_ROUNDS

    model = fake_model(forever=call("get_occupation_salary", {"code": "2512"}))
    events = stream(advisor(model), [{"text": AD}])
    assert kind(events[-1]) == "status:TASK_STATE_FAILED"
    assert f"Stopped after {MAX_ROUNDS} model rounds" in status_text(events[-1])


def test_a_model_failure_fails_the_task_without_internals(advisor, fake_model):
    model = fake_model(RuntimeError("/Users/someone/secret/path.py exploded"))
    events = stream(advisor(model), [{"text": AD}])
    assert kind(events[-1]) == "status:TASK_STATE_FAILED"
    assert "model service failed" in status_text(events[-1])
    assert "secret" not in json.dumps(events)


def test_blocking_send_message_returns_the_final_task(advisor, fake_model):
    body = rpc(advisor(fake_model(*SCRIPT)), "SendMessage",
               message([{"data": {"ad": AD, "offer": OFFER}}])["params"])
    task = body["result"]["task"]
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    assert [a["name"] for a in task["artifacts"]] == [
        "ui_sync:search_occupations", "ui_sync:get_occupation_salary", "memo"]


def test_cancel_a_running_task(advisor, fake_model):
    import threading
    import time

    abandoned = threading.Event()

    async def slow():
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            abandoned.set()
            raise
        return Reply("too late", [])

    client = advisor(fake_model(forever=slow))
    params = message([{"text": AD}], method="SendMessage")["params"] | {
        "configuration": {"returnImmediately": True}}
    task_id = rpc(client, "SendMessage", params)["result"]["task"]["id"]
    assert rpc(client, "CancelTask", {"id": task_id})["result"]["status"]["state"] == \
        "TASK_STATE_CANCELED"
    assert rpc(client, "GetTask", {"id": task_id})["result"]["status"]["state"] == \
        "TASK_STATE_CANCELED"
    start = time.perf_counter()
    assert abandoned.wait(2), "the model call in flight was not abandoned"
    assert time.perf_counter() - start < 2


def test_concurrent_runs_both_complete(advisor, fake_model):  # FR-018
    from concurrent.futures import ThreadPoolExecutor

    client = advisor(fake_model(forever=Reply("Memo.", [])))
    with ThreadPoolExecutor(2) as pool:
        runs = list(pool.map(lambda _: stream(client, [{"text": AD}]), range(2)))
    assert [kind(r[-1]) for r in runs] == ["status:TASK_STATE_COMPLETED"] * 2


def test_same_context_runs_independently(advisor, fake_model):  # FR-011a
    model = fake_model(forever=Reply("Memo.", []))
    client = advisor(model)
    first = stream(client, [{"text": AD}])
    context = first[0]["task"]["contextId"]
    stream(client, [{"text": "And what about code 2421?"}], context_id=context)
    assert [len(messages) for messages, _ in model.seen] == [2, 2]
    assert model.seen[1][0][1]["content"] == "And what about code 2421?"


def test_request_content_is_not_logged(advisor, fake_model, caplog):  # FR-005
    import logging

    ad = "PRIVATE-AD-TEXT for a backend developer"
    offer = OFFER | {"monthly_salary_sek": 41234}
    script = (call("search_occupations", {"request": {"text": ad}}),
              call("evaluate_permit_eligibility", {"request": offer | {"code": "2512"}}, "c2"),
              Reply("Memo.", []))
    client = advisor(fake_model(*script))
    with caplog.at_level(logging.DEBUG):
        events = stream(client, [{"data": {"ad": ad, "offer": offer}}])
        failed = stream(client, [{"data": {"ad": ad, "offer": offer | {"fte_percent": 0}}}])
    assert kind(events[-1]) == "status:TASK_STATE_COMPLETED"
    assert kind(failed[-1]) == "status:TASK_STATE_FAILED"
    assert "PRIVATE-AD-TEXT" not in caplog.text and "41234" not in caplog.text
    assert "41234" not in status_text(failed[-1]) and "PRIVATE" not in status_text(failed[-1])


def test_validator_messages_do_not_echo_values(advisor, fake_model):  # Copilot review on PR #3
    offer = OFFER | {"exemptions": ["PRIVATE-AD-TEXT"]}
    events = stream(advisor(fake_model()), [{"data": {"ad": AD, "offer": offer}}])
    text = status_text(events[-1])
    assert kind(events[-1]) == "status:TASK_STATE_FAILED"
    assert "exemptions" in text and "unknown exemptions" in text and "PRIVATE" not in text


@pytest.mark.parametrize("background", [123, 0])
def test_a_non_string_background_is_rejected_with_text_parts(advisor, fake_model, background):
    model = fake_model(Reply("Memo.", []))  # Copilot review on PR #3
    events = stream(advisor(model), [{"data": {"ad": AD, "background": background}},
                                     {"text": "Also speaks Swedish."}])
    assert kind(events[-1]) == "status:TASK_STATE_FAILED"
    assert "background" in status_text(events[-1]) and model.seen == []


@pytest.fixture
def no_key_app(fixture_engine, salaries, monkeypatch):
    from lonekrav.app import create_app

    monkeypatch.delenv("OPENROUTER_KEY", raising=False)
    engine, profiles = fixture_engine
    with TestClient(create_app(engine=engine, profiles=profiles, salaries=salaries)) as client:
        yield client


def test_no_key_card_is_served(no_key_app):
    assert no_key_app.get("/.well-known/agent-card.json").json()["name"] == "lonekrav-advisor"


def test_no_key_message_is_rejected_quickly(no_key_app):  # FR-017, SC-005
    import time

    start = time.perf_counter()
    events = stream(no_key_app, [{"data": {"ad": AD, "offer": OFFER}}])
    assert time.perf_counter() - start < 1
    assert [kind(e) for e in events] == ["task:TASK_STATE_SUBMITTED",
                                         "status:TASK_STATE_REJECTED"]
    assert "Agent unavailable" in status_text(events[-1])
    assert "OPENROUTER_KEY" in status_text(events[-1])


def test_no_key_everything_else_works(no_key_app):
    from fastmcp import Client

    async def salary():
        async with Client(no_key_app.app.state.mcp) as c:
            return await c.call_tool("get_occupation_salary", {"code": "2512"})
    assert not asyncio.run(salary()).is_error
    assert no_key_app.get("/api/v1/health").status_code == 200


def test_the_key_selects_the_openrouter_model(fixture_engine, salaries, monkeypatch):
    import lonekrav.app

    chosen = []
    monkeypatch.setattr(lonekrav.app, "openrouter_model",
                        lambda key, model: chosen.append((key, model)) or object())
    monkeypatch.setenv("OPENROUTER_KEY", "sk-or-SENTINEL")
    monkeypatch.delenv("LONEKRAV_LLM_MODEL", raising=False)
    engine, profiles = fixture_engine
    app = lonekrav.app.create_app(engine=engine, profiles=profiles, salaries=salaries)
    monkeypatch.setenv("LONEKRAV_LLM_MODEL", "some/other-model")
    lonekrav.app.create_app(engine=engine, profiles=profiles, salaries=salaries)
    monkeypatch.setenv("LONEKRAV_LLM_MODEL", "")  # docker compose passes an unset variable as ""
    lonekrav.app.create_app(engine=engine, profiles=profiles, salaries=salaries)

    from lonekrav.protocols.agent.loop import DEFAULT_MODEL
    assert chosen == [("sk-or-SENTINEL", DEFAULT_MODEL), ("sk-or-SENTINEL", "some/other-model"),
                      ("sk-or-SENTINEL", DEFAULT_MODEL)]
    with TestClient(app) as client:
        assert "SENTINEL" not in client.get("/.well-known/agent-card.json").text
