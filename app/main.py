import re
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import json

from app.database import get_db, engine
from app.models.book import Base
from app.models.book import Книги, Авторы, Жанры, Статус, Избранные_книги, Отзывы_пользователя, Пользователь
from app.schemas.book import (
    BookCreate, BookResponse, FavoriteToggle, StatusUpdate, RatingUpdate,
    LoginRequest, RegisterRequest, APIResponse, BookSearchQuery
)
from app.crud import books as crud_books
from app.auth import create_access_token, verify_token, verify_password, get_password_hash
from datetime import timedelta
from fastapi import Query
from sqlalchemy import or_

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BookApp API",
    version="1.0.0",
    description="API для управления библиотекой книг"
)

# CORS для Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость для аутентификации
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = crud_books.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

# Хелпер для формирования ответа
def api_response(data: Any = None, message: str = None, error: str = None):
    return APIResponse(data=data, message=message, error=error)

# ========== АУТЕНТИФИКАЦИЯ ==========
@app.post("/api/auth/login", response_model=APIResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    # 1. Находим пользователя
    user = crud_books.get_user_by_email(db, login_data.email)
    
    # 2. Если пользователь не найден - возвращаем 401 Unauthorized
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль"
        )
    
    # 3. Проверяем пароль
    try:
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Неверный email или пароль"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка проверки пароля: {str(e)}"
        )
    
    # 4. Создаем токен
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.Id_пользователя)},
        expires_delta=access_token_expires
    )
    
    user_data = {
        "id": user.Id_пользователя,
        "email": user.email,
        "username": user.Имя_пользователя
    }
    
    return api_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        },
        message="Вход выполнен успешно"
    )

@app.post("/api/auth/register", response_model=APIResponse)
def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    # 1. Валидация email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, register_data.email):
        return api_response(error="Некорректный формат email")
    
    # 2. Валидация пароля
    if len(register_data.password) < 6:
        return api_response(error="Пароль должен быть не менее 6 символов")
    if len(register_data.password) > 50:
        return api_response(error="Пароль должен быть не более 50 символов")
    
    # 3. Валидация имени пользователя
    if len(register_data.username) < 2:
        return api_response(error="Имя пользователя должно быть не менее 2 символов")
    if len(register_data.username) > 30:
        return api_response(error="Имя пользователя должно быть не более 30 символов")
    if not register_data.username.replace(" ", "").isalnum():
        return api_response(error="Имя пользователя может содержать только буквы, цифры и пробелы")
    
    # 4. Проверка существующего пользователя
    existing_user = crud_books.get_user_by_email(db, register_data.email)
    if existing_user:
        return api_response(error="Пользователь с таким email уже существует")
    
    # 5. Хеширование пароля
    try:
        hashed_password = get_password_hash(register_data.password)
    except ValueError as e:
        return api_response(error=str(e))
    
    # 6. Создание пользователя
    try:
        user = crud_books.create_user(
            db,
            email=register_data.email,
            username=register_data.username,
            password_hash=hashed_password
        )
    except Exception as e:
        return api_response(error=f"Ошибка создания пользователя: {str(e)}")
    
    # 7. Автоматический логин
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.Id_пользователя)},
        expires_delta=access_token_expires
    )
    
    user_data = {
        "id": user.Id_пользователя,
        "email": user.email,
        "username": user.Имя_пользователя
    }
    
    return api_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        },
        message="Регистрация успешна"
    )

# ========== КНИГИ ==========
@app.get("/api/books", response_model=APIResponse)
def get_all_books(
    q: Optional[str] = None,
    genre: Optional[str] = None,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество книг на странице"),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    
    books = crud_books.get_books(
        db, 
        skip=skip, 
        limit=limit, 
        search=q, 
        genre=genre
    )
    
    # Получаем общее количество для пагинации
    total_query = db.query(Книги)
    if q:
        total_query = total_query.join(Авторы).filter(
            or_(
                Книги.Название_книги.ilike(f"%{q}%"),
                Авторы.Имя_автора.ilike(f"%{q}%"),
                Авторы.Фамилия_автора.ilike(f"%{q}%")
            )
        )
    if genre:
        total_query = total_query.join(Жанры).filter(
            Жанры.Наименование_жанра.ilike(f"%{genre}%")
        )
    
    total = total_query.count()
    
    return api_response(
        data={
            "books": books,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )

@app.get("/api/books/search", response_model=APIResponse)
def search_books(
    q: Optional[str] = None,
    genre: Optional[str] = None,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    books = crud_books.search_books(db, search_term=q, genre=genre)
    return api_response(data=books)

@app.get("/api/books/genre/{genre}", response_model=APIResponse)
def get_books_by_genre(
    genre: str,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    books = crud_books.get_books(db, genre=genre)
    return api_response(data=books)

@app.get("/api/books/{book_id}", response_model=APIResponse)
def get_book(
    book_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    book = crud_books.get_book_by_id(db, book_id)
    if not book:
        return api_response(error="Book not found")
    return api_response(data=book)

# ========== ИЗБРАННОЕ ==========
@app.get("/api/favorites", response_model=APIResponse)
def get_favorites(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    favorites = crud_books.get_user_favorites(db, current_user.Id_пользователя)
    return api_response(data=favorites)

@app.post("/api/favorites/toggle/{book_id}", response_model=APIResponse)
def toggle_favorite(
    book_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    favorite_data = FavoriteToggle(
        book_id=book_id,
        user_id=current_user.Id_пользователя
    )
    result = crud_books.toggle_favorite(db, favorite_data)
    
    message = "Book added to favorites" if result["action"] == "added" else "Book removed from favorites"
    return api_response(data=result, message=message)

@app.put("/api/favorites/{book_id}/status", response_model=APIResponse)
def update_status(
    book_id: int,
    status_update: StatusUpdate,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Маппим строковый статус в ID
    status_map = {
        "want-to-read": 1,
        "reading": 2,
        "completed": 3
    }
    
    status_id = status_update.status_id  # фронт должен отправлять ID
    
    result = crud_books.update_favorite_status_by_book(
        db,
        book_id=book_id,
        user_id=current_user.Id_пользователя,
        status_id=status_id
    )
    
    if not result:
        return api_response(error="Book not found in favorites")
    
    return api_response(
        data={"status_id": status_id},
        message="Status updated successfully"
    )

@app.put("/api/favorites/{book_id}/rating", response_model=APIResponse)
def update_rating(
    book_id: int,
    rating_update: RatingUpdate,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if rating_update.rating < 1 or rating_update.rating > 5:
        return api_response(error="Rating must be between 1 and 5")
    
    result = crud_books.update_favorite_rating_by_book(
        db,
        book_id=book_id,
        user_id=current_user.Id_пользователя,
        rating=rating_update.rating
    )
    
    if not result:
        return api_response(error="Book not found in favorites")
    
    return api_response(
        data={"rating": rating_update.rating},
        message="Rating updated successfully"
    )

@app.delete("/api/favorites/{book_id}", response_model=APIResponse)
def remove_favorite(
    book_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud_books.remove_from_favorites_by_book(
        db,
        book_id=book_id,
        user_id=current_user.Id_пользователя
    )
    
    if not success:
        return api_response(error="Book not found in favorites")
    
    return api_response(message="Book removed from favorites")

# Health check
@app.get("/api/health")
def health_check():
    return api_response(message="BookApp API is running")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)