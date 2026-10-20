"""Tests de la lógica pura: sin terminal ni persistencia."""

from datetime import date, timedelta

import pytest

from tasks import (
    Task,
    add_task,
    complete_task,
    delete_task,
    edit_task,
    filter_tasks,
    find_task,
    format_task,
    is_overdue,
    normalize_tags,
    parse_due_date,
)

TODAY = date(2026, 10, 19)
TOMORROW = TODAY + timedelta(days=1)
YESTERDAY = TODAY - timedelta(days=1)


def test_add_task_assigns_incremental_ids():
    tasks = []

    first = add_task(tasks, "Comprar pan")
    second = add_task(tasks, "Estudiar Python")

    assert first.id == 1
    assert second.id == 2
    assert [task.title for task in tasks] == ["Comprar pan", "Estudiar Python"]


def test_add_task_strips_whitespace():
    task = add_task([], "  Comprar pan  ")

    assert task.title == "Comprar pan"


def test_add_task_rejects_empty_title():
    with pytest.raises(ValueError, match="vacío"):
        add_task([], "   ")


def test_add_task_stores_priority_tags_and_due():
    task = add_task(
        [],
        "Comprar pan",
        priority="high",
        tags=["Casa", "casa", "Compras"],
        due_date="2026-11-01",
    )

    assert task.priority == "high"
    assert task.tags == ["casa", "compras"]
    assert task.due_date == "2026-11-01"


def test_add_task_rejects_invalid_priority():
    with pytest.raises(ValueError, match="Prioridad inválida"):
        add_task([], "Comprar pan", priority="urgent")


def test_add_task_rejects_bad_due_date():
    with pytest.raises(ValueError, match="Fecha inválida"):
        add_task([], "Comprar pan", due_date="01/11/2026")


def test_normalize_tags_accepts_a_comma_separated_string():
    assert normalize_tags("Casa, compras ") == ["casa", "compras"]
    assert normalize_tags(None) == []


def test_parse_due_date_normalizes_and_rejects():
    assert parse_due_date(" 2026-11-01 ") == "2026-11-01"

    with pytest.raises(ValueError, match="Fecha inválida"):
        parse_due_date("2026/11/01")


def test_task_validates_due_date_on_construction():
    with pytest.raises(ValueError, match="Fecha inválida"):
        Task(id=1, title="Comprar pan", due_date="2026-13-01")


def test_complete_task_marks_done():
    tasks = [add_task([], "Comprar pan")]

    task = complete_task(tasks, 1)

    assert task.done is True


def test_find_missing_task_raises_lookup_error():
    with pytest.raises(LookupError, match="#99"):
        find_task([], 99)


def test_delete_task_removes_it():
    tasks = [add_task([], "Comprar pan")]

    removed = delete_task(tasks, 1)

    assert removed.title == "Comprar pan"
    assert tasks == []


def test_edit_task_updates_only_given_fields():
    tasks = [add_task([], "Comprar pan", tags=["casa"])]

    edited = edit_task(tasks, 1, title="Comprar pan integral", priority="high")

    assert edited.title == "Comprar pan integral"
    assert edited.priority == "high"
    assert edited.tags == ["casa"]


def test_edit_task_can_add_a_tag_and_clear_the_due_date():
    tasks = [add_task([], "Comprar pan", due_date="2026-11-01")]

    edited = edit_task(tasks, 1, add_tag="Urgente", clear_due=True)

    assert edited.tags == ["urgente"]
    assert edited.due_date is None


def test_edit_task_requires_at_least_one_change():
    tasks = [add_task([], "Comprar pan")]

    with pytest.raises(ValueError, match="ningún cambio"):
        edit_task(tasks, 1)


def test_edit_task_rejects_empty_title():
    tasks = [add_task([], "Comprar pan")]

    with pytest.raises(ValueError, match="vacío"):
        edit_task(tasks, 1, title="   ")


def test_is_overdue_only_for_pending_tasks_with_past_due():
    overdue = Task(id=1, title="Atrasada", due_date=YESTERDAY.isoformat())
    future = Task(id=2, title="Futura", due_date=TOMORROW.isoformat())
    finished = Task(id=3, title="Hecha", done=True, due_date=YESTERDAY.isoformat())
    undated = Task(id=4, title="Sin fecha")

    assert is_overdue(overdue, TODAY) is True
    assert is_overdue(future, TODAY) is False
    assert is_overdue(finished, TODAY) is False
    assert is_overdue(undated, TODAY) is False


def test_filter_tasks_combines_filters():
    tasks: list[Task] = []
    add_task(tasks, "Casa", tags=["casa"], due_date=YESTERDAY.isoformat())
    add_task(tasks, "Trabajo", tags=["trabajo"], priority="high")
    complete_task(tasks, 2)

    assert [t.title for t in filter_tasks(tasks, pending=True)] == ["Casa"]
    assert [t.title for t in filter_tasks(tasks, overdue=True, today=TODAY)] == ["Casa"]
    assert [t.title for t in filter_tasks(tasks, tag="CASA")] == ["Casa"]
    assert [t.title for t in filter_tasks(tasks, priority="high")] == ["Trabajo"]
    assert [t.title for t in filter_tasks(tasks, tag="casa", priority="high")] == []


def test_format_task_changes_mark_when_done():
    task = Task(
        id=7,
        title="Comprar pan",
        done=False,
        created_at="2026-10-19T07:11:16",
    )

    pending_line = format_task(task)
    task.done = True
    done_line = format_task(task)

    assert "7" in pending_line
    assert "Comprar pan" in pending_line
    assert "2026-10-19" in pending_line
    assert pending_line != done_line


def test_format_task_shows_priority_tags_and_overdue_due_date():
    task = Task(
        id=7,
        title="Comprar pan",
        priority="high",
        tags=["casa"],
        due_date=YESTERDAY.isoformat(),
    )

    line = format_task(task, TODAY)

    assert "!high" in line
    assert "#casa" in line
    assert "vencida" in line
