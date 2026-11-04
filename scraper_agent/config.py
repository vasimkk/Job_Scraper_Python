import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Locate and load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5433"))
    name: str = os.getenv("DB_NAME", "scraperAgent")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "root")

    @property
    def connection_string(self) -> str:
        return f"host={self.host} port={self.port} dbname={self.name} user={self.user} password={self.password}"


@dataclass(frozen=True)
class ScraperConfig:
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    user_agent: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 JobScraperAgent/1.0",
    )
    filter_tech_only: bool = os.getenv("FILTER_TECH_ONLY", "true").lower() in ("true", "1", "yes")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


DB_CONFIG = DatabaseConfig()
SCRAPER_CONFIG = ScraperConfig()

