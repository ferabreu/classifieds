# CODE STYLE (short, actionable)

This file contains the canonical, human- and machine-friendly coding rules for the project.
Keep edits small and follow these rules when modifying code.

## Python
- Follow PEP 8. Use 4 spaces for indentation.
- Use Black for formatting (line length 88) and isort for import ordering.
- Prefer single quotes in Python source; let Black normalize quotes.
- Use descriptive names (snake_case for functions/variables, PascalCase for classes).
- Add type hints for public functions where useful.

Quick local format/lint:
- pip install black isort flake8 pre-commit
- black .
- isort .
- python -m pyflakes . || true

## Flask & DB patterns
- Blueprints: follow existing pattern and register in create_app().
- File uploads: always follow temp -> commit -> move sequence (see app/routes/* examples).
- Use current_app.config for paths and options (no hard-coded paths).
- Wrap db.session.commit() in try/except and rollback on exceptions.

## Jinja templates
- Keep templates dumb: prepare data in views.
- Put reusable macros under `templates/macros/`.
- Import macros at the start of the block where used:
  `{% import 'macros/file.html' as file_macros %}` and call `{{ file_macros.macro(...) }}`.
- Avoid heavy data transformations in templates; pass pre-sorted/structured data instead.

## HTML / JS / CSS
- Double quotes for HTML attributes.
- Place scripts in `{% block scripts %}` and keep inline JS minimal.
- Use let/const in scripts; avoid globals.

## Tooling (recommended)
- Install and enable pre-commit hooks (example `.pre-commit-config.yaml`):
  - black, isort, flake8
- CI: add a workflow to run black --check, isort --check-only, flake8.

## Why this exists
- Improve consistency across human and automated edits.
- Make automated editors (Copilot/CI) behave predictably.
