# Test-specific Django settings
# Inherits from main settings and overrides for test stability

from .settings import *

# Disable throttling completely for tests
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
# Set throttle rates to very high values to effectively disable throttling
# while still allowing throttle classes to instantiate without errors
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'auth_register': '1000000/min',  # Effectively unlimited
    'post_create': '1000000/min',    # Effectively unlimited
    'comment_create': '1000000/min', # Effectively unlimited
}

# Faster password validation for tests
AUTH_PASSWORD_VALIDATORS = []

# Use in-memory database for speed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Fast password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations for faster test setup
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific media settings
MEDIA_ROOT = '/tmp/test_media'

# Reduce SimpleJWT token lifetimes for faster tests
from datetime import timedelta
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=1),
})