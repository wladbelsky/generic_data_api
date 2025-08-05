import aiohttp
from aiohttp import ClientTimeout
from fastapi import Depends

from app.models.pydantic.process_data.external_api_response import ExternalAPIResponse
from app.models.pydantic.process_data.process_data_response import ProcessDataResponse
from app.services.logging_service.service import LoggingService, get_logging_service


class ProcessDataService:
    def __init__(self, logging_service: LoggingService):
        self.logging_service = logging_service

    @staticmethod
    async def fetch_cat_fact() -> ExternalAPIResponse:
        url = "https://catfact.ninja/fact"
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=10.0)) as client:
            response = await client.get(url)
            response.raise_for_status()
            return ExternalAPIResponse(**await response.json())

    async def process_incoming_data(self, data: dict) -> ProcessDataResponse:
        status = "success"
        error_message = None
        exc = None
        try:
            cat_fact = await self.fetch_cat_fact()
            result = ProcessDataResponse(
                received_data=data,
                cat_fact=cat_fact.model_dump(),
            )
        except Exception as e:
            status = "error"
            error_message = str(e)
            result = None
            exc = e

        await self.logging_service.log_request(
            endpoint="/process_data",
            input_data=data,
            output_data=result.model_dump() if result else None,
            status=status,
            error_message=error_message
        )
        if result is not None:
            return result
        raise exc


def get_process_data_service(logging_service: LoggingService = Depends(get_logging_service)):
    return ProcessDataService(logging_service)
