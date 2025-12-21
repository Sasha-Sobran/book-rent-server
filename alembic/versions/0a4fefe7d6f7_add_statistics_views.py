"""add_statistics_views

Revision ID: 0a4fefe7d6f7
Revises: 974a5a4dcff1
Create Date: 2025-12-14 16:19:20.214184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a4fefe7d6f7'
down_revision: Union[str, None] = '974a5a4dcff1'
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
        CREATE OR REPLACE VIEW rent_statistics_view AS
        SELECT 
            rs.id AS status_id,
            rs.name AS status_name,
            COUNT(r.id) AS rent_count,
            COALESCE(SUM(r.rent_price), 0) AS total_revenue,
            COALESCE(SUM(p.amount), 0) AS total_penalties
        FROM rent_status rs
        LEFT JOIN rent r ON r.status_id = rs.id
        LEFT JOIN penalty p ON p.rent_id = r.id
        GROUP BY rs.id, rs.name;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW revenue_statistics_view AS
        SELECT 
            DATE_TRUNC('day', r.rent_date) AS date,
            COUNT(r.id) AS rent_count,
            COALESCE(SUM(r.rent_price), 0) AS rent_revenue,
            COALESCE(SUM(p.amount), 0) AS penalty_revenue,
            COALESCE(SUM(r.rent_price) + SUM(p.amount), 0) AS total_revenue,
            b.library_id,
            l.name AS library_name
        FROM rent r
        LEFT JOIN book b ON r.book_id = b.id
        LEFT JOIN library l ON b.library_id = l.id
        LEFT JOIN penalty p ON p.rent_id = r.id
        WHERE r.return_date IS NOT NULL
        GROUP BY DATE_TRUNC('day', r.rent_date), b.library_id, l.name;
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
        CREATE OR REPLACE VIEW revenue_by_date_view AS
        SELECT 
            DATE_TRUNC('day', r.rent_date) AS date,
            COUNT(r.id) AS rent_count,
            COALESCE(SUM(r.rent_price), 0) AS rent_revenue,
            COALESCE(SUM(p.amount), 0) AS penalty_revenue,
            COALESCE(SUM(r.rent_price) + SUM(p.amount), 0) AS total_revenue,
            b.library_id,
            l.name AS library_name
        FROM rent r
        LEFT JOIN book b ON r.book_id = b.id
        LEFT JOIN library l ON b.library_id = l.id
        LEFT JOIN penalty p ON p.rent_id = r.id
        WHERE r.return_date IS NOT NULL
        GROUP BY DATE_TRUNC('day', r.rent_date), b.library_id, l.name;
    """)

    op.execute("""
        CREATE OR REPLACE VIEW popular_books_view AS
        SELECT 
            b.id AS book_id,
            b.title,
            b.author,
            b.library_id,
            l.name AS library_name,
            COUNT(r.id) AS rent_count,
            b.quantity AS current_quantity
        FROM book b
        LEFT JOIN library l ON b.library_id = l.id
        LEFT JOIN rent r ON r.book_id = b.id
        GROUP BY b.id, b.title, b.author, b.library_id, l.name, b.quantity
        ORDER BY rent_count DESC;
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
    op.execute("DROP VIEW IF EXISTS active_readers_view;")
    op.execute("DROP VIEW IF EXISTS popular_books_view;")
    op.execute("DROP VIEW IF EXISTS revenue_by_date_view;")
    op.execute("DROP VIEW IF EXISTS rents_by_date_view;")
    op.execute("DROP VIEW IF EXISTS revenue_statistics_view;")
    op.execute("DROP VIEW IF EXISTS rent_statistics_view;")
    op.execute("DROP VIEW IF EXISTS reader_statistics_view;")
    op.execute("DROP VIEW IF EXISTS book_statistics_view;")
    op.execute("DROP VIEW IF EXISTS library_statistics_view;")
