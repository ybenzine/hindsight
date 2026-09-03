"""Smoke test: the project imports and the home URL responds."""


def test_project_imports():
    import config  # noqa: F401
    import config.wsgi  # noqa: F401


def test_home_url_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
