

import functools
import logging
import time

logger = logging.getLogger(__name__)


def log_call(func):
   
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"→ Calling {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"✓ {func.__name__} completed")
        return result
    return wrapper


def retry(times: int = 3, delay: float = 1.0, exceptions=(Exception,)):
   
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    logger.warning(
                        f"[retry] {func.__name__} attempt {attempt}/{times} failed: {exc}"
                    )
                    if attempt < times:
                        time.sleep(delay)
            # All attempts exhausted — re-raise the last exception
            raise last_exc
        return wrapper
    return decorator
