"""Platform adapters that parse HTML into structured data."""

from __future__ import annotations

from phoenix.adapters.base import BaseAdapter, PluginInterface, ScraperPlugin
from phoenix.adapters.facebook import FacebookAdapter
from phoenix.adapters.generic import GenericWebAdapter
from phoenix.adapters.instagram import InstagramAdapter
from phoenix.adapters.linkedin import LinkedInAdapter
from phoenix.adapters.tiktok import TikTokAdapter
from phoenix.adapters.x_twitter import XTwitterAdapter
from phoenix.adapters.youtube import YouTubeAdapter

__all__ = [
    "BaseAdapter",
    "FacebookAdapter",
    "GenericWebAdapter",
    "InstagramAdapter",
    "LinkedInAdapter",
    "PluginInterface",
    "ScraperPlugin",
    "TikTokAdapter",
    "XTwitterAdapter",
    "YouTubeAdapter",
]
