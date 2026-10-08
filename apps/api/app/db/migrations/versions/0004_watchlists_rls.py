"""watchlists rls and idempotency

Revision ID: 0004_watchlists_rls
Revises: 0003_learning_rls_and_seed
Create Date: 2026-10-08 22:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_watchlists_rls"
down_revision: Union[str, None] = "0003_learning_rls_and_seed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add idempotency_key to watchlist_scans
    op.add_column("watchlist_scans", sa.Column("idempotency_key", sa.String(120), nullable=True))
    op.create_index("ix_watchlist_scans_idempotency_key", "watchlist_scans", ["idempotency_key"], unique=True)

    # 2. Enable RLS on watchlist_items and watchlist_scans (§11, §30)
    for table in ["watchlist_items", "watchlist_scans"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

    # 3. Create RLS Isolation Policies
    op.execute("""
        CREATE POLICY watchlist_items_isolation_policy ON watchlist_items
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM watchlists
                WHERE watchlists.id = watchlist_items.watchlist_id
                AND (
                    watchlists.user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                    OR current_setting('app.is_admin', true) = 'true'
                    OR current_setting('app.bypass_rls', true) = 'true'
                )
            )
        );
    """)

    op.execute("""
        CREATE POLICY watchlist_scans_isolation_policy ON watchlist_scans
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM watchlists
                WHERE watchlists.id = watchlist_scans.watchlist_id
                AND (
                    watchlists.user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                    OR current_setting('app.is_admin', true) = 'true'
                    OR current_setting('app.bypass_rls', true) = 'true'
                )
            )
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS watchlist_scans_isolation_policy ON watchlist_scans;")
    op.execute("ALTER TABLE watchlist_scans NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE watchlist_scans DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS watchlist_items_isolation_policy ON watchlist_items;")
    op.execute("ALTER TABLE watchlist_items NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE watchlist_items DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_watchlist_scans_idempotency_key", table_name="watchlist_scans")
    op.drop_column("watchlist_scans", "idempotency_key")
