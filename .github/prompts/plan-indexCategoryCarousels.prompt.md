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
