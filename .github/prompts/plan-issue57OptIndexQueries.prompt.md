# Optimize Index Page Carousel Queries (Issue #57)

**Date:** 2026-01-25  
**Author:** GitHub Copilot (Claude Sonnet 4.5) 
**Issue:** https://github.com/ferabreu/classifieds/issues/57  
**Goal:** Reduce index page carousel queries from 7-13 queries to ≤2 queries

---

## Agent Role

You are an experienced developer versed in software development best practices with excellent knowledge of the Pythonic Way. You will optimize database query performance by refactoring an N+1 query pattern into efficient batch operations while maintaining identical user-facing behavior.

---

## Problem Analysis

### Current State

The index page (`/`) displays carousel showcases for multiple categories. The current implementation in `app/routes/listings.py` (lines 60-103) uses an N+1 query pattern:

**Query breakdown with 6 carousel categories:**
- **Query 0:** `Category.query.first()` - Redundant check if categories exist (1 query)
- **Per carousel category (N categories):**
  - **Query 1+N:** Fetch direct listings: `Listing.query.filter_by(category_id=category.id)...` (1 query per category)
  - **Query 2+N:** Conditionally fetch descendant listings if needed: `Listing.query.filter(Listing.category_id.in_(descendant_ids))...` (1 query per category with descendants)

**Total queries:**
- Best case: 1 + 6 = **7 queries** (all categories have enough direct listings)
- Worst case: 1 + (6 × 2) = **13 queries** (all categories need descendant fallback)

### Root Cause

Loop-based querying instead of batch operations. Each category triggers separate database queries for fetching listings, instead of fetching all needed listings in 1-2 batch queries and grouping results in Python.

### Impact

- Performance degradation on index page load
- Scales poorly as number of carousel categories increases
- Unnecessary database round-trips

---

## Work Plan

Use the `manage_todo_list` tool to track progress through these phases. Mark tasks as in-progress when starting, completed immediately after finishing.

### Phase 1: Refactor Batch Queries

**Target file:** `app/routes/listings.py` (index route, lines 60-103)

1. **Remove redundant category check**
   - Delete `Category.query.first()` check (line ~60)
   - Use `len(carousel_categories) > 0` instead

2. **Implement batch direct listings fetch**
   - Extract all carousel category IDs into a list
   - Use single query: `filter(Listing.category_id.in_(carousel_category_ids))`
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

6. **Verify identical behavior**
   - Ensure carousel data structure passed to template is unchanged
   - No template modifications required
   - User-facing behavior must be identical

**Acceptance criteria for Phase 1:**
- Code refactored in `app/routes/listings.py`
- Maximum 2 queries executed for carousel data (direct + optional descendants)
- Existing functionality preserved

### Phase 2: Write Automated Tests

**Target files:** `tests/conftest.py`, `tests/test_listings.py`

7. **Create carousel test fixtures in `conftest.py`**
   - Fixture: `carousel_categories` - Creates 3-6 categories with varied characteristics
   - Fixture: `carousel_listings` - Creates listings distributed across categories
   - Fixture: `category_with_children` - Parent category with child categories for descendant fallback testing
   - Keep fixtures minimal (focus on correctness, not scale)

8. **Write query count verification test**
   - Enable query tracking in test: `app.config['TESTING'] = True`
   - Use `flask_sqlalchemy.get_debug_queries()` to capture queries
   - Request index page route
   - Assert total queries for carousel data ≤ 2
   - Document test with clear comments explaining what it verifies

9. **Write functional correctness tests**
   - Test: Each carousel category displays correct listings
   - Test: Randomization produces varied results (multiple requests show different orderings)
   - Test: Display slots limit is respected (max N items per carousel)

10. **Write descendant fallback test**
    - Create category with no direct listings but descendants with listings
    - Request index page
    - Assert descendant listings appear in that category's carousel
    - Verify batch query optimization still applies

11. **Verify existing tests pass**
    - Run all tests in `tests/test_listings.py`
    - Ensure no regressions
    - All existing tests must pass without modification

**Acceptance criteria for Phase 2:**
- New test fixtures created
- Query count test passes (≤2 queries)
- Functional correctness tests pass
- Descendant fallback test passes
- All existing tests pass unchanged

### Phase 3: Execute Manual QA

12. **Visual carousel inspection**
    - Start development server
    - Load index page in browser
    - Verify all carousels render correctly
    - Check carousel titles, "See all" links, listing cards

13. **Randomization verification**
    - Refresh page multiple times (5+ refreshes)
    - Observe that listing order changes per carousel
    - Verify randomization is per-category (different categories show different random selections)

14. **Descendant fallback verification**
    - Identify or create category with no direct listings but has descendants with listings
    - Load index page
    - Verify carousel shows descendant listings for that category

