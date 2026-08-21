from __future__ import annotations

from types import SimpleNamespace

from app.services.openclaw_runtime import OpenClawHttpRuntime
from app.services.retrieval import RetrievedContext


def test_openclaw_runtime_calls_chat_completions(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "choices": [
                    {"message": {"content": "Answer from OpenClaw", "tool_calls": []}}
                ]
            }

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("app.services.openclaw_runtime.httpx.post", fake_post)

    runtime = OpenClawHttpRuntime(
        base_url="https://gateway.example.test",
        api_key="gateway-token",
        model="openclaw/default",
    )
    context = RetrievedContext(query="Where did I meet Alex?")

    result = runtime.run(query="Where did I meet Alex?", context=context, tools=())

    assert result.answer == "Answer from OpenClaw"
    assert captured["url"] == "https://gateway.example.test/v1/chat/completions"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer gateway-token"
    assert captured["kwargs"]["json"]["model"] == "openclaw/default"
    assert "EVIDENCE:" in captured["kwargs"]["json"]["messages"][1]["content"]


def test_openclaw_runtime_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.setattr(
        "app.services.openclaw_runtime.settings",
        SimpleNamespace(openclaw_base_url="", openclaw_api_key=None, llm_model=""),
    )

    runtime = OpenClawHttpRuntime()
    context = RetrievedContext(query="test")

    try:
        runtime.run(query="test", context=context, tools=())
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 503
        assert "not configured" in str(getattr(exc, "detail", ""))
    else:
        raise AssertionError("Unconfigured OpenClaw runtime must fail closed")
