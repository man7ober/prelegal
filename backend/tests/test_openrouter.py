import asyncio
import json

from prelegal_api import openrouter


def test_openrouter_uses_the_required_model_and_forced_schema_tool(monkeypatch) -> None:
    sent = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "document_intake",
                                        "arguments": json.dumps(
                                            {
                                                "action": "ask",
                                                "document_id": "mutual-nda",
                                                "message": "Who are the parties?",
                                                "suggested_document_id": None,
                                                "field_updates": [],
                                            }
                                        ),
                                    }
                                }
                            ]
                        }
                    }
                ]
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            sent.update(url=url, headers=headers, payload=json)
            return FakeResponse()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter.httpx, "AsyncClient", lambda timeout: FakeClient())
    result = asyncio.run(
        openrouter.request_intake(
            [{"role": "user", "content": "I need an NDA"}],
            {"catalog": [{"id": "mutual-nda", "title": "Mutual NDA"}], "selected_document": None},
        )
    )

    assert result["document_id"] == "mutual-nda"
    assert sent["payload"]["model"] == openrouter.OPENROUTER_MODEL
    assert sent["payload"]["tool_choice"]["function"]["name"] == "document_intake"
    tool = sent["payload"]["tools"][0]["function"]
    assert tool["strict"] is True
    assert tool["parameters"]["additionalProperties"] is False
