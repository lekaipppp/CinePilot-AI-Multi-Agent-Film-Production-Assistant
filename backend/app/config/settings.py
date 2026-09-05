from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    GEMINI_MODEL: str = "gemini-3.5-flash"


settings = Settings()
