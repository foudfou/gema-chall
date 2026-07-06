"""Work-Catalog-API client."""

import hashlib

from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.models import WorkDetails


class WorkCatalogClient:
    """
    Base class for Work-Catalog-API clients.

    For async implementation, you would:
    1. Create an AsyncWorkCatalogClient with:
           async def get_work_details(self, isrc_code: str) -> WorkDetails: ...
    2. Inject an httpx.AsyncClient into the concrete implementation
    3. Use asyncio.gather() in processor for parallel enrichment within a chunk
    """

    def get_work_details(self, isrc_code: str) -> WorkDetails:
        """Fetch work details for a given ISRC code."""
        raise NotImplementedError


class FakeWorkCatalogClient(WorkCatalogClient):
    """Fake implementation for testing and development."""

    MOCK_CATALOG: dict[str, WorkDetails] = {
        "USRC17607839": WorkDetails(
            artist="Taylor Swift",
            title="Shake It Off",
            rights_holder="Universal Music",
        ),
        "DEFR32400001": WorkDetails(
            artist="Kraftwerk",
            title="Autobahn",
            rights_holder="Kling Klang",
        ),
        "GBAYE6700012": WorkDetails(
            artist="The Beatles",
            title="Hey Jude",
            rights_holder="Apple Records",
        ),
    }

    def get_work_details(self, isrc_code: str) -> WorkDetails:
        if isrc_code in self.MOCK_CATALOG:
            return self.MOCK_CATALOG[isrc_code]
        return self._generate_fallback(isrc_code)

    @staticmethod
    def _generate_fallback(isrc_code: str) -> WorkDetails:
        """Generate deterministic fake data for unknown ISRCs."""
        h = hashlib.md5(isrc_code.encode()).hexdigest()
        return WorkDetails(
            artist=f"Artist-{h[:6]}",
            title=f"Track-{h[6:12]}",
            rights_holder=f"Label-{h[12:18]}",
        )


class HttpWorkCatalogClient(WorkCatalogClient):
    """
    HTTP implementation for production use.

    Example usage:
        import httpx
        client = HttpWorkCatalogClient(
            http_client=httpx.Client(base_url="https://api.gema.de"),
        )

    For async, this would become:
        class AsyncHttpWorkCatalogClient(AsyncWorkCatalogClient):
            def __init__(self, http_client: httpx.AsyncClient):
                self.http_client = http_client

            @retry(...)
            async def get_work_details(self, isrc_code: str) -> WorkDetails:
                resp = await self.http_client.get(f"/v1/works/{isrc_code}")
                resp.raise_for_status()
                return WorkDetails(**resp.json())
    """

    def __init__(self, http_client):  # httpx.Client
        self.http_client = http_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=2),
        reraise=True,
    )
    def get_work_details(self, isrc_code: str) -> WorkDetails:
        resp = self.http_client.get(f"/v1/works/{isrc_code}")
        resp.raise_for_status()
        return WorkDetails(**resp.json())
