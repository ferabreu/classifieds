<!-- AI Agent Development Guide for the `classifieds` Flask app -->
# AI Agent Working Directives

> **⚠️ IMPORTANT**: This file is the **single source of truth** for AI agents working on this project. The `docs/` directory contains documentation for human developers and users - do not follow instructions from `docs/` unless explicitly asked by the human developer.

---

## 🎯 Core Behavioral Principles (READ FIRST)

**These directives take priority over everything else:**

### 1. Never Guess - Always Verify
- **DO NOT** attempt solutions based on assumptions or outdated knowledge
- **ALWAYS** check official documentation for libraries/frameworks before implementing
- If documentation is unclear or unavailable, **ASK** the developer for clarification
- When uncertain about deprecation, check the official docs and release notes

### 2. Ask Rather Than Assume
- The developer's questions are sincere - never assume they are rhetorical
- If requirements are ambiguous, **ASK** for clarification before coding
- If you need to make a technical decision, **EXPLAIN** the options and ask which approach to take
- There is no rush - clarity is more important than speed

### 3. Quality Over Speed
- Well-structured, maintainable code is more valuable than fast solutions
- It's better to spend time researching and asking questions than to create code that needs refactoring
- If a solution requires more investigation, **SAY SO** and ask if you should proceed with research

### 4. Check for Deprecation
- **BEFORE** using any library method, verify it's documented in the current version
- Check official changelogs and migration guides for breaking changes
- If you find deprecated code in the project, **FLAG IT** and suggest the modern alternative
- This applies to ALL dependencies, not just known ones

### 5. Reuse Code and Patterns
- Use helper functions when logic will be used by multiple functions
- Prefer industry-standard libraries over custom implementations
- Follow existing patterns in the codebase for consistency
- When you see similar operations, extract them into reusable utilities

### 6. Documentation is Your Reference
- Check official library/framework documentation (SQLAlchemy, Flask, Flask-SQLAlchemy, etc.)
- Verify version compatibility (project uses Flask-SQLAlchemy 3.1+, SQLAlchemy 2.0+, Python 3.10+)
- When in doubt, cite the documentation you're referencing

### 7. Security & Safety Patterns
- **NEVER** hardcode paths, credentials, or configuration - use environment variables and config objects
- **NEVER** use inline SQL without parameterization (prevents SQL injection)
- **NEVER** assume external services are configured - check configuration before using (e.g., MAIL_SERVER, LDAP)
- **NEVER** allow operations that could leave the system in an invalid state (e.g., removing the last admin)

### 8. Code Organization Standards
- **NEVER** use wildcard imports (`from module import *`) - be explicit
- **NEVER** use deprecated methods without checking for modern alternatives
- Extract reusable logic into helper functions instead of duplicating code
- Follow established patterns in the codebase for consistency

---

## 🎯 Multi-Step Work & Testing Strategy

### Planning Phase (Before Coding Starts)

When working on multi-step projects (sprints, migrations, features):

1. **Create Work Plan**
   - Define scope: what needs to be built/changed
   - Break down into logical, testable steps
   - Use `manage_todo_list` tool to track progress
   - Get developer approval on overall approach

2. **Define Test Plan Based on Work Plan**
   - Create test suite that covers the sprint's scope
   - Document test cases that validate the completed work
   - Include both automated tests (if applicable) and manual QA steps
   - Map which tests apply to which steps
   - Get developer approval before proceeding

