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

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the server

```bash
python manage.py migrate      # applies Django's built-in migrations
python manage.py runserver
```

The home page is served at http://127.0.0.1:8000/ and currently returns a
plain-text placeholder.

## Run the tests

```bash
pytest
```

Pytest is configured in [`pyproject.toml`](./pyproject.toml)
(`DJANGO_SETTINGS_MODULE = "config.settings"`). The smoke test in
[`tests/test_smoke.py`](./tests/test_smoke.py) asserts the project imports and
that `GET /` returns `200`.
