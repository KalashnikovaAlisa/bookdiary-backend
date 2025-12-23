from pydantic import BaseModel, Field
from typing import Optional, List, Any

class BookBase(BaseModel):
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    pages: Optional[int] = None
    coverImage: Optional[str] = Field(None, alias="cover_url")  # Добавлено для фронта
    
    class Config:
        populate_by_name = True  # Позволяет использовать alias и имя поля

class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    pages: Optional[int] = None
    cover_url: Optional[str] = None

class BookResponse(BookBase):
    id: int
    
    class Config:
        from_attributes = True
        populate_by_name = True

# Для избранных книг - специальная схема
class FavoriteBookResponse(BaseModel):
    id_избранной_книги: Optional[int] = None
    Id_книги: Optional[int] = None
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    pages: Optional[int] = None
    coverImage: Optional[str] = None
    status: Optional[str] = None  # "want-to-read", "reading", "completed"
    rating: Optional[int] = None
    favorite_id: Optional[int] = None  # id_избранной_книги
    
    class Config:
        from_attributes = True

class FavoriteToggle(BaseModel):
    book_id: int
    user_id: int

class StatusUpdate(BaseModel):
    status_id: int  # Изменили: фронт отправляет ID статуса
    
class RatingUpdate(BaseModel):
    rating: int

# Универсальный ответ API
class APIResponse(BaseModel):
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None

# Схемы для аутентификации
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Схема для поиска
class BookSearchQuery(BaseModel):
    q: Optional[str] = None
    genre: Optional[str] = None