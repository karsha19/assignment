from pydantic_settings import BaseSettings
from typing import List, Optional
import json
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "okDriver CCTV Platform"
    ENV: str = "development"

    DATABASE_URL: Optional[str] = None
    MYSQL_HOST: str = "mysql"
    MYSQL_PORT: str = "3306"
    MYSQL_USER: str = "okdriver"
    MYSQL_PASSWORD: str = "okdriver"
    MYSQL_DATABASE: str = "okdriver"

    JWT_SECRET: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    HEARTBEAT_OFFLINE_SECONDS: int = 120
    HEARTBEAT_DEGRADED_SECONDS: int = 45
    WATCHLIST_MATCH_CONFIDENCE_MIN: float = 0.85
    WATCHLIST_FUZZY_THRESHOLD: float = 0.90
    MEDIA_DIR: Optional[str] = None

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        origins: List[str] = []
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return origins

        items: List[str] = []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    items = [str(x) for x in parsed]
                else:
                    items = [raw]
            except Exception:
                items = [raw]
        else:
            items = [x.strip() for x in raw.split(",") if x.strip()]

        for o in items:
            o = o.strip().strip('"').strip("'")
            if not o:
                continue
            if not (o.startswith("http://") or o.startswith("https://")):
                if "localhost" in o or o.startswith("127."):
                    o = f"http://{o}"
                else:
                    o = f"https://{o}"
            origins.append(o)
        return origins

    @property
    def resolved_media_dir(self) -> str:
        if self.MEDIA_DIR:
            return self.MEDIA_DIR
        repo_root = Path(__file__).resolve().parents[3]
        docker_baked_path = Path("/media/sample")
        if docker_baked_path.is_dir():
            return str(docker_baked_path)
        return str(repo_root / "data" / "sample")

    class Config:
        env_file = str(Path(__file__).resolve().parents[3] / ".env")
        extra = "ignore"


settings = Settings()

