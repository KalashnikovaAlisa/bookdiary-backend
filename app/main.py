from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional

# ПРАВИЛЬНЫЕ ИМПОРТЫ
from app.database import get_db, engine
from app.models.book import Base
from app.schemas.book import BookCreate, BookResponse, FavoriteToggle, StatusUpdate, RatingUpdate
from app.crud import books as crud_books

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookApp API", version="1.0.0")

# CORS для Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Эндпоинты книг
@app.get("/api/books", response_model=List[BookResponse])
def get_all_books(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    books = crud_books.get_books(db, skip=skip, limit=limit, search=search, genre=genre)
    return books

@app.post("/api/books", response_model=BookResponse)
def add_book(book: BookCreate, db: Session = Depends(get_db)):
    return crud_books.create_book(db, book)

@app.get("/api/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud_books.get_book_by_id(db, book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book

# Эндпоинты избранного
@app.get("/api/favorites")
def get_favorites(user_id: int, db: Session = Depends(get_db)):
    favorites = crud_books.get_user_favorites(db, user_id)
    return favorites

@app.post("/api/favorites/toggle")
def toggle_favorite(favorite_data: FavoriteToggle, db: Session = Depends(get_db)):
    return crud_books.toggle_favorite(db, favorite_data)

@app.put("/api/favorites/{favorite_id}/status")
def update_status(favorite_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)):
    result = crud_books.update_favorite_status(db, favorite_id, status_update.status)
    if not result:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Status updated successfully"}

@app.put("/api/favorites/{favorite_id}/rating")
def update_rating(favorite_id: int, rating_update: RatingUpdate, db: Session = Depends(get_db)):
    if rating_update.rating < 1 or rating_update.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    result = crud_books.update_favorite_rating(db, favorite_id, rating_update.rating)
    if not result:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Rating updated successfully"}

@app.delete("/api/favorites/{favorite_id}")
def remove_favorite(favorite_id: int, db: Session = Depends(get_db)):
    success = crud_books.remove_from_favorites(db, favorite_id)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Book removed from favorites"}

# Health check
@app.get("/api/health")
def health_check():
    return {"status": "OK", "message": "BookApp API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)