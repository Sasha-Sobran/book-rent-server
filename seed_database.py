#!/usr/bin/env python3
"""
Скрипт для заповнення бази даних тестовими даними
Використання: python seed_database.py
"""

import random
from datetime import datetime, timedelta
from sqlmodel import Session, select

from database import engine
from app.models.city import City
from app.models.library import Library
from app.models.book import Book
from app.models.reader import Reader
from app.models.category import Category
from app.models.genre import Genre
from app.models.reader_category import ReaderCategory
from app.models.book import BookCategory, BookGenre
from app.models.rent import Rent
from app.models.rent_status import RentStatus
from app.models.librarian import Librarian
from app.common.db_utils import save_and_refresh
from app.common.utils import get_or_create_by_name
from app.common.constants import RentStatusNames
from app.common.rent_utils import calculate_daily_rate, get_reader_discount


UKRAINIAN_CITIES = [
    "Київ", "Харків", "Одеса", "Дніпро", "Запоріжжя", "Львів", "Кривий Ріг",
    "Миколаїв", "Маріуполь", "Луганськ", "Вінниця", "Севастополь", "Сімферополь",
    "Херсон", "Полтава", "Чернігів", "Черкаси", "Хмельницький", "Житомир",
    "Івано-Франківськ", "Тернопіль", "Рівне", "Луцьк", "Ужгород", "Мукачево"
]

LIBRARY_NAMES = [
    "Центральна бібліотека", "Бібліотека ім. Шевченка", "Публічна бібліотека",
    "Наукова бібліотека", "Дитяча бібліотека", "Бібліотека мистецтв",
    "Технічна бібліотека", "Медична бібліотека", "Бібліотека історії",
    "Університетська бібліотека", "Шкільна бібліотека", "Районна бібліотека"
]

BOOK_TITLES = [
    "Гаррі Поттер і філософський камінь", "Володар перснів", "Гра престолів",
    "1984", "Війна і мир", "Анна Кареніна", "Маленький принц", "Гордість і упередження",
    "Джейн Ейр", "Мобі Дік", "Великий Гетсбі", "Злочин і кара", "Брати Карамазови",
    "Ідіот", "Майстер і Маргарита", "Собаче серце", "12 стільців", "Золоте теля",
    "Тисяча і одна ніч", "Дон Кіхот", "Фауст", "Гамлет", "Ромео і Джульєтта",
    "Макбет", "Отелло", "Король Лір", "Пригоди Тома Сойєра", "Пригоди Гекльберрі Фінна",
    "Острів скарбів", "Робінзон Крузо", "Граф Монте-Крісто", "Три мушкетери",
    "Граф Монте-Крісто", "Двадцять тисяч льє під водою", "Навколо світу за 80 днів",
    "Аліса в Країні Чудес", "Вітер у вербах", "Хобіт", "Сильмариліон",
    "Дюна", "Фундація", "Я, робот", "451 градус за Фаренгейтом",
    "Механічний апельсин", "Колгосп тварин", "Повернення короля", "Дві вежі",
    "Братство персня", "Хроніки Нарнії", "Володар мух", "Старий і море",
    "По кому подзвін", "Прощавай, зброє!", "Сонячний удар", "Білі ночі"
]

AUTHORS = [
    "Дж. К. Роулінг", "Дж. Р. Р. Толкін", "Джордж Мартін", "Джордж Орвелл",
    "Лев Толстой", "Федір Достоєвський", "Антуан де Сент-Екзюпері", "Джейн Остін",
    "Шарлотта Бронте", "Герман Мелвілл", "Френсіс Скотт Фіцджеральд", "Міхаїл Булгаков",
    "Ілля Ільф", "Євген Петров", "Мігель де Сервантес", "Йоганн Вольфганг фон Гете",
    "Вільям Шекспір", "Марк Твен", "Роберт Льюїс Стівенсон", "Даніель Дефо",
    "Александр Дюма", "Жуль Верн", "Льюїс Керролл", "Френк Герберт",
    "Айзек Азімов", "Рей Бредбері", "Ентоні Берджесс", "Ернест Гемінгуей",
    "Клайв Стейплз Льюїс", "Вільям Голдінг", "Сергій Лук'яненко", "Андрій Курков"
]

