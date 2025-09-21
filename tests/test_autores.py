import pytest
from flask import Flask

from app.web.routes.autores_routes import autores_bp


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


class ConnectionQueue:
    def __init__(self, connections):
        self._connections = list(connections)

    def __call__(self, *args, **kwargs):
        if not self._connections:
            raise RuntimeError("No hay más conexiones disponibles")
        return self._connections.pop(0)


@pytest.fixture
def app_client():
    app = Flask(__name__)
    app.register_blueprint(autores_bp)
    return app.test_client()


def test_list_autores_with_filters(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(4,)],
        fetchall_results=[
            [
                (1, "Ana", 3),
                (2, "Andrés", 2),
            ]
        ],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/autores?nombre=an&min_obras=2&limit=10")
    assert response.status_code == 200
    data = response.get_json()
    assert data["meta"]["total"] == 4
    assert data["meta"]["total_pages"] == 1
    assert data["meta"]["page"] == 1
    assert data["meta"]["count"] == 2
    assert data["filters"]["nombre"] == "an"
    assert connection.queries[0][0].lower().startswith("with agg as")
    assert connection.queries[1][1][-2] == 10  # limit in data query
    assert connection.queries[1][1][-1] == 0  # offset defaults to 0


def test_list_autores_limit_capped(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(0,)],
        fetchall_results=[[]],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/autores?limit=500&offset=15")
    assert response.status_code == 200
    data = response.get_json()
    assert data["meta"]["limit"] == 100
    assert data["meta"]["offset"] == 15
    assert data["meta"]["total_pages"] == 1
    assert connection.queries[1][1][-2] == 100
    assert connection.queries[1][1][-1] == 15


def test_list_autores_invalid_range_returns_400(app_client):
    response = app_client.get("/autores?min_obras=5&max_obras=2")
    assert response.status_code == 400
    data = response.get_json()
    assert "min_obras" in data["error"].lower()


def test_list_autores_no_results(monkeypatch, app_client):
    connection = MockConnection(
        fetchone_results=[(0,)],
        fetchall_results=[[]],
    )
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/autores")
    assert response.status_code == 200
    data = response.get_json()
    assert data["items"] == []
    assert data["meta"]["total"] == 0
    assert data["meta"]["total_pages"] == 1
    assert data["meta"]["count"] == 0


def test_autor_detail_success(monkeypatch, app_client):
    lookup_conn = MockConnection(fetchone_results=[(5, "Autor Detalle")])
    obras_conn = MockConnection(
        fetchone_results=[(2,)],
        fetchall_results=[
            [
                (
                    1,
                    "Obra Uno",
                    5,
                    "Autor Detalle",
                    2000,
                    "Escultura",
                    "Comuna 10",
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            ]
        ],
    )
    queue = ConnectionQueue([lookup_conn, obras_conn])
    monkeypatch.setattr("app.utils.database.psycopg2.connect", queue)

    response = app_client.get("/autores/5")
    assert response.status_code == 200
    data = response.get_json()
    assert data["autor"]["id"] == 5
    assert data["obras"]["meta"]["total"] == 2
    assert obras_conn.queries[1][1][-2] == 50  # default limit applied


def test_autor_detail_not_found(monkeypatch, app_client):
    connection = MockConnection(fetchone_results=[None])
    monkeypatch.setattr(
        "app.utils.database.psycopg2.connect",
        lambda *args, **kwargs: connection,
    )

    response = app_client.get("/autores/999")
    assert response.status_code == 404
    data = response.get_json()
    assert "no encontrado" in data["error"].lower()
