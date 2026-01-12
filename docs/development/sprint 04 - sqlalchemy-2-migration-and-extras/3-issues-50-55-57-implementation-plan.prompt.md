# Implementation Plan: Issues #55 → #50 → #57

**Sprint:** 04 (Tech Debt Foundation + Optimization)  
**Created:** January 11, 2026  
**Target Branch:** `sqlalchemy-2-migration-and-extras`  
**Estimated Total Effort:** 13-15 hours

---

## Overview: What Problems Are We Solving?

### Issue #55: Outdated Database API (8-10 hours) - **DO THIS FIRST**

**Problem in Plain English:**
The app uses an "old way" of talking to the database that's being discontinued. Imagine using a phone with old technology - it still works, but soon it won't be supported anymore.

**Technical Details:**
- The codebase uses Flask-SQLAlchemy's legacy `.query` API (e.g., `User.query.filter(...)`)
- This API is deprecated and **will be completely removed** in Flask-SQLAlchemy 3.1+
- The modern equivalent is the `select()` API (e.g., `select(User).where(...)`)
- When someone upgrades Flask-SQLAlchemy, the entire app will break if this isn't fixed

**Why Fix It First?**
Issues #50 and #57 require new code. If we write that new code using the old API, we'll have to rewrite it later when doing the tech debt work. Instead, modernize the API first, then write all new code in the modern style.

**Real-World Analogy:**
It's like painting a house. Don't paint new rooms with old paint that peels off - first update to new paint, then paint everything consistently.

---

### Issue #50: Cycle Protection for Categories (2 hours) - **DO THIS SECOND**

**Problem in Plain English:**
Categories can be organized in a hierarchy (like folder structures: Electronics > Computers > Laptops). Currently, the system prevents someone from creating circular relationships, but only **after** they submit the form with a confusing error message.

**What's a Cycle?**
```
❌ BAD (Circular):
- Electronics (parent: null)
- Computers (parent: Electronics)  
- Laptops (parent: Computers)
- Then someone tries: Electronics (parent: Laptops)
- This creates a circle: Electronics → Laptops → Computers → Electronics → ...

✅ GOOD (Hierarchy):
- Electronics (parent: null)
- Computers (parent: Electronics)
- Laptops (parent: Computers)
```

**Current Behavior:**
1. User submits form
2. Database detects cycle
3. Form submission fails with generic error
4. User is confused

