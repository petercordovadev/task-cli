"""Tests de persistencia en SQLite, siempre contra una base temporal."""

import pytest

from storage import import_json, load_tasks, open_db, save_tasks
from tasks import Task


def test_load_from_empty_database_returns_empty_list(tmp_path):
    assert load_tasks(tmp_path / "tasks.db") == []


def test_open_db_creates_the_table(tmp_path):
    path = tmp_path / "tasks.db"

    with open_db(path) as conn:
        names = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master")}

    assert "tasks" in names


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "tasks.db"
    tasks = [
        Task(
            id=1,
            title="Comprar pan",
            done=True,
            created_at="2026-10-19T07:11:16",
            priority="high",
            tags=["casa", "compras"],
            due_date="2026-11-01",
        )
    ]

    save_tasks(tasks, path)

    assert load_tasks(path) == tasks


def test_save_replaces_previous_content(tmp_path):
    path = tmp_path / "tasks.db"
    save_tasks([Task(id=1, title="Vieja")], path)

    save_tasks([Task(id=1, title="Nueva")], path)

    assert [task.title for task in load_tasks(path)] == ["Nueva"]


def test_save_keeps_accents_and_tags(tmp_path):
    path = tmp_path / "tasks.db"

    save_tasks([Task(id=1, title="Programación", tags=["ñandú", "casa"])], path)

    task = load_tasks(path)[0]
    assert task.title == "Programación"
    assert task.tags == ["ñandú", "casa"]


def test_load_invalid_row_raises_value_error(tmp_path):
    path = tmp_path / "tasks.db"
    with open_db(path) as conn:
        conn.execute(
            """
            INSERT INTO tasks (id, title, done, created_at, priority, tags, due_date)
            VALUES (1, 'Rota', 0, '2026-10-19T00:00:00', 'urgent', '', NULL)
            """
        )

    with pytest.raises(ValueError, match="Prioridad inválida"):
        load_tasks(path)


def test_open_db_on_a_file_that_is_not_a_database_raises(tmp_path):
    path = tmp_path / "no-es-una-base.db"
    path.write_text("hola", encoding="utf-8")

    with pytest.raises(ValueError, match="Error de base de datos"):
        load_tasks(path)


def test_import_json_migrates_old_tasks(tmp_path):
    json_path = tmp_path / "tasks.json"
    json_path.write_text(
        '[{"id": 1, "title": "Vieja", "done": false, '
        '"created_at": "2026-10-19T07:11:16", "priority": "high", '
        '"tags": ["casa"], "due_date": null}]',
        encoding="utf-8",
    )
    db_path = tmp_path / "tasks.db"

    count = import_json(json_path, db_path)

    assert count == 1
    (imported,) = load_tasks(db_path)
    assert imported.title == "Vieja"
    assert imported.priority == "high"
    assert imported.tags == ["casa"]


def test_import_json_missing_file_raises(tmp_path):
    with pytest.raises(ValueError, match="No existe"):
        import_json(tmp_path / "no-existe.json", tmp_path / "tasks.db")


def test_import_json_corrupt_file_raises(tmp_path):
    json_path = tmp_path / "tasks.json"
    json_path.write_text("{no soy json", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON válido"):
        import_json(json_path, tmp_path / "tasks.db")
