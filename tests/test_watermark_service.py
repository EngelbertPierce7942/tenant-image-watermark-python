import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.watermark_service import CreatorImage, InfraiImageClient, publishing_decision, watermark_before_publish


def test_empty_mark_blocks_publish():
    image = CreatorImage("draft.png", b"bytes", "  ")
    decision = publishing_decision(image)
    assert decision.allowed is False
    assert decision.reason == "watermark text is required"


def test_mark_allows_publish():
    image = CreatorImage("draft.png", b"bytes", "Tenant 42")
    assert publishing_decision(image).allowed is True


def test_upload_and_process_request_shapes():
    client = InfraiImageClient(api_key="test")
    calls = []

    def post(path, payload):
        calls.append((path, payload))
        return {"data": {"image_id": "pim_test"}}

    client._post = post
    watermark_before_publish(client, CreatorImage("draft.png", b"\x00\xff", "Tenant 42"))
    assert calls == [
        ("/v1/image/upload", {"file": "AP8=", "filename": "draft.png"}),
        ("/v1/image/process", {
            "image": {"image_id": "pim_test"},
            "ops": [{"op": "watermark", "params": {
                "text": "Tenant 42", "position": "bottom-right", "opacity": 0.75,
            }}],
        }),
    ]
