from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PublishResult:
    destination_dir: Path
    target_path: str
    published: bool = False
    public_url: str | None = None
    revision: str | None = None
