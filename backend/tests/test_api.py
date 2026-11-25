from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from backend.main import HabitCheck, app, get_session


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    # No context manager: skip lifespan so habits.db is never created.
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_habits_empty(client: TestClient) -> None:
    response = client.get("/api/habits")
    assert response.status_code == 200
    assert response.json() == []


def test_create_habit(client: TestClient) -> None:
    response = client.post("/api/habits", json={"name": "Read"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Read"
    assert body["done_today"] is False
    assert isinstance(body["id"], int)
    assert "created_at" in body

    listed = client.get("/api/habits").json()
    assert [h["name"] for h in listed] == ["Read"]


@pytest.mark.parametrize("name", ["", "   "])
def test_create_habit_rejects_blank_name(client: TestClient, name: str) -> None:
    response = client.post("/api/habits", json={"name": name})
    assert response.status_code == 422


def test_create_habit_strips_name(client: TestClient) -> None:
    response = client.post("/api/habits", json={"name": "  Read  "})
    assert response.json()["name"] == "Read"


def test_check_habit_marks_today_done(client: TestClient) -> None:
    habit_id = client.post("/api/habits", json={"name": "Run"}).json()["id"]

    response = client.post(f"/api/habits/{habit_id}/check")
    assert response.status_code == 200
    assert response.json()["done_today"] is True

    listed = client.get("/api/habits").json()
    assert listed[0]["done_today"] is True


def test_check_habit_twice_is_idempotent(
    client: TestClient, session: Session
) -> None:
    habit_id = client.post("/api/habits", json={"name": "Run"}).json()["id"]

    client.post(f"/api/habits/{habit_id}/check")
    client.post(f"/api/habits/{habit_id}/check")

    checks = session.exec(
        select(HabitCheck).where(HabitCheck.habit_id == habit_id)
    ).all()
    assert len(checks) == 1


def test_check_unknown_habit_returns_404(client: TestClient) -> None:
    response = client.post("/api/habits/999/check")
    assert response.status_code == 404
