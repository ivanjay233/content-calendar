"""Core calendar management logic."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml

from content_calendar.models import (
    CalendarConfig,
    ContentCalendar,
    ContentItem,
    ContentStatus,
    ContentType,
    Platform,
)


class CalendarManager:
    """Manages the content calendar lifecycle."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config: CalendarConfig = CalendarConfig()
        self.calendar: ContentCalendar = ContentCalendar()
        self.config_path = config_path or os.environ.get(
            "CONTENT_CALENDAR_CONFIG", "config.yaml"
        )

    def load_config(self, path: Optional[str] = None) -> CalendarConfig:
        """Load configuration from a YAML file."""
        config_file = path or self.config_path
        if not os.path.exists(config_file):
            msg = f"Configuration file not found: {config_file}"
            raise FileNotFoundError(msg)

        with open(config_file) as f:
            data = yaml.safe_load(f)

        cfg = data.get("calendar", {})
        self.config = CalendarConfig(**cfg)

        if "name" in data.get("calendar", {}):
            self.calendar.name = data["calendar"]["name"]

        return self.config

    def load_calendar(self, path: Optional[str] = None) -> ContentCalendar:
        """Load calendar data from a JSON file."""
        filepath = path or self._get_storage_path()
        if not os.path.exists(filepath):
            self.calendar = ContentCalendar()
            return self.calendar

        with open(filepath) as f:
            data = json.load(f)

        items = [ContentItem(**item) for item in data.get("items", [])]
        self.calendar = ContentCalendar(
            name=data.get("name", "Content Calendar"),
            items=items,
        )
        return self.calendar

    def save_calendar(self, path: Optional[str] = None) -> None:
        """Save calendar data to a JSON file."""
        filepath = path or self._get_storage_path()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.calendar.to_dict(), f, indent=2)

    def add_content(
        self,
        title: str,
        content_type: ContentType,
        platform: Platform,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        scheduled_date: Optional[date] = None,
    ) -> ContentItem:
        """Create and add a new content item."""
        item = ContentItem(
            title=title,
            description=description,
            content_type=content_type,
            platform=platform,
            tags=tags or [],
            scheduled_date=scheduled_date,
        )
        self.calendar.add_item(item)
        return item

    def generate_schedule(
        self,
        start_date: Optional[date] = None,
        days: int = 30,
        platforms: Optional[list[Platform]] = None,
    ) -> list[ContentItem]:
        """Generate a content schedule by creating placeholder items on each weekday."""
        start = start_date or date.today()
        targets = platforms or [p for p in Platform]

        created: list[ContentItem] = []
        for day_offset in range(days):
            current = start + timedelta(days=day_offset)
            if current.weekday() >= 5:  # skip weekends
                continue

            for platform in targets:
                content_type = self._default_type_for_platform(platform)
                item = ContentItem(
                    title=f"Untitled ({platform.value} - {current.isoformat()})",
                    content_type=content_type,
                    platform=platform,
                    status=ContentStatus.DRAFT,
                    scheduled_date=current,
                )
                self.calendar.add_item(item)
                created.append(item)

        return created

    def get_stats(self) -> dict:
        """Get calendar statistics."""
        total = len(self.calendar.items)
        by_status = self.calendar.count_by_type()
        scheduled = len(self.calendar.get_items_by_status(ContentStatus.SCHEDULED))
        published = len(self.calendar.get_items_by_status(ContentStatus.PUBLISHED))
        drafts = len(self.calendar.get_items_by_status(ContentStatus.DRAFT))

        return {
            "total_items": total,
            "scheduled": scheduled,
            "published": published,
            "drafts": drafts,
            "by_type": by_status,
            "upcoming_7_days": len(self.calendar.get_upcoming(7)),
        }

    def _get_storage_path(self) -> str:
        """Resolve the storage file path."""
        if hasattr(self.config, "calendar") and hasattr(self.config, "timezone"):
            return "./data/calendar.json"
        return os.environ.get("CONTENT_CALENDAR_FILE", "./data/calendar.json")

    @staticmethod
    def _default_type_for_platform(platform: Platform) -> ContentType:
        """Get the default content type for a platform."""
        mapping = {
            Platform.BLOG: ContentType.BLOG_POST,
            Platform.TWITTER: ContentType.SOCIAL_POST,
            Platform.LINKEDIN: ContentType.ARTICLE,
            Platform.YOUTUBE: ContentType.VIDEO,
            Platform.SUBSTACK: ContentType.NEWSLETTER,
            Platform.WEBSITE: ContentType.BLOG_POST,
        }
        return mapping.get(platform, ContentType.BLOG_POST)


def create_calendar(name: str = "Content Calendar") -> ContentCalendar:
    """Factory function to create a new calendar."""
    return ContentCalendar(name=name)
