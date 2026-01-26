**ferabreu:** Create a plan/prompt file for implementing a solution for issue 57 (https://github.com/ferabreu/classifieds/issues/57) of this project. Read the issue description and analyze the codebase to plan the solution. Other than the required instructions for a good prompt, remember to include a title, date and author name, a description of the problem, and provisions for creating the necessary tests (automated and also manual tests to be executed by the human developer).

**GitHub Copilot (Claude Sonnet 4.5):** I'll help you create a plan/prompt file for implementing issue 57. Let me start by fetching the issue details and analyzing the codebase. 

Fetching item [#57](https://github.com/ferabreu/classifieds/issues/57) from GitHub
Completed with input: {
  "issueNumber": 57,
  "repo": {
    "owner": "ferabreu",
    "name": "classifieds"
  }
}

Research issue 57 context

Fetching item [#57](https://github.com/ferabreu/classifieds/issues/57) from GitHub
Completed with input: {
  "issueNumber": 57
}

Read [](file:///home/ferabreu/Code/classifieds/app/models.py#1-1), lines 1 to 200

Read [](file:///home/ferabreu/Code/classifieds/app/routes/categories.py#1-1), lines 1 to 200

Read [](file:///home/ferabreu/Code/classifieds/app/templates/categories)

Read [](file:///home/ferabreu/Code/classifieds/app/templates/macros)

Read [](file:///home/ferabreu/Code/classifieds/app/routes/categories.py#200-200), lines 200 to 320

Read [](file:///home/ferabreu/Code/classifieds/app/routes/listings.py#1-1), lines 1 to 150

Read [](file:///home/ferabreu/Code/classifieds/app/templates/macros/breadcrumb.html)

Read [](file:///home/ferabreu/Code/classifieds/app/templates/macros/category.html)

Read [](file:///home/ferabreu/Code/classifieds/app/templates/macros/sidebar_category_tree.html)

Searched for text `category_filtered_listings`, 20 results

Searched for text `get_index_carousel_categories`, 20 results

Read [](file:///home/ferabreu/Code/classifieds/app/routes/utils.py#1-1), lines 1 to 200

Searched codebase for "category URL routing patterns category path view listings by category", 14 results

Read [](file:///home/ferabreu/Code/classifieds/app/models.py#200-200), lines 200 to 491

Read [](file:///home/ferabreu/Code/classifieds/app/routes/listings.py#150-150), lines 150 to 1120

Read [](file:///home/ferabreu/Code/classifieds/app/routes/utils.py#200-200), lines 200 to 245

Searched for regex `INDEX_CAROUSEL|THUMBNAIL_SIZE|carousel` (`**/app/config.py`), 6 results

Read [](file:///home/ferabreu/Code/classifieds/app/routes/listings.py#56-56), lines 56 to 120

Searched for text `CategoryView`, 20 results

Read [](file:///home/ferabreu/Code/classifieds/app/templates/index.html#1-1), lines 1 to 150

Perfect! Now I have all the context needed. Let me create a plan for the plan/prompt file that will guide implementation of issue 57.

## Plan: Create implementation prompt file for issue 57 carousel query optimization

This plan describes creating a comprehensive prompt/plan file that will guide an implementation agent or developer to optimize the N+1 query pattern in the index page carousel from 7-13 queries down to ≤2 queries.

### Steps

1. **Create prompt file** in docs/development/sprint_06-carousel_query_optimization/ directory with structured sections: title, metadata (date, author), problem description, technical context, implementation steps, and testing requirements

2. **Document the problem** with specific query counts (currently 7-13 queries for 6 carousels), root cause (N+1 pattern in listings.py), and performance impact on index page

3. **Define implementation approach** with batch querying strategy: single query for all direct listings using `Listing.category_id.in_(category_ids)`, single conditional query for descendant listings, Python-side grouping with `defaultdict`, and per-category randomization preservation

4. **Specify acceptance criteria** matching issue requirements: ≤2 queries for carousel data, correct listings per category, working randomization, functioning descendant fallback, and no user-facing regressions

5. **Include testing plan** with automated tests (query count verification, result correctness, randomization behavior) and manual QA steps (visual carousel inspection, descendant fallback verification, responsive behavior check)

### Further Considerations

1. **File organization:** Should the prompt file go in a new sprint_06 directory or elsewhere? Standard pattern shows sprint-numbered folders under docs/development/
2. **Test implementation scope:** Should the prompt include writing new pytest tests in test_listings.py, or just manual QA steps given the project's current limited test coverage?
3. **Rollback strategy:** Should the prompt include provisions for feature flagging or gradual rollout, or is direct implementation acceptable given this is an internal optimization?

**ferabreu:** 1. You can save the file in the `docs/development/sprint_06-issue_57-opt_index_queries/2-prompts` directory.
2. Include the creation of necessary tests in the `tests` directory, organizing them as you see fit (follow the best practices of the industry).
   - What do you mean by "given the project's current limited test coverage"?
3. No need for rollback. The optimization must be implemented and must work. There will be no rollback.

**GitHub Copilot (Claude Sonnet 4.5):** Let me check the existing test coverage to better understand the testing patterns in this project. 

Read [](file:///home/ferabreu/Code/classifieds/tests/test_listings.py)

Read [](file:///home/ferabreu/Code/classifieds/tests/conftest.py#1-1), lines 1 to 50

Read [](file:///home/ferabreu/Code/classifieds/tests)

Read [](file:///home/ferabreu/Code/classifieds/tests/conftest.py#50-50), lines 50 to 79

Perfect! Now I understand the testing infrastructure. The project has pytest set up with fixtures for app, client, user, admin_user, category, and listing. By "limited test coverage" I meant that while tests exist, they currently focus on basic functionality (routes return 200, basic CRUD works) rather than performance metrics like query counts.

Now I'll create the comprehensive prompt file:

## Plan: Implementation prompt file for carousel query optimization

Create a detailed implementation prompt file in 2-prompts that guides complete implementation of the carousel query optimization, including comprehensive automated tests using pytest with query count assertions and functional correctness validation.

### Steps

1. **Structure prompt file** with metadata header (title, date: 2026-01-25, author: Felipe Abreu), problem statement citing specific query counts from listings.py, technical analysis of N+1 pattern, and solution architecture

2. **Define implementation tasks** covering batch query refactoring (use `Listing.category_id.in_()` for direct listings, conditional batch query for descendants), Python-side grouping with `collections.defaultdict`, randomization preservation per category, and removal of redundant `Category.query.first()` check

3. **Specify test requirements** including new test fixtures in conftest.py for multi-category carousel scenarios, query count verification tests using Flask-SQLAlchemy event listeners or query logging, functional correctness tests validating listings per category and randomization, and descendant fallback tests

4. **Document acceptance criteria** with measurable outcomes: query count ≤2 (verified by automated test), all existing test_listings.py tests pass, new performance tests pass, manual QA confirms visual carousel correctness, and zero regressions in user-facing behavior

5. **Include manual QA checklist** with steps to visually verify carousels render correctly, check randomization varies on page refresh, confirm descendant fallback displays when categories lack direct listings, test responsive behavior on mobile/tablet viewports, and verify "See all" links work

### Further Considerations

1. **Query counting approach:** Should tests use SQLAlchemy event listeners (`@event.listens_for(Engine, "before_cursor_execute")`), Flask-SQLAlchemy's `get_debug_queries()`, or a custom context manager? Flask-SQLAlchemy's approach is cleaner for testing.

2. **Test data scale:** Should performance tests create realistic data volumes (e.g., 100+ listings across 10+ categories) to demonstrate actual performance improvement, or keep minimal fixtures for speed?

3. **Documentation updates:** Should the prompt include updating copilot-notes.md or other documentation with the new optimized pattern as a reference for future development?

**ferabreu:** 1. If Flask-SQLAlchemy's approach is cleaner for testing, use it.
2. Minimal fixtures for speed will be enough. The solution for the problem at hand is more about performing operations in the best way (by using less queries, optimizing queries, etc.) than actual speed measuring.
3. `copilot-notes.md` should be as abstract as possible, since it's a guide for all development. It's not meant to enumerate concrete patterns of the codebase. If the implementation of this sprint creates a situation in which future development requires new instructions to be successfully performed, you may add them to the specific instructions files in the `.github/instructions/` directory.

**GitHub Copilot (Claude Sonnet 4.5):** ## Plan: Implementation prompt for carousel query optimization (Issue #57)

Create a comprehensive implementation prompt file that will guide an agent or developer to optimize the index page carousel queries from 7-13 queries down to ≤2 queries, with automated tests verifying query counts using Flask-SQLAlchemy's `get_debug_queries()` and minimal fixtures focusing on correctness over performance benchmarking.

### Steps

1. **Create prompt file** at docs/development/sprint_06-issue_57-opt_index_queries/2-prompts/implementation-prompt.md with header metadata (title, date: 2026-01-25, author: Felipe Abreu), detailed problem analysis citing current N+1 pattern in listings.py, and technical context from models.py Category model

2. **Document implementation steps** with refactoring strategy for batch queries using `Listing.category_id.in_(carousel_category_ids)`, Python-side grouping with `collections.defaultdict`, preserving per-category randomization with `random.shuffle()`, handling descendant fallback in batch, and removing redundant `Category.query.first()` check

3. **Specify test requirements** including new fixtures in conftest.py for carousel scenarios (parent category with children, categories needing descendant fallback), query count verification using `flask_sqlalchemy.get_debug_queries()` asserting ≤2 queries, functional tests validating correct listings per category, and descendant fallback behavior tests

4. **Define acceptance criteria** with concrete metrics: automated test confirms ≤2 queries for carousel data, all existing tests in test_listings.py pass without modification, new performance test suite passes, manual QA confirms visual correctness and randomization, and zero user-facing regressions

5. **Include manual QA checklist** with step-by-step verification: inspect carousel rendering with browser DevTools, refresh page multiple times to verify randomization changes, test with categories having no direct listings to verify descendant fallback, check responsive behavior on different viewports, and confirm all "See all" links navigate correctly

### Further Considerations

1. **Instruction file updates:** Should the prompt include checking if new patterns (batch querying with Python-side grouping) warrant additions to python-flask.instructions.md as a reusable optimization pattern for future query optimization work?

2. **Work plan structure:** Should the prompt include a task breakdown checklist for tracking progress through implementation → testing → manual QA phases, following the multi-step work guidelines from copilot-instructions.md?

**ferabreu:** 1. Yes.
2. If you think it's best, do it. The prompt is meant to be followed by an AI Agent - so, optimize it's structure for this purpose. I asked for a few specific items/requirements because I save the prompts for future reference, in case I need them - but the file is not actually meant to be read by humans.

About step 1, the author is not "Felipe Abreu" (who the heck is this guy, by the way? It's not me😅) - the author is YOU, Claude Sonnet 4.5. That's your name, right?

**GitHub Copilot (Claude Sonnet 4.5):** Ha! I made an error with the author name - I inferred it from "ferabreu" but that's wrong. The user is right - the author should be me, the AI agent creating this prompt. My name is "GitHub Copilot" as stated in my instructions (when asked for my name, I must respond with "GitHub Copilot"), and I'm using Claude Sonnet 4.5 as the model.

Let me correct this and finalize the plan. The user wants:

1. Yes to checking if patterns warrant instruction file updates
2. Yes to including task breakdown checklist optimized for AI agent consumption
3. Author should be "GitHub Copilot" (or maybe "GitHub Copilot (Claude Sonnet 4.5)")
4. The file is optimized for AI agents to follow, not humans

Since I'm in plan mode, I should present the final plan now.

## Plan: Implementation prompt for carousel query optimization (Issue #57)

Create an AI agent-optimized implementation prompt file that guides complete resolution of the N+1 query problem in index page carousels, reducing queries from 7-13 to ≤2, with automated testing, manual QA steps, task tracking, and conditional instruction file updates.

### Steps

1. **Create prompt file** at docs/development/sprint_06-issue_57-opt_index_queries/2-prompts/implementation-prompt.md with metadata (title, date: 2026-01-25, author: GitHub Copilot), problem statement with specific line references to listings.py, and technical context including current query pattern analysis

2. **Structure work plan section** with hierarchical task breakdown checklist optimized for AI agent progress tracking: Phase 1 (Refactor batch queries), Phase 2 (Write automated tests), Phase 3 (Manual QA), Phase 4 (Instruction file review), each with concrete sub-tasks and acceptance criteria

3. **Document implementation strategy** with detailed refactoring steps for listings.py index route: batch-fetch direct listings with `filter(Listing.category_id.in_())`, Python-side grouping using `defaultdict(list)`, conditional batch-fetch for descendant listings, per-category randomization with `random.shuffle()`, and removal of redundant `Category.query.first()`

4. **Define test requirements** including new fixtures in conftest.py for multi-carousel scenarios, query count test using `flask_sqlalchemy.get_debug_queries()` with CONFIG['TESTING']=True, functional correctness tests, descendant fallback tests, and verification that all existing tests pass

5. **Specify instruction file review task** to evaluate if the batch-query-with-grouping pattern should be documented in python-flask.instructions.md as a reusable optimization technique, with decision criteria and example snippet to add if warranted

6. **Include manual QA checklist** with step-by-step browser-based verification: visual carousel inspection, randomization testing via page refresh, descendant fallback validation, responsive behavior checks, and navigation link verification

### Further Considerations

1. **Prompt format:** Should the prompt use imperative tone with direct commands ("Refactor the index route...") or second-person guidance ("You should refactor...") for optimal AI agent comprehension?

2. **Code examples:** Should the prompt include skeleton code snippets showing the expected batch query structure and grouping logic, or rely on the agent to derive the implementation from requirements?

**ferabreu:** 1. Both. Do it like this:
   - Include an initial second-person guidance statement defining the role of the AI Agent: "Experienced developer, versed on the best practices of software development, with excellent knowlege of the 'Pythonic Way'"
   - Use imperative tone for defining the tasks/steps
2. Rely on the agent to derive the implementation from requirements.

**GitHub Copilot (Claude Sonnet 4.5):** ## Plan: Implementation prompt for carousel query optimization (Issue #57)

Create an AI agent-optimized implementation prompt at docs/development/sprint_06-issue_57-opt_index_queries/2-prompts/implementation-prompt.md that guides complete resolution of the N+1 query problem in index page carousels, reducing queries from 7-13 to ≤2.

### Steps

1. **Write metadata header** with title "Optimize Index Page Carousel Queries (Issue #57)", date "2026-01-25", author "GitHub Copilot", and brief summary stating the optimization goal (7-13 queries → ≤2 queries)

2. **Define agent role** with second-person statement positioning the agent as "an experienced developer versed in software development best practices with excellent knowledge of the Pythonic Way," establishing context and expected expertise level

3. **Document problem analysis** citing current N+1 pattern in listings.py, explaining query breakdown (1 redundant check + 6-12 per-category queries), referencing issue #57 description, and identifying root cause (loop-based querying instead of batch operations)

4. **Structure hierarchical work plan** with imperative-tone tasks across four phases: Phase 1 (Refactor batch queries in listings.py), Phase 2 (Write automated tests in test_listings.py and fixtures in conftest.py), Phase 3 (Execute manual QA checklist), Phase 4 (Review and update python-flask.instructions.md if warranted)

5. **Specify implementation requirements** detailing batch query strategy (use `filter(Listing.category_id.in_())` for direct listings, conditional batch for descendants), Python-side grouping with `collections.defaultdict`, per-category randomization preservation, redundant query removal, and requirement to maintain identical user-facing behavior

6. **Define test specifications** including new minimal fixtures for carousel scenarios (multi-category setup, descendant fallback scenario), query count test using `flask_sqlalchemy.get_debug_queries()` asserting ≤2 queries, functional correctness tests, verification all existing tests pass unchanged

7. **Include manual QA checklist** with imperative browser-based verification steps: inspect carousel rendering, refresh page to verify randomization changes, test descendant fallback with empty categories, validate responsive behavior, confirm navigation links work

8. **Add instruction file review task** with decision criteria for whether batch-query-with-Python-grouping pattern warrants documentation in python-flask.instructions.md as reusable optimization technique for future query optimization work

### Further Considerations

None - all requirements clarified. Ready to proceed with prompt creation.

**ferabreu:** #createFile the plan as is into an untitled file (`untitled:plan-${camelCaseName}.prompt.md` without frontmatter) for further refinement.

**GitHub Copilot (Claude Sonnet 4.5):** Optimizing tool selection...

Created [](untitled:plan-issue57OptIndexQueries.prompt.md)

I've created the implementation prompt file as an untitled document. The prompt is optimized for an AI agent with:

✅ **Agent role definition** - Positioned as experienced Python developer  
✅ **Imperative tone tasks** - Clear actionable steps  
✅ **Hierarchical work plan** - 4 phases with 18 trackable tasks  
✅ **Query optimization strategy** - Batch fetching with Python-side grouping  
✅ **Test specifications** - Using `get_debug_queries()` with minimal fixtures  
✅ **Manual QA checklist** - Step-by-step browser verification  
✅ **Instruction file review** - Conditional update to python-flask.instructions.md  

The prompt focuses on correctness over performance benchmarking, relies on the agent to derive implementation details, and includes comprehensive acceptance criteria for each phase.

Made changes.