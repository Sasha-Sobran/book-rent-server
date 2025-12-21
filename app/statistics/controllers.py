from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from sqlmodel import Session

from app.statistics.schemas import (
    LibraryStatistics,
    BookStatistics,
    ReaderStatistics,
    RentStatistics,
    RevenueStatistics,
    RentsByDate,
    OverviewStatistics,
    RentStatusChartData,
    BooksByLibraryChartData,
    ReadersByCategoryChartData,
    RentsByLibraryChartData,
)


def get_overview_statistics(session: Session, library_id: Optional[int] = None) -> OverviewStatistics:
    if library_id:
        books_query = text("""
            SELECT 
                COUNT(DISTINCT b.id) AS total_books,
                COUNT(DISTINCT CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_rents,
                COUNT(DISTINCT CASE WHEN r.return_date IS NULL AND DATE(r.expected_return_date) < CURRENT_DATE AND rs.name IN ('active', 'issued', 'overdue') THEN r.id END) AS overdue_rents,
                COALESCE(SUM(r.rent_price), 0) AS total_revenue,
                COALESCE(SUM(p.amount), 0) AS total_penalties
            FROM book b
            LEFT JOIN rent r ON r.book_id = b.id
            LEFT JOIN rent_status rs ON r.status_id = rs.id
            LEFT JOIN penalty p ON p.rent_id = r.id
            WHERE b.library_id = :library_id
        """)
        books_result = session.execute(books_query, {"library_id": library_id}).fetchone()
        
        libraries_query = text("SELECT COUNT(*) FROM library WHERE id = :library_id")
        libraries_result = session.execute(libraries_query, {"library_id": library_id}).fetchone()
        
        readers_query = text("SELECT COUNT(*) FROM reader")
        readers_result = session.execute(readers_query).fetchone()
        
        return OverviewStatistics(
            total_books=books_result[0] or 0,
            total_readers=readers_result[0] or 0,
            total_libraries=libraries_result[0] or 0,
            active_rents=books_result[1] or 0,
            overdue_rents=books_result[2] or 0,
            total_revenue=float(books_result[3] or 0),
            total_penalties=float(books_result[4] or 0),
        )
    else:
        books_query = text("""
            SELECT 
                COUNT(DISTINCT b.id) AS total_books,
                COUNT(DISTINCT CASE WHEN rs.name IN ('active', 'issued', 'overdue') AND r.return_date IS NULL THEN r.id END) AS active_rents,
                COUNT(DISTINCT CASE WHEN r.return_date IS NULL AND DATE(r.expected_return_date) < CURRENT_DATE AND rs.name IN ('active', 'issued', 'overdue') THEN r.id END) AS overdue_rents,
                COALESCE(SUM(r.rent_price), 0) AS total_revenue,
                COALESCE(SUM(p.amount), 0) AS total_penalties
            FROM book b
            LEFT JOIN rent r ON r.book_id = b.id
            LEFT JOIN rent_status rs ON r.status_id = rs.id
            LEFT JOIN penalty p ON p.rent_id = r.id
        """)
        books_result = session.execute(books_query).fetchone()
        
        libraries_query = text("SELECT COUNT(*) FROM library")
        libraries_result = session.execute(libraries_query).fetchone()
        
        readers_query = text("SELECT COUNT(*) FROM reader")
        readers_result = session.execute(readers_query).fetchone()
        
        return OverviewStatistics(
            total_books=books_result[0] or 0,
            total_readers=readers_result[0] or 0,
            total_libraries=libraries_result[0] or 0,
            active_rents=books_result[1] or 0,
            overdue_rents=books_result[2] or 0,
            total_revenue=float(books_result[3] or 0),
            total_penalties=float(books_result[4] or 0),
        )


def get_library_statistics(session: Session, library_id: Optional[int] = None) -> list[LibraryStatistics]:
    if library_id:
        query = text("SELECT * FROM library_statistics_view WHERE library_id = :library_id ORDER BY total_rents DESC")
        results = session.execute(query, {"library_id": library_id}).fetchall()
    else:
        query = text("SELECT * FROM library_statistics_view ORDER BY total_rents DESC")
        results = session.execute(query).fetchall()
    
    return [
        LibraryStatistics(
            library_id=row[0],
            library_name=row[1],
            city_id=row[2],
            city_name=row[3],
            total_books=row[4],
            total_rents=row[5],
            active_rents=row[6],
            overdue_rents=row[7],
            returned_rents=row[8],
            total_revenue=float(row[9] or 0),
            confirmed_revenue=float(row[10] or 0),
            total_penalties=float(row[11] or 0),
        )
        for row in results
    ]


