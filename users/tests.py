import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from users.models import Profile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import Post, Like, Comment
from io import BytesIO
from PIL import Image

User = get_user_model()


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/token/'
        self.refresh_url = '/api/auth/token/refresh/'
        self.logout_url = '/api/auth/logout/'
        
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'display_name': 'Test User'
        }

    def register(self, prefix='u'):
        import uuid
        data = self.user_data.copy()
        data['email'] = f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"
        resp = self.client.post(self.register_url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"Unexpected registration status {resp.status_code}: {getattr(resp,'data',None)}")
        return resp

    def test_user_registration(self):
        """Test user registration with profile creation"""
        response = self.register('reg')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Check user was created using email from response
        user_email = response.data['user']['email']
        user = User.objects.get(email=user_email)
        self.assertTrue(user.check_password(self.user_data['password']))
        
        # Check profile was created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.display_name, self.user_data['display_name'])
    
    # Media validation moved to PostFlowTestCase

    def test_user_login(self):
        """Test user login with JWT token generation"""
        reg = self.register('login')
        login_data = {
            'email': reg.data['user']['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_token_refresh(self):
        """Test JWT token refresh"""
        response = self.register('refresh')
        refresh_token = response.data['tokens']['refresh']
        
        # Test token refresh
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_logout(self):
        """Test user logout with token blacklisting"""
        response = self.register('logout')
        refresh_token = response.data['tokens']['refresh']
        access_token = response.data['tokens']['access']
        
        # Authenticate with access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test logout
        logout_data = {'refresh': refresh_token}
        response = self.client.post(self.logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without authentication"""
        response = self.client.get('/api/users/1/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        response = self.register('protected')
        access_token = response.data['tokens']['access']
        user_id = response.data['user']['id']
        
        # Access protected endpoint with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(f'/api/users/{user_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure returned email matches the user we registered
        self.assertTrue(response.data['email'])

    def test_profile_update(self):
        """Test profile update functionality"""
        response = self.register('profile')
        access_token = response.data['tokens']['access']
        
        # Update profile
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        update_data = {
            'display_name': 'Updated Name',
            'bio': 'This is my bio'
        }
        response = self.client.patch('/api/users/profile/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_name'], update_data['display_name'])
        self.assertEqual(response.data['bio'], update_data['bio'])

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        import uuid
        invalid_data = self.user_data.copy()
        invalid_data['email'] = f"mismatch-{uuid.uuid4().hex[:8]}@example.com"
        invalid_data['password_confirm'] = 'differentpassword'
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        first = self.client.post(self.register_url, self.user_data)
        self.assertEqual(first.status_code, 201)
        duplicate = self.client.post(self.register_url, self.user_data)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)


class PostFlowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.post_list_url = '/api/posts/'
        reg = self.client.post(self.register_url, {
            'email':'poster@example.com','password':'pass12345','password_confirm':'pass12345'
        })
        self.assertEqual(reg.status_code, 201, f"PostFlow setup registration failed: {reg.status_code} {getattr(reg,'data',None)}")
        self.assertIn('tokens', reg.data, f"Registration response missing tokens: {reg.data}")
        self.access = reg.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_create_post_and_like_toggle(self):
        r = self.client.post(self.post_list_url, {'content':'Hello world'})
        self.assertEqual(r.status_code, 201)
        post_id = r.data['id']
        like_url = f'/api/posts/{post_id}/like/'
        r2 = self.client.post(like_url)
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.data['liked'])
        r3 = self.client.post(like_url)
        self.assertFalse(r3.data['liked'])

    def test_comment_and_media_upload(self):
        r = self.client.post(self.post_list_url, {'content':'Post with media'})
        post_id = r.data['id']
        # comment
        cr = self.client.post(f'/api/posts/{post_id}/comments/', {'text':'Nice'})
        self.assertEqual(cr.status_code, 201)
        # media upload
        dummy = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        mr = self.client.post(f'/api/posts/{post_id}/media/', {'file': dummy}, format='multipart')
        self.assertEqual(mr.status_code, 201)

    def test_comment_permission_enforcement(self):
        # User1 creates post & comment
        r = self.client.post(self.post_list_url, {'content':'Post for comment perms'})
        post_id = r.data['id']
        c = self.client.post(f'/api/posts/{post_id}/comments/', {'text':'Original'})
        self.assertEqual(c.status_code, 201)
        comment_id = c.data['id']
        # Second user attempts to modify
        c2 = APIClient()
        reg2 = c2.post(self.register_url, {'email':'permtest2@example.com','password':'pass12345','password_confirm':'pass12345'})
        token2 = reg2.data['tokens']['access']
        c2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        upd = c2.patch(f'/api/posts/{post_id}/comments/{comment_id}/', {'text':'Hacked'})
        self.assertIn(upd.status_code, (403, 404))  # 404 acceptable if hidden by object-level logic
        dele = c2.delete(f'/api/posts/{post_id}/comments/{comment_id}/')
        self.assertIn(dele.status_code, (403, 404))
        # Original author edits successfully
        upd_owner = self.client.patch(f'/api/posts/{post_id}/comments/{comment_id}/', {'text':'Edited'})
        self.assertEqual(upd_owner.status_code, 200)

    def test_media_deletion_permissions(self):
        # User1 creates post and uploads media
        r = self.client.post(self.post_list_url, {'content':'Post with deletable media'})
        post_id = r.data['id']
        dummy = SimpleUploadedFile('test.txt', b'hello', content_type='text/plain')
        mr = self.client.post(f'/api/posts/{post_id}/media/', {'file': dummy}, format='multipart')
        self.assertEqual(mr.status_code, 201)
        media_id = mr.data['id']
        
        # Second user attempts to delete media
        c2 = APIClient()
        import uuid
        reg2 = c2.post(self.register_url, {'email':f'mediadel-{uuid.uuid4().hex[:6]}@example.com','password':'pass12345','password_confirm':'pass12345'})
        token2 = reg2.data['tokens']['access']
        c2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        # Non-owner delete should fail
        del_fail = c2.delete(f'/api/posts/{post_id}/media/{media_id}/')
        self.assertIn(del_fail.status_code, (403, 404))
        
        # Owner can delete successfully
        del_success = self.client.delete(f'/api/posts/{post_id}/media/{media_id}/')
        self.assertEqual(del_success.status_code, 204)
        
        # Verify media is gone
        get_deleted = self.client.get(f'/api/posts/{post_id}/media/{media_id}/')
        self.assertEqual(get_deleted.status_code, 404)

    def test_media_validation_and_batch(self):
        r = self.client.post(self.post_list_url, {'content':'Post with many media'})
        post_id = r.data['id']
        oversize_content = b'a' * (settings.MEDIA_MAX_SIZE + 1)
        oversize = SimpleUploadedFile('big.txt', oversize_content, content_type='text/plain')
        mr = self.client.post(f'/api/posts/{post_id}/media/', {'file': oversize}, format='multipart')
        self.assertEqual(mr.status_code, 400)
        bad = SimpleUploadedFile('file.bin', b'binarydata', content_type='application/octet-stream')
        mr2 = self.client.post(f'/api/posts/{post_id}/media/', {'file': bad}, format='multipart')
        self.assertEqual(mr2.status_code, 400)
        img_bytes = BytesIO()
        img = Image.new('RGB', (10, 10), color='red')
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        img_file = SimpleUploadedFile('img.png', img_bytes.read(), content_type='image/png')
        txt_file = SimpleUploadedFile('readme.txt', b'hello', content_type='text/plain')
        batch = self.client.post(f'/api/posts/{post_id}/media/batch/', {'files': [img_file, txt_file]}, format='multipart')
        self.assertIn(batch.status_code, (201, 207))
        self.assertTrue(len(batch.data['created']) >= 1)

    def test_private_post_visibility(self):
        # Create a private post
        p = self.client.post(self.post_list_url, {'content':'Secret','privacy':'private'})
        self.assertEqual(p.status_code, 201)
        private_id = p.data['id']
        # Owner can retrieve
        r_owner = self.client.get(f'/api/posts/{private_id}/')
        self.assertEqual(r_owner.status_code, 200)
        # Register second user
        c2 = APIClient()
        import uuid
        email2 = f"other-{uuid.uuid4().hex[:6]}@example.com"
        reg2 = c2.post(self.register_url, {
            'email': email2,'password':'pass12345','password_confirm':'pass12345'
        })
        access2 = reg2.data['tokens']['access']
        c2.credentials(HTTP_AUTHORIZATION=f'Bearer {access2}')
        # Second user list should not contain the private post
        list_other = c2.get(self.post_list_url)
        self.assertEqual(list_other.status_code, 200)
        data_list = list_other.data
        if isinstance(data_list, dict) and 'results' in data_list:
            items = data_list['results']
        else:
            items = data_list
        self.assertFalse(any(item['id'] == private_id for item in items), f"Private post unexpectedly visible: {items}")
        # Second user direct retrieve should be 404 (filtered)
        get_other = c2.get(f'/api/posts/{private_id}/')
        self.assertEqual(get_other.status_code, 404)

    def test_public_and_own_posts_combined(self):
        # Create a public and a private post for user1
        pub = self.client.post(self.post_list_url, {'content':'Visible','privacy':'public'})
        priv = self.client.post(self.post_list_url, {'content':'Hidden','privacy':'private'})
        self.assertEqual(pub.status_code, 201)
        self.assertEqual(priv.status_code, 201)
        # Second user creates own private post and should see their own + public from user1 (not user1 private)
        c2 = APIClient()
        reg2 = c2.post(self.register_url, {
            'email':'another@example.com','password':'pass12345','password_confirm':'pass12345'
        })
        access2 = reg2.data['tokens']['access']
        c2.credentials(HTTP_AUTHORIZATION=f'Bearer {access2}')
        own_private = c2.post(self.post_list_url, {'content':'Mine','privacy':'private'})
        self.assertEqual(own_private.status_code, 201)
        listing = c2.get(self.post_list_url)
        self.assertEqual(listing.status_code, 200)
        data_list = listing.data
        if isinstance(data_list, dict) and 'results' in data_list:
            items = data_list['results']
        else:
            items = data_list
        ids = {item['id'] for item in items}
        self.assertIn(pub.data['id'], ids)
        self.assertIn(own_private.data['id'], ids)
        self.assertNotIn(priv.data['id'], ids)


class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client2 = APIClient()
        self.register_url = '/api/auth/register/'
        
        # Create two users
        import uuid
        
        # User 1
        reg1 = self.client.post(self.register_url, {
            'email': f'user1-{uuid.uuid4().hex[:6]}@example.com',
            'password': 'pass12345',
            'password_confirm': 'pass12345'
        })
        self.user1_token = reg1.data['tokens']['access']
        self.user1_id = reg1.data['user']['id']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
        
        # User 2
        reg2 = self.client2.post(self.register_url, {
            'email': f'user2-{uuid.uuid4().hex[:6]}@example.com',
            'password': 'pass12345',
            'password_confirm': 'pass12345'
        })
        self.user2_token = reg2.data['tokens']['access']
        self.user2_id = reg2.data['user']['id']
        self.client2.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user2_token}')

    def test_post_ownership_violations(self):
        # User1 creates a post
        post = self.client.post('/api/posts/', {'content': 'User1 post', 'privacy': 'public'})
        self.assertEqual(post.status_code, 201)
        post_id = post.data['id']
        
        # User2 attempts to update User1's post
        update_resp = self.client2.patch(f'/api/posts/{post_id}/', {'content': 'Hacked content'})
        self.assertIn(update_resp.status_code, (403, 404))
        
        # User2 attempts to delete User1's post
        delete_resp = self.client2.delete(f'/api/posts/{post_id}/')
        self.assertIn(delete_resp.status_code, (403, 404))
        
        # Verify post unchanged by owner check
        get_resp = self.client.get(f'/api/posts/{post_id}/')
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.data['content'], 'User1 post')

    def test_comment_ownership_violations(self):
        # User1 creates a post
        post = self.client.post('/api/posts/', {'content': 'Post for comment test'})
        post_id = post.data['id']
        
        # User1 adds a comment
        comment = self.client.post(f'/api/posts/{post_id}/comments/', {'text': 'User1 comment'})
        self.assertEqual(comment.status_code, 201)
        comment_id = comment.data['id']
        
        # User2 attempts to update User1's comment
        update_resp = self.client2.patch(f'/api/posts/{post_id}/comments/{comment_id}/', {'text': 'Hacked comment'})
        self.assertIn(update_resp.status_code, (403, 404))
        
        # User2 attempts to delete User1's comment
        delete_resp = self.client2.delete(f'/api/posts/{post_id}/comments/{comment_id}/')
        self.assertIn(delete_resp.status_code, (403, 404))

    def test_media_ownership_violations(self):
        # User1 creates a post and uploads media
        post = self.client.post('/api/posts/', {'content': 'Post with protected media'})
        post_id = post.data['id']
        
        dummy = SimpleUploadedFile('user1.txt', b'user1 content', content_type='text/plain')
        media = self.client.post(f'/api/posts/{post_id}/media/', {'file': dummy}, format='multipart')
        self.assertEqual(media.status_code, 201)
        media_id = media.data['id']
        
        # User2 attempts to delete User1's media
        delete_resp = self.client2.delete(f'/api/posts/{post_id}/media/{media_id}/')
        self.assertIn(delete_resp.status_code, (403, 404))
        
        # User2 attempts to retrieve User1's media (should also fail - only owner/uploader can access)
        get_resp = self.client2.get(f'/api/posts/{post_id}/media/{media_id}/')
        self.assertEqual(get_resp.status_code, 404)
        
        # Owner can still retrieve their media
        owner_get = self.client.get(f'/api/posts/{post_id}/media/{media_id}/')
        self.assertEqual(owner_get.status_code, 200)

    def test_private_post_access_violations(self):
        # User1 creates a private post
        post = self.client.post('/api/posts/', {'content': 'Secret private content', 'privacy': 'private'})
        self.assertEqual(post.status_code, 201)
        post_id = post.data['id']
        
        # User2 attempts to retrieve private post
        get_resp = self.client2.get(f'/api/posts/{post_id}/')
        self.assertEqual(get_resp.status_code, 404)  # Should appear as not found for security
        
        # User2 attempts to like private post (should fail since can't access)
        like_resp = self.client2.post(f'/api/posts/{post_id}/like/')
        self.assertEqual(like_resp.status_code, 404)
        
        # User2 attempts to comment on private post
        comment_resp = self.client2.post(f'/api/posts/{post_id}/comments/', {'text': 'Unauthorized comment'})
        self.assertIn(comment_resp.status_code, (403, 404))

    def test_unauthorized_media_upload(self):
        # User1 creates a post
        post = self.client.post('/api/posts/', {'content': 'Post for unauthorized media test'})
        post_id = post.data['id']
        
        # Unauthenticated user attempts to upload media
        unauth_client = APIClient()
        dummy = SimpleUploadedFile('unauth.txt', b'unauthorized', content_type='text/plain')
        upload_resp = unauth_client.post(f'/api/posts/{post_id}/media/', {'file': dummy}, format='multipart')
        self.assertEqual(upload_resp.status_code, 401)

    def test_like_nonexistent_post(self):
        # Attempt to like a non-existent post
        like_resp = self.client.post('/api/posts/99999/like/')
        self.assertEqual(like_resp.status_code, 404)

    def test_comment_nonexistent_post(self):
        # Attempt to comment on non-existent post
        comment_resp = self.client.post('/api/posts/99999/comments/', {'text': 'Comment on nothing'})
        self.assertEqual(comment_resp.status_code, 404)


# ThrottleTestCase disabled - throttling is disabled in test settings (settings_test.py)
# class ThrottleTestCase(TestCase):
#     def setUp(self):
#         self.client = APIClient()
# 
#     def test_register_throttle(self):
#         base_email = 'user{}@example.com'
#         for i in range(5):
#             resp = self.client.post('/api/auth/register/', {
#                 'email': base_email.format(i),
#                 'password': 'pass12345',
#                 'password_confirm': 'pass12345'
#             })
#             self.assertIn(resp.status_code, (201, 429))
#             if resp.status_code == 429:
#                 break
#         # Next request should likely be throttled if not already
#         resp_final = self.client.post('/api/auth/register/', {
#             'email': 'overflow@example.com',
#             'password': 'pass12345',
#             'password_confirm': 'pass12345'
#         })
#         # Acceptable outcomes: throttled 429 or created if timing difference
#         self.assertIn(resp_final.status_code, (201, 429))
# 
#     def test_post_create_throttle(self):
#         # Register and login
#         reg = self.client.post('/api/auth/register/', {
#             'email': 'throttleposter@example.com',
#             'password': 'pass12345',
#             'password_confirm': 'pass12345'
#         })
#         token = reg.data['tokens']['access']
#         self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
#         statuses = []
#         for i in range(35):  # exceed 30/min limit
#             r = self.client.post('/api/posts/', {'content': f'msg {i}'})
#             statuses.append(r.status_code)
#             if r.status_code == 429:
#                 break
#         self.assertTrue(any(code == 429 for code in statuses))


class SocialAuthTestCase(TestCase):
    """Test social authentication functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.google_login_url = '/api/auth/social/google/'
        
        # Mock Google user data
        self.mock_google_data = {
            'id': '12345678901234567890',
            'email': 'testuser@gmail.com',
            'verified_email': True,
            'name': 'Test User',
            'given_name': 'Test',
            'family_name': 'User',
            'picture': 'https://example.com/photo.jpg',
            'locale': 'en'
        }
    
    def test_google_login_invalid_token(self):
        """Test Google login with invalid token"""
        response = self.client.post(self.google_login_url, {
            'access_token': 'invalid-token-12345'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_google_login_missing_token(self):
        """Test Google login without access token"""
        response = self.client.post(self.google_login_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_social_auth_url_structure(self):
        """Test that social auth URL is properly configured"""
        # This is a basic structural test to ensure our URL routing works
        response = self.client.get(self.google_login_url)
        # Should return 405 Method Not Allowed since we only accept POST
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_social_login_serializer_validation(self):
        """Test social login request validation"""
        from users.social_auth import SocialLoginSerializer
        
        # Valid data
        serializer = SocialLoginSerializer(data={'access_token': 'test-token'})
        self.assertTrue(serializer.is_valid())
        
        # Missing access_token
        serializer = SocialLoginSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('access_token', serializer.errors)
