# Content Calendar

AI-powered content planning and scheduling system.

## Overview

Content Calendar helps you plan, organize, schedule, and export content across multiple platforms. It uses AI-assisted topic generation, smart scheduling algorithms, and multi-format export to streamline your content workflow.

## Features

- **AI-powered topic generation** — Discover content ideas from existing topics
- **Smart scheduling** — Optimal posting times based on platform patterns
- **Multi-format export** — CSV, JSON, Markdown, HTML, and iCalendar
- **Configurable content types** — Blog posts, social media, newsletters, videos
- **Pluggable backends** — Local file, Google Sheets, Airtable
- **CLI and Python API** — Use from command line or integrate into your code

## Installation

```bash
pip install content-calendar
```

## Quick Start

```bash
# Initialize a new calendar
content-calendar init

# Generate content topics
content-calendar topics generate --seed "AI productivity tools"

# Plan a schedule
content-calendar plan --days 30

# Export to calendar
content-calendar export --format csv
```

## Configuration

Copy and edit the example config:

```bash
cp examples/config.yaml.example config.yaml
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run linting
make lint
```

## License

MIT
