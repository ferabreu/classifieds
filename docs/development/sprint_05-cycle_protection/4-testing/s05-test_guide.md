# Sprint 05: Category Cycle Protection - Testing Guide

## Overview

This document provides comprehensive testing instructions for the category cycle protection implementation. The implementation includes form-level validation (fixing the string-to-int conversion bug) and automated tests covering form validation, database-level protection, and integration scenarios.

## Test Scope

The testing strategy validates three layers of cycle protection:

1. **Form-level validation** - Prevents invalid parent assignments before submission
2. **Database-level protection** - Last resort catch for cycles that bypass form validation
3. **Integration** - End-to-end verification that cycles are properly prevented in admin routes

---

## Automated Testing

### Prerequisites

- Python 3.10+ installed
- Virtual environment active (`uv sync` completed)
- All dependencies installed
- SQLite database available (test fixtures initialize it)

### Running Tests

**Run cycle protection test suite:**
```bash
uv run python -m pytest tests/test_category_cycle_protection.py -v
```

**Run specific test:**
```bash
uv run python -m pytest tests/test_category_cycle_protection.py::TestFormValidationStringToIntConversion::test_validate_parent_id_converts_string_to_int -v
```

**Run all tests (including other suites):**
```bash
uv run python -m pytest tests/ -v
```

**Check code quality:**
```bash
ruff check app/forms.py tests/test_category_cycle_protection.py
```

---

## Test Suite Breakdown

### Form Validation Tests

**Class:** `TestFormValidationStringToIntConversion`  
**File:** `tests/test_category_cycle_protection.py`  
**Purpose:** Verify the string-to-int conversion bug fix

**Test Cases:**

1. **test_validate_parent_id_converts_string_to_int**
   - Verifies SelectField string "5" is correctly converted to integer 5 before comparison
   - Confirms self-parent assignment is rejected with error message
   - Status: ✅ PASS

2. **test_validate_parent_id_handles_none_string**
   - Verifies "0" (no parent) is handled correctly
   - Confirms empty strings are accepted without errors
   - Status: ✅ PASS

3. **test_validate_parent_id_allows_valid_parent**
   - Confirms valid, unrelated categories can be assigned as parents
   - Verifies no ValidationError is raised for valid assignments
   - Status: ✅ PASS

### Database Protection Tests

**Class:** `TestDatabaseLevelCycleProtection`  
**File:** `tests/test_category_cycle_protection.py`  
**Purpose:** Verify database-level cycle detection listener works

**Test Cases:**

1. **test_database_prevents_self_parent_cycle**
   - Attempts to flush a category with itself as parent
   - Verifies flush fails and changes are rolled back
   - Confirms database integrity maintained
   - Status: ✅ PASS

### Integration Tests

**Class:** `TestIntegrationCycleProtection`  
**File:** `tests/test_category_cycle_protection.py`  
**Purpose:** Verify end-to-end cycle prevention in realistic scenarios

**Test Cases:**

1. **test_edit_category_with_valid_parent**
   - Performs valid parent reassignment on a category
   - Confirms commit succeeds and database consistency maintained
   - Status: ✅ PASS

---

## Verification Checklist

### ✅ Unit & Integration Tests

**Command:** `uv run python -m pytest tests/test_category_cycle_protection.py -v`

- [✓] All 5 cycle protection tests pass
- [✓] No syntax or import errors
- [✓] Test execution time < 2 seconds
- [✓] No deprecation warnings related to cycle protection

### ✅ Full Test Suite (Regression)

**Command:** `uv run python -m pytest tests/ -v`

- [✓] All 21 tests pass (includes cycle protection + existing tests)
- [✓] No regressions in existing functionality
- [✓] Total execution time < 5 seconds
- [✓] Test breakdown:
  - [✓] 2 admin routes tests
  - [✓] 2 auth tests
  - [✓] 5 cycle protection tests
  - [✓] 6 listings tests
  - [✓] 4 user routes tests
  - [✓] 2 syntax tests

### ✅ Code Quality

**Command:** `ruff check app/forms.py tests/test_category_cycle_protection.py`

- [✓] No linting errors in modified files
- [✓] Code style compliant with project standards
- [✓] All imports properly resolved

**Command:** `python -m py_compile app/forms.py tests/test_category_cycle_protection.py`

- [✓] Python syntax validation passes
- [✓] No parse errors in modified code

---

## Manual QA Testing

### Environment Setup

**Start the application:**
```bash
uv run python -m flask run
```

**Access admin interface:**
- URL: `http://localhost:5000/admin/categories`
- Login with admin credentials if required

### Manual Test Cases

**Important Note on Protection Layers:**

The route-level filtering in `app/routes/categories.py` (lines 68-72, 151-157) prevents invalid options from appearing in the dropdown at all:
- Self-category options never appear in the dropdown
- Descendant categories never appear as parent options

This means invalid parent selections are **not possible through the UI**. Scenarios that would attempt invalid cycles (self-parent, descendant-as-parent) are fully tested by unit tests but cannot be executed manually. The following test cases verify the actual UI workflows that are possible:

