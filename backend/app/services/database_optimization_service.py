"""
Database optimization service for query optimization and performance monitoring
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import engine
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseOptimizationService:
    """Service for database optimization and performance monitoring"""
    
    @staticmethod
    async def create_missing_indexes(session: AsyncSession) -> Dict[str, Any]:
        """Create additional performance indexes if they don't exist"""
        
        indexes_created = []
        errors = []
        
        # Additional indexes for better query performance
        additional_indexes = [
            # Composite indexes for common query patterns
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_match_results_job_score_created "
            "ON match_results (job_id, match_score DESC, created_at DESC)",
            
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resumes_processed_uploaded "
            "ON resumes (is_processed, uploaded_at DESC) WHERE is_processed = 'true'",
            
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_active_created "
            "ON job_descriptions (is_active, created_at DESC) WHERE is_active = 'true'",
            
            # Partial indexes for better performance on filtered queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_match_results_high_score "
            "ON match_results (job_id, resume_id, match_score DESC) WHERE match_score >= 70.0",
            
            # Text search indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_title_gin "
            "ON job_descriptions USING gin(to_tsvector('english', title))",
            
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resumes_content_gin "
            "ON resumes USING gin(to_tsvector('english', content))",
            
            # Array indexes for skills
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_skills_gin "
            "ON job_descriptions USING gin(skills_required)",
            
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_resumes_skills_gin "
            "ON resumes USING gin(extracted_skills)",
        ]
        
        for index_sql in additional_indexes:
            try:
                await session.execute(text(index_sql))
                await session.commit()
                index_name = index_sql.split("IF NOT EXISTS ")[1].split(" ")[0]
                indexes_created.append(index_name)
                logger.info(f"Created index: {index_name}")
            except Exception as e:
                error_msg = f"Failed to create index: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
                await session.rollback()
        
        return {
            "indexes_created": indexes_created,
            "errors": errors,
            "total_created": len(indexes_created)
        }
    
    @staticmethod
    async def analyze_tables(session: AsyncSession) -> Dict[str, Any]:
        """Run ANALYZE on all tables to update statistics"""
        
        tables = ["users", "job_descriptions", "resumes", "match_results"]
        analyzed_tables = []
        errors = []
        
        for table in tables:
            try:
                await session.execute(text(f"ANALYZE {table}"))
                analyzed_tables.append(table)
                logger.info(f"Analyzed table: {table}")
            except Exception as e:
                error_msg = f"Failed to analyze table {table}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        await session.commit()
        
        return {
            "analyzed_tables": analyzed_tables,
            "errors": errors,
            "total_analyzed": len(analyzed_tables)
        }
    
    @staticmethod
    async def get_query_performance_stats(session: AsyncSession) -> Dict[str, Any]:
        """Get query performance statistics"""
        
        try:
            # Get slow queries
            slow_queries_sql = """
            SELECT query, calls, total_time, mean_time, rows
            FROM pg_stat_statements 
            WHERE mean_time > 100 
            ORDER BY mean_time DESC 
            LIMIT 10
            """
            
            # Get table statistics
            table_stats_sql = """
            SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, 
                   n_live_tup, n_dead_tup, last_vacuum, last_autovacuum, last_analyze
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
            """
            
            # Get index usage
            index_usage_sql = """
            SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_tup_read DESC
            LIMIT 20
            """
            
            stats = {}
            
            try:
                result = await session.execute(text(slow_queries_sql))
                stats["slow_queries"] = [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                stats["slow_queries"] = f"Error: {str(e)}"
            
            try:
                result = await session.execute(text(table_stats_sql))
                stats["table_stats"] = [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                stats["table_stats"] = f"Error: {str(e)}"
            
            try:
                result = await session.execute(text(index_usage_sql))
                stats["index_usage"] = [dict(row._mapping) for row in result.fetchall()]
            except Exception as e:
                stats["index_usage"] = f"Error: {str(e)}"
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def optimize_database_settings(session: AsyncSession) -> Dict[str, Any]:
        """Apply database optimization settings"""
        
        optimizations = []
        errors = []
        
        # Database optimization settings
        optimization_queries = [
            # Increase work memory for complex queries
            "SET work_mem = '256MB'",
            
            # Optimize for read-heavy workload
            "SET random_page_cost = 1.1",
            
            # Increase effective cache size
            "SET effective_cache_size = '2GB'",
            
            # Optimize checkpoint settings
            "SET checkpoint_completion_target = 0.9",
            
            # Enable parallel query execution
            "SET max_parallel_workers_per_gather = 4",
            
            # Optimize vacuum settings
            "SET autovacuum_vacuum_scale_factor = 0.1",
            "SET autovacuum_analyze_scale_factor = 0.05",
        ]
        
        for query in optimization_queries:
            try:
                await session.execute(text(query))
                optimizations.append(query)
                logger.info(f"Applied optimization: {query}")
            except Exception as e:
                error_msg = f"Failed to apply optimization '{query}': {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return {
            "optimizations_applied": optimizations,
            "errors": errors,
            "total_applied": len(optimizations)
        }
    
    @staticmethod
    async def vacuum_analyze_tables(session: AsyncSession) -> Dict[str, Any]:
        """Run VACUUM ANALYZE on all tables"""
        
        tables = ["users", "job_descriptions", "resumes", "match_results"]
        processed_tables = []
        errors = []
        
        for table in tables:
            try:
                # Use VACUUM ANALYZE for better performance
                await session.execute(text(f"VACUUM ANALYZE {table}"))
                processed_tables.append(table)
                logger.info(f"Vacuumed and analyzed table: {table}")
            except Exception as e:
                error_msg = f"Failed to vacuum table {table}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
        
        return {
            "processed_tables": processed_tables,
            "errors": errors,
            "total_processed": len(processed_tables)
        }
    
    @staticmethod
    async def get_database_size_info(session: AsyncSession) -> Dict[str, Any]:
        """Get database size information"""
        
        try:
            # Get database size
            db_size_sql = "SELECT pg_size_pretty(pg_database_size(current_database())) as database_size"
            
            # Get table sizes
            table_sizes_sql = """
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            
            # Get index sizes
            index_sizes_sql = """
            SELECT 
                indexname,
                pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size,
                pg_relation_size(schemaname||'.'||indexname) as size_bytes
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC
            LIMIT 10
            """
            
            result = await session.execute(text(db_size_sql))
            database_size = result.fetchone()[0]
            
            result = await session.execute(text(table_sizes_sql))
            table_sizes = [dict(row._mapping) for row in result.fetchall()]
            
            result = await session.execute(text(index_sizes_sql))
            index_sizes = [dict(row._mapping) for row in result.fetchall()]
            
            return {
                "database_size": database_size,
                "table_sizes": table_sizes,
                "index_sizes": index_sizes
            }
            
        except Exception as e:
            logger.error(f"Failed to get database size info: {e}")
            return {"error": str(e)}


# Global optimization service instance
db_optimization_service = DatabaseOptimizationService()