# PostgreSQL Performance Optimizations

This document describes the performance optimizations implemented to speed up database operations after migrating from SQLite to PostgreSQL.

## Changes Made

### 1. Connection Pooling ✓
**File:** `backend/db.py`

- **Problem:** Opening a new PostgreSQL connection on every request added significant latency (TCP handshake, TLS negotiation, authentication).
- **Solution:** Implemented `psycopg_pool.ConnectionPool` with:
  - Min pool size: 2 connections (always ready)
  - Max pool size: 10 connections (handles concurrent requests)
  - 5-second timeout for acquiring connections
  - Singleton pattern to reuse the pool across all requests

**Expected Impact:** Reduces connection overhead from ~50-200ms to <1ms per request.

### 2. Schema Caching ✓
**File:** `backend/db.py`

- **Problem:** Every request that called `list_columns()` queried `information_schema.columns`, adding 10-50ms overhead.
- **Solution:** Added in-memory cache for table schemas:
  - Cache key: `{database_type}:{table_name}`
  - First call queries the database, subsequent calls use cache
  - `clear_schema_cache()` function available for migrations
  - Optional `use_cache=False` parameter to force refresh

**Expected Impact:** Eliminates repeated schema queries, saving 10-50ms per request.

### 3. Database Indexes ✓
**File:** `backend/db_migrations.py`

Created indexes for common query patterns:

#### Workflows Table
- `idx_workflows_created_at` - Speeds up `ORDER BY created_at DESC`
- `idx_workflows_name` - Speeds up `WHERE name LIKE 'Untitled %'`

#### Deployments Table
- `idx_deployments_workflow_id` - Speeds up `WHERE workflow_id = ?`
- `idx_deployments_created_at` - Speeds up `ORDER BY created_at DESC`
- `idx_deployments_is_active` - Speeds up `WHERE is_active = ?`

#### Deployment Logs Table
- `idx_deployment_logs_deployment_created` - Composite index for filtering and sorting
- `idx_deployment_logs_created_at` - Speeds up time-based queries

**Expected Impact:** Converts full table scans to index lookups, reducing query time from O(n) to O(log n).

### 4. Optimized Log Pruning ✓
**File:** `backend/api/v1/deployments.py`

- **Problem:** Every deployment invocation ran a heavy `DELETE ... NOT IN (SELECT ...)` query.
- **Solution:** 
  - Prune only 10% of the time (probabilistic pruning)
  - Use more efficient PostgreSQL query with `OFFSET` instead of `NOT IN`
  - Relies on the new index for fast execution

**Expected Impact:** Reduces invocation overhead by ~90%, only pruning occasionally.

## Installation

1. **Install new dependency:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
   This will install `psycopg-pool` which is now required.

2. **Apply indexes:**
   The indexes are automatically created on server startup. Alternatively, run manually:
   ```bash
   cd backend
   python db_migrations.py
   ```

## Usage

### Normal Operation
No code changes needed! All optimizations are transparent:
- Connection pooling happens automatically
- Schema caching happens automatically
- Indexes are used automatically by PostgreSQL query planner

### Manual Index Creation
If you need to create indexes manually:
```python
from db_migrations import create_performance_indexes
create_performance_indexes()
```

### Clear Schema Cache (After Migrations)
If you add/remove columns and need to refresh the cache:
```python
from db import clear_schema_cache

# Clear specific table
clear_schema_cache("workflows")

# Clear all tables
clear_schema_cache()
```

### Force Schema Refresh
```python
from db import list_columns, get_connection

with get_connection() as conn:
    # Force refresh (bypass cache)
    columns = list_columns(conn, "workflows", use_cache=False)
```

## Performance Expectations

### Before Optimization
- List workflows: ~200-500ms
- Get deployment: ~150-300ms
- Create deployment: ~300-600ms
- Invoke deployment: ~200-400ms

### After Optimization
- List workflows: ~10-50ms (5-10x faster)
- Get deployment: ~5-20ms (10-30x faster)
- Create deployment: ~20-80ms (5-15x faster)
- Invoke deployment: ~10-50ms (5-20x faster)

*Actual times depend on network latency to PostgreSQL server, query complexity, and data volume.*

## Monitoring

### Check Pool Status
```python
from db import _postgres_pool

if _postgres_pool:
    print(f"Pool size: {_postgres_pool.get_stats()}")
```

### Verify Indexes
```sql
-- PostgreSQL
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename IN ('workflows', 'deployments', 'deployment_logs');

-- SQLite
SELECT name, sql FROM sqlite_master 
WHERE type = 'index' 
AND tbl_name IN ('workflows', 'deployments', 'deployment_logs');
```

### Query Performance
```sql
-- PostgreSQL: Check if indexes are being used
EXPLAIN ANALYZE SELECT * FROM workflows ORDER BY created_at DESC;

-- Look for "Index Scan" instead of "Seq Scan"
```

## Troubleshooting

### Connection Pool Exhausted
If you see timeout errors:
1. Increase `max_size` in `db.py` (currently 10)
2. Check for connection leaks (ensure all `with get_connection()` blocks complete)

### Schema Cache Stale
If you see wrong columns after migration:
```python
from db import clear_schema_cache
clear_schema_cache()
```

### Indexes Not Used
1. Verify indexes exist: `\d+ workflows` in psql
2. Run `ANALYZE` to update statistics: `ANALYZE workflows;`
3. Check query plan: `EXPLAIN ANALYZE your_query;`

## Rollback

If you need to revert to the old behavior:

1. **Disable connection pooling:**
   ```python
   # In db.py, replace get_connection() with:
   if USING_POSTGRES:
       conn = psycopg.connect(POSTGRES_URL, row_factory=dict_row, autocommit=True)
       try:
           yield conn
       finally:
           conn.close()
   ```

2. **Disable schema caching:**
   ```python
   # In db.py, set use_cache=False by default
   def list_columns(conn, table_name, use_cache=False):
   ```

3. **Drop indexes (not recommended):**
   ```sql
   DROP INDEX IF EXISTS idx_workflows_created_at;
   -- etc.
   ```

## Future Improvements

1. **Read Replicas:** For read-heavy workloads, route SELECT queries to replicas
2. **Query Result Caching:** Cache frequently accessed workflows/deployments
3. **Async Connection Pool:** Use `AsyncConnectionPool` with async FastAPI endpoints
4. **Prepared Statements:** Pre-compile frequently used queries
5. **Batch Operations:** Bulk insert/update for multiple records

## Notes

- All optimizations are backward compatible with SQLite
- Connection pool is only used for PostgreSQL (SQLite uses simple connections)
- Indexes work for both PostgreSQL and SQLite
- Schema cache works for both database types

