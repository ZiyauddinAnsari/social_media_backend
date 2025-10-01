# Social Media API Backend - Week 3

A comprehensive Django REST API for social media functionality with JWT authentication, file uploads, and API documentation.

## Features Implemented ✅

- ✅ Custom user model with email as primary field
- ✅ Profile model with display name, bio, and avatar support
- ✅ JWT authentication (access + refresh tokens)
- ✅ User registration, login, token refresh, and logout endpoints
- ✅ Protected endpoints with proper permissions
- ✅ Interactive API documentation with drf-spectacular
- ✅ Comprehensive test coverage
- ✅ Media file handling configuration

## Quick Start

### Prerequisites

- Python 3.11+ (you have Python 3.13.7)
- Virtual environment activated

### Installation

```bash
# Navigate to project directory
cd /f/python/backend

# Install dependencies (already done)
pip install djangorestframework-simplejwt drf-spectacular pytest-django pillow

# Run migrations (already done)
python manage.py migrate

# Start development server
python manage.py runserver
```

### API Endpoints

#### Authentication

- **POST** `/api/auth/register/` - User registration
- **POST** `/api/auth/token/` - Login (get tokens)
- **POST** `/api/auth/token/refresh/` - Refresh access token
- **POST** `/api/auth/logout/` - Logout (blacklist refresh token)

#### Users

- **GET** `/api/users/{id}/` - Get user details
- **PATCH** `/api/users/profile/` - Update user profile

#### Documentation

- **GET** `/api/docs/` - Swagger UI
- **GET** `/api/redoc/` - ReDoc UI
- **GET** `/api/schema/` - OpenAPI schema

## Testing the API

### 1. Access API Documentation

Open your browser and go to:

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/

### 2. Test Registration

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123",
    "display_name": "Test User"
  }'
```

### 3. Test Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### 4. Test Protected Endpoint

```bash
# Replace {ACCESS_TOKEN} with the token from login response
curl -X GET http://127.0.0.1:8000/api/users/1/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

### 5. Test Token Refresh

```bash
# Replace {REFRESH_TOKEN} with the refresh token from login/register
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "{REFRESH_TOKEN}"}'
```

## Run Tests

```bash
# Run all authentication tests
python manage.py test users.tests.AuthenticationTestCase

# Run specific test
python manage.py test users.tests.AuthenticationTestCase.test_user_registration
```

## Settings Summary

### JWT Configuration

- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days
- Token rotation enabled
- Blacklist after rotation enabled

### Media Files

- Media URL: `/media/`
- Media root: `backend/media/`
- Avatar uploads: `avatars/` directory

### API Settings

- Authentication: JWT via Bearer token
- Default permissions: IsAuthenticated
- Pagination: 20 items per page
- Schema generation: drf-spectacular

## Database Models

### CustomUser

- email (unique, primary identifier)
- username (optional)
- password (hashed)
- is_active, is_staff, is_superuser
- date_joined, last_login

### Profile

- user (OneToOne with CustomUser)
- display_name
- bio
- avatar (ImageField)
- created_at, updated_at

## Next Steps (Week 3 Remaining Days)

### Day 2 (Tomorrow)

- [ ] Add API throttling/rate limiting
- [ ] Enhance API documentation with examples
- [ ] Add more comprehensive user management features

### Day 3

- [ ] Implement Post model and endpoints
- [ ] Add Media model for file uploads
- [ ] Create post CRUD operations with file support

### Day 4

- [ ] Add Comment and Like models
- [ ] Implement nested comment endpoints
- [ ] Add proper permissions (IsOwnerOrReadOnly)

### Day 5

- [ ] Final testing and documentation
- [ ] Performance optimization
- [ ] Deployment preparation

## Development Notes

### Custom User Model

- Uses email as the primary identifier instead of username
- Custom manager handles user creation without requiring username
- Profile is automatically created on user registration

### Token Management

- Access tokens are short-lived (15 minutes) for security
- Refresh tokens are long-lived (7 days) and can be blacklisted
- Tokens are automatically rotated on refresh for enhanced security

### Security Features

- Password validation using Django's built-in validators
- JWT tokens with proper expiration
- Token blacklisting on logout
- CORS-ready for frontend integration
