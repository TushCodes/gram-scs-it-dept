# Pagination, Sorting & Search Implementation for Internal Consignment Database

## Overview
This implementation adds comprehensive pagination, sorting, and search functionality to the internal consignment database interface. Users can now efficiently browse large datasets with real-time filtering and flexible data organization.

## Features Implemented

### 1. **Pagination**
- Load 10, 25, 50, or 100 rows per page
- Navigate between pages with Previous/Next buttons
- Smart page number display with ellipsis (e.g., 1 ... 3 4 5 ... 50)
- Current page highlighting
- Shows record count (e.g., "Showing 1-10 of 150")
- Disabled navigation buttons at boundaries

### 2. **Sorting**
- Click any column header to sort ascending/descending
- Visual indicators: ↑ for ascending, ↓ for descending, ↕ for unsorted
- Sortable columns:
  - ID
  - Consignment Number
  - Status
  - Pickup Pincode
  - Drop Pincode
  - Pickup Tag
  - Drop Tag
  - Pickup Date
  - Drop Date
- Active sort column highlighted in blue

### 3. **Search/Filtering**
- Real-time search with 500ms debounce
- Search across 8 fields:
  - Consignment Number
  - Status
  - Pickup Tag & Drop Tag
  - Pickup Pincode & Drop Pincode
  - Pickup Address & Drop Address
- "Clear Filters" button to reset all settings
- Shows results matching your search criteria

### 4. **Local Row Management**
- **Add Row**: Click "Add Row" button, fill modal, save locally (blue highlight)
- **Edit Row**: Click pencil icon, modify fields, save changes
- **Delete Row**: Click X button to remove row (before or after saving)
- **Save All**: Sends all new/modified/deleted rows to database
- Unsaved changes don't affect pagination/search/sort

## Technical Implementation

### Backend Changes

#### New API Endpoint
**Route**: `/admin/consignments/list` (GET)  
**Authentication**: Requires admin login  
**Parameters**:
```
- page (int): Page number, default 1
- per_page (int): Rows per page, default 10, max 100
- search (str): Search query, searches 8 fields
- sort_by (str): Column to sort by, default "id"
- sort_order (str): "asc" or "desc", default "asc"
```

**Response**:
```json
{
  "success": true,
  "rows": [
    {
      "id": 1,
      "consignment_number": "CON123456",
      "status": "In Transit",
      "pickup_pincode": "110001",
      "pickup_address": "Delhi",
      "pickup_tag": "Office",
      "pickup_date": "2026-05-14",
      "drop_pincode": "400001",
      "drop_address": "Mumbai",
      "drop_tag": "Warehouse",
      "drop_date": "2026-05-16",
      "eta": ""
    }
  ],
  "page": 1,
  "per_page": 10,
  "total": 150,
  "pages": 15,
  "has_prev": false,
  "has_next": true
}
```

**Error Handling**:
- Validates page number ≥ 1
- Limits per_page to 1-100
- Validates sort_by against allowed columns
- Case-insensitive search with ILIKE operator
- Returns 500 error if database schema is missing columns
- Handles database connection errors gracefully

### Frontend Changes

#### HTML Updates
- **Search Input**: Debounced text input for real-time filtering
- **Per-page Selector**: Dropdown with options 10, 25, 50, 100
- **Sortable Headers**: Click to toggle sort order, visual icons
- **Pagination Controls**: 
  - Previous/Next buttons with icons
  - Dynamic page number buttons
  - Pagination info box
- **Loading Indicator**: Shows during data fetch
- **Clear Filters**: Resets all search/sort/page settings

#### CSS Classes
```css
.sort-header         /* Clickable, changes cursor to pointer */
.sort-icon          /* Sort direction indicator */
.sort-icon.active   /* Highlighted when sorted */
.pagination-controls /* Container for pagination UI */
.pagination-info    /* Shows "Showing X-Y of Z" */
.pagination-buttons /* Button group for page navigation */
.page-number        /* Individual page button */
```

### JavaScript Implementation

