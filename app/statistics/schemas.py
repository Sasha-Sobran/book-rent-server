from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LibraryStatistics(BaseModel):
    library_id: int
    library_name: str
    city_id: int
    city_name: str
    total_books: int
    total_rents: int
    active_rents: int
    overdue_rents: int
    returned_rents: int
    total_revenue: float
    confirmed_revenue: float
    total_penalties: float


class BookStatistics(BaseModel):
    book_id: int
    title: str
    author: str
    library_id: int
    library_name: str
    total_rents: int
    active_rents: int
    overdue_rents: int
    returned_rents: int
    total_revenue: float
    total_penalties: float
    current_quantity: int


class ReaderStatistics(BaseModel):
    reader_id: int
    name: str
    surname: str
    user_id: Optional[int]
    total_rents: int
    active_rents: int
    overdue_rents: int
    returned_rents: int
    total_spent: float
    total_penalties_paid: float


class RentStatistics(BaseModel):
    status_id: int
    status_name: str
    rent_count: int
    total_revenue: float
    total_penalties: float


class RevenueStatistics(BaseModel):
    date: datetime
    rent_count: int
    rent_revenue: float
    penalty_revenue: float
    total_revenue: float
    library_id: Optional[int]
    library_name: Optional[str]


class RentsByDate(BaseModel):
    date: datetime
    rent_count: int
    active_count: int
    overdue_count: int
    returned_count: int
    library_id: Optional[int]
    library_name: Optional[str]


class OverviewStatistics(BaseModel):
    total_books: int
    total_readers: int
    total_libraries: int
    active_rents: int
    overdue_rents: int
    total_revenue: float
    total_penalties: float


class RentStatusChartData(BaseModel):
    status_id: int
    status_name: str
    rent_count: int
    total_revenue: float


class BooksByLibraryChartData(BaseModel):
    library_id: int
    library_name: str
    city_name: Optional[str]
    book_count: int


class ReadersByCategoryChartData(BaseModel):
    category_id: int
    category_name: str
    reader_count: int


class RentsByLibraryChartData(BaseModel):
    library_id: int
    library_name: str
    city_name: Optional[str]
    status_id: int
    status_name: str
    rent_count: int

