"""fix_overdue_rents_logic_in_views

Revision ID: d01bbe3fe057
Revises: 0a4fefe7d6f7
Create Date: 2025-12-14 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd01bbe3fe057'
down_revision: Union[str, None] = '0a4fefe7d6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW library_statistics_view AS
        SELECT 
            l.id AS library_id,
            l.name AS library_name,
            l.city_id,
            c.name AS city_name,
            COUNT(DISTINCT b.id) AS total_books,
            COUNT(DISTINCT r.id) AS total_rents,
            COUNT(DISTINCT CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_rents,
            COUNT(DISTINCT CASE WHEN r.return_date IS NULL AND DATE(r.expected_return_date) < CURRENT_DATE AND rs.name IN ('active', 'issued', 'overdue') THEN r.id END) AS overdue_rents,
            COUNT(DISTINCT CASE WHEN r.return_date IS NOT NULL THEN r.id END) AS returned_rents,
            COALESCE(SUM(r.rent_price), 0) AS total_revenue,
            COALESCE(SUM(CASE WHEN r.return_date IS NOT NULL THEN r.rent_price ELSE 0 END), 0) AS confirmed_revenue,
            COALESCE(SUM(p.amount), 0) AS total_penalties
        FROM library l
        LEFT JOIN city c ON l.city_id = c.id
        LEFT JOIN book b ON b.library_id = l.id
        LEFT JOIN rent r ON r.book_id = b.id
        LEFT JOIN rent_status rs ON r.status_id = rs.id
        LEFT JOIN penalty p ON p.rent_id = r.id
        GROUP BY l.id, l.name, l.city_id, c.name;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW book_statistics_view AS
        SELECT 
            b.id AS book_id,
            b.title,
            b.author,
            b.library_id,
            l.name AS library_name,
            COUNT(DISTINCT r.id) AS total_rents,
            COUNT(DISTINCT CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_rents,
            COUNT(DISTINCT CASE WHEN r.return_date IS NULL AND DATE(r.expected_return_date) < CURRENT_DATE AND rs.name IN ('active', 'issued', 'overdue') THEN r.id END) AS overdue_rents,
            COUNT(DISTINCT CASE WHEN r.return_date IS NOT NULL THEN r.id END) AS returned_rents,
            COALESCE(SUM(r.rent_price), 0) AS total_revenue,
            COALESCE(SUM(p.amount), 0) AS total_penalties,
            b.quantity AS current_quantity
        FROM book b
        LEFT JOIN library l ON b.library_id = l.id
        LEFT JOIN rent r ON r.book_id = b.id
        LEFT JOIN rent_status rs ON r.status_id = rs.id
        LEFT JOIN penalty p ON p.rent_id = r.id
        GROUP BY b.id, b.title, b.author, b.library_id, l.name, b.quantity;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW reader_statistics_view AS
        SELECT 
            rd.id AS reader_id,
            rd.name,
            rd.surname,
            rd.user_id,
            COUNT(DISTINCT r.id) AS total_rents,
            COUNT(DISTINCT CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_rents,
            COUNT(DISTINCT CASE WHEN r.return_date IS NULL AND DATE(r.expected_return_date) < CURRENT_DATE AND rs.name IN ('active', 'issued', 'overdue') THEN r.id END) AS overdue_rents,
            COUNT(DISTINCT CASE WHEN r.return_date IS NOT NULL THEN r.id END) AS returned_rents,
            COALESCE(SUM(r.rent_price), 0) AS total_spent,
            COALESCE(SUM(p.amount), 0) AS total_penalties_paid
        FROM reader rd
        LEFT JOIN rent r ON r.reader_id = rd.id
        LEFT JOIN rent_status rs ON r.status_id = rs.id
        LEFT JOIN penalty p ON p.rent_id = r.id
        GROUP BY rd.id, rd.name, rd.surname, rd.user_id;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW rents_by_date_view AS
        SELECT 
            DATE_TRUNC('day', r.rent_date) AS date,
            COUNT(r.id) AS rent_count,
            COUNT(CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_count,
            COUNT(CASE WHEN r.return_date IS NULL AND DATE(r.expected_return_date) < CURRENT_DATE AND rs.name IN ('active', 'issued', 'overdue') THEN r.id END) AS overdue_count,
            COUNT(CASE WHEN r.return_date IS NOT NULL THEN r.id END) AS returned_count,
            b.library_id,
            l.name AS library_name
        FROM rent r
        LEFT JOIN book b ON r.book_id = b.id
        LEFT JOIN library l ON b.library_id = l.id
        LEFT JOIN rent_status rs ON r.status_id = rs.id
        GROUP BY DATE_TRUNC('day', r.rent_date), b.library_id, l.name;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW active_readers_view AS
        SELECT 
            rd.id AS reader_id,
            rd.name,
            rd.surname,
            rd.user_id,
            COUNT(r.id) AS rent_count,
            COUNT(CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_rents
        FROM reader rd
        LEFT JOIN rent r ON r.reader_id = rd.id
        LEFT JOIN rent_status rs ON r.status_id = rs.id
        GROUP BY rd.id, rd.name, rd.surname, rd.user_id
        ORDER BY rent_count DESC;
    """)


def downgrade() -> None:
    pass