**New Behavior (After #50):**
1. User types in the form
2. JavaScript checks if selection would create a cycle
3. Form shows user-friendly error: "Cannot set Laptops as parent of Electronics (would create a circle)"
4. User fixes the problem before submitting

**Why Now?**
User experience. Errors caught early = happy users.

---

### Issue #57: Speed Up Index Page (3 hours) - **DO THIS THIRD**

**Problem in Plain English:**
The index page shows carousel displays of listings by category. Currently, it's inefficient - it asks the database for information multiple times instead of once.

**What's Happening Now (Bad - Multiple Queries):**
```
For 6 carousel categories:
Query 1: "Get listings in category 1"
Query 2: "Get listings in category 1's children"
Query 3: "Get listings in category 2"
Query 4: "Get listings in category 2's children"
... repeat for 6 categories
= 12 database queries!
```

**What Should Happen (Good - Batch Queries):**
```
Query 1: "Get listings in ALL 6 categories at once"
Query 2: "Get listings in ALL children of these 6 categories at once"
Then organize the results in Python
= 2 database queries!
```

**Impact:**
- Current: 12 queries, slower page load
- After fix: 2 queries, 3-6x faster

**Why Now?**
Performance matters. Users notice slow pages. Fix it while implementing carousel features.

---

## Part 1: Issue #55 - Modernize Database Code (First Sprint Phase)

### What We're Doing

Converting all database queries from the old `.query` style to the new `select()` style.

**Old Style (❌ Deprecated):**
```python
user = User.query.filter_by(email=email).first()
users = User.query.order_by(User.email).all()
```

**New Style (✅ Modern):**
```python
from sqlalchemy import select

user = db.session.execute(
    select(User).where(User.email == email)
).scalar_one_or_none()

users = db.session.execute(
    select(User).order_by(User.email)
).scalars().all()
```

### Implementation Steps

#### Step 1: Update `requirements.txt` (Pin Dependencies) - 15 minutes

Pin specific versions to avoid future compatibility issues:

```python
# In requirements.txt, change these lines:
# FROM:
# Flask-SQLAlchemy
# SQLAlchemy

# TO:
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.23
```

**Why?** These versions are tested and compatible with each other.

**Test:** Run this command to verify no conflicts:
```bash
pip install --dry-run -r requirements.txt
```

#### Step 2: Migrate `app/routes/auth.py` (1 hour)

This file handles login and registration. Replace all `.query` calls with `select()`.

**Imports to add at top of file:**
```python
from sqlalchemy import select
```

**Changes needed (Find and replace these patterns):**

| Location | Old Code | New Code |
|----------|----------|----------|
| forgot_password route | `User.query.filter_by(email=email.lower()).first()` | `db.session.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()` |
| login route | `User.query.filter_by(email=email.lower()).first()` | `db.session.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()` |
| register route (check exists) | `User.query.filter_by(email=email).first()` | `db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()` |

**Step-by-step for one example:**
```python
# BEFORE (lines ~XX):
if User.query.filter_by(email=email.lower()).first():
    form.email.errors = ('This email is already registered.',)

# AFTER:
existing_user = db.session.execute(
    select(User).where(User.email == email.lower())
).scalar_one_or_none()

if existing_user:
    form.email.errors = ('This email is already registered.',)
```

**Why this works:**
- `select(User)` - "Select from User table"
- `.where(User.email == email.lower())` - "Filter by email" 
- `db.session.execute(...)` - "Execute the query"
- `.scalar_one_or_none()` - "Return a single result or None"

**Code Reuse:** The pattern `db.session.execute(select(Model).where(...)).scalar_one_or_none()` is the standard modern way. Use it consistently.

#### Step 3: Migrate `app/routes/users.py` (1.5 hours)

This file handles user profiles and admin user management.

**Imports to add:**
```python
from sqlalchemy import select
```

**Changes needed:**

Find all these patterns and replace:

```python
# Pattern 1: Getting a single user by ID
# BEFORE:
user = User.query.get_or_404(user_id)

# AFTER:
user = db.session.get(User, user_id) or abort(404)

---

# Pattern 2: Getting a single user by email
# BEFORE:
user = User.query.filter_by(email=email).first()

# AFTER:
user = db.session.execute(
    select(User).where(User.email == email)
).scalar_one_or_none()

---

# Pattern 3: Getting all users (with ordering)
# BEFORE:
all_users = User.query.order_by(User.email).all()

# AFTER:
all_users = db.session.execute(
    select(User).order_by(User.email)
).scalars().all()

---

# Pattern 4: Counting users (important in admin_list)
# BEFORE:
user_count = User.query.count()

# AFTER:
user_count = db.session.query(func.count(User.id)).scalar()
# OR simpler:
user_count = len(db.session.execute(select(User)).scalars().all())
```

**Special Note on admin_list() function:**
- This function already has N+1 query optimization (fetching listing counts)
- Use `selectinload` for eagerly loading relationships when available
- Check if subquery pattern needs updating to use `select()`

#### Step 4: Migrate `app/routes/categories.py` (1.5 hours)

This file handles category CRUD (Create, Read, Update, Delete).

**Imports to add:**
```python
from sqlalchemy import select
```

**Critical Patterns to Replace:**

```python
# Pattern 1: Get category by ID
# BEFORE:
category = Category.query.get_or_404(category_id)

# AFTER:
category = db.session.get(Category, category_id) or abort(404)

---

# Pattern 2: Check if category exists
# BEFORE:
if Category.query.filter_by(url_name=url_name, parent_id=parent_id).first():

# AFTER:
if db.session.execute(
    select(Category).where(
        Category.url_name == url_name,
        Category.parent_id == parent_id
    )
).scalar_one_or_none():

---

# Pattern 3: Get all root categories (parent_id is None)
# BEFORE:
root_cats = Category.query.filter_by(parent_id=None).order_by(Category.name).all()

# AFTER:
root_cats = db.session.execute(
    select(Category).where(
        Category.parent_id == None
    ).order_by(Category.name)
).scalars().all()

---

# Pattern 4: Get many categories in a list
# BEFORE:
categories = Category.query.filter(Category.id.in_(category_ids)).all()

# AFTER:
categories = db.session.execute(
    select(Category).where(Category.id.in_(category_ids))
).scalars().all()
```

**Code Reuse Tip:** The function `_validate_category_inputs()` at the bottom is already modern-ready. Verify it uses `db.session.execute()` for the sibling uniqueness check (line ~300).

#### Step 5: Migrate `app/routes/listings.py` (2 hours)

This is the largest file with the most complex queries.

**Imports to add:**
```python
from sqlalchemy import select
```

**Key Functions to Update:**

1. **`index()` function:**
   - Already being refactored for #57
   - Will naturally use `select()` API in the new implementation

2. **`category_listings()` function:**
   ```python
   # BEFORE:
   category = Category.query.get_or_404(category_id)
   listings_query = Listing.query.filter(Listing.category_id.in_(descendant_ids))
   
   # AFTER:
   category = db.session.get(Category, category_id) or abort(404)
   listings_query = db.session.execute(
       select(Listing).where(Listing.category_id.in_(descendant_ids))
   )
   ```

3. **`category_filtered_listings()` function:**
   - Uses `Category.from_path()` which is already modern
   - Verify it doesn't use `.query` internally

4. **`listing_detail()` function:**
   - `Listing.query.get_or_404(listing_id)` → `db.session.get(Listing, listing_id) or abort(404)`

5. **Helper functions (_delete_listings_impl, _edit_listing_impl, etc.):**
   - Check each one for `.query` API usage
   - Replace with equivalent `select()` calls
   - Keep the logic exactly the same, just change the API

**Complex Example - Listing Query:**
```python
# BEFORE (in listing_detail or similar):
listing = Listing.query.filter_by(id=listing_id).first()
if not listing:
    abort(404)

# AFTER:
listing = db.session.execute(
    select(Listing).where(Listing.id == listing_id)
).scalar_one_or_none()
if not listing:
    abort(404)
```

#### Step 6: Migrate `app/routes/admin.py` (1 hour)

Admin-specific operations.

**Patterns:**
```python
# BEFORE:
user = User.query.get_or_404(user_id)
all_categories = Category.query.all()
all_listings = Listing.query.all()

# AFTER:
user = db.session.get(User, user_id) or abort(404)
all_categories = db.session.execute(select(Category)).scalars().all()
all_listings = db.session.execute(select(Listing)).scalars().all()
```

#### Step 7: Migrate `app/cli/` Commands (1.5 hours)

CLI commands in `maintenance.py` and `demo.py`.

**Same patterns apply:**
- `Model.query` → `select(Model)`
- `.filter_by()` → `.where()`
- `.all()` → `.scalars().all()`

#### Step 8: Verify `app/models.py` (30 minutes)

Check if any model definitions use query patterns (they shouldn't, but verify).

**These should already be modern:**
- `would_create_cycle()` - uses `session.get()` ✓
- `get_descendant_ids()` - uses list comprehension ✓
- `breadcrumb` property - uses list comprehension ✓
- `from_path()` - uses `db.session.execute()` (or should)

Verify `from_path()` uses modern API. If not:
```python
# BEFORE:
parent = Category.query.filter_by(url_name=segment).first()

# AFTER:
parent = db.session.execute(
    select(Category).where(Category.url_name == segment)
).scalar_one_or_none()
```

### Testing Checklist for #55

**Automated Checks:**
- [ ] Syntax check: `python -m py_compile app/routes/*.py app/cli/*.py app/models.py`
- [ ] Import check: `python -c "from app import create_app; app = create_app(); print('✓ App imports successfully')"`
- [ ] No legacy `.query` references remain: `grep -r "\.query\." app/ --include="*.py" | grep -v "# type: ignore"`

**Manual QA (User Flows):**
- [ ] **Registration flow:**
  - [ ] Register new user with email → works
  - [ ] Try registering with existing email → error message shown
  
- [ ] **Login flow:**
  - [ ] Login with correct email/password → works
  - [ ] Login with wrong password → "Invalid credentials"
  - [ ] Forgot password → can request reset token
  
- [ ] **Category management:**
  - [ ] View all categories → loads
  - [ ] Create category → saves
  - [ ] Edit category → saves
  - [ ] Get category by path (e.g., `/electronics/computers`) → works
  
- [ ] **Listing management:**
  - [ ] View listing → loads
  - [ ] Create listing → saves with images
  - [ ] Edit listing → saves
  - [ ] Delete listing → deletes
  
- [ ] **Admin functions:**
  - [ ] View admin dashboard → loads user list
  - [ ] Edit user → saves
  - [ ] Delete user → works (with safeguards)
  - [ ] View all listings → loads
  
- [ ] **CLI commands (if applicable):**
  - [ ] `flask init` → works
  - [ ] `flask demo` → works (creates demo data)
  - [ ] `flask backfill-thumbnails` → works

**Performance Validation:**
- [ ] Load index page
- [ ] Monitor page load time (should not noticeably change)
- [ ] No slowdown introduced by new API

### Commit Message for #55

```
refactor(#55): Migrate entire codebase from .query API to modern select() API

Complete migration to SQLAlchemy 2.0 select() API:
- Pin Flask-SQLAlchemy==3.0.5 and SQLAlchemy==2.0.23 in requirements.txt
- Convert all .query API calls in auth.py, users.py, categories.py, listings.py, admin.py
- Migrate CLI commands in maintenance.py and demo.py
- Update models.py to use select() and session.get() consistently
- Remove # type: ignore comments where migration improves type safety

Technical details:
- Model.query.filter(...) → db.session.execute(select(Model).where(...))
- Model.query.get(id) → db.session.get(Model, id)
- Model.query.all() → db.session.execute(select(Model)).scalars().all()

No behavioral changes - pure API modernization.
This modernization provides foundation for issues #50 and #57.

Fixes: #55
```

---

## Part 2: Issue #50 - Form-Level Cycle Protection (After #55 Complete)

### Problem Recap

Currently, category parent assignment allows cycles (circular relationships) only at the database level. Users don't get friendly feedback until after form submission fails with a generic database error.

### What We're Building

A form validator that:
1. Checks if the selected parent would create a cycle
2. Shows user-friendly error message BEFORE form submission
3. Reuses database's `would_create_cycle()` method
4. Works in both create and edit flows

### Implementation Steps

#### Step 1: Create WTForms Validator in `app/forms.py`

Add this new validator class. Find where other validators are defined (look for `class` definitions in forms.py), and add this after them:

```python
class NoCycleValidator:
    """
    Validates that assigning a parent category wouldn't create a cycle.
    
    Prevents situations like:
    - Electronics → Computers → Laptops → Electronics (circular!)
    
    This validator reuses the Category.would_create_cycle() method
    which already exists in models.py. We're just using it in the form
    for early validation feedback.
    
    Works with:
    - Create flow: form._obj is None
    - Edit flow: form._obj is the Category being edited
    """
    
    def __init__(self, message=None):
        self.message = message or "Cannot set this category as parent (would create a cycle)"
    
    def __call__(self, form, field):
        """
        Called automatically when form validates.
        
        Args:
            form: The CategoryForm instance
            field: The parent_id field being validated
        """
        # Get the category being edited (None if creating new)
        current_category = getattr(form, '_obj', None)
        
        # Extract parent_id from field data
        # SelectField returns string, so convert to int
        if not field.data or field.data == "0":
            # No parent selected = not a cycle
            return
        
        try:
            parent_id = int(field.data)
        except (TypeError, ValueError):
            # Invalid data, other validators will catch this
            return
        
        # Only validate if we're editing an existing category
        # (new categories can't create cycles yet since they don't exist)
        if current_category and hasattr(current_category, 'would_create_cycle'):
            # Use the Category model's built-in cycle detection
            if current_category.would_create_cycle(parent_id, db.session):
                raise ValidationError(self.message)
```

**Code Reuse:** This reuses the existing `Category.would_create_cycle()` method from models.py. Don't reinvent the wheel - the database logic is already there.

#### Step 2: Update CategoryForm in `app/forms.py`

Find the `CategoryForm` class and add the validator:

**Before:**
```python
class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[...])
    parent_id = SelectField('Parent Category', coerce=...)
    submit = SubmitField('Create Category')
```

**After:**
```python
class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[...])
    parent_id = SelectField(
        'Parent Category',
        coerce=lambda x: int(x) if x and x != "0" else None,
        validators=[
            Optional(),
            NoCycleValidator()  # Add this line
        ]
    )
    submit = SubmitField('Create Category')
```

#### Step 3: Update `app/routes/categories.py` - Edit Route

Find the `edit_category()` function and add one line:

**Before:**
```python
@categories_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)  # Now db.session.get() after #55
    form = CategoryForm()  # <-- Form created here
    
    # ... set up choices ...
    
    if form.validate_on_submit():
```

**After:**
```python
@categories_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    category = db.session.get(Category, category_id) or abort(404)
    form = CategoryForm()
    
    # ADD THIS LINE - tells the validator which category we're editing
    form._obj = category
    
    # ... rest of function ...
    
    if form.validate_on_submit():
```

**Why?** The validator needs to know which category is being edited so it can check `would_create_cycle()` correctly.

#### Step 4: Update Create Route (Optional Polish)

In `create_category()`, no changes needed - form._obj is None by default, which is correct.

#### Step 5: Test Template Error Display

Find `templates/categories/category_form.html` and verify it shows form errors. Look for something like:

```html
<div class="form-group">
    {{ form.parent_id.label }}
    {{ form.parent_id(class="form-control") }}
    {% if form.parent_id.errors %}
        <div class="text-danger">
            {% for error in form.parent_id.errors %}
                <small>{{ error }}</small><br>
            {% endfor %}
        </div>
    {% endif %}
}</div>
```

If not present, add it. This displays validation errors automatically.

### Testing Checklist for #50

**Code Validation:**
- [ ] Syntax check: `python -m py_compile app/forms.py app/routes/categories.py`
- [ ] App initialization: `python -c "from app import create_app; app = create_app()"`

**Manual QA - Create Flow:**
- [ ] Create root category "Electronics" (no parent) → saves ✓
- [ ] Create child "Computers" with parent "Electronics" → saves ✓
- [ ] Create grandchild "Laptops" with parent "Computers" → saves ✓

**Manual QA - Edit Flow (Cycle Prevention):**
- [ ] Edit "Electronics" category
- [ ] Try to set parent to "Computers" 
  - [ ] Form shows validation error before submission ✓
  - [ ] Error message is user-friendly ✓
- [ ] Try to set parent to "Laptops"
  - [ ] Form shows validation error ✓
- [ ] Try to set parent to "Electronics" (self)
  - [ ] Form shows validation error ✓
- [ ] Change parent to valid category (e.g., another root category)
  - [ ] Form submits successfully ✓

**Manual QA - Database-Level Safety:**
- [ ] Database-level protection still works if someone bypasses form
  - [ ] Direct database manipulation to create cycle should still fail at flush time

**Edge Cases:**
- [ ] Create category with no parent → works ✓
- [ ] Edit category removing parent (setting to None) → works ✓
- [ ] Validate form with empty parent choice → no error ✓

### Commit Message for #50

```
feat(#50): Add form-level validation for category cycle prevention

Provides user-friendly cycle detection when assigning category parents:
- Create NoCycleValidator in forms.py that reuses Category.would_create_cycle()
- Add validator to CategoryForm.parent_id field
- Set form._obj in edit_category() route for validator context
- Form errors display before submission (improved UX)
- Database-level protection (before_flush) remains as safety net

Users now see validation error immediately when trying to:
- Assign self as parent
- Assign descendant as parent
- Create any circular relationship

Technical approach:
- Leverages existing Category.would_create_cycle() (DRY principle)
- Works with modern select() API from #55
- No behavioral changes to create/edit routes
- Template error display already functional

Fixes: #50
```

---

## Part 3: Issue #57 - Optimize Carousel Queries (After #55 Complete)

### Problem Recap

Index page loads carousel data using 6+ database queries (one per carousel category). This can be optimized to 2 queries by batch-fetching and grouping results in Python.

### What We're Building

New helper function that:
1. Batch-fetches all direct listings for all carousel categories (Query 1)
2. Batch-fetches all descendant listings (Query 2)
3. Groups results in Python
4. Maintains per-category randomization
5. Preserves existing UI/UX exactly

### Implementation Steps

#### Step 1: Create Batch Helper in `app/routes/utils.py`

Add this new function to utils.py. Add imports at the top:

```python
from sqlalchemy import select, func
import random
```

Then add the helper function (find where other helpers are and add after them):

```python
def get_carousel_listings_batch(
    carousel_categories: list['Category'],
    items_per_carousel: int = 10
) -> list[dict]:
    """
    Efficiently fetch all carousel listings using batch queries instead of per-category queries.
    
    BEFORE (Inefficient - N+1 problem):
    - For each of 6 carousel categories:
      - Query 1: Get direct listings
      - Query 2: Get descendant listings (if needed)
    - Total: 6+ queries
    
    AFTER (Efficient):
    - Query 1: Get all direct listings for all 6 categories at once
    - Query 2: Get all descendant listings for all categories at once
    - Total: 2 queries, then organize in Python
    
    Args:
        carousel_categories: List of Category objects to fetch listings for
        items_per_carousel: Max items to show per carousel (default 10)
    
    Returns:
        List of dicts: [
            {"category": Category, "listings": [Listing, ...]},
            {"category": Category, "listings": [Listing, ...]},
            ...
        ]
    
    Randomization:
    - Per-category results are shuffled in Python
    - User sees different listings each page reload
    - Preserves randomization from original implementation
    """
    if not carousel_categories:
        return []
    
    carousel_ids = [c.id for c in carousel_categories]
    
    # How many listings to fetch per category
    # (fetch more than display to have variety for randomization)
    display_slots = min(items_per_carousel, 5)  # UI shows up to 5 per row
    fetch_limit = max(display_slots * 2, items_per_carousel)
    
    # ===== QUERY 1: Fetch all direct listings for all carousel categories =====
    # Instead of: for each category, query its listings
    # Now: query all categories' listings at once
    direct_listings = db.session.execute(
        select(Listing)
        .where(Listing.category_id.in_(carousel_ids))
        .order_by(Listing.created_at.desc())
        .limit(fetch_limit * len(carousel_ids))  # Buffer for having variety
    ).scalars().all()
    
    # Group direct listings by category_id for quick lookup
    # This turns the flat list into: {category_id: [listing1, listing2, ...]}
    listings_by_category_id = {}
    for listing in direct_listings:
        if listing.category_id not in listings_by_category_id:
            listings_by_category_id[listing.category_id] = []
        listings_by_category_id[listing.category_id].append(listing)
    
    # Find categories that don't have enough direct listings
    # These will need to pull from descendant categories
    categories_needing_more = []
    for category in carousel_categories:
        direct_count = len(listings_by_category_id.get(category.id, []))
        if direct_count < fetch_limit:
            categories_needing_more.append(category)
    
    # ===== QUERY 2: Fetch descendant listings for categories that need more =====
    if categories_needing_more:
        # Build set of all descendant IDs for the categories needing more
        # Example: if Computers needs more, get all IDs of its children (Laptops, etc.)
        all_descendant_ids = set()
        for category in categories_needing_more:
            # category.get_descendant_ids() returns [id1, id2, id3, ...]
            descendant_ids = category.get_descendant_ids()
            # Remove the category itself (already queried above)
            all_descendant_ids.update(d for d in descendant_ids if d != category.id)
        
        if all_descendant_ids:
            # Query all descendant listings at once
            descendant_listings = db.session.execute(
                select(Listing)
                .where(Listing.category_id.in_(all_descendant_ids))
                .order_by(Listing.created_at.desc())
                .limit(fetch_limit * len(carousel_categories))
            ).scalars().all()
            
            # Distribute descendant listings to the appropriate categories
            for listing in descendant_listings:
                # Find which carousel category "owns" this descendant listing
                for category in categories_needing_more:
                    if listing.category_id in category.get_descendant_ids():
                        # Add to this category's pool
                        if category.id not in listings_by_category_id:
                            listings_by_category_id[category.id] = []
                        
                        # Only add if not already included from direct query
                        if listing not in listings_by_category_id[category.id]:
                            listings_by_category_id[category.id].append(listing)
                        break
    
    # ===== Build carousel data with per-category randomization =====
    carousel_data = []
    for category in carousel_categories:
        listings_pool = listings_by_category_id.get(category.id, [])
        
        if listings_pool:
            # Shuffle within the pool to get variety
            random.shuffle(listings_pool)
            # Take only the display slots
            displayed_listings = listings_pool[:display_slots]
            
            carousel_data.append({
                "category": category,
                "listings": displayed_listings
            })
    
    return carousel_data
```

**Code Reuse Notes:**
- Uses existing `category.get_descendant_ids()` method - don't reinvent this
- Uses existing `Listing` model and `db.session` - standard Flask-SQLAlchemy
- Python's `random.shuffle()` is the standard library way to randomize
- Groups using dictionaries - simple, clear, Pythonic

#### Step 2: Update `app/routes/listings.py` - Index Route

Find the `index()` function and replace the carousel-building loop:

**Before (lines ~58-103):**
```python
def index():
    any_categories_exist = Category.query.first() is not None
    carousel_categories = get_index_carousel_categories()
    
    items_per_carousel = current_app.config.get("INDEX_CAROUSEL_ITEMS_PER_CATEGORY", 10)
    display_slots = min(items_per_carousel, 5)
    fetch_limit = max(display_slots * 2, items_per_carousel)
    category_carousels = []
    
    for category in carousel_categories:
        # Query 1: direct listings
        direct_listings = (
            Listing.query.filter_by(category_id=category.id)
            .order_by(Listing.created_at.desc())
            .limit(fetch_limit)
            .all()
        )
        
        listings_pool = list(direct_listings)
        
        # Query 2 (conditional): descendant listings
        if len(listings_pool) < fetch_limit:
            descendant_ids = category.get_descendant_ids()
            descendant_ids = [cid for cid in descendant_ids if cid != category.id]
            if descendant_ids:
                needed = fetch_limit - len(listings_pool)
                descendant_listings = (
                    Listing.query.filter(Listing.category_id.in_(descendant_ids))
                    .order_by(Listing.created_at.desc())
                    .limit(max(needed * 2, display_slots))
                    .all()
                )
                listings_pool.extend(descendant_listings)
        
        if listings_pool:
            random.shuffle(listings_pool)
            listings = listings_pool[:display_slots]
            category_carousels.append({"category": category, "listings": listings})
    
    # ... render template ...
```

**After:**
```python
def index():
    # Get categories for carousel display
    carousel_categories = get_index_carousel_categories()
    
    # Removed redundant: Category.query.first() is not None
    # Instead, use carousel data to determine if categories exist
    any_categories_exist = len(carousel_categories) > 0
    
    items_per_carousel = current_app.config.get("INDEX_CAROUSEL_ITEMS_PER_CATEGORY", 10)
    
    # Use new batch helper instead of per-category queries
    from app.routes.utils import get_carousel_listings_batch
    category_carousels = get_carousel_listings_batch(carousel_categories, items_per_carousel)
    
    return render_template(
        "index.html",
        category_carousels=category_carousels,
        any_categories_exist=any_categories_exist,
        page_title="",
    )
```

**Key Changes Explained:**

1. Removed the loop `for category in carousel_categories:` 
   - The loop did individual queries per category
   - Now the helper does all queries at once

2. Removed `Category.query.first()` check
   - It was a separate query just to check if categories exist
   - We can infer from `len(carousel_categories) > 0` instead
   - Saves one query!

3. Call new helper instead of loop
   - `get_carousel_listings_batch()` replaces 6+ queries with 2

#### Step 3: Imports Update

Verify the top of `app/routes/listings.py` includes:
```python
from sqlalchemy import select  # From #55 migration
import random  # Already there, used by shuffle
```

### Testing Checklist for #57

**Code Validation:**
- [ ] Syntax check: `python -m py_compile app/routes/utils.py app/routes/listings.py`
- [ ] App initialization: `python -c "from app import create_app; app = create_app()"`

**Performance Testing:**
- [ ] Create test database with 6+ carousel categories, each with 10+ listings
- [ ] Load index page and monitor database queries
  - [ ] Should see exactly 2 SELECT queries (down from 6+)
  - [ ] Use query logger or Flask debug toolbar to count queries
  
**Functional QA - Carousel Display:**
- [ ] Index page loads without errors ✓
- [ ] All carousel categories display ✓
- [ ] Each carousel shows listings (not empty) ✓
- [ ] Number of listings per carousel matches config ✓
- [ ] Responsive on desktop (shows ~5 items per row) ✓
- [ ] Responsive on mobile ✓

**Functional QA - Randomization:**
- [ ] Reload index page multiple times
- [ ] Listings in carousels should be different each reload ✓
- [ ] Randomization is per-category (different categories still show different items) ✓

**Functional QA - Descendant Fallback:**
- [ ] Create category with NO direct listings
- [ ] Create child categories with listings
- [ ] Index page carousel for parent category shows child listings ✓
- [ ] Works correctly when blending direct + descendant listings ✓

**Functional QA - Edge Cases:**
- [ ] Category with zero listings shows no carousel (doesn't crash) ✓
- [ ] Category with 1 listing displays it ✓
- [ ] Large number of categories (10+) works without slowdown ✓
- [ ] Large number of listings (100+) works correctly ✓

**Query Count Verification (Advanced):**

Add temporary logging to verify query count:

```python
# In app/routes/listings.py, just before the index() function:

from sqlalchemy import event

query_count = 0

@event.listens_for(db.engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    global query_count
    query_count += 1
    print(f"Query {query_count}: {statement[:100]}...")

# Then in index():
def index():
    global query_count
    query_count = 0
    
    # ... existing code ...
    
    print(f"\n===== Index page loaded with {query_count} total queries =====")
    # Expected: ~2-3 for carousel (up from 6+)
    
    return render_template(...)
```

After testing, remove this debug code.

### Commit Message for #57

```
perf(#57): Reduce carousel N+1 queries from 6+ to 2

Optimize index page carousel data loading using batch queries:
- Create get_carousel_listings_batch() helper in utils.py
- Batch-fetch all direct listings in single query (instead of per-category)
- Batch-fetch all descendant listings in single query
- Group results in Python with proper randomization
- Remove redundant Category.query.first() check
- Use len(carousel_categories) > 0 instead

Performance impact:
- Before: 6-12 queries for 6 carousel categories
- After: 2 queries for all carousel categories
- Estimated 3-6x faster carousel load time

Technical approach:
- Reuses Category.get_descendant_ids() (DRY principle)
- Per-category randomization preserved (Python-side shuffle)
- Descendant fallback logic maintained
- No UI/UX changes (user sees identical result)
- Works with modern select() API from #55

Fixes: #57
```

---

## Overall Success Metrics

| Issue | Success Criteria | Target |
|-------|------------------|--------|
| #55 | Codebase converted to select() API | 100% coverage |
| #55 | No `.query` references remain | 0 found |
| #55 | All existing flows work | 100% manual QA pass |
| #50 | Users see form errors before submit | 100% of validation cases |
| #50 | Database cycle protection still active | Still blocks at flush |
| #57 | Carousel queries reduced | 6+ → ≤2 |
| #57 | Randomization still works | Varies on reload |
| #57 | No UI changes | Identical appearance |

---

## Deployment Notes

### Rollback Strategy

If something breaks during deployment:

```bash
# Revert commits (newest first)
git revert <#57-commit-hash>
git revert <#50-commit-hash>
git revert <#55-commit-hash>

# Reinstall original dependencies
pip install -r requirements.txt  # Before changes
```

### Deployment Order

1. Deploy #55 (tech debt)
   - Database queries might be slightly different, but functionality identical
   - Monitor for any unexpected slowdowns

2. Deploy #50 (form validation)
   - Just adds validation, no breaking changes

3. Deploy #57 (performance)
   - Queries are more efficient, should be transparent to users
   - Might see faster page loads

### Monitoring Post-Deployment

- [ ] Check error logs for any exceptions
- [ ] Monitor page load times (should see improvement in #57)
- [ ] Verify form errors display correctly (#50)
- [ ] Check database query patterns (#55 should reduce query variety)

---

## Final Notes

**Key Philosophy:** Do tech debt first (foundations), then build new features on clean code. This saves time and reduces bugs.

**Code Reuse Throughout:**
- #55: Uses existing SQLAlchemy patterns
- #50: Reuses `Category.would_create_cycle()`
- #57: Reuses `Category.get_descendant_ids()` and `random.shuffle()`

**Testing Importance:** Each section has extensive testing checklists. Complete them before moving to the next phase.

**Questions?** Refer back to the problem summaries at the top if any technical decision is unclear.
