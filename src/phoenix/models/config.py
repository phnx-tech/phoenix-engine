"""Configuration model."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PhoenixAIConfig(BaseModel):
    """Phoenix AI (local Ollama) configuration."""

    api_key: str | None = Field(
        default="ollama",
        description="API key for the AI endpoint. Ollama ignores this value.",
    )
    base_url: str = Field(
        default="http://localhost:11434/v1",
        description="OpenAI-compatible base URL for the local AI server.",
    )
    model: str = Field(
        default="qwen2.5:7b",
        description="Default model for Phoenix AI extraction.",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature.",
    )
    max_tokens: int = Field(
        default=8192,
        ge=1,
        description="Maximum tokens per response.",
    )
    timeout: float = Field(
        default=30.0,
        gt=0.0,
        description="AI request timeout in seconds.",
    )
    cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Response cache TTL in seconds.",
    )
    max_budget_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Maximum estimated AI spend in USD (0 = unlimited).",
    )


class Config(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="PHOENIX_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    timeout: float = Field(default=30.0, description="Default request timeout in seconds.")
    max_redirects: int = Field(default=5, description="Maximum redirects to follow.")
    browser_timeout: float = Field(
        default=60.0,
        description="Browser navigation timeout in seconds.",
    )
    archive_enabled: bool = Field(default=True, description="Enable source archiving.")
    data_dir: str = Field(
        default=".phoenix",
        description="Directory for local JSON fallback stores.",
    )
    learning_memory_enabled: bool = Field(
        default=True,
        description="Enable persistent per-domain learning memory.",
    )
    rate_limits: dict[str, float] = Field(
        default_factory=dict,
        description="Per-domain or per-platform rate limits in requests per second.",
    )
    change_detection_enabled: bool = Field(
        default=True,
        description="Enable structural drift and selector degradation alerts.",
    )
    change_alert_size_threshold: float = Field(
        default=0.3,
        ge=0.0,
        description="Fractional HTML size delta that triggers a change alert.",
    )
    change_alert_webhook_url: str | None = Field(
        default=None,
        description="Optional webhook URL for change alerts.",
    )
    license_key: str | None = Field(
        default=None,
        description="License key for this Phoenix Engine instance.",
    )
    license_secret: str | None = Field(
        default=None,
        description="HMAC secret used to sign/validate license keys. Keep private.",
    )
    license_enforcement_enabled: bool = Field(
        default=False,
        description="Require a valid license key before the engine can be used.",
    )
    ai_enabled: bool = Field(
        default=False,
        description="Enable Phoenix AI-assisted extraction fallback.",
    )
    ai_api_key: str | None = Field(
        default="ollama",
        description="API key for Phoenix AI (Ollama ignores this value).",
    )
    ai_base_url: str = Field(
        default="http://localhost:11434/v1",
        description="OpenAI-compatible base URL for Phoenix AI.",
    )
    ai_model: str = Field(
        default="qwen2.5:7b",
        description="Default Phoenix AI model.",
    )
    ai_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Phoenix AI sampling temperature.",
    )
    ai_max_tokens: int = Field(
        default=8192,
        ge=1,
        description="Maximum tokens per Phoenix AI response.",
    )
    ai_timeout: float = Field(
        default=30.0,
        gt=0.0,
        description="Phoenix AI request timeout in seconds.",
    )
    ai_cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Phoenix AI response cache TTL in seconds.",
    )
    ai_max_budget_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Maximum estimated Phoenix AI spend in USD (0 = unlimited).",
    )

    # Stealth / anti-detection settings
    stealth_enabled: bool = Field(
        default=False,
        description="Enable anti-detection browser profiles and behavior.",
    )
    stealth_profiles: list[str] = Field(
        default_factory=lambda: ["chrome_windows"],
        description="List of stealth profile presets to rotate through.",
    )
    stealth_rotation_policy: str = Field(
        default="round_robin",
        description="Profile rotation policy: 'round_robin' or 'random'.",
    )
    proxy_list: list[str] = Field(
        default_factory=list,
        description="List of upstream proxy URLs (http://host:port or http://user:pass@host:port).",
    )
    proxy_rotation_policy: str = Field(
        default="round_robin",
        description="Proxy rotation policy: 'round_robin' or 'random'.",
    )
    delay_min_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum human-like delay before/after browser navigation in milliseconds.",
    )
    delay_max_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Maximum human-like delay before/after browser navigation in milliseconds.",
    )
    warm_session: bool = Field(
        default=False,
        description="Warm browser sessions by visiting benign sites before the target.",
    )
    captcha_detection_enabled: bool = Field(
        default=False,
        description="Enable heuristic CAPTCHA / anti-bot challenge detection.",
    )
    captcha_action: str = Field(
        default="flag",
        description="Action on CAPTCHA detection: 'flag', 'raise', or 'skip'.",
    )

    @property
    def phoenix_ai(self) -> PhoenixAIConfig:
        """Return a :class:`PhoenixAIConfig` derived from flattened settings."""
        return PhoenixAIConfig(
            api_key=self.ai_api_key,
            base_url=self.ai_base_url,
            model=self.ai_model,
            temperature=self.ai_temperature,
            max_tokens=self.ai_max_tokens,
            timeout=self.ai_timeout,
            cache_ttl=self.ai_cache_ttl,
            max_budget_usd=self.ai_max_budget_usd,
        )


__all__ = ["Config", "PhoenixAIConfig"]
