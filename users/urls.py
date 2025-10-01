from django.urls import path, include
from .views import (
    RegisterView, LoginView, logout_view, CustomTokenRefreshView,
    UserDetailView, ProfileUpdateView,
    PostViewSet, CommentViewSet, MediaUploadView, MediaDetailView
)
from .views import MediaBatchUploadView
from .social_auth import google_login
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout_view, name='logout'),
    
    # Social auth endpoints
    path('auth/social/google/', google_login, name='google-login'),
    
    # User endpoints
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/profile/', ProfileUpdateView.as_view(), name='profile-update'),

    # Post + nested endpoints
    path('', include(router.urls)),
    path('posts/<int:post_pk>/comments/', CommentViewSet.as_view({'get':'list','post':'create'}), name='comment-list-create'),
    path('posts/<int:post_pk>/comments/<int:pk>/', CommentViewSet.as_view({'delete':'destroy','put':'update','patch':'partial_update'}), name='comment-detail'),
    path('posts/<int:post_pk>/media/', MediaUploadView.as_view(), name='media-upload'),
    path('posts/<int:post_pk>/media/batch/', MediaBatchUploadView.as_view(), name='media-batch-upload'),
    path('posts/<int:post_pk>/media/<int:pk>/', MediaDetailView.as_view(), name='media-detail'),
]
