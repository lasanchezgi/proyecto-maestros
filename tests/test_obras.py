import pytest
from flask import Flask

from app.web.routes.obras_routes import obras_bp


class MockCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.connection.queries.append((sql, params))

    def fetchone(self):
        if self.connection.fetchone_results:
            return self.connection.fetchone_results.pop(0)
        return None

    def fetchall(self):
        if self.connection.fetchall_results:
            return self.connection.fetchall_results.pop(0)
        return []

    def close(self):
        return None


class MockConnection:
    def __init__(self, *, fetchone_results=None, fetchall_results=None):
        self.queries = []
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])

    def cursor(self):
        return MockCursor(self)

    def close(self):
        return None


@pytest.fixture
def app_client():
    app = Flask(__name__)
    app.register_blueprint(obras_bp)
    return app.test_client()


def test_list_obras_with_location_filter(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(1,)],
        fetchall_results=[
            [
                (
                    1,
                    "Escultura",
                    10,
                    "Autor",
                    1999,
                    "Escultura",
                    "Comuna 1",
                    None,
                    None,
                    None,
                    6.27,
                    -75.55,
                )
            ]
        ],
    )

    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/obras?lat=6.27&lon=-75.55&radius=500")
    assert response.status_code == 200
    data = response.get_json()
    assert data["meta"]["total"] == 1
    assert data["meta"]["count"] == 1
    assert data["filters"]["lat"] == "6.27"
    assert any("ST_DWithin" in sql for sql, _ in connection.queries)
    assert connection.queries[0][1][-1] == 500


def test_list_obras_caps_limit(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(0,)],
        fetchall_results=[[]],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/obras?limit=500&offset=5")
    assert response.status_code == 200
    data = response.get_json()
    assert data["meta"]["limit"] == 100
    assert data["meta"]["offset"] == 5
    assert connection.queries[1][1][-2] == 100
    assert connection.queries[1][1][-1] == 5


def test_list_obras_invalid_location_params(app_client):
    response = app_client.get("/obras?lat=123&lon=-75&radius=500")
    assert response.status_code == 400
    assert "lat" in response.get_json()["error"].lower()

    response = app_client.get("/obras?lat=6.27&radius=500")
    assert response.status_code == 400
    assert "lat" in response.get_json()["error"].lower()

    response = app_client.get("/obras?lat=6.27&lon=-75.55&radius=-10")
    assert response.status_code == 400
    assert "radius" in response.get_json()["error"].lower()


def test_list_obras_combined_filters(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(2,)],
        fetchall_results=[
            [
                (
                    3,
                    "Obra Dos",
                    12,
                    "Autor 2",
                    2001,
                    "Escultura",
                    "Comuna 2",
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            ]
        ],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/obras?autor=andr&lat=6.24&lon=-75.57&radius=750")
    assert response.status_code == 200
    assert any("ST_DWithin" in sql for sql, _ in connection.queries)
    count_params = connection.queries[0][1]
    assert any(isinstance(param, str) and "%andr%" in param for param in count_params)


def test_list_obras_pagination_metadata(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(5,)],
        fetchall_results=[
            [
                (
                    3,
                    "Obra Dos",
                    12,
                    "Autor 2",
                    2001,
                    "Escultura",
                    "Comuna 2",
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
                (
                    4,
                    "Obra Tres",
                    12,
                    "Autor 2",
                    2002,
                    "Escultura",
                    "Comuna 3",
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            ]
        ],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/obras?limit=2&offset=2")
    assert response.status_code == 200
    meta = response.get_json()["meta"]
    assert meta["limit"] == 2
    assert meta["offset"] == 2
    assert meta["total"] == 5
    assert meta["total_pages"] == 3
    assert meta["page"] == 2
    assert meta["has_prev"] is True
    assert meta["prev_offset"] == 0
    assert meta["has_next"] is True
    assert meta["next_offset"] == 4


def test_list_obras_no_results(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(0,)],
        fetchall_results=[[]],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/obras")
    assert response.status_code == 200
    data = response.get_json()
    assert data["items"] == []
    assert data["meta"]["total"] == 0
    assert data["meta"]["total_pages"] == 1
    assert data["meta"]["count"] == 0
