"""
OpenAPI schema components for drf-spectacular
Defines reusable schemas for API documentation
"""
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiResponse
from drf_spectacular.types import OpenApiTypes


# Error Schema Components
ERROR_VALIDATION_SCHEMA = {
    'type': 'object',
    'description': 'Validation error response',
    'properties': {
        'field_name': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
            'description': 'List of validation errors for this field',
            'example': ['This field is required.']
        }
    },
    'example': {
        'email': ['This field is required.'],
        'password': ['This password is too short.', 'This password is too common.']
    }
}

ERROR_THROTTLE_SCHEMA = {
    'type': 'object',
    'description': 'Rate limit exceeded error',
    'properties': {
        'detail': {
            'type': 'string',
            'description': 'Error message describing the rate limit',
            'example': 'Request was throttled. Expected available in 42 seconds.'
        }
    },
    'required': ['detail']
}

ERROR_AUTHENTICATION_SCHEMA = {
    'type': 'object',
    'description': 'Authentication error response',
    'properties': {
        'detail': {
            'type': 'string',
            'description': 'Authentication error message',
            'example': 'Authentication credentials were not provided.'
        }
    },
    'required': ['detail']
}

ERROR_PERMISSION_SCHEMA = {
    'type': 'object',
    'description': 'Permission denied error response',
    'properties': {
        'detail': {
            'type': 'string',
            'description': 'Permission error message',
            'example': 'You do not have permission to perform this action.'
        }
    },
    'required': ['detail']
}

ERROR_NOT_FOUND_SCHEMA = {
    'type': 'object',
    'description': 'Resource not found error',
    'properties': {
        'detail': {
            'type': 'string',
            'description': 'Not found error message',
            'example': 'Not found.'
        }
    },
    'required': ['detail']
}

ERROR_GENERIC_SCHEMA = {
    'type': 'object',
    'description': 'Generic error response',
    'properties': {
        'error': {
            'type': 'string',
            'description': 'Error message',
            'example': 'An error occurred while processing your request.'
        }
    },
    'required': ['error']
}

# Token Response Schemas
TOKEN_RESPONSE_SCHEMA = {
    'type': 'object',
    'description': 'JWT token pair response',
    'properties': {
        'access': {
            'type': 'string',
            'description': 'JWT access token (15min lifetime)',
            'example': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjMwMDAwMDAwfQ.abc123'
        },
        'refresh': {
            'type': 'string',
            'description': 'JWT refresh token (7day lifetime)',
            'example': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYzMDAwMDAwMH0.def456'
        }
    },
    'required': ['access', 'refresh']
}

# Media Batch Response Schema
MEDIA_BATCH_RESPONSE_SCHEMA = {
    'type': 'object',
    'description': 'Batch media upload response',
    'properties': {
        'created': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'example': 1},
                    'file': {'type': 'string', 'example': '/media/posts/1/image.jpg'},
                    'content_type': {'type': 'string', 'example': 'image/jpeg'},
                    'size': {'type': 'integer', 'example': 1024000},
                    'uploaded_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'description': 'Successfully uploaded media files'
        },
        'errors': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'example': 'large_file.jpg'},
                    'error': {'type': 'string', 'example': 'File size exceeds maximum allowed size of 5MB'}
                }
            },
            'description': 'Files that failed to upload with error messages'
        }
    },
    'required': ['created', 'errors']
}

# Reusable OpenAPI response objects
OPENAPI_RESPONSES = {
    '400': OpenApiResponse(
        response=ERROR_VALIDATION_SCHEMA,
        description='Validation error - invalid request data'
    ),
    '401': OpenApiResponse(
        response=ERROR_AUTHENTICATION_SCHEMA,
        description='Authentication required - missing or invalid credentials'
    ),
    '403': OpenApiResponse(
        response=ERROR_PERMISSION_SCHEMA,
        description='Permission denied - insufficient privileges'
    ),
    '404': OpenApiResponse(
        response=ERROR_NOT_FOUND_SCHEMA,
        description='Resource not found'
    ),
    '429': OpenApiResponse(
        response=ERROR_THROTTLE_SCHEMA,
        description='Rate limit exceeded - too many requests'
    ),
}

# Schema components to be added to SPECTACULAR_SETTINGS
SCHEMA_COMPONENTS = {
    'ErrorValidation': ERROR_VALIDATION_SCHEMA,
    'ErrorThrottle': ERROR_THROTTLE_SCHEMA,
    'ErrorAuthentication': ERROR_AUTHENTICATION_SCHEMA,
    'ErrorPermission': ERROR_PERMISSION_SCHEMA,
    'ErrorNotFound': ERROR_NOT_FOUND_SCHEMA,
    'ErrorGeneric': ERROR_GENERIC_SCHEMA,
    'TokenResponse': TOKEN_RESPONSE_SCHEMA,
    'MediaBatchResponse': MEDIA_BATCH_RESPONSE_SCHEMA,
}


def postprocess_schema_enhancements(result, generator, request, public):
    """
    Post-processing hook to add custom schema components to the OpenAPI schema.
    This avoids circular import issues during Django startup.
    """
    if 'components' not in result:
        result['components'] = {}
    if 'schemas' not in result['components']:
        result['components']['schemas'] = {}
    
    # Add our custom schema components
    result['components']['schemas'].update(SCHEMA_COMPONENTS)
    
    return result