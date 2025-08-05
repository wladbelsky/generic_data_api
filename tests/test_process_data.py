from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.pydantic.process_data.external_api_response import ExternalAPIResponse
from app.services.database import Database


@pytest.fixture
def mock_database():
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
def client():
    return TestClient(app)


@pytest.fixture
def mock_cat_fact():
    return ExternalAPIResponse(fact="Cats are awesome!", length=18)


@pytest.fixture(autouse=True)
def mock_database_dependency(mock_database):
    """Automatically mock the database dependency for all tests"""
    db, session = mock_database
    with patch('app.services.database.Database', return_value=db), \
            patch('app.services.database.get_database', return_value=db), \
            patch('app.services.logging_service.service.get_database', return_value=db), \
            patch('app.services.logging_service.service.Database', return_value=db):
        yield db, session


class TestProcessDataEndpoint:
    def test_process_data_success(self, client, mock_cat_fact, mock_database_dependency):
        db, session = mock_database_dependency
        payload = {"test": "data", "number": 42}

        with patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                   return_value=mock_cat_fact):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["received_data"] == payload
            assert data["cat_fact"]["fact"] == "Cats are awesome!"
            assert data["cat_fact"]["length"] == 18

            # Verify logging occurred via database operations
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_process_data_with_complex_payload(self, client, mock_cat_fact, mock_database_dependency):
        db, session = mock_database_dependency
        payload = {
            "user": {"name": "John", "age": 30},
            "items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
            "metadata": {"timestamp": "2025-01-01T00:00:00Z"}
        }

        with patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                   return_value=mock_cat_fact):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["received_data"] == payload

            # Verify logging occurred
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_process_data_external_api_error(self, client, mock_database_dependency):
        db, session = mock_database_dependency
        payload = {"test": "data"}

        with patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                   side_effect=Exception("External API failed")):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 500
            assert response.json()["detail"] == "An unexpected error occurred"

            # Verify error logging occurred
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_process_data_http_client_error(self, client, mock_database_dependency):
        from aiohttp.client_exceptions import ClientResponseError
        db, session = mock_database_dependency
        payload = {"test": "data"}

        mock_request_info = Mock()
        error = ClientResponseError(request_info=mock_request_info, history=(), status=404)

        with patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                   side_effect=error):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 502

            # Verify error logging occurred
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_process_data_validation_error(self, client, mock_database_dependency):
        from pydantic import ValidationError
        db, session = mock_database_dependency
        payload = {"test": "data"}

        # Create a proper ValidationError with correct structure
        error = ValidationError.from_exception_data("ExternalAPIResponse", [
            {
                'type': 'missing',
                'loc': ('fact',),
                'msg': 'Field required',
                'input': {},
            }
        ])

        with patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                   side_effect=error):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 502

            # Verify error logging occurred
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_process_data_empty_payload(self, client, mock_cat_fact, mock_database_dependency):
        db, session = mock_database_dependency
        payload = {}

        with patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                   return_value=mock_cat_fact):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["received_data"] == {}

            # Verify logging occurred
            session.add.assert_called_once()
            session.commit.assert_called_once()

    def test_process_data_invalid_json(self, client):
        response = client.post("/process_data", data="invalid json")
        assert response.status_code == 422  # Unprocessable Entity

    def test_process_data_with_logging_disabled(self, client, mock_cat_fact):
        """Test endpoint with logging disabled via environment variable"""
        payload = {"test": "data"}

        # Mock the environment variable and the get_logging_service function
        with patch('app.services.logging_service.service.os.getenv', return_value="false"), \
                patch('app.services.process_data_service.service.ProcessDataService.fetch_cat_fact',
                      return_value=mock_cat_fact):
            response = client.post("/process_data", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["received_data"] == payload
            # No database operations should occur when logging is disabled


class TestAppLifespan:
    def test_app_startup(self):
        # Test that the app can be created without errors
        from app.main import app
        assert app is not None

    def test_exception_handler(self, client, mock_database_dependency):
        db, session = mock_database_dependency
        # Test the global exception handler by triggering an unhandled exception
        with patch('app.services.process_data_service.service.ProcessDataService.process_incoming_data',
                   side_effect=RuntimeError("Unhandled error")):
            response = client.post("/process_data", json={"test": "data"})
            assert response.status_code == 500
            assert response.json()["detail"] == "An unexpected error occurred"
