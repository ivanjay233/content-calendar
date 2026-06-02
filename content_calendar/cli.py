"""Command-line interface for Content Calendar."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from content_calendar import __version__
from content_calendar.core import CalendarManager
from content_calendar.exporter import Exporter
from content_calendar.models import ContentStatus, ContentType, Platform
from content_calendar.planner import TopicGenerator

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="content-calendar")
def cli() -> None:
    """AI-powered content planning and scheduling tool."""


@cli.command()
@click.option("--name", default="My Content Calendar", help="Calendar name")
@click.option("--config", default="config.yaml", help="Config file path")
def init(name: str, config: str) -> None:
    """Initialize a new content calendar."""
    manager = CalendarManager(config_path=config)
    manager.calendar.name = name
    manager.save_calendar()

    console.print(Panel(f"[green]✓[/] Created calendar: [bold]{name}[/]", title="Content Calendar"))
    console.print(f"  Data stored in: {manager._get_storage_path()}")


@cli.group()
def topics() -> None:
    """Manage content topics."""


@topics.command(name="generate")
@click.option("--seed", multiple=True, help="Seed topics for generation")
@click.option("--count", default=10, help="Number of topics to generate")
@click.option("--type", "content_type", multiple=True, help="Content types to generate for")
def topics_generate(seed: tuple[str, ...], count: int, content_type: tuple[str, ...]) -> None:
    """Generate content topic ideas."""
    seeds = list(seed) if seed else None
    generator = TopicGenerator(seed_topics=seeds)

    if content_type:
        types = [ContentType(t) for t in content_type]
    else:
        types = None

    topics_list = generator.generate_topics(count=count, content_types=types)

    table = Table(title=f"Generated {len(topics_list)} Topics")
    table.add_column("#", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Platform", style="blue")

    for idx, topic in enumerate(topics_list, 1):
        table.add_row(str(idx), topic["title"], topic["content_type"], topic["suggested_platform"])

    console.print(table)


@cli.command()
@click.option("--days", default=30, help="Number of days to schedule")
@click.option("--start", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--platform", multiple=True, help="Platforms to include")
def plan(days: int, start: Optional[str], platform: tuple[str, ...]) -> None:
    """Generate a content schedule."""
    manager = CalendarManager()
    start_date = date.fromisoformat(start) if start else None

    platforms = [Platform(p) for p in platform] if platform else None
    created = manager.generate_schedule(start_date=start_date, days=days, platforms=platforms)
    manager.save_calendar()

    table = Table(title=f"Scheduled {len(created)} Items")
    table.add_column("Date", style="yellow")
    table.add_column("Platform", style="blue")
    table.add_column("Type", style="green")
    table.add_column("Status", style="magenta")

    for item in created[:20]:
        table.add_row(
            item.scheduled_date.isoformat() if item.scheduled_date else "—",
            item.platform.value,
            item.content_type.value,
            item.status.value,
        )

    if len(created) > 20:
        console.print(f"\n[dim]... and {len(created) - 20} more items[/]")

    console.print(table)
    console.print(f"\n[green]✓[/] Calendar saved with {len(created)} new items")


@cli.command()
@click.option("--format", "fmt", default="csv", help="Export format")
@click.option("--output", "-o", default=None, help="Output file path")
def export(fmt: str, output: Optional[str]) -> None:
    """Export the content calendar."""
    manager = CalendarManager()
    try:
        manager.load_calendar()
    except FileNotFoundError:
        console.print("[red]✗[/] No calendar found. Run [bold]content-calendar init[/] first.")
        return

    exporter = Exporter(manager.calendar)
    content = exporter.export(fmt, output_path=output)

    if output:
        console.print(f"[green]✓[/] Exported to [bold]{output}[/] ({len(content)} bytes)")
    else:
        console.print(content)


@cli.command()
def stats() -> None:
    """Show calendar statistics."""
    manager = CalendarManager()
    try:
        manager.load_calendar()
    except FileNotFoundError:
        console.print("[red]✗[/] No calendar found. Run [bold]content-calendar init[/] first.")
        return

    stats_data = manager.get_stats()

    info = Panel(
        f"[bold]Total Items:[/] {stats_data['total_items']}\n"
        f"[bold]Scheduled:[/] {stats_data['scheduled']}\n"
        f"[bold]Published:[/] {stats_data['published']}\n"
        f"[bold]Drafts:[/] {stats_data['drafts']}\n"
        f"[bold]Upcoming (7 days):[/] {stats_data['upcoming_7_days']}\n"
        f"[bold]By Type:[/] {stats_data['by_type']}",
        title="Calendar Statistics",
    )
    console.print(info)


@cli.command()
def list() -> None:  # noqa: A001
    """List all content items."""
    manager = CalendarManager()
    try:
        manager.load_calendar()
    except FileNotFoundError:
        console.print("[red]✗[/] No calendar found. Run [bold]content-calendar init[/] first.")
        return

    if not manager.calendar.items:
        console.print("[yellow]⚠[/] Calendar is empty. Add items or run [bold]content-calendar plan[/].")
        return

    table = Table(title=f"Content Calendar: {manager.calendar.name}")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title", style="cyan")
    table.add_column("Date", style="yellow")
    table.add_column("Type", style="green")
    table.add_column("Platform", style="blue")
    table.add_column("Status", style="magenta")

    for item in manager.calendar.items:
        table.add_row(
            item.id,
            item.title[:40],
            item.scheduled_date.isoformat() if item.scheduled_date else "—",
            item.content_type.value,
            item.platform.value,
            item.status.value,
        )

    console.print(table)


if __name__ == "__main__":
    cli()
