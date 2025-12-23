from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.schemas.book import BookCreate, FavoriteToggle, StatusUpdate, RatingUpdate
from app.models.book import Книги, Авторы, Жанры, Избранные_книги, Статус, Отзывы_пользователя, Пользователь

# Вспомогательные функции для маппинга статусов
def _map_status_id_to_name(status_id: int) -> str:
    """Маппинг ID статуса в строковое название для фронта"""
    status_map = {
        1: "want-to-read",  # Хочу прочитать
        2: "reading",       # В процессе
        3: "completed"      # Прочитано
    }
    return status_map.get(status_id, "want-to-read")

def _map_status_name_to_id(status_name: str) -> int:
    """Маппинг названия статуса в ID"""
    status_map = {
        "want-to-read": 1,
        "reading": 2,
        "completed": 3
    }
    # Если статус передан на русском
    if status_name == "Хочу прочитать":
        return 1
    elif status_name == "В процессе":
        return 2
    elif status_name == "Прочитано":
        return 3
    
    return status_map.get(status_name, 1)

def get_books(db: Session, skip: int = 0, limit: int = 20, search: str = None, genre: str = None):
    query = db.query(Книги).join(Авторы).join(Жанры)
    
    if search:
        query = query.filter(
            or_(
                Книги.Название_книги.ilike(f"%{search}%"),
                Авторы.Имя_автора.ilike(f"%{search}%"),
                Авторы.Фамилия_автора.ilike(f"%{search}%")
            )
        )
    
    if genre:
        query = query.filter(Жанры.Наименование_жанра.ilike(f"%{genre}%"))
    
    books = query.order_by(Книги.Название_книги).offset(skip).limit(limit).all()
    
    result = []
    for book in books:
        result.append({
            "id": book.Id_книги,
            "title": book.Название_книги,
            "author": f"{book.автор_rel.Имя_автора} {book.автор_rel.Фамилия_автора}",
            "genre": book.жанр_rel.Наименование_жанра,
            "coverImage": book.URL_обложки,
            "pages": book.Кол_во_страниц,
            "description": book.Описание[:200] + "..." if book.Описание and len(book.Описание) > 200 else book.Описание  # Обрезаем описание
        })
    
    return result

def get_book_by_id(db: Session, book_id: int):
    book = db.query(Книги).join(Авторы).join(Жанры).filter(Книги.Id_книги == book_id).first()
    
    if not book:
        return None
    
    return {
        "id": book.Id_книги,
        "title": book.Название_книги,
        "author": f"{book.автор_rel.Имя_автора} {book.автор_rel.Фамилия_автора}",
        "genre": book.жанр_rel.Наименование_жанрa,
        "coverImage": book.URL_обложки,  # Изменено
        "pages": book.Кол_во_страниц,
        "description": book.Описание
    }

def create_book(db: Session, book: BookCreate):
    # Сначала находим или создаем автора
    author = None
    if book.author:
        # Разделяем имя и фамилию автора
        author_parts = book.author.split()
        first_name = author_parts[0] if author_parts else ""
        last_name = author_parts[1] if len(author_parts) > 1 else ""
        
        # Ищем существующего автора
        author = db.query(Авторы).filter(
            Авторы.Имя_автора == first_name,
            Авторы.Фамилия_автора == last_name
        ).first()
        
        # Если автора нет - создаем нового
        if not author:
            author = Авторы(
                Имя_автора=first_name,
                Фамилия_автора=last_name
            )
            db.add(author)
            db.commit()
            db.refresh(author)

    # Находим жанр
    genre = None
    if book.genre:
        genre = db.query(Жанры).filter(
            Жанры.Наименование_жанра.ilike(f"%{book.genre}%")
        ).first()
        
        # Если жанра нет - создаем новый
        if not genre:
            genre = Жанры(Наименование_жанра=book.genre)
            db.add(genre)
            db.commit()
            db.refresh(genre)

    # Создаем книгу
    db_book = Книги(
        Название_книги=book.title,
        Id_автора=author.Id_автора if author else 1,
        Id_жанра=genre.Id_жанра if genre else 1,
        URL_обложки=book.cover_url,
        Кол_во_страниц=book.pages,
        Описание=book.description
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)

    # Получаем книгу с отношениями для возврата
    db_book_with_relations = db.query(Книги)\
        .join(Авторы)\
        .join(Жанры)\
        .filter(Книги.Id_книги == db_book.Id_книги)\
        .first()

    # Преобразуем в формат для фронта
    return {
        "id": db_book_with_relations.Id_книги,
        "title": db_book_with_relations.Название_книги,
        "author": f"{db_book_with_relations.автор_rel.Имя_автора} {db_book_with_relations.автор_rel.Фамилия_автора}",
        "genre": db_book_with_relations.жанр_rel.Наименование_жанра,
        "coverImage": db_book_with_relations.URL_обложки, 
        "pages": db_book_with_relations.Кол_во_страниц,
        "description": db_book_with_relations.Описание
    }

