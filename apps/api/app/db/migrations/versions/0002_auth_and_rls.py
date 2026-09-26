"""auth and row level security

Revision ID: 0002_auth_and_rls
Revises: 0001_initial_schema
Create Date: 2026-09-26 23:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_auth_and_rls"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Application role for RLS isolation
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'finsight_app') THEN
                CREATE ROLE finsight_app WITH LOGIN PASSWORD 'finsight_secret';
            END IF;
            GRANT ALL PRIVILEGES ON SCHEMA public TO finsight_app;
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finsight_app;
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finsight_app;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO finsight_app;
        END $$;
    """)

    # 1. Add auth columns to users table
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    # 2. Enable Row-Level Security on user-owned tables
    rls_tables = [
        "users",
        "financial_profiles",
        "goals",
        "portfolios",
        "holdings",
        "transactions",
        "research_projects",
        "research_runs",
        "watchlists",
        "notifications",
        "learning_progress",
        "quiz_attempts",
        "audit_logs"
    ]

    for table in rls_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    # 3. Create RLS Isolation Policies
    # Users
    op.execute("""
        CREATE POLICY users_isolation_policy ON users
        FOR ALL
        USING (
            id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Portfolios
    op.execute("""
        CREATE POLICY portfolios_isolation_policy ON portfolios
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Holdings
    op.execute("""
        CREATE POLICY holdings_isolation_policy ON holdings
        FOR ALL
        USING (
            portfolio_id IN (
                SELECT id FROM portfolios 
                WHERE user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            )
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Transactions
    op.execute("""
        CREATE POLICY transactions_isolation_policy ON transactions
        FOR ALL
        USING (
            portfolio_id IN (
                SELECT id FROM portfolios 
                WHERE user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            )
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Financial profiles
    op.execute("""
        CREATE POLICY profiles_isolation_policy ON financial_profiles
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Goals
    op.execute("""
        CREATE POLICY goals_isolation_policy ON goals
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Research projects
    op.execute("""
        CREATE POLICY research_projects_isolation_policy ON research_projects
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Research runs
    op.execute("""
        CREATE POLICY research_runs_isolation_policy ON research_runs
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Watchlists
    op.execute("""
        CREATE POLICY watchlists_isolation_policy ON watchlists
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Notifications
    op.execute("""
        CREATE POLICY notifications_isolation_policy ON notifications
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)

    # Audit logs
    op.execute("""
        CREATE POLICY audit_logs_isolation_policy ON audit_logs
        FOR ALL
        USING (
            user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_admin', true) = 'true'
            OR current_setting('app.bypass_rls', true) = 'true'
        );
    """)


def downgrade() -> None:
    # Drop policies
    policies = [
        ("users_isolation_policy", "users"),
        ("portfolios_isolation_policy", "portfolios"),
        ("holdings_isolation_policy", "holdings"),
        ("transactions_isolation_policy", "transactions"),
        ("profiles_isolation_policy", "financial_profiles"),
        ("goals_isolation_policy", "goals"),
        ("research_projects_isolation_policy", "research_projects"),
        ("research_runs_isolation_policy", "research_runs"),
        ("watchlists_isolation_policy", "watchlists"),
        ("notifications_isolation_policy", "notifications"),
        ("audit_logs_isolation_policy", "audit_logs"),
    ]

    for policy_name, table in policies:
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # Drop columns
    op.drop_column("users", "email_verified")
    op.drop_column("users", "is_active")
    op.drop_column("users", "hashed_password")
