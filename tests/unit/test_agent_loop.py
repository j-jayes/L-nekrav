"""The advisor's tool loop against a scripted model (Feature 003 FR-012, FR-013, FR-015)."""

import asyncio
import json

import pytest

from lonekrav.core.advisor import THIRD_PARTY_NOTICE, AdvisorRequest
from lonekrav.protocols.agent.loop import (
    MAX_ROUNDS,
    SYSTEM_PROMPT,
    Memo,
    Progress,
    Reply,
    RoundLimit,
    ToolCall,
    ToolResult,
    run,
)


class FakeTools:
    def __init__(self, results):
        self.results, self.calls = results, []

    async def specs(self):
        return [{"type": "function", "function": {"name": n, "parameters": {}}}
                for n in self.results]

    async def call(self, name, args):
        self.calls.append((name, args))
        return self.results[name]


def call(name, args, id_="c1"):
    return Reply(None, [ToolCall(id_, name, json.dumps(args))])


def events(request, model, tools):
    async def go():
        return [e async for e in run(request, model, tools)]
    return asyncio.run(go())


SEARCH = {"hits": [{"code": "2512"}]}
SALARY = {"code": "2512", "distributions": []}
TOOLS = {"search_occupations": (False, SEARCH), "get_occupation_salary": (False, SALARY)}


def test_two_tools_then_a_memo(fake_model):
    model = fake_model(call("search_occupations", {"request": {"text": "dev"}}),
                       call("get_occupation_salary", {"code": "2512"}, "c2"),
                       Reply("Code 2512 fits.", []))
    out = events(AdvisorRequest(ad="dev"), model, FakeTools(TOOLS))
    assert [type(e) for e in out] == [Progress, ToolResult, Progress, ToolResult, Memo]
    assert out[1] == ToolResult("search_occupations", {"request": {"text": "dev"}}, SEARCH)
    assert out[3].result == SALARY
    assert out[-1].text.startswith("Code 2512 fits.") and THIRD_PARTY_NOTICE in out[-1].text
    tool_msgs = [m for m in model.seen[-1][0] if m["role"] == "tool"]
    assert [json.loads(m["content"]) for m in tool_msgs] == [SEARCH, SALARY]
    assert model.seen[0][1] == asyncio.run(FakeTools(TOOLS).specs())


def test_a_tool_error_goes_to_the_model_not_the_ui(fake_model):
    tools = FakeTools({"get_occupation_salary": (True, "unknown SSYK code '1234'")})
    model = fake_model(call("get_occupation_salary", {"code": "1234"}), Reply("Sorry.", []))
    out = events(AdvisorRequest(ad="dev"), model, tools)
    assert not any(isinstance(e, ToolResult) for e in out)
    assert "failed" in out[1].text
    assert model.seen[1][0][-1] == {"role": "tool", "tool_call_id": "c1",
                                    "content": "unknown SSYK code '1234'"}
    assert "not based on any Lönekrav result" in out[-1].text  # no tool succeeded


@pytest.mark.parametrize(("sent", "error"), [("{not json", "not valid JSON"),
                                             ("[1, 2]", "must be a JSON object")])
def test_arguments_that_are_not_a_json_object_are_reported_to_the_model(fake_model, sent, error):
    tools = FakeTools(TOOLS)
    model = fake_model(Reply(None, [ToolCall("c1", "search_occupations", sent)]),
                       Reply("Done.", []))
    events(AdvisorRequest(ad="dev"), model, tools)
    assert tools.calls == []
    assert error in model.seen[1][0][-1]["content"]


def test_a_model_that_never_stops_hits_the_round_limit(fake_model):
    model = fake_model(forever=call("search_occupations", {"request": {"text": "dev"}}))
    with pytest.raises(RoundLimit, match=str(MAX_ROUNDS)):
        events(AdvisorRequest(ad="dev"), model, FakeTools(TOOLS))
    assert len(model.seen) == MAX_ROUNDS


def test_a_model_error_propagates(fake_model):
    with pytest.raises(TimeoutError):
        events(AdvisorRequest(ad="dev"), fake_model(TimeoutError()), FakeTools(TOOLS))


def test_first_messages_are_the_prompt_and_the_request(fake_model):
    model = fake_model(Reply("Memo.", []))
    req = AdvisorRequest(ad="Backend developer", background="MSc, 5 years Python",
                         offer={"monthly_salary_sek": 52000, "fte_percent": 100,
                                "application_type": "first_permit", "filed_on": "2026-10-01"})
    events(req, model, FakeTools(TOOLS))
    system, user = model.seen[0][0]
    assert system == {"role": "system", "content": SYSTEM_PROMPT}
    assert user["role"] == "user"
    for text in ("Backend developer", "MSc, 5 years Python", '"monthly_salary_sek": 52000',
                 "2026-10-01"):
        assert text in user["content"]


def test_without_an_offer_the_model_is_told_not_to_check_eligibility(fake_model):
    model = fake_model(Reply("Memo.", []))
    events(AdvisorRequest(ad="Backend developer"), model, FakeTools(TOOLS))
    assert "No offer" in model.seen[0][0][1]["content"]


def test_plain_text_is_passed_through(fake_model):
    model = fake_model(Reply("Memo.", []))
    events("Backend developer, 52 000 a month, first permit", model, FakeTools(TOOLS))
    assert model.seen[0][0][1] == {"role": "user",
                                   "content": "Backend developer, 52 000 a month, first permit"}


class SchemaTools(FakeTools):
    async def specs(self):
        return [{"type": "function", "function": {"name": "search_occupations", "parameters": {
            "type": "object", "properties": {"request": {"$ref": "#/$defs/SearchRequest"},
                                             "note": {"type": "string"}}}}}]


@pytest.mark.parametrize("sent", ['{"text": "dev"}', '{"text": "dev"}}'])
def test_an_object_argument_sent_as_a_json_string_is_decoded(fake_model, sent):
    # Haiku 5.5 sends `request` as JSON text on its first call, with a stray closing brace
    # (references/a2a-stream.md); the leading object is what it meant.
    tools = SchemaTools(TOOLS)
    model = fake_model(call("search_occupations", {"request": sent, "note": '{"kept": "as text"}'}),
                       Reply("Memo.", []))
    events(AdvisorRequest(ad="dev"), model, tools)
    assert tools.calls == [("search_occupations",
                            {"request": {"text": "dev"}, "note": '{"kept": "as text"}'})]


def test_the_openrouter_client_has_a_timeout_and_one_retry(monkeypatch):  # FR-015
    import openai

    from lonekrav.protocols.agent.loop import OPENROUTER_URL, openrouter_model

    made = []
    monkeypatch.setattr(openai, "AsyncOpenAI", lambda **kw: made.append(kw))
    openrouter_model("sk-test")
    assert made == [{"base_url": OPENROUTER_URL, "api_key": "sk-test", "timeout": 30,
                     "max_retries": 1}]


def test_the_prompt_allows_market_context_but_never_choosing_by_it():  # Feature 005 FR-017
    prompt = " ".join(SYSTEM_PROMPT.split())
    assert "get_occupation_market" in prompt
    assert "Never use open ads or pay as a reason to prefer or rank a code" in prompt
    assert "with its source and date" in prompt
