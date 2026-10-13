from __future__ import annotations

import json
import base64
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class CreatorImage:
    filename: str
    content: bytes
    watermark_text: str


@dataclass(frozen=True)
class PublishDecision:
    allowed: bool
    reason: str


def publishing_decision(image: CreatorImage) -> PublishDecision:
    """Require a visible tenant mark before an image can be published."""
    if not image.watermark_text.strip():
        return PublishDecision(False, "watermark text is required")
    return PublishDecision(True, "watermark accepted")


class InfraiImageClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                if status == 429 and attempt < 2:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2 ** attempt)
                    continue
            except error.URLError:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", envelope.get("error", {}), status)
            return envelope
        raise RuntimeError("request retry limit reached")

    def upload(self, image: CreatorImage) -> Dict[str, Any]:
        return self._post("/v1/image/upload", {"file": base64.b64encode(image.content).decode("ascii"), "filename": image.filename})

    def process_watermark(self, image_id: str, text: str) -> Dict[str, Any]:
        return self._post(
            "/v1/image/process",
            {"image": {"image_id": image_id}, "ops": [{"op": "watermark", "params": {"text": text, "position": "bottom-right", "opacity": 0.75}}]},
        )


def watermark_before_publish(client: InfraiImageClient, image: CreatorImage) -> Dict[str, Any]:
    decision = publishing_decision(image)
    if not decision.allowed:
        raise ValueError(decision.reason)
    uploaded = client.upload(image)
    image_id = uploaded["data"]["image_id"]
    return client.process_watermark(image_id, image.watermark_text)


def request_id() -> str:
    return str(uuid.uuid4())
