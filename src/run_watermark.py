import json
import os
import base64
from pathlib import Path

from watermark_service import CreatorImage, InfraiImageClient, watermark_before_publish


def main() -> None:
    filename = os.environ.get("CREATOR_IMAGE", "creator.png")
    sample_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lXcAAAAASUVORK5CYII="
    )
    content = Path(filename).read_bytes() if os.environ.get("CREATOR_IMAGE") else sample_png
    image = CreatorImage(filename=filename, content=content, watermark_text="Acme Studio")
    result = watermark_before_publish(InfraiImageClient(), image)
    print(json.dumps({"published": True, "result": result}, indent=2))


if __name__ == "__main__":
    main()
