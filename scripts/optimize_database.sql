-- Database optimization script for Deal Scout
-- Run this in production environment to optimize queries and storage

-- ============================================================================
-- INDEXES FOR HIGH-FREQUENCY QUERIES
-- ============================================================================

-- Listings table indexes
CREATE INDEX IF NOT EXISTS idx_listings_source_id
    ON listings(source, source_id)
    WHERE available = true;

CREATE INDEX IF NOT EXISTS idx_listings_created_at
    ON listings(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_listings_category_price
    ON listings(category, price)
    WHERE available = true;

CREATE INDEX IF NOT EXISTS idx_listings_location
    ON listings USING GIST(location);

-- Listing scores indexes
CREATE INDEX IF NOT EXISTS idx_listing_scores_deal_score
    ON listing_scores(metric, value DESC)
    WHERE metric = 'deal_score';

CREATE INDEX IF NOT EXISTS idx_listing_scores_created_at
    ON listing_scores(created_at DESC);

-- Comparables indexes
CREATE INDEX IF NOT EXISTS idx_comps_category_condition
    ON comps(category, condition, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_comps_price_range
    ON comps(price)
    WHERE price > 0;

-- Notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_status_created
    ON notifications(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_listing
    ON notifications(listing_id, sent_at DESC);

-- User preferences indexes
CREATE INDEX IF NOT EXISTS idx_user_prefs_user_id
    ON user_prefs(user_id);

-- Cross posts indexes
CREATE INDEX IF NOT EXISTS idx_cross_posts_status
    ON cross_posts(status, created_at DESC);

-- Snap jobs indexes
CREATE INDEX IF NOT EXISTS idx_snap_jobs_status
    ON snap_jobs(status, created_at DESC);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- These should already exist but verify
ALTER TABLE listing_scores ADD CONSTRAINT fk_listing_scores_listing
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE notifications ADD CONSTRAINT fk_notifications_listing
    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE cross_posts ADD CONSTRAINT fk_cross_posts_my_item
    FOREIGN KEY (my_item_id) REFERENCES my_items(id) ON DELETE CASCADE
    DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE orders ADD CONSTRAINT fk_orders_cross_post
    FOREIGN KEY (cross_post_id) REFERENCES cross_posts(id) ON DELETE CASCADE
    DEFERRABLE INITIALLY DEFERRED;

-- ============================================================================
-- TABLE PARTITIONING (Optional for very large tables)
-- ============================================================================

-- Partition listings by source for better performance with high volume
-- CREATE TABLE listings_craigslist PARTITION OF listings
--     FOR VALUES IN ('craigslist');
-- CREATE TABLE listings_ebay PARTITION OF listings
--     FOR VALUES IN ('ebay');
-- etc...

-- ============================================================================
-- STATISTICS & VACUUMING
-- ============================================================================

-- Analyze all tables to update query planner statistics
ANALYZE;

-- Vacuum all tables to reclaim space
VACUUM ANALYZE;

-- ============================================================================
-- PERFORMANCE CONFIGURATION
-- ============================================================================

-- Increase work_mem for complex queries (if not already set)
-- SET work_mem = '256MB';

-- Configure connection pool
-- max_connections should be set in postgresql.conf
-- ALTER SYSTEM SET max_connections = 200;

-- Configure autovacuum for aggressive cleanup
ALTER TABLE listings SET (autovacuum_vacuum_scale_factor = 0.05);
ALTER TABLE listing_scores SET (autovacuum_vacuum_scale_factor = 0.05);
ALTER TABLE notifications SET (autovacuum_vacuum_scale_factor = 0.05);

-- ============================================================================
-- SLOW QUERY LOGGING
-- ============================================================================

-- Enable slow query logging (if not already enabled)
-- ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
-- ALTER SYSTEM SET log_statement = 'all';
-- SELECT pg_reload_conf();

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if all indexes were created successfully
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index sizes
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check for missing indexes (common query patterns without indexes)
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1
ORDER BY abs(correlation), n_distinct DESC;

-- Check autovacuum status
SELECT
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY last_autovacuum DESC;

-- ============================================================================
-- MAINTENANCE TASKS
-- ============================================================================

-- To be run periodically (daily/weekly):

-- Full reindex (maintenance window only, locks tables)
-- REINDEX DATABASE deal_scout;

-- Remove dead tuples (use vacuum full sparingly)
-- VACUUM FULL ANALYZE;

-- Identify bloated tables
SELECT
    schemaname,
    tablename,
    round(100 * (pg_relation_size(schemaname||'.'||tablename) -
        pg_relation_size(schemaname||'.'||tablename, 'main')) /
        pg_relation_size(schemaname||'.'||tablename)) AS waste_ratio
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY waste_ratio DESC;

-- ============================================================================
-- MONITORING QUERIES
-- ============================================================================

-- Current active queries
SELECT
    pid,
    usename,
    query_start,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;

-- Long-running transactions
SELECT
    pid,
    now() - xact_start AS duration,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY duration DESC;

-- Sequence of locks
SELECT
    t.schemaname,
    t.tablename,
    l.locktype,
    l.mode,
    l.granted
FROM pg_locks l
JOIN pg_tables t ON l.relation = t.tableid
ORDER BY t.tablename, l.mode;
