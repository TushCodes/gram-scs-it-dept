# Consignment Pagination API Documentation

## Endpoint Overview

**Base URL**: `/admin/consignments/list`  
**Method**: GET  
**Authentication**: Required (admin login)  
**Response Format**: JSON

## Request Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `page` | integer | 1 | 1-N | Page number |
| `per_page` | integer | 10 | 1-100 | Rows per page |
| `search` | string | "" | - | Search query (searches 8 fields) |
| `sort_by` | string | "id" | See allowed columns | Column to sort by |
| `sort_order` | string | "asc" | "asc", "desc" | Sort direction |

## Allowed Sort Columns

```
id
consignment_number
status
pickup_pincode
drop_pincode
pickup_tag
drop_tag
pickup_date
drop_date
```

## Searchable Fields

The search query searches across these fields using case-insensitive LIKE matching:
- `consignment_number`
- `status`
- `pickup_tag`
- `drop_tag`
- `pickup_pincode`
- `drop_pincode`
- `pickup_address`
- `drop_address`

## Example Requests

### 1. Get first page with defaults
```
GET /admin/consignments/list
```

### 2. Get second page with 25 rows
```
GET /admin/consignments/list?page=2&per_page=25
```

### 3. Search for consignments
```
GET /admin/consignments/list?search=CON123&page=1&per_page=10
```

### 4. Sort by status descending
```
GET /admin/consignments/list?sort_by=status&sort_order=desc
```

### 5. Complex query: search, filter, sort, paginate
```
GET /admin/consignments/list?page=3&per_page=50&search=In%20Transit&sort_by=pickup_date&sort_order=asc
```

## Example Responses

### Success Response

```json
{
  "success": true,
  "rows": [
    {
      "id": 1,
      "consignment_number": "CON-2026-001",
      "status": "In Transit",
      "pickup_pincode": "110001",
      "pickup_address": "Plot 123, Delhi Office, New Delhi",
      "pickup_tag": "Main Office",
      "pickup_date": "2026-05-10",
      "drop_pincode": "400001",
      "drop_address": "Warehouse A, Mumbai",
      "drop_tag": "Warehouse",
      "drop_date": "2026-05-15",
      "eta": ""
    },
    {
      "id": 2,
      "consignment_number": "CON-2026-002",
      "status": "Delivered",
      "pickup_pincode": "560001",
      "pickup_address": "Bangalore Office",
      "pickup_tag": "Branch",
      "pickup_date": "2026-05-11",
      "drop_pincode": "700001",
      "drop_address": "Kolkata Hub",
      "drop_tag": "Distribution",
      "drop_date": "2026-05-14",
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

### Empty Results

```json
{
  "success": true,
  "rows": [],
  "page": 1,
  "per_page": 10,
  "total": 0,
  "pages": 0,
  "has_prev": false,
  "has_next": false
}
```

### Error Response - Invalid Parameter

```json
{
  "success": false,
  "error": "Database schema needs an update. Missing consignment fields."
}
```

HTTP Status: 500

### Error Response - Database Connection

```json
{
  "success": false,
  "error": "Database connection error. Please try again."
}
```

HTTP Status: 500

## Pagination Examples

### First Page
```
GET /admin/consignments/list?page=1&per_page=10

Response:
{
  "page": 1,
  "per_page": 10,
  "total": 150,
  "pages": 15,
  "has_prev": false,
  "has_next": true,
  "rows": [rows 1-10]
}
```

### Middle Page
```
GET /admin/consignments/list?page=5&per_page=10

Response:
{
  "page": 5,
  "per_page": 10,
  "total": 150,
  "pages": 15,
  "has_prev": true,
  "has_next": true,
  "rows": [rows 41-50]
}
```

### Last Page
```
GET /admin/consignments/list?page=15&per_page=10

Response:
{
  "page": 15,
  "per_page": 10,
  "total": 150,
  "pages": 15,
  "has_prev": true,
  "has_next": false,
  "rows": [rows 141-150]
}
```

## Sorting Examples

### Sort by Consignment Number (Ascending)
```
GET /admin/consignments/list?sort_by=consignment_number&sort_order=asc
```

### Sort by Status (Descending)
```
GET /admin/consignments/list?sort_by=status&sort_order=desc
```

### Sort by Date (Most Recent First)
```
GET /admin/consignments/list?sort_by=pickup_date&sort_order=desc
```

## Search Examples

### Search for "In Transit"
```
GET /admin/consignments/list?search=In%20Transit
```

Returns all rows where any searchable field contains "In Transit"

### Search for pincode "110001"
```
GET /admin/consignments/list?search=110001
```

Returns all rows where pickup or drop pincode is 110001

### Search for consignment number prefix
```
GET /admin/consignments/list?search=CON-2026
```

Returns all rows with consignment number starting with "CON-2026"

## JavaScript Usage

### Fetch with Vanilla JavaScript

```javascript
// Get first page
fetch('/admin/consignments/list')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log(data.rows);
      console.log(`Page ${data.page} of ${data.pages}`);
    }
  });

// With parameters
const params = new URLSearchParams({
  page: 2,
  per_page: 25,
  search: 'In Transit',
  sort_by: 'pickup_date',
  sort_order: 'desc'
});

fetch('/admin/consignments/list?' + params.toString())
  .then(response => response.json())
  .then(data => console.log(data));
```

### jQuery Usage

```javascript
$.ajax({
  url: '/admin/consignments/list',
  method: 'GET',
  data: {
    page: 1,
    per_page: 10,
    search: 'test',
    sort_by: 'status',
    sort_order: 'asc'
  },
  success: function(data) {
    if (data.success) {
      console.log('Rows:', data.rows);
      console.log(`Showing ${data.total} total records`);
    }
  },
  error: function(error) {
    console.error('Error:', error);
  }
});
```

## Response Metadata

- **page**: Current page number (1-indexed)
- **per_page**: Number of rows returned on this page
- **total**: Total number of records matching search/filter
- **pages**: Total number of pages available
- **has_prev**: Boolean indicating if previous page exists
- **has_next**: Boolean indicating if next page exists
- **rows**: Array of consignment objects

## Field Descriptions

Each row in the response contains:

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier |
| consignment_number | string | Consignment number (max 16 chars) |
| status | string | Current status |
| pickup_pincode | string | Pickup location postal code |
| pickup_address | string | Pickup location address |
| pickup_tag | string | Pickup location tag/name |
| pickup_date | string | Scheduled pickup date |
| drop_pincode | string | Drop location postal code |
| drop_address | string | Drop location address |
| drop_tag | string | Drop location tag/name |
| drop_date | string | Scheduled drop date |
| eta | string | Estimated time of arrival |

## HTTP Status Codes

- **200**: Success (even if no results)
- **401**: Unauthorized (not logged in as admin)
- **500**: Server error (database issue, schema mismatch)

## Error Handling

Always check `data.success` in responses:

```javascript
fetch('/admin/consignments/list')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Process data.rows
    } else {
      // Handle error: data.error
      console.error('Error:', data.error);
    }
  });
```

## Rate Limiting

- No explicit rate limit on this endpoint
- May be subject to general admin endpoint rate limits
- Recommended: Implement client-side debouncing for search (500ms)

## Performance Tips

1. Use reasonable `per_page` values (10-50 for most cases)
2. Limit `search` query length to prevent heavy DB scans
3. Use specific `sort_by` columns that have indexes
4. Implement debouncing for rapid search/filter changes
5. Consider caching results if appropriate for your use case
