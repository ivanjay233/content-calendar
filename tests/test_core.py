"""Tests for Content Calendar models and core logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
import yaml

from content_calendar.core import CalendarManager, create_calendar
from content_calendar.exporter import Exporter
from content_calendar.models import (
    ContentCalendar,
    ContentItem,
    ContentStatus,
    ContentType,
    Platform,
    ScheduleSlot,
)
from content_calendar.planner import TopicGenerator


class TestContentItem:
    """Tests for the ContentItem model."""

    def test_create_content_item(self):
        """Test creating a basic content item."""
        item = ContentItem(
            title="Test Post",
            content_type=ContentType.BLOG_POST,
            platform=Platform.BLOG,
        )
        assert item.title == "Test Post"
        assert item.content_type == ContentType.BLOG_POST
        assert item.platform == Platform.BLOG
        assert item.status == ContentStatus.DRAFT
        assert len(item.id) == 12

    def test_content_item_defaults(self):
        """Test that default values are set correctly."""
        item = ContentItem(
            title="Defaults Test",
            content_type=ContentType.SOCIAL_POST,
            platform=Platform.TWITTER,
        )
        assert item.tags == []
        assert item.seo_keywords == []
        assert item.metadata == {}
        assert item.author is None
        assert item.scheduled_date is None

    def test_schedule_item(self):
        """Test scheduling a content item."""
        item = ContentItem(
            title="Scheduled Post",
            content_type=ContentType.BLOG_POST,
            platform=Platform.BLOG,
        )
        target_date = date(2025, 6, 15)
        item.schedule(target_date, "10:30")
        assert item.status == ContentStatus.SCHEDULED
        assert item.scheduled_date == target_date
        assert item.scheduled_time == "10:30"

    def test_publish_item(self):
        """Test publishing a content item."""
        item = ContentItem(
            title="Published Post",
            content_type=ContentType.ARTICLE,
            platform=Platform.LINKEDIN,
        )
        item.publish()
        assert item.status == ContentStatus.PUBLISHED

    def test_item_to_dict(self):
        """Test serialization to dictionary."""
        item = ContentItem(
            title="Dict Test",
            content_type=ContentType.VIDEO,
            platform=Platform.YOUTUBE,
            tags=["tutorial", "python"],
        )
        data = item.to_dict()
        assert data["title"] == "Dict Test"
        assert data["content_type"] == "video"
        assert data["platform"] == "youtube"
        assert data["tags"] == ["tutorial", "python"]

    def test_invalid_time_format(self):
        """Test that invalid time format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time format"):
            ContentItem(
                title="Bad Time",
                content_type=ContentType.BLOG_POST,
                platform=Platform.BLOG,
                scheduled_time="25:00",
            )


