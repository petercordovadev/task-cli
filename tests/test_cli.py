"""Tests de la CLI: llaman a main() directamente, sin subprocess."""

import pytest

from main import main


def db_path(tmp_path):
    return str(tmp_path / "tasks.db")


def test_cli_add_and_list(tmp_path, capsys):
    db = db_path(tmp_path)

    assert main(["--db", db, "add", "Comprar pan"]) == 0
    assert "Tarea añadida: #1 Comprar pan" in capsys.readouterr().out

    assert main(["--db", db, "list"]) == 0
    assert "Comprar pan" in capsys.readouterr().out


def test_cli_data_survives_between_calls(tmp_path, capsys):
    db = db_path(tmp_path)

    main(["--db", db, "add", "Comprar pan"])
    capsys.readouterr()

    main(["--db", db, "list"])

    assert "Comprar pan" in capsys.readouterr().out


def test_cli_add_with_metadata_then_filter_by_tag(tmp_path, capsys):
    db = db_path(tmp_path)

    assert (
        main(
            [
                "--db",
                db,
                "add",
                "Comprar pan",
                "--priority",
                "high",
                "--tags",
                "casa,compras",
                "--due",
                "2026-11-01",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["--db", db, "list", "--tag", "casa"]) == 0
    assert "Comprar pan" in capsys.readouterr().out

    assert main(["--db", db, "list", "--tag", "trabajo"]) == 0
    assert "Ninguna tarea coincide" in capsys.readouterr().out


def test_cli_add_rejects_invalid_priority(tmp_path):
    db = db_path(tmp_path)

    # argparse corta antes de llegar al try de main(): SystemExit con código 2
    with pytest.raises(SystemExit) as excinfo:
        main(["--db", db, "add", "Comprar pan", "--priority", "urgent"])

    assert excinfo.value.code == 2


def test_cli_done_updates_task(tmp_path, capsys):
    db = db_path(tmp_path)
    main(["--db", db, "add", "Comprar pan"])
    capsys.readouterr()

    assert main(["--db", db, "done", "1"]) == 0
    assert "completada" in capsys.readouterr().out


def test_cli_edit_changes_title_and_priority(tmp_path, capsys):
    db = db_path(tmp_path)
    main(["--db", db, "add", "Comprar pan"])
    capsys.readouterr()

    assert (
        main(
            [
                "--db",
                db,
                "edit",
                "1",
                "--title",
                "Comprar pan integral",
                "--priority",
                "high",
            ]
        )
        == 0
    )
    output = capsys.readouterr().out

    assert "Comprar pan integral" in output
    assert "!high" in output


def test_cli_edit_without_changes_returns_exit_code_1(tmp_path, capsys):
    db = db_path(tmp_path)
    main(["--db", db, "add", "Comprar pan"])
    capsys.readouterr()

    assert main(["--db", db, "edit", "1"]) == 1
    assert "ningún cambio" in capsys.readouterr().err


def test_cli_list_pending_filters_done_tasks(tmp_path, capsys):
    db = db_path(tmp_path)
    main(["--db", db, "add", "Hecha"])
    main(["--db", db, "add", "Pendiente"])
    main(["--db", db, "done", "1"])
    capsys.readouterr()

    assert main(["--db", db, "list", "--pending"]) == 0
    output = capsys.readouterr().out

    assert "Pendiente" in output
    assert "Hecha" not in output


def test_cli_list_overdue_filters_future_tasks(tmp_path, capsys):
    db = db_path(tmp_path)
    main(["--db", db, "add", "Atrasada", "--due", "2020-01-01"])
    main(["--db", db, "add", "Futura", "--due", "2999-01-01"])
    capsys.readouterr()

    assert main(["--db", db, "list", "--overdue"]) == 0
    output = capsys.readouterr().out

    assert "Atrasada" in output
    assert "Futura" not in output


def test_cli_import_migrates_old_json(tmp_path, capsys):
    json_path = tmp_path / "tasks.json"
    json_path.write_text(
        '[{"id": 1, "title": "Vieja", "done": false, "created_at": "2026-10-19T07:11:16"}]',
        encoding="utf-8",
    )
    db = db_path(tmp_path)

    assert main(["--db", db, "import", str(json_path)]) == 0
    assert "1 tarea(s) importadas" in capsys.readouterr().out

    main(["--db", db, "list"])
    assert "Vieja" in capsys.readouterr().out


def test_cli_import_missing_file_returns_exit_code_1(tmp_path, capsys):
    db = db_path(tmp_path)

    assert main(["--db", db, "import", str(tmp_path / "no.json")]) == 1
    assert "No existe" in capsys.readouterr().err


def test_cli_database_in_missing_directory_returns_exit_code_1(tmp_path, capsys):
    db = str(tmp_path / "carpeta-que-no-existe" / "tasks.db")

    assert main(["--db", db, "add", "Comprar pan"]) == 1
    assert "No se pudo abrir la base" in capsys.readouterr().err


def test_cli_missing_task_returns_exit_code_1(tmp_path, capsys):
    db = db_path(tmp_path)

    assert main(["--db", db, "done", "99"]) == 1
    assert "No existe la tarea #99" in capsys.readouterr().err
