from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "face_recognition"
    RECOGNITION_TOLERANCE: float = 0.6

    model_config = {"env_file": ".env"}


settings = Settings()
