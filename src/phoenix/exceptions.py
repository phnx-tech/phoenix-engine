"""Custom exceptions for Phoenix Engine."""

from __future__ import annotations


class PhoenixError(Exception):
    """Base exception for all Phoenix Engine errors."""


class ScrapingError(PhoenixError):
    """Raised when a scraping operation fails."""


class RetryableError(ScrapingError):
    """Raised for transient failures that may succeed on retry."""


class HTTPError(ScrapingError):
    """Raised when an HTTP request returns a client or server error."""


class BrowserError(ScrapingError):
    """Raised when browser automation fails."""


class RateLimitExceededError(ScrapingError):
    """Raised when a request is blocked by a rate limit."""


class AntiBotDetectedError(ScrapingError):
    """Raised when a page is identified as a CAPTCHA or anti-bot challenge."""


class UnsupportedURLError(PhoenixError):
    """Raised when no scraper can handle a URL."""


class ConfigurationError(PhoenixError):
    """Raised when configuration is invalid."""


class LicenseError(PhoenixError):
    """Base exception for license-key errors."""


class LicenseInvalidError(LicenseError):
    """Raised when a license key is malformed or has an invalid signature."""


class LicenseExpiredError(LicenseError):
    """Raised when a license key has passed its expiration date."""


class LicenseUsesExceededError(LicenseError):
    """Raised when a license key has exceeded its maximum use count."""


class LicenseMissingError(LicenseError):
    """Raised when a license key is required but not provided."""


__all__ = [
    "AntiBotDetectedError",
    "BrowserError",
    "ConfigurationError",
    "HTTPError",
    "LicenseError",
    "LicenseExpiredError",
    "LicenseInvalidError",
    "LicenseMissingError",
    "LicenseUsesExceededError",
    "PhoenixError",
    "RateLimitExceededError",
    "RetryableError",
    "ScrapingError",
    "UnsupportedURLError",
]
