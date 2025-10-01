# Social Authentication Implementation

## Overview

This implementation adds Google OAuth2 social login to the Django backend using `django-allauth` and `dj-rest-auth`. Users can now authenticate using their Google accounts and receive JWT tokens for API access.

## Features Implemented

### ✅ Core Functionality

- **Google OAuth2 Integration** - Complete authentication flow
- **JWT Token Generation** - Social login returns access + refresh tokens
- **User Account Linking** - Links Google accounts to existing email-based accounts
- **Profile Auto-Creation** - Automatically creates user profiles from Google data
- **Email Verification** - Trusts Google's email verification

### ✅ API Endpoints

- `POST /api/auth/social/google/` - Main social login endpoint
- Full allauth integration available at `/api/auth/` endpoints

### ✅ Security Features

- Server-side Google token validation
- Proper user creation and linking logic
- Social account tracking and management
- Consistent permissions with regular auth

## API Usage

### Social Login Request

```http
POST /api/auth/social/google/
Content-Type: application/json

{
  "access_token": "ya29.a0AfH6SMD..."
}
```

### Social Login Response

```json
{
  "user": {
    "id": 1,
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
      "display_name": "John Doe",
      "bio": ""
    }
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "created": false
}
```

## Configuration

### Environment Variables

Set these in your environment or `.env` file:

```bash
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Google OAuth Setup

1. Go to [Google Developers Console](https://console.developers.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth2 credentials
5. Add authorized redirect URIs (for development: `http://localhost:8000/`)

## Database Schema

### New Tables Added

- `socialaccount_socialapp` - OAuth provider apps
- `socialaccount_socialaccount` - User social accounts
- `socialaccount_socialtoken` - Social auth tokens
- `account_emailaddress` - Email verification tracking

## Testing

### Automated Tests

```bash
python manage.py test users.SocialAuthTestCase --settings=backend.settings_test
```

### Manual Testing

```bash
python test_social_auth.py
```

## Implementation Details

### User Creation Flow

1. Validate Google access token
2. Extract user information from Google API
3. Check for existing social account
4. Link to existing email account or create new user
5. Generate JWT tokens
6. Return user data and tokens

### Account Linking Logic

- **Existing Google Account**: Returns existing user
- **Existing Email Account**: Links Google account to existing user
- **New User**: Creates new account with Google data

### Profile Management

- Auto-populates display name from Google profile
- Creates user profile if not exists
- Preserves existing profile data

## Security Considerations

- ✅ Server-side token validation
- ✅ No client secrets exposed
- ✅ Proper user account linking
- ✅ Email verification handling
- ✅ Social account tracking

## Frontend Integration

### Required Frontend Flow

1. Implement Google OAuth2 on frontend (Google Sign-In API)
2. Obtain access token from Google
3. Send token to `/api/auth/social/google/`
4. Store returned JWT tokens
5. Use JWT tokens for authenticated API requests

### Example Frontend Code (JavaScript)

```javascript
// After Google Sign-In completes
async function handleGoogleLogin(googleToken) {
  const response = await fetch("/api/auth/social/google/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      access_token: googleToken,
    }),
  });

  const data = await response.json();

  if (response.ok) {
    // Store tokens
    localStorage.setItem("access_token", data.tokens.access);
    localStorage.setItem("refresh_token", data.tokens.refresh);

    // User is now authenticated
    console.log("User:", data.user);
  }
}
```

## Files Modified/Created

### New Files

- `users/social_auth.py` - Social authentication views and logic
- `users/adapters.py` - Custom allauth adapters
- `.env.example` - Environment variable template

### Modified Files

- `backend/settings.py` - Added allauth configuration
- `backend/urls.py` - Added social auth URLs
- `users/urls.py` - Added Google login endpoint
- `users/tests.py` - Added social auth tests

## Status: ✅ COMPLETE

P1 (Social Login Integration) is now fully implemented and tested. The backend supports Google OAuth2 social login with JWT token generation, ready for frontend integration.
