from datetime import datetime, timezone

from app.agent.local_llm import LocalLLM, PROMPT_VERSION


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


def test_local_llm_returns_none_for_malformed_model_output():
    assert LocalLLM._parse_content("not JSON") is None
    assert LocalLLM._parse_content(None) is None


def test_local_llm_returns_none_for_malformed_response_envelope(monkeypatch):
    for response_data in (None, {}, {"message": None}, {"message": {}}):
        monkeypatch.setattr(
            "app.agent.local_llm.requests.post",
            lambda *args, **kwargs: FakeResponse(response_data),
        )

        assert LocalLLM().understand("revise") is None


def test_local_llm_uses_fixed_clock_and_timeout(monkeypatch):
    captured_request = {}

    def fake_post(url, **kwargs):
        captured_request["url"] = url
        captured_request.update(kwargs)
        return FakeResponse(
            {
                "message": {
                    "content": (
                        '{"action":"create_task","title":"revise",'
                        '"description":null,"priority":null,"deadline":null}'
                    )
                }
            }
        )

    monkeypatch.setattr("app.agent.local_llm.requests.post", fake_post)
    fixed_now = datetime(2026, 9, 24, 10, 30, tzinfo=timezone.utc)
    llm = LocalLLM(
        now_provider=lambda: fixed_now,
        request_timeout_seconds=7,
    )

    intent = llm.understand("revise")

    assert intent is not None
    assert intent.title == "revise"
    assert captured_request["timeout"] == 7
    assert fixed_now.isoformat() in captured_request["json"]["messages"][0][
        "content"
    ]
    assert llm.prompt_version == PROMPT_VERSION
