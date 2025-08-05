from unittest.mock import Mock, AsyncMock, patch, MagicMock

import aiohttp
import pytest

from app.models.pydantic.process_data.external_api_response import ExternalAPIResponse
from app.models.pydantic.process_data.process_data_response import ProcessDataResponse
from app.services.database import Database
from app.services.logging_service.service import LoggingService
from app.services.process_data_service.service import ProcessDataService


class TestProcessDataService:
    @pytest.fixture
    def mock_database(self):
        """Mock Database instance for testing"""
        mock_db = Mock(spec=Database)
        mock_session = Mock()

        # Properly mock the context manager
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_db.get_db.return_value = mock_context

        return mock_db, mock_session

    @pytest.fixture
    def mock_logging_service(self, mock_database):
        """Create LoggingService with mocked database"""
        db, session = mock_database
        return LoggingService(db, enabled=True)

    @pytest.fixture
    def service(self, mock_logging_service):
        """Create ProcessDataService with mocked logging service"""
        return ProcessDataService(mock_logging_service)

    @pytest.mark.asyncio
    async def test_fetch_cat_fact_success(self, service):
        mock_response_data = {"fact": "Cats are awesome!", "length": 18}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.raise_for_status = Mock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value = mock_client
            mock_session.return_value.__aexit__.return_value = None

            result = await service.fetch_cat_fact()

            assert isinstance(result, ExternalAPIResponse)
            assert result.fact == "Cats are awesome!"
            assert result.length == 18

    @pytest.mark.asyncio
    async def test_fetch_cat_fact_http_error(self, service):
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
                request_info=Mock(), history=(), status=500
            )

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value = mock_client
            mock_session.return_value.__aexit__.return_value = None

            with pytest.raises(aiohttp.ClientResponseError):
                await service.fetch_cat_fact()

    @pytest.mark.asyncio
    async def test_process_incoming_data_success(self, service, mock_database):
        db, session = mock_database
        input_data = {"test": "data", "number": 42}
        mock_cat_fact = ExternalAPIResponse(fact="Test fact", length=9)

        with patch.object(service, 'fetch_cat_fact', return_value=mock_cat_fact):
            result = await service.process_incoming_data(input_data)

            assert isinstance(result, ProcessDataResponse)
            assert result.received_data == input_data
            assert result.cat_fact == {"fact": "Test fact", "length": 9}

            # Verify logging was called (database operations)
            session.add.assert_called_once()
            session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_incoming_data_external_api_failure(self, service, mock_database):
        db, session = mock_database
        input_data = {"test": "data"}
        error_message = "External API failed"

        with patch.object(service, 'fetch_cat_fact', side_effect=Exception(error_message)):
            with pytest.raises(Exception) as exc_info:
                await service.process_incoming_data(input_data)

            assert str(exc_info.value) == error_message

            # Verify logging was called even on error
            session.add.assert_called_once()
            session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_incoming_data_preserves_original_exception(self, service, mock_database):
        db, session = mock_database
        input_data = {"test": "data"}
        original_exception = ValueError("Custom error")

        with patch.object(service, 'fetch_cat_fact', side_effect=original_exception):
            with pytest.raises(ValueError) as exc_info:
                await service.process_incoming_data(input_data)

            # Verify the original exception is preserved
            assert exc_info.value is original_exception

            # Verify logging was attempted
            session.add.assert_called_once()
            session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_incoming_data_with_disabled_logging(self):
        """Test ProcessDataService with logging disabled"""
        # Create service with logging disabled
        logging_service = LoggingService(db=None, enabled=False)
        service = ProcessDataService(logging_service)

        input_data = {"test": "data"}
        mock_cat_fact = ExternalAPIResponse(fact="Test fact", length=9)

        with patch.object(service, 'fetch_cat_fact', return_value=mock_cat_fact):
            result = await service.process_incoming_data(input_data)

            assert isinstance(result, ProcessDataResponse)
            assert result.received_data == input_data
            assert result.cat_fact == {"fact": "Test fact", "length": 9}
            # No database operations should occur when logging is disabled
