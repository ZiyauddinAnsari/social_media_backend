from rest_framework.throttling import SimpleRateThrottle

class BurstRateThrottle(SimpleRateThrottle):
    scope = 'burst'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}

class SustainedRateThrottle(SimpleRateThrottle):
    scope = 'sustained'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}

class AuthLoginThrottle(SimpleRateThrottle):
    scope = 'auth_login'

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}

class AuthRegisterThrottle(SimpleRateThrottle):
    scope = 'auth_register'

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}

class PostCreateThrottle(SimpleRateThrottle):
    scope = 'post_create'

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
        # tie to user if auth; else IP
        if request.user and request.user.is_authenticated:
            ident = str(request.user.pk)
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}

class CommentCreateThrottle(SimpleRateThrottle):
    scope = 'comment_create'

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
        if request.user and request.user.is_authenticated:
            ident = str(request.user.pk)
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}
