# Plan: Add Configurable Category Carousels to Index Page

Replace the current paginated listings grid with up to N Bootstrap carousels. Each carousel displays up to M recent listings from one category using Bootstrap's default responsive carousel behavior with multiple cards visible and prev/next arrows. Categories can be explicitly configured or auto-selected randomly from top 2N by listing count. Empty categories are skipped.

## Steps

1. (DONE) **Add configuration in `app/config.py`**: Add `INDEX_CAROUSEL_COUNT` (default 4), `INDEX_CAROUSEL_ITEMS_PER_CATEGORY` (default 10), and `INDEX_CAROUSEL_CATEGORIES` (default None, list of category IDs when explicitly set).

2. (DONE) **Create utility function in `app/routes/utils.py`**: Add `get_index_carousel_categories()` returning up to N categories with listings—uses explicit category IDs from config if set, otherwise queries top 2N by listing count and randomly selects N; filters out empty categories.

3. (DONE) **Modify `app/routes/listings.py` `index()` function**: Call `get_index_carousel_categories()`; for each category, fetch up to M most recent listings; check if any categories exist (controls "+ Post New Listing" button); pass `category_carousels` to template; remove pagination logic.

4. (DONE) **Update `app/templates/index.html`**: Replace grid and pagination with conditional logic for empty states (no categories → admin message; categories exist but no listings → no listings message); loop rendering Bootstrap carousels with unique `id`, clickable category heading using `url_for('listings.category_filtered_listings', category_path=category.url_path)`, reused card HTML (card-dimensions, image, title, price), and prev/next controls.

5. (DONE) **Add carousel CSS in `app/static/css/styles.css`**: Add spacing between carousels; use Bootstrap's default responsive carousel behavior for card layout; ensure listing cards maintain 192px × 256px dimensions; position carousel controls.

## Key Requirements

- **Configurable**: Number of carousels, items per carousel, and specific categories all configurable with sane defaults
- **Graceful degradation**: "Up to" philosophy—show fewer carousels if fewer categories with listings, fewer items if category has fewer listings
- **Empty states**: 
  - No categories exist → "Contact administrator to add categories"
  - Categories exist but none have listings → "No listings found" with "+ Post New Listing" button
  - No categories → "+ Post New Listing" button hidden
- **Category selection strategy**: 
  - If `INDEX_CAROUSEL_CATEGORIES` explicitly set → use those IDs
  - Otherwise → query top 2N categories by listing count, randomly select N
- **Card layout**: Reuse existing card HTML (192px × 256px, thumbnail with fallback, title, price)
- **Category navigation**: Category heading links to `/listings/<category.url_path>` (category_filtered_listings route)
- **Responsive**: Use Bootstrap's default carousel responsive behavior
- **No pagination**: Remove pagination logic entirely when carousels implemented

## Additional Unplanned Steps (Sprint 1 Leftovers)

### Layout Alignment & Standardization

6. (DONE) **Align navbar with grid**: Remove horizontal padding from navbar and container-fluid; drop brand/toggle margins to eliminate inset; navbar content now aligns with page content width.

7. (DONE) **Standardize content width across pages**: Wrap content in shared `category-row-content` div for consistent width constraints:
   - `listing_detail.html`: Breadcrumb, title, description, images, buttons
   - `listing_form.html`: Form fields; place category dropdown and price side-by-side with responsive grid
   - `user_profile.html`: Add "Your profile" / "User profile" header; wrap content in width container
   - `user_form.html`: Add conditional "Edit profile" / "Edit user" header; place first/last name side-by-side with responsive grid
   - `admin_dashboard.html`: Replace text links with three cards (Manage Users, Categories, Listings) using Bootstrap Icons (bi-people, bi-tags, bi-card-list)
   - `admin_categories.html`: Remove "Parent" column; right-align "Listings" column; wrap in width container
   - `admin_listings.html`: Remove "Price" column; rename "Date Created" to "Date"; right-align Date column; wrap in width container
   - `admin_users.html`: Make "Listings" column sortable with directional arrows; right-align column; wrap in width container

8. (DONE) **Wrap alerts in width container**: Move flash messages inside `category-row-content` in `base.html` so they respect the same width constraints as content.

### Category Browsing Enhancement
9. (DONE) **Add showcases to intermediate categories**: When viewing an intermediate category (one with children), display showcases of child categories instead of a grid. Each showcase shows up to 6 random listings from that child category and its descendants.

10. (DONE) **Handle orphaned listings in intermediate categories**: Add an "Other <category_name>" showcase at the end of intermediate category pages to display listings posted directly to the intermediate category (not in any child).

11. (DONE) **Add grid view toggle for categories**: Support `?view=listings` query parameter to force any category (leaf or intermediate) to display a full grid with pagination. Intermediate categories link to "Other <category>" showcase with this parameter; leaf categories naturally fall through to grid without it.