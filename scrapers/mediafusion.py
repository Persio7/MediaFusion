from datetime import timedelta
from typing import Dict, Any, Optional, List

import PTT

from db.config import settings
from db.models import MediaFusionMetaData, TorrentStreams
from scrapers.stremio_addons import StremioScraper
from utils.parser import convert_size_to_bytes
from utils.runtime_const import MEDIAFUSION_SEARCH_TTL


class MediafusionScraper(StremioScraper):
    def __init__(self):
        super().__init__(
            cache_key_prefix="mediafusion",
            base_url=settings.mediafusion_url,
            logger_name=__name__,
        )

    @StremioScraper.cache(ttl=MEDIAFUSION_SEARCH_TTL)
    @StremioScraper.rate_limit(calls=5, period=timedelta(seconds=1))
    async def _scrape_and_parse(
        self,
        metadata: MediaFusionMetaData,
        catalog_type: str,
        season: Optional[int] = None,
        episode: Optional[int] = None,
    ) -> List[TorrentStreams]:
        return await super()._scrape_and_parse(metadata, catalog_type, season, episode)

    def get_adult_content_field(self, stream_data: Dict[str, Any]) -> str:
        return stream_data["description"]

    def get_scraper_name(self) -> str:
        return "Mediafusion"

    def parse_stream_title(self, stream: dict) -> dict:
        description = stream["description"].splitlines()
        torrent_name = description[0]
        metadata = PTT.parse_title(torrent_name, True)

        addon_name = stream["name"].split()[0].title()
        source = description[-1].removeprefix("🔗 ")
        if addon_name not in source:
            source = f"{addon_name} | {source}"

        return {
            "torrent_name": torrent_name,
            "title": metadata.get("title"),
            "size": convert_size_to_bytes(
                self.extract_size_string(stream["description"])
            ),
            "seeders": self.extract_seeders(stream["description"]),
            "languages": metadata.get("languages", []),
            "metadata": metadata,
            "file_name": (stream.get("behaviorHints", {}).get("filename")),
            "source": source,
        }