READER_NAMES = [
    "Олександр", "Дмитро", "Максим", "Артем", "Іван", "Олег", "Андрій", "Сергій",
    "Володимир", "Роман", "Віктор", "Олексій", "Михайло", "Павло", "Юрій",
    "Анна", "Марія", "Олена", "Ольга", "Наталія", "Катерина", "Тетяна",
    "Ірина", "Юлія", "Вікторія", "Світлана", "Валентина", "Галина", "Людмила"
]

READER_SURNAMES = [
    "Іваненко", "Петренко", "Коваленко", "Бондаренко", "Ткаченко", "Морозенко",
    "Шевченко", "Бондар", "Кравченко", "Коваль", "Мельник", "Шевчук", "Бондарчук",
    "Ткачук", "Мороз", "Лисенко", "Романенко", "Савченко", "Петриченко", "Кравчук",
    "Олійник", "Шевчук", "Марченко", "Левченко", "Клименко", "Павленко", "Кравченко"
]

CATEGORIES = [
    "Художня література", "Наукова література", "Історична література",
    "Дитяча література", "Фантастика", "Детективи", "Романтична література",
    "Біографії", "Поезія", "Драматургія", "Філософія", "Психологія",
    "Економіка", "Право", "Медицина", "Техніка", "Мистецтво", "Спорт"
]

GENRES = [
    "Роман", "Повість", "Оповідання", "Детектив", "Трилер", "Фантастика",
    "Фентезі", "Жахи", "Романтика", "Історичний роман", "Біографія",
    "Автобіографія", "Мемуари", "Поезія", "Драма", "Комедія", "Трагедія",
    "Пригоди", "Подорожі", "Наукова література", "Філософія", "Психологія"
]

READER_CATEGORIES = [
    "Студент", "Школяр", "Пенсіонер", "Працівник", "Дошкільня", "Дорослий"
]


def create_cities(session: Session, count: int = 5) -> list[City]:
    """Створює міста"""
    cities = []
    for city_name in random.sample(UKRAINIAN_CITIES, min(count, len(UKRAINIAN_CITIES))):
        existing = session.exec(select(City).where(City.name == city_name)).first()
        if not existing:
            city = City(name=city_name)
            save_and_refresh(session, city)
            cities.append(city)
        else:
            cities.append(existing)
    return cities


def create_libraries(session: Session, cities: list[City], count: int = 3) -> list[Library]:
    """Створює бібліотеки"""
    libraries = []
    for i in range(count):
        city = random.choice(cities)
        library_name = f"{random.choice(LIBRARY_NAMES)} {i+1}"
        address = f"вул. {random.choice(['Шевченка', 'Грушевського', 'Хрещатик', 'Львівська', 'Київська'])}, {random.randint(1, 100)}"
        phone = f"+380{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
        
        library = Library(
            name=library_name,
            city_id=city.id,
            address=address,
            phone_number=phone
        )
        save_and_refresh(session, library)
        libraries.append(library)
    return libraries


def get_or_create_categories(session: Session) -> list[Category]:
    """Отримує або створює категорії"""
    categories = []
    for cat_name in CATEGORIES:
        existing = session.exec(select(Category).where(Category.name == cat_name)).first()
        if not existing:
            category = Category(name=cat_name)
            save_and_refresh(session, category)
            categories.append(category)
        else:
            categories.append(existing)
    return categories


def get_or_create_genres(session: Session) -> list[Genre]:
    """Отримує або створює жанри"""
    genres = []
    for genre_name in GENRES:
        existing = session.exec(select(Genre).where(Genre.name == genre_name)).first()
        if not existing:
            genre = Genre(name=genre_name)
            save_and_refresh(session, genre)
            genres.append(genre)
        else:
            genres.append(existing)
    return genres


