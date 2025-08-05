from aiohttp.client_exceptions import ClientResponseError, ClientConnectionError
from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError

from app.models.pydantic.process_data.process_data_response import ProcessDataResponse
from app.services.process_data_service.service import ProcessDataService, get_process_data_service

router = APIRouter()


@router.post('/process_data', response_model=ProcessDataResponse)
async def process_data(request: dict,
                       service: ProcessDataService = Depends(get_process_data_service)) -> ProcessDataResponse:
    try:
        result = await service.process_incoming_data(request)
    except (ClientResponseError, ClientConnectionError, ValidationError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

    return result
