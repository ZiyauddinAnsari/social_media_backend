# Social authentication views and serializers
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from django.contrib.auth import get_user_model
from django.conf import settings
from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount import app_settings
import requests
from rest_framework import serializers

User = get_user_model()


class SocialLoginSerializer(serializers.Serializer):
    """Serializer for social login requests."""
    access_token = serializers.CharField(
        help_text="Access token from social provider (Google)"
    )
    code = serializers.CharField(
        required=False,
        help_text="Authorization code from social provider (alternative to access_token)"
    )


class SocialLoginResponseSerializer(serializers.Serializer):
    """Serializer for social login responses."""
    user = serializers.DictField(help_text="User information")
    tokens = serializers.DictField(help_text="JWT access and refresh tokens")
    created = serializers.BooleanField(help_text="Whether user was newly created")


@extend_schema(
    request=SocialLoginSerializer,
    responses={
        200: SocialLoginResponseSerializer,
        400: OpenApiTypes.OBJECT,
        401: OpenApiTypes.OBJECT,
    },
    description="Authenticate with Google OAuth2 token",
    examples=[
        OpenApiExample(
            "Google Login",
            summary="Login with Google access token",
            description="Authenticate using a Google OAuth2 access token",
            value={
                "access_token": "ya29.a0AfH6SMD..."
            },
            request_only=True,
        ),
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """
    Authenticate user with Google OAuth2 token.
    
    Accepts a Google access token, validates it, and returns JWT tokens.
    Creates new user account if needed, or links to existing account with same email.
    """
    serializer = SocialLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    access_token = serializer.validated_data.get('access_token')
    
    try:
        # Validate Google token and get user info
        google_user_info = validate_google_token(access_token)
        if not google_user_info:
            return Response(
                {'error': 'Invalid Google access token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get or create user
        user, created = get_or_create_user_from_google(google_user_info)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_jwt = refresh.access_token
        
        # Prepare response data
        from .serializers import UserSerializer
        user_data = UserSerializer(user).data
        
        response_data = {
            'user': user_data,
            'tokens': {
                'access': str(access_jwt),
                'refresh': str(refresh),
            },
            'created': created
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Social authentication failed: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


def validate_google_token(access_token):
    """
    Validate Google access token and return user information.
    """
    try:
        # Call Google's userinfo endpoint to validate token and get user data
        response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except requests.RequestException:
        return None


def get_or_create_user_from_google(google_user_info):
    """
    Get existing user or create new user from Google user information.
    Returns tuple (user, created).
    """
    email = google_user_info.get('email')
    google_id = google_user_info.get('id')
    
    if not email or not google_id:
        raise ValueError("Missing required user information from Google")
    
    # First check if user already exists with this Google account
    try:
        social_account = SocialAccount.objects.get(
            provider='google',
            uid=google_id
        )
        return social_account.user, False
    except SocialAccount.DoesNotExist:
        pass
    
    # Check if user exists with this email
    try:
        user = User.objects.get(email=email)
        created = False
        
        # Link Google account to existing user
        SocialAccount.objects.create(
            user=user,
            provider='google',
            uid=google_id,
            extra_data=google_user_info
        )
        
    except User.DoesNotExist:
        # Create new user
        user = create_user_from_google(google_user_info)
        created = True
    
    return user, created


def create_user_from_google(google_user_info):
    """
    Create a new user from Google user information.
    """
    email = google_user_info.get('email')
    first_name = google_user_info.get('given_name', '')
    last_name = google_user_info.get('family_name', '')
    google_id = google_user_info.get('id')
    
    # Create user
    user = User.objects.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=None,  # No password for social users
    )
    
    # Create social account
    SocialAccount.objects.create(
        user=user,
        provider='google',
        uid=google_id,
        extra_data=google_user_info
    )
    
    # Ensure profile exists (create if signal didn't trigger)
    from .models import Profile
    if not hasattr(user, 'profile'):
        name = google_user_info.get('name', '')
        if not name:
            name = f"{first_name} {last_name}".strip()
        if not name:
            name = email.split('@')[0]
            
        Profile.objects.create(
            user=user,
            display_name=name,
            bio='',
        )
    else:
        # Update profile display name if not set
        profile = user.profile
        if not profile.display_name:
            name = google_user_info.get('name', '')
            if not name:
                name = f"{first_name} {last_name}".strip()
            if not name:
                name = email.split('@')[0]
            profile.display_name = name
            profile.save()
    
    return user