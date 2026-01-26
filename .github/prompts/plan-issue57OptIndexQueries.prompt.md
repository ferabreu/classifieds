# Optimize Showcase Queries (Issue #57)

**Date:** 2026-01-25 (Updated: 2026-01-26)  
**Author:** GitHub Copilot (Claude Sonnet 4.5) 
**Issue:** https://github.com/ferabreu/classifieds/issues/57  
**Goal:** Reduce showcase queries from 7-13+ queries to ≤2 queries per route

---

## Agent Role

You are an experienced developer versed in software development best practices with excellent knowledge of the Pythonic Way. You will optimize database query performance by refactoring an N+1 query pattern into efficient batch operations while maintaining identical user-facing behavior.

---

## Problem Analysis

### Current State

**Two routes use the same N+1 query pattern:**

1. **Index route (`/`)** - lines 60-115 in `app/routes/listings.py`
   - Displays showcases for top-level categories
   
2. **Category page route (`/<path:category_path>`)** - lines 185-265 in `app/routes/listings.py`
   - Displays showcases for child categories when viewing intermediate categories (e.g., `/goods/musical-instruments`)
   - Also fetches "Other {category}" listings for the parent category itself

Both routes use an N+1 query pattern:

Both routes use an N+1 query pattern:

**Query breakdown example (6 showcase categories):**
- **Per showcase category (N categories):**
  - **Query 1+N:** Fetch direct listings: `select(Listing).where(Listing.category_id == category.id)...` (1 query per category)
  - **Query 2+N:** Conditionally fetch descendant listings if needed: `select(Listing).where(Listing.category_id.in_(descendant_ids))...` (1 query per category with insufficient direct listings)

**Total queries per route:**
- Best case: **6 queries** (all categories have enough direct listings)
- Worst case: **12 queries** (all categories need descendant fallback)
- Category page adds **1 more query** for "Other {category}" listings: **7-13 total**

**Code duplication:** The showcase-building logic is duplicated between both routes (lines 70-114 and lines 202-242), making the codebase harder to maintain.

### Root Cause

1. **Loop-based querying** instead of batch operations - each category triggers separate database queries
2. **Code duplication** - identical logic exists in two places, violating DRY principle

### Impact

- Performance degradation on both index and category pages
- Scales poorly as number of showcases increases
- Unnecessary database round-trips
- Maintenance burden from duplicated code

---

## Work Plan

Use the `manage_todo_list` tool to track progress through these phases. Mark tasks as in-progress when starting, completed immediately after finishing.

### Phase 0: Restructure Listings Blueprint as Package

**Goal:** Convert single-file `app/routes/listings.py` into a package structure for better organization.

**Target structure:**
```
app/routes/listings/
  __init__.py      # Blueprint registration + route imports
  routes.py        # All route handlers (@listings_bp.route decorators)
  helpers.py       # All helper functions
```

1. **Create directory and files**
   - Create `app/routes/listings/` directory
   - Create `__init__.py` with blueprint registration
   - Create `routes.py` for route handlers
   - Create `helpers.py` for helper functions

2. **Move route handlers to `routes.py`**
   - Move all `@listings_bp.route(...)` decorated functions
   - Keep imports and route logic together
   - Import blueprint from `__init__.py`

3. **Move helpers to `helpers.py`**
   - Move `_delete_listings_impl()`, `_delete_listing_impl()`, `_edit_listing_impl()`
   - Move `get_index_showcase_categories()` from `app/routes/utils.py` (renamed from `get_index_carousel_categories()`)
   - Add all necessary imports (models, db, SQLAlchemy constructs)

4. **Update `__init__.py`**
   - Create blueprint: `listings_bp = Blueprint("listings", __name__)`
   - Import routes to register them: `from . import routes  # noqa: F401, E402`
   - Export blueprint for app registration

5. **Update import statements**
   - `app/__init__.py`: No change needed (still `from .routes.listings import listings_bp`)
   - `app/routes/users.py`: Change to `from .listings.helpers import _delete_listings_impl`

6. **Delete old file**
   - Remove `app/routes/listings.py` after verifying all code is migrated

7. **Run tests to verify**
   - Execute test suite to ensure no regressions
   - Verify all routes still accessible
   - Check that helper imports work correctly

**Acceptance criteria for Phase 0:**
- Blueprint package structure created
- All routes functional (no 404s or import errors)
- Helper function imports working in `users.py`
- All existing tests pass
- Old `listings.py` removed

### Phase 1: Create Reusable Helper Function

