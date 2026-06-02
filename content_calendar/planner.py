"""AI-powered topic generation and content planning."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

from content_calendar.models import ContentItem, ContentType, Platform


class TopicGenerator:
    """Generates content topics using configurable strategies."""

    TOPIC_TEMPLATES: dict[ContentType, list[str]] = {
        ContentType.BLOG_POST: [
            "How to {action} {topic}",
            "The Ultimate Guide to {topic}",
            "{number} {adjective} Ways to {action} {topic}",
            "Why {topic} Matters in {year}",
            "Understanding {topic}: A Beginner's Guide",
        ],
        ContentType.SOCIAL_POST: [
            "Just discovered {topic}! 🚀",
            "Tip: {action} your {topic} game with this one trick",
            "Thread: {number} things I wish I knew about {topic}",
            "{topic} is changing — here's what you need to know",
        ],
        ContentType.NEWSLETTER: [
            "This Week in {topic}",
            "{topic} Digest: Top Stories and Insights",
            "Deep Dive: {topic} Trends for {year}",
        ],
        ContentType.VIDEO: [
            "Building {topic} from Scratch",
            "{topic} Tutorial for Beginners",
            "Reviewing the Latest in {topic}",
            "Reacting to {topic} News",
        ],
    }

    ADJECTIVES = [
        "Essential", "Powerful", "Simple", "Advanced", "Creative",
        "Effective", "Modern", "Practical", "Innovative", "Proven",
    ]

    ACTIONS = [
        "master", "improve", "optimize", "leverage", "automate",
        "build", "scale", "design", "implement", "integrate",
    ]

    def __init__(self, seed_topics: Optional[list[str]] = None) -> None:
        self.seed_topics = seed_topics or [
            "AI", "productivity", "remote work",
            "content marketing", "digital tools",
        ]

    def generate_topics(
        self,
        count: int = 10,
        content_types: Optional[list[ContentType]] = None,
    ) -> list[dict]:
        """Generate a list of content topic ideas."""
        types = content_types or list(ContentType)
        topics: list[dict] = []

        for _ in range(count):
            content_type = random.choice(types)
            topic = random.choice(self.seed_topics)
            template = random.choice(self.TOPIC_TEMPLATES.get(content_type, self.TOPIC_TEMPLATES[ContentType.BLOG_POST]))

            title = self._fill_template(template, topic=topic)
            topics.append({
                "title": title,
                "content_type": content_type.value,
                "seed_topic": topic,
                "suggested_platform": self._suggest_platform(content_type).value,
            })

        return topics

    def suggest_tags(self, topic: str, count: int = 5) -> list[str]:
        """Suggest relevant tags for a given topic."""
        words = topic.lower().replace("?", "").replace(",", "").split()
        words = [w for w in words if len(w) > 3 and w not in {"this", "that", "with", "from", "your"}]
        tags = list(set(words))

        while len(tags) < count:
            tags.append(random.choice(self.seed_topics).lower().replace(" ", ""))

        return tags[:count]

    def _fill_template(self, template: str, **kwargs: str) -> str:
        """Fill a template string with dynamic values."""
        filled = template.format(
            number=str(random.randint(3, 15)),
            adjective=random.choice(self.ADJECTIVES),
            action=random.choice(self.ACTIONS),
            year=str(date.today().year),
            **kwargs,
        )
        return filled

    @staticmethod
    def _suggest_platform(content_type: ContentType) -> Platform:
        mapping = {
            ContentType.BLOG_POST: Platform.BLOG,
            ContentType.SOCIAL_POST: Platform.TWITTER,
            ContentType.NEWSLETTER: Platform.SUBSTACK,
            ContentType.VIDEO: Platform.YOUTUBE,
            ContentType.TUTORIAL: Platform.BLOG,
            ContentType.THREAD: Platform.TWITTER,
            ContentType.ARTICLE: Platform.LINKEDIN,
        }
        return mapping.get(content_type, Platform.BLOG)

    @staticmethod
    def generate_dates(start: Optional[date] = None, count: int = 10) -> list[date]:
        """Generate a list of future dates (weekdays only)."""
        current = start or date.today()
        dates: list[date] = []
        while len(dates) < count:
            current += timedelta(days=1)
            if current.weekday() < 5:  # weekdays only
                dates.append(current)
        return dates
