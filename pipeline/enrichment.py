"""Work-Catalog-API client."""

import hashlib

from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.models import WorkDetails


class WorkCatalogClient:
    """
    Base class for Work-Catalog-API clients.

    For async implementation, you would:
    1. Create an AsyncWorkCatalogClient with:
           async def get_work_details_batch(...) -> dict[str, WorkDetails]: ...
    2. Inject an httpx.AsyncClient into the concrete implementation
    """

    def get_work_details_batch(
        self, isrc_codes: list[str]
    ) -> dict[str, WorkDetails]:
        """
        Fetch work details for multiple ISRC codes in one call.

        Returns a dict mapping ISRC code to WorkDetails.
        Missing ISRCs are omitted from the result.
        """
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

    def get_work_details_batch(
        self, isrc_codes: list[str]
    ) -> dict[str, WorkDetails]:
        return {
            isrc: self.MOCK_CATALOG.get(isrc) or self._generate_fallback(isrc)
            for isrc in isrc_codes
        }

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
            async def get_work_details_batch(self, isrc_code: str) -> dict[str, WorkDetails]:
                resp = await self.http_client.post(...)
                # ...
    """

    def __init__(self, http_client):  # httpx.Client
        self.http_client = http_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=2),
        reraise=True,
    )
    def get_work_details_batch(
        self, isrc_codes: list[str]
    ) -> dict[str, WorkDetails]:
        resp = self.http_client.post(
            "/v1/works/batch",
            json={"isrc_codes": isrc_codes},
        )
        resp.raise_for_status()
        return {
            isrc: WorkDetails(**details)
            for isrc, details in resp.json().items()
        }