def get_user_favorites(db: Session, user_id: int):
    # Получаем избранные записи
    favorites = db.query(Избранные_книги)\
        .filter(Избранные_книги.Пользователь == user_id)\
        .all()
    
    result = []
    for fav in favorites:
        # Для каждой избранной записи загружаем книгу с автором и жанром
        book_query = db.query(Книги)\
            .join(Авторы, Книги.Автор == Авторы.Id_автора)\
            .join(Жанры, Книги.Жанр == Жанры.id_жанра)\
            .filter(Книги.Id_книги == fav.Книга)
        
        book = book_query.first()
        
        # Загружаем статус
        status = db.query(Статус)\
            .filter(Статус.Id_статуса == fav.Статус_книги)\
            .first()
        
        # Получаем рейтинг из таблицы отзывов
        review = db.query(Отзывы_пользователя)\
            .filter(Отзывы_пользователя.Избранная_книга == fav.id_избранной_книги)\
            .first()
        
        if book:
            # Получаем название статуса для фронта
            status_name = _map_status_id_to_name(fav.Статус_книги)
            
            result.append({
                "id": book.Id_книги,
                "Id_книги": book.Id_книги,  # Для совместимости
                "title": book.Название_книги,
                "Название_книги": book.Название_книги,  # Для совместимости
                "author": f"{book.автор_rel.Имя_автора} {book.автор_rel.Фамилия_автора}",
                "Автор": {"Имя_автора": book.автор_rel.Имя_автора, "Фамилия_автора": book.автор_rel.Фамилия_автора},  # Для совместимости
                "genre": book.жанр_rel.Наименование_жанра,
                "Жанр": {"Наименование_жанра": book.жанр_rel.Наименование_жанра},  # Для совместимости
                "coverImage": book.URL_обложки,  # Изменено
                "cover_url": book.URL_обложки,  # Для обратной совместимости
                "URL_обложки": book.URL_обложки,  # Для совместимости
                "pages": book.Кол_во_страниц,
                "Кол_во_страниц": book.Кол_во_страниц,  # Для совместимости
                "description": book.Описание,
                "Описание": book.Описание,  # Для совместимости
                "favorite_id": fav.id_избранной_книги,
                "id_избранной_книги": fav.id_избранной_книги,  # Для совместимости
                "status": status_name,  # Мапим в строковый формат
                "Статус_книги": status_name,  # Для совместимости
                "rating": review.Оценка if review else None,
                "Оценка": review.Оценка if review else None  # Для совместимости
            })
    
    return result

def toggle_favorite(db: Session, favorite_data: FavoriteToggle):
    # Проверяем, есть ли уже книга в избранном
    existing_favorite = db.query(Избранные_книги).filter(
        Избранные_книги.Книга == favorite_data.book_id,        
        Избранные_книги.Пользователь == favorite_data.user_id  
    ).first()
    
    if existing_favorite:
        # Сначала удаляем все связанные отзывы
        db.query(Отзывы_пользователя)\
            .filter(Отзывы_пользователя.Избранная_книга == existing_favorite.id_избранной_книги)\
            .delete(synchronize_session=False)
        
        # Затем удаляем избранную запись
        db.delete(existing_favorite)
        db.commit()
        return {"action": "removed", "favorite_id": existing_favorite.id_избранной_книги}
    else:
        # Добавляем в избранное со статусом "want-to-read"
        status = db.query(Статус).filter(
            Статус.Наименование_статуса == "Хочу прочитать"
        ).first()
        
        new_favorite = Избранные_книги(
            Книга=favorite_data.book_id,           
            Пользователь=favorite_data.user_id,    
            Статус_книги=status.Id_статуса if status else 1 
        )
        db.add(new_favorite)
        db.commit()
        db.refresh(new_favorite)
        return {"action": "added", "favorite_id": new_favorite.id_избранной_книги}

def update_favorite_status(db: Session, favorite_id: int, status_id: int):
    """Обновляем статус по favorite_id"""
    favorite = db.query(Избранные_книги).filter(
        Избранные_книги.id_избранной_книги == favorite_id 
    ).first()
    
    if not favorite:
        return None
    
    # Проверяем, что статус существует
    status_obj = db.query(Статус).filter(
        Статус.Id_статуса == status_id
    ).first()
    
    if status_obj:
        favorite.Статус_книги = status_id
        db.commit()
        db.refresh(favorite)
    
    return favorite

def update_favorite_status_by_book(db: Session, book_id: int, user_id: int, status_id: int):
    """Обновляем статус по book_id и user_id (альтернативный метод)"""
    favorite = db.query(Избранные_книги).filter(
        Избранные_книги.Книга == book_id,
        Избранные_книги.Пользователь == user_id
    ).first()
    
    if not favorite:
        return None
    
    favorite.Статус_книги = status_id
    db.commit()
    db.refresh(favorite)
    return favorite

def update_favorite_rating(db: Session, favorite_id: int, rating: int):
    # Находим или создаем отзыв
    review = db.query(Отзывы_пользователя).filter(
        Отзывы_пользователя.Избранная_книга == favorite_id
    ).first()
    
    if review:
        review.Оценка = rating
    else:
        review = Отзывы_пользователя(
            Избранная_книга=favorite_id,
            Оценка=rating,
            Комментарий=""
        )
        db.add(review)
    
    db.commit()
    db.refresh(review)
    return review

