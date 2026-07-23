"""Application configuration.

Usage:
    from app.core.config import settings

    db_url = settings.database_url
"""

from app.core.config.settings import AppSettings, Environment, get_settings, settings

__all__ = ["AppSettings", "Environment", "get_settings", "settings"]
