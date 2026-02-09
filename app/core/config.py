from pydantic_settings import BaseSettings, SettingsConfigDict

from functools import lru_cache

class Settings(BaseSettings):
    """沙箱API服务基础信息配置"""
    log_level: str = "INFO" #日志等级
    server_timeout_minutes: int = 60  # 服务超时的时间

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()