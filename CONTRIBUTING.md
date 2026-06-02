# Contributing

Thank you for considering contributing to Content Calendar!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/ivanjay233/content-calendar.git
cd content-calendar

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Code Guidelines

- **Type hints** — All public functions must have type annotations
- **Docstrings** — Use Google-style docstrings for public APIs
- **Testing** — New features must include tests
- **Formatting** — Run `make format` before committing

## Running Tests

```bash
make test        # Run tests with coverage
make lint        # Run ruff and mypy
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with descriptive commits
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `test:` — Tests
- `refactor:` — Code restructuring
- `ci:` — CI/CD changes
- `chore:` — Maintenance
