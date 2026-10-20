# task-cli

Gestor de tareas de línea de comandos escrito en Python, con persistencia en
SQLite. Es mi primer proyecto en Python, hecho para aprender el lenguaje viniendo
de JavaScript.

## Características

- Tareas con prioridad (`low` / `normal` / `high`), etiquetas y fecha límite
- `list` con filtros combinables: `--pending`, `--overdue`, `--tag`, `--priority`
- `edit` para modificar solo los campos que indiques
- Persistencia en SQLite, con `import` para migrar un `tasks.json` viejo
- Colores en terminal (verde = completada, rojo = vencida) que se desactivan
  solos cuando la salida no es una terminal
- 43 tests con pytest, más ruff y mypy en modo estricto

## Requisitos

- Python 3.10 o superior (probado con 3.14)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Uso

```bash
python main.py add "Comprar pan" --priority high --tags casa,compras --due 2026-11-01
python main.py add "Estudiar Python" --tags estudio

python main.py list
python main.py list --pending
python main.py list --overdue
python main.py list --tag casa
python main.py list --priority high

python main.py edit 1 --title "Comprar pan integral" --add-tag urgente
python main.py edit 1 --no-due

python main.py done 1
python main.py delete 1
python main.py --help
```

Salida de ejemplo (en una terminal real, las completadas se ven en verde y las
vencidas en rojo):

```
$ python main.py list
[o] 1   Comprar pan (2026-10-19)  !high  (vencida 2026-10-01)  #casa #compras
[✓] 2   Estudiar Python (2026-10-19)  #estudio
```

Si instalaste con `-e ".[dev]"`, también tenés el comando `task`:

```bash
task list --pending
```

### Base de datos

Por defecto `tasks.db`, junto al código. Se puede usar otra con `--db`, siempre
**antes** del subcomando:

```bash
python main.py --db /tmp/otras.db add "Probar otra base"
```

Migración desde la versión anterior en JSON:

```bash
python main.py import tasks.json
```

## Tests y calidad

```bash
pytest                 # 43 tests
ruff check .           # lint
ruff format --check .  # formato
mypy .                 # tipos, en modo estricto
```

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `main.py` | CLI: parsea argumentos, imprime y decide el código de salida |
| `tasks.py` | Lógica pura: `Task`, añadir, editar, completar, eliminar, filtrar, formatear |
| `storage.py` | SQLite: esquema, cargar, guardar e importar desde JSON |
| `tests/` | 43 tests: lógica (`test_tasks.py`), persistencia (`test_storage.py`) y CLI (`test_cli.py`) |
| `pyproject.toml` | Empaquetado y configuración de pytest, ruff y mypy |
| `.github/workflows/ci.yml` | CI: lint, formato, tipos y tests en Python 3.10, 3.13 y 3.14 |

Regla de diseño: `tasks.py` no sabe nada de la terminal ni de SQLite, `storage.py`
no imprime nada, y `main.py` solo traduce entre el usuario y esas dos capas.

## Hoja de ruta

- [x] Hito 0: entorno virtual y `.gitignore`
- [x] Hito 1: script mínimo con `sys.argv`
- [x] Hito 2: `Task` y lógica en memoria
- [x] Hito 3: CLI con `argparse`
- [x] Hito 4: persistencia JSON
- [x] Hito 5: validación y códigos de salida
- [x] Hito 6: tests con pytest
- [x] Hito 7: extras (`--pending`, colores, `pyproject.toml`)
- [x] `edit`, prioridades, etiquetas y vencimientos
- [x] Migración de JSON a SQLite
- [x] ruff + mypy + workflow de CI

## Licencia

MIT. Ver [LICENSE](LICENSE).

