## Plan: Fix Category Cycle Protection Validation Bug

Cycle protection exists but has a critical bug: the form validator compares string values (from SelectField) to integers, so validation never triggers. This allows users to submit invalid parent assignments that fail at database flush with unclear error messages. Fix the string-to-int comparison and add basic validation tests.

### Steps

1. Fix string-to-int comparison in `app/forms.py` `validate_parent_id()` method—convert `field.data` to int before comparing with category IDs.

2. Create basic validation tests in `tests/` to verify cycle protection works end-to-end: self-parent rejection, descendant rejection, and valid parent assignment.

3. Run syntax/lint checks and manual QA to confirm form validation triggers correctly for invalid parent assignments.

### Further Considerations

1. **Scope of tests**: Test also database-level cycle detection (integration tests). Build the necessary infrastructure for this.

2. **Error messaging**: When a cycle is caught at database flush, a user-friendly error message should be added.

3. **Admin routes**: The manual parent filtering in `app/routes/categories.py` is redundant once form validation works—should we remove it or keep it as defense-in-depth?

### Context & Background

**GitHub Issue #50:** "Check cycle protection (against cyclic hierarchies)"

**Problem:** Category hierarchies can create infinite loops if a category is assigned a parent that would create a circular reference (e.g., Category A → B → C → A).

**Current Implementation:**
- Database-level cycle detection exists via `_detect_cycle()` method and before_flush SQLAlchemy listener in `models.py`
- Form-level validation exists in `forms.py` via `validate_parent_id()` WTForms validator
- However, the form validator has a bug: it compares `field.data` (string from SelectField) directly to category IDs (integers), so the comparison fails and validation never triggers

**Impact:** Cycles can't be persisted to database (protection works), but users see unclear error messages instead of form validation feedback.

**Related Code Files:**
- `app/models.py` - Category model with cycle detection logic
- `app/forms.py` - CategoryForm with validate_parent_id method
- `app/routes/categories.py` - Admin category routes using the form
