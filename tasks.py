"""Lógica de tareas: sin prints, sin argparse y sin tocar la base de datos.

Mantener este módulo "puro" permite testearlo sin simular la terminal.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

PRIORITIES = ("low", "normal", "high")
DATE_FORMAT = "%Y-%m-%d"


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    priority: str = "normal"
    tags: list[str] = field(default_factory=list)
    due_date: str | None = None

    def __post_init__(self) -> None:
        """Valida y normaliza los campos derivados, sin importar cómo se creó."""
        if self.priority not in PRIORITIES:
            raise ValueError(
                f"Prioridad inválida: {self.priority!r}. Opciones: {', '.join(PRIORITIES)}."
            )
        self.tags = normalize_tags(self.tags)
        if self.due_date is not None:
            self.due_date = parse_due_date(self.due_date)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        try:
            raw_tags = data.get("tags") or []
            if isinstance(raw_tags, str):
                raw_tags = raw_tags.split(",")
            return cls(
                id=int(data["id"]),
                title=str(data["title"]),
                done=bool(data.get("done", False)),
                created_at=str(
                    data.get("created_at") or datetime.now().isoformat(timespec="seconds")
                ),
                priority=str(data.get("priority") or "normal").lower(),
                tags=raw_tags,
                due_date=data.get("due_date") or None,
            )
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"Tarea inválida: {data!r}") from exc


def normalize_tags(tags: Iterable[str] | str | None) -> list[str]:
    """Quita espacios, pasa a minúsculas y elimina repetidos conservando el orden.

    Acepta una lista o un string tipo "Casa, compras".
    """
    if tags is None:
        return []
    if isinstance(tags, str):
        tags = tags.split(",")

    cleaned: list[str] = []
    for tag in tags:
        value = str(tag).strip().lower()
        if value and value not in cleaned:
            cleaned.append(value)
    return cleaned


def parse_due_date(value: str) -> str:
    """Valida y normaliza una fecha a ISO (YYYY-MM-DD)."""
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date().isoformat()
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"Fecha inválida: {value!r}. Formato esperado: YYYY-MM-DD.") from exc


def add_task(
    tasks: list[Task],
    title: str,
    *,
    priority: str = "normal",
    tags: Iterable[str] | str | None = None,
    due_date: str | None = None,
) -> Task:
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("El título no puede estar vacío.")

    new_id = max((task.id for task in tasks), default=0) + 1
    task = Task(
        id=new_id,
        title=clean_title,
        priority=priority,
        tags=normalize_tags(tags),
        due_date=parse_due_date(due_date) if due_date else None,
    )
    tasks.append(task)
    return task


def find_task(tasks: list[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise LookupError(f"No existe la tarea #{task_id}.")


def complete_task(tasks: list[Task], task_id: int) -> Task:
    task = find_task(tasks, task_id)
    task.done = True
    return task


def delete_task(tasks: list[Task], task_id: int) -> Task:
    task = find_task(tasks, task_id)
    tasks.remove(task)
    return task


def edit_task(
    tasks: list[Task],
    task_id: int,
    *,
    title: str | None = None,
    priority: str | None = None,
    tags: str | None = None,
    add_tag: str | None = None,
    due_date: str | None = None,
    clear_due: bool = False,
) -> Task:
    """Modifica solo los campos indicados; el resto queda igual."""
    if (
        title is None
        and priority is None
        and tags is None
        and add_tag is None
        and due_date is None
        and not clear_due
    ):
        raise ValueError("No indicaste ningún cambio. Mirá: python main.py edit --help")

    task = find_task(tasks, task_id)

    if title is not None:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("El título no puede estar vacío.")
        task.title = clean_title

    if priority is not None:
        task.priority = Task(id=task.id, title=task.title, priority=priority).priority

    if tags is not None:
        task.tags = normalize_tags(tags)

    if add_tag is not None:
        task.tags = normalize_tags([*task.tags, add_tag])

    if clear_due:
        task.due_date = None

    if due_date is not None:
        task.due_date = parse_due_date(due_date)

    return task


def is_overdue(task: Task, today: date | None = None) -> bool:
    """Una tarea está vencida si tiene fecha pasada y sigue pendiente."""
    if task.done or task.due_date is None:
        return False
    reference = today or date.today()
    return date.fromisoformat(task.due_date) < reference


def filter_tasks(
    tasks: list[Task],
    *,
    pending: bool = False,
    overdue: bool = False,
    tag: str | None = None,
    priority: str | None = None,
    today: date | None = None,
) -> list[Task]:
    result = list(tasks)
    if pending:
        result = [task for task in result if not task.done]
    if overdue:
        result = [task for task in result if is_overdue(task, today)]
    if tag:
        wanted = tag.strip().lower()
        result = [task for task in result if wanted in task.tags]
    if priority:
        result = [task for task in result if task.priority == priority]
    return result


def format_task(task: Task, today: date | None = None) -> str:
    mark = "✓" if task.done else "o"
    line = f"[{mark}] {task.id:<3} {task.title} ({task.created_at[:10]})"
    if task.priority != "normal":
        line += f"  !{task.priority}"
    if task.due_date:
        label = "vencida" if is_overdue(task, today) else "vence"
        line += f"  ({label} {task.due_date})"
    if task.tags:
        line += "  " + " ".join(f"#{tag}" for tag in task.tags)
    return line
