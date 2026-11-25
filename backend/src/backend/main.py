from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HabitCheck(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key="habit.id", index=True)
    date: date


class HabitCreate(SQLModel):
    name: str = Field(min_length=1)


class HabitRead(SQLModel):
    id: int
    name: str
    created_at: datetime
    done_today: bool


engine = create_engine(
    "sqlite:///habits.db", connect_args={"check_same_thread": False}
)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    SQLModel.metadata.create_all(engine)
    yield


def _to_read(habit: Habit, done_today: bool) -> HabitRead:
    assert habit.id is not None
    return HabitRead(
        id=habit.id,
        name=habit.name,
        created_at=habit.created_at,
        done_today=done_today,
    )


def _done_today_ids(session: Session) -> set[int]:
    today = date.today()
    return set(
        session.exec(select(HabitCheck.habit_id).where(HabitCheck.date == today))
    )


router = APIRouter(prefix="/api")


@router.get("/habits")
def list_habits(session: SessionDep) -> list[HabitRead]:
    done = _done_today_ids(session)
    habits = session.exec(select(Habit).order_by(Habit.id)).all()
    return [_to_read(h, h.id in done) for h in habits]


@router.post("/habits", status_code=201)
def create_habit(data: HabitCreate, session: SessionDep) -> HabitRead:
    habit = Habit(name=data.name)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return _to_read(habit, False)


@router.post("/habits/{habit_id}/check")
def check_habit(habit_id: int, session: SessionDep) -> HabitRead:
    habit = session.get(Habit, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    today = date.today()
    existing = session.exec(
        select(HabitCheck).where(
            HabitCheck.habit_id == habit_id, HabitCheck.date == today
        )
    ).first()
    if existing is None:
        session.add(HabitCheck(habit_id=habit_id, date=today))
        session.commit()
    return _to_read(habit, True)


app = FastAPI(title="Habit Tracker", lifespan=lifespan)
app.include_router(router)
