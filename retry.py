from functools import wraps
from exceptions import SystemTimeoutError, SystemAssertionError
from logging_config import get_logger
from tenacity import (
    retry, wait_fixed, retry_if_exception_type, stop_after_attempt
)

logger = get_logger(__name__)

def ui_retry(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        
        async def before_retry(retry_state):
            exc = retry_state.outcome.exception()

            if (isinstance(exc, SystemTimeoutError) or
                isinstance(exc, SystemAssertionError)
            ):
                logger.error('Tentando regarregar a página...')
                await self.page.reload()
        dec = retry(
            retry=retry_if_exception_type((SystemTimeoutError, SystemAssertionError)),
            wait=wait_fixed(3),
            stop=stop_after_attempt(3),
            before_sleep=before_retry,
            reraise=True
        )
        return await dec(func)(self, *args, **kwargs)
    return wrapper


def bootstrap_retry(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        
        async def before_retry(retry_state):
            exc = retry_state.outcome.exception()

            if isinstance(exc, SystemTimeoutError):
                if hasattr(self, 'page') and self.page:
                    logger.error('Tentando regarregar a página...')
                    await self.page.reload()

        dec = retry(
            retry=retry_if_exception_type(SystemTimeoutError),
            wait=wait_fixed(3),
            stop=stop_after_attempt(2),
            before_sleep=before_retry,
            reraise=True
        )
        return await dec(func)(self, *args, **kwargs)
    return wrapper
