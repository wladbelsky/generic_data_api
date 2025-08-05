from unittest.mock import Mock, MagicMock

import pytest

from app.services.database import Database
from app.services.logging_service.service import LoggingService


class TestLoggingService:
    @pytest.fixture
    def mock_database(self):
        """Mock Database instance for testing"""
        mock_db = Mock(spec=Database)
        mock_session = Mock()

        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_db.get_db.return_value = mock_context

        return mock_db, mock_session

    @pytest.mark.asyncio
    async def test_log_request_enabled(self, mock_database):
        db, session = mock_database
        service = LoggingService(db, enabled=True)

        input_data = {"test": "data"}
        output_data = {"result": "success"}

        log_id = await service.log_request(
            endpoint="/test",
            input_data=input_data,
            output_data=output_data,
            status="success"
        )

        assert log_id is not None
        assert len(log_id) > 0
        session.add.assert_called_once()
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_request_disabled(self, mock_database):
        db, session = mock_database
        service = LoggingService(db, enabled=False)

        log_id = await service.log_request(
            endpoint="/test",
            input_data={"test": "data"}
        )

        assert log_id is None
        session.add.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_request_with_error(self, mock_database):
        db, session = mock_database
        service = LoggingService(db, enabled=True)

        log_id = await service.log_request(
            endpoint="/test",
            input_data={"test": "data"},
            status="error",
            error_message="Test error"
        )

        assert log_id is not None
        session.add.assert_called_once()
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_request_database_error(self, mock_database):
        db, session = mock_database
        session.commit.side_effect = Exception("Database error")
        service = LoggingService(db, enabled=True)

        log_id = await service.log_request(
            endpoint="/test",
            input_data={"test": "data"}
        )

        assert log_id is not None
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_request_no_database(self):
        """Test logging service with no database (disabled state)"""
        service = LoggingService(db=None, enabled=True)

        log_id = await service.log_request(
            endpoint="/test",
            input_data={"test": "data"}
        )

        assert log_id is None
