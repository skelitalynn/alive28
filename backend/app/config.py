from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "alive-mvp"
    version: str = "mvp-1.0.0"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./alive.db")
    default_timezone: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Shanghai")
    challenge_id: int = int(os.getenv("CHALLENGE_ID", "1"))
    llm_provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")
    llm_model: str = os.getenv("DEFAULT_MODEL", "deepseek-chat")

settings = Settings()
