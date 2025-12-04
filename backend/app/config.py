"""
Configuration management for Wealth Advisor.
Loads settings from environment variables.
"""
import os
from functools import lru_cache
from typing import List


class Settings:
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Wealth Advisor API"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # JWT (used for our own tokens after Supabase auth)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", "30"))
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Database - Supabase PostgreSQL or local SQLite
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./wealth_advisor.db"
    )
    
    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://localhost:3000,http://localhost:5000,https://wealth-advisor-hmadan24-gmailcoms-projects.vercel.app"
        ).split(",")
        if origin.strip()
    ]
    
    # Demo mode - allows hardcoded OTP for all users
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"
    DEMO_OTP: str = os.getenv("DEMO_OTP", "1234")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.SECRET_KEY != "dev-secret-key-change-in-production"
    
    @property
    def has_supabase(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)
    
    @property
    def use_postgres(self) -> bool:
        """Check if using PostgreSQL (Supabase or other)."""
        return "postgresql" in self.DATABASE_URL or "postgres" in self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
