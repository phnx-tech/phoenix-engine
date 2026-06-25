from phoenix.adapters.base import BaseAdapter, UnifiedOutput
from phoenix.plugins.manifest import PluginManifest
import json
from bs4 import BeautifulSoup

class QuotesToScrapeAdapter(BaseAdapter):
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            platform_name="quotes",
            site_type="e_commerce|news|jobs|generic",
            data_fields=["title", "text", "author"],
            data_location="__NEXT_DATA__|JSON-LD|meta_tags|css_selectors",
            url_patterns=[],
            notes=""
        )

    def extract(self, raw_response: str) -> UnifiedOutput:
        soup = BeautifulSoup(raw_response, 'html.parser')

        quotes = []
        for quote in soup.find_all('div', class_='quote'):
            title = quote.find('span', class_='text').get_text()
            author = quote.find('small', class_='author').get_text().split(':')[1].strip()

            quote_dict = {
                'title': title,
                'text': '',  # Not available in the HTML sample
                'author': author
            }
            quotes.append(quote_dict)

        return UnifiedOutput(data=quotes)