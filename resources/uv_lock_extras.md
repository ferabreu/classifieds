# uv.lock extras report

This file lists packages that appear in `uv.lock` but are not declared in `pyproject.toml`.

Columns:
- Package: package name from `uv.lock`
- Version: resolved version recorded in `uv.lock`
- Direct declared parents: declared packages (from `pyproject.toml` dependencies or groups) that depend directly on the package
- Transitive declared parents: declared packages that depend on the package via other dependencies

| Package | Version | Direct declared parents | Transitive declared parents |
|---|---:|---|---|
| alembic | 1.18.0 | flask-migrate | - |
| bcrypt | 5.0.0 | flask-bcrypt | - |
| blinker | 1.9.0 | flask, flask-mail | flask-bcrypt, flask-ldap3-login, flask-login, flask-migrate, flask-sqlalchemy, flask-wtf, pytest-flask |
| build | 1.4.0 | pip-tools | - |
| certifi | 2026.1.4 | requests | - |
| cfgv | 3.5.0 | pre-commit | - |
| charset-normalizer | 3.4.4 | requests | - |
| classifieds | 0.5.0 | - | - |
| click | 8.3.1 | black, flask, pip-tools | flask-bcrypt, flask-ldap3-login, flask-login, flask-mail, flask-migrate, flask-sqlalchemy, flask-wtf, pytest-flask |
| colorama | 0.4.6 | pytest | black, flask, flask-bcrypt, flask-ldap3-login, flask-login, flask-mail, flask-migrate, flask-sqlalchemy, flask-wtf, pip-tools, pytest-cov, pytest-flask |
| coverage | 7.13.1 | pytest-cov | - |
| distlib | 0.4.0 | - | pre-commit |
| dnspython | 2.8.0 | email-validator | - |
| exceptiongroup | 1.3.1 | pytest | pytest-cov, pytest-flask |
| filelock | 3.20.3 | - | pre-commit |
| greenlet | 3.3.0 | sqlalchemy | flask-migrate, flask-sqlalchemy |
| identify | 2.6.15 | pre-commit | - |
| idna | 3.11 | email-validator, requests | - |
| importlib-metadata | 8.7.1 | - | pip-tools |
| iniconfig | 2.3.0 | pytest | pytest-cov, pytest-flask |
| itsdangerous | 2.2.0 | flask, flask-wtf | flask-bcrypt, flask-ldap3-login, flask-login, flask-mail, flask-migrate, flask-sqlalchemy, pytest-flask |
| jinja2 | 3.1.6 | flask | flask-bcrypt, flask-ldap3-login, flask-login, flask-mail, flask-migrate, flask-sqlalchemy, flask-wtf, pytest-flask |
| ldap3 | 2.9.1 | flask-ldap3-login | - |
| librt | 0.7.7 | mypy | - |
| mako | 1.3.10 | - | flask-migrate |
| markupsafe | 3.0.3 | flask, wtforms | flask-bcrypt, flask-ldap3-login, flask-login, flask-mail, flask-migrate, flask-sqlalchemy, flask-wtf, pytest-flask |
| mypy-extensions | 1.1.0 | black, mypy | - |
| nodeenv | 1.10.0 | pre-commit | - |
| packaging | 25.0 | black, gunicorn, pytest | pip-tools, pytest-cov, pytest-flask |
| pathspec | 1.0.3 | black, mypy | - |
| pip | 25.3 | pip-tools | - |
| platformdirs | 4.5.1 | black | pre-commit |
| pluggy | 1.6.0 | pytest, pytest-cov | pytest-flask |
| pyasn1 | 0.6.1 | - | flask-ldap3-login |
| pygments | 2.19.2 | pytest | pytest-cov, pytest-flask |
| pyproject-hooks | 1.2.0 | pip-tools | - |
| pytokens | 0.3.0 | black | - |
| pyyaml | 6.0.3 | pre-commit | - |
| setuptools | 80.9.0 | pip-tools | - |
| text-unidecode | 1.3 | python-slugify | - |
| tomli | 2.4.0 | black, mypy, pip-tools, pytest | flask-migrate, pytest-cov, pytest-flask |
| typing-extensions | 4.15.0 | black, mypy, sqlalchemy | flask-migrate, flask-sqlalchemy, pre-commit, pytest, pytest-cov, pytest-flask |
| tzdata | 2025.3 | faker | - |
| urllib3 | 2.6.3 | requests | - |
| virtualenv | 20.36.1 | pre-commit | - |
| werkzeug | 3.1.5 | flask, flask-login, pytest-flask | flask-bcrypt, flask-ldap3-login, flask-mail, flask-migrate, flask-sqlalchemy, flask-wtf |
| wheel | 0.45.1 | pip-tools | - |
| zipp | 3.23.0 | - | pip-tools |

---

Notes:
- Many entries are transitive or dev/test tooling (e.g., `black`, `pre-commit` group pulls in `cfgv`, `pyyaml`, `virtualenv` etc.).
- If a package looks surprising as a top-level dependency, run `pipdeptree` in a venv created from this lock to inspect the dependency chain.
- Do not edit `uv.lock` by hand — update `pyproject.toml` and regenerate the lockfile with `uv lock`.
