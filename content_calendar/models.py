"""Content Calendar data models."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ContentType(str, Enum):
    """Supported content types."""

    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    NEWSLETTER = "newsletter"
    VIDEO = "video"
    TUTORIAL = "tutorial"
    THREAD = "thread"
    ARTICLE = "article"


class ContentStatus(str, Enum):
    """Content lifecycle status."""

    DRAFT = "draft"
    REVIEW = "review"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class Platform(str, Enum):
    """Supported publishing platforms."""

    BLOG = "blog"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    SUBSTACK = "substack"
    WEBSITE = "website"


class CalendarConfig(BaseModel):
    """Top-level calendar configuration."""

    name: str = "My Content Calendar"
    timezone: str = "UTC"
    default_content_type: ContentType = ContentType.BLOG_POST


class ScheduleSlot(BaseModel):
    """A scheduled time slot for content publishing."""

    day_of_week: str = Field(..., description="Day of week (monday-sunday)")
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    platform: Platform
    content_type: ContentType


class ContentItem(BaseModel):
    """A single piece of planned content."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    title: str
    description: Optional[str] = None
    content_type: ContentType
    platform: Platform
    status: ContentStatus = ContentStatus.DRAFT
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)
    author: Optional[str] = None
    url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("scheduled_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not __import__("re").match(r"^\d{2}:\d{2}$", v):
            msg = f"Invalid time format: {v!r}. Use HH:MM"
            raise ValueError(msg)
        return v

    def schedule(self, target_date: date, target_time: Optional[str] = None) -> None:
        """Schedule this content item for publishing."""
        self.status = ContentStatus.SCHEDULED
        self.scheduled_date = target_date
        if target_time:
            self.scheduled_time = target_time
        self.updated_at = datetime.utcnow()

    def publish(self) -> None:
        """Mark content as published."""
        self.status = ContentStatus.PUBLISHED
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize to a dictionary."""
        return self.model_dump(mode="json")


class ContentCalendar(BaseModel):
    """A collection of content items forming a calendar."""

    name: str = "Content Calendar"
    items: list[ContentItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_item(self, item: ContentItem) -> None:
        """Add a content item to the calendar."""
        self.items.append(item)
        self.updated_at = datetime.utcnow()

    def remove_item(self, item_id: str) -> Optional[ContentItem]:
        """Remove a content item by ID."""
        for idx, item in enumerate(self.items):
            if item.id == item_id:
                self.updated_at = datetime.utcnow()
                return self.items.pop(idx)
        return None

    def get_items_by_status(self, status: ContentStatus) -> list[ContentItem]:
        """Filter items by their status."""
        return [item for item in self.items if item.status == status]

    def get_items_by_date(self, target_date: date) -> list[ContentItem]:
        """Get all items scheduled for a specific date."""
        return [
            item
            for item in self.items
            if item.scheduled_date == target_date
        ]

    def get_upcoming(self, days: int = 7) -> list[ContentItem]:
        """Get items scheduled within the next N days."""
        today = date.today()
        cutoff = today + timedelta(days=days)
        return [
            item
            for item in self.items
            if item.scheduled_date and today <= item.scheduled_date <= cutoff
        ]

    def count_by_type(self) -> dict[str, int]:
        """Count content items grouped by type."""
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.content_type.value] = counts.get(item.content_type.value, 0) + 1
        return counts

    def to_dict(self) -> dict:
        """Serialize the entire calendar to a dictionary."""
        return {
            "name": self.name,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