def get_book_statistics(session: Session, library_id: Optional[int] = None, limit: int = 10) -> list[BookStatistics]:
    if library_id:
        query = text("SELECT * FROM book_statistics_view WHERE library_id = :library_id ORDER BY total_rents DESC LIMIT :limit")
        results = session.execute(query, {"library_id": library_id, "limit": limit}).fetchall()
    else:
        query = text("SELECT * FROM book_statistics_view ORDER BY total_rents DESC LIMIT :limit")
        results = session.execute(query, {"limit": limit}).fetchall()
    
    return [
        BookStatistics(
            book_id=row[0],
            title=row[1],
            author=row[2],
            library_id=row[3],
            library_name=row[4],
            total_rents=row[5],
            active_rents=row[6],
            overdue_rents=row[7],
            returned_rents=row[8],
            total_revenue=float(row[9] or 0),
            total_penalties=float(row[10] or 0),
            current_quantity=row[11],
        )
        for row in results
    ]


def get_reader_statistics(session: Session, limit: int = 10) -> list[ReaderStatistics]:
    query = text("SELECT * FROM reader_statistics_view ORDER BY total_rents DESC LIMIT :limit")
    results = session.execute(query, {"limit": limit}).fetchall()
    
    return [
        ReaderStatistics(
            reader_id=row[0],
            name=row[1],
            surname=row[2],
            user_id=row[3],
            total_rents=row[4],
            active_rents=row[5],
            overdue_rents=row[6],
            returned_rents=row[7],
            total_spent=float(row[8] or 0),
            total_penalties_paid=float(row[9] or 0),
        )
        for row in results
    ]


def get_rent_statistics(session: Session) -> list[RentStatistics]:
    query = text("SELECT * FROM rent_statistics_view ORDER BY rent_count DESC")
    results = session.execute(query).fetchall()
    
    return [
        RentStatistics(
            status_id=row[0],
            status_name=row[1],
            rent_count=row[2],
            total_revenue=float(row[3] or 0),
            total_penalties=float(row[4] or 0),
        )
        for row in results
    ]


def get_revenue_statistics(
    session: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    library_id: Optional[int] = None,
) -> list[RevenueStatistics]:
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date.date()
    if end_date:
        conditions.append("date <= :end_date")
        params["end_date"] = end_date.date()
    if library_id:
        conditions.append("library_id = :library_id")
        params["library_id"] = library_id
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = text(f"SELECT * FROM revenue_statistics_view {where_clause} ORDER BY date DESC")
    results = session.execute(query, params).fetchall()
    
    return [
        RevenueStatistics(
            date=row[0],
            rent_count=row[1],
            rent_revenue=float(row[2] or 0),
            penalty_revenue=float(row[3] or 0),
            total_revenue=float(row[4] or 0),
            library_id=row[5],
            library_name=row[6],
        )
        for row in results
    ]


def get_rents_by_date(
    session: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    library_id: Optional[int] = None,
) -> list[RentsByDate]:
    conditions = []
    params = {}
    
    if start_date:
        conditions.append("date >= :start_date")
        params["start_date"] = start_date.date()
    if end_date:
        conditions.append("date <= :end_date")
        params["end_date"] = end_date.date()
    if library_id:
        conditions.append("library_id = :library_id")
        params["library_id"] = library_id
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = text(f"SELECT * FROM rents_by_date_view {where_clause} ORDER BY date DESC")
    results = session.execute(query, params).fetchall()
    
    return [
        RentsByDate(
            date=row[0],
            rent_count=row[1],
            active_count=row[2],
            overdue_count=row[3],
            returned_count=row[4],
            library_id=row[5],
            library_name=row[6],
        )
        for row in results
    ]


def get_rents_by_status_chart(session: Session) -> list[RentStatusChartData]:
    query = text("SELECT * FROM rents_by_status_view WHERE rent_count > 0")
    results = session.execute(query).fetchall()
    
    return [
        RentStatusChartData(
            status_id=row[0],
            status_name=row[1],
            rent_count=row[2],
            total_revenue=float(row[3] or 0),
        )
        for row in results
    ]


def get_books_by_library_chart(session: Session) -> list[BooksByLibraryChartData]:
    query = text("SELECT * FROM books_by_library_view WHERE book_count > 0")
    results = session.execute(query).fetchall()
    
    return [
        BooksByLibraryChartData(
            library_id=row[0],
            library_name=row[1],
            city_name=row[2],
            book_count=row[3],
        )
        for row in results
    ]


def get_readers_by_category_chart(session: Session) -> list[ReadersByCategoryChartData]:
    query = text("SELECT * FROM readers_by_category_view WHERE reader_count > 0")
    results = session.execute(query).fetchall()
    
    return [
        ReadersByCategoryChartData(
            category_id=row[0],
            category_name=row[1],
            reader_count=row[2],
        )
        for row in results
    ]


def get_rents_by_library_chart(session: Session) -> list[RentsByLibraryChartData]:
    query = text("SELECT * FROM rents_by_library_view WHERE rent_count > 0 AND status_id IS NOT NULL")
    results = session.execute(query).fetchall()
    
    return [
        RentsByLibraryChartData(
            library_id=row[0],
            library_name=row[1],
            city_name=row[2],
            status_id=row[3],
            status_name=row[4],
            rent_count=row[5],
        )
        for row in results
    ]