def update_favorite_rating_by_book(db: Session, book_id: int, user_id: int, rating: int):
    """Обновляем рейтинг по book_id и user_id"""
    # Находим избранную запись
    favorite = db.query(Избранные_книги).filter(
        Избранные_книги.Книга == book_id,
        Избранные_книги.Пользователь == user_id
    ).first()
    
    if not favorite:
        return None
    
    # Находим или создаем отзыв
    review = db.query(Отзывы_пользователя).filter(
        Отзывы_пользователя.Избранная_книга == favorite.id_избранной_книги
    ).first()
    
    if review:
        review.Оценка = rating
    else:
        review = Отзывы_пользователя(
            Избранная_книга=favorite.id_избранной_книги,
            Оценка=rating,
            Комментарий=""
        )
        db.add(review)
    
    db.commit()
    db.refresh(review)
    return review

def remove_from_favorites(db: Session, favorite_id: int):
    # Сначала удаляем все связанные отзывы
    db.query(Отзывы_пользователя)\
        .filter(Отзывы_пользователя.Избранная_книга == favorite_id)\
        .delete(synchronize_session=False)
    
    # Затем удаляем избранную запись
    favorite = db.query(Избранные_книги).filter(
        Избранные_книги.id_избранной_книги == favorite_id
    ).first()
    
    if favorite:
        db.delete(favorite)
        db.commit()
        return True
    return False

def remove_from_favorites_by_book(db: Session, book_id: int, user_id: int):
    """Удаляем по book_id и user_id"""
    # Находим избранную запись
    favorite = db.query(Избранные_книги).filter(
        Избранные_книги.Книга == book_id,
        Избранные_книги.Пользователь == user_id
    ).first()
    
    if not favorite:
        return False
    
    # Сначала удаляем все связанные отзывы
    db.query(Отзывы_пользователя)\
        .filter(Отзывы_пользователя.Избранная_книга == favorite.id_избранной_книги)\
        .delete(synchronize_session=False)
    
    # Затем удаляем избранную запись
    db.delete(favorite)
    db.commit()
    return True

# CRUD для пользователей
def create_user(db: Session, email: str, username: str, password_hash: str):
    user = Пользователь(
        email=email,
        Имя_пользователя=username,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(Пользователь).filter(Пользователь.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(Пользователь).filter(Пользователь.Id_пользователя == user_id).first()

# Дополнительные функции
def search_books(db: Session, search_term: str = None, genre: str = None):
    return get_books(db, search=search_term, genre=genre)

def get_favorite_id_by_book_and_user(db: Session, book_id: int, user_id: int):
    """Получаем favorite_id по book_id и user_id"""
    favorite = db.query(Избранные_книги).filter(
        Избранные_книги.Книга == book_id,
        Избранные_книги.Пользователь == user_id
    ).first()
    
    return favorite.id_избранной_книги if favorite else None

# Дополнительные функции для работы с книгами 
def get_books_by_author(db: Session, author_id: int):
    return db.query(Книги).filter(Книги.Id_автора == author_id).all()

def get_books_by_genre(db: Session, genre_id: int):
    return db.query(Книги).filter(Книги.Id_жанра == genre_id).all()

def update_book(db: Session, book_id: int, book_update: BookCreate):
    db_book = db.query(Книги).filter(Книги.Id_книги == book_id).first()
    if not db_book:
        return None
    
    # Обновляем автора если нужно
    if book_update.author:
        author = db.query(Авторы).filter(
            Авторы.Имя_автора == book_update.author.split()[0]
        ).first()
        
        if not author:
            author_parts = book_update.author.split()
            author = Авторы(
                Имя_автора=author_parts[0] if author_parts else "",
                Фамилия_автора=author_parts[1] if len(author_parts) > 1 else ""
            )
            db.add(author)
            db.commit()
            db.refresh(author)
        db_book.Id_автора = author.Id_автора
    
    # Обновляем жанр если нужно
    if book_update.genre:
        genre = db.query(Жанры).filter(
            Жанры.Наименование_жанра.ilike(f"%{book_update.genre}%")
        ).first()
        if genre:
            db_book.Id_жанra = genre.Id_жанра
    
    # Обновляем остальные поля
    if book_update.title:
        db_book.Название_книги = book_update.title
    if book_update.pages:
        db_book.Кол_во_страниц = book_update.pages
    if book_update.cover_url:
        db_book.URL_обложки = book_update.cover_url
    if book_update.description:
        db_book.Описание = book_update.description
    
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int):
    db_book = db.query(Книги).filter(Книги.Id_книги == book_id).first()
    if not db_book:
        return False
    
    db.delete(db_book)
    db.commit()
    return True

def get_all_authors(db: Session):
    return db.query(Авторы).all()

def get_all_genres(db: Session):
    return db.query(Жанры).all()

def get_all_statuses(db: Session):
    return db.query(Статус).all()