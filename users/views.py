from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, UserSerializer, ProfileSerializer,
    PostSerializer, CommentSerializer, MediaSerializer, LikeSerializer
)
from .models import Profile, Post, Comment, Media, Like
from .validators import validate_media_file
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from users.throttles import (
    AuthLoginThrottle, AuthRegisterThrottle,
    PostCreateThrottle, CommentCreateThrottle
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
from django.db.models import Q
from .schemas import OPENAPI_RESPONSES

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        tags=['auth'],
        summary="Register a new user",
        description="Creates a user, profile, and returns JWT access & refresh tokens.",
        request=UserRegistrationSerializer,
        examples=[OpenApiExample('Register', value={
            'email': 'user@example.com', 'password': 'Passw0rd!', 'password_confirm': 'Passw0rd!', 'display_name': 'User'
        })],
        responses={
            201: OpenApiResponse(
                description='User created successfully with JWT tokens',
                response=UserSerializer,
                examples=[OpenApiExample('Success', value={
                    'user': {'id': 1, 'email': 'user@example.com', 'display_name': 'User'},
                    'tokens': {
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                    }
                })]
            ),
            **OPENAPI_RESPONSES
        }
    )
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['auth'],
    summary="Login to obtain JWT tokens",
    description="Returns access & refresh tokens plus user object.",
    examples=[OpenApiExample('Login', value={'email':'user@example.com','password':'Passw0rd!'})],
    responses={
        200: OpenApiResponse(
            description='Login successful with JWT tokens',
            examples=[OpenApiExample('Success', value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'user': {'id': 1, 'email': 'user@example.com', 'display_name': 'User'}
            })]
        ),
        **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['400', '401', '429']}
    }
)
class LoginView(TokenObtainPairView):
    """Custom login view that returns user data along with tokens"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Get user from email
            email = request.data.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                    response.data['user'] = UserSerializer(user).data
                except User.DoesNotExist:
                    pass
        return response


@extend_schema(
    methods=['post'],
    tags=['auth'],
    summary='Logout (blacklist refresh token)',
    description='Blacklists the provided refresh token to prevent further use.',
    request={'type': 'object', 'properties': {'refresh': {'type': 'string', 'description': 'JWT refresh token to blacklist'}}, 'required': ['refresh']},
    examples=[OpenApiExample('Logout', value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'})],
    responses={
        200: OpenApiResponse(
            description='Logout successful',
            examples=[OpenApiExample('Success', value={'message': 'Successfully logged out'})]
        ),
        **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['400', '401']}
    }
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['auth'],
    summary='Refresh JWT access token',
    description='Exchange a valid refresh token for a new access token. Refresh tokens have a 7-day lifetime.',
    request={'type': 'object', 'properties': {'refresh': {'type': 'string', 'description': 'Valid JWT refresh token'}}, 'required': ['refresh']},
    examples=[OpenApiExample('Token Refresh', value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'})],
    responses={
        200: OpenApiResponse(
            description='New access token generated',
            response={'$ref': '#/components/schemas/TokenResponse'},
            examples=[OpenApiExample('Success', value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            })]
        ),
        **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['400', '401']}
    }
)
class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view with enhanced documentation"""
    pass


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'author', None) == request.user