class TestContentCalendar:
    """Tests for the ContentCalendar collection."""

    def test_add_item(self):
        """Test adding items to the calendar."""
        calendar = ContentCalendar(name="Test Calendar")
        item = ContentItem(title="Item 1", content_type=ContentType.BLOG_POST, platform=Platform.BLOG)
        calendar.add_item(item)
        assert len(calendar.items) == 1
        assert calendar.items[0].title == "Item 1"

    def test_remove_item(self):
        """Test removing an item by ID."""
        calendar = ContentCalendar()
        item = ContentItem(title="Remove Me", content_type=ContentType.BLOG_POST, platform=Platform.BLOG)
        calendar.add_item(item)
        assert len(calendar.items) == 1
        removed = calendar.remove_item(item.id)
        assert removed is not None
        assert removed.title == "Remove Me"
        assert len(calendar.items) == 0

    def test_remove_nonexistent_item(self):
        """Test removing a nonexistent item returns None."""
        calendar = ContentCalendar()
        result = calendar.remove_item("nonexistent")
        assert result is None

    def test_get_items_by_status(self):
        """Test filtering items by status."""
        calendar = ContentCalendar()
        draft = ContentItem(title="Draft", content_type=ContentType.BLOG_POST, platform=Platform.BLOG)
        scheduled = ContentItem(title="Scheduled", content_type=ContentType.SOCIAL_POST, platform=Platform.TWITTER)
        scheduled.schedule(date.today() + timedelta(days=1))
        published = ContentItem(title="Published", content_type=ContentType.NEWSLETTER, platform=Platform.SUBSTACK)
        published.publish()

        calendar.add_item(draft)
        calendar.add_item(scheduled)
        calendar.add_item(published)

        drafts = calendar.get_items_by_status(ContentStatus.DRAFT)
        assert len(drafts) == 1
        assert drafts[0].title == "Draft"

        published_items = calendar.get_items_by_status(ContentStatus.PUBLISHED)
        assert len(published_items) == 1
        assert published_items[0].title == "Published"

    def test_get_items_by_date(self):
        """Test filtering items by scheduled date."""
        calendar = ContentCalendar()
        target = date(2025, 7, 4)

        item1 = ContentItem(title="July 4th", content_type=ContentType.BLOG_POST, platform=Platform.BLOG)
        item1.schedule(target)

        item2 = ContentItem(title="Other Day", content_type=ContentType.SOCIAL_POST, platform=Platform.TWITTER)
        item2.schedule(target + timedelta(days=1))

        calendar.add_item(item1)
        calendar.add_item(item2)

        result = calendar.get_items_by_date(target)
        assert len(result) == 1
        assert result[0].title == "July 4th"

    def test_get_upcoming(self):
        """Test getting upcoming items within a window."""
        calendar = ContentCalendar()
        today = date.today()
        item1 = ContentItem(title="Tomorrow", content_type=ContentType.BLOG_POST, platform=Platform.BLOG)
        item1.schedule(today + timedelta(days=1))
        item2 = ContentItem(title="Next Week", content_type=ContentType.SOCIAL_POST, platform=Platform.TWITTER)
        item2.schedule(today + timedelta(days=5))
        item3 = ContentItem(title="Far Future", content_type=ContentType.VIDEO, platform=Platform.YOUTUBE)
        item3.schedule(today + timedelta(days=30))

        calendar.add_item(item1)
        calendar.add_item(item2)
        calendar.add_item(item3)

        upcoming = calendar.get_upcoming(days=7)
        assert len(upcoming) == 2
        assert upcoming[0].title == "Tomorrow"

    def test_count_by_type(self):
        """Test counting items grouped by content type."""
        calendar = ContentCalendar()
        calendar.add_item(ContentItem(title="Blog 1", content_type=ContentType.BLOG_POST, platform=Platform.BLOG))
        calendar.add_item(ContentItem(title="Blog 2", content_type=ContentType.BLOG_POST, platform=Platform.BLOG))
        calendar.add_item(ContentItem(title="Social 1", content_type=ContentType.SOCIAL_POST, platform=Platform.TWITTER))

        counts = calendar.count_by_type()
        assert counts["blog_post"] == 2
        assert counts["social_post"] == 1

    def test_calendar_to_dict(self):
        """Test calendar serialization."""
        calendar = ContentCalendar(name="Serialize Test")
        item = ContentItem(title="Test", content_type=ContentType.BLOG_POST, platform=Platform.BLOG)
        calendar.add_item(item)

        data = calendar.to_dict()
        assert data["name"] == "Serialize Test"
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Test"


