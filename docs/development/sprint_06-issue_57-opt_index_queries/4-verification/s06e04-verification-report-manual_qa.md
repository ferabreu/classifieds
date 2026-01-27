## Manual QA Checklist

### Browser-Based Verification

**Visual Inspection:**
1. Start development server: `flask run`
2. Open browser to `http://localhost:5000/`
3. Inspect each showcase:
   - [✓] Showcase title displays category name
   - [✓] "See all" link is present and correctly formatted
   - [✓] Listing cards render with thumbnail, title, price
   - [✓] No broken images or missing data
4. Check page layout:
   - [✓] No layout shifts or rendering issues
   - [✓] Showcases are properly spaced
   - [✓] Overall page aesthetics unchanged

**Randomization Testing:**
1. Refresh page (F5 or Cmd+R)
2. Note order of listings in first showcase
3. Refresh 4 more times
4. Verify:
   - [✓] Listing order changes between refreshes
   - [✓] Different categories show different random selections
   - [✓] All refreshes complete successfully (no errors)

**Descendant Fallback Testing:**
1. Identify category with no direct listings (check admin panel or database)
2. Verify that category has child categories with listings
3. Load index page
4. Check that category's showcase:
   - [✓] Displays listings (from descendants)
   - [✓] Shows correct listing cards
   - [✓] "See all" link works

**Responsive Behavior:**
1. Desktop (1920x1080):
   - [✓] Showcases display multiple cards per row
   - [✓] Layout is clean and properly aligned
2. Tablet (768x1024):
   - [✓] Showcases adapt to narrower width
   - [✓] Cards redistribute appropriately
   - [✓] No horizontal scroll
3. Mobile (375x667):
   - [!] Showcases display single or stacked cards
   - [!] Touch scrolling works if showcase has horizontal scroll
   - [!] Text remains readable

**Navigation Verification:**
1. Click "See all" link for each showcase category
2. Verify:
   - [✓] Navigates to correct category page
   - [✓] Category page displays all listings for that category
   - [✓] Breadcrumb shows correct path
   - [✓] Back button returns to index page

### Results

1. Problems detected with responsive behavior on mobile screens.
   - Thumbnails are too small
   - Will address in separate issue
   - Not really about the problem solved by this sprint
