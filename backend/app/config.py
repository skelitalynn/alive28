from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "alive-mvp"
    version: str = "mvp-1.0.0"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./alive.db")
    default_timezone: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Shanghai")
    challenge_id: int = int(os.getenv("CHALLENGE_ID", "1"))
    chain_id: int = int(os.getenv("CHAIN_ID", "11155111"))
    proof_registry_address: str = os.getenv("PROOF_REGISTRY_ADDRESS", "0x0000000000000000000000000000000000000000")
    milestone_nft_address: str = os.getenv("MILESTONE_NFT_ADDRESS", "0x0000000000000000000000000000000000000000")
    milestone_base_uri: str = os.getenv("MILESTONE_BASE_URI", "https://api.YOUR_DOMAIN/metadata/")
    llm_provider: str = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")
    llm_model: str = os.getenv("DEFAULT_MODEL", "deepseek-chat")
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    demo_start_date_key: str = os.getenv("DEMO_START_DATE_KEY", "")

settings = Settings()