@extend_schema_view(
    list=extend_schema(
        tags=['posts'],
        summary="List posts (public + your private posts)",
        description=(
            "Returns public posts plus any private posts authored by the authenticated user. "
            "Other users' private posts are excluded and direct retrieval of them yields 404."
        ),
        examples=[
            OpenApiExample(
                'List Example',
                value=[
                    {
                        'id': 10,
                        'author': {'id': 1, 'email': 'author@example.com'},
                        'title': '',
                        'content': 'Hello world',
                        'privacy': 'public',
                        'tags': [],
                        'created_at': '2025-09-29T12:00:00Z',
                        'updated_at': '2025-09-29T12:00:00Z',
                        'media': [],
                        'likes_count': 0,
                        'comments_count': 0
                    }
                ]
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['posts'],
        summary="Retrieve a post (404 for private if not owner)",
        responses={404: OpenApiResponse(description='Not found (or private)')}
    ),
    create=extend_schema(
        tags=['posts'],
        summary="Create a post",
        description="Creates a post and returns a success message.",
        examples=[
            OpenApiExample(
                'Create Response',
                value={
                    'id': 42,
                    'author': {'id': 1, 'email': 'me@example.com'},
                    'title': '',
                    'content': 'My first post',
                    'privacy': 'public',
                    'tags': [],
                    'created_at': '2025-09-29T12:00:00Z',
                    'updated_at': '2025-09-29T12:00:00Z',
                    'media': [],
                    'likes_count': 0,
                    'comments_count': 0,
                    'message': 'Post created successfully'
                }
            )
        ]
    ),
    update=extend_schema(
        tags=['posts'],
        summary="Update a post",
        examples=[
            OpenApiExample(
                'Update Response',
                value={
                    'id': 42,
                    'author': {'id': 1, 'email': 'me@example.com'},
                    'title': 'New title',
                    'content': 'Edited',
                    'privacy': 'private',
                    'tags': [],
                    'created_at': '2025-09-29T12:00:00Z',
                    'updated_at': '2025-09-29T12:05:00Z',
                    'media': [],
                    'likes_count': 0,
                    'comments_count': 0,
                    'message': 'Post updated successfully'
                }
            )
        ]
    ),
    partial_update=extend_schema(
        tags=['posts'],
        summary="Partially update a post",
    ),
    destroy=extend_schema(tags=['posts'], summary="Delete a post"),
    like=extend_schema(
        tags=['posts'],
        summary="Toggle like on a post",
        examples=[
            OpenApiExample('Like', value={'liked': True, 'likes_count': 5, 'message': 'Post liked'}),
            OpenApiExample('Unlike', value={'liked': False, 'likes_count': 4, 'message': 'Like removed'})
        ]
    )
)
@extend_schema_view(
    list=extend_schema(
        tags=['posts'],
        summary='List posts',
        description='Retrieve a list of posts. Users see their own posts plus public posts.',
        responses={
            200: OpenApiResponse(description='List of posts', response=PostSerializer(many=True)),
            **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['401', '429']}
        }
    ),
    create=extend_schema(
        tags=['posts'],
        summary='Create a new post',
        description='Create a new post. Rate limited to prevent spam.',
        responses={
            201: OpenApiResponse(
                description='Post created successfully',
                response=PostSerializer,
                examples=[OpenApiExample('Created', value={
                    'id': 1, 'content': 'My first post!', 'privacy': 'public', 'author': 1,
                    'message': 'Post created successfully'
                })]
            ),
            **OPENAPI_RESPONSES
        }
    ),
    retrieve=extend_schema(
        tags=['posts'],
        summary='Retrieve a post',
        description='Get details of a specific post.',
        responses={
            200: OpenApiResponse(description='Post details', response=PostSerializer),
            **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['401', '403', '404']}
        }
    ),
    update=extend_schema(
        tags=['posts'],
        summary='Update a post',
        description='Update an existing post. Only the author can update their posts.',
        responses={
            200: OpenApiResponse(
                description='Post updated successfully',
                response=PostSerializer,
                examples=[OpenApiExample('Updated', value={
                    'id': 1, 'content': 'Updated content', 'privacy': 'public',
                    'message': 'Post updated successfully'
                })]
            ),
            **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['400', '401', '403', '404']}
        }
    ),
    destroy=extend_schema(
        tags=['posts'],
        summary='Delete a post',
        description='Delete a post. Only the author can delete their posts.',
        responses={
            204: OpenApiResponse(description='Post deleted successfully'),
            **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['401', '403', '404']}
        }
    )
)
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author').prefetch_related('tags','media')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        base = super().get_queryset()
        user = self.request.user
        # Unauthenticated safety (though permission blocks) & staff see all
        if not user.is_authenticated:
            return base.filter(privacy='public')
        if user.is_staff:
            return base
        # Regular users: own posts + public posts
        return base.filter(Q(privacy='public') | Q(author=user))

    def get_throttles(self):
        # Apply creation-specific throttle on POST
        if self.action == 'create':
            self.throttle_classes = getattr(self, 'creation_throttle_classes', [])
        return super().get_throttles()

    creation_throttle_classes = [PostCreateThrottle]

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = dict(serializer.data)
        data['message'] = 'Post created successfully'
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        data = dict(serializer.data)
        data['message'] = 'Post updated successfully'
        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            return Response({'liked': False, 'likes_count': post.likes.count(), 'message': 'Like removed'})
        return Response({'liked': True, 'likes_count': post.likes.count(), 'message': 'Post liked'})


