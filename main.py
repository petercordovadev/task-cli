"""Punto de entrada de task-cli: interpreta argumentos y muestra resultados."""

import argparse
import sys
from pathlib import Path

from storage import DEFAULT_DB, import_json, load_tasks, save_tasks
from tasks import (
    PRIORITIES,
    Task,
    add_task,
    complete_task,
    delete_task,
    edit_task,
    filter_tasks,
    format_task,
    is_overdue,
)


def colorize(text: str, code: str) -> str:
    """Aplica color ANSI solo si la salida va a una terminal real."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def print_tasks(tasks: list[Task]) -> None:
    for task in tasks:
        line = format_task(task)
        if task.done:
            print(colorize(line, "32"))  # verde
        elif is_overdue(task):
            print(colorize(line, "31"))  # rojo
        else:
            print(line)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task-cli",
        description="Gestor de tareas simple, con persistencia en SQLite.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        metavar="RUTA",
        help="Base SQLite donde guardar las tareas (por defecto: tasks.db).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMANDO")

    add_parser = subparsers.add_parser("add", help="Añade una tarea")
    add_parser.add_argument("title", help="Título de la tarea")
    add_parser.add_argument("--priority", choices=PRIORITIES, default="normal", help="Prioridad")
    add_parser.add_argument("--tags", help="Etiquetas separadas por coma: casa,compras")
    add_parser.add_argument("--due", metavar="YYYY-MM-DD", help="Fecha límite")

    list_parser = subparsers.add_parser("list", help="Lista las tareas")
    list_parser.add_argument("--pending", action="store_true", help="Solo las pendientes")
    list_parser.add_argument("--overdue", action="store_true", help="Solo las vencidas")
    list_parser.add_argument("--tag", help="Solo las que tengan esa etiqueta")
    list_parser.add_argument("--priority", choices=PRIORITIES, help="Solo esa prioridad")

    edit_parser = subparsers.add_parser("edit", help="Modifica una tarea existente")
    edit_parser.add_argument("id", type=int, help="ID de la tarea")
    edit_parser.add_argument("--title", help="Nuevo título")
    edit_parser.add_argument("--priority", choices=PRIORITIES, help="Nueva prioridad")
    edit_parser.add_argument("--tags", help="Reemplaza las etiquetas: casa,compras")
    edit_parser.add_argument("--add-tag", dest="add_tag", help="Agrega una etiqueta")
    edit_parser.add_argument("--due", metavar="YYYY-MM-DD", help="Nueva fecha límite")
    edit_parser.add_argument(
        "--no-due", dest="no_due", action="store_true", help="Quita la fecha límite"
    )

    done_parser = subparsers.add_parser("done", help="Marca una tarea como completada")
    done_parser.add_argument("id", type=int, help="ID de la tarea")

    delete_parser = subparsers.add_parser("delete", help="Elimina una tarea")
    delete_parser.add_argument("id", type=int, help="ID de la tarea")

    import_parser = subparsers.add_parser("import", help="Importa tareas desde un tasks.json viejo")
    import_parser.add_argument(
        "json_path", type=Path, metavar="TASKS_JSON", help="Archivo JSON de origen"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "import":
            count = import_json(args.json_path, args.db)
            print(f"{count} tarea(s) importadas en {args.db}.")
            return 0

        tasks = load_tasks(args.db)

        if args.command == "add":
            task = add_task(
                tasks,
                args.title,
                priority=args.priority,
                tags=args.tags,
                due_date=args.due,
            )
            save_tasks(tasks, args.db)
            print(f"Tarea añadida: #{task.id} {task.title}")

        elif args.command == "list":
            visible = filter_tasks(
                tasks,
                pending=args.pending,
                overdue=args.overdue,
                tag=args.tag,
                priority=args.priority,
            )
            if not tasks:
                print('No hay tareas todavía. Añadí una con: python main.py add "Comprar pan"')
            elif not visible:
                print("Ninguna tarea coincide con esos filtros.")
            else:
                print_tasks(visible)

        elif args.command == "edit":
            task = edit_task(
                tasks,
                args.id,
                title=args.title,
                priority=args.priority,
                tags=args.tags,
                add_tag=args.add_tag,
                due_date=args.due,
                clear_due=args.no_due,
            )
            save_tasks(tasks, args.db)
            print(f"Tarea #{task.id} actualizada: {format_task(task)}")

        elif args.command == "done":
            task = complete_task(tasks, args.id)
            save_tasks(tasks, args.db)
            print(f"Tarea #{task.id} completada.")

        elif args.command == "delete":
            task = delete_task(tasks, args.id)
            save_tasks(tasks, args.db)
            print(f"Tarea #{task.id} eliminada: {task.title}")

    except (ValueError, LookupError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
