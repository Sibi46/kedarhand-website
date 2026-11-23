"""Independent deployment settings for the pre-23-November storefront."""
import os

os.environ.setdefault('APP_BASE_PATH', '/kedarmart1')

from .settings import *  # noqa: F403

SESSION_COOKIE_NAME = 'kedarmart1_sessionid'
CSRF_COOKIE_NAME = 'kedarmart1_csrftoken'