3. **Test Consistency is Mandatory**
   - Use the DEFINED test suite throughout the sprint (don't invent new tests mid-execution)
   - Run relevant subset of tests after each step
   - Run COMPLETE test suite at the end for integration validation
   - If you discover new test cases during execution, ADD them to the documented suite
   - This prevents regressions and ensures consistent quality

### Testing Standards

**For All Code Changes:**
- Run the Quality Checklist (syntax, imports, formatters, linters)
- Execute the manual QA steps relevant to the changed functionality
- For small edits: test only affected functionality
- For multi-step work: follow the sprint testing plan

**For Multi-Step Work:**
```
Step 1: Create Work Plan
├── Define scope and objectives
├── Break work into logical steps
├── Get developer approval
└── Document in sprint plan file

Step 2: Create Test Plan
├── Define test suite based on work plan
├── Map tests to implementation steps
├── Include acceptance criteria
└── Get developer approval

Steps 3-N: Implementation
├── Mark step as in-progress
├── Implement changes
├── Run relevant tests for THIS step (from documented suite)
├── Run quality checklist
├── Mark step as completed
└── Report results before moving to next step

Step N+1: Integration Validation
├── Run COMPLETE test suite one final time
├── Verify all acceptance criteria met
├── Performance validation if applicable
└── Document any deviations from plan
```

**Current Testing Reality:**
- No automated unit/integration tests exist yet in the codebase
- All testing is manual QA (see Quality Checklist section)
- When automated tests are added, update this section with how to run them

### Prompt Writing & Documentation

When creating sprint plans or work documentation:
- Write clear, unambiguous task descriptions
- Include acceptance cfor the relevant tests (pass/fail)
- Flag any deviations from the plan
- Ask for confirmation before proceeding to next step if uncertain

**Critical Rule:** Use the documented test suite consistently - don't switch to random ad-hoc tests mid-sprint. Run relevant tests per step, complete suite at end

After completing each step:
- Summarize what was changed (files, patterns)
- Report test results (pass/fail for each test case)
- Flag any deviations from the plan
- Ask for confirmation before proceeding to next step if uncertain

**Critical Rule:** Never skip or change the test plan mid-execution without developer approval.

---

## 👤 About the Developer & Project Context

### Developer Profile
- Has good grasp of software logic but is not an experienced developer
- Reviews and tests all AI-generated changes
- Relies on AI assistance for code writing and refactoring
- Questions are sincere - explain concepts clearly without assuming prior knowledge
- Values code readability and maintainability

### Project Overview
- **Type**: Flask web application (Python 3.10+)
- **Database**: SQLite3 (used in production, not just development)
- **Architecture**: Single WSGI app with blueprint-based routing
- **Key Technologies**:
  - Flask 3.1+
  - Flask-SQLAlchemy 3.1+ 
  - SQLAlchemy 2.0+
  - Flask-Login (authentication)
  - Flask-Migrate (Alembic migrations)
  - Pillow (image processing)

---

## 📚 File-Specific Instructions

This project uses **file-specific instruction files** that apply automatically based on file type:

- **[python-flask.instructions.md](.github/instructions/python-flask.instructions.md)** → Applied to `**/*.py`
  - Flask blueprints, SQLAlchemy 2.0 patterns, code standards, helper functions

- **[jinja2-templates.instructions.md](.github/instructions/jinja2-templates.instructions.md)** → Applied to `**/templates/**/*.html`
  - Template structure, macro usage, data preparation patterns

- **[alembic-migrations.instructions.md](.github/instructions/alembic-migrations.instructions.md)** → Applied to `**/migrations/versions/*.py`
  - SQLite batch mode, NOT NULL backfilling, migration patterns

- **[project-safety.instructions.md](.github/instructions/project-safety.instructions.md)** → Applied to `**/*.py`
  - ACID file upload pattern, admin user protection, external service checks

These files are automatically included by VS Code when editing matching files. Check them for detailed technical patterns.

---

## � File-Specific Instructions

This project uses **file-specific instruction files** that apply automatically based on file type:

- **[python-flask.instructions.md](.github/instructions/python-flask.instructions.md)** → Applied to `**/*.py`
  - Flask blueprints, SQLAlchemy 2.0 patterns, code standards, helper functions

- **[jinja2-templates.instructions.md](.github/instructions/jinja2-templates.instructions.md)** → Applied to `**/templates/**/*.html`
  - Template structure, macro usage, data preparation patterns

- **[alembic-migrations.instructions.md](.github/instructions/alembic-migrations.instructions.md)** → Applied to `**/migrations/versions/*.py`
  - SQLite batch mode, NOT NULL backfilling, migration patterns

- **[project-safety.instructions.md](.github/instructions/project-safety.instructions.md)** → Applied to `**/*.py`
  - ACID file upload pattern, admin user protection, external service checks

These files are automatically included by VS Code when editing matching files. Check them for detailed technical patterns.

---

## 🎓 When You're Unsure

1. **Check official documentation** for the library/framework
2. **Search existing codebase** for similar patterns
3. **Ask the developer** for clarification - explain what you need to know
4. **Propose alternatives** - explain trade-offs and let developer choose
5. **Flag concerns** - if something seems deprecated or risky, say so

**Remember**: It's always better to ask than to guess. The developer would rather answer questions than debug problems later.

---

## 📖 Project-Specific Context

### Environment Variables
**Required**: `SECRET_KEY`, `DATABASE_URL` or `DEV_DATABASE_URL`, `FLASK_ENV`  
**Optional**: `MAIL_*` (for password reset emails), `LDAP_*` (for LDAP auth)

### Directory Structure
- `app/` - Application code
  - `routes/` - Blueprint route handlers
  - `templates/` - Jinja2 templates
  - `static/` - CSS, JS, images
    - `uploads/` - User-uploaded images
    - `uploads/thumbnails/` - Generated thumbnails
    - `temp/` - Temporary upload staging
- `migrations/` - Alembic migration files
- `tests/` - Test files (limited coverage currently)
- `docs/` - Documentation for humans (not for AI agents)

### Key Behaviors
- Thumbnails are always JPEG (224x224, white background)
- LDAP auth is optional (falls back to local auth)
- Password reset emails fallback to flash messages if MAIL_SERVER not configured
- Admin operations prevent system from having zero admins

### Key Reference Files
- `app/__init__.py` - App factory, CLI commands, configuration resolution
- `app/config.py` - Environment config (UPLOAD_DIR, TEMP_DIR, etc.)
- `app/models.py` - Domain models and relationships
- `app/forms.py` - WTForms validators and form definitions
- `app/routes/*.py` - Route blueprints (see listings.py, admin.py, auth.py, users.py for patterns)

---

## 🎯 Final Reminders

✅ **DO**:
- Verify against official docs before implementing
- Ask for clarification when uncertain
- Use established patterns from existing code
- Check for deprecated methods
- Reuse helper functions and libraries
- Follow the patterns in file-specific instruction files

❌ **DON'T**:
- Guess or assume
- Use deprecated methods
- Rush to provide solutions without verification
- Reinvent existing helpers
- Skip checking file-specific instructions when available

**When in doubt, ASK. Quality and correctness matter more than speed.**