15. **Responsive behavior check**
    - Test page on desktop viewport (1920x1080)
    - Test page on tablet viewport (768x1024)
    - Test page on mobile viewport (375x667)
    - Verify carousel cards wrap/resize appropriately

16. **Navigation link verification**
    - Click "See all" link for each carousel
    - Verify navigation to correct category page
    - Verify listing count on category page matches expected results

**Acceptance criteria for Phase 3:**
- All manual QA steps completed
- No visual regressions observed
- Randomization working as expected
- Descendant fallback working correctly
- Responsive behavior intact
- Navigation links functional

### Phase 4: Review and Update Instruction Files

17. **Evaluate pattern documentation need**
    - Review the batch-query-with-Python-grouping pattern implemented
    - Determine if this pattern is reusable for future query optimizations
    - Decision criteria:
      - Is this pattern applicable to other routes? (e.g., category page with child showcases)
      - Does it represent a general optimization technique?
      - Would future developers benefit from documented guidance?

18. **Update instruction file if warranted**
    - If decision is YES: Add section to `.github/instructions/python-flask.instructions.md`
    - Section title: "Query Optimization: Batch Fetching with Python-Side Grouping"
    - Content should include:
      - When to use this pattern (N+1 query scenarios)
      - Key principles (minimize database round-trips, group in Python)
      - Reference to this implementation as example
      - Trade-offs (memory vs query count)
    - If decision is NO: Document reasoning in sprint notes

**Acceptance criteria for Phase 4:**
- Pattern evaluation completed
- Decision documented
- Instruction file updated if applicable

---

## Implementation Requirements

### Batch Query Strategy

**Direct listings:**
```
Use: filter(Listing.category_id.in_(carousel_category_ids))
Order: by created_at.desc()
Result: Single query fetching all direct listings for all carousel categories
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
- Data structure: carousel_categories list with embedded showcase_listings must match current format
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

**carousel_categories fixture:**
- Create 3-6 categories with varied characteristics
- At least one category with child categories
- At least one category with no direct listings (for descendant fallback test)

**carousel_listings fixture:**
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
- Setup: carousel_categories and carousel_listings fixtures
- Action: GET request to index route
- Capture: get_debug_queries()
- Assert: ≤2 queries for listing data (exclude category/user queries)

**Functional correctness tests:**
- Test: Each carousel displays listings from correct category
- Test: Listing count per carousel respects display_slots limit
- Test: Response status is 200
- Test: Carousel data structure matches expected format

**Randomization test:**
- Setup: Category with 10+ listings
- Action: Multiple GET requests to index (3-5 requests)
- Capture: Order of listings per request
- Assert: At least one request shows different order than others

**Descendant fallback test:**
- Setup: category_with_children fixture (parent has no listings, children have listings)
- Action: GET request to index route
- Assert: Parent category's carousel shows child category listings
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
3. Inspect each carousel:
   - [ ] Carousel title displays category name
   - [ ] "See all" link is present and correctly formatted
   - [ ] Listing cards render with thumbnail, title, price
   - [ ] No broken images or missing data
4. Check page layout:
   - [ ] No layout shifts or rendering issues
   - [ ] Carousels are properly spaced
   - [ ] Overall page aesthetics unchanged

**Randomization Testing:**
1. Refresh page (F5 or Cmd+R)
2. Note order of listings in first carousel
3. Refresh 4 more times
4. Verify:
   - [ ] Listing order changes between refreshes
   - [ ] Different categories show different random selections
   - [ ] All refreshes complete successfully (no errors)

**Descendant Fallback Testing:**
1. Identify category with no direct listings (check admin panel or database)
2. Verify that category has child categories with listings
3. Load index page
4. Check that category's carousel:
   - [ ] Displays listings (from descendants)
   - [ ] Shows correct listing cards
   - [ ] "See all" link works

**Responsive Behavior:**
1. Desktop (1920x1080):
   - [ ] Carousels display multiple cards per row
   - [ ] Layout is clean and properly aligned
2. Tablet (768x1024):
   - [ ] Carousels adapt to narrower width
   - [ ] Cards resize appropriately
   - [ ] No horizontal scroll
3. Mobile (375x667):
   - [ ] Carousels display single or stacked cards
   - [ ] Touch scrolling works if carousel has horizontal scroll
   - [ ] Text remains readable

**Navigation Verification:**
1. Click "See all" link for each carousel category
2. Verify:
   - [ ] Navigates to correct category page
   - [ ] Category page displays all listings for that category
   - [ ] Breadcrumb shows correct path
   - [ ] Back button returns to index page

---

## Success Criteria Summary

### Automated Tests
- [ ] Query count test passes (≤2 queries for carousel data)
- [ ] Functional correctness tests pass
- [ ] Randomization test passes
- [ ] Descendant fallback test passes
- [ ] All existing tests pass unchanged

### Manual QA
- [ ] Visual carousel inspection: PASS
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
