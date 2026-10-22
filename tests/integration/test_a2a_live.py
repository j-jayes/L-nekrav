"""One real advisor run against OpenRouter (Feature 003 FR-020). Skipped without a key.

    uv run pytest -m live
"""

import json
import logging
import os

import pytest
from dotenv import dotenv_values

KEY = os.environ.get("OPENROUTER_KEY") or dotenv_values(".env").get("OPENROUTER_KEY")
AD = """Backend Developer (Python)

Responsibilities
- Design, build and maintain REST APIs in Python
- Run our services on AWS and keep them reliable

Requirements
- Several years of software development experience
"""
OFFER = {"monthly_salary_sek": 52000, "fte_percent": 100, "application_type": "first_permit",
         "filed_on": "2026-10-01"}

pytestmark = [pytest.mark.live,
              pytest.mark.skipif(not KEY, reason="OPENROUTER_KEY is not set (env or .env)")]


def test_a_real_model_writes_a_guarded_memo(fixture_engine, salaries, caplog):
    from fastapi.testclient import TestClient

    from lonekrav.app import create_app
    from lonekrav.core.advisor import THIRD_PARTY_NOTICE
    from lonekrav.core.search import HONEST_FIT
    from lonekrav.protocols.agent.loop import openrouter_model

    engine, profiles = fixture_engine
    app = create_app(engine=engine, profiles=profiles, salaries=salaries,
                     chat_model=openrouter_model(KEY))
    body = {"jsonrpc": "2.0", "id": 1, "method": "SendStreamingMessage", "params": {"message": {
        "messageId": "live-1", "role": "ROLE_USER", "parts": [{"data": {"ad": AD, "offer": OFFER}}]}}}
    with TestClient(app) as client, caplog.at_level(logging.DEBUG), \
            client.stream("POST", "/a2a", json=body, headers={"A2A-Version": "1.0"}) as r:
        events = [json.loads(line[5:])["result"] for line in r.iter_lines()
                  if line.startswith("data:")]

    final = events[-1]["statusUpdate"]["status"]
    assert final["state"] == "TASK_STATE_COMPLETED", final
    names = [e["artifactUpdate"]["artifact"]["name"] for e in events if "artifactUpdate" in e]
    assert any(n.startswith("ui_sync:") for n in names) and names[-1] == "memo"
    memo = next(e for e in events if "artifactUpdate" in e
                and e["artifactUpdate"]["artifact"]["name"] == "memo")
    text = memo["artifactUpdate"]["artifact"]["parts"][0]["text"]
    assert HONEST_FIT in text and text.endswith(THIRD_PARTY_NOTICE)
    assert KEY not in caplog.text  # FR-014
