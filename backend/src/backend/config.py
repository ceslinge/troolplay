from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432

    # En production : true (cookies seulement en HTTPS) et l'adresse du site.
    cookie_secure: bool = False
    allowed_origins: list[str] = ["http://localhost:5173"]
    site_url: str = "http://localhost:5173"

    # Les emails. Sans SMTP_HOST, ils s'affichent dans le terminal (développement).
    # Port 465 : la connexion est chiffrée dès le départ (SMTPS).
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    # L'expéditeur affiché. Par défaut, le compte SMTP lui-même.
    mail_from: str = ""

    # Le masquage automatique (charte de modération) : combien de signaleurs distincts et
    # fiables, et depuis combien de jours leur compte existe. À baisser en local pour l'essayer.
    auto_hide_reporters: int = 3
    auto_hide_min_account_days: int = 3

    # La documentation interactive de l'API (/api/docs). Éteinte par défaut : en production,
    # elle donnerait à n'importe qui la carte complète de l'API (#56).
    api_docs: bool = False

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


settings = Settings()
