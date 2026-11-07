from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import tomllib


@dataclass(frozen=True)
class Config:
    channel_name: str = "Little Wonder Friends"
    audience: str = "children aged 4–8"
    language: str = "en-US"
    min_duration: float = 25
    max_duration: float = 40
    width: int = 1080
    height: int = 1920
    fps: int = 30
    timezone: str = "Asia/Colombo"
    target_time: str = "18:15"
    expected_channel_id: str = ""
    region: str = "US"
    category_name: str = "Education"
    upload_enabled: bool = False
    contains_synthetic_media: bool = False

    @classmethod
    def load(cls, path="config.toml"):
        config = cls(**tomllib.loads(Path(path).read_text()))
        ZoneInfo(config.timezone)
        if (config.width, config.height, config.fps) != (1080, 1920, 30):
            raise ValueError("The validated renderer requires 1080x1920 at 30 fps")
        if config.language != "en-US":
            raise ValueError("This content pack and voice support en-US; add a reviewed language pack first")
        if not 25 <= config.min_duration <= config.max_duration <= 40:
            raise ValueError("Duration must be within 25–40 seconds")
        datetime.strptime(config.target_time, "%H:%M")
        if not config.channel_name.strip() or len(config.channel_name) > 60:
            raise ValueError("Channel name must contain 1–60 characters")
        return config

    def live_enabled(self):
        # Explicit repository variable is the final opt-in; config alone cannot publish.
        return self.upload_enabled and os.getenv("UPLOAD_ENABLED", "false").lower() == "true"


def job_id(config, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Use a timezone-aware datetime")
    return "wonder-" + now.astimezone(ZoneInfo(config.timezone)).date().isoformat()
