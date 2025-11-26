from pydantic import BaseModel
from typing import Optional, List

class BookBase(BaseModel):
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    pages: Optional[int] = None

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: int
    
    class Config:
        from_attributes = True

class FavoriteBase(BaseModel):
    book_id: int
    user_id: int
    status: str

class FavoriteCreate(FavoriteBase):
    pass

class FavoriteResponse(FavoriteBase):
    id: int
    favorite_id: int
    
    class Config:
        from_attributes = True

class FavoriteToggle(BaseModel):
    book_id: int
    user_id: int

class StatusUpdate(BaseModel):
    status: str

class RatingUpdate(BaseModel):
    rating: int