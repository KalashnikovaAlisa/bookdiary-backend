from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API работает!"}

@app.get("/api/health")
def health_check():
    return {"status": "OK", "message": "BookApp API запущен"}

@app.get("/api/books")
def get_books():
    return [
        {"id": 1, "title": "Война и мир", "author": "Лев Толстой", "genre": "Классика"},
        {"id": 2, "title": "Преступление и наказание", "author": "Фёдор Достоевский", "genre": "Классика"},
        {"id": 3, "title": "Руслан и Людмила", "author": "Александр Пушкин", "genre": "Поэзия"}
    ]

@app.post("/api/favorites/toggle")
def toggle_favorite(book_id: int, user_id: int):
    return {"action": "added", "book_id": book_id, "user_id": user_id}

@app.put("/api/favorites/{favorite_id}/status")
def update_status(favorite_id: int, status: str):
    return {"message": f"Статус обновлен на {status}", "favorite_id": favorite_id}