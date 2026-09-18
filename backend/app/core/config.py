from pydantic_settings import BaseSettings
from typing import List, Optional


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

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