def get_or_create_reader_categories(session: Session) -> list[ReaderCategory]:
    """Отримує або створює категорії читачів"""
    reader_categories = []
    discounts = {"Студент": 10, "Школяр": 15, "Пенсіонер": 20, "Працівник": 5, "Дошкільня": 25, "Дорослий": 0}
    for cat_name in READER_CATEGORIES:
        existing = session.exec(select(ReaderCategory).where(ReaderCategory.name == cat_name)).first()
        if not existing:
            category = ReaderCategory(name=cat_name, discount_percentage=discounts.get(cat_name, 0))
            save_and_refresh(session, category)
            reader_categories.append(category)
        else:
            reader_categories.append(existing)
    return reader_categories


def create_books(
    session: Session,
    libraries: list[Library],
    categories: list[Category],
    genres: list[Genre],
    count: int = 50
) -> list[Book]:
    """Створює книги"""
    books = []
    for i in range(count):
        library = random.choice(libraries)
        title = random.choice(BOOK_TITLES)
        author = random.choice(AUTHORS)
        price = round(random.uniform(100, 2000), 2)
        publish_year = str(random.randint(1950, 2024))
        quantity = random.randint(0, 20)
        
        book = Book(
            title=title,
            author=author,
            price=price,
            publish_year=publish_year,
            library_id=library.id,
            quantity=quantity
        )
        save_and_refresh(session, book)
        
        # Додаємо категорії та жанри
        selected_categories = random.sample(categories, random.randint(1, 3))
        selected_genres = random.sample(genres, random.randint(1, 2))
        
        for cat in selected_categories:
            book_category = BookCategory(book_id=book.id, category_id=cat.id)
            session.add(book_category)
        
        for gen in selected_genres:
            book_genre = BookGenre(book_id=book.id, genre_id=gen.id)
            session.add(book_genre)
        
        session.commit()
        books.append(book)
    return books


def create_readers(
    session: Session,
    reader_categories: list[ReaderCategory],
    count: int = 30
) -> list[Reader]:
    """Створює читачів"""
    readers = []
    for i in range(count):
        name = random.choice(READER_NAMES)
        surname = random.choice(READER_SURNAMES)
        phone = f"+380{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
        address = f"вул. {random.choice(['Шевченка', 'Грушевського', 'Хрещатик', 'Львівська'])}, {random.randint(1, 100)}"
        reader_category = random.choice(reader_categories) if reader_categories else None
        
        reader = Reader(
            name=name,
            surname=surname,
            phone_number=phone,
            address=address,
            reader_category_id=reader_category.id if reader_category else None
        )
        save_and_refresh(session, reader)
        readers.append(reader)
    return readers


def get_or_create_rent_statuses(session: Session) -> dict[str, RentStatus]:
    """Отримує або створює статуси рентів"""
    statuses = {}
    status_names = [
        RentStatusNames.ACTIVE,
        RentStatusNames.PENDING,
        RentStatusNames.RETURNED,
        RentStatusNames.DECLINED,
        RentStatusNames.CANCELLED,
        RentStatusNames.ISSUED,
        RentStatusNames.OVERDUE,
    ]
    for status_name in status_names:
        status = get_or_create_by_name(session, RentStatus, status_name)
        statuses[status_name] = status
    return statuses


