from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str = "ZTFhMjNkYWMtNjY0OC00ZjU5LTkyNjEtMjc5ZTI1NTUyMzIwYjg3Njk4YjMtMWFjNy00MWYwLWE3ZmEtNDlkYThmYzIwY2U1"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()