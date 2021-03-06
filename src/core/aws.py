import logging
from contextlib import AsyncExitStack
from types import TracebackType
from typing import Optional, Type

import aiobotocore
import aiobotocore.client
from botocore.config import Config

from core.config import settings

logger = logging.getLogger(__name__)


class AWSManager:
    """Provides common interface for the Amazon API services

    Example:
        async with AWSManager() as manager:
            do job

    """

    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self._dynamodb_client: Optional[aiobotocore.client.AioBaseClient] = None
        self.initialized = False

        self._session: Optional[aiobotocore.AioSession] = None

    @property
    def dynamodb(self) -> aiobotocore.client.AioBaseClient:
        if self._dynamodb_client is None or not self.initialized:
            msg = (
                "Dynamodb is not initialized. "
                "It is not allowed to use without context manager"
            )
            logger.error(msg)
            raise ValueError(msg)

        return self._dynamodb_client

    async def __aenter__(self) -> "AWSManager":
        await self.initialize()
        return self

    async def initialize(self) -> None:
        if self.initialized:
            msg = "AWS manager was already initialized."
            logger.error(msg)
            raise ValueError(msg)

        self.initialized = True
        session = self._get_session()
        self._dynamodb_client = await self._exit_stack.enter_async_context(
            session.create_client(
                "dynamodb",
                region_name=settings.AWS_REGION_NAME,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                endpoint_url=settings.AWS_DYNAMODB_ENDPOINT_URL,
            )
        )

    async def close(self) -> None:
        if self.initialized:
            self.initialized = False
            await self._exit_stack.__aexit__(None, None, None)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self.initialized:
            self.initialized = False
            await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    def _get_session(self) -> aiobotocore.AioSession:
        """
        Return a session object. Creates new if not exists.
        """
        if not self._session:
            self._session = aiobotocore.get_session()

            # https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html
            self._session.set_default_client_config(
                Config(
                    retries={"max_attempts": settings.AWS_CLIENT_MAX_ATTEMPTS},
                    connect_timeout=settings.AWS_CLIENT_CONNECT_TIMEOUT,
                    read_timeout=settings.AWS_CLIENT_READ_TIMEOUT,
                    max_pool_connections=settings.AWS_CLIENT_MAX_POOL_CONNECTIONS,
                    parameter_validation=settings.AWS_CLIENT_PARAMETER_VALIDATION,
                )
            )

        return self._session