---

#### TC-01: Valid Parent Assignment

**Objective:** Confirm valid category parent assignment works

**Steps:**
1. Navigate to admin categories list
2. Click "Create Category"
3. Enter name: "TestCategory"
4. Select an existing category as parent
5. Submit form

**Expected Results:**
- [✓] Category created successfully
- [✓] Parent relationship established
- [✓] Hierarchy displays correctly
- [✓] No error messages

---

#### TC-02: Dropdown Filtering Verification

**Objective:** Confirm that invalid parent options are properly filtered from dropdown

**Steps:**
1. Navigate to admin categories list
2. Edit an existing parent category (one that has children)
3. Click on the "Parent Category" dropdown
4. Review the available options

**Expected Results:**
- [✓] Category itself is NOT in the list
- [✓] Descendant categories are NOT in the list
- [✓] Only valid ancestors/unrelated categories appear
- [✓] "- None -" option available to remove parent

---

#### TC-03: Parent Removal

**Objective:** Confirm removing parent assignment works

**Steps:**
1. Edit a category that has a parent
2. In Parent Category dropdown, select "- None -"
3. Submit form

**Expected Results:**
- [✓] Form submits successfully
- [✓] Parent assignment removed
- [✓] Category moves to root level
- [✓] Hierarchy updates correctly

---

#### TC-04: Valid Reparenting

**Objective:** Confirm moving category to different valid parent works

**Setup:** Hierarchy: `A`, `B → C`, `D`

**Steps:**
1. Edit category "C" (currently under "B")
2. In Parent dropdown, select "A"
3. Submit form

**Expected Results:**
- [✓] Form submits successfully
- [✓] Category "C" now appears under "A"
- [✓] Category "C" no longer under "B"
- [✓] Hierarchy correctly updated

---

#### TC-05: Hierarchy Consistency After Multiple Operations

**Objective:** Confirm hierarchy remains valid after multiple edit operations

**Steps:**
1. Create or edit several categories with various parent/child relationships
2. Perform multiple parent reassignments
3. Navigate through the hierarchy to verify structure
4. Check category counts and breadcrumb paths

**Expected Results:**
- [✓] All categories display in correct hierarchy
- [✓] No orphaned or broken relationships
- [✓] Breadcrumbs/paths display correctly
- [✓] Category listings show accurate parent/child counts

---

## Results Summary

### Test Execution Results

| Test Category | Count | Status | Notes |
|---|---|---|---|
| Form Validation | 3 | ✅ All Pass | String-to-int fix verified |
| Database Protection | 1 | ✅ Pass | Listener prevents cycles |
| Integration | 1 | ✅ Pass | Valid changes work |
| Full Test Suite | 21 | ✅ All Pass | Zero regressions |
| Code Quality | 2 | ✅ Pass | Ruff + syntax checks |

### Implementation Verification

- [✓] **Form Validation Bug Fixed**
  - Before: `"5" == 5` → False (validation skipped)
  - After: `int("5") == 5` → True (validation works)
  - File: `app/forms.py` lines 168-190

- [✓] **Tests Created**
  - 5 automated tests covering form, database, and integration layers
  - File: `tests/test_category_cycle_protection.py`

- [✓] **Defense-in-Depth Maintained**
  - Layer 1: Form validation (NOW WORKING)
  - Layer 2: Route-level filtering (existing)
  - Layer 3: Database listener (existing)

---

## Troubleshooting

### Test Fails with "DetachedInstanceError"

**Cause:** SQLAlchemy session scope issue  
**Solution:** Tests use `db.session.get()` to fetch fresh objects within app context

### Test Reports ValidationError Not Raised

**Cause:** Form validator context not properly set  
**Solution:** Manual tests set `form._obj` to ensure validator has access to category instance

### Manual QA Shows Database Error Instead of Form Error

**Cause:** Form validation bug (original issue)  
**Fix Verification:** Confirm `app/forms.py` line 177 contains: `parent_id = int(parent_id_str)`

### Dropdown Still Shows Invalid Options

**Cause:** Route-level filtering incomplete  
**Location:** Check `app/routes/categories.py` lines 68-72 and 151-155

---

## Regression Testing

When making future changes to category management, run these tests to ensure no regressions:

```bash
# Quick cycle protection validation
uv run python -m pytest tests/test_category_cycle_protection.py -v

# Full regression check
uv run python -m pytest tests/ -v

# Code quality check
ruff check app/forms.py app/routes/categories.py app/models.py
```

---

## Documentation References

- **Implementation Plan:** `.github/prompts/plan-cycleProtection.prompt.md`
- **Source Code:**
  - Form validation fix: `app/forms.py` (lines 168-190)
  - Model cycle detection: `app/models.py` (lines 146-165, 410-427)
  - Route filtering: `app/routes/categories.py` (lines 68-72, 151-157)
- **Test Suite:** `tests/test_category_cycle_protection.py`
- **GitHub Issue:** [#50 - Cycle Protection](https://github.com/ferabreu/classifieds/issues/50)