def create_rents(
    session: Session,
    books: list[Book],
    readers: list[Reader],
    librarians: list[Librarian],
    count: int = 40
) -> list[Rent]:
    """Створює ренти з різними статусами"""
    rents = []
    statuses = get_or_create_rent_statuses(session)
    
    # Розподіл статусів (приблизно)
    status_distribution = {
        RentStatusNames.ACTIVE: 0.3,
        RentStatusNames.PENDING: 0.2,
        RentStatusNames.RETURNED: 0.25,
        RentStatusNames.DECLINED: 0.1,
        RentStatusNames.CANCELLED: 0.1,
        RentStatusNames.OVERDUE: 0.05,
    }
    
    for i in range(count):
        book = random.choice(books)
        reader = random.choice(readers)
        librarian = random.choice(librarians)
        
        # Вибір статусу згідно з розподілом
        rand = random.random()
        cumulative = 0
        selected_status = RentStatusNames.ACTIVE
        for status_name, probability in status_distribution.items():
            cumulative += probability
            if rand <= cumulative:
                selected_status = status_name
                break
        
        status = statuses[selected_status]
        
        # Розрахунок дат залежно від статусу
        days_ago = random.randint(0, 60)
        rent_date = datetime.utcnow() - timedelta(days=days_ago)
        loan_days = random.randint(7, 30)
        expected_return_date = rent_date + timedelta(days=loan_days)
        
        return_date = None
        if selected_status in [RentStatusNames.RETURNED]:
            return_days_ago = random.randint(0, loan_days)
            return_date = rent_date + timedelta(days=return_days_ago)
        elif selected_status == RentStatusNames.OVERDUE:
            expected_return_date = rent_date + timedelta(days=loan_days - random.randint(5, 15))
        
        # Розрахунок ціни
        discount = get_reader_discount(session, reader)
        daily_rate = calculate_daily_rate(book.price, discount)
        rent_price = max(round(daily_rate * loan_days, 2), 0)
        deposit_price = max(int(round(book.price)), 0)
        
        rent = Rent(
            book_id=book.id,
            reader_id=reader.id,
            librarian_id=librarian.id,
            rent_date=rent_date,
            expected_return_date=expected_return_date,
            return_date=return_date,
            rent_price=rent_price,
            deposit_price=deposit_price,
            status_id=status.id,
        )
        
        # Зменшуємо кількість книг тільки для активних/виданих рентів
        if selected_status in [RentStatusNames.ACTIVE, RentStatusNames.ISSUED, RentStatusNames.OVERDUE]:
            if book.quantity > 0:
                book.quantity -= 1
        
        save_and_refresh(session, rent)
        if selected_status in [RentStatusNames.ACTIVE, RentStatusNames.ISSUED, RentStatusNames.OVERDUE]:
            session.add(book)
        session.commit()
        
        rents.append(rent)
    
    return rents


def main():
    """Основна функція для заповнення бази даних"""
    print("Початок заповнення бази даних...")
    
    with Session(engine) as session:
        # Створюємо міста
        print("Створення міст...")
        cities = create_cities(session, count=5)
        print(f"Створено {len(cities)} міст")
        
        # Створюємо бібліотеки
        print("Створення бібліотек...")
        libraries = create_libraries(session, cities, count=3)
        print(f"Створено {len(libraries)} бібліотек")
        
        # Створюємо категорії та жанри
        print("Створення категорій та жанрів...")
        categories = get_or_create_categories(session)
        genres = get_or_create_genres(session)
        reader_categories = get_or_create_reader_categories(session)
        print(f"Створено {len(categories)} категорій, {len(genres)} жанрів, {len(reader_categories)} категорій читачів")
        
        # Створюємо книги
        print("Створення книг...")
        books = create_books(session, libraries, categories, genres, count=100)
        print(f"Створено {len(books)} книг")
        
        # Створюємо читачів
        print("Створення читачів...")
        readers = create_readers(session, reader_categories, count=50)
        print(f"Створено {len(readers)} читачів")
        
        # Створюємо ренти
        print("Створення рентів...")
        librarians = session.exec(select(Librarian)).all()
        if librarians:
            rents = create_rents(session, books, readers, librarians, count=40)
            print(f"Створено {len(rents)} рентів")
        else:
            print("Попередження: немає бібліотекарів для створення рентів")
            rents = []
        
        session.commit()
        print("База даних успішно заповнена!")
        print(f"\nПідсумок:")
        print(f"- Міст: {len(cities)}")
        print(f"- Бібліотек: {len(libraries)}")
        print(f"- Книг: {len(books)}")
        print(f"- Читачів: {len(readers)}")
        print(f"- Рентів: {len(rents)}")


if __name__ == "__main__":
    main()

