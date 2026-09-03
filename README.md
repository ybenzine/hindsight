# Hindsight

Team feedback cycles and retrospectives. See [`_docs/plan.md`](./_docs/plan.md)
and [`_docs/architecture.md`](./_docs/architecture.md) for the product and the
technical design.

## Status

Task 1 of the [backlog](./_docs/tasks.md): a runnable Django skeleton with a
passing smoke test. No apps, models, or database yet — the default SQLite
config from `django-admin startproject` is still in place and gets replaced in
task 2 (settings split + Postgres via docker-compose).

## Setup

Requires Python 3.14+. Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

This creates `.venv/` and installs the runtime and dev dependencies from
`pyproject.toml` / `uv.lock`.

## Run the server

```bash
uv run python manage.py migrate      # applies Django's built-in migrations
uv run python manage.py runserver
```

The home page is served at http://127.0.0.1:8000/ and currently returns a
plain-text placeholder.

## Run the tests

```bash
uv run pytest
```

Pytest is configured in [`pyproject.toml`](./pyproject.toml)
(`DJANGO_SETTINGS_MODULE = "config.settings"`). The smoke test in
[`tests/test_smoke.py`](./tests/test_smoke.py) asserts the project imports and
that `GET /` returns `200`.
