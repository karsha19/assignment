from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "okDriver CCTV Platform"
    ENV: str = "development"

    # Preferred: a full SQLAlchemy URL. If not set, it is built from the
    # MYSQL_* parts below -- this lets a platform like Render inject host
    # and port from a separate database service without needing string
    # interpolation in its blueprint config.
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

    # Directory the backend serves sample videos from at /media/sample/*.
    # If unset, it's auto-detected: inside the Docker image the Dockerfile
    # bakes videos at /media/sample, so that path is used when it exists;
    # otherwise (running from source, e.g. `uvicorn` directly on Windows/
    # macOS/Linux) it falls back to <repo root>/data/sample, which works
    # cross-platform because pathlib resolves it to a native path.
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
        origins = []
        for o in self.CORS_ORIGINS.split(","):
            o = o.strip()
            if not o:
                continue
            # Render's fromService "host" property returns a bare hostname
            # (no scheme). Accept that form and assume HTTPS, since every
            # Render web service is served over TLS.
            if not o.startswith("http://") and not o.startswith("https://"):
                o = f"https://{o}"
            origins.append(o)
        return origins

    @property
    def resolved_media_dir(self) -> str:
        if self.MEDIA_DIR:
            return self.MEDIA_DIR
        # backend/app/core/config.py -> parents[2] is backend/, parents[3] is repo root
        repo_root = Path(__file__).resolve().parents[3]
        docker_baked_path = Path("/media/sample")
        if docker_baked_path.is_dir():
            return str(docker_baked_path)
        return str(repo_root / "data" / "sample")

    class Config:
        env_file = str(Path(__file__).resolve().parents[3] / ".env")
        extra = "ignore"


settings = Settings()

