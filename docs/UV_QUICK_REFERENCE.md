# uv Quick Reference Guide

This project now uses **uv** for modern Python dependency management. Here's what you need to know:

## Installation

If you don't have uv installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Common Commands

### Initial Setup
```bash
# Clone the repo and sync dependencies
git clone <repo-url>
cd classifieds
uv sync
```

### Running Commands
```bash
# Run any Python command in the project environment
uv run python script.py
uv run flask run
uv run pytest

# Run Flask development server
uv run flask run

# Run CLI commands
uv run flask init
uv run flask backfill-thumbnails
```

### Managing Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev pytest

# Remove a dependency
uv remove package-name

# Upgrade all dependencies
uv lock --upgrade

# Upgrade specific package
uv add package-name --upgrade

# Sync environment with lock file (after pulling changes)
uv sync
```

### Security & Maintenance

```bash
# Check for security vulnerabilities
uv pip list --format=freeze | uv tool run safety check --stdin

# List installed packages
uv pip list

# Show dependency tree
uv pip tree
```

## Migration from pip/requirements.txt

| Old Command | New Command |
|-------------|-------------|
| `pip install -r requirements.txt` | `uv sync` |
| `source .venv/bin/activate` | *(not needed, use `uv run`)* |
| `pip install package` | `uv add package` |
| `pip uninstall package` | `uv remove package` |
| `pip freeze > requirements.txt` | *(handled by uv.lock automatically)* |
| `python script.py` | `uv run python script.py` |

## Key Benefits

- **Fast**: 10-100x faster than pip
- **Reproducible**: `uv.lock` ensures everyone has identical environments
- **Modern**: Uses `pyproject.toml` (PEP 621) standard
- **No virtualenv management**: uv handles it automatically
- **Automatic updates**: Dependabot keeps dependencies current

## Project Structure

- `pyproject.toml` - Project metadata and dependency specifications
- `uv.lock` - Locked dependency versions (committed to git)
- `.legacy-requirements/` - Old requirements.txt files (backup only)

## Troubleshooting

**"command not found: uv"**
- Add `~/.local/bin` to your PATH or reinstall uv

**"Failed to resolve dependencies"**
- Check for conflicting version constraints in pyproject.toml
- Try `uv lock --upgrade` to resolve with newer versions

**"ImportError after sync"**
- Make sure to use `uv run` prefix for all Python commands
- Or activate the environment: `source .venv/bin/activate`

## Learn More

- [uv documentation](https://docs.astral.sh/uv/)
- [pyproject.toml specification](https://peps.python.org/pep-0621/)


## 🚀 Common Operations Quick Reference

### Start Development Server
```bash
uv run flask run
```

### Initialize Database
```bash
uv run flask init
```

### Create Migration
```bash
uv run flask db migrate -m "description"
uv run flask db upgrade
```

### Run Pre-commit Hooks
```bash
uv run pre-commit install       # First time setup
uv run pre-commit run --all-files
```

### Quality Checklist (Run Before Committing)
```bash
# Syntax & Import Check
python -m pyflakes app migrations scripts wsgi.py
python -c "import importlib; importlib.import_module('app')"

# Formatter & Linter
uv run black app/
uv run isort app/
uv run ruff check app/
```

---