**Target file:** `app/routes/listings/helpers.py`

1. **Create `build_category_showcases()` helper function**
   - Input: list of categories, display_slots, fetch_limit
   - Output: list of dicts with `{"category": Category, "listings": [Listing, ...]}`
   - Extract the common showcase-building logic into a single reusable function

2. **Implement batch direct listings fetch**
   - Extract all category IDs into a list
   - Use single query: `filter(Listing.category_id.in_(category_ids))`
   - Order by `created_at.desc()` 
   - Fetch all direct listings in one query

3. **Implement Python-side grouping**
   - Use `collections.defaultdict(list)` to group listings by `category_id`
   - Iterate through fetched listings and populate the dictionary

4. **Implement batch descendant listings fetch**
   - Identify which categories need descendant fallback (insufficient direct listings)
   - Collect all descendant IDs for those categories
   - Execute single conditional batch query if any categories need descendants
   - Merge descendant listings into the grouped dictionary

5. **Preserve per-category randomization**
   - For each category's listing pool, apply `random.shuffle()` in Python
   - Select first N items after shuffling
   - Maintain existing display_slots logic

6. **Add comprehensive docstring**
   - Document the function's purpose, parameters, return value
   - Note that maximum 2 queries are executed (direct + optional descendants)

**Acceptance criteria for Phase 1:**
- Helper function created in `app/routes/listings/helpers.py`
- Maximum 2 queries executed per function call (direct + optional descendants)
- Returns identical data structure to existing code
- Comprehensive docstring included

### Phase 2: Refactor Both Routes to Use Helper

**Target file:** `app/routes/listings/routes.py`

7. **Refactor index route (`/`)**
   - Import `build_category_showcases` from `.helpers`
   - Replace loop-based showcase building with helper function call
   - Remove redundant `db.session.execute(select(Category)).first()` check
   - Use `len(showcase_categories) > 0` instead
   - Verify template receives identical data structure