#### Key Functions
```javascript
loadPage(page, search, perPage, sortBy, sortOrder)
  - Fetches data from API
  - Updates table with new rows
  - Refreshes pagination UI
  - Updates sort indicators

updatePaginationUI()
  - Updates "Showing X-Y of Z" text
  - Enables/disables prev/next buttons
  - Generates page number buttons

updateSortHeaders()
  - Updates sort icons
  - Highlights active sort column
```

#### Event Handlers
- **Search Input**: Debounced input (500ms delay)
- **Per-page Selector**: Immediate page reload
- **Column Headers**: Toggle sort order
- **Pagination Buttons**: Navigate to page
- **Clear Filters**: Reset to defaults
- **Add Row**: Modal for new entry
- **Edit Row**: Modal for modification
- **Delete Row**: Remove from table and mark for deletion
- **Save All**: Send changes to database

#### State Management
```javascript
currentPage        // Current page number
currentPerPage     // Rows per page
currentSearch      // Current search query
currentSortBy      // Sort column
currentSortOrder   // "asc" or "desc"
totalRows          // Total record count
totalPages         // Total pages
deletedIds         // IDs to delete
modifiedRowIds     // IDs that were modified
locallyAddedRows   // Rows added locally
newRowIdCounter    // Auto-incrementing ID for new rows
```

#### Backwards Compatibility
- All existing functionality preserved
- Unsaved changes don't interfere with pagination
- Export/Import/Add/Edit/Delete still work
- Save functionality enhanced to handle pagination context

## Usage Guide

### Basic Operations

**Search for consignments**:
1. Enter search term in "Search" field
2. Table automatically filters to matching records
3. Results show in real-time (500ms delay)

**Sort data**:
1. Click column header
2. First click: sort ascending (↑ icon)
3. Second click: sort descending (↓ icon)
4. Third click: return to original sort

**Change page size**:
1. Select from "Rows per page" dropdown (10, 25, 50, 100)
2. Table reloads with new page size

**Navigate pages**:
1. Click page number or Prev/Next buttons
2. Shows "Showing X-Y of Z" at bottom
3. Current page highlighted

**Add new row**:
1. Click "Add Row" button
2. Fill in consignment details in modal
3. Click "Save" to add locally (row turns blue)
4. Click "Save All" to save to database

**Edit existing row**:
1. Click pencil icon on row
2. Modify fields in modal
3. Click "Save" to update locally
4. Click "Save All" to save to database

**Delete row**:
1. Click X icon on row
2. Row immediately removed
3. Click "Save All" to confirm deletion in database

**Clear all filters**:
1. Click "Clear Filters" button
2. Resets search, page size, and sorting
3. Shows first page with default sort

### Performance Notes
- Large datasets (1000+ rows) load efficiently
- Pagination reduces memory usage
- Search is case-insensitive using ILIKE
- Max 100 rows per page to prevent slowdown
- Debounced search prevents excessive API calls

## Testing Checklist

- [ ] Search filters results correctly across all fields
- [ ] Sorting works ascending/descending for all columns
- [ ] Pagination displays correct rows per page
- [ ] Page navigation works (prev/next and number buttons)
- [ ] Clear filters resets everything
- [ ] Add new row creates entry with blue highlight
- [ ] Edit row updates values correctly
- [ ] Delete row removes from table
- [ ] Save All sends changes to database
- [ ] Loading spinner appears during fetch
- [ ] Error messages display for failures
- [ ] Per-page selector updates immediately
- [ ] Sort icons update to reflect current sort
- [ ] Page info shows correct range and total

## Files Modified

1. **app/admin/consignment_controller.py**
   - Added `consignments_list_api()` endpoint

2. **app/templates/admin/consignments.html**
   - Added search controls
   - Added sortable column headers
   - Added pagination controls
   - Added loading spinner
   - Updated styling for new UI elements

3. **app/static/js/consignments.js**
   - Complete rewrite to support AJAX-based pagination
   - Added `loadPage()` function
   - Added `updatePaginationUI()` function
   - Added event handlers for search, sort, pagination
   - Maintained local editing functionality

## Future Enhancements

- Export filtered/sorted results
- Column visibility toggle
- Advanced filtering (date range, status dropdown)
- Bulk operations (select multiple rows)
- Custom sort order persistence
- Export to CSV with current filters
