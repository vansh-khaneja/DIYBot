"""Database migration utilities for creating indexes and optimizing queries."""

from __future__ import annotations

from db import get_connection, USING_POSTGRES


def create_performance_indexes() -> None:
    """Create indexes to speed up common query patterns.
    
    This should be run once after switching to Postgres or when setting up a new database.
    It's safe to run multiple times as it uses IF NOT EXISTS.
    """
    with get_connection() as conn:
        if USING_POSTGRES:
            # Workflows table indexes
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflows_created_at 
                ON workflows (created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflows_name 
                ON workflows (name)
                """
            )
            
            # Deployments table indexes
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployments_workflow_id 
                ON deployments (workflow_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployments_created_at 
                ON deployments (created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployments_is_active 
                ON deployments (is_active)
                """
            )
            
            # Deployment logs indexes (composite for efficient filtering and sorting)
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployment_logs_deployment_created 
                ON deployment_logs (deployment_id, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployment_logs_created_at 
                ON deployment_logs (created_at DESC)
                """
            )
            
            print("✓ PostgreSQL indexes created successfully")
        else:
            # SQLite indexes
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflows_created_at 
                ON workflows (created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_workflows_name 
                ON workflows (name)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployments_workflow_id 
                ON deployments (workflow_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployments_created_at 
                ON deployments (created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployments_is_active 
                ON deployments (is_active)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployment_logs_deployment_created 
                ON deployment_logs (deployment_id, created_at DESC)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_deployment_logs_created_at 
                ON deployment_logs (created_at DESC)
                """
            )
            conn.commit()
            print("✓ SQLite indexes created successfully")


if __name__ == "__main__":
    print("Creating performance indexes...")
    create_performance_indexes()
    print("Done!")