8. **Refactor category_filtered_listings route (`/<path:category_path>`)**
   - Import `build_category_showcases` from `.helpers`
   - Replace child showcase loop with helper function call
   - Keep "Other {category}" direct listings fetch separate (it's a single query, not N+1)
   - Verify template receives identical data structure

9. **Verify identical behavior**
   - Ensure showcase data structure passed to templates is unchanged
   - No template modifications required
   - User-facing behavior must be identical

**Acceptance criteria for Phase 2:**
- Both routes refactored to use helper function
- Code duplication eliminated
- Existing functionality preserved
- No template changes needed

### Phase 3: Update Utils File

**Target file:** `app/routes/utils.py`

10. **Remove `get_index_showcase_categories()` from utils.py**
    - Function has been moved to `app/routes/listings/helpers.py` (and renamed from `get_index_carousel_categories()`)
    - Remove function definition and any related imports (if now unused)
    - Verify no other files import this function from utils

**Acceptance criteria for Phase 3:**
- `get_index_showcase_categories()` removed from utils.py
- No orphaned imports remain
- Utils file contains only generic utilities (thumbnails, file operations)

### Phase 4: Write and Run Automated Tests

**Target files:** `tests/conftest.py`, `tests/test_listings.py`

11. **Create showcase test fixtures in `conftest.py`**
   - Fixture: `showcase_categories` - Creates 3-6 categories with varied characteristics
   - Fixture: `showcase_listings` - Creates listings distributed across categories
   - Fixture: `category_with_children` - Parent category with child categories for descendant fallback testing
   - Keep fixtures minimal (focus on correctness, not scale)

12. **Write query count verification test for index route**
   - Enable query tracking in test: `app.config['TESTING'] = True`
   - Use `flask_sqlalchemy.get_debug_queries()` to capture queries
   - Request index page route
   - Assert query count ≤ 2 for showcase data (excluding unrelated queries like session checks)

13. **Write query count verification test for category page route**
   - Similar to above, but test `/<path:category_path>` with intermediate category
   - Assert query count ≤ 3 (2 for child showcases + 1 for "Other" listings)

14. **Write functional correctness tests**
   - Test showcase data structure matches expected format
   - Test randomization produces varied results
   - Test descendant fallback works when direct listings are insufficient
   - Test "Other {category}" listings appear correctly

**Acceptance criteria for Phase 4:**
- Query count tests pass with ≤2 queries for index, ≤3 for category pages
- Functional tests verify correct behavior
- Tests are maintainable and well-documented

### Phase 5: Documentation and Verification

15. **Run all tests to verify no regressions.**
   - Execute full test suite
   - Ensure all tests pass without modification
   - Verify no deprecated methods or anti-patterns introduced

16. **Update code comments**
   - Document the batch query optimization in helper function
   - Add inline comments explaining the grouping/shuffling logic

17. **Manual QA verification**
   - Load index page and verify showcases display correctly
   - Navigate to intermediate category pages (e.g., `/goods/musical-instruments`)
   - Verify child showcases display correctly
   - Verify "Other {category}" section appears when appropriate
   - Test with empty categories, categories with few listings, etc.

**Acceptance criteria for Phase 5:**
- All tests pass without modification
- Code comments and documentation updated
- Manual QA confirms correct behavior
- Code is well-documented

---

## Future Considerations (Out of Scope)

### Routing Structure Simplification

**Observation:** The current routing structure has conceptual overlap:
- `/` - shows root-level showcases
- `/<path:category_path>` - shows child showcases OR listings depending on category type

**Potential improvement:** Consider unifying these routes in a future refactor:
- A single route could handle both cases by treating "/" as "root level browsing"
- This would simplify the codebase and make the URL structure more consistent

**Why not now:**
- Routing changes are architectural and carry higher risk
- Issue #57 is specifically about query optimization, not routing refactor
- URL pattern changes could affect SEO and existing bookmarks
- Should be planned as a separate issue/sprint with dedicated testing

**Recommendation:** Create a separate GitHub issue to track routing structure improvements after this optimization is complete and stable.

---

## Implementation Requirements

### Helper Function Specification

**Function signature:**
```python
def build_category_showcases(
    categories: list[Category],
    display_slots: int,
    fetch_limit: int
) -> list[dict[str, Any]]:
    """
    Build showcase data for multiple categories using batch queries.
    
    Fetches listings for all categories in maximum 2 database queries:
    1. Direct listings for all categories (batch query)
    2. Descendant listings for categories needing fallback (conditional batch query)
    
    Args:
        categories: List of Category objects to build showcases for
        display_slots: Number of listings to display per showcase
        fetch_limit: Number of listings to fetch per category (for variety before randomization)
    
    Returns:
        List of dicts with structure: {"category": Category, "listings": [Listing, ...]}
        Listings are randomized per category and limited to display_slots.
    """
```

### Batch Query Strategy

**Direct listings query:**
```python
Use: filter(Listing.category_id.in_(showcase_category_ids))
Order: by created_at.desc()
Result: Single query fetching all direct listings for all showcase categories
```

**Descendant listings (conditional):**
```
Logic: Identify categories with insufficient direct listings
Collect: All descendant IDs for those categories
Use: filter(Listing.category_id.in_(all_descendant_ids)) if descendant_ids is not empty
Result: Single query fetching all needed descendant listings, or zero queries if not needed
```

### Python-Side Grouping

**Data structure:**
```
Use: collections.defaultdict(list)
Key: category.id (integer)
Value: List of Listing objects
Population: Iterate through fetched listings, append to listings_by_category[listing.category_id]
```

### Randomization Preservation

**Per-category operation:**
```
For each category:
  1. Get listings pool: listings_by_category[category.id]
  2. Shuffle in-place: random.shuffle(listings_pool)
  3. Select top N: listings_pool[:display_slots]
Result: Each category maintains independent randomization
```

### Behavioral Requirements

- User-facing behavior: MUST be identical to current implementation
- Template compatibility: NO template changes required
- Data structure: `category_showcases` list with embedded `showcase_listings` must match current format (note: variable name will change from `category_carousels` to `category_showcases`)
- Edge cases: Handle empty categories, categories with only descendants, single-listing categories

---

## Test Specifications

### Test Configuration

**Enable query debugging:**
```
In test setup: app.config['TESTING'] = True
Import: from flask_sqlalchemy import get_debug_queries
Usage: queries = get_debug_queries()
Assertion: len([q for q in queries if 'listing' in q.statement.lower()]) <= 2
```

### Minimal Fixtures

**showcase_categories fixture:**
- Create 3-6 categories with varied characteristics
- At least one category with child categories
- At least one category with no direct listings (for descendant fallback test)

**showcase_listings fixture:**
- Create 10-30 total listings distributed across categories
- Some categories with many listings (10+)
- Some categories with few listings (1-2)
- Some categories with zero listings

**category_with_children fixture:**
- Parent category (no direct listings)
- 2-3 child categories with listings
- Used to test descendant fallback

### Test Cases

**Query count test:**
- Setup: showcase_categories and showcase_listings fixtures
- Action: GET request to index route
- Capture: get_debug_queries()
- Assert: ≤2 queries for listing data (exclude category/user queries)

**Functional correctness tests:**
- Test: Each showcase displays listings from correct category
- Test: Listing count per showcase respects display_slots limit
- Test: Response status is 200
- Test: Showcase data structure matches expected format

**Randomization test:**
- Setup: Category with 10+ listings
- Action: Multiple GET requests to index (3-5 requests)
- Capture: Order of listings per request
- Assert: At least one request shows different order than others

**Descendant fallback test:**
- Setup: category_with_children fixture (parent has no listings, children have listings)
- Action: GET request to index route
- Assert: Parent category's showcase shows child category listings
- Assert: Query count still ≤2

**Regression test:**
- Action: Run all existing tests in tests/test_listings.py
- Assert: All tests pass without modification

---

## Manual QA Checklist

### Browser-Based Verification

**Visual Inspection:**
1. Start development server: `flask run`
2. Open browser to `http://localhost:5000/`
3. Inspect each showcase:
   - [ ] Showcase title displays category name
   - [ ] "See all" link is present and correctly formatted
   - [ ] Listing cards render with thumbnail, title, price
   - [ ] No broken images or missing data
4. Check page layout:
   - [ ] No layout shifts or rendering issues
   - [ ] Showcases are properly spaced
   - [ ] Overall page aesthetics unchanged

**Randomization Testing:**
1. Refresh page (F5 or Cmd+R)
2. Note order of listings in first showcase
3. Refresh 4 more times
4. Verify:
   - [ ] Listing order changes between refreshes
   - [ ] Different categories show different random selections
   - [ ] All refreshes complete successfully (no errors)

**Descendant Fallback Testing:**
1. Identify category with no direct listings (check admin panel or database)
2. Verify that category has child categories with listings
3. Load index page
4. Check that category's showcase:
   - [ ] Displays listings (from descendants)
   - [ ] Shows correct listing cards
   - [ ] "See all" link works

**Responsive Behavior:**
1. Desktop (1920x1080):
   - [ ] Showcases display multiple cards per row
   - [ ] Layout is clean and properly aligned
2. Tablet (768x1024):
   - [ ] Showcases adapt to narrower width
   - [ ] Cards resize appropriately
   - [ ] No horizontal scroll
3. Mobile (375x667):
   - [ ] Showcases display single or stacked cards
   - [ ] Touch scrolling works if showcase has horizontal scroll
   - [ ] Text remains readable

**Navigation Verification:**
1. Click "See all" link for each showcase category
2. Verify:
   - [ ] Navigates to correct category page
   - [ ] Category page displays all listings for that category
   - [ ] Breadcrumb shows correct path
   - [ ] Back button returns to index page

---

## Success Criteria Summary

### Automated Tests
- [ ] Query count test passes (≤2 queries for showcase data)
- [ ] Functional correctness tests pass
- [ ] Randomization test passes
- [ ] Descendant fallback test passes
- [ ] All existing tests pass unchanged

### Manual QA
- [ ] Visual showcase inspection: PASS
- [ ] Randomization verification: PASS
- [ ] Descendant fallback verification: PASS
- [ ] Responsive behavior check: PASS
- [ ] Navigation link verification: PASS

### Code Quality
- [ ] Code follows Pythonic conventions
- [ ] No deprecated methods used
- [ ] Proper use of SQLAlchemy 2.0 patterns
- [ ] Code is readable and maintainable
- [ ] Comments explain complex logic

### Documentation
- [ ] Pattern evaluation completed
- [ ] Instruction file updated if warranted
- [ ] Sprint completion documented

---

## Notes for Implementation

- **Import requirements:** Ensure `from collections import defaultdict` and `import random` are present
- **Query debugging:** Use `get_debug_queries()` during development to verify query count
- **Edge cases:** Test with zero categories, single category, all categories empty
- **Performance:** While focusing on query count, be mindful of Python-side processing efficiency
- **Rollback:** Not applicable - implementation must work correctly (no rollback option)

---

## References

- **Issue:** https://github.com/ferabreu/classifieds/issues/57
- **Primary file:** `app/routes/listings.py` (lines 60-103)
- **Model reference:** `app/models.py` (Category model)
- **Helper function:** `app/routes/utils.py` (get_index_carousel_categories)
- **Template:** `app/templates/index.html`
- **Test file:** `tests/test_listings.py`
- **Test fixtures:** `tests/conftest.py`
