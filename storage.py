"""Persistencia en SQLite."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from tasks import Task

DEFAULT_DB = Path(__file__).with_name("tasks.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY,
    title      TEXT    NOT NULL,
    done       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL,
    priority   TEXT    NOT NULL DEFAULT 'normal',
    tags       TEXT    NOT NULL DEFAULT '',
    due_date   TEXT
);
"""


@contextmanager
def open_db(path: Path = DEFAULT_DB) -> Iterator[sqlite3.Connection]:
    """Abre la base, garantiza el esquema, hace commit y cierra al salir."""
    try:
        conn = sqlite3.connect(path)
    except sqlite3.Error as exc:
        raise ValueError(f"No se pudo abrir la base {path}: {exc}") from exc

    conn.row_factory = sqlite3.Row
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    except sqlite3.DatabaseError as exc:
        conn.rollback()
        raise ValueError(f"Error de base de datos en {path}: {exc}") from exc
    finally:
        conn.close()


def load_tasks(path: Path = DEFAULT_DB) -> list[Task]:
    with open_db(path) as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return [task_from_row(row) for row in rows]


def save_tasks(tasks: list[Task], path: Path = DEFAULT_DB) -> None:
    """Reemplaza el contenido de la tabla por la lista recibida.

    Simple y coherente con el resto del programa (se carga todo, se muta
    en memoria y se guarda todo). Un sistema con muchos registros usaría
    INSERT/UPDATE/DELETE puntuales dentro de una transacción.
    """
    with open_db(path) as conn:
        conn.execute("DELETE FROM tasks")
        conn.executemany(
            """
            INSERT INTO tasks (id, title, done, created_at, priority, tags, due_date)
            VALUES (:id, :title, :done, :created_at, :priority, :tags, :due_date)
            """,
            [row_from_task(task) for task in tasks],
        )


def import_json(json_path: Path, db_path: Path = DEFAULT_DB) -> int:
    """Migra un tasks.json viejo a la base. Devuelve cuántas tareas importó."""
    if not json_path.exists():
        raise ValueError(f"No existe el archivo {json_path}.")

    try:
        raw = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"El archivo {json_path} no contiene JSON válido.") from exc

    if not isinstance(raw, list):
        raise ValueError(f"El archivo {json_path} debe contener una lista de tareas.")

    tasks = [Task.from_dict(item) for item in raw]
    save_tasks(tasks, db_path)
    return len(tasks)


def row_from_task(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "done": int(task.done),
        "created_at": task.created_at,
        "priority": task.priority,
        "tags": ",".join(task.tags),
        "due_date": task.due_date,
    }


def task_from_row(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
        created_at=row["created_at"],
        priority=row["priority"],
        tags=[tag for tag in (row["tags"] or "").split(",") if tag],
        due_date=row["due_date"],
    )
