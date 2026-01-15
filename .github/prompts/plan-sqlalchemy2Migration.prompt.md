# Plan: Migrate to SQLAlchemy 2.0 select() API

Migrate the entire Flask application from the deprecated `.query` API to the modern SQLAlchemy 2.0 `select()` API. The codebase has 65 query usages across 12 files, with patterns ranging from simple lookups to complex joins with pagination. This migration is critical for future Flask-SQLAlchemy 3.1+ compatibility and improves type safety and maintainability.

## Steps

1. **Modernize dependency management and establish baseline** — Audit current dependencies across `requirements.txt`, `requirements-dev.txt`, and `pyproject.toml` to identify version conflicts and unpinned packages. Install **`uv`** via standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`) for system-wide access independent of Python/pip. Migrate fully to modern `pyproject.toml` (PEP 621) structure with `[project.dependencies]` for production deps and `[project.optional-dependencies]` groups for dev/test tools (pytest, ruff, mypy, flake8). Initialize uv project with `uv init` or manually configure `pyproject.toml`, then run `uv sync` to resolve dependencies and generate `uv.lock` for reproducible installs. Upgrade all dependencies to latest compatible versions (target: SQLAlchemy 2.0.35+, Flask-SQLAlchemy 3.1+, Flask 3.1+) using `uv add <package> --upgrade` or `uv lock --upgrade`. Set up **GitHub Dependabot** (`.github/dependabot.yml`) for automated weekly dependency update PRs with grouped updates for related packages (Flask ecosystem, testing tools, etc.). Configure `uv audit` in GitHub Actions workflow to scan for security vulnerabilities on every PR. Document current installed versions (`uv pip freeze > baseline-versions.txt`), create feature branch `feature/sqlalchemy-2-migration`, run performance benchmarks on critical queries (user login, listing pagination, category tree loading), and remove legacy `requirements*.txt` files after validating `uv sync` successfully recreates the environment.

2. **Create comprehensive test suite** — Write integration tests for all routes (`app/routes/auth.py`, `app/routes/users.py`, `app/routes/listings.py`, `app/routes/admin.py`), model class methods in `app/models.py`, and pagination/join patterns to ensure safe refactoring.

3. **Migrate low-risk files first** — Convert simple query patterns in `app/routes/errors.py` (3 queries), `app/cli/maintenance.py` (1 query), `app/forms.py` (1 query), and `scripts/test_reserved_names.py` (3 queries) using straightforward `db.session.execute(db.select(Model))` replacements.

4. **Refactor authentication and core utilities** — Migrate `app/routes/auth.py` (5 queries), `app/__init__.py` (critical user loader and context processor), and `app/routes/categories.py` (3 queries), paying special attention to `Category.get_children()` and `Category.from_path()` class methods that need session injection.

5. **Convert complex routes with joins and pagination** — Systematically migrate the following files, ensuring all queries use `select()` with proper joins, eager loading, and pagination handling:
   1. `app/routes/users.py` (complex subquery with aggregation).
   2. `app/routes/listings.py` (18 queries with eager loading).
   3. `app/routes/admin.py` (10 queries).

6. **Finalize and validate** — Migrate remaining `app/cli/demo.py` (6 demo queries).

7. Run full test suite, compare performance benchmarks.

8. Update `docs/development/sprint 04 - sqlalchemy-2-migration-and-extras/`:
   1. Update `s04-Summary.md` with reports on steps 4 and 5. Add additional relevant information on any steps as you see fit.
   2. Add migration guide and create rollback documentation.

## Further Considerations

1. **Model class methods pattern** — `Category.get_children()` and `Category.from_path()` in `app/models.py` currently use `cls.query` which is unavailable in SQLAlchemy 2.0. Should these become static methods accepting `db.session`, or should queries move to a repository pattern?

2. **Migration timeline** — Issue suggests gradual migration in future sprints. Should this be one comprehensive PR (4-6 weeks) or incremental PRs per file/phase (8+ weeks with smaller merge points)?

3. **Test coverage strategy** — No automated tests currently exist. Should tests be written for the entire application first (2-3 weeks prep), or can migration proceed with manual QA per the existing pattern, accepting higher risk?

4. **uv workflow transition** — Team members will need to adopt new commands: `uv sync` (instead of `pip install -r requirements.txt`), `uv add <package>` (instead of pip install + manual requirements.txt edit), `uv run <command>` (instead of activating venv). Should a migration guide or quick reference card be created for the team?

5. **Dependabot configuration scope** — Should Dependabot updates be grouped by ecosystem (all Flask packages together) or separated by update frequency (security patches immediately, feature updates weekly)? Should it also monitor GitHub Actions versions?