class CommentViewSet(viewsets.GenericViewSet,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.ListModelMixin):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @extend_schema(tags=['comments'], summary='List comments for a post')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=['comments'], summary='Create a comment', examples=[
        OpenApiExample('Create Comment', value={'text': 'Nice post!'})
    ])
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return Comment.objects.filter(post_id=post_id).select_related('author')

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        # Validate post exists and user can access it (respects privacy)
        try:
            post = Post.objects.get(id=post_id)
            # Check if user can access this post (privacy rules)
            if post.privacy == 'private' and post.author != self.request.user:
                from django.http import Http404
                raise Http404("Post not found")
        except Post.DoesNotExist:
            from django.http import Http404
            raise Http404("Post not found")
        serializer.save(author=self.request.user, post_id=post_id)

    def get_throttles(self):
        if self.action == 'create':
            self.throttle_classes = [CommentCreateThrottle]
        return super().get_throttles()


class MediaUploadView(generics.CreateAPIView):
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['media'], summary='Upload a single media file for a post')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        # Validate post exists and user can access it
        try:
            post = Post.objects.get(id=post_id)
            # Check if user can access this post (privacy rules)
            if post.privacy == 'private' and post.author != self.request.user:
                from django.http import Http404
                raise Http404("Post not found")
        except Post.DoesNotExist:
            from django.http import Http404
            raise Http404("Post not found")
        serializer.save(post_id=post_id)


@extend_schema_view(
    post=extend_schema(
        tags=['media'],
        summary='Batch upload media files to a post',
        description='Upload multiple media files to a post in a single request. Returns details of successfully uploaded files and any errors.',
        request={
            'type': 'object',
            'properties': {
                'files': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'binary'},
                    'description': 'Array of media files to upload (images, videos)'
                }
            },
            'required': ['files']
        },
        examples=[
            OpenApiExample(
                'Batch Upload',
                description='Upload multiple files using multipart/form-data',
                value={'files': ['file1.jpg', 'file2.mp4']}
            )
        ],
        responses={
            201: OpenApiResponse(
                description='All files uploaded successfully',
                response={'$ref': '#/components/schemas/MediaBatchResponse'},
                examples=[OpenApiExample('All Success', value={
                    'created': [
                        {'id': 1, 'file': '/media/posts/1/image.jpg', 'content_type': 'image/jpeg', 'size': 1024000},
                        {'id': 2, 'file': '/media/posts/1/video.mp4', 'content_type': 'video/mp4', 'size': 5120000}
                    ],
                    'errors': []
                })]
            ),
            207: OpenApiResponse(
                description='Partial success - some files uploaded, some failed',
                response={'$ref': '#/components/schemas/MediaBatchResponse'},
                examples=[OpenApiExample('Partial Success', value={
                    'created': [
                        {'id': 1, 'file': '/media/posts/1/image.jpg', 'content_type': 'image/jpeg', 'size': 1024000}
                    ],
                    'errors': [
                        {'filename': 'large_file.jpg', 'error': 'File size exceeds maximum allowed size of 5MB'}
                    ]
                })]
            ),
            **{k: v for k, v in OPENAPI_RESPONSES.items() if k in ['400', '401', '403', '404']}
        }
    )
)
class MediaBatchUploadView(generics.GenericAPIView):
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_pk')
        # Validate post exists and user can access it
        try:
            post = Post.objects.get(id=post_id)
            # Check if user can access this post (privacy rules)
            if post.privacy == 'private' and post.author != self.request.user:
                from django.http import Http404
                raise Http404("Post not found")
        except Post.DoesNotExist:
            from django.http import Http404
            raise Http404("Post not found")
            
        files = request.FILES.getlist('files')
        if not files:
            return Response({'error':'No files provided'}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        errors = []
        for f in files:
            try:
                meta = validate_media_file(f)
                media = Media.objects.create(
                    post_id=post_id,
                    file=f,
                    uploaded_by=request.user,
                    **meta
                )
                created.append(MediaSerializer(media).data)
            except Exception as e:
                errors.append({'filename': getattr(f,'name',''), 'error': str(e)})
        status_code = status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED
        return Response({'created': created, 'errors': errors}, status=status_code)


class MediaDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return Media.objects.filter(post_id=post_id)
    
    def get_object(self):
        obj = super().get_object()
        # Check permission: either post author or media uploader
        if obj.post.author != self.request.user and obj.uploaded_by != self.request.user:
            from django.http import Http404
            raise Http404("Media not found")
        return obj
    
    @extend_schema(tags=['media'], summary='Retrieve media details')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['media'], 
        summary='Delete media file',
        responses={204: OpenApiResponse(description='Media deleted successfully')}
    )
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response({'message': 'Media deleted successfully'}, status=status.HTTP_204_NO_CONTENT)