class TestCalendarManager:
    """Tests for the CalendarManager service."""

    def test_create_calendar_factory(self):
        """Test the create_calendar factory function."""
        calendar = create_calendar("My Calendar")
        assert isinstance(calendar, ContentCalendar)
        assert calendar.name == "My Calendar"

    def test_add_content(self):
        """Test adding content through the manager."""
        manager = CalendarManager()
        item = manager.add_content(
            title="Manager Test",
            content_type=ContentType.BLOG_POST,
            platform=Platform.BLOG,
            tags=["test"],
        )
        assert item.title == "Manager Test"
        assert item.tags == ["test"]
        assert len(manager.calendar.items) == 1

    def test_generate_schedule(self):
        """Test schedule generation creates items."""
        manager = CalendarManager()
        start = date(2025, 1, 6)  # Monday
        items = manager.generate_schedule(start_date=start, days=5)
        # 5 weekdays, no weekends in this range
        assert len(items) > 0
        assert all(item.scheduled_date is not None for item in items)

    def test_save_and_load_calendar(self):
        """Test saving and loading a calendar from disk."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "calendar.json"
            manager = CalendarManager()
            manager.add_content("Save Test", ContentType.BLOG_POST, Platform.BLOG)
            manager.save_calendar(str(path))

            assert path.exists()
            assert path.stat().st_size > 0

            manager2 = CalendarManager()
            manager2.load_calendar(str(path))
            assert len(manager2.calendar.items) == 1
            assert manager2.calendar.items[0].title == "Save Test"

    def test_get_stats(self):
        """Test calendar statistics."""
        manager = CalendarManager()
        manager.add_content("Draft 1", ContentType.BLOG_POST, Platform.BLOG)
        manager.add_content("Draft 2", ContentType.SOCIAL_POST, Platform.TWITTER)
        item = manager.add_content("Scheduled 1", ContentType.ARTICLE, Platform.LINKEDIN)
        item.schedule(date.today() + timedelta(days=1))

        stats = manager.get_stats()
        assert stats["total_items"] == 3
        assert stats["drafts"] == 2
        assert stats["scheduled"] == 1
        assert stats["published"] == 0


class TestExporter:
    """Tests for the Exporter module."""

    @pytest.fixture
    def calendar(self):
        """Create a populated calendar for export tests."""
        cal = ContentCalendar(name="Export Test")
        cal.add_item(ContentItem(
            title="Export Item 1",
            content_type=ContentType.BLOG_POST,
            platform=Platform.BLOG,
            scheduled_date=date(2025, 8, 1),
            tags=["test"],
        ))
        cal.add_item(ContentItem(
            title="Export Item 2",
            content_type=ContentType.SOCIAL_POST,
            platform=Platform.TWITTER,
            scheduled_date=date(2025, 8, 2),
        ))
        return cal

    def test_export_csv(self, calendar):
        """Test CSV export."""
        exporter = Exporter(calendar)
        content = exporter.export("csv")
        assert "ID" in content
        assert "Title" in content
        assert "Export Item 1" in content
        assert "Export Item 2" in content

    def test_export_json(self, calendar):
        """Test JSON export."""
        exporter = Exporter(calendar)
        content = exporter.export("json")
        assert '"name": "Export Test"' in content
        assert '"title": "Export Item 1"' in content

    def test_export_markdown(self, calendar):
        """Test Markdown export."""
        exporter = Exporter(calendar)
        content = exporter.export("markdown")
        assert "# Export Test" in content
        assert "Export Item 1" in content
        assert "|" in content

    def test_export_invalid_format(self, calendar):
        """Test that invalid format raises error."""
        exporter = Exporter(calendar)
        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export("pdf")

    def test_export_to_file(self, calendar):
        """Test exporting to a file."""
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            exporter = Exporter(calendar)
            exporter.export("csv", output_path=str(path))
            assert path.exists()
            assert path.stat().st_size > 0


class TestTopicGenerator:
    """Tests for the TopicGenerator."""

    def test_generate_topics(self):
        """Test basic topic generation."""
        generator = TopicGenerator(seed_topics=["AI"])
        topics = generator.generate_topics(count=5)
        assert len(topics) == 5
        for topic in topics:
            assert "title" in topic
            assert "content_type" in topic
            assert "suggested_platform" in topic

    def test_generate_specific_type(self):
        """Test generating topics for a specific content type."""
        generator = TopicGenerator()
        topics = generator.generate_topics(count=3, content_types=[ContentType.VIDEO])
        assert len(topics) == 3
        for topic in topics:
            assert topic["content_type"] == "video"

    def test_suggest_tags(self):
        """Test tag suggestion."""
        generator = TopicGenerator()
        tags = generator.suggest_tags("How to build AI tools for productivity")
        assert len(tags) >= 3

    def test_generate_dates(self):
        """Test date generation (weekdays only)."""
        dates = TopicGenerator.generate_dates(count=10)
        assert len(dates) == 10
        for d in dates:
            assert d.weekday() < 5  # Monday-Friday


class TestScheduleSlot:
    """Tests for the ScheduleSlot model."""

    def test_create_schedule_slot(self):
        """Test creating a schedule slot."""
        slot = ScheduleSlot(
            day_of_week="monday",
            time="09:00",
            platform=Platform.BLOG,
            content_type=ContentType.BLOG_POST,
        )
        assert slot.day_of_week == "monday"
        assert slot.time == "09:00"
        assert slot.platform == Platform.BLOG

    def test_invalid_slot_time(self):
        """Test that invalid time raises validation error."""
        with pytest.raises(Exception):
            ScheduleSlot(
                day_of_week="monday",
                time="9:00",  # Missing leading zero
                platform=Platform.BLOG,
                content_type=ContentType.BLOG_POST,
            )
