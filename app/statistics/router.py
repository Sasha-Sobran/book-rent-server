from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query
from sqlmodel import Session

from app.common.dependencies import SessionDep, RootUserDep
from app.statistics import controllers
from app.statistics.schemas import (
    OverviewStatistics,
    LibraryStatistics,
    BookStatistics,
    ReaderStatistics,
    RentStatistics,
    RevenueStatistics,
    RentsByDate,
    RentStatusChartData,
    BooksByLibraryChartData,
    ReadersByCategoryChartData,
    RentsByLibraryChartData,
)

statistics_router = APIRouter(prefix="/statistics", tags=["statistics"])


@statistics_router.get("/overview", response_model=OverviewStatistics)
async def get_overview_route(
    session: SessionDep,
    user: RootUserDep,
    library_id: Optional[int] = Query(None, description="Filter by library ID"),
):
    return controllers.get_overview_statistics(session, library_id=library_id)


@statistics_router.get("/libraries", response_model=list[LibraryStatistics])
async def get_libraries_statistics_route(
    session: SessionDep,
    user: RootUserDep,
    library_id: Optional[int] = Query(None, description="Filter by library ID"),
):
    return controllers.get_library_statistics(session, library_id=library_id)


@statistics_router.get("/books", response_model=list[BookStatistics])
async def get_books_statistics_route(
    session: SessionDep,
    user: RootUserDep,
    library_id: Optional[int] = Query(None, description="Filter by library ID"),
    limit: int = Query(10, ge=1, le=100, description="Limit results"),
):
    return controllers.get_book_statistics(session, library_id=library_id, limit=limit)


@statistics_router.get("/readers", response_model=list[ReaderStatistics])
async def get_readers_statistics_route(
    session: SessionDep,
    user: RootUserDep,
    limit: int = Query(10, ge=1, le=100, description="Limit results"),
):
    return controllers.get_reader_statistics(session, limit=limit)


@statistics_router.get("/rents", response_model=list[RentStatistics])
async def get_rents_statistics_route(
    session: SessionDep,
    user: RootUserDep,
):
    return controllers.get_rent_statistics(session)


@statistics_router.get("/revenue", response_model=list[RevenueStatistics])
async def get_revenue_statistics_route(
    session: SessionDep,
    user: RootUserDep,
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    library_id: Optional[int] = Query(None, description="Filter by library ID"),
):
    return controllers.get_revenue_statistics(
        session,
        start_date=start_date,
        end_date=end_date,
        library_id=library_id,
    )


@statistics_router.get("/trends", response_model=list[RentsByDate])
async def get_trends_route(
    session: SessionDep,
    user: RootUserDep,
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    library_id: Optional[int] = Query(None, description="Filter by library ID"),
):
    return controllers.get_rents_by_date(
        session,
        start_date=start_date,
        end_date=end_date,
        library_id=library_id,
    )


@statistics_router.get("/charts/rents-by-status", response_model=list[RentStatusChartData])
async def get_rents_by_status_chart_route(
    session: SessionDep,
    user: RootUserDep,
):
    return controllers.get_rents_by_status_chart(session)


@statistics_router.get("/charts/books-by-library", response_model=list[BooksByLibraryChartData])
async def get_books_by_library_chart_route(
    session: SessionDep,
    user: RootUserDep,
):
    return controllers.get_books_by_library_chart(session)


@statistics_router.get("/charts/readers-by-category", response_model=list[ReadersByCategoryChartData])
async def get_readers_by_category_chart_route(
    session: SessionDep,
    user: RootUserDep,
):
    return controllers.get_readers_by_category_chart(session)


@statistics_router.get("/charts/rents-by-library", response_model=list[RentsByLibraryChartData])
async def get_rents_by_library_chart_route(
    session: SessionDep,
    user: RootUserDep,
):
    return controllers.get_rents_by_library_chart(session)

