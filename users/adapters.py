# Social account adapters for customizing allauth behavior
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field
from django.contrib.auth import get_user_model

User = get_user_model()


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social account handling.
    Integrates with our CustomUser model and profile creation.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle existing users with same email from social login.
        This allows linking social accounts to existing email-based accounts.
        """
        if sociallogin.is_existing:
            return
        
        if not sociallogin.account.extra_data.get('email'):
            return
        
        email = sociallogin.account.extra_data.get('email')
        try:
            # Check if user with this email already exists
            existing_user = User.objects.get(email=email)
            # Link the social account to existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            # No existing user, will create new one
            pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user data from social account information.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get extra data from social provider
        extra_data = sociallogin.account.extra_data
        
        # Set display name from social profile if available
        if not user.first_name and not user.last_name:
            if 'given_name' in extra_data:
                user.first_name = extra_data.get('given_name', '')
            if 'family_name' in extra_data:
                user.last_name = extra_data.get('family_name', '')
        
        # Email verification status from trusted provider
        if sociallogin.account.provider == 'google':
            # Google emails are pre-verified
            user_field(user, 'email_verified', True)
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and ensure profile is created.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Ensure profile exists (should be created by signal, but double-check)
        if not hasattr(user, 'profile'):
            from .models import Profile
            extra_data = sociallogin.account.extra_data
            
            # Create profile with social data
            display_name = extra_data.get('name', '')
            if not display_name and user.first_name:
                display_name = f"{user.first_name} {user.last_name}".strip()
            if not display_name:
                display_name = user.email.split('@')[0]
            
            Profile.objects.create(
                user=user,
                display_name=display_name,
                bio='',
            )
        
        return user