"""add_chart_statistics_views

Revision ID: 47a333c34455
Revises: d01bbe3fe057
Create Date: 2025-12-14 18:37:20.142665

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47a333c34455'
down_revision: Union[str, None] = 'd01bbe3fe057'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW rents_by_status_view AS
        SELECT 
            rs.id AS status_id,
            rs.name AS status_name,
            COUNT(r.id) AS rent_count,
            COALESCE(SUM(r.rent_price), 0) AS total_revenue
        FROM rent_status rs
        LEFT JOIN rent r ON r.status_id = rs.id
        GROUP BY rs.id, rs.name
        ORDER BY rent_count DESC;
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW books_by_library_view AS
        SELECT 
            l.id AS library_id,
            l.name AS library_name,
            c.name AS city_name,
            COUNT(b.id) AS book_count
        FROM library l
        LEFT JOIN city c ON l.city_id = c.id
        LEFT JOIN book b ON b.library_id = l.id
        GROUP BY l.id, l.name, c.name
        ORDER BY book_count DESC;
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW readers_by_category_view AS
        SELECT 
            rc.id AS category_id,
            rc.name AS category_name,
            COUNT(rd.id) AS reader_count
        FROM reader_category rc
        LEFT JOIN reader rd ON rd.reader_category_id = rc.id
        GROUP BY rc.id, rc.name
        ORDER BY reader_count DESC;
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW rents_by_library_view AS
        SELECT 
            l.id AS library_id,
            l.name AS library_name,
            c.name AS city_name,
            rs.id AS status_id,
            rs.name AS status_name,
            COUNT(r.id) AS rent_count
        FROM library l
        LEFT JOIN city c ON l.city_id = c.id
        LEFT JOIN book b ON b.library_id = l.id
        LEFT JOIN rent r ON r.book_id = b.id
        LEFT JOIN rent_status rs ON r.status_id = rs.id
        GROUP BY l.id, l.name, c.name, rs.id, rs.name
        ORDER BY l.name, rent_count DESC;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS rents_by_status_view;")
    op.execute("DROP VIEW IF EXISTS books_by_library_view;")
    op.execute("DROP VIEW IF EXISTS readers_by_category_view;")
    op.execute("DROP VIEW IF EXISTS rents_by_library_view;")
