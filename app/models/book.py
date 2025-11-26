from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Пользователь(Base):
    __tablename__ = "Пользователь"
    
    Id_пользователя = Column(Integer, primary_key=True, index=True)
    Имя_пользователя = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Жанры(Base):
    __tablename__ = "Жанры"
    
    id_жанра = Column(Integer, primary_key=True, index=True)
    Наименование_жанра = Column(String, nullable=False)

class Авторы(Base):
    __tablename__ = "Авторы"
    
    Id_автора = Column(Integer, primary_key=True, index=True)
    Имя_автора = Column(String, nullable=False)
    Фамилия_автора = Column(String, nullable=False)

class Статус(Base):
    __tablename__ = "Статус"
    
    Id_статуса = Column(Integer, primary_key=True, index=True)
    Наименование_статуса = Column(String, nullable=False)

class Книги(Base):
    __tablename__ = "Книги"
    
    Id_книги = Column(Integer, primary_key=True, index=True)
    Название_книги = Column(String(255), nullable=False)
    Автор = Column(Integer, ForeignKey("Авторы.Id_автора"))
    URL_обложки = Column(String(500))
    Кол_во_страниц = Column(Integer)
    Жанр = Column(Integer, ForeignKey("Жанры.id_жанра"))
    Описание = Column(Text)
    
    автор_rel = relationship("Авторы")
    жанр_rel = relationship("Жанры")

class Избранные_книги(Base):
    __tablename__ = "Избранные_книги"
    
    id_избранной_книги = Column(Integer, primary_key=True, index=True)
    Книга = Column(Integer, ForeignKey("Книги.Id_книги"))
    Пользователь = Column(Integer, ForeignKey("Пользователь.Id_пользователя"))
    Статус_книги = Column(Integer, ForeignKey("Статус.Id_статуса"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    книга_rel = relationship("Книги")
    пользователь_rel = relationship("Пользователь")
    статус_rel = relationship("Статус")

class Отзывы_пользователя(Base):
    __tablename__ = "Отзывы_пользователя"
    
    id_отзыва = Column(Integer, primary_key=True, index=True)
    Дата_отзыва = Column(DateTime(timezone=True), server_default=func.now())
    Избранная_книга = Column(Integer, ForeignKey("Избранные_книги.id_избранной_книги"))
    Оценка = Column(Integer)
    Комментарий = Column(String(1000))
    
    __table_args__ = (
        CheckConstraint('Оценка >= 1 AND Оценка <= 5', name='check_rating_range'),
    )
    
    избранная_книга_rel = relationship("Избранные_книги")